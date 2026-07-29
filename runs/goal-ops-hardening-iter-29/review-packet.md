# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 7. Shown in full: 7.

```diff
diff --git a/apps/backend/app/engine/evidence.py b/apps/backend/app/engine/evidence.py
index 08093e1f..d21ff81c 100644
--- a/apps/backend/app/engine/evidence.py
+++ b/apps/backend/app/engine/evidence.py
@@ -32,6 +32,7 @@ This module consumes `app.engine.ledger` (read) + `app.engine.referee` (the PASS
 """
 from __future__ import annotations
 
+import logging
 import os
 from pathlib import Path
 from typing import Optional
@@ -42,6 +43,8 @@ from app.config import REPO_ROOT, Config, get_config
 from app.engine.ledger import FORWARD_WALK_TYPE, read_entries
 from app.engine.referee import STATUS_PASS
 
+logger = logging.getLogger("trendora.evidence")
+
 # The environment-variable NAME (the NAME only — never a path VALUE literal in code) the runtime ledger
 # path may be overridden with. Forward-looking; the config default already points at the gate's ledger.
 LEDGER_PATH_ENV = "TRENDORA_LEDGER_PATH"
@@ -134,7 +137,18 @@ def build_evidence_payload(
     phase-conditional drawdown/dry-spell `expectations` payload from
     `app.engine.forward_testing.compute_drawdown_expectations` (an honestly-absent key when that returns
     `None` — an unresolvable cohort or a zero-observation cohort — never a crash, never a fabricated
-    panel)."""
+    panel).
+
+    ops-hardening iter-29 (AG-8): the per-claim compute call is wrapped in an isolate-and-continue guard,
+    mirroring the EXISTING per-claim `MemoryError`-then-continue convention `data_manager.py`'s
+    drawdown-expectations ingest warm loop already uses (`data_manager.py:3361`) — but, unlike that
+    BACKGROUND warm loop (which may abort its remaining claims under memory pressure), this is a LIVE
+    request path: a compute failure (`MemoryError` or any other exception) for one claim NEVER aborts the
+    rest of this response, so it always logs + continues to the next entry, never breaks. On a caught
+    failure that claim's row omits `expectations` and instead carries `expectations_status: "unavailable"`
+    — additive ONLY on the exception path; the pre-existing honest-`None` case (an unresolvable cohort or a
+    zero-observation cohort, returned without raising) is UNCHANGED — no `expectations` key, no
+    `expectations_status` key, exactly as before this iteration."""
     claims: list[dict] = []
     proven_signals: dict[str, dict] = {}
     for entry in read_entries(ledger_path):
@@ -150,9 +164,26 @@ def build_evidence_payload(
             # J-15 latency budget by the claim count (see the cache's own docstring for the measurement).
             from app.engine.forward_testing import compute_drawdown_expectations_cached
 
-            expectations = compute_drawdown_expectations_cached(session, row["claim"], config)
-            if expectations is not None:
-                row["expectations"] = expectations
+            try:
+                expectations = compute_drawdown_expectations_cached(session, row["claim"], config)
+            except MemoryError as exc:
+                # isolate-and-continue (AG-8): unlike the ingest warm loop's break-on-MemoryError, a live
+                # `/evidence` response must still render every OTHER claim — never abort the rest of the
+                # page over one claim's compute pressure.
+                logger.exception(
+                    "evidence per-claim drawdown-expectations compute aborted — memory pressure, "
+                    "continuing to the next claim: %s", exc,
+                )
+                row["expectations_status"] = "unavailable"
+            except Exception as exc:  # noqa: BLE001 — isolate-and-continue: one claim's failure must
+                # never blank the whole /evidence response for every other claim.
+                logger.exception(
+                    "evidence per-claim drawdown-expectations compute failed (non-fatal): %s", exc,
+                )
+                row["expectations_status"] = "unavailable"
+            else:
+                if expectations is not None:
+                    row["expectations"] = expectations
         claims.append(row)
         signal = row["signal"]
         if row["proven"] and signal:
diff --git a/apps/backend/app/engine/research.py b/apps/backend/app/engine/research.py
index 1e041eea..5c48bd4f 100644
--- a/apps/backend/app/engine/research.py
+++ b/apps/backend/app/engine/research.py
@@ -174,6 +174,26 @@ def _extract_factor_value(res: ScannerResult, parsed: dict) -> Optional[float]:
     return None
 
 
+def _fr_slice_map(
+    session: Session, horizon: int, slice_run_ids: list[int], batch: int,
+) -> dict[tuple[int, str], tuple[float, Optional[float]]]:
+    """iter-29 (AG-8): the `(run_id, symbol) -> (realized_return, max_drawdown)` join map for ONE bounded
+    SLICE of run ids — `_factor_observations`'s chunk axis. Column-projected + `yield_per`-streamed exactly
+    like the pre-chunk single-pass read; the only difference is the added `run_id.in_(slice_run_ids)`
+    scope, which is what bounds this dict's LIVE size to (len(slice_run_ids) x symbols-per-run) instead of
+    the full horizon's distinct (run_id, symbol) pair count (803,042 measured live at iter-28, one horizon,
+    as_of=None — an unbounded whole-history materialization in substance, since the prior accumulator held
+    one entry per pair across ALL of `runs_with_fr` at once). A named function (not an inlined loop body)
+    so a test can wrap/instrument it to observe the live per-slice size directly (TC-1)."""
+    fr_stmt = select(
+        ForwardReturn.run_id, ForwardReturn.symbol, ForwardReturn.realized_return, ForwardReturn.max_drawdown
+    ).where(ForwardReturn.horizon == horizon, ForwardReturn.run_id.in_(slice_run_ids))
+    ret_by_run_symbol: dict[tuple[int, str], tuple[float, Optional[float]]] = {}
+    for run_id, symbol, realized_return, max_drawdown in session.exec(fr_stmt).yield_per(batch):
+        ret_by_run_symbol[(run_id, symbol)] = (realized_return, max_drawdown)
+    return ret_by_run_symbol
+
+
 def _factor_observations(
     session: Session, factor, horizon: int, as_of: Optional[date_cls] = None,
     *, cfg: Optional[Config] = None,
@@ -189,32 +209,37 @@ def _factor_observations(
 
     `as_of` (iter-19, J-32) optionally scopes the pool to the EXPANDING WALK-FORWARD WINDOW: when set,
     ONLY snapshots with `ScannerRun.asof_date <= as_of` contribute (no run dated > D leaks). It is a
-    SINGLE membership filter on the `fr_rows` step — identical to `forward_testing.py` — so it equally
-    bounds `runs_with_fr`, `results`, `run_rows`, and the regime map (all derived from it). The cutoff is
-    the canonical `ScannerRun.asof_date` (not the denormalized `ForwardReturn.asof_date`). `as_of=None`
-    adds NO clause → byte-identical all-history."""
+    SINGLE membership filter on the `runs_with_fr` discovery step below — identical to `forward_testing.py`
+    — so it equally bounds `runs_with_fr`, every chunk's `results`, `run_rows`, and the regime map (all
+    derived from it). The cutoff is the canonical `ScannerRun.asof_date` (not the denormalized
+    `ForwardReturn.asof_date`). `as_of=None` adds NO clause → byte-identical all-history.
+
+    iter-29 (AG-8): the join accumulator used to be ONE dict holding every distinct (run_id, symbol) pair
+    across the FULL horizon's history at once (803,042 pairs measured live at iter-28, as_of=None) even
+    though the SOURCE query was already `yield_per`-streamed — an unbounded whole-history materialization
+    in substance. `runs_with_fr` is now discovered via a lightweight DISTINCT-projected query (bounded by
+    run count, never by pair count), then walked in bounded SLICES of `batch` run ids: each slice rebuilds
+    its own `_fr_slice_map` accumulator, streams+joins that slice's `ScannerResult`s, extends `observations`,
+    and discards the slice's dict before the next — so peak LIVE accumulator size is bounded by
+    (batch x symbols-per-run), never by the full history. Slices walk the sorted `runs_with_fr` list in
+    non-overlapping, increasing contiguous ranges, so concatenating each slice's (run_id, id)-ordered
+    `ScannerResult` output reproduces the SAME global order the prior single-pass implementation produced —
+    byte-identical (TC-2), never re-derived."""
     parsed = parse_factor_source(factor.source)
     # iter-47 (J-105): column-project + stream the (possibly huge) forward-return scan so the read path is
     # bounded by config (`yield_per`) instead of materializing the whole table as ORM rows. We read only the
     # three fields the join consumes (run_id, symbol, realized_return) — projected Row values are the EXACT
     # same Python types as ORM attribute access (no coercion → byte-identical served value).
     batch = (cfg or get_config()).research.read_batch_size
-    # iter-52 (J-109): the FR scan ALSO projects the stored `max_drawdown` (the J-86 column, read VERBATIM)
-    # so each observation carries the realized return AND its paired post-snapshot drawdown — both fed to
-    # `_deciles` (the per-decile mean-MDD beside the mean return). One added projected column; no extra read.
-    fr_stmt = select(
-        ForwardReturn.run_id, ForwardReturn.symbol, ForwardReturn.realized_return, ForwardReturn.max_drawdown
-    ).where(ForwardReturn.horizon == horizon)
+
+    # iter-29 (AG-8): the distinct run ids at this horizon, via a DISTINCT-projected query — bounded by run
+    # count, never by (run, symbol) pair count (the dimension `_fr_slice_map` below chunks over).
+    runs_with_fr_stmt = select(ForwardReturn.run_id).where(ForwardReturn.horizon == horizon)
     if as_of is not None:
-        fr_stmt = fr_stmt.join(ScannerRun, ScannerRun.id == ForwardReturn.run_id).where(
+        runs_with_fr_stmt = runs_with_fr_stmt.join(ScannerRun, ScannerRun.id == ForwardReturn.run_id).where(
             ScannerRun.asof_date <= as_of
         )
-    ret_by_run_symbol: dict[tuple[int, str], tuple[float, Optional[float]]] = {}
-    runs_with_fr_set: set[int] = set()
-    for run_id, symbol, realized_return, max_drawdown in session.exec(fr_stmt).yield_per(batch):
-        ret_by_run_symbol[(run_id, symbol)] = (realized_return, max_drawdown)
-        runs_with_fr_set.add(run_id)
-    runs_with_fr = sorted(runs_with_fr_set)
+    runs_with_fr = sorted(session.exec(runs_with_fr_stmt.distinct()).all())
     run_rows = (
         session.exec(select(ScannerRun).where(ScannerRun.id.in_(runs_with_fr))).all()
         if runs_with_fr else []
@@ -231,29 +256,37 @@ def _factor_observations(
     # rides that SAME index (no `USE TEMP B-TREE FOR ORDER BY`), so the sort never spills a temp file to a
     # nearly-full disk; a bare `ORDER BY id` would force a full temp-B-tree sort over ~598K rows that can
     # exhaust disk. Factor Lab is UNCACHED (recomputes every request) → this is the genuine OOM site.
-    res_stmt = (
-        select(ScannerResult)
-        .where(ScannerResult.run_id.in_(runs_with_fr))
-        .order_by(ScannerResult.run_id, ScannerResult.id)
-    )
-    results = session.exec(res_stmt).yield_per(batch) if runs_with_fr else []
-
+    #
+    # iter-29 (AG-8): this scan now runs PER CHUNK (`runs_with_fr[start:start+batch]`), scoped by the SAME
+    # `run_id.in_(slice_run_ids)` filter every chunk's `_fr_slice_map` join uses, so a chunk's ScannerResult
+    # rows and its accumulator cover the identical run-id set — the join lookup below never misses.
     observations: list[dict] = []
-    for res in results:
-        fr = ret_by_run_symbol.get((res.run_id, res.ticker))
-        if fr is None:
-            continue  # no realized return at this horizon for this stock (n=0 contribution)
-        realized, max_drawdown = fr
-        value = _extract_factor_value(res, parsed)
-        if value is None:
-            continue  # factor-NULL observation EXCLUDED (never bucketed) — honest, not fabricated
-        observations.append({
-            "run_id": res.run_id, "ticker": res.ticker, "factor": float(value), "return": realized,
-            # iter-27/52 (J-86/J-109): the stored max_drawdown read VERBATIM — aggregated read-only into the
-            # per-decile mean-MDD beside the mean return; None on a short window (honest NA, never a 0).
-            "max_drawdown": max_drawdown,
-            "regime": regime_by_run.get(res.run_id),  # stored regime label for the run (J-27)
-        })
+    for start in range(0, len(runs_with_fr), batch):
+        slice_run_ids = runs_with_fr[start:start + batch]
+        ret_by_run_symbol = _fr_slice_map(session, horizon, slice_run_ids, batch)
+        res_stmt = (
+            select(ScannerResult)
+            .where(ScannerResult.run_id.in_(slice_run_ids))
+            .order_by(ScannerResult.run_id, ScannerResult.id)
+        )
+        for res in session.exec(res_stmt).yield_per(batch):
+            fr = ret_by_run_symbol.get((res.run_id, res.ticker))
+            if fr is None:
+                continue  # no realized return at this horizon for this stock (n=0 contribution)
+            realized, max_drawdown = fr
+            value = _extract_factor_value(res, parsed)
+            if value is None:
+                continue  # factor-NULL observation EXCLUDED (never bucketed) — honest, not fabricated
+            observations.append({
+                "run_id": res.run_id, "ticker": res.ticker, "factor": float(value), "return": realized,
+                # iter-27/52 (J-86/J-109): the stored max_drawdown read VERBATIM — aggregated read-only into
+                # the per-decile mean-MDD beside the mean return; None on a short window (honest NA, never a
+                # fabricated 0).
+                "max_drawdown": max_drawdown,
+                "regime": regime_by_run.get(res.run_id),  # stored regime label for the run (J-27)
+            })
+        # `ret_by_run_symbol` is rebound (not accumulated into) on the next iteration — this slice's dict is
+        # eligible for GC before the next chunk's query even starts (the bounded-memory guarantee, TC-1).
     return observations
 
 
diff --git a/apps/backend/tests/test_evidence.py b/apps/backend/tests/test_evidence.py
index 512e6e5d..e6ded870 100644
--- a/apps/backend/tests/test_evidence.py
+++ b/apps/backend/tests/test_evidence.py
@@ -21,6 +21,7 @@ from pathlib import Path
 import pytest
 from sqlmodel import Session
 
+import app.engine.forward_testing as forward_testing
 import app.engine.market_phase as market_phase
 from app.config import REPO_ROOT, load_config
 from app.db import create_db_and_tables, make_engine
@@ -615,6 +616,110 @@ def test_build_payload_session_provided_unresolvable_claim_no_expectations_key(t
     with Session(evidence_dd_engine) as session:
         payload = build_evidence_payload(str(ledger), session=session, config=load_config())
     assert "expectations" not in payload["claims"][0]
+    # ops-hardening iter-29 (AG-8) error-case regression: the pre-existing HONEST-None path (an
+    # unresolvable cohort, `compute_drawdown_expectations` returning None WITHOUT raising) must stay
+    # byte-unchanged by the new per-claim failure guard below — no `expectations_status` field either.
+    # This is what proves the new field is ADDITIVE (only on a caught exception), never a replacement of
+    # the pre-existing silent-omission behavior.
+    assert "expectations_status" not in payload["claims"][0]
+
+
+# ==================================================================================================
+# ops-hardening iter-29 (AG-8) — a per-claim `compute_drawdown_expectations_cached` failure
+# (`MemoryError` or otherwise) must never abort the response for the OTHER claims: the failing claim's row
+# omits `expectations` and carries the new `expectations_status: "unavailable"` field; every other claim's
+# row is byte-unchanged (isolate-and-continue, mirroring the EXISTING per-claim `MemoryError`-then-continue
+# convention `data_manager.py`'s drawdown-expectations ingest warm loop already uses near
+# `data_manager.py:3361` — TC-4).
+# ==================================================================================================
+@pytest.fixture()
+def evidence_dd_two_claims_engine(tmp_path, monkeypatch):
+    """TWO independently resolvable claims in ONE fixture, dedicated (not a mutation of `evidence_dd_engine`
+    above, so its own two existing tests stay untouched): AAA (leadership_score, decile 10, horizon 20 —
+    byte-identical setup to `evidence_dd_engine`) plus BBB (entry_quality_score, decile 10, horizon 20) in
+    the SAME run/date. BBB's high `entry_quality_score` / baseline `leadership_score` (and AAA's inverse)
+    mean each name is the SOLE decile-10 member of its OWN factor's single-observation cohort — adding BBB
+    does not disturb AAA's leadership_score decile-10 membership (still {AAA} alone, n=1)."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'evidence_dd_two.db'}")
+    create_db_and_tables(engine)
+    d = date(2025, 1, 10)
+    with Session(engine) as session:
+        run = ScannerRun(
+            asof_date=d, created_at=datetime.now(timezone.utc), provider="seed", benchmark="SPY",
+            regime_score=50.0, regime_label="Risk-on", regime_components_json="[]",
+            new_high_low_json="{}", candidate_counts_json="{}",
+        )
+        session.add(run)
+        session.flush()
+        session.add(ScannerResult(
+            run_id=run.id, ticker="AAA", name="AAA", sector="Technology",
+            leadership_score=90.0, leadership_bucket="A",
+            entry_quality_score=50.0, entry_quality_bucket="C",
+            risk_score=50.0, risk_bucket="C",
+            setup_status="Actionable", rank=1, record_json="{}",
+        ))
+        session.add(ForwardReturn(
+            run_id=run.id, symbol="AAA", horizon=20, asof_date=d, entry_close=100.0,
+            measured_date=d + timedelta(days=40), realized_return=0.02,
+            max_drawdown=-0.05, underwater_days=3, time_to_recover_days=5,
+        ))
+        session.add(ScannerResult(
+            run_id=run.id, ticker="BBB", name="BBB", sector="Technology",
+            leadership_score=50.0, leadership_bucket="C",
+            entry_quality_score=90.0, entry_quality_bucket="A",
+            risk_score=50.0, risk_bucket="C",
+            setup_status="Actionable", rank=2, record_json="{}",
+        ))
+        session.add(ForwardReturn(
+            run_id=run.id, symbol="BBB", horizon=20, asof_date=d, entry_close=100.0,
+            measured_date=d + timedelta(days=40), realized_return=0.03,
+            max_drawdown=-0.04, underwater_days=2, time_to_recover_days=4,
+        ))
+        session.commit()
+
+    def _fake_ctx(session=None, as_of=None, config=None):
+        return {d.isoformat(): {"phase": "Expansion", "severity": 10.0, "p_bear": 0.05}}
+
+    monkeypatch.setattr(market_phase, "phase_context_by_date", _fake_ctx)
+    return engine
+
+
+def test_build_payload_per_claim_compute_failure_is_isolated(
+    tmp_path, evidence_dd_two_claims_engine, monkeypatch
+):
+    """TC-4: `compute_drawdown_expectations_cached` monkeypatched to raise `MemoryError` for exactly ONE of
+    two resolvable claims. The failing claim's row carries `expectations_status: "unavailable"` and no
+    `expectations` key; the OTHER claim's row carries its normal `expectations` key, fully unaffected —
+    proving one claim's compute failure never blanks the rest of the `/evidence` response."""
+    ledger = tmp_path / "certified-claims.jsonl"
+    append_entry(str(ledger), _pass_entry("leadership_score"))
+    append_entry(str(ledger), _pass_entry("entry_quality_score", factor="entry_quality_score"))
+
+    real_cached = forward_testing.compute_drawdown_expectations_cached
+
+    def _flaky_cached(session, claim, config=None):
+        if claim.get("factor") == "leadership_score":
+            raise MemoryError("synthetic TC-4 failure")
+        return real_cached(session, claim, config)
+
+    monkeypatch.setattr(forward_testing, "compute_drawdown_expectations_cached", _flaky_cached)
+
+    with Session(evidence_dd_two_claims_engine) as session:
+        payload = build_evidence_payload(str(ledger), session=session, config=load_config())
+
+    rows = payload["claims"]
+    assert len(rows) == 2
+    failed_row = next(r for r in rows if r["claim"]["factor"] == "leadership_score")
+    ok_row = next(r for r in rows if r["claim"]["factor"] == "entry_quality_score")
+
+    assert failed_row.get("expectations_status") == "unavailable"
+    assert "expectations" not in failed_row
+
+    assert "expectations_status" not in ok_row
+    assert "expectations" in ok_row
+    assert ok_row["expectations"]["horizon"] == 20
+    exp_phase = next(p for p in ok_row["expectations"]["by_phase"] if p["phase"] == "Expansion")
+    assert exp_phase["n"] == 1
 
 
 def test_resolve_ledger_path_env_override(tmp_path, monkeypatch):
diff --git a/apps/backend/tests/test_research_streaming.py b/apps/backend/tests/test_research_streaming.py
index f6ccdc7b..dfaf2a99 100644
--- a/apps/backend/tests/test_research_streaming.py
+++ b/apps/backend/tests/test_research_streaming.py
@@ -26,8 +26,9 @@ import json
 from datetime import date, datetime, timezone
 
 import pytest
-from sqlmodel import Session
+from sqlmodel import Session, select
 
+import app.engine.research as research_module
 from app.config import load_config
 from app.db import create_db_and_tables, make_engine
 from app.engine.research import (
@@ -566,3 +567,150 @@ def test_compute_factor_lab_all_chunk_independent_component(component_engine, as
         small = compute_factor_lab_all(session, _cfg_batch(1), as_of=as_of)
         big = compute_factor_lab_all(session, _cfg_batch(1_000_000), as_of=as_of)
         assert _eq(small, big), f"factor-lab-all payload differs by batch (as_of={as_of})"
+
+
+# ==================================================================================================
+# ops-hardening iter-29 (AG-8): `_factor_observations`'s join accumulator (`ret_by_run_symbol`) used to
+# hold ONE entry per distinct (run_id, symbol) pair across the FULL horizon's `forward_returns` history for
+# as_of=None (803,042 pairs / 3,964,725 rows measured live at iter-28) even though the SOURCE query was
+# already `yield_per`-streamed — an unbounded whole-history materialization in substance (AG-8). The fix
+# chunks `runs_with_fr` (the sorted distinct run-id list, now discovered via a lightweight DISTINCT query
+# instead of as a side effect of building the full accumulator) into bounded slices, rebuilding the
+# accumulator ONE slice at a time via the new `_fr_slice_map` helper — so its LIVE size is bounded by
+# (chunk width x symbols-per-run), never by the full history's distinct-pair count. These proofs pin:
+#   1. TC-1: the live accumulator (`_fr_slice_map`'s return value) never holds more than one chunk's worth
+#      of entries at any point during a call, on a fixture whose rows span more than one chunk across >=2
+#      distinct run ids.
+#   2. TC-2: the chunked rewrite is byte-identical to a pinned copy of the PRE-FIX (single-accumulator)
+#      implementation, for both as_of=None and a historical as_of=D.
+#   3. TC-3: the as_of=D call returns zero observations from a run dated after D (no-lookahead preserved).
+# ==================================================================================================
+@pytest.fixture()
+def chunked_accumulator_engine(tmp_path):
+    """5 distinct ScannerRuns (one per month, Jan-May 2025), each with 3 tickers carrying a forward return
+    at horizon H — 15 total distinct (run_id, symbol) pairs, spanning 5 distinct run ids. Dedicated (not
+    reused from `prune_engine`/`component_engine`) so the chunk-boundary proof (TC-1) and the as_of cutoff
+    proof (TC-3) have a fixture shaped exactly for them: enough runs to force multiple chunks at a small
+    `read_batch_size`, and dates that cleanly split into an early/late group around a chosen as_of."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'chunked.db'}")
+    create_db_and_tables(engine)
+    with Session(engine) as session:
+        runs = [
+            _add_run(session, date(2025, m, 10), regime_label="Risk-on" if m % 2 else "Risk-off")
+            for m in range(1, 6)  # r0=Jan .. r4=May 2025
+        ]
+        session.flush()
+        for i, run in enumerate(runs):
+            for j, base in enumerate(("AA", "BB", "CC")):
+                ticker = f"{base}{i}"  # distinct symbol per run -> 15 genuinely distinct (run_id, symbol) pairs
+                _add_result(session, run.id, ticker, j + 1, setup="Actionable", sector="Technology",
+                            lead=50.0 + i + j)
+                _add_fr(session, run.id, ticker, 0.01 * (i + 1) + 0.001 * j, horizon=H,
+                        mae=-0.02, mfe=0.05, mdd=-0.03 - 0.001 * j)
+        session.commit()
+    return engine
+
+
+def _factor_observations_reference_unchunked(session, factor, horizon, as_of, cfg):
+    """A pinned copy of iter-29's PRE-FIX `_factor_observations` body: ONE unbounded `ret_by_run_symbol`
+    accumulator built from a SINGLE un-sliced `fr_stmt` covering the FULL `runs_with_fr` set at once (no
+    `_fr_slice_map`, no chunk loop) — the regression oracle for the iter-29 chunked rewrite's byte-identity
+    proof (TC-2). Calls the SAME unchanged helpers (`parse_factor_source`, `_extract_factor_value`) the real,
+    rewritten function still uses, so any divergence can only come from the chunking itself."""
+    from app.engine.research import _extract_factor_value, parse_factor_source
+    parsed = parse_factor_source(factor.source)
+    batch = cfg.research.read_batch_size
+    fr_stmt = select(
+        ForwardReturn.run_id, ForwardReturn.symbol, ForwardReturn.realized_return, ForwardReturn.max_drawdown
+    ).where(ForwardReturn.horizon == horizon)
+    if as_of is not None:
+        fr_stmt = fr_stmt.join(ScannerRun, ScannerRun.id == ForwardReturn.run_id).where(
+            ScannerRun.asof_date <= as_of
+        )
+    ret_by_run_symbol = {}
+    runs_with_fr_set = set()
+    for run_id, symbol, realized_return, max_drawdown in session.exec(fr_stmt).yield_per(batch):
+        ret_by_run_symbol[(run_id, symbol)] = (realized_return, max_drawdown)
+        runs_with_fr_set.add(run_id)
+    runs_with_fr = sorted(runs_with_fr_set)
+    run_rows = (
+        session.exec(select(ScannerRun).where(ScannerRun.id.in_(runs_with_fr))).all()
+        if runs_with_fr else []
+    )
+    regime_by_run = {run.id: run.regime_label for run in run_rows}
+    res_stmt = (
+        select(ScannerResult)
+        .where(ScannerResult.run_id.in_(runs_with_fr))
+        .order_by(ScannerResult.run_id, ScannerResult.id)
+    )
+    results = session.exec(res_stmt).yield_per(batch) if runs_with_fr else []
+    observations = []
+    for res in results:
+        fr = ret_by_run_symbol.get((res.run_id, res.ticker))
+        if fr is None:
+            continue
+        realized, max_drawdown = fr
+        value = _extract_factor_value(res, parsed)
+        if value is None:
+            continue
+        observations.append({
+            "run_id": res.run_id, "ticker": res.ticker, "factor": float(value), "return": realized,
+            "max_drawdown": max_drawdown,
+            "regime": regime_by_run.get(res.run_id),
+        })
+    return observations
+
+
+def test_factor_observations_accumulator_is_chunk_bounded(chunked_accumulator_engine, monkeypatch):
+    """TC-1: `_factor_observations`'s join accumulator (`_fr_slice_map`'s return value, wrapped/observed via
+    monkeypatch) never holds more entries than ONE bounded chunk at any point during the call — never one
+    entry per distinct (run_id, symbol) pair in the whole fixture (15 pairs across 5 run ids)."""
+    factor = next(f for f in load_config().research.factor_lab.factors if f.key == "leadership_score")
+    observed_sizes: list[int] = []
+    real_fr_slice_map = research_module._fr_slice_map
+
+    def _wrapped(session, horizon, slice_run_ids, batch):
+        result = real_fr_slice_map(session, horizon, slice_run_ids, batch)
+        observed_sizes.append(len(result))
+        return result
+
+    monkeypatch.setattr(research_module, "_fr_slice_map", _wrapped)
+    with Session(chunked_accumulator_engine) as session:
+        # chunk width = 2 run ids/slice over 5 distinct run ids -> 3 slices (2, 2, 1 run ids each)
+        observations = research_module._factor_observations(session, factor, H, None, cfg=_cfg_batch(2))
+
+    total_pairs = 15  # 5 runs x 3 tickers, by fixture construction
+    assert len(observations) == total_pairs, "sanity: every fixture pair must surface as an observation"
+    assert len(observed_sizes) == 3, f"expected 3 chunks (5 run ids at width 2), got {len(observed_sizes)}"
+    assert max(observed_sizes) <= 6, (
+        f"a single slice must never exceed 2 run ids x 3 tickers = 6 entries, got {max(observed_sizes)}"
+    )
+    assert max(observed_sizes) < total_pairs, (
+        "the live accumulator must never hold the WHOLE fixture's pairs at once"
+    )
+
+
+@pytest.mark.parametrize("as_of", [None, date(2025, 3, 15)])
+def test_factor_observations_chunked_equals_unchunked_reference(chunked_accumulator_engine, as_of):
+    """TC-2: the iter-29 chunked `_factor_observations` is byte-identical to the pinned pre-fix
+    (single-accumulator) reference — for as_of=None (all-history) AND a historical as_of=D (2025-03-15) that
+    splits the 5-run fixture into an early (Jan-Mar) / late (Apr-May) group."""
+    cfg = _cfg_batch(2)
+    factor = next(f for f in cfg.research.factor_lab.factors if f.key == "leadership_score")
+    with Session(chunked_accumulator_engine) as session:
+        chunked = _factor_observations(session, factor, H, as_of, cfg=cfg)
+        reference = _factor_observations_reference_unchunked(session, factor, H, as_of, cfg)
+    assert _eq(chunked, reference), f"chunked output != pinned pre-fix reference (as_of={as_of})"
+
+
+def test_factor_observations_chunked_as_of_excludes_runs_after_cutoff(chunked_accumulator_engine):
+    """TC-3: for the as_of=D-scoped chunked call, zero returned observations reference a run dated after D
+    (no-lookahead preserved through the chunk rewrite)."""
+    d = date(2025, 3, 15)  # between run r2 (Mar 10) and run r3 (Apr 10)
+    factor = next(f for f in load_config().research.factor_lab.factors if f.key == "leadership_score")
+    with Session(chunked_accumulator_engine) as session:
+        observations = _factor_observations(session, factor, H, d, cfg=_cfg_batch(2))
+        run_dates = {run.id: run.asof_date for run in session.exec(select(ScannerRun)).all()}
+    assert observations, "sanity: the early-group runs (Jan-Mar) must still contribute observations"
+    for obs in observations:
+        assert run_dates[obs["run_id"]] <= d, f"observation from run {obs['run_id']} dated after {d}"
diff --git a/apps/frontend/app/evidence/page.tsx b/apps/frontend/app/evidence/page.tsx
index cf22310f..4bdf60a3 100644
--- a/apps/frontend/app/evidence/page.tsx
+++ b/apps/frontend/app/evidence/page.tsx
@@ -16,8 +16,8 @@ import {
   formatStreak,
   insufficientLabel,
   regimeLabel,
+  resolveDrawdownExpectationsPanelState,
   type DistributionCell,
-  type DrawdownExpectations,
   type LossStreakCell,
 } from "@/lib/evidence";
 import { fetchEvidence, type CertifiedClaim, type EvidenceLedgerResponse } from "@/lib/api";
@@ -233,26 +233,44 @@ function ClaimRow({ claim }: { claim: CertifiedClaim }) {
           </Field>
         </dl>
 
-        <DrawdownExpectationsPanel expectations={claim.expectations} />
+        <DrawdownExpectationsPanel claim={claim} />
       </CardContent>
     </Card>
   );
 }
 
 /** J-25 — the phase-conditional drawdown & dry-spell expectations panel: an additive section inside the
- *  SAME claim card, below the existing field grid. Renders NOTHING when `expectations` is absent/null
- *  (mirrors the Stock-detail RiskBudgetCard's "return null when absent" precedent, iter-40) — never an
- *  error boundary, never a blank placeholder. Reads `claim.expectations` VERBATIM — no client-side
- *  recompute; every figure is the served median/p90/streak, re-formatted only. Renders for ANY claim
- *  regardless of its PASS/FAIL verdict (outcome-neutral, J-25) — descriptive history, never a forecast. */
-function DrawdownExpectationsPanel({
-  expectations,
-}: {
-  expectations: DrawdownExpectations | null | undefined;
-}) {
-  if (!expectations) {
+ *  SAME claim card, below the existing field grid. Renders NOTHING when `expectations` is absent/null with
+ *  no status field (mirrors the Stock-detail RiskBudgetCard's "return null when absent" precedent,
+ *  iter-40) — never an error boundary, never a blank placeholder. Reads `claim.expectations` VERBATIM — no
+ *  client-side recompute; every figure is the served median/p90/streak, re-formatted only. Renders for ANY
+ *  claim regardless of its PASS/FAIL verdict (outcome-neutral, J-25) — descriptive history, never a
+ *  forecast.
+ *
+ *  ops-hardening iter-29 (AG-8): branches on `resolveDrawdownExpectationsPanelState` (the single, pure
+ *  authority) so a genuine per-claim compute failure THIS request (`expectations_status === "unavailable"`)
+ *  renders a calm inline note instead of being indistinguishable from the pre-existing "not applicable"
+ *  (absent) case. */
+function DrawdownExpectationsPanel({ claim }: { claim: CertifiedClaim }) {
+  const state = resolveDrawdownExpectationsPanelState(claim);
+  if (state.kind === "absent") {
     return null;
   }
+  if (state.kind === "unavailable") {
+    // A routine transient-failure disclosure, not an error banner — same calm `text-text-faint` treatment
+    // the "Pending — monitored as new data matures" forward-walk cell above already uses on this card.
+    return (
+      <div className="border-t border-border pt-3" data-testid="evidence-expectations-unavailable">
+        <h3 className="text-xs font-semibold uppercase tracking-wide text-text-faint">
+          Historical drawdown &amp; dry-spell expectations
+        </h3>
+        <p className="mt-0.5 text-xs text-text-faint">
+          Unavailable — monitored and refreshed as new data arrives.
+        </p>
+      </div>
+    );
+  }
+  const { expectations } = state;
   return (
     <div className="space-y-2 border-t border-border pt-3" data-testid="evidence-expectations-panel">
       <div>
diff --git a/apps/frontend/lib/evidence.test.ts b/apps/frontend/lib/evidence.test.ts
index c17f852d..46b188a0 100644
--- a/apps/frontend/lib/evidence.test.ts
+++ b/apps/frontend/lib/evidence.test.ts
@@ -43,9 +43,11 @@ import {
   regimeLabel,
   resolveCohortEvidence,
   resolveCombinationEvidence,
+  resolveDrawdownExpectationsPanelState,
   resolveEvidenceStatus,
   type CertifiedClaim,
   type CombinationCohort,
+  type DrawdownExpectations,
   type FactorCohort,
   type ProvenSignal,
 } from "./evidence.ts";
@@ -981,4 +983,58 @@ check("formatStreak renders a rounded integer, and an em dash for null/undefined
   assert.strictEqual(formatStreak(undefined), "—");
 });
 
+// --- drawdown-expectations panel state resolver (ops-hardening iter-29, AG-8 residual-failure disclosure,
+// TC-5) — the pure decision function `DrawdownExpectationsPanel` (app/evidence/page.tsx) branches on. Three
+// states: the pre-existing "present" (a table renders) and "absent" (no expectations, no status field —
+// renders nothing, unchanged honest-None cohort-unresolvable case) plus the NEW "unavailable" (a per-claim
+// compute failure this request — an inline note, no table). Mirrors the extracted-decision-function pattern
+// `lib/background-compute-panel-branch.ts` established (iter-24/25, J-09).
+const SAMPLE_EXPECTATIONS: DrawdownExpectations = {
+  horizon: 20,
+  min_sample: 5,
+  streak_min_n: 3,
+  survivorship_bias: "Current-membership seed; survivorship bias not corrected for.",
+  method_note: "Median/p90 by market phase at entry.",
+  by_phase: [],
+};
+
+check("resolveDrawdownExpectationsPanelState: expectations present => 'present', carrying it verbatim", () => {
+  const claim: CertifiedClaim = { ...provenRow("leadership_score"), expectations: SAMPLE_EXPECTATIONS };
+  const state = resolveDrawdownExpectationsPanelState(claim);
+  assert.strictEqual(state.kind, "present");
+  if (state.kind === "present") {
+    assert.strictEqual(state.expectations, SAMPLE_EXPECTATIONS); // read verbatim, never recomputed
+  }
+});
+
+check("resolveDrawdownExpectationsPanelState: expectations_status='unavailable' => 'unavailable' (TC-5)", () => {
+  const claim: CertifiedClaim = { ...provenRow("leadership_score"), expectations_status: "unavailable" };
+  const state = resolveDrawdownExpectationsPanelState(claim);
+  assert.strictEqual(state.kind, "unavailable");
+});
+
+check(
+  "resolveDrawdownExpectationsPanelState: no expectations + no status field => 'absent' (pre-existing " +
+    "honest-None case, unchanged, TC-5)",
+  () => {
+    const claim: CertifiedClaim = provenRow("leadership_score"); // no expectations, no expectations_status
+    const state = resolveDrawdownExpectationsPanelState(claim);
+    assert.strictEqual(state.kind, "absent");
+  },
+);
+
+check(
+  "resolveDrawdownExpectationsPanelState: 'unavailable' is DISTINCT from the pre-existing absent case (TC-5)",
+  () => {
+    const unavailable = resolveDrawdownExpectationsPanelState({
+      ...provenRow("leadership_score"),
+      expectations_status: "unavailable",
+    });
+    const absent = resolveDrawdownExpectationsPanelState(provenRow("leadership_score"));
+    assert.notStrictEqual(unavailable.kind, absent.kind);
+    assert.strictEqual(unavailable.kind, "unavailable");
+    assert.strictEqual(absent.kind, "absent");
+  },
+);
+
 console.log(`\n${passed} evidence-badge resolver checks passed.`);
diff --git a/apps/frontend/lib/evidence.ts b/apps/frontend/lib/evidence.ts
index cea8c8d8..de18d546 100644
--- a/apps/frontend/lib/evidence.ts
+++ b/apps/frontend/lib/evidence.ts
@@ -74,7 +74,13 @@ export interface DrawdownExpectations {
  *  PASS backs (null for a real signal-less writer entry — fail-safe). `forward_walk` is the forward-walk
  *  score-to-date (null until a certified claim is monitored). `expectations` (iter-41, J-25) is ADDITIVE
  *  and OPTIONAL — the backend omits the key entirely (never a fabricated panel) when the cohort could not
- *  be resolved; a `null`/`undefined` value must render nothing for the panel section (never an error). */
+ *  be resolved; a `null`/`undefined` value must render nothing for the panel section (never an error).
+ *  `expectations_status` (ops-hardening iter-29, AG-8) is ALSO additive and OPTIONAL — present ONLY when
+ *  this request's per-claim `expectations` compute raised an exception (`"unavailable"`, the one legal
+ *  value today); absent for a successful compute AND for every pre-existing honest-None case (an
+ *  out-of-scope horizon, an unresolvable cohort, a zero-observation cohort) — those keep rendering nothing,
+ *  byte-unchanged. `resolveDrawdownExpectationsPanelState` below is the single place that distinguishes
+ *  the three states. */
 export interface CertifiedClaim {
   signal: string | null;
   claim: Record<string, unknown>;
@@ -86,6 +92,7 @@ export interface CertifiedClaim {
   proven: boolean;
   forward_walk: unknown | null;
   expectations?: DrawdownExpectations | null;
+  expectations_status?: "unavailable";
 }
 
 /** A proven claim row, as stored in the served `proven_signals` map (keyed by signal). Same shape as a
@@ -277,6 +284,39 @@ export function formatStreak(value: number | null | undefined): string {
   return `${Math.round(value)}`;
 }
 
+// --- drawdown-expectations PANEL state resolver (ops-hardening iter-29, AG-8 residual-failure disclosure) -
+// PURE, read-only: the SINGLE authority for which of the THREE states `DrawdownExpectationsPanel`
+// (app/evidence/page.tsx) renders for one claim. No React, no DOM types, so it is unit-testable under
+// `node`/`tsx` (mirrors `lib/background-compute-panel-branch.ts`'s extracted-decision-function pattern,
+// iter-24/25 J-09). Reads `claim.expectations` / `claim.expectations_status` VERBATIM — recomputes nothing.
+
+/** Which state the drawdown-expectations panel renders for ONE claim:
+ *   - "present"     — a resolved `expectations` payload exists; the table renders (pre-existing, unchanged).
+ *   - "unavailable" — this request's per-claim compute raised an exception (`expectations_status ===
+ *                     "unavailable"`); a calm inline note renders instead of a table (NEW, iter-29).
+ *   - "absent"      — no `expectations` and no `expectations_status` (the pre-existing honest-None cohort-
+ *                     unresolvable case); the panel renders nothing (unchanged). */
+export type DrawdownExpectationsPanelState =
+  | { kind: "present"; expectations: DrawdownExpectations }
+  | { kind: "unavailable" }
+  | { kind: "absent" };
+
+/**
+ * Resolve which state `DrawdownExpectationsPanel` should render for one claim (PURE, read-only — no
+ * client-side recompute of anything). `"unavailable"` (a genuine per-claim compute failure THIS request)
+ * is DISTINCT from `"absent"` (the pre-existing, unaffected "no expectations, no status field" case) so the
+ * panel can disclose a transient failure honestly instead of rendering it identically to "not applicable".
+ */
+export function resolveDrawdownExpectationsPanelState(claim: CertifiedClaim): DrawdownExpectationsPanelState {
+  if (claim.expectations) {
+    return { kind: "present", expectations: claim.expectations };
+  }
+  if (claim.expectations_status === "unavailable") {
+    return { kind: "unavailable" };
+  }
+  return { kind: "absent" };
+}
+
 // --- claim-row presentation (goal-mcp-loop iter-4) — regime label + honest title/linkback --------------
 // PURE, read-only helpers the `/evidence` ClaimRow consumes to deliver J-04 (regime-conditioned evidence,
 // "clearly labeled with the regime it holds in") WITHOUT regressing J-05 (the leadership score row's title
```

## Excluded-path stat (dependency/lockfile visibility)

 .../dispatch/prompt-req.q0n1Vz.md                  | 540 ---------------------
 .../state/project-story.md                         |  12 +-
 runs/goal-session-ops-hardening/telemetry.jsonl    |   7 +
 runs/goal-session-ops-hardening/trace/.next-step   |   2 +-
 runs/goal-session-ops-hardening/trace/trace.jsonl  |   3 +
 5 files changed, 17 insertions(+), 547 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
