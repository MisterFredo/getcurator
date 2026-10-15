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

    target_page_count: int | None = Field(
        default=None,
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


# ============================================================
# PAGE LAYOUT
# ============================================================

ProductionPageLayout = Literal[
    "COVER",
    "EXECUTIVE_SUMMARY",
    "CHART_WITH_ANALYSIS",
    "KEY_NUMBERS",
    "CASE_STUDY",
    "COMPARISON",
    "EXPLANATORY",
    "IMPLICATIONS",
    "SOURCES",
]


# ============================================================
# PAGE PLAN
# ============================================================

class ProductionPagePlan(ProductionModel):
    page_id: str = Field(
        min_length=1,
        max_length=100,
    )

    layout: ProductionPageLayout

    title: str = Field(
        min_length=1,
        max_length=250,
    )

    # Main message the page must explain or demonstrate.
    key_message: str = Field(
        min_length=1,
        max_length=1500,
    )

    # Proposed reasoning, not the final page copy.
    explanation_outline: list[str] = Field(
        default_factory=list,
        max_length=8,
    )

    # References from the prepared corpus evidence_index.
    evidence_reference_ids: list[str] = Field(
        default_factory=list,
    )

    # Subset of references whose kind is NUMBER.
    # No values are generated or copied by the plan LLM.
    number_reference_ids: list[str] = Field(
        default_factory=list,
    )

    # Editorial intent only.
    # The renderer will later receive validated chart data.
    visual_intent: str = Field(
        default="",
        max_length=2000,
    )

    # Existing uncertainties to preserve on this page.
    cautions: list[str] = Field(
        default_factory=list,
        max_length=8,
    )

    @field_validator(
        "page_id",
        "title",
        "key_message",
    )
    @classmethod
    def normalize_required_page_text(
        cls,
        value: str,
    ) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "Un champ obligatoire de page est vide."
            )

        return value

    @field_validator(
        "evidence_reference_ids",
        "number_reference_ids",
    )
    @classmethod
    def normalize_page_references(
        cls,
        values: list[str],
    ) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()

        for value in values:
            if not value.strip():
                raise ValueError(
                    "Une référence de preuve est vide."
                )

            # Preserve the exact reference identifier.
            if value not in seen:
                seen.add(value)
                result.append(value)

        return result


# ============================================================
# EDITORIAL PLAN GENERATED BY THE MODEL
# ============================================================

class ProductionEditorialPlan(ProductionModel):
    title: str = Field(
        min_length=1,
        max_length=250,
    )

    editorial_angle: str = Field(
        min_length=1,
        max_length=3000,
    )

    pages: list[ProductionPagePlan] = Field(
        min_length=4,
        max_length=40,
    )

    @field_validator(
        "title",
        "editorial_angle",
    )
    @classmethod
    def normalize_required_plan_text(
        cls,
        value: str,
    ) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "Un champ obligatoire du plan est vide."
            )

        return value

    @field_validator("pages")
    @classmethod
    def validate_plan_structure(
        cls,
        pages: list[ProductionPagePlan],
    ) -> list[ProductionPagePlan]:
        page_ids = [
            page.page_id
            for page in pages
        ]

        if len(page_ids) != len(set(page_ids)):
            raise ValueError(
                "Les identifiants des pages "
                "doivent être uniques."
            )

        if pages[0].layout != "COVER":
            raise ValueError(
                "La première page doit être "
                "une couverture."
            )

        if sum(
            page.layout == "COVER"
            for page in pages
        ) != 1:
            raise ValueError(
                "Le plan doit contenir "
                "une seule couverture."
            )

        if pages[-1].layout != "SOURCES":
            raise ValueError(
                "La dernière page doit présenter "
                "les sources."
            )

        return pages


# ============================================================
# PLAN ATTACHED TO ITS SOURCE CORPUS
# ============================================================

class ProductionPlanSnapshot(ProductionModel):
    production_id: str

    corpus_sha256: str

    generated_at: datetime

    status: Literal[
        "PLAN_TO_REVIEW"
    ] = "PLAN_TO_REVIEW"

    plan: ProductionEditorialPlan
