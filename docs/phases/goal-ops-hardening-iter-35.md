# Goal Iteration 35 — Bound the whole-table price prefill on J-07's warm path; wire honest loading into 4 sibling labs

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 35
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — the fix bounds `_membership_timeline`/`_compute_coverage_uncached`'s
  (`app.engine.data_manager`) shared whole-table `prefilled_bar_cache` load
  (`app.engine.prices`), reached simultaneously on J-07's ingest-finalize warm chain, J-05's
  aggregate-refresh path, and J-04's boot-warmup safety net — a genuinely cross-cutting,
  ≥3-module change (`prices.py`, `data_manager.py`, config) whose byte-identity / no-lookahead
  correctness is not covered by any single journey's own test suite.
- **Frontend Present:** yes
- **Target journeys:** J-07, J-06
- **Required-still-passing journeys:** J-01, J-03, J-04, J-05, J-08, J-09
- **Anti-goal reminders:**
  - **AG-3:** A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation
    for the same as-of date — not merely that the page renders. *(critical)*
  - **AG-5 — Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of;
    never introduce lookahead anywhere. *(critical)*
  - **AG-8 — Resilience to data-shape and data-scale change:** widening the data basis (new nulls, broader pools, deeper history) must never crash an existing page or exhaust a service's memory — every
    existing consumer of a widened field is re-validated, the UI degrades gracefully (contained error
    boundary, honest "—"/NA placeholder, never a blank application-error page), and unbounded
    whole-table ORM loads are forbidden on the deep basis. *(critical)*
  - **AG-10 — Host resource ceiling (hardware protection):** heavy compute — backfills,
    full-universe rebuilds, measurement passes, load drills, test-suite bursts — MUST be launched
    only via the project launch scripts (`scripts/dev.sh` / `scripts/start-backend.sh`), and those
    scripts MUST apply the host caps declared in `project-extensions/host-guard/host-guard.env`
    whenever that file is present (CPU-affinity mask, BLAS/OMP thread caps, `memory_cap_mb`,
    `malloc_arena_max`). Never remove, weaken, or bypass these caps: stripping a HOST-GUARD
    marked block from a launch script is a REGRESSION regardless of test outcomes. The ceilings
    are a physical constraint of the current host (two instant hardware resets under all-core
    vectorized ingest bursts: 2026-07-20 19:17, 2026-07-21 10:33), not a performance budget to
    optimize away. *(critical)*

## GOAL

Close the session's biggest remaining anti-goal finding — the whole-table `daily_prices` prefill
that runs on J-07's own ingest-finalize warm path — by bounding its memory footprint to the real
per-symbol/per-batch need instead of the full 30-year basis, and give the four sibling Research
labs the same honest computing/error/retry loading behavior Regime Lab already has.

## BACKGROUND

All 8 Must-have journeys are `passing` (iteration-state, after iter-34); the only work left is 8
open ledger findings blocking GOAL_ACHIEVED. The iter-34 evaluator ranked them explicitly and
named item 1 "the gap a fresh reviewer would find first": `apps/backend/app/engine/prices.py`'s
`_BarCache.prefill` issues an unfiltered `select` over the WHOLE `daily_prices` table and
accumulates every row into `by_symbol` in RAM (~1.5 GB at the live 590-symbol/30-year basis,
`data_manager.py:3025`'s own comment) — a direct, verbatim violation of `docs/goal.md`'s Success
Criterion "no code path streams the full `daily_prices` table into RAM," reached on J-07's own
warm path (`_refresh_ingest_aggregates` → `refresh_coverage_snapshot` → `_compute_coverage_uncached`,
`data_manager.py:814` → `prefilled_bar_cache`). This has been carried, untouched, as ledger finding
iter-29/d since iteration 29.

I read the call chain first-hand rather than carrying the description (`data_manager.py:780-897`,
`universe_resolver.py:119-198`, `prices.py:391-416`): `_compute_coverage_uncached` wraps its ENTIRE
body in `prefilled_bar_cache`, but only ONE of its five sub-calls actually needs the whole-table,
all-symbols-resident shape — `membership_timeline_cached`'s cache-MISS path
(`_membership_timeline`'s per-date resolver loop over ~1369 snapshot dates × the candidate pool,
`data_manager.py:497-544`), and `_refresh_ingest_aggregates`'s own comment
(`data_manager.py:3209-3211`) confirms this call IS the one that warms `membership_timeline_cache`
on every ingest finalize — so on J-07's exact warm scenario this is a genuine cache MISS, not
avoidable by scoping the wrap alone. `_resolved_universe`'s single as-of resolve
(`resolve_with_reasons`, `universe_resolver.py:158-168`) already falls back to a lightweight,
already-byte-identical SQL-side `GROUP BY` count when no cache is active; `_per_symbol_coverage`
(`data_manager.py:177-184`) and `_missing_data_diagnostic` (`data_manager.py:239-265`) already run
their own separate grouped/bounded queries and never touch `prefilled_bar_cache` at all. The real
fix has to bound `_membership_timeline`'s OWN loop — process the candidate pool in bounded batches
(each batch's full history resident only while active, never all ~590 symbols simultaneously)
instead of one all-symbols prefill — leaving `_BarCache`/`bars_asof`/`bars_after`/`trailing_count`
and every OTHER consumer across the engine (scoring/regime/sector, which this file's own docstring
says reads bars through this SAME accessor) untouched.

This session's own lessons apply directly and are binding: (iter-29) a shipped bound must be
proven against the REAL config value / real basis, never a fixture-sized knob, and a new chunk
dimension (symbols, here) must get its OWN config key rather than reusing `research.read_batch_size`
(a rows knob); (iter-30, second entry) name the exact frame the growth scales with and require the
plan to bound THAT, not a container next to it; (iter-31, second entry) ask "would the test fail if
the fix were reverted?" before accepting a bound as proven; (iter-32, first entry) a byte-identity
reference oracle must be pinned via `git show HEAD:<file>`, never an edited copy that also compiles
against the new code.

Per the priority rubric: rule 3 (unblockers) — this is the single item every recent evaluator has
put first, and it directly unblocks the achievement gate. Rule 5 (never bundle two risky changes) —
the evaluator's own #2 item, Regime Lab's cold `view=pooled` background dispatch + diagnosing an
undiagnosed HTTP 200/"Internal Server Error" body (iter-33/g), is a SEPARATE, real backend behavior
change with its own open failure mode; bundling it with this iteration's memory-bound fix would
repeat exactly the two-risky-changes-at-once pattern iter-32/33/34 each deliberately avoided
(blueprint.md iter-32/33/34 narrative paragraphs). It is deferred to the next iteration instead.
Rule 4 (smallest spec wins ties) — the sibling-lab wiring (iter-33/h) is explicitly "cheap and
structural" (evaluator's own words): the resolver is already generic, exported, and proven (13/13
tests, a line-level Retry trace) for Regime Lab; wiring it into the 4 siblings is mechanical, low
risk, and closes a P1-class gap (the exact bare-skeleton shape that failed browser-qa at iter-33)
that has been open on 4 of 5 labs for two iterations. Bundling it alongside the one risky backend
change (never two risky items, but a risky item plus a cheap mechanical one is exactly what this
rule permits) keeps this iteration's spec small while making real progress on two ledger items at
once.

## IN SCOPE

### Backend
- [ ] Bound `_membership_timeline`'s (`app.engine.data_manager`, `data_manager.py:497-544`) candidate-pool
      loading so it no longer holds every candidate symbol's full price history resident in RAM at
      once — process the pool in bounded batches (config-driven width, its own dedicated key, never
      `research.read_batch_size`) so peak resident bar data scales with the batch width, not the full
      590-symbol × 30-year product.
- [ ] Preserve `_BarCache`'s existing load-once-per-job / re-entrancy semantics (`_prefilled` guard,
      `prices.py`), `trailing_count`'s byte-identity contract, and every OTHER consumer of
      `prefilled_bar_cache`/`bars_asof`/`bars_after` across the engine (scoring/regime/sector) —
      no signature change to any existing caller, no second cache instance, no second producer for
      the Coverage payload row.
- [ ] Add a `git show HEAD`-pinned reference-oracle test (never an edited copy that also calls the
      new code, per the binding iter-32 lesson) proving `_compute_coverage_uncached`'s served
      payload (`universe_count`, `per_symbol`, `membership_timeline`, `gaps`, `capacity`) is
      byte-identical before/after the fix.
- [ ] Add a permanent regression test that proves the shipped batch width actually bounds peak
      accumulator size at the REAL `config.universe.symbols` / real live-basis scale (not a
      fixture-sized substitute) — a mutation-style proof that fails against a reverted/unbatched
      implementation (binding iter-29 and iter-31 lessons).
- [ ] Record a before/after peak-RSS/VmPeak measurement of this call specifically (isolate the named
      term, not the whole process, per the binding iter-31/iter-32 lessons) in `reports/perf-budgets.md`.

### Frontend
- [ ] Wire the already-generic, already-exported `resolveLabLoadPanel`
      (`apps/frontend/lib/lab-load-panel.ts`) into the 4 sibling research lab pages
      (`phase-severity-lab`, `regime-phase-factor`, `factor-lab`, `severity-velocity` inside
      `apps/frontend/app/research/_labs.tsx`) exactly as it is already wired for Regime Lab — same
      computing/error/retry states, same component, no fork or second implementation.
- [ ] No change to `resolveLabLoadPanel`'s own resolution logic (already proven correct at iter-33 —
      13/13 resolver tests, a line-level trace that Retry re-enters the loading state) — wiring only.

### New user-facing capability
On the 4 sibling research labs, a cold or slow load now shows a labelled "Still computing — Ns
elapsed" card with a spinner and honest explanatory copy instead of a bare unlabelled skeleton, and
a genuine backend-unavailable state shows a working **Retry** control instead of a frozen or blank
frame — identical to what Regime Lab already does.

### New information displayed
None — reuses the exact computing/error copy already shipped for Regime Lab (iter-33 UT-11).

### New user actions
A working **Retry** button on the 4 sibling labs' error state (previously absent on all 4).

### UI surface changes
`phase-severity-lab`, `regime-phase-factor`, `factor-lab`, `severity-velocity` loading and error
panels (inside `apps/frontend/app/research/_labs.tsx`).

### Product surface delta
Consistent honest-wait/retry behavior across all 5 Research labs (previously only Regime Lab had
it); no user-visible change to `/data`'s coverage panel or `/backtest`'s served values — the
prices.py fix is internal-only and byte-identical by requirement.

### Blueprint conformance
Both surfaces stay under existing Information-Architecture homes — no new page/nav. The prices.py
fix stays under the Coverage payload row's existing home (`GET /api/data`, Data Manager nav
section); the sibling-lab wiring stays under the Research nav section's existing `/research/*`
lab pages (Feature/journey homes table, J-06 row).

### Data-contract additions
None. The coverage/membership-timeline fix reuses the already-registered Coverage payload row's
computing module (`app.engine.data_manager`, `_compute_coverage_uncached`) and serving endpoint
(`GET /api/data`) — byte-identical output proven by TC-2; only the internal loading mechanism
changes. The sibling-lab wiring reuses the already-registered, already-exported
`resolveLabLoadPanel` component — no new field, no new endpoint, no new displayed value.

## OUT OF SCOPE

- Regime Lab's cold `view=pooled` background dispatch + diagnosing the intermittent HTTP 200 body
  "Internal Server Error" (iter-33/g) — deferred to the next iteration; bundling it here would put
  two risky backend changes in one diff (rule 5).
- `warmup.py:194` / what the readiness badge should say after a permanently failed warm-up;
  iter-31/e; iter-32/f (watch-only) — carried, non-blocking, untouched this iteration.
- The OWNER decisions iter-34/j (`GET /api/health` ≤ 0.1 s budget disposition) and iter-33/i
  (whether `start-frontend.sh` joins `HOST_GUARD_MARKER_FILES`) — explicit owner-only calls per the
  binding "Do not redo" list; not re-opened as agent work.
- The `[NEW]`-flagged walkthrough steps J-06's and J-07's own Acceptance text name, and
  `J-07.json`'s `1873` provenance line — capture-only ride-alongs (never a goal); may be captured
  incidentally by this iteration's own demo/QA lanes since real work is landing, but do not gate
  this iteration's Definition of Done.
- Any change to `compute_forward_aggregates`, `resolved_forward_aggregate_evidence`,
  `ensure_historical_forward_aggregates_dispatched` — byte-frozen, binding "Do not redo".
- Re-running J-07's iter-34 memory-pressure drill from scratch — only re-verify it against the new
  coverage/membership-timeline code path, per "Do not redo."

## DEFINITION OF DONE

- [ ] J-07 passes via browser-qa-agent (full-horizon forward-aggregate warm including the
      coverage/membership-timeline finalize step, 1 Hz `/api/health` poll, VmPeak margin, and the
      induced-memory-pressure drill re-verified against the bounded load)
- [ ] J-06 passes via browser-qa-agent; all 4 sibling research labs render the shared
      `resolveLabLoadPanel` computing/error/retry states
- [ ] Required-still-passing journeys J-01, J-03, J-04, J-05, J-08, J-09 remain green via
      deterministic golden replay (LLM fallback for any journey without a golden on file)
- [ ] No anti-goal violation introduced; ledger finding iter-29/d is closed with fresh first-hand
      evidence (byte-identity + live-basis-proven bound + VmPeak measurement), or, if a genuine
      residual remains, it is stated explicitly per the iter-31 split-record precedent — never
      silently rounded away
- [ ] Unit tests pass; the shipped batch bound is proven against the REAL live basis; the
      `git show HEAD`-pinned reference-oracle test proves byte-identical coverage/membership-timeline
      output; no regression in `_BarCache`/`bars_asof`/`bars_after`/`trailing_count`'s existing test
      suites
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-35-dev.md`

## TESTING REQUIREMENTS

- Browser: J-06 (all 5 research labs, including the 4 newly-wired siblings), J-07 (full-horizon
  warm + health poll + VmPeak margin + memory-pressure drill)
- Unit/integration: `test_bar_cache.py` / `test_data_manager.py` coverage + membership-timeline
  tests extended for the batched load; a new `git show HEAD`-pinned reference-oracle byte-identity
  test; a new live-basis-proven batch-bound regression test (mutation-style: fails reverted, passes
  shipped); `lab-load-panel.test.ts` plus wiring assertions for each of the 4 newly-wired labs
- Error cases: a candidate-pool symbol absent from `daily_prices` still resolves via an empty
  series with no crash (existing behavior, must not regress); a `membership_timeline_cache` MISS
  mid-batch must not leave `_BarCache`'s session registry in a partially-initialized state visible
  to a concurrent reader (existing lock-guarded contract, must not regress); clicking Retry while
  the backend is still down must not throw and must safely re-enter the loading state, never a
  second frozen error card

- TC-1: given `_compute_coverage_uncached` invoked for a resolved as-of on the live seed DB
  (590 symbols, 1996-01-02 → 2026-07-17) with `membership_timeline_cache` cleared for that
  dataset_version (a genuine cache MISS, matching J-07's own ingest-finalize scenario), when the
  batched/bounded loading runs, then the peak RSS/VmPeak growth attributable to this call is
  measured before and after the fix and recorded in `reports/perf-budgets.md`, showing peak
  resident bar data no longer scales with the full 590-symbol × 30-year product.
- TC-2: given the pre-fix `_membership_timeline`/`_compute_coverage_uncached` body pinned verbatim
  as a `_reference_*` helper via `git show HEAD:apps/backend/app/engine/data_manager.py`, when both
  the reference and the post-fix implementation run for the same snapshot-date set and as-of on the
  live seed DB, then the returned coverage payload (`universe_count`, `per_symbol`,
  `membership_timeline`, `gaps`, `capacity`) is byte-identical between the two.
- TC-3: given the REAL `config.universe.symbols` count and the real live basis (not a fixture-sized
  substitute), when the permanent regression test asserts the shipped batch width, then it fails
  against a reverted/unbatched implementation and passes against the shipped one.
- TC-4: given the fix landed, when browser-qa re-runs J-07's four steps, then `/api/health`
  continues returning HTTP 200 throughout with no new frozen window, the recorded VmPeak margin
  under `server.memory_cap_mb` does not regress from iter-34's measured margin, and the
  memory-pressure drill still aborts honestly with the same process continuing to serve.
- TC-5: given each of the 4 sibling research labs (`phase-severity-lab`, `regime-phase-factor`,
  `factor-lab`, `severity-velocity`) is loaded cold with a pending backend fetch, when the initial
  data request has not yet resolved, then each renders the shared `resolveLabLoadPanel` "computing"
  card (labelled elapsed-time copy, spinner, explanatory text that nothing partial/fabricated is
  shown), never the bare unlabelled `LabSkeleton`.
- TC-6: given a fetch failure / backend-unavailable condition on any of the 4 sibling labs, when the
  error state renders, then it shows the shared "Backend unavailable ... No figures are shown
  rather than fabricated values" card with a working Retry control, and clicking Retry re-enters the
  loading state (never a frozen error card) — mirroring the line-level trace already proven for
  Regime Lab (`_labs.tsx`'s `attempt` in the effect deps).
- TC-7: given the required-still-passing regression set (J-01, J-03, J-04, J-05, J-08, J-09), when
  the deterministic golden replay runs post-fix, then all 6 replay PASS with zero FAIL rows and zero
  reconciliation overturns.

## NOTES

- Lessons applied (session `lessons.md`, all binding for this iteration's primary item): iter-29
  (shipped bound proven against the REAL basis, a new chunk dimension gets its own config key);
  iter-30 second entry (name the exact frame the growth scales with); iter-31 second entry ("would
  the test fail if the fix were reverted?"); iter-32 first entry (pin the reference oracle via
  `git show HEAD`, never an edited copy that also compiles against the new code).
- If, after investigation, the batched approach cannot fully remove the scaling term (e.g. a genuine
  sub-consumer needs the whole pool resident for correctness), disclose the residual explicitly and
  record it as a new, separate ledger finding — mirroring the iter-31 `goal-evaluator` precedent of
  splitting a fixed-crash record from its measured residual — rather than silently downgrading scope
  or claiming a full bound that a mutation test would not actually prove (TC-3).
- Carried and explicitly out of scope this iteration (see OUT OF SCOPE): iter-33/g (Regime Lab
  background dispatch + HTTP-200-error-body diagnosis) is next in queue after this iteration;
  `warmup.py:194`; iter-31/e; iter-32/f (watch-only); the two OWNER decision items iter-34/j and
  iter-33/i remain open and unresolved pending the owner.
- Blueprint updated: `runs/goal-session-ops-hardening/state/blueprint.md` gets an iter-35 narrative
  paragraph and an appended note on the Coverage payload row documenting this fix as
  TARGETED/not-yet-built, per the session's established per-iteration convention. No Information
  Architecture change; no `blueprint.reapproval-requested` needed.
