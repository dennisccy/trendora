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
from typing import ClassVar, Optional, Sequence


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
    # goal-market-compass iter-9 (J-10 gap #2, audit B5): an OPTIONAL provider-identity label — `None`
    # for every provider that doesn't declare one (no behavior change for any pre-existing subclass).
    # A subclass that names a real, distinct vendor SHOULD set this to that vendor's catalog id (e.g.
    # `YahooProvider.source = "yahoo"`) so a caller comparing two provider INSTANCES can tell whether
    # they are the same vendor without importing every concrete provider class. This is the minimal,
    # non-invasive field `app.engine.j10_recovery.run_gated_recovery`'s `fetch_provider`/
    # `convention_provider` mismatch guard reads (`getattr(provider, "source", None)`) — added ONLY for
    # that guard; it does not change `get_daily`'s contract or any other caller.
    source: ClassVar[Optional[str]] = None

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

    def get_market_caps(self, symbols: Sequence[str]) -> Optional[dict[str, Optional[float]]]:
        """OPTIONAL *batched* market-cap-reference capability (J-84) — used ONLY by the expand path.

        A provider that can serve many symbols in one authenticated request (Yahoo's cookie+crumb
        `/v7/finance/quote`, fetched ONCE per session and reused across the batch) OVERRIDES this to
        return a `{symbol: REAL cap | None}` map: a symbol present in a 200 response WITH a positive
        `marketCap` maps to that real float; a symbol present-but-without a cap (a per-candidate absence)
        maps to `None` (the expand caller omits it `no_market_cap` — never fabricated). A SYSTEMIC
        auth/limit failure of the whole batch — the cookie/crumb acquisition itself failing, or the
        batched quote returning a persistent 401/429 — RAISES `RateLimitError`, so it flows through the
        expand's existing resumable-pause branch (a whole-universe auth outage is NOT silently recorded
        as "every candidate omitted"). It MUST NOT synthesize a cap (anti-goals: No fabricated data; Live
        fetch is real-data-only); the request URL carries the crumb as a query param, so any raised error
        is built from the REDACTED URL (`_http`/`_provider_error`) — the crumb/cookie never leaks.

        The DEFAULT returns `None` to mean "no batch capability — fall back to the per-symbol
        `get_market_cap` path" (preserving every per-symbol provider, e.g. Tiingo/Finnhub, and the
        per-candidate `market_cap_fetch_failed` / `no_market_cap` reasons exactly as before). It does NOT
        raise — the caller treats `None` as "use per-symbol"."""
        return None
