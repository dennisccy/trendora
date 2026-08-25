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

import hashlib
import json
import os
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Optional, Union

from sqlalchemy import func
from sqlalchemy.engine import Engine
from sqlmodel import Session, select

from app.config import Config, get_config
from app.engine import engine_identity
from app.engine import j11_maintenance
from app.engine import j11_schema_migration as migration
from app.engine import j11_stage_c as jsc
from app.engine.j11_maintenance import INCIDENT_DATES
from app.models import DailyPrice, ForwardReturn, NextSessionManifest, ScannerRun


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
# goal-market-compass iter-15 (Goal 9) -- a READINESS-TIME-ONLY identity observation, explicitly labeled
# non-authorizing and non-reusable, layered ON TOP OF `freeze_stage_d_attempt_identity` rather than
# folded into it.
# ----------------------------------------------------------------------------------------------


def capture_readiness_time_identity_observation(
    session: Session,
    config: Optional[Config] = None,
    *,
    git_head: Optional[str] = None,
    goal_md_text: Optional[str] = None,
    prior_iteration_14_identity: Optional[str] = None,
) -> dict:
    """Goal 9 -- wraps `freeze_stage_d_attempt_identity` (left COMPLETELY UNCHANGED -- TC-39: it still
    takes no artifact-path parameter that could load a prior freeze) with explicit `readiness_time_only:
    true`, `authorizing: false`, `reusable_for_stage_d_execution: false` labels, so no later reader can
    mistake THIS iteration's re-derivation for a frozen Stage D EXECUTION identity available for reuse.

    These labels are added HERE, at this call-site wrapper, rather than inside
    `freeze_stage_d_attempt_identity`'s own return shape -- a REAL future Stage D execution must call
    THAT function fresh, immediately before its first write, once all code/config for that execution are
    final (`docs/goal.md` J-11 step 12); mutating its return shape risks a future caller reading these
    readiness-only labels as if they described that fresh call, rather than describing only this
    iteration's separate, non-binding observation (the interpretive call logged in
    `runs/goal-session-market-compass/state/assumptions.md`, iter-15 entry 2).

    `prior_iteration_14_identity` is iteration 14's own frozen `engine_identity` value, INJECTED by the
    caller (this function performs no file I/O and never hardcodes iteration 14's `53d2ffd1...` string
    literally) -- the comparison against it is stated HONESTLY, whichever way it falls (TC-38): `matches`
    is `True`/`False` when a prior value was supplied, or `None` (never assumed) when it was not."""
    fresh = freeze_stage_d_attempt_identity(session, config, git_head=git_head, goal_md_text=goal_md_text)
    matches_iteration_14 = (
        None if prior_iteration_14_identity is None
        else fresh["engine_identity"] == prior_iteration_14_identity
    )
    observation = dict(fresh)
    observation.update({
        "readiness_time_only": True,
        "authorizing": False,
        "reusable_for_stage_d_execution": False,
        "comparison_to_iteration_14_frozen_identity": {
            "iteration_14_frozen_engine_identity": prior_iteration_14_identity,
            "this_iteration_engine_identity": fresh["engine_identity"],
            "matches": matches_iteration_14,
            "note": (
                "stated honestly from a genuine equality comparison -- never assumed equal or assumed "
                "drifted; `matches: null` means iteration 14's value was not supplied to this call, not "
                "that the two are known to differ"
            ),
        },
    })
    return observation


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
    prior_iteration_14_identity: Optional[str] = None,
) -> dict:
    """Re-derives live state fresh (never trusting iteration 13's certified figures without re-proving
    them), composed entirely from already-existing read-only primitives. Writes nothing -- `session` is
    used for SELECTs only, `engine`/`db_path` only for DDL/file introspection. `goal_md_text`/`git_head`
    are injected by the caller so the whole capture stays a pure, fixture-testable composition.

    goal-market-compass iter-15 (Goal 9): `attempt_identity` is now captured via
    `capture_readiness_time_identity_observation` (labeled `readiness_time_only`/non-authorizing/
    non-reusable, honestly compared against `prior_iteration_14_identity` when supplied) instead of the
    raw `freeze_stage_d_attempt_identity` call iteration 14 made directly -- backward compatible: omitting
    `prior_iteration_14_identity` still returns the same `engine_identity`/`config_subset`/... fields
    iteration 14's shape carried, plus the new labels."""
    cfg = config or get_config()
    pre_reset_inventory = j11_maintenance.capture_pre_reset_inventory(session)
    attempt_identity = capture_readiness_time_identity_observation(
        session, cfg, git_head=git_head, goal_md_text=goal_md_text,
        prior_iteration_14_identity=prior_iteration_14_identity,
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


# ----------------------------------------------------------------------------------------------
# goal-market-compass iter-15 (Goal 1) -- reconcile iteration 14's contradictory truth: the stale
# `runs/goal-market-compass-iter-14/j11-stage-d-readiness.json` (avb_classification: AVB-B, ready: true,
# blocking_reasons: []) against `runs/goal-session-market-compass/iter-14/eval.md`'s own corrected
# owner-facing line (`J-11 STAGE D READY: NO`). Read-only; does NOT edit/delete/regenerate either source
# file -- both are loaded/quoted verbatim (AG-17) and this function's return value is always a NEW,
# separate artifact the caller persists elsewhere.
# ----------------------------------------------------------------------------------------------

# The dispatching coordinator's own captured true-start values (2026-08-25) -- to be RE-DERIVED live and
# COMPARED, never trusted verbatim (the coordinator's own words: "to verify rather than trust"). Any
# mismatch is reported explicitly, never silently reconciled. The two sha256 figures are TRUNCATED
# prefix...suffix excerpts as supplied, not full hashes -- compared via prefix/suffix match only, honestly
# labeled as weaker than full equality (see `_compare_against_owner_capture`).
OWNER_TRUE_START_CAPTURE: dict = {
    "db_mtime": 1787591622,
    "db_size_bytes": 8365871104,
    "all_11_incident_dates_zero_scanner_runs": True,
    "daily_prices_row_count": 3310374,
    "scanner_runs_total_count": 3117,
    "forward_returns_total_count": 6797728,
    "data_provider_runs_count": 549,
    "manifest_row_count": 24,
    "manifest_ddl_sha256_prefix": "9f653c81",
    "manifest_ddl_sha256_suffix": "c501ee",
    "watchlist_count": 6,
    "forward_returns_measured_into_incident_total": 16614,
    "scanner_runs_stamped_6261ca17_count": 34,
    "avb_daily_prices_sha256_prefix": "0257c56d",
    "avb_daily_prices_sha256_suffix": "0b11cd",
}

# iteration 10's earlier-attempt identity prefix (the 34 surviving runs) -- a literal historical fact
# about this incident, same posture as `INCIDENT_DATES` (see `j11_maintenance.py`'s own module docstring).
_LEGACY_ATTEMPT_IDENTITY_PREFIX = "6261ca17"

_READINESS_LINE_RE = re.compile(r"`(J-11 STAGE D READY:\s*(?:YES|NO))`")


def _scanner_runs_by_identity_group(session: Session) -> dict:
    """`scanner_runs` grouped into NULL / `6261ca17...` (iteration 10's earlier-attempt identity) /
    anything-else `engine_identity` buckets -- the EXACT id set for the `6261ca17...` group (not merely
    its count), mirroring `j11_stage_c.small_table_id_snapshot`'s full-enumeration idiom, since TC-44
    requires the exact 34-row id set (not just its count) to be proven byte-identical before/after."""
    rows = session.exec(select(ScannerRun.id, ScannerRun.engine_identity)).all()
    null_ids: list[int] = []
    legacy_ids: list[int] = []
    other_ids: list[int] = []
    for run_id, identity in rows:
        if identity is None:
            null_ids.append(int(run_id))
        elif identity.startswith(_LEGACY_ATTEMPT_IDENTITY_PREFIX):
            legacy_ids.append(int(run_id))
        else:
            other_ids.append(int(run_id))
    return {
        "null_count": len(null_ids),
        "legacy_6261ca17_count": len(legacy_ids),
        "legacy_6261ca17_ids": sorted(legacy_ids),
        "other_count": len(other_ids),
        "other_ids": sorted(other_ids),
    }


def _avb_daily_prices_fingerprint(session: Session) -> dict:
    """AVB's OWN `daily_prices` content fingerprint -- the SAME sha256-over-canonical-JSON pattern
    `j11_maintenance.capture_pre_reset_inventory`'s whole-table `daily_prices` fingerprint already uses
    (row_count/min_date/max_date/id_sum/ohlcv_sum -> sha256), scoped to `symbol == "AVB"` (Goal 1's own
    instruction: reuse the pattern, never reinvent it)."""
    row = session.exec(
        select(
            func.count(DailyPrice.id),
            func.min(DailyPrice.date),
            func.max(DailyPrice.date),
            func.sum(DailyPrice.id),
            func.sum(DailyPrice.open + DailyPrice.high + DailyPrice.low + DailyPrice.close + DailyPrice.volume),
        ).where(DailyPrice.symbol == "AVB")
    ).one()
    row_count, min_date, max_date, id_sum, ohlcv_sum = row
    payload = {
        "row_count": int(row_count or 0),
        "min_date": min_date.isoformat() if min_date else None,
        "max_date": max_date.isoformat() if max_date else None,
        "id_sum": int(id_sum or 0),
        "ohlcv_sum": float(ohlcv_sum or 0.0),
    }
    fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()
    return {**payload, "fingerprint": fingerprint}


def _prefix_suffix_match(full_value: Optional[str], prefix: Optional[str], suffix: Optional[str]) -> bool:
    if not full_value or not prefix or not suffix:
        return False
    return full_value.startswith(prefix) and full_value.endswith(suffix)


def _compare_against_owner_capture(derived: dict, owner_capture: dict) -> dict:
    """Per-figure match/mismatch against the owner's captured true-start values (TC-1) -- ANY mismatch is
    reported explicitly, never silently reconciled or explained away. Count/boolean figures are compared
    by EXACT equality (`comparison_method: exact`); the two sha256 figures the owner captured are
    TRUNCATED prefix...suffix excerpts (not full hashes), so they are compared via `startswith`/`endswith`
    only and honestly labeled `comparison_method: prefix_suffix_excerpt_not_full_hash` -- a materially
    WEAKER proof than full equality, never silently presented as a complete cryptographic match."""
    comparisons: dict[str, dict] = {}

    def _exact(name: str, derived_value: Any, owner_key: str) -> None:
        owner_value = owner_capture.get(owner_key)
        comparisons[name] = {
            "derived_value": derived_value,
            "owner_value": owner_value,
            "comparison_method": "exact",
            "matches_owner_capture": derived_value == owner_value,
        }

    def _prefix_suffix(name: str, derived_full_value: str, prefix_key: str, suffix_key: str) -> None:
        prefix, suffix = owner_capture.get(prefix_key), owner_capture.get(suffix_key)
        comparisons[name] = {
            "derived_value": derived_full_value,
            "owner_value_prefix": prefix,
            "owner_value_suffix": suffix,
            "comparison_method": "prefix_suffix_excerpt_not_full_hash",
            "matches_owner_capture": _prefix_suffix_match(derived_full_value, prefix, suffix),
        }

    db_file = derived.get("db_file") or {}
    _exact(
        "db_mtime",
        int(db_file["mtime"]) if db_file.get("exists") and db_file.get("mtime") is not None else None,
        "db_mtime",
    )
    _exact("db_size_bytes", db_file.get("size_bytes"), "db_size_bytes")
    _exact(
        "all_11_incident_dates_zero_scanner_runs",
        derived["all_11_incident_dates_zero_scanner_runs"], "all_11_incident_dates_zero_scanner_runs",
    )
    _exact("daily_prices_row_count", derived["daily_prices_row_count"], "daily_prices_row_count")
    _exact("scanner_runs_total_count", derived["scanner_runs_total_count"], "scanner_runs_total_count")
    _exact("forward_returns_total_count", derived["forward_returns_total_count"], "forward_returns_total_count")
    _exact("data_provider_runs_count", derived["data_provider_runs_count"], "data_provider_runs_count")
    _exact("manifest_row_count", derived["manifest_row_count"], "manifest_row_count")
    _exact("watchlist_count", derived["watchlist_count"], "watchlist_count")
    _exact(
        "forward_returns_measured_into_incident_total",
        derived["forward_returns_measured_into_incident_total"], "forward_returns_measured_into_incident_total",
    )
    _exact(
        "scanner_runs_stamped_6261ca17_count",
        derived["scanner_runs_by_identity_group"]["legacy_6261ca17_count"], "scanner_runs_stamped_6261ca17_count",
    )
    _prefix_suffix(
        "manifest_ddl_sha256", derived["manifest_ddl_sha256"], "manifest_ddl_sha256_prefix", "manifest_ddl_sha256_suffix",
    )
    _prefix_suffix(
        "avb_daily_prices_sha256", derived["avb_daily_prices_fingerprint"]["fingerprint"],
        "avb_daily_prices_sha256_prefix", "avb_daily_prices_sha256_suffix",
    )
    return comparisons


def _extract_readiness_line(eval_md_text: str) -> str:
    """The literal backtick-quoted `J-11 STAGE D READY: YES/NO` line(s) inside iteration 14's eval.md,
    extracted read-only via a fail-closed anchored regex (never a broad guess, mirroring `j11_stage_c.
    extract_incident_date_lists`'s own anchor-based-extraction posture). Raises if no such line is found,
    or if multiple are found and they CONTRADICT each other -- never silently picks one."""
    matches = _READINESS_LINE_RE.findall(eval_md_text)
    if not matches:
        raise ValueError("no backtick-quoted 'J-11 STAGE D READY: YES/NO' line found in the supplied eval.md text")
    unique = sorted(set(matches))
    if len(unique) > 1:
        raise ValueError(f"eval.md contains CONTRADICTORY backtick-quoted readiness lines: {unique}")
    return matches[0]


def reconcile_prior_iteration_truth(
    session: Session,
    engine: Engine,
    db_path: Optional[Path],
    *,
    iteration_14_readiness_path: Path,
    iteration_14_eval_md_path: Path,
    owner_true_start_capture: Optional[dict] = None,
) -> dict:
    """Goal 1 -- re-derives, LIVE and READ-ONLY, the figures the dispatching coordinator's true-start
    capture named, compares each against that capture (verify, never trust it), and reconciles iteration
    14's two contradictory J-11 Stage D readiness conclusions: the stale machine-readable
    `j11-stage-d-readiness.json` (`avb_classification: "AVB-B"`, `ready: true`, `blocking_reasons: []`)
    against `iter-14/eval.md`'s own corrected owner-facing line (`J-11 STAGE D READY: NO`).

    Composed ENTIRELY from already-existing read-only primitives -- `j11_maintenance.
    capture_pre_reset_inventory` for the 11-date `ScannerRun`/forward-return/manifest figures,
    `j11_schema_migration.fetch_object_ddl`/`dump_table` for the manifest DDL/dump -- never reimplemented.

    Any mismatch against `owner_true_start_capture` is recorded EXPLICITLY (a `matches_owner_capture:
    False` entry with both values side by side) -- never silently reconciled, explained away, or omitted
    from the returned artifact. Does NOT edit, delete, or regenerate `iteration_14_readiness_path` or
    `iteration_14_eval_md_path` -- both are loaded/read-only and quoted verbatim (AG-17); this function's
    return value is always a NEW, separate artifact for the caller to persist elsewhere."""
    owner_capture = owner_true_start_capture if owner_true_start_capture is not None else OWNER_TRUE_START_CAPTURE

    pre_reset_inventory = j11_maintenance.capture_pre_reset_inventory(session)
    incident_dates = pre_reset_inventory["incident_dates"]
    per_date = pre_reset_inventory["per_date"]

    all_11_zero = not any(per_date[d]["scanner_run"]["present"] for d in incident_dates)
    forward_returns_measured_into_incident_total = sum(
        int(per_date[d]["forward_returns_measured_into_count"]) for d in incident_dates
    )

    scanner_runs_total_count = int(session.scalar(select(func.count()).select_from(ScannerRun)) or 0)
    scanner_runs_by_identity_group = _scanner_runs_by_identity_group(session)
    forward_returns_total_count = int(session.scalar(select(func.count()).select_from(ForwardReturn)) or 0)

    manifest_ddl = migration.fetch_object_ddl(engine, migration.TABLE_NAME)
    manifest_dump = migration.dump_table(engine, NextSessionManifest.__table__)
    manifest_ddl_sha256 = hashlib.sha256((manifest_ddl.get("table_sql") or "").encode("utf-8")).hexdigest()
    manifest_dump_sha256 = hashlib.sha256(
        json.dumps(manifest_dump, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()

    avb_daily_prices_fingerprint = _avb_daily_prices_fingerprint(session)
    db_file = jsc.db_file_fingerprint(db_path) if db_path is not None else {"exists": False}

    derived: dict[str, Any] = {
        "db_file": db_file,
        "all_11_incident_dates_zero_scanner_runs": all_11_zero,
        "per_date_scanner_run_present": {
            d: bool(per_date[d]["scanner_run"]["present"]) for d in incident_dates
        },
        "daily_prices_row_count": pre_reset_inventory["daily_prices"]["row_count"],
        "daily_prices_fingerprint": pre_reset_inventory["daily_prices"]["fingerprint"],
        "scanner_runs_total_count": scanner_runs_total_count,
        "scanner_runs_by_identity_group": scanner_runs_by_identity_group,
        "forward_returns_total_count": forward_returns_total_count,
        "forward_returns_measured_into_incident_total": forward_returns_measured_into_incident_total,
        "data_provider_runs_count": pre_reset_inventory["data_provider_runs_count"],
        "manifest_row_count": len(manifest_dump),
        "manifest_ddl_sha256": manifest_ddl_sha256,
        "manifest_dump_sha256_own_method": manifest_dump_sha256,
        "watchlist_count": pre_reset_inventory["watchlist_count"],
        "avb_daily_prices_fingerprint": avb_daily_prices_fingerprint,
    }

    comparisons = _compare_against_owner_capture(derived, owner_capture)
    any_mismatch = any(not c["matches_owner_capture"] for c in comparisons.values())

    stale_readiness_payload = json.loads(Path(iteration_14_readiness_path).read_text())
    eval_md_text = Path(iteration_14_eval_md_path).read_text()
    corrected_line = _extract_readiness_line(eval_md_text)

    return {
        "generated_at": _now_iso(),
        "derived_live_read_only": derived,
        "owner_true_start_capture": owner_capture,
        "comparisons_against_owner_capture": comparisons,
        "any_mismatch_against_owner_capture": any_mismatch,
        "forward_returns_measured_into_incident_total_matches_16614": (
            forward_returns_measured_into_incident_total == 16614
        ),
        "iteration_14_stale_artifact": {
            "path": str(iteration_14_readiness_path),
            "content_verbatim": stale_readiness_payload,
            "stale_artifact_superseded": True,
            "superseded_by": (
                "runs/goal-market-compass-iter-15/j11-stage-d-readiness.json "
                "(this iteration's committed producer output, Goal 7)"
            ),
        },
        "iteration_14_eval_md_corrected_line": {
            "path": str(iteration_14_eval_md_path),
            "quoted_line": corrected_line,
        },
        "reconciliation_statement": (
            f"{iteration_14_readiness_path} records "
            f"avb_classification={stale_readiness_payload.get('avb_classification')!r} "
            f"ready={stale_readiness_payload.get('ready')!r} "
            f"blocking_reasons={stale_readiness_payload.get('blocking_reasons')!r}, which CONTRADICTS "
            f"{iteration_14_eval_md_path}'s own corrected owner-facing line ({corrected_line!r}). The "
            "stale JSON artifact is SUPERSEDED -- its underlying classify_avb/"
            "compute_counterfactual_representations inputs were price-only-tautological "
            "(volume_a == volume_b == stored_volume by construction), which this iteration's Goal 3/4 "
            "fix closes. It is preserved BYTE-FOR-BYTE as historical evidence (AG-17) and is NOT edited, "
            "deleted, or regenerated by this function -- only loaded read-only and quoted verbatim above. "
            "The current authoritative result is this iteration's OWN freshly-produced "
            "runs/goal-market-compass-iter-15/j11-stage-d-readiness.json (Goal 7's committed producer)."
        ),
    }


# ----------------------------------------------------------------------------------------------
# goal-market-compass iter-15 (Goal 7) -- a COMMITTED, non-test caller of `stage_d_readiness_verdict`.
# `stage_d_readiness_verdict` was called only from `tests/test_j11_stage_d.py` through iteration 14,
# which is precisely why that iteration's `j11-stage-d-readiness.json` went stale relative to its own
# evaluator's corrected conclusion (nothing in committed, non-test code ever re-derived it).
# ----------------------------------------------------------------------------------------------

_KNOWN_AVB_CLASSIFICATIONS = _AVB_READY_CLASSIFICATIONS + _AVB_BLOCKING_CLASSIFICATIONS

# The staleness bound between the two input artifacts' OWN `generated_at` timestamps -- the only
# cross-artifact provenance signal both of `produce_stage_d_readiness_artifact`'s two-path inputs
# actually carry (neither the preflight-gate JSON nor the AVB-diagnostic JSON embeds the OTHER's raw
# db-file mtime/size within this function's narrow two-path signature). A documented, generous
# same-maintenance-session bound -- not a scoring/decision threshold, so this module's `CALC_FILES`
# exclusion (this module carries no entry there at all) applies identically to this constant.
_MAX_ARTIFACT_GENERATION_SKEW_SECONDS = 6 * 60 * 60  # 6 hours


def _preflight_gate_generated_at(payload: dict) -> Optional[str]:
    comparison = payload.get("comparison") if isinstance(payload, dict) else None
    return comparison.get("generated_at") if isinstance(comparison, dict) else None


def _avb_diagnostic_generated_at(payload: dict) -> Optional[str]:
    return payload.get("generated_at") if isinstance(payload, dict) else None


def _parse_iso(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)


def _generation_staleness_check(preflight_gate_payload: dict, avb_diagnostic_payload: dict) -> dict:
    """Whether the two input artifacts were plausibly captured against the SAME live-database state --
    TC-33. `consistent: False` on a missing/unparseable timestamp OR a skew beyond the documented bound;
    the specific contradiction is always recorded, never just a bare boolean."""
    preflight_ts_raw = _preflight_gate_generated_at(preflight_gate_payload)
    avb_ts_raw = _avb_diagnostic_generated_at(avb_diagnostic_payload)
    if not preflight_ts_raw or not avb_ts_raw:
        return {
            "consistent": False,
            "reason": "missing_generated_at_timestamp",
            "preflight_gate_generated_at": preflight_ts_raw,
            "avb_diagnostic_generated_at": avb_ts_raw,
        }
    try:
        preflight_ts = _parse_iso(preflight_ts_raw)
        avb_ts = _parse_iso(avb_ts_raw)
    except ValueError as exc:
        return {
            "consistent": False,
            "reason": f"unparseable_generated_at_timestamp: {exc}",
            "preflight_gate_generated_at": preflight_ts_raw,
            "avb_diagnostic_generated_at": avb_ts_raw,
        }
    skew_seconds = abs((preflight_ts - avb_ts).total_seconds())
    consistent = skew_seconds <= _MAX_ARTIFACT_GENERATION_SKEW_SECONDS
    return {
        "consistent": consistent,
        "reason": "within_bound" if consistent else "generation_timestamp_skew_exceeds_bound",
        "preflight_gate_generated_at": preflight_ts_raw,
        "avb_diagnostic_generated_at": avb_ts_raw,
        "skew_seconds": skew_seconds,
        "max_allowed_skew_seconds": _MAX_ARTIFACT_GENERATION_SKEW_SECONDS,
    }


def produce_stage_d_readiness_artifact(
    preflight_gate_path: Path, avb_diagnostic_path: Path, *, output_path: Path
) -> dict:
    """Goal 7 -- the FIRST committed (non-test) caller of `stage_d_readiness_verdict`. Reads BOTH
    artifacts from caller-supplied paths (never hand-typed values), calls the EXISTING `stage_d_readiness_
    verdict` (reused, never reimplemented), writes the result with `authorized: false` UNCONDITIONALLY,
    and records the exact provenance paths of both inputs.

    Fails closed (raises `ValueError`, writes NOTHING) when: either input path is missing or unreadable;
    the AVB artifact's `classification` field is missing or not one of the four known labels (TC-32); or
    the two artifacts' own `generated_at` timestamps disagree beyond `_MAX_ARTIFACT_GENERATION_SKEW_
    SECONDS` (TC-33) -- they were not plausibly captured against the same live-database state. Every
    fail-closed check runs BEFORE the write statement, so no partial artifact is ever left behind."""
    preflight_gate_path = Path(preflight_gate_path)
    avb_diagnostic_path = Path(avb_diagnostic_path)
    output_path = Path(output_path)

    if not preflight_gate_path.exists():
        raise ValueError(f"preflight gate artifact not found: {preflight_gate_path}")
    if not avb_diagnostic_path.exists():
        raise ValueError(f"AVB diagnostic artifact not found: {avb_diagnostic_path}")

    try:
        preflight_gate_payload = json.loads(preflight_gate_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"preflight gate artifact unreadable ({preflight_gate_path}): {exc}") from exc
    try:
        avb_diagnostic_payload = json.loads(avb_diagnostic_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"AVB diagnostic artifact unreadable ({avb_diagnostic_path}): {exc}") from exc

    verdict = preflight_gate_payload.get("verdict") if isinstance(preflight_gate_payload, dict) else None
    if not isinstance(verdict, dict) or "passed" not in verdict:
        raise ValueError(f"{preflight_gate_path} does not carry a recognizable preflight verdict object")

    classification_block = (
        avb_diagnostic_payload.get("classification") if isinstance(avb_diagnostic_payload, dict) else None
    )
    avb_classification = (
        classification_block.get("classification") if isinstance(classification_block, dict) else None
    )
    if avb_classification not in _KNOWN_AVB_CLASSIFICATIONS:
        raise ValueError(
            f"{avb_diagnostic_path} does not carry a recognized AVB classification "
            f"(found {avb_classification!r}, expected one of {_KNOWN_AVB_CLASSIFICATIONS}) -- refusing "
            "to produce a readiness artifact"
        )

    staleness = _generation_staleness_check(preflight_gate_payload, avb_diagnostic_payload)
    if not staleness["consistent"]:
        raise ValueError(
            f"the two input artifacts disagree on the live-database state they were captured against "
            f"({staleness}) -- refusing to combine them into one readiness verdict"
        )

    readiness = stage_d_readiness_verdict(verdict, avb_classification)
    readiness["authorized"] = False  # unconditional, regardless of what the inputs say
    readiness["inputs"] = {
        "preflight_gate_artifact": str(preflight_gate_path),
        "avb_diagnostic_artifact": str(avb_diagnostic_path),
    }
    readiness["staleness_check"] = staleness

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(readiness, indent=2, sort_keys=True, default=str))
    return readiness
