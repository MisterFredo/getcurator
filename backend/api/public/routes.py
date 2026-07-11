from fastapi import APIRouter, HTTPException
import logging
import os
import requests

from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import query_bq

from api.public.models import (
    DrawerNewsResponse,
    PublicMembersResponse,
    PublicMemberResponse,
    NewsletterSubscribeRequest,
    NewsletterSubscribeResponse,
)

from core.content.service import list_contents, get_content

logger = logging.getLogger(__name__)
router = APIRouter()

# ============================================================
# ANALYSIS — LIST (CURATOR CORE FEED)
# ============================================================

@router.get("/analysis/list")
def list_public_analyses():
    """
    Flux global des analyses (Curator + Ratecard)
    """
    try:
        items = list_contents()
        return {"items": items}

    except Exception:
        logger.exception("Erreur list_public_analyses")
        raise HTTPException(500, "Erreur récupération analyses")


# ============================================================
# ANALYSIS — READ (DRAWER)
# ============================================================

@router.get("/content/{id_content}")
def read_content(id_content: str):
    """
    Lecture détaillée d’une analyse
    """
    try:
        content = get_content(id_content)

        if not content:
            raise HTTPException(404, "Analyse introuvable")

        return content

    except HTTPException:
        raise
    except Exception:
        logger.exception("Erreur read_content")
        raise HTTPException(500, "Erreur lecture analyse")


# ============================================================
# NEWS — READ (DRAWER)
# ============================================================

@router.get("/news/{id_news}", response_model=DrawerNewsResponse)
def read_news(id_news: str):
    """
    Lecture d’une news (drawer)
    """
    try:
        rows = list_news()
        n = next((x for x in rows if x["ID_NEWS"] == id_news), None)

        if not n or n["STATUS"] != "PUBLISHED":
            raise HTTPException(404, "News introuvable")

        return DrawerNewsResponse(
            id_news=n["ID_NEWS"],
            title=n["TITLE"],
            excerpt=n.get("EXCERPT"),
            body=n.get("BODY"),
            published_at=n["PUBLISHED_AT"],
            visual_rect_id=n.get("VISUAL_RECT_ID"),
            company={
                "id_company": n["ID_COMPANY"],
                "name": n["COMPANY_NAME"],
                "media_logo_rectangle_id": n.get(
                    "MEDIA_LOGO_RECTANGLE_ID"
                ),
            },
        )

    except HTTPException:
        raise
    except Exception:
        logger.exception("Erreur read_news")
        raise HTTPException(500, "Erreur lecture news")


# ============================================================
# MEMBERS — LIST
# ============================================================

@router.get("/members", response_model=PublicMembersResponse)
def get_members():
    """
    Liste des partenaires (public)
    """
    try:
        rows = query_bq(
            f"""
            SELECT
                ID_COMPANY,
                NAME,
                DESCRIPTION,
                MEDIA_LOGO_RECTANGLE_ID
            FROM `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY`
            WHERE
                IS_PARTNER = TRUE
                AND IS_ACTIVE = TRUE
            ORDER BY NAME ASC
            """
        )

        return {
            "items": [
                {
                    "id_company": r["ID_COMPANY"],
                    "name": r["NAME"],
                    "description": r.get("DESCRIPTION"),
                    "media_logo_rectangle_id": r.get("MEDIA_LOGO_RECTANGLE_ID"),
                }
                for r in rows
            ]
        }

    except Exception:
        logger.exception("Erreur récupération membres")
        raise HTTPException(500, "Erreur récupération membres")


# ============================================================
# MEMBER — DETAIL + NEWS
# ============================================================

@router.get("/member/{id_company}", response_model=PublicMemberResponse)
def get_member(id_company: str):
    """
    Fiche partenaire + ses news
    """
    try:
        # --- Company
        company_rows = query_bq(
            f"""
            SELECT
                ID_COMPANY,
                NAME,
                DESCRIPTION,
                MEDIA_LOGO_RECTANGLE_ID
            FROM `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY`
            WHERE
                ID_COMPANY = @id
                AND IS_PARTNER = TRUE
                AND IS_ACTIVE = TRUE
            """,
            {"id": id_company},
        )

        if not company_rows:
            raise HTTPException(404, "Partenaire introuvable")

        c = company_rows[0]

        # --- News liées
        news_rows = query_bq(
            f"""
            SELECT
                ID_NEWS,
                TITLE,
                EXCERPT,
                PUBLISHED_AT
            FROM `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_NEWS`
            WHERE
                ID_COMPANY = @id
                AND STATUS = 'PUBLISHED'
            ORDER BY PUBLISHED_AT DESC
            """,
            {"id": id_company},
        )

        return {
            "id_company": c["ID_COMPANY"],
            "name": c["NAME"],
            "description": c.get("DESCRIPTION"),
            "media_logo_rectangle_id": c.get("MEDIA_LOGO_RECTANGLE_ID"),
            "news": [
                {
                    "id_news": n["ID_NEWS"],
                    "title": n["TITLE"],
                    "excerpt": n.get("EXCERPT"),
                    "published_at": n["PUBLISHED_AT"],
                }
                for n in news_rows
            ],
        }

    except HTTPException:
        raise
    except Exception:
        logger.exception("Erreur récupération membre")
        raise HTTPException(500, "Erreur récupération membre")


# ============================================================
# NEWSLETTER — SUBSCRIBE
# ============================================================

@router.post(
    "/newsletter/subscribe",
    response_model=NewsletterSubscribeResponse
)
def subscribe_newsletter(payload: NewsletterSubscribeRequest):
    """
    Inscription newsletter (Brevo)
    """
    try:
        BREVO_API_KEY = os.getenv("BREVO_API_KEY")
        BREVO_LIST_ID_MAIN = os.getenv("BREVO_LIST_ID_MAIN")
        BREVO_LIST_ID_PARTNERS = os.getenv("BREVO_LIST_ID_PARTNERS")

        if not BREVO_API_KEY or not BREVO_LIST_ID_MAIN or not BREVO_LIST_ID_PARTNERS:
            raise HTTPException(500, "Brevo non configuré")

        url = "https://api.brevo.com/v3/contacts"

        data = {
            "email": payload.email,
            "attributes": {
                "PRENOM": payload.first_name,
                "NOM": payload.last_name,
                "SOCIETE": payload.company,
            },
            "listIds": [
                int(BREVO_LIST_ID_MAIN),
                int(BREVO_LIST_ID_PARTNERS),
            ],
            "updateEnabled": True,
        }

        headers = {
            "api-key": BREVO_API_KEY,
            "Content-Type": "application/json",
        }

        response = requests.post(url, json=data, headers=headers)

        if response.status_code not in (200, 201):
            logger.error(response.text)
            raise HTTPException(400, "Erreur inscription newsletter")

        return NewsletterSubscribeResponse(success=True)

    except HTTPException:
        raise
    except Exception:
        logger.exception("Erreur newsletter subscribe")
        raise HTTPException(500, "Erreur inscription newsletter")
