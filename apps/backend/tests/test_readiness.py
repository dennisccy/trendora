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

from datetime import date

import pytest
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
from app.models import DailyPrice


def _readiness_cfg(cfg, **overrides):
    """A `cfg` copy with `readiness.<field>` overridden — keeps each test's intent to one line."""
    updated = cfg.readiness.model_copy(update=overrides)
    return cfg.model_copy(update={"readiness": updated})


def _point_ledgers_at(monkeypatch, tmp_dir, *, ok: bool) -> None:
    """Point all three ledger/registry resolvers at `tmp_dir`: valid-but-empty files when `ok`, else
    paths that are never created (the honest "missing" integrity failure)."""
    for filename, env_var in (
        ("certified-claims.jsonl", "TRENDORA_LEDGER_PATH"),
        ("staging-ledger.jsonl", "STAGING_LEDGER_PATH"),
        ("pre-registrations.jsonl", "TRENDORA_REGISTRY_PATH"),
    ):
        target = tmp_dir / filename
        if ok:
            target.write_text("")
        monkeypatch.setenv(env_var, str(target))


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
        assert set(result["components"]) == {"servability", "freshness", "integrity"}
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
            severity={"servability": "no-go", "freshness": "no-go", "integrity": "no-go"},
            verdict_history_path="x.jsonl",
        )


def test_readiness_cfg_rejects_unknown_severity_value():
    from app.config import ReadinessCfg

    with pytest.raises(ValueError, match="must be one of"):
        ReadinessCfg(
            freshness_max_age_days=5,
            severity={"servability": "critical", "freshness": "degraded", "integrity": "no-go"},
            verdict_history_path="x.jsonl",
        )


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
    """`compute_preflight` is ADDITIVE — `compute_readiness`'s own return shape is untouched (J-40 not
    regressed): exactly `{"state", "warmup"}`, `warmup` exactly `{"done","total","status","message"}`."""
    cfg = load_config()
    with Session(loaded_engine) as session:
        result = compute_readiness(session, config=cfg)
    assert set(result) == {"state", "warmup"}
    assert result["state"] in {"ready", "initializing", "unavailable"}
    assert set(result["warmup"]) == {"done", "total", "status", "message"}


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
