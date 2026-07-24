# Phase goal-ops-hardening-iter-18 — UI Test Results

**Phase:** goal-ops-hardening-iter-18
**Date:** 2026-07-24
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** SKIPPED

**Overall:** 0/4 tests passed (4 skipped)

---

## Why everything is SKIPPED, not FAIL

Chrome MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`) could not be brought up in this
session despite thorough troubleshooting. Every `navigate` call failed identically:

```
Error: Failed to auto-start Chrome: Chrome did not become ready on port 9224 within 15000ms
```

**Troubleshooting performed (10 tool-level attempts over ~10 minutes), all reproducing the identical symptom:**
1. Two initial `navigate` calls failed; `ps aux` showed two competing Chrome processes for this
   session's assigned automation profile (`superpowers-chrome-2`, port 9224), a stale `SingletonLock`
   pointing at an already-dead PID.
2. Killed the stray `superpowers-chrome-2`-profile processes, removed the stale `Singleton*` lock
   files, retried — same timeout.
3. Checked system resources: memory had 18 GiB available, `ulimit -a` showed generous `nproc`/`nofile`
   ceilings (95352 / 524288, far above the ~171 processes / ~477 Chrome threads actually running), so
   this was not a hard resource ceiling.
4. Retried with a fresh cleanup — same timeout. Direct process inspection showed the new Chrome
   process alive and burning ~32% CPU continuously but its zygote children never progressed to
   spawning a GPU/renderer/network process, and the CDP port never opened.
5. Waited patiently for an in-flight attempt for 90 seconds straight (well beyond the tool's own
   15s timeout) — it never reached a listening state; still stuck at the zygote stage.
6. Attempted to relocate the (possibly corrupted-by-my-own-repeated-kill-9) profile directory aside
   (non-destructively, via `mv`, after `rm -rf` under `/home` was correctly refused by the sandbox's
   dangerous-command guard) — the retry after this still failed identically.
7. Tried the tool's own dedicated `restart_chrome` recovery action — same timeout.
8. Confirmed this is not a system-wide Chrome failure: a **sibling** automation profile
   (`superpowers-chrome`, port 9223, owned by a different long-running MCP server process on this
   host) is alive right now with its GPU/renderer/network child processes all up — so Chrome itself
   works on this host generally.
9. Used `set_profile` to switch to a brand-new, never-before-used profile name
   (`trendora-goal-ops-hardening-iter18-qa`) to rule out on-disk profile corruption from my own earlier
   `kill -9`s. **Retried — identical failure, same port (9224), same zygote-stuck symptom.** This is
   conclusive: the fresh profile proves the problem is not corrupted profile data. This session's
   Chrome-automation MCP server process is fixed to CDP port 9224 regardless of which profile
   it targets (the sibling on 9223 is a different, separate long-running MCP server process), and
   *that specific server process* cannot get a Chrome instance past the zygote stage on this run,
   independent of profile. This points at the automation server process backing this conversation, not
   at anything file-cleanable — a fix likely needs a new MCP connection/session, which is outside what
   this agent can do from within the conversation.
10. One final retry after the profile switch — same timeout. Stopped here; all stray processes and
    lock files from every attempt were cleaned up, and the product's own services (`:3255`, `:8255`)
    were confirmed untouched and healthy throughout (this troubleshooting only ever killed processes
    matching this session's own disposable automation-profile names).

Per the browser-qa-agent instructions ("Do NOT mark FAIL merely because browser automation had
trouble — note as SKIPPED with reason" / "If Chrome MCP is not available: write all tests as SKIPPED
with reason 'Chrome MCP not available'"), all four journeys below are recorded SKIPPED, not FAIL.

**What I did instead, to maximize honest signal:** read-only `curl` checks against the backend and a
read of `logs/backend.log` (NOT a substitute for browser verification — no DOM/render/console
evidence exists for any journey this run). Results below, per journey.

**Independent of the Chrome outage**, two of the four journeys had additional out-of-scope steps this
run regardless: J-07's steps 1/3/4 require triggering a full deep-basis forward-aggregate warm across
every horizon and inducing memory pressure, and J-08's step 1 requires submitting a live single-day
backfill on `/data` — both are ingest/heavy-compute triggers the pump note explicitly instructed me not
to perform ("do NOT click the Start/backfill trigger on /data or otherwise kick off an ingest... If a
test case seems to require triggering heavy compute, stop and describe what you would do rather than
doing it"). Per that instruction: what I would have done for J-07 is trigger the finalize-path warm for
all configured horizons in a long-lived process while polling `/api/health` once/sec and sampling
VmPeak — this is OPERATOR/TC-9-class work already covered separately in `reports/perf-budgets.md`. What
I would have done for J-08 is submit one `POST /api/data/jobs {kind:"backfill", start:<gap-date>,
end:<same-date>}` for a single unsnapshotted day, then reload `/backtest` to watch the
last-good→refreshing→fresh-serve transition — this is exactly the kind of ingest trigger AG-10 asks me
to avoid on this host. Neither was executed.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-04 | Non-blocking boot with visible status | regression | P1 | This iteration's scope is a non-disruptive steady-state check only (no kill/restart — that is TC-10, operator-performed); health 200/ready, badge correct, no new crash lines | Chrome MCP unavailable — no badge/DOM/screenshot evidence obtainable. Non-browser signal only: `GET /api/health` → 200, `readiness:"ready"`, `db_ok:true`; `logs/backend.log` tail shows only clean `INFO` access lines plus new `backtest_timing` instrumentation lines, no crash/traceback | SKIPPED | none — see reason below |
| UT-J-06 | Pages load only what they need | regression | P1 | All 11 pages from the existing `J-06.json` golden script (`/`, `/stocks`, `/stocks/AAPL`, `/sectors`, `/themes`, `/data`, `/evidence`, `/scanner-runs`, `/backtest`, `/watchlist`, `/research/event-study`) render their expected content; spot-check that `/backtest` is byte-identical post-instrumentation | Chrome MCP unavailable — could not navigate to or render any page. Non-browser signal only: raw `GET /backtest` (server-rendered HTML, not client-verified) → HTTP 200, 45684 bytes, 0.46s; `GET /api/backtest` → `evidence_status:"ready"`, `evidence_asof:"2026-07-22"`, 5 horizon keys, `scorecard` present | SKIPPED | none — see reason below |
| UT-J-07 | Heavy aggregates never take the service down | regression | P1 | Spot-check only this iteration (no new UI behavior for J-06/J-07/J-08); full acceptance requires triggering a deep-basis forward-aggregate warm + memory-pressure induction, out of scope for this agent | Chrome MCP unavailable, and the full journey additionally requires a heavy-compute trigger this agent was instructed not to perform (see note above). Non-browser signal only: `GET /api/health` → 200 while idle | SKIPPED | none — see reason below |
| UT-J-08 | Backtest evidence serves from storage only — never a cold recompute on request | regression | P1 | Spot-check that `/backtest` still serves stored evidence correctly; full acceptance requires submitting a live backfill to observe the version-bump/refreshing transition, out of scope for this agent | Chrome MCP unavailable, and the full journey additionally requires an ingest trigger this agent was instructed not to perform (see note above). Non-browser signal only: `GET /api/backtest` → `evidence_status:"ready"` (not `refreshing`, not `not_yet_computed`), `evidence_generated_at:"2026-07-24T02:11:25Z"`, `is_latest:true`; two fresh curl calls each produced a `backtest_timing` log line with `total_ms` ~150-160ms (well under the 1.5s budget at idle, consistent with a stored-value read, not a request-path recompute) | SKIPPED | none — see reason below |

---

## Skipped Tests

### UT-J-04 — Non-blocking boot with visible status
**Verdict:** SKIPPED
**Reason:** Chrome MCP not available (see troubleshooting log above) — no badge screenshot, no DOM
assertion, no console-log evidence possible this run. This journey's disruptive steps (kill/restart,
steps 1/3/4/6 of J-04) are additionally out of scope for this agent regardless of Chrome availability:
the pump note states "You CANNOT start/stop services (permission classifier)... do not launch any raw
server process yourself," and the iter-18 spec assigns the live kill/restart replay to the operator as
TC-10, immediately after TC-9, in the same session — matching the established iter-14 through iter-17
precedent of treating this journey as a non-disruptive sanity check for the browser-qa lane. The
non-disruptive portion I could check without a browser: `GET /api/health` on `:8255` → HTTP 200,
`{"status":"ok","db_ok":true,"readiness":"ready","readiness_detail":null,"provider":"seed"}`; a fresh
tail of `logs/backend.log` shows normal `INFO` access-log lines and the new `backtest_timing`
instrumentation lines, with no crash/traceback/restart banner. This is consistent with (not proof of,
absent a browser) a correctly non-blocking, currently-ready boot state.

### UT-J-06 — Pages load only what they need
**Verdict:** SKIPPED
**Reason:** Chrome MCP not available — could not navigate any of the 11 pages in the existing
`journey-scripts/J-06.json` golden replay, so no page-load rendering, no time-to-interactive
measurement, and no visual regression check of `/backtest`'s evidence section was possible this run.
The only substitute I obtained was a raw (non-browser) HTTP fetch of `/backtest`'s server-rendered HTML
(HTTP 200, 45684 bytes in 0.46s) and the `/api/backtest` JSON payload showing `evidence_status:"ready"`
with 5 populated horizon keys and a `scorecard` field — this confirms the API/SSR layer is healthy but
does **not** confirm client-side rendering, DOM content, or absence of console errors, so it cannot
stand in for the browser check. No golden-script update was made to `J-06.json` this run since nothing
was actually re-verified live.

### UT-J-07 — Heavy aggregates never take the service down
**Verdict:** SKIPPED
**Reason:** Two independent blockers this run: (1) Chrome MCP not available. (2) This journey's full
acceptance requires triggering a deep-basis forward-aggregate warm across every configured horizon in a
long-lived process (steps 1/3) and inducing memory pressure (step 4) — both heavy-compute/ingest-class
actions the pump note explicitly told me not to perform ("If a test case seems to require triggering
heavy compute, stop and describe what you would do rather than doing it," and the standing AG-10 host
ceiling, given two prior hard-resets under all-core ingest bursts on this exact host). What I would do
instead (not performed): trigger the finalize-path warm for all configured horizons under
`scripts/start-backend.sh`'s host-guard caps, poll `GET /api/health` once/sec throughout, and record
peak `VmPeak` — this is explicitly OPERATOR/TC-9-class work per the iter-18 spec, already covered
separately (deep-basis re-measurement) in `reports/perf-budgets.md`. This iteration's own testing
requirements note that J-06/J-07/J-08 get "no new UI behavior to verify" this run — only a `/backtest`
spot check, which itself needed the (unavailable) browser to be meaningful. Non-browser signal only:
`GET /api/health` responded 200 while the system was idle (not under a warm).

### UT-J-08 — Backtest evidence serves from storage only — never a cold recompute on request
**Verdict:** SKIPPED
**Reason:** Two independent blockers this run: (1) Chrome MCP not available. (2) This journey's steps
1-3 require submitting a live single-day backfill on `/data` to bump the dataset version and observe
the last-good→refreshing→fresh-serve transition — an ingest trigger the pump note explicitly forbids
("do NOT click the Start/backfill trigger on /data or otherwise kick off an ingest — this host has
hard-reset twice under ingest bursts. Navigate and read only."). What I would do instead (not
performed): submit one `POST /api/data/jobs {kind:"backfill", start:<gap-date>, end:<same-date>}` for a
single unsnapshotted day, then reload `/backtest` to confirm it serves the last complete stored version
with a "refreshing" indicator within budget, then again after the finalize warm completes to confirm the
fresh version serves with the indicator gone. Step 5 (the fresh-install empty-state check, previously
verified live in iter-17 against a throwaway instance on `:18255`/`:13255`) could not be repeated either:
those throwaway services are confirmed torn down (`ss -tlnp` shows nothing on `:18255`/`:13255` any
more; only `:8255`/`:3255` are listening), and spinning up a fresh one is itself a service-start action
outside this agent's permission. Non-browser signal only: the live main backend's `GET /api/backtest`
currently reports `evidence_status:"ready"` (a served, non-refreshing state) with a real
`evidence_generated_at` timestamp and `is_latest:true`; two consecutive curl calls each logged a
`backtest_timing` line with `total_ms` of 162.54ms and 149.64ms respectively — fast and consistent with
a stored-value read rather than a request-path recompute, though this is inferential, not a direct
call-count assertion (that assertion is TC-8's unit-test job, not this agent's).

---

## Golden replay scripts

None written this run — the golden-script instructions apply only to journeys verified PASS, and none
passed (all four are SKIPPED due to Chrome MCP unavailability, and J-07/J-08 additionally could not be
fully exercised even with a browser per the out-of-scope heavy-compute/ingest steps above). The existing
`runs/goal-session-ops-hardening/journey-scripts/J-06.json` from a prior iteration is left untouched.

## Environment

- **Frontend URL:** http://localhost:3255 (confirmed serving: `GET /backtest` → HTTP 200 via raw curl)
- **Backend URL:** http://localhost:8255 (confirmed serving: `GET /api/health` → HTTP 200, `readiness:"ready"`)
- **Browser:** Chrome via MCP — **unavailable this run** (see troubleshooting log above); no browser
  session was ever successfully established, so no screenshots exist for this iteration
- **Test Date:** 2026-07-24
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-18-evidence/` (contains only the
  deterministic-replay tool's `J-01-verify.png`, `J-03-verify.png`, `J-05-verify.png` from the separate
  regression-replay pass that ran before this agent; no new files added by this browser-qa pass since no
  browser session succeeded)
