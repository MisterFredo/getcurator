from fastapi import (
    APIRouter,
    HTTPException,
    Query,
)

from typing import (
    Optional,
    List,
)

from api.translation.models import (
    TranslationRequest,
    TranslationBatchRequest,
)

from core.translation.content_translation_service import (
    translate_content_fields,
    translate_contents_batch,
)

router = APIRouter()


# ============================================================
# TRANSLATE ONE CONTENT
# ============================================================

@router.post("/content")
def translate_content_route(
    data: TranslationRequest
):

    try:

        result = translate_content_fields(
            content_id=data.content_id,
            target_lang=data.target_lang,
            fields=data.fields,
        )

        return {
            "status": "ok",
            "result": result,
        }

    except Exception as e:

        raise HTTPException(
            400,
            f"Erreur traduction contenu : {e}"
        )


# ============================================================
# TRANSLATE BATCH
# ============================================================

@router.post("/batch")
def translate_batch_route(
    data: TranslationBatchRequest
):

    try:

        result = translate_contents_batch(
            target_lang=data.target_lang,

            fields=data.fields,

            limit=data.limit,

            only_missing=data.only_missing,

            content_ids=data.content_ids,

            source_id=data.source_id,
        )

        return {
            "status": "ok",
            "translated": result,
        }

    except Exception as e:

        raise HTTPException(
            400,
            f"Erreur batch traduction : {e}"
        )


# ============================================================
# TRANSLATE ONE QUICK
# ============================================================

@router.post("/quick")
def quick_translate_route(
    data: dict
):

    try:

        from core.translation.service import (
            translate_text
        )

        text = (
            data.get("text")
            or ""
        ).strip()

        target_lang = (
            data.get("target_lang")
            or "en"
        ).strip()

        if not text:

            raise HTTPException(
                400,
                "text required"
            )

        translated = translate_text(
            text=text,
            target_lang=target_lang,
        )

        return {
            "status": "ok",
            "translated_text": translated,
        }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            400,
            f"Erreur traduction rapide : {e}"
        )


# ============================================================
# HEALTH
# ============================================================

@router.get("/health")
def health_route():

    return {
        "status": "ok",
        "service": "translation",
    }
