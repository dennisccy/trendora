"""Readiness state producer (Data Contract: app.engine.readiness) — iter-28, J-40; widened iter-4 (B3 fix).

The SINGLE honest readiness computer. It returns ONE state ∈ {`ready`, `initializing`, `unavailable`,
`awaiting_snapshot`} plus the background warm-up progress `{done, total}` (cadence snapshots produced /
expected — "history n/m") and an optional `detail` string, computed ONCE here and served by the SINGLE
canonical readiness endpoint (the extended `GET /api/health`). It is descriptive operational/job-control
state — NOT a canonical score/return/bucket and NOT a duplicate of any existing value; it recomputes
nothing (anti-goal: No recompute in the read path does not apply — readiness is not a snapshot value, it
is liveness about whether the snapshots are servable).

The state is reported HONESTLY (anti-goal: Readiness is reported honestly):
  - `unavailable` — the DB is unreachable, OR no run has EVER been persisted (no price data / the
    synchronous latest-snapshot step has not produced a first run). NEVER a fabricated `ready`. This is
    the ONLY unconditional case — even `awaiting_snapshot` below never masks it.
  - `awaiting_snapshot` (iter-4, B3 fix) — a run IS servable (some snapshot exists), but the BENCHMARK
    symbol's (`cfg.etfs.index[0]` — SPY, the same symbol `_warmup_dates`/`walk_forward_asof_dates` use to
    define the trading calendar) own latest bar has advanced past that run, with no run yet for that later
    date — "new data landed for the calendar-defining symbol, snapshot pending." Compared via a per-symbol
    indexed query (`_latest_benchmark_bar_date`, never a whole-table scan — AG-8), so an UNRELATED symbol's
    ordinary fetch never produces this state (the B3 bug this fixes: the check used to compare against the
    whole-table `latest_data_date` max, so any symbol's new bar could falsely flip the badge all the way to
    `unavailable`). `detail` carries a non-null human-readable string naming the condition + recovery
    action; `null` for every other state.
  - `initializing` — the latest snapshot IS servable (so the core read pages work) but the background
    historical warm-up is still in flight (or has not started / has failed): `done < total`, or the
    warm-up record reports `running`/`failed`. A still-warming backend is NEVER mislabeled `unavailable`.
  - `ready` — the latest snapshot is servable AND the historical warm-up has finished (`done >= total`,
    e.g. all cadence snapshots present). `ready` is NEVER reported before the latest snapshot is servable.

`warmup` carries `{done, total, status, message}` so the frontend badge renders live "history n/m"
progress and the analytics pages show their "warming up (n/m)" state — both reading THIS single value
(the frontend never computes readiness itself).
"""
from __future__ import annotations

import json
import os
from datetime import date as date_cls
from pathlib import Path
from typing import Optional

from sqlalchemy import func
from sqlmodel import Session, select

from app.config import REPO_ROOT, Config, get_config
from app.engine import drift as drift_module
from app.engine.evidence import resolve_ledger_path
from app.engine.graveyard import resolve_staging_ledger_path
from app.engine.ledger import append_entry, read_entries
from app.engine.prices import bar_cache, latest_data_date
from app.engine.registry import resolve_registry_path
from app.engine.warmup import _warmup_dates, get_warmup
from app.models import DailyPrice, ScannerRun

READY = "ready"
INITIALIZING = "initializing"
UNAVAILABLE = "unavailable"
# ops-hardening iter-4 (B3 fix): a run IS servable, but the benchmark symbol's (`cfg.etfs.index[0]`) own
# latest bar has advanced past it with no run yet for that date -- distinct from `unavailable` (nothing
# servable at all) and `initializing` (cadence warm-up in flight). See `_latest_benchmark_bar_date` below
# and the module docstring above.
AWAITING_SNAPSHOT = "awaiting_snapshot"

# The three composite preflight verdicts (iter-33, J-20 / backlog B-301). String values are the exact
# DoD-mandated spelling ("NO-GO", hyphenated) — never re-derived elsewhere.
GO = "GO"
DEGRADED = "DEGRADED"
NO_GO = "NO-GO"
_VERDICT_RANK = {GO: 0, DEGRADED: 1, NO_GO: 2}  # for "worst breached component wins" composition
_SEVERITY_TO_VERDICT = {"degraded": DEGRADED, "no-go": NO_GO}


def _latest_run_date(session: Session):
    """The most recent persisted run's as-of date, or None when no snapshot is stored yet."""
    return session.scalar(select(func.max(ScannerRun.asof_date)))


def _latest_benchmark_bar_date(session: Session, cfg: Config):
    """ops-hardening iter-4 (B3 fix) — the BENCHMARK symbol's (`cfg.etfs.index[0]`, SPY — the exact same
    symbol `forward_testing.walk_forward_asof_dates` / `warmup._warmup_dates` already use to define the
    trading calendar) own latest bar date. ONE indexed max query filtered to a single symbol (mirrors
    `latest_data_date`'s shape, AG-8) — never a whole-table scan across all symbols. None when the
    benchmark itself has no stored bars."""
    benchmark = cfg.etfs.index[0]
    return session.scalar(select(func.max(DailyPrice.date)).where(DailyPrice.symbol == benchmark))


# --------------------------------------------------------------------------------------------------
# iter-24 fast-platform item G — memoize the cadence-date set `/api/health` re-derives on every poll.
#
# `_warmup_dates` (which `compute_readiness` calls below) derives its calendar via `walk_forward_asof_dates`
# (`forward_testing.py`), which calls `bars_asof(session, benchmark, latest)` for SPY — on the DEFAULT
# (uncached) path that is a full ORM-row `select(DailyPrice)` query materializing every SPY bar (the exact
# iter-19 OOM-fix shape, just not yet applied to this call site). `/api/health` is polled every
# ~2s (`startup.health_poll_interval_seconds`), so re-deriving this on every poll is wasted work: the
# cadence-date SET only changes when new price data lands (moving `latest_data_date`) or the process loads
# a different config — both captured by the memo key below.
#
# Single-entry memo keyed by `(latest_date, id(cfg))`: production reuses ONE `cfg` object for the process
# lifetime (`get_config()` is `@lru_cache(maxsize=1)`), so `id(cfg)` is stable there; two tests loading
# separate config fixtures get distinct ids, so a memo from one config is never served to another. The
# cold (cache-miss) compute is wrapped in `bar_cache(session)` so the underlying SPY `bars_asof` call
# routes through the COLUMN-PROJECTED `_BarCache` lazy-load path (iter-19's `Bar` records) instead of the
# raw ORM-row query — reusing the existing load-once-bar-cache machinery rather than a second, duplicate
# calendar-fetch implementation. Byte-identical output either way (`bar_cache` is a pure loading
# optimization — same rows, same order); only the memo skips re-deriving it entirely on a poll hit.
_cadence_memo_key: Optional[tuple] = None
_cadence_memo_dates: list[date_cls] = []


def _cached_warmup_dates(session: Session, cfg: Config, latest_data: date_cls) -> list[date_cls]:
    """`_warmup_dates(session, cfg)`, memoized for the steady-state polling case (no re-derivation on
    repeated calls with the same `(latest_date, cfg)`)."""
    global _cadence_memo_key, _cadence_memo_dates
    key = (latest_data, id(cfg))
    if key != _cadence_memo_key:
        with bar_cache(session):
            _cadence_memo_dates = _warmup_dates(session, cfg)
        _cadence_memo_key = key
    return _cadence_memo_dates


def reset_readiness_cache() -> None:
    """Clear the in-process cadence-date memo (tests that mutate the DB/config under the SAME cfg
    object and need a forced fresh derive)."""
    global _cadence_memo_key, _cadence_memo_dates
    _cadence_memo_key = None
    _cadence_memo_dates = []


def compute_readiness(
    session: Session, engine=None, config: Optional[Config] = None
) -> dict:
    """Compute the single honest readiness state + warm-up progress (Data Contract value).

    `engine` is used only to compute the warm-up `total` (the expected cadence-snapshot count) when no
    warm-up record exists yet (e.g. readiness probed before `start_warmup`); when a warm-up record is
    present its own `dates_total`/`dates_done` are authoritative. Reads ONLY the DB + the in-memory
    warm-up record — it never recomputes a canonical score/return/bucket."""
    cfg = config or get_config()

    # DB reachability + the servable-latest check, both in one guarded block: a DB error -> unavailable
    # (surfaced, never faked).
    try:
        latest_data = latest_data_date(session)
        latest_run = _latest_run_date(session)
        # ops-hardening iter-4 (B3 fix): the benchmark's OWN latest bar (one indexed per-symbol query,
        # AG-8) is the ONLY input compared against `latest_run` below -- never `latest_data`'s whole-table
        # max. `latest_data` is still read (unchanged) for the cadence/warm-up total further down; an
        # unrelated symbol's fetch can move IT but no longer touches servability at all.
        latest_benchmark_bar = _latest_benchmark_bar_date(session, cfg)
        db_ok = True
    except Exception:  # pragma: no cover - DB unreachable is surfaced, never faked
        latest_data = None
        latest_run = None
        latest_benchmark_bar = None
        db_ok = False

    # A servable run exists iff ANY run has ever been persisted -- the ONLY unconditional case: a true
    # never-scanned DB (`latest_run is None`) is ALWAYS unavailable, regardless of benchmark bar data
    # (regression guard for the pre-existing `unscanned_engine` fixture / J-04 crash detection).
    has_servable_run = latest_run is not None

    # B3 fix: the benchmark's own latest bar has advanced past the last persisted run, with no run yet
    # for that later date -- "new data landed for the symbol that defines the trading calendar, but the
    # snapshot hasn't caught up." Compared via the per-symbol query above, never the whole-table
    # `latest_data` -- so an unrelated symbol's ordinary fetch can NEVER produce this state.
    awaiting_snapshot = bool(
        has_servable_run and latest_benchmark_bar is not None and latest_benchmark_bar > latest_run
    )

    # The honest cadence-warm-up progress. The expected `total` is the full historical cadence set (the
    # background warm-up's denominator); `done` is how many of those snapshots are ACTUALLY persisted in
    # the DB right now — the ground truth, independent of whether the in-process warm-up thread is alive.
    # The in-memory warm-up record (when present) supplies the live `status`/`message` for the badge, but
    # the DB-derived `done`/`total` keep the signal correct on a warm DB even with no thread running.
    if db_ok and latest_data is not None:
        # item G (iter-24): the memoized cadence-date derivation (see `_cached_warmup_dates` above) —
        # re-derived only when `latest_data` or the config object changes, not on every poll.
        cadence_dates = _cached_warmup_dates(session, cfg, latest_data)
        total = len(cadence_dates)
        # ONE grouped existence query instead of one `get_run_for_date` point-query per cadence date.
        # `ScannerRun.asof_date` is unique (one run per date), so the count of persisted dates that are
        # IN `cadence_dates` is exactly `sum(1 for d in cadence_dates if a run exists for d)`.
        persisted_dates = set(
            session.exec(
                select(ScannerRun.asof_date).where(ScannerRun.asof_date.in_(cadence_dates))
            ).all()
        ) if cadence_dates else set()
        done = len(persisted_dates)
    else:
        cadence_dates = []
        total = 0
        done = 0

    warmup = get_warmup()
    if warmup is not None:
        status = warmup.get("status", "running")
        # prefer the live record's progress when it is ahead of the DB read (covers the brief window
        # before a just-committed snapshot is visible to this session), but never below the DB ground truth
        done = max(done, int(warmup.get("dates_done", 0)))
        if int(warmup.get("dates_total", 0)) > total:
            total = int(warmup.get("dates_total", 0))
    else:
        # No warm-up launched in this process (readiness probed during the synchronous boot, or a test
        # that never starts the background task). The DB ground truth above is authoritative.
        status = "ok" if done >= total else "pending"

    message = f"history {done}/{total}"

    # The honest state. unavailable dominates (no servable run at all -- the ONLY unconditional case).
    # Otherwise awaiting_snapshot when the benchmark's own bar has outrun the last run (B3 fix, iter-4).
    # Otherwise ready iff the historical warm-up is COMPLETE (every cadence snapshot persisted) AND the
    # warm-up is not still actively running and did not fail — so the badge truthfully shows the flip to
    # Ready only once warm-up settles. A `running` record stays `initializing` even when its snapshots are
    # all present (its forward-returns backfill may still be in flight); a `failed` record never reports
    # `ready` (honest, not a silent green); `pending` (no in-process warm-up / DB-derived-complete on a
    # warm DB) with all snapshots present is ready. A still-warming / failed / awaiting-snapshot backend is
    # NEVER mislabeled unavailable.
    if not db_ok or not has_servable_run:
        state = UNAVAILABLE
    elif awaiting_snapshot:
        state = AWAITING_SNAPSHOT
    elif done >= total and status in ("ok", "pending"):
        state = READY
    else:
        state = INITIALIZING

    # ops-hardening iter-4 (B3 fix): the honest, human-readable detail -- non-null ONLY for the new
    # state (mirrors the `PreflightComponent.detail` naming precedent), naming the condition + the
    # recovery action (an operator-run backfill/rebuild on Data Manager produces the missing snapshot).
    detail: Optional[str] = None
    if state == AWAITING_SNAPSHOT:
        benchmark = cfg.etfs.index[0]
        detail = (
            f"New data has landed for the benchmark ({benchmark}) through "
            f"{latest_benchmark_bar.isoformat()}, but no snapshot has been produced for that date yet. "
            "Run a backfill or rebuild on Data Manager to produce it."
        )

    # ops-hardening iter-24 (J-09): compose the historical background-dispatch registry's own disclosure
    # accessor into this SAME return dict, mirroring how `warmup`'s separate-module state is already
    # composed above -- no new pattern, no DB read added (a pure in-memory registry read). Deferred import
    # (this module has never imported `forward_testing` before; keeping it local here, rather than at
    # module level, mirrors `forward_testing.py`'s own established deferred-import convention for its
    # cross-module `app.engine.research._dataset_version` dependency -- avoid introducing any import-order
    # coupling between the two engine modules for the sake of one read-only accessor call).
    #
    # Scoped try/except (mirrors this function's OWN db_ok guard above): a broken in-memory read here must
    # degrade ONLY this one field to its honest empty shape -- never blank the rest of the readiness
    # payload (`state`/`warmup` stay correct even if this accessor were to raise).
    from app.engine import forward_testing

    try:
        background_compute = forward_testing.get_background_compute_status()
    except Exception:  # pragma: no cover - a broken in-memory read must never blank readiness
        background_compute = {"active": [], "recent_outcomes": []}

    return {
        "state": state,
        "detail": detail,
        "background_compute": background_compute,
        "warmup": {
            "done": done,
            "total": total,
            "status": status,
            "message": message,
        },
    }


# ====================================================================================================
# Daily preflight verdict (iter-33, J-20 / backlog B-301) — a composite GO/DEGRADED/NO-GO verdict
# layered on top of `compute_readiness` above. See `app.config.ReadinessCfg` for the tunables.
# ====================================================================================================
def _ledger_file_ok(path: str) -> tuple[bool, str]:
    """`(True, "")` when `path` exists and every non-blank line parses as JSON (the honest "empty
    ledger" case — zero lines — also counts as ok, mirroring `app.engine.ledger.read_entries`); `(False,
    <reason>)` when the file is missing or contains unparseable JSON. Tiny-file read only — never a DB
    query or a whole-table scan (anti-goal #8)."""
    if not os.path.exists(path):
        return False, f"missing ({path})"
    try:
        with open(path, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    json.loads(line)
    except (OSError, json.JSONDecodeError) as exc:
        return False, f"unparseable ({path}: {exc})"
    return True, ""


def compute_preflight(session: Session, config: Optional[Config] = None) -> dict:
    """Compute the single daily preflight verdict (Data Contract value) — a PURE composition over four
    inputs that exist now, recomputing none of them:

      - **servability** — reuses `compute_readiness`'s OWN liveness check verbatim (no second
        computation): breached iff its `state == "unavailable"`.
      - **freshness** — the latest bar's age in trading days vs a deterministic, seed-resolved reference
        (always the latest data date itself — never `date.today()`, anti-goal #5), so a fully-loaded
        seed is always 0 days old. Breached when that age exceeds `config.readiness.freshness_max_age_days`
        (an owner-configured threshold; lowering it — e.g. below zero — is the sanctioned lever for
        inducing a breach without mutating committed seed data) or when there is no price data at all.
      - **DB/ledger integrity** — the DB is reachable AND the canonical/staging/registry JSONL files
        (`resolve_ledger_path` / `resolve_staging_ledger_path` / `resolve_registry_path` — the EXACT
        existing resolvers, never duplicated) exist and parse. Tiny-file reads only.
      - **drift** (iter-35, J-21 / backlog B-304) — the live-vs-seed overlap-check artifact, re-read
        VERBATIM via `app.engine.drift.read_drift_report()` (a tiny-file read, never a DB query/scan —
        anti-goal #8, mirroring the integrity component above). `ok` when the artifact is ABSENT (no
        fetch has run yet — servability/freshness/integrity behave IDENTICALLY to a pre-iter-35 backend
        in this case, the J-20 non-regression guarantee) or its `status == "clean"`; breached when
        `status == "drift"` (the detail names every affected symbol) or the artifact exists but could
        not be parsed (an honest degraded reason — never silently treated as clean).

    The overall verdict is the WORST of every breached component's configured severity (`GO` when
    nothing is breached). Returns `{verdict, reasons, components, as_of, reference}` (the spec names the
    freshness anchor "as_of/reference" — both keys are served, same value, so either name finds it) —
    `components` carries every input's `{ok, severity, detail}` regardless of outcome; `reasons` collects
    the breached components' plain-language `detail` strings, in composition order, for direct display."""
    cfg = config or get_config()
    rcfg = cfg.readiness
    readiness_result = compute_readiness(session, config=cfg)

    try:
        latest_data = latest_data_date(session)
        db_ok = True
    except Exception:  # pragma: no cover - DB unreachable is surfaced, never faked
        latest_data = None
        db_ok = False

    components: dict[str, dict] = {}
    reasons: list[str] = []
    verdict = GO

    def _apply(name: str, ok: bool, detail: str) -> None:
        nonlocal verdict
        severity = rcfg.severity[name]
        components[name] = {"ok": ok, "severity": severity, "detail": detail}
        if not ok:
            reasons.append(detail)
            mapped = _SEVERITY_TO_VERDICT[severity]
            if _VERDICT_RANK[mapped] > _VERDICT_RANK[verdict]:
                verdict = mapped

    # --- servability: compute_readiness's own liveness check, verbatim ---
    servable = readiness_result["state"] != UNAVAILABLE
    _apply(
        "servability",
        servable,
        "Backend is serving the latest snapshot."
        if servable
        else "No servable snapshot: the database is unreachable or no run is persisted for the latest data date.",
    )

    # --- freshness: trading-day age of the latest bar vs the deterministic seed-resolved reference ---
    if latest_data is None:
        _apply("freshness", False, "Data freshness could not be determined: no price data is loaded.")
    else:
        age_days = 0  # the reference IS the latest available bar (never date.today()) -- see docstring
        fresh = age_days <= rcfg.freshness_max_age_days
        if fresh:
            detail = (
                f"Latest data ({latest_data.isoformat()}) is {age_days} trading day(s) old "
                f"(max {rcfg.freshness_max_age_days})."
            )
        else:
            detail = (
                f"Latest data ({latest_data.isoformat()}) is {age_days} trading day(s) old, exceeding "
                f"the configured maximum of {rcfg.freshness_max_age_days} day(s)."
            )
        _apply("freshness", fresh, detail)

    # --- DB / ledger integrity: DB reachable AND the three canonical JSONL files exist + parse ---
    problems: list[str] = []
    if not db_ok:
        problems.append("the database is unreachable")
    for label, resolver in (
        ("evidence ledger", resolve_ledger_path),
        ("staging ledger", resolve_staging_ledger_path),
        ("pre-registration registry", resolve_registry_path),
    ):
        ok, reason = _ledger_file_ok(resolver())
        if not ok:
            problems.append(f"{label} {reason}")
    _apply(
        "integrity",
        not problems,
        "The database and all ledger/registry files are reachable and parse."
        if not problems
        else "Integrity check failed: " + "; ".join(problems) + ".",
    )

    # --- drift: the live-vs-seed overlap-check artifact (iter-35, J-21 / backlog B-304) — a tiny-file
    # read via the SINGLE reader `read_drift_report`, never a DB query/scan (anti-goal #8). A MISSING
    # artifact means no fetch has run yet (honest inert -> ok, byte-identical to a pre-iter-35 backend);
    # `status == "clean"` -> ok; `status == "drift"` -> breached, naming every affected symbol; any other
    # status (the artifact exists but could not be parsed) -> breached with an honest degraded reason,
    # never silently treated as clean.
    drift_report = drift_module.read_drift_report()
    if drift_report is None:
        _apply("drift", True, "No fetch has run yet — nothing to compare against the committed seed.")
    elif drift_report.get("status") == drift_module.STATUS_CLEAN:
        _apply("drift", True, "The most recent fetch matched the committed seed over the overlap window.")
    elif drift_report.get("status") == drift_module.STATUS_DRIFT:
        symbols = sorted(a.get("symbol", "?") for a in drift_report.get("affected") or [])
        _apply(
            "drift", False,
            "Live-vs-seed drift detected (adjustment seam) for: " + ", ".join(symbols) + ".",
        )
    else:
        _apply(
            "drift", False,
            "Drift report is unreadable: the artifact exists but could not be parsed.",
        )

    reference = latest_data.isoformat() if latest_data else None
    return {
        "verdict": verdict,
        "reasons": reasons,
        "components": components,
        # the spec names this "as_of/reference" (either name); both keys carry the SAME deterministic
        # freshness anchor so a reader using either name finds it -- never two different values.
        "as_of": reference,
        "reference": reference,
    }


# The environment-variable NAME the verdict-history path may be overridden with (test/gate seam — the
# NAME only, never a path VALUE literal in code). Mirrors `app.engine.evidence.LEDGER_PATH_ENV`.
VERDICT_HISTORY_PATH_ENV = "READINESS_VERDICT_HISTORY_PATH"


def resolve_verdict_history_path() -> str:
    """The verdict-history log path: the `READINESS_VERDICT_HISTORY_PATH` env override if set, else
    `config.readiness.verdict_history_path` resolved against `REPO_ROOT` when relative. Mirrors
    `app.engine.evidence.resolve_ledger_path()` exactly."""
    override = os.environ.get(VERDICT_HISTORY_PATH_ENV)
    if override:
        return override
    configured = Path(get_config().readiness.verdict_history_path)
    if not configured.is_absolute():
        configured = REPO_ROOT / configured
    return str(configured)


def record_verdict_transition(
    verdict: str, reasons: list[str], reference: Optional[str], path: Optional[str] = None
) -> bool:
    """Append ONE verdict-history entry iff `verdict` differs from the LAST recorded one (append-only;
    bounded growth — this is the "only on a transition, never on every ~2s poll" guard). Returns True iff
    an entry was appended. `path` defaults to `resolve_verdict_history_path()`; a test may pass a
    `tmp_path` file instead (mirrors `app.engine.budget_accounting.build_budget_payload`'s optional-path
    pattern). Reuses `app.engine.ledger`'s existing `read_entries`/`append_entry` verbatim — no second
    JSONL read/write implementation."""
    resolved = path if path is not None else resolve_verdict_history_path()
    entries = read_entries(resolved)
    last_verdict = entries[-1].get("verdict") if entries else None
    if last_verdict == verdict:
        return False
    append_entry(resolved, {"verdict": verdict, "reasons": reasons, "reference": reference})
    return True
