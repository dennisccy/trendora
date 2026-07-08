"""iter-22 (J-14) — targeted, idempotent loader for `config.index_chart.symbols` entries that are
missing from `daily_prices` on an ALREADY-BUILT local database.

`app.seed_loader.load_seed` only (re)loads prices when `daily_prices` is completely EMPTY (`if existing
and not force: return {"loaded": False, ...}`), so a symbol added to `index_chart.symbols` (config.yaml)
AFTER a local DB was already built is never picked up by a normal restart. The `kind="rebuild"`
data-manager job WOULD pick it up, but it wipes and reprocesses the WHOLE database from scratch — a
multi-hour operation that destroys every existing snapshot run (the evidence ledger's underlying
historical data). That is disproportionate for adding a handful of presentation-only index/benchmark
symbols, so this script does the minimal, additive, idempotent thing instead: for each symbol in
`config.index_chart.symbols` with ZERO existing rows in `daily_prices`, insert its bars from the SAME
committed `SeedProvider` fixture `load_prices` reads. Every symbol that already has >= 1 row — and every
other table (snapshots, forward returns, scanner results) — is left completely untouched. Safe to
re-run: a symbol loaded on a prior run is skipped on the next one (idempotent no-op).

For a FRESH database (a clean clone, CI, or a deliberately rebuilt local DB) this script is unnecessary —
`load_seed`/`load_prices` already include every `index_chart.symbols` entry via `all_seed_symbols`, with
zero special-casing. It exists purely for THIS-ENVIRONMENT remediation of an already-populated database.

Usage:
    .venv/bin/python scripts/load_missing_index_symbols.py [--dry-run]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import func, insert, select  # noqa: E402
from sqlmodel import Session  # noqa: E402

from app.config import Config, get_config  # noqa: E402
from app.data_providers.base import ProviderUnavailableError  # noqa: E402
from app.data_providers.seed_provider import SeedProvider  # noqa: E402
from app.db import get_engine  # noqa: E402
from app.engine.universe_screen import DEFAULT_SEED_DIR  # noqa: E402
from app.models import DailyPrice  # noqa: E402


def load_missing_index_symbols(
    session: Session,
    seed_dir: Optional[str | Path] = None,
    *,
    config: Optional[Config] = None,
    dry_run: bool = False,
) -> dict[str, int]:
    """Insert bars for every `config.index_chart.symbols` entry that currently has ZERO rows in
    `daily_prices`, reading each from the committed `SeedProvider` fixture (the same one `load_prices`
    uses). A symbol that already has >= 1 row is skipped — idempotent, safe to re-run. A configured
    symbol with no committed CSV is skipped honestly (never fabricated — the same contract
    `load_prices` already has). Returns `{symbol: rows_inserted}` for the symbols actually (or, in
    `dry_run`, that WOULD be) loaded this run; an empty dict means every configured symbol already has
    bars. `dry_run=True` reports without writing anything."""
    cfg = config or get_config()
    provider = SeedProvider(Path(seed_dir) if seed_dir else DEFAULT_SEED_DIR)
    loaded: dict[str, int] = {}
    for entry in cfg.index_chart.symbols:
        symbol = entry.symbol
        existing = session.scalar(
            select(func.count()).select_from(DailyPrice).where(DailyPrice.symbol == symbol)
        )
        if existing:
            continue  # already loaded — idempotent no-op
        try:
            bars = provider.get_daily(symbol)
        except ProviderUnavailableError:
            continue  # no committed fixture for this symbol — honestly skipped, never fabricated
        if not bars:
            continue
        if not dry_run:
            rows = [
                {
                    "symbol": symbol, "date": bar.date, "open": bar.open, "high": bar.high,
                    "low": bar.low, "close": bar.close, "volume": bar.volume,
                }
                for bar in bars
            ]
            session.execute(insert(DailyPrice.__table__), rows)
        loaded[symbol] = len(bars)
    if not dry_run and loaded:
        session.commit()
    return loaded


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--dry-run", action="store_true", help="report what would load without writing to the database"
    )
    args = parser.parse_args()

    engine = get_engine()
    with Session(engine) as session:
        loaded = load_missing_index_symbols(session, dry_run=args.dry_run)

    if not loaded:
        print("No index_chart.symbols are missing bars — nothing to load (already up to date).")
        return
    verb = "Would load" if args.dry_run else "Loaded"
    for symbol, count in loaded.items():
        print(f"{verb} {symbol}: {count} bars")


if __name__ == "__main__":
    main()
