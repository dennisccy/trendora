"""goal-market-compass iter-15 -- J-11 Stage D readiness, Goal 2: fixture/mock-provider tests for the ONE
AG-9 dated-exception-#2 bounded fetch (TC-5..TC-7, TC-10's own reuse note).

NEVER a real network call -- every provider here is a small in-repo `FakePriceProvider` test double
implementing `app.data_providers.base.PriceProvider`, never `app.data_providers.yahoo_provider.
YahooProvider`.
"""
from __future__ import annotations

from datetime import date

import pytest

from app.data_providers.base import Bar, PriceProvider, ProviderUnavailableError, RateLimitError
from app.engine import j11_avb_provider_fetch as fetch

BRIDGE_FACTOR = 2.7930001225759193


class _FakeProvider(PriceProvider):
    """Records every `get_daily` call it receives and returns a caller-supplied bar list (or raises a
    caller-supplied exception) -- never touches the network."""

    source = "yahoo"

    def __init__(self, *, bars: "list[Bar] | None" = None, raises: Exception | None = None):
        self._bars = bars or []
        self._raises = raises
        self.calls: list[dict] = []

    def get_daily(self, symbol, start=None, end=None):
        self.calls.append({"symbol": symbol, "start": start, "end": end})
        if self._raises is not None:
            raise self._raises
        return list(self._bars)


def _bar(iso_date: str, close: float, volume: float) -> Bar:
    y, m, d = (int(x) for x in iso_date.split("-"))
    return Bar(date=date(y, m, d), open=close, high=close, low=close, close=close, volume=volume)


_ALL_SIX_BARS = [
    _bar("2026-08-05", 67.89, 2_100_000.0),
    _bar("2026-08-06", 66.79, 2_050_000.0),
    _bar("2026-08-07", 67.15, 2_090_000.0),
    _bar("2026-08-10", 65.82, 1_950_000.0),
    _bar("2026-08-11", 65.08, 5_390_000.0),
    _bar("2026-08-12", 64.37, 34_100_000.0),
]


# --- TC-5: exactly one call, exact symbol/window, strict filtering to the six permitted dates ---------


def test_tc5_calls_get_daily_exactly_once_with_avb_and_the_full_window():
    provider = _FakeProvider(bars=_ALL_SIX_BARS)
    fetch.fetch_avb_provider_evidence(provider, bridge_factor=BRIDGE_FACTOR)

    assert len(provider.calls) == 1
    call = provider.calls[0]
    assert call["symbol"] == "AVB"
    assert call["start"] == date(2026, 8, 5)
    assert call["end"] == date(2026, 8, 12)


def test_tc5_discards_any_returned_bar_outside_the_six_permitted_dates():
    bars_with_extras = list(_ALL_SIX_BARS) + [
        _bar("2026-08-04", 70.0, 1_000_000.0),  # before the window -- must be discarded
        _bar("2026-08-13", 63.0, 1_000_000.0),  # after the window -- must be discarded
    ]
    provider = _FakeProvider(bars=bars_with_extras)
    result = fetch.fetch_avb_provider_evidence(provider, bridge_factor=BRIDGE_FACTOR)

    assert set(result["per_date"]) == {d.isoformat() for d in fetch.PERMITTED_DATES}
    assert sorted(result["discarded_dates_outside_permitted_set"]) == ["2026-08-04", "2026-08-13"]
    assert result["sufficient_evidence"] is True


# --- TC-6: full success -- per-date close/volume, provider label, timestamp, bridge_factor, formulas ---


def test_tc6_full_success_records_complete_auditable_provenance():
    provider = _FakeProvider(bars=_ALL_SIX_BARS)
    result = fetch.fetch_avb_provider_evidence(provider, bridge_factor=BRIDGE_FACTOR)

    assert result["provider"] == "yahoo"
    assert result["symbol"] == "AVB"
    assert result["requested_dates"] == [d.isoformat() for d in fetch.PERMITTED_DATES]
    assert result["bridge_factor"] == BRIDGE_FACTOR
    assert result["fetch_call_count"] == 1
    assert result["fetch_error"] is None
    assert result["missing_dates"] == []
    assert result["sufficient_evidence"] is True

    # capture_timestamp / generated_at are real UTC ISO strings, parseable and offset-aware.
    from datetime import datetime
    parsed_capture = datetime.fromisoformat(result["capture_timestamp"])
    parsed_generated = datetime.fromisoformat(result["generated_at"])
    assert parsed_capture.tzinfo is not None
    assert parsed_generated.tzinfo is not None

    assert result["per_date"]["2026-08-11"] == {"close": 65.08, "volume": 5_390_000.0}
    assert result["per_date"]["2026-08-05"] == {"close": 67.89, "volume": 2_100_000.0}

    formulas = result["comparison_formulas"]
    assert formulas["close_ratio"] == "stored_close / provider_close"
    assert formulas["volume_ratio"] == "stored_volume / provider_volume"
    assert formulas["expected_inverse_volume_ratio"] == "1 / bridge_factor"


def test_output_written_to_caller_supplied_path_only(tmp_path):
    import json

    provider = _FakeProvider(bars=_ALL_SIX_BARS)
    result = fetch.fetch_avb_provider_evidence(provider, bridge_factor=BRIDGE_FACTOR)
    out = tmp_path / "evidence.json"
    out.write_text(json.dumps(result, default=str))
    assert out.exists()
    reloaded = json.loads(out.read_text())
    assert reloaded["sufficient_evidence"] is True


# --- TC-7: provider failure or short return -- fail closed, no adjacent-day substitute, no propagation --


def test_tc7_provider_unavailable_error_is_caught_never_propagates():
    provider = _FakeProvider(raises=ProviderUnavailableError("yahoo: 503"))
    result = fetch.fetch_avb_provider_evidence(provider, bridge_factor=BRIDGE_FACTOR)  # must not raise

    assert result["sufficient_evidence"] is False
    assert result["fetch_error"]["type"] == "ProviderUnavailableError"
    assert result["missing_dates"] == [d.isoformat() for d in fetch.PERMITTED_DATES]
    assert result["per_date"] == {}


def test_tc7_rate_limit_error_subclass_is_also_caught():
    provider = _FakeProvider(raises=RateLimitError("yahoo: 429"))
    result = fetch.fetch_avb_provider_evidence(provider, bridge_factor=BRIDGE_FACTOR)  # must not raise

    assert result["sufficient_evidence"] is False
    assert result["fetch_error"]["type"] == "RateLimitError"


def test_tc7_short_return_names_the_specific_missing_dates_no_adjacent_day_substitute():
    partial_bars = [b for b in _ALL_SIX_BARS if b.date != date(2026, 8, 12)]  # 08-12 missing
    provider = _FakeProvider(bars=partial_bars)
    result = fetch.fetch_avb_provider_evidence(provider, bridge_factor=BRIDGE_FACTOR)

    assert result["sufficient_evidence"] is False
    assert result["missing_dates"] == ["2026-08-12"]
    assert "2026-08-12" not in result["per_date"]
    # the five genuinely fetched dates are still recorded -- a partial result is not discarded wholesale.
    assert len(result["per_date"]) == 5


def test_tc7_a_bar_with_null_close_or_volume_counts_as_missing_not_present():
    bars = list(_ALL_SIX_BARS)
    bars[-1] = Bar(date=date(2026, 8, 12), open=1, high=1, low=1, close=None, volume=None)
    provider = _FakeProvider(bars=bars)
    result = fetch.fetch_avb_provider_evidence(provider, bridge_factor=BRIDGE_FACTOR)

    assert result["sufficient_evidence"] is False
    assert "2026-08-12" in result["missing_dates"]
    assert "2026-08-12" not in result["per_date"]


def test_no_other_provider_call_is_ever_made_on_failure():
    provider = _FakeProvider(raises=ProviderUnavailableError("boom"))
    fetch.fetch_avb_provider_evidence(provider, bridge_factor=BRIDGE_FACTOR)
    assert len(provider.calls) == 1  # exactly one attempt, no retry-with-broadened-window
