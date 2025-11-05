"""OptiInfra Performance Agent."""

from __future__ import annotations

import sys
from pathlib import Path

__version__ = "0.1.0"

# Allow imports from the repo root (shared/* packages) when running directly.
try:
    _PROJECT_ROOT = Path(__file__).resolve().parents[3]
except IndexError:
    _PROJECT_ROOT = None

if _PROJECT_ROOT and (str_path := str(_PROJECT_ROOT)) not in sys.path:
    sys.path.insert(0, str_path)
