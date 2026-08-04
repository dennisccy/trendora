# Demo Results — goal-ops-hardening-iter-47

**Demo Verdict:** RECORDED_WITH_NOTES
**Date:** 2026-08-04
**Frontend URL:** http://localhost:3255

## Captured Steps

| Step | Title | Journey | New | Screenshot |
|------|-------|---------|-----|------------|
| 01 | Open the Evidence page |  |  | reports/demo/goal-ops-hardening-iter-47/step-01.png |
| 02 | Verify idle Evidence page shows real numbers with no 'Refreshing' badge |  |  | reports/demo/goal-ops-hardening-iter-47/step-02.png |
| 03 | Open the Data Manager to start a backfill |  |  | reports/demo/goal-ops-hardening-iter-47/step-03.png |
| 05 | Fill in a new date range starting the day after the latest bar |  |  | reports/demo/goal-ops-hardening-iter-47/step-05.png |
| 07 | Click Start to begin the backfill job |  |  | reports/demo/goal-ops-hardening-iter-47/step-07.png |
| 08 | Return to the Evidence page to observe the 'Refreshing' badge |  | yes | reports/demo/goal-ops-hardening-iter-47/step-08.png |
| 09 | Verify the home page stays responsive while the backfill runs |  |  | reports/demo/goal-ops-hardening-iter-47/step-09.png |
| 10 | Observe the honest 'Refreshing' badge disclosure |  | yes | reports/demo/goal-ops-hardening-iter-47/step-10.png |

## Soft notes

- Step 04 — couldn't perform click (Locator.wait_for: Timeout 4000ms exceeded.); captured the page anyway.
- Step 08 — expected "Refreshing" did not appear; recorded anyway.
- Step 10 — expected "last complete version" did not appear; recorded anyway.

## Environment

- **Frontend URL:** http://localhost:3255
- **Browser:** Chromium via Playwright (record)
- **Demo mode:** record
