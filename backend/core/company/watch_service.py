"""Configuration Watch Corpo uniquement. Aucun accès au pipeline RAW."""
import json
import uuid
from fastapi import HTTPException
from google.cloud import bigquery
from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import get_bigquery_client
from api.company.models import CompanyWatchCreate, CompanyWatchUpdate

TABLE = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY_WATCH"
COMPANY = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY"
FIELDS = {
    "label": "STRING", "source_type": "STRING", "source_url": "STRING",
    "source_role": "STRING", "author_name": "STRING",
    "collection_method": "STRING", "collection_config": "STRING", "is_active": "BOOL",
}


def _query(sql, params=()):
    return list(get_bigquery_client().query(
        sql, job_config=bigquery.QueryJobConfig(query_parameters=list(params))
    ).result())


def _param(name, kind, value):
    return bigquery.ScalarQueryParameter(name, kind, value)


def _company(company_id, require_active=False):
    rows = _query(f"SELECT IS_ACTIVE FROM `{COMPANY}` WHERE ID_COMPANY=@company LIMIT 1",
                  [_param("company", "STRING", company_id)])
    if not rows:
        raise HTTPException(404, "Société introuvable")
    if require_active and not rows[0]["IS_ACTIVE"]:
        raise HTTPException(409, "Le suivi ne peut pas être activé pour une société inactive")


def _out(row):
    result = {key.lower(): value for key, value in dict(row).items()}
    config = result.get("collection_config")
    result["collection_config"] = json.loads(config) if isinstance(config, str) else (config or {})
    return result


def list_company_watch(id_company=None, is_active=None, limit=100, offset=0):
    if not 1 <= limit <= 500 or offset < 0:
        raise HTTPException(400, "Pagination invalide")
    clauses, params = [], []
    if id_company is not None:
        _company(id_company)
        clauses.append("w.ID_COMPANY=@company")
        params.append(_param("company", "STRING", id_company))
    if is_active is not None:
        clauses.append("w.IS_ACTIVE=@active")
        params.append(_param("active", "BOOL", is_active))
    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    params += [_param("limit", "INT64", limit + 1), _param("offset", "INT64", offset)]
    rows = _query(f"""SELECT w.*, c.NAME AS COMPANY_NAME
        FROM `{TABLE}` w LEFT JOIN `{COMPANY}` c USING (ID_COMPANY)
        {where} ORDER BY w.CREATED_AT DESC, w.ID_COMPANY_WATCH
        LIMIT @limit OFFSET @offset""", params)
    return {"status": "ok", "watches": [_out(r) for r in rows[:limit]],
            "has_more": len(rows) > limit, "limit": limit, "offset": offset}


def get_company_watch(id_company, watch_id):
    rows = _query(f"""SELECT w.*, c.NAME AS COMPANY_NAME FROM `{TABLE}` w
        LEFT JOIN `{COMPANY}` c USING (ID_COMPANY)
        WHERE w.ID_COMPANY=@company AND w.ID_COMPANY_WATCH=@watch LIMIT 1""",
        [_param("company", "STRING", id_company), _param("watch", "STRING", watch_id)])
    if not rows:
        raise HTTPException(404, "Point de collecte introuvable pour cette société")
    return _out(rows[0])


def _duplicate(id_company, source_type, url, exclude=None):
    rows = _query(f"""SELECT ID_COMPANY_WATCH FROM `{TABLE}`
        WHERE ID_COMPANY=@company AND SOURCE_TYPE=@type AND SOURCE_URL=@url
        AND (@exclude IS NULL OR ID_COMPANY_WATCH != @exclude) LIMIT 1""",
        [_param("company", "STRING", id_company), _param("type", "STRING", source_type),
         _param("url", "STRING", url), _param("exclude", "STRING", exclude)])
    if rows:
        raise HTTPException(409, "Ce point de collecte existe déjà, éventuellement suspendu")


def _values(data):
    values = data.dict(exclude_unset=True)
    if "collection_config" in values:
        try:
            values["collection_config"] = json.dumps(values["collection_config"], allow_nan=False)
        except (ValueError, TypeError):
            raise HTTPException(422, "collection_config doit être un objet JSON valide")
    return values


def create_company_watch(id_company, data: CompanyWatchCreate):
    _company(id_company, require_active=data.is_active)
    _duplicate(id_company, data.source_type, data.source_url)
    # Inclure les valeurs par défaut lors de la création.
    values = _values(CompanyWatchCreate(**data.dict()))
    watch_id = str(uuid.uuid4())
    columns = ["ID_COMPANY_WATCH", "ID_COMPANY", *[k.upper() for k in values], "CREATED_AT", "UPDATED_AT"]
    expressions = ["@watch", "@company", *[
        "PARSE_JSON(@collection_config)" if k == "collection_config" else f"@{k}" for k in values
    ], "CURRENT_TIMESTAMP()", "CURRENT_TIMESTAMP()"]
    params = [_param("watch", "STRING", watch_id), _param("company", "STRING", id_company)]
    params += [_param(k, FIELDS[k], v) for k, v in values.items()]
    _query(f"INSERT INTO `{TABLE}` ({', '.join(columns)}) VALUES ({', '.join(expressions)})", params)
    return get_company_watch(id_company, watch_id)


def update_company_watch(id_company, watch_id, data: CompanyWatchUpdate):
    current = get_company_watch(id_company, watch_id)
    changes = data.dict(exclude_unset=True)
    if not changes:
        raise HTTPException(400, "Aucune modification fournie")
    merged = {k: current[k] for k in FIELDS}
    merged.update(changes)
    # Revalider l'état complet et les contraintes inter-champs futures.
    validated = CompanyWatchCreate(**merged)
    _company(id_company, require_active=validated.is_active)
    _duplicate(id_company, validated.source_type, validated.source_url, watch_id)
    values = _values(data)
    assignments = [f"{k.upper()}=" + ("PARSE_JSON(@collection_config)" if k == "collection_config" else f"@{k}") for k in values]
    params = [_param(k, FIELDS[k], v) for k, v in values.items()]
    params += [_param("company", "STRING", id_company), _param("watch", "STRING", watch_id)]
    _query(f"""UPDATE `{TABLE}` SET {', '.join(assignments)}, UPDATED_AT=CURRENT_TIMESTAMP()
        WHERE ID_COMPANY=@company AND ID_COMPANY_WATCH=@watch""", params)
    return get_company_watch(id_company, watch_id)
