# goal-ops-hardening-iter-57 Audit Report

**Date:** 2026-08-10
**Auditor:** Hard audit pass — skeptical, evidence-based (re-audit after the audit-fix pass)

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-06's substantive work is real and correct. I traced every risk-class DoD item through the actual code
rather than the handoff: the availability stale-serving fallback, both `persisted_this_call` rollback
fixes, the recursive-CTE distinct-symbol count, the bounded `sma_series` slice, and the `list_runs`
grouped aggregate are each sound, byte-identity-preserving, and covered by tight fault-injection or
against-the-original regression tests (I re-ran the fast subset myself: **11 passed, 0 failed**). The
during-a-job lie is genuinely gone — QA's UT-03 shows the real 5,391-cell heatmap plus the honest
banner while a real backfill was mid-flight.

Three gaps keep this off a clean PASS. The most serious is **not a product defect but a verification
defect**: the TC-7 health drill's own log ends with a poll that never answered (`000` after a 10.0 s
timeout) while an ingest heavy-warm window was still open, yet `reports/perf-budgets.md` Addendum 23,
the dev handoff and `status.json` all record "1,211 polls, **ZERO non-200**, no unresponsive gap." The
log wins. The other two are the previously-carried B4/B5: the J-06 golden's gates are a 4.5 s
page-level bound rather than the committed per-call budgets, and the "— updating" banner asserts an
in-flight ingest whenever the cache stamp mismatches, including when no job is running.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (gap, unresolved): the TC-7 drill's one failed poll was dropped from the record, and the compute window was mis-segmented — the committed claim "ZERO non-200 / no unresponsive gap" is contradicted by its own log**

Evidence, in order:

1. `runs/goal-ops-hardening-iter-57/tc7-health-poll.log` has **1,212** records, not 1,211. Its **last
   line** is:
   ```
   2026-08-10T10:30:00Z 000 10.002641ERR -1
   ```
   HTTP code `000` after `10.002641 s` — a `--max-time 10` expiry, i.e. `GET /api/health` returned
   nothing for ten seconds. The preceding poll (10:29:59Z) answered in 7.6 ms.
2. `reports/perf-budgets.md` Addendum 23 (line 9357) records `Whole window (10:06:44Z → 10:29:59Z) |
   1,211 | … | non-200 **0**` and states in prose (line 9363): *"Every one of 1,211 polls answered
   HTTP 200 — no non-200, no frozen window, no unresponsive gap."* The segment counts (699 + 424 + 88
   = 1,211) confirm the failed record was excluded from every segment, and the window's stated end
   (10:29:59Z) is exactly one second before it. The same claim is repeated in
   `docs/handoffs/goal-ops-hardening-iter-57-dev.md` ("1,211 polls, ZERO non-200") and in
   `runs/goal-ops-hardening-iter-57/status.json` ("the binding HTTP-200/no-freeze clause held on all
   1,211 polls").
3. The backend was **alive and inside a declared heavy-compute window** at that moment.
   `logs/backend.log`:
   - `10:16:41,695 ingest heavy-warm window OPEN: job=682b13b49f4d4c1ba98361c83e5a56d8 depth=1`
   - `10:34:17,144 ingest heavy-warm window CLOSED: job=682b13b49f4d4c1ba98361c83e5a56d8 depth=0`
   - `10:28:32,773 … phase=factor_lab_all_warm elapsed=589.63s`, then
     `phase=drawdown_expectations_warm` sub-phases at `10:30:11,477` (66.58 s),
     `10:30:39,577`, `10:31:06,866`, total `344.20s`, ending `10:34:16,974`.
   The process kept logging normally through 10:34 and ran further jobs at 10:38 and 10:40, so
   "the operator killed the backend at 10:30:00" is ruled out by the evidence.

Two consequences:

- **The segmentation is wrong.** Addendum 23 labels 10:18:51Z→10:28:27Z "the background-compute
  window" (that is only the J-09-triggered *forward-aggregate* sub-warm) and labels the 88 polls from
  10:28:28Z onward *"After the window closed … max 89.7 ms, 0 non-200."* Those 88 polls were still
  inside the ingest heavy-warm window (open until 10:34:17), during `drawdown_expectations_warm`. The
  failed poll sits inside that window too.
- **TC-7's binding clause did not hold.** TC-7 requires *"every poll answers HTTP 200 within the
  … relaxed ≤2 s ceiling"* during a bounded background-compute window. One poll answered nothing for
  ≥10 s. That is a stronger breach than the 2.593 s latency overshoot that *was* reported, and it is
  the J-07-class "heavy compute takes the service away" signal the clause exists to detect.

This is not a defect in this iteration's product diff — `_distinct_symbol_count` is a strict reduction
in `/api/health`'s cost, so the endpoint can only be faster than before. The defect is in the
verification record, which downstream agents (goal-evaluator, iter-58 decomposer) will read as
"binding clause held." Per `.claude/judgment-rubrics.md` §6, when the artifact contradicts the claim,
the artifact wins.

**Not fixed here** (DoD item 9 / TC-14 binds audit findings to notes; the dispatch instruction is
"write the report and STOP"). The required correction, for iter-58 to append verbatim as a dated
`reports/perf-budgets.md` addendum:

> *Correction to Addendum 23 (filed by the iter-57 audit).* The TC-7 drill log contains **1,212**
> records, not 1,211. The final record, `2026-08-10T10:30:00Z 000 10.002641ERR -1`, is a poll that did
> not receive an HTTP response within its 10 s timeout, and it occurred **inside** the ingest
> heavy-warm window for job `682b13b4…` (OPEN 10:16:41,695 → CLOSED 10:34:17,144, `logs/backend.log`),
> during `drawdown_expectations_warm`. The "After the window closed" segment (88 polls) was likewise
> inside that window. TC-7's binding HTTP-200 clause therefore **did not hold**: 1 poll of 1,212 (0.08 %)
> returned no response for ≥10 s, in addition to the 1 poll at 2.593 s against the ≤2 s ceiling. The
> statements "non-200: 0" and "no frozen window, no unresponsive gap" are withdrawn.

**B2 — IMPORTANT (gap, carried): the "— updating" banner asserts an in-flight ingest whenever the cache stamp mismatches, including when no job is running**

`apps/backend/app/engine/data_manager.py:1722` computes
`payload["stale"] = row.dataset_version != version` — pure stamp inequality, with no reference to
whether a job is actually running. The spec's own data-contract defines `stale: true` as *"an ingest
is mid-flight and the finalize warm has not yet re-run"*, and the UI renders the word "updating"
(`apps/frontend/components/availability-heatmap.tsx:224-230`). The code computes a strictly larger set
than that definition:

- The **only** writer of `AvailabilityCache` is the ingest finalize tail
  (`data_manager.py:4517`); `grep -n availability apps/backend/app/engine/warmup.py` returns nothing,
  so there is no boot-time warm to re-converge the stamp.
- That warm is deliberately non-fatal: `except MemoryError: … _release_process_memory()` /
  `except Exception: … (non-fatal)` (`data_manager.py:4519-4524`). If it is skipped, the job still
  completes, the stamp stays bumped, and `/data` reads "Data as of `<old stamp>` — updating"
  indefinitely, with no job running. The sibling warms in the same tail have already been skipped this
  way many times on this host (`logs/backend.log`: `ingest forward-aggregate warm aborted` ×29,
  `drawdown-expectations` ×14, `index-series` ×4); the availability warm has the identical guard and
  runs a full-history `GROUP BY` over 3.3 M rows.
- Independently, `_membership_dataset_version` (`app/engine/research.py:2566-2570`) folds
  `max(scanner_runs.id)` and `count(scanner_runs)`, and the boot warm-up creates cadence snapshots via
  `run_scan` (`app/engine/warmup.py:295`). Any newly-snapshotted cadence date bumps the stamp with no
  ingest job in sight.

Net effect is still a large honesty *improvement* over iter-56 (the operator now sees the real 5,391
cells instead of "No availability yet" over a 3.3 M-row DB), so this is a residual, not a regression.
Already scheduled as iter-58 carry item 3 ("gate the banner on the live job signal `/data` already
renders"). Confirmed unfixed in the current tree.

**B3 — IMPORTANT (gap, carried): J-06's golden gates a 4.5 s page-level bound, not the committed per-call budgets — a `/api/health` regression to 2 s would still PASS**

`runs/goal-session-ops-hardening/journey-scripts/J-06.json` steps 1/2, 4/5, 8/10, 12/13 pair a 2500 ms
`goto` cap with a 2000 ms assertion cap. I verified the gates are genuinely non-vacuous — the dev's
sabotage matrix (Addendum 22, and the golden's own `_notes`) fails each endpoint independently
(+5000 ms health → FAIL step 02; +6200 ms bars → FAIL step 05; +3000 ms availability → FAIL step 10;
+6800 ms runs → FAIL step 13) with a 0 ms control passing. That is a real fix of the reviewer's earlier
CRITICAL.

But TC-12 asks for *"a measured latency at or under **its committed budget**"*, and the committed
budgets are ≤0.1 s (health) and ≤1.5 s (the other three). The shipped gate is 4.5 s end-to-end
(2.0 s for availability past its own stagger). Concretely: the 241 ms `/api/health` reading that this
iteration exists to fix would **not** fail the golden, nor would a 20× regression to 2 s. DoD item 7 is
therefore partially met. The honest scope is stated plainly in the golden's `_notes` and the handoff,
and the per-call budgets are proven by instruments that can actually measure them (Addendum 21 curl;
QA UT-06 in-browser 23/24/28/34/38/47 ms; UT-07 bars 3 ms). Closing it needs a `demo_runner`
resource-timing primitive that does not exist — framework track, iter-58 carry item 2.

**B4 — GAP (disclosed, remediated by process): AG-9 breach during this iteration's drills; TC-16 as literally worded is not met**

`data_provider_runs` id=369 — `provider='yahoo'`, 591 outbound requests, 09:14:13Z, `bars_fetched: 0` —
from a manual drill click on `/data`'s pre-existing "Fetch real EOD prices" button. DoD item 12 asserts
"AG-9 all ingest rows created this iteration read `provider='seed'`"; that is false for this iteration.
No non-seed data entered the basis and no product code introduced the path. The audit-fix pass logged
it as an owner-visible event with the five prior uncaught occurrences named (ids 135/261/262/264/297)
and adopted two process rules — drills use backfill only, and TC-16 is verified **after** the lane
(`runs/goal-session-ops-hardening/state/assumptions.md:429-468`). I re-verified the AG-10 half
directly: `git status --porcelain` and `git diff --stat` over `config.yaml`,
`project-extensions/host-guard/host-guard.env`, `scripts/start-backend.sh`, `scripts/dev.sh`,
`scripts/start-frontend.sh` are both **empty**.

**B5 — GAP: `stale: true` with an empty payload would still render the false "No availability yet — Fetch real EOD prices" message**

`apps/frontend/components/availability-heatmap.tsx:247` gates the empty state on
`state.data.cells.length === 0` alone. The spec's frontend requirement says that message is honest
**only** when `stale: false` and cells are empty. A cache row persisted while the DB had no benchmark
trading days, followed by bars landing before the next warm, yields `stale: true` + empty cells — the
banner and the false empty state would render together. Narrow precondition; noted, not fixed.

**B6 — OBSERVATION: `models.py` still documents the opposite of the shipped behavior**

`apps/backend/app/models.py:742-744`: *"a stale row keyed to an older stamp is never hit (and is pruned
on write), so the cache can NEVER serve a stale heatmap."* Serving exactly that stale row is now the
intended, tested behavior. Also flagged by the reviewer; iter-58 carry item 4.

**B7 — OBSERVATION: `availability_from_storage`'s row read has no `ORDER BY`, relying on an invariant held elsewhere**

`data_manager.py:1720` is `session.exec(select(AvailabilityCache)).first()` — unfiltered, unordered. I
verified the at-most-one-row invariant it depends on actually holds: `UniqueConstraint("dataset_version")`
(`models.py:750-752`), prune-every-other-stamp before insert (`data_manager.py:1649-1660`), and a single
writer (`data_manager.py:4517` is the only call site of `availability_cached_with_status` in
`apps/backend/app`). A concurrent second writer with a *different* stamp could in principle leave two
rows and make the served row arbitrary; with one writer behind the job lock this is not currently
reachable. Worth an explicit `order_by(AvailabilityCache.created_at.desc())` some day — one line, not
this iteration's business.

**B8 — OBSERVATION: the banner surfaces an internal cache stamp to the operator**

QA UT-03 captured `Data as of r2945-rc2945-b2026-08-03-bc3306390-h200 — updating`. The spec asked for
exactly `<served_dataset_version>`, so this is conformant, but it reads as debug output on an operator
page.

### Frontend Findings

**F1 — verified sound.** The banner sits outside the loading/error/ok branches
(`availability-heatmap.tsx:224-230`), so it never gates the grid; `stale: false` + non-empty cells is
byte-unchanged from iter-56; `apps/frontend/lib/api.ts:2734-2735` extends `AvailabilityResponse`
additively and `app/data/page.tsx` needed no change because it passes the response through unnarrowed.
Live-confirmed by QA UT-03 (banner + 5,391 real cells mid-job), UT-04 (banner absent when idle), UT-08
(className byte-identical to the existing `coverage-stale-notice`). No finding beyond B5/B8 above.

### Test Findings

**T1 — GAP (carried, TI-1): TC-13 is not met — `test_api_runs.py` still does not complete.**
Two attempts this iteration (59 min, then 10 min on a warm cache), the file's 4th consecutive
non-completion across iters 55/56×2/57×2. Recorded honestly, which is what TC-13's second clause asks
for; the first clause ("then it completes") is unmet. Mitigation is real: `app/api/runs.py` has a zero
diff this iteration, and the 4 non-`loaded_engine` tests pass in 0.56 s.

**T2 — GAP (carried, TI-2): a test written this iteration has never executed once.**
`test_health_symbol_count_matches_naive_count_distinct_on_loaded_engine`
(`apps/backend/tests/test_health.py:317-326`) is the only endpoint-layer byte-identity check for the
`/api/health` fix, and the dev's `-k distinct_symbol_count` selector does not match its name, so it was
silently deselected. TC-5's byte-identity is still well-evidenced by the three fast hand-built tests
plus the live 591-vs-591 check, so this is a coverage hole, not an unproven claim.

**T3 — GAP (disclosed): J-05 has no deterministic replay row this round.**
Its single-use golden date (2010-11-10) was consumed by this same iteration's LLM lane
(`scanner_runs` id 2946). Its evidence is the LLM lane's detailed live PASS (UT-J-05, ~18-minute
backfill, run 2946 reached and rendered) plus `data_provider_runs` id=370. Acceptable — the rubric's
"No regressions" floor allows an explicit list of what was not re-verified — but J-05's date must be
rotated before its next replay (iter-58 carry item 1).

**T4 — test quality is otherwise high.** Assertions are exact-value, not permissive: the rollback tests
monkeypatch `session.commit` to raise while leaving `session.rollback` real, then assert both
`persisted is False` **and** `rows == []` (`test_data_manager.py:383-407`, `test_indexes.py:654-681`);
the `sma_series` test compares against a literal copy of the pre-fix algorithm across 7 periods rather
than a second call of the new one (`test_indicators.py:57-74`); the `list_runs` tests assert exactly one
grouped `scanner_results` statement via a `before_cursor_execute` listener and include a zero-result run
(`test_mcp_window.py:271-341`); TC-1 asserts the served payload equals the **prior** row's values and
that the stamp genuinely moved. I re-ran the fast subset independently:
`pytest tests/test_indicators.py tests/test_health.py tests/test_indexes.py tests/test_mcp_window.py -q
-k "sma_series or distinct_symbol_count or rollback or list_runs"` → **11 passed, 83 deselected in
0.81 s**.

---

## 3. Domain Assessment

I traced all five risk-class items through the code rather than the handoff.

**Availability stale-serving (the headline fix)** — correct. The three-way branch is exactly what the
spec asked for: no row → honest empty sentinel with `stale: False`/`served_dataset_version: None`;
row with matching stamp → unchanged iter-56 behavior; row with mismatched stamp → that row's real
payload with `stale: True` and the row's own stamp. Zero new queries (the same single row read),
zero recompute — `compute_availability` is never reachable from this path, and a test enforces that by
monkeypatching it to raise. The `dict` returned by `data_availability` is un-modelled, so both new keys
reach the client unfiltered (`app/api/data.py:157-173`).

**`_distinct_symbol_count`** — the recursive-CTE loose-index-scan is a faithful substitute for
`COUNT(DISTINCT symbol)`. I checked the semantics by hand: the anchor `MIN(symbol)` returns NULL on an
empty table (count 0, matching `COUNT(DISTINCT)`); each recursive step seeks the next symbol strictly
greater; the terminal NULL row is filtered by `WHERE sym IS NOT NULL`, so the recursion terminates
after exactly one step past the last symbol. NULL symbols are excluded by both forms. It is a pure
query-shape change with no persisted or cached value, so no staleness is introduced.

**`sma_series`** — byte-identity holds by construction, not merely by test. `sma`
(`indicators.py:40-47`) returns NA when `len(values) < period` and otherwise averages `values[-period:]`.
For `i+1 ≥ period` the bounded slice is exactly `period` long and equals `values[:i+1][-period:]`; for
`i+1 < period` it is `i+1` long, tripping the same NA branch at the same index. Also confirmed the
function is genuinely on the audited request path (`app/api/stocks.py:179`). The dev's disclosure that
the historical 6.2 s reading was probably inflated by GIL contention already fixed in iter-56 — rather
than claiming a 0.14 s fix explains a 6.2 s regression — is the right kind of honesty.

**`persisted_this_call`** — both siblings now `return payload, False` on the rollback branch
(`data_manager.py:1670`, `indexes.py:287`). The freshly computed payload is still served, which is
correct: the value is right, only the durability claim changed. This closes a genuine AG-3 hole feeding
`aggregates_refreshed`.

**`list_runs`** — one grouped query read into a dict before the loop; a run absent from the grouped
result defaults to `0`, identical to what the old per-run `COUNT()` returned. Same response shape.

The architecture stayed local-first and minimal: no schema change, no new endpoint, no second producer,
no new dependency, 13 files, and the two new fields are additive extensions of an already-registered
Data Contract row. Failure handling is explicit throughout (rollback → honest flag; missing row →
honest sentinel; memory pressure → logged skip). TC-14's freeze holds by measurement, not assertion:
the newest `apps/**` mtime is `availability-heatmap.tsx` at **07:23:10**, and every lane artifact is
**11:18-11:26**.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | **None.** Verification-only pass. DoD item 9 / TC-14 binds an audit-found defect to a note for iter-58 rather than a code-changing audit-fix, and the dispatch instruction was "write the audit report and STOP." B1's correction is a documentation change and is supplied verbatim above so iter-58 can append it without re-deriving it. |

Independent verification I did run (read-only): the 11-test fast subset above (11 passed); the frozen-
surface `git status`/`git diff` check (both empty); the TC-14 mtime ordering; and the TC-7 log/backend
log cross-read that produced B1.

---

## 5. Recommended Next Step

**Proceed to iter-58.** J-06's product work is done and evidenced — do not reopen it, and do not
re-litigate the implementation; it should ship as-is.

Iter-58 should carry these, in this order:

1. **Correct the TC-7 record (B1)** — append the withdrawal above to `reports/perf-budgets.md`, and fix
   the same claim in the iter-57 dev handoff and `status.json`. Until that lands, no downstream agent
   should treat "TC-7's binding clause held" as established. Then re-drill TC-7 with the poll bounded by
   the process's own `ingest heavy-warm window OPEN/CLOSED` markers rather than a hand-picked sub-window,
   and count every record including failures.
2. **Gate the banner on the live job signal (B2)** — `/data` already renders `job-status` /
   `background-compute-panel`; a skipped finalize warm must not be able to assert an in-flight ingest
   forever. While in that file, also gate the empty state on `stale === false` (B5).
3. **Rotate J-05's golden date** before its next replay (T3).
4. **Correct `models.py:742-744`** (B6).
5. **Framework track:** a `demo_runner` resource-timing primitive so goldens can assert per-call
   budgets (B3), and TI-1/TI-2 (`test_api_runs.py`'s fixture cost, and the health byte-identity test
   that has never executed).

The two J-07-class conditions this iteration surfaced — the ≥10 s unanswered `/api/health` inside a
heavy-warm window (B1) and the post-`MemoryError` wedge where `/api/health` reports `"ready"` while
every DB-touching endpoint 500s — are the same underlying problem and should be planned together, not
as separate cards.
