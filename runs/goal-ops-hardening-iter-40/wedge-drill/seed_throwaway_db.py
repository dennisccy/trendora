"""ops-hardening iter-40 (J-07 last blocker post-fix re-check) -- builds the THROWAWAY DB for the
tightened-cap wedge-recurrence drill.

Adapted VERBATIM in structure from iter-39's own `runs/goal-ops-hardening-iter-39/mem-drill/
seed_throwaway_db.py`: loads the REAL committed seed (`load_seed` -- the same ~590-symbol, 30-year price
history every other test module's fixture already uses) into a FRESH, disposable sqlite file, never the
live `apps/backend/data/trendora.db`, so the shared bar-cache prefill this drill exercises carries
REALISTIC weight (comparable to the live basis' own documented figures in `reports/perf-budgets.md`).

Extends iter-38's fixture with the iter-34 lesson (still applicable): bulk-relabel EVERY
`ScannerResult.setup_status` to "Avoid" so `_refresh_ingest_aggregates`'s `research_hot_keys` warm call
pools an EMPTY cohort on this throwaway DB instead of a real, potentially high-cardinality one, keeping the
drill's cost dominated by the coverage diagnostic step this iteration's fix targets (not masked by a
research_hot_keys MemoryError under its own generic `except Exception`).

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

K = 3  # J-07 DoD: "dates_total >= 3" -- matches iter-39 trial 3's own K exactly, same window shape
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
