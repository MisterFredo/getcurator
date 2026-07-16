# backend/core/content/search_service.py

from math import ceil

from api.content.models import ContentSearchRequest

from config import (
    BQ_PROJECT,
    BQ_DATASET,
)

from utils.bigquery_utils import query_bq


# ============================================================
# TABLES
# ============================================================

TABLE_CONTENT = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT"
)

TABLE_CONTENT_COMPANY = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_COMPANY"
)

TABLE_CONTENT_SOLUTION = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_SOLUTION"
)

TABLE_CONTENT_TOPIC = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_TOPIC"
)

TABLE_CONTENT_CONCEPT = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_CONCEPT"
)


# ============================================================
# SEARCH
# ============================================================

def search_contents(
    request: ContentSearchRequest,
):

    filters = request.filters

    limit = request.page_size

    offset = (
        request.page - 1
    ) * request.page_size

    where = [
        "c.IS_ACTIVE = TRUE",
    ]

    params = {}

    # ========================================================
    # SEARCH
    # ========================================================

    if filters.search:

        where.append(
            """
            (
                UPPER(c.TITLE)
                    LIKE UPPER(@search)

                OR

                UPPER(c.SOURCE_TITLE)
                    LIKE UPPER(@search)

                OR

                UPPER(c.SOURCE_URL)
                    LIKE UPPER(@search)
            )
            """
        )

        params["search"] = (
            f"%{filters.search}%"
        )

    # ========================================================
    # COMPANY
    # ========================================================

    if filters.company_id:

        where.append(
            f"""
            EXISTS (
                SELECT 1

                FROM `{TABLE_CONTENT_COMPANY}` cc

                WHERE
                    cc.ID_CONTENT = c.ID_CONTENT
                AND
                    cc.ID_COMPANY = @company_id
            )
            """
        )

        params["company_id"] = (
            filters.company_id
        )

    # ========================================================
    # SOLUTION
    # ========================================================

    if filters.solution_id:

        where.append(
            f"""
            EXISTS (
                SELECT 1

                FROM `{TABLE_CONTENT_SOLUTION}` cs

                WHERE
                    cs.ID_CONTENT = c.ID_CONTENT
                AND
                    cs.ID_SOLUTION = @solution_id
            )
            """
        )

        params["solution_id"] = (
            filters.solution_id
        )

    # ========================================================
    # TOPIC
    # ========================================================

    if filters.topic_id:

        where.append(
            f"""
            EXISTS (
                SELECT 1

                FROM `{TABLE_CONTENT_TOPIC}` ct

                WHERE
                    ct.ID_CONTENT = c.ID_CONTENT
                AND
                    ct.ID_TOPIC = @topic_id
            )
            """
        )

        params["topic_id"] = (
            filters.topic_id
        )

    # ========================================================
    # CONCEPT
    # ========================================================

    if filters.concept_id:

        where.append(
            f"""
            EXISTS (
                SELECT 1

                FROM `{TABLE_CONTENT_CONCEPT}` cc

                WHERE
                    cc.ID_CONTENT = c.ID_CONTENT
                AND
                    cc.ID_CONCEPT = @concept_id
            )
            """
        )

        params["concept_id"] = (
            filters.concept_id
        )

    # ========================================================
    # SOURCE
    # ========================================================

    if filters.source_id:

        where.append(
            "c.SOURCE_ID = @source_id"
        )

        params["source_id"] = (
            filters.source_id
        )

    # ========================================================
    # DATES
    # ========================================================

    if filters.date_from:

        where.append(
            "c.SOURCE_DATE >= @date_from"
        )

        params["date_from"] = (
            filters.date_from
        )

    if filters.date_to:

        where.append(
            "c.SOURCE_DATE <= @date_to"
        )

        params["date_to"] = (
            filters.date_to
        )

    # ========================================================
    # NUMBERS
    # ========================================================

    if filters.only_numbers:

        where.append(
            """
            c.CHIFFRES IS NOT NULL
            AND TRIM(c.CHIFFRES) != ''
            """
        )

    # ========================================================
    # WHERE
    # ========================================================

    where_sql = "\nAND\n".join(
        where
    )

    # ========================================================
    # COUNT
    # ========================================================

    total_sql = f"""
    SELECT
        COUNT(*) AS TOTAL

    FROM `{TABLE_CONTENT}` c

    WHERE
        {where_sql}
    """

    total_rows = query_bq(
        total_sql,
        params,
    )

    total_results = (
        total_rows[0]["TOTAL"]
        if total_rows
        else 0
    )

    total_pages = max(
        1,
        ceil(
            total_results / limit
        ),
    )

    # ========================================================
    # DATA
    # ========================================================

    sql = f"""
    SELECT

        c.ID_CONTENT,

        c.TITLE,

        c.SOURCE_TITLE,

        c.SOURCE_DATE,

        c.PUBLISHED_AT

    FROM `{TABLE_CONTENT}` c

    WHERE
        {where_sql}

    ORDER BY

        c.SOURCE_DATE DESC,

        c.PUBLISHED_AT DESC,

        c.CREATED_AT DESC

    LIMIT @limit

    OFFSET @offset
    """

    params["limit"] = limit
    params["offset"] = offset

    rows = query_bq(
        sql,
        params,
    )

    contents = [
        {
            "id_content": r["ID_CONTENT"],
            "title": r.get(
                "TITLE"
            ),
            "source_title": r.get(
                "SOURCE_TITLE"
            ),
            "source_date": r.get(
                "SOURCE_DATE"
            ),
            "published_at": r.get(
                "PUBLISHED_AT"
            ),
        }
        for r in rows
    ]

    return {
        "contents": contents,
        "page": request.page,
        "page_size": limit,
        "total_results": total_results,
        "total_pages": total_pages,
        "has_next": request.page < total_pages,
        "has_previous": request.page > 1,
    }
