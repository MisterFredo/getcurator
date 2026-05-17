import re
import unicodedata
from typing import Dict, Any, Optional, List

from config import BQ_PROJECT, BQ_DATASET
from utils.llm import run_llm
from utils.bigquery_utils import query_bq


# ============================================================
# UTILS — NORMALISATION HEADER
# ============================================================

def normalize_key(text: str) -> str:
    text = unicodedata.normalize("NFD", text)
    text = text.encode("ascii", "ignore").decode("utf-8")
    text = text.replace("#", "")
    text = text.replace(":", "")
    return text.strip().upper()


# ============================================================
# GENERATE SUMMARY + ANALYSE FROM SOURCE
# ============================================================

def generate_summary(
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

    if not topics_rows:
        raise ValueError(f"Aucun topic disponible pour la source {source_id}")

    allowed_topics = {
        row["LABEL"]: row["ID_TOPIC"]
        for row in topics_rows
    }

    topics_list_text = "\n".join(
        f"- {label}" for label in allowed_topics.keys()
    )

    # ============================================================
    # LOAD CONCEPTS (GLOBAL)
    # ============================================================

    concepts_rows = query_bq(f"""
        SELECT ID_CONCEPT, LABEL
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
Tu es un assistant éditorial B2B spécialisé marketing, AdTech et Retail Media.

RÈGLES ABSOLUES :
- Strictement basé sur la source fournie.
- Aucun fait inventé.
- Aucun chiffre inventé.
- Aucun acteur inventé.
- Toute analyse doit être déduite des éléments présents dans la source.
- Ne pas extrapoler au-delà de ce qui est implicitement ou explicitement contenu dans le texte.
- Ne jamais formuler de recommandation.
- Ne jamais dire ce qu’il faut faire.
- Style professionnel, clair, structuré et synthétique.
- Rédige toujours en français.

OBJECTIF :
Produire une analyse structurée permettant de comprendre :
- ce qui se passe
- comment cela fonctionne
- quelles dynamiques sont à l’œuvre

================ SOURCE ================
Source : {source_id}

{source_text}

================ RÈGLES DE CLASSIFICATION IMPORTANTES ================

Tu dois impérativement distinguer deux types d’entités :

1) ACTEURS = ENTREPRISES UNIQUEMENT
- sociétés, groupes, organisations
- exemples : Google, Amazon, LiveRamp, TF1 Pub, Meta

2) SOLUTIONS = PRODUITS / PLATEFORMES / OFFRES
- produits commerciaux, marques, technologies, solutions marketing
- exemples : DV360, RampID, Amazon DSP, TF1+, Johnnie Walker

IMPORTANT :
- Une entité ne doit apparaître QUE dans une seule catégorie
- Si c’est un produit → SOLUTIONS (et PAS ACTEURS)
- Si c’est une entreprise → ACTEURS (et PAS SOLUTIONS)
- Ne jamais dupliquer une même entité dans les deux sections
- Si tu hésites :
  → entreprise → ACTEURS
  → produit → SOLUTIONS

================ FORMAT OBLIGATOIRE ================

TITLE
(Titre factuel et informatif.)

EXCERPT
(3 phrases synthétiques permettant de comprendre rapidement le sujet et son intérêt.)

POINTS CLES
(Liste factuelle des éléments importants présents dans la source.
Exhaustif mais strictement basé sur le texte.
Une ligne = une information.)

CHIFFRES
Extraire uniquement les chiffres présents dans la source.

FORMAT STRICT OBLIGATOIRE :
Chaque ligne doit respecter EXACTEMENT ce format (6 champs) :

label | valeur | unité | acteur | géographie | période

RÈGLES STRICTES :

1. valeur
- nombre uniquement (pas de texte)
- utiliser "." pour les décimales
- ne jamais inclure d’unité dans la valeur
- exemples valides : 13 | 3.5 | 1000

2. unité
- choisir parmi :
  % | € | $ | utilisateurs | millions | milliards | ans | jours | heures
- ne jamais mélanger unité et échelle

3. acteur
- entreprise uniquement (ex : Amazon, Netflix)
- sinon écrire : Aucun

4. géographie
- uniquement une zone géographique
- exemples autorisés :
  France | UK | US | Europe | Global
- si non précisé → écrire : Global

INTERDIT :
- catégories métier (CTV, Retail Media, Audio, etc.)
- noms d’entreprises
- concepts ou topics

5. période
- année ou période claire
- exemples :
  2024 | 2023 | Q1 2024 | Non précisé

6. format obligatoire
- EXACTEMENT 6 champs
- séparés par "|"
- aucun texte en dehors des lignes

INTERDIT :
- phrases
- commentaires
- champs manquants
- champs supplémentaires

EXEMPLES CORRECTS :

Part de marché CTV | 35 | % | Netflix | France| 2024  
Revenus publicitaires | 1200 | millions | Amazon | Etats-Unis | 2023  
Utilisateurs actifs | 50 | millions | Aucun | Moldavie | Non précisé

ACTEURS
(Liste des entreprises citées ou "Aucun")

SOLUTIONS
(Liste des produits, plateformes, marques ou offres citées ou "Aucun")

CONCEPTS
(Choisir 1 à 3 concepts uniquement parmi la liste suivante.
Ne jamais inventer.)

{concepts_list_text}

TOPICS
(Choisir 1 à 3 topics uniquement parmi la liste suivante.
Ne jamais inventer.)

RÈGLES TOPICS IMPORTANTES

- "Ready-to-Drink (RTD)" :
inclut RTD, Ready-to-Drink, canned cocktails,
premix, premixed drinks, hard seltzers.

- "Ready-to-Serve (RTS)" :
inclut RTS, Ready-to-Serve,
batched cocktails, bottled cocktails,
pre-batched cocktails.

{topics_list_text}

================ ANALYSE STRATEGIQUE ================

MECANIQUE
- Expliquer COMMENT cela fonctionne réellement

ENJEU
- Identifier ce que cela révèle

FRICTION
- Identifier les limites ou écrire "Aucun"

SIGNAL
- Identifier la dynamique de marché
"""

    raw = run_llm(prompt)

    if not raw:
        raise ValueError("Réponse LLM vide")

    # ============================================================
    # PARSING
    # ============================================================

    sections = {
        "TITLE": "",
        "EXCERPT": "",
        "POINTS CLES": "",
        "CHIFFRES": "",
        "ACTEURS": "",
        "CONCEPTS": "",
        "SOLUTIONS": "",
        "TOPICS": "",
        "MECANIQUE": "",
        "ENJEU": "",
        "FRICTION": "",
        "SIGNAL": "",
    }

    current = None

    for line in raw.splitlines():

        clean = line.strip()
        if not clean:
            continue

        normalized = normalize_key(clean)

        matched = False
        for key in sections.keys():
            if normalized.startswith(key):
                current = key
                matched = True
                break

        if matched:
            continue

        if current:
            sections[current] += clean + "\n"

    # ============================================================
    # HELPERS
    # ============================================================

    def parse_list(block: str) -> List[str]:

        if not block:
            return []

        if block.strip().lower().startswith("aucun"):
            return []

        items = []

        for line in block.splitlines():
            line = line.strip()
            line = re.sub(r"^[-•]\s*", "", line)
            line = re.sub(r"^\d+\.\s*", "", line)

            if line and line.lower() != "aucun":
                items.append(line)

        return items

    def parse_concepts(block: str) -> List[str]:

        if not block:
            return []

        if block.strip().lower().startswith("aucun"):
            return []

        items = []

        for line in block.splitlines():
            line = line.strip()
            line = re.sub(r"^[-•]\s*", "", line)
            line = re.sub(r"^\d+\.\s*", "", line)

            if line and line.lower() != "aucun":
                items.append(line)

        return items

    # ============================================================
    # BODY
    # ============================================================

    body_lines = parse_list(sections["POINTS CLES"])

    body = (
        "<ul>" + "".join(f"<li>{l}</li>" for l in body_lines) + "</ul>"
        if body_lines else ""
    )

    # ============================================================
    # TOPICS
    # ============================================================

    raw_topics = parse_list(sections["TOPICS"])

    valid_topics = [
        t for t in raw_topics
        if any(k.lower() == t.lower() for k in allowed_topics.keys())
    ]

    topic_ids = [
        allowed_topics[
            next(k for k in allowed_topics if k.lower() == t.lower())
        ]
        for t in valid_topics
    ]

    raw_concepts = parse_concepts(sections["CONCEPTS"])

    concept_ids = [
        allowed_concepts[
            next(k for k in allowed_concepts if k.lower() == c.lower())
        ]
        for c in raw_concepts
        if any(k.lower() == c.lower() for k in allowed_concepts.keys())
    ]

    # ============================================================
    # RETURN
    # ============================================================

    return {
        "title": sections["TITLE"].strip(),
        "excerpt": sections["EXCERPT"].strip(),
        "content_body": body,
        "chiffres": parse_list(sections["CHIFFRES"]),
        "acteurs_cites": parse_list(sections["ACTEURS"]),
        "concepts": concept_ids,
        "solutions": parse_list(sections["SOLUTIONS"]),
        "topics": topic_ids,
        "mecanique_expliquee": sections["MECANIQUE"].strip(),
        "enjeu_strategique": sections["ENJEU"].strip(),
        "point_de_friction": sections["FRICTION"].strip(),
        "signal_analytique": sections["SIGNAL"].strip(),
    }
