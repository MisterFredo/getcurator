from typing import List, Dict

from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import query_bq
from utils.llm import run_llm

TABLE_NUMBERS = f"{BQ_PROJECT}.{BQ_DATASET}.V_NUMBERS_ENRICHED"


# ============================================================
# FETCH NUMBERS BY IDS
# ============================================================

def get_numbers_by_ids(ids: List[str]) -> List[Dict]:

    # 🔥 sécurité totale
    if isinstance(ids, str):
        ids = [ids]

    if not ids or not isinstance(ids, list):
        return []

    rows = query_bq(
        f"""
        SELECT
            ID_NUMBER,
            ENTITY_TYPE,
            ENTITY_ID,
            ENTITY_LABEL,

            LABEL,
            VALUE,
            UNIT,
            SCALE,

            TYPE,
            CATEGORY,

            ZONE,
            PERIOD,
            CREATED_AT

        FROM `{TABLE_NUMBERS}`
        WHERE ID_NUMBER IN UNNEST(@ids)
        """,
        {"ids": ids}
    )

    return [
        {
            "id": r.get("ID_NUMBER"),
            "label": r.get("LABEL"),
            "value": r.get("VALUE"),
            "unit": r.get("UNIT"),
            "scale": r.get("SCALE"),

            "type": r.get("TYPE"),
            "category": r.get("CATEGORY"),

            "zone": r.get("ZONE"),
            "period": r.get("PERIOD"),

            "entity_type": r.get("ENTITY_TYPE"),
            "entity_id": r.get("ENTITY_ID"),
            "entity_label": r.get("ENTITY_LABEL"),
        }
        for r in rows
    ]

# ============================================================
# BUILD PROMPT
# ============================================================

def build_numbers_prompt(numbers: List[Dict]) -> str:

    blocks = []

    for n in numbers:
        block = f"""
LABEL: {n.get("label")}
VALUE: {n.get("value")} {n.get("unit")} {n.get("scale")}
TYPE: {n.get("type")}
CATEGORY: {n.get("category")}
ZONE: {n.get("zone")}
PERIOD: {n.get("period")}
ENTITY: {n.get("entity_label")}
"""
        blocks.append(block.strip())

    context = "\n\n-----------------\n\n".join(blocks)

    return f"""
Tu es un assistant DATA pour un expert métier.

Tu travailles sur des chiffres déjà sélectionnés.
Tu ne dois PAS inventer.
Tu dois STRUCTURER.

--------------------------------------------------
OBJECTIF

Transformer une liste de chiffres en :

1. une STRUCTURE logique
2. un ORDRE de présentation
3. une LECTURE business claire

--------------------------------------------------
CONTEXTE
{context}

--------------------------------------------------
TÂCHE

1. REGROUPER les chiffres par logique (ex: marché, performance, adoption…)
2. IDENTIFIER les niveaux :
   - taille
   - croissance
   - performance
3. ORGANISER :
   - du plus structurant au plus opérationnel

--------------------------------------------------
OUTPUT

STRUCTURE

- Bloc 1 → thème + logique
  - chiffre
  - chiffre

- Bloc 2 → thème + logique

--------------------------------------------------

LECTURE

- ce que ces chiffres racontent
- sans interprétation libre
- sans storytelling

--------------------------------------------------

RÈGLES

- pas de résumé
- pas d’invention
- pas de blabla
- uniquement structuration + logique

Tu es un outil d’organisation, pas un analyste.
""".strip()


# ============================================================
# MAIN PIPELINE
# ============================================================

def generate_numbers_insight(ids: List[str]) -> str:

    if not ids:
        return ""

    numbers = get_numbers_by_ids(ids)

    if not numbers:
        return ""

    prompt = build_numbers_prompt(numbers)

    result = run_llm(
        prompt=prompt,
        temperature=0.2,
    )

    return result or ""

def get_latest_numbers(entity_label: str, limit: int = 3):

    rows = query_bq(f"""
        SELECT
            ID_NUMBER,
            LABEL,
            VALUE,
            UNIT,
            SCALE,
            ENTITY_LABEL
        FROM `{TABLE_NUMBERS}`
        WHERE LOWER(ENTITY_LABEL) = LOWER(@label)
        ORDER BY CREATED_AT DESC
        LIMIT @limit
    """, {
        "label": entity_label,
        "limit": limit
    })

    return rows
