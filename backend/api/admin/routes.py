from fastapi import APIRouter, HTTPException, Response
from core.digest.service import search_digest
from core.digest.template_service import (
    create_template,
    list_templates,
    get_template,
    update_template,
    delete_template,
)

from core.digest.run_service import generate_monthly_runs

router = APIRouter()

ADMIN_EMAIL = "mister.fredo@gmail.com"


# ============================================================
# LOGIN / LOGOUT
# ============================================================

@router.post("/login")
def admin_login(payload: dict, response: Response):
    email = payload.get("email")

    if email != ADMIN_EMAIL:
        raise HTTPException(401, "Unauthorized")

    response.set_cookie(
        key="ratecard_admin_session",
        value="ok",
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
        path="/",
    )

    return {"status": "ok"}


@router.post("/logout")
def admin_logout(response: Response):
    response.delete_cookie(
        key="ratecard_admin_session",
        path="/",
    )
    return {"status": "ok"}


# ============================================================
# DIGEST SEARCH
# ============================================================

@router.post("/digest/search")
def admin_digest_search(payload: dict):

    period = payload.get("period", "total")

    if period not in ("total", "30d", "7d"):
        period = "total"

    result = search_digest(
        topics=payload.get("topics"),
        companies=payload.get("companies"),
        news_types=payload.get("news_types"),
        limit=payload.get("limit", 20),
        cursor=payload.get("cursor"),
        period=period,
    )

    return {
        "status": "ok",
        "result": result,
    }


# ============================================================
# DIGEST TEMPLATES
# ============================================================

@router.get("/digest/template")
def admin_list_templates():
    templates = list_templates()

    return {
        "status": "ok",
        "templates": templates,
    }


@router.get("/digest/template/{template_id}")
def admin_get_template(template_id: str):
    tpl = get_template(template_id)

    if not tpl:
        raise HTTPException(404, "Template introuvable")

    return {
        "status": "ok",
        "template": tpl,
    }


@router.post("/digest/template")
def admin_create_template(payload: dict):
    template_id = create_template(payload)

    return {
        "status": "ok",
        "id_template": template_id,
    }


@router.put("/digest/template/{template_id}")
def admin_update_template(template_id: str, payload: dict):
    update_template(template_id, payload)

    return {
        "status": "ok",
        "updated": True,
    }


@router.delete("/digest/template/{template_id}")
def admin_delete_template(template_id: str):
    delete_template(template_id)

    return {
        "status": "ok",
        "deleted": True,
    }

@router.post("/digest/template/apply")
def admin_apply_template(payload: dict):

    template_id = payload.get("template_id")

    if not template_id:
        raise HTTPException(400, "template_id requis")

    result = apply_template(template_id)

    return {
        "status": "ok",
        "result": result,
    }


@router.post("/digest/run/generate")
def admin_generate_digest_runs(payload: dict):

    period = payload.get("period")

    if not period:
        raise HTTPException(400, "period requis")

    runs = generate_monthly_runs(period)

    return {
        "status": "ok",
        "count": len(runs),
    }

@router.get("/digest/run")
def admin_list_runs():
    return {
        "status": "ok",
        "runs": list_runs(),
    }


