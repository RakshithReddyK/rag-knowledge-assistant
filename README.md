# RAG Knowledge Assistant

A local knowledge API for system-design notes and operating runbooks, with measured retrieval, optional LLM generation, and a bounded two-tool evidence agent.

**Runnable today:** keyless BM25 retrieval, cited excerpts, FastAPI, two read-only agent tools, request validation, optional API-key protection, readiness, process metrics, tests, and a reproducible evaluation. **Live LLM quality and public deployment are not validated.**

## Try it in five minutes

```bash
git clone https://github.com/RakshithReddyK/rag-knowledge-assistant.git
cd rag-knowledge-assistant
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-test.txt
cp .env.example .env
uvicorn api.main:app --host 127.0.0.1 --port 9000
```

No API key, downloaded model, or database is needed for the default demo. In another terminal:

```bash
curl http://127.0.0.1:9000/ready
curl http://127.0.0.1:9000/ask -H 'Content-Type: application/json' \
  -d '{"question":"How does token bucket rate limiting allow bursts?"}'
curl http://127.0.0.1:9000/agent -H 'Content-Type: application/json' \
  -d '{"question":"How does token bucket rate limiting allow bursts?"}'
```

`/ask` defaults to **extractive evidence**, not an LLM-written answer. `/agent` defaults to a deterministic search → read policy. Both return sources and an index version. Swagger is at `/docs`.

## What is actually implemented

| Path | Behavior |
|---|---|
| `POST /ask` | BM25 retrieval; `extractive` excerpts or optional `generative` answer |
| `POST /agent` | `deterministic` two-tool policy or optional `llm` tool-calling loop |
| `GET /health` | Process liveness |
| `GET /ready` | Nonempty corpus, document/chunk count, index version |
| `GET /metrics` | Process-local request counts and rolling latency p95 |
| `python -m rag.evaluate` | Labeled retrieval comparison and chunk-size experiment |
| `python scripts/benchmark.py` | Real loopback HTTP latency; one worker, concurrency one |

The default index is built once from `data/samples/` and kept in memory. Restart after changing documents. Stable chunk identifiers and a content/configuration digest make repeated builds reproducible. Symlinks and files over 1 MB are excluded or rejected. This is a small-corpus implementation, not a distributed search service.

## Optional generated answers and model-directed agent

Set `GROQ_API_KEY` and, if necessary, `GROQ_MODEL_NAME` in `.env`, then restart the API. Credentials stay server-side.

```bash
curl http://127.0.0.1:9000/ask -H 'Content-Type: application/json' \
  -d '{"question":"How do Bloom filters work?","mode":"generative"}'
curl http://127.0.0.1:9000/agent -H 'Content-Type: application/json' \
  -d '{"question":"How do Bloom filters work?","mode":"llm"}'
```

The Groq adapter uses a 15-second request timeout, no automatic retries, temperature zero, and a 500-token output cap. Missing credentials and provider failures produce controlled failures. Generation returns actual provider token counts when available. Dollar cost is `null` because no verified price is configured.

**Validation boundary:** provider behavior is tested with controlled responses. No live Groq generation or model-directed conversation was executed for this release. Citation validation checks source identifiers, not factual entailment; an answer with valid citations can still be wrong.

## Agent contract and failure paths

| Tool | Allowed action |
|---|---|
| `search_knowledge(question, top_k)` | Search the local corpus; validated arguments |
| `read_document(source)` | Read only an indexed source; never open a caller-supplied path |

The deterministic agent makes at most two calls. The model-directed agent allows at most four calls and four planning turns within a 30-second total budget; its read tool accepts only sources returned by search in that run. Neither mode has a shell, arbitrary network access, write tools, or external side effects.

Failures are explicit: `refused`, `insufficient_evidence`, `invalid_tool_arguments`, `tool_not_allowed`, `tool_error`, `tool_budget_exhausted`, `turn_budget_exhausted`, `deadline_exceeded`, `provider_unavailable`, and `invalid_citations`. The deterministic deadline is checked around local calls; it cannot forcibly cancel a stuck Python function. Pattern-based refusals are only defense in depth. The read-only tool boundary is the primary control.

## Retrieval evaluation

See [raw retrieval results](reports/retrieval.json), [questions](evals/questions.jsonl), and [model/system card](MODEL_CARD.md).

The corpus has **8 documents and 19 chunks**: five system-design explainers plus three operating runbooks. There are **12 development, 12 test, and 4 out-of-domain questions**, all hand-authored for this repository. The development set compares 100/20, 160/32, and 200/40 word chunk/overlap settings. The predeclared selection rule is evidence hit rate, then MRR, then larger chunks. It selected **200 words / 40 words overlap**.

| Test metric (12 questions) | Term-overlap baseline | BM25 |
|---|---:|---:|
| Correct source ranked first | 11/12 | 11/12 |
| Correct source in top three | 12/12 | 12/12 |
| Mean reciprocal rank @3 | 0.9583 | 0.9583 |
| Expected evidence phrase in top three | 11/12 | 11/12 |

**BM25 did not beat the simpler baseline on this set.** Four obvious out-of-domain questions returned no evidence. Lexical overlap can still produce irrelevant hits for less obvious out-of-domain queries; there is no calibrated relevance threshold. This tiny regression set is not an independent production benchmark, and source retrieval is not answer-quality evaluation. Per-question failures remain in the report.

Chunking prefers sentence/paragraph boundaries, carries trailing sentences within the overlap budget, and splits oversized sentences to enforce the hard limit. Counts are whitespace-delimited **words**, not model tokens. The chosen overlap is a maximum, not a guaranteed duplicate length.

## Latency and cost

[Captured HTTP measurements](reports/latency.json) include 100 sequential requests per endpoint after five warmups, one Uvicorn worker, a persistent loopback client, and the same repeated query. In this run, p95 was **1.63 ms for `/ask`** and **2.93 ms for the deterministic `/agent`**. These are tiny-corpus local measurements; they exclude LLM inference and are not throughput or production latency promises.

The measured paths made zero hosted-model calls, so their provider charge is $0. Compute and hosting costs are not zero. Generated requests expose token usage; price them with the provider's applicable rate before deployment.

## Test and reproduce

```bash
pytest -q
ruff check .
python -m rag.evaluate
python scripts/benchmark.py
# Also exercise the retained Chroma adapter without downloading embedding weights:
pip install chromadb==1.5.9
pytest -q tests/test_vectorstore.py
```

Tests cover actual local API requests, corpus retrieval, index replacement, oversized chunks, authentication, 429/503 responses, tool allowlists, invalid arguments, budgets, provider failures, and citation validation. Model-planning and generation tests use controlled provider responses. CI runs Python 3.11 and 3.12 and uploads its retrieval report.

## Optional dense retrieval and UI

The earlier MiniLM/Chroma implementation remains available as a separate experiment; **the default API and published retrieval scores use BM25**.

```bash
pip install -r requirements.txt
python -m rag.ingest
python -c "from rag.vectorstore import VectorStore; print(VectorStore().query('What is a Bloom filter?', top_k=3))"
streamlit run streamlit_app.py
```

Dense ingestion upserts stable IDs, then removes stale chunks. Run it offline; replacement is not atomic for concurrent readers. Existing pre-migration Chroma collections may use the old distance metric: rebuild into a fresh directory before comparing dense results. Real embedding retrieval was not benchmarked in this release; adapter tests use a deterministic fake embedder.

## Running and operating

```bash
docker compose up --build api
# Optional frontend with its extra dependencies:
docker compose --profile ui up --build api frontend
```

The container runs as a non-root user. Published ports bind to loopback. Docker build/runtime was not exercised in this environment. Set `RAG_API_KEY` to enable `X-API-Key` protection; the optional UI forwards the server-side environment key. The rolling request limit defaults to 60 per minute **per process**, shared across callers. Application logs omit question text, answers, and credentials.

Before a shared deployment: add gateway TLS and identity, per-user authorization, distributed rate limits/metrics, corpus access controls, load testing, and evaluated answer quality. The current shared key is not tenant isolation. No private employer documents are bundled.

[Portfolio audit and proposed pins](docs/PORTFOLIO_AUDIT.md) · [Operations notes](data/samples/api_operations.md)
