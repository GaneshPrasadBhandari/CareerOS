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


def _job_text_from_item(item: dict[str, Any], role: str, location: str) -> str:
    title = str(item.get("title") or role)
    snippet = str(item.get("snippet") or "")
    link = str(item.get("link") or "")
    return (
        f"Role: {title}\n"
        f"Location: {location}\n"
        f"Source URL: {link}\n"
        f"Description: {snippet}\n"
    )


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
    job_texts: list[str] = []
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
                    job_texts.append(_job_text_from_item(item, role=role, location=location))
            except Exception as e:  # noqa: BLE001
                errors.append(f"{src}: {e}")

    # Tavily fallback enrichment
    tavily_key = os.getenv("TAVILY_API_KEY")
    if tavily_key:
        with httpx.Client(timeout=20) as client:
            for src in TOP_8_SOURCES:
                query = f"{role} jobs {location} site:{src}"
                try:
                    r = client.post(
                        "https://api.tavily.com/search",
                        json={"api_key": tavily_key, "query": query, "max_results": max_per_source},
                    )
                    r.raise_for_status()
                    data = r.json()
                    for item in (data.get("results") or [])[:max_per_source]:
                        link = item.get("url")
                        if isinstance(link, str) and link.startswith("http"):
                            urls.append(link)
                        job_texts.append(
                            _job_text_from_item(
                                {
                                    "title": item.get("title"),
                                    "snippet": item.get("content"),
                                    "link": item.get("url"),
                                },
                                role=role,
                                location=location,
                            )
                        )
                except Exception as e:  # noqa: BLE001
                    errors.append(f"tavily:{src}: {e}")

    unique_urls = list(dict.fromkeys(urls))
    return {
        "status": "ok" if unique_urls else "degraded",
        "urls": unique_urls,
        "job_texts": job_texts,
        "errors": errors,
        "sources": TOP_8_SOURCES,
    }


def discover_job_urls_for_roles(
    *,
    roles: list[str],
    location: str,
    max_per_source: int = 2,
    daily_limit: int = 20,
) -> dict[str, Any]:
    """Multi-role discovery with stable dedupe and daily cap."""
    role_urls: dict[str, list[str]] = {}
    all_urls: list[str] = []
    all_errors: list[str] = []
    all_job_texts: list[str] = []

    role_list = [r.strip() for r in roles if isinstance(r, str) and r.strip()]
    if not role_list:
        role_list = ["Software Engineer"]

    for role in role_list:
        out = discover_job_urls(role=role, location=location, max_per_source=max_per_source)
        urls = out.get("urls", [])
        role_urls[role] = urls
        all_urls.extend(urls)
        all_job_texts.extend(out.get("job_texts", []))
        all_errors.extend([f"{role}: {e}" for e in out.get("errors", [])])

    unique_urls = list(dict.fromkeys(all_urls))[: max(1, daily_limit)]
    return {
        "status": "ok" if unique_urls else "degraded",
        "urls": unique_urls,
        "job_texts": all_job_texts[: max(1, daily_limit)],
        "urls_by_role": role_urls,
        "errors": all_errors,
        "daily_limit": daily_limit,
        "sources": TOP_8_SOURCES,
    }
