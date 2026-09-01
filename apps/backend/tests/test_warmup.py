"""Fast-ready boot + background warm-up + concurrency-safe / non-fatal startup — iter-28 (J-40/J-41).

Named proofs, each guarding a target journey / critical anti-goal:

  J-40 fast-ready boot
  - ensure-latest-only            — the synchronous boot persists ONLY the latest snapshot (the historical
                                    cadence is NOT all present), so the server serves the latest immediately.
  - readiness-initializing        — readiness reports `initializing` with honest {done,total} while the
                                    cadence is incomplete, and is NEVER `ready` before the latest snapshot
                                    is servable.
  - readiness-ready-after-warmup  — after the background warm-up finishes, readiness flips to `ready`.
  - warm-up-completes-cadence     — `start_warmup` (background thread) produces EVERY remaining cadence
                                    snapshot + forward returns, reusing the canonical engines.

  J-41 boot resilience
  - run_scan-concurrency-safe     — a create-between-check-and-insert race for the same as-of date returns
                                    the existing immutable row, no UNIQUE crash, no duplicate.       *(Snapshots immutable)*
  - forward-returns-concurrency-safe — a concurrent forward-returns INSERT for an already-inserted key does
                                    not crash and produces no duplicate.
  - warm-up-non-fatal             — a warm-up that raises is caught + logged + marked failed; the server still
                                    serves persisted snapshots; readiness reports it honestly (not a silent
                                    green); a subsequent boot completes the idempotent warm-up.

  Invariant re-verification (only the SCHEDULING moved)
  - byte-identical-output         — re-running the OLD synchronous path (bootstrap_runs + backfill) on the
                                    warmed DB inserts ZERO new rows and mutates nothing — i.e. the background
                                    warm-up already produced exactly what the synchronous path would have.

The per-date scan is genuinely expensive (capability #33 memoization is a separate, out-of-scope journey),
so the FULL warm-up is paid ONCE in a module-scoped fixture and reused; the concurrency proofs use a small
early as-of date (less history → faster) and never the latest.
"""
from __future__ import annotations

import json
import threading
from datetime import date

import pytest
from sqlalchemy import func
from sqlmodel import Session, select

from app.config import load_config
from app.db import create_db_and_tables, make_engine
from app.engine import data_manager, prices, warmup as warmup_mod
from app.engine.forward_testing import backfill_forward_returns
from app.engine.prices import latest_data_date
from app.engine.readiness import compute_readiness
from app.engine.scanner import bootstrap_runs, get_run_for_date, run_scan
from app.engine.warmup import (
    WARMUP_JOB_ID,
    ensure_latest_snapshot,
    start_warmup,
    warmup_total,
    _warmup_dates,
)
from app.engine.data_manager import _membership_timeline, membership_timeline_cached
from app.engine.research import _membership_dataset_version
from app.models import (
    CoverageSnapshot,
    ForwardReturn,
    MembershipTimelineCache,
    ScannerResult,
    ScannerRun,
    SectorScoreRow,
    ThemeScoreRow,
)
from app.seed_loader import load_seed

EARLY = date(2022, 10, 7)  # an early, low-history as-of date (fast to scan) used by the race proofs


def _fast_cfg():
    """Real config with a REDUCED walk-forward look-back so the warm-up scans only a few cadence dates
    (keeps these proofs as fast as the engine allows); the universe + engines + startup tunables are real."""
    cfg = load_config()
    wf = cfg.walk_forward.model_copy(update={"history_years": 1, "asof_cadence": "quarterly"})
    return cfg.model_copy(update={"walk_forward": wf})


def _clear_warmup_registry():
    with data_manager._LOCK:
        data_manager._JOBS.pop(WARMUP_JOB_ID, None)


def _join_warmup(job_id: str, timeout: float = 3000.0) -> None:
    """Block until the warm-up thread has SETTLED (reached a terminal status), so the test asserts on a
    final state. The warm-up runs in a daemon thread named `warmup-<id>`; join it, then confirm the
    in-memory record reached `ok`/`failed` (the worker sets the status in its `finally`).

    iter-18 basis budget: the deep 30-year / ~548-name pool makes each cadence `run_scan` score ~4.5x more
    symbols than the retired ~122-name basis, so the full `_warmup_dates` sweep (bootstrap ∪ walk-forward
    cadence) legitimately takes longer than the retired 600s cap allowed (observed ~200-300s/date under the
    marathon full-suite contention -> the 8-date fast-cfg warm-up overran 600s and the daemon thread lingered,
    which also cascaded into the single-flight thread-count proof). This is a TEST-fixture wall-clock
    characteristic, NOT a product problem (the product serves the latest snapshot immediately and warms the
    history in the background). The worker provably PROGRESSES (it is never hung — `test_iter27`'s full-universe
    warm fixture completes the same sweep with no timeout), so a generous settle budget lets it reach its real
    terminal state instead of the harness abandoning a still-progressing warm-up. Sequential/alone (the
    sanctioned full-suite run) is well under this ceiling."""
    name = f"warmup-{job_id}"
    for t in threading.enumerate():
        if t.name == name:
            t.join(timeout)
            break
    rec = data_manager.get_job(job_id)
    assert rec is None or rec["status"] in {"ok", "failed"}, (
        f"warm-up did not settle within {timeout}s: {rec}"
    )


@pytest.fixture(scope="module")
def warmed_engine(tmp_path_factory):
    """A temp DB taken through the FULL NEW boot path ONCE: seed → ensure_latest_snapshot (synchronous)
    → start_warmup (background, joined to completion). Returns the engine + cfg + the latest date + the
    cadence set + the post-ensure (pre-warm) readiness captured BEFORE the warm-up finished. Reused by
    every J-40 assertion so the ~minutes-long warm-up is paid only once."""
    cfg = _fast_cfg()
    db_path = tmp_path_factory.mktemp("warmed_db") / "warmed.db"
    engine = make_engine(f"sqlite:///{db_path}")
    create_db_and_tables(engine)
    load_seed(engine, cfg)
    _clear_warmup_registry()

    # readiness BEFORE any snapshot — unavailable (no servable latest). Never a fabricated ready.
    with Session(engine) as session:
        readiness_empty = compute_readiness(session, engine=engine, config=cfg)

    latest = ensure_latest_snapshot(engine, cfg)

    # readiness AFTER the synchronous latest-snapshot but BEFORE the background warm-up — initializing
    # with honest progress (latest servable, history incomplete). Captured here, before warm-up runs.
    with Session(engine) as session:
        readiness_pre_warmup = compute_readiness(session, engine=engine, config=cfg)
        cadence_dates = set(_warmup_dates(session, cfg))

    job_id = start_warmup(engine, cfg)
    _join_warmup(job_id)
    yield {
        "engine": engine,
        "cfg": cfg,
        "latest": latest,
        "cadence_dates": cadence_dates,
        "readiness_empty": readiness_empty,
        "readiness_pre_warmup": readiness_pre_warmup,
        "warmup_record": data_manager.get_job(job_id),
    }
    _clear_warmup_registry()


@pytest.fixture
def early_engine(tmp_path_factory):
    """A freshly-seeded temp DB with NO snapshots — a clean starting point for the concurrency race
    proofs (which scan only the fast EARLY date, never the slow latest)."""
    cfg = _fast_cfg()
    db_path = tmp_path_factory.mktemp("race_db") / "race.db"
    engine = make_engine(f"sqlite:///{db_path}")
    create_db_and_tables(engine)
    load_seed(engine, cfg)
    return engine, cfg


# ==================================================================================================
# J-40 — fast-ready boot: only the latest snapshot is synchronous; the cadence warms up in background
# ==================================================================================================
def test_ensure_latest_persists_only_latest_before_warmup(warmed_engine):
    """The minimal synchronous boot step persists ONLY the latest data date's snapshot — at that point
    the historical cadence dates are NOT yet present (they are the background warm-up's job), and the
    latest is EXCLUDED from the warm-up set. So the server can serve the latest as-of immediately on
    yield without waiting on the multi-date backfill."""
    cfg = warmed_engine["cfg"]
    latest = warmed_engine["latest"]
    cadence = warmed_engine["cadence_dates"]
    # there IS remaining historical cadence work (the synchronous step did not do it all)...
    assert len(cadence) > 0
    # ...and the latest is excluded from it (it was produced synchronously).
    assert latest not in cadence


def test_readiness_unavailable_then_initializing_then_ready(warmed_engine):
    """Readiness is honest across the boot lifecycle (J-40): unavailable before any snapshot, then
    initializing with a real {done, total} after the synchronous latest-snapshot but before the cadence
    warm-up, then ready ONLY after the background warm-up has finished. NEVER ready before the latest
    snapshot is servable."""
    # (1) before any snapshot -> unavailable
    assert warmed_engine["readiness_empty"]["state"] == "unavailable"

    # (2) latest servable, history incomplete -> initializing with honest progress (done < total)
    pre = warmed_engine["readiness_pre_warmup"]
    assert pre["state"] == "initializing"
    assert pre["warmup"]["total"] > 0
    assert pre["warmup"]["done"] < pre["warmup"]["total"]
    assert pre["warmup"]["message"] == f"history {pre['warmup']['done']}/{pre['warmup']['total']}"

    # (3) after the warm-up completes -> ready, with done == total
    engine, cfg = warmed_engine["engine"], warmed_engine["cfg"]
    with Session(engine) as session:
        post = compute_readiness(session, engine=engine, config=cfg)
    assert post["state"] == "ready"
    assert post["warmup"]["done"] == post["warmup"]["total"]


def test_warmup_produced_every_cadence_snapshot_and_forward_returns(warmed_engine):
    """The background warm-up reused the canonical engines to persist EVERY remaining cadence snapshot
    AND its realized forward returns — so after it finishes the DB holds the complete historical
    evidence the analytics pages read (J-40), produced off the boot path (only scheduling moved)."""
    engine = warmed_engine["engine"]
    expected = warmed_engine["cadence_dates"]
    latest = warmed_engine["latest"]
    with Session(engine) as session:
        run_dates = {r.asof_date for r in session.exec(select(ScannerRun)).all()}
        assert expected <= run_dates  # every cadence date persisted
        assert latest in run_dates    # plus the synchronously-produced latest
        n_fr = session.scalar(select(func.count()).select_from(ForwardReturn))
        assert n_fr > 0               # the warm-up inserted realized forward returns
    assert warmed_engine["warmup_record"]["status"] == "ok"


def test_warmup_loads_each_symbol_at_most_once_across_cadence_and_forward_returns(early_engine, monkeypatch):
    """iter-26 (J-16, fast-platform item F): the warm-up's cadence loop (`run_scan` x N dates) AND its
    trailing `backfill_forward_returns` call now share ONE `bar_cache` context (the `warmup.py` fix —
    the call moved inside the `with bar_cache(session):` block and now passes `session`, not `engine`),
    so together they load each symbol's full series AT MOST ONCE for the whole warm-up run — not once
    per cadence date, and not a SECOND time for the forward-return backfill (which used to open a brand
    new, uncached session). Instrumented exactly like
    `test_bar_cache.py::test_kdate_backfill_loads_each_symbol_at_most_once` (every full-series bar-store
    load: the lazy `bars_asof` fallback AND `prefill`; `bars_after`'s cache path routes through the
    same instrumented `bars_asof`, since it calls `self.bars_asof(...)` to ensure the load).

    The iter-36 (J-96) membership-timeline warm step (`_warm_membership_timeline`) is a SEPARATE,
    pre-existing, out-of-scope feature: it deliberately opens its OWN new session (never the cadence
    loop's) and therefore pays its own one-time prefill regardless of this fix — confirmed unrelated
    (its own test, `test_warmup_precomputes_membership_timeline_cache`, passes unedited). It is
    no-op'd here so this proof isolates exactly the two pieces iter-26 changed."""
    engine, cfg = early_engine
    monkeypatch.setattr(warmup_mod, "_warm_membership_timeline", lambda engine, cfg: None)
    load_counts: dict[str, int] = {}
    orig_bars_asof = prices._BarCache.bars_asof
    orig_prefill = prices._BarCache.prefill

    def _counting_bars_asof(self, session, symbol, d):
        if symbol not in self._by_symbol:  # a real lazy bar-store load is about to happen
            load_counts[symbol] = load_counts.get(symbol, 0) + 1
        return orig_bars_asof(self, session, symbol, d)

    def _counting_prefill(self, session, expected_symbols=None):
        before = set(self._by_symbol)
        orig_prefill(self, session, expected_symbols=expected_symbols)
        for symbol in self._by_symbol:
            if symbol not in before:  # newly loaded by this prefill
                load_counts[symbol] = load_counts.get(symbol, 0) + 1

    monkeypatch.setattr(prices._BarCache, "bars_asof", _counting_bars_asof)
    monkeypatch.setattr(prices._BarCache, "prefill", _counting_prefill)

    job_id = start_warmup(engine, cfg)
    _join_warmup(job_id)
    rec = data_manager.get_job(job_id)
    assert rec["status"] == "ok"
    assert rec["forward_returns_inserted"] > 0, "the warm-up should have inserted realized forward returns"
    assert load_counts, "the warm-up should have loaded at least one symbol's bar series"
    assert max(load_counts.values()) == 1, f"a symbol was loaded more than once: {load_counts}"


# ==================================================================================================
# goal-market-compass iter-33 (J-09/AG-8, Constraints (c)) — bound the cold cadence-date allocation
# `warmup.py:351`'s bar-cache context produces. `cfg.startup.warmup_bar_cache_bounded` (default True)
# selects `prefilled_bar_cache` (the compact array-based `_SymbolColumns` eager scan, unconditional --
# no `expected_symbols` filter, so no iter-42-class exclusion) instead of the pre-iter-33 lazy
# `bar_cache` context, which built the costlier per-symbol `list[Bar]` representation for every symbol
# the cadence loop touched. These two tests prove (1) the config key genuinely selects the mechanism,
# with zero symbol exclusion either way, and (2) the two mechanisms produce BYTE-IDENTICAL served
# output -- the switch changes only which representation is resident, never a stored value.
#
# Both tests no-op `_warm_drawdown_expectations` (like the iter-26 test above no-ops
# `_warm_membership_timeline`): that step (added ops-hardening iter-46, AFTER the iter-26 test was
# written) computes each evidence-ledger claim on its OWN short-lived per-claim `Session` + bar-cache
# context, strictly AFTER `_run_warmup`'s cadence `with cache_ctx:` block this iteration targets has
# already exited -- unrelated machinery, confirmed by a live call-stack trace during this iteration's
# investigation. Without this no-op, `test_warmup_loads_each_symbol_at_most_once_across_cadence_and_
# forward_returns` (the iter-26 test above) fails on an UNMODIFIED `main` too (reproduced by stashing
# this iteration's diff and re-running it) -- `^VIX` is loaded once per evidence claim (7 on the live
# ledger) via `market_phase.phase_context_by_date` -> `_causal_timeline` -> `_severity_reading` ->
# `_latest_vix_on_or_before` -> `close_on`, each call opening its own fresh session/cache pair. This is
# a pre-existing test/instrumentation gap, NOT introduced by this iteration and NOT touched by it (out
# of this iteration's scope) -- see this iteration's dev handoff Known Issues.
def test_warmup_bar_cache_bounded_config_selects_prefill_mechanism(early_engine, monkeypatch):
    """`cfg.startup.warmup_bar_cache_bounded=True` (the default) routes the cadence loop's bar-cache
    context through `prefilled_bar_cache` with `expected_symbols=None` (the unconditional whole-table
    scan -- never the iter-42 filtered shape); `False` reverts to the plain `bar_cache` context. Proves
    the config key actually selects the mechanism (not merely documented intent)."""
    engine, cfg = early_engine
    monkeypatch.setattr(warmup_mod, "_warm_membership_timeline", lambda engine, cfg: None)
    monkeypatch.setattr(warmup_mod, "_warm_drawdown_expectations", lambda engine, cfg: None)

    calls: list[tuple[str, object]] = []
    orig_bar_cache = warmup_mod.bar_cache
    orig_prefilled = warmup_mod.prefilled_bar_cache

    def _tracking_bar_cache(session):
        calls.append(("bar_cache", None))
        return orig_bar_cache(session)

    def _tracking_prefilled(session, expected_symbols=None):
        calls.append(("prefilled_bar_cache", expected_symbols))
        return orig_prefilled(session, expected_symbols=expected_symbols)

    monkeypatch.setattr(warmup_mod, "bar_cache", _tracking_bar_cache)
    monkeypatch.setattr(warmup_mod, "prefilled_bar_cache", _tracking_prefilled)

    bounded_cfg = cfg.model_copy(
        update={"startup": cfg.startup.model_copy(update={"warmup_bar_cache_bounded": True})}
    )
    job_id = start_warmup(engine, bounded_cfg)
    _join_warmup(job_id)
    assert data_manager.get_job(job_id)["status"] == "ok"
    assert calls == [("prefilled_bar_cache", None)], (
        f"bounded=True must call prefilled_bar_cache(session, expected_symbols=None) exactly once, "
        f"never bar_cache directly and never a filtered expected_symbols: {calls}"
    )

    _clear_warmup_registry()
    calls.clear()
    unbounded_cfg = cfg.model_copy(
        update={"startup": cfg.startup.model_copy(update={"warmup_bar_cache_bounded": False})}
    )
    job_id2 = start_warmup(engine, unbounded_cfg)
    _join_warmup(job_id2)
    assert data_manager.get_job(job_id2)["status"] == "ok"
    assert calls == [("bar_cache", None)], (
        f"bounded=False must call bar_cache(session) exactly once, never prefilled_bar_cache: {calls}"
    )


def test_warmup_bar_cache_bounded_is_byte_identical_to_unbounded(tmp_path_factory, monkeypatch):
    """The config switch changes ONLY which `_BarCache` loading mechanism the cadence context uses --
    never a served value. Runs the SAME fast fixture warm-up on two freshly-seeded, otherwise-identical
    DBs, once with `warmup_bar_cache_bounded=True` and once `False`, and asserts every persisted
    `ScannerRun`/`ScannerResult`/`ForwardReturn` field the two runs produce is identical (never a
    diff, never merely 'both non-empty') -- the exact AG-3/Constraints(c) 'no served value changes'
    guarantee this iteration's safety catch requires before any bound may ship."""
    monkeypatch.setattr(warmup_mod, "_warm_membership_timeline", lambda engine, cfg: None)
    monkeypatch.setattr(warmup_mod, "_warm_drawdown_expectations", lambda engine, cfg: None)

    def _run_once(bounded: bool, label: str) -> dict:
        cfg = _fast_cfg()
        cfg = cfg.model_copy(
            update={"startup": cfg.startup.model_copy(update={"warmup_bar_cache_bounded": bounded})}
        )
        db_path = tmp_path_factory.mktemp(f"bytecheck_{label}") / "db.sqlite"
        engine = make_engine(f"sqlite:///{db_path}")
        create_db_and_tables(engine)
        load_seed(engine, cfg)
        _clear_warmup_registry()
        job_id = start_warmup(engine, cfg)
        _join_warmup(job_id)
        rec = data_manager.get_job(job_id)
        assert rec["status"] == "ok"
        with Session(engine) as session:
            runs = sorted(session.exec(select(ScannerRun)).all(), key=lambda r: r.asof_date.isoformat())
            run_rows = [
                (
                    r.asof_date.isoformat(), r.regime_score, r.regime_label, r.breadth_above_50dma,
                    r.breadth_above_200dma, r.new_high_low_json, r.candidate_counts_json,
                    r.regime_components_json,
                )
                for r in runs
            ]
            results = sorted(
                session.exec(select(ScannerResult)).all(),
                key=lambda x: (x.run_id, x.ticker),
            )
            result_rows = [
                (
                    x.run_id, x.ticker, x.leadership_score, x.entry_quality_score, x.risk_score,
                    x.setup_status, x.rank,
                )
                for x in results
            ]
            fr_rows = sorted(
                (
                    fr.run_id, fr.symbol, fr.horizon, round(fr.realized_return, 8),
                )
                for fr in session.exec(select(ForwardReturn)).all()
            )
        _clear_warmup_registry()
        return {"runs": run_rows, "results": result_rows, "forward_returns": fr_rows}

    bounded_out = _run_once(True, "bounded")
    unbounded_out = _run_once(False, "unbounded")

    assert bounded_out["runs"], "the fast fixture must have produced at least one cadence run"
    assert bounded_out["runs"] == unbounded_out["runs"], "bounded ScannerRun fields diverged from unbounded"
    assert bounded_out["results"] == unbounded_out["results"], (
        "bounded ScannerResult fields diverged from unbounded"
    )
    assert bounded_out["forward_returns"] == unbounded_out["forward_returns"], (
        "bounded ForwardReturn fields diverged from unbounded"
    )


# ==================================================================================================
# iter-36 (J-96) — the warm-up precomputes the membership-timeline cache OFF the boot path so the FIRST
# `GET /api/data` after boot/rebuild serves the cached payload (not the O(dates × pool) cold compute)
# ==================================================================================================
def test_warmup_precomputes_membership_timeline_cache(warmed_engine):
    """After the background warm-up finishes, the dynamic-universe membership-timeline cache is already
    populated under the CURRENT membership-dataset stamp — so the first `GET /api/data` serves it from
    storage rather than paying the per-date resolver loop synchronously (the iter-35 regression fix). The
    cached payload is byte-identical to a fresh `_membership_timeline(...)` compute (a cache of the
    deterministic derivation, not a second computation).

    iter-42 (J-100): the cache row is keyed by the NARROW `_membership_dataset_version` (the snapshot set +
    bars manifest), NOT the broad `_dataset_version` (which folds in the forward-return count). The warm-up
    precomputes the membership cache AFTER the forward-return backfill, but because the narrow stamp is
    INDEPENDENT of the forward-return inserts the warmed row stays valid for a subsequent read (no recompute
    storm) — exactly the stamp a `GET /api/data` looks up."""
    engine, cfg = warmed_engine["engine"], warmed_engine["cfg"]
    with Session(engine) as session:
        version = _membership_dataset_version(session, cfg)
        rows = session.exec(select(MembershipTimelineCache)).all()
        # exactly ONE cache row, keyed to the membership-dataset stamp the warm-up wrote under.
        assert len(rows) == 1, f"expected exactly one warmed cache row, got {len(rows)}"
        assert rows[0].dataset_version == version
        # the cached payload is byte-identical to a fresh compute over the same warmed DB.
        snapshot_dates = sorted(session.exec(select(ScannerRun.asof_date)).all())
        fresh = _membership_timeline(session, cfg, snapshot_dates)
        served = membership_timeline_cached(session, cfg, snapshot_dates)  # must HIT the warmed row
        assert served == fresh
        assert served["points"], "the warmed timeline has points (the cadence snapshots exist)"


def test_membership_timeline_cache_warm_failure_is_nonfatal(early_engine, monkeypatch, caplog):
    """A failure precomputing the membership-timeline cache during warm-up is CAUGHT + logged and does NOT
    flip an otherwise-successful warm-up to `failed` (the cadence snapshots + forward returns already
    succeeded). The warm-up settles `ok`, and a subsequent (real) `compute`/read still serves the bounded
    cold miss — the server is never left in a failed state by a cache-warm hiccup."""
    engine, cfg = early_engine
    ensure_latest_snapshot(engine, cfg)  # latest servable before the warm-up
    _clear_warmup_registry()
    warmup_mod._WARMUP_THREAD = None

    # force ONLY the membership-timeline precompute to raise (the cadence + forward-return steps succeed).
    def _boom(*_args, **_kwargs):
        raise RuntimeError("forced membership-timeline cache warm failure")

    monkeypatch.setattr(warmup_mod.data_manager, "membership_timeline_cached", _boom)
    with caplog.at_level("ERROR"):
        job_id = start_warmup(engine, cfg)
        _join_warmup(job_id)

    rec = data_manager.get_job(job_id)
    # the warm-up still settled OK (the cache-warm failure is non-fatal — it did not fail the job).
    assert rec is not None and rec["status"] == "ok"
    # the failure was logged honestly (not swallowed silently).
    assert any("membership-timeline cache warm failed" in r.message.lower() for r in caplog.records)
    # no stale/garbage cache row was written by the failed warm (the inner compute raised before persist).
    with Session(engine) as session:
        assert session.exec(select(MembershipTimelineCache)).all() == []

    # un-patch: a real read now serves the bounded cold miss and persists the cache (server recovers).
    monkeypatch.undo()
    with Session(engine) as session:
        snapshot_dates = sorted(session.exec(select(ScannerRun.asof_date)).all())
        served = membership_timeline_cached(session, cfg, snapshot_dates)
        assert served == _membership_timeline(session, cfg, snapshot_dates)
    _clear_warmup_registry()
    warmup_mod._WARMUP_THREAD = None


# ==================================================================================================
# ops-hardening iter-2 (J-05) — the coverage_snapshot boot-time safety net: a not-yet-ingested-once DB
# gets exactly one persisted coverage_snapshot row after the background warm-up finishes, computed
# strictly in this background thread (never on the boot/request path), idempotent, and non-fatal.
# ==================================================================================================
def test_warmup_precomputes_coverage_snapshot_if_missing(warmed_engine):
    """After the background warm-up finishes, a `CoverageSnapshot` row exists for the CURRENT (asof_key,
    dataset_version) stamp — the boot-time safety net for a not-yet-ingested-once DB, run strictly in this
    background warm-up thread (never blocking `yield`/serving). Byte-identical to a fresh
    `_compute_coverage_uncached` compute (a cache of the deterministic derivation, not a second
    computation)."""
    engine, cfg = warmed_engine["engine"], warmed_engine["cfg"]
    with Session(engine) as session:
        resolved_asof = data_manager._resolve_coverage_asof(session, None, cfg)
        version = data_manager._membership_dataset_version(session, cfg)
        rows = session.exec(select(CoverageSnapshot)).all()
        assert len(rows) == 1, f"expected exactly one warmed coverage_snapshot row, got {len(rows)}"
        assert rows[0].asof_key == resolved_asof.isoformat()
        assert rows[0].dataset_version == version
        fresh = data_manager._compute_coverage_uncached(session, cfg, as_of=None)
        stored = json.loads(rows[0].payload_json)
    assert stored == fresh


def test_warmup_coverage_snapshot_is_noop_when_already_present(early_engine):
    """The boot safety net is a no-op when a `coverage_snapshot` row already exists for the current stamp
    — it does not recompute/overwrite on every boot; only the ingest finalize hook refreshes it
    thereafter."""
    engine, cfg = early_engine
    ensure_latest_snapshot(engine, cfg)  # latest servable
    with Session(engine) as session:
        data_manager.refresh_coverage_snapshot(session, cfg)  # seed one row directly (a prior ingest)
        rows_before = session.exec(select(CoverageSnapshot)).all()
        assert len(rows_before) == 1
        computed_at_before = rows_before[0].computed_at

    warmup_mod._warm_coverage_snapshot(engine, cfg)  # the safety net — must see the row and no-op

    with Session(engine) as session:
        rows_after = session.exec(select(CoverageSnapshot)).all()
    assert len(rows_after) == 1
    assert rows_after[0].computed_at == computed_at_before  # untouched — no recompute


def test_warmup_coverage_snapshot_warm_failure_is_nonfatal(early_engine, monkeypatch, caplog):
    """A failure precomputing the coverage snapshot during warm-up is CAUGHT + logged and does NOT flip an
    otherwise-successful warm-up to `failed` (mirrors
    `test_membership_timeline_cache_warm_failure_is_nonfatal`)."""
    engine, cfg = early_engine
    ensure_latest_snapshot(engine, cfg)  # latest servable before the warm-up
    _clear_warmup_registry()
    warmup_mod._WARMUP_THREAD = None

    def _boom(*_args, **_kwargs):
        raise RuntimeError("forced coverage snapshot warm failure")

    monkeypatch.setattr(warmup_mod.data_manager, "refresh_coverage_snapshot", _boom)
    with caplog.at_level("ERROR"):
        job_id = start_warmup(engine, cfg)
        _join_warmup(job_id)

    rec = data_manager.get_job(job_id)
    # the warm-up still settled OK (the coverage-warm failure is non-fatal — it did not fail the job).
    assert rec is not None and rec["status"] == "ok"
    assert any("coverage snapshot warm failed" in r.message.lower() for r in caplog.records)
    # no stale/garbage row was written by the failed warm (the inner compute raised before persist).
    with Session(engine) as session:
        assert session.exec(select(CoverageSnapshot)).all() == []

    monkeypatch.undo()
    _clear_warmup_registry()
    warmup_mod._WARMUP_THREAD = None


def test_lifespan_serves_dashboard_200_while_warmup_in_flight(tmp_path_factory, monkeypatch):
    """The J-40 keystone integration proof named verbatim in goal.md acceptance: the SERVER is serving —
    the lifespan has yielded, the latest snapshot is present, `GET /api/dashboard` returns 200 and the
    readiness endpoint honestly reports `initializing` — WHILE the background cadence warm-up is still
    producing snapshots. The warm-up worker is held provably in-flight by a gate (deterministic, no
    sleeps): the synchronous boot's latest-snapshot step passes through to the real engine, but every
    background cadence date blocks until the test releases it. (Added by the iter-28 audit: the
    engine-level tests above prove each component; THIS test proves the composed lifespan behaviour at
    the HTTP layer, per the spec's "server serving while cadence snapshots ... are still being produced".)
    """
    from fastapi.testclient import TestClient

    import main as main_mod
    from app import db as db_module

    db_path = tmp_path_factory.mktemp("serving_db") / "serving.db"
    fresh_engine = make_engine(f"sqlite:///{db_path}")
    prev_engine = db_module.get_engine()
    _clear_warmup_registry()
    warmup_mod._WARMUP_THREAD = None

    release = threading.Event()
    real_run_scan = warmup_mod.run_scan

    def _gated_run_scan(session, asof, config=None):
        # the synchronous boot's SINGLE latest-snapshot step passes through to the canonical engine;
        # every background cadence date is HELD in-flight so the server is provably serving WHILE the
        # historical warm-up is still producing snapshots.
        if asof == latest_data_date(session):
            return real_run_scan(session, asof, config)
        if release.wait(timeout=120):
            raise RuntimeError("audit gate: cadence scan aborted after assertions (non-fatal path)")
        raise RuntimeError("audit gate: warm-up gate timed out")

    monkeypatch.setattr(warmup_mod, "run_scan", _gated_run_scan)
    db_module.set_engine(fresh_engine)
    try:
        # Entering the TestClient runs the REAL lifespan against the fresh DB: config -> tables -> seed
        # -> ensure_latest_snapshot (one real scan) -> start_warmup (its worker blocks on the gate).
        with TestClient(main_mod.app) as client:
            # the lifespan HAS yielded and the warm-up worker is alive + held mid-cadence
            live = [t for t in threading.enumerate() if t.name == f"warmup-{WARMUP_JOB_ID}"]
            assert len(live) == 1

            health = client.get("/api/health")
            assert health.status_code == 200
            body = health.json()
            # honest readiness WHILE warming: initializing (never `ready`, never `unavailable`)
            assert body["readiness"] == "initializing"
            assert body["warmup"]["total"] > 0
            assert body["warmup"]["done"] < body["warmup"]["total"]

            # the core read page serves the LATEST as-of snapshot while the cadence is still warming
            dash = client.get("/api/dashboard")
            assert dash.status_code == 200
            assert dash.json()["regime"]["asof_date"] == body["seed_latest_date"]
    finally:
        release.set()  # unblock the held worker (it aborts via the non-fatal path and settles)
        _join_warmup(WARMUP_JOB_ID)
        _clear_warmup_registry()
        warmup_mod._WARMUP_THREAD = None
        db_module.set_engine(prev_engine)


# ==================================================================================================
# Invariant — only the SCHEDULING moved: re-running the OLD synchronous path mutates / inserts nothing
# ==================================================================================================
def test_scheduling_change_only_old_synchronous_path_is_a_noop(warmed_engine):
    """Only the SCHEDULING moved (not the values): re-running the OLD synchronous boot path
    (`bootstrap_runs` + `backfill_forward_returns`) on the warmed DB inserts ZERO new rows and changes no
    counts — proving the background warm-up already produced EXACTLY what the synchronous path would have
    (the engines + their byte-identical outputs are unchanged; only when they run moved). Idempotent +
    immutable (anti-goal: Snapshots are immutable)."""
    engine, cfg = warmed_engine["engine"], warmed_engine["cfg"]
    with Session(engine) as session:
        before = _counts(session)
        result_fp_before = _result_fingerprint(session)
        fr_fp_before = _forward_return_fingerprint(session)

    # the OLD synchronous path, re-run on the already-warmed DB
    bootstrap_runs(engine, cfg)
    second = backfill_forward_returns(engine, cfg)
    assert second["rows_inserted"] == 0  # nothing new — the warm-up already produced it all

    with Session(engine) as session:
        assert _counts(session) == before  # no new runs / results / sector / theme / forward-return rows
        assert _result_fingerprint(session) == result_fp_before  # snapshot rows byte-identical
        assert _forward_return_fingerprint(session) == fr_fp_before  # forward returns byte-identical


# ==================================================================================================
# J-41 — concurrency-safe create (the create-between-check-and-insert race), fast EARLY date
# ==================================================================================================
def test_run_scan_concurrency_safe_returns_existing_no_duplicate(early_engine):
    """Simulate the create-between-check-and-insert race for the SAME as-of date: two independent
    sessions each pass the `get_run_for_date` existence check (both see None), then both INSERT + commit.
    Exactly ONE snapshot ends up stored, the second commit's duplicate is rolled back and the existing
    immutable row is returned — no `UNIQUE constraint failed: scanner_runs.asof_date`, no duplicate row,
    no overwrite (anti-goal: Snapshots are immutable; J-41)."""
    engine, cfg = early_engine
    s1 = Session(engine)
    s2 = Session(engine)
    try:
        assert get_run_for_date(s1, EARLY) is None
        assert get_run_for_date(s2, EARLY) is None  # both see the race precondition: no existing run
        run1 = run_scan(s1, EARLY, cfg)  # winner commits first
        run2 = run_scan(s2, EARLY, cfg)  # loser hits the IntegrityError guard -> returns the existing row
        assert run1.asof_date == EARLY and run2.asof_date == EARLY
    finally:
        s1.close()
        s2.close()

    with Session(engine) as session:
        n = session.scalar(
            select(func.count()).select_from(ScannerRun).where(ScannerRun.asof_date == EARLY)
        )
        assert n == 1  # the race produced no duplicate


def test_concurrent_run_scan_threads_no_unique_crash(early_engine):
    """The race under REAL threads: several threads call `run_scan` for the same as-of date at once. None
    raises `IntegrityError`, and exactly one snapshot is stored. Proves the catch-on-commit guard, not
    just the single-process check-then-return idempotency."""
    engine, cfg = early_engine
    errors: list[Exception] = []
    barrier = threading.Barrier(3)

    def worker():
        try:
            barrier.wait()
            with Session(engine) as session:
                run_scan(session, EARLY, cfg)
        except Exception as exc:  # capture any UNIQUE-constraint crash
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == [], f"concurrent run_scan crashed: {errors!r}"
    with Session(engine) as session:
        n = session.scalar(
            select(func.count()).select_from(ScannerRun).where(ScannerRun.asof_date == EARLY)
        )
        assert n == 1


def test_forward_returns_concurrent_insert_idempotent_no_duplicate(early_engine):
    """A concurrent / repeated forward-returns INSERT is idempotent + concurrency-safe (J-41): after one
    backfill populates the rows for the early snapshot, a second backfill inserts nothing, crashes on no
    UNIQUE constraint, and leaves exactly one row per (run, symbol, horizon) key."""
    engine, cfg = early_engine
    with Session(engine) as session:
        run_scan(session, EARLY, cfg)  # one snapshot to attach forward returns to
    first = backfill_forward_returns(engine, cfg)
    assert first["rows_inserted"] > 0
    second = backfill_forward_returns(engine, cfg)  # the idempotent re-run
    assert second["rows_inserted"] == 0

    with Session(engine) as session:
        rows = session.exec(select(ForwardReturn)).all()
        keys = [(r.run_id, r.symbol, r.horizon) for r in rows]
        assert len(keys) == len(set(keys))  # no duplicate key


# ==================================================================================================
# J-41 — non-fatal warm-up failure (forced-raise; fast because no real cadence scan runs)
# ==================================================================================================
def test_warmup_failure_is_caught_logged_and_nonfatal(early_engine, monkeypatch, caplog):
    """A background warm-up that raises is CAUGHT + logged + marked `failed` — it never propagates out of
    the worker (non-fatal). The latest snapshot stays servable, readiness reports the failure honestly
    (initializing, NOT a silent ready/green), and a SUBSEQUENT (real) warm-up completes the idempotent
    remainder -> ready (J-41)."""
    engine, cfg = early_engine
    ensure_latest_snapshot(engine, cfg)  # latest servable before the warm-up
    _clear_warmup_registry()

    # force the cadence step to raise inside the worker (no slow real scan runs → fast test)
    def _boom(session, asof, config=None):
        raise RuntimeError("forced warm-up failure")

    monkeypatch.setattr(warmup_mod, "run_scan", _boom)
    with caplog.at_level("ERROR"):
        job_id = start_warmup(engine, cfg)
        _join_warmup(job_id)

    rec = data_manager.get_job(job_id)
    assert rec is not None and rec["status"] == "failed"
    assert any("forced warm-up failure" in e for e in rec["errors"])
    assert any("warm-up failed" in r.message.lower() for r in caplog.records)  # logged, not swallowed

    # the latest snapshot is still servable and the read path still works (server kept serving)
    with Session(engine) as session:
        latest = latest_data_date(session)
        assert get_run_for_date(session, latest) is not None
        r_failed = compute_readiness(session, engine=engine, config=cfg)
    # honest: not ready (warm-up failed / incomplete), and NOT mislabeled unavailable
    assert r_failed["state"] == "initializing"

    # un-patch and run the warm-up again (the next boot) — it completes the idempotent remainder -> ready
    monkeypatch.undo()
    _clear_warmup_registry()
    job_id2 = start_warmup(engine, cfg)
    _join_warmup(job_id2)
    with Session(engine) as session:
        r_ok = compute_readiness(session, engine=engine, config=cfg)
    assert r_ok["state"] == "ready"
    _clear_warmup_registry()


def test_start_warmup_is_single_flight_no_duplicate_concurrent_worker(early_engine, monkeypatch):
    """J-41 re-spawn resilience + the iter-28 QA-gate fix: while a warm-up is RUNNING in-process, a
    re-invocation of `start_warmup` (a readiness-probe re-spawn, a `--reload` double-fire, or every
    repeated `TestClient(main.app)` lifespan entry over the shared test DB) MUST NOT spawn a second
    concurrent daemon worker — it returns the existing job id, leaving exactly ONE warm-up thread alive.
    Without this guard, N TestClient entries spawned N concurrent warm-ups all writing the one SQLite DB,
    the root cause of the non-deterministic API-suite failures + the multi-minute write-contention crawl."""
    engine, cfg = early_engine
    ensure_latest_snapshot(engine, cfg)  # latest servable before the warm-up
    _clear_warmup_registry()
    warmup_mod._WARMUP_THREAD = None  # clean single-flight state for this test

    # Gate the worker so it stays RUNNING until we release it — guarantees the re-invocations below race a
    # live warm-up (deterministic, no sleeps). The first run_scan blocks on the gate; the guard must hold.
    release = threading.Event()
    real_run_scan = warmup_mod.run_scan
    call_count = {"n": 0}

    def _gated_run_scan(session, asof, config=None):
        call_count["n"] += 1
        release.wait(timeout=30)  # block the worker so it is alive while we re-invoke start_warmup
        return real_run_scan(session, asof, config)

    monkeypatch.setattr(warmup_mod, "run_scan", _gated_run_scan)
    try:
        job_id = start_warmup(engine, cfg)        # spawns the (single) warm-up; its worker is now blocked
        # re-invoke repeatedly while the first warm-up is still alive — each is a single-flight no-op.
        ids = {start_warmup(engine, cfg) for _ in range(5)}
        assert ids == {job_id}                    # every re-invocation returned the SAME existing job id
        live = [t for t in threading.enumerate() if t.name == f"warmup-{WARMUP_JOB_ID}"]
        assert len(live) == 1                     # exactly ONE warm-up thread alive — no duplicate spawned
    finally:
        release.set()                             # let the single worker finish
        _join_warmup(job_id)

    # after the worker has SETTLED, a fresh boot's start_warmup is allowed again (idempotent remainder).
    monkeypatch.undo()
    _clear_warmup_registry()
    warmup_mod._WARMUP_THREAD = None
    job_id2 = start_warmup(engine, cfg)
    assert job_id2 == WARMUP_JOB_ID
    _join_warmup(job_id2)
    _clear_warmup_registry()
    warmup_mod._WARMUP_THREAD = None


def test_readiness_unavailable_on_empty_db(tmp_path_factory):
    """An error case: a DB with NO price data (and no snapshot) reports `unavailable` — never a fabricated
    `ready` (anti-goal: No fabricated data / Readiness is reported honestly)."""
    cfg = _fast_cfg()
    db_path = tmp_path_factory.mktemp("empty_db") / "empty.db"
    engine = make_engine(f"sqlite:///{db_path}")
    create_db_and_tables(engine)  # tables but NO seed
    _clear_warmup_registry()
    with Session(engine) as session:
        r = compute_readiness(session, engine=engine, config=cfg)
    assert r["state"] == "unavailable"
    assert r["warmup"]["done"] == 0 and r["warmup"]["total"] == 0


# --------------------------------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------------------------------
def _counts(session: Session) -> dict:
    return {
        "runs": session.scalar(select(func.count()).select_from(ScannerRun)),
        "results": session.scalar(select(func.count()).select_from(ScannerResult)),
        "sector_scores": session.scalar(select(func.count()).select_from(SectorScoreRow)),
        "theme_scores": session.scalar(select(func.count()).select_from(ThemeScoreRow)),
        "forward_returns": session.scalar(select(func.count()).select_from(ForwardReturn)),
    }


def _result_fingerprint(session: Session) -> dict:
    """Content-only fingerprint of every scanner_result, keyed by (as-of date, ticker) — excludes auto
    PKs / run_id FKs, so it is independent of insertion order / which scheduling produced it."""
    runs = {r.id: r.asof_date.isoformat() for r in session.exec(select(ScannerRun)).all()}
    results = session.exec(select(ScannerResult)).all()
    return {(runs[r.run_id], r.ticker): r.record_json for r in results}


def _forward_return_fingerprint(session: Session) -> dict:
    """Content-only fingerprint of every forward_return, keyed by (as-of date, symbol, horizon)."""
    runs = {r.id: r.asof_date.isoformat() for r in session.exec(select(ScannerRun)).all()}
    frs = session.exec(select(ForwardReturn)).all()
    return {
        (runs[fr.run_id], fr.symbol, fr.horizon): (
            fr.entry_close, fr.realized_return, fr.measured_date.isoformat(), fr.mae, fr.mfe
        )
        for fr in frs
    }


# ==================================================================================================
# ops-hardening iter-46 FIX PASS (QA blockers 3 — J-06 / J-07) — the evidence (per-claim
# drawdown-expectations) cache boot warm.
#
# WHAT THE QA RUN MEASURED: `GET /api/evidence` did not return inside a 300s budget, both in isolation
# (UT-J-06 step 7) and under concurrent load (UT-J-07). The dev handoff and the QA report both attributed
# this to GIL contention from a concurrent backfill's finalize tail.
#
# THAT ATTRIBUTION WAS WRONG, and this fix pass measured it directly: on a FULLY IDLE, freshly-restarted
# backend with no ingest job running at all, a cold `GET /api/evidence` took **163.3s** (HTTP 200, 100%
# CPU, one runnable thread, ~1 GB RSS — never a memory problem). Immediately afterwards the SAME endpoint
# served in **11-52ms**. So the endpoint is not slow; its COLD MISS is expensive, and the committed budget
# (`reports/perf-budgets.md` Item I) is explicitly the WARM steady-state one (≤3s).
#
# ROOT CAUSE: the per-claim `drawdown_expectations` EventStudyCache is warmed by the INGEST finalize tail
# (`data_manager._refresh_ingest_aggregates`) but NOT by the boot warm-up — so every backend restart left
# the first `/evidence` viewer paying the full 7-claim cold compute synchronously, on the request path.
# The QA run restarted the backend immediately before the browser sweep, which is exactly why it hit it.
#
# THE FIX MIRRORS THE TWO WARM STEPS ALREADY BESIDE IT (`_warm_membership_timeline`, iter-36;
# `_warm_coverage_snapshot`, iter-2): own session on the engine, idempotent (a cache HIT is a cheap no-op),
# NON-FATAL, and — critically — sequenced AFTER the warm-up record reaches `ok` so the readiness badge
# (J-04, and J-07 step 1's "Ready") is never delayed by it.
# ==================================================================================================
def _stub_ledger(monkeypatch, entries):
    """Pin the ledger the warm loop iterates — the committed ledger's real contents are not the subject
    of these proofs, only which of its entries get warmed."""
    monkeypatch.setattr(warmup_mod, "read_entries", lambda _path: entries)
    monkeypatch.setattr(warmup_mod.evidence, "resolve_ledger_path", lambda *_a, **_k: "unused.jsonl")


def test_warmup_warms_every_ledger_claim_and_skips_forward_walk_records(early_engine, monkeypatch):
    """The boot warm must warm the SAME per-claim cache `GET /api/evidence` looks up lazily — once per
    ORIGINAL claim — and must skip `forward_walk` MONITORING records, applying the exact filter
    `build_evidence_payload` and the ingest finalize tail already apply (a forward-walk record re-scores an
    existing claim; it is not itself a claim with a panel to warm)."""
    engine, cfg = early_engine
    claim_a = {"signal": "claim-a", "horizon": 20}
    claim_b = {"signal": "claim-b", "horizon": 60}
    _stub_ledger(monkeypatch, [
        {"type": "claim", "claim": claim_a},
        {"type": "forward_walk", "claim": {"signal": "monitoring-record", "horizon": 20}},
        {"type": "claim", "claim": claim_b},
        "a malformed non-dict ledger line",
    ])
    warmed: list[dict] = []
    monkeypatch.setattr(
        warmup_mod.forward_testing, "compute_drawdown_expectations_cached",
        lambda _session, claim, _cfg: warmed.append(claim) or {"by_phase": []},
    )

    warmup_mod._warm_drawdown_expectations(engine, cfg)

    assert warmed == [claim_a, claim_b], (
        "the boot warm must warm exactly the ORIGINAL claims, in ledger order, skipping forward-walk "
        f"monitoring records and malformed lines; warmed={warmed}"
    )


def test_warmup_drawdown_expectations_failure_is_nonfatal_on_textless_memoryerror(
    early_engine, monkeypatch, caplog
):
    """A `MemoryError` — raised TEXTLESS, the shape this session's honesty rule requires every new handler
    to be tested against (`str(MemoryError())` is `""`, so any handler that relies on the message degrades
    silently) — during the evidence warm is CAUGHT + logged and does NOT flip an otherwise-successful
    warm-up to `failed`. Mirrors the membership-timeline / coverage-snapshot non-fatal proofs above."""
    engine, cfg = early_engine
    ensure_latest_snapshot(engine, cfg)  # latest servable before the warm-up
    _clear_warmup_registry()
    warmup_mod._WARMUP_THREAD = None
    _stub_ledger(monkeypatch, [{"type": "claim", "claim": {"signal": "boom", "horizon": 20}}])

    def _boom(*_args, **_kwargs):
        raise MemoryError()  # TEXTLESS on purpose — see docstring

    monkeypatch.setattr(warmup_mod.forward_testing, "compute_drawdown_expectations_cached", _boom)
    with caplog.at_level("ERROR"):
        job_id = start_warmup(engine, cfg)
        _join_warmup(job_id)

    rec = data_manager.get_job(job_id)
    assert rec is not None and rec["status"] == "ok", (
        f"an evidence-cache warm failure must be non-fatal to the warm-up; record={rec}"
    )
    assert any(
        "drawdown-expectations" in r.message.lower() or "drawdown_expectations" in r.message.lower()
        for r in caplog.records
    ), (
        "the textless MemoryError must still be logged honestly (never swallowed silently); "
        f"captured={[r.message for r in caplog.records]}"
    )
    _clear_warmup_registry()
    warmup_mod._WARMUP_THREAD = None


# ==================================================================================================
# ops-hardening iter-47 (TC-6, carried from iter-44/45/46): `_warm_drawdown_expectations`'s two per-claim
# exception handlers (warmup.py:205 MemoryError, :212 generic Exception) called a BARE `logger.exception`
# — under the SAME exhausted `ulimit -v` cap that raised the original exception, rendering the full
# traceback can itself allocate and raise a SECOND exception that escapes the handler before
# `_release_process_memory()` runs (the module-wide isolation convention 19+ other sites already apply).
# These proofs are DIRECT: they monkeypatch `_log_isolation_failure` itself and assert it was invoked — a
# caplog text check cannot discriminate a guarded call from a bare one, because `_log_isolation_failure`
# ALSO calls `logger.exception` internally on its own happy path.
# ==================================================================================================
def test_warmup_drawdown_memoryerror_calls_log_isolation_failure_not_bare_exception(early_engine, monkeypatch):
    """TC-6 (warmup.py:205): the per-claim `MemoryError` handler calls `data_manager._log_isolation_failure`
    — proven directly, not inferred from a log message — on a TEXTLESS `MemoryError`
    (`str(MemoryError())` is `""`, this session's standing honesty rule for every new handler)."""
    engine, cfg = early_engine
    _stub_ledger(monkeypatch, [{"type": "claim", "claim": {"signal": "boom", "horizon": 20}}])

    def _boom(*_args, **_kwargs):
        raise MemoryError()  # TEXTLESS on purpose

    monkeypatch.setattr(warmup_mod.forward_testing, "compute_drawdown_expectations_cached", _boom)
    monkeypatch.setattr(warmup_mod.data_manager, "_release_process_memory", lambda: None)
    calls: list[tuple] = []
    monkeypatch.setattr(
        warmup_mod.data_manager, "_log_isolation_failure",
        lambda msg, *args, **kwargs: calls.append((msg, args)),
    )

    warmup_mod._warm_drawdown_expectations(engine, cfg)

    assert len(calls) == 1, f"expected exactly one _log_isolation_failure call, got {calls}"
    assert "memory pressure" in calls[0][0].lower(), calls[0]


def test_warmup_drawdown_generic_exception_calls_log_isolation_failure_not_bare_exception(
    early_engine, monkeypatch,
):
    """TC-6 (warmup.py:212): the per-claim GENERIC exception handler (one bad claim never blocks the
    others) also calls `data_manager._log_isolation_failure` — proven directly — and, unlike the
    `MemoryError` branch, must NOT abort the loop: a second, healthy claim after the failing one still
    warms."""
    engine, cfg = early_engine
    claim_bad = {"signal": "bad-claim", "horizon": 20}
    claim_good = {"signal": "good-claim", "horizon": 60}
    _stub_ledger(monkeypatch, [
        {"type": "claim", "claim": claim_bad},
        {"type": "claim", "claim": claim_good},
    ])

    warmed: list[dict] = []

    def _per_claim(_session, claim, _cfg):
        if claim is claim_bad:
            raise RuntimeError("boom")
        warmed.append(claim)
        return {"by_phase": []}

    monkeypatch.setattr(warmup_mod.forward_testing, "compute_drawdown_expectations_cached", _per_claim)
    calls: list[tuple] = []
    monkeypatch.setattr(
        warmup_mod.data_manager, "_log_isolation_failure",
        lambda msg, *args, **kwargs: calls.append((msg, args)),
    )

    warmup_mod._warm_drawdown_expectations(engine, cfg)

    assert len(calls) == 1, f"expected exactly one _log_isolation_failure call, got {calls}"
    assert "non-fatal" in calls[0][0].lower(), calls[0]
    assert warmed == [claim_good], "a generic per-claim failure must not block the NEXT claim from warming"


def test_warmup_evidence_warm_runs_only_after_readiness_reaches_ok(early_engine, monkeypatch):
    """SEQUENCING PROOF (protects J-04 and J-07 step 1): the evidence warm is expensive (163.3s measured
    live for 7 claims), so it must run strictly AFTER the warm-up record has settled `ok` — the readiness
    badge must flip `Ready` on exactly the same schedule as before this fix. Asserted by reading the job's
    OWN status at the moment the warm is invoked, never inferred from ordering in the source."""
    engine, cfg = early_engine
    ensure_latest_snapshot(engine, cfg)
    _clear_warmup_registry()
    warmup_mod._WARMUP_THREAD = None

    status_when_warmed: list[object] = []

    def _record_status(_engine, _cfg):
        rec = data_manager.get_job(WARMUP_JOB_ID)
        status_when_warmed.append(rec["status"] if rec else None)

    monkeypatch.setattr(warmup_mod, "_warm_drawdown_expectations", _record_status)
    job_id = start_warmup(engine, cfg)
    _join_warmup(job_id)

    assert status_when_warmed == ["ok"], (
        "the evidence warm must be invoked exactly once, and only after the warm-up already reported `ok` "
        "(otherwise it delays the readiness badge J-04/J-07 depend on); "
        f"status at warm time={status_when_warmed}"
    )
