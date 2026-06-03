# Iteration 15 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** lean

## Summary

J-31 (the synthesis capstone — the last buildable journey) was **built** exactly as specified:
frontend-only, +89/−4 across the two intended files, with the principal anti-goal risk (J-18, "exactly
one date selector") verified clean in source by this evaluator. But J-31's **defining acceptance is a
multi-step cross-page browser travel (lab evidence → cross-link → pre-filtered leaderboard → Stock
Detail), and that travel was never captured** — the browser-QA agent returned **SKIPPED** because the
iter-15 DoD step `npm run build` clobbered the running `next dev` server's `.next`, serving a dead,
un-hydrated shell on every route (an environmental fault, not an iter-15 code defect). Per the iter-4
lesson cited in the spec ("convert J-31 only if the full travel is actually captured"), J-31 is recorded
**partial**, not passing. No journey regressed; coherence is COHERENCE-PASS; the remaining work is a
tractable lean re-verify on a clean `.next`.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| **J-31** (synthesis, TARGET) | failing | **partial** | Built + statically verified; defining browser travel **not captured** (browser-QA SKIPPED on `.next` clobber). Source: `stocks/page.tsx` deep-linkable filters (lines 88–154), `research/page.tsx` `SubjectLeaderboardLink` (lines 1002–1006); build/typecheck PASS; coherence COHERENCE-PASS. `reports/qa/.../iter-15-evidence/UT-01-research-dead-shell.png` (the env block) |
| J-18 (principal risk) | passing | passing (source-reverified) | Evaluator read the diff: fetch keyed `[asOf]` only (`stocks/page.tsx:122`), `asOf` solely from `useAsOf()` (:99), filter params `sector`/`setup`/`pattern` only (:108–110, :150–152), **zero `as_of`/date query param**. One date control preserved. |
| J-02 | passing | passing (carried/source) | Dropdown filters intact + now URL-synced; `visible` memo unchanged (no re-sort/recompute). QA source-verified. |
| J-15 | passing | passing (carried/source) | No new fetch — fetch effect dep array is `[asOf]` only; filter change cannot refetch. Warm load unchanged. |
| J-05, J-06 | passing | passing (carried) | Stock Detail + scoring path untouched by the 2-file FE diff; scores byte-identical to leaderboard (last live-confirmed iter-14). |
| J-25, J-27, J-29, J-30 | passing | passing (carried) | Labs' analytics byte-unchanged; the cross-link is purely additive to `EventStudyLab`. |
| J-13, J-16 | passing | passing (carried) | as-of provider + VCP/pattern paths untouched. |
| J-01, J-03, J-04, J-07, J-08, J-09, J-10, J-11, J-12, J-14, J-17, J-19, J-20, J-21, J-26, J-28 | passing | passing (carried) | Additive 2-file FE diff → no backend/engine/serving path touched → no regression possible; not browser-re-exercised this iter (browser-QA SKIPPED, env). |
| J-22, J-23, J-24 | failing | failing (out of scope) | Externally Yahoo-429 data-walled; not autonomously retried (correct). |

**Newly passing:** none. **Newly failing:** none. **Regressed:** none. **Progress:** J-31 moved
failing (unbuilt) → partial (built + statically/source verified; defining browser flow blocked by env).

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Exactly one date selector *(critical for this iter)* | OK | **Source-verified by evaluator.** Only `sector`/`setup`/`pattern` filter params read/written; no `as_of`/date param; `useAsOf()` is the sole date source; fetch keyed `[asOf]`. The one historical minor violation (the old `BacktestDatePicker`) stays RESOLVED since iter-1. |
| Single source of truth / No recompute in read path *(critical)* | OK | No new endpoint, query, or computation. `parsePatternParam` is a pure URL→sentinel decoder; filtering stays the existing client-side `visible` memo over server rows. |
| No magic numbers (config-driven UI vocabulary) | OK | Cross-link href derived from the payload's `subject.kind` (`pattern` → `?pattern=<key>__only`; `setup` → `?setup=<key>`) — no hard-coded subject↔filter table. |
| No fabricated data / honest NA | OK | Unrecognized `pattern` param → `__all__` (no crash, no fabricated filter); zero-match filter → existing honest empty-state; low-sample lab cells stay NA + n. |
| No lookahead / Immutable / No order path / No secrets | OK | No backend, engine, schema, or dependency change (diff = 2 FE files). |

Coherence audit: **COHERENCE-PASS** (no structural veto).

## Next-Step Recommendation

**lean re-verify of J-31 only**, hardened against the `.next` clobber that blocked this iter (no code
change expected — the feature is built and statically sound):

1. **Fix the environment first (the actual blocker):** stop `next dev` on :3835, `rm -rf
   apps/frontend/.next`, restart `next dev`, and ensure `npm run build` does **not** run against the live
   dev `.next` (use a separate build dir or run it before the dev server starts). Confirm `GET
   /_next/static/chunks/main-app.js` → 200 and the health badge flips off "Checking backend…" before
   driving any UT case. (Recurring hazard — see MEMORY `browser-qa-dead-shell-next-cache`.)
2. **Capture the full J-31 travel under exclusive Chrome** (serialize vs the cross-project Tapeology
   contention, iter-6 lesson): Factor Lab decile + downside-risk-adjusted + rank-IC + n + by-regime split
   (J-25/J-27/J-30) → Setup & Pattern Lab event study with honest NA (J-29) → click "View the names
   expressing this on the leaderboard →" → **DOM-assert** the pre-applied filter + narrowed `visible/total`
   (use a populated subject: pattern `pullback_to_rising_dma` ≈ 9 names, or setup `Breakout-watch` ≈ 8) →
   open one row → `/stocks/[ticker]` with the badge + three A–E scores + invalidation (J-06/J-20).
3. **J-18 cross-check live:** with a filter deep-linked, toggle the global as-of; assert (distinct shots +
   network) the filter stays intact, the page re-points by date, and **no `as_of`** appears in a
   leaderboard fetch. Ground-truth counts for assertions are pre-captured in the browser-QA report.

If the full travel captures green and nothing regresses, J-31 → passing (**28/31**).

## Halt Justification (if halting)

N/A — not halting. **Not GOAL_ACHIEVED:** J-31 is unverified at its defining flow (partial), and
J-22/J-23/J-24 remain failing (data-walled). **Not REGRESSION:** no prior-passing journey regressed; the
diff is additive frontend-only and the dead-shell is a route-agnostic dev-server `.next` artifact (the
prod build itself succeeded), not a code regression. **Not STALLED:** a concrete, tractable next step
exists (clean `.next` + re-run browser QA). **Not ESCALATE:** already full depth.

**Strategic (forward, not this iter's fix):** even once J-31 verifies green, **GOAL_ACHIEVED is not
autonomously reachable** — J-22/J-23/J-24 stay externally Yahoo-429 data-walled and unblock only on
operator confirmation of a reachable no-key egress (J-22 auto-heals via its committed finish runbook) or
a `docs/goal.md` scope edit. After the J-31 re-verify, expect either that operator confirmation or a
correct STALLED on the data-walled remainder. Do NOT autonomously retry J-22/J-23/J-24.
