from __future__ import annotations

from datetime import datetime

from democracy_turnout_notebook.provenance import build_source_provenance_table
from democracy_turnout_notebook.validation import (
    build_validation_report,
    validate_count_identity,
    validate_percentage_identity,
)


def test_validate_count_identity_passes() -> None:
    result = validate_count_identity("counts", 100, 60, 40)
    assert result.status == "pass"


def test_validate_percentage_identity_detects_mismatch() -> None:
    results = validate_percentage_identity(
        "percentages",
        100,
        60,
        40,
        59.0,
        41.0,
        status_on_failure="warning",
    )
    report = build_validation_report(results)
    assert "warning" in set(report["status"])
    assert report.loc[report["check_name"] == "percentages_sum", "status"].iloc[0] == "pass"


def test_build_source_provenance_table_has_required_rows() -> None:
    table = build_source_provenance_table(datetime(2026, 7, 4))
    assert len(table) >= 4
    assert "final_official" in set(table["source_status"])
