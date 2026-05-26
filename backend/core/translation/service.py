import logging
import hashlib
from typing import Optional

from utils.llm import run_llm
from utils.bigquery_utils import query_bq

from config import (
    BQ_PROJECT,
    BQ_DATASET,
)

logger = logging.getLogger(__name__)


# ============================================================
# TABLE
# ============================================================

TABLE_TRANSLATION_CACHE = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_TRANSLATION_CACHE"
)


# ============================================================
# HELPERS
# ============================================================

def _hash_text(
    text: str,
    lang: str
) -> str:

    raw = f"{text.strip()}_{lang}"

    return hashlib.md5(
        raw.encode("utf-8")
    ).hexdigest()


def _get_cached_translation(
    text: str,
    lang: str
) -> Optional[str]:

    hash_key = _hash_text(
        text,
        lang
    )

    rows = query_bq(
        f"""
        SELECT
            TRANSLATED_TEXT

        FROM `{TABLE_TRANSLATION_CACHE}`

        WHERE HASH_KEY = @hash

        LIMIT 1
        """,
        {
            "hash": hash_key
        }
    )

    if rows:
        return rows[0]["TRANSLATED_TEXT"]

    return None


def _store_translation(
    text: str,
    lang: str,
    translated: str
):

    hash_key = _hash_text(
        text,
        lang
    )

    query_bq(
        f"""
        INSERT INTO `{TABLE_TRANSLATION_CACHE}` (
            HASH_KEY,
            SOURCE_TEXT,
            TARGET_LANG,
            TRANSLATED_TEXT,
            CREATED_AT
        )

        SELECT *
        FROM (

            SELECT
                @hash AS HASH_KEY,
                @text AS SOURCE_TEXT,
                @lang AS TARGET_LANG,
                @translated AS TRANSLATED_TEXT,
                CURRENT_TIMESTAMP() AS CREATED_AT

        )

        WHERE NOT EXISTS (

            SELECT 1

            FROM `{TABLE_TRANSLATION_CACHE}`

            WHERE HASH_KEY = @hash

        )
        """,
        {
            "hash": hash_key,
            "text": text,
            "lang": lang,
            "translated": translated,
        }
    )


# ============================================================
# CORE TRANSLATION
# ============================================================

def translate_text(
    text: str,
    target_lang: str
) -> str:

    if not text:
        return text

    if target_lang == "fr":
        return text

    try:

        # =====================================================
        # CACHE
        # =====================================================

        cached = _get_cached_translation(
            text,
            target_lang
        )

        if cached:
            return cached

        # =====================================================
        # LLM
        # =====================================================

        prompt = f"""
You are a professional translator specialized in:
- business
- media
- marketing
- AdTech
- analytics

MISSION:
Translate the following text into {target_lang}.

STRICT RULES:
- Do NOT summarize
- Do NOT rewrite
- Do NOT add information
- Do NOT remove information
- Preserve exact meaning
- Preserve tone
- Preserve formatting
- Preserve numbers exactly
- Preserve company / product names exactly

TEXT:
{text}

OUTPUT:
Return ONLY the translated text.
"""

        raw = run_llm(prompt)

        if not raw:
            return text

        translated = raw.strip()

        # =====================================================
        # STORE CACHE
        # =====================================================

        _store_translation(
            text,
            target_lang,
            translated
        )

        return translated

    except Exception:

        logger.exception(
            "Translation error"
        )

        return text
