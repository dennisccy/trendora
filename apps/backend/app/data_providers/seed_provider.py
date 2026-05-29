"""SeedProvider — the deterministic, offline DEFAULT provider.

Reads the committed frozen CSV fixture under `data/seed/prices/`. No network, no keys.
The same `(symbol, start, end)` returns byte-identical bars across calls. On a missing or
unreadable fixture it RAISES `ProviderUnavailableError` and never returns synthesized bars
(anti-goal: No fabricated data).
"""
from __future__ import annotations

import csv
from datetime import date as date_cls
from pathlib import Path
from typing import Optional

from app.data_providers.base import Bar, PriceProvider, ProviderUnavailableError


def symbol_to_filename(symbol: str) -> str:
    """Deterministic, filesystem-safe mapping. e.g. '^VIX' -> '_VIX.csv'."""
    return symbol.replace("^", "_").upper() + ".csv"


class SeedProvider(PriceProvider):
    def __init__(self, seed_dir: str | Path):
        self.seed_dir = Path(seed_dir)
        self.prices_dir = self.seed_dir / "prices"

    def get_daily(
        self,
        symbol: str,
        start: Optional[date_cls] = None,
        end: Optional[date_cls] = None,
    ) -> list[Bar]:
        path = self.prices_dir / symbol_to_filename(symbol)
        if not path.exists():
            raise ProviderUnavailableError(
                f"seed fixture missing for symbol {symbol!r} at {path} — refusing to fabricate bars"
            )
        bars: list[Bar] = []
        try:
            with path.open(newline="") as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    d = date_cls.fromisoformat(row["date"])
                    if start is not None and d < start:
                        continue
                    if end is not None and d > end:
                        continue
                    bars.append(
                        Bar(
                            date=d,
                            open=float(row["open"]),
                            high=float(row["high"]),
                            low=float(row["low"]),
                            close=float(row["close"]),
                            volume=float(row["volume"]),
                        )
                    )
        except (OSError, KeyError, ValueError) as exc:
            raise ProviderUnavailableError(
                f"seed fixture unreadable for {symbol!r} ({path}): {exc}"
            ) from exc
        bars.sort(key=lambda b: b.date)
        return bars
