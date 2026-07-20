import os
import re
from pathlib import Path
from typing import List

from .config import CHUNK_OVERLAP, CHUNK_SIZE, DATA_DIR
from .vectorstore import VectorStore

# Matches one or more blank lines, used to split text into paragraphs.
_PARAGRAPH_SPLIT_RE = re.compile(r"\n\s*\n")

# Splits on whitespace that follows a sentence-ending punctuation mark.
# Good enough for plain prose/markdown without pulling in an NLP library.
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def load_files() -> List[Path]:
    exts = {".txt", ".md"}
    # data/README.md documents the sample corpus itself -- it isn't part of
    # the corpus and shouldn't be ingested as a retrievable chunk.
    excluded_names = {"README.md"}
    files = [
        p
        for p in DATA_DIR.glob("**/*")
        if p.suffix in exts and p.is_file() and p.name not in excluded_names
    ]
    return files


def _split_paragraphs(text: str) -> List[str]:
    return [p.strip() for p in _PARAGRAPH_SPLIT_RE.split(text) if p.strip()]


def _split_sentences(paragraph: str) -> List[str]:
    return [s.strip() for s in _SENTENCE_SPLIT_RE.split(paragraph) if s.strip()]


def _count_tokens(text: str) -> int:
    """Whitespace-delimited word count, used as a cheap, dependency-free
    proxy for an LLM token count. It's not exact, but it scales chunk
    sizes sensibly without pulling in a real tokenizer."""
    return len(text.split())


def chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    """Split ``text`` into chunks along paragraph/sentence boundaries,
    greedily packing sentences up to a ``chunk_size``-token budget and
    carrying up to ``overlap`` tokens of trailing context into the next
    chunk for retrieval continuity.

    ``chunk_size`` and ``overlap`` are measured in whitespace-delimited
    "tokens" (see ``_count_tokens``), not raw characters -- this avoids
    slicing sentences in half mid-word the way naive character slicing
    does.

    If ``overlap >= chunk_size`` the chunks would never make forward
    progress (each new chunk would re-include everything from the last
    one, or more), so it is clamped to ``chunk_size - 1`` rather than
    looping forever.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be a positive integer")
    overlap = max(0, min(overlap, chunk_size - 1))

    sentences: List[str] = []
    for paragraph in _split_paragraphs(text):
        sentences.extend(_split_sentences(paragraph))

    if not sentences:
        return []

    chunks: List[str] = []
    current: List[str] = []
    current_tokens = 0

    for sentence in sentences:
        sentence_tokens = _count_tokens(sentence)

        if current and current_tokens + sentence_tokens > chunk_size:
            chunks.append(" ".join(current))

            if overlap > 0:
                # Carry trailing sentences (up to `overlap` tokens) from
                # the chunk we just closed into the next one.
                overlap_sentences: List[str] = []
                overlap_tokens = 0
                for s in reversed(current):
                    t = _count_tokens(s)
                    if overlap_tokens + t > overlap:
                        break
                    overlap_sentences.insert(0, s)
                    overlap_tokens += t
                current = overlap_sentences
                current_tokens = overlap_tokens
            else:
                current = []
                current_tokens = 0

        current.append(sentence)
        current_tokens += sentence_tokens

    if current:
        chunks.append(" ".join(current))

    return chunks


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
