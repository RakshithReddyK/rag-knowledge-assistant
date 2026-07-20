# Sample Knowledge Base

The `samples/` directory contains five short, original Markdown explainer
documents on unrelated backend/systems topics (HTTP caching, Bloom filters,
database indexing, consistent hashing, and API rate limiting). They exist
purely as a small, public, PII-free corpus so anyone who clones this repo
can run `python -m rag.ingest` and get a working, reproducible demo without
needing any private documents. Drop your own `.txt`/`.md` files anywhere
under `data/` (including in new subdirectories) to index different content
instead — `rag/ingest.py` walks the directory recursively.
