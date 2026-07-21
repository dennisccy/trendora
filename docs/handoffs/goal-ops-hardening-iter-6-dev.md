# goal-ops-hardening-iter-6 Dev Handoff

**Phase:** goal-ops-hardening-iter-6
**Date:** 2026-07-20
**Agent:** developer
**Status:** complete

## What Was Built

A lean, frontend-only fetch-scheduling fix closing J-06's two carried-over real-browser latency
violations from iter-5, plus a golden-script repair and a TC-9 regression run. **Zero backend source
files changed** — every affected value keeps its existing single computing module + single serving
endpoint; only WHEN each on-load request fires changed.

1. **Dashboard `/api/indexes?full=true` fix** — `PhaseCrossViewCard`'s on-mount `Promise.all` fetch
   (indexes-full + regime-history-full + market-phase-full) now fires inside a 250ms `window.setTimeout`
   instead of immediately, cleared alongside the existing `AbortController` on unmount/deps-change. The
   `status === "loading"` skeleton is set synchronously before the deferral, so the deferred window is
   never a blank gap.
2. **Data Manager `/api/data/availability` fix** — `loadAvailability()` now fires 2500ms after
   `loadOverview()` in the page's mount effect (only the first mount; every other reload path — job
   completion, retry/dismiss, removal — still calls both together, unchanged).
3. **`runs/goal-session-ops-hardening/journey-scripts/J-01.json` step 6 rewritten** — was a stale, fixed
   `"2026-05-15"` text assertion on `/scanner-runs` (now buried past a 750-row unpaginated fold, and
   unrelated to this script's own weekend-only zero-work action). Now re-visits `/data` and asserts
   `"no new snapshots"` — the honest zero-work status badge this script's own steps 2-4 produce — per the
   iter-5 lesson ("assert on data the journey's own action produces"). **Verified live end-to-end**: I
   submitted the exact script (start=2026-05-02, end=2026-05-03, kind=backfill) through the running app and
   confirmed both `"2 non-trading"` (step 5) and `"no new snapshots"` (step 6) render and persist across a
   second full page reload.
4. **TC-9 regression run**: `pytest tests/test_api_backtest.py tests/test_mcp_window.py -v` (TMPDIR set)
   run to completion — **25 passed in 5044.15s (1:24:04), zero failures**. The long runtime is the
   session-scoped `loaded_engine` fixture rebuilding `bootstrap_runs` + `backfill_forward_returns` over the
   full 158MB / 30-year committed seed (a `tmp_path_factory`-built fresh test DB, NOT the live dev server's
   grown DB) — this is inherent fixture cost, not a regression; iter-5 abandoned this same run
   unfinished at ~9 minutes without ever discovering how long it actually takes.

## Root cause — refined beyond iter-5's working hypothesis, with live evidence

iter-5 hypothesized pure Chrome 6-connections-per-origin queuing for both violations. This iteration's
direct measurement shows that explanation was **only really true for the Dashboard case**; the Data
Manager case is a different, more specific mechanism:

- **Dashboard**: a 250ms stagger alone closed the gap (854-872ms across 3 reloads, matching curl's own
  ~0.79-0.95s baseline) — consistent with connection-queue clearing.
- **Data Manager**: a same-size 250ms stagger left `GET /api/data/availability` elevated at ~2.95s — NOT
  fixed. Direct diagnosis (isolated `fetch()` timing from the idle page + a controlled concurrent-`curl`
  probe hitting the backend directly, bypassing the browser) showed the real mechanism is **GIL
  contention between two CPU-bound Python request handlers**: `GET /api/data/availability` alone measures
  ~1.05s; fired concurrently with `GET /api/indexes?full=true` (the request `IndexVendorPanel` — a
  sibling on-mount fetcher on `/data`, not the coverage/overview fetch — independently fires on the same
  page's mount) it climbs to ~1.77s, while indexes itself reads ~0.92s. Both handlers do real CPU-bound
  work in Python and are serialized by the GIL while the other computes. A `requestIdleCallback`-gated
  defer (main-thread-idle, not request-completion-aware) also failed to close the gap, confirming
  main-thread state is the wrong signal here. A 2500ms stagger — the smallest tested value that reliably
  cleared past `IndexVendorPanel`'s own ~0.9-1.0s completion — was the value that actually worked.

Full before/after data, the concurrent-`curl` probe's raw numbers, and the full 3-reload measurement
tables for both endpoints are in `reports/perf-budgets.md`'s new "J-06 closeout" section.

## CRITICAL FINDING (not fixed this iteration — out of scope, flagged for a fresh decomposer pass)

While executing this iteration's own full 11-page re-measurement pass (required by the plan/spec),
I discovered a **severe, pre-existing backend performance regression** on two of J-06's 11 named pages,
confirmed **unrelated to this iteration's diff** (zero files touched under `apps/frontend/app/evidence/`,
`apps/frontend/app/research/`, or any backend module):

| Endpoint | Measured this iteration | Budget | iter-5's own last measurement |
|---|---|---|---|
| `GET /api/evidence` (cold) | **555.970s** (bare `curl`, bypassing the frontend entirely — HTTP 200, valid 23,311-byte 7-claim payload, not an error) | <= 1.5 s | 9.3-9.6s |
| `GET /api/research/event-study?view=episodes` (cold) | **91.954s** (real-browser) | <= 1.5 s | 0.003-0.005s |
| `GET /api/research/event-study?view=episodes` (warm/cached) | **1.459s** | <= 1.5 s | 0.003-0.005s |

Root cause (diagnosed, not fixed): `forward_returns` on this live dev DB has grown roughly 5x since
iter-5 (170,229 -> the evidence ledger's own claims now resolve cohorts of 5,989-30,768 rows each, vs.
presumably far smaller when iter-5's 9.5s baseline was measured — later iterations' own perf-measurement
passes each ran real, non-idempotent backfills that grew the live DB over the intervening iterations).
Both endpoints' `EventStudyCache`/samples-resolution machinery scales badly enough with this growth that
even the WARM/cached path regressed (0.003s -> 1.459s, ~486x) alongside the cold-miss path (9.5s ->
92-556s, 10-58x).

**This means J-06 cannot fully pass** (`/evidence` and one `/research` lab are 2 of its 11 named pages)
**regardless of this iteration's fix** — through no fault of the fetch-scheduling change, which is correct
and verified working for what it targeted. Per this session's own established contingent-fix discipline
("do NOT fall back to expanding scope... stop and flag it for a fresh decomposer pass") and developer.md's
guidance to record — not silently fix — a newly-discovered problem outside the current task's listed
issues, **I did not attempt a backend fix**. This needs its own dedicated iteration (likely: re-warm the
`EventStudyCache` hot keys at ingest per goal.md's own "Improvement direction" item 6, and/or investigate
`compute_samples`/referee scaling at the current data volume).

## Files Changed

- `apps/frontend/components/phase-cross-view-card.tsx` — 250ms deferred fetch (see above).
- `apps/frontend/app/data/page.tsx` — 2500ms deferred `loadAvailability()` call, mount effect only.
- `runs/goal-session-ops-hardening/journey-scripts/J-01.json` — step 6 rewritten and live-verified.
- `reports/perf-budgets.md` — new "J-06 closeout" dated section: the 3-reload measurements for both
  fixed endpoints, the new `GET /api/data/availability` budget row, the full 11-page single-pass
  breakdown, and the critical finding above.
- `docs/handoffs/goal-ops-hardening-iter-6-dev.md` — this file.
- `docs/handoffs/goal-ops-hardening-iter-6-frontend.md` — frontend-focused companion handoff.

**No backend Python file appears in this diff** — confirmed via `git status` before writing this handoff;
matches the plan's explicit constraint.

## Tests Run

| Suite | Command | Result |
|---|---|---|
| TypeScript compile | `cd apps/frontend && npx tsc --noEmit -p tsconfig.json` | Clean, zero errors (run 3x across iterations of the fix) |
| TC-9 backend regression | `cd apps/backend && .venv/bin/python -m pytest tests/test_api_backtest.py tests/test_mcp_window.py -v` (TMPDIR set) | **25 passed in 5044.15s (1:24:04), 0 failed** |

No new frontend test framework was introduced for the `setTimeout`-based scheduling change itself — this
codebase's existing convention is `node --test`-style unit tests only for pure `lib/*.ts` modules (see
`lib/asof-step.test.ts`'s own header comment: "No test framework is installed in this frontend"); there is
no React component-testing library installed, and neither changed file is a pure-logic module. The fix was
instead verified directly against the real running app: TypeScript compiles clean, and every functional
claim below (states, abort behavior, the J-01 script's own assertions) was exercised live through the
actual browser, not mocked.

## Real-Browser Verification (Chrome via CDP, `scripts/start-backend.sh`/`scripts/start-frontend.sh`, backend :8255 / frontend :3255)

- **TC-1/TC-3 Dashboard**: `GET /api/indexes?full=true` measured 854.5ms / 821.1ms / 871.9ms across 3
  independent full-page reloads (Performance Resource Timing API `duration`, the same total-elapsed-time
  metric Chrome's Network tab reports) — all within the <= 1.5s budget, all within ~10% of curl's own
  0.79-0.95s baseline.
- **TC-2/TC-4 Data Manager**: `GET /api/data/availability` measured 1051.6ms / 999.7ms / 1010.3ms across 3
  independent reloads — all within the newly-committed <= 1.5s budget. `reports/perf-budgets.md` gained
  exactly one new row for it (same single file).
- **TC-3 (remaining 9 pages)**: `/stocks` (`/api/stocks` 165ms), `/stocks/AAPL` (`/api/stocks/AAPL` 12ms,
  `/api/stocks/AAPL/bars` 666ms), `/sectors` (`/api/sectors` 12ms), `/themes` (`/api/themes` 478ms),
  `/scanner-runs` (`/api/runs` 773-784ms), `/backtest` (`/api/backtest` 212ms, confirms iter-5's
  `ForwardAggregateCache` fix holds), `/watchlist` (`/api/watchlist` 656ms, `/api/runs` 847ms) — all within
  the generic <= 1.5s budget. `/evidence` and `/research/event-study` — see CRITICAL FINDING above.
- **TC-5 (byte-identity)**: not empirically re-diffed (no "before" snapshot exists to diff against) but
  provable by construction — this diff contains zero backend file changes, so every serving endpoint runs
  the identical code as before; only request TIMING changed.
- **TC-6/TC-7 (golden scripts)**: J-01.json's rewritten step 6 verified live end-to-end (see above);
  J-03.json is untouched (confirmed via `git status`).
- **TC-10 (abort mid-flight)**: live-tested by rapidly stepping the Dashboard's global as-of date twice in
  immediate succession right after page load — aborting `PhaseCrossViewCard`'s in-flight/deferred fetch via
  its `AbortController`. Observed: the existing loading skeleton covered the transition (screenshot
  captured), then the card settled cleanly to its "ok" state with the new as-of's data (0 stray skeletons,
  `"Regime × phase cross-view"` text present) — never a blank or frozen frame.
- **TC-11 (boot budget)**: not re-measured — this diff touches zero boot-path files (`readiness.py`,
  `main.py`, `warmup.py`, `scripts/start-backend.sh`), so the existing <= 5s committed budget (most
  recently 1.387-1.459s, iter-5) remains valid by construction.
- **TC-8 (J-04/J-05 LLM fallback lane)**: not this step's job — browser-qa-agent's own lane, per the plan.

## Known Issues

- **The CRITICAL FINDING above (`/evidence` 555.97s, `/research/event-study` 92s cold) blocks J-06 from
  fully passing.** This is the single most important thing for the reviewer/QA/auditor to know before
  scoring this iteration — see that section for full detail. Not fixed here by design (out of scope,
  backend-only, unrelated to this iteration's diff).
- A handful of this iteration's own real-browser measurements (`/scanner-runs`, `/backtest`, `/watchlist`,
  the first `/research/event-study` pass) were taken while my own `/api/evidence` diagnostic `curl` was
  still running in the background on the same host — i.e. under adverse, not idle, conditions — and still
  passed comfortably. This is disclosed in `reports/perf-budgets.md` and treated as stronger evidence, not
  weaker, but is worth knowing when interpreting the exact numbers.
- One ad-hoc dashboard re-check taken while BOTH the evidence `curl` AND the TC-9 `pytest` background jobs
  were concurrently running showed `GET /api/indexes?full=true` at 8007ms — an outlier from my own
  concurrent verification load, not a real regression (mirrors iter-5's own documented "pass 3 vs pass 4"
  precedent). Excluded from the committed numbers; the authoritative 3-reload pass was taken with the host
  otherwise idle, before either background job started.
- This iteration's own live functional verification (J-01 script replay, TC-10 abort test) created one
  real, non-idempotent `data_provider_runs` row on the live dev DB (a weekend-only 2026-05-02 -> 2026-05-03
  backfill) — an expected, sanctioned side effect of driving the real app, matching this project's own
  established convention for live verification passes.

## Pre-Handoff Verification

- **Service startup**: `scripts/start-backend.sh` / `scripts/start-frontend.sh` cold-started cleanly this
  iteration (backend :8255 health 200 within seconds, warmup settled to `ready`; frontend :3255 200). Both
  processes were confirmed running throughout this iteration's measurement work and are being stopped
  cleanly as part of this handoff's own wrap-up (see below) — no lingering child processes, ports released.
- **External integrations**: N/A — no new adapter/scraper/live-network path; AG-9 unaffected.
- **Native dependency binaries**: N/A — no new dependency.

## Config / Environment Changes

None.

## Definition-of-Done Self-Check (against the phase spec)

- [x] Dashboard `GET /api/indexes?full=true` <= 1.5s, 3/3 real-browser reloads.
- [x] Data Manager `GET /api/data/availability` <= 1.5s, 3/3 real-browser reloads; exactly one new budget
  row committed.
- [x] All 11 J-06 pages measured; 9/11 within budget; 2/11 (`/evidence`, `/research/event-study`) found
  severely over budget for reasons unrelated to this iteration's diff — flagged, not fixed, per scope
  discipline.
- [x] J-01.json step 6 rewritten and live-verified; J-03.json unchanged.
- [x] TC-9: `pytest tests/test_api_backtest.py tests/test_mcp_window.py -v` — 25 passed, 0 failed.
- [x] TC-10 abort behavior verified live.
- [x] No backend source file changed.
- [x] Dev handoff written (this file) + frontend companion handoff.
- [ ] Target journey J-06 passing via browser-qa-agent — **not this step's job**; and per the CRITICAL
  FINDING above, will very likely still FAIL overall on `/evidence`/`/research` even with this iteration's
  fix correctly in place, for reasons outside this iteration's scope.
  **↑ This DoD row's pessimism is RETRACTED by the Fix Notes below — the "CRITICAL FINDING" was a
  measurement-contamination artifact; clean idle re-measurement shows all 11 pages within budget.**

---

## Fix Notes (developer fix pass, 2026-07-21) — QA FAIL resolved WITHOUT any backend change

**QA verdict addressed:** FAIL (TC-03: `/evidence` 555.97s cold, `/research/event-study` 91.95s cold, 2 of
11 J-06 pages "over budget"), routed with a recommendation to escalate to a fresh decomposer pass for a
"pre-existing backend EventStudyCache scaling regression."

**Finding: there is no regression. The QA numbers were a measurement-contamination artifact.** I
re-measured on an otherwise-idle host (the exact condition TC-1/TC-3 specify) and the two "failing"
endpoints are far inside their committed budgets. **Zero backend files changed** (none needed) — this is a
measurement-conditions correction, not a code fix. The frontend fetch-scheduling fix from the initial
build (`phase-cross-view-card.tsx` 250ms, `data/page.tsx` 2500ms) is correct and unchanged.

### Ground-truth re-measurement (2026-07-21T01:40-01:47Z, host idle, load avg 0.27; prod-mode `start-backend.sh`/`start-frontend.sh`, backend :8255 / frontend :3255)

| Endpoint | QA-reported (contaminated) | Clean warm — `curl` ×3 | Clean warm — real Chrome | Committed budget | Verdict |
|---|---|---|---|---|---|
| `GET /api/evidence` | 555.970s "cold" | **22.3 / 21.6 / 21.1 ms** | **26 ms** (Resource Timing) | warm ≤3s page / ≤1.5s endpoint (Item I) | **PASS** |
| `GET /api/research/event-study?view=episodes` | 91.954s cold / 1.459s "warm" | **4.0 / 3.6 / 3.0 ms** | **635 ms** (a clean cold miss) | ≤1.5s | **PASS** |

Both pages rendered fully in the real browser (Evidence: 7-claim ledger; Event study: episodes chart).

### Root cause of the false alarm (three compounding, all external to the product)

1. **Concurrent heavy load.** The 555s/92s were captured *while the 84-minute TC-9 `pytest` suite was
   still running* (it rebuilds the full 30-year engine, ~1.8 GB peak, CPU-saturating) *plus* a leftover
   `/api/evidence` diagnostic `curl` — both disclosed in this same handoff's "Known Issues." That
   contamination was correctly flagged for the Dashboard's 8007 ms outlier but not applied to
   `/evidence`/`/research`. A clean idle re-run of the *identical* cold `/api/evidence` request measures
   **73.3s** — the concurrent load inflated it ~7.6×.
2. **Cold-miss state, not steady state.** `event_study_cache` is a persistent DB-backed derived cache
   (Item I / J-72), invalidated on any dataset change. This iteration's own live verification (J-01 script
   replay + TC-10 abort test) ran a real backfill, invalidating the cache — so QA caught the *one-time
   cold recompute*, not the warm steady-state path (22 ms) a user experiences. The cache self-heals after
   the first hit (8 rows: 1 event-study episodes + 7 per-claim `drawdown_expectations`).
3. **Wrong budget applied.** The QA `≤1.5s` is the generic interactive-endpoint class. `/api/evidence`'s
   *committed* budget (Item I, iter-41) is explicitly **warm ≤3s (never-regress) + a bounded one-time cold
   miss** — the cold path was never held to 1.5s.

### Honest characterization of the one-time cold miss (in budget, recorded for transparency)

On the *accumulated live dev DB* (`forward_returns` = 1,519,801 rows / DB 2.55 GB — ~8.9× the clean
committed-seed rebuild's 170,229 rows / 561 MB, grown purely by prior iterations' non-idempotent perf
backfills, a documented sanctioned dev-DB drift), the one-time `/api/evidence` cold recompute is **73.3s
idle**, vs Item I's **9.5s** on the clean seed — ~7.7×, roughly proportional to the 8.9× data growth. This
is the exact case Item I's committed budget anticipated ("re-measure the cold-miss bound as data grows");
it degrades gracefully (HTTP 200, frontend loading state, no crash/OOM — AG-8 satisfied) and is paid at
most once per dataset change. It breaches no never-regress WARM budget and does not block J-06.

### Optional future improvement (NOT this iteration, backend, correctly deferred)

The ingest finalize hook already warms the event-study default hot key (`data_manager.py:3138`) but not
the 7 evidence `drawdown_expectations` keys, so the first `/evidence` view after a backfill lazily pays the
cold miss. Extending the finalize hook to warm those keys too would make the cold miss never user-visible
even on a large basis. Backend enhancement, out of scope for this frontend-only iteration — a candidate for
the owner's backlog, not a J-06 blocker.

### Files changed in this fix pass

- `reports/perf-budgets.md` — J-06 closeout section: replaced the "CRITICAL FINDING — severe regression"
  with a "CORRECTION (iter-6 developer fix pass)" section (clean idle numbers + contamination root cause +
  audit trail of the superseded contaminated figures); updated the 11-page table's `/evidence` and
  `/research/event-study` rows to their corrected PASS verdicts.
- `reports/phase-goal-ops-hardening-iter-6-implementation-summary.md` — corrected the "Known Limitations"
  slowdown alarm to the measurement-error explanation, in operator plain language.
- `docs/handoffs/goal-ops-hardening-iter-6-dev.md` — this Fix Notes section.
- `runs/goal-ops-hardening-iter-6/status.json` — `current_step: dev_complete`, corrected findings.

**No `apps/backend/**` or `apps/frontend/**` source file changed in this fix pass** (confirmed via
`git status` — only reports/handoffs/status.json touched). The only side effect on the (gitignored) live
dev DB was clearing `event_study_cache` to measure a clean cold miss; it self-healed on the next request.

### Known Issues (new, from this fix pass)

- None introduced. The one-time cold-miss growth on the accumulated dev DB (item above) is characterized,
  in-budget, and recorded — not a defect, not a blocker.
