"""Simple Google News requests with bounded, redacted response diagnostics."""
import json
import logging
import os
import re
from time import perf_counter
from urllib.parse import urlencode
import requests

logger=logging.getLogger(__name__)

class SerpFailure(RuntimeError):
    def __init__(self,reason,details):
        super().__init__(reason);self.details=details


def _excerpt(value,token):
    text=value if isinstance(value,str) else ''
    if token:text=text.replace(token,'[secret]')
    text=re.sub(r'(?i)Bearer\s+[^\s"<>]+','Bearer [secret]',text)
    text=re.sub(r'(?i)(["\']?(?:api[_-]?key|authorization|password|cookie|token|access_token)["\']?\s*[:=]\s*)(?:"[^"]*"|\'[^\']*\'|[^\s,;<]+)',r'\1[secret]',text)
    text=re.sub(r'https?://[^\s"<>]+','[url]',text)
    return re.sub(r'\s+',' ',text)[:240]


def search(term,precision,mode,country,language,start_date,end_date,offset,domains):
    if mode!='NEWS':raise ValueError('Seul Google News est autorisé pour les mentions externes')
    token=os.getenv('BRIGHTDATA_API_KEY','').strip();zone=os.getenv('BRIGHTDATA_SERP_ZONE','').strip()
    if not token or not zone:raise ValueError('BRIGHTDATA_API_KEY et BRIGHTDATA_SERP_ZONE doivent être configurées dans le backend')
    q=term.strip()
    if not q:raise ValueError('Nom de société manquant')
    params={'q':q,'gl':country,'hl':language,'brd_json':'1','start':offset,'tbm':'nws'}
    url='https://www.google.com/search?'+urlencode(params)
    started=perf_counter();response=None
    def fail(reason,*,body=None,stage='transport'):
        text=body if isinstance(body,str) else getattr(response,'text','')
        text=text if isinstance(text,str) else ''
        headers=getattr(response,'headers',{}) or {}
        mime=headers.get('Content-Type','')
        diagnostics={'stage':stage,'http_status':getattr(response,'status_code',None),
            'content_type':str(mime)[:100] if isinstance(mime,str) else '',
            'body_bytes':len(text.encode('utf-8',errors='replace')),
            'elapsed_seconds':round(perf_counter()-started,3),'response_excerpt':_excerpt(text,token)}
        logger.warning('[MENTIONS] SERP failure reason=%s locale=%s/%s offset=%s diagnostics=%s',
            reason,country,language,offset,json.dumps(diagnostics,ensure_ascii=False))
        raise SerpFailure(reason,diagnostics) from None
    try:
        response=requests.post('https://api.brightdata.com/request',
            headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'},
            json={'zone':zone,'url':url,'format':'raw','data_format':'parsed'},timeout=(10,60),allow_redirects=False)
    except requests.ConnectTimeout:fail('SERP_CONNECT_TIMEOUT')
    except requests.ReadTimeout:fail('SERP_READ_TIMEOUT')
    except requests.exceptions.SSLError:fail('SERP_SSL_ERROR')
    except requests.RequestException:fail('SERP_CONNECTION_ERROR')
    if response.status_code!=200:fail(f'SERP_HTTP_{response.status_code}')
    try:result=response.json()
    except ValueError:fail('SERP_INVALID_JSON',stage='response_json')
    # Accept a JSON-encoded object or a documented body envelope, but never
    # interpret HTML/error pages as an empty successful search.
    for _ in range(3):
        if isinstance(result,str):
            try:result=json.loads(result.lstrip('\ufeff'))
            except ValueError:fail('SERP_INVALID_JSON',body=result,stage='encoded_json')
        elif isinstance(result,dict) and 'body' in result:
            result=result['body']
        else:break
    if not isinstance(result,dict):fail('SERP_INVALID_JSON',stage='object_shape')
    general=result.get('general') or {}
    if not isinstance(general,dict):fail('SERP_INVALID_GENERAL',stage='schema')
    if general.get('search_type') and general['search_type']!='news':fail('SERP_WRONG_MODE',stage='schema')
    rows=result.get('news')
    if rows is None and general.get('empty') is not True:fail('SERP_MISSING_RESULTS',stage='schema')
    if rows is not None and not isinstance(rows,list):fail('SERP_INVALID_RESULTS',stage='schema')
    pagination=result.get('pagination') or {}
    if not isinstance(pagination,dict):fail('SERP_INVALID_PAGINATION',stage='schema')
    return result,rows or [],pagination.get('next_page_start')
