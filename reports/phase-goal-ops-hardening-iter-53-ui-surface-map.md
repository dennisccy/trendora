# Phase goal-ops-hardening-iter-53 — UI Surface Map

**Phase:** goal-ops-hardening-iter-53
**Date:** 2026-08-08
**Written by:** ui-impact-analyst

---

## Scope note

`Frontend Present: no` in `plan.md` is correct at the file-diff level — zero `apps/frontend/` files changed
(verified directly: both `git diff --stat -- apps/frontend/` and `git status --porcelain -- apps/frontend/`
are empty). Every row below is therefore an *existing, unmodified* frontend surface whose underlying
**reliability** (rows 1–3) or **correctness under a narrower fetch** (rows 4–6) was targeted or must be
re-confirmed by a backend-only change. Unlike iter-52's equivalent attempt (which measured worse), this
iteration's own live measurement (`reports/perf-budgets.md` Item X / Addendum 15) found the *targeted*
reliability improvement was achieved for both phases this iteration aimed at, while the system-wide picture
narrowed rather than closed — the "Why Changed" and "What to Test" columns reflect that honest, mixed
status. See `reports/phase-goal-ops-hardening-iter-53-user-visible-changes.md` for the full narrative.

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| All pages (global header) | `HealthBadge` readiness pill (`data-testid="readiness-badge"`, `components/health-badge.tsx`, file unchanged) | Changed behavior — targeted, **achieved for the two treated causes** | This iteration bounded two backend finalize-tail steps (`coverage_membership_timeline_refresh`, `market_phase_warm`) that were each fetching a symbol's entire multi-decade price history to read a small trailing window off the end of it — the actual measured cause of the badge's underlying `GET /api/health` poll going unanswered during those steps. The badge's own rendering/trigger logic is unchanged; only the backend's failure frequency from these two specific causes was targeted. | Start a fetch/backfill job on `http://localhost:3255/data` (see the `/data` Job Form row below) and continuously watch the pill in the top-right of the header. This iteration's own drill measured **zero** flips attributable to the two treated steps (down from 1 each) but **one** flip attributable to a third, untreated step (`per_date_coverage_warm`). Record what you observe; do not grade a single flip as a new bug — do grade a flip that never recovers, or a fabricated "Ready" during a failing poll, as a real fail. |
| All pages (below header) | `PreflightBanner` (`data-testid="preflight-banner"`, `components/preflight-banner.tsx`, file unchanged) | Changed behavior — targeted, **achieved for the two treated causes** | Reads the exact same shared readiness poll as `HealthBadge` (no second fetch). Same underlying condition as the row above, surfaced through a second, more attention-grabbing element. | During the same job-watching session as the row above, note every time this full-width banner turns red with `data-verdict="NO-GO"` and the reason text "Backend is unavailable — the preflight check could not run." Same recording rule as the badge row: a single occurrence traceable to a job's finalize tail is the known, disclosed, not-fully-closed condition — not automatically a new defect. |
| `/data` | "Start a fetch / backfill job" panel — `JobForm` (`Start date`/`End date`/`Job kind`/"Start" button, `app/data/page.tsx`, file unchanged) | Unaffected — entry point for the row above | Not touched this iteration; included because it is the only entry point that can trigger the two treated finalize-tail code paths — a broken form here would block verifying every row above. | Navigate to `http://localhost:3255/data`, confirm the "Start date" and "End date" fields (`data-testid="job-start-date"` / `"job-end-date"`) are pre-filled from the first detected coverage gap, "Job kind" defaults to "Backfill snapshots", and the "Start" button is enabled (not greyed out). |
| `/data` | "Job progress" card — job status badge + stage timings (`data-testid="job-status"`, `data-testid="stage-timings"`, `app/data/page.tsx`, file unchanged) | Changed behavior (timing) — two treated sub-phases faster; total time measured **worse**, for unrelated reasons | The two treated steps' own elapsed time dropped under the same concurrent load (`market_phase_warm` 26.26s → 0.73s; `coverage_membership_timeline_refresh` 46.05s → 40.54s). The job's overall finalize-tail total is nonetheless measured at 1,559.30s vs 1,261.42s previously (29.9% vs 5.1% over the ~1,200s budget) — the developer's own analysis attributes this to two OTHER, untouched steps subject to scheduling variance from a concurrent research-request stream, not to this iteration's change. | Start a backfill job on `http://localhost:3255/data` (leave the pre-filled dates, "Job kind" = "Backfill snapshots", click "Start") and time how long the status badge (`data-testid="job-status"`) stays in a running state before reaching a terminal status (e.g. "ok"). Record the elapsed time; a run resembling this iteration's own measured date may exceed 20 minutes. |
| `/data` | "Refreshed: …" summary line (`data-testid="aggregates-refreshed"`, `app/data/page.tsx`, file unchanged) | Unaffected — regression check (TC-4, AG-3) | This iteration only changes HOW MUCH price history is fetched per symbol inside the two treated steps, never WHAT is computed or disclosed. The list of refreshed categories must be byte-identical to before. | Once a job from the row above reaches a terminal status, read the "Refreshed:" line and confirm it lists the same category set (e.g. "coverage", "membership timeline", "market phase", "forward aggregates", "research hot keys", "factor lab all", "drawdown expectations") a completed backfill listed before this iteration — no category should appear or disappear because of this iteration's change alone. |
| `/data` | "Dataset coverage" + "Universe resolution as of …" + membership-timeline panels (`data-testid="universe-count"`, `data-testid="universe-diagnostic-panel"`, `app/data/page.tsx`, file unchanged) | Unaffected — regression check (AG-3 byte-identity) | These panels are the on-screen consumers of `coverage_membership_timeline_refresh`'s stored output — the exact function this iteration changed to fetch a bounded trailing window instead of full history. A byte-identity integration test (`test_data_manager_membership_cache.py`) and 4 new tests in `test_universe_resolver.py` already prove the disclosed `.bars` count and excluded-by-reason totals are unaffected. | Navigate to `http://localhost:3255/data` and read the "Universe (as of date)" figure, the "Admitted" figure in the "Universe resolution as of …" panel, and its four excluded-by-reason figures (below min history, stale series, below min price, below min liquidity). Confirm admitted + the four excluded reasons sum to the candidate-pool count shown in the same panel, and that none of these read "—"/NA/error. |
| `/` (Dashboard) | "Market Phase & Severity" card (`PhaseGlanceCard`, `app/page.tsx`, file unchanged) | Unaffected — regression check (AG-3 byte-identity) | The on-screen consumer of `market_phase.compute_market_phase`'s stored output — the exact function this iteration bounded (VIX gate now reads one bar via `close_on` instead of a symbol's entire history; benchmark-drawdown window and recovery-turn MA now fetch a bounded trailing window). Three new byte-identity unit tests in `test_market_phase.py` already prove the computed value is unaffected. | Navigate to `http://localhost:3255/`, read the "Market Phase & Severity" card's phase label and 0–100 severity score, then click its "Why this regime — component breakdown" disclosure and confirm real component rows render (not an error or "—"). Values must match what the same as-of showed before this iteration. |
| `/data` | "Background compute" panel (`data-testid="background-compute-panel"`, `app/data/page.tsx`, file unchanged) | Unaffected — regression check (J-09, required-still-passing) | Not touched this iteration; included because J-09 is a required-still-passing journey this pass's browser-qa lane must replay. | After viewing a historical as-of on `/backtest` (click "Previous available date" a few times), navigate to `/data` and confirm this panel shows either an active in-flight entry or an updated "Last outcome" summary, with the footer text "Since the last backend restart — this history is process-lifetime only, never persisted." still present. |
| `/backtest` | Forward-test scorecard + evidence section (`data-testid="evidence-aggregate"`, `"evidence-summary"`, `app/backtest/page.tsx`, file unchanged) | Unaffected — regression check (J-08, required-still-passing) | Not touched this iteration; included because J-08 is a required-still-passing journey this pass's browser-qa lane must replay. | Navigate to `http://localhost:3255/backtest`, confirm the forward-test scorecard renders with real (non-placeholder) rows, and scroll to the evidence section to confirm it shows "Snapshots contributing" with a real numeric count, not a cold-recompute spinner. |
| `/`, `/data`, `/backtest` | Sidebar navigation (`components/sidebar.tsx`, file unchanged) | Unaffected — discoverability/regression check | Entry points are unchanged; included to confirm the global badge/banner (rows 1–2) render consistently across distinct pages, not only on `/data`. | Click through "Dashboard" (`/`), "Data Manager" (`/data`), and "Backtest" (`/backtest`) in the left sidebar; confirm the readiness pill (and, when not in a quiet "GO" state, the preflight banner) appear identically in the header/sub-header area on all three pages. |
| Global (all pages) + backend process | Persistent backend logfile (`logs/backend.log`, path unchanged) + boot/crash presentation (badge + banner) | Changed evidence status — **first-ever capture this iteration** (TC-6, J-04 steps 3–5) | J-04's boot/crash/interrupted-job behavior is already-shipped, unchanged code, but its badge-detail, crashed-presentation, and logfile-truncation evidence has never actually been captured by a prior lane pass — this iteration's spec explicitly names it as a piggyback deliverable (TC-6) riding on the mandatory 8-journey lane. | Restart the backend (`scripts/start-backend.sh`) and, from that instant, poll `GET /api/health` at ≤250ms intervals while watching the header pill — capture a screenshot/DOM read showing `data-state="initializing"` with "Initializing… history n/m". Then kill the process (`pkill -9 -f "uvicorn app.main:app"`), capture a screenshot/DOM read showing `data-state="unavailable"`/`data-verdict="NO-GO"`, and run `tail -5 logs/backend.log` to confirm the file ends abruptly (no clean-shutdown line) after boot entries. |

<!-- Change Type legend used above: Changed behavior (targeted, achieved) | Changed behavior (timing, mixed) | Unaffected (regression check) | Changed evidence status (first capture). No New page/component/form/nav rows exist this iteration — zero frontend files changed. -->

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/universe_resolver.py` — `resolve_candidate` accepts an optional `bar_count`
  (defaults to `len(bars)`, unchanged for every existing caller); `resolve_with_reasons` now fetches a
  bounded trailing window (`bars_asof_window(..., adv_window_days)`) per admitted-eligible symbol instead
  of the full `<= as-of` price-history prefix; a `_fault_inject_memory_error("coverage_membership_timeline")`
  call added at the treated fetch. Scheduling/fetch-bounding only, no UI surface of its own.
- `apps/backend/app/engine/market_phase.py` — `_latest_vix_on_or_before` now calls `close_on` (a single
  bisected bar) instead of building a symbol's entire history; `_severity_reading`'s benchmark-drawdown
  window and `_trailing_ma_reclaimed`'s recovery-turn window now fetch a bounded trailing window
  (`bars_asof_window`) before applying the same calendar-day filter as before; a
  `_fault_inject_memory_error("market_phase")` call added inside `_severity_reading`. Fetch-bounding only,
  no UI surface of its own.
- `apps/backend/app/engine/data_manager.py` — `_FAULT_INJECT_SITES` gains `"coverage_membership_timeline"`
  and `"market_phase"`; `_refresh_ingest_aggregates`'s `coverage_membership_timeline_refresh` phase gains a
  dedicated `except MemoryError: ... _release_process_memory()` branch (previously only a generic
  `except Exception`) ahead of the existing generic handler. Reliability-only, no UI surface of its own —
  the `/data` "Refreshed:" line's honest-omission behavior on a memory error was already correct and is
  unchanged (see the `/data` "Refreshed:" row above).
- `apps/backend/tests/test_universe_resolver.py`, `test_market_phase.py`,
  `test_data_manager_membership_cache.py`, `test_data_manager.py` — new byte-identity and fault-injection
  unit/integration tests proving the bounded fetch changes nothing computed or disclosed. Test-only, no UI
  impact.
- `reports/perf-budgets.md` — new `## Item X` / `### Addendum 15` (append-only). An internal engineering
  report, not part of the product UI.
- `runs/goal-session-ops-hardening/state/assumptions.md` — unchanged this pass (no new judgment call
  beyond the already-logged iter-53 decomposer scoping entry). No UI impact.

---

## Summary

- **Frontend surfaces changed (code):** 0 — zero `apps/frontend/` files touched this iteration.
- **Frontend surfaces with targeted-and-achieved behavior change (for their specific cause):** 2 — the
  global readiness badge's and preflight banner's "unavailable" flip frequency attributable specifically to
  `coverage_membership_timeline_refresh` and `market_phase_warm` (both measured at zero, down from 1 each).
- **Frontend surfaces with a mixed/disclosed timing change:** 1 — `/data`'s "Job progress" total elapsed
  time (two treated sub-phases faster; system-wide total measured worse for unrelated, untouched reasons).
- **Frontend surfaces confirmed unaffected (regression checks only):** 6 — `/data`'s "Refreshed:" line
  content, `/data`'s coverage/universe-diagnostic/membership-timeline panels, the Dashboard's "Market Phase
  & Severity" card, `/data`'s Background compute panel, `/backtest`'s evidence section, sidebar navigation.
- **Frontend surfaces getting first-ever evidence capture (no code change, new proof only):** 1 — J-04's
  badge/banner/logfile boot-and-crash presentation.
- **New pages/routes:** 0
- **Modified components:** 0
- **Navigation changes:** no
- **Backend-only changes:** 6 (3 product-code files + 4 test files) + 1 report addendum.
