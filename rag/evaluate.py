"""Run a small source-and-evidence retrieval regression benchmark offline."""

import json
import platform
import statistics
import time

from .config import BASE_DIR
from .retrieval import KnowledgeBase


def evaluate(kb, rows, method="bm25", k=3):
    results = []
    for row in rows:
        start = time.perf_counter()
        hits = kb.search(row["question"], k, method)
        elapsed = (time.perf_counter() - start) * 1000
        rank = next(
            (i for i, h in enumerate(hits, 1) if h["metadata"]["source"] == row["source"]), 0
        )
        supported = (
            any(
                h["metadata"]["source"] == row["source"]
                and row["evidence"].lower() in h["text"].lower()
                for h in hits
            )
            if rank
            else False
        )
        results.append(
            {
                "id": row["id"],
                "rank": rank,
                "evidence_hit": supported,
                "retrieved_sources": [h["metadata"]["source"] for h in hits],
                "latency_ms": elapsed,
            }
        )
    count = len(results)
    durations = sorted(r["latency_ms"] for r in results)
    return {
        "n": count,
        "hit_rate_at_1": sum(r["rank"] == 1 for r in results) / count,
        "hit_rate_at_3": sum(r["rank"] > 0 for r in results) / count,
        "mrr_at_3": sum(1 / r["rank"] if r["rank"] else 0 for r in results) / count,
        "evidence_hit_at_3": sum(r["evidence_hit"] for r in results) / count,
        "latency_p50_ms": statistics.median(durations),
        "latency_p95_ms": durations[max(0, int(0.95 * count) - 1)],
        "queries": results,
    }


def main():
    rows = [json.loads(s) for s in (BASE_DIR / "evals/questions.jsonl").read_text().splitlines()]
    report = {
        "scope": "28 hand-authored cases; small regression set, not a general benchmark",
        "python": platform.python_version(),
        "platform": platform.platform(),
        "provider_calls": 0,
        "provider_cost_usd": 0,
        "development": {},
    }
    for size, overlap in [(100, 20), (160, 32), (200, 40)]:
        kb = KnowledgeBase(chunk_size=size, overlap=overlap)
        report["development"][f"{size}/{overlap}"] = evaluate(
            kb, [r for r in rows if r["split"] == "dev"]
        )
    # Predeclared selection: best evidence hit, then MRR, then fewer total chunks.
    choice = max(
        report["development"],
        key=lambda key: (
            report["development"][key]["evidence_hit_at_3"],
            report["development"][key]["mrr_at_3"],
            int(key.split("/")[0]),
        ),
    )
    size, overlap = map(int, choice.split("/"))
    kb = KnowledgeBase(chunk_size=size, overlap=overlap)
    report.update(
        {
            "selected_chunk_words": size,
            "selected_overlap_words": overlap,
            "index_version": kb.version,
            "documents": len(kb.documents),
            "chunks": len(kb.chunks),
            "test": {},
        }
    )
    for method in ["overlap", "bm25"]:
        report["test"][method] = evaluate(kb, [r for r in rows if r["split"] == "test"], method)
    report["out_of_domain"] = [
        {"question": r["question"], "returned_evidence": bool(kb.search(r["question"]))}
        for r in rows
        if r["split"] == "ood"
    ]
    output = BASE_DIR / "reports/retrieval.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps({k: v for k, v in report.items() if k not in {"development", "test"}}, indent=2)
    )
    print(
        json.dumps(
            {m: {k: v for k, v in r.items() if k != "queries"} for m, r in report["test"].items()},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
