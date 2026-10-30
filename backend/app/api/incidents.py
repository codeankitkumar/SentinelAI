"""Incident management: CRUD, notes, and PDF report export."""
from __future__ import annotations

import io
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.orm import Session

from ..core.deps import _db, AnalystDep, UserDep
from ..models import Alert, Incident, IncidentNote
from ..schemas import (
    IncidentCreate,
    IncidentDetail,
    IncidentNoteCreate,
    IncidentNoteOut,
    IncidentOut,
    IncidentUpdate,
)

router = APIRouter(prefix="/incidents", tags=["incidents"])


def _to_out(incident: Incident) -> IncidentOut:
    data = IncidentOut.model_validate(incident).model_dump()
    data["alert_count"] = len(incident.alerts) if incident.alerts else 0
    return IncidentOut(**data)


@router.get("")
def list_incidents(
    _: AnalystDep,
    db: _db,
    severity: str | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
):
    q = db.query(Incident)
    if severity:
        q = q.filter(Incident.severity == severity)
    if status:
        q = q.filter(Incident.status == status)
    total = q.count()
    incidents = q.order_by(Incident.updated_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [_to_out(i) for i in incidents],
    }


@router.post("", response_model=IncidentOut, status_code=201)
def create_incident(payload: IncidentCreate, user: UserDep, db: _db) -> IncidentOut:
    incident = Incident(
        title=payload.title,
        description=payload.description,
        severity=payload.severity,
        status="open",
        created_by=user.id,
        assignee=user.full_name or user.username,
    )
    if payload.alert_ids:
        incident.alerts = db.query(Alert).filter(Alert.id.in_(payload.alert_ids)).all()
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return _to_out(incident)


@router.get("/{incident_id}", response_model=IncidentDetail)
def get_incident(incident_id: int, _: AnalystDep, db: _db) -> IncidentDetail:
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    out = _to_out(incident)
    notes = db.query(IncidentNote).filter(IncidentNote.incident_id == incident.id) \
        .order_by(IncidentNote.created_at).all()
    return IncidentDetail(**out.model_dump(), notes=[IncidentNoteOut.model_validate(n) for n in notes])


@router.patch("/{incident_id}", response_model=IncidentOut)
def update_incident(incident_id: int, payload: IncidentUpdate, user: UserDep, db: _db) -> IncidentOut:
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    data = payload.model_dump(exclude_unset=True)
    alert_ids = data.pop("alert_ids", None)
    if alert_ids is not None:
        incident.alerts = db.query(Alert).filter(Alert.id.in_(alert_ids)).all()
    for k, v in data.items():
        if v is not None:
            setattr(incident, k, v)
    if incident.assignee and not incident.assignee_id:
        incident.assignee_id = user.id
    incident.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(incident)
    return _to_out(incident)


@router.post("/{incident_id}/notes", response_model=IncidentNoteOut, status_code=201)
def add_note(incident_id: int, payload: IncidentNoteCreate, user: UserDep, db: _db) -> IncidentNoteOut:
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    note = IncidentNote(
        incident_id=incident.id,
        author_id=user.id,
        author_name=user.full_name or user.username,
        content=payload.content,
    )
    db.add(note)
    incident.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(note)
    return IncidentNoteOut.model_validate(note)


def _pdf_bytes(incident: Incident, notes: list[IncidentNote]) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = [
        Paragraph(f"<b>SentinelAI Incident Report — #{incident.id}</b>", styles["Title"]),
        Paragraph(incident.title, styles["Heading2"]),
        Paragraph(f"<b>Severity:</b> {incident.severity}", styles["Normal"]),
        Paragraph(f"<b>Status:</b> {incident.status}", styles["Normal"]),
        Paragraph(f"<b>Assignee:</b> {incident.assignee or 'unassigned'}", styles["Normal"]),
        Paragraph(f"<b>Created:</b> {incident.created_at.strftime('%Y-%m-%d %H:%M')}", styles["Normal"]),
        Spacer(1, 0.2 * inch),
        Paragraph("Description", styles["Heading3"]),
        Paragraph(incident.description or "No description provided.", styles["BodyText"]),
        Spacer(1, 0.2 * inch),
        Paragraph("Linked Alerts", styles["Heading3"]),
    ]
    alert_rows = [["ID", "Severity", "Rule", "Title"]]
    for a in incident.alerts or []:
        alert_rows.append([str(a.id), a.severity, a.rule_name, a.title])
    if incident.alerts:
        table = Table(alert_rows, colWidths=[0.5 * inch, 0.8 * inch, 1.6 * inch, 3.2 * inch])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
        ]))
        elements.append(table)
    else:
        elements.append(Paragraph("(no linked alerts)", styles["BodyText"]))
    elements += [Spacer(1, 0.2 * inch), Paragraph("Investigation Notes", styles["Heading3"])]
    for n in notes:
        elements.append(Paragraph(f"<b>{n.author_name}</b> — {n.created_at.strftime('%Y-%m-%d %H:%M')}", styles["Normal"]))
        elements.append(Paragraph(n.content, styles["BodyText"]))
    doc.build(elements)
    return buf.getvalue()


@router.get("/{incident_id}/export", response_class=Response)
def export_incident_pdf(incident_id: int, _: AnalystDep, db: _db) -> Response:
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    notes = db.query(IncidentNote).filter(IncidentNote.incident_id == incident.id) \
        .order_by(IncidentNote.created_at).all()
    pdf = _pdf_bytes(incident, notes)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="incident_{incident.id}.pdf"'},
    )