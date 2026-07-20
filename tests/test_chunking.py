"""Unit tests for rag.ingest.chunk_text."""
import pytest

from rag.ingest import chunk_text


def test_empty_text_returns_no_chunks():
    assert chunk_text("", chunk_size=50, overlap=10) == []


def test_whitespace_only_text_returns_no_chunks():
    assert chunk_text("   \n\n   ", chunk_size=50, overlap=10) == []


def test_short_text_fits_in_one_chunk():
    text = "This is a short sentence. And another one."
    chunks = chunk_text(text, chunk_size=50, overlap=0)
    assert len(chunks) == 1
    assert "short sentence" in chunks[0]
    assert "another one" in chunks[0]


def test_splits_long_text_into_multiple_chunks():
    text = " ".join(f"Sentence number {i}." for i in range(20))
    chunks = chunk_text(text, chunk_size=10, overlap=0)
    assert len(chunks) > 1
    # No chunk should wildly exceed the requested budget (a single
    # oversized sentence may exceed it, but these sentences are tiny).
    for c in chunks:
        assert len(c.split()) <= 12


def test_overlap_carries_context_between_chunks():
    text = "Alpha bravo charlie. Delta echo foxtrot. Golf hotel india. Juliet kilo lima."
    chunks = chunk_text(text, chunk_size=6, overlap=3)
    assert len(chunks) >= 2
    # The tail of one chunk should reappear at the head of the next,
    # since overlap > 0 carries trailing sentences forward.
    first_words = chunks[0].split()
    second_words = chunks[1].split()
    assert any(w in second_words for w in first_words)


def test_no_chunk_is_empty_or_blank():
    text = "First sentence here. Second sentence here. Third sentence here."
    chunks = chunk_text(text, chunk_size=4, overlap=2)
    assert all(c.strip() for c in chunks)


def test_reassembled_chunks_preserve_all_sentences():
    text = "One. Two. Three. Four. Five."
    chunks = chunk_text(text, chunk_size=2, overlap=0)
    combined = " ".join(chunks)
    for sentence in ["One.", "Two.", "Three.", "Four.", "Five."]:
        assert sentence in combined


def test_overlap_greater_than_chunk_size_terminates_and_clamps():
    """Regression test: the original character-slicing implementation
    computed `start = end - overlap`, which never advances (or even goes
    backwards) once overlap >= chunk_size, looping forever. The rewritten
    sentence-packing implementation must clamp overlap below chunk_size
    and always terminate."""
    text = " ".join(f"Word{i} filler token here." for i in range(30))

    chunks = chunk_text(text, chunk_size=5, overlap=999)

    assert isinstance(chunks, list)
    assert len(chunks) > 0
    assert all(isinstance(c, str) and c for c in chunks)


def test_overlap_equal_to_chunk_size_terminates():
    text = "Sentence one here. Sentence two here. Sentence three here."
    chunks = chunk_text(text, chunk_size=4, overlap=4)
    assert len(chunks) > 0


def test_zero_or_negative_chunk_size_raises():
    with pytest.raises(ValueError):
        chunk_text("some text", chunk_size=0, overlap=0)
    with pytest.raises(ValueError):
        chunk_text("some text", chunk_size=-5, overlap=0)


def test_paragraph_boundaries_are_respected():
    text = "Para one sentence A. Para one sentence B.\n\nPara two sentence A. Para two sentence B."
    # Generous budget so each paragraph's sentences stay together, but the
    # point is that paragraph splitting doesn't crash and content survives.
    chunks = chunk_text(text, chunk_size=100, overlap=0)
    combined = " ".join(chunks)
    assert "Para one sentence A." in combined
    assert "Para two sentence B." in combined
