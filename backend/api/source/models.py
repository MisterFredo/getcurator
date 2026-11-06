from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, Field

AcquisitionMode=Literal['MANUAL','PDF_MANUAL','LINKEDIN_PROFILE','LINKEDIN_BRIGHTDATA',
    'NEWSLETTER_MANUAL','HTML','RSS','SITEMAP','WORDPRESS_API','API']

class SourceCreate(BaseModel):
    name: str = Field(...,min_length=1)
    type_source: Optional[str] = None
    description: Optional[str] = None
    domain: Optional[str] = None
    author: Optional[str] = None
    author_profile: Optional[str] = None
    logo: Optional[str] = None
    universe_id: Optional[str] = None
    acquisition_mode: AcquisitionMode = 'MANUAL'
    class Config:
        extra='forbid'

class SourceUpdate(BaseModel):
    name: Optional[str] = None
    type_source: Optional[str] = None
    description: Optional[str] = None
    domain: Optional[str] = None
    author: Optional[str] = None
    author_profile: Optional[str] = None
    logo: Optional[str] = None
    universe_id: Optional[str] = None
    acquisition_mode: Optional[AcquisitionMode] = None
    class Config:
        extra='forbid'

class SourceOut(BaseModel):
    source_id: str
    name: str
    type_source: Optional[str] = None
    description: Optional[str] = None
    domain: Optional[str] = None
    author: Optional[str] = None
    author_profile: Optional[str] = None
    logo: Optional[str] = None
    created_at: Optional[datetime] = None
    universe_id: Optional[str] = None
    acquisition_mode: Optional[AcquisitionMode] = None
    class Config:
        extra='forbid'

class SourceListOut(BaseModel):
    status: str
    sources: List[SourceOut]
    class Config:
        extra='forbid'
