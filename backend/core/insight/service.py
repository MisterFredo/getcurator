from typing import List, Dict

from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import query_bq
from utils.llm import run_llm


# ============================================================
# TABLE
# ============================================================

TABLE_CONTENT = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT"


# ============================================================
# FETCH ANALYSES (LLM ONLY)
# ============================================================

def get_analysis_details_by_ids(ids: List[str]) -> List[Dict]:
    """
    Récupère les analyses enrichies pour le LLM uniquement.
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
        FROM `{TABLE_CONTENT}`
        WHERE ID_CONTENT IN UNNEST(@ids)
        """,
        {"ids": ids}
    )

    return [
        {
            "id": r["ID_CONTENT"],
            "title": r.get("TITLE"),
            "excerpt": r.get("EXCERPT"),
            "content_body": r.get("CONTENT_BODY"),
            "mecanique": r.get("MECANIQUE_EXPLIQUEE"),
            "enjeu": r.get("ENJEU_STRATEGIQUE"),
            "friction": r.get("POINT_DE_FRICTION"),
            "signal": r.get("SIGNAL_ANALYTIQUE"),
            "chiffres": r.get("CHIFFRES") or [],
        }
        for r in rows
    ]


# ============================================================
# PROMPT
# ============================================================

def build_prompt(payload: Dict) -> str:

    analyses = payload.get("analyses", [])

    if not analyses:
        return "Aucune donnée."

    context_blocks = []

    for a in analyses:
        block = f"""
TITRE:
{a.get("title")}

CONTENU:
{a.get("content_body")}

CONCEPTS:
{a.get("concepts_llm")}

CHIFFRES:
{a.get("chiffres")}

SIGNAL:
{a.get("signal")}

MECANIQUE:
{a.get("mecanique")}
"""
        context_blocks.append(block.strip())

    context = "\n\n====================\n\n".join(context_blocks)

    prompt = f"""
Tu es un assistant de SYNTHÈSE FACTUELLE pour un expert métier.

Tu travailles sur des signaux déjà structurés.
Tu ne dois PAS interpréter, tu dois STRUCTURER.

--------------------------------------------------
OBJECTIF

Faire gagner du temps à un professionnel :
→ Il ne veut PAS lire les analyses
→ Il veut les faits importants, organisés

--------------------------------------------------
MÉTHODE (OBLIGATOIRE)

1. IDENTIFIER les CONCEPTS récurrents
2. REGROUPER les analyses par concept
3. EXTRAIRE :
   - faits concrets (signal / mécanique)
   - chiffres associés
4. PRIORISER :
   - fréquence
   - impact business

--------------------------------------------------
CONTEXTE
{context}

--------------------------------------------------
TÂCHE

Produire 2 sections :

TOP 5
→ les signaux les plus importants

À NOTER
→ signaux secondaires mais pertinents

--------------------------------------------------
FORMAT STRICT

POINTS CLÉS

TOP 5

- [CONCEPT] → fait + chiffre

À NOTER

- [CONCEPT] → fait

--------------------------------------------------
RÈGLES STRICTES

- MAX 5 points dans TOP 5
- MAX 5 points dans À NOTER
- PAS de remplissage
- PAS de résumé d’article
- PAS de storytelling
- PAS de généralité
- PAS d’invention

INTERDIT :
❌ Ajouter "Analyse", "Résumé", emojis
❌ Reproduire le contenu brut
❌ Faire 1 point = 1 analyse

AUTORISÉ :
✅ faits
✅ chiffres
✅ regroupement

--------------------------------------------------

Tu es un filtre, pas un rédacteur.
"""

    return prompt.strip()


# ============================================================
# LLM
# ============================================================

def generate_insight(payload: Dict) -> str:
    """
    Génération insight LLM (ultra clean)
    """

    if payload.get("count", 0) == 0:
        return "Aucune analyse disponible."

    prompt = build_prompt(payload)

    result = run_llm(
        prompt=prompt,
        temperature=0.2,
    )

    if not result:
        return "Impossible de générer l'insight."

    return result


# ============================================================
# PIPELINE FINAL
# ============================================================

def run_insight_pipeline(ids: List[str]) -> Dict:
    """
    Pipeline final simplifié (LLM only)
    """

    if not ids:
        return {
            "status": "empty",
            "insight": "",
        }

    analyses = get_analysis_details_by_ids(ids)

    payload = {
        "type": "insight",
        "count": len(analyses),
        "analyses": analyses,
    }

    insight = generate_insight(payload)

    return {
        "status": "ok",
        "insight": insight,
    }
