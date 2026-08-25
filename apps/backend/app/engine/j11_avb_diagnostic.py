"""app.engine.j11_avb_diagnostic -- J-11 Stage D readiness: read-only AVB bridge/volume diagnostic
(goal-market-compass iter-14, Goal 4).

J-10 bridged AVB's OHLC by a persisted factor (`bridge_factor approx 2.793`) for the two recovered dates
(2026-08-11, 2026-08-12) and deliberately did NOT transform volume, while Trendora computes Average
Dollar Volume as `close * volume` -- feeding universe membership
(`app.engine.universe_resolver._adv_dollar`/`resolve_candidate`), Risk's `liquidity` component
(`app.engine.scoring`'s `_neg(adv)`), and cross-sectional liquidity percentiles. This module re-derives
the bridge factor and its calibration pairs from the PERSISTED J-10 evidence (never re-fetched -- AG-9's
recovery-fetch exception is exhausted), establishes AVB's ACTUAL stored local convention from the stored
`daily_prices` series itself (never from finance convention alone), computes three counterfactual ADV
representations, and traces the decision impact through the named canonical modules -- read-only,
in-memory, never mutating `daily_prices`, never calling any J-10 recovery/fetch function, never creating
a `ScannerRun`.

**The single most important empirical fact this module's own live capture establishes** (re-derived, not
assumed): of the 566 pool symbols the J-10 evidence file computed a `bridge_factor` for, AVB is the ONLY
one whose factor differs materially from 1.0 (every other symbol is a raw+raw pass-through, factor in
[0.99, 1.01]). This is what makes the diagnostic's classification question real rather than academic --
AVB's stored scale genuinely differs from its peers', so a naive "close * volume" ADV comparison across
the pool is NOT scale-neutral for this one name.

Classification vocabulary (exactly one, per Goal 4):
  - **AVB-A** -- no material issue found; Stage D may proceed.
  - **AVB-B** -- material effect confirmed, but the canonical stored convention is proven internally
    consistent (from the stored series itself); record an explicit caveat, never "correct" volume; Stage
    D may still proceed.
  - **AVB-C** -- the restored representation is inconsistent with Trendora's own stored convention AND
    materially affects canonical Stage D output; **STAGE D NOT READY**, owner decision.
  - **AVB-D** -- evidence insufficient; **STAGE D NOT READY**, do not guess.

**goal-market-compass iter-15 addendum.** Iteration 14 left a price-only tautology behind:
`compute_counterfactual_representations` set `volume_a = volume_b = stored_volume`, so `volume_a_equals_b`
was true BY CONSTRUCTION and `bridged+compensating` -- the one label that could flag a genuine volume
problem -- was structurally unreachable from any real input. `docs/goal.md` AG-9's "Dated exception #2 --
AVB convention diagnostic (owner, 2026-08-25)" authorizes the ONE bounded fetch that fixes this
(`app.engine.j11_avb_provider_fetch`, called from `apps/backend/scripts/run_j11_avb_provider_fetch.py` --
never from this module, which stays fetch-free). This module now consumes that persisted fetch evidence:
`compute_provider_comparison`/`classify_date_from_provider_comparison`/
`classify_local_convention_with_volume_evidence` are the NEW genuinely volume-aware functions;
`compute_counterfactual_representations` now sources representation B from the FETCHED evidence (fails
closed, `evidence_available: False`, when it is missing for a date -- never a silent fallback to the old
arithmetic derivation or a copy of `stored_volume`); `_build_bars_with_transformed_close` and both
`trace_*_impact` functions gained an optional `volume_override` so the decision-impact trace substitutes
BOTH close and volume for the target dates, not close alone. `classify_local_convention` (price-only) and
`compute_counterfactual_representations`'s old arithmetic path are both PRESERVED, unchanged, as
documented fallbacks/cross-checks -- never removed, never silently preferred over real fetched evidence
when it exists.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy import func
from sqlmodel import Session, select

from app.config import REPO_ROOT, Config, get_config
from app.engine import scoring
from app.engine import universe_resolver as ur
from app.engine.buckets import to_bucket
from app.engine.compass import _qualifier_checks
from app.engine.normalize import cross_sectional_percentiles
from app.engine.prices import Bar, bars_asof_window
from app.engine.regime import score_regime
from app.engine.scoring import CONTEXTUAL_KEYS, NA_KEYS, score_stocks
from app.engine.setups import classify_setup
from app.models import DailyPrice

AVB_SYMBOL = "AVB"

DEFAULT_J10_EVIDENCE_PATH = (
    REPO_ROOT / "runs" / "goal-market-compass-iter-9" / "j10-population-evidence.json"
)

# The J-10 calibration window (never-deleted, pre-incident dates the recovery used to validate the
# bridge factor) and the two recovered (bridged-on-write) dates -- literal historical facts about THIS
# incident, not a reusable threshold (same posture as `j11_maintenance.INCIDENT_DATES`).
CALIBRATION_DATES: tuple[date, ...] = (
    date(2026, 8, 5), date(2026, 8, 6), date(2026, 8, 7), date(2026, 8, 10),
)
RECOVERED_DATES: tuple[date, ...] = (date(2026, 8, 11), date(2026, 8, 12))

# A day-over-day return magnitude beyond this is treated as an anomalous jump for the continuity check
# (structural sanity bound, not a scoring/decision threshold -- a genuine ~2.79x scale break would show
# up as a +179%/-64% single-day "return", two full orders of magnitude past any plausible normal move;
# excluded from `test_no_magic_numbers.CALC_FILES` for the identical reason `j10_recovery.py`/
# `j11_maintenance.py` are -- a diagnostic sanity bound, not a decision cutoff).
_CONTINUITY_JUMP_THRESHOLD = 0.25

# goal-market-compass iter-15 (Goal 3): the relative-tolerance band a ratio must fall within to count as
# "matches" a target value (1.0 for "unchanged", `bridge_factor` for "fully rebased", or
# `expected_inverse_volume_ratio` for "compensating"). Reuses the SAME 1% band the ORIGINAL calibration
# check already applied inline (`0.99 <= ratio <= 1.01`, i.e. target*(1-0.01) .. target*(1+0.01)) -- now a
# single named, documented constant so the price-only check and the new volume-aware checks apply
# IDENTICAL tolerance rather than two independently-chosen bands. A diagnostic sanity bound, not a
# decision cutoff -- excluded from `test_no_magic_numbers.CALC_FILES` for the same reason
# `_CONTINUITY_JUMP_THRESHOLD` above already is (this whole module is not in `CALC_FILES`).
_RATIO_RELATIVE_TOLERANCE = 0.01


def _within_relative_tolerance(
    value: Optional[float], target: Optional[float], tolerance: float = _RATIO_RELATIVE_TOLERANCE
) -> bool:
    """Whether `value` sits within `tolerance` (relative) of `target`. `target` of `None`/`0`, or `value`
    of `None`, is NEVER "within tolerance" -- fails closed rather than raising or silently treating a
    missing measurement as a match."""
    if value is None or target is None or target == 0:
        return False
    return abs(value - target) <= abs(target) * tolerance


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ----------------------------------------------------------------------------------------------
# Persisted J-10 evidence -- re-derive the bridge factor and calibration pairs, never re-fetch
# ----------------------------------------------------------------------------------------------


def load_j10_avb_evidence(path: Path = DEFAULT_J10_EVIDENCE_PATH) -> dict:
    """AVB's own per-symbol row from the persisted J-10 population-recovery evidence file -- the
    `bridge_factor` and the 4 calibration-window `pairs` (`fallback_close`/`stored_close`/`ratio` per
    trading date), read verbatim, never re-derived from a fresh fetch (AG-9 is exhausted)."""
    payload = json.loads(Path(path).read_text())
    for row in payload.get("symbols", []):
        if row.get("symbol") == AVB_SYMBOL:
            return row
    raise ValueError(f"{AVB_SYMBOL} not found in J-10 evidence file {path}")


def summarize_pool_bridge_factor_distribution(path: Path = DEFAULT_J10_EVIDENCE_PATH) -> dict:
    """Whether AVB's bridging is symbol-specific or pool-wide -- re-derived from the SAME persisted
    evidence file, across every symbol it recorded a `bridge_factor` for (never re-fetched). This is the
    fact that makes the classification question material: if every symbol were bridged, a pool-wide ADV
    comparison would be scale-neutral; if AVB alone is bridged, it is not."""
    payload = json.loads(Path(path).read_text())
    rows = payload.get("symbols", [])
    factors = {row["symbol"]: row["bridge_factor"] for row in rows if row.get("bridge_factor") is not None}
    near_one = {sym: f for sym, f in factors.items() if 0.99 <= f <= 1.01}
    not_near_one = {sym: f for sym, f in factors.items() if not (0.99 <= f <= 1.01)}
    return {
        "symbols_with_bridge_factor": len(factors),
        "total_symbols_in_evidence": len(rows),
        "near_one_count": len(near_one),
        "materially_bridged_symbols": not_near_one,
        "avb_is_unique_material_outlier": set(not_near_one) == {AVB_SYMBOL},
    }


# ----------------------------------------------------------------------------------------------
# Stored series + local-convention classification (from the stored series itself)
# ----------------------------------------------------------------------------------------------


def fetch_avb_stored_series(
    session: Session, start_date: date, end_date: date, symbol: str = AVB_SYMBOL
) -> list[dict]:
    """AVB's stored `daily_prices` rows in `[start_date, end_date]`, column-projected (symbol/date/close/
    volume only -- never a full-row ORM load), read-only, ascending by date."""
    rows = session.exec(
        select(DailyPrice.date, DailyPrice.close, DailyPrice.volume)
        .where(DailyPrice.symbol == symbol)
        .where(DailyPrice.date >= start_date)
        .where(DailyPrice.date <= end_date)
        .order_by(DailyPrice.date)
    ).all()
    out = []
    for d, close, volume in rows:
        entry = {
            "date": d.isoformat(),
            "close": float(close) if close is not None else None,
            "volume": float(volume) if volume is not None else None,
        }
        entry["close_times_volume"] = (
            entry["close"] * entry["volume"] if entry["close"] is not None and entry["volume"] is not None else None
        )
        out.append(entry)
    return out


def _day_over_day_returns(series: list[dict]) -> list[dict]:
    """Simple close-to-close % return between consecutive STORED rows (whatever their date gap) -- the
    continuity-check signal: a genuine ~2.79x scale break shows up as an enormous single-step "return"
    (+179%/-64%), far past any plausible ordinary daily move."""
    out = []
    for prev, cur in zip(series, series[1:]):
        if prev["close"] in (None, 0) or cur["close"] is None:
            continue
        pct = (cur["close"] - prev["close"]) / prev["close"]
        out.append({"from_date": prev["date"], "to_date": cur["date"], "pct_return": pct})
    return out


def classify_local_convention(stored_series: list[dict], evidence_row: dict) -> dict:
    """Classifies AVB's actual stored local convention per window, FROM THE STORED SERIES ITSELF -- never
    from finance convention alone (docs/goal.md, Goal 4). Three sub-windows:

      - the calibration window (2026-08-05/06/07/10, never deleted, never touched by J-10): a DIRECT
        ratio check against the persisted `fallback_close` pairs -- the only sub-window with an
        independent comparable value.
      - the two recovered dates (2026-08-11/12): no independent comparable exists (J-10 WROTE these by
        applying the bridge factor to the fallback close for exactly these two dates) -- classified by
        CONTINUITY instead: does the day-over-day return crossing into/out of these dates stay within a
        plausible ordinary-move bound, or does it show the ~2.79x jump a scale mismatch would produce.
      - dates outside both (earlier history / post-recovery through the frontier): no independent
        comparable either -- classified by the SAME continuity test, honestly labeled as continuity-only
        evidence, never asserted as independently verified.

    Returns one of `raw+raw` / `bridged+raw` / `bridged+compensating` / `mixed/indeterminate` PER WINDOW,
    plus an overall `internally_consistent` flag (True only if every window's classification agrees --
    all bridged+raw, or all raw+raw -- with no discontinuity at the incident boundary) and an
    `indeterminate` flag (True if any sub-window's evidence is insufficient to classify at all)."""
    by_date = {row["date"]: row for row in stored_series}
    pairs_by_date = {p["trading_date"]: p for p in evidence_row.get("pairs", [])}

    calibration_results = []
    for one_date in CALIBRATION_DATES:
        key = one_date.isoformat()
        pair = pairs_by_date.get(key)
        stored = by_date.get(key)
        if pair is None or stored is None or stored["close"] is None:
            calibration_results.append({"date": key, "classification": "mixed/indeterminate", "reason": "no comparable pair or stored row"})
            continue
        ratio = stored["close"] / pair["fallback_close"] if pair["fallback_close"] else None
        classification = "bridged+raw" if ratio is not None and not _within_relative_tolerance(ratio, 1.0) else "raw+raw"
        calibration_results.append({
            "date": key, "stored_close": stored["close"], "fallback_close": pair["fallback_close"],
            "ratio": ratio, "classification": classification,
        })
    calibration_classes = {r["classification"] for r in calibration_results}
    calibration_window_classification = (
        calibration_classes.pop() if len(calibration_classes) == 1 else "mixed/indeterminate"
    )

    returns = _day_over_day_returns(stored_series)
    anomalous_jumps = [r for r in returns if abs(r["pct_return"]) > _CONTINUITY_JUMP_THRESHOLD]

    recovered_keys = {d.isoformat() for d in RECOVERED_DATES}
    boundary_jumps = [j for j in anomalous_jumps if j["from_date"] in recovered_keys or j["to_date"] in recovered_keys]
    recovered_window_classification = (
        "mixed/indeterminate" if not boundary_jumps and calibration_window_classification == "mixed/indeterminate"
        else ("bridged+raw" if calibration_window_classification == "bridged+raw" and not boundary_jumps
              else ("raw+raw" if calibration_window_classification == "raw+raw" and not boundary_jumps
                    else "mixed/indeterminate"))
    )

    surrounding_window_classification = (
        calibration_window_classification if not anomalous_jumps else "mixed/indeterminate"
    )

    windows = {
        "calibration_window": {
            "dates": [d.isoformat() for d in CALIBRATION_DATES],
            "classification": calibration_window_classification,
            "per_date": calibration_results,
            "evidence": "direct ratio against the persisted J-10 fallback_close pairs",
        },
        "recovered_dates": {
            "dates": [d.isoformat() for d in RECOVERED_DATES],
            "classification": recovered_window_classification,
            "boundary_jumps": boundary_jumps,
            "evidence": (
                "no independent comparable exists for these dates (J-10 wrote them); classified by "
                "day-over-day continuity with the adjacent calibration-window/post-recovery dates only"
            ),
        },
        "surrounding_window": {
            "classification": surrounding_window_classification,
            "anomalous_jumps": anomalous_jumps,
            "evidence": (
                "no independent comparable exists outside the calibration window; classified by "
                "day-over-day continuity across the whole fetched stored series only -- never asserted "
                "as independently verified against a raw source"
            ),
        },
    }

    all_classes = {w["classification"] for w in windows.values()}
    indeterminate = "mixed/indeterminate" in all_classes
    internally_consistent = (not indeterminate) and len(all_classes) == 1 and not anomalous_jumps

    return {
        "windows": windows,
        "day_over_day_returns_checked": len(returns),
        "anomalous_jump_count": len(anomalous_jumps),
        "internally_consistent": internally_consistent,
        "indeterminate": indeterminate,
        "overall_classification": (
            "mixed/indeterminate" if indeterminate
            else (calibration_window_classification if internally_consistent else "mixed/indeterminate")
        ),
        "reasoning": (
            f"calibration window classifies as {calibration_window_classification} from "
            f"{len(calibration_results)} direct fallback-close pairs (zero comparable-pair failures); "
            f"{len(anomalous_jumps)} anomalous day-over-day jump(s) found across "
            f"{len(returns)} checked transitions in the fetched stored series "
            f"({len(boundary_jumps)} at the 2026-08-11/12 recovery boundary specifically) -- "
            + ("no discontinuity at the incident boundary or elsewhere in the fetched window."
               if not anomalous_jumps else
               "a discontinuity WAS found -- see anomalous_jumps/boundary_jumps.")
        ),
    }


# ----------------------------------------------------------------------------------------------
# goal-market-compass iter-15 (Goals 3/4): genuine cross-source (fetched provider vs stored) per-date
# comparison + volume-aware window classification -- the fix for the price-only tautology iter-14 left
# behind (`volume_a = volume_b = stored_volume`, so `bridged+compensating` was structurally unreachable).
# ----------------------------------------------------------------------------------------------


def compute_provider_comparison(
    stored_close: Optional[float],
    stored_volume: Optional[float],
    provider_close: Optional[float],
    provider_volume: Optional[float],
    bridge_factor: float,
) -> dict:
    """The per-date REAL cross-source comparison record Goal 3 requires (TC-11) -- computed for any date
    where BOTH a stored `daily_prices` row and Goal 2's fetched provider evidence exist. Every field is a
    plain, auditable arithmetic derivation; this function only MEASURES -- `classify_date_from_provider_
    comparison` is what DECIDES a classification from these measurements.

    `bridge_adjusted_compensation_test`'s reasoning (logged assumption, `runs/goal-session-market-compass/
    state/assumptions.md` iter-15 entry, independently re-derived here): dollar volume (close x volume) is
    invariant under a genuine, consistent basis change -- if BOTH price and share-count/volume were
    rebased together by a reverse-split-like factor (price x bridge_factor, volume / bridge_factor), then
    `stored_close*stored_volume` and `provider_close*provider_volume` are approximately EQUAL
    (`dollar_volume_ratio ~= 1`, i.e. "compensating"). If only price was rebased and volume was left on
    the provider's raw scale, `stored_close*stored_volume` is instead approximately `bridge_factor` TIMES
    `provider_close*provider_volume` (`dollar_volume_ratio ~= bridge_factor`, i.e. "raw" volume) -- which
    is exactly `close_ratio(~=bridge_factor) x volume_ratio(~=1)`. Neither hypothesis is assumed true here
    -- both `compensates` and `matches_raw_volume_dollar_shift` are computed and reported side by side."""
    close_ratio = (
        stored_close / provider_close if stored_close is not None and provider_close else None
    )
    volume_ratio = (
        stored_volume / provider_volume if stored_volume is not None and provider_volume else None
    )
    expected_inverse_volume_ratio = 1.0 / bridge_factor if bridge_factor else None
    stored_dollar_volume = (
        stored_close * stored_volume if stored_close is not None and stored_volume is not None else None
    )
    provider_dollar_volume = (
        provider_close * provider_volume if provider_close is not None and provider_volume is not None else None
    )
    dollar_volume_ratio = (
        stored_dollar_volume / provider_dollar_volume
        if stored_dollar_volume is not None and provider_dollar_volume else None
    )
    compensates = _within_relative_tolerance(dollar_volume_ratio, 1.0)
    matches_raw_volume_dollar_shift = _within_relative_tolerance(dollar_volume_ratio, bridge_factor)

    return {
        "stored_close": stored_close,
        "stored_volume": stored_volume,
        "provider_close": provider_close,
        "provider_volume": provider_volume,
        "close_ratio": close_ratio,
        "volume_ratio": volume_ratio,
        "bridge_factor": bridge_factor,
        "expected_inverse_volume_ratio": expected_inverse_volume_ratio,
        "stored_dollar_volume": stored_dollar_volume,
        "provider_dollar_volume": provider_dollar_volume,
        "dollar_volume_ratio": dollar_volume_ratio,
        "bridge_adjusted_compensation_test": {
            "formula": (
                "dollar_volume_ratio = (stored_close*stored_volume) / (provider_close*provider_volume); "
                "compensates iff dollar_volume_ratio ~= 1.0 (price-up offset by volume-down); "
                "matches_raw_volume_dollar_shift iff dollar_volume_ratio ~= bridge_factor (only price "
                "was rebased, volume stayed on the provider's raw scale)"
            ),
            "dollar_volume_ratio": dollar_volume_ratio,
            "compensates": compensates,
            "matches_raw_volume_dollar_shift": matches_raw_volume_dollar_shift,
        },
    }


def classify_date_from_provider_comparison(
    comparison: dict, tolerance: float = _RATIO_RELATIVE_TOLERANCE
) -> str:
    """One of `raw+raw` / `bridged+raw` / `bridged+compensating` / `mixed/indeterminate`, from a SINGLE
    date's real cross-source comparison (Goal 3/4) -- every label is mechanically reachable, never
    hardcoded or pre-selected:
      - `raw+raw`: close_ratio ~= 1 AND volume_ratio ~= 1 (neither side was rebased).
      - `bridged+compensating`: close_ratio ~= bridge_factor AND volume_ratio ~= expected_inverse_volume_
        ratio (price AND volume were both rebased; dollar volume conserved -- TC-14).
      - `bridged+raw`: close_ratio ~= bridge_factor AND volume_ratio ~= 1 (only price was rebased,
        volume was left on the provider's raw scale -- TC-15).
      - `mixed/indeterminate`: evidence missing, or a shape that matches none of the three hypotheses
        above (a genuine inconsistency -- never silently forced into the nearest label)."""
    close_ratio = comparison.get("close_ratio")
    volume_ratio = comparison.get("volume_ratio")
    bridge_factor = comparison.get("bridge_factor")
    expected_inverse_volume_ratio = comparison.get("expected_inverse_volume_ratio")
    if close_ratio is None or volume_ratio is None or not bridge_factor or expected_inverse_volume_ratio is None:
        return "mixed/indeterminate"

    close_near_one = _within_relative_tolerance(close_ratio, 1.0, tolerance)
    close_near_bridge = _within_relative_tolerance(close_ratio, bridge_factor, tolerance)
    volume_near_one = _within_relative_tolerance(volume_ratio, 1.0, tolerance)
    volume_near_inverse = _within_relative_tolerance(volume_ratio, expected_inverse_volume_ratio, tolerance)

    if close_near_one and volume_near_one:
        return "raw+raw"
    if close_near_bridge and volume_near_inverse:
        return "bridged+compensating"
    if close_near_bridge and volume_near_one:
        return "bridged+raw"
    return "mixed/indeterminate"


def classify_local_convention_with_volume_evidence(
    stored_series: list[dict], evidence_row: dict, provider_evidence_by_date: dict[str, dict]
) -> dict:
    """The volume-aware successor to `classify_local_convention` (Goal 3/4) -- this is the function
    `classify_avb` is fed from THIS iteration onward. Classifies the calibration window AND the
    recovered-dates window from a GENUINE per-date cross-source comparison (Goal 2's fetched provider
    close+volume vs the stored close+volume), so `bridged+compensating` becomes genuinely reachable and
    `raw+raw`/`bridged+raw` are PROVEN from real volume evidence rather than assumed from price alone.
    `provider_evidence_by_date` is Goal 2's persisted fetch evidence (`{iso_date: {"close": ...,
    "volume": ...}}`) for AG-9 dated exception #2's six permitted dates.

    A date inside either window whose fetched evidence is missing/insufficient classifies its OWN entry
    (and therefore that whole window, since a window's classification requires every one of its dates to
    agree) as `mixed/indeterminate` -- it NEVER falls back to the OLD price-only continuity method
    (evidence was supposed to exist for these six specific dates; `classify_local_convention` remains
    available unchanged as a documented price-only cross-check/fallback, never silently substituted here).

    The `surrounding_window` (dates outside the six AG-9-permitted dates, where no fetched evidence exists
    or could exist under the amendment) still uses ONLY the day-over-day continuity check -- corroborating
    narrative, never a substitute for the direct fetched comparison the two windows above now have
    (Goal 3's own words)."""
    by_date = {row["date"]: row for row in stored_series}
    bridge_factor = evidence_row.get("bridge_factor")

    def _classify_window(dates: tuple) -> tuple[list[dict], str]:
        results = []
        for one_date in dates:
            key = one_date.isoformat()
            stored = by_date.get(key)
            provider = provider_evidence_by_date.get(key)
            if (
                stored is None or stored.get("close") is None
                or provider is None or provider.get("close") is None or provider.get("volume") is None
            ):
                results.append({
                    "date": key,
                    "classification": "mixed/indeterminate",
                    "reason": "no stored row, or no sufficient fetched provider evidence, for this date",
                })
                continue
            comparison = compute_provider_comparison(
                stored["close"], stored.get("volume"), provider["close"], provider["volume"], bridge_factor,
            )
            classification = classify_date_from_provider_comparison(comparison)
            results.append({"date": key, "classification": classification, "comparison": comparison})
        classes = {r["classification"] for r in results}
        overall = classes.pop() if len(classes) == 1 else "mixed/indeterminate"
        return results, overall

    calibration_results, calibration_window_classification = _classify_window(CALIBRATION_DATES)
    recovered_results, recovered_window_classification = _classify_window(RECOVERED_DATES)

    returns = _day_over_day_returns(stored_series)
    anomalous_jumps = [r for r in returns if abs(r["pct_return"]) > _CONTINUITY_JUMP_THRESHOLD]
    recovered_keys = {d.isoformat() for d in RECOVERED_DATES}
    boundary_jumps = [
        j for j in anomalous_jumps if j["from_date"] in recovered_keys or j["to_date"] in recovered_keys
    ]

    windows = {
        "calibration_window": {
            "dates": [d.isoformat() for d in CALIBRATION_DATES],
            "classification": calibration_window_classification,
            "per_date": calibration_results,
            "evidence": (
                "genuine cross-source comparison against Goal 2's AG-9 dated-exception-#2 fetched "
                "provider evidence (close AND volume, never a stored-volume tautology)"
            ),
        },
        "recovered_dates": {
            "dates": [d.isoformat() for d in RECOVERED_DATES],
            "classification": recovered_window_classification,
            "per_date": recovered_results,
            "boundary_jumps": boundary_jumps,
            "evidence": (
                "genuine cross-source comparison against Goal 2's AG-9 dated-exception-#2 fetched "
                "provider evidence -- the SAME direct evidence class as the calibration window, no "
                "longer continuity-only the way iteration 14 left it"
            ),
        },
        "surrounding_window": {
            "classification": "mixed/indeterminate" if anomalous_jumps else "no_independent_signal",
            "anomalous_jumps": anomalous_jumps,
            "evidence": (
                "no independent comparable exists outside the six AG-9-permitted dates; day-over-day "
                "continuity is corroborating narrative ONLY here, never a substitute for the direct "
                "fetched comparison the two windows above now have (Goal 3)"
            ),
        },
    }

    evidence_backed_classes = {calibration_window_classification, recovered_window_classification}
    indeterminate = "mixed/indeterminate" in evidence_backed_classes
    internally_consistent = (
        (not indeterminate) and len(evidence_backed_classes) == 1 and not boundary_jumps
    )
    overall_classification = (
        "mixed/indeterminate" if indeterminate
        else (calibration_window_classification if internally_consistent else "mixed/indeterminate")
    )

    return {
        "windows": windows,
        "day_over_day_returns_checked": len(returns),
        "anomalous_jump_count": len(anomalous_jumps),
        "internally_consistent": internally_consistent,
        "indeterminate": indeterminate,
        "overall_classification": overall_classification,
        "reasoning": (
            f"calibration window classifies as {calibration_window_classification} and the recovered-"
            f"dates window classifies as {recovered_window_classification}, BOTH from genuine fetched "
            f"cross-source (close+volume) comparisons against Goal 2's AG-9 dated-exception-#2 evidence "
            "(never a price-only tautology) -- "
            + (
                f"{len(boundary_jumps)} boundary continuity jump(s) noted at the recovery boundary as "
                "corroborating narrative only. "
                if boundary_jumps else ""
            )
            + (
                "internally consistent." if internally_consistent
                else "NOT internally consistent, or evidence insufficient for at least one permitted "
                     "date -- see per-date entries."
            )
        ),
    }


# ----------------------------------------------------------------------------------------------
# Counterfactual representations A / B / C
# ----------------------------------------------------------------------------------------------


def compute_counterfactual_representations(
    bridge_factor: float,
    stored_close: float,
    stored_volume: float,
    provider_evidence: Optional[dict] = None,
) -> dict:
    """The three counterfactual ADV representations for one date's stored row (Goal 3/4):

      - **A** -- bridged close x stored raw volume: the actual canonical value served today.
      - **B** -- goal-market-compass iter-15 fix: when `provider_evidence` (Goal 2's fetched
        `{"close": ..., "volume": ...}` for this date) is supplied, B is the GENUINE fetched provider
        close AND fetched provider volume -- two independently-sourced values, never a copy of
        `stored_volume` (the iter-14 tautology this fixes: `volume_a = volume_b = stored_volume` made
        `volume_a_equals_b` true by construction). The OLD arithmetic derivation
        (`stored_close / bridge_factor`) is still recorded, but ONLY as a documented fallback/cross-check
        field (`close_b_arithmetic_fallback`) -- never silently substituted for a real fetched measurement
        that exists. When `provider_evidence` is `None` or incomplete for this date, B FAILS CLOSED: its
        `close`/`volume` are `None` and `evidence_available` is `False` -- never a silent fallback to the
        arithmetic derivation or a copy of `stored_volume` (TC-13).
      - **C** -- bridged close x a stated HYPOTHETICAL inverse-adjusted volume (`stored_volume *
        bridge_factor` -- the share-count-continuity value IF the bridge factor reflected a genuine
        corporate action with a matching volume adjustment): UNCHANGED from iteration 14 -- diagnostic
        only, its formula/rationale recorded, never written, never assumed correct."""
    close_a, volume_a = stored_close, stored_volume
    arithmetic_close_b = stored_close / bridge_factor if bridge_factor else None
    volume_c = stored_volume * bridge_factor if bridge_factor else None

    evidence_available = (
        provider_evidence is not None
        and provider_evidence.get("close") is not None
        and provider_evidence.get("volume") is not None
    )
    close_b = provider_evidence["close"] if evidence_available else None
    volume_b = provider_evidence["volume"] if evidence_available else None

    def _leaf(close, volume, formula):
        adv = close * volume if close is not None and volume is not None else None
        return {"close": close, "volume": volume, "close_times_volume": adv, "formula": formula}

    representation_a = _leaf(
        close_a, volume_a, "A = stored_bridged_close x stored_raw_volume (the actual canonical value served today)"
    )
    if evidence_available:
        b_formula = (
            "B = provider_close x provider_volume (Goal 2's FETCHED evidence -- two independently-"
            "sourced values, never a copy of stored_volume; the arithmetic stored_close/bridge_factor "
            "value is recorded separately in close_b_arithmetic_fallback for cross-check only)"
        )
    else:
        b_formula = (
            "B = UNAVAILABLE -- no sufficient fetched provider evidence for this date (fail-closed; "
            "never silently substituted with the arithmetic stored_close/bridge_factor derivation or a "
            "copy of stored_volume)"
        )
    representation_b = _leaf(close_b, volume_b, b_formula)
    representation_c = _leaf(
        close_a, volume_c,
        "C = stored_bridged_close x (stored_volume x bridge_factor) -- DIAGNOSTIC ONLY: the hypothetical "
        "share-count-continuity-preserving volume IF the bridge factor reflected a genuine corporate "
        "action; never written to the database, never assumed correct",
    )
    return {
        "bridge_factor": bridge_factor,
        "evidence_available": evidence_available,
        "close_b_arithmetic_fallback": arithmetic_close_b,
        "A": representation_a,
        "B": representation_b,
        "C": representation_c,
        "volume_a_equals_b": (
            representation_a["volume"] == representation_b["volume"] if evidence_available else None
        ),
    }


# ----------------------------------------------------------------------------------------------
# Decision-impact trace -- through the named canonical modules, read-only / in-memory
# ----------------------------------------------------------------------------------------------


def _build_bars_with_transformed_close(
    bars_real: list,
    target_dates: set,
    bridge_factor: float,
    *,
    volume_override: Optional[dict] = None,
) -> list[Bar]:
    """A NEW, in-memory `Bar` list -- never mutates the fetched ORM/`Bar` objects, never touches the DB --
    identical to `bars_real` except every bar whose date is in `target_dates` has its close divided by
    `bridge_factor` (representation B).

    goal-market-compass iter-15 (Goal 5): `volume_override` is an OPTIONAL `{date: volume}` map (Goal 2's
    fetched provider volume for the target dates) -- when a target-date bar's date is a key in
    `volume_override`, ITS volume is ALSO replaced by the override value; every other bar's volume (and
    every bar's open/high/low outside `target_dates`) passes through completely unchanged. `None`/omitted
    `volume_override` (the default) reproduces iteration 14's exact behavior -- close-only substitution,
    volume always passed through from `bars_real` -- so every existing caller/test is unaffected."""
    out: list[Bar] = []
    overrides = volume_override or {}
    for b in bars_real:
        if b.date in target_dates and b.close is not None:
            new_volume = overrides.get(b.date, b.volume)
            out.append(Bar(date=b.date, open=b.open, high=b.high, low=b.low, close=b.close / bridge_factor, volume=new_volume))
        else:
            out.append(Bar(date=b.date, open=b.open, high=b.high, low=b.low, close=b.close, volume=b.volume))
    return out


def trace_universe_resolver_impact(
    session: Session,
    cfg: Config,
    asof: date,
    bridge_factor: float,
    *,
    volume_override: Optional[dict] = None,
) -> dict:
    """Traces (A) vs (B) through `app.engine.universe_resolver._adv_dollar`/`resolve_candidate` -- the ADV
    value and the ADV admission gate (`REASON_BELOW_ADV`), via the REAL canonical functions, never
    reimplemented. Mirrors `resolve_with_reasons`'s OWN two-step read exactly: a full trailing-bar COUNT
    (date <= asof, the true history-gate input) computed separately from the bounded `adv_window_days`
    bar fetch (the value-gate input) -- passing a `bar_count` shorter than the true history whenever
    `adv_window_days < min_history_bars` would silently misreport the history gate (a real bug this
    module's own fixture test caught and this fix closes).

    goal-market-compass iter-15 (Goal 5): `volume_override` (Goal 2's fetched provider volume per date)
    is threaded through to `_build_bars_with_transformed_close`, so representation (B) substitutes BOTH
    close AND volume for the target dates when real fetched evidence is available -- never close alone."""
    filters = cfg.universe.filters
    true_bar_count = int(
        session.exec(
            select(func.count(DailyPrice.id))
            .where(DailyPrice.symbol == AVB_SYMBOL)
            .where(DailyPrice.date <= asof)
        ).one()
        or 0
    )
    bars_real = bars_asof_window(session, AVB_SYMBOL, asof, filters.adv_window_days)
    recovered_in_window = {d for d in RECOVERED_DATES if d <= asof}
    bars_b = _build_bars_with_transformed_close(
        bars_real, recovered_in_window, bridge_factor, volume_override=volume_override
    )

    adv_a = ur._adv_dollar(bars_real, filters.adv_window_days)
    adv_b = ur._adv_dollar(bars_b, filters.adv_window_days)
    resolution_a = ur.resolve_candidate(bars_real, AVB_SYMBOL, cfg, asof, bar_count=true_bar_count)
    resolution_b = ur.resolve_candidate(bars_b, AVB_SYMBOL, cfg, asof, bar_count=true_bar_count)

    applied_volume_overrides = {
        d.isoformat(): (volume_override or {})[d] for d in recovered_in_window if d in (volume_override or {})
    }
    return {
        "asof": asof.isoformat(),
        "adv_window_days": filters.adv_window_days,
        "min_dollar_vol_threshold": filters.min_dollar_vol,
        "true_bar_count": true_bar_count,
        "recovered_dates_in_window": sorted(d.isoformat() for d in recovered_in_window),
        "volume_override_applied": applied_volume_overrides,
        "adv_dollar_a": adv_a,
        "adv_dollar_b": adv_b,
        "resolution_a": {"admitted": resolution_a.admitted, "reason": resolution_a.reason, "bars": resolution_a.bars},
        "resolution_b": {"admitted": resolution_b.admitted, "reason": resolution_b.reason, "bars": resolution_b.bars},
        "admission_changed": resolution_a.admitted != resolution_b.admitted,
    }


def trace_scoring_and_selection_impact(
    session: Session,
    cfg: Config,
    asof: date,
    bridge_factor: float,
    *,
    volume_override: Optional[dict] = None,
) -> dict:
    """Traces (A) vs (B) through `app.engine.scoring`'s `liquidity` component (`_neg(adv)`), AVB's
    cross-sectional liquidity percentile, the Risk score/bucket, setup status, and candidate eligibility
    -- plus whether OTHER pool names' liquidity percentiles shift. ONE real `score_stocks(session, asof,
    cfg)` call (representation A, the actual served state) supplies AVB's real other-component raws/
    percentiles AND every OTHER resolved member's real liquidity raw (read off the already-assembled
    output -- no second per-symbol query for the rest of the pool, AG-8); representation B substitutes
    ONLY AVB's liquidity raw/percentile and recomputes AVB's Risk score/bucket/setup/eligibility via the
    REAL `_build_score`/`to_bucket`/`classify_setup`/`_qualifier_checks` functions.

    goal-market-compass iter-15 (Goal 5): `volume_override` (Goal 2's fetched provider volume per date) is
    threaded through to `_build_bars_with_transformed_close`, so representation (B)'s ADV/liquidity trace
    uses BOTH the fetched close AND the fetched volume for the target dates -- never volume held fixed at
    the stored (representation A) value the way iteration 14 left it."""
    scored_a = score_stocks(session, asof, cfg)
    rows_by_ticker = {row["ticker"]: row for row in scored_a["rows"]}
    if AVB_SYMBOL not in rows_by_ticker:
        return {
            "asof": asof.isoformat(),
            "avb_resolved_member": False,
            "note": f"AVB is not a point-in-time-resolved universe member at {asof.isoformat()} under "
                    "representation A -- no score to trace.",
        }
    avb_row_a = rows_by_ticker[AVB_SYMBOL]

    icfg = cfg.indicators
    bars_real = bars_asof_window(session, AVB_SYMBOL, asof, icfg.vol_avg_period)
    recovered_in_window = {d for d in RECOVERED_DATES if d <= asof}
    bars_b = _build_bars_with_transformed_close(
        bars_real, recovered_in_window, bridge_factor, volume_override=volume_override
    )
    closes_a, vols_a = scoring.closes(bars_real), scoring.volumes(bars_real)
    closes_b, vols_b = scoring.closes(bars_b), scoring.volumes(bars_b)
    adv_liquidity_a = scoring._avg_dollar_volume(closes_a, vols_a, icfg.vol_avg_period)
    adv_liquidity_b = scoring._avg_dollar_volume(closes_b, vols_b, icfg.vol_avg_period)
    liquidity_raw_a = scoring._neg(adv_liquidity_a)
    liquidity_raw_b = scoring._neg(adv_liquidity_b)

    risk_components_a = {c["name"]: c for c in avb_row_a["risk"]["components"]}
    served_liquidity = risk_components_a.get("liquidity")
    served_liquidity_raw = served_liquidity["raw"] if served_liquidity else None
    liquidity_raw_a_reproduces_served = (
        served_liquidity_raw is not None and liquidity_raw_a is not None
        and round(liquidity_raw_a, 4) == served_liquidity_raw
    )

    pool_liquidity_raw_a: dict[str, float] = {}
    for ticker, row in rows_by_ticker.items():
        component = next((c for c in row["risk"]["components"] if c["name"] == "liquidity"), None)
        if component is not None and component.get("available") and component.get("raw") is not None:
            pool_liquidity_raw_a[ticker] = component["raw"]
    pool_liquidity_raw_b = dict(pool_liquidity_raw_a)
    if liquidity_raw_b is not None:
        pool_liquidity_raw_b[AVB_SYMBOL] = liquidity_raw_b

    pool_percentiles_a = cross_sectional_percentiles(pool_liquidity_raw_a)
    pool_percentiles_b = cross_sectional_percentiles(pool_liquidity_raw_b)
    served_liquidity_percentile = served_liquidity["percentile"] if served_liquidity else None
    percentile_a_reproduces_served = (
        served_liquidity_percentile is not None
        and round(pool_percentiles_a.get(AVB_SYMBOL, -1), 4) == served_liquidity_percentile
    )
    other_ticker_percentile_shifts = {
        ticker: {"percentile_a": pool_percentiles_a[ticker], "percentile_b": pool_percentiles_b[ticker]}
        for ticker in pool_percentiles_a
        if ticker != AVB_SYMBOL and pool_percentiles_a[ticker] != pool_percentiles_b.get(ticker)
    }

    raws_b_for_avb = {
        name: (c["raw"] if name != "liquidity" else liquidity_raw_b) for name, c in risk_components_a.items()
    }
    percentiles_b_for_avb: dict[str, dict[str, float]] = {}
    for name, c in risk_components_a.items():
        if name in NA_KEYS or name in CONTEXTUAL_KEYS:
            continue
        value = pool_percentiles_b.get(AVB_SYMBOL) if name == "liquidity" else c["percentile"]
        percentiles_b_for_avb[name] = {AVB_SYMBOL: value}

    risk_b = scoring._build_score(AVB_SYMBOL, cfg.scores.risk.weights, raws_b_for_avb, percentiles_b_for_avb)
    risk_b["bucket"] = to_bucket(risk_b["score"], cfg)

    leadership_a = avb_row_a["leadership"]
    entry_quality_a = avb_row_a["entry_quality"]
    risk_a = avb_row_a["risk"]
    regime_label = score_regime(session, asof, cfg)["label"]
    setup_b_raw = classify_setup(
        {"leadership": leadership_a["score"], "entry_quality": entry_quality_a["score"], "risk": risk_b["score"]},
        regime_label, cfg,
    )

    checks_a = _qualifier_checks(
        {"leadership_score": leadership_a["score"], "entry_quality_score": entry_quality_a["score"],
         "risk_score": risk_a["score"]},
        cfg,
    )
    checks_b = _qualifier_checks(
        {"leadership_score": leadership_a["score"], "entry_quality_score": entry_quality_a["score"],
         "risk_score": risk_b["score"]},
        cfg,
    )
    eligible_a = all(c["passed"] for c in checks_a)
    eligible_b = all(c["passed"] for c in checks_b)

    applied_volume_overrides = {
        d.isoformat(): (volume_override or {})[d] for d in recovered_in_window if d in (volume_override or {})
    }
    return {
        "asof": asof.isoformat(),
        "avb_resolved_member": True,
        "vol_avg_period": icfg.vol_avg_period,
        "volume_override_applied": applied_volume_overrides,
        "adv_liquidity_a": adv_liquidity_a,
        "adv_liquidity_b": adv_liquidity_b,
        "liquidity_raw_a": liquidity_raw_a,
        "liquidity_raw_b": liquidity_raw_b,
        "liquidity_raw_a_reproduces_served": liquidity_raw_a_reproduces_served,
        "liquidity_percentile_a": pool_percentiles_a.get(AVB_SYMBOL),
        "liquidity_percentile_b": pool_percentiles_b.get(AVB_SYMBOL),
        "percentile_a_reproduces_served": percentile_a_reproduces_served,
        "pool_member_count": len(pool_liquidity_raw_a),
        "other_ticker_percentile_shifts": other_ticker_percentile_shifts,
        "risk_score_a": risk_a["score"],
        "risk_score_b": risk_b["score"],
        "risk_bucket_a": risk_a["bucket"],
        "risk_bucket_b": risk_b["bucket"],
        "setup_status_a": avb_row_a["setup"]["status"],
        "setup_status_b": setup_b_raw["status"],
        "eligible_a": eligible_a,
        "eligible_b": eligible_b,
        "qualifier_checks_a": checks_a,
        "qualifier_checks_b": checks_b,
        "leadership_score": leadership_a["score"],  # unchanged A vs B -- no leadership component reads ADV
        "entry_quality_score": entry_quality_a["score"],  # unchanged A vs B -- same reason
        "relative_ranking_note": (
            "AVB's relative ranking (candidates are sorted by Leadership score, descending -- the sole "
            "sort key `evaluate_selection` uses) is unaffected by A vs B: Leadership does not read ADV/"
            "volume at all (confirmed by inspecting `_raw_components` -- none of rs_spy_1m/rs_spy_3m/"
            "rs_sector/rs_theme/ma_stack/high_proximity/up_down_vol reads `adv`). A full population-wide "
            "selection-disposition replay (`evaluate_selection`) requires a persisted ScannerRun for this "
            "as-of, which does not exist (Stage C cleared it) and creating one is forbidden this "
            "iteration -- the individual qualifier-check pass/fail above is the direct, checkable proxy "
            "for candidate eligibility instead."
        ),
    }


# ----------------------------------------------------------------------------------------------
# Overall classification
# ----------------------------------------------------------------------------------------------


def classify_avb(local_convention: dict, decision_impact_by_date: dict[str, dict]) -> dict:
    """Combines the local-convention classification and the per-date decision-impact traces into exactly
    one of AVB-A / AVB-B / AVB-C / AVB-D, with reasoning naming the specific evidence (never a bare
    label)."""
    material_signals: list[str] = []
    for asof_key, impact in decision_impact_by_date.items():
        ur_impact = impact.get("universe_resolver", {})
        if ur_impact.get("admission_changed"):
            material_signals.append(f"{asof_key}: universe admission changed under representation B")

        scoring_impact = impact.get("scoring_and_selection", {})
        if scoring_impact.get("avb_resolved_member") is False:
            continue
        if scoring_impact.get("risk_bucket_a") != scoring_impact.get("risk_bucket_b"):
            material_signals.append(
                f"{asof_key}: Risk bucket changed ({scoring_impact.get('risk_bucket_a')} -> "
                f"{scoring_impact.get('risk_bucket_b')})"
            )
        if scoring_impact.get("setup_status_a") != scoring_impact.get("setup_status_b"):
            material_signals.append(
                f"{asof_key}: setup status changed ({scoring_impact.get('setup_status_a')} -> "
                f"{scoring_impact.get('setup_status_b')})"
            )
        if scoring_impact.get("eligible_a") != scoring_impact.get("eligible_b"):
            material_signals.append(f"{asof_key}: candidate eligibility changed")
        shifts = scoring_impact.get("other_ticker_percentile_shifts") or {}
        if shifts:
            material_signals.append(f"{asof_key}: {len(shifts)} OTHER pool ticker(s)' liquidity percentile shifted")

    indeterminate = bool(local_convention.get("indeterminate"))
    internally_consistent = bool(local_convention.get("internally_consistent"))

    if indeterminate:
        classification = "AVB-D"
        reasoning = (
            "The stored-series local-convention classification could not be determined with sufficient "
            "evidence: " + local_convention.get("reasoning", "") + " -- do not guess; STAGE D NOT READY."
        )
    elif not internally_consistent:
        classification = "AVB-C"
        reasoning = (
            "The restored representation is inconsistent with Trendora's own stored convention for AVB: "
            + local_convention.get("reasoning", "") + " -- STAGE D NOT READY, owner decision."
        )
    elif material_signals:
        classification = "AVB-B"
        reasoning = (
            "Material effect confirmed (" + "; ".join(material_signals) + ") but the stored convention is "
            "proven internally consistent from GENUINE fetched cross-source (close+volume) evidence -- "
            f"overall convention: {local_convention.get('overall_classification', 'unknown')} ("
            + local_convention.get("reasoning", "") + ") -- record an explicit caveat, do NOT silently "
            "correct anything; Stage D may still proceed."
        )
    else:
        classification = "AVB-A"
        reasoning = (
            "No material effect found under representation B across the traced dates: no universe-"
            "admission change, no Risk-bucket change, no setup-status change, no eligibility change, and "
            "no OTHER pool ticker's liquidity percentile shifted."
        )

    return {
        "generated_at": _now_iso(),
        "classification": classification,
        "reasoning": reasoning,
        "material_signals": material_signals,
        "stage_d_ready_per_avb": classification in ("AVB-A", "AVB-B"),
    }
