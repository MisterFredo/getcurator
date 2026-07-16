# backend/api/cockpit/__init__.py

from fastapi import APIRouter
from api.cockpit.routes import router as cockpit_routes

router = APIRouter()
router.include_router(cockpit_routes)
