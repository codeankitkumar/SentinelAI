"""AI assistant endpoints."""
from fastapi import APIRouter

from ..assistant import AssistantService
from ..core.deps import _db, AnalystDep
from ..schemas.assistant import AssistantRequest, AssistantResponse

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/query", response_model=AssistantResponse)
def ask(payload: AssistantRequest, _: AnalystDep, db: _db) -> AssistantResponse:
    return AssistantService(db).handle(payload)