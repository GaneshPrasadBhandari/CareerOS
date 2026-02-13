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

# Keep local test runs deterministic and offline-safe.
# Force-disable tracing even when shells export tracing env vars.
os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["LANGSMITH_TRACING"] = "false"
os.environ["LANGCHAIN_ENDPOINT"] = ""
os.environ["LANGSMITH_ENDPOINT"] = ""
os.environ.pop("LANGCHAIN_API_KEY", None)
os.environ.pop("LANGSMITH_API_KEY", None)
