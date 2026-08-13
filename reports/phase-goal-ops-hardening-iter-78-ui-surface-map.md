# Phase goal-ops-hardening-iter-78 — UI Surface Map

**Phase:** goal-ops-hardening-iter-78
**Date:** 2026-08-13
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| Global — every page (mounted once in `apps/frontend/app/layout.tsx`, e.g. visit `http://localhost:3255/`) | `HealthBadge` staleness text — `data-testid="readiness-staleness"`, the "as of Ns ago" text next to the green "Ready" pill in the top-right header | Changed behavior | `ReadinessProvider` now re-derives `staleForS` on a local 1-second interval (`lib/staleness-tick.ts`'s `deriveLiveStaleForS`) instead of only setting it when a `GET /api/health` poll lands (iter-77/d fix) | Navigate to `http://localhost:3255/`, confirm the "Ready" pill is showing, note the exact number in the "as of Ns ago" text next to it, wait 10 seconds without clicking or navigating anywhere, then read the text again — it must have increased by approximately 10 (not still show the original number) |
| Global — every page (mounted once in `apps/frontend/app/layout.tsx`, strip directly under the header) | `PreflightBanner` staleness text — `data-testid="preflight-staleness"`, the "(as of Ns ago)" suffix on the "GO — today's board is current." message (or on a DEGRADED/NO-GO warning) | Changed behavior | Same `ReadinessProvider` tick feeds this component too — it reads the identical `staleForS` context value via the same `formatStaleAnnotation()` call, no separate fetch or formatter | On any page where the banner reads "GO — today's board is current. (as of Ns ago)", note the number, wait 10 seconds without interacting, and confirm the number in the parentheses increased by approximately 10 |
| Global — every page | `HealthBadge` / `PreflightBanner` staleness text (`stale_for_s === 0` or a failed poll) | Unchanged (regression check) | `deriveLiveStaleForS` deliberately does not tick a `0` or `null` base, so the pre-existing "render nothing" behavior for a fresh/failed poll must still hold | Immediately after the backend answers a synchronous/fresh compute (`stale_for_s` is `0`), or while the backend is stopped so the health poll fails, confirm neither `readiness-staleness` nor `preflight-staleness` renders any text — the pill/banner still render (e.g. "Backend unavailable" or "NO-GO"), just with no "(as of ...)" suffix |

<!-- No new page, route, form, modal, table, or navigation element was added or removed this
     iteration. Layout/position/styling of both annotations are unchanged from iter-77 — only the
     update cadence of the displayed number changed. -->

---

## Backend-Only Changes (No UI Impact)

- `scripts/start-frontend.sh` (tracked source `incredible_auto_dev/scripts/start-frontend.sh`) —
  before its existing build-if-stale check, the launcher now purges the reserved test-residue
  filename `apps/frontend/__tc3_intentionally_broken.ts` and any `apps/frontend/.next-test-*`
  scratch directory (excluding its own current build target) if present, logging what it removed,
  and fails loud (non-zero exit, clear log line) if the purge itself errors — no UI surface
  affected; this is a launch-time ops script, not served application code.
- `apps/backend/tests/test_start_frontend_script.py` — new regression test
  (`test_launcher_purges_leftover_test_residue_from_a_different_process`) proving the launcher's
  own purge defense end-to-end (real build, real serve) — no UI surface affected; test-only.
- `scripts/automation/lib/demo_runner.py` (tracked source
  `incredible_auto_dev/scripts/automation/lib/demo_runner.py`) — raised the per-step wait ceiling
  for the walkthrough-gallery screenshot tool from a hard 20s cap to an opt-in 45s cap (existing
  20s default unchanged for steps that don't ask for more) — no UI surface affected; this is
  internal documentation/showcase tooling, not part of the served application.
- `apps/frontend/lib/staleness-tick.ts` (new) and `apps/frontend/lib/staleness-tick.test.ts` (new)
  — the pure numeric derivation function and its unit test. `staleness-tick.ts` has no UI of its
  own (it renders nothing and is not a component); it is consumed by `readiness-provider.tsx`,
  whose visible effect is captured in the two rows above. Listed here to be explicit that no new
  standalone surface was created by adding this file.

---

## Summary

- **Frontend surfaces changed:** 2 (readiness badge staleness text, preflight banner staleness text — both global, present on every route)
- **New pages/routes:** 0
- **Modified components:** 1 (`apps/frontend/components/readiness-provider.tsx`); plus 1 new supporting (non-visual) lib file (`apps/frontend/lib/staleness-tick.ts`)
- **Navigation changes:** no
- **Backend-only changes:** 3 (`scripts/start-frontend.sh`, `apps/backend/tests/test_start_frontend_script.py`, `scripts/automation/lib/demo_runner.py`)
