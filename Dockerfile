# Single image used for both the FastAPI backend and the Streamlit
# frontend (see docker-compose.yml, which overrides `command:` per
# service) as well as for one-off ingestion runs.
FROM python:3.11-slim

WORKDIR /app

# System deps: chromadb's dependency chain (onnxruntime etc.) and
# sentence-transformers occasionally need a C build toolchain.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY rag ./rag
COPY api ./api
COPY streamlit_app.py ./
COPY data ./data

# rag/config.py resolves CHROMA_DIR as <repo-root>/chroma_db, which inside
# this image is /app/chroma_db. Mount a volume at that path in
# docker-compose so the persisted index survives container restarts.
RUN mkdir -p /app/chroma_db

EXPOSE 9000

# Default: run the FastAPI backend. docker-compose overrides this for the
# streamlit service and for the one-off ingestion job.
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "9000"]
