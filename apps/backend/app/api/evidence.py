"""GET /api/evidence — the read-only certified-claims ledger surface (goal-mcp-loop iter-1).

Serves `app.engine.evidence.build_evidence_payload` over the ledger the post-decompose gate writes (the
single source of proven-ness). READ-ONLY: this endpoint never writes the ledger and never computes
proven-ness — it re-displays the referee's verdicts verbatim. An absent/empty ledger returns 200 with an
empty payload (`{"claims": [], "proven_signals": {}}`), never a 500 — the fail-safe the whole evidence
frame rests on (an unbacked signal must render "Not yet proven", never a confident number).

No DB/session is needed (the evidence comes from the append-only ledger file, not the snapshot DB). The
ledger path is config/env-driven via the resolver (anti-goal: No magic numbers — no path literal here).
"""
from __future__ import annotations

from fastapi import APIRouter

from app.engine.evidence import build_evidence_payload, resolve_ledger_path

router = APIRouter(tags=["evidence"])


@router.get("/evidence")
def get_evidence() -> dict:
    """The certified-claims ledger payload: `claims` (the ledger rows the Evidence page renders —
    hypothesis, out-of-sample verdict, control comparison, registration date, forward-walk score-to-date)
    plus the `proven_signals` map the inline status badge reads. READ-ONLY — recomputes no proven-ness.
    Empty/absent ledger ⇒ `{"claims": [], "proven_signals": {}}` (200, never 500)."""
    return build_evidence_payload(resolve_ledger_path())
