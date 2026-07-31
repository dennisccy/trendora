"""ops-hardening iter-42 (bound attempt #5, TC-6/TC-7) -- measure `_BarCache.prefill`'s peak RSS/
VmPeak, SUBSET (`expected_symbols=pool_symbols`, the shipped call shape every real caller uses) vs
FULL-UNIVERSE (`expected_symbols=None`, the pre-iter-42 unconditional whole-table scan every caller
effectively got before this change), against the live committed-seed DB
(`apps/backend/data/trendora.db`).

Both arms run the SAME shipped `_BarCache.prefill` -- this is a genuine A/B of the new
`expected_symbols`-filtered code path against its own unfiltered fallback, not a synthetic
old-vs-new reimplementation (iter-41's script compared a reimplemented OLD body against the NEW
one; this one needs no reimplementation because both arms are the current, single, shipped
function).

Each mode runs in its OWN process invocation so `/proc/<pid>/status`'s VmPeak/VmHWM reflect ONLY
that mode's allocation. Read-only (SELECT only, no writes) -- safe, AG-9-compliant (no network), not
an AG-10 concern (a single serial `.yield_per()`-streamed table scan/subset scan, the same operation
every backfill job already runs routinely).

iter-37 lesson ("assert the condition was actually live"): this script also prints N_SYMBOLS/N_ROWS
for each arm so the caller can verify the subset arm genuinely loaded FEWER symbols/rows than the
full arm before trusting any VmPeak delta -- an absence of a particular allocation is not proof the
bound landed if the code path recording it was never actually exercised.

Usage: <venv python> measure_prefill_subset_vs_full.py <db_path> <subset|full>
Prints MODE / N_SYMBOLS / N_ROWS / VmPeak / VmHWM / VmRSS / VmSize (kB) to stdout.
"""
from __future__ import annotations

import os
import sys

BACKEND_ROOT = "/home/dennis-chan/Git/trendora/apps/backend"
sys.path.insert(0, BACKEND_ROOT)

from sqlmodel import Session  # noqa: E402

from app.db import make_engine  # noqa: E402
from app.engine.prices import _BarCache  # noqa: E402
from app.engine.universe_screen import read_pool  # noqa: E402


def _run(engine, mode: str) -> tuple[int, int]:
    """The SHIPPED (iter-42) `_BarCache.prefill` -- the actual product code, unmodified call, run
    with either the real candidate-pool `expected_symbols` (subset) or none at all (full-universe,
    the fallback every pre-iter-42 caller effectively got)."""
    with Session(engine) as session:
        cache = _BarCache()
        if mode == "subset":
            pool_symbols = {row["symbol"] for row in read_pool()}
            cache.prefill(session, expected_symbols=pool_symbols)
        elif mode == "full":
            cache.prefill(session)  # expected_symbols=None -> unconditional whole-table scan
        else:
            raise SystemExit(f"unknown mode {mode!r} -- expected 'subset' or 'full'")
    n_symbols = len(cache._by_symbol)
    n_rows = sum(len(v) for v in cache._by_symbol.values())
    return n_symbols, n_rows


def main() -> None:
    db_path = sys.argv[1]
    mode = sys.argv[2]
    engine = make_engine(f"sqlite:///{db_path}")

    n_symbols, n_rows = _run(engine, mode)

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
