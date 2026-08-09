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
        "companies": companies,
        "topics": r.get("topics") or [],
        "solutions": r.get("solutions") or [],

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

def _map_content_detail(
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
# LIST CONTENTS
# ============================================================

def list_contents(
    limit: int = 20,
    offset: int = 0,
    company_id: Optional[str] = None,
    topic_id: Optional[str] = None,
    solution_id: Optional[str] = None,
    concept_id: Optional[str] = None,
    universe_id: Optional[str] = None,
) -> List[Dict]:

    where = [
        "status = 'PUBLISHED'",
        "is_active = TRUE",
    ]

    params = {
        "limit": limit,
        "offset": offset,
    }

    # ========================================================
    # COMPANY
    # ========================================================

    if company_id:

        where.append(
            """
            EXISTS (
                SELECT 1
                FROM UNNEST(companies) company
                WHERE company.id_company = @company_id
            )
            """
        )

        params["company_id"] = company_id

    # ========================================================
    # TOPIC
    # ========================================================

    if topic_id:

        where.append(
            """
            EXISTS (
                SELECT 1
                FROM UNNEST(topics) topic
                WHERE topic.id_topic = @topic_id
            )
            """
        )

        params["topic_id"] = topic_id

    # ========================================================
    # SOLUTION
    # ========================================================

    if solution_id:

        where.append(
            """
            EXISTS (
                SELECT 1
                FROM UNNEST(solutions) solution
                WHERE solution.id_solution = @solution_id
            )
            """
        )

        params["solution_id"] = solution_id

    # ========================================================
    # CONCEPT
    # ========================================================

    if concept_id:

        where.append(
            """
            EXISTS (
                SELECT 1
                FROM UNNEST(concepts) concept
                WHERE concept.id_concept = @concept_id
            )
            """
        )

        params["concept_id"] = concept_id

    # ========================================================
    # UNIVERSE
    # ========================================================

    if universe_id:

        where.append(
            """
            EXISTS (
                SELECT 1
                FROM UNNEST(universes) universe
                WHERE universe.id_universe = @universe_id
            )
            """
        )

        params["universe_id"] = universe_id

    # ========================================================
    # QUERY
    # ========================================================

    sql = f"""
    SELECT

        id_content,
    
        title,
        title_en,
    
        excerpt,
        excerpt_en,
    
        signal_analytique,
    
        published_at,
    
        source_title,
        source_url,
    
        id_primary_company,
    
        companies,
        topics,
        solutions

    FROM `{TABLE_CONTENT_ENRICHED}`

    WHERE

        {" AND ".join(where)}

    ORDER BY published_at DESC

    LIMIT @limit

    OFFSET @offset
    """

    rows = query_bq(
        sql,
        params,
    )

    return [

        _map_content_summary(
            row,
        )

        for row in rows

    ]

# ============================================================
# READ CONTENT
# ============================================================

def get_content(
    id_content: str,
) -> Optional[Dict]:

    contents = get_contents(
        [id_content]
    )

    return (
        contents[0]
        if contents
        else None
    )

# ============================================================
# READ CONTENTS
# ============================================================

def get_contents(
    ids: List[str],
) -> List[Dict]:

    if not ids:
        return []

    rows = query_bq(
        f"""
        SELECT *
        FROM `{TABLE_CONTENT_ENRICHED}`
        WHERE id_content IN UNNEST(@ids)
        """,
        {
            "ids": ids,
        },
    )

    contents = [
        _map_content(row)
        for row in rows
    ]

    # ========================================================
    # KEEP INPUT ORDER
    # ========================================================

    by_id = {
        c["id"]: c
        for c in contents
    }

    return [
        by_id[id_content]
        for id_content in ids
        if id_content in by_id
    ]


# ============================================================
# LATEST CONTENTS
# ============================================================

def get_latest_contents(
    limit: int = 20,
    company_id: Optional[str] = None,
    topic_id: Optional[str] = None,
    solution_id: Optional[str] = None,
    concept_id: Optional[str] = None,
    universe_id: Optional[str] = None,
) -> List[Dict]:

    return list_contents(
        limit=limit,
        offset=0,
        company_id=company_id,
        topic_id=topic_id,
        solution_id=solution_id,
        concept_id=concept_id,
        universe_id=universe_id,
    )

# ============================================================
# CONTENTS BY COMPANY
# ============================================================

def get_contents_by_company(
    company_id: str,
    limit: int = 20,
) -> List[Dict]:

    return list_contents(
        company_id=company_id,
        limit=limit,
    )


# ============================================================
# CONTENTS BY TOPIC
# ============================================================

def get_contents_by_topic(
    topic_id: str,
    limit: int = 20,
) -> List[Dict]:

    return list_contents(
        topic_id=topic_id,
        limit=limit,
    )


# ============================================================
# CONTENTS BY SOLUTION
# ============================================================

def get_contents_by_solution(
    solution_id: str,
    limit: int = 20,
) -> List[Dict]:

    return list_contents(
        solution_id=solution_id,
        limit=limit,
    )


# ============================================================
# CONTENTS BY CONCEPT
# ============================================================

def get_contents_by_concept(
    concept_id: str,
    limit: int = 20,
) -> List[Dict]:

    return list_contents(
        concept_id=concept_id,
        limit=limit,
    )


# ============================================================
# CONTENTS BY UNIVERSE
# ============================================================

def get_contents_by_universe(
    universe_id: str,
    limit: int = 20,
) -> List[Dict]:

    return list_contents(
        universe_id=universe_id,
        limit=limit,
    )

# ============================================================
# RELATED CONTENTS
# ============================================================

def get_related_contents(
    id_content: str,
    limit: int = 10,
) -> List[Dict]:

    content = get_content(
        id_content,
    )

    if not content:
        return []

    # ========================================================
    # PRIORITY
    # ========================================================

    if content["companies"]:

        return [
            c
            for c in get_contents_by_company(
                company_id=content["companies"][0]["id_company"],
                limit=limit + 1,
            )
            if c["id"] != id_content
        ][:limit]

    if content["topics"]:

        return [
            c
            for c in get_contents_by_topic(
                topic_id=content["topics"][0]["id_topic"],
                limit=limit + 1,
            )
            if c["id"] != id_content
        ][:limit]

    if content["solutions"]:

        return [
            c
            for c in get_contents_by_solution(
                solution_id=content["solutions"][0]["id_solution"],
                limit=limit + 1,
            )
            if c["id"] != id_content
        ][:limit]

    return []
