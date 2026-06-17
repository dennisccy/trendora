# Iteration 28 Evaluation

**Verdict:** GOAL_ACHIEVED
**Depth Recommendation For Next Iteration:** lean

## Summary

Iter-28 was a lean, frontend-only (3-file) consolidation that closed J-86's two open iter-27 UI legs: the max-drawdown colour is now magnitude-graded via a shared `lib/mdd-color.ts` (`color-mix` over the existing `--neg`/`--text-muted` design tokens, NA/0 muted, zero hardcoded hex), and the MDD + forward-return column sort is confirmed working on all five columns when the header is resolved by `aria-label` (the iter-27 "no-op" was a browser-QA XPath `text()` selector false-negative on a byte-unchanged sort path). With J-86 — the lone remaining non-passing buildable journey — flipping `partial` → `passing`, every buildable Must-have (J-01..J-21, J-25..J-86) is now passing/already_passing; J-22/J-23/J-24 stay honestly blocked-NA (data-walled), which `goal.md` (lines 105-108) designates non-vetoing. Coherence is COHERENCE-PASS, no anti-goal violation is unresolved, so all three GOAL_ACHIEVED conditions hold.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-86 (Max-drawdown columns everywhere; colour-graded + sortable) | partial | **passing** | reports/qa/goal-…-iter-28-evidence/UT-J-86-stocks-mdd-color-graded.png, UT-J-86-stocks-5d-mdd-sort-asc.png, UT-J-86-themes-mdd-sort.png, UT-J-86-sectors-mdd-sort.png |
| J-48 (leaderboard column sorting — view transform) | passing | passing | reports/phase-…-iter-28-ui-test-results.md (UT-J-48; aria-label sort + `#` restores stored rank) |
| J-75 (forward returns on /stocks + detail) | passing | passing | reports/qa/goal-…-iter-28-evidence/UT-J-86-stocks-initial.png (UT-J-75) |
| J-81 (Themes/Sectors fwd-return + MDD columns) | passing | passing | reports/qa/goal-…-iter-28-evidence/UT-J-86-themes-mdd-sort.png, UT-J-86-sectors-mdd-sort.png |
| J-06 (score/MDD consistency leaderboard vs detail) | passing | passing | reports/qa/goal-…-iter-28-evidence/UT-J-06-nvda-detail-scores.png (VIEWED: 1d/5d/10d −4.17%, 20d −6.63%, 60d −12.06% match) |
| J-05 (Stock Detail explainable scores) | passing | passing | reports/qa/goal-…-iter-28-evidence/UT-J-06-nvda-detail-scores.png |
| J-18 (one date control, no duplicate) | passing | passing | reports/phase-…-iter-28-ui-test-results.md (UT-J-18; Backtest 0 page-local date inputs) |
| J-70 (heatmap readable/compact) | passing | passing | reports/qa/goal-…-iter-28-evidence/UT-J-70-J-74-heatmap.png |
| J-74 (heatmap multi-hue legibility) | passing | passing | reports/qa/goal-…-iter-28-evidence/UT-J-70-J-74-heatmap.png |
| J-22 / J-23 / J-24 (data-walled) | unknown | unknown (blocked-NA, non-vetoing) | n/a — provider-walled, never halts per goal.md 105-108 |

All other buildable Must-haves (carried) remain `passing`/`already_passing`; backend diff is empty so the iter-27 GREEN suite (878 passed, 0 failed) is the valid standing gate for the byte-unchanged backend.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Single source of truth (critical) | OK | MDD reads identically leaderboard↔detail (J-06 VIEWED: NVDA five values match exactly). Colour is a pure view transform over the single-sourced served value; coherence Step 1 PASS. |
| No recompute in the read path | OK | `mddColorClass` does class mapping only — no arithmetic on the drawdown value, no fetch, no `useState`/`useEffect`. Re-formats the already-served `max_drawdown`. |
| No magic numbers / no hardcoded hex | OK | Grep of the 3-file diff: zero `#` hex literals. Bands are `color-mix(in_srgb,var(--neg)_N%,var(--text-muted))`; thresholds are named module constants (`MDD_BANDS`). Unit test asserts every band mixes `--neg` and contains no hex. |
| No fabricated data; honest forward-test for partial windows | OK | `mddColorClass(null/undefined/0)` → `text-text-muted` (unit-test + live UT-J-86 confirmed); NA never coloured as a real drawdown. |
| Exactly one date selector (critical) | OK | No as-of component in the diff (`asof-provider/switcher/calendar` absent); UT-J-18 Backtest shows 0 page-local date inputs. No date state introduced. |
| Snapshots immutable / no lookahead (critical) | OK | Backend diff empty — no scanner/forward-test/snapshot code touched. |
| No order/execution path (critical) | OK | Frontend presentation-only change; no execution surface added. |
| No secrets in source | OK | No credential/key/token in the diff. |
| Prior minor violation (iter-20 magic-number) | RESOLVED | Resolved in iter-21; no float literal remains in `research.py`; guard test green. Not reintroduced. |

## Next-Step Recommendation

Halt — goal achieved. The J-83..J-86 extension is complete and every buildable Must-have (J-01..J-21, J-25..J-86) is passing/already_passing with positive evidence. No tractable code work remains for the buildable journeys. J-22 (the real ≥500-member Yahoo screen) auto-unblocks through the already-built J-84 cookie+crumb expand path once a cap-capable provider is reachable on this host (no code change); J-23/J-24 follow the committed intraday runbook (data, not build). If the owner later extends `goal.md` with new journeys and resumes in-place — as in the J-48..J-54, J-55..J-67, J-79..J-82, and J-83..J-86 extensions — regenerate/re-approve the blueprint on resume and dispatch the first new iteration; a presentation-only follow-up like this one warrants **lean** depth, while any backend-touching journey should run **full** with the pytest suite as the gate.

## Halt Justification

All three GOAL_ACHIEVED conditions are satisfied with concrete, independently-verified evidence:

1. **Every Must-have journey has positive evidence of passing** — 71 `passing` + 12 `already_passing` = 83 buildable Must-haves green; J-86 (the lone prior `partial`) verified passing this iteration via (a) the magnitude-graded `mddColorClass` source + 9 GREEN unit tests + browser-QA computed-CSS showing four distinct `color-mix` colours, and (b) aria-label-resolved sort confirmed reordering all five MDD columns and the five forward-return columns (NA last, indicator flips). The only non-passing journeys are J-22/J-23/J-24, which `goal.md` (lines 105-108: "Data-dependent journeys never block the rest … records those journeys as honestly blocked (NA) and continues — they never halt the loop or veto completion") explicitly designates non-vetoing; they are provider-walled, not failing.
2. **No unresolved anti-goal violation** — the only ever-recorded violation (iter-20, minor magic-number) was resolved in iter-21; this iteration's grep confirms no new hardcoded hex and no client-side recompute.
3. **Coherence is COHERENCE-PASS** — `iter-28/coherence.md` confirms no data-contract drift (no second `max_drawdown` computation; all surfaces read the unchanged canonical endpoints; single-source-of-truth strengthened by centralizing the colour scale in one module) and no IA drift (no new route/home/shell). One deferred presentational WARN (local `MaxDrawdownCell` "NA" vs shared em-dash) is non-blocking and explicitly out of scope.

Independent verifications performed: `git diff --stat HEAD -- apps/backend` empty; `git status` confirms only `forward-return.tsx` modified + `lib/mdd-color.ts` / `lib/mdd-color.test.ts` new, with `stocks/themes/sectors page.tsx` (the sort code path) byte-unchanged; `grep -nE '#[0-9a-fA-F]{3,8}'` over the 3 files returns nothing; `node lib/mdd-color.test.ts` → 9 passed; and four evidence screenshots viewed (graded /stocks leaderboard, historical sort capture, NVDA detail J-06 coherence panel, themes/sectors sort). No regression, no critical breach, COHERENCE-PASS ⇒ GOAL_ACHIEVED.
