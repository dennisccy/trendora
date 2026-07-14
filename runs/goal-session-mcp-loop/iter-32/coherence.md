# Iteration 32 — Coherence Audit

**Iteration:** goal-mcp-loop-iter-32
**Date:** 2026-07-14
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Certification-budget accounting composition (canonical trials/`required_p`/Thresholdout remaining + staging LORD++ next-level, each with spend-over-time) | OK | `apps/backend/app/engine/budget_accounting.py:89-153` composes ONLY over `app.engine.ledger:{count_trials,alpha_spent,rejection_offsets,read_entries}` (imported `apps/backend/app/engine/budget_accounting.py:51-57`), `app.engine.online_fdr:test_level` (`:49`,`:116-123`), and the imported referee constants `DEFAULT_ALPHA_PER_TEST`/`DEFAULT_ALPHA_BUDGET` (`:58`, used at `:101`,`:104`) — no literal `0.05`/`1.0`. Verified byte-identical to the canonical formula `verify_edge` itself uses: `apps/backend/app/mcp/tools.py:509-511` (`prior_trials = ledger_mod.count_trials(...)`; `spent = ledger_mod.alpha_spent(...)`; `remaining = DEFAULT_ALPHA_BUDGET - spent`) matches `budget_accounting.py:94-104` exactly. Served once by `GET /api/research/budget` (`apps/backend/app/api/budget.py:27-33`, `return build_budget_payload()` verbatim — no re-derivation in the route). Single frontend reader: `apps/frontend/app/research/budget/page.tsx:35` calls `fetchBudget()` → `apps/frontend/lib/api.ts:391` `GET /api/research/budget` only; no second fetch path, no client-side recompute (the `Sparkline` component at `page.tsx:174-208` only maps already-fetched numbers to pixel coordinates — pure presentation, not a new statistic). Registered in the SAME change: `runs/goal-session-mcp-loop/state/blueprint.md` Data Contract table gains this exact row and the iter-32 clarification paragraph (blueprint.md diff, new row + trailing paragraph). Backend test suite (`apps/backend/tests/test_budget_accounting.py:52-81`) directly asserts payload equality against the live seams (`test_canonical_single_source_against_live_ledger`, `test_staging_single_source_against_live_ledger`) — the single-source claim is not just asserted in prose, it is pinned by a test. |
| Evidence status / certified-claim, scores, regime, sectors, themes, forward-return evidence, research-lab cohorts, registry, graveyard (all pre-existing contract rows) | OK — untouched | None of these computing modules or endpoints appear in the diff. `certified-claims.jsonl`, `staging-ledger.jsonl`, `pre-registrations.jsonl` are byte-identical (`git status --porcelain` on all three: empty). `apps/frontend/app/research/registry/page.tsx` (the J-19 lineage-scroll `useEffect`) shows no diff against the snapshot SHA — confirmed not reopened. |

No new displayed value appears in this iteration outside the one registered above; no synonym/re-derivation of an existing contract value was introduced.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/research/budget` (new page, J-17) | OK | Blueprint IA homes table gains a J-17 row pointing to exactly this route under "Research (budget page, hub-reached)" (blueprint.md diff). Reachability verified statically: `apps/frontend/components/sidebar.tsx:38` — persistent "Research" link → `/research` (click 1, unchanged); `apps/frontend/app/research/page.tsx:128-150` diff adds a third card (`data-testid="research-governance-link-budget"`) to the EXISTING `data-testid="research-governance"` grid alongside the registry/graveyard cards, linking to `/research/budget` (click 2). ≤2 clicks, matches the established pattern for `/research/registry` (iter-30) and `/research/graveyard` (iter-31). No parallel shell: `apps/frontend/app/research/budget/` contains only `page.tsx` (no local `layout.tsx`); the page imports the shared `PageHeading`/`Card`/`CardContent` components (`page.tsx:7-12`), mirroring `research/graveyard/page.tsx`'s shape as the spec required. Not a duplicate home — this is a genuinely new feature with no prior canonical home. No `blueprint.reapproval-requested` file was created, consistent with the spec's claim that this is additive under the already-approved (iter-30) "Governance & process" grouping — confirmed no such file exists in `runs/goal-session-mcp-loop/state/`. |
| `/research` hub — third governance card | OK | Same diff hunk as above (`apps/frontend/app/research/page.tsx`); grid was already `xl:grid-cols-3` holding 2 cards, now holds 3 — no layout change needed, confirmed by reading the surrounding JSX. |
| J-19 graveyard→registry lineage scroll (re-verification rider, no code change) | OK | `apps/frontend/app/research/registry/page.tsx` has no diff since the snapshot SHA — confirmed the fix is not reopened. QA report (`reports/qa/goal-mcp-loop-iter-32-qa.md:80,93,143`) records TC-10 PASS via the canonical browser-qa lane (scrollY=194 > 0), which is the DoD-named lane this session's lessons require (not a self-check retest) — J-19 flip from partial→passing is properly evidenced. |

No IA-skeleton change: the top-level nav (`sidebar.tsx`) is untouched by this iteration's diff.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- `README.md` gained one line in this diff (the iter-31 "Negative-results graveyard" bullet, apparently a carry-over from a prior showcase step that hadn't landed in README yet), but no bullet describing this iteration's new "Certification-budget accounting" panel was added (`grep -c budget README.md` → 0 hits post-diff). This is a documentation-currency gap in the readme-maintainer's own domain, not a blueprint Information-Architecture or Data-Contract violation — the app's actual nav/data surfaces are fully coherent and correctly registered regardless of README wording. Flagging only so the next readme-maintainer pass picks it up; does not affect this verdict.
- No other advisory issues found: no inconsistent labeling of the budget concept across `/research`, `/research/budget`, the blueprint, and the tests; no formatting drift (percentages/`p`-values use the same `formatPValue` helper already established by the evidence/graveyard pages); the new page's visual shell matches the established Research governance-card pattern exactly.
