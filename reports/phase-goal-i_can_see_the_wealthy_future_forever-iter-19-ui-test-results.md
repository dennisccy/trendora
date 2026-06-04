# Phase goal-i_can_see_the_wealthy_future_forever-iter-19 — UI Test Results

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-19
**Date:** 2026-06-04
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 12/12 tests passed (0 failed, 0 skipped)

All P1 tests pass. **Both critical anti-goal gates pass:** UT-07 (J-15 — All-history mode does NOT refetch on global-date change, network-asserted) and UT-08 (J-18 — exactly one date control, in `<header>`; the mode toggle is a button group, not a date picker).

---

## Environment

- **Frontend URL:** http://localhost:3835
- **Backend:** http://localhost:8835 (`/api/health` → `db_ok:true`, provider `seed`, latest snapshot `2026-05-28`, 158 symbols)
- **Browser:** Chrome via superpowers-chrome MCP (headless)
- **Test Date:** 2026-06-04
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-19-evidence/`
- **Available as-of dates (descending):** 2026-05-28 (Latest) · 2026-02-27 · 2025-11-28 · 2025-08-28 · 2025-05-28 · 2025-04-04 · 2025-02-28 · 2024-11-27 · 2024-08-28 · 2024-05-28 · 2022-10-07 (earliest)

### Pre-test environment note (handled, not a defect)
On first load the page carried **residual in-memory state from the immediately-prior `qa` browser run** (qa evidence `TC-10`/`TC-11` timestamped 12:56–13:00) plus a stray `/stocks` tab — the as-of switcher was left at an early date and the mode at "As of date". The `AsOfProvider` keeps state in React memory (no localStorage/cookie/URL persistence) and lives in the root layout, so client-side navigation does not reset it. I closed the stray tab and performed a hard `about:blank → /research` reload, then ran a **two-read stability check** (identical results, no concurrent writer) to establish a deterministic default baseline before asserting anything. This is the recurring "serialize Chrome access if both qa + browser-qa run" lesson (iter-6/iter-15) — managed, with no impact on the results below.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Research page loads with mode toggle | smoke | P1 | Heading + `analysis-mode-toggle` (All history active, `aria-pressed=true`) + default context line; all labs render; no crash | Heading "Research — Factor Lab"; toggle present, "All history" `aria-pressed=true` / "As of date" `false`; context = "Pooling every snapshot — all history (the default cross-date aggregate)."; decile/Rank-IC/regime/combination/event-study all render; no error overlay | PASS | `UT-01-default-all-history.png` |
| UT-02 | Default All-history full-sample baseline | smoke | P1 | Each lab shows a non-zero full-sample n | Factor Obs **1218**; Rank-IC +0.00 **n=1218**; Combination composite **n=244**; Event-study (subject "Actionable") **n=2** (genuinely low-sample → honest NA even at all-history) | PASS | `UT-01-default-all-history.png` |
| UT-03 | Toggle to As-of updates segment + context | happy-path | P1 | As-of becomes active; at latest date context says "equals all history"; figures unchanged | asof `aria-pressed=true`, all `false`; context = "As of the latest date — equals all history. Pick an earlier date in the top-bar as-of switcher to restrict the window."; Obs 1218 / Rank-IC n=1218 / combo n=244 unchanged | PASS | `UT-03-asof-mode-at-latest.png` |
| UT-04 | Context line names resolved cutoff | happy-path | P1 | Context names "only snapshots dated ≤ <date>" matching the global switcher; accent phrase present | At 2022-10-07: context = "Point-in-time: pooling only snapshots dated ≤ 2022-10-07 (a walk-forward view — smaller n, honest NA at early dates), driven by the single global as-of switcher."; accent span = "only snapshots dated ≤ 2022-10-07" | PASS | `UT-05-asof-2022-10-07-reduced-n.png` |
| UT-05 | As-of @ early date re-points labs, n drops | happy-path | P1 | Each lab's n strictly smaller than baseline; low-sample → NA; survivorship banner persists | Obs 1218→**120**; Rank-IC n 1218→**120**; Combination composite 244→**25** rendered as **NA** (25 < min_sample 30); Event-study → honest "No forward-tested occurrences for this subject" empty state; survivorship banner present; no fabricated values | PASS | `UT-05-asof-2022-10-07-reduced-n.png` |
| UT-06 | All history restores full sample | happy-path | P1 | All-history active; context reverts; each lab's n returns to baseline | all `aria-pressed=true`; context = "Pooling every snapshot — all history…"; Obs→**1218**, Rank-IC n→**1218**, combo→**244**, event-study table back to n=2 — **even though global date still pinned at 2022-10-07** (All-history ignores it) | PASS | `UT-06-all-history-restored-fullsample.png` |
| UT-07 | All-history ignores global date (J-15) | regression | P1 | Context unchanged; every lab's n identical to baseline; **no research refetch** | In All-history, changed global date 2022-10-07→2024-08-28: `fetch` spy recorded **0** `/research/*` calls; Obs 1218 / Rank-IC n=1218 / combo n=244 byte-identical; context unchanged | **PASS** (critical) | `UT-06-all-history-restored-fullsample.png` |
| UT-08 | Exactly one date control, in header (J-18) | regression | P1 | Exactly one date `<select>` in `<header>`, none in `<main>`; toggle is a mode switch, not a date picker | **1** date select total (aria "View as-of date", `inHeader=true`, `inMain=false`); **0** date selects in main; **0** `<input type=date>`; **0** calendar widgets; toggle is a `DIV` with **2 buttons**, no `<select>`. Corroboration: As-of refetch carries the single global `?as_of=2024-08-28` on all 3 lab calls (expected — single global date transmitted, MEMORY `j18-asof-on-stocks-fetch-is-correct`) | **PASS** (critical) | `UT-08-single-date-control-header.png` |
| UT-09 | Backend-unavailable surfaced, no crash | error | P2 | Each lab shows "Backend unavailable"; exact Factor-Lab copy; no blank/crash; no fabricated numbers | 3× "Backend unavailable" cards; Factor-Lab card = "The Factor-Lab evidence could not load from the API. No figures are shown rather than fabricated values. Confirm the backend is running and retry."; combination + event-study show their own messages; no React error overlay; heading/toggle still render; data tables removed (no fabricated numbers). Labs recovered cleanly when fetch restored | PASS | `UT-09-backend-unavailable.png` |
| UT-10 | Stale "no date control" copy removed | regression | P2 | Subject helper points at the global control; no copy claims the page lacks a date control | Subject helper = "Re-uses the page's shared horizon selector and the page-level analysis-mode toggle above — no date control of its own (the single global as-of drives any point-in-time scoping, J-18)." — the only "no date control" phrase on the page, and it correctly points at the global as-of (not a denial that any date control exists) | PASS | `UT-05-asof-2022-10-07-reduced-n.png` |
| UT-11 | Prior journeys + synthesis travel intact | regression | P1 | All three labs render full-sample; combination Baseline/single/composite/strict rows; event-study per-horizon + by-regime + by-sector; leaderboard cross-link travels | Decile table, Rank-IC, regime-effectiveness table, combination table (Baseline + composite + Strict-overlap rows), event-study (per-horizon + by-regime + by-sector) all render in default mode; "View the names expressing this on the leaderboard→" navigates to **`/stocks?setup=Actionable`** with the Setup filter applied (honest "No stock is currently 'Actionable' … No rows are fabricated" empty state — travel intact, no fabrication) | PASS | `UT-11-leaderboard-setup-Actionable.png` |
| UT-12 | Toggle discoverable + keyboard-operable | ux | P3 | "Analysis mode" label visible; keyboard focus ring; Enter/Space activates; active segment highlighted | Visible "Analysis mode" label + group aria-label "Analysis mode (all-history or as-of-date)"; "As of date" is a real `<button>`, focusable; **Enter** activated it and switched the mode; class carries `focus-visible:ring-1 focus-visible:ring-accent` (keyboard ring); active segment `bg-accent font-semibold` (filled accent) vs inactive transparent | PASS | `UT-12-toggle-keyboard-focus.png` |

---

## Passed Tests

### UT-01 — Research page loads with the new analysis-mode toggle
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-19-evidence/UT-01-default-all-history.png`
- Heading "Research — Factor Lab" visible.
- `analysis-mode-toggle` present with two buttons "All history" / "As of date"; "All history" `aria-pressed="true"` (filled accent), "As of date" `aria-pressed="false"`.
- `analysis-mode-context` = "Pooling every snapshot — all history (the default cross-date aggregate)."
- Decile table, Rank-IC card, regime-effectiveness table, Multi-factor combination cohort, and Setup & Pattern Lab all render with numbers/NA cells. No "Backend unavailable" card, no blank screen, no React error overlay (console capture is not implemented by the MCP tool; verified via full render + absence of error overlay).

### UT-02 — Default All-history full-sample baseline
**Verdict:** PASS
**Evidence:** `UT-01-default-all-history.png`
- Baseline recorded (All-history @ latest 2026-05-28): **Factor Obs 1218**, **Rank-IC +0.00 n=1218**, **Combination composite n=244** (+1.21% / +0.70% / +54.10% / +0.26), **Event-study subject "Actionable" n=2 per horizon**.
- Note: the event-study default subject "Actionable" is genuinely low-sample (n=2 across all snapshots ever) so it already shows honest NA at all-history; the n-drop in UT-05 is demonstrated decisively by Factor Lab (1218→120) and Combination (244→25). The event study shows its sample as per-horizon `n=` in the table rather than a separate "Pooled occurrences (Nd):" line.

### UT-03 — Toggle to As-of updates segment + context
**Verdict:** PASS
**Evidence:** `UT-03-asof-mode-at-latest.png`
- Clicking "As of date" moved `aria-pressed` to the As-of segment; context became "As of the latest date — equals all history. Pick an earlier date in the top-bar as-of switcher to restrict the window."
- Figures unchanged (Obs 1218 / Rank-IC n=1218 / combo n=244) because as-of @ latest == all history.

### UT-04 — Context line names the resolved cutoff
**Verdict:** PASS
**Evidence:** `UT-05-asof-2022-10-07-reduced-n.png`
- With the global switcher set to 2022-10-07 (native-setter + bubbling change, per MEMORY `react-controlled-select-needs-native-setter`), the context read "Point-in-time: pooling only snapshots dated ≤ 2022-10-07 (a walk-forward view — smaller n, honest NA at early dates), driven by the single global as-of switcher." The accent-coloured span "only snapshots dated ≤ 2022-10-07" exactly matches the selected date.

### UT-05 — As-of @ early date re-points every lab with reduced n
**Verdict:** PASS
**Evidence:** `UT-05-asof-2022-10-07-reduced-n.png`
- Factor Lab Observations 1218 → **120**; Rank-IC n 1218 → **120**; Combination composite n 244 → **25** (rendered **NA** because 25 < min_sample 30 — honest NA, not a fabricated number); Event-study → honest "No forward-tested occurrences for this subject. No stored snapshot has this setup/pattern with a realized forward return yet." empty state (no crash, no 500, no fabricated row).
- Monotonic scoping cross-checked at an intermediate date (2024-08-28): Factor Obs **364**, Combination composite **n=73** — i.e. 120 (2022) < 364 (2024) < 1218 (all), and 25 < 73 < 244. Survivorship · universe-relative · descriptive banner persists in As-of mode.
- Backend cross-check (API): `/api/research/factor-lab?as_of=2025-01-15` → 486 obs vs 1218 all-history; `?as_of=banana` → 422; `?as_of=2099-01-01` (future) → 400.

### UT-06 — Returning to All history restores the full sample
**Verdict:** PASS
**Evidence:** `UT-06-all-history-restored-fullsample.png`
- Clicking "All history" reverted the context to "Pooling every snapshot — all history (the default cross-date aggregate)." and restored Obs **1218** / Rank-IC n **1218** / combo **244** / event-study n=2 — while the global switcher was still pinned at 2022-10-07, proving All-history mode ignores the global date.

### UT-07 — All-history ignores global date (J-15) — CRITICAL
**Verdict:** PASS
**Evidence:** `UT-06-all-history-restored-fullsample.png`
- A `window.fetch` spy was installed and reset. In All-history mode the global date was moved 2022-10-07 → 2024-08-28. The spy recorded **0** `/research/{factor-lab,factor-combination,event-study}` calls (`__researchCalls = []`), and every figure stayed byte-identical (Obs 1218 / Rank-IC n=1218 / combo n=244); context unchanged. The labs key their fetch effect on the resolved `asofCutoff` (which stays `null` in All-history mode), not raw `asOf` — read-path discipline preserved.

### UT-08 — Exactly one date control, in the header (J-18) — CRITICAL
**Verdict:** PASS
**Evidence:** `UT-08-single-date-control-header.png`
- Live DOM audit: **1** date `<select>` total (aria "View as-of date"), a descendant of `<header>`, not `<main>`; **0** date selects in `<main>`; **0** `<input type=date>`; **0** calendar widgets. The other 6 selects are non-date (Factor, two Condition factors, two Condition quantiles, Subject). The Analysis-mode toggle is a `DIV` containing **2 `<button>`s** and **no `<select>`** — a mode switch, not a date picker.
- Corroboration of the J-18 nuance (MEMORY `j18-asof-on-stocks-fetch-is-correct`): switching to As-of mode fired exactly 3 research refetches, each carrying the single global `?as_of=2024-08-28` — the global date transmitted on a snapshot-served read, which is expected and correct, NOT a second date state.

### UT-09 — Backend-unavailable surfaced, not a crash
**Verdict:** PASS
**Evidence:** `UT-09-backend-unavailable.png`
- Simulated at the browser layer (overrode `fetch` to reject `/research/*` so the shared backend stayed up for other agents), then triggered a refetch. All three labs rendered "Backend unavailable" cards. Factor-Lab card text exactly = "The Factor-Lab evidence could not load from the API. No figures are shown rather than fabricated values. Confirm the backend is running and retry." Combination and Event-study showed their own "Backend unavailable" messages. No blank screen, no React error overlay; data tables were removed (no fabricated numbers). Restoring `fetch` recovered all labs to full sample.

### UT-10 — Stale "no date control" copy removed
**Verdict:** PASS
**Evidence:** `UT-05-asof-2022-10-07-reduced-n.png` (event-study helper visible)
- The event-study subject helper reads exactly "Re-uses the page's shared horizon selector and the page-level analysis-mode toggle above — no date control of its own (the single global as-of drives any point-in-time scoping, J-18)." This is the only "no date control" phrase on the page and it correctly points at the single global control. No on-page copy denies that the page has an as-of/date control (the old "NONE has an as-of/date control" framing is gone).

### UT-11 — Prior journeys + synthesis travel intact
**Verdict:** PASS
**Evidence:** `UT-11-leaderboard-setup-Actionable.png`
- In default All-history mode the Factor-Lab decile table, Rank-IC card, and regime-effectiveness table render full-sample figures; the combination cohort renders Baseline, single-factor, Combined (composite), and Strict overlap (AND) rows; the Setup & Pattern Lab renders the per-horizon table plus by-regime and by-sector panels.
- "View the names expressing this on the leaderboard→" navigated to `/stocks?setup=Actionable` (h1 "Stocks") with the Setup filter applied. The leaderboard honestly shows "No stocks match these filters — No stock is currently 'Actionable'. No rows are fabricated to fill the view — clear a filter to see more." — the J-31 cross-link travel and the no-fabrication discipline are both intact (the empty result is honest data, consistent with "Actionable" being a rare setup).

### UT-12 — Mode toggle is keyboard-operable and clearly labelled
**Verdict:** PASS
**Evidence:** `UT-12-toggle-keyboard-focus.png`
- Visible "Analysis mode" caption above the group; group `aria-label="Analysis mode (all-history or as-of-date)"`. The "As of date" element is a real `<button>` that accepts focus; pressing **Enter** while it was focused switched the mode (asof `aria-pressed`→true) and updated the context line. The button class carries `focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent` (a keyboard focus ring for `:focus-visible`) and `bg-accent font-semibold text-bg` when active (the active segment is unambiguously highlighted vs the transparent inactive segment).

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Source cross-checks (supporting the live results)

- `app/research/page.tsx`: `mode` defaults to `"all"` (line 49); `asofCutoff = mode === "asof" ? asOf : null` (line 60); the three lab fetch effects depend on `asofCutoff` (lines 71/662/…), **not** raw `asOf`; there is **no** effect coupling `asOf → mode`. This is the source basis for UT-06/UT-07/J-15.
- `components/asof-provider.tsx`: `asOf` defaults to `null` (latest); the provider holds the single global date — no second date state. Basis for J-18.
- Backend `app/api/research.py`: the three routes accept an optional `as_of` and echo the resolved `asof_date`; validation returns 422 (unparseable) / 400 (future) — confirmed live against `:8835`.

---

## Notes for downstream agents

- **Both critical anti-goal gates passed:** J-15 (UT-07, network-asserted 0 refetches) and J-18 (UT-08, exactly one date control in `<header>`; toggle is a button group).
- **No second date state introduced.** The `?as_of=` carried on the As-of-mode research fetch is the single global date being transmitted (expected per MEMORY `j18-asof-on-stocks-fetch-is-correct`), not a J-18 violation.
- **Evidence is de-duplicated:** all 8 screenshots have distinct sha256 hashes; before/after states are grounded on distinct DOM + network assertions, not a single screenshot pair (iter-6 lesson).
- **Browser state hygiene:** the prior `qa` run left residual in-memory state + a stray tab; this was reset (hard reload + stability check) before measuring. Subsequent UI-driving agents should likewise hard-reset `/research` rather than trusting carried state.
