from fastapi import APIRouter, BackgroundTasks, HTTPException
from core.cockpit.monitoring import get_monitoring
from core.cockpit.operations import (
    publish_all_drafts, rebuild_content_company, rebuild_content_solution,
    populate_content_enriched, matching_full_dismiss, backup_prod, sync_prod_to_dev,
    continue_all_knowledge, restart_destock, backfill_topics,
)
from core.cockpit.quality import get_unmatched_companies, get_unmatched_solutions, get_numbers_structure
from core.cockpit.duplicates import get_duplicate_urls, delete_duplicate_url, delete_duplicate_urls
from core.company.description_service import generate_missing_company_descriptions
from core.translation.content_translation_service import translate_contents_batch
from core.translation.backfill_service import reserve_translation_backfill, run_translation_backfill, get_translation_backfill_status
from pydantic import BaseModel, Field
from typing import Literal, List
router=APIRouter()

@router.get('/monitoring')
def monitoring():return {'status':'ok','monitoring':get_monitoring()}
@router.post('/operations/publish-drafts')
def publish_drafts():return publish_all_drafts()
@router.post('/operations/translate-missing')
def translate_missing():
    try:
        result=translate_contents_batch(target_lang='fr',fields=None,limit=9999,only_missing=True,content_ids=None,source_id=None)
        return {'status':'ok','message':'Missing translations completed.','result':result}
    except Exception as e:raise HTTPException(400,f'Erreur batch traduction : {e}')

def _translation(background_tasks,message):
    if not reserve_translation_backfill():raise HTTPException(409,'Le backlog de traduction est déjà en cours.')
    background_tasks.add_task(run_translation_backfill)
    return {'status':'ok','message':message}
@router.post('/operations/translation-backfill/start')
def start_translation_backfill(background_tasks:BackgroundTasks):return _translation(background_tasks,'Translation backlog started.')
@router.post('/operations/translation-backfill/retry')
def retry_translation_backfill(background_tasks:BackgroundTasks):return _translation(background_tasks,'Translation backlog resumed.')
@router.get('/operations/translation-backfill/status')
def translation_backfill_status():return {'status':'ok','backfill':get_translation_backfill_status()}
@router.post('/operations/rebuild-company')
def rebuild_company():return rebuild_content_company()
@router.post('/operations/rebuild-solution')
def rebuild_solution():return rebuild_content_solution()
@router.post('/operations/populate-content-enriched')
def populate():return populate_content_enriched()
@router.post('/operations/matching-dismiss')
def matching_dismiss():return matching_full_dismiss()
@router.post('/operations/restart-destock')
def restart():return restart_destock()
# Legacy endpoints retained; their shortcuts are removed from the Cockpit.
@router.post('/operations/backfill-topics')
def run_topics_backfill(background_tasks:BackgroundTasks):
    background_tasks.add_task(backfill_topics,5000)
    return {'status':'started','message':'Topics backfill started.'}
@router.post('/operations/generate-company-descriptions')
def generate_company_descriptions():
    result=generate_missing_company_descriptions(limit=100)
    return {'status':'ok','message':f'{result["generated"]} company descriptions generated · {result["failed"]} failed','result':result}
@router.post('/operations/backup')
def backup():return backup_prod()
@router.post('/operations/sync-dev')
def sync_dev():return sync_prod_to_dev()
@router.post('/operations/continue-knowledge')
def continue_knowledge():return continue_all_knowledge()

class DuplicateBatchRequest(BaseModel):
    content_ids:List[str]=Field(min_items=1,max_items=10000)
    class Config:extra='forbid'

@router.post('/quality/duplicate-urls/delete-batch')
def delete_duplicate_batch(data:DuplicateBatchRequest):
    return delete_duplicate_urls(data.content_ids)

@router.get('/quality/duplicate-urls')
@router.get('/quality/duplicate-titles')
def duplicate_titles():return {'status':'ok','results':get_duplicate_urls()}
@router.delete('/quality/duplicate-urls/{content_id}')
@router.delete('/quality/duplicate-titles/{content_id}')
def delete_duplicate_title(content_id:str):return delete_duplicate_url(content_id)
@router.get('/quality/unmatched-companies')
def unmatched_companies():return {'status':'ok','results':get_unmatched_companies()}
@router.get('/quality/unmatched-solutions')
def unmatched_solutions():return {'status':'ok','results':get_unmatched_solutions()}
@router.get('/quality/numbers-structure')
def numbers_structure():return {'status':'ok','results':get_numbers_structure()}

class MediaRequest(BaseModel):
    scope:Literal['ALL','WEB','LINKEDIN']='ALL'
    class Config:extra='forbid'

@router.post('/discovery/media/start')
def start_media(data:MediaRequest,background_tasks:BackgroundTasks):
    from core.cockpit import media_jobs
    result=media_jobs.launch(data.scope)
    background_tasks.add_task(media_jobs.drain)
    return result
@router.get('/discovery/media/jobs')
def media_jobs_list():
    from core.cockpit import media_jobs
    return media_jobs.list_jobs()
@router.get('/discovery/media/jobs/{id_job}')
def media_job_detail(id_job:str):
    from core.cockpit import media_jobs
    return media_jobs.get_job(id_job)
@router.post('/discovery/media/jobs/{id_job}/resume')
def resume_media(id_job:str,background_tasks:BackgroundTasks):
    from core.cockpit import media_jobs
    result=media_jobs.get_job(id_job)
    if result['status'] not in {'COMPLETE','PARTIAL'}:background_tasks.add_task(media_jobs.drain)
    return result
# Corpo uses the existing company launch endpoint and persisted mention-job UI.


@router.get("/operations/library-post-backlog/status")
def library_post_backlog_status():
    from core.company import library_post_backlog

    return library_post_backlog.status()


@router.post("/operations/library-post-backlog/start")
def start_library_post_backlog(background_tasks: BackgroundTasks):
    from core.company import library_post_backlog

    job = library_post_backlog.launch()
    background_tasks.add_task(library_post_backlog.run, job["id_job"])
    return job
