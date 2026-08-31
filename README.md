# democracy_turnout_extract

This repository now includes a small Python package that extracts and validates the data used in the article about voter abstention in Portugal and trust in democratic institutions.

The pipeline extracts:

- final official Portugal 2025 legislative election totals from the CNE official map,
- Europe and Fora da Europa circle values from the same official source,
- a derived participation breakdown where `Territory = Total - Overseas` and `Overseas = Europa + Fora da Europa`,
- optional provisional SGMAI/MAI 2025 totals for comparison only,
- OECD 2024 trust indicators pinned to the article package.

Official, provisional, and contextual sources:

- Official: CNE / Diário da República final official 2025 legislative election documents.
- Provisional: SGMAI / MAI 2025 election site. These values never override final CNE totals.
- Contextual: OECD 2024 trust report and page, plus any background-only references.

## Run the pipeline

Install the package in editable mode with dev dependencies:

```bash
pip install -e .[dev]
```

Run the offline smoke pipeline:

```bash
democracy-turnout-extract build-all --offline-fixtures
```

Run the live pipeline with provisional comparison enabled:

```bash
democracy-turnout-extract build-all --include-provisional
```

Other commands:

```bash
democracy-turnout-extract discover-sources
democracy-turnout-extract extract-cne-2025 --offline-fixtures
democracy-turnout-extract extract-sgmai-2025 --offline-fixtures
democracy-turnout-extract extract-oecd-2024 --offline-fixtures
democracy-turnout-extract validate --offline-fixtures
```

## Outputs

Processed files are written to `data/processed/`:

- `portugal_2025_final_totals.csv`
- `portugal_2025_circle_results.csv`
- `portugal_2025_participation_breakdown.csv`
- `oecd_2024_trust_indicators.csv`
- `extraction_manifest.json`
- `portugal_2025_sgmai_provisional_totals.csv` when provisional output is enabled

## Tests and checks

```bash
pytest
ruff check .
mypy src
```

## Updating for future elections or OECD report years

Update source URLs and year-specific validation targets in `src/democracy_turnout_extract/cne.py`, `oecd.py`, and `validators.py`. Keep the extraction functions configurable, but pin tests and validators to the article’s intended year. If the article is updated to a newer OECD edition, change the report-year configuration deliberately rather than silently switching to a newer publication.

## Limitations

- The offline smoke path uses saved text and HTML excerpts rather than a full live PDF parse.
- Territory is derived, not scraped directly.
- Historical turnout series in the article data should be rebuilt from official primary sources before being treated as fully publication-grade.
- OECD 2024 values are intentionally pinned for the article package unless the article itself is updated.

## Licence

Code is [MIT](LICENSE). Data, derived tables and manuscript text are
[CC BY 4.0](LICENSE-DATA.md). Third-party source data keeps its provider's terms — see
[`LICENSE-DATA.md`](LICENSE-DATA.md).
