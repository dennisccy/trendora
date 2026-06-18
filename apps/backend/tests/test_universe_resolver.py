"""iter-33 (J-93 / J-94) — the per-as-of-date point-in-time universe resolver.

FAST synthetic tests (no seed boot — iter-29 lesson): a tiny in-memory DB with hand-made bars + a
throwaway candidate-pool CSV exercise every resolver leg in milliseconds. The seed-loading
`loaded_engine`-fixture cross-checks live in test_universe_screen.py / test_data_manager.py.
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
    resolve_candidate,
    resolve_members,
    resolve_with_reasons,
)
from app.models import DailyPrice


# --------------------------------------------------------------------------------------------------
# Test config: a small, distinctive threshold set so the gates are easy to reason about.
# --------------------------------------------------------------------------------------------------
def _cfg():
    """A real Config with a SMALL min_history_bars + clear price/ADV cutoffs so synthetic series are
    cheap. Reads through model_copy so all other required keys stay valid."""
    cfg = load_config().model_copy(deep=True)
    cfg = cfg.model_copy(
        update={"indicators": cfg.indicators.model_copy(update={"min_history_bars": 5})}
    )
    cfg = cfg.model_copy(
        update={
            "universe": cfg.universe.model_copy(
                update={
                    "filters": cfg.universe.filters.model_copy(
                        update={"min_price": 10.0, "min_dollar_vol": 1000.0, "adv_window_days": 3}
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

    def __init__(self, close, volume):
        self.close = close
        self.volume = volume


# --------------------------------------------------------------------------------------------------
# PURE resolve_candidate — each gate exercised in isolation (no DB).
# --------------------------------------------------------------------------------------------------
def test_resolve_candidate_admits_when_all_three_gates_pass():
    cfg = _cfg()  # min_history=5, min_price=10, min_dollar_vol=1000, adv_window=3
    bars = [_Bar(20.0, 100.0) for _ in range(5)]  # 5 bars, $20, ADV$ = 20*100 = 2000 >= 1000
    r = resolve_candidate(bars, "AAA", cfg)
    assert r.admitted is True and r.reason is None and r.bars == 5


def test_resolve_candidate_below_history_excluded_first():
    cfg = _cfg()
    bars = [_Bar(20.0, 100.0) for _ in range(4)]  # only 4 bars < 5
    r = resolve_candidate(bars, "AAA", cfg)
    assert r.admitted is False and r.reason == REASON_BELOW_HISTORY and r.bars == 4


def test_resolve_candidate_zero_bars_is_below_history():
    cfg = _cfg()
    r = resolve_candidate([], "AAA", cfg)
    assert r.admitted is False and r.reason == REASON_BELOW_HISTORY and r.bars == 0


def test_resolve_candidate_below_price_excluded():
    cfg = _cfg()
    bars = [_Bar(9.0, 100000.0) for _ in range(5)]  # enough history + ADV but price $9 < $10
    r = resolve_candidate(bars, "AAA", cfg)
    assert r.admitted is False and r.reason == REASON_BELOW_PRICE


def test_resolve_candidate_below_adv_excluded():
    cfg = _cfg()
    bars = [_Bar(20.0, 1.0) for _ in range(5)]  # price ok, but ADV$ = 20*1 = 20 < 1000
    r = resolve_candidate(bars, "AAA", cfg)
    assert r.admitted is False and r.reason == REASON_BELOW_ADV


def test_resolve_candidate_gate_order_history_before_price():
    """A candidate failing BOTH history and price records below_history (the first gate)."""
    cfg = _cfg()
    bars = [_Bar(9.0, 1.0) for _ in range(2)]  # too few bars AND too cheap AND too thin
    r = resolve_candidate(bars, "AAA", cfg)
    assert r.reason == REASON_BELOW_HISTORY  # history is checked first


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
    """A name enters on the FIRST date it clears all three gates: it is cheap before, then becomes
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
    denominator: one passer, one below_history, one below_price, one below_adv (= the whole pool)."""
    cfg = _cfg()  # min_history=5, min_price=10, min_dollar_vol=1000, adv_window=3
    seed_dir = _write_pool(tmp_path, ["PASS", "SHORT", "CHEAP", "THIN"])
    engine = make_engine(f"sqlite:///{tmp_path / 'd.db'}")
    create_db_and_tables(engine)
    start = date(2024, 1, 1)
    D = start + timedelta(days=9)
    with Session(engine) as session:
        _seed_bars(session, "PASS", start, [20.0] * 10, volume=1000.0)   # admitted
        _seed_bars(session, "SHORT", start, [20.0] * 3, volume=1000.0)   # below_history (3 < 5)
        _seed_bars(session, "CHEAP", start, [5.0] * 10, volume=100000.0) # below_price ($5 < $10)
        _seed_bars(session, "THIN", start, [20.0] * 10, volume=1.0)      # below_adv (20*1 = 20 < 1000)
        out = resolve_with_reasons(session, D, cfg, seed_dir=seed_dir)
    assert out["candidate_pool_count"] == 4
    assert out["admitted"] == ["PASS"] and out["admitted_count"] == 1
    assert out["excluded_counts"] == {
        REASON_BELOW_HISTORY: 1, REASON_BELOW_PRICE: 1, REASON_BELOW_ADV: 1,
    }
    assert sum(out["excluded_counts"].values()) == out["candidate_pool_count"] - out["admitted_count"]
    assert set(EXCLUSION_REASONS) == set(out["excluded_counts"])


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
    assert out["excluded_counts"][REASON_BELOW_HISTORY] == 2
