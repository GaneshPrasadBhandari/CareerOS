from __future__ import annotations

import hashlib
import re
from typing import Any


EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(r"(?:(?:\+?\d{1,3}[\s.-]?)?(?:\(\d{2,4}\)|\d{2,4})[\s.-]?\d{3}[\s.-]?\d{4,6})")
LINKEDIN_RE = re.compile(r"https?://(?:www\.)?linkedin\.com/[^\s)]+", re.IGNORECASE)


def fingerprint_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def redact_pii(text: str) -> str:
    redacted = EMAIL_RE.sub("[REDACTED_EMAIL]", text)
    redacted = PHONE_RE.sub("[REDACTED_PHONE]", redacted)
    redacted = LINKEDIN_RE.sub("[REDACTED_LINKEDIN_URL]", redacted)
    return redacted


def privacy_metadata(*, raw_text: str, private_mode: bool) -> dict[str, Any]:
    return {
        "private_mode": private_mode,
        "raw_text_sha256": fingerprint_text(raw_text) if raw_text else None,
        "raw_char_count": len(raw_text),
    }

