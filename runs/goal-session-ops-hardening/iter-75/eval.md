# Iteration 75 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** lean

## Summary

Good news first: all eight must-have journeys were checked this round and all eight passed, and
for the first time since round 72 the two journeys about the backtest page and the
background-work notice — J-08 "Backtest page always shows saved results, never waits for a fresh
calculation" and J-09 "The app says when it is doing work in the background" — were watched live
and photographed working. Every picture I opened shows the real, fully-drawn app; the broken,
half-loaded pages that spoiled the last three rounds did not appear once. I re-checked the
important numbers against the database myself and they match exactly.

The honest other half: this round did not do the job it was given. The plan asked for a repair of
the test-picture-taking setup that keeps breaking, plus two small clean-ups. The engine ran an
evidence-only pass instead, so no developer worked and nothing in the product changed. The broken
setup was not repaired — it simply did not misbehave this time. Two small clean-ups the plan
listed are still undone. Because of that, and because 133 small open notes remain on the record,
this is not the round to declare the goal reached.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Backfill honors the requested range and explains zero-work | passing | passing (re-verified) | `reports/phase-goal-ops-hardening-iter-75-ui-test-results.md` row UT-J-01 · `reports/qa/goal-ops-hardening-iter-75-evidence/J-01-verify.png` · DB `data_provider_runs` 485/486 |
| J-03 No per-run range cap | passing | passing (re-verified) | row UT-J-03 · `.../J-03-verify.png` (Job progress "backfill job · 2025-06-01 → 2026-07-17", 412 days) · DB `data_provider_runs` 487 (calendar_days 412) |
| J-04 Non-blocking boot with visible status | passing | passing (re-verified) | row UT-J-04 · `.../J-04-verify.png` (SNAPSHOT DATES 2980 / GAPS 2416 at 06:26 UTC) |
| J-05 Aggregates are precomputed at ingest, never on the fly | passing | passing (re-verified) | row UT-J-05 · `.../J-05-verify.png` ("as of 2005-07-14 … Scanned 2026-08-13 06:26:31") · DB `scanner_runs` 2981 created 06:26:31.386031, `data_provider_runs` 488 |
| J-06 Pages load only what they need | passing | passing (re-verified) | row UT-J-06 · `.../J-06-verify.png` (styled Regime Lab in its honest "Still computing — 16s elapsed" state) |
| J-07 Heavy aggregates never take the service down | passing | passing (carried; golden is a smoke test) | row UT-J-07 · `.../J-07-verify.png` · substantive evidence carried from `runs/goal-session-ops-hardening/iter-74/phase-vmpeak-samples.csv` (4,724.0 MB peak vs 8,192 MB cap = 42.33% margin) under an EMPTY product diff |
| J-08 Backtest evidence serves from storage only | passing (carried since iter-72) | passing (FRESH first-party evidence) | rows UT-J-08 (replay + LLM) · `.../J-08-refreshing-indicator.png`, `.../J-08-fresh-settled.png`, `.../J-08-verify.png` · DB `data_provider_runs` 491, `forward_aggregate_cache` r2982-f6596450 n_runs 2980 / n 1292431 |
| J-09 The backend discloses its own background-compute activity | passing (carried since iter-72) | passing (FRESH first-party evidence) | rows UT-J-09 (replay + LLM) · `.../J-09-active-window.png`, `.../J-09-idle-last-outcome.png`, `.../J-09-verify.png` · DB `forward_aggregate_cache` writes 07:25:06 → 07:35:43 |

No journey is `failing`, `regressed`, `partial`, `unknown` or `DEFERRED-BUDGET`. No
`browser-infra.json` exists (no infra block). No `journeys-changed.md` exists, and I recomputed
all eight `spec_hash` values from `docs/goal.md` with
`scripts/automation/lib/goal_gate.py hash-journeys` — every one is byte-identical to the recorded
value, so no journey's goal text moved.

### What I opened, and what the pictures actually show

Binding lesson from rounds 72–74: open EVERY frame in the batch, not a sample. I opened all
thirteen images in `reports/qa/goal-ops-hardening-iter-75-evidence/` plus all eight demo frames.

- **Zero broken shells.** Not one frame is the unstyled, asset-less "Checking backend… / Checking
  board status…" page that spoiled iter-72, iter-73 and iter-74. Every frame is the drawn app with
  its stylesheet, sidebar, top bar and real data.
- **J-09's frame is finally about J-09.** In iter-73 and iter-74 its frame showed `/backtest`;
  this round `J-09-verify.png` shows `/data`, and the LLM lane's two frames show the disclosure
  itself — the badge reading `Ready` **and** `background compute running (1)` at the same time,
  the panel reading `as-of 2026-07-31 · elapsed 4m 55s · horizons 2/5 · dataset r2981-f6595650`,
  and then `No background compute running.` + `Completed · as-of 2026-07-31 · 8m 4s`.
- **Two frames I will not overstate.** `J-07-verify.png` and `J-08-verify.png` are the same
  `/backtest` landing page (both 135,003 bytes, different md5), and `J-07.json` has only two steps,
  so J-07 was not really re-tested this round. `J-06-verify.png` shows a page still computing.
  Both are stated in the journey gaps rather than smoothed over.

### Numbers I re-derived myself rather than accepting

1. **J-08's served payload vs storage.** `forward_aggregate_cache` (asof_key `2026-07-31`,
   dataset_version `r2982-f6596450`, horizon 1, created 07:25:06.087) holds `n_runs` 2980 and
   `overall` = mean_return 0.0007046800121982145, mean_max_drawdown -0.025303636926811413,
   n 1292431. `J-08-fresh-settled.png` displays 2980, +0.07%, -2.53%, n=1292431. Exact agreement
   (AG-3).
2. **The +1 snapshot is arithmetically visible.** Between the refreshing frame and the settled
   frame the per-bucket sample sizes move A +4, B +16, C +17, D +15, E +97 — summing to exactly
   149, one snapshot's worth of result rows. The headline count moves 2979 → 2980 and the total n
   moves 1292282 → 1292431 (+149).
3. **J-08's job, from the job record.** `data_provider_runs` 491: kind backfill, 2005-07-18,
   started 07:20:38.068770, finished 07:41:11.359506 (20m33.3s), status ok, snapshots_created 1 —
   matching the report to the second. `scanner_runs` 2982 (2005-07-18) created 07:20:50.043172.
4. **J-09's window, from the clock.** The window started 07:07:17 and completed 07:15:21
   (duration_ms 483875 = 8m 3.9s → panel "8m 4s"). `J-09-active-window.png`'s own file time is
   07:12 UTC and it displays "elapsed 4m 55s"; 07:07:17 + 4m55s = 07:12:12. The frame and the
   filesystem agree independently of the report. A second window is visible in storage:
   `forward_aggregate_cache` r2982 rows for the same as-of written 07:25:06.087 → 07:35:43.991 =
   732.5 s, the figure the report gives.
5. **The replay sequence is corroborated in the database.** `data_provider_runs` 485 (06:25:58,
   19 of 28 days, 9 non-trading), 486 (06:26:00, 0 of 2 weekend), 487 (06:26:05, 412 calendar
   days), 488 (06:26:20 → 06:43:53, one new snapshot) line up one-for-one with J-01, J-01's second
   run, J-03 and J-05 — in the order and at the minutes the frames were taken.
6. **The server log is clean, and I counted it.** Since the QA backend booted
   (`logs/backend.log`, `=== start-backend.sh: launching at 2026-08-13T06:25:07Z ===`, port=8255)
   its 2,579 lines carry **2,336 requests, all HTTP 200**, and **zero** MemoryError, QueuePool,
   Traceback, "Exceeded concurrency limit", ERROR or CRITICAL — across two real ingest jobs and
   two background-compute windows.
7. **No golden was weakened.** `J-08.json` and `J-09.json` are the only two journey scripts
   changed this round, and the diff is one appended `_notes` entry each; every step and setting is
   byte-unchanged. The binding "do not regenerate the J-05..J-09 goldens" was honored.
8. **One number I could not re-derive, and I say so.** The report's baseline "Snapshots
   contributing (≤ 2026-08-03): 2920" belongs to a cache version that r2982's rows overwrote at
   07:21, so it is no longer checkable. It is not load-bearing — the 2979 → 2980 chain is, and
   that one I verified.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials (AG-7) | OK | `iter-75/scan-report.md`: **CLEAN**, no secret/dependency/license findings. `iter-diff.md` reads "(no changes)" — there are no added lines to carry a credential. |
| Paid / external SaaS | OK | Zero-change product diff: no manifest (`requirements*.txt`, `pyproject.toml`, `package.json`) was touched, so no dependency could be added. |
| License changes | OK | No LICENSE or license-field change is possible on an empty diff; scan-report confirms none. |
| Fabricated / substituted data (AG-3, AG-9) | OK | I queried the DB: every `data_provider_runs` row from this round (485–492) has `provider='seed'`; the only non-seed rows in the whole table are `yahoo` runs whose newest is id 369 at 2026-08-10 09:14, both pre-existing and pre-dating this iteration. And the displayed figures match storage exactly (points 1–4 above). |
| AG-1 / AG-2 / AG-4 / AG-6 (proven-language, promises, referee) | OK | No product change, no new claim, no Evidence Claim. The frames show the standing survivorship-bias caution and "Nothing is fabricated" copy; `J-09-active-window.png` carries "no fabricated finish-time estimate or completion percentage". |
| AG-5 (no-lookahead) | OK | No engine change. J-08's fallback served a complete OLDER version (2979) rather than a partially newer one, which is the no-lookahead-preserving behavior the journey requires. |
| AG-8 (resilience, no unbounded loads, graceful degrade) | OK | Zero non-200s in 2,336 requests, zero MemoryError/QueuePool on the live QA server; `J-06-verify.png` shows an honest "still computing" state, not a blank error page. |
| AG-10 (host resource ceiling) | OK | `git status --porcelain -- config.yaml project-extensions/ scripts/` is EMPTY, and the live QA backend's own boot header echoes the caps: `port=8255 memory_cap_mb=8192 malloc_arena_max=2` and `host-guard: cpu_list=0-15 blas_threads=8`, launched via `scripts/start-backend.sh`, never `dev.sh`. All heavy work this round was single-day in-app backfills. |
| Coherence | OK | `iter-75/coherence.md` = **COHERENCE-PASS** (deterministic pass, zero-change product diff — no dispatch needed). Not a crash-stub. |

**Ledger after this round: 259 total, 133 unresolved, 0 unresolved critical.**
Closed (2): iter-73/c and iter-74/b — the "required journeys must have their own fresh evidence"
pair, closed because J-08 and J-09 now do.
Opened (4, all minor): **iter-75/a** the round's declared depth and its Definition of Done did not
match what ran (spec says `lean` with code work; `depth-dispatched` says `evidence`; developer and
reviewer both `step_skipped`; TC-6 unfiled and the stray `=` file still present — I checked);
**iter-75/b** the walkthrough recorder produced byte-identical frames for both before/after pairs
(step-04 = step-07, step-05 = step-06), so neither transition is depicted; **iter-75/c** J-07's
golden is a two-step page-render check and J-09's passes against an idle panel, so "8/8 replay
PASS" overstates regression coverage; **iter-75/d** fifteenth consecutive over-budget round
(6,529 s against 3,600 s ≈ 1.8x — the smallest overrun in several rounds).

Deliberately kept OPEN: **iter-72/c** (the intermittent asset-less frontend) — it did not recur,
which is not the same as fixed, and no code changed; **iter-74/a** (replay failures explained by
an assumed cause) — there were no failures to explain, and the canned-void mechanism is untouched;
**iter-74/c** (the stray `=` file) — still on disk.

## Next-Step Recommendation

Run the next round at **lean** depth, with a developer, and do the work the last plan asked for.
In order:

1. **Find out why the test browser sometimes gets a half-loaded page, and fix it.** It behaved
   this round, so there is no broken picture to chase — use the frontend's own start-up log and
   rule the "rebuild while serving" theory in or out. Until this is understood, every good round
   is luck.
2. **Make the automatic re-checks mean something for two journeys.** The saved script for J-07
   "Heavy aggregates never take the service down" only opens two pages and checks two words; the
   script for J-09 "The app says when it is doing work in the background" passes even when nothing
   is running. Give each one a check of the thing the journey is actually about.
3. **Two one-line clean-ups that keep being carried:** delete the stray empty file named `=` at
   the top of the project, and either take the one missing picture of the Data page's polite
   failure message or remove the unused test hook at `apps/backend/app/api/data.py:119` with its
   test.
4. **Tidy the stale re-record list.** `runs/goal-session-ops-hardening/state/goldens-regen-pending`
   still names J-05 to J-09 even though all five passed this round; it was always the wrong fix
   and should be cleared so nobody acts on it.
5. **Rides along, never the goal:** the short guided walkthrough for J-05, J-07, J-08 and J-09 is
   still not recorded properly (the recorder saved the same picture twice for each pair), and
   J-06's page timings are still owed to `reports/perf-budgets.md`.
6. **After that, one full round** for showing the data-freshness age on the readiness badge
   (iter-72/f) — the first change a real user would see in a while.
7. **Still carried, untouched:** iter-29/b and the badge wording after a permanently failed
   warm-up (48th round unmade); iter-31/e; iter-32/f; iter-35/k; iter-36/n; iter-37/o; iter-37/q;
   iter-39/u; iter-46/az; iter-46/ba; iter-47/bd; iter-47/bf; iter-47/bi; iter-48/bj; iter-57/f;
   iter-57/l; iter-59/g; iter-59/h; iter-59/k; iter-62/e; iter-62/f; iter-63/a; iter-63/b;
   iter-63/d; iter-64/b; iter-64/e; iter-64/f; iter-65/b; iter-65/c; iter-65/d; iter-66/b;
   iter-66/e; iter-66/f; iter-66/g; iter-67/f; iter-67/g; iter-68/d; iter-68/e; iter-69/e;
   iter-70/c; iter-70/e; iter-70/f; iter-71/e; iter-71/f; iter-71/g; iter-71/h; iter-72/a;
   iter-72/b; iter-72/c; iter-72/d; iter-72/e; iter-72/f; iter-72/g; iter-73/b; iter-73/d;
   iter-73/f; iter-74/a; iter-74/c; iter-74/d. Deferred a forty-second time: iter-33/g, the
   Regime Lab.

**OWNER — one new decision, and it is the important one.** Every one of your eight must-have
journeys now passes, and this round every one was checked with its own fresh evidence. The only
thing still standing between this project and "finished" is a list of 133 small open notes that
this loop has been writing about itself — things like "the walkthrough recording saved the same
picture twice", "the round went over its time budget", "a stray empty file is still there". They
are real, but they are housekeeping, not your product, and the loop is now adding about four a
round and closing about two, so on the current rule the project can never be declared finished.
Please pick one: (a) let the loop close the goal when all journeys pass and no *serious* problem is
open, treating the housekeeping list as a to-do list instead of a blocker; or (b) tell us to spend
two or three rounds clearing the housekeeping list first, and accept the time that costs. Still
waiting on you from before: (i) keep the two-second health-answer promise during long jobs, or
apply it only to short ones; (ii) may we limit how many heavy calculations run at once (B-1107);
(iii) permission to fix the one-line ordering bug in
`scripts/automation/browser-qa-phase.sh`; and (iv) a cost decision — this round ran about 1.8
times its time budget, the fifteenth over-budget round in a row, though the smallest overrun in
several.

## Halt Justification (if halting)

Not halting. Verdict is CONTINUE.

Decision tree, applied top-down:

- **C.1 REGRESSION — rejected.** No journey moved `passing`/`already_passing` → `failing`; all
  eight are `passing` on this round's own evidence. No critical anti-goal violation is unresolved
  (0 unresolved critical in the ledger; scan-report CLEAN; ingest seed-only, verified in the DB;
  caps declared and echoed by the live boot header; displayed numbers matched to storage; zero
  non-200s).
- **C.2 STALLED — rejected.** C.2 needs EVERY unblock path to be human-owned, and most are not:
  root-causing the frontend serving fault, strengthening the J-07 and J-09 goldens, deleting the
  `=` file, resolving the TC-6 hook, clearing the stale regen queue and fixing the walkthrough
  recorder are all ordinary agent work in existing files. Only B-1107, the health-ceiling policy
  sentence, the `scripts/automation` sign-off, the cost sanction and the new
  achievement-criteria decision above are the owner's. Not an infra stall either: no
  `browser-infra.json` exists, both verification lanes RAN, and thirteen fresh frames landed.
- **C.3 GOAL_ACHIEVED — rejected, on two grounds.** (1) The framework rule is literal: a
  GOAL_ACHIEVED verdict requires that no anti-goal violation be unresolved, and 133 remain (all
  minor). (2) This round's own Definition of Done is unmet — the engine ran an evidence micro-path
  against a spec written for lean depth with code-level work, so the harness defect that corrupted
  three rounds of evidence is still un-root-caused and two clean-ups are undone. Declaring the
  goal achieved in a round where no developer ran, and where an intermittent defect merely failed
  to fire, would be exactly the over-read this framework warns about. I record plainly that on a
  reading where only genuine AG-1..AG-10 breaches count, this round's journey table would qualify
  — that is why the owner paragraph asks for a decision instead of hiding the tension.
- **C.4 ESCALATE — rejected.** No journey has failed twice (none failed at all); the review verdict
  is PASS, not a fail-open FAIL; and what this round surfaced is a process/harness matter already
  diagnosed and queued, not product ambiguity. A full round would add audit and UX lanes with an
  EMPTY product diff to read, on an already over-budget cycle.
- **C.5 CONTINUE — chosen.** Coherence is PASS, so no consolidation pass is mandated.
