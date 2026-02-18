from careeros.integrations.job_boards import sources


class _Resp:
    def __init__(self, text: str, status_code: int = 200):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError("bad")


def test_fetch_job_page_text_direct_success(monkeypatch):
    def fake_get(url, timeout=12, follow_redirects=True):
        return _Resp("<html><body>job desc</body></html>")

    monkeypatch.setattr(sources.httpx, "get", fake_get)
    out = sources.fetch_job_page_text("https://example.com/job")
    assert out["status"] == "ok"
    assert "direct_httpx" in out["notes"]


def test_fetch_job_page_text_jina_fallback(monkeypatch):
    calls = {"n": 0}

    def fake_get(url, timeout=12, follow_redirects=True):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("blocked")
        return _Resp("clean text from jina")

    monkeypatch.setattr(sources.httpx, "get", fake_get)
    out = sources.fetch_job_page_text("https://example.com/job")
    assert out["status"] == "ok"
    assert "jina_reader" in out["notes"]
