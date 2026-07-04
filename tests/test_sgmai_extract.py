from __future__ import annotations

from pathlib import Path

from democracy_turnout_extract.sgmai import extract_sgmai_provisional_totals


def test_extract_sgmai_provisional_totals() -> None:
    html = (
        Path(__file__).parent / "fixtures" / "sgmai" / "legislativas2025_snapshot.html"
    ).read_text(encoding="utf-8")
    total = extract_sgmai_provisional_totals({"text": html})
    assert total.source_status == "provisional"
    assert total.registered_voters == 10_850_215
    assert total.voters == 6_317_949
    assert total.turnout_percent == 58.23
