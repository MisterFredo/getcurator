from typing import List, Dict

from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import query_bq

def get_numbers_backlog(limit: int = 100) -> List[Dict]:

    TABLE_CONTENT = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT"
    TABLE_TOPIC = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_TOPIC"
    TABLE_TOPIC_REF = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_TOPIC"
    TABLE_COMPANY = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_COMPANY"
    TABLE_COMPANY_REF = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY"
    TABLE_SOLUTION = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_SOLUTION"
    TABLE_SOLUTION_REF = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOLUTION"
    TABLE_BACKLOG = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_NUMBERS_BACKLOG"

    rows = query_bq(f"""
        WITH base AS (

            SELECT
                c.ID_CONTENT AS id_content,
                c.SOURCE_DATE AS source_date,
                chiffre,

                IFNULL(STRING_AGG(DISTINCT t.LABEL), "Non précisé") AS topics,
                IFNULL(STRING_AGG(DISTINCT comp.NAME), "Non précisé") AS companies,
                IFNULL(STRING_AGG(DISTINCT sol.NAME), "Non précisé") AS solutions

            FROM `{TABLE_CONTENT}` c

            LEFT JOIN UNNEST(c.CHIFFRES) AS chiffre

            LEFT JOIN `{TABLE_TOPIC}` ct
              ON c.ID_CONTENT = ct.ID_CONTENT
            LEFT JOIN `{TABLE_TOPIC_REF}` t
              ON ct.ID_TOPIC = t.ID_TOPIC

            LEFT JOIN `{TABLE_COMPANY}` cc
              ON c.ID_CONTENT = cc.ID_CONTENT
            LEFT JOIN `{TABLE_COMPANY_REF}` comp
              ON cc.ID_COMPANY = comp.ID_COMPANY

            LEFT JOIN `{TABLE_SOLUTION}` cs
              ON c.ID_CONTENT = cs.ID_CONTENT
            LEFT JOIN `{TABLE_SOLUTION_REF}` sol
              ON cs.ID_SOLUTION = sol.ID_SOLUTION

            WHERE chiffre IS NOT NULL

            GROUP BY
                id_content,
                source_date,
                chiffre
        )

        SELECT *
        FROM base b

        WHERE NOT EXISTS (
            SELECT 1
            FROM `{TABLE_BACKLOG}` bl
            WHERE bl.RAW_LINE = b.chiffre
              AND bl.ID_CONTENT = b.id_content
        )

        LIMIT @limit
    """, {
        "limit": limit
    })

    results = []

    for r in rows:

        results.append({
            "id_content": r["id_content"],
            "chiffre": r["chiffre"],
            "date": str(r["source_date"]) if r.get("source_date") else None,
            "topics": r["topics"],
            "companies": r["companies"],
            "solutions": r["solutions"],
        })

    return results


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
- REJECT → sinon

--------------------------------------------------

2. CRITÈRES KEEP (OBLIGATOIRES)

Le chiffre doit :

✔ être un KPI business clair (revenus, part de marché, croissance, CPM, CPC, CPA, volume utilisateurs…)
✔ être comparable (entre acteurs, périodes ou marchés)
✔ être compréhensible seul (sans contexte externe)
✔ contenir au moins un élément de contexte exploitable (acteur OU marché OU période)

✔ les estimations de marché global sont autorisées (taille de marché, projections, croissance secteur)

--------------------------------------------------

3. REJECT SI (STRICT)

❌ métrique marketing "soft" :
   - affinité
   - considération
   - engagement relatif
   - "plus susceptibles"
   - "plus de chances"

❌ formulation vague ou non standardisable :
   - "augmentation"
   - "baisse"
   - "réduction"
   sans précision KPI claire

❌ événement ponctuel :
   - acquisition
   - levée de fonds
   - annonce isolée

❌ plusieurs valeurs dans une même ligne non séparables clairement
❌ KPI reformulé ou interprété (ex: "croissance", "priorité", "augmentation") sans métrique directement exploitable

❌ range :
   - "10-15%"
   - "2 à 3 fois"

❌ absence de contexte exploitable

❌ chiffre trop ancien ou non pertinent aujourd’hui (ex: data > 5-10 ans sans valeur benchmark claire)

❌ KPI non standardisable ou non comparable dans un dashboard

--------------------------------------------------

4. STRUCTURE SI KEEP

- decision
- label → KPI métier clair, court, standardisé (ex: "part de marché retail media", "revenus annuels", "CPM moyen")
- le label doit correspondre à un KPI standardisé directement utilisable dans un dashboard
(ex: revenus, part de marché, volume, coût, performance)
- value → nombre uniquement (pas de %, $, texte, espace)
- unit → EXACTEMENT parmi :
  %, $, €, millions, milliards, x, utilisateurs, autres
- actor → sinon "Non précisé"
- market → sinon "Non précisé"
- period → sinon "Non précisé"
- confidence → HIGH si très fiable, sinon MEDIUM

--------------------------------------------------

5. IMPORTANT

- Si doute → REJECT
- Priorité à la qualité, pas au volume
- Objectif : environ 20-30% de KEEP maximum
- Le KPI doit être directement exploitable dans un dashboard sans transformation

--------------------------------------------------

6. FORMAT

Retourne UNIQUEMENT un JSON valide, sans texte avant ou après :

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

Chiffre : {row["chiffre"]}
Date : {row["date"]}
Topics : {row["topics"]}
Companies : {row["companies"]}
Solutions : {row["solutions"]}
"""
