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
     The optional **as-of mode** (iter-19, J-32 — the iter-17 `compute_forward_aggregates` seam verbatim)
     is a pure membership FILTER on the opening `ForwardReturn` query: when `as_of=D` is set it keeps ONLY
     snapshots with `ScannerRun.asof_date <= D` (a point-in-time / walk-forward view — no run dated > D
     contributes); `as_of=None` adds NO clause → byte-identical all-history. It recomputes nothing — the
     mode merely scopes WHICH stored observations are pooled (anti-goal: Research lab as-of mode FILTERS,
     never recomputes a figure).

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
import logging
import threading
from collections import defaultdict
from datetime import date as date_cls
from datetime import datetime, timezone
from math import ceil, sqrt
from statistics import mean, median
from typing import Optional

from sqlalchemy import func
from sqlmodel import Session, select

from app.config import (
    VELOCITY_SIGN_FALLING,
    VELOCITY_SIGN_FLAT,
    VELOCITY_SIGN_RISING,
    Config,
    get_config,
    parse_factor_source,
)
from app.engine.forward_testing import (
    SURVIVORSHIP_BIAS_LABEL,
    _distribution,
    _mean_or_none,
)
from app.engine.setups import ALL_STATUSES
from app.models import DailyPrice, EventStudyCache, ForwardReturn, ScannerResult, ScannerRun

# ops-hardening iter-31 (AG-8) — the all-factors Factor-Lab return-value pool-bound WARNING (never raised,
# never truncates a payload — see `_all_factor_observations_by_horizon`) and the `factor_lab_all_cached`
# single-flight guard's failure-path fallback both log through this, mirroring the established
# "trendora.<module>" convention (`data_manager.py`, `forward_testing.py`, `evidence.py`).
logger = logging.getLogger("trendora.research")

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


def _runs_with_fr(
    session: Session, horizons: list[int], as_of: Optional[date_cls],
) -> list[int]:
    """The sorted DISTINCT `forward_returns.run_id`s carrying a return at ANY of `horizons` — the chunk axis
    BOTH factor-observation builders walk (`_factor_observations` passes a single-horizon list;
    `_all_factor_observations_by_horizon` passes every config horizon). A DISTINCT-projected read, so the
    returned list is bounded by the RUN count (1,812-1,871 live) and never by the (run_id, symbol) PAIR count
    the join accumulators used to materialize whole (AG-8).

    `as_of` (J-32) scopes membership to snapshots with `ScannerRun.asof_date <= as_of`; `as_of=None` adds NO
    clause -> byte-identical all-history. Applying the cutoff HERE, upstream of every derived structure,
    is what keeps the per-slice reads below (which filter only on `run_id.in_(slice)`) no-lookahead-correct:
    a run dated after D never enters `runs_with_fr`, so it can never enter a slice."""
    stmt = select(ForwardReturn.run_id).where(ForwardReturn.horizon.in_(horizons))
    if as_of is not None:
        stmt = stmt.join(ScannerRun, ScannerRun.id == ForwardReturn.run_id).where(
            ScannerRun.asof_date <= as_of
        )
    return sorted(session.exec(stmt.distinct()).all())


def _fr_slice_map(
    session: Session, horizon: int, slice_run_ids: list[int], batch: int,
) -> dict[tuple[int, str], tuple[float, Optional[float]]]:
    """iter-29 (AG-8): the `(run_id, symbol) -> (realized_return, max_drawdown)` join map for ONE bounded
    SLICE of run ids — `_factor_observations`'s chunk axis. Column-projected + `yield_per`-streamed exactly
    like the pre-chunk single-pass read; the only difference is the added `run_id.in_(slice_run_ids)`
    scope, which is what bounds this dict's LIVE size to (len(slice_run_ids) x symbols-per-run) instead of
    the full horizon's distinct (run_id, symbol) pair count (803,042 measured live at iter-28, one horizon,
    as_of=None — an unbounded whole-history materialization in substance, since the prior accumulator held
    one entry per pair across ALL of `runs_with_fr` at once). A named function (not an inlined loop body)
    so a test can wrap/instrument it to observe the live per-slice size directly (TC-1)."""
    fr_stmt = select(
        ForwardReturn.run_id, ForwardReturn.symbol, ForwardReturn.realized_return, ForwardReturn.max_drawdown
    ).where(ForwardReturn.horizon == horizon, ForwardReturn.run_id.in_(slice_run_ids))
    ret_by_run_symbol: dict[tuple[int, str], tuple[float, Optional[float]]] = {}
    for run_id, symbol, realized_return, max_drawdown in session.exec(fr_stmt).yield_per(batch):
        ret_by_run_symbol[(run_id, symbol)] = (realized_return, max_drawdown)
    return ret_by_run_symbol


def _factor_observations(
    session: Session, factor, horizon: int, as_of: Optional[date_cls] = None,
    *, cfg: Optional[Config] = None,
) -> list[dict]:
    """The read-only per-observation list for (factor, horizon): join each stored
    `ForwardReturn.realized_return` at this horizon to its stored `ScannerResult` (by `run_id` + ticker)
    and read the factor's stored value. SELECT-only against `ForwardReturn` + `ScannerResult`; it
    recomputes NO return and NO factor. This is the SAME observation pool
    `forward_testing.compute_forward_aggregates(horizon)` builds — observations with no realized return
    contribute nothing (n=0), and a factor-NULL observation is EXCLUDED (never bucketed). Each
    observation also carries the run's STORED `regime_label` (read verbatim from `scanner_runs`,
    mirroring `forward_testing.py` — the regime is never recomputed here; J-27).

    `as_of` (iter-19, J-32) optionally scopes the pool to the EXPANDING WALK-FORWARD WINDOW: when set,
    ONLY snapshots with `ScannerRun.asof_date <= as_of` contribute (no run dated > D leaks). It is a
    SINGLE membership filter on the `runs_with_fr` discovery step below — identical to `forward_testing.py`
    — so it equally bounds `runs_with_fr`, every chunk's `results`, `run_rows`, and the regime map (all
    derived from it). The cutoff is the canonical `ScannerRun.asof_date` (not the denormalized
    `ForwardReturn.asof_date`). `as_of=None` adds NO clause → byte-identical all-history.

    iter-29 (AG-8): the join accumulator used to be ONE dict holding every distinct (run_id, symbol) pair
    across the FULL horizon's history at once (803,042 pairs measured live at iter-28, as_of=None) even
    though the SOURCE query was already `yield_per`-streamed — an unbounded whole-history materialization
    in substance. `runs_with_fr` is now discovered via a lightweight DISTINCT-projected query (bounded by
    run count, never by pair count), then walked in bounded SLICES of `research.factor_join_run_chunk` run
    ids: each slice rebuilds its own `_fr_slice_map` accumulator, streams+joins that slice's
    `ScannerResult`s, extends `observations`, and discards the slice's dict before the next — so peak LIVE
    accumulator size is bounded by (chunk x symbols-per-run), never by the full history. Slices walk the
    sorted `runs_with_fr` list in non-overlapping, increasing contiguous ranges, so concatenating each
    slice's (run_id, id)-ordered `ScannerResult` output reproduces the SAME global order the prior
    single-pass implementation produced — byte-identical (TC-2), never re-derived.

    iter-29 AUDIT: the chunk width is `research.factor_join_run_chunk` (a RUN COUNT), NOT `read_batch_size`
    (a ROW count for `yield_per`). As first shipped this loop reused the row knob (2000) as its run width,
    and with only 1,812-1,871 distinct runs per horizon on the live basis it produced exactly ONE chunk —
    a bound that bound nothing (792,507-entry peak at h=20, 0% below the pre-fix figure). The two knobs are
    now separate so the accumulator width can be sized against the RUN count it actually indexes."""
    parsed = parse_factor_source(factor.source)
    # iter-47 (J-105): column-project + stream the (possibly huge) forward-return scan so the read path is
    # bounded by config (`yield_per`) instead of materializing the whole table as ORM rows. We read only the
    # three fields the join consumes (run_id, symbol, realized_return) — projected Row values are the EXACT
    # same Python types as ORM attribute access (no coercion → byte-identical served value).
    research_cfg = (cfg or get_config()).research
    batch = research_cfg.read_batch_size
    # iter-29 AUDIT (AG-8): the accumulator chunk width is a RUN COUNT, read from its OWN config key —
    # `read_batch_size` counts ROWS (the `yield_per` size above) and reusing it here as a run width made the
    # bound inert on the live basis (2000 runs/chunk vs 1,812-1,871 real runs -> one chunk, no reduction).
    run_chunk = research_cfg.factor_join_run_chunk

    # iter-29 (AG-8): the distinct run ids at this horizon, via the shared DISTINCT-projected discovery —
    # bounded by run count, never by (run, symbol) pair count (the dimension `_fr_slice_map` below chunks
    # over). The `as_of` cutoff lives in that ONE helper, so both builders scope membership identically.
    runs_with_fr = _runs_with_fr(session, [horizon], as_of)
    run_rows = (
        session.exec(select(ScannerRun).where(ScannerRun.id.in_(runs_with_fr))).all()
        if runs_with_fr else []
    )
    regime_by_run = {run.id: run.regime_label for run in run_rows}  # stored regime label, read VERBATIM

    # iter-48 (J-105): stream the (possibly ~609K-row) ScannerResult side with `yield_per` instead of an
    # unbounded `.all()` materialization (the live factor-lab MemoryError site, research.py:216 pre-fix).
    # We stream the FULL ORM row — NOT a narrow column projection — because `_extract_factor_value` reads
    # `res.record_json` for a COMPONENT factor; dropping it would silently change figures. We order by
    # `(run_id, id)` — the EXACT order the prior implicit `.all()` produced on the `run_id IN (...)` filter
    # (SQLite walks the `ix_scanner_results_run_id` index, so rows already arrive grouped by run_id then id)
    # — so every observation/decile/rank-IC/by_regime figure is byte-identical. Ordering by `(run_id, id)`
    # rides that SAME index (no `USE TEMP B-TREE FOR ORDER BY`), so the sort never spills a temp file to a
    # nearly-full disk; a bare `ORDER BY id` would force a full temp-B-tree sort over ~598K rows that can
    # exhaust disk. Factor Lab is UNCACHED (recomputes every request) → this is the genuine OOM site.
    #
    # iter-29 (AG-8): this scan now runs PER CHUNK (`runs_with_fr[start:start+run_chunk]`), scoped by the
    # SAME `run_id.in_(slice_run_ids)` filter every chunk's `_fr_slice_map` join uses, so a chunk's
    # ScannerResult rows and its accumulator cover the identical run-id set — the join lookup never misses.
    observations: list[dict] = []
    for start in range(0, len(runs_with_fr), run_chunk):
        slice_run_ids = runs_with_fr[start:start + run_chunk]
        ret_by_run_symbol = _fr_slice_map(session, horizon, slice_run_ids, batch)
        res_stmt = (
            select(ScannerResult)
            .where(ScannerResult.run_id.in_(slice_run_ids))
            .order_by(ScannerResult.run_id, ScannerResult.id)
        )
        for res in session.exec(res_stmt).yield_per(batch):
            fr = ret_by_run_symbol.get((res.run_id, res.ticker))
            if fr is None:
                continue  # no realized return at this horizon for this stock (n=0 contribution)
            realized, max_drawdown = fr
            value = _extract_factor_value(res, parsed)
            if value is None:
                continue  # factor-NULL observation EXCLUDED (never bucketed) — honest, not fabricated
            observations.append({
                "run_id": res.run_id, "ticker": res.ticker, "factor": float(value), "return": realized,
                # iter-27/52 (J-86/J-109): the stored max_drawdown read VERBATIM — aggregated read-only into
                # the per-decile mean-MDD beside the mean return; None on a short window (honest NA, never a
                # fabricated 0).
                "max_drawdown": max_drawdown,
                "regime": regime_by_run.get(res.run_id),  # stored regime label for the run (J-27)
            })
        # `ret_by_run_symbol` is rebound (not accumulated into) on the next iteration — this slice's dict is
        # eligible for GC before the next chunk's query even starts (the bounded-memory guarantee, TC-1).
    return observations


def _decile_member_slice(ordered: list[dict], count: int, decile: int) -> list[dict]:
    """The EXACT `ordered[lo:hi]` member slice the `_deciles` aggregate assigns to a 1-based `decile`
    (D1…D`count`). The lo/hi quantile edges are the SAME integer-arithmetic boundaries `_deciles` uses
    (`lo = (d-1)*n//count`, `hi = d*n//count`), so the samples drill-down for a decile reproduces the
    aggregate's membership byte-identically — the count-coherence keystone (J-51, invariant 13): no
    second membership rule, no re-derived "equivalent" edges. The caller is responsible for passing the
    SAME ascending-by-factor `ordered` list (deterministic tie-break by ticker+run) the aggregate used."""
    n = len(ordered)
    lo = (decile - 1) * n // count
    hi = decile * n // count
    return ordered[lo:hi]


def _deciles(ordered: list[dict], count: int, min_sample: int) -> list[dict]:
    """Split the factor-ascending `ordered` observations into `count` equal-count quantiles (deciles).
    Each row carries its `factor_min`/`factor_max`, `mean_return`, downside `risk_adjusted`, the paired
    `mean_max_drawdown` (iter-52, J-109), `n`, and a `low_sample` flag (`n < min_sample`). When there are
    fewer observations than `count`, the higher deciles are honest empty rows (`mean_return` None, `n` 0) —
    never fabricated buckets. Membership uses the SAME `_decile_member_slice` the samples drill-down reads
    (one quantile-edge definition).

    `mean_max_drawdown` (J-109) is the mean of the members' STORED `forward_returns.max_drawdown` read
    VERBATIM, over ONLY the members whose drawdown is non-None (the SAME `_group_mdd` convention the
    forward-test scorecard uses — a member with no stored drawdown is excluded, never counted as a
    fabricated 0); None when no member has one (honest NA). Because both `compute_factor_lab` and the
    all-horizons `compute_factor_lab_all` feed the SAME observation shape into THIS one builder, the paired
    drawdown column is byte-identical between the single-horizon and all-horizons views."""
    rows: list[dict] = []
    for d in range(1, count + 1):
        members = _decile_member_slice(ordered, count, d)
        returns = [m["return"] for m in members]
        mdds = [m["max_drawdown"] for m in members if m.get("max_drawdown") is not None]
        rows.append({
            "decile": d,
            "factor_min": members[0]["factor"] if members else None,
            "factor_max": members[-1]["factor"] if members else None,
            "mean_return": mean(returns) if returns else None,
            "risk_adjusted": _risk_adjusted(returns),
            "mean_max_drawdown": _mean_or_none(mdds),
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
    session: Session, factor_key: str, horizon: int, config: Optional[Config] = None, *,
    as_of: Optional[date_cls] = None,
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

    `as_of` (iter-19, J-32) optionally scopes the observation pool to snapshots dated <= D (a
    point-in-time / walk-forward view — the iter-17 seam, recomputes nothing). The payload echoes the
    resolved cutoff as `asof_date` (ISO) when scoped, else `null` (all-history). `as_of=None` is
    byte-identical to the cross-date all-history aggregate. Raises `ValueError` for an unknown factor
    (the API pre-validates -> 422)."""
    cfg = config or get_config()
    fl = cfg.research.factor_lab
    wf = cfg.walk_forward
    catalog = factor_catalog(cfg)

    factor = next((f for f in fl.factors if f.key == factor_key), None)
    if factor is None:
        raise ValueError(
            f"unknown factor {factor_key!r}; valid factors are {[f['key'] for f in catalog]}"
        )

    observations = _factor_observations(session, factor, horizon, as_of, cfg=cfg)
    # ascending by stored factor value; deterministic tie-break by (ticker, run_id) so deciles reproduce
    ordered = sorted(observations, key=lambda o: (o["factor"], o["ticker"], o["run_id"]))

    return {
        "factor": {
            "key": factor.key, "label": factor.label, "family": factor.family,
            "direction": factor.direction, "source": factor.source,
        },
        "horizon": horizon,
        # the resolved as-of scoping cutoff echoed (J-32) — ISO date when scoped, null in all-history mode
        "asof_date": as_of.isoformat() if as_of is not None else None,
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
# All-factors Factor-Lab view (J-107 → J-109) — one row per catalog factor, served from a SINGLE shared
# observation pool. iter-52 (J-109): the view now shows EVERY config horizon at once as paired (forward-
# return, max-drawdown) columns instead of a single user-selected horizon. Each (factor, horizon, decile)
# figure is BYTE-IDENTICAL to today's single-horizon `compute_factor_lab(factor, horizon, …)` for the same
# tuple (same `_deciles` / `_rank_ic` builders over the same per-horizon observation set). NO new served
# value — every figure is a re-presentation of an existing `compute_factor_lab` output across all horizons.
# --------------------------------------------------------------------------------------------------
def _all_fr_slice_map(
    session: Session, horizons: list[int], slice_run_ids: list[int], batch: int,
) -> dict[int, dict[tuple[int, str], tuple[float, Optional[float]]]]:
    """iter-29 fix-2 (AG-8): the per-horizon `(run_id, symbol) -> (realized_return, max_drawdown)` join maps
    for ONE bounded SLICE of run ids — `_all_factor_observations_by_horizon`'s chunk axis, and the
    all-horizons sibling of `_fr_slice_map`. Column-projected + `yield_per`-streamed exactly like the
    pre-chunk single-pass read; the only difference is the added `run_id.in_(slice_run_ids)` scope, which
    bounds the LIVE size of these dicts to (horizons x len(slice_run_ids) x symbols-per-run) instead of
    (horizons x full-history distinct pairs) — ~4.0M entries across the 5 config horizons on the live basis,
    the structure whose fill site (`research.py:497`/`:508` in the shipped tracebacks) raised the live
    `MemoryError` that made `/research/factor-lab` return 500 on EVERY visit. A named function (not an
    inlined loop body) so a test can wrap/instrument it to observe the live per-slice size directly."""
    fr_stmt = select(
        ForwardReturn.horizon, ForwardReturn.run_id, ForwardReturn.symbol,
        ForwardReturn.realized_return, ForwardReturn.max_drawdown,
    ).where(ForwardReturn.horizon.in_(horizons), ForwardReturn.run_id.in_(slice_run_ids))
    fr_by_h: dict[int, dict[tuple[int, str], tuple[float, Optional[float]]]] = {h: {} for h in horizons}
    for h, run_id, symbol, realized_return, max_drawdown in session.exec(fr_stmt).yield_per(batch):
        fr_by_h[h][(run_id, symbol)] = (realized_return, max_drawdown)
    return fr_by_h


def _all_factor_observations_by_horizon(
    session: Session, factors: list, horizons: list[int], as_of: Optional[date_cls] = None,
    *, cfg: Optional[Config] = None,
) -> tuple[list[tuple[int, str, tuple]], dict[int, list[tuple[int, float, Optional[float]]]]]:
    """The read-only SHARED per-observation pools for the all-factors view across EVERY horizon in
    `horizons` (J-109), built from ONE run-chunked sweep: per slice of run ids, one `ForwardReturn` SELECT
    covering all horizons (`horizon IN horizons`, column-projected to run_id/symbol/realized_return/
    max_drawdown) and one `ScannerResult` stream. Every ScannerResult row is still visited EXACTLY ONCE
    across the whole call (the slices partition the run-id space), so the per-result `record_json` parse
    count is unchanged.

    ops-hardening iter-31 (AG-8, J-06/J-07) — RETURN-VALUE memory bound. iter-29 fix-2 (below) bounded the
    JOIN ACCUMULATOR (`fr_by_h`) but left this function's OWN return shape unbounded "by design": the OLD
    `{horizon: [{run_id, ticker, return, max_drawdown, values} for every observation]}` held FIVE parallel
    Python lists of 5-key dicts, each dict INLINING its own copy of `run_id`/`ticker` on top of the
    (already-shared) `values` reference — duplicating run_id+ticker once per horizon a result touches
    (typically all 5) plus the per-dict container overhead. That duplication is `research.py:583`'s
    `pools[h].append` fill site — the live `MemoryError` frame both iter-29 and iter-30 reproduced and
    deferred (771,629-804,372 observations PER horizon on the live basis — `config.yaml`'s
    `research.factor_pool_max_observations` comment).

    Returns `(core_records, pools)` — a genuine memory-representation redesign, not a smaller constant:
      - `core_records`: ONE entry per ScannerResult with a realized return at >= 1 horizon —
        `(run_id, ticker, values)`, where `values` is a TUPLE (not a dict) of every catalog factor's stored
        value, ORDERED to match `factors` (so `values[i]` is `factors[i]`'s value — `compute_factor_lab_all`
        looks it up by a precomputed index, never by string key). `ticker` is INTERNED against a local cache
        scoped to this call, so the (far smaller) set of distinct ticker strings is held ONCE rather than
        once per horizon-observation.
      - `pools[h]`: a list of SMALL `(core_idx, realized_return, max_drawdown)` tuples — the genuinely
        per-horizon-specific data (a result's realized return / drawdown differ by horizon; its identity and
        factor values do not) — replacing the old per-horizon 5-key dict. `core_idx` indexes `core_records`.
      Neither the run-id chunking below nor the "ONE shared read serves every factor at every horizon"
      property changes: `core_records` is built lazily on the FIRST horizon a result has an FR at (same
      trigger the old `values` dict used), so this remains ONE pass over `ScannerResult`, never a per-horizon
      re-read (`test_all_factors_fires_one_shared_pool_read_not_n`).

    BYTE-IDENTITY keystone (same data, compacted container): for factor `f` at its precomputed index `idx`
    and horizon `h`, `[(core_records[i][0], core_records[i][1], core_records[i][2][idx], ret, mdd)
    for (i, ret, mdd) in pools[h] if core_records[i][2][idx] is not None]` reproduces EXACTLY the rows
    `_all_factor_observations(f, h, as_of)` would have produced — same values, same `(run_id, id)` traversal
    order — the property `compute_factor_lab_all` relies on for per-(factor,horizon,decile) byte-identity. A
    NULL in one factor does NOT drop the observation (unlike `_combination_observations`): `values[idx]`
    stays `None` for that factor's own filter. An observation is kept for horizon h ONLY when a realized
    return exists at h (the SAME n=0 exclusion as `_factor_observations`); a ScannerResult whose run has FRs
    at some other horizon but not at h simply contributes nothing to `pools[h]` (the per-horizon `fr is None`
    gate), exactly as the single-horizon builder dropped it.

    `as_of` (J-32) scopes ALL horizons' pools to snapshots with `ScannerRun.asof_date <= as_of` (the SAME
    single membership filter); `as_of=None` adds NO clause -> byte-identical all-history.

    iter-52 (J-105 / iter-46/47/48 OOM lesson): the read is BOUNDED — the FR scan is column-projected +
    `yield_per`-streamed (lightweight value tuples, NEVER full ORM rows over `forward_returns`), and the
    ScannerResult side is `yield_per`-streamed in `(run_id, id)` order (rides `ix_scanner_results_run_id`,
    so no `USE TEMP B-TREE FOR ORDER BY` spills a temp file). ONE heavy read serves ALL N factors at ALL
    horizons (not N×H reads) — and there is NO unbounded `.all()` over `ForwardReturn` or `ScannerResult`.
    The same one-sweep-for-all-horizons pattern as `_event_study_members_by_horizon`.

    iter-29 fix-2 (AG-8): streaming the two SOURCE queries was never enough — the JOIN ACCUMULATOR
    (`fr_by_h`) was one map per horizon holding every distinct (run_id, symbol) pair of the FULL history at
    once, ~4.0M entries across the 5 config horizons on the live basis. That is what raised the live
    `MemoryError` (against `start-backend.sh`'s `ulimit -v` cap) which made `GET /research/factor-lab?all=
    true` return 500 on EVERY visit — 4 of 4 requests in `logs/backend.log`, the page's only consumer, since
    `FactorLabPage` requests `?all=true` on mount. `runs_with_fr` is now discovered up front via the shared
    `_runs_with_fr` DISTINCT-projected query (bounded by RUN count, never by pair count) and walked in
    bounded SLICES of `research.factor_join_run_chunk` run ids — the SAME chunk axis and the SAME config
    knob `_factor_observations` uses. Each slice builds its own `_all_fr_slice_map`, streams+joins that
    slice's `ScannerResult`s, extends the pools, and discards the slice's maps before the next.

    BYTE-IDENTITY under chunking: `runs_with_fr` is sorted and the slices are non-overlapping contiguous
    increasing ranges, each `ScannerResult` scan re-applies the SAME `ORDER BY run_id, id`, and a slice's
    accumulator and its `ScannerResult` filter use the identical `run_id.in_(slice_run_ids)` set (so the
    join can never miss) — concatenating the slices reproduces the prior single-pass global order exactly.
    Per-slice last-write-wins cannot diverge from global last-write-wins because `forward_returns` carries
    `UNIQUE (run_id, symbol, horizon)`. No-lookahead is preserved because the `as_of` cutoff moved UP into
    `_runs_with_fr`, upstream of every derived structure.

    iter-31 AG-8 disclosure net (NOT the memory fix itself — see above): if any horizon's `pools[h]` ever
    exceeds `research.factor_pool_max_observations` (a soft ceiling, set with headroom above today's live
    max per `config.yaml`'s comment), this logs a WARNING and keeps going — NEVER raises, NEVER truncates
    (truncation would break the byte-identity contract this function exists to preserve). The check runs
    PER RUN-CHUNK inside the sweep, once per horizon (iter-31 audit): a widening large enough to exhaust
    memory raises inside that loop, so an after-the-loop check could never fire on the very crash this net
    exists to pre-announce."""
    parsed_by_key = {f.key: parse_factor_source(f.source) for f in factors}
    research_cfg = (cfg or get_config()).research
    batch = research_cfg.read_batch_size          # ROW count — the `yield_per` size of each stream
    run_chunk = research_cfg.factor_join_run_chunk  # RUN count — the accumulator's slice width
    pool_cap = research_cfg.factor_pool_max_observations  # AG-8 disclosure ceiling — never truncates

    runs_with_fr = _runs_with_fr(session, horizons, as_of)
    core_records: list[tuple[int, str, tuple]] = []
    pools: dict[int, list[tuple[int, float, Optional[float]]]] = {h: [] for h in horizons}
    ticker_intern: dict[str, str] = {}  # dedupes repeated ticker strings across the whole sweep (iter-31)
    warned_horizons: set[int] = set()  # one WARNING per horizon — never a per-chunk log storm (iter-31 audit)
    for start in range(0, len(runs_with_fr), run_chunk):
        slice_run_ids = runs_with_fr[start:start + run_chunk]
        fr_by_h = _all_fr_slice_map(session, horizons, slice_run_ids, batch)
        res_stmt = (
            select(ScannerResult)
            .where(ScannerResult.run_id.in_(slice_run_ids))
            .order_by(ScannerResult.run_id, ScannerResult.id)
        )
        for res in session.exec(res_stmt).yield_per(batch):
            core_idx: Optional[int] = None  # assigned lazily on the first horizon that has an FR
            for h in horizons:
                fr = fr_by_h[h].get((res.run_id, res.ticker))
                if fr is None:
                    continue  # no realized return at this horizon (n=0) — same exclusion as per-factor
                if core_idx is None:
                    values = tuple(_extract_factor_value(res, parsed) for parsed in parsed_by_key.values())
                    ticker = ticker_intern.setdefault(res.ticker, res.ticker)
                    core_idx = len(core_records)
                    core_records.append((res.run_id, ticker, values))
                realized, max_drawdown = fr
                pools[h].append((core_idx, realized, max_drawdown))
        # `fr_by_h` is rebound (not accumulated into) on the next iteration — this slice's maps are eligible
        # for GC before the next chunk's query even starts (the bounded-memory guarantee, unchanged iter-29).
        #
        # iter-31 AUDIT FIX: the ceiling is checked HERE, per run-chunk, NOT after the sweep. The scenario
        # `config.yaml`'s comment promises to pre-announce ("a future data-scale widening logs a WARNING
        # instead of silently repeating this crash at a larger scale") is precisely the one in which the
        # build never reaches its own end: a widening big enough to exhaust memory raises MemoryError
        # INSIDE this loop, so an after-the-loop check could never fire on the very crash it disclaims.
        # Per-chunk costs O(len(runs)/run_chunk) length reads (a handful on the live basis) and lands the
        # line in `logs/backend.log` while the build is still running. Still never raises, never truncates.
        for h, pool in pools.items():
            if len(pool) > pool_cap and h not in warned_horizons:
                warned_horizons.add(h)
                logger.warning(
                    "research.factor_pool_max_observations exceeded: horizon=%s observations=%d cap=%d — a "
                    "data-scale widening past the documented live basis (config.yaml comment); the payload "
                    "is still computed and served correctly, this is AG-8 disclosure only, never a "
                    "truncation",
                    h, len(pool), pool_cap,
                )
    return core_records, pools


def compute_factor_lab_all(
    session: Session, config: Optional[Config] = None, *, as_of: Optional[date_cls] = None,
) -> dict:
    """The all-factors, all-horizons Factor-Lab view (J-107 → J-109): one entry per config-catalog factor,
    each carrying — at the FIXED `config.walk_forward.default_horizon` — `family` + Spearman `rank_ic`
    (`{value, n}`) + the top-decile downside `risk_adjusted` figure, PLUS a `by_horizon` block with, for
    EVERY `config.walk_forward.horizons` horizon, that factor's full D1..D`deciles` decile table (each
    decile row pairing the mean realized forward return with its mean `max_drawdown`, J-86). Every
    `(factor, horizon, decile)` figure is BYTE-IDENTICAL to `compute_factor_lab(factor, horizon,
    as_of=cutoff)` for the same tuple (Single source of truth).

    ONE computation path: the shared observation pools are built ONCE for all horizons
    (`_all_factor_observations_by_horizon` — one heavy read carrying every factor's value + the paired
    drawdown per observation), then for EACH (factor, horizon) we filter to that factor's non-null subset
    (preserving the pool's order, which equals `_factor_observations(factor, horizon)`' order), sort with the
    EXACT `(factor, ticker, run_id)` key `compute_factor_lab` uses, and derive the deciles from the SAME
    `_deciles` builder (which pairs mean_return + mean_max_drawdown). The rank-IC + top-decile risk-adjusted
    are computed ONCE at `default_horizon` (no longer a user selector — relabelled with that horizon). No
    second rank-IC / decile / risk-adjusted / drawdown derivation; NO new served value — every figure is a
    re-presentation of an existing `compute_factor_lab` output.

    `as_of` (J-32) scopes the shared pools to snapshots dated <= D (a pure FILTER — recomputes nothing);
    `as_of=None` is the all-history aggregate. The catalog is config-driven, so there is no unknown-factor
    case here; the view is horizon-independent (it shows ALL horizons), so it takes no `horizon` argument."""
    cfg = config or get_config()
    fl = cfg.research.factor_lab
    wf = cfg.walk_forward
    catalog = factor_catalog(cfg)
    factors = list(fl.factors)
    horizons = list(wf.horizons)
    default_h = wf.default_horizon

    core_records, pools = _all_factor_observations_by_horizon(session, factors, horizons, as_of, cfg=cfg)
    # position of each factor inside `core_records[i][2]`'s values tuple — built from the SAME `factors`
    # list (in the SAME order) `_all_factor_observations_by_horizon` used to build that tuple (iter-31).
    factor_index = {f.key: i for i, f in enumerate(factors)}

    factors_table: list[dict] = []
    for factor in factors:
        idx = factor_index[factor.key]
        by_horizon: list[dict] = []
        dh_rank_ic: dict = {"value": None, "n": 0}
        dh_risk_adjusted: Optional[float] = None
        dh_n_total = 0
        for h in horizons:
            # ITS non-null subset at horizon h, in the pool's order (== `_factor_observations(factor, h)`
            # order), so the rank-IC pearson summation order — and thus the byte value — matches
            # compute_factor_lab(factor, h) exactly. The paired drawdown rides along verbatim. `core_records`
            # holds the (run_id, ticker, values) identity SHARED across every horizon a result touches — only
            # `ret`/`max_drawdown` are genuinely per-horizon (iter-31 compact-encoding return-value bound).
            obs = []
            for core_idx, ret, max_drawdown in pools[h]:
                factor_value = core_records[core_idx][2][idx]
                if factor_value is None:
                    continue
                run_id, ticker, _values = core_records[core_idx]
                obs.append({
                    "run_id": run_id, "ticker": ticker,
                    "factor": float(factor_value), "return": ret, "max_drawdown": max_drawdown,
                })
            # ascending by stored factor value; SAME deterministic tie-break compute_factor_lab uses.
            ordered = sorted(obs, key=lambda o: (o["factor"], o["ticker"], o["run_id"]))
            deciles = _deciles(ordered, fl.deciles, wf.min_sample)
            by_horizon.append({"horizon": h, "n_total": len(obs), "deciles": deciles})
            if h == default_h:
                # the relabelled rank-IC + top-decile downside risk-adjusted at the FIXED default horizon —
                # byte-identical to compute_factor_lab(factor, default_h).rank_ic / deciles[-1].risk_adjusted.
                dh_rank_ic = _rank_ic([(o["factor"], o["return"]) for o in obs])
                dh_risk_adjusted = deciles[-1]["risk_adjusted"]
                dh_n_total = len(obs)
        factors_table.append({
            "key": factor.key, "label": factor.label, "family": factor.family,
            "direction": factor.direction,
            "n_total": dh_n_total,          # observations at the default horizon (== rank-IC n)
            "rank_ic": dh_rank_ic,          # Spearman rank-IC at the default horizon
            "risk_adjusted": dh_risk_adjusted,  # top-decile downside risk-adjusted at the default horizon
            "by_horizon": by_horizon,       # per-horizon decile table (paired return + max-drawdown)
        })

    return {
        # the resolved as-of scoping cutoff echoed (J-32) — ISO date when scoped, null in all-history mode.
        "asof_date": as_of.isoformat() if as_of is not None else None,
        "factors": catalog,
        "horizons": horizons,
        "default_horizon": default_h,  # the fixed horizon the rank-IC / risk-adjusted are labelled with
        "deciles_count": fl.deciles,
        "min_sample": wf.min_sample,
        "survivorship_bias": SURVIVORSHIP_BIAS_LABEL,
        "descriptive_caveat": RESEARCH_CAVEAT,
        "factors_table": factors_table,
    }


# --------------------------------------------------------------------------------------------------
# Multi-factor combination cohorts (J-26) — read-only over the SAME stored pool. The HEADLINE `composite`
# cohort is a config-weighted COMPOSITE PERCENTILE-RANK BLEND of the conditions' STORED factor values (the
# top config-quantile of the blend); the exact AND-intersection rides along as the SECONDARY `strict_overlap`
# cohort. The composite is a deterministic ranking / GROUPING of stored values (the SAME read-only class as
# the J-25 decile sort) — it recomputes NO factor and NO return and is NOT a fitted/learned/ML model.
# --------------------------------------------------------------------------------------------------
def _combination_observations(
    session: Session, factors: list, horizon: int, as_of: Optional[date_cls] = None,
    *, cfg: Optional[Config] = None,
) -> list[dict]:
    """The read-only multi-factor per-observation pool for (`factors`, `horizon`): mirror
    `_factor_observations` but read EVERY referenced factor's stored value per result. SELECT-only against
    `ForwardReturn` + `ScannerResult`; it recomputes NO return and NO factor. An observation is kept ONLY
    when a realized return exists at this horizon AND every referenced factor is non-null — a NULL in ANY
    referenced factor EXCLUDES the observation (never fabricated), so the pool is a (possibly strict)
    subset of any single factor's `_factor_observations` pool. Each observation is
    `{run_id, ticker, return, values: {factor_key: float}}`.

    `as_of` (iter-19, J-32) optionally scopes the pool to snapshots with `ScannerRun.asof_date <= as_of`
    (the SAME single membership filter as `_factor_observations` / `forward_testing`); `as_of=None` adds
    NO clause → byte-identical all-history.

    ops-hardening iter-46 (AG-8): this sibling of `_factor_observations` used to build ONE
    `ret_by_run_symbol` dict over the ENTIRE horizon's `forward_returns` population in a single pass —
    1,285,609 rows measured live at horizon=20 (the evidence-serving path's other named `MemoryError`
    site, `research.py:777` pre-fix) — even though the source query was already `yield_per`-streamed (a
    bounded READ, unbounded RETENTION, the exact shape iter-40's lesson names). Now mirrors
    `_factor_observations`'s already-audited iter-29 fix exactly: `_runs_with_fr` discovers the distinct
    run ids ONCE (bounded by run count, never by pair count), walked in bounded SLICES of
    `research.factor_join_run_chunk`; each slice reuses the SAME `_fr_slice_map` join-map builder
    `_factor_observations` already uses (its `max_drawdown` half is simply unused here), then that slice's
    matching `ScannerResult`s are streamed ordered `(run_id, id)` and `observations` extended, before the
    slice's dict is rebound (not accumulated into) on the next iteration — eligible for GC before the next
    chunk's query starts. Slices walk the sorted `runs_with_fr` list in non-overlapping increasing ranges,
    so concatenating each slice's `(run_id, id)`-ordered output reproduces the SAME global order the prior
    single-pass implementation produced — byte-identical (TC-3), never re-derived. No new config knob."""
    parsed_by_key = {f.key: parse_factor_source(f.source) for f in factors}
    research_cfg = (cfg or get_config()).research
    batch = research_cfg.read_batch_size
    run_chunk = research_cfg.factor_join_run_chunk

    # iter-46 (AG-8): the distinct run ids at this horizon, via the SAME shared DISTINCT-projected
    # discovery `_factor_observations` uses — bounded by run count, never by (run, symbol) pair count.
    runs_with_fr = _runs_with_fr(session, [horizon], as_of)

    observations: list[dict] = []
    for start in range(0, len(runs_with_fr), run_chunk):
        slice_run_ids = runs_with_fr[start:start + run_chunk]
        # reuses `_fr_slice_map` (the SAME per-slice join accumulator `_factor_observations` already
        # uses) rather than a second near-duplicate builder — this pool only reads the `realized_return`
        # half of its `(realized_return, max_drawdown)` tuple.
        ret_by_run_symbol = _fr_slice_map(session, horizon, slice_run_ids, batch)
        res_stmt = (
            select(ScannerResult)
            .where(ScannerResult.run_id.in_(slice_run_ids))
            .order_by(ScannerResult.run_id, ScannerResult.id)
        )
        for res in session.exec(res_stmt).yield_per(batch):
            fr = ret_by_run_symbol.get((res.run_id, res.ticker))
            if fr is None:
                continue  # no realized return at this horizon for this stock (excluded, never fabricated)
            realized, _max_drawdown = fr  # this pool doesn't carry max_drawdown; the shared map does
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
        # `ret_by_run_symbol` is rebound (not accumulated into) on the next iteration — this slice's dict
        # is eligible for GC before the next chunk's query even starts (the bounded-memory guarantee, TC-1).
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


def _combination_cohort_members(pool: list[dict], resolved: list[dict], comb) -> dict:
    """The SINGLE membership-derivation path for every combination cohort over `pool` (J-26): the
    per-condition `single` index sets (each condition's nearest-rank quantile membership over the SHARED
    pool's values for that factor), the `strict` AND-intersection of those singles, and the `composite`
    rank-blend cohort (the top config-quantile of the config-weighted oriented-percentile-rank blend).
    Returns `{"single": list[set[int]], "strict": set[int], "composite": set[int]}` — pool indices into
    `pool`. BOTH `compute_factor_combination` (the published n) and the samples drill-down (the member
    list) call THIS function, so a cohort's drill-down total EQUALS its published N by construction
    (count-coherence keystone, invariant 13 — never a second membership rule). Pure index arithmetic over
    the already-built pool; recomputes no factor and no return."""
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

    return {"single": single_members, "strict": strict_members, "composite": composite_members}


def compute_factor_combination(
    session: Session, conditions: list[dict], horizon: int, config: Optional[Config] = None, *,
    as_of: Optional[date_cls] = None,
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
    factor's `_factor_observations` n. `as_of` (iter-19, J-32) optionally scopes the pool to snapshots
    dated <= D (the iter-17 membership seam — recomputes nothing); the payload echoes the resolved cutoff
    as `asof_date` (ISO) when scoped, else `null`; `as_of=None` is byte-identical all-history. Raises
    `ValueError` for an unknown factor/side/quantile or an out-of-range condition count (the API
    pre-validates -> 422)."""
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
    pool = _combination_observations(session, distinct_factors, horizon, as_of, cfg=cfg)
    pool_n = len(pool)

    # the SINGLE membership-derivation path (shared verbatim with the samples drill-down so a cohort's
    # drill-down total EQUALS its published N — invariant 13). Returns pool-index sets for the singles,
    # the strict AND-intersection, and the composite rank-blend cohort.
    cohort_members = _combination_cohort_members(pool, resolved, comb)
    single_members = cohort_members["single"]
    strict_members = cohort_members["strict"]
    composite_members = cohort_members["composite"]
    # echoed for the payload labelling (config-driven — not a hard-coded UI string).
    comp = comb.composite
    composite_quantile = next(q for q in comb.quantiles if q.key == comp.quantile)  # boot-validated to exist

    def _returns(indices) -> list[float]:
        return [pool[i]["return"] for i in sorted(indices)]

    resolved_conditions = [_condition_payload(c) for c in resolved]

    return {
        "conditions": resolved_conditions,
        "horizon": horizon,
        # the resolved as-of scoping cutoff echoed (J-32) — ISO date when scoped, null in all-history mode
        "asof_date": as_of.isoformat() if as_of is not None else None,
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
# The two overlap-honesty views (J-63) a cohort can be observed under — a fixed structural vocabulary
# (not a tunable). `episodes` (the DEFAULT) collapses each continuous run of a symbol triggering a
# subject into ONE first-trigger observation; `pooled` keeps every per-signal-day observation (the
# pre-J-63 behaviour, byte-identical). Both endpoints validate `view` against this set (422 otherwise).
VIEW_EPISODES = "episodes"
VIEW_POOLED = "pooled"
ALL_VIEWS = (VIEW_EPISODES, VIEW_POOLED)


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


def pattern_keys(cfg: Config) -> list[str]:
    """The ordered, config-driven detected-pattern keys (`config.patterns` keys — vcp /
    pullback_to_rising_dma / flat_base_breakout). The SAME vocabulary `subject_catalog` derives the
    pattern subjects from, so a config-added pattern flows into the J-77 study with NO code change (no
    hardcoded pattern list anywhere)."""
    return list(cfg.patterns.model_dump())


def _stored_pattern_flags(res: ScannerResult, keys: list[str]) -> dict[str, bool]:
    """The stored detected-pattern mirror flags for ONE result, read VERBATIM (J-77): `{pattern_key:
    bool}` from each `is_<key>` column (the SAME `by_<name>` stored-mirror convention `_subject_member`
    / `forward_testing` already read), for the config-driven `keys`. Recomputes no pattern — no hardcoded
    list. Used to enrich each event-study observation additively."""
    return {key: bool(getattr(res, f"is_{key}")) for key in keys}


def _subject_member(res: ScannerResult, subject: dict) -> bool:
    """Whether a stored result belongs to the subject's pooled cohort, read VERBATIM from the snapshot
    (never re-classified): a SETUP subject pools `scanner_results.setup_status == key`; a PATTERN subject
    pools the stored mirror flag `is_<key>` being True — the SAME `by_<name>` stored-mirror grouping
    convention `forward_testing` already uses for is_vcp / is_pullback_to_rising_dma / is_flat_base_breakout."""
    if subject["kind"] == "setup":
        return res.setup_status == subject["key"]
    return bool(getattr(res, f"is_{subject['key']}"))


# iter-47 (J-105): the light projected ScannerResult row the event-study builders need — the stored
# fields the member dict + `_subject_member` read, NEVER the full ORM row (which would grow the identity
# map). `patterns` is the SAME `{key: bool(is_<key>)}` mirror `_stored_pattern_flags` builds, derived from
# the projected `is_<k>` flags so it can NOT diverge from `_subject_member`'s pattern test.
class _SubjectResultRow:
    __slots__ = ("id", "run_id", "ticker", "sector", "setup_status", "patterns")

    def __init__(self, id, run_id, ticker, sector, setup_status, patterns):
        self.id = id
        self.run_id = run_id
        self.ticker = ticker
        self.sector = sector
        self.setup_status = setup_status
        self.patterns = patterns


def _subject_matching_result_rows(
    session: Session, subject: dict, as_of: Optional[date_cls], p_keys: list[str], batch: int,
) -> tuple[list["_SubjectResultRow"], set[int]]:
    """Stream the subject-matching `ScannerResult`s FIRST (iter-47 reorder, J-105), column-projected and
    ordered by `ScannerResult.id` — the SAME total deterministic order the prior full-ORM scan produced.
    Returns `(ordered_matches, needed_runs)` where each match is a light `_SubjectResultRow` carrying ONLY
    the stored fields the member dict + `_subject_member` read (id, run_id, ticker, sector, setup_status,
    and the `{pattern_key: bool}` mirror derived from the projected `is_<k>` flags). The FR scan is later
    pruned to `run_id IN needed_runs`, so memory is O(subject matches), independent of the table size.

    BYTE-IDENTITY: the prior builders scanned ALL results in FR-bearing runs and kept the subject members;
    here we filter to the subject members directly in SQL (setup → `setup_status == key`; pattern →
    `is_<key> == True`, the SAME stored-mirror test `_subject_member` applies). Dropping the old
    `run_id IN runs_with_fr` pre-filter can only ADD matches in runs with no FR — those are then dropped by
    the per-horizon `fr is None` gate at emission → identical content; ordering by `ScannerResult.id` is
    preserved → identical order. `as_of` scopes via the canonical `ScannerRun.asof_date <= D` join."""
    # project the light fields the member shape + the subject/pattern tests read (derive the is_<k>
    # projection FROM p_keys so `patterns`/`_subject_member` can never diverge).
    flag_cols = [getattr(ScannerResult, f"is_{k}") for k in p_keys]
    stmt = select(
        ScannerResult.id, ScannerResult.run_id, ScannerResult.ticker,
        ScannerResult.sector, ScannerResult.setup_status, *flag_cols,
    )
    if subject["kind"] == "setup":
        stmt = stmt.where(ScannerResult.setup_status == subject["key"])
    else:
        stmt = stmt.where(getattr(ScannerResult, f"is_{subject['key']}").is_(True))
    if as_of is not None:
        stmt = stmt.join(ScannerRun, ScannerRun.id == ScannerResult.run_id).where(
            ScannerRun.asof_date <= as_of
        )
    stmt = stmt.order_by(ScannerResult.id)

    ordered: list[_SubjectResultRow] = []
    needed_runs: set[int] = set()
    for row in session.exec(stmt).yield_per(batch):
        rid, run_id, ticker, sector, setup_status = row[0], row[1], row[2], row[3], row[4]
        patterns = {key: bool(row[5 + i]) for i, key in enumerate(p_keys)}
        ordered.append(_SubjectResultRow(rid, run_id, ticker, sector, setup_status, patterns))
        needed_runs.add(run_id)
    return ordered, needed_runs


def _regime_by_run_projected(
    session: Session, needed_runs: set[int], batch: int
) -> dict[int, Optional[str]]:
    """`run_id -> stored regime_label` over a SUPERSET of the FR-bearing runs (every subject-matching run),
    column-projected + streamed. Every emitted member has an FR and so its run is in `needed_runs` → the
    `.get` is identical to the prior full-run-row map. Read VERBATIM; recomputes no regime."""
    if not needed_runs:
        return {}
    regime_by_run: dict[int, Optional[str]] = {}
    stmt = select(ScannerRun.id, ScannerRun.regime_label).where(ScannerRun.id.in_(needed_runs))
    for run_id, regime_label in session.exec(stmt).yield_per(batch):
        regime_by_run[run_id] = regime_label
    return regime_by_run


def _event_study_members(
    session: Session, subject: dict, horizon: int, as_of: Optional[date_cls] = None,
    *, cfg: Optional[Config] = None,
) -> list[dict]:
    """The read-only per-observation pool for (subject, horizon): join each stored `ForwardReturn` at this
    horizon (its `realized_return` + `mae` + `mfe`, read VERBATIM) to its stored `ScannerResult` (by
    run_id + ticker) and the run's stored `regime_label`, keeping ONLY the subject's members. SELECT-only
    against `ForwardReturn` + `ScannerResult` + `ScannerRun`; it recomputes NO return / excursion / score /
    regime / pattern. This pools the SAME per-observation rows `compute_forward_aggregates`'s `by_setup` /
    `by_<pattern>` group (the consistency invariant is unit-asserted). A member with no realized return at
    this horizon contributes nothing (n=0).

    iter-47 (J-105): the forward-return scan is column-projected + `yield_per`-streamed and PRUNED to the
    subject's needed runs (the subject-matching results are streamed first), so memory is O(subject
    matches), not O(table). Byte-identical to the prior implementation (same member shape, same
    `ScannerResult.id` order, same verbatim values).

    `as_of` (iter-19, J-32) optionally scopes the pool to snapshots with `ScannerRun.asof_date <= as_of`
    (the SAME single membership filter as `_factor_observations` / `forward_testing`); `as_of=None` adds
    NO clause → byte-identical all-history."""
    cfg = cfg or get_config()
    batch = cfg.research.read_batch_size
    # iter-20 (J-77): the config-driven pattern keys resolved ONCE for this build (no per-row get_config).
    p_keys = pattern_keys(cfg)

    # (1) stream the subject-matching results first (ordered by id) → the needed-runs cohort.
    ordered_matches, needed_runs = _subject_matching_result_rows(session, subject, as_of, p_keys, batch)
    if not ordered_matches:
        return []
    # (2) projected regime map over a superset of FR-bearing runs (read verbatim).
    regime_by_run = _regime_by_run_projected(session, needed_runs, batch)

    # (3) projected + streamed FR scan, PRUNED to the needed runs at this horizon → light value tuples.
    needed_pairs = {(m.run_id, m.ticker) for m in ordered_matches}
    fr_by_run_symbol: dict[tuple[int, str], tuple] = {}
    fr_stmt = select(
        ForwardReturn.run_id, ForwardReturn.symbol,
        ForwardReturn.realized_return, ForwardReturn.mae, ForwardReturn.mfe, ForwardReturn.max_drawdown,
    ).where(ForwardReturn.horizon == horizon, ForwardReturn.run_id.in_(needed_runs))
    for run_id, symbol, realized_return, mae, mfe, max_drawdown in session.exec(fr_stmt).yield_per(batch):
        if (run_id, symbol) in needed_pairs:
            fr_by_run_symbol[(run_id, symbol)] = (realized_return, mae, mfe, max_drawdown)

    # (4) emit members in `ScannerResult.id` order — identical dict shape / key order / values.
    members: list[dict] = []
    for res in ordered_matches:
        fr = fr_by_run_symbol.get((res.run_id, res.ticker))
        if fr is None:
            continue  # no realized return at this horizon for this member (n=0 contribution)
        realized_return, mae, mfe, max_drawdown = fr
        members.append({
            "run_id": res.run_id, "ticker": res.ticker,
            "return": realized_return, "mae": mae, "mfe": mfe,
            # iter-27 (J-86): the stored max_drawdown read VERBATIM — aggregated read-only by the event
            # study (mean-MDD beside the return stats); never recomputed. None on a short window.
            "max_drawdown": max_drawdown,
            "regime": regime_by_run.get(res.run_id),  # stored regime label (read verbatim)
            "sector": res.sector,                     # stored sector (read verbatim)
            # iter-20 (J-77) ADDITIVE enrichment: the observation's STORED setup status + pattern mirror
            # flags, read VERBATIM from `scanner_results` (the SAME `is_<pattern>` mirrors `_subject_member`
            # / `forward_testing` already read) — never recomputed. PURELY ADDITIVE: every existing
            # event-study figure (J-29 / J-63) and the existing samples drill-downs ignore these keys, so
            # they stay byte-identical. The regime×setup×pattern study (J-77) groups by these stored fields.
            "setup_status": res.setup_status,
            "patterns": res.patterns,
        })
    return members


def _event_study_members_by_horizon(
    session: Session, subject: dict, horizons: list[int], as_of: Optional[date_cls] = None,
    *, cfg: Optional[Config] = None,
) -> dict[int, list[dict]]:
    """The read-only per-observation pools for (subject, EVERY horizon in `horizons`) built from a SINGLE
    batched read (J-72 perf): ONE `ForwardReturn` SELECT covering all configured horizons (`horizon IN
    horizons`), ONE `ScannerResult` stream, and ONE `ScannerRun` stream. The returned `{horizon: [members]}`
    is BYTE-IDENTICAL per horizon to calling `_event_study_members(session, subject, h, as_of)` in a loop
    (the SAME join, the SAME member shape + enrichment, the SAME insertion order — results iterated once in
    `ScannerResult.id` order, each appended to its horizon's list keyed by the run-symbol pair). It
    recomputes NO return / excursion / score / regime / pattern.

    iter-47 (J-105): the FR scan is column-projected + `yield_per`-streamed and PRUNED to the subject's
    needed runs (`horizon IN horizons AND run_id IN needed_runs`), the subject-matching results streamed
    first — memory is O(subject matches), not O(table). The reorder is byte-identical: a subject match in a
    run with no FR at horizon h is simply dropped by the per-horizon `fr is None` gate (exactly as the prior
    builder dropped it), and ordering by `ScannerResult.id` is preserved.

    `as_of` (J-32) scopes ALL horizons' pools to snapshots dated <= D (the SAME single membership filter);
    `as_of=None` adds NO clause -> byte-identical all-history."""
    cfg = cfg or get_config()
    batch = cfg.research.read_batch_size
    p_keys = pattern_keys(cfg)

    # (1) stream the subject-matching results first (ordered by id) → the needed-runs cohort.
    ordered_matches, needed_runs = _subject_matching_result_rows(session, subject, as_of, p_keys, batch)
    members_by_h: dict[int, list[dict]] = {h: [] for h in horizons}
    if not ordered_matches:
        return members_by_h
    # (2) projected regime map over a superset of FR-bearing runs (read verbatim).
    regime_by_run = _regime_by_run_projected(session, needed_runs, batch)

    # (3) projected + streamed FR scan over ALL requested horizons, PRUNED to the needed runs/pairs →
    # `{horizon: {(run_id, symbol): (return, mae, mfe, max_drawdown)}}` (one row per the unique constraint).
    needed_pairs = {(m.run_id, m.ticker) for m in ordered_matches}
    fr_by_h_run_symbol: dict[int, dict[tuple[int, str], tuple]] = {h: {} for h in horizons}
    fr_stmt = select(
        ForwardReturn.horizon, ForwardReturn.run_id, ForwardReturn.symbol,
        ForwardReturn.realized_return, ForwardReturn.mae, ForwardReturn.mfe, ForwardReturn.max_drawdown,
    ).where(ForwardReturn.horizon.in_(horizons), ForwardReturn.run_id.in_(needed_runs))
    for h, run_id, symbol, realized_return, mae, mfe, max_drawdown in session.exec(fr_stmt).yield_per(batch):
        if (run_id, symbol) in needed_pairs:
            fr_by_h_run_symbol[h][(run_id, symbol)] = (realized_return, mae, mfe, max_drawdown)

    # (4) emit members per horizon iterating results in `ScannerResult.id` order — identical shape/order.
    for res in ordered_matches:
        for h in horizons:
            fr = fr_by_h_run_symbol[h].get((res.run_id, res.ticker))
            if fr is None:
                continue
            realized_return, mae, mfe, max_drawdown = fr
            members_by_h[h].append({
                "run_id": res.run_id, "ticker": res.ticker,
                "return": realized_return, "mae": mae, "mfe": mfe,
                "max_drawdown": max_drawdown,  # iter-27 (J-86) stored MDD read verbatim
                "regime": regime_by_run.get(res.run_id),
                "sector": res.sector,
                "setup_status": res.setup_status,
                "patterns": res.patterns,
            })
    return members_by_h


def _run_position_index(
    session: Session, as_of: Optional[date_cls] = None
) -> dict[int, int]:
    """`run_id → ordinal position` over the GLOBAL ordered stored-snapshot sequence (every immutable
    `scanner_runs` row, ascending by the canonical `ScannerRun.asof_date` — which is unique per run, so
    the ordering is total and deterministic). This is the run-date sequence episode-consecutiveness is
    judged on (J-63): two of a symbol's signal-days are CONSECUTIVE iff their runs' ordinals differ by
    exactly 1 — i.e. there is no intervening stored run-date between them. Consecutiveness is therefore
    judged on the run-date SEQUENCE, NOT on raw calendar adjacency (a 50-trading-day gap with no
    intervening stored run is still consecutive; an intervening stored run on which the symbol did NOT
    trigger the subject breaks the run). A single SELECT; recomputes nothing.

    `as_of` (J-32) scopes the global sequence to snapshots dated <= D (the SAME single membership filter
    `_event_study_members` applies), so consecutiveness is judged WITHIN the same point-in-time window the
    members were pooled from; `as_of=None` indexes every stored run → all-history."""
    stmt = select(ScannerRun.id, ScannerRun.asof_date)
    if as_of is not None:
        stmt = stmt.where(ScannerRun.asof_date <= as_of)
    ordered = sorted(session.exec(stmt).all(), key=lambda row: row[1])  # ascending by asof_date
    return {run_id: position for position, (run_id, _asof) in enumerate(ordered)}


def _collapse_to_episodes(members: list[dict], run_position: dict[int, int]) -> list[dict]:
    """Collapse the pooled per-signal-day `members` of ONE (subject, horizon) into first-trigger EPISODES
    (J-63), a pure in-memory deterministic grouping of the STORED rows — it recomputes NO return /
    excursion / regime / sector / membership. For each `ticker`, its member signal-days are ordered by
    their run's GLOBAL ordinal (`run_position`) and split into maximal runs of CONSECUTIVE ordinals
    (ordinal difference exactly 1 — no intervening stored run-date on which the ticker did not trigger).
    Each such run collapses to ONE episode observed at its FIRST trigger date, carrying that first
    observation's stored `return` / `mae` / `mfe` / `regime` / `sector` VERBATIM (the later signal-days of
    the run are dropped from the count — that is the overlap correction). A break in the ordinal sequence
    yields a SEPARATE episode. Determinism: the same members + run order always yield the same episodes
    (ticker grouping + ordinal sort are total orders). Output preserves the input member order of the
    surviving first-trigger rows so downstream sorts/slices stay stable."""
    # group members by ticker, remembering each member's global run ordinal
    by_ticker: dict[str, list[tuple[int, dict]]] = defaultdict(list)
    for member in members:
        ordinal = run_position.get(member["run_id"])
        if ordinal is None:  # defensive: a member whose run is outside the indexed window is dropped
            continue
        by_ticker[member["ticker"]].append((ordinal, member))

    # the first-trigger member of each maximal consecutive-ordinal run (the ordinal sort is per-ticker, so
    # ordinals never collide ACROSS tickers — two tickers triggering on the SAME run-date are independent
    # episodes). Collect the surviving rows' identities, then re-emit in the ORIGINAL member order (stable).
    kept_ids: set[int] = set()
    for occurrences in by_ticker.values():
        occurrences.sort(key=lambda pair: pair[0])  # ascending by global run ordinal
        prev_ordinal: Optional[int] = None
        for ordinal, member in occurrences:
            if prev_ordinal is None or ordinal != prev_ordinal + 1:
                kept_ids.add(id(member))  # a NEW episode → its first trigger is this signal-day
            prev_ordinal = ordinal

    return [member for member in members if id(member) in kept_ids]


def _event_study_observation_set(
    session: Session, subject: dict, horizon: int, view: str, as_of: Optional[date_cls] = None
) -> list[dict]:
    """The observation set for (subject, horizon) under the selected `view` (J-63) — the SINGLE membership
    builder every event-study figure AND the samples drill-down read, so a cohort's drill-down total
    EQUALS its published n by construction (count-coherence keystone). `view="pooled"` returns the
    `_event_study_members` list UNCHANGED (byte-identical to the pre-J-63 behaviour); `view="episodes"`
    (the default) returns its first-trigger episode collapse (`_collapse_to_episodes`). Recomputes nothing
    — pure SELECT + in-memory grouping. `as_of` scopes both the members and the run-ordinal index to the
    same point-in-time window."""
    members = _event_study_members(session, subject, horizon, as_of)
    if view == VIEW_POOLED:
        return members  # the unchanged pooled list — byte-identical to pre-J-63
    run_position = _run_position_index(session, as_of)
    return _collapse_to_episodes(members, run_position)


def _episode_count(session: Session, subject: dict, horizon: int, as_of: Optional[date_cls] = None) -> int:
    """The number of distinct first-trigger EPISODES for (subject, horizon) — identical in BOTH views
    (it counts episodes regardless of which view renders, per the J-63 disclosure contract). Derived from
    the SAME collapse helper, so it never drifts from the episodes-view n."""
    members = _event_study_members(session, subject, horizon, as_of)
    run_position = _run_position_index(session, as_of)
    return len(_collapse_to_episodes(members, run_position))


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
    # iter-27 (J-86): the stored max-drawdowns over only members with one (same NA discipline as mae/mfe).
    mdds = [m["max_drawdown"] for m in members if m.get("max_drawdown") is not None]
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
        # J-86: the aggregate mean max-drawdown beside the return stats (read-only over stored values).
        "mean_max_drawdown": _mean_or_none(mdds),
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
    session: Session, subject_key: str, horizon: int, config: Optional[Config] = None, *,
    as_of: Optional[date_cls] = None, view: str = VIEW_EPISODES,
) -> dict:
    """The SINGLE canonical Setup & Pattern event study (Data Contract value, J-29 / J-63) for `subject_key`
    at the selected `horizon` under the chosen overlap-honesty `view`. Pools EVERY historical occurrence of
    the subject (a setup OR a detected pattern) across all immutable snapshots and reports, per configured
    horizon, the forward-return distribution (mean / median / %positive / dispersion) + expectancy + mean
    MAE / MFE + the downside-only risk-adjusted ratios (return/downside-dev AND return/mean-|MAE|), plus the
    best exit-horizon and the by-regime + by-sector slices at the selected horizon — each carrying `n` and
    honest NA.

    `view` (J-63, default `episodes`) makes the study OVERLAP-HONEST: in `episodes` EVERY figure derives
    from the FIRST-TRIGGER episode collapse of the subject's signal-days (each continuous run of a symbol
    triggering the subject counts ONCE, observed at its first trigger date — `_collapse_to_episodes`); in
    `pooled` every figure derives from the raw per-signal-day pool. **`view="pooled"` routes through the
    UNCHANGED pre-J-63 path (the `_event_study_members` list used directly), so its output is BYTE-IDENTICAL
    to the prior published values** — the episode path is purely additive. The payload also carries the
    three disclosure values for the selected horizon, present in BOTH views: `n` (observations in the
    current view at the selected horizon — == `n_total`), `unique_symbols` (distinct tickers in that set),
    and `episode_count` (distinct first-trigger episodes — identical in both views since it counts episodes
    regardless of which view renders). `view` is a cohort/MODE selector ONLY — orthogonal to `?asof`, the
    global as-of, and the analysis-mode `mode` state. Raises `ValueError` for an unknown view.

    READ-ONLY (the keystone anti-goal): derived ENTIRELY from stored values — `forward_returns`
    (`realized_return` + the iter-14 `mae` / `mfe`, read VERBATIM) JOINED to the stored `scanner_results`
    (setup status + the pattern mirror flags) and `scanner_runs.regime_label` (verbatim). It issues ONLY
    SELECTs and pure stats (the episode collapse is a pure in-memory grouping of stored rows — recomputes
    no return / excursion / score / regime / pattern); it calls NO scoring / regime / return / excursion /
    pattern math (no run_scan, score_stocks, backfill*, forward_return, forward_excursions, detect_*,
    score_regime). In `pooled` it pools the SAME per-observation rows `compute_forward_aggregates` groups,
    so the pooled mean for a subject at horizon h equals the matching `by_setup` / `by_<pattern>` cohort mean
    (the consistency invariant, unit-asserted). Risk is downside-only everywhere (never total volatility).

    `as_of` (iter-19, J-32) optionally scopes EVERY pooled member (and the episode run-ordinal index) to
    snapshots dated <= D — threaded through the per-horizon LOOP (and the defensive direct-call fallback) so
    every horizon row, the by-regime and the by-sector slices reflect the SAME point-in-time window (the
    iter-17 seam — recomputes nothing). The payload echoes the resolved cutoff as `asof_date` (ISO) when
    scoped, else `null`; `as_of=None` is byte-identical all-history. Raises `ValueError` for an unknown
    subject (the API pre-validates -> 422)."""
    cfg = config or get_config()
    wf = cfg.walk_forward
    subjects = subject_catalog(cfg)

    if view not in ALL_VIEWS:
        raise ValueError(f"unknown view {view!r}; valid views are {list(ALL_VIEWS)}")

    subject = next((s for s in subjects if s["key"] == subject_key), None)
    if subject is None:
        raise ValueError(
            f"unknown subject {subject_key!r}; valid subjects are {[s['key'] for s in subjects]}"
        )

    # J-72 SINGLE-BATCHED-READ: load EVERY configured horizon's pooled members in ONE batched read
    # (`_event_study_members_by_horizon`) instead of one `ForwardReturn` scan per horizon. The selected
    # horizon (when not in `wf.horizons` — a defensive direct-call path) is added to the batch so its
    # members come from the same single read. The per-horizon lists are byte-identical to the per-horizon
    # builder (deterministic id-ordered results). The episode collapse stays a pure in-memory grouping of
    # those SAME stored rows (J-63 untouched).
    batch_horizons = list(wf.horizons)
    if horizon not in batch_horizons:
        batch_horizons = batch_horizons + [horizon]
    pooled_by_h = _event_study_members_by_horizon(session, subject, batch_horizons, as_of, cfg=cfg)
    # the episode collapse needs the GLOBAL ordered run-date sequence (same as-of window); loaded ONCE and
    # reused across horizons. Built whenever episodes is the view OR the (view-independent) episode_count
    # disclosure is needed — a single SELECT, never per-horizon.
    run_position = _run_position_index(session, as_of)

    def _view_members(h: int) -> list[dict]:
        members = pooled_by_h[h]
        if view == VIEW_POOLED:
            return members  # unchanged pooled list — byte-identical to pre-J-63
        return _collapse_to_episodes(members, run_position)  # first-trigger episode collapse

    by_horizon: list[dict] = []
    selected_members: Optional[list[dict]] = None
    episode_count = 0
    for h in wf.horizons:
        members = _view_members(h)
        by_horizon.append(_event_study_horizon_row(members, h, wf.min_sample))
        if h == horizon:
            selected_members = members
            # episode_count is view-independent: the distinct first-trigger episodes at the selected
            # horizon. In the episodes view `selected_members` ARE the episodes; in pooled, collapse here.
            episode_count = (
                len(selected_members) if view == VIEW_EPISODES
                else len(_collapse_to_episodes(pooled_by_h[h], run_position))
            )
    if selected_members is None:  # horizon not in wf.horizons (API validates; defensive for direct calls)
        selected_members = _view_members(horizon)
        episode_count = len(_collapse_to_episodes(pooled_by_h[horizon], run_position))

    unique_symbols = len({m["ticker"] for m in selected_members})

    return {
        "subject": subject,
        "horizon": horizon,
        # the resolved as-of scoping cutoff echoed (J-32) — ISO date when scoped, null in all-history mode
        "asof_date": as_of.isoformat() if as_of is not None else None,
        "view": view,  # J-63: the resolved overlap-honesty view (episodes default | pooled)
        "subjects": subjects,
        "horizons": list(wf.horizons),
        "default_horizon": wf.default_horizon,
        "min_sample": wf.min_sample,
        "survivorship_bias": SURVIVORSHIP_BIAS_LABEL,
        "descriptive_caveat": RESEARCH_CAVEAT,
        "n_total": len(selected_members),
        # J-63 disclosure values for the selected horizon (present in BOTH views) — overlap is never hidden
        "n": len(selected_members),
        "unique_symbols": unique_symbols,
        "episode_count": episode_count,
        "by_horizon": by_horizon,
        "best_exit_horizon": _best_exit_horizon(by_horizon),
        "by_regime": _event_study_by_regime(selected_members, cfg),
        "by_sector": _event_study_by_sector(selected_members, cfg),
    }


# --------------------------------------------------------------------------------------------------
# Event-study derived-aggregate cache (J-72) — serve `compute_event_study` from a persisted/cached
# aggregate that REFRESHES after any dataset change. The figures are BYTE-IDENTICAL to a fresh compute
# (a cache of the deterministic read-only aggregation, never a recompute, never a second value).
# --------------------------------------------------------------------------------------------------
# The all-history sentinel for the cache key's as-of slot (so an all-history aggregate never collides
# with an as-of-scoped one). A fixed structural label, not a tunable.
_ASOF_ALL = "all"


def _dataset_version(session: Session) -> str:
    """A stamp derived from the stored state that CHANGES whenever the dataset changes (J-72 cache
    invalidation). Combines the max `scanner_runs.id` (changes when a backfill adds a snapshot, or the
    max drops when the newest is removed) with the `forward_returns` row count (changes when returns are
    added or a removal cascade deletes them). A read computes the CURRENT stamp and looks up the cache by
    THIS exact stamp — a row keyed to an older stamp is never hit (and is pruned on write), so the cache
    can never serve a stale figure (it refreshes after any dataset change). A pure read (two scalar
    SELECTs); recomputes no aggregate."""
    max_run_id = session.exec(select(func.max(ScannerRun.id))).one()
    # `func.max` over an empty table is None; `func.count` is 0 — both stringify deterministically.
    if isinstance(max_run_id, tuple):  # some drivers return a 1-tuple row
        max_run_id = max_run_id[0]
    fr_count = session.exec(select(func.count()).select_from(ForwardReturn)).one()
    if isinstance(fr_count, tuple):
        fr_count = fr_count[0]
    return f"r{max_run_id or 0}-f{fr_count or 0}"


def _membership_dataset_version(session: Session, config: Optional[Config] = None) -> str:
    """A NARROWER cache stamp for the J-96 membership-timeline cache (iter-42 / J-100). It depends ONLY on
    the inputs the membership timeline actually reads — the snapshot/`ScannerRun.asof_date` set, the bars
    manifest, and the history threshold config — and NOT on the `forward_returns` row count.

    Why a second stamp: `_dataset_version` (the J-72/J-87 event-study/market-phase stamp) folds in
    `count(forward_returns)`, so EVERY warm-up forward-return insert bumped it and re-invalidated the
    membership cache (a recompute storm — the iter-42 J-100 root cause). The membership timeline reads the
    persisted per-snapshot `ScannerResult` membership + the bars (`date <= D`) + the `min_history_bars`
    threshold; it reads NO forward return. So its cache must refresh on a real membership change — a
    backfill that adds a snapshot or bars, a removal/rebuild that drops them — but NOT on a pure
    forward-return insert. This stamp encodes exactly those inputs:

      - `max(scanner_runs.id)`     — bumps when a snapshot is added (or the max drops when the newest is
                                     removed) — a NEW membership observation row.
      - `count(scanner_runs)`      — disambiguates an add-then-remove that leaves max(id) unchanged but the
                                     snapshot SET changed (a removed-then-re-added run gets a new id, but
                                     counting guards the symmetric case).
      - `max(daily_prices.date)` + `count(daily_prices)` — the bars manifest: a backfill/fetch that adds
                                     bars (changing which candidates clear the history gate at a date) or a
                                     removal that drops bars changes one of these. `forward_returns` rows
                                     are NOT bars, so a forward-return insert leaves both untouched.
      - `min_history_bars`         — the only config input the per-date resolver's history gate reads; if it
                                     were retuned the admitted set would change, so it belongs in the stamp.

    Like `_dataset_version` this is a pure read (a few scalar SELECTs); it recomputes no canonical value and
    appears in NO served payload — it is an internal cache-invalidation input only. A forward-return-only
    insert leaves every term above unchanged, so the membership cache HITS across forward-return churn (no
    recompute storm); a snapshot add/remove or a bar backfill changes a term, so the cache correctly
    invalidates and recomputes."""
    cfg = config or get_config()
    max_run_id = session.exec(select(func.max(ScannerRun.id))).one()
    if isinstance(max_run_id, tuple):
        max_run_id = max_run_id[0]
    run_count = session.exec(select(func.count()).select_from(ScannerRun)).one()
    if isinstance(run_count, tuple):
        run_count = run_count[0]
    max_bar_date = session.exec(select(func.max(DailyPrice.date))).one()
    if isinstance(max_bar_date, tuple):
        max_bar_date = max_bar_date[0]
    bar_count = session.exec(select(func.count()).select_from(DailyPrice)).one()
    if isinstance(bar_count, tuple):
        bar_count = bar_count[0]
    bar_stamp = max_bar_date.isoformat() if max_bar_date is not None else "none"
    return (
        f"r{max_run_id or 0}-rc{run_count or 0}"
        f"-b{bar_stamp}-bc{bar_count or 0}"
        f"-h{cfg.indicators.min_history_bars}"
    )


def _cache_asof_key(as_of: Optional[date_cls]) -> str:
    """The cache key's as-of slot: the resolved ISO date when scoped, else the all-history sentinel."""
    return as_of.isoformat() if as_of is not None else _ASOF_ALL


def event_study_cached(
    session: Session, subject_key: str, horizon: int, config: Optional[Config] = None, *,
    as_of: Optional[date_cls] = None, view: str = VIEW_EPISODES,
) -> dict:
    """Serve the event study from the J-72 cache: on a cache HIT for the current
    `(subject, view, asof_key, dataset_version, horizon)` key, deserialize and return the stored
    aggregate (NO recompute); on a MISS, compute it ONCE via `compute_event_study`, persist it under the
    current dataset-version stamp, prune any stale rows for this analysis identity, and return it. The
    returned payload is BYTE-IDENTICAL to `compute_event_study(...)` — the cache is a pure performance
    layer (No recompute in the read path). Because the key carries the dataset-version stamp, the cache
    REFRESHES automatically after any dataset change (a backfill add or a removal) — a stale row is never
    hit. Validation (unknown subject/view -> ValueError) happens in `compute_event_study`, so an invalid
    request never writes a cache row (the compute raises before the write)."""
    cfg = config or get_config()
    subject_key = subject_key  # validated downstream
    version = _dataset_version(session)
    asof_key = _cache_asof_key(as_of)

    hit = session.exec(
        select(EventStudyCache).where(
            EventStudyCache.subject == subject_key,
            EventStudyCache.view == view,
            EventStudyCache.asof_key == asof_key,
            EventStudyCache.dataset_version == version,
            EventStudyCache.horizon == horizon,
        )
    ).first()
    if hit is not None:
        return json.loads(hit.payload_json)

    # MISS — compute once (this also validates subject/view, raising before any write) and persist.
    payload = compute_event_study(session, subject_key, horizon, cfg, as_of=as_of, view=view)

    # prune stale rows for THIS analysis identity (any older dataset_version) so the cache table does not
    # grow unbounded as the dataset matures; the current-version row is then upserted.
    stale = session.exec(
        select(EventStudyCache).where(
            EventStudyCache.subject == subject_key,
            EventStudyCache.view == view,
            EventStudyCache.asof_key == asof_key,
            EventStudyCache.horizon == horizon,
            EventStudyCache.dataset_version != version,
        )
    ).all()
    for row in stale:
        session.delete(row)

    session.add(EventStudyCache(
        subject=subject_key, view=view, asof_key=asof_key, dataset_version=version,
        horizon=horizon, payload_json=json.dumps(payload),
        created_at=datetime.now(timezone.utc),
    ))
    try:
        session.commit()
    except Exception:  # a concurrent writer raced us to the same key — the cache is best-effort, not a
        session.rollback()  # source of truth; the freshly computed payload is still byte-identical, so return it
    return payload


# --------------------------------------------------------------------------------------------------
# Regime × Setup × Pattern ranked combinations study (J-77) — read-only grouping of the SAME enriched
# observation set the event study reads. NO new computation: every figure is a pure grouping of stored
# values (realized return + stored regime + stored setup status + stored pattern mirror flags), so it is
# the SAME read-only class as the J-25 decile sort / J-29 event study. NOT a fitted/learned/ML model.
# --------------------------------------------------------------------------------------------------
# The sentinel pattern value for an observation with NO detected pattern flagged (so a (regime, setup)
# cohort is still represented honestly rather than dropped). A fixed structural label, not a tunable.
PATTERN_NONE = "none"


def _rsp_member(
    run_id, ticker, sector, setup_status, patterns: dict, fr: tuple, regime: Optional[str],
) -> dict:
    """One enriched per-observation row for the J-77 study, read VERBATIM from stored values (no
    recompute): the realized return + stored regime label + stored setup status + stored pattern mirror
    flags. Mirrors the `_event_study_members` enrichment shape so the same downstream helpers
    (`_collapse_to_episodes`, the samples builder) consume it identically. iter-47 (J-105): accepts the
    stored FR VALUE tuple `(realized_return, mae, mfe, max_drawdown)` from the column-projected stream (not
    an ORM `fr`) — same verbatim values, no coercion → byte-identical."""
    realized_return, mae, mfe, max_drawdown = fr
    return {
        "run_id": run_id, "ticker": ticker,
        "return": realized_return, "mae": mae, "mfe": mfe,
        "max_drawdown": max_drawdown,  # iter-27 (J-86) stored MDD read verbatim
        "regime": regime, "sector": sector,
        "setup_status": setup_status,
        "patterns": patterns,
    }


def _regime_setup_pattern_observations(
    session: Session, horizon: int, view: str, cfg: Config, as_of: Optional[date_cls] = None
) -> list[dict]:
    """The SINGLE cross-subject observation set the J-77 study and its samples drill-down BOTH read
    (count-coherence keystone — one membership rule). Pools EVERY stored (run, ticker) that has a realized
    `ForwardReturn` at `horizon` (the SAME `forward_returns`-joined-to-`scanner_results` pool the event
    study / forward aggregates read), each row carrying its stored regime + setup status + pattern flags
    read VERBATIM. SELECT-only + pure grouping; recomputes nothing.

    iter-47 (J-105): the FR scan is column-projected + `yield_per`-streamed to light value tuples (no
    full-table ORM materialization). No subject prune (it pools every FR-bearing result), so the FR scan is
    bounded by the per-horizon row count; the ScannerResult side is read in `ScannerResult.id` order
    (matching the prior implicit-ordering `.all()`) so the pooled list is byte-identical.

    `view` (J-63): in `episodes` (default) the pool is collapsed to first-trigger episodes per ticker
    (`_collapse_to_episodes`, the SAME per-ticker run-ordinal collapse the event study uses); in `pooled`
    every per-signal-day observation survives. `as_of` (J-32) scopes both the members and the run-ordinal
    index to snapshots dated <= D (a FILTER only — no recompute, no second date state)."""
    batch = cfg.research.read_batch_size
    p_keys = pattern_keys(cfg)

    # column-projected + streamed FR scan → `(run_id, symbol) -> (return, mae, mfe, max_drawdown)` value
    # tuple (one row per the unique constraint at this horizon), and the runs the result side needs.
    fr_stmt = select(
        ForwardReturn.run_id, ForwardReturn.symbol,
        ForwardReturn.realized_return, ForwardReturn.mae, ForwardReturn.mfe, ForwardReturn.max_drawdown,
    ).where(ForwardReturn.horizon == horizon)
    if as_of is not None:
        fr_stmt = fr_stmt.join(ScannerRun, ScannerRun.id == ForwardReturn.run_id).where(
            ScannerRun.asof_date <= as_of
        )
    fr_by_run_symbol: dict[tuple[int, str], tuple] = {}
    runs_with_fr: set[int] = set()
    for run_id, symbol, realized_return, mae, mfe, max_drawdown in session.exec(fr_stmt).yield_per(batch):
        fr_by_run_symbol[(run_id, symbol)] = (realized_return, mae, mfe, max_drawdown)
        runs_with_fr.add(run_id)

    regime_by_run = _regime_by_run_projected(session, runs_with_fr, batch)

    # column-projected + streamed ScannerResult side over the FR-bearing runs, in id order (the prior
    # implicit-`.all()` order on SQLite) — project the fields `_rsp_member` reads + the is_<k> flags.
    members: list[dict] = []
    if runs_with_fr:
        flag_cols = [getattr(ScannerResult, f"is_{k}") for k in p_keys]
        res_stmt = (
            select(
                ScannerResult.run_id, ScannerResult.ticker,
                ScannerResult.sector, ScannerResult.setup_status, *flag_cols,
            )
            .where(ScannerResult.run_id.in_(runs_with_fr))
            .order_by(ScannerResult.id)
        )
        for row in session.exec(res_stmt).yield_per(batch):
            run_id, ticker, sector, setup_status = row[0], row[1], row[2], row[3]
            fr = fr_by_run_symbol.get((run_id, ticker))
            if fr is None:
                continue  # no realized return at this horizon for this stock (n=0 contribution)
            patterns = {key: bool(row[4 + i]) for i, key in enumerate(p_keys)}
            members.append(_rsp_member(
                run_id, ticker, sector, setup_status, patterns, fr, regime_by_run.get(run_id)
            ))

    if view == VIEW_POOLED:
        return members
    run_position = _run_position_index(session, as_of)
    return _collapse_to_episodes(members, run_position)


def _observation_pattern_labels(obs: dict, p_keys: list[str]) -> list[str]:
    """The pattern dimension value(s) ONE observation contributes to (J-77): one label per flagged
    pattern key, or the `PATTERN_NONE` sentinel when no pattern is flagged — so an observation matching
    two patterns honestly appears under BOTH (and the samples filter reproduces that exactly), while an
    observation matching none is still counted under its (regime, setup) with pattern=none. Pure read of
    the stored `patterns` flags — recomputes nothing."""
    flagged = [key for key in p_keys if obs["patterns"].get(key)]
    return flagged if flagged else [PATTERN_NONE]


def _rsp_combination_members(obs: dict, p_keys: list[str]) -> list[tuple[str, str, str]]:
    """The (regime, setup, pattern) combination keys ONE observation belongs to — the SAME membership
    rule the aggregate AND the samples drill-down apply, so a combination row's n equals its drill-down
    total by construction (count-coherence keystone). An observation with a NULL stored regime is keyed
    under the literal regime value (None → kept honest via the caller's grouping)."""
    return [
        (obs["regime"], obs["setup_status"], pattern)
        for pattern in _observation_pattern_labels(obs, p_keys)
    ]


def _rsp_combination_filter(obs: dict, regime: str, setup: str, pattern: str, p_keys: list[str]) -> bool:
    """Whether ONE observation belongs to the (regime, setup, pattern) cohort — the SINGLE membership
    predicate BOTH the study aggregate and the samples drill-down use (never a second rule). Pattern
    `PATTERN_NONE` matches observations with no flagged pattern; a real pattern key matches observations
    whose stored `is_<pattern>` mirror is True."""
    if obs["regime"] != regime or obs["setup_status"] != setup:
        return False
    if pattern == PATTERN_NONE:
        return all(not obs["patterns"].get(key) for key in p_keys)
    return bool(obs["patterns"].get(pattern))


def _rsp_stats(returns: list[float], maes: list[float], mdds: list[float], min_sample: int) -> dict:
    """Per-combination descriptive stats over the member realized returns (read-only, J-77): `n`,
    `low_sample` (`n < min_sample`), `mean`, `median`, `pct_positive` (hit-rate), the expectancy
    decomposition, the aggregate mean max-drawdown (iter-27, J-86 — beside the return stats, read-only
    over the stored values), and BOTH downside-only risk-adjusted figures (return/downside-dev REUSING
    `_risk_adjusted`; return/mean-|MAE| REUSING `_return_per_mae`) — never total volatility. An empty
    cohort yields None for every figure (honest NA, never a fabricated 0). The engine computes every
    figure; the UI gates low-sample/empty cells to NA + n."""
    n = len(returns)
    dist = _distribution(returns)  # {mean_return, median, pct_positive, dispersion, n}
    return {
        "n": n,
        "low_sample": n < min_sample,
        "mean": dist["mean_return"],
        "median": dist["median"],
        "pct_positive": dist["pct_positive"],
        "expectancy": _expectancy(returns)["expectancy"],
        "mean_max_drawdown": _mean_or_none(mdds),  # J-86 aggregate mean MDD (same NA discipline)
        "return_per_downside_dev": _risk_adjusted(returns),
        "return_per_mae": _return_per_mae(returns, maes),
    }


def _rsp_rank_key(row: dict) -> tuple:
    """The default ranking key for the J-77 table: descending by the risk-adjusted figure
    (`return_per_downside_dev`), NA last, then by raw mean (NA last), then a deterministic tie-break by
    the (regime, setup, pattern) label so the order is total + reproducible. Returns a tuple usable with
    `reverse=True` — a None metric sorts LAST under reverse via the `(is_not_none, value)` pairing.

    The `is_not_none` boolean ALREADY partitions present-before-None under `reverse=True` (True > False),
    so the metric value is only ever compared between two rows that BOTH have it present. For the
    None case we reuse the `is_not_none` flag itself as the fallback (a structural, non-float comparable
    that equals itself for the both-None pair and is NEVER cross-compared against a float, because a
    differing first element short-circuits the tuple comparison). This carries NO float literal — the
    fallback is structural to the sort, not a tunable scoring value (No magic numbers anti-goal)."""
    ra = row["stats"]["return_per_downside_dev"]
    mean_r = row["stats"]["mean"]
    ra_present = ra is not None
    mean_present = mean_r is not None
    return (
        (ra_present, ra if ra_present else ra_present),
        (mean_present, mean_r if mean_present else mean_present),
    )


def compute_regime_setup_pattern_study(
    session: Session, horizon: int, config: Optional[Config] = None, *,
    as_of: Optional[date_cls] = None, view: str = VIEW_EPISODES,
) -> dict:
    """The SINGLE canonical Regime × Setup × Pattern ranked combinations study (Data Contract value,
    J-77). Groups the SAME cross-subject enriched observation set
    (`_regime_setup_pattern_observations`) — every stored (run, ticker) with a realized forward return at
    `horizon`, carrying its stored regime label + setup status + pattern mirror flags read VERBATIM — by
    the (regime, setup, pattern) key, and reports per combination: `n`, `mean`, `median`, `pct_positive`
    (hit-rate), `expectancy`, and BOTH downside-only risk-adjusted figures (return/downside-dev AND
    return/mean-|MAE| — downside only, NEVER total volatility). Rows are ranked by the risk-adjusted
    figure (default); a combination below `config.walk_forward.min_sample` carries its honest `n` + a
    `low_sample` flag (the UI shows NA + n — never a fabricated number).

    `view` (J-63, default `episodes`) makes the study overlap-honest exactly like the event study; `as_of`
    (J-32) scopes the pool to snapshots dated <= D (a FILTER only — no recompute, no second date state).
    The vocabularies (regime labels, setup statuses, pattern keys) come from the EXISTING config-backed
    catalogs — no hardcoded list. READ-ONLY: SELECT + pure grouping; calls NO scoring/regime/return/
    excursion/pattern math. Raises `ValueError` for an unknown view (the API pre-validates -> 422)."""
    cfg = config or get_config()
    wf = cfg.walk_forward

    if view not in ALL_VIEWS:
        raise ValueError(f"unknown view {view!r}; valid views are {list(ALL_VIEWS)}")

    p_keys = pattern_keys(cfg)
    observations = _regime_setup_pattern_observations(session, horizon, view, cfg, as_of)

    # group the observations into (regime, setup, pattern) cohorts — the SAME membership the samples
    # drill-down reproduces (one rule). Each observation contributes to one cohort per flagged pattern
    # (or the `none` sentinel), so a two-pattern observation honestly counts under both.
    grouped: dict[tuple, dict[str, list]] = defaultdict(lambda: {"returns": [], "maes": [], "mdds": []})
    for obs in observations:
        for key in _rsp_combination_members(obs, p_keys):
            grouped[key]["returns"].append(obs["return"])
            if obs["mae"] is not None:
                grouped[key]["maes"].append(obs["mae"])
            if obs.get("max_drawdown") is not None:  # iter-27 (J-86): stored MDD over the cohort
                grouped[key]["mdds"].append(obs["max_drawdown"])

    rows = [
        {
            "regime": regime,
            "setup": setup,
            "pattern": pattern,
            "stats": _rsp_stats(bucket["returns"], bucket["maes"], bucket["mdds"], wf.min_sample),
        }
        for (regime, setup, pattern), bucket in grouped.items()
    ]
    # default ranking: descending by the risk-adjusted figure (NA last), then raw mean, then a stable
    # deterministic label tie-break so the order is total + reproducible.
    rows.sort(key=lambda r: (r["regime"] or "", r["setup"], r["pattern"]))  # stable inner tie-break first
    rows.sort(key=_rsp_rank_key, reverse=True)

    return {
        "horizon": horizon,
        "asof_date": as_of.isoformat() if as_of is not None else None,
        "view": view,  # J-63 overlap-honesty view (episodes default | pooled)
        "horizons": list(wf.horizons),
        "default_horizon": wf.default_horizon,
        "min_sample": wf.min_sample,
        "regime_labels": list(cfg.regime.labels),
        "setups": list(ALL_STATUSES),
        "patterns": p_keys,
        "pattern_none": PATTERN_NONE,
        "survivorship_bias": SURVIVORSHIP_BIAS_LABEL,
        "descriptive_caveat": RESEARCH_CAVEAT,
        "n_total": len(observations),
        "rows": rows,
    }


# --------------------------------------------------------------------------------------------------
# Recovery-Turn Edge study (J-90) — read-only over the SAME stored `forward_returns` the event study reads,
# pooled over the CAUSAL recovery-turn signal dates (from the read-only `market_phase` derivation, never
# recomputed) and tagged with the causal phase/severity/P(bear) at the signal date. NO new computation:
# every figure is a pure aggregation of stored values (realized return + MAE/MFE + max_drawdown) — the SAME
# read-only class as the J-29 event study. NOT a fitted/learned/ML model. NO order/execution affordance.
# --------------------------------------------------------------------------------------------------
def _recovery_turn_observation_set(
    session: Session, horizon: int, view: str, cfg: Config, as_of: Optional[date_cls] = None
) -> list[dict]:
    """The SINGLE observation set the Recovery-Turn Edge study AND its samples drill-down BOTH read
    (count-coherence keystone — one membership rule). The CAUSAL recovery-turn signal dates come from the
    read-only `market_phase.recovery_turn_dates` derivation (the SAME single timeline the panel reads, <=
    `as_of` when scoped — never recomputed). For each signal date's run, pool EVERY stored `ForwardReturn`
    at `horizon` (its realized return + MAE/MFE + `max_drawdown`, read VERBATIM) joined to its stored
    `ScannerResult` (by run_id + ticker), each tagged with the CAUSAL phase / severity / P(bear) at the
    signal date (read from the derivation, never recomputed). SELECT-only + the read-only derivation; it
    recomputes NO return / excursion / score / regime / signal.

    `view` (J-63): in `episodes` (default) the pooled per-signal-day members are collapsed to first-trigger
    episodes per ticker (`_collapse_to_episodes`, the SAME per-ticker run-ordinal collapse the event study
    uses); in `pooled` every per-signal-day observation survives. `as_of` (J-32) scopes BOTH the signal
    dates and the run-ordinal index to snapshots dated <= D (a FILTER only — no recompute, no second date
    state); `as_of=None` => all-history."""
    from app.engine.market_phase import recovery_turn_dates  # lazy import (avoids a config/research cycle)

    signal_context = recovery_turn_dates(session, as_of, cfg)  # {iso_date: {phase, severity, p_bear, ...}}
    if not signal_context:
        return []

    # the runs whose snapshot date is a recovery-turn signal date (those are the entry dates we study).
    signal_dates = set(signal_context)
    run_rows = session.exec(
        select(ScannerRun).where(ScannerRun.asof_date <= as_of)
        if as_of is not None else select(ScannerRun)
    ).all()
    signal_runs = {run.id: run for run in run_rows if run.asof_date.isoformat() in signal_dates}
    if not signal_runs:
        return []
    signal_run_ids = sorted(signal_runs)

    # the stored forward returns at this horizon for ONLY the signal-date runs (read verbatim). iter-47
    # (J-105): already run_id-bounded to the signal-date runs; column-project + stream the scan to light
    # value tuples (no full-ORM materialization) for consistency with the other builders.
    batch = cfg.research.read_batch_size
    fr_stmt = select(
        ForwardReturn.run_id, ForwardReturn.symbol,
        ForwardReturn.realized_return, ForwardReturn.mae, ForwardReturn.mfe, ForwardReturn.max_drawdown,
    ).where(
        ForwardReturn.horizon == horizon,
        ForwardReturn.run_id.in_(signal_run_ids),
    )
    fr_by_run_symbol: dict[tuple[int, str], tuple] = {}
    runs_with_fr: set[int] = set()
    for run_id, symbol, realized_return, mae, mfe, max_drawdown in session.exec(fr_stmt).yield_per(batch):
        fr_by_run_symbol[(run_id, symbol)] = (realized_return, mae, mfe, max_drawdown)
        runs_with_fr.add(run_id)
    results = (
        session.exec(
            select(ScannerResult).where(ScannerResult.run_id.in_(runs_with_fr)).order_by(ScannerResult.id)
        ).all()
        if runs_with_fr else []
    )

    members: list[dict] = []
    for res in results:
        fr = fr_by_run_symbol.get((res.run_id, res.ticker))
        if fr is None:
            continue  # no realized return at this horizon for this signal-date stock (n=0 contribution)
        realized_return, mae, mfe, max_drawdown = fr
        run = signal_runs[res.run_id]
        context = signal_context[run.asof_date.isoformat()]
        members.append({
            "run_id": res.run_id, "ticker": res.ticker,
            "return": realized_return, "mae": mae, "mfe": mfe,
            "max_drawdown": max_drawdown,  # stored MDD read verbatim (J-86)
            "regime": run.regime_label,       # stored regime label (read verbatim)
            "sector": res.sector,             # stored sector (read verbatim)
            "setup_status": res.setup_status,
            # the CAUSAL market-phase context at the signal date (read from the derivation, never recomputed)
            "signal_date": run.asof_date.isoformat(),
            "signal_phase": context["phase"],
            "signal_severity": context["severity"],
            "signal_p_bear": context["p_bear"],
        })

    if view == VIEW_POOLED:
        return members
    run_position = _run_position_index(session, as_of)
    return _collapse_to_episodes(members, run_position)


def _recovery_turn_horizon_row(members: list[dict], horizon: int, min_sample: int) -> dict:
    """One per-horizon row of the Recovery-Turn Edge study over the signal-date members: the distribution
    (mean / median / %positive / dispersion, REUSING `_distribution`), the expectancy decomposition, the
    mean stored MAE / MFE, the aggregate mean `max_drawdown` (read VERBATIM, J-86), and BOTH downside-only
    risk-adjusted ratios (return/downside-dev REUSING `_risk_adjusted`; return/mean-|MAE| REUSING
    `_return_per_mae`). Carries `n` + `low_sample`. NO total volatility anywhere. Identical shape to
    `_event_study_horizon_row` so the frontend reuses the same renderer."""
    returns = [m["return"] for m in members]
    maes = [m["mae"] for m in members if m["mae"] is not None]
    mfes = [m["mfe"] for m in members if m["mfe"] is not None]
    mdds = [m["max_drawdown"] for m in members if m.get("max_drawdown") is not None]
    n = len(returns)
    dist = _distribution(returns)
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
        "mean_max_drawdown": _mean_or_none(mdds),
        "return_per_downside_dev": _risk_adjusted(returns),
        "return_per_mae": _return_per_mae(returns, maes),
    }


def _recovery_turn_by_phase(members: list[dict], cfg: Config) -> list[dict]:
    """The by-signal-phase slice at the selected horizon: one row per CONFIGURED phase label
    (`config.market_phase.labels` order — no hard-coded phase list), each with its per-phase `n`,
    `low_sample`, `mean_return`, `hit_rate`, and downside `risk_adjusted`. Members are grouped by their
    CAUSAL signal-date phase (read from the derivation, never recomputed). Every label emits a row even at
    n=0 (honest NA — never omitted). Conditions the edge on the causal phase/severity/P(bear) at the
    signal date (the study's conditioning leg)."""
    min_sample = cfg.walk_forward.min_sample
    by_phase: dict[str, list[float]] = defaultdict(list)
    for member in members:
        by_phase[member["signal_phase"]].append(member["return"])
    rows: list[dict] = []
    for label in cfg.market_phase.labels:
        returns = by_phase.get(label, [])
        n = len(returns)
        rows.append({
            "phase": label,
            "n": n,
            "low_sample": n < min_sample,
            "mean_return": _mean_or_none(returns),
            "hit_rate": (sum(1 for r in returns if r > 0) / n) if returns else None,
            "risk_adjusted": _risk_adjusted(returns),
        })
    return rows


def compute_recovery_turn_edge(
    session: Session, horizon: int, config: Optional[Config] = None, *,
    as_of: Optional[date_cls] = None, view: str = VIEW_EPISODES,
) -> dict:
    """The SINGLE canonical Recovery-Turn Edge study (Data Contract value, J-90) for the selected `horizon`
    under the chosen overlap-honesty `view`. Pools EVERY stored (run, ticker) observation whose run's
    snapshot date is a CAUSAL recovery-turn signal date (from the read-only `market_phase` derivation —
    never recomputed) and reports, per configured horizon, the forward-return distribution (mean / median /
    %positive / dispersion) + expectancy + mean MAE/MFE + the downside-only risk-adjusted ratios + the
    aggregate mean max-drawdown, plus the best exit-horizon and the by-signal-phase slice at the selected
    horizon (the causal-phase conditioning leg). Each carries `n` and honest NA.

    READ-ONLY (the keystone anti-goal): every figure is derived ENTIRELY from stored values —
    `forward_returns` (realized return + MAE/MFE + `max_drawdown`, read VERBATIM) JOINED to stored
    `scanner_results` + the read-only recovery-turn derivation — it recomputes NO return / excursion /
    score / regime / signal. Risk is downside-only everywhere (never total volatility). `view` (J-63,
    default `episodes`) makes the study overlap-honest; `as_of` (J-32) scopes the pool to snapshots dated
    <= D (a FILTER only). The payload echoes the resolved cutoff as `asof_date` (ISO) when scoped, else
    null. Raises `ValueError` for an unknown view (the API pre-validates -> 422). NO order/execution path
    (recovery-only descriptive evidence)."""
    cfg = config or get_config()
    wf = cfg.walk_forward

    if view not in ALL_VIEWS:
        raise ValueError(f"unknown view {view!r}; valid views are {list(ALL_VIEWS)}")

    by_horizon: list[dict] = []
    selected_members: list[dict] = []
    for h in wf.horizons:
        members = _recovery_turn_observation_set(session, h, view, cfg, as_of)
        by_horizon.append(_recovery_turn_horizon_row(members, h, wf.min_sample))
        if h == horizon:
            selected_members = members
    if horizon not in wf.horizons:  # a defensive direct-call path (API validates horizon)
        selected_members = _recovery_turn_observation_set(session, horizon, view, cfg, as_of)

    unique_symbols = len({m["ticker"] for m in selected_members})
    signal_dates = sorted({m["signal_date"] for m in selected_members})

    return {
        "horizon": horizon,
        "asof_date": as_of.isoformat() if as_of is not None else None,
        "view": view,  # J-63 overlap-honesty view (episodes default | pooled)
        "horizons": list(wf.horizons),
        "default_horizon": wf.default_horizon,
        "min_sample": wf.min_sample,
        "phase_labels": list(cfg.market_phase.labels),
        "survivorship_bias": SURVIVORSHIP_BIAS_LABEL,
        "descriptive_caveat": RESEARCH_CAVEAT,
        "n_total": len(selected_members),
        "n": len(selected_members),
        "unique_symbols": unique_symbols,
        "signal_dates": signal_dates,
        "signal_count": len(signal_dates),
        "by_horizon": by_horizon,
        "best_exit_horizon": _best_exit_horizon(by_horizon),
        "by_phase": _recovery_turn_by_phase(selected_members, cfg),
    }


# The sentinel `subject` slot the Recovery-Turn Edge study reuses in the SHARED `EventStudyCache` table —
# so its cache rows never collide with a real event-study subject (every real subject is a setup status or
# a pattern key; the leading `__` makes this impossible to clash). Reusing the same cache table keeps the
# cache machinery single-sourced (no second cache mechanism, no new table — iter-20 lesson).
_RECOVERY_TURN_EDGE_SUBJECT = "__recovery_turn_edge__"


def recovery_turn_edge_cached(
    session: Session, horizon: int, config: Optional[Config] = None, *,
    as_of: Optional[date_cls] = None, view: str = VIEW_EPISODES,
) -> dict:
    """Serve the Recovery-Turn Edge study from the J-72 cache (mirrors `event_study_cached`), reusing the
    SHARED `EventStudyCache` table under the `_RECOVERY_TURN_EDGE_SUBJECT` sentinel so it never collides
    with a real event-study subject. On a HIT for the current `(sentinel, view, asof_key, dataset_version,
    horizon)` key, return the stored payload (NO recompute); on a MISS, compute it ONCE via
    `compute_recovery_turn_edge` (which validates the view, raising before any write), persist under the
    current stamp, prune stale rows for this identity, and return it. BYTE-IDENTICAL to a fresh compute
    (a pure performance layer); the cache REFRESHES after any dataset change via the dataset-version key."""
    cfg = config or get_config()
    version = _dataset_version(session)
    asof_key = _cache_asof_key(as_of)

    hit = session.exec(
        select(EventStudyCache).where(
            EventStudyCache.subject == _RECOVERY_TURN_EDGE_SUBJECT,
            EventStudyCache.view == view,
            EventStudyCache.asof_key == asof_key,
            EventStudyCache.dataset_version == version,
            EventStudyCache.horizon == horizon,
        )
    ).first()
    if hit is not None:
        return json.loads(hit.payload_json)

    payload = compute_recovery_turn_edge(session, horizon, cfg, as_of=as_of, view=view)

    stale = session.exec(
        select(EventStudyCache).where(
            EventStudyCache.subject == _RECOVERY_TURN_EDGE_SUBJECT,
            EventStudyCache.view == view,
            EventStudyCache.asof_key == asof_key,
            EventStudyCache.horizon == horizon,
            EventStudyCache.dataset_version != version,
        )
    ).all()
    for row in stale:
        session.delete(row)

    session.add(EventStudyCache(
        subject=_RECOVERY_TURN_EDGE_SUBJECT, view=view, asof_key=asof_key, dataset_version=version,
        horizon=horizon, payload_json=json.dumps(payload),
        created_at=datetime.now(timezone.utc),
    ))
    try:
        session.commit()
    except Exception:  # best-effort cache; a concurrent writer raced us — the payload is byte-identical
        session.rollback()
    return payload


# --------------------------------------------------------------------------------------------------
# Downtrend Opportunity study (J-91) — read-only over the SAME enriched event-study observation set, each
# observation ADDITIVELY tagged with the CAUSAL as-of phase / severity band / P(bear) band at its snapshot
# date (from the read-only `market_phase` derivation, <= D — never recomputed; the FILTERED P(bear) only,
# never the J-89 SMOOTHED/true-bear fence). NO new computation: every figure is a pure grouping of stored
# values (realized return + MAE/MFE + max_drawdown) by a causal conditioning tag — the SAME read-only class
# as the J-29 event study. NOT a fitted/learned/ML model. The weakness angle is EVIDENCE ONLY — no
# order/execution/short-deployment affordance. Angle (c) REUSES `compute_recovery_turn_edge` verbatim.
# --------------------------------------------------------------------------------------------------
# The three conditioning DIMENSIONS the study groups by. A fixed structural vocabulary (not a tunable) —
# `phase` reads `config.market_phase.labels`; `severity_band`/`pbear_band` read the config-backed band
# catalogs (`config.research.downtrend_opportunity`). The samples drill-down validates a requested
# dimension against this set (422 otherwise).
DIM_PHASE = "phase"
DIM_SEVERITY_BAND = "severity_band"
DIM_PBEAR_BAND = "pbear_band"
ALL_DOWNTREND_DIMENSIONS = (DIM_PHASE, DIM_SEVERITY_BAND, DIM_PBEAR_BAND)


def _band_for(value: Optional[float], bands: list) -> Optional[str]:
    """The band KEY a continuous reading falls in (J-91): the first `ConditioningBand` whose
    `min <= value < max`, with the band whose `max` is the scale top INCLUSIVE at `max` (so the very top of
    the scale is covered). None when `value` is None (an honest no-tag — never fabricated). The catalog is
    boot-validated contiguous + full-cover, so every non-null reading lands in exactly one band."""
    if value is None:
        return None
    scale_top = max(b.max for b in bands)
    for band in bands:
        if band.min <= value < band.max:
            return band.key
        if value == band.max == scale_top:
            return band.key
    return None  # defensive: a value outside [0, scale_top] (the catalog is validated to cover the scale)


def _downtrend_opportunity_observation_set(
    session: Session, horizon: int, view: str, cfg: Config, as_of: Optional[date_cls] = None
) -> list[dict]:
    """The SINGLE observation set the Downtrend Opportunity study AND its samples drill-down BOTH read
    (count-coherence keystone — one membership rule). Pools the SAME enriched event-study observations
    (`_regime_setup_pattern_observations` — every stored (run, ticker) with a realized `ForwardReturn` at
    `horizon`, each carrying its stored regime/setup/pattern/sector + realized return + MAE/MFE +
    max_drawdown read VERBATIM), then ADDITIVELY tags each with the CAUSAL as-of phase / severity band /
    P(bear) band at its snapshot date (from the read-only `market_phase.phase_context_by_date` derivation,
    <= the resolved as-of — never recomputed; the FILTERED P(bear) only, never the J-89 SMOOTHED fence).
    An observation whose snapshot date has no derivable causal context (insufficient history) carries
    `phase=None`/band=None and is honestly EXCLUDED from a conditioned cohort (never fabricated).

    `view` (J-63): episodes (default — first-trigger collapse) | pooled (per-signal-day) — reuses the SAME
    `_regime_setup_pattern_observations` collapse so the conditioning rides the SAME membership. `as_of`
    (J-32) scopes BOTH the observation pool and the causal context to snapshots dated <= D (a FILTER only —
    no recompute, no second date state). SELECT-only + the read-only derivation; recomputes NO return /
    excursion / score / regime / phase / signal."""
    from app.engine.market_phase import phase_context_by_date  # lazy import (avoids a config/research cycle)

    members = _regime_setup_pattern_observations(session, horizon, view, cfg, as_of)
    if not members:
        return []
    # the CAUSAL phase/severity/P(bear) at each snapshot date (<= the resolved as-of) — read from the SAME
    # single derivation the panel reads (never a second computation, never the SMOOTHED retrospective).
    context_by_date = phase_context_by_date(session, as_of, cfg)
    # iter-45 (J-104b): the run-date map BOUNDED to snapshots dated <= the resolved as-of (no full-table
    # scan). The members already came from `_regime_setup_pattern_observations(... as_of)` (only runs <= D),
    # so a bound run-date map covers every member's run; an as-of-scoped read no longer loads the entire run
    # table. `as_of=None` keeps the all-history scan (every run is in scope — byte-identical to before).
    run_date_stmt = select(ScannerRun.id, ScannerRun.asof_date)
    if as_of is not None:
        run_date_stmt = run_date_stmt.where(ScannerRun.asof_date <= as_of)
    run_dates = {run_id: asof.isoformat() for run_id, asof in session.exec(run_date_stmt).all()}

    do = cfg.research.downtrend_opportunity
    tagged: list[dict] = []
    for obs in members:
        signal_date = run_dates.get(obs["run_id"])
        ctx = context_by_date.get(signal_date) if signal_date is not None else None
        phase = ctx["phase"] if ctx is not None else None
        severity = ctx["severity"] if ctx is not None else None
        p_bear = ctx["p_bear"] if ctx is not None else None
        tagged.append({
            **obs,
            "signal_date": signal_date,
            "signal_phase": phase,
            "signal_severity": severity,
            "signal_p_bear": p_bear,
            "signal_severity_band": _band_for(severity, do.severity_bands),
            "signal_pbear_band": _band_for(p_bear, do.pbear_bands),
        })
    return tagged


def _downtrend_member_dimension_value(obs: dict, dimension: str) -> Optional[str]:
    """The band/label value ONE observation contributes to for a conditioning `dimension` (J-91) — the
    SAME membership rule the aggregate AND the samples drill-down apply (so a cohort's n equals its
    drill-down total by construction). None when the observation has no causal tag for that dimension
    (insufficient history) — honestly excluded from a conditioned cohort, never fabricated."""
    if dimension == DIM_PHASE:
        return obs["signal_phase"]
    if dimension == DIM_SEVERITY_BAND:
        return obs["signal_severity_band"]
    if dimension == DIM_PBEAR_BAND:
        return obs["signal_pbear_band"]
    return None


def _downtrend_dimension_catalog(cfg: Config) -> dict[str, list[dict]]:
    """The config-driven conditioning vocabulary served in the payload (J-91): per dimension an ordered
    list of `{key, label}` cohorts. `phase` reads `config.market_phase.labels`; the two band dimensions
    read the config-backed band catalogs. No hard-coded list — a config-added phase/band flows through with
    no code change. The study emits one row per (dimension, catalog entry) cohort, even at n=0 (honest NA)."""
    do = cfg.research.downtrend_opportunity
    return {
        DIM_PHASE: [{"key": label, "label": label} for label in cfg.market_phase.labels],
        DIM_SEVERITY_BAND: [{"key": b.key, "label": b.label} for b in do.severity_bands],
        DIM_PBEAR_BAND: [{"key": b.key, "label": b.label} for b in do.pbear_bands],
    }


def _downtrend_cohort_stats(members: list[dict], min_sample: int) -> dict:
    """Per-cohort descriptive stats over the conditioned members' realized returns (read-only, J-91): `n`,
    `low_sample`, `mean`, `median`, `pct_positive` (hit-rate), `expectancy`, the aggregate mean
    max-drawdown, and BOTH downside-only risk-adjusted figures (return/downside-dev REUSING `_risk_adjusted`;
    return/mean-|MAE| REUSING `_return_per_mae`) — never total volatility. An empty cohort yields None for
    every figure (honest NA, never a fabricated 0). Mirrors `_rsp_stats` so the frontend reuses the renderer."""
    returns = [m["return"] for m in members]
    maes = [m["mae"] for m in members if m["mae"] is not None]
    mdds = [m["max_drawdown"] for m in members if m.get("max_drawdown") is not None]
    n = len(returns)
    dist = _distribution(returns)
    return {
        "n": n,
        "low_sample": n < min_sample,
        "mean": dist["mean_return"],
        "median": dist["median"],
        "pct_positive": dist["pct_positive"],
        "expectancy": _expectancy(returns)["expectancy"],
        "mean_max_drawdown": _mean_or_none(mdds),
        "return_per_downside_dev": _risk_adjusted(returns),
        "return_per_mae": _return_per_mae(returns, maes),
    }


def _downtrend_angle_rows(
    observations: list[dict], cfg: Config, *, reverse: bool
) -> list[dict]:
    """The ranked conditioned-cohort rows for ONE angle (J-91). Groups the tagged observations by EVERY
    (dimension, catalog cohort) key (each emitted even at n=0 — honest NA, never omitted), computes the
    per-cohort stats, and ranks by the downside risk-adjusted figure (NA last), then raw mean (NA last),
    then a deterministic (dimension, cohort) label tie-break. `reverse=True` ranks BEST-first (angle a —
    held up best); `reverse=False` ranks WORST-first (angle b — fell hardest, EVIDENCE ONLY). Both angles
    rank the SAME cohorts (one grouping) — only the direction + presentation differ; the samples drill-down
    keys on (dimension, cohort) so it reproduces either angle's row byte-for-byte (count-coherence)."""
    wf = cfg.walk_forward
    catalog = _downtrend_dimension_catalog(cfg)
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for obs in observations:
        for dimension in ALL_DOWNTREND_DIMENSIONS:
            value = _downtrend_member_dimension_value(obs, dimension)
            if value is None:
                continue  # an observation with no causal tag for this dimension is honestly excluded
            grouped[(dimension, value)].append(obs)

    rows: list[dict] = []
    for dimension in ALL_DOWNTREND_DIMENSIONS:
        for entry in catalog[dimension]:
            members = grouped.get((dimension, entry["key"]), [])
            rows.append({
                "dimension": dimension,
                "cohort": entry["key"],
                "cohort_label": entry["label"],
                "stats": _downtrend_cohort_stats(members, wf.min_sample),
            })

    # stable inner tie-break (dimension, cohort) first, then rank by the risk-adjusted figure (NA last via
    # the (is_not_none, value) pairing the J-77 study uses), then raw mean. `reverse` flips best/worst.
    rows.sort(key=lambda r: (r["dimension"], r["cohort"]))
    rows.sort(key=_downtrend_rank_key, reverse=reverse)
    return rows


def _downtrend_rank_key(row: dict) -> tuple:
    """The ranking key for the Downtrend Opportunity angles (J-91): by the downside risk-adjusted figure
    (`return_per_downside_dev`), NA last, then raw mean (NA last). Returns a tuple usable with both
    `reverse=True` (best-first, angle a) and `reverse=False` (worst-first, angle b). The `is_not_none`
    boolean partitions present-before-None, and the fallback reuses that flag so a None metric is NEVER
    cross-compared against a float (the SAME structural pattern `_rsp_rank_key` uses — no float literal,
    so the No-magic-numbers contract holds)."""
    ra = row["stats"]["return_per_downside_dev"]
    mean_r = row["stats"]["mean"]
    ra_present = ra is not None
    mean_present = mean_r is not None
    return (
        (ra_present, ra if ra_present else ra_present),
        (mean_present, mean_r if mean_present else mean_present),
    )


def compute_downtrend_opportunity_study(
    session: Session, horizon: int, config: Optional[Config] = None, *,
    as_of: Optional[date_cls] = None, view: str = VIEW_EPISODES,
) -> dict:
    """The SINGLE canonical Downtrend Opportunity study (Data Contract value, J-91) for the selected
    `horizon` under the chosen overlap-honesty `view`. Conditions the EXISTING forward-return evidence on
    the CAUSAL as-of downtrend state (phase / severity band / P(bear) band, all <= D) and returns THREE
    angles:
      - (a) `held_up_best` — the conditioned cohorts with the STRONGEST forward returns (best-first).
      - (b) `fell_hardest` — the conditioned cohorts with the WORST forward returns / deepest drawdown
        (worst-first). EVIDENCE ONLY — no order/execution/short-deployment affordance.
      - (c) `recovery_turn_edge` — the EXISTING J-90 `compute_recovery_turn_edge` surfaced in the same
        panel (REUSED verbatim — never re-derived).

    Angles (a)+(b) rank the SAME conditioned cohorts (one grouping of `_downtrend_opportunity_observation_set`),
    each cohort carrying per-horizon-selected forward-return stats (n, mean, median, %-positive/hit-rate,
    expectancy, downside-only risk-adjusted [return/downside-dev, return/|MAE|], aggregate max-drawdown).
    A cohort below `config.walk_forward.min_sample` carries its honest `n` + a `low_sample` flag (the UI
    shows NA + n). The conditioning vocabulary comes from the config-backed catalog (no hard-coded list).

    READ-ONLY (the keystone anti-goal): every figure is derived ENTIRELY from stored values —
    `forward_returns` (realized return + MAE/MFE + `max_drawdown`, read VERBATIM) JOINED to stored
    `scanner_results` + the read-only `market_phase` causal context — it recomputes NO return / excursion /
    score / regime / phase / signal. The additive causal-tag enrichment leaves `compute_event_study` /
    `compute_regime_setup_pattern_study` / `compute_recovery_turn_edge` figures byte-identical (assert).
    Risk is downside-only everywhere. `view` (J-63) makes the study overlap-honest; `as_of` (J-32) scopes
    the pool + the causal context to snapshots dated <= D (a FILTER only). Raises `ValueError` for an
    unknown view (the API pre-validates -> 422). NO order/execution path (downtrend-conditioned descriptive
    evidence only)."""
    cfg = config or get_config()
    wf = cfg.walk_forward

    if view not in ALL_VIEWS:
        raise ValueError(f"unknown view {view!r}; valid views are {list(ALL_VIEWS)}")

    observations = _downtrend_opportunity_observation_set(session, horizon, view, cfg, as_of)

    held_up_best = _downtrend_angle_rows(observations, cfg, reverse=True)
    fell_hardest = _downtrend_angle_rows(observations, cfg, reverse=False)

    # angle (c): the EXISTING J-90 recovery-turn edge surfaced in the same panel (reused verbatim — its own
    # observation membership, never re-derived here). Served via the cache like the standalone J-90 endpoint.
    recovery_turn_edge = recovery_turn_edge_cached(session, horizon, cfg, as_of=as_of, view=view)

    catalog = _downtrend_dimension_catalog(cfg)
    return {
        "horizon": horizon,
        "asof_date": as_of.isoformat() if as_of is not None else None,
        "view": view,  # J-63 overlap-honesty view (episodes default | pooled)
        "horizons": list(wf.horizons),
        "default_horizon": wf.default_horizon,
        "min_sample": wf.min_sample,
        "dimensions": list(ALL_DOWNTREND_DIMENSIONS),
        # the config-driven conditioning vocabulary (phase labels + the two band catalogs) — the frontend
        # conditioning controls + the cohort labels are built from THIS (no hard-coded list).
        "conditioning_catalog": catalog,
        "phase_labels": list(cfg.market_phase.labels),
        "survivorship_bias": SURVIVORSHIP_BIAS_LABEL,
        "descriptive_caveat": RESEARCH_CAVEAT,
        # an honest disclosure that the weakness angle is research evidence only — never an order/execution
        # path (the *No order/execution path* critical anti-goal, surfaced for the UI label).
        "weakness_evidence_only": True,
        "n_total": len(observations),
        # angle (a) + (b): the SAME conditioned cohorts, ranked best-first / worst-first respectively.
        "held_up_best": held_up_best,
        "fell_hardest": fell_hardest,
        # angle (c): the J-90 recovery-turn edge (reused verbatim).
        "recovery_turn_edge": recovery_turn_edge,
    }


# The sentinel `subject` slot the Downtrend Opportunity study reuses in the SHARED `EventStudyCache` table
# (mirroring `_RECOVERY_TURN_EDGE_SUBJECT`) so its cache rows never collide with a real event-study subject
# or the recovery-turn sentinel. Reusing the same cache table keeps the cache machinery single-sourced.
_DOWNTREND_OPPORTUNITY_SUBJECT = "__downtrend_opportunity__"


def downtrend_opportunity_cached(
    session: Session, horizon: int, config: Optional[Config] = None, *,
    as_of: Optional[date_cls] = None, view: str = VIEW_EPISODES,
) -> dict:
    """Serve the Downtrend Opportunity study from the J-72 cache (mirrors `recovery_turn_edge_cached`),
    reusing the SHARED `EventStudyCache` table under the `_DOWNTREND_OPPORTUNITY_SUBJECT` sentinel so it
    never collides with a real event-study subject or the recovery-turn sentinel. On a HIT for the current
    `(sentinel, view, asof_key, dataset_version, horizon)` key, return the stored payload (NO recompute);
    on a MISS, compute it ONCE via `compute_downtrend_opportunity_study` (which validates the view, raising
    before any write), persist under the current stamp, prune stale rows for this identity, and return it.
    BYTE-IDENTICAL to a fresh compute; the cache REFRESHES after any dataset change via the dataset-version
    key."""
    cfg = config or get_config()
    version = _dataset_version(session)
    asof_key = _cache_asof_key(as_of)

    hit = session.exec(
        select(EventStudyCache).where(
            EventStudyCache.subject == _DOWNTREND_OPPORTUNITY_SUBJECT,
            EventStudyCache.view == view,
            EventStudyCache.asof_key == asof_key,
            EventStudyCache.dataset_version == version,
            EventStudyCache.horizon == horizon,
        )
    ).first()
    if hit is not None:
        return json.loads(hit.payload_json)

    payload = compute_downtrend_opportunity_study(session, horizon, cfg, as_of=as_of, view=view)

    stale = session.exec(
        select(EventStudyCache).where(
            EventStudyCache.subject == _DOWNTREND_OPPORTUNITY_SUBJECT,
            EventStudyCache.view == view,
            EventStudyCache.asof_key == asof_key,
            EventStudyCache.horizon == horizon,
            EventStudyCache.dataset_version != version,
        )
    ).all()
    for row in stale:
        session.delete(row)

    session.add(EventStudyCache(
        subject=_DOWNTREND_OPPORTUNITY_SUBJECT, view=view, asof_key=asof_key, dataset_version=version,
        horizon=horizon, payload_json=json.dumps(payload),
        created_at=datetime.now(timezone.utc),
    ))
    try:
        session.commit()
    except Exception:  # best-effort cache; a concurrent writer raced us — the payload is byte-identical
        session.rollback()
    return payload


# --------------------------------------------------------------------------------------------------
# Severity-velocity × Regime forward-return study (J-103, iter-45) — read-only over the stored SPY
# `forward_returns`, GROUPED by the (regime FAMILY, velocity SIGN) at each snapshot date. The regime family
# is a config-backed grouping of the STORED regime label (read VERBATIM); the velocity sign is the sign of
# the SERVED `severity_velocity` (J-102, read from the read-only `market_phase` derivation — never recomputed
# here). NO new computation: every figure is a pure grouping of the stored benchmark forward returns by two
# already-served conditioning values — the SAME read-only class as the J-29 event study. NOT a fitted/ML
# model. NO order/execution affordance (research evidence only).
# --------------------------------------------------------------------------------------------------
def _regime_family_for(label: Optional[str], cfg: Config) -> Optional[str]:
    """The config-backed regime FAMILY key for a STORED regime label (J-103) — read VERBATIM via the
    `research.severity_velocity.regime_families` catalog (the families partition `regime.labels`, validated
    at boot). None when the label is None or (defensively) not in any family — an honest no-tag, never
    fabricated. Recomputes no regime."""
    if label is None:
        return None
    for family in cfg.research.severity_velocity.regime_families:
        if label in family.regimes:
            return family.key
    return None


def _velocity_sign_for(velocity: Optional[float]) -> Optional[str]:
    """The severity-velocity SIGN cohort key for a served velocity (J-103): rising (`> 0`, worsening), flat
    (`== 0`), or falling (`< 0`, easing). None when the velocity is None (the warm-up head — an honest no-tag,
    honestly EXCLUDED from a cohort, never fabricated). A fixed structural sign test (no threshold literal —
    only the sign of the served value decides; the labels are config-backed)."""
    if velocity is None:
        return None
    if velocity > 0:
        return VELOCITY_SIGN_RISING
    if velocity < 0:
        return VELOCITY_SIGN_FALLING
    return VELOCITY_SIGN_FLAT


def _severity_velocity_observation_set(
    session: Session, horizon: int, cfg: Config, as_of: Optional[date_cls] = None
) -> list[dict]:
    """The SINGLE observation set the Severity-velocity × Regime study AND its samples drill-down BOTH read
    (count-coherence keystone — one membership rule). Pools the stored BENCHMARK (SPY) `ForwardReturn` at
    `horizon` (its `realized_return`, read VERBATIM — the forward MARKET return), ONE per snapshot date,
    joined to its run's STORED `regime_label` (read verbatim) and the SERVED `severity_velocity` at that
    snapshot date (from the read-only `market_phase.severity_velocity_by_date` derivation, <= the resolved
    as-of — never recomputed). Each observation carries its derived (regime family, velocity sign) cohort
    tags; an observation with no derivable velocity (the warm-up head) or no family is honestly EXCLUDED from
    a conditioned cohort (its tag is None). SELECT-only + the read-only derivation; it recomputes NO return,
    NO regime, NO slope.

    `as_of` (J-32) scopes BOTH the pooled SPY returns and the served-velocity timeline to snapshots dated <=
    D (a FILTER only — no recompute, no second date state); `as_of=None` -> all-history. Forward returns are
    the stored realized returns (bars > D by construction of `forward_returns`), so No-lookahead holds."""
    from app.engine.market_phase import severity_velocity_by_date  # lazy import (avoids a config/research cycle)

    spy = cfg.etfs.index[0]  # the benchmark whose forward return is the "market" return (SPY) — from config
    # iter-47 (J-105): already symbol-bounded to SPY (one row per snapshot date); column-project + stream
    # the scan to light value tuples (run_id, symbol, realized_return) for consistency — same verbatim values.
    batch = cfg.research.read_batch_size
    fr_stmt = select(
        ForwardReturn.run_id, ForwardReturn.symbol, ForwardReturn.realized_return
    ).where(ForwardReturn.horizon == horizon, ForwardReturn.symbol == spy)
    if as_of is not None:
        fr_stmt = fr_stmt.join(ScannerRun, ScannerRun.id == ForwardReturn.run_id).where(
            ScannerRun.asof_date <= as_of
        )
    fr_rows = [
        (run_id, symbol, realized_return)
        for run_id, symbol, realized_return in session.exec(fr_stmt).yield_per(batch)
    ]
    if not fr_rows:
        return []
    runs_with_fr = sorted({run_id for run_id, _, _ in fr_rows})
    run_rows = session.exec(select(ScannerRun).where(ScannerRun.id.in_(runs_with_fr))).all()
    run_by_id = {run.id: run for run in run_rows}
    # the SERVED severity-velocity per snapshot date (read from the SAME single causal timeline the panel
    # reads, <= the resolved as-of — never a second computation). Keyed by ISO date.
    velocity_by_date = severity_velocity_by_date(session, as_of, cfg)

    observations: list[dict] = []
    for fr_run_id, fr_symbol, fr_realized_return in sorted(fr_rows, key=lambda r: r[0]):
        run = run_by_id.get(fr_run_id)
        if run is None:
            continue  # defensive: a benchmark return whose run is missing (never on a consistent DB)
        signal_date = run.asof_date.isoformat()
        velocity = velocity_by_date.get(signal_date)
        observations.append({
            "run_id": fr_run_id,
            "ticker": fr_symbol,                       # SPY (the benchmark) — read verbatim
            "return": fr_realized_return,              # the stored forward MARKET return (read verbatim)
            "snapshot_date": signal_date,
            "regime": run.regime_label,                # the STORED regime label (read verbatim)
            "regime_family": _regime_family_for(run.regime_label, cfg),
            "severity_velocity": velocity,             # the SERVED velocity (read verbatim from the derivation)
            "velocity_sign": _velocity_sign_for(velocity),
        })
    return observations


def _severity_velocity_member_key(obs: dict) -> Optional[tuple[str, str]]:
    """The (regime_family, velocity_sign) cohort key ONE observation belongs to (J-103) — the SAME
    membership rule the aggregate AND the samples drill-down apply (so a cell's published N equals its
    drill-down total by construction). None when the observation has no family OR no velocity sign
    (insufficient history at the warm-up head) — honestly EXCLUDED from a conditioned cell, never
    fabricated."""
    if obs["regime_family"] is None or obs["velocity_sign"] is None:
        return None
    return (obs["regime_family"], obs["velocity_sign"])


def _severity_velocity_cell_stats(returns: list[float], min_sample: int) -> dict:
    """Per-cell descriptive stats over the member SPY forward returns (read-only, J-103): `n`, `low_sample`
    (`n < min_sample`), `mean_return`, and `win_rate` (fraction of returns `> 0`). An empty cell yields None
    for `mean_return`/`win_rate` (honest NA, never a fabricated 0). The `> 0` win boundary is a fixed
    structural rule (like `_expectancy`'s), not a tunable."""
    n = len(returns)
    return {
        "n": n,
        "low_sample": n < min_sample,
        "mean_return": mean(returns) if returns else None,
        "win_rate": (sum(1 for r in returns if r > 0) / n) if returns else None,
    }


# The honest verdict caveats carried VERBATIM on every Severity-velocity × Regime study payload (J-103,
# goal.md invariant) — the survivorship / bull-dominated-sample / underpowered-for-crashes limitations and
# the conclusion that, on the committed seed, rising stress-velocity under a red regime preceded a BOUNCE,
# not continuation (the stated hypothesis is NOT supported on this window). A fixed honest disclosure string,
# not a tunable (No magic numbers — it is descriptive copy, the same class as `RESEARCH_CAVEAT`).
SEVERITY_VELOCITY_VERDICT_CAVEAT = (
    "Honest limitations: this study is survivorship-biased to current-membership names, and the loaded "
    "2021–2026 seed is a bull-dominated sample with only shallow drawdowns — so it is underpowered for "
    "sustained crashes until the pre-2021 deep-drawdown history loads. On the committed seed, rising "
    "stress-velocity under a red regime preceded a bounce, not continuation — the hypothesis that rising "
    "stress under a red regime predicts a further decline is NOT supported on this window. NA/partial cells "
    "are shown honestly, never fabricated."
)


def compute_severity_velocity_study(
    session: Session, horizon: int, config: Optional[Config] = None, *,
    as_of: Optional[date_cls] = None,
) -> dict:
    """The SINGLE canonical Severity-velocity × Regime forward-return study (Data Contract value, J-103) for
    the selected `horizon`. Builds a regime-FAMILY × velocity-SIGN matrix of the stored BENCHMARK (SPY)
    forward return — each cell reporting `mean_return`, `win_rate`, and `n` — by GROUPING the stored SPY
    `forward_returns` (read VERBATIM) by the config-backed regime family of the STORED regime label and the
    SIGN of the SERVED `severity_velocity` (J-102) at each snapshot date. It recomputes NO canonical return,
    NO regime, NO slope (Single source of truth; No recompute in the read path) — a pure grouping of two
    already-served values, the SAME read-only class as the J-29 event study. NOT a fitted/ML model. NO
    order/execution affordance.

    The matrix emits one row per configured regime family and one cell per velocity sign (even at n=0 — an
    honest NA cell, never omitted, never fabricated). A cell below `walk_forward.min_sample` carries its
    honest `n` + a `low_sample` flag (the UI shows NA + n). The payload carries the config-driven family +
    sign vocabularies (so the frontend matrix headers + the samples chips are built from config), the
    survivorship/descriptive labels, and the honest verdict caveat VERBATIM. `as_of` (J-32) scopes the pool
    + the served velocity to snapshots dated <= D (a FILTER only); the payload echoes the resolved cutoff as
    `asof_date` (ISO) when scoped, else null. Forward returns use only bars dated > D by construction of
    `forward_returns` (No lookahead)."""
    cfg = config or get_config()
    wf = cfg.walk_forward
    sv = cfg.research.severity_velocity
    min_sample = wf.min_sample

    observations = _severity_velocity_observation_set(session, horizon, cfg, as_of)

    # group the observations into (family, sign) cells — the SAME membership the samples drill-down
    # reproduces (one rule). An observation with no derivable family/sign (the warm-up head where the
    # severity-velocity is NA, or an unknown regime label) is honestly EXCLUDED from every cell — never
    # fabricated. `n_total` counts only the ASSIGNABLE observations (those that landed in a cell), so it
    # equals the sum of the cell Ns (the matrix's honest displayed total — the warm-up head is not a cell).
    grouped: dict[tuple[str, str], list[float]] = defaultdict(list)
    assignable = 0
    for obs in observations:
        key = _severity_velocity_member_key(obs)
        if key is None:
            continue
        grouped[key].append(obs["return"])
        assignable += 1

    families = [{"key": f.key, "label": f.label} for f in sv.regime_families]
    signs = [{"key": s.key, "label": s.label} for s in sv.velocity_signs]

    # one row per family, one cell per sign — every cell emitted (honest NA at n=0, never omitted).
    matrix = [
        {
            "family": family.key,
            "family_label": family.label,
            "cells": [
                {
                    "velocity_sign": sign.key,
                    "velocity_sign_label": sign.label,
                    "stats": _severity_velocity_cell_stats(
                        grouped.get((family.key, sign.key), []), min_sample
                    ),
                }
                for sign in sv.velocity_signs
            ],
        }
        for family in sv.regime_families
    ]

    return {
        "horizon": horizon,
        "asof_date": as_of.isoformat() if as_of is not None else None,
        "horizons": list(wf.horizons),
        "default_horizon": wf.default_horizon,
        "min_sample": min_sample,
        "benchmark": cfg.etfs.index[0],  # the SPY benchmark whose forward return is the "market" return
        "regime_families": families,
        "velocity_signs": signs,
        "survivorship_bias": SURVIVORSHIP_BIAS_LABEL,
        "descriptive_caveat": RESEARCH_CAVEAT,
        # the honest verdict caveat VERBATIM (the hypothesis is NOT supported on this bull-dominated seed).
        "verdict_caveat": SEVERITY_VELOCITY_VERDICT_CAVEAT,
        # the ASSIGNABLE observation count (== Σ cell N) — the warm-up-head / unknown-family observations are
        # honestly excluded (a cell's published N never includes them).
        "n_total": assignable,
        "matrix": matrix,
    }


# The sentinel `subject` slot the Severity-velocity × Regime study reuses in the SHARED `EventStudyCache`
# table (mirroring `_RECOVERY_TURN_EDGE_SUBJECT` / `_DOWNTREND_OPPORTUNITY_SUBJECT`) so its cache rows never
# collide with a real event-study subject or the other sentinels. Reusing the same cache table keeps the
# cache machinery single-sourced (no second cache mechanism, no new table — iter-20 lesson).
_SEVERITY_VELOCITY_SUBJECT = "__severity_velocity__"


def severity_velocity_cached(
    session: Session, horizon: int, config: Optional[Config] = None, *,
    as_of: Optional[date_cls] = None,
) -> dict:
    """Serve the Severity-velocity × Regime study from the J-72 cache (mirrors `recovery_turn_edge_cached`),
    reusing the SHARED `EventStudyCache` table under the `_SEVERITY_VELOCITY_SUBJECT` sentinel. The study has
    no overlap-honesty view, so the `view` slot is the fixed sentinel too. On a HIT for the current
    `(sentinel, view=sentinel, asof_key, dataset_version, horizon)` key, return the stored payload (NO
    recompute); on a MISS, compute it ONCE via `compute_severity_velocity_study`, persist under the current
    stamp, prune stale rows for this identity, and return it. BYTE-IDENTICAL to a fresh compute (a pure
    performance layer); the cache REFRESHES after any dataset change via the dataset-version key."""
    cfg = config or get_config()
    version = _dataset_version(session)
    asof_key = _cache_asof_key(as_of)
    view = _SEVERITY_VELOCITY_SUBJECT  # no overlap-honesty view for this study — a fixed sentinel slot

    hit = session.exec(
        select(EventStudyCache).where(
            EventStudyCache.subject == _SEVERITY_VELOCITY_SUBJECT,
            EventStudyCache.view == view,
            EventStudyCache.asof_key == asof_key,
            EventStudyCache.dataset_version == version,
            EventStudyCache.horizon == horizon,
        )
    ).first()
    if hit is not None:
        return json.loads(hit.payload_json)

    payload = compute_severity_velocity_study(session, horizon, cfg, as_of=as_of)

    stale = session.exec(
        select(EventStudyCache).where(
            EventStudyCache.subject == _SEVERITY_VELOCITY_SUBJECT,
            EventStudyCache.view == view,
            EventStudyCache.asof_key == asof_key,
            EventStudyCache.horizon == horizon,
            EventStudyCache.dataset_version != version,
        )
    ).all()
    for row in stale:
        session.delete(row)

    session.add(EventStudyCache(
        subject=_SEVERITY_VELOCITY_SUBJECT, view=view, asof_key=asof_key, dataset_version=version,
        horizon=horizon, payload_json=json.dumps(payload),
        created_at=datetime.now(timezone.utc),
    ))
    try:
        session.commit()
    except Exception:  # best-effort cache; a concurrent writer raced us — the payload is byte-identical
        session.rollback()
    return payload


# --------------------------------------------------------------------------------------------------
# J-104(a) — cache the two remaining uncached studies via the EXISTING `EventStudyCache` + `_dataset_version`
# idiom (the SAME pattern `event_study_cached` / `recovery_turn_edge_cached` / `downtrend_opportunity_cached`
# use), so a repeat request is a cache HIT (byte-identical figures), not a full recompute. No new table.
# --------------------------------------------------------------------------------------------------
# The sentinel `subject` slot the Regime × Setup × Pattern study reuses in the SHARED `EventStudyCache` table
# (mirroring the other sentinels) so its rows never collide. The study has no `subject`, so a fixed sentinel.
_REGIME_SETUP_PATTERN_SUBJECT = "__regime_setup_pattern__"
# The sentinel `subject` PREFIX for the factor-combination cache. Because a combination is identified by its
# ordered list of conditions (not a single subject), the deterministic condition serialization is folded
# INTO the `subject` slot (after this prefix) — the SAME discipline of folding the full analysis identity
# into the cache key the iter-38/39 cache-schema lessons require (so two distinct combinations never share a
# row). The `view` slot stays a fixed sentinel (the study has no overlap-honesty view).
_FACTOR_COMBINATION_SUBJECT_PREFIX = "__factor_combination__"


def _factor_combination_cache_subject(conditions: list[dict]) -> str:
    """The deterministic `subject` cache-key slot for ONE factor-combination request (J-104a): the sentinel
    prefix + the ORDERED conditions serialized as `factor:side:quantile` triples joined by `|`. Two distinct
    combinations (different factors/sides/quantiles/order) therefore key to DIFFERENT rows, while the SAME
    combination always keys to the SAME row (an idempotent cache hit). The conditions are the request's
    resolved identity — folding the full analysis identity into the key is the iter-38/39 cache discipline."""
    serialized = "|".join(
        f"{c.get('factor')}:{c.get('side')}:{c.get('quantile')}" for c in conditions
    )
    return f"{_FACTOR_COMBINATION_SUBJECT_PREFIX}{serialized}"


def factor_combination_cached(
    session: Session, conditions: list[dict], horizon: int, config: Optional[Config] = None, *,
    as_of: Optional[date_cls] = None,
) -> dict:
    """Serve the multi-factor combination cohort analysis (J-26) from the J-72 cache (J-104a — mirrors
    `event_study_cached`), reusing the SHARED `EventStudyCache` table with the ordered conditions folded into
    the `subject` slot (`_factor_combination_cache_subject`) so distinct combinations never collide. On a HIT
    for the current `(subject, view=sentinel, asof_key, dataset_version, horizon)` key, return the stored
    payload (NO recompute); on a MISS, compute it ONCE via `compute_factor_combination` (which validates the
    conditions, raising before any write), persist under the current stamp, prune stale rows for this
    identity, and return it. BYTE-IDENTICAL to a fresh compute; the cache REFRESHES after any dataset change
    via the dataset-version key."""
    cfg = config or get_config()
    version = _dataset_version(session)
    asof_key = _cache_asof_key(as_of)
    subject = _factor_combination_cache_subject(conditions)
    view = _FACTOR_COMBINATION_SUBJECT_PREFIX  # no overlap-honesty view for this study — a fixed sentinel slot

    hit = session.exec(
        select(EventStudyCache).where(
            EventStudyCache.subject == subject,
            EventStudyCache.view == view,
            EventStudyCache.asof_key == asof_key,
            EventStudyCache.dataset_version == version,
            EventStudyCache.horizon == horizon,
        )
    ).first()
    if hit is not None:
        return json.loads(hit.payload_json)

    payload = compute_factor_combination(session, conditions, horizon, cfg, as_of=as_of)

    stale = session.exec(
        select(EventStudyCache).where(
            EventStudyCache.subject == subject,
            EventStudyCache.view == view,
            EventStudyCache.asof_key == asof_key,
            EventStudyCache.horizon == horizon,
            EventStudyCache.dataset_version != version,
        )
    ).all()
    for row in stale:
        session.delete(row)

    session.add(EventStudyCache(
        subject=subject, view=view, asof_key=asof_key, dataset_version=version,
        horizon=horizon, payload_json=json.dumps(payload),
        created_at=datetime.now(timezone.utc),
    ))
    try:
        session.commit()
    except Exception:  # best-effort cache; a concurrent writer raced us — the payload is byte-identical
        session.rollback()
    return payload


# The all-factors Factor-Lab view (J-107 → J-109) is served through the SHARED `EventStudyCache` under a
# fixed sentinel subject/view namespace — it is ONE global all-horizons view per as-of (NOT per horizon —
# J-109 shows every horizon at once), so a fixed sentinel pair (never colliding with a real event-study
# subject or the other sentinels) is the whole key identity. NO new `table=True` model (the `test_db.py`
# expected-tables guard stays unchanged).
_ALL_FACTORS_SUBJECT = "__all_factors__"
_ALL_FACTORS_VIEW = "factors_table"
# iter-52 (J-109): the served all-factors shape CHANGED (all-horizons + paired max-drawdown columns). Fold
# a schema token into the dataset_version slot so EVERY pre-iter-52 cached row (the old single-horizon
# `factors_table` shape, keyed by the bare `_dataset_version`) is a guaranteed cache MISS AND is pruned on
# the next write (same subject/view/asof_key/horizon, different dataset_version) — never served field-less
# (iter-38/39/44 stale-cache discipline). Bump this token on any future change to the served all-factors
# shape. The view is horizon-independent now, so the cache `horizon` slot is pinned to `default_horizon`.
_ALL_FACTORS_SCHEMA_TOKEN = "allh-mdd-v1"

# ops-hardening iter-31 (audit finding B5, AG-8) — single-flight de-dup guarding `factor_lab_all_cached`'s
# cache-MISS path, mirroring `data_manager.compute_coverage`'s established per-key-lock + in-flight-event
# idiom (never a new concurrency abstraction) with `forward_testing.forward_aggregates_ingest_cached`'s
# bounded-wait failure-path convention (iter-15, UT-04). Root cause: the audit observed a concurrent
# duplicate `compute_factor_lab_all` invocation for the SAME `(asof_key, dataset_version+token, horizon)`
# identity complete while another was already in flight and about to write the same row — no lock, unlike
# every sibling all-horizons cache (`forward_aggregates_ingest_cached`, `compute_coverage`) — wasting exactly
# the memory headroom the return-value bound above exists to create. The FIRST caller for a key computes
# below; every OTHER concurrent caller for that SAME key waits (bounded), then re-reads the now-persisted
# row with its OWN session — never a second producer. A waiter whose bounded wait elapses (the owner raised,
# or a genuine wedge) falls through and computes independently rather than hanging — never a deadlock, never
# a raise of its own.
_FACTOR_LAB_ALL_LOCK = threading.Lock()
# per-key in-flight events: (asof_key, dataset_version+token, horizon) -> Event, set when the owner finishes
# (success or failure) so any waiter wakes. Always removed by the owner in a `finally`.
_FACTOR_LAB_ALL_INFLIGHT: dict[tuple, threading.Event] = {}
# Bounded wait for a NON-owner caller. It must be sized against THIS call's OWN compute duration — the
# first cut of this guard copied `forward_testing._FORWARD_AGG_WAIT_TIMEOUT_S` (45s, tuned for that
# module's much faster aggregate compute) and was rejected in review for exactly that reason: one full
# cold-MISS `compute_factor_lab_all` on the live deep basis, under the mandatory host-guard CPU caps
# (AG-10 — a permanent physical constraint of this host, never removable), was measured at ~2-4 min and
# ~4-5 min across two independent backend restarts (2026-07-29, iter-31 dev handoff) => worst observed
# ~300s. A 45s ceiling would therefore ALWAYS elapse mid-compute, sending every waiter off to start its
# own duplicate compute — precisely the audit-B5 waste this guard exists to close. The owner ALWAYS sets
# the event in its `finally` (success OR raise), so this ceiling is only ever reached by a genuinely
# wedged owner: sizing it generously costs a healthy request nothing, while sizing it below the real
# compute duration silently disables the de-dup. Integer seconds (`Event.wait` accepts an int) so the
# derivation stays literal-free under the no-magic-numbers engine rule.
_FACTOR_LAB_ALL_MEASURED_COLD_MISS_S = 300  # worst observed live cold-MISS compute (2026-07-29 measurement)
_FACTOR_LAB_ALL_WAIT_SAFETY_FACTOR = 3      # headroom for a slower/more loaded host than the measured one
_FACTOR_LAB_ALL_WAIT_TIMEOUT_S = _FACTOR_LAB_ALL_MEASURED_COLD_MISS_S * _FACTOR_LAB_ALL_WAIT_SAFETY_FACTOR


def factor_lab_all_cached(
    session: Session, config: Optional[Config] = None, *, as_of: Optional[date_cls] = None,
) -> dict:
    """Serve the all-factors, all-horizons Factor-Lab view (J-109) from the J-72 cache (mirrors
    `factor_combination_cached`), reusing the SHARED `EventStudyCache` table under the
    `_ALL_FACTORS_SUBJECT`/`_ALL_FACTORS_VIEW` sentinel namespace (no new table). The view is horizon-
    independent (it shows every config horizon at once), so the cache `horizon` slot is pinned to
    `default_horizon` and the dataset-version slot folds in `_ALL_FACTORS_SCHEMA_TOKEN` (so a pre-iter-52
    old-shape row is a guaranteed MISS and is pruned on write). On a HIT for the current `(sentinel, view,
    asof_key, dataset_version+token, default_horizon)` key, return the stored payload (NO recompute); on a
    MISS, compute it ONCE via `compute_factor_lab_all`, persist under the current stamp, prune any stale rows
    for this identity, and return it. BYTE-IDENTICAL to a fresh compute; the cache REFRESHES after any
    dataset change via the dataset-version key. `as_of` is folded into the `asof_key` slot (a pure
    observation-set FILTER).

    iter-31 (audit B5, AG-8): a MISS now goes through the module-level single-flight guard above, keyed on
    the SAME `(asof_key, version, horizon)` tuple used for the cache row itself — concurrent same-key MISSes
    share ONE `compute_factor_lab_all` invocation instead of racing duplicate computes onto the same row."""
    cfg = config or get_config()
    version = f"{_dataset_version(session)}-{_ALL_FACTORS_SCHEMA_TOKEN}"
    asof_key = _cache_asof_key(as_of)
    horizon = cfg.walk_forward.default_horizon  # the horizon-independent view pins the cache horizon slot

    def _cached_row() -> Optional[dict]:
        row = session.exec(
            select(EventStudyCache).where(
                EventStudyCache.subject == _ALL_FACTORS_SUBJECT,
                EventStudyCache.view == _ALL_FACTORS_VIEW,
                EventStudyCache.asof_key == asof_key,
                EventStudyCache.dataset_version == version,
                EventStudyCache.horizon == horizon,
            )
        ).first()
        return json.loads(row.payload_json) if row is not None else None

    hit = _cached_row()
    if hit is not None:
        return hit

    # single-flight: only the FIRST caller for this key computes; concurrent same-key callers wait.
    key = (asof_key, version, horizon)
    with _FACTOR_LAB_ALL_LOCK:
        event = _FACTOR_LAB_ALL_INFLIGHT.get(key)
        is_owner = event is None
        if is_owner:
            event = threading.Event()
            _FACTOR_LAB_ALL_INFLIGHT[key] = event

    if not is_owner:
        event.wait(timeout=_FACTOR_LAB_ALL_WAIT_TIMEOUT_S)
        hit = _cached_row()
        if hit is not None:
            return hit
        # the owner failed (its `finally` already released the slot) or a genuine wedge exceeded the
        # bounded wait without persisting — fall through and compute independently rather than blocking
        # indefinitely. Still byte-identical (the SAME sole producer); at worst a rare redundant compute.
        # The wait ceiling is sized well above the measured real compute (above), so reaching it is an
        # abnormal event: log it, so a duplicate compute can never happen SILENTLY (audit B5 was found by
        # observing one, and this is the only path that can still start one).
        logger.warning(
            "factor_lab_all single-flight wait elapsed or owner failed for key=%s after %ss — computing "
            "independently (duplicate compute possible)", key, _FACTOR_LAB_ALL_WAIT_TIMEOUT_S,
        )

    # MISS (owner path, or the rare fallback above) — compute once and persist.
    try:
        payload = compute_factor_lab_all(session, cfg, as_of=as_of)

        stale = session.exec(
            select(EventStudyCache).where(
                EventStudyCache.subject == _ALL_FACTORS_SUBJECT,
                EventStudyCache.view == _ALL_FACTORS_VIEW,
                EventStudyCache.asof_key == asof_key,
                EventStudyCache.horizon == horizon,
                EventStudyCache.dataset_version != version,
            )
        ).all()
        for row in stale:
            session.delete(row)

        session.add(EventStudyCache(
            subject=_ALL_FACTORS_SUBJECT, view=_ALL_FACTORS_VIEW, asof_key=asof_key, dataset_version=version,
            horizon=horizon, payload_json=json.dumps(payload),
            created_at=datetime.now(timezone.utc),
        ))
        try:
            session.commit()
        except Exception:  # best-effort cache; a concurrent writer raced us — the payload is byte-identical
            session.rollback()
        return payload
    finally:
        # release the in-flight slot + wake any waiter whether we succeeded or raised — a waiter then either
        # finds the persisted payload or falls through and computes independently — never a hang.
        if is_owner:
            with _FACTOR_LAB_ALL_LOCK:
                _FACTOR_LAB_ALL_INFLIGHT.pop(key, None)
            event.set()


def regime_setup_pattern_cached(
    session: Session, horizon: int, config: Optional[Config] = None, *,
    as_of: Optional[date_cls] = None, view: str = VIEW_EPISODES,
) -> dict:
    """Serve the Regime × Setup × Pattern ranked combinations study (J-77) from the J-72 cache (J-104a —
    mirrors `recovery_turn_edge_cached`), reusing the SHARED `EventStudyCache` table under the
    `_REGIME_SETUP_PATTERN_SUBJECT` sentinel so its rows never collide with a real event-study subject or the
    other sentinels. On a HIT for the current `(sentinel, view, asof_key, dataset_version, horizon)` key,
    return the stored payload (NO recompute); on a MISS, compute it ONCE via
    `compute_regime_setup_pattern_study` (which validates the view, raising before any write), persist under
    the current stamp, prune stale rows for this identity, and return it. BYTE-IDENTICAL to a fresh compute;
    the cache REFRESHES after any dataset change via the dataset-version key."""
    cfg = config or get_config()
    version = _dataset_version(session)
    asof_key = _cache_asof_key(as_of)

    hit = session.exec(
        select(EventStudyCache).where(
            EventStudyCache.subject == _REGIME_SETUP_PATTERN_SUBJECT,
            EventStudyCache.view == view,
            EventStudyCache.asof_key == asof_key,
            EventStudyCache.dataset_version == version,
            EventStudyCache.horizon == horizon,
        )
    ).first()
    if hit is not None:
        return json.loads(hit.payload_json)

    payload = compute_regime_setup_pattern_study(session, horizon, cfg, as_of=as_of, view=view)

    stale = session.exec(
        select(EventStudyCache).where(
            EventStudyCache.subject == _REGIME_SETUP_PATTERN_SUBJECT,
            EventStudyCache.view == view,
            EventStudyCache.asof_key == asof_key,
            EventStudyCache.horizon == horizon,
            EventStudyCache.dataset_version != version,
        )
    ).all()
    for row in stale:
        session.delete(row)

    session.add(EventStudyCache(
        subject=_REGIME_SETUP_PATTERN_SUBJECT, view=view, asof_key=asof_key, dataset_version=version,
        horizon=horizon, payload_json=json.dumps(payload),
        created_at=datetime.now(timezone.utc),
    ))
    try:
        session.commit()
    except Exception:  # best-effort cache; a concurrent writer raced us — the payload is byte-identical
        session.rollback()
    return payload


# --------------------------------------------------------------------------------------------------
# Regime Lab (J-110) — cross-sectional forward returns + paired max-drawdown by market-regime LABEL and by
# regime-SCORE decile. A read-only re-surfacing of ALREADY-STORED canonical values: it pools the SAME
# cross-sectional per-observation forward returns the Factor Lab / event study build (stock × snapshot),
# tags each observation with its run's STORED `regime_score` + `regime_label` (J-80, read VERBATIM from the
# immutable `ScannerRun` — the regime is NEVER recomputed), and groups them two ways — (a) by the six
# canonical regime labels, (b) into deciles D1…D`deciles` of the 0–100 regime score — at EVERY config
# horizon as paired (mean forward-return, mean max-drawdown) columns, with the rank-IC of the regime score
# vs the forward return per horizon. It recomputes NO regime / return / drawdown and introduces NO new
# canonical value — every figure is a grouping of stored values. NOT a fitted/learned/ML model. It is
# DISTINCT from J-77 (regime × setup × pattern) and J-103 (severity-velocity sign vs SPY): it studies the
# regime score/label ALONE against cross-sectional stock returns, on its OWN home (no duplicate home).
# --------------------------------------------------------------------------------------------------
def _regime_meta_by_run(
    session: Session, needed_runs: set[int], batch: int
) -> dict[int, tuple[Optional[float], Optional[str]]]:
    """`run_id -> (stored regime_score, stored regime_label)` over the FR-bearing runs, column-projected +
    `yield_per`-streamed. Read VERBATIM from the immutable `ScannerRun` (J-80); recomputes no regime. Mirrors
    `_regime_by_run_projected`, additionally carrying the 0–100 `regime_score` the decile split groups on (so
    ONE projected read serves both the by-label and the by-score-decile groupings)."""
    if not needed_runs:
        return {}
    meta: dict[int, tuple[Optional[float], Optional[str]]] = {}
    stmt = select(ScannerRun.id, ScannerRun.regime_score, ScannerRun.regime_label).where(
        ScannerRun.id.in_(needed_runs)
    )
    for run_id, regime_score, regime_label in session.exec(stmt).yield_per(batch):
        meta[run_id] = (regime_score, regime_label)
    return meta


def _regime_lab_members_by_horizon(
    session: Session, horizons: list[int], as_of: Optional[date_cls] = None,
    *, cfg: Optional[Config] = None,
) -> dict[int, list[dict]]:
    """The read-only SHARED per-observation pools for the Regime Lab across EVERY horizon in `horizons`
    (J-110), built from a SINGLE batched read (mirrors `_all_factor_observations_by_horizon` /
    `_event_study_members_by_horizon`): ONE `ForwardReturn` SELECT covering all horizons (`horizon IN
    horizons`, column-projected to run_id/symbol/realized_return/max_drawdown), ONE `ScannerResult` stream,
    and ONE projected per-run regime read. Returns `{horizon: [observations]}` where each observation is
    `{run_id, ticker, return, max_drawdown, regime_score, regime_label}` — the realized forward return +
    the J-86 max_drawdown (read VERBATIM) tagged with the run's STORED `regime_score`/`regime_label` (J-80,
    read VERBATIM). It recomputes NO regime / return / drawdown.

    BYTE-IDENTITY keystone: `{horizon: pools}[h]` is byte-identical (row-for-row, same `(run_id, id)` order)
    to calling this builder with `horizons=[h]` — the property `compute_regime_lab` (all-horizons) and the
    `_regime_lab_observation_set` samples drill-down (single-horizon) both rely on for count-coherence. An
    observation is kept for horizon h ONLY when a realized return exists at h (the SAME n=0 exclusion as the
    Factor Lab); a ScannerResult whose run has FRs at some OTHER horizon but not at h simply contributes
    nothing to `pools[h]` (the per-horizon `fr is None` gate), exactly as the single-horizon build would.

    `as_of` (J-32) scopes ALL horizons' pools to snapshots with `ScannerRun.asof_date <= as_of` (the SAME
    single membership filter); `as_of=None` adds NO clause -> byte-identical all-history.

    iter-46/47/48 OOM lesson / J-105: the read is BOUNDED — the FR scan is column-projected +
    `yield_per`-streamed (lightweight value tuples, NEVER full ORM rows over `forward_returns`), the
    ScannerResult side is column-projected (run_id/id/ticker — the regime is per-RUN, so the heavy
    `record_json` is NOT read here, unlike the Factor Lab) and `yield_per`-streamed in `(run_id, id)` order
    (rides `ix_scanner_results_run_id`, so no `USE TEMP B-TREE FOR ORDER BY` spills a temp file to a nearly-
    full disk; a bare `ORDER BY id` returned `disk is full` on this host). ONE heavy read serves ALL horizons
    (not H reads) — and there is NO unbounded `.all()` over `ForwardReturn` or `ScannerResult`."""
    batch = (cfg or get_config()).research.read_batch_size
    fr_stmt = select(
        ForwardReturn.horizon, ForwardReturn.run_id, ForwardReturn.symbol,
        ForwardReturn.realized_return, ForwardReturn.max_drawdown,
    ).where(ForwardReturn.horizon.in_(horizons))
    if as_of is not None:
        fr_stmt = fr_stmt.join(ScannerRun, ScannerRun.id == ForwardReturn.run_id).where(
            ScannerRun.asof_date <= as_of
        )
    fr_by_h: dict[int, dict[tuple[int, str], tuple[float, Optional[float]]]] = {h: {} for h in horizons}
    runs_with_fr_set: set[int] = set()
    for h, run_id, symbol, realized_return, max_drawdown in session.exec(fr_stmt).yield_per(batch):
        fr_by_h[h][(run_id, symbol)] = (realized_return, max_drawdown)
        runs_with_fr_set.add(run_id)
    runs_with_fr = sorted(runs_with_fr_set)
    # the per-run regime score + label, read VERBATIM over the FR-bearing runs (projected + streamed).
    regime_by_run = _regime_meta_by_run(session, runs_with_fr_set, batch)
    # the ScannerResult side: only (run_id, id, ticker) is needed to join the FR (the regime is per-RUN, not
    # per-result) — a lighter column projection than the Factor Lab's full-row stream. Ordered (run_id, id).
    res_stmt = (
        select(ScannerResult.run_id, ScannerResult.id, ScannerResult.ticker)
        .where(ScannerResult.run_id.in_(runs_with_fr))
        .order_by(ScannerResult.run_id, ScannerResult.id)
    )
    results = session.exec(res_stmt).yield_per(batch) if runs_with_fr else []

    pools: dict[int, list[dict]] = {h: [] for h in horizons}
    for run_id, _res_id, ticker in results:
        regime_meta: Optional[tuple] = None  # resolved lazily on the first horizon that has an FR
        for h in horizons:
            fr = fr_by_h[h].get((run_id, ticker))
            if fr is None:
                continue  # no realized return at this horizon (n=0) — same exclusion as the Factor Lab
            if regime_meta is None:
                regime_meta = regime_by_run.get(run_id, (None, None))
            realized, max_drawdown = fr
            regime_score, regime_label = regime_meta
            pools[h].append({
                "run_id": run_id, "ticker": ticker, "return": realized, "max_drawdown": max_drawdown,
                # the run's STORED regime score (0–100) + label, read VERBATIM (J-80) — never recomputed.
                "regime_score": regime_score, "regime_label": regime_label,
            })
    return pools


def _regime_score_ordered(members: list[dict]) -> list[dict]:
    """The Regime-Lab observation members reshaped to the `_deciles` 'factor' contract — `factor` = the
    stored 0–100 `regime_score` — and ordered ascending by regime score with the deterministic
    `(score, ticker, run_id)` tie-break. This is the SINGLE ordering BOTH the by-decile aggregate AND the
    samples decile drill-down read, so a decile's drill-down `total` EQUALS its published `n` by construction
    (count-coherence keystone — one quantile-edge definition, never a second). An observation with a NULL
    regime score is EXCLUDED (never bucketed) — honest, not fabricated (the stored column is non-null in
    practice, so this drops nothing; it is a defensive parity with the Factor Lab's factor-NULL exclusion)."""
    scored = [
        {
            "factor": m["regime_score"], "ticker": m["ticker"], "run_id": m["run_id"],
            "return": m["return"], "max_drawdown": m["max_drawdown"],
            # carry the run's stored label too (ignored by `_deciles`, but surfaced on a decile drill-down row
            # so each row shows which regime the score came from). Read verbatim — never recomputed.
            "regime_label": m["regime_label"], "regime_score": m["regime_score"],
        }
        for m in members
        if m["regime_score"] is not None
    ]
    return sorted(scored, key=lambda o: (o["factor"], o["ticker"], o["run_id"]))


def _regime_lab_observation_set(
    session: Session, horizon: int, view: str, as_of: Optional[date_cls] = None,
    *, cfg: Optional[Config] = None,
) -> list[dict]:
    """The Regime-Lab observation set for ONE (horizon, view) — the SINGLE membership builder the samples
    drill-down reads, so a cohort's drill-down `total` EQUALS its published `n` by construction (J-51
    count-coherence keystone). `view="pooled"` returns the per-signal-day pool UNCHANGED; `view="episodes"`
    returns its first-trigger episode collapse (`_collapse_to_episodes`, the SAME overlap-honesty collapse
    the event study uses, J-63). Built via the SAME `_regime_lab_members_by_horizon` builder `compute_regime_
    lab` reads (single-horizon call — byte-identical to that horizon's slice of the all-horizons build), so
    the samples set is byte-identical to the published one. Recomputes nothing. `as_of` scopes both the
    members and the run-ordinal index to the same point-in-time window."""
    members = _regime_lab_members_by_horizon(session, [horizon], as_of, cfg=cfg)[horizon]
    if view == VIEW_POOLED:
        return members  # the unchanged per-signal-day pool — byte-identical to the published pooled set
    run_position = _run_position_index(session, as_of)
    return _collapse_to_episodes(members, run_position)  # first-trigger episode collapse (J-63)


def compute_regime_lab(
    session: Session, config: Optional[Config] = None, *,
    view: str = VIEW_EPISODES, as_of: Optional[date_cls] = None,
) -> dict:
    """The SINGLE canonical Regime-Lab analysis (Data Contract value, J-110) under the chosen overlap-honesty
    `view`. READS the stored cross-sectional forward returns (`realized_return` + the J-86 `max_drawdown`,
    VERBATIM) tagged with each run's STORED `regime_score`/`regime_label` (J-80, VERBATIM) — it recomputes NO
    regime, NO return, NO drawdown. Groups them two ways at EVERY `config.walk_forward.horizons` horizon:

      - `by_label`  — one entry per CONFIGURED regime label (`config.regime.labels` order — no hard-coded
        regime list), each carrying per horizon: mean realized forward return, paired mean max-drawdown, `n`,
        `low_sample` (`n < walk_forward.min_sample`).
      - `by_decile` — D1…D`research.factor_lab.deciles` of the 0–100 regime score (the EXISTING generic
        `_deciles` / `_decile_member_slice` machinery, the SAME quantile-edge definition the samples
        drill-down reads), each carrying per horizon: mean return, paired mean max-drawdown, `n`,
        `low_sample`, and the decile's regime-score range (`score_min`/`score_max`).
      - `rank_ic_by_horizon` — the Spearman rank-IC of the regime score vs the realized forward return, per
        horizon (the decile table's header figure; `{value, n}`, NA when n < 2 or zero rank variance).

    Every figure is byte-identical to the reference aggregation over `_regime_lab_observation_set(horizon,
    view)` (the SAME builders the samples drill-down reads — one computation path, no number recomputed). The
    view shows ALL horizons at once (paired columns), so it takes NO `horizon` argument. `as_of` (J-32) scopes
    the observation set to snapshots dated <= D (a pure FILTER — recomputes nothing); `as_of=None` is the
    all-history aggregate. The payload echoes the resolved cutoff as `asof_date` (ISO) when scoped, else
    `null`. Raises `ValueError` for an unknown view (the API pre-validates -> 422)."""
    cfg = config or get_config()
    wf = cfg.walk_forward
    fl = cfg.research.factor_lab
    horizons = list(wf.horizons)

    if view not in ALL_VIEWS:
        raise ValueError(f"unknown view {view!r}; valid views are {list(ALL_VIEWS)}")

    labels = list(cfg.regime.labels)

    # ONE heavy read builds the per-observation pools for ALL horizons (the bounded, byte-identity-preserving
    # keystone); the episode collapse (when the view is episodes) is a pure in-memory grouping of those SAME
    # stored rows, computed ONCE per horizon and shared by both the by-label and by-decile groupings.
    pools = _regime_lab_members_by_horizon(session, horizons, as_of, cfg=cfg)
    run_position = _run_position_index(session, as_of) if view == VIEW_EPISODES else None
    members_by_h: dict[int, list[dict]] = {}
    for h in horizons:
        members = pools[h]
        members_by_h[h] = members if view == VIEW_POOLED else _collapse_to_episodes(members, run_position)

    # (a) by-label: every configured regime label emits a row even at n=0 (honest empty row — never omitted,
    # never fabricated). The paired mean max-drawdown uses the SAME NA convention as the Factor Lab / forward
    # scorecard (mean over only the members with a stored drawdown; None when none).
    by_label: list[dict] = []
    for label in labels:
        by_horizon: list[dict] = []
        for h in horizons:
            label_members = [m for m in members_by_h[h] if m["regime_label"] == label]
            returns = [m["return"] for m in label_members]
            mdds = [m["max_drawdown"] for m in label_members if m["max_drawdown"] is not None]
            n = len(label_members)
            by_horizon.append({
                "horizon": h,
                "n": n,
                "low_sample": n < wf.min_sample,
                "mean_return": mean(returns) if returns else None,
                "mean_max_drawdown": _mean_or_none(mdds),
            })
        by_label.append({"regime": label, "by_horizon": by_horizon})

    # (b) by-decile of the 0–100 regime score (the generic `_deciles` machinery) + the per-horizon rank-IC of
    # the regime score vs the realized forward return.
    decile_rows_by_h: dict[int, list[dict]] = {}
    rank_ic_by_horizon: list[dict] = []
    for h in horizons:
        ordered = _regime_score_ordered(members_by_h[h])
        decile_rows_by_h[h] = _deciles(ordered, fl.deciles, wf.min_sample)
        rank_ic_by_horizon.append({
            "horizon": h,
            "rank_ic": _rank_ic([(o["factor"], o["return"]) for o in ordered]),
        })
    by_decile: list[dict] = []
    for d in range(1, fl.deciles + 1):
        by_horizon = []
        for h in horizons:
            drow = decile_rows_by_h[h][d - 1]
            by_horizon.append({
                "horizon": h,
                "n": drow["n"],
                "low_sample": drow["low_sample"],
                "mean_return": drow["mean_return"],
                "mean_max_drawdown": drow["mean_max_drawdown"],
                # the decile's regime-score range (the `_deciles` factor bounds, re-labelled to "score").
                "score_min": drow["factor_min"],
                "score_max": drow["factor_max"],
            })
        by_decile.append({"decile": d, "by_horizon": by_horizon})

    return {
        "view": view,  # J-63: the resolved overlap-honesty view (episodes default | pooled)
        # the resolved as-of scoping cutoff echoed (J-32) — ISO date when scoped, null in all-history mode.
        "asof_date": as_of.isoformat() if as_of is not None else None,
        "horizons": horizons,
        "default_horizon": wf.default_horizon,  # the horizon the rank-IC column header is labelled with
        "deciles_count": fl.deciles,
        "min_sample": wf.min_sample,
        "regime_labels": labels,  # the by-label row vocabulary (config-driven — not hard-coded in the UI)
        "survivorship_bias": SURVIVORSHIP_BIAS_LABEL,
        "descriptive_caveat": RESEARCH_CAVEAT,
        "by_label": by_label,
        "by_decile": by_decile,
        "rank_ic_by_horizon": rank_ic_by_horizon,
    }


# The all-horizons Regime-Lab view is served through the SHARED `EventStudyCache` under a fixed sentinel
# subject (never colliding with a real event-study subject or the other sentinels). It is ONE global
# all-horizons view per (view, as-of), so the cache `horizon` slot is pinned to `default_horizon`. The
# served shape is NEW (by-label + by-score-decile paired columns), so a schema token is folded into the
# dataset-version slot — any old-schema cached row keyed by the bare `_dataset_version` is a guaranteed MISS
# AND is pruned on the next write (iter-38/39/44 stale-cache discipline). Bump this token on any future
# change to the served Regime-Lab shape. No new `table=True` model (the `test_db.py` guard stays unchanged).
_REGIME_LAB_SUBJECT = "__regime_lab__"
_REGIME_LAB_SCHEMA_TOKEN = "regimelab-v1"


def regime_lab_cached(
    session: Session, config: Optional[Config] = None, *,
    view: str = VIEW_EPISODES, as_of: Optional[date_cls] = None,
) -> dict:
    """Serve the all-horizons Regime Lab (J-110) from the J-72 cache (mirrors `factor_lab_all_cached`),
    reusing the SHARED `EventStudyCache` table under the `_REGIME_LAB_SUBJECT` sentinel + the actual `view`
    (so episodes/pooled never collide), no new table. The view is horizon-independent (it shows every config
    horizon at once), so the cache `horizon` slot is pinned to `default_horizon` and the dataset-version slot
    folds in `_REGIME_LAB_SCHEMA_TOKEN` (so any old-schema row is a guaranteed MISS and is pruned on write).
    On a HIT for the current `(sentinel, view, asof_key, dataset_version+token, default_horizon)` key, return
    the stored payload (NO recompute); on a MISS, compute it ONCE via `compute_regime_lab` (which validates
    the view, raising before any write), persist under the current stamp, prune any stale rows for this
    identity, and return it. BYTE-IDENTICAL to a fresh compute; the cache REFRESHES after any dataset change
    via the dataset-version key. `as_of` is folded into the `asof_key` slot (a pure observation-set FILTER)."""
    cfg = config or get_config()
    version = f"{_dataset_version(session)}-{_REGIME_LAB_SCHEMA_TOKEN}"
    asof_key = _cache_asof_key(as_of)
    horizon = cfg.walk_forward.default_horizon  # the horizon-independent view pins the cache horizon slot

    hit = session.exec(
        select(EventStudyCache).where(
            EventStudyCache.subject == _REGIME_LAB_SUBJECT,
            EventStudyCache.view == view,
            EventStudyCache.asof_key == asof_key,
            EventStudyCache.dataset_version == version,
            EventStudyCache.horizon == horizon,
        )
    ).first()
    if hit is not None:
        return json.loads(hit.payload_json)

    # MISS — compute once (this also validates the view, raising before any write) and persist.
    payload = compute_regime_lab(session, cfg, view=view, as_of=as_of)

    stale = session.exec(
        select(EventStudyCache).where(
            EventStudyCache.subject == _REGIME_LAB_SUBJECT,
            EventStudyCache.view == view,
            EventStudyCache.asof_key == asof_key,
            EventStudyCache.horizon == horizon,
            EventStudyCache.dataset_version != version,
        )
    ).all()
    for row in stale:
        session.delete(row)

    session.add(EventStudyCache(
        subject=_REGIME_LAB_SUBJECT, view=view, asof_key=asof_key, dataset_version=version,
        horizon=horizon, payload_json=json.dumps(payload),
        created_at=datetime.now(timezone.utc),
    ))
    try:
        session.commit()
    except Exception:  # best-effort cache; a concurrent writer raced us — the payload is byte-identical
        session.rollback()
    return payload


# --------------------------------------------------------------------------------------------------
# Market Phase & Severity Lab (J-111) — the STRUCTURAL TWIN of the Regime Lab (J-110): cross-sectional
# forward returns + paired max-drawdown grouped (a) by the five canonical market-PHASE labels and (b) into
# deciles of the 0–100 SEVERITY score. A read-only re-surfacing of ALREADY-STORED canonical values: it pools
# the SAME cross-sectional per-observation forward returns the Factor Lab / Regime Lab / event study build
# (stock × snapshot), tags each observation with its snapshot date's SERVED phase label + 0–100 severity
# score read VERBATIM from the `market_phase` causal timeline (`phase_context_by_date` — the SAME single
# derived series the Dashboard panel + J-97/J-102/J-103 consume; no phase/severity recomputed), joined BY
# SNAPSHOT DATE, and groups them two ways at EVERY config horizon as paired (mean forward-return, mean
# max-drawdown) columns, with the rank-IC of the severity score vs the forward return per horizon. It
# recomputes NO phase / severity / return / drawdown and introduces NO new canonical value. NOT a fitted/
# learned/ML model. It is DISTINCT from J-110 (the REGIME score/label, read from `ScannerRun`) and from J-103
# (severity-velocity SIGN/slope vs SPY): it studies the severity LEVEL + the market-phase LABEL against
# cross-sectional stock returns, on its OWN home (no duplicate home). The ONLY material difference from J-110
# is the grouping subject's SOURCE — the served `market_phase` timeline, joined by snapshot date.
# --------------------------------------------------------------------------------------------------
def _phase_severity_meta_by_run(
    session: Session, needed_runs: set[int], batch: int, phase_ctx: dict[str, dict]
) -> dict[int, tuple[Optional[str], Optional[float]]]:
    """`run_id -> (served phase label, served 0–100 severity)` over the FR-bearing runs, column-projected +
    `yield_per`-streamed. The phase + severity are read VERBATIM from the SERVED `market_phase` causal
    timeline (`phase_ctx`, == `phase_context_by_date`), joined to each run BY SNAPSHOT DATE (the run's
    `asof_date` ISO key) — it recomputes NO phase / severity. The single structural difference from J-110's
    `_regime_meta_by_run` (which read the regime off the immutable `ScannerRun`): the grouping subject comes
    from the served timeline, joined by date. A run whose snapshot date has NO timeline entry (the warm-up
    head, where `_severity_reading` yields nothing) gets `(None, None)` — an honest UNCLASSIFIED tag, never a
    fabricated phase/severity (the by-label table never emits a row for it; the decile split EXCLUDES it)."""
    if not needed_runs:
        return {}
    meta: dict[int, tuple[Optional[str], Optional[float]]] = {}
    stmt = select(ScannerRun.id, ScannerRun.asof_date).where(ScannerRun.id.in_(needed_runs))
    for run_id, asof_date in session.exec(stmt).yield_per(batch):
        ctx = phase_ctx.get(asof_date.isoformat())  # join BY SNAPSHOT DATE to the served timeline
        meta[run_id] = (ctx["phase"], ctx["severity"]) if ctx is not None else (None, None)
    return meta


def _phase_severity_lab_members_by_horizon(
    session: Session, horizons: list[int], as_of: Optional[date_cls] = None,
    *, cfg: Optional[Config] = None,
) -> dict[int, list[dict]]:
    """The read-only SHARED per-observation pools for the Phase & Severity Lab across EVERY horizon in
    `horizons` (J-111), built from a SINGLE batched read (mirrors `_regime_lab_members_by_horizon`): ONE
    `ForwardReturn` SELECT covering all horizons (`horizon IN horizons`, column-projected to run_id/symbol/
    realized_return/max_drawdown), ONE `ScannerResult` stream, ONE projected per-run snapshot-date read, and
    ONE read of the SERVED `market_phase` causal timeline (`phase_context_by_date`, read VERBATIM). Returns
    `{horizon: [observations]}` where each observation is `{run_id, ticker, return, max_drawdown, phase,
    severity}` — the realized forward return + the J-86 max_drawdown (read VERBATIM) tagged with the snapshot
    date's SERVED phase label + 0–100 severity (read VERBATIM from the timeline, joined BY SNAPSHOT DATE). It
    recomputes NO phase / severity / return / drawdown.

    BYTE-IDENTITY keystone: `{horizon: pools}[h]` is byte-identical (row-for-row, same `(run_id, id)` order)
    to calling this builder with `horizons=[h]` — the property `compute_phase_severity_lab` (all-horizons) and
    the `_phase_severity_lab_observation_set` samples drill-down (single-horizon) both rely on for count-
    coherence. An observation is kept for horizon h ONLY when a realized return exists at h (the SAME n=0
    exclusion as the Factor / Regime Lab); a ScannerResult whose run has FRs at some OTHER horizon but not at h
    contributes nothing to `pools[h]`.

    `as_of` (J-32) scopes ALL horizons' pools to snapshots with `ScannerRun.asof_date <= as_of` AND scopes the
    served timeline to dates <= as_of (the SAME single membership filter on both sides — a consistent point-in-
    time window); `as_of=None` adds NO clause -> byte-identical all-history.

    iter-46/47/48 OOM lesson / J-105: the read is BOUNDED — the FR scan is column-projected + `yield_per`-
    streamed, the ScannerResult side is column-projected (run_id/id/ticker — the phase/severity are per-RUN, so
    the heavy `record_json` is NOT read here) and `yield_per`-streamed in `(run_id, id)` order (rides
    `ix_scanner_results_run_id`, so no `USE TEMP B-TREE FOR ORDER BY` spills a temp file to a nearly-full disk;
    a bare `ORDER BY id` returned `disk is full` on this host). ONE heavy read serves ALL horizons (not H
    reads) — and there is NO unbounded `.all()` over `ForwardReturn` or `ScannerResult`."""
    from app.engine.market_phase import phase_context_by_date  # lazy import (avoids a market_phase<->research cycle)

    cfg = cfg or get_config()
    batch = cfg.research.read_batch_size
    fr_stmt = select(
        ForwardReturn.horizon, ForwardReturn.run_id, ForwardReturn.symbol,
        ForwardReturn.realized_return, ForwardReturn.max_drawdown,
    ).where(ForwardReturn.horizon.in_(horizons))
    if as_of is not None:
        fr_stmt = fr_stmt.join(ScannerRun, ScannerRun.id == ForwardReturn.run_id).where(
            ScannerRun.asof_date <= as_of
        )
    fr_by_h: dict[int, dict[tuple[int, str], tuple[float, Optional[float]]]] = {h: {} for h in horizons}
    runs_with_fr_set: set[int] = set()
    for h, run_id, symbol, realized_return, max_drawdown in session.exec(fr_stmt).yield_per(batch):
        fr_by_h[h][(run_id, symbol)] = (realized_return, max_drawdown)
        runs_with_fr_set.add(run_id)
    runs_with_fr = sorted(runs_with_fr_set)
    # the SERVED phase label + 0–100 severity per snapshot date, read VERBATIM from the SAME single causal
    # timeline the panel + J-97/J-102/J-103 read (<= the resolved as-of — never a second computation). Keyed
    # by ISO date; joined to each run BY SNAPSHOT DATE in `_phase_severity_meta_by_run`.
    phase_ctx = phase_context_by_date(session, as_of, cfg)
    phase_by_run = _phase_severity_meta_by_run(session, runs_with_fr_set, batch, phase_ctx)
    # the ScannerResult side: only (run_id, id, ticker) is needed to join the FR (the phase/severity are
    # per-RUN, not per-result) — a lighter column projection than the Factor Lab's full-row stream. Ordered
    # (run_id, id).
    res_stmt = (
        select(ScannerResult.run_id, ScannerResult.id, ScannerResult.ticker)
        .where(ScannerResult.run_id.in_(runs_with_fr))
        .order_by(ScannerResult.run_id, ScannerResult.id)
    )
    results = session.exec(res_stmt).yield_per(batch) if runs_with_fr else []

    pools: dict[int, list[dict]] = {h: [] for h in horizons}
    for run_id, _res_id, ticker in results:
        phase_meta: Optional[tuple] = None  # resolved lazily on the first horizon that has an FR
        for h in horizons:
            fr = fr_by_h[h].get((run_id, ticker))
            if fr is None:
                continue  # no realized return at this horizon (n=0) — same exclusion as the Regime Lab
            if phase_meta is None:
                phase_meta = phase_by_run.get(run_id, (None, None))
            realized, max_drawdown = fr
            phase, severity = phase_meta
            pools[h].append({
                "run_id": run_id, "ticker": ticker, "return": realized, "max_drawdown": max_drawdown,
                # the snapshot date's SERVED phase label + 0–100 severity, read VERBATIM — never recomputed.
                "phase": phase, "severity": severity,
            })
    return pools


def _severity_ordered(members: list[dict]) -> list[dict]:
    """The Phase & Severity-Lab observation members reshaped to the `_deciles` 'factor' contract — `factor` =
    the served 0–100 `severity` LEVEL — and ordered ascending by severity with the deterministic
    `(severity, ticker, run_id)` tie-break. This is the SINGLE ordering BOTH the by-decile aggregate AND the
    samples decile drill-down read, so a decile's drill-down `total` EQUALS its published `n` by construction
    (count-coherence keystone — one quantile-edge definition, never a second). An observation with a NULL
    severity (a warm-up-head snapshot date with no served timeline value) is EXCLUDED (never bucketed) —
    honest, not fabricated (mirrors the Regime Lab's score-NULL exclusion)."""
    scored = [
        {
            "factor": m["severity"], "ticker": m["ticker"], "run_id": m["run_id"],
            "return": m["return"], "max_drawdown": m["max_drawdown"],
            # carry the served phase label too (ignored by `_deciles`, but surfaced on a decile drill-down row
            # so each row shows which phase the severity came from). Read verbatim — never recomputed.
            "phase": m["phase"], "severity": m["severity"],
        }
        for m in members
        if m["severity"] is not None
    ]
    return sorted(scored, key=lambda o: (o["factor"], o["ticker"], o["run_id"]))


def _phase_severity_lab_observation_set(
    session: Session, horizon: int, view: str, as_of: Optional[date_cls] = None,
    *, cfg: Optional[Config] = None,
) -> list[dict]:
    """The Phase & Severity-Lab observation set for ONE (horizon, view) — the SINGLE membership builder the
    samples drill-down reads, so a cohort's drill-down `total` EQUALS its published `n` by construction (J-51
    count-coherence keystone). `view="pooled"` returns the per-signal-day pool UNCHANGED; `view="episodes"`
    returns its first-trigger episode collapse (`_collapse_to_episodes`, the SAME overlap-honesty collapse
    the event study uses, J-63). Built via the SAME `_phase_severity_lab_members_by_horizon` builder
    `compute_phase_severity_lab` reads (single-horizon call — byte-identical to that horizon's slice of the
    all-horizons build), so the samples set is byte-identical to the published one. Recomputes nothing. `as_of`
    scopes both the members and the run-ordinal index to the same point-in-time window."""
    members = _phase_severity_lab_members_by_horizon(session, [horizon], as_of, cfg=cfg)[horizon]
    if view == VIEW_POOLED:
        return members  # the unchanged per-signal-day pool — byte-identical to the published pooled set
    run_position = _run_position_index(session, as_of)
    return _collapse_to_episodes(members, run_position)  # first-trigger episode collapse (J-63)


def compute_phase_severity_lab(
    session: Session, config: Optional[Config] = None, *,
    view: str = VIEW_EPISODES, as_of: Optional[date_cls] = None,
) -> dict:
    """The SINGLE canonical Phase & Severity-Lab analysis (Data Contract value, J-111) under the chosen
    overlap-honesty `view`. READS the stored cross-sectional forward returns (`realized_return` + the J-86
    `max_drawdown`, VERBATIM) tagged with each snapshot date's SERVED `market_phase` phase label + 0–100
    severity (J-87/J-97, VERBATIM from `phase_context_by_date`, joined by snapshot date) — it recomputes NO
    phase, NO severity, NO return, NO drawdown. Groups them two ways at EVERY `config.walk_forward.horizons`
    horizon:

      - `by_label`  — one entry per CONFIGURED market-phase label (`config.market_phase.labels` order — no
        hard-coded phase list), each carrying per horizon: mean realized forward return, paired mean
        max-drawdown, `n`, `low_sample` (`n < walk_forward.min_sample`).
      - `by_decile` — D1…D`research.factor_lab.deciles` of the 0–100 severity score (the EXISTING generic
        `_deciles` / `_decile_member_slice` machinery, the SAME quantile-edge definition the samples drill-down
        reads), each carrying per horizon: mean return, paired mean max-drawdown, `n`, `low_sample`, and the
        decile's severity-score range (`score_min`/`score_max`).
      - `rank_ic_by_horizon` — the Spearman rank-IC of the severity score vs the realized forward return, per
        horizon (the decile table's header figure; `{value, n}`, NA when n < 2 or zero rank variance).

    Every figure is byte-identical to the reference aggregation over `_phase_severity_lab_observation_set(
    horizon, view)` (the SAME builders the samples drill-down reads — one computation path, no number
    recomputed). The view shows ALL horizons at once (paired columns), so it takes NO `horizon` argument.
    `as_of` (J-32) scopes the observation set to snapshots dated <= D (a pure FILTER — recomputes nothing);
    `as_of=None` is the all-history aggregate. The payload echoes the resolved cutoff as `asof_date` (ISO)
    when scoped, else `null`. Raises `ValueError` for an unknown view (the API pre-validates -> 422)."""
    cfg = config or get_config()
    wf = cfg.walk_forward
    fl = cfg.research.factor_lab
    horizons = list(wf.horizons)

    if view not in ALL_VIEWS:
        raise ValueError(f"unknown view {view!r}; valid views are {list(ALL_VIEWS)}")

    labels = list(cfg.market_phase.labels)

    # ONE heavy read builds the per-observation pools for ALL horizons (the bounded, byte-identity-preserving
    # keystone); the episode collapse (when the view is episodes) is a pure in-memory grouping of those SAME
    # stored rows, computed ONCE per horizon and shared by both the by-label and by-decile groupings.
    pools = _phase_severity_lab_members_by_horizon(session, horizons, as_of, cfg=cfg)
    run_position = _run_position_index(session, as_of) if view == VIEW_EPISODES else None
    members_by_h: dict[int, list[dict]] = {}
    for h in horizons:
        members = pools[h]
        members_by_h[h] = members if view == VIEW_POOLED else _collapse_to_episodes(members, run_position)

    # (a) by-label: every configured market-phase label emits a row even at n=0 (honest empty row — never
    # omitted, never fabricated). The paired mean max-drawdown uses the SAME NA convention as the Factor /
    # Regime Lab (mean over only the members with a stored drawdown; None when none).
    by_label: list[dict] = []
    for label in labels:
        by_horizon: list[dict] = []
        for h in horizons:
            label_members = [m for m in members_by_h[h] if m["phase"] == label]
            returns = [m["return"] for m in label_members]
            mdds = [m["max_drawdown"] for m in label_members if m["max_drawdown"] is not None]
            n = len(label_members)
            by_horizon.append({
                "horizon": h,
                "n": n,
                "low_sample": n < wf.min_sample,
                "mean_return": mean(returns) if returns else None,
                "mean_max_drawdown": _mean_or_none(mdds),
            })
        by_label.append({"phase": label, "by_horizon": by_horizon})

    # (b) by-decile of the 0–100 severity score (the generic `_deciles` machinery) + the per-horizon rank-IC of
    # the severity score vs the realized forward return.
    decile_rows_by_h: dict[int, list[dict]] = {}
    rank_ic_by_horizon: list[dict] = []
    for h in horizons:
        ordered = _severity_ordered(members_by_h[h])
        decile_rows_by_h[h] = _deciles(ordered, fl.deciles, wf.min_sample)
        rank_ic_by_horizon.append({
            "horizon": h,
            "rank_ic": _rank_ic([(o["factor"], o["return"]) for o in ordered]),
        })
    by_decile: list[dict] = []
    for d in range(1, fl.deciles + 1):
        by_horizon = []
        for h in horizons:
            drow = decile_rows_by_h[h][d - 1]
            by_horizon.append({
                "horizon": h,
                "n": drow["n"],
                "low_sample": drow["low_sample"],
                "mean_return": drow["mean_return"],
                "mean_max_drawdown": drow["mean_max_drawdown"],
                # the decile's severity-score range (the `_deciles` factor bounds, re-labelled to "score").
                "score_min": drow["factor_min"],
                "score_max": drow["factor_max"],
            })
        by_decile.append({"decile": d, "by_horizon": by_horizon})

    return {
        "view": view,  # J-63: the resolved overlap-honesty view (episodes default | pooled)
        # the resolved as-of scoping cutoff echoed (J-32) — ISO date when scoped, null in all-history mode.
        "asof_date": as_of.isoformat() if as_of is not None else None,
        "horizons": horizons,
        "default_horizon": wf.default_horizon,  # the horizon the rank-IC column header is labelled with
        "deciles_count": fl.deciles,
        "min_sample": wf.min_sample,
        "phase_labels": labels,  # the by-label row vocabulary (config-driven — not hard-coded in the UI)
        "survivorship_bias": SURVIVORSHIP_BIAS_LABEL,
        "descriptive_caveat": RESEARCH_CAVEAT,
        "by_label": by_label,
        "by_decile": by_decile,
        "rank_ic_by_horizon": rank_ic_by_horizon,
    }


# The all-horizons Phase & Severity-Lab view is served through the SHARED `EventStudyCache` under a fixed
# sentinel subject (never colliding with a real event-study subject or the other sentinels), pinned to
# `default_horizon` (the horizon-independent all-horizons view). The served shape is NEW (by-phase-label +
# by-severity-decile paired columns), so a schema token is folded into the dataset-version slot — any
# old-schema cached row keyed by the bare `_dataset_version` is a guaranteed MISS AND is pruned on the next
# write (iter-38/39/44 stale-cache discipline). UNIQUE to J-111 (the single-source subtlety): the phase/
# severity values are read from the `market_phase` series, whose OWN cache carries a `SCHEMA_VERSION` (bumped
# `s1`→`s2` at iter-44) + a dataset stamp — so the market-phase stamp `f"{_dataset_version}|{SCHEMA_VERSION}"`
# is ALSO folded into the lab key, so a phase/severity refresh (a schema bump OR a dataset change) invalidates
# the lab (no stale phase tags). No new `table=True` model (the `test_db.py` guard stays unchanged).
_PHASE_SEVERITY_LAB_SUBJECT = "__phase_severity_lab__"
_PHASE_SEVERITY_LAB_SCHEMA_TOKEN = "phaseseverlab-v1"


def _phase_severity_lab_cache_version(session: Session) -> str:
    """The composite cache-key version for the Phase & Severity Lab: the J-72 dataset stamp + the lab's
    payload-SCHEMA token + the SERVED `market_phase` dataset/`SCHEMA_VERSION` stamp (single-sourced from
    `market_phase._cache_version`, the SAME stamp the phase/severity series caches under). Folding the
    market-phase stamp is the single-source subtlety UNIQUE to J-111: because the phase label + severity are
    read from the served `market_phase` timeline, a phase/severity refresh (a `SCHEMA_VERSION` bump OR a
    market-phase dataset change) MUST invalidate this lab so no stale phase tag is ever served."""
    from app.engine import market_phase  # lazy import (avoids a market_phase<->research cycle)

    return (
        f"{_dataset_version(session)}-{_PHASE_SEVERITY_LAB_SCHEMA_TOKEN}"
        f"-mp:{market_phase._cache_version(session)}"
    )


def phase_severity_lab_cached(
    session: Session, config: Optional[Config] = None, *,
    view: str = VIEW_EPISODES, as_of: Optional[date_cls] = None,
) -> dict:
    """Serve the all-horizons Phase & Severity Lab (J-111) from the J-72 cache (mirrors `regime_lab_cached`),
    reusing the SHARED `EventStudyCache` table under the `_PHASE_SEVERITY_LAB_SUBJECT` sentinel + the actual
    `view` (so episodes/pooled never collide), no new table. The view is horizon-independent (it shows every
    config horizon at once), so the cache `horizon` slot is pinned to `default_horizon` and the dataset-version
    slot is `_phase_severity_lab_cache_version` (the dataset stamp + the lab schema token + the market-phase
    stamp — so any old-schema OR stale-phase row is a guaranteed MISS and is pruned on write). On a HIT for the
    current `(sentinel, view, asof_key, dataset_version, default_horizon)` key, return the stored payload (NO
    recompute); on a MISS, compute it ONCE via `compute_phase_severity_lab` (which validates the view, raising
    before any write), persist under the current stamp, prune any stale rows for this identity, and return it.
    BYTE-IDENTICAL to a fresh compute; the cache REFRESHES after any dataset change OR a phase/severity
    schema/dataset change via the composite key. `as_of` is folded into the `asof_key` slot (a pure
    observation-set FILTER)."""
    cfg = config or get_config()
    version = _phase_severity_lab_cache_version(session)
    asof_key = _cache_asof_key(as_of)
    horizon = cfg.walk_forward.default_horizon  # the horizon-independent view pins the cache horizon slot

    hit = session.exec(
        select(EventStudyCache).where(
            EventStudyCache.subject == _PHASE_SEVERITY_LAB_SUBJECT,
            EventStudyCache.view == view,
            EventStudyCache.asof_key == asof_key,
            EventStudyCache.dataset_version == version,
            EventStudyCache.horizon == horizon,
        )
    ).first()
    if hit is not None:
        return json.loads(hit.payload_json)

    # MISS — compute once (this also validates the view, raising before any write) and persist.
    payload = compute_phase_severity_lab(session, cfg, view=view, as_of=as_of)

    stale = session.exec(
        select(EventStudyCache).where(
            EventStudyCache.subject == _PHASE_SEVERITY_LAB_SUBJECT,
            EventStudyCache.view == view,
            EventStudyCache.asof_key == asof_key,
            EventStudyCache.horizon == horizon,
            EventStudyCache.dataset_version != version,
        )
    ).all()
    for row in stale:
        session.delete(row)

    session.add(EventStudyCache(
        subject=_PHASE_SEVERITY_LAB_SUBJECT, view=view, asof_key=asof_key, dataset_version=version,
        horizon=horizon, payload_json=json.dumps(payload),
        created_at=datetime.now(timezone.utc),
    ))
    try:
        session.commit()
    except Exception:  # best-effort cache; a concurrent writer raced us — the payload is byte-identical
        session.rollback()
    return payload


# --------------------------------------------------------------------------------------------------
# Regime × Market-Phase/Severity × Factor 3-way decile study (J-112) — the UNION of the Regime Lab (J-110)
# and the Phase & Severity Lab (J-111) source paths, surfaced through the J-77/J-82 ranked-combination
# pattern (a ranked, filterable, paginated combination table) instead of the sibling two-table layout. For a
# SELECTED factor it groups the SAME cross-sectional per-observation forward returns the sibling labs build
# (stock × snapshot) by the `(regime-score decile × severity-score decile × factor decile)` triple, reporting
# per `config.walk_forward.horizons` horizon the combination's mean realized forward return + paired mean
# max-drawdown + n. A read-only re-surfacing of ALREADY-STORED canonical values — it recomputes NOTHING:
#   (a) the run's STORED `ScannerRun.regime_score` read VERBATIM (the J-80/J-110 path, via `_regime_meta_by_run`),
#   (b) the snapshot date's SERVED 0–100 severity read VERBATIM from the `market_phase` causal timeline
#       (`phase_context_by_date`, joined by snapshot date — the J-87/J-111 path, via `_phase_severity_meta_by_run`),
#   (c) the SELECTED factor's STORED value read VERBATIM off the `ScannerResult` (the Factor-Lab source, via
#       `_extract_factor_value`),
# each bucketed into deciles via the EXISTING generic `_deciles`/`_decile_member_slice` edges and grouped by
# the triple key. NOT a fitted/learned/ML model. It is DISTINCT from J-77 (regime × setup × pattern), J-103
# (severity-velocity SIGN/slope vs SPY), J-110 (regime alone) and J-111 (phase/severity alone): the THREE-WAY
# regime × severity × factor-decile interaction, on its OWN home (no duplicate home, no recomputed value). It
# is the ONLY lab that reads BOTH the regime path AND the served-severity path in the same observation.
# --------------------------------------------------------------------------------------------------
def _regime_phase_factor_members_by_horizon(
    session: Session, horizons: list[int], factor, as_of: Optional[date_cls] = None,
    *, cfg: Optional[Config] = None,
) -> dict[int, list[dict]]:
    """The read-only SHARED per-observation pools for the Regime × Phase × Factor study across EVERY horizon
    in `horizons` (J-112) for the SELECTED `factor` (a config-catalog factor object), built from a SINGLE
    batched read (mirrors `_regime_lab_members_by_horizon` / `_phase_severity_lab_members_by_horizon`): ONE
    `ForwardReturn` SELECT covering all horizons (`horizon IN horizons`, column-projected to run_id/symbol/
    realized_return/max_drawdown), ONE projected per-run regime read, ONE read of the SERVED `market_phase`
    causal timeline + a projected per-run snapshot-date join, and ONE `ScannerResult` stream. Returns
    `{horizon: [observations]}` where each observation is `{run_id, ticker, return, max_drawdown,
    regime_score, severity, factor_value}` — the realized forward return + the J-86 max_drawdown (read
    VERBATIM) tagged with the run's STORED `regime_score` (J-80, VERBATIM), the snapshot date's SERVED 0–100
    severity (J-87/J-111, VERBATIM from the timeline, joined BY SNAPSHOT DATE), and the SELECTED factor's
    STORED value (the Factor-Lab `_extract_factor_value`, VERBATIM). It recomputes NO regime / severity /
    factor / return / drawdown.

    UNIQUE to J-112: it reads BOTH source paths in the SAME observation — the regime score off the immutable
    `ScannerRun` AND the served severity off the `market_phase` timeline by snapshot date AND the factor off
    the `ScannerResult`. A None tag on ANY dimension (a warm-up-head date with no served severity, a NULL
    component factor) is kept honestly None and is EXCLUDED from the displayed buckets at the decile-assignment
    stage (`_assign_triple_deciles`) — never fabricated.

    BYTE-IDENTITY keystone: `{horizon: pools}[h]` is byte-identical (row-for-row, same `(run_id, id)` order)
    to calling this builder with `horizons=[h]` — the property `compute_regime_phase_factor_study` (all-
    horizons) and the `_regime_phase_factor_observation_set` samples drill-down (single-horizon) both rely on
    for count-coherence. An observation is kept for horizon h ONLY when a realized return exists at h (the SAME
    n=0 exclusion as the sibling labs); a ScannerResult whose run has FRs at some OTHER horizon but not at h
    contributes nothing to `pools[h]`.

    `as_of` (J-32) scopes ALL horizons' pools to snapshots with `ScannerRun.asof_date <= as_of` AND scopes the
    served timeline to dates <= as_of (the SAME single membership filter on both sides — a consistent point-in-
    time window); `as_of=None` adds NO clause -> byte-identical all-history.

    iter-46/47/48 OOM lesson / J-105: the read is BOUNDED — the FR scan is column-projected + `yield_per`-
    streamed; the ScannerResult side is streamed in `(run_id, id)` order (rides `ix_scanner_results_run_id`, so
    no `USE TEMP B-TREE FOR ORDER BY` spills a temp file to a nearly-full disk; a bare `ORDER BY id` returned
    `disk is full` on this host). Unlike the regime/phase labs (where the grouping subject is per-RUN), the
    factor value is per-RESULT and a COMPONENT factor reads `res.record_json`, so the full ScannerResult ORM
    row is streamed here exactly as the Factor Lab does — still bounded by `yield_per`, never an unbounded
    `.all()`. ONE heavy read serves ALL horizons (not H reads)."""
    from app.engine.market_phase import phase_context_by_date  # lazy import (avoids a market_phase<->research cycle)

    cfg = cfg or get_config()
    batch = cfg.research.read_batch_size
    parsed = parse_factor_source(factor.source)
    fr_stmt = select(
        ForwardReturn.horizon, ForwardReturn.run_id, ForwardReturn.symbol,
        ForwardReturn.realized_return, ForwardReturn.max_drawdown,
    ).where(ForwardReturn.horizon.in_(horizons))
    if as_of is not None:
        fr_stmt = fr_stmt.join(ScannerRun, ScannerRun.id == ForwardReturn.run_id).where(
            ScannerRun.asof_date <= as_of
        )
    fr_by_h: dict[int, dict[tuple[int, str], tuple[float, Optional[float]]]] = {h: {} for h in horizons}
    runs_with_fr_set: set[int] = set()
    for h, run_id, symbol, realized_return, max_drawdown in session.exec(fr_stmt).yield_per(batch):
        fr_by_h[h][(run_id, symbol)] = (realized_return, max_drawdown)
        runs_with_fr_set.add(run_id)
    runs_with_fr = sorted(runs_with_fr_set)
    # (a) the per-run STORED regime score, read VERBATIM (J-80) — projected + streamed over the FR-bearing runs.
    regime_by_run = _regime_meta_by_run(session, runs_with_fr_set, batch)
    # (b) the SERVED phase label + 0–100 severity per snapshot date, read VERBATIM from the SAME single causal
    # timeline the panel + J-97/J-102/J-103/J-111 read (<= the resolved as-of — never a second computation),
    # joined to each run BY SNAPSHOT DATE in `_phase_severity_meta_by_run`.
    phase_ctx = phase_context_by_date(session, as_of, cfg)
    phase_by_run = _phase_severity_meta_by_run(session, runs_with_fr_set, batch, phase_ctx)
    # the ScannerResult side: the FULL ORM row (a COMPONENT factor reads `res.record_json` — same as the
    # Factor Lab), streamed in (run_id, id) order. Bounded by `yield_per`; never an unbounded `.all()`.
    res_stmt = (
        select(ScannerResult)
        .where(ScannerResult.run_id.in_(runs_with_fr))
        .order_by(ScannerResult.run_id, ScannerResult.id)
    )
    results = session.exec(res_stmt).yield_per(batch) if runs_with_fr else []

    pools: dict[int, list[dict]] = {h: [] for h in horizons}
    for res in results:
        run_id = res.run_id
        ticker = res.ticker
        resolved = False  # the per-result tags are resolved lazily on the first horizon that has an FR
        regime_score = severity = factor_value = None
        for h in horizons:
            fr = fr_by_h[h].get((run_id, ticker))
            if fr is None:
                continue  # no realized return at this horizon (n=0) — same exclusion as the sibling labs
            if not resolved:
                regime_score = regime_by_run.get(run_id, (None, None))[0]  # (regime_score, regime_label)
                severity = phase_by_run.get(run_id, (None, None))[1]       # (phase, severity)
                value = _extract_factor_value(res, parsed)
                factor_value = float(value) if value is not None else None  # VERBATIM; None excluded later
                resolved = True
            realized, max_drawdown = fr
            pools[h].append({
                "run_id": run_id, "ticker": ticker, "return": realized, "max_drawdown": max_drawdown,
                # the three grouping dimensions, each read VERBATIM from its single canonical source.
                "regime_score": regime_score, "severity": severity, "factor_value": factor_value,
            })
    return pools


def _assign_triple_deciles(members: list[dict], deciles_count: int) -> list[dict]:
    """Tag each BUCKETABLE observation with its `(regime_decile, severity_decile, factor_decile)` — the SINGLE
    decile assignment BOTH the study aggregate AND the samples drill-down read, so a combination's drill-down
    `total` EQUALS its published `n` by construction (count-coherence keystone). An observation is bucketable
    ONLY when ALL THREE dimensions are non-null (a warm-up-head NULL severity or a NULL component factor is
    EXCLUDED — honest, never bucketed into a fabricated combination), mirroring the sibling labs' score-NULL
    exclusion. Each dimension is bucketed INDEPENDENTLY: the bucketable set is ordered ascending by that
    dimension's value with the deterministic `(value, ticker, run_id)` tie-break, then split via the EXACT
    `_decile_member_slice` quantile edges the generic `_deciles` machinery uses — so a per-horizon decile
    assignment here reproduces byte-identically in the samples builder over the SAME observation set. Returns
    NEW observation dicts (the input pool is never mutated)."""
    bucketable = [
        {**m, "regime_decile": None, "severity_decile": None, "factor_decile": None}
        for m in members
        if m["regime_score"] is not None and m["severity"] is not None and m["factor_value"] is not None
    ]
    for value_key, decile_key in (
        ("regime_score", "regime_decile"),
        ("severity", "severity_decile"),
        ("factor_value", "factor_decile"),
    ):
        ordered = sorted(bucketable, key=lambda o: (o[value_key], o["ticker"], o["run_id"]))
        for d in range(1, deciles_count + 1):
            for m in _decile_member_slice(ordered, deciles_count, d):
                m[decile_key] = d
    return bucketable


def _regime_phase_factor_observation_set(
    session: Session, horizon: int, view: str, factor, as_of: Optional[date_cls] = None,
    *, cfg: Optional[Config] = None,
) -> list[dict]:
    """The Regime × Phase × Factor observation set for ONE (horizon, view) for the SELECTED `factor` — the
    SINGLE membership builder the samples drill-down reads, so a cohort's drill-down `total` EQUALS its
    published `n` by construction (J-51 count-coherence keystone). `view="pooled"` returns the per-signal-day
    pool UNCHANGED; `view="episodes"` returns its first-trigger episode collapse (`_collapse_to_episodes`, the
    SAME overlap-honesty collapse the event study uses, J-63). Built via the SAME
    `_regime_phase_factor_members_by_horizon` builder `compute_regime_phase_factor_study` reads (single-horizon
    call — byte-identical to that horizon's slice of the all-horizons build), so the samples set is byte-
    identical to the published one. Recomputes nothing. `as_of` scopes both the members and the run-ordinal
    index to the same point-in-time window. The triple-decile tags are NOT assigned here (the caller applies
    `_assign_triple_deciles` to the SAME shape — one decile-assignment rule)."""
    members = _regime_phase_factor_members_by_horizon(session, [horizon], factor, as_of, cfg=cfg)[horizon]
    if view == VIEW_POOLED:
        return members  # the unchanged per-signal-day pool — byte-identical to the published pooled set
    run_position = _run_position_index(session, as_of)
    return _collapse_to_episodes(members, run_position)  # first-trigger episode collapse (J-63)


def _rpf_resolve_factor(cfg: Config, factor_key: str):
    """Resolve a factor KEY to its config-catalog factor object (the vocabulary is the EXISTING Factor-Lab
    catalog — no hardcoded list). Raises `ValueError` for an unknown key (the API pre-validates -> 422)."""
    factor = next((f for f in cfg.research.factor_lab.factors if f.key == factor_key), None)
    if factor is None:
        raise ValueError(
            f"unknown factor {factor_key!r}; valid factors are {[f.key for f in cfg.research.factor_lab.factors]}"
        )
    return factor


def _rpf_rank_key(row: dict, default_horizon: int) -> tuple:
    """The default ranking key for the J-112 table: descending by the SELECTED factor's combination mean
    realized forward return at `default_horizon`, NA last. Returns a tuple usable with `reverse=True` — a None
    metric sorts LAST under reverse via the `(is_not_none, value)` pairing (the J-21 boolean-sentinel idiom; no
    float literal — the fallback is structural to the sort, never a tunable scoring value). A deterministic
    `(regime, severity, factor)` decile tie-break is applied as a stable inner sort by the caller, so the order
    is total + reproducible."""
    cell = next((b for b in row["by_horizon"] if b["horizon"] == default_horizon), None)
    val = cell["mean_return"] if cell is not None else None
    present = val is not None
    return ((present, val if present else present),)


def compute_regime_phase_factor_study(
    session: Session, *, factor: str, view: str = VIEW_EPISODES, as_of: Optional[date_cls] = None,
    config: Optional[Config] = None,
) -> dict:
    """The SINGLE canonical Regime × Phase × Factor 3-way decile study (Data Contract value, J-112) for the
    SELECTED `factor` under the chosen overlap-honesty `view`. READS the stored cross-sectional forward returns
    (`realized_return` + the J-86 `max_drawdown`, VERBATIM) tagged with each run's STORED `regime_score` (J-80,
    VERBATIM), the snapshot date's SERVED 0–100 severity (J-87/J-111, VERBATIM from `phase_context_by_date`,
    joined by snapshot date) and the SELECTED factor's STORED value (the Factor-Lab source, VERBATIM) — it
    recomputes NO regime, NO severity, NO factor, NO return, NO drawdown. Buckets each dimension into D1…D
    `research.factor_lab.deciles` via the EXISTING `_deciles`/`_decile_member_slice` edges (one quantile-edge
    definition the samples drill-down reproduces) and groups by the `(regime-decile, severity-decile,
    factor-decile)` triple. For each combination that the observation set EMITS it reports, per
    `config.walk_forward.horizons` horizon: mean realized forward return, paired mean max-drawdown, `n`, and a
    `low_sample` flag (`n < walk_forward.min_sample` — the UI shows NA + n, never a fabricated number).

    The view shows ALL horizons at once (paired columns), so it takes NO `horizon` argument. Rows are ranked
    by the combination's `default_horizon` mean return (NA last) with a deterministic decile-triple tie-break;
    the columns are client-side sortable/filterable/paginated on the frontend (a pure view transform). `as_of`
    (J-32) scopes the observation set to snapshots dated <= D (a pure FILTER — recomputes nothing); `as_of=None`
    is the all-history aggregate. The payload echoes the resolved cutoff as `asof_date` (ISO) when scoped, else
    `null`, plus the config-driven `page_size` (the 30-rows/page constant — config-sourced, never an inline
    literal). Raises `ValueError` for an unknown view or factor (the API pre-validates -> 422)."""
    cfg = config or get_config()
    wf = cfg.walk_forward
    fl = cfg.research.factor_lab
    horizons = list(wf.horizons)

    if view not in ALL_VIEWS:
        raise ValueError(f"unknown view {view!r}; valid views are {list(ALL_VIEWS)}")
    factor_obj = _rpf_resolve_factor(cfg, factor)

    deciles_count = fl.deciles
    min_sample = wf.min_sample

    # ONE heavy read builds the per-observation pools for ALL horizons (the bounded, byte-identity-preserving
    # keystone); the episode collapse (when the view is episodes) is a pure in-memory grouping of those SAME
    # stored rows, computed ONCE per horizon. Each horizon is bucketed INDEPENDENTLY into the triple deciles
    # (mirroring the sibling labs' per-horizon `_deciles` split), then grouped by the triple key.
    pools = _regime_phase_factor_members_by_horizon(session, horizons, factor_obj, as_of, cfg=cfg)
    run_position = _run_position_index(session, as_of) if view == VIEW_EPISODES else None

    # combo -> {horizon: {"returns": [...], "mdds": [...]}} for every combination the observation set emits.
    combos: dict[tuple[int, int, int], dict[int, dict[str, list]]] = {}
    for h in horizons:
        members = pools[h] if view == VIEW_POOLED else _collapse_to_episodes(pools[h], run_position)
        bucketable = _assign_triple_deciles(members, deciles_count)
        grouped: dict[tuple[int, int, int], dict[str, list]] = defaultdict(
            lambda: {"returns": [], "mdds": []}
        )
        for m in bucketable:
            key = (m["regime_decile"], m["severity_decile"], m["factor_decile"])
            grouped[key]["returns"].append(m["return"])
            if m["max_drawdown"] is not None:
                grouped[key]["mdds"].append(m["max_drawdown"])
        for key, bucket in grouped.items():
            combos.setdefault(key, {})[h] = bucket

    rows: list[dict] = []
    for (regime_decile, severity_decile, factor_decile), by_h in combos.items():
        by_horizon: list[dict] = []
        for h in horizons:
            bucket = by_h.get(h)
            if bucket is None:
                # the combination has no members at this horizon (the per-horizon decile partition differs) —
                # an honest NA + n=0 cell, never a fabricated figure.
                by_horizon.append({
                    "horizon": h, "n": 0, "low_sample": True,
                    "mean_return": None, "mean_max_drawdown": None,
                })
                continue
            returns = bucket["returns"]
            n = len(returns)
            by_horizon.append({
                "horizon": h,
                "n": n,
                "low_sample": n < min_sample,
                "mean_return": mean(returns) if returns else None,
                "mean_max_drawdown": _mean_or_none(bucket["mdds"]),
            })
        rows.append({
            "regime_decile": regime_decile,
            "severity_decile": severity_decile,
            "factor_decile": factor_decile,
            "by_horizon": by_horizon,
        })

    # default ranking: a stable deterministic decile-triple inner sort first, then descending by the
    # default-horizon mean return (NA last) — a total + reproducible order (the frontend re-sorts client-side).
    rows.sort(key=lambda r: (r["regime_decile"], r["severity_decile"], r["factor_decile"]))
    rows.sort(key=lambda r: _rpf_rank_key(r, wf.default_horizon), reverse=True)

    return {
        "view": view,  # J-63: the resolved overlap-honesty view (episodes default | pooled)
        # the resolved as-of scoping cutoff echoed (J-32) — ISO date when scoped, null in all-history mode.
        "asof_date": as_of.isoformat() if as_of is not None else None,
        "factor": {
            "key": factor_obj.key, "label": factor_obj.label, "family": factor_obj.family,
            "direction": factor_obj.direction, "source": factor_obj.source,
        },
        "factors": factor_catalog(cfg),  # the config-driven factor selector vocabulary (no hardcoded list)
        "horizons": horizons,
        "default_horizon": wf.default_horizon,  # the horizon the default ranking is on
        "deciles_count": deciles_count,
        "min_sample": min_sample,
        # the config-driven rows-per-page (30 per goal.md) — served so the frontend reads it from config; the
        # pagination is a pure client-side view transform (no inline literal in this CALC_FILE).
        "page_size": cfg.research.regime_phase_factor_page_size,
        "survivorship_bias": SURVIVORSHIP_BIAS_LABEL,
        "descriptive_caveat": RESEARCH_CAVEAT,
        "rows": rows,
    }


# The all-horizons Regime × Phase × Factor study is served through the SHARED `EventStudyCache` under a fixed
# sentinel subject with the SELECTED factor folded in (`__regime_phase_factor__:<factor>`, mirroring the
# `_factor_combination__` per-identity subject) — so two factors never share a cache row (no cross-factor
# bleed) and the per-factor study never collides with a real event-study subject or the other sentinels. It
# is ONE all-horizons view per (factor, view, as-of), so the cache `horizon` slot is pinned to
# `default_horizon`. The served shape is NEW (the 3-way combination table), so a schema token is folded into
# the dataset-version slot — any old-schema cached row is a guaranteed MISS AND is pruned on the next write
# (iter-38/39/44 stale-cache discipline). TWIST shared with J-111: because the severity values are read from
# the `market_phase` series (cached behind its OWN `SCHEMA_VERSION` + dataset stamp), the market-phase stamp is
# ALSO folded into the lab cache version, so a phase/severity refresh invalidates the lab (no stale severity
# tags). No new `table=True` model (the `test_db.py` guard stays unchanged).
_REGIME_PHASE_FACTOR_SUBJECT = "__regime_phase_factor__"
_REGIME_PHASE_FACTOR_SCHEMA_TOKEN = "regimephasefactor-v1"


def _regime_phase_factor_cache_subject(factor_key: str) -> str:
    """The cache `subject` slot for the J-112 study: the fixed sentinel + the SELECTED factor key, so distinct
    factors key to distinct rows (no cross-factor cache bleed)."""
    return f"{_REGIME_PHASE_FACTOR_SUBJECT}:{factor_key}"


def _regime_phase_factor_cache_version(session: Session) -> str:
    """The composite cache-key version for the Regime × Phase × Factor study: the J-72 dataset stamp + the
    study's payload-SCHEMA token + the SERVED `market_phase` dataset/`SCHEMA_VERSION` stamp (single-sourced
    from `market_phase._cache_version`, the SAME stamp the phase/severity series caches under). Folding the
    market-phase stamp is the single-source subtlety shared with J-111: because the severity dimension is read
    from the served `market_phase` timeline, a phase/severity refresh (a `SCHEMA_VERSION` bump OR a market-
    phase dataset change) MUST invalidate this study so no stale severity tag is ever served."""
    from app.engine import market_phase  # lazy import (avoids a market_phase<->research cycle)

    return (
        f"{_dataset_version(session)}-{_REGIME_PHASE_FACTOR_SCHEMA_TOKEN}"
        f"-mp:{market_phase._cache_version(session)}"
    )


def regime_phase_factor_cached(
    session: Session, config: Optional[Config] = None, *,
    factor: str, view: str = VIEW_EPISODES, as_of: Optional[date_cls] = None,
) -> dict:
    """Serve the all-horizons Regime × Phase × Factor study (J-112) from the J-72 cache (mirrors
    `phase_severity_lab_cached`), reusing the SHARED `EventStudyCache` table under the per-factor
    `_regime_phase_factor_cache_subject` + the actual `view` (so factors / episodes / pooled never collide),
    no new table. The view is horizon-independent (it shows every config horizon at once), so the cache
    `horizon` slot is pinned to `default_horizon` and the dataset-version slot is
    `_regime_phase_factor_cache_version` (the dataset stamp + the study schema token + the market-phase stamp —
    so any old-schema OR stale-severity row is a guaranteed MISS and is pruned on write). On a HIT for the
    current `(subject, view, asof_key, dataset_version, default_horizon)` key, return the stored payload (NO
    recompute); on a MISS, compute it ONCE via `compute_regime_phase_factor_study` (which validates the view +
    factor, raising before any write), persist under the current stamp, prune any stale rows for this identity,
    and return it. BYTE-IDENTICAL to a fresh compute; the cache REFRESHES after any dataset change OR a
    phase/severity schema/dataset change via the composite key. `as_of` is folded into the `asof_key` slot (a
    pure observation-set FILTER)."""
    cfg = config or get_config()
    # validate the factor up front (so an unknown factor raises before any cache read/write) and key the cache
    # on the RESOLVED catalog key (never a malformed input string).
    factor_obj = _rpf_resolve_factor(cfg, factor)
    subject = _regime_phase_factor_cache_subject(factor_obj.key)
    version = _regime_phase_factor_cache_version(session)
    asof_key = _cache_asof_key(as_of)
    horizon = cfg.walk_forward.default_horizon  # the horizon-independent view pins the cache horizon slot

    hit = session.exec(
        select(EventStudyCache).where(
            EventStudyCache.subject == subject,
            EventStudyCache.view == view,
            EventStudyCache.asof_key == asof_key,
            EventStudyCache.dataset_version == version,
            EventStudyCache.horizon == horizon,
        )
    ).first()
    if hit is not None:
        return json.loads(hit.payload_json)

    # MISS — compute once (this also validates the view, raising before any write) and persist.
    payload = compute_regime_phase_factor_study(session, factor=factor_obj.key, view=view, as_of=as_of, config=cfg)

    stale = session.exec(
        select(EventStudyCache).where(
            EventStudyCache.subject == subject,
            EventStudyCache.view == view,
            EventStudyCache.asof_key == asof_key,
            EventStudyCache.horizon == horizon,
            EventStudyCache.dataset_version != version,
        )
    ).all()
    for row in stale:
        session.delete(row)

    session.add(EventStudyCache(
        subject=subject, view=view, asof_key=asof_key, dataset_version=version,
        horizon=horizon, payload_json=json.dumps(payload),
        created_at=datetime.now(timezone.utc),
    ))
    try:
        session.commit()
    except Exception:  # best-effort cache; a concurrent writer raced us — the payload is byte-identical
        session.rollback()
    return payload
