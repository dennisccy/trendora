"""SeedProvider: determinism, exact fixture match, date filtering, and the no-fabrication
failure path (anti-goal: missing/unreadable fixture RAISES — never returns synthesized bars)."""
from __future__ import annotations

import csv
from datetime import date

import pytest

from app.data_providers import ProviderUnavailableError, SeedProvider, symbol_to_filename


def test_determinism_repeated_calls_identical(seed_dir):
    provider = SeedProvider(seed_dir)
    first = provider.get_daily("SPY")
    second = provider.get_daily("SPY")
    assert first == second
    assert len(first) > 100


def test_two_instances_return_identical_bars(seed_dir):
    assert SeedProvider(seed_dir).get_daily("QQQ") == SeedProvider(seed_dir).get_daily("QQQ")


def test_bars_match_committed_fixture_exactly(seed_dir):
    provider = SeedProvider(seed_dir)
    bars = provider.get_daily("SPY")
    with (seed_dir / "prices" / symbol_to_filename("SPY")).open() as fh:
        first_row = next(csv.DictReader(fh))
    assert bars[0].date.isoformat() == first_row["date"]
    assert bars[0].open == float(first_row["open"])
    assert bars[0].close == float(first_row["close"])
    assert bars[0].volume == float(first_row["volume"])
    # ascending by date
    assert all(bars[i].date < bars[i + 1].date for i in range(len(bars) - 1))


def test_date_window_filter_is_inclusive_and_bounded(seed_dir):
    provider = SeedProvider(seed_dir)
    full = provider.get_daily("SPY")
    bounded = provider.get_daily("SPY", start=date(2023, 1, 1), end=date(2023, 12, 31))
    assert 0 < len(bounded) < len(full)
    assert all(date(2023, 1, 1) <= b.date <= date(2023, 12, 31) for b in bounded)


def test_vix_loads_under_sanitized_filename(seed_dir):
    bars = SeedProvider(seed_dir).get_daily("^VIX")
    assert len(bars) > 100
    assert (seed_dir / "prices" / "_VIX.csv").exists()


def test_missing_symbol_raises_and_does_not_synthesize(seed_dir):
    provider = SeedProvider(seed_dir)
    with pytest.raises(ProviderUnavailableError):
        provider.get_daily("ZZ_NOT_A_REAL_SYMBOL")


def test_empty_seed_dir_raises_not_returns_empty(tmp_path):
    """A provider pointed at a dir with no fixture RAISES — it must not silently return []."""
    provider = SeedProvider(tmp_path)
    with pytest.raises(ProviderUnavailableError):
        provider.get_daily("SPY")


def test_get_market_cap_none_when_no_reference_file(seed_dir):
    """The committed seed dir carries NO market_caps.csv (the production default provider) → get_market_cap
    returns None (an honest absence) and NEVER fabricates or raises (iter-26, J-35 offline expand)."""
    provider = SeedProvider(seed_dir)
    assert not (provider.seed_dir / "market_caps.csv").exists()  # committed seed has no cap reference
    assert provider.get_market_cap("NVDA") is None


def test_get_market_cap_reads_committed_reference_and_omits_absent(tmp_path):
    """With a market_caps.csv overlay (a THROWAWAY dir, never the committed seed), get_market_cap returns
    the REAL listed value and None for an absent symbol — read from a committed file, never synthesized."""
    overlay = tmp_path / "overlay"
    (overlay / "prices").mkdir(parents=True)
    (overlay / "market_caps.csv").write_text("symbol,market_cap\nNVDA,3300000000000\nAMSC,1200000000\n")
    provider = SeedProvider(overlay)
    assert provider.get_market_cap("NVDA") == 3_300_000_000_000.0
    assert provider.get_market_cap("AMSC") == 1_200_000_000.0
    assert provider.get_market_cap("ZZZZ_ABSENT") is None  # honest omission, not a fabricated cap
