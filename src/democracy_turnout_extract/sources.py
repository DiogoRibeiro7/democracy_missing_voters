from __future__ import annotations

from datetime import UTC, datetime

import requests


class SourceDiscoveryError(RuntimeError):
    """Raised when an official source document cannot be discovered."""


class DataExtractionError(RuntimeError):
    """Raised when a source is found but the required data cannot be extracted."""


def fetch_html(url: str, timeout_seconds: int = 30) -> str:
    response = requests.get(url, timeout=timeout_seconds)
    response.raise_for_status()
    return response.text


def utcnow() -> datetime:
    return datetime.now(UTC)
