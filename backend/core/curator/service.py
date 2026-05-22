from typing import List, Dict, Optional

from config import BQ_PROJECT, BQ_DATASET

from utils.bigquery_utils import query_bq


TABLE_CONTENT_ENRICHED = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_ENRICHED"
)


# ============================================================
# 🔥 USER FILTER FACTO (UNIVERSES)
# ============================================================

def build_user_filter(alias: str = "c") -> str:
    return f"""
    AND EXISTS (
        SELECT 1
        FROM UNNEST({alias}.universes) u
        JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER_UNIVERSE` uu
          ON uu.ID_UNIVERSE = u.id_universe
        WHERE uu.ID_USER = @user_id
    )
    """


# ============================================================
# 🔥 CONTENT TYPE FILTER
# ============================================================

def build_content_type_filter() -> str:
    return """
    AND (
        @content_type IS NULL
        OR LOWER(c.content_type) = LOWER(@content_type)
    )
    """


# ============================================================
# 🔥 MY FEED FILTER
# ============================================================

def build_preferences_filter() -> str:
    return """
    AND (

        EXISTS (
            SELECT 1
            FROM UNNEST(c.companies) co
            WHERE co.id_company IN UNNEST(@fav_companies)
        )

        OR EXISTS (
            SELECT 1
            FROM UNNEST(c.topics) t
            WHERE t.id_topic IN UNNEST(@fav_topics)
        )

        OR EXISTS (
            SELECT 1
            FROM UNNEST(c.solutions) s
            WHERE s.id_solution IN UNNEST(@fav_solutions)
        )
    )
    """


# ============================================================
# 🔥 LOAD USER PREFS
# ============================================================

def load_user_preferences(
    user_id: Optional[str]
):

    if not user_id:
        return [], [], []

    from core.user.user_preferences_service import (
        get_user_preferences_grouped
    )

    prefs = (
        get_user_preferences_grouped(user_id)
        or {}
    )

    fav_companies = (
        prefs.get("COMPANY", [])
    )

    fav_topics = (
        prefs.get("TOPIC", [])
    )

    fav_solutions = (
        prefs.get("SOLUTION", [])
    )

    return (
        fav_companies,
        fav_topics,
        fav_solutions,
    )


# ============================================================
# SEARCH
# ============================================================

def search(
    q: str,
    limit: int = 20,
    offset: int = 0,
    user_id: Optional[str] = None,
    universe_id: Optional[str] = None,
    content_type: Optional[str] = None,
    feed_mode: Optional[str] = None,
) -> List[Dict]:

    q = (q or "").strip()

    (
        fav_companies,
        fav_topics,
        fav_solutions,
    ) = load_user_preferences(user_id)

    universe_filter = ""

    if universe_id:

        universe_filter = """
        AND EXISTS (
            SELECT 1
            FROM UNNEST(c.universes) u
            WHERE u.id_universe = @universe_id
        )
        """

    preferences_filter = ""

    if (
        feed_mode == "mine"
        and (
            fav_companies
            or fav_topics
            or fav_solutions
        )
    ):

        preferences_filter = (
            build_preferences_filter()
        )

    sql = f"""
    SELECT
        c.id_content AS id,

        LOWER(
            COALESCE(
                c.content_type,
                'ANALYSIS'
            )
        ) AS type,

        c.id_primary_company,

        c.title,
        c.title_en,

        c.excerpt,
        c.excerpt_en,

        c.content_body,

        c.published_at,

        c.topics,
        c.universes,
        c.companies,
        c.solutions,
        c.concepts,

        c.source_id

    FROM `{TABLE_CONTENT_ENRICHED}` c

    WHERE (

        LOWER(c.title)
            LIKE LOWER(CONCAT('%', @query, '%'))

        OR LOWER(c.title_en)
            LIKE LOWER(CONCAT('%', @query, '%'))

        OR LOWER(c.excerpt)
            LIKE LOWER(CONCAT('%', @query, '%'))

        OR LOWER(c.excerpt_en)
            LIKE LOWER(CONCAT('%', @query, '%'))
    )

    {build_content_type_filter()}
    {build_user_filter("c")}
    {universe_filter}
    {preferences_filter}

    ORDER BY published_at DESC

    LIMIT @limit
    OFFSET @offset
    """

    params = {
        "query": q,

        "limit": limit,
        "offset": offset,

        "user_id": user_id,

        "universe_id": universe_id,

        "content_type": content_type,

        "fav_companies": fav_companies,
        "fav_topics": fav_topics,
        "fav_solutions": fav_solutions,
    }

    rows = query_bq(sql, params)

    mapped = [
        _map_feed_row(r)
        for r in rows
    ]

    from core.user.user_service import (
        get_user_context
    )

    context = (
        get_user_context(user_id)
        if user_id else None
    )

    lang = (
        context["lang"]
        if context else "fr"
    )

    if lang == "en":

        for item in mapped:

            item["title"] = (
                item.get("title_en")
                or item.get("title")
            )

            item["excerpt"] = (
                item.get("excerpt_en")
                or item.get("excerpt")
            )

    return mapped


# ============================================================
# LATEST
# ============================================================

def latest(
    limit: int = 20,
    offset: int = 0,
    user_id: Optional[str] = None,
    universe_id: Optional[str] = None,
    content_type: Optional[str] = None,
    feed_mode: Optional[str] = None,
) -> List[Dict]:

    (
        fav_companies,
        fav_topics,
        fav_solutions,
    ) = load_user_preferences(user_id)

    universe_filter = ""

    if universe_id:

        universe_filter = """
        AND EXISTS (
            SELECT 1
            FROM UNNEST(c.universes) u
            WHERE u.id_universe = @universe_id
        )
        """

    preferences_filter = ""

    if (
        feed_mode == "mine"
        and (
            fav_companies
            or fav_topics
            or fav_solutions
        )
    ):

        preferences_filter = (
            build_preferences_filter()
        )

    sql = f"""
    SELECT
        c.id_content AS id,

        LOWER(
            COALESCE(
                c.content_type,
                'ANALYSIS'
            )
        ) AS type,

        c.id_primary_company,

        c.title,
        c.title_en,

        c.excerpt,
        c.excerpt_en,

        c.content_body,

        c.published_at,

        c.topics,
        c.universes,
        c.companies,
        c.solutions,
        c.concepts,

        c.source_id

    FROM `{TABLE_CONTENT_ENRICHED}` c

    WHERE c.published_at IS NOT NULL

    {build_content_type_filter()}
    {build_user_filter("c")}
    {universe_filter}
    {preferences_filter}

    ORDER BY published_at DESC

    LIMIT @limit
    OFFSET @offset
    """

    params = {
        "limit": limit,
        "offset": offset,

        "user_id": user_id,

        "universe_id": universe_id,

        "content_type": content_type,

        "fav_companies": fav_companies,
        "fav_topics": fav_topics,
        "fav_solutions": fav_solutions,
    }

    rows = query_bq(sql, params)

    mapped = [
        _map_feed_row(r)
        for r in rows
    ]

    from core.user.user_service import (
        get_user_context
    )

    context = (
        get_user_context(user_id)
        if user_id else None
    )

    lang = (
        context["lang"]
        if context else "fr"
    )

    if lang == "en":

        for item in mapped:

            item["title"] = (
                item.get("title_en")
                or item.get("title")
            )

            item["excerpt"] = (
                item.get("excerpt_en")
                or item.get("excerpt")
            )

    return mapped

# ============================================================
# ITEM
# ============================================================

def get_item_curator(
    item_id: str,
    user_id: Optional[str] = None
) -> Optional[Dict]:

    sql = f"""
    SELECT

        c.id_content AS id,

        LOWER(
            COALESCE(
                c.content_type,
                'ANALYSIS'
            )
        ) AS type,

        c.id_primary_company,

        c.title,
        c.title_en,
        c.excerpt,
        c.excerpt_en,
        c.published_at,

        source_url,
        source_title,

        c.topics,
        c.companies,
        c.solutions,
        c.concepts,

        SAFE_CAST(
            c.source_id AS STRING
        ) AS id_source

    FROM `{TABLE_CONTENT_ENRICHED}` c

    WHERE c.id_content = @id

    AND (
        @user_id IS NULL

        OR EXISTS (
            SELECT 1

            FROM `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOURCE_UNIVERSE` su

            JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER_UNIVERSE` uu
              ON uu.ID_UNIVERSE = su.ID_UNIVERSE

            WHERE uu.ID_USER = @user_id
              AND su.ID_SOURCE = c.source_id
        )
    )

    LIMIT 1
    """

    rows = query_bq(sql, {
        "id": item_id,
        "user_id": user_id,
    })

    if not rows:
        return None

    return _map_feed_row(rows[0])


# ============================================================
# DETAIL
# ============================================================

def get_item_detail(
    item_id: str,
    user_id: Optional[str] = None
) -> Optional[Dict]:

    item = get_item_curator(
        item_id,
        user_id=user_id
    )

    if not item:
        return None

    from core.content.public_service import (
        get_content
    )

    from core.translation.service import (
        translate_text
    )

    from core.user.user_service import (
        get_user_context
    )

    content = get_content(item_id)

    if not content:
        return None

    context = (
        get_user_context(user_id)
        if user_id else None
    )

    lang = (
        context["lang"]
        if context else "fr"
    )

    # ========================================================
    # FEED FIELDS
    # ========================================================

    if lang == "en":

        content["title"] = (
            content.get("title_en")
            or content.get("title")
        )

        content["excerpt"] = (
            content.get("excerpt_en")
            or content.get("excerpt")
        )

    # ========================================================
    # DRAWER DYNAMIC TRANSLATION
    # ========================================================

    if lang != "fr":

        try:

            content = {
                **content,

                "content_body": translate_text(
                    content.get("content_body", ""),
                    lang
                ),

                "mecanique_expliquee": translate_text(
                    content.get(
                        "mecanique_expliquee",
                        ""
                    ),
                    lang
                ),

                "enjeu_strategique": translate_text(
                    content.get(
                        "enjeu_strategique",
                        ""
                    ),
                    lang
                ),

                "point_de_friction": translate_text(
                    content.get(
                        "point_de_friction",
                        ""
                    ),
                    lang
                ),

                "signal_analytique": translate_text(
                    content.get(
                        "signal_analytique",
                        ""
                    ),
                    lang
                ),
            }

        except Exception:
            pass

    return {
        **content,

        "source_url": item.get("source_url"),
        "source_title": item.get("source_title"),

        "topics": item.get("topics", []),

        "companies": item.get("companies", []),

        "solutions": item.get("solutions", []),
    }

# ============================================================
# STATS
# ============================================================

def get_content_stats():

    global_rows = query_bq(f"""
        SELECT *
        FROM `{BQ_PROJECT}.{BQ_DATASET}.V_CONTENT_STATS_GLOBAL`
    """)

    if global_rows:

        g = global_rows[0]

        total_count = (
            g.get("total", 0)
            or 0
        )

        last_7 = (
            g.get("last_7_days", 0)
            or 0
        )

        last_30 = (
            g.get("last_30_days", 0)
            or 0
        )

    else:

        total_count = 0
        last_7 = 0
        last_30 = 0

    topics_rows = query_bq(f"""
        SELECT *
        FROM `{BQ_PROJECT}.{BQ_DATASET}.V_CONTENT_STATS_TOPIC`
        ORDER BY total DESC
    """)

    topics_stats = [
        {
            "id_topic": r.get("id_topic"),
            "label": r.get("label"),

            "total_count":
                r.get("total", 0) or 0,

            "last_7_days":
                r.get("last_7_days", 0) or 0,

            "last_30_days":
                r.get("last_30_days", 0) or 0,
        }

        for r in topics_rows

        if (
            r.get("id_topic")
            and r.get("label")
        )
    ]

    company_rows = query_bq(f"""
        SELECT *
        FROM `{BQ_PROJECT}.{BQ_DATASET}.V_CONTENT_STATS_COMPANY`
        ORDER BY total DESC
    """)

    top_companies = [
        {
            "id_company": r.get("id_company"),
            "name": r.get("name"),

            "total_count":
                r.get("total", 0) or 0,

            "last_7_days":
                r.get("last_7_days", 0) or 0,

            "last_30_days":
                r.get("last_30_days", 0) or 0,
        }

        for r in company_rows

        if (
            r.get("id_company")
            and r.get("name")
        )
    ]

    solution_rows = query_bq(f"""
        SELECT *
        FROM `{BQ_PROJECT}.{BQ_DATASET}.V_CONTENT_STATS_SOLUTION`
        ORDER BY total DESC
    """)

    top_solutions = [
        {
            "id_solution": r.get("id_solution"),
            "name": r.get("name"),

            "total_count":
                r.get("total", 0) or 0,

            "last_7_days":
                r.get("last_7_days", 0) or 0,

            "last_30_days":
                r.get("last_30_days", 0) or 0,
        }

        for r in solution_rows

        if (
            r.get("id_solution")
            and r.get("name")
        )
    ]

    return {
        "total_count": total_count,

        "last_7_days": last_7,

        "last_30_days": last_30,

        "topics_stats": topics_stats,

        "top_companies": top_companies,

        "top_solutions": top_solutions,
    }


# ============================================================
# MAPPER
# ============================================================

def _map_feed_row(r: Dict) -> Dict:

    topics = r.get("topics") or []
    companies = r.get("companies") or []
    solutions = r.get("solutions") or []
    concepts = r.get("concepts") or []
    universes = r.get("universes") or []

    badges = []

    for t in topics:

        if isinstance(t, dict):

            badges.append({
                "type": "topic",
                "label":
                    t.get("label")
                    or t.get("name"),

                "id":
                    t.get("id_topic"),
            })

        else:

            badges.append({
                "type": "topic",
                "label": t,
            })

    for c in concepts:

        if isinstance(c, dict):

            badges.append({
                "type": "concept",
                "label": c.get("label"),
                "id": c.get("id_concept"),
            })

        else:

            badges.append({
                "type": "concept",
                "label": c,
            })

    for c in companies:

        if not isinstance(c, dict):
            continue

        cid = (
            c.get("id_company")
            or c.get("id")
        )

        if not cid:
            continue

        badges.append({
            "type": "company",
            "label": c.get("name"),
            "id": cid,
        })

    for s in solutions:

        if not isinstance(s, dict):
            continue

        sid = (
            s.get("id_solution")
            or s.get("id")
        )

        if not sid:
            continue

        badges.append({
            "type": "solution",
            "label": s.get("name"),
            "id": sid,
        })

    for u in universes:

        if not isinstance(u, dict):
            continue

        uid = (
            u.get("id_universe")
            or u.get("id")
        )

        if not uid:
            continue

        badges.append({
            "type": "universe",
            "label": u.get("label"),
            "id": uid,
        })

    return {
        "id": r.get("id"),

        "type": r.get("type"),

        "id_primary_company":
            r.get("id_primary_company"),

        "title": r.get("title"),
        "title_en": r.get("title_en"),

        "excerpt": r.get("excerpt"),
        "excerpt_en": r.get("excerpt_en"),

        "source_url":
            r.get("source_url"),

        "source_title":
            r.get("source_title"),

        "content_body":
            r.get("content_body"),

        "published_at":
            r.get("published_at"),

        "topics": topics,

        "companies": companies,

        "solutions": solutions,

        "concepts": concepts,

        "universes": universes,

        "badges": badges,
    }
