from fastapi import APIRouter
from api.newsletter.routes import router as newsletter_routes

router = APIRouter()
router.include_router(newsletter_routes)
