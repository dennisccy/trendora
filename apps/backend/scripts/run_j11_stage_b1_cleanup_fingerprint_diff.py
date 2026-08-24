"""goal-market-compass iter-12 -- J-11 Stage B1 CLEANUP: diff two fingerprint artifacts produced by
`run_j11_stage_b1_cleanup_fingerprint.py` (TC-22: "given a read-only fingerprint... taken at the start of
this iteration's work and an identical fingerprint taken at the end, when the two are diffed, then every
one of them is identical").

Excludes ONLY the fields that legitimately differ between two capture RUNS of the same unchanged
database -- the capture act's own timestamps -- never database CONTENT. Everything else (every table's
row count, the db file mtime/size, the manifest table's full DDL/index text, every manifest row's every
column value, the `daily_prices` row-count + content fingerprint, and the `data_provider_runs`/
`watchlist` counts) must be byte-identical or this script reports a non-empty diff and exits non-zero.

Usage:
    apps/backend/.venv/bin/python apps/backend/scripts/run_j11_stage_b1_cleanup_fingerprint_diff.py \\
        --before runs/goal-market-compass-iter-12/j11-stage-b1-cleanup-fingerprint-before.json \\
        --after runs/goal-market-compass-iter-12/j11-stage-b1-cleanup-fingerprint-after.json \\
        --output-path runs/goal-market-compass-iter-12/j11-stage-b1-cleanup-fingerprint-diff.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Fields that legitimately differ between two capture RUNS of the SAME unchanged database (the wall-clock
# instant each capture ran at) -- never database content. Listed explicitly and matched by exact
# dotted-path so nothing else is silently ignored.
_IGNORED_PATHS = {
    "captured_at",
    "pre_reset_inventory.captured_at",
    "db_file_mtime_before_capture",
    "db_file_mtime_after_capture",
}


def _diff(a: dict, b: dict, path: str = "") -> list[dict]:
    diffs: list[dict] = []
    for key in sorted(set(a) | set(b)):
        p = f"{path}.{key}" if path else key
        av, bv = a.get(key), b.get(key)
        if isinstance(av, dict) and isinstance(bv, dict):
            diffs.extend(_diff(av, bv, p))
        elif av != bv:
            diffs.append({"path": p, "before": av, "after": bv})
    return diffs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--after", type=Path, required=True)
    parser.add_argument("--output-path", type=Path, required=True)
    args = parser.parse_args()

    before = json.loads(args.before.read_text())
    after = json.loads(args.after.read_text())

    diffs = [d for d in _diff(before, after) if d["path"] not in _IGNORED_PATHS]
    result = {
        "diffs": diffs,
        "identical_except_capture_timestamps": len(diffs) == 0,
        "ignored_paths": sorted(_IGNORED_PATHS),
        "before_captured_at": before.get("captured_at"),
        "after_captured_at": after.get("captured_at"),
        "before_path": str(args.before),
        "after_path": str(args.after),
    }

    args.output_path.parent.mkdir(parents=True, exist_ok=True)
    args.output_path.write_text(json.dumps(result, indent=2, sort_keys=True, default=str))
    print(f"wrote {args.output_path}", file=sys.stderr)
    print(f"identical_except_capture_timestamps={result['identical_except_capture_timestamps']}", file=sys.stderr)
    if diffs:
        print("DIFFS FOUND:", file=sys.stderr)
        for d in diffs:
            print(f"  {d['path']}: before={d['before']!r} after={d['after']!r}", file=sys.stderr)
    return 0 if result["identical_except_capture_timestamps"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
