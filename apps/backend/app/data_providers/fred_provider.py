"""FRED macro-feed provider (iter-32, J-92).

A STANDALONE macro provider — distinct from the OHLCV price providers — that fetches configured FRED
macro series (yield-curve 10y-2y inversion, unemployment trend, credit spreads, …) into the additive
`MacroSeries` table. It is registered in `make_provider` like the OHLCV providers, but its capability is
macro observations (`get_macro_series`), NOT daily bars.

KEY HANDLING (anti-goals: No secrets in source; Import keys are env-or-session, never persisted): the
FRED key is read FROM THE ENVIRONMENT ONLY (the `api_key` argument the engine resolves from the env-var
NAME in `config.macro.env_var`). It is held in memory for the request only — never written to disk, the
DB, the run log, any committed file, or echoed back in any response. A FRED provider constructed with no
`api_key` RAISES `ProviderUnavailableError` when used — never a silent fallback, never a fabricated value.

DATA HONESTY (anti-goals: No fabricated data; Live fetch is real-data-only): on any transport/HTTP
failure it RAISES `ProviderUnavailableError` (or `RateLimitError` on a 429) — it MUST NOT synthesize a
macro value. A walled provider / an uncommitted series therefore flows through to an honest blocked-NA
state; it never fabricates a value to force a green journey.

The live FRED pull is data-dependent / NON-HALTING — the committed macro seed makes every macro-conditioned
feature fully testable OFFLINE; only the live refresh is data-gated and honestly blocked-NA.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date as date_cls, datetime
from typing import Optional

from app.data_providers._http import fetch_json
from app.data_providers.base import (
    Bar,
    PriceProvider,
    ProviderUnavailableError,
)

# The FRED observations endpoint (the host + path only — the key is a request-time query param, never
# committed). A fixed structural constant (the API base URL), not a tunable scoring value.
_FRED_OBSERVATIONS_URL = "https://api.stlouisfed.org/fred/series/observations"
# FRED's sentinel for a missing observation value (a period with no reading). Excluded, never fabricated.
_FRED_MISSING_VALUE = "."


@dataclass(frozen=True)
class MacroObservation:
    """One macro observation: the reference `date`, the raw `value`, and the `published_date` it became
    public (`reference_date + publication_lag_days`, supplied by the caller from config). Frozen so
    equality is by value (supports determinism tests)."""

    date: date_cls
    value: float
    published_date: date_cls


class FredProvider(PriceProvider):
    """The FRED macro provider. `get_daily` is NOT a FRED capability (macro series are not OHLCV bars) —
    it raises `ProviderUnavailableError` so a misrouted price fetch never silently returns nothing. The
    macro capability is `get_macro_series`, used ONLY by the J-92 macro-feed path."""

    def __init__(self, api_key: Optional[str] = None, *, client=None) -> None:
        # the key is held in memory for THIS request only — never persisted/logged/echoed (anti-goal).
        self._api_key = api_key
        # an injectable httpx-like client for tests (a fake returning a canned body / raising a canned
        # error) — exactly like the OHLCV providers; the default (None) uses module-level httpx.get.
        self._client = client

    def get_daily(
        self,
        symbol: str,
        start: Optional[date_cls] = None,
        end: Optional[date_cls] = None,
    ) -> list[Bar]:
        """FRED serves macro observations, not OHLCV bars — raise rather than fabricate a bar. The OHLCV
        macro PROXIES (^TNX/^DXY/^VXN) are fetched via the configured OHLCV provider, not here."""
        raise ProviderUnavailableError(
            "FredProvider does not serve OHLCV bars (macro series only) — "
            f"requested {symbol!r}"
        )

    def get_macro_series(
        self,
        fred_series_id: str,
        publication_lag_days: int,
        *,
        start: Optional[date_cls] = None,
        end: Optional[date_cls] = None,
    ) -> list[MacroObservation]:
        """Fetch one FRED series' observations as `MacroObservation`s, sorted ascending by reference date.
        The key is sent ONLY as a request-time query param (never committed); a missing key RAISES
        `ProviderUnavailableError` (never a silent fallback). On a 429 it RAISES `RateLimitError`; on any
        other transport/HTTP failure it RAISES `ProviderUnavailableError` — it MUST NOT synthesize a value
        (anti-goals: No fabricated data; Live fetch is real-data-only). A FRED `.` (missing) observation is
        EXCLUDED, never fabricated. The error is built from the REDACTED URL so the key never leaks."""
        if not self._api_key:
            raise ProviderUnavailableError(
                "FredProvider requires a FRED API key (read from the environment) — none was provided; "
                "no macro value is fabricated"
            )
        params = {
            "series_id": fred_series_id,
            "api_key": self._api_key,
            "file_type": "json",
        }
        if start is not None:
            params["observation_start"] = start.isoformat()
        if end is not None:
            params["observation_end"] = end.isoformat()

        # `fetch_json` builds any error from a REDACTED URL (the key travels in `params`, never the endpoint
        # URL), and maps a 429 to `RateLimitError` — so the key never leaks and a rate-limit stays distinct.
        payload = fetch_json(
            _FRED_OBSERVATIONS_URL,
            symbol=fred_series_id,
            label="FRED",
            params=params,
            client=self._client,
        )

        observations = payload.get("observations") if isinstance(payload, dict) else None
        if not isinstance(observations, list):
            raise ProviderUnavailableError(
                f"FRED returned no observations for {fred_series_id!r} — no value is fabricated"
            )

        out: list[MacroObservation] = []
        for obs in observations:
            if not isinstance(obs, dict):
                continue
            raw_value = obs.get("value")
            raw_date = obs.get("date")
            if raw_value is None or raw_value == _FRED_MISSING_VALUE or raw_date is None:
                continue  # a missing observation is EXCLUDED, never fabricated
            try:
                ref_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
                value = float(raw_value)
            except (ValueError, TypeError):
                continue  # an unparseable row is skipped, never fabricated
            published = _add_calendar_days(ref_date, publication_lag_days)
            out.append(MacroObservation(date=ref_date, value=value, published_date=published))

        out.sort(key=lambda o: o.date)
        return out


def _add_calendar_days(d: date_cls, days: int) -> date_cls:
    """The publication date for a reference date + a calendar-day lag (`published_date = reference_date +
    publication_lag_days`). A value is usable for a causal date D only when `published_date <= D` — so the
    lag forbids using the reference-date value on D (forbidden lookahead). Pure date arithmetic."""
    from datetime import timedelta

    return d + timedelta(days=days)
