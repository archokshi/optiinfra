"""Resource Agent - GPU/CPU/memory resource optimization agent."""

from __future__ import annotations

import sys
from pathlib import Path

__version__ = "1.0.0"

# Make sure imports from shared/* succeed when executing the service directly.
try:
    _PROJECT_ROOT = Path(__file__).resolve().parents[3]
except IndexError:
    _PROJECT_ROOT = None

if _PROJECT_ROOT and (str_path := str(_PROJECT_ROOT)) not in sys.path:
    sys.path.insert(0, str_path)
