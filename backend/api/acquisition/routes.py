from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List, Dict, Optional

from api.acquisition.models import (
    ContentRawCreate,
    ContentRawOut,
    ContentRawUpdate,
    ContentRawDestockRequest,
)

from core.acquisition.service import (
    list_active_sources,
    list_raw_stock,
    get_raw_detail,
    destock_raw_contents,
    destock_all_raw_contents,
    delete_raw_content,
    retry_raw_content,
    get_source_monitoring,
    get_raw_stats,
)

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
# IMPORT RAW CONTENT
# ============================================================

@router.post("/raw/import")
def import_raw_route(
    payload: ImportTextRequest,
)

    text = payload.get("text")

    id_source = payload.get("id_source")

    id_primary_company = payload.get(
        "id_primary_company"
    )

    count = import_raw_content(
        text=text,
        id_source=id_source,
        id_primary_company=id_primary_company,
    )

    return {
        "imported": count
    }

@router.post("/raw/import-csv")
def import_csv_route(
    payload: ImportCsvRequest
):

    if not payload.csv_text.strip():

        raise HTTPException(
            400,
            "CSV manquant"
        )

    if not payload.id_source:

        raise HTTPException(
            400,
            "Source obligatoire"
        )

    try:

        result = import_urls_csv(
            csv_text=payload.csv_text,
            id_source=payload.id_source,
        )

        return {
            "status": "ok",
            **result
        }

    except Exception as e:

        logger.exception(
            "Erreur import CSV"
        )

        raise HTTPException(
            400,
            str(e)
        )


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

        logger.exception(
            "Erreur stock raw"
        )

        raise HTTPException(
            400,
            str(e)
        )


# ============================================================
# RAW DETAIL
# ============================================================

@router.get("/raw/detail/{id_raw}")
def raw_detail_route(id_raw: str):

    try:

        raw = get_raw_detail(id_raw)

        if not raw:

            raise HTTPException(
                404,
                "RAW introuvable"
            )

        return {
            "status": "ok",
            **raw
        }

    except HTTPException:

        raise

    except Exception as e:

        logger.exception(
            "Erreur récupération RAW detail"
        )

        raise HTTPException(
            400,
            str(e)
        )


# ============================================================
# DESTOCK RAW (BATCH)
# ============================================================

@router.post("/raw/destock")
def destock_raw_route(
    payload: ContentRawDestockRequest
):

    # ========================================================
    # SINGLE RAW
    # ========================================================

    if payload.id_raw:

        result = destock_raw_contents(
            limit=1,
            specific_id=payload.id_raw
        )

        return {
            "status": "ok",
            "processed": result
        }

    # ========================================================
    # FULL DESTOCK
    # ========================================================

    result = destock_all_raw_contents(
        batch_size=payload.limit or 50
    )

    return {
        "status": "ok",
        "processed": result
    }


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

        logger.exception(
            "Erreur suppression RAW"
        )

        raise HTTPException(
            400,
            str(e)
        )


# ============================================================
# IMPORT RAW CONTENT FROM URLS (BATCH)
# ============================================================

@router.post("/raw/import-urls")
def import_urls_route(
    payload: ImportUrlsRequest
):

    if not payload.urls_text.strip():

        raise HTTPException(
            400,
            "URLs manquantes"
        )

    if not payload.id_source:

        raise HTTPException(
            400,
            "Source obligatoire"
        )

    try:

        result = import_urls_batch(
            urls_text=payload.urls_text,
            id_source=payload.id_source,
            id_primary_company=payload.id_primary_company,
        )

        return {
            "status": "ok",
            **result
        }

    except Exception as e:

        logger.exception(
            "Erreur import URLs"
        )

        raise HTTPException(
            400,
            str(e)
        )


# ============================================================
# UPDATE RAW
# ============================================================

@router.put("/raw/update/{id_raw}")
def update_raw(
    id_raw: str,
    payload: ContentRawUpdate
):

    from core.content.service import (
        update_raw_content
    )

    try:

        update_raw_content(

            id_raw=id_raw,

            date_source=payload.date_source,

            source_title=payload.source_title,

            raw_text=payload.raw_text,

            id_primary_company=payload.id_primary_company,
        )

        return {
            "status": "ok"
        }

    except Exception as e:

        raise HTTPException(
            400,
            str(e)
        )


# ============================================================
# RAW STATS (ADMIN)
# ============================================================

@router.get("/raw/admin/stats")
def raw_stats_route():

    try:

        stats = get_raw_stats()

        return {
            "status": "ok",
            "stats": stats
        }

    except Exception as e:

        logger.exception(
            "Erreur stats raw"
        )

        raise HTTPException(
            400,
            str(e)
        )

# ============================================================
# RETRY RAW CONTENT
# ============================================================

@router.post("/raw/retry/{id_raw}")
def retry_raw_route(id_raw: str):

    try:

        retry_raw_content(id_raw)

        return {
            "status": "ok"
        }

    except Exception as e:

        logger.exception(
            "Erreur retry raw"
        )

        raise HTTPException(
            400,
            str(e)
        )

# ============================================================
# LIST SOURCES
# ============================================================

@router.get("/source/list")
def list_sources():

    try:

        rows = list_active_sources()

        return {
            "status": "ok",
            "sources": rows
        }

    except Exception as e:

        logger.exception(
            "Erreur liste sources"
        )

        raise HTTPException(
            400,
            str(e)
        )

# ============================================================
# SOURCE MONITORING
# ============================================================

@router.get("/source/monitoring")
def source_monitoring_route():

    try:

        rows = get_source_monitoring()

        return {
            "status": "ok",
            "sources": rows
        }

    except Exception as e:

        logger.exception(
            "Erreur source monitoring"
        )

        raise HTTPException(
            400,
            str(e)
        )


