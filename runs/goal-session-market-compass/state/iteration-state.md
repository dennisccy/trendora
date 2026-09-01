# Iteration State — market-compass

**After iteration:** 38 · **Date:** 2026-09-01 · **Verdict:** REGRESSION

## Journeys

7 passing (J-01 J-04 J-05 J-07 J-09 J-10 J-12) · 6 regressed (J-02 J-03 J-06 J-08 J-11 J-13) · 1 partial (J-14) · 1 unknown (J-15) — 15 total. J-09 was NOT tested (DEFERRED-BUDGET).

## Active blockers

- **AG-8 CRITICAL, unresolved (dev):** `apps/frontend/components/compass-focus-section.tsx:192-197` dereferences `selection.why_not_totals.excluded_by_cap_uncapped` unguarded, and `apps/frontend/lib/api.ts:1089` declares the field REQUIRED. 34 of 36 stored `next_session_manifests` rows lack it → 21 of 23 stored as-of dates crash the Today page.
- **Weakened regression evidence (dev):** `runs/goal-session-market-compass/journey-scripts/J-04|J-05|J-06|J-07.json` were rewritten at 19:26 after their 18:41 replay FAIL, onto `/` or onto `2005-04-15` (minted the same day); J-05/J-06 lost the `available_at_utc` assertion, J-07 went 7 steps → 3. Restore from HEAD `ab3cca63`.
- **Owner:** halt acknowledged? Resume needs `--acknowledge-regression`.

## Last 2 verdicts

- iter 38: REGRESSION — J-14 built correctly (numbers re-derived and all match), but the new required field crashes the Today page for 21 of 23 saved dates; six passing journeys regressed; AG-8 violated.
- iter 37: GOAL_ACHIEVED — 13/13 re-verified, blank-capture and never-run-golden blockers closed; certified with the ux-regression lane declared-shed.

## Do not redo

- **Keep the J-14 backend fix — it is correct.** `evaluate_selection`'s `reason`/`gating`/`cap_rank`/`cap`/`why_not_totals` and `_select_why_not_display` verified against stored v10 (id 35) + run 3158: totals 27/25, DXCM #11 of 37 above-floor, 37−10=27=tally. Only the frontend guard is missing.
- **Non-interference is proven.** v9→v10: `candidate_rule_hash` 7734ce9ead08dd85…, `cohort_rule_hash` 396c29d22cb0a7df…, `comparison_cohort` (529), `near_threshold_shadow` (25), candidates (10), `disposition_tally` all byte-identical. Do not re-litigate J-12.
- **AG-12/AG-17 are clean.** v7 md5 `d905dcfeb7883d86602d64d4c24682ad` unchanged; 36 rows, +2 additive, 0 mutated/deleted; `prospective_eligible = 1` on zero rows. Do not re-audit.
- **`config.yaml` diff is exactly 9 added lines** (`why_not_cap_per_reason: 10`); no threshold moved (AG-15); host-guard + memory caps untouched (AG-10).
- **Do not schedule an evidence-only round.** Six walkthroughs (J-02 J-03 J-05 J-06 J-07 J-12) and J-14's crop ride as passengers only.
- **J-15 is still unbuilt** and stays queued behind the repair round.
