from __future__ import annotations

import os
from dotenv import load_dotenv
from pydantic import BaseModel


class Settings(BaseModel):
    env: str = "dev"
    demo_mode: bool = True
    orchestration_mode: str = "pipeline"

    openai_api_key: str | None = None
    huggingface_api_key: str | None = None
    tavily_api_key: str | None = None
    serper_api_key: str | None = None


def load_settings() -> Settings:
    # Loads .env into environment variables (if .env exists)
    load_dotenv(override=False)

    def as_bool(value: str | None, default: bool) -> bool:
        if value is None:
            return default
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}

    return Settings(
        env=os.getenv("ENV", "dev"),
        demo_mode=as_bool(os.getenv("DEMO_MODE"), True),
        orchestration_mode=os.getenv("ORCHESTRATION_MODE", "pipeline"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        huggingface_api_key=os.getenv("HUGGINGFACE_API_KEY"),
        tavily_api_key=os.getenv("TAVILY_API_KEY"),
        serper_api_key=os.getenv("SERPER_API_KEY"),
    )
