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
# CHUNK_SIZE / CHUNK_OVERLAP are measured in whitespace-delimited "tokens"
# (see rag/ingest.py:_count_tokens), not raw characters -- chunking is
# paragraph/sentence-boundary aware rather than a fixed character slice.
CHUNK_SIZE = 200      # tokens (~words) per chunk
CHUNK_OVERLAP = 40    # tokens of overlap carried into the next chunk
TOP_K = 5             # retrieved chunks
