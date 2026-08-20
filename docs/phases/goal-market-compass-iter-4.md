# Goal Iteration 4 — J-09 host resource-fit: halve the SQLite pool's page-cache memory

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** market-compass
- **Iteration:** 4
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** no
- **Target journeys:** J-09
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04 (regression smoke — every one of these
  pages reads through the same connection pool whose per-connection cache this iteration shrinks;
  their evidence proves no served value moved)
- **Anti-goal reminders:**
  - **AG-3:** A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation
    for the same as-of date — not merely that the page renders. *(critical)*
  - **AG-8 — Resilience to data-shape and data-scale change:** widening the data basis must never crash an existing
    page or exhaust memory — consumers of widened fields are re-validated, the UI degrades gracefully (contained
    error boundary, honest "—"/NA placeholder), and unbounded whole-table ORM loads are forbidden (the delta
    engine reads column-projected selects, never full record_json sweeps). *(critical)*
  - **AG-9 — Offline-deterministic ingest:** ingest jobs run only against the committed seed / local provider
    fixtures — no live external network calls or paid data services without an explicit goal.md amendment. *(critical)*
  - **AG-10 — Host resource ceiling (hardware protection), carried from ops-hardening:** heavy compute MUST be
    launched only via the project launch scripts, which MUST apply the host caps declared in
    `project-extensions/host-guard/host-guard.env` whenever present (CPU-affinity mask, BLAS/OMP thread caps)
    plus the `config.yaml` `server.memory_cap_mb` / `malloc_arena_max` values. Never remove, weaken, or bypass
    these caps; stripping a HOST-GUARD marked block from a launch script is a REGRESSION regardless of test
    outcomes. The ceiling VALUES are an owner-set envelope (current: `memory_cap_mb` 8192,
    `HOST_GUARD_MEMORY_HIGH` 12G, per the dated owner amendments recorded in
    `docs/archive/goal-ops-hardening.md`); only the owner may change them. *(critical)*

## GOAL

Halve the backend's standing memory footprint by shrinking one SQLite connection-pool pragma, with
zero change to any served value, so future full-depth (two-backend) iterations can run on this
shared host without repeating the 2026-08-20 freeze.

## BACKGROUND

Both the iter-3 evaluator's binding next-step and goal.md's own 2026-08-20 owner insert name J-09 as
the mandatory next slice, ahead of the J-05/J-06 freeze-drill make-up: `database.pragmas.cache_size`
currently reserves 256 MB of SQLite page cache per pooled connection, and the pool's 24 persistent
connections warming up (not any specific compute phase) drove a measured 4,837,420 kB VmPeak at
standing warm (`reports/perf-budgets.md:12018-12055` — "the pool's own connection warm-up IS the
peak", per J-09's own "Why"), comfortable in isolation against the 8192 MB `memory_cap_mb` but
dangerous once full-depth iterations run TWO backends — exactly the class of run that froze this
26.7 GB shared host this morning. No full-depth trigger holds for this iteration: the last verdict
was CONTINUE (not ESCALATE), the last coherence audit was COHERENCE-PASS (not FAIL), the
consecutive-lean counter is 0/6 (cadence not due), and the change itself is a single config value in
one file with a mechanical before/after proof — not a structural refactor and not a Data-Contract
migration. This plans at lean depth, matching the evaluator's binding recommendation, with no
escape condition invoked.

Target selection followed the priority rubric without deviation: nothing is regressed (rule 1 does
not apply), the last coherence verdict was PASS so no consolidation is owed (rule 2), and J-09 is
this iteration's clearest unblocker under rule 3 — not by sharing a Data-Contract value with another
journey, but by removing the host-capacity obstacle that stands between this session and the J-05/J-06
freeze-drill iteration's own two-backend, full-depth requirements. It is also the smallest available
change (rule 4: one YAML value plus measurements) and is fully dev-workable, not human-blocked (rule
6). Per goal.md's own parenthetical — "J-09 carries the config half" — the sibling Host resource-fit
constraints (memory-pressure test env-gating, the `next build` worker bound, `_BarCache.prefill`'s
re-bound) are explicitly NOT part of J-09's own Steps/Acceptance and stay out of this iteration (see
OUT OF SCOPE and NOTES).

**Lessons applied:** the iter-3 lesson on checksummed evidence ("run `md5sum` over
`reports/qa/<iter>-evidence/*.png` before citing any of them" — five of fourteen iter-3 screenshots
were duplicate/blank frames) applies to this iteration's J-01–J-04 regression capture. The iter-1
lesson on `pytest.skip()` masking an undelivered deliverable applies directly to the VmPeak drill
below: an opt-in-gated test that skips by default must never be read as "passing" for this
iteration's purposes — the measured number is the deliverable, not a green skip.

## IN SCOPE

### Backend
- [ ] `config.yaml:109` — change `database.pragmas.cache_size` from `-262144` to `-65536` (256 MB →
  64 MB SQLite page cache per pooled connection). Leave every other key in the `database:` block
  byte-unchanged, in particular `pool_size: 24` (`config.yaml:125`) and `max_overflow: 44`
  (`config.yaml:126`) — ops-hardening iter-72 sized their sum (68) to clear
  `server.limit_concurrency` (64) after a real pool-starvation outage; do not touch them while in
  the file. No code change is required: `apps/backend/app/db.py:61` already reads
  `pragmas.cache_size` from the typed config loader (`apps/backend/app/config.py:1999`) — the value
  flows through unchanged.
- [ ] Re-run the standing-warm VmPeak measurement against a backend started via
  `bash scripts/start-backend.sh` with the updated `cache_size`. Reproduce it via the LIGHTER path
  the original finding itself points to: drive a concurrent read burst sufficient to open the pool's
  persistent connections (reuse the existing pool-pressure / concurrent-load harness — the
  4,837,420 kB figure was driven by pool connection warm-up itself, not by any finalize-tail compute
  phase, per `reports/perf-budgets.md:12043-12051`), then read the process's `VmPeak` from
  `/proc/<pid>/status`. The full ~31-minute opt-in `backfill`+finalize-tail live drill
  (`test_start_backend_phase_by_phase_vmpeak_profile_under_pool_pressure`,
  `TRENDORA_RUN_HEAVY_INGEST_TEST=1`-gated) remains an available fallback only if the lighter path
  does not reproduce a comparable peak — see the assumption logged in NOTES.
- [ ] Append a new dated row to `reports/perf-budgets.md` (beside, never over, the existing
  `4,837,420` kB entry at lines ~12018-12055) recording the new measured figure.
- [ ] Re-run the existing pool-pressure / concurrent-load burst check
  (`apps/backend/tests/test_data_manager_concurrency_load.py`) at `server.limit_concurrency` (64)
  against the new `cache_size` and confirm zero `QueuePool` `TimeoutError`.
- [ ] Perform, and cite in the dev handoff, a same-as-of byte-identity spot check across
  representative read endpoints (`GET /api/dashboard`, `GET /api/stocks`, `GET /api/market-phase`,
  `GET /api/compass`), comparing captured responses before and after the config change.
- [ ] If the measured VmPeak exceeds 2.5 GB (2,621,440 kB), record the honest figure verbatim in the
  dev handoff and flag it for owner review — do not widen `memory_cap_mb`, `malloc_arena_max`, or the
  pool sizes to compensate (AG-10 governs).

(No Frontend section — J-09 is deliberately backend-only; goal.md waives its walkthrough
requirement explicitly: "no UI surface changes".)

### New user-facing capability
None. This iteration is backend-only performance tuning; the app's behavior and every displayed
value are unchanged — that sameness is exactly what the byte-identity spot check (TC-5) proves.

### New information displayed
None. The only new artifact is a dated measurement line appended to `reports/perf-budgets.md`, an
internal ops report, not a product surface.

### New user actions
None.

### UI surface changes
None — J-09's walkthrough requirement is explicitly waived in goal.md.

### Product surface delta
None visible to the user; the change is purely in backend standing memory footprint.

### Blueprint conformance
No new surfaces. `blueprint.md` is left unchanged this iteration: J-09 touches no page, no nav
entry, and no Information-Architecture home.

### Data-contract additions
None. `database.pragmas.cache_size` is a performance-only tunable, not a displayed value — this
iteration's entire acceptance bar is that it moves NOTHING in the Data Contract (TC-5), so it is
deliberately not added to `blueprint.md`.

## OUT OF SCOPE

- `database.pool_size` / `database.max_overflow` — untouched; see IN SCOPE rationale.
- `apps/backend/app/config.py`'s `PragmasCfg.cache_size` Python-side default (`-262144`) — left as
  the typed loader's documented fallback for a missing key; `config.yaml` is present and authoritative,
  so this default is never the effective value. J-09's own text scopes the change to "one number in
  config.yaml"; nothing else in the `database:` block or its loader.
- J-05 / J-06 freeze-drill make-up (remove+backfill the last two trading days and watch a real close
  seal a manifest; delete/restore a day and watch the basis disclosure flip) — deferred to the next
  iteration per the iter-3 evaluator's own plan. This iteration exists specifically to make that
  iteration's two-backend, full-depth run safe on this host.
- J-07, J-08 — untouched, still failing, not this iteration's target.
- Host resource-fit Constraints (a) the three `*_memory_pressure` test modules' env-gating plus the
  `test_start_backend_script.py` DB-copy sites switching to a synthesized/subset DB, (b) `next build`'s
  ≤4-worker bound in `next.config.mjs`, (c) `_BarCache.prefill`'s re-bound to a configured memory
  budget — goal.md's own text says these "ride the nearest applicable slices" and that "J-09 carries
  the config half" only; none of J-09's own Steps/Acceptance mention them (see NOTES for a forward
  flag).
- `[NEW]` walkthrough recordings for J-01–J-04, and re-taking iter-3's blank/duplicate screenshots —
  carried passenger tasks, explicitly attached by the iter-3 evaluator to the NEXT iteration (the
  J-05/J-06 make-up), not this one; J-09 itself has no UI surface to screenshot.
- The still-open owner decisions (J-01 step-1/step-2 rewording; the empty next-session-focus ruling;
  J-06's "underlying run unavailable" wording) — unresolved by this iteration, restated here only for
  visibility.
- Any change to `server.memory_cap_mb`, `malloc_arena_max`, or any `host-guard.env` value — AG-10
  reserves these to the owner.

## DEFINITION OF DONE

- [ ] Measured backend VmPeak at standing warm ≤ 2,621,440 kB (2.5 GB), OR — if missed — the honest
  measured figure is recorded in the dev handoff with an explicit owner-review flag (never a widened
  target)
- [ ] The new VmPeak figure is appended dated to `reports/perf-budgets.md` beside the existing
  `4,837,420` kB entry, with no existing line altered or removed
- [ ] The concurrent-load burst check at `server.limit_concurrency` (64) completes with zero
  `QueuePool` `TimeoutError`
- [ ] The same-as-of byte-identity spot check across `/api/dashboard`, `/api/stocks`,
  `/api/market-phase`, `/api/compass` shows zero diff before vs. after the config change
- [ ] `config.yaml` diff touches exactly one value (`database.pragmas.cache_size`); `pool_size`,
  `max_overflow`, and every other `database:` key are byte-unchanged
- [ ] Required-still-passing journeys J-01–J-04 remain green (deterministic replay + LLM fallback)
- [ ] No anti-goal violation introduced (AG-10 governs; `memory_cap_mb` / `malloc_arena_max` /
  host-guard caps untouched)
- [ ] Unit tests pass; no regressions
- [ ] Dev handoff written at `docs/handoffs/goal-market-compass-iter-4-dev.md`

## TESTING REQUIREMENTS

- Browser: no target-journey browser walkthrough — J-09's walkthrough is explicitly waived in
  goal.md ("deliberately backend-only (no UI surface changes)"). Required-still-passing smoke: J-01
  through J-04 via deterministic replay + LLM fallback (Today-page compass cards, `/stocks` sector
  coverage) to confirm the `cache_size` change moved nothing on screen.
- Unit/integration: re-run (or execute the lighter pool-warm-up-only equivalent of)
  `apps/backend/tests/test_start_backend_script.py`'s standing-warm VmPeak drill; re-run
  `apps/backend/tests/test_data_manager_concurrency_load.py`'s pool-pressure burst check. The
  byte-identity spot check (TC-5) may be a one-time scripted before/after comparison cited with
  concrete values in the dev handoff rather than a new permanent pytest — there is no ongoing
  "before" state once the config value changes for good.
- Error cases: N/A — no new input surface. The honest-miss path (TC-6) is this iteration's closest
  analog: a measured-over-budget result must be recorded truthfully and escalated, never silently
  absorbed by widening a ceiling value.

Test-first contract scenarios:

- TC-1: given `config.yaml`'s `database.pragmas.cache_size` is `-262144` and `pool_size`/
  `max_overflow` are `24`/`44`, when the developer edits only `cache_size` to `-65536`, then a diff
  of `config.yaml` shows exactly one changed value under `database.pragmas.cache_size` and
  `pool_size`/`max_overflow` still read `24`/`44`.
- TC-2: given a backend started fresh via `bash scripts/start-backend.sh` with the updated
  `cache_size`, when a concurrent read burst opens the pool's persistent connections (standing
  warm), then `/proc/<pid>/status`'s `VmPeak` reads at or below `2,621,440 kB` (2.5 GB).
- TC-3: given `reports/perf-budgets.md` already carries the `4,837,420 kB` measurement (lines
  ~12018-12055), when the new VmPeak figure is recorded, then the file contains a new dated
  line/row reporting it and a diff of the file shows only an addition — the existing `4,837,420`
  figure is neither edited nor removed.
- TC-4: given the backend is running with the new `cache_size`, when a request burst at
  `server.limit_concurrency` (64 simultaneous connections) is issued, then the burst completes with
  zero `QueuePool` `TimeoutError` and `GET /api/health` returns 200 throughout.
- TC-5: given a fixed `as_of` date with an existing stored run, when `GET /api/dashboard`,
  `GET /api/stocks`, `GET /api/market-phase`, and `GET /api/compass` are captured before and after
  the `cache_size` change, then every field value is identical and a byte diff of the two captured
  JSON payloads for each endpoint is empty.
- TC-6: given the measured VmPeak exceeds `2,621,440 kB`, when the developer writes the dev
  handoff, then it records the true measured figure verbatim and explicitly flags it for owner
  review, and `memory_cap_mb`, `malloc_arena_max`, and the pool sizes remain unchanged from their
  current values.
- TC-7: given the change is scoped to `database.pragmas.cache_size`, when
  `apps/backend/tests/test_no_magic_numbers.py`'s scan runs and a repo-wide grep for `cache_size`
  is checked, then `apps/backend/app/db.py:61`'s `pragmas.cache_size` read remains the only site
  that determines the effective pragma value — no second hardcoded `cache_size` number exists in
  any engine or route file.
- TC-8: given J-01–J-04 are currently passing with recorded evidence, when the regression replay +
  LLM-fallback lane re-verifies them after the `cache_size` change lands, then all four still
  report passing with no data or visual difference from their last recorded evidence.

## NOTES

- **Host safety while executing this spec.** This host is shared with another concurrent goal-mode
  engine and froze once already today from memory overcommit. Whichever path is used for the VmPeak
  drill (lighter concurrent-burst or the heavier opt-in `backfill` fallback), run it in isolation —
  not stacked with any other heavy job — and rely on the project launch scripts' host-guard caps
  (AG-10); do not bypass them to get a faster measurement.
- **Assumption logged.** J-09 step 2's phrasing ("the perf-budget drill's pool warm-up path") was
  read as licensing the lighter concurrent-burst reproduction over the full ~31-minute heavy drill;
  full reasoning is in `runs/goal-session-market-compass/state/assumptions.md` under `iter-4 —
  goal-decomposer`. Reversible: if the lighter path under-measures, the heavier opt-in drill is the
  fallback.
- **Forward flag for the next decomposer pass.** Host resource-fit Constraints (a) memory-pressure
  test env-gating + DB-copy-site fixes, (b) the `next build` ≤4-worker bound, and (c)
  `_BarCache.prefill`'s re-bound remain unassigned to any iteration. Consider picking them up before
  or alongside whichever iteration next runs two backends or a frontend build (the J-05/J-06
  make-up, or J-07/J-08) — (b) and (c) target the exact failure mode that froze the host.
- **Two owner decisions remain open** (carried from iter-2/iter-3, restated for visibility only):
  (1) J-06's "underlying run unavailable" wording is unreachable as written — either the compass
  read must resolve the stored manifest before the shared as-of contract, or the sentence needs
  rewording; (2) J-01's first two test steps (destructive Remove+backfill; an "Unassigned" filter
  option that no longer renders) need rewording, and the empty next-session-focus state on the
  frontier date needs an accept/revisit ruling. Neither blocks J-09.
