from datetime import datetime
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


class ProductionModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ============================================================
# REQUEST
# ============================================================

class ProductionPrepareRequest(ProductionModel):
    title: str = Field(min_length=1, max_length=250)

    report_ids: list[str] = Field(
        min_length=1,
        max_length=20,
    )

    objective: str = Field(
        default="",
        max_length=5000,
    )

    target_audience: str = Field(
        default="",
        max_length=2000,
    )

    output_language: Literal["fr", "en"] = "fr"

    output_format: Literal[
        "AUTONOMOUS_REPORT",
        "SPEAKER_PRESENTATION",
    ] = "AUTONOMOUS_REPORT"

    target_page_count: int = Field(
        default=12,
        ge=4,
        le=40,
    )

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "Le titre de la production est obligatoire."
            )

        return value

    @field_validator("objective", "target_audience")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("report_ids")
    @classmethod
    def normalize_report_ids(
        cls,
        values: list[str],
    ) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()

        for value in values:
            report_id = value.strip()

            if not report_id:
                raise ValueError(
                    "Un identifiant de rapport est vide."
                )

            if report_id not in seen:
                seen.add(report_id)
                result.append(report_id)

        return result


# ============================================================
# REPORT SNAPSHOT
# ============================================================

class ProductionReportSnapshot(ProductionModel):
    report_id: str
    version_number: int = Field(ge=1)

    snapshot_sha256: str

    # Exact JSON-compatible response returned by
    # get_touch_report(), including the saved notebook.
    payload: dict[str, Any]


# ============================================================
# EVIDENCE REFERENCES
# ============================================================

ProductionEvidenceKind = Literal[
    "NOTE",
    "EVENT",
    "NUMBER",
    "SECTION",
    "SUMMARY",
    "CROSS_READING",
]


class ProductionEvidenceReference(ProductionModel):
    # Unique across reports and evidence collections.
    reference_id: str

    report_id: str
    report_version: int = Field(ge=1)

    kind: ProductionEvidenceKind

    # Original identifier, unchanged inside its notebook.
    local_id: str


# ============================================================
# COUNTS
# ============================================================

class ProductionCorpusCounts(ProductionModel):
    reports: int
    unique_contents: int

    notes: int
    events: int

    # Counts occurrences in saved reports.
    # The same canonical Number may appear in several reports.
    number_occurrences: int

    unique_number_ids: int

    sections: int
    executive_summary_items: int
    cross_readings: int


# ============================================================
# PREPARED CORPUS
# ============================================================

class ProductionPreparedCorpus(ProductionModel):
    schema_version: Literal["1.0"] = "1.0"

    production_id: str
    prepared_at: datetime

    status: Literal["CORPUS_PREPARED"] = (
        "CORPUS_PREPARED"
    )

    data_policy: Literal[
        "SAVED_TOUCH_REPORTS_ONLY"
    ] = "SAVED_TOUCH_REPORTS_ONLY"

    request: ProductionPrepareRequest

    reports: list[ProductionReportSnapshot]

    evidence_index: list[
        ProductionEvidenceReference
    ]

    counts: ProductionCorpusCounts

    corpus_sha256: str
