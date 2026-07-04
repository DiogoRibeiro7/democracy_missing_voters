from __future__ import annotations

from pathlib import Path
from typing import Literal

import requests
import typer

from .cne import (
    CNE_PDF_URL,
    build_participation_breakdown,
    discover_cne_ar_2025_documents,
    download_binary,
    extract_ar2025_circles_from_cne_pdf,
    extract_ar2025_totals_from_cne_pdf,
)
from .config import DEFAULT_FIXTURES_DIR, DEFAULT_PROCESSED_DIR, DEFAULT_RAW_DIR, Settings
from .exporters import (
    compute_content_hash,
    export_circle_results_csv,
    export_election_totals_csv,
    export_manifest_json,
    export_participation_breakdown_csv,
    export_trust_indicators_csv,
    manifest_timestamp,
)
from .models import ExtractionManifest, ManifestEntry, TrustIndicator
from .oecd import (
    OECD_REPORT_URL,
    discover_oecd_trust_2024_documents,
    extract_oecd_trust_2024_from_html,
    extract_oecd_trust_2024_from_pdf_text,
    fetch_oecd_trust_2024_indicators,
)
from .sgmai import extract_sgmai_provisional_totals, fetch_sgmai_legislativas_2025_snapshot
from .validators import validate_final_cne_2025_totals, validate_oecd_2024_indicators

app = typer.Typer(no_args_is_help=True)

OutputDirOption = typer.Option(DEFAULT_PROCESSED_DIR, "--output-dir")
RawDirOption = typer.Option(DEFAULT_RAW_DIR, "--raw-dir")
OfflineFixturesOption = typer.Option(False, "--offline-fixtures")
IncludeProvisionalOption = typer.Option(False, "--include-provisional")
StrictOption = typer.Option(False, "--strict")


def _resolve_settings(
    output_dir: Path,
    raw_dir: Path,
    include_provisional: bool,
    strict: bool,
) -> Settings:
    return Settings(
        raw_dir=raw_dir,
        output_dir=output_dir,
        fixtures_dir=DEFAULT_FIXTURES_DIR,
        include_provisional=include_provisional,
        strict=strict,
    )


def _load_offline_cne_fixture(settings: Settings) -> Path:
    return settings.fixtures_dir / "cne" / "ar2025_official_map_excerpt.txt"


def _load_offline_oecd_indicators(settings: Settings) -> list[TrustIndicator]:
    html = (settings.fixtures_dir / "oecd" / "oecd_trust_2024_page.html").read_text(
        encoding="utf-8"
    )
    text = (
        settings.fixtures_dir / "oecd" / "oecd_trust_2024_report_excerpt.txt"
    ).read_text(encoding="utf-8")
    indicators = extract_oecd_trust_2024_from_html(html)
    indicators.extend(extract_oecd_trust_2024_from_pdf_text(text))
    by_name = {indicator.indicator_name: indicator for indicator in indicators}
    return [by_name[name] for name in sorted(by_name)]


ManifestSourceStatus = Literal["final_official", "provisional", "contextual"]


def _build_manifest_entries(
    paths: list[tuple[str, str, Path, str, int, list[str], ManifestSourceStatus]],
) -> list[ManifestEntry]:
    entries: list[ManifestEntry] = []
    for source_name, source_url, path, extraction_function, rows, warnings, source_status in paths:
        entries.append(
            ManifestEntry(
                source_name=source_name,
                source_url=source_url,
                download_timestamp=manifest_timestamp(),
                content_hash=compute_content_hash(path),
                extraction_function=extraction_function,
                extracted_rows=rows,
                validation_status="warning" if warnings else "passed",
                warnings=warnings,
                source_status=source_status,
            )
        )
    return entries


@app.command("discover-sources")
def discover_sources() -> None:
    cne_documents = discover_cne_ar_2025_documents()
    oecd_documents = discover_oecd_trust_2024_documents()
    typer.echo(f"CNE documents discovered: {len(cne_documents)}")
    typer.echo(f"OECD documents discovered: {len(oecd_documents)}")


@app.command("extract-cne-2025")
def extract_cne_2025(
    output_dir: Path = OutputDirOption,
    raw_dir: Path = RawDirOption,
    offline_fixtures: bool = OfflineFixturesOption,
) -> None:
    settings = _resolve_settings(output_dir, raw_dir, include_provisional=False, strict=False)
    if offline_fixtures:
        pdf_path = _load_offline_cne_fixture(settings)
    else:
        pdf_path = download_binary(CNE_PDF_URL, raw_dir / "cne" / "ar2025_official_map.pdf")
    total = extract_ar2025_totals_from_cne_pdf(pdf_path)
    circles = extract_ar2025_circles_from_cne_pdf(pdf_path)
    breakdown = build_participation_breakdown(total, circles)
    export_election_totals_csv(total, output_dir / "portugal_2025_final_totals.csv")
    export_circle_results_csv(circles, output_dir / "portugal_2025_circle_results.csv")
    export_participation_breakdown_csv(
        breakdown, output_dir / "portugal_2025_participation_breakdown.csv"
    )
    typer.echo("CNE 2025 extraction complete")


@app.command("extract-sgmai-2025")
def extract_sgmai_2025(
    output_dir: Path = OutputDirOption,
    include_provisional: bool = typer.Option(
        True, "--include-provisional/--no-include-provisional"
    ),
    offline_fixtures: bool = OfflineFixturesOption,
) -> None:
    if not include_provisional:
        typer.echo("Provisional extraction disabled")
        raise typer.Exit()
    snapshot: dict[str, object]
    if offline_fixtures:
        html = (DEFAULT_FIXTURES_DIR / "sgmai" / "legislativas2025_snapshot.html").read_text(
            encoding="utf-8"
        )
        snapshot = {"text": html}
    else:
        snapshot = fetch_sgmai_legislativas_2025_snapshot()
    total = extract_sgmai_provisional_totals(snapshot)
    export_election_totals_csv(total, output_dir / "portugal_2025_sgmai_provisional_totals.csv")
    typer.echo("SGMAI provisional extraction complete")


@app.command("extract-oecd-2024")
def extract_oecd_2024(
    output_dir: Path = OutputDirOption,
    offline_fixtures: bool = OfflineFixturesOption,
) -> None:
    if offline_fixtures:
        settings = _resolve_settings(output_dir, DEFAULT_RAW_DIR, False, False)
        indicators = _load_offline_oecd_indicators(settings)
    else:
        indicators = fetch_oecd_trust_2024_indicators()
    validate_oecd_2024_indicators(indicators)
    export_trust_indicators_csv(indicators, output_dir / "oecd_2024_trust_indicators.csv")
    typer.echo("OECD 2024 extraction complete")


@app.command("validate")
def validate(
    raw_dir: Path = RawDirOption,
    offline_fixtures: bool = OfflineFixturesOption,
) -> None:
    settings = _resolve_settings(
        DEFAULT_PROCESSED_DIR,
        raw_dir,
        include_provisional=False,
        strict=True,
    )
    if offline_fixtures:
        pdf_path = _load_offline_cne_fixture(settings)
    else:
        pdf_path = raw_dir / "cne" / "ar2025_official_map.pdf"
    total = extract_ar2025_totals_from_cne_pdf(pdf_path)
    validate_final_cne_2025_totals(total)
    if offline_fixtures:
        indicators = _load_offline_oecd_indicators(settings)
    else:
        indicators = fetch_oecd_trust_2024_indicators()
    validate_oecd_2024_indicators(indicators)
    typer.echo("Validation passed")


@app.command("build-all")
def build_all(
    output_dir: Path = OutputDirOption,
    raw_dir: Path = RawDirOption,
    offline_fixtures: bool = OfflineFixturesOption,
    include_provisional: bool = IncludeProvisionalOption,
    strict: bool = StrictOption,
) -> None:
    settings = _resolve_settings(output_dir, raw_dir, include_provisional, strict)
    raw_sources: list[tuple[str, str, Path, str, int, list[str], ManifestSourceStatus]] = []

    if offline_fixtures:
        cne_path = _load_offline_cne_fixture(settings)
        oecd_html_path = settings.fixtures_dir / "oecd" / "oecd_trust_2024_page.html"
        oecd_text_path = settings.fixtures_dir / "oecd" / "oecd_trust_2024_report_excerpt.txt"
    else:
        discover_cne_ar_2025_documents()
        discover_oecd_trust_2024_documents()
        cne_path = download_binary(CNE_PDF_URL, raw_dir / "cne" / "ar2025_official_map.pdf")
        oecd_html_path = raw_dir / "oecd" / "oecd_trust_2024_page.html"
        oecd_html_path.parent.mkdir(parents=True, exist_ok=True)
        oecd_html_path.write_text(requests.get(OECD_REPORT_URL, timeout=60).text, encoding="utf-8")
        oecd_text_path = settings.fixtures_dir / "oecd" / "oecd_trust_2024_report_excerpt.txt"

    total = extract_ar2025_totals_from_cne_pdf(cne_path)
    circles = extract_ar2025_circles_from_cne_pdf(cne_path)
    validate_final_cne_2025_totals(total)
    breakdown = build_participation_breakdown(total, circles)
    export_election_totals_csv(total, output_dir / "portugal_2025_final_totals.csv")
    export_circle_results_csv(circles, output_dir / "portugal_2025_circle_results.csv")
    export_participation_breakdown_csv(
        breakdown, output_dir / "portugal_2025_participation_breakdown.csv"
    )
    raw_sources.append(
        (
            total.source_name,
            total.source_url,
            cne_path,
            "extract_ar2025_totals_from_cne_pdf",
            1 + len(circles),
            [],
            total.source_status,
        )
    )

    if offline_fixtures:
        indicators = _load_offline_oecd_indicators(settings)
    else:
        indicators = extract_oecd_trust_2024_from_html(
            oecd_html_path.read_text(encoding="utf-8")
        ) + extract_oecd_trust_2024_from_pdf_text(oecd_text_path.read_text(encoding="utf-8"))
    by_name = {indicator.indicator_name: indicator for indicator in indicators}
    indicators = [by_name[name] for name in sorted(by_name)]
    validate_oecd_2024_indicators(indicators)
    export_trust_indicators_csv(indicators, output_dir / "oecd_2024_trust_indicators.csv")
    raw_sources.append(
        (
            indicators[0].source_name,
            indicators[0].source_url,
            oecd_text_path,
            "fetch_oecd_trust_2024_indicators",
            len(indicators),
            [],
            "contextual",
        )
    )

    if include_provisional:
        snapshot: dict[str, object]
        snapshot = (
            {
                "text": (
                    settings.fixtures_dir / "sgmai" / "legislativas2025_snapshot.html"
                ).read_text(encoding="utf-8")
            }
            if offline_fixtures
            else fetch_sgmai_legislativas_2025_snapshot()
        )
        sgmai_total = extract_sgmai_provisional_totals(snapshot)
        export_election_totals_csv(
            sgmai_total, output_dir / "portugal_2025_sgmai_provisional_totals.csv"
        )
        warnings = []
        if (
            sgmai_total.registered_voters != total.registered_voters
            or sgmai_total.voters != total.voters
        ):
            warnings.append("Provisional SGMAI totals differ from final official CNE totals")
        raw_sources.append(
            (
                sgmai_total.source_name,
                sgmai_total.source_url,
                settings.fixtures_dir / "sgmai" / "legislativas2025_snapshot.html"
                if offline_fixtures
                else cne_path,
                "extract_sgmai_provisional_totals",
                1,
                warnings,
                "provisional",
            )
        )

    manifest = ExtractionManifest(
        generated_at=manifest_timestamp(),
        entries=_build_manifest_entries(raw_sources),
    )
    export_manifest_json(manifest, output_dir / "extraction_manifest.json")
    typer.echo("Build complete")


if __name__ == "__main__":
    app()
