# Model / system card

**System:** RAG Knowledge Assistant 2.0.0. **Review date:** 2026-10-04.

## Purpose and scope

Retrieve system-design notes and project operating instructions, return cited evidence, and optionally generate an answer. The two-tool agent searches and reads the same local corpus. It is a portfolio-scale reference with tests and reproducible measurements, not an independently validated production service.

## Models and data

- Default retrieval: BM25, no trained weights. 8 checked-in Markdown documents, 19 chunks, 200-word chunk limit and up to 40 words of overlap.
- Optional generation/planning: Groq-hosted model configured by `GROQ_MODEL_NAME`, default `llama-3.1-8b-instant`. No model training or fine-tuning was performed here. Provider availability must be verified by the operator.
- Optional dense experiment: pretrained `sentence-transformers/all-MiniLM-L6-v2` and Chroma. Not used for the reported default API results.
- Evaluation: 12 hand-authored development questions for configuration selection, 12 separate test questions, four simple out-of-domain questions. All concern the same tiny corpus. No private or employer data was introduced.

## Evidence

The selected BM25 configuration achieved source hit@1 = 11/12, hit@3 = 12/12, MRR@3 = 0.9583, and expected-evidence hit@3 = 11/12. The term-overlap baseline tied these scores. See `reports/retrieval.json` for every query, configuration, and timing. Phrase matching is an auditable retrieval proxy, not a semantic correctness score.

Actual HTTP benchmarks used one local worker and concurrency one. `/ask` p95 = 1.63 ms and deterministic `/agent` p95 = 2.93 ms for 100 repeated requests each. No paid provider calls occurred. Generated-answer faithfulness, live model tool selection, embedding retrieval quality, concurrent load, and Docker runtime remain unmeasured.

## Controls and known limitations

Inputs have length limits; optional shared-key access, process request limits, readiness, and process metrics are implemented. Tool names and arguments are validated; reads use an allowlisted in-memory lookup. The model-directed loop can read only sources found during the same run. There are tool/turn/time budgets and explicit failure statuses. No action tools are present.

Refusal regexes are bypassable and are not a complete injection defense. Correctly formatted citations do not prove claims are supported. Lexical retrieval can miss synonyms and retrieve unrelated text with overlapping words. No confidence calibration, reranking, tenant-specific document authorization, conversation memory, or distributed index exists. Local tool deadlines do not preempt running Python functions.

## Appropriate and inappropriate use

Suitable for local learning, portfolio review, and retrieval regression experiments. Unsuitable for clinical, financial, legal, or other consequential decisions, private multi-tenant corpora, and publicly exposed autonomous execution. A deployment requires application-specific evaluation and access controls.

## Reproduce and maintenance

Run `python -m rag.evaluate`, `python scripts/benchmark.py`, and `pytest -q`. Restart to load corpus updates and compare the returned index version. Keep labels outside the corpus. Expand the test set with independently authored paraphrases and difficult negatives before claiming generalization. Human-review generated answers and any future tools with side effects.
