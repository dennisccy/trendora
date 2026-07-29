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
from datetime import date, datetime, timedelta, timezone

import pytest
from sqlmodel import Session, select

import app.engine.research as research_module
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


def _cfg_batch(batch: int, run_chunk: int | None = None):
    """The real config with `research.read_batch_size` overridden to `batch` (chunk-size probe), and
    `research.factor_join_run_chunk` (the iter-29-audit RUN-COUNT accumulator width — a DIFFERENT unit)
    overridden to `run_chunk`, defaulting to the same value so every existing probe keeps varying BOTH the
    `yield_per` row batch and the join-accumulator chunking exactly as it did before the two knobs split."""
    cfg = load_config()
    return cfg.model_copy(update={"research": cfg.research.model_copy(update={
        "read_batch_size": batch,
        "factor_join_run_chunk": batch if run_chunk is None else run_chunk,
    })})


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


# ==================================================================================================
# ops-hardening iter-29 (AG-8): `_factor_observations`'s join accumulator (`ret_by_run_symbol`) used to
# hold ONE entry per distinct (run_id, symbol) pair across the FULL horizon's `forward_returns` history for
# as_of=None (803,042 pairs / 3,964,725 rows measured live at iter-28) even though the SOURCE query was
# already `yield_per`-streamed — an unbounded whole-history materialization in substance (AG-8). The fix
# chunks `runs_with_fr` (the sorted distinct run-id list, now discovered via a lightweight DISTINCT query
# instead of as a side effect of building the full accumulator) into bounded slices, rebuilding the
# accumulator ONE slice at a time via the new `_fr_slice_map` helper — so its LIVE size is bounded by
# (chunk width x symbols-per-run), never by the full history's distinct-pair count. These proofs pin:
#   1. TC-1: the live accumulator (`_fr_slice_map`'s return value) never holds more than one chunk's worth
#      of entries at any point during a call, on a fixture whose rows span more than one chunk across >=2
#      distinct run ids.
#   2. TC-2: the chunked rewrite is byte-identical to a pinned copy of the PRE-FIX (single-accumulator)
#      implementation, for both as_of=None and a historical as_of=D.
#   3. TC-3: the as_of=D call returns zero observations from a run dated after D (no-lookahead preserved).
# ==================================================================================================
@pytest.fixture()
def chunked_accumulator_engine(tmp_path):
    """5 distinct ScannerRuns (one per month, Jan-May 2025), each with 3 tickers carrying a forward return
    at horizon H — 15 total distinct (run_id, symbol) pairs, spanning 5 distinct run ids. Dedicated (not
    reused from `prune_engine`/`component_engine`) so the chunk-boundary proof (TC-1) and the as_of cutoff
    proof (TC-3) have a fixture shaped exactly for them: enough runs to force multiple chunks at a small
    `read_batch_size`, and dates that cleanly split into an early/late group around a chosen as_of."""
    engine = make_engine(f"sqlite:///{tmp_path / 'chunked.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        runs = [
            _add_run(session, date(2025, m, 10), regime_label="Risk-on" if m % 2 else "Risk-off")
            for m in range(1, 6)  # r0=Jan .. r4=May 2025
        ]
        session.flush()
        for i, run in enumerate(runs):
            for j, base in enumerate(("AA", "BB", "CC")):
                ticker = f"{base}{i}"  # distinct symbol per run -> 15 genuinely distinct (run_id, symbol) pairs
                _add_result(session, run.id, ticker, j + 1, setup="Actionable", sector="Technology",
                            lead=50.0 + i + j)
                _add_fr(session, run.id, ticker, 0.01 * (i + 1) + 0.001 * j, horizon=H,
                        mae=-0.02, mfe=0.05, mdd=-0.03 - 0.001 * j)
        session.commit()
    return engine


def _factor_observations_reference_unchunked(session, factor, horizon, as_of, cfg):
    """A pinned copy of iter-29's PRE-FIX `_factor_observations` body: ONE unbounded `ret_by_run_symbol`
    accumulator built from a SINGLE un-sliced `fr_stmt` covering the FULL `runs_with_fr` set at once (no
    `_fr_slice_map`, no chunk loop) — the regression oracle for the iter-29 chunked rewrite's byte-identity
    proof (TC-2). Calls the SAME unchanged helpers (`parse_factor_source`, `_extract_factor_value`) the real,
    rewritten function still uses, so any divergence can only come from the chunking itself."""
    from app.engine.research import _extract_factor_value, parse_factor_source
    parsed = parse_factor_source(factor.source)
    batch = cfg.research.read_batch_size
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
    res_stmt = (
        select(ScannerResult)
        .where(ScannerResult.run_id.in_(runs_with_fr))
        .order_by(ScannerResult.run_id, ScannerResult.id)
    )
    results = session.exec(res_stmt).yield_per(batch) if runs_with_fr else []
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


def test_factor_observations_accumulator_is_chunk_bounded(chunked_accumulator_engine, monkeypatch):
    """TC-1: `_factor_observations`'s join accumulator (`_fr_slice_map`'s return value, wrapped/observed via
    monkeypatch) never holds more entries than ONE bounded chunk at any point during the call — never one
    entry per distinct (run_id, symbol) pair in the whole fixture (15 pairs across 5 run ids)."""
    factor = next(f for f in load_config().research.factor_lab.factors if f.key == "leadership_score")
    observed_sizes: list[int] = []
    real_fr_slice_map = research_module._fr_slice_map

    def _wrapped(session, horizon, slice_run_ids, batch):
        result = real_fr_slice_map(session, horizon, slice_run_ids, batch)
        observed_sizes.append(len(result))
        return result

    monkeypatch.setattr(research_module, "_fr_slice_map", _wrapped)
    with Session(chunked_accumulator_engine) as session:
        # chunk width = 2 run ids/slice over 5 distinct run ids -> 3 slices (2, 2, 1 run ids each)
        observations = research_module._factor_observations(session, factor, H, None, cfg=_cfg_batch(2))

    total_pairs = 15  # 5 runs x 3 tickers, by fixture construction
    assert len(observations) == total_pairs, "sanity: every fixture pair must surface as an observation"
    assert len(observed_sizes) == 3, f"expected 3 chunks (5 run ids at width 2), got {len(observed_sizes)}"
    assert max(observed_sizes) <= 6, (
        f"a single slice must never exceed 2 run ids x 3 tickers = 6 entries, got {max(observed_sizes)}"
    )
    assert max(observed_sizes) < total_pairs, (
        "the live accumulator must never hold the WHOLE fixture's pairs at once"
    )


@pytest.mark.parametrize("as_of", [None, date(2025, 3, 15)])
def test_factor_observations_chunked_equals_unchunked_reference(chunked_accumulator_engine, as_of):
    """TC-2: the iter-29 chunked `_factor_observations` is byte-identical to the pinned pre-fix
    (single-accumulator) reference — for as_of=None (all-history) AND a historical as_of=D (2025-03-15) that
    splits the 5-run fixture into an early (Jan-Mar) / late (Apr-May) group."""
    cfg = _cfg_batch(2)
    factor = next(f for f in cfg.research.factor_lab.factors if f.key == "leadership_score")
    with Session(chunked_accumulator_engine) as session:
        chunked = _factor_observations(session, factor, H, as_of, cfg=cfg)
        reference = _factor_observations_reference_unchunked(session, factor, H, as_of, cfg)
    assert _eq(chunked, reference), f"chunked output != pinned pre-fix reference (as_of={as_of})"


def test_factor_observations_chunked_as_of_excludes_runs_after_cutoff(chunked_accumulator_engine):
    """TC-3: for the as_of=D-scoped chunked call, zero returned observations reference a run dated after D
    (no-lookahead preserved through the chunk rewrite)."""
    d = date(2025, 3, 15)  # between run r2 (Mar 10) and run r3 (Apr 10)
    factor = next(f for f in load_config().research.factor_lab.factors if f.key == "leadership_score")
    with Session(chunked_accumulator_engine) as session:
        observations = _factor_observations(session, factor, H, d, cfg=_cfg_batch(2))
        run_dates = {run.id: run.asof_date for run in session.exec(select(ScannerRun)).all()}
    assert observations, "sanity: the early-group runs (Jan-Mar) must still contribute observations"
    for obs in observations:
        assert run_dates[obs["run_id"]] <= d, f"observation from run {obs['run_id']} dated after {d}"


# ==================================================================================================
# iter-29 AUDIT (AG-8): the two proofs above pin the chunking MECHANISM, but both drive it through an
# artificially small `_cfg_batch(2)` override — so they pass no matter what the SHIPPED config does. As
# first shipped, iter-29's loop reused `research.read_batch_size` (2000, a ROW count) as its RUN-COUNT
# chunk width; the live basis carries only 1,812-1,871 distinct runs per horizon, so the loop produced
# exactly ONE chunk and the accumulator still held every pair at once (792,507 measured at h=20 via
# `SELECT ... WHERE horizon=20 AND run_id IN (<first 2000 sorted run ids>)` — 0% below the pre-fix peak,
# i.e. a bound that bound nothing). The two tests below pin the property at the REAL configuration, which
# is what AG-8 is actually about.
# ==================================================================================================

# The live basis measured during the iter-29 audit: 1,812-1,871 distinct scanner runs per horizon, ~429
# symbols per run. A run-chunk width at/above the run count degenerates to a single chunk, so the shipped
# width must stay well below it with room for years of further daily-cadence growth; 500 is the loosest
# ceiling that still forces real chunking on today's basis (>=4 chunks) and would have caught the shipped
# 2000. Peak accumulator = width x symbols-per-run, so the shipped 100 holds ~43-55K pairs, not ~800K.
_MAX_MEANINGFUL_RUN_CHUNK = 500


def test_shipped_factor_join_run_chunk_actually_binds_on_the_live_basis():
    """The SHIPPED `research.factor_join_run_chunk` must be small enough to produce real chunking against
    a multi-year daily-cadence basis. This is the regression guard for the iter-29 audit finding: a width
    of 2000 runs (the row knob, reused) against 1,812-1,871 live runs per horizon meant one chunk and zero
    peak reduction, while every unit proof still passed because it overrode the knob to 2."""
    research_cfg = load_config().research
    width = research_cfg.factor_join_run_chunk
    assert 1 <= width <= _MAX_MEANINGFUL_RUN_CHUNK, (
        f"research.factor_join_run_chunk={width} cannot bound the join accumulator on the live basis "
        f"(1,812-1,871 distinct runs/horizon): it must be <= {_MAX_MEANINGFUL_RUN_CHUNK}"
    )


def test_factor_observations_chunks_at_the_shipped_config(tmp_path, monkeypatch):
    """The accumulator is chunk-bounded under the SHIPPED config — no `_cfg_batch` override. Builds a
    fixture with (shipped width + 3) runs so real chunking is REQUIRED, then asserts `_factor_observations`
    made >= 2 slice reads and that no single slice ever held the whole fixture's (run_id, symbol) pairs."""
    cfg = load_config()  # the REAL config.yaml — deliberately NOT overridden
    width = cfg.research.factor_join_run_chunk
    n_runs, tickers = width + 3, ("AA", "BB")
    engine = make_engine(f"sqlite:///{tmp_path / 'shipped_chunk.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        for i in range(n_runs):
            run = _add_run(session, date(2025, 1, 1) + timedelta(days=i), regime_label="Risk-on")
            session.flush()
            for j, base in enumerate(tickers):
                ticker = f"{base}{i}"
                _add_result(session, run.id, ticker, j + 1, setup="Actionable", sector="Technology",
                            lead=50.0 + (i % 7) + j)
                _add_fr(session, run.id, ticker, 0.01 * (i + 1) + 0.001 * j, horizon=H,
                        mae=-0.02, mfe=0.05, mdd=-0.03)
        session.commit()

    factor = next(f for f in cfg.research.factor_lab.factors if f.key == "leadership_score")
    observed_sizes: list[int] = []
    real_fr_slice_map = research_module._fr_slice_map

    def _wrapped(session, horizon, slice_run_ids, batch):
        result = real_fr_slice_map(session, horizon, slice_run_ids, batch)
        observed_sizes.append(len(result))
        return result

    monkeypatch.setattr(research_module, "_fr_slice_map", _wrapped)
    with Session(engine) as session:
        observations = research_module._factor_observations(session, factor, H, None, cfg=cfg)

    total_pairs = n_runs * len(tickers)
    assert len(observations) == total_pairs, "sanity: every fixture pair must surface as an observation"
    assert len(observed_sizes) >= 2, (
        f"the SHIPPED config produced {len(observed_sizes)} chunk(s) over {n_runs} runs — the accumulator "
        f"bound is inert at the real configuration (width={width})"
    )
    assert max(observed_sizes) <= width * len(tickers), "a slice exceeded its configured run-chunk width"
    assert max(observed_sizes) < total_pairs, (
        "the live accumulator must never hold the WHOLE fixture's pairs at once under the shipped config"
    )
