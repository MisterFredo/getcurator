from fastapi import APIRouter

from api.visuals.company import router as company_router
from api.visuals.solution import router as solution_router
from api.visuals.topic import router as topic_router
from api.visuals.source import router as source_router

router = APIRouter()

router.include_router(company_router, prefix="/company")
router.include_router(solution_router, prefix="/solution")
router.include_router(topic_router, prefix="/topic")
router.include_router(source_router, prefix="/source")
