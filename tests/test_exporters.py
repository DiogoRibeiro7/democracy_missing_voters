from __future__ import annotations

from datetime import UTC, date, datetime

from democracy_turnout_extract.cne import build_participation_breakdown
from democracy_turnout_extract.exporters import (
    export_circle_results_csv,
    export_election_totals_csv,
    export_manifest_json,
    export_participation_breakdown_csv,
    export_trust_indicators_csv,
)
from democracy_turnout_extract.models import (
    ElectionCircleResult,
    ElectionTotals,
    ExtractionManifest,
    ManifestEntry,
    TrustIndicator,
)


def test_exporters_write_files(tmp_path) -> None:  # type: ignore[no-untyped-def]
    total = ElectionTotals(
        source_name="CNE",
        source_url="https://example.com/cne.pdf",
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
    circles = [
        ElectionCircleResult(
            circle_name="Europa",
            registered_voters=948_062,
            voters=256_784,
            abstentions=691_278,
            turnout_percent=27.08,
            abstention_percent=72.92,
            source_name="CNE",
            source_url="https://example.com/cne.pdf",
        ),
        ElectionCircleResult(
            circle_name="Fora da Europa",
            registered_voters=636_660,
            voters=98_234,
            abstentions=538_426,
            turnout_percent=15.43,
            abstention_percent=84.57,
            source_name="CNE",
            source_url="https://example.com/cne.pdf",
        ),
    ]
    breakdown = build_participation_breakdown(total, circles)
    indicators = [
        TrustIndicator(
            indicator_name="trust_national_government",
            value_percent=39,
            population="OECD average",
            survey_year=2023,
            report_year=2024,
            source_name="OECD",
            source_url="https://example.com/oecd",
        )
    ]
    manifest = ExtractionManifest(
        generated_at=datetime.now(UTC),
        entries=[
            ManifestEntry(
                source_name="CNE",
                source_url="https://example.com/cne.pdf",
                download_timestamp=datetime.now(UTC),
                content_hash="abc123",
                extraction_function="extract",
                extracted_rows=1,
                validation_status="passed",
                warnings=[],
                source_status="final_official",
            )
        ],
    )

    assert export_election_totals_csv(total, tmp_path / "totals.csv").exists()
    assert export_circle_results_csv(circles, tmp_path / "circles.csv").exists()
    assert export_participation_breakdown_csv(breakdown, tmp_path / "breakdown.csv").exists()
    assert export_trust_indicators_csv(indicators, tmp_path / "trust.csv").exists()
    assert export_manifest_json(manifest, tmp_path / "manifest.json").exists()
