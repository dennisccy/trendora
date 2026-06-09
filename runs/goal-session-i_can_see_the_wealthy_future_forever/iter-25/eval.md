# Iteration 25 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

J-37 (Missing-data diagnostic + gap-exact pull-missing) and J-38 (unified Unfinished-imports with Resume/Retry/Remove) were BUILT this iter, are source- and test-proven (backend 601/0, COHERENCE-PASS, review PASS_WITH_NOTES), and most of their browser legs pass — but neither reached `passing`: the dedicated browser-qa-agent returned **FAIL** on UT-11 (a P1 happy-path: Resume on a needs-key checkpoint with no key → backend 400 → no running job, no visible error feedback), J-37's three-category diagnostic + pull flow was SKIPPED (the live host has no insufficient universe member, so the defining fixture flow was never exercised), and J-39 + J-35 were again NOT captured at their defining multi-step flows (only surface-presence in the QA MODE-2 report). No prior-passing journey regressed (diff is 9 additive `/data`-only files, no DB regen, key-leak scrub + Dismiss audit boundary verified in source). This is **CONTINUE**: real progress, four targets tractable and well-specified for a re-capture/UX-fix iter-26.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-37 (target) | failing | **partial** | UT-01 (panel present) + UT-02 (honest empty-state) PASS; UT-03/04/05/06/07/16/19 SKIP — no insufficient member on host so the 3-category + gap-exact-pull defining flow was never captured against a fixture. Source/tests proven (601 green incl. real-httpx key-leak regression). |
| J-38 (target) | failing | **partial** | Panel/state-strings (UT-08), badges (UT-10), Retry (UT-12), Dismiss-preserves-audit (UT-13), key re-prompt (UT-14), key-not-echoed (UT-15), heading (UT-21) PASS. **UT-11 Resume = FAIL** (deliberate no-key resume → correct 400, but no running job + no visible feedback; Resume-success leg unverified). |
| J-39 (carried) | partial | **partial** | QA MODE-2 TC-39-Preview = "Preview control present" only (surface-presence, not the confirm-preview multi-step flow). No code change to J-39 this iter; cascade boundary source-proven. |
| J-35 (carried) | partial | **partial** | QA MODE-2 TC-35 = "Expand option present/selectable" only. No injected-provider expand end-to-end capture. Machinery integration-proven; live expansion data-walled (universe_count 122, NA/non-halting). |
| J-36 (req) | passing | passing | UT-17: Coverage panel 162 rows, single as-of selector; diagnostic reuses the SAME compute_coverage producer (coherence PASS). |
| J-34 (req) | passing | passing | UT-08: durable resumable checkpoint "Paused 429 chunk 0/7" survives restart; J-37 pull + J-38 Retry reuse the engine (no fork). |
| J-33 (req) | passing | passing | UT-15 + source: key-leak scrub holds on the new pull/retry/resume error strings; sentinel 0x in any response. |
| J-08 (req) | passing | passing | UT-13 + source: J-38 Dismiss soft-flags DataProviderRun / deletes a checkpoint only; Run history (audit) retained 14 rows incl. 3 partial. |
| J-18 (req) | passing | passing | UT-18: exactly one date `<select>` (global as-of) on /data; zero date inputs in the two new panels (the flagged watch risk, held). |
| J-06/J-07/J-15 (req) | passing | passing | scoring/scanner/regime/snapshot path git-untouched; no DB regen. Structural carry. |
| J-01–J-05, J-09–J-14, J-16, J-17, J-19–J-21, J-25–J-32 | passing | passing | Out-of-scope git check EMPTY; additive 9-file /data-only diff; 601 tests green → cannot have regressed. |
| J-22 / J-23 / J-24 | failing | failing | Externally Yahoo-429 data-walled; NON-HALTING / NON-VETOING per goal.md lines 989–1012. Not re-probed (spec forbids). |

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Import keys env-or-session, never echoed back | OK (RE-CONFIRMED) | iter-22 fix holds on every NEW error string (J-37 pull, J-38 retry/resume): all errors route through `scrub(...)` from `_resolved_key`; resolved key never written to checkpoint/run; REAL-httpx key-leak regression in the 601-green suite; UT-15 sentinel only as type=password value, 0x in job card / unfinished-state. |
| Exactly one date selector | OK (RE-CONFIRMED) | The two new /data panels add no date state — UT-18: one global as-of `<select>`, zero date inputs in diagnostic/unfinished panels; the 4 `<input type=date>` are job/removal action params. Coherence-auditor concurs. |
| Snapshots are immutable (critical) | OK | J-38 Dismiss touches no snapshot/forward-return row; `dismiss_import` soft-flags `DataProviderRun.dismissed` or deletes a checkpoint only; UT-13 + source confirm audit row preserved. No DB regen. |
| Single source of truth (critical) | OK | Diagnostic reuses the single `compute_coverage` producer; pull reuses the J-34 engine; no rival module (coherence PASS). |
| Risk-Off gates Actionable (critical) | OK | scoring/regime path git-untouched; no DB regen. |
| No recompute in read path | OK | Diagnostic + unfinished list are read-only over stored bars / job-control rows; snapshot_serving.py untouched. |
| No fabricated data | OK | Diagnostic shows missing/thin as NA; provider failure surfaces explicit error/resumable; pull fabricates no bar (tests). |
| No magic numbers | OK | Thin threshold from `indicators.min_history_bars`; gap calendar from the benchmark bars (config); review confirms none introduced. |
| Pull-missing fetches exactly the gap, idempotently | OK (source/tests) | Pull constructs `symbols`+`[start,end]` == diagnosed shortfall, dispatched through the EXISTING J-34 path; per-(symbol,date) INSERT-new-only idempotent (tests). Browser leg uncaptured (no host fixture). |

No new anti-goal violation introduced. Both historical minor violations remain RESOLVED.

## Coherence

COHERENCE-PASS (`runs/goal-session-.../iter-25/coherence.md`) — both new values (J-37 diagnostic, J-38 unfinished-imports) registered in the blueprint Data Contract; diagnostic reuses the canonical coverage producer; pull reuses the J-34 fetch; Dismiss mutates job-control only; no new page/route/nav. One advisory WARN only (the legacy `resumable_imports` array is still served alongside `unfinished_imports` for backward compatibility — the frontend renders only the new one; no data shown twice; non-blocking).

## Next-Step Recommendation

**full** depth, iter-26 — close the four targets to `passing`; this is the last buildable wave and GOAL_ACHIEVED is reachable once they capture green.

1. **Environment first** (gates every capture): stop strays by port (no broad pkill — MEMORY `dev-server-cleanup-by-port`), `rm -rf apps/frontend/.next`, restart `next dev`, confirm `main-app.js` → 200 + health badge cleared BEFORE any UI; do NOT run a prod build against the live dev `.next`.
2. **J-37 (capture + nothing else needed in code):** seed an injected fixture with a no-history member, a thin member, and an intra-series-gap member so the diagnostic actually renders all three categories with exact shortfalls; click "Pull the missing data" and assert the constructed job's `symbols`+`[start,end]` == the diagnosed gap (NOT the whole universe/window); run an offline injected-provider pull to completion → row clears → J-36 coverage reflects the new bars. Live pull over a walled provider stays NA/non-halting.
3. **J-38 (one small UX fix + a success capture):** (a) capture a SUCCESSFUL Resume of a no-key / env-key / injected resumable checkpoint continuing from `next_chunk_index` — the defining acceptance, never demonstrated; (b) fix the UT-11 UX so a 400 (needs-key Resume without a key) surfaces a VISIBLE inline error and does NOT drop the row from the panel (the `ResumeControl` catch already sets a `role=alert` error and does not remove the row — verify it renders, and ensure no overview reload silently removes the row on a failed resume). Do not let the deliberate-missing-key 400 path be the only Resume evidence.
4. **J-39 + J-35 (re-capture only, no code change):** J-39 Remove-data confirm-preview (removable bars + range + protected committed-seed breakdown + cascade) + seed-only refusal via the **preview** path on the live host (MEMORY `j39-live-host-has-user-added-nvda-bars` — never destructive-confirm a real symbol live); J-35 injected-provider expand end-to-end → passers + omitted-with-reason → grown universe-count.
5. Evidence hygiene: the iter-25 dedicated-QA shots collided (UT-11-before.png == UT-11-after.png; UT-08/UT-01-initial/TC-06/TC-XX all share one sha) — capture distinct before/after shots and sha-dedupe.

Do NOT autonomously re-probe J-22/J-23/J-24. Do NOT declare completion on a single import-journey landing (iter-20 re-scope trap) — all four targets must capture green.

## Halt Justification (if halting)

N/A — not halting. CONTINUE: ≥0 newly-passing but substantial built+verified machinery, no regression, no critical anti-goal, COHERENCE-PASS; four tractable, well-specified targets remain (a UX fix + browser re-captures on a clean build / injected fixture). Not GOAL_ACHIEVED (J-37/J-38 partial + a P1 browser FAIL; J-39/J-35 still uncaptured). Not REGRESSION (no prior-passing journey regressed; additive /data-only diff, no DB regen, key-leak + immutability boundaries verified in source). Not STALLED (concrete next work). Not ESCALATE (already full depth).
