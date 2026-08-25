"""goal-market-compass iter-15 -- J-11 Stage D readiness, Goal 7: the CLI wrapper for the committed
readiness-artifact producer (`app.engine.j11_stage_d.produce_stage_d_readiness_artifact`).

This is the FIRST committed, non-test caller of `stage_d_readiness_verdict` -- through iteration 14 that
function was called only from `tests/test_j11_stage_d.py`, which is exactly why iteration 14's
`j11-stage-d-readiness.json` went stale relative to its own evaluator's corrected conclusion. This script
reads TWO already-persisted evidence artifacts (the Stage D preflight gate, from a Goal-6-fixed run of
`run_j11_stage_d_preflight.py`; the AVB bridge diagnostic, from a Goal-6-fixed run of
`run_j11_avb_bridge_diagnostic.py`) and combines them into the final, single, machine-readable readiness
verdict -- performing NO database or network access itself (it only reads two JSON files and writes one).

Every path is required, no default (Goal 6's guard, applied to this new script from the start): all three
paths point at evidence this iteration produces, and an omitted flag must fail loudly rather than
silently reading/writing the wrong location.

Prints the literal `J-11 STAGE D READY: YES` / `NO` line -- read verbatim from the artifact's own `ready`
field, never re-typed independently (TC-40) -- and the unconditional `J-11 STAGE D AUTHORIZED: NO` line
(Stage D readiness is never self-authorizing; the C10/A12 pattern).

Usage:
    apps/backend/.venv/bin/python apps/backend/scripts/run_j11_stage_d_readiness.py \\
        --preflight-gate-path runs/goal-market-compass-iter-15/j11-stage-d-preflight-gate.json \\
        --avb-diagnostic-path runs/goal-market-compass-iter-15/j11-avb-bridge-diagnostic.json \\
        --output-path runs/goal-market-compass-iter-15/j11-stage-d-readiness.json
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# scripts/ -> backend -> apps -> repo root
BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.engine import j11_stage_d as jsd  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--preflight-gate-path", type=Path, default=None,
        help="required -- the Stage D preflight-gate JSON (e.g. j11-stage-d-preflight-gate.json).",
    )
    parser.add_argument(
        "--avb-diagnostic-path", type=Path, default=None,
        help="required -- the AVB bridge-diagnostic JSON (e.g. j11-avb-bridge-diagnostic.json).",
    )
    parser.add_argument(
        "--output-path", type=Path, default=None,
        help=(
            "required -- the final readiness JSON this script writes. Has NO default on purpose (Goal "
            "6's guard, applied to this new script from the start): an omitted flag must fail loudly "
            "rather than silently landing this iteration's headline verdict somewhere unintended."
        ),
    )
    args = parser.parse_args()

    missing = [
        name for name, value in (
            ("--preflight-gate-path", args.preflight_gate_path),
            ("--avb-diagnostic-path", args.avb_diagnostic_path),
            ("--output-path", args.output_path),
        )
        if value is None
    ]
    if missing:
        print(
            f"refusing to run without explicit {', '.join(missing)}. This script combines two committed "
            "evidence artifacts into the final J-11 Stage D readiness verdict -- none of its paths "
            "default into a committed evidence directory. No file has been read or written.",
            file=sys.stderr,
        )
        return 2

    try:
        readiness = jsd.produce_stage_d_readiness_artifact(
            args.preflight_gate_path, args.avb_diagnostic_path, output_path=args.output_path,
        )
    except ValueError as exc:
        print(f"FAIL (fail-closed, nothing written): {exc}", file=sys.stderr)
        return 1

    print(f"wrote {args.output_path}", file=sys.stderr)
    print(
        f"avb_classification={readiness['avb_classification']} "
        f"preflight_gate_passed={readiness['preflight_gate_passed']} "
        f"blocking_reasons={readiness['blocking_reasons']}",
        file=sys.stderr,
    )
    print(f"J-11 STAGE D READY: {'YES' if readiness['ready'] else 'NO'}", file=sys.stderr)
    print("J-11 STAGE D AUTHORIZED: NO", file=sys.stderr)
    return 0 if readiness["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
