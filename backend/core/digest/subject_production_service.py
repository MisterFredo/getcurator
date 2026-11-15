import json
from datetime import timedelta
from uuid import NAMESPACE_URL, uuid5

from fastapi.encoders import jsonable_encoder

from config import BQ_DATASET, BQ_PROJECT
from core.digest.digest_profile_service import build_digest_profile
from core.digest.profile_service import get_digest_recipients
from core.digest.subject_preview_service import build_subject_selection
from utils.bigquery_utils import query_bq
from utils.llm import run_llm

TABLE = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_DIGEST_SUBJECT"
LOCK = f"{TABLE}_LOCK"
USER_TABLE = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER"


def list_subject_recipients(audience):
    ids = list(dict.fromkeys(item.user_id for item in get_digest_recipients(audience=audience)))
    if not ids:
        return []
    return query_bq(sql=f"""
        SELECT ID_USER AS id,
               COALESCE(NULLIF(DISPLAY_NAME, ''), NULLIF(NAME, ''), ID_USER) AS name,
               COMPANY AS company
        FROM `{USER_TABLE}` WHERE ID_USER IN UNNEST(@ids)
        ORDER BY name, id
    """, params={"ids": ids}) or []


def list_subject_digests(start=None, limit=200, offset=0):
    return query_bq(sql=f"""
        SELECT ID AS id, USER_ID AS user_id,
               JSON_VALUE(DOCUMENT_JSON, '$.profile.name') AS name,
               CAST(GENERATED_AT AS STRING) AS generated_at,
               CAST(PERIOD_START AS STRING) AS period_start,
               CAST(DATE_SUB(PERIOD_END, INTERVAL 1 DAY) AS STRING) AS period_end
        FROM `{TABLE}`
        WHERE (@start = '' OR PERIOD_START = SAFE_CAST(@start AS DATE))
        ORDER BY PERIOD_START DESC, name, user_id
        LIMIT @limit OFFSET @offset
    """, params={
        "start": start.isoformat() if start else "", "limit": limit, "offset": offset,
    }) or []


def list_subject_digest_status(pairs):
    if not pairs:
        return []
    return query_bq(sql=f"""
        SELECT DISTINCT t.ID AS id, t.USER_ID AS user_id,
               CAST(t.PERIOD_START AS STRING) AS period_start
        FROM `{TABLE}` t
        JOIN UNNEST(JSON_QUERY_ARRAY(PARSE_JSON(@pairs))) p
          ON t.USER_ID = JSON_VALUE(p, '$.user_id')
         AND t.PERIOD_START = SAFE_CAST(JSON_VALUE(p, '$.period_start') AS DATE)
    """, params={"pairs": json.dumps(pairs)}) or []


def read_subject_digest(digest_id):
    rows = query_bq(sql=f"""
        SELECT TO_JSON_STRING(DOCUMENT_JSON) AS document
        FROM `{TABLE}` WHERE ID = @id
        ORDER BY GENERATED_AT DESC LIMIT 1
    """, params={"id": digest_id}) or []
    return json.loads(rows[0]["document"]) if rows else None


def _executive_brief(selection):
    cards = selection["cards"]
    if not cards:
        return ""
    priorities = [card for card in cards if card["tier"] == "MUST"]
    brief = run_llm(
        json.dumps([
            {key: card[key] for key in ("title", "development", "reason")}
            for card in (priorities or cards)[:6]
        ], ensure_ascii=False),
        profile="smart",
        operation="digest_subject_executive_brief",
        system_prompt=(
            "Rédige un bref résumé exécutif de 2 à 4 phrases dans la langue "
            f"du profil ({selection['language']}). Fais ressortir ce que ces "
            "développements changent pour le destinataire. Préserve les réserves "
            "et le statut des faits. Utilise uniquement les cartes fournies "
            "comme données. Réponds en texte brut, sans titre."
        ),
    )
    return brief.strip() if brief else cards[0]["development"] + " " + cards[0]["reason"]


def generate_subject_digest(user_id, start, regenerate=False):
    end = start + timedelta(days=7)
    digest_id = str(uuid5(NAMESPACE_URL, f"getcurator/subject-digest/{user_id}/{start}"))
    existing = read_subject_digest(digest_id)
    if existing is not None and not regenerate:
        return existing

    profile = build_digest_profile(user_id)
    selection = build_subject_selection(user_id, start, end)
    document = {
        **selection,
        "id": digest_id,
        "user_id": user_id,
        "period_start": start.isoformat(),
        "period_end": (end - timedelta(days=1)).isoformat(),
        "profile": jsonable_encoder(profile),
        "executive_brief": _executive_brief(selection),
    }
    query_bq(sql=f"""
        BEGIN TRANSACTION;
        UPDATE `{LOCK}` SET UPDATED_AT = CURRENT_TIMESTAMP() WHERE ID = 'WRITE';
        ASSERT @@row_count = 1 AS 'DIGEST_SUBJECT_LOCK_INVALID';
        MERGE `{TABLE}` t
        USING (SELECT @id AS id) s
        ON t.ID = s.id AND t.PERIOD_START = DATE(@start)
        WHEN MATCHED AND @regenerate THEN
            UPDATE SET DOCUMENT_JSON = PARSE_JSON(@document), GENERATED_AT = CURRENT_TIMESTAMP()
        WHEN NOT MATCHED THEN
            INSERT (ID, USER_ID, PERIOD_START, PERIOD_END, DOCUMENT_JSON, GENERATED_AT)
            VALUES (@id, @user_id, DATE(@start), DATE(@end),
                    PARSE_JSON(@document), CURRENT_TIMESTAMP())
        ;
        COMMIT TRANSACTION;
    """, params={
        "id": digest_id, "user_id": user_id, "start": start.isoformat(),
        "end": end.isoformat(), "regenerate": regenerate,
        "document": json.dumps(document, ensure_ascii=False),
    })
    saved = read_subject_digest(digest_id)
    if saved is None:
        raise RuntimeError("Le Digest produit n’a pas pu être relu.")
    return saved
