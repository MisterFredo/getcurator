"""Server-side filters: applied before pagination, never just to the visible rows."""
from concurrent.futures import ThreadPoolExecutor
from fastapi import HTTPException
from core.company import watch_monitoring as monitoring

CHANNEL = r"CASE WHEN REGEXP_CONTAINS(LOWER(w.SOURCE_URL), r'^https?://([a-z0-9-]+\.)*linkedin\.com(?:/|$)') THEN 'LINKEDIN' ELSE 'WEB' END"
KIND = f"""CASE WHEN w.COLLECTION_METHOD='BRIGHTDATA' THEN 'PUBLICATIONS'
 WHEN JSON_VALUE(w.COLLECTION_CONFIG, '$.mode')='SINGLE_PAGE' THEN 'SINGLE_PAGE'
 WHEN JSON_VALUE(w.COLLECTION_CONFIG, '$.mode') IS NULL AND ({CHANNEL})='LINKEDIN' THEN 'SINGLE_PAGE'
 ELSE 'PUBLICATIONS' END"""
ITEM_CHANNEL = r"CASE WHEN REGEXP_CONTAINS(LOWER(d.URL), r'^https?://([a-z0-9-]+\.)*linkedin\.com(?:/|$)') THEN 'LINKEDIN' ELSE 'WEB' END"
ITEM_KIND = "CASE WHEN d.CHANGE_TYPE IN ('NEW_PAGE','UPDATED_PAGE') THEN 'SINGLE_PAGE' ELSE 'PUBLICATIONS' END"

def filters(channel, kind):
    if channel not in {'ALL', 'WEB', 'LINKEDIN'} or kind not in {'ALL', 'PUBLICATIONS', 'SINGLE_PAGE'}:
        raise HTTPException(400, 'Filtre invalide')

def list_sources(company_id=None, is_active=None, channel='ALL', kind='ALL', offset=0, limit=50):
    from core.company import watch_service as service
    filters(channel, kind)
    if offset < 0 or not 1 <= limit <= 500: raise HTTPException(400, 'Pagination invalide')
    clauses, params = [], []
    for value, sql, name, type_ in ((company_id, 'w.ID_COMPANY', 'company', 'STRING'),
        (is_active, 'w.IS_ACTIVE', 'active', 'BOOL'),
        (channel if channel != 'ALL' else None, f'({CHANNEL})', 'channel', 'STRING'),
        (kind if kind != 'ALL' else None, f'({KIND})', 'kind', 'STRING')):
        if value is not None:
            clauses.append(sql + '=@' + name); params.append(service._param(name, type_, value))
    where = 'WHERE ' + ' AND '.join(clauses) if clauses else ''
    params += [service._param('limit','INT64',limit+1), service._param('offset','INT64',offset)]
    rows = service._query(f'''SELECT w.*, c.NAME AS COMPANY_NAME,
        ({CHANNEL}) AS WATCH_CHANNEL, ({KIND}) AS WATCH_KIND FROM `{service.TABLE}` w
        LEFT JOIN `{service.COMPANY}` c USING(ID_COMPANY) {where}
        ORDER BY c.NAME, w.LABEL, w.ID_COMPANY_WATCH LIMIT @limit OFFSET @offset''', params)
    watches = [service._out(r) for r in rows[:limit]]
    with ThreadPoolExecutor(max_workers=8) as pool: diagnostics = list(pool.map(monitoring.diagnostic, watches))
    for watch, diagnostic in zip(watches, diagnostics): watch['diagnostic'] = diagnostic
    return {'status':'ok','watches':watches,'has_more':len(rows)>limit,'offset':offset,'limit':limit}

def list_items(company_id=None, watch_id=None, status='NEW', channel='ALL', kind='ALL', offset=0, limit=50):
    from core.company import watch_discovery_service as service
    filters(channel, kind)
    if status not in {'NEW','STORED','DISMISSED','ALL','IMPORTING','IMPORTED','ERROR'}:
        raise HTTPException(400, 'Statut invalide')
    clauses, params = [], []
    for value, sql, name in ((company_id,'d.ID_COMPANY','company'),(watch_id,'d.ID_COMPANY_WATCH','watch'),
        (channel if channel!='ALL' else None,f'({ITEM_CHANNEL})','channel'),
        (kind if kind!='ALL' else None,f'({ITEM_KIND})','kind')):
        if value is not None:
            clauses.append(sql+'=@'+name); params.append(service._p(name,'STRING',value))
    if status == 'NEW':
        clauses.append("d.STATUS IN ('NEW','STORED') AND COALESCE(d.LIBRARY_STATUS,'PENDING')='PENDING'")
    elif status in {'IMPORTING','IMPORTED','ERROR'}:
        clauses.append("d.STATUS != 'DISMISSED' AND d.LIBRARY_STATUS=@status")
        params.append(service._p('status','STRING',status))
    elif status != 'ALL':
        clauses.append('d.STATUS=@status'); params.append(service._p('status','STRING',status))
    where = 'WHERE '+' AND '.join(clauses) if clauses else ''
    params += [service._p('limit','INT64',limit+1), service._p('offset','INT64',offset)]
    rows = service._query(f'''SELECT d.*, w.LABEL AS WATCH_LABEL, c.NAME AS COMPANY_NAME,
        w.IS_ACTIVE AS WATCH_ACTIVE, w.COLLECTION_METHOD,
        ({ITEM_CHANNEL}) AS WATCH_CHANNEL, ({ITEM_KIND}) AS WATCH_KIND
        FROM `{service.DISCOVERY}` d LEFT JOIN `{service.WATCH}` w USING(ID_COMPANY_WATCH,ID_COMPANY)
        LEFT JOIN `{service.COMPANY}` c ON c.ID_COMPANY=d.ID_COMPANY {where}
        ORDER BY d.DATE_FOUND DESC,d.ID_DISCOVERY DESC LIMIT @limit OFFSET @offset''', params)
    with ThreadPoolExecutor(max_workers=8) as pool: items = list(pool.map(service._candidate_out, rows[:limit]))
    return {'items':items,'has_more':len(rows)>limit,'offset':offset,'limit':limit}
