# NOTE: MLX requires Apple Silicon (Metal GPU). This image will not work
# on Linux x86 or inside a standard Docker Linux VM.
# Run with Docker Desktop on Apple Silicon.

FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
