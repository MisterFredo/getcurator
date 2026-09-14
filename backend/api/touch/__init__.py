# backend/api/touch/__init__.py

from fastapi import APIRouter
from api.touch.routes import router as touch_routes

router = APIRouter()
router.include_router(touch_routes)
