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
from math import sqrt
from statistics import mean
from typing import Optional

from sqlmodel import Session, select

from app.config import Config, get_config, parse_factor_source
from app.engine.forward_testing import SURVIVORSHIP_BIAS_LABEL
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
    is the `ScannerResult` attribute (never NULL); for a component it is the `record_json[<block>]
    ["components"]` entry named `<name>` -> its `raw` (None when missing or `available: false` — an
    excluded factor-NULL observation, never fabricated)."""
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
