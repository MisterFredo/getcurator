from fastapi import APIRouter, HTTPException

from api.topic.models import TopicCreate, TopicUpdate

from core.topic.service import (
    create_topic,
    list_topics,
    list_topics_for_user,
    get_topic,
    update_topic,
    delete_topic,
)

# 🔥 CURATOR
from core.curator.entity_service import get_topic_view

router = APIRouter()


# ============================================================
# CREATE
# ============================================================
@router.post("/create")
def create_route(data: TopicCreate):
    try:
        topic_id = create_topic(data)
        return {"status": "ok", "id_topic": topic_id}
    except Exception as e:
        raise HTTPException(400, f"Erreur création topic : {e}")


# ============================================================
# LIST
# ============================================================
@router.get("/list")
def list_route():
    try:
        topics = list_topics()
        return {"status": "ok", "topics": topics}
    except Exception as e:
        raise HTTPException(400, f"Erreur liste topics : {e}")

@router.get("/list-for-user")
def topic_list_for_user(request: Request):

    user_id = request.headers.get("x-user-id")

    if not user_id:
        raise HTTPException(401, "User ID missing")

    topics = list_topics_for_user(user_id)

    return {
        "status": "ok",
        "topics": topics,
    }


# ============================================================
# GET ONE (ADMIN / CRUD)
# ============================================================
@router.get("/{id_topic}")
def get_route(id_topic: str):
    topic = get_topic(id_topic)

    if not topic:
        raise HTTPException(404, "Topic introuvable")

    return topic


# ============================================================
# GET VIEW (CURATOR)
# ============================================================
@router.get("/{id_topic}/view")
def get_view_route(
    id_topic: str,
    limit: int = 20,
    offset: int = 0
):
    try:
        topic = get_topic_view(
            id_topic,
            limit=limit,
            offset=offset
        )

        if not topic:
            raise HTTPException(404, "Topic introuvable")

        return topic

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            400,
            f"Erreur récupération topic view : {e}"
        )


# ============================================================
# UPDATE
# ============================================================
@router.put("/update/{id_topic}")
def update_route(id_topic: str, data: TopicUpdate):
    try:
        updated = update_topic(id_topic, data)
        return {"status": "ok", "updated": updated}
    except Exception as e:
        raise HTTPException(400, f"Erreur mise à jour topic : {e}")


# ============================================================
# DELETE
# ============================================================
@router.delete("/{id_topic}")
def delete_route(id_topic: str):
    try:
        deleted = delete_topic(id_topic)

        if not deleted:
            raise HTTPException(404, "Topic introuvable")

        return {"status": "ok", "deleted": True}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, f"Erreur suppression topic : {e}")
