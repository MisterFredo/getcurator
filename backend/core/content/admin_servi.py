import re
import uuid
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, date
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin

from google.cloud import bigquery

from config import BQ_PROJECT, BQ_DATASET
from api.content.models import ContentCreate, ContentUpdate

# ============================================================
# TABLE
# ============================================================

TABLE_CONTENT = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT"
)


# ============================================================
# TABLES
# ============================================================

TABLE_CONTENT = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT"

TABLE_CONTENT_TOPIC = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_TOPIC"
TABLE_CONTENT_COMPANY = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_COMPANY"

TABLE_CONTENT_CONCEPT = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_CONCEPT"
TABLE_CONTENT_SOLUTION = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_SOLUTION"
TABLE_CONTENT_RAW = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_RAW"

TABLE_TOPIC = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_TOPIC"
TABLE_COMPANY = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY"
TABLE_CONCEPT = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONCEPT"
TABLE_SOLUTION = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOLUTION"
TABLE_SOURCE = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOURCE"

# ============================================================
# LIST CONTENTS ADMIN move from SERVICE
# ============================================================

def list_contents_admin():

    rows = query_bq(
        f"""
        SELECT
          c.ID_CONTENT,

          -- 🔥 NEW
          c.ID_PRIMARY_COMPANY,

          pc.NAME AS PRIMARY_COMPANY_NAME,

          c.TITLE,
          c.TITLE_EN,

          c.EXCERPT,
          c.EXCERPT_EN,

          c.STATUS,

          c.SOURCE_DATE,
          c.SOURCE_URL,
          c.SOURCE_TITLE,

          c.PUBLISHED_AT,
          c.UPDATED_AT

        FROM `{TABLE_CONTENT}` c

        -- 🔥 NEW
        LEFT JOIN `{TABLE_COMPANY}` pc
          ON c.ID_PRIMARY_COMPANY = pc.ID_COMPANY

        WHERE c.IS_ACTIVE = TRUE

        ORDER BY c.UPDATED_AT DESC
        """
    )

    return [

        {
            "id_content": r["ID_CONTENT"],

            # 🔥 NEW
            "id_primary_company": r.get(
                "ID_PRIMARY_COMPANY"
            ),

            "primary_company_name": r.get(
                "PRIMARY_COMPANY_NAME"
            ),

            "source_url": r.get(
                "SOURCE_URL"
            ),

            "source_title": r.get(
                "SOURCE_TITLE"
            ),

            "title": r["TITLE"],
            "title_en": r["TITLE_EN"],

            "excerpt": r["EXCERPT"],
            "excerpt_en": r["EXCERPT_EN"],

            "status": r["STATUS"],

            "source_date": (

                r["SOURCE_DATE"].isoformat()

                if r.get("SOURCE_DATE")

                else None
            ),

            "published_at": (

                r["PUBLISHED_AT"].isoformat()

                if r.get("PUBLISHED_AT")

                else None
            ),

            "updated_at": (

                r["UPDATED_AT"].isoformat()

                if r.get("UPDATED_AT")

                else None
            ),
        }

        for r in rows
    ]


# ============================================================
# CONTENT STATS move from SERVICE
# ============================================================

def get_content_stats():

    sql = f"""
        SELECT

          COUNT(*) AS TOTAL,

          COUNTIF(
            STATUS = 'DRAFT'
          ) AS TOTAL_DRAFT,

          COUNTIF(
            STATUS = 'READY'
          ) AS TOTAL_READY,

          COUNTIF(
            STATUS = 'PUBLISHED'
          ) AS TOTAL_PUBLISHED,

          COUNTIF(
            STATUS = 'SCHEDULED'
          ) AS TOTAL_SCHEDULED,

          COUNTIF(
            STATUS = 'PUBLISHED'
            AND EXTRACT(YEAR FROM PUBLISHED_AT)
                = EXTRACT(YEAR FROM CURRENT_DATE())
          ) AS TOTAL_PUBLISHED_THIS_YEAR,

          COUNTIF(
            STATUS = 'PUBLISHED'
            AND EXTRACT(YEAR FROM PUBLISHED_AT)
                = EXTRACT(YEAR FROM CURRENT_DATE())
            AND EXTRACT(MONTH FROM PUBLISHED_AT)
                = EXTRACT(MONTH FROM CURRENT_DATE())
          ) AS TOTAL_PUBLISHED_THIS_MONTH

        FROM `{TABLE_CONTENT}`
    """

    rows = query_bq(sql)

    if not rows:

        return {
            "total": 0,
            "total_draft": 0,
            "total_ready": 0,
            "total_published": 0,
            "total_scheduled": 0,

            # 🔥 NEW

            "total_published_this_year": 0,
            "total_published_this_month": 0,
        }

    r = rows[0]

    return {

        "total": r.get("TOTAL", 0),

        "total_draft": r.get("TOTAL_DRAFT", 0),

        "total_ready": r.get("TOTAL_READY", 0),

        "total_published": r.get("TOTAL_PUBLISHED", 0),

        "total_scheduled": r.get("TOTAL_SCHEDULED", 0),

        # 🔥 NEW
        "total_published_this_year": r.get(
            "TOTAL_PUBLISHED_THIS_YEAR",
            0
        ),

        "total_published_this_month": r.get(
            "TOTAL_PUBLISHED_THIS_MONTH",
            0
        ),
    }
