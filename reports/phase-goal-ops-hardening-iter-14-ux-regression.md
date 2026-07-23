# Phase goal-ops-hardening-iter-14 — UX Regression Review

**Date:** 2026-07-23

**Verdict:** UX-REGRESSION-WARN

---

## Methodology note (why this is not the boilerplate backend-only PASS)

The plan and phase spec both state `Frontend Present: no`, and this is confirmed independently:
`git diff --stat -- apps/frontend` and `git status --short -- apps/frontend` both return empty — zero
frontend files are in this iteration's diff. Under a literal reading of my agent instructions'
"Backend-only phase handling" clause, that alone would justify the boilerplate
`UX-REGRESSION-PASS / Backend-only phase. No UI regression review required.` response.

I did not take that shortcut, for three reasons specific to this iteration: (1) the phase's own stated
purpose is an availability/resilience fix whose entire value is a *user-observable behavior change* on
existing surfaces (no frozen readiness badge, no frozen `/backtest` panel) — the ui-impact-analyst's own
`user-visible-changes.md`/`ui-surface-map.md` explicitly declined to treat `Frontend Present: no` as
"nothing to report" for the same reason; (2) a real browser-qa pass ran this iteration (required by the
dispatch regardless of `Frontend Present`) and returned an overall **FAIL** driven by two findings on
existing, prior-phase UI surfaces (UT-04, UT-10) — exactly the kind of live regression evidence my role
exists to weigh; (3) my own agent instructions list `ui-test-results.md` among the files to "always read
first," which would be pointless if a `Frontend Present: no` flag made its contents moot. The rest of this
report is a substantive review, not the boilerplate.

---

## New Capability Discoverability

**No new user-facing capability was introduced this iteration** — confirmed by the phase spec ("New
user-facing capability: None new," "Any new UI page, nav entry, or displayed value" listed under Out of
Scope) and independently by the empty `apps/frontend` diff. Step 1's literal "is there a nav path to the
new thing" question therefore has no subject. What *is* assessable is whether the iteration's actual
promise — three existing surfaces become more resilient under heavy load — is realized where users already
know to look:

| Surface | Path from home | Clicks | Promise realized? |
|---|---|---:|---|
| Global readiness badge (`HealthBadge`, top bar, every page) | Always visible, no navigation needed | 0 | **Yes** — live-confirmed `ready` throughout a real ~6.8-min warm (UT-03) and correct crash→unavailable→initializing→ready narration through a real kill/restart (UT-J-04). |
| `/backtest` evidence panel | Sidebar → "Backtest" (`apps/frontend/components/sidebar.tsx:37`) | 1 | **Partially** — page still renders and never errors, but under a live concurrent warm it took 211.8 s to resolve a cache-miss (UT-04 FAIL), far outside its own 2‑minute budget. See Regression Risk. |
| `/data` "Refreshed: ..." aggregate line (3 render sites: live job card, persisted last‑run summary, Run History row) | Sidebar → "Data Manager" (`sidebar.tsx:44`) | 1 | **Yes** — "forward aggregates" confirmed present at all three sites (UT-05/06/07 PASS). |

All three surfaces were already 0-1 click from home before this iteration and remain so — nothing about
this change affects reachability. The label on each surface (badge text, "Backtest," "Refreshed: ...")
is unchanged and still matches what it does.

---

## Regression Risk

Navigation integrity is not at risk: no `Sidebar.tsx`, `layout.tsx`, or router file appears in this
iteration's diff, so every route/nav entry established by prior phases is byte-identical and reachable
exactly as before. The risk that exists is behavioral, on three shared components this iteration's
rewritten `compute_forward_aggregates` sits behind:

| Shared component | Prior feature it serves | This iteration's touch | Risk |
|---|---|---|---|
| `HealthBadge` (global) | J-04 "Non-blocking boot with visible status," most recently hardened in ops-hardening iter-4 (added the `awaiting_snapshot` state) | No file touched; the badge's underlying `/api/health` liveness is exercised harder by the now-longer-but-successful warm | **Low, and net-positive.** UT-03/UT-09/UT-J-04 all confirm the badge narrates every state correctly and never freezes — this iteration *improves* this component's guarantee, validated live, not just by design. |
| `/backtest` evidence panel + `BacktestSkeleton` loading state | Product-era feature, hardened in **ops-hardening iter-5** (J-06): iter-5's own fix brought a confirmed 34.766 s violation down to sub-200 ms via `forward_aggregates_cached`, and that handoff explicitly treated the *existing* `BacktestSkeleton` idiom as already adequate, unchanged, for that fix | No file touched; the shared `compute_forward_aggregates` dependency is exercised under a load pattern iter-5 never tested (a live cache-miss arriving **during** a concurrent forward-aggregate warm, not just a cold single request) | **Medium-high, live-confirmed.** UT-04: tab opened at a cache-miss, still on the skeleton at 135.5 s (already past budget), resolved at 257.4 s; the resolving `GET /api/backtest` call itself measured **211,829 ms** via the browser's own Resource Timing API. No crash, no red "Backend unavailable" card, badge stayed healthy — this is *not* a repeat of iter-7/iter-13's catastrophic mode — but it is a real, ~580-1500x violation of the page's own committed budget (≤1.5 s per `perf-budgets.md`; ≤2 min per this iteration's own UX bound), on a page whose fast-load guarantee was a named, already-shipped deliverable of a prior phase. |
| `/data` "Refreshed: ..." line (`BackfillBreakdown`) | ops-hardening iter-1/iter-2 (the J-05 aggregate-listing mechanic) | `_refresh_ingest_aggregates` is byte-unchanged; only its dependency got safer | **Low, and net-positive.** UT-05/06/07 all PASS at all three render sites; the entry should now drop less often (the failure mode it used to guard against — the very first horizon's memory error — is what this iteration removes). |
| `/data` job-progress panel (`job-live-activity` / `job-heartbeat`) | **ops-hardening iter-4** (F1 fix): a deliberately bare `prog.tick()` before each of the 5 horizons' compute inside `_refresh_ingest_aggregates` (`apps/backend/app/engine/data_manager.py:3220`), explicitly sized (per that line's own code comment) against an assumed "~35 s pre-warm" per horizon, and deliberately leaving `current_activity` frozen on the last scan message so as not to break `test_progress_payload_has_heartbeat_and_activity`'s existing assertion | The exact compute this per-horizon tick wraps (`compute_forward_aggregates`) was rewritten; the tick's cadence/spacing (still once per horizon, before that horizon starts) was not revisited | **Medium, live-confirmed, self-recovering.** UT-10: heartbeat read "updated 1m 43s ago · possibly stalled" at ~103 s into the warm (later reset to "10s ago"), and `current_activity` stayed pinned at "scanning 2026-07-21 (1/1)" for the entire ~6.8-minute run even once deep into the aggregate-warm stage. This is not a new bug this iteration introduced — it is iter-4's own by-design tradeoff (confirmed by reading its docstring and the `~35s` sizing comment), now stretched thin by the same ~9x data growth that motivated this whole iteration: a single horizon's compute apparently now runs long enough to cross the staleness threshold before the next per-horizon tick resets it. |

**Required-still-passing journeys:** J-01, J-03, J-05 all re-verified PASS via deterministic golden replay
(`reports/phase-goal-ops-hardening-iter-14-regression-replay-results.md`, 3/3), and J-04 was executed live
end-to-end against a real operator-scheduled kill/restart and passed (UT-J-04) — no regression in any of
the four required journeys' own core acceptance.

**Open, untested risk (not evidenced, flagged for follow-up):** UT-04's root cause is explicitly not
diagnosed in the dev handoff ("no root cause is asserted here, only the observed timing" — could be DB/
connection-layer contention from the concurrent backfill, or something specific to
`compute_forward_aggregates`'s own logic under contention). If the cause is shared-connection/DB-file
contention rather than something intrinsic to this one function, other pages that read from the same
database during a heavy warm (`/stocks`, `/sectors`, `/scanner-runs`, `/evidence`, etc.) could show similar
unexplained multi-minute waits under the same concurrent-warm condition — this was not tested this
iteration (only `/backtest` was browser-measured during a live warm).

---

## UI vs Backend Parity

- **Rewritten read path (`compute_forward_aggregates`'s streaming rewrite):** correctly not surfaced in the
  UI — byte-identical output (TC-1/TC-2), no new endpoint/field, no schema change. This is intentionally
  backend-only per the phase spec, and appropriately unexposed.
- **The core reliability guarantee (no more full-backend wedge):** appropriately reflected as *improved
  behavior* of existing surfaces rather than a new displayed value — correct call, and confirmed live for
  the badge (UT-03/UT-09/UT-J-04).
- **Gap:** the guarantee is only partially realized in practice — the badge's honesty holds, but two
  adjacent, already-shipped UI promises (`/backtest`'s committed load budget; the job-progress heartbeat's
  "not stalled" honesty) are not fully covered by this iteration's fix, per the live evidence in Regression
  Risk above. This is not a "hidden backend capability" in the classic sense (nothing new exists to expose)
  — it is that the fix's real-world envelope is narrower than what the UI (and this project's own committed
  budgets) already promise.
- **Documentation-freshness note (not user-facing, flagged for pipeline hygiene only):**
  `reports/phase-goal-ops-hardening-iter-14-implementation-summary.md` (written 11:22, per file mtime)
  still lists under "Incomplete Items" that "the full-scale, real-database measurement pass is not done
  yet." The dev handoff's later same-day "Operator-Supervised Measurement Transcription" section and
  `reports/perf-budgets.md` both record TC-5/TC-7 as **CLOSED PASS** via an operator-supervised pass. The
  two reports now disagree about what was completed. This has zero live-product impact (both describe an
  internal measurement step, not a UI element), but is worth reconciling so a reader of
  `implementation-summary.md` alone isn't misled about iteration completeness.

---

## Flags

### Hidden Capabilities
- None. No new backend capability this iteration lacks a UI entry point — the change is an internal,
  byte-identical-output read-path rewrite; there is nothing new to hide.

### Undiscoverable Capabilities
- None. `/backtest` and `/data` are both existing, top-level, 1-click sidebar entries
  (`apps/frontend/components/sidebar.tsx:37,44`, file unchanged this iteration); the global readiness badge
  requires 0 clicks. Nothing about this iteration changes reachability of anything.

### Potential Regressions
- **`/backtest` evidence panel under concurrent warm (ops-hardening iter-5's feature)** — live-confirmed
  211.8 s resolution on a cache-miss arriving during a concurrent forward-aggregate warm (UT-04 FAIL),
  vs. the page's own committed ≤1.5 s (`perf-budgets.md`) / ≤2 min (this iteration's UX bound) budgets. No
  crash, no error card, self-resolving — a real but non-catastrophic degradation of an already-shipped,
  budget-committed prior-phase feature.
- **Job-progress heartbeat/activity cadence under long warms (ops-hardening iter-4's feature)** — live-
  confirmed a "possibly stalled" heartbeat reading (self-recovering) and a `current_activity` string frozen
  on a stale "scanning ..." message for an entire ~6.8-minute run (UT-10 FAIL, P3). By design per iter-4's
  own docstring (a deliberate tradeoff to preserve an existing test assertion), but the tradeoff's sizing
  assumption (~35 s/horizon, per `data_manager.py:3220`'s own comment) has been outpaced by the same ~9x
  data growth this iteration's own narrative is about — this specific message ("possibly stalled") is a
  false alarm on what is, per every other signal, a perfectly healthy job.

### Visual Consistency
- N/A. Zero frontend files touched (`git diff --stat -- apps/frontend` empty) — no new page, component, or
  style exists to compare against the DESIGN SYSTEM. Every established visual pattern (badge states,
  skeleton loaders, Run History table styling) is byte-unchanged.

---

## Recommendation

1. **Root-cause UT-04's 211.8 s `/backtest` resolution** before treating J-07's "heavy aggregates never take
   the service down" guarantee as fully closed for the concurrent-load case — the dev handoff itself does
   not assert a cause (DB/connection contention vs. compute contention under the GIL). Until diagnosed, the
   guarantee should be understood as "the catastrophic wedge is gone; a milder, unexplained multi-minute
   slowdown under concurrent load is not."
2. **Consider an elapsed-time-aware affordance for long `/backtest` cache-misses** (e.g., a "still computing
   — this can take a few minutes under heavy load" message once the skeleton has been showing past some
   threshold) instead of an indefinite bare skeleton. Explicitly out of this iteration's scope, but the live
   evidence (a 4+ minute silent skeleton) makes this a concrete, not theoretical, backlog item now.
3. **Revisit the per-horizon heartbeat-tick cadence** iter-4 sized at `data_manager.py:3220` against the
   current, ~9x-larger data basis — either tick more granularly within a single horizon's now-streamed
   compute (iter-14's own rewrite would make this straightforward to add), or adjust the frontend's staleness
   threshold with a documented justification.
4. **Consider letting `current_activity` name the finalize sub-stage** (coverage / market-phase /
   forward-aggregate warm / drawdown-expectations) instead of leaving the last scan message pinned for the
   whole finalize tail — iter-4 deferred this specifically to avoid touching
   `test_progress_payload_has_heartbeat_and_activity`; that assertion could be updated alongside a fix.
5. **Reconcile `implementation-summary.md`'s "Incomplete Items"** with the dev handoff's later transcription
   turn and `perf-budgets.md`'s TC-5/TC-7 PASS results — a documentation-freshness fix, not a product one.
6. **Spot-check other data-reading pages** (`/stocks`, `/sectors`, `/scanner-runs`, `/evidence`) for the
   same kind of latency spike when loaded during a concurrent forward-aggregate warm — this iteration's
   browser-qa only measured `/backtest` under that condition; if the cause is shared DB/connection
   contention rather than something specific to `compute_forward_aggregates`, the risk may not be confined
   to the one page tested.

No action is required on discoverability or navigation — both are unaffected and already correct.
