"""
Gemma 4 E2B-it — interactive chat with optional image input.
Uses MLX (Apple Silicon native) with 4-bit quantization (~3 GB RAM).

Usage:
    python run_gemma4.py                          # interactive text chat
    python run_gemma4.py --image photo.jpg        # chat with an image
    python run_gemma4.py --prompt "one-shot"      # single non-interactive response

Model variants (pass with --model):
    mlx-community/gemma-4-e2b-it-4bit   (default, ~3 GB)
    mlx-community/gemma-4-e2b-it-8bit   (~5 GB)
    mlx-community/gemma-4-e2b-it-bf16   (~10 GB, highest quality)

First run downloads the model weights to ~/.cache/huggingface/
"""

import argparse
import sys

DEFAULT_MODEL = "mlx-community/gemma-4-e2b-it-4bit"

SYSTEM_PROMPT = "You are a helpful assistant."


# ---------------------------------------------------------------------------
# Text-only chat via mlx-lm
# ---------------------------------------------------------------------------

def load_text_model(model_id: str):
    from mlx_lm import load
    print(f"Loading {model_id} ...")
    print("(First run downloads model weights — this may take a while)\n")
    model, tokenizer = load(model_id)
    print("Model loaded.\n")
    return model, tokenizer


def chat_text(model, tokenizer, history: list, max_tokens: int = 512) -> str:
    from mlx_lm import generate
    from mlx_lm.sample_utils import make_sampler

    prompt = tokenizer.apply_chat_template(
        history,
        add_generation_prompt=True,
        tokenize=False,
    )
    response = generate(
        model,
        tokenizer,
        prompt=prompt,
        max_tokens=max_tokens,
        sampler=make_sampler(temp=1.0, top_p=0.95),
        verbose=False,
    )
    return response


def run_interactive_chat(model_id: str, initial_prompt: str | None, max_tokens: int):
    model, tokenizer = load_text_model(model_id)
    history = [{"role": "system", "content": SYSTEM_PROMPT}]

    print("Gemma 4 E2B-it — interactive chat")
    print("Type 'quit' or 'exit' to stop, 'clear' to reset conversation.\n")

    if initial_prompt:
        history.append({"role": "user", "content": initial_prompt})
        print(f"You: {initial_prompt}")
        response = chat_text(model, tokenizer, history, max_tokens)
        print(f"Gemma: {response}\n")
        history.append({"role": "assistant", "content": response})

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit"):
            print("Goodbye!")
            break
        if user_input.lower() == "clear":
            history = [{"role": "system", "content": SYSTEM_PROMPT}]
            print("Conversation cleared.\n")
            continue

        history.append({"role": "user", "content": user_input})
        response = chat_text(model, tokenizer, history, max_tokens)
        print(f"Gemma: {response}\n")
        history.append({"role": "assistant", "content": response})


# ---------------------------------------------------------------------------
# Vision chat via mlx-vlm
# ---------------------------------------------------------------------------

def run_image_chat(model_id: str, image_path: str, prompt: str | None, max_tokens: int):
    try:
        from mlx_vlm import load as vlm_load, generate as vlm_generate
        from mlx_vlm.prompt_utils import apply_chat_template
        from mlx_vlm.utils import load_config
    except ImportError:
        print("mlx-vlm is required for image input. Install it with:\n  pip install mlx-vlm")
        sys.exit(1)

    print(f"Loading {model_id} for vision ...")
    print("(First run downloads model weights — this may take a while)\n")
    model, processor = vlm_load(model_id)
    config = load_config(model_id)
    print("Model loaded.\n")

    if prompt is None:
        prompt = "Describe this image in detail."

    formatted = apply_chat_template(processor, config, prompt, num_images=1)
    response = vlm_generate(
        model,
        processor,
        formatted,
        image=image_path,
        max_tokens=max_tokens,
        temperature=1.0,
        verbose=False,
    )
    print(f"Gemma: {response}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Run Gemma 4 E2B-it via MLX on Apple Silicon")
    parser.add_argument("--model", default=DEFAULT_MODEL,
                        help=f"MLX model ID (default: {DEFAULT_MODEL})")
    parser.add_argument("--image", metavar="PATH",
                        help="Path to an image file (enables vision mode)")
    parser.add_argument("--prompt", metavar="TEXT",
                        help="Initial / one-shot prompt")
    parser.add_argument("--max-tokens", type=int, default=512,
                        help="Maximum tokens to generate (default: 512)")
    args = parser.parse_args()

    if args.image:
        run_image_chat(args.model, args.image, args.prompt, args.max_tokens)
    else:
        run_interactive_chat(args.model, args.prompt, args.max_tokens)


if __name__ == "__main__":
    main()
