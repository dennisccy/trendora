# goal-lint report — docs/goal.md

Run: 2026-08-20 · deterministic exit: 0 · semantic findings: 3

## Deterministic lint (goal_lint.py)
clean (exit 0, no output)

## Semantic findings
### Unobservable-by-browser acceptance (deliberate, watch) — J-09
> - **Walkthrough:** waived — deliberately backend-only (no UI surface changes); the
- **Problem:** J-09 (owner, 2026-08-20) is the file's only journey whose acceptance a browser test cannot see — evidence lives in `/proc/<pid>/status` VmPeak and `reports/perf-budgets.md`, not on a page. The waiver is stated explicitly in the journey, but the goal-evaluator and browser-qa lanes have never processed a waived-walkthrough journey in this session; watch the first J-09 iteration for a lane mis-scoring the missing browser evidence.
- **Suggested rewrite:** none — the deviation is the point (a resource journey after the 2026-08-20 freeze incident). If the evaluator mis-handles the waiver, tighten the wording to "browser-qa: SKIP for this journey" rather than restructuring.

### Step relies on a breadcrumb, not a named script — J-09 step 2
> 2. Re-run the standing-warm measurement that recorded 4,837,420 kB VmPeak (the
- **Problem:** the step identifies the measurement by its recorded figure and description rather than a script path; the implementer must locate the drill via `reports/perf-budgets.md` (grep for `4,837,420`). Executable, but with one lookup of indirection.
- **Suggested rewrite:** once the slice identifies the concrete drill entrypoint, pin it into the step (e.g. "run `<script>` as recorded at `reports/perf-budgets.md:<line>`"). Advisory — the figure is grep-findable today.

### Interaction watch: cache shrink vs finalize-tail timing — J-09 × J-05/J-06
> 1. In `config.yaml`, change `database.pragmas.cache_size` from `-262144` to `-65536`
- **Problem:** a 256→64 MB per-connection page cache may slow the ingest finalize tail (J-05/J-06 drive it three times through the UI). No committed page-load budget covers the tail, and J-09's byte-identity step protects correctness — but if any finalize-tail wall-clock figure in `reports/perf-budgets.md` is treated as a budget, the J-09 slice must re-measure and append it rather than let an old figure stand as an implicit gate.
- **Suggested rewrite:** none needed in goal.md — J-09 step 3 already mandates dated append-only re-measurement. Noting so the slice does not skip the tail re-measurement.

## Summary
Structurally clean; the 2026-08-20 owner additions (J-09 resource-fit journey, the Host
resource-fit Constraints bullet, the build-order insert) are concrete, checkable, and
consistent with AG-8/AG-10 and the existing journeys. Highest-impact watch item: the first
J-09 iteration is the file's first walkthrough-waived journey — confirm the evaluator and
browser-qa lanes honor the stated waiver instead of scoring the absent browser evidence.
