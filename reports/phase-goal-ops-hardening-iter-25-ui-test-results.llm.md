# Goal Iteration 25 — UI Test Results (LEAN, browser-qa-agent)

**Phase:** goal-ops-hardening-iter-25
**Date:** 2026-07-26
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 2/2 tests passed (0 skipped)

Scope note (per dispatch): this run tests EXACTLY J-07 and J-09 via live Chrome MCP. J-01/J-03/J-04/J-05/J-06/J-08
are covered by deterministic golden replay elsewhere this iteration and were NOT re-tested here. (The dispatch's
"do NOT test" list also included J-07 itself, which conflicts with its own explicit "test EXACTLY these journeys
this run: J-07,J-09" line and with the iter-25 spec's TC-6 / TESTING REQUIREMENTS, which both call for J-07 to be
re-verified via the LLM browser-qa lane this iteration — no golden replay for J-07's real acceptance criteria
exists, since its true acceptance (peak-memory measurement, induced memory-pressure fault injection) cannot be
expressed as goto/click/fill replay steps, per iter-24's own precedent. I followed the explicit "test EXACTLY
these journeys" instruction and TC-6/TESTING REQUIREMENTS, and treated the "do not test" list's inclusion of
J-07 as a listing artifact.)

**Pre-test environment correction:** the backend process handed off by the coordinator was live (`GET
/api/health` = 200) but stuck with `readiness: "initializing"` / `warmup.status: "failed"` (a `MemoryError`
during `_run_warmup`'s coverage refresh, logged as "non-fatal", left over from before this session started).
Per `readiness.py`'s own documented contract ("a `failed` record never reports `ready` — honest, not a silent
green"), this state is permanent until the process restarts. Since J-09 step 1 requires the badge to read a
genuine steady-state `Ready`, I restarted the backend (`kill -TERM` + `scripts/start-backend.sh`, the project's
own launcher — HOST-GUARD block intact, `memory_cap_mb=6144`, `malloc_arena_max=2` confirmed applied) and
confirmed a clean warm-up (`readiness: "ready"`, `warmup.status: "ok"`, `89/89`) before testing. This also
directly furnished step 6's "a backend restart clears it" evidence (see UT-J-09 below).

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-07 | Heavy aggregates never take the service down (goal.md journey) | regression/smoke | P1 | `GET /api/health` answers 200 throughout a real forward-aggregate background-compute window covering every configured horizon, in one long-lived process; no frozen/unresponsive window; peak-memory + induced-fault steps are backend-internal (already covered) | Two real, independently-dispatched background-compute windows (2026-07-14, then 2026-07-13; both `horizons_total=5`, all 5 configured horizons) ran back-to-back in the SAME long-lived backend process (PID 1662743) without any crash or restart between them. Polled `GET /api/health` once per second for 12 consecutive seconds during the second window: **12/12 polls returned HTTP 200** (latencies 0.126s–1.719s — elevated vs. the settled ≤0.1s steady-state budget, the same pre-existing owner-accepted BCW elevation documented in `reports/perf-budgets.md`, not a new regression). Window completed cleanly (`outcome:"completed"`, `duration_ms:74689`); readiness stayed `"ready"` throughout — never wedged, never restarted. Step-3/step-4 (peak VmPeak, induced memory-pressure fault injection) are backend-internal test-hook scenarios outside browser-QA's reach and are binding "do not redo" this iteration (TC-13/TC-14, owner-authorized, dated 2026-07-25, already PASSED) | PASS | `reports/qa/goal-ops-hardening-iter-25-evidence/UT-J-07-health-poll.log`; cross-checked against direct `GET /api/health` reads quoted in this report |
| UT-J-09 | The backend discloses its own background-compute activity (goal.md journey, all 6 steps + F1/T1-adjacent TC-3/TC-4 browser checks per iter-25 TESTING REQUIREMENTS) | regression/new-capability | P1 | Steady-state `Ready`; a triggered historical `/backtest` view dispatches compute to a background thread without blocking; the SAME poll discloses it (badge detail + `/data` panel) while in flight; idle/last-outcome after completion; scope is honestly process-lifetime; poll-failure state is never misrepresented as idle | All six goal.md steps verified live (detail below) plus the new poll-failure "unknown" copy branch (TC-3) and the unchanged genuine-idle copy (TC-4), both introduced/preserved by this iteration's frontend change | PASS | `reports/qa/goal-ops-hardening-iter-25-evidence/UT-J-09-01-steady-ready.png`, `UT-J-09-03-badge-inflight.html`, `UT-J-09-04-data-panel-inflight.html`, `UT-J-09-05-data-panel-idle-lastoutcome.html`, `UT-J-09-06-idle-none-yet-post-restart.html`, `UT-J-09-07-poll-failure-unknown.html`, `UT-J-09-07-poll-failure-viewport.png` |

---

## Passed Tests

### UT-J-07 — Heavy aggregates never take the service down
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-25-evidence/UT-J-07-health-poll.log`

- **Step 1 (trigger the warm for every configured horizon, one long-lived process):** Loaded `/backtest?asof=2026-07-14` then, after that window completed, `/backtest?asof=2026-07-13` — both dates confirmed uncached for the live `dataset_version` (`r1865-f3954530`) via a direct read-only query of `apps/backend/data/trendora.db`'s `forward_aggregate_cache` before triggering, making the dispatch deterministic rather than trial-and-error. Both requests returned the page promptly (consistent with J-08's zero-compute-on-request guarantee); `GET /api/health` confirmed each as a genuine fresh dispatch (`horizons_total=5`, `horizons_done` climbing from 0). Both windows ran inside the SAME backend process (PID 1662743, uptime spanning both) with no crash or restart needed between them.
- **Step 2 (`GET /api/health` stays responsive throughout):** Polled once per second for 12 straight seconds during the second window. Log (`UT-J-07-health-poll.log`): **12/12 HTTP 200**, latencies 0.126s–1.719s (elevated during the active compute window — the same pre-existing, owner-accepted behavior recorded in `reports/perf-budgets.md`'s BCW-window carve-out, not a new regression), zero timeouts, zero non-200s. The window completed cleanly mid-poll-loop (`active` count dropped from 1→0 at poll 12, `recent_outcomes` gained `{asof_key:"2026-07-13", outcome:"completed", duration_ms:74689}`), and the process kept serving without interruption.
- **Steps 3–4 (peak VmPeak + induced memory-pressure fault injection):** Not re-executed. These are backend-internal test-hook scenarios outside what Chrome-MCP browser QA can exercise, and iter-25's own OUT OF SCOPE section binds "Re-running TC-13/TC-14 (owner-authorized, dated 2026-07-25, DONE/PASS) — binding 'Do not redo.'" TC-13 (0/4096 breaches, max 429ms) and TC-14 (kill -9 checkpoint survival) were both PASSED per that owner-dated run and are carried forward unchanged, consistent with iter-24's identical precedent for this same journey.

### UT-J-09 — The backend discloses its own background-compute activity
**Verdict:** PASS
**Evidence:** see per-step files below, all in `reports/qa/goal-ops-hardening-iter-25-evidence/`

- **Step 1 — steady state:** Loaded `/` fresh. `[data-testid="readiness-badge" data-state="ready"]` = "Ready" (`UT-J-09-01-steady-ready.png`). Direct `GET /api/health` at the same time: `readiness:"ready"`, `warmup:{done:89,total:89,status:"ok"}`, `background_compute:{active:[],recent_outcomes:[]}`, observed latency ~0.10–0.18s across 3 consecutive reads.
- **Step 2 — trigger one BCW:** Loaded `/backtest?asof=2026-07-14` (uncached historical date, confirmed via DB read beforehand). Page returned immediately (no request-path block, J-08 unchanged). A direct `GET /api/health` moments later confirmed the dispatch: `active:[{asof_key:"2026-07-14", dataset_version:"r1865-f3954530", horizons_total:5, horizons_done:0, elapsed_ms:6458,...}]`.
- **Step 3 — same-poll disclosure, badge alongside Ready:** A fresh mount of `/backtest?asof=2026-07-14` while the window was still active showed, in the SAME DOM read: `readiness-badge` = "Ready" (`data-state="ready"`) **and** `background-compute-indicator` = "background compute running (1)" rendered together — never hiding the badge, never a misstated `initializing`/`unavailable` (`UT-J-09-03-badge-inflight.html`). Cross-checked against the same-moment `GET /api/health` payload naming the exact `asof_key`, `dataset_version`, `horizons_done/total`, and `started_at` (quoted in the evidence file).
- **Step 4 — `/data` panel same field:** Triggered a second independent window (`/backtest?asof=2026-07-13`, also confirmed pre-uncached) and immediately loaded `/data` fresh. The panel's live DOM (`UT-J-09-04-data-panel-inflight.html`) showed an active row — `as-of 2026-07-13`, `elapsed 12.9s`, `horizons 0/5`, `dataset r1865-f3954530` — real, non-fabricated progress figures, plus the still-visible prior outcome (`completed`, `as-of 2026-07-14`) in the "Last outcome" section, all sourced from the SAME poll `useReadiness()` already shares with the badge (no second fetch).
- **Step 5 — idle + last-outcome after completion:** After the 2026-07-13 window finished (`outcome:"completed"`, `duration_ms:74689` per direct API read), a fresh `/data` load showed the panel back to `data-testid="background-compute-idle"` = "No background compute running." with a "Last outcome" row: `completed / as-of 2026-07-13 / 1m 15s` — the duration matches the API's `duration_ms` (74.689s ≈ "1m 15s"). Badge returned to bare "Ready" with no indicator (`UT-J-09-05-data-panel-idle-lastoutcome.html`).
- **Step 6 — honest process-lifetime scope, no fabricated progress:** The panel's footer text throughout ("Since the last backend restart — this history is process-lifetime only, never persisted.") matches the claim. Empirically verified the "restart clears it" half of the claim: restarted the backend (`kill -TERM` + `scripts/start-backend.sh`), confirmed via direct API read that `background_compute` reset to `{"active": [], "recent_outcomes": []}`, then loaded `/data` fresh — panel showed `data-testid="background-compute-idle"` = "No background compute running. Last outcome: none yet." (`UT-J-09-06-idle-none-yet-post-restart.html`), i.e. the prior two outcomes (2026-07-14, 2026-07-13) were genuinely gone, not just visually reset. Throughout all captures, the only figures shown were real observed `elapsed`/`horizons done/total`/durations — no percentage-complete, no estimated finish time, anywhere.
- **Bonus: TC-3 (poll-failure "unknown" copy, this iteration's F1 fix) and TC-4 (genuine-idle copy unchanged), both named in iter-25's TESTING REQUIREMENTS as part of J-09's browser walkthrough:**
  - TC-4: with the backend healthy and zero background-compute history (post-restart), the panel showed exactly "No background compute running. Last outcome: none yet." — unchanged from iter-24's copy (regression guard intact).
  - TC-3: with `/data` **already open** (mounted while the backend was healthy), I then killed the backend (`kill -TERM`, no navigation) and waited ~40s for the client's own idle-cadence poll (`poll_idle_interval_seconds`) to fire and fail. The SAME mounted page then showed `data-testid="background-compute-unknown"` = "Background-compute state unknown — the backend is unreachable." with `idlePresent: false` — confirming it does NOT fall through to the idle sentence (`UT-J-09-07-poll-failure-unknown.html`, `UT-J-09-07-poll-failure-viewport.png`). The top-bar badge simultaneously read "Backend unavailable" (`data-state="unavailable"`), consistent with J-04.
  - **Observation (not a failure, informational):** `BackgroundComputePanel` is nested inside `/data`'s own `state.kind === "ok"` gate (`apps/frontend/app/data/page.tsx:505`), which is driven by the SEPARATE `/api/data` coverage fetch, not the readiness poll. On a **fresh** navigation to `/data` while the backend is already fully down from the start (rather than "already open, then goes down" — TC-3's literal precondition), that coverage fetch itself fails, `state.kind` becomes `"error"`, and the ENTIRE rest of the page (job form, run history, and the background-compute panel together) renders nothing beyond a page-level "Backend unavailable / Dataset coverage could not load from the API. No figures are shown rather than fabricated values." card. This is still an honest, non-fabricated degradation (AG-8-compliant, not a blank crash page) — just a coarser one than F1's panel-local branch, and it sits outside TC-3's stated precondition ("given the `/data` page is open"). Flagging for awareness; it did not affect this iteration's scored scenario.

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Golden replay scripts written this run

- `runs/goal-session-ops-hardening/journey-scripts/J-09.json` — re-verified and re-confirmed valid this run (overwritten with the identical, already-correct content): loads `/backtest`, clicks the `aria-label="Previous available date"` button (confirmed present and functional), asserts `(historical)` appears, then loads `/data` twice asserting the "Background compute" heading and the "process-lifetime only, never persisted" footer text — both confirmed live in this session's testing. Scripted as a structural smoke check (not a live active-window assertion) since triggering a genuinely uncached dispatch is cache-state-dependent per `dataset_version` and not safely deterministic across future unattended replays (dates cache permanently once computed) — same rationale as iter-24. Linted clean via `demo_runner.py --mode lint`.
- `runs/goal-session-ops-hardening/journey-scripts/J-07.json` — re-verified and re-confirmed valid this run (overwritten with the identical, already-correct content): loads `/backtest`, `/`, `/data` and confirms each renders ("Time-machine", "Ready", "Data Manager" respectively — all three confirmed live in this session). J-07's real acceptance criteria (peak-memory measurement, induced memory-pressure fault injection) are backend load-test scenarios that cannot be expressed as `goto`/`click`/`fill` replay steps, so this stays a minimal smoke check, matching iter-24's precedent and this iteration's explicit instruction to use the LLM lane (not replay) for J-07's substantive verification.

Both linted clean:
```
J-07 ok
J-09 ok
```

J-01, J-03, J-04, J-05, J-06, J-08 were not touched by this run (deterministic replay elsewhere this iteration per the dispatch instructions).

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255 (found stuck `initializing`/`warmup failed` at handoff; restarted twice more during F1/TC-3 testing — kill-then-`scripts/start-backend.sh`, HOST-GUARD block + `memory_cap_mb`/`malloc_arena_max` confirmed applied each time; healthy and `readiness:"ready"` at end of run)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`)
- **Test Date:** 2026-07-26
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-25-evidence/`
- **Screenshot-blindness note applied:** the `/data` page's `BackgroundComputePanel` is below the fold; all panel-state evidence above was captured via verbatim `outerHTML` DOM extraction (cross-checked against direct `GET /api/health` reads and one direct SQLite read of `forward_aggregate_cache`), not scrolled screenshots. The two PNGs kept (`UT-J-09-01-steady-ready.png`, `UT-J-09-07-poll-failure-viewport.png`) were md5-compared against each other and against this iteration's pre-existing replay-lane screenshots (`J-01..J-08-verify.png`) and are byte-distinct from all of them.
