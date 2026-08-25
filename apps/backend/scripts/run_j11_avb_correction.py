"""goal-market-compass iter-16 -- J-11 "OWNER RULING -- AVB two-row raw-volume correction before Stage D"
(docs/goal.md, owner 2026-08-25): the ONE authorized live write this iteration.

Mirrors `run_j11_stage_c_bounded_clear.py`'s established idiom exactly: NO database interaction of any
kind, not even a read, without `--confirm`; evidence is persisted at every checkpoint; the write itself
executes ONLY after Goal 2's derivation verifies (fail-closed otherwise -- nothing written, nothing
guessed). Sequence: TRUE-start envelope capture (Goal 1) -> comparison against the coordinator's
independently-posted true-start figures (STOP on any mismatch) -> load already-committed iteration-15
provider-fetch evidence + the persisted J-10 `bridge_factor` (NO new network fetch anywhere in this
process -- AG-9 dated exception #2 stays exhausted) -> derive the correction (Goal 2, persisted BEFORE
any write is contemplated) -> fail closed if the derivation does not verify -> THE ONE authorized
`daily_prices.volume` write, scoped to exactly `symbol='AVB' AND date IN ('2026-08-11','2026-08-12')`
(Goal 3) -> TRUE-end envelope capture + full mutation-evidence proof (Goal 4).

`--evidence-dir` (the true-start/derivation/true-end evidence trail) and `--output-path` (the final
consolidated mutation-evidence artifact) are BOTH required, with NO default -- applying the guard from
the start (iter-13/14's own lesson: an omitted `--evidence-dir` once silently overwrote committed Stage C
forensic evidence; see `docs/handoffs/goal-market-compass-iter-14-dev.md`).

Usage:
    apps/backend/.venv/bin/python apps/backend/scripts/run_j11_avb_correction.py \\
        --confirm \\
        --evidence-dir runs/goal-market-compass-iter-16 \\
        --output-path runs/goal-market-compass-iter-16/j11-avb-correction-mutation-evidence.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# scripts/ -> backend -> apps -> repo root
BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from sqlmodel import Session  # noqa: E402

from app.config import load_config  # noqa: E402
from app.db import get_engine, resolve_database_url  # noqa: E402
from app.engine import j11_avb_correction as corr  # noqa: E402
from app.engine import j11_avb_diagnostic as diag  # noqa: E402

CANONICAL_EVIDENCE_DIR = REPO_ROOT / "runs" / "goal-market-compass-iter-16"


def _db_file_path(database_url: str) -> "Path | None":
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        return None
    raw = database_url[len(prefix):]
    if not raw or raw == ":memory:":
        return None
    path = Path(raw)
    return path if path.is_absolute() else (REPO_ROOT / raw)


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str))
    print(f"wrote {path}", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--evidence-dir", type=Path, default=None,
        help=(
            "required -- the directory the true-start/derivation/true-end evidence JSON files are "
            f"written to. No default on purpose: the real target ({CANONICAL_EVIDENCE_DIR}) is a "
            "committed evidence directory, and an implicit default has previously let a forgotten flag "
            "silently overwrite committed forensic evidence instead of failing."
        ),
    )
    parser.add_argument(
        "--output-path", type=Path, default=None,
        help=(
            "required -- the final consolidated mutation-evidence JSON this script writes (e.g. "
            "j11-avb-correction-mutation-evidence.json). No default on purpose -- same reasoning as "
            "--evidence-dir."
        ),
    )
    parser.add_argument(
        "--provider-fetch-evidence-path", type=Path, default=corr.DEFAULT_PROVIDER_FETCH_EVIDENCE_PATH,
        help="the already-committed iteration-15 AG-9 dated-exception-#2 fetch evidence -- read-only "
             "input; this script performs NO network fetch of its own.",
    )
    parser.add_argument(
        "--j10-evidence-path", type=Path, default=diag.DEFAULT_J10_EVIDENCE_PATH,
        help="the persisted J-10 population-recovery evidence file (for the bridge factor) -- read-only "
             "input, never re-fetched.",
    )
    parser.add_argument(
        "--confirm", action="store_true",
        help="required -- without it, the script touches the database not at all and exits non-zero.",
    )
    args = parser.parse_args()

    if not args.confirm:
        print(
            "refusing to run without --confirm (this is the ONE owner-authorized bounded destructive "
            "write this iteration -- docs/goal.md J-11 step 11, 'OWNER RULING -- AVB two-row raw-volume "
            "correction before Stage D'). No database interaction, not even a read, has occurred.",
            file=sys.stderr,
        )
        return 2

    missing = [name for name, value in (("--evidence-dir", args.evidence_dir), ("--output-path", args.output_path)) if value is None]
    if missing:
        print(
            f"refusing to run without explicit {', '.join(missing)}. Their real targets under "
            f"{CANONICAL_EVIDENCE_DIR} are committed evidence paths, so they must be named explicitly and "
            "can never be reached by default. No database interaction, not even a read, has occurred, and "
            "nothing has been written.",
            file=sys.stderr,
        )
        return 2

    evidence_dir: Path = args.evidence_dir
    output_path: Path = args.output_path

    cfg = load_config()
    resolved_url = resolve_database_url(cfg.database.url)
    db_path = _db_file_path(resolved_url)
    print(f"database: {resolved_url}", file=sys.stderr)

    engine = get_engine()  # the SAME pooled writable engine the real backend uses -- never a raw file copy.

    # --- Goal 1: TRUE-start envelope, before anything else touches the database -----------------------
    with Session(engine) as session:
        true_start = corr.capture_true_envelope(session, engine, db_path)
    _write_json(evidence_dir / "j11-avb-correction-true-start.json", true_start)
    print(
        f"true-start captured: daily_prices.row_count={true_start['daily_prices']['row_count']} "
        f"db_file={true_start['db_file']}",
        file=sys.stderr,
    )

    comparison = corr.compare_true_envelope_to_coordinator_capture(true_start)
    _write_json(evidence_dir / "j11-avb-correction-true-start-comparison.json", comparison)
    if comparison["any_mismatch"]:
        mismatched = [name for name, c in comparison["comparisons"].items() if not c["matches"]]
        print(
            f"STOP: the true-start envelope does NOT match the coordinator's posted true-start capture "
            f"(mismatched fields: {mismatched}). No write has been attempted. See "
            "j11-avb-correction-true-start-comparison.json for the full per-figure comparison.",
            file=sys.stderr,
        )
        return 1
    print("true-start envelope matches the coordinator's posted capture exactly (zero mismatches).", file=sys.stderr)

    # --- Goal 2: derive the correction deterministically, BEFORE the write is contemplated -------------
    provider_fetch_evidence = corr.load_provider_fetch_evidence(args.provider_fetch_evidence_path)
    j10_evidence_row = diag.load_j10_avb_evidence(args.j10_evidence_path)
    stored_volume_before = {k: v["volume"] for k, v in true_start["avb_target_rows"].items()}
    stored_close = {k: v["close"] for k, v in true_start["avb_target_rows"].items()}
    derivation = corr.derive_avb_volume_correction(
        provider_fetch_evidence, j10_evidence_row, stored_volume_before, stored_close
    )
    _write_json(evidence_dir / "j11-avb-correction-derivation.json", derivation)
    print(f"derivation verified={derivation['verified']}", file=sys.stderr)

    if not derivation["verified"]:
        print(
            "FAIL (fail-closed): the AVB volume correction could not be derived/verified from the "
            "committed evidence. NO write has been attempted -- nothing in daily_prices has changed. "
            "This needs OWNER REVIEW rather than a guess. See j11-avb-correction-derivation.json for the "
            "per-date failure detail.",
            file=sys.stderr,
        )
        return 1

    corrected_volume_by_date = {
        key: row["corrected_volume"] for key, row in derivation["per_date"].items()
    }

    # --- Goal 3: THE ONE AUTHORIZED WRITE ---------------------------------------------------------------
    with Session(engine) as session:
        written = corr.apply_avb_volume_correction(session, corrected_volume_by_date)
    print(f"WROTE corrected volumes: {written}", file=sys.stderr)

    # Force the change durably into the MAIN db file (never a second data write -- see checkpoint_wal's
    # own docstring): a two-cell update is far too small to cross SQLite's default auto-checkpoint
    # threshold on its own, and the true-end proof below requires the main file to have moved and the
    # `-wal` sidecar to be back at 0 bytes.
    checkpoint_result = corr.checkpoint_wal(engine)
    print(f"WAL checkpoint (TRUNCATE): {checkpoint_result}", file=sys.stderr)

    # --- Goal 4: TRUE-end envelope + mutation-evidence proof --------------------------------------------
    with Session(engine) as session:
        true_end = corr.capture_true_envelope(session, engine, db_path)
    _write_json(evidence_dir / "j11-avb-correction-true-end.json", true_end)

    mutation_evidence = corr.build_mutation_evidence(true_start=true_start, true_end=true_end, derivation=derivation)
    mutation_evidence["written"] = written
    mutation_evidence["wal_checkpoint"] = checkpoint_result
    mutation_evidence["true_start_comparison_against_coordinator_capture"] = comparison
    _write_json(output_path, mutation_evidence)

    print(f"mutation evidence: all_checks_pass={mutation_evidence['all_checks_pass']}", file=sys.stderr)
    if not mutation_evidence["all_checks_pass"]:
        failing = [k for k, v in mutation_evidence["checks"].items() if not v]
        print(
            f"FAILING CHECKS: {failing}. The write already executed and cannot be undone by this script "
            "(no transaction spans the whole invocation). All captured evidence is preserved for owner "
            "review.",
            file=sys.stderr,
        )
        return 1

    print("J-11 AVB CORRECTION COMPLETE: YES", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
