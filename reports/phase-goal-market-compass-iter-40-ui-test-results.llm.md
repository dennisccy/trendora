# Goal Iteration 40 (market-compass) — UI Test Results (LLM browser-qa, lean mode)

**Phase:** goal-market-compass-iter-40
**Date:** 2026-09-02
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- Lean mode: tested exactly J-02, J-09, J-15 per dispatch. J-01, J-03, J-04, J-07, J-08, J-12,
     J-13, J-14 verified separately by deterministic replay this iteration. -->

**Overall:** 3/3 tests passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-02 | "What changed" reports meaningful session-over-session deltas with honest empties | regression | P1 | Header names the prior stored session date + gap; visible changes ordered market→breadth→sectors→themes→stocks and each meets its kind's threshold; suppressed disclosure entries are each below threshold and its count equals the listed entries; a spot-checked sector rank move and a stock leadership-bucket crossing match `GET /api/sectors`/`GET /api/stocks`; the earliest stored run renders an explicit no-prior-run state, nothing fabricated | `/` at latest (2026-08-12) shows "vs 2026-08-11 (1 day ago)"; changes list order is Sector×5, Theme×2, Stock×10 (market/breadth had no qualifying move this pair, consistent — nothing from a later kind appears before an earlier kind); "Suppressed moves (79)" expanded shows 79 entries (1 market + 2 breadth + 24 sector + 9 theme + 43 stock), every entry's shown magnitude is `<` its shown threshold; spot-check: Home Construction (iShares) sector rank 21→25 matches `GET /api/sectors?as_of=2026-08-11/2026-08-12` exactly; SMCI leadership bucket E→D matches `GET /api/stocks` leadership.bucket at both dates exactly; `/?asof=1996-02-01` (earliest stored run) shows "This is the earliest stored session — there is no prior session to compare against.", "Suppressed moves (0)", no market-phase/regime data fabricated (explicit "Not enough history..." / "NA") | PASS | `reports/qa/goal-market-compass-iter-40-evidence/UT-J-02-result.png` |
| UT-J-09 | The backend fits the host — standing memory halves with zero behavior change (backend-only, walkthrough explicitly waived per its own Acceptance) | regression | P1 | `database.pragmas.cache_size` = -65536 in config; live backend VmPeak ≤ 2.5 GB; served values/UI unaffected (zero behavior change) | This journey's own Acceptance waives the Walkthrough/UI requirement ("deliberately backend-only, no UI surface changes") — no dedicated UI journey exists to browser-test, so verified via the same confirmatory pattern as iter-39: `config.yaml:109` shows `cache_size: -65536` (64 MB, annotated "was -262144/256 MB"); live backend (`uvicorn`, pid 4166639, listening on 8255, up 12m29s) `/proc/4166639/status` shows `VmPeak: 2285944 kB` (≈2.18 GB), under the 2.5 GB budget. Browser confirmed zero visible regression: `/` and `/market` both render fully (no error boundary, no "Backend unavailable"), and every value cross-checked during UT-J-02/UT-J-15 (sector ranks, stock buckets, suppressed counts) matched the backend's own API exactly — no evidence of any behavior change from the cache_size shrink. This is a confirmatory spot-check (config value + VmPeak reading + UI cross-check), not the full perf-budget standing-warm drill or the concurrent-load burst test, which are the dev/reviewer's cited responsibility per the journey's own spec | PASS | `reports/qa/goal-market-compass-iter-40-evidence/UT-J-09-result.png` |
| UT-J-15 | "What changed" accounts for every stock-level crossing it already evaluated — nothing above the threshold vanishes and "Suppressed moves" tells the truth (NEW target journey) | happy-path | P1 | Every stock-kind bucket crossing lands in exactly one of shown/suppressed/residual; "Suppressed moves" count now includes the stock kind (43 more); an above-threshold mover held back by the display cap is disclosed as a residual, visibly distinct text from suppressed, count-only (no per-name list); a "showing top N" disclosure appears beside the shown stock entries only when the cap actually held something back | `/` at latest (2026-08-12, manifest v11) shows "Showing the top 10 stock moves" beside the 10 shown stock changes (SMCI, TOL, HUM, KBH, TER, ENTG, V, DRI, OKTA, VRSN); "4 more stock moves held back by the display cap" rendered as a distinct line (different wording/placement from "Suppressed moves"), no per-name list attached; "Suppressed moves (79)" expanded shows exactly 43 Stock-kind rows, each `< 8.00` (the configured `stock_score_min_change`), ranging 7.98→0.26; none of the four named residual movers (TRV, SJM, ALL, TTWO) appear in either the shown-changes list or the suppressed list — confirmed absent from both, consistent with `GET /api/compass` `session_delta.stock_accounting = {evaluated_count:57, shown_count:10, suppressed_count:43, residual_count:4}` (57 = 10+43+4). Older-manifest degrade path not independently re-clicked this run (already verified live in the dev handoff at `/?asof=2025-04-15`) but the absent-field guard is implicitly exercised by every other historical as-of rendering without a residual/shown-cap line (e.g. the 1996-02-01 no-prior-run check above shows neither line) | PASS | `reports/qa/goal-market-compass-iter-40-evidence/UT-J-15-result.png` |

---

## Passed Tests

### UT-J-02 — "What changed" honest deltas re-verification (goal-slice full re-test)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-40-evidence/UT-J-02-result.png`
- Loaded `/` at latest as-of (2026-08-12). What-changed header read "vs 2026-08-11 (1 day ago)" — the prior stored session date, confirmed equal to the immediately preceding row in `GET /api/runs` (asof_date 2026-08-11), gap 1 day.
- Visible changes list (17 entries) ordered Sector→Sector×5, Theme×2, Stock×10 — consistent with the required market→breadth→sectors→themes→stocks ordering (market and breadth had no above-threshold move this pair, so they're correctly absent, never fabricated as present).
- Clicked "Suppressed moves (79)" (count updated from prior iteration's 36, since J-15's fix now correctly counts the stock kind too): all 79 entries shown, each magnitude strictly less than its listed threshold (spot examples: "Market 0.26 < 5.00", "Stock 7.98 < 8.00" ... down to "Stock 0.26 < 8.00"). Count of listed entries (79) equals the disclosed count exactly.
- Spot-check 1 (sector): "Home Construction (iShares) 21 → 25" on screen matches `GET /api/sectors?as_of=2026-08-11` (rank 21) and `?as_of=2026-08-12` (rank 25) exactly.
- Spot-check 2 (stock leadership bucket): "SMCI leadership bucket E → D" on screen matches `GET /api/stocks` leadership.bucket at both as-of dates exactly (E on 2026-08-11, D on 2026-08-12).
- Stepped as-of to `1996-02-01` (earliest stored run reachable that this project's compass treats as having no prior — verified via `GET /api/compass?as_of=1996-02-01` returning `prior_as_of: null`): rendered "This is the earliest stored session — there is no prior session to compare against.", "Suppressed moves (0)", "This is the earliest stored session — there is no prior session to compare rotation against." — no deltas, no direction words, nothing fabricated. Market phase/breadth also explicitly rendered "Not enough history..." / "NA" rather than any invented value.

### UT-J-09 — Backend memory-fit re-verification (backend-only, walkthrough waived)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-40-evidence/UT-J-09-result.png`
- `config.yaml` line 109 confirms `database.pragmas.cache_size: -65536` (the J-09 target value, 64 MB/connection, annotated as changed from -262144/256 MB).
- Live backend (uvicorn pid 4166639 on port 8255) `/proc/4166639/status` reports `VmPeak: 2285944 kB` (≈2.18 GB) — within the ≤2.5 GB budget.
- Browsed `/` and `/market`: both render fully with correct data (GO preflight, real regime/phase/breadth/candidate content), no error boundary, no degraded/unavailable state — zero visible behavior change from the memory config shrink.
- Every displayed value cross-checked in UT-J-02/UT-J-15 (sector ranks, stock leadership buckets, suppressed/residual counts) matched the backend's live API responses exactly, corroborating "served values unaffected."

### UT-J-15 — Stock-kind What-changed accounting (NEW journey, full goal-slice verification)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-40-evidence/UT-J-15-result.png`
- At the regenerated frontier manifest (`/`, 2026-08-12, manifest strip shows "version 11"), the What-changed card renders "Showing the top 10 stock moves" immediately after the 10 shown stock entries, and "4 more stock moves held back by the display cap" as a separate, visibly distinct line (different wording, no per-name list) below the "Suppressed moves" disclosure.
- Expanded "Suppressed moves (79)": exactly 43 rows tagged "Stock", each with magnitude `< 8.00` (compass.delta.stock_score_min_change), ranging from 7.98 down to 0.26 — confirms the suppressed count now genuinely includes every below-threshold stock crossing (was 0 stock-kind rows before this iteration's fix).
- Confirmed the four named above-threshold movers this iteration's build cites as previously vanishing — TRV (8.66), SJM (8.48), ALL (8.33), TTWO (8.14) — do not appear anywhere in the visible 10-item shown list nor in the 43-item suppressed list, consistent with them being the 4 counted in `residual_count`.
- Cross-checked against `GET /api/compass?as_of=2026-08-12`: `session_delta.stock_accounting = {evaluated_count: 57, shown_count: 10, suppressed_count: 43, residual_count: 4}`; identity 10+43+4=57 holds exactly, matching both the rendered counts and the goal spec's cited baseline numbers.
- Top-level `suppressed_count` (79) = sector 24 + theme 9 + breadth 2 + market 1 + stock 43, matching the goal text's TC-4 expectation exactly.

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Golden Replay Scripts

Per goal-mode lean-mode instructions, wrote/updated self-contained deterministic replay scripts to
`runs/goal-session-market-compass/journey-scripts/`:

- **`J-02.json`** (updated) — step 2's click target updated from the stale `"Suppressed moves (36)"`
  to the current `"Suppressed moves (79)"` (the count this iteration's J-15 fix corrected by adding
  the stock kind); the `"0.26 < 5.00"` expect text was unaffected (still the market-kind suppressed
  entry) and needed no change.
- **`J-09.json`** (new — REQUIRED deliverable per dispatch). J-09's own Acceptance waives the
  Walkthrough/UI requirement (deliberately backend-only, no UI surface). No UI action can assert the
  VmPeak/config claims a replay script is limited to `goto`/`click`/`fill` + text assertions, so this
  golden is a **UI-render smoke check only** — it re-confirms `/` and `/market` both render their
  stable static copy (no crash / no "Backend unavailable" state), which is a real but partial signal:
  it would catch a regression that breaks the page, but it can NOT catch a memory-budget regression
  itself (VmPeak still requires a `/proc/<pid>/status` read, which stays an LLM/bash re-verification
  step every iteration this journey is checked, same as prior iterations).
- **`J-15.json`** (new) — asserts the two new disclosure lines ("Showing the top 10 stock moves",
  "4 more stock moves held back by the display cap"), the corrected "Suppressed moves (79)" count, and
  (after clicking it open) a stock-kind suppressed entry ("7.98 < 8.00") to confirm the stock kind is
  now present in the disclosure.

All three lint clean via
`python3 scripts/automation/lib/demo_runner.py --mode lint --scripts-dir runs/goal-session-market-compass/journey-scripts --journeys J-02,J-09,J-15`
→ `J-02 ok`, `J-09 ok`, `J-15 ok`.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chromium (headless, Chrome MCP, pinned profile)
- **Test Date:** 2026-09-02
- **Evidence directory:** `reports/qa/goal-market-compass-iter-40-evidence/`
- **Manifest under test:** `next_session_manifests` v11 for as_of 2026-08-12 (minted by this iteration's
  authorized `POST /api/compass/regenerate` call per the dev handoff)
