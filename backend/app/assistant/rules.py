"""Rule-based AI assistant provider (offline, deterministic, no cost).

Generates structured, IR-driven guidance for the five supported intents:
explain, summarize, investigate, remediate, report. When an LLM API key is
configured in .env (ASSISTANT_PROVIDER=openai), the OpenAI provider is used
instead via provider.py.
"""
from __future__ import annotations

import textwrap
from typing import Any


def _fmt(prompt: str) -> str:
    return textwrap.dedent(prompt).strip()


def explain_threat(threat_type: str, description: str = "") -> str:
    doc = {
        "port_scan": (
            "A port scan is reconnaissance where an attacker (or legitimate "
            "tooling) probes a host for open services by sending connections to "
            "many ports in sequence. It is frequently the first stage of an "
            "attack chain and can reveal exploitable services."
        ),
        "brute_force": (
            "Brute force / credential stuffing attempts many username/password "
            "combinations against an authentication service (SSH, RDP, FTP, DB)."
            " A successful guess can lead to lateral movement or data exposure."
        ),
        "ddos": (
            "A distributed denial-of-service (DDoS) floods a target with traffic "
            "or requests to exhaust bandwidth, CPU, or connection tables, taking "
            "legitimate users offline."
        ),
        "abnormal": (
            "Abnormal traffic is traffic that deviates from an established "
            "baseline for the network — unusual flow asymmetry, protocols, or "
            "destinations. It often indicates data exfiltration, tunneling, or "
            "misconfiguration."
        ),
        "normal": "Benign traffic that falls within expected patterns for the network.",
    }
    base = doc.get(threat_type, "An unclassified network event.") 
    return _fmt(
        f"{base}\n\n"
        f"Detected details: {description or 'No additional description provided.'}"
    )


def investigate_steps(alert: dict | None) -> list[str]:
    if alert is None:
        return [
            "Confirm the source and destination IPs belong to the environment.",
            "Filter netflow/packet captures for the involved 5-tuple.",
            "Check adjacent events and correlation with login or service logs.",
        ]
    src = alert.get("source_ip")
    dst = alert.get("dst_ip")
    rule = alert.get("rule_name")
    steps = [
        f"Open the entity page for {src} and inspect its full history in SentinelAI.",
        f"Drill into flows toward {dst or '<unknown>'} and verify the protocol/port mix.",
        f"Cross-check the '{rule}' rule with IDS/firewall logs outside SentinelAI.",
        "Check whether the source IP is on internal allow/deny lists.",
        "Look for other impacted hosts or lateral movement from the same source.",
    ]
    return steps


def remediate(alert: dict | None, threat_type: str = "") -> list[str]:
    steps = ["Contain the source IP at firewall/network ACL (if attack is confirmed)."]
    if "brute" in threat_type or "brute" in str(alert):
        steps += [
            "Enforce strong password policy and multi-factor authentication on the target service.",
            "Enable account lockout and rate limiting; review and rotate affected credentials.",
        ]
    if "ddos" in threat_type or "scan" in threat_type:
        steps += [
            "Apply rate limiting and geo/ASN filtering at the edge.",
            "Scale out or enable anti-DDoS / Web Application Firewall protections.",
        ]
    steps += [
        "Preserve evidence and packet captures for the investigation.",
        "Document findings and timeline in the incident record.",
        "Harden the affected service and review detection coverage.",
    ]
    return steps


def summarize_incident(incident: dict) -> str:
    n = incident.get("alert_count", 0)
    title = incident.get("title", "Untitled incident")
    sev = incident.get("severity", "medium")
    status = incident.get("status", "open")
    detail = ("Review the linked alerts for IOCs and affected assets." if n
              else "No alerts linked yet — attach evidence as the investigation proceeds.")
    return _fmt(
        f"Incident '{title}' is currently {status} with severity '{sev}'. "
        f"It aggregates {n} alert(s). {detail}"
    )


def build_report(incident: dict, notes: list[dict], linked_alerts: list[dict]) -> str:
    lines = [
        "# SentinelAI Incident Report",
        "",
        f"**Title:** {incident.get('title')}",
        f"**Severity:** {incident.get('severity')}",
        f"**Status:** {incident.get('status')}",
        f"**Assignee:** {incident.get('assignee') or 'unassigned'}",
        "",
        f"**Description:** {incident.get('description') or 'No description.'}",
        "",
        "## Summary",
    ]
    lines.append(summarize_incident(incident))
    lines.append("")
    lines.append("## Linked Alerts")
    if linked_alerts:
        for a in linked_alerts[:20]:
            lines.append(f"- [{a.get('severity')}] {a.get('title')} ({a.get('rule_name')})")
    else:
        lines.append("- (none)")
    lines.append("")
    lines.append("## Investigation Notes")
    if notes:
        for note in notes[:50]:
            lines.append(f"- ({note.get('author_name', 'analyst')}) {note.get('content')}")
    else:
        lines.append("- (no notes yet)")
    lines.append("")
    lines.append("## Recommended Next Steps")
    for s in remediate(None, incident.get('severity', '')):
        lines.append(f"- {s}")
    return "\n".join(lines)