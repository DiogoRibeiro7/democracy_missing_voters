from __future__ import annotations

import csv
import hashlib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .models import (
    DerivedParticipationBreakdown,
    ElectionCircleResult,
    ElectionTotals,
    ExtractionManifest,
    TrustIndicator,
)


def _write_csv(rows: list[dict[str, Any]], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError("Cannot export an empty CSV")
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return output_path


def export_election_totals_csv(total: ElectionTotals, output_path: Path) -> Path:
    return _write_csv([total.model_dump(mode="json")], output_path)


def export_circle_results_csv(circles: list[ElectionCircleResult], output_path: Path) -> Path:
    return _write_csv([circle.model_dump(mode="json") for circle in circles], output_path)


def export_participation_breakdown_csv(
    breakdown: DerivedParticipationBreakdown,
    output_path: Path,
) -> Path:
    rows = [
        {
            "geography": "Total",
            **breakdown.total.model_dump(
                mode="json",
                exclude={
                    "source_name",
                    "source_url",
                    "source_status",
                    "election_name",
                    "election_date",
                    "publication_date",
                },
            ),
        },
        {
            "geography": breakdown.territory.circle_name,
            **breakdown.territory.model_dump(
                mode="json",
                exclude={"circle_name", "source_name", "source_url"},
            ),
        },
        {
            "geography": breakdown.overseas.circle_name,
            **breakdown.overseas.model_dump(
                mode="json",
                exclude={"circle_name", "source_name", "source_url"},
            ),
        },
    ]
    return _write_csv(rows, output_path)


def export_trust_indicators_csv(
    indicators: list[TrustIndicator],
    output_path: Path,
) -> Path:
    return _write_csv([indicator.model_dump(mode="json") for indicator in indicators], output_path)


def export_manifest_json(manifest: ExtractionManifest, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    return output_path


def compute_content_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest_timestamp() -> datetime:
    return datetime.now(UTC)
