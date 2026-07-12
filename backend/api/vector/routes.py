from fastapi import APIRouter, HTTPException

from api.vector.models import (
    VectorBatchRequest,
    VectorContentBatchResponse,
    VectorContentBatchItem,
)

# ==================================================
# SERVICES
# ==================================================

# CONTENT
from core.vectorization.content_vector_service import (
    vectorize_content,
    get_content_vector_status,
    get_content_to_vectorize,
)

router = APIRouter()

# --------------------------------------------------
# VECTORIZE MULTIPLE CONTENT (⚠️ AVANT /{content_id})
# --------------------------------------------------

@router.post("/content/batch", response_model=VectorContentBatchResponse)
def vectorize_content_batch(payload: VectorBatchRequest):

    results = []
    success = 0
    error = 0

    try:
        # =========================
        # SOURCE DES IDS
        # =========================
        if payload.ids:
            content_ids = payload.ids
        else:
            content_ids = get_content_to_vectorize(
                limit=payload.limit,
                offset=payload.offset,
                status=payload.status,
            )

        if not content_ids:
            return VectorContentBatchResponse(
                status="done",
                processed=0,
                success=0,
                error=0,
                results=[]
            )

        # =========================
        # PROCESS
        # =========================
        for content_id in content_ids:
            try:
                res = vectorize_content(content_id)

                results.append(
                    VectorContentBatchItem(
                        content_id=content_id,
                        status=res.get("status", "ok"),
                        nb_vectors=res.get("nb_vectors"),
                    )
                )
                success += 1

            except Exception as e:
                results.append(
                    VectorContentBatchItem(
                        content_id=content_id,
                        status="error",
                        error=str(e),
                    )
                )
                error += 1

        return VectorContentBatchResponse(
            status="done",
            processed=len(content_ids),
            success=success,
            error=error,
            results=results
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --------------------------------------------------
# VECTORIZE ONE CONTENT
# --------------------------------------------------

@router.post("/content/{content_id}")
def vectorize_content_route(content_id: str):
    try:
        if content_id == "batch":
            raise ValueError("Invalid content_id")

        result = vectorize_content(content_id)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --------------------------------------------------
# STATUS CONTENT
# --------------------------------------------------

@router.get("/content/status")
def content_status(limit: int = 50, offset: int = 0):
    try:
        return get_content_vector_status(limit=limit, offset=offset)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
