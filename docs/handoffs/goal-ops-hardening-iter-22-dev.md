# goal-ops-hardening-iter-22 Dev Handoff

**Phase:** goal-ops-hardening-iter-22
**Date:** 2026-07-25
**Agent:** developer
**Status:** complete

## What Was Built

Nothing — this is a zero-product-diff, evidence-consolidation iteration per the spec's own framing
("Re-score J-06/J-07 against the owner's BCW budget amendment, zero code changes"). The deliverable is (1) an
independent re-verification of the amendment's iter-20 citation, (2) one fresh, iter-22-dated single-BCW
live measurement (`GET /api/backtest?as_of=2026-07-21` → poll → VmPeak capture), recorded in a new
"Iteration 22" section in `reports/perf-budgets.md`, and (3) this handoff. No backend or frontend source file
was created, edited, or deleted.

**Explicit statement (TC-11): zero product source files changed this iteration.** Confirmed under
"Verification" below.

## TL;DR — the fresh measurement did NOT fully cross

The fresh BCW re-trigger succeeded (I did not fall back to citation-only) and is fully instrumented, but it
surfaced a real, honest finding rather than a clean pass: **3 of the 4 measured sub-requirements passed
(trigger latency, per-sample latency ceilings, VmPeak margin), but the BCW's completion time was 68.79 s —
8.79 s (14.6 %) over the amendment's 60 s window bound.** I am reporting this plainly rather than rounding it
away, per this session's own iter-20 meta-lesson ("STALLED is the honest verdict even after real progress")
which the spec itself cites. Whether this moves J-06/J-07 to `passing`, keeps them `partial`, or triggers the
spec's own pre-written "holding spec" contingency is the evaluator's/next-decomposer's call, not mine — see
`reports/perf-budgets.md` § "Iteration 22" for the full instrumented evidence.

## Files Changed

- `reports/perf-budgets.md` -- appended a new "## Iteration 22" section (after the existing "OWNER BUDGET
  AMENDMENT" section, which — like "Iteration 20" — was left untouched, per the spec's explicit instruction).
- `runs/goal-ops-hardening-iter-22/bcw-measure.csv` -- raw 29-row (1 trigger + 28 poll) CSV for the official
  measurement (new).
- `runs/goal-ops-hardening-iter-22/drain-monitor.csv` and `drain-status.log` -- raw data for the incidental
  5-concurrent episode (new; disclosed, not the official citation — see "Investigation" below).
- `docs/handoffs/goal-ops-hardening-iter-22-dev.md` -- this handoff (new).
- `runs/goal-ops-hardening-iter-22/status.json` -- `current_step` updated to `dev_complete`.
- Nothing under `apps/backend/` or `apps/frontend/`.

## Investigation — an honest account of how the measurement was actually obtained

I want to be transparent about a mistake in my own methodology, because it produced a real (if incidental)
finding and because it explains why the official measurement needed a backend restart mid-iteration.

**What happened.** To find a historical `as_of` date not yet `"ready"` under the current `dataset_version`
(IN SCOPE's own suggested first step), I checked 5 candidate dates in a loop
(`2026-07-08`, `2026-07-09`, `2026-05-15`, `2026-06-15`, `2026-04-15`) via plain `GET /api/backtest?as_of=<d>`.
I had read `backtest.py`'s route before doing this and knew the historical branch calls
`ensure_historical_forward_aggregates_dispatched` whenever `evidence_status != "ready"` — but I underestimated
that this fires **independently for every distinct date**, because the single-flight guard
(`_HIST_DISPATCH_LOCK` / `_HIST_DISPATCH_INFLIGHT`, `forward_testing.py:1201-1202`) is keyed per
`(asof_key, dataset_version)`, not global. All 5 dates were simultaneously not-`"ready"` (the dataset_version
had advanced past them since iter-20/21), so all 5 GETs dispatched 5 independent background computes.

**What I observed.** I monitored this for over 180 s (`runs/goal-ops-hardening-iter-22/drain-monitor.csv` /
`drain-status.log`) rather than silently discarding it. Full findings are in `reports/perf-budgets.md` §
"Incidental finding" — in short: the service never went down (100 % HTTP 200, `readiness: ready` throughout,
no exception logged), but `VmPeak` climbed to and plateaued at 6,291,424 kB — **32 kB short of the exact
6,291,456 kB `ulimit -v` cap** — and none of the 5 dates reached `"ready"` within the monitored window.

**What I did about it.** Rather than let a 6th, official trigger stack on top of this (which would have
measured "6 concurrent BCWs" and mislabeled it as "one BCW" — scientifically invalid against an amendment
whose numbers are explicitly single-BCW), I **gracefully restarted the backend**
(`SIGTERM` on the old PID → confirmed clean `INFO: Shutting down` / `INFO: Application shutdown complete.` in
`logs/backend.log`, no abrupt kill → relaunched via `scripts/start-backend.sh` only, per the coordinator's
operational note). This is explicitly **not** a `kill -9` disruptive-crash trigger and **not** a re-run of
TC-13/TC-14 (OUT OF SCOPE, binding "Do not redo") — it is ordinary measurement hygiene to undo my own
contamination, the same "backend restarted via `scripts/start-backend.sh`" pattern iter-20's own section
already uses before its measurements. Host-guard caps were re-verified live on the new PID (807942) via
`/proc` before proceeding. The partial cache rows the 5 stuck dispatches wrote (horizons `[1,5,10]` for 4
dates, `[1]` for the 5th) are harmless: incomplete-horizon-set rows never satisfy `"ready"`, so a future read
of those dates still correctly reports `"refreshing"` — no correctness risk, no cleanup required (the existing
cache-pruning-on-write behavior handles it on the next real dataset-version bump).

**Why I'm disclosing this at length.** It is the honest account of how the environment reached the state the
official measurement ran in, and the near-cap `VmPeak` observation is itself a genuine (if off-target) data
point about concurrent-BCW behavior that seemed worth recording rather than quietly erasing.

## (a) TC-1 — independent re-verification of the amendment's iter-20 citation

Read the amendment's "Why these numbers" section against the original "Iteration 20" section (not the
amendment's own restatement) line by line. **Confirmed accurate — no discrepancy:**

- `/backtest` worst during a BCW: source says "6.32 s (t=10 s)" + "3.40 s (t=20 s), 3.08 s (t=30 s)"; amendment
  cites the same 6.32/3.40/3.08 s → ceiling 8.0 s. All three within ceiling (worst-case margin 1.68 s / 21 %).
- `/api/health` worst during a BCW: source says "max 1.60 s (0.64/0.90/1.01/1.60 s on 4 of 16 samples)";
  amendment cites the same 1.60 s → ceiling 2.0 s. Within ceiling (margin 0.40 s / 20 %).
- BCW duration: source says "~30 s later ... serves `ready`"; amendment cites the same ~30 s → bound 60 s.
  Within bound for that specific iter-20 instance.

The amendment's citation is faithful to its source in every figure. Full table in
`reports/perf-budgets.md` § "Iteration 22" (a).

## (b) The fresh, iter-22-dated single-BCW measurement

Trigger date: `2026-07-21` (selected read-only from `scanner_runs`, confirmed zero `forward_aggregate_cache`
rows at the current `dataset_version` `r1865-f3954530` before the trigger GET — so the trigger GET is
simultaneously the pre-check and the official dispatch, per TC-2's literal wording). Full instrumented data,
per-TC results table, and the raw CSVs are in `reports/perf-budgets.md` § "Iteration 22" (b) — summarized:

| TC | Result |
|---|---|
| TC-2 (trigger < 1.5 s, dispatches) | **PASS** — 87.9 ms client / 75.87 ms server, `ensure_loop_ms` 2.00 ms |
| TC-3 (every sample ≤ 8.0 s / ≤ 2.0 s, all HTTP 200) | **PASS** — max 7.119 s `/backtest`, max 0.253 s `/api/health`, 28/28 HTTP 200 both endpoints, `readiness: ready` throughout |
| TC-4 (window ≤ 60 s) | **FAIL** — 68.79 s (trigger `06:53:23.474051Z` → horizon=60 commit / served-ready `06:54:32.266617Z`), +8.79 s / +14.6 % over |
| TC-5 (`VmPeak` + margin) | **PASS** — flat 2,631,612 kB start-to-finish (zero incremental growth), margin 3,659,844 kB ≈ 3574 MB (58.2 % headroom) under the 6144 MB `memory_cap_mb` cap |
| TC-14/goal (served == stored, byte-identical) | **PASS** — all 5 horizons' `evidence_by_horizon` values and `evidence_generated_at` exactly match the stored `forward_aggregate_cache` rows (deep-equality checked) |

**On the TC-4 breach specifically:** the five per-horizon cache commits are evenly spaced 13.7–14.3 s apart
(`walk_forward.horizons: [1, 5, 10, 20, 60]`, 5 horizons, unchanged config) — a structural ~14 s/horizon
cadence, not a noisy outlier. I did not attempt to root-cause *why* this run's per-horizon cost differs from
iter-20's single ~30 s example (that would drift toward the explicitly out-of-scope "technical mitigation for
the transient contention" investigation) — I verified the environment was clean when this ran (thermal
41–51 °C, well below any throttle threshold; loadavg 1.08–1.86, not elevated; fresh process, zero leftover
threads from the incidental episode) so I'm confident this is a genuine measurement, not a residual-
contamination artifact, but I'm not asserting a cause beyond what the timestamps show.

## Required-still-passing journeys (J-01, J-03, J-04, J-05, J-08)

Zero source changed, so there is no code-level reason for any to have regressed. I ran the one directly
adjacent targeted test file as a live behavioral sanity check (host-guard-confined, matching iter-21's exact
invocation):

```
cd apps/backend
taskset -c 0-3,8-11 env OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 NUMEXPR_NUM_THREADS=4 \
  .venv/bin/python -m pytest tests/test_forward_testing_serving_split.py -q
```

Result: **25 passed, 0 failed, in 3.55 s** — matches iter-20/iter-21's own count for this file exactly, no
drift. Golden-replay confirmation for J-01/J-03/J-05 and the LLM browser-qa lane for J-04/J-08 are the
reviewer/browser-qa pipeline stage's own tooling per this spec's Testing Requirements, not developer-invoked
for a zero-diff iteration — I did not independently drive a browser this iteration.

## Pre-handoff verification (developer.md checklist)

- **Service startup works:** satisfied incidentally by the methodology above — the backend was stopped
  gracefully and restarted via `scripts/start-backend.sh` mid-iteration (to get a clean measurement
  environment, see "Investigation"), came back with `readiness: ready` and `warmup: 89/89 done`, no port
  conflict (old PID fully exited before the new one bound port 8255), host-guard caps re-verified via `/proc`
  on the new PID. I did not additionally cycle the frontend — it stayed up and healthy (HTTP 200) throughout,
  untouched by anything this iteration did.
- **External integrations:** N/A — no new adapters/scrapers this iteration.
- **Native dependency binaries:** N/A — no new dependencies this iteration.

## Tests Run

```
cd apps/backend
taskset -c 0-3,8-11 env OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 NUMEXPR_NUM_THREADS=4 \
  .venv/bin/python -m pytest tests/test_forward_testing_serving_split.py -q
```
Result: **25 passed, 0 failed, in 3.55s.** No other test files run (zero source changes; no full-suite run,
per the standing "never run the full suite" instruction — 30-year fixture basis makes it ~10h). All
long-running commands (the BCW measurement scripts, the drain monitor) were launched via
`setsid nohup ... &` from a foreground call and polled with bounded sleep loops, per the coordinator's
operational note; no stray processes remained afterward (one self-inflicted stray polling loop from my own
monitoring script, caused by a `pgrep -f` pattern that matched its own invoking shell's command text — killed
and confirmed gone before writing this handoff).

## Verification (`git status` / `git diff` at completion — IN SCOPE requirement, TC-11)

```
$ git status --short --porcelain -- apps/backend apps/frontend
(no output)
$ git diff --stat -- apps/backend apps/frontend
(no output)
$ git ls-files apps/backend/data/trendora.db
(no output -- DB untracked, never committed; the measurement's DB writes do not appear in either check above)
```

Both empty. Zero files under `apps/backend/` or `apps/frontend/` changed, staged, or left untracked by this
iteration.

## Anti-goal checks (TC-12, TC-14 per iter spec numbering)

- **AG-9:** every request issued this iteration was a plain `GET` (`/api/backtest`, `/api/health`) or a
  read-only local `sqlite3`/Python DB query. No backfill/fetch/rebuild job was submitted (the fallback
  small-backfill path in IN SCOPE was not needed — `2026-07-21` was already not-`"ready"`). No live network
  call at any point.
- **AG-10:** the backend serving the official measurement (PID 807942) was launched exclusively via
  `scripts/start-backend.sh`; host-guard caps verified live via `/proc/807942/{status,limits,environ}`:
  `Cpus_allowed_list 0-3,8-11`, `Max address space 6442450944 bytes` (6144 MB), `MALLOC_ARENA_MAX=2`,
  `OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=4`. No bare `uvicorn` invocation at any point.
- **AG-3:** the served evidence for the fresh trigger date was spot-checked byte-identical (deep-equality) to
  the stored `forward_aggregate_cache` rows — see TC-14 above.

## Known Issues

- **TC-4 (BCW window ≤ 60 s) did not pass on this fresh measurement** — 68.79 s observed vs. the amendment's
  60 s bound, for the reasons and with the evidence detailed above. This is the one substantive open item this
  handoff surfaces; I have not attempted to resolve it (out of scope) or soften its reporting.
- The incidental 5-concurrent-dispatch episode (my own methodology error) pushed `VmPeak` to within 32 kB of
  the exact `ulimit -v` cap. Not a breach, not this iteration's scored scenario, but worth the next
  spec-writer's awareness if multi-date concurrent BCWs ever become an intentional test target.
- No code-level issues — there is no code change to have issues.
