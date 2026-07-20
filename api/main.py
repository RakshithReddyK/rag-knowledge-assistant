from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI
from pydantic import BaseModel

from rag.rag_chain import RAGPipeline

# Load environment variables from .env (e.g., GROQ_API_KEY)
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="RAG Knowledge Assistant",
    version="1.0.0",
    description=(
        "Ask questions over your indexed documents using "
        "Retrieval-Augmented Generation (RAG)."
    ),
)

# The RAG pipeline (vector store + LLM client) is constructed lazily on the
# first request rather than at import time. Building it eagerly would load
# the embedding model and require GROQ_API_KEY just to *import* this module,
# which makes the app impossible to test without real credentials. Tests
# override `get_rag_pipeline` via `app.dependency_overrides` instead.
_rag_pipeline: Optional[RAGPipeline] = None


def get_rag_pipeline() -> RAGPipeline:
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = RAGPipeline()
    return _rag_pipeline


class AskRequest(BaseModel):
    question: str


class ContextChunk(BaseModel):
    text: str
    metadata: Dict[str, Any]


class AskResponse(BaseModel):
    answer: str
    context: List[ContextChunk]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest, pipeline: RAGPipeline = Depends(get_rag_pipeline)):
    result = pipeline.answer(req.question)

    return AskResponse(
        answer=result["answer"],
        context=[
            ContextChunk(text=c["text"], metadata=c["metadata"])
            for c in result["context"]
        ],
    )
