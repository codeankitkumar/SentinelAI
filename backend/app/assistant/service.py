"""Assistant orchestrator deciding between rule-based and LLM providers."""
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..models import Alert, Incident, IncidentNote
from . import rules
from . import provider
from ..schemas.assistant import AssistantRequest, AssistantResponse


class AssistantService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def handle(self, req: AssistantRequest) -> AssistantResponse:
        alert = (self.db.query(Alert).filter(Alert.id == req.alert_id).first()
                 if req.alert_id else None)
        incident = (self.db.query(Incident).filter(Incident.id == req.incident_id).first()
                    if req.incident_id else None)

        intent = req.intent
        prompt = self._context(req)

        if provider.llm_available() and intent in ("explain", "investigate", "remediate"):
            system = (
                "You are SentinelAI, an expert SOC assistant. Be concise, "
                "specific, and safety-focused. Suggest investigation and "
                "remediation steps appropriate for an authorized security lab."
            )
            answer = provider.ask(system, prompt)
            steps = self._steps_for(intent, alert, incident)
            return AssistantResponse(intent=intent, answer=answer, steps=steps)

        answer = self._run_rules(intent, req, alert, incident)
        steps = self._steps_for(intent, alert, incident)
        return AssistantResponse(intent=intent, answer=answer, steps=steps)

    def _context(self, req: AssistantRequest) -> str:
        parts = [f"Query from analyst: {req.query or '(none)'}"]
        if req.source_ip:
            parts.append(f"Source IP of interest: {req.source_ip}")
        if req.alert_id:
            parts.append(f"Alert ID: {req.alert_id}")
        if req.incident_id:
            parts.append(f"Incident ID: {req.incident_id}")
        return "\n".join(parts)

    def _run_rules(self, intent: str, req: AssistantRequest, alert, incident) -> str:
        if intent == "explain":
            if alert is None:
                raise HTTPException(status_code=404, detail="alert_id required for explain")
            return rules.explain_threat(alert.rule_name.lower(), alert.description)
        if intent == "summarize":
            if incident is None:
                raise HTTPException(status_code=404, detail="incident_id required for summarize")
            return rules.summarize_incident(self._incident_dict(incident))
        if intent == "investigate":
            return self._investigate_answer(req, alert)
        if intent == "remediate":
            threat = alert.rule_name.lower() if alert else ""
            steps = rules.remediate(self._alert_dict(alert) if alert else None, threat)
            return "Recommended remediation (analyzer-reviewed):\n- " + "\n- ".join(steps)
        if intent == "report":
            if incident is None:
                raise HTTPException(status_code=404, detail="incident_id required for report")
            notes = self.db.query(IncidentNote).filter(
                IncidentNote.incident_id == incident.id).order_by(IncidentNote.created_at).all()
            alerts = incident.alerts
            return rules.build_report(
                self._incident_dict(incident),
                [{"author_name": n.author_name, "content": n.content} for n in notes],
                [{"severity": a.severity, "title": a.title, "rule_name": a.rule_name} for a in alerts],
            )
        raise HTTPException(status_code=400, detail=f"Unknown intent: {intent}")

    def _investigate_answer(self, req: AssistantRequest, alert):
        steps = self._steps_for("investigate", alert, None)
        return "Recommended investigation steps:\n- " + "\n- ".join(steps) + (
            f"\n\nTarget IP: {req.source_ip or (alert.source_ip if alert else 'unknown')}"
        )

    def _steps_for(self, intent: str, alert, incident) -> list[str]:
        a = self._alert_dict(alert) if alert else None
        if intent == "investigate":
            return rules.investigate_steps(a)
        if intent == "remediate":
            threat = (alert.rule_name or "").lower() if alert else ""
            return rules.remediate(a, threat)
        return []

    @staticmethod
    def _alert_dict(alert: Alert) -> dict:
        return {
            "id": alert.id,
            "title": alert.title,
            "rule_name": alert.rule_name,
            "severity": alert.severity,
            "source_ip": alert.source_ip,
            "dst_ip": alert.dst_ip,
        }

    @staticmethod
    def _incident_dict(incident: Incident) -> dict:
        return {
            "id": incident.id,
            "title": incident.title,
            "description": incident.description,
            "severity": incident.severity,
            "status": incident.status,
            "assignee": incident.assignee,
            "alert_count": len(incident.alerts) if incident.alerts else 0,
        }