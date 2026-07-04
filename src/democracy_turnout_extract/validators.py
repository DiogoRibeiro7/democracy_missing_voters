from __future__ import annotations

from collections.abc import Sequence
from math import isclose
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import TrustIndicator


class DataValidationError(ValueError):
    """Raised when extracted values fail a consistency check."""


def validate_count_identity(registered_voters: int, voters: int, abstentions: int) -> None:
    if registered_voters < 0 or voters < 0 or abstentions < 0:
        raise DataValidationError("registered_voters, voters, and abstentions must be non-negative")
    if registered_voters != voters + abstentions:
        raise DataValidationError(
            f"registered_voters must equal voters + abstentions; got "
            f"{registered_voters} != {voters} + {abstentions}"
        )


def validate_percentages(
    registered_voters: int,
    voters: int,
    abstentions: int,
    turnout_percent: float,
    abstention_percent: float,
    tolerance: float = 0.05,
) -> None:
    validate_count_identity(registered_voters, voters, abstentions)
    if not isclose(turnout_percent + abstention_percent, 100.0, abs_tol=tolerance):
        raise DataValidationError(
            "turnout_percent + abstention_percent must be approximately 100"
        )
    if registered_voters == 0:
        return
    expected_turnout = round(voters / registered_voters * 100, 2)
    expected_abstention = round(abstentions / registered_voters * 100, 2)
    if not isclose(turnout_percent, expected_turnout, abs_tol=tolerance):
        raise DataValidationError(
            f"turnout_percent does not match voters / registered_voters * 100; "
            f"got {turnout_percent}, expected {expected_turnout}"
        )
    if not isclose(abstention_percent, expected_abstention, abs_tol=tolerance):
        raise DataValidationError(
            f"abstention_percent does not match abstentions / registered_voters * 100; "
            f"got {abstention_percent}, expected {expected_abstention}"
        )


def validate_final_cne_2025_totals(total: object) -> None:
    from .models import ElectionTotals

    if not isinstance(total, ElectionTotals):
        raise DataValidationError("validate_final_cne_2025_totals expects ElectionTotals")
    expected = {
        "registered_voters": 10_848_816,
        "voters": 6_319_969,
        "abstentions": 4_528_847,
        "turnout_percent": 58.25,
        "abstention_percent": 41.75,
    }
    for field_name, field_value in expected.items():
        actual = getattr(total, field_name)
        if actual != field_value:
            raise DataValidationError(
                f"CNE 2025 total mismatch for {field_name}: got {actual}, expected {field_value}"
            )


def validate_oecd_2024_indicators(indicators: Sequence[TrustIndicator]) -> None:
    expected = {
        "trust_national_government": 39.0,
        "low_or_no_trust_national_government": 44.0,
        "trust_if_feel_have_say": 69.0,
        "trust_if_feel_no_say": 22.0,
    }
    actual = {
        indicator.indicator_name: indicator.value_percent
        for indicator in indicators
    }
    missing = sorted(set(expected) - set(actual))
    if missing:
        raise DataValidationError(f"Missing OECD 2024 indicators: {', '.join(missing)}")
    for name, value in expected.items():
        if actual[name] != value:
            raise DataValidationError(
                f"OECD 2024 indicator mismatch for {name}: got {actual[name]}, expected {value}"
            )
