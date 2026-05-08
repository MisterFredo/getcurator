from typing import List, Dict, Optional

from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import query_bq


TABLE_BACKLOG = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_NUMBERS_BACKLOG"


# ============================================================
# BACKLOG LIST
# ============================================================

def get_numbers_backlog(
    limit: int = 100,
    decision: Optional[str] = None,
    query: Optional[str] = None,
) -> List[Dict]:

    conditions = ["TRUE"]
    params = {
        "limit": limit,
    }

    # ============================================================
    # FILTER DECISION
    # ============================================================

    if decision == "NULL":
        conditions.append("DECISION IS NULL")

    elif decision:
        conditions.append("DECISION = @decision")
        params["decision"] = decision

    # ============================================================
    # SEARCH
    # ============================================================

    if query:
        conditions.append("""
        (
            LOWER(IFNULL(LABEL, '')) LIKE LOWER(@query)
            OR LOWER(IFNULL(ACTOR, '')) LIKE LOWER(@query)
            OR LOWER(IFNULL(MARKET, '')) LIKE LOWER(@query)
            OR LOWER(IFNULL(RAW_LINE, '')) LIKE LOWER(@query)
        )
        """)
        params["query"] = f"%{query}%"

    where_sql = " AND ".join(conditions)

    # ============================================================
    # QUERY
    # ============================================================

    rows = query_bq(f"""
        SELECT
            ID_BACKLOG,
            ID_CONTENT,

            RAW_LINE,

            LABEL,
            VALUE,
            UNIT,

            ACTOR,
            MARKET,
            PERIOD,

            CONFIDENCE,
            DECISION,

            CREATED_AT

        FROM `{TABLE_BACKLOG}`

        WHERE {where_sql}

        ORDER BY CREATED_AT DESC

        LIMIT @limit
    """, params)

    return rows


# ============================================================
# PROMPT
# ============================================================

def build_prompt(row: dict) -> str:

    return f"""
Tu es un expert data marketing senior.

Ta mission est de décider si un chiffre peut être intégré dans un dashboard professionnel.

--------------------------------------------------

OBJECTIF

Ne garder QUE des KPI solides, comparables et réellement exploitables business.

--------------------------------------------------

1. DECISION

- KEEP → uniquement si le chiffre peut être utilisé directement dans un dashboard
- IGNORE → sinon

--------------------------------------------------

2. CRITÈRES KEEP (OBLIGATOIRES)

Le chiffre doit :

✔ être un KPI business clair
(revenus, part de marché, croissance, CPM, CPC, CPA, volume utilisateurs…)

✔ être comparable
(entre acteurs, périodes ou marchés)

✔ être compréhensible seul
(sans contexte externe)

✔ contenir au moins un élément de contexte exploitable
(acteur OU marché OU période)

✔ les projections marché et tailles de marché sont autorisées
si elles sont clairement quantifiées et datées

--------------------------------------------------

3. IGNORE SI (STRICT)

❌ métrique marketing "soft"
❌ KPI vague ou non standardisable
❌ événement ponctuel
❌ plusieurs chiffres ambigus
❌ ranges
❌ absence de contexte exploitable
❌ KPI non comparable
❌ chiffre trop ancien sans valeur benchmark

--------------------------------------------------

4. STRUCTURE SI KEEP

- decision
- label
- value
- unit
- actor
- market
- period
- confidence

--------------------------------------------------

5. UNITÉS AUTORISÉES

- PERCENT
- EUR
- USD
- MULTIPLIER
- USERS
- OTHER

--------------------------------------------------

6. IMPORTANT

- Si doute → IGNORE
- Priorité à la qualité
- Objectif ≈ 20-30% de KEEP
- Le KPI doit être directement exploitable

--------------------------------------------------

7. FORMAT

Retourne UNIQUEMENT un JSON valide :

{{
  "decision": "...",
  "label": "...",
  "value": ...,
  "unit": "...",
  "actor": "...",
  "market": "...",
  "period": "...",
  "confidence": "..."
}}

--------------------------------------------------

DONNÉES :

Chiffre : {row.get("chiffre")}
Date : {row.get("date")}
Topics : {row.get("topics")}
Companies : {row.get("companies")}
Solutions : {row.get("solutions")}
"""
