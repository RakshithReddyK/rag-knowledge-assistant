import os
from pathlib import Path
from typing import List

from .config import DATA_DIR, CHUNK_SIZE, CHUNK_OVERLAP
from .vectorstore import VectorStore


def load_files() -> List[Path]:
    exts = {".txt", ".md"}
    files = [p for p in DATA_DIR.glob("**/*") if p.suffix in exts and p.is_file()]
    return files


def chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk.strip())
        start = end - overlap
        if start < 0:
            start = 0
    return [c for c in chunks if c]


def ingest():
    os.makedirs(DATA_DIR, exist_ok=True)
    vs = VectorStore()

    files = load_files()
    if not files:
        print(f"No .txt or .md files found in {DATA_DIR}.")
        return

    all_texts = []
    all_metas = []

    for f in files:
        content = f.read_text(encoding="utf-8", errors="ignore")
        chunks = chunk_text(content, CHUNK_SIZE, CHUNK_OVERLAP)
        for i, ch in enumerate(chunks):
            all_texts.append(ch)
            all_metas.append({
                "source": f.name,
                "chunk_index": i
            })

    print(f"Ingesting {len(all_texts)} chunks from {len(files)} files...")
    vs.add_texts(all_texts, all_metas)
    print("Ingestion complete.")


if __name__ == "__main__":
    ingest()
