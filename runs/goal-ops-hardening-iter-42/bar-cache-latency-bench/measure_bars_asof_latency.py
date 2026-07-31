"""ops-hardening iter-42 (T2/TC-10) -- a before/after latency figure for representative
`bars_asof`/`bars_asof_window` reads over `_SymbolColumns` (iter-41's B5 columnar accumulator) vs.
the pre-iter-41 `list[Bar]` baseline. iter-41's own audit (T2) flagged that no such figure was ever
measured -- the iteration shipped the memory-bound columnar rewrite with only a VmPeak comparison,
never confirming the read path it changes (every `bars_asof`/`bars_asof_window` call, the hottest
read in the engine) did not get slower in exchange for the memory win.

Both arms are built from the SAME live seed rows (`apps/backend/data/trendora.db`) so the comparison
is apples-to-apples:
  - OLD: a faithful reimplementation of the pre-iter-41 accumulation body (list[Bar] per symbol --
    the exact shape `test_bar_cache.py::_old_prefill_by_symbol` and iter-41's own bench script use),
    wired directly into a `_BarCache` instance (bypassing `prefill()`'s loading mechanism -- only the
    RESULTING data-structure shape under test, not how it got there).
  - NEW: the shipped `_BarCache.prefill(expected_symbols=pool_symbols)` -- the actual product code,
    unmodified call, producing `_SymbolColumns` per symbol.

Both arms then time the SAME representative (symbol, as-of-date) sample through `bars_asof` and
`bars_asof_window` (lookback=200, the same order of magnitude `cfg.indicators.max_lookback_bars`
uses), repeated many times so per-call microsecond timing is stable against measurement noise.

Usage: <venv python> measure_bars_asof_latency.py <db_path>
Prints OLD/NEW per-call microsecond timings for both accessors to stdout.
"""
from __future__ import annotations

import random
import sys
import time

BACKEND_ROOT = "/home/dennis-chan/Git/trendora/apps/backend"
sys.path.insert(0, BACKEND_ROOT)

from sqlmodel import Session, select  # noqa: E402

from app.config import get_config  # noqa: E402
from app.db import make_engine  # noqa: E402
from app.engine.prices import Bar, _BarCache  # noqa: E402
from app.engine.universe_screen import read_pool  # noqa: E402
from app.models import DailyPrice  # noqa: E402


def _old_by_symbol(session) -> dict[str, list]:
    """Verbatim pre-iter-41 `_BarCache.prefill` accumulation body (mirrors
    `test_bar_cache.py::_old_prefill_by_symbol` and iter-41's own bench script's `_old_prefill_peak`):
    one `Bar` NamedTuple per row, appended into a plain `list[Bar]` per symbol."""
    batch = get_config().research.read_batch_size
    stmt = (
        select(
            DailyPrice.symbol, DailyPrice.date, DailyPrice.open, DailyPrice.high,
            DailyPrice.low, DailyPrice.close, DailyPrice.volume,
        )
        .order_by(DailyPrice.symbol, DailyPrice.date)
    )
    by_symbol: dict[str, list] = {}
    for symbol, d, o, h, lo, c, v in session.exec(stmt).yield_per(batch):
        by_symbol.setdefault(symbol, []).append(Bar(d, o, h, lo, c, v))
    return by_symbol


def _bench(cache: _BarCache, session, samples, lookback: int, reps: int) -> tuple[float, float]:
    t0 = time.perf_counter()
    for _ in range(reps):
        for symbol, d in samples:
            cache.bars_asof(session, symbol, d)
    t_asof = time.perf_counter() - t0

    t0 = time.perf_counter()
    for _ in range(reps):
        for symbol, d in samples:
            cache.bars_asof_window(session, symbol, d, lookback)
    t_window = time.perf_counter() - t0
    return t_asof, t_window


def main() -> None:
    db_path = sys.argv[1]
    engine = make_engine(f"sqlite:///{db_path}")
    pool_symbols = sorted({row["symbol"] for row in read_pool()})

    with Session(engine) as old_session:
        old_by_symbol = _old_by_symbol(old_session)

    old_cache = _BarCache()
    old_cache._by_symbol = old_by_symbol
    old_cache._dates_by_symbol = {s: [b.date for b in bars] for s, bars in old_by_symbol.items()}
    old_cache._prefilled = True

    new_session = Session(engine)
    new_cache = _BarCache()
    new_cache.prefill(new_session, expected_symbols=set(pool_symbols))

    # Representative sample: 50 pool symbols with substantial history, each read at its OWN latest
    # bar date (a late as-of, the common hot-path shape — regime/breadth/52-week-high reads near the
    # current as-of, not the symbol's first bar).
    random.seed(42)
    candidates = [s for s in pool_symbols if s in old_by_symbol and len(old_by_symbol[s]) > 300]
    sample_symbols = random.sample(candidates, min(50, len(candidates)))
    samples = [(s, old_by_symbol[s][-1].date) for s in sample_symbols]

    lookback = 200  # same order of magnitude as cfg.indicators.max_lookback_bars
    reps = 200
    n_calls = len(samples) * reps

    old_asof, old_window = _bench(old_cache, old_session, samples, lookback, reps)
    new_asof, new_window = _bench(new_cache, new_session, samples, lookback, reps)
    new_session.close()

    print(f"N_SAMPLES={len(samples)}")
    print(f"REPS={reps}")
    print(f"N_CALLS_PER_METRIC={n_calls}")
    print(f"OLD_bars_asof_total_s={old_asof:.6f}")
    print(f"OLD_bars_asof_per_call_us={old_asof / n_calls * 1e6:.3f}")
    print(f"NEW_bars_asof_total_s={new_asof:.6f}")
    print(f"NEW_bars_asof_per_call_us={new_asof / n_calls * 1e6:.3f}")
    print(f"OLD_bars_asof_window_total_s={old_window:.6f}")
    print(f"OLD_bars_asof_window_per_call_us={old_window / n_calls * 1e6:.3f}")
    print(f"NEW_bars_asof_window_total_s={new_window:.6f}")
    print(f"NEW_bars_asof_window_per_call_us={new_window / n_calls * 1e6:.3f}")


if __name__ == "__main__":
    main()
