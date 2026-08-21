from fastapi import APIRouter, HTTPException

from api.discovery.models import (
    DiscoveryListOut,
    ScanAllRequest,
    ScanResponse,
    StoreRequest,
    StoreResponse,
    IgnoreRequest,
    IgnoreResponse,
    ManualDiscoveryListOut,
)

from core.discovery.service import (
    scan_all_sources,
    scan_source,
    list_discovery_items,
    store_discovery_urls,
    ignore_discovery_urls,
    mark_discovery_manual,
    list_manual_discovery,
    dismiss_discovery,
)

router = APIRouter()

# ============================================================
# TEST RSS PAGINATION
# ============================================================

@router.get("/test-rss")
def test_rss():

    import requests
    import xml.etree.ElementTree as ET

    results = []

    urls = [
        "https://www.retaildive.com/feeds/news/",
        "https://www.retaildive.com/feeds/news/?page=2",
        "https://www.retaildive.com/feeds/news/?page=3",
    ]

    for url in urls:

        try:

            response = requests.get(
                url,
                timeout=30,
            )

            data = {
                "url": url,
                "status_code": response.status_code,
                "content_type": response.headers.get(
                    "content-type"
                ),
                "size": len(response.content),
            }

            if response.status_code == 200:

                try:

                    root = ET.fromstring(
                        response.content
                    )

                    items = root.findall(
                        ".//item"
                    )

                    data["items"] = len(
                        items
                    )

                    data["links"] = [
                        (
                            item.find("link").text
                            if item.find("link") is not None
                            else None
                        )
                        for item in items
                    ]

                except Exception as e:

                    data["parse_error"] = str(e)

            results.append(
                data
            )

        except Exception as e:

            results.append(
                {
                    "url": url,
                    "error": str(e),
                }
            )

    return {
        "results": results
    }




# ============================================================
# SCAN ALL SOURCES
# ============================================================

@router.post(
    "/scan-all",
    response_model=ScanResponse,
)
def scan_all_route(
    data: ScanAllRequest,
):

    try:

        result = scan_all_sources(
            universe_id=data.universe_id,
        )

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
# MANUAL DISCOVERY LIST
# ============================================================

@router.get(
    "/manual-list",
    response_model=ManualDiscoveryListOut,
)
def manual_list_route():

    try:

        items = list_manual_discovery()

        return {
            "status": "ok",
            "items": items,
        }

    except Exception as e:

        raise HTTPException(
            400,
            f"Erreur liste manual discovery : {e}"
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
def dismiss_route(
    id_discovery: str
):

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

# ============================================================
# SEND TO MANUAL REVIEW
# ============================================================

@router.post(
    "/manual",
)
def manual_route(data: IgnoreRequest):

    try:

        result = mark_discovery_manual(
            data.discovery_ids
        )

        return result

    except Exception as e:

        raise HTTPException(
            400,
            f"Erreur envoi Studio : {e}"
        )
