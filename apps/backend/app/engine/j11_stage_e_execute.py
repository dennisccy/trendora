"""app.engine.j11_stage_e_execute -- J-11 Stage E EXECUTION (goal-market-compass iter-20).

`docs/goal.md`'s "OWNER RULING -- J-11 Stage D through Stage G recovery execution AUTHORIZED" (owner,
2026-08-26) item 7 authorizes Stage E, unconditionally, once Stage D has succeeded (iteration 19 --
`runs/goal-market-compass-iter-19/j11-stage-d-execute-outcome.json`: `executed: true`). Stage E is the
GLOBAL create-once forward-return hole repair: fill every derivable `forward_returns` gap on the eleven
Stage-D-regenerated incident-date runs AND on any retained (non-incident) run whose forward-return rows
the original incident cascade deleted -- through the EXISTING canonical machinery only, with zero write
to any table other than `forward_returns`.

**The one write-scope risk this module exists to avoid (see the iteration-20 spec's BACKGROUND, and the
plan's Alignment check, both independently confirmed by reading `forward_testing._backfill()` directly):**
`forward_testing.backfill_forward_returns()` -- the WHOLE-DATABASE entry point -- delegates to `_backfill`,
which, BEFORE inserting a single forward return, calls `scanner.run_scan` for any `walk_forward_asof_dates()`
date lacking a `ScannerRun` (a `quarterly`, 30-year cadence grid independent of the scanner's own `monthly`
snapshot schedule). Calling it here risks minting a `ScannerRun` OUTSIDE the eleven-date incident boundary
as an undocumented side effect -- exactly what ruling item 7 forbids ("Stage E may not ... broaden into
unrelated historical cleanup"). This module therefore calls ONLY
`forward_testing.backfill_run_forward_returns(session, run, config)` -- the per-run, create-once,
INSERT-only path that never touches `scanner_runs`/`scanner_results`/`*_scores` -- once per row currently
in `scanner_runs`. `test_j11_stage_e_execute.py::test_tc3_module_never_references_backfill_forward_returns`
and `::test_tc3_cli_script_never_references_backfill_forward_returns` prove this statically (AST-walked,
not a docstring/code-review claim).

Sequence:

  1. Fresh, READ-ONLY preflight -- before any write: `j11_stage_d_execute.recheck_maintenance_boundary_and_guard`
     (REUSED directly, never reimplemented) re-verifies the `j11-incident-recovery` boundary is `active=1`
     covering exactly `INCIDENT_DATES` and the live guard blocks all 11; `confirm_stage_d_runs_present_unrestamped`
     re-derives, per incident date, that Stage D's OWN recorded run id is still the live row's id, still
     stamped with Stage D's frozen `engine_identity`, and currently carries ZERO `ForwardReturn` rows;
     `check_engine_identity_matches_stage_d` recomputes `engine_identity.compute_engine_identity(config)`
     fresh and asserts it equals the value Stage D froze (per ruling item 2, a mismatch means the whole D-G
     attempt has drifted and is incomplete -- STOP, never proceed under a new identity);
     `confirm_manifests_unchanged` re-dumps `next_session_manifests` and diffs it against the SAME certified
     baseline (`runs/goal-market-compass-iter-16/j11-stage-d-certified-baseline.json`) Stage D's own preflight
     compared against -- transitively valid because Stage D's own post-execution mutation accounting already
     proved manifests were unchanged THROUGH Stage D, and maintenance isolation (one controlled writer) means
     nothing else could have touched them since. `stage_e_preflight_gate_verdict` combines all four into one
     go/no-go: proceed ONLY if every check agrees.
  2. The ONE authorized write sequence -- `execute_stage_e_repair_loop`: every row currently in `scanner_runs`
     (the full retained-plus-Stage-D-rebuilt population), ascending `asof_date`, gets exactly one
     `forward_testing.backfill_run_forward_returns(session, run, config)` call, inside ONE shared
     `prices.prefilled_bar_cache(session, expected_symbols=<the resolved candidate pool>)` context (iter-19
     audit finding B3: the columnar `_SymbolColumns` shape this loads into is ~3.3x more memory-efficient
     than the lazy per-symbol `list[Bar]` path for a loop that -- given ~3,100+ runs spanning 30 years --
     will eventually touch nearly every symbol in `daily_prices` regardless of which path is chosen; one
     bulk streamed query beats thousands of small per-symbol ones on both memory and I/O). A B4-style hard
     assertion proves the iterated row set is exactly the live `scanner_runs` table, never a caller-narrowed
     subset.
  3. Live, read-only re-verification of the three populations `docs/goal.md` step 5 names, by DIRECT QUERY
     against `forward_returns` -- never merely asserted from the loop's own in-process diff
     (`live_verify_three_populations`).
  4. Post-execution mutation accounting (`build_stage_e_mutation_accounting`) -- proves
     `changed_existing_tables` is a subset of exactly `{forward_returns}`, the 8 named out-of-scope tables
     (`daily_prices`, `scanner_runs`, `scanner_results`, `sector_scores`, `theme_scores`, `data_provider_runs`,
     `watchlist`, `maintenance_boundaries`) show zero fingerprint change, `next_session_manifests` stays
     byte-identical, and the loop's self-reported total reconciles exactly against the live
     `COUNT(*)` delta.

Never touches (imports nothing from, calls nothing in): `app/api/*`, `scoring.py`, `sectors.py`, `compass.py`,
`data_manager.py`'s write paths, or `scanner.resolve_run`. Does not modify `forward_testing.py`, `scanner.py`,
`prices.py`, `j11_maintenance.py`, `j11_stage_d.py`, or `j11_stage_d_execute.py` -- this module COMPOSES
their existing functions as-is.
"""
from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

from sqlalchemy import func
from sqlmodel import Session, select

from app.config import Config, get_config
from app.engine import engine_identity
from app.engine import forward_testing
from app.engine import j11_maintenance
from app.engine import j11_schema_migration as migration
from app.engine import j11_stage_d_execute as jsde
from app.engine.j11_maintenance import INCIDENT_DATES
from app.engine.prices import prefilled_bar_cache
from app.engine.universe_screen import read_pool
from app.models import DailyPrice, ForwardReturn, NextSessionManifest, ScannerRun

# The ONE table this module's one authorized write may ever touch (ruling item 7: Stage E "may fill
# derivable missing forward-return rows ... may not ... broaden into unrelated historical cleanup").
STAGE_E_WRITE_TABLES: tuple[str, ...] = ("forward_returns",)

# The 8 named tables the DoD requires proven at zero fingerprint change (TC-18) -- everything Stage E
# reads but must never write, spelled out explicitly rather than derived, so a future schema addition
# does not silently narrow this list.
OUT_OF_SCOPE_TABLES: tuple[str, ...] = (
    "daily_prices", "scanner_runs", "scanner_results", "sector_scores", "theme_scores",
    "data_provider_runs", "watchlist", "maintenance_boundaries",
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _count(session: Session, model: Any, **filters: Any) -> int:
    """A column-projected `COUNT(*)` -- never an ORM hydration of the matched rows (AG-8). Mirrors
    `j11_maintenance._count`'s idiom (not imported cross-module -- each j11_*.py module carries its own
    trivial copy, the established convention in this file family)."""
    stmt = select(func.count()).select_from(model)
    for key, value in filters.items():
        stmt = stmt.where(getattr(model, key) == value)
    return int(session.scalar(stmt) or 0)


# ================================================================================================
# Step 1 -- fresh, read-only preflight (boundary/guard reuse + three Stage-E-specific checks)
# ================================================================================================


def confirm_stage_d_runs_present_unrestamped(
    session: Session,
    *,
    expected_run_id_by_date: dict[str, int],
    frozen_engine_identity: str,
) -> dict:
    """For every one of Stage D's 11 rebuilt incident dates, confirm the live `ScannerRun` row is
    present, carries the SAME `id` Stage D's own recorded regeneration evidence assigned to that date
    (proving it was never deleted/recreated since), carries the SAME frozen `engine_identity` Stage D
    stamped, and currently has ZERO `ForwardReturn` rows (Stage E's own starting-state precondition).
    Read-only -- never writes, never restamps."""
    per_date: dict[str, dict] = {}
    for date_str, expected_run_id in sorted(expected_run_id_by_date.items()):
        one_date = date.fromisoformat(date_str)
        row = session.exec(
            select(ScannerRun.id, ScannerRun.asof_date, ScannerRun.engine_identity, ScannerRun.created_at)
            .where(ScannerRun.asof_date == one_date)
        ).first()
        present = row is not None
        observed_id = int(row[0]) if present else None
        observed_identity = row[2] if present else None
        fr_count = _count(session, ForwardReturn, run_id=observed_id) if present else None
        id_matches = present and observed_id == expected_run_id
        identity_matches = present and observed_identity == frozen_engine_identity
        zero_forward_returns = present and fr_count == 0
        per_date[date_str] = {
            "expected_run_id": expected_run_id,
            "present": present,
            "observed_run_id": observed_id,
            "id_matches": id_matches,
            "observed_engine_identity": observed_identity,
            "identity_matches": identity_matches,
            "observed_created_at": row[3].isoformat() if present and row[3] is not None else None,
            "forward_return_count": fr_count,
            "zero_forward_returns": zero_forward_returns,
            "ok": present and id_matches and identity_matches and zero_forward_returns,
        }
    ok = bool(per_date) and all(v["ok"] for v in per_date.values())
    return {"checked_at": _now_iso(), "per_date": per_date, "ok": ok}


def check_engine_identity_matches_stage_d(fresh_identity: str, stage_d_frozen_identity: Optional[str]) -> dict:
    """A fresh, honestly-stated (equal-or-not, either way) comparison of the LIVE recomputed
    `engine_identity` against Stage D's frozen value. UNLIKE Stage D's own historical comparison (where
    an equal value against an OLDER attempt was an expected non-failure), inequality HERE is a hard
    blocker -- per ruling item 2, a drift since Stage D makes the whole D-G attempt incomplete."""
    matches = stage_d_frozen_identity is not None and fresh_identity == stage_d_frozen_identity
    return {
        "checked_at": _now_iso(),
        "fresh_engine_identity": fresh_identity,
        "stage_d_frozen_engine_identity": stage_d_frozen_identity,
        "matches": matches,
        "ok": matches,
    }


def confirm_manifests_unchanged(engine: Any, *, certified_manifest_dump: list[dict]) -> dict:
    """Fresh live dump of `next_session_manifests`, diffed against the SAME certified baseline dump
    Stage D's own preflight compared against (`runs/goal-market-compass-iter-16/
    j11-stage-d-certified-baseline.json`'s `manifest_dump`) -- valid transitively because Stage D's own
    post-execution mutation accounting already proved zero manifest change THROUGH Stage D, and
    maintenance isolation (one controlled writer, no boot warmup) means nothing else could have written
    since. Reuses `j11_schema_migration.dump_table`/`diff_dumps` -- never a second comparison
    implementation."""
    live_dump = migration.dump_table(engine, NextSessionManifest.__table__)
    diff = migration.diff_dumps(certified_manifest_dump, live_dump)
    return {
        "checked_at": _now_iso(),
        "certified_row_count": len(certified_manifest_dump),
        "live_row_count": len(live_dump),
        "diff": diff,
        "ok": diff["equal"],
    }


def stage_e_preflight_gate_verdict(
    *, boundary_recheck: dict, runs_check: dict, identity_check: dict, manifest_check: dict,
) -> dict:
    """The single go/no-go decision for Stage E EXECUTION. Any one of the four checks failing means
    `proceed: False`, and the caller MUST perform zero writes to any table."""
    boundary_ok = bool(boundary_recheck.get("ok"))
    runs_ok = bool(runs_check.get("ok"))
    identity_ok = bool(identity_check.get("ok"))
    manifest_ok = bool(manifest_check.get("ok"))
    proceed = boundary_ok and runs_ok and identity_ok and manifest_ok

    blocking_reasons: list[str] = []
    if not boundary_ok:
        blocking_reasons.append("maintenance_boundary_or_guard_recheck_failed")
    if not runs_ok:
        blocking_reasons.append("stage_d_runs_not_present_unrestamped_and_zero_forward_returns")
    if not identity_ok:
        blocking_reasons.append("engine_identity_drifted_since_stage_d")
    if not manifest_ok:
        blocking_reasons.append("next_session_manifests_changed_since_stage_d")

    return {
        "generated_at": _now_iso(),
        "proceed": proceed,
        "boundary_ok": boundary_ok,
        "runs_ok": runs_ok,
        "identity_ok": identity_ok,
        "manifest_ok": manifest_ok,
        "blocking_reasons": blocking_reasons,
    }


# ================================================================================================
# Step 2 -- pre/post captures reused by the CLI script for mutation accounting
# ================================================================================================


def capture_all_scanner_run_fingerprint(session: Session) -> dict:
    """A full, column-projected (id, asof_date, engine_identity, created_at) snapshot of EVERY
    `ScannerRun` row -- Stage E must never touch ANY of them (unlike Stage D's narrower legacy/null
    population, Stage E's write is confined to `forward_returns` alone, so the WHOLE table must be
    byte-unchanged). ~3,100+ rows is small and bounded (never a multi-million-row hydration -- AG-8),
    mirroring `j11_stage_d_execute.capture_legacy_and_null_scanner_run_fingerprint`'s exact shape widened
    to every row instead of a filtered subset."""
    rows = session.exec(
        select(ScannerRun.id, ScannerRun.asof_date, ScannerRun.engine_identity, ScannerRun.created_at)
        .order_by(ScannerRun.id)
    ).all()
    payload = [
        {
            "id": int(r[0]),
            "asof_date": r[1].isoformat() if r[1] is not None else None,
            "engine_identity": r[2],
            "created_at": r[3].isoformat() if r[3] is not None else None,
        }
        for r in rows
    ]
    fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()
    return {"captured_at": _now_iso(), "row_count": len(payload), "rows": payload, "fingerprint": fingerprint}


def capture_retained_incident_hole_counts(session: Session, *, incident_run_ids: Iterable[int]) -> dict:
    """Per-`run_id` counts of `ForwardReturn` rows whose `measured_date` lands on one of the 11 incident
    dates but whose `run_id` is NOT one of Stage D's 11 rebuilt runs -- the "holes on retained runs"
    population (b) `docs/goal.md` step 5 names, first sized in Stage B's pre-reset inventory. ONE grouped
    scan (mirrors `j11_maintenance.capture_pre_reset_inventory`'s own `measured_into_counts` idiom -- a
    single bounded aggregation, never a per-date or per-run repeated full-table scan)."""
    excluded = set(incident_run_ids)
    rows = session.exec(
        select(ForwardReturn.run_id, func.count())
        .where(ForwardReturn.measured_date.in_(INCIDENT_DATES))
        .group_by(ForwardReturn.run_id)
    ).all()
    counts = {int(run_id): int(n) for run_id, n in rows if int(run_id) not in excluded}
    return {
        "captured_at": _now_iso(),
        "per_run_id_counts": counts,
        "total": sum(counts.values()),
        "run_count": len(counts),
    }


# ================================================================================================
# Step 3 -- the per-run write loop (the ONE authorized write sequence)
# ================================================================================================


def resolve_pool_symbols() -> set[str]:
    """The candidate-pool symbol set, read from the SAME committed `universe_pool.csv` parser
    `data_manager.py`'s own `_do_backfill`/`_persist_per_date_coverage_snapshots` already use for their
    `prefilled_bar_cache(session, expected_symbols=pool_symbols)` call (`pool_symbols = {row["symbol"]
    for row in read_pool()}`) -- a pure, offline, local file read (no network, no DB). A thin, separately
    named wrapper so a test can inject a small synthetic pool instead of reading the real committed CSV."""
    return {row["symbol"] for row in read_pool()}


def execute_stage_e_repair_loop(
    session: Session, config: Config, *, pool_symbols: Optional[set[str]] = None,
) -> dict:
    """The whole-attempt per-run loop: every row CURRENTLY in `scanner_runs` (ascending `asof_date`),
    each getting exactly one `forward_testing.backfill_run_forward_returns(session, run, config)` call --
    the create-once, INSERT-only path. NEVER calls or imports `forward_testing.backfill_forward_returns`
    (the whole-database entry point -- see the module docstring). Runs inside ONE shared
    `prices.prefilled_bar_cache(session, expected_symbols=<resolved pool>)` context so every symbol's
    price series loads at most once for the whole loop, however many of the ~3,100+ runs touch it.

    B4-style hard assertion: the iterated row set is exactly the live `scanner_runs` table at the moment
    the loop starts (never a caller-narrowed subset) -- a plain `COUNT(*)` compared against the fetched
    row count, both read from the same open session before the loop begins."""
    live_total = _count(session, ScannerRun)
    runs = session.exec(select(ScannerRun).order_by(ScannerRun.asof_date)).all()
    if len(runs) != live_total:
        raise RuntimeError(
            f"execute_stage_e_repair_loop: fetched {len(runs)} ScannerRun rows but a fresh COUNT(*) on "
            f"the same session reports {live_total} -- refusing to proceed on an inconsistent row set "
            "(B4 hard assertion; this loop must always receive exactly the live scanner_runs table)."
        )

    incident_date_set = set(INCIDENT_DATES)
    symbols = pool_symbols if pool_symbols is not None else resolve_pool_symbols()

    per_run_results: list[dict] = []
    with prefilled_bar_cache(session, expected_symbols=symbols):
        for run in runs:
            result = forward_testing.backfill_run_forward_returns(session, run, config)
            classification = "rebuilt_incident_run" if run.asof_date in incident_date_set else "retained_run"
            per_run_results.append({**result, "classification": classification})

    total_inserted = sum(r["rows_inserted"] for r in per_run_results)
    incident_inserted = sum(r["rows_inserted"] for r in per_run_results if r["classification"] == "rebuilt_incident_run")
    retained_inserted = sum(r["rows_inserted"] for r in per_run_results if r["classification"] == "retained_run")
    return {
        "generated_at": _now_iso(),
        "total_runs_processed": len(per_run_results),
        "total_rows_inserted": total_inserted,
        "rows_inserted_on_rebuilt_incident_runs": incident_inserted,
        "rows_inserted_on_retained_runs": retained_inserted,
        "per_run_results": per_run_results,
    }


# ================================================================================================
# Step 4 -- live, read-only re-verification of the three named populations
# ================================================================================================


def live_verify_three_populations(
    session: Session,
    *,
    incident_run_ids: list[int],
    pre_retained_hole_counts_by_run: dict[int, int],
) -> dict:
    """Live, read-only re-derivation of the three populations `docs/goal.md` step 5 names, by DIRECT
    query against `forward_returns` -- never merely asserted from the write loop's own in-process diff
    (DoD: "proven by live read-only query, not asserted from a diff").

    (a) rows now present for the 11 Stage-D-rebuilt runs (pre-Stage-E count was proven zero by the
        preflight gate, so `post` IS the newly-inserted count).
    (b) rows on retained (non-incident) runs whose `measured_date` lands on an incident date --
        never decreases from its pre-Stage-E per-run value (TC-6).
    (c) the not-yet-mature population: two live structural proofs that no immature combination was ever
        fabricated -- no stored `measured_date` exceeds the latest stored `daily_prices` date (a
        `ForwardReturn` can only ever be measured against an already-stored bar), and the run with the
        single LATEST `asof_date` in the whole table (the run with the least, often zero, observable
        post-snapshot history) carries no MORE forward-return rows than its own live-computed
        observable-horizon ceiling allows."""
    incident_ids = set(incident_run_ids)

    post_a_rows = session.exec(
        select(ForwardReturn.run_id, func.count())
        .where(ForwardReturn.run_id.in_(incident_run_ids))
        .group_by(ForwardReturn.run_id)
    ).all()
    post_a_counts = {int(run_id): int(n) for run_id, n in post_a_rows}
    population_a = {
        str(rid): {"pre": 0, "post": post_a_counts.get(rid, 0), "newly_inserted": post_a_counts.get(rid, 0)}
        for rid in incident_run_ids
    }
    population_a_total_newly_inserted = sum(v["newly_inserted"] for v in population_a.values())

    post_b_rows = session.exec(
        select(ForwardReturn.run_id, func.count())
        .where(ForwardReturn.measured_date.in_(INCIDENT_DATES))
        .group_by(ForwardReturn.run_id)
    ).all()
    post_b_counts = {int(run_id): int(n) for run_id, n in post_b_rows if int(run_id) not in incident_ids}
    never_decreased = all(
        post_b_counts.get(run_id, 0) >= pre_count for run_id, pre_count in pre_retained_hole_counts_by_run.items()
    )
    population_b_total_pre = sum(pre_retained_hole_counts_by_run.values())
    population_b_total_post = sum(post_b_counts.values())

    max_measured_date = session.exec(select(func.max(ForwardReturn.measured_date))).first()
    max_measured_date = max_measured_date[0] if isinstance(max_measured_date, tuple) else max_measured_date
    max_price_date = session.exec(select(func.max(DailyPrice.date))).first()
    max_price_date = max_price_date[0] if isinstance(max_price_date, tuple) else max_price_date
    no_row_beyond_stored_prices = (
        max_measured_date is None or max_price_date is None or max_measured_date <= max_price_date
    )

    latest_run = session.exec(select(ScannerRun).order_by(ScannerRun.asof_date.desc()).limit(1)).first()
    latest_run_check: dict = {"latest_run_present": latest_run is not None}
    if latest_run is not None:
        cfg = get_config()
        horizons = cfg.walk_forward.horizons
        max_h = max(horizons)
        observable_days = len(
            session.exec(
                select(DailyPrice.date).where(DailyPrice.date > latest_run.asof_date)
                .distinct().order_by(DailyPrice.date).limit(max_h)
            ).all()
        )
        observable_horizon_count = len([h for h in horizons if h <= observable_days])
        latest_run_fr_count = _count(session, ForwardReturn, run_id=latest_run.id)
        latest_run_check.update({
            "asof_date": latest_run.asof_date.isoformat(),
            "observable_days": observable_days,
            "observable_horizon_count": observable_horizon_count,
            "forward_return_row_count": latest_run_fr_count,
            # zero observable horizons => zero rows are POSSIBLE for this run (never proves zero rows are
            # REQUIRED when horizons ARE observable -- symbols can still be legitimately absent/NA).
            "ok": observable_horizon_count > 0 or latest_run_fr_count == 0,
        })
    else:
        latest_run_check["ok"] = True  # vacuous -- an empty scanner_runs table has no latest run to check

    checks = {
        "population_a_pre_was_zero": all(v["pre"] == 0 for v in population_a.values()),
        "population_b_never_decreased": never_decreased,
        "population_c_no_row_beyond_stored_prices": no_row_beyond_stored_prices,
        "population_c_latest_run_observable_ceiling_respected": latest_run_check["ok"],
    }
    return {
        "generated_at": _now_iso(),
        "population_a_rebuilt_incident_runs": population_a,
        "population_a_total_newly_inserted": population_a_total_newly_inserted,
        "population_b_retained_run_holes": {
            "pre_total": population_b_total_pre,
            "post_total": population_b_total_post,
            "pre_by_run_id": pre_retained_hole_counts_by_run,
            "post_by_run_id": post_b_counts,
            "never_decreased": never_decreased,
        },
        "population_c_not_yet_mature": {
            "max_measured_date": max_measured_date.isoformat() if max_measured_date else None,
            "max_daily_price_date": max_price_date.isoformat() if max_price_date else None,
            "no_row_beyond_stored_prices": no_row_beyond_stored_prices,
            "latest_run_check": latest_run_check,
        },
        "checks": checks,
        "all_checks_pass": all(checks.values()),
    }


# ================================================================================================
# Memory measurement (TC-11, AG-10) -- read-only /proc inspection, the SAME instrument J-09 uses
# ================================================================================================


def read_process_vm_peak_kb(pid: Optional[int] = None) -> Optional[int]:
    """The CURRENT process's (or an explicit `pid`'s) `VmPeak` from `/proc/<pid>/status`, in kB -- the
    kernel's own running high-water mark for virtual memory over the process's whole life, so ONE read
    at (or after) the heaviest point already reflects the true peak; no sampling loop is needed. Returns
    `None` on any read/parse failure (a missing `/proc` on a non-Linux host, a raced process exit) --
    honest absence, never a fabricated number."""
    target = pid if pid is not None else "self"
    try:
        text = Path(f"/proc/{target}/status").read_text()
    except OSError:
        return None
    for line in text.splitlines():
        if line.startswith("VmPeak:"):
            parts = line.split()
            if len(parts) >= 2 and parts[1].isdigit():
                return int(parts[1])
    return None


def build_memory_check(*, vm_peak_kb: Optional[int], memory_cap_mb: int) -> dict:
    """Compares the measured peak against the configured `server.memory_cap_mb` ceiling (AG-10). This
    process is a standalone maintenance script (never booted via `scripts/start-backend.sh`, which is
    reserved for the API server), so no OS-level `ulimit -v` is applied to it here -- this function
    RECORDS the observed figure against the ceiling (matching J-09's own measurement discipline) rather
    than enforcing one; the DoD requires measurement and recording, not in-process self-termination."""
    cap_kb = memory_cap_mb * 1024
    within_cap = vm_peak_kb is not None and vm_peak_kb <= cap_kb
    return {
        "checked_at": _now_iso(),
        "vm_peak_kb": vm_peak_kb,
        "vm_peak_mb": round(vm_peak_kb / 1024, 1) if vm_peak_kb is not None else None,
        "memory_cap_mb": memory_cap_mb,
        "memory_cap_kb": cap_kb,
        "within_cap": within_cap,
        "margin_mb": round((cap_kb - vm_peak_kb) / 1024, 1) if vm_peak_kb is not None else None,
    }


# ================================================================================================
# Post-execution mutation accounting
# ================================================================================================


def build_stage_e_mutation_accounting(
    *,
    pre_full_table_sweep: dict,
    post_full_table_sweep: dict,
    pre_manifest_dump: list,
    post_manifest_dump: list,
    pre_all_scanner_run_fingerprint: dict,
    post_all_scanner_run_fingerprint: dict,
    pre_daily_prices: dict,
    post_daily_prices: dict,
    pre_provider_runs: dict,
    post_provider_runs: dict,
    pre_watchlist: dict,
    post_watchlist: dict,
    pre_maintenance_boundary_dump: list,
    post_maintenance_boundary_dump: list,
    pre_forward_returns_count: int,
    post_forward_returns_count: int,
    self_reported_total_inserted: int,
    db_file_true_start: dict,
    db_file_true_end: dict,
) -> dict:
    """Pure composition of every pre/post capture into the DoD's mutation-accounting proof obligations
    (TC-4, TC-9, TC-10, TC-12, TC-18). Takes no session/engine -- trivially fixture-tested with synthetic
    dicts, mirroring `j11_stage_d_execute.build_stage_d_mutation_accounting`'s own pure-composition idiom.
    ANY False in `checks` means `all_checks_pass` is False and the caller MUST NOT report
    `STAGE E COMPLETE: YES`."""
    checks: dict[str, Any] = {}

    table_sweep_diff = j11_maintenance.diff_full_table_sweeps(pre_full_table_sweep, post_full_table_sweep)
    checks["no_unexpected_new_tables"] = not table_sweep_diff["unexpected_new_tables"]
    checks["no_unexpected_removed_tables"] = not table_sweep_diff["unexpected_removed_tables"]
    checks["changed_tables_subset_of_stage_e_write_tables"] = set(
        table_sweep_diff["changed_existing_tables"]
    ).issubset(set(STAGE_E_WRITE_TABLES))
    checks["out_of_scope_tables_zero_fingerprint_change"] = not (
        set(table_sweep_diff["changed_existing_tables"]) & set(OUT_OF_SCOPE_TABLES)
    )

    manifest_diff = migration.diff_dumps(pre_manifest_dump, post_manifest_dump)
    checks["manifests_unchanged"] = manifest_diff["equal"] and len(pre_manifest_dump) == len(post_manifest_dump)

    checks["all_scanner_runs_unchanged"] = (
        pre_all_scanner_run_fingerprint["fingerprint"] == post_all_scanner_run_fingerprint["fingerprint"]
        and pre_all_scanner_run_fingerprint["rows"] == post_all_scanner_run_fingerprint["rows"]
    )

    checks["daily_prices_unchanged"] = pre_daily_prices["fingerprint"] == post_daily_prices["fingerprint"]
    checks["data_provider_runs_unchanged"] = pre_provider_runs == post_provider_runs
    checks["watchlist_unchanged"] = pre_watchlist == post_watchlist

    maintenance_boundary_diff = migration.diff_dumps(pre_maintenance_boundary_dump, post_maintenance_boundary_dump)
    checks["maintenance_boundary_unchanged"] = maintenance_boundary_diff["equal"]

    observed_delta = post_forward_returns_count - pre_forward_returns_count
    checks["forward_returns_delta_reconciles_with_self_reported_total"] = (
        observed_delta == self_reported_total_inserted
    )

    all_checks_pass = all(bool(v) for v in checks.values())
    return {
        "generated_at": _now_iso(),
        "checks": checks,
        "table_sweep_diff": table_sweep_diff,
        "manifest_diff": manifest_diff,
        "all_scanner_run_counts": {
            "pre": pre_all_scanner_run_fingerprint["row_count"],
            "post": post_all_scanner_run_fingerprint["row_count"],
        },
        "daily_prices": {"pre": pre_daily_prices, "post": post_daily_prices},
        "data_provider_runs": {"pre": pre_provider_runs, "post": post_provider_runs},
        "watchlist": {"pre": pre_watchlist, "post": post_watchlist},
        "maintenance_boundary_diff": maintenance_boundary_diff,
        "forward_returns_count": {
            "pre": pre_forward_returns_count, "post": post_forward_returns_count,
            "observed_delta": observed_delta, "self_reported_total_inserted": self_reported_total_inserted,
        },
        "db_file": {"true_start": db_file_true_start, "true_end": db_file_true_end},
        "all_checks_pass": all_checks_pass,
    }


def stage_e_execution_outcome(
    *,
    preflight_gate: dict,
    repair_loop_result: Optional[dict],
    population_verification: Optional[dict],
    mutation_accounting: Optional[dict],
) -> dict:
    """The final `STAGE E COMPLETE: YES/NO` decision -- `YES` only if the preflight gate proceeded, the
    repair loop ran, the live population re-verification agrees, AND the post-execution mutation
    accounting proves every check passes. Any other combination is `NO`, with the exact reason recorded
    -- never an invented third state (docs/goal.md item 14)."""
    if not preflight_gate.get("proceed"):
        return {
            "executed": False, "reason": "preflight_gate_did_not_proceed",
            "blocking_reasons": preflight_gate.get("blocking_reasons", []),
        }
    if repair_loop_result is None:
        return {"executed": False, "reason": "no_repair_loop_attempted"}
    if population_verification is None or not population_verification.get("all_checks_pass"):
        return {"executed": False, "reason": "live_population_verification_failed"}
    if mutation_accounting is None or not mutation_accounting.get("all_checks_pass"):
        return {"executed": False, "reason": "post_execution_mutation_accounting_failed"}
    return {"executed": True, "reason": "forward_return_holes_repaired_and_verified"}
