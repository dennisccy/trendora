# Goal Iteration 36 — Re-dispatch: bound the whole-table price prefill + the evidence-path drawdown dict; wire honest loading into 4 sibling labs

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 36
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — prior verdict was ESCALATE (mandatory, no exceptions). Independently
  also meets trigger 1 (structural/cross-cutting): the coverage/membership-timeline fix touches
  `prices.py`, `data_manager.py`, and config together, reached simultaneously on J-07's
  ingest-finalize warm chain, J-05's aggregate-refresh path, and J-04's boot-warmup safety net —
  a ≥3-module change whose byte-identity / no-lookahead correctness is not covered by any single
  journey's own test suite.
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

Actually build what iter-35 planned but never shipped — bound the whole-table `daily_prices`
prefill on J-07's ingest-finalize warm path and give the four sibling Research labs the same
honest computing/error/retry loading behavior Regime Lab already has — and additionally close the
one new small memory-safety gap iter-35's own live run discovered on the `/api/evidence` serving
path.

## BACKGROUND

Iteration 35 wrote a full-depth spec (`docs/phases/goal-ops-hardening-iter-35.md`) targeting
exactly these two items, but the engine dispatched it at `evidence` depth against a Definition of
Done that required code — only `decomposer.done` and `browser-qa.done` ran (`.steps/` audit,
iter-35 eval.md), so the product tree is byte-identical to iter-34 and zero of the planned work
landed. J-06 and J-07 both dropped `passing` → `partial` purely from a heavier live scenario (a
long-lived process that had already run a 283-date backfill, then 5 concurrent as-of warms)
proving two carried ledger findings real: iter-29/d (the whole-table `prefilled_bar_cache` load,
carried since iteration 29) and iter-33/h (4 of 5 research labs still render a bare unlabelled
skeleton). Per the binding "Do not redo" instruction in iteration-state — "Do NOT rewrite the
iter-35 spec ... Execute it" — this iteration re-issues that SAME scope, not a re-plan.

One addition: the same iter-35 live run also surfaced a NEW, previously-unseen finding, ledger
item iter-35/k — `compute_drawdown_expectations`'s (`app.engine.forward_testing:2270-2392`)
`stored_by_key` `ForwardReturn` read aborted twice with `MemoryError` on the `/api/evidence`
SERVING path (`build_evidence_payload` → `compute_drawdown_expectations_cached` on a cache MISS)
during the same heavy scenario. The iter-35 evaluator's own next-step recommendation ranks this
item 4, "NEW AND SMALL, same family as item 1," immediately after the two carried items — it is a
genuine instance of J-07's own Acceptance clause ("no unbounded whole-table ORM materialization
remains on the warm OR SERVING path"), not scope creep, and closes the serving-path half of that
clause the session has not yet addressed (iter-29 only fixed the analogous `research.py`
accumulator, a different call site). Folding it into this already-full-depth, re-dispatched
iteration is logged as an interpretation call (`assumptions.md`, iter-36) rather than assumed.

Per the priority rubric: rule 1 (regressed journeys first) does not apply — nothing moved
`passing → failing`, both drops are `partial` per the iter-35 evaluator's explicit, checked
reasoning (byte-identical tree, no crash, honest degradation, AG-10 caps held). Rule 3
(unblockers) — this is the single item every recent evaluator has ranked first; it directly
unblocks the achievement gate. Rule 4 (smallest spec wins ties) — the sibling-lab wiring stays
purely mechanical (the resolver is already generic, exported, and proven — 13/13 tests, a
line-level Retry trace — for Regime Lab), and the new evidence-path fix mirrors an
already-established idiom (chunked/streamed read replacing `.all()`, the same shape as the item-1
fix and the iter-29 `research.py` precedent) rather than introducing new mechanism. Rule 5 (never
bundle two risky changes) — Regime Lab's cold `view=pooled` background dispatch + the undiagnosed
HTTP 200 carrying "Internal Server Error" (iter-33/g) stays deliberately OUT of this iteration; it
is a separate, real backend behavior change with its own open failure mode, and bundling it here
would repeat exactly the two-risky-changes-at-once pattern this session has avoided since iter-30.

Lessons applied (all binding): (iter-29) a shipped bound must be proven against the REAL config
value / real basis, never a fixture-sized knob, and a new chunk dimension (symbols, here) needs its
OWN config key rather than reusing `research.read_batch_size` (a rows knob); (iter-30, second
entry) name the exact frame the growth scales with and bound THAT, not a container next to it;
(iter-31, second entry) ask "would the test fail if the fix were reverted?" before accepting a
bound as proven; (iter-32, first entry) pin the byte-identity reference oracle via `git show HEAD`,
never an edited copy that also compiles against the new code; (iter-35, first entry) an
`evidence`-depth dispatch paired with a code-requiring DoD guarantees a wasted iteration — check
`.steps/` and `iter-<N>/depth-dispatched` before trusting any verdict about this iteration's
predecessor; (iter-35, third entry) cross-check a "page renders fine" claim against the browser
screenshot AND the server's own access log for the same minutes, not prose alone.

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
- [ ] NEW (ledger finding iter-35/k, same family): bound `compute_drawdown_expectations`'s
      (`app.engine.forward_testing:2270-2392`) `stored_by_key` `ForwardReturn` read (`symbol`,
      `asof_date`, `max_drawdown`, `underwater_days`, `time_to_recover_days`) to a chunked/streamed
      read whose peak accumulator no longer scales unboundedly with the claim's cohort size — same
      canonical computing module (`app.engine.forward_testing`), same cache table (`event_study_cache`
      via `compute_drawdown_expectations_cached`), same endpoint (`GET /api/evidence`), no second
      producer, byte-identical payload required for both reachers (the `/evidence` per-claim panel
      and the ingest-finalize `drawdown_expectations` warm).
- [ ] Reproduce the memory-pressure scenario (throwaway process, tightened cap, launched only via
      `scripts/start-backend.sh` per AG-10) against BOTH the pre-fix and post-fix code, and confirm
      the existing isolate-and-continue guard (`build_evidence_payload`, iter-29) still degrades
      honestly (`expectations_status: "unavailable"`, HTTP 200, never a 500 or wedge) in whichever
      case still fails, while the bound measurably reduces the failure at the real per-claim scale.

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
frame — identical to what Regime Lab already does. On `/evidence`, a per-claim drawdown-expectations
panel that previously could abort under heavy concurrent load now either renders its figures or
shows the existing honest NA disclosure — never a 500.

### New information displayed
None — reuses the exact computing/error copy already shipped for Regime Lab (iter-33 UT-11) and the
existing `expectations_status: "unavailable"` NA disclosure (iter-29).

### New user actions
A working **Retry** button on the 4 sibling labs' error state (previously absent on all 4).

### UI surface changes
`phase-severity-lab`, `regime-phase-factor`, `factor-lab`, `severity-velocity` loading and error
panels (inside `apps/frontend/app/research/_labs.tsx`). No visual change to `/evidence` — its
existing rendering (figures or honest NA) is unchanged; only the backend's resilience under load
improves.

### Product surface delta
Consistent honest-wait/retry behavior across all 5 Research labs (previously only Regime Lab had
it); no user-visible change to `/data`'s coverage panel, `/backtest`'s served values, or
`/evidence`'s rendered figures — all three backend fixes are internal-only and byte-identical by
requirement.

### Blueprint conformance
All three surfaces stay under existing Information-Architecture homes — no new page/nav. The
prices.py/data_manager.py fix stays under the Coverage payload row's existing home (`GET /api/data`,
Data Manager nav section); the drawdown-expectations fix stays under the Membership timeline /
research hot-key caches row's existing home (`GET /api/evidence`, Evidence nav section); the
sibling-lab wiring stays under the Research nav section's existing `/research/*` lab pages
(Feature/journey homes table, J-06 row). `runs/goal-session-ops-hardening/state/blueprint.md`
already carries the iter-36 narrative paragraph and both row-level notes for this iteration
(added by this decomposer pass).

### Data-contract additions
None. The coverage/membership-timeline fix reuses the already-registered Coverage payload row's
computing module (`app.engine.data_manager`, `_compute_coverage_uncached`) and serving endpoint
(`GET /api/data`) — byte-identical output proven by TC-2. The drawdown-expectations fix reuses the
already-registered Membership timeline / research hot-key row's computing module
(`app.engine.forward_testing`) and serving endpoint (`GET /api/evidence`) — byte-identical output
required. The sibling-lab wiring reuses the already-registered, already-exported
`resolveLabLoadPanel` component — no new field, no new endpoint, no new displayed value.

## OUT OF SCOPE

- Regime Lab's cold `view=pooled` background dispatch + diagnosing the intermittent HTTP 200 body
  "Internal Server Error" (iter-33/g) — deferred; bundling it here would put two risky backend
  changes in one diff (rule 5).
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
  coverage/membership-timeline and drawdown-expectations code paths, per "Do not redo."
- `_combination_observations` / `_event_study_members` (`app.engine.research`) — sibling
  accumulators with the same theoretical shape as `stored_by_key`, but unproven live (all observed
  MemoryErrors this session trace to `_factor_observations` (fixed iter-29) or `stored_by_key`
  (this iteration)) — named, non-blocking follow-up only (mirrors the iter-29 precedent).

## DEFINITION OF DONE

- [ ] J-07 passes via browser-qa-agent (full-horizon forward-aggregate warm including the
      coverage/membership-timeline finalize step, 1 Hz `/api/health` poll, VmPeak margin, the
      induced-memory-pressure drill re-verified against the bounded paths, and the
      `/api/evidence` serving-path fix confirmed under reproduced pressure)
- [ ] J-06 passes via browser-qa-agent; all 4 sibling research labs render the shared
      `resolveLabLoadPanel` computing/error/retry states
- [ ] Required-still-passing journeys J-01, J-03, J-04, J-05, J-08, J-09 remain green via
      deterministic golden replay (LLM fallback for any journey without a golden on file)
- [ ] No anti-goal violation introduced; ledger findings iter-29/d and iter-35/k are closed with
      fresh first-hand evidence (byte-identity + live-basis-proven bound + VmPeak measurement for
      iter-29/d; reproduced-pressure comparison for iter-35/k), or, if a genuine residual remains,
      it is stated explicitly per the iter-31 split-record precedent — never silently rounded away
- [ ] Unit tests pass; the shipped batch bound is proven against the REAL live basis; the
      `git show HEAD`-pinned reference-oracle test proves byte-identical coverage/membership-timeline
      output; the drawdown-expectations fix proves byte-identical `/api/evidence` payloads; no
      regression in `_BarCache`/`bars_asof`/`bars_after`/`trailing_count`'s existing test suites
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-36-dev.md`

## TESTING REQUIREMENTS

- Browser: J-06 (all 5 research labs, including the 4 newly-wired siblings), J-07 (full-horizon
  warm + health poll + VmPeak margin + memory-pressure drill + evidence-path resilience)
- Unit/integration: `test_bar_cache.py` / `test_data_manager.py` coverage + membership-timeline
  tests extended for the batched load; a new `git show HEAD`-pinned reference-oracle byte-identity
  test; a new live-basis-proven batch-bound regression test (mutation-style: fails reverted, passes
  shipped); `test_forward_testing.py` / `test_evidence.py` extended for the chunked
  `stored_by_key` read (byte-identical payload, mutation-style bound proof); `lab-load-panel.test.ts`
  plus wiring assertions for each of the 4 newly-wired labs
- Error cases: a candidate-pool symbol absent from `daily_prices` still resolves via an empty
  series with no crash (existing behavior, must not regress); a `membership_timeline_cache` MISS
  mid-batch must not leave `_BarCache`'s session registry in a partially-initialized state visible
  to a concurrent reader (existing lock-guarded contract, must not regress); clicking Retry while
  the backend is still down must not throw and must safely re-enter the loading state, never a
  second frozen error card; a claim whose `stored_by_key` read is starved by injected memory
  pressure still returns `expectations_status: "unavailable"` and HTTP 200, never a 500

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
- TC-8: given a claim whose `compute_drawdown_expectations` call is exercised under the same
  reproduced memory-pressure scenario that produced 2 live `MemoryError` aborts at iter-35 (a
  throwaway process, tightened `server.memory_cap_mb`, launched via `scripts/start-backend.sh`),
  when `GET /api/evidence` is requested for that claim before and after the fix, then the response
  is HTTP 200 in both cases (never a 500 or a wedge), the pre-fix run reproduces the abort with the
  claim's row carrying `expectations_status: "unavailable"`, and the post-fix run either serves the
  real computed panel or, if pressure is severe enough to still starve it, degrades identically
  honestly — with the failure rate/threshold measurably reduced, recorded in the dev handoff.

## NOTES

- Lessons applied (session `lessons.md`, all binding): iter-29 (shipped bound proven against the
  REAL basis, a new chunk dimension gets its own config key); iter-30 second entry (name the exact
  frame the growth scales with); iter-31 second entry ("would the test fail if the fix were
  reverted?"); iter-32 first entry (pin the reference oracle via `git show HEAD`, never an edited
  copy that also compiles against the new code); iter-35 first entry (verify `.steps/` and
  `depth-dispatched` before trusting a predecessor iteration's verdict); iter-35 third entry
  (cross-check a "renders fine" claim against the screenshot AND the access log, not prose alone).
- If, after investigation, either bounded approach cannot fully remove its scaling term (e.g. a
  genuine sub-consumer needs the whole pool/cohort resident for correctness), disclose the residual
  explicitly and record it as a new, separate ledger finding — mirroring the iter-31
  `goal-evaluator` precedent of splitting a fixed-crash record from its measured residual — rather
  than silently downgrading scope or claiming a full bound that a mutation test would not actually
  prove (TC-3, TC-8).
- Carried and explicitly out of scope this iteration (see OUT OF SCOPE): iter-33/g (Regime Lab
  background dispatch + HTTP-200-error-body diagnosis) is next in queue after this iteration;
  `warmup.py:194`; iter-31/e; iter-32/f (watch-only); the two OWNER decision items iter-34/j and
  iter-33/i remain open and unresolved pending the owner.
- Blueprint already updated this decomposer pass: `runs/goal-session-ops-hardening/state/blueprint.md`
  carries a new iter-36 narrative paragraph plus row-level notes on the Coverage payload row (iter-35's
  plan is unbuilt, this iteration executes it unchanged) and the Membership timeline / research
  hot-key row (the new `compute_drawdown_expectations` bound, TARGETED). No Information Architecture
  change; no `blueprint.reapproval-requested` needed.
- Interpretation call logged: whether folding ledger finding iter-35/k into this already-full-depth
  iteration (vs. deferring it to iter-37) is consistent with rule 5 — see `assumptions.md`, iter-36.
