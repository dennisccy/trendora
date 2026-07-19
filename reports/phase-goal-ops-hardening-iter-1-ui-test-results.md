# Phase goal-ops-hardening-iter-1 — UI Test Results

**Phase:** goal-ops-hardening-iter-1
**Date:** 2026-07-19
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 17/17 tests passed (0 skipped) — 16 UT test cases from the UI test plan + 1 goal-mode regression journey (J-04, row `UT-J-04`)

---

## Scope / methodology notes (read before the table)

- **Database state was not pristine at start.** A prior functional-QA pass had already run before this
  browser session started (visible in Run History timestamps from 14:41–17:14 today), including the
  exact UT-02 range (`2026-05-02 → 2026-05-29`) and the exact UT-03 range (`2026-05-02 → 2026-05-03`).
  Per UT-02's own written precondition ("if it has already been backfilled... you will instead see the
  zero-work outcome described in UT-04; that is not a failure of THIS test"), this was anticipated. Where
  this happened, it is called out explicitly per-test below, and cross-referenced against the still-persisted
  historical row that shows the fresh/productive pattern, so both code paths (productive "ok" and zero-work
  "no new snapshots") are verified with concrete evidence either live or from Run History still rendering
  correctly on screen.
- **UT-12's large-backfill test used a substitute date range.** The exact prescribed range in the test plan
  (`2025-06-01 → 2026-07-17`) had already been fully backfilled twice by the prior functional-QA pass (visible
  in Run History), so resubmitting it would only exercise the zero-work path, not real chunked progress. I
  substituted a fresh, never-touched >370-day range (`2012-01-01 → 2013-06-01`, then `2014-01-01 →
  2015-06-01`) that still has real backfill gaps, so UT-12/UT-13's accept+chunk-progress behavior could be
  observed against real work. This is a rendering/behavior check (does the UI correctly show acceptance and
  advancing chunk progress for a large range), not a re-verification of the exact arithmetic for one specific
  range, consistent with this plan's own scope note.
- **Most verification used direct DOM assertions (`eval`) in addition to screenshots** — reading
  `data-testid`/`data-state` attributes and exact text content — because several of these tests hinge on exact
  wording and color-coding that a screenshot alone can't prove byte-for-byte. Screenshot evidence is included
  for every test; a few (noted inline) came out visually blank because the viewport had scrolled to an empty
  gap between sections at the moment of capture — the DOM assertion quoted for that test is the authoritative
  record in those cases, and is quoted verbatim.
- **Backend restarts were performed manually** (`kill -9` on the uvicorn PID + relaunching
  `scripts/start-backend.sh` with the same env/log conventions `run-phase.sh`'s fanout uses), since UT-09,
  UT-14, UT-15, and J-04 all require taking the backend down. The backend was left in a healthy `ready` state
  at the end of the session (verified: `GET /api/health` → `readiness: ready`, frontend `/data` → 200).

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | `/data` loads without errors | smoke | P1 | Heading + 4 panels visible, no error card, no crash | Heading "Data Manager", subtitle, all 4 panels (Dataset coverage / Start a fetch.../ Job progress / Run history) rendered; no error card | PASS | `UT-01-result.png` |
| UT-02 | May-2026 backfill creates snapshots | happy-path | P1 | Green "ok" badge, 19/19 dates, "28 calendar days · 0 already snapshotted · 9 non-trading" | Range already backfilled by a prior functional-QA pass before this session started (per UT-02's own contingency clause) — my live submission showed the zero-work fallback (see UT-04). The productive/fresh pattern for this exact range is still visibly rendered in Run History right now: row @17:13:05, badge class `border-pos/text-pos` ("ok", green), Snapshots "19", breakdown "28 calendar days · 0 already snapshotted · 9 non-trading" — confirmed via live DOM read of that still-on-screen row | PASS (via documented fallback + on-screen historical row) | `UT-04-result-fullpage.png` (Run History table, row 6 from top) |
| UT-03 | Weekend-only backfill = zero-work state | happy-path | P1 | Grey "no new snapshots", zero-work note, "0/0 dates", "2 calendar days · 0 already snapshotted · 2 non-trading" | Live submission of 2026-05-02→2026-05-03: `job-status`="no new snapshots" (class `border-border/text-text-muted`), `zero-work-note` text exact match, "Snapshots backfilled" = "0/0 dates", `backfill-breakdown` = "2 calendar days · 0 already snapshotted · 2 non-trading" | PASS | `UT-03-result.png` |
| UT-04 | Identical re-run = zero-work state | happy-path | P1 | Grey "no new snapshots", zero-work note, "19/19 dates", "28 calendar days · 19 already snapshotted · 9 non-trading" | Live re-submission of 2026-05-02→2026-05-29: `job-status`="no new snapshots", breakdown = "28 calendar days · 19 already snapshotted · 9 non-trading" exact match, zero-work note present | PASS | `UT-04-result-fullpage.png` |
| UT-05 | Reload preserves run history | regression | P1 | Same row count before/after reload; empty-session text never appears | 36 rows before reload, 36 rows after a second reload (stable); `document.body.textContent` search for "No job has been started this session" = 0 matches at every check this session | PASS | `UT-05-result.png` |
| UT-06 | Fresh session shows latest persisted run | happy-path | P1 | No empty-session text; badge+message+"N snapshots · N trading days in range"+hint ending "from a previous session" | Fresh incognito-equivalent tab (`new_tab`, no job ever started in it): `last-run-status`="no new snapshots", snapshots line="0 snapshots · 0 trading days in range", hint="backfill job · 2026-05-02 → 2026-05-03 · from a previous session", empty-session text absent | PASS | `UT-06-result.png` |
| UT-07 | Inverted range still rejected | regression | P1 | Job NOT accepted; red error "start date X must be on or before end date Y" | Filled start=2026-06-01, end=2026-05-01, clicked Start: form-level alert text = "start date 2026-06-01 must be on or before end date 2026-05-01" (exact match); Job progress panel did not switch to a running job | PASS | `UT-07-result.png` (came out visually blank — viewport had scrolled off the alert; DOM text quoted above is the authoritative record) |
| UT-08 | Malformed date shows inline error | validation | P2 | Inline error "Enter a valid date as yyyy-MM-dd", red border, Start disabled | Typed `2026-13-40` into Start date, blurred: field error text exact match, input class includes `border-neg`, Start button `disabled=true` (even with a valid End date present) | PASS | `UT-08-result.png` |
| UT-09 | Backend unavailable shows error card | error | P2 | Red card, heading "Backend unavailable", exact body text | Stopped backend (`kill -TERM`), reloaded `/data`: heading + exact body text both present ("Dataset coverage could not load from the API. No figures are shown rather than fabricated values. Confirm the backend is running and retry."), page not blank; backend restarted and page recovered afterward | PASS | `UT-09-result.png` |
| UT-10 | Breakdown absent for non-backfill run | regression | P2 | Breakdown line completely absent (not a fabricated "0 calendar days...") for seed-load/fetch rows | Seed-load row (2026-07-15, kind "seed load"): Snapshots column = "—" exactly, no breakdown text. Fetch row (2024-01-01→2024-12-31): Snapshots column = "0" exactly, no breakdown text appended | PASS | `UT-10-result.png` (blank — viewport scrolled off; row content quoted above from direct DOM read) |
| UT-11 | `/scanner-runs` gains new dates | happy-path | P1 | Rows for 2026-05-04/05-15/05-29; click → Scanner Run detail with regime badge + stock table | All three dates present as links (`/scanner-runs/195`, `/204`, `/213`). Navigated to `/scanner-runs/195`: heading "Scanner Run", exact subtitle, "Immutable snapshot — as of 2026-05-04", green "Risk-on" regime badge, stock rows table (MRVL, VRT, SNDK...) — not empty/error | PASS | `UT-11-top.png`, `UT-11-result.png` |
| UT-12 | >370-day backfill accepted | happy-path | P1 | Accepted (no "too large" error), running badge, "chunk N/M" with M>1 | Substitute fresh range 2012-01-01→2013-06-01 (517 days, see methodology note): `job-status`="running" (blue/accent), `chunk-progress`="chunk 0/6", no "too large"/"cap" text anywhere | PASS | `UT-12-result.png` (blank — see note; DOM values quoted above) |
| UT-13 | Chunk progress advances | happy-path | P2 | Chunk N advances 0→1+; dates-done advances above 0; no range/cap error | Over a ~30s window: chunk "0/6"→"1/6"; "Snapshots backfilled" dates-done "0"→"71"→"127" (of 354); status stayed "running" throughout, no range/cap error text | PASS | `UT-13-result.png` (blank — see note; DOM values quoted above) |
| UT-14 | Interrupted job badge after restart | regression (J-04) | P1 | Badge reads "interrupted", neutral/grey, distinct from ok/no-new-snapshots/failed; row not dropped | Killed backend mid-flight twice (once for the 2012-2013 job, once for a 2014-2015 job); after each restart+reload, both rows show status "interrupted" (grey `border-border` badge, distinct text) and remain visible in Run History across a further reload/restart — not silently dropped | PASS | `UT-14-result.png` |
| UT-15 | Readiness badge boot-state sequence | regression (J-04) | P2 | 4 visually/textually distinct states: "Checking backend…" (grey), "Initializing… history N/M" (amber), "Ready" (green), "Backend unavailable" (red) | Directly observed live in the DOM: `data-state="unavailable"`/"Backend unavailable" after a hard kill; `data-state="initializing"`/"Initializing… history 89/89" during a restart's warm-up window; `data-state="ready"`/"Ready" once settled. The 4th ("Checking backend…"/`loading`) is real per source (`health-badge.tsx` lines 41-47) but is sub-second on this warm DB and round-trip latency could not catch it live — confirmed by code read, not by a live DOM capture | PASS | `UT-15-unavailable.png` (blank — see note), `UT-15-initializing.png` (blank — see note; both DOM values quoted above and in the initializing capture's raw eval result), `UT-15-ready.png` |
| UT-16 | Zero-work info is self-explanatory | ux | P2 | Plain-English badge/note/breakdown; no raw field names (`dates_total` etc.) anywhere | Confirmed via UT-02/03/04 observations (plain-English badge text, note box, breakdown phrasing) plus an explicit page-text scan for `dates_total`, `snapshots_created`, `already_snapshotted`, `calendar_days`, `non_trading_days`, `error_other` — zero matches found on `/data` | PASS | (see UT-03/04 screenshots; no new screenshot needed) |
| UT-J-04 | Goal-mode journey J-04: Non-blocking boot with visible status | regression (goal-mode journey) | P1 | See `docs/goal.md` J-04 steps 1-6 + Acceptance (single-source readiness, ≤5s first-200, honest initializing/unreachable/interrupted presentations, no whole-table boot loads) | Step1/2: restart→first `GET /api/health` 200 at **+0.868s to +2s** across 3 restarts (well under 5s budget), warm DB. Step3: direct timestamped poll captured `readiness:"initializing"` with `warmup:{done:89,total:89,status:"running"}` for a **16+ second window** on one restart (job-interruption orphan-sweep in progress) — and separately the live frontend badge itself was caught mid-transition showing `data-state="initializing"` / "Initializing… history 89/89" on a later restart. Step4: hard `kill -9` while frontend open → badge live-transitioned to `data-state="unavailable"` / "Backend unavailable" (confirmed via direct DOM read, timestamped). Step5: `fanout-backend-8255.log` contains "Application startup complete" boot lines each restart; after each hard kill the log's last lines are ordinary in-flight request logs with **no** "shutting down"/"application shutdown complete" line — confirmed by grep. Step6: both jobs killed mid-flight (2012-2013 range, 2014-2015 range) show status "interrupted" in Run History after restart, persisting across a further restart/reload — never a stuck "running" row with no live process | PASS | `UT-15-initializing.png`, `UT-15-unavailable.png`, `UT-15-ready.png`, `UT-14-result.png` (screenshots for the initializing/unavailable moments came out blank — see note; the quoted timestamped DOM/API reads are the authoritative record) |

**P1 tests:** UT-01, UT-02, UT-03, UT-04, UT-05, UT-06, UT-07, UT-11, UT-12, UT-14, UT-J-04 — **all PASS.**

---

## Passed Tests

### UT-01 — `/data` loads without errors
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-1-evidence/UT-01-result.png`
- Navigated to `http://localhost:3255/data`; heading "Data Manager" + subtitle "Grow the dataset on demand…" rendered; "Dataset coverage", "Start a fetch / backfill job", "Job progress", "Run history" panels all present in the page markdown extraction; no "Backend unavailable" card; no blank/crash.

### UT-02 — May-2026 backfill creates snapshots
**Verdict:** PASS (via the test's own documented fallback)
**Evidence:** `reports/qa/goal-ops-hardening-iter-1-evidence/UT-04-result-fullpage.png`
- The exact prescribed range (2026-05-02 → 2026-05-29) had already been backfilled by a prior functional-QA
  pass earlier the same day (Run History shows it at 14:46, 17:13:05, 17:13:49 — all before this browser
  session began). My live submission of the same range therefore hit the zero-work path (documented and
  expected by UT-02's own precondition text), which is reported under UT-04 below.
- To still verify the productive/"ok" pattern this test is actually checking, I read the still-rendered
  historical row for the FIRST backfill of this range (started 17:13:05, before my session): via direct DOM
  read, its `[data-testid="run-status"]` badge has `text="ok"` and class
  `border-pos bg-surface-2 text-pos` (green), Snapshots column "19", and
  `[data-testid="backfill-breakdown"]` text "28 calendar days · 0 already snapshotted · 9 non-trading" — an
  exact match to this test's expected result, still correctly rendering on screen right now (also serving as
  live proof of UT-05's persistence).

### UT-03 — Weekend-only backfill = zero-work state
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-1-evidence/UT-03-result.png`
- Submitted start=2026-05-02, end=2026-05-03, kind=backfill (default), clicked Start.
- `[data-testid="job-status"]` text "no new snapshots", class includes `border-border` / `text-text-muted` (grey, not green).
- `[data-testid="zero-work-note"]` text: "Zero-work outcome — every requested trading day already had a snapshot (or the range contains no trading days). No new computation was needed; this is not a failure." (exact match).
- "Snapshots backfilled" line: "0/0 dates".
- `[data-testid="backfill-breakdown"]`: "2 calendar days · 0 already snapshotted · 2 non-trading" (exact match).

### UT-04 — Identical re-run = zero-work state
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-1-evidence/UT-04-result-fullpage.png`
- Submitted start=2026-05-02, end=2026-05-29 (same as UT-02) a second time in this session.
- `job-status`="no new snapshots" (grey, same style as UT-03).
- `zero-work-note` present (same exact text as UT-03).
- "Snapshots backfilled": "19/19 dates".
- `backfill-breakdown`: "28 calendar days · 19 already snapshotted · 9 non-trading" — differs from UT-02's historical row only in the middle number (19 vs 0), exactly as specified.

### UT-05 — Reload preserves run history
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-1-evidence/UT-05-result.png`
- Counted 36 `[data-testid="run-status"]` rows, reloaded (`navigate` to the same URL), counted again: 36 (stable across a second reload with no new activity in between).
- `document.body.textContent.includes('No job has been started this session')` = `false` at every check throughout the session.
- Methodology note: a row count taken *immediately* after a job submission (before any reload) can under-count by one, because the Run History list appears to be fetched once per page load rather than live-polled — this is normal fetch-cadence behavior, not a reload-preservation bug; the actual regression check (count stable across reload-with-no-new-activity) passed cleanly.

### UT-06 — Fresh session shows latest persisted run
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-1-evidence/UT-06-result.png`
- Opened a brand-new tab (`new_tab`) to `/data` — no job ever started in that tab.
- `document.body.textContent` does NOT include "No job has been started this session".
- `[data-testid="last-run-status"]` = "no new snapshots".
- Snapshots line: "0 snapshots · 0 trading days in range".
- Panel hint: "backfill job · 2026-05-02 → 2026-05-03 · from a previous session" — matches "kind and date range, ending in 'from a previous session'" exactly.

### UT-07 — Inverted range still rejected
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-1-evidence/UT-07-result.png` (blank — viewport had scrolled past the alert at capture time; DOM read below is authoritative)
- Filled start=2026-06-01, end=2026-05-01 (end before start), clicked Start.
- Job progress panel did not switch to a running-job view.
- Form-level `role="alert"` text: "start date 2026-06-01 must be on or before end date 2026-05-01" — exact match, only one "Start" submit button existed (no ambiguous click target), page did not crash.

### UT-08 — Malformed date shows inline error
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-1-evidence/UT-08-result.png`
- Typed `2026-13-40` into Start date, blurred focus.
- `[data-testid="job-start-date-error"]` text: "Enter a valid date as yyyy-MM-dd" (exact match).
- Start-date input class includes `border-neg` (red border).
- The single Start submit button had `disabled=true`, even though the End date field held a valid value from a prior test.

### UT-09 — Backend unavailable shows error card
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-1-evidence/UT-09-result.png`
- Stopped the backend (`kill -TERM` on the uvicorn PID), confirmed port 8255 free, navigated to `/data`.
- `document.body.textContent` includes both "Backend unavailable" and the exact body copy: "Dataset coverage could not load from the API. No figures are shown rather than fabricated values. Confirm the backend is running and retry."
- Page was not blank (44KB+ of rendered HTML).
- Backend restarted and `/data` reloaded cleanly afterward (Dataset coverage / Price history text present again), leaving the environment ready for the rest of the session.

### UT-10 — Breakdown absent for non-backfill run
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-1-evidence/UT-10-result.png` (blank — viewport scrolled off; DOM read below is authoritative)
- Row with Kind badge "seed load" (2026-07-15 21:35:18, present from the committed seed): Snapshots column text = "—" exactly, no breakdown line.
- Row with Kind badge "fetch" (2024-01-01 → 2024-12-31): Snapshots column text = "0" exactly, no breakdown line appended (not "0 calendar days · 0 already snapshotted · 0 non-trading").

### UT-11 — `/scanner-runs` gains new dates
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-1-evidence/UT-11-top.png`, `UT-11-result.png`
- On `/scanner-runs`, links found for all three target dates: 2026-05-04 → `/scanner-runs/195`, 2026-05-15 → `/scanner-runs/204`, 2026-05-29 → `/scanner-runs/213`.
- Navigated to `/scanner-runs/195`: heading "Scanner Run", subtitle "The exact, immutable as-of view the scanner produced on this date" (exact match), "Immutable snapshot — as of 2026-05-04", a green "Risk-on" regime badge, and a rendered stock-rows table (MRVL, VRT, SNDK, LITE, KEYS, PWR, DELL...) — not an empty state or error card.

### UT-12 — >370-day backfill accepted
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-1-evidence/UT-12-result.png` (blank — see note; DOM read below is authoritative)
- The literal prescribed range (2025-06-01 → 2026-07-17) was already fully backfilled twice by the prior functional-QA pass, so I used a fresh, never-touched 517-day range (2012-01-01 → 2013-06-01) to get a real (non-zero-work) acceptance+chunking demonstration, per this plan's own "rendering check, not a recomputation" scope note.
- Submitted; immediately: `[data-testid="job-status"]` = "running" (class `border-accent`/`text-accent`, blue), `[data-testid="chunk-progress"]` = "chunk 0/6" (M=6 > 1), no "too large"/"cap" text anywhere on the page.

### UT-13 — Chunk progress advances
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-1-evidence/UT-13-result.png` (blank — see note; DOM read below is authoritative)
- Watched the same job from UT-12 for ~30 seconds without navigating away.
- Chunk badge: "chunk 0/6" → "chunk 1/6".
- "Snapshots backfilled" dates-done: 0 → 71 → 127 (of 354 total trading days in range).
- Status remained "running" throughout; no range/cap error appeared. (Full completion was not required or awaited, per the test's own acceptance criteria.)

### UT-14 — Interrupted job badge after restart (J-04)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-1-evidence/UT-14-result.png`
- While UT-12/13's backfill was running, hard-killed the backend (`kill -9`), restarted it (`scripts/start-backend.sh`), reloaded `/data`.
- Top Run History row (2012-01-01 → 2013-06-01): status badge text "interrupted", class includes `border-border`/`text-text-muted` (same neutral family as "no new snapshots" but distinct text, never confused with "ok"/"failed").
- Repeated the same kill/restart against a second fresh job (2014-01-01 → 2015-06-01, started specifically to re-verify this transition): also landed as "interrupted".
- Both interrupted rows remained visible (not dropped) after a THIRD restart later in the session — durability confirmed across multiple restarts, not just one.
- **Additional observation (non-blocking, flagged for the dev/auditor):** both interrupted rows' breakdown line reads "0 calendar days · 0 already snapshotted · 0 non-trading" — but the actual requested ranges span 517 and 517 days respectively (not 0). Per `GET /api/data`, the backend persists `calendar_days`/`non_trading_days`/`already_snapshotted` as literal `0` (not `null`) for a job that never reached the point of computing a real breakdown before being killed. `BackfillBreakdown`'s own doc comment states the intended contract is "renders nothing when every field is absent/null... never a fabricated '0'" — the frontend code is correct (it only suppresses when ALL FOUR fields are null), but the backend's interrupted/orphan-sweep path appears to zero-fill these fields instead of leaving them null, which produces exactly the "fabricated zero" pattern UT-10's own principle warns against, just via a different code path (interrupted-backfill) than UT-10 directly tests (fetch/seed-load). This does not fail UT-14's own written assertions (badge text/style/visibility all correct), so UT-14 is PASS, but it is worth a fix given goal.md's anti-fabrication anti-goals.

### UT-15 — Readiness badge boot-state sequence (J-04)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-1-evidence/UT-15-unavailable.png` (blank), `UT-15-initializing.png` (blank), `UT-15-ready.png` (visible) — DOM reads below are authoritative for the two blank captures
- **unavailable:** after a hard kill (frontend already open), live DOM read of `[data-testid="readiness-badge"]` returned `data-state="unavailable"`, text "Backend unavailable" — red/danger variant.
- **initializing:** on a subsequent restart (interrupting a job, triggering a real orphan-sweep warm-up window), a live DOM read caught `data-state="initializing"`, text "Initializing… history 89/89" — amber/warn variant. A separate raw-API timestamped poll on another restart showed this state (`readiness:"initializing"`, `warmup.status:"running"`, done/total 89/89) persisting for 16+ seconds.
- **ready:** once settled, `data-state="ready"`, text "Ready" — green/ok variant.
- **loading ("Checking backend…"):** confirmed to exist and be correctly coded (`components/health-badge.tsx` lines 41-47: rendered when `loading || state === null`) but is sub-second on this warm database — round-trip tool latency (network + eval overhead) could not catch it live in the DOM before it resolved to "ready" on either of two attempts. This is a code-verified pass, not a live-DOM-verified pass, for this one sub-state only; the three operationally-significant states (initializing/ready/unavailable) were all directly observed live.
- All four states use visually distinct Badge variants (`default`/grey, `warn`/amber, `ok`/green, `danger`/red per `components/ui/badge.tsx`) — confirmed via source and via the `border-*`/`text-*` class names read live for 3 of the 4.

### UT-16 — Zero-work info is self-explanatory
**Verdict:** PASS
- Read only the on-screen text from UT-02/03/04's observations: the "no new snapshots" badge + "Zero-work outcome — every requested trading day already had a snapshot…" note box together answer "did this do anything, and why not" in plain English.
- The breakdown line ("N calendar days · N already snapshotted · N non-trading") reads as plain language.
- Explicit scan: `document.body.textContent` on `/data` contains zero occurrences of the raw field names `dates_total`, `snapshots_created`, `already_snapshotted`, `calendar_days`, `non_trading_days`, `error_other`.
- Everything needed is on the same `/data` page already used to submit jobs — no new navigation required.

### UT-J-04 — Goal-mode journey: Non-blocking boot with visible status
**Verdict:** PASS
**Evidence:** `UT-15-initializing.png`, `UT-15-unavailable.png`, `UT-15-ready.png`, `UT-14-result.png` (screenshots for the live transitional moments came out blank — see note; timestamped DOM/API reads below are authoritative)

Per `docs/goal.md`'s J-04 steps and Acceptance:
1. **Restart + immediate poll:** performed 3 full backend restarts this session (`kill -9` + `scripts/start-backend.sh`). First successful `GET /api/health` after each ranged from **+0.868s to ~+2s** post-launch — comfortably under the 5-second budget, on the warm DB.
2. **≤5s first-200 on warm DB:** confirmed above (max observed +2s).
3. **≤250ms-interval poll capturing a pre-ready phase+progress payload, badge showing the same detail:** a tight poll loop (curl every ~0.1-0.15s) on the first restart captured `readiness:"initializing"` with `warmup:{done:89,total:89,status:"running","message":"history 89/89"}` at +0.868s, persisting through at least +16.5s (this restart also had to orphan-sweep an interrupted job, extending the window). On a later restart, the **live frontend badge itself** (not just the raw API) was directly caught via DOM read showing `data-state="initializing"`, text "Initializing… history 89/89" — never a bare "Backend unavailable" during this window.
4. **Kill → explicit unreachable/crashed presentation, visibly distinct from initializing:** a hard `kill -9` with the frontend already open produced a live badge transition to `data-state="unavailable"`, text "Backend unavailable" (red/danger — distinct Badge variant from initializing's amber/warn).
5. **Persistent logfile has boot events; ends abruptly (no clean-shutdown line) after the simulated crash:** `fanout-backend-8255.log` contains "Application startup complete" for each restart (`grep -c` = 1 per cycle checked); immediately after each hard kill, the log's final lines are ordinary in-flight `INFO: ... GET ... 200 OK` / `404 Not Found` request lines — `grep -i "shutting down\|application shutdown complete\|Finished server process"` found **zero matches**, confirming the abrupt (crash-like) ending a killed process leaves behind.
6. **Restart → mid-flight job shows an explicit interrupted state, not a stuck "running" row:** two separate jobs killed mid-flight (2012-01-01→2013-06-01 and 2014-01-01→2015-06-01) both show `status: "interrupted"` in Run History after their respective restarts, and **both remained visible with the correct status** across a further restart later in the session (no stuck "running" row with no live process, no silent drop).

**Note carried over from UT-14:** the interrupted jobs' breakdown fields are persisted as fabricated zeros rather than null — see that finding above; it does not affect any of J-04's six numbered steps or its Acceptance bullets, all of which are about readiness/logging/interrupted-status, not the breakdown line.

**Golden replay script:** not written for this journey. J-04's steps require killing/restarting the OS-level
backend process and asserting against a server logfile — none of that is expressible in the 3-action
(`goto`/`click`/`fill`) browser-only replay schema `demo_runner.py` supports, so per the "best-effort, skip if
you cannot produce a clean script" rule this journey is left to fall back to the LLM lane on the next
iteration.

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Additional Observations (non-blocking)

1. **Fabricated-zero breakdown on interrupted backfill rows** (see UT-14 above in detail). An interrupted
   backfill/both/rebuild run persists `calendar_days`/`non_trading_days`/`already_snapshotted` as `0` instead
   of `null`, so its Run History breakdown line reads "0 calendar days · 0 already snapshotted · 0
   non-trading" even when the actual requested range was hundreds of days — the exact "fabricated zero"
   pattern this iteration's own `BackfillBreakdown` component doc comment and UT-10 both explicitly guard
   against for other row kinds. Recommend the backend's interrupted/orphan-sweep path leave these fields
   `null` (matching the fetch/seed-load convention already correct elsewhere) rather than zero-filling them.
   Reproduced twice (two different interrupted jobs), so this is a systemic behavior, not a one-off.
2. **Run History does not appear to live-poll.** A row count taken immediately after a job submission can
   under-count by one until the next full page fetch (see UT-05 methodology note). Not a defect against any
   written test in this plan (UT-05's actual reload-stability assertion passed cleanly), but worth knowing if
   a future test expects the table to update live without a reload.
3. **Frontend readiness-badge idle poll cadence is slow (~30s)** once "Ready" — by design, per
   `poll_idle_interval_seconds: 30.0` in the health payload — so the badge can visibly lag several seconds to
   ~30s behind an actual backend outage/recovery. This is a reasonable trade-off (avoids hammering `/health`
   once steady) and is why UT-15's "unavailable" and "initializing" captures required waiting/timing rather
   than an instant check; not a defect.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`)
- **Test Date:** 2026-07-19
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-1-evidence/`
- **Final environment state:** backend `readiness: ready` (warmup 89/89 ok), frontend `/data` → HTTP 200, 38 total rows in Run History (34 pre-existing + 4 created this session: the UT-02/04 resubmit, UT-03's weekend run, and the two interrupted large-backfill jobs from the restart cluster).
