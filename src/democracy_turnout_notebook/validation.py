from __future__ import annotations

from dataclasses import dataclass
from math import isclose
from typing import Any

import pandas as pd


@dataclass(slots=True)
class ValidationResult:
    check_name: str
    status: str
    expected: str
    observed: str
    tolerance: float
    message: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "check_name": self.check_name,
            "status": self.status,
            "expected": self.expected,
            "observed": self.observed,
            "tolerance": self.tolerance,
            "message": self.message,
        }


def validate_count_identity(
    check_name: str,
    registered_voters: int,
    voters: int,
    abstentions: int,
    *,
    status_on_failure: str = "fail",
) -> ValidationResult:
    expected = voters + abstentions
    status = "pass" if registered_voters == expected else status_on_failure
    message = (
        "registered_voters equals voters + abstentions"
        if status == "pass"
        else "registered_voters does not equal voters + abstentions"
    )
    return ValidationResult(
        check_name=check_name,
        status=status,
        expected=str(expected),
        observed=str(registered_voters),
        tolerance=0.0,
        message=message,
    )


def validate_percentage_identity(
    check_name: str,
    registered_voters: int,
    voters: int,
    abstentions: int,
    turnout_percent: float,
    abstention_percent: float,
    *,
    tolerance: float = 0.05,
    status_on_failure: str = "fail",
) -> list[ValidationResult]:
    if registered_voters == 0:
        raise ValueError("registered_voters must be positive for percentage validation")
    computed_turnout = round(voters / registered_voters * 100, 2)
    computed_abstention = round(abstentions / registered_voters * 100, 2)
    turnout_ok = isclose(turnout_percent, computed_turnout, abs_tol=tolerance)
    abstention_ok = isclose(abstention_percent, computed_abstention, abs_tol=tolerance)
    sum_ok = isclose(turnout_percent + abstention_percent, 100.0, abs_tol=tolerance)
    return [
        ValidationResult(
            check_name=f"{check_name}_turnout",
            status="pass" if turnout_ok else status_on_failure,
            expected=f"{computed_turnout:.2f}",
            observed=f"{turnout_percent:.2f}",
            tolerance=tolerance,
            message="turnout percent matches computed value"
            if turnout_ok
            else "turnout percent differs from computed value",
        ),
        ValidationResult(
            check_name=f"{check_name}_abstention",
            status="pass" if abstention_ok else status_on_failure,
            expected=f"{computed_abstention:.2f}",
            observed=f"{abstention_percent:.2f}",
            tolerance=tolerance,
            message="abstention percent matches computed value"
            if abstention_ok
            else "abstention percent differs from computed value",
        ),
        ValidationResult(
            check_name=f"{check_name}_sum",
            status="pass" if sum_ok else status_on_failure,
            expected="100.00",
            observed=f"{turnout_percent + abstention_percent:.2f}",
            tolerance=tolerance,
            message="turnout and abstention sum to 100"
            if sum_ok
            else "turnout and abstention do not sum to 100",
        ),
    ]


def build_validation_report(results: list[ValidationResult]) -> pd.DataFrame:
    """Return a stable validation report table for notebook display and export."""

    return pd.DataFrame([result.as_dict() for result in results])[
        ["check_name", "status", "expected", "observed", "tolerance", "message"]
    ]
