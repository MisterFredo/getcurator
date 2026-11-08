from typing import Optional
from fastapi import APIRouter,HTTPException,Query
from api.contact.models import ContactCreate,ContactUpdate,ContactFollowUpdate
from core.contact import service
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
@router.post('/create')
def create_contact(data:ContactCreate):return call(service.create_contact,data)
@router.get('/{id_contact}/companies')
def contact_companies(id_contact:str):return call(service.company_history,id_contact)
@router.put('/{id_contact}/follow')
def follow_contact(id_contact:str,data:ContactFollowUpdate):return call(service.set_follow,id_contact,data)
@router.put('/{id_contact}')
def update_contact(id_contact:str,data:ContactUpdate):return call(service.update_contact,id_contact,data)
@router.get('/{id_contact}')
def get_contact(id_contact:str):return call(service.get_contact,id_contact)
