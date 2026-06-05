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
