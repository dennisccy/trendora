# Phase goal-ops-hardening-iter-77 — UI Surface Map

**Phase:** goal-ops-hardening-iter-77
**Date:** 2026-08-13
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/` (and every page — global top bar) | `HealthBadge` (`components/health-badge.tsx`) | Changed behavior | First UI consumer of `GET /api/health`'s `stale_for_s` field: adds an "as of Ns ago" annotation next to the readiness pill when the read is stale | Trigger a background-compute window (POST a not-yet-computed `as_of` to `/api/backtest`), reload any page, and verify `[data-testid="readiness-staleness"]` shows text matching `as of Ns ago` next to the "Ready" pill; verify it disappears once `stale_for_s` returns to 0 |
| `/` (and every page — preflight banner) | `PreflightBanner` (`components/preflight-banner.tsx`) | Changed behavior | Same `stale_for_s` field rendered on the preflight strip/banner as `(as of Ns ago)` | With the same stale condition active, verify the thin banner under the top bar reads "GO — today's board is current." followed by `[data-testid="preflight-staleness"]` text `(as of Ns ago)` |
| `/` (and every page — global top bar) | Header badge row (`app/layout.tsx` + `HealthBadge`) | Updated layout | iter-76/e regression fix: the "Ready" pill was hidden off-screen at 1280×800 when a background-compute chip also rendered, because the outer flex row had no wrap allowance | Resize the browser to exactly 1280×800, trigger an active background-compute window, and verify BOTH the readiness pill (`[data-testid="readiness-badge"]`) AND the `[data-testid="background-compute-indicator"]` chip ("background compute running (N)") are simultaneously visible on-screen (the row should wrap to a second line rather than clipping either element) |
| `/backtest` | `ScorecardSection` table rows (`app/backtest/page.tsx`) | Test hook added (no visible change) | J-07 golden hardening: replaces a fragile bare-text `"1d"` match with a real selector | With a populated as-of date loaded, run `document.querySelectorAll('[data-testid^="scorecard-row-"]')` in the browser console and verify one element per configured horizon exists (`scorecard-row-1d`, `scorecard-row-5d`, `scorecard-row-10d`, `scorecard-row-20d`, `scorecard-row-60d`); verify the visible table itself (horizon/cohort/vs SPY/etc. columns) is pixel-identical to before |
| `/data` | Coverage error card ("Backend unavailable") | Regression verification (no code changed this iteration) | This iteration captured fresh evidence for the pre-existing honest-fallback fault-injection hook (`data_overview_endpoint`) as a housekeeping item; confirms it still degrades honestly rather than showing fabricated numbers | With the backend restarted with `TRENDORA_FAULT_INJECT_MEMORY_ERROR=data_overview_endpoint` set, navigate to `/data` and verify the card reads "Backend unavailable" / "Dataset coverage could not load from the API. No figures are shown rather than fabricated values. Confirm the backend is running and retry." — no coverage numbers rendered |

<!-- Change Type options used: Changed behavior | Updated layout | Test hook added | Regression verification -->

---

## Backend-Only Changes (No UI Impact)

- `scripts/start-frontend.sh` — added a `flock`-based lock serializing the build-if-stale → `next build`
  → `next start` sequence per dist-dir, closing a race where two overlapping launches could serve a
  torn/partial (unstyled) page. No UI surface itself; this is a launch-time reliability fix with no
  in-app click path to trigger it — it can only be exercised by launching the script concurrently, which
  is exactly what the two new pytest regression tests (`test_start_frontend_script.py`) do. Not
  independently testable through manual browser use.
- `scripts/automation/lib/demo_runner.py` (`_settle_for_capture` and its three call sites) — fixes the
  walkthrough recorder's before/after screenshot pairs so the "after" frame waits for the actual DOM
  change instead of a blind timeout. This is internal showcase/QA tooling that generates demo artifacts
  after the fact; it has no end-user-facing surface in the running product.
- `runs/goal-session-ops-hardening/journey-scripts/J-07.json` (step 4 selector upgrade) and
  `runs/goal-session-ops-hardening/state/goldens-regen-pending` (stale listing partially cleared) —
  test-harness/bookkeeping artifacts, not product code; no UI surface affected.
- Repo-root `=` file (deleted) — a stray zero-byte file with no references anywhere in the codebase; no
  UI surface affected.

---

## Summary

- **Frontend surfaces changed:** 4 (global badge row content, global badge row layout, preflight banner
  content, `/backtest` scorecard test hooks) across 2 distinct routes (global top bar/banner — present on
  every page — and `/backtest`)
- **New pages/routes:** 0
- **Modified components:** 4 (`health-badge.tsx`, `preflight-banner.tsx`, `readiness-provider.tsx` +
  `lib/api.ts` + `lib/staleness-annotation.ts` as supporting plumbing, `app/layout.tsx`,
  `app/backtest/page.tsx`)
- **Navigation changes:** no
- **Backend-only changes:** 4 (`start-frontend.sh` race fix, `demo_runner.py` recorder fix, golden/state
  housekeeping, stray file deletion)
