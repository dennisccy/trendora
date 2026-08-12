"""Daily preflight-verdict composer tests (goal-mcp-loop iter-33, J-20 / backlog B-301).

`app.engine.readiness.compute_preflight` is a PURE composer over three inputs that exist now:

  - **servability** — reuses `compute_readiness`'s own liveness check verbatim (no re-derivation).
  - **freshness** — the latest bar's trading-day age vs a deterministic, seed-resolved reference
    (never `date.today()`), breached past `config.readiness.freshness_max_age_days`.
  - **DB/ledger integrity** — DB reachable AND the canonical/staging/registry JSONL files exist+parse.

These tests pin: the exact verdict per component-combination (the B-301 correctness bar — a fixture
matrix, not a smoke check); severity/threshold config wiring (the verdict moves with config, never a
code literal); that `compute_readiness`'s own `state`/`warmup` shape is untouched (J-40 not regressed);
that servability is REUSED rather than re-derived; honest degradation on every error case (DB
unreachable / missing / unparseable ledger / stale freshness) — never a raise, never a fabricated GO;
and that `record_verdict_transition` appends ONLY on a verdict change (bounded growth).
"""
from __future__ import annotations

import threading
import time
from datetime import date, datetime, timedelta

import pytest
from sqlalchemy import event
from sqlmodel import Session

from app.config import load_config
from app.db import create_db_and_tables, make_engine
from app.engine import readiness
from app.engine.ledger import read_entries
from app.engine.readiness import (
    DEGRADED,
    GO,
    NO_GO,
    compute_preflight,
    compute_readiness,
    record_verdict_transition,
    resolve_verdict_history_path,
)
from app.models import DailyPrice, ScannerRun


def _readiness_cfg(cfg, **overrides):
    """A `cfg` copy with `readiness.<field>` overridden — keeps each test's intent to one line."""
    updated = cfg.readiness.model_copy(update=overrides)
    return cfg.model_copy(update={"readiness": updated})


def _point_ledgers_at(monkeypatch, tmp_dir, *, ok: bool) -> None:
    """Point all three ledger/registry resolvers at `tmp_dir`: valid-but-empty files when `ok`, else
    paths that are never created (the honest "missing" integrity failure). Also points the iter-35
    drift-report resolver at a guaranteed-ABSENT path under `tmp_dir` (never created here), so the new
    `drift` preflight component is deterministically `ok` (no fetch has run yet) regardless of the real
    repo's filesystem state — the drift-specific fixture tests below point it elsewhere explicitly."""
    for filename, env_var in (
        ("certified-claims.jsonl", "TRENDORA_LEDGER_PATH"),
        ("staging-ledger.jsonl", "STAGING_LEDGER_PATH"),
        ("pre-registrations.jsonl", "TRENDORA_REGISTRY_PATH"),
    ):
        target = tmp_dir / filename
        if ok:
            target.write_text("")
        monkeypatch.setenv(env_var, str(target))
    monkeypatch.setenv("TRENDORA_DRIFT_REPORT_PATH", str(tmp_dir / "drift-report.json"))


# ==================================================================================================
# Fixture engines for the servability axis (independent of the shared warmed `loaded_engine`)
# ==================================================================================================
@pytest.fixture(scope="module")
def empty_engine(tmp_path_factory):
    """No price data at all: servability AND freshness are both honestly un-derivable (coupled)."""
    db_path = tmp_path_factory.mktemp("preflight_empty_db") / "empty.db"
    engine = make_engine(f"sqlite:///{db_path}")
    create_db_and_tables(engine)
    return engine


@pytest.fixture(scope="module")
def unscanned_engine(tmp_path_factory):
    """Price data present (so freshness resolves OK) but NO persisted `ScannerRun` for it: servability
    BREACH with freshness OK — the one combination the fully-warmed and the fully-empty DB cannot
    independently produce."""
    db_path = tmp_path_factory.mktemp("preflight_unscanned_db") / "unscanned.db"
    engine = make_engine(f"sqlite:///{db_path}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        session.add(
            DailyPrice(symbol="ZZZ", date=date(2026, 7, 8), open=1, high=1, low=1, close=1, volume=1)
        )
        session.commit()
    return engine


# ==================================================================================================
# B-301 correctness bar: exact verdict per {servability, freshness, integrity} combination
# ==================================================================================================
def test_preflight_fixture_matrix(loaded_engine, empty_engine, unscanned_engine, tmp_path_factory, monkeypatch):
    cfg = load_config()
    # Reused config identities (not a fresh model_copy per row) so `compute_readiness`'s cadence-date
    # memo hits on the second use against the same (expensive) fully-warmed engine — a perf courtesy,
    # not a correctness requirement.
    cfg_relaxed = _readiness_cfg(cfg, freshness_max_age_days=100)  # 0-day age never breaches this
    cfg_strict = _readiness_cfg(cfg, freshness_max_age_days=-1)  # 0-day age always breaches this

    cases = [
        # (label, engine, config, integrity_ok, expected_verdict, expected_component_oks)
        ("all ok", loaded_engine, cfg_relaxed, True, GO, {"servability": True, "freshness": True, "integrity": True}),
        ("servability breach only", unscanned_engine, cfg_relaxed, True, NO_GO,
         {"servability": False, "freshness": True, "integrity": True}),
        ("freshness breach only", loaded_engine, cfg_strict, True, DEGRADED,
         {"servability": True, "freshness": False, "integrity": True}),
        ("integrity breach only", loaded_engine, cfg_relaxed, False, NO_GO,
         {"servability": True, "freshness": True, "integrity": False}),
        ("servability + freshness breach", empty_engine, cfg_relaxed, True, NO_GO,
         {"servability": False, "freshness": False, "integrity": True}),
        ("servability + integrity breach", unscanned_engine, cfg_relaxed, False, NO_GO,
         {"servability": False, "freshness": True, "integrity": False}),
        ("freshness + integrity breach", loaded_engine, cfg_strict, False, NO_GO,
         {"servability": True, "freshness": False, "integrity": False}),
        ("all breach", empty_engine, cfg_relaxed, False, NO_GO,
         {"servability": False, "freshness": False, "integrity": False}),
    ]

    for label, engine, test_cfg, integrity_ok, expected_verdict, expected_oks in cases:
        tmp_dir = tmp_path_factory.mktemp("ledgers_" + label.replace(" ", "_").replace("+", "and"))
        _point_ledgers_at(monkeypatch, tmp_dir, ok=integrity_ok)
        with Session(engine) as session:
            result = compute_preflight(session, config=test_cfg)
        assert result["verdict"] == expected_verdict, f"{label}: got {result}"
        assert set(result) == {"verdict", "reasons", "components", "as_of", "reference"}
        assert result["as_of"] == result["reference"]  # same value under both spec-named keys
        # iter-35 (J-21/B-304) added the 4th `drift` component; `_point_ledgers_at` points it at an
        # absent path for every row above, so it is always `ok` here (no fetch has run in this matrix) —
        # the drift-specific behavior (breach on a written "drift"/unreadable artifact) is covered by its
        # own dedicated tests below, not re-derived per row of this pre-existing 3-axis matrix.
        assert set(result["components"]) == {"servability", "freshness", "integrity", "drift"}
        assert result["components"]["drift"]["ok"] is True, f"{label}: {result['components']['drift']}"
        for component, expected_ok in expected_oks.items():
            assert result["components"][component]["ok"] is expected_ok, f"{label}/{component}: {result}"
        if expected_verdict == GO:
            assert result["reasons"] == [], f"{label}: {result['reasons']}"
        else:
            assert result["reasons"], f"{label}: expected non-empty reasons"
            # every breached component's detail is present verbatim in the top-level reasons list
            for component, expected_ok in expected_oks.items():
                if not expected_ok:
                    assert result["components"][component]["detail"] in result["reasons"]


def test_preflight_components_always_carry_configured_severity(loaded_engine, tmp_path_factory, monkeypatch):
    """Every component's `severity` is the CONFIGURED value regardless of its `ok` state (informational,
    self-documenting payload) — proving `severity` is read from config, never inferred from outcome."""
    cfg = load_config()
    _point_ledgers_at(monkeypatch, tmp_path_factory.mktemp("severity_labels"), ok=True)
    with Session(loaded_engine) as session:
        result = compute_preflight(session, config=cfg)
    assert result["components"]["servability"]["severity"] == cfg.readiness.severity["servability"]
    assert result["components"]["freshness"]["severity"] == cfg.readiness.severity["freshness"]
    assert result["components"]["integrity"]["severity"] == cfg.readiness.severity["integrity"]
    assert result["components"]["drift"]["severity"] == cfg.readiness.severity["drift"]


# ==================================================================================================
# Config wiring: the verdict moves with config, never a code literal
# ==================================================================================================
def test_freshness_threshold_is_config_driven_not_a_literal(loaded_engine, tmp_path_factory, monkeypatch):
    cfg = load_config()
    _point_ledgers_at(monkeypatch, tmp_path_factory.mktemp("threshold_wiring"), ok=True)
    with Session(loaded_engine) as session:
        relaxed = compute_preflight(session, config=_readiness_cfg(cfg, freshness_max_age_days=100))
        strict = compute_preflight(session, config=_readiness_cfg(cfg, freshness_max_age_days=-1))
    assert relaxed["verdict"] == GO
    assert strict["verdict"] == DEGRADED


def test_severity_mapping_is_config_driven_not_a_literal(loaded_engine, tmp_path_factory, monkeypatch):
    """The SAME breach (freshness) maps to a DIFFERENT overall verdict purely by re-pointing
    `readiness.severity.freshness` — proving the severity map, not just the threshold, is config-read."""
    cfg = load_config()
    _point_ledgers_at(monkeypatch, tmp_path_factory.mktemp("severity_wiring"), ok=True)
    degraded_cfg = _readiness_cfg(cfg, freshness_max_age_days=-1)
    no_go_severity = dict(degraded_cfg.readiness.severity, freshness="no-go")
    no_go_cfg = _readiness_cfg(degraded_cfg, severity=no_go_severity)
    with Session(loaded_engine) as session:
        as_degraded = compute_preflight(session, config=degraded_cfg)
        as_no_go = compute_preflight(session, config=no_go_cfg)
    assert as_degraded["verdict"] == DEGRADED
    assert as_no_go["verdict"] == NO_GO


def test_readiness_cfg_rejects_severity_missing_a_component():
    from app.config import ReadinessCfg

    with pytest.raises(ValueError, match="missing components"):
        ReadinessCfg(
            freshness_max_age_days=5,
            severity={"servability": "no-go", "freshness": "degraded"},  # integrity missing
            verdict_history_path="x.jsonl",
        )


def test_readiness_cfg_rejects_severity_missing_both_states():
    from app.config import ReadinessCfg

    with pytest.raises(ValueError, match="degraded.*no-go|no-go.*degraded"):
        ReadinessCfg(
            freshness_max_age_days=5,
            severity={"servability": "no-go", "freshness": "no-go", "integrity": "no-go", "drift": "no-go"},
            verdict_history_path="x.jsonl",
        )


def test_readiness_cfg_rejects_unknown_severity_value():
    from app.config import ReadinessCfg

    with pytest.raises(ValueError, match="must be one of"):
        ReadinessCfg(
            freshness_max_age_days=5,
            severity={"servability": "critical", "freshness": "degraded", "integrity": "no-go", "drift": "degraded"},
            verdict_history_path="x.jsonl",
        )


def test_readiness_cfg_rejects_severity_missing_drift_component():
    """iter-35 (J-21/B-304): `drift` joins the required component set — a severity map covering the
    original three but omitting `drift` alone is rejected, exactly like an original omission."""
    from app.config import ReadinessCfg

    with pytest.raises(ValueError, match="missing components"):
        ReadinessCfg(
            freshness_max_age_days=5,
            severity={"servability": "no-go", "freshness": "degraded", "integrity": "no-go"},  # drift missing
            verdict_history_path="x.jsonl",
        )


def test_readiness_cfg_accepts_severity_with_all_four_components():
    from app.config import ReadinessCfg

    cfg = ReadinessCfg(
        freshness_max_age_days=5,
        severity={"servability": "no-go", "freshness": "degraded", "integrity": "no-go", "drift": "degraded"},
        verdict_history_path="x.jsonl",
    )
    assert cfg.severity["drift"] == "degraded"


# ==================================================================================================
# Single source: servability is REUSED from compute_readiness, never re-derived
# ==================================================================================================
def test_preflight_servability_reuses_compute_readiness_verbatim(loaded_engine, tmp_path_factory, monkeypatch):
    """Monkeypatching `compute_readiness` to return a crafted state proves `compute_preflight` READS it
    rather than re-deriving liveness independently (no second computation)."""
    cfg = load_config()
    _point_ledgers_at(monkeypatch, tmp_path_factory.mktemp("single_source"), ok=True)
    monkeypatch.setattr(
        readiness,
        "compute_readiness",
        lambda session, config=None: {
            "state": "unavailable",
            "warmup": {"done": 0, "total": 0, "status": "pending", "message": "history 0/0"},
        },
    )
    with Session(loaded_engine) as session:
        result = compute_preflight(session, config=cfg)
    assert result["components"]["servability"]["ok"] is False


def test_compute_readiness_shape_unchanged_by_preflight_addition(loaded_engine):
    """`compute_preflight` is ADDITIVE — `compute_readiness`'s own return shape is untouched BY IT (J-40
    not regressed): exactly `{"state", "detail", "warmup", "background_compute"}` (ops-hardening iter-4's
    B3 fix added the `detail` sibling alongside `state`/`warmup`; ops-hardening iter-24, J-09, additively
    added `background_compute`), `warmup` exactly `{"done","total","status","message"}`. This warmed,
    fully-caught-up fixture never produces the new `awaiting_snapshot` state, so `detail` is null here (see
    the dedicated B3 fixture-matrix below for the non-null case)."""
    cfg = load_config()
    with Session(loaded_engine) as session:
        result = compute_readiness(session, config=cfg)
    assert set(result) == {"state", "detail", "warmup", "background_compute"}
    assert result["state"] in {"ready", "initializing", "unavailable", "awaiting_snapshot"}
    assert result["detail"] is None
    assert set(result["warmup"]) == {"done", "total", "status", "message"}
    assert set(result["background_compute"]) == {"active", "recent_outcomes"}


# ==================================================================================================
# ops-hardening iter-24 (J-09) — compute_readiness composes app.engine.forward_testing.
# get_background_compute_status()'s output into its own return dict as the new `background_compute`
# sibling key. These tests pin the composition itself (empty/active shapes, degrade-on-error); the
# registry's OWN bookkeeping (started_at/horizons_done/ring cap/failure path) is covered in
# test_forward_testing_concurrency.py, the producer module's own test file.
# ==================================================================================================
def _background_compute_identity(status: dict) -> dict:
    """Reduce a `background_compute` payload to the parts two back-to-back LIVE reads of the SAME
    process-lifetime registry can be compared on without flaking (audit T1 fix): `elapsed_ms` on each
    active entry is computed fresh at READ TIME from its own `started_at`, so it can legitimately grow
    between two reads of a genuinely in-flight window -- it is excluded here. `recent_outcomes` is
    reduced to its ordering/length (the identifying `(asof_key, dataset_version)` sequence)."""
    return {
        "active": [{k: v for k, v in entry.items() if k != "elapsed_ms"} for entry in status["active"]],
        "recent_outcomes_order": [(o["asof_key"], o["dataset_version"]) for o in status["recent_outcomes"]],
        "recent_outcomes_count": len(status["recent_outcomes"]),
    }


def test_compute_readiness_composes_background_compute_empty_shape(loaded_engine):
    """A process that has never dispatched a historical background compute reports the honest empty
    shape -- never omitted, never fabricated non-empty. Compares two back-to-back live reads of the SAME
    registry on identity/shape rather than raw equality, excluding the read-time-volatile `elapsed_ms`
    field (closes audit T1 -- a false-alarm risk on any whole-file run where a background thread left by
    an earlier test may still be in flight between the two reads below)."""
    import app.engine.forward_testing as forward_testing_module

    cfg = load_config()
    with Session(loaded_engine) as session:
        # A previous test in this same process could have left dispatch state behind (the registry is a
        # process-lifetime global, by design -- J-09 step 6). Reading the SAME accessor directly proves
        # compute_readiness composes it VERBATIM regardless of what it currently holds.
        direct = forward_testing_module.get_background_compute_status()
        result = compute_readiness(session, config=cfg)
    composed = result["background_compute"]
    assert isinstance(composed["active"], list)
    assert isinstance(composed["recent_outcomes"], list)
    assert len(composed["active"]) == len(direct["active"])
    assert _background_compute_identity(composed) == _background_compute_identity(direct)


def test_compute_readiness_composes_background_compute_active_entry(loaded_engine, monkeypatch):
    """A crafted non-empty `get_background_compute_status()` return is composed VERBATIM (read-only,
    single source -- no re-derivation) into `compute_readiness`'s own `background_compute` key."""
    import app.engine.forward_testing as forward_testing_module

    crafted = {
        "active": [{
            "asof_key": "2026-01-05", "dataset_version": "r1-f2", "started_at": "2026-01-05T00:00:00+00:00",
            "elapsed_ms": 1234, "horizons_done": 1, "horizons_total": 5,
        }],
        "recent_outcomes": [{
            "asof_key": "2026-01-04", "dataset_version": "r1-f2", "outcome": "completed",
            "started_at": "2026-01-04T00:00:00+00:00", "finished_at": "2026-01-04T00:00:05+00:00",
            "duration_ms": 5000, "reason": None,
        }],
    }
    monkeypatch.setattr(forward_testing_module, "get_background_compute_status", lambda: crafted)
    cfg = load_config()
    with Session(loaded_engine) as session:
        result = compute_readiness(session, config=cfg)
    assert result["background_compute"] == crafted


def test_compute_readiness_background_compute_degrades_honestly_on_error(loaded_engine, monkeypatch):
    """A broken registry read degrades ONLY `background_compute` to the honest empty shape -- it must
    never blank/raise the surrounding `state`/`warmup` (mirrors this module's own db_ok degrade
    convention)."""
    import app.engine.forward_testing as forward_testing_module

    def _boom():
        raise RuntimeError("simulated registry read failure")

    monkeypatch.setattr(forward_testing_module, "get_background_compute_status", _boom)
    cfg = load_config()
    with Session(loaded_engine) as session:
        result = compute_readiness(session, config=cfg)  # must not raise
    assert result["background_compute"] == {"active": [], "recent_outcomes": []}
    assert result["state"] in {"ready", "initializing", "unavailable", "awaiting_snapshot"}


# ==================================================================================================
# ops-hardening iter-4 (B3 fix): compute_readiness's servability check is benchmark-scoped, never a
# whole-table `daily_prices` scan -- an unrelated symbol's ordinary fetch must never flip the badge to
# `unavailable`; the BENCHMARK's own latest bar outrunning the last run gets its own honest new state.
# ==================================================================================================
@pytest.fixture(scope="module")
def non_benchmark_ahead_engine(tmp_path_factory, config):
    """A `ScannerRun` persisted for date D, alongside the BENCHMARK's own single bar also dated D — the
    ordinary "caught up" baseline (TC-1). Mutated in-test by landing a NON-benchmark symbol's bar at D+1
    (an ordinary fetch) to reproduce B3's exact trigger shape (TC-2): the benchmark's own latest bar stays
    put, so this must change NOTHING about `state`."""
    db_path = tmp_path_factory.mktemp("non_benchmark_ahead_db") / "non_benchmark_ahead.db"
    engine = make_engine(f"sqlite:///{db_path}")
    create_db_and_tables(engine)
    benchmark = config.etfs.index[0]
    d0 = date(2024, 3, 4)
    with Session(engine) as session:
        session.add(DailyPrice(symbol=benchmark, date=d0, open=1, high=1, low=1, close=1, volume=1))
        session.add(ScannerRun(
            asof_date=d0, created_at=datetime(2024, 3, 4), provider="seed", benchmark=benchmark,
            regime_score=50.0, regime_label="Choppy", regime_components_json="[]",
            new_high_low_json="{}", candidate_counts_json="{}",
        ))
        session.commit()
    return engine, benchmark, d0


def test_non_benchmark_symbol_fetch_never_affects_servability(non_benchmark_ahead_engine):
    """TC-1 + TC-2: the baseline "benchmark caught up" case reads ready/initializing (never unavailable,
    never awaiting_snapshot) — and landing an ORDINARY fetch for an unrelated symbol dated AFTER the last
    run (the actual B3 reproduction: an ordinary "Fetch EOD prices" job for some other ticker) changes
    `state`/`warmup` NOT AT ALL, because the new per-symbol query never reads that unrelated symbol."""
    engine, benchmark, d0 = non_benchmark_ahead_engine
    cfg = load_config()
    readiness.reset_readiness_cache()
    with Session(engine) as session:
        before = compute_readiness(session, config=cfg)
    assert before["state"] in {"ready", "initializing"}
    assert before["detail"] is None

    d1 = d0 + timedelta(days=1)
    with Session(engine) as session:
        session.add(DailyPrice(symbol="ZZZ", date=d1, open=1, high=1, low=1, close=1, volume=1))
        session.commit()
    readiness.reset_readiness_cache()  # force a fresh derive -- a stale memo hit could mask a real bug
    with Session(engine) as session:
        after = compute_readiness(session, config=cfg)

    assert after["state"] == before["state"] != "unavailable"
    assert after["detail"] is None
    assert after["warmup"] == before["warmup"]


@pytest.fixture(scope="module")
def benchmark_ahead_engine(tmp_path_factory, config):
    """A `ScannerRun` persisted for date D, then the BENCHMARK symbol's OWN latest bar advances to D+1
    with no run yet for D+1 — the exact `awaiting_snapshot` condition (TC-3, B3 fix): a servable last run
    exists, but new data has landed for the symbol that defines the trading calendar."""
    db_path = tmp_path_factory.mktemp("awaiting_snapshot_db") / "benchmark_ahead.db"
    engine = make_engine(f"sqlite:///{db_path}")
    create_db_and_tables(engine)
    benchmark = config.etfs.index[0]
    d0 = date(2024, 3, 4)
    d1 = date(2024, 3, 5)
    with Session(engine) as session:
        session.add(DailyPrice(symbol=benchmark, date=d0, open=1, high=1, low=1, close=1, volume=1))
        session.add(DailyPrice(symbol=benchmark, date=d1, open=1, high=1, low=1, close=1, volume=1))
        session.add(ScannerRun(
            asof_date=d0, created_at=datetime(2024, 3, 4), provider="seed", benchmark=benchmark,
            regime_score=50.0, regime_label="Choppy", regime_components_json="[]",
            new_high_low_json="{}", candidate_counts_json="{}",
        ))
        session.commit()
    return engine, benchmark, d0, d1


def test_awaiting_snapshot_when_benchmark_own_bar_outruns_last_run(benchmark_ahead_engine):
    """TC-3: the BENCHMARK's own latest bar advancing past the last persisted run (no run yet for that
    date) is the new honest `awaiting_snapshot` state — distinct from unavailable/ready/initializing —
    with a non-null detail naming the condition and the recovery action."""
    engine, benchmark, d0, d1 = benchmark_ahead_engine
    cfg = load_config()
    readiness.reset_readiness_cache()
    with Session(engine) as session:
        result = compute_readiness(session, config=cfg)
    assert result["state"] == "awaiting_snapshot"
    assert result["detail"] is not None
    assert benchmark in result["detail"]
    assert d1.isoformat() in result["detail"]


def test_awaiting_snapshot_never_masks_true_unavailability(unscanned_engine):
    """TC-6 regression guard: `latest_run is None` (no ScannerRun ever persisted) MUST still resolve
    unconditionally to `unavailable`, even on a DB with real price data — the one case where "nothing is
    servable" must never be softened by the new state."""
    cfg = load_config()
    readiness.reset_readiness_cache()
    with Session(unscanned_engine) as session:
        result = compute_readiness(session, config=cfg)
    assert result["state"] == "unavailable"
    assert result["detail"] is None


def test_preflight_servability_ok_for_awaiting_snapshot_state(benchmark_ahead_engine, tmp_path_factory, monkeypatch):
    """TC-5: `compute_preflight`'s servability component stays `ok` (verdict GO, not forced to
    NO-GO/DEGRADED) when readiness is `awaiting_snapshot` alone — `compute_preflight`'s existing
    `!= UNAVAILABLE` check already treats the new state as non-breaching; this pins that it stays true
    without re-deriving it."""
    engine, benchmark, d0, d1 = benchmark_ahead_engine
    cfg = load_config()
    _point_ledgers_at(monkeypatch, tmp_path_factory.mktemp("awaiting_snapshot_preflight"), ok=True)
    readiness.reset_readiness_cache()
    with Session(engine) as session:
        readiness_result = compute_readiness(session, config=cfg)
        assert readiness_result["state"] == "awaiting_snapshot"  # sanity: this IS the target condition
        preflight_result = compute_preflight(session, config=cfg)
    assert preflight_result["components"]["servability"]["ok"] is True
    assert preflight_result["verdict"] == GO


def test_latest_benchmark_bar_query_is_symbol_scoped_not_whole_table_scan(loaded_engine):
    """TC-10 (AG-8): the new benchmark-scoped latest-bar query filters to ONE symbol via a WHERE clause
    on `daily_prices.symbol` — never an unfiltered whole-table scan. Captured at the SQL-statement level
    (mirrors test_health.py's query-shape instrumentation) so this is a structural guarantee, not merely
    an accidental byte-identical result."""
    cfg = load_config()
    captured: list[str] = []

    def _capture(conn, cursor, statement, parameters, context, executemany):
        lowered = statement.lower()
        if "daily_prices" in lowered and lowered.strip().startswith("select"):
            captured.append(statement)

    event.listen(loaded_engine, "before_cursor_execute", _capture)
    try:
        with Session(loaded_engine) as session:
            readiness._latest_benchmark_bar_date(session, cfg)
    finally:
        event.remove(loaded_engine, "before_cursor_execute", _capture)

    assert len(captured) == 1, f"expected exactly one query, got: {captured}"
    statement = captured[0].lower()
    assert "where" in statement and "symbol" in statement, f"expected a symbol-filtered WHERE clause, got: {statement}"


# ==================================================================================================
# iter-35 (J-21/B-304): the `drift` component -- ok when absent/clean, breached on a written artifact,
# worst-severity composition across all FOUR components still correct
# ==================================================================================================
def test_drift_component_ok_when_artifact_absent(loaded_engine, tmp_path_factory, monkeypatch):
    """No fetch has ever run -> the drift artifact is absent -> `ok` (the J-20 non-regression
    guarantee: GO stays GO with the drift component wired in but inert)."""
    cfg = load_config()
    _point_ledgers_at(monkeypatch, tmp_path_factory.mktemp("drift_absent"), ok=True)
    with Session(loaded_engine) as session:
        result = compute_preflight(session, config=cfg)
    assert result["components"]["drift"]["ok"] is True
    assert result["verdict"] == GO


def test_drift_component_ok_when_artifact_clean(loaded_engine, tmp_path_factory, monkeypatch):
    from app.engine.drift import write_drift_report

    cfg = load_config()
    tmp_dir = tmp_path_factory.mktemp("drift_clean")
    _point_ledgers_at(monkeypatch, tmp_dir, ok=True)
    monkeypatch.setenv("TRENDORA_DRIFT_REPORT_PATH", str(tmp_dir / "written-drift-report.json"))
    write_drift_report({"status": "clean", "reference": "2024-03-01", "overlap_days": 20, "affected": []})
    with Session(loaded_engine) as session:
        result = compute_preflight(session, config=cfg)
    assert result["components"]["drift"]["ok"] is True
    assert result["verdict"] == GO


def test_drift_component_breached_on_drift_status_names_affected_symbols(loaded_engine, tmp_path_factory, monkeypatch):
    from app.engine.drift import write_drift_report

    cfg = load_config()
    tmp_dir = tmp_path_factory.mktemp("drift_breach")
    _point_ledgers_at(monkeypatch, tmp_dir, ok=True)
    monkeypatch.setenv("TRENDORA_DRIFT_REPORT_PATH", str(tmp_dir / "written-drift-report.json"))
    write_drift_report({
        "status": "drift", "reference": "2024-03-01", "overlap_days": 20,
        "affected": [{"symbol": "AAPL", "mismatching_dates": ["2024-02-28"], "classification": "adjustment_seam"}],
    })
    with Session(loaded_engine) as session:
        result = compute_preflight(session, config=cfg)
    assert result["components"]["drift"]["ok"] is False
    assert "AAPL" in result["components"]["drift"]["detail"]
    assert result["components"]["drift"]["detail"] in result["reasons"]
    assert result["verdict"] == DEGRADED  # config default: readiness.severity.drift == "degraded"


def test_drift_component_breached_on_unreadable_artifact(loaded_engine, tmp_path_factory, monkeypatch):
    cfg = load_config()
    tmp_dir = tmp_path_factory.mktemp("drift_unreadable")
    _point_ledgers_at(monkeypatch, tmp_dir, ok=True)
    drift_path = tmp_dir / "corrupt-drift-report.json"
    drift_path.write_text("{not valid json")
    monkeypatch.setenv("TRENDORA_DRIFT_REPORT_PATH", str(drift_path))
    with Session(loaded_engine) as session:
        result = compute_preflight(session, config=cfg)  # must not raise
    assert result["components"]["drift"]["ok"] is False
    assert "unreadable" in result["components"]["drift"]["detail"].lower()


def test_drift_breach_composes_with_other_breaches_worst_severity_wins(loaded_engine, tmp_path_factory, monkeypatch):
    """A drift breach (config-default `degraded`) alongside an integrity breach (config-default `no-go`)
    still yields the WORST verdict, NO-GO -- the 4th component doesn't change the existing worst-of
    composition rule."""
    from app.engine.drift import write_drift_report

    cfg = load_config()
    tmp_dir = tmp_path_factory.mktemp("drift_plus_integrity")
    _point_ledgers_at(monkeypatch, tmp_dir, ok=False)  # integrity breach (no-go)
    drift_path = tmp_dir / "written-drift-report.json"
    monkeypatch.setenv("TRENDORA_DRIFT_REPORT_PATH", str(drift_path))  # override the absent default
    write_drift_report({
        "status": "drift", "reference": "x", "overlap_days": 20,
        "affected": [{"symbol": "ZZZ", "mismatching_dates": ["2024-01-01"], "classification": "adjustment_seam"}],
    })
    with Session(loaded_engine) as session:
        result = compute_preflight(session, config=cfg)
    assert result["components"]["integrity"]["ok"] is False
    assert result["components"]["drift"]["ok"] is False
    assert result["verdict"] == NO_GO  # integrity's no-go outranks drift's degraded


# ==================================================================================================
# Error cases: honest degradation, never a raise, never a fabricated GO
# ==================================================================================================
def test_db_unreachable_degrades_honestly_never_raises(loaded_engine, tmp_path_factory, monkeypatch):
    _point_ledgers_at(monkeypatch, tmp_path_factory.mktemp("db_down"), ok=True)

    def _boom(session):
        raise RuntimeError("simulated DB failure")

    monkeypatch.setattr(readiness, "latest_data_date", _boom)
    cfg = load_config()
    with Session(loaded_engine) as session:
        result = compute_preflight(session, config=cfg)  # must not raise
    assert result["verdict"] == NO_GO
    assert result["components"]["servability"]["ok"] is False
    assert result["components"]["integrity"]["ok"] is False
    assert "database is unreachable" in result["components"]["integrity"]["detail"]
    assert result["components"]["freshness"]["ok"] is False
    assert result["as_of"] is None
    assert result["reference"] is None


def test_integrity_breach_on_missing_ledger_file(loaded_engine, tmp_path_factory, monkeypatch):
    _point_ledgers_at(monkeypatch, tmp_path_factory.mktemp("missing_ledger"), ok=False)
    cfg = load_config()
    with Session(loaded_engine) as session:
        result = compute_preflight(session, config=cfg)
    assert result["components"]["integrity"]["ok"] is False
    assert "missing" in result["components"]["integrity"]["detail"]
    assert result["verdict"] == NO_GO  # integrity is configured "no-go" by default


def test_integrity_breach_on_unparseable_ledger_line(loaded_engine, tmp_path_factory, monkeypatch):
    tmp_dir = tmp_path_factory.mktemp("bad_ledger")
    (tmp_dir / "certified-claims.jsonl").write_text("{not valid json\n")
    (tmp_dir / "staging-ledger.jsonl").write_text("")
    (tmp_dir / "pre-registrations.jsonl").write_text("")
    monkeypatch.setenv("TRENDORA_LEDGER_PATH", str(tmp_dir / "certified-claims.jsonl"))
    monkeypatch.setenv("STAGING_LEDGER_PATH", str(tmp_dir / "staging-ledger.jsonl"))
    monkeypatch.setenv("TRENDORA_REGISTRY_PATH", str(tmp_dir / "pre-registrations.jsonl"))
    cfg = load_config()
    with Session(loaded_engine) as session:
        result = compute_preflight(session, config=cfg)
    assert result["components"]["integrity"]["ok"] is False
    assert "unparseable" in result["components"]["integrity"]["detail"]
    assert result["verdict"] == NO_GO


def test_freshness_breach_on_no_price_data(empty_engine, tmp_path_factory, monkeypatch):
    _point_ledgers_at(monkeypatch, tmp_path_factory.mktemp("no_price_data"), ok=True)
    cfg = load_config()
    with Session(empty_engine) as session:
        result = compute_preflight(session, config=cfg)
    assert result["components"]["freshness"]["ok"] is False
    assert "no price data" in result["components"]["freshness"]["detail"]


# ==================================================================================================
# Verdict-history: append-only, ONLY on a transition
# ==================================================================================================
def test_record_verdict_transition_appends_only_on_change(tmp_path):
    path = str(tmp_path / "history.jsonl")
    assert record_verdict_transition(GO, [], "2026-07-08", path=path) is True
    assert record_verdict_transition(GO, [], "2026-07-08", path=path) is False  # unchanged -> no growth
    assert record_verdict_transition(GO, [], "2026-07-08", path=path) is False  # repeated polls: still no growth
    assert record_verdict_transition(DEGRADED, ["stale"], "2026-07-08", path=path) is True
    assert record_verdict_transition(NO_GO, ["stale", "db down"], "2026-07-08", path=path) is True
    entries = read_entries(path)
    assert [e["verdict"] for e in entries] == [GO, DEGRADED, NO_GO]
    assert entries[1]["reasons"] == ["stale"]


def test_record_verdict_transition_missing_file_first_call_appends(tmp_path):
    """A brand-new (never-created) history file: the first verdict is itself a transition worth
    recording (an honest starting point for the audit trail), not silently skipped."""
    path = str(tmp_path / "does-not-exist-yet" / "history.jsonl")
    assert record_verdict_transition(GO, [], "2026-07-08", path=path) is True
    assert [e["verdict"] for e in read_entries(path)] == [GO]


def test_resolve_verdict_history_path_env_override(monkeypatch, tmp_path):
    target = tmp_path / "custom-history.jsonl"
    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(target))
    assert resolve_verdict_history_path() == str(target)


def test_resolve_verdict_history_path_defaults_to_config(monkeypatch):
    monkeypatch.delenv(readiness.VERDICT_HISTORY_PATH_ENV, raising=False)
    cfg = load_config()
    resolved = resolve_verdict_history_path()
    assert resolved.endswith(cfg.readiness.verdict_history_path)


# ==================================================================================================
# ops-hardening iter-70 (J-07) -- config validation for the new readiness.refresh_interval_seconds knob
# ==================================================================================================
def test_readiness_cfg_refresh_interval_defaults_to_half_second():
    from app.config import ReadinessCfg

    cfg = ReadinessCfg(
        freshness_max_age_days=5,
        severity={"servability": "no-go", "freshness": "degraded", "integrity": "no-go", "drift": "degraded"},
        verdict_history_path="x.jsonl",
    )
    assert cfg.refresh_interval_seconds == 0.5


def test_readiness_cfg_rejects_nonpositive_refresh_interval():
    from app.config import ReadinessCfg

    with pytest.raises(ValueError, match="refresh_interval_seconds must be > 0"):
        ReadinessCfg(
            freshness_max_age_days=5,
            severity={"servability": "no-go", "freshness": "degraded", "integrity": "no-go", "drift": "degraded"},
            verdict_history_path="x.jsonl",
            refresh_interval_seconds=0,
        )


# ==================================================================================================
# ops-hardening iter-71 (J-07 closure) -- the readiness-cache staleness bound's config knob.
# ==================================================================================================
def test_readiness_cfg_max_stale_intervals_defaults_to_three():
    from app.config import ReadinessCfg

    cfg = ReadinessCfg(
        freshness_max_age_days=5,
        severity={"servability": "no-go", "freshness": "degraded", "integrity": "no-go", "drift": "degraded"},
        verdict_history_path="x.jsonl",
    )
    assert cfg.max_stale_intervals == 3


def test_readiness_cfg_rejects_nonpositive_max_stale_intervals():
    from app.config import ReadinessCfg

    with pytest.raises(ValueError, match="max_stale_intervals must be > 0"):
        ReadinessCfg(
            freshness_max_age_days=5,
            severity={"servability": "no-go", "freshness": "degraded", "integrity": "no-go", "drift": "degraded"},
            verdict_history_path="x.jsonl",
            max_stale_intervals=0,
        )


# ==================================================================================================
# ops-hardening iter-70 (J-07) -- bounded-interval background-refresh cache: cold-start fallback (TC-1),
# steady-state cache-read vs. recompute (TC-2), concurrency/atomic-swap, degrade-on-error (TC-6), the
# verdict-transition write firing exactly once under concurrent ticks (TC-5), the immediate-refresh
# trigger, and the single-flight thread guard. A tiny, dedicated `cache_engine` fixture (NOT the shared
# `loaded_engine`/`empty_engine`/etc. fixtures above) keeps these tests fast; an autouse fixture stops any
# live background thread and resets the shared cache before AND after every test in this file, so nothing
# here can leak a ticking thread or a stale cached value into another test module.
# ==================================================================================================
@pytest.fixture(autouse=True)
def _isolated_readiness_cache():
    readiness.stop_readiness_refresh()
    readiness.reset_readiness_refresh_cache()
    yield
    readiness.stop_readiness_refresh()
    readiness.reset_readiness_refresh_cache()


@pytest.fixture
def cache_engine(tmp_path, config):
    """A tiny, fast, dedicated DB with one servable snapshot, for the background-refresh CACHE tests
    only -- independent of the shared fixtures above."""
    engine = make_engine(f"sqlite:///{tmp_path / 'cache_test.db'}")
    create_db_and_tables(engine)
    benchmark = config.etfs.index[0]
    d0 = date(2024, 3, 4)
    with Session(engine) as session:
        session.add(DailyPrice(symbol=benchmark, date=d0, open=1, high=1, low=1, close=1, volume=1))
        session.add(ScannerRun(
            asof_date=d0, created_at=datetime(2024, 3, 4), provider="seed", benchmark=benchmark,
            regime_score=50.0, regime_label="Choppy", regime_components_json="[]",
            new_high_low_json="{}", candidate_counts_json="{}",
        ))
        session.commit()
    return engine


def test_readiness_cache_cold_start_matches_direct_compute(cache_engine, config, monkeypatch, tmp_path):
    """TC-1: before the background thread's first tick completes, `get_readiness_and_preflight` computes
    once synchronously -- byte-identical to a direct `compute_readiness`/`compute_preflight` call taken
    at the same moment (no thread has been started against `cache_engine` in this test)."""
    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
    with Session(cache_engine) as session:
        cached = readiness.get_readiness_and_preflight(session, engine=cache_engine, config=config)
        direct_readiness = compute_readiness(session, engine=cache_engine, config=config)
        direct_preflight = compute_preflight(session, config=config)
    assert cached["readiness"] == direct_readiness
    assert cached["preflight"] == direct_preflight


def test_readiness_cache_cold_start_never_raises_on_a_first_tick_failure(cache_engine, config, monkeypatch):
    """A first-ever tick failure (before any completed tick exists) degrades to the SAME honest
    unavailable/NO-GO fallback shape `compute_readiness`/`compute_preflight` already produce on their own
    internal errors -- `get_readiness_and_preflight` never raises."""
    def _boom(session, engine=None, config=None):
        raise RuntimeError("simulated DB failure")

    monkeypatch.setattr(readiness, "compute_readiness", _boom)
    with Session(cache_engine) as session:
        result = readiness.get_readiness_and_preflight(session, engine=cache_engine, config=config)
    assert result["readiness"]["state"] == "unavailable"
    assert result["preflight"]["verdict"] == "NO-GO"


def test_readiness_cache_steady_state_reads_do_not_recompute(cache_engine, config, monkeypatch, tmp_path):
    """TC-2: once the background thread has ticked at least once, repeated `get_readiness_and_preflight`
    calls serve the SAME cached payload without re-invoking `compute_readiness`/`compute_preflight` --
    proven by a call-counting monkeypatch (output-value equality alone would also hold under a per-call
    recompute on an unchanging DB, so this proves the READ PATH itself, not just the result)."""
    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
    readiness.start_readiness_refresh(cache_engine, config)
    deadline = time.monotonic() + 5.0
    while readiness._READINESS_CACHE is None and time.monotonic() < deadline:
        time.sleep(0.01)
    assert readiness._READINESS_CACHE is not None, "background thread never completed its first tick"

    calls = {"readiness": 0, "preflight": 0}
    real_compute_readiness = readiness.compute_readiness
    real_compute_preflight = readiness.compute_preflight

    def _counting_readiness(*a, **kw):
        calls["readiness"] += 1
        return real_compute_readiness(*a, **kw)

    def _counting_preflight(*a, **kw):
        calls["preflight"] += 1
        return real_compute_preflight(*a, **kw)

    monkeypatch.setattr(readiness, "compute_readiness", _counting_readiness)
    monkeypatch.setattr(readiness, "compute_preflight", _counting_preflight)

    with Session(cache_engine) as session:
        results = [
            readiness.get_readiness_and_preflight(session, engine=cache_engine, config=config)
            for _ in range(50)
        ]
    readiness.stop_readiness_refresh()  # before the NEXT (interval-away) tick could fire and get counted

    assert calls == {"readiness": 0, "preflight": 0}
    # ops-hardening iter-71: `stale_for_s` is a REAL elapsed-time measurement (re-derived every call
    # against `computed_at`), so it legitimately differs call-to-call even when served from the SAME
    # cache entry -- compare the entry's actual content (readiness/preflight), not the whole dict.
    assert all(r["readiness"] == results[0]["readiness"] for r in results)
    assert all(r["preflight"] == results[0]["preflight"] for r in results)


def test_readiness_cache_degrades_to_last_known_good_on_tick_failure(cache_engine, config, monkeypatch, tmp_path):
    """TC-6: a tick whose compute raises leaves the cache serving the PRIOR last-known-good value -- never
    blanked, never raised out to the caller. The thread keeps ticking on schedule: once the failure clears,
    the NEXT tick resumes normal cache updates."""
    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
    real_compute_readiness = readiness.compute_readiness
    with Session(cache_engine) as session:
        good = readiness._tick_and_cache(session, config, engine=cache_engine)
    assert good is not None

    def _boom(session, engine=None, config=None):
        raise RuntimeError("simulated DB/ledger read failure")

    monkeypatch.setattr(readiness, "compute_readiness", _boom)
    with Session(cache_engine) as session:
        failed = readiness._tick_and_cache(session, config, engine=cache_engine)
    assert failed is None
    assert readiness._READINESS_CACHE == good  # untouched by the failed tick

    with Session(cache_engine) as session:
        served = readiness.get_readiness_and_preflight(session, engine=cache_engine, config=config)
    # a reader still gets the last-known-good value -- HTTP 200 shape intact. `stale_for_s` (ops-hardening
    # iter-71) is compared separately: it's an ADDITIVE, real elapsed-time reading, not part of `good`'s
    # own identity (`_tick_and_cache`'s raw return has no `stale_for_s` key at all).
    assert served["readiness"] == good["readiness"]
    assert served["preflight"] == good["preflight"]
    assert served["stale_for_s"] >= 0.0

    monkeypatch.setattr(readiness, "compute_readiness", real_compute_readiness)  # the failure clears
    with Session(cache_engine) as session:
        recovered = readiness._tick_and_cache(session, config, engine=cache_engine)
    assert recovered is not None
    assert readiness._READINESS_CACHE == recovered


def test_readiness_cache_verdict_transition_fires_once_under_concurrent_ticks(
    cache_engine, config, monkeypatch, tmp_path
):
    """TC-5: when the SAME new verdict is observed by two ticks racing concurrently (e.g. the periodic
    thread and an ingest finalize hook's immediate-refresh trigger landing at the same instant),
    `record_verdict_transition` still appends exactly ONE entry for that transition -- `_TICK_LOCK`
    serializes the read-last-entry-then-maybe-append sequence so two concurrent ticks never both observe
    'no transition recorded yet' and both append."""
    history_path = tmp_path / "history.jsonl"
    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(history_path))

    def _fixed_preflight(session, config=None):
        return {
            "verdict": "DEGRADED", "reasons": ["forced"], "components": {},
            "as_of": "2024-03-04", "reference": "2024-03-04",
        }

    monkeypatch.setattr(readiness, "compute_preflight", _fixed_preflight)

    barrier = threading.Barrier(2)

    def _run():
        barrier.wait()
        with Session(cache_engine) as session:
            readiness._tick_and_cache(session, config, engine=cache_engine)

    threads = [threading.Thread(target=_run) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    entries = read_entries(str(history_path))
    assert [e["verdict"] for e in entries] == ["DEGRADED"]


def test_readiness_cache_read_never_observes_a_torn_write(cache_engine, config, monkeypatch, tmp_path):
    """Concurrency: a cache read on one thread never observes a torn/partial write from an in-flight tick
    on another thread. `readiness["state"]` and `preflight["verdict"]` observed together in ONE read are
    always tagged from the SAME tick (an incrementing counter shared by both crafted producers), never a
    mix of two different ticks' halves -- proving the cache swap is atomic, not merely usually-fast."""
    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
    monkeypatch.setattr(readiness, "record_verdict_transition", lambda *a, **kw: False)
    tick_counter = {"n": 0}

    def _tagged_readiness(session, engine=None, config=None):
        tick_counter["n"] += 1
        tag = tick_counter["n"]
        time.sleep(0.001)  # widen the window a torn read would need to land in
        return {
            "state": f"tag-{tag}", "detail": None,
            "warmup": {"done": tag, "total": tag, "status": "ok", "message": f"history {tag}/{tag}"},
            "background_compute": {"active": [], "recent_outcomes": []},
        }

    def _tagged_preflight(session, config=None):
        tag = tick_counter["n"]  # the SAME counter value the readiness call just used
        return {"verdict": f"tag-{tag}", "reasons": [], "components": {}, "as_of": None, "reference": None}

    monkeypatch.setattr(readiness, "compute_readiness", _tagged_readiness)
    monkeypatch.setattr(readiness, "compute_preflight", _tagged_preflight)

    stop_flag = {"stop": False}
    observed: list[dict] = []

    def _writer():
        with Session(cache_engine) as session:
            while not stop_flag["stop"]:
                readiness._tick_and_cache(session, config, engine=cache_engine)

    def _reader():
        with Session(cache_engine) as session:
            for _ in range(200):
                observed.append(readiness.get_readiness_and_preflight(session, engine=cache_engine, config=config))

    writer_thread = threading.Thread(target=_writer)
    reader_threads = [threading.Thread(target=_reader) for _ in range(4)]
    writer_thread.start()
    for t in reader_threads:
        t.start()
    for t in reader_threads:
        t.join()
    stop_flag["stop"] = True
    writer_thread.join()

    assert observed, "no reads were captured -- the test setup itself is broken"
    for cached in observed:
        readiness_tag = cached["readiness"]["state"].split("-")[1]
        preflight_tag = cached["preflight"]["verdict"].split("-")[1]
        assert readiness_tag == preflight_tag, f"torn read observed: {cached}"


def test_trigger_readiness_refresh_updates_the_cache_immediately(cache_engine, config, monkeypatch, tmp_path):
    """The immediate-refresh trigger (called from the ingest finalize hook) runs one tick right now and
    publishes it to the shared cache -- TC-4's cache-level half (the finalize hook actually FIRING the
    trigger is covered by test_data_manager.py's own dedicated test)."""
    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
    assert readiness._READINESS_CACHE is None
    with Session(cache_engine) as session:
        readiness.trigger_readiness_refresh(session, config=config, engine=cache_engine)
    assert readiness._READINESS_CACHE is not None
    assert readiness._READINESS_CACHE["readiness"]["state"] in {
        "ready", "initializing", "unavailable", "awaiting_snapshot",
    }


def test_start_readiness_refresh_is_single_flight(cache_engine, config):
    """Mirrors `warmup.start_warmup`'s own single-flight guard shape: a re-entry while the thread is
    already alive is a no-op (no second concurrent thread spawned)."""
    readiness.start_readiness_refresh(cache_engine, config)
    first_thread = readiness._REFRESH_THREAD
    readiness.start_readiness_refresh(cache_engine, config)
    assert readiness._REFRESH_THREAD is first_thread
    readiness.stop_readiness_refresh()
    assert readiness._REFRESH_THREAD.is_alive() is False


# ==================================================================================================
# ops-hardening iter-71 (J-07 closure) -- the readiness-cache staleness bound: a wedged/dead
# background-refresh tick thread must never let `get_readiness_and_preflight` go on serving an
# ever-more-frozen cache entry forever. TC-1 (synchronous fallback past the bound) and TC-2 (a fresh
# entry is still served as-is, with a real `stale_for_s` reading) both live here.
# ==================================================================================================
def test_readiness_cache_serves_fresh_entry_with_stale_for_s_below_threshold(cache_engine, config, monkeypatch, tmp_path):
    """TC-2: a cache entry younger than `max_stale_intervals x refresh_interval_seconds` is served AS-IS
    -- `stale_for_s` is a real, non-negative measurement strictly below that threshold, and NO synchronous
    compute fires (call-count instrumentation, not just output-value equality)."""
    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
    with Session(cache_engine) as session:
        readiness._tick_and_cache(session, config, engine=cache_engine)

    calls = {"n": 0}
    real_compute_readiness = readiness.compute_readiness

    def _counting(*a, **kw):
        calls["n"] += 1
        return real_compute_readiness(*a, **kw)

    monkeypatch.setattr(readiness, "compute_readiness", _counting)
    with Session(cache_engine) as session:
        result = readiness.get_readiness_and_preflight(session, engine=cache_engine, config=config)

    threshold = config.readiness.max_stale_intervals * config.readiness.refresh_interval_seconds
    assert calls["n"] == 0  # served straight from the cache -- no fallback compute
    assert 0.0 <= result["stale_for_s"] < threshold


def test_readiness_cache_falls_back_to_synchronous_compute_past_the_staleness_bound(
    cache_engine, config, monkeypatch, tmp_path
):
    """TC-1: given the readiness background-refresh tick thread effectively stopped (a test hook backdates
    the cache entry's `computed_at`, simulating a wedged/dead tick thread with no live thread required),
    when the entry's age exceeds `max_stale_intervals x refresh_interval_seconds` and a client calls
    `GET /api/health`'s read path, then the response is produced by a SYNCHRONOUS `compute_readiness` call
    (proven by call-count instrumentation, not the stale cache) and `stale_for_s` equals 0 -- never served
    indefinitely stale."""
    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
    with Session(cache_engine) as session:
        readiness._tick_and_cache(session, config, engine=cache_engine)
    assert readiness._READINESS_CACHE is not None

    threshold = config.readiness.max_stale_intervals * config.readiness.refresh_interval_seconds
    stale = dict(readiness._READINESS_CACHE)
    stale["computed_at"] -= (threshold + 10.0)  # well past the bound
    readiness._READINESS_CACHE = stale

    # Counts `compute_preflight`, not `compute_readiness` -- `compute_preflight` itself calls
    # `compute_readiness` a second time internally (servability reuses it verbatim), so counting
    # `compute_readiness` directly would over-count by 2x per tick. `compute_preflight` is invoked
    # exactly once per tick, making it the clean "did exactly one synchronous tick fire" signal.
    calls = {"n": 0}
    real_compute_preflight = readiness.compute_preflight

    def _counting(*a, **kw):
        calls["n"] += 1
        return real_compute_preflight(*a, **kw)

    monkeypatch.setattr(readiness, "compute_preflight", _counting)
    with Session(cache_engine) as session:
        result = readiness.get_readiness_and_preflight(session, engine=cache_engine, config=config)

    assert calls["n"] == 1  # exactly one synchronous fallback tick fired -- the stale entry was never served
    assert result["stale_for_s"] == 0.0
    # the fallback also re-published a FRESH cache entry (mirrors the cold-start path) -- a later reader
    # within the bound serves this fresh entry, not the stale one that triggered the fallback.
    assert readiness._READINESS_CACHE["computed_at"] > stale["computed_at"]


def test_readiness_cache_staleness_bound_never_raises_when_the_fallback_tick_also_fails(
    cache_engine, config, monkeypatch, tmp_path
):
    """A stale entry past the bound whose fallback compute ALSO fails degrades to the SAME honest
    unavailable/NO-GO shape the cold-start path already produces -- never raises, never serves the
    stale entry as a fallback of last resort (the whole point of the bound is to never do that)."""
    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
    with Session(cache_engine) as session:
        readiness._tick_and_cache(session, config, engine=cache_engine)

    threshold = config.readiness.max_stale_intervals * config.readiness.refresh_interval_seconds
    stale = dict(readiness._READINESS_CACHE)
    stale["computed_at"] -= (threshold + 10.0)
    readiness._READINESS_CACHE = stale

    def _boom(session, engine=None, config=None):
        raise RuntimeError("simulated fallback compute failure")

    monkeypatch.setattr(readiness, "compute_readiness", _boom)
    with Session(cache_engine) as session:
        result = readiness.get_readiness_and_preflight(session, engine=cache_engine, config=config)

    assert result["readiness"]["state"] == "unavailable"
    assert result["preflight"]["verdict"] == "NO-GO"
    assert result["stale_for_s"] == 0.0


# ==================================================================================================
# ops-hardening iter-70 AUDIT (finding B1) -- a tick failure whose OWN `logger.exception` render also
# raises (the `MemoryError`-under-an-exhausted-`ulimit -v` class `data_manager._log_isolation_failure`
# was built for in iter-45) must still not escape. Two callers make the escape matter: the ingest
# finalize hook (`_refresh_ingest_aggregates` -> `trigger_readiness_refresh`), where an escape discards
# the whole `refreshed` list, and `_refresh_loop`, where an escape kills the daemon thread and freezes
# the cache forever with no error surfaced.
# ==================================================================================================
def test_tick_failure_never_escapes_even_when_its_own_logging_raises(cache_engine, config, monkeypatch, tmp_path):
    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))

    def _boom(session, engine=None, config=None):
        raise MemoryError()

    def _logging_also_boom(*a, **kw):
        raise MemoryError()

    monkeypatch.setattr(readiness, "compute_readiness", _boom)
    monkeypatch.setattr(readiness.logger, "exception", _logging_also_boom)
    monkeypatch.setattr(readiness.logger, "error", _logging_also_boom)

    with Session(cache_engine) as session:
        # `_tick_and_cache`'s own contract: returns None, never raises.
        assert readiness._tick_and_cache(session, config, engine=cache_engine) is None
        # the ingest finalize hook's contract: "never raises out into the calling ingest job".
        readiness.trigger_readiness_refresh(session, config=config, engine=cache_engine)


def test_refresh_loop_survives_a_tick_whose_logging_raises(cache_engine, config, monkeypatch, tmp_path):
    """The background thread keeps ticking (and stays alive) even when both the tick AND its own failure
    logging raise -- a dead thread would freeze the cache indefinitely while `GET /api/health` went on
    serving the stale value with no error anywhere."""
    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
    ticks = {"n": 0}

    def _boom(session, engine=None, config=None):
        ticks["n"] += 1
        raise MemoryError()

    def _logging_also_boom(*a, **kw):
        raise MemoryError()

    monkeypatch.setattr(readiness, "compute_readiness", _boom)
    monkeypatch.setattr(readiness.logger, "exception", _logging_also_boom)
    monkeypatch.setattr(readiness.logger, "error", _logging_also_boom)

    readiness.start_readiness_refresh(cache_engine, config)
    deadline = time.monotonic() + 5.0
    while ticks["n"] < 2 and time.monotonic() < deadline:
        time.sleep(0.01)
    assert ticks["n"] >= 2, "the refresh thread stopped ticking after the first failing tick"
    assert readiness._REFRESH_THREAD.is_alive() is True
    assert readiness._READINESS_CACHE is None  # never blanked into a partial/undefined value
    readiness.stop_readiness_refresh()
