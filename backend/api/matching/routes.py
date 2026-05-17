from fastapi import APIRouter, HTTPException

from api.matching.models import (
    EntityMatch,
    BulkEntityMatchRequest,
)

from core.matching.service import (
    list_unmatched_entities,
    match_entity,
)

router = APIRouter()

# ============================================================
# LIST UNMATCHED ENTITIES
# ============================================================

@router.get("/")
def list_entities():

    try:

        rows = list_unmatched_entities()

        return {
            "status": "ok",
            "entities": rows,
        }

    except Exception as e:

        raise HTTPException(
            400,
            str(e),
        )

# ============================================================
# APPLY ENTITY MATCH
# ============================================================

@router.post("/match")
def apply_entity_match(
    data: EntityMatch
):

    try:

        match_entity(
            alias=data.alias,
            target_type=data.target_type,
            target_id=data.target_id,
        )

        return {
            "status": "ok",
        }

    except Exception as e:

        raise HTTPException(
            400,
            str(e),
        )

# ============================================================
# BULK ENTITY MATCH
# ============================================================

@router.post("/bulk-match")
def bulk_entity_match(
    payload: BulkEntityMatchRequest
):

    results = []

    for item in payload.items:

        try:

            match_entity(
                alias=item.alias,
                target_type=item.target_type,
                target_id=item.target_id,
            )

            results.append({
                "alias": item.alias,
                "status": "ok",
            })

        except Exception as e:

            results.append({
                "alias": item.alias,
                "status": "error",
                "error": str(e),
            })

    return {
        "status": "ok",
        "total": len(payload.items),
        "matched": len([
            r for r in results
            if r["status"] == "ok"
        ]),
        "errors": len([
            r for r in results
            if r["status"] == "error"
        ]),
        "results": results,
    }
