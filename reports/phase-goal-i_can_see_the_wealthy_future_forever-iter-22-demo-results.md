# Demo Results — goal-i_can_see_the_wealthy_future_forever-iter-22

**Demo Verdict:** RECORDED_WITH_NOTES
**Date:** 2026-06-07
**Frontend URL:** http://localhost:3835
**Iteration:** 22

## Captured Steps

| Step | Title | Journey | New | Screenshot |
|------|-------|---------|-----|------------|
| 01 | Data Manager — page loads | J-17 |  | reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-22/step-01.png |
| 02 | Backfill job runs — no source label in header | J-17 | yes | reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-22/step-02.png |
| 03 | Switch to Fetch — Import source picker appears | J-33 |  | reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-22/step-03.png |
| 04 | Needs-key source — masked key field appears | J-33 |  | reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-22/step-04.png |
| 05 | API key never appears in error messages | J-33 | yes | reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-22/step-05.png |
| 06 | Resumable imports panel — survives a backend restart | J-34 | yes | reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-22/step-06.png |
| 07 | Resume rejected gracefully — inline error, page stays up | J-34 | yes | reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-22/step-07.png |
| 08 | Coverage card and run history intact after all changes | J-17 |  | reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-22/step-08.png |

## Soft notes

- Step 02 — couldn't perform click (Locator.wait_for: Timeout 10000ms exceeded.); captured the page anyway.
- Step 03 — expected "Import source" did not appear; recorded anyway.
- Step 04 — expected "Session API key for" did not appear; recorded anyway.
- Step 05 — expected "Run history" did not appear; recorded anyway.
- Step 06 — expected "Resumable imports" did not appear; recorded anyway.
- Step 07 — couldn't perform click (Locator.wait_for: Timeout 8000ms exceeded.); captured the page anyway.
- Step 08 — expected "Run history" did not appear; recorded anyway.

## Environment

- **Frontend URL:** http://localhost:3835
- **Browser:** Chromium via Playwright (record)
- **Demo mode:** record
