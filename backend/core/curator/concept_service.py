from typing import List, Dict

from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import query_bq


TABLE_CONCEPT = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONCEPT"
TABLE_CONTENT_CONCEPT = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_CONCEPT"
VIEW_CONTENT = f"{BQ_PROJECT}.{BQ_DATASET}.V_CONTENT_ENRICHED"
TABLE_USER_UNIVERSE = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER_UNIVERSE"


# ============================================================
# GET CONCEPTS (USER FILTERED)
# ============================================================

def get_concepts(user_id: str) -> List[Dict]:

    rows = query_bq(f"""
        SELECT
            c.ID_CONCEPT,
            c.LABEL,
            c.CATEGORY

        FROM `{TABLE_CONCEPT}` c

        WHERE c.IS_ACTIVE = TRUE

        -- 🔐 uniquement concepts présents dans les contenus accessibles
        AND EXISTS (
            SELECT 1
            FROM `{TABLE_CONTENT_CONCEPT}` cc
            JOIN `{VIEW_CONTENT}` vc
              ON vc.id_content = cc.ID_CONTENT

            JOIN `{TABLE_USER_UNIVERSE}` uu
              ON uu.ID_UNIVERSE IN (
                  SELECT u.id_universe FROM UNNEST(vc.universes) u
              )

            WHERE cc.ID_CONCEPT = c.ID_CONCEPT
              AND uu.ID_USER = @user_id
        )

        ORDER BY c.CATEGORY, c.LABEL
    """, {
        "user_id": user_id
    })

    return [
        {
            "id": r["ID_CONCEPT"],
            "label": r["LABEL"],
            "category": r["CATEGORY"],
        }
        for r in rows
    ]
