"""Price-provider abstraction.

A provider returns REAL daily bars or RAISES. On any failure it MUST raise
`ProviderUnavailableError` — it MUST NOT return synthesized/placeholder bars
(anti-goal: No fabricated data). The default runtime provider is the offline
`SeedProvider`; a live request-path provider is out of scope this iteration.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date as date_cls
from typing import Optional


class ProviderUnavailableError(Exception):
    """A provider could not return real data. Callers surface this as an explicit
    stale/unavailable state; providers never fabricate data to avoid raising it."""


@dataclass(frozen=True)
class Bar:
    """One daily OHLCV bar. Frozen so equality is by value (supports determinism tests)."""

    date: date_cls
    open: float
    high: float
    low: float
    close: float
    volume: float


class PriceProvider(ABC):
    @abstractmethod
    def get_daily(
        self,
        symbol: str,
        start: Optional[date_cls] = None,
        end: Optional[date_cls] = None,
    ) -> list[Bar]:
        """Return the symbol's daily bars (optionally bounded by [start, end], inclusive),
        sorted by ascending date. Raises ProviderUnavailableError if unavailable."""
        raise NotImplementedError
