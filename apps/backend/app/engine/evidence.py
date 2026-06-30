"""Read-side evidence resolver (goal-mcp-loop iter-1) — RECOMPUTES NOTHING.

This module is the SINGLE source of the displayed proven-ness the UI shows. It reads the append-only
certified-claims ledger (the SAME file the post-decompose gate writes via `app.mcp.tools.verify_edge`)
and projects it into the read-only `GET /api/evidence` payload:

  - `claims`         — the certified-claims ledger rows the Evidence page renders (hypothesis = the cohort
                       selectors, the out-of-sample verdict, the control comparison, the registration date,
                       and the forward-walk score-to-date), read VERBATIM from each entry.
  - `proven_signals` — `{ signal_key -> claim row }` the inline status badge reads.

The evidence ledger is the ONLY source of proven-ness (goal.md Constraints + anti-goal): a signal is
**Proven** ONLY when a ledger entry whose `verdict.status == "PASS"` NAMES it; everything else is
"Not yet proven" — the fail-safe default. This module never computes proven-ness; it re-displays the
referee's verdict exactly as written. A missing/empty ledger is an empty payload (every signal reads
"Not yet proven").

The `signal` key is resolved DEFENSIVELY (`_resolve_signal`): an explicit `claim.signal` (the iter-2+
convention — the gate persists the Evidence-Claim JSON's `signal` verbatim) wins; otherwise, ONLY for a
score-column factor cohort (`kind == "factor"` and `factor` ∈ the three score columns, whose factor key is
byte-identical to the UI signal key) the signal is DERIVED as `signal = factor`. This is display-ROUTING
only — proven-ness still flows 100% from `verdict.status == "PASS"`; deriving a signal never makes a
non-PASS entry proven, and it is non-spoofable (only the three score columns self-map). Any other
signal-less entry maps to NO UI signal (it stays "Not yet proven") instead of raising — preserving the
fail-safe. The derivation is defense-in-depth: a future score-column claim that forgets to stamp `signal`
still lights its badge instead of silently going dark.

The ledger PATH is config/env-driven (anti-goal: No magic numbers — no path literal lives here): the
runtime override `TRENDORA_LEDGER_PATH`, else `config.evidence.ledger_path` resolved against the repo root.
This module consumes `app.engine.ledger` (read) + `app.engine.referee` (the PASS status constant) and
`app.config` READ-ONLY — it modifies none of them.
"""
from __future__ import annotations

import os
from pathlib import Path

from app.config import REPO_ROOT, get_config
from app.engine.ledger import FORWARD_WALK_TYPE, read_entries
from app.engine.referee import STATUS_PASS

# The environment-variable NAME (the NAME only — never a path VALUE literal in code) the runtime ledger
# path may be overridden with. Forward-looking; the config default already points at the gate's ledger.
LEDGER_PATH_ENV = "TRENDORA_LEDGER_PATH"


def resolve_ledger_path() -> str:
    """The certified-claims ledger path: the `TRENDORA_LEDGER_PATH` env override if set, else
    `config.evidence.ledger_path` resolved against `REPO_ROOT` when relative.

    This MUST resolve to the SAME file the post-decompose gate writes (set by `run-goal.sh`), so the UI's
    proven-ness is consistent with what the referee certified. No path literal lives here — the default
    lives in config (anti-goal: No magic numbers)."""
    override = os.environ.get(LEDGER_PATH_ENV)
    if override:
        return override
    configured = Path(get_config().evidence.ledger_path)
    if not configured.is_absolute():
        configured = REPO_ROOT / configured
    return str(configured)


# The three per-stock score columns whose factor-catalog key is BYTE-IDENTICAL to the UI signal key.
# ONLY these three self-map when a PASS claim omits an explicit `signal` (non-spoofable display-routing —
# no other factor or cohort kind derives a signal). Proven-ness is unaffected: it still requires a PASS.
_SCORE_COLUMN_FACTORS = frozenset({"leadership_score", "entry_quality_score", "risk_score"})


def _resolve_signal(claim: dict) -> str | None:
    """The UI signal key this claim's badge routes to, resolved defensively (display-routing ONLY — this
    never decides proven-ness, which flows solely from `verdict.status == PASS`):

      1. an explicit `claim["signal"]` (the iter-2+ convention — the gate persists the Evidence-Claim
         JSON's `signal` verbatim) always wins;
      2. else, ONLY for a score-column factor cohort (`kind == "factor"` and `factor` ∈ the three score
         columns), DERIVE `signal = factor` — a tautologically honest, non-spoofable self-map that keeps a
         future score-column claim which forgot to stamp `signal` from silently going dark;
      3. else `None` — any other signal-less entry maps to NO UI signal (it stays "Not yet proven"),
         preserving the fail-safe."""
    explicit = claim.get("signal")
    if explicit:
        return explicit
    if claim.get("kind") == "factor" and claim.get("factor") in _SCORE_COLUMN_FACTORS:
        return claim.get("factor")
    return None


def _claim_row(entry: dict) -> dict:
    """Project ONE ledger entry into a read-only claim row — read VERBATIM (the UI never recomputes
    proven-ness). `signal` is resolved defensively (`_resolve_signal`) so a signal-less PASS entry never
    KeyErrors. A row is `proven` ONLY when its referee verdict status is PASS (re-displayed, not
    recomputed)."""
    claim = entry.get("claim") if isinstance(entry.get("claim"), dict) else {}
    verdict = entry.get("verdict") if isinstance(entry.get("verdict"), dict) else {}
    return {
        "signal": _resolve_signal(claim),
        "claim": claim,                       # the hypothesis (cohort selectors), verbatim
        "register_date": entry.get("register_date"),
        "horizon": entry.get("horizon"),
        "cohort_n": entry.get("cohort_n"),
        "control_n": entry.get("control_n"),
        "verdict": verdict,                   # status + reason + holdout edge + control comparison, verbatim
        "proven": verdict.get("status") == STATUS_PASS,
        # forward-walk score-to-date: populated by the renewing-holdout monitor once a claim is certified;
        # None today (empty ledger). Surfaced so the page's claim-row layout is complete + testable now.
        "forward_walk": entry.get("forward_walk"),
    }


def build_evidence_payload(ledger_path: str) -> dict:
    """Project the certified-claims ledger at `ledger_path` into the read-only `/api/evidence` payload.

      - `claims`: every ORIGINAL claim row, read verbatim. Forward-walk MONITORING records
        (`type == 'forward_walk'`) are EXCLUDED — they re-score an existing claim, they are not new claims.
      - `proven_signals`: `{ signal_key -> claim row }` for ONLY the entries whose `verdict.status == "PASS"`
        AND that NAME a `signal`. A signal absent from this map is, by definition, "Not yet proven".

    A missing/empty ledger ⇒ `{"claims": [], "proven_signals": {}}`. RECOMPUTES NOTHING — every verdict
    field is re-displayed exactly as the referee wrote it."""
    claims: list[dict] = []
    proven_signals: dict[str, dict] = {}
    for entry in read_entries(ledger_path):
        if not isinstance(entry, dict) or entry.get("type") == FORWARD_WALK_TYPE:
            continue
        row = _claim_row(entry)
        claims.append(row)
        signal = row["signal"]
        if row["proven"] and signal:
            proven_signals[signal] = row
    return {"claims": claims, "proven_signals": proven_signals}
