from pathlib import Path

from careeros.phase3 import next_steps


def test_parser_extract_from_url_and_redacts_pii(monkeypatch):
    html = """
    <html><body>
      <h1>Jane Doe</h1>
      <p>Email: jane@example.com</p>
      <p>Phone: +1 415-555-1111</p>
      <p>Skills: Python FastAPI SQL Docker</p>
    </body></html>
    """

    class R:
        text = html

        def raise_for_status(self):
            return None

    monkeypatch.setattr(next_steps.httpx, "get", lambda *a, **k: R())

    out = next_steps.parser_extract(
        {
            "source_type": "linkedin_url",
            "source_url": "https://linkedin.com/in/demo",
            "private_mode": True,
        }
    )

    assert out["status"] == "ok"
    assert out["privacy"]["private_mode"] is True
    text = out["extracted_text"]
    assert "jane@example.com" in text
    artifact = Path(out["path"]).read_text(encoding="utf-8")
    assert "jane@example.com" not in artifact
    assert "redaction" in artifact.lower()


def test_p25_package_includes_full_tailored_resume():
    resume_text = Path("data/demo/resume_sample_backend_ml.txt").read_text(encoding="utf-8")
    job_text = Path("data/demo/job_description_ml_platform.txt").read_text(encoding="utf-8")

    out = next_steps.p25_automation_run(
        {
            "run_id": "unit_p25_tailored_resume",
            "candidate_name": "Riya Patel",
            "resume": {"source_type": "inline", "text": resume_text},
            "jobs": {"job_texts": [job_text]},
            "privacy": {"private_mode": True},
        }
    )

    assert out["status"] == "ok"
    pkg_text = Path(out["paths"]["package_path"]).read_text(encoding="utf-8")
    assert "tailored_resume" in pkg_text
