import json
from uuid import uuid4

from config import BQ_DATASET, BQ_PROJECT
from core.expertise.content_service import load_contents_by_ids
from core.touch.notebook_models import (
    TouchCorpusNotebook,
    TouchNotebookRequest,
)
from utils.bigquery_utils import query_bq


TABLE_TOUCH_REPORT = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_TOUCH_REPORT"
)


def _read_json(value):
    if isinstance(value, str):
        return json.loads(value)
    return value


def save_touch_report(
    request: TouchNotebookRequest,
    notebook: TouchCorpusNotebook,
) -> str:
    """Save one immutable snapshot; return its report ID."""

    if not request.content_ids:
        raise ValueError("Impossible d'enregistrer un corpus vide")

    contents = load_contents_by_ids(
        content_ids=request.content_ids,
        language=request.output_language,
    )

    contents_by_id = {
        content.id: content
        for content in contents
    }

    if set(contents_by_id) != set(request.content_ids):
        raise ValueError(
            "Impossible d'enregistrer le rapport : "
            "certaines sources sont introuvables"
        )

    # Snapshot limité aux métadonnées affichables.
    # Ne stocke pas à nouveau le corps intégral des articles.
    sources = [
        {
            "content_id": content_id,
            "title": getattr(
                contents_by_id[content_id],
                "title",
                None,
            ),
            "original_title": getattr(
                contents_by_id[content_id],
                "original_title",
                None,
            ),
            "source_name": getattr(
                contents_by_id[content_id],
                "source_name",
                None,
            ),
            "url": getattr(
                contents_by_id[content_id],
                "url",
                None,
            ),
            "published_at": getattr(
                contents_by_id[content_id],
                "published_at",
                None,
            ),
        }
        for content_id in request.content_ids
    ]

    report_id = str(uuid4())

    query_bq(
        f"""
        INSERT INTO `{TABLE_TOUCH_REPORT}` (
            REPORT_ID,
            PARENT_REPORT_ID,
            VERSION_NUMBER,
            CREATED_AT,
            SUBJECT,
            OBJECTIVE,
            OUTPUT_LANGUAGE,
            CONTENT_IDS,
            CONTRIBUTIONS_JSON,
            SOURCES_JSON,
            NOTEBOOK_JSON
        )
        SELECT
            @report_id,
            NULL,
            1,
            CURRENT_TIMESTAMP(),
            @subject,
            @objective,
            @output_language,
            JSON_VALUE_ARRAY(@content_ids_json),
            PARSE_JSON(@contributions_json),
            PARSE_JSON(@sources_json),
            PARSE_JSON(@notebook_json)
        """,
        {
            "report_id": report_id,
            "subject": request.subject,
            "objective": request.objective,
            "output_language": request.output_language,
            "content_ids_json": json.dumps(
                request.content_ids,
                ensure_ascii=False,
            ),
            "contributions_json": json.dumps(
                [
                    contribution.model_dump(mode="json")
                    for contribution in request.contributions
                ],
                ensure_ascii=False,
            ),
            "sources_json": json.dumps(
                sources,
                ensure_ascii=False,
                default=str,
            ),
            "notebook_json": notebook.model_dump_json(),
        },
    )

    return report_id


def list_touch_reports(limit: int = 50) -> list[dict]:
    rows = query_bq(
        f"""
        SELECT
            REPORT_ID,
            PARENT_REPORT_ID,
            VERSION_NUMBER,
            CREATED_AT,
            SUBJECT,
            OBJECTIVE,
            OUTPUT_LANGUAGE,
            ARRAY_LENGTH(CONTENT_IDS) AS SOURCE_COUNT
        FROM `{TABLE_TOUCH_REPORT}`
        ORDER BY CREATED_AT DESC
        LIMIT @limit
        """,
        {"limit": min(max(limit, 1), 100)},
    ) or []

    return [
        {
            "report_id": row["REPORT_ID"],
            "parent_report_id": row["PARENT_REPORT_ID"],
            "version_number": row["VERSION_NUMBER"],
            "created_at": str(row["CREATED_AT"]),
            "subject": row["SUBJECT"],
            "objective": row["OBJECTIVE"],
            "output_language": row["OUTPUT_LANGUAGE"],
            "source_count": row["SOURCE_COUNT"],
        }
        for row in rows
    ]


def get_touch_report(report_id: str) -> dict | None:
    rows = query_bq(
        f"""
        SELECT
            REPORT_ID,
            PARENT_REPORT_ID,
            VERSION_NUMBER,
            CREATED_AT,
            SUBJECT,
            OBJECTIVE,
            OUTPUT_LANGUAGE,
            CONTENT_IDS,
            CONTRIBUTIONS_JSON,
            SOURCES_JSON,
            NOTEBOOK_JSON
        FROM `{TABLE_TOUCH_REPORT}`
        WHERE REPORT_ID = @report_id
        LIMIT 1
        """,
        {"report_id": report_id},
    ) or []

    if not rows:
        return None

    row = rows[0]

    # Vérifie que l'instantané reste compatible avec
    # le modèle de Notebook actuellement déployé.
    notebook = TouchCorpusNotebook.model_validate(
        _read_json(row["NOTEBOOK_JSON"])
    )

    return {
        "report_id": row["REPORT_ID"],
        "parent_report_id": row["PARENT_REPORT_ID"],
        "version_number": row["VERSION_NUMBER"],
        "created_at": str(row["CREATED_AT"]),
        "subject": row["SUBJECT"],
        "objective": row["OBJECTIVE"],
        "output_language": row["OUTPUT_LANGUAGE"],
        "content_ids": row["CONTENT_IDS"],
        "contributions": _read_json(
            row["CONTRIBUTIONS_JSON"]
        ),
        "sources": _read_json(row["SOURCES_JSON"]),
        "notebook": notebook.model_dump(mode="json"),
    }
