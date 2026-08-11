# Goal Iteration 61 — Fix the stale `/data` coverage counts and honestly re-close J-05/J-07's remaining gaps

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 61
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — prior verdict was ESCALATE (iter-60); full depth is mandatory, no exceptions.
- **Frontend Present:** yes
- **Target journeys:** J-05, J-07
- **Required-still-passing journeys:** J-01, J-03, J-04, J-06, J-08, J-09 (full regression — widened per the
  post-ESCALATE rule; iter-60 was ESCALATE)
- **Anti-goal reminders:**
  - **AG-1:** A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a
    **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked
    values MUST render a "not yet proven" state. *(critical)*
  - **AG-2 — Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or
    alpha claims; never place or simulate orders. *(critical)*
  - **AG-3:** A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation
    for the same as-of date — not merely that the page renders. *(critical)*
  - **AG-4 — No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed
    out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **AG-5 — Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars >
    as-of; never introduce lookahead anywhere. *(critical)*
  - **AG-6:** No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from
    the post-decompose gate. *(critical)*
  - **AG-7:** No hard-coded credentials, API keys, or tokens in source files. *(critical)*
  - **AG-8 — Resilience to data-shape and data-scale change:** widening the data basis (new nulls, broader pools, deeper history) must never crash an existing page or exhaust a service's memory — every
    existing consumer of a widened field is re-validated, the UI degrades gracefully (contained error
    boundary, honest "—"/NA placeholder, never a blank application-error page), and unbounded
    whole-table ORM loads are forbidden on the deep basis. *(critical)*
  - **AG-9 — Offline-deterministic ingest:** ingest jobs (fetch/backfill/rebuild) run only
    against the committed seed / local provider fixtures — no live external network calls or
    paid data services may be introduced without an explicit goal.md amendment. *(critical)*
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

Fix the concrete, evaluator-found defect keeping J-05 open — `/data` displaying a stale snapshot-date/gap
pair for tens of minutes after a real ingest wrote the correct counts — and honestly re-measure/re-write J-07's
one remaining open step (health responsiveness during a real 18-23 minute heavy ingest), so both journeys
carry current, mechanically-reconciled evidence instead of prose claims.

## BACKGROUND

iter-60 (ESCALATE) independently re-derived every load-bearing fact from source/sqlite/logs rather than
trusting any lane's write-up, and found: (a) `coverage_snapshot` id=1 held the CORRECT `snapshot_count=2954`
/ `gap_count=2442` at 06:58:55 (inside the ingest finalize tail), while `/data` screenshots captured 48
minutes later in the SAME never-restarted process displayed the exact PRE-backfill pair, 2953/2443 — the
served/rendered path did not re-serve the persisted payload (iter-60/a, scored `minor`, and the concrete,
independently-evidenced reason J-05 stays `partial`, per `assumptions.md` iter-60 (2 of 2)); (b) the
developer's own top-priority fix (routing `TARGET_JOURNEYS` goldens into the deterministic replay set) could
not self-verify because `goal-iter-lean.sh:45` sources `lib/replay-lane.sh` at executor start, before the
edit landed — this iteration's own fresh executor start sources the ALREADY-fixed library, so this is a
verification task, not a code task; (c) the new "Unavailable" degrade indicator (`sample-link.tsx`) shipped
with zero visual evidence; (d) the J-07 step-2 health-poll write-up reported a bare success count with no raw
file or timings, regressing the measurement discipline iter-59 had just won (raw CSVs, mechanically
reconciled). iter-60's own next-step recommendation orders these five items 1-5, and this spec follows that
order verbatim (binding ESCALATE recommendation).

**Lessons applied (recurring in this exact area):** (1) iter-57/iter-58's lesson — a "zero failures" health
drill claim is worthless without a raw log reconciled by line count against the process's own
`OPEN`/`CLOSED` job-window markers; hand-picked segment boundaries are where failures disappear (this
iteration's TC-5 exists specifically to not repeat that). (2) iter-58's lesson — hashing/distinctness of
screenshot files does not prove they show anything; the "Unavailable" capture must be opened and checked for
the actual indicator, not merely produced. (3) iter-60's own lesson — a shell-library fix cannot verify
itself in the run that edits it; this iteration's replay lane runs against the library as it stood BEFORE
this dispatch (already fixed at iter-60), so it CAN self-verify this time, and the check must read the live
engine log, not assume the fix "should" work.

The `J-07` owner decision (does the ≤2s `/api/health` ceiling apply to an 18-23 minute job, or only the
~30s window it was written for) is explicitly NOT resolved by this spec — it is an owner-only call flagged
for 11 consecutive rounds. This iteration ships the agent-actionable parts of J-07 (an honest, reconciled
step-2 write-up) and restates the owner question verbatim in NOTES; J-07's final pass/fail is the
evaluator's call once that answer exists.

## IN SCOPE

### Backend
- [ ] Diagnose and fix the `/data` coverage staleness defect: after a real ingest's finalize hook persists
      a fresh `coverage_snapshot` row (`app.engine.data_manager.compute_coverage` /
      `_upsert_coverage_snapshot`), the SAME never-restarted process must serve that row's exact
      `snapshot_count`/`gap_count` (via `coverage_from_storage`, `GET /api/data`) to every subsequent
      request for the same resolved as-of — including after an intervening `_membership_dataset_version`
      stamp bump from an unrelated request-path event, where the iter-27 stale-row fallback
      (`coverage_from_storage`'s `asof_key`-only lookup) must return the MOST RECENT row for that
      `asof_key`, never a superseded one. Root-cause first (the defect may sit in the backend's
      dataset-version/stale-fallback resolution, or in the frontend's post-job-completion refetch — see
      Frontend below); fix at the actual source, not both speculatively.
- [ ] Regression test pinning the fix: a fixture that ingests, bumps the stamp again via an unrelated
      request-path `ScannerRun` creation, and asserts the served payload's `snapshot_count`/`gap_count`
      still equal the freshest persisted row, not an older one.

### Frontend (if applicable)
- [ ] If diagnosis attributes the staleness to the client (e.g. `/data`'s post-job-completion or
      periodic-refresh path in `apps/frontend/app/data/page.tsx` not re-fetching or discarding a fresher
      response), fix the refetch/render path there instead of duplicating the backend fix.
- [ ] Capture one evidence screenshot of the new "Unavailable" sample-link indicator
      (`components/sample-link.tsx`, `data-testid="sample-link-unavailable"`) on the Regime Lab, taken with
      the backend launched under `TRENDORA_FAULT_INJECT_MEMORY_ERROR=regime_lab` armed (dev arms via a
      throwaway/relaunched process; browser-qa shoots), then the backend is restored to its normal
      unarmed launch for the rest of the iteration's work.

### New user-facing capability
None — this iteration repairs an already-shipped display path (`/data`'s coverage counts) and produces
missing evidence for already-shipped code (the "Unavailable" indicator); no new capability.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None — same `/data` page, same Regime Lab page; only the served/rendered values become current.

### Product surface delta
No visible change to a healthy user under normal conditions; a user who runs a backfill and stays on `/data`
now sees the counts update to match the just-finished job instead of a stale pre-job pair persisting for
tens of minutes.

### Blueprint conformance
Data Manager (`/data`) home, Coverage payload row — same computing module (`app.engine.data_manager`), same
serving endpoint (`GET /api/data`), per `blueprint.md`'s Information Architecture + Data Contract. No new
page, no nav change. Research home (`/research/regime-lab`), Membership timeline / research hot-key row —
same module/endpoint, evidence-only addition.

### Data-contract additions
None — this iteration re-derives/repairs two ALREADY-registered Data Contract values (Coverage payload;
Membership timeline / research hot-key caches' degrade-state fields) at their existing computing
module/serving endpoint. It introduces no new field, no second producer, no second endpoint.

## OUT OF SCOPE

- Resolving the J-07 owner question (≤2s ceiling scope for an 18-23 minute job) — owner-only, restated in
  NOTES, not decided by this spec.
- The long-carried backlog items (iter-29/b, iter-31/e, iter-32/f, iter-35/k, iter-36/n, iter-37/o, iter-37/q,
  iter-39/u, iter-46/az, iter-46/ba, iter-47/bd, iter-47/bf, iter-47/bi, iter-48/bj, iter-57/f, iter-57/l,
  iter-59/g, iter-59/h, iter-59/k) and the Regime Lab UI/feature backlog (iter-33/g) — untouched again this
  round, per this session's established rule 5 (one risky change per iteration).
- Moving heavy Regime Lab compute into its own process — per iter-60's own reasoning, this is no longer
  needed (peak memory now runs at 71% of the raised cap with zero errors overnight).
- Re-measuring J-07 step 3 (VmPeak margin) or J-05 step 3 (cold-restart coverage) — both stand on prior
  live evidence per the binding "Do not redo" list; this diff does not touch boot, coverage-serving-on-cold,
  or warm-seam code in a way that invalidates either.
- Any new page, nav entry, or Data Contract value.

## DEFINITION OF DONE

- [ ] Target journey J-05 passes via browser-qa-agent: the stale-coverage defect is fixed, and the rendered
      Snapshot Dates / Backfill Gaps match `coverage_snapshot`'s persisted `snapshot_count`/`gap_count` for
      the resolved as-of, verified against sqlite in the same evidence pass.
- [ ] J-07 step 2 (health responsiveness during a real heavy ingest) is re-measured and written up from a
      raw poll log, reconciled by `wc -l` against the process's own `OPEN`/`CLOSED` job-window markers, with
      every non-200 (if any) and the slowest latency named explicitly — no unreconciled "N polls, zero
      failures" prose claim.
- [ ] The "Unavailable" sample-link indicator (`sample-link.tsx`) is captured in at least one opened,
      inspected evidence screenshot under an armed fault.
- [ ] The engine's own replay-lane log for this iteration lists J-05 and J-07 among the journeys replayed by
      the deterministic lane (confirms iter-60's routing fix took effect in a live run).
- [ ] Required-still-passing journeys (J-01, J-03, J-04, J-06, J-08, J-09) remain green via full-regression
      deterministic replay + LLM fallback.
- [ ] Walkthrough recorded for J-05 and J-07 via `demo.sh ops-hardening --session-live` (full-depth demo
      lane), covering both journeys' `[NEW]`-flagged walkthrough acceptance clauses.
- [ ] No anti-goal violation introduced (AG-3 and AG-8 apply directly to this iteration's surface).
- [ ] Unit tests pass; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-61-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-05 (all 4 steps; steps 1/2/4 re-verified live, step 3 stands on iteration-59 evidence per
  binding Do-Not-Redo), J-07 (step 2 freshly re-measured; steps 1/3/4 stand on prior binding evidence).
  Full regression over J-01, J-03, J-04, J-06, J-08, J-09.
- Unit/integration: a fixture-backed regression test for the coverage-staleness fix (see IN SCOPE); the
  existing coverage/dataset-version test suite must still pass with no weakened assertion.
- Error cases: an unrelated request-path `ScannerRun` creation that bumps `_membership_dataset_version`
  between the ingest finalize write and the next `/data` read must never cause a superseded/older
  `coverage_snapshot` row to be served in place of the freshest one for that `asof_key`.

Test-first contract:

- TC-1: given a real ingest finishes and its finalize hook persists a `coverage_snapshot` row with
  `snapshot_count=N`/`gap_count=M` for the resolved as-of, when `/data` is loaded (fresh mount) any time
  after in the same never-restarted process, then the rendered "Snapshot Dates" and "Backfill Gaps" values
  equal N and M exactly, as queried directly from sqlite in the same evidence pass.
- TC-2: given the same never-restarted process, when an unrelated request-path event (e.g. a historical
  `/backtest` view) creates a new `ScannerRun` row and bumps `_membership_dataset_version` after the fresh
  `coverage_snapshot` was written, then a subsequent `/data` load still serves that SAME freshest row's
  `snapshot_count`/`gap_count` (via the iter-27 stale-row fallback returning the most-recent row for the
  `asof_key`), never an older superseded payload.
- TC-3: given this iteration's executor starts fresh (sourcing the already-fixed `replay-lane.sh`), when the
  deterministic replay lane runs, then the engine log's "Regression (deterministic replay):" line includes
  both J-05 and J-07 among the replayed journeys.
- TC-4: given the backend is relaunched with `TRENDORA_FAULT_INJECT_MEMORY_ERROR=regime_lab` armed, when the
  Regime Lab page is loaded for a degraded cohort, then the captured, opened screenshot shows the
  `data-testid="sample-link-unavailable"` element (AlertTriangle + "Unavailable" text) with no active
  drill-down link, for a cohort holding a nonzero real observation count in the database.
- TC-5: given a real ingest job runs for its full 18-23 minute duration, when `GET /api/health` is polled
  once per second throughout, then the raw poll log's line count reconciles exactly against the sum of every
  reported segment, the window is bounded by the process's own `heavy-warm window OPEN`/`CLOSED` markers,
  every non-200 response (if any) is listed individually, and the single slowest answered latency is named
  with its timestamp.
- TC-6: given J-05 and J-07's product-side steps are all satisfied per this iteration's evidence, when
  `demo.sh ops-hardening --session-live` runs at full depth, then a walkthrough recording exists on disk
  covering both journeys' `[NEW]`-flagged acceptance clauses.
- TC-7: given the full regression replay runs, when J-01/J-03/J-04/J-06/J-08/J-09 goldens are replayed, then
  all six report PASS with no selector-drift failure.

## NOTES

- **OWNER — restated verbatim (11th round unanswered):** the app must answer its health check within 2
  seconds while a background job runs; that promise was written for a job of about 30 seconds and our jobs
  last 18 to 23 minutes. Please say which you want — keep the 2-second promise for long jobs (J-07 stays
  open until the app is faster), or apply it to short jobs only (J-07's last gap closes). This spec does not
  choose for you; it only re-measures and honestly writes up the current numbers so the answer is not
  blocked on missing evidence.
- Root-cause the coverage-staleness bug before fixing it — do not patch both backend and frontend
  speculatively; the diagnosis determines which surface actually holds the defect (see IN SCOPE).
- Reuse `runs/goal-ops-hardening-iter-59/evidence-drill/reconcile_drill.py`'s reconciliation pattern for the
  TC-5 health drill rather than writing a new one.
- Review and QA lanes: this session has repeated the same two write-up defects across rounds 57-60
  (a "no blockers"/"complete"/"N passed" headline written over a status file or unmet item that says
  otherwise) — re-derive each claim from its own raw artifact before writing it, per the iter-57/iter-58/
  iter-60 lessons.
- Do not attempt any of the OUT OF SCOPE items above even if time remains — carry them forward per rule 5
  (one risky change per iteration).
