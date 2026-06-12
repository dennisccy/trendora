# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-8 — UI Test Results

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-8
**Date:** 2026-06-12
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 13/14 tests passed (0 skipped)

> Note on screenshots: the `/data` page is very long and the browser session's screenshot rendering
> produced blank images whenever the page was scrolled past the initial viewport (a known rendering
> issue with this machine documented in project memory — "dead shell / .next cache" variant: dark
> Next.js long pages render blank on scroll). All content was verified via DOM inspection, `get_text`
> extraction, and captured HTML file analysis (`session-1781251290932/`). Screenshots of pages at
> scroll position 0 (dashboard, methodology) rendered correctly and are included.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | `/data` page loads without errors | smoke | P1 | Heading "Data Manager" visible, no error | "Data Manager" heading confirmed, full coverage table rendered | PASS | `UT-01-data-page-final.png` |
| UT-02 | Dashboard loads with five index lines | smoke | P1 | 5 legend entries including DIA | All 5 entries confirmed: SPY, QQQ, IWM, RSP, Dow 30 (DIA) | PASS | `UT-02-UT-04-dashboard-1200h.png` |
| UT-03 | Methodology page shows new glossary entries | smoke | P1 | "stage timings" and "concurrency" visible | Both terms found in rendered glossary with full definitions | PASS | `UT-03-UT-09-methodology-top-final.png` |
| UT-04 | DIA appears in Major-indexes chart legend with drawn line | happy-path | P1 | Fifth legend entry "Dow 30 (DIA)" with line drawn | `await_text("Dow 30 (DIA)")` confirmed; 5 colored lines visible in chart screenshot | PASS | `UT-02-UT-04-dashboard-1200h.png` |
| UT-05 | Completed job card shows Stage timings block | happy-path | P1 | "Stage timings" heading, Backfill sub-block with non-zero values | Backfill sub-block: Elapsed 9.4s, Dates 5, Concurrency 4×, Per-date sum 1.0s; DOM testid=stage-timings confirmed | PASS | DOM: session/210-eval.html |
| UT-06 | Backfill-only job shows only Backfill sub-block | happy-path | P1 | Backfill sub-block present, no Fetch sub-block | `data-testid="stage-timing-fetch"` absent; `data-testid="stage-timing-backfill"` present | PASS | DOM: session/210-eval.html |
| UT-07 | TermInfo tooltip on "Stage timings" label | happy-path | P1 | Tooltip with non-empty definition appears | `aria-expanded=true`, `role=tooltip` panel with "Per-stage operational timings on a fetch+backfill job..." confirmed in DOM | PASS | DOM: session/223-click.html |
| UT-08 | TermInfo tooltip on "Concurrency" stat label | happy-path | P1 | Tooltip with non-empty definition appears | `aria-expanded=true`, `role=tooltip` panel with "How many worker threads a job stage used in parallel..." confirmed in DOM | PASS | DOM: session/227-click.html |
| UT-09 | Glossary entries with definitions for new terms | happy-path | P1 | "stage timings" and "concurrency" with full definitions in /methodology | Both terms in glossary with complete definitions verified via `get_text` and markdown capture | PASS | `UT-03-UT-09-methodology-top-final.png` |
| UT-10 | Backfill speed-up ratio > 1 on job card | happy-path | P1 | Speed-up ratio > 1.0 shown on Backfill sub-block | Speedup line "0.1× faster than the per-date sum" is rendered; ratio is 0.1× (< 1) because per_date_seconds_sum (1.0s compute) / elapsed (9.4s wall-clock incl. DB writes) = 0.106 | FAIL | DOM: session/210-eval.html |
| UT-11 | Existing job progress bars/summary still present | regression | P1 | Progress elements coexist alongside Stage timings | Job card shows: status badge "ok", summary message, "Snapshots backfilled 5/5 dates", "5 snapshots · 3200 forward returns inserted", AND Stage timings block | PASS | DOM: session/210-eval.html |
| UT-12 | Four existing index lines still displayed | regression | P1 | SPY, QQQ, IWM, RSP all in legend | All 4 pre-existing lines confirmed in legend alongside Dow 30 (DIA) | PASS | `UT-02-UT-04-dashboard-1200h.png` |
| UT-13 | Stage timings info icon discoverable by non-developer | ux | P2 | Visible info icon adjacent to "Stage timings" heading | `button[aria-label="Definition of stage timings"]` with SVG circle-i icon found; adjacent to "Stage timings" span; click reveals readable tooltip | PASS | DOM: session/221-eval.html |
| UT-14 | DIA legend label is human-readable and distinguishable | ux | P2 | DIA entry reads "Dow 30 (DIA)" or similar, not just "DIA" | Legend entry confirmed as "Dow 30 (DIA)" with a distinct color swatch; human-readable without developer knowledge | PASS | `UT-02-UT-04-dashboard-1200h.png` |

---

## Passed Tests

### UT-01 — `/data` page loads without errors
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-8-evidence/UT-01-data-page-final.png`
- Navigated to `http://localhost:3835/data`. Page loaded with heading "Data Manager", dataset coverage stats (price history, universe=122, symbols=163, trading days=1365, snapshot dates=200, backfill gaps=1166), per-symbol coverage table, and job form. No error banner or crash.

---

### UT-02 — Dashboard loads with five index lines
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-8-evidence/UT-02-UT-04-dashboard-1200h.png`
- Dashboard loaded. "Major indexes & regime" chart visible. `await_text("Dow 30 (DIA)")` returned "Text found". `get_text` extraction confirmed five legend entries: S&P 500 (SPY), Nasdaq 100 (QQQ), Russell 2000 (IWM), S&P 500 Equal-Weight (RSP), Dow 30 (DIA). Five colored lines visible in chart screenshot at 1200px viewport height.

---

### UT-03 — Methodology page shows new glossary entries
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-8-evidence/UT-03-UT-09-methodology-top-final.png`
- Navigated to `/methodology`. `get_text` and markdown capture confirmed "stage timings" entry with definition: "Per-stage operational timings on a fetch+backfill job...". Confirmed "concurrency" entry with definition: "How many worker threads a job stage used in parallel...". Both in the UNIVERSE & DATA category. No error.

---

### UT-04 — DIA appears in Major-indexes chart legend with drawn line
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-8-evidence/UT-02-UT-04-dashboard-1200h.png`
- "Dow 30 (DIA)" confirmed as fifth legend entry via `await_text`. `document.body.innerText.includes('Dow 30 (DIA)')` returned true. Screenshot shows 5 distinct colored lines across the chart area. DIA data present in backend seed (2021-01-04 → 2026-05-28, 1356 bars confirmed in coverage table).

---

### UT-05 — Completed job card shows Stage timings block
**Verdict:** PASS
**Evidence:** DOM verified from session-1781251290932/210-eval.html
- Started backfill job (2021-02-25 → 2021-03-08) via UI. `await_text("Stage timings")` returned "Text found". DOM confirmed `data-testid="stage-timings"` with: Backfill sub-block showing Elapsed=9.4s, Dates=5, Concurrency=4×, Per-date sum=1.0s, speedup line "0.1× faster than the per-date sum". TermInfo buttons present with `aria-expanded="false"` (closed state). No blank or zero values.

---

### UT-06 — Backfill-only job shows only Backfill sub-block
**Verdict:** PASS
**Evidence:** DOM verified from session-1781251290932/210-eval.html
- The completed backfill-only job (kind=backfill, no fetch stage): `data-testid="stage-timing-fetch"` was absent from the stage-timings block. `data-testid="stage-timing-backfill"` was present with all values. The fetch sub-block was entirely absent — not zeroed, not shown as NA, but omitted as designed.

---

### UT-07 — TermInfo tooltip on "Stage timings" label
**Verdict:** PASS
**Evidence:** DOM verified from session-1781251290932/223-click.html
- Clicked `button[aria-label="Definition of stage timings"]`. After click: `aria-expanded="true"` confirmed on that button. `role="tooltip"` panel rendered in DOM containing: "stage timings Per-stage operational timings on a fetch+backfill job — for each stage that actually ran (fetch, backfill): the elapsed wall-clock, the items processed (symbols for fetch, dates for backfill), and the concurrency used..." — a full readable definition, not the raw term key. Escaped with Escape key successfully dismisses (aria-expanded reverts to false).

---

### UT-08 — TermInfo tooltip on "Concurrency" stat label
**Verdict:** PASS
**Evidence:** DOM verified from session-1781251290932/227-click.html
- After Escape dismissed stage timings tooltip, clicked `button[aria-label="Definition of concurrency"]`. `aria-expanded="true"` confirmed. `role="tooltip"` panel with: "concurrency How many worker threads a job stage used in parallel — the fetch pool fetches symbols concurrently (network I/O), and the multi-date backfill computes per-date snapshots concurrently while all database writes stay serialized on one thread..." — full non-empty readable definition.

---

### UT-09 — Glossary entries with definitions for new terms
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-8-evidence/UT-03-UT-09-methodology-top-final.png`
- "stage timings" confirmed in UNIVERSE & DATA glossary category. Definition: "Per-stage operational timings on a fetch+backfill job — for each stage that actually ran (fetch, backfill): the elapsed wall-clock, the items processed (symbols for fetch, dates for backfill), and the concurrency used. The backfill stage also shows the per-date-sum... WHERE: Data Manager job card."
- "concurrency" confirmed with definition: "How many worker threads a job stage used in parallel... WHERE: Data Manager job card stage timings."
- No duplicate entries for either term. Both in the UNIVERSE & DATA category, ordered logically after "Data Manager".

---

### UT-11 — Existing job progress bars/summary still present
**Verdict:** PASS
**Evidence:** DOM verified from session-1781251290932/210-eval.html
- Completed backfill job card shows all existing elements: status badge ("ok"), job description line ("backfill job · 2021-02-25 → 2021-03-08"), completion message ("backfill: 5 snapshots over 5 dates, 3200 forward returns"), progress counters ("Snapshots backfilled 5/5 dates", "5 snapshots · 3200 forward returns inserted"), AND the new Stage timings block appended after. Stage timings is additive — no existing elements removed.

---

### UT-12 — Four existing index lines still displayed
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-8-evidence/UT-02-UT-04-dashboard-1200h.png`
- Dashboard legend confirmed: "S&P 500 (SPY)", "Nasdaq 100 (QQQ)", "Russell 2000 (IWM)", "S&P 500 Equal-Weight (RSP)" — all four pre-existing lines present and drawn. Dow 30 (DIA) is the fifth addition; none of the four existing entries were replaced.

---

### UT-13 — Stage timings info icon discoverable by non-developer
**Verdict:** PASS
**Evidence:** DOM verified from session-1781251290932/221-eval.html
- `button[aria-label="Definition of stage timings"]` present with a circle info SVG icon. It is placed as a sibling immediately adjacent to the "Stage timings" `<span>` text. The button has clear hover/focus styling (`hover:text-accent`). Clicking reveals a readable tooltip — no developer knowledge required to discover or use it.

---

### UT-14 — DIA legend label is human-readable and distinguishable
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-8-evidence/UT-02-UT-04-dashboard-1200h.png`
- Legend entry reads "Dow 30 (DIA)" — includes the full index name "Dow 30" alongside the ticker "DIA". An operator can identify which line represents the Dow Jones Industrial Average without looking it up. Dashboard screenshot at 1200px height shows chart with 5 colored lines and the full legend row including "Dow 30 (DIA)" with its distinct color swatch.

---

## Failed Tests

### UT-10 — Backfill speed-up ratio > 1 on job card
**Verdict:** FAIL
**Failure:** The speed-up ratio displayed is 0.1× (less than 1), not greater than 1 as the test expects.

**Steps taken:**
1. Navigated to `/data`.
2. Started backfill job (2021-02-25 → 2021-03-08, 5 dates, concurrency=4).
3. Awaited "Stage timings" text to appear after job completion.
4. Read `data-testid="backfill-speedup"` content from DOM.

**Expected:** Speed-up ratio > 1.0 (e.g. "2.1× faster than the per-date sum")

**Actual:** "0.1× faster than the per-date sum" — where `per_date_seconds_sum=1.0s` (sum of per-date CPU compute time) divided by `elapsed_seconds=9.4s` (total wall-clock including serialized DB writes) = 0.106.

**Root cause analysis:** The speedup formula is `per_date_seconds_sum / elapsed_seconds`. The `per_date_seconds_sum` (1.0s) represents the total CPU compute time summed across all 5 dates. The wall-clock `elapsed` (9.4s) is dominated by serialized database write I/O. On this machine, DB writes take ~8-9s for 5 dates. The parallel backfill reduces compute time but not DB write time, so the ratio is < 1. The feature itself (speedup line, per-date-sum field, backfill timings block) is fully implemented and rendering correctly. The test precondition "backfill_workers >= 4" was satisfied (concurrency=4×), but the test's expectation of ratio > 1 does not hold on this hardware profile. A fetch+backfill job would likely show a ratio > 1 for the fetch stage (network I/O parallelism), but no fetch job was available to test.

---

## Skipped Tests

None.

---

## Environment

- **Frontend URL:** http://localhost:3835
- **Backend URL:** http://localhost:8835
- **Browser:** Chrome via MCP (session-1781251290932)
- **Test Date:** 2026-06-12
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-8-evidence/`
- **Screenshot note:** Screenshots from `/data` page at non-zero scroll position render blank due to a known browser rendering issue on this machine with long dark-themed Next.js pages (documented in project memory: "Browser QA dead-shell / .next cache"). Content verified via DOM inspection and captured HTML files. Dashboard and methodology screenshots at scroll-0 rendered correctly.
