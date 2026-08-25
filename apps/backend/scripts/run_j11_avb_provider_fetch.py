"""goal-market-compass iter-15 -- J-11 Stage D readiness, Goal 2: the CLI wrapper for the ONE
owner-authorized bounded AVB comparison fetch (`docs/goal.md` AG-9 "Dated exception #2 -- AVB convention
diagnostic (owner, 2026-08-25 -- single-use, self-closing, DIAGNOSTIC ONLY)").

This script constructs the REAL `app.data_providers.yahoo_provider.YahooProvider` and is the ONLY place
in this iteration's diff that does so -- `app.engine.j11_avb_provider_fetch.fetch_avb_provider_evidence`
takes it as an injected dependency and calls `.get_daily` exactly once. This script needs NO database
engine or session at all -- it imports nothing from `app.db`/`app.config.load_config`/`sqlmodel`, so it is
structurally incapable of touching `apps/backend/data/trendora.db` (verified: zero references to
`get_engine`/`Session`/`load_config` anywhere in this file). Its only inputs are the persisted J-10
evidence file (for the bridge factor -- never re-derived, never re-fetched; AG-9's ORIGINAL J-10 exception
stays exhausted, this is a SEPARATE dated exception) and the network; its only output is the evidence JSON
this script writes to the required `--output-path`.

`--output-path` carries NO default, mirroring `run_j11_stage_c_bounded_clear.py`'s already-fixed pattern
(Goal 6): a forgotten flag must fail loudly rather than silently landing evidence in an unintended, or
worse a real committed, location. Refuses BEFORE constructing the provider or reading the J-10 evidence
file -- no network call and no file I/O beyond argument parsing occurs when the required path is missing.

Usage:
    apps/backend/.venv/bin/python apps/backend/scripts/run_j11_avb_provider_fetch.py \\
        --output-path runs/goal-market-compass-iter-15/j11-avb-provider-fetch-evidence.json \\
        [--j10-evidence-path runs/goal-market-compass-iter-9/j10-population-evidence.json]

This is the SINGLE execution of AG-9 dated exception #2 -- once the artifact is written, the exception is
exhausted for the rest of this iteration; every later step (the AVB bridge diagnostic, the readiness
producer) reads the persisted artifact this script writes, never re-fetches.
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

from app.data_providers.yahoo_provider import YahooProvider  # noqa: E402
from app.engine import j11_avb_provider_fetch as fetch  # noqa: E402
from app.engine.j11_avb_diagnostic import DEFAULT_J10_EVIDENCE_PATH, load_j10_avb_evidence  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--output-path", type=Path, default=None,
        help=(
            "required -- the evidence JSON this script writes. Has NO default on purpose (Goal 6's "
            "guard, applied to this new script from the start): an omitted flag must fail loudly rather "
            "than silently writing this iteration's ONE authorized network fetch's evidence somewhere "
            "unintended."
        ),
    )
    parser.add_argument(
        "--j10-evidence-path", type=Path, default=DEFAULT_J10_EVIDENCE_PATH,
        help="the persisted J-10 population-recovery evidence file (for the bridge factor) -- read-only "
             "input, never re-derived, never re-fetched.",
    )
    args = parser.parse_args()

    if args.output_path is None:
        print(
            "refusing to run without an explicit --output-path. This script performs this iteration's "
            "ONE owner-authorized network fetch (docs/goal.md AG-9 'Dated exception #2') -- its evidence "
            "must land at an explicitly named location, never a default. No network call has occurred, "
            "and nothing has been written.",
            file=sys.stderr,
        )
        return 2

    evidence_row = load_j10_avb_evidence(args.j10_evidence_path)
    bridge_factor = evidence_row["bridge_factor"]
    print(f"loaded persisted J-10 bridge_factor={bridge_factor} from {args.j10_evidence_path}", file=sys.stderr)

    provider = YahooProvider()
    print(
        f"performing the ONE authorized AG-9 dated-exception-#2 fetch: symbol={fetch.AVB_SYMBOL} "
        f"dates={[d.isoformat() for d in fetch.PERMITTED_DATES]} provider=yahoo",
        file=sys.stderr,
    )
    result = fetch.fetch_avb_provider_evidence(provider, bridge_factor=bridge_factor)

    args.output_path.parent.mkdir(parents=True, exist_ok=True)
    args.output_path.write_text(json.dumps(result, indent=2, sort_keys=True, default=str))
    print(f"wrote {args.output_path}", file=sys.stderr)
    print(
        f"sufficient_evidence={result['sufficient_evidence']} missing_dates={result['missing_dates']}",
        file=sys.stderr,
    )
    if not result["sufficient_evidence"]:
        print(
            "FAIL CLOSED: the fetch did not supply sufficient evidence for all six permitted dates -- "
            "per the amendment, this classifies AVB-D downstream. No adjacent-day substitute, no retry "
            "with a broadened request.",
            file=sys.stderr,
        )
    return 0 if result["sufficient_evidence"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
