from fastapi import APIRouter, HTTPException, Request

from api.topic.models import (
    TopicCreate,
    TopicUpdate,
)

from core.topic.service import (
    create_topic,
    list_topics,
    list_topics_for_user,
    get_topic,
    update_topic,
    delete_topic,
)

from core.curator.entity_service import (
    get_topic_view,
)

from utils.auth import (
    get_user_id_from_request,
)

router = APIRouter()


# ============================================================
# AUTH
# ============================================================

def require_user(
    request: Request,
) -> str:

    user_id = get_user_id_from_request(
        request
    )

    if not user_id:

        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
        )

    return user_id


# ============================================================
# CREATE
# ============================================================

@router.post("/create")
def create_route(
    data: TopicCreate,
):

    try:

        topic_id = create_topic(
            data
        )

        return {
            "status": "ok",
            "id_topic": topic_id,
        }

    except Exception as e:

        raise HTTPException(
            400,
            f"Erreur création topic : {e}",
        )


# ============================================================
# LIST
# ============================================================

@router.get("/list")
def list_route():

    try:

        return {
            "status": "ok",
            "topics": list_topics(),
        }

    except Exception as e:

        raise HTTPException(
            400,
            f"Erreur liste topics : {e}",
        )


# ============================================================
# LIST CURATOR
# ============================================================

@router.get("/list-curator")
def list_curator_route(
    request: Request,
):

    try:

        user_id = require_user(
            request
        )

        return {
            "status": "ok",
            "topics": list_topics_for_user(
                user_id
            ),
        }

    except HTTPException:
        raise

    except Exception:

        raise HTTPException(
            status_code=500,
            detail="Internal error",
        )


# ============================================================
# GET ONE
# ============================================================

@router.get("/{id_topic}")
def get_route(
    id_topic: str,
):

    try:

        topic = get_topic(
            id_topic
        )

        if not topic:

            raise HTTPException(
                404,
                "Topic introuvable",
            )

        return {
            "status": "ok",
            "topic": topic,
        }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            400,
            f"Erreur récupération topic : {e}",
        )


# ============================================================
# VIEW
# ============================================================

@router.get("/{id_topic}/view")
def get_view_route(

    id_topic: str,

    limit: int = 20,

    offset: int = 0,

):

    try:

        topic = get_topic_view(

            id_topic,

            limit=limit,

            offset=offset,

        )

        if not topic:

            raise HTTPException(
                404,
                "Topic introuvable",
            )

        return topic

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            400,
            f"Erreur récupération topic : {e}",
        )


# ============================================================
# UPDATE
# ============================================================

@router.put("/update/{id_topic}")
def update_route(

    id_topic: str,

    data: TopicUpdate,

):

    try:

        updated = update_topic(

            id_topic,

            data,

        )

        if not updated:

            raise HTTPException(
                404,
                "Topic introuvable ou aucune modification",
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
            f"Erreur mise à jour topic : {e}",
        )


# ============================================================
# DELETE
# ============================================================

@router.delete("/{id_topic}")
def delete_route(
    id_topic: str,
):

    try:

        deleted = delete_topic(
            id_topic
        )

        if not deleted:

            raise HTTPException(
                404,
                "Topic introuvable",
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
            f"Erreur suppression topic : {e}",
        )
