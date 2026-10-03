import re
import unicodedata

from typing import (
    Dict,
    Any,
    Optional,
)

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

from core.content.prompts import (
    build_summary_prompt,
)


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
# LOAD TOPICS TEXT
# ============================================================

def _load_topics_text(
    source_id: str,
) -> str:

    rows = query_bq(
        f"""
        SELECT DISTINCT
            t.LABEL

        FROM `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOURCE_UNIVERSE` su

        JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_TOPIC_UNIVERSE` tu
          ON su.ID_UNIVERSE = tu.ID_UNIVERSE

        JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_TOPIC` t
          ON tu.ID_TOPIC = t.ID_TOPIC

        WHERE
            su.ID_SOURCE = @source_id
            AND COALESCE(t.IS_ACTIVE, TRUE) = TRUE

        ORDER BY t.LABEL
        """,
        {
            "source_id": source_id,
        },
    )

    if not rows:
        raise ValueError(
            f"Aucun topic disponible pour la source {source_id}"
        )

    return "\n".join(
        f"- {row['LABEL']}"
        for row in rows
    )


# ============================================================
# LOAD CONCEPTS TEXT
# ============================================================

def _load_concepts_text() -> str:

    rows = query_bq(
        f"""
        SELECT
            LABEL

        FROM `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONCEPT`

        WHERE
            COALESCE(IS_ACTIVE, TRUE) = TRUE

        ORDER BY LABEL
        """
    )

    return "\n".join(
        f"- {row['LABEL']}"
        for row in rows
    )

# ============================================================
# PARSE LLM SECTIONS
# ============================================================

def _parse_llm_sections(
    raw: str,
):

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

        normalized = normalize_key(
            clean
        )

        matched = False

        for key in sections:

            if normalized.startswith(key):

                current = key

                matched = True

                break

        if matched:
            continue

        if current:

            sections[current] += (
                clean + "\n"
            )

    return sections

# ============================================================
# PARSE LIST
# ============================================================

def _parse_list(
    block: str,
):

    if not block:
        return []

    normalized_block = (
        block
        .strip()
        .lower()
    )

    if normalized_block.startswith(
        (
            "aucun",
            "none",
        )
    ):

        return []

    items = []

    for line in block.splitlines():

        line = line.strip()

        line = re.sub(
            r"^[-•]\s*",
            "",
            line,
        )

        line = re.sub(
            r"^\d+\.\s*",
            "",
            line,
        )

        if (
            line
            and line.lower()
            not in {
                "aucun",
                "none",
            }
        ):

            items.append(
                line
            )

    return items
# ============================================================
# BUILD BODY
# ============================================================

def _build_body(
    block: str,
):

    lines = _parse_list(
        block
    )

    if not lines:
        return ""

    return (
        "<ul>"
        + "".join(
            f"<li>{line}</li>"
            for line in lines
        )
        + "</ul>"
    )


# ============================================================
# GENERATE SUMMARY
# ============================================================

def generate_summary(
    source_id: Optional[str],
    source_text: str,
) -> Dict[str, Any]:

    # ========================================================
    # CHECKS
    # ========================================================

    if not isinstance(source_text, str) or not source_text.strip():
        raise ValueError("Source vide")

    if not source_id:
        raise ValueError("source_id obligatoire")

    # ========================================================
    # REFERENTIALS
    # ========================================================

    topics_list_text = _load_topics_text(
        source_id,
    )

    concepts_list_text = _load_concepts_text()

    # ========================================================
    # PROMPT
    # ========================================================

    prompt = build_summary_prompt(

        source_id=source_id,

        source_text=source_text,

        topics_list_text=topics_list_text,

        concepts_list_text=concepts_list_text,

    )

    # ========================================================
    # LLM
    # ========================================================

    raw = run_llm(
        prompt,
    )

    if not raw:
        raise ValueError(
            "Réponse LLM vide"
        )

    # ========================================================
    # PARSING
    # ========================================================

    sections = _parse_llm_sections(
        raw,
    )

    # ========================================================
    # RETURN
    # ========================================================

    return {

        "title": sections["TITLE"].strip(),

        "excerpt": sections["EXCERPT"].strip(),

        "content_body": _build_body(
            sections["POINTS CLES"],
        ),

        "chiffres": _parse_list(
            sections["CHIFFRES"],
        ),

        "acteurs_cites": _parse_list(
            sections["ACTEURS"],
        ),

        "solutions_llm": _parse_list(
            sections["SOLUTIONS"],
        ),

        "topics_llm": _parse_list(
            sections["TOPICS"],
        ),

        "concepts_llm": _parse_list(
            sections["CONCEPTS"],
        ),

        "mecanique_expliquee": sections[
            "MECANIQUE"
        ].strip(),

        "enjeu_strategique": sections[
            "ENJEU"
        ].strip(),

        "point_de_friction": sections[
            "FRICTION"
        ].strip(),

        "signal_analytique": sections[
            "SIGNAL"
        ].strip(),

    }


# ============================================================
# GENERATE TOPICS
# BACKFILL ONLY
# ============================================================

def generate_topics(
    source_id: Optional[str],
    source_text: str,
) -> list[str]:

    if (
        not isinstance(source_text, str)
        or not source_text.strip()
    ):
        raise ValueError("Source vide")

    if not source_id:
        raise ValueError(
            "source_id obligatoire"
        )

    # ========================================================
    # ALLOWED TOPICS
    # ========================================================

    topics_list_text = _load_topics_text(
        source_id,
    )

    # ========================================================
    # PROMPT
    # ========================================================

    prompt = f"""
Tu dois classifier le contenu ci-dessous.

Sélectionne uniquement les TOPICS réellement pertinents.

RÈGLES IMPORTANTES :

- Utilise exclusivement les valeurs présentes dans la liste autorisée.
- N'invente aucun topic.
- Ne reformule jamais les labels.
- Ne sélectionne que les topics clairement pertinents.
- Si aucun topic n'est pertinent, réponds "None".
- Ne produis aucun commentaire.

TOPICS AUTORISÉS :

{topics_list_text}

CONTENU :

{source_text}

FORMAT DE RÉPONSE OBLIGATOIRE :

TOPICS
- label exact
- label exact
"""

    # ========================================================
    # LLM
    # ========================================================

    raw = run_llm(
        prompt,
    )
    
    if not raw:
        raise ValueError(
            "Réponse LLM vide"
        )
    
    sections = _parse_llm_sections(
        raw,
    )
    
    print("\n==============================")
    print("[TOPICS LLM RAW]")
    print(raw)
    print("------------------------------")
    print("[TOPICS SECTIONS]")
    print(sections)
    print("------------------------------")
    
    topics = _parse_list(
        sections["TOPICS"],
    )
    
    print("[TOPICS PARSED]", topics)
    print("==============================\n")
    
    return topics
