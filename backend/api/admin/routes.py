from fastapi import APIRouter, HTTPException, Response

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





