# Goal Iteration 45 — Fix the membership-timeline recompute storm root-causing both J-05's and J-07's stalls

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 45
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — the prior iteration's verdict was ESCALATE; per the binding rule ("If the prior
  evaluator log emitted `ESCALATE`, you MUST set depth to `full` for this iteration"), this is
  mandatory. It is independently the evaluator's own bound-by-default recommendation for this
  iteration, and reinforced by trigger 1 (the touched Data-Contract row — membership timeline — feeds
  `/data`, `/sectors`, `/themes`, `/research/*`, and `/evidence`, so its correctness is cross-cutting).
- **Frontend Present:** no
- **Target journeys:** J-05, J-07
- **Required-still-passing journeys:** J-01, J-03, J-04, J-06, J-08, J-09 (full regression of the
  entire currently-passing set — the iter-44 evaluator explicitly asked that "all eight journey checks"
  be re-run after this fix, since their pictures were taken 21 minutes before the last build went
  silent, and this fix touches a Data-Contract row several of them transitively depend on)
- **Anti-goal reminders:**
  - **AG-1:** A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a
    **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked
    values MUST render a "not yet proven" state. *(critical)*
  - **AG-2 — Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha
    claims; never place or simulate orders. *(critical)*
  - **AG-3:** A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation
    for the same as-of date — not merely that the page renders. *(critical)*
  - **AG-4 — No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed
    out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **AG-5 — Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of;
    never introduce lookahead anywhere. *(critical)*
  - **AG-6:** No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the
    post-decompose gate. *(critical)*
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

Fix the single root cause blocking both target journeys — ingesting a snapshot date currently forces an
O(dates × pool) full-history resolver storm before any downstream aggregate can be served — so a
single-day backfill (J-05) and a full-deep-basis forward-aggregate warm (J-07) actually reach a terminal
outcome instead of stalling for ten-plus minutes or freezing the whole process.

## BACKGROUND

iter-44 finally named the stall live, via the SIGUSR1 all-thread dump armed at iter-40 and fired at a
genuine freeze for the first time: the blocked call chain is `resolve_with_reasons` ←
`_excluded_counts_by_date` ← `_membership_timeline` ← `membership_timeline_cached`, reached from
`_refresh_ingest_aggregates`'s very first step (`refresh_coverage_snapshot` → `_compute_coverage_uncached`
→ `membership_timeline_cached`) — **before** the forward-aggregate warm loop that J-07's
`horizons_done: 0/5` counter tracks ever runs. Ingesting ONE day bumps `_membership_dataset_version`
(a narrow but all-or-nothing stamp), which invalidates the ENTIRE cached membership timeline and forces
`_excluded_counts_by_date` to re-resolve exclusion reasons for all ~2,860 historical snapshot dates
against the ~591-symbol pool — an O(dates × pool) recompute that ran 1,001 s without finishing in iter-43
and left J-05's own live attempt at ~600 s, `dates_done: 0/1`, then `failed`, in iter-44.
`reports/perf-budgets.md`'s own "For the evaluator" section independently names this fix — not the
watchdog — "the fix the evidence actually points at" and "the highest-value next-iteration item," and
the iter-44 evaluator's next-step ranked it item (2), calling it "the highest-value item on the board"
that "deserves a round of its own." Per rule 3 (unblockers) this iteration targets it directly: it is the
one lever with a plausible path to making BOTH J-05 (whose defining case has never completed in three
attempts) and J-07 (whose warm has failed three consecutive live rounds) actually pass, not merely bound
one symptom's duration. The out-of-process watchdog (the evaluator's item (1), same artifact's OTHER
named candidate) is deliberately deferred to its own iteration — see `assumptions.md` iter-45 for the
reasoning; in short, it is a general safety net that, per J-07's own acceptance text ("never a deadlock,
wedge, or restart requirement"), cannot by itself make any currently-failing acceptance clause pass, and
rule 5 bars bundling it with this iteration's one genuinely risky change.

Applies the binding iter-38/39/42 lessons: no speculative rewrite absent a proven mechanism (this fix
targets the exact call chain the live dump named, not a guess); a memory/performance claim must measure
the whole job, never a narrowed function (TC-4/TC-5 below measure the real end-to-end job/warm, not an
isolated sub-call). Applies the binding iter-44 lesson: a memory-pressure guard proven by one green run
is not proven — the reviewer's third `MemoryError` escape (inside `_refresh_ingest_aggregates`'s own
error-logging call) must be closed and re-verified across 3–5 consecutive runs, not one.

Per rule 5 (never bundle two risky changes): the membership-timeline incremental fix is this iteration's
ONE risky product-code action. The memory-pressure logging fix, the golden-script text refresh, and the
stale-comment correction are small and mechanical, bundled per this session's established convention for
carried small items riding alongside the one risky change.

## IN SCOPE

### Backend

- [ ] `app.engine.data_manager` (`_membership_timeline`, `_excluded_counts_by_date`,
      `membership_timeline_cached`, and the `_membership_dataset_version`-driven invalidation): bound the
      finalize-hook recompute cost so ingesting a snapshot date at or after every already-cached
      historical date computes ONLY the new date's point (via `resolve_with_reasons`/
      `_excluded_counts_by_date`) and reuses every previously-cached date's point unchanged — the
      append-forward fast path. An ingest that lands a date strictly EARLIER than an already-cached date
      (a historical gap-fill, which can retroactively change order-dependent `entries`/`exits` for later
      cached dates) falls back to the EXISTING full recompute, unchanged — an explicit, logged scoping
      call (`assumptions.md` iter-45), not a general rewrite of the order-dependent traversal.
- [ ] Fixture-backed byte-identity test: the incremental (fast-path) output and the fallback (full
      recompute) output must both equal a pinned pre-fix full-recompute reference oracle for the same
      database state.
- [ ] Unit test asserting call-count: ingesting one new forward date does not re-invoke
      `resolve_with_reasons`/`_excluded_counts_by_date` for any already-cached historical date.
- [ ] Close the reviewer's THIRD `MemoryError` escape (iter-44 CRITICAL) inside
      `_refresh_ingest_aggregates`'s own error-logging path — `logger.exception()` itself allocating
      under the tightened test cap in one of the per-item isolation handlers. Re-run
      `test_ingest_finalize_memory_pressure.py` 5 consecutive times before calling it closed (binding
      iter-44 lesson: a single green run under an exhausted cap mostly measures luck, not a proof).
- [ ] `runs/goal-session-ops-hardening/journey-scripts/J-07.json` — refresh the stale dataset-size
      anchors (`n=8878`, `3508`) to match the current live dataset's actual counts (verified live, not
      guessed).
- [ ] Correct the stale comment near `data_manager.py:4730` (predating the grown dataset — locate by its
      stale numbers, not by line number, since prior edits may have shifted it).

### Frontend

None — this iteration is a backend algorithm/correctness fix with no UI-visible change in shape.

### New user-facing capability

Backfilling a single new historical day reaches a terminal outcome (instead of stalling for 10+ minutes
or failing outright) and its aggregates become visible on `/scanner-runs`/`/data` within a bounded time;
a full-deep-basis heavy forward-aggregate warm (J-07) advances past `horizons_done: 0` instead of
freezing the process.

### New information displayed

None.

### New user actions

None.

### UI surface changes

None — no new component; the global readiness badge and `/data`'s panels keep their existing shape.

### Product surface delta

None visible in shape for a healthy run. The observable delta is that `/data` backfills and heavy
forward-aggregate warms complete/progress instead of stalling or freezing the whole app — a reliability
fix, not a new feature.

### Blueprint conformance

J-05 and J-07 keep their existing cross-cutting homes per
`runs/goal-session-ops-hardening/state/blueprint.md`'s Information Architecture table (J-05: Data
Manager / Scanner Runs / Dashboard / Research / Evidence; J-07: global readiness badge + `/backtest`) —
no new page/nav/route this iteration. Blueprint updated with an iter-45 narrative paragraph and a
`[TARGETED]` tag on the Membership timeline / research hot-key caches Data-Contract row.

### Data-contract additions

None. This is an implementation-only change to the ALREADY-registered "Membership timeline / research
hot-key caches" row — same computing module (`app.engine.data_manager`), same tables
(`membership_timeline_cache`), same serving paths (`/data`, `/sectors`, `/themes`, `/research/*`,
`/evidence`), byte-identical output required. No second producer, no new field, no schema change.

## OUT OF SCOPE

- The out-of-process watchdog / shutdown-deadline mechanism (evaluator's next-step item (1);
  `perf-budgets.md`'s OTHER named "highest-value" candidate) — deliberately deferred to its own
  iteration (rule 5, `assumptions.md` iter-45); it is a general safety net, not this iteration's fix.
- A sixth `_BarCache.prefill`/`_SymbolColumns`/`bars_asof` bound attempt — the live dump's T2 finding
  (a slow per-call bar lookup inside `resolve_with_reasons`) is far less consequential once the resolver
  only runs for the new date instead of ~2,860 dates; no further per-call speedup this iteration
  (proportionality, binding iter-38/39/42 lessons).
- Extending the incremental fast path to historical gap-fill inserts (a date strictly earlier than an
  already-cached date) — falls back to the existing full recompute, unchanged (`assumptions.md`
  iter-45).
- iter-44/al's two unbounded evidence-path accumulators (`research.py:777`, `forward_testing.py:2343`) —
  a separate, real finding, deliberately not this iteration's second risky action (rule 5).
- The same thread-launch-guard class gap in `warmup.start_warmup` (`forward_testing.py:1691`) — same
  class as iter-43's fix, no evidenced incident there, carried.
- iter-33/g — Regime Lab's cold `view=pooled` background dispatch (deferred an eleventh time).
- iter-29/b and the badge wording after a permanently failed warm-up; iter-31/e; iter-32/f; iter-35/k;
  iter-36/n; iter-37/o; iter-37/q; iter-39/u — carried, untouched, none blocking J-05/J-07.
- J-07's `[NEW]` walkthrough recording and J-05's real acceptance frames — capture-only, never an
  iteration's own goal (rule 7); ride along with whichever iteration lands the passing evidence.
- Any further `docs/goal.md` edit or `memory_cap_mb`/host-guard cap change — no owner items outstanding.

## DEFINITION OF DONE

- [ ] Ingesting one new snapshot date's finalize hook does not re-invoke the O(dates × pool) resolver
      pass over previously-cached historical dates (TC-1).
- [ ] Every previously-cached date's membership-timeline point is unchanged byte-for-byte after an
      append-forward ingest (TC-2).
- [ ] Incremental (fast-path) and fallback (full-recompute) output are both byte-identical to a pinned
      pre-fix full-recompute reference oracle for the same inputs (TC-3).
- [ ] J-05's own defining case — a backfill of a day confirmed absent from `/scanner-runs` beforehand —
      reaches a terminal `ok` status with a rendered leaderboard within a bounded observation window
      (TC-4).
- [ ] J-07 step 1's full-deep-basis forward-aggregate warm advances `horizons_done` past 0 promptly and
      `GET /api/health` stays responsive throughout, in one clean single-trigger re-measurement (TC-5,
      TC-6).
- [ ] The existing induced-pressure abort (J-07 step 4) still holds — no regression (TC-7).
- [ ] `test_ingest_finalize_memory_pressure.py` passes 5 consecutive runs with no `MemoryError` escape,
      including inside the error-logging call itself (TC-8).
- [ ] `journey-scripts/J-07.json`'s dataset-size anchors match the current live dataset (TC-9).
- [ ] The stale comment near `data_manager.py:4730` is corrected (TC-10).
- [ ] Target journeys J-05, J-07 pass via browser-qa-agent.
- [ ] Required-still-passing journeys J-01, J-03, J-04, J-06, J-08, J-09 all report PASS with unique,
      dated evidence — no two journeys sharing one screenshot file (TC-11).
- [ ] No anti-goal violation introduced; AG-8's unbounded-load ban and AG-10's caps stay enforced
      end-to-end.
- [ ] Unit tests pass; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-45-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-05 (`journey-scripts/J-05.json`, re-triggered against a date freshly confirmed absent from
  `/scanner-runs`, not a stale default date), J-07 (`journey-scripts/J-07.json`, all 4 steps); full
  regression replay of J-01, J-03, J-04, J-06, J-08, J-09. Evidence capture must produce a distinct
  screenshot per journey (unique file, verified by checksum) — no two journeys sharing one capture
  (closes/keeps closed iter-43/ai).
- Unit/integration: a call-count/mock test proving `resolve_with_reasons`/`_excluded_counts_by_date`
  is invoked ONLY for the new date(s) on an append-forward ingest; a fixture-backed byte-identity test
  comparing incremental vs. fallback vs. pre-fix full-recompute output; a regression test pinning the
  historical-gap-fill fallback path still produces correct (full-recompute-equivalent) output; a
  regression test for the closed third `MemoryError` escape in the error-logging path, run 5 consecutive
  times.
- Error cases: a historical gap-fill backfill (a date strictly earlier than an already-cached date) must
  never silently reuse a stale/incorrect `entries`/`exits` value — either it correctly falls back to full
  recompute, or the dev handoff documents why the case cannot occur in this codebase's actual ingest
  paths.

Test-first contract: every DEFINITION OF DONE checkbox and every Data-contract addition above maps
to at least one concrete scenario line below.

- TC-1: given a live backend whose membership-timeline cache already has a point for every historical
  snapshot date up to and including `D_prev`, when a backfill ingests exactly one new, previously-
  unsnapshotted trading day `D_new > D_prev`, then the finalize hook's membership-timeline refresh does
  not invoke `resolve_with_reasons` (directly or via `_excluded_counts_by_date`) for any date `<= D_prev`
  — verified via a call-count assertion in a unit test.
- TC-2: given the same scenario, when the finalize hook completes, then the persisted membership-timeline
  payload for the new `dataset_version` stamp contains exactly one more point (for `D_new`) than the
  prior stamp's payload, and every date `<= D_prev`'s `size`/`entries`/`exits`/`excluded` fields are
  byte-for-byte unchanged from the prior payload.
- TC-3: given a full recompute via the PRE-FIX `_membership_timeline` implementation (a pinned reference
  oracle) run over a fixed database state, when compared to this iteration's output for the SAME
  `snapshot_dates` — both the append-forward fast path and the historical-gap-fill fallback path — then
  the payloads are byte-identical (fixture-backed equality test).
- TC-4: given a historical trading day CONFIRMED absent from `/scanner-runs` immediately before the run
  (checked via the UI/API, not assumed), when a backfill covering exactly that one day is submitted via
  `/data` and run to completion, then within 300 seconds the run reaches status `ok`, `/scanner-runs`
  lists the new date with its rendered leaderboard, and the persisted run record's `aggregates_refreshed`
  includes `"membership_timeline"`.
- TC-5: given the backend running the full deep basis, when the full-horizon forward-aggregate warm
  (J-07 step 1, one single ingest-finalize trigger, no manual mid-run probing) is triggered, then
  `background_compute.active[].horizons_done` advances past 0 within 120 seconds of `started_at` — no
  repeat of the prior 137-second stuck-at-0/5 stall.
- TC-6: given the same single-trigger warm, when `GET /api/health` is polled at 1Hz throughout, then
  every poll returns HTTP 200 within its rescoped ≤2 s bounded-compute-window budget, recorded in a fresh
  dated `reports/perf-budgets.md` section; the port never returns connection-refused and never goes
  fully unreachable.
- TC-7 (regression): given J-07 step 4's existing sanctioned induced-pressure test hook (a tightened
  `server.memory_cap_mb` in a throwaway process, launched only via `start-backend.sh`), when memory
  pressure is induced during a warm, then the warm aborts honestly via the existing per-item `MemoryError`
  isolation handler while the SAME process's `/api/health` and cached reads keep responding HTTP 200 —
  no deadlock, wedge, or restart.
- TC-8: given `test_ingest_finalize_memory_pressure.py`'s tightened-cap induction test after this
  iteration's error-logging fix, when it is run 5 consecutive times back-to-back, then all 5 runs pass —
  no `MemoryError` escapes any per-item isolation handler, including inside the `logger.exception()` call
  itself.
- TC-9: given `runs/goal-session-ops-hardening/journey-scripts/J-07.json`'s current dataset-size anchors
  (`n=8878`, `3508`), when this iteration's diff is reviewed, then the anchors are refreshed to match the
  current live dataset's actual, verified counts.
- TC-10: given the stale comment near `data_manager.py:4730` (predating the grown dataset), when this
  iteration's diff is reviewed, then the comment's numbers match the current live dataset.
- TC-11: given the full required-still-passing set (J-01, J-03, J-04, J-06, J-08, J-09), when the full
  regression replay runs against this iteration's build, then all six journeys report PASS with dated
  evidence, and an `md5sum` check over the evidence directory confirms no two journeys share one
  screenshot file.

## NOTES

- Applies the binding iter-38/39/42 lessons verbatim: no speculative rewrite absent a proven mechanism
  (this fix targets the exact call chain the iter-44 live dump named, not a guess); any memory/latency
  claim must measure the whole job/warm, never an isolated sub-call — TC-4/TC-5/TC-6 measure the real
  end-to-end job and warm, not a narrowed function.
- Applies the binding iter-44 (second) lesson: a memory-pressure guard proven by one green run is not
  proven — TC-8 requires 5 consecutive passes, not one.
- Applies the binding iter-39 lesson: three probes without hitting the target means diagnosing the wrong
  thing — this iteration does not repeat the diagnostic; it applies the fix the iter-44 live dump already
  identified.
- Applies the binding iter-27/iter-9 "order-dependent state" caution: `entries`/`exits` are defined
  relative to the FULL prior timeline, so the incremental fast path is deliberately scoped to the
  append-forward case only (see `assumptions.md` iter-45) — a historical gap-fill still uses the existing,
  already-correct full recompute.
- See `runs/goal-session-ops-hardening/state/assumptions.md` iter-45 (two entries) for the reasoning on
  sequencing this fix ahead of the out-of-process watchdog, and on scoping the incremental path to the
  append-forward case with a full-recompute fallback for historical gap-fills.
- `reports/perf-budgets.md`'s "For the evaluator" section (iter-44 dated entries) is the primary
  evidentiary source for this iteration's root-cause diagnosis — read it before re-deriving the call
  chain from scratch.
