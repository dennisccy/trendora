# Goal Iteration 47 — Close the Evidence page's cache-thrash + third unbounded accumulator

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 47
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — prior verdict (iter-46) was ESCALATE; the dispatch's depth recommendation is
  binding by default and ESCALATE is a mandatory full-depth trigger with no exceptions.
- **Frontend Present:** yes (conditional — actual frontend change depends on which backend fix path is taken; see IN SCOPE / Frontend)
- **Target journeys:** J-06, J-07
- **Required-still-passing journeys:** J-01, J-03, J-04, J-05, J-08, J-09 (all 6 remaining Must-have
  journeys — a full 8-journey pass this round, per the evaluator's explicit item (1) and the ESCALATE
  cadence guidance to widen the regression set)
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
    marked block from a launch script is a REGRESSION regardless of test outcomes. *(critical)*
    (Owner amendment 2026-07-31: `memory_cap_mb` 6144→8192, `HOST_GUARD_MEMORY_HIGH` 10G→12G,
    `HOST_GUARD_GLOBAL_MEMORY_BUDGET` 22G→24G — the envelope VALUES, never the prohibition, are
    re-set; agents still may never raise/weaken/bypass caps themselves.)

## GOAL

Make `GET /api/evidence` stay within its committed budget after any data job — never falling onto a
multi-minute cold-recompute tail because one unrelated `forward_returns` row busted every claim's
cache — and bound the last unguarded whole-cohort read on that same page, so opening the Evidence
page is no longer the app's one remaining ordinary-use path to an availability failure.

## BACKGROUND

The iter-46 evaluator returned ESCALATE (mandatory full depth, no exceptions) and named this round's
"one real job" explicitly: `GET /api/evidence`'s per-claim cache key
(`r{max(scanner_runs.id)}-f{count(forward_returns)}`, `forward_testing.py:2475`) invalidates all 7
stored claim panels whenever ANY new `forward_returns` row lands anywhere in the DB — not only rows
relevant to that claim — forcing the page onto a ~163s-idle / >300s-loaded cold-recompute tail; the
same audit independently found a third unbounded whole-cohort materialization on the identical
serving path (`apps/backend/app/engine/samples.py:145` builds the whole-history observation list,
`:156` sorts it whole), a sibling of the two accumulators (`research.py`, `forward_testing.py`) this
session already bounded at iter-46. Both live on the SAME already-registered "Membership timeline /
research hot-key caches" Data Contract row and the SAME `/evidence` page — one coherent fix cluster,
consistent with rule 5's "one risky change per iteration." J-05 (the session's sole `failing`
journey, 3 consecutive rounds) is deliberately NOT this iteration's code target — its remaining
old-day-insert case is a separate, riskier change to a different subsystem
(`_membership_timeline`'s order-dependent recompute); see `assumptions.md` iter-47 for the full
reasoning. Applying the binding iter-46 lesson: a QA-fix or audit-fix pass that lands product code
AFTER browser-qa has run silently voids the entire lane — this iteration's browser-qa lane must be
the LAST product-code-adjacent event before scoring, and any audit-fix triggers a mandatory re-run.
Applying the binding iter-44 lesson: a memory-pressure guard proven by one green run is not proven —
the new `samples.py` bound gets the same 5-consecutive-run protocol already used for its siblings.

## IN SCOPE

### Backend
- [ ] Fix `GET /api/evidence`'s drawdown-expectations cache-key/staleness handling
  (`forward_testing.py:2475`) so an unrelated new `forward_returns` row never forces the page onto
  its cold-recompute tail — either narrow the cache key's invalidation scope to the claim's own
  relevant data, or serve the last-good generation behind an honest label while a background re-warm
  completes; `GET /api/evidence` must answer within its committed ≤1.5s endpoint / ≤3s page budget
  (`reports/perf-budgets.md` Item I) after any ingest lands one new `forward_returns` row, both idle
  and under concurrent load.
- [ ] Bound `apps/backend/app/engine/samples.py:145` (whole-history observation list) and `:156`
  (its whole-list sort) using the same slice-and-discard convention already applied to
  `_combination_observations` / `compute_drawdown_expectations` at iter-46; byte-identical output
  required against a pinned pre-fix reference oracle; prove it with 5 consecutive runs under the
  same tightened memory-pressure test used for its siblings (binding iter-44 lesson).
- [ ] Add the snapshot-date filter to `_drawdown_ticker_slice_map` (`forward_testing.py`, added
  iter-46) that the iter-46 auditor proved safe — narrows a 7,994,388-row read serving 7 claims to
  only the dates each claim's evaluation window needs; byte-identical output required.
- [ ] Guard the last two unprotected log calls in `apps/backend/app/engine/warmup.py:205` and `:212`
  with the existing `_log_isolation_failure` degrade-to-marker convention already applied at 19+
  other sites (iter-44/45/46).
- [ ] Full re-verification of all 8 Must-have journeys against the CURRENT build, each with its own
  dedicated evidence file/screenshot (no journey borrows another's script or asserts page-wide text
  a persisted history panel already satisfies — binding iter-46 lesson); ensure no product code
  change lands after this iteration's browser-qa lane runs, or re-run the lane before scoring
  (binding iter-46 lesson).

### Frontend (conditional — only if the backend fix path serves a stale generation)
- [ ] IF the chosen `GET /api/evidence` fix serves a previous-generation panel while re-warming
  (rather than correcting the cache key's own invalidation scope), render an honest "recomputing"
  label on the affected `/evidence` claim card(s), reading the new `expectations_status` field —
  mirroring the existing evidence-status rendering pattern already used elsewhere in the product
  (e.g. `/backtest`'s `evidence_status` badge). No frontend change is needed if the fix instead
  corrects the cache key's invalidation scope, since the served values are simply fresh.

### New user-facing capability
Opening the Evidence page shortly after any data job completes no longer risks a multi-minute stall
or an unresponsive backend — it reliably answers within its committed budget, honestly labeled if a
generation is still catching up.

### New information displayed
Conditional only: if the "serve-stale-behind-a-label" fix path is taken, an honest "recomputing"
indicator on the Evidence page's claim card(s) while a fresher generation warms in the background.

### New user actions
None.

### UI surface changes
None structurally — the existing `/evidence` page's claim cards gain, at most, a conditional status
label (see Frontend above). No new page, route, or nav entry.

### Product surface delta
The Evidence page (`/evidence`) becomes reliably fast and honest immediately after any ingest,
closing the app's last ordinary-use path to a multi-minute availability failure (per iter-45's
measured ~42-minute outage, 16/24 of whose wedge-window `MemoryError`s entered via this exact page).

### Blueprint conformance
No new page/nav — this iteration's work lives entirely under the already-registered `/evidence` home
(the "Membership timeline / research hot-key caches" row's Feature/journey-home entry, `blueprint.md`
Information Architecture table). `blueprint.md` has been updated additively: (1) an iter-47 top-level
paragraph documenting this iteration's scope and retroactively naming iter-46's two undocumented
additions per the iter-46 coherence-auditor's advisory; (2) the "Coverage payload" row's Notes now
name iter-46's zero-work redundancy gate; (3) the "Membership timeline / research hot-key caches"
row's Notes now name iter-46's `_warm_drawdown_expectations` boot trigger, correct its own stale
`[TARGETED, not yet built]` tag for iter-46's already-evaluator-confirmed accumulator bounds, and
register this iteration's CONDITIONAL `expectations_status` field (see below).

### Data-contract additions
CONDITIONAL, on the "Membership timeline / research hot-key caches" row (already registered;
`app.engine.forward_testing`, `GET /api/evidence`) — no second producer or endpoint either way:
- IF the fix serves a previous-generation panel while re-warming: one new optional field on the SAME
  `GET /api/evidence` payload, `expectations_status: "ready"|"refreshing"` (string enum, per claim),
  mirroring the already-registered iter-29 `expectations_status: "unavailable"` sibling value and the
  J-08 `evidence_status` pattern (`"ready"|"refreshing"|"not_yet_computed"`) on the neighboring
  Backtest-evidence row.
- IF the fix instead narrows the cache key's own invalidation scope so the slow tail never triggers
  on an unrelated ingest: **none** — the same fields, same values, just correctly cached.

## OUT OF SCOPE

- J-05's remaining old-day-insert case (a separate, riskier change to `_membership_timeline`'s
  order-dependent recompute) — evaluator's next-step item (4), deferred to a later iteration
  (`assumptions.md` iter-47); this iteration gives J-05 a dedicated live re-verification capture only,
  no code change.
- QueuePool exhaustion handling on `POST /api/backtest` (iter-46/ba) — a different endpoint, not on
  the Evidence-page serving-path cluster this iteration targets.
- A clean, uncongested re-measurement of J-04's boot-to-first-200 latency below the ≤5s budget — will
  be captured naturally as part of this iteration's J-04 Required-still-passing regression pass, but
  no code change is planned for it.
- A sixth `_BarCache.prefill` bound attempt; iter-33/g (Regime Lab's cold `view=pooled` dispatch,
  deferred a 12th time); the out-of-process watchdog/shutdown-deadline mechanism (deferred since
  iter-45); the golden-replay null-test fix for J-01/J-03 (test-infrastructure work, carried).

## DEFINITION OF DONE

- [ ] Target journeys J-06, J-07 verified via browser-qa-agent against the build this iteration ships
      (TC-1, TC-2, TC-3, TC-9)
- [ ] Required-still-passing journeys J-01, J-03, J-04, J-05, J-08, J-09 remain green (deterministic
      replay + LLM fallback), each with its own dedicated evidence (TC-8)
- [ ] `GET /api/evidence` answers within its committed ≤1.5s endpoint / ≤3s page budget after an
      ingest lands one new `forward_returns` row, both idle and under concurrent load, with
      byte-identical claim values (TC-1, TC-2, TC-3)
- [ ] `samples.py:145/156` bounded, byte-identical output proven, zero MemoryError escapes across
      5 consecutive pressure-test runs (TC-4)
- [ ] `_drawdown_ticker_slice_map` gains the snapshot-date filter, byte-identical output proven (TC-5)
- [ ] `warmup.py:205`/`:212` guarded with the `_log_isolation_failure` convention (TC-6)
- [ ] Browser-qa lane is the last product-code-adjacent event this iteration — no code change lands
      after it runs without a re-run before scoring (TC-7)
- [ ] No anti-goal violation introduced (AG-3 byte-identity preserved on every changed read path; AG-8
      no new unbounded whole-table load; AG-10 caps unchanged)
- [ ] Unit tests pass; no regressions
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-47-dev.md`

## TESTING REQUIREMENTS

- Browser: J-06 (all steps), J-07 (all 4 steps); full regression replay/LLM fallback for J-01, J-03,
  J-04, J-05, J-08, J-09
- Unit/integration: cache-key/staleness fix for `compute_drawdown_expectations_cached`; bounded
  `samples.py` accumulators (byte-identity + 5x memory-pressure repeat); `_drawdown_ticker_slice_map`
  filter (byte-identity + row-count reduction); `warmup.py:205`/`:212` guard clauses
- Error cases: a `MemoryError` raised inside `samples.py`'s bounded loop must degrade the SAME way its
  already-bounded siblings do (isolate-and-continue or honest per-claim `"unavailable"`, never crash
  the request); a `GET /api/evidence` request arriving mid-re-warm must never mix two generations of
  the SAME claim's fields in one response

Test-first contract: every DEFINITION OF DONE checkbox and every Data-contract
addition above maps to at least one concrete scenario line, numbered
sequentially, of exactly this shape:

- TC-1: given a fully-ingested backend with the evidence ledger's current 7 certified claims and an
  idle process, when `GET /api/evidence` is requested, then it returns HTTP 200 with all 7 claim
  panels populated within 1.5s (endpoint) / 3s (page), matching the committed Item I budget in
  `reports/perf-budgets.md`.
- TC-2: given that same idle backend, when a backfill job inserts exactly one new `forward_returns`
  row unrelated to any of the 7 stored claims and completes, then a subsequent `GET /api/evidence`
  still answers within the SAME ≤1.5s endpoint / ≤3s page budget — never falling onto the prior
  >163s cold-recompute tail — and every returned claim panel's values are byte-identical to the
  canonical computation for that claim (AG-3).
- TC-3: given a concurrent heavy ingest job in flight (mirroring J-07 step 1's warm), when
  `GET /api/evidence` is requested, then it answers within 300s and its response is provably correct
  (AG-3); if the response serves a not-yet-refreshed generation, its `expectations_status` field
  reads `"refreshing"` (never silently stale with no label) — if the fix instead scopes the cache key
  correctly, the response serves fresh values with `expectations_status` absent or `"ready"`.
- TC-4: given `samples.py:145`'s whole-history observation list and `:156`'s whole-list sort under
  the SAME tightened `ulimit -v` cap used for the research.py/forward_testing.py sibling tests
  (iter-46), when the bounding fix is applied and the pressure test is run 5 consecutive times, then
  all 5 runs pass with zero `MemoryError` escapes (binding iter-44 lesson) and the fixed output is
  byte-identical to a pinned pre-fix reference oracle.
- TC-5: given `_drawdown_ticker_slice_map` reading a claim's full ticker history today (7,994,388
  rows for 7 claims per the iter-46 audit), when the snapshot-date filter is added, then the same 7
  claims resolve to byte-identical `drawdown_expectations` values while the underlying query's row
  count drops to only the dates each claim's evaluation window requires (measured and recorded in
  the dev handoff).
- TC-6: given `warmup.py:205` and `:212`'s current bare log calls, when an exception is raised at
  either site during the boot-time drawdown-expectations warm, then the SAME `_log_isolation_failure`
  degrade-to-marker convention already applied at 19+ other sites fires instead, verified by a
  dedicated unit test for both lines.
- TC-7: given this iteration's code has landed and browser-qa has run, when any audit-fix or QA-fix
  pass subsequently modifies product code, then the browser-qa lane is re-run before the iteration is
  scored — verified by comparing the last product-code file mtime against the browser-qa results
  file's timestamp; the iteration is not scored complete if the results file predates the last code
  change (binding iter-46 lesson).
- TC-8: given all 8 Must-have journeys, when this iteration's browser-qa + replay lanes run, then
  every journey has its own dedicated evidence file/screenshot — none borrows another journey's
  script or asserts page-wide text a persisted history panel would already satisfy (binding iter-46
  lesson on the J-01/J-03 golden-replay null test) — and J-05 receives its first dedicated capture in
  3 rounds.
- TC-9: given J-07 step 1's full-horizon forward-aggregate warm running concurrently with
  `GET /api/health` polled at 1Hz, when this iteration's Evidence-page and `samples.py` fixes are in
  place, then every health poll still answers HTTP 200 within its existing budget (no
  frozen/unresponsive window) and process VmPeak stays under the declared 8192 MB `memory_cap_mb`,
  recorded in `reports/perf-budgets.md`.

## NOTES

- Binding lessons applied this iteration: iter-46 (a QA-fix/audit-fix pass landing after browser-qa
  silently voids the whole lane — TC-7); iter-44 (a memory-pressure guard proven by one green run is
  not proven — TC-4's 5-consecutive-run protocol); iter-46 (the golden replay is a null test for
  J-01/J-03 — TC-8's per-journey dedicated-evidence requirement); iter-41 (promoting a journey to
  Target silently removes coverage for journeys left off both lists — hence all 6 remaining journeys
  are explicitly listed as Required-still-passing, not left implicit).
- `assumptions.md` (iter-47) records the reasoning for targeting J-06/J-07 over J-05 this round —
  read it before treating J-05's continued `failing` status as an oversight rather than a deliberate,
  disclosed scope choice.
- Coherence: iter-46 returned COHERENCE-WARN (2 undocumented-but-non-violating additions, now
  retroactively documented in `blueprint.md` by this decomposer) — not a FAIL, so this iteration is
  not a mandatory consolidation-only pass, but the blueprint documentation debt is paid down as part
  of this dispatch regardless.
- If the developer's investigation finds the cache-key-scoping fix path is materially riskier or
  slower to prove correct than the serve-stale-behind-a-label path, prefer the label path — it has a
  direct, already-registered precedent (J-08's `evidence_status`) and degrades honestly by
  construction, matching AG-8's "never a blank application-error page" spirit extended to "never a
  silently stale one" either.
