"""app.engine.j11_stage_d -- J-11 Stage D readiness hardening (goal-market-compass iter-14).

Iteration 13's auditor found two live defects that would otherwise silently break the still-unauthorized
Stage D (canonical regeneration of the 11 incident dates, `docs/goal.md` J-11 step 12):

  - **B1** -- no per-run identity-comparison call site exists yet for Stage D; only Stage B2's freeze
    (`j11_maintenance.freeze_attempt_identity`) and the pure per-run helper
    (`j11_maintenance.check_attempt_identity_consistency`) exist, with nothing that actually CALLS the
    helper at the three points step 12/13 require.
  - **B2** -- the Stage C-era preflight gate CAPTURES an identity value but never COMPARES it against
    anything (`j11_stage_c.capture_stage_c_preflight` has no drift check at all -- `compare_preflight_to_
    certified` covers Stage C's own C2 invariants, not Stage D's).

This module closes both, plus builds the Stage D preflight gate itself -- ALL read-only. It performs
NO Stage D execution: no `scanner.run_scan`, no `scanner.persist_run_payload`, no ScannerRun INSERT, no
ForwardReturn mutation. `docs/goal.md` J-11 step 12's 2026-08-24 clarification governs the identity
question this module implements exactly:

  > Stage D begins a FRESH regeneration attempt from the successfully cleared Stage C baseline; its
  > frozen identity is computed immediately before Stage D and applies ONLY to the 11 rebuilt incident-
  > date runs. Surviving historical runs retain their existing stamps.

So `freeze_stage_d_attempt_identity` NEVER hardcodes or trusts iteration 10's `6261ca17...` or iteration
13's `53d2ffd1...` -- it re-derives fresh, every time, via the SAME `app.engine.engine_identity.
compute_engine_identity` the real `scanner.persist_run_payload` stamps onto every newly created
`ScannerRun.engine_identity` (reused, never reimplemented, so a later per-run compare is like-for-like).

Goal 2's three checks are genuine COMPARE call sites (iter-13's own lesson: "capturing an invariant's
value is not checking it, and a gate that cannot compare is a gate that always passes") -- each wraps
`j11_maintenance.check_attempt_identity_consistency` rather than reimplementing comparison logic, and
each returns a per-call evidence record, never an aggregate boolean alone (iter-9's AVB lesson: a
population-wide "all N matched" claim is exactly where the one real counter-example hides). Checks (B)
and (C) take an explicit `date` and vacuously PASS (`in_scope: False`, no comparison performed) for any
date outside this attempt's 11-date `INCIDENT_DATES` scope -- the step-12 clarification's own words: the
34 surviving `6261ca17...` runs and the ~3,083 NULL-stamped pre-stamping-era rows "are not members of the
new 11-date attempt" and so are never candidates for this attempt's identity check at all (TC-ID-6).

Goal 3a's Stage D preflight mirrors `j11_stage_c.capture_stage_c_preflight`'s composition pattern
(re-derive live state fresh from already-existing read-only primitives -- `j11_maintenance.
capture_pre_reset_inventory`, `j11_schema_migration.fetch_object_ddl`/`dump_table`,
`j11_stage_c.check_c1_date_set_boundary`) plus one Stage-D-specific addition: every one of the 11
incident dates must currently show ZERO `ScannerRun` rows (the Stage C-cleared baseline this attempt
regenerates from). `load_stage_d_certified_baseline` composes the certified comparison target from TWO
already-persisted iteration-13 artifacts: `j11-stage-c-preflight.json` (manifest DDL/dump -- captured
BEFORE Stage C's delete, but Layer 3/manifests are proven untouched by that same delete, per iteration
13's own `manifests_unchanged: true` mutation-accounting check, so this pre-delete capture IS the
terminal post-Stage-C manifest state) and `j11-stage-c-mutation-accounting.json` (the actual POST-delete
`daily_prices`/`data_provider_runs`/`watchlist` figures -- the real terminal state after the one
authorized destructive write).

Everything here composes already-existing read-only primitives; nothing here deletes, updates, or
inserts a snapshot/manifest/price row (mirrors `j11_maintenance.py`'s and `j11_stage_c.py`'s own "nothing
here deletes" posture)."""
from __future__ import annotations

import json
import os
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Optional, Union

from sqlalchemy.engine import Engine
from sqlmodel import Session

from app.config import Config, get_config
from app.engine import engine_identity
from app.engine import j11_maintenance
from app.engine import j11_schema_migration as migration
from app.engine import j11_stage_c as jsc
from app.engine.j11_maintenance import INCIDENT_DATES
from app.models import NextSessionManifest


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _identity_value(frozen: Union[dict, str, None]) -> Optional[str]:
    return frozen.get("engine_identity") if isinstance(frozen, dict) else frozen


def _in_attempt_scope(one_date: date) -> bool:
    """Whether `one_date` is one of THIS attempt's 11 incident dates. A date outside this set (e.g. one
    of the 34 surviving `6261ca17...` runs' own historical dates) is never a member of the new attempt
    per docs/goal.md J-11 step 12's 2026-08-24 clarification -- TC-ID-6."""
    return one_date in INCIDENT_DATES


# ----------------------------------------------------------------------------------------------
# Goal 1 -- fresh Stage D attempt identity
# ----------------------------------------------------------------------------------------------


def freeze_stage_d_attempt_identity(
    session: Session,
    config: Optional[Config] = None,
    *,
    git_head: Optional[str] = None,
    goal_md_text: Optional[str] = None,
) -> dict:
    """A thin wrapper around `j11_maintenance.freeze_attempt_identity` that re-derives the identity FRESH
    (never trusting or hardcoding iteration 10's `6261ca17...` or iteration 13's `53d2ffd1...`) and
    assembles the full Stage D attempt-identity artifact. `git_head`/`goal_md_text` are injected
    (defaulting to real read-only I/O via `j11_stage_c`'s helpers when omitted) so this function stays a
    pure, fixture-testable composition when the caller supplies synthetic values -- mirrors
    `j11_stage_c.capture_stage_c_preflight`'s own injected-params pattern.

    Applies ONLY to the 11 dates Stage D will rebuild. The 34 surviving runs stamped `6261ca17...`
    (iteration 10's EARLIER attempt identity) and the ~3,083 NULL-stamped pre-stamping-era rows are not
    members of this attempt and must never be restamped -- recorded explicitly in `scope_note` so the
    artifact is self-documenting."""
    cfg = config or get_config()
    b2_identity = j11_maintenance.freeze_attempt_identity(session, cfg)
    resolved_git_head = git_head if git_head is not None else jsc.read_git_head()
    resolved_goal_md_text = goal_md_text if goal_md_text is not None else jsc.read_goal_md_text()
    contract_hash = jsc.compute_contract_hash(resolved_goal_md_text)
    frozen_at = datetime.now(timezone.utc)
    return {
        "attempt_id": f"j11-stage-d-{frozen_at.strftime('%Y%m%dT%H%M%S%fZ')}",
        "frozen_at": b2_identity["frozen_at"],
        "engine_identity": b2_identity["engine_identity"],
        "config_subset_hash": b2_identity["config_subset_hash"],
        "config_subset": b2_identity["config_subset"],
        "provenance": {
            "engine_files": b2_identity["provenance_engine_files"],
            "config_keys": b2_identity["provenance_config_keys"],
        },
        "git_head": resolved_git_head,
        "j11_contract_hash": contract_hash,
        "incident_dates": [d.isoformat() for d in INCIDENT_DATES],
        "scope_note": (
            "This identity applies ONLY to the 11 dates Stage D will rebuild "
            "(docs/goal.md J-11 step 12's 2026-08-24 clarification: 'Stage D begins a FRESH regeneration "
            "attempt from the successfully cleared Stage C baseline; its frozen identity is computed "
            "immediately before Stage D and applies only to the 11 rebuilt incident-date runs. Surviving "
            "historical runs retain their existing stamps.'). The 34 surviving ScannerRun rows stamped "
            "'6261ca17...' (iteration 10's earlier-attempt identity, since drifted) and the pre-stamping-"
            "era NULL-engine_identity rows are NOT members of this attempt and must never be restamped, "
            "mutated, or otherwise touched by any check in this module."
        ),
    }


# ----------------------------------------------------------------------------------------------
# Goal 2 -- three fail-closed identity COMPARE checks (never a second capture)
# ----------------------------------------------------------------------------------------------


def check_identity_before_first_write(frozen: Union[dict, str], current: Optional[str]) -> dict:
    """Check (A): before Stage D's first regeneration write, the current recomputed identity MUST equal
    the frozen attempt identity, else STOP (zero writes). Reuses `j11_maintenance.
    check_attempt_identity_consistency` -- a genuine COMPARE call site, never a second capture."""
    ok = j11_maintenance.check_attempt_identity_consistency(frozen, current)
    return {
        "check": "before_first_write",
        "frozen_engine_identity": _identity_value(frozen),
        "current_engine_identity": current,
        "ok": ok,
        "checked_at": _now_iso(),
    }


def check_identity_before_date(frozen: Union[dict, str], current: Optional[str], one_date: date) -> dict:
    """Check (B): before EVERY subsequent incident date, recompute and re-prove equality; on drift, STOP
    before that date -- never silently update the frozen value, never continue piecemeal. A date outside
    this attempt's 11-date scope is never checked at all (`in_scope: False`, vacuous pass, no comparison
    performed) -- TC-ID-6: the 34 surviving `6261ca17...` runs' own dates are not members of this
    attempt, so no failure is ever raised against them."""
    if not _in_attempt_scope(one_date):
        return {
            "check": "before_date",
            "date": one_date.isoformat(),
            "in_scope": False,
            "ok": True,
            "reason": "date_outside_j11_stage_d_attempt_scope_no_check_performed",
            "checked_at": _now_iso(),
        }
    ok = j11_maintenance.check_attempt_identity_consistency(frozen, current)
    return {
        "check": "before_date",
        "date": one_date.isoformat(),
        "in_scope": True,
        "frozen_engine_identity": _identity_value(frozen),
        "current_engine_identity": current,
        "ok": ok,
        "checked_at": _now_iso(),
    }


def check_identity_after_persist(
    frozen: Union[dict, str], persisted_run_identity: Optional[str], run_id: Any, one_date: date
) -> dict:
    """Check (C): after each `ScannerRun` persistence, the newly persisted row's OWN `engine_identity`
    column MUST equal the frozen identity -- NULL, missing, or mismatched is failure (fail-closed, via
    `check_attempt_identity_consistency`'s own `run_identity is not None and run_identity == expected`).
    Same out-of-scope vacuous-pass rule as Check (B) -- TC-ID-6."""
    if not _in_attempt_scope(one_date):
        return {
            "check": "after_persist",
            "date": one_date.isoformat(),
            "run_id": run_id,
            "in_scope": False,
            "ok": True,
            "reason": "date_outside_j11_stage_d_attempt_scope_no_check_performed",
            "checked_at": _now_iso(),
        }
    ok = j11_maintenance.check_attempt_identity_consistency(frozen, persisted_run_identity)
    return {
        "check": "after_persist",
        "date": one_date.isoformat(),
        "run_id": run_id,
        "in_scope": True,
        "frozen_engine_identity": _identity_value(frozen),
        "persisted_engine_identity": persisted_run_identity,
        "ok": ok,
        "checked_at": _now_iso(),
    }


# ----------------------------------------------------------------------------------------------
# Goal 3a -- Stage D preflight gate (built AND executed read-only against the live DB this iteration)
# ----------------------------------------------------------------------------------------------


def capture_stage_d_preflight(
    session: Session,
    engine: Engine,
    db_path: Optional[Path],
    *,
    goal_md_text: str,
    git_head: Optional[str],
    config: Optional[Config] = None,
) -> dict:
    """Re-derives live state fresh (never trusting iteration 13's certified figures without re-proving
    them), composed entirely from already-existing read-only primitives. Writes nothing -- `session` is
    used for SELECTs only, `engine`/`db_path` only for DDL/file introspection. `goal_md_text`/`git_head`
    are injected by the caller so the whole capture stays a pure, fixture-testable composition."""
    cfg = config or get_config()
    pre_reset_inventory = j11_maintenance.capture_pre_reset_inventory(session)
    attempt_identity = freeze_stage_d_attempt_identity(
        session, cfg, git_head=git_head, goal_md_text=goal_md_text
    )
    # Check (A) exercised HERE, against a SECOND, independent re-derivation of the current identity --
    # not the identity artifact's own value compared to itself (that would be a no-op self-compare). At
    # freeze time no drift is expected yet; this proves the compare plumbing works end-to-end against
    # real, freshly re-computed data (TC-11).
    current_identity_for_check_a = engine_identity.compute_engine_identity(cfg)
    identity_check_a = check_identity_before_first_write(attempt_identity, current_identity_for_check_a)

    manifest_ddl = migration.fetch_object_ddl(engine, migration.TABLE_NAME)
    manifest_dump = migration.dump_table(engine, NextSessionManifest.__table__)
    c1_check = jsc.check_c1_date_set_boundary(goal_md_text)
    maintenance_isolation_value = os.environ.get("CHAIN_MAINTENANCE_ISOLATION")

    return {
        "captured_at": _now_iso(),
        "git_head": git_head,
        "goal_md_j11_contract_hash": jsc.compute_contract_hash(goal_md_text),
        "c1_date_set_boundary_check": c1_check,
        "attempt_identity": attempt_identity,
        "identity_check_a": identity_check_a,
        "pre_reset_inventory": pre_reset_inventory,
        "manifest_ddl": manifest_ddl,
        "manifest_dump": manifest_dump,
        "manifest_row_count": len(manifest_dump),
        "maintenance_isolation_env": {
            "present": maintenance_isolation_value is not None,
            "value": maintenance_isolation_value,
        },
    }


def load_stage_d_certified_baseline(
    stage_c_preflight_path: Path, stage_c_mutation_accounting_path: Path
) -> dict:
    """The terminal (post-Stage-C) certified state Stage D's preflight gate compares against, composed
    from TWO already-persisted iteration-13 artifacts:

      - `j11-stage-c-preflight.json` for the manifest DDL/dump -- captured BEFORE Stage C's delete, but
        proven byte-identical to the POST-delete state by that same iteration's own mutation-accounting
        `manifests_unchanged: true` check (manifests are Layer 3, untouched by Stage C's Layer-2-only
        clear). Raises if the loaded mutation-accounting artifact does not itself prove that equality --
        fail closed rather than silently trusting a pre-delete capture as if it were the post-delete
        state.
      - `j11-stage-c-mutation-accounting.json` for the ACTUAL post-delete `daily_prices`/
        `data_provider_runs`/`watchlist` figures -- the real terminal state after the one authorized
        destructive write."""
    preflight = json.loads(Path(stage_c_preflight_path).read_text())
    mutation_accounting = json.loads(Path(stage_c_mutation_accounting_path).read_text())

    checks = mutation_accounting.get("checks", {})
    if not checks.get("manifests_unchanged"):
        raise ValueError(
            f"{stage_c_mutation_accounting_path} does not prove manifests_unchanged=True -- refusing to "
            "treat the pre-delete preflight capture's manifest dump as the post-Stage-C certified baseline"
        )
    if not (checks.get("data_provider_runs_unchanged") and checks.get("watchlist_unchanged")):
        raise ValueError(
            f"{stage_c_mutation_accounting_path} does not prove data_provider_runs/watchlist unchanged -- "
            "refusing to build a certified baseline from it"
        )

    return {
        "source": {
            "stage_c_preflight_path": str(stage_c_preflight_path),
            "stage_c_mutation_accounting_path": str(stage_c_mutation_accounting_path),
        },
        "daily_prices_fingerprint": mutation_accounting["daily_prices"]["post"]["fingerprint"],
        "manifest_row_count": preflight["manifest_row_count"],
        "manifest_ddl": preflight["manifest_ddl"],
        "manifest_dump": preflight["manifest_dump"],
        "data_provider_runs_count": mutation_accounting["data_provider_runs"]["post"]["count"],
        "watchlist_count": mutation_accounting["watchlist"]["post"]["count"],
    }


def compare_stage_d_preflight_to_certified(preflight: dict, certified: dict) -> dict:
    """The Stage D preflight comparison gate -- mirrors `j11_stage_c.compare_preflight_to_certified`'s
    shape and idiom but checks Stage D's OWN preconditions: canonical inputs (`daily_prices`) and
    manifests unchanged since the certified post-Stage-C baseline, the C1 date-set boundary still
    agreeing, Check (A)'s identity comparison passing, and -- the genuinely NEW Stage D-specific
    precondition -- every one of the 11 incident dates currently showing ZERO `ScannerRun` rows (the
    Stage-C-cleared baseline this attempt regenerates from; TC-19's 'unexpected incident ScannerRun
    population' refusal). ANY False in `checks` means `material_mismatch` is True and the caller MUST
    stop before the first destructive statement."""
    checks: dict[str, Any] = {}

    checks["daily_prices_fingerprint_unchanged"] = (
        preflight["pre_reset_inventory"]["daily_prices"]["fingerprint"] == certified["daily_prices_fingerprint"]
    )
    checks["manifest_row_count_unchanged"] = preflight["manifest_row_count"] == certified["manifest_row_count"]

    fresh_ddl_sql = preflight["manifest_ddl"]["table_sql"] or ""
    certified_ddl_sql = certified["manifest_ddl"]["table_sql"] or ""
    checks["manifest_ddl_unchanged"] = fresh_ddl_sql == certified_ddl_sql
    checks["manifest_indexes_unchanged"] = (
        sorted(preflight["manifest_ddl"]["index_names"]) == sorted(certified["manifest_ddl"]["index_names"])
        and sorted(preflight["manifest_ddl"]["index_sqls"]) == sorted(certified["manifest_ddl"]["index_sqls"])
    )

    manifest_dump_diff = migration.diff_dumps(certified["manifest_dump"], preflight["manifest_dump"])
    checks["manifest_values_unchanged"] = manifest_dump_diff["equal"]

    certified_source_ids = {row["id"]: row["source_run_id"] for row in certified["manifest_dump"]}
    fresh_source_ids = {row["id"]: row["source_run_id"] for row in preflight["manifest_dump"]}
    checks["source_run_id_values_unchanged"] = certified_source_ids == fresh_source_ids

    checks["data_provider_runs_count_unchanged"] = (
        preflight["pre_reset_inventory"]["data_provider_runs_count"] == certified["data_provider_runs_count"]
    )
    checks["watchlist_count_unchanged"] = (
        preflight["pre_reset_inventory"]["watchlist_count"] == certified["watchlist_count"]
    )
    checks["c1_date_set_boundary_ok"] = bool(preflight["c1_date_set_boundary_check"]["ok"])

    incident_dates = preflight["pre_reset_inventory"]["incident_dates"]
    per_date_scanner_run_present = {
        d: bool(preflight["pre_reset_inventory"]["per_date"][d]["scanner_run"]["present"])
        for d in incident_dates
    }
    checks["all_incident_dates_zero_scanner_runs"] = not any(per_date_scanner_run_present.values())

    checks["identity_check_a_ok"] = bool(preflight["identity_check_a"]["ok"])

    all_hold = all(bool(v) for v in checks.values())
    return {
        "generated_at": _now_iso(),
        "checks": checks,
        "per_date_scanner_run_present": per_date_scanner_run_present,
        "manifest_dump_diff": manifest_dump_diff,
        "all_invariants_hold": all_hold,
        "material_mismatch": not all_hold,
    }


def stage_d_preflight_verdict(comparison: dict) -> dict:
    """The single pass/fail decision the Stage D readiness verdict is built on -- mirrors
    `j11_stage_c.stage_c_overall_verdict`'s shape."""
    if not comparison.get("all_invariants_hold"):
        failing = [k for k, v in comparison.get("checks", {}).items() if not v]
        return {"passed": False, "reason": "preflight_comparison_gate_failed", "failing_checks": failing}
    return {"passed": True, "reason": "all_checks_passed"}


# ----------------------------------------------------------------------------------------------
# Goal 5 -- explicit Stage D readiness verdict (does NOT authorize Stage D)
# ----------------------------------------------------------------------------------------------

_AVB_READY_CLASSIFICATIONS = ("AVB-A", "AVB-B")
_AVB_BLOCKING_CLASSIFICATIONS = ("AVB-C", "AVB-D")


def stage_d_readiness_verdict(preflight_verdict: dict, avb_classification: str) -> dict:
    """Combines the preflight gate's verdict (Goal 3a) with the AVB diagnostic's classification (Goal 4)
    into the single `J-11 STAGE D READY: YES/NO` decision (TC-25) -- AVB-C/AVB-D forces `NO` regardless
    of the preflight gate's own result. `authorized` is unconditionally `False`: this verdict never
    self-authorizes Stage D (the C10/A12 pattern -- a separate owner instruction is required)."""
    if avb_classification not in _AVB_READY_CLASSIFICATIONS + _AVB_BLOCKING_CLASSIFICATIONS:
        raise ValueError(f"unknown avb_classification {avb_classification!r}")
    avb_blocks = avb_classification in _AVB_BLOCKING_CLASSIFICATIONS
    preflight_passed = bool(preflight_verdict.get("passed"))
    ready = preflight_passed and not avb_blocks

    blocking_reasons: list[str] = []
    if not preflight_passed:
        blocking_reasons.append(f"preflight_gate_failed:{preflight_verdict.get('reason')}")
    if avb_blocks:
        blocking_reasons.append(f"avb_classification_blocks:{avb_classification}")

    return {
        "generated_at": _now_iso(),
        "ready": ready,
        "preflight_gate_passed": preflight_passed,
        "preflight_gate_reason": preflight_verdict.get("reason"),
        "avb_classification": avb_classification,
        "blocking_reasons": blocking_reasons,
        "authorized": False,
    }
