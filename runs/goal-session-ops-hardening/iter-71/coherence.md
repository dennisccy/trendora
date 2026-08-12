# Iteration 71 — Coherence Audit

**Iteration:** goal-ops-hardening-iter-71
**Date:** 2026-08-12
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

This iteration touches exactly one registered Data Contract row — "Backend readiness / boot
phase + preflight verdict" (canonical computing modules `app.engine.readiness.compute_readiness`
/ `compute_preflight`; canonical endpoint `GET /api/health`) — adding one additive field,
`stale_for_s`, per the iter spec's "Data-contract additions" and the blueprint's own pre-recorded
iter-71 note on that row (`runs/goal-session-ops-hardening/state/blueprint.md:433`).

Traced against the diff (`runs/goal-session-ops-hardening/iter-71/iter-diff.md`, confirmed
byte-identical to `git diff 5efd4a30...` — 7 files changed, all shown in full, no truncation):

- `apps/backend/app/engine/readiness.py:127` (`_tick_and_cache`) stamps the SAME payload
  produced by the existing tick call with `computed_at=time.monotonic()` — no new compute.
- `apps/backend/app/engine/readiness.py:165-194` (`get_readiness_and_preflight`, the single read
  accessor `GET /api/health` calls) now branches on the cache entry's age: fresh → serve the
  cached dict plus a derived `stale_for_s`; stale (past `max_stale_intervals ×
  refresh_interval_seconds`) → fall through to the SAME `_tick_and_cache` synchronous call the
  pre-existing cold-start path already used; total failure → `_unavailable_fallback()`, a small
  extracted helper that returns the SAME honest NO-GO shape that was previously written inline
  (behavior-preserving refactor, not a second producer). No new function computes readiness or
  preflight independently — `compute_readiness`/`compute_preflight` remain the only two callers of
  the underlying computation, both still owned by `app.engine.readiness`.
- `apps/backend/app/api/health.py:174-208` assigns `cached = None` explicitly on the fetch-failure
  path (audit MINOR fix, no new logic) and derives `stale_for_s = cached.get("stale_for_s", 0.0)
  if cached is not None else 0.0` — a bare read off the SAME dict `get_readiness_and_preflight`
  already returned earlier in the same handler; this is a re-format/derivation, not a second
  fetch or recomputation (permitted per Part A rule 3).
- `apps/backend/app/config.py` / `config.yaml` add the `max_stale_intervals` config knob (a
  threshold parameter, not a displayed value) with boot-time validation (`> 0`).
- The three test files (`test_data_manager.py`, `test_health.py`, `test_readiness.py`) only add
  coverage for the above; no production code path outside `readiness.py`/`health.py`/`config.py`.

No new UI surface fetches this value from a non-canonical endpoint — the diff contains zero
frontend files (confirmed by `git diff --stat` against the snapshot SHA: only
`apps/backend/app/api/health.py`, `apps/backend/app/config.py`,
`apps/backend/app/engine/readiness.py`, 3 backend test files, and `config.yaml` changed).
`stale_for_s` is not read by any frontend component this iteration (iter spec's "New information
displayed: None visible" — confirmed, no `apps/frontend/**` file appears in the diff).

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Backend readiness / preflight verdict (`readiness`/`preflight`) | OK | `app/engine/readiness.py:165-194`, `app/api/health.py:174-208` — same two producers, same endpoint |
| `stale_for_s` (new additive field on the same row) | OK — registered | Iter spec "Data-contract additions"; blueprint.md:433 iter-71 note; computed in `readiness.py:185-193`, surfaced in `health.py:208` off the existing payload |

## Information Architecture check

No new page, route, component, or nav entry this iteration — the diff touches zero files under
`apps/frontend/`. The iter spec confirms this explicitly ("Frontend: None this iteration",
"UI surface changes: None — no page, badge, or banner changes"). No ui-surface-map report exists
for this iteration (consistent with a backend-only lean round), so IA surfaces were derived
directly from the diff; there are none to check.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no frontend change this iteration) | OK | n/a — confirmed via `git diff --stat 5efd4a30... -- apps/frontend` (empty) |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- `stale_for_s` is deliberately not surfaced on the readiness badge or preflight banner this
  round (explicitly deferred in the iter spec's OUT OF SCOPE, to avoid triggering the goal.md
  Loop Mechanics full-depth rule on a first UI change). This is a reasoned, documented deferral
  rather than a coherence gap — noted here only so a future iteration that does surface it treats
  the existing global readiness badge / `/data` preflight banner as the canonical display
  location, not a new panel.
- None otherwise — the change is a clean, behavior-preserving refactor of the single existing
  read accessor plus one additive field; naming, module ownership, and endpoint identity are all
  consistent with the blueprint's already-recorded iter-71 note on this row.
