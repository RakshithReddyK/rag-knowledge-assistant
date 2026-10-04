# Evidence agent safety contract

## Two tools
The evidence agent has exactly two read-only tools: search_knowledge searches the local corpus; read_document returns an indexed document by its allowed source name. A source argument is looked up in an in-memory map. It is never used as a filesystem path. The agent cannot run a shell, write files, visit a URL, send a message, or change an account.

## Budget and stopping
The deterministic policy searches once, reads the best matching source once, and returns evidence. The maximum tool count is two. A missing result stops with insufficient_evidence. A failed tool stops with tool_error and directs the caller to a maintainer. Exceeding the tool budget stops with tool_budget_exhausted. The deadline is checked between and after local calls; it does not forcibly interrupt a running Python function.

## Untrusted input
Obvious attempts to reveal secrets, run commands, or ignore instructions are refused. Pattern checks are defense in depth and can be bypassed; the actual boundary is the read-only tool allowlist. Retrieved text is untrusted evidence and is never evaluated as code. The optional generation endpoint cites allowlisted retrieved sources, but a valid citation alone does not prove an answer is correct.
