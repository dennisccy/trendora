"""GET /api/research/referee-audit — the read-only referee-calibration report (goal-mcp-loop iter-36,
J-22 / backlog B-102).

Serves `app.engine.referee_audit.read_referee_audit_report` verbatim (re-format only — no recompute): the
null-trial count, the empirical false-pass rate + binomial CI, the configured α, the lookahead-
contaminated-factor verdict (labeled "expected: rejected"), the run date, and the run parameters — all
re-read from the persisted artifact the offline harness job (`python -m app.engine.referee_audit`) wrote.

No DB/session is needed (the artifact is a state file, not the snapshot DB). The artifact path is
config/env-driven via the existing resolver (anti-goal: No magic numbers — no path literal here). A
missing artifact (the harness has never run) returns 200 with an honest `null` `report`, never a 500
(anti-goal: resilience to data-shape change).

READ-ONLY, always: no proven-language — this endpoint audits the certifier, it certifies nothing. It never
touches `app.engine.evidence` / `GET /api/evidence`, the real ledgers, or the real Thresholdout budget.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.engine.referee_audit import read_referee_audit_report

router = APIRouter(tags=["referee-audit"])


@router.get("/research/referee-audit")
def get_referee_audit() -> dict:
    """The referee-calibration report, verbatim: `{"report": {...} | None}`. READ-ONLY — recomputes
    nothing; a missing artifact (the offline harness has never run) yields `{"report": None}` (200, never
    500), the honest empty state the panel renders as "no audit run yet"."""
    return {"report": read_referee_audit_report()}
