from typing import Optional
from fastapi import APIRouter,BackgroundTasks,HTTPException,Query
from api.contact.models import ContactCreate,ContactUpdate,ContactFollowUpdate,LinkedInContactImportRequest,LinkedInChangesRequest,LinkedInCompanyDecision,LinkedInCompanyMappingsRequest
from core.contact import service
from core.contact import linkedin_import
from core.contact import linkedin_changes
from core.contact import linkedin_company_rules
from core.contact.company_counts import get_company_contact_counts
import logging
router=APIRouter()
log=logging.getLogger(__name__)
def call(function,*args,**kwargs):
    try:return function(*args,**kwargs)
    except HTTPException:raise
    except Exception as exc:
        log.exception('Contact operation failed')
        raise HTTPException(500,'Opération Contacts impossible ; consulter les logs') from exc

@router.get('/list')
def list_contacts(id_company:Optional[str]=None,q:Optional[str]=Query(None,max_length=300),offset:int=Query(0,ge=0),limit:int=Query(50,ge=1,le=200)):
    return call(service.list_contacts,id_company,q,offset,limit)
@router.get('/company-counts')
def company_contact_counts():return call(get_company_contact_counts)

@router.post('/create')
def create_contact(data:ContactCreate):return call(service.create_contact,data)
# Static paths before the generic contact ID route.
@router.post('/linkedin/preview')
def start_linkedin_preview(tasks:BackgroundTasks):
    result=call(linkedin_import.start)
    if result['queued']:tasks.add_task(linkedin_import.collect,result['id_run'])
    return result

@router.get('/linkedin/preview/{run_id}')
def get_linkedin_preview(run_id:str):return call(linkedin_import.preview,run_id)

@router.put('/linkedin/preview/{run_id}/company-mappings')
def validate_linkedin_company_mappings(run_id:str,payload:LinkedInCompanyMappingsRequest):return call(linkedin_company_rules.match_batch,run_id,payload)

@router.put('/linkedin/preview/{run_id}/company-decision')
def decide_linkedin_company(run_id:str,payload:LinkedInCompanyDecision):return call(linkedin_company_rules.decide,run_id,payload)

@router.post('/linkedin/preview/{run_id}/changes')
def start_linkedin_changes(run_id:str,payload:LinkedInChangesRequest,tasks:BackgroundTasks):
    result=call(linkedin_changes.reserve,run_id,payload)
    if result['queued']:tasks.add_task(linkedin_changes.apply,run_id)
    return result

@router.post('/linkedin/preview/{run_id}/changes/resume')
def resume_linkedin_changes(run_id:str,tasks:BackgroundTasks):
    result=call(linkedin_changes.resume,run_id)
    if result['queued']:tasks.add_task(linkedin_changes.apply,run_id)
    return result

@router.post('/linkedin/preview/{run_id}/continue')
def continue_linkedin_preview(run_id:str):return call(linkedin_import.continue_preview,run_id)

@router.post('/linkedin/preview/{run_id}/resume')
def resume_linkedin_preview(run_id:str,tasks:BackgroundTasks):
    result=call(linkedin_import.resume,run_id)
    if result['queued']:
        tasks.add_task(linkedin_import.import_selected if result.get('phase')=='IMPORT' else linkedin_import.collect,result['id_run'])
    return result

@router.post('/linkedin/preview/{run_id}/import')
def import_linkedin_preview(run_id:str,payload:LinkedInContactImportRequest,tasks:BackgroundTasks):
    result=call(linkedin_import.commit,run_id,payload.selections)
    if result.get('queued'):tasks.add_task(linkedin_import.import_selected,run_id)
    return result

# CSV staging is separate from the LinkedIn network snapshot.
from api.contact.models import CsvContactPreviewRequest,CsvContactCommitRequest
from core.contact import csv_import

@router.post('/csv/preview')
def csv_preview(payload:CsvContactPreviewRequest):return call(csv_import.preview,payload.csv_text)

@router.get('/csv/imports/{run_id}')
def csv_status(run_id:str):return call(csv_import.status,run_id)

@router.post('/csv/imports/{run_id}/commit')
def csv_commit(run_id:str,payload:CsvContactCommitRequest,tasks:BackgroundTasks):
    result=call(csv_import.reserve,run_id,payload.selections)
    if result['queued']:tasks.add_task(csv_import.apply,run_id)
    return result

@router.post('/csv/imports/{run_id}/resume')
def csv_resume(run_id:str,tasks:BackgroundTasks):
    result=call(csv_import.resume,run_id)
    if result['queued']:tasks.add_task(csv_import.apply,run_id)
    return result

@router.get('/{id_contact}/companies')
def contact_companies(id_contact:str):return call(service.company_history,id_contact)
@router.put('/{id_contact}/follow')
def follow_contact(id_contact:str,data:ContactFollowUpdate):return call(service.set_follow,id_contact,data)
@router.put('/{id_contact}')
def update_contact(id_contact:str,data:ContactUpdate):return call(service.update_contact,id_contact,data)
@router.get('/{id_contact}')
def get_contact(id_contact:str):return call(service.get_contact,id_contact)
