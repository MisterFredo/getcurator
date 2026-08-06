# ============================================================
# IA — GENERATE CONTENT
# ============================================================

@router.post("/ai/generate")
def ai_generate(
    payload: ContentSummaryRequest
):

    if not payload.source_text.strip():

        raise HTTPException(
            400,
            "Source manquante"
        )

    try:

        result = generate_summary(
            source_id=payload.source_id,
            source_text=payload.source_text,
        )

        if not isinstance(
            result,
            dict
        ):

            raise ValueError(
                "Réponse IA invalide"
            )

        return {
            "status": "ok",
            **result
        }

    except Exception as e:

        logger.exception(
            "Erreur génération contenu IA"
        )

        raise HTTPException(
            400,
            str(e)
        )
