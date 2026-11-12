from typing import Literal
from fastapi import APIRouter, HTTPException, Request, Query, BackgroundTasks
from typing import Optional

from api.company.models import (
    CompanyCreate,
    CompanyUpdate,
    CompanyOut,
    CompanyWatchCreate,
    CompanyWatchUpdate,
    CompanyWatchOut,
    WatchOperationRequest,
)
from core.company.service import (
    create_company,
    list_companies,
    list_company_types,
    get_company,
    update_company,
    delete_company,
    get_company_aliases,
    create_company_alias,
    delete_company_alias,
)
from core.company.public_service import get_company_view, list_companies_for_user
from core.company.description_service import (
    generate_company_description,
    generate_company_description_preview,
    generate_missing_company_descriptions,
)
from core.company.watch_service import (
    list_company_watch,
    get_company_watch,
    create_company_watch,
    update_company_watch,
)
from utils.auth import get_user_id_from_request
from core.company import watch_operations as watch_ops
from core.company import watch_operations_query as watch_ops_query

router = APIRouter()


# ============================================================
# AUTH HELPER — conservé pour les routes Curator existantes
# ============================================================
def require_user(request: Request) -> str:
    user_id = get_user_id_from_request(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user_id


# ============================================================
# WATCH CORPO
# Même protection globale que les routes de gestion Company.
# Les routes statiques sont placées avant /{id_company}.
# ============================================================
@router.get("/watch/list")
def list_watch_route(
    id_company: Optional[str] = None,
    is_active: Optional[bool] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    return list_company_watch(id_company, is_active, limit, offset)


@router.get("/{id_company}/watch")
def list_company_watch_route(
    id_company: str,
    is_active: Optional[bool] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    return list_company_watch(id_company, is_active, limit, offset)


@router.get("/{id_company}/watch/{id_company_watch}", response_model=CompanyWatchOut)
def get_company_watch_route(id_company: str, id_company_watch: str):
    return get_company_watch(id_company, id_company_watch)


@router.post("/{id_company}/watch", response_model=CompanyWatchOut, status_code=201)
def create_company_watch_route(id_company: str, data: CompanyWatchCreate):
    return create_company_watch(id_company, data)


@router.put("/{id_company}/watch/{id_company_watch}", response_model=CompanyWatchOut)
def update_company_watch_route(
    id_company: str,
    id_company_watch: str,
    data: CompanyWatchUpdate,
):
    return update_company_watch(id_company, id_company_watch, data)



# ============================================================
# WATCH CORPO — COLLECTE ET PUBLICATIONS LIBRARY
# ============================================================
from api.company.models import CompanyWatchCollectRequest, CompanyWatchImportRequest
from core.company.watch_collection_service import active_watch, scan_watch, collect_url, import_text
from core.library.company_watch_library import (
    extract_step, list_publications, publication_detail,
)
import logging

_watch_logger = logging.getLogger(__name__)


def _watch_call(function, *args, **kwargs):
    try:
        return function(*args, **kwargs)
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        _watch_logger.exception("Erreur traitement Corpo")
        raise HTTPException(500, "Erreur traitement Corpo ; consulter les logs et réessayer") from exc


# Eligibility is administered on Company; collection remains under Discovery/Corpo.
from api.company.models import CompanyMentionWatchUpdate, CompanyMentionWatchOut
from core.company.mention_watch_service import (
    get_mention_watch_config, set_mention_watch_config, list_mention_watch_companies,
)

@router.get("/mention-watch/companies")
def eligible_mention_companies_route():
    return {"status":"ok", "companies":_watch_call(list_mention_watch_companies)}

@router.get("/{id_company}/mention-watch", response_model=CompanyMentionWatchOut)
def get_mention_watch_config_route(id_company: str):
    return _watch_call(get_mention_watch_config, id_company)

@router.put("/{id_company}/mention-watch", response_model=CompanyMentionWatchOut)
def update_mention_watch_config_route(id_company: str, data: CompanyMentionWatchUpdate):
    return _watch_call(set_mention_watch_config, id_company, data.is_enabled)


@router.post("/{id_company}/watch/{id_company_watch}/scan")
def scan_watch_route(id_company: str, id_company_watch: str):
    return _watch_call(scan_watch, id_company, id_company_watch)


from core.company.watch_brightdata_service import scan_linkedin, attach_snapshot
from api.company.models import CompanyWatchAttachSnapshot


@router.get("/{id_company}/watch/{id_company_watch}/scan/status")
def watch_scan_status_route(id_company: str, id_company_watch: str):
    return _watch_call(scan_linkedin, id_company, id_company_watch)


@router.post("/{id_company}/watch/{id_company_watch}/scan/attach")
def watch_scan_attach_route(id_company: str, id_company_watch: str, data: CompanyWatchAttachSnapshot):
    return _watch_call(attach_snapshot, id_company, id_company_watch, data.snapshot_id)


@router.post("/{id_company}/watch/{id_company_watch}/collect")
def collect_watch_route(id_company: str, id_company_watch: str, data: CompanyWatchCollectRequest):
    return _watch_call(collect_url, id_company, id_company_watch, data.url)


@router.post("/{id_company}/watch/{id_company_watch}/import-text")
def import_watch_text_route(id_company: str, id_company_watch: str, data: CompanyWatchImportRequest):
    return _watch_call(import_text, id_company, id_company_watch, data)


@router.post("/{id_company}/watch/{id_company_watch}/publications/{id_document}/extract-step")
def extract_watch_step_route(id_company: str, id_company_watch: str, id_document: str):
    raise HTTPException(409, "Le déstockage Corpo est suspendu ; aucune extraction automatique. Actualiser le frontend.")


@router.get("/{id_company}/watch/{id_company_watch}/publications")
def list_watch_publications_route(
    id_company: str, id_company_watch: str,
    offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
):
    get_company_watch(id_company, id_company_watch)
    return _watch_call(list_publications, id_company, id_company_watch, offset, limit)


@router.get("/{id_company}/watch/{id_company_watch}/publications/{id_document}")
def get_watch_publication_route(
    id_company: str, id_company_watch: str, id_document: str,
    offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500),
):
    return _watch_call(publication_detail, id_company, id_company_watch, id_document, offset, limit)



# ============================================================
# CORPO — DÉCOUVERTE ET STOCK DISTINCTS DE LA LIBRARY
# ============================================================
from core.company.watch_discovery_service import (
    list_candidates, store_candidate, candidate_detail, change_candidates_status,
)
from pydantic import BaseModel, Field


class CompanyWatchDiscoverySelection(BaseModel):
    discovery_ids: list[str]

    class Config:
        extra = "forbid"


@router.post("/watch/discovery/dismiss")
def dismiss_watch_discoveries_route(data: CompanyWatchDiscoverySelection):
    return _watch_call(change_candidates_status, data.discovery_ids, "DISMISS")


@router.post("/watch/discovery/restore")
def restore_watch_discoveries_route(data: CompanyWatchDiscoverySelection):
    return _watch_call(change_candidates_status, data.discovery_ids, "RESTORE")


@router.get("/watch/discovery/list")
def list_watch_discoveries_route(
    id_company: Optional[str] = None, id_company_watch: Optional[str] = None,
    status: str = "NEW", offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
):
    return _watch_call(list_candidates, id_company, id_company_watch, status, offset, limit)


@router.post("/watch/discovery/{id_discovery}/store")
def store_watch_discovery_route(id_discovery: str):
    return _watch_call(store_candidate, id_discovery)


@router.get("/watch/discovery/{id_discovery}/content")
def get_watch_stored_content_route(id_discovery: str):
    return _watch_call(candidate_detail, id_discovery)


# ============================================================
# CORPO -> LIBRARY (no RAW, no topics)
# ============================================================
from core.company.watch_library_service import import_step, list_corpo_library, corpo_library_detail


@router.post("/watch/discovery/{id_discovery}/library-step")
def import_corpo_library_step_route(id_discovery: str):
    return _watch_call(import_step, id_discovery)


from api.company.models import MentionRunRequest, MentionRetrySearchRequest, MentionSerpProbeRequest
from core.company import mention_service, mention_jobs
from api.company.models import MentionBatchRequest

def _launch_mentions(background_tasks, function, *args):
    result = _watch_call(function, *args)
    from core.company.mention_worker import drain_queue
    background_tasks.add_task(drain_queue)
    return result


@router.post('/watch/mention-jobs/{id_job}/resume')
def resume_mention_job_route(id_job: str, background_tasks: BackgroundTasks):
    result = _watch_call(mention_jobs.read_job, id_job)
    from core.company.mention_worker import drain_queue
    background_tasks.add_task(drain_queue)
    return result


@router.get('/watch/mention-jobs')
def list_mention_jobs_route():
    return _watch_call(mention_jobs.list_jobs)

@router.post('/watch/mention-jobs/global')
def launch_global_mentions_route(data: MentionBatchRequest, background_tasks: BackgroundTasks):
    return _launch_mentions(background_tasks, mention_jobs.launch_global, data)

@router.post('/watch/mention-jobs/company/{id_company}')
def launch_company_mentions_route(id_company: str, data: MentionBatchRequest, background_tasks: BackgroundTasks):
    return _launch_mentions(background_tasks, mention_jobs.launch_company, id_company, data)

@router.post('/watch/mention-jobs/continue/{id_run}')
def continue_mention_run_route(id_run: str, background_tasks: BackgroundTasks):
    return _launch_mentions(background_tasks, mention_jobs.enqueue_existing, id_run, 'CONTINUE')

@router.get('/watch/mention-jobs/{id_job}')
def get_mention_job_route(id_job: str):
    return _watch_call(mention_jobs.read_job, id_job)

@router.post('/watch/mentions/probe')
def probe_mention_connector(data: MentionSerpProbeRequest):
    return _watch_call(mention_service.probe_connector, data)

@router.post('/watch/mentions/{id_run}/retry-searches')
def retry_mention_searches(id_run: str, data: MentionRetrySearchRequest, background_tasks: BackgroundTasks):
    return _launch_mentions(background_tasks, mention_jobs.enqueue_existing, id_run, 'RETRY_SEARCHES', data.search_workers)

@router.post('/watch/mentions/create')
def create_mention_run(data: MentionRunRequest, background_tasks: BackgroundTasks):
    return _launch_mentions(background_tasks, mention_jobs.launch_company, data.id_company, data)

@router.get('/watch/mentions/{id_run}')
def get_mention_run(id_run: str):
    return _watch_call(mention_service.read, id_run)

@router.post('/watch/mentions/{id_run}/recheck')
def recheck_mention_run(id_run: str, background_tasks: BackgroundTasks):
    return _launch_mentions(background_tasks, mention_jobs.enqueue_existing, id_run, 'RECHECK')


@router.post('/watch/mentions/{id_run}/step')
def step_mention_run(id_run: str):
    return _watch_call(mention_jobs.reject_browser_step, id_run)


from api.company.models import CompanyLibraryEditorialUpdate
from core.company.library_editorial_service import set_mention_editorial

@router.post('/watch/library/{id_document}/editorial')
def set_library_editorial_route(id_document:str,data:CompanyLibraryEditorialUpdate):
    return _watch_call(set_mention_editorial,id_document,data.is_withdrawn,data.reason)

class CompanyPostReview(BaseModel):
    verdict: str
    post_type: str
    reason: Optional[str] = Field(None, max_length=1000)


@router.post("/watch/library/{id_document}/review")
def save_library_post_review(id_document: str, data: CompanyPostReview):
    from core.company.library_post_review import save_review

    return _watch_call(save_review, id_document, data.verdict, data.post_type, data.reason)


class CompanyPostReviewConfirmation(BaseModel):
    document_ids: list[str]
    pending_verdict: Optional[str] = None


@router.post("/watch/library/reviews/confirm")
def confirm_library_post_reviews(data: CompanyPostReviewConfirmation):
    from core.company.library_post_review import confirm_reviews

    return _watch_call(confirm_reviews, data.document_ids, data.pending_verdict)


@router.get("/watch/library/list")
def list_corpo_library_route(
    id_company: Optional[str] = None,
    offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
    q: Optional[str] = Query(None, max_length=500),
    sort: str = "published_at", direction: str = "desc", status: Optional[str] = None,
    published_from: Optional[str] = None, published_to: Optional[str] = None,
    document_type: Optional[str] = None,
    editorial_status: str = "ACTIVE",
    with_summary: bool = False,
    qualification: Optional[str] = None,
    post_type: Optional[str] = None,
    review_state: Optional[str] = None,
    origin: Optional[str] = None,
    media_format: Optional[str] = None,
):
    return _watch_call(list_corpo_library, id_company, offset, limit,
        q, sort, direction, status, published_from, published_to, document_type,
        editorial_status, with_summary, qualification, post_type, review_state, origin=origin, media_format=media_format)


class CompanyReportCorpusUpdate(BaseModel):
    company_id: str
    month: str
    selected_ids: list[str]
    revision: str


@router.get("/watch/library/report-corpus")
def company_report_corpus_route(company_id: str, month: str):
    from core.company.company_report_corpus import get_corpus

    return _watch_call(get_corpus, company_id, month)


@router.put("/watch/library/report-corpus")
def save_company_report_corpus_route(data: CompanyReportCorpusUpdate):
    from core.company.company_report_corpus import save_corpus

    return _watch_call(save_corpus, data.company_id, data.month, data.selected_ids, data.revision)


class CompanyReportNotebookRequest(BaseModel):
    company_id: str
    month: str
    revision: str


@router.get("/watch/library/report-notebook")
def company_report_notebook_route(company_id: str, month: str, revision: str):
    from core.company.company_report_notebook import get_notebook

    return _watch_call(get_notebook, company_id, month, revision)


@router.post("/watch/library/report-notebook")
def generate_company_report_notebook_route(data: CompanyReportNotebookRequest):
    from core.company.company_report_notebook import generate_notebook

    return _watch_call(generate_notebook, data.company_id, data.month, data.revision)


class CompanyReportRequest(CompanyReportNotebookRequest):
    language: Literal["fr", "en"] = "fr"


@router.get("/watch/library/company-report")
def company_report_route(company_id: str, month: str, revision: str, language: Literal["fr", "en"] = "fr"):
    from core.company.company_report import get_report

    return _watch_call(get_report, company_id, month, revision, language)


@router.post("/watch/library/company-report")
def generate_company_report_route(data: CompanyReportRequest):
    from core.company.company_report import generate_report

    return _watch_call(generate_report, data.company_id, data.month, data.revision, data.language)


@router.get("/watch/library/{id_document}")
def corpo_library_detail_route(
    id_document: str, offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500),
):
    return _watch_call(corpo_library_detail, id_document, offset, limit)


# ============================================================
# VEILLE — COLLECTES, REPRISE ET DIAGNOSTICS
# ============================================================
@router.post('/watch/operations/start')
def start_watch_operation(data: WatchOperationRequest, background_tasks: BackgroundTasks, role: str = "ALL"):
    result = _watch_call(watch_ops.launch, **data.dict(), role=role)
    background_tasks.add_task(watch_ops.drain)
    return result

@router.get('/watch/operations/jobs')
def watch_operations_list(company_id: Optional[str] = None, watch_id: Optional[str] = None, role: str = "ALL"):
    return _watch_call(watch_ops.list_jobs, company_id, watch_id, role=role)

@router.get('/watch/operations/jobs/{job_id}')
def watch_operations_get(job_id: str):
    return _watch_call(watch_ops.get_job, job_id)

@router.post('/watch/operations/jobs/{job_id}/resume')
def watch_operations_resume(job_id: str, background_tasks: BackgroundTasks):
    result = _watch_call(watch_ops.resume, job_id)
    if result['status'] == 'RUNNING': background_tasks.add_task(watch_ops.drain)
    return result

@router.post('/watch/operations/jobs/{job_id}/pause')
def watch_operations_pause(job_id: str):
    return _watch_call(watch_ops.pause, job_id)

@router.get('/watch/operations/companies')
def watch_operations_companies():
    return _watch_call(watch_ops_query.list_active_companies)


@router.get('/watch/operations/sources')
def watch_operations_sources(company_id: Optional[str] = None, is_active: Optional[bool] = None,
    channel: str = 'ALL', kind: str = 'ALL', offset: int = 0, limit: int = 50, role: str = 'ALL'):
    return _watch_call(watch_ops_query.list_sources, company_id, is_active, channel, kind, offset, limit, role)

@router.get('/watch/operations/items')
def watch_operations_items(company_id: Optional[str] = None, watch_id: Optional[str] = None,
    status: str = 'NEW', channel: str = 'ALL', kind: str = 'ALL', offset: int = 0, limit: int = 50, role: str = 'ALL'):
    if offset < 0 or not 1 <= limit <= 200:
        raise HTTPException(400, 'Pagination invalide')
    return _watch_call(watch_ops_query.list_items, company_id, watch_id, status, channel, kind, offset, limit, role)


# ============================================================
# CREATE
# ============================================================
@router.post("/create")
def create_route(data: CompanyCreate):
    try:
        company_id = create_company(data)
        return {"status": "ok", "id_company": company_id}
    except Exception as e:
        raise HTTPException(400, f"Erreur création société : {e}")


@router.post("/suggest-alias")
def suggest_alias_route(data: dict):
    name = data.get("name")
    if not name:
        raise HTTPException(400, "name required")
    aliases = suggest_company_aliases(name)
    return {"status": "ok", "aliases": aliases}


# ============================================================
# LIST
# ============================================================
@router.get("/list")
def list_route():
    try:
        companies = list_companies()
        return {"status": "ok", "companies": companies}
    except Exception as e:
        raise HTTPException(400, f"Erreur liste sociétés : {e}")


# ============================================================
# TYPES
# ============================================================
@router.get("/types")
def list_types_route():
    try:
        types = list_company_types()
        return {"status": "ok", "types": types}
    except Exception as e:
        raise HTTPException(400, f"Erreur récupération types sociétés : {e}")


# ============================================================
# USER COMPANIES
# ============================================================
@router.get("/list-curator")
def list_companies_curator(request: Request):
    try:
        user_id = require_user(request)
        companies = list_companies_for_user(user_id)
        return {"status": "ok", "companies": companies}
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Companies curator error: {e}")
        raise HTTPException(status_code=500, detail="Internal error")


# ============================================================
# ALIASES
# ============================================================
@router.get("/{id_company}/aliases")
def get_aliases_route(id_company: str):
    try:
        aliases = get_company_aliases(id_company=id_company)
        return {"status": "ok", "aliases": aliases}
    except Exception as e:
        raise HTTPException(400, f"Erreur récupération aliases : {e}")


@router.post("/{id_company}/alias")
def create_alias_route(id_company: str, data: dict):
    try:
        alias = (data.get("alias") or "").strip()
        if not alias:
            raise HTTPException(400, "alias required")
        create_company_alias(id_company=id_company, alias=alias)
        return {"status": "ok", "alias": alias}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, f"Erreur création alias : {e}")


@router.delete("/{id_company}/alias")
def delete_alias_route(id_company: str, alias: str):
    try:
        delete_company_alias(id_company=id_company, alias=alias)
        return {"status": "ok", "deleted": True}
    except Exception as e:
        raise HTTPException(400, f"Erreur suppression alias : {e}")


# ============================================================
# VIEW (CURATOR)
# ============================================================
@router.get("/{id_company}/view")
def get_view_route(request: Request, id_company: str):
    try:
        require_user(request)
        company = get_company_view(company_id=id_company)
        if not company:
            raise HTTPException(404, "Company introuvable")
        return company
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Company view error: {e}")
        raise HTTPException(status_code=500, detail="Internal error")


# ============================================================
# DESCRIPTION GENERATION
# ============================================================
@router.post("/{id_company}/generate-description")
def generate_description_route(id_company: str):
    try:
        result = generate_company_description(company_id=id_company)
        return {"status": "ok", "result": result}
    except Exception as e:
        raise HTTPException(400, f"Erreur génération description : {e}")


@router.post("/generate-missing-descriptions")
def generate_missing_descriptions_route(limit: int = 20):
    try:
        result = generate_missing_company_descriptions(limit=limit)
        return {"status": "ok", "result": result}
    except Exception as e:
        raise HTTPException(400, f"Erreur génération descriptions : {e}")


@router.post("/generate-description")
def generate_description_preview_route(data: dict):
    name = (data.get("name") or "").strip()
    if not name:
        raise HTTPException(400, "name required")
    description = generate_company_description_preview(company_name=name)
    return {"status": "ok", "description": description}


# ============================================================
# UPDATE
# ============================================================
@router.put("/update/{id_company}")
def update_route(id_company: str, data: CompanyUpdate):
    try:
        updated = update_company(id_company, data)
        if not updated:
            raise HTTPException(404, "Société introuvable ou aucune modification")
        return {"status": "ok", "updated": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, f"Erreur mise à jour société : {e}")


# ============================================================
# DELETE
# ============================================================
@router.delete("/{id_company}")
def delete_route(id_company: str):
    try:
        deleted = delete_company(id_company)
        if not deleted:
            raise HTTPException(404, "Société introuvable")
        return {"status": "ok", "deleted": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, f"Erreur suppression société : {e}")

# ============================================================
# GET ONE — conserver en dernier
# ============================================================
@router.get("/{id_company}", response_model=CompanyOut)
def get_route(id_company: str):
    company = get_company(id_company)
    if not company:
        raise HTTPException(404, "Société introuvable")
    return company
