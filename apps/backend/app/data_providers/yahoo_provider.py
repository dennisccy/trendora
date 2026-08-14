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
from typing import Optional, Sequence

import httpx

from app.data_providers._http import HTTP_TIMEOUT_SECONDS, _provider_error, fetch_json
from app.data_providers.base import Bar, PriceProvider, ProviderUnavailableError, RateLimitError

# Yahoo Finance public chart endpoint (no key). Yahoo uses bare US tickers and keeps the caret for
# indices (e.g. `AAPL`, `SPY`, `^VIX`) — the SAME symbols Trendora uses internally, so no remapping.
_YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/"
# Yahoo Finance public quote endpoint (no key) — the J-35 market-cap reference source (`marketCap`).
_YAHOO_QUOTE_URL = "https://query1.finance.yahoo.com/v7/finance/quote"
# The no-key cookie + crumb endpoints (J-84): visiting the site sets the A1/A3 cookie, then the crumb
# (an anti-CSRF token, NOT a credential) authorizes `/v7/finance/quote` to return `marketCap`. The crumb
# is acquired at RUNTIME ONLY and is NEVER stored/logged/committed (anti-goal: No secrets in source).
_YAHOO_COOKIE_URL = "https://finance.yahoo.com/"
_YAHOO_CRUMB_URL = "https://query1.finance.yahoo.com/v1/test/getcrumb"
# A browser-like UA avoids Yahoo's bare-client 403; it carries no credential.
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; Trendora/1.0)"}
# The browser-like UA the cookie+crumb flow needs (the bare `Trendora/1.0` UA gets a 401 on the crumb).
# Mirrors the committed `screen_universe.py` runbook; carries NO credential.
_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "Accept": "application/json,text/plain,*/*",
    "Accept-Language": "en-US,en;q=0.9",
}
# HTTP statuses that, on the SHARED cookie/crumb acquisition or the batched quote, are a SYSTEMIC
# auth/limit failure of the whole cap batch (not a per-candidate absence) → `RateLimitError` so the
# expand pauses *resumable* (J-84). 401 = Yahoo rejecting the un-authenticated/expired crumb; 429 = the
# rate limit. IETF protocol status codes (like 404/503), NOT scoring tunables (`data_providers/` is I/O,
# excluded from the no-magic-numbers contract — same basis as `_http._HTTP_TOO_MANY_REQUESTS`).
_HTTP_UNAUTHORIZED = 401
_HTTP_TOO_MANY_REQUESTS = 429
# Symbols per `/v7/finance/quote` request — kept modest to be polite to the no-key API (the named
# module constant pattern of `screen_universe.QUOTE_BATCH = 40`; `data_providers/` I/O, not calc code).
QUOTE_BATCH = 40


class YahooProvider(PriceProvider):
    def __init__(self, *, client: Optional[httpx.Client] = None, timeout: float = HTTP_TIMEOUT_SECONDS):
        self._client = client
        self._timeout = timeout
        # Cookie+crumb are acquired ONCE per provider session and reused across the whole cap batch
        # (J-84). Cached in memory only — NEVER persisted/logged/committed. `_owns_client` tracks a
        # client we created lazily (so the cookie jar survives between the cookie GET and the quote GET)
        # so we can close it; an INJECTED client (tests) is never closed by us.
        self._crumb: Optional[str] = None
        self._owns_client = False

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
        """REAL market-cap reference for ONE symbol (J-35 expand capability, behind the same abstraction;
        yahoo is `supports_market_cap: true`). Authenticates with the no-key cookie+crumb flow (acquired
        ONCE per provider session, reused), reads Yahoo's quote endpoint and returns the real `marketCap`
        (a positive float), or `None` when the field is absent for the symbol (the expand caller omits that
        candidate with `no_market_cap` — never fabricates a cap). A SYSTEMIC auth/limit failure (cookie/
        crumb acquisition, or a 401/429 on the quote) RAISES `RateLimitError`; any other transport/HTTP
        failure RAISES `ProviderUnavailableError` (built from a REDACTED URL by `_http.fetch_json`, so no
        credential/crumb can leak). NOTE: live Yahoo market-cap egress is rate-limited for this host
        (MEMORY: data-provider-access-constraints) — the expand machinery is proven offline with an
        injected provider; this live path records NA/rate-limited honestly when walled.

        The expand path uses the BATCHED `get_market_caps` (cookie+crumb once, many symbols per request);
        this single-symbol method delegates to it so both share the one authenticated code path."""
        return self.get_market_caps([symbol]).get(symbol)

    def get_market_caps(self, symbols: Sequence[str]) -> dict[str, Optional[float]]:
        """BATCHED REAL market caps (J-84). Acquire the no-key cookie + crumb ONCE for this provider
        session (a persistent client so the cookie jar survives between the cookie GET and the quote GET),
        then call `/v7/finance/quote?symbols=…&crumb=…` in batches of `QUOTE_BATCH`. Returns
        `{symbol: REAL cap | None}`: a symbol present in a 200 WITH a positive `marketCap` → that float;
        a symbol present-but-without one → `None` (a per-candidate absence → `no_market_cap`; NEVER
        fabricated). A SYSTEMIC failure — the cookie/crumb step failing, or the batched quote returning a
        persistent 401/429 — RAISES `RateLimitError`, flowing through the expand's resumable-pause branch
        (a whole-batch auth outage is NOT silently recorded as "every candidate omitted"). The crumb rides
        as a query param, so any error is built from the REDACTED URL — the crumb/cookie never leaks."""
        client, created = self._ensure_client()
        try:
            crumb = self._ensure_crumb(client)
            caps: dict[str, Optional[float]] = {}
            syms = list(symbols)
            for i in range(0, len(syms), QUOTE_BATCH):
                batch = syms[i:i + QUOTE_BATCH]
                caps.update(self._fetch_cap_batch(client, batch, crumb))
            # a symbol Yahoo did not return at all is an honest per-candidate absence (→ None), never fab
            for sym in syms:
                caps.setdefault(sym, None)
            return caps
        finally:
            if created:
                client.close()
                self._owns_client = False

    def _ensure_client(self) -> tuple[httpx.Client, bool]:
        """Return `(client, created)`. An INJECTED client (tests) is reused as-is and never closed by us;
        otherwise we lazily create ONE persistent client (follow_redirects so the cookie jar survives the
        302 from `finance.yahoo.com/`) and report `created=True` so the caller closes it after the batch."""
        if self._client is not None:
            return self._client, False
        client = httpx.Client(follow_redirects=True, timeout=self._timeout)
        self._owns_client = True
        return client, True

    def _ensure_crumb(self, client: httpx.Client) -> str:
        """Acquire the no-key cookie + crumb ONCE (cached on the instance, reused across the batch). Visit
        `finance.yahoo.com/` to set the A1/A3 cookie, then GET `/v1/test/getcrumb` with a browser-like UA.
        A 401/429 on either step — or an empty/throttled crumb body — is a SYSTEMIC auth/limit failure →
        `RateLimitError` (NOT a per-candidate absence) so the expand pauses resumable. The crumb is held in
        memory only and NEVER stored/logged/committed; it is NOT embedded in any raised error."""
        if self._crumb is not None:
            return self._crumb
        # 1) set the cookie (a 401/429 here means Yahoo is walling us systemically)
        try:
            cookie_resp = client.get(_YAHOO_COOKIE_URL, headers=_BROWSER_HEADERS, timeout=self._timeout)
        except httpx.HTTPError as exc:  # connect/timeout — surface, never fabricate (no crumb in the msg)
            raise ProviderUnavailableError(f"yahoo cookie acquisition failed: {type(exc).__name__}") from exc
        self._raise_if_systemic(cookie_resp.status_code, "cookie")
        # 2) get the crumb (a 401/429 / empty body is the systemic auth failure)
        try:
            crumb_resp = client.get(_YAHOO_CRUMB_URL, headers=_BROWSER_HEADERS, timeout=self._timeout)
        except httpx.HTTPError as exc:
            raise ProviderUnavailableError(f"yahoo crumb acquisition failed: {type(exc).__name__}") from exc
        self._raise_if_systemic(crumb_resp.status_code, "crumb")
        crumb = (crumb_resp.text or "").strip()
        if not crumb or "Too Many" in crumb:  # empty / throttled body → systemic, pause resumable
            raise RateLimitError("yahoo crumb acquisition failed: empty or throttled crumb")
        self._crumb = crumb  # cache for reuse across the batch (in memory only — never persisted)
        return crumb

    @staticmethod
    def _raise_if_systemic(status_code: int, step: str) -> None:
        """A 401/429 on a SHARED cookie/crumb/quote step is a whole-batch auth/limit failure →
        `RateLimitError` (the expand pauses resumable). No URL/crumb is embedded — just the status + step."""
        if status_code in (_HTTP_UNAUTHORIZED, _HTTP_TOO_MANY_REQUESTS):
            raise RateLimitError(f"yahoo market-cap {step} systemic auth/limit failure: HTTP {status_code}")

    def _fetch_cap_batch(
        self, client: httpx.Client, batch: Sequence[str], crumb: str
    ) -> dict[str, Optional[float]]:
        """One batched `/v7/finance/quote` request WITH the crumb. A 401 or 429 is a SYSTEMIC auth/limit
        failure → `RateLimitError` (so the expand pauses resumable — a whole-batch auth outage is never
        recorded as "every candidate omitted"); any other transport/HTTP error → `ProviderUnavailableError`.
        BOTH error messages are built from the REDACTED URL (`_provider_error` strips the entire query
        string, so the `crumb=…` param can NEVER leak). Returns `{symbol: cap | None}` for the symbols
        Yahoo returned in the 200 body (a present-but-capless symbol → `None`)."""
        params = {"symbols": ",".join(batch), "crumb": crumb}
        label = f"batch of {len(batch)}"
        try:
            response = client.get(_YAHOO_QUOTE_URL, params=params, headers=_BROWSER_HEADERS, timeout=self._timeout)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:  # a status error carries a response → classify 401/429 systemic
            status = exc.response.status_code if exc.response is not None else None
            if status in (_HTTP_UNAUTHORIZED, _HTTP_TOO_MANY_REQUESTS):
                # re-route through `_provider_error` for the REDACTED URL, then force `RateLimitError`
                # (a 401 on the quote is systemic too — `_http` only maps 429, so we wrap it here).
                base = _provider_error(exc, url=_YAHOO_QUOTE_URL, symbol=label, label="yahoo")
                raise RateLimitError(str(base)) from exc
            raise _provider_error(exc, url=_YAHOO_QUOTE_URL, symbol=label, label="yahoo") from exc
        except httpx.HTTPError as exc:  # connect/timeout — surface (redacted), never fabricate
            raise _provider_error(exc, url=_YAHOO_QUOTE_URL, symbol=label, label="yahoo") from exc
        try:
            data = response.json()
        except (ValueError, TypeError) as exc:  # non-JSON body — surface, never fabricate (no URL leaked)
            raise ProviderUnavailableError(f"yahoo returned an unparseable quote body for {label}: {exc}") from exc
        try:
            results = data["quoteResponse"]["result"]  # type: ignore[index]
        except (KeyError, IndexError, TypeError) as exc:  # unexpected shape — surface, never fabricate
            raise ProviderUnavailableError(f"yahoo quote unparseable for {label}: {exc}") from exc
        out: dict[str, Optional[float]] = {}
        for row in results or []:
            if not isinstance(row, dict):
                continue
            sym = row.get("symbol")
            if not sym:
                continue
            out[sym] = self._parse_cap(row.get("marketCap"))
        return out

    @staticmethod
    def _parse_cap(cap: object) -> Optional[float]:
        """A raw `marketCap` value → a positive float, or `None` (absent/malformed/non-positive) — the
        caller omits that candidate `no_market_cap`, never fabricating a cap."""
        if cap is None:
            return None
        try:
            value = float(cap)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return None  # malformed cap → treat as absent (omit + log), never fabricate
        return value if value > 0 else None

    def _parse(self, symbol: str, data: object, start: Optional[date_cls], end: Optional[date_cls]) -> list[Bar]:
        try:
            chart = data["chart"]  # type: ignore[index]
            if chart.get("error"):
                raise ProviderUnavailableError(f"yahoo returned an error for {symbol!r}: {chart['error']}")
            result = chart["result"]
            if not result:
                raise ProviderUnavailableError(f"yahoo returned no result for {symbol!r}")
            block = result[0]
            # A range Yahoo HAS no rows for is answered as a WELL-FORMED success, not an error: HTTP 200,
            # `chart.error: null`, one `result` entry carrying a real `meta` (and an `indicators` object)
            # but NO `timestamp` array at all. Reading `block["timestamp"]` straight through raised a bare
            # `KeyError` that the handler below relabelled "yahoo response unparseable for 'X': 'timestamp'"
            # — reporting a PROVIDER FAULT for a provider that answered correctly. Live-confirmed on
            # 2026-08-14 for `^DXY` (a defunct quote: `firstTradeDate: null`, last market time in 2019) and
            # `SATS` (listed too recently to have rows in the window); `EA` hit the same path intermittently
            # whenever a requested window happened to precede its available rows. All three counted toward a
            # job's failed-symbol tally and its "N errors" banner.
            #
            # Zero rows is the honest answer here — the symbol simply has no bars in `[start, end]` — so
            # return no bars rather than raising. `.get(...)` falsiness covers all three empty shapes
            # (key absent, `null`, `[]`) identically. This deliberately does NOT soften any other failure:
            # a Yahoo-reported `chart.error`, a missing/empty `result`, an HTTP error (`fetch_json` raises
            # before this is reached), or a block that HAS timestamps but malformed quote arrays all still
            # surface exactly as before.
            if not block.get("timestamp"):
                return []
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
