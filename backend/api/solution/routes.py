from fastapi import APIRouter, HTTPException, Query, Request
from typing import Optional

from api.solution.models import (
    SolutionCreate,
    SolutionUpdate,
    SolutionOut,
)

from core.solution.service import (
    create_solution,
    list_solutions,
    list_solutions_for_user,
    get_solution,
    update_solution,
    delete_solution,
    get_solution_aliases,
    create_solution_alias,
    delete_solution_alias,
)

from core.curator.entity_service import (
    get_solution_view,
)

from utils.auth import (
    get_user_id_from_request,
)
router = APIRouter()


# ============================================================
# AUTH HELPER (SAFE)
# ============================================================

def require_user(request: Request) -> str:

    user_id = get_user_id_from_request(
        request
    )

    if not user_id:

        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )

    return user_id


# ============================================================
# CREATE
# ============================================================

@router.post("/create")
def create_route(data: SolutionCreate):

    try:

        solution_id = create_solution(
            data
        )

        return {
            "status": "ok",
            "id_solution": solution_id,
        }

    except Exception as e:

        raise HTTPException(
            400,
            f"Erreur création solution : {e}"
        )




# ============================================================
# LIST (ADMIN / GLOBAL)
# ============================================================

@router.get("/list")
def list_route():

    try:

        solutions = list_solutions()

        return {
            "status": "ok",
            "solutions": solutions,
        }

    except Exception as e:

        raise HTTPException(
            400,
            f"Erreur liste solutions : {e}"
        )


# ============================================================
# LIST CURATOR
# ============================================================

@router.get("/list-curator")
def list_solutions_curator(
    request: Request
):

    try:

        user_id = require_user(
            request
        )

        solutions = list_solutions_for_user(
            user_id
        )

        return {
            "status": "ok",
            "solutions": solutions,
        }

    except HTTPException:
        raise

    except Exception as e:

        print(
            f"❌ Solutions curator error: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail="Internal error"
        )


# ============================================================
# ALIASES
# ============================================================

@router.get("/{id_solution}/aliases")
def get_aliases_route(
    id_solution: str
):

    try:

        aliases = get_solution_aliases(
            id_solution=id_solution
        )

        return {
            "status": "ok",
            "aliases": aliases,
        }

    except Exception as e:

        raise HTTPException(
            400,
            f"Erreur récupération aliases : {e}"
        )


@router.post("/{id_solution}/alias")
def create_alias_route(
    id_solution: str,
    data: dict,
):
    try:

        alias = (
            data.get("alias")
            or ""
        ).strip()

        if not alias:

            raise HTTPException(
                400,
                "alias required"
            )

        create_solution_alias(
            id_solution=id_solution,
            alias=alias,
        )

        return {
            "status": "ok",
            "alias": alias,
        }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            400,
            f"Erreur création alias : {e}"
        )


@router.delete("/{id_solution}/alias")
def delete_alias_route(
    id_solution: str,
    alias: str,
):

    try:

        delete_solution_alias(
            id_solution=id_solution,
            alias=alias,
        )

        return {
            "status": "ok",
            "deleted": True,
        }

    except Exception as e:

        raise HTTPException(
            400,
            f"Erreur suppression alias : {e}"
        )


# ============================================================
# GET ONE
# ============================================================

@router.get(
    "/{id_solution}",
    response_model=SolutionOut,
)
def get_route(
    id_solution: str,
):

    solution = get_solution(
        id_solution
    )

    if not solution:

        raise HTTPException(
            404,
            "Solution introuvable",
        )

    return solution

# ============================================================
# VIEW (CURATOR)
# ============================================================

@router.get("/{id_solution}/view")
def get_solution_view_route(
    id_solution: str,
    limit: int = 20,
    offset: int = 0,
    universe_id: Optional[str] = Query(
        None
    ),
):

    try:

        solution = get_solution_view(
            solution_id=id_solution,
            limit=limit,
            offset=offset,
            universe_id=(
                universe_id
                if universe_id
                else None
            ),
        )

        if not solution:

            raise HTTPException(
                404,
                "Solution introuvable"
            )

        return solution

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            400,
            f"Erreur récupération solution view : {e}"
        )


# ============================================================
# UPDATE
# ============================================================

@router.put("/update/{id_solution}")
def update_route(
    id_solution: str,
    data: SolutionUpdate
):

    try:

        updated = update_solution(
            id_solution,
            data
        )

        if not updated:

            raise HTTPException(
                404,
                "Solution introuvable ou aucune modification"
            )

        return {
            "status": "ok",
            "updated": True,
        }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            400,
            f"Erreur mise à jour solution : {e}"
        )


# ============================================================
# DELETE
# ============================================================

@router.delete("/{id_solution}")
def delete_route(
    id_solution: str
):

    try:

        deleted = delete_solution(
            id_solution
        )

        if not deleted:

            raise HTTPException(
                404,
                "Solution introuvable"
            )

        return {
            "status": "ok",
            "deleted": True,
        }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            400,
            f"Erreur suppression solution : {e}"
        )
