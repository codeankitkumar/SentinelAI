"""Threat intelligence lookup service using AbuseIPDB and VirusTotal."""
from __future__ import annotations

from datetime import datetime, timezone

import httpx

from ..config import settings
from ..schemas.threatintel import ThreatIntelResult

ABUSEIPDB_URL = "https://api.abuseipdb.com/api/v2/check"
VIRUSTOTAL_URL = "https://www.virustotal.com/api/v3/ip_addresses/{ip}"


class ThreatIntelService:
    def __init__(self) -> None:
        self._headers = {}
        if settings.abuseipdb_api_key:
            self._headers["abuseipdb"] = {"Key": settings.abuseipdb_api_key, "Accept": "application/json"}

    def configured_providers(self) -> list[str]:
        out = []
        if settings.abuseipdb_api_key:
            out.append("abuseipdb")
        if settings.virustotal_api_key:
            out.append("virustotal")
        return out

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    async def lookup(self, ip: str, provider: str | None = None) -> list[ThreatIntelResult]:
        results: list[ThreatIntelResult] = []
        providers = [provider] if provider else self.configured_providers()
        if not providers:
            return [ThreatIntelResult(
                ip=ip, provider="none", found=False,
                note="No threat-intel keys configured. Set ABUSEIPDB_API_KEY / VIRUSTOTAL_API_KEY.",
                queried_at=self._now(),
            )]
        async with httpx.AsyncClient(timeout=12.0) as client:
            if "abuseipdb" in providers:
                results.append(await self._abuseipdb(client, ip))
            if "virustotal" in providers and settings.virustotal_api_key:
                results.append(await self._virustotal(client, ip))
        # Ensure deterministic ordering.
        return [r for r in results if r is not None]

    async def _abuseipdb(self, client: httpx.AsyncClient, ip: str) -> ThreatIntelResult | None:
        try:
            resp = await client.get(
                ABUSEIPDB_URL,
                params={"ipAddress": ip, "maxAgeInDays": 90, "verbose": ""},
                headers=self._headers.get("abuseipdb"),
            )
            if resp.status_code != 200:
                return ThreatIntelResult(
                    ip=ip, provider="abuseipdb", found=False,
                    note=f"HTTP {resp.status_code}: {resp.text[:120]}", queried_at=self._now(),
                )
            data = resp.json().get("data", {})
            found = data.get("abuseConfidenceScore", 0) > 0
            return ThreatIntelResult(
                ip=ip, provider="abuseipdb", found=found,
                data={
                    "abuseConfidenceScore": data.get("abuseConfidenceScore"),
                    "countryCode": data.get("countryCode"),
                    "isp": data.get("isp"),
                    "usageType": data.get("usageType"),
                    "totalReports": data.get("totalReports"),
                    "lastReportedAt": data.get("lastReportedAt"),
                },
                queried_at=self._now(),
            )
        except httpx.HTTPError as exc:
            return ThreatIntelResult(ip=ip, provider="abuseipdb", found=False,
                                     note=f"Request failed: {exc}", queried_at=self._now())

    async def _virustotal(self, client: httpx.AsyncClient, ip: str) -> ThreatIntelResult | None:
        try:
            resp = await client.get(
                VIRUSTOTAL_URL.format(ip=ip),
                headers={"x-apikey": settings.virustotal_api_key},
            )
            if resp.status_code != 200:
                return ThreatIntelResult(
                    ip=ip, provider="virustotal", found=False,
                    note=f"HTTP {resp.status_code} (respect VT rate limits)", queried_at=self._now(),
                )
            data = resp.json().get("data", {})
            attrs = data.get("attributes", {})
            stats = attrs.get("last_analysis_stats", {})
            found = int(stats.get("malicious", 0) or 0) + int(stats.get("suspicious", 0) or 0) > 0
            return ThreatIntelResult(
                ip=ip, provider="virustotal", found=found,
                data={"stats": stats, "country": attrs.get("country"),
                      "as_owner": attrs.get("as_owner")},
                queried_at=self._now(),
            )
        except httpx.HTTPError as exc:
            return ThreatIntelResult(ip=ip, provider="virustotal", found=False,
                                     note=f"Request failed: {exc}", queried_at=self._now())