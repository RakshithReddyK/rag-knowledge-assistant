"""Unit test for rag.vectorstore.VectorStore add/query round-trip.

Uses a deterministic fake embedder (instead of the real sentence-transformers
model) so the test is fast, offline, and doesn't depend on downloading model
weights. It also points Chroma at a pytest tmp_path instead of the app's
real chroma_db/ directory, so tests never touch (or pollute) real data.
"""
import hashlib

from rag.vectorstore import VectorStore


class FakeEmbedder:
    """Deterministic, dependency-free stand-in for EmbeddingModel.

    The same input text always produces the same vector, and different
    texts produce different vectors -- enough to exercise Chroma's
    add/query path without loading a real ML model.
    """

    def encode(self, texts, normalize: bool = True):
        if isinstance(texts, str):
            texts = [texts]
        vectors = []
        for text in texts:
            digest = hashlib.sha256(text.encode("utf-8")).digest()
            vectors.append([b / 255.0 for b in digest[:16]])
        return vectors


def make_store(tmp_path):
    return VectorStore(
        collection_name="test_collection",
        persist_directory=tmp_path / "chroma_test",
        embedder=FakeEmbedder(),
    )


def test_add_and_query_round_trip(tmp_path):
    vs = make_store(tmp_path)

    texts = [
        "Bloom filters are probabilistic set membership structures.",
        "B-tree indexes keep keys sorted for fast range scans.",
        "Token bucket rate limiting allows short bursts of traffic.",
    ]
    metadatas = [
        {"source": "bloom_filters.md", "chunk_index": 0},
        {"source": "database_indexing.md", "chunk_index": 0},
        {"source": "rate_limiting.md", "chunk_index": 0},
    ]

    vs.add_texts(texts, metadatas)

    results = vs.query(texts[0], top_k=1)

    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]

    assert len(docs) == 1
    assert docs[0] == texts[0]
    assert metas[0]["source"] == "bloom_filters.md"


def test_query_returns_top_k_results(tmp_path):
    vs = make_store(tmp_path)

    texts = [f"Document number {i} about topic {i}." for i in range(5)]
    metadatas = [{"source": f"doc{i}.md", "chunk_index": 0} for i in range(5)]
    vs.add_texts(texts, metadatas)

    results = vs.query("Document number 0 about topic 0.", top_k=3)
    docs = results.get("documents", [[]])[0]

    assert len(docs) == 3


def test_query_on_empty_collection_returns_no_documents(tmp_path):
    vs = make_store(tmp_path)
    results = vs.query("anything", top_k=5)
    docs = results.get("documents", [[]])[0]
    assert docs == []
