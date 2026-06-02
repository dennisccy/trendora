"""Methodology API test (iter-12, J-12) — GET /api/methodology returns the config-backed catalog.

Mounts ONLY the methodology router on a bare FastAPI app (NO lifespan) so the test needs NO seeded DB
and NO walk-forward boot — the endpoint reads config, not a snapshot (iter-10 slow-boot lesson)."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import methodology
from app.config import get_config
from app.engine.methodology import build_catalog
from app.seed_loader import DEFAULT_SEED_DIR, load_universe_screen_record


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(methodology.router, prefix="/api")
    return TestClient(app)


def test_methodology_endpoint_returns_catalog():
    with _client() as client:
        resp = client.get("/api/methodology")
        assert resp.status_code == 200
        data = resp.json()
        # The endpoint re-formats config only — entries/intro come from build_catalog verbatim.
        expected = build_catalog(get_config())
        # Honest universe gate (J-22): the universe_selection section is served ONLY when the committed
        # screen record (data/seed/universe.json) exists. Until the offline screen runs, the universe is
        # the prior curated list and MUST NOT be presented as a screen result (anti-goal: Universe screen
        # is reproducible & honest — no hand-curated list masquerading as a screen).
        screen_applied = bool(load_universe_screen_record(DEFAULT_SEED_DIR))
        assert ("universe_selection" in data) == screen_applied
        if not screen_applied:
            expected.pop("universe_selection", None)
        assert data == expected
        assert data["entries"]
        kinds = {e["kind"] for e in data["entries"]}
        assert kinds == {"setup", "pattern"}


def test_methodology_endpoint_documents_vcp():
    with _client() as client:
        data = client.get("/api/methodology").json()
        vcp = next(e for e in data["entries"] if e["key"] == "vcp")
        assert vcp["kind"] == "pattern"
        assert vcp["thresholds"]  # config-referenced VCP thresholds present


def test_universe_selection_gated_on_committed_screen_record():
    """Honest gate (J-22 — anti-goal: Universe screen is reproducible & honest). The API serves the
    universe_selection section ONLY when the committed screen record (data/seed/universe.json) exists.
    Before the offline screen has run, the universe is the prior curated list and MUST NOT be presented
    as a screen result, so the section is absent (the frontend then hides the card). It returns
    automatically — with the real screened members — once the screen runs and commits its record."""
    record_present = bool(load_universe_screen_record(DEFAULT_SEED_DIR))
    with _client() as client:
        data = client.get("/api/methodology").json()
    if record_present:
        assert "universe_selection" in data
        assert data["universe_selection"]["resolved_size"] >= 1
    else:
        assert "universe_selection" not in data
