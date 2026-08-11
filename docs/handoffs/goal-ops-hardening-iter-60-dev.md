# goal-ops-hardening-iter-60 Dev Handoff

**Phase:** goal-ops-hardening-iter-60
**Date:** 2026-08-11
**Agent:** developer
**Status:** complete

## What Was Built

- **`compute_regime_lab`'s pre-loop prologue is now isolate-and-continue too**
  (`apps/backend/app/engine/research.py`). Before this iteration, the horizon list
  (`list(wf.horizons)`), the label vocabulary (`list(cfg.regime.labels)`), and (for the episodes view)
  the run-ordinal index (`_run_position_index`, a real `scanner_runs` DB read) were resolved OUTSIDE the
  per-horizon `try`/`except` the loop body already has — a failure there propagated as an unhandled
  exception straight to `GET /api/research/regime-lab` (a 500). The three reads now sit inside their own
  `try`, and on ANY failure (`except Exception`, mirroring the loop body's own broad catch — AG-8), every
  configured horizon degrades honestly via the SAME `_degrade_regime_lab_horizon` helper the loop body
  already calls (`status: "unavailable"`, `n: 0`, `low_sample: True`, `mean_return`/`mean_max_drawdown:
  None` — never fabricated), the per-horizon loop body is skipped entirely (nothing trustworthy left to
  iterate with), and the function returns its normal payload shape with `regime_lab_status:
  "unavailable"` set — never a raw exception. The top-level `horizons`/`regime_labels` payload fields
  still echo the full configured lists (re-derived directly from config in the except branch, not from
  the possibly-unset try-block locals), so a consumer sees the same vocabulary either way. Logged via
  `logger.exception(...)` with "isolate-and-continue" in the message, matching the loop body's own
  convention.
- **Degraded Regime-Lab cells no longer show a misleading `n=0` drill-down link**
  (`apps/frontend/components/sample-link.tsx`, `apps/frontend/app/research/_labs.tsx`,
  `apps/frontend/lib/regime-cell-status.ts`). `SampleLink` gained a new, additive, optional `unavailable`
  prop (default `false` — every pre-existing call site across the codebase that never passes it renders
  byte-unchanged). When `true`, it renders a plain, visible "Unavailable" indicator (an `AlertTriangle`
  icon + the word "Unavailable", `text-text-faint`, non-tooltip-only — readable without hovering) instead
  of the active `Link`-wrapped `n=…` chip, so no `data-testid="sample-link"` element is rendered for that
  cell. `RegimeReturnCell` passes `unavailable={isRegimeCellUnavailable(cell)}` — a new one-line pure
  predicate (`cell.status === "unavailable"`) extracted into `lib/regime-cell-status.ts` specifically so
  the degrade-vs-not decision is unit-testable under this frontend's existing `node`-native-TS-stripping
  test convention (no React/DOM rendering harness exists in this project — see `lib/availability-empty-
  state.ts` for the established precedent this mirrors). A genuine low-sample cell (`low_sample: true`,
  `status` absent) is completely unaffected — `unavailable` resolves `false`, so `SampleLink` takes its
  original branch untouched.
- **`replay-lane.sh`'s partition loop now closes the target-journey lane-coverage gap**
  (`scripts/automation/lib/replay-lane.sh` — hardlinked 1:1 with
  `incredible_auto_dev/scripts/automation/lib/replay-lane.sh`, same file, one edit). Previously
  `replay_lane_partition_and_verify` looped ONLY `REQUIRED_JOURNEYS` when deciding what to route into the
  deterministic replay set (`R_REPLAY`) — a `TARGET_JOURNEYS` entry's on-file golden sat unexecuted every
  run, so `merge_ui_test_results.py --target` could only ever FLAG the journey as having zero rows
  (BLOCKED), never actually close the gap by replaying it (this is exactly what happened to J-05/J-07 in
  iter-59: both passed LIVE but never got a lane row). Fix: the lint pass now covers the union of
  `REQUIRED_JOURNEYS` and `TARGET_JOURNEYS` (deduped), and a second loop routes every `TARGET_JOURNEYS`
  entry with an on-file, lint-valid golden into `R_REPLAY` too (skipping one already routed by the
  required-journeys loop, so a journey listed in both sets is never double-entered) — it is then ACTUALLY
  REPLAYED by `demo_runner.py --mode verify` in the SAME invocation as the required set, producing a real
  row in `$REGRESSION_RESULTS`. A target-only journey with a missing or lint-invalid golden is
  deliberately left OFF `R_LLM` — that set feeds `replay_lane_llm_regression_set`'s "required-still-
  passing regression re-check" LLM dispatch, a different semantic from "this iteration's own Target
  journey", which `goal-iter-lean.sh` already covers independently (`_llm_set="$TARGET_JOURNEYS
  $(replay_lane_llm_regression_set)"`, line ~782 — confirmed by direct read before deciding not to touch
  `R_LLM`); an invalid target golden is still quarantined (`*.json.invalid`) for hygiene, same as a
  required journey's. Both new `TARGET_JOURNEYS` reads use `${TARGET_JOURNEYS:-}` (never a bare
  reference) and end their pipelines with `|| true` — TARGET_JOURNEYS is legitimately unset or empty on
  most callers/iterations, and this whole file runs under `set -e -o pipefail`, so an unguarded `grep`
  matching zero lines would otherwise silently kill the caller (the exact class of bug the file's own
  `replay_lane_spec_journeys` comment already documents — I hit this live while testing my own change,
  see "Tests Run" below).
- **`journey-scripts/J-01.json`: diagnosed, NOT changed — verified genuinely passing, deterministically,
  4 times.** Investigated whether step 9's `zero-work-note` assertion (or an earlier step) had an actual
  defect. Found none: the current committed working DB (the same one this whole session ingests into) has
  all 19 trading days in `2026-05-02..2026-05-29` already snapshotted (confirmed via a live `GET
  /api/runs` query), so the golden's first backfill genuinely IS a zero-work run against today's DB state
  — its assumptions are correct as written. I ran a real deterministic replay of J-01 against live
  services FOUR separate times this pass (see "Tests Run"): all four passed cleanly, 16/16 steps, no LLM-
  lane override needed, with opened (not just hashed) evidence screenshots showing real, non-blank
  content (the `/scanner-runs/…` detail page for `2026-05-29`, populated Market Regime / breadth /
  candidate-count panels). The prior iterations' claim that this golden was "rewritten" was false (`git
  diff --stat` over the path is empty, confirmed again this pass) — but the underlying behavior it
  exercises already works correctly against the current DB. I deliberately did NOT force a content change
  into an already-correct file (the phase spec's own guidance: "Do not just re-annotate the script as
  'rewritten' — verify the fix against a live replay run before commit" — I did the verification, found
  nothing broken, and am reporting that honestly rather than inventing a diff). My best-evidence
  hypothesis for the ORIGINAL iter-59 failure: the deterministic replay likely ran during that session's
  own concurrent heavy compute (J-07's forward-aggregate warm), and the backfill job's async completion
  didn't reach `status: "ok"` inside step 9's ~20s auto-retry window (`_check_expect`'s Playwright
  `wait_for(state="visible", timeout=…)`) under that resource contention — not a defect in the golden's
  assertions themselves, which are logically sound against the DB state both then and now.

## Files Changed

- `apps/backend/app/engine/research.py` -- `compute_regime_lab`'s prologue (`horizons`/`labels`/
  `run_position` reads) wrapped in a `try`/`except Exception`, degrading every configured horizon
  honestly via `_degrade_regime_lab_horizon` on failure instead of propagating an unhandled exception.
- `apps/backend/tests/test_regime_lab.py` -- new test
  `test_compute_regime_lab_prologue_failure_degrades_honestly` (TC-4): monkeypatches
  `research._run_position_index` to raise unconditionally, proves the VIEW_EPISODES call degrades every
  configured horizon honestly (never raises) while a VIEW_POOLED control run (which never calls that
  function) is unaffected — proving the assertions exercise the faulted path, not a globally-broken
  function.
- `apps/frontend/components/sample-link.tsx` -- `SampleLink` gained the additive, optional `unavailable`
  prop (default `false`); renders a plain "Unavailable" indicator instead of the active link/chip when
  `true`.
- `apps/frontend/app/research/_labs.tsx` -- `RegimeReturnCell`'s `SampleLink` call now passes
  `unavailable={isRegimeCellUnavailable(cell)}`; new import of `isRegimeCellUnavailable` from
  `@/lib/regime-cell-status`.
- `apps/frontend/lib/regime-cell-status.ts` -- new file: `isRegimeCellUnavailable(cell)`, the single pure
  predicate (`cell.status === "unavailable"`) both the component and its unit test share.
- `apps/frontend/lib/regime-cell-status.test.ts` -- new file, 3 checks (TC-5/TC-6): a degraded cell is
  reported unavailable; a genuine low-sample cell (status absent) is not; a clean well-sampled cell is
  not.
- `scripts/automation/lib/replay-lane.sh` (== `incredible_auto_dev/scripts/automation/lib/replay-lane.sh`
  — hardlinked, one file) -- `replay_lane_partition_and_verify`'s lint pass now covers `REQUIRED_JOURNEYS`
  ∪ `TARGET_JOURNEYS`; a new loop routes `TARGET_JOURNEYS` entries with an on-file, lint-valid golden
  into `R_REPLAY` (deduped against journeys already routed by the required-journeys loop); invalid target
  goldens are quarantined but not routed to `R_LLM`; both new `TARGET_JOURNEYS` reads are `set -u`-safe
  (`${TARGET_JOURNEYS:-}`) and pipefail-safe (`|| true`).
- `tests/automation/test-replay-lane.sh` (== `incredible_auto_dev/tests/automation/test-replay-lane.sh` —
  hardlinked, one file) -- `run_partition` gained an optional `$2` (TARGET_JOURNEYS) parameter, default
  unset (every pre-existing call site is byte-unchanged); 7 new scenarios (3b/3c/3d): a target-only
  journey with a valid golden joins `R_REPLAY` and is actually replayed (real row in the raw results
  file); a lint-invalid target-only golden is quarantined but not added to `R_LLM`; a target-only journey
  with no golden at all is left completely untouched; `TARGET_JOURNEYS` never being assigned at all does
  not crash the lane (`set -u` safety — the common case); a journey in BOTH required and target sets is
  never double-entered. Header "Covered:" comment updated to describe the new coverage.
- `runs/goal-session-ops-hardening/journey-scripts/J-01.json` -- **unchanged** (see "What Was Built"
  above — diagnosed and live-verified passing 4x, no defect found, no edit made).
- `docs/handoffs/goal-ops-hardening-iter-60-dev.md` -- this file.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/<file>.py -v` (TMPDIR set per the
coordinator's env note).

| Target | Result |
|---|---|
| `tests/test_regime_lab.py` (full file, 37 tests) | **37 passed** (~9s) — includes the new prologue-failure test (TC-4) and all 36 pre-existing tests (no regression). |
| `tests/test_samples.py` (Regime-Lab cohort count-coherence, shares the same builders) | **18 passed** (3.32s) — no regression. |
| `tests/test_api_research.py -k regime_lab` (HTTP-layer byte-identity/shape tests) | **NOT re-run to completion.** This file's `loaded_engine` fixture is documented in the iter-59 dev handoff as costing **65+ minutes** on this host regardless of `-k` filtering (session-scoped fixture, paid once per invocation). I started it in the background, confirmed via `ps` it was genuinely CPU-bound (not hung) at the 5-minute mark, then killed it deliberately rather than block this dispatch — my change to the prologue is purely additive on the success path (the `try` body is byte-identical to the pre-iter-60 code; only a NEW `except` branch was added, never reached on a clean run), so the byte-identity contract this file tests is structurally unaffected. Substituted with direct live verification instead (see below). |
| `npx tsc --noEmit` (frontend) | Clean, zero errors. |
| `node`/`npx tsx lib/regime-cell-status.test.ts` | **3 passed.** (This dev box's Node lacks native TS-stripping — same pre-existing, documented limitation as every other `lib/*.test.ts` file in this project; `npx tsx` is the local fallback.) |
| All 11 other pre-existing `apps/frontend/lib/*.test.ts` files | **All pass**, run individually — no regression from the `sample-link.tsx`/`_labs.tsx` changes. |
| `tests/automation/test-replay-lane.sh` (via `incredible_auto_dev/tests/automation/test-replay-lane.sh` — must be run from a real, non-symlinked `scripts/` directory; the `trendora/scripts` symlink breaks the sandbox's `cp -r`) | **75 passed, 0 failed** (68 pre-existing + 7 new TARGET_JOURNEYS scenarios). |
| `tests/automation/test-replay-lane-full.sh` | **24 passed, 0 failed** — no regression (full-pipeline caller path). |
| `tests/automation/test-goal-parallel-bqa.sh` | **102 passed, 1 failed.** The one failure (`L: merged results — canary PASS overrides, voided journey stays SKIP, headline PASS`) is **pre-existing, unrelated to this iteration's changes** — confirmed by `git stash`-ing all my changes and re-running: it fails identically on the untouched baseline. Not touched (out of scope; not named by this iteration's IN SCOPE list). |

### Live verification (backend + frontend running via `scripts/dev.sh`, ports 8255/3255)

- `GET /api/research/regime-lab` — HTTP 200, real data (6 labels, 10 deciles, 5 horizons, e.g. horizon=1
  `n=518, mean_return=0.00275`), no `regime_lab_status` (clean compute, unaffected by the prologue
  change).
- `GET /api/research/regime-lab?view=pooled` — 200. `?as_of=2026-05-29` — 200. `?view=nope` — **422**
  (unknown-view validation, which sits BEFORE my new `try`, confirmed unaffected).
- `GET /research/regime-lab` (frontend page) — 200. `GET /data` — 200.
- **`journey-scripts/J-01.json` replayed via the REAL production `replay_lane_partition_and_verify` path**
  (not just a raw `demo_runner.py` CLI call) — **4 separate clean PASS runs** across this session
  (including one immediately after a full `scripts/dev.sh` restart): 16/16 steps, `Browser QA Verdict:
  PASS`, evidence screenshots opened and confirmed non-blank each time (real
  `/scanner-runs/…` detail content, not a placeholder). All diagnostic artifacts (`reports/phase-*-
  j01check-*`, `reports/qa/*-j01check-evidence/`, `*-j01final-*`) were cleaned up afterward — `git status`
  confirms nothing left behind.

## Pre-handoff verification

- [x] **Service startup works:** `scripts/dev.sh` started cleanly (backend healthy in 1s, frontend 200),
  stopped, and restarted — the second `scripts/dev.sh` invocation correctly killed the FIRST run's
  processes (including uvicorn's `--reload` worker, which re-execs via `multiprocessing.spawn` and does
  **not** contain the string "uvicorn" in its own `/proc/<pid>/cmdline` — a manual `pkill -f
  "uvicorn main:app.*8255"` I ran later in this session missed that exact process for this reason; only
  `scripts/dev.sh`'s own port-based `lsof -ti :$PORT` / `fuser -k` cleanup reliably catches it, which it
  did, both at restart and when I shut everything down at the end via explicit PID kills after diagnosing
  the gap with `lsof`/`ps`). No port conflicts on either restart; `ss` confirmed both ports fully released
  after final shutdown.
- N/A: no live external network/paid-provider integration touched this iteration (`replay-lane.sh`
  replays against the local `demo_runner.py` + committed-seed DB only, per AG-9).
- N/A: no new dependency, no native binary, no schema migration this iteration.

## Known Issues

- **`test_api_research.py -k regime_lab` was not re-run to completion** (65+ minute cost, documented in
  iter-59's own dev handoff). The reviewer/QA lane should re-run it with a generous time budget if a
  from-scratch HTTP-layer confirmation is wanted; the change it would verify (prologue-only, additive) is
  already covered at the compute layer (`test_regime_lab.py`, 37/37 passing) and by direct live `curl`
  verification of the endpoint above.
- **A pre-existing, unrelated test failure exists in `test-goal-parallel-bqa.sh` scenario L**
  ("merged results — canary PASS overrides, voided journey stays SKIP, headline PASS") — confirmed via
  `git stash` to be present on the untouched baseline too, not introduced by this iteration. Left
  untouched; not named by this iteration's IN SCOPE list.
- **TC-9's opportunistic "quiet machine" cold-load timing measurement was not captured by this dev
  pass.** It requires an idle backend with no concurrent heavy job at the moment of measurement and is
  framed by the phase spec as a QA/browser-pass artifact (append to `reports/perf-budgets.md`); left for
  the browser-qa-agent's pass, which naturally times a cold `/research/regime-lab` load anyway while
  producing J-05/J-07's walkthrough evidence.
- **No live capture of an actual DEGRADED Regime-Lab cell was taken this pass** (would require restarting
  the backend with `TRENDORA_FAULT_INJECT_MEMORY_ERROR=regime_lab` armed and hitting a guaranteed cache-
  miss key, then restarting clean again). The backend-level behavior is proven deterministically by the
  new unit test (TC-4) and the pre-existing per-horizon isolate-and-continue tests; the frontend-level
  decision is proven by the new `regime-cell-status.test.ts` (TC-5/TC-6). A live visual capture of the
  "Unavailable" indicator replacing the old `n=0` chip is left to the browser-qa-agent's pass, consistent
  with iter-59's own TC-11 evidence-capture precedent (dev hands the lane a pre-armed backend; QA/browser
  performs and screenshots the capture).
