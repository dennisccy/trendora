# Demo Results — goal-ops-hardening-iter-42

**Demo Verdict:** RECORDED_WITH_NOTES
**Date:** 2026-07-31
**Frontend URL:** http://localhost:3255

## Captured Steps

| Step | Title | Journey | New | Screenshot |
|------|-------|---------|-----|------------|
| 01 | Open the dashboard |  |  | reports/demo/goal-ops-hardening-iter-42/step-01.png |
| 02 | Navigate to Data Manager |  |  | reports/demo/goal-ops-hardening-iter-42/step-02.png |
| 03 | Run a backfill job | J-01 |  | reports/demo/goal-ops-hardening-iter-42/step-03.png |
| 04 | Set the end date and start the job | J-01 |  | reports/demo/goal-ops-hardening-iter-42/step-04.png |
| 05 | Click Start to submit the backfill | J-01 |  | reports/demo/goal-ops-hardening-iter-42/step-05.png |
| 06 | View scanner runs | J-08 |  | reports/demo/goal-ops-hardening-iter-42/step-06.png |
| 07 | Open the Backtest page | J-08 |  | reports/demo/goal-ops-hardening-iter-42/step-07.png |
| 08 | Check the Data page for background compute status | J-09 |  | reports/demo/goal-ops-hardening-iter-42/step-08.png |

## Soft notes

- Step 01 — expected "Ready" did not appear; recorded anyway.
- Step 02 — expected "Start a fetch / backfill job" did not appear; recorded anyway.
- Step 03 — couldn't perform fill (Locator.wait_for: Timeout 4000ms exceeded.); captured the page anyway.
- Step 04 — couldn't perform fill (Locator.wait_for: Timeout 4000ms exceeded.); captured the page anyway.
- Step 05 — couldn't perform click (Locator.wait_for: Timeout 4000ms exceeded.); captured the page anyway.
- Step 06 — expected "2026-05-29" did not appear; recorded anyway.
- Step 08 — expected "Background compute" did not appear; recorded anyway.

## Environment

- **Frontend URL:** http://localhost:3255
- **Browser:** Chromium via Playwright (record)
- **Demo mode:** record
