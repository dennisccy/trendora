# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 11. Shown in full: 11.

```diff
diff --git a/apps/backend/app/config.py b/apps/backend/app/config.py
index c953b34d..03189bf6 100644
--- a/apps/backend/app/config.py
+++ b/apps/backend/app/config.py
@@ -57,6 +57,13 @@ class UniverseCfg(BaseModel):
     model_config = ConfigDict(extra="allow")
     symbols: list[str] = Field(min_length=1)
     filters: UniverseFilters
+    # goal-market-compass iter-1 (J-01): RAW `universe_pool.csv` sector name -> a valid `etfs.sector`
+    # name — a normalization seam for the pool-CSV sector fallback
+    # (`app.engine.universe_screen.resolve_pool_sector`), for a future pool refresh whose sector
+    # spelling doesn't match one of `etfs.sector`'s 11 names. Default empty: today's 11 pool sector
+    # names already equal `etfs.sector`'s 11 names verbatim, so the fallback starts as a straight,
+    # un-aliased read (TC-6 proves the no-op) — never populated speculatively.
+    pool_sector_aliases: dict[str, str] = Field(default_factory=dict)
 
     @model_validator(mode="after")
     def _validate(self) -> "UniverseCfg":
@@ -1793,6 +1800,11 @@ class UniverseSelectionCfg(BaseModel):
 
     model_config = ConfigDict(extra="allow")
     membership_rule: str
+    # goal-market-compass iter-1 (J-01): the two-source stock-sector-label disclosure — curated
+    # `config.stock_sectors` first, the `universe_pool.csv` fallback second, and the current-only
+    # limitation (no point-in-time sector history; B-114 stays open). Plain prose resolved live, like
+    # `membership_rule` — never re-typed in the engine/frontend.
+    sector_basis: str
     thresholds: list[MethodologyThreshold] = Field(min_length=1)
 
 
diff --git a/apps/backend/app/engine/methodology.py b/apps/backend/app/engine/methodology.py
index 046807a1..2399f8a4 100644
--- a/apps/backend/app/engine/methodology.py
+++ b/apps/backend/app/engine/methodology.py
@@ -139,11 +139,18 @@ def _universe_selection(config: Config) -> dict:
     pool, NOT date-scoped, since methodology describes the rule, not a snapshot); `candidate_pool_size`
     is the same read for clarity. The as-of-DEPENDENT resolved member count (members-resolved-at-D) is
     served on `GET /api/data` (`universe_count` / `universe_diagnostic`) — pointed to via `per_date_note`.
-    The API/frontend reads this verbatim; neither recomputes membership."""
+    The API/frontend reads this verbatim; neither recomputes membership.
+
+    `sector_basis` (J-01, goal-market-compass iter-1) is the two-source stock-sector-label disclosure
+    (curated `config.stock_sectors` first, `universe_pool.csv` fallback second, current-only
+    limitation) — config prose, resolved live exactly like `membership_rule`."""
     section = config.methodology.universe_selection
     candidate_size = len(config.universe.symbols)
     return {
         "membership_rule": section.membership_rule,
+        # J-01 (goal-market-compass iter-1): the two-source stock-sector-label disclosure — config
+        # prose, resolved live like `membership_rule` (never re-typed here).
+        "sector_basis": section.sector_basis,
         "thresholds": [_threshold_row(threshold, config) for threshold in section.thresholds],
         # the candidate-universe (static pool) size — read once, here and on /api/data
         # (`candidate_universe_count`), so the two surfaces never drift (single source, no recompute).
diff --git a/apps/backend/app/engine/scoring.py b/apps/backend/app/engine/scoring.py
index 65b19e9c..8414865e 100644
--- a/apps/backend/app/engine/scoring.py
+++ b/apps/backend/app/engine/scoring.py
@@ -46,6 +46,7 @@ from app.engine.prices import bars_asof, bars_asof_window, closes, highs, lows,
 from app.engine.regime import score_regime
 from app.engine.sectors import score_sectors
 from app.engine.universe_resolver import resolve_members
+from app.engine.universe_screen import pool_sector_map
 from app.engine.setups import classify_setup
 from app.engine.themes import basket_return, theme_name, total_return
 from app.models import Sector, Stock
@@ -293,6 +294,16 @@ def score_stocks(session: Session, asof: date_cls, config: Optional[Config] = No
     sector_result = score_sectors(session, asof, cfg)
     sector_score_by_etf = {row["ticker"]: row["score"] for row in sector_result["rows"]}
 
+    # J-01 (goal-market-compass iter-1): the DESCRIPTIVE pool-CSV sector fallback — computed ONCE
+    # here, never per-stock. Completely separate from `stock_sector_etf` below (which feeds
+    # `rs_sector` / sector_strength scoring) and from `sector_score_by_etf` above (the sector ETF's
+    # own score) — this map only fills the row's display-only `"sector"` field below when
+    # `cfg.stock_sectors` has no entry for the ticker (curated map always wins; TC-4 proves this
+    # touches no score/bucket/setup_status).
+    pool_sectors = pool_sector_map(
+        aliases=cfg.universe.pool_sector_aliases, valid_sectors=cfg.etfs.sector.values()
+    )
+
     # resolve each stock's sector ETF (Stock.sector_id -> Sector.etf_ticker) for rs_sector / sector_strength
     sector_etf_by_id = {s.id: s.etf_ticker for s in session.exec(select(Sector)).all()}
     stock_sector_etf = {
@@ -442,7 +453,9 @@ def score_stocks(session: Session, asof: date_cls, config: Optional[Config] = No
         rows.append({
             "ticker": ticker,
             "name": ticker,
-            "sector": cfg.stock_sectors.get(ticker),
+            # J-01: curated map first, the pool-CSV fallback second — descriptive only, never a score
+            # input; a name absent from both stays None (renders "Unassigned"), never fabricated.
+            "sector": cfg.stock_sectors.get(ticker) or pool_sectors.get(ticker),
             "leadership": leadership,
             "entry_quality": entry_quality,
             "risk": risk,
diff --git a/apps/backend/app/engine/universe_screen.py b/apps/backend/app/engine/universe_screen.py
index 0c1acc97..685950af 100644
--- a/apps/backend/app/engine/universe_screen.py
+++ b/apps/backend/app/engine/universe_screen.py
@@ -15,6 +15,7 @@ NOT a hand-picked list).
 from __future__ import annotations
 
 import csv
+from collections.abc import Iterable, Mapping
 from pathlib import Path
 
 # app/engine/universe_screen.py -> app/engine -> app -> backend ; the committed pool lives under data/seed.
@@ -100,3 +101,45 @@ def read_pool(seed_dir: Path | None = None) -> list[dict]:
             if row.get("symbol"):
                 out.append({"symbol": row["symbol"], "sector": row.get("sector"), "source": row.get("source")})
     return out
+
+
+# --- J-01 (goal-market-compass iter-1): the pool-CSV sector fallback ------------------------------
+# `scoring.score_stocks` reads `cfg.stock_sectors` FIRST (the curated 122-name mapping — untouched by
+# this module) and falls back to `pool_sector_map`'s result only when a resolved-at-D member has no
+# curated entry. Both helpers read NO config of their own (mirrors `screen_reasons` above) — the
+# caller passes the resolved `universe.pool_sector_aliases` / `etfs.sector` values, so this module
+# stays a pure normalization seam, never a second config reader.
+
+def resolve_pool_sector(
+    raw_sector: str | None, *, aliases: Mapping[str, str], valid_sectors: Iterable[str]
+) -> str | None:
+    """Normalize ONE `universe_pool.csv` raw sector name through the caller's alias map (identity
+    today — no alias entry resolves anything yet) and validate the normalized name is a member of the
+    caller's valid sector set (`etfs.sector`'s values). A missing/blank raw sector, or one that fails
+    alias+validity resolution, returns `None` — never raises, never a fabricated or stray sector
+    string (AG-8 resilience; honesty: NA over fabrication)."""
+    if not raw_sector:
+        return None
+    normalized = aliases.get(raw_sector, raw_sector)
+    return normalized if normalized in set(valid_sectors) else None
+
+
+def pool_sector_map(
+    *, aliases: Mapping[str, str], valid_sectors: Iterable[str], seed_dir: Path | None = None
+) -> dict[str, str]:
+    """Ticker -> resolved pool-CSV sector, built ONCE from the SAME `read_pool()` parser (never a
+    second CSV reader) — the pool-CSV fallback half of J-01's two-source sector basis. Only tickers
+    that resolve to a valid sector are present; an unresolvable or missing pool sector is simply
+    absent (the caller's `.get(ticker)` then honestly returns `None` — never a fabricated value). A
+    not-yet-built pool (`FileNotFoundError`) degrades to an empty map, the same honest-empty contract
+    `read_pool`'s other callers already tolerate."""
+    try:
+        pool = read_pool(seed_dir)
+    except FileNotFoundError:
+        return {}
+    out: dict[str, str] = {}
+    for row in pool:
+        resolved = resolve_pool_sector(row.get("sector"), aliases=aliases, valid_sectors=valid_sectors)
+        if resolved is not None:
+            out[row["symbol"]] = resolved
+    return out
diff --git a/apps/backend/tests/test_api_methodology.py b/apps/backend/tests/test_api_methodology.py
index d6b1449a..3a4321ce 100644
--- a/apps/backend/tests/test_api_methodology.py
+++ b/apps/backend/tests/test_api_methodology.py
@@ -4,6 +4,7 @@ Mounts ONLY the methodology router on a bare FastAPI app (NO lifespan) so the te
 and NO walk-forward boot — the endpoint reads config, not a snapshot (iter-10 slow-boot lesson)."""
 from __future__ import annotations
 
+import pytest
 from fastapi import FastAPI
 from fastapi.testclient import TestClient
 
@@ -110,3 +111,24 @@ def test_universe_selection_gated_on_committed_screen_record():
         assert data["universe_selection"]["resolved_size"] >= 1
     else:
         assert "universe_selection" not in data
+
+
+# --- J-01 (goal-market-compass iter-1): the two-source sector-basis disclosure ---------------
+
+def test_universe_selection_sector_basis_served_and_names_both_sources():
+    """TC-5 at the API layer: GET /api/methodology's universe_selection carries `sector_basis` naming
+    both the curated and pool-CSV sources and the current-only limitation. (The deep-equality
+    `test_methodology_endpoint_returns_catalog` above already proves byte-parity with `build_catalog`;
+    this is the explicit, human-readable TC-5 citation.)"""
+    record_present = bool(load_universe_screen_record(DEFAULT_SEED_DIR))
+    if not record_present:
+        pytest.skip("universe_selection is served only once the committed screen record exists")
+    with _client() as client:
+        data = client.get("/api/methodology").json()
+    sector_basis = data["universe_selection"]["sector_basis"]
+    assert isinstance(sector_basis, str) and sector_basis.strip()
+    lowered = sector_basis.lower()
+    assert "stock_sectors" in sector_basis or "curated" in lowered
+    assert "pool" in lowered
+    assert "current" in lowered
+    assert "b-114" in lowered
diff --git a/apps/backend/tests/test_methodology.py b/apps/backend/tests/test_methodology.py
index 85475761..a96eb6ae 100644
--- a/apps/backend/tests/test_methodology.py
+++ b/apps/backend/tests/test_methodology.py
@@ -167,6 +167,34 @@ def test_universe_selection_thresholds_are_live_refs(tmp_path):
     assert by_label["Minimum share price"]["value"] == 25
 
 
+# --- J-01 (goal-market-compass iter-1): the two-source sector-basis disclosure ---------------
+
+def test_universe_selection_sector_basis_present_and_matches_config():
+    """TC-5: the Universe Selection section carries `sector_basis` verbatim from config (plain prose
+    resolved live, like `membership_rule` — never re-typed), naming both sources (curated first,
+    pool-CSV fallback second) and the current-only limitation (B-114 stays open, referenced)."""
+    config = load_config()
+    us = build_catalog(config)["universe_selection"]
+    assert us["sector_basis"] == config.methodology.universe_selection.sector_basis
+    text = us["sector_basis"]
+    assert isinstance(text, str) and text.strip()
+    lowered = text.lower()
+    assert "stock_sectors" in text or "curated" in lowered  # names the curated source first
+    assert "pool" in lowered  # names the pool-CSV fallback source
+    assert "current" in lowered  # states the current-only limitation
+    assert "b-114" in lowered  # references the still-open backlog item
+
+
+def test_sector_basis_is_config_only_no_hard_coded_copy(tmp_path):
+    """Changing `methodology.universe_selection.sector_basis` in config moves the served disclosure
+    with no code change (anti-goal: config-driven UI — the matching-config keystone)."""
+    raw = _committed_raw()
+    raw["methodology"]["universe_selection"]["sector_basis"] = "A distinctive test-only sector basis sentence."
+    config = load_config(_write(tmp_path, raw))
+    us = build_catalog(config)["universe_selection"]
+    assert us["sector_basis"] == "A distinctive test-only sector basis sentence."
+
+
 def test_universe_selection_is_not_a_setup_or_pattern_entry():
     """The Universe Selection section is SEPARATE from the setup/pattern catalog — it must not appear as
     a glossary entry (which would break the completeness assertion / setup-filter vocabulary)."""
diff --git a/apps/backend/tests/test_scoring.py b/apps/backend/tests/test_scoring.py
index 39a2d534..7272521e 100644
--- a/apps/backend/tests/test_scoring.py
+++ b/apps/backend/tests/test_scoring.py
@@ -9,6 +9,8 @@ deterministic; and the as-of date bounds the computation (no lookahead).
 """
 from __future__ import annotations
 
+import json
+
 import pytest
 from sqlmodel import Session, select
 
@@ -19,9 +21,10 @@ from app.engine.indicators import sma
 from app.engine.prices import bars_asof, bars_asof_window, closes, latest_data_date, opens
 from app.engine.scoring import score_stocks
 from app.engine.setups import ALL_STATUSES
-from app.engine.universe_screen import read_pool
+from app.engine.snapshot_serving import resolved_run, stocks_payload
+from app.engine.universe_screen import pool_sector_map, read_pool
 from app.engine.themes import theme_name
-from app.models import DailyPrice
+from app.models import DailyPrice, ScannerResult
 
 SCORE_KEYS = ("leadership", "entry_quality", "risk")
 
@@ -65,9 +68,10 @@ def test_each_stock_has_three_bucketed_explainable_scores(loaded_engine):
         # setup status + reason ride on the same row (single composition path)
         assert row["setup"]["status"] in ALL_STATUSES
         assert isinstance(row["setup"]["reason"], str) and row["setup"]["reason"].strip()
-        # iter-18: broadened-pool names have no `cfg.stock_sectors` mapping, so sector is honestly None
-        # (never a fabricated sector — pool-sector surfacing is J-13/J-14, out of scope). Config-universe
-        # names still carry a valid mapped sector.
+        # J-01 (goal-market-compass iter-1): broadened-pool names with no `cfg.stock_sectors` mapping
+        # now resolve their sector via the pool-CSV fallback (see
+        # test_pool_sector_fallback_lifts_coverage_at_or_above_95_percent below) — a name absent from
+        # BOTH sources still serves an honest None, never a fabricated sector.
         assert row["sector"] is None or row["sector"] in set(cfg.etfs.sector.values())
 
 
@@ -495,3 +499,112 @@ def test_asof_bounds_the_computation_no_lookahead(loaded_engine):
     assert late_result["asof_date"] == latest.isoformat()
     # a different as-of window yields a different canonical result (the as-of bound is wired in)
     assert early_result["rows"] != late_result["rows"]
+
+
+# --- J-01 (goal-market-compass iter-1): the pool-CSV sector fallback --------------------------
+
+def _score_snapshot(rows):
+    """The score-path signature EXCLUDING `sector` — leadership/entry_quality/risk score+bucket and
+    setup_status. Mirrors the proven `test_risk_budget_values_ride_the_row_but_enter_no_score` /
+    `test_volatility_values_ride_the_row_but_enter_no_score` invariance-proof shape."""
+    return {
+        r["ticker"]: (
+            r["leadership"]["score"], r["leadership"]["bucket"],
+            r["entry_quality"]["score"], r["entry_quality"]["bucket"],
+            r["risk"]["score"], r["risk"]["bucket"],
+            r["setup"]["status"],
+        )
+        for r in rows
+    }
+
+
+def test_pool_sector_fallback_never_changes_any_score_bucket_or_setup(loaded_engine, monkeypatch):
+    """TC-4 (byte-identity fixture): the pool-CSV sector fallback is DESCRIPTIVE ONLY. Force it off
+    (`app.engine.scoring.pool_sector_map` -> empty, the pre-iteration `cfg.stock_sectors`-only
+    resolution) and assert every row's leadership/entry_quality/risk score+bucket and setup_status are
+    BYTE-IDENTICAL to the real (fallback-on) run. `Stock.sector_id` / `stock_sector_etf` / `rs_sector`
+    (scoring.py:296-331) are a completely separate machinery this change never touches."""
+    cfg = load_config()
+    with Session(loaded_engine) as session:
+        asof = latest_data_date(session)
+        with_fallback_rows = score_stocks(session, asof, cfg)["rows"]
+        with_fallback = _score_snapshot(with_fallback_rows)
+
+        # force the pool-CSV fallback off — the pre-iteration cfg.stock_sectors-only resolution
+        monkeypatch.setattr("app.engine.scoring.pool_sector_map", lambda *a, **k: {})
+        without_fallback_rows = score_stocks(session, asof, cfg)["rows"]
+        without_fallback = _score_snapshot(without_fallback_rows)
+
+    assert with_fallback == without_fallback  # the fallback moved not one score/bucket/setup_status
+
+    # the fallback DID change sector coverage (proving the monkeypatch and the real code both ran)
+    with_fallback_sectors = {r["ticker"]: r["sector"] for r in with_fallback_rows}
+    without_fallback_sectors = {r["ticker"]: r["sector"] for r in without_fallback_rows}
+    assert with_fallback_sectors != without_fallback_sectors
+    newly_covered = [
+        t for t in with_fallback_sectors
+        if with_fallback_sectors[t] is not None and without_fallback_sectors[t] is None
+    ]
+    assert newly_covered, "expected at least one pool-only ticker to gain a sector under the fallback"
+
+
+def test_pool_sector_fallback_lifts_coverage_at_or_above_95_percent(loaded_engine):
+    """TC-1 (engine-level companion to the browser-level check): on a freshly-scored run under this
+    iteration's code, at most 5% of resolved members serve `sector: None` (down from the
+    pre-iteration 78.4%)."""
+    cfg = load_config()
+    with Session(loaded_engine) as session:
+        asof = latest_data_date(session)
+        rows = score_stocks(session, asof, cfg)["rows"]
+    assert rows
+    unassigned = sum(1 for r in rows if r["sector"] is None)
+    share = unassigned / len(rows)
+    assert share <= 0.05, f"{unassigned}/{len(rows)} rows Unassigned ({share:.1%}) — expected <= 5%"
+
+
+def test_pool_sector_fallback_prefers_curated_map_when_both_resolve(loaded_engine):
+    """Curated `config.stock_sectors` wins over the pool-CSV fallback for every curated ticker (the
+    plan's ordering: curated first, pool-CSV fallback second) — spot-checked against a real curated
+    universe member."""
+    cfg = load_config()
+    with Session(loaded_engine) as session:
+        asof = latest_data_date(session)
+        rows = score_stocks(session, asof, cfg)["rows"]
+    curated_ticker = next(t for t in cfg.stock_sectors if t in {r["ticker"] for r in rows})
+    row = _row(rows, curated_ticker)
+    assert row["sector"] == cfg.stock_sectors[curated_ticker]
+
+
+def test_historical_row_sector_not_rewritten_by_pool_fallback(loaded_engine):
+    """TC-8: a `ScannerResult` row already persisted keeps its STORED sector forever — the read path
+    (`stocks_payload`, GET /api/stocks) serves `record_json` verbatim and never recomputes
+    `score_stocks` (anti-goal: Snapshots immutable). Simulated by rewinding one ALREADY-STORED
+    pool-only row to its honest pre-iteration value (`sector: None`) even though the pool-CSV
+    fallback would now resolve it to a real sector — the served row must still read the STORED None,
+    proving storage (not live recompute) is what /api/stocks serves."""
+    cfg = load_config()
+    with Session(loaded_engine) as session:
+        run = resolved_run(session, None)
+        pool_sectors = pool_sector_map(
+            aliases=cfg.universe.pool_sector_aliases, valid_sectors=cfg.etfs.sector.values()
+        )
+        results = session.exec(select(ScannerResult).where(ScannerResult.run_id == run.id)).all()
+        # a pool-only ticker (uncurated) the fallback resolves to a real sector TODAY
+        target = next(
+            r for r in results
+            if r.ticker not in cfg.stock_sectors and pool_sectors.get(r.ticker) is not None
+        )
+        assert target.sector is not None  # sanity: currently stored WITH the fallback applied
+
+        # rewind this ALREADY-STORED row to the honest pre-iteration value
+        record = json.loads(target.record_json)
+        record["sector"] = None
+        target.record_json = json.dumps(record)
+        target.sector = None
+        session.add(target)
+        session.commit()
+
+        served = stocks_payload(session, run)
+        served_row = next(r for r in served["rows"] if r["ticker"] == target.ticker)
+
+    assert served_row["sector"] is None  # served exactly as stored, never re-resolved
diff --git a/apps/backend/tests/test_universe_screen.py b/apps/backend/tests/test_universe_screen.py
index d85f9502..ee2c257c 100644
--- a/apps/backend/tests/test_universe_screen.py
+++ b/apps/backend/tests/test_universe_screen.py
@@ -13,6 +13,7 @@ Two layers:
 """
 from __future__ import annotations
 
+import csv
 import json
 
 import pytest
@@ -21,7 +22,7 @@ from sqlmodel import Session, select
 from app.config import load_config
 from app.engine.data_manager import compute_coverage
 from app.engine.methodology import build_catalog
-from app.engine.universe_screen import read_pool
+from app.engine.universe_screen import pool_sector_map, read_pool, resolve_pool_sector
 from app.models import Stock
 from app.seed_loader import DEFAULT_SEED_DIR, load_universe_screen_record
 from scripts.screen_universe import screen_reasons
@@ -143,3 +144,103 @@ def test_stock_market_cap_read_from_committed_record(loaded_engine):
             assert stock.market_cap == expected_cap, (
                 f"{ticker} stored market_cap {stock.market_cap} != committed record {expected_cap}"
             )
+
+
+# --- J-01 (goal-market-compass iter-1): the pool-CSV sector fallback ------------------------------
+# `resolve_pool_sector` (one raw name -> a validated sector or None) and `pool_sector_map` (the whole
+# pool, ticker -> resolved sector) are the SINGLE normalization seam `scoring.score_stocks` reads
+# AFTER the curated `config.stock_sectors` map (curated always wins — see test_scoring.py's
+# byte-identity fixture for proof the fallback never touches a score/bucket/setup_status).
+
+def _write_pool_csv(tmp_path, rows: list[dict]):
+    """A synthetic `universe_pool.csv` under `tmp_path`, in the same shape `read_pool` parses
+    (header `symbol,sector,source`; comment lines stripped by `read_pool` itself, not needed here)."""
+    path = tmp_path / "universe_pool.csv"
+    with path.open("w", newline="") as fh:
+        writer = csv.DictWriter(fh, fieldnames=["symbol", "sector", "source"])
+        writer.writeheader()
+        writer.writerows(rows)
+    return tmp_path
+
+
+def test_resolve_pool_sector_identity_when_no_alias_configured():
+    """TC-6: with no alias entry for a raw pool sector name, the resolved value equals the raw value
+    unchanged — today's REAL behavior (the pool's 11 sector names already equal `etfs.sector`'s 11
+    names verbatim, so `universe.pool_sector_aliases` stays a legitimate empty/no-op map)."""
+    valid = set(load_config().etfs.sector.values())
+    assert "Technology" in valid
+    assert resolve_pool_sector("Technology", aliases={}, valid_sectors=valid) == "Technology"
+
+
+def test_resolve_pool_sector_applies_a_configured_alias():
+    """A configured alias DOES substitute (proving the normalization seam works even though today's
+    real config leaves it empty) — the ALIASED name still has to pass the valid-sectors check."""
+    assert (
+        resolve_pool_sector("Tech", aliases={"Tech": "Technology"}, valid_sectors={"Technology"})
+        == "Technology"
+    )
+
+
+def test_resolve_pool_sector_unresolvable_name_degrades_to_none():
+    """TC-7 (AG-8 resilience): a pool sector name (after alias normalization) that is not a member of
+    `etfs.sector`'s valid set degrades to None — never raises, never serves an unrecognized string."""
+    assert resolve_pool_sector("Not A Real Sector", aliases={}, valid_sectors={"Technology"}) is None
+    # an alias that itself points at an invalid name degrades the same way (never a stray string)
+    assert (
+        resolve_pool_sector("Tech", aliases={"Tech": "Not Real Either"}, valid_sectors={"Technology"})
+        is None
+    )
+
+
+def test_resolve_pool_sector_missing_or_blank_raw_value_is_none():
+    """TC-3 (unit half): a missing/blank raw sector value is honestly None, never fabricated."""
+    assert resolve_pool_sector(None, aliases={}, valid_sectors={"Technology"}) is None
+    assert resolve_pool_sector("", aliases={}, valid_sectors={"Technology"}) is None
+
+
+def test_pool_sector_map_covers_the_real_committed_pool_with_identity_aliases():
+    """TC-6 (map-level, real data): with the REAL config's default-empty `pool_sector_aliases`, every
+    one of the committed pool's 548 rows resolves — the map is a straight, un-aliased read of
+    `universe_pool.csv`'s `sector` column (the pool's 11 sector names already equal `etfs.sector`'s 11
+    verbatim)."""
+    cfg = load_config()
+    assert cfg.universe.pool_sector_aliases == {}  # today's committed config: a genuine no-op default
+    mapping = pool_sector_map(aliases=cfg.universe.pool_sector_aliases, valid_sectors=cfg.etfs.sector.values())
+    pool = read_pool()
+    assert len(pool) == 548
+    assert len(mapping) == len(pool)
+    by_symbol = {row["symbol"]: row["sector"] for row in pool}
+    for symbol, sector in mapping.items():
+        assert sector == by_symbol[symbol]  # identity — no alias substitution applied (TC-6)
+
+
+def test_pool_sector_map_degrades_unresolvable_row_gracefully(tmp_path):
+    """TC-7: a synthetic pool with one row whose sector is outside the valid set is simply absent from
+    the resolved map (never raises, never a stray/unrecognized string) — a normal row alongside it
+    still resolves fine (AG-8: the bad row doesn't take down the whole map)."""
+    seed_dir = _write_pool_csv(
+        tmp_path,
+        [
+            {"symbol": "ZZZFAKE", "sector": "Not A Real Sector", "source": "test"},
+            {"symbol": "ZZZOK", "sector": "Technology", "source": "test"},
+            {"symbol": "ZZZBLANK", "sector": "", "source": "test"},
+        ],
+    )
+    mapping = pool_sector_map(aliases={}, valid_sectors={"Technology"}, seed_dir=seed_dir)
+    assert mapping == {"ZZZOK": "Technology"}
+    assert "ZZZFAKE" not in mapping
+    assert "ZZZBLANK" not in mapping
+
+
+def test_pool_sector_map_ticker_outside_the_pool_is_simply_absent(tmp_path):
+    """TC-3 (map-level): a ticker not present in the pool at all is not a key in the map — the
+    caller's `.get(ticker)` then honestly returns None (never fabricated)."""
+    seed_dir = _write_pool_csv(tmp_path, [{"symbol": "ZZZOK", "sector": "Technology", "source": "test"}])
+    mapping = pool_sector_map(aliases={}, valid_sectors={"Technology"}, seed_dir=seed_dir)
+    assert mapping.get("SOME_UNKNOWN_TICKER") is None
+
+
+def test_pool_sector_map_missing_pool_file_degrades_to_empty_map(tmp_path):
+    """A not-yet-built pool file degrades to an empty map (never a crash) — the same honest-empty
+    contract `read_pool`'s other callers already tolerate for a missing `universe_pool.csv`."""
+    assert pool_sector_map(aliases={}, valid_sectors={"Technology"}, seed_dir=tmp_path) == {}
diff --git a/apps/frontend/app/methodology/page.tsx b/apps/frontend/app/methodology/page.tsx
index 002445cb..04f2bb81 100644
--- a/apps/frontend/app/methodology/page.tsx
+++ b/apps/frontend/app/methodology/page.tsx
@@ -232,8 +232,9 @@ function fmtMoney(value: number): string {
 /** The Universe Selection section (J-22 / J-93) — the membership rule + the three config screen
  *  thresholds (read live from config) + the resolved universe size, plus the J-93 per-as-of-date
  *  membership rule (the `per_date_rule` prose, the `candidate_pool_size` full-pool denominator, and the
- *  `per_date_min_history_bars` warm-up bar count). Mirrors the EntryCard config-backed pattern; no
- *  hard-coded copy or numbers — every value is read verbatim from the GET /api/methodology payload. */
+ *  `per_date_min_history_bars` warm-up bar count), plus the J-01 (goal-market-compass iter-1) two-source
+ *  sector-basis disclosure (`sector_basis`). Mirrors the EntryCard config-backed pattern; no hard-coded
+ *  copy or numbers — every value is read verbatim from the GET /api/methodology payload. */
 function UniverseSelectionCard({ selection }: { selection: UniverseSelection }) {
   return (
     <Card className="space-y-3 p-4" data-testid="universe-selection">
@@ -284,6 +285,14 @@ function UniverseSelectionCard({ selection }: { selection: UniverseSelection })
           trailing bars
         </p>
       </div>
+
+      <div className="space-y-1.5 border-t border-border pt-3" data-testid="universe-sector-basis">
+        <div className="flex flex-wrap items-center gap-2">
+          <p className="text-xs uppercase tracking-wide text-text-faint">Stock sector labels</p>
+          <Badge variant="default">Data basis</Badge>
+        </div>
+        <p className="text-sm text-text-muted">{selection.sector_basis}</p>
+      </div>
     </Card>
   );
 }
diff --git a/apps/frontend/lib/api.ts b/apps/frontend/lib/api.ts
index 432317dd..9d582714 100644
--- a/apps/frontend/lib/api.ts
+++ b/apps/frontend/lib/api.ts
@@ -1283,11 +1283,14 @@ export interface MethodologyEntry {
  *  the per-as-of-date membership rule: `per_date_rule` is the prose for the per-date resolver (the same
  *  candidate pool screened from bars ≤ D only on price + ADV + `per_date_min_history_bars` trailing bars,
  *  market-cap dropped per-date), `candidate_pool_size` is the full candidate-pool denominator, and
- *  `per_date_min_history_bars` is the warm-up bar count. All three are produced by the single canonical
- *  module `methodology._universe_selection` and served by the single `GET /api/methodology`; the frontend
- *  re-formats them only — it never recomputes membership. */
+ *  `per_date_min_history_bars` is the warm-up bar count. `sector_basis` (J-01, goal-market-compass iter-1)
+ *  is the two-source stock-sector-label disclosure (curated `config.stock_sectors` first, the
+ *  `universe_pool.csv` fallback second, plus the current-only limitation). All are produced by the single
+ *  canonical module `methodology._universe_selection` and served by the single `GET /api/methodology`; the
+ *  frontend re-formats them only — it never recomputes membership or resolves a sector. */
 export interface UniverseSelection {
   membership_rule: string;
+  sector_basis: string;
   thresholds: MethodologyThresholdRow[];
   resolved_size: number;
   candidate_pool_size: number;
diff --git a/config.yaml b/config.yaml
index a5fa74fd..84d70737 100644
--- a/config.yaml
+++ b/config.yaml
@@ -270,6 +270,13 @@ universe:
     - GS
     - ABNB
 
+  # goal-market-compass iter-1 (J-01): RAW `universe_pool.csv` sector name -> a valid `etfs.sector`
+  # name — a normalization seam for a future pool refresh whose sector spelling doesn't match
+  # `etfs.sector`'s 11 names. Empty today: the pool's 11 distinct sector names already equal
+  # `etfs.sector`'s 11 names verbatim, so the pool-CSV sector fallback (`scoring.score_stocks`) is a
+  # straight, un-aliased read of `universe_pool.csv`'s `sector` column (TC-6 proves the no-op).
+  pool_sector_aliases: {}
+
 # ----------------------------------------------------------------------------------------
 # ETFs + the volatility index. Loaded into reference tables + daily_prices.
 etfs:
@@ -1404,6 +1411,9 @@ methodology:
   # one canonical `universe.symbols` by build_catalog (a read, not a literal). No hard-coded copy/number.
   universe_selection:
     membership_rule: "The universe is a transparent, reproducible screen — not a hand-picked list. Its candidate pool is the union of the S&P 500 and Nasdaq-100 index constituents (real index memberships) together with Trendora's prior curated names; every candidate is then screened against the liquidity, price, and market-cap filters below from real committed end-of-day data. Only names that pass all three thresholds are members; candidates that fail to fetch or fall below a threshold are omitted, never fabricated. Breadth and walk-forward evidence remain universe-relative and survivorship-biased to the current membership."
+    # goal-market-compass iter-1 (J-01): the two-source stock-sector-label disclosure. Curated first,
+    # pool-CSV fallback second, current-only limitation stated, B-114 referenced as still open.
+    sector_basis: "Each stock's sector label is resolved from two sources, in order: the curated `config.stock_sectors` mapping (Trendora's original universe) first, then — for any name the curated map does not cover — a fallback to the sector recorded in the committed candidate pool (universe_pool.csv). A name present in neither source serves no sector ('Unassigned') — never a fabricated value. Both sources describe the CURRENT sector only: there is no point-in-time sector history, so a stock's sector label at a historical as-of date reflects today's mapping, not necessarily what its sector was on that date (tracked open as backlog item B-114)."
     thresholds:
       - { label: "Minimum market cap", cmp: ">=", ref: "universe.filters.min_market_cap", unit: "$" }
       - { label: "Minimum average daily dollar volume", cmp: ">=", ref: "universe.filters.min_dollar_vol", unit: "$" }
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/goal-session-market-compass-index.html     | 11 +++--
 .../goal-session-market-compass/.engine.lock/epoch |  2 +-
 runs/goal-session-market-compass/.engine.lock/pid  |  2 +-
 runs/goal-session-market-compass/engine.pid        |  2 +-
 runs/goal-session-market-compass/session.json      |  6 +--
 runs/goal-session-market-compass/summary.md        | 55 ++++++++++++++++++++--
 runs/goal-session-market-compass/telemetry.jsonl   | 18 +++++++
 runs/goal-session-market-compass/trace/.next-step  |  2 +-
 runs/goal-session-market-compass/trace/trace.jsonl |  1 +
 9 files changed, 84 insertions(+), 15 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
