# Goal Session ops-hardening — Lessons Learned

Append-only ledger of takeaways from prior iterations. The goal-evaluator
appends one entry per iteration; the goal-decomposer reads this file before
planning each iteration to avoid repeating known pitfalls.

Each entry should be 1-3 sentences capturing a non-obvious lesson — surprising
failures, regression triggers, or decisions that worked well. Avoid
restating the verdict (the evaluator-log.md already does that).

## iter-0 — 2026-07-19T15:19:32Z

**Verdict:** CONTINUE
**Lesson:** J-01's real blocker is NOT the obvious missing exclusion-reason schema but the
cadence gate: `_do_backfill` (`data_manager.py` ~:2496) filters every backfill through
`_cadence_allowed_dates`, and because `snapshot_cadence.daily_start` is `2026-06-01`, the exact
goal.md-suggested May 2026 range (and J-05's 2026-05-15 single-day date) both compute
`dates_total=0` and ingest nothing. So J-01 and J-05 share ONE root cause — "requested range
always wins" must land before either journey can even be exercised. Secondary: the iter-25 prose
in `reports/perf-budgets.md` claims `start-backend.sh` applies a `ulimit -v` cap, but the current
script applies none (confirmed by source read + `/proc/<pid>/environ`) — whoever builds J-04's
memory-cap enforcement must not assume that doc reflects reality.
**Applies to:** any iter touching `data_manager.py` `_do_backfill` / `_cadence_allowed_dates`
(build J-01's explicit-request override before J-05); any iter building J-04's logfile/memory-cap
layer in `scripts/start-backend.sh`.

## iter-1 — 2026-07-19T19:21:22Z

**Verdict:** CONTINUE
**Lesson:** A new persisted numeric-display field's honesty risk lives in its NOT-YET-COMPUTED and
mass-failure edges, not its happy path. The breakdown fields (`calendar_days` etc.) were exact on
completed backfills but (a) served a fabricated literal `0` on interrupted/job-start rows — because
`_create_run_record` serializes `_run_detail(prog)` while `prog` is still at dataclass defaults and
the orphan-sweep freezes that row without recomputing — and (b) `error_other = len(date_failures)`
silently under-counted past the 20-sample cap. Both are direct AG-3 hits; the browser-qa's exact
DOM reads found (a) and the audit found both, yet the reviewer rated (b) MINOR/out-of-scope and QA
did not act — so DO NOT rely on reviewer/QA alone to catch honesty edges on a new field. Fix
pattern: gate each field's serialization on "actually computed" (a sentinel like `calendar_days>0`)
and mirror the existing bounded-sample/`_total` split (`omitted`/`omitted_total`) for any count.
**Applies to:** any iter adding persisted/served numeric fields to `data_provider_runs` /
`JobProgress` / a run-summary or aggregate payload (J-05's `coverage_snapshot` finalize hooks next
cycle) — cover the interrupted/orphan-sweep and >sample-cap paths, not just the happy path.

## iter-2 — 2026-07-20T06:06:21Z

**Verdict:** CONTINUE
**Lesson:** Keying a served ingest-time cache on a LIVE dataset fingerprint (`coverage_snapshot`'s
`dataset_version` = `_membership_dataset_version`, embedding bar/symbol/run counts) means ANY
count-changing ingest silently invalidates EVERY cached row for every as-of — and if some ingest
kinds are (correctly, per scope) excluded from the refresh hook, the read path serves the
honest-empty all-zero sentinel for a fully-populated DB until a restart or backfill re-persists. Two
individually-correct decisions (exclude `fetch`/`expand` from the finalize hook; key on a fingerprint
for byte-identity) compose into an emergent AG-3-class false-zero on the DEFAULT `/data` view (audit
B1, live-reproduced in UT-07 when a fetch landed 1 bar). The offline "fetch is always zero-work"
assumption also proved false — the committed fixture had a landable 2026-07-17 bar.
**Applies to:** any iter warming/serving an ingest-time cache keyed on a dataset-version fingerprint —
EVERY count-changing ingest path (fetch/expand/remove-data too) must refresh it or the sentinel must
do a cheap real existence check; verify the fetch-then-view path, not just backfill-then-view.
