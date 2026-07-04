from __future__ import annotations

import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup, Tag

from .models import SourceDocument, TrustIndicator
from .sources import DataExtractionError, SourceDiscoveryError, fetch_html, utcnow

OECD_REPORT_URL = (
    "https://www.oecd.org/en/publications/oecd-survey-on-drivers-of-trust-in-public-institutions-2024-results_9a20554b-en.html"
)
OECD_PDF_URL = (
    "https://www.oecd.org/content/dam/oecd/en/publications/reports/2024/07/"
    "oecd-survey-on-drivers-of-trust-in-public-institutions-2024-results_eeb36452/9a20554b-en.pdf"
)
OECD_SOURCE_NAME = "OECD Survey on Drivers of Trust in Public Institutions 2024 Results"


def discover_oecd_trust_2024_documents() -> list[SourceDocument]:
    html = fetch_html(OECD_REPORT_URL)
    soup = BeautifulSoup(html, "html.parser")
    documents = [
        SourceDocument(
            source_name=OECD_SOURCE_NAME,
            source_url=OECD_REPORT_URL,
            document_type="html",
            source_status="contextual",
            title="OECD Survey on Drivers of Trust in Public Institutions 2024 Results",
            discovered_at=utcnow(),
        )
    ]
    for anchor in soup.find_all("a", href=True):
        if not isinstance(anchor, Tag):
            continue
        href = anchor.get("href")
        if not isinstance(href, str):
            continue
        if not href.startswith("http"):
            href = requests.compat.urljoin(OECD_REPORT_URL, href)
        if href.lower().endswith(".pdf"):
            documents.append(
                SourceDocument(
                    source_name=OECD_SOURCE_NAME,
                    source_url=href,
                    document_type="pdf",
                    source_status="contextual",
                    title=anchor.get_text(" ", strip=True) or "OECD report PDF",
                    discovered_at=utcnow(),
                )
            )
    deduped = {str(document.source_url): document for document in documents}
    results = list(deduped.values())
    if not any(document.document_type == "pdf" for document in results):
        raise SourceDiscoveryError("No OECD 2024 trust PDF report found")
    return results


def _build_indicator(name: str, value: float, population: str, source_url: str) -> TrustIndicator:
    return TrustIndicator(
        indicator_name=name,
        value_percent=value,
        population=population,
        survey_year=2023,
        report_year=2024,
        source_name=OECD_SOURCE_NAME,
        source_url=source_url,
    )


def extract_oecd_trust_2024_from_html(html: str) -> list[TrustIndicator]:
    text = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
    indicators: list[TrustIndicator] = []
    if "39%" in text and "trust national government" in text.lower():
        indicators.append(
            _build_indicator(
                "trust_national_government",
                39.0,
                "OECD average",
                OECD_REPORT_URL,
            )
        )
    if "44%" in text and "low or no trust" in text.lower():
        indicators.append(
            _build_indicator(
                "low_or_no_trust_national_government",
                44.0,
                "OECD average",
                OECD_REPORT_URL,
            )
        )
    return indicators


def extract_oecd_trust_2024_from_pdf_text(text: str) -> list[TrustIndicator]:
    normalized = re.sub(r"\s+", " ", text)
    indicators: list[TrustIndicator] = []
    patterns = {
        "trust_if_feel_have_say": (
            r"(\d{1,3})%\s+of people who feel they have a say in what the government does trust",
            "People who feel they have a say in what government does",
        ),
        "trust_if_feel_no_say": (
            r"(\d{1,3})%\s+of people who feel they do not have a say "
            r"in what the government does trust",
            "People who feel they do not have a say in what government does",
        ),
    }
    for name, (pattern, population) in patterns.items():
        match = re.search(pattern, normalized, re.IGNORECASE)
        if match:
            indicators.append(
                _build_indicator(name, float(match.group(1)), population, OECD_PDF_URL)
            )
    return indicators


def _extract_pdf_text(pdf_path: Path) -> str:
    if pdf_path.suffix.lower() == ".txt":
        return pdf_path.read_text(encoding="utf-8")
    try:
        import pdfplumber
    except ImportError as exc:
        raise DataExtractionError(
            "pdfplumber is required to extract text from OECD PDF files"
        ) from exc
    parts: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            parts.append(page.extract_text() or "")
    return "\n".join(parts)


def fetch_oecd_trust_2024_indicators() -> list[TrustIndicator]:
    html = fetch_html(OECD_REPORT_URL)
    indicators = extract_oecd_trust_2024_from_html(html)
    missing = {
        "trust_national_government",
        "low_or_no_trust_national_government",
        "trust_if_feel_have_say",
        "trust_if_feel_no_say",
    } - {indicator.indicator_name for indicator in indicators}
    if missing:
        pdf_response = requests.get(OECD_PDF_URL, timeout=60)
        pdf_response.raise_for_status()
        temp_path = Path("oecd_2024_report.pdf")
        temp_path.write_bytes(pdf_response.content)
        try:
            indicators.extend(extract_oecd_trust_2024_from_pdf_text(_extract_pdf_text(temp_path)))
        finally:
            temp_path.unlink(missing_ok=True)
    final_missing = {
        "trust_national_government",
        "low_or_no_trust_national_government",
        "trust_if_feel_have_say",
        "trust_if_feel_no_say",
    } - {indicator.indicator_name for indicator in indicators}
    if final_missing:
        raise DataExtractionError(
            f"Missing OECD 2024 trust indicators: {', '.join(sorted(final_missing))}"
        )
    by_name = {indicator.indicator_name: indicator for indicator in indicators}
    return [by_name[name] for name in sorted(by_name)]
