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


# --- J-47: the served terminology glossary on the SAME endpoint -----------------------------

# The J-47 step-3 spot-check terms — corroborated against the SERVED /api/methodology payload (the
# independent-corroboration record QA reads, not screenshots alone).
GLOSSARY_SPOT_CHECK_TERMS = {
    "breadth > 50-DMA", "DMA", "rank-IC", "universe", "decile", "MAE", "MFE", "expectancy",
    "hit-rate", "dispersion", "walk-forward", "survivorship bias", "horizon", "excess return",
    "composite", "quantile", "ATR%", "pivot", "invalidation",
    # iter-40 (J-24 / B-201 risk-budget card)
    "overnight-gap profile", "worst 20-day window", "distance-to-invalidation %",
}


def test_methodology_endpoint_serves_glossary_with_at_least_100_terms():
    """The endpoint serves the J-47 glossary on the SAME payload (no new endpoint); the served term count
    is >= 100 and the categories are present in order (the verifiable, corroborable count)."""
    with _client() as client:
        data = client.get("/api/methodology").json()
    glossary = data["glossary"]
    terms = [t for c in glossary["categories"] for t in c["terms"]]
    assert len(terms) >= 100, f"served glossary has {len(terms)} terms; J-47 requires >= 100"
    labels = [c["label"] for c in glossary["categories"]]
    for required in ("Scores & Buckets", "Setups & Patterns", "Regime & Breadth", "Universe & Data",
                     "Forward-testing & Evidence", "Factor Lab & Statistics"):
        assert required in labels


def test_methodology_endpoint_glossary_has_spot_check_terms():
    with _client() as client:
        data = client.get("/api/methodology").json()
    served = {t["term"] for c in data["glossary"]["categories"] for t in c["terms"]}
    missing = GLOSSARY_SPOT_CHECK_TERMS - served
    assert not missing, f"served glossary missing spot-check terms: {sorted(missing)}"


def test_methodology_endpoint_glossary_setups_patterns_single_sourced():
    """The served Setups & Patterns glossary rows are DERIVED from `entries` (same key/meaning), so a
    setup/pattern is served in exactly one place — never a duplicated copy (anti-goal: one catalog)."""
    with _client() as client:
        data = client.get("/api/methodology").json()
    sp = next(c for c in data["glossary"]["categories"] if c["label"] == "Setups & Patterns")
    entry_by_name = {e["name"]: e for e in data["entries"]}
    for row in sp["terms"]:
        assert row["term"] in entry_by_name
        assert row["definition"] == entry_by_name[row["term"]]["meaning"]
        assert row["entry_key"] == entry_by_name[row["term"]]["key"]


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
