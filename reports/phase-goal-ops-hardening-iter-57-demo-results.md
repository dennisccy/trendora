# Demo Results — goal-ops-hardening-iter-57

**Demo Verdict:** RECORDED_WITH_NOTES
**Date:** 2026-08-10
**Frontend URL:** http://localhost:3255

## Captured Steps

| Step | Title | Journey | New | Screenshot |
|------|-------|---------|-----|------------|
| 01 | Sign in and reach the homepage |  |  | reports/demo/goal-ops-hardening-iter-57/step-01.png |
| 02 | Open the Data Manager page | J-01 |  | reports/demo/goal-ops-hardening-iter-57/step-02.png |
| 03 | View the stock detail page for AAPL | J-06 | yes | reports/demo/goal-ops-hardening-iter-57/step-03.png |
| 04 | Check the health call timing in the browser Network tab | J-06 | yes | reports/demo/goal-ops-hardening-iter-57/step-04.png |
| 05 | Check the stock bars call timing in the browser Network tab | J-06 | yes | reports/demo/goal-ops-hardening-iter-57/step-05.png |
| 06 | Observe the calendar grid during an active ingest | J-06 | yes | reports/demo/goal-ops-hardening-iter-57/step-06.png |
| 07 | Verify the stale banner is calm and clear, not alarming | J-06 | yes | reports/demo/goal-ops-hardening-iter-57/step-07.png |
| 08 | Backfill honors large date ranges without a cap | J-03 |  | reports/demo/goal-ops-hardening-iter-57/step-08.png |

## Soft notes

- Step 05 — expected {'css': "[data-testid='chart-window-caption']"} did not appear; recorded anyway.
- Step 06 — expected {'css': "[data-testid='availability-heatmap']"} did not appear; recorded anyway.

## Environment

- **Frontend URL:** http://localhost:3255
- **Browser:** Chromium via Playwright (record)
- **Demo mode:** record
