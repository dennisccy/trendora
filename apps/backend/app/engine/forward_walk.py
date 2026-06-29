"""The **forward-walk monitor** — Trendora's *renewing holdout*.

The referee's sealed temporal holdout (`app.engine.referee`) is a DEPLETING resource: every certified
claim is judged against the slice of history that existed at registration, and once that out-of-sample
window is consumed it cannot be re-used without leaking future information into the past. This module is
the permanent BACKSTOP. As NEW market data arrives over time, it RE-SCORES every previously-certified
claim against the LATEST available data — a forward walk whose holdout RENEWS itself out of dates that did
not exist when the claim was first tested. An edge that genuinely persists keeps passing; one that has
quietly decayed FAILS forward, on data it was never fit to.

It is a STANDALONE job (NOT goal mode), and it is a MONITOR, not a test:
  * it re-runs `referee.certify_edge` using the claim's ORIGINAL trial ordinal (`n_trials_at_test`) — a
    re-score watches the SAME hypothesis, it is NOT a new multiple-comparisons trial, so it must not
    inflate the Bonferroni divisor;
  * it re-scores against a FRESH, uncharged alpha budget — forward-walk monitoring must never consume the
    certification alpha budget (that budget governs what may SHIP, not the watching of what already did);
  * it APPENDS a ``{"type": "forward_walk", ...}`` record to the SAME append-only ledger — records that
    `ledger.count_trials` / `ledger.alpha_spent` deliberately EXCLUDE, so monitoring leaves the state a
    future certification deflates against completely intact;
  * it is IDEMPOTENT per (claim, as-of): re-running it for the same data frontier appends nothing new.

How new / matured data enters the re-score: the assembler reads the LIVE DB (the same
`app.mcp.tools.assemble_claim_observations` seam `verify_edge` uses). As snapshots are ingested and
forward returns mature, the SAME claim re-assembles to a LARGER cohort+control spanning later dates; the
referee then re-splits that larger series, so the renewed sealed holdout is dominated by the new dates —
the genuine out-of-sample test the depleting historical holdout can no longer provide.

PURE-ish: all statistics are the PURE referee; the only impurity is reading current observations from the
DB and the append-only ledger write. The observation-assembler is INJECTABLE (`assemble=`), so the whole
job is unit-testable WITHOUT a database (mirroring how `tests/test_referee.py` injects synthetic
observations). numpy-only — no new dependencies.

Run it::

    python -m app.engine.forward_walk <ledger_path> [--as-of YYYY-MM-DD]

(default as-of = the latest data date in the DB.)
"""
from __future__ import annotations

from datetime import date as date_cls
from typing import Callable, Optional

from app.engine import ledger as ledger_mod
from app.engine.referee import DEFAULT_ALPHA_BUDGET, DEFAULT_SEED, RefereeState, certify_edge

# An assembler maps a stored `claim` dict -> ``(cohort_obs, control_obs, horizon)`` — exactly the seam
# `app.mcp.tools.assemble_claim_observations` provides. Injectable so the monitor is DB-free in tests.
Assembler = Callable[[dict], tuple]

# The `type` tag carried by every forward-walk record (the certification aggregates skip these — see
# `ledger.count_trials` / `ledger.alpha_spent`). Re-exported from the ledger so there is ONE source.
FORWARD_WALK_TYPE = ledger_mod.FORWARD_WALK_TYPE


def run(
    session,
    ledger_path: str,
    *,
    as_of_date=None,
    assemble: Optional[Assembler] = None,
) -> list[dict]:
    """Re-score every certified claim in `ledger_path` against the latest data and APPEND one forward-walk
    record per claim. Returns the list of records appended THIS run (empty when everything is already up
    to date for `as_of_date` — the idempotent no-op).

    Args:
      session: a live DB session — used only to build the default assembler + resolve the default as-of.
        Ignored when both `assemble` and `as_of_date` are supplied (so tests pass ``None``).
      ledger_path: the append-only certified-claims ledger (the SAME file `verify_edge` writes).
      as_of_date: the data frontier to re-score at (``date`` or ISO ``str``). Defaults to the DB's latest
        data date. It LABELS the re-score and is the per-claim idempotency key.
      assemble: an injectable ``claim -> (cohort_obs, control_obs, horizon)``. Defaults to the real
        `assemble_claim_observations` seam (bound to `session`); tests inject a DB-free assembler.
    """
    if assemble is None:
        assemble = _default_assembler(session)
    if as_of_date is None:
        as_of_date = _default_as_of_date(session)
    as_of_str = _as_of_string(as_of_date)

    entries = ledger_mod.read_entries(ledger_path)
    # Idempotency guard: every (claim_ref, as_of) a PRIOR forward-walk run already recorded.
    already: set = {
        (entry.get("claim_ref"), entry.get("as_of_date"))
        for entry in entries
        if isinstance(entry, dict) and entry.get("type") == FORWARD_WALK_TYPE
    }

    appended: list[dict] = []
    for idx, entry in enumerate(entries):
        if not _is_original_claim(entry):
            continue  # skip forward-walk records + any malformed / non-claim row
        claim_ref = idx  # stable id: the original entry's index in append order (append-only => stable)
        if (claim_ref, as_of_str) in already:
            continue  # idempotent — this claim was already re-scored at this data frontier

        verdict = _rescore(entry, assemble)
        record = {
            "type": FORWARD_WALK_TYPE,
            "claim_ref": claim_ref,
            "as_of_date": as_of_str,
            "verdict": verdict.to_dict(),
        }
        ledger_mod.append_entry(ledger_path, record)  # append-only — never rewrites a prior entry
        already.add((claim_ref, as_of_str))
        appended.append(record)
    return appended


def _rescore(entry: dict, assemble: Assembler):
    """Re-run the PURE referee on ONE original claim with CURRENT observations, the claim's ORIGINAL trial
    ordinal, and a FRESH uncharged budget (so monitoring neither inflates n_trials nor spends budget). The
    seed, direction and min_effect_size are taken from the recorded original verdict/claim, so an UNCHANGED
    dataset reproduces the original verdict byte-for-byte — only newer/matured data can move it."""
    claim = entry["claim"]
    orig_verdict = entry["verdict"]
    cohort_obs, control_obs, horizon = assemble(claim)

    n_trials = int(orig_verdict.get("n_trials_at_test") or 1)  # the ORIGINAL ordinal — never inflated
    seed_val = orig_verdict.get("seed")
    seed = int(seed_val) if seed_val is not None else DEFAULT_SEED
    # Fresh, full budget: forward-walk monitoring must not be REFUSED for an exhausted certification budget
    # nor charge against it — its own `alpha_charged` lives only inside the (excluded) forward-walk record.
    state = RefereeState(n_trials=n_trials, alpha_budget_remaining=DEFAULT_ALPHA_BUDGET)

    direction = claim.get("direction", "positive")
    extra = {}
    if claim.get("min_effect_size") is not None:
        extra["min_effect_size"] = float(claim["min_effect_size"])
    return certify_edge(
        cohort_obs, control_obs, horizon=horizon, state=state, seed=seed, direction=direction, **extra
    )


def _is_original_claim(entry) -> bool:
    """An ORIGINAL claim verdict (the rows `verify_edge` writes): a dict carrying a `claim` + a `verdict`
    and NOT itself a forward-walk monitoring record."""
    return (
        isinstance(entry, dict)
        and entry.get("type") != FORWARD_WALK_TYPE
        and isinstance(entry.get("claim"), dict)
        and isinstance(entry.get("verdict"), dict)
    )


def _as_of_string(as_of_date) -> str:
    """Canonical ISO string for the as-of date (the forward-walk record value + idempotency key)."""
    if isinstance(as_of_date, date_cls):
        return as_of_date.isoformat()
    return str(as_of_date)


def _default_assembler(session) -> Assembler:
    """The PRODUCTION assembler: the SHARED `assemble_claim_observations` seam (also used by verify_edge),
    bound to `session`. Imported LAZILY so ``import app.engine.forward_walk`` stays light (numpy + referee
    + ledger only) and DB-free tests never drag in the MCP / tools / SQLAlchemy stack."""
    from app.mcp.tools import assemble_claim_observations

    def assemble(claim: dict) -> tuple:
        return assemble_claim_observations(session, claim)

    return assemble


def _default_as_of_date(session):
    """The DB's latest data date — the default data frontier to re-score at. Imported lazily (see above)."""
    from app.engine.prices import latest_data_date

    return latest_data_date(session)


def _main(argv: Optional[list] = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m app.engine.forward_walk",
        description=(
            "Forward-walk monitor (the renewing holdout): re-score every certified claim in a ledger "
            "against the latest data. Appends type=forward_walk records; never spends the certification "
            "alpha budget and never inflates n_trials. Idempotent per (claim, as-of)."
        ),
    )
    parser.add_argument("ledger_path", help="path to the append-only certified-claims ledger (JSONL)")
    parser.add_argument(
        "--as-of",
        dest="as_of",
        default=None,
        metavar="YYYY-MM-DD",
        help="data frontier to re-score at; default = the DB's latest data date",
    )
    args = parser.parse_args(argv)

    from sqlmodel import Session

    from app.db import get_engine

    with Session(get_engine()) as session:
        records = run(session, args.ledger_path, as_of_date=args.as_of)
    frontier = args.as_of or "latest"
    print(f"forward-walk @ {frontier}: appended {len(records)} re-score record(s) to {args.ledger_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
