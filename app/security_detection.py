import re

INJECTION_PATTERNS = [
    r"ignore.{0,80}instructions",
    r"override (the )?system",
    r"reveal (the )?(system prompt|secret|api key|password)",
    r"developer message",
    r"you are now",
    r"execute .*tool",
    r"bypass .*permission",
]

SENSITIVE_PATTERNS = [
    r"sk-[A-Za-z0-9_-]{10,}",
    r"password\s*[:=]\s*\S+",
    r"api[_ -]?key\s*[:=]\s*\S+",
]

def detect_prompt_injection(text: str) -> list[str]:
    hits = []
    lower = text.lower()
    for pat in INJECTION_PATTERNS:
        if re.search(pat, lower, re.I):
            hits.append(pat)
    return hits

def redact_sensitive(text: str) -> str:
    out = text
    for pat in SENSITIVE_PATTERNS:
        out = re.sub(pat, "[REDACTED]", out, flags=re.I)
    return out
