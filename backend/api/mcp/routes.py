from fastapi import APIRouter
from pydantic import BaseModel

# MCP core
from core.mcp.intent import detect_intent
from core.mcp.entity import resolve_entity

# handlers enrichissement
from core.mcp.handlers.topic import handle_topic
from core.mcp.handlers.company import handle_company
from core.mcp.handlers.numbers import handle_numbers
from core.mcp.handlers.benchmark import handle_benchmark

# moteur recherche
from core.curator.service import search

# insight + suggestions
from core.mcp.suggestions import build_suggestions


router = APIRouter()


class MCPQuery(BaseModel):
    query: str


# ============================================================
# CLEAN QUERY (NON DESTRUCTIF)
# ============================================================

def clean_query(q: str) -> str:

    q = q.lower()

    noise = [
        "👉",
        "donne moi",
        "parle moi de",
        "je veux",
        # ⚠️ volontairement retiré :
        # "analyse", "explique", "comprendre"
        # car impact sur intent detection
    ]

    for n in noise:
        q = q.replace(n, "")

    return q.strip()


# ============================================================
# ROUTE MCP
# ============================================================

@router.post("/query")
def mcp_query(body: MCPQuery):

    user_query = body.query

    # ----------------------------------------------------------
    # 🔒 SAFETY
    # ----------------------------------------------------------
    if "call the" in user_query.lower():
        return {
            "status": "error",
            "message": "Invalid query"
        }

    # ----------------------------------------------------------
    # 1. INTENT + ENTITY (PRIORITAIRE)
    # ----------------------------------------------------------
    intent = detect_intent(user_query)
    entity = resolve_entity(user_query)

    # 👉 sécurité entity (CRITIQUE FIX)
    if not entity or entity.get("type") == "unknown":
        entity = {"type": None, "label": None}

    # ----------------------------------------------------------
    # 2. NUMBERS (PRIORITÉ MAX)
    # ----------------------------------------------------------
    if intent == "numbers":

        result = handle_numbers(entity, user_query)

        # 👉 fallback si aucun chiffre trouvé
        if result.get("status") in ["empty", "error"]:
            # on bascule vers search
            cleaned_query = clean_query(user_query)
            search_query = cleaned_query if cleaned_query else user_query

            rows = search(q=search_query, limit=10) or []

            if rows:
                for item in rows:
                    if item.get("type") == "news":
                        item["url"] = f"/news/{item.get('id')}"
                    else:
                        item["url"] = f"/analysis/{item.get('id')}"

                return {
                    "status": "ok",
                    "intent": "search_fallback",
                    "entity": entity,
                    "answer": {
                        "text": "Aucun chiffre précis trouvé, voici les contenus associés :",
                        "items": rows
                    }
                }

        return result

    # ----------------------------------------------------------
    # 3. BENCHMARK
    # ----------------------------------------------------------
    if intent == "benchmark":
        return handle_benchmark(user_query)

    # ----------------------------------------------------------
    # 4. ENTITY (COMPANY / TOPIC)
    # ----------------------------------------------------------
    if entity.get("type") == "company":
        return handle_company(entity)

    if entity.get("type") == "topic":
        return handle_topic(entity)

    # ----------------------------------------------------------
    # 5. SEARCH (FALLBACK INTELLIGENT)
    # ----------------------------------------------------------

    cleaned_query = clean_query(user_query)
    search_query = cleaned_query if cleaned_query else user_query

    rows = search(q=search_query, limit=10) or []

    # fallback si nettoyage trop agressif
    if not rows and cleaned_query != user_query:
        rows = search(q=user_query, limit=10) or []

    # enrichissement URLs
    for item in rows:
        if item.get("type") == "news":
            item["url"] = f"/news/{item.get('id')}"
        else:
            item["url"] = f"/analysis/{item.get('id')}"

    # ----------------------------------------------------------
    # 6. FALLBACK VIDE
    # ----------------------------------------------------------
    if not rows:
        return {
            "status": "ok",
            "intent": "search",
            "entity": {
                "type": "text",
                "label": user_query
            },
            "answer": {
                "text": "Aucune donnée disponible dans Curator pour cette requête.",
                "items": []
            }
        }

    # ----------------------------------------------------------
    # 7. INSIGHT
    # ----------------------------------------------------------
    analysis_ids = [
        r["id"]
        for r in rows
        if r.get("type") == "analysis"
    ]

    analysis_text = None

    if analysis_ids:
        result = run_insight_pipeline(analysis_ids)
        analysis_text = result.get("insight")

    # ----------------------------------------------------------
    # 8. SUGGESTIONS
    # ----------------------------------------------------------
    suggestions = build_suggestions(
        intent="search",
        entity={"label": user_query},
        items=rows
    )

    # ----------------------------------------------------------
    # 9. RESPONSE
    # ----------------------------------------------------------
    return {
        "status": "ok",
        "intent": "search",
        "entity": {
            "type": "text",
            "label": user_query
        },
        "answer": {
            "items": rows,
            "analysis": analysis_text
        },
        "meta": {
            "suggestions": suggestions
        }
    }
