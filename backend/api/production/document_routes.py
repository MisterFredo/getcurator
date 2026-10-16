import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from openai import APIConnectionError, APIStatusError
# routes.py must be imported before this module in __init__.py.
from api.production.routes import _require_production_admin
from core.production.document_service import start_document, get_document_job

logger = logging.getLogger(__name__)
router = APIRouter(dependencies=[Depends(_require_production_admin)])


class DocumentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reviewed_plan: str = Field(min_length=1, max_length=150_000)


def execute(action):
    try:
        return {"status": "ok", "job": action()}
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except APIStatusError as exc:
        logger.exception("Document API rejection")
        raise HTTPException(status_code=502, detail=f"OpenAI a refusé la demande (HTTP {exc.status_code}). Consulter les logs.") from exc
    except APIConnectionError as exc:
        logger.exception("Document connection interrupted")
        raise HTTPException(status_code=502, detail="Connexion interrompue. L'acceptation de la demande n'est pas confirmée ; consulter les logs avant de relancer.") from exc
    except Exception as exc:
        logger.exception("Document request failed")
        raise HTTPException(status_code=500, detail="Opération impossible. Consulter les logs avant de relancer.") from exc


@router.post("/{production_id}/documents/jobs", status_code=202)
def create_document_job(production_id: str, payload: DocumentRequest):
    return execute(lambda: start_document(production_id, payload.reviewed_plan))


@router.get("/documents/jobs/{response_id}")
def read_document_job(response_id: str):
    return execute(lambda: get_document_job(response_id))
