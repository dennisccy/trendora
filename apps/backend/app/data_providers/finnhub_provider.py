"""FinnhubProvider — a key-aware live EOD provider (J-33 import-source catalog).

Fetches REAL daily OHLCV bars from Finnhub's stock-candle JSON endpoint. The API token is read from the
environment (`FINNHUB_API_KEY`) or pasted SESSION-ONLY into the import UI and passed through as `api_key`
— held only for the request, NEVER persisted (anti-goal: Import keys are env-or-session, never
persisted). On ANY failure — no key, a network/HTTP error, a non-`ok` status field, or an unparseable
body — it RAISES `ProviderUnavailableError` and returns ZERO bars; it NEVER fabricates a bar (anti-goals:
No fabricated data; Live fetch is real-data-only).
"""
from __future__ import annotations

from datetime import date as date_cls, datetime, timezone
from typing import Optional

import httpx

from app.data_providers._http import HTTP_TIMEOUT_SECONDS, fetch_json
from app.data_providers.base import Bar, PriceProvider, ProviderUnavailableError

_FINNHUB_CANDLE_URL = "https://finnhub.io/api/v1/stock/candle"


class FinnhubProvider(PriceProvider):
    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        client: Optional[httpx.Client] = None,
        timeout: float = HTTP_TIMEOUT_SECONDS,
    ):
        self._api_key = api_key
        self._client = client
        self._timeout = timeout

    def get_daily(
        self,
        symbol: str,
        start: Optional[date_cls] = None,
        end: Optional[date_cls] = None,
    ) -> list[Bar]:
        if not self._api_key:
            raise ProviderUnavailableError(
                f"finnhub requires an API key to fetch {symbol!r}; set $FINNHUB_API_KEY or paste a session key"
            )
        # Finnhub candles are bounded by a UNIX from/to window; default to a wide window when unbounded.
        lo = start or date_cls(1970, 1, 1)
        hi = end or datetime.now(timezone.utc).date()
        params = {
            "symbol": symbol,
            "resolution": "D",
            "from": int(datetime(lo.year, lo.month, lo.day, tzinfo=timezone.utc).timestamp()),
            "to": int(datetime(hi.year, hi.month, hi.day, 23, 59, 59, tzinfo=timezone.utc).timestamp()),
            "token": self._api_key,
        }
        data = fetch_json(
            _FINNHUB_CANDLE_URL,
            symbol=symbol,
            label="finnhub",
            params=params,
            client=self._client,
            timeout=self._timeout,
        )
        return self._parse(symbol, data, start, end)

    def _parse(self, symbol: str, data: object, start: Optional[date_cls], end: Optional[date_cls]) -> list[Bar]:
        if not isinstance(data, dict) or data.get("s") != "ok":
            raise ProviderUnavailableError(
                f"finnhub returned no usable data for {symbol!r} (status {data.get('s') if isinstance(data, dict) else data!r})"
            )
        bars: list[Bar] = []
        try:
            ts, opens, highs, lows, closes, volumes = (
                data["t"], data["o"], data["h"], data["l"], data["c"], data["v"],
            )
            for i, t in enumerate(ts):
                d = datetime.fromtimestamp(t, tz=timezone.utc).date()
                if start is not None and d < start:
                    continue
                if end is not None and d > end:
                    continue
                bars.append(Bar(date=d, open=float(opens[i]), high=float(highs[i]), low=float(lows[i]),
                                close=float(closes[i]), volume=float(volumes[i])))
        except (KeyError, IndexError, ValueError, TypeError) as exc:  # malformed series — surface, never fabricate
            raise ProviderUnavailableError(f"finnhub response unparseable for {symbol!r}: {exc}") from exc
        bars.sort(key=lambda b: b.date)
        return bars
