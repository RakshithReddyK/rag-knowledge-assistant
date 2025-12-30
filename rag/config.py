import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CHROMA_DIR = BASE_DIR / "chroma_db"

# Embedding model
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# LLM config
GROQ_MODEL_NAME = "llama-3.1-8b-instant"  # adjust if needed
GROQ_API_KEY_ENV = "GROQ_API_KEY"

# RAG parameters
CHUNK_SIZE = 600      # characters per chunk
CHUNK_OVERLAP = 100   # overlap between chunks
TOP_K = 5             # retrieved chunks
