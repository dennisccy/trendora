"""GET /api/runs (+ /{run_id}) — the immutable as-of scanner-run history (Data Contract:
app.engine.scanner). Serves the STORED snapshot rows ONLY — it NEVER calls the live `score_*`
engines for a historical run (that would show today's numbers for an old date, the exact
immutability bug J-08 guards against). The per-stock rows are rehydrated from `record_json`, so a
run-detail row is the SAME canonical `StockRow` shape the leaderboard serves.

`404` for an unknown `run_id` (no fabricated run); `503` when no price data exists — never a
fabricated row (anti-goal: No fabricated data).
"""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlmodel import Session, select

from app.db import get_session
from app.engine.prices import latest_data_date
from app.models import ScannerResult, ScannerRun

router = APIRouter(tags=["runs"])


@router.get("/runs")
def runs(session: Session = Depends(get_session)) -> dict:
    """List persisted runs, descending by as-of date, each with its regime label/score, stored
    candidate counts, and stock count — so the Risk-Off row is identifiable and the history is dated.

    ops-hardening iter-56 (J-06 closure): `n_stocks` for EVERY run is read from ONE grouped aggregate
    query (`GROUP BY ScannerResult.run_id`) instead of one `COUNT` query issued PER stored run inside
    the loop — the confirmed N+1 pattern this iteration's live profiling measured issuing one query per
    of the DB's 2,937 `scanner_runs` rows (6.8-10.7s against the committed <=1.5s budget,
    `reports/perf-budgets.md` Addendum 18/20). Same endpoint, same response shape, byte-identical
    `n_stocks` per run — no second producer; a run with zero stored results is honestly `0` (absent from
    the grouped result, defaulted below), exactly as the old per-run `COUNT` returned `0` for it."""
    if latest_data_date(session) is None:
        raise HTTPException(status_code=503, detail="no price data available")
    run_rows = session.exec(select(ScannerRun).order_by(ScannerRun.asof_date.desc())).all()
    counts_by_run_id = dict(
        session.exec(
            select(ScannerResult.run_id, func.count())
            .select_from(ScannerResult)
            .group_by(ScannerResult.run_id)
        ).all()
    )
    out = []
    for run in run_rows:
        out.append(
            {
                "run_id": run.id,
                "asof_date": run.asof_date.isoformat(),
                "created_at": run.created_at.isoformat(),
                "regime": {"label": run.regime_label, "score": run.regime_score},
                "candidate_counts": json.loads(run.candidate_counts_json),
                "n_stocks": int(counts_by_run_id.get(run.id, 0) or 0),
            }
        )
    return {"runs": out}


@router.get("/runs/{run_id}")
def run_detail(run_id: int, session: Session = Depends(get_session)) -> dict:
    """One run's full STORED snapshot: its regime panel (label + score + components, as-of that
    date), universe-relative breadth, candidate counts, and the ranked stored stock results
    (rehydrated from `record_json` into the canonical `StockRow` shape). Reads STORED rows only —
    never the live engine."""
    if latest_data_date(session) is None:
        raise HTTPException(status_code=503, detail="no price data available")
    run = session.get(ScannerRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"unknown run: {run_id}")
    results = session.exec(
        select(ScannerResult).where(ScannerResult.run_id == run_id).order_by(ScannerResult.rank)
    ).all()
    rows = [json.loads(result.record_json) for result in results]  # stored canonical rows verbatim
    return {
        "run_id": run.id,
        "asof_date": run.asof_date.isoformat(),
        "created_at": run.created_at.isoformat(),
        "provider": run.provider,
        "benchmark": run.benchmark,
        "regime": {
            "label": run.regime_label,
            "score": run.regime_score,
            "components": json.loads(run.regime_components_json),
            "asof_date": run.asof_date.isoformat(),
        },
        "breadth": {
            "above_50dma_pct": run.breadth_above_50dma,
            "above_200dma_pct": run.breadth_above_200dma,
            "new_high_low": json.loads(run.new_high_low_json),
            "label": "universe-relative",
        },
        "candidate_counts": json.loads(run.candidate_counts_json),
        "rows": rows,
    }
