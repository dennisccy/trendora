# goal-mcp-loop-iter-21 Execution Plan

**Verification-only iteration. Zero source-code changes.** Target: flip J-13 `partial → passing`
by producing the canonical browser-qa evidence trail iter-20 was missing. Iter-20's closure
returned **CLOSURE-FAIL** because the canonical `browser-qa-agent` lane blanket-SKIPped (both
services unreachable at precondition — curl `000` on `:3255`/`:8255`), leaving the evidence
directory empty, while the QA report separately self-graded browser-typed cases from *code
inspection*. The underlying J-13 code (548-pool Fetch scope, "Expand universe" removal, two-group
availability legend) is already correct and independently verified — review PASS, audit
PASS_WITH_GAPS ("deliverable correct; gaps are verification-chain only"), coherence PASS, and a
live ux-regression DOM/computed-style spot-check confirmed all three visual criteria. This
iteration only has to prove it against a real running stack and formally re-clear closure.

**Alignment check:** this directly operationalizes iter-20's evaluator recommendation
(`runs/goal-session-mcp-loop/iter-20/eval.md` §Next-Step Recommendation, matched almost verbatim)
and goal.md's own priority rubric (no journey `regressed`; iter-20 coherence was PASS so no
consolidation is owed; completing J-13 is the reachable unblocker toward GOAL_ACHIEVED). No drift
from `docs/goal.md` found. The spec's own OUT OF SCOPE section already excludes the two things
that *would* be drift (fixing the non-blocking `start-frontend.sh` staleness-stamp gap;
re-certifying the sanctioned-partial evidence journeys J-02/06/07/08/09) — nothing else in the
spec asks for anything beyond verification.

**Live-verified at plan-writing time:** current `HEAD=6b0f961` (one commit past the `aac9abc` the
spec names — an intervening "iter-20 showcase artifacts" commit that does not touch these files).
`git diff HEAD` on all 5 J-13 implementation files plus the 4 touched test files is currently
**empty** — the spec's "must stay empty" premise holds right now. (Note: the environment's
initial git-status snapshot for this session showed these files as modified — that snapshot
predates iter-20's own commit and is stale; the live check just now confirms a clean tree.) The
developer's job this iteration is to **keep it that way and prove it**, not establish it from a
dirty state.

## What to Build

Nothing. No feature, fix, or refactor ships. The only outputs are verification artifacts:
- A regenerated `ui-test-plan.md` for iter-21 (ui-test-designer), equivalent in coverage to
  iter-20's 22-case / 14-P1 plan (`reports/phase-goal-mcp-loop-iter-20-ui-test-plan.md`).
- A **real, executed** (not code-inspected) `reports/phase-goal-mcp-loop-iter-21-ui-test-results.md`
  from the canonical `browser-qa-agent` lane, with md5-distinct screenshots landing in
  `reports/qa/goal-mcp-loop-iter-21-evidence/`.
- A reconciled `reports/qa/goal-mcp-loop-iter-21-qa.md` whose Browser-Checks section agrees with
  `ui-test-results.md` on service reachability (no "PASS via code review" while a live check is claimed).
- CLOSURE-PASS, an audit incorporating the ux-regression verdict, and UX-REGRESSION-PASS.
- A no-code dev handoff (`docs/handoffs/goal-mcp-loop-iter-21-dev.md`) recording the re-run outcome.

## Agents Required

- backend-data: no -- no backend implementation. The developer's only job this iteration is
  verification (see "Developer turn" below): confirm `git diff HEAD` stays empty on
  `apps/backend/app/engine/data_manager.py`, re-run the J-13-relevant scoped test files, report
  results. Do NOT touch `data_manager.py`, `compute_availability`, or any engine file.
- frontend-ux: no -- no frontend implementation. Confirm `git diff HEAD` stays empty on
  `app/data/page.tsx`, `components/availability-heatmap.tsx`, `app/globals.css`,
  `tailwind.config.ts`. Do NOT re-touch the Expand removal or the legend/color work — it is
  already correct per iter-20's review + audit + ux-regression passes.

Frontend Present: yes

## Developer turn (no-op build — still required, not skippable)

`dev-phase.sh` always dispatches the developer agent, so this turn must positively confirm the
baseline rather than silently do nothing:
1. `git diff HEAD -- apps/backend/app/engine/data_manager.py apps/frontend/app/data/page.tsx apps/frontend/components/availability-heatmap.tsx apps/frontend/app/globals.css apps/frontend/tailwind.config.ts`
   must print nothing. If it does not, STOP and report — that is a regression this iteration must
   not paper over.
2. Re-run the scoped backend tests: `cd apps/backend && .venv/bin/python -m pytest
   tests/test_data_manager.py tests/test_data_manager_jobs_pipeline.py
   tests/test_data_manager_parallel.py tests/test_seed_loader_pool.py -v` (all four — iter-20's
   actual commit touched all four; confirming all four stay green is a stronger, still-cheap
   guard than the two the spec names as a minimum). Clear `/tmp/pytest-of-*` first if disk is
   tight. Do NOT run the full suite (~10-11h on the 30-year basis; fork-locks the box).
3. Optionally re-confirm `cd apps/frontend && npx tsc --noEmit` is clean (0 errors) — cheap,
   already known-clean, catches silent drift.
4. Do NOT start or leave services running here. `dev-phase.sh` installs its own `cleanup_dev_servers`
   EXIT trap that kills anything bound to the project's ports the moment the developer's turn
   ends, so a service left running here will not survive into the QA/browser-qa stage anyway.
   Service bring-up is the QA/browser-qa stage's own idempotent bootstrap
   (`scripts/automation/lib/common.sh`) — iter-20's implementation summary confirms this division
   of labor ("the routine start-the-app check is performed by the standard QA step... which runs
   after this").
5. Write `docs/handoffs/goal-mcp-loop-iter-21-dev.md` and
   `reports/phase-goal-mcp-loop-iter-21-implementation-summary.md` stating plainly: zero code
   changed, all scoped tests green, diff confirmed empty against HEAD (name the exact SHA).

## Files to Create/Modify

**Source: NONE.** Every file below must show an empty `git diff HEAD` at every gate (dev, review,
QA, audit, closure):
`apps/backend/app/engine/data_manager.py`, `apps/frontend/app/data/page.tsx`,
`apps/frontend/components/availability-heatmap.tsx`, `apps/frontend/app/globals.css`,
`apps/frontend/tailwind.config.ts`.

**Artifacts (created/updated this iteration):**
- `docs/handoffs/goal-mcp-loop-iter-21-dev.md` -- no-code verification handoff
- `reports/phase-goal-mcp-loop-iter-21-implementation-summary.md` -- plain-language "nothing
  changed, re-verified" summary
- `reports/phase-goal-mcp-loop-iter-21-user-visible-changes.md` / `-ui-surface-map.md` --
  ui-impact-analyst; must describe the iter-20 J-13 surfaces (see UI Evolution note — do not
  write "no changes" stubs)
- `reports/phase-goal-mcp-loop-iter-21-ui-test-plan.md` -- ui-test-designer, equivalent to
  iter-20's 22-case / 14-P1 plan
- `reports/phase-goal-mcp-loop-iter-21-ui-test-results.md` +
  `reports/qa/goal-mcp-loop-iter-21-evidence/*.png` -- browser-qa-agent, EXECUTED not code-inspected
- `reports/qa/goal-mcp-loop-iter-21-qa.md` -- QA lane, reconciled with the browser-qa lane on reachability
- `reports/phase-goal-mcp-loop-iter-21-closure-verdict.md` -- target CLOSURE-PASS
- `docs/handoffs/goal-mcp-loop-iter-21-audit.md`, `reports/phase-goal-mcp-loop-iter-21-ux-regression.md`
  -- target PASS / UX-REGRESSION-PASS

## UI Evolution

No new capability, information, action, surface, or nav change ships (the phase spec's own
"Product surface delta: None" is authoritative). **A zero-diff phase must not collapse the UI
chain into stub reports** — the ui-impact-analyst, ui-test-designer, and browser-qa-agent must
treat the ALREADY-COMMITTED iter-20 surfaces as the surfaces-under-test (analyze the `aac9abc`
diff, not iter-21's empty one):
- New user-facing capability: none (already shipped in iter-20; this iteration proves it live).
- New information displayed: none — same `GET /api/data/availability` values, byte-identical.
- New user actions: none (Expand was already removed in iter-20).
- UI surface changes: none — `/data`'s job-kind picker + availability heatmap are the surfaces
  under verification, byte-identical to HEAD.
- Navigation changes: none.

## Visual Requirements (re-verify live, do not redesign)

- Component patterns / layout: unchanged — existing `Card`/`Select` on `/data`, existing
  `AvailabilityHeatmap` card, no new component.
- Key visual facts to reconfirm via computed style (not eyeballing): legend renders as two
  labeled groups ("Price data — cell fill" / "Scored snapshot — indicator"); top density bucket
  computed `background-color` is `rgb(166, 200, 242)` / `#a6c8f2` (not amber `#f0b429`); snapshot
  ring computed color is `rgb(167, 139, 250)` / `#a78bfa` (not green `#34d399`); all 6 density
  steps visibly distinct from their neighbors.
- States to handle: `/data`'s existing loading/empty/error states, including the honest
  "Availability could not load... No cells are shown rather than fabricated values" degrade path
  (UT-16) — confirm unchanged; do not add new states.

## Key Test Scenarios

**Operational preconditions (sequence matters — before any browser case is attempted):**
1. `rm -rf apps/frontend/.next` (dodges the staleness-stamp trap that silently served a stale
   pre-iter-20 bundle last time).
2. `scripts/start-backend.sh` (`:8255`) then `scripts/start-frontend.sh` (`:3255`) — prod mode,
   never `dev.sh`.
3. `curl :8255/health` and `curl :3255` both return 200 (not `000`) before browser-qa-agent is
   dispatched; keep both up for the whole browser-qa run.

**Browser (canonical browser-qa-agent lane, executed live, not code-inspected):**
- J-13 (target): UT-02/03/04/05 (no Expand option; fetch/backfill/both start clean), UT-10/11/12
  (two-group legend; exact colors above), UT-14 (hover distinguishes a backfill-gap day from a
  snapshotted day, naming Fetch/Backfill).
- Required-still-passing replay (closes iter-20's gap): J-01/UT-17 (`/stocks` Sector-sort — the
  iter-18 crash driver, highest-value smoke), J-03/UT-18 ("Not yet proven" badges intact),
  J-05/UT-19 (`/evidence` renders), J-10/UT-20 (deep-history chart), J-12/UT-21 (universe count
  consistent `/methodology` ↔ `/stocks`).
- UT-01 (page loads, no "Backend unavailable" card) and UT-16 (honest degrade on API failure)
  round out anti-goal #8.
- Screenshot hygiene: scroll the legend and both hovered cells into frame; full-page or
  element-clip captures only (a scrolled-viewport capture previously produced ~5855-byte blank
  frames); `md5sum` every PNG so no capture is reused/relabeled across the three J-13 assertions.

**Unit/integration:** the developer-turn checklist above; the reviewer independently re-runs the
same scoped test command per project convention.

**Gate re-runs:** phase-closure (target CLOSURE-PASS, reconciled against the QA report's
Browser-Checks section), audit (incorporates the ux-regression verdict), ux-regression (target
UX-REGRESSION-PASS, not another WARN).

## Risks and Mitigations (carried forward from iter-20's exact failure)

- **Services not actually reachable when browser-qa dispatches**, even though QA's shared
  bootstrap (`scripts/automation/lib/common.sh`) is designed to auto-start and self-heal a stale
  `.next`. Mitigation: treat the manual `rm -rf .next` + explicit curl-confirm as a hard
  precondition regardless of what the automation is expected to do — this exact gap produced last
  iteration's blanket SKIP.
- **QA report re-asserting "PASS via code review" language for browser-typed cases.** Mitigation:
  QA must cite the real `browser-qa-agent` run (by report path/date) for any case requiring a live
  browser, never "code verification," and must not claim reachability that `ui-test-results.md`
  contradicts.
- **A reused/relabeled screenshot standing in for two different assertions.** Mitigation: md5sum
  hygiene (above); a capture must visibly show the two-group legend and the two distinct hover
  states, not a generic `/data` screenshot.
- **Zero-diff phase makes the ui-impact-analyst/ui-test-designer default to "nothing changed"
  stubs**, which would fail phase-closure-auditor's non-vague check exactly like iter-20's
  evidence-emptiness failure did, just one stage earlier. Mitigation: explicit instruction above
  to analyze the iter-20 committed diff (`aac9abc`) as the surfaces-under-test.
- **Reopening or "improving" the J-13 implementation** even if a reviewer notices a polish
  opportunity (e.g., the non-blocking `start-frontend.sh` staleness-stamp gap, audit finding O1).
  Mitigation: file as a follow-up only — any source edit this iteration fails the DoD's
  empty-diff requirement.

## Out of Scope

- Any source-code change (this is the entire point of the iteration).
- Fixing `start-frontend.sh`'s freshness-stamp gap (audit finding O1) — non-blocking follow-up only.
- Re-certifying J-02/J-06/J-07/J-08/J-09 on the 30-year basis (a separate, referee-gated iteration
  per goal.md's Data-basis-change provision).
- J-14 (deep index/macro context), J-15/J-16 (fast-platform perf budgets) — sequenced separately.
- Any `## Evidence Claim`, referee submission, or ledger write.
