"""Defense in depth; the real boundary is read-only, allowlisted tools."""

import re

_PATTERN = re.compile(
    r"ignore\s+(?:all\s+|the\s+|previous\s+)*(?:instructions|rules|prompts)|"
    r"(?:reveal|print|show|steal|exfiltrate)\s+.{0,40}(?:secret|password|api.key|system.prompt)|"
    r"(?:execute|run)\s+(?:a\s+)?(?:shell|command|code)|"
    r"(?:delete|drop)\s+(?:all|the|my|database|files)|"
    r"(?:/etc/passwd|\.\./|https?://)",
    re.IGNORECASE,
)


def unsafe_request(text):
    return bool(_PATTERN.search(text))
