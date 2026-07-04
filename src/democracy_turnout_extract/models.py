from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .validators import validate_count_identity, validate_percentages


class CsvModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class SourceDocument(CsvModel):
    source_name: str
    source_url: str
    document_type: Literal["html", "pdf", "xlsx", "csv", "json", "page"]
    source_status: Literal["final_official", "provisional", "contextual"]
    title: str
    discovered_at: datetime | None = None


class ElectionTotals(CsvModel):
    source_name: str
    source_url: str
    source_status: Literal["final_official", "provisional", "contextual"]
    election_name: str
    election_date: date
    publication_date: date | None = None
    registered_voters: int = Field(ge=0)
    voters: int = Field(ge=0)
    abstentions: int = Field(ge=0)
    turnout_percent: float = Field(ge=0, le=100)
    abstention_percent: float = Field(ge=0, le=100)

    @model_validator(mode="after")
    def validate_consistency(self) -> ElectionTotals:
        validate_count_identity(self.registered_voters, self.voters, self.abstentions)
        validate_percentages(
            self.registered_voters,
            self.voters,
            self.abstentions,
            self.turnout_percent,
            self.abstention_percent,
        )
        return self


class ElectionCircleResult(CsvModel):
    circle_name: str
    registered_voters: int = Field(ge=0)
    voters: int = Field(ge=0)
    abstentions: int = Field(ge=0)
    turnout_percent: float = Field(ge=0, le=100)
    abstention_percent: float = Field(ge=0, le=100)
    source_name: str
    source_url: str

    @model_validator(mode="after")
    def validate_consistency(self) -> ElectionCircleResult:
        validate_count_identity(self.registered_voters, self.voters, self.abstentions)
        validate_percentages(
            self.registered_voters,
            self.voters,
            self.abstentions,
            self.turnout_percent,
            self.abstention_percent,
        )
        return self


class DerivedParticipationBreakdown(CsvModel):
    total: ElectionTotals
    territory: ElectionCircleResult
    overseas: ElectionCircleResult
    derivation_method: str
    derived_from_circles: list[str]


class TrustIndicator(CsvModel):
    indicator_name: str
    value_percent: float = Field(ge=0, le=100)
    population: str
    survey_year: int
    report_year: int
    source_name: str
    source_url: str

    @model_validator(mode="after")
    def validate_consistency(self) -> TrustIndicator:
        if self.survey_year > self.report_year:
            raise ValueError("survey_year must be less than or equal to report_year")
        return self


class ManifestEntry(CsvModel):
    source_name: str
    source_url: str
    download_timestamp: datetime
    content_hash: str
    extraction_function: str
    extracted_rows: int
    validation_status: Literal["passed", "failed", "warning"]
    warnings: list[str]
    source_status: Literal["final_official", "provisional", "contextual"]


class ExtractionManifest(CsvModel):
    generated_at: datetime
    entries: list[ManifestEntry]
