# Goal-market-compass iter-2 — UI Test Results

**Phase:** goal-market-compass-iter-2
**Date:** 2026-08-20
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All smoke and happy-path tests pass. -->
<!-- Lean-mode scope: J-01, J-02, J-03, J-04 only (per dispatch). -->

**Overall:** 4/4 journeys passed (0 failed, 0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Sector attribution is honest and near-complete on new runs | journey | P1 | Unassigned sector share ≤5% of resolved members on the latest run; two spot-checked names (curated-map + pool-fallback) show matching sector on leaderboard, detail header, and API; /methodology discloses the two-source basis + current-only limitation; a symbol absent from both maps serves null / renders "Unassigned". | 0/539 (0%) Unassigned on run 3081 (2026-08-12) — the Sector dropdown offers no "Unassigned" option because none exist. GRMN = "Consumer Discretionary" matches on the /stocks row, the /stocks/GRMN detail header, and GET /api/stocks/GRMN. DELL = "Technology" confirmed via API. /methodology's "Stock sector labels" card shows the exact two-source + current-only disclosure text. GWW at historical as-of 2026-07-23 (pre-mapping row) serves sector:null and renders "Unassigned" on the leaderboard. Step 1 (destructive Remove+backfill) intentionally NOT re-run — see notes. | PASS | `reports/qa/goal-market-compass-iter-2-evidence/UT-J-01-result.png` |
| UT-J-02 | "What changed" reports meaningful session-over-session deltas with honest empties | journey | P1 | What-changed header names the immediately-preceding stored run + day gap; entries ordered market→breadth→sector→theme→stock, threshold-gated, each linked with the current `?asof`; suppressed-moves disclosure count equals listed entries; a spot-checked sector-rank move and stock-bucket crossing match stored API values; the earliest stored run renders an explicit no-prior-run state. | Header reads "vs 2026-08-11 (1 day ago)" — exactly the row immediately preceding 2026-08-12 in `GET /api/runs`. 17 changes rendered (5 sector + 2 theme + 10 stock; market/breadth suppressed) in the correct order with correct `?asof` drill links. "Suppressed moves (28)" matches 28 listed sub-threshold entries, each magnitude < threshold. ITB (Home Construction) rank 21→25 and SMCI leadership bucket E→D verified byte-exact against `GET /api/sectors` and `GET /api/stocks` at both 2026-08-11 and 2026-08-12. At as-of 1996-02-01 (earliest of 3093 stored runs) the card shows "This is the earliest stored session — there is no prior session to compare against." with 0 changes, 0 suppressed. | PASS | `reports/qa/goal-market-compass-iter-2-evidence/UT-J-02-result.png` |
| UT-J-03 | The plain-English summary is deterministic, cited, and never invents a cause | journey | P1 | Summary renders state/direction/breadth/focus-count sentences verbatim; "Show cited facts" lists each sentence's template_id + facts matching canonical endpoints; no banned-language token anywhere; earliest run shows the no-comparison variant; a historical as-of shows a visible retrospective stamp. | All 4 sentences rendered exactly matching `GET /api/compass`'s narrative. Cited facts (regime_score 73.24, severity 25.84, breadth 59.84%/66.39%) byte-match `GET /api/dashboard` and `GET /api/market-phase` for the same as-of. No banned term (buy/sell/will rise/recommend/because of/etc.) found in any rendered sentence. As-of 1996-02-01 shows "This is the earliest stored session — no prior-session comparison is available." (plus an honest breadth-NA variant). As-of 2026-03-30 and 1996-02-01 both show "This is a retrospective view, reconstructed under the CURRENT selection rule and config — not necessarily what would have rendered live on this date." Two `GET /api/compass` calls for the same `as_of`, minutes apart, returned a byte-identical `content_hash` (`8bb67cd6…`). | PASS | `reports/qa/goal-market-compass-iter-2-evidence/UT-J-03-result.png` |
| UT-J-04 | Every next-session candidate explains why, why-not, and what would change it | journey | P1 | Candidate count matches API + summary focus sentence; a candidate card's words/scores/reasons/cautions/checklist/what-would-change/invalidation match the stored row + config; why-not entries name failed conditions with distances; disposition tally partitions member−candidate count; the shadow cohort never appears; a Risk-off date shows the REGIME_RISK_OFF caution on every candidate; an empty-candidates run shows an explicit state. | Latest as-of (2026-08-12, 0 candidates) shows the explicit `candidates_empty_reason` text live (satisfies the empty-candidates case organically, no fixture needed). As-of 2026-07-23: 1 candidate (GWW) — Leadership "Strong leader (81.2)", Entry "Fair entry (70.3)", Risk "Very low risk (43.3)" all byte-match `GET /api/stocks/GWW`; eligibility checklist is all-Pass and reproduces inclusion; "what would change this" shows the same 3 rows, all "met"; ATR caution "2.23% of price (p17 of universe)" matches `risk_budget.atr_pct`; invalidation text verbatim; disposition tally (539 floor + 0 cap) + 1 candidate = 540 = member count for that date. "Not priority (20)" lists 20 why-not tickers with condition/actual/threshold/distance (e.g. TRV entry_min_score 35.5 vs 70.0, distance 34.5). As-of 2026-03-30 (Risk-off, 10 candidates): every one of the 10 candidate cards carries "REGIME_RISK_OFF: the market regime is Risk-off as of this date — every candidate here is context, not a signal to act."; Market Regime tile reads Risk-off 18.61; no imperative/advice wording anywhere. The near-threshold shadow cohort has no field in the payload and no UI element (component source read confirms it). | PASS | `reports/qa/goal-market-compass-iter-2-evidence/UT-J-04-result.png` |

---

## Passed Tests

### UT-J-01 — Sector attribution is honest and near-complete on new runs
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-2-evidence/UT-J-01-result.png`

- Steps executed: journey steps 2–5 (non-destructive), against the already-existing run 3081 (as-of 2026-08-12), per the iter-2 spec's explicit carve-out — see Notes below for why step 1 was not run.
- Step 2: `/stocks` at latest as-of. The Sector filter's `<select>` options are `__all__` + 11 real GICS-style sectors — **no "Unassigned" option is rendered at all**, confirmed by reading `select.options` directly. Cross-checked at the API layer: `GET /api/stocks?as_of=2026-08-12` returns 539/539 rows with a non-null `sector` — 0.0% Unassigned, comfortably inside the ≤5% acceptance bound (a stronger result than the bound requires).
- Step 3: searched `/stocks` for **GRMN** (pool-fallback example) — leaderboard row shows Sector = "Consumer Discretionary"; opened the GRMN detail page — header badge also shows "Consumer Discretionary"; `GET /api/stocks/GRMN?as_of=2026-08-12` returns `"sector": "Consumer Discretionary"`. All three surfaces agree. **DELL** (curated-map example) confirmed at the API layer: `GET /api/stocks/DELL?as_of=2026-08-12` returns `"sector": "Technology"` (not independently re-clicked through the UI this run, given the GRMN round-trip already proved leaderboard/detail/API agreement end-to-end).
- Step 4: `/methodology` → "Stock sector labels — Data basis" card renders the exact two-source disclosure ("curated `config.stock_sectors` mapping... first, then... a fallback to the sector recorded in the committed candidate pool...") and the current-only limitation sentence, verbatim-matching `config.yaml`'s `methodology.universe_selection.sector_basis` text.
- Step 5: rather than fabricate a symbol, used real data — **GWW** at historical as-of 2026-07-23 (a pre-iter-1 stored row) has `"sector": null` at the API and renders **"Unassigned"** on the `/stocks` leaderboard (not blank, not an error). This is the honest-NA path exercised with genuine data.
- Step 6 (fixture-test citation for byte-identity of scores pre/post the sector wiring) is a dev-handoff/unit-test item, not browser-testable — out of scope for this agent.
- Bonus: `/methodology` also carries the new "Next-session focus — Selection rule" disclosure card (J-04's IN SCOPE frontend item), with live-resolved thresholds (Leadership ≥80, Entry Quality ≥70, Risk ≤60, focus list ≤10) matching `config.yaml`'s `compass.selection.*` exactly.

### UT-J-02 — "What changed" reports meaningful session-over-session deltas with honest empties
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-2-evidence/UT-J-02-result.png`

- Step 1: `/` at latest as-of (2026-08-12) — What-changed header reads "vs 2026-08-11 (1 day ago)". `GET /api/runs` confirms 2026-08-11 (run 3049) is exactly the row immediately preceding 2026-08-12 (run 3081).
- Step 2: 17 change entries rendered, in order Sector×5, Theme×2, Stock×10 (Market/Breadth had zero entries above threshold this session, so they're correctly absent rather than empty-labeled — order market→breadth→sectors→themes→stocks holds for the kinds that qualify); each entry links to its drill surface carrying `?asof=2026-08-12` (verified for sector/theme/stock link hrefs).
- Step 3: "Suppressed moves (28)" — the disclosure's DOM content (verified via markdown extraction, which surfaces `<details>` content regardless of open/closed state) lists exactly 28 entries, each with magnitude < threshold (e.g. market 0.20<5.00, breadth 2.46<5.00/3.28<5.00, nine sector and eight further sector/theme entries all <2.00). Count matches the header exactly. Interactive open/close of the sibling "Show cited facts" `<details>` was separately click-tested and confirmed working (same `Disclosure` component), giving confidence the "Suppressed moves" disclosure is equally interactive.
- Step 4: spot-checked "Home Construction (iShares)" sector rank 21→25 against `GET /api/sectors?as_of=2026-08-11` (rank 21) and `?as_of=2026-08-12` (rank 25); spot-checked "SMCI leadership bucket" E→D against `GET /api/stocks/SMCI` at both dates (34.24/E → 62.70/D, magnitude 28.46 matches the displayed change). Both exact matches.
- Step 5: stepped `?asof=1996-02-01` (the earliest of 3093 stored runs) — card renders "This is the earliest stored session — there is no prior session to compare against." with no deltas and "Suppressed moves (0)".
- Step 6 (fixture citations for the quiet-pair and new-to-universe cases) is a dev-handoff/unit-test item — out of scope for this agent.

### UT-J-03 — The plain-English summary is deterministic, cited, and never invents a cause
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-2-evidence/UT-J-03-result.png`

- Step 1: `/` at latest as-of — all 4 sentences render verbatim: state, direction, breadth, focus_count, matching `GET /api/compass`'s `narrative.sentences` exactly (byte-compared).
- Step 2: opened "Show cited facts" — each sentence lists its `template_id` and facts. Spot-checked `regime_score: 73.24` against `GET /api/dashboard`'s `regime.score` (73.24, exact) and `severity: 25.84` against `GET /api/market-phase`'s `severity` (25.84, exact); also cross-checked `breadth_above_50dma`/`breadth_above_200dma` (59.84/66.39) against `GET /api/dashboard`'s `breadth` block (exact).
- Step 3 (golden byte-identity unit test) is a dev-handoff citation — not directly browser-testable. As a lighter API-level corroboration, two separate `GET /api/compass?as_of=2026-08-12` calls (taken several minutes apart) returned an identical `content_hash` and an identical full payload.
- Step 4: scanned all rendered summary sentences (across all as-of dates visited) against the committed banned-term list (buy, sell, will rise/fall, target price, guaranteed, recommend, act now, because of, caused by) — no match found anywhere.
- Step 5: at as-of 1996-02-01, the direction sentence renders "This is the earliest stored session — no prior-session comparison is available." (the no-comparison variant); the breadth sentence also honestly renders "Breadth data is not available for this session." The NA-velocity warm-up-head fixture is a dev-handoff citation, not reachable via live stored data — out of scope for this agent.
- Step 6: both as-of 2026-03-30 and as-of 1996-02-01 (both pre-frontier historical dates) render the visible retrospective stamp: "This is a retrospective view, reconstructed under the CURRENT selection rule and config — not necessarily what would have rendered live on this date."

### UT-J-04 — Every next-session candidate explains why, why-not, and what would change it
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-2-evidence/UT-J-04-result.png`

- Step 1: at latest as-of (2026-08-12), the focus section, `GET /api/compass`'s `selection.candidates` length, and the summary's focus sentence ("No names are worth monitoring next session…") all agree on 0. At as-of 2026-07-23, all three agree on 1 ("1 name worth monitoring next session.").
- Step 2: opened the GWW candidate card (as-of 2026-07-23) — Leadership "Strong leader (81.2)", Entry "Fair entry (70.3)", Risk "Very low risk (43.3)" match `GET /api/stocks/GWW`'s `leadership.score` 81.24 (bucket B), `entry_quality.score` 70.32, `risk.score` 43.33 (bucket E) and the `compass.vocabulary.*` word maps in `config.yaml` exactly.
- Step 3: reasons cite the exact thresholds and actuals ("Leadership score 81.2 clears the 80.0 floor…" etc.); the ATR caution "2.23% of price (p17 of universe)" matches `risk_budget.atr_pct.value` (2.2286 → 2.23%) and `.percentile` (0.1688 → p17); invalidation "Invalid below the 50-DMA at $1317.45" matches the stored `invalidation.note` verbatim.
- Step 4: eligibility checklist shows `leadership_min_score`/`entry_min_score`/`risk_max_score`, each with threshold + actual and a "Pass" verdict from the fixed set — jointly reproducing the candidate's inclusion (3/3 Pass).
- Step 5: "What would change this" renders the same 3 condition/threshold/actual rows, each "met" — reading only served fields (confirmed by source: `apps/frontend/components/compass-focus-section.tsx` maps only over `candidate.checklist`/`candidate.what_would_change`; no threshold or rule table is defined in the component).
- Step 6: "Not priority (20)" lists 20 tickers with failed_conditions (condition, actual vs threshold, distance) — e.g. TRV `entry_min_score: 35.5 vs 70.0 (distance 34.5)`. Disposition-tally partition verified at the API for both as-of dates tested: 2026-08-12 → `below_selection_floor 539 + excluded_by_cap 0` = 539 = 539 members − 0 candidates; 2026-07-23 → 539 + 0 = 539 = 540 members − 1 candidate. The near-threshold shadow cohort has no key in the `selection` payload and the component renders no such field — confirmed absent from the section both by source read and by live payload inspection.
- Step 7: stepped to as-of 2026-03-30 (`GET /api/regime-history` label "Risk-off", score 18.61) — all 10 rendered candidates (DUK, PPL, LNT, EXC, NI, ATO, CMS, EQIX, WEC, CNP) carry the caution "REGIME_RISK_OFF: the market regime is Risk-off as of this date — every candidate here is context, not a signal to act."; the Market Regime tile reads "Risk-off / 18.61"; no entry-advice wording found anywhere on the page.
- Step 8: the empty-candidates state (`candidates_empty_reason`) was exercised live at the latest as-of (2026-08-12) rather than needing a synthetic fixture — see Step 1 above.

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Notes

- **J-01 step 1 (destructive Remove+backfill) intentionally not executed.** The iter-2 spec (`docs/phases/goal-market-compass-iter-2.md`, BACKGROUND + NOTES) explicitly carves this out: "the non-destructive evidence capture against the already-existing run 3081 rides along as a passenger task" and "this iteration does not depend on it and does not re-attempt the destructive steps." The prior iteration's Remove+backfill already cost the permanent loss of the 2026-08-13/14 bars, and the owner still owes a decision on rewording that precondition in `docs/goal.md`. Steps 2–5 were run in full against the already-existing run 3081 (as-of 2026-08-12) exactly as the spec's own TC-30 describes, so J-01's iter-2 success bar is fully met.
- Frontend was reachable throughout at `http://localhost:3255` (backend at `http://localhost:8255`, confirmed via running-process inspection since the frontend's own `/api/*` paths are Next.js 404s — the frontend calls the backend directly).
- Several journey-step items are dev-handoff/unit-test citations by design (golden byte-identity tests, synthetic fixtures for warm-up-head/quiet-pair/empty-candidates cases, code-audit notes) and are explicitly out of browser-QA's scope; each is called out inline above rather than silently skipped.
- Golden replay scripts written for all 4 PASSing journeys to `runs/goal-session-market-compass/journey-scripts/{J-01,J-02,J-03,J-04}.json`, and lint-checked clean via `demo_runner.py --mode lint`.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), headless, pinned profile
- **Test Date:** 2026-08-20
- **Evidence directory:** `reports/qa/goal-market-compass-iter-2-evidence/`
- **Data basis:** offline seed spine, latest stored run 3081 (as-of 2026-08-12, 539 members)
