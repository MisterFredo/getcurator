"""Reusable content/layout contract. No topic-specific data or layouts."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class DocumentModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class DocumentSource(DocumentModel):
    id: str = Field(min_length=1, max_length=40)
    report_id: str
    report_version: int = Field(ge=1)
    # RFC 6901 pointer, relative to the saved report payload.
    json_pointer: str = Field(min_length=1, max_length=500)
    # Verbatim substring of the pointed value, not a model paraphrase.
    quote: str = Field(min_length=1, max_length=1200)
    content_id: str | None
    label: str = Field(min_length=1, max_length=300)


class DocumentMetric(DocumentModel):
    value: float
    display_value: str = Field(min_length=1, max_length=45)
    label: str = Field(min_length=1, max_length=120)
    context: str = Field(max_length=200)
    source_id: str


class DocumentChartPoint(DocumentModel):
    label: str = Field(min_length=1, max_length=30)
    value: float
    source_id: str


class DocumentChart(DocumentModel):
    kind: Literal["COMPARISON", "TREND"]
    title: str = Field(min_length=1, max_length=160)
    unit: str = Field(min_length=1, max_length=40)
    measure: str = Field(min_length=1, max_length=160)
    scope: str = Field(min_length=1, max_length=200)
    comparability_note: str = Field(min_length=1, max_length=350)
    points: list[DocumentChartPoint] = Field(min_length=2, max_length=6)


class DocumentPage(DocumentModel):
    page_id: str
    layout: Literal[
        "COVER", "SUMMARY", "METRICS", "COMPARISON", "TREND",
        "CASE_STUDY", "ANALYSIS", "IMPLICATIONS", "SOURCES",
    ]
    title: str = Field(min_length=1, max_length=160)
    eyebrow: str = Field(max_length=80)
    paragraphs: list[str] = Field(max_length=3)
    bullets: list[str] = Field(max_length=4)
    metrics: list[DocumentMetric] = Field(max_length=4)
    chart: DocumentChart | None
    takeaway: str = Field(max_length=450)
    cautions: list[str] = Field(max_length=3)
    source_ids: list[str]


class ProductionDocument(DocumentModel):
    schema_version: Literal["1.0"]
    template: Literal["GETCURATOR_AUTONOMOUS_V1"]
    title: str = Field(min_length=1, max_length=180)
    subtitle: str = Field(max_length=240)
    pages: list[DocumentPage] = Field(min_length=4, max_length=40)
    sources: list[DocumentSource] = Field(min_length=1, max_length=100)
    review_notes: list[str] = Field(max_length=30)

    @model_validator(mode="after")
    def validate_structure(self):
        if self.pages[0].layout != "COVER" or self.pages[-1].layout != "SOURCES":
            raise ValueError("Couverture en premier et sources en dernier obligatoires.")
        if sum(p.layout == "COVER" for p in self.pages) != 1 or sum(p.layout == "SOURCES" for p in self.pages) != 1:
            raise ValueError("Une seule couverture et une seule page sources.")
        ids = [p.page_id for p in self.pages]
        if len(ids) != len(set(ids)):
            raise ValueError("Identifiants de pages dupliqués.")
        source_ids = [s.id for s in self.sources]
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("Identifiants de sources dupliqués.")
        known = set(source_ids)
        for page in self.pages:
            cited = set(page.source_ids)
            if cited - known:
                raise ValueError(f"Page {page.page_id} : source inconnue.")
            if page.layout not in {"COVER", "SOURCES"} and not cited:
                raise ValueError(f"Page {page.page_id} : preuves absentes.")
            if sum(len(t) for t in page.paragraphs + page.bullets) > 2200:
                raise ValueError(f"Page {page.page_id} : texte trop long pour le modèle.")
            if any(not t.strip() for t in page.paragraphs + page.bullets):
                raise ValueError("Texte vide dans une page.")
            if page.chart and page.metrics:
                raise ValueError("Une page utilise un graphique OU des indicateurs, pas les deux.")
            if page.layout in {"COMPARISON", "TREND"}:
                if not page.chart or page.chart.kind != page.layout:
                    raise ValueError("Le graphique doit correspondre à la composition.")
            elif page.chart:
                raise ValueError("Graphique réservé aux compositions COMPARISON et TREND.")
            if page.layout == "METRICS" and not page.metrics:
                raise ValueError("METRICS nécessite au moins un indicateur.")
            refs = {m.source_id for m in page.metrics}
            if page.chart:
                refs |= {point.source_id for point in page.chart.points}
            if refs - cited:
                raise ValueError(f"Page {page.page_id} : citer les sources des indicateurs et du graphique.")
        return self
