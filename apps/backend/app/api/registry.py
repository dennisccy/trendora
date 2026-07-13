"""GET /api/research/registry — the read-only pre-registration registry surface (goal-mcp-loop iter-30,
J-18 / backlog B-901).

Serves `app.engine.registry.load_registrations` verbatim (re-format only — no recompute): every
hypothesis ever registered/tested, the SAME file + loader the post-decompose gate (`verify_claim.py`)
cross-checks an incoming Evidence Claim against, so the registry page a human browses and the machine
check can never disagree (the Data Contract single source of truth).

No DB/session is needed (the registry comes from the append-only state file, not the snapshot DB). The
registry path is config/env-driven via the resolver (anti-goal: No magic numbers — no path literal here).
A missing/empty registry file returns 200 with an empty list, never a 500 (anti-goal: resilience to
data-shape change) — the honest state before any backfill/registration has landed.

This module carries NO proven-language: a registration's `status` is a descriptive process state
("registered" / "tested" / "closed"), never a "Proven"/"Not yet proven" signal — that continues to flow
solely from the certified-claims ledger via `app.engine.evidence` / `GET /api/evidence`.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.engine.registry import load_registrations

router = APIRouter(tags=["registry"])


@router.get("/research/registry")
def get_registry() -> dict:
    """Every registered hypothesis, verbatim, in registration (append) order: `{"registrations": [...]}`.
    READ-ONLY — recomputes nothing. An absent/empty registry file ⇒ `{"registrations": []}` (200, never
    500)."""
    return {"registrations": load_registrations()}
