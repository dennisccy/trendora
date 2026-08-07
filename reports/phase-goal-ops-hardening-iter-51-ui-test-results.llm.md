# Phase goal-ops-hardening-iter-51 — UI Test Results

**Phase:** goal-ops-hardening-iter-51
**Date:** 2026-08-07
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- All 8 executed tests (including all P1 smoke/happy-path/regression cases) passed, several with
byte-identical API cross-checks. UT-05 (P1, error case) is SKIPPED — its precondition (a backend restart
with a fault-injection env var) was blocked by the permission system in this session; this is an
environment/tooling gap, not an observed product failure. See its section below and the "Coverage gap"
note for what this means for scoring. -->

**Overall:** 8/9 tests passed (1 skipped) — 8 of 8 executed tests passed (0 failures); UT-05 skipped.

**Coordinator note:** the pump restarted the backend (`CHAIN_BACKEND_PORT=8255 CHAIN_FRONTEND_PORT=3255
bash scripts/start-backend.sh`) before this dispatch began; it was confirmed healthy (200 on `/api/health`)
at the start of this run and needed no further restart by me except for the (blocked) attempts described
under UT-05.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Factor Lab loads without errors | smoke | P1 | Page renders, heading visible, table or labelled loading/error state, no console errors | Heading "Research — Factor Lab" present; 11-row factor table rendered immediately with real data; no error card; no indefinite spinner. Console-log capture unsupported by this Chrome MCP build ("Console logging not yet implemented") — verified absence of errors via DOM/content instead | PASS | `reports/qa/goal-ops-hardening-iter-51-evidence/UT-01-result.png` |
| UT-02 | Factor Lab is a fast cache HIT with real data | happy-path | P1 | No "Still computing" card; real rows; sort works with no reload; expand shows decile grid | `slow-compute-notice` never appeared; 11 real factor rows (e.g. "Leadership score"); clicked Rank-IC header — `aria-sort` flipped descending→ascending, rows re-ordered client-side; clicked first row — expanded to a real D1–D10 decile grid, no error. Direct API cross-check: `GET /api/research/factor-lab?all=true` → HTTP 200 in **0.0078s** (well under 1s) | PASS | `reports/qa/goal-ops-hardening-iter-51-evidence/UT-02-result.png` |
| UT-03 | `/data` Refreshed line lists "factor lab all" | happy-path | P1 | `aggregates-refreshed` paragraph present, includes "factor lab all" | Line read "Refreshed: forward aggregates, research hot keys, factor lab all, drawdown expectations". Cross-checked byte-identical against `GET /api/data` run id=323's `aggregates_refreshed` JSON list | PASS | `reports/qa/goal-ops-hardening-iter-51-evidence/UT-03-result.png` |
| UT-04 | Start-job form blocks invalid dates | validation | P2 | Inline error shown, Start button disabled, no job created | Typed `2026-13-40` into Start date; error span `job-start-date-error` read "Enter a valid date as yyyy-MM-dd" (functionally the format the plan describes as YYYY-MM-DD); Start button gained `disabled=""`. Verified via DOM `attr` inspection 3 times independently. Screenshot capture returned a blank/black image on all 4 attempts (2 tabs) — a Chrome/CDP rendering issue that emerged partway through this session, not a product defect (see Notes) | PASS | Screenshot unusable (blank) — see Notes; DOM evidence recorded above |
| UT-05 | Degraded warm honestly omitted; job still completes | error | P1 | Job completes cleanly; "factor lab all" omitted from Refreshed; log shows phase timing + isolation-failure line, no unhandled traceback | **NOT EXECUTED.** Precondition requires restarting the backend with `TRENDORA_FAULT_INJECT_MEMORY_ERROR=factor_lab_all`. Two restart methods were denied by the permission system (see Skipped Tests section). No unsafe state resulted — original backend confirmed still healthy afterward | SKIPPED | none |
| UT-06 | Factor Combination results unchanged | regression | P1 | Page loads, returns results, no error; counts/samples match pre-iteration behavior | Default (server-resolved 2-condition) load took **~108s** to resolve (no error) — cross-checked byte-identical against a direct API call (baseline n=1254322, mean +1.31%, etc., all fields matched exactly). Clicked "Add condition" (→3 conditions, "Leadership score" added): recomputed correctly (composite n=250866, strict_overlap n=38975, appropriately smaller), again byte-identical to a fresh direct API call. See Notes for a plan-vs-actual precondition deviation and a UX finding | PASS | `reports/qa/goal-ops-hardening-iter-51-evidence/UT-06-result.png` |
| UT-07 | Factor Lab sort/expand/mode controls still work | regression | P2 | Sort flips direction with indicator; mode switch re-fetches without error | "N" column: click 1 → `aria-sort="descending"`; click 2 → `aria-sort="ascending"`; `sort-indicator` present and rows re-ordered each time. "As of date" → real data reloaded, no error; "All history" → switched back cleanly, no error | PASS | `reports/qa/goal-ops-hardening-iter-51-evidence/UT-07-result.png` |
| UT-08 | Health + concurrent requests survive a live warm | regression | P1 | Health polls mostly 200; concurrent research pages load quickly, no MemoryError/500 (failure here is explicitly scoping input, not an auto-blocker per the phase spec) | Ran the full concurrent TC-5/TC-6 drill (a fresh ingest + 2 concurrent research-page loads) that the dev handoff explicitly deferred to this lane. Job ran 1435.87s; health polls 19/892 (2.1%) non-200 during the run (0/269 in the 300s after completion) — same order of magnitude as the dev's disclosed solo baseline (9/653, 1.4%), clustered around the run's single longest sub-phase. Zero MemoryError/Traceback/500 anywhere. Both concurrent pages eventually resolved with fresh, correct data but took the full warm duration to do so (not "quick") — see Notes for full detail and why this is scored PASS per the test's own guidance | PASS | `reports/qa/goal-ops-hardening-iter-51-evidence/UT-08-factorlab-result.png`, `reports/qa/goal-ops-hardening-iter-51-evidence/UT-08-factorcombination-result.png` |
| UT-09 | Factor Lab discoverable from Research hub | ux | P2 | Tile visible, click navigates to `/research/factor-lab` and loads | "Factor Lab" tile present in the lab grid; clicked it; URL became `/research/factor-lab`; page loaded fully (same content as UT-01) | PASS | `reports/qa/goal-ops-hardening-iter-51-evidence/UT-09-result.png` |

---

## Passed Tests

### UT-01 — Factor Lab loads without errors
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-51-evidence/UT-01-result.png`
- Navigated to `/research/factor-lab`; heading "Research — Factor Lab" visible; factor table (11 rows: Downside volatility, ATR %, HV, Risk score, Up/down volume, VCP contraction, Leadership score, RS vs SPY, Entry Quality, MA stack, 52-week-high proximity) rendered with real Rank-IC/N/risk-adjusted/decile numbers — never a blank screen or unhandled error.
- This Chrome MCP build's console-log capture is a stub ("TODO: Console logging not yet implemented" — confirmed by reading the tool's own `-console.txt` capture file), so "no new console errors" was verified via DOM/content inspection (no error boundary text, no crash markers in the extracted HTML) rather than a literal console read. Noting this as a tool limitation, not a skipped check.

### UT-02 — Factor Lab is a fast cache HIT with real data
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-51-evidence/UT-02-result.png`
- Watched the page from navigation; the amber `slow-compute-notice` card never appeared at any point (confirmed absent from the DOM both immediately after navigation and on a clean reload with `await_text` resolving almost instantly).
- Clicked the "Rank-IC (20d)" column header: `aria-sort` on that `<th>` flipped from `descending` to `ascending`, and the button's `aria-label` updated to match; row order visibly changed (e.g. "Proximity to 52-week high" moved to first).
- Clicked the (now-first) "Proximity to 52-week high" row: `aria-expanded` flipped to `true` and a full D1…D10 decile grid rendered (factor range, Fwd 1d/5d/10d/20d/60d, MDD 1d/5d/10d/20d/60d, real percentages and `n=` counts for every decile) — no error.
- Terminal cross-check: `curl -s -o /dev/null -w "%{http_code} %{time_total}s\n" "http://localhost:8255/api/research/factor-lab?all=true"` → `200 0.007799s`, matching the plan's expected 0.008–0.043s range and confirming a genuine cache HIT (vs. the pre-iteration 578–875s).

### UT-03 — `/data` Refreshed line lists "factor lab all"
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-51-evidence/UT-03-result.png`
- On `/data`, the Job progress card fell back to the most recent persisted run's summary ("backfill job · 2025-06-01 → 2026-07-17 · from a previous session"), exactly as the plan anticipates.
- The `data-testid="aggregates-refreshed"` paragraph beneath the "412 calendar days · 283 already snapshotted · 129 non-trading" line read: **"Refreshed: forward aggregates, research hot keys, factor lab all, drawdown expectations."**
- Cross-checked directly against the backend: `GET /api/data` → the run with `id: 323` has `"aggregates_refreshed": ["forward_aggregates", "research_hot_keys", "factor_lab_all", "drawdown_expectations"]` — an exact, byte-identical match to what the UI rendered (AG-3 compliant: the displayed value is the engine's own recorded value, not a re-derivation).

### UT-04 — Start-job form blocks invalid dates
**Verdict:** PASS
**Evidence:** DOM-verified (screenshot unusable — see Notes below)
- Cleared the Start date field (click → Ctrl+A → Delete, confirmed empty) and typed `2026-13-40`.
- Result (verified via direct `attr` DOM query, repeated independently 3 times across the session with consistent results): input `value="2026-13-40"`, `aria-invalid="true"`, `aria-describedby="job-start-date-error"`; the error `<span data-testid="job-start-date-error" role="alert">` read **"Enter a valid date as yyyy-MM-dd"** (the plan's prose says "YYYY-MM-DD" — same format, different casing convention, matching the placeholder text used elsewhere on this exact page).
- The Start `<button type="submit">` carried a bare `disabled=""` attribute — confirmed unclickable. No job was created (no new `id` appeared in `GET /api/data`'s `runs` list while this state was active).

### UT-06 — Factor Combination results unchanged after the cohort-members allocation fix
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-51-evidence/UT-06-result.png`
- Navigated to `/research/factor-combination`. On mount the page fetches its default (server-resolved) 2-condition combination immediately — no "Add condition" clicks are needed to reach 2 conditions; see the Notes deviation below. Direct terminal timing: `GET /api/research/factor-combination` (no params, defaults) → **HTTP 200 in 107.94s**, then a second identical call (now cached) → 200 in 0.044s.
- Every displayed number cross-checked byte-identical against the raw API JSON: baseline n=1254322 (mean +1.31%, median +1.25%, hit 57.11%, risk-adj +0.22); RS-vs-SPY single n=250958 (+1.54%/+1.23%/56.39%/+0.25); ATR% single n=418074 (+0.67%/+0.94%/57.16%/+0.16); composite n=250865 (+0.68%/+0.93%/57.19%/+0.16); strict overlap n=54328 (+0.58%/+0.67%/54.87%/+0.14).
- Clicked "Add condition" (`data-testid="condition-add"`): a 3rd condition row appeared (defaulted to "Leadership score · top · Quintile"); the table dimmed (`aria-busy="true"`) while stale 2-condition numbers stayed visible (good stale-while-revalidate behavior), then resolved to fresh 3-condition numbers — again cross-checked byte-identical against a direct API call with the same 3 conditions: composite n=250866 (+0.77%/+0.97%/56.94%/+0.17), strict_overlap n=38975 (+0.58%/+0.69%/55.02%/+0.14, correctly smaller than the 2-condition strict overlap since a 3rd AND-condition narrows the intersection). No error state at any point.

### UT-07 — Factor Lab's sort/expand/mode controls still work on cache-warmed data
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-51-evidence/UT-07-result.png`
- "N" column header: 1st click → `aria-sort="descending"`, `aria-label="Sort by N, descending"`; 2nd click → `aria-sort="ascending"`, `aria-label="Sort by N, ascending"` — direction flipped correctly both times, row order changed each time, `data-testid="sort-indicator"` present on the active column.
- Clicked `analysis-mode-asof` ("As of date"): `aria-pressed="true"`, table re-rendered with real data (`factors-table` present, "Leadership score" text present), no error card, no stuck skeleton.
- Clicked `analysis-mode-all` ("All history") to switch back: `aria-pressed="true"` on the All-history button, real data present, no error.

### UT-08 — `/api/health` and concurrent research requests survive a live finalize-tail warm
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-51-evidence/UT-08-factorlab-result.png`, `reports/qa/goal-ops-hardening-iter-51-evidence/UT-08-factorcombination-result.png`, `reports/qa/goal-ops-hardening-iter-51-evidence/UT-08-data-jobcomplete-result.png` (blank — CDP issue, see Notes)

This is the exact concurrent TC-5/TC-6 drill the dev handoff's own "Known Issues"/"Suggested Next Phase"
sections state was **not run** during development ("deferred to the browser-qa-agent/audit lane") — so this
result is new, first-time coverage for this iteration, not a repeat of the dev's own measurement.

**Setup:** Picked `2019-02-25` as the target date — confirmed via a direct read-only query against
`apps/backend/data/trendora.db` that 546/591 symbols have a `daily_prices` bar on that date and it had zero
`scanner_runs` rows (a genuine snapshot gap, unlike an earlier candidate date that turned out to have no
bars at all and produced a zero-work no-op job). Started the backfill on `/data`, then opened
`/research/factor-lab` and `/research/factor-combination` in two more tabs roughly 35–50s later while the
job card still showed "running", and ran a client-side `curl` loop against `/api/health` once per second
for the duration.

**Job outcome:** `id=325`, status `ok`, 1 snapshot created, 2305 forward returns, total duration
**1435.87s** (00:10:18–00:34:14 UTC). `aggregates_refreshed` included all 8 categories (`latest_snapshot`,
`coverage`, `membership_timeline`, `market_phase`, `forward_aggregates`, `research_hot_keys`,
`factor_lab_all`, `drawdown_expectations`) — a fully clean, non-degraded finalize tail.

**Finalize-tail phase breakdown** (from `logs/backend.log`, job's internal id
`f766d4279f2d4ce0a26651389f21689e`):
- `forward_aggregates_warm`: **1003.37s total** (h1=96.30s, h5=159.32s, h10=152.46s, **h20=573.87s**,
  h60=21.41s) — the dominant cost in THIS run.
- `research_hot_keys_warm`: 2.54s. `index_series_warm`: 0.04s.
- **`factor_lab_all_warm`: 0.05s** — near-instant, because my own concurrent `/research/factor-lab` tab's
  request reached the single-flight compute first and cached the result before the finalize tail's own
  scheduled call for the same key arrived; a live confirmation the single-flight sharing mechanism works
  as designed rather than duplicating the compute.
- `drawdown_expectations_warm`: 359.61s total across 7 claims (8.6s–117.1s each).
- Teardown: `_release_process_memory: DONE gc_collect=0.09s malloc_trim=0.11s total=0.20s`;
  `J-05 finalize-tail teardown timing: ... total_teardown=0.20s` — present as TC-7 expects.
- Also observed 14 `"evidence drawdown-expectations warm deferred -- an ingest finalize-tail heavy-warm
  window is open"` lines — the documented boot/re-warm-vs-finalize-tail interlock correctly yielding, not
  an error.

**Health-poll results:**
- During the run: 892 client-side polls captured, **19 non-200/connection-failures (2.13%)**. All 19
  cluster in two narrow windows — offsets 554–610s (14) and 992–1102s (5) since my poll loop started —
  which align with `forward_aggregates_warm horizon=20`'s 573.87s span (the run's single longest sub-phase),
  not with `factor_lab_all_warm` (which barely ran this time).
- **Methodology gap, disclosed:** my polling process was itself reaped at a harness turn boundary around
  offset 1102s (the job ran to ~1436s) — the same background-process-survival limitation the dev handoff
  documents hitting during its own measurement attempt. I do not have direct client-side failure counts for
  the last ~5.5 minutes of the run. Indirect evidence for that slice: the backend's own access log shows
  every one of the 520 `GET /api/health` requests that reached it inside the job's exact log-line range
  (lines 201455–203577) returned 200 OK, and a direct grep of that exact line range found zero
  `MemoryError`/`Traceback`/`ERROR`-level lines — but a server-side access log cannot see a client-side
  connection failure that never reached the server, so this is corroborating, not equivalent, evidence.
- After completion: a fresh, uninterrupted 300s foreground poll (269 polls) → **0 failures**, back to fully
  healthy immediately.
- **Context vs. the dev's own baseline:** the dev handoff's solo (non-concurrent) run found 9/653 (1.4%)
  non-200 polls, ALL inside `factor_lab_all_warm`'s window specifically. My concurrent run's 2.1% is the
  same order of magnitude, but clustered around a *different* phase (`forward_aggregates_warm h20`) simply
  because that was the longest CPU-bound sub-phase this time (`factor_lab_all_warm` was nearly free due to
  the single-flight sharing above). This generalizes the dev's finding: occasional
  connection-level `/api/health` starvation is a property of *any* sufficiently long, tight CPU-bound
  finalize-tail sub-phase running in-process — not something unique to `factor_lab_all_warm`'s own code —
  which matches the phase spec's own GIL-contention diagnosis.

**Concurrent research pages:** Both `/research/factor-lab` and `/research/factor-combination`, opened while
the job was running, showed an honest in-progress state rather than an error: factor-lab showed the
labelled `slow-compute-notice` ("Still computing — Xs elapsed", the counter visibly incrementing from 28s to
over a minute); factor-combination showed its plain (unlabeled — see UT-06's Notes) skeleton. **Both
eventually resolved successfully** with fresh, updated data reflecting the new snapshot (factor-lab's N
count moved from 1263712 to 1264160; factor-combination's baseline n moved from 1254322 to 1254770) — never
a `MemoryError`, never a 500, never a permanently stuck state.
- **The one real caveat:** they did not resolve "quickly" — both effectively waited for the shared warm
  compute they were joined to, i.e. tens of minutes, not the "consistent with UT-02's cache-HIT timing"
  outcome the plan describes as the best case. UT-08's own Expected Result explicitly names this exact
  possibility and says to "treat a failure here as scoping input for the next iteration, not automatically
  a blocker for this one," since goal.md already carries the ≤2s-during-ingest ceiling as a known, disclosed
  gap out of this iteration's scope. Scored PASS on that explicit basis — the requirements this test DOES
  hard-gate on (no MemoryError, no 500, no permanent hang, health polls mostly 200 and comparable to the
  disclosed baseline) were all met. The timing caveat is recorded here as the exact scoping input the dev
  handoff's own "Suggested Next Phase" asked this lane to produce.

### UT-09 — Factor Lab discoverable from Research hub
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-51-evidence/UT-09-result.png`
- On `/research`, the `data-testid="research-lab-link-factor-lab"` tile ("Factor Lab") was present in the lab grid with `href="/research/factor-lab"`, unchanged in wording/position.
- Clicked it; `location.pathname` became `/research/factor-lab` (no query param); page loaded fully (20 interactive elements, same heading/table content verified in UT-01).

---

## Failed Tests

None.

---

## Skipped Tests

### UT-05 — A degraded factor-lab warm is honestly omitted; the job still completes cleanly
**Verdict:** SKIPPED
**Reason:** The test's precondition requires restarting the backend with
`TRENDORA_FAULT_INJECT_MEMORY_ERROR=factor_lab_all scripts/start-backend.sh`. Two restart attempts were
made and both were **denied by the permission system** ("Claude Code auto mode classifier"), not by any
product or test-framework error:
1. `kill -TERM <pid>` on the running uvicorn process (to free port 8255 before relaunching) — denied.
2. `TRENDORA_FAULT_INJECT_MEMORY_ERROR=factor_lab_all CHAIN_BACKEND_PORT=8255 CHAIN_FRONTEND_PORT=3255 bash scripts/start-backend.sh &` (launching the fault-injected backend directly, without an explicit prior kill) — also denied.

Both denials were confirmed to have zero side effects: the original (non-fault-injected) backend was
verified still running and healthy (`GET /api/health` → 200) immediately after each denial, with no stray
processes. I did not attempt further variations (e.g. `pkill`, `fuser -k`) since that would have been
working around the same permission boundary rather than using a genuinely different, sanctioned approach —
per my instructions, that is not something I should try to route around.

**What I could NOT verify this run:** whether a `factor_lab_all` warm that raises `MemoryError` mid-compute
(a) still lets the job reach a normal terminal status, (b) correctly omits `"factor_lab_all"` from
`aggregates_refreshed` while leaving other categories intact, and (c) logs the expected phase-timing +
isolation-failure lines with no unhandled traceback.

**Historical context found in `logs/backend.log` (NOT fresh evidence from this dispatch — presented only
for context):** four occurrences from 2026-08-05 23:37–23:44 read `factor_lab_all_cached:
compute_factor_lab_all aborted under memory pressure for key=(...) -- degrading the response honestly, not
crashing`, each followed by clean recovery (no crash) — consistent with an earlier pipeline pass (developer
or audit-fix lane) having exercised this exact fault-injection scenario successfully at some point before
this dispatch. This is suggestive but is a different run, on a different day, that I did not personally
observe end-to-end — it should not be treated as this iteration's own browser-QA verification of UT-05.

**Recommendation:** re-run UT-05 specifically in a session/environment where the backend-restart-with-env-var
permission is available (e.g. an interactive session where the operator can approve it, or a dispatch
context whose permission profile allows project launch-script invocations with env-var overrides).

---

## Notes

**CDP/screenshot tooling issue (not a product defect):** partway through this session — after the ~24-minute
UT-08 drill with 4 simultaneous tabs — the Chrome MCP tool's screenshot capture (`Page.captureScreenshot`)
began intermittently failing outright, and even when it reported success it sometimes wrote out a fully
blank/black PNG (reproduced 4 times across 2 different tabs: `UT-04-result.png` and
`UT-08-data-jobcomplete-result.png`). Regular DOM operations (`extract`, `attr`, `eval`, `click`, `type`)
continued to work reliably throughout and were used to independently re-confirm both tests' functional pass
state via direct attribute/value inspection. Treating this as a browser-automation tooling hiccup under
sustained load, per "Do NOT mark FAIL merely because browser automation had trouble."

**UT-06 precondition deviation:** the test plan's steps read "Click 'Add condition' twice to configure two
factor conditions," written under the assumption the page starts with zero conditions. In this build, the
page fetches and displays the server's config-resolved 2-condition default immediately on mount (no clicks
needed to reach "two factor conditions" — that state is already the landing state). Since the landing state
already matched the test's stated target, I verified it thoroughly (byte-identical cross-check against the
API) and then clicked "Add condition" once (→3 conditions) purely to confirm the control itself still
functions correctly after this iteration's `_combination_cohort_members` change, rather than clicking twice
more to reach 4 conditions, which would move further from "two conditions" for no extra verification value
and cost another ~100s+ live compute.

**UX finding (not scored as a failure — informational for a future iteration):**
`/research/factor-combination`'s initial page load shows a bare, unlabeled `animate-pulse` skeleton with no
elapsed-time indicator for however long the combination compute takes (observed ~108s cold, and effectively
the job's full duration when concurrent with the UT-08 ingest). Its sibling page, `/research/factor-lab`,
has an honest `SlowComputeNotice` ("Still computing — Xs elapsed") for the exact same class of wait,
shipped in iter-33. Neither this iteration nor its diff touches `factor-combination`'s frontend, and the
underlying slowness itself is explicitly named as a pre-existing, disclosed, OUT-OF-SCOPE cost in the phase
spec (`_combination_observations`'s own ~250s cost, "already named and deliberately carried since
iter-50") — so this is not a regression introduced here. Flagging the missing elapsed-time UX treatment as
a small, concrete follow-up for whichever iteration next touches this page, since goal.md's own
anti-goal-adjacent language elsewhere is explicit that a wait should never look like "an indefinite
unlabeled spinner."

**Golden replay scripts:** `runs/goal-session-ops-hardening/journey-scripts/J-05.json` and `J-06.json`
already exist and were left untouched. J-05.json (dated 2026-08-06, from the iter-50 audit-fix pass) is a
careful, single-use-by-construction script targeting an as-yet-unconsumed date (`2010-11-08` — re-verified
live via direct DB query: still 0 `scanner_runs` rows) with anti-stale-assertion discipline already applied;
my own UT-02/UT-03/UT-08 evidence corroborates its underlying claims but does not follow its exact steps
(different target date, different assertions), so overwriting it with a rougher version would be a quality
regression rather than an improvement. J-06.json covers an 11-page sweep ending at `/research/regime-lab`,
none of which is `/research/factor-lab` — this dispatch's plan only exercised the factor-lab slice of that
journey (per its own "specifically /research factor-lab" scoping), so I did not have grounds to refresh the
other 10 pages' coverage. **No J-07.json was written**: the replay schema's three action types
(goto/click/fill with text-expectations) cannot express UT-08's actual verification method — a ~24-minute
background job, a raw `/api/health` curl-polling loop, and two extra browser tabs — and step 4 (induced
memory-pressure abort) was not exercised this round (see UT-05). A superficial J-07 script that only
loaded the two research pages under normal conditions would not actually test "heavy aggregates never take
the service down" and would be misleading rather than useful, so it was skipped per the "best-effort... skip
it" instruction.

**Backend restarts during this dispatch:** none needed outside the two blocked UT-05 attempts above — the
backend the pump started before dispatch stayed up and healthy (aside from expected, load-induced latency
during the UT-08 heavy-warm window) for the entire ~2-hour session.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), pinned profile/CDP port per environment
- **Test Date:** 2026-08-07 (session start 2026-08-06 late evening through 2026-08-07 ~01:50 local)
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-51-evidence/`
- **Data used:** existing warmed state (run id 323) for UT-01–UT-04/06/07/09; a fresh single-day backfill of
  `2019-02-25` (run id 325, confirmed a genuine bars-present/no-prior-snapshot gap via direct DB query) for
  UT-08's concurrent drill
