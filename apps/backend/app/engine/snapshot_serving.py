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
from typing import Optional

from fastapi import HTTPException
from sqlmodel import Session, select

from app.config import Config
from app.engine.scanner import AsOfError, resolve_as_of_date, resolve_run
from app.models import ScannerResult, ScannerRun, SectorScoreRow, ThemeScoreRow

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


def stored_stock_rows(session: Session, run: ScannerRun) -> list[dict]:
    """The run's per-stock results rehydrated from `record_json` (the COMPLETE canonical StockRow
    dict), ordered by rank — the SAME rows `/api/stocks` and `/api/stocks/{ticker}` both serve (J-06)."""
    results = session.exec(
        select(ScannerResult).where(ScannerResult.run_id == run.id).order_by(ScannerResult.rank)
    ).all()
    return [json.loads(result.record_json) for result in results]


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


def stocks_payload(session: Session, run: ScannerRun) -> dict:
    """The `/api/stocks` (list) shape, served from the stored run's per-stock results."""
    return {
        "asof_date": run.asof_date.isoformat(),
        "benchmark": run.benchmark,
        "rows": stored_stock_rows(session, run),
    }


def stock_detail_payload(session: Session, run: ScannerRun, ticker: str) -> dict:
    """The `/api/stocks/{ticker}` (detail) shape: the SAME stored row the leaderboard serves (J-06).
    `404` for a ticker absent from this run — never a fabricated row."""
    target = ticker.upper()
    for row in stored_stock_rows(session, run):
        if row["ticker"].upper() == target:
            return {"asof_date": run.asof_date.isoformat(), "benchmark": run.benchmark, "row": row}
    raise HTTPException(status_code=404, detail=f"unknown ticker: {ticker}")


def _sector_row(row: SectorScoreRow) -> dict:
    """Reshape one stored `SectorScoreRow` into the canonical `score_sectors` row dict (verbatim
    columns + the stored component breakdown)."""
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
    }


def sectors_payload(session: Session, run: ScannerRun) -> dict:
    """The `/api/sectors` shape, served from the stored `SectorScoreRow` children (echoing asof_date)."""
    rows = session.exec(
        select(SectorScoreRow).where(SectorScoreRow.run_id == run.id).order_by(SectorScoreRow.rank)
    ).all()
    return {
        "asof_date": run.asof_date.isoformat(),
        "benchmark": run.benchmark,
        "rows": [_sector_row(row) for row in rows],
    }


def _theme_row(row: ThemeScoreRow) -> dict:
    """Reshape one stored `ThemeScoreRow` into the canonical `score_themes` row dict (verbatim columns
    + the stored member list + component breakdown)."""
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
    }


def themes_payload(session: Session, run: ScannerRun) -> dict:
    """The `/api/themes` shape, served from the stored `ThemeScoreRow` children (echoing asof_date)."""
    rows = session.exec(
        select(ThemeScoreRow).where(ThemeScoreRow.run_id == run.id).order_by(ThemeScoreRow.rank)
    ).all()
    return {
        "asof_date": run.asof_date.isoformat(),
        "rows": [_theme_row(row) for row in rows],
    }
