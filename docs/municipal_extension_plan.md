# Municipal Extension Plan

This package can be extended to municipality-level abstention data by separating source extraction, normalization, and joins into distinct steps.

Recommended sources:

- CNE or SGMAI municipality-level election result tables for official vote counts.
- INE or PORDATA municipal indicators for socio-economic context.
- Eurostat regional indicators only where municipality coverage is incomplete or a regional proxy is explicitly acceptable.

Recommended outputs:

- `data/processed/portugal_2025_municipality_turnout.csv`
- `data/processed/portugal_2025_municipality_abstention_joined_indicators.csv`

Core fields:

- `municipality`
- `district`
- `registered_voters`
- `voters`
- `abstentions`
- `abstention_rate`
- `median_income_or_purchasing_power`
- `unemployment`
- `age_structure`
- `education`
- `housing_pressure`
- `population_density`

Design notes:

- Use stable municipality codes whenever the source provides them. Name-only joins are fragile.
- Build a dedicated normalization layer for municipality names, including accents, abbreviations, and historical spelling variants.
- Keep election extraction and socio-economic joins separate so provenance remains clear.
- Store join diagnostics showing unmatched, ambiguous, and many-to-one matches.

Join risks:

- Municipality names may differ across CNE, INE, PORDATA, and Eurostat exports.
- Boundary changes, merged entities, and code-version drift can break historical comparability.
- Regional proxies should never be silently mixed with municipality-level data.

Interpretation warnings:

- Correlation does not prove individual-level voting behaviour.
- Ecological fallacy is a real risk: municipality-level patterns cannot be treated as evidence about how any given individual voted or abstained.
- Any future modeling should document assumptions, missingness, and geographic comparability before publication.
