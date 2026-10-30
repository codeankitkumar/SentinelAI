"""Network events endpoints (analyst+admin)."""
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.orm import Session

from ..core.deps import _db, AnalystDep
from ..models import NetworkEvent
from ..schemas import NetworkEventOut

router = APIRouter(prefix="/events", tags=["events"])


def _query(
    db: Session,
    query: str | None,
    threat_type: str | None,
    severity: str | None,
    start, end,
):
    q = db.query(NetworkEvent)
    if threat_type:
        q = q.filter(NetworkEvent.threat_type == threat_type)
    if severity:
        q = q.filter(NetworkEvent.severity == severity)
    if start:
        q = q.filter(NetworkEvent.timestamp >= start)
    if end:
        q = q.filter(NetworkEvent.timestamp <= end)
    if query:
        like = f"%{query}%"
        q = q.filter(
            NetworkEvent.src_ip.like(like)
            | NetworkEvent.dst_ip.like(like)
            | NetworkEvent.protocol.like(like)
        )
    return q


@router.get("")
def list_events(
    _: AnalystDep,
    db: _db,
    query: str | None = None,
    threat_type: str | None = None,
    severity: str | None = None,
    start=None,
    end=None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
):
    q = _query(db, query, threat_type, severity, start, end)
    total = q.count()
    events = q.order_by(NetworkEvent.timestamp.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [NetworkEventOut.model_validate(e).model_dump() for e in events],
    }


@router.get("/{event_id}", response_model=NetworkEventOut)
def get_event(event_id: int, _: AnalystDep, db: _db) -> NetworkEvent:
    event = db.query(NetworkEvent).filter(NetworkEvent.id == event_id).first()
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event