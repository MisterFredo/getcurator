from fastapi import APIRouter, HTTPException, Query, Request
from typing import List, Dict, Optional

from api.company.models import CompanyCreate, CompanyUpdate, CompanyOut

from core.company.service import (
    create_company,
    list_companies,
    list_companies_for_user,
    list_company_types,
    get_company,
    update_company,
    delete_company,
    get_company_aliases,
    create_company_alias,
    delete_company_alias,
)

from core.curator.entity_service import get_company_view
from core.company.ai import suggest_company_aliases

# 🔐 AUTH
from utils.auth import get_user_id_from_request

router = APIRouter()


# ============================================================
# AUTH HELPER (SAFE)
# ============================================================

def require_user(request: Request) -> str:
    user_id = get_user_id_from_request(request)

    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    return user_id


# ============================================================
# CREATE
# ============================================================

@router.post("/create")
def create_route(data: CompanyCreate):
    try:
        company_id = create_company(data)
        return {"status": "ok", "id_company": company_id}
    except Exception as e:
        raise HTTPException(400, f"Erreur création société : {e}")

@router.post("/suggest-alias")
def suggest_alias_route(data: dict):

    name = data.get("name")

    if not name:
        raise HTTPException(400, "name required")

    aliases = suggest_company_aliases(name)

    return {
        "status": "ok",
        "aliases": aliases
    }


# ============================================================
# LIST
# ============================================================

@router.get("/list")
def list_route():
    try:
        companies = list_companies()
        return {"status": "ok", "companies": companies}
    except Exception as e:
        raise HTTPException(400, f"Erreur liste sociétés : {e}")


# ============================================================
# TYPES
# ============================================================

@router.get("/types")
def list_types_route():
    try:
        types = list_company_types()
        return {"status": "ok", "types": types}
    except Exception as e:
        raise HTTPException(400, f"Erreur récupération types sociétés : {e}")


# ============================================================
# USER COMPANIES
# ============================================================

@router.get("/list-curator")
def list_companies_curator(request: Request):
    try:
        user_id = require_user(request)

        companies = list_companies_for_user(user_id)

        return {
            "status": "ok",
            "companies": companies,
        }

    except Exception as e:
        print(f"❌ Companies curator error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal error"
        )

# ============================================================
# ALIASES
# ============================================================

@router.get("/{id_company}/aliases")
def get_aliases_route(id_company: str):

    try:

        aliases = get_company_aliases(
            id_company=id_company
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


@router.post("/{id_company}/alias")
def create_alias_route(
    id_company: str,
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

        create_company_alias(
            id_company=id_company,
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

@router.delete("/{id_company}/alias")
def delete_alias_route(
    id_company: str,
    alias: str,
):
    try:

        delete_company_alias(
            id_company=id_company,
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
# VIEW (CURATOR)
# ============================================================

@router.get("/{id_company}/view")
def get_view_route(
    request: Request,
    id_company: str,
    limit: int = 50,
    offset: int = 0,
    universe_id: Optional[str] = Query(None),
):
    try:
        user_id = require_user(request)

        company = get_company_view(
            company_id=id_company,
            limit=limit,
            offset=offset,
            universe_id=universe_id if universe_id else None,
            user_id=user_id,
        )

        if not company:
            raise HTTPException(404, "Company introuvable")

        return company

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Internal error"
        )


# ============================================================
# UPDATE
# ============================================================

@router.put("/update/{id_company}")
def update_route(id_company: str, data: CompanyUpdate):
    try:
        updated = update_company(id_company, data)

        if not updated:
            raise HTTPException(
                404,
                "Société introuvable ou aucune modification"
            )

        return {"status": "ok", "updated": True}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, f"Erreur mise à jour société : {e}")


# ============================================================
# DELETE (SOFT)
# ============================================================

@router.delete("/{id_company}")
def delete_route(id_company: str):
    try:
        deleted = delete_company(id_company)

        if not deleted:
            raise HTTPException(404, "Société introuvable")

        return {"status": "ok", "deleted": True}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, f"Erreur suppression société : {e}")

# ============================================================
# GET ONE
# ============================================================

@router.get("/{id_company}", response_model=CompanyOut)
def get_route(id_company: str):

    company = get_company(id_company)

    if not company:
        raise HTTPException(404, "Société introuvable")

    return company
