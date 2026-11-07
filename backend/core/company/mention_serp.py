"""Simple Google News requests with bounded, redacted response diagnostics."""
import json
import logging
import os
import re
from time import perf_counter
from urllib.parse import urlencode
import requests
from collections.abc import Mapping

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


SAFE_RESPONSE_HEADERS={
    'content-type','content-length','content-encoding','date','retry-after',
    'x-brd-error-code','x-brd-error','x-brd-err-code','x-brd-err-msg',
    'x-brd-rate-limit','x-brd-rate-limit-period-ms','x-brd-request-id',
    'x-request-id','x-luminati-request-id',
}

def _response_headers(response,token):
    headers=getattr(response,'headers',{}) or {}
    if not isinstance(headers,Mapping):return {}
    lowered={str(k).lower():v for k,v in headers.items()}
    selected={k:_excerpt(str(v),token) for k,v in lowered.items() if k in SAFE_RESPONSE_HEADERS}
    debug=lowered.get('x-brd-debug','')
    if isinstance(debug,str):
        match=re.search(r'(?:^|[; ,])req_id=([^; ,]+)',debug)
        if match:selected['x-brd-debug-req-id']=_excerpt(match[1],token)[:160]
    return selected


def build_url(term,country,language,offset=0):
    q=term.strip()
    if not q:raise ValueError('Nom de société manquant')
    params={'q':q,'gl':country,'hl':language,'brd_json':'1','start':offset,'tbm':'nws'}
    return 'https://www.google.com/search?'+urlencode(params)


def search(term,precision,mode,country,language,start_date,end_date,offset,domains):
    if mode!='NEWS':raise ValueError('Seul Google News est autorisé pour les mentions externes')
    return _request(build_url(term,country,language,offset),country,language,offset)[:3]


def probe(url,country='FR',language='fr',offset=0,*,response_format='raw',parsed_response=True):
    """Same live connector as production, no cache, no Library import."""
    try:
        result,rows,_,diagnostics=_request(url,country,language,offset,response_format=response_format,parsed_response=parsed_response)
        return {'ok':True,'count':len(rows),'diagnostics':diagnostics,
            'sample':[{k:row.get(k) for k in ('title','link','url','source','date')} for row in rows[:3] if isinstance(row,dict)]}
    except SerpFailure as exc:return {'ok':False,'reason':str(exc),'diagnostics':exc.details}


def _request(url,country,language,offset,*,response_format='raw',parsed_response=True):
    token=os.getenv('BRIGHTDATA_API_KEY','').strip();zone=os.getenv('BRIGHTDATA_SERP_ZONE','').strip()
    if not token or not zone:raise ValueError('BRIGHTDATA_API_KEY et BRIGHTDATA_SERP_ZONE doivent être configurées dans le backend')
    request_payload={'zone':zone,'url':url,'format':response_format}
    if parsed_response:request_payload['data_format']='parsed'
    envelope={}
    started=perf_counter();response=None
    def diagnostic(stage,body=None):
        text=body if isinstance(body,str) else getattr(response,'text','')
        text=text if isinstance(text,str) else ''
        content=getattr(response,'content',None)
        raw_size=len(content) if isinstance(content,bytes) else len(text.encode('utf-8',errors='replace'))
        headers=_response_headers(response,token)
        return {'stage':stage,'http_status':getattr(response,'status_code',None),
            'content_type':headers.get('content-type',''),'body_bytes':raw_size,
            'decoded_text_bytes':len(text.encode('utf-8',errors='replace')),
            'elapsed_seconds':round(perf_counter()-started,3),'response_excerpt':_excerpt(text,token),
            'response_headers':headers,'request_payload':dict(request_payload),**envelope}
    def fail(reason,*,body=None,stage='transport'):
        diagnostics=diagnostic(stage,body)
        logger.warning('[MENTIONS] SERP failure reason=%s locale=%s/%s offset=%s diagnostics=%s',
            reason,country,language,offset,json.dumps(diagnostics,ensure_ascii=False))
        raise SerpFailure(reason,diagnostics) from None
    try:
        response=requests.post('https://api.brightdata.com/request',
            headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'},
            json=request_payload,timeout=(5,15),allow_redirects=False)
    except requests.ConnectTimeout:fail('SERP_CONNECT_TIMEOUT')
    except requests.ReadTimeout:fail('SERP_READ_TIMEOUT')
    except requests.exceptions.SSLError:fail('SERP_SSL_ERROR')
    except requests.RequestException:fail('SERP_CONNECTION_ERROR')
    provider_headers=_response_headers(response,token)
    provider_code=provider_headers.get('x-brd-error-code') or provider_headers.get('x-brd-err-code')
    if provider_code:
        if 'captcha' in provider_code.lower() or provider_code=='verifying':fail('SERP_CAPTCHA',stage='provider')
        if any(part in provider_code.lower() for part in ('rate_limit','query_rejected','10110')):fail('SERP_RATE_LIMIT',stage='provider')
        fail('SERP_PROVIDER_ERROR',stage='provider')
    if response.status_code!=200:fail(f'SERP_HTTP_{response.status_code}')
    content=getattr(response,'content',None)
    text=getattr(response,'text','')
    if isinstance(content,bytes) and not content and (not isinstance(text,str) or not text.strip()):
        fail('SERP_EMPTY_RESPONSE',stage='response_body')
    try:result=response.json()
    except ValueError:fail('SERP_INVALID_JSON',stage='response_json')
    # Accept a JSON-encoded object or a documented body envelope, but never
    # interpret HTML/error pages as an empty successful search.
    for _ in range(3):
        if isinstance(result,str):
            if not result.strip():fail('SERP_EMPTY_RESPONSE',body=result,stage='encoded_body')
            try:result=json.loads(result.lstrip('\ufeff'))
            except ValueError:fail('SERP_INVALID_JSON',body=result,stage='encoded_json')
        elif isinstance(result,dict) and 'body' in result:
            envelope['upstream_status_code']=result.get('status_code')
            carrier=type('HeadersOnly',(),{'headers':result.get('headers') or {}})()
            envelope['upstream_headers']=_response_headers(carrier,token)
            inner_code=envelope['upstream_headers'].get('x-brd-error-code') or envelope['upstream_headers'].get('x-brd-err-code')
            if inner_code:
                if 'captcha' in inner_code.lower() or inner_code=='verifying':fail('SERP_CAPTCHA',stage='provider_upstream')
                if any(part in inner_code.lower() for part in ('rate_limit','query_rejected','10110')):fail('SERP_RATE_LIMIT',stage='provider_upstream')
                fail('SERP_PROVIDER_ERROR',stage='provider_upstream')
            status=result.get('status_code')
            if isinstance(status,int) and status>=400:fail(f'SERP_UPSTREAM_HTTP_{status}',stage='upstream_response')
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
    diagnostics=diagnostic('complete')
    provider_input=result.get('input') or {}
    if isinstance(provider_input,dict) and isinstance(provider_input.get('request_id'),str):
        diagnostics['provider_request_id']=provider_input['request_id'][:160]
    logger.info('[MENTIONS] SERP success locale=%s/%s offset=%s count=%s diagnostics=%s',country,language,offset,len(rows or []),json.dumps({k:v for k,v in diagnostics.items() if k!='response_excerpt'},ensure_ascii=False))
    return result,rows or [],pagination.get('next_page_start'),diagnostics
