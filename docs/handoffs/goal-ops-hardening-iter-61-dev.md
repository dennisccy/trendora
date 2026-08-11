# goal-ops-hardening-iter-61 Dev Handoff

**Phase:** goal-ops-hardening-iter-61
**Date:** 2026-08-11
**Agent:** developer
**Status:** complete

## What Was Built

- **Root-caused the `/data` coverage-staleness defect and found the backend already correct — the fix
  lands on the frontend.** Diagnosed first, per the spec's binding order. Read `coverage_from_storage`
  (`apps/backend/app/engine/data_manager.py`) line by line for the exact TC-1/TC-2 scenario (a fresh
  ingest persists a `coverage_snapshot` row, then an unrelated request-path `ScannerRun` creation bumps
  `_membership_dataset_version`), then PROVED it empirically rather than by inspection alone: wrote and
  ran a new regression test that drives the REAL finalize hook (`_refresh_ingest_aggregates`) and the
  REAL unrelated-event code path (`scanner.resolve_run`, not a hand-inserted row) through the actual
  API-layer function `app.api.data.data_overview` — it already serves the freshest row's exact
  `snapshot_count`/`gap_count`, never a superseded value (see "Tests Run"). A live sqlite check of the
  CURRENT production DB independently confirmed the same: `coverage_snapshot` never carries more than one
  row per `asof_key` at a time (`_upsert_coverage_snapshot`'s reclaim step deletes every non-current-stamp
  row on each write), so the iter-27 stale-row fallback's `ORDER BY computed_at DESC LIMIT 1` always finds
  the one real row for that key. **No backend code change was made** — the existing logic is correct for
  every scenario TC-1/TC-2 describe, and the new test pins that permanently.
  - Also checked, and ruled out, a decoy: `data_manager.compute_coverage`'s 8-key in-process cache (what
    iter-60's evaluator note actually named as "the serving path") is DEAD on the live request path — a
    `grep` for its call sites shows it is reached only by tests and `compute_coverage`'s own definition;
    `GET /api/data` has served exclusively from `coverage_from_storage` since iter-2 and never touches it.
  - Also checked `GET /api/health`'s `last_run_date` field, live: it is **hardcoded to `None`**
    (`apps/backend/app/api/health.py:126`) regardless of how many `ScannerRun` rows exist — confirmed via
    a real `curl` against the running backend with 2954+ scanner runs on file. This is a real, separate,
    pre-existing defect (the docstring above it says "null until a scanner run exists" — the code never
    honors that), but it is **out of scope for this iteration** (a different Data Contract value —
    readiness/boot — at a different endpoint than Coverage). Flagging it here rather than silently
    patching an unlisted file; it is why the frontend fix below reads the readiness poll's IDLE CADENCE
    rather than its `last_run_date`.
  - **The real, evidenced defect: the frontend never refetches coverage except in response to a job THIS
    tab itself started.** `/data`'s coverage/availability reload path (`apps/frontend/app/data/page.tsx`)
    fires on mount and when `jobId`/`jobStatus` (this tab's OWN tracked job) leaves `"running"` — nothing
    else. A backfill started elsewhere (another tab, a script, a teammate, or — as iter-60's evidence
    shows — a browser-qa pass that screenshots `/data` well after an earlier pass's own ingest finished)
    leaves an already-open or later-visited `/data` view rendering whatever it fetched before that
    ingest, indefinitely — this is the "served/rendered path did not re-serve the persisted payload"
    iter-60 observed, and it is a rendering-layer gap, not a backend one.
- **Fix: `/data` now runs an ambient, idle-cadence coverage refresh, independent of this tab's own job
  tracking.** `apps/frontend/components/readiness-provider.tsx`'s already-polling `useReadiness()` hook
  (mounted app-shell-wide, already fetches `GET /api/health` on a config-derived cadence for the top-bar
  badge) now ALSO exposes `pollIdleIntervalSeconds` — the SAME `poll_idle_interval_seconds` value
  (`config.yaml`, 30 s) it already reads for its own back-off, threaded through additively (mirrors
  exactly how `backgroundCompute` was added in iter-24 — no second fetch, no new backend field, no new
  config key). `/data`'s page now runs its own `setInterval` on that cadence, unconditionally, that
  reloads coverage + availability + the as-of run list (the SAME reload path the job-completion branch
  already uses) regardless of who or what triggered the underlying ingest. This closes the staleness
  window from "indefinitely, until the next manual reload" to "at most one idle-poll interval (30 s)" —
  matching the plan's own stated product delta: "a user who runs a backfill and stays on `/data` now sees
  the counts update... instead of a stale pre-job pair persisting for tens of minutes."
- **J-07 step 2 re-measured and reconciled from a raw poll log** (TC-5). Launched a real single-date
  `backfill` job (`2005-06-23`, a genuine gap trading day) through `scripts/dev.sh` (AG-10 caps intact,
  no bare `uvicorn`), polled `GET /api/health` once per second for the whole ~17-minute finalize tail via
  a dedicated poller process (`runs/goal-ops-hardening-iter-59/evidence-drill/poll_health.py`, reused
  verbatim), then reconciled with `.../reconcile_drill.py` (also reused verbatim, per the spec's explicit
  instruction not to write a new one). Result: window OPEN→CLOSED = 1015.37 s (16 m 55 s); **1078/1078
  polls answered, 100 % HTTP 200, zero non-answers**; exactly **1 poll** (2.849 s, at the very start of the
  finalize tail) breached the owner-amended ≤2 s relaxed ceiling. Full reconciliation:
  `runs/goal-ops-hardening-iter-61/evidence-drill/reconciliation.md`; dated section appended to
  `reports/perf-budgets.md` (Addendum 28, append-only per convention).
- **TC-4 evidence captured: the shipped "Unavailable" `sample-link.tsx` indicator, opened and visually
  confirmed, with a control arm proving the underlying cohort holds real, nonzero observations.** Relaunched
  the backend (only) with `TRENDORA_FAULT_INJECT_MEMORY_ERROR=regime_lab` armed via `scripts/start-backend.sh`
  (the frontend, already running via `scripts/dev.sh`, was left untouched and reconnected automatically),
  drove a real browser to `/research/regime-lab?asof=2010-11-05` in "As of date" mode, and read back the
  live DOM: 80 `[data-testid="sample-link-unavailable"]` elements (AlertTriangle + "Unavailable" text,
  `title="Temporarily unavailable — degraded under memory pressure"`), zero active `sample-link` chips.
  Restarted DISARMED for the SAME as-of: 0 unavailable indicators, 80 active `sample-link` chips carrying
  real `n=16452` (and similar) observation counts — confirmed both in the DOM and via a direct
  `GET /api/research/regime-lab` call. The closeup screenshot was opened and inspected (not just hashed):
  it shows a legible triangle icon followed by the word "Unavailable". Backend restored to normal unarmed
  state before continuing. Artifacts:
  `runs/goal-ops-hardening-iter-61/evidence-drill/TC-4-degrade-rendered*.png`,
  `TC-4-control-clean*.png`, `tc4-sample-link-unavailable.json`.
- **TC-3 (replay-lane routing) — verified the fix is live in the code this iteration's executor sources;
  the log-line confirmation itself materializes later in this iteration's own pipeline run.** Confirmed by
  direct read that `scripts/automation/lib/replay-lane.sh`'s `replay_lane_partition_and_verify` still
  contains iter-60's fix (the `REQUIRED_JOURNEYS` ∪ `TARGET_JOURNEYS` lint union + the target-only routing
  loop into `R_REPLAY`), and that `journey-scripts/J-05.json` / `J-07.json` both exist and were touched
  today (iter-60's own work) — the preconditions the fix needs to actually route them. The engine's own
  "Regression (deterministic replay):" log line for THIS iteration does not exist yet at dev-handoff time
  (the most recent line in `runs/goal-session-ops-hardening/engine.log` is from iter-60's own pass,
  `J-01 J-03 J-04 J-06 J-08 J-09` — no J-05/J-07, because that call's `TARGET_JOURNEYS` was different) —
  the replay lane runs later in this iteration's own pipeline (QA/regression phase), which is outside the
  developer step's own tools. Whoever runs that phase should re-grep `engine.log` for this iteration's own
  "Regression (deterministic replay):" line and confirm it lists both J-05 and J-07.

## Files Changed

- `apps/backend/tests/test_data_manager.py` -- new test
  `test_data_overview_serves_freshest_ingested_coverage_after_unrelated_dataset_version_bump` (TC-1/TC-2):
  real finalize-hook ingest + real unrelated-event `ScannerRun` creation (via `scanner.resolve_run`) +
  assertion against the actual `app.api.data.data_overview` function, not `coverage_from_storage` in
  isolation. New import: `from app.api.data import data_overview`. No existing test weakened.
- `apps/frontend/components/readiness-provider.tsx` -- additive `pollIdleIntervalSeconds: number | null`
  on `ReadinessContextValue`, populated from the already-fetched `GET /api/health`'s
  `poll_idle_interval_seconds` on each poll (mirrors the `backgroundCompute` precedent exactly); `null`
  before the first poll resolves / on a failed poll, matching every sibling field's honesty convention.
- `apps/frontend/app/data/page.tsx` -- new `useReadiness()` call + a `useEffect`/`setInterval` that
  reloads coverage + availability + the as-of run list on the shared idle cadence, independent of this
  tab's own job-tracking state. No other behavior changed.
- `reports/perf-budgets.md` -- append-only Addendum 28 (J-07 step 2 reconciled TC-5 measurement).
- `runs/goal-ops-hardening-iter-61/evidence-drill/` -- raw evidence: `tc5-health-poll.csv`,
  `reconciliation.md`, `dev.log` (this pass's own `scripts/dev.sh` redirect, used as the `reconcile_drill.py`
  backend-log argument since `dev.sh` does not write `logs/backend.log` — only `start-backend.sh` does),
  `capture_sample_link_unavailable.py` (new capture script, adapted from iter-59's
  `capture_degrade_ui.py` to target the CURRENT `data-testid="sample-link-unavailable"` element instead of
  the pre-iter-60 title-tooltip cell), `TC-4-*.png`, `tc4-sample-link-unavailable.json`,
  `tc4-control-only.json`, `data-page-sanity.png` (a quick post-fix live sanity screenshot of `/data`,
  showing the current, correct 2955 snapshot dates / 2441 backfill gaps figures after this pass's own two
  real backfills).
- `docs/handoffs/goal-ops-hardening-iter-61-dev.md` -- this file.
- `docs/handoffs/goal-ops-hardening-iter-61-frontend.md` -- frontend-focused handoff (same UI change).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/<file>.py -v` (TMPDIR set per the
coordinator's env note).

| Target | Result |
|---|---|
| `tests/test_data_manager.py` (full file, 217 tests) | **217 passed** (327s) — includes the new TC-1/TC-2 regression test and every pre-existing coverage/dataset-version test, no weakened assertion, no regression. |
| `tests/test_api_data.py` (full file, 53 tests) | **53 passed** (10s) — no regression. |
| `npx tsc --noEmit` (frontend) | Clean, zero errors. |
| All 13 `apps/frontend/lib/*.test.ts` files (via `npx tsx`, this project's documented Node-lacks-native-TS-stripping fallback) | **All pass** — no regression from the `readiness-provider.tsx`/`app/data/page.tsx` changes (neither has an extracted pure-logic file per this project's existing convention — the same shape as the pre-existing, untested job-polling `useEffect` block in the same component). |

### Live verification (real backend + frontend, `scripts/dev.sh`, ports 8255/3255)

- `GET /api/health` — confirms `poll_idle_interval_seconds: 30.0` served and `last_run_date: null` (the
  pre-existing, out-of-scope defect named above).
- A real backfill (`2005-06-23`, the TC-5 drill job) ran to completion (17 m), persisting a fresh
  `coverage_snapshot`; a fresh `/data` page load afterward rendered the CURRENT figures (2955 snapshot
  dates, 2441 backfill gaps — up from 2954/2442 before this pass's two real backfills), confirmed by an
  opened screenshot (`data-page-sanity.png`) and zero browser console errors.
- The TC-4 fault-injected/control screenshot pair (above) is itself a second live confirmation the whole
  stack (backend restart, frontend reconnect, readiness poll, page render) behaves correctly under this
  pass's changes.
- `scripts/dev.sh` started cleanly (backend + frontend both healthy), and was cleanly stopped at the end
  of this pass (`lsof`/`ss` confirmed both ports 8255/3255 fully released — no lingering `uvicorn`/
  `next dev`/`next-server` process).

## Pre-handoff verification

- [x] **Service startup works:** `scripts/dev.sh` launched backend (healthy, `readiness` warming then
  `ready`) + frontend (200) cleanly; stopped at the end via port-based `lsof`/`fuser` kill (mirrors
  `dev.sh`'s own cleanup convention) — confirmed no port conflict, no lingering process.
- [x] **External integrations:** N/A — no new adapter/scraper/external API this iteration; the TC-5
  backfill and TC-4 fault-injection both ran offline against the committed seed only (AG-9).
- [x] **Native dependency binaries:** N/A — no new dependency this iteration. (Playwright, used only for
  this pass's own evidence capture, is a pre-existing user-level install at `~/.local`, not a project
  dependency; the backend/frontend's own dependency sets are unchanged.)

## Known Issues

- **`GET /api/health`'s `last_run_date` is hardcoded to `None`** (`apps/backend/app/api/health.py:126`),
  contradicting its own docstring ("null until a scanner run exists"). Found while diagnosing this
  iteration's own defect; NOT fixed (a different Data Contract value/endpoint than this iteration's scope,
  and not named in the spec's IN SCOPE list). Recorded here per the "discover but don't fix" rule so the
  reviewer/auditor can triage it as a future backlog item.
- **TC-3's literal log-line confirmation is not yet observable** at dev-handoff time — the deterministic
  replay lane for THIS iteration has not run yet (it runs later in this iteration's own pipeline). The
  code-level precondition (the fix present in `replay-lane.sh`, both goldens on file) is verified; the
  actual "Regression (deterministic replay): ... J-05 ... J-07 ..." line needs to be re-checked once that
  phase runs.
- **The health-drill window measured 16 m 55 s**, not the 18-23 min range the spec/prior addenda describe
  for this shape of job — reported as measured, not padded. It is close to, but honestly under, that
  range; a reader who requires the full 18-23 min band before accepting the ≤2 s-ceiling reading should
  treat this as informative rather than conclusive on that narrow point.
- **The J-07 owner question is restated verbatim, not resolved, per the spec's explicit instruction:** the
  app promises to answer its health check within 2 seconds while a background job runs; that promise was
  written for a ~30 s job, and this pass's own real job ran 16 m 55 s (this session's jobs of this shape
  have run 8-23 min across recent passes). Please say which is wanted — keep the 2-second promise for long
  jobs (J-07 stays open until the app is faster), or apply it to short jobs only (J-07's last gap closes).
  This iteration does not choose for you; it only re-measures and reconciles the current numbers (one
  answered poll over the relaxed ceiling, zero non-answers, zero non-200) so the answer is not blocked on
  missing evidence.
- **The J-05/J-07 walkthrough recording (TC-6, `demo.sh ops-hardening --session-live`) was not run by this
  dev pass** — per this project's pipeline, the demo/showcase lane runs later (demo-narrator), not as part
  of the developer step.
