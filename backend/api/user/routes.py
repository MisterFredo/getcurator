from fastapi import APIRouter, HTTPException, Query, Request
from typing import Optional

from api.user.models import (
    CreateUserPayload,
    AssignUniversePayload,
    LoginPayload,
    UpdateUserPayload,
)

from core.user.user_service import (
    create_user,
    update_user,
    assign_universes,
    list_users,
    get_user_by_email,
    get_user_by_id,
    get_user_universes,
    get_user_context,
)

router = APIRouter()

# =========================================================
# CREATE USER
# =========================================================

@router.post("/create")
def create_user_route(payload: CreateUserPayload):
    try:
        user_id = create_user(payload)
        return {
            "status": "ok",
            "user_id": user_id,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/bootstrap-admin")
def bootstrap_admin(secret: str):

    if secret != "INIT_123":
        raise HTTPException(status_code=403)

    existing = get_user_by_email("mister.fredo@gmail.com")

    if existing:
        return {"status": "already_exists"}

    payload = CreateUserPayload(
        email="mister.fredo@gmail.com",
        password="felixmax55",
        name="Admin Fredo",
        company="Curator",          # 🔥 AJOUT
        language="fr",              # 🔥 AJOUT
        role="admin",
        universes=[]
    )

    user_id = create_user(payload)

    return {
        "status": "created",
        "user_id": user_id
    }
# =========================================================
# LIST USERS
# =========================================================

@router.get("/list")
def list_users_route():
    users = list_users()
    return {"users": users}


# =========================================================
# UPDATE USER
# =========================================================

@router.post("/update")
def update_user_route(payload: UpdateUserPayload):
    try:
        update_user(payload)
        return {"status": "ok"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =========================================================
# LOGIN (VERSION SIMPLE - SANS JWT)
# =========================================================

@router.post("/login")
def login(payload: LoginPayload):

    user = get_user_by_email(payload.email)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if payload.password != user["PASSWORD"]:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    universes = get_user_universes(user["ID_USER"])

    return {
        "token": user["ID_USER"],  # 👈 seule vraie modif utile
        "user_id": user["ID_USER"],
        "email": user["EMAIL"],
        "role": user.get("ROLE", "user"),
        "universes": universes,
    }
# =========================================================
# GET USER
# =========================================================

@router.get("/{user_id}")
def get_user(user_id: str):
    user = get_user_by_id(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    universes = get_user_universes(user_id)

    return {
        "user": user,
        "universes": universes,
    }


# =========================================================
# USER CONTEXT (🔥 PLUS DE COOKIES)
# =========================================================

@router.get("/context")
def get_context(request: Request):

    user_id = get_user_id_from_request(request)

    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    context = get_user_context(user_id)

    if not context:
        raise HTTPException(status_code=404, detail="User not found or inactive")

    return context


# =========================================================
# ASSIGN UNIVERS
# =========================================================

@router.post("/assign-universes")
def assign_universes_route(payload: AssignUniversePayload):
    assign_universes(payload.user_id, payload.universes)

    return {
        "status": "ok",
        "assigned": payload.universes,
    }
