from utils.bigquery_utils import query_bq
from typing import List, Dict, Optional

TABLE_CONTENT = \
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT"

TABLE_CONTENT_COMPANY = \
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_COMPANY"

TABLE_COMPANY_ALIAS = \
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY_ALIAS"

# ============================================================
# REBUILD CONTENT → COMPANY
# ============================================================

def rebuild_content_company():

    sql = f"""
    INSERT INTO `{TABLE_CONTENT_COMPANY}` (
        ID_CONTENT,
        ID_COMPANY
    )

    SELECT DISTINCT
        c.ID_CONTENT,
        a.ID_COMPANY

    FROM `{TABLE_CONTENT}` c,
    UNNEST(c.ACTEURS_CITES) AS raw

    JOIN `{TABLE_COMPANY_ALIAS}` a
      ON REGEXP_REPLACE(
            UPPER(TRIM(raw)),
            r'[^A-Z0-9 ]',
            ''
         )
       =
         REGEXP_REPLACE(
            UPPER(TRIM(a.ALIAS)),
            r'[^A-Z0-9 ]',
            ''
         )

    WHERE raw IS NOT NULL
      AND TRIM(raw) != ""

      AND NOT EXISTS (

          SELECT 1

          FROM `{TABLE_CONTENT_COMPANY}` existing

          WHERE
              existing.ID_CONTENT = c.ID_CONTENT
          AND existing.ID_COMPANY = a.ID_COMPANY

      )
    """

    query_bq(sql)

    return {
        "status": "ok",
        "message": "Content → Company rebuilt.",
    }


# ============================================================
# PUBLISH CONTENT
# ============================================================

def publish_content(
    id_content: str,
    published_at: Optional[datetime] = None,
):

    now_dt = datetime.now(
        timezone.utc
    )

    # ========================================================
    # CHECK CONTENT
    # ========================================================

    rows = query_bq(
        f"""
        SELECT
            STATUS,
            SOURCE_DATE
        FROM `{TABLE_CONTENT}`
        WHERE ID_CONTENT = @id_content
        """,
        {
            "id_content": id_content,
        },
    )

    if not rows:
        raise ValueError(
            "Content introuvable"
        )

    current_status = rows[0]["STATUS"]

    source_date = rows[0]["SOURCE_DATE"]

    if current_status != "READY":
        raise ValueError(
            "Content must be READY before publish"
        )

    # ========================================================
    # PUBLISHED DATE
    # ========================================================

    if published_at is None:

        published_at = (
            source_date
            or now_dt
        )

    if (
        isinstance(published_at, date)
        and not isinstance(
            published_at,
            datetime,
        )
    ):

        published_at = datetime.combine(
            published_at,
            datetime.min.time(),
            tzinfo=timezone.utc,
        )

    elif (
        isinstance(
            published_at,
            datetime,
        )
        and published_at.tzinfo is None
    ):

        published_at = published_at.replace(
            tzinfo=timezone.utc,
        )

    # ========================================================
    # STATUS
    # ========================================================

    status = (
        "PUBLISHED"
        if published_at <= now_dt
        else "SCHEDULED"
    )

    # ========================================================
    # UPDATE CONTENT
    # ========================================================

    update_bq(
        table=TABLE_CONTENT,
        fields={
            "STATUS": status,
            "PUBLISHED_AT": published_at,
            "UPDATED_AT": now_dt,
        },
        where={
            "ID_CONTENT": id_content,
        },
    )

    # ========================================================
    # SYNC
    # ========================================================

    after_publish_sync(
        id_content=id_content,
    )

    print(
        "🚀 CONTENT PUBLISHED:",
        {
            "id_content": id_content,
            "status": status,
            "published_at": str(
                published_at,
            ),
        },
    )

    return status


def mark_content_ready(id_content: str):

    rows = query_bq(
        f"""
        SELECT STATUS
        FROM `{TABLE_CONTENT}`
        WHERE ID_CONTENT = @id_content
        """,
        {"id_content": id_content}
    )

    if not rows:
        raise ValueError("Content introuvable")

    current_status = rows[0]["STATUS"]

    if current_status == "READY":
        # Déjà ready → OK
        return

    if current_status not in ["DRAFT"]:
        raise ValueError(f"Cannot mark READY from status {current_status}")

    update_bq(
        TABLE_CONTENT,
        {
            "STATUS": "READY",
            "UPDATED_AT": datetime.utcnow().isoformat()
        },
        where={"ID_CONTENT": id_content}
    )

def bulk_ready(ids: list[str]) -> int:

    if not ids:
        return 0

    now = datetime.now(timezone.utc)

    query = f"""
        UPDATE `{TABLE_CONTENT}`
        SET
            STATUS = 'READY',
            UPDATED_AT = @now
        WHERE
            STATUS = 'DRAFT'
            AND ID_CONTENT IN UNNEST(@ids)
    """

    query_bq(
        query,
        {
            "ids": ids,
            "now": now,
        },
    )

    return len(ids)


def bulk_publish(ids: List[str]) -> Dict[str, int]:

    if not ids:
        return {"updated": 0, "skipped": 0}

    updated = 0
    skipped = 0

    for id_content in ids:
        try:
            publish_content(id_content)
            updated += 1
        except Exception:
            skipped += 1

    return {
        "updated": updated,
        "skipped": skipped,
    }

