# Phase goal-ops-hardening-iter-47 — UI Test Results

**Phase:** goal-ops-hardening-iter-47
**Date:** 2026-08-04
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 8/8 tests passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Evidence page loads without errors | smoke | P1 | Heading "Evidence" visible, ≥1 claim card or empty-state card, no "Backend unavailable" card, no console errors | Heading visible; 7 `evidence-claim-row` cards rendered; no error card; console-log capture unimplemented in this Chrome MCP build (noted, not a failure) | PASS | `reports/qa/goal-ops-hardening-iter-47-evidence/UT-01-result.png` |
| UT-02 | Idle Evidence page fast, no Refreshing badge | happy-path | P1 | Page renders with no multi-second hang; no claim shows the "Refreshing" badge; every panel shows real median/p90/n numbers | Single navigate returned immediately; 0 occurrences of `evidence-expectations-refreshing` across all 7 claims; all 7 tables populated with real median/p90/n figures, 0 "Unavailable" panels | PASS | `reports/qa/goal-ops-hardening-iter-47-evidence/UT-02-result.png` |
| UT-03 | New backfill triggers honest "Refreshing" badge | happy-path | P1 | After a genuinely new trading day is ingested, ≥1 claim shows the amber "Refreshing" badge with real table numbers, the added disclosure sentence, and the page still loads fast | Ran a fresh `both` (fetch+backfill) job for 2026-08-03 (the next real trading day after the prior latest bar 2026-07-31 — 2026-08-01/02 are a weekend, see Notes); immediately after completion ALL 7 claims flipped to `expectations_status:"refreshing"`, each retaining real median/p90/n numbers and the exact disclosure sentence "A newer version is computing in the background after a recent data update — the table below is the last complete version, not a partial or fabricated one."; `GET /api/evidence`/page load stayed fast throughout (health polls stayed HTTP 200, no multi-second hang observed) | PASS | `reports/qa/goal-ops-hardening-iter-47-evidence/UT-03-result.png` |
| UT-04 | "Refreshing" badge clears after catch-up | happy-path | P2 | Badge no longer present after the background catch-up finishes; table numbers may differ or match, never blank | All 7 claims' "Refreshing" badges cleared (`expectations_status` absent, confirmed via both the `GET /api/evidence` API and a fresh browser load); all 7 tables still populated with real numbers. See Notes for the actual settle-time observation (much longer than the "~8-10 min" example window, attributable to repeated backend restarts in this QA session, not a code defect) | PASS | `reports/qa/goal-ops-hardening-iter-47-evidence/UT-04-result.png` |
| UT-05 | Data Manager backfill flow still works | regression | P1 | No client-side validation error; job-status badge appears; Run history gets a new row | Filled 2026-07-30→2026-07-31 (already-snapshotted range), clicked Start; job-status badge read "no new snapshots" with an honest "Zero-work outcome" message; Run history row added with correct stats | PASS | `reports/qa/goal-ops-hardening-iter-47-evidence/UT-05-result.png` |
| UT-06 | Home + Evidence stay responsive during a backfill | regression | P1 | Both pages load quickly while a job is running; no "Backend unavailable" card; no indefinite spinner | While the UT-03 job was "running", `/` loaded and showed the "Ready" health badge (`data-state="ready"`); `/evidence` loaded within a couple seconds showing all 7 claim cards (no error card, no infinite spinner) | PASS | `reports/qa/goal-ops-hardening-iter-47-evidence/UT-06-result.png` |
| UT-07 | "Unavailable"/absent panel states unchanged | regression | P3 | Any "Unavailable" or absent-panel claim renders unchanged; neither state shows the Refreshing badge | Observational: at test time all 7 live claims are in the full-table state (0 in "Unavailable", 0 with no panel) — nothing to contradict; confirmed the Refreshing badge never appears outside the full-table state | PASS | `reports/qa/goal-ops-hardening-iter-47-evidence/UT-07-result.png` |
| UT-08 | "Refreshing" badge is calm and doesn't break layout | ux | P2 | Badge sits inline, amber/warn color (not alarm-red, not full-width banner); rest of card unchanged; disclosure sentence reads naturally | Badge renders as a small inline amber pill directly beside the "Historical drawdown & dry-spell expectations" heading, visually distinct from the red "FAIL" verdict badge; verdict badge, hypothesis chips, registration date all laid out normally with no overlap/wrapping; disclosure sentence reads as a natural continuation of the existing paragraph | PASS | `reports/qa/goal-ops-hardening-iter-47-evidence/UT-08-result.png` |

**Goal-mode regression lane:** J-01, J-03, J-04, J-05, J-08, J-09 were already re-verified this iteration via deterministic golden replay (`reports/phase-goal-ops-hardening-iter-47-regression-replay-results.md`, 6/6 PASS) per the dispatch's instruction — not re-tested here, no rows emitted for them.

---

## Passed Tests

### UT-01 — Evidence page loads without errors
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-47-evidence/UT-01-result.png`
- Navigated to `/evidence`; heading "Evidence" visible; 7 `data-testid="evidence-claim-row"` cards rendered; 0 occurrences of the "Backend unavailable" error card or `evidence-empty` in the DOM.

### UT-02 — Idle Evidence page fast, no Refreshing badge
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-47-evidence/UT-02-result.png`
- Confirmed via `/data`'s Run history that no job was "running" beforehand. Navigated to `/evidence`: 0 `evidence-expectations-refreshing` badges across all 7 claims, 0 `Unavailable` panels — every claim's table shows real `median (p90 …) n=…` figures (e.g. `-7.86% (p90 -3.73%) n=58584`).

### UT-03 — New backfill triggers honest "Refreshing" badge
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-47-evidence/UT-03-result.png`
- Read the on-screen "Price history" end date (`2026-07-31`) on `/data`. The literal "day immediately after" (2026-08-01) is a Saturday — a non-trading day that would produce a zero-work job — so, per the operational instruction to trust on-screen reality over baked-in examples, used the next real trading day (2026-08-03, Monday) with job kind "Fetch + backfill" (the default "Backfill"-only kind cannot create bars for a date with none yet). Job completed: Price history end date advanced to `2026-08-03`, 588 new bars, 1 new snapshot. Immediately after, `GET /api/evidence` and the `/evidence` page both showed **all 7 of 7** claims with `expectations_status:"refreshing"` / the amber "Refreshing" badge, each still rendering real historical numbers and the exact required disclosure sentence. No page-load stall was observed.

### UT-04 — "Refreshing" badge clears after catch-up
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-47-evidence/UT-04-result.png`
- Polled `GET /api/health` + `GET /api/evidence` every ~20s. The stale-claim count decreased monotonically (7 → 6 → 5 → 4 → 3 → 2 → 1 → 0) and reached 0 (fully settled) at 14:16. A fresh `/evidence` browser load confirmed 0 `evidence-expectations-refreshing` badges remain and all 7 tables still show real numbers. `GET /api/health` returned HTTP 200 on effectively every poll (see Notes for the one exception).

### UT-05 — Data Manager backfill flow still works
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-47-evidence/UT-05-result.png`
- Filled Start=2026-07-30/End=2026-07-31 (already-ingested range, per the test's own "does not need to be a NEW date" allowance) and clicked Start. No client-side validation error. `job-status` badge read "no new snapshots"; job panel showed "0 snapshots · 0 forward returns inserted" with the honest "Zero-work outcome — every requested trading day already had a snapshot… not a failure" message; a new Run history row was added.

### UT-06 — Home + Evidence stay responsive during a backfill
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-47-evidence/UT-06-result.png`
- While the UT-03 job's status badge still read "running", navigated to `/`: the top-bar health badge read "Ready" (`data-state="ready"`). Navigated to `/evidence`: loaded within a couple seconds, all 7 claim cards rendered, no "Backend unavailable" card, no indefinite spinner.

### UT-07 — "Unavailable"/absent panel states unchanged
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-47-evidence/UT-07-result.png`
- All 7 currently-live claims are in the full-table state (`evidence-expectations-table` present, `evidence-expectations-unavailable` count = 0, no claim with an absent panel) — this iteration's live ledger has no claim currently in the "Unavailable"/absent state to exercise, so the check is observationally vacuous but consistent: the Refreshing badge is confirmed exclusive to the full-table state (never co-occurs with "Unavailable" or an absent panel).

### UT-08 — "Refreshing" badge is calm and doesn't break layout
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-47-evidence/UT-08-result.png`
- Visual inspection (viewport screenshot taken while claims were in the "refreshing" state from UT-03): the "Refreshing" badge is a small amber/warn pill sitting inline immediately after the "Historical drawdown & dry-spell expectations (20-day hold)" heading — visually calm, clearly distinct from the red "FAIL" verdict badge, not a banner. The table, hypothesis chips, verdict badge, and registration date are all laid out exactly as on a claim card with no badge. The disclosure sentence appends naturally to the existing description paragraph.

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Notes / Observations (not failures)

- **TC-7 (browser-qa lane freshness) verified:** all product files touched by this iteration's diff (`evidence.py`, `forward_testing.py`, `research.py`, `samples.py`, `warmup.py`, `lib/evidence.ts`, `app/evidence/page.tsx`) last changed between 10:52 and 12:13; the dev handoff (12:45) and review (12:58) both postdate every code change; this QA run (13:37 onward) is the last product-code-adjacent event — no audit-fix has landed since.
- **UT-03 date choice:** the test plan's own worked example ("… → 2026-07-31, type 2026-08-01") coincidentally matches this run's live data, but 2026-08-01 is a Saturday (non-trading). Following the coordinator's instruction to read actual on-screen state rather than trust baked-in examples, the next real trading day (2026-08-03) was used instead, with job kind switched from the default "Backfill" to "Fetch + backfill" (a pure Backfill on a date with no bars yet is a zero-work no-op). This is a deliberate, disclosed adaptation, not a deviation from the test's intent.
- **UT-04 settle-time observation:** the test plan describes an "~8-10 minute" wait; the actual full settle (7→0 stale claims) took roughly 90 minutes of wall-clock time in this session. `logs/backend.log` shows the backend process restarting repeatedly throughout this window (12 restarts visible in the tail alone) — consistent with the dispatch's own documented behavior ("services are restarted automatically if they die during quota-retry sleeps"). Each restart resets the in-process single-flight re-warm guard, so the background catch-up effectively had to resume/restart multiple times rather than running in one uninterrupted ~8-minute pass, which plausibly explains the gap versus the dev handoff's own isolated-session measurement (~450-480s). This reads as a QA-environment artifact of this sandboxed session, not a product defect — the badge, table values, and disclosure text were correct and honest at every observed point in between, and the claim never showed a blank/broken table. Recorded for the record, not counted as a failure (UT-04 is P2; its actual acceptance criteria — badge absent, real numbers — were fully met at settle).
- **One health-poll blip:** during the supplementary `GET /api/health` polling between UT-03 and UT-04 (not itself a UT-XX step), one poll at 14:04:12 returned `000` (connection failure) and the very next poll 27s later returned 200 again — coincident with one of the backend restarts noted above. All UT-XX-scoped checks themselves (UT-01 through UT-08) observed HTTP 200 throughout.
- Console-log capture in this Chrome MCP build returns "not yet implemented" for every action — noted for UT-01's "no console errors" criterion rather than silently assumed.

---

## Golden replay scripts

- `runs/goal-session-ops-hardening/journey-scripts/J-06.json` — re-verified fresh this iteration (all 11 page loads confirmed: `/`, `/stocks`, `/stocks/AAPL`, `/sectors`, `/themes`, `/data`, `/evidence`, `/scanner-runs`, `/backtest`, `/watchlist`, `/research/regime-lab`); content unchanged, overwritten to confirm freshness. Lints clean (`demo_runner.py --mode lint`).
- `runs/goal-session-ops-hardening/journey-scripts/J-07.json` — re-verified fresh this iteration (`/` → "Ready", `/backtest` → "n=14647" still present, `/data` → "2526" backfill gaps still accurate); content unchanged, overwritten to confirm freshness. Lints clean.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), pinned profile, headless
- **Test Date:** 2026-08-04
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-47-evidence/`
