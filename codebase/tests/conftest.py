"""pytest configuration — adds hackathon/ to sys.path."""

import sys
from pathlib import Path

# Ensure hackathon/ is importable for both src/ and backend/
_ROOT = str(Path(__file__).parent.parent)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
