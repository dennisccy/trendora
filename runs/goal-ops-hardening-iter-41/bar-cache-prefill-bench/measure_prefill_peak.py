"""ops-hardening iter-41 (B6) -- measure `_BarCache.prefill`'s peak RSS/VmPeak, OLD (pre-iter-41,
`list[Bar]` of individually-boxed-float NamedTuples) vs NEW (iter-41 B5, columnar `_SymbolColumns` /
`array.array('d')`), against the live committed-seed DB (`apps/backend/data/trendora.db`).

Each mode runs in its OWN process invocation (this script is called twice, once per mode) so
`/proc/<pid>/status`'s VmPeak/VmHWM reflect ONLY that mode's allocation -- never cross-contaminated by
running both in one process. Read-only (SELECT only, no writes) against the real seed DB -- safe,
AG-9-compliant (no network), and not the kind of induced-pressure/all-core burst AG-10 guards against
(a single serial `.yield_per()`-streamed table scan, the same operation every backfill job already runs
routinely). The OLD mode is a faithful reimplementation of the PRE-iter-41 `_BarCache.prefill` body
(the exact code this iteration replaced -- see `apps/backend/app/engine/prices.py`'s git history at
the iter-40 tree) -- not a second product code path, a benchmark-only reference kept here, never
imported by the shipped app.

Usage: <venv python> measure_prefill_peak.py <db_path> <old|new>
Prints MODE / N_SYMBOLS / N_ROWS / VmPeak / VmHWM / VmRSS / VmSize (kB) to stdout.
"""
from __future__ import annotations

import os
import sys

BACKEND_ROOT = "/home/dennis-chan/Git/trendora/apps/backend"
sys.path.insert(0, BACKEND_ROOT)

from sqlmodel import Session, select  # noqa: E402

from app.config import get_config  # noqa: E402
from app.db import make_engine  # noqa: E402
from app.models import DailyPrice  # noqa: E402


def _old_prefill_peak(engine) -> tuple[int, int]:
    """Verbatim pre-iter-41 `_BarCache.prefill` accumulation body (the code this iteration's B5 fix
    replaced): one `Bar` NamedTuple per row, appended into a plain `list[Bar]` per symbol."""
    from app.engine.prices import Bar

    batch = get_config().research.read_batch_size
    stmt = (
        select(
            DailyPrice.symbol, DailyPrice.date, DailyPrice.open, DailyPrice.high,
            DailyPrice.low, DailyPrice.close, DailyPrice.volume,
        )
        .order_by(DailyPrice.symbol, DailyPrice.date)
    )
    by_symbol: dict[str, list] = {}
    with Session(engine) as session:
        for symbol, d, o, h, lo, c, v in session.exec(stmt).yield_per(batch):
            by_symbol.setdefault(symbol, []).append(Bar(d, o, h, lo, c, v))
    n_symbols = len(by_symbol)
    n_rows = sum(len(v) for v in by_symbol.values())
    return n_symbols, n_rows


def _new_prefill_peak(engine) -> tuple[int, int]:
    """The SHIPPED (iter-41 B5) `_BarCache.prefill` -- the actual product code, unmodified call."""
    from app.engine.prices import _BarCache

    with Session(engine) as session:
        cache = _BarCache()
        cache.prefill(session)
    n_symbols = len(cache._by_symbol)
    n_rows = sum(len(v) for v in cache._by_symbol.values())
    return n_symbols, n_rows


def main() -> None:
    db_path = sys.argv[1]
    mode = sys.argv[2]
    engine = make_engine(f"sqlite:///{db_path}")

    if mode == "old":
        n_symbols, n_rows = _old_prefill_peak(engine)
    elif mode == "new":
        n_symbols, n_rows = _new_prefill_peak(engine)
    else:
        raise SystemExit(f"unknown mode {mode!r} -- expected 'old' or 'new'")

    with open(f"/proc/{os.getpid()}/status") as fh:
        status = {}
        for line in fh:
            if ":" in line:
                k, v = line.split(":", 1)
                status[k.strip()] = v.strip()

    print(f"MODE={mode}")
    print(f"N_SYMBOLS={n_symbols}")
    print(f"N_ROWS={n_rows}")
    for field in ("VmPeak", "VmHWM", "VmRSS", "VmSize"):
        print(f"{field}={status.get(field, '?')}")


if __name__ == "__main__":
    main()
