import json

from datetime import datetime
from uuid import NAMESPACE_URL, uuid5

from config import BQ_DATASET, BQ_PROJECT
from utils.bigquery_utils import query_bq


TABLE_TOUCH_EDITION = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_TOUCH_EDITION"
)


# ============================================================
# IDENTITY AND READ
# ============================================================

def build_touch_edition_id(
    expert_id: str,
    period_start: datetime,
) -> str:
    """One stable identity per expert and complete UTC calendar month."""
    return str(uuid5(
        NAMESPACE_URL,
        f"getcurator:touch:{expert_id}:{period_start:%Y-%m}",
    ))


def get_touch_edition(
    edition_id: str,
) -> dict | None:

    rows = query_bq(
        f"""
        SELECT *
        FROM `{TABLE_TOUCH_EDITION}`
        WHERE EDITION_ID = @edition_id
        LIMIT 1
        """,
        {"edition_id": edition_id},
    ) or []

    if not rows:
        return None

    row = rows[0]
    search = row.get("SEARCH_JSON")
    if isinstance(search, str):
        search = json.loads(search)

    def timestamp(name):
        value = row.get(name)
        return value.isoformat() if value is not None else None

    return {
        "edition_id": row["EDITION_ID"],
        "expert_id": row["EXPERT_ID"],
        "period_start": timestamp("PERIOD_START"),
        "period_end": timestamp("PERIOD_END"),
        "status": row["STATUS"],
        "subject": row["SUBJECT"],
        "output_language": row["OUTPUT_LANGUAGE"],
        "search": search,
        "selected_content_ids": list(row.get("SELECTED_CONTENT_IDS") or []),
        "dismissed_content_ids": list(row.get("DISMISSED_CONTENT_IDS") or []),
        "report_id": row.get("REPORT_ID"),
        "error": row.get("ERROR"),
        "created_at": timestamp("CREATED_AT"),
        "updated_at": timestamp("UPDATED_AT"),
    }


# ============================================================
# CLAIM A NEW OR FAILED EDITION
# ============================================================

def claim_touch_edition(
    edition_id: str,
    expert_id: str,
    period_start: datetime,
    period_end: datetime,
    subject: str,
    output_language: str,
) -> None:
    """Ready, reviewed and generated editions are never reset."""
    query_bq(
        f"""
        MERGE `{TABLE_TOUCH_EDITION}` AS target
        USING (SELECT @edition_id AS EDITION_ID) AS source
        ON target.EDITION_ID = source.EDITION_ID
        WHEN MATCHED AND target.STATUS = 'ERROR' THEN
          UPDATE SET
            STATUS = 'BUILDING',
            SUBJECT = @subject,
            OUTPUT_LANGUAGE = @output_language,
            ERROR = NULL,
            UPDATED_AT = CURRENT_TIMESTAMP()
        WHEN NOT MATCHED THEN
          INSERT (
            EDITION_ID, EXPERT_ID, PERIOD_START, PERIOD_END,
            STATUS, SUBJECT, OUTPUT_LANGUAGE, SEARCH_JSON,
            SELECTED_CONTENT_IDS, DISMISSED_CONTENT_IDS,
            REPORT_ID, ERROR, CREATED_AT, UPDATED_AT
          )
          VALUES (
            @edition_id, @expert_id,
            CAST(@period_start AS TIMESTAMP),
            CAST(@period_end AS TIMESTAMP),
            'BUILDING', @subject, @output_language, NULL,
            ARRAY<STRING>[], ARRAY<STRING>[],
            NULL, NULL, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()
          )
        """,
        {
            "edition_id": edition_id,
            "expert_id": expert_id,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "subject": subject,
            "output_language": output_language,
        },
    )


# ============================================================
# STORE PROPOSED CORPUS OR FAILURE
# ============================================================

def save_touch_edition_search(
    edition_id: str,
    search: dict,
) -> None:
    """No content is selected on the administrator's behalf."""
    query_bq(
        f"""
        UPDATE `{TABLE_TOUCH_EDITION}`
        SET
          STATUS = 'TO_REVIEW',
          SEARCH_JSON = PARSE_JSON(@search_json),
          ERROR = NULL,
          UPDATED_AT = CURRENT_TIMESTAMP()
        WHERE EDITION_ID = @edition_id
          AND STATUS = 'BUILDING'
        """,
        {
            "edition_id": edition_id,
            "search_json": json.dumps(search, ensure_ascii=False),
        },
    )


def record_touch_edition_error(
    edition_id: str,
    error: str,
) -> None:
    query_bq(
        f"""
        UPDATE `{TABLE_TOUCH_EDITION}`
        SET
          STATUS = 'ERROR',
          ERROR = @error,
          UPDATED_AT = CURRENT_TIMESTAMP()
        WHERE EDITION_ID = @edition_id
          AND STATUS = 'BUILDING'
        """,
        {"edition_id": edition_id, "error": error[:4000]},
    )


# ============================================================
# LIST EDITIONS AND SAVE MANUAL CORPUS
# ============================================================

def list_touch_editions(
    expert_id: str | None = None,
    limit: int = 100,
) -> list[dict]:
    where = "WHERE EXPERT_ID = @expert_id" if expert_id else ""
    params = {"limit": min(max(limit, 1), 200)}
    if expert_id:
        params["expert_id"] = expert_id

    rows = query_bq(
        f"""
        SELECT
          EDITION_ID, EXPERT_ID, PERIOD_START, PERIOD_END,
          STATUS, SUBJECT, OUTPUT_LANGUAGE,
          REPORT_ID, ERROR, CREATED_AT, UPDATED_AT,
          (SELECT MAX(r.ARCHIVED_AT)
           FROM `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_TOUCH_REPORT` r
           WHERE r.REPORT_ID = edition.REPORT_ID) AS ARCHIVED_AT,
          ARRAY_LENGTH(SELECTED_CONTENT_IDS) AS SELECTED_COUNT,
          ARRAY_LENGTH(
            JSON_QUERY_ARRAY(SEARCH_JSON, '$.candidates')
          ) AS CANDIDATE_COUNT,
          CASE
            WHEN JSON_QUERY_ARRAY(SEARCH_JSON, '$.candidates') IS NULL
              THEN NULL
            ELSE (
              SELECT COUNT(*)
              FROM UNNEST(
                JSON_QUERY_ARRAY(SEARCH_JSON, '$.candidates')
              ) AS candidate
              WHERE NOT EXISTS (
                SELECT 1
                FROM UNNEST(DISMISSED_CONTENT_IDS) AS dismissed_id
                WHERE dismissed_id = JSON_VALUE(candidate, '$.content_id')
              )
              AND COALESCE((
                SELECT JSON_VALUE(decision, '$.relevance')
                FROM UNNEST(
                  JSON_QUERY_ARRAY(SEARCH_JSON, '$.evaluation.decisions')
                ) AS decision WITH OFFSET AS decision_position
                WHERE JSON_VALUE(decision, '$.content_id')
                  = JSON_VALUE(candidate, '$.content_id')
                ORDER BY decision_position DESC
                LIMIT 1
              ), '') != 'OUT_OF_SCOPE'
            )
          END AS PROPOSED_COUNT
        FROM `{TABLE_TOUCH_EDITION}` AS edition
        {where}
        ORDER BY PERIOD_START DESC, CREATED_AT DESC
        LIMIT @limit
        """,
        params,
    ) or []

    return [
        {
            "edition_id": row["EDITION_ID"],
            "expert_id": row["EXPERT_ID"],
            "period_start": row["PERIOD_START"].isoformat(),
            "period_end": row["PERIOD_END"].isoformat(),
            "status": row["STATUS"],
            "subject": row["SUBJECT"],
            "output_language": row["OUTPUT_LANGUAGE"],
            "report_id": row.get("REPORT_ID"),
            "error": row.get("ERROR"),
            "created_at": row["CREATED_AT"].isoformat(),
            "updated_at": row["UPDATED_AT"].isoformat(),
            "selected_count": row["SELECTED_COUNT"],
            "candidate_count": row.get("CANDIDATE_COUNT"),
            "proposed_count": row.get("PROPOSED_COUNT"),
            "archived_at": str(row["ARCHIVED_AT"]) if row.get("ARCHIVED_AT") else None,
        }
        for row in rows
    ]


def update_touch_edition_corpus(
    edition_id: str,
    selected_content_ids: list[str],
    dismissed_content_ids: list[str],
) -> dict | None:
    edition = get_touch_edition(edition_id)
    if edition is None:
        return None
    if edition["status"] != "TO_REVIEW":
        raise ValueError(
            "Seule une édition à réviser peut modifier son corpus."
        )

    selected = list(dict.fromkeys(selected_content_ids))
    dismissed = list(dict.fromkeys(dismissed_content_ids))
    if set(selected) & set(dismissed):
        raise ValueError("Un contenu ne peut pas être sélectionné et écarté.")

    known_ids = {
        candidate["content_id"]
        for candidate in (edition.get("search") or {}).get("candidates", [])
    }
    if (set(selected) | set(dismissed)) - known_ids:
        raise ValueError("Le corpus contient des identifiants inconnus.")

    query_bq(
        f"""
        UPDATE `{TABLE_TOUCH_EDITION}`
        SET
          SELECTED_CONTENT_IDS = JSON_VALUE_ARRAY(@selected_json),
          DISMISSED_CONTENT_IDS = JSON_VALUE_ARRAY(@dismissed_json),
          UPDATED_AT = CURRENT_TIMESTAMP()
        WHERE EDITION_ID = @edition_id
          AND STATUS = 'TO_REVIEW'
        """,
        {
            "edition_id": edition_id,
            "selected_json": json.dumps(selected),
            "dismissed_json": json.dumps(dismissed),
        },
    )
    return get_touch_edition(edition_id)


# ============================================================
# LINK A SAVED REPORT TO ITS MONTHLY EDITION
# ============================================================

def link_touch_edition_report(
    edition_id: str,
    report_id: str,
) -> dict | None:
    from core.touch.notebook_report_service import get_touch_report

    edition = get_touch_edition(edition_id)
    if edition is None:
        return None
    if edition["status"] not in ("TO_REVIEW", "GENERATED"):
        raise ValueError("Le corpus de cette édition n'est pas prêt.")

    report = get_touch_report(report_id)
    if report is None:
        raise ValueError("Rapport Touch introuvable.")
    if report.get("expert_id") != edition["expert_id"]:
        raise ValueError("Le rapport appartient à un autre expert.")

    for field in ("period_start", "period_end"):
        expected = datetime.fromisoformat(edition[field].replace("Z", "+00:00"))
        actual_text = report.get(field)
        if not actual_text:
            raise ValueError("La période du rapport est manquante.")
        actual = datetime.fromisoformat(actual_text.replace("Z", "+00:00"))
        # Browser dates have millisecond precision; BQ has microseconds.
        if abs((actual - expected).total_seconds()) > 0.001:
            raise ValueError("La période du rapport diffère de celle de l'édition.")

    selected = edition["selected_content_ids"]
    if not selected or set(selected) != set(report["content_ids"]):
        raise ValueError("Le rapport ne correspond pas au corpus enregistré.")

    if edition.get("report_id") not in (None, report_id):
        raise ValueError("Cette édition est déjà liée à un autre rapport.")

    query_bq(
        f"""
        UPDATE `{TABLE_TOUCH_EDITION}`
        SET STATUS = 'GENERATED',
            REPORT_ID = @report_id,
            ERROR = NULL,
            UPDATED_AT = CURRENT_TIMESTAMP()
        WHERE EDITION_ID = @edition_id
          AND STATUS IN ('TO_REVIEW', 'GENERATED')
          AND (REPORT_ID IS NULL OR REPORT_ID = @report_id)
        """,
        {"edition_id": edition_id, "report_id": report_id},
    )
    return get_touch_edition(edition_id)

def reopen_touch_edition(edition_id: str) -> dict | None:
    """Archive the linked document and preserve all corpus choices."""
    edition = get_touch_edition(edition_id)
    if edition is None:
        return None
    if edition["status"] == "TO_REVIEW":
        return edition
    if edition["status"] != "GENERATED":
        raise ValueError("Seule une édition générée peut être reprise.")
    query_bq(
        f"""
        BEGIN TRANSACTION;
        UPDATE `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_TOUCH_REPORT`
        SET ARCHIVED_AT = COALESCE(ARCHIVED_AT, CURRENT_TIMESTAMP())
        WHERE REPORT_ID IN (
            SELECT REPORT_ID FROM `{TABLE_TOUCH_EDITION}`
            WHERE EDITION_ID = @edition_id AND STATUS = 'GENERATED'
        );
        UPDATE `{TABLE_TOUCH_EDITION}`
        SET REPORT_ID = NULL, STATUS = 'TO_REVIEW', ERROR = NULL,
            UPDATED_AT = CURRENT_TIMESTAMP()
        WHERE EDITION_ID = @edition_id AND STATUS = 'GENERATED';
        COMMIT TRANSACTION;
        """,
        {"edition_id": edition_id},
    )
    return get_touch_edition(edition_id)

# ============================================================
# DELETE MONTHLY EDITION AND LINKED REPORT
# ============================================================

def delete_touch_edition(
    edition_id: str,
) -> bool:
    """Delete the edition, its corpus choices and its linked report."""

    cleaned_id = edition_id.strip()

    if not cleaned_id:
        raise ValueError(
            "L’identifiant de l’édition Touch est vide."
        )

    rows = query_bq(
        f"""
        DECLARE edition_exists BOOL DEFAULT FALSE;
        DECLARE edition_building BOOL DEFAULT FALSE;

        BEGIN TRANSACTION;

        SET edition_exists = EXISTS (
            SELECT 1
            FROM `{TABLE_TOUCH_EDITION}`
            WHERE EDITION_ID = @edition_id
        );

        SET edition_building = EXISTS (
            SELECT 1
            FROM `{TABLE_TOUCH_EDITION}`
            WHERE EDITION_ID = @edition_id
              AND STATUS = 'BUILDING'
        );

        IF edition_exists AND NOT edition_building THEN

            DELETE FROM
              `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_TOUCH_REPORT`
            WHERE REPORT_ID IN (
                SELECT REPORT_ID
                FROM `{TABLE_TOUCH_EDITION}`
                WHERE EDITION_ID = @edition_id
                  AND REPORT_ID IS NOT NULL
            );

            DELETE FROM `{TABLE_TOUCH_EDITION}`
            WHERE EDITION_ID = @edition_id;

        END IF;

        COMMIT TRANSACTION;

        SELECT
            edition_exists AS EDITION_EXISTS,
            edition_building AS EDITION_BUILDING;
        """,
        {
            "edition_id": cleaned_id,
        },
    ) or []

    if not rows:
        raise RuntimeError(
            "La réinitialisation de l’édition Touch "
            "n’a retourné aucun résultat."
        )

    if rows[0]["EDITION_BUILDING"]:
        raise ValueError(
            "Cette édition est en cours de construction. "
            "Attendez la fin avant de la réinitialiser."
        )

    return bool(
        rows[0]["EDITION_EXISTS"]
    )
