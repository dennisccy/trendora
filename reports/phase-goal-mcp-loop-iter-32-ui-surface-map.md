# Phase goal-mcp-loop-iter-32 — UI Surface Map

**Phase:** goal-mcp-loop-iter-32 (goal mode, journey J-17 / backlog B-903, + J-19 close-out)
**Date:** 2026-07-14
**Written by:** ui-impact-analyst

---

## File Classification

Per `.claude/skills/diff-to-ui-impact.md`, applied to every file listed in the dev handoff's "Files Changed" section (verified against the actual diffs, not paraphrased):

| File | Category | UI Impact | Explanation |
|------|----------|-----------|-------------|
| `apps/backend/app/engine/budget_accounting.py` (NEW) | backend-internal | indirect | Pure read-compose module (`build_budget_payload`, `_canonical_section`, `_staging_section`, `_spend_over_time`). No DB/session, no direct UI coupling itself — it is the sole data source for the endpoint below. |
| `apps/backend/app/api/budget.py` (NEW) | backend-api | indirect — confirmed consumed | New `GET /api/research/budget`. Confirmed consumed: `apps/frontend/lib/api.ts` calls it via `fetchBudget()`, rendered by `/research/budget` (grepped — no other consumer exists). Surface is affected. |
| `apps/backend/main.py` (router wiring, +2 lines) | backend-internal (wiring) | indirect | Registers `budget.router` (`import budget` + `include_router(budget.router, prefix="/api")`). No UI surface of its own; enables the endpoint above to be reachable. |
| `apps/backend/tests/test_budget_accounting.py` (NEW) | tests | none | Test coverage only (20 tests per dev handoff). |
| `apps/backend/tests/test_api_budget.py` (NEW) | tests | none | Test coverage only (4 tests per dev handoff). |
| `apps/frontend/lib/budget.ts` (NEW) | frontend-direct (data/types layer) | indirect | `BudgetSpendPoint` / `CanonicalBudget` / `StagingBudget` / `BudgetResponse` types only. No rendering of its own; consumed by the new page. |
| `apps/frontend/lib/api.ts` (modified) | frontend-direct (data layer) | indirect | Adds `fetchBudget()` + re-exports the budget types — the fetch call the new page uses. |
| `apps/frontend/app/research/budget/page.tsx` (NEW) | frontend-direct | direct | New page — the entire four-card accounting panel, sparklines, and loading/error states. |
| `apps/frontend/app/research/page.tsx` (modified) | frontend-direct | direct | Existing hub page — third card added to the "Governance & process" grid; section header comment updated (code comment only, not user-visible). |

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/research/budget` | `BudgetPage` root — three-state shell (loading / error / ok) | New page | Ships J-17 (backlog B-903): exposes the platform's statistical-credibility budget spend before any new scan is proposed | Navigate to `/research/budget` directly (or via the Research hub card). Confirm a brief loading skeleton (`data-testid="budget-skeleton"`, 4 placeholder cards) appears, then is replaced by the four-card grid (`data-testid="budget-grid"`) — never a blank page or unhandled error. |
| `/research/budget` | "Total trials to date" card (`data-testid="budget-trials"`) | New component | Surfaces the canonical trial count that drives the Bonferroni divisor | Confirm the headline value (`data-testid="budget-trials-value"`) reads `7` and the subtext reads "Next canonical trial will be #8" — both must equal `GET /api/research/budget`'s `canonical.n_trials_to_date` (7) and `canonical.n_trials_next` (8) fields exactly. |
| `/research/budget` | "Current canonical required p" card (`data-testid="budget-required-p"`) | New component | Surfaces the live significance bar the next canonical trial must clear | Confirm the headline value (`data-testid="budget-required-p-value"`) reads `0.00625` and the subtext reads "= 0.05 ÷ 8 (Bonferroni)" — cross-check against the API response's `canonical.required_p` (0.00625), `canonical.alpha_per_test` (0.05), and `canonical.n_trials_next` (8). |
| `/research/budget` | "Thresholdout budget remaining" card (`data-testid="budget-thresholdout-remaining"`) | New component | Surfaces the reusable-holdout alpha budget remaining before it is fully spent | Confirm the headline value (`data-testid="budget-thresholdout-remaining-value"`) reads `0.9` and the subtext reads "of 1 total · spent 0.1" — cross-check against `canonical.alpha_budget_remaining` (0.9), `alpha_budget_total` (1), and `alpha_spent` (0.1) in the API response. |
| `/research/budget` | "Staging LORD++ next-trial level" card (`data-testid="budget-staging-wealth"`) | New component | Surfaces the internal staging exploration economy's next-trial significance level — never shown anywhere in the product before this iteration | Confirm the headline value (`data-testid="budget-staging-wealth-value"`) matches `staging.next_level` from the API response (≈0.0003926) and the subtext reads "trial #8 of the internal staging economy", matching `staging.n_trials_next`. |
| `/research/budget` | Spend-over-time sparklines (`data-testid="budget-sparkline"`, one per card) | New feature | Shows each figure's per-trial trend, re-read verbatim from recorded verdicts, never recomputed | On each of the 4 cards, confirm an inline SVG polyline with 7 plotted points renders (both live ledgers hold 7 trials today) and none show the empty-state text "No trials yet" (`data-testid="budget-sparkline-empty"`). On the Thresholdout card specifically, confirm its sparkline (built from `alpha_charged`, a spend-EVENT series, not a running total) shows exactly 2 non-zero points among the 7 (the two trials that actually charged alpha 0.05 each), not a smoothly declining line. |
| `/research/budget` | Error state (`Card` with "Backend unavailable" text) | New feature | Graceful degrade when the API is unreachable (anti-goal: never a blank crash on availability change) | Stop the backend service and reload `/research/budget`. Confirm a red-bordered card reading "Backend unavailable" appears in place of the grid, the "Back to Research" link at the top remains clickable, and no blank/crashed application-error page appears. |
| `/research/budget` | Proven-language absence (whole-page text) | Anti-goal compliance (no new UI element) | Anti-goal #1 forbids any "Proven"/"Not yet proven" signal outside the certified-claim evidence flow; this page is descriptive accounting only | View the rendered `/research/budget` page (page heading, subtitle, all 4 card titles/subtexts) and confirm the strings "Proven" and "not yet proven" do not appear anywhere. |
| `/research` | Governance & process grid — new "Certification-budget accounting" card (`data-testid="research-governance-link-budget"`) | Added navigation | Discoverability entry point for the new budget panel, reachable in ≤2 clicks from the Research hub | On `/research`, confirm a third card titled "Certification-budget accounting" (Wallet icon) appears in the `data-testid="research-governance"` grid, after "Pre-registration registry" and "Negative-results graveyard" (the grid is now 3/3 full). Click it and confirm the browser navigates to `/research/budget`. |

---

## Re-Verification Only — No Code Change This Iteration

This journey is listed separately because the phase Definition of Done requires it to be re-verified against the current build, **not** because anything changed in the code this iteration. `git log` confirms no commit against either file below since iter-30/31, and neither appears in this iteration's dev-handoff "Files Changed" list.

| Route / Page | Component / Element | Change Type | Why Flagged | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/research/graveyard` → `/research/registry` | Lineage link (`data-testid="graveyard-lineage-link"`) → target row anchor (`id="registration-<id>"`) | No change (re-verification only) | J-19 has been `partial` in journey-history since iter-31; this iteration's DoD requires a **canonical browser-qa-agent** run against the FINAL iter-32 build (not a self-check or `qa.md` retest, per the iter-31/22/20/13 lessons) before it can flip to `passing`. The underlying `useEffect` fix (`apps/frontend/app/research/registry/page.tsx:50-59`) is confirmed present and unmodified. | From `/research/graveyard`, click a row's Lineage link. Confirm the browser navigates to `/research/registry#registration-<id>` AND that `window.scrollY > 0` immediately after navigation completes (the target row is scrolled into view beneath the sticky header — not left at the page top). |

---

## Backend-Only Changes (No UI Impact)

These have no UI surface of their own; each is a supporting dependency of the `/research/budget` surface above and is fully realized through it — none is an unwired "not visible yet" capability.

- `apps/backend/app/engine/budget_accounting.py` (NEW) — `build_budget_payload()` and its `_canonical_section`/`_staging_section`/`_spend_over_time` helpers. Pure read-compose logic re-reading the `ledger`/`online_fdr`/`referee` seams `verify_edge` already uses; no DB session, no rendering. Feeds `GET /api/research/budget` exclusively.
- `apps/backend/main.py` — two-line additive router registration (`budget` import + `include_router(budget.router, prefix="/api")`). No UI surface itself; makes the endpoint above reachable.
- `apps/backend/tests/test_budget_accounting.py`, `apps/backend/tests/test_api_budget.py` — test coverage only (24 tests total per dev handoff). No UI impact.

---

## Summary

- **Frontend surfaces changed:** 2 (`/research/budget` new; `/research` hub modified)
- **New pages/routes:** 1 (`/research/budget`)
- **Modified components:** 1 visible (`/research` governance card) + 2 non-visual supporting data-layer files (`lib/budget.ts` new, `lib/api.ts` extended — no independent UI surface)
- **Navigation changes:** yes — new card added to `/research`'s existing "Governance & process" grid (now 3/3 full); no change to the persistent top-level nav
- **Backend-only changes:** 3 (engine composition module, `main.py` router wiring, 2 test files)
- **Re-verification-only items (no code change):** 1 (J-19 graveyard→registry lineage scroll)
