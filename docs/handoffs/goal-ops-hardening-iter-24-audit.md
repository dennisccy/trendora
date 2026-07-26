# goal-ops-hardening-iter-24 Audit Report

**Date:** 2026-07-26
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-09 is genuinely implemented, not merely rendered: the iter-20 dispatch registry really does record
`started_at`/`horizons_done`/`horizons_total`, the bounded ring really is capped by config, the accessor is
the single producer, `compute_readiness` composes it once, `GET /api/health` serves it additively with a
real degrade path, and the badge/panel read that one poll. I did not take the handoffs' word for any of
this — I executed the composition, degrade, ring-cap and failure paths directly (16/16 checks, evidence
below) and independently cross-checked the disclosed timestamps against `forward_aggregate_cache` rows in
the live database (AG-3 holds to ~1.7 ms). The remaining gaps are honest and non-blocking: TC-7's
steady-state latency is borderline and not demonstrably met by the developer's own numbers, two test files
carrying six of this iteration's new tests were never executed by anyone in the pipeline, and the panel
conflates "unknown" with "nothing running" on a failed poll.

---

## 2. Findings

### Backend Findings

**B1 — GAP (not fixed): a failed dispatch's raw exception text is served to an unauthenticated endpoint**
`apps/backend/app/engine/forward_testing.py:1252` sets `reason = str(exc)` and that string is served
verbatim at `apps/backend/app/api/health.py:109`. For a SQLAlchemy/OS failure this can carry SQL text,
bound parameters, or filesystem paths. The phase spec explicitly required "the worker's existing
caught-and-logged exception message", and this is a local-first single-operator tool with a SQLite file DB
(no DSN credentials to leak — checked: `config.yaml` provider config and `app/db.py` use a local file
URL), so this is a limitation to record rather than a defect to fix. Not an AG-7 violation: no credential
or key is reachable through this path.

**B2 — GAP (pre-existing, not fixed; now user-visible): a thread-start failure wedges the identity AND the
badge**
`ensure_historical_forward_aggregates_dispatched` inserts the in-flight slot under the lock
(`forward_testing.py:1313-1317`) and only then starts the worker (`:1326`). If `Thread.start()` raises
(e.g. thread exhaustion), nothing pops the slot: the single-flight guard blocks every future dispatch for
that identity for the process lifetime. `git diff` confirms this ordering is byte-identical to iter-20
(`add(key)` → `thread.start()`), so this iteration did not introduce it — but it did change the
consequence: the top bar would now show "background compute running (1)" forever for a window that never
started. Fixing it means a `try/except` that pops the slot around `thread.start()`, which touches
`ensure_historical_forward_aggregates_dispatched` — explicitly byte-frozen by this phase's binding "Do not
redo" list. Left for a future iteration; recorded here so it is not rediscovered forensically.

**B3 — OBSERVATION: the ring is copied shallowly**
`forward_testing.py:1351` returns `list(_HIST_RECENT_OUTCOMES)` — a new list holding the registry's own
dict objects. No current consumer mutates them (FastAPI only serializes), so this is correct today; a
future consumer that edits an outcome in place would silently corrupt process state.

**B4 — OBSERVATION: the registry is snapshotted twice per health poll**
`health.py:63` calls `compute_readiness`, and `compute_preflight` (`readiness.py:323`) calls it again;
the second call's `background_compute` is discarded (only `["state"]` is read). Two extra lock
acquisitions on a no-op in-memory read per ~2 s poll — no correctness or measurable latency impact, noted
only because it means the served field and the preflight-internal one are separate reads.

**B5 — GAP (not fixed): TC-7's ≤ 0.1 s steady-state budget is not demonstrably met by the developer's own
measurement, and the reviewer's requested disclosure was only partially applied**
`reports/perf-budgets.md`'s Iteration 24 section records a 10-sample max of **0.127788 s** and an
official-convention single sample of **0.100023 s** — both at or over the unchanged ≤ 0.1 s budget the
DEFINITION OF DONE checkbox requires. QA's own independent 10-sample run recorded max 0.0946 s (within
budget). The reviewer asked for this to be flagged in the dev handoff's *Known Issues*; the dev handoff's
Known Issues section lists three items and none of them is the latency excursion (it is disclosed in
`perf-budgets.md` prose and in the QA report instead), so the disclosure is present but not where the
reviewer asked for it. On the substance I agree with the disclosed reading rather than escalating: I
verified by code and by execution that the new field adds **zero** database work (a pure in-memory dict
read under the pre-existing lock — see the verification evidence below), so nothing in this diff can have
moved the endpoint's ~98 % budget consumption. I could not add a third independent measurement: at audit
time both services are down (`curl http://localhost:8255/api/health` → connection refused; no `uvicorn`
or `next` process), and booting the backend purely to re-time an endpoint is a heavy operation on this
host (AG-10) with no diagnostic value the two existing measurements lack.

### Frontend Findings

**F1 — GAP (not fixed): "unknown" renders identically to "nothing is running"**
On a failed poll `ReadinessProvider` sets `backgroundCompute = null`
(`apps/frontend/components/readiness-provider.tsx:87`), and `BackgroundComputePanel` maps `null` through
`backgroundCompute?.active ?? []` (`apps/frontend/app/data/page.tsx:3593-3594`) into exactly the
known-empty copy: "No background compute running. Last outcome: none yet." (`:3603-3605`). That is an
affirmative claim about state the frontend does not have. Harm is bounded — the same failed poll drives
the top-bar pill to "Backend unavailable" (`readiness-provider.tsx:84`), and with the backend fully down
`/data`'s shared page-level loading gate hides every panel including this one (browser QA UT-07 verified
this and correctly attributed the gate to pre-existing page architecture). The exposed window is a
transient poll failure on an already-loaded page. The spec specified only empty-vs-active copy, never an
unknown state, so this is a gap rather than a spec miss.

**F2 — OBSERVATION: four of the five retained outcomes are served but never rendered**
The ring retains `startup.background_compute_history_size` (5) entries and `/api/health` serves all of
them, but the panel renders only `recentOutcomes[0]` (`data/page.tsx:3624`). This matches the spec's
literal "the most recent completed/failed outcome" — recorded only because the config value reads as if it
sizes what the operator sees, and it does not.

### Test Findings

**T1 — GAP (not fixed): two new tests assert byte equality across two separate reads of a live registry**
`test_health_background_compute_is_single_source` (`apps/backend/tests/test_health.py:113`) compares the
served field against a later direct `compute_readiness` call, and
`test_compute_readiness_composes_background_compute_empty_shape`
(`apps/backend/tests/test_readiness.py:292`) compares a direct accessor read against a later composed one.
`elapsed_ms` is computed **at read time** and the ring can gain an entry between the two reads, so both
assertions are only deterministic while no dispatch is in flight. In a whole-suite process where an
earlier file (e.g. `test_api_backtest.py`'s historical as-of requests, which really do dispatch and can run
for ~75 s) leaves a window active, they can fail spuriously. I weighed IMPORTANT and settled on GAP: the
product is correct, the failure mode is a false alarm rather than a missed defect, and the tests' own
docstrings show the authors were aware the registry is process-lifetime state.

**T2 — GAP (closed by other means, not by running them): the two files carrying six of this iteration's
new tests were never executed to completion by anyone**
`tests/test_readiness.py` and `tests/test_health.py` share the 30-year `loaded_engine` fixture; the
developer, the reviewer and QA each documented that the full-file run did not finish. Rather than launch a
fourth multi-hour run, I verified the *behaviors those six tests assert* by direct execution against the
real modules with a throwaway SQLite DB (no heavy fixture) — 16/16 checks passed, see section 3. The tests
themselves remain unrun; if a future iteration ever gets a cheap fixture, they should be executed once as
written (and T1 addressed first).

**T3 — OBSERVATION: what the executed tests do cover is tight**
`test_forward_testing_concurrency.py`'s four new tests use real threads with bounded event handshakes and
exact assertions (`horizons_total == len(cfg.walk_forward.horizons)`, `started_at` within 1 s of the
dispatch, ring length `== cap`, newest-first identity by name, `call_count["n"] == n_horizons`,
convergence-or-fail on the re-dispatch loop). No loose "in {a, b}" outcomes, no assertion that would pass
on a stub. The failure test proves the guard releases *and* that a subsequent dispatch completes, which is
the contract that matters.

---

## 3. Domain Assessment

The domain question for J-09 is whether the disclosed numbers are the dispatch's own truth (AG-3) or a
plausible-looking reconstruction. I checked this three ways, none of which relies on a handoff summary.

**Direct execution of the untested paths** (script:
`…/scratchpad/audit_check.py`, run with
`cd apps/backend && .venv/bin/python …/audit_check.py`; result **16/16 checks passed**):

- `compute_readiness` returns exactly `{state, detail, warmup, background_compute}` — one
  `background_compute` key, so the duplicate-key bug the developer self-reported is genuinely gone.
- A crafted accessor return is composed **verbatim** (no re-derivation), and a raising accessor degrades
  only that field to `{"active": [], "recent_outcomes": []}` while `state`/`warmup` stay byte-identical to
  the healthy call.
- `elapsed_ms` is computed at read time and grows between two reads of the same slot (0 → 350 ms across a
  350 ms sleep) — it is observation, not a stored estimate; `started_at` is tz-aware ISO-8601.
- Driving the real worker `cap + 3` times caps the ring at exactly `cfg.startup.background_compute_history_size`
  (5) with the newest identity first; a forced horizon exception records `outcome: "failed"` with the exact
  exception text and releases the `active` slot.
- Calling the `health()` handler directly serves the additive field with every pre-existing key intact, and
  with `compute_readiness` forced to raise, the response is `readiness: "unavailable"` **and**
  `background_compute: {"active": [], "recent_outcomes": []}` — the total-failure fallback is real, not a
  comment.

**Independent AG-3 cross-check against the database** (read-only query of
`apps/backend/data/trendora.db`, `forward_aggregate_cache`): browser QA's disclosed outcome for
`(2026-07-17, r1865-f3954530)` was `finished_at = 2026-07-26T12:57:03.885921+00:00`,
`duration_ms = 75108`. The cache rows for that identity are `12:56:02.744937`, `12:56:18.412623`,
`12:56:33.655229`, `12:56:49.161907`, `12:57:03.884239` — five horizons, ~15 s apart, and the **last**
commit is **1.7 ms** before the disclosed `finished_at`. TC-5's "within 2 s of `created_at`" is therefore
met by three orders of magnitude, and the 75.1 s duration matches the observed 5-horizon span. Nobody in
the pipeline ran this cross-check; it is the strongest correctness evidence this iteration has.

**Single-source and no-behavior-change**: `grep` confirms `background_compute` appears in exactly one
producer (`forward_testing.get_background_compute_status`), one composer (`readiness.py:254-257`) and one
serving key (`health.py:109`); `compute_preflight` consumes only `readiness_result["state"]`, so the value
is not restated inside `preflight`. The diff of `forward_testing.py` shows the dispatch decision, keying,
and the `!= "ready"` gate untouched — the only semantic change is a `set` → `dict` swap at the same call
sites, and the pre-existing iter-19/iter-20 keying tests pass (QA re-ran them: 3 passed). Frontend
`npx tsc --noEmit` re-run by me: **exit 0**. `scripts/` and `project-extensions/` are untouched, so AG-10's
host-guard blocks are intact; the accessor issues no query and no network call (AG-9/AG-8 unaffected).

Anti-goal language: the badge reads "background compute running (N)", the panel hint explicitly disclaims
finish-time estimates and completion percentages, and the process-lifetime sentence is present in all three
states (browser QA verified it verbatim in each). No proven/reassurance language, no evidence claim, no
new score — AG-1/AG-2/AG-4/AG-6 clean.

---

## 4. Fixes Applied During This Audit

None. No CRITICAL or IMPORTANT finding survived verification; every issue above is a GAP or OBSERVATION,
and the two candidates I considered fixing (B2's thread-start wedge, T1's flaky equality assertions) touch
either a byte-frozen function or test code whose defect is a false-alarm risk, not a masked defect —
fixing them here would be scope creep against this iteration's additive-only mandate.

---

## 5. Recommended Next Step

Proceed. J-09 is achieved and, unusually for this session, its correctness is provable from the payload
alone rather than by forensic DB reconstruction — which was the point of the iteration.

Carry forward, in priority order:

1. **B2** — wrap `thread.start()` so a start failure pops the in-flight slot; it is the only finding that
   can produce a permanently wrong user-visible state. Needs an amendment to the "Do not redo" freeze on
   `ensure_historical_forward_aggregates_dispatched`, so it belongs in a decomposer-planned iteration, not
   an opportunistic patch.
2. **T1** — make the two single-source tests compare on identity/shape (or exclude `elapsed_ms`) before
   anyone attempts a whole-suite run, so they cannot manufacture a false REGRESSION verdict.
3. **F1** — give the panel a distinct "backend unreachable — background-compute state unknown" copy for
   `backgroundCompute === null`, separate from the known-idle copy.
4. **B5** — the ≤ 0.1 s steady-state budget remains an owner question, unchanged by this iteration; the
   evidence that this diff adds zero DB work is now independently confirmed, so any future excursion should
   not be attributed to `background_compute`.
5. Unchanged carries from iter-23: retarget `test_forward_testing_serving_split.py`'s four `is_latest`
   monkeypatches before removing the dangling imports at `backtest.py:75` / `mcp/tools.py:38`; backlog card
   B-1107 (bounding concurrent dispatch count) stays owner-optional.
