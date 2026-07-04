from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RAW_DIR = PACKAGE_ROOT / "data" / "raw"
DEFAULT_PROCESSED_DIR = PACKAGE_ROOT / "data" / "processed"
DEFAULT_FIXTURES_DIR = PACKAGE_ROOT / "tests" / "fixtures"


@dataclass(slots=True)
class Settings:
    raw_dir: Path = DEFAULT_RAW_DIR
    output_dir: Path = DEFAULT_PROCESSED_DIR
    fixtures_dir: Path = DEFAULT_FIXTURES_DIR
    include_provisional: bool = False
    strict: bool = False
    timeout_seconds: int = 30
