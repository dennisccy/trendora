"""app.engine.j11_maintenance -- J-11 Stages B/B1/B2 precondition tooling (goal-market-compass iter-10).

J-11 repairs the derived-state fallout of the iter-5 drill (`docs/handoffs/goal-market-compass-iter-5-dev.md`)
over 11 incident dates, but the destructive clear/regenerate (Stages C-G) is explicitly OUT OF SCOPE this
iteration (`docs/phases/goal-market-compass-iter-10.md`). This module is read-only/pure precondition
tooling only:

  - `capture_pre_reset_inventory(session)` -- Stage B: a read-only, column-projected snapshot of every
    row Stage C onward touches or must leave untouched. An audit checkpoint, not a second historical
    database (docs/goal.md Stage B wording).
  - `freeze_attempt_identity(session, config)` -- Stage B2: freezes ONE `engine_identity` (+ its decomposed
    config subset) for the WHOLE later regeneration attempt, so Stage D can prove every rebuilt run shares
    one identity rather than silently mixing "dates 1-5 under engine A, dates 6-11 under engine B"
    (docs/goal.md J-11 step 12).
  - `check_attempt_identity_consistency(frozen_identity, run_identity)` -- the PURE per-run invariant
    helper Stage D will call once per rebuilt run. Deliberately no aggregate-only form -- iter-9's AVB
    counter-example is the reason: a population-wide "all N matched" claim is exactly where the one real
    mismatch hides.

Nothing here deletes, updates, or inserts a snapshot/manifest/price row. `app.engine.compass.
basis_disclosure`'s DESIGN of resolving current-run identity by `as_of` + `source_run_created_at`
(never by dereferencing `source_run_id`) is correct and needs no change here — but its IMPLEMENTATION
had a fail-closed defect the owner's 2026-08-23 correction withdraws the earlier "needs no change"
reading on: `basis_disclosure` fabricated `{"status": "available"}` for a manifest with no recorded
generation basis at all. That defect is fixed directly in `app.engine.compass.basis_disclosure`
(goal-market-compass iter-11, J-11 step 11 ruling A4) — not in this module, which stays read-only/pure
precondition tooling as described above.
"""
from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Optional, Union

from sqlalchemy import func, text
from sqlmodel import Session, select

from app.config import Config, get_config
from app.engine import engine_identity
from app.engine.evidence import resolve_ledger_path
from app.engine.graveyard import resolve_staging_ledger_path
from app.models import (
    DailyPrice,
    DataProviderRun,
    ForwardReturn,
    NextSessionManifest,
    ScannerResult,
    ScannerRun,
    SectorScoreRow,
    ThemeScoreRow,
    Watchlist,
)

# The exact 11 incident dates from `data_provider_runs` id=538's own cascade record (docs/goal.md J-11,
# "The incident date set -- all 11, not the 8 currently absent"). These are INCIDENT-SPECIFIC historical
# facts, not a reusable threshold -- literal here for the SAME reason `app.engine.j10_recovery.
# RECOVERY_DATES` is a literal (docs/goal.md NOTES: "promoting them to config would misrepresent a single
# dated incident as a standing feature", contrary to AG-9's "not a standing path" framing).
# `test_no_magic_numbers.py`'s `CALC_FILES` deliberately excludes this module for the identical reason it
# excludes `j10_recovery.py` -- nothing here is a scoring weight, band edge, or decision cutoff.
INCIDENT_DATES: tuple[date, ...] = (
    date(2026, 5, 12),
    date(2026, 5, 13),
    date(2026, 7, 10),
    date(2026, 7, 13),
    date(2026, 7, 24),
    date(2026, 7, 27),
    date(2026, 8, 3),
    date(2026, 8, 5),
    date(2026, 8, 10),
    date(2026, 8, 11),
    date(2026, 8, 12),
)


def _utc_isoformat(value: Optional[datetime]) -> Optional[str]:
    """Same tzinfo-safe re-serialization `app.engine.compass._utc_isoformat` uses (SQLite drops tzinfo on
    round-trip) -- an honest `None` passes through unchanged, never a fabricated timestamp."""
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def _file_sha256(path: str) -> dict:
    """Read-only sha256 of a ledger file. A missing file records `exists: False` honestly (ledgers are
    append-only and may legitimately not exist yet) -- never a fabricated hash, never a crash."""
    resolved = Path(path)
    if not resolved.exists():
        return {"path": str(resolved), "exists": False, "sha256": None}
    return {"path": str(resolved), "exists": True, "sha256": hashlib.sha256(resolved.read_bytes()).hexdigest()}


def _count(session: Session, model: Any, **filters: Any) -> int:
    """A column-projected `COUNT(*)` -- never an ORM hydration of the matched rows (AG-8)."""
    stmt = select(func.count()).select_from(model)
    for key, value in filters.items():
        stmt = stmt.where(getattr(model, key) == value)
    return int(session.scalar(stmt) or 0)


def capture_pre_reset_inventory(session: Session) -> dict:
    """Stage B -- read-only snapshot of everything the later destructive stages (C onward, OUT OF SCOPE
    this iteration) touch or must leave untouched: per-incident-date derived row counts (from BOTH
    populations goal.md names -- rows a date's own run originated, and rows whose `measured_date` lands on
    that date regardless of originating run, i.e. the "holes on retained runs" population Stage E must
    repair), the `daily_prices` canonical-input coverage + a cheap SQL-side aggregate fingerprint (never a
    full ORM hydration of the ~3.3M-row table -- AG-8), the manifest inventory for the incident dates that
    currently carry one, and the audit/user-state row counts + ledger file hashes that must be
    byte-identical after any future J-11 stage. Every value here is READ; nothing is written."""
    captured_at = datetime.now(timezone.utc).isoformat()

    # ONE grouped scan of forward_returns for the "measured INTO an incident date" population (the
    # defensive-sweep hole population on possibly-RETAINED runs) -- never 11 separate full-table scans.
    measured_into_counts: dict[date, int] = dict(
        session.exec(
            select(ForwardReturn.measured_date, func.count())
            .where(ForwardReturn.measured_date.in_(INCIDENT_DATES))
            .group_by(ForwardReturn.measured_date)
        ).all()
    )

    manifests_by_date: dict[str, list[dict]] = {}
    manifest_rows = session.exec(
        select(NextSessionManifest)
        .where(NextSessionManifest.as_of.in_(INCIDENT_DATES))
        .order_by(NextSessionManifest.as_of, NextSessionManifest.version)
    ).all()
    for row in manifest_rows:
        manifests_by_date.setdefault(row.as_of.isoformat(), []).append(
            {
                "version": row.version,
                "mode": row.mode,
                "frozen": row.frozen,
                "source_run_id": row.source_run_id,
                "content_hash": row.content_hash,
                "manifest_hash": row.manifest_hash,
                "prospective_eligible": row.prospective_eligible,
                "available_at_utc": _utc_isoformat(row.available_at_utc),
            }
        )

    per_date: dict[str, dict] = {}
    for one_date in INCIDENT_DATES:
        key = one_date.isoformat()
        run = session.exec(select(ScannerRun).where(ScannerRun.asof_date == one_date)).first()
        run_id = run.id if run is not None else None
        per_date[key] = {
            "scanner_run": {
                "present": run is not None,
                "run_id": run_id,
                "created_at": _utc_isoformat(run.created_at) if run is not None else None,
                "engine_identity": run.engine_identity if run is not None else None,
            },
            "scanner_results_count": _count(session, ScannerResult, run_id=run_id),
            "sector_scores_count": _count(session, SectorScoreRow, run_id=run_id),
            "theme_scores_count": _count(session, ThemeScoreRow, run_id=run_id),
            "forward_returns_from_run_count": _count(session, ForwardReturn, run_id=run_id),
            "forward_returns_measured_into_count": int(measured_into_counts.get(one_date, 0)),
            "manifests": manifests_by_date.get(key, []),
        }

    price_row = session.exec(
        select(
            func.count(DailyPrice.id),
            func.min(DailyPrice.date),
            func.max(DailyPrice.date),
            func.sum(DailyPrice.id),
            func.sum(DailyPrice.open + DailyPrice.high + DailyPrice.low + DailyPrice.close + DailyPrice.volume),
        )
    ).one()
    row_count, min_date, max_date, id_sum, ohlcv_sum = price_row
    price_fingerprint_payload = {
        "row_count": int(row_count or 0),
        "min_date": min_date.isoformat() if min_date else None,
        "max_date": max_date.isoformat() if max_date else None,
        "id_sum": int(id_sum or 0),
        "ohlcv_sum": float(ohlcv_sum or 0.0),
    }
    price_fingerprint = hashlib.sha256(
        json.dumps(price_fingerprint_payload, sort_keys=True, default=str).encode()
    ).hexdigest()

    return {
        "captured_at": captured_at,
        "incident_dates": [d.isoformat() for d in INCIDENT_DATES],
        "per_date": per_date,
        "daily_prices": {**price_fingerprint_payload, "fingerprint": price_fingerprint},
        "data_provider_runs_count": _count(session, DataProviderRun),
        "watchlist_count": _count(session, Watchlist),
        "certified_claims_ledger": _file_sha256(resolve_ledger_path()),
        "staging_ledger": _file_sha256(resolve_staging_ledger_path()),
    }


def freeze_attempt_identity(session: Session, config: Optional[Config] = None) -> dict:
    """Stage B2 -- freezes ONE `engine_identity` for the WHOLE later J-11 regeneration attempt (Stages
    C-G, out of scope this iteration; docs/goal.md step 12's invariant: "Every `ScannerRun` recreated by
    one J-11 regeneration attempt MUST carry the same `engine_identity`, equal to the identity frozen in
    that attempt's pre-reset inventory"). `session` is accepted for call-shape symmetry with
    `capture_pre_reset_inventory` (a uniform three-function surface for the CLI script) -- this function
    itself performs no DB read: the frozen identity is purely code+config, via the SAME
    `app.engine.engine_identity.compute_engine_identity` function `scanner.persist_run_payload` already
    stamps onto every newly created `ScannerRun.engine_identity` (reused, not reimplemented -- so Stage
    D's later per-run check compares like with like).

    `config_subset`/`config_subset_hash` decompose the SAME `provenance.config_keys` values
    `compute_engine_identity` already folds into its digest -- recorded here in cleartext (not just
    hashed) so `j11-frozen-identity.json` is itself human-auditable: a reader can see WHICH config values
    were frozen for this attempt, not just a hash of them."""
    cfg = config or get_config()
    identity = engine_identity.compute_engine_identity(cfg)
    cfg_dict = cfg.model_dump()
    config_subset = {key: engine_identity._config_value(cfg_dict, key) for key in cfg.provenance.config_keys}
    config_subset_hash = hashlib.sha256(
        json.dumps(config_subset, sort_keys=True, default=str).encode()
    ).hexdigest()
    return {
        "engine_identity": identity,
        "config_subset_hash": config_subset_hash,
        "config_subset": config_subset,
        "provenance_config_keys": list(cfg.provenance.config_keys),
        "provenance_engine_files": list(cfg.provenance.engine_files),
        "frozen_at": datetime.now(timezone.utc).isoformat(),
    }


def capture_full_table_sweep(session: Session) -> dict:
    """goal-market-compass iter-18 -- a schema-agnostic, read-only row-count-and-content-fingerprint
    sweep over EVERY table currently listed in `sqlite_master`. This is the J-11 table-create + arm live
    sequence's mutation-accounting evidence (docs/goal.md J-11 step 11, "OWNER RULING -- J-11 exact
    maintenance-boundary table creation and live arm AUTHORIZED", implementation requirement 4: "capture
    before/after evidence proving no unrelated application state changed").

    For each table, computes the SAME cheap SQL-side aggregate this module's own `_count`/
    `capture_pre_reset_inventory` idiom already relies on for the narrower per-population case (count + a
    bounded set of aggregates -> sha256, never a full ORM hydration of a multi-million-row table -- AG-8)
    -- generalized here to SQLite's own hidden `rowid` so it needs no per-table column knowledge at all.
    Every table in this schema is an ordinary rowid table (a plain `id INTEGER PRIMARY KEY` column with
    no `AUTOINCREMENT`, verified against the live schema for all 24 pre-existing tables, including empty
    ones) -- none is declared `WITHOUT ROWID`, so `rowid` is universally available and requires no schema
    introspection per table.

    This is a CORROBORATING check, never the PRIMARY instrument: a same-rowid content UPDATE (e.g. a
    non-key column changed on an existing row) would NOT move `count`/`min`/`max`/`sum` of `rowid` and so
    would NOT be caught by this sweep alone -- the whole-file mtime/size/`-wal` bracket
    (`j11_stage_c.db_file_fingerprint`, captured by the calling script at the TRUE process start and TRUE
    process end) is the PRIMARY instrument that would catch that, per iter-12/13's established "mtime+WAL
    as primary instrument, corroborated NOT replaced by a narrower fingerprint" precedent. Read-only --
    never writes; never touches `maintenance_boundaries` specially (a caller comparing before/after
    naturally sees it appear between the two sweeps, with a fingerprint of its own)."""
    table_names = sorted(
        row[0]
        for row in session.exec(
            text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        ).all()
    )
    per_table: dict[str, dict] = {}
    for name in table_names:
        # Table names here come ONLY from `sqlite_master` itself (never user input) -- safe to interpolate
        # into the FROM clause; every bind-able value (there are none here) would still go through
        # parameters. Double-quoted identifier so a table name is never ambiguous with a keyword.
        count, min_rowid, max_rowid, sum_rowid = session.exec(
            text(f'SELECT COUNT(*), MIN(rowid), MAX(rowid), SUM(rowid) FROM "{name}"')
        ).one()
        payload = {
            "count": int(count or 0),
            "min_rowid": int(min_rowid) if min_rowid is not None else None,
            "max_rowid": int(max_rowid) if max_rowid is not None else None,
            "sum_rowid": int(sum_rowid) if sum_rowid is not None else None,
        }
        fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()
        per_table[name] = {**payload, "fingerprint": fingerprint}
    return {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "table_names": table_names,
        "table_count": len(table_names),
        "per_table": per_table,
    }


def diff_full_table_sweeps(before: dict, after: dict, *, expected_new_tables: tuple[str, ...] = ()) -> dict:
    """Compares two `capture_full_table_sweep(...)` results. `expected_new_tables` names tables that are
    PERMITTED to be new in `after` (e.g. `("maintenance_boundaries",)`) -- any OTHER new or removed table,
    or ANY fingerprint change on a table present in BOTH sweeps, is an unexpected mutation. Never mutates
    its inputs; pure comparison."""
    before_tables = set(before["per_table"])
    after_tables = set(after["per_table"])
    unexpected_new = sorted((after_tables - before_tables) - set(expected_new_tables))
    unexpected_removed = sorted(before_tables - after_tables)  # no table may ever disappear
    changed_existing = sorted(
        name
        for name in (before_tables & after_tables)
        if before["per_table"][name]["fingerprint"] != after["per_table"][name]["fingerprint"]
    )
    return {
        "unexpected_new_tables": unexpected_new,
        "unexpected_removed_tables": unexpected_removed,
        "changed_existing_tables": changed_existing,
        "expected_new_tables_present": sorted(t for t in expected_new_tables if t in after_tables),
        "clean": not unexpected_new and not unexpected_removed and not changed_existing,
    }


def check_attempt_identity_consistency(
    frozen_identity: Union[dict, str], run_identity: Optional[str]
) -> bool:
    """The PURE per-run invariant helper Stage D will call once per rebuilt run -- no aggregate-only form
    (iter-9 lesson: a population-wide "all matched" flag is exactly where the one real mismatch hides).
    `frozen_identity` accepts either the `dict` `freeze_attempt_identity` returns or a bare identity
    string, so a caller holding either shape need not unpack first. `run_identity` is the run's OWN
    stamped `ScannerRun.engine_identity` value -- fail-closed: `None` (a pre-stamping-era or
    not-yet-persisted run) is NEVER consistent, never silently treated as a match."""
    expected = frozen_identity.get("engine_identity") if isinstance(frozen_identity, dict) else frozen_identity
    return run_identity is not None and run_identity == expected
