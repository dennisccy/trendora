"""app.engine.j11_avb_correction -- goal-market-compass iter-16.

Implements the two new owner rulings recorded in `docs/goal.md` J-11 step 11, immediately after ruling
C12, both dated 2026-08-25:

  - **"OWNER RULING -- AVB two-row raw-volume correction before Stage D."** Iteration 15 proved (via the
    single-use AG-9 dated exception #2 provider fetch) that AVB's two J-10-recovered `daily_prices` rows
    (2026-08-11, 2026-08-12) carry `bridged price + RAW volume`, while every surrounding stored AVB bar
    (the four-date calibration window) carries `bridged price + COMPENSATING volume` -- so the recovered
    rows' dollar volume is inflated by approximately the persisted bridge factor
    (`2.7930001225759193`), which classifies as `AVB-C` (STAGE D NOT READY). The owner authorizes exactly
    ONE bounded corrective mutation: table `daily_prices`, symbol `AVB`, dates `2026-08-11`/`2026-08-12`,
    field `volume` ONLY -- derived **deterministically** from the already-committed iteration-15 evidence
    (`runs/goal-market-compass-iter-15/j11-avb-provider-fetch-evidence.json` + the persisted J-10
    `bridge_factor`), with **NO new network fetch** (AG-9 dated exception #2 stays exhausted). This module
    is the pure/read-only computation half: true-start/true-end envelope capture, the derivation itself,
    and the mutation-evidence comparison builder. The actual `UPDATE` statement lives in
    `apps/backend/scripts/run_j11_avb_correction.py` (mirrors the `j11_stage_c.py` /
    `run_j11_stage_c_bounded_clear.py` split: this module never writes).
  - **"OWNER RULING -- pre-boot incident guard required."** Handled by the SIBLING module
    `app.engine.j11_preboot_guard` (Goals 6/7) -- not this one.

**Verification-before-write discipline (iter-13's lesson, restated in the owner's own dispatch note):**
"capturing an invariant's value is not checking it, and a gate that cannot compare is a gate that always
passes." The true-start envelope this module captures is compared, in the CLI script, against the
coordinator's independently-posted true-start figures BEFORE any write is contemplated; any mismatch is
reported explicitly, never silently reconciled (docs/goal.md's own words). The exact isolating-hash
recipe below was independently re-derived (not copied blind) by probing the live, read-only database
until three candidate SQL/ordering choices reproduced the coordinator's three posted target digests
byte-for-byte, plus the manifest row-dump digest's posted truncated prefix/suffix -- see this module's
own hash helpers for the confirmed exact recipe.

**J-10 is NOT reopened by this module.** J-10 stays historically closed at its recorded terminal state
(585 restored; EA/EQR accepted unrestorable; AG-9's recovery-fetch authorization exhausted). This is a
narrowly authorized post-J-10 correction of a defect the J-11 readiness audit found -- not a recovery
programme, not a re-fetch, not a reclassification of J-10's own acceptance.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy import func, select as sa_select
from sqlalchemy.engine import Engine
from sqlmodel import Session, select

from app.config import REPO_ROOT
from app.engine import j11_avb_diagnostic as diag
from app.engine import j11_maintenance as jm
from app.engine import j11_schema_migration as migration
from app.engine import j11_stage_c as jsc
from app.engine import j11_stage_d as jsd
from app.models import DailyPrice, ForwardReturn

AVB_SYMBOL = "AVB"

# The two owner-authorized target dates (docs/goal.md, "OWNER RULING -- AVB two-row raw-volume
# correction before Stage D") -- a literal historical fact about THIS one-time correction, never a
# reusable threshold (same posture as `j11_maintenance.INCIDENT_DATES`/`j11_avb_diagnostic.
# RECOVERED_DATES`, which this tuple is deliberately equal to but kept as its OWN literal so this
# module's authorization boundary is self-contained and legible without cross-referencing another
# module's unrelated-purpose constant).
TARGET_DATES: tuple[date, ...] = (date(2026, 8, 11), date(2026, 8, 12))

DEFAULT_PROVIDER_FETCH_EVIDENCE_PATH = (
    REPO_ROOT / "runs" / "goal-market-compass-iter-15" / "j11-avb-provider-fetch-evidence.json"
)

# Reuse the SAME relative-tolerance band the calibration-window compensating check already uses (Goal
# 2's cross-check must land within it) -- never a fresh, independently-chosen number.
_RATIO_RELATIVE_TOLERANCE = diag._RATIO_RELATIVE_TOLERANCE

# The coordinator's independently-posted true-start capture (dispatch note, 2026-08-25) -- to be
# RE-DERIVED live and COMPARED, never trusted verbatim ("verify it yourself, don't trust it" -- the
# coordinator's own words). Any mismatch is reported explicitly, never silently reconciled. The three
# isolating hashes and the manifest DDL hash are compared by FULL sha256 equality (independently
# re-derived and confirmed byte-for-byte against a live read-only probe before this module was written);
# the manifest row-dump hash was posted only as a truncated `prefix...suffix` excerpt (the SAME
# `NNNNNNNN...NNNNNNN` shorthand `j11_stage_d.OWNER_TRUE_START_CAPTURE` already uses for this exact
# figure), so it is compared the SAME weaker prefix/suffix way, honestly labeled as such.
COORDINATOR_TRUE_START_CAPTURE: dict = {
    "db_mtime": 1787591622,
    "db_size_bytes": 8365871104,
    "db_wal_size_bytes": 0,
    "daily_prices_row_count": 3310374,
    "scanner_runs_total_count": 3117,
    "scanner_runs_stamped_6261ca17_count": 34,
    "forward_returns_total_count": 6797728,
    "forward_returns_measured_into_incident_total": 16614,
    "data_provider_runs_count": 549,
    "manifest_row_count": 24,
    "manifest_ddl_sha256": "9f653c8147c7c8931b07ea4a88d46ef1d6ddefb2ef5177b700d2b60e7fc501ee",
    "manifest_row_dump_sha256_prefix": "bb954b60",
    "manifest_row_dump_sha256_suffix": "6d2a2e6",
    "watchlist_count": 6,
    "all_11_incident_dates_zero_scanner_runs": True,
    "isolating_hashes": {
        "avb_ohlc_only": "757c3c63a39d7c167f691a929ec0579dd7e9584c20f6c9ff99879e6bec4c8fd3",
        "avb_other_dates_full_row": "53bca57105dad60137049f9a8b2350d6d6d0d3a6645337e4352b3fa5c56dc14f",
        "non_avb_full_row": "78146554cab8a2a619507e60cafa6354350d176f5685383d41c8c97899264997",
    },
    "avb_target_rows": {
        "2026-08-11": {
            "open": 183.22001534990548, "high": 184.13001191846783, "low": 181.7100027790582,
            "close": 181.76001476703186, "volume": 1549436.0,
        },
        "2026-08-12": {
            "open": 181.08999902870366, "high": 182.0900043902787, "low": 179.45999604273928,
            "close": 179.79000697488598, "volume": 10350885.0,
        },
    },
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ----------------------------------------------------------------------------------------------
# Read-only sqlite3 (mode=ro + PRAGMA query_only=ON) row-hash helpers -- the confirmed exact recipe.
# Never an ORM hydration of the matched rows (AG-8): each query streams through a raw sqlite3 cursor,
# hashing one row's `repr()` at a time into a running sha256, so memory stays O(1) regardless of row
# count (proven live against the ~3.3M-row non-AVB population).
# ----------------------------------------------------------------------------------------------


def _ro_connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.execute("PRAGMA query_only=ON")
    return conn


def _hash_query(db_path: Path, sql: str, params: tuple = ()) -> dict:
    """sha256 over `repr(row)` per row, in cursor iteration order, over a read-only connection. Returns
    `{sql, row_count, sha256}` -- the recipe is carried alongside every hash this module ever reports, so
    no hash is ever presented without a falsifiable recipe (iter-15b's lesson: "a fingerprint quoted into
    a spec without its recipe is an unfalsifiable verification target")."""
    conn = _ro_connect(db_path)
    try:
        cursor = conn.execute(sql, params)
        h = hashlib.sha256()
        row_count = 0
        for row in cursor:
            h.update(repr(row).encode())
            row_count += 1
        return {"sql": sql, "row_count": row_count, "sha256": h.hexdigest()}
    finally:
        conn.close()


_AVB_OHLC_ONLY_SQL = (
    "SELECT symbol, date, open, high, low, close FROM daily_prices WHERE symbol=? ORDER BY date"
)
_AVB_OTHER_DATES_FULL_ROW_SQL = (
    "SELECT symbol, date, open, high, low, close, volume FROM daily_prices "
    "WHERE symbol=? AND date NOT IN (?, ?) ORDER BY date"
)
_NON_AVB_FULL_ROW_SQL = (
    "SELECT symbol, date, open, high, low, close, volume FROM daily_prices WHERE symbol!=? ORDER BY symbol, date"
)
_MANIFEST_ROW_DUMP_SQL = "SELECT * FROM next_session_manifests ORDER BY id"


def capture_isolating_hashes(db_path: Path) -> dict:
    """The three population-partition hashes (iter-9's lesson: a population-wide uniform aggregate is
    exactly where the one real counter-example hides -- these prove the ABSENCE of collateral change on
    every partition the correction must NOT touch, not merely the presence of the intended change):
      - `avb_ohlc_only` -- every AVB row's (symbol, date, open, high, low, close), volume EXCLUDED,
        across ALL AVB dates including the two target dates (proves OHLC is untouched even for the
        rows being corrected).
      - `avb_other_dates_full_row` -- every AVB row's full (symbol, date, o, h, l, c, volume) EXCEPT the
        two target dates (proves no OTHER AVB date's volume moved).
      - `non_avb_full_row` -- every non-AVB `daily_prices` row's full tuple (proves no other symbol was
        touched at all)."""
    target_iso = [d.isoformat() for d in TARGET_DATES]
    return {
        "avb_ohlc_only": _hash_query(db_path, _AVB_OHLC_ONLY_SQL, (AVB_SYMBOL,)),
        "avb_other_dates_full_row": _hash_query(
            db_path, _AVB_OTHER_DATES_FULL_ROW_SQL, (AVB_SYMBOL, *target_iso)
        ),
        "non_avb_full_row": _hash_query(db_path, _NON_AVB_FULL_ROW_SQL, (AVB_SYMBOL,)),
    }


def capture_manifest_row_dump_hash(db_path: Path) -> dict:
    """The manifest row-dump fingerprint (distinct from `manifest_ddl_sha256`, which hashes the CREATE
    TABLE text only) -- SAME raw-sqlite3-repr recipe as the isolating hashes above, confirmed against the
    coordinator's posted truncated `bb954b60...6d2a2e6` reference."""
    return _hash_query(db_path, _MANIFEST_ROW_DUMP_SQL)


# ----------------------------------------------------------------------------------------------
# Goal 1/4 -- true-start / true-end safety envelope (the SAME capture function serves both; the CLI
# script calls it once before Goal 3's write and once immediately after).
# ----------------------------------------------------------------------------------------------


def fetch_avb_target_rows(session: Session) -> dict[str, dict]:
    """The two target rows' exact `(open, high, low, close, volume)`, column-projected, keyed by ISO
    date string."""
    rows = session.exec(
        select(
            DailyPrice.date, DailyPrice.open, DailyPrice.high, DailyPrice.low, DailyPrice.close,
            DailyPrice.volume,
        )
        .where(DailyPrice.symbol == AVB_SYMBOL)
        .where(DailyPrice.date.in_(TARGET_DATES))
        .order_by(DailyPrice.date)
    ).all()
    return {
        d.isoformat(): {"open": o, "high": h, "low": l, "close": c, "volume": v}
        for d, o, h, l, c, v in rows
    }


def capture_true_envelope(session: Session, engine: Engine, db_path: Optional[Path]) -> dict:
    """Goal 1 (true-start) / Goal 4 (true-end, same function reused) -- read-only, composed entirely
    from already-existing primitives (`j11_maintenance.capture_pre_reset_inventory`,
    `j11_stage_d._scanner_runs_by_identity_group` -- iter-15's own exact-id-set scanner-run breakdown,
    reused rather than reimplemented, `j11_schema_migration.fetch_object_ddl`, `j11_stage_c.
    db_file_fingerprint`) plus this module's own isolating-hash helpers. Writes nothing."""
    pre_reset_inventory = jm.capture_pre_reset_inventory(session)
    incident_dates = pre_reset_inventory["incident_dates"]
    all_11_zero = not any(
        pre_reset_inventory["per_date"][d]["scanner_run"]["present"] for d in incident_dates
    )
    forward_returns_measured_into_incident_total = sum(
        int(pre_reset_inventory["per_date"][d]["forward_returns_measured_into_count"]) for d in incident_dates
    )

    scanner_runs_by_identity_group = jsd._scanner_runs_by_identity_group(session)
    scanner_runs_total_count = (
        scanner_runs_by_identity_group["null_count"]
        + scanner_runs_by_identity_group["legacy_6261ca17_count"]
        + scanner_runs_by_identity_group["other_count"]
    )
    forward_returns_total_count = int(session.scalar(sa_select(func.count()).select_from(ForwardReturn)) or 0)

    manifest_ddl = migration.fetch_object_ddl(engine, migration.TABLE_NAME)
    manifest_ddl_sha256 = hashlib.sha256((manifest_ddl.get("table_sql") or "").encode("utf-8")).hexdigest()

    avb_target_rows = fetch_avb_target_rows(session)

    db_file = jsc.db_file_fingerprint(db_path) if db_path is not None else {"exists": False}
    isolating_hashes = capture_isolating_hashes(db_path) if db_path is not None else None
    manifest_row_dump_hash = capture_manifest_row_dump_hash(db_path) if db_path is not None else None
    manifest_row_count = (
        manifest_row_dump_hash["row_count"] if manifest_row_dump_hash is not None else None
    )

    return {
        "captured_at": _now_iso(),
        "db_file": db_file,
        "daily_prices": pre_reset_inventory["daily_prices"],
        "data_provider_runs_count": pre_reset_inventory["data_provider_runs_count"],
        "watchlist_count": pre_reset_inventory["watchlist_count"],
        "all_11_incident_dates_zero_scanner_runs": all_11_zero,
        "scanner_runs_total_count": scanner_runs_total_count,
        "scanner_runs_by_identity_group": scanner_runs_by_identity_group,
        "forward_returns_total_count": forward_returns_total_count,
        "forward_returns_measured_into_incident_total": forward_returns_measured_into_incident_total,
        "manifest_row_count": manifest_row_count,
        "manifest_ddl_sha256": manifest_ddl_sha256,
        "manifest_row_dump_fingerprint": manifest_row_dump_hash,
        "isolating_hashes": isolating_hashes,
        "avb_target_rows": avb_target_rows,
    }


def _prefix_suffix_match(full_value: Optional[str], prefix: Optional[str], suffix: Optional[str]) -> bool:
    if not full_value or not prefix or not suffix:
        return False
    return full_value.startswith(prefix) and full_value.endswith(suffix)


def compare_true_envelope_to_coordinator_capture(
    derived: dict, coordinator_capture: dict = COORDINATOR_TRUE_START_CAPTURE
) -> dict:
    """TC-1 through TC-5: per-figure match/mismatch against the coordinator's posted true-start capture.
    ANY mismatch is reported explicitly (never silently reconciled) -- mirrors `j11_stage_d.
    _compare_against_owner_capture`'s idiom exactly (same session, same convention), applied to this
    module's own capture shape."""
    comparisons: dict[str, dict] = {}

    def _exact(name: str, derived_value, key: str) -> None:
        expected = coordinator_capture.get(key)
        comparisons[name] = {
            "derived_value": derived_value, "expected_value": expected,
            "comparison_method": "exact", "matches": derived_value == expected,
        }

    db_file = derived.get("db_file") or {}
    _exact("db_mtime", int(db_file["mtime"]) if db_file.get("exists") and db_file.get("mtime") is not None else None, "db_mtime")
    _exact("db_size_bytes", db_file.get("size_bytes"), "db_size_bytes")
    wal = db_file.get("wal") or {}
    wal_size = wal.get("size_bytes", 0) if wal.get("exists") else 0
    _exact("db_wal_size_bytes", wal_size, "db_wal_size_bytes")
    _exact("daily_prices_row_count", derived["daily_prices"]["row_count"], "daily_prices_row_count")
    _exact("scanner_runs_total_count", derived["scanner_runs_total_count"], "scanner_runs_total_count")
    _exact(
        "scanner_runs_stamped_6261ca17_count",
        derived["scanner_runs_by_identity_group"]["legacy_6261ca17_count"], "scanner_runs_stamped_6261ca17_count",
    )
    _exact("forward_returns_total_count", derived["forward_returns_total_count"], "forward_returns_total_count")
    _exact(
        "forward_returns_measured_into_incident_total",
        derived["forward_returns_measured_into_incident_total"], "forward_returns_measured_into_incident_total",
    )
    _exact("data_provider_runs_count", derived["data_provider_runs_count"], "data_provider_runs_count")
    _exact("manifest_row_count", derived["manifest_row_count"], "manifest_row_count")
    _exact("watchlist_count", derived["watchlist_count"], "watchlist_count")
    _exact(
        "all_11_incident_dates_zero_scanner_runs",
        derived["all_11_incident_dates_zero_scanner_runs"], "all_11_incident_dates_zero_scanner_runs",
    )
    _exact("manifest_ddl_sha256", derived["manifest_ddl_sha256"], "manifest_ddl_sha256")

    for hash_name in ("avb_ohlc_only", "avb_other_dates_full_row", "non_avb_full_row"):
        derived_hash = (derived.get("isolating_hashes") or {}).get(hash_name, {}).get("sha256")
        expected_hash = coordinator_capture.get("isolating_hashes", {}).get(hash_name)
        comparisons[f"isolating_hash.{hash_name}"] = {
            "derived_value": derived_hash, "expected_value": expected_hash,
            "comparison_method": "exact", "matches": derived_hash == expected_hash,
        }

    manifest_dump_hash = (derived.get("manifest_row_dump_fingerprint") or {}).get("sha256")
    comparisons["manifest_row_dump_sha256"] = {
        "derived_value": manifest_dump_hash,
        "expected_prefix": coordinator_capture.get("manifest_row_dump_sha256_prefix"),
        "expected_suffix": coordinator_capture.get("manifest_row_dump_sha256_suffix"),
        "comparison_method": "prefix_suffix_excerpt_not_full_hash",
        "matches": _prefix_suffix_match(
            manifest_dump_hash,
            coordinator_capture.get("manifest_row_dump_sha256_prefix"),
            coordinator_capture.get("manifest_row_dump_sha256_suffix"),
        ),
    }

    for key, expected_row in coordinator_capture.get("avb_target_rows", {}).items():
        derived_row = derived.get("avb_target_rows", {}).get(key, {})
        comparisons[f"avb_target_row.{key}"] = {
            "derived_value": derived_row, "expected_value": expected_row,
            "comparison_method": "exact", "matches": derived_row == expected_row,
        }

    any_mismatch = any(not c["matches"] for c in comparisons.values())
    return {
        "generated_at": _now_iso(),
        "comparisons": comparisons,
        "any_mismatch": any_mismatch,
    }


# ----------------------------------------------------------------------------------------------
# Goal 2 -- derive the correction deterministically; fail closed before any write is contemplated.
# ----------------------------------------------------------------------------------------------


def load_provider_fetch_evidence(path: Path = DEFAULT_PROVIDER_FETCH_EVIDENCE_PATH) -> dict:
    """Iteration 15's already-committed AG-9 dated-exception-#2 fetch evidence -- read-only, no network
    call anywhere in this function or any caller of it."""
    return json.loads(Path(path).read_text())


def derive_avb_volume_correction(
    provider_fetch_evidence: dict,
    j10_evidence_row: dict,
    stored_volume_before: dict[str, float],
    stored_close: dict[str, float],
) -> dict:
    """Goal 2 (TC-7..TC-10): `corrected_volume(date) = round(provider_volume(date) / bridge_factor)` --
    the SAME inverse transform `j11_avb_diagnostic.compute_provider_comparison`'s own
    `expected_inverse_volume_ratio = 1/bridge_factor` already establishes and has proven matches the four
    calibration dates. Rounding rule: nearest whole share (Python's `round()`, applied identically to
    both dates) -- share counts are conventionally whole numbers, and every calibration-window stored
    compensating volume is itself a whole number.

    Cross-verifies BEFORE any write is contemplated: `dollar_volume_ratio_after = (stored_close_unchanged
    * corrected_volume) / (provider_close * provider_volume)` must land within the SAME relative-
    tolerance band (`_RATIO_RELATIVE_TOLERANCE`) the calibration-window compensating check already uses
    around 1.0. **Fails closed** (`verified: False`, per-date `ok: False`) on: `sufficient_evidence` not
    True in the fetch evidence; a missing/None provider volume, provider close, or `bridge_factor`; or a
    cross-check ratio outside tolerance. Never raises for a business-logic failure -- the caller checks
    `verified` and withholds the write itself."""
    bridge_factor = j10_evidence_row.get("bridge_factor")
    per_date_provider = provider_fetch_evidence.get("per_date", {})
    sufficient = bool(provider_fetch_evidence.get("sufficient_evidence", False))

    per_date_results: dict[str, dict] = {}
    all_ok = sufficient and bool(bridge_factor)
    for one_date in TARGET_DATES:
        key = one_date.isoformat()
        provider = per_date_provider.get(key) or {}
        provider_volume = provider.get("volume")
        provider_close = provider.get("close")
        before_volume = stored_volume_before.get(key)
        before_close = stored_close.get(key)

        if not sufficient or not bridge_factor or provider_volume is None or provider_close is None:
            per_date_results[key] = {
                "ok": False,
                "reason": "insufficient_provider_evidence_or_missing_bridge_factor",
                "provider_volume": provider_volume, "provider_close": provider_close,
                "bridge_factor": bridge_factor, "sufficient_evidence": sufficient,
            }
            all_ok = False
            continue

        raw_corrected_volume = provider_volume / bridge_factor
        corrected_volume = float(round(raw_corrected_volume))

        dollar_volume_ratio_after = None
        within_tolerance = False
        if before_close is not None and provider_close:
            dollar_volume_ratio_after = (before_close * corrected_volume) / (provider_close * provider_volume)
            within_tolerance = diag._within_relative_tolerance(
                dollar_volume_ratio_after, 1.0, _RATIO_RELATIVE_TOLERANCE
            )

        per_date_results[key] = {
            "ok": within_tolerance,
            "stored_volume_before": before_volume,
            "stored_close_unchanged": before_close,
            "provider_volume": provider_volume,
            "provider_close": provider_close,
            "bridge_factor": bridge_factor,
            "formula": "corrected_volume = round(provider_volume / bridge_factor)",
            "raw_corrected_volume": raw_corrected_volume,
            "rounding_rule": "nearest_whole_share (python round(), applied identically to both dates)",
            "corrected_volume": corrected_volume,
            "cross_check_formula": (
                "dollar_volume_ratio_after = (stored_close_unchanged * corrected_volume) / "
                "(provider_close * provider_volume)"
            ),
            "dollar_volume_ratio_after": dollar_volume_ratio_after,
            "tolerance": _RATIO_RELATIVE_TOLERANCE,
            "within_tolerance": within_tolerance,
        }
        if not within_tolerance:
            all_ok = False

    return {
        "generated_at": _now_iso(),
        "target_dates": [d.isoformat() for d in TARGET_DATES],
        "per_date": per_date_results,
        "verified": all_ok,
    }


# ----------------------------------------------------------------------------------------------
# Goal 3's write lives in the CLI script (this module stays write-free) -- `apply_avb_volume_correction`
# below is the ONE function that mutates, so it can be unit-tested in isolation against a fixture DB
# while the CLI script itself is exercised only via control-flow (mock) tests, mirroring the
# `j11_stage_c.py` / `run_j11_stage_c_bounded_clear.py` split exactly.
# ----------------------------------------------------------------------------------------------


def checkpoint_wal(engine: Engine) -> dict:
    """Forces a WAL checkpoint (`PRAGMA wal_checkpoint(TRUNCATE)`) immediately after the one authorized
    write. A two-cell, one-column `UPDATE` produces far too little WAL data to cross SQLite's default
    auto-checkpoint page threshold on its own -- without this, the change is fully durable (WAL commits
    are themselves fsynced) but sits ONLY in the `-wal` sidecar, so the main db file's mtime/size never
    move and the sidecar never truncates back to 0, which is exactly the true-end proof TC-18 requires.
    This changes WHERE the already-committed data durably lives, never WHAT is stored -- not a second
    data write. Returns SQLite's own `(busy, log_pages, checkpointed_pages)` triple, recorded honestly:
    `busy != 0` means another connection prevented a full checkpoint (never expected under this script's
    single-controlled-writer discipline, but never silently assumed clean either)."""
    with engine.connect() as conn:
        row = conn.exec_driver_sql("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
        conn.commit()
    busy, log_pages, checkpointed_pages = row
    return {"busy": busy, "log_pages": log_pages, "checkpointed_pages": checkpointed_pages}


def apply_avb_volume_correction(session: Session, corrected_volume_by_date: dict[str, float]) -> dict:
    """THE ONE authorized live write. Fetches EXACTLY the two AVB target rows (`symbol='AVB' AND date IN
    ('2026-08-11','2026-08-12')`), mutates ONLY their `.volume` attribute (grep-verifiable: no other
    attribute is ever assigned in this function), and commits. Raises (refuses to write ANYTHING) if the
    live row count for the target scope is not exactly `len(TARGET_DATES)` -- fail closed rather than
    silently writing fewer/more rows than authorized."""
    rows = session.exec(
        select(DailyPrice).where(DailyPrice.symbol == AVB_SYMBOL).where(DailyPrice.date.in_(TARGET_DATES))
    ).all()
    if len(rows) != len(TARGET_DATES):
        raise RuntimeError(
            f"expected exactly {len(TARGET_DATES)} AVB target rows for {[d.isoformat() for d in TARGET_DATES]}, "
            f"found {len(rows)} -- refusing to write anything"
        )
    written: dict[str, float] = {}
    for row in rows:
        key = row.date.isoformat()
        if key not in corrected_volume_by_date:
            raise RuntimeError(f"no corrected volume supplied for {key} -- refusing to write anything")
        row.volume = corrected_volume_by_date[key]
        session.add(row)
        written[key] = row.volume
    session.commit()
    return written


# ----------------------------------------------------------------------------------------------
# Goal 4 -- the mutation-evidence comparison builder (pure; takes already-captured true-start/true-end
# envelopes + the derivation artifact, never touches the DB itself).
# ----------------------------------------------------------------------------------------------


def build_mutation_evidence(*, true_start: dict, true_end: dict, derivation: dict) -> dict:
    """Goal 4 (TC-13..TC-18): the full true-end proof. Every check must be True for the correction to be
    considered verified; `all_checks_pass=False` means the write executed (it cannot be undone by this
    function -- no transaction spans a whole CLI invocation, same honesty this session's Stage C script
    already applies) but did NOT prove itself safe, and the caller must surface that for owner review."""
    checks: dict[str, bool] = {}

    ohlc_identical = {}
    volume_correct = {}
    for one_date in TARGET_DATES:
        key = one_date.isoformat()
        before = true_start["avb_target_rows"][key]
        after = true_end["avb_target_rows"][key]
        ohlc_identical[key] = (
            before["open"] == after["open"] and before["high"] == after["high"]
            and before["low"] == after["low"] and before["close"] == after["close"]
        )
        expected_volume = derivation["per_date"][key]["corrected_volume"]
        volume_correct[key] = after["volume"] == expected_volume
    checks["ohlc_byte_identical_both_dates"] = all(ohlc_identical.values())
    checks["volume_equals_corrected_both_dates"] = all(volume_correct.values())

    checks["row_count_unchanged"] = true_start["daily_prices"]["row_count"] == true_end["daily_prices"]["row_count"]
    checks["min_date_unchanged"] = true_start["daily_prices"]["min_date"] == true_end["daily_prices"]["min_date"]
    checks["max_date_unchanged"] = true_start["daily_prices"]["max_date"] == true_end["daily_prices"]["max_date"]
    checks["id_sum_unchanged"] = true_start["daily_prices"]["id_sum"] == true_end["daily_prices"]["id_sum"]

    expected_ohlcv_sum_delta = sum(
        true_start["avb_target_rows"][d.isoformat()]["volume"] - derivation["per_date"][d.isoformat()]["corrected_volume"]
        for d in TARGET_DATES
    )
    actual_ohlcv_sum_delta = true_start["daily_prices"]["ohlcv_sum"] - true_end["daily_prices"]["ohlcv_sum"]
    checks["ohlcv_sum_shifted_by_exact_delta"] = abs(actual_ohlcv_sum_delta - expected_ohlcv_sum_delta) < 1e-6

    for hash_name in ("avb_ohlc_only", "avb_other_dates_full_row", "non_avb_full_row"):
        checks[f"isolating_hash_unchanged.{hash_name}"] = (
            true_start["isolating_hashes"][hash_name]["sha256"] == true_end["isolating_hashes"][hash_name]["sha256"]
        )

    checks["scanner_runs_by_identity_group_unchanged"] = (
        true_start["scanner_runs_by_identity_group"] == true_end["scanner_runs_by_identity_group"]
    )
    checks["forward_returns_total_unchanged"] = (
        true_start["forward_returns_total_count"] == true_end["forward_returns_total_count"]
    )
    checks["forward_returns_measured_into_incident_unchanged"] = (
        true_start["forward_returns_measured_into_incident_total"]
        == true_end["forward_returns_measured_into_incident_total"]
    )
    checks["data_provider_runs_count_unchanged"] = (
        true_start["data_provider_runs_count"] == true_end["data_provider_runs_count"]
    )
    checks["manifest_row_count_unchanged"] = true_start["manifest_row_count"] == true_end["manifest_row_count"]
    checks["manifest_ddl_sha256_unchanged"] = true_start["manifest_ddl_sha256"] == true_end["manifest_ddl_sha256"]
    checks["manifest_row_dump_fingerprint_unchanged"] = (
        true_start["manifest_row_dump_fingerprint"]["sha256"] == true_end["manifest_row_dump_fingerprint"]["sha256"]
    )
    checks["watchlist_count_unchanged"] = true_start["watchlist_count"] == true_end["watchlist_count"]
    checks["all_11_incident_dates_zero_scanner_runs_unchanged"] = (
        true_start["all_11_incident_dates_zero_scanner_runs"] == true_end["all_11_incident_dates_zero_scanner_runs"] is True
    ) or (
        true_start["all_11_incident_dates_zero_scanner_runs"] and true_end["all_11_incident_dates_zero_scanner_runs"]
    )

    start_db_file = true_start.get("db_file") or {}
    end_db_file = true_end.get("db_file") or {}
    checks["db_file_moved"] = (
        end_db_file.get("mtime") != start_db_file.get("mtime")
        or end_db_file.get("size_bytes") != start_db_file.get("size_bytes")
    )
    end_wal = end_db_file.get("wal") or {}
    checks["wal_checkpointed_to_zero"] = (not end_wal.get("exists")) or end_wal.get("size_bytes", 0) == 0

    all_checks_pass = all(bool(v) for v in checks.values())
    return {
        "generated_at": _now_iso(),
        "checks": checks,
        "expected_ohlcv_sum_delta": expected_ohlcv_sum_delta,
        "actual_ohlcv_sum_delta": actual_ohlcv_sum_delta,
        "all_checks_pass": all_checks_pass,
    }
