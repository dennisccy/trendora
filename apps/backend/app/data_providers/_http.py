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

from app.data_providers.base import ProviderUnavailableError

# Network timeout — NOT a scoring tunable (data_providers/ is I/O, not calc code, and is excluded from
# the no-magic-numbers contract), mirroring `stooq_provider._HTTP_TIMEOUT_SECONDS`.
HTTP_TIMEOUT_SECONDS = 15.0


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
    """GET `url` and parse the response body as JSON, or RAISE `ProviderUnavailableError`. `label` names
    the provider in the error; `symbol` is the requested ticker (included for an explicit message)."""
    try:
        if client is not None:
            response = client.get(url, params=params, headers=headers, timeout=timeout)
        else:
            response = httpx.get(url, params=params, headers=headers, timeout=timeout)
        response.raise_for_status()
    except httpx.HTTPError as exc:  # connect/timeout/non-2xx status — surface, never fabricate
        raise ProviderUnavailableError(f"{label} request failed for {symbol!r}: {exc}") from exc
    try:
        return response.json()
    except (ValueError, TypeError) as exc:  # non-JSON / unparseable body — surface, never fabricate
        raise ProviderUnavailableError(
            f"{label} returned an unparseable body for {symbol!r}: {exc}"
        ) from exc
