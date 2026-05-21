from typing import List, Dict, Optional

from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import query_bq


TABLE_CONTENT_ENRICHED = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_ENRICHED"
)


# ============================================================
# 🔥 USER FILTER FACTO (SOURCE_ID cohérent)
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

    sql = f"""
    SELECT
        c.id_content AS id,
        LOWER(COALESCE(c.content_type, 'ANALYSIS')) AS type,
        c.id_primary_company,
        c.title,
        c.excerpt,
        c.published_at,
        c.topics,
        c.universes,
        c.companies,
        c.solutions,
        c.concepts,
        c.source_id

    FROM `{TABLE_CONTENT_ENRICHED}` c

    WHERE
        LOWER(c.title) LIKE LOWER(CONCAT('%', @query, '%'))
        OR LOWER(c.excerpt) LIKE LOWER(CONCAT('%', @query, '%'))

    ORDER BY published_at DESC
    LIMIT @limit
    OFFSET @offset
    """

    params = {
        "query": q,
        "limit": limit,
        "offset": offset,
        "user_id": user_id,
    }

    rows = query_bq(sql, params)

    items = [_map_feed_row(r) for r in rows]

    # ============================================================
    # 🔥 PERSONALIZATION
    # ============================================================

    if user_id and items:

        from core.user.user_preferences_service import get_user_preferences_grouped

        prefs = get_user_preferences_grouped(user_id) or {}

        fav_companies = set(prefs.get("COMPANY", []))
        fav_topics = set(prefs.get("TOPIC", []))
        fav_solutions = set(prefs.get("SOLUTION", []))

        def match(item):

            for c in (item.get("companies") or []):
                if c.get("id_company") in fav_companies:
                    return True

            for t in (item.get("topics") or []):
                if isinstance(t, dict) and t.get("id_topic") in fav_topics:
                    return True

            for s in (item.get("solutions") or []):
                if s.get("id_solution") in fav_solutions:
                    return True

            return False

        # 🔥 FILTER MODE
        if feed_mode == "mine":

            items = [
                i for i in items
                if match(i)
            ]

        # 🔥 PRIORITIZATION MODE
        else:

            items.sort(
                key=lambda x: (
                    0 if match(x) else 1,
                    x.get("published_at") or ""
                )
            )

    return items
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

    universe_filter = ""

    if universe_id:
        universe_filter = """
        AND EXISTS (
            SELECT 1
            FROM UNNEST(c.universes) u
            WHERE u.id_universe = @universe_id
        )
        """

    sql = f"""
    SELECT
        c.id_content AS id,
        LOWER(COALESCE(c.content_type, 'ANALYSIS')) AS type,
        c.id_primary_company,
        c.title,
        c.excerpt,
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
    }

    rows = query_bq(sql, params)

    items = [_map_feed_row(r) for r in rows]

    # ============================================================
    # 🔥 PERSONALIZATION
    # ============================================================

    if user_id and items:

        from core.user.user_preferences_service import get_user_preferences_grouped

        prefs = get_user_preferences_grouped(user_id) or {}

        fav_companies = set(prefs.get("COMPANY", []))
        fav_topics = set(prefs.get("TOPIC", []))
        fav_solutions = set(prefs.get("SOLUTION", []))

        def match(item):

            for c in (item.get("companies") or []):
                if c.get("id_company") in fav_companies:
                    return True

            for t in (item.get("topics") or []):
                if isinstance(t, dict) and t.get("id_topic") in fav_topics:
                    return True

            for s in (item.get("solutions") or []):
                if s.get("id_solution") in fav_solutions:
                    return True

            return False

        # 🔥 STRICT MODE (My Feed)
        if feed_mode == "mine":

            items = [
                i for i in items
                if match(i)
            ]

        # 🔥 PRIORITIZATION (All Feed)
        else:

            items.sort(
                key=lambda x: (
                    0 if match(x) else 1,
                    x.get("published_at") or ""
                )
            )

    return items
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
            COALESCE(c.content_type, 'ANALYSIS')
        ) AS type,

        c.id_primary_company,

        c.title,
        c.excerpt,
        c.published_at,
        source_url,
        source_title,

        c.topics,
        c.companies,
        c.solutions,
        c.concepts,

        SAFE_CAST(c.source_id AS STRING) AS id_source

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

    from core.content.public_service import get_content
    from core.translation.service import translate_text
    from core.user.user_service import get_user_context

    content = get_content(item_id)

    if not content:
        return None

    # ============================================================
    # USER CONTEXT
    # ============================================================

    context = get_user_context(user_id) if user_id else None
    lang = context["lang"] if context else "fr"

    # ============================================================
    # TRANSLATION (DRAWER)
    # ============================================================

    if lang != "fr":

        try:
            content = {
                **content,

                # --------------------------------------------------
                # CORE FIELDS
                # --------------------------------------------------

                "TITLE": translate_text(
                    content.get("TITLE", ""),
                    lang
                ),

                "EXCERPT": translate_text(
                    content.get("EXCERPT", ""),
                    lang
                ),

                "CONTENT_BODY": translate_text(
                    content.get("CONTENT_BODY", ""),
                    lang
                ),

                # --------------------------------------------------
                # ANALYTICS FIELDS
                # --------------------------------------------------

                "MECANIQUE_EXPLIQUEE": translate_text(
                    content.get("MECANIQUE_EXPLIQUEE", ""),
                    lang
                ),

                "ENJEU_STRATEGIQUE": translate_text(
                    content.get("ENJEU_STRATEGIQUE", ""),
                    lang
                ),

                "POINT_DE_FRICTION": translate_text(
                    content.get("POINT_DE_FRICTION", ""),
                    lang
                ),

                "SIGNAL_ANALYTIQUE": translate_text(
                    content.get("SIGNAL_ANALYTIQUE", ""),
                    lang
                ),
            }

        except Exception:
            # fallback silencieux → on garde le FR
            pass

    # ============================================================
    # RETURN
    # ============================================================

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

        total_count = g.get("total", 0) or 0
        last_7 = g.get("last_7_days", 0) or 0
        last_30 = g.get("last_30_days", 0) or 0

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
            "total_count": r.get("total", 0) or 0,
            "last_7_days": r.get("last_7_days", 0) or 0,
            "last_30_days": r.get("last_30_days", 0) or 0,
        }
        for r in topics_rows
        if r.get("id_topic") and r.get("label")
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
            "total_count": r.get("total", 0) or 0,
            "last_7_days": r.get("last_7_days", 0) or 0,
            "last_30_days": r.get("last_30_days", 0) or 0,
        }
        for r in company_rows
        if r.get("id_company") and r.get("name")
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
            "total_count": r.get("total", 0) or 0,
            "last_7_days": r.get("last_7_days", 0) or 0,
            "last_30_days": r.get("last_30_days", 0) or 0,
        }
        for r in solution_rows
        if r.get("id_solution") and r.get("name")
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

    # ============================================================
    # TOPICS
    # ============================================================

    normalized_topics = []

    for t in topics:

        if isinstance(t, dict):

            tid = t.get("id_topic") or t.get("id")

            label = t.get("label") or t.get("name")

            normalized_topics.append({
                "id_topic": tid,
                "label": label,
            })

            badges.append({
                "type": "topic",
                "label": label,
                "id": tid,
            })

        else:

            badges.append({
                "type": "topic",
                "label": t,
            })

    # ============================================================
    # CONCEPTS
    # ============================================================

    normalized_concepts = []

    for c in concepts:

        if isinstance(c, dict):

            normalized_concepts.append({
                "id_concept": c.get("id_concept") or c.get("id"),
                "label": c.get("label"),
            })

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

    # ============================================================
    # COMPANIES
    # ============================================================

    normalized_companies = []

    for c in companies:

        if isinstance(c, dict):

            cid = c.get("id_company") or c.get("id")

            name = c.get("name")

            normalized_companies.append({
                "id_company": cid,
                "name": name,
            })

            badges.append({
                "type": "company",
                "label": name,
                "id": cid,
            })

    # ============================================================
    # SOLUTIONS
    # ============================================================

    normalized_solutions = []

    for s in solutions:

        if isinstance(s, dict):

            sid = s.get("id_solution") or s.get("id")

            name = s.get("name")

            normalized_solutions.append({
                "id_solution": sid,
                "name": name,
            })

            badges.append({
                "type": "solution",
                "label": name,
                "id": sid,
            })

    # ============================================================
    # UNIVERSES
    # ============================================================

    normalized_universes = []

    for u in universes:

        if isinstance(u, dict):

            uid = u.get("id_universe") or u.get("id")

            label = u.get("label")

            normalized_universes.append({
                "id_universe": uid,
                "label": label,
            })

            badges.append({
                "type": "universe",
                "label": label,
                "id": uid,
            })

    # ============================================================
    # RETURN
    # ============================================================

    return {
        "id": r.get("id"),

        "type": r.get("type"),

        "id_primary_company": r.get("id_primary_company"),

        "title": r.get("title"),

        "excerpt": r.get("excerpt"),

        "source_url": r.get("source_url"),

        "source_title": r.get("source_title"),

        "content_body": r.get("content_body"),

        "published_at": r.get("published_at"),

        # 🔥 NORMALIZED
        "topics": normalized_topics,

        "companies": normalized_companies,

        "solutions": normalized_solutions,

        "concepts": normalized_concepts,

        "universes": normalized_universes,

        "badges": badges,
    }
