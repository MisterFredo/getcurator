# backend/core/knowledge/cockpit_service.py

from .cockpit_repository import (
    get_dashboard,
    list_entities,
)


def get_dashboard_service():
    return get_dashboard()


def list_entities_service():
    return list_entities()
