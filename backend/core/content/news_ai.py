import json
import logging
import re
from typing import Dict, Any, Optional, List

from config import BQ_PROJECT, BQ_DATASET
from utils.llm import run_llm
from utils.bigquery_utils import query_bq


logger = logging.getLogger(__name__)


# ============================================================
# HELPERS
# ============================================================

def parse_list(values: Optional[List[str]]) -> List[str]:

    if not values:
        return []

    cleaned = []

    for v in values:

        if not v:
            continue

        value = str(v).strip()

        if not value:
            continue

        if value.lower() == "aucun":
            continue

        cleaned.append(value)

    return list(dict.fromkeys(cleaned))


# ============================================================
# GENERATE NEWS
# ============================================================

def generate_news(
    source_id: Optional[str],
    source_text: str,
) -> Dict[str, Any]:

    if not isinstance(source_text, str) or not source_text.strip():
        raise ValueError("Source vide")

    if not source_id:
        raise ValueError("source_id obligatoire")

    # ============================================================
    # LOAD TOPICS BY SOURCE UNIVERSE
    # ============================================================

    topics_rows = query_bq(f"""
        SELECT
            t.ID_TOPIC,
            t.LABEL
        FROM `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOURCE_UNIVERSE` su

        JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_TOPIC_UNIVERSE` tu
          ON su.ID_UNIVERSE = tu.ID_UNIVERSE

        JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_TOPIC` t
          ON t.ID_TOPIC = tu.ID_TOPIC

        WHERE su.ID_SOURCE = @source_id
          AND COALESCE(t.IS_ACTIVE, TRUE) = TRUE
    """, {"source_id": source_id})

    allowed_topics = {
        row["LABEL"]: row["ID_TOPIC"]
        for row in topics_rows
    }

    topics_list_text = "\n".join(
        f"- {label}" for label in allowed_topics.keys()
    )

    # ============================================================
    # LOAD CONCEPTS
    # ============================================================

    concepts_rows = query_bq(f"""
        SELECT
            ID_CONCEPT,
            LABEL
        FROM `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONCEPT`
        WHERE COALESCE(IS_ACTIVE, TRUE) = TRUE
    """)

    allowed_concepts = {
        row["LABEL"]: row["ID_CONCEPT"]
        for row in concepts_rows
    }

    concepts_list_text = "\n".join(
        f"- {label}" for label in allowed_concepts.keys()
    )

    # ============================================================
    # PROMPT
    # ============================================================

    prompt = f"""
Tu es l’assistant éditorial de Curator, plateforme spécialisée marketing, AdTech, Retail Media et transformation digitale.

MISSION :
Transformer une source brute (post, communiqué, interview, article, note interne, transcription, etc.)
en une news éditoriale factuelle, claire et immédiatement exploitable en français professionnel.

RÈGLES ABSOLUES :
- Strictement basé sur la source fournie.
- Aucun ajout d'information non présente dans la source.
- Aucun chiffre inventé.
- Aucun acteur inventé.
- Aucun ton promotionnel ou commercial.
- Pas d’exagération.
- Pas d’opinion.
- Pas de recommandation.
- Ne pas extrapoler au-delà du texte.
- Style sobre, précis et synthétique.
- Français professionnel irréprochable.

OBJECTIF ÉDITORIAL :
- Mettre en évidence le fait principal.
- Clarifier ce qui se passe concrètement.
- Expliciter les éléments de contexte ou enjeux implicites présents dans la source.
- Permettre une compréhension rapide sans relire l’article.
- Produire une lecture utile, pas un résumé narratif.

================ SOURCE ================

Source : {source_id}

{source_text}

================ CLASSIFICATION ENTITÉS ================

Tu dois distinguer :

1) ACTEURS = ENTREPRISES UNIQUEMENT
Exemples :
- Google
- Amazon
- Meta
- TF1 Pub
- LiveRamp

2) SOLUTIONS = PRODUITS / PLATEFORMES / OFFRES
Exemples :
- DV360
- RampID
- Amazon DSP
- TF1+
- Johnnie Walker

IMPORTANT :
- Une entité ne doit apparaître QUE dans une seule catégorie.
- Produit → SOLUTIONS.
- Entreprise → ACTEURS.
- Aucun doublon entre ACTEURS et SOLUTIONS.

================ CONCEPTS AUTORISÉS ================

Choisir entre 1 et 3 concepts uniquement parmi cette liste.

{concepts_list_text}

================ TOPICS AUTORISÉS ================

Choisir entre 1 et 3 topics uniquement parmi cette liste.

{topics_list_text}

================ FORMAT DE SORTIE ================

Retourne uniquement un JSON strict valide.
Aucun texte avant ou après.

FORMAT STRICT :

{{
  "title": "...",
  "excerpt": "...",
  "body_html": "...",
  "acteurs": [],
  "solutions": [],
  "concepts": [],
  "topics": [],
  "chiffres": []
}}

================ CONTRAINTES ================

TITLE
- 70 à 120 caractères
- Informatif et factuel
- Sans point d’exclamation
- Sans superlatif
- Refléter le signal principal

EXCERPT
- 3 à 4 phrases
- 300 à 500 caractères
- Ne pas répéter le titre
- Chaque phrase doit apporter une information nouvelle
- Aucun adjectif promotionnel
- Aucun remplissage vide

BODY_HTML
- Liste de 4 à 6 points clés
- Format STRICT :

<ul>
  <li>...</li>
</ul>

- Chaque point :
  - une seule idée
  - directement informatif
  - utile à la compréhension rapide
  - strictement basé sur la source

CHIFFRES
- Extraire uniquement les chiffres présents dans la source.
- Format :

label | valeur | unité | acteur | géographie | période

Exemple :
Revenus publicitaires | 1200 | millions | Amazon | US | 2024
"""

    raw = run_llm(prompt)

    if not raw:
        raise ValueError("Réponse LLM vide")

    # ============================================================
    # JSON EXTRACTION
    # ============================================================

    try:

        match = re.search(r"\{[\s\S]*\}", raw)

        if not match:
            raise ValueError("JSON introuvable")

        data = json.loads(match.group(0))

    except Exception:

        logger.exception("Erreur parsing NEWS AI")
        raise ValueError("Erreur parsing NEWS AI")

    # ============================================================
    # VALID TOPICS
    # ============================================================

    raw_topics = parse_list(
        data.get("topics", [])
    )

    valid_topics = [
        t for t in raw_topics
        if any(
            k.lower() == t.lower()
            for k in allowed_topics.keys()
        )
    ]

    topic_ids = [
        allowed_topics[
            next(
                k for k in allowed_topics
                if k.lower() == t.lower()
            )
        ]
        for t in valid_topics
    ]

    # ============================================================
    # VALID CONCEPTS
    # ============================================================

    raw_concepts = parse_list(
        data.get("concepts", [])
    )

    concept_ids = [
        allowed_concepts[
            next(
                k for k in allowed_concepts
                if k.lower() == c.lower()
            )
        ]
        for c in raw_concepts
        if any(
            k.lower() == c.lower()
            for k in allowed_concepts.keys()
        )
    ]

    # ============================================================
    # RETURN CURATOR FORMAT
    # ============================================================

    return {
        "title": (data.get("title") or "").strip(),

        "excerpt": (data.get("excerpt") or "").strip(),

        "content_body": (
            data.get("body_html") or ""
        ).strip(),

        "chiffres": parse_list(
            data.get("chiffres", [])
        ),

        "acteurs_cites": parse_list(
            data.get("acteurs", [])
        ),

        "concepts": concept_ids,

        "solutions": parse_list(
            data.get("solutions", [])
        ),

        "topics": topic_ids,

        # ========================================================
        # ANALYSIS FIELDS EMPTY FOR NEWS
        # ========================================================

        "mecanique_expliquee": None,
        "enjeu_strategique": None,
        "point_de_friction": None,
        "signal_analytique": None,
    }
