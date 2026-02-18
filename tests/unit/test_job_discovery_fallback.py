from careeros.integrations.job_boards.sources import discover_job_urls


def test_discover_job_urls_returns_fallback_when_serper_missing(monkeypatch):
    monkeypatch.delenv("SERPER_API_KEY", raising=False)
    out = discover_job_urls(role="ML Engineer", location="USA", max_per_source=2)
    assert out["status"] == "degraded"
    assert len(out["urls"]) >= 1
    assert len(out.get("job_texts", [])) >= 1
