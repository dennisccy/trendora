# Iteration Summary — goal-market-compass-iter-27

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-08-28
**Iteration:** 27

## In plain words

**What you can do now:** See each stock's honest, mostly-complete sector label. See why each next-session candidate was picked, and why others weren't. Trust that each evening's saved briefing exactly matches what's on screen and never changes once saved — and now the app will honestly say if the data behind an old saved briefing has gone missing, instead of quietly rebuilding it. Browse the two recovered trading days with corrected numbers, and trust the repair work behind them has been checked live.

**What changed this time:** The Today page's Manifest card can now show a red "Basis: unavailable" badge when a saved briefing's underlying data run has been deleted — before, the app would quietly rebuild that data behind the scenes and never let you know it had ever gone missing.

**What's next:** Next, work begins on the Today page's main view — the "ten-second read" — followed by rebuilding the Market page.

## Headline

J-06 closes: frozen manifests now honestly show "Basis: unavailable" when their source run is gone

## Direction

**Signal:** improving
**Why:** J-06 "A frozen manifest never changes" moved from partial to passing this iteration, closing its last unmet acceptance limb via a route reorder that makes `basis.status == "unavailable"` reachable through the live serving path for the first time — proven by a genuine HEAD-vs-working-tree red→green flip on the removal test, plus 97 passing backend tests. The scoreboard now stands at 6 passing / 3 partial / 2 failing, with one new MINOR anti-goal violation (an out-of-scope browser-QA request that minted manifest row 26 — benign, but left a stale row count in three reports until the auditor corrected it) and two J-06 residuals written down rather than hidden. Full depth ran as the spec required, and the independent auditor again caught real gaps (TC-5/TC-9 marked PASS with no asserting test; the stale row count) that four earlier lanes missed.

**Trend (last 3 iters):**
- Newly passing this iter: J-06
- Newly passing in last 3 iters total: J-05 (iter-26), J-06 (iter-27)
- Regressions in last 3 iters: none
- Anti-goal violations in last 3 iters: 1 minor (iter-27, resolved; none in iter-25 or iter-26)
- Iters with no journey state change: 1 of 3 (iter-25)

**Latest evaluator reasoning:** "The one job asked for was done, and it works. Before this round, a saved briefing whose source run had been deleted could never say so: opening the page quietly rebuilt the missing run first, so the screen could only ever say 'available' or 'rebuilt'. Now the page checks whether a saved briefing exists first, and serves it without rebuilding anything — so it can honestly say 'Basis: unavailable'."

## What was done

- Product changes: apps/backend/app/api/compass.py (GET /api/compass route reorder), apps/backend/app/engine/compass.py (new `latest_manifest_for_date` helper), apps/backend/tests/test_api_compass.py
- Today page's manifest strip can now show "Basis: unavailable" for a frozen briefing whose source scan run was removed, instead of silently rebuilding it and hiding the gap.
- Reordered `GET /api/compass` to check for an existing manifest before ever calling the self-heal path (`resolved_run`/`run_scan`), so a removed source run stays removed; added the pure-read helper `latest_manifest_for_date`, shared by both callers.
- Flipped the route-level test from asserting the bug to asserting the fix, and added restore-path plus warm-path regression tests (93 → 97 backend tests passing after the auditor's additions).
- Auditor added 4 more tests closing two definition-of-done gaps (TC-5, TC-9) that two lanes had reported PASS while no test actually asserted them.
- Verified zero writes on the canonical database for the two authorized live checks (2025-04-15, 2026-08-12) by driving the real route over a genuinely read-only DB connection.
- Verified 6 target/required-still-passing journeys (J-01, J-04, J-05, J-06, J-10, J-11) pass via browser QA (12/12 UI checks) and the deterministic replay lane (5/5).

## What's left

- Journey J-07 "The Today page answers the ten-second read" — failing, not started.
- Journey J-08 "Market page moves over intact and history stays honest" — failing, not started (`/market` route returns 404).
- Journeys J-02 "What changed since the previous session" and J-03 "Plain-English summary with cited facts" remain partial; not targeted this iteration.
- Journey J-09 "The backend fits the host" remains partial — memory measured at ~2.99 GB against a ≤2.5 GB target, figure still uncorroborated (open, non-blocking owner question).
- The new "Basis: unavailable" badge cannot be exercised live yet — no as-of date in the current database triggers it; proven only by an automated backend test, not a browser walkthrough.
- Process gap: an out-of-scope browser-QA request permanently added a 26th manifest row to the protected database (benign, correctly classified, but three reports quoted the stale count of 25 until the auditor corrected it).
- J-06's "unavailable" state is proven only at the fixture/route level, never through the real remove-data action; and a pre-existing gap (audit finding B3) means removing a frontier manifest's own price range makes it unreadable behind an HTTP 400 instead of serving it.
- J-04's screenshot re-take (still owed, ninth round running) and the J-05/J-06 walkthrough recordings remain outstanding.

## Next step

Build J-07 "The Today page answers the ten-second read" next — the goal file's own next item now that J-06 is closed — then J-08 "Market page moves over intact." Run it at full depth: J-07 is the main page, its acceptance requires every on-screen number to match stored values and a strict separation between system and market words, and this round is fresh proof the independent auditor lane is load-bearing. Only the owner can add `Depth enforcement: required` to guarantee full depth rather than merely request it. One process fix for the next plan: state that the browsing lane may visit only the dates the plan lists whenever the real database is in use — this round it chose its own extra date and left a permanent row.

## Assumptions made

- iter-27 · goal-evaluator — Ambiguity: audit finding B3 shows J-06 step 2's "never a 404" promise holds only while the as-of still resolves; removing a FRONTIER manifest's price range moves `latest_data_date` behind its as-of, so `resolve_as_of_date` raises `future` → HTTP 400 and the intact frozen row becomes unreadable. We chose: record B3 as an honest residual and promote J-06 anyway — pre-existing, unchanged by this iteration, narrowed by `remove_data`'s seed-safety, and closing it would require a larger out-of-scope reorder. Reversible: yes.
- iter-27 · goal-evaluator — Ambiguity: J-06 step 2's literal `remove_data()` call was never executed against any database in this scoping (canonical DB deletion unauthorized; the fixture test deletes rows by SQL instead) — unclear whether a route-level fixture reproduction of the post-removal state satisfies a step written in terms of the removal action. We chose: promote J-06 to passing, scoring step 2 from the route-level fixture proof (the spec's own Definition of Done authorizes it, and the auditor confirmed the fixture faithfully reproduces what `remove_data` leaves behind) plus live evidence for steps 3-4. Reversible: yes.
- iter-26 · goal-evaluator — Ambiguity: the confirm-gated "regenerate" action minted a permanent version-2 manifest row on the canonical database; unclear whether a permanent additive row counts as "ordinary non-destructive work" (no owner approval needed) or a "genuinely irreversible" act (owner approval required). We chose: read it as authorized — nothing was mutated or deleted, AG-12 names new version rows as the sanctioned correction mechanism, and J-06 step 4 explicitly instructs triggering this action. Reversible: no for the row itself (permanent by design); yes for the policy.
- iter-26 · goal-evaluator — Ambiguity: J-05 step 2 requires a specific frozen-at-ingest database state that can never be observed live again — the only date that could show it was regenerated during incident recovery and is now correctly ineligible. We chose: promote J-05 to passing, scoring step 2 from route-level fixture evidence and steps 3-5 from live evidence re-derived independently, since holding the journey open on a permanently unprovable limb would be an unsatisfiable loop. Reversible: yes.
- iter-26 · goal-decomposer — Ambiguity: J-05/J-06's literal live remove+backfill drill targets "the last two trading days," which still resolves to 2026-08-11/08-12 — the exact pair whose removal caused this session's core incident, and whose AG-9 recovery exception is now exhausted. We chose: route the drill to the existing isolated fixture suite instead of the canonical database, and use only safe, additive, already-shipped live actions for real browser-QA evidence. Reversible: yes for the scoping choice; the one non-reversible piece is the permanent version-2 row minted by the live "regenerate" call used for evidence.
- iter-25 · goal-evaluator — Ambiguity: a machine-level flag says an iteration must never show a clean headline while a target journey has no browser test row, but J-09's own acceptance text says its walkthrough is deliberately waived and replaced by a dated memory measurement — the two point opposite ways. We chose: treat the goal's own waiver as authoritative and score J-09 from the measurement evidence rather than as unknown; the practical stake is low since J-09 stays partial either way. Reversible: yes.

## Quick verify

From `reports/phase-goal-market-compass-iter-27-what-to-click.md`:

1. Open `http://localhost:3255/?asof=2025-04-15` in your browser
2. Inside the Manifest card, find the badge row just below the small hash chips (labeled "Engine identity", "Candidate rule", etc.)
3. Open `http://localhost:3255/?asof=2026-08-12` in your browser
4. Find the same badge row inside the Manifest card
5. On this same page, click the outlined amber "Regenerate manifest" button (with a circular-arrow icon) near the bottom of the Manifest card

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-market-compass-iter-27.md |
| Dev handoff | — | docs/handoffs/goal-market-compass-iter-27-dev.md |
| Review | PASS | reports/reviews/goal-market-compass-iter-27-review.md |
| Browser QA | PASS | reports/phase-goal-market-compass-iter-27-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-market-compass-iter-27-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-market-compass-iter-27-user-visible-changes.md |
| What to click | — | reports/phase-goal-market-compass-iter-27-what-to-click.md |
| UI surface map | — | reports/phase-goal-market-compass-iter-27-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-market-compass-iter-27-ui-test-plan.md |
| UX regression | UX-REGRESSION-PASS | reports/phase-goal-market-compass-iter-27-ux-regression.md |
| QA | PASS | reports/qa/goal-market-compass-iter-27-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-market-compass-iter-27-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-market-compass-iter-27-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-market-compass/iter-27/eval.md |
| Journey history | — | runs/goal-session-market-compass/state/journey-history.json |
