import os
import sys
import importlib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# -------------------------------------------------------
# PATH FIX
# -------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# -------------------------------------------------------
# APP
# -------------------------------------------------------
app = FastAPI(
    title="Ratecard Backend",
    version="1.2.0",
    description="Ratecard backend API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://ratecard-frontend.onrender.com",
        "https://ratecard-frontend-prod.onrender.com",
        "https://ratecard.fr",

        "https://curator-frontend-zayd.onrender.com",
        "https://curator-frontend-prod.onrender.com",
        "https://getcurator.ai",
        "https://www.getcurator.ai",  # 👈 IMPORTANT
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# -------------------------------------------------------
# ROUTER INCLUSION HELPER
# -------------------------------------------------------
def include_router(module_path: str, prefix: str, tag: str):
    """
    Importe dynamiquement un module FastAPI et monte son router.
    Hypothèse : le module expose un attribut `router`.
    """
    mod = importlib.import_module(module_path)
    router = getattr(mod, "router")
    app.include_router(router, prefix=prefix, tags=[tag])

# -------------------------------------------------------
# MODULE REGISTRATION
# -------------------------------------------------------

# --- HEALTH
include_router("api.health", "/api/health", "HEALTH")

# --- ADMIN / PRODUCTION
include_router("api.content", "/api/content", "CONTENT")
include_router("api.news", "/api/news", "NEWS")
include_router("api.company", "/api/company", "COMPANY")
include_router("api.person", "/api/person", "PERSON")
include_router("api.topic", "/api/topic", "TOPIC")
include_router("api.solution", "/api/solution", "SOLUTION")
include_router("api.concept", "/api/concept", "CONCEPT")
include_router("api.matching", "/api/matching", "MATCHING")
include_router("api.curator", "/api/curator", "CURATOR")
include_router("api.event", "/api/event", "EVENT")
include_router("api.source", "/api/source", "SOURCE")
include_router("api.universe", "/api/universe", "UNIVERSE")
include_router("api.search", "/api/search", "SEARCH")
include_router("api.vector", "/api/vector", "VECTOR")
include_router("api.insight", "/api/insight", "INSIGHT")
include_router("api.workspace", "/api/workspace", "WORKSPACE")
include_router("api.synthesis", "/api/synthesis", "SYNTHESIS")

# --- FRONT PUBLIC (MEDIA)
include_router("api.public", "/api/public", "PUBLIC")

# --- ADMIN AUTH
include_router("api.admin", "/api/admin", "ADMIN")
include_router("api.user", "/api/user", "USER")
include_router("api.mcp", "/api/mcp", "MCP")
include_router("api.radar", "/api/radar", "RADAR")
include_router("api.numbers", "/api/numbers", "NUMBERS")

# --- SUPPORT
include_router("api.visuals", "/api/visuals", "VISUALS")

# -------------------------------------------------------
# ROOT
# -------------------------------------------------------
@app.get("/")
def root():
    return {
        "service": "ratecard-backend",
        "status": "ok",
        "version": "1.2.0",
        "modules": [
            "content",
            "content_read",
            "news",
            "event",
            "topic",
            "company",
            "person",
            "synthesis",
            "public",
            "visuals",
        ]
    }

# -------------------------------------------------------
# ROUTES DEBUG
# -------------------------------------------------------
@app.get("/__routes")
def list_routes():
    """
    Debug helper: liste toutes les routes montées.
    Utile pour vérifier l’enregistrement Render.
    """
    return {
        "routes": [
            {
                "path": r.path,
                "methods": list(r.methods or [])
            }
            for r in app.router.routes
        ]
    }
