"""GET /api/research/graveyard — the read-only negative-results graveyard surface (goal-mcp-loop iter-31,
J-19 / backlog B-902).

Serves `app.engine.graveyard.build_graveyard_payload` verbatim (re-format only — no recompute): every
NON-PASS referee verdict across BOTH the canonical and staging certified-claims ledgers, each tagged with
its origin ledger and joined to its registration lineage, plus the served `revisit_protocol` constant.

No DB/session is needed (both ledgers are append-only state files, not the snapshot DB). Ledger paths are
config/env-driven via the resolvers (anti-goal: No magic numbers — no path literal here). A missing/empty
ledger (either or both) returns 200 with an empty entries list, never a 500 (anti-goal: resilience to
data-shape change).

READ-ONLY, always: this module carries no deletion/edit path for any entry (append-only history), and no
proven-language — a verdict-kind (FAIL/INSUFFICIENT) is descriptive, never a "Proven"/"Not yet proven"
signal. That continues to flow solely from `app.engine.evidence` / `GET /api/evidence`, untouched here.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.engine.graveyard import build_graveyard_payload

router = APIRouter(tags=["graveyard"])


@router.get("/research/graveyard")
def get_graveyard() -> dict:
    """Every NON-PASS referee verdict across both ledgers, verbatim, tagged by origin ledger and
    lineage-attached: `{"entries": [...], "revisit_protocol": {...}}`. READ-ONLY — recomputes nothing. A
    missing/empty ledger (either or both) ⇒ fewer/zero entries (200, never 500)."""
    return build_graveyard_payload()
