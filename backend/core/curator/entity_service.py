from typing import List, Dict, Optional

from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import query_bq

from core.company.service import get_company
from core.user.user_service import get_user_context
from core.user.user_preferences_service import get_user_preferences_grouped


# ============================================================
# TABLES / VIEWS
# ============================================================

TABLE_CONTENT_ENRICHED = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_ENRICHED"
)

VIEW_STATS_COMPANY = (
    f"{BQ_PROJECT}.{BQ_DATASET}.V_CONTENT_STATS_COMPANY"
)

VIEW_STATS_TOPIC = (
    f"{BQ_PROJECT}.{BQ_DATASET}.V_CONTENT_STATS_TOPIC"
)

VIEW_STATS_SOLUTION = (
    f"{BQ_PROJECT}.{BQ_DATASET}.V_CONTENT_STATS_SOLUTION"
)

TABLE_TOPIC = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_TOPIC"
)

TABLE_SOLUTION = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOLUTION"
)

TABLE_COMPANY_UNIVERSE = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY_UNIVERSE"
)

TABLE_USER_UNIVERSE = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER_UNIVERSE"
)


# ============================================================
# 🔥 GENERIC FEED BUILDER
# ============================================================

def _get_entity_feed(
    where_clause_content: str,
    params: Dict,
    limit: int = 50,
    offset: int = 0,
    user_id: Optional[str] = None,
    universe_id: Optional[str] = None,
    lang: str = "fr",
) -> List[Dict]:

    # ============================================================
    # 🔐 USER FILTER
    # ============================================================

    user_filter = ""

    if user_id:

        user_filter = f"""
        AND EXISTS (
            SELECT 1
            FROM UNNEST(c.companies) comp

            JOIN `{TABLE_COMPANY_UNIVERSE}` cu
              ON cu.ID_COMPANY = comp.id_company

            JOIN `{TABLE_USER_UNIVERSE}` uu
              ON uu.ID_UNIVERSE = cu.ID_UNIVERSE

            WHERE uu.ID_USER = @user_id
        )
        """

    # ============================================================
    # 🌍 UNIVERSE FILTER
    # ============================================================

    universe_filter = ""

    if universe_id:

        universe_filter = f"""
        AND EXISTS (
            SELECT 1
            FROM UNNEST(c.companies) comp

            JOIN `{TABLE_COMPANY_UNIVERSE}` cu
              ON cu.ID_COMPANY = comp.id_company

            WHERE cu.ID_UNIVERSE = @universe_id
        )
        """

    # ============================================================
    # QUERY
    # ============================================================

    sql = f"""
    SELECT

        c.id_content AS id,

        -- ========================================================
        -- 🔥 FRONT OBJECT TYPE
        -- ========================================================

        'content' AS type,

        -- ========================================================
        -- META
        -- ========================================================

        c.id_primary_company,

        c.title,
        c.title_en,

        c.excerpt,
        c.excerpt_en,

        c.published_at,

        c.topics,

        c.companies,

        c.solutions,

        c.concepts,

        c.universes,

        c.source_id

    FROM `{TABLE_CONTENT_ENRICHED}` c

    WHERE {where_clause_content}

    {user_filter}

    {universe_filter}

    ORDER BY c.published_at DESC

    LIMIT @limit
    OFFSET @offset
    """

    query_params = {
        **params,
        "limit": limit,
        "offset": offset,
        "user_id": user_id,
    }

    if universe_id:
        query_params["universe_id"] = universe_id

    rows = query_bq(sql, query_params)

    return [
        _map_feed_row(r, lang)
        for r in rows
    ]


# ============================================================
# COMPANY
# ============================================================

def get_company_feed(
    company_id: str,
    limit: int = 50,
    offset: int = 0,
    user_id: Optional[str] = None,
    universe_id: Optional[str] = None,
    lang: str = "fr",
) -> List[Dict]:

    return _get_entity_feed(
        where_clause_content="""

            EXISTS (
                SELECT 1
                FROM UNNEST(c.companies) co
                WHERE co.id_company = @company_id
            )

        """,
        params={
            "company_id": company_id
        },
        limit=limit,
        offset=offset,
        user_id=user_id,
        universe_id=universe_id,
        lang=lang,
    )


def get_company_view(
    company_id: str,
    limit: int = 50,
    offset: int = 0,
    user_id: Optional[str] = None,
    universe_id: Optional[str] = None
) -> Optional[Dict]:

    company = get_company(company_id)

    if not company:
        return None

    # ============================================================
    # STATS
    # ============================================================

    stats_rows = query_bq(
        f"""
        SELECT
            COALESCE(total, 0) AS NB_ANALYSES,
            COALESCE(last_30_days, 0) AS DELTA_30D

        FROM `{VIEW_STATS_COMPANY}`

        WHERE id_company = @company_id

        LIMIT 1
        """,
        {
            "company_id": company_id
        }
    )

    stats = stats_rows[0] if stats_rows else {}

    # ============================================================
    # USER CONTEXT
    # ============================================================

    context = (
        get_user_context(user_id)
        if user_id else None
    )

    lang = (
        context["lang"]
        if context else "fr"
    )

    # ============================================================
    # ITEMS
    # ============================================================

    items = get_company_feed(
        company_id=company_id,
        limit=limit,
        offset=offset,
        user_id=user_id,
        universe_id=universe_id,
        lang=lang,
    )

    # ============================================================
    # USER CONTEXT
    # ============================================================

    prefs = (
        get_user_preferences_grouped(user_id)
        if user_id else None
    )

    # ============================================================
    # PRIORITIZATION (PREFERENCES)
    # ============================================================

    if prefs:

        def score(item):
            score = 0

            for c in item.get("companies", []):
                if c.get("id_company") in prefs["COMPANY"]:
                    score += 2

            for t in item.get("topics", []):
                if t.get("id_topic") in prefs["TOPIC"]:
                    score += 1

            for s in item.get("solutions", []):
                if s.get("id_solution") in prefs["SOLUTION"]:
                    score += 1

            return score

        items = sorted(items, key=score, reverse=True)

    # ============================================================
    # RETURN
    # ============================================================

    return {
        **company,

        "nb_analyses": stats.get("NB_ANALYSES", 0),

        "delta_30d": stats.get("DELTA_30D", 0),

        "items": items,
    }


# ============================================================
# TOPIC
# ============================================================

def get_topic_feed(
    topic_id: str,
    limit: int = 50,
    offset: int = 0,
    user_id: Optional[str] = None,
    universe_id: Optional[str] = None,
    lang: str = "fr",
) -> List[Dict]:

    return _get_entity_feed(
        where_clause_content="""
            EXISTS (
                SELECT 1
                FROM UNNEST(c.topics) t
                WHERE t.id_topic = @topic_id
            )
        """,
        params={
            "topic_id": topic_id
        },
        limit=limit,
        offset=offset,
        user_id=user_id,
        universe_id=universe_id,
        lang=lang,
    )


def get_topic_view(
    topic_id: str,
    limit: int = 50,
    offset: int = 0,
    user_id: Optional[str] = None,
    universe_id: Optional[str] = None
) -> Dict:

    topic_rows = query_bq(
        f"""
        SELECT
            ID_TOPIC,
            LABEL,
            TOPIC_AXIS,
            DESCRIPTION

        FROM `{TABLE_TOPIC}`

        WHERE ID_TOPIC = @topic_id

        LIMIT 1
        """,
        {
            "topic_id": topic_id
        }
    )

    topic = topic_rows[0] if topic_rows else {}

    # ============================================================
    # STATS
    # ============================================================

    stats_rows = query_bq(
        f"""
        SELECT
            COALESCE(total, 0) AS NB_ANALYSES,
            COALESCE(last_30_days, 0) AS DELTA_30D

        FROM `{VIEW_STATS_TOPIC}`

        WHERE id_topic = @topic_id

        LIMIT 1
        """,
        {
            "topic_id": topic_id
        }
    )

    stats = stats_rows[0] if stats_rows else {}

    # ============================================================
    # USER CONTEXT
    # ============================================================

    context = (
        get_user_context(user_id)
        if user_id else None
    )

    lang = (
        context["lang"]
        if context else "fr"
    )

    # ============================================================
    # ITEMS
    # ============================================================

    items = get_topic_feed(
        topic_id=topic_id,
        limit=limit,
        offset=offset,
        user_id=user_id,
        universe_id=universe_id,
        lang=lang,
    )

    # ============================================================
    # USER CONTEXT
    # ============================================================

    prefs = (
        get_user_preferences_grouped(user_id)
        if user_id else None
    )

    # ============================================================
    # PRIORITIZATION
    # ============================================================

    if prefs:

        def score(item):
            score = 0

            for c in item.get("companies", []):
                if c.get("id_company") in prefs["COMPANY"]:
                    score += 2

            for t in item.get("topics", []):
                if t.get("id_topic") in prefs["TOPIC"]:
                    score += 1

            for s in item.get("solutions", []):
                if s.get("id_solution") in prefs["SOLUTION"]:
                    score += 1

            return score

        items = sorted(items, key=score, reverse=True)

    # ============================================================
    # RETURN
    # ============================================================

    return {
        "id_topic": topic_id,
        "label": topic.get("LABEL"),
        "topic_axis": topic.get("TOPIC_AXIS"),
        "description": topic.get("DESCRIPTION"),
        "nb_analyses": stats.get("NB_ANALYSES", 0),
        "delta_30d": stats.get("DELTA_30D", 0),
        "items": items
    }


# ============================================================
# SOLUTION
# ============================================================

def get_solution_feed(
    solution_id: str,
    limit: int = 50,
    offset: int = 0,
    user_id: Optional[str] = None,
    universe_id: Optional[str] = None,
    lang: str = "fr",
) -> List[Dict]:

    return _get_entity_feed(
        where_clause_content="""
            EXISTS (
                SELECT 1
                FROM UNNEST(c.solutions) s
                WHERE s.id_solution = @solution_id
            )
        """,
        params={
            "solution_id": solution_id
        },
        limit=limit,
        offset=offset,
        user_id=user_id,
        universe_id=universe_id,
        lang=lang,
    )


def get_solution_view(
    solution_id: str,
    limit: int = 50,
    offset: int = 0,
    user_id: Optional[str] = None,
    universe_id: Optional[str] = None
) -> Dict:

    solution_rows = query_bq(
        f"""
        SELECT
            s.ID_SOLUTION,
            s.NAME,

            c.NAME AS COMPANY_NAME,
            c.MEDIA_LOGO_RECTANGLE_ID

        FROM `{TABLE_SOLUTION}` s

        LEFT JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY` c
            ON c.ID_COMPANY = s.ID_COMPANY

        WHERE s.ID_SOLUTION = @solution_id

        LIMIT 1
        """,
        {
            "solution_id": solution_id
        }
    )

    solution = solution_rows[0] if solution_rows else {}

    # ============================================================
    # STATS
    # ============================================================

    stats_rows = query_bq(
        f"""
        SELECT
            COALESCE(total, 0) AS NB_ANALYSES,
            COALESCE(last_30_days, 0) AS DELTA_30D

        FROM `{VIEW_STATS_SOLUTION}`

        WHERE id_solution = @solution_id

        LIMIT 1
        """,
        {
            "solution_id": solution_id
        }
    )

    stats = stats_rows[0] if stats_rows else {}

    # ============================================================
    # USER CONTEXT
    # ============================================================

    context = (
        get_user_context(user_id)
        if user_id else None
    )

    lang = (
        context["lang"]
        if context else "fr"
    )

    # ============================================================
    # ITEMS
    # ============================================================

    items = get_solution_feed(
        solution_id=solution_id,
        limit=limit,
        offset=offset,
        user_id=user_id,
        universe_id=universe_id,
        lang=lang,
    )

    # ============================================================
    # USER CONTEXT
    # ============================================================

    prefs = (
        get_user_preferences_grouped(user_id)
        if user_id else None
    )

    # ============================================================
    # PRIORITIZATION
    # ============================================================

    if prefs:

        def score(item):
            score = 0

            for c in item.get("companies", []):
                if c.get("id_company") in prefs["COMPANY"]:
                    score += 2

            for t in item.get("topics", []):
                if t.get("id_topic") in prefs["TOPIC"]:
                    score += 1

            for s in item.get("solutions", []):
                if s.get("id_solution") in prefs["SOLUTION"]:
                    score += 1

            return score

        items = sorted(items, key=score, reverse=True)

    # ============================================================
    # RETURN
    # ============================================================

    return {
        "id_solution": solution_id,
        "name": solution.get("NAME"),
        "company_name": solution.get("COMPANY_NAME"),
        "media_logo_rectangle_id": solution.get("MEDIA_LOGO_RECTANGLE_ID"),
        "nb_analyses": stats.get("NB_ANALYSES", 0),
        "delta_30d": stats.get("DELTA_30D", 0),
        "items": items
    }


# ============================================================
# DEDUPE HELPERS
# ============================================================

def _dedupe_entities(
    items: List[Dict],
    id_key: str,
    label_key: str,
) -> List[Dict]:

    if not items:
        return []

    seen = set()

    cleaned = []

    for item in items:

        if not item:
            continue

        unique_id = item.get(id_key)

        if unique_id:

            key = f"{id_key}:{unique_id}"

        else:

            key = (
                item.get(label_key, "")
                .strip()
                .lower()
            )

        if key in seen:
            continue

        seen.add(key)

        cleaned.append(item)

    return cleaned


# ============================================================
# MAPPER
# ============================================================

def _map_feed_row(
    r: Dict,
    lang: str = "fr"
):

    def fmt(dt):
        return dt.isoformat() if dt else None

    return {

        "id": r.get("id"),


        # ========================================================
        # CONTENT
        # ========================================================

        "title": (

            r.get("title_en")

            if lang == "en"

            else None

        ) or r.get("title"),

        "title_en": r.get("title_en"),

        "excerpt": (

            r.get("excerpt_en")

            if lang == "en"

            else None

        ) or r.get("excerpt"),

        "excerpt_en": r.get("excerpt_en"),

        "published_at": fmt(
            r.get("published_at")
        ),

        # ========================================================
        # ENTITIES
        # ========================================================

        "topics": _dedupe_entities(
            r.get("topics") or [],
            "id_topic",
            "label",
        ),

        "companies": _dedupe_entities(
            r.get("companies") or [],
            "id_company",
            "name",
        ),

        "solutions": _dedupe_entities(
            r.get("solutions") or [],
            "id_solution",
            "name",
        ),

        "concepts": _dedupe_entities(
            r.get("concepts") or [],
            "id_concept",
            "label",
        ),

        "universes": _dedupe_entities(
            r.get("universes") or [],
            "id_universe",
            "label",
        ),
    }
