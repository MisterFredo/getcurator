from typing import List, Dict, Optional

from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import query_bq

from core.curator.service import build_user_filter

# ============================================================
# TABLES
# ============================================================

TABLE_CONCEPT = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONCEPT"
TABLE_CONTENT_CONCEPT = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_CONCEPT"
VIEW_CONTENT = f"{BQ_PROJECT}.{BQ_DATASET}.V_CONTENT_ENRICHED"

# ============================================================
# LIST CONCEPTS (USER-AWARE)
# ============================================================

def get_curator_concepts(
    user_id: Optional[str] = None,
    universe_id: Optional[str] = None,
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
    SELECT DISTINCT
        con.ID_CONCEPT,
        con.LABEL,
        con.CATEGORY

    FROM `{TABLE_CONCEPT}` con

    WHERE con.IS_ACTIVE = TRUE

    -- 🔥 IMPORTANT : filtrer via CONTENT (pas via JOIN IN)
    AND EXISTS (
        SELECT 1
        FROM `{TABLE_CONTENT_CONCEPT}` cc
        JOIN `{VIEW_CONTENT}` c
          ON c.id_content = cc.ID_CONTENT

        WHERE cc.ID_CONCEPT = con.ID_CONCEPT

        {build_user_filter("c") if user_id else ""}

        {universe_filter}
    )

    ORDER BY con.CATEGORY, con.LABEL
    """

    params = {
        "user_id": user_id,
        "universe_id": universe_id,
    }

    rows = query_bq(sql, params)

    return [
        {
            "id_concept": r.get("ID_CONCEPT"),
            "title": r.get("LABEL"),
            "category": r.get("CATEGORY"),
        }
        for r in rows
    ]
