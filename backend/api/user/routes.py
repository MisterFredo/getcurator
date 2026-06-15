from fastapi import APIRouter, HTTPException, Request
from typing import Optional

from api.user.models import (
    CreateUserPayload,
    AssignUniversePayload,
    LoginPayload,
    UpdateUserPayload,
    UserKeywordPayload,
    UserKeywordPayload,
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
    list_digest_users,
)

from core.user.user_preferences_service import (
    get_user_preferences,
    add_user_preference,
    remove_user_preference,
)

from core.user.user_keyword_service import (
    get_user_keywords,
    add_user_keyword,
    remove_user_keyword,
)

from core.user.user_profile_service import (
    get_user_profile,
    update_user_profile,
)

from utils.auth import get_user_id_from_request

router = APIRouter()


# =========================================================
# USER PREFERENCES
# =========================================================

@router.get("/preferences")
def get_preferences(request: Request):

    user_id = get_user_id_from_request(request)

    if not user_id:
        return {
            "preferences": {
                "COMPANY": [],
                "TOPIC": [],
                "SOLUTION": [],
            }
        }

    from core.user.user_preferences_service import get_user_preferences_grouped

    prefs = get_user_preferences_grouped(user_id)

    return {
        "preferences": prefs or {
            "COMPANY": [],
            "TOPIC": [],
            "SOLUTION": [],
        }
    }


@router.post("/preferences/add")
def add_preference(request: Request, payload: dict):

    user_id = get_user_id_from_request(request)

    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    add_user_preference(
        user_id,
        payload.get("type"),
        payload.get("value_id")
    )

    return {"status": "ok"}


@router.post("/preferences/remove")
def remove_preference(request: Request, payload: dict):

    user_id = get_user_id_from_request(request)

    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    remove_user_preference(
        user_id,
        payload.get("type"),
        payload.get("value_id")
    )

    return {"status": "ok"}


# =========================================================
# USER KEYWORDS
# =========================================================

@router.get("/keywords")
def get_keywords(request: Request):

    user_id = get_user_id_from_request(request)

    if not user_id:
        return {
            "keywords": []
        }

    keywords = get_user_keywords(user_id)

    return {
        "keywords": keywords
    }


@router.post("/keywords/add")
def add_keyword(
    request: Request,
    payload: UserKeywordPayload
):

    user_id = get_user_id_from_request(request)

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )

    add_user_keyword(
        user_id=user_id,
        keyword=payload.keyword,
    )

    return {
        "status": "ok"
    }


@router.post("/keywords/remove")
def remove_keyword(
    request: Request,
    payload: UserKeywordPayload
):

    user_id = get_user_id_from_request(request)

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )

    remove_user_keyword(
        user_id=user_id,
        keyword=payload.keyword,
    )

    return {
        "status": "ok"
    }


# =========================================================
# USER PROFILE
# =========================================================

@router.get("/profile")
def get_profile(request: Request):

    user_id = get_user_id_from_request(request)

    if not user_id:
        return {
            "profile": None
        }

    profile = get_user_profile(user_id)

    return {
        "profile": profile
    }


@router.post("/profile/update")
def update_profile(
    request: Request,
    payload: UserProfilePayload
):

    user_id = get_user_id_from_request(request)

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )

    update_user_profile(
        user_id=user_id,
        geography_1=payload.geography_1,
        geography_2=payload.geography_2,
        geography_3=payload.geography_3,
        profile_text=payload.profile_text,
    )

    return {
        "status": "ok"
    }

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
        company="Curator",
        language="fr",
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

@router.get("/digest-users")
def list_digest_users_route():

    users = list_digest_users()

    return {
        "users": users
    }


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
# LOGIN
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
        "token": user["ID_USER"],
        "user_id": user["ID_USER"],
        "email": user["EMAIL"],
        "role": user.get("ROLE", "user"),
        "language": user.get("LANGUAGE", "fr"),  # 🔥 AJOUT
        "universes": universes,
    }


# =========================================================
# GET CURRENT USER (ME)
# =========================================================

@router.get("/me")
def get_me(request: Request):

    user_id = get_user_id_from_request(request)

    if not user_id:
        return {"user": None}

    user = get_user_by_id(user_id)

    if not user:
        return {"user": None}

    return {"user": user}


# =========================================================
# USER CONTEXT
# =========================================================

@router.get("/context")
def get_context(request: Request):

    user_id = get_user_id_from_request(request)

    # 🔥 MODE PUBLIC
    if not user_id:
        return {
            "universes": [],
            "preferences": {
                "COMPANY": [],
                "TOPIC": [],
                "SOLUTION": [],
            }
        }

    context = get_user_context(user_id)

    if not context:
        return {}

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

# =========================================================
# GET USER (BY ID)
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

