from careeros.jobs.service import build_jobpost_from_text

def test_job_ingest_extracts_keywords():
    txt = "Required: Python, Docker, Kubernetes. Preferred: MLflow and DVC."
    j = build_jobpost_from_text(txt)
    assert "python" in j.keywords
    assert "docker" in j.keywords
    assert "kubernetes" in j.keywords
