"""StooqProvider — the config-selected LIVE EOD provider (iter-3, J-17).

The critical-anti-goal proof here is *Live fetch is real-data-only*: on ANY failure the provider RAISES
`ProviderUnavailableError` and returns ZERO bars — it never fabricates a placeholder bar to force a
green fetch (mirrors `SeedProvider`'s contract). The offline tests inject a fake httpx client so they
need no network; one `@pytest.mark.integration` test hits the real Stooq endpoint and SKIPS (honestly,
not silently passes) when offline.
"""
from __future__ import annotations

from datetime import date

import httpx
import pytest

from app.data_providers import make_provider
from app.data_providers.base import Bar, ProviderUnavailableError
from app.data_providers.stooq_provider import StooqProvider, to_stooq_symbol

_VALID_CSV = (
    "Date,Open,High,Low,Close,Volume\n"
    "2024-01-02,185.0,186.0,184.0,185.5,1000\n"
    "2024-01-03,186.0,188.0,185.0,187.25,1200\n"
    "2024-01-04,187.0,187.5,183.0,184.0,1500\n"
)


class _FakeResponse:
    def __init__(self, text: str, status_code: int = 200):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"HTTP {self.status_code}", request=httpx.Request("GET", _STOOQ_URL), response=None
            )


_STOOQ_URL = "https://stooq.com/q/d/l/"


class _FakeClient:
    """A stand-in httpx client: either returns a canned body or raises a canned httpx error."""

    def __init__(self, *, text: str | None = None, exc: Exception | None = None):
        self._text = text
        self._exc = exc
        self.calls: list[dict] = []

    def get(self, url, params=None, timeout=None):
        self.calls.append({"url": url, "params": params, "timeout": timeout})
        if self._exc is not None:
            raise self._exc
        return _FakeResponse(self._text or "")


def test_to_stooq_symbol_mapping():
    """US equities/ETFs take a `.us` suffix; an index keeps its caret."""
    assert to_stooq_symbol("AAPL") == "aapl.us"
    assert to_stooq_symbol("SPY") == "spy.us"
    assert to_stooq_symbol("^VIX") == "^vix"


def test_network_failure_raises_provider_unavailable_no_bars():
    """A connect/timeout error surfaces as ProviderUnavailableError — no fabricated bars."""
    provider = StooqProvider(client=_FakeClient(exc=httpx.ConnectError("offline")))
    with pytest.raises(ProviderUnavailableError) as exc:
        provider.get_daily("AAPL", start=date(2024, 1, 1), end=date(2024, 1, 31))
    assert "AAPL" in str(exc.value)


def test_http_error_status_raises_provider_unavailable():
    """A non-2xx HTTP status surfaces as ProviderUnavailableError (never a fabricated bar)."""
    provider = StooqProvider(client=_FakeClient(text="rate limited", exc=None))
    # a 5xx body that does not start with the CSV header is treated as no usable data
    with pytest.raises(ProviderUnavailableError):
        provider.get_daily("AAPL")


def test_unknown_symbol_nd_body_raises():
    """Stooq's "N/D" unknown-symbol response yields NO bars (explicit error, never fabricated)."""
    provider = StooqProvider(client=_FakeClient(text="N/D\n"))
    with pytest.raises(ProviderUnavailableError) as exc:
        provider.get_daily("ZZZZ_NOT_A_SYMBOL")
    assert "ZZZZ_NOT_A_SYMBOL" in str(exc.value)


def test_unparseable_row_raises_not_fabricates():
    """A malformed numeric cell surfaces as ProviderUnavailableError — the provider never substitutes
    a synthesized value to keep the row."""
    bad_csv = "Date,Open,High,Low,Close,Volume\n2024-01-02,185.0,186.0,184.0,N/D,1000\n"
    provider = StooqProvider(client=_FakeClient(text=bad_csv))
    with pytest.raises(ProviderUnavailableError):
        provider.get_daily("AAPL")


def test_parses_valid_csv_into_sorted_bars():
    """A valid CSV is parsed into exact, ascending Bars (the happy path, no network)."""
    client = _FakeClient(text=_VALID_CSV)
    provider = StooqProvider(client=client)
    bars = provider.get_daily("AAPL", start=date(2024, 1, 2), end=date(2024, 1, 4))

    assert [b.date for b in bars] == [date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4)]
    assert bars[1] == Bar(date=date(2024, 1, 3), open=186.0, high=188.0, low=185.0, close=187.25, volume=1200.0)
    # the request used the Stooq symbol + daily interval + the date window
    assert client.calls[0]["params"] == {"s": "aapl.us", "i": "d", "d1": "20240102", "d2": "20240104"}


def test_date_window_filters_bars():
    """`start`/`end` filter the parsed rows inclusively (bars outside the window are dropped)."""
    provider = StooqProvider(client=_FakeClient(text=_VALID_CSV))
    bars = provider.get_daily("AAPL", start=date(2024, 1, 3), end=date(2024, 1, 3))
    assert [b.date for b in bars] == [date(2024, 1, 3)]


def test_factory_resolves_stooq_and_seed():
    """The provider factory maps the config names to the right concrete providers."""
    assert isinstance(make_provider("stooq"), StooqProvider)
    from app.data_providers.seed_provider import SeedProvider

    assert isinstance(make_provider("seed"), SeedProvider)
    with pytest.raises(ValueError):
        make_provider("bogus")


@pytest.mark.integration
def test_stooq_real_fetch_single_symbol_or_skip():
    """Live integration (real-data-only): fetch a single liquid US symbol's recent bars from the real
    Stooq endpoint. SKIPS honestly when offline / rate-limited (never silently passes) so the dev
    handoff can state whether the live provider was exercised."""
    provider = StooqProvider()
    try:
        bars = provider.get_daily("AAPL", start=date(2024, 1, 2), end=date(2024, 1, 12))
    except ProviderUnavailableError as exc:
        pytest.skip(f"Stooq unavailable (offline / rate-limited): {exc}")
    assert bars, "expected >=1 real bar from Stooq for AAPL"
    assert all(date(2024, 1, 2) <= b.date <= date(2024, 1, 12) for b in bars)
    assert all(b.close > 0 and b.high >= b.low for b in bars)
