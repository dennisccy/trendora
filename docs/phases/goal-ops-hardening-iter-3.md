# Goal Iteration 3 — Close the fetch/expand coverage-freshness gap (audit B1/B2) and measure J-05's heavy-job health/memory ceiling

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 3
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-05
- **Required-still-passing journeys:** J-01, J-03, J-04
- **Anti-goal reminders:**
  - **AG-1:** A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked values MUST render a "not yet proven" state. *(critical)*
  - **AG-2 — Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha claims; never place or simulate orders. *(critical)*
  - **AG-3:** A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation for the same as-of date — not merely that the page renders. *(critical)*
  - **AG-4 — No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **AG-5 — Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of; never introduce lookahead anywhere. *(critical)*
  - **AG-6:** No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the post-decompose gate. *(critical)*
  - **AG-7:** No hard-coded credentials, API keys, or tokens in source files. *(critical)*
  - **AG-8 — Resilience to data-shape and data-scale change:** widening the data basis (new nulls, broader pools, deeper history) must never crash an existing page or exhaust a service's memory — every existing consumer of a widened field is re-validated, the UI degrades gracefully (contained error boundary, honest "—"/NA placeholder, never a blank application-error page), and unbounded whole-table ORM loads are forbidden on the deep basis. *(critical)*
  - **AG-9 — Offline-deterministic ingest:** ingest jobs (fetch/backfill/rebuild) run only against the committed seed / local provider fixtures — no live external network calls or paid data services may be introduced without an explicit goal.md amendment. *(critical)*

## GOAL

Every ingest kind that actually changes the bars/membership manifest — including `fetch`/`expand`,
not just `backfill`/`rebuild` — keeps the persisted coverage payload fresh, so the default `/data`
view never again silently shows a false all-zero coverage count for a fully-ingested database; and
J-05's one remaining unmeasured acceptance step (backend health and memory stay within budget
during a real heavy ingest job) is measured live and recorded.

## BACKGROUND

The iter-2 evaluator (`runs/goal-session-ops-hardening/iter-2/eval.md`) scored J-05 `partial` —
its own step-4 live measurement (`/api/health` responsiveness + `VmPeak` ceiling DURING a heavy
job) is the one gap keeping it from `passing`. The SAME iteration's audit
(`docs/handoffs/goal-ops-hardening-iter-2-audit.md`) independently found **B1**: a `fetch`/`expand`
that changes the bars manifest does not refresh `coverage_snapshot`, so `GET /api/data`'s default
view silently serves the honest-*looking* but FALSE all-zero "not yet computed" sentinel for a
fully-ingested DB until an unrelated restart or backfill/rebuild happens to refresh it — reproduced
live by browser-qa (UT-07), explicitly named the evaluator's **#1 next-step and declared blocker to
any future GOAL_ACHIEVED** (`iteration-state.md`'s Active Blockers). The audit's **B2** (stale
`coverage_snapshot` rows under a superseded `dataset_version` are never reclaimed) is a small,
mechanically-related cleanup the same eval asked to fold in.

Per the priority rubric, this iteration targets **J-05 alone**: closing B1/B2 finishes J-05's own
"Consistency" ("no request path recomputes it") and "Correctness" ("byte-identical to the canonical
computation") acceptance bullets for the general case (today they hold only for
`backfill`/`both`/`rebuild`, not for `fetch`/`expand`), and the step-4 live measurement is J-05's
one remaining explicit acceptance gap — this is rule 3 (unblocker: B1 is this session's own declared
top blocker to GOAL_ACHIEVED) and rule 4 (smallest spec wins ties) at once. **Deviation from the
eval's own suggested bundling, stated per the self-check:** the iter-2 eval's next-step recommendation
listed B1, the step-4 measurement, AND the J-06 capstone together as one iteration's priority order;
this spec deliberately defers J-06 to the next iteration instead of bundling it here. Reason (rule 5,
never bundle two risky journeys): the B1 fix reopens the exact cross-ingest-kind gating surface in
`_run_job`/`_refresh_ingest_aggregates` that produced an undetected regression once already this
session (a change built and reviewed against backfill/rebuild-only journeys silently mis-behaved on
the fetch path — caught only by the audit's independent code-trace, not by review or QA). That is
this iteration's one risky change. J-06's own acceptance requires "a code-level audit that no
on-load endpoint performs an unbounded scan" across seven pages this session has not yet inspected
(`/`, `/sectors`, `/themes`, `/scanner-runs`, `/backtest`, `/watchlist`, a `/research` lab) — that
audit could surface an unrelated finding needing its own fix, which would be undiagnosable if mixed
with the B1 change in one diff. J-06 remains queued as the immediate next iteration once J-05 is
`passing`.

**Depth is full**: **trigger 1 (structural/cross-cutting)** — the fix touches the ingest-kind gate
shared across `fetch`/`expand`/`backfill`/`both`/`rebuild` in `_run_job`/`_refresh_ingest_aggregates`/
`_upsert_coverage_snapshot` (`app.engine.data_manager`), exactly the kind of cross-path interaction
whose failure mode already crossed agent boundaries once this session (built + reviewed by
developer/reviewer, missed by QA, caught only by the audit's independent code-trace) — the full
pipeline's audit step is the lane that caught this the first time and should re-verify the fix.
This also hardens the blueprint's Coverage payload Data-Contract row in the trigger-2 sense: the
value's canonical write-path *trigger conditions* change (not its computing module or endpoint,
which stay the same), and the coherence-auditor is specifically watching this row for drift.

**Lesson applied** (`lessons.md`, iter-2): "Keying a served ingest-time cache on a LIVE dataset
fingerprint... means ANY count-changing ingest silently invalidates every cached row... EVERY
count-changing ingest path (fetch/expand/remove-data too) must refresh it or the sentinel must do a
cheap real existence check; verify the fetch-then-view path, not just backfill-then-view. The
offline 'fetch is always zero-work' assumption also proved false." This iteration is exactly that
fix — do not re-assume fetch is always zero-work; the committed fixture has landed a real bar
before (iter-2 UT-07). The iter-1 lesson (a new persisted/served field's honesty risk lives in its
not-yet-computed/interrupted edge, not its happy path) is also kept in mind while touching this
same finalize-hook machinery, though this iteration adds no new field.

## IN SCOPE

### Backend
- [ ] Widen the ingest finalize trigger (`app.engine.data_manager`: `_run_job`'s completion gate +
      `_refresh_ingest_aggregates`) so a successful `fetch`/`expand` job also refreshes the
      current-stamp `coverage_snapshot` row, via the existing `refresh_coverage_snapshot` — no
      second derivation — gated to skip (zero extra compute, zero extra write) when
      `_membership_dataset_version` is unchanged from what the current-stamp row already reflects.
      Closes audit finding B1.
- [ ] Reclaim stale `coverage_snapshot` rows left under a superseded `dataset_version` (today's
      `_upsert_coverage_snapshot` only prunes a stale row for the SAME `asof_key` being written) —
      one bounded SQL delete keyed on `dataset_version != current`, not a per-row Python scan.
      Closes audit finding B2.
- [ ] No change to: the `as_of=None` default-path self-heal gate, the cold-boot no-whole-table
      guarantee (iter-2's TC-6/TC-9), `aggregates_refreshed`'s existing nullability contract
      (stays `null` for `fetch`/`expand` — see Data-contract additions), or any J-01/J-03 shipped
      field.

### Frontend
- [ ] None — no frontend file changes. The existing `/data` coverage panel (built iter-2) already
      renders whatever `GET /api/data` serves; this iteration makes that served data honest after a
      `fetch`/`expand`, with no template/component change. `Frontend Present: yes` is set because
      the fix's correctness is user-visible on an existing page and must be confirmed live via
      browser-qa (see DEFINITION OF DONE) — not because any frontend file changes.

### Live measurement (J-05 step 4 — no code change, a QA/verification task)
- [ ] Dispatch one real heavy `rebuild` (or a large multi-day `backfill`) against a
      `scripts/start-backend.sh`-launched process (the now-enforced 6144 MB `ulimit -v` cap live),
      poll `GET /api/health` at ≤250ms intervals for the job's full duration, and sample
      `/proc/<pid>/status` `VmPeak`/`VmSize` alongside it.
- [ ] Record both results as a new dated section in `reports/perf-budgets.md`, continuing the
      file's existing lettered-item convention (alongside Items J/K).

### New user-facing capability
None new — this iteration fixes a correctness bug in an existing capability (J-05's ingest-time
coverage maintenance, shipped iter-2): the `/data` coverage panel now stays accurate after ANY
ingest kind that changes the data, including a `fetch`/`expand`, not only `backfill`/`rebuild`.

### New information displayed
None — no new field or panel. The existing coverage numbers on `/data` (universe/symbols/
trading-days/snapshot-dates) simply stop going stale/false-zero after a `fetch`/`expand`.

### New user actions
None.

### UI surface changes
None — same `/data` page, same coverage panel, same job form; only the backend's freshness
guarantee widens to cover more ingest kinds.

### Product surface delta
After a `fetch` or `expand` job that actually changes the bars manifest, `/data`'s default coverage
view reflects the change immediately (served from storage, not a live recompute) instead of
silently falling back to an honest-looking but false all-zero state until an unrelated restart or
backfill/rebuild.

### Blueprint conformance
`/data` (Data Manager nav section) — the existing canonical home for J-05 per `blueprint.md`'s
Information Architecture. No new page, panel, or nav entry; no nav-skeleton change (no
`blueprint.reapproval-requested` file written).

### Data-contract additions
None. This iteration introduces no new displayed value. It fixes WHEN the already-registered
"Coverage payload" value (`app.engine.data_manager` → `GET /api/data`) gets refreshed (widening the
set of ingest kinds that trigger its existing canonical computing module) and reclaims stale rows
of the same already-registered `coverage_snapshot` table — no second computing module, no second
serving endpoint. `blueprint.md` is updated to match (the Coverage payload row keeps its `[TARGET]`
tag, retagged `iter-3 building`, describing exactly this fix; three other rows' now-stale
`[TARGET, iter-2 building]` tags are removed as evaluator-confirmed built and unaffected by this
fix).

## OUT OF SCOPE

- J-06 (the measurement capstone) — deferred to the next iteration; see BACKGROUND's stated
  deviation from the eval's suggested bundling (rule 5: this iteration carries one risky change).
- Widening `aggregates_refreshed`'s nullability so a `fetch`/`expand` run also reports `"coverage"`
  refreshed — the field's existing `backfill`/`both`/`rebuild`-only contract (registered in
  `blueprint.md`) is unchanged; the fix is silent from that field's transparency perspective.
- Retiring `ensure_latest_snapshot`'s boot branch or the boot warm-up loop's cadence bootstrap —
  unchanged from iter-2's own out-of-scope reasoning (still dormant/unverifiable against the
  offline seed; still risks regressing archived mcp-loop-era guarantees).
- Extending the explicit-`as_of` historical self-heal (`coverage_from_storage`, gated
  `as_of is not None`) to the default path — do NOT touch; it must stay off the default path per
  iter-2's own fix rationale (re-introducing it there reopens the cold-boot whole-table CRITICAL
  J-05 exists to remove).
- Any change to J-01/J-03's shipped `dates_total`/breakdown/`chunk_index` fields, or J-04's shipped
  `ulimit`/`MALLOC_ARENA_MAX`/logfile mechanics — "Do not redo" per `iteration-state.md`.
- Wiring `limit_concurrency`/`timeout_keep_alive_seconds`/`graceful_timeout_seconds` into
  `scripts/start-backend.sh` — still not named by goal.md's binding note; deferred again unless
  this iteration's own health measurement reveals it is actually needed.
- Editing `docs/goal.md` — lint-final (commit `9c98cb3`); not touched.

## DEFINITION OF DONE

- [ ] Target journey J-05 passes via browser-qa-agent — all 4 acceptance steps, including the
      step-4 live health/memory measurement
- [ ] The fetch/expand coverage-freshness gap (audit B1) is closed and evidenced live: a
      fetch/expand that changes the bars manifest refreshes `coverage_snapshot`; a zero-work
      fetch/expand pays no extra compute
- [ ] The stale-stamp prune (audit B2) is implemented and tested
- [ ] Required-still-passing journeys J-01, J-03, J-04 remain green (deterministic replay + LLM
      fallback — mechanically verified at both depths)
- [ ] No anti-goal violation introduced (AG-3 byte-identity, AG-8 no unbounded request-path compute
      on the default path, AG-9 no network call introduced)
- [ ] Unit tests pass; no regressions
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-3-dev.md`, documenting the
      heavy-job measurement numbers and the B1/B2 fix

## TESTING REQUIREMENTS

- Browser: J-05 (target — the literal B1 regression now fixed, TC-11; the step-4 live measurement,
  TC-8/TC-9); J-01, J-03, J-04 (required-still-passing regression, deterministic replay with LLM
  fallback)
- Unit/integration: extend `test_data_manager.py` for the widened finalize gate (fetch/expand
  trigger + dataset-version-unchanged skip + stale-row prune); a no-network assertion for the
  widened trigger path; a byte-identity assertion for a fetch-triggered coverage refresh
- Error cases: a fetch/expand whose bars manifest is genuinely unchanged (the common offline case)
  must not write a `coverage_snapshot` row or invoke the whole-table compute; a fetch/expand that
  fails partway must not leave a partially-written/inconsistent row

Test-first contract:

- TC-1: given a committed DB with a current-stamp `coverage_snapshot` row already persisted, when a
  `fetch` job lands at least one new bar (changing `_membership_dataset_version`) and completes
  successfully, then the finalize hook persists a fresh `coverage_snapshot` row for the current
  stamp (`computed_at` updated) and `GET /api/data`'s default (`as_of=None`) coverage block's
  `symbol_count`/`snapshot_count` match a fresh independent `_compute_coverage_uncached` call for
  the same stamp, not the pre-fetch persisted values.
- TC-2: given the same setup as TC-1 but the fetch lands zero new bars (the common offline no-op),
  when the fetch completes, then `_compute_coverage_uncached` is never invoked (a call-count
  assertion) and no new `coverage_snapshot` row is written or re-timestamped.
- TC-3: given an `expand` job whose bars manifest changes (a new passer's history is added), when it
  completes, then the same fetch-path finalize behavior applies — a fresh `coverage_snapshot` row is
  persisted for the current stamp, byte-identical to a direct fresh `_compute_coverage_uncached`
  call for that stamp.
- TC-4: given multiple `coverage_snapshot` rows exist under a now-superseded `dataset_version` (for
  different `asof_key`s), when the finalize hook next detects the dataset version has changed, then
  every row whose `dataset_version` differs from the new current value is deleted, leaving only
  current-stamp rows, via one bounded SQL delete (not a per-row Python scan).
- TC-5: given the backend has just booted with zero ingest yet this session, when `GET /api/data` is
  called with the default `as_of=None`, then it still returns HTTP 200 with the honest all-zero "not
  yet computed" sentinel and zero `daily_prices`-table queries beyond the committed-pool file read
  (iter-2's TC-6/TC-9 remain unregressed).
- TC-6: given a fetch/expand-triggered `coverage_snapshot` refresh (TC-1/TC-3), when its
  `payload_json` is compared field-by-field against an independent fresh call to
  `_compute_coverage_uncached` for the same resolved as-of, then every field is byte-identical.
- TC-7: given the widened finalize trigger executes for a fetch/expand kind, when outbound
  network/socket activity is monitored for that process during the finalize step, then zero
  external calls occur (AG-9).
- TC-8: given a real heavy `rebuild` (or large multi-day `backfill`) job is dispatched against a
  `scripts/start-backend.sh`-launched process, when `GET /api/health` is polled at ≤250ms intervals
  for the job's full duration, then every poll returns HTTP 200 within 1 second, with zero timeouts
  or non-200 responses.
- TC-9: given the same heavy job as TC-8, when peak `VmPeak`/`VmSize` is sampled from
  `/proc/<pid>/status` across the job's duration, then it stays under the 6144 MB `ulimit -v` cap,
  recorded with its margin in `reports/perf-budgets.md`.
- TC-10: given the existing J-01/J-03/J-04 test suites (breakdown/chunking/boot/readiness/logfile),
  when they run after this iteration's finalize-gate widening, then every previously-passing
  assertion still passes unedited.
- TC-11: given a fetch that lands a new bar completes via `/data`'s job form, when the default
  `/data` page (no explicit `as_of`) is reloaded, then the coverage panel shows the real non-zero
  Universe/Symbols/Trading-days/Snapshot-dates counts, not the all-zero sentinel that was the
  literal B1 regression.
- TC-12: given the iteration completes, when `docs/handoffs/goal-ops-hardening-iter-3-dev.md` is
  read, then it documents the TC-8/TC-9 measured numbers and a concrete before/after description of
  the B1 fix.

## NOTES

- **Lesson applied:** iter-2's lesson on keying a served cache to a live dataset fingerprint (every
  count-changing ingest path must refresh it or the sentinel must do a cheap existence check) is
  this iteration's entire scope; do not assume "fetch is always offline zero-work" — the committed
  fixture has landed a real bar before (iter-2 UT-07), which is exactly how B1 was found.
- **Audit findings closed this iteration:** B1 (IMPORTANT, AG-3-dimension, declared top blocker to
  GOAL_ACHIEVED) and B2 (GAP, stale-row cleanup), both from
  `docs/handoffs/goal-ops-hardening-iter-2-audit.md`.
- **`blueprint.md` updated this iteration:** the Coverage payload row keeps a
  `[TARGET, iter-3 building]` tag (describing exactly this fix) and now names the coherence
  auditor's flagged explicit-historical-`as_of` self-heal exception instead of an unqualified
  "never a live compute." The `aggregates_refreshed` field, the market-phase warm-trigger row, and
  the membership-timeline/research-hot-key row all have their `[TARGET, iter-2 building]` tags
  removed (evaluator-confirmed built in iter-2, unaffected by this iteration's fix).
- No blueprint nav-skeleton change — no `runs/goal-session-ops-hardening/state/
  blueprint.reapproval-requested` file written.
- Zero assumption-ledger entries this iteration: the scope here executes a specific, already-named
  audit finding (B1/B2) and evaluator recommendation rather than resolving a fresh ambiguity in
  `docs/goal.md`'s own text; deferring J-06 is a rubric-driven scoping call (explained above in
  BACKGROUND), not a goal-text interpretation.
- Once J-05 is scored `passing`, J-06 (the measurement capstone — the last remaining Must-have
  journey this session) is the natural next target per goal.md's suggested build order.
