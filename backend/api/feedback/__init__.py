# backend/api/feedback/__init__.py

from fastapi import APIRouter
from api.feedback.routes import router as feedback_routes

router = APIRouter()
router.include_router(feedback_routes)
