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
