# Phase goal-ops-hardening-iter-50 — User-Visible Changes

**Phase:** goal-ops-hardening-iter-50
**Date:** 2026-08-05
**Written by:** ui-impact-analyst

---

## Context

`plan.md` and the phase spec both set `Frontend Present: no`, and the dev handoff confirms zero files
under `apps/frontend/` were touched — the three changed product files are
`apps/backend/app/engine/{research.py,data_manager.py,warmup.py}` plus backend test files and
`reports/perf-budgets.md`. Despite that, the phase spec's own "Product surface delta" section (not "None")
describes a real, observable reliability change to two already-existing pages — the SAME classification
precedent iter-49 used in this session — so this is scored as a genuine (if narrow, indirect) user-visible
change, not a pure backend-only phase. No component, page, label, field, or button was added, removed, or
renamed anywhere.

This iteration is the direct continuation of iter-49's own live incident: iter-49 fixed its own scoped
finalize-tail work but the backend then DIED for 12m45s during that same round's browser lane, caused by
three concurrent heavy loops — the ingest finalize tail, the boot re-warm's `_warm_drawdown_expectations`,
and a live `/research/factor-lab` page view whose `compute_factor_lab_all` raised an uncaught `MemoryError`
that actually killed the process. Iter-50 closes exactly that crash frame, interlocks the two background
warms so they never race for memory, and (as a small same-subsystem companion fix) skips an unconditional
~24-second precompute when nothing needs it.

---

## What Users Can Now Do

- View `/research/factor-lab` (the "all factors" table) while a data ingest job or the backend's own
  restart warm-up is running in the background, without that combination risking the entire backend going
  down for every user. Previously this exact combination killed the process for 12m45s (iter-49's own live
  incident) — the confirmed crash site (`research.py:1051`'s `sorted(obs, ...)`) is now bounded and
  isolated.
- If a genuine memory-pressure event still occurs while `/research/factor-lab` computes, the page still
  finishes loading: the one affected `(factor, horizon)` cell renders as an honest "NA" (the SAME visual
  state already used for a genuine low-sample factor) while every other factor/horizon on the page renders
  normally — never a blanked whole page, never a crashed backend for other users' sessions.
- A historical-day backfill on `/data` (J-05's own defining case — backfilling exactly one day the app has
  never snapshotted before) now has a materially better chance of running to a genuine completion, because
  the crash source that has been interrupting this exact flow for several rounds is closed. (This iteration
  proves the fix in isolated tests plus one live 5x-repeated fault-injection drill against the real
  database; a fresh end-to-end recording of the backfill itself, and of the crash scenario under genuine
  concurrent load, is still pending the browser/QA lane — see "Not Visible Yet.")

---

## What Changed in the Visible UI

- Nothing. Zero frontend files were modified this iteration; no new page, panel, route, button, field, or
  label exists anywhere that did not exist before. The SAME `/research/factor-lab` all-factors table, the
  SAME `/data` job-status badge and "Refreshed: …" line, and the SAME `/scanner-runs` table are unchanged in
  shape — only how reliably they behave under concurrent background load has changed.

---

## What Old Behavior Changed

- **`/research/factor-lab`'s all-factors table.** Previously: a memory-pressure event anywhere inside
  `compute_factor_lab_all`'s per-`(factor, horizon)` computation could crash the whole backend, taking down
  every other user's session too (proven live last round). Now: that ONE `(factor, horizon)` entry degrades
  to an honest "unavailable" status server-side and renders as "NA" client-side — visually indistinguishable
  from the pre-existing "not enough sample data" NA state — while every other row/horizon on the page keeps
  rendering, and the server itself stays up.
- **`/research/factor-lab`'s whole-page empty state — a disclosed caveat, not a fix this iteration makes.**
  If memory pressure instead hits somewhere OUTSIDE the per-`(factor,horizon)` loop (the shared observation
  pool builder, the shared decile aggregator), the backend degrades the ENTIRE response instead of one cell
  — the frontend has no field to distinguish this from a genuinely empty store, so the page falls back to
  its existing "No forward-tested factors" empty state, whose own wording ("No stored snapshot has a factor
  value with a realized forward return at any horizon. No rank-IC or decile is fabricated to fill the gap.")
  would read as factually wrong in this scenario — real data exists; the true cause is a transient
  memory-pressure degrade, not an empty store. This is a genuine, newly-surfaced UX gap this iteration does
  not close (see "Not Visible Yet").
- **`/data`'s "Refreshed: …" line — a rare edge case, not an ordinary-path change.** On ordinary ingests this
  line is unaffected. In the narrow case where an ingest's own drawdown-expectations warm phase starts while
  the backend's own boot re-warm is already mid-flight in the same process (most plausible right after a
  restart), the new interlock makes the ingest's warm defer entirely for that one run: "drawdown
  expectations" is honestly omitted from that job's "Refreshed: …" line (it is retried automatically on the
  next ingest) rather than the two loops racing for memory the way they previously could.

---

## Not Visible Yet

- The new per-`(factor, horizon)` `"unavailable"` degrade status and the whole-response `"factors_status":
  "unavailable"` field the backend now returns are **not read anywhere in the frontend.** Confirmed:
  `apps/frontend/lib/api.ts`'s `FactorHorizonDeciles` and `FactorLabAllResponse` TypeScript interfaces carry
  no `status` / `factors_status` field. The degrade is invisible as a distinct state to the frontend code —
  it always falls back to an existing NA cell or the existing "No forward-tested factors" empty state, never
  a dedicated "temporarily unavailable, please retry" message.
- The warm-in-progress guard's deferral (`_try_acquire_drawdown_warm` / `_release_drawdown_warm`) is
  server-log-only (a single `logger.info` line naming which caller deferred and why) — no UI element on
  `/data` or anywhere else indicates "a background warm was deferred this run."
- The `phase_context_by_date` skip's live numeric before/after (does it actually close the ~23.6–23.9s MID
  health-poll-stall cluster recorded in `reports/perf-budgets.md` Item R Addendum 6) has only been proven as
  a MECHANISM (a real two-call test proves the precompute is invoked once on a genuine cache MISS, zero times
  once every claim is a HIT) — the live re-drill against a real ingest is left to the browser/QA lane.
- The test-only fault-injection switch (`TRENDORA_FAULT_INJECT_MEMORY_ERROR=factor_lab_all`, and the new
  `"factor_lab_all"` entry in `data_manager._FAULT_INJECT_SITES`) has no UI surface at all — it is an
  environment variable read once at process start, exercised only by automated tests, never reachable from
  the browser.
- Per the dev handoff's own Known Issues: TC-1 (an ingest's finalize-tail warm running concurrently with a
  live `/research/factor-lab` view — the EXACT iter-49 crash scenario), TC-7/TC-8/TC-9 (the full-horizon
  forward-aggregate warm's health-poll cadence, peak-memory margin, and an induced-pressure abort test),
  TC-10/TC-11 (J-05's live in-app backfill of one unsnapshotted historical day), and TC-12
  (`/research/factor-lab`'s time-to-interactive + on-load API latency) have **not** been run live this pass
  — they are explicitly assigned to the browser/QA lane. What was proven this pass: the confirmed crash
  frame survives 5 consecutive real HTTP requests against the real committed database with the fault
  deterministically armed (no crash, `GET /api/health` stayed 200 throughout), and the warm-in-progress
  guard holds in both trigger orders in isolated tests — strong but not identical evidence for the SAME
  concurrent-load scenario that actually caused iter-49's outage.
