import logging
import os
import requests

from fastapi import (
    APIRouter,
    HTTPException,
    Body,
    File,
    UploadFile,
    Form,
)

from api.discovery.models import (
    DiscoveryListOut,
    ScanAllRequest,
    ScanResponse,
    StoreRequest,
    StoreResponse,
    IgnoreRequest,
    IgnoreResponse,
    ManualDiscoveryListOut,
    LinkedInStudioStoreRequest,
    NewsletterStudioStoreRequest,
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

from core.discovery.linkedin_studio import (
    parse_linkedin_activity,
    analyze_linkedin_activity,
    store_linkedin_posts,
)

from core.discovery.newsletter_studio import (
    analyze_newsletter,
    store_newsletter_items,
)


from core.discovery.pdf_studio import (
    MAX_BYTES,
    inspect_pdf,
    map_pdf,
)


from core.discovery.pdf_extract import extract_pdf_batch
from core.discovery.pdf_consolidate import consolidate

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================
# PDF STUDIO — READ UPLOAD
# ============================================================

async def _read_pdf_studio_upload(file: UploadFile) -> bytes:
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Un fichier .pdf est requis")

    data = await file.read(MAX_BYTES + 1)
    await file.close()

    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="PDF supérieur à 30 Mo")

    return data


# ============================================================
# PDF STUDIO — REGISTER ORIGINAL DOCUMENT
# ============================================================

@router.post("/pdf-studio/document/register")
async def register_pdf_studio_document(
    file: UploadFile = File(...),
    source_id: str = Form(...),
    title: str = Form(""),
):
    data = await _read_pdf_studio_upload(file)
    from core.discovery.pdf_document_store import register_pdf
    try:
        return register_pdf(data, file.filename or "document.pdf", source_id, title or None)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        logger.exception("Erreur enregistrement PDF Studio")
        raise HTTPException(status_code=500, detail="Erreur enregistrement du document PDF")


# ============================================================
# PDF STUDIO — IMPORT APPROVED ARTICLES
# ============================================================

@router.post("/pdf-studio/import-approved")
def import_approved_pdf_studio(data: dict = Body(...)):
    from core.discovery.pdf_import import import_approved
    try:
        return import_approved(data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        logger.exception("Erreur import articles PDF Studio")
        raise HTTPException(status_code=500, detail="Erreur import articles PDF Studio")


@router.get("/pdf-studio/article/{id_raw}")
def get_pdf_studio_article(id_raw: str):
    from core.discovery.pdf_import import get_pdf_article
    try:
        return get_pdf_article(id_raw)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception:
        logger.exception("Erreur lecture article PDF Studio")
        raise HTTPException(status_code=500, detail="Erreur lecture article PDF Studio")


# ============================================================
# PDF STUDIO — EXTRACT BATCH (NO PERSISTENCE)
# ============================================================

@router.post("/pdf-studio/extract")
async def extract_pdf_studio(
    file: UploadFile = File(...),
    start_page: int = Form(...),
):
    data = await _read_pdf_studio_upload(file)
    try:
        return extract_pdf_batch(data, start_page)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        logger.exception("Erreur extraction PDF Studio")
        raise HTTPException(status_code=500, detail="Erreur extraction PDF Studio")


# ============================================================
# PDF STUDIO — CONSOLIDATE (JSON EXTRACTION, NO DB WRITE)
# ============================================================

@router.post("/pdf-studio/consolidate")
def consolidate_pdf_studio(data: dict = Body(...)):
    if not isinstance(data.get("units"), list) or not data["units"]:
        raise HTTPException(status_code=400, detail="Extraction JSON sans unités")
    if len(data["units"]) > 5000:
        raise HTTPException(status_code=400, detail="Trop d'unités (max 5000)")
    try:
        return consolidate(data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        logger.exception("Erreur consolidation PDF Studio")
        raise HTTPException(status_code=500, detail="Erreur consolidation PDF Studio")


# ============================================================
# PDF STUDIO — GENERATE DRAFT (NO DB WRITE)
# ============================================================

@router.post("/pdf-studio/generate")
def generate_pdf_studio(data: dict = Body(...)):
    from core.discovery.pdf_generate import generate_article
    try:
        return generate_article(data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        logger.exception("Erreur génération PDF Studio")
        raise HTTPException(status_code=500, detail="Erreur génération PDF Studio")


# ============================================================
# PDF STUDIO — SEGMENT (NO PERSISTENCE)
# ============================================================

@router.post("/pdf-studio/segment")
async def segment_pdf_studio(file: UploadFile = File(...)):
    data = await _read_pdf_studio_upload(file)
    from core.discovery.pdf_segment import segment_pdf
    try:
        return segment_pdf(data, file.filename or "document.pdf")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        logger.exception("Erreur segmentation PDF Studio")
        raise HTTPException(status_code=500, detail="Erreur segmentation PDF Studio")

# ============================================================
# PDF STUDIO — DOCUMENT CANDIDATES (V6)
# ============================================================

@router.post("/pdf-studio/document-candidates")
async def document_candidates_pdf_studio(
    file: UploadFile = File(...),
):
    data = await _read_pdf_studio_upload(file)

    from core.discovery.pdf_segment import (
        build_document_candidates,
    )

    try:
        return build_document_candidates(
            data,
            file.filename or "document.pdf",
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception:
        logger.exception(
            "Erreur création candidats documentaires PDF Studio"
        )
        raise HTTPException(
            status_code=500,
            detail="Erreur création candidats documentaires PDF Studio",
        )


# ============================================================
# PDF STUDIO — INSPECT
# ============================================================

@router.post("/pdf-studio/inspect")
async def inspect_pdf_studio(file: UploadFile = File(...)):
    data = await _read_pdf_studio_upload(file)
    try:
        return {
            "status": "ok",
            **inspect_pdf(data, file.filename or "document.pdf"),
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        logger.exception("Erreur inspection PDF Studio")
        raise HTTPException(status_code=500, detail="Erreur lors de l'inspection du PDF")


# ============================================================
# PDF STUDIO — MAP
# ============================================================

@router.post("/pdf-studio/map")
async def map_pdf_studio(file: UploadFile = File(...)):
    data = await _read_pdf_studio_upload(file)
    try:
        return {
            "status": "ok",
            **map_pdf(data, file.filename or "document.pdf"),
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        logger.exception("Erreur cartographie PDF Studio")
        raise HTTPException(status_code=500, detail="Erreur lors de la cartographie du PDF")


# ============================================================
# LINKEDIN STUDIO — ANALYZE
# ============================================================

@router.post(
    "/linkedin-studio/analyze/{source_id}",
)
def analyze_linkedin_studio(
    source_id: str,
    text: str = Body(
        ...,
        media_type="text/plain",
    ),
):

    try:

        result = (
            analyze_linkedin_activity(
                source_id=source_id,
                text=text,
            )
        )

        return {
            "status": "ok",
            **result,
        }

    except Exception as e:

        logger.exception(
            "Erreur analyse LinkedIn Studio"
        )

        raise HTTPException(
            500,
            (
                "Erreur analyse "
                f"LinkedIn Studio : {e}"
            ),
        )

# ============================================================
# LINKEDIN STUDIO — STORE
# ============================================================

@router.post(
    "/linkedin-studio/store/{source_id}",
)
def store_linkedin_studio(
    source_id: str,
    data: LinkedInStudioStoreRequest,
):

    try:

        posts = [
            post.model_dump()
            for post in data.posts
        ]

        result = (
            store_linkedin_posts(
                source_id=source_id,
                posts=posts,
            )
        )

        return {
            "status": "ok",
            **result,
        }

    except Exception as e:

        logger.exception(
            "Erreur stockage LinkedIn Studio"
        )

        raise HTTPException(
            500,
            (
                "Erreur stockage "
                f"LinkedIn Studio : {e}"
            ),
        )

# ============================================================
# NEWSLETTER STUDIO — ANALYZE
# ============================================================

@router.post(
    "/newsletter-studio/analyze/{source_id}",
)
def analyze_newsletter_studio(
    source_id: str,
    text: str = Body(
        ...,
        media_type="text/plain",
    ),
):

    try:

        result = analyze_newsletter(
            source_id=source_id,
            text=text,
        )

        return {
            "status": "ok",
            **result,
        }

    except Exception as e:

        logger.exception(
            "Erreur analyse Newsletter Studio"
        )

        raise HTTPException(
            500,
            (
                "Erreur analyse "
                f"Newsletter Studio : {e}"
            ),
        )


# ============================================================
# NEWSLETTER STUDIO — STORE
# ============================================================

@router.post(
    "/newsletter-studio/store/{source_id}",
)
def store_newsletter_studio(
    source_id: str,
    data: NewsletterStudioStoreRequest,
):

    try:

        items = [
            item.model_dump()
            for item in data.items
        ]

        result = store_newsletter_items(
            source_id=source_id,
            items=items,
        )

        return {
            "status": "ok",
            **result,
        }

    except Exception as e:

        logger.exception(
            "Erreur stockage Newsletter Studio"
        )

        raise HTTPException(
            500,
            (
                "Erreur stockage "
                f"Newsletter Studio : {e}"
            ),
        )


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
