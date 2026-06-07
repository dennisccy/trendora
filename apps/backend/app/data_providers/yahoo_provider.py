"""YahooProvider — a no-key live EOD provider (J-33 import-source catalog).

Fetches REAL daily OHLCV bars from Yahoo Finance's public chart JSON endpoint (no API key — the
canonical runbook source, listed first in the goal). It mirrors `SeedProvider`/`StooqProvider`'s
contract exactly: on ANY failure — a network/HTTP error, a chart `error` payload, a missing/empty
result, or an unparseable field — it RAISES `ProviderUnavailableError` and returns ZERO bars. It NEVER
synthesizes a placeholder bar to avoid raising (anti-goals: No fabricated data; Live fetch is
real-data-only). A row whose price fields are null (a provider gap) is SKIPPED, never back-filled.

Resolved ONLY by the on-demand Data Manager fetch path via the provider factory from the config
`data_manager.providers` catalog; the default boot/runtime provider stays the offline `SeedProvider`.
"""
from __future__ import annotations

from datetime import date as date_cls, datetime, timezone
from typing import Optional

import httpx

from app.data_providers._http import HTTP_TIMEOUT_SECONDS, fetch_json
from app.data_providers.base import Bar, PriceProvider, ProviderUnavailableError

# Yahoo Finance public chart endpoint (no key). Yahoo uses bare US tickers and keeps the caret for
# indices (e.g. `AAPL`, `SPY`, `^VIX`) — the SAME symbols Trendora uses internally, so no remapping.
_YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/"
# Yahoo Finance public quote endpoint (no key) — the J-35 market-cap reference source (`marketCap`).
_YAHOO_QUOTE_URL = "https://query1.finance.yahoo.com/v7/finance/quote"
# A browser-like UA avoids Yahoo's bare-client 403; it carries no credential.
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; Trendora/1.0)"}


class YahooProvider(PriceProvider):
    def __init__(self, *, client: Optional[httpx.Client] = None, timeout: float = HTTP_TIMEOUT_SECONDS):
        self._client = client
        self._timeout = timeout

    def get_daily(
        self,
        symbol: str,
        start: Optional[date_cls] = None,
        end: Optional[date_cls] = None,
    ) -> list[Bar]:
        params: dict[str, object] = {"interval": "1d"}
        if start is not None and end is not None:
            params["period1"] = int(datetime(start.year, start.month, start.day, tzinfo=timezone.utc).timestamp())
            params["period2"] = int(datetime(end.year, end.month, end.day, 23, 59, 59, tzinfo=timezone.utc).timestamp())
        else:
            params["range"] = "1y"
        data = fetch_json(
            _YAHOO_CHART_URL + symbol,
            symbol=symbol,
            label="yahoo",
            params=params,
            headers=_HEADERS,
            client=self._client,
            timeout=self._timeout,
        )
        return self._parse(symbol, data, start, end)

    def get_market_cap(self, symbol: str) -> Optional[float]:
        """REAL market-cap reference for one symbol (J-35 expand capability, behind the same abstraction;
        yahoo is `supports_market_cap: true`). Reads Yahoo's no-key quote endpoint and returns the real
        `marketCap` (a positive float), or `None` when the field is absent for the symbol (the expand
        caller omits that candidate with `no_market_cap` — never fabricates a cap). On a transport/HTTP
        failure it RAISES `ProviderUnavailableError` / `RateLimitError` exactly like `get_daily` (the error
        is built from a REDACTED URL by `_http.fetch_json`, so no credential can leak). NOTE: live Yahoo
        market-cap egress is rate-limited for this host (MEMORY: data-provider-access-constraints) — the
        expand machinery is proven offline with an injected provider; this live path records NA/rate-limited
        honestly when walled."""
        data = fetch_json(
            _YAHOO_QUOTE_URL,
            symbol=symbol,
            label="yahoo",
            params={"symbols": symbol},
            headers=_HEADERS,
            client=self._client,
            timeout=self._timeout,
        )
        try:
            results = data["quoteResponse"]["result"]  # type: ignore[index]
        except (KeyError, IndexError, TypeError) as exc:  # unexpected shape — surface, never fabricate
            raise ProviderUnavailableError(f"yahoo quote unparseable for {symbol!r}: {exc}") from exc
        for row in results or []:
            cap = row.get("marketCap") if isinstance(row, dict) else None
            if cap is not None:
                try:
                    value = float(cap)
                except (TypeError, ValueError):
                    return None  # malformed cap → treat as absent (omit + log), never fabricate
                return value if value > 0 else None
        return None  # no marketCap for this symbol — absent, not fabricated

    def _parse(self, symbol: str, data: object, start: Optional[date_cls], end: Optional[date_cls]) -> list[Bar]:
        try:
            chart = data["chart"]  # type: ignore[index]
            if chart.get("error"):
                raise ProviderUnavailableError(f"yahoo returned an error for {symbol!r}: {chart['error']}")
            result = chart["result"]
            if not result:
                raise ProviderUnavailableError(f"yahoo returned no result for {symbol!r}")
            block = result[0]
            timestamps = block["timestamp"]
            quote = block["indicators"]["quote"][0]
            opens, highs, lows, closes, volumes = (
                quote["open"], quote["high"], quote["low"], quote["close"], quote["volume"],
            )
        except (KeyError, IndexError, TypeError) as exc:  # unexpected shape — surface, never fabricate
            raise ProviderUnavailableError(f"yahoo response unparseable for {symbol!r}: {exc}") from exc

        bars: list[Bar] = []
        try:
            for i, ts in enumerate(timestamps):
                o, h, l, c, v = opens[i], highs[i], lows[i], closes[i], volumes[i]
                if o is None or h is None or l is None or c is None:
                    continue  # a provider gap (null price) is skipped — never back-filled
                d = datetime.fromtimestamp(ts, tz=timezone.utc).date()
                if start is not None and d < start:
                    continue
                if end is not None and d > end:
                    continue
                bars.append(Bar(date=d, open=float(o), high=float(h), low=float(l), close=float(c),
                                volume=float(v) if v is not None else 0.0))
        except (KeyError, IndexError, ValueError, TypeError) as exc:  # malformed cell — surface, never fabricate
            raise ProviderUnavailableError(f"yahoo response unparseable for {symbol!r}: {exc}") from exc
        bars.sort(key=lambda b: b.date)
        return bars
