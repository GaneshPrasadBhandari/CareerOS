from careeros.integrations.job_boards import sources


def test_discover_job_urls_for_roles_merges_and_caps(monkeypatch):
    def fake_discover_job_urls(*, role: str, location: str, max_per_source: int = 2):
        return {
            "status": "ok",
            "urls": [
                f"https://example.com/{role.replace(' ', '_')}/1",
                "https://example.com/shared/1",
            ],
            "errors": [],
            "sources": ["example"],
        }

    monkeypatch.setattr(sources, "discover_job_urls", fake_discover_job_urls)

    out = sources.discover_job_urls_for_roles(
        roles=["ML Engineer", "Backend Engineer"],
        location="USA",
        max_per_source=2,
        daily_limit=2,
    )

    assert out["status"] == "ok"
    assert len(out["urls"]) == 2
    assert "ML Engineer" in out["urls_by_role"]
    assert "Backend Engineer" in out["urls_by_role"]
