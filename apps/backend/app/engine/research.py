"""Research-lab analytics engine (Data Contract: app.engine.research).

The first lab is the **Factor Lab** (J-25): for a chosen factor + forward horizon it reports a decile
table (D1…D10) of mean realized forward return alongside a downside-risk-adjusted column, each with
sample size `n`, plus the factor's Spearman rank information coefficient (rank-IC). It is purely
DESCRIPTIVE evidence — NOT a fitted/ML predictive model.

THREE non-negotiable disciplines (each unit-proved):

  1. READ-ONLY (anti-goal: Research lab is read-only / No recompute in the read path). Every figure is
     derived ENTIRELY from values ALREADY STORED by the canonical engines: the realized forward returns
     (`forward_returns.realized_return`) JOINED to the stored factor value on `scanner_results` — a typed
     score column, or a `record_json` component `raw` read VERBATIM. This module issues ONLY SELECTs
     against `ForwardReturn` + `ScannerResult` and calls NO scoring / regime / return / bucket / pattern
     math (no `run_scan`, `score_stocks`, `backfill*`, `forward_return`, `detect_*`). It recomputes no
     factor and no return — it groups the SAME per-observation pool `forward_testing.compute_forward_
     aggregates(horizon)` builds (the pooled-mean == `overall.mean_return` invariant is unit-asserted).

  2. RISK IS DOWNSIDE-ONLY (anti-goal: Risk-adjusted reporting must not conflate up/down volatility).
     The risk-adjusted column is `mean_return / downside_deviation`, where the downside deviation uses
     ONLY the negative leg (`sqrt(mean(min(r, 0)**2))`, MAR=0) — never total volatility, which would
     penalise healthy upside moves. Raw mean and risk-adjusted are returned side by side; NA (None) when
     the downside deviation is zero or n < 2 (never a huge total-vol number).

  3. NO MAGIC NUMBERS / NO FABRICATION. The decile count and the entire factor catalog come from
     `config.research.factor_lab` (no literal here); the low-sample threshold is reused from
     `walk_forward.min_sample`. A factor-NULL observation is EXCLUDED (never bucketed); a decile or IC
     with too few observations carries its honest `n` and an NA/low-sample flag — never a fabricated 0.
"""
from __future__ import annotations

import json
from collections import defaultdict
from math import ceil, sqrt
from statistics import mean, median
from typing import Optional

from sqlmodel import Session, select

from app.config import Config, get_config, parse_factor_source
from app.engine.forward_testing import (
    SURVIVORSHIP_BIAS_LABEL,
    _distribution,
    _mean_or_none,
)
from app.engine.setups import ALL_STATUSES
from app.models import ForwardReturn, ScannerResult, ScannerRun

# The honest "descriptive, not predictive / universe-relative" caveat carried on every Factor-Lab
# payload alongside the (reused, single-source) survivorship-bias label (anti-goals: Research lab is
# read-only, honest & not predictive + Honest limitations surfaced).
RESEARCH_CAVEAT = (
    "Descriptive evidence, not a predictive model: these are realized forward returns sorted by a "
    "stored factor on the current-membership (universe-relative) seed — read them as historical "
    "association, never a forecast. Low-sample deciles show NA + n rather than a fabricated number."
)


# --------------------------------------------------------------------------------------------------
# Config-driven catalog (the dropdown vocabulary — config-only factor needs no frontend edit)
# --------------------------------------------------------------------------------------------------
def factor_catalog(cfg: Config) -> list[dict]:
    """The ordered, config-driven factor catalog: one `{key, label, family, direction, source}` per
    `config.research.factor_lab.factors` row (the `source` is descriptive metadata — where the stored
    value is read from, not a re-typed number). The frontend dropdown is built from THIS list."""
    return [
        {"key": f.key, "label": f.label, "family": f.family, "direction": f.direction, "source": f.source}
        for f in cfg.research.factor_lab.factors
    ]


# --------------------------------------------------------------------------------------------------
# Pure stats helpers (downside-only risk + Spearman rank-IC) — no DB, no recomputation of any return
# --------------------------------------------------------------------------------------------------
def _downside_deviation(returns: list[float]) -> float:
    """Downside deviation about MAR=0: `sqrt(mean(min(r, 0)**2))`. Penalises ONLY downside dispersion —
    NEVER total volatility (anti-goal: risk must not conflate up/down volatility). Zero when no return
    is negative (an all-up cohort has no downside risk); the caller maps that to NA, not a huge number."""
    if not returns:
        return 0
    return sqrt(sum(min(r, 0) ** 2 for r in returns) / len(returns))


def _risk_adjusted(returns: list[float]) -> Optional[float]:
    """Mean return per unit DOWNSIDE deviation (`mean / downside_deviation`). NA (None) when n < 2 or
    the downside deviation is 0 (an all-non-negative cohort has no downside risk — never a fabricated
    or total-vol number, anti-goal: Risk-adjusted reporting is honest)."""
    if len(returns) < 2:
        return None
    dd = _downside_deviation(returns)
    if dd == 0:
        return None
    return mean(returns) / dd


def _average_ranks(values: list[float]) -> list[float]:
    """1-based average ranks (standard Spearman tie handling): tied values share the mean of the
    positions they span, so the rank transform is a permutation-invariant monotone encoding."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0] * len(values)  # placeholder ints; every position is assigned an average-rank float below
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        average_position = (i + j) / 2 + 1  # mean of the 1-based positions i+1 .. j+1
        for k in range(i, j + 1):
            ranks[order[k]] = average_position
        i = j + 1
    return ranks


def _pearson(xs: list[float], ys: list[float]) -> Optional[float]:
    """Pearson correlation of two equal-length series, or None when either side has zero variance
    (an undefined correlation — honest NA, never a fabricated 0)."""
    mx, my = mean(xs), mean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx == 0 or syy == 0:
        return None
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    return sxy / sqrt(sxx * syy)


def _rank_ic(pairs: list[tuple[float, float]]) -> dict:
    """Spearman rank information coefficient = Pearson correlation of the average-rank-transformed
    factor and realized return across all observations. `{value, n}`; `value` is None when n < 2 or a
    side has zero rank variance (honest NA, never a fabricated 0)."""
    n = len(pairs)
    if n < 2:
        return {"value": None, "n": n}
    factor_ranks = _average_ranks([p[0] for p in pairs])
    return_ranks = _average_ranks([p[1] for p in pairs])
    return {"value": _pearson(factor_ranks, return_ranks), "n": n}


# --------------------------------------------------------------------------------------------------
# Read-only per-observation builder (the SAME stored pool compute_forward_aggregates groups)
# --------------------------------------------------------------------------------------------------
def _extract_factor_value(res: ScannerResult, parsed: dict) -> Optional[float]:
    """The stored factor value for ONE result, read VERBATIM (no recomputation). For a typed column it
    is the `ScannerResult` attribute (the three score columns are never NULL; the iter-13 volatility-family
    columns `hv`/`vcp_contraction`/`downside_vol` MAY be NULL on short history → excluded below, never
    fabricated); for a component it is the `record_json[<block>]["components"]` entry named `<name>` -> its
    `raw` (None when missing or `available: false` — an excluded factor-NULL observation, never fabricated)."""
    if parsed["kind"] == "column":
        return getattr(res, parsed["column"])
    try:
        record = json.loads(res.record_json)
    except (ValueError, TypeError):
        return None
    block = record.get(parsed["block"]) if isinstance(record, dict) else None
    if not isinstance(block, dict):
        return None
    for component in block.get("components", []):
        if isinstance(component, dict) and component.get("name") == parsed["name"]:
            return component.get("raw")
    return None


def _factor_observations(session: Session, factor, horizon: int) -> list[dict]:
    """The read-only per-observation list for (factor, horizon): join each stored
    `ForwardReturn.realized_return` at this horizon to its stored `ScannerResult` (by `run_id` + ticker)
    and read the factor's stored value. SELECT-only against `ForwardReturn` + `ScannerResult`; it
    recomputes NO return and NO factor. This is the SAME observation pool
    `forward_testing.compute_forward_aggregates(horizon)` builds — observations with no realized return
    contribute nothing (n=0), and a factor-NULL observation is EXCLUDED (never bucketed). Each
    observation also carries the run's STORED `regime_label` (read verbatim from `scanner_runs`,
    mirroring `forward_testing.py` — the regime is never recomputed here; J-27)."""
    parsed = parse_factor_source(factor.source)
    fr_rows = session.exec(select(ForwardReturn).where(ForwardReturn.horizon == horizon)).all()
    ret_by_run_symbol = {(fr.run_id, fr.symbol): fr.realized_return for fr in fr_rows}
    runs_with_fr = sorted({fr.run_id for fr in fr_rows})
    results = (
        session.exec(select(ScannerResult).where(ScannerResult.run_id.in_(runs_with_fr))).all()
        if runs_with_fr else []
    )
    run_rows = (
        session.exec(select(ScannerRun).where(ScannerRun.id.in_(runs_with_fr))).all()
        if runs_with_fr else []
    )
    regime_by_run = {run.id: run.regime_label for run in run_rows}  # stored regime label, read VERBATIM

    observations: list[dict] = []
    for res in results:
        realized = ret_by_run_symbol.get((res.run_id, res.ticker))
        if realized is None:
            continue  # no realized return at this horizon for this stock (n=0 contribution)
        value = _extract_factor_value(res, parsed)
        if value is None:
            continue  # factor-NULL observation EXCLUDED (never bucketed) — honest, not fabricated
        observations.append({
            "run_id": res.run_id, "ticker": res.ticker, "factor": float(value), "return": realized,
            "regime": regime_by_run.get(res.run_id),  # stored regime label for the run (J-27)
        })
    return observations


def _deciles(ordered: list[dict], count: int, min_sample: int) -> list[dict]:
    """Split the factor-ascending `ordered` observations into `count` equal-count quantiles (deciles).
    Each row carries its `factor_min`/`factor_max`, `mean_return`, downside `risk_adjusted`, `n`, and a
    `low_sample` flag (`n < min_sample`). When there are fewer observations than `count`, the higher
    deciles are honest empty rows (`mean_return` None, `n` 0) — never fabricated buckets."""
    n = len(ordered)
    rows: list[dict] = []
    for d in range(1, count + 1):
        lo = (d - 1) * n // count
        hi = d * n // count
        members = ordered[lo:hi]
        returns = [m["return"] for m in members]
        rows.append({
            "decile": d,
            "factor_min": members[0]["factor"] if members else None,
            "factor_max": members[-1]["factor"] if members else None,
            "mean_return": mean(returns) if returns else None,
            "risk_adjusted": _risk_adjusted(returns),
            "n": len(members),
            "low_sample": len(members) < min_sample,
        })
    return rows


def _regime_effectiveness(observations: list[dict], cfg: Config, horizon: int) -> list[dict]:
    """The read-only by-regime effectiveness split (J-27): for EACH configured regime label (in
    `config.regime.labels` order — no hard-coded regime list) emit one row describing whether the factor
    still sorts forward returns WITHIN that market regime. Observations are grouped by their STORED
    regime label (read verbatim from `scanner_runs.regime_label` — recomputes no regime); each row
    carries the per-regime `n`, the `low_sample` flag (`n < walk_forward.min_sample`), the Spearman
    `rank_ic`, the raw top/bottom decile means from a PER-REGIME decile split (the same `_deciles`), and
    the long-short top-minus-bottom-decile `spread` both raw and downside-`risk_adjusted`. Both spreads
    are honest NA (None) when the regime is low-sample OR either decile leg is None — an all-non-negative
    top decile has no downside risk → `risk_adjusted_spread` None, NEVER a total-vol number. Every
    configured regime emits a row even at n=0 (an honest empty row — never omitted, never fabricated)."""
    fl = cfg.research.factor_lab
    wf = cfg.walk_forward
    rows: list[dict] = []
    for label in cfg.regime.labels:
        regime_obs = [o for o in observations if o["regime"] == label]
        n = len(regime_obs)
        low_sample = n < wf.min_sample
        # ascending by stored factor value with the SAME deterministic tie-break compute_factor_lab uses,
        # so the per-regime deciles reproduce (a regime's pool is a subset of the pooled, re-sorted).
        ordered = sorted(regime_obs, key=lambda o: (o["factor"], o["ticker"], o["run_id"]))
        deciles = _deciles(ordered, fl.deciles, wf.min_sample)
        top_mean, bottom_mean = deciles[-1]["mean_return"], deciles[0]["mean_return"]
        top_ra, bottom_ra = deciles[-1]["risk_adjusted"], deciles[0]["risk_adjusted"]
        spread = (
            top_mean - bottom_mean
            if not low_sample and top_mean is not None and bottom_mean is not None
            else None
        )
        risk_adjusted_spread = (
            top_ra - bottom_ra
            if not low_sample and top_ra is not None and bottom_ra is not None
            else None
        )
        rows.append({
            "regime": label,
            "n": n,
            "low_sample": low_sample,
            "rank_ic": _rank_ic([(o["factor"], o["return"]) for o in regime_obs]),
            "top_decile_mean": top_mean,
            "bottom_decile_mean": bottom_mean,
            "spread": spread,
            "risk_adjusted_spread": risk_adjusted_spread,
        })
    return rows


# --------------------------------------------------------------------------------------------------
# The single canonical Factor-Lab read (read-only aggregation of stored values)
# --------------------------------------------------------------------------------------------------
def compute_factor_lab(
    session: Session, factor_key: str, horizon: int, config: Optional[Config] = None
) -> dict:
    """The SINGLE canonical Factor-Lab analysis (Data Contract value, J-25) for `factor_key` at
    `horizon`. READS the stored factor value (typed column or `record_json` component `raw`, verbatim)
    joined to the stored realized return — it recomputes NO factor and NO return. Returns the resolved
    `factor` + `horizon` + the full config-driven `factors` catalog + `horizons` + `default_horizon` +
    `min_sample` + survivorship/descriptive labels + `n_total`, the decile table (`mean_return` +
    downside `risk_adjusted` + `n` per decile, ascending by factor value, deterministic tie-break by
    ticker+run), the Spearman `rank_ic` (`{value, n}`), and the `by_regime` effectiveness split (J-27 —
    per configured regime label: `n`, rank-IC, top/bottom decile means, and the raw + downside-risk-
    adjusted top-minus-bottom-decile spread, all from the SAME observation pool, regime read verbatim).
    Raises `ValueError` for an unknown factor (the API pre-validates -> 422)."""
    cfg = config or get_config()
    fl = cfg.research.factor_lab
    wf = cfg.walk_forward
    catalog = factor_catalog(cfg)

    factor = next((f for f in fl.factors if f.key == factor_key), None)
    if factor is None:
        raise ValueError(
            f"unknown factor {factor_key!r}; valid factors are {[f['key'] for f in catalog]}"
        )

    observations = _factor_observations(session, factor, horizon)
    # ascending by stored factor value; deterministic tie-break by (ticker, run_id) so deciles reproduce
    ordered = sorted(observations, key=lambda o: (o["factor"], o["ticker"], o["run_id"]))

    return {
        "factor": {
            "key": factor.key, "label": factor.label, "family": factor.family,
            "direction": factor.direction, "source": factor.source,
        },
        "horizon": horizon,
        "factors": catalog,
        "horizons": list(wf.horizons),
        "default_horizon": wf.default_horizon,
        "deciles_count": fl.deciles,
        "min_sample": wf.min_sample,
        "survivorship_bias": SURVIVORSHIP_BIAS_LABEL,
        "descriptive_caveat": RESEARCH_CAVEAT,
        "n_total": len(observations),
        "deciles": _deciles(ordered, fl.deciles, wf.min_sample),
        "rank_ic": _rank_ic([(o["factor"], o["return"]) for o in observations]),
        "by_regime": _regime_effectiveness(observations, cfg, horizon),
    }


# --------------------------------------------------------------------------------------------------
# Multi-factor combination cohorts (J-26) — read-only over the SAME stored pool. The HEADLINE `composite`
# cohort is a config-weighted COMPOSITE PERCENTILE-RANK BLEND of the conditions' STORED factor values (the
# top config-quantile of the blend); the exact AND-intersection rides along as the SECONDARY `strict_overlap`
# cohort. The composite is a deterministic ranking / GROUPING of stored values (the SAME read-only class as
# the J-25 decile sort) — it recomputes NO factor and NO return and is NOT a fitted/learned/ML model.
# --------------------------------------------------------------------------------------------------
def _combination_observations(session: Session, factors: list, horizon: int) -> list[dict]:
    """The read-only multi-factor per-observation pool for (`factors`, `horizon`): mirror
    `_factor_observations` but read EVERY referenced factor's stored value per result. SELECT-only against
    `ForwardReturn` + `ScannerResult`; it recomputes NO return and NO factor. An observation is kept ONLY
    when a realized return exists at this horizon AND every referenced factor is non-null — a NULL in ANY
    referenced factor EXCLUDES the observation (never fabricated), so the pool is a (possibly strict)
    subset of any single factor's `_factor_observations` pool. Each observation is
    `{run_id, ticker, return, values: {factor_key: float}}`."""
    parsed_by_key = {f.key: parse_factor_source(f.source) for f in factors}
    fr_rows = session.exec(select(ForwardReturn).where(ForwardReturn.horizon == horizon)).all()
    ret_by_run_symbol = {(fr.run_id, fr.symbol): fr.realized_return for fr in fr_rows}
    runs_with_fr = sorted({fr.run_id for fr in fr_rows})
    results = (
        session.exec(select(ScannerResult).where(ScannerResult.run_id.in_(runs_with_fr))).all()
        if runs_with_fr else []
    )

    observations: list[dict] = []
    for res in results:
        realized = ret_by_run_symbol.get((res.run_id, res.ticker))
        if realized is None:
            continue  # no realized return at this horizon for this stock (excluded, never fabricated)
        values: dict[str, float] = {}
        for key, parsed in parsed_by_key.items():
            value = _extract_factor_value(res, parsed)
            if value is None:
                break  # a NULL in ANY referenced factor EXCLUDES this observation (never fabricated)
            values[key] = float(value)
        else:  # ran without a break -> every referenced factor was non-null
            observations.append({
                "run_id": res.run_id, "ticker": res.ticker, "return": realized, "values": values,
            })
    return observations


def _quantile_cutoff(sorted_values: list[float], fraction: float) -> float:
    """Deterministic nearest-rank empirical quantile cutoff on ascending `sorted_values`: the value at
    1-based rank `ceil(fraction * n)` (clamped to [1, n]). Tie-tolerant — the caller's `>=`/`<=` boundary
    test INCLUDES values equal to the cutoff, so a cohort may be marginally larger than `fraction · n`
    (honest, documented). A fixed statistical RULE, not a tunable — only `fraction` comes from config, so
    no magic number is introduced (the structural 1's are rank/index arithmetic, not thresholds)."""
    n = len(sorted_values)
    rank = max(1, min(ceil(fraction * n), n))
    return sorted_values[rank - 1]


def _cohort_stats(returns: list[float], min_sample: int) -> dict:
    """Per-cohort descriptive stats over the member realized returns (read-only): raw `mean_return`,
    `median_return`, `hit_rate` (fraction of returns `> 0`), the downside-only `risk_adjusted` (REUSE
    `_risk_adjusted` — `mean / downside_deviation`, never total volatility), `n`, and the `low_sample`
    flag (`n < min_sample`, reusing `walk_forward.min_sample`). An EMPTY cohort yields `None` for every
    figure (NA) — never a fabricated 0."""
    n = len(returns)
    return {
        "n": n,
        "mean_return": mean(returns) if returns else None,
        "median_return": median(returns) if returns else None,
        "hit_rate": (sum(1 for r in returns if r > 0) / n) if returns else None,
        "risk_adjusted": _risk_adjusted(returns),
        "low_sample": n < min_sample,
    }


def _condition_payload(cond: dict) -> dict:
    """Serialize a resolved condition (factor object + side + quantile object) into its JSON payload
    shape: the full catalog factor descriptor, the `side`, and the resolved quantile `{key, label,
    fraction}` — the same vocabulary the frontend's factor/quantile dropdowns render."""
    factor = cond["factor"]
    quantile = cond["quantile"]
    return {
        "factor": {
            "key": factor.key, "label": factor.label, "family": factor.family,
            "direction": factor.direction, "source": factor.source,
        },
        "side": cond["side"],
        "quantile": {"key": quantile.key, "label": quantile.label, "fraction": quantile.fraction},
    }


def _percentile_rank_fractions(values: list[float]) -> list[float]:
    """Each value's percentile rank as a fraction in (0, 1] — the 1-based average rank (REUSE
    `_average_ranks`, standard Spearman tie handling) divided by n. A pure, monotone re-encoding /
    GROUPING of the STORED values (the SAME read-only operation the J-25 decile sort performs) — it
    recomputes NO factor and is NOT a fitted model. Empty in -> empty out. Used to build the composite
    rank-blend below; no threshold or magic number is introduced (the only arithmetic is rank / n)."""
    n = len(values)
    if not n:
        return []
    return [rank / n for rank in _average_ranks(values)]


def _composite_scores(pool: list[dict], resolved: list[dict], weights: list[float]) -> list[float]:
    """The config-weighted COMPOSITE percentile-rank score per pool observation (J-26 headline blend). For
    EACH condition (a catalog factor at a `top`/`bottom` side) percentile-rank that condition's STORED
    factor value within the pool (REUSE `_percentile_rank_fractions`), ORIENT it by the user's `side`
    (`top` keeps the fraction so a HIGH stored value scores high; `bottom` uses `1 − fraction` so a LOW
    stored value scores high — exactly how the single-condition cohorts are oriented; the catalog
    `direction`/`family` stay descriptive and never flip the blend), then take the `weights`-weighted mean
    across the conditions (`weights` sum to 1, normalized by the caller from config — no `1/k` literal
    here). A deterministic ranking / GROUPING of stored values — NOT a fitted/learned/ML model and NOT a
    recomputed factor. NOTE a CONDITION (factor+side), not a distinct factor, contributes a rank: a factor
    used in two conditions (the opposing-extremes fixture) contributes two oriented ranks (which average to
    a flat 0.5 — the blend then has no differentiating signal, honestly selecting the whole pool)."""
    oriented_by_condition: list[list[float]] = []
    for cond in resolved:
        key = cond["factor"].key
        fractions = _percentile_rank_fractions([obs["values"][key] for obs in pool])
        oriented_by_condition.append(
            [frac if cond["side"] == "top" else 1 - frac for frac in fractions]
        )
    return [
        sum(weight * oriented[i] for weight, oriented in zip(weights, oriented_by_condition))
        for i in range(len(pool))
    ]


def compute_factor_combination(
    session: Session, conditions: list[dict], horizon: int, config: Optional[Config] = None
) -> dict:
    """The SINGLE canonical multi-factor combination read (Data Contract value, J-26). Each condition is a
    catalog factor at its `top`/`bottom` `quantile`. The HEADLINE `composite` cohort (iter-18 re-scope) is
    the top config-quantile of the pool by a config-weighted COMPOSITE PERCENTILE-RANK BLEND of the
    conditions' STORED factor values — so combining factors yields a real, sample-sufficient cohort (non-
    empty + clears `min_sample` for a sensible selection) that scales to ALL catalog factors, instead of the
    perpetually-0/NA strict intersection. The exact AND-intersection of the single-condition memberships is
    retained as the SECONDARY `strict_overlap` cohort (NA + n when empty — never a fabricated 0). Both ride
    beside the unconditional `baseline` (the whole pool) and each `single` cohort so factor INTERACTION is
    visible. READS the stored factor values (typed column or `record_json` component `raw`, verbatim)
    joined to the stored realized return via `_combination_observations` — it recomputes NO factor and NO
    return (SELECT + pure grouping/ranking only; calls no run_scan/score_stocks/backfill*/forward_return/
    detect_*/score_regime). The composite is a DETERMINISTIC ranking/GROUPING of stored values (the SAME
    read-only class as the J-25 decile sort) — it is NOT a fitted/learned/ML model.

    `conditions` is a list of `{factor: <key>, side: 'top'|'bottom', quantile: <key>}` dicts. Each
    single-condition quantile membership uses a deterministic nearest-rank cutoff over the SHARED pool's
    values for that factor: `top` -> value >= cutoff(1 − fraction); `bottom` -> value <= cutoff(fraction);
    boundary ties included. The composite blends, per condition, the observation's percentile rank of that
    condition's stored value (oriented by `side`), config-weighted (default equal — every tunable from
    config), and takes the top `composite.quantile` of the blend. Per-cohort stats reuse the downside-only
    `_risk_adjusted`; an empty/low-sample cohort shows NA + `n`, never a fabricated number. The pool
    requires ALL referenced factors non-null, so `pool_n` is a (possibly strict) subset of any single
    factor's `_factor_observations` n. Raises `ValueError` for an unknown factor/side/quantile or an
    out-of-range condition count (the API pre-validates -> 422)."""
    cfg = config or get_config()
    fl = cfg.research.factor_lab
    comb = fl.combination
    wf = cfg.walk_forward
    catalog = factor_catalog(cfg)
    min_sample = wf.min_sample

    if not (comb.min_conditions <= len(conditions) <= comb.max_conditions):
        raise ValueError(
            f"condition count {len(conditions)} out of range "
            f"[{comb.min_conditions}, {comb.max_conditions}]"
        )

    resolved: list[dict] = []
    for cond in conditions:
        factor = next((f for f in fl.factors if f.key == cond.get("factor")), None)
        if factor is None:
            raise ValueError(
                f"unknown factor {cond.get('factor')!r}; valid factors are {[c['key'] for c in catalog]}"
            )
        side = cond.get("side")
        if side not in ("top", "bottom"):
            raise ValueError(f"unknown side {side!r}; valid sides are ['bottom', 'top']")
        quantile = next((q for q in comb.quantiles if q.key == cond.get("quantile")), None)
        if quantile is None:
            raise ValueError(
                f"unknown quantile {cond.get('quantile')!r}; valid quantiles are "
                f"{[q.key for q in comb.quantiles]}"
            )
        resolved.append({"factor": factor, "side": side, "quantile": quantile})

    # the DISTINCT referenced factors (a factor MAY appear in >1 condition — e.g. top AND bottom of the
    # same factor, the opposing-extremes NA fixture). The pool requires every one of them non-null.
    distinct_factors = list({c["factor"].key: c["factor"] for c in resolved}.values())
    pool = _combination_observations(session, distinct_factors, horizon)
    pool_n = len(pool)

    # per-condition membership (a set of pool indices) using each condition's nearest-rank quantile cutoff
    # over the SHARED pool's values for that factor; strict_overlap = the exact AND-intersection of singles.
    single_members: list[set[int]] = []
    for cond in resolved:
        key = cond["factor"].key
        fraction = cond["quantile"].fraction
        ordered = sorted(obs["values"][key] for obs in pool)
        if not ordered:
            single_members.append(set())
            continue
        if cond["side"] == "top":
            cutoff = _quantile_cutoff(ordered, 1 - fraction)
            members = {i for i, obs in enumerate(pool) if obs["values"][key] >= cutoff}
        else:  # bottom
            cutoff = _quantile_cutoff(ordered, fraction)
            members = {i for i, obs in enumerate(pool) if obs["values"][key] <= cutoff}
        single_members.append(members)

    # SECONDARY strict-overlap cohort: the exact AND-intersection of all single memberships (the demoted
    # iter-12 cohort) — empty for many selections (then NA + n, never a fabricated 0).
    strict_members: set[int] = set(range(pool_n))
    for members in single_members:
        strict_members &= members

    # HEADLINE composite cohort: the top config-quantile of the pool by a config-weighted blend of the
    # conditions' oriented percentile ranks of the STORED values (REUSE `_composite_scores` +
    # `_quantile_cutoff`). Config-weighted (default equal): each condition's base weight is the config
    # `default_weight`, normalized to sum to 1 — so NO `1/k` weight literal lives here (anti-goal: No magic
    # numbers). Non-empty + clears `min_sample` for a sensible selection; scales to all catalog factors.
    comp = comb.composite
    composite_quantile = next(q for q in comb.quantiles if q.key == comp.quantile)  # boot-validated to exist
    base_weights = [comp.weighting.default_weight] * len(resolved)
    weight_total = sum(base_weights)
    weights = [w / weight_total for w in base_weights]
    composite_scores = _composite_scores(pool, resolved, weights)
    if composite_scores:
        cutoff = _quantile_cutoff(sorted(composite_scores), 1 - composite_quantile.fraction)
        composite_members = {i for i, score in enumerate(composite_scores) if score >= cutoff}
    else:
        composite_members = set()

    def _returns(indices) -> list[float]:
        return [pool[i]["return"] for i in sorted(indices)]

    resolved_conditions = [_condition_payload(c) for c in resolved]

    return {
        "conditions": resolved_conditions,
        "horizon": horizon,
        "horizons": list(wf.horizons),
        "default_horizon": wf.default_horizon,
        "min_sample": min_sample,
        "min_conditions": comb.min_conditions,
        "max_conditions": comb.max_conditions,
        "factors": catalog,
        "quantiles": [{"key": q.key, "label": q.label, "fraction": q.fraction} for q in comb.quantiles],
        # echo the resolved composite quantile + weighting so the UI labels the blend honestly (transparent,
        # config-driven — not a hard-coded UI string).
        "composite_quantile": {
            "key": composite_quantile.key,
            "label": composite_quantile.label,
            "fraction": composite_quantile.fraction,
        },
        "weighting": {"scheme": comp.weighting.scheme, "default_weight": comp.weighting.default_weight},
        "survivorship_bias": SURVIVORSHIP_BIAS_LABEL,
        "descriptive_caveat": RESEARCH_CAVEAT,
        "pool_n": pool_n,
        "baseline": {
            "label": "Baseline (all names)",
            "stats": _cohort_stats(_returns(range(pool_n)), min_sample),
        },
        "singles": [
            {"condition": rc, "stats": _cohort_stats(_returns(single_members[i]), min_sample)}
            for i, rc in enumerate(resolved_conditions)
        ],
        # HEADLINE: the composite rank-blend cohort (non-empty for a sensible selection).
        "composite": {
            "label": "Combined (composite rank-blend)",
            "stats": _cohort_stats(_returns(composite_members), min_sample),
        },
        # SECONDARY: the exact AND-intersection (NA + n when empty, never a fabricated 0).
        "strict_overlap": {
            "label": "Strict overlap (AND)",
            "stats": _cohort_stats(_returns(strict_members), min_sample),
        },
    }


# --------------------------------------------------------------------------------------------------
# Setup & Pattern event study (J-29) — read-only pooled cross-snapshot analytic over stored values
# --------------------------------------------------------------------------------------------------
def subject_catalog(cfg: Config) -> list[dict]:
    """The ordered, config-driven event-study subject catalog: one `{key, label, kind}` per subject —
    every setup status (`setups.ALL_STATUSES`, kind "setup") followed by every detected pattern
    (`config.patterns` keys, kind "pattern"). Labels REUSE the single config-backed methodology copy
    (`config.methodology.entries[*].name`), falling back to the key, so an added setup/pattern appears
    in the subject selector automatically with NO frontend edit (anti-goal: config-driven vocabulary in
    the UI too). The frontend subject selector AND the API default subject are built from THIS list."""
    label_by_key = {entry.key: entry.name for entry in cfg.methodology.entries}
    subjects = [
        {"key": status, "label": label_by_key.get(status, status), "kind": "setup"}
        for status in ALL_STATUSES
    ]
    subjects += [
        {"key": key, "label": label_by_key.get(key, key), "kind": "pattern"}
        for key in cfg.patterns.model_dump()
    ]
    return subjects


def _subject_member(res: ScannerResult, subject: dict) -> bool:
    """Whether a stored result belongs to the subject's pooled cohort, read VERBATIM from the snapshot
    (never re-classified): a SETUP subject pools `scanner_results.setup_status == key`; a PATTERN subject
    pools the stored mirror flag `is_<key>` being True — the SAME `by_<name>` stored-mirror grouping
    convention `forward_testing` already uses for is_vcp / is_pullback_to_rising_dma / is_flat_base_breakout."""
    if subject["kind"] == "setup":
        return res.setup_status == subject["key"]
    return bool(getattr(res, f"is_{subject['key']}"))


def _event_study_members(session: Session, subject: dict, horizon: int) -> list[dict]:
    """The read-only per-observation pool for (subject, horizon): join each stored `ForwardReturn` at this
    horizon (its `realized_return` + `mae` + `mfe`, read VERBATIM) to its stored `ScannerResult` (by
    run_id + ticker) and the run's stored `regime_label`, keeping ONLY the subject's members. SELECT-only
    against `ForwardReturn` + `ScannerResult` + `ScannerRun`; it recomputes NO return / excursion / score /
    regime / pattern. This pools the SAME per-observation rows `compute_forward_aggregates`'s `by_setup` /
    `by_<pattern>` group (the consistency invariant is unit-asserted). A member with no realized return at
    this horizon contributes nothing (n=0)."""
    fr_rows = session.exec(select(ForwardReturn).where(ForwardReturn.horizon == horizon)).all()
    fr_by_run_symbol = {(fr.run_id, fr.symbol): fr for fr in fr_rows}
    runs_with_fr = sorted({fr.run_id for fr in fr_rows})
    results = (
        session.exec(select(ScannerResult).where(ScannerResult.run_id.in_(runs_with_fr))).all()
        if runs_with_fr else []
    )
    run_rows = (
        session.exec(select(ScannerRun).where(ScannerRun.id.in_(runs_with_fr))).all()
        if runs_with_fr else []
    )
    regime_by_run = {run.id: run.regime_label for run in run_rows}  # stored regime label, read VERBATIM

    members: list[dict] = []
    for res in results:
        if not _subject_member(res, subject):
            continue
        fr = fr_by_run_symbol.get((res.run_id, res.ticker))
        if fr is None:
            continue  # no realized return at this horizon for this member (n=0 contribution)
        members.append({
            "run_id": res.run_id, "ticker": res.ticker,
            "return": fr.realized_return, "mae": fr.mae, "mfe": fr.mfe,
            "regime": regime_by_run.get(res.run_id),  # stored regime label (read verbatim)
            "sector": res.sector,                     # stored sector (read verbatim)
        })
    return members


def _expectancy(returns: list[float]) -> dict:
    """Per-occurrence expectancy with its decomposition over the member returns: `win_rate` (fraction
    `> 0`), `avg_win` (mean of returns `> 0`; None when no win), `avg_loss` (mean of returns `<= 0`,
    negative; None when no loss), and `expectancy` = `win_rate*avg_win + (1-win_rate)*avg_loss` — which
    equals the plain mean (asserted in tests). Empty -> all None (honest NA, never a fabricated 0). The
    `> 0` win / loss boundary is a fixed structural rule (like `_distribution.pct_positive`), not a tunable."""
    n = len(returns)
    if n == 0:
        return {"win_rate": None, "avg_win": None, "avg_loss": None, "expectancy": None}
    wins = [r for r in returns if r > 0]
    losses = [r for r in returns if r <= 0]
    win_rate = len(wins) / n
    avg_win = mean(wins) if wins else None
    avg_loss = mean(losses) if losses else None
    expectancy = (
        (win_rate * avg_win if avg_win is not None else 0)
        + ((1 - win_rate) * avg_loss if avg_loss is not None else 0)
    )
    return {"win_rate": win_rate, "avg_win": avg_win, "avg_loss": avg_loss, "expectancy": expectancy}


def _return_per_mae(returns: list[float], maes: list[float]) -> Optional[float]:
    """Mean return per unit mean-|MAE| (`mean_return / mean(|mae|)`) — the J-30-deferred MAE-risk ratio
    the new stored excursions enable, downside-by-construction (MAE is the adverse leg, never total
    volatility). NA (None) when n < 2 or `mean(|mae|) == 0` (no adverse excursion) — never fabricated."""
    if len(returns) < 2 or not maes:
        return None
    mean_abs_mae = mean(abs(m) for m in maes)
    if mean_abs_mae == 0:
        return None
    return mean(returns) / mean_abs_mae


def _event_study_horizon_row(members: list[dict], horizon: int, min_sample: int) -> dict:
    """One per-horizon row of the event study over the subject's pooled members: the distribution (mean /
    median / %positive / dispersion, REUSING `forward_testing._distribution`), the expectancy
    decomposition, the mean stored MAE / MFE excursions (read VERBATIM, never recomputed), and BOTH
    downside-only risk-adjusted ratios (return/downside-dev REUSING `_risk_adjusted`; return/mean-|MAE|),
    each beside the raw mean. Carries `n` + `low_sample` (`n < min_sample`). The engine computes every
    figure; the UI gates low-sample/empty cells to NA + n. NO total volatility anywhere (anti-goal:
    risk-adjusted reporting must not conflate up/down volatility)."""
    returns = [m["return"] for m in members]
    maes = [m["mae"] for m in members if m["mae"] is not None]
    mfes = [m["mfe"] for m in members if m["mfe"] is not None]
    n = len(returns)
    dist = _distribution(returns)  # {mean_return, median, pct_positive, dispersion, n}
    return {
        "horizon": horizon,
        "n": n,
        "low_sample": n < min_sample,
        "mean_return": dist["mean_return"],
        "median": dist["median"],
        "pct_positive": dist["pct_positive"],
        "dispersion": dist["dispersion"],
        "expectancy": _expectancy(returns),
        "mean_mae": _mean_or_none(maes),
        "mean_mfe": _mean_or_none(mfes),
        "return_per_downside_dev": _risk_adjusted(returns),
        "return_per_mae": _return_per_mae(returns, maes),
    }


def _best_exit_horizon(by_horizon: list[dict]) -> Optional[int]:
    """The argmax horizon among the NON-low-sample horizons of the primary metric — the downside
    risk-adjusted `return_per_downside_dev`, falling back to the raw `mean_return` when it is NA. NA
    (None) when EVERY horizon is low-sample (honest — never a fabricated 'best' on thin evidence)."""
    best_horizon: Optional[int] = None
    best_metric: Optional[float] = None
    for row in by_horizon:
        if row["low_sample"]:
            continue
        metric = row["return_per_downside_dev"]
        if metric is None:
            metric = row["mean_return"]
        if metric is None:
            continue
        if best_metric is None or metric > best_metric:
            best_metric = metric
            best_horizon = row["horizon"]
    return best_horizon


def _event_study_by_regime(members: list[dict], cfg: Config) -> list[dict]:
    """The by-regime slice at the selected horizon: one row per CONFIGURED regime label
    (`config.regime.labels` order — no hard-coded regime list, mirroring `_regime_effectiveness`'s
    every-label discipline), each with its per-regime `n`, `low_sample`, `mean_return`, `hit_rate`
    (fraction `> 0`), and downside `risk_adjusted` (REUSE `_risk_adjusted`). Members are grouped by their
    STORED regime label (read verbatim). Every label emits a row even at n=0 (honest NA — never omitted),
    and Σ per-regime `n` == the pooled member count (every member carries exactly one configured label) —
    the consistency invariant (unit-asserted)."""
    min_sample = cfg.walk_forward.min_sample
    by_label: dict[str, list[float]] = defaultdict(list)
    for member in members:
        by_label[member["regime"]].append(member["return"])
    rows: list[dict] = []
    for label in cfg.regime.labels:
        returns = by_label.get(label, [])
        n = len(returns)
        rows.append({
            "regime": label,
            "n": n,
            "low_sample": n < min_sample,
            "mean_return": _mean_or_none(returns),
            "hit_rate": (sum(1 for r in returns if r > 0) / n) if returns else None,
            "risk_adjusted": _risk_adjusted(returns),
        })
    return rows


def _event_study_by_sector(members: list[dict], cfg: Config) -> list[dict]:
    """The by-sector slice at the selected horizon: one row per STORED `scanner_results.sector` that has
    members (config sector-name order first, then any extras sorted — NON-padded, mirroring
    `_attribution_slices.by_sector`), each with its per-sector `n`, `low_sample`, `mean_return`, and
    downside `risk_adjusted` (REUSE `_risk_adjusted`). Sectors with no members do not appear; a thin
    sector shows honest NA + n (low_sample)."""
    min_sample = cfg.walk_forward.min_sample
    sector_order = list(cfg.etfs.sector.values())  # config sector NAMES (never a literal sector list)
    by_sector: dict[str, list[float]] = defaultdict(list)
    for member in members:
        if member["sector"] is not None:
            by_sector[member["sector"]].append(member["return"])

    def _row(sector: str, returns: list[float]) -> dict:
        return {
            "sector": sector,
            "n": len(returns),
            "low_sample": len(returns) < min_sample,
            "mean_return": _mean_or_none(returns),
            "risk_adjusted": _risk_adjusted(returns),
        }

    rows: list[dict] = []
    emitted: set = set()
    for sector in sector_order:
        if sector in by_sector:
            rows.append(_row(sector, by_sector[sector]))
            emitted.add(sector)
    for sector in sorted(by_sector):
        if sector not in emitted:
            rows.append(_row(sector, by_sector[sector]))
    return rows


def compute_event_study(
    session: Session, subject_key: str, horizon: int, config: Optional[Config] = None
) -> dict:
    """The SINGLE canonical Setup & Pattern event study (Data Contract value, J-29) for `subject_key` at
    the selected `horizon`. Pools EVERY historical occurrence of the subject (a setup OR a detected
    pattern) across all immutable snapshots and reports, per configured horizon, the forward-return
    distribution (mean / median / %positive / dispersion) + expectancy + mean MAE / MFE + the downside-
    only risk-adjusted ratios (return/downside-dev AND return/mean-|MAE|), plus the best exit-horizon and
    the by-regime + by-sector slices at the selected horizon — each carrying `n` and honest NA.

    READ-ONLY (the keystone anti-goal): derived ENTIRELY from stored values — `forward_returns`
    (`realized_return` + the iter-14 `mae` / `mfe`, read VERBATIM) JOINED to the stored `scanner_results`
    (setup status + the pattern mirror flags) and `scanner_runs.regime_label` (verbatim). It issues ONLY
    SELECTs and pure stats; it calls NO scoring / regime / return / excursion / pattern math (no run_scan,
    score_stocks, backfill*, forward_return, forward_excursions, detect_*, score_regime). It pools the SAME
    per-observation rows `compute_forward_aggregates` groups, so the pooled mean for a subject at horizon h
    equals the matching `by_setup` / `by_<pattern>` cohort mean (the consistency invariant, unit-asserted).
    Risk is downside-only everywhere (never total volatility). Raises `ValueError` for an unknown subject
    (the API pre-validates -> 422)."""
    cfg = config or get_config()
    wf = cfg.walk_forward
    subjects = subject_catalog(cfg)

    subject = next((s for s in subjects if s["key"] == subject_key), None)
    if subject is None:
        raise ValueError(
            f"unknown subject {subject_key!r}; valid subjects are {[s['key'] for s in subjects]}"
        )

    by_horizon: list[dict] = []
    selected_members: Optional[list[dict]] = None
    for h in wf.horizons:
        members = _event_study_members(session, subject, h)
        by_horizon.append(_event_study_horizon_row(members, h, wf.min_sample))
        if h == horizon:
            selected_members = members
    if selected_members is None:  # horizon not in wf.horizons (API validates; defensive for direct calls)
        selected_members = _event_study_members(session, subject, horizon)

    return {
        "subject": subject,
        "horizon": horizon,
        "subjects": subjects,
        "horizons": list(wf.horizons),
        "default_horizon": wf.default_horizon,
        "min_sample": wf.min_sample,
        "survivorship_bias": SURVIVORSHIP_BIAS_LABEL,
        "descriptive_caveat": RESEARCH_CAVEAT,
        "n_total": len(selected_members),
        "by_horizon": by_horizon,
        "best_exit_horizon": _best_exit_horizon(by_horizon),
        "by_regime": _event_study_by_regime(selected_members, cfg),
        "by_sector": _event_study_by_sector(selected_members, cfg),
    }
