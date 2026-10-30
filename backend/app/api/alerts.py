"""Alerts endpoints: list, filter, update (triage)."""
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.orm import Session

from ..core.deps import _db, AnalystDep
from ..models import Alert
from ..schemas import AlertOut, AlertUpdate

router = APIRouter(prefix="/alerts", tags=["alerts"])


def _query(
    db: Session, severity: str | None, status: str | None,
    source_ip: str | None, query: str | None, start, end,
):
    q = db.query(Alert)
    if severity:
        q = q.filter(Alert.severity == severity)
    if status:
        q = q.filter(Alert.status == status)
    if source_ip:
        q = q.filter(Alert.source_ip == source_ip)
    if start:
        q = q.filter(Alert.timestamp >= start)
    if end:
        q = q.filter(Alert.timestamp <= end)
    if query:
        like = f"%{query}%"
        q = q.filter(Alert.title.like(like) | Alert.rule_name.like(like) | Alert.description.like(like))
    return q


@router.get("")
def list_alerts(
    _: AnalystDep,
    db: _db,
    severity: str | None = None,
    status: str | None = None,
    source_ip: str | None = None,
    query: str | None = None,
    start=None,
    end=None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
):
    q = _query(db, severity, status, source_ip, query, start, end)
    total = q.count()
    alerts = q.order_by(Alert.timestamp.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [AlertOut.model_validate(a).model_dump() for a in alerts],
    }


@router.get("/{alert_id}", response_model=AlertOut)
def get_alert(alert_id: int, _: AnalystDep, db: _db) -> Alert:
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.patch("/{alert_id}", response_model=AlertOut)
def update_alert(alert_id: int, payload: AlertUpdate, _: AnalystDep, db: _db) -> Alert:
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        if v is not None:
            setattr(alert, k, v)
    db.commit()
    db.refresh(alert)
    return alert