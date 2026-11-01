"""Filesystem locations for the backend.

Paths are relative to this package (or an override directory) so the app can
run outside a container that hardcoded an absolute install path.
"""

from __future__ import annotations

import os
from pathlib import Path

BACKEND_DIR = Path(os.environ.get("NIND_BACKEND_DIR", Path(__file__).resolve().parent)).resolve()
UPLOADS_DIR = Path(os.environ.get("NIND_UPLOADS_DIR", BACKEND_DIR / "uploads")).resolve()
WORK_DIR = Path(os.environ.get("NIND_WORK_DIR", BACKEND_DIR / "video_work")).resolve()


def ensure_data_dirs() -> None:
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    WORK_DIR.mkdir(parents=True, exist_ok=True)


def backend_path(*parts: str) -> Path:
    return BACKEND_DIR.joinpath(*parts)
