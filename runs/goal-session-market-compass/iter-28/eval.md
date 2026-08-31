# Iteration 28 Evaluation

**Verdict:** ESCALATE
**Depth Recommendation For Next Iteration:** full

## Summary

The two pages asked for were built and they work. `/` is now a "Today" page with the six sections in
the right order, and the whole old dashboard moved to a new `/market` page with nothing dropped. I
checked the pictures myself and the numbers on screen match the stored numbers. But the one NEW thing
this round invented — three little words that say whether the market is improving or getting worse —
shows "NA" on every date the product can serve. I proved that against the real database myself: not one
of the 26 stored briefings carries those words. So J-08 "Market page moves over intact" is closed and
J-07 "The Today page answers the ten-second read" is NOT — it is most of the way there. This round was
planned as a deep review and ran as a light one for the seventh time this session, so no independent
checker looked at an iteration that permanently added a column to the protected database.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Sector labels honest and near-complete | passing | passing | reports/qa/goal-market-compass-iter-28-evidence/J-01-verify.png (replay UT-J-01 PASS) |
| J-02 What changed since the previous session | partial | partial (unchanged; replay PASS, limbs not re-examined) | reports/qa/goal-market-compass-iter-28-evidence/J-02-verify.png |
| J-03 Plain-English summary with cited facts | partial | partial (unchanged; replay PASS, limbs not re-examined) | reports/qa/goal-market-compass-iter-28-evidence/J-03-verify.png |
| J-04 Each candidate explains why and why-not | passing | passing (capture defect kept, 10th iter) | reports/qa/goal-market-compass-iter-28-evidence/J-04-verify.png (replay UT-J-04 PASS) |
| J-05 Each close freezes one manifest | passing | passing | reports/qa/goal-market-compass-iter-28-evidence/J-05-verify.png (replay UT-J-05 PASS) |
| J-06 A frozen manifest never changes | passing | passing | reports/qa/goal-market-compass-iter-28-evidence/J-06-verify.png (replay UT-J-06 PASS) |
| **J-07 The Today page answers the ten-second read** | **failing** | **partial** | reports/qa/goal-market-compass-iter-28-evidence/UT-J-07-today-page.png (LLM lane UT-J-07; steps 1,2,4,5,6,7 live-verified — step 3 fixture-only) |
| **J-08 Market page moves over intact, history stays honest** | **failing** | **passing** | reports/qa/goal-market-compass-iter-28-evidence/UT-J-08-market-page.png + UT-J-08-historical-retrospective.png (LLM lane UT-J-08, all 6 steps live) |
| J-09 Backend fits the host | partial | partial (not targeted, carried; last_verified iter-25) | n/a — out of scope this iteration |
| J-10 Bounded recovery of two trading days | passing | passing | reports/qa/goal-market-compass-iter-28-evidence/J-10-verify.png (replay UT-J-10 PASS) |
| J-11 Incident-bounded clean regeneration | passing | passing | reports/qa/goal-market-compass-iter-28-evidence/J-11-verify.png (replay UT-J-11 PASS) |

Deterministic replay lane: 8/8 PASS over the full Required-still-passing set
(`reports/phase-goal-market-compass-iter-28-regression-replay-results.md`). LLM browser lane: 2/2 PASS
(`reports/phase-goal-market-compass-iter-28-ui-test-results.llm.md`). No `DEFERRED-BUDGET` rows, no
`browser-infra.json`, NOT maintenance isolation, no `journeys-changed.md`. All eleven `spec_hash`
values byte-identical to the recorded ones — I ran `goal_gate.py hash-journeys` and compared each.

### Why J-07 is `partial`, not `passing`

I opened `UT-J-07-today-page.png` and walked all seven steps.

- **Verified live and clean (steps 1, 2, 4, 5, 6, 7).** Body order is exactly market-state band →
  Summary → What changed → Leadership rotation → Next-session focus → Manifest, with the readiness
  badge and the "GO — today's board is current" strip only in the chrome above. Regime tile reads
  Risk-on 73.18, phase tile Expansion 25.85 severity / P(bear) 0.00 — matching `/api/dashboard` and
  `/api/market-phase`. Both component breakdowns are expanded in the picture and match the served
  arrays row for row. No readiness word appears anywhere in the body and no market word in the chrome.
  There is no cross-view chart on `/`, and the "Full market context" link reaches `/market` where the
  chart lives. Perf Addendum 42 was appended (dated, nothing overwritten) and the on-load network
  capture shows no `/api/sectors` and no `/api/themes` call.
- **Step 3 is NOT verified live.** All three direction badges render "NA". The browser lane, the
  reviewer and the developer all state — correctly — that `null` is the honest served value. I
  re-derived the cause read-only against the canonical database:
  `select count(*) from next_session_manifests where state_band_json is not null` returns **0** of 26
  rows. Every stored briefing was frozen before this code existed, and briefings are never rewritten,
  so the new words are absent from all of them. The words themselves are proven only by fixture and
  route tests — I re-ran them myself: **11 passed**, including the route-level test that drives the
  real `app.api.compass.compass` function and asserts real words, and the deliberate stress-polarity
  flip.
- **The user-visible consequence, which is why I did not close it.** On the very same page, the band
  says "NA" for the regime direction while the Summary one card below says "Conditions are little
  changed since the prior session (-0.2 regime-score points)". The inputs for that comparison exist and
  are displayed; only the new stored field is missing. So the journey's headline capability — a reader
  learning in ten seconds whether things are improving — does not work on any date the product can
  serve today.
- **This is not an unsatisfiable criterion.** Unlike J-05's and J-06's fixture-only limbs (whose live
  premise was destroyed by the iteration-5 incident and can never return), this one closes with a
  single authorized live request on a date that has no briefing yet: that mints a fresh briefing
  through the now-state_band-aware freeze path and makes the three words observable. That is a concrete
  one-step task, not a loop.

### Why J-08 is `passing`

All six steps were exercised live and I corroborated them against two screenshots. `/market` carries
the full former inventory — both glance cards, the cross-view card with its hide toggle still keyed to
`trendora.dashboard.phaseCrossView`, three breadth cards, Top Sectors, Candidate Counts, Top Themes and
the complete Market Phase & Severity detail. The sidebar lists Today then Market with correct
highlighting on each route (visible in both captures). At `?asof=2025-04-15` the page shows that date's
own values (Risk-off 14.01, Recovery 71.47, P(bear) 1.00, breadth 15.6%), What-changed names
2025-04-14 as the comparison date, and the summary carries the retrospective sentence.

One caveat, disclosed rather than passed silently: step 4 asks for "version-1 stamps" at the frontier,
and the strip shows version 6. On this database that date's version 1 was never frozen and versions 2-6
were minted during incident recovery — so version 1 can never be shown again. The substantive
requirement (frozen, at-ingest, provenance stamps, and never a newer date's briefing) holds and is
visible in the capture. Recorded in the assumption ledger.

## Anti-goal Check

Deterministic scan (`iter-28/scan-report.md`): **CLEAN** — no secret, dependency or license findings.
No dependency-manifest file changed at all (`git diff` on `package.json` / `requirements.txt` /
`pyproject.toml` is empty). All eighteen answered explicitly.

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 no unproven "edge" presented as proven | OK | No new score or confidence claim; the state band renders words or NA only. Grep of both new components: no proof/confidence language. |
| AG-2 decision-quality only, no advice | OK | Grepped the two new components and both pages for buy/sell/target/forecast wording — none. Candidate cautions still read "context, not a signal to act" (J-05-verify.png). |
| AG-3 displayed numbers correct | OK | Verified on three live dates from screenshots: 73.18/Risk-on/25.85/0.00/59.8% at Latest, 14.01/Risk-off/71.47/1.00/15.6% at 2025-04-15, 18.61/63.01/12.3% at 2026-03-30; component breakdowns match the served arrays. The NA badges are the correct rendering of a null field, not a wrong number. |
| AG-4 no overfit edges | OK | No evidence claim, no pattern surfaced as proven this iteration. |
| AG-5 determinism / no lookahead | OK | `build_state_band` compares the current run against the PREVIOUS stored run only; `_severity_at` reads the existing per-date cache for a past date. No future bar is touched. |
| AG-6 referee verdict for evidence claims | OK | No Evidence Claims introduced — gate passes automatically. |
| AG-7 no credentials in source | OK | Deterministic scan CLEAN over the product diff, tracked and untracked. |
| AG-8 resilience / graceful degradation | OK | Null state_band renders "NA" and does not crash — observed live on three dates, and proven by `test_compass_route_state_band_null_on_pre_iter28_row`. No new whole-table read: `_severity_at` reuses the existing cached per-date reader. |
| AG-9 offline-deterministic ingest | OK | No ingest ran. I re-derived read-only: price frontier still 2026-08-12, `daily_prices` still 3,310,374, `scanner_runs` still 3,128 (max id 3158, newest created 2026-08-26) — all unchanged. |
| AG-10 host resource ceiling | OK | `git status` shows zero changes under `scripts/` and `project-extensions/`; no launch script or host-guard block touched. |
| AG-11 no new composite number | OK | `state_band` is three independent word+delta pairs over existing scalars (regime_score, severity, breadth_above_50dma), never blended; no candidate field changed. |
| AG-12 manifest immutability | OK — re-derived by me | 26 rows, ids 1..26 contiguous (nothing deleted), **zero new rows minted this iteration** (26 before and after — the DoD's own safety item, verified independently), zero rows backfilled (`state_band_json` non-null on 0 rows), and 2025-04-15 v1 still stamped 2026-08-20T11:41:00.381102 exactly as recorded at iter-26/27 (J-05-verify.png). I re-ran `test_manifest_invariants.py` myself: **51 passed**. |
| AG-13 system-vs-market separation | OK | Programmatic scan by the browser lane both directions, plus my own read of the screenshot: "GO"/"Ready" appear only in the top chrome strip and no market word appears there; grep of the new components finds no readiness token. |
| AG-14 no Tapeology coupling | OK | Grepped every changed and new file — no tapeology reference. |
| AG-15 no outcome-tuned selection | OK | Selection rule and thresholds untouched (explicitly out of scope; diff confirms). |
| AG-16 cohorts are not controls | OK | Cohort code untouched; the audit table still labels comparison cohort / near-threshold shadow descriptively. |
| AG-17 repair never rewrites provenance | OK — re-derived by me | `prospective_eligible` true on **zero** of 26 rows; no version, hash or `available_at_utc` changed. |
| AG-18 authorized migration preserves everything | OK — checked closely, see note | This iteration DID permanently alter the canonical table: `ALTER TABLE next_session_manifests ADD COLUMN state_band_json` ran against the live database (the column exists there now). Every protection AG-18 enumerates holds and I verified each: no manifest regenerated, rebound, rehashed, upgraded, deleted or minted; all 26 rows and every stored column value survive; the new column is appended at ordinal 29 with no existing column renamed or reordered (contrast the iter-11 event AG-18 records, which moved `version` from ordinal 9 to 3); no other table's schema touched. AG-18's residual sentence about "schema drift" is written about migrations, and this is the codebase's long-standing additive-column registry. I judged it authorized ordinary work — and logged the interpretation in the assumption ledger so the owner can overrule it. |

**Ledger: 9 total, 0 unresolved — unchanged.** No new violation opened.

One process note that is NOT a violation: the deterministic replay lane drove `as_of` values outside
this iteration's declared safe set (2026-03-30 in J-04's golden, and others), because stored goldens
carry their own baked-in dates. Nothing was minted — I verified the row count is 26 before and after —
so no anti-goal was broken. But the plan's safety wording does not account for the replay lane, and
this is the second iteration running where lane behaviour and plan wording disagreed.

## Next-Step Recommendation

FINISH J-07 "The Today page answers the ten-second read" — make the three direction words actually
appear on screen. The page and its numbers are already right; only the words are missing, and they are
missing because every saved briefing on this database was written before the words existed. The next
iteration should make ONE authorized live request for a date that has no saved briefing yet, so a new
briefing is written with the words in it, and then photograph the page showing real words instead of
"NA". Please note that this request permanently adds one new row to the protected briefings table — the
same kind of addition the owner already accepted at iteration 26 — so the plan must name the exact date
in advance and no other.

RUN IT AT FULL DEPTH. This round was planned as full and ran light for the seventh time this session,
and the light round permanently changed the shape of the protected database table with no independent
checker present. Only the owner can add the `Depth enforcement: required` line that outranks the cost
rule; standing guidance keeps `CHAIN_REQUIRE_FULL_DEPTH` and `CHAIN_MAINTENANCE_ISOLATION` off.

ONE THING THE OWNER SHOULD LOOK AT ON SCREEN, small but real: on the Today page the "What changed" list
and the "Leadership rotation" list below it show the identical sixteen rows, because on this date every
change happens to be a sector, theme or stock. The two sections are honest and read from the same
served field by design, but a reader sees the same list twice. Worth a decision: keep, merge, or
narrow the rotation view.

SIX SMALLER ITEMS, none blocking: (1) J-04's picture still needs re-taking so it includes the candidate
card — tenth round owed, passenger task; (2) J-05, J-06, J-07 and J-08 all still owe a recorded
walkthrough — passenger task, never an iteration goal; (3) the next plan should say that the automatic
re-test lane replays its own stored dates, so the plan's "only these dates" rule must either exempt it
or the goldens must be re-pointed; (4) adding the new words to a briefing changes what the briefing's
content fingerprint covers, so a future re-issue of an old date will no longer produce the same
fingerprint as its earlier versions — expected, but write it down before someone reads it as damage;
(5) the `/market` picture has the cross-view chart collapsed, so the chart itself is not visible in the
image — the next capture should leave it open; (6) J-01's automated re-check still asserts far less than
the journey claims.

FIVE OLDER OWNER QUESTIONS remain open and non-blocking: J-09's ~2.99 GB acceptability; J-06's
"underlying run unavailable" wording; J-01's first two test steps; whether an empty "next-session focus"
is acceptable; whether MNST joins the recovery list. ONE MECHANICAL ITEM: the whole iteration — plan,
handoff, reports, evidence folder, and the three new frontend files — is untracked at scoring time;
confirm it lands. ONE STANDING FRAMEWORK NOTE: `goal_gate.py`'s duplicate-journey-heading defect is
still unfixed and must be closed before any GOAL_ACHIEVED certification.

## Halt Justification (if halting)

Not halting. ESCALATE continues the loop and forces the next iteration to run the full pipeline.
