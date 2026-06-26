"""J-108 — dev CORS allows the LAN-IP frontend origin so the readiness badge is not stuck "unavailable".

`./scripts/dev.sh` advertises the app at BOTH `http://localhost:<port>` and `http://<LAN_IP>:<port>`.
A browser opened at the LAN-IP origin sends that origin on its `/api/health` request; a localhost-only
`CORS_ORIGINS` list rejects it, so `fetchHealth()` throws and the badge sticks on "Backend unavailable".
The fix widens the DEV CORS allowance via `CORS_ORIGIN_REGEX` (a private-LAN pattern, set by dev.sh).

These tests build a fresh app via `main.create_app()` so the env-driven CORS policy is exercised:
  - with the regex set, the LAN-IP frontend origin IS allowed (the bug is fixed);
  - without it, the LAN-IP origin is NOT allowed (documents the original bug);
  - the readiness states themselves are unchanged (J-108 touches only the request path, not readiness).
"""
from __future__ import annotations

from fastapi.testclient import TestClient

import main

# The SAME private-LAN pattern `./scripts/dev.sh` exports as CORS_ORIGIN_REGEX.
DEV_LAN_REGEX = r"http://(localhost|127\.0\.0\.1|10\.[0-9.]+|172\.(1[6-9]|2[0-9]|3[01])\.[0-9.]+|192\.168\.[0-9.]+)(:[0-9]+)?"

# A representative LAN-IP frontend origin (host:port the dev banner prints), as a browser would send it.
LAN_ORIGIN = "http://192.168.1.50:3217"


def test_cors_allows_lan_ip_frontend_origin_when_regex_set(monkeypatch, loaded_engine):
    """With the dev private-LAN regex set, a request bearing the LAN-IP frontend origin is allowed:
    the CORS middleware echoes that exact origin back in `access-control-allow-origin` (so the browser
    lets `fetchHealth()` read the response and the readiness badge can reach Ready)."""
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3217,http://localhost:3000")
    monkeypatch.setenv("CORS_ORIGIN_REGEX", DEV_LAN_REGEX)
    app = main.create_app()
    with TestClient(app) as client:
        resp = client.get("/api/health", headers={"Origin": LAN_ORIGIN})
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == LAN_ORIGIN


def test_cors_rejects_lan_ip_origin_without_regex(monkeypatch, loaded_engine):
    """Without the dev regex (localhost-only CORS — the original config), the LAN-IP frontend origin is
    NOT echoed back — exactly the bug J-108 fixes. (A localhost origin is still allowed.)"""
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3217,http://localhost:3000")
    monkeypatch.delenv("CORS_ORIGIN_REGEX", raising=False)
    app = main.create_app()
    with TestClient(app) as client:
        blocked = client.get("/api/health", headers={"Origin": LAN_ORIGIN})
        allowed = client.get("/api/health", headers={"Origin": "http://localhost:3217"})
    # The LAN-IP origin is not in the allow-list and there is no regex -> not echoed (browser would block).
    assert blocked.headers.get("access-control-allow-origin") != LAN_ORIGIN
    # A configured localhost origin is still allowed (the same-host dev path is unaffected).
    assert allowed.headers.get("access-control-allow-origin") == "http://localhost:3217"


def test_readiness_states_unchanged(loaded_engine):
    """J-108 changes only the request path (CORS + client base) — the readiness STATES are unchanged:
    exactly the three honest labels, served on the single canonical /api/health."""
    from app.engine.readiness import INITIALIZING, READY, UNAVAILABLE

    assert (READY, INITIALIZING, UNAVAILABLE) == ("ready", "initializing", "unavailable")
    with TestClient(main.app) as client:
        body = client.get("/api/health").json()
    assert body["readiness"] in {"ready", "initializing", "unavailable"}
    # the latest snapshot is produced synchronously before serving, so it is never 'unavailable' here.
    assert body["readiness"] != "unavailable"
