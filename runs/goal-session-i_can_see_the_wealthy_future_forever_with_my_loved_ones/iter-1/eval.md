**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** lean

# Iteration 1 Evaluation

## Summary

J-42 (uniform ISO date presentation) is newly passing with strong, fresh evidence: a single shared formatter (`apps/frontend/lib/dates.ts`) is now the format authority across every date surface, the four `/data` native date pickers became validated ISO text inputs (invalid `2026-13-40` / `10/06/2026` show an inline error and block submit), and the coherence audit independently confirmed no per-component format literal remains. J-43 (deep-linkable as-of) moved from failing to **partial**: interactive selection writes `?asof=D`, invalid params degrade safely, latest removes the param, and a deep-linked `?asof` restores into the one global control — but the URL is stripped after hydration on reload / fresh tab / post-click-through, so deep links are not yet durable (browser-QA FAIL with a precise root cause). All five required-still-passing journeys (J-06, J-13, J-17, J-18, J-20) re-verified green with fresh per-journey screenshots, and the baseline's full-pytest debt was paid (622 passed / 4 skipped / 0 failed).

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-42 | partial | **passing** | reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-1-evidence/UT-J-42-invalid-2026-13-40.png (full /data page with error state); ISO switcher/indicator also visible in UT-J-13-dashboard-historical.png |
| J-43 | failing | **partial** | reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-1-evidence/UT-J-43-url-missing-asof.png |
| J-06 | already_passing (thin baseline) | passing (re-verified: MRVL A 94.42 / E 20.54 / E 58.42 identical leaderboard↔detail at 2026-06-09) | UT-J-43-detail-clickthrough.png + UT-J-43-url-missing-asof.png |
| J-13 | already_passing | passing (re-verified) | UT-J-13-dashboard-historical.png |
| J-17 | already_passing | passing (form-submit leg re-verified; backfill job ran to completion) | UT-J-17-job-complete.png |
| J-18 | already_passing | passing (re-verified per the J-43 amendment — no page-local date state) | UT-J-18-backtest-no-local-date.png |
| J-20 | already_passing | passing (re-verified at historical as-of 2026-06-09) | UT-J-20-nvda-chart-full.png |
| J-35/J-37/J-38/J-39/J-41 | already_passing (suite-basis, "full suite re-run owed in iter-1") | verification debt paid: full pytest 622/4/0 at this commit | dev handoff Tests Run section |
| All other journeys | already_passing / unknown (blocked-NA) | unchanged (not re-tested) | carried over |

### J-43 detail (why partial, not passing)

Verbatim acceptance requires that reload and a fresh tab of a URL carrying `?asof=D` preserve the param. QA verified by DOM extraction (`window.location.href`) that after hydration of `/stocks?asof=2026-06-09` the date IS restored into the global control (switcher = 2026-06-09, historical indicator shown, data correct) but the URL collapses to `/stocks`. Passing legs: interactive selection → `?asof=D` persists; switch-to-latest removes it; `?asof=not-a-date` and `?asof=2026-01-01` (no run) both degrade to latest with no crash.

**Root cause (confirmed against the diff, `apps/frontend/components/asof-provider.tsx`):** the serialize effect in `AsOfUrlSync` declares deps `[asOf, latest, ready, pathname]` but reads `searchParams` from the closure. On deep-link load, the restore effect calls `setAsOf(D)` while the serialize effect fires first with `asOf=null`, stripping the param; when `asOf` lands as D the effect re-runs against a stale `searchParams` still showing `?asof=D`, sees `current === next`, and early-returns — the pending strip then wins and nothing re-triggers. Fix is small: include `searchParams` (or a `searchParams.toString()` key) in the serialize effect's dependency set, or defer serialization until the restored state has committed.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| One date format, displayed — ISO contracts unchanged | OK | One formatter module; no `toLocaleDateString`; no native `type="date"`; zero backend/API/DB/config changes in the diff |
| `?asof` is a serialization, not a second date state | OK | `asof-provider.tsx` is the sole reader/writer (`ASOF_PARAM` defined and used only there); `/stocks` `useSearchParams` reads only filter params; invalid `?asof` degrades to latest (verified in browser) |
| Exactly one date selector | OK | J-18 re-verified: `/backtest` has no page-local date control; the global switcher drives it |
| Single source of truth (critical) | OK | J-06 re-verified numerically at a historical date (MRVL identical on both pages); coherence audit Part A clean |
| No recompute in the read path (critical) | OK | No backend change; no new endpoint (coherence audit confirmed) |
| Secrets / paid SaaS / new deps | OK | Diff is frontend presentation code only; no dependency or credential touched |

Coherence audit: **COHERENCE-PASS** (no Part A/B violations; `lib/dates.ts` IS the registered TARGET row; no IA change).

## Evidence-hygiene notes

- Primary evidence is fresh and journey-specific (timestamps 09:55–10:43 today, distinct md5s for all cited files). Minor: four small UT-J-42 element captures are byte-identical and `UT-J-42-invalid-input-detail.png` is blank — but the cited full-page capture stands on its own and the validation claims are DOM-extracted. The UT-J-43 duplicate pairs are explainable (identical viewport for reload-check vs click-through; the URL bar is not in the viewport — the URL claims rest on `window.location.href` extraction).
- J-42's chart tooltip leg was not hover-verified (canvas not automatable); it is accepted on code inspection of the single `localization.timeFormatter → formatIsoDate` hook plus the coherence audit's formatter-authority confirmation — the acceptance's axis-tick carve-out is respected.

## Next-Step Recommendation

Iter-2 **lean**, primary target: **finish J-43** — fix the serialize-effect stale-`searchParams` dependency in `apps/frontend/components/asof-provider.tsx` (root-caused above; a small, surgical change) and re-run the reload / fresh-tab / click-through legs in browser QA. The fix is small enough that the decomposer may bundle it with starting **J-44 + J-45** (stored-regime-history + server-side index-series endpoints per the blueprint TARGET rows), which was the planned next target and whose QA will navigate via the now-working `?asof` deep links. Required-still-passing set should again include J-13/J-18/J-06. The decomposer should flip the **J-42** blueprint annotation to built (J-43 stays TARGET until the reload/fresh-tab legs pass). Also: drop the `npm run lint` DoD line — ESLint is genuinely not installed in this project; `tsc --noEmit` is the working frontend gate.
