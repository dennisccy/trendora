"""goal-market-compass iter-10 -- J-11 Stage B/B2 read-only pre-reset inventory + frozen-identity CLI.

Wraps `app.engine.j11_maintenance.capture_pre_reset_inventory` (Stage B) and `freeze_attempt_identity`
(Stage B2) against the LIVE production database, via the SAME `app.db` session helpers the real backend
uses (`get_engine()` -- never a raw file copy, never `create_db_and_tables()`/`metadata.create_all()`,
which would run additive-ALTER/index-hygiene sweeps this script has no business triggering). Every
statement this script issues is a plain SELECT/aggregate read; it inserts, updates, and deletes nothing.

This is the ONE authorized live-database interaction for goal-market-compass iter-10 (J-11 Stages B/B1/B2
only -- the destructive clear/regenerate, Stages C-G, stays out of scope for a later iteration;
`docs/phases/goal-market-compass-iter-10.md`). Maintenance isolation is active for this iteration: no
backend/frontend boot, no browser QA, no replay lane -- this script is the sanctioned live-DB check.

Self-proving zero-write check (TC-1/TC-2): the `daily_prices` count/date-range/fingerprint the capture
step itself computes is re-derived a SECOND time, independently, via `_daily_prices_spot_check` (the
identical aggregate query, run again over the pooled connection) -- and the file's own mtime is compared
before/after. All three must match for the script to report success; the full comparison, plus the file
mtime themselves, is written into the inventory artifact as `zero_write_proof` so the proof travels with
the evidence rather than living only in this run's stdout.

Usage:
    apps/backend/.venv/bin/python apps/backend/scripts/run_j11_pre_reset_inventory.py \\
        [--inventory-path runs/goal-market-compass-iter-10/j11-pre-reset-inventory.json] \\
        [--identity-path runs/goal-market-compass-iter-10/j11-frozen-identity.json]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

# scripts/ -> backend -> apps -> repo root
BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import func  # noqa: E402
from sqlmodel import Session, select  # noqa: E402

from app.config import load_config  # noqa: E402
from app.db import get_engine, resolve_database_url  # noqa: E402
from app.engine.j11_maintenance import capture_pre_reset_inventory, freeze_attempt_identity  # noqa: E402
from app.models import DailyPrice  # noqa: E402

DEFAULT_INVENTORY_PATH = REPO_ROOT / "runs" / "goal-market-compass-iter-10" / "j11-pre-reset-inventory.json"
DEFAULT_IDENTITY_PATH = REPO_ROOT / "runs" / "goal-market-compass-iter-10" / "j11-frozen-identity.json"


def _db_file_path(database_url: str) -> "Path | None":
    """The on-disk path a `sqlite:///...` URL resolves to, or `None` for a non-sqlite / in-memory URL
    (no mtime to check in that case)."""
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        return None
    raw = database_url[len(prefix):]
    if not raw or raw == ":memory:":
        return None
    return Path(raw)


def _daily_prices_spot_check(session: Session) -> dict:
    """An INDEPENDENT re-query of the SAME daily_prices count/date-range/fingerprint the inventory
    capture itself computed -- run a second time, over a second statement, purely to PROVE the capture
    step wrote nothing (TC-2). Mirrors `capture_pre_reset_inventory`'s own price aggregate query exactly
    (never a second formula -- both read `DailyPrice.id`/`.date`/OHLCV the identical way)."""
    row = session.exec(
        select(
            func.count(DailyPrice.id),
            func.min(DailyPrice.date),
            func.max(DailyPrice.date),
            func.sum(DailyPrice.id),
            func.sum(DailyPrice.open + DailyPrice.high + DailyPrice.low + DailyPrice.close + DailyPrice.volume),
        )
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--inventory-path", type=Path, default=DEFAULT_INVENTORY_PATH)
    parser.add_argument("--identity-path", type=Path, default=DEFAULT_IDENTITY_PATH)
    args = parser.parse_args()

    cfg = load_config()
    resolved_url = resolve_database_url(cfg.database.url)
    print(f"database (read-only queries only, never written): {resolved_url}", file=sys.stderr)

    db_file = _db_file_path(resolved_url)
    mtime_before = db_file.stat().st_mtime if db_file is not None and db_file.exists() else None

    engine = get_engine()  # existing app.db session helper -- resolves the SAME committed config.yaml
    # database.url the real backend boots against. Deliberately NOT create_db_and_tables()/
    # metadata.create_all() (those run additive-ALTER + index-hygiene sweeps) and NEVER a raw file copy.

    with Session(engine) as session:
        inventory = capture_pre_reset_inventory(session)
        identity = freeze_attempt_identity(session, cfg)
        spot_check = _daily_prices_spot_check(session)

    mtime_after = db_file.stat().st_mtime if db_file is not None and db_file.exists() else None

    captured_prices = inventory["daily_prices"]
    zero_write_proof = {
        "capture_daily_prices": captured_prices,
        "independent_spot_check": spot_check,
        "counts_match": (
            captured_prices["row_count"] == spot_check["row_count"]
            and captured_prices["min_date"] == spot_check["min_date"]
            and captured_prices["max_date"] == spot_check["max_date"]
        ),
        "fingerprints_match": captured_prices["fingerprint"] == spot_check["fingerprint"],
        "db_file": str(db_file) if db_file is not None else None,
        "mtime_before": mtime_before,
        "mtime_after": mtime_after,
        "mtime_unchanged": mtime_before == mtime_after,
    }
    inventory["zero_write_proof"] = zero_write_proof

    proved_zero_write = (
        zero_write_proof["counts_match"]
        and zero_write_proof["fingerprints_match"]
        and zero_write_proof["mtime_unchanged"]
    )

    args.inventory_path.parent.mkdir(parents=True, exist_ok=True)
    args.inventory_path.write_text(json.dumps(inventory, indent=2, sort_keys=True, default=str))
    print(f"wrote {args.inventory_path}", file=sys.stderr)

    if not proved_zero_write:
        print("FAIL: the capture step did not prove zero writes -- see zero_write_proof in the "
              "written inventory artifact. Refusing to write the identity artifact.", file=sys.stderr)
        return 1

    args.identity_path.parent.mkdir(parents=True, exist_ok=True)
    args.identity_path.write_text(json.dumps(identity, indent=2, sort_keys=True, default=str))
    print(f"wrote {args.identity_path}", file=sys.stderr)

    print(f"engine_identity={identity['engine_identity']}", file=sys.stderr)
    print(
        f"zero_write_proof: mtime_unchanged={zero_write_proof['mtime_unchanged']} "
        f"counts_match={zero_write_proof['counts_match']} "
        f"fingerprints_match={zero_write_proof['fingerprints_match']}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
