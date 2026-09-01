# Goal Iteration 31 — UI Test Results

**Phase:** goal-market-compass-iter-31
**Date:** 2026-09-01
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All smoke and happy-path tests pass -->

**Overall:** 2/2 tests passed (0 skipped)

Lean mode: only J-02 and J-03 were in scope this run (J-01, J-04, J-05, J-06, J-07, J-08, J-10, J-11
are covered separately by the deterministic replay lane per the dispatch instructions).

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-02 | "What changed" reports meaningful session-over-session deltas with honest empties | happy-path | P1 | What-changed header names the immediately preceding stored session + gap; entries ordered market→breadth→sector→theme→stock and threshold-filtered; suppressed-count disclosure matches listed entries below threshold; sector-rank and leadership-bucket spot-checks byte-match `GET /api/sectors` / `GET /api/stocks`; earliest stored run renders the explicit no-prior-run empty state with no fabricated deltas | All six steps verified live at frontier `2026-08-12` and earliest `1996-02-01`: header reads "vs 2026-08-11 (1 day ago)", matching `GET /api/runs`' immediately preceding row and a 1-day gap; visible entries are Sector→Theme→Stock (Market/Breadth entries all below threshold this session, honestly absent) each linking `?asof=2026-08-12` to a live drill page; "Suppressed moves (36)" disclosure lists exactly 36 entries, every one strictly below its kind's threshold; Materials sector rank 12→16 and Home Construction 21→25 byte-match `GET /api/sectors?as_of=2026-08-11` / `?as_of=2026-08-12`; SMCI leadership bucket E→D (34.18→62.51, Δ28.33) byte-matches `GET /api/stocks` at both dates; `?asof=1996-02-01` renders "This is the earliest stored session — there is no prior session to compare against." with zero delta entries and `Suppressed moves (0)` | PASS | `reports/qa/goal-market-compass-iter-31-evidence/J-02-whatchanged-suppressed.png` |
| UT-J-03 | The plain-English summary is deterministic, cited, and never invents a cause | happy-path | P1 | Summary card renders state/direction/breadth/focus-count sentences with `data-testid="compass-sentence-<template_id>"`; "Show cited facts" lists every sentence's template id + facts; two facts byte-match `GET /api/dashboard` regime score and `GET /api/market-phase` severity; no banned-language tokens; earliest run shows the no-comparison variant; a pre-frontier historical date shows the visible retrospective stamp | All six steps verified live at frontier `2026-08-12`, earliest `1996-02-01`, and historical `2025-04-15`: four sentences rendered each with `data-testid="compass-sentence-{state,direction,breadth,focus_count}"`, verbatim served text; "Show cited facts" opened and lists `state{regime_label:Risk-on, regime_score:73.18, market_phase:Expansion, severity:25.85}`, `direction{regime_score_delta:-0.26, direction_word:little changed}`, `breadth{...59.84/66.39}`, `focus_count{candidate_count:0.00}` — `regime_score` 73.18 byte-matches `GET /api/dashboard?as_of=2026-08-12` regime.score, `severity` 25.85 byte-matches `GET /api/market-phase?as_of=2026-08-12` severity; no rendered sentence contains any imperative/forecast/causal token; `?asof=1996-02-01` shows "This is the earliest stored session — no prior-session comparison is available." (no direction word, no delta); `?asof=2025-04-15` (an already-manifested retrospective row, version 2) shows "This is a retrospective view, reconstructed under the CURRENT selection rule and config — not necessarily what would have rendered live on this date." plus the Manifest strip's `retrospective` mode badge | PASS | `reports/qa/goal-market-compass-iter-31-evidence/J-03-summary-citedfacts.png` |

---

## Passed Tests

### UT-J-02 — "What changed" reports meaningful session-over-session deltas with honest empties
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-31-evidence/J-02-whatchanged-suppressed.png`

- Step 1: Loaded `/` (frontier, no `asof` param). What-changed header reads "vs 2026-08-11 (1 day ago)". `GET /api/runs` confirms `run_id 3157 asof_date 2026-08-11` is the row immediately preceding `run_id 3158 asof_date 2026-08-12` — the prior-session anchor and gap are correct.
- Step 2: 17 visible change entries render in order Sector (5) → Theme (2) → Stock (10) — no Market/Breadth entries are visible because both kinds' only candidate moves this session (market Δ0.26, breadth Δ2.46/Δ3.28) sit below their `compass.delta.*` thresholds (5.0) and are correctly demoted to the suppressed list rather than fabricated as changes. Every entry's link (verified via extracted hrefs) carries `?asof=2026-08-12` and resolves (spot-checked `/sectors?asof=2026-08-12` → heading "Sectors"; `/stocks/SMCI?asof=2026-08-12` → heading "SMCI").
- Step 3: Clicked "Suppressed moves (36)" to expand the disclosure. All 36 listed entries show magnitude strictly below threshold (e.g. `Market 0.26 < 5.00`, `Breadth 2.46 < 5.00`, `Sector 1.00 < 2.00` ×19, `Sector 0.00 < 2.00` ×7, `Theme 1.00 < 2.00` ×4, `Theme 0.00 < 2.00` ×5) — count of listed entries (36) equals the header's declared count and the API's `suppressed_count` field (36).
- Step 4: Spot-checked one sector-rank move (Materials 12→16) against `GET /api/sectors?as_of=2026-08-11` (rank 12) and `?as_of=2026-08-12` (rank 16) — byte match. Spot-checked one leadership-bucket crossing (SMCI E→D, magnitude 28.33) against `GET /api/stocks?as_of=2026-08-11` (leadership.score 34.18, bucket E) and `?as_of=2026-08-12` (leadership.score 62.51, bucket D); 62.51−34.18 = 28.33, byte match.
- Step 5: Navigated to `/?asof=1996-02-01` (true earliest stored run, already manifested — no new mint). What-changed card renders "This is the earliest stored session — there is no prior session to compare against.", zero delta entries, `Suppressed moves (0)`, and "Leadership rotation" shows "No sector, theme, or stock rotation this session." — nothing fabricated, no direction words present.
- Step 6 (dev-handoff citation of the fixture test) is outside browser-QA scope; not verified here.

### UT-J-03 — The plain-English summary is deterministic, cited, and never invents a cause
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-31-evidence/J-03-summary-citedfacts.png`

- Step 1: Loaded `/` (frontier). Summary card renders all four sentences: state ("Market regime is Risk-on (73.2/100); market phase is Expansion with calm conditions (severity 25.9/100)."), direction ("Conditions are little changed since the prior session (-0.3 regime-score points)."), breadth ("Universe breadth: 59.8% of the universe above its 50-day average, 66.4% above its 200-day average."), focus_count ("No names are worth monitoring next session (…)"). `document.querySelectorAll('[data-testid^="compass-sentence-"]')` confirmed all four `data-testid="compass-sentence-{state,direction,breadth,focus_count}"` attributes present, text matching the served narrative verbatim.
- Step 2: Clicked "Show cited facts". Disclosure lists each sentence's template id and its facts (`state`, `direction`, `breadth`, `focus_count` — matching JSON keys). Spot-checked `regime_score: 73.18` against `GET /api/dashboard?as_of=2026-08-12` → `regime.score: 73.18` (byte match), and `severity: 25.85` against `GET /api/market-phase?as_of=2026-08-12` → `severity: 25.85` (byte match).
- Step 3 (dev-handoff citation of the golden test) is outside browser-QA scope; not verified here.
- Step 4: Visual/text scan of every rendered sentence at all three tested as-of dates (`2026-08-12`, `2025-04-15`, `1996-02-01`) found no imperative trade verb, forecast term, or causal-attribution phrase — all sentences are descriptive of stored facts and rule names ("clears the … floor", "is little changed", "is not yet available"). The committed banned-language golden test in `test_compass.py` is dev's own citation obligation; this browser pass corroborates the rendered output is clean.
- Step 5: Navigated to `/?asof=1996-02-01`. Summary card renders the no-comparison variant: "This is the earliest stored session — no prior-session comparison is available." in place of a direction sentence — no fabricated direction word.
- Step 6: Navigated to `/?asof=2025-04-15` (a pre-frontier historical date, already carrying manifest version 2 — no new mint). Summary card shows the visible retrospective stamp: "This is a retrospective view, reconstructed under the CURRENT selection rule and config — not necessarily what would have rendered live on this date." The Manifest strip below independently confirms `mode: retrospective`, `version 2`.

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Notes on scope and safety

- Every `/api/compass`-backed page load this run targeted only the three dates the iteration spec
  declares as the safe-mint set: the frontier (`2026-08-12`, no `asof` param), `2025-04-15`, and
  `1996-02-01` — all three confirmed by the spec to already carry manifest rows before this iteration
  started. No other `as_of` value was loaded through `/`. Non-manifest endpoint spot-checks
  (`GET /api/sectors`, `GET /api/stocks`) additionally targeted `2026-08-11` per the iteration's
  explicit allowance (these endpoints carry no manifest and cannot mint anything).
- No source files were modified. No destructive or write actions were taken; all verification was via
  GET requests and read-only browser navigation/clicks.
- Golden replay scripts written/overwritten for both PASSing journeys at
  `runs/goal-session-market-compass/journey-scripts/J-02.json` and `J-03.json`, using only the
  safe-mint-set dates exercised in this run (the prior `J-03.json` golden referenced `?asof=2026-03-30`,
  a date not verified this iteration and not in the declared safe set — replaced with `2025-04-15`,
  which this run did verify). Both lint clean via
  `python3 scripts/automation/lib/demo_runner.py --mode lint --scripts-dir runs/goal-session-market-compass/journey-scripts --journeys J-02,J-03`.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255 (confirmed via `/proc` process list; `NEXT_PUBLIC_API_URL` resolves the frontend's API calls here)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), pinned profile, headless
- **Test Date:** 2026-09-01
- **Evidence directory:** `reports/qa/goal-market-compass-iter-31-evidence/`
