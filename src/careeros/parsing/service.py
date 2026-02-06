from __future__ import annotations

from pathlib import Path
from datetime import datetime

from careeros.parsing.schema import EvidenceProfile


COMMON_SKILLS = [
    "python", "sql", "mlflow", "dvc", "docker", "kubernetes",
    "aws", "azure", "gcp", "fastapi", "streamlit",
    "langchain", "langgraph", "pydantic", "rag",
    "pytorch", "tensorflow", "scikit-learn", "genai", "llm",
    "vector db", "faiss", "chroma"
]

TITLE_HINTS = [
    "solution architect", "ml engineer", "data scientist",
    "genai architect", "ai engineer", "senior solution architect",
    "sr. solution architect"
]


def extract_skills(text: str) -> list[str]:
    t = text.lower()
    found = [s for s in COMMON_SKILLS if s in t]
    return sorted(set(found))


def extract_titles(text: str) -> list[str]:
    t = text.lower()
    found = [x for x in TITLE_HINTS if x in t]
    return sorted(set(found))


def extract_domains(text: str) -> list[str]:
    t = text.lower()
    domains = []
    if "health" in t or "clinical" in t or "hospital" in t:
        domains.append("healthcare")
    if "supply chain" in t or "logistics" in t:
        domains.append("supply-chain")
    if "finance" in t or "bank" in t:
        domains.append("finance")
    return sorted(set(domains))


def build_profile_from_text(raw_text: str, candidate_name: str | None = None) -> EvidenceProfile:
    return EvidenceProfile(
        candidate_name=candidate_name,
        raw_text=raw_text,
        skills=extract_skills(raw_text),
        titles=extract_titles(raw_text),
        domains=extract_domains(raw_text),
        experiences=[],
        projects=[],
    )


def write_profile(profile: EvidenceProfile, out_dir: str = "outputs/profile") -> Path:
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = Path(out_dir) / f"profile_{profile.version}_{ts}.json"
    path.write_text(profile.model_dump_json(indent=2), encoding="utf-8")
    return path


import json

def latest_profile_path(out_dir: str = "outputs/profile") -> str | None:
    files = sorted(Path(out_dir).glob("profile_*.json"))
    return str(files[-1]) if files else None

def load_profile(path: str | Path) -> EvidenceProfile:
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))
    return EvidenceProfile(**data)
