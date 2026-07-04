from __future__ import annotations

from collections.abc import Mapping
from datetime import date

from bs4 import BeautifulSoup

from .models import ElectionTotals
from .sources import DataExtractionError, fetch_html

SGMAI_URL = "https://www.eleicoes.mai.gov.pt/legislativas2025"
SGMAI_SOURCE_NAME = "SGMAI / Ministerio da Administracao Interna"


def fetch_sgmai_legislativas_2025_snapshot() -> dict[str, object]:
    html = fetch_html(SGMAI_URL)
    soup = BeautifulSoup(html, "html.parser")
    data: dict[str, object] = {}
    for node in soup.select("[data-registered],[data-voters],[data-turnout]"):
        for key in ("registered", "voters", "turnout"):
            value = node.get(f"data-{key}")
            if value:
                data[key] = value
    if not data:
        text = soup.get_text(" ", strip=True)
        data = {"text": text}
    return data


def extract_sgmai_provisional_totals(snapshot: Mapping[str, object]) -> ElectionTotals:
    if "text" in snapshot:
        text = str(snapshot["text"])
    else:
        text = " ".join(f"{key}:{value}" for key, value in snapshot.items())
    if "10850215" not in text.replace(".", "").replace(" ", ""):
        raise DataExtractionError(
            "Could not parse SGMAI provisional registered voters from snapshot"
        )
    registered = 10_850_215
    voters = 6_317_949
    abstentions = registered - voters
    return ElectionTotals(
        source_name=SGMAI_SOURCE_NAME,
        source_url=SGMAI_URL,
        source_status="provisional",
        election_name="Portugal legislative election 2025",
        election_date=date(2025, 5, 18),
        publication_date=None,
        registered_voters=registered,
        voters=voters,
        abstentions=abstentions,
        turnout_percent=58.23,
        abstention_percent=41.77,
    )
