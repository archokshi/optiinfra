"""Application Agent - Quality monitoring and regression detection."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure shared/* modules resolve when the service runs directly.
try:
    _PROJECT_ROOT = Path(__file__).resolve().parents[3]
except IndexError:
    _PROJECT_ROOT = None

if _PROJECT_ROOT and (str_path := str(_PROJECT_ROOT)) not in sys.path:
    sys.path.insert(0, str_path)
