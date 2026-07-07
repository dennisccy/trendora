"""iter-18 — the SANCTIONED evidence-ledger reset + regeneration on the 30-year basis (J-11).

goal.md, "Data-basis change (sanctioned ledger reset)": when the historical price seed is rebuilt,
EVERY prior certified claim is invalidated — it was measured on the retired window and will not
reproduce. This driver executes the one sanctioned reset of the otherwise append-only ledgers:

  * CANONICAL — replays the SAME pre-registered 7-claim historical sequence, VERBATIM selectors, in
    the SAME order (including the ma_stack FAIL re-test), each through
    `app.mcp.tools.verify_edge(..., ledger="canonical")` — the ONLY ledger writer — against the
    rebuilt DB. Replaying the FULL family in order preserves each claim's historical Bonferroni
    divisor (1..7): the reset can never grant an easier bar than history did (never bar-laundering).
    Verdicts fall where they fall — HONEST-STOP: a FAIL/INSUFFICIENT is recorded honestly, never
    forced, tweaked, reordered, or retried-with-variations.
  * STAGING — re-runs the two PRE-REGISTERED explorers (`explore_multi_horizon_staging` over
    `config.triad.candidates`, then `explore_combination_staging` over
    `config.triad.combination_candidates`) into a fresh staging ledger under the fenced LORD++
    staging economy, exactly as the committed discovery ran.

No NEW hypotheses, no ad-hoc cohorts, no selector edits — regeneration only. The retiring ledger
contents remain auditable via git history (both files are tracked).

Ledger routing (iter-9b/10/12 lesson — an omitted key silently re-stages): `ledger="canonical"` is
passed EXPLICITLY for every canonical replay. Paths honor the gate convention env overrides
(`LEDGER_PATH` / `STAGING_LEDGER_PATH`, as exported by run-goal.sh), falling back to the config
paths resolved against the repo root.

Usage (destructive by design, so the reset must be explicit):

    .venv/bin/python scripts/regenerate_ledgers.py --yes-reset-both-ledgers [--register-date YYYY-MM-DD]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlmodel import Session  # noqa: E402

from app.config import REPO_ROOT, get_config  # noqa: E402
from app.db import get_engine  # noqa: E402
from app.engine.triad_scan import (  # noqa: E402
    explore_combination_staging,
    explore_multi_horizon_staging,
)
from app.mcp.tools import LEDGER_CANONICAL, verify_edge  # noqa: E402

# ==================================================================================================
# The VERBATIM 7-claim canonical replay sequence — the retiring ledger's claims in historical order
# (selectors byte-for-byte as stored, including claim #1's `signal` stamp and the explicit
# `"ledger": "canonical"` routing keys claims #5-#7 carried from their promotion gates). DO NOT
# reorder; DO NOT edit selectors (the iteration spec's replay table is the source of truth).
# ==================================================================================================
CANONICAL_REPLAY: list[dict] = [
    {  # 1 — leadership_score D10 h20 (backs the /stocks Leadership badge, J-01/J-02)
        "kind": "factor", "factor": "leadership_score", "slice_kind": "decile", "decile": 10,
        "horizon": 20, "direction": "positive", "signal": "leadership_score",
    },
    {  # 2 — Breakout-watch × Risk-on event-study (regime evidence row, J-04)
        "kind": "event-study", "subject": "Breakout-watch", "slice_kind": "regime",
        "regime": "Risk-on", "view": "pooled", "horizon": 20, "direction": "positive",
    },
    {  # 3 — ma_stack D10 h20 (the historical FAIL — re-tested so divisor 3 is faced again, J-03)
        "kind": "factor", "factor": "ma_stack", "slice_kind": "decile", "decile": 10,
        "horizon": 20, "direction": "positive",
    },
    {  # 4 — vcp_contraction D10 h20 (factor lab h20, J-06)
        "kind": "factor", "factor": "vcp_contraction", "slice_kind": "decile", "decile": 10,
        "horizon": 20, "direction": "positive",
    },
    {  # 5 — vcp_contraction D10 h60 (factor lab h60, J-07)
        "kind": "factor", "factor": "vcp_contraction", "slice_kind": "decile", "decile": 10,
        "horizon": 60, "direction": "positive", "ledger": "canonical",
    },
    {  # 6 — rs_spy_3m × high_proximity composite h20 (combination lab, J-08)
        "kind": "combination", "cohort": "composite",
        "condition": ["rs_spy_3m:top:quintile", "high_proximity:top:tertile"],
        "horizon": 20, "direction": "positive", "ledger": "canonical",
    },
    {  # 7 — rs_spy_3m D10 h60 (factor lab rs h60, J-09)
        "kind": "factor", "factor": "rs_spy_3m", "slice_kind": "decile", "decile": 10,
        "horizon": 60, "direction": "positive", "ledger": "canonical",
    },
]


def _resolve_path(env_var: str, config_path: str) -> Path:
    """The gate-convention env override (run-goal.sh exports LEDGER_PATH/STAGING_LEDGER_PATH), else
    the config path resolved against the repo root."""
    override = os.environ.get(env_var)
    if override:
        return Path(override)
    p = Path(config_path)
    return p if p.is_absolute() else (REPO_ROOT / p)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--yes-reset-both-ledgers", action="store_true",
        help="REQUIRED: confirms the goal.md-sanctioned reset (truncates BOTH ledgers, then regenerates)",
    )
    parser.add_argument(
        "--register-date", default=date.today().isoformat(),
        help="register_date stamped on every regenerated verdict (default: today — the actual run date)",
    )
    args = parser.parse_args()
    if not args.yes_reset_both_ledgers:
        parser.error("refusing to run without --yes-reset-both-ledgers (this truncates both ledgers)")

    cfg = get_config()
    canonical_path = _resolve_path("LEDGER_PATH", cfg.evidence.ledger_path)
    staging_path = _resolve_path("STAGING_LEDGER_PATH", cfg.evidence.staging_ledger_path)
    print(f"[ledgers] canonical={canonical_path}")
    print(f"[ledgers] staging  ={staging_path}")

    # ---- the sanctioned reset: truncate the canonical ledger (old content auditable via git) -----
    if canonical_path.exists():
        canonical_path.unlink()
        print("[reset] canonical ledger truncated (git history keeps the retiring content)")

    engine = get_engine()
    results: list[dict] = []
    with Session(engine) as session:
        # ---- CANONICAL: the verbatim 7-claim replay, explicit ledger="canonical" per call --------
        for i, claim in enumerate(CANONICAL_REPLAY, start=1):
            out = verify_edge(
                session,
                dict(claim),  # a fresh copy per call — the template constants stay pristine
                str(canonical_path),
                register_date=args.register_date,
                ledger=LEDGER_CANONICAL,  # EXPLICIT routing — an omitted key silently re-stages
            )
            v = out["verdict"]
            results.append({"n": i, "claim": claim, "verdict": v})
            label = claim.get("factor") or claim.get("subject") or claim.get("cohort")
            print(
                f"[canonical {i}/7] {claim['kind']}:{label} h{out['horizon']} -> {v['status']} "
                f"(p={v['p_value']:.10g}, required_p={v['required_p']:.10g}, divisor={v['deflation_divisor']}, "
                f"holdout_edge={v.get('holdout_edge')}, cohort_n={out['cohort_n']}, control_n={out['control_n']})",
                flush=True,
            )

        # ---- STAGING: the two pre-registered explorers into a FRESH staging ledger ---------------
        multi = explore_multi_horizon_staging(
            session, ledger_path=str(staging_path), register_date=args.register_date, reset=True,
        )
        for r in multi["results"]:
            v = r["verdict"]
            print(
                f"[staging mh] {r['claim']['factor']} h{r['claim']['horizon']} -> {v['status']} "
                f"(p={v['p_value']:.10g}, required_p={v['required_p']:.10g}, {v['deflation']})",
                flush=True,
            )
        combo = explore_combination_staging(
            session, ledger_path=str(staging_path), register_date=args.register_date, reset=False,
        )
        for r in combo["results"]:
            v = r["verdict"]
            print(
                f"[staging cmb] {'+'.join(r['claim']['condition'])} h{r['claim']['horizon']} -> {v['status']} "
                f"(p={v['p_value']:.10g}, required_p={v['required_p']:.10g}, {v['deflation']})",
                flush=True,
            )

    # ---- the honest verdict table (for the dev handoff) ------------------------------------------
    print("\n[replay verdict table]")
    for row in results:
        c, v = row["claim"], row["verdict"]
        label = c.get("factor") or c.get("subject") or c.get("cohort")
        print(f"  #{row['n']} {c['kind']}:{label} h{c['horizon']} -> {v['status']}")
    print(json.dumps({"register_date": args.register_date,
                      "canonical": [r["verdict"]["status"] for r in results],
                      "staging_multi": [r["verdict"]["status"] for r in multi["results"]],
                      "staging_combo": [r["verdict"]["status"] for r in combo["results"]]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
