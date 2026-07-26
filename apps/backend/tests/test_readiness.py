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
def test_compute_readiness_composes_background_compute_empty_shape(loaded_engine):
    """A process that has never dispatched a historical background compute reports the honest empty
    shape -- never omitted, never fabricated non-empty."""
    import app.engine.forward_testing as forward_testing_module

    cfg = load_config()
    with Session(loaded_engine) as session:
        # A previous test in this same process could have left dispatch state behind (the registry is a
        # process-lifetime global, by design -- J-09 step 6). Reading the SAME accessor directly proves
        # compute_readiness composes it VERBATIM regardless of what it currently holds.
        direct = forward_testing_module.get_background_compute_status()
        result = compute_readiness(session, config=cfg)
    assert result["background_compute"] == direct
    assert isinstance(result["background_compute"]["active"], list)
    assert isinstance(result["background_compute"]["recent_outcomes"], list)


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
