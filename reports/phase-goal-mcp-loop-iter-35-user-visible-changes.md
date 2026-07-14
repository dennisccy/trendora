# goal-mcp-loop-iter-35 — User-Visible Changes

**Phase:** goal-mcp-loop-iter-35
**Date:** 2026-07-14
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now see, on the Data Manager page (`/data`), a new "Live-vs-seed drift" card that reports whether the most recent Fetch job's freshly-pulled prices agreed with the platform's trusted, committed reference history.
- When the live data provider has silently revised history for dates the platform already had on file (e.g. after recalculating a whole price history for a dividend/split), users can now see exactly which stock ticker(s) and which date(s) were affected, labeled "adjustment seam" — previously this discrepancy went completely unnoticed because the database never overwrites an already-stored date.
- Users can now see the site-wide "is today's board trustworthy" banner (shown at the top of every page, not just `/data`) automatically turn cautionary — amber "DEGRADED", with a specific reason naming the affected symbol(s) — the moment a drift is detected, and automatically recover to the normal green "GO" state once a later clean fetch supersedes it. This happens without needing to visit `/data` at all; the warning is visible everywhere.
- Users can hover the drift card's title for an explanatory tooltip describing exactly what the check does ("Byte/fixed-precision compares the last N dates a Fetch job returns against the committed seed... descriptive integrity reporting, recomputes nothing, never auto-repairs or re-fetches").

No new controls were added — this is a read-only report produced automatically as a byproduct of running the existing "Fetch" job. There is no new button, form, or setting for a user to operate.

---

## What Changed in the Visible UI

- The `/data` page now shows a new "Live-vs-seed drift" card, positioned directly under the existing "Storage footprint" card and above the "Rebuild snapshots for current universe" panel — the page's vertical card stack is one card taller. No existing card moved or was restructured.
- The new card has four distinct visual states depending on what's on record: a quiet gray "no fetch has run yet" message, a quiet green "matched the seed" line, a loud amber alert box listing every affected symbol + its exact mismatching dates when drift is detected, and a loud amber "could not be read" fallback if the underlying report file is corrupted.
- The site-wide preflight banner (present on every page) can now display a new reason line inside its existing bulleted list when it degrades: "Live-vs-seed drift detected (adjustment seam) for: `<SYMBOL>`." No new banner element, color, or layout was added — the banner's existing generic reasons list simply gained a fourth possible source of text (previously it could only degrade for service-down, stale-data, or unreadable-internal-records reasons).
- If the drift report itself becomes unreadable, both the `/data` card and the site-wide banner show an honest "could not be read / re-run a Fetch job" message rather than silently treating it as fine or crashing the page.

---

## What Old Behavior Changed

- The daily "is today's board trustworthy" check (the GO / DEGRADED / NO-GO banner) now composes over four inputs instead of three (service running, data freshness, internal records readable, and now: does the live feed match the trusted reference). This is verified inert for any user who has never triggered a live Fetch: with no fetch ever run, the new check honestly reports "nothing to compare yet" and counts as fine, so the banner's GO/DEGRADED/NO-GO outcome is byte-identical to before this phase. The new behavior only becomes observable after someone actually runs a Fetch job whose overlap window reveals a mismatch.

---

## Not Visible Yet

- The whole-check on/off switch (`data_quality.drift.enabled` in `config.yaml`) is a deployment/config lever only — there is no in-app admin toggle to disable the drift check from the UI. This is consistent with the rest of this product, which has no admin settings screen; every other operational knob is also config-only.
- Two related but separate integrity checks from the same backlog idea (comparing today's overall statistical patterns against historical norms, and a deeper cross-referenced anomaly scan) were intentionally not built this iteration and do not exist in any form yet — not even as an unwired backend capability. They are planned as separate future work, not a hidden capability of this phase.
