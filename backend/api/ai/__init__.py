from fastapi import APIRouter
from api.ai.routes import router as ai_routes

router = APIRouter()
router.include_router(ai_routes)
