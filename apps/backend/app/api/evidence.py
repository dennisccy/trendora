"""GET /api/evidence — the read-only certified-claims ledger surface (goal-mcp-loop iter-1).

Serves `app.engine.evidence.build_evidence_payload` over the ledger the post-decompose gate writes (the
single source of proven-ness). READ-ONLY: this endpoint never writes the ledger and never computes
proven-ness — it re-displays the referee's verdicts verbatim. An absent/empty ledger returns 200 with an
empty payload (`{"claims": [], "proven_signals": {}}`), never a 500 — the fail-safe the whole evidence
frame rests on (an unbacked signal must render "Not yet proven", never a confident number).

The ledger path is config/env-driven via the resolver (anti-goal: No magic numbers — no path literal
here). A DB session is threaded through (iter-41, J-25) so `build_evidence_payload` can ADDITIVELY attach
each claim's phase-conditional drawdown/dry-spell `expectations` (`app.engine.forward_testing.
compute_drawdown_expectations`) — the snapshot DB itself is still never written by this route.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.config import get_config
from app.db import get_session
from app.engine.evidence import build_evidence_payload, resolve_ledger_path

router = APIRouter(tags=["evidence"])


@router.get("/evidence")
def get_evidence(session: Session = Depends(get_session)) -> dict:
    """The certified-claims ledger payload: `claims` (the ledger rows the Evidence page renders —
    hypothesis, out-of-sample verdict, control comparison, registration date, forward-walk score-to-date,
    and the additive iter-41 `expectations` drawdown/dry-spell panel) plus the `proven_signals` map the
    inline status badge reads. READ-ONLY — recomputes no proven-ness; the snapshot DB is read-only here
    too (`compute_drawdown_expectations` is a pure read-compose). Empty/absent ledger ⇒
    `{"claims": [], "proven_signals": {}}` (200, never 500)."""
    return build_evidence_payload(resolve_ledger_path(), session=session, config=get_config())
