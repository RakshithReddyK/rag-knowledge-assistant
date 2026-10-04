from rag.ingest import chunk_text
from rag.retrieval import KnowledgeBase


def test_chunk_budget_even_for_long_sentences_and_overlap():
    text = " ".join(f"word{i}" for i in range(105)) + ". Short final sentence."
    chunks = chunk_text(text, 20, 19)
    assert all(len(c.split()) <= 20 for c in chunks)
    assert all(f"word{i}" in " ".join(chunks) for i in range(105))


def test_index_is_stable_and_does_not_accumulate_duplicates(tmp_path):
    source = tmp_path / "guide.md"
    source.write_text("Token bucket rate limiting controls request bursts.")
    first, second = KnowledgeBase(tmp_path), KnowledgeBase(tmp_path)
    assert first.version == second.version
    assert first.chunks == second.chunks
    source.write_text("Changed guidance for retry backoff.")
    third = KnowledgeBase(tmp_path)
    assert third.version != first.version
    assert third.search("bucket") == []
    source.unlink()
    assert KnowledgeBase(tmp_path).chunks == []


def test_source_allowlist_and_symlinks(tmp_path):
    import pytest

    (tmp_path / "ok.md").write_text("Allowed document")
    (tmp_path / "secret.md").symlink_to("/etc/passwd")
    kb = KnowledgeBase(tmp_path)
    assert set(kb.documents) == {"ok.md"}
    with pytest.raises(ValueError):
        kb.read_document("../../etc/passwd")


def test_empty_corpus_and_zero_match(tmp_path):
    kb = KnowledgeBase(tmp_path)
    assert kb.search("anything") == []
    assert KnowledgeBase().search("zxqvnonsense") == []


def test_real_corpus_retrieval():
    hits = KnowledgeBase().search("How does a token bucket allow bursts?")
    assert hits[0]["metadata"]["source"] == "rate_limiting.md"
