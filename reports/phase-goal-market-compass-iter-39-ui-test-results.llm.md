# Phase goal-market-compass-iter-39 — UI Test Results

**Phase:** goal-market-compass-iter-39
**Date:** 2026-09-02
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 13/13 tests passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Today page loads at latest date | smoke | P1 | Heading "Today", subtitle, "Data as-of 2026-08-12" badge, all cards render, no error card | All present; all cards (Market state, Summary, What changed, Rotation, Next-session focus, Manifest strip) rendered; no error card; no console errors | PASS | `reports/qa/goal-market-compass-iter-39-evidence/UT-01-result.png` |
| UT-02 | Pre-iter-38 date renders + degraded text | happy-path | P1 | No crash at `?asof=2026-08-11`; disclosure reads "Not priority (20 shown — held-back counts unavailable for this manifest version)"; no "ranked #N ... cap" lead-in; entries still show own detail | Page rendered fully, no crash. Disclosure text byte-matches expected exactly. Expanded list shows each entry's own `entry_min_score`/`risk_max_score` advisory distances (the honest per-entry detail); no "ranked #N of the above-floor names" lead-in appeared anywhere | PASS | `reports/qa/goal-market-compass-iter-39-evidence/UT-02-result.png` |
| UT-03 | Frontier date text unchanged | happy-path | P1 | Disclosure reads "Not priority (20 shown of 52 held back — 27 cap-excluded, 25 below-floor near-miss)"; at least one entry shows "ranked #N ... cap 20" lead-in with real numbers | Disclosure text byte-matches exactly. Expanded list shows e.g. "DXCM — ranked #11 of the above-floor names, cap 10" — real, non-blank rank+cap. Note: test-plan text literally said "cap 20"; the served/rendered cap value is 10, cross-checked against `GET /api/compass?as_of=2026-08-12` selection.why_not[0].cap = 10 (matches `max_candidates`=10, i.e. the number of actual candidate cards shown, 10). This is the correct served value (AG-3 satisfied) — the test plan's literal "20" appears to be an authoring mix-up with the unrelated `why_not_cap`=20 display limit, not a product defect; unchanged from before this iteration since backend is untouched | PASS | `reports/qa/goal-market-compass-iter-39-evidence/UT-03-result.png` |
| UT-04 | Backend-unreachable error card | error | P2 | Red "Backend unavailable" card with exact caveat text; no blank page/crash screen | Backend stopped (SIGTERM), health check returned connection failure. Frontend showed exact text: "Backend unavailable" / "NO-GO — do not rely on today's board." / "The Today page could not load the market regime from the API. Nothing is fabricated — confirm the backend is running and reload." No blank page, no Next.js crash screen. Backend restarted via `scripts/start-backend.sh` afterward; confirmed healthy (200) before continuing | PASS | `reports/qa/goal-market-compass-iter-39-evidence/UT-04-result.png` |
| UT-05 | J-04 candidate reasoning click-through | regression | P1 | "Strong leader (81.2)" at 2026-07-23; "TRV" in expanded Not-priority list; "REGIME_RISK_OFF" at 2026-03-30 | All three assertions confirmed in order, no error card at any step. Candidate GWW's served leadership/entry/risk (81.24/70.32/43.33 from `GET /api/compass`) matches displayed "81.2"/"70.3"/"43.3" exactly | PASS | `reports/qa/goal-market-compass-iter-39-evidence/UT-05-result.png` |
| UT-06 | J-05/J-06 manifest immutability | regression | P1 | "MCD" ticker, "Basis: available", exact timestamp `2026-08-20T11:41:00.381102+00:00` all visible on first load and reload | All three values present, byte-identical, before and after F5 reload. No error card | PASS | `reports/qa/goal-market-compass-iter-39-evidence/UT-06-result.png` |
| UT-07 | J-07 ten-second read + market link | regression | P1 | "Risk-on", exact breadth sentence, market-link navigation to `/market` with "severity-velocity line", 3 direction-word testids = "little changed", `?asof=2026-08-03` improving sentence | All assertions confirmed in order: "Risk-on" visible; exact breadth sentence matched; market link navigated and "severity-velocity line" text found; regime/stress/breadth-direction testids all read "little changed"; `/?asof=2026-08-03` showed exact text "Conditions are improving since the prior session (+4.7 regime-score points)." | PASS | `reports/qa/goal-market-compass-iter-39-evidence/UT-07-result.png` |
| UT-08 | 21-date crash-free loop | regression | P1 | None of 21 dates shows error card; all 21 `GET /api/compass?as_of=<date>` return 200 | All 21 curl calls returned 200. All 21 page loads checked via DOM (`document.body.innerText.includes('Something went wrong')` = false on every date, several also verified via full-text extraction) — zero error cards across the full previously-crashing date set | PASS | `reports/qa/goal-market-compass-iter-39-evidence/UT-08-result.png` |
| UT-09 | J-14 full why-not list, not cropped | happy-path | P1 | Screenshot shows ≥1 cap-excluded name (rank+cap legible) and ≥1 below-floor near-miss name (floor+distance legible), neither cropped | Full-page screenshot (measured with PIL — 1668×5416px, cropped region visually verified, not credited from filename) shows the complete 20-entry list from DXCM (#11, cap-excluded, "ranked #11 of the above-floor names, cap 10") through BKNG (20th/last entry, below-floor near-miss, "leadership_min_score: 78.4 vs 80.0 (distance 1.6)"), both fully legible and not cut off; the details panel's closing border is visible below the last entry | PASS | `reports/qa/goal-market-compass-iter-39-evidence/UT-09-result.png` |
| UT-10 | Zero-extra-nav discoverability | ux | P2 | "Not priority" visible on home page with 0 extra navigation; click expands in place, no navigation/new tab | Confirmed present in home page DOM without any click (`document.querySelectorAll('summary')` found it directly). After clicking, `window.location.href` unchanged (`http://localhost:3255/`) and tab count unchanged (single tab) — expansion is in-place | PASS | `reports/qa/goal-market-compass-iter-39-evidence/UT-10-result.png` |
| UT-J-04 | J-04: candidate reasoning, why-not, Risk-off caution (goal-slice full re-verify) | regression | P1 | Candidate count matches API; word-map labels correct; ATR caution + invalidation cite stored values; eligibility checklist verdicts; why-not entries name failed conditions w/ distances; shadow cohort never in focus section; REGIME_RISK_OFF caution at Risk-off dates | Re-confirms UT-05 plus additional spot-checks: at 2026-07-23, 1 candidate (GWW) matches summary's "1 name worth monitoring" and API's `len(candidates)==1`; leadership/entry/risk scores (81.24/70.32/43.33) match UI (81.2/70.3/43.3) exactly. At 2026-08-12, eligibility checklist shows fixed-vocabulary verdicts (Pass/Miss) with threshold+actual; "what would change this" panel states rules with met/not-met; why-not entries name `entry_min_score`/`risk_max_score`/`leadership_min_score` with distances; near-threshold shadow cohort renders only in a separate "research-only" audit table, never inside Next-session focus. At 2026-03-30 (Risk-off), all 10 candidates carry REGIME_RISK_OFF caution and market band reads "Risk-off". At 2026-08-11, explicit `candidates_empty_reason` text renders ("No stored member cleared the selection rule...") instead of a bare empty list. Golden script `J-04.json` already matches (lints clean, byte-restored) — no repair needed; the replay lane's flagged possible-regression is stale/resolved | PASS | `reports/qa/goal-market-compass-iter-39-evidence/UT-05-result.png` |
| UT-J-09 | J-09: backend memory fits host budget (config-only, backend-only — walkthrough explicitly waived per its own spec) | regression | P1 | `database.pragmas.cache_size` = -65536 in config; live backend VmPeak ≤ 2.5 GB; served values unaffected | This journey's own Acceptance explicitly waives the Walkthrough/UI requirement ("deliberately backend-only (no UI surface changes)"); no UI journey exists to browser-test. Confirmed via available tooling instead: `config.yaml` line 109 shows `cache_size: -65536` (64 MB, the J-09 target, annotated "was -262144/256 MB"); live backend (freshly restarted this run for UT-04) `/proc/<pid>/status` shows `VmPeak: 2477024 kB` (≈2.42 GB), under the 2.5 GB budget. Backend served correct, consistent values throughout this entire QA run (21/21 dates 200 OK, all displayed values cross-checked against `/api/compass` matched) — no evidence of any regression from the cache_size change. This is a confirmatory spot-check, not the full perf-budget standing-warm drill methodology (that measurement is the dev/reviewer's responsibility per the journey's own citation requirement) | PASS | n/a (backend-only; VmPeak reading captured in this report's Actual column) |
| UT-J-14 | J-14: why-not names its real reason, near-miss names restored (goal-slice full re-verify) | happy-path | P1 | Zero why-not entries claim a qualifier pass the stored row contradicts; both cap-excluded and below-floor reason classes appear when both exist; disclosed per-reason counts equal uncapped totals; shadow cohort never in focus section | Re-confirms UT-03/UT-09 plus the "false positive" fix: at 2026-08-12, all 20 why-not entries show at least one advisory-qualifier-miss line (e.g. DXCM `entry_min_score: 26.5 vs 70.0`) — none renders the old "passed every qualifier, cut only by cap" false claim. Both reason classes present: 10 cap-excluded (ranked #11–20, cap 10) and 10 below-floor near-miss (leadership_min_score distance shown, e.g. BKNG distance 1.6). Disclosure header "20 shown of 52 held back — 27 cap-excluded, 25 below-floor near-miss" matches uncapped totals from `GET /api/compass` `why_not_totals` (`excluded_by_cap_uncapped: 27`, `below_floor_in_band_uncapped: 25`). Shadow cohort renders only in the separate "Near-threshold shadow — research-only substrate, not part of selection or display ranking" audit table, confirmed absent from the Next-session focus section itself. Golden script `J-14.json` already matches (lints clean) — no repair needed | PASS | `reports/qa/goal-market-compass-iter-39-evidence/UT-09-result.png` |

---

## Passed Tests

### UT-01 — Today page loads at latest date
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-39-evidence/UT-01-result.png`
- Navigated to `/`. Heading "Today", subtitle "The ten-second read after the close", badge "Data as-of 2026-08-12" all visible. All six cards (Market state, Summary, What changed, Leadership rotation, Next-session focus, Manifest strip) rendered with real content. No "Something went wrong" or "Backend unavailable" card anywhere.

### UT-02 — Pre-iter-38 date renders + degraded text
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-39-evidence/UT-02-result.png`
- `/?asof=2026-08-11` (a genuine pre-iter-38 row, confirmed lacking `why_not_totals`) rendered in full with no crash — this is the exact AG-8 scenario iter-39 repairs. Disclosure summary read exactly "Not priority (20 shown — held-back counts unavailable for this manifest version)". Expanding it showed each of the 20 entries with its own `entry_min_score`/`risk_max_score` advisory-distance detail and zero "ranked #N ... cap" lead-in sentences anywhere.

### UT-03 — Frontier date text unchanged
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-39-evidence/UT-03-result.png`
- `/?asof=2026-08-12` disclosure text byte-matches "Not priority (20 shown of 52 held back — 27 cap-excluded, 25 below-floor near-miss)" exactly. Expanded list shows real rank+cap lead-ins (e.g. "DXCM — ranked #11 of the above-floor names, cap 10") — cross-verified against the live `GET /api/compass` payload, confirming the served `cap` field genuinely is 10 (equal to `max_candidates`, the 10 rendered candidate cards), not the test plan's literal "cap 20" example. Recorded as a test-plan authoring note, not a functional defect — the byte-identical acceptance criterion (the disclosure summary string) is met exactly.

### UT-04 — Backend-unreachable error card
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-39-evidence/UT-04-result.png`
- Stopped the live backend process with `kill -TERM`. Reloaded `/`; within 15s the page showed the exact expected error card text. No blank page, no framework crash screen. Restarted backend via `scripts/start-backend.sh` with the original `CHAIN_BACKEND_PORT=8255`/`CHAIN_FRONTEND_PORT=3255`/`CORS_ORIGINS` env, confirmed `/api/health` returned 200 before continuing.

### UT-05 — J-04 candidate reasoning click-through
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-39-evidence/UT-05-result.png`
- All three text assertions (Strong leader (81.2), TRV in expanded list, REGIME_RISK_OFF) confirmed in order with no error card. Also superseded and extended by UT-J-04 below.

### UT-06 — J-05/J-06 manifest immutability
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-39-evidence/UT-06-result.png`
- `/?asof=2025-04-15`: MCD, "Basis: available", and the exact provenance timestamp `2026-08-20T11:41:00.381102+00:00` (v1's frozen timestamp in the versions table) all present. Reloaded page (full navigate re-fetch); all three values byte-identical on the second load.

### UT-07 — J-07 ten-second read + market link
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-39-evidence/UT-07-result.png`
- "Risk-on" and the exact breadth sentence confirmed on `/`. Clicked the `compass-state-band-market-link` testid; navigated to `/market` and "severity-velocity line" text found in the cross-view chart description. Returned to `/`; all three direction testids (regime/stress/breadth) read "little changed". `/?asof=2026-08-03` showed the exact improving sentence.

### UT-08 — 21-date crash-free loop
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-39-evidence/UT-08-result.png`
- All 21 `curl http://localhost:8255/api/compass?as_of=<date>` calls returned 200. All 21 `/?asof=<date>` page loads checked (several via full page-text extraction, the rest via a DOM check for the absence of "Something went wrong") — zero crashes across the full previously-crashing set, including the earliest stored session (1996-01-02, which renders honest NA/empty states, not a crash).

### UT-09 — J-14 full why-not list, not cropped
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-39-evidence/UT-09-result.png`
- Took a full-document screenshot (`fullpage: true`, 1668×5416px, confirmed via `PIL.Image.open().size`), then cropped and visually verified the "Not priority" details region (measured bounding box, not credited from filename). All 20 entries visible: DXCM through STT (10 cap-excluded, "ranked #N ... cap 10") then EXPE through BKNG (10 below-floor near-miss, "leadership_min_score ... distance ..."). BKNG (20th, last) is fully legible with the panel's closing border visible beneath it — not cropped.

### UT-10 — Zero-extra-nav discoverability
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-39-evidence/UT-10-result.png`
- On `/` with zero clicks, `document.querySelectorAll('summary')` found the "Not priority (...)" element directly in the DOM (only scrolling needed). After clicking it, `window.location.href` was unchanged and no new tab opened (`list_tabs` still showed 1 tab) — expansion happens in place.

### UT-J-04 — J-04 full goal-slice re-verification
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-39-evidence/UT-05-result.png`
- See Results Table for full detail. Candidate count/scores cross-checked against `GET /api/compass` and matched exactly (AG-3). Eligibility checklist, "what would change this", why-not distances, Risk-off caution persistence, and the `candidates_empty_reason` honest-empty state all confirmed rendering correctly. Shadow cohort confirmed absent from the focus section. Golden script `J-04.json` already correct (lints clean) — the replay lane's flagged possible-regression on J-04 is resolved/stale.

### UT-J-09 — J-09 backend memory-fit re-verification (backend-only, walkthrough waived)
**Verdict:** PASS
**Evidence:** n/a (see Actual column; VmPeak reading and config value captured directly in this report)
- `config.yaml` confirms `database.pragmas.cache_size: -65536`. Live backend VmPeak measured at 2,477,024 kB (≈2.42 GB) ≤ 2.5 GB budget. Backend served correct, byte-consistent values throughout this entire QA session with zero errors.

### UT-J-14 — J-14 full goal-slice re-verification
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-39-evidence/UT-09-result.png`
- See Results Table for full detail. Zero why-not entries claim a false qualifier pass (all 20 entries at 2026-08-12 carry at least one named advisory-qualifier-miss). Both cap-excluded and below-floor near-miss reason classes present when both exist. Disclosed uncapped totals (27/25) match `GET /api/compass` `why_not_totals` exactly. Shadow cohort confirmed absent from the focus section. Golden script `J-14.json` already correct (lints clean) — the replay lane's flagged possible-regression on J-14 is resolved/stale.

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`, headless, pinned profile)
- **Test Date:** 2026-09-02
- **Evidence directory:** `reports/qa/goal-market-compass-iter-39-evidence/`
- **Note:** Backend was deliberately stopped (`kill -TERM`) for UT-04 and restarted via `scripts/start-backend.sh` with the original `CHAIN_BACKEND_PORT=8255`/`CHAIN_FRONTEND_PORT=3255`/`CORS_ORIGINS` environment before continuing with remaining tests; health confirmed (200) before resuming.
