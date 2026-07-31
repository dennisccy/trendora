"""ops-hardening iter-40 (iter-39/w, AG-3 checkpoint honesty) -- builds the THROWAWAY DB for the live
kill -9 + restart checkpoint-cadence drill.

Same lineage as `../wedge-drill/seed_throwaway_db.py` (itself adapted from iter-39's
`runs/goal-ops-hardening-iter-39/mem-drill/seed_throwaway_db.py`): loads the REAL committed seed into a
FRESH, disposable sqlite file, never the live `apps/backend/data/trendora.db`. K is much larger here
(20 trading days, not 3) -- this drill needs a job that runs long enough to `kill -9` it mid-flight with
an independently-tracked "M dates done" checkpoint, not a fast 3-date job that would finish before a
kill could land.

Usage: <venv python> seed_throwaway_db.py <db_path>
Prints a JSON summary line (target dates, seed stats) to stdout for the orchestrating shell.
"""
from __future__ import annotations

import json
import sys
import time

BACKEND_ROOT = "/home/dennis-chan/Git/trendora/apps/backend"
sys.path.insert(0, BACKEND_ROOT)

from sqlmodel import Session  # noqa: E402

from app.config import load_config  # noqa: E402
from app.db import create_db_and_tables, make_engine  # noqa: E402
from app.engine.data_manager import _trading_days  # noqa: E402
from app.seed_loader import load_seed  # noqa: E402

K = 20  # long enough to kill -9 mid-job with room either side
BUFFER_FROM_LATEST = 8  # trading days of buffer before the seed's own latest date (keeps target dates
                         # strictly non-"current", same convention as the wedge-drill fixture)


def main() -> None:
    db_path = sys.argv[1]
    t0 = time.perf_counter()

    engine = make_engine(f"sqlite:///{db_path}")
    create_db_and_tables(engine)
    cfg = load_config()

    load_summary = load_seed(engine, cfg)
    assert load_summary["loaded"], f"expected a fresh throwaway DB to load the seed fresh: {load_summary}"
    seed_elapsed = time.perf_counter() - t0

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

    out = {
        "db_path": db_path,
        "price_rows": load_summary["price_rows"],
        "symbols_ok": load_summary["symbols_ok"],
        "symbols_failed": load_summary["symbols_failed"],
        "seed_load_seconds": round(seed_elapsed, 2),
        "trading_calendar_span": [trading[0].isoformat(), trading[-1].isoformat()],
        "target_start": target_dates[0].isoformat(),
        "target_end": target_dates[-1].isoformat(),
        "k": K,
    }
    print(json.dumps(out))


if __name__ == "__main__":
    main()
