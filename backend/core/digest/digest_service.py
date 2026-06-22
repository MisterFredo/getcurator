from typing import (
    Dict,
    Any,
    List,
)

from uuid import uuid4

from datetime import (
    datetime,
    timedelta,
    timezone,
)
import json

from utils.bigquery_utils import (
    query_bq,
    insert_bq,
    update_bq,
    get_bigquery_client,
)

from config import (
    BQ_PROJECT,
    BQ_DATASET,
)

from google.cloud import (
    bigquery,
)

from core.digest.content_service import (
    get_digest_contents,
)

from core.digest.analysis_service import (
    generate_digest_analysis,
)

from core.insight.service import (
    get_analysis_details_by_ids,
)

# ============================================================
# TABLES
# ============================================================

TABLE_DIGEST = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_DIGEST"
)

TABLE_DIGEST_CONTENT = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_DIGEST_CONTENT"
)

TABLE_CONTENT_ENRICHED = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_ENRICHED"
)

# ============================================================
# PRIVATE
# ============================================================

def _load_digest(
    digest_id: str,
) -> Dict[str, Any]:

    rows = query_bq(
        f"""
        SELECT *
        FROM `{TABLE_DIGEST}`
        WHERE ID_DIGEST = @digest_id
        LIMIT 1
        """,
        {
            "digest_id": digest_id,
        },
    )

    if not rows:
        return {}

    return rows[0]


def _load_digest_content_ids(
    digest_id: str,
) -> List[str]:

    rows = query_bq(
        f"""
        SELECT
            ID_CONTENT
        FROM `{TABLE_DIGEST_CONTENT}`
        WHERE ID_DIGEST = @digest_id
        """,
        {
            "digest_id": digest_id,
        },
    )

    return [
        r["ID_CONTENT"]
        for r in rows
        if r.get("ID_CONTENT")
    ]


def _load_digest_contents(
    digest_id: str,
) -> List[Dict]:

    rows = query_bq(
        f"""
        SELECT
            c.*
        FROM `{TABLE_DIGEST_CONTENT}` dc

        JOIN `{TABLE_CONTENT_ENRICHED}` c
        ON dc.ID_CONTENT = c.id_content

        WHERE dc.ID_DIGEST = @digest_id

        ORDER BY c.published_at DESC
        """,
        {
            "digest_id": digest_id,
        },
    )

    contents = []

    for row in rows:

        companies = (
            row.get("companies")
            or []
        )

        primary_logo = None

        primary_company_id = (
            row.get(
                "ID_PRIMARY_COMPANY"
            )
        )

        if (
            primary_company_id
            and companies
        ):

            for company in companies:

                if (
                    company.get(
                        "id_company"
                    )
                    == primary_company_id
                ):

                    primary_logo = (
                        company.get(
                            "media_logo_rectangle_id"
                        )
                    )

        contents.append(
            {
                "id":
                    row.get(
                        "id_content"
                    ),

                "content_type":
                    (
                        row.get(
                            "CONTENT_TYPE"
                        )
                        or "analysis"
                    ).lower(),

                "title":
                    row.get(
                        "title"
                    ),

                "excerpt":
                    row.get(
                        "excerpt"
                    ),

                "published_at":
                    row.get(
                        "published_at"
                    ),

                "url":
                    (
                        f"https://www.getcurator.ai/feed?news_id={row.get('id_content')}"
                        if (
                            row.get(
                                "CONTENT_TYPE"
                            )
                            or ""
                        ).upper() == "NEWS"
                        else
                        f"https://www.getcurator.ai/feed?analysis_id={row.get('id_content')}"
                    ),

                "primary_company_logo":
                    primary_logo,

                "companies":
                    companies,

                "solutions":
                    row.get(
                        "solutions"
                    )
                    or [],

                "topics":
                    row.get(
                        "topics"
                    )
                    or [],

                "universes":
                    row.get(
                        "universes"
                    )
                    or [],

                "concepts":
                    row.get(
                        "concepts"
                    )
                    or [],
            }
        )

    return contents


# ============================================================
# CREATE
# ============================================================

def create_digest(
    user_id: str,
    digest_name: str,
    frequency: str = "WEEKLY",
) -> Dict:

    now = datetime.now(
        timezone.utc
    ).isoformat()

    # ========================================================
    # PERIOD
    # ========================================================

    period_start, period_end = (
        get_digest_period(
            frequency
        )
    )

    # ========================================================
    # DIGEST CONTENTS
    # ========================================================

    digest_data = get_digest_contents(
        user_id=user_id,
        period_start=period_start,
        period_end=period_end,
    )

    contents = (
        digest_data.get(
            "contents"
        )
        or []
    )

    if not contents:

        return {
            "status": "empty",
            "message":
                "No contents found",
        }

    # ========================================================
    # USER CONTEXT
    # ========================================================

    user_context = (
        digest_data.get(
            "user_context"
        )
        or {}
    )

    profile_text = (
        user_context.get(
            "profile_text"
        )
        or ""
    )

    keywords = (
        user_context.get(
            "keywords"
        )
        or []
    )

    language = (
        digest_data.get(
            "language"
        )
        or "fr"
    )

    # ========================================================
    # ANALYSIS
    # ========================================================

    analysis = (
        generate_digest_analysis(
            contents=contents,
            profile_text=profile_text,
        )
    )

    # ========================================================
    # DIGEST
    # ========================================================

    digest_id = str(
        uuid4()
    )

    insert_bq(
        TABLE_DIGEST,
        [
            {
                "ID_DIGEST":
                    digest_id,

                "ID_USER":
                    user_id,

                "DIGEST_NAME":
                    digest_name,

                "DIGEST_FREQUENCY":
                    frequency,

                "LANGUAGE":
                    language,

                "STATUS":
                    "GENERATED",

                "PERIOD_START":
                    period_start,

                "PERIOD_END":
                    period_end,

                "GENERATED_AT":
                    now,

                "NB_CONTENTS":
                    len(contents),

                "PROFILE_SNAPSHOT":
                    profile_text,

                "KEYWORDS_SNAPSHOT":
                    json.dumps(
                        keywords
                    ),

                "SUMMARY":
                    analysis.get(
                        "summary"
                    ),

                "IMPLICATIONS":
                    analysis.get(
                        "implications"
                    ),
            }
        ],
    )

    # ========================================================
    # CONTENTS
    # ========================================================

    rows = []

    for content in contents:

        rows.append(
            {
                "ID_DIGEST":
                    digest_id,

                "ID_CONTENT":
                    content.get(
                        "id"
                    ),

                "CREATED_AT":
                    now,
            }
        )

    if rows:

        insert_bq(
            TABLE_DIGEST_CONTENT,
            rows,
        )

    # ========================================================
    # RESPONSE
    # ========================================================

    return {
        "status": "ok",

        "id_digest":
            digest_id,

        "frequency":
            frequency,

        "period_start":
            period_start,

        "period_end":
            period_end,

        "nb_contents":
            len(contents),
    }

# ============================================================
# PERIODS
# ============================================================

def get_digest_period(
    frequency: str,
) -> tuple[str, str]:

    now = datetime.now(
        timezone.utc
    )

    frequency = (
        frequency or "WEEKLY"
    ).upper()

    if frequency == "QUARTERLY":

        period_start = (
            now - timedelta(days=90)
        )

    elif frequency == "MONTHLY":

        period_start = (
            now - timedelta(days=30)
        )

    else:

        frequency = "WEEKLY"

        period_start = (
            now - timedelta(days=7)
        )

    return (
        period_start.isoformat(),
        now.isoformat(),
    )

# ============================================================
# UPDATE DIGEST
# ============================================================

def update_digest(
    digest_id: str,
    digest_name: str,
    summary: str,
    implications: str,
) -> bool:

    update_bq(
        TABLE_DIGEST,
        fields={
            "DIGEST_NAME": digest_name,
            "SUMMARY": summary,
            "IMPLICATIONS": implications,
        },
        where={
            "ID_DIGEST": digest_id,
        },
    )

    return True

# ============================================================
# UPDATE DIGEST CONTENTS
# ============================================================

def update_digest_contents(
    digest_id: str,
    content_ids: List[str],
) -> bool:

    client = get_bigquery_client()

    client.query(
        f"""
        DELETE FROM `{TABLE_DIGEST_CONTENT}`
        WHERE ID_DIGEST = @digest_id
        """,
        job_config=bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter(
                    "digest_id",
                    "STRING",
                    digest_id,
                )
            ]
        ),
    ).result()

    now = datetime.now(
        timezone.utc
    ).isoformat()

    rows = []

    for content_id in content_ids:

        rows.append(
            {
                "ID_DIGEST": digest_id,
                "ID_CONTENT": content_id,
                "CREATED_AT": now,
            }
        )

    if rows:

        insert_bq(
            TABLE_DIGEST_CONTENT,
            rows,
        )

    update_bq(
        TABLE_DIGEST,
        fields={
            "NB_CONTENTS": len(content_ids),
        },
        where={
            "ID_DIGEST": digest_id,
        },
    )

    return True


# ============================================================
# LIST
# ============================================================

def list_digests(
    user_id: str,
) -> List[Dict]:

    return query_bq(
        f"""
        SELECT *
        FROM `{TABLE_DIGEST}`
        WHERE ID_USER = @user_id
        ORDER BY GENERATED_AT DESC
        """,
        {
            "user_id": user_id,
        },
    )

# ============================================================
# LIST ALL DIGESTS
# ============================================================

def list_all_digests() -> List[Dict]:

    rows = query_bq(
        f"""
        SELECT
            ID_DIGEST,
            ID_USER,
            DIGEST_NAME,
            LANGUAGE,
            STATUS,
            PERIOD_START,
            PERIOD_END,
            GENERATED_AT,
            SENT_AT,
            NB_CONTENTS
        FROM `{TABLE_DIGEST}`
        ORDER BY GENERATED_AT DESC
        """
    )

    return rows


# ============================================================
# GET
# ============================================================

def get_digest(
    digest_id: str,
) -> Dict:

    digest = (
        _load_digest(
            digest_id
        )
    )

    if not digest:

        return {}

    contents = (
        _load_digest_contents(
            digest_id
        )
    )

    return {
        "digest":
            digest,

        "contents":
            contents,
    }


# ============================================================
# DELETE
# ============================================================

def delete_digest(
    digest_id: str,
) -> Dict:

    client = get_bigquery_client()

    tables = [
        TABLE_DIGEST_CONTENT,
    ]

    for table in tables:

        client.query(
            f"""
            DELETE FROM `{table}`
            WHERE ID_DIGEST = @id
            """,
            job_config=bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter(
                        "id",
                        "STRING",
                        digest_id,
                    ),
                ]
            ),
        ).result()

    client.query(
        f"""
        DELETE FROM `{TABLE_DIGEST}`
        WHERE ID_DIGEST = @id
        """,
        job_config=bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter(
                    "id",
                    "STRING",
                    digest_id,
                ),
            ]
        ),
    ).result()

    return {
        "status": "ok",
    }
# ============================================================
# REGENERATE ANALYSIS
# ============================================================

def regenerate_analysis(
    digest_id: str,
) -> Dict:

    digest = (
        _load_digest(
            digest_id
        )
    )

    if not digest:

        return {
            "status":
                "not_found",
        }

    content_ids = (
        _load_digest_content_ids(
            digest_id
        )
    )

    contents = (
        get_analysis_details_by_ids(
            content_ids
        )
    )

    profile_text = (
        digest.get(
            "PROFILE_SNAPSHOT"
        )
        or ""
    )

    analysis = (
        generate_digest_analysis(
            contents=contents,
            profile_text=profile_text,
        )
    )

    update_bq(
        TABLE_DIGEST,

        {
            "SUMMARY":
                analysis.get(
                    "summary"
                ),

            "IMPLICATIONS":
                analysis.get(
                    "implications"
                ),
        },

        {
            "ID_DIGEST":
                digest_id,
        },
    )

    return {
        "status":
            "ok",

        "summary":
            analysis.get(
                "summary"
            ),

        "implications":
            analysis.get(
                "implications"
            ),
    }


# ============================================================
# SEND
# ============================================================

def send_digest(
    digest_id: str,
) -> Dict:
    now = datetime.now(
        timezone.utc
    ).isoformat()

    update_bq(
        TABLE_DIGEST,

        {
            "STATUS":
                "SENT",

            "SENT_AT":
                now,
        },

        {
            "ID_DIGEST":
                digest_id,
        },
    )

    return {
        "status":
            "ok",
    }
