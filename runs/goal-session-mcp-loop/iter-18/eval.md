# Iteration 18 Evaluation

**Verdict:** REGRESSION
**Depth Recommendation For Next Iteration:** full

## Summary

The atomic 30-year / 548-pool basis swap and the ONE sanctioned all-FAIL ledger reset landed correctly and honestly — I read both ledgers directly (7 canonical + 7 staging rows, all FAIL, register 2026-07-03, Bonferroni divisors 1..7 preserved, ZERO retired values), confirmed the shared certification engine is byte-untouched, and verified `proven_signals={}` forces every badge product-wide to "Not yet proven." That half is the system working as goal.md sanctions. **But this iteration also shipped a confirmed, unfixed, reproducible full-page crash: `/stocks` — the product's most-prominent page — crashes to a blank "Application error" (all navigation wiped) the moment a user sorts by the "Sector" column, because the broadened pool now returns `sector:null` for ~78% of rows into an unguarded comparator (`stocks/page.tsx:93`) with no error boundary.** I opened `UT-21-fail-crash.png` and confirmed the crash directly. Sector-sort has been live since iter-2, so this is a prior-passing journey (J-01's `/stocks` surface) now failing — a REGRESSION. It is an UNSANCTIONED defect, categorically distinct from the goal.md-sanctioned edge non-survival. The terminal closure gate is CLOSURE-FAIL and ux-regression is UX-REGRESSION-FAIL; both caught it, while the pipeline's own status.json and QA report falsely claimed "zero blockers / ready to ship."

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Every score shows an evidence status | passing | **regressed** | reports/qa/goal-mcp-loop-iter-18-evidence/UT-21-fail-crash.png (crash) · UT-02-leaderboard-top.png (default OK) · stocks/page.tsx:93 + scoring.py:377 |
| J-02 Drill into the proof behind a score | passing | partial | UT-01-result.png (honest not-proven affordance; no Proven badge exists to drill — data-basis provision) |
| J-03 Unproven / noise honestly marked | passing | passing (fresh) | UT-02-leaderboard-top.png · TC-04-evidence-page.png (leadership_score FAIL -0.03%) |
| J-04 Regime-conditioned evidence | passing | passing (contract) | TC-04-evidence-page.png + certified-claims.jsonl row 2 (Breakout-watch × Risk-on FAIL, p=0.9460) · QA TC-13 (regime-row pixel below fold) |
| J-05 Audit the evidence ledger | passing | passing (fresh) | TC-04-evidence-page.png (7 rows, full fields, linkback) + direct ledger read |
| J-06 vcp_contraction edge surfaced | passing | partial | certified-claims.jsonl row 4 FAIL (was +3.33%) — sanctioned, honestly dark |
| J-07 Multi-horizon edge surfaced | passing | partial | certified-claims.jsonl row 5 FAIL (was +8.91%) — sanctioned |
| J-08 Multi-factor combination edge surfaced | passing | partial | certified-claims.jsonl row 6 FAIL (was +4.69%) — sanctioned |
| J-09 rs_spy_3m 60-day edge surfaced | passing | partial | certified-claims.jsonl row 7 FAIL (was +21.34% yellow-flag) — sanctioned; retired value renders nowhere |
| J-10 Deep price history surfaced | unknown | **passing** | UT-01-result.png ("history since 1996-01-02 · weekly-sampled") · QA TC-02 ARM short · audit-verified (F1 viewport nuance non-blocking) |
| J-11 Every Proven edge re-certified; no stale survives | unknown | **passing** | Direct read of both ledgers (all FAIL, no retired values) · TC-04-evidence-page.png · evidence.py strict PASS filter |
| J-12 Broad point-in-time dynamic universe | unknown | partial | UT-02 (541/541, 587 symbols) + staleness gate unit-verified; /methodology timeline assertions NOT cleanly verified (UT-13-fail-no-universe-section.png; canonical lane crashed) |
| J-13 Data Manager 548-pool + legend | unknown | unknown | Out of scope (goal.md sequences to iter-19) |
| J-14 Deep index/macro context + vendor labels | unknown | unknown | Steps 2-3 out of scope (step-1 data delivered iter-17) |

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| #1 No unbacked "Proven" / unbacked renders "not yet proven" | OK (upheld — strongly) | Both ledgers ALL FAIL → `proven_signals={}` (evidence.py:103 strict `status==PASS`); zero "Proven" chips anywhere (UT-01/UT-02/TC-04). Load-bearing enforcement verified in source. |
| #2 No buy/sell/price-target/alpha | OK on available evidence | No such language added in the diff (grep clean); "Research-only · decision support · no orders" on UT-01/UT-02; audit confirmed on stock-detail. GAP: the product-wide UT-29 sweep only ~25% executed before the lane crashed — complete it in iter-19. Not a violation. |
| #3 Displayed numbers correct (match engine) | OK (upheld) | /evidence FAIL rows byte-match the regenerated ledger (row 1 −0.0003136 → "−0.03%"); no UI recompute. |
| #4 No overfit edge shown proven | OK (upheld) | Retired edges (incl. +21.34% OOS≫in-sample) honestly FAIL on the deep multi-regime holdout; none surfaced as proven. |
| #5 Determinism + no-lookahead | OK (upheld) | seed 20240601; bars_asof slice `date<=as_of` in every /bars mode; engine untouched (audit-verified). |
| #6 No claim ships without referee PASS | OK (upheld) | No `## Evidence Claim` block; the ledger IS the referee's own regenerated verdicts (the sanctioned in-iteration replay). |
| #7 No hard-coded credentials | OK (upheld) | scan-report CLEAN; my diff grep clean; `redact_stooq_key` choke point intact (audit-verified). |

**No anti-goal was violated.** The `/stocks` crash is a functional REGRESSION, not an anti-goal violation (there is no "must not crash" anti-goal).

## Coherence

COHERENCE-PASS (no structural veto). Independently re-verified diff base (`git diff HEAD` + untracked, per spec NOTES); no new endpoints/pages/nav; the bars `range` param and `stale_series` reason are additive presentation extensions of already-registered values; `resolve_servable_symbol` consolidation is a coherence improvement.

## Next-Step Recommendation

iter-19 (FULL), after the human acknowledges the regression (`--acknowledge-regression`). No new feature/evidence work; this is a fix + complete-verification pass:

1. **Fix the J-01 crash (blocking):** harden `apps/frontend/app/stocks/page.tsx:93` `SORT_COMPARATORS.sector` against `null` (e.g. `(a.sector ?? "").localeCompare(b.sector ?? "")`), filter/relabel `null` out of the `sectors` filter vocabulary at lines 355-357 (an explicit "Unassigned" bucket, never a literal `null` option), and correct `apps/frontend/lib/api.ts:279` `sector: string` → `sector: string | null` so the type system reflects the real contract. Add a route-level `error.tsx`/`global-error.tsx` so a future uncaught client exception degrades to a contained card instead of wiping the whole app.
2. **Complete the canonical browser-qa lane** (it crashed at exit 70 with tasks #18-22 pending): keep BOTH services up and staying up, then re-run to completion — re-verify UT-21 sector-sort against the fix; Watchlist negative paths (unknown-ticker 404, duplicate 409); the Backtest 2005-02-25 as-of floor; and — highest priority, goal.md-critical — the full four-quadrant P1 anti-goal-#2 language sweep (UT-29).
3. **Cleanly browser-verify J-12** (currently partial): the /methodology membership timeline entries/exits, a mid-history-IPO name absent-before/present-after, and the `stale_series` reason card in frame.
4. **Reconcile** `status.json` and `goal-mcp-loop-iter-18-qa.md` against the completed evidence set (both currently overstate completion), and re-run the auditor with an explicit instruction to read and reconcile the ux-regression verdict.
5. **Non-blocking (carry):** F1 — confirm live whether the Full-history chart plots pre-2018 weekly bars for >8y names (e.g. /stocks/NVDA) and widen the x-domain to `first_available_date` if not.

On a clean re-run, J-01 returns to passing, J-12 flips to passing, and — with J-02/J-06..J-09 correctly held partial under the data-basis provision — the product presents an honest, crash-free, fully-verified 30-year basis.

## Halt Justification

**REGRESSION — loop halts for human review.** A journey with prior status `passing` (J-01, the `/stocks` leaderboard) is now failing: a confirmed, reproducible, unfixed full-page crash on the product's most-prominent page (one click from home), triggered by the pre-existing one-click "Sector" sort control on the DEFAULT data state (~78% null sectors), wiping all navigation with no error containment. I verified this myself: opened `UT-21-fail-crash.png` (blank "Application error: a client-side exception has occurred"), traced the root cause to this iteration's own data-basis change (`scoring.py:377` `cfg.stock_sectors.get(ticker)` → `null` for the broadened pool) flowing into the unguarded comparator `stocks/page.tsx:93` (git diff HEAD on that file is EMPTY — a data-contract regression, not a code change), and confirmed no `error.tsx`/`global-error.tsx` exists to contain it. Two independent gates concur — ux-regression-reviewer (UX-REGRESSION-FAIL) and phase-closure-auditor (CLOSURE-FAIL, which personally opened the same screenshot) — while the pipeline's own `status.json` ("Zero blockers... All 18 functional test cases passed... Ready for auditor/release") and `qa.md` ("Verdict: PASS, No blockers") falsely claimed clean completion despite the crash screenshot sitting in the very evidence folder they cite. This is precisely the class of defect the REGRESSION verdict exists to halt on, on the session's highest-stakes iteration. The fix is surgical (null guards), so the operator can `--acknowledge-regression` and let the loop repair it in iter-19, or fix manually first. NOTE: J-06..J-09's edge non-survival and J-02's un-exercisability are the goal.md-SANCTIONED data-basis reset (`partial`, not-a-regression) and did NOT drive this verdict — only the unsanctioned `/stocks` crash did.
