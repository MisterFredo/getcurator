from typing import List, Dict

from config import (
    BQ_PROJECT,
    BQ_DATASET,
)

from utils.bigquery_utils import (
    query_bq,
)

from utils.llm import (
    run_llm,
)

# ============================================================
# TABLE
# ============================================================

TABLE_CONTENT = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT"
)

# ============================================================
# FETCH CONTENTS
# ============================================================

def get_analysis_details_by_ids(
    ids: List[str]
) -> List[Dict]:
    """
    Récupère les analyses utiles
    pour génération éditoriale digest.
    """

    if not ids:
        return []

    rows = query_bq(
        f"""
        SELECT

          ID_CONTENT,

          TITLE,

          EXCERPT,

          CONTENT_BODY,

          MECANIQUE_EXPLIQUEE,

          ENJEU_STRATEGIQUE,

          POINT_DE_FRICTION,

          SIGNAL_ANALYTIQUE,

          CHIFFRES,

          CONCEPTS_LLM,

          TOPICS_LLM

        FROM `{TABLE_CONTENT}`

        WHERE ID_CONTENT IN UNNEST(@ids)

        """,
        {
            "ids": ids
        }
    )

    return [

        {
            "id":
                r["ID_CONTENT"],

            "title":
                r.get("TITLE"),

            "excerpt":
                r.get("EXCERPT"),

            "content_body":
                r.get("CONTENT_BODY"),

            "mecanique":
                r.get(
                    "MECANIQUE_EXPLIQUEE"
                ),

            "enjeu":
                r.get(
                    "ENJEU_STRATEGIQUE"
                ),

            "friction":
                r.get(
                    "POINT_DE_FRICTION"
                ),

            "signal":
                r.get(
                    "SIGNAL_ANALYTIQUE"
                ),

            "concepts":
                r.get(
                    "CONCEPTS_LLM"
                ),

            "topics":
                r.get(
                    "TOPICS_LLM"
                ),

            "chiffres":
                r.get(
                    "CHIFFRES"
                ) or [],
        }

        for r in rows
    ]

# ============================================================
# BUILD PROMPT
# ============================================================

def build_prompt(
    payload: Dict
) -> str:

    analyses = payload.get(
        "analyses",
        []
    )

    if not analyses:
        return "Aucune donnée."

    # ========================================================
    # CONTEXT
    # ========================================================

    context_blocks = []

    for a in analyses:

        block = f"""
TITRE:
{a.get("title")}

EXCERPT:
{a.get("excerpt")}

SIGNAL:
{a.get("signal")}

MECANIQUE:
{a.get("mecanique")}

ENJEU:
{a.get("enjeu")}

FRICTION:
{a.get("friction")}

CONCEPTS:
{a.get("concepts")}

TOPICS:
{a.get("topics")}

CHIFFRES:
{a.get("chiffres")}
"""

        context_blocks.append(
            block.strip()
        )

    context = "\n\n====================\n\n".join(
        context_blocks
    )

    # ========================================================
    # PROMPT
    # ========================================================

    prompt = f"""
Tu es un assistant éditorial pour une newsletter premium destinée à des professionnels.

Tu travailles à partir de signaux déjà structurés.

Tu ne dois PAS :
- résumer les articles
- raconter les contenus
- faire du storytelling
- inventer
- produire du remplissage

--------------------------------------------------
OBJECTIF

Produire une section :
"Points à retenir"

Cette section doit permettre à un dirigeant ou expert :
- de comprendre les principaux mouvements
- d’identifier les signaux importants
- de voir les tendances récurrentes
- en moins de 30 secondes

--------------------------------------------------
MÉTHODE

1. Identifier les signaux récurrents
2. Regrouper les analyses similaires
3. Prioriser :
   - impact business
   - fréquence
   - nouveauté
4. Extraire :
   - faits concrets
   - chiffres utiles
   - mouvements marché
   - changements produit / stratégie

--------------------------------------------------
CONTEXTE

{context}

--------------------------------------------------
FORMAT STRICT

POINTS À RETENIR

- [Concept / sujet] → fait concret + impact
- [Concept / sujet] → fait concret + chiffre
- [Concept / sujet] → évolution marché
- [Concept / sujet] → mouvement stratégique

--------------------------------------------------
RÈGLES

- MAXIMUM 8 points
- Chaque point = 1 seule idée
- Phrase courte
- Ton professionnel
- Pas d’introduction
- Pas de conclusion
- Pas de titres supplémentaires
- Pas de catégories
- Pas de markdown complexe
- Pas d’émojis
- Pas de storytelling
- Pas de langage marketing

INTERDIT :
❌ "Cette semaine..."
❌ "Les analyses montrent..."
❌ "On observe que..."
❌ résumé article par article

AUTORISÉ :
✅ regroupement
✅ synthèse
✅ chiffres
✅ signaux
✅ mouvements marché

--------------------------------------------------

Tu es un filtre stratégique.
Pas un rédacteur marketing.
"""

    return prompt.strip()

# ============================================================
# GENERATE INSIGHT
# ============================================================

def generate_insight(
    payload: Dict
) -> str:
    """
    Génération éditoriale digest.
    """

    if payload.get(
        "count",
        0
    ) == 0:

        return (
            "Aucune analyse disponible."
        )

    prompt = build_prompt(
        payload
    )

    result = run_llm(
        prompt=prompt,

        temperature=0.15,
    )

    if not result:

        return (
            "Impossible de générer les points clés."
        )

    return result.strip()

# ============================================================
# PIPELINE
# ============================================================

def run_insight_pipeline(
    ids: List[str]
) -> Dict:
    """
    Pipeline digest editorial.
    """

    if not ids:

        return {
            "status": "empty",
            "insight": "",
        }

    analyses = (
        get_analysis_details_by_ids(
            ids
        )
    )

    payload = {

        "type":
            "digest_editorial",

        "count":
            len(analyses),

        "analyses":
            analyses,
    }

    insight = generate_insight(
        payload
    )

    return {

        "status":
            "ok",

        "insight":
            insight,
    }
