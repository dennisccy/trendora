"""app.engine.j11_preboot_guard -- goal-market-compass iter-16 (Goals 6/7).

Implements the "OWNER RULING -- pre-boot incident guard required" (docs/goal.md J-11 step 11, owner
2026-08-25): iteration 15 proved that `apps/backend/main.py`'s ordinary boot path
(`warmup.ensure_latest_snapshot` -> `scanner.run_scan`) resolves the latest STORED price date and writes
a canonical `ScannerRun` for it unconditionally -- so while the latest `daily_prices` date is an incident
date deliberately held at zero `ScannerRun`s (J-11's Stage-C-cleared quarantine), **merely booting the
backend can recreate derived state before Stage D is authorized.** "Operator discipline alone is no
longer sufficient."

This module is the reusable, state-driven substrate: `MaintenanceBoundary` (`app.models`) is the
persisted state; `evaluate_boundary_for_date` is the fail-closed core check; `register_boundary` /
`clear_boundary` are the generic (incident-agnostic) registration primitives; `register_j11_incident_
boundary` is the ONE place that ties a boundary's date-set to `j11_maintenance.INCIDENT_DATES` for the
CURRENT J-11 incident specifically.

**The design trap this module is built to avoid (owner's own words):** source production date
membership from `j11_maintenance.INCIDENT_DATES` (never a fresh literal), but drive the runtime
refuse/allow decision from PERSISTED STATE, not a hardcoded conditional -- otherwise a fixture-only
state change could never flip the guard's behaviour, and the guard would be untestable as "state-driven"
even though it claims to be. `evaluate_boundary_for_date` below reads ONLY `MaintenanceBoundary` rows; it
contains no reference to `INCIDENT_DATES`, `AVB`, or any incident-specific date anywhere in its body --
that wiring lives exclusively in `register_j11_incident_boundary`, a thin registration helper this
module's own tests exercise but which iteration 16 does NOT invoke against the live database (maintenance
isolation stays externally active; the live backend is never booted this iteration -- the guard is proven
on disposable fixture/in-memory state only).

**Fail-closed contract:** no `MaintenanceBoundary` row registered at all is the ONLY case that behaves as
a true no-op (allowed) -- the common, no-incident case every OTHER journey's boot already depends on. Any
row whose `active` flag or `quarantined_dates_json` cannot be read/parsed cleanly is treated as BLOCKING
(never silently skipped, never treated as cleared) -- "fails CLOSED on missing/unreadable/ambiguous
state, never fails open." An explicitly CLEARED row (`active=False`) never blocks, regardless of what its
date-set contains.

**goal-market-compass iter-17 (AG-8 fix).** The owner's "OWNER RULING -- J-11 maintenance-boundary
lifecycle AUTHORIZED" (docs/goal.md J-11 step 11, implementation requirement 3) flagged
`evaluate_boundary_for_date`'s original `select(MaintenanceBoundary)` as an unbounded whole-table ORM
load on a path every boot crosses. It is now (a) filtered to only the rows that can possibly matter --
`active IS NOT FALSE`, never `active == True` alone (SQL's three-valued comparison logic silently drops
`active IS NULL` rows under plain equality -- the exact trap the ruling names; `IS NOT` never yields NULL,
so an unreadable/NULL-active row is always fetched, never silently excluded); (b) column-projected to
only the four fields the decision needs; and (c) deterministically bounded via `.limit(...)`, failing
CLOSED (blocked, ambiguous) if the bound is exceeded rather than silently truncating a real match away.
Table-absence (the additive `maintenance_boundaries` table simply never created, because ordinary boot's
`create_db_and_tables()` never ran while maintenance isolation kept the live backend un-booted) is treated
as the SAME true no-op as "table exists, zero rows" -- `select(...)` against an absent table raises
`OperationalError`, which is checked for explicitly rather than allowed to propagate.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone
from typing import Iterable, Optional

from sqlalchemy import inspect as sa_inspect
from sqlmodel import Session, select

from app.engine import j11_maintenance
from app.models import MaintenanceBoundary

# THE J-11 incident boundary's registered name -- a literal identifier for THIS incident's row, exactly
# analogous to `j11_maintenance.INCIDENT_DATES` being a literal historical fact rather than a reusable
# threshold. The guard's own evaluation logic below never references this constant.
J11_INCIDENT_BOUNDARY_NAME = "j11-incident-recovery"

_DEFAULT_J11_BOUNDARY_REASON = (
    "J-11 incident-bounded derived-state quarantine (docs/goal.md) -- Stage D has not yet been "
    "authorized/executed for these dates; canonical producer writes are refused until this boundary is "
    "explicitly cleared by a future maintenance operation."
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ----------------------------------------------------------------------------------------------
# Generic, incident-agnostic registration primitives -- no reference to J-11/AVB/any specific date
# anywhere in this section.
# ----------------------------------------------------------------------------------------------


def register_boundary(
    session: Session, *, name: str, dates: Iterable[date], reason: str, active: bool = True,
) -> MaintenanceBoundary:
    """Insert-or-update (by unique `name`) a maintenance boundary row -- idempotent registration, never a
    second row for the same name. `dates` is stored as a JSON list of ISO date strings, sorted for a
    deterministic on-disk representation."""
    existing = session.exec(select(MaintenanceBoundary).where(MaintenanceBoundary.name == name)).first()
    dates_json = json.dumps(sorted(d.isoformat() for d in dates))
    now = _now()
    if existing is None:
        row = MaintenanceBoundary(
            name=name, quarantined_dates_json=dates_json, active=active, reason=reason,
            created_at=now, updated_at=now,
        )
    else:
        existing.quarantined_dates_json = dates_json
        existing.active = active
        existing.reason = reason
        existing.updated_at = now
        row = existing
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def clear_boundary(session: Session, name: str) -> Optional[MaintenanceBoundary]:
    """Marks the named boundary CLEARED (`active=False`) -- a no-op (returns `None`) if no such boundary
    is registered. Never DELETEs the row: the row itself stays queryable as an audit trail of a past
    incident boundary having existed and been lifted."""
    existing = session.exec(select(MaintenanceBoundary).where(MaintenanceBoundary.name == name)).first()
    if existing is None:
        return None
    existing.active = False
    existing.updated_at = _now()
    session.add(existing)
    session.commit()
    session.refresh(existing)
    return existing


def register_j11_incident_boundary(
    session: Session, *, active: bool = True, reason: str = _DEFAULT_J11_BOUNDARY_REASON,
) -> MaintenanceBoundary:
    """Registers (or updates) THE J-11 incident-recovery boundary, sourcing its date-set from the
    canonical `j11_maintenance.INCIDENT_DATES` -- never a fresh hardcoded list here (the exact design
    trap the owner's dispatch note flagged). This is the ONLY function in this module that imports or
    references `j11_maintenance` at all; `evaluate_boundary_for_date` below never does."""
    return register_boundary(
        session, name=J11_INCIDENT_BOUNDARY_NAME, dates=j11_maintenance.INCIDENT_DATES, reason=reason,
        active=active,
    )


# ----------------------------------------------------------------------------------------------
# The fail-closed, state-driven core check -- contains NO incident-specific conditional of any kind.
# ----------------------------------------------------------------------------------------------

# goal-market-compass iter-17 -- AG-8 fix (owner ruling, docs/goal.md J-11 step 11, implementation
# requirement 3: "apply a deterministic finite bound ... and fail closed if the bound is exceeded").
# Generous headroom over any realistic number of named maintenance boundaries this project will ever
# register at once (today: exactly one, "j11-incident-recovery") -- deterministic and finite, never an
# unbounded whole-table scan. No `j11_*.py` module is in `test_no_magic_numbers.CALC_FILES` (verified);
# this is boot-path plumbing, not a scoring/decision threshold, so -- following the established precedent
# of inline module constants elsewhere in this same file family (e.g.
# `j11_avb_correction._RATIO_RELATIVE_TOLERANCE`) -- this bound is a plain module constant here, not a
# new `config.yaml` entry.
_MAX_RELEVANT_BOUNDARY_ROWS = 100


def _relevant_boundary_rows_statement():
    """The bounded, filtered, column-projected statement the boot path actually runs -- factored out as
    its own pure statement-builder (no session, no execution) so a test can inspect the emitted SQL/LIMIT
    clause directly, never only the boolean result of running it.

    Filter: `active IS NOT FALSE` (SQLAlchemy `.isnot(False)`) -- NEVER `active == True` alone. Under
    SQL's three-valued comparison logic, `NULL = TRUE` evaluates to NULL/unknown (not TRUE), so plain
    equality SILENTLY DROPS `active IS NULL` rows -- the exact regression trap the owner's ruling names.
    `IS NOT` is defined to never itself yield NULL: `NULL IS NOT FALSE` evaluates to true, so an
    unreadable/NULL-active row is always fetched here and always reaches the ambiguous/fail-closed branch
    below in `evaluate_boundary_for_date` -- never silently excluded by the query itself. An explicitly
    cleared row (`active=False`) IS excluded here -- by design; clearing is authoritative (docs above).

    Projection: only the four fields the decision logic reads (`name`, `active`,
    `quarantined_dates_json`, `reason`) -- never `id`/`created_at`/`updated_at`, which this function never
    inspects (owner requirement 3: "project only the fields the decision needs where practical").

    Bound: `.limit(_MAX_RELEVANT_BOUNDARY_ROWS + 1)` -- fetches ONE row past the bound so the caller can
    distinguish "exactly at the bound" from "more matching rows exist than the bound allows" and fail
    closed on the latter, rather than silently truncating away a row that might have matched."""
    return (
        select(
            MaintenanceBoundary.name,
            MaintenanceBoundary.active,
            MaintenanceBoundary.quarantined_dates_json,
            MaintenanceBoundary.reason,
        )
        .where(MaintenanceBoundary.active.isnot(False))
        .limit(_MAX_RELEVANT_BOUNDARY_ROWS + 1)
    )


def evaluate_boundary_for_date(session: Session, one_date: date) -> dict:
    """Whether `one_date` currently falls inside an ACTIVE, cleanly-readable maintenance boundary.

    Returns `{"blocked": bool, "boundary_name": str|None, "reason": str|None, "ambiguous": bool}`.

      - The `maintenance_boundaries` table does not exist at all -> `blocked=False` -- the SAME true
        no-op as "table exists, zero rows" (iter-17: the table is purely additive and normally minted by
        ordinary boot, which maintenance isolation deliberately prevents; its absence is a consequence of
        the quarantine itself, never an error state).
      - No `MaintenanceBoundary` rows registered at all -> `blocked=False` (the true no-op / common
        no-incident case).
      - More than `_MAX_RELEVANT_BOUNDARY_ROWS` active-or-ambiguous rows exist -> `blocked=True,
        ambiguous=True` -- the deterministic bound was exceeded; fails CLOSED rather than scanning an
        unbounded set (AG-8).
      - A row with `active=True` whose parsed `quarantined_dates_json` contains `one_date` ->
        `blocked=True`, naming that row and its `reason`.
      - A row that is explicitly cleared (`active=False`) never blocks, regardless of its date-set --
        excluded by the query's own filter before any Python-level logic runs.
      - A row whose `active` flag is unreadable (SQL `NULL`), or whose `quarantined_dates_json` is
        missing, empty, malformed JSON, or not a JSON list of date strings, while otherwise appearing
        active-ish (not provably cleared) -> `blocked=True, ambiguous=True` -- fails CLOSED rather than
        silently skipping an unreadable row or assuming it is cleared.

    This function performs ONLY read queries; it never writes."""
    # Table-absence check FIRST -- `select(...)` against a table that does not exist raises
    # `sqlalchemy.exc.OperationalError` ("no such table"), not an empty result; checked explicitly here so
    # that exception never propagates. A genuinely unexpected inspection failure (anything other than a
    # clean "table present/absent" answer) is left to the CALLER's own fail-closed wrapping
    # (`warmup.ensure_latest_snapshot`'s try/except already treats any exception here as blocked), never
    # silently swallowed inside this function.
    if not sa_inspect(session.get_bind()).has_table(MaintenanceBoundary.__tablename__):
        return {"blocked": False, "boundary_name": None, "reason": None, "ambiguous": False}

    rows = session.exec(_relevant_boundary_rows_statement()).all()
    if len(rows) > _MAX_RELEVANT_BOUNDARY_ROWS:
        return {
            "blocked": True,
            "boundary_name": None,
            "reason": (
                f"more than {_MAX_RELEVANT_BOUNDARY_ROWS} active/unreadable maintenance-boundary rows "
                "exist -- failing closed rather than scanning an unbounded set (AG-8)"
            ),
            "ambiguous": True,
        }
    if not rows:
        return {"blocked": False, "boundary_name": None, "reason": None, "ambiguous": False}

    date_key = one_date.isoformat()
    ambiguous_names: list[str] = []
    for row in rows:
        # `active=False` rows are already excluded by `_relevant_boundary_rows_statement`'s own WHERE
        # filter above -- every row reaching this loop is either `active=True` or `active IS NULL`.
        if row.active is None:
            ambiguous_names.append(row.name)
            continue
        if not row.quarantined_dates_json:
            ambiguous_names.append(row.name)  # active but no date-set content at all
            continue
        try:
            parsed = json.loads(row.quarantined_dates_json)
            if not isinstance(parsed, list) or not all(isinstance(d, str) for d in parsed):
                raise ValueError("quarantined_dates_json did not decode to a JSON list of date strings")
        except (TypeError, ValueError, json.JSONDecodeError):
            ambiguous_names.append(row.name)
            continue
        if date_key in parsed:
            return {"blocked": True, "boundary_name": row.name, "reason": row.reason, "ambiguous": False}

    if ambiguous_names:
        return {
            "blocked": True,
            "boundary_name": ambiguous_names[0],
            "reason": (
                f"maintenance boundary state unreadable/ambiguous for {ambiguous_names!r} -- failing "
                "closed (cannot prove this date is not quarantined)"
            ),
            "ambiguous": True,
        }
    return {"blocked": False, "boundary_name": None, "reason": None, "ambiguous": False}
