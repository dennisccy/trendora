"""Walk-forward forward-testing engine (Data Contract: app.engine.forward_testing).

This module turns the immutable as-of snapshots into hard, forward-tested evidence — the product's
keystone "does the ranking actually work?" capability (J-09, J-10), served by `GET /api/system-health`.

THREE no-negotiable disciplines, each unit-proved:

  1. NO LOOKAHEAD (forward direction). A realized forward return is measured ONLY from POST-snapshot
     bars: the entry is the close ON the run's `asof_date` D (`close_on`, date <= D) and the exit is
     the close of the h-th bar with date > D (`bars_after`, date > D). A future bar can therefore
     never influence an as-of score — the scoring side reads `bars_asof` (date <= D), this side reads
     strictly date > D, and the two never overlap.

  2. IMMUTABLE SNAPSHOTS. Forward returns are written ONLY to the separate append-only `forward_returns`
     table, keyed to the snapshot by `run_id`. The backfill performs INSERTs exclusively — it never
     UPDATEs a `scanner_runs` / `scanner_results` / `*_scores` row — and is idempotent (a second boot
     inserts zero new rows).

  3. SINGLE SOURCE OF TRUTH. `compute_forward_aggregates` READS the stored canonical bucket / setup /
     sector / rank (from `scanner_results`) and regime label (from `scanner_runs`) VERBATIM and groups
     the stored realized returns by them. It NEVER recomputes a score, bucket, or setup from a second
     formula — buckets are read, not re-derived.

Every aggregate cell carries its sample size `n`, the payload carries the `min_sample` honesty
threshold and a `survivorship_bias` label, and a (symbol, horizon) with fewer than `horizon` post-
snapshot bars contributes NO row (n=0) — never a fabricated 0% (anti-goal: No fabricated data). Every
tunable (replay window, cadence, horizons, min_sample, control-group seed/top_n/peers_per_sector,
benchmark symbols) comes from config — no walk-forward literal lives here (anti-goal: No magic numbers).
"""
from __future__ import annotations

import random
from calendar import monthrange
from collections import defaultdict
from datetime import date as date_cls, timedelta
from statistics import mean
from typing import Optional, Union

from sqlalchemy.engine import Engine
from sqlmodel import Session, select

from app.config import Config, get_config
from app.engine.prices import bars_after, bars_asof, close_on, latest_data_date
from app.engine.scanner import run_scan
from app.engine.setups import ALL_STATUSES
from app.models import ForwardReturn, ScannerResult, ScannerRun

# The honest caveat carried on every payload (anti-goal: Honest limitations surfaced). Walk-forward
# evidence is computed on the CURRENT-membership universe, so delisted/dropped names are absent.
SURVIVORSHIP_BIAS_LABEL = (
    "Walk-forward evidence is measured on the current-membership universe and therefore carries "
    "survivorship bias: names that were later delisted or dropped from the universe are absent, so "
    "realized forward returns may be overstated. Read the edge as an upper bound, not a guarantee."
)

# The A-E bucket vocabulary (string labels, not tunables) in display order — strongest to weakest.
BUCKET_ORDER = ("A", "B", "C", "D", "E")

MONTHS_PER_YEAR = 12  # calendar constant (structural, not a scoring tunable)
QUARTER_MONTHS = 3    # calendar constant (structural, not a scoring tunable)


# --------------------------------------------------------------------------------------------------
# Benchmark + forward-return symbol sets (from config — never literal tickers)
# --------------------------------------------------------------------------------------------------
def benchmark_symbols(cfg: Config) -> dict:
    """The benchmark tickers, all read from config: SPY + QQQ (`etfs.index`) and the sector ETFs
    (`etfs.sector`). Used both as forward-return symbols and as control-group comparators."""
    return {
        "spy": cfg.etfs.index[0],
        "qqq": cfg.etfs.index[1],
        "sector_etfs": list(cfg.etfs.sector.keys()),
    }


def forward_symbols(cfg: Config) -> list[str]:
    """Every symbol a forward return is stored for: the universe stocks AND the benchmark ETFs
    (SPY, QQQ, the 11 sector ETFs), de-duplicated and order-preserving."""
    bm = benchmark_symbols(cfg)
    ordered: list[str] = []
    seen: set[str] = set()
    for symbol in [*cfg.universe.symbols, bm["spy"], bm["qqq"], *bm["sector_etfs"]]:
        if symbol not in seen:
            seen.add(symbol)
            ordered.append(symbol)
    return ordered


def _sector_etf_by_name(cfg: Config) -> dict[str, str]:
    """sector NAME -> sector ETF ticker (reverse of config.etfs.sector). A stored stock row carries
    its sector NAME (config.stock_sectors), so this resolves the matching sector ETF for a control."""
    return {name: ticker for ticker, name in cfg.etfs.sector.items()}


# --------------------------------------------------------------------------------------------------
# Pure forward-return math (the keystone no-lookahead boundary)
# --------------------------------------------------------------------------------------------------
def forward_return(bars_after_list: list, entry_close: Optional[float], horizon: int) -> Optional[float]:
    """Realized return over `horizon` trading days = close of the h-th POST-snapshot bar / `entry_close`
    - 1, where `entry_close` is the close ON the as-of date D and `bars_after_list` is the ascending
    list of bars with date > D (from `bars_after`). Only the first `horizon` post-bars matter, so the
    result is unchanged when later bars are removed.

    Returns None (NA) — NEVER a fabricated/truncated number — when `entry_close` is missing or zero, or
    when fewer than `horizon` post-snapshot bars exist (the realized return is not yet observable)."""
    if entry_close is None or entry_close == 0:
        return None
    if len(bars_after_list) < horizon:
        return None
    measured_close = bars_after_list[horizon - 1].close
    return measured_close / entry_close - 1


# --------------------------------------------------------------------------------------------------
# Walk-forward as-of date set (cadence intersected with real seed trading days)
# --------------------------------------------------------------------------------------------------
def _add_months(d: date_cls, months: int) -> date_cls:
    """`d` shifted by `months` (may be negative), clamping the day to the target month's length."""
    total = d.month - 1 + months
    year = d.year + total // MONTHS_PER_YEAR
    month = total % MONTHS_PER_YEAR + 1
    day = min(d.day, monthrange(year, month)[1])
    return date_cls(year, month, day)


def _advance(d: date_cls, asof_cadence: str) -> date_cls:
    """The next calendar cadence target after `d` (snapped to a real trading day by the caller)."""
    if asof_cadence == "daily":
        return d + timedelta(days=1)
    if asof_cadence == "weekly":
        return d + timedelta(weeks=1)
    if asof_cadence == "monthly":
        return _add_months(d, 1)
    return _add_months(d, QUARTER_MONTHS)  # quarterly


def _snap_back(target: date_cls, trading_days: list[date_cls]) -> Optional[date_cls]:
    """The latest trading day <= `target` (no fabricated as-of dates), or None if before all data."""
    lo, hi = 0, len(trading_days)
    while lo < hi:
        mid = (lo + hi) // 2
        if trading_days[mid] <= target:
            lo = mid + 1
        else:
            hi = mid
    return trading_days[lo - 1] if lo > 0 else None


def walk_forward_asof_dates(session: Session, config: Optional[Config] = None) -> list[date_cls]:
    """The bounded walk-forward as-of date set: starting `history_years` before the latest data date,
    stepping at `asof_cadence`, each target snapped to the latest real trading day <= it, and capped at
    the cutoff that still leaves >= max(horizons) POST-snapshot bars (so every cadence run has a full
    forward window). Intersected with actual seed trading days; de-duplicated and ascending."""
    cfg = config or get_config()
    wf = cfg.walk_forward
    benchmark = cfg.etfs.index[0]  # SPY defines the trading calendar
    latest = latest_data_date(session)
    if latest is None:
        return []
    trading_days = [bar.date for bar in bars_asof(session, benchmark, latest)]
    max_h = max(wf.horizons)
    if len(trading_days) <= max_h:
        return []
    cutoff = trading_days[-(max_h + 1)]  # this date has exactly max_h trading days after it
    window_start = _add_months(latest, -MONTHS_PER_YEAR * wf.history_years)

    targets: list[date_cls] = []
    target = window_start
    while target <= cutoff:
        targets.append(target)
        target = _advance(target, wf.asof_cadence)

    asof: set[date_cls] = set()
    for target in targets:
        snapped = _snap_back(target, trading_days)
        if snapped is not None and snapped <= cutoff:
            asof.add(snapped)
    return sorted(asof)


# --------------------------------------------------------------------------------------------------
# Backfill — persist the cadence snapshots, then INSERT realized forward returns (idempotent)
# --------------------------------------------------------------------------------------------------
def _insert_run_forward_returns(
    session: Session,
    run: ScannerRun,
    symbols: list[str],
    horizons,
    max_h: int,
    existing: set,
) -> int:
    """INSERT the missing realized forward returns for ONE run; return how many rows were inserted.

    This is the SINGLE implementation of the forward-return INSERT (entry = the close ON D via
    `close_on`, exit = the h-th post-D bar via `bars_after` + `forward_return`), factored out of
    `_backfill` so the walk-forward boot AND the per-date `backfill_run_forward_returns` share exactly
    ONE forward-return formula (no second math path). Only keys absent from `existing` are inserted
    (idempotent), and `existing` is updated in place. INSERT-only — it never UPDATEs/overwrites a
    snapshot row. A (symbol, horizon) with fewer than `horizon` post-D bars contributes nothing
    (NA, n=0) — never a fabricated 0% (anti-goal: No fabricated data)."""
    inserted = 0
    for symbol in symbols:
        # Idempotency fast-path: if every horizon for this (run, symbol) is already persisted, skip the
        # price fetches entirely — so a warm re-run does no redundant bar materialization.
        needed = [h for h in horizons if (run.id, symbol, h) not in existing]
        if not needed:
            continue
        entry_close = close_on(session, symbol, run.asof_date)  # close ON D (date <= D)
        if entry_close is None:
            continue
        post_bars = bars_after(session, symbol, run.asof_date, limit=max_h)  # date > D, bounded
        if not post_bars:
            continue  # no post-snapshot bar -> nothing to measure (n=0)
        for horizon in needed:
            realized = forward_return(post_bars, entry_close, horizon)
            if realized is None:
                continue  # fewer than `horizon` post-bars -> NA, no fabricated row
            session.add(
                ForwardReturn(
                    run_id=run.id,
                    symbol=symbol,
                    horizon=horizon,
                    asof_date=run.asof_date,
                    entry_close=entry_close,
                    measured_date=post_bars[horizon - 1].date,
                    realized_return=realized,
                )
            )
            existing.add((run.id, symbol, horizon))
            inserted += 1
    return inserted


def _backfill(session: Session, cfg: Config) -> dict:
    latest = latest_data_date(session)
    if latest is None:
        return {"asof_dates": [], "runs_with_returns": 0, "rows_inserted": 0}

    wf = cfg.walk_forward
    horizons = wf.horizons
    max_h = max(horizons)
    symbols = forward_symbols(cfg)

    # (1)+(2): ensure a persisted immutable snapshot for every cadence as-of date. run_scan is
    # idempotent and recomputes nothing — the snapshot is the canonical bucket/setup/sector source.
    asof_dates = walk_forward_asof_dates(session, cfg)
    for asof in asof_dates:
        run_scan(session, asof, cfg)

    # Idempotency: only INSERT (run, symbol, horizon) keys that do not already exist.
    existing = {
        (fr.run_id, fr.symbol, fr.horizon) for fr in session.exec(select(ForwardReturn)).all()
    }

    # (3): for EVERY persisted run with >= 1 post-snapshot bar (including the bootstrap Risk-off runs,
    # so the by-regime sample carries both regimes), INSERT the realized per-(run, symbol, horizon)
    # forward returns. Runs with no post-snapshot bars (the latest seed-date run) insert nothing (n=0).
    runs = session.exec(select(ScannerRun)).all()
    rows_inserted = 0
    runs_with_returns = 0
    for run in runs:
        run_inserted = _insert_run_forward_returns(session, run, symbols, horizons, max_h, existing)
        rows_inserted += run_inserted
        if run_inserted:
            runs_with_returns += 1

    session.commit()
    return {
        "asof_dates": [d.isoformat() for d in asof_dates],
        "runs_with_returns": runs_with_returns,
        "rows_inserted": rows_inserted,
    }


def backfill_forward_returns(
    session_or_engine: Union[Session, Engine], config: Optional[Config] = None
) -> dict:
    """Idempotently persist the walk-forward cadence snapshots and INSERT their realized forward
    returns into the append-only `forward_returns` table. Frozen-seed-only (reads the committed seed
    via `bars_asof`/`bars_after`/`close_on` — never the network), mirroring `scanner.bootstrap_runs`.
    Accepts a `Session` (tests) or an `Engine` (the app lifespan). A second call inserts zero new rows."""
    cfg = config or get_config()
    if isinstance(session_or_engine, Session):
        return _backfill(session_or_engine, cfg)
    with Session(session_or_engine) as session:
        return _backfill(session, cfg)


# --------------------------------------------------------------------------------------------------
# Aggregation — the SINGLE canonical forward-return analysis (reads stored buckets/setups verbatim)
# --------------------------------------------------------------------------------------------------
def _mean_or_none(values: list[float]) -> Optional[float]:
    return mean(values) if values else None


def _group_means(observations: list[dict], group_attr: str, label_key: str, order, pad: bool) -> list[dict]:
    """Mean realized return + n per stored group value (`group_attr`), ordered by `order` first then any
    extras. With `pad`, every value in `order` is emitted even at n=0 (mean None) so the table is
    complete (used for the A-E bucket rows); otherwise only non-empty groups appear."""
    buckets: dict[str, list[float]] = defaultdict(list)
    for obs in observations:
        value = obs.get(group_attr)
        if value is not None:
            buckets[value].append(obs["return"])

    rows: list[dict] = []
    emitted: set = set()
    for value in order:
        if value in buckets:
            rows.append({label_key: value, "mean_return": mean(buckets[value]), "n": len(buckets[value])})
            emitted.add(value)
        elif pad:
            rows.append({label_key: value, "mean_return": None, "n": 0})
            emitted.add(value)
    for value in sorted(buckets):
        if value not in emitted:
            rows.append({label_key: value, "mean_return": mean(buckets[value]), "n": len(buckets[value])})
    return rows


def _control_groups(
    horizon: int,
    stock_obs: list[dict],
    ret_by_run_symbol: dict,
    runs_with_fr: list[int],
    cfg: Config,
) -> list[dict]:
    """The control-group cohorts at `horizon` (J-10): the top-ranked cohort vs a random same-sector
    cohort vs SPY / QQQ / sector-ETF — each numeric, labelled, with n. The random same-sector cohort is
    drawn with a deterministic RNG re-seeded from `control_group.seed` (reproducible across calls and
    restarts), sampling `peers_per_sector` stocks per sector that the top-ranked cohort occupies."""
    cg = cfg.walk_forward.control_group
    bm = benchmark_symbols(cfg)
    etf_by_sector = _sector_etf_by_name(cfg)
    rng = random.Random(cg.seed)  # re-seeded every computation -> reproducible cohort

    obs_by_run: dict[int, list[dict]] = defaultdict(list)
    for obs in stock_obs:
        obs_by_run[obs["run_id"]].append(obs)

    top_returns: list[float] = []
    random_returns: list[float] = []
    sector_etf_returns: list[float] = []
    # deterministic iteration order (sorted runs, sorted sectors, sorted pools) so RNG draws reproduce
    for run_id in sorted(obs_by_run):
        run_obs = obs_by_run[run_id]
        top_sectors = sorted(
            {o["sector"] for o in run_obs if o["rank"] is not None and o["rank"] <= cg.top_n and o["sector"]}
        )
        by_sector: dict[str, list[dict]] = defaultdict(list)
        for o in run_obs:
            if o["sector"]:
                by_sector[o["sector"]].append(o)
        for o in run_obs:
            if o["rank"] is not None and o["rank"] <= cg.top_n:
                top_returns.append(o["return"])
        for sector in top_sectors:
            pool = sorted(by_sector.get(sector, []), key=lambda o: o["ticker"])
            if pool:
                sample = rng.sample(pool, min(cg.peers_per_sector, len(pool)))
                random_returns.extend(o["return"] for o in sample)
            etf_ret = ret_by_run_symbol.get((run_id, etf_by_sector.get(sector)))
            if etf_ret is not None:
                sector_etf_returns.append(etf_ret)

    spy_returns = [ret_by_run_symbol[(r, bm["spy"])] for r in runs_with_fr if (r, bm["spy"]) in ret_by_run_symbol]
    qqq_returns = [ret_by_run_symbol[(r, bm["qqq"])] for r in runs_with_fr if (r, bm["qqq"]) in ret_by_run_symbol]

    return [
        {"key": "top_ranked", "label": f"Top-ranked cohort (rank ≤ {cg.top_n})",
         "mean_return": _mean_or_none(top_returns), "n": len(top_returns)},
        {"key": "random_same_sector", "label": "Random same-sector peers",
         "mean_return": _mean_or_none(random_returns), "n": len(random_returns)},
        {"key": "spy", "label": bm["spy"], "mean_return": _mean_or_none(spy_returns), "n": len(spy_returns)},
        {"key": "qqq", "label": bm["qqq"], "mean_return": _mean_or_none(qqq_returns), "n": len(qqq_returns)},
        {"key": "sector_etf", "label": "Sector ETF (same sectors)",
         "mean_return": _mean_or_none(sector_etf_returns), "n": len(sector_etf_returns)},
    ]


def compute_forward_aggregates(session: Session, horizon: int, config: Optional[Config] = None) -> dict:
    """The SINGLE canonical forward-return aggregation at `horizon` (Data Contract value). Joins the
    stored realized returns (`forward_returns`) to the stored canonical bucket / setup / sector / rank
    (`scanner_results`) and regime label (`scanner_runs`), all READ VERBATIM — no score/bucket/setup is
    ever recomputed. Returns, each cell carrying `n`: forward return by bucket (A-E), by setup, by
    regime; excess vs SPY and QQQ; and the control-group cohorts. Carries the `min_sample` threshold
    and the survivorship-bias label. A run with no post-snapshot bars contributes nothing (n=0)."""
    cfg = config or get_config()
    wf = cfg.walk_forward
    bm = benchmark_symbols(cfg)

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
    regime_by_run = {run.id: run.regime_label for run in run_rows}

    # Per-stock observations: each stored result joined to its stored realized return at this horizon.
    # The bucket / setup / sector / rank / regime are READ from the snapshot — never recomputed here.
    stock_obs: list[dict] = []
    for res in results:
        realized = ret_by_run_symbol.get((res.run_id, res.ticker))
        if realized is None:
            continue  # this stock has no realized return at this horizon in this run (n=0 contribution)
        stock_obs.append({
            "run_id": res.run_id,
            "ticker": res.ticker,
            "return": realized,
            "bucket": res.leadership_bucket,   # stored canonical A-E (verbatim — no re-bucketing)
            "setup": res.setup_status,         # stored canonical setup status (verbatim)
            "sector": res.sector,
            "rank": res.rank,
            "regime": regime_by_run.get(res.run_id),  # stored regime label for the run
        })

    stock_returns = [o["return"] for o in stock_obs]
    overall_mean = _mean_or_none(stock_returns)
    spy_returns = [ret_by_run_symbol[(r, bm["spy"])] for r in runs_with_fr if (r, bm["spy"]) in ret_by_run_symbol]
    qqq_returns = [ret_by_run_symbol[(r, bm["qqq"])] for r in runs_with_fr if (r, bm["qqq"]) in ret_by_run_symbol]
    spy_mean = _mean_or_none(spy_returns)
    qqq_mean = _mean_or_none(qqq_returns)

    excess = {
        "vs_spy": {
            "benchmark": bm["spy"],
            "mean_excess": (overall_mean - spy_mean) if (overall_mean is not None and spy_mean is not None) else None,
            "stock_mean": overall_mean,
            "benchmark_mean": spy_mean,
            "n": len(stock_returns),
            "benchmark_n": len(spy_returns),
        },
        "vs_qqq": {
            "benchmark": bm["qqq"],
            "mean_excess": (overall_mean - qqq_mean) if (overall_mean is not None and qqq_mean is not None) else None,
            "stock_mean": overall_mean,
            "benchmark_mean": qqq_mean,
            "n": len(stock_returns),
            "benchmark_n": len(qqq_returns),
        },
    }

    asof_dates = sorted((run.asof_date.isoformat() for run in run_rows), reverse=True)

    return {
        "horizon": horizon,
        "horizons": list(wf.horizons),
        "default_horizon": wf.default_horizon,
        "min_sample": wf.min_sample,
        "survivorship_bias": SURVIVORSHIP_BIAS_LABEL,
        "n_runs": len(runs_with_fr),
        "asof_dates": asof_dates,
        "overall": {"mean_return": overall_mean, "n": len(stock_returns)},
        "by_bucket": _group_means(stock_obs, "bucket", "bucket", BUCKET_ORDER, pad=True),
        "by_setup": _group_means(stock_obs, "setup", "setup", ALL_STATUSES, pad=False),
        "by_regime": _group_means(stock_obs, "regime", "regime", cfg.regime.labels, pad=False),
        "excess": excess,
        "control_group": _control_groups(horizon, stock_obs, ret_by_run_symbol, runs_with_fr, cfg),
    }


# --------------------------------------------------------------------------------------------------
# Per-date scorecard (J-14) — create-once population + the SINGLE per-date forward-test read
# --------------------------------------------------------------------------------------------------
def backfill_run_forward_returns(
    session: Session, run: ScannerRun, config: Optional[Config] = None
) -> dict:
    """Create-once population of ONE run's realized forward returns into the append-only
    `forward_returns` table, via the shared `_insert_run_forward_returns` helper (the single
    forward-return formula). INSERT-only + idempotent — a 2nd call inserts 0 rows and it never UPDATEs
    a `scanner_runs` / `scanner_results` / `*_scores` row (anti-goal: Snapshots immutable). Frozen-seed-
    only. This is the "first view computes once" path the No-recompute-in-the-read-path anti-goal
    explicitly permits; for a run the iter-6 boot backfill already covered it inserts nothing."""
    cfg = config or get_config()
    wf = cfg.walk_forward
    horizons = wf.horizons
    max_h = max(horizons)
    symbols = forward_symbols(cfg)
    existing = {
        (fr.run_id, fr.symbol, fr.horizon)
        for fr in session.exec(select(ForwardReturn).where(ForwardReturn.run_id == run.id)).all()
    }
    inserted = _insert_run_forward_returns(session, run, symbols, horizons, max_h, existing)
    session.commit()
    return {"run_id": run.id, "asof_date": run.asof_date.isoformat(), "rows_inserted": inserted}


def _scorecard_excess(cohort_mean: Optional[float], cohort_n: int, bench: dict) -> dict:
    """Cohort excess vs one benchmark cohort = cohort mean − benchmark mean (NA when either side is
    NA — never a fabricated 0%). Mirrors `compute_forward_aggregates`'s excess subtraction; the
    benchmark label / mean / n are READ from the shared control-group cohort, so there is no second
    source for the benchmark figure."""
    bench_mean = bench["mean_return"]
    return {
        "benchmark": bench["label"],
        "mean_excess": (cohort_mean - bench_mean)
        if (cohort_mean is not None and bench_mean is not None) else None,
        "cohort_mean": cohort_mean,
        "benchmark_mean": bench_mean,
        "n": cohort_n,
        "benchmark_n": bench["n"],
    }


def compute_run_scorecard(session: Session, run: ScannerRun, config: Optional[Config] = None) -> dict:
    """The SINGLE canonical per-date forward-test scorecard (Data Contract value, J-14). READS the
    stored `forward_returns` for THIS `run.id` joined to the stored `scanner_results` (leadership
    bucket / setup / sector / rank, read VERBATIM) — it RECOMPUTES no score, bucket, or return. For
    EACH configured horizon it returns: the as-of cohort mean realized return + `n` (cohort = stocks
    ranked <= `control_group.top_n`, i.e. the control-group "top_ranked" definition); the excess
    (cohort mean − benchmark mean) vs SPY / QQQ / sector, each with `n`; and the five control-group
    cohorts, each with `mean_return` + `n`. A horizon (or cohort) with no stored realized return for
    the run -> `mean_return: None` / `n: 0` (honest NA — never a fabricated 0%). Reuses the iter-6
    `_control_groups` so the cohort + control-group math has exactly ONE implementation."""
    cfg = config or get_config()
    wf = cfg.walk_forward

    results = session.exec(select(ScannerResult).where(ScannerResult.run_id == run.id)).all()
    fr_rows = session.exec(select(ForwardReturn).where(ForwardReturn.run_id == run.id)).all()

    by_horizon: list[dict] = []
    for horizon in wf.horizons:
        fr_at_h = [fr for fr in fr_rows if fr.horizon == horizon]
        ret_by_symbol = {fr.symbol: fr.realized_return for fr in fr_at_h}
        ret_by_run_symbol = {(run.id, sym): ret for sym, ret in ret_by_symbol.items()}
        runs_with_fr = sorted({fr.run_id for fr in fr_at_h})  # [] or [run.id]

        # Per-stock observations at this horizon: each stored result joined to its stored realized
        # return — the bucket / setup / sector / rank are READ from the snapshot, never recomputed.
        stock_obs: list[dict] = []
        for res in results:
            realized = ret_by_symbol.get(res.ticker)
            if realized is None:
                continue  # no realized return at this horizon for this stock (n=0 contribution)
            stock_obs.append({
                "run_id": run.id,
                "ticker": res.ticker,
                "return": realized,
                "bucket": res.leadership_bucket,   # stored canonical A-E (verbatim — no re-bucketing)
                "setup": res.setup_status,         # stored canonical setup status (verbatim)
                "sector": res.sector,
                "rank": res.rank,                  # stored canonical rank (verbatim — cohort membership)
            })

        cohorts = _control_groups(horizon, stock_obs, ret_by_run_symbol, runs_with_fr, cfg)
        by_key = {c["key"]: c for c in cohorts}
        cohort = by_key["top_ranked"]
        cohort_mean, cohort_n = cohort["mean_return"], cohort["n"]

        by_horizon.append({
            "horizon": horizon,
            "cohort": {"mean_return": cohort_mean, "n": cohort_n},
            "excess": {
                "vs_spy": _scorecard_excess(cohort_mean, cohort_n, by_key["spy"]),
                "vs_qqq": _scorecard_excess(cohort_mean, cohort_n, by_key["qqq"]),
                "vs_sector": _scorecard_excess(cohort_mean, cohort_n, by_key["sector_etf"]),
            },
            "control_group": cohorts,
        })

    return {
        "asof_date": run.asof_date.isoformat(),
        "min_sample": wf.min_sample,
        "horizons": list(wf.horizons),
        "survivorship_bias": SURVIVORSHIP_BIAS_LABEL,
        "scorecard": {"by_horizon": by_horizon},
    }
