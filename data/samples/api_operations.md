# Running the local knowledge API

## Health and readiness
The health endpoint reports whether the HTTP process is alive. Readiness checks that the knowledge base contains chunks. Missing generation credentials do not disable local search: generative requests return a controlled HTTP 503 if the Groq key is absent or the provider fails. Provider calls have a fifteen-second timeout and no automatic retries.

## Access and request budgets
Configure RAG_API_KEY to require an X-API-Key header on ask, agent, readiness, and metrics endpoints. Without a configured key the API is a local development service. Bind it to 127.0.0.1. A global per-process rolling window permits sixty requests per minute by default and returns HTTP 429 with Retry-After when exhausted. For a shared public service, use gateway authentication, TLS, and distributed rate limiting.

## Measurement
The process records response statuses and the last thousand request durations. Questions, credentials, and answer text are not written to application logs. The metrics endpoint exposes a process-local p95. Measure end-to-end HTTP latency separately, including client overhead, and record concurrency and warmup. Local retrieval makes no paid model calls. Its hosted provider cost is zero, but CPU, memory, and hosting still cost money. Generation returns actual token usage when available; its dollar cost is unknown until a verified provider price is supplied.
