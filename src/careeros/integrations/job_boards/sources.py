from __future__ import annotations

import os
from typing import Any

import httpx


TOP_8_SOURCES = [
    "linkedin.com/jobs",
    "indeed.com",
    "wellfound.com/jobs",
    "dice.com/jobs",
    "builtin.com/jobs",
    "glassdoor.com/Job",
    "ziprecruiter.com/jobs",
    "usajobs.gov",
]


def discover_job_urls(*, role: str, location: str, max_per_source: int = 2) -> dict[str, Any]:
    """Discover candidate job links for top sources via Serper (if API key configured)."""
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        return {
            "status": "degraded",
            "urls": [],
            "errors": ["SERPER_API_KEY not configured; skipping web discovery."],
            "sources": TOP_8_SOURCES,
        }

    urls: list[str] = []
    errors: list[str] = []

    headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
    with httpx.Client(timeout=20) as client:
        for src in TOP_8_SOURCES:
            query = f"{role} jobs {location} site:{src}"
            try:
                r = client.post("https://google.serper.dev/search", headers=headers, json={"q": query, "num": max_per_source})
                r.raise_for_status()
                data = r.json()
                for item in (data.get("organic") or [])[:max_per_source]:
                    link = item.get("link")
                    if isinstance(link, str) and link.startswith("http"):
                        urls.append(link)
            except Exception as e:  # noqa: BLE001
                errors.append(f"{src}: {e}")

    # stable dedupe
    unique_urls = list(dict.fromkeys(urls))
    return {
        "status": "ok" if unique_urls else "degraded",
        "urls": unique_urls,
        "errors": errors,
        "sources": TOP_8_SOURCES,
    }

