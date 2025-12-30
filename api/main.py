from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any

from dotenv import load_dotenv
from rag.rag_chain import RAGPipeline

# Load environment variables from .env (e.g., GROQ_API_KEY)
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="RAG Knowledge Assistant",
    version="1.0.0",
    description="Ask questions over your indexed documents using Retrieval-Augmented Generation (RAG).",
)

# Initialize RAG pipeline (vector store + LLM)
rag_pipeline = RAGPipeline()


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
def ask(req: AskRequest):
    result = rag_pipeline.answer(req.question)

    return AskResponse(
        answer=result["answer"],
        context=[
            ContextChunk(text=c["text"], metadata=c["metadata"])
            for c in result["context"]
        ],
    )
