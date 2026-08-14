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
    def __init__(self, payload=None, *, status_code: int = 200, text: str = "", url: str = "http://x"):
        self._payload = payload
        self.status_code = status_code
        self.text = text
        self._url = url

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            # carry a REAL request + response so a caller can read `exc.response.status_code` (J-84's
            # systemic 401/429 classification) and so the redaction (`_redacted_url`) has a URL to strip.
            request = httpx.Request("GET", self._url)
            raise httpx.HTTPStatusError(
                f"HTTP {self.status_code}", request=request,
                response=httpx.Response(self.status_code, request=request),
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


# --------------------------------------------------------------------------------------------------
# A range with NO rows is a successful empty answer, never a provider fault.
#
# Yahoo answers a window it has no data for with a WELL-FORMED success — HTTP 200, `chart.error: null`,
# one `result` entry carrying a real `meta`/`indicators` but NO `timestamp` array. Reading `timestamp`
# straight through raised a bare KeyError that surfaced to the operator as
# "yahoo response unparseable for 'X': 'timestamp'", counting a correct provider answer as a failed
# symbol. Live-confirmed 2026-08-14 against `^DXY` (defunct quote: `firstTradeDate: null`), `SATS`
# (listed after the requested window) and intermittently `EA`.
# --------------------------------------------------------------------------------------------------
_YAHOO_EMPTY_WINDOW = {
    "chart": {"error": None, "result": [{
        # the exact shape Yahoo returned for ^DXY / SATS: meta + indicators present, timestamp absent
        "meta": {"symbol": "SATS", "instrumentType": "EQUITY", "dataGranularity": "1d"},
        "indicators": {"adjclose": [{}], "quote": [{}]},
    }]}
}


@pytest.mark.parametrize("block", [
    # key absent entirely — the live ^DXY / SATS shape
    {"meta": {"symbol": "X"}, "indicators": {"quote": [{}]}},
    # explicit null
    {"meta": {"symbol": "X"}, "timestamp": None, "indicators": {"quote": [{}]}},
    # empty array
    {"meta": {"symbol": "X"}, "timestamp": [], "indicators": {"quote": [{}]}},
])
def test_yahoo_range_with_no_rows_returns_no_bars_not_an_error(block):
    """THE REGRESSION: all three empty shapes mean the same thing — the symbol has no bars in the
    requested window — and none of them is a provider fault."""
    provider = YahooProvider(client=_FakeClient(payload={"chart": {"error": None, "result": [block]}}))
    assert provider.get_daily("SATS", start=date(2026, 8, 3), end=date(2026, 8, 14)) == []


def test_yahoo_empty_window_live_shape_returns_no_bars():
    """The captured live payload verbatim, so the fix is pinned to what Yahoo actually sends."""
    provider = YahooProvider(client=_FakeClient(payload=_YAHOO_EMPTY_WINDOW))
    assert provider.get_daily("SATS", start=date(2026, 8, 3), end=date(2026, 8, 14)) == []


def test_yahoo_genuinely_malformed_rows_still_raise():
    """The empty-window allowance must not soften a REAL malformation: a block that HAS timestamps but
    broken quote arrays is still an honest `unparseable`, exactly as before."""
    payload = {"chart": {"error": None, "result": [{
        "timestamp": [_unix(date(2024, 1, 2))],
        "indicators": {"quote": [{"open": [1.0]}]},  # high/low/close/volume missing
    }]}}
    with pytest.raises(ProviderUnavailableError) as exc:
        YahooProvider(client=_FakeClient(payload=payload)).get_daily("AAPL")
    assert "unparseable" in str(exc.value)


def test_yahoo_reported_error_and_empty_result_still_raise():
    """The other two failure branches are untouched — an empty window is distinguished from Yahoo saying
    it failed, and from a response carrying no result block at all."""
    with pytest.raises(ProviderUnavailableError):
        YahooProvider(
            client=_FakeClient(payload={"chart": {"error": "Not Found", "result": [{"meta": {}}]}})
        ).get_daily("ZZZZ")
    with pytest.raises(ProviderUnavailableError):
        YahooProvider(client=_FakeClient(payload={"chart": {"error": None, "result": []}})).get_daily("ZZZZ")


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


def test_make_provider_seed_honors_overlay_env_dir(tmp_path, monkeypatch):
    """iter-26: the env-gated offline `seed` import source reads its seed dir from `TRENDORA_SEED_IMPORT_DIR`
    when set (the throwaway QA overlay carrying a `market_caps.csv` for an OFFLINE J-35 expand) — never
    the committed seed tree. An explicit `seed_dir=` still wins; unset → the committed default."""
    from app.data_providers import DEFAULT_SEED_DIR, SEED_IMPORT_DIR_ENV
    from app.data_providers.seed_provider import SeedProvider

    overlay = tmp_path / "overlay"
    (overlay / "prices").mkdir(parents=True)
    monkeypatch.setenv(SEED_IMPORT_DIR_ENV, str(overlay))
    p = make_provider("seed")
    assert isinstance(p, SeedProvider) and p.seed_dir == overlay  # overlay env dir honored
    # an explicit seed_dir wins over the env override
    other = tmp_path / "explicit"
    (other / "prices").mkdir(parents=True)
    assert make_provider("seed", seed_dir=other).seed_dir == other
    # unset → the committed default seed dir
    monkeypatch.delenv(SEED_IMPORT_DIR_ENV, raising=False)
    assert make_provider("seed").seed_dir == DEFAULT_SEED_DIR


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


def test_base_provider_get_market_caps_default_is_none_fallback():
    """The base BATCHED `get_market_caps` returns `None` to mean "no batch capability — fall back to the
    per-symbol path" (J-84). It does NOT raise — a per-symbol provider keeps its per-candidate semantics."""

    class _BarsOnly(PriceProvider):
        def get_daily(self, symbol, start=None, end=None):
            return []

    assert _BarsOnly().get_market_caps(["AAPL", "MSFT"]) is None


# --------------------------------------------------------------------------------------------------
# J-84: Yahoo market-cap via the no-key cookie + crumb flow (batched), with systemic-failure classifying.
# --------------------------------------------------------------------------------------------------
_YAHOO_COOKIE = "https://finance.yahoo.com/"
_YAHOO_CRUMB = "https://query1.finance.yahoo.com/v1/test/getcrumb"
_YAHOO_QUOTE = "https://query1.finance.yahoo.com/v7/finance/quote"


class _YahooCapClient:
    """A URL-aware fake httpx client for the J-84 cookie→crumb→quote flow. Each URL gets its own canned
    response (status + text/JSON). Records every GET so a test can assert the cookie+crumb are fetched
    ONCE and reused across the batch, and that the quote carries `crumb=…`."""

    def __init__(self, *, crumb_status=200, crumb_text="CRUMB-XYZ", quote_status=200, quote_payload=None,
                 cookie_status=200):
        self._crumb_status = crumb_status
        self._crumb_text = crumb_text
        self._quote_status = quote_status
        self._quote_payload = quote_payload if quote_payload is not None else {"quoteResponse": {"result": []}}
        self._cookie_status = cookie_status
        self.calls: list[dict] = []

    def get(self, url, params=None, headers=None, timeout=None):
        self.calls.append({"url": url, "params": params, "headers": headers})
        if url == _YAHOO_COOKIE:
            return _FakeResponse(None, status_code=self._cookie_status, url=url)
        if url == _YAHOO_CRUMB:
            return _FakeResponse(None, status_code=self._crumb_status, text=self._crumb_text, url=url)
        if url == _YAHOO_QUOTE:
            return _FakeResponse(self._quote_payload, status_code=self._quote_status, url=url)
        raise AssertionError(f"unexpected URL {url!r}")

    def url_calls(self, url):
        return [c for c in self.calls if c["url"] == url]


def test_yahoo_get_market_caps_cookie_crumb_flow_batched_with_crumb():
    """J-84 cookie→crumb→quote flow: the cookie (`finance.yahoo.com`) then the crumb (`/v1/test/getcrumb`)
    are fetched, then `/v7/finance/quote` is called WITH `crumb=…` for the BATCH. A 200 with `marketCap` →
    a real float; a 200 without it → None (absent, never fabricated)."""
    payload = {"quoteResponse": {"result": [
        {"symbol": "AAPL", "marketCap": 3.0e12},
        {"symbol": "MSFT"},  # present but capless → None
    ]}}
    client = _YahooCapClient(quote_payload=payload)
    caps = YahooProvider(client=client).get_market_caps(["AAPL", "MSFT", "NVDA"])
    assert caps["AAPL"] == 3.0e12
    assert caps["MSFT"] is None  # present-but-capless → absent, never fabricated
    assert caps["NVDA"] is None  # not returned by Yahoo at all → absent, never fabricated
    # the quote carried the crumb
    quote_call = client.url_calls(_YAHOO_QUOTE)[0]
    assert quote_call["params"]["crumb"] == "CRUMB-XYZ"
    assert quote_call["params"]["symbols"] == "AAPL,MSFT,NVDA"  # batched in one request


def test_yahoo_get_market_caps_acquires_cookie_crumb_once_reused_across_batch():
    """J-84: the cookie + crumb are acquired ONCE per provider session and reused across the whole batch —
    a SECOND `get_market_caps` (or a second batch) does NOT re-fetch the crumb (the instance caches it)."""
    payload = {"quoteResponse": {"result": [{"symbol": "AAPL", "marketCap": 3.0e12}]}}
    provider = YahooProvider(client=_YahooCapClient(quote_payload=payload))
    provider.get_market_caps(["AAPL"])
    provider.get_market_caps(["AAPL"])
    client = provider._client
    assert len(client.url_calls(_YAHOO_CRUMB)) == 1  # crumb fetched once, reused on the second call
    assert len(client.url_calls(_YAHOO_COOKIE)) == 1


def test_yahoo_get_market_cap_single_delegates_to_batched():
    """The single-symbol `get_market_cap` delegates to the batched cookie+crumb path (one auth code path)."""
    payload = {"quoteResponse": {"result": [{"symbol": "AAPL", "marketCap": 3.0e12}]}}
    assert YahooProvider(client=_YahooCapClient(quote_payload=payload)).get_market_cap("AAPL") == 3.0e12


def test_yahoo_get_market_cap_absent_returns_none_never_fabricates():
    """A symbol with no `marketCap` field yields None (the expand caller omits it) — never a fabricated cap."""
    payload = {"quoteResponse": {"result": [{"symbol": "AAPL"}]}}
    assert YahooProvider(client=_YahooCapClient(quote_payload=payload)).get_market_cap("AAPL") is None


def test_yahoo_get_market_caps_systemic_401_on_crumb_raises_rate_limit():
    """J-84 systemic classification: a 401 on the SHARED crumb acquisition is a whole-batch auth failure →
    `RateLimitError` (the expand pauses resumable — NOT a per-candidate omission, NOT a fabricated cap)."""
    client = _YahooCapClient(crumb_status=401)
    with pytest.raises(RateLimitError):
        YahooProvider(client=client).get_market_caps(["AAPL", "MSFT"])


def test_yahoo_get_market_caps_empty_crumb_body_is_systemic_rate_limit():
    """An empty / throttled crumb body (200 but no token) is a systemic auth/limit failure → RateLimitError."""
    client = _YahooCapClient(crumb_text="   ")
    with pytest.raises(RateLimitError):
        YahooProvider(client=client).get_market_caps(["AAPL"])


def test_yahoo_get_market_caps_systemic_401_on_quote_raises_rate_limit_redacted():
    """J-84: a 401 on the BATCHED quote (after a good crumb) is also systemic → `RateLimitError`, and the
    error is built from the REDACTED URL so the `crumb=…` query param can NEVER leak."""
    client = _YahooCapClient(quote_status=401)
    with pytest.raises(RateLimitError) as exc:
        YahooProvider(client=client).get_market_caps(["AAPL", "MSFT"])
    msg = str(exc.value)
    assert "CRUMB-XYZ" not in msg and "crumb=" not in msg and "?" not in msg  # the crumb never leaks
    assert "HTTP 401" in msg  # the systemic status is surfaced (useful, non-secret)


def test_yahoo_get_market_caps_systemic_429_on_quote_raises_rate_limit():
    """A 429 on the batched quote is systemic → RateLimitError (the existing rate-limit pause path)."""
    client = _YahooCapClient(quote_status=429)
    with pytest.raises(RateLimitError):
        YahooProvider(client=client).get_market_caps(["AAPL"])


def test_yahoo_get_market_cap_http_error_raises():
    """A transport/HTTP failure on the cap fetch RAISES — it never returns a fabricated cap."""
    provider = YahooProvider(client=_YahooCapClient(quote_status=500))
    with pytest.raises(ProviderUnavailableError):
        provider.get_market_cap("AAPL")


def test_yahoo_get_market_caps_unparseable_quote_body_raises():
    """A 200 quote with an unparseable body → ProviderUnavailableError (surfaced, never fabricated)."""
    client = _YahooCapClient(quote_payload=_UNPARSEABLE)
    with pytest.raises(ProviderUnavailableError):
        YahooProvider(client=client).get_market_caps(["AAPL"])


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
