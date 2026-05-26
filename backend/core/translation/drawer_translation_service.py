import logging
import json

from typing import (
    Optional,
    Dict,
)

from utils.llm import run_llm

logger = logging.getLogger(__name__)


# ============================================================
# DRAWER TRANSLATION
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
        # PAYLOAD
        # =====================================================

        payload = json.dumps(
            cleaned_fields,
            ensure_ascii=False,
            indent=2
        )

        # =====================================================
        # PROMPT
        # =====================================================

        prompt = f"""
You are a professional translator specialized in:
- business
- media
- marketing
- AdTech
- analytics

MISSION:
Translate all JSON values into {target_lang}.

STRICT RULES:
- Keep EXACT same JSON keys
- Return ONLY valid JSON
- No markdown
- No explanation
- No intro
- No code block
- Do NOT summarize
- Do NOT rewrite
- Preserve exact meaning
- Preserve formatting
- Preserve numbers exactly
- Preserve company / product names exactly

JSON:
{payload}
"""

        # =====================================================
        # LLM
        # =====================================================

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
        # SAFETY
        # =====================================================

        if not isinstance(
            translated_payload,
            dict
        ):
            return cleaned_fields

        # =====================================================
        # RETURN
        # =====================================================

        return {
            **cleaned_fields,
            **translated_payload
        }

    except Exception:

        logger.exception(
            "Drawer translation error"
        )

        return fields
