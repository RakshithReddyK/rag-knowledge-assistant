"""Inspectable BM25 retrieval over an immutable, versioned corpus snapshot."""

import hashlib
import math
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

from .config import CHUNK_OVERLAP, CHUNK_SIZE, DATA_DIR
from .ingest import chunk_text

STOP_WORDS = frozenset(
    (
        "a an and are as at be by can do does for from how i in is it of on or "
        "should that the this to was what when where which why with you your"
    ).split()
)


def tokenize(text):
    return [word for word in re.findall(r"[a-z0-9]+", text.lower()) if word not in STOP_WORDS]


@dataclass(frozen=True)
class Chunk:
    id: str
    source: str
    chunk_index: int
    text: str

    def result(self, score):
        return {
            "text": self.text,
            "metadata": {
                "source": self.source,
                "chunk_index": self.chunk_index,
                "chunk_id": self.id,
            },
            "score": round(score, 5),
        }


class KnowledgeBase:
    def __init__(self, root=DATA_DIR / "samples", chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
        root = Path(root).resolve()
        self.documents = {}
        self.chunks = []
        for path in sorted(root.rglob("*")):
            if path.suffix not in {".txt", ".md"} or path.name == "README.md":
                continue
            if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(root):
                continue
            if path.stat().st_size > 1_000_000:
                raise ValueError("Corpus files must be at most 1 MB")
            source = path.relative_to(root).as_posix()
            text = path.read_text(encoding="utf-8")
            self.documents[source] = text
            for index, part in enumerate(chunk_text(text, chunk_size, overlap)):
                digest = hashlib.sha256(f"{source}:{index}:{part}".encode()).hexdigest()[:16]
                self.chunks.append(Chunk(digest, source, index, part))
        manifest = "\n".join(f"{s}:{t}" for s, t in self.documents.items())
        self.version = hashlib.sha256(f"{chunk_size}:{overlap}:{manifest}".encode()).hexdigest()[
            :16
        ]
        self.counts = [Counter(tokenize(c.text)) for c in self.chunks]
        self.lengths = [sum(c.values()) for c in self.counts]
        self.avg_length = sum(self.lengths) / max(len(self.lengths), 1)
        self.frequency = Counter(token for count in self.counts for token in count)

    def search(self, question, top_k=3, method="bm25"):
        if not 1 <= top_k <= 10:
            raise ValueError("top_k must be between 1 and 10")
        if method not in {"bm25", "overlap"}:
            raise ValueError("Unknown retrieval method")
        query = set(tokenize(question))
        if not query:
            return []
        scored = []
        n = len(self.chunks)
        for i, count in enumerate(self.counts):
            if method == "overlap":
                score = len(query & count.keys()) / len(query)
            else:
                score = 0.0
                for term in query:
                    tf = count[term]
                    if tf:
                        idf = math.log(
                            1 + (n - self.frequency[term] + 0.5) / (self.frequency[term] + 0.5)
                        )
                        norm = 1.5 * (0.25 + 0.75 * self.lengths[i] / self.avg_length)
                        score += idf * tf * 2.5 / (tf + norm)
            if score > 0:
                scored.append((score, i))
        scored.sort(key=lambda item: (-item[0], self.chunks[item[1]].id))
        return [self.chunks[i].result(score) for score, i in scored[:top_k]]

    def read_document(self, source):
        # Lookup only: a user/model supplied value is never passed to open().
        if source not in self.documents:
            raise ValueError("Source is not in the indexed document allowlist")
        return {
            "source": source,
            "text": self.documents[source][:12000],
            "truncated": len(self.documents[source]) > 12000,
        }

    def manifest(self):
        return {
            "version": self.version,
            "documents": len(self.documents),
            "chunks": len(self.chunks),
            "items": [asdict(c) for c in self.chunks],
        }
