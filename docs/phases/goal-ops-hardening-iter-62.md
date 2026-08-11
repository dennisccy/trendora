# Goal Iteration 62 — Stop `/data`'s ambient refresh from erasing good data, and fix `/api/health`'s dead `last_run_date`

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 62
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-07
- **Required-still-passing journeys:** J-01, J-03, J-04, J-05, J-06, J-09
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

A user who leaves `/data` open no longer sees a spurious "Backend unavailable" card wipe already-good
coverage/availability numbers during one transient refresh hiccup, and `GET /api/health`'s `last_run_date`
field finally reports the real latest scan date instead of a hardcoded `null`.

## BACKGROUND

J-07 is the only non-passing journey (7 of 8 pass, per `journey-history.json`), and its single remaining
gap is an owner-only call, asked 12 consecutive rounds running (iteration-state.md's Active Blockers):
does the ≤2s `/api/health` ceiling apply to an 18-23 minute heavy job, or only to the ~30s window it was
written for? Nothing further can be measured on that question (iter-61 reconciled 1,078/1,078 polls,
exactly one over 2.0s). A second concrete unblocker — the `browser-qa-phase.sh` line-286-before-272 fix
that would make target-journey goldens replay on the FULL path — is explicitly owner-gated too ("it needs
the owner's go-ahead because it is a build-system file", iter-61 eval.md, restated verbatim in NOTES).
Per the priority rubric's rule 6, this iteration does not re-plan either. Per iter-61's own evaluator
("everything else on the list is work the agents can do without you"), it instead picks up the two
concrete, ledger-documented, non-owner-blocked small defects the last two rounds surfaced but did not
fix (`journey-history.json` iter-61/g, iter-61/h — both explicitly labelled "SMALL AND WRITTEN DOWN"):
`/api/health`'s `last_run_date` hardcoded `null`, and the ambient `/data` refresh iter-60/61 shipped with
no automated protection. Investigating iter-61/h's own catch handler surfaced a second, related and more
material bug in the SAME code the auditor named but did not score (F3): a single transient failure on the
30-second ambient poll unconditionally overwrites already-rendered good data with the "Backend
unavailable" card — the exact "silently discard good data" failure mode this session's AG-8 discipline
exists to catch, one accident away from a real (if brief) false alarm on a healthy backend. This iteration
fixes that alongside adding the missing test, since both live in the same two `useEffect`/`.catch` sites.

**Depth — lean, not the evaluator's recommended full.** None of the four full triggers is literally true
this iteration: the prior verdict (iter-61) was CONTINUE, not ESCALATE/REGRESSION; iter-61's own
`coherence.md` was COHERENCE-PASS (0 blocking, 0 advisory); "Consecutive lean iterations dispatched: 0
(hardening cadence: 6)" is not due; and this iteration deliberately introduces no new user-visible
capability (goal.md's own Loop Mechanics: "full when an iteration first lands user-visible UI changes" —
this one lands none; `last_run_date` stays unexposed and the refresh fix is a same-surface bug fix, not a
new one). The evaluator's own recommendation is driven by wanting the full-depth-only demo/walkthrough
recorder to finally satisfy J-05/J-07's `[NEW]` walkthrough clause — a real, carried gap, but this
session's own repeated discipline is to never "manufacture a clause match... to buy a side effect"
(iter-59, iter-61 `assumptions.md`), and that discipline applies to depth selection the same as to verdict
class. Logged in `assumptions.md` as an interpretation call with its cost stated honestly.

**Lessons applied:** the reporting-headline defect (4 consecutive rounds: 57, 58, 60, 61) is explicitly
OUT OF SCOPE for a code fix this iteration — iter-60 already established the precedent ("report-writing
behaviors already covered by standing lessons... no product code change is planned for them") and this
spec follows it; the NOTES below restate the standing lesson for whichever lane writes this iteration's
own headline. The `test_health.py::test_health_returns_ok_shape` assertion that `last_run_date is None`
will break once the fix lands (`loaded_engine` genuinely carries `ScannerRun` rows, per iter-9/iter-28
warm-up fixture history) — this is an EXPECTED, in-scope test update, not a regression to chase.

## IN SCOPE

### Backend
- [ ] `apps/backend/app/api/health.py`: replace the hardcoded `"last_run_date": None` with
      `session.scalar(select(func.max(ScannerRun.asof_date)))`, ISO-formatted (`.isoformat() if ... else
      None`) — the SAME query shape `app/engine/data_manager.py` already uses for "latest run date" (e.g.
      its `latest_run_date` resolution), imported directly (`ScannerRun`, already available via
      `app.models`); no new computing module, no second derivation. Wrap it inside the handler's existing
      `db_ok`/`try`-`except` so a DB error degrades to `None`, the SAME convention already used for
      `db_ok`/`readiness`/`preflight`.
- [ ] `apps/backend/tests/test_health.py`: update `test_health_returns_ok_shape`'s stale
      `assert body["last_run_date"] is None` to assert the correct ISO date (queried directly via
      `select(func.max(ScannerRun.asof_date))` in the same test, against `loaded_engine`, which already
      carries `ScannerRun` rows). Add a new test against a freshly created, unloaded engine (the existing
      `create_db_and_tables(engine)`-only pattern already used elsewhere, e.g. `test_api_watchlist.py:173`)
      asserting `last_run_date` stays `null` on a DB with zero `ScannerRun` rows — preserves the
      pre-existing empty-DB contract the docstring already promises.

### Frontend
- [ ] `apps/frontend/lib/data-overview-refresh.ts` (new): a pure, framework-free helper —
      `nextStateAfterFetchError<T>(prev: {kind:"loading"}|{kind:"ok";data:T}|{kind:"error"})` — that
      returns `prev` UNCHANGED when `prev.kind === "ok"` (a periodic refresh's transient failure must
      never erase already-displayed data) and returns `{kind:"error"}` otherwise (preserves today's
      initial-mount-failure behavior byte-for-byte). No React/jsdom dependency, matching the existing
      `lib/*.ts` + `lib/*.test.ts` convention this codebase already uses (see `lib/api-base.ts`).
- [ ] `apps/frontend/app/data/page.tsx`: route `loadOverview`'s and `loadAvailability`'s `.catch` handlers
      (currently `setState({kind:"error"})` / `setAvailability({kind:"error"})` unconditionally, on ANY
      failure — auditor F3) through `nextStateAfterFetchError`, e.g.
      `setState((prev) => nextStateAfterFetchError(prev))`. Both call sites get the identical fix — same
      root cause, same file, same iter-60/61 ambient-refresh feature.
- [ ] `apps/frontend/lib/data-overview-refresh.test.ts` (new, run via `node` per the existing
      `api-base.test.ts` convention — no test framework is installed in this frontend): pins the helper's
      three input cases (`ok` preserved, `loading` → `error`, `error` → `error`).

### New user-facing capability
None — this iteration corrects an already-shipped refresh path's failure handling and a pre-existing,
currently-inert health field; no new capability.

### New information displayed
None. `last_run_date` remains unexposed in the UI (still typed in `apps/frontend/lib/api.ts:191`, still
rendered nowhere) — only its SERVED value becomes honest instead of a hardcoded lie.

### New user actions
None.

### UI surface changes
None — same `/data` page; only its existing transient-failure handling is corrected (a bug fix, not a new
surface). No new page, panel, or route.

### Product surface delta
A user with `/data` open during a brief, transient backend hiccup now keeps seeing the last-good
coverage/availability numbers instead of a spurious "Backend unavailable" card that would previously have
cleared on the next successful 30-second poll. The page's INITIAL-load failure case (no data yet) is
byte-identical to today. No other visible difference; `last_run_date` stays invisible.

### Blueprint conformance
No blueprint edit required this iteration. Both touched surfaces already have registered rows: "Backend
readiness / boot phase + preflight verdict" (`app.engine.readiness.compute_readiness`, `GET /api/health`)
and "Coverage payload" (`app.engine.data_manager`, `GET /api/data`) in `blueprint.md`'s Data Contract; `/data`
is the Data Manager home in the Information Architecture. This iteration changes neither row's computing
module nor its serving endpoint — only a served value's correctness (`last_run_date`) and a client-side
failure-handling behavior (never the computation itself).

### Data-contract additions
None. `last_run_date` is a pre-existing field of the already-registered `GET /api/health` payload, not a
new value, and it is not newly displayed anywhere. The `/data` refresh fix changes only how the frontend
CONSUMES the already-registered Coverage payload row on a failed fetch — no second computing module, no
second endpoint, no new field.

## OUT OF SCOPE

- J-07's owner-blocked health-latency ceiling question (13th round unanswered, restated verbatim in
  NOTES) — no code change to `/api/health`'s SLA/window interpretation.
- The `browser-qa-phase.sh` line-286-before-272 target-journey replay-routing fix — iter-61's own
  evaluator explicitly flagged it as needing "the owner's go-ahead" (build-system file); not attempted
  without that sanction.
- "Teach the summary lanes to re-read the file they summarise" (the review/QA/audit headline-accuracy
  defect, now 4 consecutive rounds: 57, 58, 60, 61) — this is agent report-writing behavior, not product
  code; per iter-60's own established precedent ("report-writing behaviors already covered by standing
  lessons... no product code change is planned for them"), this iteration relies on the standing
  `lessons.md` entries (restated in NOTES for whichever lane writes this iteration's own summary) rather
  than inventing a new reconciliation script.
- Recording the J-05/J-07 walkthrough — the `[NEW]` acceptance clause's recorder runs only at full depth;
  this iteration is lean (see BACKGROUND). It remains a passenger task, never a round's own goal, for the
  next full round.
- The long-carried backlog (iter-29/b, iter-31/e, iter-32/f, iter-35/k, iter-36/n, iter-37/o, iter-37/q,
  iter-39/u, iter-46/az, iter-46/ba, iter-47/bd, iter-47/bf, iter-47/bi, iter-48/bj, iter-57/f, iter-57/l,
  iter-59/g, iter-59/h, iter-59/k) and the Regime Lab feature backlog (iter-33/g, deferred 27 times) —
  untouched again, per rule 5 (one coordinated small fix, not stacking unrelated backlog items into the
  same diff).
- A component-level test harness (Jest/React Testing Library/jsdom) for `/data`'s interval-wiring itself
  (that the `useEffect` actually fires `loadOverview`/`loadAvailability` on the idle cadence) — confirmed
  this frontend has no test framework installed at all (`package.json` has no test script/dependency;
  every existing `lib/*.test.ts` runs as a plain Node script via `assert`, per `api-base.test.ts`'s own
  comment). Building one is out of proportion for this fix; the auditor already recorded this gap as true
  rather than arguing it away (iter-61/h). The extracted pure-logic helper's test is the closest available
  protection under the existing convention and directly pins the behavior this iteration changes.
- The `pollIdleIntervalSeconds === 0` edge case (auditor F3, "noted not scored") — carried as a
  documented, low-priority observation (config validation already requires it `>=
  health_poll_interval_seconds`, itself never configured to 0 in this project); not changed this
  iteration.

## DEFINITION OF DONE

- [ ] `GET /api/health`'s `last_run_date` reflects `max(ScannerRun.asof_date)` — non-null on a DB with
      scanner runs, `null` on an empty DB (TC-1, TC-2).
- [ ] `/data`'s ambient 30-second coverage/availability refresh no longer discards already-rendered data on
      a single transient fetch failure; the existing initial-mount-failure "Backend unavailable" path is
      byte-identical to today (TC-3, TC-4, TC-5, TC-6).
- [ ] J-07 remains correctly `partial` — this iteration does not claim it closed; the owner question is
      restated verbatim in NOTES for the 13th consecutive round.
- [ ] Required-still-passing journeys (J-01, J-03, J-04, J-05, J-06, J-09) remain green via deterministic
      replay + LLM fallback (TC-7).
- [ ] No anti-goal violation introduced — AG-3 (no wrong number reaches a screen; `last_run_date` is
      unexposed so nothing new is "displayed", but the SERVED value must match the DB) and AG-8 (honest
      degrade — the fix stops good data from being silently replaced by a fabricated-looking "unavailable"
      state on a transient blip; the true failure path still shows the honest "Backend unavailable" card).
- [ ] Unit tests pass; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-62-dev.md`.

## TESTING REQUIREMENTS

- Browser: no new browser journey to verify beyond the Required-still-passing regression set (J-01, J-03,
  J-04, J-05, J-06, J-09) — neither fix changes a journey's acceptance steps. `/data`'s existing
  "Backend unavailable" card and coverage panel are re-confirmed unchanged for the healthy/initial-error
  cases during that regression pass.
- Unit/integration: `test_health.py` (TC-1, TC-2); `lib/data-overview-refresh.test.ts` (TC-6); full
  backend `pytest` suite for no regression; existing `lib/*.test.ts` suite for no regression.
- Error cases: a DB read error inside `/api/health`'s `last_run_date` resolution must degrade to `null`,
  never crash the endpoint (mirrors the existing `db_ok`/`readiness` degrade convention); a fetch that
  rejects with no prior "ok" state must still show "Backend unavailable" (never silently swallowed).

Test-first contract:

- TC-1: given a `loaded_engine`-warmed database (≥1 `ScannerRun` row), when `GET /api/health` is called,
  then `last_run_date` equals `select(func.max(ScannerRun.asof_date))`'s ISO date, read directly from the
  same session in the test — not `null`.
- TC-2: given a freshly created, unloaded database engine (tables created, zero `ScannerRun` rows), when
  `GET /api/health` is called, then `last_run_date` is `null`.
- TC-3: given `/data`'s `state` is `{kind:"ok", data}` with rendered coverage numbers, when the ambient
  30-second `loadOverview` refresh's `fetchDataCoverage` call rejects (a single transient failure), then
  `state` stays `{kind:"ok", data}` unchanged — the coverage numbers keep rendering, no "Backend
  unavailable" card appears.
- TC-4: given `/data`'s `availability` is `{kind:"ok", data}`, when the ambient `loadAvailability`
  refresh's `fetchDataAvailability` call rejects, then `availability` stays `{kind:"ok", data}` unchanged
  (the same preserve-on-refresh-failure behavior, mirrored for the availability heatmap).
- TC-5: given `/data` mounts fresh with `state: {kind:"loading"}` (no prior data), when the INITIAL
  `loadOverview` call rejects, then `state` becomes `{kind:"error"}` and the page shows "Backend
  unavailable" — unchanged from today's behavior.
- TC-6: given `nextStateAfterFetchError` is called directly with each of the three possible previous
  states (`loading`, `ok`, `error`), when a fetch failure is signaled, then it returns `{kind:"error"}` for
  `loading`/`error` inputs and returns the SAME `ok` value unchanged for an `ok` input — verified via
  `node apps/frontend/lib/data-overview-refresh.test.ts` per the existing convention.
- TC-7: given the Required-still-passing journeys (J-01, J-03, J-04, J-05, J-06, J-09), when the
  deterministic replay lane runs after this iteration's diff, then all six still verify PASS via replay or
  the LLM fallback, with zero regressions attributable to the `health.py` or `data/page.tsx` changes.

## NOTES

- **OWNER — restated verbatim (13th consecutive round unanswered):** the app must answer its health check
  within 2 seconds while a background job runs; that promise was written for a job of about 30 seconds and
  our jobs last 16 to 23 minutes. Please say which you want — keep the 2-second promise for long jobs
  (J-07 stays open until the app is faster), or apply it to short jobs only (J-07's last gap closes). Two
  facts worth knowing: the app has served zero errors of any kind for the last several rounds, and nothing
  further can be measured on this question — it is a decision now, not a data gap. Separately, and also
  owner-gated: the `browser-qa-phase.sh` target-journey routing fix (`scripts/automation/browser-qa-phase.sh`
  line 286 needed at line 272) needs the owner's go-ahead as a build-system file, plus a cost decision
  (J-05's own check script waits 40 minutes and consumes a reserved date per run).
- Priority-rubric application: rule 1 (regressed journeys first) — none regressed, N/A. Rule 2
  (consolidation before features) — iter-61's `coherence.md` was COHERENCE-PASS, no forced consolidation.
  Rule 3 (unblockers next) — neither fix unblocks another journey; picked on rule 4 (smallest spec wins
  ties) among the ledger's own "SMALL AND WRITTEN DOWN" candidates (iter-61/g, iter-61/h). Rule 5 (never
  bundle two risky changes) — both fixes are small, same-file, same-feature-area, non-risky (no
  data-model migration, no provider integration); treated as one coordinated cleanup, not two. Rule 6
  (don't plan human-blocked work) — J-07's remaining acceptance gap and the lane-routing fix are both
  genuinely owner-blocked and are excluded; everything actually planned here is agent-actionable, per
  iter-61's own evaluator ("everything else on the list is work the agents can do without you").
- Review/QA/audit lanes: this session has repeated the SAME write-up defect for 4 consecutive rounds (57,
  58, 60, 61) — a "no blockers"/"complete"/"N passed" headline written over a status file or unmet item
  that says otherwise. Re-derive each claim in this iteration's own review/QA/audit reports from the raw
  artifact it summarizes (`ui-test-results.md`, the DoD checklist, `engine.log`) before writing it, per the
  iter-57/iter-58/iter-60/iter-61 lessons.
- Assumption ledger: one new entry filed this iteration (`assumptions.md`, iter-62 — goal-decomposer),
  recording the depth-selection deviation from the evaluator's "full" recommendation and its cost.
