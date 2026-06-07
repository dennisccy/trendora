"""Data Manager engine — on-demand dataset growth (iter-3, J-17).

The named proofs, each guarding a critical anti-goal / DoD item:
  - coverage correctness        — price-range / symbol-count / snapshot-set / GAPS exact on a fixture.
  - backfill grows `n`          — a range backfill adds ScannerRun rows and raises the forward-test n.
  - lookahead-free + reuse      — a backfilled snapshot equals the canonical score_stocks(D) VERBATIM
                                  (no second scan math), and its forward returns use only bars > D.  *(No lookahead / Reuse)*
  - create-once / immutable     — re-running the same range creates 0 new snapshots, mutates no
                                  created_at, inserts 0 new forward returns; DataProviderRun is append-only. *(Snapshots immutable)*
  - config-driven limits        — the max-range guard reads config (no magic number in control code).
  - fetch forced-failure        — a failing provider writes ZERO bars / ZERO snapshots and a `failed`
                                  run; never a fabricated price.                                   *(Live fetch is real-data-only)*

The coverage / validation / forced-failure tests run on tiny in-memory data (fast). The realistic
backfill proof loads the committed seed and runs the real engines ONCE (module-scoped).
"""
from __future__ import annotations

import json
from datetime import date

import httpx
import pytest
from sqlalchemy import func
from sqlmodel import Session, select

from app.config import load_config
from app.db import create_db_and_tables, make_engine
from app.data_providers.base import Bar, PriceProvider, ProviderUnavailableError, RateLimitError
from app.engine import data_manager
from app.engine import forward_testing, scanner
from app.engine.data_manager import (
    JobProgress,
    _chunk_plan,
    _trading_days,
    compute_coverage,
    compute_provider_availability,
    create_job,
    get_job,
    recent_runs,
    resolve_provider_key,
    resumable_imports,
    resume_data_job,
    run_data_job,
    validate_job_request,
)
from app.engine.forward_testing import compute_forward_aggregates
from app.engine.scoring import score_stocks
from app.models import (
    DailyPrice,
    DataProviderRun,
    ForwardReturn,
    ImportCheckpoint,
    ScannerResult,
    ScannerRun,
)
from app.seed_loader import all_seed_symbols, load_seed


def _noop_sleep(_seconds: float) -> None:
    """A zero-wall-clock sleep injected into the chunked-fetch tests so the 429 backoff adds no real
    wait (MEMORY: backend-test-suite-runtime — never let a backoff balloon the suite)."""


# ==================================================================================================
# compute_coverage — read-only descriptive metadata (tiny hand-built DB, no engines)
# ==================================================================================================
@pytest.fixture()
def coverage_engine(tmp_path):
    """SPY bars on four dates (the trading calendar) + a stock on two of them, with ONE snapshot —
    so coverage's range / symbol-count / snapshot-set / gaps are all exact by construction."""
    engine = make_engine(f"sqlite:///{tmp_path / 'cov.db'}")
    create_db_and_tables(engine)
    spy_days = [date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4), date(2024, 1, 5)]
    with Session(engine) as session:
        for d in spy_days:
            session.add(DailyPrice(symbol="SPY", date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        for d in spy_days[:2]:
            session.add(DailyPrice(symbol="AAA", date=d, open=2.0, high=2.0, low=2.0, close=2.0, volume=2.0))
        # one snapshot on the 2nd trading day (the other three are gaps)
        session.add(
            ScannerRun(
                asof_date=spy_days[1], created_at=__import__("datetime").datetime(2024, 1, 3),
                provider="seed", benchmark="SPY", regime_score=50.0, regime_label="Choppy",
                regime_components_json="[]", new_high_low_json="{}", candidate_counts_json="{}",
            )
        )
        session.commit()
    return engine, spy_days


def test_compute_coverage_exact(coverage_engine):
    """Exact coverage: price range D1..D4, two symbols, one snapshot date, three gap trading days."""
    engine, spy_days = coverage_engine
    cfg = load_config()
    with Session(engine) as session:
        cov = compute_coverage(session, cfg)

    assert cov["price_start"] == spy_days[0].isoformat()
    assert cov["price_end"] == spy_days[3].isoformat()
    assert cov["symbol_count"] == 2  # SPY + AAA
    assert cov["snapshot_count"] == 1
    assert cov["snapshot_dates"] == [spy_days[1].isoformat()]
    assert cov["trading_day_count"] == 4  # SPY defines the calendar
    # gaps = the trading days without a snapshot = D1, D3, D4 (D2 has the snapshot)
    assert cov["gap_count"] == 3
    assert cov["gap_first"] == spy_days[0].isoformat()
    assert cov["gap_last"] == spy_days[3].isoformat()
    assert cov["gaps_preview"] == [spy_days[0].isoformat(), spy_days[2].isoformat(), spy_days[3].isoformat()]


def test_compute_coverage_gap_preview_capped_by_config(coverage_engine):
    """The gap preview length is bounded by `config.data_manager.gap_preview` (no magic cap in code)."""
    engine, _ = coverage_engine
    cfg = load_config()
    cfg = cfg.model_copy(update={"data_manager": cfg.data_manager.model_copy(update={"gap_preview": 1})})
    with Session(engine) as session:
        cov = compute_coverage(session, cfg)
    assert cov["gap_count"] == 3  # the true count is unaffected
    assert len(cov["gaps_preview"]) == 1  # only the preview is capped


def test_compute_coverage_empty_db_is_all_none():
    """An empty DB reports null range / zero counts — never a fabricated coverage figure."""
    engine = make_engine("sqlite:///:memory:")
    create_db_and_tables(engine)
    with Session(engine) as session:
        cov = compute_coverage(session, load_config())
    assert cov["price_start"] is None and cov["price_end"] is None
    assert cov["symbol_count"] == 0 and cov["snapshot_count"] == 0
    assert cov["trading_day_count"] == 0 and cov["gap_count"] == 0


# ==================================================================================================
# validate_job_request — config-driven limits + explicit rejection (the API maps these to 4xx)
# ==================================================================================================
def test_validate_job_request_reads_config_max_range():
    """The max-range guard reads `config.data_manager.max_range_days` — shrinking it rejects a span that
    was previously allowed (no magic range literal in control code)."""
    cfg = load_config()
    small = cfg.model_copy(
        update={"data_manager": cfg.data_manager.model_copy(update={"max_range_days": 3})}
    )
    validate_job_request("backfill", date(2024, 1, 1), date(2024, 1, 3), small)  # exactly 3 days — ok
    with pytest.raises(ValueError):
        validate_job_request("backfill", date(2024, 1, 1), date(2024, 1, 10), small)  # 10 > 3


def test_validate_job_request_rejects_inverted_and_unknown():
    cfg = load_config()
    with pytest.raises(ValueError):
        validate_job_request("backfill", date(2024, 1, 10), date(2024, 1, 1), cfg)  # start > end
    with pytest.raises(ValueError):
        validate_job_request("teleport", date(2024, 1, 1), date(2024, 1, 2), cfg)  # unknown kind


# ==================================================================================================
# Fetch forced-failure — real-data-only: zero fabricated bars / snapshots, an explicit failed run
# ==================================================================================================
class _FailingProvider(PriceProvider):
    """A live provider that is unavailable for every symbol (mirrors an offline / rate-limited Stooq)."""

    def get_daily(self, symbol, start=None, end=None):
        raise ProviderUnavailableError(f"forced failure for {symbol}")


def test_fetch_forced_failure_writes_no_bars_or_snapshots(tmp_path):
    """A fetch job whose provider fails for every symbol ends `failed` with an explicit error and writes
    ZERO `DailyPrice` rows and ZERO snapshots — never a fabricated price (anti-goal: real-data-only)."""
    cfg = load_config()
    engine = make_engine(f"sqlite:///{tmp_path / 'fetch_fail.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        for d in (date(2024, 1, 2), date(2024, 1, 3)):  # a little SPY data so a calendar exists
            session.add(DailyPrice(symbol="SPY", date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        session.commit()
        prices_before = session.scalar(select(func.count()).select_from(DailyPrice))
        runs_before = session.scalar(select(func.count()).select_from(ScannerRun))

    job = create_job("fetch", date(2024, 1, 2), date(2024, 1, 31))
    summary = run_data_job(job.job_id, config=cfg, engine=engine, provider=_FailingProvider())

    assert summary["status"] == "failed"
    assert summary["symbols_total"] == len(all_seed_symbols(cfg))
    assert summary["symbols_failed"] == summary["symbols_total"] and summary["symbols_ok"] == 0
    assert summary["bars_fetched"] == 0 and summary["snapshots_created"] == 0
    assert summary["errors"]  # explicit per-symbol failure messages

    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(DailyPrice)) == prices_before  # no fabricated bars
        assert session.scalar(select(func.count()).select_from(ScannerRun)) == runs_before  # no snapshots
        dpr = session.exec(select(DataProviderRun).order_by(DataProviderRun.id.desc())).first()
    assert dpr is not None and dpr.status == "failed"  # the failure is recorded honestly


# ==================================================================================================
# Backfill on the real seed — grows n, lookahead-free, create-once/immutable (module-scoped, once)
# ==================================================================================================
@pytest.fixture(scope="module")
def backfilled_job(tmp_path_factory):
    """Load the seed, create one baseline run (so n_before > 0), run a backfill JOB over a 3-date range
    of older trading days, capture before/after facts, then run the SAME job again for idempotency."""
    cfg = load_config()
    db_path = tmp_path_factory.mktemp("dm_seed") / "dm.db"
    engine = make_engine(f"sqlite:///{db_path}")
    create_db_and_tables(engine)
    load_seed(engine, cfg)

    with Session(engine) as session:
        trading = _trading_days(session, cfg)
    assert len(trading) > 320, "seed should provide a long trading calendar"
    base_date = trading[300]
    r_start, r_end = trading[305], trading[307]
    in_range = [d for d in trading if r_start <= d <= r_end]  # the gap dates the job will create
    horizon = cfg.walk_forward.default_horizon

    # baseline: one pre-existing run + its forward returns (the n_before reference)
    with Session(engine) as session:
        base_run = scanner.run_scan(session, base_date, cfg)
        forward_testing.backfill_run_forward_returns(session, base_run, cfg)
        n_before = compute_forward_aggregates(session, horizon, cfg)["overall"]["n"]
        runs_before = session.scalar(select(func.count()).select_from(ScannerRun))
        dpr_before = session.scalar(select(func.count()).select_from(DataProviderRun))

    # FIRST job over the range (synchronous — deterministic)
    job1 = create_job("backfill", r_start, r_end)
    summary1 = run_data_job(job1.job_id, config=cfg, engine=engine)

    with Session(engine) as session:
        n_after = compute_forward_aggregates(session, horizon, cfg)["overall"]["n"]
        runs_after = session.scalar(select(func.count()).select_from(ScannerRun))
        dpr_after = session.scalar(select(func.count()).select_from(DataProviderRun))
        created = {}
        for d in in_range:
            run = scanner.get_run_for_date(session, d)
            results = session.exec(
                select(ScannerResult).where(ScannerResult.run_id == run.id).order_by(ScannerResult.rank)
            ).all()
            frs = session.exec(select(ForwardReturn).where(ForwardReturn.run_id == run.id)).all()
            created[d] = {
                "id": run.id,
                "created_at": run.created_at,
                "records": [r.record_json for r in results],
                "fr_lookahead_ok": all(fr.measured_date > d and fr.asof_date == d for fr in frs),
                "fr_count": len(frs),
            }
        # canonical equality: the backfilled snapshot's stored Leadership == a fresh score_stocks(d0)
        d0 = in_range[0]
        live_lead = {row["ticker"]: row["leadership"]["score"] for row in score_stocks(session, d0, cfg)["rows"]}
        stored_lead = {
            r.ticker: r.leadership_score
            for r in session.exec(select(ScannerResult).where(ScannerResult.run_id == created[d0]["id"])).all()
        }

    # SECOND identical job — create-once / idempotent
    with Session(engine) as session:
        runs_pre2 = session.scalar(select(func.count()).select_from(ScannerRun))
        fr_pre2 = session.scalar(select(func.count()).select_from(ForwardReturn))
    job2 = create_job("backfill", r_start, r_end)
    summary2 = run_data_job(job2.job_id, config=cfg, engine=engine)
    with Session(engine) as session:
        runs_post2 = session.scalar(select(func.count()).select_from(ScannerRun))
        fr_post2 = session.scalar(select(func.count()).select_from(ForwardReturn))
        dpr_post2 = session.scalar(select(func.count()).select_from(DataProviderRun))
        created_at_recheck = {d: scanner.get_run_for_date(session, d).created_at for d in in_range}

    return {
        "in_range": in_range, "horizon": horizon,
        "n_before": n_before, "n_after": n_after,
        "runs_before": runs_before, "runs_after": runs_after,
        "dpr_before": dpr_before, "dpr_after": dpr_after, "dpr_post2": dpr_post2,
        "summary1": summary1, "summary2": summary2,
        "created": created, "live_lead": live_lead, "stored_lead": stored_lead,
        "runs_pre2": runs_pre2, "runs_post2": runs_post2,
        "fr_pre2": fr_pre2, "fr_post2": fr_post2,
        "created_at_recheck": created_at_recheck,
    }


def test_backfill_grows_n_and_adds_runs(backfilled_job):
    """The forward-test sample size grows and the expected ScannerRun rows are added (the J-17 crux:
    new dates appear + System Health n rises)."""
    f = backfilled_job
    assert f["n_after"] > f["n_before"]  # the forward-test evidence base grew
    assert f["runs_after"] == f["runs_before"] + len(f["in_range"])  # one new immutable run per gap date
    assert f["summary1"]["dates_total"] == len(f["in_range"])
    assert f["summary1"]["dates_done"] == len(f["in_range"])
    assert f["summary1"]["snapshots_created"] == len(f["in_range"])
    assert f["summary1"]["forward_returns_inserted"] > 0
    assert f["summary1"]["status"] == "ok"


def test_backfill_is_lookahead_free_and_reuses_canonical(backfilled_job):
    """The backfilled snapshot equals the canonical score_stocks(D) VERBATIM (no second scan math), and
    every realized forward return for the run uses only bars with date > D (the entry is on D)."""
    f = backfilled_job
    assert f["stored_lead"] == f["live_lead"]  # single-source: stored == fresh canonical computation
    assert f["stored_lead"]  # not vacuously empty
    for d, info in f["created"].items():
        assert info["fr_lookahead_ok"], f"forward returns for {d} must use only bars > D"
        assert info["fr_count"] > 0  # older dates have a full forward window


def test_backfill_create_once_immutable(backfilled_job):
    """Re-running the SAME range is a no-op: 0 new snapshots, unchanged run/forward-return counts, and
    every created_at is byte-identical (a snapshot is never overwritten — anti-goal: Snapshots immutable)."""
    f = backfilled_job
    assert f["summary2"]["snapshots_created"] == 0
    assert f["summary2"]["dates_total"] == 0  # nothing left to backfill in the range
    assert f["runs_post2"] == f["runs_pre2"]  # no new runs created by the second job
    assert f["fr_post2"] == f["fr_pre2"]  # no new forward returns inserted by the second job
    for d, info in f["created"].items():
        assert f["created_at_recheck"][d] == info["created_at"]  # created_at never mutated


def test_dataprovider_run_is_append_only_per_job(backfilled_job):
    """Each job appends exactly one DataProviderRun row (append-only); none are overwritten."""
    f = backfilled_job
    assert f["dpr_after"] == f["dpr_before"] + 1  # first job appended one row
    assert f["dpr_post2"] == f["dpr_after"] + 1  # second job appended one more
    runs = recent_runs  # the history reader exists and is importable
    assert callable(runs)


# ==================================================================================================
# iter-21 (J-33): import-source catalog availability (env-detected) — descriptive metadata, NO key
# ==================================================================================================
def test_compute_provider_availability_env_detected(monkeypatch):
    """A no-key source is always `available`; a needs-key source is `available` ONLY when its env var is
    set. The env VALUE / any key is NEVER in the output — only the env-var NAME + the boolean + a reason
    (anti-goal: Import keys are env-or-session, never persisted)."""
    cfg = load_config()
    # No env keys set → yahoo available (no key), tiingo NOT available (needs key, env unset).
    monkeypatch.delenv("TIINGO_API_KEY", raising=False)
    sources = compute_provider_availability(cfg)
    by_id = {s["id"]: s for s in sources}
    assert by_id["yahoo"]["available"] is True and by_id["yahoo"]["needs_key"] is False
    assert by_id["tiingo"]["available"] is False and by_id["tiingo"]["needs_key"] is True
    assert by_id["tiingo"]["env_var"] == "TIINGO_API_KEY"  # the NAME is exposed
    # the catalog is config-driven (the named sources appear)
    assert {"yahoo", "tiingo", "stooq"}.issubset(set(by_id))

    # Set the env var → tiingo flips to available, but the secret VALUE never appears in the output.
    monkeypatch.setenv("TIINGO_API_KEY", "super-secret-env-value-zzz")
    sources2 = compute_provider_availability(cfg)
    by_id2 = {s["id"]: s for s in sources2}
    assert by_id2["tiingo"]["available"] is True
    assert "super-secret-env-value-zzz" not in json.dumps(sources2)


def test_resolve_provider_key_prefers_paste_then_env(monkeypatch):
    """The effective key is the pasted session key if present, else the env var; a no-key source returns
    None and ignores any pasted value (the key is request-only — never written anywhere)."""
    cfg = load_config()
    yahoo = cfg.data_manager.provider_by_id("yahoo")
    tiingo = cfg.data_manager.provider_by_id("tiingo")
    assert resolve_provider_key(yahoo, "ignored") is None  # no-key source never uses a key
    monkeypatch.delenv("TIINGO_API_KEY", raising=False)
    assert resolve_provider_key(tiingo, None) is None  # needs key, none available
    assert resolve_provider_key(tiingo, "pasted-key") == "pasted-key"  # paste wins
    monkeypatch.setenv("TIINGO_API_KEY", "env-key")
    assert resolve_provider_key(tiingo, None) == "env-key"  # env fallback
    assert resolve_provider_key(tiingo, "pasted-key") == "pasted-key"  # paste still wins over env


# ==================================================================================================
# iter-21 (J-33) PRINCIPAL ANTI-GOAL: a pasted api_key is NEVER persisted / logged / echoed
# ==================================================================================================
class _RecordingOkProvider(PriceProvider):
    """An injected live provider that returns one real bar per symbol (a successful offline fetch)."""

    def get_daily(self, symbol, start=None, end=None):
        return [Bar(date=start or date(2024, 1, 2), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0)]


def test_pasted_api_key_never_persisted(tmp_path, caplog):
    """Run a FETCH job (injected provider) with a pasted session `api_key` against a needs-key source.
    The key string MUST be absent from the in-memory job snapshot, from every `DataProviderRun` column,
    and from the logs; the chosen `source` id (not secret) IS recorded. The `JobProgress` record has NO
    field that could hold the key. THE principal anti-goal: Import keys are env-or-session, never
    persisted."""
    secret = "sk-PASTE-NEVER-PERSIST-7f3a9c"
    cfg = load_config()
    engine = make_engine(f"sqlite:///{tmp_path / 'key.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        session.add(DailyPrice(symbol="SPY", date=date(2024, 1, 2), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        session.commit()

    job = create_job("fetch", date(2024, 1, 2), date(2024, 1, 3), source="tiingo")
    with caplog.at_level("DEBUG"):
        summary = run_data_job(
            job.job_id, config=cfg, engine=engine, provider=_RecordingOkProvider(), api_key=secret
        )

    # the chosen source is recorded (not secret); the key is nowhere in the job snapshot
    assert summary["source"] == "tiingo"
    assert summary["status"] == "ok"
    assert secret not in json.dumps(summary)
    assert secret not in json.dumps(recent_runs.__doc__ or "")  # sanity: not a constant somewhere

    # structural guarantee: the in-memory job record has NO field that holds a key
    assert "api_key" not in JobProgress.__dataclass_fields__

    # absent from every DataProviderRun column (provider == the source id, message == key-free detail JSON)
    with Session(engine) as session:
        rows = session.exec(select(DataProviderRun)).all()
    assert rows and rows[-1].provider == "tiingo"  # source id recorded, not the key
    serialized = json.dumps([
        {col: str(getattr(r, col)) for col in ("provider", "status", "message")} for r in rows
    ])
    assert secret not in serialized

    # absent from the logs
    assert secret not in caplog.text


# ==================================================================================================
# iter-22 (J-33 fix): the key is scrubbed even from a REAL-httpx-error string that slipped past _http
# ==================================================================================================
def _real_httpx_error_str_with_key(key: str) -> str:
    """A REAL `httpx.HTTPStatusError` str (from `raise_for_status`) whose request URL carries `key` as a
    `?token=` query param — the EXACT iter-21 leak vector (`str(exc)` embeds the key). Built from a real
    `httpx.Request`/`httpx.Response` directly (no `client.get`, so httpx emits no transport-level request
    log of its own — keeping this a test of OUR scrub, not the httpx library's logging)."""
    req = httpx.Request("GET", "https://api.tiingo.com/tiingo/daily/AAPL/prices", params={"token": key})
    try:
        httpx.Response(429, request=req).raise_for_status()
    except httpx.HTTPStatusError as exc:
        return str(exc)
    return ""  # pragma: no cover


class _KeyLeakingProvider(PriceProvider):
    """An injected provider that (like iter-21's un-redacted `_http.py`) raises a
    `ProviderUnavailableError` whose message EMBEDS a real httpx error str carrying the key in the URL.
    The `data_manager` defense-in-depth scrub MUST still remove the key before it reaches any error
    surface — belt-and-suspenders on top of the `_http.py` redaction."""

    def __init__(self, key: str):
        self._leak = _real_httpx_error_str_with_key(key)

    def get_daily(self, symbol, start=None, end=None):
        raise ProviderUnavailableError(self._leak)


def test_real_httpx_error_key_scrubbed_end_to_end(tmp_path, caplog):
    """EXTENDS `test_pasted_api_key_never_persisted` (iter-2 lesson: extend invariant tests, never
    delete): a FETCH whose injected provider raises an error EMBEDDING a real httpx error with the key in
    the URL → the data_manager scrub removes it. The sentinel is ABSENT from `JobProgress.errors`,
    `GET /api/data/jobs/{id}`, the `ImportCheckpoint` row + `resumable_imports`, every `DataProviderRun`
    column, and the logs — while the redaction marker `***` proves the scrub fired."""
    secret = "sk-REAL-HTTPX-SCRUB-5b2e1f"
    assert secret in _real_httpx_error_str_with_key(secret)  # sanity: there IS a key to scrub
    cfg = load_config()
    engine = make_engine(f"sqlite:///{tmp_path / 'scrub.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        session.add(DailyPrice(symbol="SPY", date=date(2024, 1, 2), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        session.commit()

    job = create_job("fetch", date(2024, 1, 2), date(2024, 1, 3), source="tiingo")
    with caplog.at_level("DEBUG"):
        summary = run_data_job(
            job.job_id, config=cfg, engine=engine,
            provider=_KeyLeakingProvider(secret), api_key=secret, sleep_fn=_noop_sleep,
        )

    assert summary["status"] == "failed"  # every symbol raised → no fabricated bar
    assert summary["errors"]  # explicit errors recorded
    assert secret not in json.dumps(summary)  # scrubbed from the snapshot + its error list
    assert "***" in json.dumps(summary["errors"])  # the redaction marker IS present (the scrub fired)
    assert secret not in json.dumps(get_job(job.job_id))  # absent from GET /api/data/jobs/{id}

    with Session(engine) as session:
        checkpoints = session.exec(select(ImportCheckpoint)).all()
        assert checkpoints  # a fetch job creates a checkpoint
        cp_blob = json.dumps(
            [{c: str(getattr(cp, c)) for c in ImportCheckpoint.model_fields} for cp in checkpoints]
        )
        assert secret not in cp_blob  # NO key column / value on the checkpoint
        assert secret not in json.dumps(resumable_imports(session, cfg))
        runs = session.exec(select(DataProviderRun)).all()
    run_blob = json.dumps([{c: str(getattr(r, c)) for c in ("provider", "status", "message")} for r in runs])
    assert secret not in run_blob  # absent from every DataProviderRun column
    assert secret not in caplog.text  # absent from the logs


# ==================================================================================================
# iter-22 (J-34): chunk plan is config-driven; chunk_total derives from symbol_batch × date_window
# ==================================================================================================
def _with_chunking(cfg, **overrides):
    """A config copy with `data_manager.import_chunking` overridden (the rest unchanged)."""
    ic = cfg.data_manager.import_chunking.model_copy(update=overrides)
    return cfg.model_copy(update={"data_manager": cfg.data_manager.model_copy(update={"import_chunking": ic})})


def test_chunk_total_derives_from_config():
    """`chunk_total` = ceil(n_symbols / symbol_batch_size) × ceil(span / date_window_days). Varying either
    config dimension changes the plan size — proving No magic numbers (both come from config)."""
    cfg = load_config()
    symbols = [f"S{i}" for i in range(10)]
    start, end = date(2024, 1, 1), date(2024, 1, 10)  # 10 calendar days
    # batch 5 over 10 symbols = 2 batches; window 5 over 10 days = 2 windows → 4 chunks
    assert len(_chunk_plan(_with_chunking(cfg, symbol_batch_size=5, date_window_days=5), symbols, start, end)) == 2 * 2
    # smaller batch → more chunks (batch 2 → 5 batches × 2 windows = 10)
    assert len(_chunk_plan(_with_chunking(cfg, symbol_batch_size=2, date_window_days=5), symbols, start, end)) == 5 * 2
    # wider window → fewer chunks (window 10 → 1 window × 2 batches(batch 5) = 2)
    assert len(_chunk_plan(_with_chunking(cfg, symbol_batch_size=5, date_window_days=10), symbols, start, end)) == 1 * 2


# ==================================================================================================
# iter-22 (J-34): 429 retry-with-backoff (patched sleep — no wall-clock); exhaustion re-raises
# ==================================================================================================
class _Rate429NTimes(PriceProvider):
    """429s the first `fail` get_daily calls, then returns one real bar. Records its call count."""

    def __init__(self, fail: int):
        self._fail = fail
        self.calls = 0

    def get_daily(self, symbol, start=None, end=None):
        self.calls += 1
        if self.calls <= self._fail:
            raise RateLimitError("HTTP 429 at https://provider/x")
        return [Bar(date=start or date(2024, 1, 2), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0)]


def test_fetch_with_retry_backoff_then_success():
    """429 exactly `max_retries` times then success → bars returned; the backoff sleeps are the exact
    exponential `min(base*2**i, cap)` sequence, of length `max_retries` (the sleep is PATCHED — no wait)."""
    chunking = load_config().data_manager.import_chunking
    sleeps: list[float] = []
    provider = _Rate429NTimes(chunking.max_retries)
    bars = data_manager._fetch_symbol_with_retry(
        provider, "AAA", date(2024, 1, 1), date(2024, 1, 2), chunking=chunking, sleep_fn=sleeps.append
    )
    assert bars and provider.calls == chunking.max_retries + 1  # max_retries retries after the first try
    expected = [min(chunking.backoff_base_seconds * (2 ** i), chunking.backoff_cap_seconds) for i in range(chunking.max_retries)]
    assert sleeps == expected  # exponential, capped — config-driven, no magic number


def test_fetch_with_retry_exhausted_reraises_rate_limit():
    """A persistent 429 → `RateLimitError` re-raised after `max_retries` backoff sleeps (the caller pauses
    resumable — it never fabricates a bar)."""
    chunking = load_config().data_manager.import_chunking

    class _Always429(PriceProvider):
        def get_daily(self, symbol, start=None, end=None):
            raise RateLimitError("HTTP 429")

    sleeps: list[float] = []
    with pytest.raises(RateLimitError):
        data_manager._fetch_symbol_with_retry(
            _Always429(), "AAA", date(2024, 1, 1), date(2024, 1, 2), chunking=chunking, sleep_fn=sleeps.append
        )
    assert len(sleeps) == chunking.max_retries  # backoff between the max_retries+1 attempts


# ==================================================================================================
# iter-22 (J-34): durable checkpoint + graceful resumable stop + resume + per-(symbol,date) idempotency
# ==================================================================================================
class _OkForThen429(PriceProvider):
    """Returns one bar for symbols in `ok_symbols`; raises a PERSISTENT `RateLimitError` for any other
    symbol. Records every symbol it is asked to fetch (to prove resume skips already-done chunks)."""

    def __init__(self, ok_symbols: set[str]):
        self._ok = ok_symbols
        self.fetched: list[str] = []

    def get_daily(self, symbol, start=None, end=None):
        self.fetched.append(symbol)
        if symbol in self._ok:
            return [Bar(date=start or date(2024, 3, 1), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0)]
        raise RateLimitError("HTTP 429 at https://provider/x")


class _OkForAll(PriceProvider):
    """Returns one bar for every symbol (a recovered provider). Records what it was asked to fetch."""

    def __init__(self):
        self.fetched: list[str] = []

    def get_daily(self, symbol, start=None, end=None):
        self.fetched.append(symbol)
        return [Bar(date=start or date(2024, 3, 1), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0)]


def test_chunked_fetch_pauses_resumable_then_resumes_idempotently(tmp_path):
    """The J-34 crux. A fetch whose provider 429s persistently from the first symbol of chunk 1 pauses
    GRACEFULLY `resumable` (NOT `failed`, nothing fabricated, the loop does not raise). A FRESH DB session
    (simulating a restart) sees the durable `ImportCheckpoint` at `next_chunk_index == 1`;
    `resumable_imports` lists it; Resume (a recovered provider) continues from chunk 1, SKIPS chunk 0's
    already-stored symbols, fetches each remaining symbol exactly once, and inserts NO duplicate
    `(symbol, date)` row."""
    secret = "sk-RESUME-KEY-NEVER-STORED-9c4"
    cfg = load_config()
    batch = cfg.data_manager.import_chunking.symbol_batch_size
    symbols = all_seed_symbols(cfg)
    chunk0 = set(symbols[:batch])  # the first chunk's symbols (date_window=90 over 1 day → 1 window)
    engine = make_engine(f"sqlite:///{tmp_path / 'resume.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:  # a little SPY data so a calendar / latest date exists
        session.add(DailyPrice(symbol="SPY", date=date(2024, 1, 2), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        session.commit()

    # --- run 1: 429s from the first symbol of chunk 1 → graceful resumable pause at chunk index 1 -----
    fetch_day = date(2024, 3, 1)
    job = create_job("fetch", fetch_day, fetch_day, source="tiingo")
    paused_provider = _OkForThen429(chunk0)
    summary1 = run_data_job(
        job.job_id, config=cfg, engine=engine, provider=paused_provider, api_key=secret, sleep_fn=_noop_sleep
    )
    assert summary1["status"] == "resumable"  # distinct from failed — a graceful pause
    assert summary1["chunk_index"] == 1 and summary1["chunk_total"] >= 2  # paused after chunk 0 completed
    assert summary1["symbols_ok"] == batch and summary1["bars_fetched"] == batch  # chunk 0 stored

    # --- a FRESH DB session sees the durable checkpoint (the restart-survival the Resume depends on) ---
    with Session(engine) as fresh:
        cp = fresh.exec(select(ImportCheckpoint).where(ImportCheckpoint.import_id == job.job_id)).one()
        assert cp.next_chunk_index == 1 and cp.status == "resumable"
        assert cp.symbols_ok == batch
        # the key is NEVER on the checkpoint (no key column) nor in resumable_imports
        cp_blob = json.dumps({c: str(getattr(cp, c)) for c in ImportCheckpoint.model_fields})
        assert secret not in cp_blob
        listed = resumable_imports(fresh, cfg)
        assert [r["import_id"] for r in listed] == [job.job_id]  # the paused import is discoverable
        assert secret not in json.dumps(listed)
        bars_after_pause = fresh.scalar(select(func.count()).select_from(DailyPrice).where(DailyPrice.date == fetch_day))
    assert bars_after_pause == batch  # only chunk 0's bars are stored so far

    # --- Resume with a recovered provider → continues from chunk 1, idempotent, completes -------------
    resumed_provider = _OkForAll()
    summary2 = resume_data_job(
        job.job_id, config=cfg, engine=engine, provider=resumed_provider, api_key=secret, sleep_fn=_noop_sleep
    )
    assert summary2["status"] == "ok"  # the import completed
    assert summary2["chunk_index"] == summary2["chunk_total"]  # all chunks done
    # resume SKIPPED chunk 0 entirely — none of its symbols were re-fetched (idempotency)
    assert chunk0.isdisjoint(set(resumed_provider.fetched))
    # resume fetched exactly the remaining symbols, each ONCE (no symbol fetched twice)
    assert resumed_provider.fetched == symbols[batch:]

    with Session(engine) as session:
        rows = session.exec(select(DailyPrice).where(DailyPrice.date == fetch_day)).all()
        # every universe+ETF symbol now has exactly ONE bar on the fetch day — no duplicate (symbol, date)
        per_symbol = {}
        for r in rows:
            per_symbol[r.symbol] = per_symbol.get(r.symbol, 0) + 1
        assert set(per_symbol) == set(symbols)  # all symbols fetched across the two runs
        assert all(count == 1 for count in per_symbol.values())  # NO duplicate row for any (symbol, date)
        # the checkpoint is now terminal (ok) → no longer resumable
        assert resumable_imports(session, cfg) == []


def test_resume_unknown_or_completed_raises():
    """A resume of an unknown import → `LookupError` (API 404); a resume of a non-resumable (ok) import →
    `ValueError` (API 409). Never a fabricated job."""
    cfg = load_config()
    engine = make_engine("sqlite:///:memory:")
    create_db_and_tables(engine)
    with pytest.raises(LookupError):
        resume_data_job("does-not-exist", config=cfg, engine=engine)
    # an `ok` checkpoint is not resumable
    with Session(engine) as session:
        session.add(ImportCheckpoint(
            import_id="done-1", source="tiingo", kind="fetch", start=date(2024, 1, 1), end=date(2024, 1, 2),
            symbol_plan_json=json.dumps(["AAA"]), chunk_total=1, next_chunk_index=1, status="ok",
            created_at=__import__("datetime").datetime(2024, 1, 1), updated_at=__import__("datetime").datetime(2024, 1, 1),
        ))
        session.commit()
    with pytest.raises(ValueError):
        resume_data_job("done-1", config=cfg, engine=engine)
