from fastapi import APIRouter
from api.knowleddge.routes import router as knowledge_routes

router = APIRouter()
router.include_router(knowledge_routes)
