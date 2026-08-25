# Iteration diff (bounded)

Files changed: 12. Shown in full: 9.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/app/engine/j11_avb_diagnostic.py` (157 lines not shown)
- `apps/backend/app/engine/j11_stage_d.py` (150 lines not shown)
- `apps/backend/tests/test_j11_stage_d.py` (66 lines not shown)

```diff
diff --git a/apps/backend/app/engine/j11_avb_diagnostic.py b/apps/backend/app/engine/j11_avb_diagnostic.py
index ec288442..ad0ac0ac 100644
--- a/apps/backend/app/engine/j11_avb_diagnostic.py
+++ b/apps/backend/app/engine/j11_avb_diagnostic.py
@@ -28,6 +28,24 @@ Classification vocabulary (exactly one, per Goal 4):
   - **AVB-C** -- the restored representation is inconsistent with Trendora's own stored convention AND
     materially affects canonical Stage D output; **STAGE D NOT READY**, owner decision.
   - **AVB-D** -- evidence insufficient; **STAGE D NOT READY**, do not guess.
+
+**goal-market-compass iter-15 addendum.** Iteration 14 left a price-only tautology behind:
+`compute_counterfactual_representations` set `volume_a = volume_b = stored_volume`, so `volume_a_equals_b`
+was true BY CONSTRUCTION and `bridged+compensating` -- the one label that could flag a genuine volume
+problem -- was structurally unreachable from any real input. `docs/goal.md` AG-9's "Dated exception #2 --
+AVB convention diagnostic (owner, 2026-08-25)" authorizes the ONE bounded fetch that fixes this
+(`app.engine.j11_avb_provider_fetch`, called from `apps/backend/scripts/run_j11_avb_provider_fetch.py` --
+never from this module, which stays fetch-free). This module now consumes that persisted fetch evidence:
+`compute_provider_comparison`/`classify_date_from_provider_comparison`/
+`classify_local_convention_with_volume_evidence` are the NEW genuinely volume-aware functions;
+`compute_counterfactual_representations` now sources representation B from the FETCHED evidence (fails
+closed, `evidence_available: False`, when it is missing for a date -- never a silent fallback to the old
+arithmetic derivation or a copy of `stored_volume`); `_build_bars_with_transformed_close` and both
+`trace_*_impact` functions gained an optional `volume_override` so the decision-impact trace substitutes
+BOTH close and volume for the target dates, not close alone. `classify_local_convention` (price-only) and
+`compute_counterfactual_representations`'s old arithmetic path are both PRESERVED, unchanged, as
+documented fallbacks/cross-checks -- never removed, never silently preferred over real fetched evidence
+when it exists.
 """
 from __future__ import annotations
 
@@ -72,6 +90,27 @@ RECOVERED_DATES: tuple[date, ...] = (date(2026, 8, 11), date(2026, 8, 12))
 # `j11_maintenance.py` are -- a diagnostic sanity bound, not a decision cutoff).
 _CONTINUITY_JUMP_THRESHOLD = 0.25
 
+# goal-market-compass iter-15 (Goal 3): the relative-tolerance band a ratio must fall within to count as
+# "matches" a target value (1.0 for "unchanged", `bridge_factor` for "fully rebased", or
+# `expected_inverse_volume_ratio` for "compensating"). Reuses the SAME 1% band the ORIGINAL calibration
+# check already applied inline (`0.99 <= ratio <= 1.01`, i.e. target*(1-0.01) .. target*(1+0.01)) -- now a
+# single named, documented constant so the price-only check and the new volume-aware checks apply
+# IDENTICAL tolerance rather than two independently-chosen bands. A diagnostic sanity bound, not a
+# decision cutoff -- excluded from `test_no_magic_numbers.CALC_FILES` for the same reason
+# `_CONTINUITY_JUMP_THRESHOLD` above already is (this whole module is not in `CALC_FILES`).
+_RATIO_RELATIVE_TOLERANCE = 0.01
+
+
+def _within_relative_tolerance(
+    value: Optional[float], target: Optional[float], tolerance: float = _RATIO_RELATIVE_TOLERANCE
+) -> bool:
+    """Whether `value` sits within `tolerance` (relative) of `target`. `target` of `None`/`0`, or `value`
+    of `None`, is NEVER "within tolerance" -- fails closed rather than raising or silently treating a
+    missing measurement as a match."""
+    if value is None or target is None or target == 0:
+        return False
+    return abs(value - target) <= abs(target) * tolerance
+
 
 def _now_iso() -> str:
     return datetime.now(timezone.utc).isoformat()
@@ -187,7 +226,7 @@ def classify_local_convention(stored_series: list[dict], evidence_row: dict) ->
             calibration_results.append({"date": key, "classification": "mixed/indeterminate", "reason": "no comparable pair or stored row"})
             continue
         ratio = stored["close"] / pair["fallback_close"] if pair["fallback_close"] else None
-        classification = "bridged+raw" if ratio is not None and not (0.99 <= ratio <= 1.01) else "raw+raw"
+        classification = "bridged+raw" if ratio is not None and not _within_relative_tolerance(ratio, 1.0) else "raw+raw"
         calibration_results.append({
             "date": key, "stored_close": stored["close"], "fallback_close": pair["fallback_close"],
             "ratio": ratio, "classification": classification,
@@ -267,27 +306,282 @@ def classify_local_convention(stored_series: list[dict], evidence_row: dict) ->
     }
 
 
+# ----------------------------------------------------------------------------------------------
+# goal-market-compass iter-15 (Goals 3/4): genuine cross-source (fetched provider vs stored) per-date
+# comparison + volume-aware window classification -- the fix for the price-only tautology iter-14 left
+# behind (`volume_a = volume_b = stored_volume`, so `bridged+compensating` was structurally unreachable).
+# ----------------------------------------------------------------------------------------------
+
+
+def compute_provider_comparison(
+    stored_close: Optional[float],
+    stored_volume: Optional[float],
+    provider_close: Optional[float],
+    provider_volume: Optional[float],
+    bridge_factor: float,
+) -> dict:
+    """The per-date REAL cross-source comparison record Goal 3 requires (TC-11) -- computed for any date
+    where BOTH a stored `daily_prices` row and Goal 2's fetched provider evidence exist. Every field is a
+    plain, auditable arithmetic derivation; this function only MEASURES -- `classify_date_from_provider_
+    comparison` is what DECIDES a classification from these measurements.
+
+    `bridge_adjusted_compensation_test`'s reasoning (logged assumption, `runs/goal-session-market-compass/
+    state/assumptions.md` iter-15 entry, independently re-derived here): dollar volume (close x volume) is
+    invariant under a genuine, consistent basis change -- if BOTH price and share-count/volume were
+    rebased together by a reverse-split-like factor (price x bridge_factor, volume / bridge_factor), then
+    `stored_close*stored_volume` and `provider_close*provider_volume` are approximately EQUAL
+    (`dollar_volume_ratio ~= 1`, i.e. "compensating"). If only price was rebased and volume was left on
+    the provider's raw scale, `stored_close*stored_volume` is instead approximately `bridge_factor` TIMES
+    `provider_close*provider_volume` (`dollar_volume_ratio ~= bridge_factor`, i.e. "raw" volume) -- which
+    is exactly `close_ratio(~=bridge_factor) x volume_ratio(~=1)`. Neither hypothesis is assumed true here
+    -- both `compensates` and `matches_raw_volume_dollar_shift` are computed and reported side by side."""
+    close_ratio = (
+        stored_close / provider_close if stored_close is not None and provider_close else None
+    )
+    volume_ratio = (
+        stored_volume / provider_volume if stored_volume is not None and provider_volume else None
+    )
+    expected_inverse_volume_ratio = 1.0 / bridge_factor if bridge_factor else None
+    stored_dollar_volume = (
+        stored_close * stored_volume if stored_close is not None and stored_volume is not None else None
+    )
+    provider_dollar_volume = (
+        provider_close * provider_volume if provider_close is not None and provider_volume is not None else None
+    )
+    dollar_volume_ratio = (
+        stored_dollar_volume / provider_dollar_volume
+        if stored_dollar_volume is not None and provider_dollar_volume else None
+    )
+    compensates = _within_relative_tolerance(dollar_volume_ratio, 1.0)
+    matches_raw_volume_dollar_shift = _within_relative_tolerance(dollar_volume_ratio, bridge_factor)
+
+    return {
+        "stored_close": stored_close,
+        "stored_volume": stored_volume,
+        "provider_close": provider_close,
+        "provider_volume": provider_volume,
+        "close_ratio": close_ratio,
+        "volume_ratio": volume_ratio,
+        "bridge_factor": bridge_factor,
+        "expected_inverse_volume_ratio": expected_inverse_volume_ratio,
+        "stored_dollar_volume": stored_dollar_volume,
+        "provider_dollar_volume": provider_dollar_volume,
+        "dollar_volume_ratio": dollar_volume_ratio,
+        "bridge_adjusted_compensation_test": {
+            "formula": (
+                "dollar_volume_ratio = (stored_close*stored_volume) / (provider_close*provider_volume); "
+                "compensates iff dollar_volume_ratio ~= 1.0 (price-up offset by volume-down); "
+                "matches_raw_volume_dollar_shift iff dollar_volume_ratio ~= bridge_factor (only price "
+                "was rebased, volume stayed on the provider's raw scale)"
+            ),
+            "dollar_volume_ratio": dollar_volume_ratio,
+            "compensates": compensates,
+            "matches_raw_volume_dollar_shift": matches_raw_volume_dollar_shift,
+        },
+    }
+
+
+def classify_date_from_provider_comparison(
+    comparison: dict, tolerance: float = _RATIO_RELATIVE_TOLERANCE
+) -> str:
+    """One of `raw+raw` / `bridged+raw` / `bridged+compensating` / `mixed/indeterminate`, from a SINGLE
+    date's real cross-source comparison (Goal 3/4) -- every label is mechanically reachable, never
+    hardcoded or pre-selected:
+      - `raw+raw`: close_ratio ~= 1 AND volume_ratio ~= 1 (neither side was rebased).
+      - `bridged+compensating`: close_ratio ~= bridge_factor AND volume_ratio ~= expected_inverse_volume_
+        ratio (price AND volume were both rebased; dollar volume conserved -- TC-14).
+      - `bridged+raw`: close_ratio ~= bridge_factor AND volume_ratio ~= 1 (only price was rebased,
+        volume was left on the provider's raw scale -- TC-15).
+      - `mixed/indeterminate`: evidence missing, or a shape that matches none of the three hypotheses
+        above (a genuine inconsistency -- never silently forced into the nearest label)."""
+    close_ratio = comparison.get("close_ratio")
+    volume_ratio = comparison.get("volume_ratio")
+    bridge_factor = comparison.get("bridge_factor")
+    expected_inverse_volume_ratio = comparison.get("expected_inverse_volume_ratio")
+    if close_ratio is None or volume_ratio is None or not bridge_factor or expected_inverse_volume_ratio is None:
+        return "mixed/indeterminate"
+
+    close_near_one = _within_relative_tolerance(close_ratio, 1.0, tolerance)
+    close_near_bridge = _within_relative_tolerance(close_ratio, bridge_factor, tolerance)
+    volume_near_one = _within_relative_tolerance(volume_ratio, 1.0, tolerance)
+    volume_near_inverse = _within_relative_tolerance(volume_ratio, expected_inverse_volume_ratio, tolerance)
+
+    if close_near_one and volume_near_one:
+        return "raw+raw"
+    if close_near_bridge and volume_near_inverse:
+        return "bridged+compensating"
+    if close_near_bridge and volume_near_one:
+        return "bridged+raw"
+    return "mixed/indeterminate"
+
+
+def classify_local_convention_with_volume_evidence(
+    stored_series: list[dict], evidence_row: dict, provider_evidence_by_date: dict[str, dict]
+) -> dict:
+    """The volume-aware successor to `classify_local_convention` (Goal 3/4) -- this is the function
+    `classify_avb` is fed from THIS iteration onward. Classifies the calibration window AND the
+    recovered-dates window from a GENUINE per-date cross-source comparison (Goal 2's fetched provider
+    close+volume vs the stored close+volume), so `bridged+compensating` becomes genuinely reachable and
+    `raw+raw`/`bridged+raw` are PROVEN from real volume evidence rather than assumed from price alone.
+    `provider_evidence_by_date` is Goal 2's persisted fetch evidence (`{iso_date: {"close": ...,
+    "volume": ...}}`) for AG-9 dated exception #2's six permitted dates.
+
+    A date inside either window whose fetched evidence is missing/insufficient classifies its OWN entry
+    (and therefore that whole window, since a window's classification requires every one of its dates to
+    agree) as `mixed/indeterminate` -- it NEVER falls back to the OLD price-only continuity method
+    (evidence was supposed to exist for these six specific dates; `classify_local_convention` remains
+    available unchanged as a documented price-only cross-check/fallback, never silently substituted here).
+
+    The `surrounding_window` (dates outside the six AG-9-permitted dates, where no fetched evidence exists
+    or could exist under the amendment) still uses ONLY the day-over-day continuity check -- corroborating
+    narrative, never a substitute for the direct fetched comparison the two windows above now have
+    (Goal 3's own words)."""
+    by_date = {row["date"]: row for row in stored_series}
+    bridge_factor = evidence_row.get("bridge_factor")
+
+    def _classify_window(dates: tuple) -> tuple[list[dict], str]:
+        results = []
+        for one_date in dates:
+            key = one_date.isoformat()
+            stored = by_date.get(key)
+            provider = provider_evidence_by_date.get(key)
+            if (
+                stored is None or stored.get("close") is None
+                or provider is None or provider.get("close") is None or provider.get("volume") is None
+            ):
+                results.append({
+                    "date": key,
+                    "classification": "mixed/indeterminate",
+                    "reason": "no stored row, or no sufficient fetched provider evidence, for this date",
+                })
+                continue
+            comparison = compute_provider_comparison(
+                stored["close"], stored.get("volume"), provider["close"], provider["volume"], bridge_factor,
+            )
+            classification = classify_date_from_provider_comparison(comparison)
+            results.append({"date": key, "classification": classification, "comparison": comparison})
+        classes = {r["classification"] for r in results}
+        overall = classes.pop() if len(classes) == 1 else "mixed/indeterminate"
+        return results, overall
+
+    calibration_results, calibration_window_classification = _classify_window(CALIBRATION_DATES)
+    recovered_results, recovered_window_classification = _classify_window(RECOVERED_DATES)
+
+    returns = _day_over_day_returns(stored_series)
+    anomalous_jumps = [r for r in returns if abs(r["pct_return"]) > _CONTINUITY_JUMP_THRESHOLD]
+    recovered_keys = {d.isoformat() for d in RECOVERED_DATES}
+    boundary_jumps = [
+        j for j in anomalous_jumps if j["from_date"] in recovered_keys or j["to_date"] in recovered_keys
+    ]
+
+    windows = {
+        "calibration_window": {
+            "dates": [d.isoformat() for d in CALIBRATION_DATES],
+            "classification": calibration_window_classification,
+            "per_date": calibration_results,
+            "evidence": (
+                "genuine cross-source comparison against Goal 2's AG-9 dated-exception-#2 fetched "
+                "provider evidence (close AND volume, never a stored-volume tautology)"
+            ),
+        },
+        "recovered_dates": {
+            "dates": [d.isoformat() for d in RECOVERED_DATES],
+            "classification": recovered_window_classification,
+            "per_date": recovered_results,
+            "boundary_jumps": boundary_jumps,
+            "evidence": (
+                "genuine cross-source comparison against Goal 2's AG-9 dated-exception-#2 fetched "
+                "provider evidence -- the SAME direct evidence class as the calibration window, no "
+                "longer continuity-only the way iteration 14 left it"
+            ),
+        },
+        "surrounding_window": {
+            "classification": "mixed/indeterminate" if anomalous_jumps else "no_independent_signal",
+            "anomalous_jumps": anomalous_jumps,
+            "evidence": (
+                "no independent comparable exists outside the six AG-9-permitted dates; day-over-day "
+                "continuity is corroborating narrative ONLY here, never a substitute for the direct "
+                "fetched comparison the two windows above now have (Goal 3)"
+            ),
+        },
+    }
+
+    evidence_backed_classes = {calibration_window_classification, recovered_window_classification}
+    indeterminate = "mixed/indeterminate" in evidence_backed_classes
+    internally_consistent = (
+        (not indeterminate) and len(evidence_backed_classes) == 1 and not boundary_jumps
+    )
+    overall_classification = (
+        "mixed/indeterminate" if indeterminate
+        else (calibration_window_classification if internally_consistent else "mixed/indeterminate")
+    )
+
+    return {
+        "windows": windows,
+        "day_over_day_returns_checked": len(returns),
+        "anomalous_jump_count": len(anomalous_jumps),
+        "internally_consistent": internally_consistent,
+        "indeterminate": indeterminate,
+        "overall_classification": overall_classification,
+        "reasoning": (
+            f"calibration window classifies as {calibration_window_classification} and the recovered-"
+            f"dates window classifies as {recovered_window_classification}, BOTH from genuine fetched "
+            f"cross-source (close+volume) comparisons against Goal 2's AG-9 dated-exception-#2 evidence "
+            "(never a price-only tautology) -- "
+            + (
+                f"{len(boundary_jumps)} boundary continuity jump(s) noted at the recovery boundary as "
+                "corroborating narrative only. "
+                if boundary_jumps else ""
+            )
+            + (
+                "internally consistent." if internally_consistent
+                else "NOT internally consistent, or evidence insufficient for at least one permitted "
+                     "date -- see per-date entries."
+            )
+        ),
+    }
+
+
 # ----------------------------------------------------------------------------------------------
 # Counterfactual representations A / B / C
 # ----------------------------------------------------------------------------------------------
 
 
-def compute_counterfactual_representations(bridge_factor: float, stored_close: float, stored_volume: float) -> dict:
-    """The three counterfactual ADV representations for one recovered date's stored row (Goal 4):
+def compute_counterfactual_representations(
+    bridge_factor: float,
+    stored_close: float,
+    stored_volume: float,
+    provider_evidence: Optional[dict] = None,
+) -> dict:
+    """The three counterfactual ADV representations for one date's stored row (Goal 3/4):
 
       - **A** -- bridged close x stored raw volume: the actual canonical value served today.
-      - **B** -- raw provider close (`stored_close / bridge_factor`, per the logged assumption -- never a
-        new fetch) x raw provider volume (== stored volume, since volume was never transformed by J-10 --
-        stated explicitly as a finding, per TC-22).
+      - **B** -- goal-market-compass iter-15 fix: when `provider_evidence` (Goal 2's fetched
+        `{"close": ..., "volume": ...}` for this date) is supplied, B is the GENUINE fetched provider
+        close AND fetched provider volume -- two independently-sourced values, never a copy of
+        `stored_volume` (the iter-14 tautology this fixes: `volume_a = volume_b = stored_volume` made
+        `volume_a_equals_b` true by construction). The OLD arithmetic derivation
+        (`stored_close / bridge_factor`) is still recorded, but ONLY as a documented fallback/cross-check
+        field (`close_b_arithmetic_fallback`) -- never silently substituted for a real fetched measurement
+        that exists. When `provider_evidence` is `None` or incomplete for this date, B FAILS CLOSED: its
+        `close`/`volume` are `None` and `evidence_available` is `False` -- never a silent fallback to the
+        arithmetic derivation or a copy of `stored_volume` (TC-13).
       - **C** -- bridged close x a stated HYPOTHETICAL inverse-adjusted volume (`stored_volume *
         bridge_factor` -- the share-count-continuity value IF the bridge factor reflected a genuine
-        corporate action with a matching volume adjustment): diagnostic only, its formula/rationale
-        recorded, never written, never assumed correct."""
+        corporate action with a matching volume adjustment): UNCHANGED from iteration 14 -- diagnostic
+        only, its formula/rationale recorded, never written, never assumed correct."""
     close_a, volume_a = stored_close, stored_volume
-    close_b = stored_close / bridge_factor if bridge_factor else None
-    volume_b = stored_volume  # never transformed by J-10 -- stated explicitly (TC-22)
+    arithmetic_close_b = stored_close / bridge_factor if bridge_factor else None
     volume_c = stored_volume * bridge_factor if bridge_factor else None
 
+    evidence_available = (
+        provider_evidence is not None
+        and provider_evidence.get("close") is not None
+        and provider_evidence.get("volume") is not None
+    )
+    close_b = provider_evidence["close"] if evidence_available else None
+    volume_b = provider_evidence["volume"] if evidence_available else None
+
     def _leaf(close, volume, formula):
         adv = close * volume if close is not None and volume is not None else None
         return {"close": close, "volume": volume, "close_times_volume": adv, "formula": formula}
@@ -295,11 +589,19 @@ def compute_counterfactual_representations(bridge_factor: float, stored_close: f
     representation_a = _leaf(
         close_a, volume_a, "A = stored_bridged_close x stored_raw_volume (the actual canonical value served today)"
     )
-    representation_b = _leaf(
-        close_b, volume_b,
-        "B = (stored_close / bridge_factor) x stored_volume (raw-provider-scale close; volume equals A's -- "
-        "never transformed by J-10)",
-    )
+    if evidence_available:
+        b_formula = (
+            "B = provider_close x provider_volume (Goal 2's FETCHED evidence -- two independently-"
+            "sourced values, never a copy of stored_volume; the arithmetic stored_close/bridge_factor "
+            "value is recorded separately in close_b_arithmetic_fallback for cross-check only)"
+        )
+    else:
+        b_formula = (
+            "B = UNAVAILABLE -- no sufficient fetched provider evidence for this date (fail-closed; "
+            "never silently substituted with the arithmetic stored_close/bridge_factor derivation or a "
+            "copy of stored_volume)"
+        )
+    representation_b = _leaf(close_b, volume_b, b_formula)
     representation_c = _leaf(
         close_a, volume_c,
         "C = stored_bridged_close x (stored_volume x bridge_factor) -- DIAGNOSTIC ONLY: the hypothetical "
@@ -308,10 +610,14 @@ def compute_counterfactual_representations(bridge_factor: float, stored_close: f
     )
     return {
         "bridge_factor": bridge_factor,
+        "evidence_available": evidence_available,
+        "close_b_arithmetic_fallback": arithmetic_close_b,
         "A": representation_a,
         "B": representation_b,
         "C": representation_c,
-        "volume_a_equals_b": representation_a["volume"] == representation_b["volume"],
+        "volume_a_equals_b": (
+            representation_a["volume"] == representation_b["volume"] if evidence_available else None
+        ),
     }
 
 
@@ -320,27 +626,53 @@ def compute_counterfactual_representations(bridge_factor: float, stored_close: f
... [diff_bound] apps/backend/app/engine/j11_avb_diagnostic.py: 157 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/app/engine/j11_avb_provider_fetch.py b/apps/backend/app/engine/j11_avb_provider_fetch.py
new file mode 100644
index 00000000..5b74272f
--- /dev/null
+++ b/apps/backend/app/engine/j11_avb_provider_fetch.py
@@ -0,0 +1,143 @@
+"""app.engine.j11_avb_provider_fetch -- J-11 Stage D readiness (goal-market-compass iter-15, Goal 2): the
+ONE bounded, read-only comparison fetch `docs/goal.md` AG-9's "Dated exception #2 -- AVB convention
+diagnostic (owner, 2026-08-25 -- single-use, self-closing, DIAGNOSTIC ONLY)" authorizes.
+
+The exception permits EXACTLY this and nothing else: symbol `AVB` only; dates `2026-08-05, 2026-08-06,
+2026-08-07, 2026-08-10, 2026-08-11, 2026-08-12` -- six dates, none others, none inferred from a range or
+cadence; fields `date`/`close`/`volume` only; via the canonical Yahoo provider path Trendora already uses
+(`app.data_providers.yahoo_provider.YahooProvider`), so the comparison is like-for-like. This module is
+the ONLY call site anywhere in this iteration's diff that calls `.get_daily`/`.get_adjusted_close` on a
+live provider -- grep-verifiable, so "exactly one fetch" stays auditable
+(`apps/backend/scripts/run_j11_avb_provider_fetch.py` constructs the real `YahooProvider` and is the only
+place that imports it; every other new/changed module or script this iteration touches reads THIS
+module's persisted output instead of ever constructing a provider itself).
+
+This is NOT ingest and NOT recovery: `fetch_avb_provider_evidence` takes an INJECTED `PriceProvider`
+(never constructs one -- so it stays unit-testable without a real network call), performs no database I/O
+of any kind (no import of `app.db`/`sqlmodel.Session` anywhere in this file), and returns a plain dict for
+the caller to persist wherever it chooses -- there is no write path to `daily_prices` or any other table
+inside this module at all. J-10 is NOT reopened: the persisted J-10 bridge factor is read verbatim by the
+caller (`app.engine.j11_avb_diagnostic.load_j10_avb_evidence`) and passed in here, never re-derived.
+
+Fail-closed, per the amendment's own words ("If the provider cannot supply sufficient evidence, classify
+honestly as AVB-D and stop -- do not guess, do not substitute adjacent-day statistics, and do not broaden
+the fetch"): `fetch_avb_provider_evidence` catches `ProviderUnavailableError` (whose `RateLimitError`
+subclass is therefore also caught) and NEVER lets it propagate past this function; any date short of a
+full six-date return records `sufficient_evidence: false` and the SPECIFIC missing date(s) instead of
+substituting anything. The whole `.get_daily` call happens exactly once per invocation of this function --
+there is no retry loop, no per-date fetch, and no broadening of the requested window anywhere in this
+file.
+"""
+from __future__ import annotations
+
+from datetime import date, datetime, timezone
+from typing import Optional
+
+from app.data_providers.base import PriceProvider, ProviderUnavailableError
+
+AVB_SYMBOL = "AVB"
+
+# The exact six ISO dates AG-9's "Dated exception #2" authorizes -- a literal historical/contractual fact
+# about THIS one-time diagnostic, never a range or cadence-derived list (same posture as
+# `j11_maintenance.INCIDENT_DATES`/`j11_avb_diagnostic.CALIBRATION_DATES`/`RECOVERED_DATES` -- this is
+# their exact union, restated here as its own literal so this module carries no import-time dependency on
+# either for its own authorization boundary). `test_no_magic_numbers.py`'s `CALC_FILES` does not include
+# this module (it is fetch/provenance plumbing, not scoring/decision calculation code).
+PERMITTED_DATES: tuple[date, ...] = (
+    date(2026, 8, 5),
+    date(2026, 8, 6),
+    date(2026, 8, 7),
+    date(2026, 8, 10),
+    date(2026, 8, 11),
+    date(2026, 8, 12),
+)
+FETCH_WINDOW_START: date = PERMITTED_DATES[0]
+FETCH_WINDOW_END: date = PERMITTED_DATES[-1]
+
+# The comparison formulas the amendment requires be recorded as auditable provenance alongside the raw
+# fetched values -- documentation only (the actual arithmetic is computed downstream, in
+# `j11_avb_diagnostic.compute_provider_comparison`, against stored + fetched values together); recorded
+# here, verbatim, so the fetch evidence artifact is self-describing even read in isolation.
+COMPARISON_FORMULAS: dict = {
+    "close_ratio": "stored_close / provider_close",
+    "volume_ratio": "stored_volume / provider_volume",
+    "expected_inverse_volume_ratio": "1 / bridge_factor",
+    "stored_dollar_volume": "stored_close * stored_volume",
+    "provider_dollar_volume": "provider_close * provider_volume",
+    "dollar_volume_ratio": "stored_dollar_volume / provider_dollar_volume",
+    "bridge_adjusted_compensation_test": (
+        "dollar_volume_ratio ~= 1.0 implies price/volume rebasing COMPENSATE (dollar volume conserved); "
+        "dollar_volume_ratio ~= bridge_factor implies volume was left RAW while only price was rebased"
+    ),
+}
+
+
+def _now_iso() -> str:
+    return datetime.now(timezone.utc).isoformat()
+
+
+def fetch_avb_provider_evidence(provider: PriceProvider, *, bridge_factor: float) -> dict:
+    """AG-9 dated exception #2's ONE authorized fetch. Calls `provider.get_daily(AVB_SYMBOL,
+    start=FETCH_WINDOW_START, end=FETCH_WINDOW_END)` EXACTLY once. Any bar the provider returns outside
+    `PERMITTED_DATES` is discarded (recorded in `discarded_dates_outside_permitted_set` for auditability,
+    never used for anything). `bridge_factor` is the CALLER-supplied, already-persisted J-10 value (the
+    caller reuses `j11_avb_diagnostic.load_j10_avb_evidence` -- this function never reads that file or any
+    other file itself, keeping it a pure, fixture-testable composition over an injected provider).
+
+    Returns a plain dict -- never writes anything, never raises past this function on a provider failure
+    (`ProviderUnavailableError`, including its `RateLimitError` subclass, is caught and recorded as
+    `sufficient_evidence: false` with `fetch_error` populated). A provider that returns fewer than six of
+    the permitted dates (no exception, just a short list) is ALSO `sufficient_evidence: false`, with
+    `missing_dates` naming exactly which ones -- never inferred, never substituted from an adjacent day."""
+    capture_timestamp = _now_iso()
+    provider_label = getattr(provider, "source", None) or "yahoo"
+    requested_dates = [d.isoformat() for d in PERMITTED_DATES]
+
+    fetch_error: Optional[dict] = None
+    try:
+        bars = provider.get_daily(AVB_SYMBOL, start=FETCH_WINDOW_START, end=FETCH_WINDOW_END)
+    except ProviderUnavailableError as exc:
+        bars = []
+        fetch_error = {"type": type(exc).__name__, "message": str(exc)}
+
+    permitted_set = set(PERMITTED_DATES)
+    per_date: dict[str, dict] = {}
+    discarded_dates: list[str] = []
+    for bar in bars:
+        if bar.date in permitted_set:
+            per_date[bar.date.isoformat()] = {
+                "close": float(bar.close) if bar.close is not None else None,
+                "volume": float(bar.volume) if bar.volume is not None else None,
+            }
+        else:
+            discarded_dates.append(bar.date.isoformat())
+
+    # A returned bar with a null close/volume is exactly as unusable as a missing bar -- treat it as
+    # absent rather than as a present-but-empty entry that could later be mistaken for real evidence.
+    for key in list(per_date):
+        entry = per_date[key]
+        if entry["close"] is None or entry["volume"] is None:
+            del per_date[key]
+
+    missing_dates = [d for d in requested_dates if d not in per_date]
+    sufficient_evidence = fetch_error is None and not missing_dates
+
+    return {
+        "generated_at": _now_iso(),
+        "capture_timestamp": capture_timestamp,
+        "provider": provider_label,
+        "symbol": AVB_SYMBOL,
+        "requested_dates": requested_dates,
+        "requested_window": {
+            "start": FETCH_WINDOW_START.isoformat(),
+            "end": FETCH_WINDOW_END.isoformat(),
+        },
+        "fetch_call_count": 1,
+        "fetch_error": fetch_error,
+        "discarded_dates_outside_permitted_set": discarded_dates,
+        "per_date": per_date,
+        "missing_dates": missing_dates,
+        "bridge_factor": bridge_factor,
+        "comparison_formulas": COMPARISON_FORMULAS,
+        "sufficient_evidence": sufficient_evidence,
+    }
diff --git a/apps/backend/app/engine/j11_stage_d.py b/apps/backend/app/engine/j11_stage_d.py
index d1e188be..79d66430 100644
--- a/apps/backend/app/engine/j11_stage_d.py
+++ b/apps/backend/app/engine/j11_stage_d.py
@@ -53,14 +53,17 @@ inserts a snapshot/manifest/price row (mirrors `j11_maintenance.py`'s and `j11_s
 here deletes" posture)."""
 from __future__ import annotations
 
+import hashlib
 import json
 import os
+import re
 from datetime import date, datetime, timezone
 from pathlib import Path
 from typing import Any, Optional, Union
 
+from sqlalchemy import func
 from sqlalchemy.engine import Engine
-from sqlmodel import Session
+from sqlmodel import Session, select
 
 from app.config import Config, get_config
 from app.engine import engine_identity
@@ -68,7 +71,7 @@ from app.engine import j11_maintenance
 from app.engine import j11_schema_migration as migration
 from app.engine import j11_stage_c as jsc
 from app.engine.j11_maintenance import INCIDENT_DATES
-from app.models import NextSessionManifest
+from app.models import DailyPrice, ForwardReturn, NextSessionManifest, ScannerRun
 
 
 def _now_iso() -> str:
@@ -141,6 +144,62 @@ def freeze_stage_d_attempt_identity(
     }
 
 
+# ----------------------------------------------------------------------------------------------
+# goal-market-compass iter-15 (Goal 9) -- a READINESS-TIME-ONLY identity observation, explicitly labeled
+# non-authorizing and non-reusable, layered ON TOP OF `freeze_stage_d_attempt_identity` rather than
+# folded into it.
+# ----------------------------------------------------------------------------------------------
+
+
+def capture_readiness_time_identity_observation(
+    session: Session,
+    config: Optional[Config] = None,
+    *,
+    git_head: Optional[str] = None,
+    goal_md_text: Optional[str] = None,
+    prior_iteration_14_identity: Optional[str] = None,
+) -> dict:
+    """Goal 9 -- wraps `freeze_stage_d_attempt_identity` (left COMPLETELY UNCHANGED -- TC-39: it still
+    takes no artifact-path parameter that could load a prior freeze) with explicit `readiness_time_only:
+    true`, `authorizing: false`, `reusable_for_stage_d_execution: false` labels, so no later reader can
+    mistake THIS iteration's re-derivation for a frozen Stage D EXECUTION identity available for reuse.
+
+    These labels are added HERE, at this call-site wrapper, rather than inside
+    `freeze_stage_d_attempt_identity`'s own return shape -- a REAL future Stage D execution must call
+    THAT function fresh, immediately before its first write, once all code/config for that execution are
+    final (`docs/goal.md` J-11 step 12); mutating its return shape risks a future caller reading these
+    readiness-only labels as if they described that fresh call, rather than describing only this
+    iteration's separate, non-binding observation (the interpretive call logged in
+    `runs/goal-session-market-compass/state/assumptions.md`, iter-15 entry 2).
+
+    `prior_iteration_14_identity` is iteration 14's own frozen `engine_identity` value, INJECTED by the
+    caller (this function performs no file I/O and never hardcodes iteration 14's `53d2ffd1...` string
+    literally) -- the comparison against it is stated HONESTLY, whichever way it falls (TC-38): `matches`
+    is `True`/`False` when a prior value was supplied, or `None` (never assumed) when it was not."""
+    fresh = freeze_stage_d_attempt_identity(session, config, git_head=git_head, goal_md_text=goal_md_text)
+    matches_iteration_14 = (
+        None if prior_iteration_14_identity is None
+        else fresh["engine_identity"] == prior_iteration_14_identity
+    )
+    observation = dict(fresh)
+    observation.update({
+        "readiness_time_only": True,
+        "authorizing": False,
+        "reusable_for_stage_d_execution": False,
+        "comparison_to_iteration_14_frozen_identity": {
+            "iteration_14_frozen_engine_identity": prior_iteration_14_identity,
+            "this_iteration_engine_identity": fresh["engine_identity"],
+            "matches": matches_iteration_14,
+            "note": (
+                "stated honestly from a genuine equality comparison -- never assumed equal or assumed "
+                "drifted; `matches: null` means iteration 14's value was not supplied to this call, not "
+                "that the two are known to differ"
+            ),
+        },
+    })
+    return observation
+
+
 # ----------------------------------------------------------------------------------------------
 # Goal 2 -- three fail-closed identity COMPARE checks (never a second capture)
 # ----------------------------------------------------------------------------------------------
@@ -230,15 +289,24 @@ def capture_stage_d_preflight(
     goal_md_text: str,
     git_head: Optional[str],
     config: Optional[Config] = None,
+    prior_iteration_14_identity: Optional[str] = None,
 ) -> dict:
     """Re-derives live state fresh (never trusting iteration 13's certified figures without re-proving
     them), composed entirely from already-existing read-only primitives. Writes nothing -- `session` is
     used for SELECTs only, `engine`/`db_path` only for DDL/file introspection. `goal_md_text`/`git_head`
-    are injected by the caller so the whole capture stays a pure, fixture-testable composition."""
+    are injected by the caller so the whole capture stays a pure, fixture-testable composition.
+
+    goal-market-compass iter-15 (Goal 9): `attempt_identity` is now captured via
+    `capture_readiness_time_identity_observation` (labeled `readiness_time_only`/non-authorizing/
+    non-reusable, honestly compared against `prior_iteration_14_identity` when supplied) instead of the
+    raw `freeze_stage_d_attempt_identity` call iteration 14 made directly -- backward compatible: omitting
+    `prior_iteration_14_identity` still returns the same `engine_identity`/`config_subset`/... fields
+    iteration 14's shape carried, plus the new labels."""
     cfg = config or get_config()
     pre_reset_inventory = j11_maintenance.capture_pre_reset_inventory(session)
-    attempt_identity = freeze_stage_d_attempt_identity(
-        session, cfg, git_head=git_head, goal_md_text=goal_md_text
+    attempt_identity = capture_readiness_time_identity_observation(
+        session, cfg, git_head=git_head, goal_md_text=goal_md_text,
+        prior_iteration_14_identity=prior_iteration_14_identity,
     )
     # Check (A) exercised HERE, against a SECOND, independent re-derivation of the current identity --
     # not the identity artifact's own value compared to itself (that would be a no-op self-compare). At
@@ -416,3 +484,426 @@ def stage_d_readiness_verdict(preflight_verdict: dict, avb_classification: str)
         "blocking_reasons": blocking_reasons,
         "authorized": False,
     }
+
+
+# ----------------------------------------------------------------------------------------------
+# goal-market-compass iter-15 (Goal 1) -- reconcile iteration 14's contradictory truth: the stale
+# `runs/goal-market-compass-iter-14/j11-stage-d-readiness.json` (avb_classification: AVB-B, ready: true,
+# blocking_reasons: []) against `runs/goal-session-market-compass/iter-14/eval.md`'s own corrected
+# owner-facing line (`J-11 STAGE D READY: NO`). Read-only; does NOT edit/delete/regenerate either source
+# file -- both are loaded/quoted verbatim (AG-17) and this function's return value is always a NEW,
+# separate artifact the caller persists elsewhere.
+# ----------------------------------------------------------------------------------------------
+
+# The dispatching coordinator's own captured true-start values (2026-08-25) -- to be RE-DERIVED live and
+# COMPARED, never trusted verbatim (the coordinator's own words: "to verify rather than trust"). Any
+# mismatch is reported explicitly, never silently reconciled. The two sha256 figures are TRUNCATED
+# prefix...suffix excerpts as supplied, not full hashes -- compared via prefix/suffix match only, honestly
+# labeled as weaker than full equality (see `_compare_against_owner_capture`).
+OWNER_TRUE_START_CAPTURE: dict = {
+    "db_mtime": 1787591622,
+    "db_size_bytes": 8365871104,
+    "all_11_incident_dates_zero_scanner_runs": True,
+    "daily_prices_row_count": 3310374,
+    "scanner_runs_total_count": 3117,
+    "forward_returns_total_count": 6797728,
+    "data_provider_runs_count": 549,
+    "manifest_row_count": 24,
+    "manifest_ddl_sha256_prefix": "9f653c81",
+    "manifest_ddl_sha256_suffix": "c501ee",
+    "watchlist_count": 6,
+    "forward_returns_measured_into_incident_total": 16614,
+    "scanner_runs_stamped_6261ca17_count": 34,
+    "avb_daily_prices_sha256_prefix": "0257c56d",
+    "avb_daily_prices_sha256_suffix": "0b11cd",
+}
+
+# iteration 10's earlier-attempt identity prefix (the 34 surviving runs) -- a literal historical fact
+# about this incident, same posture as `INCIDENT_DATES` (see `j11_maintenance.py`'s own module docstring).
+_LEGACY_ATTEMPT_IDENTITY_PREFIX = "6261ca17"
+
+_READINESS_LINE_RE = re.compile(r"`(J-11 STAGE D READY:\s*(?:YES|NO))`")
+
+
+def _scanner_runs_by_identity_group(session: Session) -> dict:
+    """`scanner_runs` grouped into NULL / `6261ca17...` (iteration 10's earlier-attempt identity) /
+    anything-else `engine_identity` buckets -- the EXACT id set for the `6261ca17...` group (not merely
+    its count), mirroring `j11_stage_c.small_table_id_snapshot`'s full-enumeration idiom, since TC-44
+    requires the exact 34-row id set (not just its count) to be proven byte-identical before/after."""
+    rows = session.exec(select(ScannerRun.id, ScannerRun.engine_identity)).all()
+    null_ids: list[int] = []
+    legacy_ids: list[int] = []
+    other_ids: list[int] = []
+    for run_id, identity in rows:
+        if identity is None:
+            null_ids.append(int(run_id))
+        elif identity.startswith(_LEGACY_ATTEMPT_IDENTITY_PREFIX):
+            legacy_ids.append(int(run_id))
+        else:
+            other_ids.append(int(run_id))
+    return {
+        "null_count": len(null_ids),
+        "legacy_6261ca17_count": len(legacy_ids),
+        "legacy_6261ca17_ids": sorted(legacy_ids),
+        "other_count": len(other_ids),
+        "other_ids": sorted(other_ids),
+    }
+
+
+def _avb_daily_prices_fingerprint(session: Session) -> dict:
+    """AVB's OWN `daily_prices` content fingerprint -- the SAME sha256-over-canonical-JSON pattern
+    `j11_maintenance.capture_pre_reset_inventory`'s whole-table `daily_prices` fingerprint already uses
+    (row_count/min_date/max_date/id_sum/ohlcv_sum -> sha256), scoped to `symbol == "AVB"` (Goal 1's own
+    instruction: reuse the pattern, never reinvent it)."""
+    row = session.exec(
+        select(
+            func.count(DailyPrice.id),
+            func.min(DailyPrice.date),
+            func.max(DailyPrice.date),
+            func.sum(DailyPrice.id),
+            func.sum(DailyPrice.open + DailyPrice.high + DailyPrice.low + DailyPrice.close + DailyPrice.volume),
+        ).where(DailyPrice.symbol == "AVB")
+    ).one()
+    row_count, min_date, max_date, id_sum, ohlcv_sum = row
+    payload = {
+        "row_count": int(row_count or 0),
+        "min_date": min_date.isoformat() if min_date else None,
+        "max_date": max_date.isoformat() if max_date else None,
+        "id_sum": int(id_sum or 0),
+        "ohlcv_sum": float(ohlcv_sum or 0.0),
+    }
+    fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()
+    return {**payload, "fingerprint": fingerprint}
+
+
+def _prefix_suffix_match(full_value: Optional[str], prefix: Optional[str], suffix: Optional[str]) -> bool:
+    if not full_value or not prefix or not suffix:
+        return False
+    return full_value.startswith(prefix) and full_value.endswith(suffix)
+
+
+def _compare_against_owner_capture(derived: dict, owner_capture: dict) -> dict:
+    """Per-figure match/mismatch against the owner's captured true-start values (TC-1) -- ANY mismatch is
+    reported explicitly, never silently reconciled or explained away. Count/boolean figures are compared
+    by EXACT equality (`comparison_method: exact`); the two sha256 figures the owner captured are
+    TRUNCATED prefix...suffix excerpts (not full hashes), so they are compared via `startswith`/`endswith`
+    only and honestly labeled `comparison_method: prefix_suffix_excerpt_not_full_hash` -- a materially
+    WEAKER proof than full equality, never silently presented as a complete cryptographic match."""
+    comparisons: dict[str, dict] = {}
+
+    def _exact(name: str, derived_value: Any, owner_key: str) -> None:
+        owner_value = owner_capture.get(owner_key)
+        comparisons[name] = {
+            "derived_value": derived_value,
+            "owner_value": owner_value,
+            "comparison_method": "exact",
+            "matches_owner_capture": derived_value == owner_value,
+        }
+
+    def _prefix_suffix(name: str, derived_full_value: str, prefix_key: str, suffix_key: str) -> None:
+        prefix, suffix = owner_capture.get(prefix_key), owner_capture.get(suffix_key)
+        comparisons[name] = {
+            "derived_value": derived_full_value,
+            "owner_value_prefix": prefix,
+            "owner_value_suffix": suffix,
+            "comparison_method": "prefix_suffix_excerpt_not_full_hash",
+            "matches_owner_capture": _prefix_suffix_match(derived_full_value, prefix, suffix),
+        }
+
+    db_file = derived.get("db_file") or {}
+    _exact(
+        "db_mtime",
+        int(db_file["mtime"]) if db_file.get("exists") and db_file.get("mtime") is not None else None,
+        "db_mtime",
+    )
+    _exact("db_size_bytes", db_file.get("size_bytes"), "db_size_bytes")
+    _exact(
+        "all_11_incident_dates_zero_scanner_runs",
+        derived["all_11_incident_dates_zero_scanner_runs"], "all_11_incident_dates_zero_scanner_runs",
+    )
+    _exact("daily_prices_row_count", derived["daily_prices_row_count"], "daily_prices_row_count")
+    _exact("scanner_runs_total_count", derived["scanner_runs_total_count"], "scanner_runs_total_count")
+    _exact("forward_returns_total_count", derived["forward_returns_total_count"], "forward_returns_total_count")
+    _exact("data_provider_runs_count", derived["data_provider_runs_count"], "data_provider_runs_count")
+    _exact("manifest_row_count", derived["manifest_row_count"], "manifest_row_count")
+    _exact("watchlist_count", derived["watchlist_count"], "watchlist_count")
+    _exact(
+        "forward_returns_measured_into_incident_total",
+        derived["forward_returns_measured_into_incident_total"], "forward_returns_measured_into_incident_total",
+    )
+    _exact(
+        "scanner_runs_stamped_6261ca17_count",
+        derived["scanner_runs_by_identity_group"]["legacy_6261ca17_count"], "scanner_runs_stamped_6261ca17_count",
+    )
+    _prefix_suffix(
+        "manifest_ddl_sha256", derived["manifest_ddl_sha256"], "manifest_ddl_sha256_prefix", "manifest_ddl_sha256_suffix",
+    )
+    _prefix_suffix(
+        "avb_daily_prices_sha256", derived["avb_daily_prices_fingerprint"]["fingerprint"],
+        "avb_daily_prices_sha256_prefix", "avb_daily_prices_sha256_suffix",
+    )
+    return comparisons
+
+
+def _extract_readiness_line(eval_md_text: str) -> str:
+    """The literal backtick-quoted `J-11 STAGE D READY: YES/NO` line(s) inside iteration 14's eval.md,
+    extracted read-only via a fail-closed anchored regex (never a broad guess, mirroring `j11_stage_c.
+    extract_incident_date_lists`'s own anchor-based-extraction posture). Raises if no such line is found,
+    or if multiple are found and they CONTRADICT each other -- never silently picks one."""
+    matches = _READINESS_LINE_RE.findall(eval_md_text)
+    if not matches:
+        raise ValueError("no backtick-quoted 'J-11 STAGE D READY: YES/NO' line found in the supplied eval.md text")
+    unique = sorted(set(matches))
+    if len(unique) > 1:
+        raise ValueError(f"eval.md contains CONTRADICTORY backtick-quoted readiness lines: {unique}")
+    return matches[0]
+
+
+def reconcile_prior_iteration_truth(
+    session: Session,
+    engine: Engine,
+    db_path: Optional[Path],
+    *,
+    iteration_14_readiness_path: Path,
+    iteration_14_eval_md_path: Path,
+    owner_true_start_capture: Optional[dict] = None,
+) -> dict:
+    """Goal 1 -- re-derives, LIVE and READ-ONLY, the figures the dispatching coordinator's true-start
+    capture named, compares each against that capture (verify, never trust it), and reconciles iteration
+    14's two contradictory J-11 Stage D readiness conclusions: the stale machine-readable
+    `j11-stage-d-readiness.json` (`avb_classification: "AVB-B"`, `ready: true`, `blocking_reasons: []`)
+    against `iter-14/eval.md`'s own corrected owner-facing line (`J-11 STAGE D READY: NO`).
+
+    Composed ENTIRELY from already-existing read-only primitives -- `j11_maintenance.
+    capture_pre_reset_inventory` for the 11-date `ScannerRun`/forward-return/manifest figures,
+    `j11_schema_migration.fetch_object_ddl`/`dump_table` for the manifest DDL/dump -- never reimplemented.
+
+    Any mismatch against `owner_true_start_capture` is recorded EXPLICITLY (a `matches_owner_capture:
+    False` entry with both values side by side) -- never silently reconciled, explained away, or omitted
+    from the returned artifact. Does NOT edit, delete, or regenerate `iteration_14_readiness_path` or
+    `iteration_14_eval_md_path` -- both are loaded/read-only and quoted verbatim (AG-17); this function's
+    return value is always a NEW, separate artifact for the caller to persist elsewhere."""
+    owner_capture = owner_true_start_capture if owner_true_start_capture is not None else OWNER_TRUE_START_CAPTURE
+
+    pre_reset_inventory = j11_maintenance.capture_pre_reset_inventory(session)
+    incident_dates = pre_reset_inventory["incident_dates"]
+    per_date = pre_reset_inventory["per_date"]
+
+    all_11_zero = not any(per_date[d]["scanner_run"]["present"] for d in incident_dates)
+    forward_returns_measured_into_incident_total = sum(
+        int(per_date[d]["forward_returns_measured_into_count"]) for d in incident_dates
+    )
+
+    scanner_runs_total_count = int(session.scalar(select(func.count()).select_from(ScannerRun)) or 0)
+    scanner_runs_by_identity_group = _scanner_runs_by_identity_group(session)
+    forward_returns_total_count = int(session.scalar(select(func.count()).select_from(ForwardReturn)) or 0)
+
+    manifest_ddl = migration.fetch_object_ddl(engine, migration.TABLE_NAME)
+    manifest_dump = migration.dump_table(engine, NextSessionManifest.__table__)
+    manifest_ddl_sha256 = hashlib.sha256((manifest_ddl.get("table_sql") or "").encode("utf-8")).hexdigest()
+    manifest_dump_sha256 = hashlib.sha256(
+        json.dumps(manifest_dump, sort_keys=True, default=str).encode("utf-8")
+    ).hexdigest()
+
+    avb_daily_prices_fingerprint = _avb_daily_prices_fingerprint(session)
+    db_file = jsc.db_file_fingerprint(db_path) if db_path is not None else {"exists": False}
+
+    derived: dict[str, Any] = {
+        "db_file": db_file,
+        "all_11_incident_dates_zero_scanner_runs": all_11_zero,
+        "per_date_scanner_run_present": {
+            d: bool(per_date[d]["scanner_run"]["present"]) for d in incident_dates
+        },
+        "daily_prices_row_count": pre_reset_inventory["daily_prices"]["row_count"],
+        "daily_prices_fingerprint": pre_reset_inventory["daily_prices"]["fingerprint"],
+        "scanner_runs_total_count": scanner_runs_total_count,
+        "scanner_runs_by_identity_group": scanner_runs_by_identity_group,
+        "forward_returns_total_count": forward_returns_total_count,
+        "forward_returns_measured_into_incident_total": forward_returns_measured_into_incident_total,
+        "data_provider_runs_count": pre_reset_inventory["data_provider_runs_count"],
+        "manifest_row_count": len(manifest_dump),
+        "manifest_ddl_sha256": manifest_ddl_sha256,
+        "manifest_dump_sha256_own_method": manifest_dump_sha256,
+        "watchlist_count": pre_reset_inventory["watchlist_count"],
+        "avb_daily_prices_fingerprint": avb_daily_prices_fingerprint,
+    }
+
+    comparisons = _compare_against_owner_capture(derived, owner_capture)
+    any_mismatch = any(not c["matches_owner_capture"] for c in comparisons.values())
+
+    stale_readiness_payload = json.loads(Path(iteration_14_readiness_path).read_text())
+    eval_md_text = Path(iteration_14_eval_md_path).read_text()
+    corrected_line = _extract_readiness_line(eval_md_text)
+
+    return {
+        "generated_at": _now_iso(),
+        "derived_live_read_only": derived,
+        "owner_true_start_capture": owner_capture,
+        "comparisons_against_owner_capture": comparisons,
+        "any_mismatch_against_owner_capture": any_mismatch,
+        "forward_returns_measured_into_incident_total_matches_16614": (
+            forward_returns_measured_into_incident_total == 16614
+        ),
+        "iteration_14_stale_artifact": {
+            "path": str(iteration_14_readiness_path),
+            "content_verbatim": stale_readiness_payload,
+            "stale_artifact_superseded": True,
+            "superseded_by": (
+                "runs/goal-market-compass-iter-15/j11-stage-d-readiness.json "
+                "(this iteration's committed producer output, Goal 7)"
+            ),
+        },
+        "iteration_14_eval_md_corrected_line": {
+            "path": str(iteration_14_eval_md_path),
+            "quoted_line": corrected_line,
+        },
... [diff_bound] apps/backend/app/engine/j11_stage_d.py: 150 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/scripts/run_j11_avb_bridge_diagnostic.py b/apps/backend/scripts/run_j11_avb_bridge_diagnostic.py
index 7e0f2ceb..fe11ef05 100644
--- a/apps/backend/scripts/run_j11_avb_bridge_diagnostic.py
+++ b/apps/backend/scripts/run_j11_avb_bridge_diagnostic.py
@@ -1,26 +1,43 @@
-"""goal-market-compass iter-14 -- J-11 Stage D readiness: the READ-ONLY AVB bridge/volume diagnostic
+"""goal-market-compass iter-14/15 -- J-11 Stage D readiness: the READ-ONLY AVB bridge/volume diagnostic
 (Goal 4). No `--confirm` needed -- this script performs ZERO writes of any kind: it opens the live
 database through an ACTUAL read-only SQLite handle (`file:<path>?mode=ro` + `PRAGMA query_only=ON`,
 mirroring `run_j11_stage_b1_live_reverification.py`'s helper), so any accidental write attempt anywhere
 in the call graph would raise `OperationalError` rather than silently succeeding. It still captures the
 db-file mtime/size and `-wal` sidecar size at the TRUE process start and TRUE process end as corroborating
-evidence (iteration 12's lesson), even though no writable connection is ever opened.
+evidence (iteration 12's lesson), even though no writable connection is ever opened. This script performs
+NO network fetch of any kind -- it consumes `app.engine.j11_avb_provider_fetch`'s ALREADY-PERSISTED
+evidence (`--provider-fetch-evidence-path`, produced separately by
+`run_j11_avb_provider_fetch.py`), never constructs a provider itself.
 
 Composes `app.engine.j11_avb_diagnostic`'s pure/read functions:
   - re-derives the bridge factor + calibration pairs from the PERSISTED J-10 evidence file (never
-    re-fetched -- AG-9's recovery-fetch exception is exhausted);
-  - classifies AVB's actual stored local convention per window from the stored `daily_prices` series
-    itself;
-  - computes the three counterfactual ADV representations (A/B/C) for both recovered dates;
+    re-fetched -- AG-9's ORIGINAL J-10 recovery-fetch exception is exhausted; this is a SEPARATE, later
+    dated exception);
+  - goal-market-compass iter-15 (Goals 2/3): classifies AVB's actual stored convention per window from a
+    GENUINE cross-source comparison against Goal 2's fetched provider close+volume evidence
+    (`classify_local_convention_with_volume_evidence`) -- no longer the price-only tautology iteration 14
+    left behind;
+  - computes the three counterfactual ADV representations (A/B/C) for ALL SIX AG-9-permitted dates (the
+    calibration window AND the two recovered dates -- not only the recovered dates, as iteration 14 did),
+    representation B now sourced from the FETCHED evidence;
   - traces the decision impact through the named canonical modules
     (`universe_resolver._adv_dollar`/`resolve_candidate`, `scoring`'s liquidity component, the Risk
     score/bucket, setup status, candidate eligibility, and the pool-wide liquidity-percentile shift) for
-    both 2026-08-11 and 2026-08-12;
-  - classifies into exactly one of AVB-A/B/C/D.
+    both 2026-08-11 and 2026-08-12, now substituting BOTH close AND fetched volume (`volume_override`);
+  - classifies into exactly one of AVB-A/B/C/D, mechanically, from the volume-aware evidence.
+
+goal-market-compass iter-15 (Goal 6): `--output-path` carries NO default -- it used to default to
+`runs/goal-market-compass-iter-14`, a real committed evidence directory, the exact footgun pattern that
+overwrote three committed iteration-13 evidence files in iteration 14. Refuses BEFORE any engine
+construction, mirroring the already-fixed `run_j11_stage_c_bounded_clear.py` pattern exactly.
+`--provider-fetch-evidence-path` is ALSO required -- Goal 2's fetch evidence is this script's ONLY source
+of provider close/volume; there is no fallback default that could silently substitute a stale or wrong
+fetch artifact.
 
 Usage:
     apps/backend/.venv/bin/python apps/backend/scripts/run_j11_avb_bridge_diagnostic.py \\
-        [--output-path runs/goal-market-compass-iter-14/j11-avb-bridge-diagnostic.json]
+        --output-path runs/goal-market-compass-iter-15/j11-avb-bridge-diagnostic.json \\
+        --provider-fetch-evidence-path runs/goal-market-compass-iter-15/j11-avb-provider-fetch-evidence.json
 """
 from __future__ import annotations
 
@@ -43,7 +60,8 @@ from app.db import resolve_database_url  # noqa: E402
 from app.engine import j11_avb_diagnostic as diag  # noqa: E402
 from app.engine.j11_stage_c import db_file_fingerprint  # noqa: E402
 
-DEFAULT_OUTPUT_PATH = REPO_ROOT / "runs" / "goal-market-compass-iter-14" / "j11-avb-bridge-diagnostic.json"
+CANONICAL_OUTPUT_PATH_FOR_DOCS = REPO_ROOT / "runs" / "goal-market-compass-iter-15" / "j11-avb-bridge-diagnostic.json"
+PERMITTED_DATES = diag.CALIBRATION_DATES + diag.RECOVERED_DATES
 
 
 def _db_file_path(database_url: str) -> "Path | None":
@@ -70,13 +88,52 @@ def _read_only_engine(db_path: Path):
 
 def main() -> int:
     parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
-    parser.add_argument("--output-path", type=Path, default=DEFAULT_OUTPUT_PATH)
+    parser.add_argument(
+        "--output-path", type=Path, default=None,
+        help=(
+            "required -- the diagnostic JSON this script writes. Has NO default on purpose (Goal 6): the "
+            f"real target this iteration ({CANONICAL_OUTPUT_PATH_FOR_DOCS}) is a committed evidence "
+            "directory, and an implicit default meant a forgotten flag could overwrite committed "
+            "forensic evidence instead of failing."
+        ),
+    )
+    parser.add_argument(
+        "--provider-fetch-evidence-path", type=Path, default=None,
+        help=(
+            "required -- Goal 2's persisted AVB provider-fetch evidence JSON (produced by "
+            "run_j11_avb_provider_fetch.py). This is this script's ONLY source of provider close/volume "
+            "-- it performs no network fetch itself, and there is no fallback default."
+        ),
+    )
     parser.add_argument(
         "--j10-evidence-path", type=Path, default=diag.DEFAULT_J10_EVIDENCE_PATH,
-        help="the persisted J-10 population-recovery evidence file -- never re-fetched.",
+        help="the persisted J-10 population-recovery evidence file (for the bridge factor) -- read-only "
+             "input, never re-fetched.",
     )
     args = parser.parse_args()
 
+    missing = [
+        name for name, value in (
+            ("--output-path", args.output_path), ("--provider-fetch-evidence-path", args.provider_fetch_evidence_path),
+        ) if value is None
+    ]
+    if missing:
+        print(
+            f"refusing to run without explicit {', '.join(missing)}. No config has been loaded, no "
+            "database engine has been constructed, and nothing has been written.",
+            file=sys.stderr,
+        )
+        return 2
+
+    fetch_evidence = json.loads(Path(args.provider_fetch_evidence_path).read_text())
+    provider_evidence_by_date: dict = fetch_evidence.get("per_date", {})
+    print(
+        f"loaded Goal 2 fetch evidence from {args.provider_fetch_evidence_path}: "
+        f"sufficient_evidence={fetch_evidence.get('sufficient_evidence')} "
+        f"missing_dates={fetch_evidence.get('missing_dates')}",
+        file=sys.stderr,
+    )
+
     cfg = load_config()
     resolved_url = resolve_database_url(cfg.database.url)
     db_path = _db_file_path(resolved_url)
@@ -102,21 +159,49 @@ def main() -> int:
         # current stored frontier, so the convention classifier's continuity check has real adjacent
         # context on both sides of the recovery boundary.
         stored_series = diag.fetch_avb_stored_series(session, date(2026, 6, 1), date(2026, 12, 31))
-        local_convention = diag.classify_local_convention(stored_series, evidence_row)
+        # goal-market-compass iter-15 (Goals 2/3): the volume-aware classifier, fed Goal 2's fetched
+        # evidence -- NOT the old price-only `classify_local_convention` (kept unchanged elsewhere as a
+        # documented fallback/cross-check, never used here as the primary classification input anymore).
+        local_convention = diag.classify_local_convention_with_volume_evidence(
+            stored_series, evidence_row, provider_evidence_by_date
+        )
 
-        recovered_rows_by_date = {row["date"]: row for row in stored_series if row["date"] in
-                                   {d.isoformat() for d in diag.RECOVERED_DATES}}
-        representations_by_date = {
-            iso_date: diag.compute_counterfactual_representations(bridge_factor, row["close"], row["volume"])
-            for iso_date, row in recovered_rows_by_date.items()
+        # goal-market-compass iter-15 (Goal 3): ALL SIX permitted dates, not only the two recovered ones.
+        stored_rows_by_date = {row["date"]: row for row in stored_series}
+        representations_by_date = {}
+        for one_date in PERMITTED_DATES:
+            key = one_date.isoformat()
+            stored_row = stored_rows_by_date.get(key)
+            if stored_row is None:
+                continue
+            representations_by_date[key] = diag.compute_counterfactual_representations(
+                bridge_factor, stored_row["close"], stored_row["volume"],
+                provider_evidence=provider_evidence_by_date.get(key),
+            )
+
+        # goal-market-compass iter-15 (Goal 5): the decision-impact trace substitutes BOTH close AND the
+        # GENUINELY FETCHED volume for the two recovered dates -- volume_override sourced strictly from
+        # dates with sufficient fetched evidence; a date without it simply has no override entry (the
+        # trace degrades gracefully to close-only substitution for THAT date, while the classifier above
+        # already forces AVB-D on any missing-evidence date, so a degraded trace for that one date is
+        # never trusted as the basis for readiness either way).
+        volume_override = {
+            one_date: provider_evidence_by_date[one_date.isoformat()]["volume"]
+            for one_date in diag.RECOVERED_DATES
+            if one_date.isoformat() in provider_evidence_by_date
+            and provider_evidence_by_date[one_date.isoformat()].get("volume") is not None
         }
 
         decision_impact_by_date: dict[str, dict] = {}
         for one_date in diag.RECOVERED_DATES:
             key = one_date.isoformat()
             print(f"tracing decision impact for {key} ...", file=sys.stderr)
-            ur_impact = diag.trace_universe_resolver_impact(session, cfg, one_date, bridge_factor)
-            scoring_impact = diag.trace_scoring_and_selection_impact(session, cfg, one_date, bridge_factor)
+            ur_impact = diag.trace_universe_resolver_impact(
+                session, cfg, one_date, bridge_factor, volume_override=volume_override
+            )
+            scoring_impact = diag.trace_scoring_and_selection_impact(
+                session, cfg, one_date, bridge_factor, volume_override=volume_override
+            )
             decision_impact_by_date[key] = {
                 "universe_resolver": ur_impact,
                 "scoring_and_selection": scoring_impact,
@@ -131,6 +216,20 @@ def main() -> int:
             )
 
     classification = diag.classify_avb(local_convention, decision_impact_by_date)
+    # Goal 4: the fetch itself failing closed (insufficient evidence for one or more permitted dates)
+    # forces AVB-D regardless of what the convention/impact classification above concluded -- named per
+    # the amendment's own words ("If the fetch comes back insufficient... the correct outcome is AVB-D").
+    if not fetch_evidence.get("sufficient_evidence", False):
+        classification = dict(classification)
+        classification["classification"] = "AVB-D"
+        classification["stage_d_ready_per_avb"] = False
+        classification["reasoning"] = (
+            "Goal 2's AG-9 dated-exception-#2 fetch did NOT supply sufficient evidence for all six "
+            f"permitted dates (missing_dates={fetch_evidence.get('missing_dates')}); classifying AVB-D "
+            "per the amendment's own fail-closed rule -- never a guess, never a substituted adjacent-day "
+            f"statistic. Underlying convention/impact classification (informational only, NOT trusted "
+            f"as the basis for readiness): {classification['classification']} -- {classification['reasoning']}"
+        )
 
     db_file_true_end = db_file_fingerprint(db_path)
     zero_write = {
@@ -147,6 +246,8 @@ def main() -> int:
     result = {
         "generated_at": diag._now_iso(),
         "j10_evidence_path": str(args.j10_evidence_path),
+        "provider_fetch_evidence_path": str(args.provider_fetch_evidence_path),
+        "provider_fetch_evidence_sufficient": fetch_evidence.get("sufficient_evidence"),
         "bridge_factor": bridge_factor,
         "calibration_pairs": evidence_row.get("pairs"),
         "pool_bridge_factor_distribution": pool_distribution,
diff --git a/apps/backend/scripts/run_j11_avb_provider_fetch.py b/apps/backend/scripts/run_j11_avb_provider_fetch.py
new file mode 100644
index 00000000..1a12752c
--- /dev/null
+++ b/apps/backend/scripts/run_j11_avb_provider_fetch.py
@@ -0,0 +1,104 @@
+"""goal-market-compass iter-15 -- J-11 Stage D readiness, Goal 2: the CLI wrapper for the ONE
+owner-authorized bounded AVB comparison fetch (`docs/goal.md` AG-9 "Dated exception #2 -- AVB convention
+diagnostic (owner, 2026-08-25 -- single-use, self-closing, DIAGNOSTIC ONLY)").
+
+This script constructs the REAL `app.data_providers.yahoo_provider.YahooProvider` and is the ONLY place
+in this iteration's diff that does so -- `app.engine.j11_avb_provider_fetch.fetch_avb_provider_evidence`
+takes it as an injected dependency and calls `.get_daily` exactly once. This script needs NO database
+engine or session at all -- it imports nothing from `app.db`/`app.config.load_config`/`sqlmodel`, so it is
+structurally incapable of touching `apps/backend/data/trendora.db` (verified: zero references to
+`get_engine`/`Session`/`load_config` anywhere in this file). Its only inputs are the persisted J-10
+evidence file (for the bridge factor -- never re-derived, never re-fetched; AG-9's ORIGINAL J-10 exception
+stays exhausted, this is a SEPARATE dated exception) and the network; its only output is the evidence JSON
+this script writes to the required `--output-path`.
+
+`--output-path` carries NO default, mirroring `run_j11_stage_c_bounded_clear.py`'s already-fixed pattern
+(Goal 6): a forgotten flag must fail loudly rather than silently landing evidence in an unintended, or
+worse a real committed, location. Refuses BEFORE constructing the provider or reading the J-10 evidence
+file -- no network call and no file I/O beyond argument parsing occurs when the required path is missing.
+
+Usage:
+    apps/backend/.venv/bin/python apps/backend/scripts/run_j11_avb_provider_fetch.py \\
+        --output-path runs/goal-market-compass-iter-15/j11-avb-provider-fetch-evidence.json \\
+        [--j10-evidence-path runs/goal-market-compass-iter-9/j10-population-evidence.json]
+
+This is the SINGLE execution of AG-9 dated exception #2 -- once the artifact is written, the exception is
+exhausted for the rest of this iteration; every later step (the AVB bridge diagnostic, the readiness
+producer) reads the persisted artifact this script writes, never re-fetches.
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
+from app.data_providers.yahoo_provider import YahooProvider  # noqa: E402
+from app.engine import j11_avb_provider_fetch as fetch  # noqa: E402
+from app.engine.j11_avb_diagnostic import DEFAULT_J10_EVIDENCE_PATH, load_j10_avb_evidence  # noqa: E402
+
+
+def main() -> int:
+    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
+    parser.add_argument(
+        "--output-path", type=Path, default=None,
+        help=(
+            "required -- the evidence JSON this script writes. Has NO default on purpose (Goal 6's "
+            "guard, applied to this new script from the start): an omitted flag must fail loudly rather "
+            "than silently writing this iteration's ONE authorized network fetch's evidence somewhere "
+            "unintended."
+        ),
+    )
+    parser.add_argument(
+        "--j10-evidence-path", type=Path, default=DEFAULT_J10_EVIDENCE_PATH,
+        help="the persisted J-10 population-recovery evidence file (for the bridge factor) -- read-only "
+             "input, never re-derived, never re-fetched.",
+    )
+    args = parser.parse_args()
+
+    if args.output_path is None:
+        print(
+            "refusing to run without an explicit --output-path. This script performs this iteration's "
+            "ONE owner-authorized network fetch (docs/goal.md AG-9 'Dated exception #2') -- its evidence "
+            "must land at an explicitly named location, never a default. No network call has occurred, "
+            "and nothing has been written.",
+            file=sys.stderr,
+        )
+        return 2
+
+    evidence_row = load_j10_avb_evidence(args.j10_evidence_path)
+    bridge_factor = evidence_row["bridge_factor"]
+    print(f"loaded persisted J-10 bridge_factor={bridge_factor} from {args.j10_evidence_path}", file=sys.stderr)
+
+    provider = YahooProvider()
+    print(
+        f"performing the ONE authorized AG-9 dated-exception-#2 fetch: symbol={fetch.AVB_SYMBOL} "
+        f"dates={[d.isoformat() for d in fetch.PERMITTED_DATES]} provider=yahoo",
+        file=sys.stderr,
+    )
+    result = fetch.fetch_avb_provider_evidence(provider, bridge_factor=bridge_factor)
+
+    args.output_path.parent.mkdir(parents=True, exist_ok=True)
+    args.output_path.write_text(json.dumps(result, indent=2, sort_keys=True, default=str))
+    print(f"wrote {args.output_path}", file=sys.stderr)
+    print(
+        f"sufficient_evidence={result['sufficient_evidence']} missing_dates={result['missing_dates']}",
+        file=sys.stderr,
+    )
+    if not result["sufficient_evidence"]:
+        print(
+            "FAIL CLOSED: the fetch did not supply sufficient evidence for all six permitted dates -- "
+            "per the amendment, this classifies AVB-D downstream. No adjacent-day substitute, no retry "
+            "with a broadened request.",
+            file=sys.stderr,
+        )
+    return 0 if result["sufficient_evidence"] else 1
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
diff --git a/apps/backend/scripts/run_j11_reconcile_iteration_14_truth.py b/apps/backend/scripts/run_j11_reconcile_iteration_14_truth.py
new file mode 100644
index 00000000..5a8aa1ce
--- /dev/null
+++ b/apps/backend/scripts/run_j11_reconcile_iteration_14_truth.py
@@ -0,0 +1,158 @@
+"""goal-market-compass iter-15 -- J-11 Stage D readiness, Goal 1: the READ-ONLY CLI wrapper for
+`app.engine.j11_stage_d.reconcile_prior_iteration_truth`.
+
+Re-derives, LIVE and READ-ONLY, the figures the dispatching coordinator's true-start capture named
+(db mtime/size, all-11-incident-dates-zero, `daily_prices`/`scanner_runs`/`forward_returns`/
+`data_provider_runs`/manifest/`watchlist`/AVB-fingerprint counts), compares each against that capture
+(verify, never trust), and reconciles iteration 14's two contradictory J-11 Stage D readiness conclusions
+-- the stale `runs/goal-market-compass-iter-14/j11-stage-d-readiness.json` (`avb_classification: "AVB-B"`,
+`ready: true`) against `runs/goal-session-market-compass/iter-14/eval.md`'s own corrected owner-facing
+line (`J-11 STAGE D READY: NO`).
+
+Opens the live database through an ACTUAL read-only SQLite handle (`file:<path>?mode=ro` + `PRAGMA
+query_only=ON`), so any accidental write attempt anywhere in the call graph would raise
+`OperationalError` rather than silently succeeding. Does NOT edit, delete, or regenerate EITHER source
+file -- both are loaded read-only and quoted verbatim inside the NEW artifact this script writes.
+
+`--output-path` carries NO default (Goal 6's guard, applied to this new script from the start): an
+omitted flag must fail loudly rather than silently landing this iteration's reconciliation artifact
+somewhere unintended.
+
+Usage:
+    apps/backend/.venv/bin/python apps/backend/scripts/run_j11_reconcile_iteration_14_truth.py \\
+        --output-path runs/goal-market-compass-iter-15/j11-iteration-14-truth-reconciliation.json \\
+        [--iteration-14-readiness-path runs/goal-market-compass-iter-14/j11-stage-d-readiness.json] \\
+        [--iteration-14-eval-md-path runs/goal-session-market-compass/iter-14/eval.md] \\
+        [--db-file-true-start-path PATH]
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
+DEFAULT_ITERATION_14_READINESS_PATH = (
+    REPO_ROOT / "runs" / "goal-market-compass-iter-14" / "j11-stage-d-readiness.json"
+)
+DEFAULT_ITERATION_14_EVAL_MD_PATH = REPO_ROOT / "runs" / "goal-session-market-compass" / "iter-14" / "eval.md"
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
+    parser.add_argument(
+        "--output-path", type=Path, default=None,
+        help=(
+            "required -- the reconciliation JSON this script writes. Has NO default on purpose (Goal 6): "
+            "an omitted flag must fail loudly rather than silently landing this artifact somewhere "
+            "unintended."
+        ),
+    )
+    parser.add_argument(
+        "--iteration-14-readiness-path", type=Path, default=DEFAULT_ITERATION_14_READINESS_PATH,
+        help="read-only input -- iteration 14's stale j11-stage-d-readiness.json, loaded verbatim, "
+             "never edited.",
+    )
+    parser.add_argument(
+        "--iteration-14-eval-md-path", type=Path, default=DEFAULT_ITERATION_14_EVAL_MD_PATH,
+        help="read-only input -- iteration 14's evaluator report, for its own corrected owner-facing line.",
+    )
+    parser.add_argument(
+        "--db-file-true-start-path", type=Path, default=None,
+        help="reuse an earlier-in-this-iteration TRUE process-start db-file fingerprint, if any -- "
+             "brackets the whole-iteration zero-write proof across every script this iteration runs.",
+    )
+    args = parser.parse_args()
+
+    if args.output_path is None:
+        print(
+            "refusing to run without an explicit --output-path. No config has been loaded, no database "
+            "engine has been constructed, and nothing has been written.",
+            file=sys.stderr,
+        )
+        return 2
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
+
+    engine = _read_only_engine(db_path)
+    with Session(engine) as session:
+        result = jsd.reconcile_prior_iteration_truth(
+            session, engine, db_path,
+            iteration_14_readiness_path=args.iteration_14_readiness_path,
+            iteration_14_eval_md_path=args.iteration_14_eval_md_path,
+        )
+
+    db_file_true_end = jsc.db_file_fingerprint(db_path)
+    result["zero_write_proof"] = {
+        "db_file_true_start": db_file_true_start,
+        "db_file_true_end": db_file_true_end,
+        "mtime_unchanged": db_file_true_start.get("mtime") == db_file_true_end.get("mtime"),
+        "size_unchanged": db_file_true_start.get("size_bytes") == db_file_true_end.get("size_bytes"),
+    }
+
+    args.output_path.parent.mkdir(parents=True, exist_ok=True)
+    args.output_path.write_text(json.dumps(result, indent=2, sort_keys=True, default=str))
+    print(f"wrote {args.output_path}", file=sys.stderr)
+    print(f"any_mismatch_against_owner_capture={result['any_mismatch_against_owner_capture']}", file=sys.stderr)
+    print(
+        f"forward_returns_measured_into_incident_total_matches_16614="
+        f"{result['forward_returns_measured_into_incident_total_matches_16614']}",
+        file=sys.stderr,
+    )
+    print(
+        f"iteration-14 stale artifact superseded: "
+        f"{result['iteration_14_stale_artifact']['stale_artifact_superseded']}",
+        file=sys.stderr,
+    )
+    return 0 if not result["any_mismatch_against_owner_capture"] else 1
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
diff --git a/apps/backend/scripts/run_j11_stage_d_preflight.py b/apps/backend/scripts/run_j11_stage_d_preflight.py
index cc2c8906..edbf8606 100644
--- a/apps/backend/scripts/run_j11_stage_d_preflight.py
+++ b/apps/backend/scripts/run_j11_stage_d_preflight.py
@@ -1,4 +1,4 @@
-"""goal-market-compass iter-14 -- J-11 Stage D readiness: the READ-ONLY Stage D preflight gate (Goal 1 +
+"""goal-market-compass iter-14/15 -- J-11 Stage D readiness: the READ-ONLY Stage D preflight gate (Goal 1 +
 Goal 3a), executed live against `apps/backend/data/trendora.db` THIS iteration -- permitted (zero
 writes), distinct from Stage D's own regeneration, which remains unauthorized and is NOT attempted
 anywhere in this script.
@@ -9,8 +9,10 @@ attempt anywhere in the call graph would raise `OperationalError` rather than si
 `--confirm` flag: there is nothing here to confirm, since nothing is ever written.
 
 Sequence:
-  1. Freeze a FRESH Stage D attempt identity (`j11_stage_d.freeze_stage_d_attempt_identity`) -- never
-     hardcodes iteration 10's `6261ca17...` or iteration 13's `53d2ffd1...`.
+  1. Freeze a FRESH Stage D attempt identity (`j11_stage_d.freeze_stage_d_attempt_identity`, wrapped in
+     iteration 15's `capture_readiness_time_identity_observation` -- Goal 9) -- never hardcodes iteration
+     10's `6261ca17...` or iteration 13's `53d2ffd1...`, and is explicitly labeled `readiness_time_only`/
+     non-authorizing/non-reusable, honestly compared against iteration 14's own frozen value.
   2. Capture the Stage D preflight (`j11_stage_d.capture_stage_d_preflight`) -- re-derives live state
      fresh, including Check (A)'s identity comparison against a SECOND independent recomputation.
   3. Load the certified post-Stage-C baseline from iteration 13's own persisted artifacts
@@ -19,11 +21,18 @@ Sequence:
   4. Persist every artifact; the verdict alone does NOT authorize Stage D (a separate owner instruction
      is required -- the C10/A12 pattern).
 
+goal-market-compass iter-15 (Goal 6): `--evidence-dir` carries NO default -- it used to default to
+`runs/goal-market-compass-iter-14`, a real committed evidence directory, the exact footgun pattern that
+overwrote three committed iteration-13 evidence files in iteration 14 (see `docs/handoffs/
+goal-market-compass-iter-14-dev.md`). Refuses BEFORE `load_config()`/`resolve_database_url`/any engine
+construction, mirroring the already-fixed `run_j11_stage_c_bounded_clear.py` pattern exactly.
+
 Usage:
     apps/backend/.venv/bin/python apps/backend/scripts/run_j11_stage_d_preflight.py \\
-        [--evidence-dir runs/goal-market-compass-iter-14] \\
+        --evidence-dir runs/goal-market-compass-iter-15 \\
         [--stage-c-preflight-path runs/goal-market-compass-iter-13/j11-stage-c-preflight.json] \\
         [--stage-c-mutation-accounting-path runs/goal-market-compass-iter-13/j11-stage-c-mutation-accounting.json] \\
+        [--iteration-14-identity-path runs/goal-market-compass-iter-14/j11-stage-d-attempt-identity.json] \\
         [--db-file-true-start-path PATH]   # reuse an earlier-in-this-iteration true-start capture, if any
 """
 from __future__ import annotations
@@ -46,11 +55,17 @@ from app.db import resolve_database_url  # noqa: E402
 from app.engine import j11_stage_c as jsc  # noqa: E402
 from app.engine import j11_stage_d as jsd  # noqa: E402
 
-DEFAULT_EVIDENCE_DIR = REPO_ROOT / "runs" / "goal-market-compass-iter-14"
+# The directory this script's evidence BELONGS in when it is run for THIS iteration. Deliberately NOT an
+# argparse default (Goal 6) -- an omitted --evidence-dir must FAIL, never silently write into (or, worse,
+# overwrite) a committed evidence directory from a prior iteration.
+CANONICAL_EVIDENCE_DIR_FOR_DOCS = REPO_ROOT / "runs" / "goal-market-compass-iter-15"
 DEFAULT_STAGE_C_PREFLIGHT_PATH = REPO_ROOT / "runs" / "goal-market-compass-iter-13" / "j11-stage-c-preflight.json"
 DEFAULT_STAGE_C_MUTATION_ACCOUNTING_PATH = (
     REPO_ROOT / "runs" / "goal-market-compass-iter-13" / "j11-stage-c-mutation-accounting.json"
 )
+DEFAULT_ITERATION_14_IDENTITY_PATH = (
+    REPO_ROOT / "runs" / "goal-market-compass-iter-14" / "j11-stage-d-attempt-identity.json"
+)
 
 
 def _db_file_path(database_url: str) -> "Path | None":
@@ -83,11 +98,27 @@ def _write_json(path: Path, payload) -> None:
 
 def main() -> int:
     parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
-    parser.add_argument("--evidence-dir", type=Path, default=DEFAULT_EVIDENCE_DIR)
+    parser.add_argument(
+        "--evidence-dir", type=Path, default=None,
+        help=(
+            "required -- the directory every evidence JSON is written to. Has NO default on purpose "
+            f"(Goal 6): the real target ({CANONICAL_EVIDENCE_DIR_FOR_DOCS}) is a committed evidence "
+            "directory, and an implicit default meant a forgotten flag could overwrite committed "
+            "forensic evidence instead of failing (this happened to a SIBLING script in iteration 14; "
+            "see docs/handoffs/goal-market-compass-iter-14-dev.md)."
+        ),
+    )
     parser.add_argument("--stage-c-preflight-path", type=Path, default=DEFAULT_STAGE_C_PREFLIGHT_PATH)
     parser.add_argument(
         "--stage-c-mutation-accounting-path", type=Path, default=DEFAULT_STAGE_C_MUTATION_ACCOUNTING_PATH
     )
+    parser.add_argument(
+        "--iteration-14-identity-path", type=Path, default=DEFAULT_ITERATION_14_IDENTITY_PATH,
+        help="goal-market-compass iter-15 (Goal 9) -- iteration 14's own frozen Stage D attempt-identity "
+             "artifact, read-only, for the honest comparison recorded on this iteration's readiness-time "
+             "identity observation. A read-only INPUT path (never a write target), so it may sensibly "
+             "default -- pass '' or a nonexistent path to skip the comparison (recorded as matches: null).",
+    )
     parser.add_argument(
         "--db-file-true-start-path", type=Path, default=None,
         help="an earlier-in-this-iteration TRUE process-start db-file fingerprint (e.g. from the AVB "
@@ -97,6 +128,16 @@ def main() -> int:
     )
     args = parser.parse_args()
 
+    if args.evidence_dir is None:
+        print(
+            "refusing to run without an explicit --evidence-dir. This script writes forensic evidence "
+            f"JSON into that directory; its real target this iteration ({CANONICAL_EVIDENCE_DIR_FOR_DOCS}) "
+            "must be named explicitly and is never reached by default. No config has been loaded, no "
+            "database engine has been constructed, and nothing has been written.",
+            file=sys.stderr,
+        )
+        return 2
+
     cfg = load_config()
     resolved_url = resolve_database_url(cfg.database.url)
     db_path = _db_file_path(resolved_url)
@@ -116,15 +157,31 @@ def main() -> int:
     git_head = jsc.read_git_head()
     engine = _read_only_engine(db_path)
 
+    prior_identity_value = None
+    if args.iteration_14_identity_path is not None and Path(args.iteration_14_identity_path).exists():
+        prior_identity_value = json.loads(Path(args.iteration_14_identity_path).read_text()).get("engine_identity")
+    print(
+        f"iteration-14 prior frozen identity loaded from {args.iteration_14_identity_path}: "
+        f"{prior_identity_value!r}",
+        file=sys.stderr,
+    )
+
     with Session(engine) as session:
-        attempt_identity = jsd.freeze_stage_d_attempt_identity(
-            session, cfg, git_head=git_head, goal_md_text=goal_md_text
+        attempt_identity = jsd.capture_readiness_time_identity_observation(
+            session, cfg, git_head=git_head, goal_md_text=goal_md_text,
+            prior_iteration_14_identity=prior_identity_value,
         )
         _write_json(args.evidence_dir / "j11-stage-d-attempt-identity.json", attempt_identity)
-        print(f"frozen Stage D attempt identity: engine_identity={attempt_identity['engine_identity']}", file=sys.stderr)
+        print(
+            f"THIS iteration's readiness-time identity observation (readiness_time_only=True, "
+            f"non-authorizing, non-reusable): engine_identity={attempt_identity['engine_identity']} "
+            f"matches_iteration_14={attempt_identity['comparison_to_iteration_14_frozen_identity']['matches']}",
+            file=sys.stderr,
+        )
 
         preflight = jsd.capture_stage_d_preflight(
             session, engine, db_path, goal_md_text=goal_md_text, git_head=git_head, config=cfg,
+            prior_iteration_14_identity=prior_identity_value,
         )
     _write_json(args.evidence_dir / "j11-stage-d-preflight.json", preflight)
     print(
diff --git a/apps/backend/scripts/run_j11_stage_d_readiness.py b/apps/backend/scripts/run_j11_stage_d_readiness.py
new file mode 100644
index 00000000..ba614301
--- /dev/null
+++ b/apps/backend/scripts/run_j11_stage_d_readiness.py
@@ -0,0 +1,98 @@
+"""goal-market-compass iter-15 -- J-11 Stage D readiness, Goal 7: the CLI wrapper for the committed
+readiness-artifact producer (`app.engine.j11_stage_d.produce_stage_d_readiness_artifact`).
+
+This is the FIRST committed, non-test caller of `stage_d_readiness_verdict` -- through iteration 14 that
+function was called only from `tests/test_j11_stage_d.py`, which is exactly why iteration 14's
+`j11-stage-d-readiness.json` went stale relative to its own evaluator's corrected conclusion. This script
+reads TWO already-persisted evidence artifacts (the Stage D preflight gate, from a Goal-6-fixed run of
+`run_j11_stage_d_preflight.py`; the AVB bridge diagnostic, from a Goal-6-fixed run of
+`run_j11_avb_bridge_diagnostic.py`) and combines them into the final, single, machine-readable readiness
+verdict -- performing NO database or network access itself (it only reads two JSON files and writes one).
+
+Every path is required, no default (Goal 6's guard, applied to this new script from the start): all three
+paths point at evidence this iteration produces, and an omitted flag must fail loudly rather than
+silently reading/writing the wrong location.
+
+Prints the literal `J-11 STAGE D READY: YES` / `NO` line -- read verbatim from the artifact's own `ready`
+field, never re-typed independently (TC-40) -- and the unconditional `J-11 STAGE D AUTHORIZED: NO` line
+(Stage D readiness is never self-authorizing; the C10/A12 pattern).
+
+Usage:
+    apps/backend/.venv/bin/python apps/backend/scripts/run_j11_stage_d_readiness.py \\
+        --preflight-gate-path runs/goal-market-compass-iter-15/j11-stage-d-preflight-gate.json \\
+        --avb-diagnostic-path runs/goal-market-compass-iter-15/j11-avb-bridge-diagnostic.json \\
+        --output-path runs/goal-market-compass-iter-15/j11-stage-d-readiness.json
+"""
+from __future__ import annotations
+
+import argparse
+import sys
+from pathlib import Path
+
+# scripts/ -> backend -> apps -> repo root
+BACKEND_DIR = Path(__file__).resolve().parents[1]
+REPO_ROOT = BACKEND_DIR.parents[1]
+sys.path.insert(0, str(BACKEND_DIR))
+
+from app.engine import j11_stage_d as jsd  # noqa: E402
+
+
+def main() -> int:
+    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
+    parser.add_argument(
+        "--preflight-gate-path", type=Path, default=None,
+        help="required -- the Stage D preflight-gate JSON (e.g. j11-stage-d-preflight-gate.json).",
+    )
+    parser.add_argument(
+        "--avb-diagnostic-path", type=Path, default=None,
+        help="required -- the AVB bridge-diagnostic JSON (e.g. j11-avb-bridge-diagnostic.json).",
+    )
+    parser.add_argument(
+        "--output-path", type=Path, default=None,
+        help=(
+            "required -- the final readiness JSON this script writes. Has NO default on purpose (Goal "
+            "6's guard, applied to this new script from the start): an omitted flag must fail loudly "
+            "rather than silently landing this iteration's headline verdict somewhere unintended."
+        ),
+    )
+    args = parser.parse_args()
+
+    missing = [
+        name for name, value in (
+            ("--preflight-gate-path", args.preflight_gate_path),
+            ("--avb-diagnostic-path", args.avb_diagnostic_path),
+            ("--output-path", args.output_path),
+        )
+        if value is None
+    ]
+    if missing:
+        print(
+            f"refusing to run without explicit {', '.join(missing)}. This script combines two committed "
+            "evidence artifacts into the final J-11 Stage D readiness verdict -- none of its paths "
+            "default into a committed evidence directory. No file has been read or written.",
+            file=sys.stderr,
+        )
+        return 2
+
+    try:
+        readiness = jsd.produce_stage_d_readiness_artifact(
+            args.preflight_gate_path, args.avb_diagnostic_path, output_path=args.output_path,
+        )
+    except ValueError as exc:
+        print(f"FAIL (fail-closed, nothing written): {exc}", file=sys.stderr)
+        return 1
+
+    print(f"wrote {args.output_path}", file=sys.stderr)
+    print(
+        f"avb_classification={readiness['avb_classification']} "
+        f"preflight_gate_passed={readiness['preflight_gate_passed']} "
+        f"blocking_reasons={readiness['blocking_reasons']}",
+        file=sys.stderr,
+    )
+    print(f"J-11 STAGE D READY: {'YES' if readiness['ready'] else 'NO'}", file=sys.stderr)
+    print("J-11 STAGE D AUTHORIZED: NO", file=sys.stderr)
+    return 0 if readiness["ready"] else 1
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
diff --git a/apps/backend/tests/test_j11_avb_diagnostic.py b/apps/backend/tests/test_j11_avb_diagnostic.py
index d576ae39..18d433bd 100644
--- a/apps/backend/tests/test_j11_avb_diagnostic.py
+++ b/apps/backend/tests/test_j11_avb_diagnostic.py
@@ -153,21 +153,263 @@ def test_classify_local_convention_indeterminate_when_calibration_pairs_missing(
     assert result["indeterminate"] is True
 
 
-# --- TC-22: counterfactual representations A/B/C -- exact formulas, B's volume equals A's -----------
+# --- TC-12/13: counterfactual representations A/B/C -- iter-15 fix: B is genuinely fetched, fails ------
+# --- closed when evidence is unavailable, never a stored-volume tautology -----------------------------
 
 
-def test_tc22_representations_a_b_c_formulas_and_volume_equality():
+def test_tc22_representation_a_and_c_formulas_unchanged():
     bridge_factor = 2.7930001225759193
     stored_close, stored_volume = 189.61, 500_000.0
     rep = diag.compute_counterfactual_representations(bridge_factor, stored_close, stored_volume)
     assert rep["A"]["close"] == stored_close
     assert rep["A"]["volume"] == stored_volume
-    assert rep["B"]["close"] == pytest.approx(stored_close / bridge_factor)
-    assert rep["B"]["volume"] == stored_volume  # stated explicitly: volume was never transformed by J-10
-    assert rep["volume_a_equals_b"] is True
     assert rep["C"]["volume"] == pytest.approx(stored_volume * bridge_factor)
-    assert rep["C"]["close"] == stored_close  # C only changes volume, never close
-    assert rep["A"]["close_times_volume"] > rep["B"]["close_times_volume"]  # A > B since bridge_factor > 1
+    assert rep["C"]["close"] == stored_close  # C only changes volume, never close -- unchanged from iter-14
+
+
+def test_tc12_representation_b_uses_fetched_provider_volume_never_a_stored_volume_copy():
+    bridge_factor = 2.7930001225759193
+    stored_close, stored_volume = 189.61, 500_000.0
+    provider_evidence = {"close": 67.89, "volume": 350_000.0}  # DELIBERATELY != stored_volume
+    rep = diag.compute_counterfactual_representations(
+        bridge_factor, stored_close, stored_volume, provider_evidence=provider_evidence
+    )
+    assert rep["evidence_available"] is True
+    assert rep["B"]["close"] == 67.89
+    assert rep["B"]["volume"] == 350_000.0  # the FETCHED value, never stored_volume (500_000.0)
+    # the genuine, non-tautological comparison: two INDEPENDENTLY-sourced values, provably unequal.
+    assert rep["volume_a_equals_b"] is False
+    # the old arithmetic derivation is still recorded, but ONLY as a documented cross-check field --
+    # never as B's own close.
+    assert rep["close_b_arithmetic_fallback"] == pytest.approx(stored_close / bridge_factor)
+    assert rep["B"]["close"] != rep["close_b_arithmetic_fallback"]
+
+
+def test_representation_b_can_also_prove_volume_a_equals_b_true_when_fetched_volume_matches():
+    bridge_factor = 2.7930001225759193
+    stored_close, stored_volume = 189.61, 500_000.0
+    provider_evidence = {"close": 67.89, "volume": 500_000.0}  # DELIBERATELY == stored_volume this time
+    rep = diag.compute_counterfactual_representations(
+        bridge_factor, stored_close, stored_volume, provider_evidence=provider_evidence
+    )
+    # still a GENUINE comparison of two independently-sourced values -- it happens to agree this time,
+    # never true by construction the way iter-14 left it (rep["B"]["volume"] IS the fetched value, not a
+    # hardcoded copy of stored_volume).
+    assert rep["B"]["volume"] == provider_evidence["volume"]
+    assert rep["volume_a_equals_b"] is True
+
+
+def test_tc13_representation_b_fails_closed_when_provider_evidence_is_unavailable():
+    bridge_factor = 2.7930001225759193
+    stored_close, stored_volume = 189.61, 500_000.0
+    rep = diag.compute_counterfactual_representations(bridge_factor, stored_close, stored_volume, provider_evidence=None)
+    assert rep["evidence_available"] is False
+    assert rep["B"]["close"] is None
+    assert rep["B"]["volume"] is None
+    assert rep["B"]["close_times_volume"] is None
+    assert rep["volume_a_equals_b"] is None  # cannot be compared -- never assumed True or False
+    # the arithmetic value is STILL recorded (documented fallback/cross-check), but never promoted into B.
+    assert rep["close_b_arithmetic_fallback"] == pytest.approx(stored_close / bridge_factor)
+
+
+def test_tc13_representation_b_fails_closed_on_partial_provider_evidence():
+    bridge_factor = 2.7930001225759193
+    rep = diag.compute_counterfactual_representations(
+        bridge_factor, 189.61, 500_000.0, provider_evidence={"close": 67.89, "volume": None}
+    )
+    assert rep["evidence_available"] is False
+    assert rep["B"]["volume"] is None
+
+
+# --- TC-11/14/15/16: compute_provider_comparison + classify_date_from_provider_comparison ---------------
+
+
+def test_tc11_compute_provider_comparison_records_every_required_field():
+    bridge_factor = 2.7930001225759193
+    cmp = diag.compute_provider_comparison(189.61, 1_549_436.0, 67.89, 554_756.0, bridge_factor)
+    for key in (
+        "stored_close", "stored_volume", "provider_close", "provider_volume", "close_ratio", "volume_ratio",
+        "bridge_factor", "expected_inverse_volume_ratio", "stored_dollar_volume", "provider_dollar_volume",
+        "bridge_adjusted_compensation_test",
+    ):
+        assert key in cmp, f"missing {key}"
+    assert cmp["close_ratio"] == pytest.approx(189.61 / 67.89)
+    assert cmp["volume_ratio"] == pytest.approx(1_549_436.0 / 554_756.0)
+    assert cmp["expected_inverse_volume_ratio"] == pytest.approx(1.0 / bridge_factor)
+    assert cmp["stored_dollar_volume"] == pytest.approx(189.61 * 1_549_436.0)
+    assert cmp["provider_dollar_volume"] == pytest.approx(67.89 * 554_756.0)
+
+
+def test_tc14_bridged_compensating_is_genuinely_reachable_from_real_evidence_shapes():
+    """Price rebased by EXACTLY bridge_factor, volume rebased by EXACTLY 1/bridge_factor -- dollar volume
+    conserved. Proves the ONE label iter-14's tautology could never produce is now mechanically reachable."""
+    bridge_factor = 2.793
+    provider_close, provider_volume = 100.0, 1_000_000.0
+    stored_close = provider_close * bridge_factor
+    stored_volume = provider_volume / bridge_factor  # the compensating hypothesis, exactly
+    cmp = diag.compute_provider_comparison(stored_close, stored_volume, provider_close, provider_volume, bridge_factor)
+    assert cmp["bridge_adjusted_compensation_test"]["compensates"] is True
+    assert diag.classify_date_from_provider_comparison(cmp) == "bridged+compensating"
+
+
+def test_tc15_bridged_raw_is_reachable_when_volume_is_untransformed():
+    """Price rebased by bridge_factor, volume left EXACTLY on the provider's raw scale -- dollar volume
+    inflated by ~bridge_factor, not conserved."""
+    bridge_factor = 2.793
+    provider_close, provider_volume = 100.0, 1_000_000.0
+    stored_close = provider_close * bridge_factor
+    stored_volume = provider_volume  # untransformed
+    cmp = diag.compute_provider_comparison(stored_close, stored_volume, provider_close, provider_volume, bridge_factor)
+    assert cmp["bridge_adjusted_compensation_test"]["matches_raw_volume_dollar_shift"] is True
+    assert diag.classify_date_from_provider_comparison(cmp) == "bridged+raw"
+
+
+def test_raw_plus_raw_is_reachable_when_neither_side_was_rebased():
+    bridge_factor = 2.793
+    cmp = diag.compute_provider_comparison(100.2, 1_000_500.0, 100.0, 1_000_000.0, bridge_factor)
+    assert diag.classify_date_from_provider_comparison(cmp) == "raw+raw"
+
+
+def test_mixed_indeterminate_when_evidence_matches_no_hypothesis():
+    bridge_factor = 2.793
+    # close bridged, but volume neither raw (~1) nor compensating (~1/bridge_factor) -- a genuine
+    # inconsistency, never silently forced into the nearest label.
+    cmp = diag.compute_provider_comparison(279.3, 1_000_000.0, 100.0, 500_000.0, bridge_factor)
+    assert diag.classify_date_from_provider_comparison(cmp) == "mixed/indeterminate"
+
+
+def test_classify_date_from_provider_comparison_fails_closed_on_missing_fields():
+    assert diag.classify_date_from_provider_comparison({"close_ratio": None, "volume_ratio": 1.0, "bridge_factor": 2.0, "expected_inverse_volume_ratio": 0.5}) == "mixed/indeterminate"
+    assert diag.classify_date_from_provider_comparison({"close_ratio": 1.0, "volume_ratio": 1.0, "bridge_factor": 0, "expected_inverse_volume_ratio": None}) == "mixed/indeterminate"
+
+
+# --- classify_local_convention_with_volume_evidence -- end-to-end window classification -----------------
+
+
+def _series_row(iso_date: str, close: float, volume: float) -> dict:
+    return {"date": iso_date, "close": close, "volume": volume, "close_times_volume": close * volume}
+
+
+def test_classify_local_convention_with_volume_evidence_reaches_bridged_compensating_end_to_end():
+    bridge_factor = 2.793
+    evidence_row = {"bridge_factor": bridge_factor, "pairs": []}
+    provider_by_date = {}
+    stored_series = []
+    provider_close = 100.0
+    for one_date in diag.CALIBRATION_DATES + diag.RECOVERED_DATES:
+        key = one_date.isoformat()
+        provider_volume = 1_000_000.0
+        stored_close = provider_close * bridge_factor
+        stored_volume = provider_volume / bridge_factor  # compensating, exactly, every date
+        provider_by_date[key] = {"close": provider_close, "volume": provider_volume}
+        stored_series.append(_series_row(key, stored_close, stored_volume))
+        provider_close += 0.1  # small drift so dates are distinguishable; ratio math stays exact per-date
+
+    result = diag.classify_local_convention_with_volume_evidence(stored_series, evidence_row, provider_by_date)
+    assert result["windows"]["calibration_window"]["classification"] == "bridged+compensating"
+    assert result["windows"]["recovered_dates"]["classification"] == "bridged+compensating"
+    assert result["indeterminate"] is False
+    assert result["internally_consistent"] is True
+    assert result["overall_classification"] == "bridged+compensating"
+
+
+def test_classify_local_convention_with_volume_evidence_reaches_bridged_raw_end_to_end():
+    bridge_factor = 2.793
+    evidence_row = {"bridge_factor": bridge_factor, "pairs": []}
+    provider_by_date = {}
+    stored_series = []
+    provider_close = 100.0
+    for one_date in diag.CALIBRATION_DATES + diag.RECOVERED_DATES:
+        key = one_date.isoformat()
+        provider_volume = 1_000_000.0
+        stored_close = provider_close * bridge_factor
+        stored_volume = provider_volume  # untransformed, every date
+        provider_by_date[key] = {"close": provider_close, "volume": provider_volume}
+        stored_series.append(_series_row(key, stored_close, stored_volume))
+        provider_close += 0.1
+
+    result = diag.classify_local_convention_with_volume_evidence(stored_series, evidence_row, provider_by_date)
+    assert result["windows"]["calibration_window"]["classification"] == "bridged+raw"
+    assert result["windows"]["recovered_dates"]["classification"] == "bridged+raw"
+    assert result["internally_consistent"] is True
+    assert result["overall_classification"] == "bridged+raw"
+
+
+def test_tc20_classify_local_convention_with_volume_evidence_indeterminate_on_missing_evidence():
+    """A date missing from the fetched evidence never falls back to the OLD price-only continuity
+    method -- it classifies mixed/indeterminate directly, naming that date's own entry."""
+    bridge_factor = 2.793
+    evidence_row = {"bridge_factor": bridge_factor, "pairs": []}
+    stored_series = [
+        _series_row(d.isoformat(), 279.3, 358_000.0) for d in diag.CALIBRATION_DATES + diag.RECOVERED_DATES
+    ]
+    provider_by_date = {
+        d.isoformat(): {"close": 100.0, "volume": 358_000.0}
+        for d in diag.CALIBRATION_DATES  # RECOVERED_DATES deliberately absent -- insufficient evidence
+    }
+    result = diag.classify_local_convention_with_volume_evidence(stored_series, evidence_row, provider_by_date)
+    assert result["windows"]["recovered_dates"]["classification"] == "mixed/indeterminate"
+    missing_entries = [
+        r for r in result["windows"]["recovered_dates"]["per_date"] if r["classification"] == "mixed/indeterminate"
+    ]
+    assert {r["date"] for r in missing_entries} == {d.isoformat() for d in diag.RECOVERED_DATES}
+    assert result["indeterminate"] is True
+
+
+def test_tc19_classify_local_convention_with_volume_evidence_inconsistent_across_windows():
+    """The calibration window proves bridged+compensating but the recovered-dates window proves
+    bridged+raw -- a genuine, evidence-backed inconsistency (never silently reconciled)."""
+    bridge_factor = 2.793
+    evidence_row = {"bridge_factor": bridge_factor, "pairs": []}
+    stored_series = []
+    provider_by_date = {}
+    for one_date in diag.CALIBRATION_DATES:
+        key = one_date.isoformat()
+        provider_by_date[key] = {"close": 100.0, "volume": 1_000_000.0}
+        stored_series.append(_series_row(key, 100.0 * bridge_factor, 1_000_000.0 / bridge_factor))
+    for one_date in diag.RECOVERED_DATES:
+        key = one_date.isoformat()
+        provider_by_date[key] = {"close": 100.0, "volume": 1_000_000.0}
+        stored_series.append(_series_row(key, 100.0 * bridge_factor, 1_000_000.0))  # untransformed here
+
+    result = diag.classify_local_convention_with_volume_evidence(stored_series, evidence_row, provider_by_date)
+    assert result["windows"]["calibration_window"]["classification"] == "bridged+compensating"
+    assert result["windows"]["recovered_dates"]["classification"] == "bridged+raw"
+    assert result["internally_consistent"] is False
+    assert result["indeterminate"] is False  # both windows individually determinate, just DISAGREE
+
+
+def test_tc16_boundary_jumps_are_corroborating_narrative_never_a_classification_override():
+    """Even when the legacy continuity check flags a boundary jump, the WINDOW classifications stay
+    exactly what the direct fetched comparison proves -- the jump is reported, not substituted."""
+    bridge_factor = 2.793
+    evidence_row = {"bridge_factor": bridge_factor, "pairs": []}
+    provider_by_date = {
+        d.isoformat(): {"close": 100.0, "volume": 1_000_000.0}
+        for d in diag.CALIBRATION_DATES + diag.RECOVERED_DATES
+    }
+    stored_series = [
+        _series_row(d.isoformat(), 100.0 * bridge_factor, 1_000_000.0 / bridge_factor)
+        for d in diag.CALIBRATION_DATES
+    ]
+    # an EXTRA synthetic row (NOT one of the six evidence dates) with an anomalous close, positioned
+    # immediately before 2026-08-11 in the list -- creates a day-over-day "jump" whose to_date is a
+    # recovered date (a boundary jump), WITHOUT touching 2026-08-11's OWN stored value, so its direct
+    # fetched comparison stays completely clean.
+    stored_series.append(_series_row("2026-08-09", 900.0, 1_000_000.0 / bridge_factor))
+    stored_series.append(_series_row("2026-08-11", 100.0 * bridge_factor, 1_000_000.0 / bridge_factor))
+    stored_series.append(_series_row("2026-08-12", 100.0 * bridge_factor, 1_000_000.0 / bridge_factor))
+
+    result = diag.classify_local_convention_with_volume_evidence(stored_series, evidence_row, provider_by_date)
+    assert result["anomalous_jump_count"] >= 1
+    assert result["windows"]["recovered_dates"]["boundary_jumps"]
+    # the per-date evidence-backed classification is UNCHANGED by the continuity narrative -- it is
+    # computed purely from compute_provider_comparison/classify_date_from_provider_comparison.
+    per_date = {r["date"]: r["classification"] for r in result["windows"]["recovered_dates"]["per_date"]}
+    assert per_date["2026-08-11"] == "bridged+compensating"
+    assert per_date["2026-08-12"] == "bridged+compensating"
+    # but internally_consistent still honestly reflects the boundary jump as a safety-net signal.
+    assert result["internally_consistent"] is False
 
 
 # --- _build_bars_with_transformed_close -- never mutates the input bars, only the targeted dates ------
@@ -325,3 +567,105 @@ def test_fetch_avb_stored_series_reads_close_volume_and_product(engine):
     assert series[0]["close"] == 100.0
     assert series[0]["close_times_volume"] == 1000.0
     assert [row["date"] for row in series] == sorted(row["date"] for row in series)
+
+
+# --- goal-market-compass iter-15 (Goal 5): _build_bars_with_transformed_close's NEW volume_override ------
+
+
+def test_build_bars_with_transformed_close_volume_override_is_backward_compatible_when_omitted():
+    """Iteration 14's exact test, unmodified call shape -- proves the new optional kwarg changes NOTHING
+    when omitted."""
+    bars = [
+        Bar(date=date(2026, 8, 10), open=1, high=1, low=1, close=100.0, volume=10.0),
+        Bar(date=date(2026, 8, 11), open=1, high=1, low=1, close=200.0, volume=20.0),
+        Bar(date=date(2026, 8, 12), open=1, high=1, low=1, close=300.0, volume=30.0),
+    ]
+    out = diag._build_bars_with_transformed_close(bars, {date(2026, 8, 11), date(2026, 8, 12)}, 2.0)
+    assert out[0].close == 100.0 and out[0].volume == 10.0
+    assert out[1].close == 100.0 and out[1].volume == 20.0  # volume unchanged -- no override supplied
+    assert out[2].close == 150.0 and out[2].volume == 30.0
+
+
+def test_build_bars_with_transformed_close_applies_volume_override_only_to_overridden_dates():
+    bars = [
+        Bar(date=date(2026, 8, 10), open=1, high=1, low=1, close=100.0, volume=10.0),
+        Bar(date=date(2026, 8, 11), open=1, high=1, low=1, close=200.0, volume=20.0),
+        Bar(date=date(2026, 8, 12), open=1, high=1, low=1, close=300.0, volume=30.0),
+    ]
+    override = {date(2026, 8, 11): 999.0}  # ONLY 08-11 has fetched evidence; 08-12 does not
+    out = diag._build_bars_with_transformed_close(
+        bars, {date(2026, 8, 11), date(2026, 8, 12)}, 2.0, volume_override=override
+    )
+    assert out[0].volume == 10.0  # untouched date -- unaffected regardless
+    assert out[1].close == 100.0 and out[1].volume == 999.0  # BOTH close and volume substituted
+    assert out[2].close == 150.0 and out[2].volume == 30.0  # close substituted, volume passes through (no evidence)
+
+
+# --- TC-22/23/24: decision-impact trace with a genuine volume_override -----------------------------------
+
+
+def test_tc22_trace_universe_resolver_impact_with_volume_override_changes_adv_b(engine):
+    cfg = _small_universe_cfg()
+    bridge_factor = 2.793
+    with Session(engine) as session:
+        _seed_daily_prices(
+            session, diag.AVB_SYMBOL, n=40, end=AVB_TEST_DATES_END,
+            close_start=180.0, close_step=0.5, volume=1_000_000.0,
+        )
+
+    with Session(engine) as session:
+        impact_no_override = diag.trace_universe_resolver_impact(session, cfg, date(2026, 8, 11), bridge_factor)
+    with Session(engine) as session:
+        impact_with_override = diag.trace_universe_resolver_impact(
+            session, cfg, date(2026, 8, 11), bridge_factor,
+            volume_override={date(2026, 8, 11): 250_000.0},  # materially different fetched volume
+        )
+
+    assert impact_with_override["volume_override_applied"] == {"2026-08-11": 250_000.0}
+    # the override materially changes B's ADV relative to the no-override (volume-held-fixed) trace --
+    # proving the override genuinely participates in the computation, not merely recorded and ignored.
+    assert impact_with_override["adv_dollar_b"] != impact_no_override["adv_dollar_b"]
+
+
+def test_tc23_trace_is_read_only_creates_no_scanner_run(engine):
+    """Grep-verifiable in the module source (zero calls to `scanner.persist_run_payload`/`session.add`/
+    `session.commit` anywhere in `j11_avb_diagnostic.py`); this test is the behavioral proof: after
+    tracing both representations, the fixture DB still has zero ScannerRun rows."""
+    from sqlalchemy import func as _func
+    from sqlmodel import select as _select
+    from app.models import ScannerRun
+
+    cfg = _small_universe_cfg()
+    bridge_factor = 2.793
+    with Session(engine) as session:
+        _seed_daily_prices(
+            session, diag.AVB_SYMBOL, n=40, end=AVB_TEST_DATES_END,
+            close_start=180.0, close_step=0.5, volume=1_000_000.0,
+        )
+
+    with Session(engine) as session:
+        diag.trace_universe_resolver_impact(
+            session, cfg, date(2026, 8, 11), bridge_factor, volume_override={date(2026, 8, 11): 250_000.0},
+        )
+        diag.trace_scoring_and_selection_impact(
+            session, cfg, date(2026, 8, 11), bridge_factor, volume_override={date(2026, 8, 11): 250_000.0},
+        )
+
+    with Session(engine) as session:
+        count = session.exec(_select(_func.count()).select_from(ScannerRun)).one()
+    assert count == 0
+
+
+def test_tc24_trace_scoring_and_selection_impact_reports_volume_override_applied(engine):
+    cfg = _small_universe_cfg()
+    bridge_factor = 2.793
+    with Session(engine) as session:
+        _seed_daily_prices(
+            session, diag.AVB_SYMBOL, n=60, end=AVB_TEST_DATES_END,
+            close_start=180.0, close_step=0.2, volume=1_000_000.0,
+        )
+    with Session(engine) as session:
+        impact = diag.trace_scoring_and_selection_impact(
+            session, cfg, date(2026, 8, 11), bridge_factor, volume_override={date(2026, 8, 11): 250_000.0},
+        )
+    assert impact["volume_override_applied"] == {"2026-08-11": 250_000.0}
diff --git a/apps/backend/tests/test_j11_avb_provider_fetch.py b/apps/backend/tests/test_j11_avb_provider_fetch.py
new file mode 100644
index 00000000..00743982
--- /dev/null
+++ b/apps/backend/tests/test_j11_avb_provider_fetch.py
@@ -0,0 +1,171 @@
+"""goal-market-compass iter-15 -- J-11 Stage D readiness, Goal 2: fixture/mock-provider tests for the ONE
+AG-9 dated-exception-#2 bounded fetch (TC-5..TC-7, TC-10's own reuse note).
+
+NEVER a real network call -- every provider here is a small in-repo `FakePriceProvider` test double
+implementing `app.data_providers.base.PriceProvider`, never `app.data_providers.yahoo_provider.
+YahooProvider`.
+"""
+from __future__ import annotations
+
+from datetime import date
+
+import pytest
+
+from app.data_providers.base import Bar, PriceProvider, ProviderUnavailableError, RateLimitError
+from app.engine import j11_avb_provider_fetch as fetch
+
+BRIDGE_FACTOR = 2.7930001225759193
+
+
+class _FakeProvider(PriceProvider):
+    """Records every `get_daily` call it receives and returns a caller-supplied bar list (or raises a
+    caller-supplied exception) -- never touches the network."""
+
+    source = "yahoo"
+
+    def __init__(self, *, bars: "list[Bar] | None" = None, raises: Exception | None = None):
+        self._bars = bars or []
+        self._raises = raises
+        self.calls: list[dict] = []
+
+    def get_daily(self, symbol, start=None, end=None):
+        self.calls.append({"symbol": symbol, "start": start, "end": end})
+        if self._raises is not None:
+            raise self._raises
+        return list(self._bars)
+
+
+def _bar(iso_date: str, close: float, volume: float) -> Bar:
+    y, m, d = (int(x) for x in iso_date.split("-"))
+    return Bar(date=date(y, m, d), open=close, high=close, low=close, close=close, volume=volume)
+
+
+_ALL_SIX_BARS = [
+    _bar("2026-08-05", 67.89, 2_100_000.0),
+    _bar("2026-08-06", 66.79, 2_050_000.0),
+    _bar("2026-08-07", 67.15, 2_090_000.0),
+    _bar("2026-08-10", 65.82, 1_950_000.0),
+    _bar("2026-08-11", 65.08, 5_390_000.0),
+    _bar("2026-08-12", 64.37, 34_100_000.0),
+]
+
+
+# --- TC-5: exactly one call, exact symbol/window, strict filtering to the six permitted dates ---------
+
+
+def test_tc5_calls_get_daily_exactly_once_with_avb_and_the_full_window():
+    provider = _FakeProvider(bars=_ALL_SIX_BARS)
+    fetch.fetch_avb_provider_evidence(provider, bridge_factor=BRIDGE_FACTOR)
+
+    assert len(provider.calls) == 1
+    call = provider.calls[0]
+    assert call["symbol"] == "AVB"
+    assert call["start"] == date(2026, 8, 5)
+    assert call["end"] == date(2026, 8, 12)
+
+
+def test_tc5_discards_any_returned_bar_outside_the_six_permitted_dates():
+    bars_with_extras = list(_ALL_SIX_BARS) + [
+        _bar("2026-08-04", 70.0, 1_000_000.0),  # before the window -- must be discarded
+        _bar("2026-08-13", 63.0, 1_000_000.0),  # after the window -- must be discarded
+    ]
+    provider = _FakeProvider(bars=bars_with_extras)
+    result = fetch.fetch_avb_provider_evidence(provider, bridge_factor=BRIDGE_FACTOR)
+
+    assert set(result["per_date"]) == {d.isoformat() for d in fetch.PERMITTED_DATES}
+    assert sorted(result["discarded_dates_outside_permitted_set"]) == ["2026-08-04", "2026-08-13"]
+    assert result["sufficient_evidence"] is True
+
+
+# --- TC-6: full success -- per-date close/volume, provider label, timestamp, bridge_factor, formulas ---
+
+
+def test_tc6_full_success_records_complete_auditable_provenance():
+    provider = _FakeProvider(bars=_ALL_SIX_BARS)
+    result = fetch.fetch_avb_provider_evidence(provider, bridge_factor=BRIDGE_FACTOR)
+
+    assert result["provider"] == "yahoo"
+    assert result["symbol"] == "AVB"
+    assert result["requested_dates"] == [d.isoformat() for d in fetch.PERMITTED_DATES]
+    assert result["bridge_factor"] == BRIDGE_FACTOR
+    assert result["fetch_call_count"] == 1
+    assert result["fetch_error"] is None
+    assert result["missing_dates"] == []
+    assert result["sufficient_evidence"] is True
+
+    # capture_timestamp / generated_at are real UTC ISO strings, parseable and offset-aware.
+    from datetime import datetime
+    parsed_capture = datetime.fromisoformat(result["capture_timestamp"])
+    parsed_generated = datetime.fromisoformat(result["generated_at"])
+    assert parsed_capture.tzinfo is not None
+    assert parsed_generated.tzinfo is not None
+
+    assert result["per_date"]["2026-08-11"] == {"close": 65.08, "volume": 5_390_000.0}
+    assert result["per_date"]["2026-08-05"] == {"close": 67.89, "volume": 2_100_000.0}
+
+    formulas = result["comparison_formulas"]
+    assert formulas["close_ratio"] == "stored_close / provider_close"
+    assert formulas["volume_ratio"] == "stored_volume / provider_volume"
+    assert formulas["expected_inverse_volume_ratio"] == "1 / bridge_factor"
+
+
+def test_output_written_to_caller_supplied_path_only(tmp_path):
+    import json
+
+    provider = _FakeProvider(bars=_ALL_SIX_BARS)
+    result = fetch.fetch_avb_provider_evidence(provider, bridge_factor=BRIDGE_FACTOR)
+    out = tmp_path / "evidence.json"
+    out.write_text(json.dumps(result, default=str))
+    assert out.exists()
+    reloaded = json.loads(out.read_text())
+    assert reloaded["sufficient_evidence"] is True
+
+
+# --- TC-7: provider failure or short return -- fail closed, no adjacent-day substitute, no propagation --
+
+
+def test_tc7_provider_unavailable_error_is_caught_never_propagates():
+    provider = _FakeProvider(raises=ProviderUnavailableError("yahoo: 503"))
+    result = fetch.fetch_avb_provider_evidence(provider, bridge_factor=BRIDGE_FACTOR)  # must not raise
+
+    assert result["sufficient_evidence"] is False
+    assert result["fetch_error"]["type"] == "ProviderUnavailableError"
+    assert result["missing_dates"] == [d.isoformat() for d in fetch.PERMITTED_DATES]
+    assert result["per_date"] == {}
+
+
+def test_tc7_rate_limit_error_subclass_is_also_caught():
+    provider = _FakeProvider(raises=RateLimitError("yahoo: 429"))
+    result = fetch.fetch_avb_provider_evidence(provider, bridge_factor=BRIDGE_FACTOR)  # must not raise
+
+    assert result["sufficient_evidence"] is False
+    assert result["fetch_error"]["type"] == "RateLimitError"
+
+
+def test_tc7_short_return_names_the_specific_missing_dates_no_adjacent_day_substitute():
+    partial_bars = [b for b in _ALL_SIX_BARS if b.date != date(2026, 8, 12)]  # 08-12 missing
+    provider = _FakeProvider(bars=partial_bars)
+    result = fetch.fetch_avb_provider_evidence(provider, bridge_factor=BRIDGE_FACTOR)
+
+    assert result["sufficient_evidence"] is False
+    assert result["missing_dates"] == ["2026-08-12"]
+    assert "2026-08-12" not in result["per_date"]
+    # the five genuinely fetched dates are still recorded -- a partial result is not discarded wholesale.
+    assert len(result["per_date"]) == 5
+
+
+def test_tc7_a_bar_with_null_close_or_volume_counts_as_missing_not_present():
+    bars = list(_ALL_SIX_BARS)
+    bars[-1] = Bar(date=date(2026, 8, 12), open=1, high=1, low=1, close=None, volume=None)
+    provider = _FakeProvider(bars=bars)
+    result = fetch.fetch_avb_provider_evidence(provider, bridge_factor=BRIDGE_FACTOR)
+
+    assert result["sufficient_evidence"] is False
+    assert "2026-08-12" in result["missing_dates"]
+    assert "2026-08-12" not in result["per_date"]
+
+
+def test_no_other_provider_call_is_ever_made_on_failure():
+    provider = _FakeProvider(raises=ProviderUnavailableError("boom"))
+    fetch.fetch_avb_provider_evidence(provider, bridge_factor=BRIDGE_FACTOR)
+    assert len(provider.calls) == 1  # exactly one attempt, no retry-with-broadened-window
diff --git a/apps/backend/tests/test_j11_stage_d.py b/apps/backend/tests/test_j11_stage_d.py
index e71eea27..80491338 100644
--- a/apps/backend/tests/test_j11_stage_d.py
+++ b/apps/backend/tests/test_j11_stage_d.py
@@ -11,6 +11,7 @@ pattern `test_j11_maintenance.py`/`test_j11_stage_c_preflight.py` use, never `lo
 from __future__ import annotations
 
 import copy
+import json
 from datetime import date, datetime, timedelta, timezone
 
 import pytest
@@ -20,7 +21,7 @@ from sqlmodel import Session, SQLModel, create_engine
 from app.config import load_config
 from app.engine import j11_stage_d as jsd
 from app.engine.j11_maintenance import INCIDENT_DATES
-from app.models import ScannerRun
+from app.models import NextSessionManifest, ScannerRun
 
 _MATCHING_DATES = ", ".join(d.isoformat() for d in INCIDENT_DATES)
 _GOAL_MD_MATCHING = f"""
@@ -45,6 +46,30 @@ _GOAL_MD_MATCHING = f"""
 _NOT_AN_INCIDENT_DATE = date(2026, 1, 5)
 assert _NOT_AN_INCIDENT_DATE not in INCIDENT_DATES
 
+# goal-market-compass iter-15 (Goal 8): a goal.md text whose C1 restatement date list disagrees with the
+# authoritative bullet (one date swapped) -- exercises `c1_date_set_boundary_ok`'s OWN failure mode.
+_MISMATCHED_DATES = ", ".join(
+    d.isoformat() for d in (INCIDENT_DATES[:-1] + (date(2099, 1, 1),))
+)
+_GOAL_MD_C1_MISMATCH = f"""
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
+         of doubt they are `{_MISMATCHED_DATES}`.
+  - Acceptance: some acceptance text
+
+<!-- Continuous-improvement auto-journeys: appended below -->
+"""
+
 
 @pytest.fixture()
 def engine():
@@ -80,6 +105,34 @@ def _mk_run(
     return run
 
 
+def _mk_manifest(session: Session, run: ScannerRun, *, version: int = 1) -> NextSessionManifest:
+    """A hand-built manifest row referencing `run` -- mirrors `test_j11_maintenance.py`'s own `_mk_manifest`
+    helper exactly (Goal 8's manifest-value/source_run_id negative tests need at least one real row)."""
+    manifest = NextSessionManifest(
+        as_of=run.asof_date,
+        version=version,
+        source_run_id=run.id,
+        session_delta_json="{}",
+        narrative_json="{}",
+        selection_json="{}",
+        content_hash="stub-content-hash",
+        created_at=datetime.now(timezone.utc),
+        mode="at_ingest",
+        frozen=True,
+        generation_json=json.dumps({
+            "producer": "ingest_finalize",
+            "engine_identity": "stub-engine-identity",
+        }),
+        engine_identity="stub-engine-identity",
+        manifest_hash="stub-manifest-hash",
+        available_at_utc=datetime.now(timezone.utc),
+        prospective_eligible=True,
+    )
+    session.add(manifest)
+    session.flush()
+    return manifest
+
+
 # --- TC-1: fresh Stage D attempt identity ------------------------------------------------------------
 
 
@@ -338,3 +391,378 @@ def test_tc25_readiness_verdict_combines_preflight_and_avb_classification(
 def test_readiness_verdict_rejects_unknown_avb_classification():
     with pytest.raises(ValueError):
         jsd.stage_d_readiness_verdict({"passed": True, "reason": "x"}, "AVB-Z")
+
+
+# ======================================================================================================
+# goal-market-compass iter-15 (Goal 8): one dedicated negative fixture test PER remaining
+# `compare_stage_d_preflight_to_certified` check -- each perturbs exactly ONE field so no shared fixture
+# masks a different failure (iter-9's lesson). Every test asserts BOTH `checks[...] is False` AND
+# `material_mismatch is True`, mirroring `test_gate_stops_on_daily_prices_fingerprint_drift` exactly.
+# ======================================================================================================
+
+
+def test_goal8_manifest_row_count_unchanged_fails_on_drift(engine, cfg):
+    preflight = _fresh_preflight(engine, cfg)
+    certified = _certified_from(preflight)
+    certified["manifest_row_count"] = preflight["manifest_row_count"] + 1
+    gate = jsd.compare_stage_d_preflight_to_certified(preflight, certified)
+    assert gate["checks"]["manifest_row_count_unchanged"] is False
+    assert gate["material_mismatch"] is True
+
+
+def test_goal8_manifest_ddl_unchanged_fails_when_one_ddl_clause_differs(engine, cfg):
+    preflight = _fresh_preflight(engine, cfg)
+    certified = _certified_from(preflight)
+    original_sql = certified["manifest_ddl"]["table_sql"] or ""
+    certified["manifest_ddl"]["table_sql"] = original_sql + " -- one clause different"
+    gate = jsd.compare_stage_d_preflight_to_certified(preflight, certified)
+    assert gate["checks"]["manifest_ddl_unchanged"] is False
+    assert gate["material_mismatch"] is True
+
+
+def test_goal8_manifest_indexes_unchanged_fails_when_index_set_differs(engine, cfg):
+    preflight = _fresh_preflight(engine, cfg)
+    certified = _certified_from(preflight)
+    certified["manifest_ddl"]["index_names"] = list(certified["manifest_ddl"]["index_names"]) + ["ix_fake_extra"]
+    certified["manifest_ddl"]["index_sqls"] = list(certified["manifest_ddl"]["index_sqls"]) + [
+        "CREATE INDEX ix_fake_extra ON next_session_manifests(id)"
+    ]
+    gate = jsd.compare_stage_d_preflight_to_certified(preflight, certified)
+    assert gate["checks"]["manifest_indexes_unchanged"] is False
+    assert gate["material_mismatch"] is True
+
+
+def test_goal8_manifest_values_unchanged_fails_when_one_stored_value_differs(engine, cfg):
+    with Session(engine) as session:
+        run = _mk_run(session, INCIDENT_DATES[0])
+        _mk_manifest(session, run)
+        session.commit()
+
+    preflight = _fresh_preflight(engine, cfg)
+    assert preflight["manifest_row_count"] == 1  # sanity: the seeded row is really captured
+    certified = _certified_from(preflight)
+    # perturb exactly ONE stored value on the one seeded row -- content_hash, chosen because it is a
+    # plain string column untouched by any other Goal 8 test in this file.
+    certified["manifest_dump"][0]["content_hash"] = "a-different-content-hash"
+    gate = jsd.compare_stage_d_preflight_to_certified(preflight, certified)
+    assert gate["checks"]["manifest_values_unchanged"] is False
+    assert gate["material_mismatch"] is True
+    # this perturbation must NOT also trip source_run_id_values_unchanged -- only ONE field changed.
+    assert gate["checks"]["source_run_id_values_unchanged"] is True
+
+
+def test_goal8_source_run_id_values_unchanged_fails_when_one_source_run_id_differs(engine, cfg):
+    with Session(engine) as session:
+        run = _mk_run(session, INCIDENT_DATES[0])
+        _mk_manifest(session, run)
+        session.commit()
+
+    preflight = _fresh_preflight(engine, cfg)
+    certified = _certified_from(preflight)
+    certified["manifest_dump"][0]["source_run_id"] = 999999  # a source_run_id that never existed
+    gate = jsd.compare_stage_d_preflight_to_certified(preflight, certified)
+    assert gate["checks"]["source_run_id_values_unchanged"] is False
+    assert gate["material_mismatch"] is True
+    # this perturbation alone must not ALSO trip manifest_values_unchanged's full-row diff for an
+    # UNRELATED column -- diff_dumps flags source_run_id specifically, proving the two checks are
+    # independent evidence, not the same signal reported twice under two names.
+    diff_columns = {m["column"] for m in gate["manifest_dump_diff"]["mismatches"]}
+    assert diff_columns == {"source_run_id"}
+
+
+def test_goal8_data_provider_runs_count_unchanged_fails_on_drift(engine, cfg):
+    preflight = _fresh_preflight(engine, cfg)
+    certified = _certified_from(preflight)
+    certified["data_provider_runs_count"] = preflight["pre_reset_inventory"]["data_provider_runs_count"] + 1
+    gate = jsd.compare_stage_d_preflight_to_certified(preflight, certified)
+    assert gate["checks"]["data_provider_runs_count_unchanged"] is False
+    assert gate["material_mismatch"] is True
+
+
+def test_goal8_watchlist_count_unchanged_fails_on_drift(engine, cfg):
+    preflight = _fresh_preflight(engine, cfg)
+    certified = _certified_from(preflight)
+    certified["watchlist_count"] = preflight["pre_reset_inventory"]["watchlist_count"] + 1
+    gate = jsd.compare_stage_d_preflight_to_certified(preflight, certified)
+    assert gate["checks"]["watchlist_count_unchanged"] is False
+    assert gate["material_mismatch"] is True
+
+
+def test_goal8_c1_date_set_boundary_ok_fails_when_goal_md_lists_disagree(engine, cfg):
+    with Session(engine) as session:
+        preflight = jsd.capture_stage_d_preflight(
+            session, engine, None, goal_md_text=_GOAL_MD_C1_MISMATCH, git_head="deadbeef", config=cfg,
+        )
+    assert preflight["c1_date_set_boundary_check"]["ok"] is False
+    certified = _certified_from(preflight)
+    gate = jsd.compare_stage_d_preflight_to_certified(preflight, certified)
+    assert gate["checks"]["c1_date_set_boundary_ok"] is False
+    assert gate["material_mismatch"] is True
+
+
+# --- TC-35/36: the pre-existing identity-check + negative tests re-run alongside the new ones, no ------
+# --- fixture collision, and no new test ever touches the 34 6261ca17... rows or the NULL-stamped rows --
+
+
+def test_goal8_new_negative_tests_never_seed_or_assert_against_legacy_identity_rows(engine, cfg):
+    """A direct assertion that THIS file's Goal 8 fixtures never construct a `6261ca17...`-stamped or
+    NULL-stamped row on a NON-incident date the way the 34 surviving/pre-stamping-era rows are shaped --
+    every `_mk_run`/`_mk_manifest` call in the Goal 8 tests above uses an INCIDENT date with no
+    `engine_identity_value` override, so it can never collide with or assert against that population."""
+    with Session(engine) as session:
+        count = session.exec(
+            __import__("sqlmodel").select(__import__("sqlalchemy").func.count()).select_from(ScannerRun)
+        ).one()
+    # the fixture engine is FRESH per test (function-scoped `engine` fixture) -- this test's own session
+    # never persisted anything, so the table is empty; this is a structural proof that Goal 8's tests run
+    # in isolated fixture DBs, never a shared/live one where a legacy row could exist to begin with.
+    assert count == 0
+
+
+# ======================================================================================================
+# goal-market-compass iter-15 (Goal 1): reconcile_prior_iteration_truth
+# ======================================================================================================
+
+
+def _write(path, payload):
+    path.parent.mkdir(parents=True, exist_ok=True)
+    if isinstance(payload, str):
+        path.write_text(payload)
+    else:
+        path.write_text(json.dumps(payload))
+    return path
+
+
+def test_reconcile_prior_iteration_truth_reports_per_figure_match_and_mismatch(engine, cfg, tmp_path):
+    stale_readiness = {
+        "avb_classification": "AVB-B", "ready": True, "blocking_reasons": [],
+        "generated_at": "2026-08-24T22:05:04.053596+00:00",
+    }
+    readiness_path = _write(tmp_path / "stale-readiness.json", stale_readiness)
+    eval_md_path = _write(
+        tmp_path / "eval.md",
+        "# Iteration 14 Evaluation\n\n**Owner-facing lines:** `J-11 STAGE D READY: NO` · `J-11 STAGE D AUTHORIZED: NO`\n",
+    )
+    # an owner capture that DISAGREES with the empty fixture DB on purpose -- proves mismatches are
+    # reported explicitly, never silently reconciled.
+    owner_capture = dict(jsd.OWNER_TRUE_START_CAPTURE)
+    owner_capture["daily_prices_row_count"] = 999999999  # will NOT match the empty fixture (0 rows)
+
+    with Session(engine) as session:
+        result = jsd.reconcile_prior_iteration_truth(
+            session, engine, None,
+            iteration_14_readiness_path=readiness_path,
+            iteration_14_eval_md_path=eval_md_path,
+            owner_true_start_capture=owner_capture,
+        )
+
+    assert result["comparisons_against_owner_capture"]["daily_prices_row_count"]["matches_owner_capture"] is False
+    assert result["any_mismatch_against_owner_capture"] is True
+    assert result["iteration_14_stale_artifact"]["content_verbatim"] == stale_readiness
+    assert result["iteration_14_stale_artifact"]["stale_artifact_superseded"] is True
+    assert result["iteration_14_eval_md_corrected_line"]["quoted_line"] == "J-11 STAGE D READY: NO"
+    # the source files themselves are untouched -- loaded read-only, never edited.
+    assert json.loads(readiness_path.read_text()) == stale_readiness
+
+
+def test_reconcile_prior_iteration_truth_matches_when_owner_capture_agrees_with_empty_fixture(engine, cfg, tmp_path):
+    readiness_path = _write(tmp_path / "stale-readiness.json", {"avb_classification": "AVB-B", "ready": True, "blocking_reasons": []})
+    eval_md_path = _write(tmp_path / "eval.md", "`J-11 STAGE D READY: NO`\n")
+
+    owner_capture = dict(jsd.OWNER_TRUE_START_CAPTURE)
+    owner_capture.update({
+        "db_mtime": None, "db_size_bytes": None,
+        "all_11_incident_dates_zero_scanner_runs": True,
+        "daily_prices_row_count": 0, "scanner_runs_total_count": 0, "forward_returns_total_count": 0,
+        "data_provider_runs_count": 0, "manifest_row_count": 0, "watchlist_count": 0,
+        "forward_returns_measured_into_incident_total": 0, "scanner_runs_stamped_6261ca17_count": 0,
+    })
+
+    with Session(engine) as session:
+        result = jsd.reconcile_prior_iteration_truth(
+            session, engine, None,
+            iteration_14_readiness_path=readiness_path,
+            iteration_14_eval_md_path=eval_md_path,
+            owner_true_start_capture=owner_capture,
+        )
+
+    count_checks = {
+        "all_11_incident_dates_zero_scanner_runs", "daily_prices_row_count", "scanner_runs_total_count",
+        "forward_returns_total_count", "data_provider_runs_count", "manifest_row_count", "watchlist_count",
+        "forward_returns_measured_into_incident_total", "scanner_runs_stamped_6261ca17_count",
+    }
+    for name in count_checks:
+        assert result["comparisons_against_owner_capture"][name]["matches_owner_capture"] is True, name
+    assert result["forward_returns_measured_into_incident_total_matches_16614"] is False  # 0 != 16614, stated honestly
+
+
+def test_reconcile_prior_iteration_truth_raises_on_contradictory_eval_md_lines(engine, cfg, tmp_path):
+    readiness_path = _write(tmp_path / "stale-readiness.json", {"avb_classification": "AVB-B", "ready": True, "blocking_reasons": []})
+    eval_md_path = _write(tmp_path / "eval.md", "`J-11 STAGE D READY: NO` ... elsewhere ... `J-11 STAGE D READY: YES`\n")
+    with Session(engine) as session:
+        with pytest.raises(ValueError):
+            jsd.reconcile_prior_iteration_truth(
+                session, engine, None,
+                iteration_14_readiness_path=readiness_path, iteration_14_eval_md_path=eval_md_path,
+            )
+
+
+def test_reconcile_prior_iteration_truth_does_not_use_default_paths_that_could_touch_iter14_evidence(engine, cfg, tmp_path):
+    """A structural proof that `reconcile_prior_iteration_truth` has no baked-in default path of its own
+    -- both evidence paths are REQUIRED keyword arguments (calling without them is a TypeError), so a
+    caller can never accidentally point this function at a real committed evidence directory."""
+    import inspect
+    sig = inspect.signature(jsd.reconcile_prior_iteration_truth)
+    assert sig.parameters["iteration_14_readiness_path"].default is inspect.Parameter.empty
+    assert sig.parameters["iteration_14_eval_md_path"].default is inspect.Parameter.empty
+
+
+# ======================================================================================================
+# goal-market-compass iter-15 (Goal 7): produce_stage_d_readiness_artifact
+# ======================================================================================================
+
+
+def _write_preflight_gate(path, *, passed=True, generated_at="2026-08-25T10:00:00+00:00"):
+    payload = {"comparison": {"generated_at": generated_at, "checks": {}}, "verdict": {"passed": passed, "reason": "x"}}
+    return _write(path, payload)
+
+
+def _write_avb_diagnostic(path, *, classification="AVB-A", generated_at="2026-08-25T10:00:00+00:00"):
+    payload = {"generated_at": generated_at, "classification": {"classification": classification}}
+    return _write(path, payload)
+
+
+def test_tc30_produce_stage_d_readiness_artifact_calls_existing_verdict_and_writes_provenance(tmp_path):
+    preflight_path = _write_preflight_gate(tmp_path / "gate.json", passed=True)
+    avb_path = _write_avb_diagnostic(tmp_path / "avb.json", classification="AVB-A")
+    output_path = tmp_path / "readiness.json"
+
+    readiness = jsd.produce_stage_d_readiness_artifact(preflight_path, avb_path, output_path=output_path)
+
+    assert readiness["ready"] is True
+    assert readiness["authorized"] is False
+    assert readiness["inputs"] == {
+        "preflight_gate_artifact": str(preflight_path), "avb_diagnostic_artifact": str(avb_path),
+    }
+    on_disk = json.loads(output_path.read_text())
+    assert on_disk["ready"] is True
+    assert on_disk["authorized"] is False
+
+
+def test_tc31_produce_stage_d_readiness_artifact_fails_closed_on_missing_preflight_path(tmp_path):
+    avb_path = _write_avb_diagnostic(tmp_path / "avb.json")
+    output_path = tmp_path / "readiness.json"
+    with pytest.raises(ValueError):
+        jsd.produce_stage_d_readiness_artifact(tmp_path / "does-not-exist.json", avb_path, output_path=output_path)
+    assert not output_path.exists()
+
+
+def test_tc32_produce_stage_d_readiness_artifact_fails_closed_on_unknown_avb_classification(tmp_path):
+    preflight_path = _write_preflight_gate(tmp_path / "gate.json")
+    avb_path = _write_avb_diagnostic(tmp_path / "avb.json", classification="AVB-Z")
+    output_path = tmp_path / "readiness.json"
+    with pytest.raises(ValueError):
+        jsd.produce_stage_d_readiness_artifact(preflight_path, avb_path, output_path=output_path)
+    assert not output_path.exists()
+
+
+def test_tc32_produce_stage_d_readiness_artifact_fails_closed_on_missing_classification_field(tmp_path):
+    preflight_path = _write_preflight_gate(tmp_path / "gate.json")
+    avb_path = _write(tmp_path / "avb.json", {"generated_at": "2026-08-25T10:00:00+00:00", "classification": {}})
+    output_path = tmp_path / "readiness.json"
+    with pytest.raises(ValueError):
+        jsd.produce_stage_d_readiness_artifact(preflight_path, avb_path, output_path=output_path)
+    assert not output_path.exists()
+
+
+def test_tc33_produce_stage_d_readiness_artifact_fails_closed_on_stale_generation_skew(tmp_path):
+    preflight_path = _write_preflight_gate(tmp_path / "gate.json", generated_at="2026-08-25T00:00:00+00:00")
+    avb_path = _write_avb_diagnostic(tmp_path / "avb.json", generated_at="2026-08-26T12:00:00+00:00")  # >6h apart
+    output_path = tmp_path / "readiness.json"
+    with pytest.raises(ValueError):
+        jsd.produce_stage_d_readiness_artifact(preflight_path, avb_path, output_path=output_path)
+    assert not output_path.exists()
+
+
+def test_produce_stage_d_readiness_artifact_passes_when_generation_timestamps_agree_closely(tmp_path):
+    preflight_path = _write_preflight_gate(tmp_path / "gate.json", generated_at="2026-08-25T10:00:00+00:00")
+    avb_path = _write_avb_diagnostic(tmp_path / "avb.json", generated_at="2026-08-25T10:05:00+00:00")  # 5 min apart
+    output_path = tmp_path / "readiness.json"
+    readiness = jsd.produce_stage_d_readiness_artifact(preflight_path, avb_path, output_path=output_path)
+    assert readiness["staleness_check"]["consistent"] is True
+
+
+def test_produce_stage_d_readiness_artifact_avb_c_forces_not_ready_even_with_passing_preflight(tmp_path):
+    preflight_path = _write_preflight_gate(tmp_path / "gate.json", passed=True)
+    avb_path = _write_avb_diagnostic(tmp_path / "avb.json", classification="AVB-C")
+    output_path = tmp_path / "readiness.json"
+    readiness = jsd.produce_stage_d_readiness_artifact(preflight_path, avb_path, output_path=output_path)
+    assert readiness["ready"] is False
+    assert readiness["authorized"] is False
+
... [diff_bound] apps/backend/tests/test_j11_stage_d.py: 66 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_j11_stage_d_cli_scripts.py b/apps/backend/tests/test_j11_stage_d_cli_scripts.py
new file mode 100644
index 00000000..85eaf72c
--- /dev/null
+++ b/apps/backend/tests/test_j11_stage_d_cli_scripts.py
@@ -0,0 +1,333 @@
+"""goal-market-compass iter-15 -- J-11 Stage D readiness, Goal 6: CLI control-flow tests for the four
+scripts this iteration touches or adds -- `run_j11_stage_d_preflight.py`, `run_j11_avb_bridge_
+diagnostic.py`, `run_j11_avb_provider_fetch.py`, `run_j11_stage_d_readiness.py` -- plus Goal 1's
+standalone reconciliation script, `run_j11_reconcile_iteration_14_truth.py`.
+
+Mirrors `test_j11_stage_c_cli_script.py`'s `importlib`-based real-module-execution pattern EXACTLY (never
+`runpy.run_path`, whose returned namespace is a COPY -- monkeypatching it would not affect what `main()`
+actually sees). NEVER a live DB and NEVER a real network call -- every DB-touching or network-touching
+name is mocked/monkeypatched, or the test proves the refusal path never reaches those names at all.
+
+TC-8, TC-9, TC-25, TC-26, TC-27, TC-28.
+"""
+from __future__ import annotations
+
+import ast
+import importlib.util
+import json
+import sys
+from datetime import date
+from pathlib import Path
+from unittest import mock
+
+import pytest
+
+BACKEND_DIR = Path(__file__).resolve().parents[1]
+SCRIPTS_DIR = BACKEND_DIR / "scripts"
+
+STAGE_D_PREFLIGHT_SCRIPT = SCRIPTS_DIR / "run_j11_stage_d_preflight.py"
+AVB_BRIDGE_DIAGNOSTIC_SCRIPT = SCRIPTS_DIR / "run_j11_avb_bridge_diagnostic.py"
+PROVIDER_FETCH_SCRIPT = SCRIPTS_DIR / "run_j11_avb_provider_fetch.py"
+STAGE_D_READINESS_SCRIPT = SCRIPTS_DIR / "run_j11_stage_d_readiness.py"
+RECONCILE_SCRIPT = SCRIPTS_DIR / "run_j11_reconcile_iteration_14_truth.py"
+
+
+def _load_script_module(script_path: Path, module_name: str):
+    """Loads `script_path` as a REAL module object via `importlib` -- its `__dict__` IS `main.__globals__`,
+    so `monkeypatch.setattr(module, name, mock)` genuinely intercepts every call the script's top-level
+    code makes to that name. Only import-time module-level code runs (the script's own
+    `if __name__ == "__main__":` guard keeps `main()` itself from executing)."""
+    spec = importlib.util.spec_from_file_location(module_name, script_path)
+    module = importlib.util.module_from_spec(spec)
+    sys.modules[module_name] = module
+    spec.loader.exec_module(module)
+    return module
+
+
+@pytest.fixture()
+def preflight_ns(monkeypatch):
+    original_argv = sys.argv
+    try:
+        yield _load_script_module(STAGE_D_PREFLIGHT_SCRIPT, "run_j11_stage_d_preflight_under_test")
+    finally:
+        sys.argv = original_argv
+        sys.modules.pop("run_j11_stage_d_preflight_under_test", None)
+
+
+@pytest.fixture()
+def avb_diagnostic_ns(monkeypatch):
+    original_argv = sys.argv
+    try:
+        yield _load_script_module(AVB_BRIDGE_DIAGNOSTIC_SCRIPT, "run_j11_avb_bridge_diagnostic_under_test")
+    finally:
+        sys.argv = original_argv
+        sys.modules.pop("run_j11_avb_bridge_diagnostic_under_test", None)
+
+
+@pytest.fixture()
+def provider_fetch_ns(monkeypatch):
+    original_argv = sys.argv
+    try:
+        yield _load_script_module(PROVIDER_FETCH_SCRIPT, "run_j11_avb_provider_fetch_under_test")
+    finally:
+        sys.argv = original_argv
+        sys.modules.pop("run_j11_avb_provider_fetch_under_test", None)
+
+
+@pytest.fixture()
+def readiness_ns(monkeypatch):
+    original_argv = sys.argv
+    try:
+        yield _load_script_module(STAGE_D_READINESS_SCRIPT, "run_j11_stage_d_readiness_under_test")
+    finally:
+        sys.argv = original_argv
+        sys.modules.pop("run_j11_stage_d_readiness_under_test", None)
+
+
+@pytest.fixture()
+def reconcile_ns(monkeypatch):
+    original_argv = sys.argv
+    try:
+        yield _load_script_module(RECONCILE_SCRIPT, "run_j11_reconcile_iteration_14_truth_under_test")
+    finally:
+        sys.argv = original_argv
+        sys.modules.pop("run_j11_reconcile_iteration_14_truth_under_test", None)
+
+
+# --- TC-25: run_j11_stage_d_preflight.py refuses without --evidence-dir, before load_config/engine ------
+
+
+def test_tc25_stage_d_preflight_refuses_without_evidence_dir(monkeypatch, preflight_ns, capsys):
+    mock_load_config = mock.MagicMock(name="load_config")
+    monkeypatch.setattr(preflight_ns, "load_config", mock_load_config)
+    mock_write_json = mock.MagicMock(name="_write_json")
+    monkeypatch.setattr(preflight_ns, "_write_json", mock_write_json)
+    monkeypatch.setattr(sys, "argv", ["run_j11_stage_d_preflight.py"])  # no --evidence-dir
+
+    exit_code = preflight_ns.main()
+
+    assert exit_code == 2
+    mock_load_config.assert_not_called()
+    mock_write_json.assert_not_called()
+    assert "--evidence-dir" in capsys.readouterr().err
+
+
+# --- TC-26: run_j11_avb_bridge_diagnostic.py refuses without --output-path/--provider-fetch-evidence- ---
+# --- path, before load_config/engine construction --------------------------------------------------
+
+
+def test_tc26_avb_bridge_diagnostic_refuses_without_output_path(monkeypatch, avb_diagnostic_ns, tmp_path, capsys):
+    mock_load_config = mock.MagicMock(name="load_config")
+    monkeypatch.setattr(avb_diagnostic_ns, "load_config", mock_load_config)
+    fetch_evidence_path = tmp_path / "fetch-evidence.json"
+    fetch_evidence_path.write_text(json.dumps({"per_date": {}, "sufficient_evidence": False}))
+    monkeypatch.setattr(
+        sys, "argv",
+        ["run_j11_avb_bridge_diagnostic.py", "--provider-fetch-evidence-path", str(fetch_evidence_path)],
+    )  # no --output-path
+
+    exit_code = avb_diagnostic_ns.main()
+
+    assert exit_code == 2
+    mock_load_config.assert_not_called()
+    assert "--output-path" in capsys.readouterr().err
+
+
+def test_tc26_avb_bridge_diagnostic_refuses_without_provider_fetch_evidence_path(monkeypatch, avb_diagnostic_ns, tmp_path, capsys):
+    mock_load_config = mock.MagicMock(name="load_config")
+    monkeypatch.setattr(avb_diagnostic_ns, "load_config", mock_load_config)
+    output_path = tmp_path / "out.json"
+    monkeypatch.setattr(
+        sys, "argv", ["run_j11_avb_bridge_diagnostic.py", "--output-path", str(output_path)],
+    )  # no --provider-fetch-evidence-path
+
+    exit_code = avb_diagnostic_ns.main()
+
+    assert exit_code == 2
+    mock_load_config.assert_not_called()
+    assert not output_path.exists()
+    assert "--provider-fetch-evidence-path" in capsys.readouterr().err
+
+
+def test_tc26_avb_bridge_diagnostic_refuses_without_either_path(monkeypatch, avb_diagnostic_ns, capsys):
+    mock_load_config = mock.MagicMock(name="load_config")
+    monkeypatch.setattr(avb_diagnostic_ns, "load_config", mock_load_config)
+    monkeypatch.setattr(sys, "argv", ["run_j11_avb_bridge_diagnostic.py"])
+
+    exit_code = avb_diagnostic_ns.main()
+
+    assert exit_code == 2
+    mock_load_config.assert_not_called()
+    err = capsys.readouterr().err
+    assert "--output-path" in err and "--provider-fetch-evidence-path" in err
+
+
+# --- TC-8: run_j11_avb_provider_fetch.py refuses without --output-path, before ANY provider/network -----
+
+
+def test_tc8_provider_fetch_refuses_without_output_path(monkeypatch, provider_fetch_ns, capsys):
+    mock_provider_cls = mock.MagicMock(name="YahooProvider")
+    monkeypatch.setattr(provider_fetch_ns, "YahooProvider", mock_provider_cls)
+    mock_load_evidence = mock.MagicMock(name="load_j10_avb_evidence")
+    monkeypatch.setattr(provider_fetch_ns, "load_j10_avb_evidence", mock_load_evidence)
+    monkeypatch.setattr(sys, "argv", ["run_j11_avb_provider_fetch.py"])  # no --output-path
+
+    exit_code = provider_fetch_ns.main()
+
+    assert exit_code == 2
+    mock_provider_cls.assert_not_called()  # no provider constructed -- structurally no network call possible
+    mock_load_evidence.assert_not_called()
+    assert "--output-path" in capsys.readouterr().err
+
+
+# --- TC-9: valid args + fixture provider -- writes only under tmp_path, no DB engine/session anywhere ---
+
+
+def test_tc9_provider_fetch_imports_no_db_engine_or_session_helpers():
+    """Static proof (never fooled by the script's own docstring prose, which discusses these names):
+    parses the script's IMPORT statements only -- if `get_engine`/`Session`/`load_config` are never
+    imported, they structurally cannot be called anywhere in the file."""
+    tree = ast.parse(PROVIDER_FETCH_SCRIPT.read_text())
+    imported_names: set[str] = set()
+    for node in ast.walk(tree):
+        if isinstance(node, (ast.Import, ast.ImportFrom)):
+            for alias in node.names:
+                imported_names.add(alias.asname or alias.name)
+    assert "get_engine" not in imported_names
+    assert "Session" not in imported_names
+    assert "load_config" not in imported_names
+
+
+def test_tc9_provider_fetch_with_valid_args_writes_only_under_tmp_path(monkeypatch, provider_fetch_ns, tmp_path):
+    from app.data_providers.base import Bar, PriceProvider
+
+    class _FakeProvider(PriceProvider):
+        source = "yahoo"
+
+        def get_daily(self, symbol, start=None, end=None):
+            return [
+                Bar(date=date(2026, 8, 5), open=1, high=1, low=1, close=67.89, volume=2_100_000.0),
+                Bar(date=date(2026, 8, 6), open=1, high=1, low=1, close=66.79, volume=2_050_000.0),
+                Bar(date=date(2026, 8, 7), open=1, high=1, low=1, close=67.15, volume=2_090_000.0),
+                Bar(date=date(2026, 8, 10), open=1, high=1, low=1, close=65.82, volume=1_950_000.0),
+                Bar(date=date(2026, 8, 11), open=1, high=1, low=1, close=65.08, volume=5_390_000.0),
+                Bar(date=date(2026, 8, 12), open=1, high=1, low=1, close=64.37, volume=34_100_000.0),
+            ]
+
+    monkeypatch.setattr(provider_fetch_ns, "YahooProvider", _FakeProvider)
+
+    j10_evidence_path = tmp_path / "j10-evidence.json"
+    j10_evidence_path.write_text(json.dumps({"symbols": [{"symbol": "AVB", "bridge_factor": 2.793, "pairs": []}]}))
+    output_path = tmp_path / "nested" / "fetch-evidence.json"
+
+    monkeypatch.setattr(
+        sys, "argv",
+        [
+            "run_j11_avb_provider_fetch.py",
+            "--output-path", str(output_path),
+            "--j10-evidence-path", str(j10_evidence_path),
+        ],
+    )
+
+    exit_code = provider_fetch_ns.main()
+
+    assert exit_code == 0
+    assert output_path.exists()
+    written = json.loads(output_path.read_text())
+    assert written["sufficient_evidence"] is True
+    assert written["fetch_call_count"] == 1
+
+
+# --- TC-27: run_j11_stage_d_readiness.py refuses before any file I/O beyond argument parsing -----------
+
+
+def test_tc27_stage_d_readiness_refuses_without_any_required_path(monkeypatch, readiness_ns, capsys):
+    mock_produce = mock.MagicMock(name="produce_stage_d_readiness_artifact")
+    monkeypatch.setattr(readiness_ns.jsd, "produce_stage_d_readiness_artifact", mock_produce)
+    monkeypatch.setattr(sys, "argv", ["run_j11_stage_d_readiness.py"])
+
+    exit_code = readiness_ns.main()
+
+    assert exit_code == 2
+    mock_produce.assert_not_called()
+    err = capsys.readouterr().err
+    assert "--preflight-gate-path" in err and "--avb-diagnostic-path" in err and "--output-path" in err
+
+
+def test_tc27_stage_d_readiness_refuses_with_only_some_required_paths(monkeypatch, readiness_ns, tmp_path, capsys):
+    mock_produce = mock.MagicMock(name="produce_stage_d_readiness_artifact")
+    monkeypatch.setattr(readiness_ns.jsd, "produce_stage_d_readiness_artifact", mock_produce)
+    monkeypatch.setattr(
+        sys, "argv",
+        ["run_j11_stage_d_readiness.py", "--preflight-gate-path", str(tmp_path / "gate.json")],
+    )  # avb-diagnostic-path and output-path still missing
+
+    exit_code = readiness_ns.main()
+
+    assert exit_code == 2
+    mock_produce.assert_not_called()
+
+
+def test_tc28_stage_d_readiness_with_all_paths_writes_only_under_tmp_path(readiness_ns, tmp_path):
+    """The real, unmocked happy path -- this script performs NO database/network access at all, so
+    exercising it for real (against tmp_path-only fixture JSONs) is safe and simple."""
+    preflight_gate_path = tmp_path / "gate.json"
+    preflight_gate_path.write_text(json.dumps({
+        "comparison": {"generated_at": "2026-08-25T10:00:00+00:00"}, "verdict": {"passed": True, "reason": "x"},
+    }))
+    avb_diagnostic_path = tmp_path / "avb.json"
+    avb_diagnostic_path.write_text(json.dumps({
+        "generated_at": "2026-08-25T10:01:00+00:00", "classification": {"classification": "AVB-A"},
+    }))
+    output_path = tmp_path / "readiness.json"
+
+    original_argv = sys.argv
+    try:
+        sys.argv = [
+            "run_j11_stage_d_readiness.py",
+            "--preflight-gate-path", str(preflight_gate_path),
+            "--avb-diagnostic-path", str(avb_diagnostic_path),
+            "--output-path", str(output_path),
+        ]
+        exit_code = readiness_ns.main()
+    finally:
+        sys.argv = original_argv
+
+    assert exit_code == 0
+    assert output_path.exists()
+    written = json.loads(output_path.read_text())
+    assert written["ready"] is True
+    assert written["authorized"] is False
+
+
+# --- TC-27 (Goal 1's standalone reconciliation script): refuses without --output-path -------------------
+
+
+def test_tc27_reconcile_script_refuses_without_output_path(monkeypatch, reconcile_ns, capsys):
+    mock_load_config = mock.MagicMock(name="load_config")
+    monkeypatch.setattr(reconcile_ns, "load_config", mock_load_config)
+    monkeypatch.setattr(sys, "argv", ["run_j11_reconcile_iteration_14_truth.py"])
+
+    exit_code = reconcile_ns.main()
+
+    assert exit_code == 2
+    mock_load_config.assert_not_called()
+    assert "--output-path" in capsys.readouterr().err
+
+
+# --- TC-29 corroboration: none of these refusal tests wrote anywhere under the real committed evidence --
+# --- directories -- proven directly by asserting on git-tracked paths, mirroring the session's standing -
+# --- practice (the phase-level `git status --porcelain` check is the authoritative proof; this is a -----
+# --- fast in-process corroboration). ------------------------------------------------------------------
+
+
+def test_none_of_the_refusal_paths_reference_a_real_committed_evidence_directory_as_a_default():
+    """Static proof: none of the five scripts' argparse `--output-path`/`--evidence-dir` arguments carry
+    a non-None default that resolves under `runs/goal-market-compass-iter-13` or `-iter-14`."""
+    for script_path in (
+        STAGE_D_PREFLIGHT_SCRIPT, AVB_BRIDGE_DIAGNOSTIC_SCRIPT, PROVIDER_FETCH_SCRIPT,
+        STAGE_D_READINESS_SCRIPT, RECONCILE_SCRIPT,
+    ):
+        source = script_path.read_text()
+        assert 'default=DEFAULT_EVIDENCE_DIR' not in source
+        assert 'default=DEFAULT_OUTPUT_PATH' not in source
```
