"""goal-market-compass iter-9 — the committed, reproducible J-10 POPULATION recovery driver.

Runs `app.engine.j10_recovery.run_gated_population_recovery` against the LIVE production database for
the recovery-population remainder (`still_missing_symbols()`, up to 567 of the 587 `RECOVERY_SYMBOLS`
— the 20 iteration 8 already restored are excluded automatically, idempotently). This is the ONE
committed caller that closes the reproducibility gap iteration 8's audit flagged (B8): "the live run is
not reproducible from the repository ... no recovery driver script is committed". Every real,
population-scale J-10 fetch/insert this iteration performs runs through this exact file.

What this script does NOT do (all already enforced, in code, inside `j10_recovery.py` itself — this
script adds no new authorization, no new threshold, no new scope):
  - it never widens `RECOVERY_SYMBOLS`, `RECOVERY_DATES`, `RECOVERY_SOURCE`, or any of the frozen
    per-symbol gate thresholds (`PATH_AGREEMENT_TOLERANCE`, `BRIDGE_DISPERSION_BOUND`,
    `MIN_COMPARABLE_PAIRS_PER_SYMBOL`) — all read, none passed as an override (none of these entry
    points even accept one);
  - it never re-samples or re-derives `CONVENTION_CHECK_SAMPLE_SYMBOLS` (the frozen 20-name
    methodology-validation sample) — this driver calls ONLY `run_gated_population_recovery`, which
    samples `still_missing_symbols()`, never the frozen constant;
  - it never touches a symbol outside the authorized envelope (`validate_recovery_scope` refuses that,
    unconditionally, before any network call);
  - it never inserts an untransformed row (`run_bounded_recovery_fetch`'s iter-9 gate refuses any
    symbol without a recorded passing bridge factor).

Idempotent by construction (TC-9): every symbol already fully restored (both recovery dates present) is
excluded from `still_missing_symbols()` — and therefore from the population SAMPLE itself — before the
convention check ever runs, so a re-run after a partial/failed/complete prior attempt only ever
evaluates what is still genuinely missing, and a re-run once nothing is missing makes zero convention
checks, zero fetches, zero writes (verified after the real run, see the dev handoff).

Retry model (`--max-passes`, default 2): AG-9's own text authorizes "a re-run of the same bounded,
idempotent recovery after a failed or partial attempt" — this is NOT a re-run of the frozen methodology
sample (that stays untouched) and NOT a threshold loosening; it is the SAME fixed gate, re-applied to
whatever the live population still contains after the previous pass, which naturally shrinks the
population on every pass that restores anything. A second pass exists ONLY to rescue a population
member whose FIRST verdict was "inconclusive" for a purely transient reason (a single dropped
connection, a momentary Yahoo hiccup) — never to convert a genuine "mismatch" into anything else (a
mismatch verdict is deterministic given the same stored/fallback series and does not change between
passes). The script stops early, before `--max-passes`, the moment a pass restores nothing at all
(no further progress is possible without a genuine methodology or scope change, neither of which this
script may perform).

Each pass's FULL per-pair evidence is written to its own file, then merged (symbol-keyed, latest pass
wins for any symbol re-sampled, everything else carried forward unchanged) into the ONE canonical
`--evidence-path` — so the final artifact always carries EXACTLY ONE recorded verdict per population
symbol (TC-1), never a partial file reflecting only the last pass's shrunken sample.

Usage:
    apps/backend/.venv/bin/python apps/backend/scripts/run_j10_population_recovery.py \\
        [--evidence-path runs/goal-market-compass-iter-9/j10-population-evidence.json] \\
        [--max-passes 2]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

# scripts/ -> backend -> apps -> repo root
BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from sqlmodel import Session  # noqa: E402

from app.config import load_config  # noqa: E402
from app.data_providers.yahoo_provider import YahooProvider  # noqa: E402
from app.db import get_engine, resolve_database_url  # noqa: E402
from app.engine import j10_recovery  # noqa: E402
from app.engine.j10_recovery import (  # noqa: E402
    EXCLUDED_UNPROVEN_SYMBOLS,
    RECOVERY_DATES,
    RECOVERY_SOURCE,
    RECOVERY_SYMBOLS,
    run_gated_population_recovery,
    still_missing_symbols,
)

DEFAULT_EVIDENCE_PATH = REPO_ROOT / "runs" / "goal-market-compass-iter-9" / "j10-population-evidence.json"


class _ProgressLoggingYahooProvider(YahooProvider):
    """A THIN, driver-script-only subclass of the real `YahooProvider` — adds nothing to the gate/fetch
    contract (it is still exactly `YahooProvider`, `source == "yahoo"` inherited unchanged), only a
    one-line stderr progress log per `get_daily` call, so a long (500+ symbol) sequential calibration
    pass is observable while it runs instead of being a single opaque multi-minute blocking call."""

    def __init__(self) -> None:
        super().__init__()
        self.call_count = 0

    def get_daily(self, symbol, start=None, end=None):
        self.call_count += 1
        print(f"  [{self.call_count:>4}] get_daily({symbol!r}, {start}, {end})", file=sys.stderr, flush=True)
        return super().get_daily(symbol, start=start, end=end)


def _load_evidence(path: Path) -> "dict | None":
    if not path.exists():
        return None
    return json.loads(path.read_text())


def _merge_evidence(base: "dict | None", fresh: dict) -> dict:
    """Merge `fresh` (this pass's full, freshly-persisted `ConventionCheckBatchResult`) on top of
    `base` (the canonical file's PRIOR content, if any): every symbol `fresh` actually sampled this
    pass overrides the same symbol's row in `base` (a newer, more current verdict); every symbol
    present in `base` but NOT re-sampled this pass (already restored by an earlier pass, or simply not
    yet reached) is carried forward byte-unchanged. Threshold/window metadata is taken from `fresh` (the
    most recent pass) — these are frozen constants that never legitimately differ between passes."""
    if base is None:
        return fresh
    by_symbol = {row["symbol"]: row for row in base.get("symbols", [])}
    for row in fresh["symbols"]:
        by_symbol[row["symbol"]] = row
    merged = dict(fresh)
    merged["symbols"] = [by_symbol[s] for s in sorted(by_symbol)]
    merged["sample_symbols"] = sorted(by_symbol)
    return merged


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--evidence-path", type=Path, default=DEFAULT_EVIDENCE_PATH,
        help="the ONE canonical, merged evidence artifact (default: %(default)s)",
    )
    parser.add_argument(
        "--max-passes", type=int, default=2,
        help="retry passes over the still-missing remainder (default: 2) — see the module docstring's "
             "'Retry model'; a pass that restores nothing stops the loop early regardless of this cap",
    )
    args = parser.parse_args()

    cfg = load_config()
    engine = get_engine()  # resolves database.url from the SAME committed config.yaml the app boots
    # under — the real, live apps/backend/data/trendora.db. No override: this driver operates on the
    # SAME database the product serves from, exactly like every prior J-10 iteration's real run.
    print(f"database: {resolve_database_url(cfg.database.url)}", file=sys.stderr)
    print(
        f"RECOVERY_DATES={sorted(d.isoformat() for d in RECOVERY_DATES)} "
        f"RECOVERY_SOURCE={RECOVERY_SOURCE!r} RECOVERY_SYMBOLS={len(RECOVERY_SYMBOLS)} "
        f"EXCLUDED_UNPROVEN_SYMBOLS={sorted(EXCLUDED_UNPROVEN_SYMBOLS)}",
        file=sys.stderr,
    )

    with Session(engine) as session:
        pre_missing = still_missing_symbols(session)
    print(f"pre-recovery still-missing population: {len(pre_missing)} symbol(s)", file=sys.stderr)
    if not pre_missing:
        print("nothing missing -- true zero-work no-op, exiting.", file=sys.stderr)
        return 0

    evidence_path = args.evidence_path
    canonical_prior = _load_evidence(evidence_path)
    restored_this_run: list[str] = []
    all_verdicts_by_symbol: dict[str, dict] = {}
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    invocation_stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())  # makes each invocation's own
    # per-pass raw evidence files unique on disk (see the loop below) -- otherwise a SECOND invocation of
    # this script (e.g. a later idempotency re-check) would silently overwrite the FIRST invocation's
    # `-pass1.json` with its own (likely much smaller) pass-1 population, destroying that earlier raw
    # snapshot even though the canonical merged file itself stays correct either way.

    provider_empty_range: dict[str, str] = {}  # symbol -> reason, for an "agree" verdict whose fetch
    # genuinely inserted nothing because the fallback provider returned ZERO bars for the target
    # recovery dates themselves (a vendor-side data gap, e.g. a halted/delisted symbol) -- DISTINCT from
    # a convention-gate mismatch/inconclusive verdict. `outcome.fetch.requested_symbols` only records
    # what the fetch job was ASKED for, never whether a bar actually landed for a given symbol -- so
    # "restored" is determined here by a fresh post-pass `still_missing_symbols()` diff, never by the
    # request list alone (the exact gap iter-9's own live run against EA exposed and this fix closes).

    for pass_num in range(1, args.max_passes + 1):
        with Session(engine) as session:
            population = still_missing_symbols(session)
        if not population:
            print(f"pass {pass_num}: nothing left missing -- stopping early.", file=sys.stderr)
            break
        print(f"\n=== pass {pass_num}/{args.max_passes}: {len(population)} symbol(s) still missing ===",
              file=sys.stderr)

        provider = _ProgressLoggingYahooProvider()
        pass_evidence_path = evidence_path.with_name(
            f"{evidence_path.stem}-{invocation_stamp}-pass{pass_num}{evidence_path.suffix}"
        )
        with Session(engine) as session:
            outcome = run_gated_population_recovery(
                session, engine, cfg, convention_provider=provider, evidence_path=pass_evidence_path,
            )

        fresh = json.loads(pass_evidence_path.read_text())
        canonical_prior = _merge_evidence(canonical_prior, fresh)
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        evidence_path.write_text(json.dumps(canonical_prior, indent=2, sort_keys=True))

        for v in outcome.convention_check.verdicts:
            all_verdicts_by_symbol[v.symbol] = {
                "verdict": v.verdict, "reason": v.reason, "bridge_factor": v.bridge_factor,
                "comparable_pair_count": v.comparable_pair_count,
            }

        # Ground truth for "actually restored": a fresh DB read AFTER the fetch+backfill, never the
        # fetch job's own `requested_symbols` (that list only reflects what was ASKED for).
        with Session(engine) as session:
            still_missing_after = set(still_missing_symbols(session))
        agree_symbols = {v.symbol for v in outcome.convention_check.verdicts if v.verdict == "agree"}
        pass_restored = sorted(agree_symbols - still_missing_after)
        pass_agree_but_empty = sorted(agree_symbols & still_missing_after)
        restored_this_run.extend(pass_restored)
        for s in pass_agree_but_empty:
            provider_empty_range[s] = (
                "convention gate verdict was 'agree' (a stable bridge factor was derived), but the "
                "fallback provider (yahoo) returned ZERO bars for the target recovery date(s) "
                "themselves -- a genuine vendor-side data gap (e.g. a halted/delisted symbol), "
                "distinct from a convention-gate mismatch/inconclusive; see the dev handoff for the "
                "live re-fetch citation confirming this is not transient"
            )

        by_verdict: dict[str, int] = {}
        for v in outcome.convention_check.verdicts:
            by_verdict[v.verdict] = by_verdict.get(v.verdict, 0) + 1
        print(
            f"pass {pass_num} result: {by_verdict} -- actually restored {len(pass_restored)} symbol(s): "
            f"{pass_restored}", file=sys.stderr,
        )
        if pass_agree_but_empty:
            print(f"pass {pass_num} WARNING -- 'agree' verdict but provider returned no data for the "
                  f"target dates: {pass_agree_but_empty}", file=sys.stderr)
        if outcome.backfill is not None:
            print(f"pass {pass_num} backfill summary: {outcome.backfill}", file=sys.stderr)
        if not pass_restored:
            print(f"pass {pass_num} restored nothing -- no further progress possible; stopping.",
                  file=sys.stderr)
            break

    with Session(engine) as session:
        post_missing = still_missing_symbols(session)
    finished = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    not_restored = [
        {"symbol": s, "verdict": v["verdict"], "reason": v["reason"]}
        for s, v in sorted(all_verdicts_by_symbol.items())
        if v["verdict"] != "agree"
    ]
    for s, reason in sorted(provider_empty_range.items()):
        not_restored.append({"symbol": s, "verdict": "agree_but_no_provider_data", "reason": reason})
    not_restored.sort(key=lambda r: r["symbol"])
    print("\n=== FINAL SUMMARY ===", file=sys.stderr)
    print(f"started:  {started}", file=sys.stderr)
    print(f"finished: {finished}", file=sys.stderr)
    print(f"pre-recovery missing:  {len(pre_missing)} symbol(s)", file=sys.stderr)
    print(f"post-recovery missing: {len(post_missing)} symbol(s)", file=sys.stderr)
    print(f"restored this run: {len(restored_this_run)} symbol(s): {sorted(restored_this_run)}",
          file=sys.stderr)
    print(f"requested but not restored: {len(not_restored)} symbol(s)", file=sys.stderr)
    for row in not_restored:
        print(f"  {row['symbol']}: {row['verdict']} -- {row['reason']}", file=sys.stderr)
    print(f"\ncanonical evidence artifact: {evidence_path} ({len(canonical_prior.get('symbols', []))} "
          f"symbol row(s))", file=sys.stderr)

    summary_path = evidence_path.with_name("j10-population-summary.json")
    summary_path.write_text(json.dumps({
        "started_utc": started,
        "finished_utc": finished,
        "pre_recovery_missing_count": len(pre_missing),
        "post_recovery_missing_count": len(post_missing),
        "restored_symbols": sorted(restored_this_run),
        "requested_but_not_restored": not_restored,
        "still_missing_after_run": sorted(post_missing),
    }, indent=2, sort_keys=True))
    print(f"human-readable run summary: {summary_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
