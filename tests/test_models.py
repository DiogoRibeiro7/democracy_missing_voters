from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from democracy_turnout_extract.models import ElectionTotals, TrustIndicator


def test_election_totals_validates_identity_and_percentages() -> None:
    total = ElectionTotals(
        source_name="CNE",
        source_url="https://example.com/source.pdf",
        source_status="final_official",
        election_name="Example Election",
        election_date=date(2025, 5, 18),
        registered_voters=100,
        voters=60,
        abstentions=40,
        turnout_percent=60.0,
        abstention_percent=40.0,
    )
    assert total.voters == 60


def test_election_totals_rejects_inconsistent_counts() -> None:
    with pytest.raises(ValidationError):
        ElectionTotals(
            source_name="CNE",
            source_url="https://example.com/source.pdf",
            source_status="final_official",
            election_name="Example Election",
            election_date=date(2025, 5, 18),
            registered_voters=100,
            voters=61,
            abstentions=40,
            turnout_percent=61.0,
            abstention_percent=39.0,
        )


def test_trust_indicator_rejects_survey_year_after_report_year() -> None:
    with pytest.raises(ValidationError):
        TrustIndicator(
            indicator_name="trust_national_government",
            value_percent=39,
            population="OECD average",
            survey_year=2025,
            report_year=2024,
            source_name="OECD",
            source_url="https://example.com/report",
        )
