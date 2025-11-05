"""OptiInfra Cost Agent - AI-powered cost optimization."""

from __future__ import annotations

import sys
from pathlib import Path

__version__ = "0.1.0"

# Ensure the repository root is on sys.path so shared/* imports resolve when the
# service is executed directly (e.g., python src/main.py or uvicorn src.main:app).
try:
    _PROJECT_ROOT = Path(__file__).resolve().parents[3]
except IndexError:
    _PROJECT_ROOT = None

if _PROJECT_ROOT and (str_path := str(_PROJECT_ROOT)) not in sys.path:
    sys.path.insert(0, str_path)
