"""
Gemma 4 E2B-it — FastAPI backend with SSE streaming.

Start with:
    cd backend
    ../.venv/bin/uvicorn main:app --port 8000
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Literal
import asyncio
import json
import queue
from concurrent.futures import ThreadPoolExecutor

MODEL_ID = "mlx-community/gemma-4-e2b-it-4bit"
SYSTEM_PROMPT = (
    "You are a helpful assistant. "
    "Be concise and direct — keep answers short unless the user explicitly asks for detail or a long explanation. "
    "Avoid restating the question, unnecessary preamble, and filler phrases like 'Certainly!' or 'Great question!'. "
    "Use markdown only when it genuinely aids clarity (e.g. code blocks, short lists). "
    "If a one-sentence answer suffices, give one sentence."
)

_model = None
_tokenizer = None
# max_workers=1: MLX saturates all cores for one job; serialise requests.
_executor = ThreadPoolExecutor(max_workers=1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _model, _tokenizer
    from mlx_lm import load
    print(f"Loading {MODEL_ID} …")
    _model, _tokenizer = load(MODEL_ID)
    print("Model ready.")
    yield
    _executor.shutdown(wait=False)


app = FastAPI(lifespan=lifespan)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    messages: list[Message]
    max_tokens: int = 1024


# ---------------------------------------------------------------------------
# Generation (runs in ThreadPoolExecutor — synchronous MLX code)
# ---------------------------------------------------------------------------

_SENTINEL = object()


def _run_generation(q: queue.SimpleQueue, messages: list, max_tokens: int) -> None:
    """
    Runs in the dedicated thread. Puts token strings onto the queue,
    then puts _SENTINEL when done (or an Exception on failure).
    """
    from mlx_lm import stream_generate
    from mlx_lm.sample_utils import make_sampler

    try:
        full_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
        prompt = _tokenizer.apply_chat_template(
            full_messages,
            add_generation_prompt=True,
            tokenize=False,
            enable_thinking=False,
        )
        for response in stream_generate(
            _model,
            _tokenizer,
            prompt,
            max_tokens=max_tokens,
            sampler=make_sampler(temp=1.0, top_p=0.95),
        ):
            q.put(response.text)
    except Exception as exc:
        q.put(exc)
    finally:
        q.put(_SENTINEL)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.post("/api/chat")
async def chat(req: ChatRequest):
    messages = [{"role": m.role, "content": m.content} for m in req.messages]

    async def stream():
        q: queue.SimpleQueue = queue.SimpleQueue()
        loop = asyncio.get_running_loop()

        # Kick off generation in the dedicated MLX thread.
        loop.run_in_executor(_executor, _run_generation, q, messages, req.max_tokens)

        while True:
            # Block the default thread pool (not the event loop) until a token arrives.
            item = await loop.run_in_executor(None, q.get)

            if item is _SENTINEL:
                break

            if isinstance(item, Exception):
                yield f"data: {json.dumps({'error': str(item)})}\n\n"
                break

            yield f"data: {json.dumps({'token': item})}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/health")
async def health():
    return {"status": "ok", "model": MODEL_ID, "ready": _model is not None}
