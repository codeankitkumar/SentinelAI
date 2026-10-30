"""Threat intelligence integrations (AbuseIPDB, VirusTotal).

These call third-party APIs. Respect their rate limits and terms of service;
keys are optional. When disabled, the API returns a clear "not configured"
message instead of silently failing.
"""
from .service import ThreatIntelService

__all__ = ["ThreatIntelService"]