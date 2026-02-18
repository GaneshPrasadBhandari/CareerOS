from __future__ import annotations

import json
import math
import os
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9_\-]{1,40}")


@dataclass
class VectorRecord:
    item_id: str
    item_type: str
    text: str
    metadata: dict[str, Any]


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in TOKEN_RE.findall(text or "")]


def _hash_embed(text: str, dims: int = 256) -> list[float]:
    vec = [0.0] * dims
    counts = Counter(_tokenize(text))
    for tok, count in counts.items():
        vec[hash(tok) % dims] += float(count)
    norm = math.sqrt(sum(v * v for v in vec))
    return [v / norm for v in vec] if norm > 0 else vec


def _embedding_backend() -> tuple[str, Any | None]:
    try:
        from sentence_transformers import SentenceTransformer

        model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        return f"sentence_transformers:{model_name}", SentenceTransformer(model_name)
    except Exception:
        return "hash", None


def _embed_texts(texts: list[str]) -> tuple[str, list[list[float]]]:
    backend, model = _embedding_backend()
    if model is None:
        return backend, [_hash_embed(t) for t in texts]
    return backend, [list(map(float, v)) for v in model.encode(texts).tolist()]


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    n = min(len(v1), len(v2))
    if n == 0:
        return 0.0
    return float(max(-1.0, min(1.0, sum(v1[i] * v2[i] for i in range(n)))))


def _index_to_local_file(run_id: str, records: list[VectorRecord], vectors: list[list[float]], backend: str) -> str:
    out_dir = Path("outputs/phase3/vectors")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"vector_index_{run_id}.json"
    out_path.write_text(
        json.dumps(
            {
                "run_id": run_id,
                "vector_backend": backend,
                "items": [
                    {
                        "item_id": rec.item_id,
                        "item_type": rec.item_type,
                        "text_preview": rec.text[:500],
                        "metadata": rec.metadata,
                        "vector": vec,
                    }
                    for rec, vec in zip(records, vectors)
                ],
            }
        ),
        encoding="utf-8",
    )
    return str(out_path)


def index_records(run_id: str, records: list[VectorRecord]) -> dict[str, Any]:
    vector_db = os.getenv("VECTOR_DB", "chroma").lower().strip()
    embedding_backend, vectors = _embed_texts([r.text for r in records])
    local_path = _index_to_local_file(run_id, records, vectors, backend=embedding_backend)

    details: dict[str, Any] = {
        "status": "ok",
        "backend": vector_db,
        "embedding_backend": embedding_backend,
        "path": local_path,
        "count": len(records),
    }

    if vector_db == "qdrant":
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams, PointStruct

            url = os.getenv("QDRANT_URL")
            api_key = os.getenv("QDRANT_API_KEY")
            if not url:
                raise ValueError("QDRANT_URL is required when VECTOR_DB=qdrant")
            client = QdrantClient(url=url, api_key=api_key)
            collection = os.getenv("QDRANT_COLLECTION", "careeros_runs")
            size = len(vectors[0]) if vectors else 256
            client.recreate_collection(collection_name=collection, vectors_config=VectorParams(size=size, distance=Distance.COSINE))
            points = [
                PointStruct(id=i + 1, vector=vectors[i], payload={"run_id": run_id, **records[i].metadata, "item_type": records[i].item_type})
                for i in range(len(records))
            ]
            if points:
                client.upsert(collection_name=collection, points=points)
            details["remote"] = {"provider": "qdrant", "collection": collection, "upserted": len(points)}
        except Exception as e:
            details["status"] = "degraded"
            details["remote_error"] = str(e)

    elif vector_db == "chroma":
        try:
            import chromadb

            persist_dir = os.getenv("CHROMA_PERSIST_DIR", "outputs/phase3/chroma")
            client = chromadb.PersistentClient(path=persist_dir)
            collection_name = os.getenv("CHROMA_COLLECTION", "careeros_runs")
            collection = client.get_or_create_collection(name=collection_name)
            ids = [f"{run_id}:{r.item_type}:{r.item_id}" for r in records]
            metadatas = [{"run_id": run_id, **r.metadata, "item_type": r.item_type} for r in records]
            collection.upsert(ids=ids, documents=[r.text for r in records], embeddings=vectors, metadatas=metadatas)
            details["remote"] = {"provider": "chroma", "collection": collection_name, "persist_dir": persist_dir, "upserted": len(ids)}
        except Exception as e:
            details["status"] = "degraded"
            details["remote_error"] = str(e)

    else:
        details["note"] = "Unsupported VECTOR_DB value. Indexed locally only."

    return details


def semantic_rank_jobs(*, resume_text: str, jobs: list[dict[str, Any]], weight: float = 0.35) -> dict[str, Any]:
    backend, vecs = _embed_texts([resume_text] + [str(j.get("raw_text") or "") for j in jobs])
    if not vecs:
        return {"status": "degraded", "jobs": [], "weight": weight, "embedding_backend": backend}
    resume_vec = vecs[0]
    scored: list[dict[str, Any]] = []
    for i, job in enumerate(jobs, start=1):
        sim = (cosine_similarity(resume_vec, vecs[i]) + 1.0) / 2.0
        scored.append({**job, "semantic_similarity": round(float(sim), 4), "semantic_weight": weight})
    scored.sort(key=lambda x: x.get("semantic_similarity", 0.0), reverse=True)
    return {"status": "ok", "jobs": scored, "weight": weight, "embedding_backend": backend}


def vector_capabilities() -> dict[str, Any]:
    return {
        "vector_db": os.getenv("VECTOR_DB", "chroma"),
        "embedding_model": os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
        "qdrant_configured": bool(os.getenv("QDRANT_URL")),
        "serper_configured": bool(os.getenv("SERPER_API_KEY")),
        "tavily_configured": bool(os.getenv("TAVILY_API_KEY")),
        "scrapingbee_configured": bool(os.getenv("SCRAPINGBEE_API_KEY")),
        "ollama_host": os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434"),
        "hf_configured": bool(os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_API_KEY")),
    }
