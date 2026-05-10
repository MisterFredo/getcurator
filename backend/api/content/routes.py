from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List, Dict, Optional

from api.content.models import (
    ContentCreate,
    ContentUpdate,
    ContentPublish,
    ContentSummaryRequest,
    ContentRawCreate,
    ContentRawOut,
    ContentRawUpdate,
    ContentRawDestockRequest,
    ImportUrlsRequest,
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
    list_active_sources,
    store_raw_content,
    list_raw_stock,
    get_raw_detail,
    destock_raw_contents,
    destock_all_raw_contents,
    delete_raw_content,
    retry_raw_content,
    get_source_monitoring,
    get_raw_stats,
    mark_content_ready,
    bulk_publish,
    bulk_ready,
)

from core.content.ai import generate_summary
from core.content.news_ai import generate_news
from core.content.raw_import_service import import_raw_content
from core.content.raw_import_service import import_urls_batch

from utils.bigquery_utils import query_bq

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
        return {"status": "ok", "id_content": content_id}
    except Exception as e:
        logger.exception("Erreur création content")
        raise HTTPException(400, str(e))


# ============================================================
# LIST CONTENTS (ADMIN)
# ============================================================
@router.get("/list")
def list_route():
    try:
        contents = list_contents_admin()
        return {"status": "ok", "contents": contents}
    except Exception as e:
        logger.exception("Erreur liste content")
        raise HTTPException(400, str(e))


# ============================================================
# CONTENT STATS (ADMIN)
# ============================================================
@router.get("/admin/stats")
def stats_route():
    try:
        stats = get_content_stats()
        return {"status": "ok", "stats": stats}
    except Exception as e:
        logger.exception("Erreur stats content")
        raise HTTPException(400, str(e))


# ============================================================
# LIST SOURCES
# ============================================================
@router.get("/source/list")
def list_sources():
    try:
        rows = list_active_sources()
        return {"status": "ok", "sources": rows}
    except Exception as e:
        logger.exception("Erreur liste sources")
        raise HTTPException(400, str(e))


# ============================================================
# UPDATE CONTENT
# ============================================================
@router.put("/update/{id_content}")
def update_route(id_content: str, data: ContentUpdate):
    try:
        update_content(id_content, data)
        return {"status": "ok", "updated": True}
    except Exception as e:
        logger.exception("Erreur mise à jour content")
        raise HTTPException(400, str(e))


# ============================================================
# ARCHIVE CONTENT
# ============================================================
@router.post("/archive/{id_content}")
def archive_route(id_content: str):
    try:
        archive_content(id_content)
        return {"status": "ok", "archived": True}
    except Exception as e:
        logger.exception("Erreur archivage content")
        raise HTTPException(400, str(e))

@router.delete("/delete/{id_content}")
def delete_route(id_content: str):
    try:
        from core.content.service import delete_content
        delete_content(id_content)
        return {"status": "ok", "deleted": True}
    except Exception as e:
        logger.exception("Erreur suppression content")
        raise HTTPException(400, str(e))


# ============================================================
# PUBLISH CONTENT
# ============================================================
@router.post("/publish/{id_content}")
def publish_route(id_content: str, payload: ContentPublish):
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
        logger.exception("Erreur publication content")
        raise HTTPException(400, str(e))

# ============================================================
# STORE RAW CONTENT
# ============================================================
@router.post("/store-raw")
def store_raw_route(payload: ContentRawCreate):
    try:

        raw_id = store_raw_content(

            source_id=payload.source_id,

            source_title=payload.source_title,

            raw_text=payload.raw_text,

            date_source=payload.date_source,

            # 🔥 NEW
            content_type=payload.content_type,
        )

        return {
            "status": "ok",
            "id_raw": raw_id
        }

    except Exception as e:
        logger.exception("Erreur stockage raw content")
        raise HTTPException(400, str(e))

# ============================================================
# IMPORT RAW CONTENT
# ============================================================

@router.post("/raw/import")
def import_raw_route(payload: dict):

    text = payload.get("text")
    id_source = payload.get("id_source")

    # 🔥 NEW
    content_type = payload.get(
        "content_type",
        "ANALYSIS"
    )

    count = import_raw_content(
        text=text,
        id_source=id_source,
        content_type=content_type,
    )

    return {"imported": count}

# ============================================================
# LIST RAW STOCK
# ============================================================
@router.get("/raw/stock")
def raw_stock_route(
    status: Optional[str] = None,
    source_id: Optional[str] = None,
    import_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    try:
        result = list_raw_stock(
            status=status,
            source_id=source_id,
            import_type=import_type,
            limit=limit,
            offset=offset,
        )

        return {
            "status": "ok",
            "rows": result["rows"],
            "total": result["total"],
        }

    except Exception as e:
        logger.exception("Erreur stock raw")
        raise HTTPException(400, str(e))

# ============================================================
# RAW DETAIL
# ============================================================

@router.get("/raw/detail/{id_raw}")
def raw_detail_route(id_raw: str):
    try:
        from core.content.service import get_raw_detail

        raw = get_raw_detail(id_raw)

        if not raw:
            raise HTTPException(404, "RAW introuvable")

        return {
            "status": "ok",
            **raw
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Erreur récupération RAW detail")
        raise HTTPException(400, str(e))

# ============================================================
# DESTOCK RAW (BATCH)
# ============================================================
@router.post("/raw/destock")
def destock_raw_route(payload: ContentRawDestockRequest):

    # 🔹 Si on destock un RAW précis → on garde le comportement actuel
    if payload.id_raw:
        result = destock_raw_contents(
            limit=1,
            specific_id=payload.id_raw
        )
        return {"status": "ok", "processed": result}

    # 🔹 Sinon → on destock TOUT en batchs successifs
    result = destock_all_raw_contents(
        batch_size=payload.limit or 50
    )

    return {"status": "ok", "processed": result}

# ============================================================
# DELETE RAW CONTENT
# ============================================================
@router.delete("/raw/delete/{id_raw}")
def delete_raw_route(id_raw: str):
    try:
        delete_raw_content(id_raw)

        return {
            "status": "ok",
            "deleted_id": id_raw
        }

    except Exception as e:
        logger.exception("Erreur suppression RAW")
        raise HTTPException(400, str(e))

# ============================================================
# IMPORT RAW CONTENT FROM URLS (BATCH)
# ============================================================

@router.post("/raw/import-urls")
def import_urls_route(payload: ImportUrlsRequest):

    if not payload.urls_text.strip():
        raise HTTPException(400, "URLs manquantes")

    if not payload.id_source:
        raise HTTPException(400, "Source obligatoire")

    try:

        result = import_urls_batch(
            urls_text=payload.urls_text,
            id_source=payload.id_source
        )

        return {
            "status": "ok",
            **result
        }

    except Exception as e:
        logger.exception("Erreur import URLs")
        raise HTTPException(400, str(e))

@router.put("/raw/update/{id_raw}")
def update_raw(
    id_raw: str,
    payload: ContentRawUpdate
):

    from core.content.service import update_raw_content

    try:

        update_raw_content(

            id_raw=id_raw,

            date_source=payload.date_source,

            source_title=payload.source_title,

            raw_text=payload.raw_text,

            # 🔥 NEW
            content_type=payload.content_type,
        )

        return {"status": "ok"}

    except Exception as e:
        raise HTTPException(400, str(e))

# ============================================================
# RAW STATS (ADMIN)
# ============================================================
@router.get("/raw/admin/stats")
def raw_stats_route():
    try:
        stats = get_raw_stats()
        return {"status": "ok", "stats": stats}
    except Exception as e:
        logger.exception("Erreur stats raw")
        raise HTTPException(400, str(e))

# ============================================================
# SOURCE MONITORING
# ============================================================
@router.get("/source/monitoring")
def source_monitoring_route():
    try:
        from core.content.service import get_source_monitoring

        rows = get_source_monitoring()

        return {
            "status": "ok",
            "sources": rows
        }

    except Exception as e:
        logger.exception("Erreur source monitoring")
        raise HTTPException(400, str(e))


# ============================================================
# IA — GENERATE CONTENT
# ============================================================
@router.post("/ai/generate")
def ai_generate(payload: ContentSummaryRequest):

    if not payload.source_text.strip():
        raise HTTPException(400, "Source manquante")

    try:

        # 🔥 NEW
        if (
            getattr(payload, "content_type", "ANALYSIS")
            == "NEWS"
        ):

            result = generate_news(
                source_id=payload.source_id,
                source_text=payload.source_text,
            )

        else:

            result = generate_summary(
                source_id=payload.source_id,
                source_text=payload.source_text,
            )

        if not isinstance(result, dict):
            raise ValueError("Réponse IA invalide")

        return {
            "status": "ok",
            **result
        }

    except Exception as e:
        logger.exception("Erreur génération contenu IA")
        raise HTTPException(400, str(e))


# ============================================================
# GET ONE CONTENT (ADMIN)
# ============================================================
@router.get("/{id_content}")
def get_route(id_content: str):

    content = get_content(id_content)

    if not content:
        raise HTTPException(404, "Content introuvable")

    return {"status": "ok", "content": content}

@router.post("/ready/{id_content}")
def mark_ready_route(id_content: str):
    try:
        mark_content_ready(id_content)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(400, str(e))

# ============================================================
# RETRY RAW CONTENT
# ============================================================

@router.post("/raw/retry/{id_raw}")
def retry_raw_route(id_raw: str):
    try:
        retry_raw_content(id_raw)
        return {"status": "ok"}
    except Exception as e:
        logger.exception("Erreur retry raw")
        raise HTTPException(400, str(e))

@router.post("/bulk/ready")
def bulk_ready_route(payload: BulkIdsRequest):
    try:
        if not payload.ids:
            raise ValueError("No ids provided")

        updated = bulk_ready(payload.ids)

        return {
            "status": "ok",
            "updated": updated
        }

    except Exception as e:
        raise HTTPException(400, str(e))


@router.post("/bulk/publish")
def bulk_publish_route(payload: BulkIdsRequest):
    try:
        result = bulk_publish(payload.ids)
        return {
            "status": "ok",
            **result
        }
    except Exception as e:
        raise HTTPException(400, str(e))
