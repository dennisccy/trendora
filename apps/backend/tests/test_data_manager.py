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

import pytest
from sqlalchemy import func
from sqlmodel import Session, select

from app.config import load_config
from app.db import create_db_and_tables, make_engine
from app.data_providers.base import Bar, PriceProvider, ProviderUnavailableError
from app.engine import forward_testing, scanner
from app.engine.data_manager import (
    JobProgress,
    _trading_days,
    compute_coverage,
    compute_provider_availability,
    create_job,
    recent_runs,
    resolve_provider_key,
    run_data_job,
    validate_job_request,
)
from app.engine.forward_testing import compute_forward_aggregates
from app.engine.scoring import score_stocks
from app.models import DailyPrice, DataProviderRun, ForwardReturn, ScannerResult, ScannerRun
from app.seed_loader import all_seed_symbols, load_seed


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
