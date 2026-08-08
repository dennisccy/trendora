"""iter-33 (J-93 / J-94) + iter-18 (J-12 hardening) — the per-as-of-date point-in-time universe resolver.

FAST synthetic tests (no seed boot — iter-29 lesson): a tiny in-memory DB with hand-made bars + a
throwaway candidate-pool CSV exercise every resolver leg in milliseconds. The seed-loading
`loaded_engine`-fixture cross-checks live in test_universe_screen.py / test_data_manager.py.

iter-18 adds the RECENCY/STALENESS gate: a candidate whose last bar is more than
`universe.filters.max_staleness_days` calendar days before the resolve date D is excluded
(`stale_series`) — a name whose data ends mid-history exits membership cleanly and can never feed a
positionally-misaligned relative-strength window. Deterministic fixed gate order:
history -> staleness -> price -> ADV.
"""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pytest
from sqlmodel import Session

from app.config import load_config
from app.db import create_db_and_tables, make_engine
from app.engine import universe_resolver
from app.engine.universe_resolver import (
    EXCLUSION_REASONS,
    REASON_BELOW_ADV,
    REASON_BELOW_HISTORY,
    REASON_BELOW_PRICE,
    REASON_STALE,
    resolve_candidate,
    resolve_members,
    resolve_with_reasons,
)
from app.models import DailyPrice


# --------------------------------------------------------------------------------------------------
# Test config: a small, distinctive threshold set so the gates are easy to reason about.
# --------------------------------------------------------------------------------------------------
def _cfg():
    """A real Config with a SMALL min_history_bars + clear price/ADV/staleness cutoffs so synthetic
    series are cheap. Reads through model_copy so all other required keys stay valid."""
    cfg = load_config().model_copy(deep=True)
    cfg = cfg.model_copy(
        update={"indicators": cfg.indicators.model_copy(update={"min_history_bars": 5})}
    )
    cfg = cfg.model_copy(
        update={
            "universe": cfg.universe.model_copy(
                update={
                    "filters": cfg.universe.filters.model_copy(
                        update={
                            "min_price": 10.0,
                            "min_dollar_vol": 1000.0,
                            "adv_window_days": 3,
                            "max_staleness_days": 7,
                        }
                    )
                }
            )
        }
    )
    return cfg


def _write_pool(tmp_path: Path, symbols: list[str]) -> Path:
    """A throwaway candidate-pool CSV the resolver's read_pool reads via seed_dir override."""
    seed_dir = tmp_path / "seed"
    seed_dir.mkdir(parents=True, exist_ok=True)
    lines = ["# test pool", "symbol,sector,source"]
    lines += [f"{s},Technology,test" for s in symbols]
    (seed_dir / "universe_pool.csv").write_text("\n".join(lines) + "\n")
    return seed_dir


class _Bar:
    """A lightweight bar stand-in for the pure resolve_candidate unit (no DB)."""

    def __init__(self, close, volume, d=None):
        self.close = close
        self.volume = volume
        self.date = d


def _bars(n: int, close: float, volume: float, *, end: date) -> list[_Bar]:
    """`n` consecutive daily bars ENDING at `end` (ascending), each with the given close/volume."""
    return [_Bar(close, volume, end - timedelta(days=n - 1 - i)) for i in range(n)]


# --------------------------------------------------------------------------------------------------
# PURE resolve_candidate — each gate exercised in isolation (no DB).
# --------------------------------------------------------------------------------------------------
D0 = date(2024, 6, 14)  # the pure-unit resolve date


def test_resolve_candidate_admits_when_all_gates_pass():
    cfg = _cfg()  # min_history=5, min_price=10, min_dollar_vol=1000, adv_window=3, staleness=7d
    bars = _bars(5, 20.0, 100.0, end=D0)  # 5 bars, $20, ADV$ = 20*100 = 2000 >= 1000, last bar == D
    r = resolve_candidate(bars, "AAA", cfg, D0)
    assert r.admitted is True and r.reason is None and r.bars == 5


def test_resolve_candidate_below_history_excluded_first():
    cfg = _cfg()
    bars = _bars(4, 20.0, 100.0, end=D0)  # only 4 bars < 5
    r = resolve_candidate(bars, "AAA", cfg, D0)
    assert r.admitted is False and r.reason == REASON_BELOW_HISTORY and r.bars == 4


def test_resolve_candidate_zero_bars_is_below_history():
    cfg = _cfg()
    r = resolve_candidate([], "AAA", cfg, D0)
    assert r.admitted is False and r.reason == REASON_BELOW_HISTORY and r.bars == 0


def test_resolve_candidate_below_price_excluded():
    cfg = _cfg()
    bars = _bars(5, 9.0, 100000.0, end=D0)  # enough history + ADV but price $9 < $10
    r = resolve_candidate(bars, "AAA", cfg, D0)
    assert r.admitted is False and r.reason == REASON_BELOW_PRICE


def test_resolve_candidate_below_adv_excluded():
    cfg = _cfg()
    bars = _bars(5, 20.0, 1.0, end=D0)  # price ok, but ADV$ = 20*1 = 20 < 1000
    r = resolve_candidate(bars, "AAA", cfg, D0)
    assert r.admitted is False and r.reason == REASON_BELOW_ADV


def test_resolve_candidate_gate_order_history_before_price():
    """A candidate failing BOTH history and price records below_history (the first gate)."""
    cfg = _cfg()
    bars = _bars(2, 9.0, 1.0, end=D0)  # too few bars AND too cheap AND too thin
    r = resolve_candidate(bars, "AAA", cfg, D0)
    assert r.reason == REASON_BELOW_HISTORY  # history is checked first


# --------------------------------------------------------------------------------------------------
# iter-18 — the RECENCY/STALENESS gate (pure unit): boundary, order, and the misalignment closure.
# --------------------------------------------------------------------------------------------------
def test_resolve_candidate_stale_series_excluded():
    """A candidate whose LAST bar is more than max_staleness_days before D is excluded as
    stale_series — enough history, fine price, fine ADV, but the series has ENDED."""
    cfg = _cfg()  # max_staleness_days = 7
    last = D0 - timedelta(days=8)  # 8 > 7 — stale
    bars = _bars(10, 20.0, 100.0, end=last)
    r = resolve_candidate(bars, "AAA", cfg, D0)
    assert r.admitted is False and r.reason == REASON_STALE and r.bars == 10


def test_resolve_candidate_staleness_boundary_admitted_at_threshold():
    """The gate is `> max_staleness_days` (a gap of EXACTLY the threshold still passes): last bar
    D-7 with a 7-day threshold is admitted; last bar D-8 is excluded."""
    cfg = _cfg()  # max_staleness_days = 7
    at_threshold = resolve_candidate(_bars(10, 20.0, 100.0, end=D0 - timedelta(days=7)), "AAA", cfg, D0)
    past_threshold = resolve_candidate(_bars(10, 20.0, 100.0, end=D0 - timedelta(days=8)), "AAA", cfg, D0)
    assert at_threshold.admitted is True and at_threshold.reason is None
    assert past_threshold.admitted is False and past_threshold.reason == REASON_STALE


def test_resolve_candidate_last_bar_on_d_is_fresh():
    cfg = _cfg()
    r = resolve_candidate(_bars(6, 20.0, 100.0, end=D0), "AAA", cfg, D0)
    assert r.admitted is True


def test_resolve_candidate_gate_order_staleness_before_price_and_adv():
    """Deterministic fixed gate order (history -> staleness -> price -> ADV): a STALE and CHEAP and
    THIN candidate records stale_series (staleness precedes price/ADV), while a SHORT and stale
    candidate still records below_history (history remains the first gate)."""
    cfg = _cfg()
    stale_cheap_thin = resolve_candidate(
        _bars(10, 9.0, 1.0, end=D0 - timedelta(days=30)), "AAA", cfg, D0
    )
    assert stale_cheap_thin.reason == REASON_STALE
    short_and_stale = resolve_candidate(
        _bars(3, 20.0, 100.0, end=D0 - timedelta(days=30)), "AAA", cfg, D0
    )
    assert short_and_stale.reason == REASON_BELOW_HISTORY


def test_exclusion_reasons_vocabulary_has_the_staleness_reason_in_gate_order():
    """The reason vocabulary carries the new stale_series label, ordered exactly as the gates run."""
    assert EXCLUSION_REASONS == (
        REASON_BELOW_HISTORY,
        REASON_STALE,
        REASON_BELOW_PRICE,
        REASON_BELOW_ADV,
    )
    assert REASON_STALE == "stale_series"


# --------------------------------------------------------------------------------------------------
# DB-backed resolve_members / resolve_with_reasons over synthetic bars + a throwaway pool.
# --------------------------------------------------------------------------------------------------
def _seed_bars(session: Session, symbol: str, start: date, closes: list[float], volume: float):
    """Insert `len(closes)` consecutive daily bars for `symbol` starting at `start`."""
    for i, c in enumerate(closes):
        session.add(
            DailyPrice(
                symbol=symbol, date=start + timedelta(days=i),
                open=c, high=c, low=c, close=c, volume=volume,
            )
        )
    session.commit()


def test_resolve_members_warmup_boundary(tmp_path):
    """The warm-up boundary is the deterministic seed-start + (min_history_bars - 1) bars: a name with
    exactly the threshold bars is admitted on its threshold-th date and EMPTY before it."""
    cfg = _cfg()  # min_history_bars = 5
    seed_dir = _write_pool(tmp_path, ["AAA"])
    engine = make_engine(f"sqlite:///{tmp_path / 'w.db'}")
    create_db_and_tables(engine)
    start = date(2024, 1, 1)
    with Session(engine) as session:
        _seed_bars(session, "AAA", start, [20.0] * 10, volume=1000.0)  # ADV$ = 20*1000 = 20000 >= 1000
        # before the boundary (4th bar, only 4 <= D bars) → empty universe
        d4 = start + timedelta(days=3)
        assert resolve_members(session, d4, cfg, seed_dir=seed_dir) == []
        # ON the boundary (5th bar, 5 bars <= D) → admitted
        d5 = start + timedelta(days=4)
        assert resolve_members(session, d5, cfg, seed_dir=seed_dir) == ["AAA"]


def test_resolve_no_lookahead_tail_invariance(tmp_path):
    """Removing bars dated > D never changes D's resolved members (the forward_return tail-invariance
    idiom): the resolution at D over the full series equals the resolution at D over only the <= D bars."""
    cfg = _cfg()
    seed_dir = _write_pool(tmp_path, ["AAA"])
    engine_full = make_engine(f"sqlite:///{tmp_path / 'full.db'}")
    engine_trunc = make_engine(f"sqlite:///{tmp_path / 'trunc.db'}")
    create_db_and_tables(engine_full)
    create_db_and_tables(engine_trunc)
    start = date(2024, 1, 1)
    d = start + timedelta(days=5)  # D = the 6th calendar day
    with Session(engine_full) as s_full:
        _seed_bars(s_full, "AAA", start, [20.0] * 20, volume=1000.0)  # full series, bars past D too
        full = resolve_members(s_full, d, cfg, seed_dir=seed_dir)
        full_diag = resolve_with_reasons(s_full, d, cfg, seed_dir=seed_dir)
    with Session(engine_trunc) as s_trunc:
        # ONLY bars with date <= D exist here
        ndays = (d - start).days + 1
        _seed_bars(s_trunc, "AAA", start, [20.0] * ndays, volume=1000.0)
        trunc = resolve_members(s_trunc, d, cfg, seed_dir=seed_dir)
        trunc_diag = resolve_with_reasons(s_trunc, d, cfg, seed_dir=seed_dir)
    assert full == trunc  # the future bars in engine_full never changed D's membership
    assert full_diag["admitted"] == trunc_diag["admitted"]
    assert full_diag["resolutions"] == trunc_diag["resolutions"]


def test_resolve_first_qualifying_date_entry(tmp_path):
    """A name enters on the FIRST date it clears all gates: it is cheap before, then becomes
    admitted exactly when price crosses the threshold (history + ADV already satisfied)."""
    cfg = _cfg()  # min_history=5, min_price=10
    seed_dir = _write_pool(tmp_path, ["AAA"])
    engine = make_engine(f"sqlite:///{tmp_path / 'q.db'}")
    create_db_and_tables(engine)
    start = date(2024, 1, 1)
    # 5 cheap bars ($9), then a 6th bar at $12 (now price clears) — history(6>=5)+ADV ok.
    closes = [9.0, 9.0, 9.0, 9.0, 9.0, 12.0]
    with Session(engine) as session:
        _seed_bars(session, "AAA", start, closes, volume=1000.0)
        d5 = start + timedelta(days=4)  # 5 bars, all $9 → below_price
        r5 = resolve_with_reasons(session, d5, cfg, seed_dir=seed_dir)
        assert r5["admitted"] == [] and r5["excluded_counts"][REASON_BELOW_PRICE] == 1
        d6 = start + timedelta(days=5)  # 6 bars, last $12 → admitted on the first qualifying date
        r6 = resolve_with_reasons(session, d6, cfg, seed_dir=seed_dir)
        assert r6["admitted"] == ["AAA"]


def test_resolve_with_reasons_excluded_by_reason_counts(tmp_path):
    """The diagnostic reports admitted + the excluded-by-reason counts against the candidate-pool
    denominator: one passer, one below_history, one below_price, one below_adv, one stale_series
    (= the whole pool). The counts dict is keyed by the FULL 4-reason vocabulary."""
    cfg = _cfg()  # min_history=5, min_price=10, min_dollar_vol=1000, adv_window=3, staleness=7d
    seed_dir = _write_pool(tmp_path, ["PASS", "SHORT", "CHEAP", "THIN", "ENDED"])
    engine = make_engine(f"sqlite:///{tmp_path / 'd.db'}")
    create_db_and_tables(engine)
    start = date(2024, 1, 1)
    D = start + timedelta(days=9)
    with Session(engine) as session:
        _seed_bars(session, "PASS", start, [20.0] * 10, volume=1000.0)   # admitted (fresh through D)
        _seed_bars(session, "SHORT", start, [20.0] * 3, volume=1000.0)   # below_history (3 < 5)
        _seed_bars(session, "CHEAP", start, [5.0] * 10, volume=100000.0) # below_price ($5 < $10)
        _seed_bars(session, "THIN", start, [20.0] * 10, volume=1.0)      # below_adv (20*1 = 20 < 1000)
        # ENDED: plenty of history but its data STOPS 30 days before D → stale_series (iter-18)
        _seed_bars(session, "ENDED", start - timedelta(days=40), [20.0] * 10, volume=1000.0)
        out = resolve_with_reasons(session, D, cfg, seed_dir=seed_dir)
    assert out["candidate_pool_count"] == 5
    assert out["admitted"] == ["PASS"] and out["admitted_count"] == 1
    assert out["excluded_counts"] == {
        REASON_BELOW_HISTORY: 1, REASON_STALE: 1, REASON_BELOW_PRICE: 1, REASON_BELOW_ADV: 1,
    }
    assert sum(out["excluded_counts"].values()) == out["candidate_pool_count"] - out["admitted_count"]
    assert set(EXCLUSION_REASONS) == set(out["excluded_counts"])


def test_stale_member_exits_membership_and_never_feeds_rs(tmp_path):
    """iter-18 (J-12): the rs_vs positional-misalignment closure. A name whose data ends mid-history is
    a member while fresh and EXITS cleanly once its last bar falls more than the staleness threshold
    behind D — it is then NEVER in the resolved membership that `score_stocks` iterates, so its bars can
    never be positionally aligned against a benchmark window ending at D."""
    cfg = _cfg()  # staleness=7d
    seed_dir = _write_pool(tmp_path, ["LIVE", "ENDS"])
    engine = make_engine(f"sqlite:///{tmp_path / 's.db'}")
    create_db_and_tables(engine)
    start = date(2024, 1, 1)
    ends_last = start + timedelta(days=19)  # ENDS trades for 20 days then stops
    with Session(engine) as session:
        _seed_bars(session, "LIVE", start, [20.0] * 60, volume=1000.0)
        _seed_bars(session, "ENDS", start, [20.0] * 20, volume=1000.0)
        # While ENDS is fresh (D == its last bar) both are members.
        both = resolve_members(session, ends_last, cfg, seed_dir=seed_dir)
        assert both == ["ENDS", "LIVE"]
        # Within the threshold after its last bar it is STILL a member (holiday-gap tolerance)…
        still = resolve_members(session, ends_last + timedelta(days=7), cfg, seed_dir=seed_dir)
        assert "ENDS" in still
        # …and once past the threshold it exits cleanly — LIVE alone remains.
        after = resolve_with_reasons(session, ends_last + timedelta(days=8), cfg, seed_dir=seed_dir)
        assert after["admitted"] == ["LIVE"]
        ends_row = next(r for r in after["resolutions"] if r["symbol"] == "ENDS")
        assert ends_row["reason"] == REASON_STALE


def test_resolve_empty_db_is_honest_empty(tmp_path):
    """An empty DB (no bars at all) → every pool candidate is below_history, admitted is empty — honest,
    no fabricated members/date."""
    cfg = _cfg()
    seed_dir = _write_pool(tmp_path, ["AAA", "BBB"])
    engine = make_engine(f"sqlite:///{tmp_path / 'e.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        out = resolve_with_reasons(session, date(2024, 6, 1), cfg, seed_dir=seed_dir)
    assert out["admitted"] == []


# ==================================================================================================
# ops-hardening iter-53 (J-05/J-07, GIL-hold bound — TC-3) — `resolve_with_reasons` now fetches a
# BOUNDED trailing window (`bars_asof_window`, `adv_window_days` wide) per admitted-history candidate
# instead of the FULL <= asof prefix (`bars_asof`), and passes the already-known trailing `bar_count`
# through explicitly rather than re-deriving it from `len(bars)`. A live GIL-stall profile (this
# iteration's `reports/perf-budgets.md` addendum) proved the FULL fetch was the real GIL-hold source —
# not a `sorted()` call and not a GC pause. `bars_asof_window`'s OWN byte-identity to
# `bars_asof(...)[-lookback:]` is proven separately (test_bar_cache.py); these tests prove
# `resolve_with_reasons`'s DISCLOSED output is unaffected by fetching less than the full history.
# ==================================================================================================
def test_resolve_with_reasons_bars_count_is_true_history_not_the_bounded_fetch_window(tmp_path):
    """The disclosed `resolutions[...]['bars']` count is the symbol's TRUE trailing-bar count (50), never
    the bounded ADV-window fetch size (3, `_cfg()`'s `adv_window_days`) — proving `bar_count` is passed
    through from the already-known count, not re-derived from the (now-windowed) `bars` list length. This
    is the exact regression a careless windowing fix would introduce (silently truncating the disclosed
    history count to the fetch window)."""
    cfg = _cfg()  # adv_window_days = 3 -- deliberately far smaller than the seeded history below
    seed_dir = _write_pool(tmp_path, ["LONGHIST"])
    engine = make_engine(f"sqlite:///{tmp_path / 'lh.db'}")
    create_db_and_tables(engine)
    start = date(2024, 1, 1)
    with Session(engine) as session:
        _seed_bars(session, "LONGHIST", start, [20.0] * 50, volume=1000.0)  # 50 bars >> adv_window_days=3
        d = start + timedelta(days=49)  # the 50th (last) bar
        out = resolve_with_reasons(session, d, cfg, seed_dir=seed_dir)
    assert out["admitted"] == ["LONGHIST"]
    row = out["resolutions"][0]
    assert row["bars"] == 50, (
        f"expected the TRUE 50-bar trailing history, not the {cfg.universe.filters.adv_window_days}-bar "
        f"fetch window — got {row['bars']}"
    )


def test_resolve_with_reasons_byte_identical_with_and_without_an_active_bar_cache(tmp_path):
    """`bars_asof_window` takes a DIFFERENT internal path depending on whether an outer `bar_cache`
    context is active (the `_BarCache.bars_asof_window` slice — the ingest finalize-tail shape this
    iteration profiled) or not (a bounded `LIMIT`-query fallback — the default per-request shape). Both
    must resolve the SAME candidates for the SAME inputs — proven here by running the identical scenario
    both ways and asserting the full diagnostic payload is equal."""
    from app.engine.prices import bar_cache

    cfg = _cfg()
    seed_dir = _write_pool(tmp_path, ["PASS", "SHORT", "CHEAP", "THIN", "ENDED"])
    engine = make_engine(f"sqlite:///{tmp_path / 'cache_ab.db'}")
    create_db_and_tables(engine)
    start = date(2024, 1, 1)
    D = start + timedelta(days=9)
    with Session(engine) as session:
        _seed_bars(session, "PASS", start, [20.0] * 10, volume=1000.0)
        _seed_bars(session, "SHORT", start, [20.0] * 3, volume=1000.0)
        _seed_bars(session, "CHEAP", start, [5.0] * 10, volume=100000.0)
        _seed_bars(session, "THIN", start, [20.0] * 10, volume=1.0)
        _seed_bars(session, "ENDED", start - timedelta(days=40), [20.0] * 10, volume=1000.0)

    with Session(engine) as session:
        no_cache = resolve_with_reasons(session, D, cfg, seed_dir=seed_dir)  # default (no active cache)
    with Session(engine) as session:
        with bar_cache(session):
            with_cache = resolve_with_reasons(session, D, cfg, seed_dir=seed_dir)  # active cache

    assert with_cache == no_cache


@pytest.mark.parametrize("history_bars", [1, 2, 3, 4, 5, 10])
def test_resolve_with_reasons_adv_window_boundary_exact_short_and_long_history(tmp_path, history_bars):
    """Boundary sweep around `adv_window_days` (3): a symbol with FEWER, EXACTLY, and MORE trailing bars
    than the fetch window must classify identically to the pre-iter-53 full-fetch behavior — proven via
    `resolve_candidate` called directly on the FULL bars (the pre-existing, unchanged pure-unit contract)
    as the reference oracle for what `resolve_with_reasons` (the bounded-fetch path) must still produce."""
    cfg = _cfg()  # min_history_bars=5, adv_window_days=3
    seed_dir = _write_pool(tmp_path, ["SYM"])
    engine = make_engine(f"sqlite:///{tmp_path / f'boundary_{history_bars}.db'}")
    create_db_and_tables(engine)
    start = date(2024, 1, 1)
    with Session(engine) as session:
        _seed_bars(session, "SYM", start, [20.0] * history_bars, volume=1000.0)
        d = start + timedelta(days=history_bars - 1)
        out = resolve_with_reasons(session, d, cfg, seed_dir=seed_dir)

    full_bars = _bars(history_bars, 20.0, 1000.0, end=d)
    reference = resolve_candidate(full_bars, "SYM", cfg, d)  # the unchanged pure-unit oracle
    row = out["resolutions"][0]
    assert row["admitted"] == reference.admitted
    assert row["reason"] == reference.reason
    assert row["bars"] == reference.bars == history_bars
