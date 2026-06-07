"""Shared HTTP helper for the live EOD provider clients (J-33).

A single documented GET that returns a parsed JSON body or RAISES `ProviderUnavailableError`. On ANY
failure — a network/timeout/HTTP-status error, or a body that is not valid JSON — it raises and returns
nothing; it NEVER hands back a partial/placeholder body to be turned into a fabricated bar (anti-goals:
No fabricated data / Live fetch is real-data-only). Imported LAZILY (only when a live provider is
constructed), so the app boot path pulls in no HTTP dependency. `client` is injectable for tests (a fake
returning a canned body / raising a canned error) — exactly like `StooqProvider`.
"""
from __future__ import annotations

from typing import Any, Optional

import httpx

from app.data_providers.base import ProviderUnavailableError, RateLimitError

# Network timeout — NOT a scoring tunable (data_providers/ is I/O, not calc code, and is excluded from
# the no-magic-numbers contract), mirroring `stooq_provider._HTTP_TIMEOUT_SECONDS`.
HTTP_TIMEOUT_SECONDS = 15.0

# HTTP "Too Many Requests" — an IETF protocol status code (like 404/503), NOT a scoring tunable; it
# distinguishes a rate-limit (retryable → resumable) from a generic failure (J-34).
_HTTP_TOO_MANY_REQUESTS = 429


def _redacted_url(exc: httpx.HTTPError, fallback: str) -> str:
    """The request URL with the ENTIRE query string + fragment stripped, or `fallback` (the static
    endpoint) when no request is attached. Stripping the whole query is key-AGNOSTIC — it covers
    `token` / `apikey` / any future credential param name — so a pasted session key (which travels as a
    URL query param) can NEVER reach the error message (anti-goal: Import keys are env-or-session, never
    persisted; this closes the iter-21 `str(httpx.HTTPStatusError)` leak). The redaction itself never
    raises (a malformed URL — or an `httpx.RequestError` with no request attached, whose `.request`
    property RAISES rather than returning None — falls back to the static endpoint, which is itself
    key-free: the credential travels in `params`, never in the endpoint URL passed to `fetch_json`)."""
    try:
        req = exc.request  # httpx's `.request` is a property that RAISES when unset, not returns None
    except (RuntimeError, AttributeError):
        req = None
    if req is not None:
        try:
            return str(req.url.copy_with(query=None, fragment=None))
        except Exception:  # pragma: no cover - defensive: never let redaction itself raise/leak
            pass
    return fallback


def _provider_error(exc: httpx.HTTPError, *, url: str, symbol: str, label: str) -> ProviderUnavailableError:
    """Build the surfaced error from a REDACTED request URL + HTTP status — NEVER `str(exc)` (which
    embeds the full request URL incl. the `?token=`/`?apikey=` query → the iter-21 key leak). Handles
    both `httpx.HTTPStatusError` (request + response → include `HTTP {status}`) and `httpx.RequestError`
    (a connect/timeout error: request present, no response → omit the status segment). A 429 maps to
    `RateLimitError` (a retryable rate-limit, distinct from a generic failure) — still redacted."""
    redacted = _redacted_url(exc, url)
    resp = getattr(exc, "response", None)
    status = resp.status_code if resp is not None else None
    status_seg = f"HTTP {status} at " if status is not None else ""
    message = f"{label} request failed for {symbol!r}: {status_seg}{redacted}"
    if status == _HTTP_TOO_MANY_REQUESTS:
        return RateLimitError(message)
    return ProviderUnavailableError(message)


def fetch_json(
    url: str,
    *,
    symbol: str,
    label: str,
    params: Optional[dict] = None,
    headers: Optional[dict] = None,
    client: Optional[httpx.Client] = None,
    timeout: float = HTTP_TIMEOUT_SECONDS,
) -> Any:
    """GET `url` and parse the response body as JSON, or RAISE `ProviderUnavailableError`
    (`RateLimitError` on HTTP 429). `label` names the provider in the error; `symbol` is the requested
    ticker. The error message is built from a REDACTED URL + status (see `_provider_error`) so a pasted
    session key in the query string is NEVER reflected back."""
    try:
        if client is not None:
            response = client.get(url, params=params, headers=headers, timeout=timeout)
        else:
            response = httpx.get(url, params=params, headers=headers, timeout=timeout)
        response.raise_for_status()
    except httpx.HTTPError as exc:  # connect/timeout/non-2xx status — surface (redacted), never fabricate
        raise _provider_error(exc, url=url, symbol=symbol, label=label) from exc
    try:
        return response.json()
    except (ValueError, TypeError) as exc:  # non-JSON / unparseable body — surface, never fabricate
        # `exc` here is a ValueError/TypeError from JSON parsing (no URL/query), but route it through the
        # same redaction-safe shape for consistency — the body's own content, never the request URL.
        raise ProviderUnavailableError(
            f"{label} returned an unparseable body for {symbol!r}: {exc}"
        ) from exc
