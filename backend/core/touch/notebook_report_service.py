import json

from uuid import (
    uuid4,
)

from config import (
    BQ_DATASET,
    BQ_PROJECT,
)

from core.expertise.content_service import (
    load_contents_by_ids,
)

from core.touch.notebook_models import (
    TouchCorpusNotebook,
    TouchNotebookRequest,
)

from utils.bigquery_utils import (
    query_bq,
)


# ============================================================
# TABLES
# ============================================================

TABLE_TOUCH_REPORT = (
    f"{BQ_PROJECT}.{BQ_DATASET}."
    "RATECARD_TOUCH_REPORT"
)


# ============================================================
# HELPERS
# ============================================================

def _read_json(
    value,
):

    if isinstance(
        value,
        str,
    ):

        return json.loads(
            value
        )

    return value


def _normalize_report_id(
    report_id: str | None,
) -> str | None:

    normalized_report_id = (
        report_id
        or ""
    ).strip()

    return (
        normalized_report_id
        or None
    )


# ============================================================
# BUILD SOURCES SNAPSHOT
# ============================================================

def _build_sources_snapshot(
    request: TouchNotebookRequest,
) -> list[dict]:

    if not request.content_ids:

        raise ValueError(
            "Impossible d'enregistrer "
            "un corpus vide"
        )

    contents = load_contents_by_ids(

        content_ids=(
            request.content_ids
        ),

        language=(
            request.output_language
        ),

    )

    contents_by_id = {

        content.id:
            content

        for content in contents

    }

    missing_content_ids = [

        content_id

        for content_id
        in request.content_ids

        if (
            content_id
            not in contents_by_id
        )

    ]

    if missing_content_ids:

        raise ValueError(
            "Impossible d'enregistrer le rapport : "
            "certaines sources sont introuvables : "
            + ", ".join(
                missing_content_ids
            )
        )

    # Snapshot limité aux métadonnées affichables.
    # Le corps intégral des articles n'est pas stocké
    # une seconde fois dans le rapport.

    return [

        {
            "content_id":
                content_id,

            "title":
                getattr(
                    contents_by_id[
                        content_id
                    ],
                    "title",
                    None,
                ),

            "original_title":
                getattr(
                    contents_by_id[
                        content_id
                    ],
                    "original_title",
                    None,
                ),

            "source_name":
                getattr(
                    contents_by_id[
                        content_id
                    ],
                    "source_name",
                    None,
                ),

            "url":
                getattr(
                    contents_by_id[
                        content_id
                    ],
                    "url",
                    None,
                ),

            "published_at":
                getattr(
                    contents_by_id[
                        content_id
                    ],
                    "published_at",
                    None,
                ),
        }

        for content_id
        in request.content_ids

    ]


# ============================================================
# SAVE OR REPLACE REPORT
# ============================================================

def save_touch_report(
    request: TouchNotebookRequest,
    notebook: TouchCorpusNotebook,
    report_id: str | None = None,
) -> str:
    """
    Create a report when report_id is absent.

    Replace the existing snapshot when report_id is supplied.
    Only one database row is kept for one Touch report.
    """

    sources = (
        _build_sources_snapshot(
            request
        )
    )

    normalized_report_id = (
        _normalize_report_id(
            report_id
        )
    )

    effective_report_id = (

        normalized_report_id

        or str(
            uuid4()
        )

    )

    params = {
        "report_id":
            effective_report_id,

        "subject":
            request.subject,

        "objective":
            request.objective,

        "output_language":
            request.output_language,

        "content_ids_json":
            json.dumps(
                request.content_ids,
                ensure_ascii=False,
            ),

        "contributions_json":
            json.dumps(
                [

                    contribution.model_dump(
                        mode="json",
                    )

                    for contribution
                    in request.contributions

                ],
                ensure_ascii=False,
            ),

        "sources_json":
            json.dumps(
                sources,
                ensure_ascii=False,
                default=str,
            ),

        "notebook_json":
            notebook.model_dump_json(),
    }

    query_bq(
        f"""
        MERGE `{TABLE_TOUCH_REPORT}` AS target

        USING (

          SELECT

            @report_id AS REPORT_ID,

            @subject AS SUBJECT,

            @objective AS OBJECTIVE,

            @output_language AS OUTPUT_LANGUAGE,

            JSON_VALUE_ARRAY(
              @content_ids_json
            ) AS CONTENT_IDS,

            PARSE_JSON(
              @contributions_json
            ) AS CONTRIBUTIONS_JSON,

            PARSE_JSON(
              @sources_json
            ) AS SOURCES_JSON,

            PARSE_JSON(
              @notebook_json
            ) AS NOTEBOOK_JSON

        ) AS source

        ON
          target.REPORT_ID = source.REPORT_ID

        WHEN MATCHED THEN

          UPDATE SET

            target.CREATED_AT =
              CURRENT_TIMESTAMP(),

            target.SUBJECT =
              source.SUBJECT,

            target.OBJECTIVE =
              source.OBJECTIVE,

            target.OUTPUT_LANGUAGE =
              source.OUTPUT_LANGUAGE,

            target.CONTENT_IDS =
              source.CONTENT_IDS,

            target.CONTRIBUTIONS_JSON =
              source.CONTRIBUTIONS_JSON,

            target.SOURCES_JSON =
              source.SOURCES_JSON,

            target.NOTEBOOK_JSON =
              source.NOTEBOOK_JSON,

            target.VERSION_NUMBER =
              COALESCE(
                target.VERSION_NUMBER,
                0
              ) + 1

        WHEN NOT MATCHED THEN

          INSERT (
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

          VALUES (
            source.REPORT_ID,
            NULL,
            1,
            CURRENT_TIMESTAMP(),
            source.SUBJECT,
            source.OBJECTIVE,
            source.OUTPUT_LANGUAGE,
            source.CONTENT_IDS,
            source.CONTRIBUTIONS_JSON,
            source.SOURCES_JSON,
            source.NOTEBOOK_JSON
          )
        """,
        params,
    )

    return effective_report_id


# ============================================================
# LIST REPORTS
# ============================================================

def list_touch_reports(
    limit: int = 50,
) -> list[dict]:

    safe_limit = min(
        max(
            limit,
            1,
        ),
        100,
    )

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

          ARRAY_LENGTH(
            CONTENT_IDS
          ) AS SOURCE_COUNT

        FROM `{TABLE_TOUCH_REPORT}`

        ORDER BY

          CREATED_AT DESC

        LIMIT @limit
        """,
        {
            "limit":
                safe_limit,
        },
    ) or []

    return [

        {
            "report_id":
                row["REPORT_ID"],

            "parent_report_id":
                row[
                    "PARENT_REPORT_ID"
                ],

            "version_number":
                row[
                    "VERSION_NUMBER"
                ],

            "created_at":
                str(
                    row["CREATED_AT"]
                ),

            "subject":
                row["SUBJECT"],

            "objective":
                row["OBJECTIVE"],

            "output_language":
                row[
                    "OUTPUT_LANGUAGE"
                ],

            "source_count":
                row["SOURCE_COUNT"],
        }

        for row in rows

    ]


# ============================================================
# GET REPORT
# ============================================================

def get_touch_report(
    report_id: str,
) -> dict | None:

    normalized_report_id = (
        _normalize_report_id(
            report_id
        )
    )

    if not normalized_report_id:

        return None

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

        WHERE
          REPORT_ID = @report_id

        LIMIT 1
        """,
        {
            "report_id":
                normalized_report_id,
        },
    ) or []

    if not rows:

        return None

    row = rows[0]

    notebook = (
        TouchCorpusNotebook
        .model_validate(
            _read_json(
                row[
                    "NOTEBOOK_JSON"
                ]
            )
        )
    )

    return {
        "report_id":
            row["REPORT_ID"],

        "parent_report_id":
            row[
                "PARENT_REPORT_ID"
            ],

        "version_number":
            row[
                "VERSION_NUMBER"
            ],

        "created_at":
            str(
                row["CREATED_AT"]
            ),

        "subject":
            row["SUBJECT"],

        "objective":
            row["OBJECTIVE"],

        "output_language":
            row[
                "OUTPUT_LANGUAGE"
            ],

        "content_ids":
            list(
                row["CONTENT_IDS"]
                or []
            ),

        "contributions":
            _read_json(
                row[
                    "CONTRIBUTIONS_JSON"
                ]
            )
            or [],

        "sources":
            _read_json(
                row[
                    "SOURCES_JSON"
                ]
            )
            or [],

        "notebook":
            notebook.model_dump(
                mode="json",
            ),
    }


# ============================================================
# DELETE REPORT
# ============================================================

def delete_touch_report(
    report_id: str,
) -> bool:

    normalized_report_id = (
        _normalize_report_id(
            report_id
        )
    )

    if not normalized_report_id:

        return False

    existing_rows = query_bq(
        f"""
        SELECT
          REPORT_ID

        FROM `{TABLE_TOUCH_REPORT}`

        WHERE
          REPORT_ID = @report_id

        LIMIT 1
        """,
        {
            "report_id":
                normalized_report_id,
        },
    ) or []

    if not existing_rows:

        return False

    query_bq(
        f"""
        DELETE FROM `{TABLE_TOUCH_REPORT}`

        WHERE
          REPORT_ID = @report_id
        """,
        {
            "report_id":
                normalized_report_id,
        },
    )

    return True
