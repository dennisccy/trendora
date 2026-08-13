# Iteration 78 — Coherence Audit

**Iteration:** goal-ops-hardening-iter-78
**Date:** 2026-08-13
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| `stale_for_s` (Backend readiness / boot phase + preflight verdict row — `compute_readiness`/`compute_preflight`, `GET /api/health`) | OK | `apps/frontend/components/readiness-provider.tsx:222-227,255-266` stores the poll's own base + client receipt time in refs and re-derives via `apps/frontend/lib/staleness-tick.ts:22-37`'s `deriveLiveStaleForS` on a local 1s interval; the result is fed through the SAME single formatter, `apps/frontend/lib/staleness-annotation.ts`'s `formatStaleAnnotation` (unmodified this iteration) — no second fetch, no second endpoint, no second formatter. `deriveLiveStaleForS` performs no business computation of its own: it is a client-wall-clock extrapolation of the one value the backend already served, explicitly short-circuited back to the unticked base for every one of `formatStaleAnnotation`'s own null-rendering cases (`null`, `0`, negative, non-finite — `staleness-tick.ts:27-34`, covered by `staleness-tick.test.ts`), so it can never fabricate or diverge into a second reading of "how stale is this payload." Re-derivation-for-live-display of an already-fetched canonical value, not a duplicate computation. |
| `background_compute` (J-09 row — `compute_readiness` via `get_background_compute_status()`, `GET /api/health`) | OK | `incredible_auto_dev/scripts/automation/lib/demo_runner.py` changes (raised per-step wait ceiling to an opt-in 45000ms, `demo_runner.py:367,376-377,385-386,394-395`) and the walkthrough script's new as-of target only change WHEN/HOW LONG the capture waits and WHICH existing route (`/backtest?asof=...`) it navigates to before screenshotting; no new endpoint, computation, or fetch is introduced. Confirmed against `reports/phase-goal-ops-hardening-iter-78-ui-surface-map.md`'s "Backend-Only Changes" list (demo_runner.py is showcase tooling, not served application code). |
| Test-residue purge (`__tc3_intentionally_broken.ts` / `.next-test-*`) | OK — not a Data Contract value | `incredible_auto_dev/scripts/start-frontend.sh:57-142` adds launch-time file cleanup, not a displayed/served value; out of Data Contract scope. |

No new displayed value/entity is introduced this iteration (spec's "New information displayed: None" — confirmed against the diff: the only new frontend file is the non-visual `apps/frontend/lib/staleness-tick.ts`).

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| Readiness badge / preflight banner staleness tick (global, every page) | OK | `runs/goal-session-ops-hardening/state/blueprint.md:387-389` registers both as layout-level (not nav items), present on every page — unchanged this iteration. `reports/phase-goal-ops-hardening-iter-78-ui-surface-map.md` confirms 0 new pages/routes and no navigation changes. |
| J-09 walkthrough capture (`/backtest?asof=2026-07-30`) | OK | `/backtest` is an existing top-level nav item (`blueprint.md:401`, confirmed live in the IA table); the demo script change only alters which as-of date it navigates to on that existing page — no new route. |
| `scripts/start-frontend.sh` residue purge | OK — not a UI surface | Launch-time script, no rendered page; correctly excluded from the UI surface map. |

No new page, route, or nav entry this iteration; the blueprint's Information Architecture is unchanged, matching the iter spec's own "Blueprint conformance" claim.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- `incredible_auto_dev/scripts/start-frontend.sh:98-107` adds `_residue_dir_has_live_server()`, whose body (read `.trendora-serving` marker → extract pid → liveness check → PID-reuse cmdline guard) duplicates the pre-existing `_dist_dir_has_live_server()` at `start-frontend.sh:203-212` almost line-for-line, differing only in that the new one takes a directory argument (needed because the purge loop must check *other* scratch dirs, not just this invocation's own `$DIST_DIR`). This is not a Data Contract violation — a "who is serving this directory" liveness check is an internal launcher guard, not a displayed/served value with a registered canonical source — but it is two hand-maintained copies of the same PID-reuse safety logic; if that guard's safety condition is ever tightened (e.g. a new process-identity check), both copies need the same edit or the launcher's two purge paths could silently diverge in what they consider "live." Worth a future-iteration consolidation (parameterize `_dist_dir_has_live_server(dir=$DIST_DIR)` and call it from both sites) — not required to close this iteration.
- `deriveLiveStaleForS`'s in-between-poll value is a client-side time extrapolation, not a re-fetch of the server's own recomputed staleness; this is the intended design (documented explicitly in `readiness-provider.tsx:209-213` and `staleness-tick.ts`'s header comment) and degrades safely to the base value on every edge case, so it is not flagged as a violation — noting only for the record that the displayed number between polls is an estimate, not a fresh server read.
