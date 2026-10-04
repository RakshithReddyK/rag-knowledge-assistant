# Sample knowledge base

`data/samples/` contains eight small Markdown documents: five system-design
explainers (HTTP caching, Bloom filters, database indexing, consistent hashing,
and rate limiting) and three operating runbooks added for this project
(retrieval operations, agent safety, and API operations).

The default API builds an immutable BM25 snapshot from `data/samples/` at first
use. Add `.md`/`.txt` files beneath that directory and restart to re-index. No
private employer documents are included. The runbooks describe this demo's
operating contract; they are not records of a real production incident.

The optional dense experiment uses `python -m rag.ingest`, which walks all of
`data/` while excluding files named `README.md`. It requires extra dependencies
and downloads the pretrained embedding model. Evaluation labels live outside
the corpus in `evals/` and must not be indexed.
