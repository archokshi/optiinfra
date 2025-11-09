"""
Shared pytest configuration for data-collector tests.

Ensures `src.*` imports resolve when the suite is executed from the monorepo
root (where `pythonpath` would otherwise omit this service).
"""

from __future__ import annotations

import sys
from pathlib import Path

SERVICE_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = SERVICE_ROOT / "src"

if SRC_PATH.exists():
    sys.path.insert(0, str(SRC_PATH))
