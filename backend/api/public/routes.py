from fastapi import APIRouter, HTTPException
import logging
import os
import requests

from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import query_bq

from api.public.models import (
    PublicMembersResponse,
    PublicMemberResponse,
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



