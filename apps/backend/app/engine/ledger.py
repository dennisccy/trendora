"""The append-only **certified-claims ledger** (JSONL).

Every `verify_edge` call appends ONE line — a JSON object carrying the claim, the register date, and the
referee's full `Verdict` — to a newline-delimited JSON file. The ledger is the referee's MEMORY across
claims: it supplies the two pieces of cumulative state the next certification deflates against —
``count_trials`` (the Bonferroni divisor) and ``alpha_spent`` (so the remaining Thresholdout budget =
starting budget − amount already spent).

Discipline: **APPEND-ONLY**. Entries are only ever appended; an existing line is never rewritten or
deleted (an immutable audit trail of every claim ever tested — including the rejected ones, so the
multiple-testing count cannot be quietly reset). A MISSING ledger file is an EMPTY ledger (0 trials, 0
alpha spent) — the first claim against a fresh path starts from a clean budget.

PURE filesystem I/O — no DB, no engine. JSON-serializable values only; non-JSON values (e.g. a `date`)
are stringified on write so the ledger never raises on an exotic claim payload.
"""
from __future__ import annotations

import json
import os
from typing import Any

# A forward-walk MONITORING record (written by `app.engine.forward_walk`, the renewing holdout) carries
# this `type`. It RE-scores an already-certified claim against newer data — it is monitoring the same
# hypothesis, NOT a new test — so it is EXCLUDED from BOTH the multiple-testing count (`count_trials`, the
# Bonferroni divisor) and the spent-budget total (`alpha_spent`): forward-walk monitoring must never
# inflate the trial count nor consume the certification alpha budget. ORIGINAL claim verdicts (written by
# `verify_edge`) carry no `type` and ARE counted. `read_entries` still returns EVERY line (the monitor
# needs them) — only the certification AGGREGATES skip these records.
FORWARD_WALK_TYPE = "forward_walk"


def _is_forward_walk(entry: Any) -> bool:
    """True for a forward-walk monitoring record (``entry['type'] == 'forward_walk'``) — the rows the
    certification aggregates (`count_trials`, `alpha_spent`) must exclude."""
    return isinstance(entry, dict) and entry.get("type") == FORWARD_WALK_TYPE


def append_entry(path: str, entry: dict) -> None:
    """Append one entry as a single JSON line (append-only — never rewrites an existing line). Creates
    the parent directory and the file on first write. `default=str` makes any non-JSON value (e.g. a
    `date`) safe to record."""
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, default=str, sort_keys=True) + "\n")


def read_entries(path: str) -> list[dict]:
    """Every ledger entry in append order. A missing file is an empty ledger (``[]``); blank lines are
    skipped so a trailing newline never yields a phantom entry."""
    if not os.path.exists(path):
        return []
    entries: list[dict] = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def count_trials(path: str) -> int:
    """The cumulative number of claims tested = the number of ORIGINAL claim entries (one per
    `verify_edge` call, INCLUDING rejected/refused claims — the multiple-testing count cannot be reset by
    failing). Forward-walk MONITORING records (`type='forward_walk'`) are EXCLUDED — a re-score is not a
    new test and must not inflate the Bonferroni divisor. Missing file ⇒ 0."""
    return sum(1 for entry in read_entries(path) if not _is_forward_walk(entry))


def _entry_alpha_charged(entry: Any) -> float:
    """The alpha charged by one entry, read from its recorded verdict (``entry['verdict']['alpha_
    charged']``), tolerating a flattened ``entry['alpha_charged']`` too. Anything unparseable ⇒ 0.0."""
    if not isinstance(entry, dict):
        return 0.0
    verdict = entry.get("verdict")
    candidate = None
    if isinstance(verdict, dict) and verdict.get("alpha_charged") is not None:
        candidate = verdict["alpha_charged"]
    elif entry.get("alpha_charged") is not None:
        candidate = entry["alpha_charged"]
    if candidate is None:
        return 0.0
    try:
        return float(candidate)
    except (TypeError, ValueError):
        return 0.0


def alpha_spent(path: str) -> float:
    """The cumulative alpha budget spent so far = the sum of every ORIGINAL claim entry's recorded
    ``alpha_charged`` (stable edges charge 0; overfit ones charge the per-claim cost). Forward-walk
    MONITORING records (`type='forward_walk'`) are EXCLUDED — re-scoring an aging claim must never consume
    the certification budget, even when the re-score itself is unstable. Missing file ⇒ 0.0. The remaining
    budget the next certification gets is ``starting_budget − alpha_spent(path)``."""
    return sum(
        _entry_alpha_charged(entry) for entry in read_entries(path) if not _is_forward_walk(entry)
    )
