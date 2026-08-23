# Iteration Summary — goal-market-compass-iter-11

**Verdict:** REGRESSION
**Iteration type:** goal-full
**Date:** 2026-08-23
**Iteration:** 11

## In plain words

**What you can do now:** See an honest sector label on every stock instead of "Unassigned". See why each next-session candidate was picked, and why others were not. The two trading days lost in the August data incident (11 and 12 August) have their prices back in the history.

**What changed this time:** Behind the scenes, the app fixed the database table that stores each evening's saved briefing record: an old, unused linking rule was removed, and every one of the 24 saved briefings was checked byte-by-byte to prove nothing was lost. A related bug was fixed too — the app used to wrongly claim "everything checks out" for the roughly one-third of older briefings missing some bookkeeping detail; it now honestly says "can't verify this" instead. The repair went slightly further than approved (it also reset a few unused technical defaults on that table), so the team paused this round to get the owner's sign-off before continuing.

**What's next:** Once the owner confirms this round's small extra database change is acceptable, the team will do the big rebuild of the daily summary and "what changed" pages so they use the restored prices — that rebuild is the next step waiting on this decision.

## Headline

Live manifest-table schema repair on production DB; fixed a false "basis available" claim

## Direction

**Signal:** regressing
**Why:** AG-18 (critical) — the owner-authorized manifest-table migration also dropped three column DEFAULTs and reordered one column, beyond its "FK constraint and nothing else" authorization — is unresolved on the live database, which is why iter-11 is scored REGRESSION under the fail-closed anti-goal rule. No journey actually broke (J-01, J-04, J-10 stay `passing`; J-11 advanced within `partial`), and the destructive J-11 Stage C rebuild — the same class of action that lost data in iteration 5 — is correctly held back pending the owner's decision on this scope breach.

**Trend (last 3 iters):**
- Newly passing this iter: none
- Newly passing in last 3 iters total: J-10 (iter-9)
- Regressions in last 3 iters: none (iter-11's REGRESSION verdict stems from an unresolved critical anti-goal violation, AG-18, not a journey status flip)
- Anti-goal violations in last 3 iters: 1 critical, unresolved (AG-18, iter-11)
- Iters with no journey state change: 1 of last 3 (iter-11)

**Latest evaluator reasoning:** The work this iteration set out to do was done, and I checked it myself instead of believing the reports. The manifest table on the real 7.8 GB database no longer carries the link that blocked the big repair, all 24 saved briefing records came through the change with every single value unchanged, and the page code that used to claim "the original basis is intact" for records that never recorded a basis now says "unverifiable" instead. But the one authorised change to that table did more than the owner allowed: besides removing the link, it also dropped three "default value" rules and moved one column into a different position.

## What was done

- Product changes: apps/backend/app/engine/j11_schema_migration.py, apps/backend/scripts/run_j11_stage_b1_manifest_schema_migration.py, apps/backend/app/engine/compass.py, apps/backend/app/engine/j11_maintenance.py, apps/backend/app/models.py, apps/frontend/lib/api.ts, apps/frontend/lib/basis-disclosure-label.ts, apps/frontend/components/compass-manifest-strip.tsx
- Live schema migration removed the `next_session_manifests` table's foreign-key constraint on the production database; all 24 manifest rows verified byte-identical before and after.
- Fixed `basis_disclosure` to fail closed: the 8 of 24 manifests missing recorded generation info now report "unverifiable" instead of a fabricated "available".
- Widened the frontend `CompassBasisDisclosure` status type and extracted a new label/variant helper for the "unverifiable" state — verified by type-check and a node script only, app not booted.
- Audit found the migration went beyond its authorization: it also dropped three column DEFAULT clauses and reordered one column — flagged as an unresolved critical anti-goal violation (AG-18) pending an owner decision.
- Re-verified J-10 against updated goal text (the owner's "CLOSED — residual accepted" note); stays `passing`.
- Ran 94-96 targeted backend tests plus a frontend type-check and node-script test, all passing; maintenance isolation held for the third consecutive iteration (no service boot).
- Browser QA lane was skipped by contract (maintenance isolation); 0 journeys re-verified via browser QA this iteration.

## What's left

- Journey J-07 (The Today page answers the ten-second read) failing
- Journey J-08 (Market page moves over intact and history stays honest) failing
- Owner decision required: the manifest-table migration exceeded its authorized scope (three dropped column defaults, one reordered column) — critical anti-goal violation AG-18 unresolved
- J-11 Stage C (the destructive derived-state rebuild) stays gated until the owner rules on the scope breach above
- Journeys J-02 (What changed since the previous session) and J-03 (Plain-English summary with cited facts) remain `partial` — still computed from the old, pre-repair derived data until J-11's later stages run
- The new "unverifiable" basis badge has never been seen in a running browser — visual confirmation is Stage G's job
- Journey J-09 (The backend fits the host) still misses its memory target (3.44 GB vs 2.5 GB) — open, non-blocking owner question
- This iteration's migration script and evidence files were not yet committed to git as of QA's check (expected to land at the iteration boundary)

## Next step

One decision is needed from the owner before anything else proceeds: the authorized manifest-table migration also dropped three DEFAULT clauses and reordered one column, beyond the "FK constraint and nothing else" authorization (AG-18). Pick one — (a) accept the delta in writing in `docs/goal.md` (no stored value changed, the dropped defaults are never read, practical risk is nil); (b) order a corrective rebuild (a second live-schema write, not recommended — it doubles the risk to restore rules nothing reads); or (c) record it as an accepted deviation (same as (a), in shorter form). After the owner answers, the next iteration is J-11 Stages C-G at full depth, alone — one writer, no web server, no browser tests — clearing both stale derived-data layers, watching AVB's volume-scale caveat, not re-running the exhausted recovery script, and confirming this iteration's migration script and evidence files actually reach version control.

## Assumptions made

- iter-11 · goal-evaluator — Ambiguity: J-10's prior pass was voided by changed goal text on a maintenance-isolated iteration, when no browser lane could run and no screenshot can ever exist for a journey whose walkthrough is waived. We chose: Kept J-10 `passing`, re-stamped with the new hash, using this iteration's own read-only DB queries (585 symbols/day, EA/EQR at zero, price frontier unchanged) as evidence — the changed text is the owner's own acceptance of that exact state, so no promotion occurred. Reversible: yes.
- iter-11 · goal-evaluator — Ambiguity: AG-18 (critical) was breached on the live database and left unresolved, a state both REGRESSION and STALLED could describe. We chose: REGRESSION, since the violated state is materialized on the live 7.8GB database and can't be undone without a second owner authorization, and the very next authorized step is the same class of destructive action that lost data in iteration 5. Reversible: yes.
- iter-11 · goal-decomposer — Ambiguity: Ruling A4 requires the basis-disclosure fail-closed fix to render an honest UI placeholder, while ruling A5 keeps maintenance isolation active (no app boot, no browser QA) for the whole iteration — goal.md doesn't say whether the UI half must land this iteration or can defer to Stage G. We chose: Landed the minimal type/label change now (a type union plus a pure label function), verified only by type-check and a node-script test, with no page render or dev-server boot. Reversible: yes.
- iter-10 · goal-evaluator — Ambiguity: Real progress was made (J-11 unknown -> partial), which reads CONTINUE, but the only ways to unblock the next step are owner decisions and goal.md shuts every other lane until J-11 Stage G passes. We chose: STALLED — the blocker is Stage C's precondition gate, and goal.md itself prescribes stopping and surfacing this as an owner decision. Reversible: yes.
- iter-10 · goal-evaluator — Ambiguity: J-11's Stage B1 precondition was only partly delivered (two of six items false on the live database) — is that `unknown` or `partial`? We chose: `partial`, since a named, contractually-required artifact (the pre-reset inventory) was produced and independently re-verified; `unknown` would have understated real, verified work. Reversible: yes.
- iter-10 · goal-decomposer — Ambiguity: goal.md describes J-11 Stages A-G as one journey with "the unit of work is the whole 11-date set," but that unit is scoped to the destructive phase (Stage C) — it is silent on whether the read-only Stages B/B1/B2 must ship with C-G in the same iteration. We chose: Scoped this iteration to Stages B/B1/B2 only (zero writes to trendora.db), deferring the destructive Stages C-G to a later iteration, mirroring how J-10 itself was safely chunked across iterations. Reversible: yes.
- iter-9 · goal-evaluator — Ambiguity: J-01 and J-04 were already held `passing` while the data beneath them kept moving (20 -> 585 symbols on the recovery dates, and now a genuinely mixed derived basis), but maintenance isolation forbade any lane that could measure the risk. We chose: Kept both `passing`, recording the enlarged mixed-basis risk explicitly rather than inventing an unproven downgrade — there is no positive evidence either journey broke. Reversible: yes.
- iter-9 · goal-evaluator — Ambiguity: The maintenance-isolation carve-out bars promoting a journey to `passing` when browser evidence is absent, but J-10's walkthrough is explicitly waived by goal.md, which names a substitute written-evidence set instead. We chose: Scored J-10 `passing`, since the rail exists to stop promotion on absent evidence and J-10's required evidence was not absent — all four named artifacts existed and were independently re-derived from primary sources. Reversible: yes.

## Quick verify

From `reports/phase-goal-market-compass-iter-11-what-to-click.md`:

1. Open `http://localhost:3255/` in your browser
2. Scroll down to the "Manifest" card and read its top badge row
3. In the same "Manifest" card, click "Versions" to expand it
4. Navigate to `http://localhost:3255/?asof=2026-03-30`
5. Navigate to `http://localhost:3255/?asof=2020-03-20`

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-market-compass-iter-11.md |
| Dev handoff | — | docs/handoffs/goal-market-compass-iter-11-dev.md |
| Review | PASS | reports/reviews/goal-market-compass-iter-11-review.md |
| Browser QA | SKIPPED | reports/phase-goal-market-compass-iter-11-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-market-compass-iter-11-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-market-compass-iter-11-user-visible-changes.md |
| What to click | — | reports/phase-goal-market-compass-iter-11-what-to-click.md |
| UI surface map | — | reports/phase-goal-market-compass-iter-11-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-market-compass-iter-11-ui-test-plan.md |
| QA | PASS | reports/qa/goal-market-compass-iter-11-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-market-compass-iter-11-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-market-compass-iter-11-closure-verdict.md |
| Goal evaluation | REGRESSION | runs/goal-session-market-compass/iter-11/eval.md |
| Journey history | — | runs/goal-session-market-compass/state/journey-history.json |
