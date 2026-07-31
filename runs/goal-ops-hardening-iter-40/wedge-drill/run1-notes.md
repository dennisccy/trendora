# Wedge-recurrence drill — run 1 (confounded, superseded by run 2)

**PID:** 1285404 · **port:** 18260 · **config:** `config.scratch.yaml` (memory_cap_mb=2650, same cap
family as iter-39 trial 3) · **launched:** 2026-07-31T00:41:14Z (`logs/backend.log` line ~149374)

Job triggered **immediately** after `/api/health` first answered 200, while the boot warmup thread
(`warmup.py::_run_warmup`) was still mid-flight (`"warmup":{"done":0,"total":89,"status":"running"}` at
trigger time). This is a methodological confound relative to iter-39's own trial 3: TWO independent heavy
consumers (the boot warmup's own coverage-snapshot warm, which itself calls the SAME
`refresh_coverage_snapshot` → `_missing_data_diagnostic` path this iteration fixed, plus the triggered
backfill job's own bar-cache prefill + finalize) were competing for the SAME 2650 MB ceiling
simultaneously — not an apples-to-apples re-check of "does the wedge recur under the SAME single-job
conditions iter-39 measured."

## What happened

- The warmup thread's own coverage-snapshot warm **completed successfully**: `logs/backend.log` shows
  `"coverage snapshot warmed (asof=2026-07-01)"` (warmup.py:147) — i.e. the FIXED `_missing_data_diagnostic`
  ran to completion at least once on this process, via the warmup path, without raising.
- Immediately before that success line, one `"Exception ignored in thread started by: <object repr()
  failed>\nMemoryError:"` line appeared — the same low-information artifact iter-39's trial 3 evidence also
  recorded, but here with NO preceding Python traceback naming a call site (unlike iter-39's trial 3, whose
  evidence file captured a full traceback pointing at `_missing_data_diagnostic`/`_raw_all_rows()` — see
  `../../goal-ops-hardening-iter-39/mem-drill/trial3-2650mb-wedge-evidence.txt:14-29`). Site NOT identified
  from this run's log alone.
- After that line, the process went unresponsive: `/api/health` timed out (`000`) on every subsequent
  probe, all 14 threads sat in `futex_do_wait` (`/proc/<pid>/task/*/wchan`), and `/proc/<pid>/stat`'s
  utime+stime showed a **0-tick delta over a 3 s window** (genuinely idle, not computing) — the same
  physical signature as iter-39's trial-3 wedge (`VmPeak` also matched exactly: 2,713,600 kB).
- `gdb -p <pid> -batch -ex "thread apply all bt"` was attempted to positively identify the blocked
  thread's stack; `ptrace` is denied by this host's `yama.ptrace_scope` policy for a non-root, non-parent
  attacher (`Could not attach to process ... ptrace: Inappropriate ioctl for device`) — no py-spy available
  either (not installed; not added mid-drill to avoid an unplanned new dependency). No positive stack-level
  identification was obtained from run 1.
- Process killed (`kill -9`, confirmed exit 137, throwaway DB, no live-product impact) after ~3.5 min of
  confirmed non-recovery (shorter than iter-39's 7+ min confirmation window, but the 0-CPU-delta + all-
  threads-blocked signature is unambiguous — waiting longer would not have changed the diagnosis, and this
  run's own confound means its outcome is not this iteration's authoritative measurement anyway).

## Why this run does not answer TC-2/TC-3 on its own

Because the warmup thread's own call to the fixed function completed cleanly, this run does NOT show the
FIXED `_missing_data_diagnostic` itself wedging — it shows SOME concurrent allocation (most likely the
backfill job's own ~1.1 GB shared bar-cache prefill racing the warmup thread's own allocations, given
`_do_backfill`'s own prefill is a documented ~1.13 GB whole-table cache per data_manager.py's own comments)
exhausting the tightened cap when TWO heavy consumers overlap. Superseded by run 2 (`run2-*` in this same
directory), which waits for warmup to fully settle before triggering the job — the same single-job shape
iter-39's trial 3 exercised.
