# Gemma 4 Demo

A local chat interface for [Gemma 4 E2B-it](https://huggingface.co/mlx-community/gemma-4-e2b-it-4bit) running entirely on your Mac via [MLX](https://github.com/ml-explore/mlx). Nothing leaves your device.

## Stack

| Layer | Technology |
|---|---|
| Model | `mlx-community/gemma-4-e2b-it-4bit` (~3 GB, 4-bit quantized) |
| Backend | FastAPI + SSE streaming, port `8000` |
| Frontend | React + Vite, markdown & syntax highlighting, port `5173` (dev) / `80` (Docker) |
| Runtime | MLX — Apple Silicon only |

## Requirements

- Apple Silicon Mac (M1 or later)
- Python 3.10+
- Node.js 18+
- Docker Desktop (optional, for containerised run)

## Run locally

**Backend**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --port 8000
```

The first start downloads the model weights (~3 GB) to `~/.cache/huggingface/`.

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. API calls are proxied to the backend automatically.

## Run with Docker

```bash
docker compose up --build
```

- Frontend → http://localhost
- Backend API → http://localhost:8000

Model weights are persisted in a named Docker volume (`model_cache`) so they survive container restarts.

> **Note:** MLX requires Apple Silicon Metal GPU access. The backend container works with Docker Desktop on Apple Silicon but will not run on Linux x86 hosts.

## Project structure

```
.
├── backend/
│   ├── main.py          # FastAPI app with SSE streaming endpoint
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.jsx      # Chat UI (streaming, markdown, copy button)
│   │   └── App.css
│   ├── nginx.conf       # SPA routing + /api proxy for production
│   ├── Dockerfile
│   ├── package.json
│   └── vite.config.js
├── run_gemma4.py        # CLI chat script (text & vision)
├── requirements.txt
└── docker-compose.yml
```

## CLI usage

The repo also includes a standalone CLI for quick text or vision chat:

```bash
# Interactive text chat
python run_gemma4.py

# Single prompt
python run_gemma4.py --prompt "Explain transformers in one paragraph"

# Vision (image + prompt)
python run_gemma4.py --image photo.jpg --prompt "What is in this image?"
```

## Model variants

| Model ID | Size | Quality |
|---|---|---|
| `mlx-community/gemma-4-e2b-it-4bit` | ~3 GB | Default |
| `mlx-community/gemma-4-e2b-it-8bit` | ~5 GB | Better |
| `mlx-community/gemma-4-e2b-it-bf16` | ~10 GB | Best |

Pass a different model with `--model <model-id>` when using the CLI, or update `MODEL_ID` in `backend/main.py`.
