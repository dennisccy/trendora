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
basis_disclosure` already resolves current-run identity by `as_of` + `source_run_created_at` and needs
no change from this module (see the comment on `NextSessionManifest.source_run_id` in `app/models.py`).
"""
from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Optional, Union

from sqlalchemy import func
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
