# Goal Iteration 58 — Gate the availability "updating" banner on a real in-flight job, correct the TC-7 record

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 58
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — cross-cutting honesty fix spans `data_manager.py`'s `stale` computation, the
  `/api/data/availability` serving path, and `availability-heatmap.tsx`'s rendering/gating logic — the
  same three-layer span whose lean-depth shipment (no audit) produced iter-56's ESCALATE. The evaluator's
  own depth recommendation for this iteration is `full`, binding by default.
- **Frontend Present:** yes
- **Target journeys:** J-05, J-07
- **Required-still-passing journeys:** J-01, J-03, J-04, J-06, J-08, J-09 (full 6-journey regression —
  the touched Availability heatmap Data-Contract row is warmed by the SAME finalize-tail hook every
  passing journey's ingest/serving path shares)
- **Anti-goal reminders:**
  - **AG-3:** A journey passes ONLY if the **displayed numbers are correct** — they match the engine's
    computation for the same as-of date — not merely that the page renders. *(critical)*
  - **AG-8 — Resilience to data-shape and data-scale change:** widening the data basis (new nulls,
    broader pools, deeper history) must never crash an existing page or exhaust a service's memory —
    every existing consumer of a widened field is re-validated, the UI degrades gracefully (contained
    error boundary, honest "—"/NA placeholder, never a blank application-error page), and unbounded
    whole-table ORM loads are forbidden on the deep basis. *(critical)*
  - **AG-9 — Offline-deterministic ingest:** ingest jobs (fetch/backfill/rebuild) run only against the
    committed seed / local provider fixtures — no live external network calls or paid data services may
    be introduced without an explicit goal.md amendment. *(critical)*
  - **AG-10 — Host resource ceiling (hardware protection):** heavy compute — backfills,
    full-universe rebuilds, measurement passes, load drills, test-suite bursts — MUST be launched
    only via the project launch scripts (`scripts/dev.sh` / `scripts/start-backend.sh`), and those
    scripts MUST apply the host caps declared in `project-extensions/host-guard/host-guard.env`
    whenever that file is present (CPU-affinity mask, BLAS/OMP thread caps, `memory_cap_mb`,
    `malloc_arena_max`). Never remove, weaken, or bypass these caps: stripping a HOST-GUARD
    marked block from a launch script is a REGRESSION regardless of test outcomes. The ceilings
    are a physical constraint of the current host (two instant hardware resets under all-core
    vectorized ingest bursts: 2026-07-20 19:17, 2026-07-21 10:33), not a performance budget to
    optimize away. *(Owner amendment 2026-07-31, two corrections of record — nothing above is
    relaxed: `memory_cap_mb` / `malloc_arena_max` live in `config.yaml`, not in `host-guard.env`;
    and the 2026-07-20/21 resets were subsequently attributed to an uncorrected hardware
    data-fabric fault (`host-guard.env`, 2026-07-30), so the ceiling VALUES are an owner-set
    envelope — re-set by the dated entry in "Additional binding notes" below — while this
    paragraph's prohibition on agents removing, weakening, or bypassing caps is unchanged.)*
    *(critical)*

## GOAL

The `/data` page's availability heatmap stops claiming "— updating" when no ingest job is actually
running (and stops the one narrow path where it could still show the false "No availability yet" message
on a stale-but-persisted row), and this session's TC-7 health-responsiveness record is corrected and
re-measured with honest, log-anchored segmentation instead of a hand-picked window that silently dropped
a real failure.

## BACKGROUND

The iter-57 audit found two residual honesty gaps in the SAME availability-cache fix iter-57 shipped:
B2 — `availability_from_storage`'s `stale` field is pure stamp inequality with no reference to whether a
job is actually running, so ANY stamp bump (a request-path historical view creating a new `ScannerRun`,
the boot warm-up's own cadence snapshots, or a non-fatal-skipped finalize warm) leaves the page reading
"Data as of `<stamp>` — updating" indefinitely with nothing in flight — the mirror-image honesty failure
of the one iter-57 fixed. B5 — the frontend's empty-state gate (`cells.length === 0` alone) does not
account for a stale-but-empty row, a narrow but real precondition under which the false "No availability
yet" message could still render. The SAME audit's B1 finding is more serious: the iter-57 TC-7 drill
actually recorded **1,212** poll records, not the 1,211 the addendum/dev-handoff/`status.json` all
report — the dropped 1,212th record is a genuine ≥10-second `GET /api/health` non-answer inside the
ingest heavy-warm window, excluded only because the addendum's hand-picked sub-window ended one second
before it. The iter-57 evaluator's own next-step explicitly orders this iteration's work: correct the
health record first, then re-drill it bounded by the process's own job markers; stop the banner from
lying when no job runs; rotate J-05's exhausted golden date; fix the small carried `models.py` docstring
(B6). Per this session's own binding "profile before fix" lesson (iter-48/50/53) and rule 5 (one risky
product-code action per iteration), this iteration does NOT attempt a code fix for the deeper
memory-ceiling wedge/GIL-contention class the corrected TC-7 record evidences — that is a distinct,
not-yet-profiled diagnosis effort, logged as a deferral in `assumptions.md` (iter-58). Lesson applied:
iter-57's two entries on segment-boundary honesty ("Segment boundaries chosen by hand are where failures
go to disappear...") and on J-06's golden provoking a regime-lab compute in the background of whatever
runs next both bind this iteration's TC-7 re-drill methodology.

## IN SCOPE

### Backend
- [ ] `app/engine/data_manager.py` — `availability_from_storage`: compute `stale` as (the cached row's
      `dataset_version` differs from the current stamp) **AND** (an ingest job is actually in flight),
      reusing an EXISTING running-job signal this module already reads elsewhere (`data_provider_runs`
      rows with `status == "running"`, or the in-memory `_JOBS` registry the live job-poll endpoint
      already serves) — no new table, no second producer, no new field.
- [ ] `app/models.py` — correct `AvailabilityCache`'s docstring (~line 742-744), which still claims a
      stamp-mismatched row is "never hit"; iter-57 made serving that row the intended, tested behavior.
- [ ] `reports/perf-budgets.md` — append a dated correction addendum withdrawing Addendum 23's "1,211
      polls, ZERO non-200" claim: the true count is 1,212, with one `000`/10.002641s non-answer at
      2026-08-10T10:30:00Z inside the ingest heavy-warm window, and the addendum's own segment boundaries
      were mis-drawn (append-only correction — the original addendum stays, this is a new dated entry).
      Add the same correction as a short append to `docs/handoffs/goal-ops-hardening-iter-57-dev.md`'s
      Known Issues and to `runs/goal-ops-hardening-iter-57/status.json` (append a correction note; do not
      silently rewrite the original claim).
- [ ] Re-drill TC-7: a fresh 1Hz `GET /api/health` poll spanning a genuine ingest heavy-warm window,
      segmented using the process's own logged `ingest heavy-warm window OPEN: job=<id>` /
      `CLOSED: job=<id>` markers (`data_manager.py:4031`/`:4043`) rather than a hand-picked timestamp,
      with the reported poll tally reconciled against `wc -l` of the raw drill log. Record the result in
      a new dated `reports/perf-budgets.md` section.
- [ ] `runs/goal-session-ops-hardening/journey-scripts/J-05.json` — rotate the exhausted target date
      2010-11-10 (`scanner_runs.id=2946`) to 2010-11-11 (live-verified 0 `scanner_runs` rows at spec time)
      in steps 2/3/13/14 and the script's `name` field — test-fixture change only.

### Frontend
- [ ] `apps/frontend/components/availability-heatmap.tsx` — change the empty-state condition from
      `state.data.cells.length === 0` to `state.data.cells.length === 0 && !state.data.stale`, so a
      stale-but-empty persisted row can never render the "No availability yet — Fetch real EOD prices"
      message (B5).
- [ ] Same file — align the stale banner's copy with the sibling Coverage-panel stale banner's phrasing
      (`apps/frontend/app/data/page.tsx:759-764`, coherence-auditor's iter-57 advisory) — wording only, no
      behavior change.

### New user-facing capability
None — this is a correctness/honesty fix to an already-shipped surface, not a new capability.

### New information displayed
None — no new field; the existing `stale`/`served_dataset_version` values now match their own
already-registered definition.

### New user actions
None.

### UI surface changes
The `/data` page's availability heatmap no longer shows "— updating" when no ingest job is running, and
never shows the false "No availability yet" message on a stale-but-persisted row.

### Product surface delta
No new page, route, or nav entry. The existing `/data` Data Manager surface's honesty is tightened; no
other surface changes.

### Blueprint conformance
No Information Architecture change — the Availability heatmap stays on its existing `/data` home
(`blueprint.md` IA table, J-05/J-09 rows). Blueprint updated additively this iteration (a forward-looking
`iter-58 update` changelog paragraph naming this targeted work); no IA table row or nav-skeleton edit.

### Data-contract additions
None. This iteration corrects the EXISTING `stale: bool` / `served_dataset_version: Optional[str]`
fields' *computation* (`blueprint.md` Data Contract row "Availability heatmap") to match their own
already-registered definition ("an ingest is mid-flight and the finalize warm has not yet re-run") — same
field names/types, same computing module (`app.engine.data_manager.availability_from_storage`), same
endpoint (`GET /api/data/availability`). No new field, no second producer, no second endpoint.

## OUT OF SCOPE

- A code fix for the memory-ceiling wedge (post-`MemoryError`, `/api/health` reports "ready" while
  `/api/data`/`/api/runs`/`/api/data/availability`/`/api/stocks/{ticker}/bars` return 500) or for the
  ≥10s connection-level `/api/health` non-answer inside a heavy-warm window — a distinct, not-yet-profiled
  diagnosis effort; this iteration's re-drilled TC-7 evidence is the input the next attempt needs, not the
  fix itself (rule 5 — see `assumptions.md` iter-58). Owner decisions (a) off-process compute and (b) does
  the 20-minute finalize budget apply while serving traffic remain outstanding, asked 8 rounds running.
- `demo_runner`'s missing per-call resource-timing primitive (audit B3) — vendored framework tooling, not
  a product surface any developer agent operating on `apps/backend`/`apps/frontend` can address (binding
  iter-56 precedent).
- `docs/test-infra-tickets.md`'s TI-1/TI-2 (a chronically slow test file, a never-executed health
  byte-identity test) — ticketed, framework-adjacent, not this iteration's risky action.
- The Regime Lab's cold `view=pooled` dispatch (iter-33/g) and every other long-carried item in
  iteration-state.md's history — untouched, no new deferral count needed this round since none of them is
  this iteration's target.
- Any change to `server.memory_cap_mb`, `malloc_arena_max`, or any other AG-10 host-guard cap value.

## DEFINITION OF DONE

- [ ] `stale` is `true` only when the cached row's stamp mismatches AND a job is genuinely in flight;
      verified via TC-1/TC-2/TC-3.
- [ ] The frontend never renders "No availability yet" on a stale row (TC-4).
- [ ] `models.py`'s `AvailabilityCache` docstring matches the shipped behavior (TC-5).
- [ ] The TC-7 record correction lands in `reports/perf-budgets.md`, the iter-57 dev handoff, and
      `runs/goal-ops-hardening-iter-57/status.json` (TC-6).
- [ ] A fresh TC-7 drill, bounded by the process's own job-window log markers and reconciled against the
      raw log's line count, is recorded in a new dated `reports/perf-budgets.md` section (TC-7).
- [ ] `journey-scripts/J-05.json`'s target date is rotated and live-verified unsnapshotted before use
      (TC-8).
- [ ] Target journeys J-05, J-07 have fresh, correctly-segmented evidence (closure not required this
      round — see BACKGROUND/NOTES).
- [ ] Required-still-passing journeys J-01, J-03, J-04, J-06, J-08, J-09 remain green (deterministic
      replay + LLM fallback).
- [ ] No anti-goal violation introduced; AG-9 drill discipline (backfill only, never the live-fetch
      button) and the post-lane TC-16 watermark check (iter-57 process rules) are honored.
- [ ] Unit tests pass; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-58-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-05 (steps 1-4, live backfill of the rotated unsnapshotted date + the health-responsiveness
  poll), J-07 (steps 1-2, forward-aggregate warm + 1Hz health poll); required-still-passing replay for
  J-01, J-03, J-04, J-06, J-08, J-09.
- Unit/integration: `availability_from_storage`'s new job-aware `stale` gating (stamp-mismatch ×
  job-running cross product); the empty-state frontend gate; the corrected `AvailabilityCache` docstring
  is a documentation-only change (no test required for prose).
- Error cases: a stamp mismatch with a `data_provider_runs` row stuck at `status == "running"` from a
  crashed process (no live `_JOBS` entry) must not be misread as "no job running" if the chosen signal is
  DB-status-only — the developer states in the dev handoff which signal was used and why it does not
  false-negative on this case.

Test-first contract: every DEFINITION OF DONE checkbox and every Data-contract addition above maps to at
least one concrete scenario line, numbered sequentially:

- TC-1: given the `AvailabilityCache` row's `dataset_version` differs from the current
  `_membership_dataset_version` stamp AND no job is in flight (no `data_provider_runs` row / `_JOBS` entry
  has `status == "running"`), when `GET /api/data/availability` is called, then the response's `stale`
  field is `false`, `served_dataset_version` equals the row's own (prior) stamp, and `/data` renders the
  chart WITHOUT the "— updating" banner.
- TC-2: given the SAME stamp mismatch AND at least one job genuinely has `status == "running"`, when
  `GET /api/data/availability` is called, then `stale` is `true` and `/data` renders the
  `data-testid="availability-stale-notice"` banner — unchanged from iter-57's shipped behavior.
- TC-3: given `AvailabilityCache` holds no row at all (a never-warmed DB), when
  `GET /api/data/availability` is called, then `total_symbols`/`trading_day_count`/`cells` are
  `0`/`0`/`[]`, `stale` is `false`, `served_dataset_version` is `null`, and `/data` renders the "No
  availability yet — Fetch real EOD prices" empty state — unchanged.
- TC-4: given a persisted `AvailabilityCache` row whose stamp mismatches AND whose `cells` array is empty
  (constructed via a direct-write test fixture — the narrow B5 precondition), when `/data` renders the
  response, then the "No availability yet" empty state does NOT appear (gated on
  `cells.length === 0 && !stale`, not `cells.length === 0` alone).
- TC-5: given `apps/backend/app/models.py`'s `AvailabilityCache` docstring, when read, then it states that
  a stamp-mismatched row IS served (with `stale=true`), not that it is "never hit."
- TC-6: given `reports/perf-budgets.md` Addendum 23, the iter-57 dev handoff, and
  `runs/goal-ops-hardening-iter-57/status.json` all currently state "1,211 polls, ZERO non-200," when the
  correction lands, then all three carry an appended note recording the true count (1,212 records, one
  `000`/10.002641s non-answer at 2026-08-10T10:30:00Z) without deleting the original text.
- TC-7: given a fresh 1Hz `GET /api/health` poll run across a genuine ingest heavy-warm window, when the
  drill's own logged `ingest heavy-warm window OPEN`/`CLOSED` markers are used to bound the in-window
  segment (not a hand-picked timestamp), then the segment's reported poll count equals `wc -l` of the raw
  log for that bounded range exactly, and any non-200 or timed-out record inside the window is included
  in the reported tally.
- TC-8: given `journey-scripts/J-05.json`'s target date 2010-11-10 now has a `scanner_runs` row
  (`id=2946`), when steps 2/3/13/14 and the `name` field are rotated to 2010-11-11 (live-verified 0
  `scanner_runs` rows before the change), then a fresh replay of J-05 exercises a genuinely-unsnapshotted
  trading day again.

## NOTES

- This iteration deliberately does NOT close J-05 or J-07 — both stay `partial` most likely, since their
  remaining acceptance gaps (health responsiveness under real load, wedge-free memory-pressure abort) are
  the memory-ceiling class of defect this iteration explicitly defers (see OUT OF SCOPE and
  `assumptions.md` iter-58). The corrected, properly-bounded TC-7 drill this iteration produces is the
  evidence a future iteration's fix needs — not a placeholder for progress, a genuine prerequisite.
- Owner: the same two questions, asked 8 rounds running — (a) may a future round move heavy compute into
  a separate process, and (b) does the 20-minute finalize budget apply while the app is also serving
  traffic? Restated here per this session's own practice of not silently dropping outstanding owner asks.
- AG-9 drill discipline (adopted iter-57): any manual browser drill against `/data` during this iteration
  exercises ingest via **Backfill only** — never the "Fetch real EOD prices" button, which resolves the
  live import provider. TC-16-style live-fetch verification (if re-run) must watermark
  `max(data_provider_runs.id)` before the lane and re-query after, per the iter-57 lesson.
- `docs/test-infra-tickets.md` already carries TI-1/TI-2; no new ticket needed this iteration.
