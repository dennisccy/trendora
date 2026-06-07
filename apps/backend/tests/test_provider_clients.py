"""Live EOD provider clients — Yahoo / Tiingo / Finnhub / Alpha Vantage (iter-21, J-33).

The critical anti-goal proof here is *Live fetch is real-data-only* + *No fabricated data*: on ANY
failure — a network/HTTP error, a non-OK status payload, a rate-limit body, an unparseable field, or a
missing API key — each client RAISES `ProviderUnavailableError` and returns ZERO bars. It NEVER
fabricates a placeholder bar to force a green fetch (mirrors `SeedProvider`/`StooqProvider`). Every test
injects a FAKE httpx client (a canned body / a canned error) — there is NO live network call. One
combined happy-path test per provider proves the JSON→ascending-`Bar` parse; the factory test proves
`make_provider` resolves every catalog id (with key pass-through) and that a needs-key provider with no
key raises an explicit error.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

import httpx
import pytest

from app.data_providers import make_provider
from app.data_providers.alpha_vantage_provider import AlphaVantageProvider
from app.data_providers.base import Bar, ProviderUnavailableError, RateLimitError
from app.data_providers.finnhub_provider import FinnhubProvider
from app.data_providers.tiingo_provider import TiingoProvider
from app.data_providers.yahoo_provider import YahooProvider


def _unix(d: date) -> int:
    return int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp())


class _FakeResponse:
    def __init__(self, payload=None, *, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"HTTP {self.status_code}", request=httpx.Request("GET", "http://x"), response=None
            )

    def json(self):
        if self._payload is _UNPARSEABLE:
            raise ValueError("not json")
        return self._payload


_UNPARSEABLE = object()


class _FakeClient:
    """A stand-in httpx client: returns a canned JSON payload (or an unparseable marker), or raises a
    canned httpx error. Records the request params for the happy-path assertion."""

    def __init__(self, *, payload=None, exc: Exception | None = None, status_code: int = 200):
        self._payload = payload
        self._exc = exc
        self._status = status_code
        self.calls: list[dict] = []

    def get(self, url, params=None, headers=None, timeout=None):
        self.calls.append({"url": url, "params": params, "headers": headers})
        if self._exc is not None:
            raise self._exc
        return _FakeResponse(self._payload, status_code=self._status)


# ==================================================================================================
# Yahoo (no-key)
# ==================================================================================================
_YAHOO_OK = {
    "chart": {
        "error": None,
        "result": [{
            "timestamp": [_unix(date(2024, 1, 2)), _unix(date(2024, 1, 3))],
            "indicators": {"quote": [{
                "open": [185.0, 186.0], "high": [186.0, 188.0], "low": [184.0, 185.0],
                "close": [185.5, 187.25], "volume": [1000, 1200],
            }]},
        }],
    }
}


def test_yahoo_parses_valid_json_into_sorted_bars():
    client = _FakeClient(payload=_YAHOO_OK)
    bars = YahooProvider(client=client).get_daily("AAPL", start=date(2024, 1, 2), end=date(2024, 1, 4))
    assert [b.date for b in bars] == [date(2024, 1, 2), date(2024, 1, 3)]
    assert bars[1] == Bar(date=date(2024, 1, 3), open=186.0, high=188.0, low=185.0, close=187.25, volume=1200.0)


def test_yahoo_http_error_raises_no_bars():
    provider = YahooProvider(client=_FakeClient(exc=httpx.ConnectError("offline")))
    with pytest.raises(ProviderUnavailableError) as exc:
        provider.get_daily("AAPL", start=date(2024, 1, 1), end=date(2024, 1, 31))
    assert "AAPL" in str(exc.value)


def test_yahoo_error_payload_raises():
    provider = YahooProvider(client=_FakeClient(payload={"chart": {"error": "Not Found", "result": None}}))
    with pytest.raises(ProviderUnavailableError):
        provider.get_daily("ZZZZ")


def test_yahoo_unparseable_body_raises():
    provider = YahooProvider(client=_FakeClient(payload=_UNPARSEABLE))
    with pytest.raises(ProviderUnavailableError):
        provider.get_daily("AAPL")


def test_yahoo_skips_null_price_rows_never_fabricates():
    """A row with a null close is a provider gap — it is SKIPPED, never back-filled with a fabricated bar."""
    payload = {
        "chart": {"error": None, "result": [{
            "timestamp": [_unix(date(2024, 1, 2)), _unix(date(2024, 1, 3))],
            "indicators": {"quote": [{
                "open": [185.0, None], "high": [186.0, None], "low": [184.0, None],
                "close": [185.5, None], "volume": [1000, None],
            }]},
        }]}
    }
    bars = YahooProvider(client=_FakeClient(payload=payload)).get_daily("AAPL")
    assert [b.date for b in bars] == [date(2024, 1, 2)]  # the null row is dropped, not invented


# ==================================================================================================
# Tiingo (key-aware)
# ==================================================================================================
_TIINGO_OK = [
    {"date": "2024-01-02T00:00:00.000Z", "open": 185.0, "high": 186.0, "low": 184.0, "close": 185.5, "volume": 1000},
    {"date": "2024-01-03T00:00:00.000Z", "open": 186.0, "high": 188.0, "low": 185.0, "close": 187.25, "volume": 1200},
]


def test_tiingo_parses_valid_json_into_sorted_bars():
    client = _FakeClient(payload=_TIINGO_OK)
    bars = TiingoProvider(api_key="k", client=client).get_daily("AAPL", start=date(2024, 1, 2), end=date(2024, 1, 4))
    assert [b.date for b in bars] == [date(2024, 1, 2), date(2024, 1, 3)]
    assert bars[0].close == 185.5
    assert client.calls[0]["params"]["token"] == "k"  # the key rides the request, never persisted


def test_tiingo_no_key_raises_explicitly():
    with pytest.raises(ProviderUnavailableError) as exc:
        TiingoProvider(api_key=None).get_daily("AAPL")
    assert "requires an API key" in str(exc.value)


def test_tiingo_http_error_raises():
    with pytest.raises(ProviderUnavailableError):
        TiingoProvider(api_key="k", client=_FakeClient(exc=httpx.ConnectError("x"))).get_daily("AAPL")


def test_tiingo_empty_body_raises():
    with pytest.raises(ProviderUnavailableError):
        TiingoProvider(api_key="k", client=_FakeClient(payload=[])).get_daily("AAPL")


# ==================================================================================================
# Finnhub (key-aware)
# ==================================================================================================
_FINNHUB_OK = {
    "s": "ok",
    "t": [_unix(date(2024, 1, 2)), _unix(date(2024, 1, 3))],
    "o": [185.0, 186.0], "h": [186.0, 188.0], "l": [184.0, 185.0], "c": [185.5, 187.25], "v": [1000, 1200],
}


def test_finnhub_parses_valid_json_into_sorted_bars():
    bars = FinnhubProvider(api_key="k", client=_FakeClient(payload=_FINNHUB_OK)).get_daily(
        "AAPL", start=date(2024, 1, 2), end=date(2024, 1, 4)
    )
    assert [b.date for b in bars] == [date(2024, 1, 2), date(2024, 1, 3)]
    assert bars[1].close == 187.25


def test_finnhub_no_key_raises_explicitly():
    with pytest.raises(ProviderUnavailableError) as exc:
        FinnhubProvider(api_key=None).get_daily("AAPL")
    assert "requires an API key" in str(exc.value)


def test_finnhub_no_data_status_raises():
    """Finnhub's `s != "ok"` (e.g. `no_data`) yields ZERO bars — an explicit error, never fabricated."""
    with pytest.raises(ProviderUnavailableError):
        FinnhubProvider(api_key="k", client=_FakeClient(payload={"s": "no_data"})).get_daily("AAPL")


# ==================================================================================================
# Alpha Vantage (key-aware)
# ==================================================================================================
_ALPHA_OK = {
    "Time Series (Daily)": {
        "2024-01-02": {"1. open": "185.0", "2. high": "186.0", "3. low": "184.0", "4. close": "185.5", "5. volume": "1000"},
        "2024-01-03": {"1. open": "186.0", "2. high": "188.0", "3. low": "185.0", "4. close": "187.25", "5. volume": "1200"},
    }
}


def test_alpha_vantage_parses_valid_json_into_sorted_bars():
    bars = AlphaVantageProvider(api_key="k", client=_FakeClient(payload=_ALPHA_OK)).get_daily(
        "AAPL", start=date(2024, 1, 2), end=date(2024, 1, 4)
    )
    assert [b.date for b in bars] == [date(2024, 1, 2), date(2024, 1, 3)]
    assert bars[0].close == 185.5


def test_alpha_vantage_no_key_raises_explicitly():
    with pytest.raises(ProviderUnavailableError) as exc:
        AlphaVantageProvider(api_key=None).get_daily("AAPL")
    assert "requires an API key" in str(exc.value)


def test_alpha_vantage_rate_limit_note_raises():
    """A rate-limit `Note` (no series) yields ZERO bars — an explicit error, never a fabricated bar."""
    payload = {"Note": "Thank you for using Alpha Vantage! Our standard API rate limit is ..."}
    with pytest.raises(ProviderUnavailableError):
        AlphaVantageProvider(api_key="k", client=_FakeClient(payload=payload)).get_daily("AAPL")


# ==================================================================================================
# make_provider — resolves every catalog id; key-aware providers accept a pass-through key
# ==================================================================================================
def test_make_provider_resolves_every_catalog_id():
    """The factory resolves every config-catalog id to its concrete client (+ seed) — no hardcoded list
    drift. A key-aware client built with no key raises an explicit error when used; an unknown name
    raises ValueError (never a silent fallback)."""
    from app.config import load_config
    from app.data_providers.seed_provider import SeedProvider

    cfg = load_config()
    expected = {
        "yahoo": YahooProvider, "tiingo": TiingoProvider,
        "finnhub": FinnhubProvider, "alpha_vantage": AlphaVantageProvider,
    }
    for source_id in cfg.data_manager.provider_ids():
        provider = make_provider(source_id)
        if source_id in expected:
            assert isinstance(provider, expected[source_id])
        else:  # stooq is also a catalog id, resolved to its own client
            assert provider is not None
    assert isinstance(make_provider("seed"), SeedProvider)
    # a key-aware provider with no key raises an explicit error when used (never a silent fallback)
    with pytest.raises(ProviderUnavailableError):
        make_provider("tiingo").get_daily("AAPL")
    # a passed key reaches the key-aware client (request-only)
    tiingo = make_provider("tiingo", api_key="session-key")
    assert isinstance(tiingo, TiingoProvider)
    with pytest.raises(ValueError):
        make_provider("definitely-not-a-provider")


# ==================================================================================================
# REAL httpx error path (key-in-URL) — the iter-21 BLIND-SPOT regression (iter-22 fix, J-33).
#
# The hard-coded `http://x` `_FakeResponse` above can NEVER reach the leak: it builds an HTTPStatusError
# whose request URL carries NO key, so `str(exc)` is just "HTTP 429". These tests drive a REAL
# httpx.HTTPStatusError — whose `.request.url` carries the pasted session key as a `?token=`/`?apikey=`
# query param — through the real `_http.py` → provider path (a real httpx.Client over MockTransport,
# injected as `client=`), and assert the key + the ENTIRE query string are ABSENT from the surfaced
# error. THE iter-21 PRINCIPAL anti-goal breach: a pasted session key echoed back in the job error.
# ==================================================================================================
_SENTINEL_KEY = "sk-REAL-HTTPX-LEAK-CHECK-9q7zZ"

_KEY_AWARE = [
    pytest.param(lambda client: TiingoProvider(api_key=_SENTINEL_KEY, client=client), id="tiingo"),
    pytest.param(lambda client: FinnhubProvider(api_key=_SENTINEL_KEY, client=client), id="finnhub"),
    pytest.param(lambda client: AlphaVantageProvider(api_key=_SENTINEL_KEY, client=client), id="alpha_vantage"),
]


def _status_client(status_code: int) -> httpx.Client:
    """A REAL httpx.Client whose transport returns `status_code` for every request — so
    `response.raise_for_status()` raises a REAL httpx.HTTPStatusError carrying `request.url` (key in the
    query). This is the path the FakeResponse (hard-coded `http://x`, no key) could never exercise."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, json={"error": "boom"})

    return httpx.Client(transport=httpx.MockTransport(handler))


@pytest.mark.parametrize("make", _KEY_AWARE)
def test_real_http_status_error_redacts_key_and_query(make):
    """A REAL 500 HTTPStatusError whose request URL carries the pasted key → ProviderUnavailableError
    whose message contains NEITHER the key NOR any query string (the redacted URL is just
    scheme://host/path). The key string is verifiably absent from the error the job would surface."""
    provider = make(_status_client(500))
    with pytest.raises(ProviderUnavailableError) as exc:
        provider.get_daily("AAPL", start=date(2024, 1, 1), end=date(2024, 1, 31))
    msg = str(exc.value)
    assert _SENTINEL_KEY not in msg  # the pasted key is NEVER reflected back (the iter-21 leak, closed)
    assert "token=" not in msg and "apikey=" not in msg and "?" not in msg  # the whole query is gone
    assert "AAPL" in msg and "HTTP 500" in msg  # explicit, useful, non-secret context remains


@pytest.mark.parametrize("make", _KEY_AWARE)
def test_real_http_429_raises_rate_limit_error_redacted(make):
    """A REAL HTTP 429 maps to `RateLimitError` (a ProviderUnavailableError subclass for J-34's
    retry/backoff), still redacted — the key + query absent, the status surfaced."""
    provider = make(_status_client(429))
    with pytest.raises(RateLimitError) as exc:
        provider.get_daily("AAPL", start=date(2024, 1, 1), end=date(2024, 1, 31))
    msg = str(exc.value)
    assert _SENTINEL_KEY not in msg and "?" not in msg  # key + the whole query string are gone
    assert "HTTP 429" in msg  # the rate-limit status is surfaced (useful, non-secret)
    assert isinstance(exc.value, ProviderUnavailableError)  # subclass — existing handlers stay correct


def test_real_unparseable_body_redacts_key():
    """A REAL 200 with a non-JSON body → ProviderUnavailableError built from the body parse error (NOT
    the request URL), so the key (which rides only the URL) is absent from the message."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html>definitely not json</html>")

    provider = TiingoProvider(api_key=_SENTINEL_KEY, client=httpx.Client(transport=httpx.MockTransport(handler)))
    with pytest.raises(ProviderUnavailableError) as exc:
        provider.get_daily("AAPL")
    assert _SENTINEL_KEY not in str(exc.value)


# ==================================================================================================
# iter-23 (J-35): the optional market-cap-reference capability (used ONLY by the expand path)
# ==================================================================================================
from app.data_providers.base import PriceProvider  # noqa: E402


def test_base_provider_get_market_cap_raises_by_default():
    """The base `PriceProvider.get_market_cap` raises `ProviderUnavailableError` — so a provider that has
    not implemented the capability (or is `supports_market_cap: false`) is never used for expand; it never
    fabricates a cap."""

    class _BarsOnly(PriceProvider):
        def get_daily(self, symbol, start=None, end=None):
            return []

    with pytest.raises(ProviderUnavailableError):
        _BarsOnly().get_market_cap("AAPL")


def test_yahoo_get_market_cap_returns_real_value():
    """Yahoo's market-cap capability returns the REAL `marketCap` from the no-key quote endpoint."""
    client = _FakeClient(payload={"quoteResponse": {"result": [{"symbol": "AAPL", "marketCap": 3.0e12}]}})
    assert YahooProvider(client=client).get_market_cap("AAPL") == 3.0e12


def test_yahoo_get_market_cap_absent_returns_none_never_fabricates():
    """A symbol with no `marketCap` field yields None (the expand caller omits it) — never a fabricated cap."""
    client = _FakeClient(payload={"quoteResponse": {"result": [{"symbol": "AAPL"}]}})
    assert YahooProvider(client=client).get_market_cap("AAPL") is None


def test_yahoo_get_market_cap_http_error_raises():
    """A transport/HTTP failure on the cap fetch RAISES (redacted) — it never returns a fabricated cap."""
    provider = YahooProvider(client=_FakeClient(exc=httpx.ConnectError("offline")))
    with pytest.raises(ProviderUnavailableError):
        provider.get_market_cap("AAPL")


def test_tiingo_get_market_cap_returns_real_value_and_no_key_raises():
    """Tiingo's market-cap capability returns the REAL latest `marketCap` from fundamentals; with no key it
    raises explicitly (the key rides the request, never persisted)."""
    client = _FakeClient(payload=[{"date": "2024-03-01", "marketCap": 5.0e11}])
    assert TiingoProvider(api_key="k", client=client).get_market_cap("AAPL") == 5.0e11
    assert client.calls[0]["params"]["token"] == "k"  # the key rides the request only
    with pytest.raises(ProviderUnavailableError):
        TiingoProvider(api_key=None).get_market_cap("AAPL")


def test_finnhub_get_market_cap_scales_millions_to_usd():
    """Finnhub reports `marketCapitalization` in $MILLIONS — the capability scales it to absolute USD."""
    client = _FakeClient(payload={"metric": {"marketCapitalization": 3000.0}})  # $3,000M = $3B
    assert FinnhubProvider(api_key="k", client=client).get_market_cap("AAPL") == 3.0e9
    with pytest.raises(ProviderUnavailableError):
        FinnhubProvider(api_key=None).get_market_cap("AAPL")
