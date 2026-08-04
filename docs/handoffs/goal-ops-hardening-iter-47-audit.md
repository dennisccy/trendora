# goal-ops-hardening-iter-47 Audit Report

**Date:** 2026-08-04
**Auditor:** Hard audit pass — skeptical, evidence-based (SECOND audit of this iteration, after the audit-fix pass)

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The engine-level goal IS achieved and I verified it independently rather than accepting the record:
`GET /api/evidence` now answers in ~50 ms after a dataset change instead of falling onto its
163 s+ cold tail, and I proved the two changed read paths are **byte-identical at live scale** with
my own SHA-256 comparison against a both-fixes-neutralised reference (below) — the AG-3 claim the
whole iteration rests on. I found and **fixed one IMPORTANT defect** the reviewer, QA and the dev
all missed: the new request-triggered re-warm had no coordination with the BOOT warm, so after a
restart-with-changed-dataset every `/api/evidence` request spawned a **second full-ledger warm
running concurrently with the boot warm** — doubling peak concurrent heavy compute in exactly the
window this iteration exists to protect. The fix is mutation-verified.

The gaps are verification-side, and one of them is load-bearing: **three DEFINITION OF DONE items
(1, 2, 7) are unmet at audit time.** The only browser-lane artifact on file
(`reports/phase-goal-ops-hardening-iter-47-ui-test-results.md`, mtime `2026-08-04T14:21:39`) reads
**`Browser QA Verdict: BLOCKED`** and states in its own Missing-Target-Journeys section that
*"`UT-J-06` — no test case executed for J-06 by any lane"* and the same for `UT-J-07` — i.e. **both
of this iteration's TARGET journeys have zero verification anywhere** — and it predates every
product-code change in the fix pass (`research.py` 15:00:21, `forward_testing.py` 15:03:35) and my
own audit fix (16:50:03). **This iteration must not be scored until the browser lane re-runs.**

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (fixed): the request-triggered re-warm ran a second full-ledger warm concurrently with the boot warm**

`apps/backend/app/engine/forward_testing.py:2632` (`_spawn_drawdown_expectations_rewarm`). The
single-flight sentinel `_REWARM_IN_FLIGHT` excludes only *another request-triggered* re-warm. It does
not observe `warmup._run_warmup`, whose **last statement** (`apps/backend/app/engine/warmup.py:303`)
runs the identical `_warm_drawdown_expectations` ledger loop.

Failure scenario, and it is the normal one: the backend restarts after an ingest has landed (exactly
what the handoff instructed the operator to do at 15:29 and what I did again at 16:55). The dataset
version has moved on, so the boot warm has real work — and while it runs, **every** `/api/evidence`
request MISSes, serves its stale generation, and spawns a full 7-claim re-warm that runs alongside the
boot warm for its whole duration (measured on this box: the 16:19:30 process's boot warm ran
16:20:05 → 16:30:58, ~10m53s). The dev's own handoff records the precondition verbatim for the 15:29
process: *"all 7 claims read `refreshing` while it warms"* — that state is exactly what triggers the
spawn. `logs/backend.log:181521-181522` shows two `evidence drawdown-expectations cache warmed
(7 claim panels)` completions 2.383 s apart inside a single process — consistent with the duplicate,
though a same-second post-completion spawn cannot be excluded from the log alone; the code path is
unconditional and I proved it by mutation (below).

Impact: each decile claim's resolver peaks at ~573 MB (dev's own Item Q measurement), so the duplicate
roughly doubles peak concurrent heavy compute plus GIL pressure, on a host the dev observed at
**8,388,524 kB VmPeak against an 8,388,608 kB cap — 84 kB of headroom** earlier the same day. That is
squarely what AG-8 forbids, and it is a *new* path introduced by this diff. It is the same class of
error the dev already corrected once this iteration (the 7-thread swarm) — corrected against itself,
not against the pre-existing producers.

**Fix applied** (`forward_testing.py:2642-2657`): stand down while `warmup._WARMUP_THREAD` is alive.
Costs nothing — that thread ends by running the identical loop, so every stale claim still settles, and
a claim invalidated *after* the boot warm passed it is picked up by the next MISS once the thread exits.
The stale generation is still served behind its honest `"refreshing"` label; only the duplicate worker
is suppressed.

**Evidence for the fix (mandatory post-fix verification):**
- New test `tests/test_forward_testing.py::test_cached_with_status_no_rewarm_while_boot_warm_thread_is_alive`
  asserts zero spawns while the boot thread is alive **and** exactly one spawn once it is gone (so a guard
  that permanently wedges the re-warm cannot pass).
- **Mutation-verified**: with the guard neutralised the test fails
  `AssertionError: a second full-ledger warm must never run alongside the boot warm (audit B1) / assert 1 == 0`;
  mutation reverted, test passes. The finding is therefore real and the test is not vacuous.
- `pytest tests/test_forward_testing.py -k "cached_with_status" -q -p no:randomly` → **5 passed in 1.02s**
  (4 pre-existing + mine).
- `pytest tests/test_evidence.py -q -p no:randomly` → **19 passed in 0.76s**.
- `pytest tests/test_warmup.py -k "drawdown or log_isolation" -q -p no:randomly` → **3 passed in 225.33s**.
- Backend restarted onto HEAD and verified live: `/api/health` 200 in 0.095 s, `/api/evidence` 200 in
  0.054 s with all 7 claims populated and `expectations_status` absent (ready); one — not two —
  `evidence drawdown-expectations cache warmed` line for the new process (`logs/backend.log:181655`).
- `git diff` re-read: my product change is one guard block plus its comment; nothing else.

**B2 — IMPORTANT (gap, NOT fixed): the same absence of coordination with the ingest finalize tail**

`apps/backend/app/engine/data_manager.py:3993` warms the identical per-claim cache inside
`_refresh_ingest_aggregates`. B1's guard cannot see it — there is no shared sentinel. So the TC-2/TC-3
scenario (an ingest lands, its finalize tail begins warming, a user opens `/evidence`) still puts a
duplicate full-ledger warm alongside the finalize tail's own warm. Not closed here because it needs new
cross-module state in a third module, which is a design change, not a surgical fix — and the dev's own
disclosed, unclosed measurement (`GET /api/health` p50 1.83 s, max 3.99 s, **8 of 20 polls over the
relaxed 2 s ceiling during an ingest finalize tail**) is the symptom this would contribute to. The
correct closure is one process-wide "drawdown-expectations warm in flight" sentinel that all three
producers (boot warm, finalize tail, request re-warm) set and check.

**B3 — GAP: the new background worker is invisible to the J-09 disclosure surface**

`get_background_compute_status()` (`forward_testing.py:1700`) reports only the historical
forward-aggregate dispatch registry `_HIST_DISPATCH_INFLIGHT`. The new `dd-expectations-rewarm` thread
is CPU-heavy in-flight background compute that `GET /api/health.background_compute` and the `/data`
panel will report as idle. J-09's step 5 promises an *"explicit idle state ('no background compute
running')"* — that field is now idle-while-busy for a third kind of work. Consistent with pre-existing
scoping (the boot warm and finalize-tail warm are equally undisclosed there), and the `/evidence`
"Refreshing" badge is an honest disclosure of this specific work, so this is a gap, not a violation.

**B4 — OBSERVATION: the disclosed decile-resolver slowdown, independently corroborated**

My live measurement, both runs in one process against the real DB (below): flagship
`leadership_score` D10 h=20 — **shipped 48.1 s vs neutralised-reference 30.7 s**. The reference ran
*second*, so it had the warmer OS page cache; the true ratio is at least this bad. This corroborates the
~2x the dev disclosed under B4 of the fix pass and confirms the record is now honest rather than
understated. The event-study claim went the other way (**shipped 6.5 s vs reference 9.7 s**) — the date
filter is a net win where no decile resolution is involved.

**Positively verified, no finding (recorded so the next auditor need not redo it):**
- **No generation mixing (TC-3).** `compute_drawdown_expectations_cached_with_status`
  (`forward_testing.py:2700`) always returns exactly one `EventStudyCache.payload_json` deserialized
  whole; nothing merges two rows.
- **No "no row to serve" window.** `compute_drawdown_expectations_cached` computes → prunes the old
  generation → inserts the new one → commits, all in one transaction (`forward_testing.py:2549-2573`),
  so the last-good row is servable for the entire re-warm. A prune-before-compute ordering would have
  dropped requests onto the cold tail in exactly the window the fix targets; it does not.
- **`_BoundedRankWindow`'s monotonicity argument is sound.** I re-derived it: `hi(n) = d·n//count` and
  `n − lo(n) = n − (d−1)·n//count` are both non-decreasing in `n`, so a capacity committed from `n_max`
  contains the true `[lo, hi)` slice for every `n ≤ n_max`; `slice()`'s `base` arithmetic is correct for
  both keep-smallest (`base = 0`) and keep-largest (`base = n − len(buf)`); the `n ≤ capacity` and
  zero-capacity edges resolve correctly (`research.py:351-406`).
- **PASS 2's `(ticker, run_id)` key set is unambiguous on the live basis.** It would over-collect if a
  run held two `scanner_results` rows for one ticker; `ScannerResult` has no such uniqueness constraint
  (`app/models.py:247-251`), so I checked the data: **0 duplicate `(run_id, ticker)` groups across
  1,272,322 rows.** Latent assumption, not a live defect.
- **AG-9 (offline ingest) intact.** The browser lane's UT-03 ran a `both` (fetch+backfill) job for
  2026-08-03; `data_provider_runs` rows 299-303 all read `provider='seed'` — the committed offline
  seed, no live external call.
- **AG-10 intact.** `project-extensions/host-guard/host-guard.env`, `scripts/start-backend.sh` and
  `scripts/dev.sh` are untouched by this diff (`git status --porcelain` clean for all three);
  `HOST_GUARD_ENABLED=1`, `HOST_GUARD_MEMORY_HIGH="12G"` unchanged.

### Frontend Findings

**F1 — none.** `apps/frontend/lib/evidence.ts` widens `expectations_status` to
`"unavailable" | "refreshing"` and adds a fourth resolver state; `apps/frontend/app/evidence/page.tsx`
renders the table **as normal** (the values are real) plus an additive `Badge variant="warn"` and one
disclosure sentence. Purely additive, reuses the existing badge component, mirrors `/backtest`'s
`evidence_status` precedent, and no pre-existing state's rendering changes. The backend sets the key
only when a stale generation is actually served (`evidence.py:197`), so a current-generation claim is
byte-unchanged on the wire.

### Test Findings

**T1 — OBSERVATION: `tests/test_samples_memory_pressure.py` documents the pre-fix-pass implementation**

`:199-200` still states *"PASS 1's own lightweight `sort_keys` accumulator is still O(population)"* —
made false by the audit-fix pass's `_BoundedRankWindow`. The module docstring's calibration figures
(`shipped PEAK_RSS_KB=692,836`) are likewise pre-fix-pass. No assertion depends on either; the test
remains valid (and now has more headroom than its docstring claims).

**T2 — OBSERVATION: undeclared disk demand in the 5-consecutive proof**

`_fresh_seed_copy` (`:68`) copies the 8.3 GB committed DB once per probe into a single `tmp_path` that
is never cleaned between loop iterations, so `test_shipped_survives_five_consecutive_tight_cap_runs`
holds ~41 GB of copies at once. It passed (180 GB free on this host) but the demand scales with the DB
and is nowhere declared.

**T3 — OBSERVATION: live-scale byte-identity rested on the dev's own drill; now independently confirmed**

`test_factor_decile_observations_equals_pre_fix_reference` runs on a **15-observation** fixture. That
is a real coverage limit — but I closed it myself rather than filing it (see §3).

### Process / Verification Findings

**P1 — IMPORTANT (gap): DoD items 1, 2 and 7 are unmet; the browser lane must re-run before scoring**

TC-7 is stated as a measurable test: *"the iteration is not scored complete if the results file predates
the last code change."* Measured:

| Artifact / file | mtime |
|---|---|
| `reports/phase-goal-ops-hardening-iter-47-regression-replay-results.md` | `2026-08-04T13:05:41` |
| `reports/phase-goal-ops-hardening-iter-47-ui-test-results.md` (merged) | `2026-08-04T14:21:39` |
| `apps/backend/app/engine/research.py` | `2026-08-04T15:00:21` |
| rebuilt `journey-scripts/J-01,J-03,J-05,J-08,J-09.json` | `15:46:21 – 16:05:57` |
| `apps/backend/app/engine/forward_testing.py` (this audit's B1 fix) | `2026-08-04T16:50:03` |

Both lane artifacts predate the fix-pass code, the rebuilt scripts, and my fix. Worse, the merged
artifact's own verdict line reads **`Browser QA Verdict: BLOCKED`**, and its Missing-Target-Journeys
section names `UT-J-06` and `UT-J-07` — **this iteration's two TARGET journeys** — as having no
executed test case in any lane. The 6/6 replay PASS at 13:05:41 was produced by the *pre-rebuild*
scripts my previous audit proved were null tests. So DoD item 1 (target journeys verified), item 2
(six required journeys green on dedicated evidence) and item 7 (TC-7 sequencing) are all currently
unmet. `status.json` already carries `browser_checks_run: false`, `next_action: browser_qa`; the
services are left live, healthy and running HEAD for that lane.

**P2 — IMPORTANT (gap, deliberately NOT fixed): J-05's rebuilt golden is one-shot and decays into a null test**

`runs/goal-session-ops-hardening/journey-scripts/J-05.json` targets `2011-01-05`, which I confirmed is
still genuinely unsnapshotted (`SELECT … FROM scanner_runs WHERE asof_date='2011-01-05'` → empty), so
the script is honest **for its first run**. But `{dates_done}/{dates_total} dates` counts trading days
in range regardless of whether they were already snapshotted (J-01 asserts `19/19 dates` on a range
where all 19 are already snapshotted — same widget, same page), and `stage-timings` renders for
zero-work jobs too. So once a lane run genuinely ingests 2011-01-05, **every later replay is a
zero-work re-run that still satisfies all nine steps** — silently restoring the exact null-test defect
B1 of my previous audit named. The dev disclosed this honestly and prescribed date rotation; a rotation
that depends on an operator remembering is not a guard.

**Prescription (one line, not applied):** add an assertion on the live card's snapshot count —
`apps/frontend/app/data/page.tsx:2785` renders `{job.snapshots_created} snapshots · {…} forward returns
inserted`, so an `expect` on `"1 snapshots"` passes only on a genuinely productive run and fails
(`0 snapshots`) on a zero-work re-run, making the script self-invalidating instead of falsely green.

**Why I did not apply it:** verifying that selector requires driving a real one-day ingest, which would
(a) mutate the committed DB, (b) consume the very gap day the committed script depends on, and
(c) start the multi-minute finalize tail the handoff explicitly says must not be in flight when the
lane starts. Landing an *unverified* new assertion into a golden immediately before the mandatory lane
run would risk a false RED for a reason that has nothing to do with the product. Per the audit
protocol, a fix without evidence is not a fix — so this is reported as an unresolved finding with an
exact prescription instead.

**P3 — GAP: J-05's script does not cover the journey's aggregates leg.** The "persisted run record lists
which aggregates its finalize hooks refreshed" leg is uncovered by the replay lane (the runner's step
timeout is hard-capped at 20 s, `demo_runner.py:1475` — I confirmed both this and that a `wait_for`
with `ms` bypasses the cap via `page.wait_for_timeout`, `demo_runner.py:990-991`, so the dev's chained
15 s waits do work). J-05's acceptance therefore depends on the LLM lane. Dev-disclosed.

**P4 — OBSERVATION: J-01 step 16 still asserts persisted history** (`goto /scanner-runs/748`, expecting
`as of 2026-05-29`) — the shape my previous audit called out. Harmless here because steps 5-14 carry
the substantive live-job-card assertions; the persisted-history step is now a tail-end sanity check
rather than the only assertion.

**P5 — OBSERVATION: two non-blocking lanes are soft.** `ux-regression` reads
`UX-REGRESSION-SKIPPED` (SPEED-15 trim rung 3b). The demo lane recorded
`RECORDED_WITH_NOTES` with *"Step 08 — expected 'Refreshing' did not appear"* — but its step 04 click
never started the backfill, so no refresh could occur; not evidence against the feature, which UT-03/
UT-04 and the dev's drill both observed working.

---

## 3. Domain Assessment

The core question is whether the two changed read paths still produce the engine's own numbers (AG-3).
I did not take that on the record's word. I ran both changed paths against the **real committed
8.3 GB DB opened read-only**, in one process, comparing the shipped code to a reference with **both**
fixes neutralised (`_drawdown_ticker_slice_map` forced back to the unfiltered read, and
`_factor_decile_observations` swapped for the pinned pre-fix whole-population sort + slice), hashing
the whole served payload:

| Claim | shipped sha256 | reference sha256 | scale | verdict |
|---|---|---|---|---|
| `factor / leadership_score / h20` (decile 10 — exercises **both** fixes) | `c34ba014…de773` (48.1 s) | `c34ba014…de773` (30.7 s) | 5 phases, **124,857** observations | **BYTE_IDENTICAL** |
| `event-study / Breakout-watch / h20` (exercises the date filter) | `1d811135…e596` (6.5 s) | `1d811135…e596` (9.7 s) | 5 phases, **46,868** observations | **BYTE_IDENTICAL** |

That is independent live-scale confirmation of the AG-3 claim, on the flagship claim and on a
different cohort kind, and it closes T3.

The domain logic itself is sound. The per-ticker date filter is byte-identical **by construction**, not
by luck: `dates_by_ticker[ticker]` is built from `rows_by_ticker[ticker]`, and the only lookup the
aggregation loop performs is `stored_by_key.get((row["ticker"], row["snapshot_date"]))` where
`row ∈ rows_by_ticker[ticker]` — the query now reads exactly the keys the loop will ask for, no more
and no less (`forward_testing.py:2424-2442`). The `_MAX_IN_PARAMS = 900` batching removes the silent
dependency on the host's SQLite variable limit. `_BoundedRankWindow`'s capacity argument is correct
(re-derived above) and, crucially, the underflow branch degrades to the **exact unbounded computation**
with a logged warning rather than serving a truncated decile — the right instinct for an AG-3 surface,
and it has a test that forces the violation.

The serve-stale design is the honest one. TC-3's no-mixing requirement is satisfied structurally
(one cache row, deserialized whole), the label reaches the UI, and the disclosure sentence tells the
user what they are looking at. The design's one real weakness was not correctness but resource
discipline — it added a third, uncoordinated producer of the same expensive warm (B1, now half-closed;
B2 open).

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/backend/app/engine/forward_testing.py` | `_spawn_drawdown_expectations_rewarm` now stands down while `warmup._WARMUP_THREAD` is alive, so a request-triggered re-warm can never run a second full-ledger warm concurrently with the boot warm (B1). Guarded by try/except so the diagnostic check can never break the serving path. |
| 2 | Important | `apps/backend/tests/test_forward_testing.py` | New `test_cached_with_status_no_rewarm_while_boot_warm_thread_is_alive` — asserts zero spawns while the boot thread is alive **and** exactly one spawn once it exits (so the guard cannot silently wedge the re-warm). Mutation-verified to fail against the unguarded code. |

No other file was touched. The dev handoff's claims remain accurate — B1 is an addition to the
mechanism it describes, not a correction of it — except that its "Consequences for the pipeline" item 1
now applies to this audit's change as well.

---

## 5. Recommended Next Step

**Do not score this iteration yet.** Run the browser-qa lane, then score. Specifically:

1. **Re-run the browser lane (mandatory, TC-7).** Product code changed at 15:00/15:03 and again at
   16:50 (this audit's B1 fix); both lane artifacts are from 13:05/14:21. Services are left live,
   healthy and on HEAD: backend PID 2642184 on :8255 (`/api/health` 200 in 0.095 s), frontend on :3255
   (200), all 7 `/api/evidence` claims `ready` in 0.054 s, no job in flight, boot warm settled
   (`logs/backend.log:181655`). Use `http://localhost:3255`, never `127.0.0.1` (CORS).
2. **The lane must produce rows for J-06 and J-07.** The existing merged artifact reads `BLOCKED`
   precisely because it has none. A clean headline while this iteration's two TARGET journeys have zero
   rows anywhere is the iter-41 failure repeating; treat a lane that again produces no J-06/J-07 row as
   a blocker, not a footnote.
3. **Rotate J-05's date before its next replay, or apply P2's one-line snapshot-count assertion.**
   After this lane's run, `2011-01-05` will have a snapshot and the committed script becomes a false
   green. The window `2005-05-24 … 2019-02-25` holds ~2,495 gap days.
4. **Next iteration: close B2** — one process-wide "drawdown-expectations warm in flight" sentinel
   shared by the boot warm, the ingest finalize tail and the request re-warm. This is also the natural
   home for the dev's disclosed-but-unclosed finding that `GET /api/health` exceeds its relaxed 2 s
   ceiling during an ingest finalize tail, and it pairs with the already-named next target (the ingest
   finalize tail itself, which keeps a job non-terminal for many minutes — corroborated here by
   `data_provider_runs` rows 299-303, all `interrupted` with `symbols_ok=0`).
5. **Carry, unchanged:** `tests/test_api_evidence.py` still not run this iteration (16+ min fixture,
   route unchanged) — run it standalone in a future pass; and refresh
   `test_samples_memory_pressure.py`'s docstrings to describe the shipped `_BoundedRankWindow` (T1).
