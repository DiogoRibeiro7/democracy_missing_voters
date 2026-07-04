from __future__ import annotations

from datetime import date

import pytest

from democracy_turnout_extract.models import ElectionTotals, TrustIndicator
from democracy_turnout_extract.validators import (
    DataValidationError,
    validate_final_cne_2025_totals,
    validate_oecd_2024_indicators,
)


def test_validate_final_cne_2025_totals_passes() -> None:
    total = ElectionTotals(
        source_name="CNE",
        source_url="https://example.com/source.pdf",
        source_status="final_official",
        election_name="Portugal legislative election 2025",
        election_date=date(2025, 5, 18),
        publication_date=date(2025, 5, 31),
        registered_voters=10_848_816,
        voters=6_319_969,
        abstentions=4_528_847,
        turnout_percent=58.25,
        abstention_percent=41.75,
    )
    validate_final_cne_2025_totals(total)


def test_validate_oecd_2024_indicators_rejects_missing_values() -> None:
    with pytest.raises(DataValidationError):
        validate_oecd_2024_indicators(
            [
                TrustIndicator(
                    indicator_name="trust_national_government",
                    value_percent=39,
                    population="OECD average",
                    survey_year=2023,
                    report_year=2024,
                    source_name="OECD",
                    source_url="https://example.com/report",
                )
            ]
        )
