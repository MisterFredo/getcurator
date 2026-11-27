"""Saved V2 Digests as editorial context; dated linked contents as evidence."""

import json
from datetime import date, timedelta
from uuid import UUID

from fastapi.encoders import jsonable_encoder

from config import BQ_DATASET, BQ_PROJECT
from core.user.user_profile_service import get_user_profile
from utils.bigquery_utils import query_bq

DIGEST_TABLE = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_DIGEST_SUBJECT"
CONTENT_TABLE = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_ENRICHED"
EVIDENCE_FIELDS = (
    "excerpt", "signal_analytique", "mecanique_expliquee",
    "enjeu_strategique", "point_de_friction", "chiffres",
)

DIGEST_INSTRUCTIONS = """
SOURCES DIGESTS V2 : les payloads source_type=DIGEST_SUBJECT contiennent
editorial_topics (contexte de sélection), profile/current_profile_context
(mandat éditorial, jamais preuve) et contents (preuves figées).
Construis une lecture adaptée aux priorités du destinataire, pas un catalogue
par semaine. Ne transforme pas ses objectifs en faits sur son entreprise.
Recompose les sujets à partir des seuls contenus fournis, en corrigeant les
regroupements hebdomadaires trop larges. Ne rajoute pas de sujet extérieur.
Distingue événement nouveau, nouvel éclairage, contradiction et simple reprise.
La date publication_day date la publication, pas nécessairement le fait.
Un même content_id repris dans plusieurs Digests reste une seule preuve.
Plusieurs articles sur un événement ou une étude ne démontrent ni progression
opérationnelle ni confirmations indépendantes. N’infère pas un recul du marché
de l’absence d’un sujet. Ne compare pas deux mois par volume brut si les
périodes ou la couverture diffèrent. analysis_start / analysis_end définissent
la période inclusive à analyser, même si les Digests chevauchent deux mois.
Les contenus ont déjà été filtrés. Les résumés hebdomadaires et les raisons de
sélection ne sont jamais citables comme preuves factuelles.
Cite uniquement /contents/N/excerpt, /contents/N/signal_analytique,
/contents/N/mecanique_expliquee, /contents/N/enjeu_strategique,
/contents/N/point_de_friction ou /contents/N/chiffres/M, avec un passage
scalaire exact et le content_id du contenu. Le profil, les titres, les dates,
les URLs et editorial_topics ne sont pas des preuves factuelles citables.
Préserve les réserves des analyses et la portée des chiffres. La présence
d’un chiffre dans un texte n’en fait pas un Number certifié.
Les payloads fournissent report_id et version_number : reproduis-les.
Le socle utilise les versions des contenus et du profil disponibles lors de
sa préparation ; ce n’est pas une reconstitution historique au jour du Digest.
""".strip()


def list_digest_sources(query="", start=None, end=None, limit=100, offset=0):
    if start and end and start > end:
        raise ValueError("La fin de période précède son début.")
    rows = query_bq(sql=f"""
        SELECT ID AS id, USER_ID AS user_id,
               JSON_VALUE(DOCUMENT_JSON, '$.profile.name') AS name,
               CAST(PERIOD_START AS STRING) AS period_start,
               CAST(DATE_SUB(PERIOD_END, INTERVAL 1 DAY) AS STRING) AS period_end,
               CAST(GENERATED_AT AS STRING) AS generated_at
        FROM `{DIGEST_TABLE}`
        WHERE (@q = '' OR STRPOS(LOWER(COALESCE(
          JSON_VALUE(DOCUMENT_JSON, '$.profile.name'), '')), LOWER(@q)) > 0)
          AND (@start = '' OR PERIOD_END > SAFE_CAST(@start AS DATE))
          AND (@end = '' OR PERIOD_START <= SAFE_CAST(@end AS DATE))
        ORDER BY PERIOD_START DESC, name, ID
        LIMIT @limit OFFSET @offset
    """, params={
        "q": query.strip(), "start": start.isoformat() if start else "",
        "end": end.isoformat() if end else "", "limit": min(max(limit, 1), 100),
        "offset": max(offset, 0),
    }) or []
    return jsonable_encoder(rows)


def read_digest_source(digest_id, start: date, end: date, profile_cache):
    digest_id = str(UUID(digest_id))
    rows = query_bq(sql=f"""
        SELECT ID, USER_ID, PERIOD_START, PERIOD_END, GENERATED_AT,
               TO_JSON_STRING(DOCUMENT_JSON) AS DOCUMENT
        FROM `{DIGEST_TABLE}` WHERE ID = @id LIMIT 2
    """, params={"id": digest_id}) or []
    if len(rows) != 1:
        raise ValueError(f"Digest introuvable ou dupliqué : {digest_id}.")
    row = rows[0]
    document = json.loads(row["DOCUMENT"])
    refs = list(dict.fromkeys(
        str(content["id"])
        for card in document.get("cards", [])
        for content in card.get("contents", [])
        if content.get("id")
    ))
    if not refs:
        raise ValueError(f"Le Digest {digest_id} ne contient aucune référence de contenu.")

    contents = query_bq(sql=f"""
        SELECT id_content AS content_id, title, excerpt, published_at, source_date,
               DATE(published_at, 'Europe/Paris') AS publication_day,
               source_id, source_title, source_url,
               signal_analytique, mecanique_expliquee, enjeu_strategique,
               point_de_friction, chiffres
        FROM `{CONTENT_TABLE}`
        WHERE id_content IN UNNEST(@ids)
        ORDER BY published_at, id_content
    """, params={"ids": refs}) or []
    found = [c["content_id"] for c in contents]
    if len(found) != len(set(found)):
        raise ValueError("Plusieurs lignes de contenus partagent un même identifiant.")
    missing = sorted(set(refs) - set(found))
    if missing:
        raise ValueError("Contenus liés au Digest introuvables : " + ", ".join(missing))
    if any(c.get("publication_day") is None for c in contents):
        raise ValueError("Un contenu lié au Digest est sans date de publication.")

    retained = [jsonable_encoder(c) for c in contents
                if start <= c["publication_day"] <= end]
    eligible_ids = {c["content_id"] for c in retained}
    if not retained:
        raise ValueError(f"Le Digest {digest_id} n’a aucun contenu dans la période choisie.")
    if not any(isinstance(c.get(k), str) and c[k].strip()
               for c in retained for k in EVIDENCE_FIELDS if k != "chiffres"):
        raise ValueError(f"Le Digest {digest_id} ne fournit aucune matière analytique exploitable.")

    topics = []
    for card in document.get("cards", []):
        ids = [str(c["id"]) for c in card.get("contents", []) if c.get("id")]
        kept = [cid for cid in ids if cid in eligible_ids]
        if not kept:
            continue
        topics.append({
            "title": card.get("title", ""), "tier": card.get("tier"),
            "score": card.get("score"), "content_ids": kept,
            # Never reuse mixed-period weekly factual summaries as evidence.
            "development": card.get("development", "") if set(ids) <= eligible_ids else "",
            "editorial_relevance": card.get("reason", ""),
            "context_only": True,
        })

    user_id = str(row["USER_ID"])
    if user_id not in profile_cache:
        profile = get_user_profile(user_id=user_id) or {}
        profile_cache[user_id] = {
            "structured_profile": profile.get("structured_profile")
                if profile.get("profile_structured_status") == "READY" else None,
            "profile_source_hash": profile.get("profile_source_hash"),
            "profile_status": profile.get("profile_structured_status"),
        }
    payload = {
        "source_type": "DIGEST_SUBJECT", "report_id": f"digest-subject:{digest_id}",
        "version_number": 1, "digest_id": digest_id, "user_id": user_id,
        "subject": f"Digest - {(document.get('profile') or {}).get('name') or user_id} - {row['PERIOD_START']}",
        "period_start": start.isoformat(),
        "period_end": (end + timedelta(days=1)).isoformat(),
        "digest_period_start": str(row["PERIOD_START"]),
        "digest_period_end_exclusive": str(row["PERIOD_END"]),
        "digest_generated_at": str(row["GENERATED_AT"]),
        "profile": document.get("profile"),
        "current_profile_context": jsonable_encoder(profile_cache[user_id]),
        "editorial_topics": topics, "contents": retained,
        "sources": [{
            "content_id": c["content_id"], "title": c.get("title"),
            "source_name": next((ref.get("source_name") for card in document.get("cards", [])
                for ref in card.get("contents", []) if ref.get("id") == c["content_id"]), None),
            "original_title": c.get("source_title"), "url": c.get("source_url"),
            "published_at": c.get("published_at"),
            "publication_day": c.get("publication_day"),
        } for c in retained],
        "evidence_policy": (
            "Only /contents analytical fields are factual evidence. Profile and topics are editorial context. "
            "Current profile is loaded at production preparation, not a historical profile snapshot. "
            "Content snapshots are frozen at production preparation and may have been edited since the Digest. "
            "Use publication_day for corpus membership; distinguish publication date from event date. "
            "Repeated content IDs across Digests are the same evidence, not independent confirmation."
        ),
    }
    return payload["report_id"], 1, payload


def validate_digest_citation(report, source):
    import re
    match = re.fullmatch(
        r"/contents/(0|[1-9][0-9]*)/(excerpt|signal_analytique|mecanique_expliquee|enjeu_strategique|point_de_friction|chiffres(?:/(?:0|[1-9][0-9]*)))",
        source.json_pointer,
    )
    if not match:
        raise ValueError(f"Source {source.id} : citer un passage analytique du contenu, pas le profil ou le résumé du Digest.")
    content = report["contents"][int(match.group(1))]
    if source.content_id != content["content_id"]:
        raise ValueError(f"Source {source.id} : identifiant sans lien avec le contenu cité.")
    metadata = next((s for s in report["sources"] if s["content_id"] == source.content_id), {})
    source.label = str(metadata.get("title") or metadata.get("original_title") or report["subject"])
