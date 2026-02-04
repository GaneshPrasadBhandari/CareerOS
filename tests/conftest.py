import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Add repo root so "import apps..." works
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Add src so "import careeros..." works
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
