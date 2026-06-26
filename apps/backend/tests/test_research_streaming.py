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
    _all_factor_observations_by_horizon,
    _combination_observations,
    _event_study_members,
    _event_study_members_by_horizon,
    _factor_observations,
    _regime_setup_pattern_observations,
    _severity_velocity_observation_set,
    compute_event_study,
    compute_factor_combination,
    compute_factor_lab,
    compute_factor_lab_all,
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


# ==================================================================================================
# iter-48 (J-105): the ScannerResult-side read in `_factor_observations` (research.py:216) and
# `_combination_observations` (research.py:421) is now ALSO `yield_per`-streamed (the live Factor-Lab
# MemoryError site — Factor Lab is UNCACHED so it recomputes the observation set every request). These
# proofs pin the NON-NEGOTIABLE byte-identity of that ScannerResult-side streaming:
#
#   1. The streamed FULL ORM row (NOT a column projection) keeps `record_json` available, so a COMPONENT
#      factor (which reads `record_json[block]["components"][name]["raw"]`) is byte-identical — a naive
#      narrow projection would drop `record_json` and silently change component-factor figures.
#   2. `.order_by(ScannerResult.id)` reproduces the prior implicit-`.all()` row order, so the observation
#      list (and every downstream decile / rank-IC / by_regime / composite / strict_overlap figure) is
#      byte-identical regardless of the streaming batch size.
#   3. A zero-N cohort stays an honest empty/NA result (never a crash, never a fabricated row).
# ==================================================================================================
def _component_record_json(ticker: str, rs_spy_3m: float, atr_pct: float) -> str:
    """A `record_json` blob carrying the two component factors used in the default combination conditions
    (`leadership.components.rs_spy_3m.raw` and `risk.components.atr_pct.raw`) — the EXACT shape
    `_extract_factor_value` reads for a `component` factor. This is what would be LOST by a narrow column
    projection, so it is the load-bearing payload for the byte-identity-with-record_json proof."""
    return json.dumps({
        "ticker": ticker, "name": ticker,
        "leadership": {"components": [
            {"name": "rs_spy_3m", "raw": rs_spy_3m},
            {"name": "ma_stack", "raw": 0.5},
        ]},
        "risk": {"components": [
            {"name": "atr_pct", "raw": atr_pct},
        ]},
    })


@pytest.fixture()
def component_engine(tmp_path):
    """A fixture whose `record_json` carries REAL component-factor blocks so a `component` factor
    (`rs_spy_3m`, `atr_pct`) produces a non-trivial, non-empty observation pool — the case where dropping
    `record_json` in a narrow projection would silently change figures. Multiple runs/rows across mixed
    regimes + distinct component values + a subject-matching run with zero FRs (zero-N leg)."""
    engine = make_engine(f"sqlite:///{tmp_path / 'component.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        r1 = _add_run(session, date(2025, 1, 10), regime_label="Risk-on")
        r2 = _add_run(session, date(2025, 2, 10), regime_label="Risk-off")
        r3 = _add_run(session, date(2025, 3, 10), regime_label="Risk-on")  # zero-FR run (zero-N leg)
        session.flush()

        # run-1: three names with distinct rs_spy_3m / atr_pct component values + a column-factor spread.
        rows1 = [
            ("AA", 1, 90.0, 10.0, 0.80, 0.012, 0.10),
            ("BB", 2, 60.0, 40.0, 0.40, 0.030, 0.04),
            ("CC", 3, 30.0, 70.0, 0.10, 0.055, -0.06),
        ]
        for tkr, rank, lead, risk, rs, atr, ret in rows1:
            session.add(ScannerResult(
                run_id=r1.id, ticker=tkr, name=tkr, sector="Technology",
                leadership_score=lead, leadership_bucket="C",
                entry_quality_score=55.0, entry_quality_bucket="C",
                risk_score=risk, risk_bucket="C",
                setup_status="Actionable", rank=rank,
                record_json=_component_record_json(tkr, rs, atr),
            ))
            _add_fr(session, r1.id, tkr, ret, horizon=H, mae=-0.05, mfe=0.15, mdd=-0.08)

        # run-2 (different regime): one name with an FR at horizon 20 only, distinct component values.
        session.add(ScannerResult(
            run_id=r2.id, ticker="DD", name="DD", sector="Energy",
            leadership_score=75.0, leadership_bucket="C",
            entry_quality_score=65.0, entry_quality_bucket="C",
            risk_score=25.0, risk_bucket="C",
            setup_status="Actionable", rank=1,
            record_json=_component_record_json("DD", 0.65, 0.020),
        ))
        _add_fr(session, r2.id, "DD", 0.30, horizon=H, mae=-0.09, mfe=0.40, mdd=-0.11)

        # run-3: a result with ZERO forward returns -> contributes nothing (zero-N leg).
        session.add(ScannerResult(
            run_id=r3.id, ticker="FF", name="FF", sector="Technology",
            leadership_score=88.0, leadership_bucket="C",
            entry_quality_score=80.0, entry_quality_bucket="C",
            risk_score=12.0, risk_bucket="C",
            setup_status="Actionable", rank=1,
            record_json=_component_record_json("FF", 0.95, 0.008),
        ))
        session.commit()
    return engine


def _factor_observations_reference(session, factor, horizon, as_of, cfg):
    """A pre-iter-48 REFERENCE of `_factor_observations` that materializes the ScannerResult side with an
    eager `.all()` (NO `yield_per`, NO `.order_by`), mirroring the exact code the streaming fix replaced.
    The streamed builder must equal this byte-for-byte (this is the regression oracle for the refactor)."""
    from app.engine.research import _extract_factor_value, parse_factor_source
    from sqlmodel import select
    parsed = parse_factor_source(factor.source)
    batch = cfg.research.read_batch_size
    # iter-52 (J-109): the reference ALSO projects/carries the stored max_drawdown so it stays a byte-for-byte
    # oracle of the (now MDD-carrying) streamed `_factor_observations`.
    fr_stmt = select(
        ForwardReturn.run_id, ForwardReturn.symbol, ForwardReturn.realized_return, ForwardReturn.max_drawdown
    ).where(ForwardReturn.horizon == horizon)
    if as_of is not None:
        fr_stmt = fr_stmt.join(ScannerRun, ScannerRun.id == ForwardReturn.run_id).where(
            ScannerRun.asof_date <= as_of
        )
    ret_by_run_symbol = {}
    runs_with_fr_set = set()
    for run_id, symbol, realized_return, max_drawdown in session.exec(fr_stmt).yield_per(batch):
        ret_by_run_symbol[(run_id, symbol)] = (realized_return, max_drawdown)
        runs_with_fr_set.add(run_id)
    runs_with_fr = sorted(runs_with_fr_set)
    run_rows = (
        session.exec(select(ScannerRun).where(ScannerRun.id.in_(runs_with_fr))).all()
        if runs_with_fr else []
    )
    regime_by_run = {run.id: run.regime_label for run in run_rows}
    # the EXACT pre-fix read: eager `.all()`, no explicit order_by.
    results = (
        session.exec(select(ScannerResult).where(ScannerResult.run_id.in_(runs_with_fr))).all()
        if runs_with_fr else []
    )
    observations = []
    for res in results:
        fr = ret_by_run_symbol.get((res.run_id, res.ticker))
        if fr is None:
            continue
        realized, max_drawdown = fr
        value = _extract_factor_value(res, parsed)
        if value is None:
            continue
        observations.append({
            "run_id": res.run_id, "ticker": res.ticker, "factor": float(value), "return": realized,
            "max_drawdown": max_drawdown,
            "regime": regime_by_run.get(res.run_id),
        })
    return observations


@pytest.mark.parametrize("factor_key", ["leadership_score", "rs_spy_3m"])  # column AND component
@pytest.mark.parametrize("as_of", [None, date(2025, 1, 31)])
def test_factor_observations_streamed_equals_eager_all_reference(component_engine, factor_key, as_of):
    """The `yield_per`-streamed `_factor_observations` (full ORM row + `.order_by(id)`) is byte-identical
    to the pre-iter-48 eager `.all()` reference — for a COLUMN factor (`leadership_score`) AND a COMPONENT
    factor (`rs_spy_3m`, read from `record_json`) — proving the stream keeps `record_json` available and
    reproduces the prior row order, across as-of / all-history."""
    cfg = load_config()
    factor = next(f for f in cfg.research.factor_lab.factors if f.key == factor_key)
    with Session(component_engine) as session:
        streamed = _factor_observations(session, factor, H, as_of, cfg=_cfg_batch(1))
        streamed_big = _factor_observations(session, factor, H, as_of, cfg=_cfg_batch(1_000_000))
        reference = _factor_observations_reference(session, factor, H, as_of, cfg)
        assert _eq(streamed, reference), f"streamed != eager .all() reference ({factor_key}, {as_of})"
        assert _eq(streamed, streamed_big), f"batch size changed values ({factor_key}, {as_of})"
        # the component factor MUST actually read non-null values from record_json (not a degenerate
        # all-None / zero-N pool that would make the byte-identity vacuous).
        if factor_key == "rs_spy_3m" and as_of is None:
            assert streamed, "component-factor pool empty — record_json was not read"
            assert all(o["factor"] is not None for o in streamed)


@pytest.mark.parametrize("factor_key", ["leadership_score", "rs_spy_3m"])  # column AND component
@pytest.mark.parametrize("as_of", [None, date(2025, 1, 31)])
def test_compute_factor_lab_chunk_independent_component(component_engine, factor_key, as_of):
    """The full `compute_factor_lab` payload (deciles, rank_ic, by_regime, n_total) is byte-identical under
    batch=1 vs huge — for a COLUMN and a COMPONENT factor — on the component-bearing fixture."""
    with Session(component_engine) as session:
        small = compute_factor_lab(session, factor_key, H, _cfg_batch(1), as_of=as_of)
        big = compute_factor_lab(session, factor_key, H, _cfg_batch(1_000_000), as_of=as_of)
        assert _eq(small, big), f"factor-lab payload differs by batch ({factor_key}, as_of={as_of})"


def test_factor_lab_zero_n_cohort_is_honest_not_crash(component_engine):
    """A factor-lab over an as_of BEFORE any snapshot yields an honest empty/NA payload (n_total 0, every
    decile mean None) — never a crash, never a fabricated row — under the streamed ScannerResult read."""
    with Session(component_engine) as session:
        payload = compute_factor_lab(session, "rs_spy_3m", H, _cfg_batch(1), as_of=date(2024, 1, 1))
        assert payload["n_total"] == 0
        for row in payload["deciles"]:
            assert row["n"] == 0
            assert row["mean_return"] is None  # honest NA, never a fabricated 0
        assert payload["rank_ic"]["value"] is None


@pytest.mark.parametrize("as_of", [None, date(2025, 1, 31)])
def test_combination_observations_streamed_chunk_independent_component(component_engine, as_of):
    """The streamed `_combination_observations` (full ORM row + `.order_by(id)`) is batch-independent on a
    multi-factor set that mixes a COLUMN factor and a COMPONENT (`record_json`) factor — proving the
    factor-combination cold-miss path keeps `record_json` and the prior row order."""
    cfg = load_config()
    # a column factor + a component factor (read from record_json) -> exercises both extract paths.
    factors = [f for f in cfg.research.factor_lab.factors if f.key in ("leadership_score", "rs_spy_3m")]
    with Session(component_engine) as session:
        small = _combination_observations(session, factors, H, as_of, cfg=_cfg_batch(1))
        big = _combination_observations(session, factors, H, as_of, cfg=_cfg_batch(1_000_000))
        assert _eq(small, big), f"_combination_observations differs by batch (as_of={as_of})"
        if as_of is None:
            assert small, "combination pool empty — record_json was not read"
            assert all("rs_spy_3m" in o["values"] for o in small)


@pytest.mark.parametrize("as_of", [None, date(2025, 1, 31)])
def test_compute_factor_combination_chunk_independent_component(component_engine, as_of):
    """The full `compute_factor_combination` payload (composite + strict_overlap + baseline + singles) is
    byte-identical under batch=1 vs huge on the component-bearing fixture (the default config conditions
    reference `rs_spy_3m` + `atr_pct`, both component factors read from `record_json`)."""
    cfg = load_config()
    conditions = [
        {"factor": c.factor, "side": c.side, "quantile": c.quantile}
        for c in cfg.research.factor_lab.combination.default_conditions
    ]
    with Session(component_engine) as session:
        small = compute_factor_combination(session, conditions, H, _cfg_batch(1), as_of=as_of)
        big = compute_factor_combination(session, conditions, H, _cfg_batch(1_000_000), as_of=as_of)
        assert _eq(small, big), f"factor-combination payload differs by batch (as_of={as_of})"


# ==================================================================================================
# iter-52 (J-109): the all-factors ALL-HORIZONS shared pool builder is the OOM-sensitive UNCACHED-cold
# factor-lab read site. It reads `realized_return` AND `max_drawdown` for EVERY horizon in ONE streamed,
# column-projected sweep (NO unbounded `.all()` over `ForwardReturn` / `ScannerResult`). These proofs pin:
#   1. Per-horizon BYTE-IDENTITY: a factor's non-null subset of `pools[h]` (preserving order) EQUALS the
#      streamed `_factor_observations(factor, h)` row-for-row — the property compute_factor_lab_all relies on
#      so each (factor, horizon, decile) figure is byte-identical to the single-horizon view.
#   2. Chunk-independence: the one-sweep all-horizons read is identical under batch=1 vs huge (cold probe).
# ==================================================================================================
@pytest.mark.parametrize("as_of", [None, date(2025, 1, 31)])
def test_all_factor_observations_by_horizon_matches_per_factor_per_horizon(prune_engine, as_of):
    """For EVERY catalog factor and EVERY config horizon, the all-horizons shared pool's non-null subset at
    horizon h (with `max_drawdown` dropped — it rides additively) equals `_factor_observations(factor, h)`
    row-for-row on the discriminating reorder fixture (multi-horizon FRs, a non-subject symbol with FRs, a
    factor-NULL column). Proves the one-sweep all-horizons read is byte-identical per (factor, horizon)."""
    cfg = load_config()
    factors = list(cfg.research.factor_lab.factors)
    horizons = list(cfg.walk_forward.horizons)
    with Session(prune_engine) as session:
        pools = _all_factor_observations_by_horizon(session, factors, horizons, as_of, cfg=cfg)
        for factor in factors:
            for h in horizons:
                subset = [
                    {"run_id": o["run_id"], "ticker": o["ticker"],
                     "factor": float(o["values"][factor.key]), "return": o["return"],
                     "max_drawdown": o["max_drawdown"], "regime": None}
                    for o in pools[h]
                    if o["values"][factor.key] is not None
                ]
                per = _factor_observations(session, factor, h, as_of, cfg=cfg)
                # compare on the shared keys (the all-horizons pool carries no per-obs regime label, which
                # compute_factor_lab_all does not use); assert the factor/return/max_drawdown identity.
                got = [
                    {"run_id": o["run_id"], "ticker": o["ticker"], "factor": o["factor"],
                     "return": o["return"], "max_drawdown": o["max_drawdown"]}
                    for o in subset
                ]
                want = [
                    {"run_id": o["run_id"], "ticker": o["ticker"], "factor": o["factor"],
                     "return": o["return"], "max_drawdown": o["max_drawdown"]}
                    for o in per
                ]
                assert _eq(got, want), f"all-horizons subset != _factor_observations ({factor.key}@{h})"


@pytest.mark.parametrize("as_of", [None, date(2025, 1, 31)])
def test_all_factor_observations_by_horizon_chunk_independent(prune_engine, as_of):
    """The all-horizons shared pool read is byte-identical under read_batch_size=1 vs a huge batch — the
    bounded/streamed cold probe (the batch changes only peak memory, never a value/order)."""
    cfg = load_config()
    factors = list(cfg.research.factor_lab.factors)
    horizons = list(cfg.walk_forward.horizons)
    with Session(prune_engine) as session:
        small = _all_factor_observations_by_horizon(session, factors, horizons, as_of, cfg=_cfg_batch(1))
        big = _all_factor_observations_by_horizon(
            session, factors, horizons, as_of, cfg=_cfg_batch(1_000_000)
        )
        assert _eq(small, big), f"all-horizons pool differs by batch (as_of={as_of})"


@pytest.mark.parametrize("as_of", [None, date(2025, 1, 31)])
def test_compute_factor_lab_all_chunk_independent_component(component_engine, as_of):
    """The full all-factors, all-horizons payload (every factor × every horizon decile table, paired MDD) is
    byte-identical under batch=1 vs huge on the component-bearing fixture — proving the cold uncached
    factor-lab-all read keeps `record_json` (component factors) and the prior order across the stream."""
    with Session(component_engine) as session:
        small = compute_factor_lab_all(session, _cfg_batch(1), as_of=as_of)
        big = compute_factor_lab_all(session, _cfg_batch(1_000_000), as_of=as_of)
        assert _eq(small, big), f"factor-lab-all payload differs by batch (as_of={as_of})"
