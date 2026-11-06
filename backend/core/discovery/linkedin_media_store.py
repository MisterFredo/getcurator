"""Shared LinkedIn RAW storage for Studio and Bright Data; no Library/extraction."""
from __future__ import annotations
import hashlib
import json
import re
import uuid
from datetime import datetime, date, timezone
from functools import lru_cache
from zoneinfo import ZoneInfo
from google.cloud import bigquery
from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import get_bigquery_client
from core.library.company_watch_library import document_lock
from core.discovery.brightdata_linkedin import post_id

BASE=f'{BQ_PROJECT}.{BQ_DATASET}'
RAW=f'{BASE}.RATECARD_CONTENT_RAW'


def query(sql, params=()):
    return list(get_bigquery_client().query(sql,job_config=bigquery.QueryJobConfig(query_parameters=list(params))).result())


def param(n,t,v):return bigquery.ScalarQueryParameter(n,t,v)


def content_hash(text):
    text=(text or '').strip().lower().replace('\u00a0',' ').replace('’',"'").replace('“','"').replace('”','"')
    return hashlib.sha256(re.sub(r'\s+',' ',text).strip().encode()).hexdigest()


def existing(source_id):
    rows=query(f"SELECT RAW_TEXT, SOURCE_URL FROM `{RAW}` WHERE SOURCE_ID=@source",
        [param('source','STRING',source_id)])
    return ({content_hash(r['RAW_TEXT']) for r in rows if r.get('RAW_TEXT')},
            {p for r in rows if (p:=post_id(r.get('SOURCE_URL')))})


@lru_cache(maxsize=1)
def raw_date_type():
    # Existing installations may use DATE, DATETIME, TIMESTAMP or STRING.
    table=get_bigquery_client().get_table(RAW)
    field=next((f for f in table.schema if f.name=='DATE_SOURCE'),None)
    kind=field.field_type if field else None
    if kind not in {'DATE','DATETIME','TIMESTAMP','STRING'}:
        raise ValueError('Type DATE_SOURCE non pris en charge dans RATECARD_CONTENT_RAW')
    return kind


def source_date(value):
    if not value:return None
    if isinstance(value,date) and not isinstance(value,datetime):return value.isoformat()
    parsed=value if isinstance(value,datetime) else datetime.fromisoformat(str(value).replace('Z','+00:00'))
    if parsed.tzinfo is not None:parsed=parsed.astimezone(ZoneInfo('Europe/Paris'))
    return parsed.date().isoformat()


def store_posts(source_id,posts,*,discovery_ids=None):
    if not source_id:raise ValueError('source_id manquant')
    with document_lock('media-store-'+hashlib.sha256((BASE+source_id).encode()).hexdigest()):
        hashes,ids=existing(source_id)
        pending=[];skipped=0
        for post in posts:
            text=str(post.get('raw_text') or '').strip()
            identifier=post_id(post.get('source_url'))
            h=content_hash(text)
            if not text or h in hashes or (identifier and identifier in ids):skipped+=1;continue
            title=post.get('title') or ' '.join(text.split())[:200]
            pending.append({'id':str(uuid.uuid5(uuid.NAMESPACE_URL,'media-linkedin:'+source_id+':'+(identifier or h))),
                'title':title,'text':text,'date':source_date(post.get('date_source')),
                'url':post.get('source_url')})
            hashes.add(h)
            if identifier:ids.add(identifier)
        if pending or discovery_ids:
            # Stable IDs make a replay after an uncertain commit idempotent.
            date_type=raw_date_type()
            sql = f"""MERGE `{RAW}` T USING (
                SELECT JSON_VALUE(p,'$.id') AS ID_RAW, JSON_VALUE(p,'$.title') AS TITLE,
                  JSON_VALUE(p,'$.text') AS RAW_TEXT, JSON_VALUE(p,'$.date') AS DATE_SOURCE,
                  JSON_VALUE(p,'$.url') AS SOURCE_URL
                FROM UNNEST(JSON_QUERY_ARRAY(PARSE_JSON(@payload))) p
            ) S ON T.ID_RAW=S.ID_RAW
            WHEN NOT MATCHED THEN INSERT (ID_RAW,CREATED_AT,STATUS,ID_PRIMARY_COMPANY,
                SOURCE_TITLE,IMPORT_TYPE,DATE_SOURCE,RAW_TEXT,SOURCE_ID,SOURCE_URL)
            VALUES (S.ID_RAW,CURRENT_TIMESTAMP(),'STORED',NULL,S.TITLE,'LINKEDIN',
                SAFE_CAST(S.DATE_SOURCE AS {date_type}),S.RAW_TEXT,@source,S.SOURCE_URL)"""
            params=[param('payload','STRING',json.dumps(pending,ensure_ascii=False)),param('source','STRING',source_id)]
            if discovery_ids:
                discovery=f'{BASE}.RATECARD_SOURCE_DISCOVERY'
                sql=f"""BEGIN TRANSACTION;
                    ASSERT (SELECT COUNT(*) FROM `{discovery}` WHERE SOURCE_ID=@source
                        AND ID_DISCOVERY IN UNNEST(@ids) AND STATUS='NEW') = @count
                        AS 'La sélection a changé de statut ; actualiser Discovery';
                    {sql};
                    UPDATE `{discovery}` SET STATUS='STORED' WHERE ID_DISCOVERY IN UNNEST(@ids) AND SOURCE_ID=@source;
                    COMMIT TRANSACTION;"""
                params += [bigquery.ArrayQueryParameter('ids','STRING',discovery_ids),param('count','INT64',len(discovery_ids))]
            query(sql,params)
        return {'requested':len(posts),'stored':len(pending),'skipped':skipped}
