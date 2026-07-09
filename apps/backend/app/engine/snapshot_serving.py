"""Snapshot-served read path (iter-8, J-15 + J-13).

Reshapes a resolved IMMUTABLE `ScannerRun` + its stored children into the EXACT existing API payloads
(`dashboard` / `stocks` / `stock_detail` / `sectors` / `themes`) and translates as-of resolution
errors into explicit HTTP responses. NO score / regime / sector / theme / return is recomputed here
(anti-goals: No recompute in the read path + Single source of truth): every served value is read from
the snapshot rows that the one `run_scan` persisted once. Because `run_scan` stored faithful copies of
the canonical engine outputs, these reshaped payloads are byte-identical to the live engine outputs for
the latest date (the iter-5 faithful-equality guarantee) — so re-pointing the read path changes only
WHERE the values come from (storage), never WHAT they are. Per-stock rows are rehydrated from the
lossless `record_json`, so the leaderboard list row and the detail row are byte-identical (J-06).

This module is the API-facing serving layer (it knows about HTTP); the pure resolver lives in
`app.engine.scanner` (it raises a semantic `AsOfError`, free of any status-code literal).
"""
from __future__ import annotations

import json
from datetime import date as date_cls
from typing import Iterable, Optional

from fastapi import HTTPException
from sqlalchemy import func
from sqlmodel import Session, select

from app.config import Config, get_config
from app.engine.forward_testing import _leadership_returns
from app.engine.scanner import AsOfError, resolve_as_of_date, resolve_run
from app.models import ForwardReturn, ScannerResult, ScannerRun, SectorScoreRow, ThemeScoreRow

# Semantic resolution failure -> explicit HTTP status (no fabrication; the API surfaces an honest 4xx).
_STATUS_BY_KIND = {"no_data": 503, "unparseable": 422, "future": 400, "before_history": 400}


def _http(exc: AsOfError) -> HTTPException:
    return HTTPException(status_code=_STATUS_BY_KIND.get(exc.kind, 400), detail=exc.detail)


def resolved_run(session: Session, as_of: Optional[str], config: Optional[Config] = None) -> ScannerRun:
    """`scanner.resolve_run`, with `AsOfError` translated to an explicit HTTP 4xx/503."""
    try:
        return resolve_run(session, as_of, config)
    except AsOfError as exc:
        raise _http(exc)


def resolved_date(session: Session, as_of: Optional[str], config: Optional[Config] = None) -> date_cls:
    """`scanner.resolve_as_of_date`, with `AsOfError` translated to an explicit HTTP 4xx/503. Used by
    `/bars`, which needs only the validated as-of date (raw bars are not a recomputed score, so they
    require no snapshot row — only the as-of slice + no-lookahead)."""
    try:
        return resolve_as_of_date(session, as_of, config)
    except AsOfError as exc:
        raise _http(exc)


def _forward_returns_by_symbol(
    session: Session, run: ScannerRun, config: Optional[Config] = None
) -> dict[str, dict[int, dict]]:
    """`symbol -> {horizon: {"return": realized_return, "max_drawdown": max_drawdown}}` for THIS run, read
    VERBATIM from the stored append-only `forward_returns` table (J-75 + J-86). The SAME stored rows the
    Backtest scorecard (J-21) reads — keyed by `run_id` + `symbol` + `horizon` — so the leaderboard /
    detail / Backtest forward returns are one single source (J-06-style coherence). It RECOMPUTES no
    return / drawdown: a single SELECT against `ForwardReturn` for the run, grouped into a per-symbol
    horizon map. A (symbol, horizon) with no stored row is simply absent from the inner map (the caller
    renders NA — never a fabricated number; no-lookahead is intrinsic to the stored rows, which only ever
    measure bars dated > D)."""
    rows = session.exec(
        select(ForwardReturn).where(ForwardReturn.run_id == run.id)
    ).all()
    by_symbol: dict[str, dict[int, dict]] = {}
    for fr in rows:
        # iter-27 (J-86): carry the stored max_drawdown beside the stored realized_return — both read
        # VERBATIM (no recompute). An older row predating the column reads max_drawdown=None (honest NA).
        by_symbol.setdefault(fr.symbol, {})[fr.horizon] = {
            "return": fr.realized_return,
            "max_drawdown": fr.max_drawdown,
        }
    return by_symbol


def _forward_returns_for_row(
    symbol: str, by_symbol: dict[str, dict[int, dict]], horizons: list[int]
) -> list[dict]:
    """The ADDITIVE per-stock forward-return list for ONE ticker (J-75 + J-86): one entry per CONFIGURED
    horizon (`config.walk_forward.horizons` — NO hardcoded `[1,5,10,20,60]` literal), each
    `{horizon, return, max_drawdown}` where `return` is the stored `realized_return` and `max_drawdown`
    is the stored max-drawdown, BOTH read verbatim, or `None` (NA) when no stored row exists for that
    (run, symbol, horizon) — so at/near the latest date all are honestly NA, never fabricated. The
    horizons are emitted in config order so the leaderboard columns map to them; `max_drawdown` is paired
    to each `return` so a row's drawdown is NA exactly when its return is."""
    horizon_map = by_symbol.get(symbol.upper(), {}) or by_symbol.get(symbol, {})
    return [
        {
            "horizon": h,
            "return": horizon_map.get(h, {}).get("return") if h in horizon_map else None,
            "max_drawdown": horizon_map.get(h, {}).get("max_drawdown") if h in horizon_map else None,
        }
        for h in horizons
    ]


def _leadership_returns_by_horizon(
    session: Session, run: ScannerRun, cfg: Config
) -> dict[int, dict]:
    """The J-21 `forward_testing:_leadership_returns` projection for THIS run, computed ONCE per CONFIGURED
    horizon (J-81). For each horizon it builds `ret_by_symbol` (symbol -> the stored `realized_return` for
    this run+horizon) from the SINGLE `forward_returns` SELECT and calls the SAME `_leadership_returns`
    builder Backtest's Top Themes / Top Sectors already use — so a theme's / sector's forward return on the
    leaderboard is BYTE-IDENTICAL to Backtest's for the same date+horizon (J-06 single-source). It reads
    VERBATIM from the stored append-only `forward_returns` table and recomputes NO return; absent members
    are skipped (never counted as 0), `None`/NA when no member / no stored row.

    Returns `{horizon: {"themes": {slug: {return, max_drawdown}}, "sectors": {sector_etf: {return,
    max_drawdown}}}}` — the per-horizon projection indexed for O(1) per-row lookup, so neither
    `themes_payload` nor `sectors_payload` issues a second query per horizon per row (one SELECT total for
    the run). iter-27 (J-86): each projected row ADDITIVELY carries `max_drawdown` (theme = equal-weight
    member-basket drawdown; sector = the ETF's own drawdown) read VERBATIM via the SAME `_leadership_returns`
    builder Backtest uses — recomputes nothing."""
    fr_rows = session.exec(
        select(ForwardReturn).where(ForwardReturn.run_id == run.id)
    ).all()
    by_horizon: dict[int, dict] = {}
    for horizon in cfg.walk_forward.horizons:
        ret_by_symbol = {fr.symbol: fr.realized_return for fr in fr_rows if fr.horizon == horizon}
        # iter-27 (J-86): the SAME stored rows' max_drawdown, read verbatim — passed to the SAME builder so
        # the leaderboard MDD is byte-identical to Backtest's for the same date+horizon (J-06).
        mdd_by_symbol = {fr.symbol: fr.max_drawdown for fr in fr_rows if fr.horizon == horizon}
        proj = _leadership_returns(ret_by_symbol, cfg, mdd_by_symbol)  # SAME builder Backtest reads (J-06)
        by_horizon[horizon] = {
            "themes": {t["slug"]: {"return": t["mean_return"], "max_drawdown": t["max_drawdown"]} for t in proj["themes"]},
            "sectors": {s["sector_etf"]: {"return": s["mean_return"], "max_drawdown": s["max_drawdown"]} for s in proj["sectors"]},
        }
    return by_horizon


def _forward_returns_from_projection(
    key: str, dimension: str, leadership_by_horizon: dict[int, dict], horizons: list[int]
) -> list[dict]:
    """The ADDITIVE per-row forward-return list for ONE theme (`dimension="themes"`, `key`=slug) or ONE
    sector/industry ETF (`dimension="sectors"`, `key`=ticker) — one entry per CONFIGURED horizon
    (`config.walk_forward.horizons` — NO hardcoded `[1,5,10,20,60]` literal), each
    `{horizon, return, max_drawdown}` where `return` is the `_leadership_returns` projection value read
    verbatim (theme = equal-weight member basket; sector = the ETF's own stored return) and `max_drawdown`
    is the paired projected drawdown (J-86), or `None` (NA) when no stored value — so at/near latest all
    are honestly NA, never fabricated (J-81)."""
    return [
        {
            "horizon": h,
            "return": leadership_by_horizon[h][dimension].get(key, {}).get("return"),
            "max_drawdown": leadership_by_horizon[h][dimension].get(key, {}).get("max_drawdown"),
        }
        for h in horizons
    ]


def stored_stock_rows(
    session: Session, run: ScannerRun, config: Optional[Config] = None
) -> list[dict]:
    """The run's per-stock results rehydrated from `record_json` (the COMPLETE canonical StockRow
    dict), ordered by rank — the SAME rows `/api/stocks` and `/api/stocks/{ticker}` both serve (J-06).

    J-75: each row ADDITIVELY carries `forward_returns` — its FIVE realized forward returns
    (1/5/10/20/60-day, from `config.walk_forward.horizons`) read VERBATIM from the stored
    `forward_returns` table for this run (NA where no stored row). This is a pure read of stored data
    attached to the served row — it recomputes NO score / return / bucket, so the leaderboard list row
    and the detail row stay byte-identical (J-06) and match the Backtest forward returns (J-21)."""
    cfg = config or get_config()
    horizons = list(cfg.walk_forward.horizons)
    results = session.exec(
        select(ScannerResult).where(ScannerResult.run_id == run.id).order_by(ScannerResult.rank)
    ).all()
    by_symbol = _forward_returns_by_symbol(session, run, cfg)
    rows: list[dict] = []
    for result in results:
        row = json.loads(result.record_json)
        # ADDITIVE J-75 field — read verbatim from the stored forward_returns; never recomputed here.
        row["forward_returns"] = _forward_returns_for_row(row["ticker"], by_symbol, horizons)
        rows.append(row)
    return rows


def dashboard_payload(run: ScannerRun) -> dict:
    """The `/api/dashboard` shape, served from the stored run: regime panel, universe-relative breadth,
    and the STORED candidate counts (read from `candidate_counts_json`, never re-derived)."""
    return {
        "regime": {
            "score": run.regime_score,
            "label": run.regime_label,
            "components": json.loads(run.regime_components_json),
            "asof_date": run.asof_date.isoformat(),
        },
        "breadth": {
            "above_50dma_pct": run.breadth_above_50dma,
            "above_200dma_pct": run.breadth_above_200dma,
            "new_high_low": json.loads(run.new_high_low_json),
            "label": "universe-relative",
        },
        "asof_date": run.asof_date.isoformat(),
        "candidate_counts": json.loads(run.candidate_counts_json),
    }


def stocks_payload(session: Session, run: ScannerRun, config: Optional[Config] = None) -> dict:
    """The `/api/stocks` (list) shape, served from the stored run's per-stock results (each row carrying
    its stored forward returns, J-75)."""
    return {
        "asof_date": run.asof_date.isoformat(),
        "benchmark": run.benchmark,
        "rows": stored_stock_rows(session, run, config),
    }


def filtered_stock_rows(
    session: Session, run: ScannerRun, tickers: Iterable[str], config: Optional[Config] = None
) -> list[dict]:
    """Item D (iter-24 fast-platform pass) — the SAME row shape `stored_stock_rows` serves (record_json
    rehydration + the J-75 stored `forward_returns` attachment), scoped to an explicit ticker set via an
    indexed `ScannerResult.ticker` filter, instead of `json.loads`-ing every one of the run's ~400+
    `record_json` blobs to return a handful. Matches case-insensitively (mirrors `stock_detail_payload`'s
    former `.upper()` comparison, so a URL-cased ticker like `nvda` still resolves) by comparing uppercased
    tickers on both sides; `tickers` may be given in any case. Ordered by rank — the SAME order
    `stored_stock_rows` yields, so a caller taking the first match preserves prior tie-break behavior.
    Recomputes nothing; byte-identical payload shape to the full-scan path for the same rows."""
    cfg = config or get_config()
    horizons = list(cfg.walk_forward.horizons)
    wanted = {t.upper() for t in tickers if t}
    if not wanted:
        return []
    results = session.exec(
        select(ScannerResult)
        .where(ScannerResult.run_id == run.id, func.upper(ScannerResult.ticker).in_(wanted))
        .order_by(ScannerResult.rank)
    ).all()
    by_symbol = _forward_returns_by_symbol(session, run, cfg)
    rows: list[dict] = []
    for result in results:
        row = json.loads(result.record_json)
        row["forward_returns"] = _forward_returns_for_row(row["ticker"], by_symbol, horizons)
        rows.append(row)
    return rows


def stock_detail_payload(
    session: Session, run: ScannerRun, ticker: str, config: Optional[Config] = None
) -> dict:
    """The `/api/stocks/{ticker}` (detail) shape: the SAME stored row the leaderboard serves (J-06),
    carrying the SAME stored forward returns (J-75). `404` for a ticker absent from this run — never a
    fabricated row. Item D: uses the ticker-filtered fetch (one indexed query for this run + ticker)
    instead of deserializing every row in the run to find one."""
    rows = filtered_stock_rows(session, run, [ticker], config)
    if rows:
        return {"asof_date": run.asof_date.isoformat(), "benchmark": run.benchmark, "row": rows[0]}
    raise HTTPException(status_code=404, detail=f"unknown ticker: {ticker}")


def _sector_row(row: SectorScoreRow, forward_returns: list[dict]) -> dict:
    """Reshape one stored `SectorScoreRow` into the canonical `score_sectors` row dict (verbatim
    columns + the stored component breakdown), ADDITIVELY carrying its five stored forward returns
    (J-81 — the ETF's OWN realized return per horizon, read verbatim via `_leadership_returns`)."""
    return {
        "ticker": row.ticker,
        "kind": row.kind,
        "name": row.name,
        # J-58: config reference metadata echoed VERBATIM from the stored immutable snapshot row —
        # never recomputed here. A stored run predating the columns has description=NULL / an empty
        # members list (the `or "[]"` guard makes a legacy NULL render the honest empty state).
        "description": row.description,
        "members": json.loads(row.members_json or "[]"),
        "score": row.score,
        "bucket": row.bucket,
        "rs_vs_spy": row.rs_vs_spy,
        "dist_from_52w_high_pct": row.dist_from_52w_high_pct,
        "trend_label": row.trend_label,
        "components": json.loads(row.components_json),
        "rank": row.rank,
        # ADDITIVE J-81 field — the ETF's own stored forward return per horizon, read verbatim from the
        # `_leadership_returns` projection (the SAME value Backtest's Top Sectors shows); NA where no row.
        "forward_returns": forward_returns,
    }


def sectors_payload(session: Session, run: ScannerRun, config: Optional[Config] = None) -> dict:
    """The `/api/sectors` shape, served from the stored `SectorScoreRow` children (echoing asof_date).

    J-81: each ETF row ADDITIVELY carries `forward_returns` — its five realized forward returns
    (1/5/10/20/60-day, from `config.walk_forward.horizons`) read VERBATIM via the SAME
    `forward_testing:_leadership_returns` builder Backtest's Top Sectors uses (sector = the ETF's OWN
    stored return), so a sector forward return reads identically on its leaderboard and on Backtest for
    the same date+horizon (J-06). Recomputes NO return; one `forward_returns` SELECT for the whole run."""
    cfg = config or get_config()
    horizons = list(cfg.walk_forward.horizons)
    leadership_by_horizon = _leadership_returns_by_horizon(session, run, cfg)
    rows = session.exec(
        select(SectorScoreRow).where(SectorScoreRow.run_id == run.id).order_by(SectorScoreRow.rank)
    ).all()
    return {
        "asof_date": run.asof_date.isoformat(),
        "benchmark": run.benchmark,
        "rows": [
            _sector_row(
                row,
                _forward_returns_from_projection(row.ticker, "sectors", leadership_by_horizon, horizons),
            )
            for row in rows
        ],
    }


def _theme_row(row: ThemeScoreRow, forward_returns: list[dict]) -> dict:
    """Reshape one stored `ThemeScoreRow` into the canonical `score_themes` row dict (verbatim columns
    + the stored member list + component breakdown), ADDITIVELY carrying its five stored forward returns
    (J-81 — the EQUAL-WEIGHT member-basket realized return per horizon, read verbatim via
    `_leadership_returns`)."""
    return {
        "slug": row.slug,
        "name": row.name,
        "score": row.score,
        "bucket": row.bucket,
        "members": json.loads(row.members_json),
        "return_1m": row.return_1m,
        "return_3m": row.return_3m,
        "breadth_pct": row.breadth_pct,
        "breadth_label": row.breadth_label,
        "trend_label": row.trend_label,
        "components": json.loads(row.components_json),
        "rank": row.rank,
        # ADDITIVE J-81 field — the equal-weight member-basket stored forward return per horizon, read
        # verbatim from the `_leadership_returns` projection (the SAME value Backtest's Top Themes shows);
        # absent members skipped (never 0), NA where no member has a stored return.
        "forward_returns": forward_returns,
    }


def themes_payload(session: Session, run: ScannerRun, config: Optional[Config] = None) -> dict:
    """The `/api/themes` shape, served from the stored `ThemeScoreRow` children (echoing asof_date).

    J-81: each theme row ADDITIVELY carries `forward_returns` — its five realized forward returns
    (1/5/10/20/60-day, from `config.walk_forward.horizons`) read VERBATIM via the SAME
    `forward_testing:_leadership_returns` builder Backtest's Top Themes uses (theme = the EQUAL-WEIGHT mean
    of its member stocks' stored returns over only members that HAVE a stored return), so a theme forward
    return reads identically on its leaderboard and on Backtest for the same date+horizon (J-06).
    Recomputes NO return; one `forward_returns` SELECT for the whole run."""
    cfg = config or get_config()
    horizons = list(cfg.walk_forward.horizons)
    leadership_by_horizon = _leadership_returns_by_horizon(session, run, cfg)
    rows = session.exec(
        select(ThemeScoreRow).where(ThemeScoreRow.run_id == run.id).order_by(ThemeScoreRow.rank)
    ).all()
    return {
        "asof_date": run.asof_date.isoformat(),
        "rows": [
            _theme_row(
                row,
                _forward_returns_from_projection(row.slug, "themes", leadership_by_horizon, horizons),
            )
            for row in rows
        ],
    }
