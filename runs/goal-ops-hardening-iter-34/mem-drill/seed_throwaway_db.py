"""ops-hardening iter-34 (J-07 step 4) -- builds a THROWAWAY, synthetic DB for the induced-memory-pressure
drill. Mirrors apps/backend/tests/test_forward_testing_concurrency.py's `_build_memory_pressure_db` shape
(one ScannerRun + high-cardinality ScannerResult/ForwardReturn rows), extended to:

  - cover EVERY configured `walk_forward.horizons` (not just one), since `_refresh_ingest_aggregates`'s
    ingest-finalize loop (the exact mechanism J-07 step 4 must exercise) iterates all of them;
  - carry a SECOND, tiny ScannerRun (R2, a later as-of) with NO pre-seeded ForwardAggregateCache rows, so
    the live throwaway backend process's ingest-finalize hook has a genuine, uncached compute to attempt
    for R2's as-of (which windows over R1+R2 together, `as_of` scoping -- AG-5) -- this is what can
    actually induce memory pressure. R1's own horizons ARE pre-computed+cached (via the real
    `forward_aggregates_ingest_cached`) BEFORE R2 exists, so `GET /api/backtest` can serve R1's stored
    evidence immediately, proving a "previously cached read" survives the drill (TC-4) without depending on
    whether the drill's own compute succeeds or aborts.
  - seed exactly one DailyPrice row for a NON-benchmark symbol (never SPY, `etfs.index[0]`) so
    `POST /api/data/jobs` 's `latest_data_date is not None` gate passes, while `_trading_days` (which reads
    ONLY the benchmark's bars) stays empty -- so ANY backfill request against this throwaway DB is a fast
    0-target no-op that still runs the ingest-finalize hook afterward (`_run_job`'s tail is unconditional on
    `final_status in (ok, partial)`, never on `dates_total > 0`).

Usage: <venv python> seed_throwaway_db.py <db_path> <n_r1_tickers> [n_r2_tickers]
Prints a JSON summary line (run ids, as-of dates, dataset versions) to stdout for the orchestrating shell.
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone

BACKEND_ROOT = "/home/dennis-chan/Git/trendora/apps/backend"
sys.path.insert(0, BACKEND_ROOT)

from sqlalchemy import insert  # noqa: E402
from sqlmodel import Session, select, func  # noqa: E402

from app.config import load_config  # noqa: E402
from app.db import create_db_and_tables, make_engine  # noqa: E402
from app.engine.forward_testing import forward_aggregates_ingest_cached  # noqa: E402
from app.models import DailyPrice, ForwardReturn, ScannerResult, ScannerRun  # noqa: E402

D1 = date(2020, 1, 2)
D2 = date(2020, 1, 3)
RECORD_JSON_BYTES = 4_000  # mirrors the real table's dominant per-row cost (record_json blobs)


def _insert_run_with_results(engine, cfg, asof: date, n_tickers: int, ticker_prefix: str) -> int:
    padding = "x" * RECORD_JSON_BYTES
    with Session(engine) as session:
        run = ScannerRun(
            asof_date=asof, created_at=datetime.now(timezone.utc), provider="seed", benchmark="SPY",
            regime_score=50.0, regime_label=cfg.regime.labels[0], regime_components_json="[]",
            new_high_low_json="{}", candidate_counts_json="{}",
        )
        session.add(run)
        session.flush()
        run_id = run.id
        result_rows = [
            dict(
                run_id=run_id, ticker=f"{ticker_prefix}{i:07d}", name=f"{ticker_prefix}{i:07d}",
                sector="Technology", leadership_score=50.0, leadership_bucket="A",
                entry_quality_score=0.0, entry_quality_bucket="E", risk_score=0.0, risk_bucket="E",
                # NOT "Actionable" (setups.ACTIONABLE) deliberately: subject_catalog(cfg)[0] is the first
                # setup status (ACTIONABLE), and _refresh_ingest_aggregates's research_hot_keys warm calls
                # event_study_cached on EXACTLY that default subject. Actionable rows here would make this
                # throwaway fixture's high-cardinality data double as event-study subject members too,
                # contaminating research_hot_keys's OWN memory footprint and making it (not
                # forward_aggregates) the first thing to hit a tightened cap -- confirmed live (calibration
                # pass 3, this iteration): a MemoryError surfaced in research.py's
                # _event_study_members_by_horizon, caught by research_hot_keys's GENERIC except, not the
                # forward_aggregates-specific iter-8 MemoryError catch this drill must exercise. "Avoid" is
                # a real, valid ALL_STATUSES member that is never subjects[0] -- these rows stay invisible
                # to the default event-study warm while remaining valid ScannerResult data.
                setup_status="Avoid", rank=(i % 500) + 1, record_json=padding, is_vcp=False,
                is_pullback_to_rising_dma=False, is_flat_base_breakout=False,
            )
            for i in range(n_tickers)
        ]
        session.execute(insert(ScannerResult.__table__), result_rows)
        for h in cfg.walk_forward.horizons:
            fr_rows = [
                dict(
                    run_id=run_id, symbol=f"{ticker_prefix}{i:07d}", horizon=h, asof_date=asof,
                    entry_close=100.0, measured_date=asof, realized_return=0.01, max_drawdown=-0.02,
                )
                for i in range(n_tickers)
            ]
            session.execute(insert(ForwardReturn.__table__), fr_rows)
        session.commit()
        return run_id


def main() -> None:
    db_path = sys.argv[1]
    n_r1 = int(sys.argv[2])
    n_r2 = int(sys.argv[3]) if len(sys.argv) > 3 else 3

    engine = make_engine(f"sqlite:///{db_path}")
    create_db_and_tables(engine)
    cfg = load_config()

    # one dummy DailyPrice row -- a NON-benchmark symbol so `latest_data_date` is non-None (passes the
    # `POST /api/data/jobs` 503 gate) while `_trading_days` (benchmark-only) stays empty (any backfill
    # request is a fast 0-target no-op).
    with Session(engine) as session:
        session.add(DailyPrice(
            symbol="ZZZZDRILL", date=D1, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0,
        ))
        session.commit()

    r1_id = _insert_run_with_results(engine, cfg, D1, n_r1, "R1T")

    # dataset_version at THIS point (R1 only) -- computed the SAME way research._dataset_version does,
    # BEFORE R2 exists, so the cache rows persisted below are correctly stamped for R1-only state.
    with Session(engine) as session:
        max_run_id = session.exec(select(func.max(ScannerRun.id))).one()
        fr_count = session.exec(select(func.count()).select_from(ForwardReturn)).one()
    v1 = f"r{max_run_id or 0}-f{fr_count or 0}"

    # pre-compute + persist ALL configured horizons for R1's as-of via the REAL ingest-only cache wrapper
    # (byte-identical to what the ingest-finalize hook itself would produce) -- this is the "previously
    # cached" evidence TC-4 reads back after the drill.
    for h in cfg.walk_forward.horizons:
        with Session(engine) as session:
            forward_aggregates_ingest_cached(session, h, cfg, as_of=D1)

    r2_id = _insert_run_with_results(engine, cfg, D2, n_r2, "R2T")

    with Session(engine) as session:
        max_run_id2 = session.exec(select(func.max(ScannerRun.id))).one()
        fr_count2 = session.exec(select(func.count()).select_from(ForwardReturn)).one()
    v2 = f"r{max_run_id2 or 0}-f{fr_count2 or 0}"

    summary = {
        "db_path": db_path, "r1_id": r1_id, "r1_asof": D1.isoformat(), "r1_n_tickers": n_r1,
        "r1_dataset_version": v1, "r2_id": r2_id, "r2_asof": D2.isoformat(), "r2_n_tickers": n_r2,
        "current_dataset_version": v2, "horizons": list(cfg.walk_forward.horizons),
    }
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
