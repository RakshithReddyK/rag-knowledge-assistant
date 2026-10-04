# Portfolio audit — 2026-10-04

Public profile: https://github.com/RakshithReddyK. Audit based on checked-in source, not README claims alone. Original order observed on the profile was ETA, sepsis, fraud, risk platform. No referenced external scoring table was provided; this audit uses the notebook-versus-runnable-system criteria in the request.

## Current pins at the start of this work

| Repository | Honest classification | Evidence and gap | Recommendation |
|---|---|---|---|
| eta-dynamic-routing-ml-service | Incomplete service scaffold | FastAPI route and feature code exist; referenced model training/prediction modules are missing. CI lives under `infra/github/workflows`, not the active Actions path. A virtual environment is tracked. | Unpin until repaired; do not present the README's MAE as verified. |
| sepsis-early-detection-ml | Packaged training pipeline, not a served system | Training CLI, serialized model, evaluation files and leakage tests exist. No inference API. README discloses pre-split SMOTE leakage in reference data. | Optional fourth pin, clearly labeled synthetic training study. |
| fraud-detection-ML | Runnable model-serving system | Generator, feature engineering, trainer, FastAPI, tests and optional Redis exist. This change fixes preprocessing leakage, Redis failure behavior, cache versioning and input validation; adds measured evaluation and a model card. | Pin second. |
| ai-risk-intelligence-platform | Partial component scaffold | Fusion module, synthetic generator, safety helpers, metrics and unit tests exist. Referenced API, Terraform, full RAG, Makefile and many linked documents do not exist in the checked-in tree. | Unpin; replace production/compliance claims with current status. |

No repository was determined to be a copied tutorial or shared assignment from this source audit. That provenance requires the owner's confirmation; no files were deleted on that assumption.

## Proposed pin order

| Position | Repository | Proposed GitHub About description |
|---|---|---|
| 1 | rag-knowledge-assistant | Knowledge API with measured BM25 retrieval, optional LLM RAG, and a bounded two-tool agent. FastAPI, evaluation, failure handling, and documented limits. |
| 2 | fraud-detection-ML | Synthetic fraud-scoring service with XGBoost, FastAPI, train-only preprocessing, baseline evaluation, versioned caching, and a model card. |
| 3 | imdb-sentiment-distilbert-app | IMDB sentiment experiments with a TF-IDF baseline, DistilBERT, FastAPI, and Streamlit. Fine-tuned weights must be produced locally. |
| 4 | sepsis-early-detection-ml | Synthetic sepsis training pipeline with leakage checks and cross-validation. Reference data has pre-split SMOTE limitations; no clinical validation. |

The IMDB API exists but model weights are absent, and README notebook paths need correction before treating it as a plug-and-play demo. Keep four pins rather than filling six slots with weaker evidence. Keep historical notebooks public as learning history; deletion is unnecessary.

For currently pinned projects being demoted:

- **ETA:** `ETA prediction scaffold with data and feature modules plus a FastAPI interface. Training modules and runnable evaluation are unfinished.`
- **Risk platform:** `Experimental risk-platform components: synthetic data, fusion model code, safety helpers, and monitoring metrics. End-to-end platform remains unfinished.`

## Other repository findings

| Repository | Classification |
|---|---|
| NYC-Taxi-ETL-Pipeline | Notebook ETL experiment plus a CSV; no deployable service. |
| Batch-Ingestion-Pipeline-for-E-commerce-Transactions | Glue job export and sample data; cloud setup is manual, not a self-contained system. |
| fraud-detection-pipeline-redshift-glue | Batch Glue/Redshift job export; the README's real-time language exceeds the implementation. |
| rag-knowledge-assistant | Existing RAG prototype, extended in this work with evaluated local retrieval and bounded agent behavior. |
| imdb-sentiment-distilbert-app | Notebook-trained model with API/UI code; absent weights prevent immediate reproduction. |

## Verification boundary

RAG local retrieval/API/tools and fraud training/serving were executed in this work. Other projects received source-level inspection only. Published metrics identify their datasets, seeds, hardware scope, and failure cases. Live hosted-model generation and public deployment were not tested. Pin order and About descriptions require a separate GitHub UI change; this document is the exact proposed update, not a claim that the profile has already changed.
