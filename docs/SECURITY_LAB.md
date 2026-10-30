# Authorized Lab & Network Capture

SentinelAI can collect live network traffic, but **only from networks you are
explicitly authorized to monitor**. Capturing or testing against networks you
do not own or have permission to monitor may violate law and acceptable-use
policies. This document describes how to operate in an isolated lab.

## Ethical & legal guardrails

- Only capture traffic on networks you own, or for which you hold written
  authorization (e.g., your own lab VLAN, CTF boxes you control, or a sandbox
  you administer).
- Do **not** run port scans, brute-force, or DDoS simulation against third
  parties. All attack-generation in this project is synthetic/demo data.
- The included ML sample dataset is **synthetic**. If you use public datasets
  (CIC-IDS2017, UNSW-NB15), follow their licenses and use them for research.

## How SentinelAI limits risk

- Live capture is **disabled by default**. `NETWORK_MONITOR_ENABLED=false`.
- The `/api/monitor/capture` endpoint refuses to run unless capture is enabled.
- A configurable `MONITOR_ALLOWED_CIDRS` setting lets you restrict analysis to
  specific ranges (empty = all, usable only when capture is enabled).
- The Scapy module is imported **lazily** and only when capture is enabled.

## Enabling capture (authorized lab only)

1. Isolate a lab network (e.g., a private VM network with no route to the
   internet or to production).
2. Run SentinelAI with privileges required by your capture interface
   (root/sudo on Linux; Administrator on Windows; Docker `--network host`).
3. Set in `.env` or compose environment:

   ```
   NETWORK_MONITOR_ENABLED=true
   MONITOR_INTERFACE=any          # or your NIC, e.g. eth0, enp0s3
   MONITOR_ALLOWED_CIDRS=10.0.0.0/24
   ```

4. Ensure `captures/` is present and that any `.pcap` output is stored only in
   authorized locations; `.gitignore` excludes `captures/` from commits.

## Capturing responsibly

- Keep capture sessions short and scoped.
- Never store production credentials or private communications in the repo.
- Delete raw captures after analysis; the platform stores derived metrics, not
  packet payloads by default.
- If you must record full payloads for analysis, keep them encrypted and
  outside version control.

## Demonstration without a network

For demos and CI, use the built-in synthetic data instead of live capture:

- `SEED_DEMO_DATA=true` seeds ~2000 synthetic events and alerts on first boot.
- The **Network Monitor** page lets an admin simulate a single flow
  (`POST /api/monitor/simulate`) using RFC 5737 TEST-NET IPs
  (198.51.100.x, 203.0.113.x, 192.0.2.x) so no real host is involved.
- `ml/generate_sample_data.py` creates the offline training dataset.

## Definitions

| Term | Meaning |
|------|---------|
| TEST-NET | RFC 5737 documentation ranges reserved for examples/lab use |
| Authorized lab | A network you own or have written permission to monitor |
| Synthetic data | Programmatically generated flows labelled by class |