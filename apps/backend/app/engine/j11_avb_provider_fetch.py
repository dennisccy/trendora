"""app.engine.j11_avb_provider_fetch -- J-11 Stage D readiness (goal-market-compass iter-15, Goal 2): the
ONE bounded, read-only comparison fetch `docs/goal.md` AG-9's "Dated exception #2 -- AVB convention
diagnostic (owner, 2026-08-25 -- single-use, self-closing, DIAGNOSTIC ONLY)" authorizes.

The exception permits EXACTLY this and nothing else: symbol `AVB` only; dates `2026-08-05, 2026-08-06,
2026-08-07, 2026-08-10, 2026-08-11, 2026-08-12` -- six dates, none others, none inferred from a range or
cadence; fields `date`/`close`/`volume` only; via the canonical Yahoo provider path Trendora already uses
(`app.data_providers.yahoo_provider.YahooProvider`), so the comparison is like-for-like. This module is
the ONLY call site anywhere in this iteration's diff that calls `.get_daily`/`.get_adjusted_close` on a
live provider -- grep-verifiable, so "exactly one fetch" stays auditable
(`apps/backend/scripts/run_j11_avb_provider_fetch.py` constructs the real `YahooProvider` and is the only
place that imports it; every other new/changed module or script this iteration touches reads THIS
module's persisted output instead of ever constructing a provider itself).

This is NOT ingest and NOT recovery: `fetch_avb_provider_evidence` takes an INJECTED `PriceProvider`
(never constructs one -- so it stays unit-testable without a real network call), performs no database I/O
of any kind (no import of `app.db`/`sqlmodel.Session` anywhere in this file), and returns a plain dict for
the caller to persist wherever it chooses -- there is no write path to `daily_prices` or any other table
inside this module at all. J-10 is NOT reopened: the persisted J-10 bridge factor is read verbatim by the
caller (`app.engine.j11_avb_diagnostic.load_j10_avb_evidence`) and passed in here, never re-derived.

Fail-closed, per the amendment's own words ("If the provider cannot supply sufficient evidence, classify
honestly as AVB-D and stop -- do not guess, do not substitute adjacent-day statistics, and do not broaden
the fetch"): `fetch_avb_provider_evidence` catches `ProviderUnavailableError` (whose `RateLimitError`
subclass is therefore also caught) and NEVER lets it propagate past this function; any date short of a
full six-date return records `sufficient_evidence: false` and the SPECIFIC missing date(s) instead of
substituting anything. The whole `.get_daily` call happens exactly once per invocation of this function --
there is no retry loop, no per-date fetch, and no broadening of the requested window anywhere in this
file.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Optional

from app.data_providers.base import PriceProvider, ProviderUnavailableError

AVB_SYMBOL = "AVB"

# The exact six ISO dates AG-9's "Dated exception #2" authorizes -- a literal historical/contractual fact
# about THIS one-time diagnostic, never a range or cadence-derived list (same posture as
# `j11_maintenance.INCIDENT_DATES`/`j11_avb_diagnostic.CALIBRATION_DATES`/`RECOVERED_DATES` -- this is
# their exact union, restated here as its own literal so this module carries no import-time dependency on
# either for its own authorization boundary). `test_no_magic_numbers.py`'s `CALC_FILES` does not include
# this module (it is fetch/provenance plumbing, not scoring/decision calculation code).
PERMITTED_DATES: tuple[date, ...] = (
    date(2026, 8, 5),
    date(2026, 8, 6),
    date(2026, 8, 7),
    date(2026, 8, 10),
    date(2026, 8, 11),
    date(2026, 8, 12),
)
FETCH_WINDOW_START: date = PERMITTED_DATES[0]
FETCH_WINDOW_END: date = PERMITTED_DATES[-1]

# The comparison formulas the amendment requires be recorded as auditable provenance alongside the raw
# fetched values -- documentation only (the actual arithmetic is computed downstream, in
# `j11_avb_diagnostic.compute_provider_comparison`, against stored + fetched values together); recorded
# here, verbatim, so the fetch evidence artifact is self-describing even read in isolation.
COMPARISON_FORMULAS: dict = {
    "close_ratio": "stored_close / provider_close",
    "volume_ratio": "stored_volume / provider_volume",
    "expected_inverse_volume_ratio": "1 / bridge_factor",
    "stored_dollar_volume": "stored_close * stored_volume",
    "provider_dollar_volume": "provider_close * provider_volume",
    "dollar_volume_ratio": "stored_dollar_volume / provider_dollar_volume",
    "bridge_adjusted_compensation_test": (
        "dollar_volume_ratio ~= 1.0 implies price/volume rebasing COMPENSATE (dollar volume conserved); "
        "dollar_volume_ratio ~= bridge_factor implies volume was left RAW while only price was rebased"
    ),
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def fetch_avb_provider_evidence(provider: PriceProvider, *, bridge_factor: float) -> dict:
    """AG-9 dated exception #2's ONE authorized fetch. Calls `provider.get_daily(AVB_SYMBOL,
    start=FETCH_WINDOW_START, end=FETCH_WINDOW_END)` EXACTLY once. Any bar the provider returns outside
    `PERMITTED_DATES` is discarded (recorded in `discarded_dates_outside_permitted_set` for auditability,
    never used for anything). `bridge_factor` is the CALLER-supplied, already-persisted J-10 value (the
    caller reuses `j11_avb_diagnostic.load_j10_avb_evidence` -- this function never reads that file or any
    other file itself, keeping it a pure, fixture-testable composition over an injected provider).

    Returns a plain dict -- never writes anything, never raises past this function on a provider failure
    (`ProviderUnavailableError`, including its `RateLimitError` subclass, is caught and recorded as
    `sufficient_evidence: false` with `fetch_error` populated). A provider that returns fewer than six of
    the permitted dates (no exception, just a short list) is ALSO `sufficient_evidence: false`, with
    `missing_dates` naming exactly which ones -- never inferred, never substituted from an adjacent day."""
    capture_timestamp = _now_iso()
    provider_label = getattr(provider, "source", None) or "yahoo"
    requested_dates = [d.isoformat() for d in PERMITTED_DATES]

    fetch_error: Optional[dict] = None
    try:
        bars = provider.get_daily(AVB_SYMBOL, start=FETCH_WINDOW_START, end=FETCH_WINDOW_END)
    except ProviderUnavailableError as exc:
        bars = []
        fetch_error = {"type": type(exc).__name__, "message": str(exc)}

    permitted_set = set(PERMITTED_DATES)
    per_date: dict[str, dict] = {}
    discarded_dates: list[str] = []
    for bar in bars:
        if bar.date in permitted_set:
            per_date[bar.date.isoformat()] = {
                "close": float(bar.close) if bar.close is not None else None,
                "volume": float(bar.volume) if bar.volume is not None else None,
            }
        else:
            discarded_dates.append(bar.date.isoformat())

    # A returned bar with a null close/volume is exactly as unusable as a missing bar -- treat it as
    # absent rather than as a present-but-empty entry that could later be mistaken for real evidence.
    for key in list(per_date):
        entry = per_date[key]
        if entry["close"] is None or entry["volume"] is None:
            del per_date[key]

    missing_dates = [d for d in requested_dates if d not in per_date]
    sufficient_evidence = fetch_error is None and not missing_dates

    return {
        "generated_at": _now_iso(),
        "capture_timestamp": capture_timestamp,
        "provider": provider_label,
        "symbol": AVB_SYMBOL,
        "requested_dates": requested_dates,
        "requested_window": {
            "start": FETCH_WINDOW_START.isoformat(),
            "end": FETCH_WINDOW_END.isoformat(),
        },
        "fetch_call_count": 1,
        "fetch_error": fetch_error,
        "discarded_dates_outside_permitted_set": discarded_dates,
        "per_date": per_date,
        "missing_dates": missing_dates,
        "bridge_factor": bridge_factor,
        "comparison_formulas": COMPARISON_FORMULAS,
        "sufficient_evidence": sufficient_evidence,
    }
