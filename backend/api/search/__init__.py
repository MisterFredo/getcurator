from fastapi import APIRouter
from api.content.routes import router as content_routes

router = APIRouter()
router.include_router(content_routes)
