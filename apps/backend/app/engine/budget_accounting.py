"""The certification-budget accounting panel — the read-side composition of the referee's own
multiple-testing accounting (goal-mcp-loop iter-32, J-17 / backlog B-903).

This module answers "how much statistical-credibility budget has already been spent, before any new
scan is proposed" by RE-READING the exact seams `app.mcp.tools:verify_edge` already uses. It computes
NO canonical value independently (B-903's named failure mode is "UI-recompute" — a parallel bookkeeping
path that could silently disagree with the referee's own accounting):

  - **Canonical** (`app.engine.ledger` + `app.engine.referee`, strict Bonferroni, ALWAYS): trials to
    date = `ledger.count_trials(canonical_path)` (display value, kept SEPARATE from the forward-looking
    ordinal below — never conflated); the forward next-trial ordinal `n_trials_next` = that count + 1;
    the current bar `required_p = referee.DEFAULT_ALPHA_PER_TEST / n_trials_next` — the EXACT value the
    next `verify_edge` call would compute (the constant is IMPORTED, never a `0.05` literal here).
    Thresholdout budget remaining = `referee.DEFAULT_ALPHA_BUDGET - ledger.alpha_spent(canonical_path)`
    (byte-identical to the `remaining` `verify_edge` computes at `tools.py:511`).
  - **Staging** (`app.engine.online_fdr`, LORD++): the same `n_trials_next` shape, and the next-trial
    significance level (the "alpha-wealth" B-903 asks to surface) via `online_fdr.test_level(n_trials_
    next, ledger.rejection_offsets(staging_path), alpha=cfg.evidence.fdr.alpha, w0_fraction=cfg.evidence.
    fdr.w0_fraction, gamma_exponent=cfg.evidence.fdr.gamma_exponent, gamma_terms=cfg.evidence.fdr.
    gamma_terms)` — the IDENTICAL call `verify_edge` makes for a staging claim (config-sourced tunables
    only, no literal).
  - **Spend-over-time** (per ledger): every ORIGINAL entry (forward-walk monitoring records excluded,
    the SAME exclusion `app.engine.graveyard` / `app.engine.evidence` already use), in append order,
    re-displaying its OWN recorded `verdict.required_p` verbatim (both ledgers — the Bonferroni bar or
    the LORD++ level THAT trial was actually judged at) plus `verdict.deflation_divisor` /
    `verdict.alpha_charged` (canonical only — under LORD++ `deflation_divisor` just mirrors the trial
    ordinal, not a meaningful divisor, so the staging series omits it). History is READ, never
    recomputed; only the two forward next-trial figures above call a live function.

Ledger paths come ONLY from the existing resolvers — `app.engine.evidence.resolve_ledger_path()`
(canonical) and `app.engine.graveyard.resolve_staging_ledger_path()` (staging, REUSED rather than
duplicated, per that module's own docstring). A missing/empty ledger degrades to an honest zero/empty
snapshot (0 trials, `required_p = 0.05/1`, the full starting alpha budget, the staging economy's
initial wealth) — never a raise; the formulas above naturally produce this on an empty ledger (`count_
trials` / `alpha_spent` / `rejection_offsets` all return the empty-file default), so no special-casing
is needed.

READ-ONLY, always: this module writes nothing, and never touches `app.engine.referee.certify_edge`,
`app.mcp.tools.verify_edge`, or either ledger's write path. It carries no proven-language — trial
counts and alpha figures are descriptive accounting, never a "Proven"/"Not yet proven" signal (that
stays the exclusive province of `app.engine.evidence` / `GET /api/evidence`, untouched here).
"""
from __future__ import annotations

from typing import Any

from app.config import get_config
from app.engine import evidence as evidence_mod
from app.engine import online_fdr
from app.engine.graveyard import resolve_staging_ledger_path
from app.engine.ledger import (
    FORWARD_WALK_TYPE,
    alpha_spent,
    count_trials,
    read_entries,
    rejection_offsets,
)
from app.engine.referee import DEFAULT_ALPHA_BUDGET, DEFAULT_ALPHA_PER_TEST


def _spend_over_time(ledger_path: str, *, staging: bool) -> list[dict]:
    """Every ORIGINAL (non-forward-walk) entry in `ledger_path`, in append order, projected into one
    spend-over-time point. `required_p` is re-read VERBATIM from the entry's OWN recorded verdict on
    BOTH ledgers (canonical: the Bonferroni bar that trial was judged at; staging: the LORD++ level
    that trial was judged at). `deflation_divisor` / `alpha_charged` ride along for the canonical series
    only. Nothing is recomputed — every value is exactly what the referee wrote at the time of that
    trial; `trial`/`register_date`/`status` are the minimal context a "spend-over-time" series needs to
    plot (an ordinal + its date + its outcome), not a derived statistic."""
    rows: list[dict] = []
    ordinal = 0
    for entry in read_entries(ledger_path):
        if not isinstance(entry, dict) or entry.get("type") == FORWARD_WALK_TYPE:
            continue
        ordinal += 1
        verdict = entry.get("verdict") if isinstance(entry.get("verdict"), dict) else {}
        point: dict[str, Any] = {
            "trial": ordinal,
            "register_date": entry.get("register_date"),
            "status": verdict.get("status"),
            "required_p": verdict.get("required_p"),
        }
        if not staging:
            point["deflation_divisor"] = verdict.get("deflation_divisor")
            point["alpha_charged"] = verdict.get("alpha_charged")
        rows.append(point)
    return rows


def _canonical_section(canonical_path: str) -> dict:
    """The canonical (strict-Bonferroni) accounting: trials to date, the forward next-trial bar, the
    Thresholdout budget remaining, and its spend-over-time series. `required_p` / `alpha_budget_
    remaining` use ONLY the imported referee constants + the `ledger` seams — the exact formulas
    `verify_edge` runs for the next real canonical claim."""
    n_trials_to_date = count_trials(canonical_path)
    n_trials_next = n_trials_to_date + 1
    spent = alpha_spent(canonical_path)
    return {
        "n_trials_to_date": n_trials_to_date,
        "n_trials_next": n_trials_next,
        "alpha_per_test": DEFAULT_ALPHA_PER_TEST,
        "required_p": DEFAULT_ALPHA_PER_TEST / n_trials_next,
        "alpha_budget_total": DEFAULT_ALPHA_BUDGET,
        "alpha_spent": spent,
        "alpha_budget_remaining": DEFAULT_ALPHA_BUDGET - spent,
        "spend_over_time": _spend_over_time(canonical_path, staging=False),
    }


def _staging_section(staging_path: str, fdr_cfg: Any) -> dict:
    """The staging (LORD++) accounting: trials to date, the forward next-trial significance level (the
    "alpha-wealth" figure B-903 asks to surface), and its spend-over-time series. `next_level` calls the
    SAME `online_fdr.test_level` seam `verify_edge` uses for a staging claim, with config-sourced
    tunables only (`cfg.evidence.fdr`) — this module names no LORD++ parameter as a literal."""
    n_trials_to_date = count_trials(staging_path)
    n_trials_next = n_trials_to_date + 1
    next_level = online_fdr.test_level(
        n_trials_next,
        rejection_offsets(staging_path),
        alpha=fdr_cfg.alpha,
        w0_fraction=fdr_cfg.w0_fraction,
        gamma_exponent=fdr_cfg.gamma_exponent,
        gamma_terms=fdr_cfg.gamma_terms,
    )
    return {
        "n_trials_to_date": n_trials_to_date,
        "n_trials_next": n_trials_next,
        "next_level": next_level,
        "spend_over_time": _spend_over_time(staging_path, staging=True),
    }


def build_budget_payload(canonical_path: str | None = None, staging_path: str | None = None) -> dict:
    """Compose the read-only `/api/research/budget` payload: `{"canonical": {...}, "staging": {...}}`.
    `canonical_path` defaults to `app.engine.evidence.resolve_ledger_path()`; `staging_path` defaults to
    `app.engine.graveyard.resolve_staging_ledger_path()` — the endpoint's real, no-argument call shape.
    A test may pass explicit fixture paths instead (mirrors `app.engine.graveyard.build_graveyard_
    payload`'s optional-path pattern).

    RECOMPUTES NOTHING: every figure is either read verbatim from a recorded verdict, or produced by
    calling the SAME `ledger` / `online_fdr` / `referee` seams `app.mcp.tools.verify_edge` calls for the
    next real claim. A missing/empty ledger (either or both) degrades to the honest empty-ledger values
    the formulas naturally produce (0 trials, `required_p = alpha_per_test / 1`, the full starting
    budget, the staging economy's initial wealth) — never a crash (anti-goal: resilience to data-shape
    change)."""
    resolved_canonical = (
        canonical_path if canonical_path is not None else evidence_mod.resolve_ledger_path()
    )
    resolved_staging = staging_path if staging_path is not None else resolve_staging_ledger_path()
    fdr_cfg = get_config().evidence.fdr
    return {
        "canonical": _canonical_section(resolved_canonical),
        "staging": _staging_section(resolved_staging, fdr_cfg),
    }
