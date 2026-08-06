from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List, Dict, Optional

from api.content.models import (
    ContentCreate,
    ContentUpdate,
    ContentPublish,
    ContentSummaryRequest,
    ContentSearchRequest,
    BulkIdsRequest,
)

from core.content.service import (
    create_content,
    list_contents_admin,
    get_content,
    update_content,
    archive_content,
    delete_content,
    publish_content,
    get_content_stats,
    mark_content_ready,
    bulk_publish,
    bulk_ready,
)

from core.content.sync_service import (
    sync_content,
    bulk_sync_contents,
    sync_all_published_contents,
    sync_all_numbers,
)

from core.content.search_service import search_contents

from config import (
    BQ_PROJECT,
    BQ_DATASET,
)

from utils.bigquery_utils import (
    query_bq,
)

import logging

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================
# CREATE CONTENT
# ============================================================

@router.post("/create")
def create_route(data: ContentCreate):

    try:

        content_id = create_content(data)

        return {
            "status": "ok",
            "id_content": content_id
        }

    except Exception as e:

        logger.exception(
            "Erreur création content"
        )

        raise HTTPException(
            400,
            str(e)
        )


# ============================================================
# LIST CONTENTS (ADMIN)
# ============================================================

@router.get("/list")
def list_route():

    try:

        contents = list_contents_admin()

        return {
            "status": "ok",
            "contents": contents
        }

    except Exception as e:

        logger.exception(
            "Erreur liste content"
        )

        raise HTTPException(
            400,
            str(e)
        )

@router.post("/search")
def search_route(
    request: ContentSearchRequest
):
    try:
        return search_contents(request)

    except Exception as e:
        raise HTTPException(
            400,
            str(e)
        )


# ============================================================
# CONTENT STATS (ADMIN)
# ============================================================

@router.get("/admin/stats")
def stats_route():

    try:

        stats = get_content_stats()

        return {
            "status": "ok",
            "stats": stats
        }

    except Exception as e:

        logger.exception(
            "Erreur stats content"
        )

        raise HTTPException(
            400,
            str(e)
        )

# ============================================================
# UPDATE CONTENT
# ============================================================

@router.put("/update/{id_content}")
def update_route(
    id_content: str,
    data: ContentUpdate
):

    try:

        update_content(
            id_content,
            data
        )

        return {
            "status": "ok",
            "updated": True
        }

    except Exception as e:

        logger.exception(
            "Erreur mise à jour content"
        )

        raise HTTPException(
            400,
            str(e)
        )


# ============================================================
# ARCHIVE CONTENT
# ============================================================

@router.post("/archive/{id_content}")
def archive_route(id_content: str):

    try:

        archive_content(id_content)

        return {
            "status": "ok",
            "archived": True
        }

    except Exception as e:

        logger.exception(
            "Erreur archivage content"
        )

        raise HTTPException(
            400,
            str(e)
        )


# ============================================================
# DELETE CONTENT
# ============================================================

@router.delete("/delete/{id_content}")
def delete_route(id_content: str):

    try:

        delete_content(id_content)

        return {
            "status": "ok",
            "deleted": True
        }

    except Exception as e:

        logger.exception(
            "Erreur suppression content"
        )

        raise HTTPException(
            400,
            str(e)
        )


# ============================================================
# PUBLISH CONTENT
# ============================================================

@router.post("/publish/{id_content}")
def publish_route(
    id_content: str,
    payload: ContentPublish
):

    try:

        status = publish_content(
            id_content=id_content,
            published_at=payload.publish_at,
        )

        return {
            "status": "ok",
            "published_status": status
        }

    except Exception as e:

        logger.exception(
            "Erreur publication content"
        )

        raise HTTPException(
            400,
            str(e)
        )


# ============================================================
# 🔥 NEW — SYNC CONTENT
# ============================================================

@router.post("/sync/{id_content}")
def sync_route(id_content: str):

    try:

        result = sync_content(
            id_content=id_content,
        )

        return {
            "status": "ok",
            **result
        }

    except Exception as e:

        logger.exception(
            "Erreur sync content"
        )

        raise HTTPException(
            400,
            str(e)
        )


# ============================================================
# 🔥 NEW — BULK SYNC CONTENTS
# ============================================================

@router.post("/bulk/sync")
def bulk_sync_route(payload: BulkIdsRequest):

    try:

        if not payload.ids:

            raise ValueError(
                "No ids provided"
            )

        result = bulk_sync_contents(
            payload.ids
        )

        return {
            "status": "ok",
            **result
        }

    except Exception as e:

        logger.exception(
            "Erreur bulk sync"
        )

        raise HTTPException(
            400,
            str(e)
        )



# ============================================================
# GET ONE CONTENT (ADMIN)
# ============================================================

@router.get("/{id_content}")
def get_route(id_content: str):

    content = get_content(id_content)

    if not content:

        raise HTTPException(
            404,
            "Content introuvable"
        )

    return {
        "status": "ok",
        "content": content
    }


# ============================================================
# MARK READY
# ============================================================

@router.post("/ready/{id_content}")
def mark_ready_route(id_content: str):

    try:

        mark_content_ready(id_content)

        return {
            "status": "ok"
        }

    except Exception as e:

        raise HTTPException(
            400,
            str(e)
        )

# ============================================================
# BULK READY
# ============================================================

@router.post("/bulk/ready")
def bulk_ready_route(
    payload: BulkIdsRequest
):

    try:

        if not payload.ids:

            raise ValueError(
                "No ids provided"
            )

        updated = bulk_ready(
            payload.ids
        )

        return {
            "status": "ok",
            "updated": updated
        }

    except Exception as e:

        raise HTTPException(
            400,
            str(e)
        )


# ============================================================
# BULK PUBLISH
# ============================================================

@router.post("/bulk/publish")
def bulk_publish_route(
    payload: BulkIdsRequest
):

    try:

        result = bulk_publish(
            payload.ids
        )

        return {
            "status": "ok",
            **result
        }

    except Exception as e:

        raise HTTPException(
            400,
            str(e)
        )

# ============================================================
# FULL SYNC — ALL PUBLISHED CONTENTS
# ============================================================

@router.post("/sync-all-published")
def sync_all_published_route():

    try:

        result = sync_all_published_contents()

        return {
            "status": "ok",
            **result
        }

    except Exception as e:

        logger.exception(
            "Erreur full sync published"
        )

        raise HTTPException(
            400,
            str(e)
        )

@router.post("/sync-numbers")
def sync_numbers_route():

    try:

        result = sync_all_numbers()

        return {
            "status": "ok",
            **result
        }

    except Exception as e:

        raise HTTPException(400, str(e))
