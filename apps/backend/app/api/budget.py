"""GET /api/research/budget — the read-only certification-budget accounting panel (goal-mcp-loop
iter-32, J-17 / backlog B-903).

Serves `app.engine.budget_accounting.build_budget_payload` verbatim (re-format only — no recompute):
total canonical trials to date, the current canonical `required_p` bar, the Thresholdout budget
remaining, and the staging LORD++ next-trial level — each with a per-trial spend-over-time series, all
re-read from the SAME `ledger` / `online_fdr` / `referee` seams `app.mcp.tools.verify_edge` uses.

No DB/session is needed (both ledgers are append-only state files, not the snapshot DB). Ledger paths
are config/env-driven via the existing resolvers (anti-goal: No magic numbers — no path literal here).
A missing/empty ledger (either or both) returns 200 with the honest empty-ledger accounting the
formulas naturally produce, never a 500 (anti-goal: resilience to data-shape change).

READ-ONLY, always: no proven-language — trial counts and alpha figures are descriptive accounting,
never a "Proven"/"Not yet proven" signal. That continues to flow solely from `app.engine.evidence` /
`GET /api/evidence`, untouched here.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.engine.budget_accounting import build_budget_payload

router = APIRouter(tags=["budget"])


@router.get("/research/budget")
def get_budget() -> dict:
    """The certification-budget accounting payload, verbatim: `{"canonical": {...}, "staging": {...}}`.
    READ-ONLY — recomputes nothing beyond the two forward next-trial bars (via the SAME seams
    `verify_edge` uses). A missing/empty ledger (either or both) ⇒ the honest empty-ledger accounting
    (200, never 500)."""
    return build_budget_payload()
