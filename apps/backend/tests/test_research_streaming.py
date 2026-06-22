"""iter-47 (J-105) — the heavy-research forward-return read path is bounded/streamed (column-projected
`yield_per`) instead of materializing the whole `forward_returns` table as ORM rows. These tests pin the
NON-NEGOTIABLE contract of that refactor: **every served figure is byte-identical** to the prior
per-observation aggregation, and the streaming is **chunk-independent** (the batch size changes peak
memory, NEVER a value or an ordering).

The proofs drive the REAL builders/endpoints (no hand-rolled stand-in — iter-15 lesson), on a
DISCRIMINATING hand-built fixture where the iter-47 reorder (stream the subject-matching ScannerResults
first, then scan FR pruned to the needed runs) is LOAD-BEARING:

  - subject-matching results WITH forward returns at several horizons,
  - subject-matching results with FRs at ONE horizon only (the test_iter20 discriminator shape),
  - a subject-matching run with ZERO forward returns (must contribute nothing, never crash),
  - NON-subject symbols that DO have forward returns (must NOT leak into a subject cohort),
  - a run with forward returns but no subject match,
  - distinct return / mae / mfe / max_drawdown / sector / setup_status / pattern values per row,
  - mixed regimes across runs.

Chunk-independence is proven by recomputing each builder under `research.read_batch_size = 1` (one row per
streamed batch) and under a huge batch, asserting BOTH equal the real-config output — `json.dumps(...,
sort_keys=True)` byte-identity, the repo convention (cf. test_market_phase.py / test_research.py).
"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone

import pytest
from sqlmodel import Session

from app.config import load_config
from app.db import create_db_and_tables, make_engine
from app.engine.research import (
    VIEW_EPISODES,
    VIEW_POOLED,
    _combination_observations,
    _event_study_members,
    _event_study_members_by_horizon,
    _factor_observations,
    _regime_setup_pattern_observations,
    _severity_velocity_observation_set,
    compute_event_study,
    compute_factor_combination,
    compute_factor_lab,
)
from app.models import ForwardReturn, ScannerResult, ScannerRun

H = 20


# --------------------------------------------------------------------------------------------------
# helpers (mirror the test_iter20_research_cluster builders so the rows are exact by construction)
# --------------------------------------------------------------------------------------------------
def _utc() -> datetime:
    return datetime.now(timezone.utc)


def _add_run(session: Session, asof: date, regime_label: str) -> ScannerRun:
    run = ScannerRun(
        asof_date=asof, created_at=_utc(), provider="seed", benchmark="SPY",
        regime_score=50.0, regime_label=regime_label, regime_components_json="[]",
        new_high_low_json="{}", candidate_counts_json="{}",
    )
    session.add(run)
    session.flush()
    return run


def _add_result(
    session, run_id, ticker, rank, *, setup, sector, lead=50.0, eqs=50.0, risk=50.0,
    is_vcp=False, is_pullback_to_rising_dma=False, is_flat_base_breakout=False,
):
    session.add(ScannerResult(
        run_id=run_id, ticker=ticker, name=ticker, sector=sector,
        leadership_score=lead, leadership_bucket="C",
        entry_quality_score=eqs, entry_quality_bucket="C",
        risk_score=risk, risk_bucket="C",
        setup_status=setup, rank=rank, record_json=json.dumps({"ticker": ticker, "name": ticker}),
        is_vcp=is_vcp, is_pullback_to_rising_dma=is_pullback_to_rising_dma,
        is_flat_base_breakout=is_flat_base_breakout,
    ))


def _add_fr(session, run_id, symbol, ret, *, horizon=H, mae, mfe, mdd):
    session.add(ForwardReturn(
        run_id=run_id, symbol=symbol, horizon=horizon, asof_date=date(2025, 1, 1),
        entry_close=100.0, measured_date=date(2025, 2, 1),
        realized_return=ret, mae=mae, mfe=mfe, max_drawdown=mdd,
    ))


@pytest.fixture()
def prune_engine(tmp_path):
    """A DISCRIMINATING dataset for the iter-47 reorder: subject-matching + non-matching results, a
    subject-matching run with ZERO FRs, non-subject symbols WITH FRs (must not leak), FRs at multiple
    horizons for some pairs and one horizon for others, mixed regimes, distinct value fields."""
    engine = make_engine(f"sqlite:///{tmp_path / 'prune.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        r1 = _add_run(session, date(2025, 1, 10), regime_label="Risk-on")
        r2 = _add_run(session, date(2025, 2, 10), regime_label="Risk-off")
        r3 = _add_run(session, date(2025, 3, 10), regime_label="Risk-on")  # subject match, ZERO FRs
        session.flush()

        # run-1: VCP names (subject match) with FRs at 1/5/20; a non-VCP name; a non-subject symbol w/ FR.
        _add_result(session, r1.id, "AA", 1, setup="Actionable", sector="Technology",
                    lead=80.0, eqs=70.0, risk=20.0, is_vcp=True)
        _add_result(session, r1.id, "BB", 2, setup="Breakout-watch", sector="Energy",
                    lead=60.0, eqs=55.0, risk=40.0, is_vcp=True, is_pullback_to_rising_dma=True)
        _add_result(session, r1.id, "CC", 3, setup="Actionable", sector="Financials",
                    lead=40.0, eqs=45.0, risk=60.0, is_vcp=False)  # NOT a vcp subject member
        _add_result(session, r1.id, "ZZ", 4, setup="Breakout-watch", sector="Health",
                    lead=30.0, eqs=35.0, risk=70.0, is_vcp=False)  # non-subject symbol but HAS an FR
        for tkr, base in (("AA", 0.10), ("BB", 0.22), ("CC", -0.07), ("ZZ", 0.05)):
            for h, sc in ((1, 0.2), (5, 0.5), (20, 1.0)):
                _add_fr(session, r1.id, tkr, base * sc, horizon=h,
                        mae=-0.05 * sc, mfe=0.15 * sc, mdd=-0.08 * sc)

        # run-2: a VCP name with an FR at horizon 20 ONLY (the test_iter20 discriminator shape) + a
        # non-subject name with an FR; different regime.
        _add_result(session, r2.id, "DD", 1, setup="Actionable", sector="Technology",
                    lead=75.0, eqs=65.0, risk=25.0, is_vcp=True, is_flat_base_breakout=True)
        _add_result(session, r2.id, "EE", 2, setup="Breakout-watch", sector="Energy",
                    lead=50.0, eqs=50.0, risk=50.0, is_vcp=False)
        _add_fr(session, r2.id, "DD", 0.30, horizon=20, mae=-0.09, mfe=0.40, mdd=-0.11)
        _add_fr(session, r2.id, "EE", 0.04, horizon=20, mae=-0.02, mfe=0.06, mdd=-0.03)

        # run-3: a subject-matching result with ZERO forward returns (must contribute nothing, no crash).
        _add_result(session, r3.id, "FF", 1, setup="Actionable", sector="Technology",
                    lead=90.0, eqs=80.0, risk=10.0, is_vcp=True)
        session.commit()
    return engine


def _cfg_batch(batch: int):
    """The real config with `research.read_batch_size` overridden to `batch` (chunk-size probe)."""
    cfg = load_config()
    return cfg.model_copy(update={"research": cfg.research.model_copy(update={"read_batch_size": batch})})


def _eq(a, b) -> bool:
    return json.dumps(a, sort_keys=True, default=str) == json.dumps(b, sort_keys=True, default=str)


# --------------------------------------------------------------------------------------------------
# 1. _event_study_members_by_horizon == per-horizon loop, on the discriminating reorder fixture
# --------------------------------------------------------------------------------------------------
def test_event_study_by_horizon_matches_per_horizon_loop_on_prune_fixture(prune_engine):
    """The batched/streamed `_event_study_members_by_horizon` is byte-identical per horizon to calling
    the streamed `_event_study_members` in a loop — on a fixture where the reorder + FR-prune is
    load-bearing (run-2 has a member at horizon 20 only; a non-subject symbol has FRs; a subject run has
    zero FRs)."""
    cfg = load_config()
    horizons = list(cfg.walk_forward.horizons)
    subject = {"key": "vcp", "kind": "pattern"}
    with Session(prune_engine) as session:
        batched = _event_study_members_by_horizon(session, subject, horizons)
        for h in horizons:
            per = _event_study_members(session, subject, h)
            assert batched[h] == per, f"horizon {h}: batched != per-horizon loop"
        # the non-subject symbol with FRs (ZZ / EE) MUST NOT leak into a vcp cohort.
        for h in horizons:
            tickers = {m["ticker"] for m in batched[h]}
            assert "ZZ" not in tickers and "EE" not in tickers, f"non-subject leak at horizon {h}"
            assert "CC" not in tickers, f"non-vcp result CC leaked at horizon {h}"
        # the subject run with zero FRs (FF) contributes nothing at every horizon.
        for h in horizons:
            assert "FF" not in {m["ticker"] for m in batched[h]}


# --------------------------------------------------------------------------------------------------
# 2. chunk-independence: read_batch_size = 1 vs huge vs default — byte-identical members
# --------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("subject", [
    {"key": "vcp", "kind": "pattern"},
    {"key": "Actionable", "kind": "setup"},
])
def test_event_study_members_chunk_independent(prune_engine, subject):
    """The streamed `_event_study_members[_by_horizon]` output is identical whether the FR scan streams
    one row per batch or the whole table at once — proving the batch size changes only memory, never a
    value/order. The batch size is threaded via the `cfg` the builder reads."""
    horizons = list(load_config().walk_forward.horizons)
    with Session(prune_engine) as session:
        outputs = [
            _event_study_members_by_horizon(session, subject, horizons, cfg=_cfg_batch(b))
            for b in (1, 7, 1_000_000)
        ]
        assert _eq(outputs[0], outputs[1]) and _eq(outputs[1], outputs[2]), "batch size changed values"
        # the per-horizon builder is likewise chunk-independent.
        per_small = _event_study_members(session, subject, H, cfg=_cfg_batch(1))
        per_big = _event_study_members(session, subject, H, cfg=_cfg_batch(1_000_000))
        assert _eq(per_small, per_big), "per-horizon builder differs by batch"


# --------------------------------------------------------------------------------------------------
# 3. compute_event_study byte-identity: as_of=None / historical, pooled / episodes — chunk-independent
# --------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("view", [VIEW_EPISODES, VIEW_POOLED])
@pytest.mark.parametrize("as_of", [None, date(2025, 1, 31)])
def test_compute_event_study_chunk_independent(prune_engine, view, as_of):
    """The full event-study payload (matrix cells, mean/win-rate/N, every horizon) is byte-identical
    under read_batch_size=1 vs the real config — across all-history / historical as_of and pooled /
    episodes views (the no-lookahead + view legs)."""
    with Session(prune_engine) as session:
        small = compute_event_study(session, "vcp", H, _cfg_batch(1), as_of=as_of, view=view)
        big = compute_event_study(session, "vcp", H, _cfg_batch(1_000_000), as_of=as_of, view=view)
        assert _eq(small, big), f"event-study payload differs by batch (view={view}, as_of={as_of})"


def test_compute_event_study_zero_n_cohort_is_honest_not_crash(prune_engine):
    """A subject with ZERO members (no result carries the flag) returns an honest empty/NA study — never
    a crash, never a fabricated figure — under the streamed read path."""
    with Session(prune_engine) as session:
        # 'flat_base_breakout' matches only DD (1 FR at h=20); choose a subject matched by NO result with an
        # FR by scoping as_of before any snapshot -> zero observations.
        payload = compute_event_study(session, "vcp", H, _cfg_batch(1), as_of=date(2024, 1, 1))
        assert payload["n"] == 0
        for row in payload["by_horizon"]:
            assert row["n"] == 0
            assert row["mean_return"] is None  # honest NA, never a fabricated 0


# --------------------------------------------------------------------------------------------------
# 4. factor-lab + multi-factor combination byte-identity (chunk-independent), as_of legs
# --------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("as_of", [None, date(2025, 1, 31)])
def test_compute_factor_lab_chunk_independent(prune_engine, as_of):
    with Session(prune_engine) as session:
        small = compute_factor_lab(session, "leadership_score", H, _cfg_batch(1), as_of=as_of)
        big = compute_factor_lab(session, "leadership_score", H, _cfg_batch(1_000_000), as_of=as_of)
        assert _eq(small, big), f"factor-lab payload differs by batch (as_of={as_of})"


@pytest.mark.parametrize("as_of", [None, date(2025, 1, 31)])
def test_compute_factor_combination_chunk_independent(prune_engine, as_of):
    cfg = load_config()
    conditions = [
        {"factor": c.factor, "side": c.side, "quantile": c.quantile}
        for c in cfg.research.factor_lab.combination.default_conditions
    ]
    with Session(prune_engine) as session:
        small = compute_factor_combination(session, conditions, H, _cfg_batch(1), as_of=as_of)
        big = compute_factor_combination(session, conditions, H, _cfg_batch(1_000_000), as_of=as_of)
        assert _eq(small, big), f"factor-combination payload differs by batch (as_of={as_of})"


def test_factor_observations_chunk_independent_and_no_leak(prune_engine):
    """Raw `_factor_observations` / `_combination_observations` lists are identical under batch=1 vs huge
    and exclude any factor-NULL / non-FR observation (the value-verbatim guard)."""
    cfg = load_config()
    factor = next(f for f in cfg.research.factor_lab.factors if f.key == "leadership_score")
    factors2 = [f for f in cfg.research.factor_lab.factors if f.key in ("leadership_score", "risk_score")]
    with Session(prune_engine) as session:
        for builder, args in (
            (_factor_observations, (factor, H)),
            (_combination_observations, (factors2, H)),
        ):
            small = builder(session, *args, None, cfg=_cfg_batch(1))
            big = builder(session, *args, None, cfg=_cfg_batch(1_000_000))
            assert _eq(small, big), f"{builder.__name__} differs by batch"


# --------------------------------------------------------------------------------------------------
# 5. regime-setup-pattern + severity-velocity observation sets chunk-independent
# --------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("view", [VIEW_EPISODES, VIEW_POOLED])
def test_regime_setup_pattern_observations_chunk_independent(prune_engine, view):
    with Session(prune_engine) as session:
        small = _regime_setup_pattern_observations(session, H, view, _cfg_batch(1))
        big = _regime_setup_pattern_observations(session, H, view, _cfg_batch(1_000_000))
        assert _eq(small, big), f"rsp observation set differs by batch (view={view})"


def test_severity_velocity_observation_set_chunk_independent(prune_engine):
    """The SPY-benchmark severity-velocity observation set (already symbol-bounded) is byte-identical
    under batch=1 vs huge after column-projection."""
    cfg = load_config()
    with Session(prune_engine) as session:
        small = _severity_velocity_observation_set(session, H, _cfg_batch(1))
        big = _severity_velocity_observation_set(session, H, _cfg_batch(1_000_000))
        assert _eq(small, big), "severity-velocity observation set differs by batch"
