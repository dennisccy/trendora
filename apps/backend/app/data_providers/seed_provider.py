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
        # OPTIONAL offline market-cap reference (iter-26, J-35 expand via the env-gated `seed` import
        # source). A committed `market_caps.csv` (header `symbol,market_cap`) under the seed dir supplies
        # the REAL cap the screen gates on — read from a committed file, NEVER synthesized. The committed
        # production seed dir carries no such file (so the default provider keeps returning None / omits
        # honestly); a QA fixture seed dir provides one so an OFFLINE expand can run to completion.
        self.market_caps_path = self.seed_dir / "market_caps.csv"

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

    def get_market_cap(self, symbol: str) -> Optional[float]:
        """The symbol's market cap from the OPTIONAL committed `market_caps.csv` (iter-26, J-35 expand via
        the env-gated `seed` import source). Returns the REAL committed value when the symbol is listed,
        `None` when no `market_caps.csv` exists OR the symbol is absent (an honest omission — the expand
        caller records `no_market_cap`, never a fabricated cap). Raises `ProviderUnavailableError` only on
        a genuinely unreadable file. The cap is read from a committed file — never synthesized (anti-goals:
        No fabricated data; Live fetch is real-data-only)."""
        if not self.market_caps_path.exists():
            return None  # no offline cap reference (e.g. the production seed dir) — honest None
        try:
            with self.market_caps_path.open(newline="") as fh:
                for row in csv.DictReader(fh):
                    if (row.get("symbol") or "").strip().upper() == symbol.strip().upper():
                        raw = (row.get("market_cap") or "").strip()
                        return float(raw) if raw else None
        except (OSError, ValueError) as exc:
            raise ProviderUnavailableError(
                f"seed market-cap reference unreadable ({self.market_caps_path}): {exc}"
            ) from exc
        return None  # symbol not listed — honest omission (no_market_cap), never fabricated
