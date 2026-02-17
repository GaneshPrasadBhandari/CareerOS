from __future__ import annotations

FREE_FIRST_POLICY = {
    "tier1": {
        "description": "Default free/open local stack",
        "providers": ["ollama", "huggingface_open"],
        "models": ["llama3.1:8b-instruct", "qwen2.5:7b-instruct", "mistral:7b-instruct"],
    },
    "tier2": {
        "description": "Low-cost hosted fallback if local fails",
        "providers": ["cheap_hosted_inference"],
    },
    "tier3": {
        "description": "Paid premium only for quality bottlenecks",
        "providers": ["premium_paid_llm"],
    },
}
