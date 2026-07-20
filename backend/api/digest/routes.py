from fastapi import APIRouter

from core.digest.models import (
    DigestBatchCreateRequest,
)

from core.digest.batch_service import (
    create_batch,
    prepare_batch,
    generate_batch,
    send_batch,
    get_batch,
    list_batches,
)

from core.digest.repository import (
    fetch_batch,
)

from core.digest.send_service import (
    send_digest_review,
)

router = APIRouter()


# ============================================================
# BATCHES
# ============================================================

@router.post("/batches")
def create_batch_route(
    request: DigestBatchCreateRequest,
):

    return create_batch(
        frequency=request.frequency,
        audience=request.audience,
    )


@router.get("/batches")
def list_batches_route():

    return list_batches()


@router.get("/batches/{batch_id}")
def get_batch_route(
    batch_id: str,
):

    return get_batch(
        batch_id=batch_id,
    )


# ============================================================
# PREPARE
# ============================================================

@router.post("/batches/{batch_id}/prepare")
def prepare_batch_route(
    batch_id: str,
):

    batch = fetch_batch(
        batch_id=batch_id,
    )

    if batch is None:

        raise ValueError(
            f"Unknown batch: {batch_id}"
        )

    return prepare_batch(
        batch=batch,
    )


# ============================================================
# GENERATE
# ============================================================

@router.post("/batches/{batch_id}/generate")
def generate_batch_route(
    batch_id: str,
):

    batch = fetch_batch(
        batch_id=batch_id,
    )

    if batch is None:

        raise ValueError(
            f"Unknown batch: {batch_id}"
        )

    return generate_batch(
        batch=batch,
    )


# ============================================================
# SEND
# ============================================================

@router.post("/batches/{batch_id}/send")
def send_batch_route(
    batch_id: str,
):

    batch = fetch_batch(
        batch_id=batch_id,
    )

    if batch is None:

        raise ValueError(
            f"Unknown batch: {batch_id}"
        )

    return send_batch(
        batch=batch,
    )


# ============================================================
# REVIEWS
# ============================================================

@router.get("/reviews/{review_id}")
def get_review_route(
    review_id: str,
):

    return get_digest_review(
        review_id=review_id,
    )

# ============================================================
# REVIEW
# ============================================================

@router.post("/reviews/{review_id}/regenerate")
def regenerate_review_route(
    review_id: str,
):

    return regenerate_digest_review(
        review_id=review_id,
    )


@router.post("/reviews/{review_id}/send")
def send_review_route(
    review_id: str,
):

    return send_digest_review(
        review_id=review_id,
    )
