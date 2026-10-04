"""A bounded, deterministic read-only evidence agent.

Policy: search -> read the best matching document -> return evidence, or stop.
No LLM plans, shell, arbitrary paths, network tools, or side-effecting actions.
"""

import time

from .retrieval import KnowledgeBase
from .safety import unsafe_request


class EvidenceAgent:
    def __init__(self, kb=None, max_tool_calls=2, deadline_seconds=2.0):
        self.kb = kb if kb is not None else KnowledgeBase()
        self.max_tool_calls = max_tool_calls
        self.deadline_seconds = deadline_seconds

    def run(self, question):
        started = time.perf_counter()
        trace = []
        base = {"agent_type": "deterministic_evidence_agent", "index_version": self.kb.version}

        def finish(status, answer, evidence=None):
            return {
                **base,
                "status": status,
                "answer": answer,
                "evidence": evidence or [],
                "tool_calls": trace,
                "latency_ms": (time.perf_counter() - started) * 1000,
            }

        def call(name, **arguments):
            if len(trace) >= self.max_tool_calls:
                raise RuntimeError("tool_budget_exhausted")
            if time.perf_counter() - started >= self.deadline_seconds:
                raise RuntimeError("deadline_exceeded")
            tools = {"search_knowledge": self.kb.search, "read_document": self.kb.read_document}
            if name not in tools:
                raise RuntimeError("tool_not_allowed")
            entry = {"tool": name, "status": "started"}
            trace.append(entry)
            try:
                result = tools[name](**arguments)
                if time.perf_counter() - started >= self.deadline_seconds:
                    raise RuntimeError("deadline_exceeded")
                entry["status"] = "ok"
                return result
            except Exception:
                entry["status"] = "error"
                raise

        if unsafe_request(question):
            return finish("refused", "Only read-only knowledge-base questions are supported.")
        try:
            hits = call("search_knowledge", question=question, top_k=1)
            if not hits:
                return finish(
                    "insufficient_evidence", "No supporting document found. Ask a maintainer."
                )
            document = call("read_document", source=hits[0]["metadata"]["source"])
            return finish(
                "evidence_found",
                f"Review [{document['source']}] for the supporting material.",
                [document],
            )
        except RuntimeError as exc:
            if str(exc) in {"tool_budget_exhausted", "deadline_exceeded", "tool_not_allowed"}:
                return finish(str(exc), "Stopped safely. Ask a maintainer to review this request.")
            return finish("tool_error", "A knowledge tool failed. Retry or ask a maintainer.")
        except Exception:
            return finish("tool_error", "A knowledge tool failed. Retry or ask a maintainer.")
