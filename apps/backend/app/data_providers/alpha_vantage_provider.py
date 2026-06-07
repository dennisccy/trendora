"""AlphaVantageProvider — a key-aware live EOD provider (J-33 import-source catalog).

Fetches REAL daily OHLCV bars from Alpha Vantage's TIME_SERIES_DAILY JSON endpoint. The API key is read
from the environment (`ALPHAVANTAGE_API_KEY`) or pasted SESSION-ONLY into the import UI and passed
through as `api_key` — held only for the request, NEVER persisted (anti-goal: Import keys are
env-or-session, never persisted). On ANY failure — no key, a network/HTTP error, a rate-limit `Note` /
`Information` / `Error Message` payload, or an unparseable body — it RAISES `ProviderUnavailableError`
and returns ZERO bars; it NEVER fabricates a bar (anti-goals: No fabricated data; Live fetch is
real-data-only).
"""
from __future__ import annotations

from datetime import date as date_cls
from typing import Optional

import httpx

from app.data_providers._http import HTTP_TIMEOUT_SECONDS, fetch_json
from app.data_providers.base import Bar, PriceProvider, ProviderUnavailableError, RateLimitError

_ALPHA_VANTAGE_URL = "https://www.alphavantage.co/query"
_SERIES_KEY = "Time Series (Daily)"


class AlphaVantageProvider(PriceProvider):
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
                f"alpha_vantage requires an API key to fetch {symbol!r}; set $ALPHAVANTAGE_API_KEY or paste a session key"
            )
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "outputsize": "full",
            "apikey": self._api_key,
        }
        data = fetch_json(
            _ALPHA_VANTAGE_URL,
            symbol=symbol,
            label="alpha_vantage",
            params=params,
            client=self._client,
            timeout=self._timeout,
        )
        return self._parse(symbol, data, start, end)

    def _parse(self, symbol: str, data: object, start: Optional[date_cls], end: Optional[date_cls]) -> list[Bar]:
        # A rate-limit / error / informational payload omits the series — surface it, never fabricate.
        if not isinstance(data, dict) or _SERIES_KEY not in data:
            note = ""
            throttled = False
            if isinstance(data, dict):
                # Alpha Vantage signals throttling in the BODY (`Note`/`Information`), not the HTTP status —
                # map those to RateLimitError (retryable → resumable in J-34); `Error Message` (e.g. an
                # invalid symbol) stays a generic failure. Best-effort: any missing-series body is at worst
                # surfaced as a generic ProviderUnavailableError (never fabricated).
                throttle_note = data.get("Note") or data.get("Information")
                note = str(throttle_note or data.get("Error Message") or "")
                throttled = throttle_note is not None
            message = f"alpha_vantage returned no usable data for {symbol!r}{f': {note}' if note else ''}"
            raise (RateLimitError if throttled else ProviderUnavailableError)(message)
        series = data[_SERIES_KEY]
        if not isinstance(series, dict) or not series:
            raise ProviderUnavailableError(f"alpha_vantage returned an empty series for {symbol!r}")
        bars: list[Bar] = []
        try:
            for date_str, row in series.items():
                d = date_cls.fromisoformat(date_str)
                if start is not None and d < start:
                    continue
                if end is not None and d > end:
                    continue
                bars.append(Bar(date=d, open=float(row["1. open"]), high=float(row["2. high"]),
                                low=float(row["3. low"]), close=float(row["4. close"]), volume=float(row["5. volume"])))
        except (KeyError, ValueError, TypeError) as exc:  # malformed/partial row — surface, never fabricate
            raise ProviderUnavailableError(f"alpha_vantage response unparseable for {symbol!r}: {exc}") from exc
        bars.sort(key=lambda b: b.date)
        return bars
