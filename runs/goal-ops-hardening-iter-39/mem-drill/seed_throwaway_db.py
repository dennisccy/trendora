"""ops-hardening iter-39 (J-07 step 4) -- builds the THROWAWAY DB for the induced-pressure drill.

Same lineage as iter-38's own `runs/goal-ops-hardening-iter-38/mem-drill/seed_throwaway_db.py`: loads the
REAL committed seed (`load_seed` -- the same ~590-symbol, 30-year price history every other test module's
fixture already uses) into a FRESH, disposable sqlite file, never the live `apps/backend/data/trendora.db`,
so the shared bar-cache prefill this drill exercises carries REALISTIC weight (comparable to the live
basis' own documented figures in `reports/perf-budgets.md`) -- a near-empty synthetic stub would make the
prefill stage trivial regardless of the memory cap, which is exactly the wrong shape for THIS step: the
whole point is a cap tuned so prefill completes but the LATER aggregate-warm stage does not.

Extends iter-38's fixture with the iter-34 lesson this iteration's plan calls out explicitly: bulk-relabel
EVERY `ScannerResult.setup_status` to "Avoid" (a real, valid `ALL_STATUSES` member that subject_catalog(cfg)
never puts at index 0 -- see setups.py's `ALL_STATUSES` ordering) so `_refresh_ingest_aggregates`'s
`research_hot_keys` warm call -- which runs `event_study_cached` on subject `ALL_STATUSES[0]` ("Actionable")
by default -- pools an EMPTY cohort on this throwaway DB instead of a real, potentially high-cardinality
one. iter-34's own fixture docstring records why this matters: on a calibration pass where "Actionable" rows
existed, a MemoryError surfaced inside `research.py`'s `_event_study_members_by_horizon`, caught by
`research_hot_keys`'s GENERIC `except Exception` (not the forward_aggregates-/drawdown_expectations-
specific iter-8 MemoryError catches this drill must exercise), masking the target. Relabeling is a bulk SQL
UPDATE after `load_seed()` -- forward_aggregates/drawdown_expectations do not filter by setup_status, so
this only shrinks research_hot_keys' own footprint, nothing else this drill measures.

A K>=3-trading-day window comfortably BEFORE the seed's own latest trading day is picked as the backfill
target (mirrors iter-38's own buffer reasoning: `_persist_per_date_coverage_snapshots`'s `todo` filter skips
whichever date equals "current", already persisted by the direct `refresh_coverage_snapshot` call that runs
just before it in `_refresh_ingest_aggregates` -- picking a non-current window keeps all K dates inside that
loop's own per-date warm).

Usage: <venv python> seed_throwaway_db.py <db_path>
Prints a JSON summary line (target dates, seed stats, relabeled-row count) to stdout for the orchestrating
shell.
"""
from __future__ import annotations

import json
import sys
import time

BACKEND_ROOT = "/home/dennis-chan/Git/trendora/apps/backend"
sys.path.insert(0, BACKEND_ROOT)

from sqlalchemy import text  # noqa: E402
from sqlmodel import Session  # noqa: E402

from app.config import load_config  # noqa: E402
from app.db import create_db_and_tables, make_engine  # noqa: E402
from app.engine.data_manager import _trading_days  # noqa: E402
from app.seed_loader import load_seed  # noqa: E402

K = 3  # J-07 DoD: "dates_total >= 3"
BUFFER_FROM_LATEST = 8  # trading days of buffer before the seed's own latest date -- keeps every target
                         # date strictly non-"current" (see module docstring)


def main() -> None:
    db_path = sys.argv[1]
    t0 = time.perf_counter()

    engine = make_engine(f"sqlite:///{db_path}")
    create_db_and_tables(engine)
    cfg = load_config()

    load_summary = load_seed(engine, cfg)
    assert load_summary["loaded"], f"expected a fresh throwaway DB to load the seed fresh: {load_summary}"
    seed_elapsed = time.perf_counter() - t0

    # iter-34 lesson (see module docstring): relabel EVERY scanner_results row to "Avoid" so the
    # research_hot_keys default subject ("Actionable") pools an empty cohort on this throwaway DB.
    with Session(engine) as session:
        result = session.exec(text("UPDATE scanner_results SET setup_status = 'Avoid'"))
        relabeled = result.rowcount
        session.commit()

    with Session(engine) as session:
        trading = _trading_days(session, cfg)
    assert len(trading) > (BUFFER_FROM_LATEST + K), (
        f"seed should provide a long trading calendar, got {len(trading)} days"
    )

    end_idx = len(trading) - 1 - BUFFER_FROM_LATEST
    start_idx = end_idx - (K - 1)
    target_dates = trading[start_idx : end_idx + 1]
    assert len(target_dates) == K
    assert trading[-1] not in target_dates, "sanity: target dates must exclude the resolved 'current' as-of"

    latest_asof = trading[-1]

    out = {
        "db_path": db_path,
        "price_rows": load_summary["price_rows"],
        "symbols_ok": load_summary["symbols_ok"],
        "symbols_failed": load_summary["symbols_failed"],
        "seed_load_seconds": round(seed_elapsed, 2),
        "scanner_results_relabeled_to_avoid": relabeled,
        "trading_calendar_span": [trading[0].isoformat(), trading[-1].isoformat()],
        "trading_calendar_days": len(trading),
        "latest_asof": latest_asof.isoformat(),
        "target_start": target_dates[0].isoformat(),
        "target_end": target_dates[-1].isoformat(),
        "target_dates": [d.isoformat() for d in target_dates],
        "k": K,
    }
    print(json.dumps(out))


if __name__ == "__main__":
    main()
