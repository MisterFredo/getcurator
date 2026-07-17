# backend/api/expertise/routes.py

from fastapi import (
    APIRouter,
)

from api.expertise.models import (
    Expertise,
)

from core.expertise.service import (
    generate_expertise,
)

router = APIRouter()


# ============================================================
# GENERATE EXPERTISE
# ============================================================

@router.post("/generate")
def generate_expertise_route(
    payload: dict,
) -> dict:

    result: Expertise = generate_expertise(

        user_id=payload.get(
            "user_id"
        ),

        period_start=payload.get(
            "period_start"
        ),

        period_end=payload.get(
            "period_end"
        ),

        limit=payload.get(
            "limit"
        ),
    )

    return {

        "status": "ok",

        "result": result,

    }
