from __future__ import annotations

from datetime import datetime

import pandas as pd


def build_source_provenance_table(accessed_at: datetime) -> pd.DataFrame:
    """Build a provenance table for the notebook's audit trail."""

    rows = [
        {
            "dataset": "Portugal 2025 final official totals",
            "source_name": "CNE Mapa Oficial n.º 2-A/2025",
            "source_url": "https://files.diariodarepublica.pt/1s/2025/05/104a00/0000200016.pdf",
            "source_status": "final_official",
            "publication_date": "2025-05-31",
            "accessed_at": accessed_at.isoformat(),
            "extraction_type": "offline fixture extraction via democracy_turnout_extract",
            "notes": "Final official national total and overseas source circles.",
        },
        {
            "dataset": "OECD 2024 trust indicators",
            "source_name": "OECD Survey on Drivers of Trust in Public Institutions – 2024 Results",
            "source_url": "https://www.oecd.org/en/publications/oecd-survey-on-drivers-of-trust-in-public-institutions-2024-results_9a20554b-en.html",
            "source_status": "contextual",
            "publication_date": "2024-07-10",
            "accessed_at": accessed_at.isoformat(),
            "extraction_type": "saved HTML and report excerpt",
            "notes": "Pinned to 2024 for the article package.",
        },
        {
            "dataset": "Portugal legislative turnout 1975–2025 series",
            "source_name": "Repository historical turnout CSV",
            "source_url": "data/portugal_legislative_turnout_1975_2025.csv",
            "source_status": "derived",
            "publication_date": "",
            "accessed_at": accessed_at.isoformat(),
            "extraction_type": "repository CSV with 2025 final override",
            "notes": (
                "Historical values require official revalidation "
                "before publication-grade reuse."
            ),
        },
        {
            "dataset": "Contextual abstention framing",
            "source_name": "EDJNet / Divergente contextual article",
            "source_url": "https://www.europeandatajournalism.eu/cp_data_news/portugal-among-eu-countries-with-lowest-voter-turnout-for-government-elections/",
            "source_status": "contextual",
            "publication_date": "",
            "accessed_at": accessed_at.isoformat(),
            "extraction_type": "contextual reference only",
            "notes": "Not used as the primary source for official totals.",
        },
    ]
    return pd.DataFrame(rows)[
        [
            "dataset",
            "source_name",
            "source_url",
            "source_status",
            "publication_date",
            "accessed_at",
            "extraction_type",
            "notes",
        ]
    ]
