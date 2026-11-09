from datetime import datetime
from typing import Optional,List,Literal
from urllib.parse import urlsplit,unquote,urlunsplit
import re
from pydantic import BaseModel,Field,StrictBool,validator,root_validator


def linkedin_profile(value):
    if value is None or isinstance(value,str) and not value.strip():return None
    if not isinstance(value,str):raise ValueError('URL LinkedIn attendue')
    parts=urlsplit(value.strip())
    host=(parts.hostname or '').lower()
    if parts.scheme.lower() not in {'http','https'} or not (host=='linkedin.com' or host.endswith('.linkedin.com')):
        raise ValueError('URL de profil LinkedIn requise : https://www.linkedin.com/in/…')
    if parts.username or parts.password or parts.port not in (None,80,443):raise ValueError('URL LinkedIn invalide')
    path=parts.path.rstrip('/')
    if not re.fullmatch(r'/in/[^/\s?#\\]+',unquote(path)):raise ValueError('Un profil personnel LinkedIn /in/ est requis')
    return urlunsplit(('https','www.linkedin.com',path.casefold(),'',''))

def sales_navigator_profile(value):
    if value is None or isinstance(value,str) and not value.strip():return None
    if not isinstance(value,str):raise ValueError('URL Sales Navigator attendue')
    parts=urlsplit(value.strip())
    if parts.scheme.lower() not in {'http','https'} or (parts.hostname or '').lower() not in {'linkedin.com','www.linkedin.com'} or parts.username or parts.password or parts.port not in (None,80,443):
        raise ValueError('URL Sales Navigator invalide')
    match=re.fullmatch(r'/sales/lead/([A-Za-z0-9_-]+)(?:,[^/?#]*)?/?',parts.path)
    if not match:raise ValueError('Un lien Sales Navigator /sales/lead/ est requis')
    return 'https://www.linkedin.com/sales/lead/'+match.group(1)

class ContactBase(BaseModel):
    @validator('sales_navigator_url',check_fields=False,pre=True)
    def sales_clean(cls,value):return sales_navigator_profile(value)
    @validator('first_name','last_name','job_title',check_fields=False,pre=True)
    def trim(cls,value):return value.strip() if isinstance(value,str) else value
    @validator('id_company',check_fields=False,pre=True)
    def company_trim(cls,value):return value.strip() or None if isinstance(value,str) else value
    @validator('email',check_fields=False,pre=True)
    def email_clean(cls,value):
        if value is None or isinstance(value,str) and not value.strip():return None
        if not isinstance(value,str) or not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+',value.strip()):raise ValueError('E-mail professionnel invalide')
        return value.strip().casefold()
    @validator('linkedin_url',check_fields=False,pre=True)
    def linkedin_clean(cls,value):return linkedin_profile(value)
    class Config:extra='forbid'

class ContactCreate(ContactBase):
    first_name:str=Field(default='',max_length=150)
    last_name:str=Field(min_length=1,max_length=150)
    email:Optional[str]=Field(default=None,max_length=320)
    linkedin_url:Optional[str]=Field(default=None,max_length=4096)
    sales_navigator_url:Optional[str]=Field(default=None,max_length=4096)
    id_company:Optional[str]=Field(default=None,max_length=100)
    job_title:Optional[str]=Field(default=None,max_length=250)
    is_active:StrictBool=True
    linkedin_follow_enabled:StrictBool=False
    @root_validator(skip_on_failure=True)
    def follow_requirements(cls,values):
        if values.get('linkedin_follow_enabled') and not (values.get('linkedin_url') and values.get('id_company') and values.get('is_active')):
            raise ValueError('Le suivi nécessite un contact actif, une société et une URL LinkedIn')
        return values

class ContactUpdate(ContactBase):
    first_name:Optional[str]=Field(default=None,max_length=150)
    last_name:Optional[str]=Field(default=None,min_length=1,max_length=150)
    email:Optional[str]=Field(default=None,max_length=320)
    linkedin_url:Optional[str]=Field(default=None,max_length=4096)
    sales_navigator_url:Optional[str]=Field(default=None,max_length=4096)
    id_company:Optional[str]=Field(default=None,max_length=100)
    job_title:Optional[str]=Field(default=None,max_length=250)
    is_active:Optional[StrictBool]=None
    linkedin_follow_enabled:Optional[StrictBool]=None
    expected_updated_at:Optional[datetime]=None
    @root_validator(pre=True)
    def no_null_required(cls,values):
        for key in ['first_name','last_name','is_active','linkedin_follow_enabled']:
            if key in values and values[key] is None:raise ValueError(f'{key} ne peut pas être null')
        return values

class ContactFollowUpdate(BaseModel):
    is_enabled:StrictBool
    expected_company_id:Optional[str]=Field(default=None,max_length=100)
    expected_updated_at:Optional[datetime]=None
    class Config:extra='forbid'


class LinkedInContactSelection(BaseModel):
    group_key:str=Field(min_length=64,max_length=64)
    id_company:str=Field(min_length=1,max_length=100)
    contact_keys:List[str]=Field(min_items=1,max_items=30000)
    class Config:extra='forbid'

class LinkedInContactImportRequest(BaseModel):
    selections:List[LinkedInContactSelection]=Field(min_items=1,max_items=10000)
    class Config:extra='forbid'


class LinkedInChangeApproval(BaseModel):
    contact_key:str=Field(min_length=64,max_length=64)
    id_contact:str=Field(min_length=1,max_length=100)
    id_company:str=Field(min_length=1,max_length=100)
    expected_updated_at:datetime
    fields:List[Literal['company','job_title','email']]=Field(min_items=1,max_items=3)
    continue_follow:StrictBool=False
    class Config:extra='forbid'

class LinkedInChangesRequest(BaseModel):
    request_id:str=Field(min_length=36,max_length=36)
    approvals:List[LinkedInChangeApproval]=Field(min_items=1,max_items=1000)
    @validator('request_id')
    def valid_request_id(cls,value):
        import uuid
        return str(uuid.UUID(value))
    class Config:extra='forbid'


class LinkedInCompanyDecision(BaseModel):
    group_keys:List[str]=Field(min_items=1,max_items=500)
    decision:Literal['MATCH','IGNORE','LATER','RESET']
    id_company:Optional[str]=Field(default=None,max_length=100)
    @validator('group_keys')
    def valid_group_keys(cls,value):
        if any(not re.fullmatch(r'[0-9a-f]{64}',v) for v in value):raise ValueError('Identifiant société invalide')
        return value
    @root_validator(skip_on_failure=True)
    def target_company(cls,values):
        if values.get('decision')=='MATCH' and not values.get('id_company'):raise ValueError('Société GetCurator obligatoire')
        if values.get('decision')!='MATCH' and values.get('id_company') is not None:raise ValueError('Société cible réservée au rapprochement')
        return values
    class Config:extra='forbid'


class LinkedInCompanyMapping(BaseModel):
    group_key:str=Field(min_length=64,max_length=64)
    id_company:str=Field(min_length=1,max_length=100)
    @validator('group_key')
    def valid_mapping_key(cls,value):
        if not re.fullmatch(r'[0-9a-f]{64}',value):raise ValueError('Identifiant société invalide')
        return value
    class Config:extra='forbid'

class LinkedInCompanyMappingsRequest(BaseModel):
    mappings:List[LinkedInCompanyMapping]=Field(min_items=1,max_items=500)
    class Config:extra='forbid'


class CsvContactPreviewRequest(BaseModel):
    csv_text:str=Field(min_length=1,max_length=3000000)
    class Config:extra='forbid'

class CsvContactChoice(BaseModel):
    line:int=Field(ge=2,le=2001)
    id_company:str=Field(min_length=1,max_length=100)
    class Config:extra='forbid'

class CsvContactCommitRequest(BaseModel):
    selections:List[CsvContactChoice]=Field(min_items=1,max_items=2000)
    class Config:extra='forbid'


class EmployerCheckRequest(BaseModel):
    include_network:StrictBool=False
    class Config:extra='forbid'

class EmployerCheckResumeRequest(BaseModel):
    snapshot_id:Optional[str]=Field(default=None,min_length=4,max_length=150)
    class Config:extra='forbid'
