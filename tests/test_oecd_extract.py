from __future__ import annotations

from pathlib import Path

import pytest

from democracy_turnout_extract.oecd import (
    discover_oecd_trust_2024_documents,
    extract_oecd_trust_2024_from_html,
    extract_oecd_trust_2024_from_pdf_text,
)
from democracy_turnout_extract.sources import DataExtractionError
from democracy_turnout_extract.validators import validate_oecd_2024_indicators

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "oecd"


def test_extract_oecd_from_html_and_pdf_text() -> None:
    html = (FIXTURE_DIR / "oecd_trust_2024_page.html").read_text(encoding="utf-8")
    text = (FIXTURE_DIR / "oecd_trust_2024_report_excerpt.txt").read_text(encoding="utf-8")
    indicators = extract_oecd_trust_2024_from_html(html)
    indicators += extract_oecd_trust_2024_from_pdf_text(text)
    validate_oecd_2024_indicators(indicators)


def test_discover_oecd_documents_from_fixture(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    html = (FIXTURE_DIR / "oecd_trust_2024_page.html").read_text(encoding="utf-8")
    monkeypatch.setattr("democracy_turnout_extract.oecd.fetch_html", lambda url: html)
    documents = discover_oecd_trust_2024_documents()
    assert any(document.document_type == "pdf" for document in documents)


def test_oecd_missing_indicator_detection() -> None:
    with pytest.raises(DataExtractionError):
        indicators = extract_oecd_trust_2024_from_html(
            "<html><body>No indicator text.</body></html>"
        )
        by_name = {indicator.indicator_name for indicator in indicators}
        missing = {
            "trust_national_government",
            "low_or_no_trust_national_government",
            "trust_if_feel_have_say",
            "trust_if_feel_no_say",
        } - by_name
        if missing:
            raise DataExtractionError(
                f"Missing OECD 2024 trust indicators: {', '.join(sorted(missing))}"
            )
