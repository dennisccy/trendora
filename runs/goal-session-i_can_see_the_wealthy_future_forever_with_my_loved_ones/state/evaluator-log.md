
## Iteration 0 — goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-0

**Date:** 2026-06-11T08:41:43+01:00
**Verdict:** CONTINUE
**Depth dispatched:** lean
**Journey deltas:**
- Newly passing: none (baseline) — 38 journeys recorded `already_passing` (J-01..J-21, J-25..J-41)
- Newly failing: J-43, J-44, J-45, J-46, J-47 (new must-haves, not yet built); J-42 `partial` (displayed dates ISO, but /data uses native type="date" inputs and no shared formatter — QA's PASS downgraded per dev source-scan)
- Regressed: none
- Blocked-NA (non-halting per goal.md): J-22, J-23, J-24 (`unknown` + note)
- Anti-goal violations: none (verify-only iteration; empty product diff)

**Reasoning:** Baseline matches the iter spec's predicted outcome exactly. Product code is identical to prior-session GOAL_ACHIEVED commit 8c566d8; this iteration's captures directly evidence the strongest legs (Risk-Off gating run 2026-03-31 Actionable=0; full Backtest page with attribution/cohorts/control-groups/honest-NA; through-latest chart with display-only labeling; Factor Lab decile+IC; coverage table). The browser-QA report's table is unreliable — ~20 journey rows describe invented journeys (J-22/23/24 as "broker/orders/portfolio") and several evidence files are byte-identical copies or mislabeled (UT-J-17 is the Research page; real DM/VCP captures sit in stray reports/qa/goal-iter-0-evidence/) — so every verdict was re-derived from raw screenshots + the dev source-scan. No coherence audit exists (no diff); no veto. DoD gap: the full pytest suite was never executed (collect-only 626/0); owed in iter-1.

**Next-step recommendation:** Iter-1 lean: build J-42 (shared yyyy-MM-dd formatter + validated ISO text inputs on /data) + J-43 (?asof URL serialization restored through the one global control; invalid → latest), run the full pytest suite once, re-verify J-06/J-13/J-18 on the touched surface. Then J-44+J-45 (shared stored-regime-history + server-side index-series endpoints), then J-47, then J-46. Tell browser-qa to use goal.md journey text verbatim and capture fresh per-journey screenshots.

## Iteration 1 — goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-1

**Date:** 2026-06-11T10:55:47+01:00
**Verdict:** CONTINUE
**Depth dispatched:** lean
**Journey deltas:**
- Newly passing: J-42 (shared formatter `lib/dates.ts` + validated ISO text inputs on /data, browser-verified error states + blocked submit)
- Improved: J-43 failing → partial (interactive `?asof` serialization, invalid-param degradation, and restore-into-control all work; URL stripped after deep-link hydration / reload / fresh tab — browser-QA FAIL on those legs)
- Re-verified passing: J-06 (MRVL numeric leaderboard↔detail match at historical date), J-13, J-17 (real backfill job via the new text inputs), J-18, J-20
- Newly failing: none
- Regressed: none
- Anti-goal violations: none (frontend-only diff; asof-provider sole `?asof` owner; contracts unchanged; coherence COHERENCE-PASS)
- Suite: baseline's full-pytest debt paid — 622 passed / 4 skipped / 0 failed (36m39s)

**Reasoning:** Target J-42 has positive fresh evidence on every acceptance leg (tooltip leg accepted via the single `localization.timeFormatter → formatIsoDate` hook — canvas hover not automatable). Target J-43 fails its reload/fresh-tab acceptance with a confirmed root cause in `asof-provider.tsx`: the serialize effect omits `searchParams` from its deps, so the restore-path strip wins and re-serialization never fires. Required-still-passing set is fully green with per-journey screenshots I inspected directly. Clear progress, one tractable, root-caused defect remaining → CONTINUE, lean.

**Next-step recommendation:** Iter-2 lean: fix the J-43 serialize-effect stale-`searchParams` dependency and re-QA reload/fresh-tab/click-through; small enough to bundle with starting J-44+J-45 (stored regime-history + server-side index-series endpoints). Flip J-42's blueprint annotation to built; keep J-43 as TARGET. Drop the `npm run lint` DoD — ESLint is not installed; `tsc --noEmit` is the frontend gate.
