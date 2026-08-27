import logging
import json

from typing import (
    Optional,
    Dict,
)

from utils.llm import run_llm


logger = logging.getLogger(__name__)


# ============================================================
# DRAWER / STRUCTURED TRANSLATION
# ============================================================

def translate_fields(
    fields: Dict[str, Optional[str]],
    target_lang: str,
    raise_on_error: bool = False,
) -> Dict[str, Optional[str]]:

    if not fields:
        return fields

    # ========================================================
    # CLEAN INPUT
    # ========================================================

    cleaned_fields = {}

    for key, value in fields.items():

        if value is None:

            cleaned_fields[key] = None

            continue

        if not isinstance(
            value,
            str,
        ):

            cleaned_fields[key] = value

            continue

        cleaned_fields[key] = (
            value.strip()
        )

    # ========================================================
    # TRANSLATABLE VALUES
    # ========================================================

    translatable_fields = {

        key:
            value

        for key, value
        in cleaned_fields.items()

        if (
            isinstance(
                value,
                str,
            )
            and value
        )
    }

    if not translatable_fields:
        return cleaned_fields

    try:

        # =====================================================
        # PAYLOAD
        # =====================================================

        payload = json.dumps(
            translatable_fields,
            ensure_ascii=False,
            indent=2,
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
- Keep EXACTLY the same JSON keys
- Return ONLY valid JSON
- No markdown
- No explanation
- No introduction
- No code block
- Do NOT summarize
- Do NOT rewrite
- Do NOT add information
- Do NOT remove information
- Preserve exact meaning
- Preserve tone
- Preserve formatting
- Preserve numbers exactly
- Preserve company and product names exactly
- Every input key must appear exactly once in the output

JSON:
{payload}
"""

        # =====================================================
        # LLM
        # =====================================================

        raw = run_llm(
            prompt
        )

        if not raw:

            raise RuntimeError(
                "Le LLM n'a retourné aucune traduction."
            )

        # =====================================================
        # CLEAN RESPONSE
        # =====================================================

        cleaned_raw = (
            raw
            .replace(
                "```json",
                "",
            )
            .replace(
                "```JSON",
                "",
            )
            .replace(
                "```",
                "",
            )
            .strip()
        )

        if not cleaned_raw:

            raise RuntimeError(
                "La traduction retournée est vide."
            )

        # =====================================================
        # PARSE JSON
        # =====================================================

        translated_payload = (
            json.loads(
                cleaned_raw
            )
        )

        # =====================================================
        # VALIDATE PAYLOAD
        # =====================================================

        if not isinstance(
            translated_payload,
            dict,
        ):

            raise ValueError(
                "La réponse de traduction n'est pas un objet JSON."
            )

        expected_keys = set(
            translatable_fields.keys()
        )

        returned_keys = set(
            translated_payload.keys()
        )

        if returned_keys != expected_keys:

            missing_keys = (
                expected_keys
                - returned_keys
            )

            unexpected_keys = (
                returned_keys
                - expected_keys
            )

            raise ValueError(
                "Clés de traduction invalides. "
                f"Manquantes : {sorted(missing_keys)}. "
                f"Inattendues : {sorted(unexpected_keys)}."
            )

        # =====================================================
        # VALIDATE VALUES
        # =====================================================

        validated_translation = {}

        for key in expected_keys:

            translated_value = (
                translated_payload.get(
                    key
                )
            )

            if not isinstance(
                translated_value,
                str,
            ):

                raise ValueError(
                    "Valeur traduite invalide "
                    f"pour le champ {key}."
                )

            translated_value = (
                translated_value.strip()
            )

            if not translated_value:

                raise ValueError(
                    "Valeur traduite vide "
                    f"pour le champ {key}."
                )

            validated_translation[key] = (
                translated_value
            )

        # =====================================================
        # RETURN
        # =====================================================

        return {

            **cleaned_fields,

            **validated_translation,
        }

    except Exception:

        logger.exception(
            "Structured translation error"
        )

        if raise_on_error:
            raise

        return cleaned_fields
