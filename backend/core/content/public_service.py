from typing import List, Dict, Optional

from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import query_bq


# ============================================================
# TABLES
# ============================================================

TABLE_CONTENT_ENRICHED = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_ENRICHED"
)

# ============================================================
# CONTENT SUMMARY
# ============================================================

def _map_content_summary(
    r: Dict,
) -> Dict:

    id_primary_company = r.get(
        "id_primary_company"
    )

    companies = (
        r.get("companies")
        or []
    )

    primary_company = next(
        (
            c
            for c in companies
            if (
                c.get("id_company")
                == id_primary_company
            )
        ),
        None,
    )

    return {

        "id": r.get("id_content"),

        "title": r.get("title"),
        "title_en": r.get("title_en"),

        "excerpt": r.get("excerpt"),
        "excerpt_en": r.get("excerpt_en"),

        "published_at": r.get(
            "published_at"
        ),

        "signal": r.get(
            "signal_analytique"
        ),

        "source_title": r.get(
            "source_title"
        ),

        "source_url": r.get(
            "source_url"
        ),

        "id_primary_company": id_primary_company,

        "primary_company": primary_company,
    }


# ============================================================
# CONTENT
# ============================================================

def _map_content(
    r: Dict,
) -> Dict:

    content = _map_content_summary(r)

    content.update({

        # ====================================================
        # IDENTIFICATION
        # ====================================================

        "content_type": r.get(
            "content_type"
        ),

        "status": r.get(
            "status"
        ),

        "is_active": r.get(
            "is_active"
        ),

        "source_id": r.get(
            "source_id"
        ),

        "id_raw": r.get(
            "id_raw"
        ),

        "source_date": r.get(
            "source_date"
        ),

        "created_at": r.get(
            "created_at"
        ),

        "updated_at": r.get(
            "updated_at"
        ),

        # ====================================================
        # BODY
        # ====================================================

        "content_body": r.get(
            "content_body"
        ),

        # ====================================================
        # ANALYSIS
        # ====================================================

        "mecanique_expliquee": r.get(
            "mecanique_expliquee"
        ),

        "enjeu_strategique": r.get(
            "enjeu_strategique"
        ),

        "point_de_friction": r.get(
            "point_de_friction"
        ),

        # ====================================================
        # RAW EXTRACTIONS
        # ====================================================

        "chiffres": r.get(
            "chiffres"
        ) or [],

        "acteurs_cites": r.get(
            "acteurs_cites"
        ) or [],

        "topics_llm": r.get(
            "topics_llm"
        ) or [],

        "solutions_llm": r.get(
            "solutions_llm"
        ) or [],

        "concepts_llm": r.get(
            "concepts_llm"
        ) or [],

        # ====================================================
        # RELATIONS
        # ====================================================

        "universes": r.get(
            "universes"
        ) or [],

        "topics": r.get(
            "topics"
        ) or [],

        "companies": r.get(
            "companies"
        ) or [],

        "solutions": r.get(
            "solutions"
        ) or [],

        "concepts": r.get(
            "concepts"
        ) or [],

    })

    return content


# ============================================================
# LIST CONTENTS (CURATOR FEED)
# ============================================================

def list_contents(
    limit: int = 20,
    offset: int = 0,
    topic_id: Optional[str] = None,
    id_primary_company: Optional[str] = None,
):

    params = {
        "limit": limit,
        "offset": offset,
    }

    join = ""

    where_topic = ""
    where_primary_company = ""

    # ============================================================
    # TOPIC FILTER
    # ============================================================

    if topic_id:

        join += f"""
            JOIN `{TABLE_CONTENT_TOPIC}` ct
              ON c.ID_CONTENT = ct.ID_CONTENT
        """

        where_topic = "AND ct.ID_TOPIC = @topic_id"

        params["topic_id"] = topic_id


    # ============================================================
    # PRIMARY COMPANY FILTER
    # ============================================================

    if id_primary_company:

        where_primary_company = """
            AND c.ID_PRIMARY_COMPANY = @id_primary_company
        """

        params["id_primary_company"] = id_primary_company

    # ============================================================
    # QUERY
    # ============================================================

    sql = f"""
        SELECT
            c.ID_CONTENT,

            c.TITLE,
            c.TITLE_EN,

            c.EXCERPT,
            c.EXCERPT_EN,

            -- 🔥 NEW
            c.ID_PRIMARY_COMPANY,

            pc.NAME AS PRIMARY_COMPANY_NAME,

            c.SIGNAL_ANALYTIQUE,

            c.PUBLISHED_AT

        FROM `{TABLE_CONTENT}` c

        -- 🔥 NEW
        LEFT JOIN `{TABLE_COMPANY}` pc
          ON c.ID_PRIMARY_COMPANY = pc.ID_COMPANY

        {join}

        WHERE
            c.STATUS = 'PUBLISHED'
            AND c.IS_ACTIVE = TRUE

            {where_topic}

            {where_primary_company}

        ORDER BY c.PUBLISHED_AT DESC

        LIMIT @limit
        OFFSET @offset
    """

    rows = query_bq(sql, params)

    # ============================================================
    # RETURN
    # ============================================================

    return [
        {
            "id": r["ID_CONTENT"],

            "title": r["TITLE"],
            "title_en": r["TITLE_EN"],

            "excerpt": r.get("EXCERPT"),
            "excerpt_en": r.get("EXCERPT_EN"),

            # 🔥 NEW
            "id_primary_company": r.get(
                "ID_PRIMARY_COMPANY"
            ),

            "primary_company_name": r.get(
                "PRIMARY_COMPANY_NAME"
            ),

            "signal": r.get("SIGNAL_ANALYTIQUE"),

            "published_at": r["PUBLISHED_AT"],
        }
        for r in rows
    ]


# ============================================================
# READ CONTENT (DRAWER CURATOR)
# ============================================================

def get_content(id_content: str) -> Dict:

    rows = query_bq(
        f"""
        SELECT *
        FROM `{TABLE_CONTENT_ENRICHED}`
        WHERE id_content = @id_content
        LIMIT 1
        """,
        {"id_content": id_content},
    )

    if not rows:
        return None

    r = rows[0]


    # ============================================================
    # PRIMARY COMPANY
    # ============================================================

    primary_company = None

    id_primary_company = r.get(
        "id_primary_company"
    )

    companies = r.get("companies") or []

    if id_primary_company:

        primary_company = next(
            (
                c for c in companies
                if (
                    c.get("id_company")
                    == id_primary_company
                )
            ),
            None
        )

    # ============================================================
    # RETURN
    # ============================================================

    return {

        # ========================================================
        # CORE
        # ========================================================

        "id_content": r.get("id_content"),

        "title": r.get("title"),
        "title_en": r.get("title_en"),

        "excerpt": r.get("excerpt"),
        "excerpt_en": r.get("excerpt_en"),

        "content_body": r.get("content_body"),

        "published_at": r.get("published_at"),


        # ========================================================
        # PRIMARY COMPANY
        # ========================================================

        "id_primary_company": id_primary_company,

        "primary_company": primary_company,

        # ========================================================
        # ANALYSIS
        # ========================================================

        "signal": r.get("signal_analytique"),

        "mecanique_expliquee": r.get(
            "mecanique_expliquee"
        ),

        "enjeu_strategique": r.get(
            "enjeu_strategique"
        ),

        "point_de_friction": r.get(
            "point_de_friction"
        ),

        # ========================================================
        # RAW EXTRACTIONS
        # ========================================================

        "chiffres": r.get("chiffres") or [],

        "acteurs_cites": r.get("acteurs_cites") or [],

        "concepts_llm": r.get("concepts_llm") or [],

        # ========================================================
        # ENRICHED RELATIONS
        # ========================================================

        "topics": r.get("topics") or [],

        "companies": companies,

        "solutions": r.get("solutions") or [],

        "concepts": r.get("concepts") or [],

        "universes": r.get("universes") or [],
    }

