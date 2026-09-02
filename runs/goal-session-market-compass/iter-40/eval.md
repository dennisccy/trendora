# Iteration 40 Evaluation

**Verdict:** GOAL_ACHIEVED
**Depth Recommendation For Next Iteration:** evidence

## Summary

The last unbuilt job, J-15 "What changed accounts for every stock move", is now built and works.
On the newest day the page shows all three numbers it promised: the ten stock moves it displays,
a plain line saying "Showing the top 10 stock moves", "Suppressed moves (79)" instead of the old
36, and a separate line saying "4 more stock moves held back by the display cap". I did not take
anyone's word for those numbers. I read them out of the picture myself, and then I counted them
again straight from the saved market data: 539 names on both days, 57 bucket changes, 14 of them
big enough to report, the biggest 10 shown, the next 4 held back (TRV, SJM, ALL, TTWO — exactly
the four the job named), and 43 too small to report. 10 + 43 + 4 = 57, with nothing left over.
All fifteen jobs now pass, no project rule is broken, and the structure check passed. Two things
the owner should still see are written below: this round ran as a light round although it was
planned as a full one, and one automatic check script was quietly rewritten after it failed.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Sector labels honest and near-complete | passing | passing | reports/qa/goal-market-compass-iter-40-evidence/J-01-verify.png (replay PASS) |
| J-02 What changed since the previous session | passing | passing | reports/qa/goal-market-compass-iter-40-evidence/UT-J-02-result.png — replay FAILed, cause traced by me (see below); LLM row re-checked against DB |
| J-03 Plain-English summary with cited facts | passing | passing | reports/qa/goal-market-compass-iter-40-evidence/J-03-verify.png (replay PASS) |
| J-04 Each candidate explains why and why-not | passing | passing | reports/qa/goal-market-compass-iter-40-evidence/J-04-verify.png — I opened it: `/?asof=2026-03-30` renders in full, no error card |
| J-05 Each close freezes one manifest, exported byte-consistently | passing | passing (carried; not in the required set) | no browser row this round. My read-only check on the new v11: export bytes == stored `session_delta`, `content_hash` and `manifest_hash` both match |
| J-06 A frozen manifest never changes | passing | passing (carried; not in the required set) | no browser row this round. My read-only check: `2026-08-12_v7.json` md5 `d905dcfeb7883d86602d64d4c24682ad` — 6th round unchanged; 36 pre-existing rows intact, +1 additive |
| J-07 Today page answers the ten-second read | passing | passing | reports/qa/goal-market-compass-iter-40-evidence/J-07-verify.png (replay PASS) |
| J-08 Market page intact, history honest | passing | passing | reports/qa/goal-market-compass-iter-40-evidence/J-08-verify.png (replay PASS) |
| J-09 Backend fits the host | passing | passing | reports/qa/goal-market-compass-iter-40-evidence/UT-J-09-result.png; I re-read `config.yaml:109` myself — `cache_size: -65536`, `git diff` on that key empty |
| J-10 Bounded recovery of the two deleted days | passing | passing (carried; code untouched) | iter-39 evidence, durable per methodology A.6 |
| J-11 Incident-bounded clean regeneration | passing | passing (carried; code untouched) | iter-39 evidence, durable; the authorized regenerate call this round produced v11 additively |
| J-12 Every frozen disposition is true | passing | passing | reports/qa/goal-market-compass-iter-40-evidence/J-12-verify.png — I opened it: version 11 / frozen / not prospective-eligible, cohort 529 + shadow 25, DXCM 85.0/26.5/57.6 "excluded by cap", rule hashes `7734ce9ead…` / `396c29d22c…` |
| J-13 Leadership rotation says which way | passing | passing | reports/qa/goal-market-compass-iter-40-evidence/J-13-verify.png; rotation block byte-identical v10 → v11 in my DB check |
| J-14 "Not priority" names its real reason | passing | passing | reports/qa/goal-market-compass-iter-40-evidence/J-14-verify.png — I opened it: DXCM "ranked #11 of the above-floor names, cap 10", `entry_min_score: 26.5 vs 70.0 (distance 43.5) — advisory` |
| **J-15 What changed accounts for every stock crossing** | **unknown** | **passing** | reports/qa/goal-market-compass-iter-40-evidence/UT-J-15-result.png — I opened and read all three new lines; numbers re-derived by me from stored runs 3157/3158 |

### J-15 — what I verified myself, not from a report

Read-only, from `apps/backend/data/trendora.db` (`mode=ro`) and the stored export:

- Stored runs 3157 (2026-08-11) and 3158 (2026-08-12): **539 members on both sides, 0
  new-to-universe**, **57 leadership-bucket crossings** — exactly the goal's measured baseline.
- **14** of the 57 move at or above `stock_score_min_change` (8.0). The top ten by magnitude are
  SMCI 28.33, TOL 14.71, HUM 13.33, KBH 13.29, TER 13.20, ENTG 12.68, V 10.75, DRI 9.70,
  OKTA 9.12, VRSN 8.86 — **identical, and in the same order, to the ten shown on the page**.
- The next four are **TRV 8.66, SJM 8.48, ALL 8.33, TTWO 8.14** — the four names the goal said
  were vanishing. `residual_count` is exactly 4, and a regex search of the whole served
  `session_delta` finds none of the four in `changes` or `suppressed` (TC-2 holds).
- **43** crossings sit below 8.0 → `suppressed_count: 43`.
- Served/stored `stock_accounting` = `{"evaluated_count": 57, "shown_count": 10,
  "suppressed_count": 43, "residual_count": 4}` and **10 + 43 + 4 = 57** (TC-1).
- The flat `suppressed` list now has **79** entries — 1 market + 2 breadth + 24 sector + 9 theme
  + 43 stock — and `suppressed_count` is 79, matching the screen (TC-4). The old v10 row carries
  `suppressed_count: 36` with **0** stock rows: the defect, confirmed at source.
- On screen (`UT-J-15-result.png`, 1385×6031, 13,479 distinct colours — genuine content):
  "Showing the top 10 stock moves", "Suppressed moves (79)" expanded with stock rows reading
  `… < 8.00` down to `0.26 < 8.00`, and a separate, differently-worded line **"4 more stock moves
  held back by the display cap"** with no names attached (TC-4, TC-4b, AG-8's no-per-name rule).
- **Nothing else moved** (TC-7): v10 → v11 `rotation` block identical, sector/theme change entries
  identical, the ten shown stock entries identical in order and content, `candidate_rule_hash`
  `7734ce9ead08dd85…` and `cohort_rule_hash` `396c29d22cb0a7df…` byte-identical.

### The old-manifest path — the exact thing that broke at iter-38

No screenshot at a historical date was captured by the LLM lane, so I checked it three other ways
and say so plainly:

- I opened `J-04-verify.png`: **`/?asof=2026-03-30` renders in full** (Regime 18.61 Risk-off,
  Market phase 63.01 Correction, breadth 12.3%, the honest retrospective caveat). No error card.
- J-04's repaired golden also clicks the degraded label **"Not priority (20 shown — held-back
  counts unavailable for this manifest version)"** at `/?asof=2026-07-23` and **passes replay** —
  a second pre-change date rendering correctly.
- J-02's row visited `/?asof=1996-02-01` and read its empty state — a third.
- In code, `stockResidualDisclosureText` / `stockShownCapDisclosureText` return `null` on
  `undefined` and both call sites are null-guarded
  (`apps/frontend/components/compass-whatchanged-card.tsx:79-85, 102-112`); `stock_accounting?`
  is optional in `apps/frontend/lib/api.ts`. The reviewer ran the 8/8 node test itself.
- The pre-change row is genuinely untouched: v10's `session_delta` still has **no**
  `stock_accounting` key (AG-12 holds — it was not backfilled).

## Anti-goal Check

Worked from `iter-40/scan-report.md` (**CLEAN**) and `iter-40/iter-diff.md` (8 files), plus my own
read-only checks. Every one answered.

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 no unproven "proven" claims | OK | grep of added lines for `proven` / `edge` / `alpha`: zero hits. No evidence-ledger claim introduced. |
| AG-2 decision-quality only | OK | grep for buy/sell/price target/forecast/predict on added lines: zero hits. New strings are "Showing the top N stock moves" and "N more stock moves held back by the display cap". |
| AG-3 displayed numbers correct | OK | Re-derived the entire 57 = 10 + 43 + 4 partition and all four residual tickers from stored scanner rows myself; screen matches the stored row to the printed decimal. |
| AG-4 no overfit edges | OK | No pattern or edge surfaced; no selection rule touched. |
| AG-5 determinism / no-lookahead | OK | `_stock_changes` reads only the two stored runs it already read; no new query, no forward data. |
| AG-6 referee gate | OK | No Evidence Claim introduced; gate passes automatically this cycle. |
| AG-7 no credentials | OK | scan-report CLEAN; no new config/env file in the 8-file diff. |
| AG-8 data-shape/scale resilience | OK — and the iter-39 MINOR is now FIXED | New field is optional and guarded on both consumers; three pre-change as-of dates render in full. `gating` is now `gating?: boolean` with a 3-state `gatingSuffix()` (`undefined` → "— not recorded"), single call site. No new `session.exec`/`select` — the two column-projected reads are byte-identical. **Watch item, not a violation:** the stock-kind `suppressed` list is now unbounded in length (43 today, +3,041 export bytes). The goal text demanded exactly this and the residual stays a count with no names, so I did not score it a breach — but I considered it and I am saying so. |
| AG-9 offline-deterministic ingest | OK | No dependency manifest touched (`git status` shows no package.json / requirements / pyproject change); no external fetch; the only write was the one authorized `POST /api/compass/regenerate`. |
| AG-10 host resource ceiling | OK | `host-guard.env` untouched (mtime 2026-08-19, `git status` clean); `memory_cap_mb` 8192 and `malloc_arena_max` 2 unchanged; `config.yaml` diff is **1 line** and comment-only. |
| AG-11 no new composite number | OK | New fields are four plain integer counts. Zero new numeric literals in any of the four product source files or the new lib file (I extracted them from the added non-comment lines). |
| AG-12 manifest immutability | OK | 37 rows / **23 distinct as-of dates** (was 36 / 23) — **+1 additive**, zero mutated, zero deleted. `2026-08-12_v7.json` md5 `d905dcfeb7883d86602d64d4c24682ad` — the same value iters 35-39 recorded, now a **6th** round. Every pre-existing export mtime predates this run. |
| AG-13 system-vs-market separation | OK | No readiness vocabulary added; the new strings are display-count disclosures. |
| AG-14 no Tapeology coupling | OK | grep for `tapeology` across the diff: zero hits. |
| AG-15 no outcome-tuned selection | OK | `max_stock_items` still **10** and `stock_score_min_change` still **8.0**; the `config.yaml` change is the comment beside `max_stock_items` only. No `compass.selection.*` touched. |
| AG-16 cohorts are not controls | OK | `comparison_cohort` (529) and `near_threshold_shadow` (25) untouched; both rule hashes byte-identical v10 → v11. |
| AG-17 repair never rewrites provenance | OK | `sum(prospective_eligible) = 0` across all 37 rows; the new v11 export carries `prospective_eligible: false`. |
| AG-18 authorized migration preserves everything | OK | No schema migration in this diff. |

**Unresolved violations: none.** The iter-39 MINOR AG-8 ledger entry is marked resolved this
iteration, with the one honest caveat that no screenshot shows the rendered "— not recorded"
string; I verified the fix at source instead.

## Two process findings the owner should see

**1. The round was planned as a full inspection and ran as a light one.** `engine.log:8447` reads:
`Depth arbiter: spec asked FULL but the deterministic ladder demotes it to LEAN (reason:
budget-breach; prior verdict: CONTINUE; evaluator depth recommendation: full)`. It was declared,
not hidden. But it dropped the auditor, the QA lane, the UX-regression reviewer, the closure check
and the walkthrough recording from the round that shipped a brand-new job and changed a card on
the front page. This is the second time in three rounds that a full plan was cut to light, and the
first time (iter-38) was followed by six jobs breaking.

**2. A check script was rewritten after it failed, and it was not announced.** The automatic
replay failed J-02 at 09:55 because its step 2 clicks the words "Suppressed moves (36)" — a count
this round deliberately changed to 79. At **10:08:08** the script was rewritten to click
"Suppressed moves (79)". The spec declared the J-04 and J-14 script repairs in advance, as it
should; the J-02 one was not declared. The note added to the replay file is the same boilerplate
sentence as the last two rounds — "the replay FAIL was a golden-script false positive" — with **no
named cause**, which the iteration spec itself said I should treat as an unresolved failure. So I
traced the cause myself and it holds: the old wording genuinely no longer exists (stored v10 says
36, new v11 says 79), the date was not changed, no assertion was deleted, and no verdict was
re-derived from the edited script — the replay file still records the failure and J-02's pass comes
from the separate live check, whose every claim I re-checked against the database and the picture.
So: a real process breach, with no effect on this round's evidence.

## Next-Step Recommendation

The goal is met, so the loop should stop. Before the owner closes the session, four small items are
worth doing as a short capture-only round (nothing here is a code change and nothing blocks):

1. Record the missing walkthrough films: J-15 "What changed accounts for every stock move" (mark
   the new step as new), and the three still owed from before — J-05 "Freeze one manifest",
   J-06 "A frozen manifest never changes", J-12 "Every frozen disposition is true". Re-take J-14's
   frame from the "Not priority" list rather than the top of the page.
2. Take one picture of an older date (for example 1 April 2005 or 17 April 2001) showing the words
   "— not recorded" beside a missed entry bar. That fix is in the code and I read it there, but no
   photograph proves it on screen.
3. Give the browser step a rule: never rewrite a check script after it has failed. If the wording on
   a page is meant to change, say so in the plan first, the way this round correctly did for two of
   the three scripts.
4. Ask the owner to decide whether the automatic "this failure was a false alarm" note should be
   allowed at all without a written, traceable reason — this is the third round it has appeared.

**In one sentence:** the project's fifteen jobs all work and nothing is left to build, so the owner
should approve the finish and, if they want the record complete, run one short round that only
takes the missing photographs and films.

## Halt Justification

Halting with success. All fifteen Must-have jobs pass with evidence I checked myself, not evidence
I was told about. The one job built this round, J-15 "What changed accounts for every stock move",
I verified twice over: I read its three new lines out of the screenshot, then I counted the same
numbers again directly from the saved market data and got the same answer, including the four
names the job said were disappearing. Nothing frozen moved: the same 23 saved dates, one new
version added and nothing changed or deleted, and the exported file fingerprint that has now stood
unchanged for six rounds. The structure check passed. The one rule that was still half-broken from
last round — a wrong word on three old dates — is fixed. No rule is broken now.

Two honest caveats, neither of which blocks the finish. First, this round ran with fewer inspectors
than planned; I compensated by re-deriving every number in the new work from the raw stored data
and by opening five pictures myself, including one at an old date to confirm the old pages still
open. Second, the films and one photograph are still missing; the project's own rules say a missing
recording of something that demonstrably works is never a reason to keep building, so I did not
treat it as one — but I have written down exactly what is owed.

Machine gates, all run by me: `results` exit **0** · `journeys` exit **0**,
`{"total":15,"passing":15,"blocking":[]}` · `regressions pre→post` exit **0** ·
`coherence --for-achievement` exit **0** · goal-text drift `changed: []`. Review: **PASS**,
`issues: []`. Coherence: **COHERENCE-PASS**. Scan: **CLEAN**.
