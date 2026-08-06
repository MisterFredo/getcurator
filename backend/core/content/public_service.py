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
    SELECT *

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
# READ CONTENT (DRAWER CURATOR)
# ============================================================

def get_contents(
    content_ids: List[str],
) -> List[Dict]:

    if not content_ids:
        return []

    client = get_bigquery_client()

    query = f"""
    SELECT *
    FROM `{TABLE_CONTENT_ENRICHED}`
    WHERE id_content IN UNNEST(@content_ids)
    """

    rows = client.query(

        query,

        job_config=bigquery.QueryJobConfig(

            query_parameters=[

                bigquery.ArrayQueryParameter(
                    "content_ids",
                    "STRING",
                    content_ids,
                )

            ]

        ),

    ).result()

    return [

        _map_content(
            dict(row)
        )

        for row in rows

    ]

