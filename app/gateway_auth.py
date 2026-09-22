from __future__ import annotations
import hashlib
import hmac

class APIKeyAuth:
    def __init__(self, keys: list[str]):
        self._hashes = {hashlib.sha256(k.encode()).hexdigest() for k in keys}

    def validate(self, key: str | None) -> bool:
        if not key:
            return False
        digest = hashlib.sha256(key.encode()).hexdigest()
        return any(hmac.compare_digest(digest, known) for known in self._hashes)
