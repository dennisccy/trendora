"""ops-hardening iter-42 AUDIT (finding B2) — the arm the developer's own TC-6 measurement omitted.

`measure_prefill_subset_vs_full.py` compares `prefill(expected_symbols=pool)` against
`prefill(None)` and reports a 2.5% VmPeak reduction. But the shipped change does not simply DROP
the 43 excluded symbols — it defers them to `bars_asof`'s lazy per-symbol path, which builds the
`list[Bar]` representation iter-41 deliberately REPLACED with `_SymbolColumns` to save memory. 36 of
those 43 (162,885 of 195,457 rows) are the index/sector/industry/volatility ETFs named in
`config.etfs` (`SPY`, `QQQ`, `IWM`, `RSP`, the 11 XL* sector SPDRs, the 20 industry ETFs, `^VIX`),
which `sectors.py`/`themes.py`/`regime.py`/`market_phase.py` read on EVERY snapshot date — so a real
job DOES pay that lazy cost, and holds it for the life of the cache.

Arms (each its own process, `/proc/<pid>/status` sampled after the load):
  iter41  — `prefill(session)` (unfiltered whole-table columnar scan): the pre-iter-42 baseline.
  iter42  — `prefill(session, expected_symbols=pool)` THEN one `bars_asof` per config-referenced
            excluded symbol (the lazy load a real snapshot job triggers). Read at a date BEFORE any
            bar so the returned slice is empty — this measures the RETAINED cache, not a transient.

Read-only (SELECT only). Run under the same host-guard caps `scripts/start-backend.sh` applies
(taskset CPU list, BLAS thread caps, `ulimit -v` from `config.server.memory_cap_mb`,
`MALLOC_ARENA_MAX`) — see the wrapper command in the audit report.

Usage: <venv python> audit_measure_prefill_plus_lazy.py <db_path> <iter41|iter42>
"""
from __future__ import annotations

import os
import sys
from datetime import date

BACKEND_ROOT = "/home/dennis-chan/Git/trendora/apps/backend"
sys.path.insert(0, BACKEND_ROOT)

from sqlmodel import Session  # noqa: E402

from app.config import get_config  # noqa: E402
from app.db import make_engine  # noqa: E402
from app.engine.prices import _BarCache  # noqa: E402
from app.engine.universe_screen import read_pool  # noqa: E402

_BEFORE_ANY_BAR = date(1900, 1, 1)


def _config_referenced_symbols() -> set[str]:
    """Every symbol `config.etfs` names — the index/sector/industry/volatility ETFs the per-date
    engines read through `bars_asof`/`bars_asof_window`/`close_on`."""
    etfs = get_config().etfs
    dumped = etfs.model_dump() if hasattr(etfs, "model_dump") else dict(etfs)
    out: set[str] = set()
    for value in dumped.values():
        items = value if isinstance(value, list) else list(value.keys()) if isinstance(value, dict) else []
        for item in items:
            if isinstance(item, str):
                out.add(item)
            elif isinstance(item, dict):
                sym = item.get("symbol") or item.get("ticker")
                if sym:
                    out.add(sym)
    return out


def _run(engine, mode: str) -> tuple[int, int, int]:
    lazy_loaded = 0
    with Session(engine) as session:
        cache = _BarCache()
        if mode == "iter41":
            cache.prefill(session)
        elif mode == "iter42":
            pool = {row["symbol"] for row in read_pool()}
            cache.prefill(session, expected_symbols=pool)
            for symbol in sorted(_config_referenced_symbols() - pool):
                before = symbol in cache._by_symbol
                cache.bars_asof(session, symbol, _BEFORE_ANY_BAR)  # empty slice; the LOAD is the point
                if not before and cache._by_symbol.get(symbol):
                    lazy_loaded += 1
        else:
            raise SystemExit(f"unknown mode {mode!r}")
    n_symbols = len(cache._by_symbol)
    n_rows = sum(len(v) for v in cache._by_symbol.values())
    return n_symbols, n_rows, lazy_loaded


def main() -> None:
    db_path, mode = sys.argv[1], sys.argv[2]
    engine = make_engine(f"sqlite:///{db_path}")
    n_symbols, n_rows, lazy_loaded = _run(engine, mode)
    status = {}
    with open(f"/proc/{os.getpid()}/status") as fh:
        for line in fh:
            if ":" in line:
                k, v = line.split(":", 1)
                status[k.strip()] = v.strip()
    print(f"MODE={mode}")
    print(f"N_SYMBOLS={n_symbols}")
    print(f"N_ROWS={n_rows}")
    print(f"LAZY_LOADED_SYMBOLS={lazy_loaded}")
    for field in ("VmPeak", "VmHWM", "VmRSS"):
        print(f"{field}={status.get(field, '?')}")


if __name__ == "__main__":
    main()
