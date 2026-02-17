from __future__ import annotations

import os
from typing import Any

import httpx


def generate_summary_with_fallback(*, run_id: str, score: float) -> dict[str, Any]:
    """Tiered generation fallback:
    tier1: ollama local
    tier2: HF inference (if token exists)
    tier3: graceful degraded response
    """
    ollama_base = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    ollama_model = os.getenv("OLLAMA_SUMMARY_MODEL", "llama3")
    prompt = f"Write 2 concise lines summarizing run {run_id} with match score {score}."

    try:
        r = httpx.post(
            f"{ollama_base}/api/generate",
            json={"model": ollama_model, "prompt": prompt, "stream": False},
            timeout=30,
        )
        if r.status_code == 200:
            return {"status": "ok", "tier": "tier1", "provider": "ollama", "text": r.json().get("response", "")}
    except Exception:
        pass

    hf_token = os.getenv("HUGGINGFACE_API_KEY") or os.getenv("HF_TOKEN")
    hf_model = os.getenv("HF_SUMMARY_MODEL", "google/flan-t5-base")
    if hf_token:
        try:
            r = httpx.post(
                f"https://api-inference.huggingface.co/models/{hf_model}",
                headers={"Authorization": f"Bearer {hf_token}"},
                json={"inputs": prompt},
                timeout=45,
            )
            if r.status_code == 200:
                data = r.json()
                text = ""
                if isinstance(data, list) and data:
                    text = data[0].get("generated_text", "")
                elif isinstance(data, dict):
                    text = data.get("generated_text", "")
                return {"status": "ok", "tier": "tier2", "provider": "huggingface", "text": text}
        except Exception:
            pass

    summary = (
        f"Run {run_id}: profile-job match completed with score {score:.2f}. "
        "Generated package and guardrails status are available in run artifacts."
    )
    return {
        "status": "ok",
        "tier": "tier3",
        "provider": "deterministic_fallback",
        "text": summary,
        "warning": "Ollama/HF unavailable, used deterministic summary fallback.",
    }
