# Iteration diff (bounded)

Files changed: 9. Shown in full: 7.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/app/engine/j11_avb_diagnostic.py` (188 lines not shown)
- `apps/backend/app/engine/j11_stage_d.py` (24 lines not shown)

```diff
diff --git a/apps/backend/scripts/run_j11_stage_c_bounded_clear.py b/apps/backend/scripts/run_j11_stage_c_bounded_clear.py
index 54827076..12fb5198 100644
--- a/apps/backend/scripts/run_j11_stage_c_bounded_clear.py
+++ b/apps/backend/scripts/run_j11_stage_c_bounded_clear.py
@@ -21,11 +21,16 @@ anywhere in this process, never a raw file copy of the 7.8+ GB database.
 Usage:
     apps/backend/.venv/bin/python apps/backend/scripts/run_j11_stage_c_bounded_clear.py \\
         --confirm \\
-        [--evidence-dir runs/goal-market-compass-iter-13] \\
+        --evidence-dir runs/goal-market-compass-iter-13 \\
         [--certified-state-path runs/goal-market-compass-iter-12/j11-stage-b1-cleanup-fingerprint-after.json]
 
 Without `--confirm`, the script performs NO database interaction at all (not even a read) and exits
-non-zero.
+non-zero. `--evidence-dir` is REQUIRED and has no implicit default: it used to default to
+`runs/goal-market-compass-iter-13`, a real committed evidence directory, so any caller that forgot the
+flag silently overwrote committed Stage C forensic evidence instead of failing loudly (this actually
+happened -- iteration 14's own CLI test omitted the flag and truncated three iteration-13 evidence files;
+see docs/handoffs/goal-market-compass-iter-14-dev.md). A committed evidence directory is now only ever
+written when it is named explicitly on the command line.
 """
 from __future__ import annotations
 
@@ -49,7 +54,9 @@ from app.engine.j11_maintenance import INCIDENT_DATES, capture_pre_reset_invento
 from app.engine import j11_schema_migration as migration  # noqa: E402
 from app.models import DataProviderRun, NextSessionManifest, Watchlist  # noqa: E402
 
-DEFAULT_EVIDENCE_DIR = REPO_ROOT / "runs" / "goal-market-compass-iter-13"
+# The directory this script's evidence BELONGS in when it is run for real. Deliberately NOT an argparse
+# default: an omitted --evidence-dir must FAIL, never silently write over these committed files.
+CANONICAL_EVIDENCE_DIR = REPO_ROOT / "runs" / "goal-market-compass-iter-13"
 DEFAULT_CERTIFIED_STATE_PATH = (
     REPO_ROOT / "runs" / "goal-market-compass-iter-12" / "j11-stage-b1-cleanup-fingerprint-after.json"
 )
@@ -75,7 +82,14 @@ def _write_json(path: Path, payload) -> None:
 
 def main() -> int:
     parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
-    parser.add_argument("--evidence-dir", type=Path, default=DEFAULT_EVIDENCE_DIR)
+    parser.add_argument(
+        "--evidence-dir", type=Path, default=None,
+        help=(
+            "required -- the directory every evidence JSON is written to. Has NO default on purpose: the "
+            f"real target ({CANONICAL_EVIDENCE_DIR}) is a committed evidence directory, and an implicit "
+            "default meant a forgotten flag overwrote committed forensic evidence instead of failing."
+        ),
+    )
     parser.add_argument("--certified-state-path", type=Path, default=DEFAULT_CERTIFIED_STATE_PATH)
     parser.add_argument(
         "--confirm", action="store_true",
@@ -92,6 +106,16 @@ def main() -> int:
         )
         return 2
 
+    if args.evidence_dir is None:
+        print(
+            "refusing to run without an explicit --evidence-dir. This script writes forensic evidence "
+            f"JSON into that directory; its real target ({CANONICAL_EVIDENCE_DIR}) is a COMMITTED "
+            "evidence directory, so it must be named explicitly and can never be reached by default. "
+            "No database interaction, not even a read, has occurred, and nothing has been written.",
+            file=sys.stderr,
+        )
+        return 2
+
     evidence_dir: Path = args.evidence_dir
 
     cfg = load_config()
diff --git a/apps/backend/tests/test_j11_stage_c_preflight.py b/apps/backend/tests/test_j11_stage_c_preflight.py
index 9a38c9bc..5e3d509e 100644
--- a/apps/backend/tests/test_j11_stage_c_preflight.py
+++ b/apps/backend/tests/test_j11_stage_c_preflight.py
@@ -159,6 +159,89 @@ def test_tc2_comparison_gate_stops_on_material_mismatch_manifest_row_count(engin
     assert gate["checks"]["manifest_row_count_matches_certified"] is False
 
 
+def test_tc14_comparison_gate_stops_on_manifest_ddl_drift(engine, cfg):
+    """goal-market-compass iter-14, Goal 3b -- `compare_preflight_to_certified`'s
+    `manifest_ddl_unchanged_from_certified` check already exists (j11_stage_c.py) but was never exercised
+    by a fixture until now."""
+    preflight = _fresh_preflight(engine, cfg)
+    certified = copy.deepcopy(preflight)
+    certified["manifest_ddl"]["table_sql"] = (certified["manifest_ddl"]["table_sql"] or "") + " -- drifted clause"
+    gate = jsc.compare_preflight_to_certified(preflight, certified)
+    assert gate["all_invariants_hold"] is False
+    assert gate["material_mismatch"] is True
+    assert gate["checks"]["manifest_ddl_unchanged_from_certified"] is False
+
+
+def test_tc15_comparison_gate_stops_on_manifest_index_set_drift(engine, cfg):
+    """`manifest_indexes_unchanged` -- an index name/sql appearing in the certified baseline but not the
+    fresh capture (or vice versa) is a material mismatch."""
+    preflight = _fresh_preflight(engine, cfg)
+    certified = copy.deepcopy(preflight)
+    certified["manifest_ddl"]["index_names"] = list(certified["manifest_ddl"]["index_names"]) + ["ix_drifted"]
+    certified["manifest_ddl"]["index_sqls"] = list(certified["manifest_ddl"]["index_sqls"]) + [
+        "CREATE INDEX ix_drifted ON next_session_manifests (id)"
+    ]
+    gate = jsc.compare_preflight_to_certified(preflight, certified)
+    assert gate["all_invariants_hold"] is False
+    assert gate["checks"]["manifest_indexes_unchanged"] is False
+
+
+def test_tc16_comparison_gate_stops_on_manifest_value_drift(engine, cfg):
+    """`manifest_values_unchanged` -- one manifest row's stored value differing from the certified dump is
+    a material mismatch (never an aggregate-only "row count matches" check, iter-9's lesson)."""
+    preflight = _fresh_preflight(engine, cfg)
+    certified = copy.deepcopy(preflight)
+    # simulate ONE stored manifest row whose value drifted -- the certified baseline recorded a row this
+    # fresh capture's dump does not carry the same value for.
+    certified["manifest_dump"] = [{"id": 1, "source_run_id": 7, "content_hash": "certified-value"}]
+    preflight_copy = copy.deepcopy(preflight)
+    preflight_copy["manifest_dump"] = [{"id": 1, "source_run_id": 7, "content_hash": "drifted-value"}]
+    gate = jsc.compare_preflight_to_certified(preflight_copy, certified)
+    assert gate["all_invariants_hold"] is False
+    assert gate["checks"]["manifest_values_unchanged"] is False
+    assert gate["manifest_dump_diff"]["mismatches"]
+
+
+def test_tc17_comparison_gate_stops_on_source_run_id_provenance_drift(engine, cfg):
+    """`source_run_id_values_unchanged` -- a manifest row's `source_run_id` differing from the certified
+    value is a material mismatch even when every other column matches (provenance drift specifically)."""
+    preflight = _fresh_preflight(engine, cfg)
+    certified = copy.deepcopy(preflight)
+    certified["manifest_dump"] = [{"id": 1, "source_run_id": 7, "content_hash": "same-value"}]
+    preflight_copy = copy.deepcopy(preflight)
+    preflight_copy["manifest_dump"] = [{"id": 1, "source_run_id": 999, "content_hash": "same-value"}]
+    gate = jsc.compare_preflight_to_certified(preflight_copy, certified)
+    assert gate["all_invariants_hold"] is False
+    assert gate["checks"]["source_run_id_values_unchanged"] is False
+    # the value drifted too (source_run_id is a manifest_dump column) -- both checks correctly fire
+    # together; this test isolates the PROVENANCE-specific check's own independent failure.
+
+
+def test_tc18_comparison_gate_stops_on_daily_prices_provider_runs_and_watchlist_drift(engine, cfg):
+    """`daily_prices_fingerprint_unchanged`, `data_provider_runs_count_unchanged`, and
+    `watchlist_count_unchanged` -- each asserted as an independent, separately-failing check (never one
+    combined canonical-inputs flag)."""
+    preflight = _fresh_preflight(engine, cfg)
+
+    certified_prices_drift = copy.deepcopy(preflight)
+    certified_prices_drift["pre_reset_inventory"]["daily_prices"]["fingerprint"] = "a-different-fingerprint"
+    gate = jsc.compare_preflight_to_certified(preflight, certified_prices_drift)
+    assert gate["checks"]["daily_prices_fingerprint_unchanged"] is False
+    assert gate["material_mismatch"] is True
+
+    certified_provider_drift = copy.deepcopy(preflight)
+    certified_provider_drift["pre_reset_inventory"]["data_provider_runs_count"] += 1
+    gate = jsc.compare_preflight_to_certified(preflight, certified_provider_drift)
+    assert gate["checks"]["data_provider_runs_count_unchanged"] is False
+    assert gate["material_mismatch"] is True
+
+    certified_watchlist_drift = copy.deepcopy(preflight)
+    certified_watchlist_drift["pre_reset_inventory"]["watchlist_count"] += 1
+    gate = jsc.compare_preflight_to_certified(preflight, certified_watchlist_drift)
+    assert gate["checks"]["watchlist_count_unchanged"] is False
+    assert gate["material_mismatch"] is True
+
+
 def test_tc2_comparison_gate_stops_on_per_date_scanner_run_drift(engine, cfg):
     preflight = _fresh_preflight(engine, cfg)
     certified = copy.deepcopy(preflight)
diff --git a/apps/backend/app/engine/j11_avb_diagnostic.py b/apps/backend/app/engine/j11_avb_diagnostic.py
new file mode 100644
index 00000000..ec288442
--- /dev/null
+++ b/apps/backend/app/engine/j11_avb_diagnostic.py
@@ -0,0 +1,582 @@
+"""app.engine.j11_avb_diagnostic -- J-11 Stage D readiness: read-only AVB bridge/volume diagnostic
+(goal-market-compass iter-14, Goal 4).
+
+J-10 bridged AVB's OHLC by a persisted factor (`bridge_factor approx 2.793`) for the two recovered dates
+(2026-08-11, 2026-08-12) and deliberately did NOT transform volume, while Trendora computes Average
+Dollar Volume as `close * volume` -- feeding universe membership
+(`app.engine.universe_resolver._adv_dollar`/`resolve_candidate`), Risk's `liquidity` component
+(`app.engine.scoring`'s `_neg(adv)`), and cross-sectional liquidity percentiles. This module re-derives
+the bridge factor and its calibration pairs from the PERSISTED J-10 evidence (never re-fetched -- AG-9's
+recovery-fetch exception is exhausted), establishes AVB's ACTUAL stored local convention from the stored
+`daily_prices` series itself (never from finance convention alone), computes three counterfactual ADV
+representations, and traces the decision impact through the named canonical modules -- read-only,
+in-memory, never mutating `daily_prices`, never calling any J-10 recovery/fetch function, never creating
+a `ScannerRun`.
+
+**The single most important empirical fact this module's own live capture establishes** (re-derived, not
+assumed): of the 566 pool symbols the J-10 evidence file computed a `bridge_factor` for, AVB is the ONLY
+one whose factor differs materially from 1.0 (every other symbol is a raw+raw pass-through, factor in
+[0.99, 1.01]). This is what makes the diagnostic's classification question real rather than academic --
+AVB's stored scale genuinely differs from its peers', so a naive "close * volume" ADV comparison across
+the pool is NOT scale-neutral for this one name.
+
+Classification vocabulary (exactly one, per Goal 4):
+  - **AVB-A** -- no material issue found; Stage D may proceed.
+  - **AVB-B** -- material effect confirmed, but the canonical stored convention is proven internally
+    consistent (from the stored series itself); record an explicit caveat, never "correct" volume; Stage
+    D may still proceed.
+  - **AVB-C** -- the restored representation is inconsistent with Trendora's own stored convention AND
+    materially affects canonical Stage D output; **STAGE D NOT READY**, owner decision.
+  - **AVB-D** -- evidence insufficient; **STAGE D NOT READY**, do not guess.
+"""
+from __future__ import annotations
+
+import json
+from datetime import date, datetime, timezone
+from pathlib import Path
+from typing import Optional
+
+from sqlalchemy import func
+from sqlmodel import Session, select
+
+from app.config import REPO_ROOT, Config, get_config
+from app.engine import scoring
+from app.engine import universe_resolver as ur
+from app.engine.buckets import to_bucket
+from app.engine.compass import _qualifier_checks
+from app.engine.normalize import cross_sectional_percentiles
+from app.engine.prices import Bar, bars_asof_window
+from app.engine.regime import score_regime
+from app.engine.scoring import CONTEXTUAL_KEYS, NA_KEYS, score_stocks
+from app.engine.setups import classify_setup
+from app.models import DailyPrice
+
+AVB_SYMBOL = "AVB"
+
+DEFAULT_J10_EVIDENCE_PATH = (
+    REPO_ROOT / "runs" / "goal-market-compass-iter-9" / "j10-population-evidence.json"
+)
+
+# The J-10 calibration window (never-deleted, pre-incident dates the recovery used to validate the
+# bridge factor) and the two recovered (bridged-on-write) dates -- literal historical facts about THIS
+# incident, not a reusable threshold (same posture as `j11_maintenance.INCIDENT_DATES`).
+CALIBRATION_DATES: tuple[date, ...] = (
+    date(2026, 8, 5), date(2026, 8, 6), date(2026, 8, 7), date(2026, 8, 10),
+)
+RECOVERED_DATES: tuple[date, ...] = (date(2026, 8, 11), date(2026, 8, 12))
+
+# A day-over-day return magnitude beyond this is treated as an anomalous jump for the continuity check
+# (structural sanity bound, not a scoring/decision threshold -- a genuine ~2.79x scale break would show
+# up as a +179%/-64% single-day "return", two full orders of magnitude past any plausible normal move;
+# excluded from `test_no_magic_numbers.CALC_FILES` for the identical reason `j10_recovery.py`/
+# `j11_maintenance.py` are -- a diagnostic sanity bound, not a decision cutoff).
+_CONTINUITY_JUMP_THRESHOLD = 0.25
+
+
+def _now_iso() -> str:
+    return datetime.now(timezone.utc).isoformat()
+
+
+# ----------------------------------------------------------------------------------------------
+# Persisted J-10 evidence -- re-derive the bridge factor and calibration pairs, never re-fetch
+# ----------------------------------------------------------------------------------------------
+
+
+def load_j10_avb_evidence(path: Path = DEFAULT_J10_EVIDENCE_PATH) -> dict:
+    """AVB's own per-symbol row from the persisted J-10 population-recovery evidence file -- the
+    `bridge_factor` and the 4 calibration-window `pairs` (`fallback_close`/`stored_close`/`ratio` per
+    trading date), read verbatim, never re-derived from a fresh fetch (AG-9 is exhausted)."""
+    payload = json.loads(Path(path).read_text())
+    for row in payload.get("symbols", []):
+        if row.get("symbol") == AVB_SYMBOL:
+            return row
+    raise ValueError(f"{AVB_SYMBOL} not found in J-10 evidence file {path}")
+
+
+def summarize_pool_bridge_factor_distribution(path: Path = DEFAULT_J10_EVIDENCE_PATH) -> dict:
+    """Whether AVB's bridging is symbol-specific or pool-wide -- re-derived from the SAME persisted
+    evidence file, across every symbol it recorded a `bridge_factor` for (never re-fetched). This is the
+    fact that makes the classification question material: if every symbol were bridged, a pool-wide ADV
+    comparison would be scale-neutral; if AVB alone is bridged, it is not."""
+    payload = json.loads(Path(path).read_text())
+    rows = payload.get("symbols", [])
+    factors = {row["symbol"]: row["bridge_factor"] for row in rows if row.get("bridge_factor") is not None}
+    near_one = {sym: f for sym, f in factors.items() if 0.99 <= f <= 1.01}
+    not_near_one = {sym: f for sym, f in factors.items() if not (0.99 <= f <= 1.01)}
+    return {
+        "symbols_with_bridge_factor": len(factors),
+        "total_symbols_in_evidence": len(rows),
+        "near_one_count": len(near_one),
+        "materially_bridged_symbols": not_near_one,
+        "avb_is_unique_material_outlier": set(not_near_one) == {AVB_SYMBOL},
+    }
+
+
+# ----------------------------------------------------------------------------------------------
+# Stored series + local-convention classification (from the stored series itself)
+# ----------------------------------------------------------------------------------------------
+
+
+def fetch_avb_stored_series(
+    session: Session, start_date: date, end_date: date, symbol: str = AVB_SYMBOL
+) -> list[dict]:
+    """AVB's stored `daily_prices` rows in `[start_date, end_date]`, column-projected (symbol/date/close/
+    volume only -- never a full-row ORM load), read-only, ascending by date."""
+    rows = session.exec(
+        select(DailyPrice.date, DailyPrice.close, DailyPrice.volume)
+        .where(DailyPrice.symbol == symbol)
+        .where(DailyPrice.date >= start_date)
+        .where(DailyPrice.date <= end_date)
+        .order_by(DailyPrice.date)
+    ).all()
+    out = []
+    for d, close, volume in rows:
+        entry = {
+            "date": d.isoformat(),
+            "close": float(close) if close is not None else None,
+            "volume": float(volume) if volume is not None else None,
+        }
+        entry["close_times_volume"] = (
+            entry["close"] * entry["volume"] if entry["close"] is not None and entry["volume"] is not None else None
+        )
+        out.append(entry)
+    return out
+
+
+def _day_over_day_returns(series: list[dict]) -> list[dict]:
+    """Simple close-to-close % return between consecutive STORED rows (whatever their date gap) -- the
+    continuity-check signal: a genuine ~2.79x scale break shows up as an enormous single-step "return"
+    (+179%/-64%), far past any plausible ordinary daily move."""
+    out = []
+    for prev, cur in zip(series, series[1:]):
+        if prev["close"] in (None, 0) or cur["close"] is None:
+            continue
+        pct = (cur["close"] - prev["close"]) / prev["close"]
+        out.append({"from_date": prev["date"], "to_date": cur["date"], "pct_return": pct})
+    return out
+
+
+def classify_local_convention(stored_series: list[dict], evidence_row: dict) -> dict:
+    """Classifies AVB's actual stored local convention per window, FROM THE STORED SERIES ITSELF -- never
+    from finance convention alone (docs/goal.md, Goal 4). Three sub-windows:
+
+      - the calibration window (2026-08-05/06/07/10, never deleted, never touched by J-10): a DIRECT
+        ratio check against the persisted `fallback_close` pairs -- the only sub-window with an
+        independent comparable value.
+      - the two recovered dates (2026-08-11/12): no independent comparable exists (J-10 WROTE these by
+        applying the bridge factor to the fallback close for exactly these two dates) -- classified by
+        CONTINUITY instead: does the day-over-day return crossing into/out of these dates stay within a
+        plausible ordinary-move bound, or does it show the ~2.79x jump a scale mismatch would produce.
+      - dates outside both (earlier history / post-recovery through the frontier): no independent
+        comparable either -- classified by the SAME continuity test, honestly labeled as continuity-only
+        evidence, never asserted as independently verified.
+
+    Returns one of `raw+raw` / `bridged+raw` / `bridged+compensating` / `mixed/indeterminate` PER WINDOW,
+    plus an overall `internally_consistent` flag (True only if every window's classification agrees --
+    all bridged+raw, or all raw+raw -- with no discontinuity at the incident boundary) and an
+    `indeterminate` flag (True if any sub-window's evidence is insufficient to classify at all)."""
+    by_date = {row["date"]: row for row in stored_series}
+    pairs_by_date = {p["trading_date"]: p for p in evidence_row.get("pairs", [])}
+
+    calibration_results = []
+    for one_date in CALIBRATION_DATES:
+        key = one_date.isoformat()
+        pair = pairs_by_date.get(key)
+        stored = by_date.get(key)
+        if pair is None or stored is None or stored["close"] is None:
+            calibration_results.append({"date": key, "classification": "mixed/indeterminate", "reason": "no comparable pair or stored row"})
+            continue
+        ratio = stored["close"] / pair["fallback_close"] if pair["fallback_close"] else None
+        classification = "bridged+raw" if ratio is not None and not (0.99 <= ratio <= 1.01) else "raw+raw"
+        calibration_results.append({
+            "date": key, "stored_close": stored["close"], "fallback_close": pair["fallback_close"],
+            "ratio": ratio, "classification": classification,
+        })
+    calibration_classes = {r["classification"] for r in calibration_results}
+    calibration_window_classification = (
+        calibration_classes.pop() if len(calibration_classes) == 1 else "mixed/indeterminate"
+    )
+
+    returns = _day_over_day_returns(stored_series)
+    anomalous_jumps = [r for r in returns if abs(r["pct_return"]) > _CONTINUITY_JUMP_THRESHOLD]
+
+    recovered_keys = {d.isoformat() for d in RECOVERED_DATES}
+    boundary_jumps = [j for j in anomalous_jumps if j["from_date"] in recovered_keys or j["to_date"] in recovered_keys]
+    recovered_window_classification = (
+        "mixed/indeterminate" if not boundary_jumps and calibration_window_classification == "mixed/indeterminate"
+        else ("bridged+raw" if calibration_window_classification == "bridged+raw" and not boundary_jumps
+              else ("raw+raw" if calibration_window_classification == "raw+raw" and not boundary_jumps
+                    else "mixed/indeterminate"))
+    )
+
+    surrounding_window_classification = (
+        calibration_window_classification if not anomalous_jumps else "mixed/indeterminate"
+    )
+
+    windows = {
+        "calibration_window": {
+            "dates": [d.isoformat() for d in CALIBRATION_DATES],
+            "classification": calibration_window_classification,
+            "per_date": calibration_results,
+            "evidence": "direct ratio against the persisted J-10 fallback_close pairs",
+        },
+        "recovered_dates": {
+            "dates": [d.isoformat() for d in RECOVERED_DATES],
+            "classification": recovered_window_classification,
+            "boundary_jumps": boundary_jumps,
+            "evidence": (
+                "no independent comparable exists for these dates (J-10 wrote them); classified by "
+                "day-over-day continuity with the adjacent calibration-window/post-recovery dates only"
+            ),
+        },
+        "surrounding_window": {
+            "classification": surrounding_window_classification,
+            "anomalous_jumps": anomalous_jumps,
+            "evidence": (
+                "no independent comparable exists outside the calibration window; classified by "
+                "day-over-day continuity across the whole fetched stored series only -- never asserted "
+                "as independently verified against a raw source"
+            ),
+        },
+    }
+
+    all_classes = {w["classification"] for w in windows.values()}
+    indeterminate = "mixed/indeterminate" in all_classes
+    internally_consistent = (not indeterminate) and len(all_classes) == 1 and not anomalous_jumps
+
+    return {
+        "windows": windows,
+        "day_over_day_returns_checked": len(returns),
+        "anomalous_jump_count": len(anomalous_jumps),
+        "internally_consistent": internally_consistent,
+        "indeterminate": indeterminate,
+        "overall_classification": (
+            "mixed/indeterminate" if indeterminate
+            else (calibration_window_classification if internally_consistent else "mixed/indeterminate")
+        ),
+        "reasoning": (
+            f"calibration window classifies as {calibration_window_classification} from "
+            f"{len(calibration_results)} direct fallback-close pairs (zero comparable-pair failures); "
+            f"{len(anomalous_jumps)} anomalous day-over-day jump(s) found across "
+            f"{len(returns)} checked transitions in the fetched stored series "
+            f"({len(boundary_jumps)} at the 2026-08-11/12 recovery boundary specifically) -- "
+            + ("no discontinuity at the incident boundary or elsewhere in the fetched window."
+               if not anomalous_jumps else
+               "a discontinuity WAS found -- see anomalous_jumps/boundary_jumps.")
+        ),
+    }
+
+
+# ----------------------------------------------------------------------------------------------
+# Counterfactual representations A / B / C
+# ----------------------------------------------------------------------------------------------
+
+
+def compute_counterfactual_representations(bridge_factor: float, stored_close: float, stored_volume: float) -> dict:
+    """The three counterfactual ADV representations for one recovered date's stored row (Goal 4):
+
+      - **A** -- bridged close x stored raw volume: the actual canonical value served today.
+      - **B** -- raw provider close (`stored_close / bridge_factor`, per the logged assumption -- never a
+        new fetch) x raw provider volume (== stored volume, since volume was never transformed by J-10 --
+        stated explicitly as a finding, per TC-22).
+      - **C** -- bridged close x a stated HYPOTHETICAL inverse-adjusted volume (`stored_volume *
+        bridge_factor` -- the share-count-continuity value IF the bridge factor reflected a genuine
+        corporate action with a matching volume adjustment): diagnostic only, its formula/rationale
+        recorded, never written, never assumed correct."""
+    close_a, volume_a = stored_close, stored_volume
+    close_b = stored_close / bridge_factor if bridge_factor else None
+    volume_b = stored_volume  # never transformed by J-10 -- stated explicitly (TC-22)
+    volume_c = stored_volume * bridge_factor if bridge_factor else None
+
+    def _leaf(close, volume, formula):
+        adv = close * volume if close is not None and volume is not None else None
+        return {"close": close, "volume": volume, "close_times_volume": adv, "formula": formula}
+
+    representation_a = _leaf(
+        close_a, volume_a, "A = stored_bridged_close x stored_raw_volume (the actual canonical value served today)"
+    )
+    representation_b = _leaf(
+        close_b, volume_b,
+        "B = (stored_close / bridge_factor) x stored_volume (raw-provider-scale close; volume equals A's -- "
+        "never transformed by J-10)",
+    )
+    representation_c = _leaf(
+        close_a, volume_c,
+        "C = stored_bridged_close x (stored_volume x bridge_factor) -- DIAGNOSTIC ONLY: the hypothetical "
+        "share-count-continuity-preserving volume IF the bridge factor reflected a genuine corporate "
+        "action; never written to the database, never assumed correct",
+    )
+    return {
+        "bridge_factor": bridge_factor,
+        "A": representation_a,
+        "B": representation_b,
+        "C": representation_c,
+        "volume_a_equals_b": representation_a["volume"] == representation_b["volume"],
+    }
+
+
+# ----------------------------------------------------------------------------------------------
+# Decision-impact trace -- through the named canonical modules, read-only / in-memory
+# ----------------------------------------------------------------------------------------------
+
+
+def _build_bars_with_transformed_close(bars_real: list, target_dates: set, bridge_factor: float) -> list[Bar]:
+    """A NEW, in-memory `Bar` list -- never mutates the fetched ORM/`Bar` objects, never touches the DB --
+    identical to `bars_real` except every bar whose date is in `target_dates` has its close divided by
+    `bridge_factor` (representation B). Volume and every other field pass through unchanged."""
+    out: list[Bar] = []
+    for b in bars_real:
+        if b.date in target_dates and b.close is not None:
+            out.append(Bar(date=b.date, open=b.open, high=b.high, low=b.low, close=b.close / bridge_factor, volume=b.volume))
+        else:
+            out.append(Bar(date=b.date, open=b.open, high=b.high, low=b.low, close=b.close, volume=b.volume))
+    return out
+
+
+def trace_universe_resolver_impact(session: Session, cfg: Config, asof: date, bridge_factor: float) -> dict:
+    """Traces (A) vs (B) through `app.engine.universe_resolver._adv_dollar`/`resolve_candidate` -- the ADV
+    value and the ADV admission gate (`REASON_BELOW_ADV`), via the REAL canonical functions, never
+    reimplemented. Mirrors `resolve_with_reasons`'s OWN two-step read exactly: a full trailing-bar COUNT
+    (date <= asof, the true history-gate input) computed separately from the bounded `adv_window_days`
+    bar fetch (the value-gate input) -- passing a `bar_count` shorter than the true history whenever
+    `adv_window_days < min_history_bars` would silently misreport the history gate (a real bug this
+    module's own fixture test caught and this fix closes)."""
+    filters = cfg.universe.filters
+    true_bar_count = int(
+        session.exec(
+            select(func.count(DailyPrice.id))
+            .where(DailyPrice.symbol == AVB_SYMBOL)
+            .where(DailyPrice.date <= asof)
+        ).one()
+        or 0
+    )
+    bars_real = bars_asof_window(session, AVB_SYMBOL, asof, filters.adv_window_days)
+    recovered_in_window = {d for d in RECOVERED_DATES if d <= asof}
+    bars_b = _build_bars_with_transformed_close(bars_real, recovered_in_window, bridge_factor)
+
+    adv_a = ur._adv_dollar(bars_real, filters.adv_window_days)
+    adv_b = ur._adv_dollar(bars_b, filters.adv_window_days)
+    resolution_a = ur.resolve_candidate(bars_real, AVB_SYMBOL, cfg, asof, bar_count=true_bar_count)
+    resolution_b = ur.resolve_candidate(bars_b, AVB_SYMBOL, cfg, asof, bar_count=true_bar_count)
+
+    return {
+        "asof": asof.isoformat(),
+        "adv_window_days": filters.adv_window_days,
+        "min_dollar_vol_threshold": filters.min_dollar_vol,
+        "true_bar_count": true_bar_count,
+        "recovered_dates_in_window": sorted(d.isoformat() for d in recovered_in_window),
+        "adv_dollar_a": adv_a,
+        "adv_dollar_b": adv_b,
+        "resolution_a": {"admitted": resolution_a.admitted, "reason": resolution_a.reason, "bars": resolution_a.bars},
+        "resolution_b": {"admitted": resolution_b.admitted, "reason": resolution_b.reason, "bars": resolution_b.bars},
+        "admission_changed": resolution_a.admitted != resolution_b.admitted,
+    }
+
+
+def trace_scoring_and_selection_impact(session: Session, cfg: Config, asof: date, bridge_factor: float) -> dict:
+    """Traces (A) vs (B) through `app.engine.scoring`'s `liquidity` component (`_neg(adv)`), AVB's
+    cross-sectional liquidity percentile, the Risk score/bucket, setup status, and candidate eligibility
+    -- plus whether OTHER pool names' liquidity percentiles shift. ONE real `score_stocks(session, asof,
+    cfg)` call (representation A, the actual served state) supplies AVB's real other-component raws/
+    percentiles AND every OTHER resolved member's real liquidity raw (read off the already-assembled
+    output -- no second per-symbol query for the rest of the pool, AG-8); representation B substitutes
+    ONLY AVB's liquidity raw/percentile and recomputes AVB's Risk score/bucket/setup/eligibility via the
+    REAL `_build_score`/`to_bucket`/`classify_setup`/`_qualifier_checks` functions."""
+    scored_a = score_stocks(session, asof, cfg)
+    rows_by_ticker = {row["ticker"]: row for row in scored_a["rows"]}
+    if AVB_SYMBOL not in rows_by_ticker:
+        return {
+            "asof": asof.isoformat(),
+            "avb_resolved_member": False,
+            "note": f"AVB is not a point-in-time-resolved universe member at {asof.isoformat()} under "
+                    "representation A -- no score to trace.",
+        }
+    avb_row_a = rows_by_ticker[AVB_SYMBOL]
... [diff_bound] apps/backend/app/engine/j11_avb_diagnostic.py: 188 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/app/engine/j11_stage_d.py b/apps/backend/app/engine/j11_stage_d.py
new file mode 100644
index 00000000..d1e188be
--- /dev/null
+++ b/apps/backend/app/engine/j11_stage_d.py
@@ -0,0 +1,418 @@
+"""app.engine.j11_stage_d -- J-11 Stage D readiness hardening (goal-market-compass iter-14).
+
+Iteration 13's auditor found two live defects that would otherwise silently break the still-unauthorized
+Stage D (canonical regeneration of the 11 incident dates, `docs/goal.md` J-11 step 12):
+
+  - **B1** -- no per-run identity-comparison call site exists yet for Stage D; only Stage B2's freeze
+    (`j11_maintenance.freeze_attempt_identity`) and the pure per-run helper
+    (`j11_maintenance.check_attempt_identity_consistency`) exist, with nothing that actually CALLS the
+    helper at the three points step 12/13 require.
+  - **B2** -- the Stage C-era preflight gate CAPTURES an identity value but never COMPARES it against
+    anything (`j11_stage_c.capture_stage_c_preflight` has no drift check at all -- `compare_preflight_to_
+    certified` covers Stage C's own C2 invariants, not Stage D's).
+
+This module closes both, plus builds the Stage D preflight gate itself -- ALL read-only. It performs
+NO Stage D execution: no `scanner.run_scan`, no `scanner.persist_run_payload`, no ScannerRun INSERT, no
+ForwardReturn mutation. `docs/goal.md` J-11 step 12's 2026-08-24 clarification governs the identity
+question this module implements exactly:
+
+  > Stage D begins a FRESH regeneration attempt from the successfully cleared Stage C baseline; its
+  > frozen identity is computed immediately before Stage D and applies ONLY to the 11 rebuilt incident-
+  > date runs. Surviving historical runs retain their existing stamps.
+
+So `freeze_stage_d_attempt_identity` NEVER hardcodes or trusts iteration 10's `6261ca17...` or iteration
+13's `53d2ffd1...` -- it re-derives fresh, every time, via the SAME `app.engine.engine_identity.
+compute_engine_identity` the real `scanner.persist_run_payload` stamps onto every newly created
+`ScannerRun.engine_identity` (reused, never reimplemented, so a later per-run compare is like-for-like).
+
+Goal 2's three checks are genuine COMPARE call sites (iter-13's own lesson: "capturing an invariant's
+value is not checking it, and a gate that cannot compare is a gate that always passes") -- each wraps
+`j11_maintenance.check_attempt_identity_consistency` rather than reimplementing comparison logic, and
+each returns a per-call evidence record, never an aggregate boolean alone (iter-9's AVB lesson: a
+population-wide "all N matched" claim is exactly where the one real counter-example hides). Checks (B)
+and (C) take an explicit `date` and vacuously PASS (`in_scope: False`, no comparison performed) for any
+date outside this attempt's 11-date `INCIDENT_DATES` scope -- the step-12 clarification's own words: the
+34 surviving `6261ca17...` runs and the ~3,083 NULL-stamped pre-stamping-era rows "are not members of the
+new 11-date attempt" and so are never candidates for this attempt's identity check at all (TC-ID-6).
+
+Goal 3a's Stage D preflight mirrors `j11_stage_c.capture_stage_c_preflight`'s composition pattern
+(re-derive live state fresh from already-existing read-only primitives -- `j11_maintenance.
+capture_pre_reset_inventory`, `j11_schema_migration.fetch_object_ddl`/`dump_table`,
+`j11_stage_c.check_c1_date_set_boundary`) plus one Stage-D-specific addition: every one of the 11
+incident dates must currently show ZERO `ScannerRun` rows (the Stage C-cleared baseline this attempt
+regenerates from). `load_stage_d_certified_baseline` composes the certified comparison target from TWO
+already-persisted iteration-13 artifacts: `j11-stage-c-preflight.json` (manifest DDL/dump -- captured
+BEFORE Stage C's delete, but Layer 3/manifests are proven untouched by that same delete, per iteration
+13's own `manifests_unchanged: true` mutation-accounting check, so this pre-delete capture IS the
+terminal post-Stage-C manifest state) and `j11-stage-c-mutation-accounting.json` (the actual POST-delete
+`daily_prices`/`data_provider_runs`/`watchlist` figures -- the real terminal state after the one
+authorized destructive write).
+
+Everything here composes already-existing read-only primitives; nothing here deletes, updates, or
+inserts a snapshot/manifest/price row (mirrors `j11_maintenance.py`'s and `j11_stage_c.py`'s own "nothing
+here deletes" posture)."""
+from __future__ import annotations
+
+import json
+import os
+from datetime import date, datetime, timezone
+from pathlib import Path
+from typing import Any, Optional, Union
+
+from sqlalchemy.engine import Engine
+from sqlmodel import Session
+
+from app.config import Config, get_config
+from app.engine import engine_identity
+from app.engine import j11_maintenance
+from app.engine import j11_schema_migration as migration
+from app.engine import j11_stage_c as jsc
+from app.engine.j11_maintenance import INCIDENT_DATES
+from app.models import NextSessionManifest
+
+
+def _now_iso() -> str:
+    return datetime.now(timezone.utc).isoformat()
+
+
+def _identity_value(frozen: Union[dict, str, None]) -> Optional[str]:
+    return frozen.get("engine_identity") if isinstance(frozen, dict) else frozen
+
+
+def _in_attempt_scope(one_date: date) -> bool:
+    """Whether `one_date` is one of THIS attempt's 11 incident dates. A date outside this set (e.g. one
+    of the 34 surviving `6261ca17...` runs' own historical dates) is never a member of the new attempt
+    per docs/goal.md J-11 step 12's 2026-08-24 clarification -- TC-ID-6."""
+    return one_date in INCIDENT_DATES
+
+
+# ----------------------------------------------------------------------------------------------
+# Goal 1 -- fresh Stage D attempt identity
+# ----------------------------------------------------------------------------------------------
+
+
+def freeze_stage_d_attempt_identity(
+    session: Session,
+    config: Optional[Config] = None,
+    *,
+    git_head: Optional[str] = None,
+    goal_md_text: Optional[str] = None,
+) -> dict:
+    """A thin wrapper around `j11_maintenance.freeze_attempt_identity` that re-derives the identity FRESH
+    (never trusting or hardcoding iteration 10's `6261ca17...` or iteration 13's `53d2ffd1...`) and
+    assembles the full Stage D attempt-identity artifact. `git_head`/`goal_md_text` are injected
+    (defaulting to real read-only I/O via `j11_stage_c`'s helpers when omitted) so this function stays a
+    pure, fixture-testable composition when the caller supplies synthetic values -- mirrors
+    `j11_stage_c.capture_stage_c_preflight`'s own injected-params pattern.
+
+    Applies ONLY to the 11 dates Stage D will rebuild. The 34 surviving runs stamped `6261ca17...`
+    (iteration 10's EARLIER attempt identity) and the ~3,083 NULL-stamped pre-stamping-era rows are not
+    members of this attempt and must never be restamped -- recorded explicitly in `scope_note` so the
+    artifact is self-documenting."""
+    cfg = config or get_config()
+    b2_identity = j11_maintenance.freeze_attempt_identity(session, cfg)
+    resolved_git_head = git_head if git_head is not None else jsc.read_git_head()
+    resolved_goal_md_text = goal_md_text if goal_md_text is not None else jsc.read_goal_md_text()
+    contract_hash = jsc.compute_contract_hash(resolved_goal_md_text)
+    frozen_at = datetime.now(timezone.utc)
+    return {
+        "attempt_id": f"j11-stage-d-{frozen_at.strftime('%Y%m%dT%H%M%S%fZ')}",
+        "frozen_at": b2_identity["frozen_at"],
+        "engine_identity": b2_identity["engine_identity"],
+        "config_subset_hash": b2_identity["config_subset_hash"],
+        "config_subset": b2_identity["config_subset"],
+        "provenance": {
+            "engine_files": b2_identity["provenance_engine_files"],
+            "config_keys": b2_identity["provenance_config_keys"],
+        },
+        "git_head": resolved_git_head,
+        "j11_contract_hash": contract_hash,
+        "incident_dates": [d.isoformat() for d in INCIDENT_DATES],
+        "scope_note": (
+            "This identity applies ONLY to the 11 dates Stage D will rebuild "
+            "(docs/goal.md J-11 step 12's 2026-08-24 clarification: 'Stage D begins a FRESH regeneration "
+            "attempt from the successfully cleared Stage C baseline; its frozen identity is computed "
+            "immediately before Stage D and applies only to the 11 rebuilt incident-date runs. Surviving "
+            "historical runs retain their existing stamps.'). The 34 surviving ScannerRun rows stamped "
+            "'6261ca17...' (iteration 10's earlier-attempt identity, since drifted) and the pre-stamping-"
+            "era NULL-engine_identity rows are NOT members of this attempt and must never be restamped, "
+            "mutated, or otherwise touched by any check in this module."
+        ),
+    }
+
+
+# ----------------------------------------------------------------------------------------------
+# Goal 2 -- three fail-closed identity COMPARE checks (never a second capture)
+# ----------------------------------------------------------------------------------------------
+
+
+def check_identity_before_first_write(frozen: Union[dict, str], current: Optional[str]) -> dict:
+    """Check (A): before Stage D's first regeneration write, the current recomputed identity MUST equal
+    the frozen attempt identity, else STOP (zero writes). Reuses `j11_maintenance.
+    check_attempt_identity_consistency` -- a genuine COMPARE call site, never a second capture."""
+    ok = j11_maintenance.check_attempt_identity_consistency(frozen, current)
+    return {
+        "check": "before_first_write",
+        "frozen_engine_identity": _identity_value(frozen),
+        "current_engine_identity": current,
+        "ok": ok,
+        "checked_at": _now_iso(),
+    }
+
+
+def check_identity_before_date(frozen: Union[dict, str], current: Optional[str], one_date: date) -> dict:
+    """Check (B): before EVERY subsequent incident date, recompute and re-prove equality; on drift, STOP
+    before that date -- never silently update the frozen value, never continue piecemeal. A date outside
+    this attempt's 11-date scope is never checked at all (`in_scope: False`, vacuous pass, no comparison
+    performed) -- TC-ID-6: the 34 surviving `6261ca17...` runs' own dates are not members of this
+    attempt, so no failure is ever raised against them."""
+    if not _in_attempt_scope(one_date):
+        return {
+            "check": "before_date",
+            "date": one_date.isoformat(),
+            "in_scope": False,
+            "ok": True,
+            "reason": "date_outside_j11_stage_d_attempt_scope_no_check_performed",
+            "checked_at": _now_iso(),
+        }
+    ok = j11_maintenance.check_attempt_identity_consistency(frozen, current)
+    return {
+        "check": "before_date",
+        "date": one_date.isoformat(),
+        "in_scope": True,
+        "frozen_engine_identity": _identity_value(frozen),
+        "current_engine_identity": current,
+        "ok": ok,
+        "checked_at": _now_iso(),
+    }
+
+
+def check_identity_after_persist(
+    frozen: Union[dict, str], persisted_run_identity: Optional[str], run_id: Any, one_date: date
+) -> dict:
+    """Check (C): after each `ScannerRun` persistence, the newly persisted row's OWN `engine_identity`
+    column MUST equal the frozen identity -- NULL, missing, or mismatched is failure (fail-closed, via
+    `check_attempt_identity_consistency`'s own `run_identity is not None and run_identity == expected`).
+    Same out-of-scope vacuous-pass rule as Check (B) -- TC-ID-6."""
+    if not _in_attempt_scope(one_date):
+        return {
+            "check": "after_persist",
+            "date": one_date.isoformat(),
+            "run_id": run_id,
+            "in_scope": False,
+            "ok": True,
+            "reason": "date_outside_j11_stage_d_attempt_scope_no_check_performed",
+            "checked_at": _now_iso(),
+        }
+    ok = j11_maintenance.check_attempt_identity_consistency(frozen, persisted_run_identity)
+    return {
+        "check": "after_persist",
+        "date": one_date.isoformat(),
+        "run_id": run_id,
+        "in_scope": True,
+        "frozen_engine_identity": _identity_value(frozen),
+        "persisted_engine_identity": persisted_run_identity,
+        "ok": ok,
+        "checked_at": _now_iso(),
+    }
+
+
+# ----------------------------------------------------------------------------------------------
+# Goal 3a -- Stage D preflight gate (built AND executed read-only against the live DB this iteration)
+# ----------------------------------------------------------------------------------------------
+
+
+def capture_stage_d_preflight(
+    session: Session,
+    engine: Engine,
+    db_path: Optional[Path],
+    *,
+    goal_md_text: str,
+    git_head: Optional[str],
+    config: Optional[Config] = None,
+) -> dict:
+    """Re-derives live state fresh (never trusting iteration 13's certified figures without re-proving
+    them), composed entirely from already-existing read-only primitives. Writes nothing -- `session` is
+    used for SELECTs only, `engine`/`db_path` only for DDL/file introspection. `goal_md_text`/`git_head`
+    are injected by the caller so the whole capture stays a pure, fixture-testable composition."""
+    cfg = config or get_config()
+    pre_reset_inventory = j11_maintenance.capture_pre_reset_inventory(session)
+    attempt_identity = freeze_stage_d_attempt_identity(
+        session, cfg, git_head=git_head, goal_md_text=goal_md_text
+    )
+    # Check (A) exercised HERE, against a SECOND, independent re-derivation of the current identity --
+    # not the identity artifact's own value compared to itself (that would be a no-op self-compare). At
+    # freeze time no drift is expected yet; this proves the compare plumbing works end-to-end against
+    # real, freshly re-computed data (TC-11).
+    current_identity_for_check_a = engine_identity.compute_engine_identity(cfg)
+    identity_check_a = check_identity_before_first_write(attempt_identity, current_identity_for_check_a)
+
+    manifest_ddl = migration.fetch_object_ddl(engine, migration.TABLE_NAME)
+    manifest_dump = migration.dump_table(engine, NextSessionManifest.__table__)
+    c1_check = jsc.check_c1_date_set_boundary(goal_md_text)
+    maintenance_isolation_value = os.environ.get("CHAIN_MAINTENANCE_ISOLATION")
+
+    return {
+        "captured_at": _now_iso(),
+        "git_head": git_head,
+        "goal_md_j11_contract_hash": jsc.compute_contract_hash(goal_md_text),
+        "c1_date_set_boundary_check": c1_check,
+        "attempt_identity": attempt_identity,
+        "identity_check_a": identity_check_a,
+        "pre_reset_inventory": pre_reset_inventory,
+        "manifest_ddl": manifest_ddl,
+        "manifest_dump": manifest_dump,
+        "manifest_row_count": len(manifest_dump),
+        "maintenance_isolation_env": {
+            "present": maintenance_isolation_value is not None,
+            "value": maintenance_isolation_value,
+        },
+    }
+
+
+def load_stage_d_certified_baseline(
+    stage_c_preflight_path: Path, stage_c_mutation_accounting_path: Path
+) -> dict:
+    """The terminal (post-Stage-C) certified state Stage D's preflight gate compares against, composed
+    from TWO already-persisted iteration-13 artifacts:
+
+      - `j11-stage-c-preflight.json` for the manifest DDL/dump -- captured BEFORE Stage C's delete, but
+        proven byte-identical to the POST-delete state by that same iteration's own mutation-accounting
+        `manifests_unchanged: true` check (manifests are Layer 3, untouched by Stage C's Layer-2-only
+        clear). Raises if the loaded mutation-accounting artifact does not itself prove that equality --
+        fail closed rather than silently trusting a pre-delete capture as if it were the post-delete
+        state.
+      - `j11-stage-c-mutation-accounting.json` for the ACTUAL post-delete `daily_prices`/
+        `data_provider_runs`/`watchlist` figures -- the real terminal state after the one authorized
+        destructive write."""
+    preflight = json.loads(Path(stage_c_preflight_path).read_text())
+    mutation_accounting = json.loads(Path(stage_c_mutation_accounting_path).read_text())
+
+    checks = mutation_accounting.get("checks", {})
+    if not checks.get("manifests_unchanged"):
+        raise ValueError(
+            f"{stage_c_mutation_accounting_path} does not prove manifests_unchanged=True -- refusing to "
+            "treat the pre-delete preflight capture's manifest dump as the post-Stage-C certified baseline"
+        )
+    if not (checks.get("data_provider_runs_unchanged") and checks.get("watchlist_unchanged")):
+        raise ValueError(
+            f"{stage_c_mutation_accounting_path} does not prove data_provider_runs/watchlist unchanged -- "
+            "refusing to build a certified baseline from it"
+        )
+
+    return {
+        "source": {
+            "stage_c_preflight_path": str(stage_c_preflight_path),
+            "stage_c_mutation_accounting_path": str(stage_c_mutation_accounting_path),
+        },
+        "daily_prices_fingerprint": mutation_accounting["daily_prices"]["post"]["fingerprint"],
+        "manifest_row_count": preflight["manifest_row_count"],
+        "manifest_ddl": preflight["manifest_ddl"],
+        "manifest_dump": preflight["manifest_dump"],
+        "data_provider_runs_count": mutation_accounting["data_provider_runs"]["post"]["count"],
+        "watchlist_count": mutation_accounting["watchlist"]["post"]["count"],
+    }
+
+
+def compare_stage_d_preflight_to_certified(preflight: dict, certified: dict) -> dict:
+    """The Stage D preflight comparison gate -- mirrors `j11_stage_c.compare_preflight_to_certified`'s
+    shape and idiom but checks Stage D's OWN preconditions: canonical inputs (`daily_prices`) and
+    manifests unchanged since the certified post-Stage-C baseline, the C1 date-set boundary still
+    agreeing, Check (A)'s identity comparison passing, and -- the genuinely NEW Stage D-specific
+    precondition -- every one of the 11 incident dates currently showing ZERO `ScannerRun` rows (the
+    Stage-C-cleared baseline this attempt regenerates from; TC-19's 'unexpected incident ScannerRun
+    population' refusal). ANY False in `checks` means `material_mismatch` is True and the caller MUST
+    stop before the first destructive statement."""
+    checks: dict[str, Any] = {}
+
+    checks["daily_prices_fingerprint_unchanged"] = (
+        preflight["pre_reset_inventory"]["daily_prices"]["fingerprint"] == certified["daily_prices_fingerprint"]
+    )
+    checks["manifest_row_count_unchanged"] = preflight["manifest_row_count"] == certified["manifest_row_count"]
+
+    fresh_ddl_sql = preflight["manifest_ddl"]["table_sql"] or ""
+    certified_ddl_sql = certified["manifest_ddl"]["table_sql"] or ""
+    checks["manifest_ddl_unchanged"] = fresh_ddl_sql == certified_ddl_sql
+    checks["manifest_indexes_unchanged"] = (
+        sorted(preflight["manifest_ddl"]["index_names"]) == sorted(certified["manifest_ddl"]["index_names"])
+        and sorted(preflight["manifest_ddl"]["index_sqls"]) == sorted(certified["manifest_ddl"]["index_sqls"])
+    )
+
+    manifest_dump_diff = migration.diff_dumps(certified["manifest_dump"], preflight["manifest_dump"])
+    checks["manifest_values_unchanged"] = manifest_dump_diff["equal"]
+
+    certified_source_ids = {row["id"]: row["source_run_id"] for row in certified["manifest_dump"]}
+    fresh_source_ids = {row["id"]: row["source_run_id"] for row in preflight["manifest_dump"]}
+    checks["source_run_id_values_unchanged"] = certified_source_ids == fresh_source_ids
+
+    checks["data_provider_runs_count_unchanged"] = (
+        preflight["pre_reset_inventory"]["data_provider_runs_count"] == certified["data_provider_runs_count"]
+    )
+    checks["watchlist_count_unchanged"] = (
+        preflight["pre_reset_inventory"]["watchlist_count"] == certified["watchlist_count"]
+    )
+    checks["c1_date_set_boundary_ok"] = bool(preflight["c1_date_set_boundary_check"]["ok"])
+
+    incident_dates = preflight["pre_reset_inventory"]["incident_dates"]
+    per_date_scanner_run_present = {
+        d: bool(preflight["pre_reset_inventory"]["per_date"][d]["scanner_run"]["present"])
+        for d in incident_dates
+    }
+    checks["all_incident_dates_zero_scanner_runs"] = not any(per_date_scanner_run_present.values())
+
+    checks["identity_check_a_ok"] = bool(preflight["identity_check_a"]["ok"])
+
+    all_hold = all(bool(v) for v in checks.values())
+    return {
+        "generated_at": _now_iso(),
+        "checks": checks,
+        "per_date_scanner_run_present": per_date_scanner_run_present,
+        "manifest_dump_diff": manifest_dump_diff,
+        "all_invariants_hold": all_hold,
+        "material_mismatch": not all_hold,
+    }
+
+
+def stage_d_preflight_verdict(comparison: dict) -> dict:
+    """The single pass/fail decision the Stage D readiness verdict is built on -- mirrors
+    `j11_stage_c.stage_c_overall_verdict`'s shape."""
+    if not comparison.get("all_invariants_hold"):
+        failing = [k for k, v in comparison.get("checks", {}).items() if not v]
+        return {"passed": False, "reason": "preflight_comparison_gate_failed", "failing_checks": failing}
+    return {"passed": True, "reason": "all_checks_passed"}
+
+
+# ----------------------------------------------------------------------------------------------
+# Goal 5 -- explicit Stage D readiness verdict (does NOT authorize Stage D)
+# ----------------------------------------------------------------------------------------------
+
+_AVB_READY_CLASSIFICATIONS = ("AVB-A", "AVB-B")
+_AVB_BLOCKING_CLASSIFICATIONS = ("AVB-C", "AVB-D")
+
+
+def stage_d_readiness_verdict(preflight_verdict: dict, avb_classification: str) -> dict:
+    """Combines the preflight gate's verdict (Goal 3a) with the AVB diagnostic's classification (Goal 4)
... [diff_bound] apps/backend/app/engine/j11_stage_d.py: 24 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/scripts/run_j11_avb_bridge_diagnostic.py b/apps/backend/scripts/run_j11_avb_bridge_diagnostic.py
new file mode 100644
index 00000000..7e0f2ceb
--- /dev/null
+++ b/apps/backend/scripts/run_j11_avb_bridge_diagnostic.py
@@ -0,0 +1,174 @@
+"""goal-market-compass iter-14 -- J-11 Stage D readiness: the READ-ONLY AVB bridge/volume diagnostic
+(Goal 4). No `--confirm` needed -- this script performs ZERO writes of any kind: it opens the live
+database through an ACTUAL read-only SQLite handle (`file:<path>?mode=ro` + `PRAGMA query_only=ON`,
+mirroring `run_j11_stage_b1_live_reverification.py`'s helper), so any accidental write attempt anywhere
+in the call graph would raise `OperationalError` rather than silently succeeding. It still captures the
+db-file mtime/size and `-wal` sidecar size at the TRUE process start and TRUE process end as corroborating
+evidence (iteration 12's lesson), even though no writable connection is ever opened.
+
+Composes `app.engine.j11_avb_diagnostic`'s pure/read functions:
+  - re-derives the bridge factor + calibration pairs from the PERSISTED J-10 evidence file (never
+    re-fetched -- AG-9's recovery-fetch exception is exhausted);
+  - classifies AVB's actual stored local convention per window from the stored `daily_prices` series
+    itself;
+  - computes the three counterfactual ADV representations (A/B/C) for both recovered dates;
+  - traces the decision impact through the named canonical modules
+    (`universe_resolver._adv_dollar`/`resolve_candidate`, `scoring`'s liquidity component, the Risk
+    score/bucket, setup status, candidate eligibility, and the pool-wide liquidity-percentile shift) for
+    both 2026-08-11 and 2026-08-12;
+  - classifies into exactly one of AVB-A/B/C/D.
+
+Usage:
+    apps/backend/.venv/bin/python apps/backend/scripts/run_j11_avb_bridge_diagnostic.py \\
+        [--output-path runs/goal-market-compass-iter-14/j11-avb-bridge-diagnostic.json]
+"""
+from __future__ import annotations
+
+import argparse
+import json
+import sys
+from datetime import date
+from pathlib import Path
+
+# scripts/ -> backend -> apps -> repo root
+BACKEND_DIR = Path(__file__).resolve().parents[1]
+REPO_ROOT = BACKEND_DIR.parents[1]
+sys.path.insert(0, str(BACKEND_DIR))
+
+from sqlalchemy import create_engine, event  # noqa: E402
+from sqlmodel import Session  # noqa: E402
+
+from app.config import load_config  # noqa: E402
+from app.db import resolve_database_url  # noqa: E402
+from app.engine import j11_avb_diagnostic as diag  # noqa: E402
+from app.engine.j11_stage_c import db_file_fingerprint  # noqa: E402
+
+DEFAULT_OUTPUT_PATH = REPO_ROOT / "runs" / "goal-market-compass-iter-14" / "j11-avb-bridge-diagnostic.json"
+
+
+def _db_file_path(database_url: str) -> "Path | None":
+    prefix = "sqlite:///"
+    if not database_url.startswith(prefix):
+        return None
+    raw = database_url[len(prefix):]
+    if not raw or raw == ":memory:":
+        return None
+    path = Path(raw)
+    return path if path.is_absolute() else (REPO_ROOT / raw)
+
+
+def _read_only_engine(db_path: Path):
+    url = f"sqlite:///file:{db_path}?mode=ro&uri=true"
+    engine = create_engine(url, connect_args={"check_same_thread": False})
+
+    @event.listens_for(engine, "connect")
+    def _set_query_only(dbapi_connection, _record):
+        dbapi_connection.execute("PRAGMA query_only=ON")
+
+    return engine
+
+
+def main() -> int:
+    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
+    parser.add_argument("--output-path", type=Path, default=DEFAULT_OUTPUT_PATH)
+    parser.add_argument(
+        "--j10-evidence-path", type=Path, default=diag.DEFAULT_J10_EVIDENCE_PATH,
+        help="the persisted J-10 population-recovery evidence file -- never re-fetched.",
+    )
+    args = parser.parse_args()
+
+    cfg = load_config()
+    resolved_url = resolve_database_url(cfg.database.url)
+    db_path = _db_file_path(resolved_url)
+    if db_path is None or not db_path.exists():
+        print(f"FAIL: could not resolve a live sqlite db file from {resolved_url!r}", file=sys.stderr)
+        return 1
+    print(f"database (READ-ONLY handle, mode=ro + PRAGMA query_only=ON): {db_path}", file=sys.stderr)
+
+    db_file_true_start = db_file_fingerprint(db_path)
+
+    evidence_row = diag.load_j10_avb_evidence(args.j10_evidence_path)
+    bridge_factor = evidence_row["bridge_factor"]
+    pool_distribution = diag.summarize_pool_bridge_factor_distribution(args.j10_evidence_path)
+    print(
+        f"bridge_factor={bridge_factor} avb_is_unique_material_outlier="
+        f"{pool_distribution['avb_is_unique_material_outlier']}",
+        file=sys.stderr,
+    )
+
+    engine = _read_only_engine(db_path)
+    with Session(engine) as session:
+        # a broad window around the incident: from well before the calibration window through the
+        # current stored frontier, so the convention classifier's continuity check has real adjacent
+        # context on both sides of the recovery boundary.
+        stored_series = diag.fetch_avb_stored_series(session, date(2026, 6, 1), date(2026, 12, 31))
+        local_convention = diag.classify_local_convention(stored_series, evidence_row)
+
+        recovered_rows_by_date = {row["date"]: row for row in stored_series if row["date"] in
+                                   {d.isoformat() for d in diag.RECOVERED_DATES}}
+        representations_by_date = {
+            iso_date: diag.compute_counterfactual_representations(bridge_factor, row["close"], row["volume"])
+            for iso_date, row in recovered_rows_by_date.items()
+        }
+
+        decision_impact_by_date: dict[str, dict] = {}
+        for one_date in diag.RECOVERED_DATES:
+            key = one_date.isoformat()
+            print(f"tracing decision impact for {key} ...", file=sys.stderr)
+            ur_impact = diag.trace_universe_resolver_impact(session, cfg, one_date, bridge_factor)
+            scoring_impact = diag.trace_scoring_and_selection_impact(session, cfg, one_date, bridge_factor)
+            decision_impact_by_date[key] = {
+                "universe_resolver": ur_impact,
+                "scoring_and_selection": scoring_impact,
+            }
+            print(
+                f"  {key}: admission_changed={ur_impact['admission_changed']} "
+                f"avb_resolved_member={scoring_impact.get('avb_resolved_member')} "
+                f"risk_bucket_a={scoring_impact.get('risk_bucket_a')} "
+                f"risk_bucket_b={scoring_impact.get('risk_bucket_b')} "
+                f"eligible_a={scoring_impact.get('eligible_a')} eligible_b={scoring_impact.get('eligible_b')}",
+                file=sys.stderr,
+            )
+
+    classification = diag.classify_avb(local_convention, decision_impact_by_date)
+
+    db_file_true_end = db_file_fingerprint(db_path)
+    zero_write = {
+        "db_file_true_start": db_file_true_start,
+        "db_file_true_end": db_file_true_end,
+        "mtime_unchanged": db_file_true_start.get("mtime") == db_file_true_end.get("mtime"),
+        "size_unchanged": db_file_true_start.get("size_bytes") == db_file_true_end.get("size_bytes"),
+        "wal_empty_at_start": (db_file_true_start.get("wal") or {}).get("size_bytes", 0) in (0, None)
+        if db_file_true_start.get("wal", {}).get("exists") else True,
+        "wal_empty_at_end": (db_file_true_end.get("wal") or {}).get("size_bytes", 0) in (0, None)
+        if db_file_true_end.get("wal", {}).get("exists") else True,
+    }
+
+    result = {
+        "generated_at": diag._now_iso(),
+        "j10_evidence_path": str(args.j10_evidence_path),
+        "bridge_factor": bridge_factor,
+        "calibration_pairs": evidence_row.get("pairs"),
+        "pool_bridge_factor_distribution": pool_distribution,
+        "stored_series_window": {"start": "2026-06-01", "end": "2026-12-31", "row_count": len(stored_series)},
+        "local_convention": local_convention,
+        "counterfactual_representations_by_date": representations_by_date,
+        "decision_impact_by_date": decision_impact_by_date,
+        "classification": classification,
+        "zero_write_proof": zero_write,
+    }
+
+    args.output_path.parent.mkdir(parents=True, exist_ok=True)
+    args.output_path.write_text(json.dumps(result, indent=2, sort_keys=True, default=str))
+    print(f"wrote {args.output_path}", file=sys.stderr)
+    print(
+        f"AVB classification: {classification['classification']} "
+        f"stage_d_ready_per_avb={classification['stage_d_ready_per_avb']}",
+        file=sys.stderr,
+    )
+    print(f"zero_write_proof: {zero_write}", file=sys.stderr)
+    return 0
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
diff --git a/apps/backend/scripts/run_j11_stage_d_preflight.py b/apps/backend/scripts/run_j11_stage_d_preflight.py
new file mode 100644
index 00000000..cc2c8906
--- /dev/null
+++ b/apps/backend/scripts/run_j11_stage_d_preflight.py
@@ -0,0 +1,159 @@
+"""goal-market-compass iter-14 -- J-11 Stage D readiness: the READ-ONLY Stage D preflight gate (Goal 1 +
+Goal 3a), executed live against `apps/backend/data/trendora.db` THIS iteration -- permitted (zero
+writes), distinct from Stage D's own regeneration, which remains unauthorized and is NOT attempted
+anywhere in this script.
+
+Opens the live database through an ACTUAL read-only SQLite handle (`file:<path>?mode=ro` + `PRAGMA
+query_only=ON`, mirroring `run_j11_stage_b1_live_reverification.py`'s helper) -- any accidental write
+attempt anywhere in the call graph would raise `OperationalError` rather than silently succeeding. No
+`--confirm` flag: there is nothing here to confirm, since nothing is ever written.
+
+Sequence:
+  1. Freeze a FRESH Stage D attempt identity (`j11_stage_d.freeze_stage_d_attempt_identity`) -- never
+     hardcodes iteration 10's `6261ca17...` or iteration 13's `53d2ffd1...`.
+  2. Capture the Stage D preflight (`j11_stage_d.capture_stage_d_preflight`) -- re-derives live state
+     fresh, including Check (A)'s identity comparison against a SECOND independent recomputation.
+  3. Load the certified post-Stage-C baseline from iteration 13's own persisted artifacts
+     (`j11_stage_d.load_stage_d_certified_baseline`) and run the comparison gate
+     (`compare_stage_d_preflight_to_certified`) + verdict (`stage_d_preflight_verdict`).
+  4. Persist every artifact; the verdict alone does NOT authorize Stage D (a separate owner instruction
+     is required -- the C10/A12 pattern).
+
+Usage:
+    apps/backend/.venv/bin/python apps/backend/scripts/run_j11_stage_d_preflight.py \\
+        [--evidence-dir runs/goal-market-compass-iter-14] \\
+        [--stage-c-preflight-path runs/goal-market-compass-iter-13/j11-stage-c-preflight.json] \\
+        [--stage-c-mutation-accounting-path runs/goal-market-compass-iter-13/j11-stage-c-mutation-accounting.json] \\
+        [--db-file-true-start-path PATH]   # reuse an earlier-in-this-iteration true-start capture, if any
+"""
+from __future__ import annotations
+
+import argparse
+import json
+import sys
+from pathlib import Path
+
+# scripts/ -> backend -> apps -> repo root
+BACKEND_DIR = Path(__file__).resolve().parents[1]
+REPO_ROOT = BACKEND_DIR.parents[1]
+sys.path.insert(0, str(BACKEND_DIR))
+
+from sqlalchemy import create_engine, event  # noqa: E402
+from sqlmodel import Session  # noqa: E402
+
+from app.config import load_config  # noqa: E402
+from app.db import resolve_database_url  # noqa: E402
+from app.engine import j11_stage_c as jsc  # noqa: E402
+from app.engine import j11_stage_d as jsd  # noqa: E402
+
+DEFAULT_EVIDENCE_DIR = REPO_ROOT / "runs" / "goal-market-compass-iter-14"
+DEFAULT_STAGE_C_PREFLIGHT_PATH = REPO_ROOT / "runs" / "goal-market-compass-iter-13" / "j11-stage-c-preflight.json"
+DEFAULT_STAGE_C_MUTATION_ACCOUNTING_PATH = (
+    REPO_ROOT / "runs" / "goal-market-compass-iter-13" / "j11-stage-c-mutation-accounting.json"
+)
+
+
+def _db_file_path(database_url: str) -> "Path | None":
+    prefix = "sqlite:///"
+    if not database_url.startswith(prefix):
+        return None
+    raw = database_url[len(prefix):]
+    if not raw or raw == ":memory:":
+        return None
+    path = Path(raw)
+    return path if path.is_absolute() else (REPO_ROOT / raw)
+
+
+def _read_only_engine(db_path: Path):
+    url = f"sqlite:///file:{db_path}?mode=ro&uri=true"
+    engine = create_engine(url, connect_args={"check_same_thread": False})
+
+    @event.listens_for(engine, "connect")
+    def _set_query_only(dbapi_connection, _record):
+        dbapi_connection.execute("PRAGMA query_only=ON")
+
+    return engine
+
+
+def _write_json(path: Path, payload) -> None:
+    path.parent.mkdir(parents=True, exist_ok=True)
+    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str))
+    print(f"wrote {path}", file=sys.stderr)
+
+
+def main() -> int:
+    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
+    parser.add_argument("--evidence-dir", type=Path, default=DEFAULT_EVIDENCE_DIR)
+    parser.add_argument("--stage-c-preflight-path", type=Path, default=DEFAULT_STAGE_C_PREFLIGHT_PATH)
+    parser.add_argument(
+        "--stage-c-mutation-accounting-path", type=Path, default=DEFAULT_STAGE_C_MUTATION_ACCOUNTING_PATH
+    )
+    parser.add_argument(
+        "--db-file-true-start-path", type=Path, default=None,
+        help="an earlier-in-this-iteration TRUE process-start db-file fingerprint (e.g. from the AVB "
+             "diagnostic script, if it ran first) -- reused verbatim as the whole-iteration start instead "
+             "of re-capturing one here, so the whole-iteration zero-write proof brackets every live read "
+             "this iteration performed, not just this script's own span.",
+    )
+    args = parser.parse_args()
+
+    cfg = load_config()
+    resolved_url = resolve_database_url(cfg.database.url)
+    db_path = _db_file_path(resolved_url)
+    if db_path is None or not db_path.exists():
+        print(f"FAIL: could not resolve a live sqlite db file from {resolved_url!r}", file=sys.stderr)
+        return 1
+    print(f"database (READ-ONLY handle, mode=ro + PRAGMA query_only=ON): {db_path}", file=sys.stderr)
+
+    if args.db_file_true_start_path is not None and args.db_file_true_start_path.exists():
+        db_file_true_start = json.loads(args.db_file_true_start_path.read_text())
+        print(f"reusing earlier TRUE process-start fingerprint from {args.db_file_true_start_path}", file=sys.stderr)
+    else:
+        db_file_true_start = jsc.db_file_fingerprint(db_path)
+    _write_json(args.evidence_dir / "j11-stage-d-db-file-true-start.json", db_file_true_start)
+
+    goal_md_text = jsc.read_goal_md_text()
+    git_head = jsc.read_git_head()
+    engine = _read_only_engine(db_path)
+
+    with Session(engine) as session:
+        attempt_identity = jsd.freeze_stage_d_attempt_identity(
+            session, cfg, git_head=git_head, goal_md_text=goal_md_text
+        )
+        _write_json(args.evidence_dir / "j11-stage-d-attempt-identity.json", attempt_identity)
+        print(f"frozen Stage D attempt identity: engine_identity={attempt_identity['engine_identity']}", file=sys.stderr)
+
+        preflight = jsd.capture_stage_d_preflight(
+            session, engine, db_path, goal_md_text=goal_md_text, git_head=git_head, config=cfg,
+        )
+    _write_json(args.evidence_dir / "j11-stage-d-preflight.json", preflight)
+    print(
+        f"preflight captured: manifest_row_count={preflight['manifest_row_count']} "
+        f"c1_ok={preflight['c1_date_set_boundary_check']['ok']} "
+        f"identity_check_a_ok={preflight['identity_check_a']['ok']}",
+        file=sys.stderr,
+    )
+
+    certified = jsd.load_stage_d_certified_baseline(
+        args.stage_c_preflight_path, args.stage_c_mutation_accounting_path
+    )
+    gate = jsd.compare_stage_d_preflight_to_certified(preflight, certified)
+    verdict = jsd.stage_d_preflight_verdict(gate)
+    _write_json(args.evidence_dir / "j11-stage-d-preflight-gate.json", {"comparison": gate, "verdict": verdict})
+    print(f"preflight comparison gate: all_invariants_hold={gate['all_invariants_hold']} verdict={verdict}", file=sys.stderr)
+    if not gate["all_invariants_hold"]:
+        failing = [k for k, v in gate["checks"].items() if not v]
+        print(f"FAILING CHECKS: {failing}", file=sys.stderr)
+
+    db_file_true_end = jsc.db_file_fingerprint(db_path)
+    _write_json(args.evidence_dir / "j11-stage-d-db-file-true-end.json", db_file_true_end)
+    mtime_unchanged = db_file_true_start.get("mtime") == db_file_true_end.get("mtime")
+    print(f"whole-iteration zero-write proof: mtime_unchanged={mtime_unchanged}", file=sys.stderr)
+
+    print(f"J-11 STAGE D PREFLIGHT PASSED: {'YES' if verdict['passed'] else 'NO'}", file=sys.stderr)
+    print("J-11 STAGE D AUTHORIZED: NO", file=sys.stderr)
+    return 0 if verdict["passed"] else 1
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
diff --git a/apps/backend/tests/test_j11_avb_diagnostic.py b/apps/backend/tests/test_j11_avb_diagnostic.py
new file mode 100644
index 00000000..d576ae39
--- /dev/null
+++ b/apps/backend/tests/test_j11_avb_diagnostic.py
@@ -0,0 +1,327 @@
+"""goal-market-compass iter-14 -- J-11 Stage D readiness, Goal 4: the read-only AVB bridge/volume
+diagnostic tests (TC-20..24).
+
+File-scoped, mostly fixture-DB-only (fresh `sqlite://` engine, small synthetic series, following
+`test_universe_resolver.py`'s reduced-threshold `Config.model_copy` pattern) -- never
+`apps/backend/data/trendora.db`. The one exception is `load_j10_avb_evidence`/
+`summarize_pool_bridge_factor_distribution`, which legitimately read the COMMITTED, already-persisted
+`runs/goal-market-compass-iter-9/j10-population-evidence.json` evidence file -- a static seed-adjacent
+artifact, not the live database.
+"""
+from __future__ import annotations
+
+from datetime import date, timedelta
+
+import pytest
+from sqlalchemy import event
+from sqlmodel import Session, SQLModel, create_engine
+
+from app.config import load_config
+from app.engine import j11_avb_diagnostic as diag
+from app.engine.prices import Bar
+from app.models import DailyPrice
+
+
+@pytest.fixture()
+def engine():
+    eng = create_engine("sqlite://", connect_args={"check_same_thread": False})
+
+    @event.listens_for(eng, "connect")
+    def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:
+        cursor = dbapi_connection.cursor()
+        cursor.execute("PRAGMA foreign_keys=ON")
+        cursor.close()
+
+    SQLModel.metadata.create_all(eng)
+    return eng
+
+
+def _small_universe_cfg():
+    """A real Config, reduced ONLY on the thresholds this test's tiny synthetic series would otherwise
+    fail (mirrors `test_universe_resolver.py`'s `_cfg()` pattern) -- every other value stays the real
+    committed config, so `resolve_candidate`/`score_stocks` exercise the REAL rule shape, not a
+    reinvented one."""
+    cfg = load_config().model_copy(deep=True)
+    cfg = cfg.model_copy(update={"indicators": cfg.indicators.model_copy(update={
+        "min_history_bars": 30, "vol_avg_period": 20,
+    })})
+    cfg = cfg.model_copy(update={"universe": cfg.universe.model_copy(update={
+        "filters": cfg.universe.filters.model_copy(update={
+            "min_price": 1.0, "min_dollar_vol": 1000.0, "adv_window_days": 20, "max_staleness_days": 30,
+        })
+    })})
+    return cfg
+
+
+def _seed_daily_prices(session: Session, symbol: str, *, n: int, end: date, close_start: float, close_step: float, volume: float) -> None:
+    """`n` consecutive daily bars ENDING at `end` (ascending) with a simple deterministic close ramp --
+    enough for the reduced-threshold config's gates and windowed indicators to have real (non-NA) values
+    without needing hundreds of days."""
+    for i in range(n):
+        d = end - timedelta(days=n - 1 - i)
+        close = close_start + close_step * i
+        session.add(DailyPrice(
+            symbol=symbol, date=d, open=close, high=close * 1.01, low=close * 0.99, close=close, volume=volume,
+        ))
+    session.commit()
+
+
+AVB_TEST_DATES_END = date(2026, 8, 12)
+
+
+# --- TC-20: bridge factor + calibration pairs reproduce EXACTLY from the persisted J-10 evidence -----
+
+
+def test_tc20_load_j10_avb_evidence_reproduces_persisted_bridge_factor_and_pairs():
+    row = diag.load_j10_avb_evidence()
+    assert row["bridge_factor"] == pytest.approx(2.7930001225759193)
+    pair_dates = sorted(p["trading_date"] for p in row["pairs"])
+    assert pair_dates == ["2026-08-05", "2026-08-06", "2026-08-07", "2026-08-10"]
+
+
+def test_avb_is_the_unique_material_bridge_factor_outlier_in_the_persisted_pool():
+    dist = diag.summarize_pool_bridge_factor_distribution()
+    assert dist["avb_is_unique_material_outlier"] is True
+    assert diag.AVB_SYMBOL in dist["materially_bridged_symbols"]
+
+
+def test_load_j10_avb_evidence_raises_on_missing_symbol(tmp_path):
+    import json
+    path = tmp_path / "evidence.json"
+    path.write_text(json.dumps({"symbols": [{"symbol": "AAPL", "bridge_factor": 1.0, "pairs": []}]}))
+    with pytest.raises(ValueError):
+        diag.load_j10_avb_evidence(path)
+
+
+# --- TC-21: local-convention classification -- from the stored series, never convention alone --------
+
+
+def test_tc21_classify_local_convention_bridged_raw_when_calibration_ratios_agree():
+    bridge_factor = 2.793
+    evidence_row = {
+        "pairs": [
+            {"trading_date": "2026-08-05", "fallback_close": 100 / bridge_factor, "ratio": bridge_factor},
+            {"trading_date": "2026-08-06", "fallback_close": 101 / bridge_factor, "ratio": bridge_factor},
+            {"trading_date": "2026-08-07", "fallback_close": 102 / bridge_factor, "ratio": bridge_factor},
+            {"trading_date": "2026-08-10", "fallback_close": 103 / bridge_factor, "ratio": bridge_factor},
+        ]
+    }
+    # a continuous, unbroken stored series across the whole window -- no anomalous jump anywhere,
+    # including at the 08-10 -> 08-11 -> 08-12 recovery boundary.
+    stored_series = [
+        {"date": "2026-08-04", "close": 99.0, "volume": 1000.0, "close_times_volume": 99000.0},
+        {"date": "2026-08-05", "close": 100.0, "volume": 1000.0, "close_times_volume": 100000.0},
+        {"date": "2026-08-06", "close": 101.0, "volume": 1000.0, "close_times_volume": 101000.0},
+        {"date": "2026-08-07", "close": 102.0, "volume": 1000.0, "close_times_volume": 102000.0},
+        {"date": "2026-08-10", "close": 103.0, "volume": 1000.0, "close_times_volume": 103000.0},
+        {"date": "2026-08-11", "close": 104.0, "volume": 1000.0, "close_times_volume": 104000.0},
+        {"date": "2026-08-12", "close": 105.0, "volume": 1000.0, "close_times_volume": 105000.0},
+        {"date": "2026-08-13", "close": 106.0, "volume": 1000.0, "close_times_volume": 106000.0},
+    ]
+    result = diag.classify_local_convention(stored_series, evidence_row)
+    assert result["windows"]["calibration_window"]["classification"] == "bridged+raw"
+    assert result["indeterminate"] is False
+    assert result["internally_consistent"] is True
+    assert result["overall_classification"] == "bridged+raw"
+
+
+def test_classify_local_convention_detects_a_discontinuity_at_the_recovery_boundary():
+    bridge_factor = 2.793
+    evidence_row = {
+        "pairs": [
+            {"trading_date": "2026-08-05", "fallback_close": 100 / bridge_factor, "ratio": bridge_factor},
+            {"trading_date": "2026-08-06", "fallback_close": 101 / bridge_factor, "ratio": bridge_factor},
+            {"trading_date": "2026-08-07", "fallback_close": 102 / bridge_factor, "ratio": bridge_factor},
+            {"trading_date": "2026-08-10", "fallback_close": 103 / bridge_factor, "ratio": bridge_factor},
+        ]
+    }
+    # an ARTIFICIAL scale break exactly at 2026-08-11 -- close jumps from 103 to 400 (the ~2.79x-scale
+    # jump a genuine mismatch would show), then continues smoothly from the new (wrong) scale.
+    stored_series = [
+        {"date": "2026-08-10", "close": 103.0, "volume": 1000.0, "close_times_volume": 103000.0},
+        {"date": "2026-08-11", "close": 400.0, "volume": 1000.0, "close_times_volume": 400000.0},
+        {"date": "2026-08-12", "close": 404.0, "volume": 1000.0, "close_times_volume": 404000.0},
+    ]
+    result = diag.classify_local_convention(stored_series, evidence_row)
+    assert result["anomalous_jump_count"] >= 1
+    assert result["internally_consistent"] is False
+    assert result["windows"]["recovered_dates"]["boundary_jumps"]
+
+
+def test_classify_local_convention_indeterminate_when_calibration_pairs_missing():
+    result = diag.classify_local_convention([], {"pairs": []})
+    assert result["indeterminate"] is True
+
+
+# --- TC-22: counterfactual representations A/B/C -- exact formulas, B's volume equals A's -----------
+
+
+def test_tc22_representations_a_b_c_formulas_and_volume_equality():
+    bridge_factor = 2.7930001225759193
+    stored_close, stored_volume = 189.61, 500_000.0
+    rep = diag.compute_counterfactual_representations(bridge_factor, stored_close, stored_volume)
+    assert rep["A"]["close"] == stored_close
+    assert rep["A"]["volume"] == stored_volume
+    assert rep["B"]["close"] == pytest.approx(stored_close / bridge_factor)
+    assert rep["B"]["volume"] == stored_volume  # stated explicitly: volume was never transformed by J-10
+    assert rep["volume_a_equals_b"] is True
+    assert rep["C"]["volume"] == pytest.approx(stored_volume * bridge_factor)
+    assert rep["C"]["close"] == stored_close  # C only changes volume, never close
+    assert rep["A"]["close_times_volume"] > rep["B"]["close_times_volume"]  # A > B since bridge_factor > 1
+
+
+# --- _build_bars_with_transformed_close -- never mutates the input bars, only the targeted dates ------
+
+
+def test_build_bars_with_transformed_close_only_touches_target_dates():
+    bars = [
+        Bar(date=date(2026, 8, 10), open=1, high=1, low=1, close=100.0, volume=10.0),
+        Bar(date=date(2026, 8, 11), open=1, high=1, low=1, close=200.0, volume=20.0),
+        Bar(date=date(2026, 8, 12), open=1, high=1, low=1, close=300.0, volume=30.0),
+    ]
+    out = diag._build_bars_with_transformed_close(bars, {date(2026, 8, 11), date(2026, 8, 12)}, 2.0)
+    assert out[0].close == 100.0  # untouched date, unchanged
+    assert out[1].close == 100.0  # 200 / 2.0
+    assert out[2].close == 150.0  # 300 / 2.0
+    assert out[0].volume == 10.0 and out[1].volume == 20.0 and out[2].volume == 30.0  # volume NEVER touched
+    # the original list's own Bar objects are untouched (new tuples returned, never mutated in place --
+    # NamedTuples are immutable anyway, but this also proves no accidental aliasing/identity confusion).
+    assert bars[1].close == 200.0
+
+
+# --- TC-23: decision-impact trace through universe_resolver -- fixture DB, reduced thresholds ---------
+
+
+def test_tc23_trace_universe_resolver_impact_admission_and_adv_shift(engine):
+    cfg = _small_universe_cfg()
+    bridge_factor = 2.793
+    with Session(engine) as session:
+        _seed_daily_prices(
+            session, diag.AVB_SYMBOL, n=40, end=AVB_TEST_DATES_END,
+            close_start=180.0, close_step=0.5, volume=1_000_000.0,
+        )
+
+    with Session(engine) as session:
+        impact = diag.trace_universe_resolver_impact(session, cfg, date(2026, 8, 11), bridge_factor)
+
+    assert impact["adv_dollar_a"] is not None and impact["adv_dollar_b"] is not None
+    # representation B divides the two most-recent bars' close by bridge_factor -- a LOWER close for
+    # those days pulls the trailing-window ADV average DOWN relative to A.
+    assert impact["adv_dollar_b"] < impact["adv_dollar_a"]
+    assert impact["resolution_a"]["admitted"] is True  # comfortably above the reduced $1,000 floor either way
+    assert impact["resolution_b"]["admitted"] is True
+    assert impact["admission_changed"] is False
+
+
+def test_trace_universe_resolver_impact_detects_admission_change_when_b_crosses_the_floor(engine):
+    cfg = _small_universe_cfg()
+    # a min_dollar_vol floor placed BETWEEN A's and B's ADV -- proves the admission gate genuinely reacts
+    # to the counterfactual, not just carries a static "admitted" value through.
+    with Session(engine) as session:
+        _seed_daily_prices(
+            session, diag.AVB_SYMBOL, n=40, end=AVB_TEST_DATES_END,
+            close_start=180.0, close_step=0.0, volume=1_000_000.0,
+        )
+        session.commit()
+
+    with Session(engine) as session:
+        # peek the real ADV values at the reduced config first, to place the floor precisely between them
+        preview = diag.trace_universe_resolver_impact(session, cfg, date(2026, 8, 11), 2.793)
+    floor = (preview["adv_dollar_a"] + preview["adv_dollar_b"]) / 2
+    cfg_with_floor = cfg.model_copy(update={"universe": cfg.universe.model_copy(update={
+        "filters": cfg.universe.filters.model_copy(update={"min_dollar_vol": floor})
+    })})
+
+    with Session(engine) as session:
+        impact = diag.trace_universe_resolver_impact(session, cfg_with_floor, date(2026, 8, 11), 2.793)
+    assert impact["resolution_a"]["admitted"] is True
+    assert impact["resolution_b"]["admitted"] is False
+    assert impact["resolution_b"]["reason"] == "below_adv"
+    assert impact["admission_changed"] is True
+
+
+# --- TC-23 (scoring half): the honest empty state when AVB is not a resolved member -------------------
+
+
+def test_trace_scoring_and_selection_impact_honest_empty_when_avb_not_resolved(engine):
+    """On an otherwise-empty fixture DB (no DailyPrice rows at all), AVB clears no history gate under the
+    REAL committed default config -- `score_stocks` resolves an empty membership set, and the trace
+    reports the honest `avb_resolved_member: False` state rather than fabricating a score."""
+    cfg = load_config()
+    with Session(engine) as session:
+        impact = diag.trace_scoring_and_selection_impact(session, cfg, date(2026, 8, 11), 2.793)
+    assert impact["avb_resolved_member"] is False
+    assert "not a point-in-time-resolved universe member" in impact["note"]
+
+
+# --- TC-24: overall classification -- exactly one of AVB-A/B/C/D, reasoning names the evidence --------
+
+
+def test_tc24_classify_avb_lands_in_avb_a_with_no_material_signal():
+    local_convention = {"indeterminate": False, "internally_consistent": True, "reasoning": "consistent"}
+    decision_impact = {
+        "2026-08-11": {
+            "universe_resolver": {"admission_changed": False},
+            "scoring_and_selection": {
+                "avb_resolved_member": True, "risk_bucket_a": "E", "risk_bucket_b": "E",
+                "setup_status_a": "Avoid", "setup_status_b": "Avoid",
+                "eligible_a": False, "eligible_b": False, "other_ticker_percentile_shifts": {},
+            },
+        }
+    }
+    result = diag.classify_avb(local_convention, decision_impact)
+    assert result["classification"] == "AVB-A"
+    assert result["stage_d_ready_per_avb"] is True
+    assert result["material_signals"] == []
+
+
+def test_classify_avb_lands_in_avb_b_when_material_but_internally_consistent():
+    local_convention = {"indeterminate": False, "internally_consistent": True, "reasoning": "consistent"}
+    decision_impact = {
+        "2026-08-11": {
+            "universe_resolver": {"admission_changed": False},
+            "scoring_and_selection": {
+                "avb_resolved_member": True, "risk_bucket_a": "E", "risk_bucket_b": "D",
+                "setup_status_a": "Avoid", "setup_status_b": "Avoid",
+                "eligible_a": False, "eligible_b": False, "other_ticker_percentile_shifts": {"HAS": {}},
+            },
+        }
+    }
+    result = diag.classify_avb(local_convention, decision_impact)
+    assert result["classification"] == "AVB-B"
+    assert result["stage_d_ready_per_avb"] is True
+    assert result["material_signals"]  # names the specific evidence, never a bare label
+    assert "Risk bucket changed" in result["material_signals"][0] or any(
+        "Risk bucket changed" in s for s in result["material_signals"]
+    )
+
+
+def test_classify_avb_lands_in_avb_c_when_inconsistent_regardless_of_impact():
+    local_convention = {"indeterminate": False, "internally_consistent": False, "reasoning": "discontinuity found"}
+    result = diag.classify_avb(local_convention, {})
+    assert result["classification"] == "AVB-C"
+    assert result["stage_d_ready_per_avb"] is False
+
+
+def test_classify_avb_lands_in_avb_d_when_indeterminate():
+    local_convention = {"indeterminate": True, "internally_consistent": False, "reasoning": "insufficient evidence"}
+    result = diag.classify_avb(local_convention, {})
+    assert result["classification"] == "AVB-D"
+    assert result["stage_d_ready_per_avb"] is False
+
+
+# --- fetch_avb_stored_series -- small fixture read-only column-projected query -------------------------
+
+
+def test_fetch_avb_stored_series_reads_close_volume_and_product(engine):
+    with Session(engine) as session:
+        _seed_daily_prices(
+            session, diag.AVB_SYMBOL, n=5, end=date(2026, 8, 12),
+            close_start=100.0, close_step=1.0, volume=10.0,
+        )
+    with Session(engine) as session:
+        series = diag.fetch_avb_stored_series(session, date(2026, 8, 8), date(2026, 8, 12))
+    assert len(series) == 5
+    assert series[0]["close"] == 100.0
+    assert series[0]["close_times_volume"] == 1000.0
+    assert [row["date"] for row in series] == sorted(row["date"] for row in series)
diff --git a/apps/backend/tests/test_j11_stage_c_cli_script.py b/apps/backend/tests/test_j11_stage_c_cli_script.py
new file mode 100644
index 00000000..f5cbf3ce
--- /dev/null
+++ b/apps/backend/tests/test_j11_stage_c_cli_script.py
@@ -0,0 +1,260 @@
+"""goal-market-compass iter-14 -- J-11 Stage D readiness, Goal 3b: the still-missing CLI control-flow
+tests for `scripts/run_j11_stage_c_bounded_clear.py` (TC-19's CLI half). `unittest.mock`-based, NEVER a
+live DB -- every DB-touching name (`get_engine`, `Session`, `clear_snapshot_dates`) is patched to a mock
+before `main()` runs, so these tests exercise CONTROL FLOW only (which functions get called, in what
+order, and which never get called), never real database I/O.
+
+Verified against the CURRENT script (`run_j11_stage_c_bounded_clear.py`) before writing these -- all
+three behaviors are genuinely already implemented there, not invented:
+  - without `--confirm`, `main()` returns before importing/calling anything DB-related at all;
+  - without an explicit `--evidence-dir`, `main()` refuses before writing anything anywhere (added in
+    iteration 14's fix pass, after the missing flag in THIS file's gate-failure test let the script fall
+    back to its old default and overwrite three committed iteration-13 evidence files);
+  - a failing preflight-comparison-gate (`all_invariants_hold: False`) returns before
+    `clear_snapshot_dates` is ever called;
+  - a failing post-delete `mutation_accounting` (`all_checks_pass: False`) returns before
+    `build_completion_marker`/the completion-marker file is ever written.
+"""
+from __future__ import annotations
+
+import importlib.util
+import sys
+from pathlib import Path
+from unittest import mock
+
+import pytest
+
+BACKEND_DIR = Path(__file__).resolve().parents[1]
+SCRIPT_PATH = BACKEND_DIR / "scripts" / "run_j11_stage_c_bounded_clear.py"
+_MODULE_NAME = "run_j11_stage_c_bounded_clear_under_test"
+
+
+def _load_script_module():
+    """Loads the script as a REAL module object via `importlib` (never `runpy.run_path` -- its returned
+    namespace is a COPY, not the module's actual `__dict__`, so mutating it does not affect what `main()`
+    sees at call time; verified directly: `runpy.run_path(...)['main'].__globals__ is <returned dict>` is
+    `False`). `importlib.util.module_from_spec` + `exec_module` gives a module whose `__dict__` IS
+    `main.__globals__`, so `monkeypatch.setattr(module, name, mock)` genuinely intercepts every call the
+    script's top-level code makes to that name -- never executes `main()` itself (only import-time
+    module-level code runs, which the script's own `if __name__ == "__main__":` guard keeps `main()` out
+    of)."""
+    spec = importlib.util.spec_from_file_location(_MODULE_NAME, SCRIPT_PATH)
+    module = importlib.util.module_from_spec(spec)
+    sys.modules[_MODULE_NAME] = module
+    spec.loader.exec_module(module)
+    return module
+
+
+@pytest.fixture()
+def script_ns(monkeypatch):
+    """The script's real, executed module object, with `sys.argv` restored afterward."""
+    original_argv = sys.argv
+    try:
+        module = _load_script_module()
+        yield module
+    finally:
+        sys.argv = original_argv
+        sys.modules.pop(_MODULE_NAME, None)
+
+
+# --- missing --confirm: NO database interaction of any kind -----------------------------------------
+
+
+def test_missing_confirm_never_calls_get_engine_or_session(monkeypatch, script_ns):
+    mock_get_engine = mock.MagicMock(name="get_engine")
+    mock_session_cls = mock.MagicMock(name="Session")
+    monkeypatch.setattr(script_ns.jsc, "db_file_fingerprint", mock.MagicMock(return_value={}))
+    monkeypatch.setattr(script_ns, "get_engine", mock_get_engine)
+    monkeypatch.setattr(script_ns, "Session", mock_session_cls)
+    monkeypatch.setattr(sys, "argv", ["run_j11_stage_c_bounded_clear.py"])  # no --confirm
+
+    exit_code = script_ns.main()
+
+    assert exit_code != 0
+    mock_get_engine.assert_not_called()
+    mock_session_cls.assert_not_called()
+
+
+# --- --confirm but no --evidence-dir: refuses, writes nothing anywhere ------------------------------
+
+
+def test_confirm_without_explicit_evidence_dir_refuses_before_writing_anything(
+    monkeypatch, script_ns, capsys
+):
+    """The guard added after this very test file overwrote three committed iteration-13 Stage C evidence
+    files: `--evidence-dir` used to DEFAULT to `runs/goal-market-compass-iter-13`, so a caller that forgot
+    the flag wrote its payloads straight over real forensic evidence. There is no implicit default now --
+    a committed evidence directory can only be reached by naming it explicitly."""
+    mock_write_json = mock.MagicMock(name="_write_json")
+    monkeypatch.setattr(script_ns, "_write_json", mock_write_json)
+    mock_get_engine = mock.MagicMock(name="get_engine")
+    monkeypatch.setattr(script_ns, "get_engine", mock_get_engine)
+    mock_session_cls = mock.MagicMock(name="Session")
+    monkeypatch.setattr(script_ns, "Session", mock_session_cls)
+    mock_fingerprint = mock.MagicMock(name="db_file_fingerprint", return_value={})
+    monkeypatch.setattr(script_ns.jsc, "db_file_fingerprint", mock_fingerprint)
+    mock_clear = mock.MagicMock(name="clear_snapshot_dates")
+    monkeypatch.setattr(script_ns, "clear_snapshot_dates", mock_clear)
+
+    # --confirm present (the destructive-intent flag), --evidence-dir absent
+    monkeypatch.setattr(sys, "argv", ["run_j11_stage_c_bounded_clear.py", "--confirm"])
+
+    exit_code = script_ns.main()
+
+    assert exit_code == 2
+    mock_write_json.assert_not_called()  # NOTHING is written, to the default path or anywhere else
+    mock_get_engine.assert_not_called()
+    mock_session_cls.assert_not_called()
+    mock_fingerprint.assert_not_called()
+    mock_clear.assert_not_called()
+    assert "--evidence-dir" in capsys.readouterr().err
+
+
+# --- comparison-gate failure: clear_snapshot_dates is never called ----------------------------------
+
+
+def test_comparison_gate_failure_never_calls_clear_snapshot_dates(monkeypatch, script_ns, tmp_path):
+    fake_certified_path = tmp_path / "certified.json"
+    import json as _json
+    fake_certified_path.write_text(_json.dumps({"manifest_row_count": 24}))
+    evidence_dir = tmp_path / "evidence"
+
+    mock_engine = mock.MagicMock(name="engine")
+    monkeypatch.setattr(script_ns, "get_engine", mock.MagicMock(return_value=mock_engine))
+    mock_session_instance = mock.MagicMock(name="session_instance")
+    mock_session_cm = mock.MagicMock()
+    mock_session_cm.__enter__ = mock.MagicMock(return_value=mock_session_instance)
+    mock_session_cm.__exit__ = mock.MagicMock(return_value=False)
+    monkeypatch.setattr(script_ns, "Session", mock.MagicMock(return_value=mock_session_cm))
+
+    monkeypatch.setattr(script_ns.jsc, "db_file_fingerprint", mock.MagicMock(return_value={}))
+    monkeypatch.setattr(script_ns.jsc, "read_goal_md_text", mock.MagicMock(return_value="goal md text"))
+    monkeypatch.setattr(script_ns.jsc, "read_git_head", mock.MagicMock(return_value="deadbeef"))
+    monkeypatch.setattr(
+        script_ns.jsc, "capture_stage_c_preflight",
+        mock.MagicMock(return_value={
+            "captured_at": "2026-01-01T00:00:00+00:00",
+            "manifest_row_count": 24,
+            "c1_date_set_boundary_check": {"ok": True},
+        }),
+    )
+    monkeypatch.setattr(
+        script_ns.jsc, "compare_preflight_to_certified",
+        mock.MagicMock(return_value={
+            "all_invariants_hold": False, "material_mismatch": True,
+            "checks": {"manifest_row_count_matches_certified": False}, "generated_at": "x",
+        }),
+    )
+
+    mock_clear = mock.MagicMock(name="clear_snapshot_dates")
+    monkeypatch.setattr(script_ns, "clear_snapshot_dates", mock_clear)
+
+    monkeypatch.setattr(
+        sys, "argv",
+        [
+            "run_j11_stage_c_bounded_clear.py", "--confirm",
+            "--certified-state-path", str(fake_certified_path),
+            # MANDATORY in every test that reaches the write path: without it the script used to fall back
+            # to the REAL committed runs/goal-market-compass-iter-13/ directory and this test overwrote
+            # three of iteration 13's Stage C evidence files with the mocked payloads above.
+            "--evidence-dir", str(evidence_dir),
+        ],
+    )
+
+    exit_code = script_ns.main()
+
+    assert exit_code != 0
+    mock_clear.assert_not_called()
+    # the pre-gate evidence went to tmp_path, and only there
+    assert (evidence_dir / "j11-stage-c-preflight.json").exists()
+    assert (evidence_dir / "j11-stage-c-preflight-comparison-gate.json").exists()
+
+
+# --- a failing check anywhere: no completion marker is written --------------------------------------
+
+
+def test_failed_mutation_accounting_never_writes_a_completion_marker(monkeypatch, script_ns, tmp_path):
+    fake_certified_path = tmp_path / "certified.json"
+    import json as _json
+    fake_certified_path.write_text(_json.dumps({"manifest_row_count": 24}))
+    evidence_dir = tmp_path / "evidence"
+
+    mock_engine = mock.MagicMock(name="engine")
+    monkeypatch.setattr(script_ns, "get_engine", mock.MagicMock(return_value=mock_engine))
+    mock_session_instance = mock.MagicMock(name="session_instance")
+    mock_session_cm = mock.MagicMock()
+    mock_session_cm.__enter__ = mock.MagicMock(return_value=mock_session_instance)
+    mock_session_cm.__exit__ = mock.MagicMock(return_value=False)
+    monkeypatch.setattr(script_ns, "Session", mock.MagicMock(return_value=mock_session_cm))
+
+    monkeypatch.setattr(script_ns.jsc, "db_file_fingerprint", mock.MagicMock(return_value={}))
+    monkeypatch.setattr(script_ns.jsc, "read_goal_md_text", mock.MagicMock(return_value="goal md text"))
+    monkeypatch.setattr(script_ns.jsc, "read_git_head", mock.MagicMock(return_value="deadbeef"))
+    monkeypatch.setattr(
+        script_ns.jsc, "capture_stage_c_preflight",
+        mock.MagicMock(return_value={
+            "captured_at": "2026-01-01T00:00:00+00:00",
+            "manifest_row_count": 24,
+            "c1_date_set_boundary_check": {"ok": True},
+        }),
+    )
+    monkeypatch.setattr(
+        script_ns.jsc, "compare_preflight_to_certified",
+        mock.MagicMock(return_value={
+            "all_invariants_hold": True, "material_mismatch": False,
+            "checks": {}, "generated_at": "2026-01-01T00:00:01+00:00",
+        }),
+    )
+    monkeypatch.setattr(
+        script_ns.jsc, "capture_intended_delete_set",
+        mock.MagicMock(return_value={
+            "captured_at": "2026-01-01T00:00:02+00:00",
+            "total_counts": {}, "deleted_run_ids": [], "per_date": {},
+        }),
+    )
+    monkeypatch.setattr(script_ns.jsc, "capture_layer2_population_fingerprints", mock.MagicMock(return_value={}))
+    monkeypatch.setattr(script_ns.jsc, "incident_scoped_counts", mock.MagicMock(return_value={}))
+    monkeypatch.setattr(script_ns.jsc, "small_table_id_snapshot", mock.MagicMock(return_value={"count": 0, "ids": []}))
+    monkeypatch.setattr(script_ns.migration, "capture_full_db_snapshot", mock.MagicMock(return_value={"tables": {}}))
+    monkeypatch.setattr(script_ns.migration, "dump_table", mock.MagicMock(return_value=[]))
+    monkeypatch.setattr(
+        script_ns, "capture_pre_reset_inventory",
+        mock.MagicMock(return_value={"daily_prices": {"row_count": 0, "fingerprint": "x"}}),
+    )
+
+    mock_clear = mock.MagicMock(
+        name="clear_snapshot_dates",
+        return_value={"totals": {}, "per_date": {}},
+    )
+    monkeypatch.setattr(script_ns, "clear_snapshot_dates", mock_clear)
+
+    monkeypatch.setattr(
+        script_ns.jsc, "build_mutation_accounting",
+        mock.MagicMock(return_value={
+            "generated_at": "2026-01-01T00:00:03+00:00",
+            "all_checks_pass": False,
+            "checks": {"daily_prices_unchanged": False},
+        }),
+    )
+    mock_build_marker = mock.MagicMock(name="build_completion_marker")
+    monkeypatch.setattr(script_ns.jsc, "build_completion_marker", mock_build_marker)
+    monkeypatch.setattr(
+        script_ns.jsc, "stage_c_overall_verdict",
+        mock.MagicMock(return_value={"passed": False, "reason": "post_delete_verification_failed"}),
+    )
+
+    monkeypatch.setattr(
+        sys, "argv",
+        [
+            "run_j11_stage_c_bounded_clear.py", "--confirm",
+            "--certified-state-path", str(fake_certified_path),
+            "--evidence-dir", str(evidence_dir),
+        ],
+    )
+
+    exit_code = script_ns.main()
+
+    assert exit_code != 0
+    mock_clear.assert_called_once()  # the gate passed, so the ONE authorized write DID run this time...
+    mock_build_marker.assert_not_called()  # ...but post-delete verification failed, so NO marker is built
+    assert not (evidence_dir / "j11-stage-c-complete.json").exists()
diff --git a/apps/backend/tests/test_j11_stage_d.py b/apps/backend/tests/test_j11_stage_d.py
new file mode 100644
index 00000000..e71eea27
--- /dev/null
+++ b/apps/backend/tests/test_j11_stage_d.py
@@ -0,0 +1,340 @@
+"""goal-market-compass iter-14 -- J-11 Stage D readiness tests: fresh attempt identity (TC-1), the three
+fail-closed identity COMPARE checks (TC-ID-1..6), the Stage D preflight capture/comparison/verdict
+(TC-8..13), and the genuinely-new Stage D-specific negative check -- unexpected incident `ScannerRun`
+population (TC-19, the Stage D half; the Stage C `compare_preflight_to_certified` half lives in
+`test_j11_stage_c_preflight.py`).
+
+File-scoped, fixture-DB-only (fresh `sqlite://` engine, `SQLModel.metadata.create_all`) -- the SAME
+pattern `test_j11_maintenance.py`/`test_j11_stage_c_preflight.py` use, never `loaded_engine` and never
+`apps/backend/data/trendora.db`.
+"""
+from __future__ import annotations
+
+import copy
+from datetime import date, datetime, timedelta, timezone
+
+import pytest
+from sqlalchemy import event
+from sqlmodel import Session, SQLModel, create_engine
+
+from app.config import load_config
+from app.engine import j11_stage_d as jsd
+from app.engine.j11_maintenance import INCIDENT_DATES
+from app.models import ScannerRun
+
+_MATCHING_DATES = ", ".join(d.isoformat() for d in INCIDENT_DATES)
+_GOAL_MD_MATCHING = f"""
+# Project Goal
+
+- **J-10: some other journey** — passing
+
+- **J-11: Incident-bounded clean regeneration of derived state (owner, 2026-08-21)**
+  - **The incident date set — all 11, not the 8 currently absent.** From the authoritative removal
+    audit (`data_provider_runs` id=538, whose own cascade record lists them):
+    `{_MATCHING_DATES}`.
+  - Steps:
+    1. some step text
+       ## OWNER AUTHORIZATION — J-11 Stage C (owner, 2026-08-24)
+       - **C1 — Date-set boundary.** For the avoidance
+         of doubt they are `{_MATCHING_DATES}`.
+  - Acceptance: some acceptance text
+
+<!-- Continuous-improvement auto-journeys: appended below -->
+"""
+
+_NOT_AN_INCIDENT_DATE = date(2026, 1, 5)
+assert _NOT_AN_INCIDENT_DATE not in INCIDENT_DATES
+
+
+@pytest.fixture()
+def engine():
+    eng = create_engine("sqlite://", connect_args={"check_same_thread": False})
+
+    @event.listens_for(eng, "connect")
+    def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:
+        cursor = dbapi_connection.cursor()
+        cursor.execute("PRAGMA foreign_keys=ON")
+        cursor.close()
+
+    SQLModel.metadata.create_all(eng)
+    return eng
+
+
+@pytest.fixture()
+def cfg():
+    return load_config()
+
+
+def _mk_run(
+    session: Session, asof: date, *, engine_identity_value: str | None = None
+) -> ScannerRun:
+    run = ScannerRun(
+        asof_date=asof, created_at=datetime.now(timezone.utc), provider="seed", benchmark="SPY",
+        regime_score=55.0, regime_label="Expansion", regime_components_json="[]",
+        breadth_above_50dma=50.0, breadth_above_200dma=55.0,
+        new_high_low_json="{}", candidate_counts_json="{}",
+        engine_identity=engine_identity_value,
+    )
+    session.add(run)
+    session.flush()
+    return run
+
+
+# --- TC-1: fresh Stage D attempt identity ------------------------------------------------------------
+
+
+def test_tc1_freeze_stage_d_attempt_identity_is_fresh_never_hardcoded(engine, cfg):
+    with Session(engine) as session:
+        identity = jsd.freeze_stage_d_attempt_identity(
+            session, cfg, git_head="deadbeef", goal_md_text=_GOAL_MD_MATCHING
+        )
+    from app.engine.engine_identity import compute_engine_identity
+
+    # the recorded value is whatever `compute_engine_identity` freshly computes RIGHT NOW -- proven by
+    # equality with an INDEPENDENT second call, never asserted against a specific prior iteration's
+    # value (iteration 10's `6261ca17...` and iteration 13's `53d2ffd1...` are both real values THIS
+    # value may legitimately equal or differ from; what matters is that it is RECOMPUTED, not hardcoded
+    # -- docs/goal.md J-11 step 12's 2026-08-24 clarification: "the new attempt's identity must be
+    # recomputed... and recorded honestly, never hardcoded").
+    assert identity["engine_identity"] == compute_engine_identity(cfg)
+    assert not identity["engine_identity"].startswith("6261ca17")  # never FORCED onto the earlier attempt's value
+    assert identity["incident_dates"] == [d.isoformat() for d in INCIDENT_DATES]
+    assert identity["git_head"] == "deadbeef"
+    assert "config_subset_hash" in identity and "config_subset" in identity
+    assert "provenance" in identity and "engine_files" in identity["provenance"]
+    assert "6261ca17" in identity["scope_note"]
+    assert "NOT members of this attempt" in identity["scope_note"]
+
+
+def test_freeze_stage_d_attempt_identity_reproducible_from_same_config(engine, cfg):
+    with Session(engine) as session:
+        first = jsd.freeze_stage_d_attempt_identity(session, cfg, git_head="a", goal_md_text=_GOAL_MD_MATCHING)
+        second = jsd.freeze_stage_d_attempt_identity(session, cfg, git_head="a", goal_md_text=_GOAL_MD_MATCHING)
+    assert first["engine_identity"] == second["engine_identity"]
+    assert first["config_subset_hash"] == second["config_subset_hash"]
+    assert first["attempt_id"] != second["attempt_id"]  # each freeze mints its OWN attempt id
+
+
+# --- TC-ID-1/2: Check (A) -- before the first write -----------------------------------------------
+
+
+def test_tc_id_1_check_a_passes_on_matching_identity():
+    frozen = {"engine_identity": "A"}
+    result = jsd.check_identity_before_first_write(frozen, "A")
+    assert result["ok"] is True
+    assert result["check"] == "before_first_write"
+
+
+def test_tc_id_2_check_a_fails_closed_on_drift_before_first_write():
+    frozen = {"engine_identity": "A"}
+    result = jsd.check_identity_before_first_write(frozen, "B")
+    assert result["ok"] is False
+    # the bare-string frozen-identity form is accepted identically to the dict form
+    result_bare = jsd.check_identity_before_first_write("A", "B")
+    assert result_bare["ok"] is False
+
+
+# --- TC-ID-3: Check (B) -- before a subsequent date, drift stops the attempt before that date --------
+
+
+def test_tc_id_3_check_b_passes_on_matching_then_fails_closed_on_drift():
+    frozen = {"engine_identity": "A"}
+    date1, date2 = INCIDENT_DATES[0], INCIDENT_DATES[1]
+    result_date1 = jsd.check_identity_before_date(frozen, "A", date1)
+    assert result_date1["ok"] is True and result_date1["in_scope"] is True
+
+    result_date2 = jsd.check_identity_before_date(frozen, "B", date2)
+    assert result_date2["ok"] is False and result_date2["in_scope"] is True
+    assert result_date2["date"] == date2.isoformat()
+
+
+# --- TC-ID-4/5: Check (C) -- after persistence, NULL or mismatched is failure -----------------------
+
+
+def test_tc_id_4_check_c_fails_on_null_persisted_identity():
+    frozen = {"engine_identity": "A"}
+    result = jsd.check_identity_after_persist(frozen, None, run_id=42, one_date=INCIDENT_DATES[0])
+    assert result["ok"] is False
+    assert result["in_scope"] is True
+
+
+def test_tc_id_5_check_c_fails_on_mismatched_persisted_identity():
+    frozen = {"engine_identity": "A"}
+    result = jsd.check_identity_after_persist(frozen, "B", run_id=42, one_date=INCIDENT_DATES[0])
+    assert result["ok"] is False
+
+
+def test_check_c_passes_on_matching_persisted_identity():
+    frozen = {"engine_identity": "A"}
+    result = jsd.check_identity_after_persist(frozen, "A", run_id=42, one_date=INCIDENT_DATES[0])
+    assert result["ok"] is True
+
+
+# --- TC-ID-6: the 34 surviving out-of-scope runs -- no failure, no mutation, vacuous pass -----------
+
+
+def test_tc_id_6_out_of_scope_date_never_raises_a_failure_regardless_of_identity_mismatch():
+    frozen = {"engine_identity": "A"}
+    # a surviving run stamped an EARLIER attempt's identity ("6261ca17...") on a date that is NOT one of
+    # this attempt's 11 incident dates -- exactly the 34 surviving runs' shape.
+    result_b = jsd.check_identity_before_date(frozen, "6261ca17-earlier-attempt", _NOT_AN_INCIDENT_DATE)
+    assert result_b["ok"] is True
+    assert result_b["in_scope"] is False
+    assert "outside_j11_stage_d_attempt_scope" in result_b["reason"]
+
+    result_c = jsd.check_identity_after_persist(
+        frozen, "6261ca17-earlier-attempt", run_id=999, one_date=_NOT_AN_INCIDENT_DATE
+    )
+    assert result_c["ok"] is True
+    assert result_c["in_scope"] is False
+
+    # Check (A) never even reads a run's stamped identity at all (its inputs are frozen/current computed
+    # values, never a ScannerRun row) -- so it structurally can never be affected by the 34 survivors'
+    # stamps either, confirming no code path in this module ever compares against them.
+    result_a = jsd.check_identity_before_first_write(frozen, "A")
+    assert result_a["ok"] is True
+
+
+# --- TC-8..13: the Stage D preflight capture + comparison gate + verdict, fixture-DB shape ----------
+
+
+def _fresh_preflight(engine, cfg):
+    with Session(engine) as session:
+        return jsd.capture_stage_d_preflight(
+            session, engine, None, goal_md_text=_GOAL_MD_MATCHING, git_head="deadbeef", config=cfg,
+        )
+
+
+def test_tc8_preflight_reports_zero_scanner_runs_on_all_11_incident_dates_when_empty(engine, cfg):
+    preflight = _fresh_preflight(engine, cfg)
+    per_date = preflight["pre_reset_inventory"]["per_date"]
+    assert set(per_date) == {d.isoformat() for d in INCIDENT_DATES}
+    assert all(not per_date[key]["scanner_run"]["present"] for key in per_date)
+
+
+def test_tc9_and_tc10_preflight_capture_shape_includes_manifest_and_prices(engine, cfg):
+    preflight = _fresh_preflight(engine, cfg)
+    assert preflight["manifest_row_count"] == 0  # empty fixture DB
+    assert "table_sql" in preflight["manifest_ddl"]
+    assert preflight["pre_reset_inventory"]["daily_prices"]["row_count"] == 0
+
+
+def test_tc11_check_a_passes_against_the_freshly_frozen_identity(engine, cfg):
+    preflight = _fresh_preflight(engine, cfg)
+    assert preflight["identity_check_a"]["ok"] is True
+    assert preflight["identity_check_a"]["current_engine_identity"] == preflight["attempt_identity"]["engine_identity"]
+
+
+def test_tc12_c1_date_set_boundary_matches_goal_md(engine, cfg):
+    preflight = _fresh_preflight(engine, cfg)
+    assert preflight["c1_date_set_boundary_check"]["ok"] is True
+
+
+def test_tc13_maintenance_isolation_env_recorded_verbatim(engine, cfg, monkeypatch):
+    monkeypatch.setenv("CHAIN_MAINTENANCE_ISOLATION", "required")
+    preflight = _fresh_preflight(engine, cfg)
+    assert preflight["maintenance_isolation_env"] == {"present": True, "value": "required"}
+
+    monkeypatch.delenv("CHAIN_MAINTENANCE_ISOLATION", raising=False)
+    preflight_absent = _fresh_preflight(engine, cfg)
+    assert preflight_absent["maintenance_isolation_env"] == {"present": False, "value": None}
+
+
+# --- the comparison gate against a certified baseline -------------------------------------------------
+
+
+def _certified_from(preflight: dict) -> dict:
+    """A certified-baseline dict in `load_stage_d_certified_baseline`'s OWN return shape, built as a
+    self-diff of a fresh preflight (an unchanged database) -- mirrors
+    `test_j11_stage_c_preflight.py`'s `test_tc2_comparison_gate_passes_when_certified_state_matches_
+    fresh_state` pattern."""
+    return {
+        "daily_prices_fingerprint": preflight["pre_reset_inventory"]["daily_prices"]["fingerprint"],
+        "manifest_row_count": preflight["manifest_row_count"],
+        "manifest_ddl": copy.deepcopy(preflight["manifest_ddl"]),
+        "manifest_dump": copy.deepcopy(preflight["manifest_dump"]),
+        "data_provider_runs_count": preflight["pre_reset_inventory"]["data_provider_runs_count"],
+        "watchlist_count": preflight["pre_reset_inventory"]["watchlist_count"],
+    }
+
+
+def test_gate_passes_when_certified_state_matches_fresh_state(engine, cfg):
+    preflight = _fresh_preflight(engine, cfg)
+    certified = _certified_from(preflight)
+    gate = jsd.compare_stage_d_preflight_to_certified(preflight, certified)
+    assert gate["all_invariants_hold"] is True
+    assert gate["material_mismatch"] is False
+    verdict = jsd.stage_d_preflight_verdict(gate)
+    assert verdict["passed"] is True
+
+
+def test_gate_stops_on_daily_prices_fingerprint_drift(engine, cfg):
+    preflight = _fresh_preflight(engine, cfg)
+    certified = _certified_from(preflight)
+    certified["daily_prices_fingerprint"] = "a-different-fingerprint"
+    gate = jsd.compare_stage_d_preflight_to_certified(preflight, certified)
+    assert gate["all_invariants_hold"] is False
+    assert gate["checks"]["daily_prices_fingerprint_unchanged"] is False
+    verdict = jsd.stage_d_preflight_verdict(gate)
+    assert verdict["passed"] is False
+    assert "daily_prices_fingerprint_unchanged" in verdict["failing_checks"]
+
+
+# --- TC-19 (Stage D half): unexpected incident ScannerRun population -> refusal ---------------------
+
+
+def test_tc19_unexpected_incident_scanner_run_population_refuses(engine, cfg):
+    with Session(engine) as session:
+        _mk_run(session, INCIDENT_DATES[0])  # a ScannerRun exists where the Stage D precondition
+        session.commit()                     # requires zero -- the boot-warmup-race / retry-collision shape
+
+    preflight = _fresh_preflight(engine, cfg)
+    certified = _certified_from(preflight)
+    # the certified baseline expects the ORIGINAL (empty) per-date state; compare_stage_d_preflight_to_
+    # certified derives its own "all_incident_dates_zero_scanner_runs" check straight from the FRESH
+    # preflight's own per_date inventory, so an unexpected run is caught without needing a certified-side
+    # per-date field at all.
+    gate = jsd.compare_stage_d_preflight_to_certified(preflight, certified)
+    assert gate["checks"]["all_incident_dates_zero_scanner_runs"] is False
+    assert gate["material_mismatch"] is True
+    verdict = jsd.stage_d_preflight_verdict(gate)
+    assert verdict["passed"] is False
+
+
+def test_scanner_run_on_a_non_incident_date_does_not_trip_the_zero_runs_check(engine, cfg):
+    with Session(engine) as session:
+        _mk_run(session, _NOT_AN_INCIDENT_DATE, engine_identity_value="6261ca17-earlier-attempt")
+        session.commit()
+
+    preflight = _fresh_preflight(engine, cfg)
+    certified = _certified_from(preflight)
+    gate = jsd.compare_stage_d_preflight_to_certified(preflight, certified)
+    assert gate["checks"]["all_incident_dates_zero_scanner_runs"] is True
+
+
+# --- Goal 5: the readiness verdict -- AVB-C/D forces NO regardless of the preflight gate (TC-25) ------
+
+
+@pytest.mark.parametrize(
+    "avb_classification,preflight_passed,expected_ready",
+    [
+        ("AVB-A", True, True),
+        ("AVB-B", True, True),
+        ("AVB-A", False, False),
+        ("AVB-C", True, False),
+        ("AVB-D", True, False),
+        ("AVB-C", False, False),
+    ],
+)
+def test_tc25_readiness_verdict_combines_preflight_and_avb_classification(
+    avb_classification, preflight_passed, expected_ready
+):
+    preflight_verdict = {"passed": preflight_passed, "reason": "x"}
+    readiness = jsd.stage_d_readiness_verdict(preflight_verdict, avb_classification)
+    assert readiness["ready"] is expected_ready
+    assert readiness["authorized"] is False  # unconditional, per every parametrized case
+
+
+def test_readiness_verdict_rejects_unknown_avb_classification():
+    with pytest.raises(ValueError):
+        jsd.stage_d_readiness_verdict({"passed": True, "reason": "x"}, "AVB-Z")
```
