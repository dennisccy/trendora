"""app.engine.j11_stage_f_execute -- J-11 Stage F EXECUTION (goal-market-compass iter-21).

`docs/goal.md`'s "OWNER RULING -- J-11 Stage D through Stage G recovery execution AUTHORIZED" (owner,
2026-08-26) item 8 authorizes Stage F, unconditionally, once Stage E has succeeded (iteration 20 --
`runs/goal-market-compass-iter-20/j11-stage-e-execute-outcome.json`: `executed: true`). Stage F is the
dependency-aware derived-CACHE invalidation: classify every `dataset_version`-bearing cache table Stage
D/E's live writes could have made stale, and explicitly DELETE the rows a live, evidence-grounded reading
proves are actually at risk -- so nothing in the database can silently serve pre-repair content once the
app eventually reboots -- while touching no raw price, snapshot, or manifest row.

**The correctness risk this module exists to fix (BACKGROUND finding 4):**
`data_manager.availability_from_storage`'s "a row exists, its stamp does not match the current one, but
no ingest job is in flight" branch (`data_manager.py:1741-1747`/`:1760-1763`) serves the SAME stale stored
row with `stale: False` -- correct behavior for its designed case (an ordinary stamp bump with nothing
running to chase it), but WRONG the first time `/api/data/availability` loads after a post-Stage-G reboot
with no ingest job running: it would silently serve the PRE-INCIDENT heatmap labeled current. Leaving
`availability_cache`'s stale row in place is a live AG-3/AG-8 risk, not hygiene.

**The decisive classification signal is `created_at`, never the `dataset_version` stamp string alone**
(iter-15b's "never trust a single fingerprint alone" lesson, and the TC-7 collision trap this module's
tests prove against): a delete-and-recreate of `scanner_runs`/`forward_returns` that reproduces an
IDENTICAL stamp string is still detected as stale by comparing every stored row's `created_at` against
Stage D's frozen execution-start instant -- a row predating that instant describes a world Stage D/E have
since changed, regardless of what its stamp string happens to read.

**membership_timeline_cache is the one table with a genuine, proof-gated tradeoff** (BACKGROUND finding
5): deleting its stale row forces the next real request onto `_membership_timeline`'s documented >300s
full O(dates x pool) cold-compute sweep. `evaluate_membership_timeline_incremental_reuse_safety` proves,
live and read-only, whether `data_manager.membership_timeline_cached`'s own MISS-repair logic
(`data_manager.py:894-963`) would instead take the CHEAP "historical gap-insert" branch (reusing cached
per-date `excluded` tallies) -- reusing `data_manager._membership_bars_are_forward_only`/
`_parse_membership_stamp` DIRECTLY (never a second implementation of that exact correctness proof). Only
when that proof holds does this table get `preserve_for_incremental_reuse`; otherwise it falls back to
`explicit_delete` like every other stale cache.

Sequence (composed by the CLI script, mirroring `j11_stage_e_execute.py`'s idiom exactly):

  1. Fresh, READ-ONLY preflight -- reusing `j11_stage_d_execute.recheck_maintenance_boundary_and_guard`
     and `j11_stage_e_execute.check_engine_identity_matches_stage_d`/`confirm_manifests_unchanged`
     directly (never reimplemented, called by the CLI script); this module adds
     `confirm_stage_e_complete_and_unrestamped` (per incident date: Stage D's own run id, unrestamped,
     carrying the EXACT `ForwardReturn` count Stage E's own population report recorded -- including run
     3158's legitimate 0), `derive_cache_table_inventory` (genuine runtime introspection, never a
     hardcoded list -- TC-3), `derive_stage_d_execution_start_instant` (live re-derivation, never a
     hardcoded citation), and `confirm_no_cache_row_at_or_after_stage_d_start` (the "gravest" check: an
     unexplained cache write during maintenance isolation halts the WHOLE attempt).
     `stage_f_preflight_gate_verdict` combines everything into one go/no-go.
  2. `classify_cache_table`, once per inventoried table -- recomputes the table's CURRENT live stamp via
     its ACTUAL writer/version function (`research._dataset_version` for the 3 broad-stamp caches,
     `research._membership_dataset_version` for `availability_cache`/`coverage_snapshot`/
     `membership_timeline_cache`, `indexes.index_series_dataset_version` for `index_series_cache`),
     reads every distinct stored stamp + every row's `created_at`, and assigns one disposition:
     `explicit_delete` (the default for 5 of the 7 tables -- decided by `created_at`, not the stamp),
     `prove_unaffected_leave_alone` (`index_series_cache`, when its own re-derived stamp still equals the
     stored one), or `preserve_for_incremental_reuse` (`membership_timeline_cache`, ONLY when the live
     incremental-reuse proof holds).
  3. `execute_stage_f_cache_disposition` -- the ONE authorized write: deletes every row in every table
     classified `explicit_delete` (the preflight already proves every row in these tables predates Stage
     D's start, so "delete everything" IS "delete exactly the already-proven-stale rows"); zero write to
     any other table.
  4. `live_verify_cache_dispositions` -- post-write, read-only: deleted tables hold zero rows; preserved
     tables are row-count-unchanged.
  5. `build_stage_f_mutation_accounting` -- proves `changed_existing_tables` is a subset of exactly the
     tables classified `explicit_delete` (a set this run computes from live classification, never a fixed
     literal the way Stage D/E's write-table sets were, since WHICH tables get deleted is itself
     data-driven), and every other table (the 10 canonical J-11-protected tables, plus any cache table
     NOT classified `explicit_delete`) shows zero fingerprint change.
  6. `stage_f_execution_outcome` -- the final `STAGE F COMPLETE: YES/NO` decision, never an invented third
     state.

Never touches (imports nothing from, calls nothing in): `app/api/*`, `scoring.py`, `compass.py`,
`data_manager.py`'s write paths, `scanner.py`, or any canonical producer/serving function's CODE (Stage F
reads `data_manager.availability_from_storage`/`coverage_from_storage`'s DOCUMENTED behavior and the
narrow stamp functions those modules already export -- it does not modify a line of any of them).
"""
from __future__ import annotations

import json
from datetime import date as date_cls
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import delete as sa_delete
from sqlalchemy import func
from sqlmodel import Session, SQLModel, select

from app.config import Config
from app.engine import data_manager
from app.engine import indexes
from app.engine import j11_maintenance
from app.engine import j11_schema_migration as migration
from app.engine import research
from app.models import (
    AvailabilityCache,
    CoverageSnapshot,
    EventStudyCache,
    ForwardAggregateCache,
    ForwardReturn,
    IndexSeriesCache,
    MarketPhaseCache,
    MembershipTimelineCache,
    ScannerRun,
)

# The seven tables confirmed exhaustive at planning time (2026-08-27, by grep against app/models.py --
# see docs/goal.md BACKGROUND finding 1). This is an EXPECTATION used only for the inventory step's
# honest comparison/reporting -- the inventory itself (`derive_cache_table_inventory`) is genuine runtime
# introspection, never driven by this tuple (TC-3).
EXPECTED_CACHE_TABLE_NAMES: tuple[str, ...] = (
    "event_study_cache", "market_phase_cache", "forward_aggregate_cache", "index_series_cache",
    "membership_timeline_cache", "availability_cache", "coverage_snapshot",
)

# The concrete SQLModel class per known table name -- used by classification/execution/verification
# (typed ORM queries, matching every other query pattern in this codebase) for the tables the inventory
# step's genuine introspection actually finds. A table name absent from this dict is classified
# `unclassified_unknown_family` rather than guessed at (see `classify_cache_table`).
CACHE_TABLE_MODEL_BY_NAME: dict[str, type] = {
    "event_study_cache": EventStudyCache,
    "market_phase_cache": MarketPhaseCache,
    "forward_aggregate_cache": ForwardAggregateCache,
    "index_series_cache": IndexSeriesCache,
    "membership_timeline_cache": MembershipTimelineCache,
    "availability_cache": AvailabilityCache,
    "coverage_snapshot": CoverageSnapshot,
}

# Which live-stamp function each table's ACTUAL writer/version call site uses (docs/goal.md BACKGROUND
# finding 2 -- verified at the call site, never trusted from a class docstring; MembershipTimelineCache's
# own class-level docstring is stale and would give the WRONG family if trusted).
CACHE_KEY_FAMILY: dict[str, str] = {
    "event_study_cache": "broad",
    "market_phase_cache": "broad",
    "forward_aggregate_cache": "broad",
    "index_series_cache": "index_narrow",
    "membership_timeline_cache": "narrow",
    "availability_cache": "narrow",
    "coverage_snapshot": "narrow",
}

# The ten tables Stage F must never write to and must show zero fingerprint change on (mirrors
# `j11_stage_e_execute.OUT_OF_SCOPE_TABLES`, widened by the two tables Stage E itself was authorized to
# touch -- `forward_returns` -- plus `next_session_manifests`, spelled out explicitly rather than derived
# so a future schema addition never silently narrows this list).
OUT_OF_SCOPE_TABLES: tuple[str, ...] = (
    "daily_prices", "scanner_runs", "scanner_results", "sector_scores", "theme_scores", "forward_returns",
    "data_provider_runs", "watchlist", "maintenance_boundaries", "next_session_manifests",
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _iso_or_none(value: Optional[datetime]) -> Optional[str]:
    """Same tzinfo-safe re-serialization `j11_maintenance._utc_isoformat` uses (SQLite drops tzinfo on
    round-trip) -- an honest `None` passes through unchanged, never a fabricated timestamp. Every
    timestamp this module reads from the database goes through this ONE function, so every string it
    hands to `_parse_iso_or_none` downstream is consistently tz-aware -- never a naive-vs-aware
    comparison surprise against a caller-supplied `stage_d_start_instant`."""
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def _parse_iso_or_none(value: Optional[str]) -> Optional[datetime]:
    return datetime.fromisoformat(value) if value else None


def _timestamp_attr_and_name(model: Any) -> tuple[Any, str]:
    """The model's own audit-timestamp column -- `created_at` for six of the seven tables,
    `computed_at` for `CoverageSnapshot` (`app/models.py:954`). Resolved by attribute presence, not a
    per-table hardcoded name, so a future rename is caught rather than silently misread."""
    if hasattr(model, "created_at"):
        return model.created_at, "created_at"
    return model.computed_at, "computed_at"


# ================================================================================================
# Step 1a -- genuine runtime introspection (TC-3): never a hardcoded list
# ================================================================================================


def derive_cache_table_inventory(metadata: Optional[Any] = None) -> dict:
    """Introspects SQLModel metadata (defaulting to the REAL `SQLModel.metadata`, i.e. every table class
    currently defined across the whole app -- including `app.models`) at RUNTIME for every table carrying
    a `dataset_version` column -- never a hardcoded list (docs/goal.md J-11 step 6, TC-3). A table is
    included iff its CURRENT schema declares the column; injecting a different `metadata` (a fixture-built
    `sqlalchemy.MetaData()`) changes the returned set, proving this is genuine introspection wearing no
    hardcoded-list costume."""
    md = metadata if metadata is not None else SQLModel.metadata
    table_names = sorted(name for name, table in md.tables.items() if "dataset_version" in table.columns)
    expected_sorted = sorted(EXPECTED_CACHE_TABLE_NAMES)
    return {
        "generated_at": _now_iso(),
        "table_names": table_names,
        "table_count": len(table_names),
        "expected_table_names": expected_sorted,
        "matches_expected_seven": table_names == expected_sorted,
    }


# ================================================================================================
# Step 1b -- Stage E end-state re-verification (mirrors confirm_stage_d_runs_present_unrestamped's
# shape, widened to check the EXACT recorded ForwardReturn count rather than merely zero)
# ================================================================================================


def confirm_stage_e_complete_and_unrestamped(
    session: Session,
    *,
    expected_run_id_by_date: dict[str, int],
    expected_forward_return_count_by_run_id: dict[str, int],
    frozen_engine_identity: str,
) -> dict:
    """For every one of Stage D's 11 rebuilt incident dates, confirm the live `ScannerRun` row is
    present, carries the SAME `id` Stage D's own recorded regeneration evidence assigned to that date,
    carries the SAME frozen `engine_identity`, and currently holds EXACTLY the `ForwardReturn` count
    Stage E's own population report recorded for that run id (including a legitimate `0` -- e.g. run
    3158, sitting on the frontier with no observable horizon -- never treated as a gap). Read-only --
    never writes, never restamps."""
    per_date: dict[str, dict] = {}
    for date_str, expected_run_id in sorted(expected_run_id_by_date.items()):
        one_date = date_cls.fromisoformat(date_str)
        row = session.exec(
            select(ScannerRun.id, ScannerRun.asof_date, ScannerRun.engine_identity, ScannerRun.created_at)
            .where(ScannerRun.asof_date == one_date)
        ).first()
        present = row is not None
        observed_id = int(row[0]) if present else None
        observed_identity = row[2] if present else None
        fr_count = (
            int(session.scalar(select(func.count()).select_from(ForwardReturn).where(ForwardReturn.run_id == observed_id)) or 0)
            if present else None
        )
        expected_fr_count = expected_forward_return_count_by_run_id.get(str(expected_run_id))
        id_matches = present and observed_id == expected_run_id
        identity_matches = present and observed_identity == frozen_engine_identity
        fr_count_matches = present and expected_fr_count is not None and fr_count == expected_fr_count
        per_date[date_str] = {
            "expected_run_id": expected_run_id,
            "present": present,
            "observed_run_id": observed_id,
            "id_matches": id_matches,
            "observed_engine_identity": observed_identity,
            "identity_matches": identity_matches,
            "observed_created_at": _iso_or_none(row[3]) if present else None,
            "expected_forward_return_count": expected_fr_count,
            "observed_forward_return_count": fr_count,
            "forward_return_count_matches": fr_count_matches,
            "ok": present and id_matches and identity_matches and fr_count_matches,
        }
    ok = bool(per_date) and all(v["ok"] for v in per_date.values())
    return {"checked_at": _now_iso(), "per_date": per_date, "ok": ok}


# ================================================================================================
# Step 1c -- Stage D's frozen execution-start instant, re-derived live (never hardcoded)
# ================================================================================================


def derive_stage_d_execution_start_instant(session: Session, incident_run_ids: list[int]) -> dict:
    """Live, read-only re-derivation of Stage D's frozen execution-start instant -- the `created_at` of
    the FIRST `ScannerRun` Stage D actually inserted (`MIN(created_at)` over the given ids). Never a
    hardcoded citation (docs/goal.md classify_cache_table bullet: "never hardcode the citation").
    `incident_run_ids` comes from Stage D's OWN recorded regeneration evidence
    (`per_date_results[*].run_id`), loaded by the caller -- this function performs no file I/O."""
    value = session.scalar(select(func.min(ScannerRun.created_at)).where(ScannerRun.id.in_(incident_run_ids)))
    return {
        "generated_at": _now_iso(),
        "incident_run_ids": sorted(incident_run_ids),
        "stage_d_execution_start_instant": _iso_or_none(value),
    }


# ================================================================================================
# Step 1d -- per-table snapshot (row count, distinct stamps, audit-timestamp bounds) -- reused by
# BOTH the late-row hygiene check and per-table classification
# ================================================================================================


def capture_cache_table_snapshot(session: Session, table_name: str) -> dict:
    """A read-only snapshot of one cache table: row count, every DISTINCT stored `dataset_version` with
    its own row count + timestamp bounds, and the table-wide MAX timestamp (the decisive value for the
    late-row hygiene check -- see `confirm_no_cache_row_at_or_after_stage_d_start`). Column-projected
    aggregates only -- never a full-row hydration (AG-8), even for `market_phase_cache`'s 1,000+ rows."""
    model = CACHE_TABLE_MODEL_BY_NAME[table_name]
    ts_attr, ts_attr_name = _timestamp_attr_and_name(model)
    row_count = int(session.scalar(select(func.count()).select_from(model)) or 0)
    stamp_rows = session.exec(
        select(model.dataset_version, func.count(), func.min(ts_attr), func.max(ts_attr))
        .group_by(model.dataset_version)
    ).all()
    distinct_stamps = [
        {
            "dataset_version": r[0], "count": int(r[1]),
            "min_timestamp": _iso_or_none(r[2]), "max_timestamp": _iso_or_none(r[3]),
        }
        for r in stamp_rows
    ]
    overall_max_ts = session.scalar(select(func.max(ts_attr)))
    return {
        "table_name": table_name,
        "timestamp_column": ts_attr_name,
        "row_count": row_count,
        "distinct_stamps": distinct_stamps,
        "max_timestamp": _iso_or_none(overall_max_ts),
    }


# ================================================================================================
# Step 1e -- the "gravest" preflight check: no cache row written during maintenance isolation
# ================================================================================================


def confirm_no_cache_row_at_or_after_stage_d_start(
    snapshots_by_table: dict[str, dict], *, stage_d_start_instant: datetime,
) -> dict:
    """For the six tables whose stamp depends on `scanner_runs` and/or `forward_returns`
    (`snapshots_by_table` must already EXCLUDE `index_series_cache` -- its stamp depends only on
    `daily_prices`, proven byte-unchanged by Stage D/E's own mutation accounting, so it carries no
    scanner-run-derived hygiene obligation): every stored row's timestamp must be STRICTLY EARLIER than
    Stage D's frozen execution-start instant. A hit here means an unexplained write happened during
    maintenance isolation -- graver than a routine classification disagreement -- and the caller MUST
    halt the WHOLE attempt before any write, never silently delete or silently accept it. Fail-closed on
    an empty `snapshots_by_table` (mirrors `confirm_stage_d_runs_present_unrestamped`'s
    `bool(per_date) and all(...)` idiom, praised sound in the iter-20 audit)."""
    per_table: dict[str, dict] = {}
    for name, snap in snapshots_by_table.items():
        max_ts = _parse_iso_or_none(snap["max_timestamp"])
        table_ok = max_ts is None or max_ts < stage_d_start_instant
        per_table[name] = {"max_timestamp": snap["max_timestamp"], "ok": table_ok}
    ok = bool(per_table) and all(v["ok"] for v in per_table.values())
    return {
        "checked_at": _now_iso(),
        "stage_d_start_instant": _iso_or_none(stage_d_start_instant),
        "per_table": per_table,
        "ok": ok,
    }


# ================================================================================================
# Step 1f -- the combined Stage F preflight gate
# ================================================================================================


def stage_f_preflight_gate_verdict(
    *,
    boundary_recheck: dict,
    stage_e_check: dict,
    identity_check: dict,
    manifest_check: dict,
    inventory: dict,
    late_rows_check: dict,
) -> dict:
    """The single go/no-go decision for Stage F EXECUTION. Any one of the six checks failing means
    `proceed: False`, and the caller MUST perform zero writes to any table."""
    boundary_ok = bool(boundary_recheck.get("ok"))
    stage_e_ok = bool(stage_e_check.get("ok"))
    identity_ok = bool(identity_check.get("ok"))
    manifest_ok = bool(manifest_check.get("ok"))
    inventory_ok = bool(inventory.get("matches_expected_seven"))
    late_rows_ok = bool(late_rows_check.get("ok"))
    proceed = boundary_ok and stage_e_ok and identity_ok and manifest_ok and inventory_ok and late_rows_ok

    blocking_reasons: list[str] = []
    if not boundary_ok:
        blocking_reasons.append("maintenance_boundary_or_guard_recheck_failed")
    if not stage_e_ok:
        blocking_reasons.append("stage_e_runs_not_present_unrestamped_or_forward_return_count_mismatch")
    if not identity_ok:
        blocking_reasons.append("engine_identity_drifted_since_stage_d")
    if not manifest_ok:
        blocking_reasons.append("next_session_manifests_changed_since_stage_d")
    if not inventory_ok:
        blocking_reasons.append(f"cache_table_inventory_mismatch:{inventory.get('table_names')}")
    if not late_rows_ok:
        blocking_reasons.append("cache_row_created_at_or_after_stage_d_start_detected")

    return {
        "generated_at": _now_iso(),
        "proceed": proceed,
        "boundary_ok": boundary_ok,
        "stage_e_ok": stage_e_ok,
        "identity_ok": identity_ok,
        "manifest_ok": manifest_ok,
        "inventory_ok": inventory_ok,
        "late_rows_ok": late_rows_ok,
        "blocking_reasons": blocking_reasons,
    }


# ================================================================================================
# Step 2a -- the membership_timeline_cache incremental-reuse proof (the one genuine tradeoff)
# ================================================================================================


def evaluate_membership_timeline_incremental_reuse_safety(
    session: Session, config: Config, *, stored_payload_json: str, stored_dataset_version: str,
) -> dict:
    """Live, read-only proof of whether `data_manager.membership_timeline_cached`'s own MISS-repair
    logic (`data_manager.py:894-963`) would take the CHEAP "historical gap-insert" branch (reusing
    per-date `excluded` tallies via `reuse_excluded_by_date`, `data_manager.py:955-963`) rather than
    either the narrower "append-forward" branch (`:921-933`) or the expensive, previously-hang-inducing
    full O(dates x pool) cold compute (`:976`) -- for THIS stale row against the CURRENT live
    snapshot-date set. Calls `data_manager._membership_bars_are_forward_only` DIRECTLY (reuse, never a
    second implementation of the SAME correctness proof `membership_timeline_cached` itself relies on)."""
    prev_payload = json.loads(stored_payload_json)
    prev_dates = sorted(p["date"] for p in prev_payload.get("points", []))
    prev_dates_set = set(prev_dates)

    live_dates = sorted(d.isoformat() for d in session.exec(select(ScannerRun.asof_date)).all())
    live_dates_set = set(live_dates)

    new_dates = [d for d in live_dates if d not in prev_dates_set]
    missing_dates = [d for d in prev_dates if d not in live_dates_set]

    fresh_stamp = research._membership_dataset_version(session, config)
    append_forward = bool(new_dates) and not missing_dates and (not prev_dates or min(new_dates) > prev_dates[-1])
    bars_forward_only = data_manager._membership_bars_are_forward_only(session, stored_dataset_version, fresh_stamp)

    safe_for_incremental_reuse = (not append_forward) and bool(new_dates) and (not missing_dates) and bars_forward_only

    if safe_for_incremental_reuse:
        reason = (
            f"{len(new_dates)} new date(s) ({new_dates[0]}..{new_dates[-1]}), 0 missing date(s), "
            f"append_forward=False (min(new_dates)={new_dates[0]!r} is not later than the cached tail "
            f"{prev_dates[-1] if prev_dates else None!r}), bars_are_forward_only=True -- the next real "
            "request's MISS would take the cheap historical-gap-insert reuse branch, never the "
            "documented >300s full cold-compute sweep; safe to preserve"
        )
    elif append_forward:
        reason = (
            "append_forward evaluated True -- the narrower fast path, not the 'historical gap-insert' "
            "branch this disposition specifically requires proven; falling back to deletion"
        )
    elif missing_dates:
        reason = (
            f"{len(missing_dates)} previously-cached date(s) are missing from the live snapshot set -- "
            "neither fast path is provably safe; falling back to deletion"
        )
    elif not bars_forward_only:
        reason = (
            "the bars-forward-only proof did not hold -- reusing cached excluded tallies would be "
            "unsafe; falling back to deletion"
        )
    else:
        reason = "no new dates since the cached generation -- nothing to gain from preserving; falling back to deletion"

    return {
        "generated_at": _now_iso(),
        "stored_dataset_version": stored_dataset_version,
        "fresh_dataset_version": fresh_stamp,
        "prev_date_count": len(prev_dates),
        "prev_max_date": prev_dates[-1] if prev_dates else None,
        "live_date_count": len(live_dates),
        "new_dates": new_dates,
        "missing_dates": missing_dates,
        "append_forward": append_forward,
        "bars_are_forward_only": bars_forward_only,
        "safe_for_incremental_reuse": safe_for_incremental_reuse,
        "reason": reason,
    }


# ================================================================================================
# Step 2b -- per-table classification
# ================================================================================================


def compute_live_stamp_for_table(session: Session, table_name: str, config: Config) -> Optional[str]:
    """Dispatches to the table's ACTUAL writer/version function -- verified at the call site (docs/goal.md
    BACKGROUND finding 2), never trusted from a class docstring (`MembershipTimelineCache`'s own is
    stale). Returns `None` for a table not in the known key-family map -- the caller treats that as a
    blocking anomaly, never a guessed formula."""
    family = CACHE_KEY_FAMILY.get(table_name)
    if family == "broad":
        return research._dataset_version(session)
    if family == "narrow":
        return research._membership_dataset_version(session, config)
    if family == "index_narrow":
        return indexes.index_series_dataset_version(session, config)
    return None


def classify_cache_table(
    session: Session, config: Config, table_name: str, *, stage_d_start_instant: datetime,
) -> dict:
    """Recomputes the table's CURRENT live stamp, reads every distinct stored stamp + the table's audit
    timestamps, and assigns ONE disposition with a stated reason. The DECISIVE signal for the five
    default tables is `created_at` (a row predating Stage D's start is stale regardless of whether its
    stamp string happens to collide with the fresh one -- the TC-7 collision-trap proof), never the stamp
    comparison alone; `stamp_matches_live` is still recorded as corroborating evidence."""
    if table_name not in CACHE_TABLE_MODEL_BY_NAME:
        return {
            "table_name": table_name, "family": None, "disposition": "unclassified_unknown_family",
            "reason": f"table {table_name!r} is not in the known cache-table model map -- refusing to guess a stamp formula or a deletion scope for it",
            "live_stamp": None, "stamp_matches_live": False, "snapshot": None,
        }

    snapshot = capture_cache_table_snapshot(session, table_name)
    live_stamp = compute_live_stamp_for_table(session, table_name, config)
    stamp_matches_live = live_stamp is not None and any(
        s["dataset_version"] == live_stamp for s in snapshot["distinct_stamps"]
    )
    max_ts = _parse_iso_or_none(snapshot["max_timestamp"])
    all_rows_created_before_stage_d_start = max_ts is None or max_ts < stage_d_start_instant

    base = {
        "table_name": table_name,
        "family": CACHE_KEY_FAMILY.get(table_name),
        "live_stamp": live_stamp,
        "stamp_matches_live": stamp_matches_live,
        "all_rows_created_before_stage_d_start": all_rows_created_before_stage_d_start,
        "snapshot": snapshot,
    }

    if table_name == "index_series_cache":
        if live_stamp is not None and stamp_matches_live and snapshot["row_count"] <= 1:
            disposition, reason = "prove_unaffected_leave_alone", (
                f"own narrow index-symbol stamp re-derived fresh ({live_stamp}) equals the stored row's "
                "stamp -- daily_prices is proven byte-unchanged by Stage D's/Stage E's own mutation "
                "accounting, so this table's inputs never moved; zero deletion"
            )
        else:
            disposition, reason = "explicit_delete", (
                "the fresh narrow index-symbol stamp does not match the stored row (or more than one row "
                "is stored) -- cannot prove this table is unaffected; falling back to deletion rather "
                "than guessing"
            )
        return {**base, "disposition": disposition, "reason": reason}

    if table_name == "membership_timeline_cache":
        if snapshot["row_count"] == 0:
            disposition, reason, reuse_eval = "explicit_delete", "no stored row to preserve", None
        else:
            stored_stamp = snapshot["distinct_stamps"][0]["dataset_version"] if len(snapshot["distinct_stamps"]) == 1 else None
            if stored_stamp is None:
                disposition, reason, reuse_eval = "explicit_delete", (
                    "more than one distinct stamp is stored for a single-row-by-design cache -- refusing "
                    "to guess which row the incremental-reuse proof should target"
                ), None
            else:
                payload_row = session.scalar(
                    select(MembershipTimelineCache.payload_json)
                    .where(MembershipTimelineCache.dataset_version == stored_stamp)
                )
                reuse_eval = evaluate_membership_timeline_incremental_reuse_safety(
                    session, config, stored_payload_json=payload_row, stored_dataset_version=stored_stamp,
                )
                if reuse_eval["safe_for_incremental_reuse"]:
                    disposition, reason = "preserve_for_incremental_reuse", reuse_eval["reason"]
                else:
                    disposition, reason = "explicit_delete", f"incremental-reuse proof did not hold -- {reuse_eval['reason']}"
        return {**base, "disposition": disposition, "reason": reason, "membership_reuse_evaluation": reuse_eval}

    # The five broad/narrow "default explicit_delete" tables: event_study_cache, market_phase_cache,
    # forward_aggregate_cache, availability_cache, coverage_snapshot.
    if not all_rows_created_before_stage_d_start:
        disposition, reason = "blocked_late_row_detected", (
            "at least one stored row's timestamp is at or after Stage D's frozen execution-start instant "
            "-- an unexplained write during maintenance isolation; refusing to classify, the whole "
            "attempt must halt (see confirm_no_cache_row_at_or_after_stage_d_start)"
        )
    else:
        disposition, reason = "explicit_delete", (
            f"{snapshot['row_count']} stored row(s) across {len(snapshot['distinct_stamps'])} distinct "
            f"stamp(s), all created before Stage D's start ({_iso_or_none(stage_d_start_instant)}) -- "
            f"proven stale by predating the repair (decisive signal: created_at, per the collision-trap "
            f"proof; stamp_matches_live={stamp_matches_live} is corroborating, not the gate)"
        )
    return {**base, "disposition": disposition, "reason": reason}


# ================================================================================================
# Step 3 -- the ONE authorized write
# ================================================================================================


def execute_stage_f_cache_disposition(session: Session, *, dispositions: dict[str, dict]) -> dict:
    """The ONE authorized write: for every table classified `explicit_delete`, deletes ALL of its rows
    (the preflight already proves every row in these tables predates Stage D's start, so a full-table
    delete IS "delete exactly the already-proven-stale rows", never a broader wipe). Zero write to any
    table classified otherwise. Commits once at the end (a single maintenance transaction, mirroring
    Stage D/E's own per-call-then-commit idiom for a bounded operation)."""
    per_table: dict[str, dict] = {}
    for table_name, record in dispositions.items():
        if record["disposition"] != "explicit_delete":
            per_table[table_name] = {
                "disposition": record["disposition"], "attempted_write": False, "rows_deleted": 0,
            }
            continue
        model = CACHE_TABLE_MODEL_BY_NAME[table_name]
        pre_count = record["snapshot"]["row_count"]
        result = session.execute(sa_delete(model))
        rows_deleted = result.rowcount if result.rowcount is not None and result.rowcount >= 0 else pre_count
        per_table[table_name] = {
            "disposition": "explicit_delete", "attempted_write": True,
            "pre_count": pre_count, "rows_deleted": int(rows_deleted),
        }
    session.commit()
    return {
        "generated_at": _now_iso(),
        "per_table": per_table,
        "total_rows_deleted": sum(v["rows_deleted"] for v in per_table.values()),
    }


# ================================================================================================
# Step 4 -- post-write, live, read-only verification
# ================================================================================================


def live_verify_cache_dispositions(session: Session, *, dispositions: dict[str, dict]) -> dict:
    """Post-write, read-only: every table classified `explicit_delete` now holds zero rows; every other
    (preserved) table's row count is UNCHANGED from its pre-write snapshot."""
    per_table: dict[str, dict] = {}
    ok = True
    for table_name, record in dispositions.items():
        if table_name not in CACHE_TABLE_MODEL_BY_NAME:
            continue
        model = CACHE_TABLE_MODEL_BY_NAME[table_name]
        post_count = int(session.scalar(select(func.count()).select_from(model)) or 0)
        if record["disposition"] == "explicit_delete":
            table_ok = post_count == 0
            per_table[table_name] = {"disposition": "explicit_delete", "post_count": post_count, "ok": table_ok}
        else:
            expected = record["snapshot"]["row_count"] if record.get("snapshot") else 0
            table_ok = post_count == expected
            per_table[table_name] = {
                "disposition": record["disposition"], "post_count": post_count,
                "expected_unchanged_count": expected, "ok": table_ok,
            }
        ok = ok and table_ok
    return {"generated_at": _now_iso(), "per_table": per_table, "ok": bool(per_table) and ok}


# ================================================================================================
# Step 5 -- post-execution mutation accounting
# ================================================================================================


def build_stage_f_mutation_accounting(
    *,
    pre_full_table_sweep: dict,
    post_full_table_sweep: dict,
    dispositions: dict[str, dict],
    pre_manifest_dump: list,
    post_manifest_dump: list,
    pre_daily_prices: dict,
    post_daily_prices: dict,
    pre_provider_runs: dict,
    post_provider_runs: dict,
    pre_watchlist: dict,
    post_watchlist: dict,
    pre_maintenance_boundary_dump: list,
    post_maintenance_boundary_dump: list,
    db_file_true_start: dict,
    db_file_true_end: dict,
) -> dict:
    """Pure composition of every pre/post capture into the DoD's mutation-accounting proof obligations
    (TC-11, TC-12). Takes no session/engine -- trivially fixture-tested with synthetic dicts, mirroring
    `j11_stage_e_execute.build_stage_e_mutation_accounting`'s own pure-composition idiom. UNLIKE Stage
    D/E, the authorized write-table set is DATA-DRIVEN (computed from live classification, not a fixed
    literal) -- `changed_tables_subset_of_explicit_delete_set` derives it from `dispositions` itself. ANY
    False in `checks` means `all_checks_pass` is False and the caller MUST NOT report
    `STAGE F COMPLETE: YES`."""
    checks: dict[str, Any] = {}

    table_sweep_diff = j11_maintenance.diff_full_table_sweeps(pre_full_table_sweep, post_full_table_sweep)
    checks["no_unexpected_new_tables"] = not table_sweep_diff["unexpected_new_tables"]
    checks["no_unexpected_removed_tables"] = not table_sweep_diff["unexpected_removed_tables"]

    explicit_delete_tables = {name for name, d in dispositions.items() if d["disposition"] == "explicit_delete"}
    checks["changed_tables_subset_of_explicit_delete_set"] = set(
        table_sweep_diff["changed_existing_tables"]
    ).issubset(explicit_delete_tables)

    preserved_cache_tables = set(dispositions) - explicit_delete_tables
    out_of_scope = set(OUT_OF_SCOPE_TABLES) | preserved_cache_tables
    checks["out_of_scope_tables_zero_fingerprint_change"] = not (
        set(table_sweep_diff["changed_existing_tables"]) & out_of_scope
    )

    manifest_diff = migration.diff_dumps(pre_manifest_dump, post_manifest_dump)
    checks["manifests_unchanged"] = manifest_diff["equal"] and len(pre_manifest_dump) == len(post_manifest_dump)

    checks["daily_prices_unchanged"] = pre_daily_prices["fingerprint"] == post_daily_prices["fingerprint"]
    checks["data_provider_runs_unchanged"] = pre_provider_runs == post_provider_runs
    checks["watchlist_unchanged"] = pre_watchlist == post_watchlist

    maintenance_boundary_diff = migration.diff_dumps(pre_maintenance_boundary_dump, post_maintenance_boundary_dump)
    checks["maintenance_boundary_unchanged"] = maintenance_boundary_diff["equal"]

    all_checks_pass = all(bool(v) for v in checks.values())
    return {
        "generated_at": _now_iso(),
        "checks": checks,
        "explicit_delete_tables": sorted(explicit_delete_tables),
        "preserved_cache_tables": sorted(preserved_cache_tables),
        "table_sweep_diff": table_sweep_diff,
        "manifest_diff": manifest_diff,
        "daily_prices": {"pre": pre_daily_prices, "post": post_daily_prices},
        "data_provider_runs": {"pre": pre_provider_runs, "post": post_provider_runs},
        "watchlist": {"pre": pre_watchlist, "post": post_watchlist},
        "maintenance_boundary_diff": maintenance_boundary_diff,
        "db_file": {"true_start": db_file_true_start, "true_end": db_file_true_end},
        "all_checks_pass": all_checks_pass,
    }


# ================================================================================================
# Step 6 -- the final outcome (no third state)
# ================================================================================================


def stage_f_execution_outcome(
    *,
    preflight_gate: dict,
    dispositions: Optional[dict[str, dict]],
    execution_result: Optional[dict],
    verification_result: Optional[dict],
    mutation_accounting: Optional[dict],
) -> dict:
    """The final `STAGE F COMPLETE: YES/NO` decision -- `YES` only if the preflight gate proceeded,
    dispositions were computed for every inventoried table with none `blocked_late_row_detected` or
    `unclassified_unknown_family`, the write executed, live verification agrees, AND the post-execution
    mutation accounting proves every check passes. Any other combination is `NO`, with the exact reason
    recorded -- never an invented third state (docs/goal.md item 14)."""
    if not preflight_gate.get("proceed"):
        return {
            "executed": False, "reason": "preflight_gate_did_not_proceed",
            "blocking_reasons": preflight_gate.get("blocking_reasons", []),
        }
    if not dispositions:
        return {"executed": False, "reason": "no_dispositions_computed"}
    unresolved = sorted(
        name for name, d in dispositions.items()
        if d["disposition"] in ("blocked_late_row_detected", "unclassified_unknown_family")
    )
    if unresolved:
        return {"executed": False, "reason": "unresolved_table_classification", "unresolved_tables": unresolved}
    if execution_result is None:
        return {"executed": False, "reason": "no_execution_attempted"}
    if verification_result is None or not verification_result.get("ok"):
        return {"executed": False, "reason": "post_execution_live_verification_failed"}
    if mutation_accounting is None or not mutation_accounting.get("all_checks_pass"):
        return {"executed": False, "reason": "post_execution_mutation_accounting_failed"}
    return {"executed": True, "reason": "cache_dispositions_classified_applied_and_verified"}
