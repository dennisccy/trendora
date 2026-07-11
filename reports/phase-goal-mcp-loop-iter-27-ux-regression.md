# Phase goal-mcp-loop-iter-27 — UX Regression Review

**Date:** 2026-07-12

**Verdict:** UX-REGRESSION-PASS

---

## Summary

This is the re-review of iter-27 after the second (successful) fix pass. The first pass's ux-regression
review and the post-decompose audit both correctly FAILed on a **confirmed, reproduced regression**: the
target journey's own job (the full-universe "Rebuild snapshots" rebuild on `/data`) crashed the entire
backend with a `MemoryError` on a second consecutive run, taking every page and API down with it — a
critical anti-goal #8 violation. That defect is what this review exists to catch, and it did.

That defect is now fixed and independently re-verified live. `reports/phase-goal-mcp-loop-iter-27-ui-test-results.md`
(Verdict: PASS) drove **three** consecutive full-universe rebuilds (exceeding the required two) through the
real `/data` page — all three reached `status: "ok"`, 322/322 dates, with `/api/health` returning 200 at
every poll and `/stocks` rendering 541/541 populated rows afterward, proving the backend *process* survived,
not merely that individual requests happened to succeed. I independently confirmed both services are live
right now (`GET /api/health` → 200, `GET http://localhost:3255/` → 200) and that `git status`/`git diff`
show zero changes under `apps/frontend/` — consistent with the plan's "verification-only, no frontend source
change" framing.

No new user-facing capability was built this iteration (by design — a memory-hardening de-regression pass),
so Step 1 (discoverability) is trivially satisfied: there is nothing new to hide. Step 2 (regression) is
the substance of this review, and the one confirmed regression from the prior attempt is resolved and
re-verified by the canonical browser-qa lane, per the iter-24 lesson that an engine-level fix alone does not
count. Two pre-existing, non-blocking UX gaps (carried forward from the audit, not introduced by this
iteration) remain open by design and are noted below as advisory, not as reasons to fail this review.

---

## New Capability Discoverability

Nothing new to assess. Per the plan's "UI Evolution" section and `reports/phase-goal-mcp-loop-iter-27-user-visible-changes.md`:
"New user-facing capability: none... New information displayed: none... New user actions: none... UI
surface changes: none." Confirmed independently: `git diff --stat HEAD -- apps/frontend/` and
`git status --short apps/frontend/` both return empty. The only user-visible delta is behavioral (the
existing "Rebuild snapshots" job on `/data` — already reachable via the persistent sidebar's "Data Manager"
entry, 1 click from `/`, per UT-15 below — now completes instead of crashing). No navigation, label, or
new-entry-point question applies.

- **UT-15** (browser-qa, PASS): sidebar shows all 11 expected entries unchanged; "Data Manager" → `/data` in
  exactly one click; all 6 named panels present with unchanged titles ("Dataset coverage", "Storage
  footprint", "Rebuild snapshots for current universe", "Dynamic-universe membership timeline", "Start a
  fetch / backfill job", "Job progress"). Confirms the existing entry point survived this iteration
  untouched.

---

## Regression Risk

| Shared component touched | Prior feature it serves | Current-phase change | Verification this round | Risk |
|---|---|---|---|---|
| `apps/backend/app/engine/prices.py` (`_BarCache.bars_asof_window`, additive), `regime.py` (`_index_ma_stack`/`_universe_stats`/`_latest_vix` routed through windowed/`close_on` accessors) | Dashboard `RegimeGlanceCard` (Market Regime badge/score/breakdown) — J-04; every journey reading price/score data | Read-side windowing to bound per-`(symbol,date)` allocation (Item G, kept from the first pass) | **Verified live, PASS.** UT-06: badge "Risk-on", score "72.25/100", all 5 breakdown components populated, evidence link works. Byte-identity re-proven: `test_scoring_window.py` 4/4 (472.51s), including a windowed-vs-unwindowed `score_regime` comparison with an explicit vacuous-pass guard. | Low — byte-identity-gated and live-confirmed unchanged |
| `apps/backend/app/engine/scoring.py` (fallback lever 1: two slice sites routed through `bars_asof_window`) | `/stocks` leaderboard scores (J-01, J-03), `/stocks/{ticker}` score cards (J-10) | Mathematically identical two-step-slice replacement | **Verified live, PASS.** UT-07/UT-08: 541/541 rows, 1,623 "Not yet proven" badges (541×3), correct muted styling/tooltip. UT-10: AAPL scores populated (Leadership 55.78, Entry Quality 69.70, Risk 33.12), full-history chart continuous 1996→2026, no fabrication. | Low — byte-identity-gated and live-confirmed unchanged |
| `apps/backend/app/engine/data_manager.py` (`_release_process_memory()` in `_do_backfill`'s `finally`; `server.malloc_arena_max` + `MALLOC_ARENA_MAX` export in `start-backend.sh`) | **The exact regression this review previously FAILed on**: J-16's "Rebuild snapshots" job, and by extension every journey that depends on the backend process staying up after a heavy job (all 8 required-still-passing journeys) | Allocator-arena cap + explicit `gc.collect()`/`malloc_trim(0)` between jobs — targets cross-job VSZ accumulation, the root cause the audit traced (`docs/handoffs/goal-mcp-loop-iter-27-audit.md` finding B2) | **Confirmed RESOLVED, not merely potential.** UT-02 (centerpiece): 3 consecutive full-universe rebuilds, all `status:"ok"`, 322/322, `/api/health` 200 throughout including at the deep-history dates (2026-06-10, 2026-07-01) where the pre-fix crash occurred. `reports/perf-budgets.md` Item H: VmPeak 5,147,876 KB on **both** runs (no growth) vs. the pre-fix run 2 pinning at the 6,291,456 KB ceiling and crashing. | **Resolved** — was High/Confirmed in the prior review, now verified fixed |
| `/data` job-progress surface (`JobProgressPanel`, unchanged source) | Anti-goal "never report done early" | No source change; re-verification only | UT-03 PASS: counter climbed monotonically across all 3 runs (e.g. 0→1→2→3→4→4→32→100→155→199→237→272→307→322), `status` stayed `"running"` until `dates_done == dates_total` on the same poll | Low — unchanged code, honest behavior re-confirmed |

### 8 required-still-passing journeys (carried SKIPPED through iter-26's outage) — re-verification status

All 8 were re-driven live this round and PASSed: J-01/J-03 (`/stocks` leaderboard + unproven badges — UT-07,
UT-08), J-04 (Dashboard regime — UT-06), J-05 (`/evidence` ledger — UT-09), J-10 (AAPL full-history — UT-10),
J-12 (membership timeline entries/exits — UT-11), J-13 (Data Manager legend/panels — UT-15), J-15 (perf
budgets — UT-12). This closes the gap the prior review flagged ("none of the 8 required-still-passing
journeys were verified this iteration... they were SKIPPED, not passed").

### Verification gap worth surfacing (not a confirmed regression)

- **UT-01 / UT-13 / UT-14 (cold-start-first `/data` repro, and the "Backend unavailable" contained-card
  degradation) were SKIPPED by the canonical browser-qa lane** this round — the agent was denied permission
  to stop/restart the coordinator-managed backend process (verified no side effect occurred). This matters
  because the project's own standing lesson (iter-24, restated in this iteration's NOTES) is explicit: "a
  critical anti-goal fix applied after the canonical browser-qa lane ran must be re-verified by that lane...
  an engine-level ablation fix alone is NOT sufficient." The dev handoff's Fix Notes section reports a cold
  `/api/data` no-OOM repro ×2 that did pass (VmPeak ~3.5 GB, backend alive, byte-identical capacity) — but
  that was run by the developer against a throwaway DB copy, not the canonical browser-qa lane against the
  live `/data` page. The "Backend unavailable" contained-card boundary (the iter-25 UI behavior this
  iteration's spec explicitly calls out as the required degraded state) was therefore not re-exercised live
  this round either. This is an environment/permission constraint, not an observed defect — no failure was
  seen, only an untested path — so it does not change the verdict, but it is a real coverage gap the next
  iteration's QA setup should close (grant the browser-qa agent backend-lifecycle permission, or have the
  coordinator perform the stop/cold-start steps on the agent's behalf).

---

## UI vs Backend Parity

No new backend capability exists to surface. Per `ui-surface-map.md`'s "Backend-Only Changes" section, every
changed backend symbol (`bars_asof_window`, the `regime.py`/`scoring.py` routing, `_release_process_memory`,
`server.malloc_arena_max`) is an internal compute-path or process-lifecycle change beneath already-registered
values (scores, regime score, forward returns, bars, `data_manager.compute_availability`/`compute_coverage`/
`compute_capacity`), each re-serving byte-identically from its existing single computing module and single
serving endpoint. There is no "backend says complete, UI says not visible yet" gap — the implementation
summary and user-visible-changes report agree exactly: no new endpoint, no new displayed value, no nav
change. The only new artifact is `reports/perf-budgets.md`'s "Item H" section, which the phase spec correctly
scopes as a committed engineering report, not a UI value.

---

## Flags

### Hidden Capabilities
None — no new capability shipped this iteration.

### Undiscoverable Capabilities
None — no new capability shipped this iteration.

### Potential Regressions
None confirmed. The one CONFIRMED regression from the prior attempt (full-universe rebuild crashing the
backend on a second consecutive run — anti-goal #8) is resolved and re-verified live via 3 consecutive
successful rebuilds plus all 8 required-still-passing journeys re-driven PASS on the fixed build. See
"Verification gap worth surfacing" above for the one non-blocking coverage gap (cold-start/backend-down path
not re-exercised by the canonical lane this round, due to a permission denial, not an observed failure).

### Potential Regressions — Advisory (pre-existing, non-blocking, carried forward by design)
These two items were already flagged in the iter-27 audit (finding F1) as non-blocking observations, and the
coordinator's plan explicitly defers them to a future iteration rather than this memory-hardening pass. They
are pre-existing gaps, not something this iteration's diff introduced or worsened, and no frontend source
change was in scope this iteration:
- **No `/data` guardrail against re-clicking "Rebuild snapshots" a second time.** Nothing in the button
  state, `RebuildConfirmModal` copy, or a rate-limit currently discourages an operator from starting a second
  full-universe rebuild back-to-back. The backend now genuinely sustains this (re-verified 3× live this
  round), so the practical risk this represented is gone — but the UI still gives no explicit signal that
  this was ever a fragile operation, which is a minor honesty/affordance gap worth a future pass.
- **No client-side timeout on the readiness poll for a wedged (TCP-accepting-but-unresponsive) backend.** If
  the backend were ever to wedge again, `/data` would show a perpetual "Checking backend…" skeleton rather
  than degrading to the established iter-25 "Backend unavailable" contained card. This did not manifest this
  round (the backend did not wedge), so it was not exercisable, but it remains an open gap in the graceful-
  degradation contract.

### Visual Consistency
Not applicable — zero frontend files changed (`git diff --stat HEAD -- apps/frontend/` empty). No new page or
component to assess against the design system; every existing page's styling is byte-for-byte unchanged.

---

## Recommendation

No action required to close this iteration. For future iterations:
1. When a critical anti-goal fix needs the cold-start/backend-restart repro (UT-01/13/14 class of test),
   ensure the browser-qa agent's dispatch has backend-lifecycle permission, or have the coordinator perform
   the stop/cold-start steps directly — this round's SKIP (not FAIL) leaves that specific degradation path
   unexercised by the canonical lane.
2. Non-blocking, carried forward from the audit: add a `/data` guardrail (disable/rate-limit) against a
   redundant second "Rebuild snapshots" click, and a client-side readiness-poll timeout so a wedged backend
   resolves to the "Backend unavailable" card instead of a perpetual loading skeleton.
