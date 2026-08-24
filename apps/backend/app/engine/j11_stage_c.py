"""app.engine.j11_stage_c -- J-11 Stage C precondition/evidence tooling (goal-market-compass iter-13).

`docs/goal.md` J-11 step 11's "## OWNER AUTHORIZATION -- J-11 Stage C (owner, 2026-08-24)" block
(rulings C1-C12) authorizes exactly ONE destructive action this iteration: the bounded, exact-11-date
clear of Layer 2 derived state via `app.engine.data_manager.clear_snapshot_dates`. Everything in THIS
module is read-only precondition/evidence tooling around that one call -- it deletes, updates, and
inserts nothing:

  - `capture_stage_c_preflight` (ruling C2) -- re-derives live state fresh (git HEAD, the J-11 contract
    text hash, a NEW Stage C attempt id wrapping the re-derived Stage B2 `engine_identity`, the 11-date
    inventory, the manifest table's DDL/index/full dump, and every table's row count), never trusting a
    prior iteration's certified figures.
  - `compare_preflight_to_certified` (TC-1/TC-2) -- the preflight comparison gate against iteration 12's
    certified live state. ANY invariant failing here means the caller MUST stop before the first
    destructive statement.
  - `check_c1_date_set_boundary` / `extract_incident_date_lists` (TC-3) -- proves the code's
    `INCIDENT_DATES` list is byte-identical to BOTH goal.md's "the incident date set -- all 11" bullet
    and the C1 restatement; a disagreement between the two, or either date list going missing, halts
    before any deletion (fail-closed anchor-based extraction -- never a broad guess).
  - `capture_intended_delete_set` (ruling C9) -- the exact per-table row-id set to be removed, captured
    and persisted BEFORE `clear_snapshot_dates` runs, so the post-delete evidence has something concrete
    to be checked against.
  - `capture_layer2_population_fingerprints` / `incident_scoped_counts` / `small_table_id_snapshot` /
    `build_mutation_accounting` -- the post-delete mutation-accounting proof: per-table PRE/DELETED/POST
    counts split incident vs. non-incident, an explicit ID-set-derived diff (never aggregate counts
    alone), and `daily_prices`/manifest/provider-run/watchlist fingerprints proven unchanged.

Every DB-facing function here composes ALREADY-EXISTING read-only primitives
(`app.engine.j11_maintenance.capture_pre_reset_inventory` / `freeze_attempt_identity` / `INCIDENT_DATES`,
`app.engine.j11_schema_migration.fetch_object_ddl` / `dump_table` / `diff_dumps` /
`capture_full_db_snapshot`) rather than reinventing an inventory formula. The ONE destructive mechanism
(`clear_snapshot_dates`) deliberately lives in `app.engine.data_manager`, next to the pattern it
specializes (`clear_snapshot_set`) -- NOT in this module, which stays read-only/pure precondition and
evidence-assembly tooling, mirroring `j11_maintenance.py`'s own "nothing here deletes" posture.

`_population_fingerprint`'s design note (AG-8 / host resource ceiling): `forward_returns` alone holds
~6.8M rows and `scanner_results` ~1.3M on the live database. Proving "every non-incident-date row id
present before is still present after" therefore uses a cheap SQL-side aggregate (count, min id, max id,
id sum -> sha256) over the population EXCLUDING the deleted run ids, rather than materializing millions
of ids into a Python set (an unbounded whole-table load AG-8 forbids). This is sufficient because Stage C
is DELETE-ONLY (ruling C8, mechanically proven by the fixture call-count assertions in
`test_j11_stage_c_bounded_clear.py`): no INSERT path is ever exercised, so the only way the excluded
population's count/min/max/sum could move is if the DELETE predicate matched a row outside the declared
run-id set -- exactly what `capture_intended_delete_set`'s own exact, fully-enumerated id lists (small
and bounded, since only the currently-run-bearing incident dates own any rows at all) independently
catch. Combined, the two proofs are strictly stronger than either alone and touch no unbounded table
scan.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Optional

from sqlalchemy import func, text
from sqlalchemy.engine import Engine
from sqlmodel import Session, select

from app.config import Config, REPO_ROOT
from app.engine import j11_maintenance
from app.engine import j11_schema_migration as migration
from app.engine.j11_maintenance import INCIDENT_DATES
from app.models import (
    DataProviderRun,
    ForwardReturn,
    NextSessionManifest,
    ScannerResult,
    ScannerRun,
    SectorScoreRow,
    ThemeScoreRow,
    Watchlist,
)

DEFAULT_GOAL_MD_PATH = REPO_ROOT / "docs" / "goal.md"

# The five Layer-2 tables ruling C4 authorizes clearing, keyed by their table name (used consistently
# across the delete-set capture, the population fingerprints, and the mutation-accounting report).
_CHILD_MODELS: dict[str, Any] = {
    "forward_returns": ForwardReturn,
    "scanner_results": ScannerResult,
    "sector_scores": SectorScoreRow,
    "theme_scores": ThemeScoreRow,
}


# ----------------------------------------------------------------------------------------------
# Filesystem/git I/O wrappers -- kept thin and separately swappable so every computation function
# below stays a pure, fixture-testable composition (the CLI script calls these two, then passes the
# results in as plain values).
# ----------------------------------------------------------------------------------------------


def read_goal_md_text(path: Path = DEFAULT_GOAL_MD_PATH) -> str:
    """The committed goal.md file's raw text -- read-only, no parsing here."""
    return path.read_text()


def read_git_head(repo_root: Path = REPO_ROOT) -> Optional[str]:
    """Current git HEAD commit hash, or `None` if it cannot be determined (never raises -- a missing git
    context must not crash preflight capture; it is recorded honestly as `None` instead)."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )
        return result.stdout.strip() or None
    except Exception:
        return None


# ----------------------------------------------------------------------------------------------
# C1 -- the J-11 contract text + the two goal.md 11-date lists (TC-3)
# ----------------------------------------------------------------------------------------------

_J11_SECTION_START = "- **J-11: Incident-bounded clean regeneration of derived state (owner, 2026-08-21)**"
_J11_SECTION_END = "<!-- Continuous-improvement auto-journeys:"

# Anchored to the literal surrounding prose from docs/goal.md so this never matches an unrelated date
# list elsewhere in the document -- fails closed (raises) rather than guessing from a broad date pattern.
_AUTHORITATIVE_BULLET_ANCHOR = "whose own cascade record lists them):"
_C1_RESTATEMENT_ANCHOR = "doubt they are"
_BACKTICK_DATE_LIST_RE = re.compile(
    r"`(\d{4}-\d{2}-\d{2}(?:,\s*\d{4}-\d{2}-\d{2})*)`"
)


def extract_j11_contract_text(goal_md_text: str) -> str:
    """The literal J-11 journey section (steps 1-14 plus the OWNER AUTHORIZATION block), sliced out of
    the full `docs/goal.md` text between two literal anchors. Fails closed (`ValueError`) if either
    boundary cannot be found exactly -- never hashes a partial or guessed slice."""
    start = goal_md_text.find(_J11_SECTION_START)
    if start == -1:
        raise ValueError(f"J-11 section start anchor not found: {_J11_SECTION_START!r}")
    end = goal_md_text.find(_J11_SECTION_END, start)
    if end == -1 or end <= start:
        raise ValueError(f"J-11 section end anchor not found after start: {_J11_SECTION_END!r}")
    return goal_md_text[start:end]


def compute_contract_hash(goal_md_text: str) -> str:
    """sha256 hex digest of the extracted J-11 contract section text (UTF-8 bytes, verbatim)."""
    section = extract_j11_contract_text(goal_md_text)
    return hashlib.sha256(section.encode("utf-8")).hexdigest()


def _next_backtick_date_list(section_text: str, anchor: str) -> list[str]:
    idx = section_text.find(anchor)
    if idx == -1:
        raise ValueError(f"anchor text not found: {anchor!r}")
    match = _BACKTICK_DATE_LIST_RE.search(section_text, idx)
    if match is None:
        raise ValueError(f"no backtick-quoted comma-separated date list found after anchor: {anchor!r}")
    return [item.strip() for item in match.group(1).split(",")]


def extract_incident_date_lists(goal_md_text: str) -> dict:
    """The two independently-authored 11-date lists in the J-11 contract text: the authoritative "the
    incident date set -- all 11" bullet, and the OWNER AUTHORIZATION block's C1 restatement. Raises
    (fails closed) if the J-11 section or either anchor cannot be located."""
    section = extract_j11_contract_text(goal_md_text)
    return {
        "authoritative_bullet_dates": _next_backtick_date_list(section, _AUTHORITATIVE_BULLET_ANCHOR),
        "c1_restatement_dates": _next_backtick_date_list(section, _C1_RESTATEMENT_ANCHOR),
    }


def check_c1_date_set_boundary(goal_md_text: str, incident_dates: tuple = INCIDENT_DATES) -> dict:
    """TC-3: the C1 date-set boundary check. Byte-identity of THREE things: the code's own
    `INCIDENT_DATES` (as ISO strings), the authoritative "incident date set -- all 11" bullet, and the C1
    restatement. If the two goal.md lists disagree with each other, or either cannot be located, `ok` is
    False and the caller MUST stop before any deletion -- never reconciled by silently preferring one."""
    code_dates = [d.isoformat() for d in incident_dates]
    try:
        lists = extract_incident_date_lists(goal_md_text)
    except ValueError as exc:
        return {
            "ok": False,
            "extraction_error": str(exc),
            "code_dates": code_dates,
        }
    bullet = lists["authoritative_bullet_dates"]
    restatement = lists["c1_restatement_dates"]
    lists_agree = bullet == restatement
    code_matches_goal_md_lists = bullet == code_dates and restatement == code_dates
    return {
        "ok": lists_agree and code_matches_goal_md_lists,
        "authoritative_bullet_dates": bullet,
        "c1_restatement_dates": restatement,
        "code_dates": code_dates,
        "lists_agree": lists_agree,
        "code_matches_goal_md_lists": code_matches_goal_md_lists,
    }


# ----------------------------------------------------------------------------------------------
# C2 -- Stage C attempt identity + fresh preflight capture
# ----------------------------------------------------------------------------------------------


def freeze_stage_c_attempt_identity(session: Session, config: Optional[Config] = None) -> dict:
    """A NEW Stage C bookkeeping attempt id/timestamp, layered ON TOP OF -- never replacing -- the
    existing Stage B2 `engine_identity` (logged assumption #2,
    `runs/goal-session-market-compass/state/assumptions.md` iter-13 entry). Re-derives the B2 identity
    fresh via `j11_maintenance.freeze_attempt_identity` rather than trusting a prior certified value."""
    b2_identity = j11_maintenance.freeze_attempt_identity(session, config)
    return {
        "stage_c_attempt_frozen_at": datetime.now(timezone.utc).isoformat(),
        "b2_engine_identity": b2_identity,
    }


def capture_stage_c_preflight(
    session: Session,
    engine: Engine,
    db_path: Optional[Path],
    *,
    goal_md_text: str,
    git_head: Optional[str],
    config: Optional[Config] = None,
) -> dict:
    """Ruling C2's fresh Stage C preflight -- re-derives live state fresh (never trusting iteration
    10/11/12's certified figures), composed entirely from already-existing read-only primitives. Writes
    nothing. `goal_md_text`/`git_head` are injected by the caller (this function performs no file/git I/O
    itself) so the whole capture stays a pure, fixture-testable composition."""
    pre_reset_inventory = j11_maintenance.capture_pre_reset_inventory(session)
    stage_c_attempt_identity = freeze_stage_c_attempt_identity(session, config)
    manifest_ddl = migration.fetch_object_ddl(engine, migration.TABLE_NAME)
    manifest_dump = migration.dump_table(engine, NextSessionManifest.__table__)
    full_db_snapshot = migration.capture_full_db_snapshot(engine, db_path)
    c1_check = check_c1_date_set_boundary(goal_md_text)
    return {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "git_head": git_head,
        "goal_md_j11_contract_hash": compute_contract_hash(goal_md_text),
        "c1_date_set_boundary_check": c1_check,
        "stage_c_attempt_identity": stage_c_attempt_identity,
        "pre_reset_inventory": pre_reset_inventory,
        "manifest_ddl": manifest_ddl,
        "manifest_dump": manifest_dump,
        "manifest_row_count": len(manifest_dump),
        "full_db_snapshot": full_db_snapshot,
    }


def load_certified_state(path: Path) -> dict:
    """Loads a prior iteration's persisted fingerprint artifact (shape:
    `{full_db_snapshot, manifest_ddl, manifest_dump, manifest_row_count, pre_reset_inventory}`) as the
    certified-state baseline the fresh preflight is compared against (ruling C2). The default caller
    (the CLI script) points this at
    `runs/goal-market-compass-iter-12/j11-stage-b1-cleanup-fingerprint-after.json` -- iteration 12's own
    diff artifact already proves that file `identical_except_capture_timestamps` against iteration 12's
    own before-capture, which is itself proven byte-identical to iteration 11's post-migration state."""
    return json.loads(path.read_text())


def compare_preflight_to_certified(preflight: dict, certified: dict) -> dict:
    """TC-1/TC-2: the preflight comparison gate. Every B/B1/B2 invariant re-checked against the supplied
    certified state: 24 manifest rows; no live FK on `source_run_id`; the manifest DDL/index set
    unchanged (the four owner-accepted residuals included, since they are already baked into the
    certified DDL text -- this checks for NO FURTHER drift, not a return to the pre-iter-11 shape);
    `source_run_id` provenance values unchanged; every manifest column value unchanged (a full row/column
    diff, never an aggregate-only check); `daily_prices`/`data_provider_runs`/`watchlist` counts
    unchanged; the C1 date-set boundary check passing; and the per-incident-date `ScannerRun` inventory
    unchanged. ANY False in `checks` means `material_mismatch` is True and the caller MUST stop before
    the first destructive statement."""
    checks: dict[str, Any] = {}

    fresh_ddl_sql = preflight["manifest_ddl"]["table_sql"] or ""
    certified_ddl_sql = certified["manifest_ddl"]["table_sql"] or ""
    # the manifest row count must match the CERTIFIED baseline exactly (dynamic equality -- never a
    # hardcoded literal here, so this function stays correct if a later iteration's certified baseline
    # legitimately differs from today's 24; the CLI script separately sanity-checks that the specific
    # baseline file it loaded for THIS iteration is the expected 24-row iteration-12 certification).
    checks["manifest_row_count_matches_certified"] = preflight["manifest_row_count"] == certified["manifest_row_count"]
    checks["no_live_fk_on_source_run_id"] = "FOREIGN KEY" not in fresh_ddl_sql
    checks["manifest_ddl_unchanged_from_certified"] = fresh_ddl_sql == certified_ddl_sql
    checks["manifest_indexes_unchanged"] = (
        sorted(preflight["manifest_ddl"]["index_names"]) == sorted(certified["manifest_ddl"]["index_names"])
        and sorted(preflight["manifest_ddl"]["index_sqls"]) == sorted(certified["manifest_ddl"]["index_sqls"])
    )

    manifest_dump_diff = migration.diff_dumps(certified["manifest_dump"], preflight["manifest_dump"])
    checks["manifest_values_unchanged"] = manifest_dump_diff["equal"]

    certified_source_ids = {row["id"]: row["source_run_id"] for row in certified["manifest_dump"]}
    fresh_source_ids = {row["id"]: row["source_run_id"] for row in preflight["manifest_dump"]}
    checks["source_run_id_values_unchanged"] = certified_source_ids == fresh_source_ids

    checks["daily_prices_fingerprint_unchanged"] = (
        preflight["pre_reset_inventory"]["daily_prices"]["fingerprint"]
        == certified["pre_reset_inventory"]["daily_prices"]["fingerprint"]
    )
    checks["data_provider_runs_count_unchanged"] = (
        preflight["pre_reset_inventory"]["data_provider_runs_count"]
        == certified["pre_reset_inventory"]["data_provider_runs_count"]
    )
    checks["watchlist_count_unchanged"] = (
        preflight["pre_reset_inventory"]["watchlist_count"]
        == certified["pre_reset_inventory"]["watchlist_count"]
    )
    checks["c1_date_set_boundary_ok"] = bool(preflight["c1_date_set_boundary_check"]["ok"])

    fresh_per_date = preflight["pre_reset_inventory"]["per_date"]
    certified_per_date = certified["pre_reset_inventory"]["per_date"]
    per_date_mismatches: list[dict] = []
    for key, fresh_row in fresh_per_date.items():
        certified_row = certified_per_date.get(key, {})
        fresh_run = fresh_row.get("scanner_run", {})
        certified_run = certified_row.get("scanner_run", {})
        if (
            fresh_run.get("present") != certified_run.get("present")
            or fresh_run.get("run_id") != certified_run.get("run_id")
            or fresh_run.get("created_at") != certified_run.get("created_at")
        ):
            per_date_mismatches.append({"date": key, "fresh": fresh_run, "certified": certified_run})
    checks["per_date_scanner_run_inventory_unchanged"] = not per_date_mismatches

    all_invariants_hold = all(bool(v) for v in checks.values())
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
        "per_date_scanner_run_mismatches": per_date_mismatches,
        "manifest_dump_diff": manifest_dump_diff,
        "all_invariants_hold": all_invariants_hold,
        "material_mismatch": not all_invariants_hold,
    }


# ----------------------------------------------------------------------------------------------
# C9 -- the intended-delete-set, captured and persisted BEFORE any DELETE statement executes
# ----------------------------------------------------------------------------------------------


def capture_intended_delete_set(session: Session, exact_date_set) -> dict:
    """Ruling C9: BEFORE any DELETE, the exact row-id set to be removed, per table, for each
    currently-run-bearing incident date, plus every associated child row's id. Column-projected `id`
    SELECTs only (AG-8) -- never a full-row hydration. This is the pre-declared plan the post-hoc
    actual-delete evidence (`clear_snapshot_dates`'s own return value) is checked against."""
    per_date: dict[str, dict] = {}
    totals: dict[str, list[int]] = {
        "scanner_runs": [], "forward_returns": [], "scanner_results": [], "sector_scores": [], "theme_scores": [],
    }
    for one_date in exact_date_set:
        key = one_date.isoformat()
        run = session.exec(select(ScannerRun).where(ScannerRun.asof_date == one_date)).first()
        if run is None:
            per_date[key] = {
                "run_id": None,
                "ids": {"scanner_runs": [], "forward_returns": [], "scanner_results": [], "sector_scores": [], "theme_scores": []},
            }
            continue
        run_id = run.id
        ids: dict[str, list[int]] = {"scanner_runs": [run_id]}
        for table_name, model in _CHILD_MODELS.items():
            rows = session.exec(select(model.id).where(model.run_id == run_id)).all()
            ids[table_name] = sorted(int(r) for r in rows)
        per_date[key] = {"run_id": run_id, "ids": ids}
        for table_name, id_list in ids.items():
            totals[table_name].extend(id_list)
    sorted_totals = {table_name: sorted(id_list) for table_name, id_list in totals.items()}
    return {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "per_date": per_date,
        "totals": sorted_totals,
        "total_counts": {table_name: len(id_list) for table_name, id_list in sorted_totals.items()},
        "deleted_run_ids": sorted(int(rid) for rid in sorted_totals["scanner_runs"]),
    }


# ----------------------------------------------------------------------------------------------
# Post-delete mutation accounting
# ----------------------------------------------------------------------------------------------


def _population_fingerprint(session: Session, agg_column, filter_column, exclude_values: list[int]) -> dict:
    """Cheap SQL-side aggregate fingerprint (count, min id, max id, id sum -> sha256) of every row whose
    `filter_column` is NOT in `exclude_values` -- see the module docstring for why this suffices in place
    of a full millions-of-ids Python diff."""
    stmt = select(func.count(agg_column), func.min(agg_column), func.max(agg_column), func.sum(agg_column))
    if exclude_values:
        stmt = stmt.where(~filter_column.in_(exclude_values))
    row = session.exec(stmt).one()
    count, min_id, max_id, id_sum = row
    payload = {
        "count": int(count or 0),
        "min_id": int(min_id) if min_id is not None else None,
        "max_id": int(max_id) if max_id is not None else None,
        "id_sum": int(id_sum or 0),
    }
    fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()
    return {**payload, "fingerprint": fingerprint}


def capture_layer2_population_fingerprints(session: Session, deleted_run_ids: list[int]) -> dict:
    """Per-table (scanner_runs + the 4 run_id-owned children) population fingerprint EXCLUDING
    `deleted_run_ids` -- the "every non-incident-date row survives unchanged" proof. Called with the SAME
    `deleted_run_ids` both BEFORE and AFTER `clear_snapshot_dates` runs; the two results must be
    byte-identical (the excluded population is, by construction, exactly the rows the delete predicate
    never touches)."""
    return {
        "scanner_runs": _population_fingerprint(session, ScannerRun.id, ScannerRun.id, deleted_run_ids),
        "forward_returns": _population_fingerprint(session, ForwardReturn.id, ForwardReturn.run_id, deleted_run_ids),
        "scanner_results": _population_fingerprint(session, ScannerResult.id, ScannerResult.run_id, deleted_run_ids),
        "sector_scores": _population_fingerprint(session, SectorScoreRow.id, SectorScoreRow.run_id, deleted_run_ids),
        "theme_scores": _population_fingerprint(session, ThemeScoreRow.id, ThemeScoreRow.run_id, deleted_run_ids),
    }


def incident_scoped_counts(session: Session, deleted_run_ids: list[int]) -> dict:
    """`COUNT(*)` of rows still matching `deleted_run_ids`, per table. Called AFTER
    `clear_snapshot_dates` this MUST be all-zero (the "deleted, and only those" proof); called BEFORE, it
    independently cross-checks `capture_intended_delete_set`'s own enumerated totals via a live
    aggregate, never trusting the enumerated id list alone."""
    zero = {"scanner_runs": 0, "forward_returns": 0, "scanner_results": 0, "sector_scores": 0, "theme_scores": 0}
    if not deleted_run_ids:
        return zero
    return {
        "scanner_runs": int(session.scalar(select(func.count()).select_from(ScannerRun).where(ScannerRun.id.in_(deleted_run_ids))) or 0),
        "forward_returns": int(session.scalar(select(func.count()).select_from(ForwardReturn).where(ForwardReturn.run_id.in_(deleted_run_ids))) or 0),
        "scanner_results": int(session.scalar(select(func.count()).select_from(ScannerResult).where(ScannerResult.run_id.in_(deleted_run_ids))) or 0),
        "sector_scores": int(session.scalar(select(func.count()).select_from(SectorScoreRow).where(SectorScoreRow.run_id.in_(deleted_run_ids))) or 0),
        "theme_scores": int(session.scalar(select(func.count()).select_from(ThemeScoreRow).where(ThemeScoreRow.run_id.in_(deleted_run_ids))) or 0),
    }


def small_table_id_snapshot(session: Session, model: Any) -> dict:
    """A full id-set snapshot of a SMALL table (`data_provider_runs`, `watchlist` -- hundreds of rows at
    most on the live database, so a full id enumeration is cheap and strictly stronger than a row-count
    check alone)."""
    ids = session.exec(select(model.id)).all()
    id_list = sorted(int(i) for i in ids)
    return {"count": len(id_list), "ids": id_list}


def build_mutation_accounting(
    *,
    pre_layer2_population: dict,
    post_layer2_population: dict,
    pre_full_db_snapshot: dict,
    post_full_db_snapshot: dict,
    pre_daily_prices: dict,
    post_daily_prices: dict,
    pre_manifest_dump: list,
    post_manifest_dump: list,
    pre_provider_runs: dict,
    post_provider_runs: dict,
    pre_watchlist: dict,
    post_watchlist: dict,
    pre_incident_scoped_counts: dict,
    post_incident_scoped_counts: dict,
    intended_delete_set: dict,
    clear_result: dict,
    db_file_true_start: dict,
    db_file_true_end: dict,
) -> dict:
    """Assembles the persisted mutation-accounting artifact (TC-7..TC-12) from already-captured pre/post
    evidence -- a pure function, deliberately taking no session/engine, so it is trivially fixture-tested
    with synthetic dicts. Every check in `checks` must be True for Stage C to be considered verified;
    ANY False means `all_checks_pass` is False and the caller MUST NOT write the completion marker."""
    checks: dict[str, Any] = {}

    # TC-9: daily_prices byte-identical.
    checks["daily_prices_unchanged"] = pre_daily_prices["fingerprint"] == post_daily_prices["fingerprint"]

    # TC-10: manifests untouched -- 24 rows, full 28-column equality.
    manifest_diff = migration.diff_dumps(pre_manifest_dump, post_manifest_dump)
    checks["manifests_unchanged"] = (
        manifest_diff["equal"] and len(pre_manifest_dump) == 24 and len(post_manifest_dump) == 24
    )

    # TC-11: data_provider_runs / watchlist unchanged -- full id-set equality.
    checks["data_provider_runs_unchanged"] = pre_provider_runs == post_provider_runs
    checks["watchlist_unchanged"] = pre_watchlist == post_watchlist

    # TC-8: every non-incident-date row's population fingerprint is byte-identical before/after.
    per_table_population_unchanged = {
        table: pre_layer2_population[table]["fingerprint"] == post_layer2_population[table]["fingerprint"]
        for table in pre_layer2_population
    }
    checks["layer2_non_incident_population_unchanged"] = all(per_table_population_unchanged.values())

    # TC-7: the deleted set is gone (post incident-scoped count == 0 for every table) and the pre
    # incident-scoped count matches the pre-declared intended-delete-set's own totals exactly.
    intended_totals = intended_delete_set["total_counts"]
    checks["post_incident_scoped_counts_all_zero"] = all(v == 0 for v in post_incident_scoped_counts.values())
    checks["pre_incident_scoped_counts_match_intended_delete_set"] = all(
        pre_incident_scoped_counts.get(table, 0) == intended_totals.get(table, 0) for table in intended_totals
    )

    # per-date/per-table reconciliation: actual deleted counts (from clear_snapshot_dates's own return)
    # must equal the pre-declared intended-delete-set's per-date counts exactly.
    per_date_reconciliation: dict[str, dict] = {}
    for key, intended_row in intended_delete_set["per_date"].items():
        actual_row = clear_result["per_date"].get(key, {})
        actual_deleted = actual_row.get("deleted", {})
        intended_counts = {table: len(ids) for table, ids in intended_row["ids"].items()}
        matches = all(intended_counts.get(table, 0) == actual_deleted.get(table, 0) for table in intended_counts)
        per_date_reconciliation[key] = {
            "intended_counts": intended_counts,
            "actual_deleted_counts": actual_deleted,
            "matches": matches,
        }
    checks["actual_delete_matches_intended_delete_set"] = all(
        row["matches"] for row in per_date_reconciliation.values()
    )

    # per-table PRE / DELETED / POST counts, split incident vs. non-incident (arithmetic cross-check
    # against the full-db-snapshot table counts captured immediately before/after the delete).
    per_table_counts: dict[str, dict] = {}
    all_tables = set(pre_full_db_snapshot["tables"]) | set(post_full_db_snapshot["tables"])
    layer2_tables = {"scanner_runs", "forward_returns", "scanner_results", "sector_scores", "theme_scores"}
    for table in sorted(all_tables & layer2_tables):
        pre_total = int(pre_full_db_snapshot["tables"].get(table, 0))
        post_total = int(post_full_db_snapshot["tables"].get(table, 0))
        deleted_incident = int(intended_totals.get(table, 0))
        per_table_counts[table] = {
            "pre_total": pre_total,
            "post_total": post_total,
            "deleted_incident": deleted_incident,
            "post_non_incident": post_total,
            "pre_non_incident": pre_total - deleted_incident,
            "arithmetic_consistent": pre_total - deleted_incident == post_total,
        }
    checks["per_table_arithmetic_consistent"] = all(
        row["arithmetic_consistent"] for row in per_table_counts.values()
    )

    # non-layer-2 tables must show ZERO row-count change of any kind (C4: expected new canonical-input
    # writes are ZERO).
    non_layer2_changes = [
        {"table": table, "before": pre_full_db_snapshot["tables"].get(table), "after": post_full_db_snapshot["tables"].get(table)}
        for table in sorted(all_tables - layer2_tables)
        if pre_full_db_snapshot["tables"].get(table) != post_full_db_snapshot["tables"].get(table)
    ]
    checks["no_non_layer2_table_row_count_changed"] = not non_layer2_changes

    all_checks_pass = all(bool(v) for v in checks.values())

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
        "per_table_counts": per_table_counts,
        "per_date_delete_reconciliation": per_date_reconciliation,
        "non_layer2_table_changes": non_layer2_changes,
        "layer2_population_fingerprints": {
            "pre": pre_layer2_population,
            "post": post_layer2_population,
            "unchanged_per_table": per_table_population_unchanged,
        },
        "daily_prices": {"pre": pre_daily_prices, "post": post_daily_prices},
        "manifest_diff": manifest_diff,
        "data_provider_runs": {"pre": pre_provider_runs, "post": post_provider_runs},
        "watchlist": {"pre": pre_watchlist, "post": post_watchlist},
        "incident_scoped_counts": {"pre": pre_incident_scoped_counts, "post": post_incident_scoped_counts},
        "db_file": {"true_start": db_file_true_start, "true_end": db_file_true_end},
        "clear_result": clear_result,
        "intended_delete_set_total_counts": intended_totals,
        "all_checks_pass": all_checks_pass,
    }


def stage_c_overall_verdict(preflight_gate: dict, mutation_accounting: Optional[dict] = None) -> dict:
    """The single pass/fail decision the CLI script's completion-marker gate is built on (ruling C9/C10:
    the marker may be written ONLY after every verification check passes). `mutation_accounting` is
    `None` when the process stopped before the destructive step (a failed preflight gate or C1 check --
    the honest, complete outcome for that case per ruling C2's "STOP before deletion")."""
    if not preflight_gate.get("all_invariants_hold"):
        return {"passed": False, "reason": "preflight_comparison_gate_failed"}
    if mutation_accounting is None:
        return {"passed": False, "reason": "no_mutation_accounting_captured"}
    if not mutation_accounting.get("all_checks_pass"):
        return {"passed": False, "reason": "post_delete_verification_failed"}
    return {"passed": True, "reason": "all_checks_passed"}


def build_completion_marker(verdict: dict, prior_artifact_timestamps: list) -> dict:
    """Ruling C9/TC-13: the completion marker is written ONLY after `verdict['passed']` is True, and its
    OWN timestamp must be strictly after every other persisted evidence artifact's own timestamp --
    proving the marker really was written last, after every verification check completed. Raises
    (refuses to build a marker) if `verdict` is not a passing verdict, or if the computed marker instant
    is not strictly after every supplied prior timestamp."""
    if not verdict.get("passed"):
        raise RuntimeError(
            f"build_completion_marker called with a non-passing verdict ({verdict!r}) -- refusing to "
            "write a completion marker"
        )
    marker_time = datetime.now(timezone.utc)
    for prior in prior_artifact_timestamps:
        if prior is None:
            continue
        prior_time = datetime.fromisoformat(prior)
        if prior_time.tzinfo is None:
            prior_time = prior_time.replace(tzinfo=timezone.utc)
        if marker_time <= prior_time:
            raise RuntimeError(
                f"completion marker instant {marker_time.isoformat()} is not strictly after prior "
                f"artifact timestamp {prior!r}"
            )
    return {
        "completed_at": marker_time.isoformat(),
        "verdict": verdict,
        "j11_stage_c_complete": True,
    }


def db_file_fingerprint(db_path: Optional[Path]) -> dict:
    """The live main database file's mtime + size, plus its `-wal` sidecar's size if present -- captured
    at whatever moment the caller invokes this (the CLI script calls it at the TRUE process start and
    TRUE process end, never a narrow internal bracket -- iteration 12's lesson). A present `-wal` sidecar
    mtime/size is NOT itself evidence of a committed write: SQLite touches the WAL file on any connection
    open in WAL mode, including read-only ones."""
    if db_path is None or not db_path.exists():
        return {"path": str(db_path) if db_path else None, "exists": False}
    stat = db_path.stat()
    wal_path = Path(str(db_path) + "-wal")
    wal = {"exists": wal_path.exists()}
    if wal["exists"]:
        wal_stat = wal_path.stat()
        wal["size_bytes"] = wal_stat.st_size
        wal["mtime"] = wal_stat.st_mtime
    return {
        "path": str(db_path),
        "exists": True,
        "mtime": stat.st_mtime,
        "size_bytes": stat.st_size,
        "wal": wal,
    }
