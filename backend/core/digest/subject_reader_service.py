import hashlib
import json

from core.digest.subject_production_service import LOCK, TABLE
from core.digest.subject_sources import add_subject_source_names
from utils.bigquery_utils import query_bq

FEEDBACK = f"{TABLE}_FEEDBACK"


def list_reader_subject_digests(user_id):
    return query_bq(sql=f"""
        SELECT ID AS id, CAST(PERIOD_START AS STRING) AS period_start,
               CAST(DATE_SUB(PERIOD_END, INTERVAL 1 DAY) AS STRING) AS period_end,
               ARRAY_LENGTH(JSON_QUERY_ARRAY(DOCUMENT_JSON, '$.cards')) AS card_count
        FROM `{TABLE}` WHERE USER_ID = @user_id
        ORDER BY PERIOD_START DESC, GENERATED_AT DESC
    """, params={"user_id": user_id}) or []


def _subject_key(card):
    content_ids = sorted({item["id"] for item in card["contents"]})
    payload = json.dumps(content_ids, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def read_reader_subject_digest(user_id, digest_id, owner_id=None):
    rows = query_bq(sql=f"""
        SELECT TO_JSON_STRING(DOCUMENT_JSON) AS document
        FROM `{TABLE}`
        WHERE ID = @id AND USER_ID = @user_id
        ORDER BY GENERATED_AT DESC LIMIT 1
    """, params={"id": digest_id, "user_id": owner_id or user_id}) or []
    if not rows:
        return None
    document = add_subject_source_names(json.loads(rows[0]["document"]))
    feedback = query_bq(sql=f"""
        SELECT SUBJECT_KEY AS subject_key, VALUE AS value
        FROM `{FEEDBACK}`
        WHERE USER_ID = @user_id AND DIGEST_ID = @id
    """, params={"id": digest_id, "user_id": user_id}) or []
    values = {row["subject_key"]: row["value"] for row in feedback}
    for card in document["cards"]:
        card["subject_key"] = _subject_key(card)
        card["feedback"] = values.get(card["subject_key"], 0)
        card.pop("score", None)
    return {
        key: document[key] for key in (
            "profile", "period_start", "period_end", "executive_brief", "cards",
        )
    }


def save_subject_feedback(user_id, digest_id, subject_key, value, owner_id=None):
    document = read_reader_subject_digest(user_id, digest_id, owner_id)
    card = next((
        card for card in (document or {}).get("cards", [])
        if card["subject_key"] == subject_key
    ), None)
    if card is None:
        return False
    query_bq(sql=f"""
        BEGIN TRANSACTION;
        UPDATE `{LOCK}` SET UPDATED_AT = CURRENT_TIMESTAMP() WHERE ID = 'WRITE';
        ASSERT @@row_count = 1 AS 'DIGEST_SUBJECT_LOCK_INVALID';
        MERGE `{FEEDBACK}` t
        USING (SELECT @user_id AS user_id, @id AS digest_id, @key AS subject_key) s
        ON t.USER_ID = s.user_id AND t.DIGEST_ID = s.digest_id AND t.SUBJECT_KEY = s.subject_key
        WHEN MATCHED AND @value = 0 THEN DELETE
        WHEN MATCHED THEN UPDATE SET VALUE = @value, SUBJECT_TITLE = @title,
                                     UPDATED_AT = CURRENT_TIMESTAMP()
        WHEN NOT MATCHED AND @value != 0 THEN
          INSERT (USER_ID, DIGEST_ID, SUBJECT_KEY, SUBJECT_TITLE, VALUE, UPDATED_AT)
          VALUES (@user_id, @id, @key, @title, @value, CURRENT_TIMESTAMP());
        COMMIT TRANSACTION;
    """, params={
        "user_id": user_id, "id": digest_id, "key": subject_key, "value": value,
        "title": card["title"],
    })
    return True
