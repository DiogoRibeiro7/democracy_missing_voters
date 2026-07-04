from __future__ import annotations

from pathlib import Path

from democracy_turnout_extract.cne import (
    build_participation_breakdown,
    discover_cne_ar_2025_documents,
    extract_ar2025_circles_from_cne_pdf,
    extract_ar2025_totals_from_cne_pdf,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "cne"


def test_extract_cne_totals_from_fixture() -> None:
    total = extract_ar2025_totals_from_cne_pdf(FIXTURE_DIR / "ar2025_official_map_excerpt.txt")
    assert total.registered_voters == 10_848_816
    assert total.voters == 6_319_969
    assert total.abstentions == 4_528_847
    assert total.turnout_percent == 58.25
    assert total.abstention_percent == 41.75


def test_extract_cne_circles_and_breakdown() -> None:
    circles = extract_ar2025_circles_from_cne_pdf(FIXTURE_DIR / "ar2025_official_map_excerpt.txt")
    assert circles[0].circle_name == "Europa"
    assert circles[0].registered_voters == 948_062
    assert circles[1].circle_name == "Fora da Europa"
    assert circles[1].voters == 98_234
    total = extract_ar2025_totals_from_cne_pdf(FIXTURE_DIR / "ar2025_official_map_excerpt.txt")
    breakdown = build_participation_breakdown(total, circles)
    assert breakdown.overseas.registered_voters == 1_584_722
    assert breakdown.overseas.voters == 355_018
    assert breakdown.overseas.abstentions == 1_229_704
    assert breakdown.overseas.turnout_percent == 22.40
    assert breakdown.territory.registered_voters == 9_264_094
    assert breakdown.territory.voters == 5_964_951


def test_discover_cne_documents_from_fixture(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    html = (FIXTURE_DIR / "ar2025_official_map_links.html").read_text(encoding="utf-8")
    monkeypatch.setattr("democracy_turnout_extract.cne.fetch_html", lambda url: html)
    documents = discover_cne_ar_2025_documents()
    assert any(document.document_type == "pdf" for document in documents)
