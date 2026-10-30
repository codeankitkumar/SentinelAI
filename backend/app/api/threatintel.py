"""Threat intelligence endpoints."""
from fastapi import APIRouter, Query

from ..core.deps import AnalystDep
from ..schemas.threatintel import ThreatIntelResult
from ..threatintel import ThreatIntelService

router = APIRouter(prefix="/threatintel", tags=["threatintel"])


@router.get("/providers")
def providers(_: AnalystDep) -> dict:
    svc = ThreatIntelService()
    return {"configured": svc.configured_providers()}


@router.get("/lookup/{ip}", response_model=list[ThreatIntelResult])
async def lookup(
    ip: str,
    service: str | None = Query(default=None),
    _: AnalystDep = None,
) -> list[ThreatIntelResult]:
    return await ThreatIntelService().lookup(ip, service)