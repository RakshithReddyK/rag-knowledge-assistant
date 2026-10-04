"""Local-first API with optional shared-key authentication and bounded inputs."""

import logging
import math
import os
import secrets
import threading
import time
from collections import Counter, deque
from functools import lru_cache
from typing import Annotated, Literal

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from rag.agent import EvidenceAgent
from rag.llm import ProviderUnavailable
from rag.rag_chain import RAGPipeline
from rag.tool_agent import ToolCallingAgent

load_dotenv()
logger = logging.getLogger(__name__)
app = FastAPI(title="RAG Knowledge Assistant", version="2.0.0")
_lock = threading.Lock()
_events = deque(maxlen=10000)
_counts = Counter()
_latency = deque(maxlen=1000)
Question = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=2000)]


@lru_cache(maxsize=1)
def get_rag_pipeline():
    return RAGPipeline()


def access_control(x_api_key: str | None = Header(default=None)):
    expected = os.getenv("RAG_API_KEY")
    if expected and not secrets.compare_digest(x_api_key or "", expected):
        raise HTTPException(401, "Invalid API key")
    # Global, per-process limit; use a gateway for multi-worker/public deployments.
    limit = max(1, min(int(os.getenv("RAG_REQUESTS_PER_MINUTE", "60")), 10000))
    now = time.monotonic()
    with _lock:
        while _events and _events[0] <= now - 60:
            _events.popleft()
        if len(_events) >= limit:
            raise HTTPException(429, "Request budget exhausted", headers={"Retry-After": "60"})
        _events.append(now)


class AskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: Question
    mode: Literal["extractive", "generative"] = "extractive"
    top_k: int = Field(default=3, ge=1, le=5)


class AgentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: Question
    mode: Literal["deterministic", "llm"] = "deterministic"


@app.middleware("http")
async def observations(request, call_next):
    started = time.perf_counter()
    response = await call_next(request)
    duration = (time.perf_counter() - started) * 1000
    with _lock:
        _counts[str(response.status_code)] += 1
        _latency.append(duration)
    # No prompt text, response content, credentials, or user-provided identifiers logged.
    logger.info("request status=%d latency_ms=%.2f", response.status_code, duration)
    response.headers["X-Response-Time-Ms"] = f"{duration:.2f}"
    return response


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready", dependencies=[Depends(access_control)])
def ready(pipeline=Depends(get_rag_pipeline)):
    if not pipeline.kb.chunks:
        raise HTTPException(503, "Knowledge base is empty")
    return {
        "status": "ready",
        "index_version": pipeline.kb.version,
        "documents": len(pipeline.kb.documents),
        "chunks": len(pipeline.kb.chunks),
        "generation_configured": bool(os.getenv("GROQ_API_KEY")),
    }


@app.post("/ask", dependencies=[Depends(access_control)])
def ask(req: AskRequest, pipeline=Depends(get_rag_pipeline)):
    try:
        return pipeline.answer(req.question, mode=req.mode, top_k=req.top_k)
    except ProviderUnavailable as exc:
        raise HTTPException(503, str(exc), headers={"Retry-After": "15"}) from exc


@app.post("/agent", dependencies=[Depends(access_control)])
def agent(req: AgentRequest, pipeline=Depends(get_rag_pipeline)):
    if req.mode == "llm":
        result = ToolCallingAgent(pipeline.kb).run(req.question)
        if result["status"] == "provider_unavailable":
            from fastapi.responses import JSONResponse

            return JSONResponse(result, status_code=503, headers={"Retry-After": "15"})
        return result
    return EvidenceAgent(pipeline.kb).run(req.question)


@app.get("/metrics", dependencies=[Depends(access_control)])
def metrics():
    with _lock:
        values = sorted(_latency)
        return {
            "requests_by_status": dict(_counts),
            "window_size": len(values),
            "p95_latency_ms": values[max(0, math.ceil(0.95 * len(values)) - 1)] if values else 0,
            "scope": "single_process_last_1000_requests",
        }
