# Operating this knowledge assistant

## Re-indexing documents
The default lexical index is an immutable snapshot built at process startup. After editing a document, restart the API. The index version is a digest of document paths, contents, chunk size, and overlap. It changes when these inputs change. Building the same snapshot twice does not create duplicate chunks.

The optional Chroma ingest command upserts stable chunk identifiers and removes stale chunks after successful encoding. Run dense ingestion offline: replacement is not atomic for concurrent readers. For a production deployment, build a new index separately, verify it, and switch readers to the new version.

## Retrieval failure
An empty index makes the readiness endpoint return HTTP 503. A question without matching terms returns insufficient evidence. A lexical match is not proof that the text answers the question. Inspect the cited passage, especially when a query asks about a topic outside the corpus.

## Evaluation and rollback
Keep a labeled question set separate from the indexed documents. Compare hit rate at k, mean reciprocal rank, and whether retrieved chunks contain the expected evidence. Evaluate chunk configurations on a development set before reporting a separate test set. Do not advertise a small hand-written set as a production benchmark. If a release worsens retrieval, restore the previous corpus and configuration, restart, and compare index versions.
