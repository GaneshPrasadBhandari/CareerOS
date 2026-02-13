import sys
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Add repo root so "import apps..." works
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Add src so "import careeros..." works
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# Keep local test runs deterministic and offline-safe by default.
# This prevents accidental external telemetry attempts (e.g., LangSmith 403 noise)
# when user shells export tracing-related environment variables.
os.environ.setdefault("LANGCHAIN_TRACING_V2", "false")
os.environ.setdefault("LANGSMITH_TRACING", "false")
os.environ.setdefault("LANGCHAIN_ENDPOINT", "")
os.environ.setdefault("LANGSMITH_ENDPOINT", "")
