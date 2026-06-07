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


class RateLimitError(ProviderUnavailableError):
    """A provider signalled rate-limiting — an HTTP 429, or a body-level throttle note (Alpha
    Vantage signals throttling in the body, not the status). A SUBCLASS of
    `ProviderUnavailableError` so every existing ``except ProviderUnavailableError`` handler stays
    correct (a rate-limit is still "no real data"); the J-34 chunked fetch loop catches this subclass
    FIRST to retry-with-backoff and then pause the import gracefully in a resumable state — distinct
    from a generic failure — rather than fabricating a bar (anti-goal: No fabricated data)."""


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

    def get_market_cap(self, symbol: str) -> Optional[float]:
        """OPTIONAL market-cap-reference capability — used ONLY by the J-35 `expand` path, behind this
        same abstraction. `get_daily` (every other journey) is unaffected.

        Returns the symbol's REAL market cap (a positive float), or `None` when the provider has no cap
        for it (the expand caller omits that candidate with a `no_market_cap` reason — never fabricates a
        cap). On a fetch/transport failure it RAISES `ProviderUnavailableError` (or `RateLimitError` on a
        429) exactly like `get_daily` — it MUST NOT synthesize a value (anti-goals: No fabricated data;
        Live fetch is real-data-only).

        The base implementation raises `ProviderUnavailableError` so a provider declared
        `supports_market_cap: false` (or one that simply has not implemented the capability) is NEVER used
        for expand — the engine gates expand to `supports_market_cap: true` sources, and an injected test
        provider overrides this method."""
        raise ProviderUnavailableError(
            f"{type(self).__name__} does not provide a market-cap reference for {symbol!r}"
        )
