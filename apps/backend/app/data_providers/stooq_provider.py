"""StooqProvider — the config-selected LIVE end-of-day provider (real data only).

Fetches REAL daily OHLCV bars from Stooq's free CSV endpoint (no API key) via `httpx`. It mirrors
`SeedProvider`'s contract exactly: on ANY failure — a network/HTTP error, an unknown-symbol "N/D"
body, a rate-limited/non-CSV response, or an unparseable row — it RAISES `ProviderUnavailableError`
and returns ZERO bars. It NEVER synthesizes/placeholder-fills a bar to avoid raising (anti-goal:
No fabricated data; *Live fetch is real-data-only*).

Used ONLY by the on-demand Data Manager fetch path (`app.engine.data_manager`), resolved via the
provider factory when a job selects the `stooq` import `source` (J-33). The default boot/runtime provider
stays the offline `SeedProvider`, so the committed seed and the walk-forward evidence remain reproducible.
This client hits Stooq's free CSV (no credential of its own); the import catalog may still mark `stooq`
`needs_key` for this environment (the free endpoint is IP-gated — iter-3 lesson), in which case the
engine's key gate requires an env/session key before the job runs. Any key would be read only from the
environment or a session paste — never persisted.
"""
from __future__ import annotations

import csv
import io
from datetime import date as date_cls
from typing import Optional

import httpx

from app.data_providers.base import Bar, PriceProvider, ProviderUnavailableError

# Stooq's daily history CSV endpoint (free, no key): ?s=<symbol>&i=d[&d1=YYYYMMDD&d2=YYYYMMDD].
_STOOQ_CSV_URL = "https://stooq.com/q/d/l/"
_HTTP_TIMEOUT_SECONDS = 15.0  # network timeout (not a scoring tunable; data_providers/ is not calc code)


def to_stooq_symbol(symbol: str) -> str:
    """Map an internal ticker to Stooq's symbol convention: US equities/ETFs take a `.us` suffix
    (e.g. `AAPL` -> `aapl.us`); an index keeps its caret (e.g. `^VIX` -> `^vix`)."""
    s = symbol.strip().lower()
    if s.startswith("^"):
        return s
    return f"{s}.us"


class StooqProvider(PriceProvider):
    # goal-market-compass iter-9 (J-10 gap #2): the provider-identity label `run_gated_recovery`'s
    # fetch_provider/convention_provider mismatch guard compares (`base.PriceProvider.source`).
    source = "stooq"

    def __init__(
        self,
        *,
        client: Optional[httpx.Client] = None,
        timeout: float = _HTTP_TIMEOUT_SECONDS,
    ):
        # `client` is injectable for tests (a fake/stub); production uses a one-shot httpx.get.
        self._client = client
        self._timeout = timeout

    def get_daily(
        self,
        symbol: str,
        start: Optional[date_cls] = None,
        end: Optional[date_cls] = None,
    ) -> list[Bar]:
        params = {"s": to_stooq_symbol(symbol), "i": "d"}
        if start is not None:
            params["d1"] = start.strftime("%Y%m%d")
        if end is not None:
            params["d2"] = end.strftime("%Y%m%d")
        try:
            if self._client is not None:
                response = self._client.get(_STOOQ_CSV_URL, params=params, timeout=self._timeout)
            else:
                response = httpx.get(_STOOQ_CSV_URL, params=params, timeout=self._timeout)
            response.raise_for_status()
            text = response.text
        except httpx.HTTPError as exc:  # connect/timeout/HTTP status — surface, never fabricate
            raise ProviderUnavailableError(
                f"stooq request failed for {symbol!r}: {exc}"
            ) from exc
        return self._parse(symbol, text, start, end)

    def _parse(
        self,
        symbol: str,
        text: str,
        start: Optional[date_cls],
        end: Optional[date_cls],
    ) -> list[Bar]:
        body = text.strip()
        first_line = body.splitlines()[0] if body else ""
        # An unknown symbol / rate-limit returns "N/D" or a non-CSV body — refuse to fabricate bars.
        if not body or not first_line.lower().startswith("date") or "N/D" in first_line:
            raise ProviderUnavailableError(
                f"stooq returned no usable data for {symbol!r}: {body[:80]!r}"
            )
        bars: list[Bar] = []
        try:
            for row in csv.DictReader(io.StringIO(body)):
                d = date_cls.fromisoformat(row["Date"])
                if start is not None and d < start:
                    continue
                if end is not None and d > end:
                    continue
                bars.append(
                    Bar(
                        date=d,
                        open=float(row["Open"]),
                        high=float(row["High"]),
                        low=float(row["Low"]),
                        close=float(row["Close"]),
                        volume=float(row["Volume"]),
                    )
                )
        except (KeyError, ValueError) as exc:  # malformed/partial row — surface, never fabricate
            raise ProviderUnavailableError(
                f"stooq response unparseable for {symbol!r}: {exc}"
            ) from exc
        bars.sort(key=lambda b: b.date)
        return bars
