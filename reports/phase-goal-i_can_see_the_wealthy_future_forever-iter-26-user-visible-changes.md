# Phase goal-i_can_see_the_wealthy_future_forever-iter-26 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-26
**Date:** 2026-06-09
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- On the Data Manager (`/data`), when a user tries to resume a paused import that requires a
  provider key but has not entered one, they can see a clear red inline message next to the
  Resume button telling them exactly what key is needed ("Enter the session key for <source> to
  resume."). The import row stays visible so the user can supply the key and try again.

---

## What Changed in the Visible UI

- **`/data` — ResumeControl error state.** After clicking Resume on a needs-key paused import
  without supplying a key, a red inline alert (`role="alert"`) now appears immediately next to
  the Resume button with an actionable, source-specific message. Previously this could look like
  nothing happened (the row could appear to silently vanish).
- **`/data` — ResumeControl row persistence on failure.** When a resume fails (any error, not
  just a missing key), the unfinished-imports row now stays in the Unfinished Imports panel.
  Previously a failed resume could drop the row from the list, making the import appear to
  disappear.

---

## What Old Behavior Changed

- **Resume on Data Manager (/data):** Previously, attempting to resume a key-requiring import
  without entering a key could cause the import row to silently disappear from the Unfinished
  Imports panel (the failed resume triggered a list reload, dropping the row). Now the row stays
  visible and a red inline error appears next to the Resume button with specific guidance on what
  key to enter.

---

## Not Visible Yet

- **Offline "seed" import source** (`TRENDORA_ENABLE_SEED_IMPORT_SOURCE`): A new "Seed (offline
  test data)" source was added to the backend's source catalog. It appears in the Data Manager's
  source picker **only when the environment flag is explicitly set**. This flag is OFF by default
  and is absent from the committed configuration; it is never shown in the real product. This is
  a QA/test harness affordance only and is not a production user-facing capability.
- **Offline market-cap reference for the seed source**: `SeedProvider` can now read a committed
  `market_caps.csv` to serve real market-cap figures for offline expand operations. This is
  consumed only by the QA harness when the seed source is enabled — no change to the production
  UI.
- **QA fixture-DB builder script** (`apps/backend/scripts/build_qa_fixture_db.py`): A script
  that constructs a throwaway database with deliberate data gaps for testing the missing-data
  diagnostic. This is a test tool; it has no UI surface and is never run in production.
