# goal-ops-hardening-iter-49 Execution Plan

## What to Build

- **Per-horizon / per-claim sub-phase timing.** Extend the existing whole-phase `"J-05 finalize-tail
  phase timing"` log line convention with a NEW, additive sub-phase log line so a slow run's cost is
  attributable to a specific horizon or claim, not just "the loop as a whole":
  - `forward_aggregates_warm` loop (`apps/backend/app/engine/data_manager.py:3965-4004`, the
    `for h in cfg.walk_forward.horizons:` loop calling
    `forward_testing.forward_aggregates_ingest_cached(session, h, cfg, as_of=latest_run_date)`): time
    each horizon's own call, log e.g. `"J-05 finalize-tail sub-phase timing: job=%s phase=forward_
    aggregates_warm horizon=%s elapsed=%.2fs"`.
  - `drawdown_expectations_warm` loop (`data_manager.py:4091-4130`, `for entry in ledger_entries:`
    calling `forward_testing.compute_drawdown_expectations_cached(session, claim, cfg)`): time each
    claim's own call, log with a stable, honest claim identity (e.g. `claim.get("kind")` +
    `claim.get("horizon")`, or the existing `forward_testing._drawdown_expectations_cache_subject(claim)`
    hash — never a raw index, which is not diagnostic across runs).
  - Keep both existing whole-phase log lines byte-for-byte unchanged (additive only, per the spec).

- **Diagnose the actual cost driver before committing to a fix** (the spec is explicit: diagnosis must
  precede the fix). Three named hypotheses to rule in/out, each with a concrete check:
  1. **Measurement contamination** (iter-6 precedent) — correlate each of the ≥3 live-run timestamp
     windows against `logs/hwmon/hwmon.csv` and process listings; note whether a concurrent pytest run
     or other heavy process overlapped a sample.
  2. **Genuine per-call cost growth against DB volume** — `forward_aggregates_ingest_cached`'s MISS path
     (`forward_testing.py:1407-1544`) calls `compute_forward_aggregates` for `as_of=latest_run_date`,
     an EXPANDING window that must legitimately rescan more history as `forward_returns`
     (344,334+ rows and growing every iteration this session backfills) / `scanner_results` grow — this
     is the leading hypothesis given the code's own docstring ("a backfilled EARLIER date's forward
     returns newly enter the latest as-of's expanding window"), and is consistent with the 102s → 153s
     → 1,334s spread tracking DB growth across the session's own successive live drills, not one run.
     Record row counts (`forward_returns`, `scanner_results`) at each of the ≥3 measurement times to test
     this directly. `compute_drawdown_expectations` (`forward_testing.py:2333-2486`) is the analogous
     candidate for `drawdown_expectations_warm`: it calls `phase_context_by_date(session, as_of=None,
     ...)` — "the SAME causal timeline" — freshly, INSIDE the loop, once PER CLAIM (7 claims today); if
     that all-history read is not itself cheap, 7 redundant calls to it is a concrete, checkable
     candidate cost multiplier independent of DB growth.
  3. **Lock/single-flight contention** — `_FORWARD_AGG_LOCK` / `_FORWARD_AGG_INFLIGHT`
     (`forward_testing.py:1393-1398`, iter-15) has a 45s bounded wait before a waiter falls through and
     computes independently (redundant compute, not a hang). Add a log line (or counter) on the
     fall-through branch (`forward_testing.py:1497-1500`) so a live run can show whether this ever fires
     during the ≥3 TC-1 drills — if it never fires, hypothesis 3 is ruled out cheaply.

- **Bound whichever mechanism the diagnosis names**, for BOTH `forward_aggregates_warm` and
  `drawdown_expectations_warm`, so the job's ENTIRE finalize tail reaches a terminal
  `data_provider_runs.status` within TC-1's 1,200s bound across ≥3 independent live runs.
  `compute_forward_aggregates` / `forward_aggregates_ingest_cached` and `compute_drawdown_expectations` /
  `compute_drawdown_expectations_cached` remain the SAME sole canonical producers — byte-identical output
  required per horizon/claim against a pinned pre-fix reference oracle (TC-3); no second producer, no
  schema change (Data-contract additions: None). If hypothesis 2 (genuine growth) is confirmed as the
  driver, expect the fix to look like the iter-48 fix's own shape (reuse/memoize what does not need
  re-deriving instead of a blanket O(history) rescan) rather than a chunk-size tuning knob — e.g.
  memoizing `phase_context_by_date`'s single all-history read ONCE per finalize-tail invocation instead
  of once per claim is a concrete, low-risk, provably-byte-identical candidate for
  `drawdown_expectations_warm` worth checking first, since it changes nothing about what is computed,
  only how many times. Whatever the actual fix, it must preserve every existing per-item isolation
  convention (`MemoryError` → stop loop + `_release_process_memory()`; generic exception → log + continue
  — `data_manager.py` finalize-tail try/except blocks, unchanged pattern) so TC-11 holds.

- **Re-run the existing opt-in live test**
  (`test_start_backend_historical_gap_insert_reaches_terminal_status_within_bound`,
  `apps/backend/tests/test_start_backend_script.py:856-969`, `TRENDORA_RUN_HEAVY_INGEST_TEST=1`,
  currently `xfail(strict=False)`): remove the `xfail` marker if the fix makes it genuinely pass on ≥3
  runs; otherwise leave it `xfail` with an accurate, updated reason naming whatever cost driver remains
  open. Never loosen its assertions (the 1,200s bound, `status in ("ok","partial")`,
  `snapshots_created >= 1`, `"membership_timeline" in aggregates_refreshed`, zero non-200 health polls)
  to force a pass.

- **New/extended tests per TESTING REQUIREMENTS** (see Key Test Scenarios below). The iter-45
  append-forward suite and the iter-48 gap-insert reuse branch (`data_manager.py:891-917`,
  `_membership_timeline_incremental`/`append_forward` gating) stay byte-for-byte untouched — do not
  redo, already correct and mutation-proven (audit T1).

- **Frontend:** none. `Frontend Present: no` — confirmed by the phase spec metadata and the IN SCOPE
  section ("Extending the J-05 golden replay script … was investigated and found infeasible … TC-1's
  proof continues to run through the live/integration test + manual drill pattern, not the browser
  replay lane").

- **`blueprint.md`**: append an iter-49 changelog paragraph plus a note on the existing "Membership
  timeline / research hot-key caches" Data Contract row — no Information Architecture change, no new
  Data Contract value (per spec).

## Agents Required

- backend-data: yes — instrumentation, diagnosis, the bound fix in `data_manager.py`/`forward_testing.py`,
  and all TESTING REQUIREMENTS coverage.
- frontend-ux: no — this iteration is backend-only; no frontend file should be touched.

## Frontend Present: no

## Files to Create/Modify

- `apps/backend/app/engine/data_manager.py` — add per-horizon sub-phase timing inside the
  `forward_aggregates_warm` loop (~3965-4004) and per-claim sub-phase timing inside the
  `drawdown_expectations_warm` loop (~4091-4130); apply the bound the diagnosis identifies, preserving
  the existing `MemoryError`/generic-exception isolation convention around each loop.
- `apps/backend/app/engine/forward_testing.py` — likely touch site for the actual bound
  (`compute_forward_aggregates`/`forward_aggregates_ingest_cached` ~1090-1546,
  `compute_drawdown_expectations`/`compute_drawdown_expectations_cached` ~2280-2577) — the warm seam
  goal.md already unfroze for bounding work; byte-identical output required, no signature/schema change.
  Possibly a log line or counter on the single-flight fall-through branch (~1497-1500) to test hypothesis
  3.
- `apps/backend/tests/test_data_manager.py` — per-horizon/per-claim sub-phase timing tests (TC-2); error-
  case tests injecting a genuine non-memory exception and a `MemoryError` inside each newly-bounded loop's
  own new code (TC-11), reusing the existing per-item isolation test pattern
  (`test_historical_gap_fill_resolver_failure_isolated_never_hangs_the_job` is the precedent shape).
- `apps/backend/tests/test_forward_testing.py` (or `test_research_streaming.py` if that is where sibling
  byte-identity tests for this module already live — confirm the existing convention before adding) —
  pinned-reference byte-identity tests for `forward_aggregates_ingest_cached` (every configured horizon:
  1, 5, 10, 20, 60) and `compute_drawdown_expectations_cached` (every ledger claim) against the fix
  (TC-3).
- `apps/backend/tests/test_start_backend_script.py` — re-run/adjust
  `test_start_backend_historical_gap_insert_reaches_terminal_status_within_bound` (~856-969): remove
  `xfail` if genuinely fixed, else update the reason string honestly (TC-6).
- `reports/perf-budgets.md` — Item R gets a new dated addendum: the ≥3 new live-run phase tables (with
  per-horizon/per-claim breakdowns), the diagnosis finding (which hypothesis was confirmed and how), the
  TC-5 VmPeak margin against `memory_cap_mb=8192`, and the TC-6/xfail outcome. Append-only — do not edit
  prior dated sections.
- `docs/blueprint.md` — iter-49 changelog paragraph + note on the existing Data Contract row (no IA/data
  contract change).
- `docs/handoffs/goal-ops-hardening-iter-49-dev.md` — required dev handoff.
- `runs/goal-session-ops-hardening/journey-scripts/J-05.json` — rotate the target date ONLY if this
  iteration's own ≥3 live drills consume `2012-01-05` (the current target per the iter-48 audit fix); log
  the rotation per the iter-46 lesson if it happens. Do not touch otherwise.

**Explicitly do NOT touch** (TC-10, AG-10 — `git diff` over these must be EMPTY): `config.yaml`,
`project-extensions/host-guard/host-guard.env`, `scripts/start-backend.sh`, `scripts/dev.sh`. Never
re-tune `memory_cap_mb`/`malloc_arena_max`/host-guard cap values.

## Key Test Scenarios

- TC-1: a historical-gap-insert backfill's `data_provider_runs.status` reaches a terminal value within
  1,200s of the snapshot write, on ≥3 independent live runs on an otherwise-idle host (not 1-2 —
  binding iter-44/iter-48 lesson).
- TC-2: per-run phase-timing log names, for BOTH `forward_aggregates_warm` and
  `drawdown_expectations_warm`, the SPECIFIC horizon/claim that consumed the largest share of that
  phase's own wall time.
- TC-3: `forward_aggregates_ingest_cached`'s output for every horizon and
  `compute_drawdown_expectations_cached`'s output for every ledger claim are byte-identical to a pinned
  pre-fix reference computation for the same inputs.
- TC-4: `GET /api/health` answers HTTP 200 on every poll throughout the ENTIRE finalize tail during a
  TC-1 run.
- TC-5: process VmPeak stays under `server.memory_cap_mb=8192` during the TC-1 drill, margin recorded in
  `reports/perf-budgets.md`.
- TC-6: the existing opt-in live test either passes with `xfail` removed, or stays honestly `xfail` with
  an accurate, updated reason — never a loosened assertion.
- TC-7: the full 8-journey browser-qa/replay pass is the LAST product-code-adjacent event (mtime-checked)
  AND every one of J-01, J-03, J-04, J-05, J-06, J-07, J-08, J-09 has at least one executed row in the
  merged results — not merely sequencing holding while rows are missing (audit F3, 2 consecutive rounds).
- TC-8: each Required-still-passing journey's golden replay script is scored by reading its own JSON
  content (asserting a new row/testid), not page-wide text a persisted history panel could already
  satisfy.
- TC-9: J-04's browser-qa row is real and executed this round — not `DEFERRED-BUDGET` or missing (2
  consecutive rounds at zero rows per audit F3).
- TC-10: `git diff` over `config.yaml`, `host-guard.env`, `scripts/start-backend.sh`, `scripts/dev.sh` is
  EMPTY; launch banners still report `memory_cap_mb=8192`/`malloc_arena_max=2` unchanged.
- TC-11: a genuine non-memory exception injected inside either newly-bounded loop's own new code still
  reaches a terminal run status honestly; a `MemoryError` injected at the same site is caught by the
  existing stop-loop + `_release_process_memory()` + honest-partial-report convention.

## Notes for the developer / downstream agents

- This is the FOURTH consecutive ESCALATE round. Required-still-passing set is WIDENED this round: J-01,
  J-03, J-04, J-06, J-08, J-09 must each produce a real executed lane row (deterministic replay content
  check, or LLM browser-qa fallback) — none may end `DEFERRED-BUDGET` or missing. J-04 in particular has
  zero executed rows for 2 consecutive rounds (audit F3) and is explicitly named as non-negotiable this
  round.
- Do not start a second data job while one is still finishing during TESTING REQUIREMENTS drills.
- Environment: before running tests or any command that writes temp files, `export
  TMPDIR="/home/dennis-chan/.cache/iad/iad.goal-ops-harde-0c6800fc.91778"
  TMP="/home/dennis-chan/.cache/iad/iad.goal-ops-harde-0c6800fc.91778"
  TEMP="/home/dennis-chan/.cache/iad/iad.goal-ops-harde-0c6800fc.91778"`.
- Heavy compute (the live TC-1 drills) must launch only via `scripts/start-backend.sh` (never a bare
  `uvicorn`/python invocation) so AG-10's host caps apply.
- Out of scope, carried untouched: Regime Lab's separate 8192MB-cap hit; B3
  (`_membership_bars_are_forward_only` compensating-removal weakness); F2 (golden's page-wide-text
  scoping gap — needs a frontend testid, excluded since `Frontend Present: no`); the shared
  ingest-vs-request warm-in-progress flag; J-09's background-worker visibility gap; health-poll ≤2s
  ceiling re-measurement (folds into required-still-passing verification, no fix attempted); any
  `memory_cap_mb`/`malloc_arena_max`/host-guard VALUE change.

## Alignment Check

- Advances `docs/goal.md`'s J-05 ("Aggregates are precomputed at ingest, never on the fly") and J-07
  ("Heavy aggregates never take the service down") Must-have journeys directly — this iteration is the
  continuation of a single, already-scoped risky change (iter-48's own precedent), not new scope.
  No goal.md drift detected; the phase spec's OUT OF SCOPE section is consistent with goal.md's Loop
  mechanics ("one risky change per iteration").
- No anti-goal is implicated by this iteration's change shape: no evidence/proven-language surface is
  touched (AG-1/AG-4/AG-6 not in play — J-05/J-07 carry no Evidence Claims per goal.md's Loop mechanics),
  no ingest source changes (AG-9), and AG-10's cap VALUES are explicitly frozen (TC-10).
