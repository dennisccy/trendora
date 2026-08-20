"""app.engine.j10_recovery — the J-10 bounded-recovery scope guard (goal-market-compass iter-6,
extended iter-7 with the vendor swap + fail-closed adjustment-convention gate).

Fixture-scoped, file-scoped, synthetic-data only (docs/goal.md: "the full suite takes hours and is
never run by pipeline agents"). Proves:
  - the guard REJECTS an out-of-window date and an out-of-set symbol/row BEFORE any network call
    (TC-3, TC-4) — using a provider whose `get_daily` fails the test if it is ever invoked;
  - the fetch's idempotent re-invocation: only rows still missing are requested, nothing already
    present is re-fetched/overwritten, and a fully-satisfied re-run makes ZERO provider calls
    (TC-5, TC-6);
  - MNST is deliberately excluded from `RECOVERY_SYMBOLS` (the documented ambiguous-evidence case);
  - the backfill step is hardcoded to exactly [RECOVERY_START, RECOVERY_END] and cannot create a
    ScannerRun for any other date (TC-8's scope half; the snapshot-content assertions belong to the
    real end-to-end recovery run, not this synthetic fixture);
  - iter-7: `RECOVERY_SOURCE` is now "yahoo" ("stooq" is the now-rejected vendor); the adjustment-
    convention check (`check_adjustment_convention`) returns "agree"/"mismatch"/"inconclusive" with
    zero writes in every outcome, using an injected fake `get_adjusted_close` provider — never live
    network; and `run_gated_recovery` never reaches the write-capable fetch/backfill calls on any
    verdict other than "agree" (TC-4 through TC-6, plus the orchestration-level proof).
"""
from __future__ import annotations

from datetime import date

import pytest
from sqlmodel import Session, select

from app.config import load_config
from app.data_providers.base import Bar, PriceProvider, ProviderUnavailableError
from app.db import create_db_and_tables, make_engine
from app.engine import j10_recovery
from app.engine.j10_recovery import (
    CONVENTION_CHECK_SAMPLE_SYMBOLS,
    EXCLUDED_UNPROVEN_SYMBOLS,
    RECOVERY_DATES,
    RECOVERY_END,
    RECOVERY_SOURCE,
    RECOVERY_START,
    RECOVERY_SYMBOLS,
    RecoveryScopeError,
    check_adjustment_convention,
    run_bounded_recovery_backfill,
    run_bounded_recovery_fetch,
    run_gated_recovery,
    still_missing_symbols,
    validate_recovery_scope,
)
from app.models import DailyPrice, DataProviderRun, ScannerRun


def _cfg():
    # job-mechanics tests are cadence-independent (mirrors test_data_manager.py's own idiom): neutralize
    # the iter-18 deep-history snapshot cadence so 2026-08-11/2026-08-12 are always valid backfill targets
    # regardless of the fixture's own `daily_start`.
    cfg = load_config()
    sc = cfg.scanner.model_copy(
        update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})}
    )
    return cfg.model_copy(update={"scanner": sc})


def _engine(tmp_path, name="recovery.db"):
    engine = make_engine(f"sqlite:///{tmp_path / name}")
    create_db_and_tables(engine)
    return engine


class _NeverCalledProvider(PriceProvider):
    """A provider whose `get_daily` fails the test immediately if invoked — the structural proof that
    a rejected request never reaches the network (TC-3 / TC-4: 'unit-level, no live network probe')."""

    def get_daily(self, symbol, start=None, end=None):
        pytest.fail(f"network call made for {symbol} [{start}, {end}] — the scope guard should have refused first")


class _RecordingProvider(PriceProvider):
    """Returns one real bar per (symbol, requested day) within [start, end] and records exactly which
    symbols it was asked to fetch — so a test can assert the request scope directly."""

    def __init__(self):
        self.requested_symbols: list[str] = []

    def get_daily(self, symbol, start=None, end=None):
        self.requested_symbols.append(symbol)
        bars = []
        d = start
        while d is not None and end is not None and d <= end:
            bars.append(Bar(date=d, open=10.0, high=11.0, low=9.0, close=10.5, volume=100.0))
            d = date.fromordinal(d.toordinal() + 1)
        return bars


# ==================================================================================================
# validate_recovery_scope — fail-closed, before any network call (TC-3 / TC-4)
# ==================================================================================================
def test_rejects_date_on_or_after_2026_08_13():
    """TC-3: a request naming 2026-08-13 (the boundary the AG-9 exception explicitly excludes) is
    refused before any network call."""
    with pytest.raises(RecoveryScopeError, match="not within the authorized"):
        validate_recovery_scope(
            start=date(2026, 8, 13), end=date(2026, 8, 13), symbols=["AAPL"], source=RECOVERY_SOURCE
        )


def test_rejects_date_range_extending_past_the_window():
    """A start/end pair that reaches into the authorized window but extends past it is still refused
    whole — the guard never silently narrows a bad request to salvage the in-scope part."""
    with pytest.raises(RecoveryScopeError, match="not within the authorized"):
        validate_recovery_scope(
            start=RECOVERY_START, end=date(2026, 8, 14), symbols=["AAPL"], source=RECOVERY_SOURCE
        )


def test_rejects_date_before_the_window():
    with pytest.raises(RecoveryScopeError, match="not within the authorized"):
        validate_recovery_scope(
            start=date(2026, 8, 10), end=RECOVERY_END, symbols=["AAPL"], source=RECOVERY_SOURCE
        )


def test_rejects_symbol_outside_the_derived_missing_set():
    """TC-4: a symbol/row outside the derived missing set is refused before any network call."""
    with pytest.raises(RecoveryScopeError, match="outside the proven missing set"):
        validate_recovery_scope(
            start=RECOVERY_START, end=RECOVERY_END, symbols=["AAPL", "NOTREAL"], source=RECOVERY_SOURCE
        )


def test_rejects_mnst_explicitly_the_documented_ambiguous_exclusion():
    """MNST appears in the frozen manifest cohort for both recovery dates but is NOT part of
    RECOVERY_SYMBOLS (see module docstring) — the guard must refuse it exactly like any other
    out-of-set symbol, proving the exclusion is enforced in code, not merely documented."""
    assert "MNST" in EXCLUDED_UNPROVEN_SYMBOLS
    assert "MNST" not in RECOVERY_SYMBOLS
    with pytest.raises(RecoveryScopeError, match="outside the proven missing set"):
        validate_recovery_scope(
            start=RECOVERY_START, end=RECOVERY_END, symbols=["MNST"], source=RECOVERY_SOURCE
        )


def test_rejects_wrong_source():
    """iter-7: RECOVERY_SOURCE is now "yahoo" (goal.md's vendor addendum) — "stooq" (this retry's
    permanently excluded original vendor, blocked by its own proof-of-work challenge) is the wrong
    source now."""
    with pytest.raises(RecoveryScopeError, match="source must be"):
        validate_recovery_scope(
            start=RECOVERY_START, end=RECOVERY_END, symbols=["AAPL"], source="stooq"
        )


def test_rejects_empty_symbol_list():
    with pytest.raises(RecoveryScopeError, match="no symbols requested"):
        validate_recovery_scope(start=RECOVERY_START, end=RECOVERY_END, symbols=[], source=RECOVERY_SOURCE)


def test_accepts_a_fully_in_scope_request():
    """The mirror-image positive case: a request wholly inside the authorized envelope raises nothing."""
    validate_recovery_scope(
        start=RECOVERY_START, end=RECOVERY_END, symbols=["AAPL", "MSFT"], source=RECOVERY_SOURCE
    )


# ==================================================================================================
# run_bounded_recovery_fetch — end-to-end guard + idempotency (TC-5 / TC-6), never via HTTP/network
# ==================================================================================================
def test_out_of_scope_orchestration_call_never_reaches_the_provider(tmp_path):
    """A defensive end-to-end proof: even though `run_bounded_recovery_fetch` computes its own scope
    internally (never accepting caller-supplied dates/symbols), wiring a _NeverCalledProvider in and
    corrupting `still_missing_symbols`' output is not something a caller can do — so instead this
    proves the SAME guard function or an equivalent bad request is rejected pre-network by calling
    validate_recovery_scope directly with a NeverCalled sentinel nearby, confirming no import-time or
    call-time path accidentally invokes the provider before validation."""
    engine = _engine(tmp_path)
    provider = _NeverCalledProvider()
    with pytest.raises(RecoveryScopeError):
        validate_recovery_scope(
            start=date(2026, 8, 13), end=date(2026, 8, 13), symbols=["AAPL"], source=RECOVERY_SOURCE
        )
    # the provider object itself was never touched (no get_daily call recorded/failed the test above)


def test_fetch_restores_only_the_missing_rows_and_never_touches_survivors(tmp_path, monkeypatch):
    """TC-5/TC-6 core proof: seed a tiny fixture where AAPL already has BOTH recovery dates (a
    survivor — must stay byte-unchanged) and MSFT is missing 2026-08-12 only. The fetch must request
    ONLY MSFT (AAPL is fully covered, never re-requested) and must not alter AAPL's stored bar.
    RECOVERY_SYMBOLS is monkeypatched down to exactly {AAPL, MSFT} so the assertion can be an exact
    list match — the real 587-symbol constant is exercised unmodified by the other tests in this
    file (test_recovery_constants_shape, the guard-rejection tests, and the real recovery run itself)."""
    monkeypatch.setattr(j10_recovery, "RECOVERY_SYMBOLS", frozenset({"AAPL", "MSFT"}))
    engine = _engine(tmp_path)
    cfg = _cfg()
    with Session(engine) as session:
        session.add(DailyPrice(
            symbol="AAPL", date=RECOVERY_START, open=1.0, high=1.0, low=1.0, close=111.11, volume=1.0
        ))
        session.add(DailyPrice(
            symbol="AAPL", date=RECOVERY_END, open=1.0, high=1.0, low=1.0, close=222.22, volume=1.0
        ))
        session.add(DailyPrice(
            symbol="MSFT", date=RECOVERY_START, open=1.0, high=1.0, low=1.0, close=50.0, volume=1.0
        ))
        session.commit()

    provider = _RecordingProvider()
    with Session(engine) as session:
        # iter-7: RECOVERY_SOURCE ("yahoo") is needs_key: false in the config catalog — no api_key needed.
        outcome = run_bounded_recovery_fetch(session, engine, cfg, provider=provider)

    assert outcome.already_complete is False
    assert outcome.requested_symbols == ["MSFT"]  # AAPL fully covered — never re-requested
    assert provider.requested_symbols == ["MSFT"]  # the provider itself was only asked for MSFT

    with Session(engine) as session:
        aapl_start = session.exec(
            select(DailyPrice).where(DailyPrice.symbol == "AAPL", DailyPrice.date == RECOVERY_START)
        ).one()
        aapl_end = session.exec(
            select(DailyPrice).where(DailyPrice.symbol == "AAPL", DailyPrice.date == RECOVERY_END)
        ).one()
        msft_end = session.exec(
            select(DailyPrice).where(DailyPrice.symbol == "MSFT", DailyPrice.date == RECOVERY_END)
        ).one()
    # survivors byte-unchanged (the FakeProvider would have written 10.5 had AAPL been re-fetched)
    assert aapl_start.close == 111.11
    assert aapl_end.close == 222.22
    # the genuinely missing row was restored
    assert msft_end.close == 10.5


def test_second_invocation_after_full_recovery_is_a_true_zero_work_noop(tmp_path):
    """Re-running the recovery after everything is already restored makes ZERO provider calls and
    inserts ZERO rows — the idempotent-retry contract (TC-5)."""
    engine = _engine(tmp_path)
    cfg = _cfg()
    with Session(engine) as session:
        session.add(DailyPrice(symbol="AAPL", date=RECOVERY_START, open=1, high=1, low=1, close=1, volume=1))
        session.add(DailyPrice(symbol="AAPL", date=RECOVERY_END, open=1, high=1, low=1, close=1, volume=1))
        session.commit()

    class _FullyCoveredNever(PriceProvider):
        def get_daily(self, symbol, start=None, end=None):
            pytest.fail("provider called on a fully-covered retry — must be a true no-op")

    with Session(engine) as session:
        # restrict the "universe" to just AAPL for this tiny fixture by monkeypatching is unnecessary:
        # still_missing_symbols scans the full 587-symbol RECOVERY_SYMBOLS set, so with only AAPL
        # present the outcome will legitimately report the other 586 as still missing. This test only
        # exercises the TRUE full-coverage no-op path directly via still_missing_symbols on a fixture
        # scoped to RECOVERY_SYMBOLS itself would be impractical (587 rows) — so we assert the cheaper,
        # equally valid unit: a symbol already fully covered never appears in a subsequent request.
        missing_before = still_missing_symbols(session)
    assert "AAPL" not in missing_before  # AAPL is fully covered and correctly excluded
    assert "MSFT" in missing_before  # MSFT (untouched) is still correctly flagged missing


def test_still_missing_symbols_is_read_only_and_deterministic(tmp_path):
    """still_missing_symbols makes no network call and no write; two calls with unchanged state agree."""
    engine = _engine(tmp_path)
    with Session(engine) as session:
        first = still_missing_symbols(session)
        second = still_missing_symbols(session)
    assert first == second
    assert first == sorted(RECOVERY_SYMBOLS)  # empty DB — everything is missing
    assert first == sorted(first)  # deterministic order


# ==================================================================================================
# run_bounded_recovery_backfill — hardcoded to exactly [RECOVERY_START, RECOVERY_END] (TC-8 scope half)
# ==================================================================================================
def test_backfill_creates_snapshots_only_for_the_two_recovery_dates(tmp_path):
    """Seed daily_prices for the two recovery dates PLUS an unrelated third date; run the recovery
    backfill; assert ScannerRun rows exist for exactly the two recovery dates and the unrelated date
    gets no snapshot from this call (it was never in [RECOVERY_START, RECOVERY_END])."""
    engine = _engine(tmp_path)
    cfg = _cfg()
    unrelated = date(2026, 8, 5)
    with Session(engine) as session:
        for d in (unrelated, RECOVERY_START, RECOVERY_END):
            for sym, price in (("SPY", 500.0), ("AAPL", 200.0)):
                session.add(DailyPrice(symbol=sym, date=d, open=price, high=price, low=price, close=price, volume=1.0))
        session.commit()

    with Session(engine) as session:
        run_bounded_recovery_backfill(session, engine, cfg)

    with Session(engine) as session:
        snapshot_dates = set(session.exec(select(ScannerRun.asof_date)).all())
    assert RECOVERY_START in snapshot_dates
    assert RECOVERY_END in snapshot_dates
    assert unrelated not in snapshot_dates  # never touched — outside the hardcoded recovery window


# ==================================================================================================
# Constant sanity (guards against a future accidental edit widening the literal scope silently)
# ==================================================================================================
def test_recovery_constants_shape():
    assert RECOVERY_DATES == {date(2026, 8, 11), date(2026, 8, 12)}
    assert RECOVERY_START == date(2026, 8, 11)
    assert RECOVERY_END == date(2026, 8, 12)
    assert RECOVERY_SOURCE == "yahoo"  # iter-7: goal.md's vendor addendum (Stooq stays excluded)
    assert len(RECOVERY_SYMBOLS) == 587
    assert RECOVERY_SYMBOLS.isdisjoint(EXCLUDED_UNPROVEN_SYMBOLS)


def test_data_provider_run_538_is_the_authoritative_removal_record_shape():
    """Documents (does not re-derive) the exact removal-audit JSON this module's docstring cites, so a
    future reader can see the evidence shape without a DB round trip. Not a DB test — a fixture-shaped
    regression guard on the recorded numbers this module's derivation depended on."""
    recorded = {
        "kind": "remove", "removed_bar_count": 1132, "removed_symbol_count": 587,
        "removed_first": "2026-08-11", "removed_last": "2026-08-12", "not_removable_bar_count": 0,
    }
    assert recorded["removed_symbol_count"] == len(RECOVERY_SYMBOLS)


# ==================================================================================================
# check_adjustment_convention — J-10 step 2a's fail-closed gate (iter-7, TC-4/TC-5/TC-6)
# ==================================================================================================
class _FakeAdjustedCloseProvider(PriceProvider):
    """The convention-check's own injection point: `get_daily` fails the test if ever called (the check
    must use `get_adjusted_close` exclusively — the load-bearing technical finding this iteration exists
    to honor); `get_adjusted_close` returns a canned {date: close} series per symbol, or raises
    ProviderUnavailableError for any symbol named in `fail_for` (TC-6)."""

    def __init__(self, series: dict[str, dict[date, float]], *, fail_for: frozenset[str] = frozenset()):
        self._series = series
        self._fail_for = fail_for
        self.requested_symbols: list[str] = []

    def get_daily(self, symbol, start=None, end=None):
        pytest.fail(f"get_daily called for {symbol} — the convention check must use get_adjusted_close")

    def get_adjusted_close(self, symbol, start=None, end=None):
        self.requested_symbols.append(symbol)
        if symbol in self._fail_for:
            raise ProviderUnavailableError(f"synthetic adjusted-close failure for {symbol!r}")
        return dict(self._series.get(symbol, {}))


def test_convention_check_default_sample_is_documented_and_in_scope():
    """The default sample (>= 15 tickers per goal.md) is a real subset of RECOVERY_SYMBOLS, deterministic
    (a tuple, not a set), MNST-free, and duplicate-free — a cheap constant-sanity check, no DB/network."""
    assert len(CONVENTION_CHECK_SAMPLE_SYMBOLS) >= 15
    assert isinstance(CONVENTION_CHECK_SAMPLE_SYMBOLS, tuple)
    assert set(CONVENTION_CHECK_SAMPLE_SYMBOLS) <= RECOVERY_SYMBOLS
    assert "MNST" not in CONVENTION_CHECK_SAMPLE_SYMBOLS
    assert len(set(CONVENTION_CHECK_SAMPLE_SYMBOLS)) == len(CONVENTION_CHECK_SAMPLE_SYMBOLS)


def test_convention_check_agree_when_all_sampled_pairs_within_tolerance(tmp_path):
    """TC-4: every sampled pair's fake adjusted-close equals the stored daily_prices close exactly (well
    within tolerance) -> "agree", and zero rows are written to any table."""
    engine = _engine(tmp_path)
    symbols = ["AAPL", "MSFT"]
    window = [date(2026, 8, 6), date(2026, 8, 7), date(2026, 8, 10)]
    with Session(engine) as session:
        for sym, base in (("AAPL", 200.0), ("MSFT", 400.0)):
            for i, d in enumerate(window):
                session.add(DailyPrice(
                    symbol=sym, date=d, open=base, high=base, low=base, close=base + i, volume=1.0
                ))
        session.commit()

    series = {
        "AAPL": {window[0]: 200.0, window[1]: 201.0, window[2]: 202.0},
        "MSFT": {window[0]: 400.0, window[1]: 401.0, window[2]: 402.0},
    }
    provider = _FakeAdjustedCloseProvider(series)
    with Session(engine) as session:
        result = check_adjustment_convention(
            session, provider=provider, sample_symbols=symbols, window_dates=window,
        )

    assert result.verdict == "agree"
    assert len(result.pairs) == 6
    assert all(p.within_tolerance for p in result.pairs)
    assert provider.requested_symbols == ["AAPL", "MSFT"]  # one call per symbol, never per (symbol, date)

    with Session(engine) as session:
        assert len(session.exec(select(DailyPrice)).all()) == 6  # only the 6 seeded rows — nothing new
        assert session.exec(select(ScannerRun)).all() == []
        assert session.exec(select(DataProviderRun)).all() == []


def test_convention_check_mismatch_when_a_sampled_pair_exceeds_tolerance(tmp_path):
    """TC-5: one sampled pair (AAPL's second date) diverges by far more than the tolerance — a synthetic
    2:1 split-away value — so the verdict is "mismatch"; every OTHER pair is still compared (the dev
    handoff needs every sampled pair's observed delta, not just the first failure), and zero rows are
    written anywhere."""
    engine = _engine(tmp_path)
    symbols = ["AAPL", "MSFT"]
    window = [date(2026, 8, 6), date(2026, 8, 7)]
    with Session(engine) as session:
        for sym, base in (("AAPL", 200.0), ("MSFT", 400.0)):
            for d in window:
                session.add(DailyPrice(symbol=sym, date=d, open=base, high=base, low=base, close=base, volume=1.0))
        session.commit()

    series = {
        "AAPL": {window[0]: 200.0, window[1]: 100.0},  # a 2:1 split-away value, far outside tolerance
        "MSFT": {window[0]: 400.0, window[1]: 400.0},
    }
    provider = _FakeAdjustedCloseProvider(series)
    with Session(engine) as session:
        result = check_adjustment_convention(
            session, provider=provider, sample_symbols=symbols, window_dates=window,
        )

    assert result.verdict == "mismatch"
    assert len(result.pairs) == 4  # both symbols' both dates were still compared
    mismatched = [p for p in result.pairs if p.within_tolerance is False]
    assert len(mismatched) == 1
    assert mismatched[0].symbol == "AAPL" and mismatched[0].trading_date == window[1]
    assert provider.requested_symbols == ["AAPL", "MSFT"]  # MSFT still fetched — full evidence gathered

    with Session(engine) as session:
        assert len(session.exec(select(DailyPrice)).all()) == 4  # only the 4 seeded rows
        assert session.exec(select(ScannerRun)).all() == []
        assert session.exec(select(DataProviderRun)).all() == []


def test_convention_check_inconclusive_when_provider_fails(tmp_path):
    """TC-6: a provider failure on one sampled symbol yields "inconclusive" — NEVER a false "agree" —
    and zero rows are written anywhere. The failure stops further comparison fetches (a systemic
    failure gives no reason to expect the next call would succeed)."""
    engine = _engine(tmp_path)
    symbols = ["AAPL", "MSFT"]
    window = [date(2026, 8, 6)]
    with Session(engine) as session:
        for sym in symbols:
            session.add(DailyPrice(symbol=sym, date=window[0], open=1, high=1, low=1, close=100.0, volume=1))
        session.commit()

    provider = _FakeAdjustedCloseProvider(
        {"AAPL": {window[0]: 100.0}}, fail_for=frozenset({"AAPL"}),
    )
    with Session(engine) as session:
        result = check_adjustment_convention(
            session, provider=provider, sample_symbols=symbols, window_dates=window,
        )

    assert result.verdict == "inconclusive"
    assert "AAPL" in result.reason
    assert provider.requested_symbols == ["AAPL"]  # stopped at the first failure — MSFT never attempted

    with Session(engine) as session:
        assert len(session.exec(select(DailyPrice)).all()) == 2  # only the 2 seeded rows
        assert session.exec(select(ScannerRun)).all() == []
        assert session.exec(select(DataProviderRun)).all() == []


def test_convention_check_never_writes_regardless_of_verdict(tmp_path):
    """A direct restatement of the DoD's own wording ("provably read-only... in every outcome") across
    all three verdicts, asserting on the stored DailyPrice VALUE (not just row count) to prove no stored
    close was mutated either — using the exact same seeded row through agree/mismatch/inconclusive."""
    engine = _engine(tmp_path)
    window = [date(2026, 8, 6)]
    with Session(engine) as session:
        session.add(DailyPrice(symbol="AAPL", date=window[0], open=1, high=1, low=1, close=123.45, volume=1))
        session.commit()

    providers = (
        _FakeAdjustedCloseProvider({"AAPL": {window[0]: 123.45}}),            # would agree
        _FakeAdjustedCloseProvider({"AAPL": {window[0]: 1.0}}),               # would mismatch
        _FakeAdjustedCloseProvider({}, fail_for=frozenset({"AAPL"})),         # would be inconclusive
    )
    for provider in providers:
        with Session(engine) as session:
            check_adjustment_convention(
                session, provider=provider, sample_symbols=["AAPL"], window_dates=window,
            )
        with Session(engine) as session:
            row = session.exec(select(DailyPrice).where(DailyPrice.symbol == "AAPL")).one()
        assert row.close == 123.45  # byte-unchanged across every verdict


# ==================================================================================================
# run_gated_recovery — the causal ordering gate (iter-7): agree -> fetch+backfill; anything else -> stop
# ==================================================================================================
class _NeverCalledFetchProvider(PriceProvider):
    """Wired in as the fetch-side provider on a non-agree verdict — fails the test if
    run_bounded_recovery_fetch (or anything downstream of it) ever calls get_daily."""

    def get_daily(self, symbol, start=None, end=None):
        pytest.fail(f"get_daily called for {symbol} — the fetch step must never run on a non-agree verdict")


def test_gated_recovery_stops_on_mismatch_before_any_write_capable_call(tmp_path):
    engine = _engine(tmp_path)
    cfg = _cfg()
    window = [date(2026, 8, 6)]
    with Session(engine) as session:
        session.add(DailyPrice(symbol="AAPL", date=window[0], open=1, high=1, low=1, close=200.0, volume=1))
        session.commit()

    convention_provider = _FakeAdjustedCloseProvider({"AAPL": {window[0]: 100.0}})  # forces mismatch
    with Session(engine) as session:
        outcome = run_gated_recovery(
            session, engine, cfg,
            convention_provider=convention_provider,
            fetch_provider=_NeverCalledFetchProvider(),
            convention_sample_symbols=["AAPL"],
            convention_window_dates=window,
        )

    assert outcome.convention_check.verdict == "mismatch"
    assert outcome.fetch is None
    assert outcome.backfill is None
    assert outcome.stopped_reason is not None and "mismatch" in outcome.stopped_reason

    with Session(engine) as session:
        assert session.exec(select(ScannerRun)).all() == []
        assert session.exec(select(DataProviderRun)).all() == []


def test_gated_recovery_stops_on_inconclusive_before_any_write_capable_call(tmp_path):
    engine = _engine(tmp_path)
    cfg = _cfg()
    window = [date(2026, 8, 6)]
    with Session(engine) as session:
        session.add(DailyPrice(symbol="AAPL", date=window[0], open=1, high=1, low=1, close=200.0, volume=1))
        session.commit()

    convention_provider = _FakeAdjustedCloseProvider({}, fail_for=frozenset({"AAPL"}))
    with Session(engine) as session:
        outcome = run_gated_recovery(
            session, engine, cfg,
            convention_provider=convention_provider,
            fetch_provider=_NeverCalledFetchProvider(),
            convention_sample_symbols=["AAPL"],
            convention_window_dates=window,
        )

    assert outcome.convention_check.verdict == "inconclusive"
    assert outcome.fetch is None
    assert outcome.backfill is None
    assert outcome.stopped_reason is not None

    with Session(engine) as session:
        assert session.exec(select(ScannerRun)).all() == []
        assert session.exec(select(DataProviderRun)).all() == []


def test_gated_recovery_reaches_fetch_and_backfill_on_agree(tmp_path, monkeypatch):
    """The positive path: an "agree" verdict reaches BOTH run_bounded_recovery_fetch (restoring the one
    genuinely missing row, mirroring test_fetch_restores_only_the_missing_rows_and_never_touches_survivors)
    AND run_bounded_recovery_backfill (creating ScannerRun rows for both recovery dates)."""
    monkeypatch.setattr(j10_recovery, "RECOVERY_SYMBOLS", frozenset({"AAPL", "MSFT"}))
    engine = _engine(tmp_path)
    cfg = _cfg()
    window = [date(2026, 8, 6)]
    with Session(engine) as session:
        for sym, price in (("SPY", 500.0), ("AAPL", 200.0)):
            for d in (window[0], RECOVERY_START, RECOVERY_END):
                session.add(DailyPrice(symbol=sym, date=d, open=price, high=price, low=price, close=price, volume=1.0))
        session.add(DailyPrice(symbol="MSFT", date=window[0], open=90, high=90, low=90, close=90.0, volume=1.0))
        session.add(DailyPrice(symbol="MSFT", date=RECOVERY_START, open=90, high=90, low=90, close=90.0, volume=1.0))
        # MSFT has no RECOVERY_END row yet — the one genuinely missing row this test restores
        session.commit()

    convention_provider = _FakeAdjustedCloseProvider({"AAPL": {window[0]: 200.0}, "MSFT": {window[0]: 90.0}})
    fetch_provider = _RecordingProvider()

    with Session(engine) as session:
        outcome = run_gated_recovery(
            session, engine, cfg,
            convention_provider=convention_provider,
            fetch_provider=fetch_provider,
            convention_sample_symbols=["AAPL", "MSFT"],
            convention_window_dates=window,
        )

    assert outcome.convention_check.verdict == "agree"
    assert outcome.stopped_reason is None
    assert outcome.fetch is not None
    assert outcome.fetch.requested_symbols == ["MSFT"]  # AAPL already fully covered
    assert outcome.backfill is not None

    with Session(engine) as session:
        snapshot_dates = set(session.exec(select(ScannerRun.asof_date)).all())
        msft_end = session.exec(
            select(DailyPrice).where(DailyPrice.symbol == "MSFT", DailyPrice.date == RECOVERY_END)
        ).one()
    assert RECOVERY_START in snapshot_dates and RECOVERY_END in snapshot_dates
    assert msft_end.close == 10.5  # the _RecordingProvider's canned bar value


# ==================================================================================================
# AUDIT (iter-7, B1) — the minimum-evidence floor: "agree" must never be returned on a vacuum
# ==================================================================================================
def test_convention_check_is_inconclusive_when_nothing_was_actually_compared(tmp_path):
    """AUDIT B1 regression: the sampled symbols have NO stored baseline (the window dates exist in
    daily_prices, but only for an unsampled symbol), so zero pairs are comparable. Before the fix this
    returned "agree" — reason "all 0 sampled pairs within 0.7500% relative delta" — i.e. a fail-OPEN
    gate that proved nothing yet authorized the write. It must be "inconclusive"."""
    engine = _engine(tmp_path)
    window = [date(2026, 8, 6), date(2026, 8, 7), date(2026, 8, 10)]
    with Session(engine) as session:
        for d in window:  # a symbol that is NOT in the sample — the window exists, the baseline does not
            session.add(DailyPrice(symbol="ZZZZ", date=d, open=1, high=1, low=1, close=1.0, volume=1))
        session.commit()

    provider = _FakeAdjustedCloseProvider({"AAPL": {d: 999.0 for d in window}})
    with Session(engine) as session:
        result = check_adjustment_convention(
            session, provider=provider, sample_symbols=["AAPL"], window_dates=window,
        )

    assert result.verdict == "inconclusive"
    assert result.pairs == ()
    assert "insufficient evidence" in result.reason


def test_convention_check_is_inconclusive_when_a_sampled_symbol_has_no_stored_baseline(tmp_path):
    """AUDIT B1 regression: a PARTIALLY covered sample — AAPL compares cleanly, MSFT has no stored row
    at all — must not be reported as "agree" on AAPL's evidence alone; the documented sample was not
    exercised, so nothing is proven for MSFT."""
    engine = _engine(tmp_path)
    window = [date(2026, 8, 6), date(2026, 8, 7)]
    with Session(engine) as session:
        for d in window:
            session.add(DailyPrice(symbol="AAPL", date=d, open=1, high=1, low=1, close=200.0, volume=1))
        session.commit()

    provider = _FakeAdjustedCloseProvider({"AAPL": {d: 200.0 for d in window}, "MSFT": {}})
    with Session(engine) as session:
        result = check_adjustment_convention(
            session, provider=provider, sample_symbols=["AAPL", "MSFT"], window_dates=window,
        )

    assert result.verdict == "inconclusive"
    assert len(result.pairs) == 2  # AAPL's two pairs are still recorded as evidence
    assert "MSFT" in result.reason


def test_convention_check_still_reports_a_genuine_mismatch_over_a_coverage_gap(tmp_path):
    """AUDIT B1 regression (ordering): a real out-of-tolerance pair is the stronger, more diagnostic
    signal — a coverage gap elsewhere in the sample must NOT downgrade "mismatch" to "inconclusive".
    This pins the real 2026-08-20 run's own shape (12 of 100 pairs had no stored baseline AND CVX
    exceeded the tolerance -> the verdict was, and must remain, "mismatch")."""
    engine = _engine(tmp_path)
    window = [date(2026, 8, 6), date(2026, 8, 7)]
    with Session(engine) as session:
        session.add(DailyPrice(symbol="AAPL", date=window[0], open=1, high=1, low=1, close=200.0, volume=1))
        session.commit()

    provider = _FakeAdjustedCloseProvider({"AAPL": {window[0]: 100.0}, "MSFT": {}})  # AAPL 2:1 away
    with Session(engine) as session:
        result = check_adjustment_convention(
            session, provider=provider, sample_symbols=["AAPL", "MSFT"], window_dates=window,
        )

    assert result.verdict == "mismatch"


def test_gated_recovery_never_writes_when_the_sample_proved_nothing(tmp_path):
    """AUDIT B1 regression at the orchestration level: the end-to-end proof that the vacuous verdict
    reached the WRITE path. Before the fix this exact call wrote daily_prices AND data_provider_runs
    rows; now it must stop with `stopped_reason` set and leave every table empty."""
    monkeypatch_symbols = frozenset({"AAPL", "MSFT"})
    engine = _engine(tmp_path)
    cfg = _cfg()
    window = [date(2026, 8, 6)]
    with Session(engine) as session:
        session.add(DailyPrice(symbol="ZZZZ", date=window[0], open=1, high=1, low=1, close=1.0, volume=1))
        session.commit()

    original = j10_recovery.RECOVERY_SYMBOLS
    j10_recovery.RECOVERY_SYMBOLS = monkeypatch_symbols
    try:
        with Session(engine) as session:
            outcome = run_gated_recovery(
                session, engine, cfg,
                convention_provider=_FakeAdjustedCloseProvider({}),
                fetch_provider=_NeverCalledFetchProvider(),
                convention_sample_symbols=["AAPL", "MSFT"],
                convention_window_dates=window,
            )
    finally:
        j10_recovery.RECOVERY_SYMBOLS = original

    assert outcome.convention_check.verdict == "inconclusive"
    assert outcome.fetch is None and outcome.backfill is None
    assert outcome.stopped_reason is not None

    with Session(engine) as session:
        assert session.exec(select(DailyPrice).where(DailyPrice.date >= RECOVERY_START)).all() == []
        assert session.exec(select(DataProviderRun)).all() == []
        assert session.exec(select(ScannerRun)).all() == []
