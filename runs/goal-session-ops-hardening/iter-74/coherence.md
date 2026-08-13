# Iteration 74 — Coherence Audit

**Iteration:** goal-ops-hardening-iter-74
**Date:** 2026-08-13
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Data Contract check

Reviewable diff scope this iteration: `apps/backend/tests/test_start_backend_script.py` (+361
lines), `docs/goal.md` (+16/-3 lines), plus `reports/perf-budgets.md` (out-of-scope harness/report
artifact per the noise-exclusion rules, but its Data Contract row is checked below since the
iteration's whole purpose is writing to it). `blueprint.md` itself changed by 3 lines (a top-of-file
narrative paragraph + one sentence appended to the "Page performance budgets" row's Notes column) —
confirmed no computing-module or endpoint column changed.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Page performance budgets / VmPeak margin (`reports/perf-budgets.md`) | OK | Blueprint row still reads "N/A — a measurement artifact, not a served runtime value," canonical artifact `reports/perf-budgets.md` unchanged; `blueprint.md:18` (Data Contract table) has the module/endpoint columns byte-identical to iter-73, only the Notes prose gained one sentence. |
| `_refresh_ingest_aggregates` finalize-tail phase timers (`app/engine/data_manager.py`) | OK — read only, not recomputed | `apps/backend/tests/test_start_backend_script.py:82-104` (`_parse_phase_timing_lines`) only regex-parses the log lines that module already emits; no new `logger.info` call, no edit to `data_manager.py` in this diff at all (`git diff --stat` shows only the test file and `docs/goal.md` touched in reviewable scope). |
| `_MemSampler` VmPeak samples (`apps/backend/tests/test_start_backend_script.py`, pre-existing) | OK — read only, not recomputed | `test_start_backend_script.py:107-118` (`_vmpeak_at`) reads `mem.samples`/`mem.peak('VmPeak')` from the SAME `_MemSampler` instance the sibling iter-49/73 drills already use (`test_start_backend_script.py:299-343`); no second sampler class, no second `/proc` reader. |
| Ground-truth DB size / `rebuild` range behavior (`docs/goal.md`) | OK — documentation, not an app-served value | `docs/goal.md:400-417`; not a UI-displayed value, not in the Data Contract table — a factual engineering-appendix correction, matching the spec's own "Blueprint conformance" note that this is ordinary documentation work. |

No new function recomputes a value that already has a canonical producer, and no new UI surface
fetches a registered value from a non-canonical source — there is no new UI surface at all in this
iteration (`Frontend Present: no`, confirmed: no `apps/frontend/**` paths in the diff). The new
`_join_phase_vmpeak`/`_parse_phase_timing_lines`/`_vmpeak_at` functions are test-only telemetry
plumbing that assembles a report addendum; they do not serve a runtime value to any page or API
consumer, so they are outside Data Contract scope by the blueprint's own definition of that row.

## Information Architecture check

No new page, route, or nav entry. The diff touches zero files under `apps/frontend/`.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| J-07 (heavy-aggregate availability) | OK — no change | `runs/goal-session-ops-hardening/state/blueprint.md:412` (IA "Feature / journey homes" table): J-07's home is still "global readiness badge (top bar, every page) + `/backtest`" — this iteration adds no page/route/nav entry; confirmed no `apps/frontend/components/sidebar.tsx` or router changes in the diff. |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- Untracked empty file `=` (0 bytes) sits in the working tree (`git status --porcelain`), almost
  certainly shell debris from an unquoted `>=` redirect during this iteration's drill/test run. Not
  a Data Contract or Information Architecture matter (no displayed value, no route) — outside this
  gate's charter; flagging only so the developer/reviewer removes it before commit rather than it
  accumulating as unrelated repo clutter.
- The blueprint's own iter-74 narrative update and the "Page performance budgets" Notes-column
  sentence were verified byte-for-byte against the diff and match the spec's "Blueprint conformance"
  claim exactly (no row's computing module/endpoint changed) — no coherence follow-up needed.
