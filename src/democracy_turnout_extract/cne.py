from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Literal

import requests
from bs4 import BeautifulSoup, Tag

from .models import (
    DerivedParticipationBreakdown,
    ElectionCircleResult,
    ElectionTotals,
    SourceDocument,
)
from .sources import DataExtractionError, SourceDiscoveryError, fetch_html, utcnow

CNE_MAIN_URL = "https://www.cne.pt/content/eleicoes-para-assembleia-da-republica-2025"
CNE_PDF_URL = "https://files.diariodarepublica.pt/1s/2025/05/104a00/0000200016.pdf"
CNE_SOURCE_NAME = "Comissao Nacional de Eleicoes"


def discover_cne_ar_2025_documents() -> list[SourceDocument]:
    html = fetch_html(CNE_MAIN_URL)
    soup = BeautifulSoup(html, "html.parser")
    documents: list[SourceDocument] = [
        SourceDocument(
            source_name=CNE_SOURCE_NAME,
            source_url=CNE_MAIN_URL,
            document_type="html",
            source_status="final_official",
            title="Eleições para a Assembleia da República 2025",
            discovered_at=utcnow(),
        )
    ]
    for anchor in soup.find_all("a", href=True):
        if not isinstance(anchor, Tag):
            continue
        text = anchor.get_text(" ", strip=True)
        href = anchor.get("href")
        if not isinstance(href, str):
            continue
        if not href.startswith("http"):
            href = requests.compat.urljoin(CNE_MAIN_URL, href)
        if (
            "mapa oficial" in text.lower()
            or "2-a/2025" in text.lower()
            or "resultados" in text.lower()
            or href.lower().endswith(".pdf")
        ):
            document_type: Literal["pdf", "page"] = (
                "pdf" if href.lower().endswith(".pdf") else "page"
            )
            documents.append(
                SourceDocument(
                    source_name=CNE_SOURCE_NAME,
                    source_url=href,
                    document_type=document_type,
                    source_status="final_official",
                    title=text or href.rsplit("/", 1)[-1],
                    discovered_at=utcnow(),
                )
            )
    deduped: dict[str, SourceDocument] = {
        str(document.source_url): document for document in documents
    }
    results = list(deduped.values())
    if not any(document.document_type == "pdf" for document in results):
        raise SourceDiscoveryError(
            "No official CNE PDF document found for Assembleia da Republica 2025"
        )
    return results


def download_binary(url: str, output_path: Path, timeout_seconds: int = 60) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(url, timeout=timeout_seconds)
    response.raise_for_status()
    output_path.write_bytes(response.content)
    return output_path


def extract_text_from_pdf(pdf_path: Path) -> str:
    if pdf_path.suffix.lower() == ".txt":
        return pdf_path.read_text(encoding="utf-8")
    try:
        import pdfplumber
    except ImportError as exc:
        raise DataExtractionError("pdfplumber is required to extract text from PDF files") from exc
    parts: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            parts.append(page.extract_text() or "")
    text = "\n".join(parts).strip()
    if not text:
        raise DataExtractionError(f"No extractable text found in PDF {pdf_path}")
    return text


def _normalize_text(text: str) -> str:
    return re.sub(r"[ \t]+", " ", text.replace("\xa0", " ")).strip()


def _parse_int(value: str) -> int:
    return int(re.sub(r"[^\d]", "", value))


def _parse_float(value: str) -> float:
    return float(value.replace("%", "").replace(",", ".").strip())


def _build_circle(
    circle_name: str,
    registered: int,
    voters: int,
    source_url: str,
) -> ElectionCircleResult:
    abstentions = registered - voters
    turnout = round(voters / registered * 100, 2)
    abstention = round(abstentions / registered * 100, 2)
    return ElectionCircleResult(
        circle_name=circle_name,
        registered_voters=registered,
        voters=voters,
        abstentions=abstentions,
        turnout_percent=turnout,
        abstention_percent=abstention,
        source_name=CNE_SOURCE_NAME,
        source_url=source_url,
    )


def _find_line(text: str, prefix: str) -> str:
    for raw_line in text.splitlines():
        line = _normalize_text(raw_line)
        if line.lower().startswith(prefix.lower()):
            return raw_line.strip()
    raise DataExtractionError(
        f"Could not find line starting with '{prefix}' in the CNE official map text"
    )


def _extract_number_groups(line: str) -> list[str]:
    groups = [part.strip() for part in re.split(r"\s{2,}", line) if part.strip()]
    return [part for part in groups if re.search(r"\d", part)]


def _extract_totals_from_text(text: str, source_url: str = CNE_PDF_URL) -> ElectionTotals:
    line = _find_line(text, "TOTAL GERAL")
    groups = _extract_number_groups(line)
    if len(groups) < 5:
        raise DataExtractionError(
            "Could not parse the final national total line from the CNE official map text"
        )
    registered, voters, abstentions, turnout, abstention = groups[:5]
    return ElectionTotals(
        source_name=CNE_SOURCE_NAME,
        source_url=source_url,
        source_status="final_official",
        election_name="Portugal legislative election 2025",
        election_date=date(2025, 5, 18),
        publication_date=date(2025, 5, 31),
        registered_voters=_parse_int(registered),
        voters=_parse_int(voters),
        abstentions=_parse_int(abstentions),
        turnout_percent=_parse_float(turnout),
        abstention_percent=_parse_float(abstention),
    )


def extract_ar2025_totals_from_cne_pdf(pdf_path: Path) -> ElectionTotals:
    text = extract_text_from_pdf(pdf_path)
    return _extract_totals_from_text(text, source_url=CNE_PDF_URL)


def extract_ar2025_circles_from_cne_pdf(pdf_path: Path) -> list[ElectionCircleResult]:
    text = extract_text_from_pdf(pdf_path)
    circles: list[ElectionCircleResult] = []
    for circle_name in ("Europa", "Fora da Europa"):
        line = _find_line(text, circle_name)
        groups = _extract_number_groups(line)
        if len(groups) < 2:
            raise DataExtractionError(f"Could not parse CNE circle section for '{circle_name}'")
        registered, voters = groups[:2]
        circles.append(
            _build_circle(circle_name, _parse_int(registered), _parse_int(voters), CNE_PDF_URL)
        )
    return circles


def derive_overseas_result(circles: list[ElectionCircleResult]) -> ElectionCircleResult:
    wanted = {"Europa", "Fora da Europa"}
    indexed = {circle.circle_name: circle for circle in circles}
    missing = sorted(wanted - set(indexed))
    if missing:
        raise DataExtractionError(
            f"Cannot derive overseas result; missing circles: {', '.join(missing)}"
        )
    registered = sum(indexed[name].registered_voters for name in wanted)
    voters = sum(indexed[name].voters for name in wanted)
    return _build_circle(
        "Overseas",
        registered,
        voters,
        indexed["Europa"].source_url,
    )


def derive_territory_result(
    total: ElectionTotals,
    overseas: ElectionCircleResult,
) -> ElectionCircleResult:
    registered = total.registered_voters - overseas.registered_voters
    voters = total.voters - overseas.voters
    return _build_circle("Territory", registered, voters, total.source_url)


def build_participation_breakdown(
    total: ElectionTotals,
    circles: list[ElectionCircleResult],
) -> DerivedParticipationBreakdown:
    overseas = derive_overseas_result(circles)
    territory = derive_territory_result(total, overseas)
    if total.registered_voters != territory.registered_voters + overseas.registered_voters:
        raise DataExtractionError("Participation breakdown does not reconcile registered_voters")
    if total.voters != territory.voters + overseas.voters:
        raise DataExtractionError("Participation breakdown does not reconcile voters")
    if total.abstentions != territory.abstentions + overseas.abstentions:
        raise DataExtractionError("Participation breakdown does not reconcile abstentions")
    return DerivedParticipationBreakdown(
        total=total,
        territory=territory,
        overseas=overseas,
        derivation_method="territory = total - overseas; overseas = Europa + Fora da Europa",
        derived_from_circles=["Europa", "Fora da Europa"],
    )
