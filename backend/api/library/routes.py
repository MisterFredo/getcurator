"""Document library: reading, search, quality control, editorial decisions."""
import logging
from fastapi import APIRouter, HTTPException
from api.library.models import LibraryEditorialDecision, LibraryQualityRequest
from core.library.pdf_library import (
    list_library_documents, get_library_document,
    list_library_topics, get_library_topic,
)
from core.library.pdf_library_search import search_library_topics, search_library_units
from core.library.pdf_quality import save_topic_quality
from core.library.pdf_library_editorial import update_topic_editorial_status

logger = logging.getLogger(__name__)
router = APIRouter()


def _raise_library_error(exc: Exception, context: str):
    if isinstance(exc, LookupError):
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if isinstance(exc, ValueError):
        status = 404 if str(exc) in ('Document introuvable.', 'Sujet introuvable.') else 400
        raise HTTPException(status_code=status, detail=str(exc)) from exc
    logger.exception('Erreur Library: %s', context)
    raise HTTPException(status_code=500, detail=f'Erreur bibliothèque : {context}') from exc


@router.get('/documents')
def documents(limit: int = 100, offset: int = 0):
    try:
        return list_library_documents(limit=limit, offset=offset)
    except Exception as exc:
        _raise_library_error(exc, 'liste des documents')


@router.get('/search/topics')
def search_topics(query: str | None = None, document_id: str | None = None,
                  quality_status: str | None = None, editorial_status: str | None = None,
                  limit: int = 50, offset: int = 0):
    try:
        return search_library_topics(query, document_id, quality_status, editorial_status, limit, offset)
    except Exception as exc:
        _raise_library_error(exc, 'recherche des sujets')


@router.get('/search/units')
def search_units(query: str | None = None, document_id: str | None = None,
                 limit: int = 50, offset: int = 0):
    try:
        return search_library_units(query, document_id, limit, offset)
    except Exception as exc:
        _raise_library_error(exc, 'recherche des informations')


@router.get('/documents/{document_id}')
def document(document_id: str):
    try:
        return get_library_document(document_id)
    except Exception as exc:
        _raise_library_error(exc, 'lecture du document')


@router.get('/documents/{document_id}/topics')
def topics(document_id: str, query: str | None = None, editorial_status: str | None = None,
           limit: int = 100, offset: int = 0):
    try:
        return list_library_topics(document_id=document_id, query=query,
                                   editorial_status=editorial_status, limit=limit, offset=offset)
    except Exception as exc:
        _raise_library_error(exc, 'liste des sujets')


@router.get('/documents/{document_id}/topics/{topic_id}')
def topic(document_id: str, topic_id: str):
    try:
        return get_library_topic(document_id, topic_id)
    except Exception as exc:
        _raise_library_error(exc, 'lecture du sujet')


@router.post('/documents/{document_id}/quality')
def validate_quality(document_id: str, payload: LibraryQualityRequest):
    try:
        return save_topic_quality(document_id, [decision.model_dump() for decision in payload.decisions])
    except Exception as exc:
        _raise_library_error(exc, 'validation qualité')


@router.patch('/documents/{document_id}/topics/{topic_id}/editorial')
def patch_editorial(document_id: str, topic_id: str, payload: LibraryEditorialDecision):
    try:
        return update_topic_editorial_status(document_id, topic_id, payload.editorial_status)
    except Exception as exc:
        _raise_library_error(exc, 'qualification éditoriale')
