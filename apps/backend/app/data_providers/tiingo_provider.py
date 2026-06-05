"""TiingoProvider — a key-aware live EOD provider (J-33 import-source catalog).

Fetches REAL daily OHLCV bars from Tiingo's daily-prices JSON endpoint. The API token is read from the
environment (`TIINGO_API_KEY`) or pasted SESSION-ONLY into the import UI and passed through as `api_key`
— it is held only for the duration of the request and is NEVER persisted (anti-goal: Import keys are
env-or-session, never persisted). On ANY failure — no key, a network/HTTP error, or an unparseable body
— it RAISES `ProviderUnavailableError` and returns ZERO bars; it NEVER fabricates a bar (anti-goals: No
fabricated data; Live fetch is real-data-only). Constructed with NEITHER an env key nor a passed key, it
raises an explicit "requires an API key" error — never a silent fallback.
"""
from __future__ import annotations

from datetime import date as date_cls
from typing import Optional

import httpx

from app.data_providers._http import HTTP_TIMEOUT_SECONDS, fetch_json
from app.data_providers.base import Bar, PriceProvider, ProviderUnavailableError

_TIINGO_DAILY_URL = "https://api.tiingo.com/tiingo/daily/{symbol}/prices"


class TiingoProvider(PriceProvider):
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
                f"tiingo requires an API key to fetch {symbol!r}; set $TIINGO_API_KEY or paste a session key"
            )
        params: dict[str, object] = {"token": self._api_key, "format": "json"}
        if start is not None:
            params["startDate"] = start.isoformat()
        if end is not None:
            params["endDate"] = end.isoformat()
        data = fetch_json(
            _TIINGO_DAILY_URL.format(symbol=symbol),
            symbol=symbol,
            label="tiingo",
            params=params,
            client=self._client,
            timeout=self._timeout,
        )
        return self._parse(symbol, data, start, end)

    def _parse(self, symbol: str, data: object, start: Optional[date_cls], end: Optional[date_cls]) -> list[Bar]:
        if not isinstance(data, list) or not data:
            raise ProviderUnavailableError(f"tiingo returned no usable data for {symbol!r}")
        bars: list[Bar] = []
        try:
            for row in data:
                d = date_cls.fromisoformat(str(row["date"])[:10])
                if start is not None and d < start:
                    continue
                if end is not None and d > end:
                    continue
                bars.append(Bar(date=d, open=float(row["open"]), high=float(row["high"]),
                                low=float(row["low"]), close=float(row["close"]), volume=float(row["volume"])))
        except (KeyError, ValueError, TypeError) as exc:  # malformed/partial row — surface, never fabricate
            raise ProviderUnavailableError(f"tiingo response unparseable for {symbol!r}: {exc}") from exc
        bars.sort(key=lambda b: b.date)
        return bars
