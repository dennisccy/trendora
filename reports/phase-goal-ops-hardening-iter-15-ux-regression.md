# Phase goal-ops-hardening-iter-15 — UX Regression Review

**Date:** 2026-07-23

**Verdict:** UX-REGRESSION-WARN

---

## Methodology note (why this is not the boilerplate backend-only PASS)

The plan and phase spec both state `Frontend Present: no`, confirmed independently: zero files under
`apps/frontend/` appear in this iteration's diff (per `user-visible-changes.md`, `ui-surface-map.md`, and
the dev handoff's own `git status` citation). Under a literal reading of my agent instructions'
"Backend-only phase handling" clause, that alone would justify the boilerplate
`UX-REGRESSION-PASS / Backend-only phase. No UI regression review required.` response.

I did not take that shortcut, for the same reasons iter-14's ux-regression review documented and that
remain true here: (1) the touched function, `forward_aggregates_cached`, is the sole serving wrapper
behind an existing, already-consumed, 1-click-from-home page (`/backtest`), so a concurrency-behavior
change to it is real, user-observable behavior even though no frontend file changed a line — the
ui-impact-analyst's own reports explicitly declined to treat `Frontend Present: no` as "nothing to
report," per this dispatch's own pump note; (2) a real browser-qa pass ran this iteration (the framework
fix, commit `d0799803`, forces the lane whenever TESTING REQUIREMENTS names journeys, regardless of
`Frontend Present`) and returned PASS 7/7 — live evidence my role exists to weigh; (3) my own agent
instructions list `ui-test-results.md` among the files to "always read first," which would be pointless if
`Frontend Present: no` made its contents moot. The rest of this report is a substantive review.

---

## New Capability Discoverability

**No new user-facing capability was introduced this iteration** — confirmed by the phase spec ("New
user-facing capability: None new," "Any new UI page, nav entry, or displayed value" listed under Out of
Scope) and independently by the empty `apps/frontend` diff. Step 1's literal "is there a nav path to the
new thing" question has no subject. What *is* assessable is whether the iteration's actual promise —
`/backtest` resolves quickly and predictably even during a concurrent ingest warm — is realized where
users already know to look:

| Surface | Path from home | Clicks | Promise realized? |
|---|---|---:|---|
| `/backtest` evidence panel | Sidebar → "Backtest" (`apps/frontend/components/sidebar.tsx:37`, unchanged) | 1 | **Partially.** The specific defect this iteration targeted — N concurrent requests for the SAME not-yet-cached key redundantly stacking — is confirmed closed (TC-1: 5→1 compute invocations on a practice fixture; live full-scale pass: 64 polled `/backtest` calls during an ~11-min warm, none stacked). But the page's own committed ≤1.5s budget is still violated in the exact live trigger this iteration reproduced: a genuinely-cold cache-miss took **178.7s** (vs. iter-14's original 211.8s — not materially closed), and a **new, unexplained 5.37s spike** was surfaced that the operator's own summary did not mention. See Regression Risk. |
| Global readiness badge (`HealthBadge`, top bar, every page) | Always visible | 0 | **Yes** — TC-6 confirms 498/500 health polls HTTP 200 throughout the live pass, two isolated non-fatal client-timeouts, no wedge; UT-J-04 confirms the badge's full crash/restart narration still holds (carried-forward evidence + this session's fresh steady-state re-check). |
| `/data` "Refreshed: ..." aggregate line | Sidebar → "Data Manager" (`sidebar.tsx:44`) | 1 | **Yes** — untouched this iteration (`data_manager.py` confirmed byte-unchanged/absent from diff); J-05 regression replay (UT-J-05) re-verified PASS. |

All three surfaces were already 0-1 click from home before this iteration and remain so. Labels are
unchanged and still match what each surface does — no label confusion.

**Visual consistency:** N/A. Zero frontend files touched; nothing new exists to compare against the
DESIGN SYSTEM. UT-07 independently re-confirms the 11-entry nav list and `/backtest`'s section order
(As-of scan summary → Forward-test scorecard → Return attribution → Leadership cohorts → Forward-tested
evidence) are byte-identical to iter-14's documented structure.

---

## Regression Risk

Navigation integrity is not at risk: no `Sidebar.tsx`, `layout.tsx`, or router file appears in this
iteration's diff. The risk that exists is behavioral, on the shared `forward_aggregates_cached` wrapper
and on surfaces this iteration's live measurement pass touched for the first time.

| Shared component / surface | Prior feature it serves | This iteration's touch | Risk |
|---|---|---|---|
| `forward_aggregates_cached`'s cache-**HIT** path (warm-cache reads) | ops-hardening iter-5's original `/backtest` fast-load guarantee (the caching mechanism itself, not touched again since) | Unchanged — the fix is scoped to the MISS path only | **None, confirmed live.** UT-01 (warm-cache load): 2 `GET /api/backtest` calls at 116.9ms/554.1ms, both far under budget. UT-02 (2 concurrent tabs, same warm date): row-text arrays byte-for-byte identical between tabs. |
| `/backtest`'s client-side fetch (`apps/frontend/app/backtest/page.tsx:71-88`) vs. the new bounded 45s server-side wait | Existing fetch/loading-state pattern | Not touched, but newly relevant given the backend now makes some callers wait up to 45s | **Checked, clear.** The page's `AbortController` has no independent timer of its own — it only aborts on unmount/dependency change (`asOf`/`readiness` change), so a waiter within the new 45s bound cannot trip a premature client-side abort or "Backend unavailable" card that didn't exist before. Verified directly in source, not merely inferred. |
| `data_manager.py`'s ingest finalize warm loop / per-horizon `job-live-activity` heartbeat tick | ops-hardening iter-4's J-100 fix, previously flagged by **iter-14's own ux-regression review** as a live FAIL (UT-10: "possibly stalled" heartbeat reading, `current_activity` frozen for a full ~6.8-min warm) | **Not touched, not re-tested this iteration.** `data_manager.py` confirmed byte-unchanged/absent from the diff; no heartbeat/`current_activity`/"possibly stalled" measurement appears anywhere in this iteration's TC-4/5/6 results (`reports/perf-budgets.md`) | **Medium, unresolved carry-forward.** The phase spec itself scoped this as "likely shrinks as a side effect of this iteration's fix; revisit only if it does not" — but nothing in this iteration's evidence confirms or refutes that it shrank. An open, previously-flagged UI-facing false-alarm risk remains genuinely untested. |
| `/evidence` page (`fetchEvidence` → `GET /api/evidence`) | Existing 1-click sidebar page (`sidebar.tsx:41`), never previously measured under a concurrent forward-aggregate warm | Not touched by this iteration's diff, but **spot-checked for the first time ever** under this load condition (TC-5, following directly from iter-14's own ux-regression recommendation #6) | **Medium-high, newly surfaced.** One ad hoc read during the heaviest part of the warm hit a **30-second timeout** — recorded honestly, not smoothed into the otherwise-fast 0.009s figure, but not independently re-verified from a raw log, not root-caused, and the page's own on-screen behavior during that timeout (loading state vs. silent hang vs. visible error) is **not characterized** by this pass. This is a pre-existing latent condition exposed by testing, not something this iteration's diff caused — but it is new information about an existing, prominently-reachable page. |
| `/scanner-runs` page | Existing 1-click sidebar page | Not touched; spot-checked | **None.** The operator's ad hoc 404 was confirmed to be a wrong guessed path (`/api/scanner-runs` has never existed); the real page's actual calls (`GET /api/runs`, `GET /api/runs/{run_id}`) were independently confirmed correct by reading the backend's route modules. Not a page defect. |
| `/stocks`, `/sectors` pages | Existing 1-click sidebar pages | Not touched; spot-checked | **Low.** Operator-reported sub-0.1s responses during the warm; not independently re-verified from a raw log this pass (informational caveat only, not a finding). |
| Four sibling caches with the identical unfixed defect: `research.event_study_cached` (Research → Event Study, ~2 clicks), `market_phase.market_phase_cached` (rendered on the dashboard, 0 clicks), `forward_testing.compute_drawdown_expectations_cached` (the `/evidence` page's own drawdown-expectations panel, 1 click), `indexes.index_series_cached_with_status` (dashboard/Data Manager index chart, 0-1 click) | N/A — these are the OTHER existing ingest-time caches, confirmed (via the developer's own `grep`, cited in the dev handoff) to have **no lock/in-flight mechanism either** | **Not touched, not tested, not measured this iteration** — an explicit, disclosed scope decision (the fix was scoped to the one confirmed UT-04 culprit only), not an oversight | **Medium, disclosed but unevaluated.** Three of these four surfaces sit behind very prominent (0-1 click) navigation — if the SAME "N concurrent same-key MISSes redundantly recompute" pattern that produced `/backtest`'s 211.8s finding exists on any of them (structurally plausible, since none has ever had a de-dup guard), a user could hit an analogous multi-minute stall on the dashboard itself or on `/evidence`, with no fix in place. No live symptom has ever been reported on these four surfaces — this is a named, disclosed risk, not a confirmed live defect. |

**Required-still-passing journeys:** J-01, J-03, J-05 all re-verified PASS via deterministic golden replay
(`reports/phase-goal-ops-hardening-iter-15-regression-replay-results.md`, 3/3), and J-04 was carried
forward from iter-14's own live kill/restart pass plus this session's fresh steady-state sanity re-check
(`GET /api/health` ready/GO, badge `Ready`, Run History populated) — no regression in any of the four
required journeys' own core acceptance.

---

## UI vs Backend Parity

- **The single-flight de-dup fix** correctly stays invisible as a "new feature" — byte-identical output
  (TC-3, 32/32 unchanged), no new endpoint/field/schema. Appropriately unexposed, matching "New
  user-facing capability: None new."
- **Gap — not a hidden-capability problem, but a committed-budget parity problem:** the fix's real-world
  envelope is narrower than what `/backtest`'s own committed ≤1.5s budget (`perf-budgets.md`) promises.
  This is disclosed thoroughly and honestly across `user-visible-changes.md`, `ui-surface-map.md`, and
  `perf-budgets.md` (both the 178.7s cold-miss WARN and the newly-surfaced 5.37s spike WARN are recorded
  plainly, not rationalized away) — there is no "complete claimed but hidden" violation here, since the
  project's own artifacts already say "partially closed," not "closed." The gap is real and user-facing,
  not concealed.
- **No on-screen affordance distinguishes the resulting states** (fast de-dup-served waiter / one-time
  slow first-ever cold-miss / the new unexplained spike / the untouched sibling-cache risk) — a user
  sees the same skeleton and the same eventual result regardless of which case they hit. This is an
  explicit, previously-flagged (iter-14's own recommendation #2), and again explicitly deferred decision
  ("A `/backtest` elapsed-time/progress affordance — deferred; only needed if this iteration's fix does
  not materially close the latency gap"). **The evidence from this iteration's own live pass shows the
  gap was NOT materially closed** (178.7s vs. the original 211.8s is not a material reduction, and a new
  spike was found) — so the phase spec's own trigger condition for revisiting this affordance is now met,
  not merely hypothetical.

---

## Flags

### Hidden Capabilities
- None. No new backend capability lacks a UI entry point — nothing new exists to hide.

### Undiscoverable Capabilities
- None new. `/backtest`, `/data`, and `/evidence` are all existing, 1-click sidebar entries
  (`sidebar.tsx:37,41,44`, file unchanged); the global readiness badge requires 0 clicks. Nothing about
  this iteration changes reachability of anything.

### Potential Regressions
- **Job-progress heartbeat/`current_activity` cadence under long warms (ops-hardening iter-4's feature,
  previously flagged FAIL by iter-14's own ux-regression review as UT-10)** — not touched, not re-tested
  this iteration. Whether the reduced redundant-compute load shrank the "possibly stalled" false-alarm
  window, as the phase spec speculated it might, is unconfirmed either way.
- **`/evidence` page — a newly-surfaced 30-second timeout during the heaviest part of a concurrent warm**
  — first-ever measurement of this page under this specific load condition; not root-caused, not
  independently re-verified from a raw log, and the page's own on-screen degradation behavior during that
  wait is uncharacterized. `/evidence` is a top-level, 1-click nav page.
- **Four sibling ingest-time caches (event-study, market-phase, evidence's drawdown-expectations panel,
  index-series) carry the identical, structurally-confirmed "no de-dup on concurrent same-key MISS"
  defect `/backtest` had before this iteration** — untouched, unmeasured, on three surfaces reachable in
  0-1 clicks. Disclosed by the developer, not evaluated this iteration.
- **New, unexplained 5.37s `/backtest` spike** (epoch 1784818231) surfaced by this iteration's own
  recomputation of the operator's raw CSVs, not mentioned in the operator's own summary — a second,
  distinct budget breach (~3.6x over ≤1.5s) beyond the known 178.7s cold-miss case, cause undetermined.

### Visual Consistency
- N/A. Zero frontend files touched (confirmed via the ui-surface-map and dev handoff's `git status`
  citations) — no new page, component, or style exists to compare against the DESIGN SYSTEM. UT-07
  independently re-confirms the nav list and `/backtest`'s section order are byte-identical to iter-14's
  documented structure. Every established visual pattern (skeleton loader, badge states, error card) is
  byte-unchanged.

---

## Recommendation

1. **Do not treat `/backtest`'s concurrent-load reliability as fully closed.** The redundant-recompute
   pile-up this iteration targeted is confirmed fixed (proof: TC-1's 5→1 invocation count; the live pass's
   64 calls resolving independently, none stacked), but the page's own committed ≤1.5s budget remains
   violated in the exact trigger scenario measured (178.7s cold-miss, not materially different from the
   original 211.8s finding) plus a new unexplained 5.37s spike. Per the phase spec's own OUT-OF-SCOPE
   language, the elapsed-time/progress affordance was deferred "only if this iteration's fix does not
   materially close the latency gap" — this iteration's own evidence shows it did not, so that affordance
   (or a further root-cause pass on the residual 178.7s/5.37s numbers) should now be treated as
   ready-to-schedule for iter-16, not speculative.
2. **Root-cause the newly-surfaced `/evidence` 30-second timeout** before assuming it is unrelated noise —
   it was observed exactly once, on a top-level 1-click page, during the heaviest part of a load condition
   this page had never been tested under before.
3. **When convenient (no live symptom reported on any of them, so non-urgent), extend the confirmed
   single-flight de-dup pattern to the four sibling caches** carrying the identical, developer-confirmed
   unfixed defect (`event_study_cached`, `market_phase_cached`, `compute_drawdown_expectations_cached`,
   `index_series_cached_with_status`) — three of the four sit behind very prominent (0-1 click)
   navigation, so a future concurrent-warm incident on the dashboard or `/evidence` is structurally
   plausible, not merely theoretical.
4. **Re-measure the per-horizon heartbeat "possibly stalled" cadence** (iter-4's feature, iter-14's UT-10
   finding) now that the redundant-compute load behind it may be reduced — this iteration did not touch
   or re-test it, so its status is genuinely unknown, not fixed-by-inference.

No action is required on discoverability or navigation — both are unaffected and already correct. The
WARN verdict reflects real, honestly-disclosed, user-facing reliability gaps on an existing, budget-
committed feature (not a hidden capability, not a broken nav path, and not a regression in any of the four
required-still-passing journeys, all of which independently re-verified PASS).
