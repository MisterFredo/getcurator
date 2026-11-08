# backend/api/contact/__init__.py

from fastapi import APIRouter
from api.contact.routes import router as contact_routes

router = APIRouter()
router.include_router(contact_routes)
