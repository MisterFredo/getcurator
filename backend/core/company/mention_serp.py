"""Bright Data SERP, fixed endpoint, explicit locales, capped pagination."""
import json
import os
import requests
from urllib.parse import urlencode


def search(term,precision,mode,country,language,start_date,end_date,offset,domains):
    if mode != 'NEWS':raise ValueError('Seul Google News est autorisé pour les mentions externes')
    token=os.getenv('BRIGHTDATA_API_KEY','').strip()
    zone=os.getenv('BRIGHTDATA_SERP_ZONE','').strip()
    if not token or not zone:raise ValueError('BRIGHTDATA_API_KEY et BRIGHTDATA_SERP_ZONE doivent être configurées dans le backend')
    from datetime import date,timedelta
    phrase='"'+term.replace('"','')+'"'
    q=('intitle:'+phrase if precision=='TITLE' else phrase)+' '+ ' '.join('-site:'+d for d in domains)
    q+=f" after:{(date.fromisoformat(start_date)-timedelta(days=1)).isoformat()} before:{(date.fromisoformat(end_date)+timedelta(days=1)).isoformat()}"
    params={'q':q,'gl':country,'hl':language,'brd_json':'1','start':offset}
    params['tbm']='nws'
    url='https://www.google.com/search?'+urlencode(params)
    try:
        response=requests.post('https://api.brightdata.com/request',
            headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'},
            json={'zone':zone,'url':url,'format':'raw','data_format':'parsed'},timeout=(10,60),allow_redirects=False)
        if response.status_code!=200:raise RuntimeError(f'SERP_HTTP_{response.status_code}')
        result=response.json()
        if isinstance(result,dict) and 'body' in result:
            result=json.loads(result['body']) if isinstance(result['body'],str) else result['body']
    except requests.RequestException:raise RuntimeError('SERP_NETWORK_ERROR') from None
    if not isinstance(result,dict):raise RuntimeError('SERP_INVALID_JSON')
    general=result.get('general') or {}
    if general.get('search_type') and general['search_type'] != 'news':raise RuntimeError('SERP_WRONG_MODE')
    rows=result.get('news')
    if rows is None and general.get('empty') is not True:raise RuntimeError('SERP_MISSING_RESULTS')
    if rows is not None and not isinstance(rows,list):raise RuntimeError('SERP_INVALID_RESULTS')
    return result,rows or [],(result.get('pagination') or {}).get('next_page_start')
