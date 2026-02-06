from __future__ import annotations
from pathlib import Path
from datetime import datetime

from careeros.jobs.schema import JobPost


KEYWORDS = [
    "python", "sql", "mlflow", "dvc", "docker", "kubernetes",
    "aws", "azure", "gcp", "fastapi", "streamlit",
    "rag", "langchain", "langgraph", "pydantic",
    "pytorch", "tensorflow", "scikit-learn", "llm", "genai"
]


def extract_keywords(text: str) -> list[str]:
    t = text.lower()
    found = [k for k in KEYWORDS if k in t]
    return sorted(set(found))


def build_jobpost_from_text(raw_text: str, url: str | None = None) -> JobPost:
    return JobPost(
        source="paste" if url is None else "url",
        url=url,
        raw_text=raw_text,
        keywords=extract_keywords(raw_text),
    )


def write_jobpost(job: JobPost, out_dir: str = "outputs/jobs") -> Path:
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = Path(out_dir) / f"job_post_{job.version}_{ts}.json"
    path.write_text(job.model_dump_json(indent=2), encoding="utf-8")
    return path


import json

def latest_job_post_path(out_dir: str = "outputs/jobs") -> str | None:
    files = sorted(Path(out_dir).glob("job_post_*.json"))
    return str(files[-1]) if files else None

def load_job_post(path: str | Path) -> JobPost:
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))
    return JobPost(**data)
