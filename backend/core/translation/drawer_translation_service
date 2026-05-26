import logging
import hashlib
import json

from typing import (
    Optional,
    Dict,
)

from utils.llm import run_llm

from utils.bigquery_utils import (
    query_bq,
    update_bq,
)

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

    update_bq(
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
# MULTI FIELDS TRANSLATION
# ============================================================

def translate_fields(
    fields: Dict[str, Optional[str]],
    target_lang: str
) -> Dict[str, Optional[str]]:

    if not fields:
        return fields

    if target_lang == "fr":
        return fields

    try:

        # =====================================================
        # CLEAN INPUT
        # =====================================================

        cleaned_fields = {}

        for key, value in fields.items():

            if value is None:
                cleaned_fields[key] = value
                continue

            if not isinstance(value, str):
                cleaned_fields[key] = value
                continue

            cleaned_fields[key] = value.strip()

        # =====================================================
        # CACHE CHECK
        # =====================================================

        results = {}
        missing = {}

        for key, value in cleaned_fields.items():

            if not value:
                results[key] = value
                continue

            cached = _get_cached_translation(
                value,
                target_lang
            )

            if cached:

                results[key] = cached

            else:

                missing[key] = value

        # =====================================================
        # EVERYTHING CACHED
        # =====================================================

        if not missing:
            return results

        # =====================================================
        # SINGLE LLM CALL
        # =====================================================

        payload = json.dumps(
            missing,
            ensure_ascii=False,
            indent=2
        )

        prompt = f"""
You are a professional translator specialized in:
- business
- media
- marketing
- AdTech
- analytics

MISSION:
Translate the JSON fields below into {target_lang}.

STRICT RULES:
- Keep EXACT same JSON structure
- Keep EXACT same keys
- Do NOT summarize
- Do NOT rewrite
- Do NOT add information
- Do NOT remove information
- Preserve exact meaning
- Preserve formatting
- Preserve numbers exactly
- Preserve company / product names exactly

IMPORTANT:
Return ONLY valid JSON.

JSON:
{payload}
"""

        raw = run_llm(prompt)

        if not raw:
            return cleaned_fields

        # =====================================================
        # CLEAN RESPONSE
        # =====================================================

        cleaned_raw = (
            raw
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )

        # =====================================================
        # PARSE JSON
        # =====================================================

        translated_payload = json.loads(
            cleaned_raw
        )

        # =====================================================
        # STORE CACHE
        # =====================================================

        for key, translated in translated_payload.items():

            source = missing.get(key)

            if not source:
                continue

            if not translated:
                results[key] = source
                continue

            if not isinstance(translated, str):
                results[key] = source
                continue

            translated = translated.strip()

            # =================================================
            # SAFETY
            # =================================================

            if (
                target_lang == "en"
                and translated == source
            ):

                logger.warning(
                    f"Translation identical to source for field: {key}"
                )

                results[key] = source

                continue

            # =================================================
            # STORE CACHE
            # =================================================

            _store_translation(
                source,
                target_lang,
                translated
            )

            results[key] = translated

        # =====================================================
        # FALLBACK SAFETY
        # =====================================================

        for key, value in cleaned_fields.items():

            if key not in results:
                results[key] = value

        return results

    except Exception:

        logger.exception(
            "Drawer translation error"
        )

        return fields
