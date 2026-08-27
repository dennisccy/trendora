"""goal-market-compass iter-23 -- J-11's one remaining acceptance objective: build a disposable,
byte-faithful clone of the repaired canonical database plus a verification-only config, so real
backend/frontend/browser verification can run WITHOUT ever booting against
`apps/backend/data/trendora.db` itself (docs/goal.md "OWNER RULING -- J-11 database recovery accepted;
one final serving verification remains", owner 2026-08-27, items 3-4).

Sequence (every step's evidence is persisted before the next runs):
  1. Capture the canonical database's provenance (row counts + max provider-run id + whole-file sha256)
     BEFORE touching anything.
  2. Create the disposable clone via the SQLite online backup API (source opened `mode=ro` -- this
     script can never write to the canonical file).
  3. Re-capture the canonical database's provenance and assert it is byte-unchanged from step 1 (the
     ruling's "canonical database remains OFF and must not be mutated by this verification").
  4. Capture the clone's provenance and assert its row counts / max id match step 1's canonical values
     (TC-1).
  5. Build the verification-only config -- a copy of the committed `config.yaml` whose ONLY changed line
     is `database.url`, pointed at the clone -- and self-check it with the SAME launch-safety guard the
     boot wrapper (`scripts/start-backend-j11-verify.sh`) uses, including a demonstration that omitting
     the override is correctly refused.

Usage:
    apps/backend/.venv/bin/python apps/backend/scripts/run_j11_disposable_clone.py \\
        --confirm \\
        --dest-dir runs/goal-market-compass-iter-23/verify-clone \\
        --evidence-dir runs/goal-market-compass-iter-23

Without `--confirm`, the script performs NO filesystem interaction at all and exits non-zero (mirrors
every other J-11 evidence-writing script's idiom).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Optional

# scripts/ -> backend -> apps -> repo root
BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.config import get_config  # noqa: E402
from app.db import resolve_database_url  # noqa: E402
from app.engine import j11_disposable_clone as jdc  # noqa: E402


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str))
    print(f"wrote {path}", file=sys.stderr)


def _db_path_from_url(database_url: str) -> Path:
    resolved_url = resolve_database_url(database_url)
    prefix = "sqlite:///"
    if not resolved_url.startswith(prefix):
        raise SystemExit(f"refusing to run: database.url is not a sqlite file URL: {database_url!r}")
    return Path(resolved_url[len(prefix):])


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--confirm", action="store_true",
        help="required -- without it, NO filesystem interaction of any kind happens",
    )
    parser.add_argument(
        "--dest-dir", type=Path, required=True,
        help="directory to create the disposable clone DB + verification config in (must not already "
        "contain trendora-clone.db)",
    )
    parser.add_argument(
        "--evidence-dir", type=Path, required=True,
        help="directory to write provenance/evidence JSON into (no implicit default)",
    )
    args = parser.parse_args(argv)

    if not args.confirm:
        print("refusing to run without --confirm -- no filesystem interaction performed", file=sys.stderr)
        return 1

    started_at = time.time()
    cfg = get_config()
    canonical_url = cfg.database.url
    canonical_path = _db_path_from_url(canonical_url)
    evidence_dir = args.evidence_dir
    dest_dir = args.dest_dir
    dest_dir.mkdir(parents=True, exist_ok=True)
    clone_db_path = dest_dir / "trendora-clone.db"
    verify_config_path = dest_dir / "config.verify.yaml"

    print(f"canonical database: {canonical_path}", file=sys.stderr)

    # Step 1 -- canonical provenance BEFORE anything.
    before = jdc.capture_db_provenance(canonical_path)
    _write_json(evidence_dir / "j11-disposable-clone-canonical-before.json", before)

    # Step 2 -- create the clone.
    clone_result = jdc.create_disposable_clone(canonical_path, clone_db_path)
    _write_json(evidence_dir / "j11-disposable-clone-clone-result.json", clone_result)

    # Step 3 -- canonical provenance AFTER clone creation; must be byte-unchanged.
    after_clone = jdc.capture_db_provenance(canonical_path)
    _write_json(evidence_dir / "j11-disposable-clone-canonical-after-clone.json", after_clone)
    canonical_unchanged = jdc.compare_provenance(before, after_clone)
    _write_json(evidence_dir / "j11-disposable-clone-canonical-unchanged-check.json", canonical_unchanged)
    if not canonical_unchanged["equal"]:
        print(
            f"FATAL: canonical database changed during clone creation -- mismatched fields: "
            f"{canonical_unchanged['mismatched_fields']}. This must never happen; STOP and report.",
            file=sys.stderr,
        )
        return 1

    # Step 4 -- clone provenance; row counts/max id must match the canonical values at clone time (TC-1).
    clone_provenance = jdc.capture_db_provenance(clone_db_path, include_sha256=False)
    _write_json(evidence_dir / "j11-disposable-clone-clone-provenance.json", clone_provenance)
    clone_matches = (
        clone_provenance["daily_prices_count"] == before["daily_prices_count"]
        and clone_provenance["next_session_manifests_count"] == before["next_session_manifests_count"]
        and clone_provenance["data_provider_runs_max_id"] == before["data_provider_runs_max_id"]
    )
    if not clone_matches:
        print(
            "FATAL: clone provenance does not match the canonical database's provenance at clone time "
            "-- TC-1 fails. STOP and report.",
            file=sys.stderr,
        )
        return 1

    # Step 5 -- build + self-check the verification-only config.
    committed_config_text = (REPO_ROOT / "config.yaml").read_text()
    clone_url = jdc.clone_sqlite_url(clone_db_path)
    verify_config_text = jdc.build_verification_config_text(committed_config_text, canonical_url, clone_url)
    verify_config_path.write_text(verify_config_text)
    print(f"wrote {verify_config_path}", file=sys.stderr)

    launch_check_pass = jdc.assert_launch_targets_clone(str(verify_config_path), canonical_url)
    try:
        jdc.assert_launch_targets_clone(None, canonical_url)
        launch_check_refusal_proof = {"raised": False}
    except jdc.ClonePreconditionError as exc:
        launch_check_refusal_proof = {"raised": True, "message": str(exc)}

    summary = {
        "started_at": started_at,
        "finished_at": time.time(),
        "canonical_db_path": str(canonical_path),
        "canonical_url": canonical_url,
        "clone_db_path": str(clone_db_path),
        "clone_url": clone_url,
        "verify_config_path": str(verify_config_path),
        "canonical_provenance_before": before,
        "canonical_provenance_after_clone": after_clone,
        "canonical_unchanged": canonical_unchanged,
        "clone_provenance": clone_provenance,
        "tc1_clone_matches_canonical": clone_matches,
        "launch_guard_passes_for_verify_config": launch_check_pass,
        "launch_guard_refuses_when_unset": launch_check_refusal_proof,
        "next_steps": {
            "export_env": {
                "TRENDORA_CONFIG": str(verify_config_path),
                "TRENDORA_COMPASS_EXPORT_DIR": str(dest_dir / "exports" / "next_session_manifests"),
            },
            "boot_backend": "bash scripts/start-backend-j11-verify.sh",
            "boot_frontend": "bash scripts/start-frontend.sh",
            "warning": (
                "NEVER call GET /api/compass?as_of=<one of the 7 manifest-less incident dates "
                "2026-05-12/05-13/07-10/07-13/07-24/07-27/08-03> -- this mints a historical manifest "
                "and is a hard verification FAIL. Verify those dates only via GET /runs or GET "
                "/runs/{run_id}."
            ),
        },
    }
    _write_json(evidence_dir / "j11-disposable-clone-summary.json", summary)
    print("disposable clone + verification config created successfully.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
