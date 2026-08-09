# backend/api/watch/__init__.py

from fastapi import APIRouter
from api.watch.routes import router as watch_routes

router = APIRouter()
router.include_router(watch_routes)
