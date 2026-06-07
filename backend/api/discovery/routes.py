from fastapi import APIRouter, HTTPException

from api.discovery.models import (
    DiscoveryListOut,
    ScanResponse,
    StoreRequest,
    StoreResponse,
    IgnoreRequest,
    IgnoreResponse,
)

from core.discovery.service import (
    scan_all_sources,
    scan_source,
    list_discovery_items,
    store_discovery_urls,
    ignore_discovery_urls,

    # 🔥 NEW
    dismiss_discovery,
)

router = APIRouter()


# ============================================================
# SCAN ALL SOURCES
# ============================================================

@router.post(
    "/scan-all",
    response_model=ScanResponse,
)
def scan_all_route():

    try:

        result = scan_all_sources()

        return result

    except Exception as e:

        raise HTTPException(
            400,
            f"Erreur scan global : {e}"
        )


# ============================================================
# SCAN ONE SOURCE
# ============================================================

@router.post(
    "/scan/{source_id}",
    response_model=ScanResponse,
)
def scan_source_route(source_id: str):

    try:

        result = scan_source(source_id)

        return result

    except Exception as e:

        raise HTTPException(
            400,
            f"Erreur scan source : {e}"
        )


# ============================================================
# LIST DISCOVERY
# ============================================================

@router.get(
    "/list",
    response_model=DiscoveryListOut,
)
def list_route():

    try:

        items = list_discovery_items()

        return {
            "status": "ok",
            "items": items,
        }

    except Exception as e:

        raise HTTPException(
            400,
            f"Erreur liste discovery : {e}"
        )


# ============================================================
# STORE SELECTED URLS
# ============================================================

@router.post(
    "/store",
    response_model=StoreResponse,
)
def store_route(data: StoreRequest):

    try:

        result = store_discovery_urls(
            data.discovery_ids
        )

        return result

    except Exception as e:

        raise HTTPException(
            400,
            f"Erreur stockage URLs : {e}"
        )


# ============================================================
# IGNORE SELECTED URLS
# ============================================================

@router.post(
    "/ignore",
    response_model=IgnoreResponse,
)
def ignore_route(data: IgnoreRequest):

    try:

        result = ignore_discovery_urls(
            data.discovery_ids
        )

        return result

    except Exception as e:

        raise HTTPException(
            400,
            f"Erreur ignore URLs : {e}"
        )


# ============================================================
# DISMISS ONE URL
# ============================================================

@router.post(
    "/dismiss/{id_discovery}",
)
def dismiss_route(id_discovery: str):

    try:

        dismiss_discovery(
            id_discovery
        )

        return {
            "status": "ok",
            "id_discovery": id_discovery,
        }

    except Exception as e:

        raise HTTPException(
            400,
            f"Erreur dismiss URL : {e}"
        )
