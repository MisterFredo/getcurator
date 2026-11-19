import re
from datetime import datetime, date
from typing import Optional, Dict, Any
from config import BQ_PROJECT, BQ_DATASET
from api.content.models import ContentCreate
from core.content.ai import generate_summary
from core.content.service import create_content
from core.content.relation_service import resolve_all_relations
from utils.bigquery_utils import query_bq, update_bq

TABLE_CONTENT = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT"
TABLE_CONTENT_RAW = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_RAW"

def normalize_llm_list(values):
    output = []
    for value in values or []:
        if not value:
            continue
        for part in re.split(r",|;", value):
            part = part.strip()
            if part:
                output.append(part)
    return list(dict.fromkeys(output))

def _load_raw_contents(limit: int, specific_id: Optional[str]):
    if specific_id:
        return query_bq(
            f"SELECT * FROM `{TABLE_CONTENT_RAW}` WHERE ID_RAW = @id_raw",
            {"id_raw": specific_id},
        )
    return query_bq(
        f"""SELECT * FROM `{TABLE_CONTENT_RAW}`
        WHERE STATUS = 'STORED'
        ORDER BY CREATED_AT DESC
        LIMIT {int(limit)}"""
    )

def _normalize_source_date(value):
    if not value:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        try:
            return datetime.strptime(value.split('T')[0], '%Y-%m-%d').date()
        except Exception:
            return None
    return None

def _build_content_payload(raw, summary):
    return ContentCreate(
        id_primary_company=raw.get('ID_PRIMARY_COMPANY'),
        id_raw=raw.get('ID_RAW'),
        source_id=raw.get('SOURCE_ID'),
        source_url=raw.get('SOURCE_URL'),
        source_title=raw.get('SOURCE_TITLE'),
        source_date=_normalize_source_date(raw.get('DATE_SOURCE')),
        title=summary.get('title'),
        excerpt=summary.get('excerpt'),
        content_body=summary.get('content_body'),
        chiffres=summary.get('chiffres', []),
        acteurs_cites=summary.get('acteurs_cites', []),
        concepts_llm=normalize_llm_list(summary.get('concepts_llm', [])),
        solutions_llm=normalize_llm_list(summary.get('solutions_llm', [])),
        topics_llm=normalize_llm_list(summary.get('topics_llm', [])),
        mecanique_expliquee=summary.get('mecanique_expliquee'),
        enjeu_strategique=summary.get('enjeu_strategique'),
        point_de_friction=summary.get('point_de_friction'),
        signal_analytique=summary.get('signal_analytique'),
    )

def _mark_raw_processing(raw_id: str):
    update_bq(TABLE_CONTENT_RAW, {'STATUS': 'PROCESSING', 'ERROR_MESSAGE': None}, where={'ID_RAW': raw_id})

def _mark_raw_processed(raw_id: str, content_id: str):
    update_bq(TABLE_CONTENT_RAW, {
        'STATUS': 'PROCESSED', 'PROCESSED_AT': datetime.utcnow(),
        'GENERATED_CONTENT_ID': content_id, 'ERROR_MESSAGE': None,
    }, where={'ID_RAW': raw_id})

def _mark_raw_error(raw_id: str, error: Exception):
    update_bq(TABLE_CONTENT_RAW, {'STATUS': 'ERROR', 'ERROR_MESSAGE': str(error)}, where={'ID_RAW': raw_id})

def _existing_content_id(raw_id: str):
    rows = query_bq(
        f"""SELECT ID_CONTENT FROM `{TABLE_CONTENT}`
        WHERE ID_RAW = @id_raw ORDER BY CREATED_AT ASC LIMIT 1""",
        {'id_raw': raw_id},
    )
    return rows[0]['ID_CONTENT'] if rows else None

def destock_all_raw_contents(batch_size: int = 50, on_batch=None):
    total_processed = 0
    total_errors = 0
    while True:
        result = destock_raw_contents(limit=batch_size)
        if result['total_selected'] == 0:
            break
        total_processed += result['processed']
        total_errors += result['errors']
        if on_batch:
            on_batch(total_processed, total_errors)
        print(f"Batch terminé → processed: {result['processed']} | errors: {result['errors']}")
        if result['processed'] == 0:
            print('Aucun traitement réussi dans ce batch → arrêt de sécurité')
            break
    return {'total_processed': total_processed, 'total_errors': total_errors}

def destock_raw_contents(limit: int = 5, specific_id: Optional[str] = None) -> Dict[str, Any]:
    raws = _load_raw_contents(limit, specific_id)
    processed = 0
    errors = 0
    for raw in raws:
        raw_id = raw['ID_RAW']
        # Never mark an already processed/processing RAW as ERROR.
        if raw['STATUS'] not in ('STORED', 'ERROR'):
            print('RAW non traitable (status invalide):', raw_id, raw['STATUS'])
            errors += 1
            continue
        try:
            print('\n==============================')
            print('RAW ID:', raw_id)
            print('SOURCE_ID:', raw.get('SOURCE_ID'))
            print('ID_PRIMARY_COMPANY:', raw.get('ID_PRIMARY_COMPANY'))
            print('RAW LENGTH:', len(raw.get('RAW_TEXT', '') or ''))
            print('------------------------------')
            _mark_raw_processing(raw_id)
            # Resume partial success without a second LLM call or CONTENT insert.
            content_id = _existing_content_id(raw_id)
            if content_id:
                print('ℹ️ CONTENT EXISTANT, reprise des relations:', content_id)
            else:
                summary = generate_summary(
                    source_id=raw.get('SOURCE_ID'),
                    source_text=raw.get('RAW_TEXT', ''),
                )
                payload = _build_content_payload(raw, summary)
                content_id = create_content(payload)
            resolve_all_relations(content_id)
            _mark_raw_processed(raw_id, content_id)
            processed += 1
        except Exception as e:
            print('\n❌ ERROR DURING DESTOCK:', str(e))
            _mark_raw_error(raw_id, e)
            errors += 1
    return {'processed': processed, 'errors': errors, 'total_selected': len(raws)}
