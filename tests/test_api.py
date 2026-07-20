"""Integration test for the FastAPI /ask endpoint.

Does NOT make real Groq API calls or load the real embedding model / Chroma
store. `api.main.get_rag_pipeline` is overridden via FastAPI's
`dependency_overrides` with a fake pipeline, so importing api.main and
calling /ask never requires GROQ_API_KEY or network access.
"""
from fastapi.testclient import TestClient

from api.main import app, get_rag_pipeline


class FakeRAGPipeline:
    """Stands in for rag.rag_chain.RAGPipeline -- no vector store, no LLM."""

    def answer(self, question: str) -> dict:
        return {
            "answer": f"Fake answer for: {question}",
            "context": [
                {
                    "text": "Some retrieved chunk relevant to the question.",
                    "metadata": {"source": "bloom_filters.md", "chunk_index": 0},
                }
            ],
        }


def _override_pipeline():
    return FakeRAGPipeline()


app.dependency_overrides[get_rag_pipeline] = _override_pipeline

client = TestClient(app)


def test_health_check():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_ask_returns_answer_and_context_from_mocked_pipeline():
    resp = client.post("/ask", json={"question": "What is a Bloom filter?"})
    assert resp.status_code == 200

    data = resp.json()
    assert data["answer"] == "Fake answer for: What is a Bloom filter?"
    assert len(data["context"]) == 1
    assert data["context"][0]["metadata"]["source"] == "bloom_filters.md"


def test_ask_requires_question_field():
    resp = client.post("/ask", json={})
    assert resp.status_code == 422
