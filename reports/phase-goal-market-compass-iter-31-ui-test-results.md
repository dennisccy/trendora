# UI Test Results (merged)

**Date:** 2026-09-01
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 10/10 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Sector attribution is honest and near-complete on new runs | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-31-evidence/J-01-verify.png |
| UT-J-04 | Every next-session candidate explains why, why-not, and what would change it | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-31-evidence/J-04-verify.png |
| UT-J-05 | Each close freezes one provenance-stamped next-session manifest, exported byte-consistently | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-31-evidence/J-05-verify.png |
| UT-J-06 | A frozen manifest never changes — later data, rebuilds, and regeneration are safe | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-31-evidence/J-06-verify.png |
| UT-J-07 | The Today page answers the ten-second read from served values only | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-31-evidence/J-07-verify.png |
| UT-J-08 | The market surface relocates intact and history never lies | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-31-evidence/J-08-verify.png |
| UT-J-10 | Bounded recovery of the two trading days the iter-5 drill deleted | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-31-evidence/J-10-verify.png |
| UT-J-11 | Incident-bounded clean regeneration of derived state (disposable-clone serving verification) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-31-evidence/J-11-verify.png |
| UT-J-02 | "What changed" reports meaningful session-over-session deltas with honest empties | happy-path | P1 | What-changed header names the immediately preceding stored session + gap; entries ordered market→breadth→sector→theme→stock and threshold-filtered; suppressed-count disclosure matches listed entries below threshold; sector-rank and leadership-bucket spot-checks byte-match `GET /api/sectors` / `GET /api/stocks`; earliest stored run renders the explicit no-prior-run empty state with no fabricated deltas | All six steps verified live at frontier `2026-08-12` and earliest `1996-02-01`: header reads "vs 2026-08-11 (1 day ago)", matching `GET /api/runs`' immediately preceding row and a 1-day gap; visible entries are Sector→Theme→Stock (Market/Breadth entries all below threshold this session, honestly absent) each linking `?asof=2026-08-12` to a live drill page; "Suppressed moves (36)" disclosure lists exactly 36 entries, every one strictly below its kind's threshold; Materials sector rank 12→16 and Home Construction 21→25 byte-match `GET /api/sectors?as_of=2026-08-11` / `?as_of=2026-08-12`; SMCI leadership bucket E→D (34.18→62.51, Δ28.33) byte-matches `GET /api/stocks` at both dates; `?asof=1996-02-01` renders "This is the earliest stored session — there is no prior session to compare against." with zero delta entries and `Suppressed moves (0)` | PASS | `reports/qa/goal-market-compass-iter-31-evidence/J-02-whatchanged-suppressed.png` |
| UT-J-03 | The plain-English summary is deterministic, cited, and never invents a cause | happy-path | P1 | Summary card renders state/direction/breadth/focus-count sentences with `data-testid="compass-sentence-<template_id>"`; "Show cited facts" lists every sentence's template id + facts; two facts byte-match `GET /api/dashboard` regime score and `GET /api/market-phase` severity; no banned-language tokens; earliest run shows the no-comparison variant; a pre-frontier historical date shows the visible retrospective stamp | All six steps verified live at frontier `2026-08-12`, earliest `1996-02-01`, and historical `2025-04-15`: four sentences rendered each with `data-testid="compass-sentence-{state,direction,breadth,focus_count}"`, verbatim served text; "Show cited facts" opened and lists `state{regime_label:Risk-on, regime_score:73.18, market_phase:Expansion, severity:25.85}`, `direction{regime_score_delta:-0.26, direction_word:little changed}`, `breadth{...59.84/66.39}`, `focus_count{candidate_count:0.00}` — `regime_score` 73.18 byte-matches `GET /api/dashboard?as_of=2026-08-12` regime.score, `severity` 25.85 byte-matches `GET /api/market-phase?as_of=2026-08-12` severity; no rendered sentence contains any imperative/forecast/causal token; `?asof=1996-02-01` shows "This is the earliest stored session — no prior-session comparison is available." (no direction word, no delta); `?asof=2025-04-15` (an already-manifested retrospective row, version 2) shows "This is a retrospective view, reconstructed under the CURRENT selection rule and config — not necessarily what would have rendered live on this date." plus the Manifest strip's `retrospective` mode badge | PASS | `reports/qa/goal-market-compass-iter-31-evidence/J-03-summary-citedfacts.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-09-01

