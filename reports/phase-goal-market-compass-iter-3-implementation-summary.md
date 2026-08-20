# goal-market-compass-iter-3 — Implementation Summary

**Phase:** goal-market-compass-iter-3
**Date:** 2026-08-20
**Written by:** developer

---

## Features Implemented

- **Frozen, stamped next-session manifests**: every trading day's close now produces one permanent,
  tamper-evident record of "what the compass said" — who computed it, when, from which code and config,
  and with which dataset — that can never be silently changed by a later data update, rebuild, or config
  edit.
- **Manifest strip on the Today page**: a new card at the bottom of `/` shows this record's stamps
  (frozen/version/eligibility badges, a freeze timestamp, identity fingerprints), an expandable table of
  every name that was NOT picked as a candidate (with the reason it wasn't), and a separate "near-miss"
  research list of names just below the bar.
- **Manual "regenerate" action**: for any past date, the owner can explicitly mint a new, clearly-labeled
  version of that date's manifest under today's rules — without ever touching or hiding the original.
  The confirm step spells out exactly what this does and does not change.
- **Export file per freeze**: each freeze also writes a local JSON file to disk (for the owner's separate
  Tapeology project to read later) whose bytes are provably identical to what the app itself is showing.
- **Cleaner sector labels & one wording fix**: a raw decimal-artifact number in the summary card's
  "cited facts" panel (e.g. `-0.20000000000000284`) now shows as a clean `-0.20`; one caution message
  that sounded like advice now states the fact only.

## Changed Behavior

- **Requesting the "current" day's compass before the nightly close has frozen it**: previously, simply
  loading the page (or calling the API) for today's date would silently compute and save a manifest on
  the spot. Now, only the actual overnight close process (or an explicit manual "regenerate") is allowed
  to create today's manifest — a plain page load before that happens honestly shows "unavailable"
  instead of quietly creating one on someone's behalf.
- **The regenerate action is brand new** — there was no way to re-run a past date's manifest under
  today's selection rules before; now there is, and it is clearly marked so it can never be confused with
  the original, live-frozen version.

## Backend-Only Items

None — every new backend field is surfaced somewhere in the new manifest strip UI.

## Incomplete Items

- **Final "Today" page redesign (readiness banner placement, page-load performance polish, ten-second
  read layout)** is a later iteration's job (already marked as such in the plan) — this iteration only
  adds the manifest proof card to the page as it exists today.
- **Automated recorded walkthroughs** for the four existing decision-surface capabilities (sector
  labels, what-changed, plain-English summary, candidate reasons) are queued for the demo-recording step
  of this pipeline, not produced directly by this implementation pass.

## Config and Environment Changes

- `config.yaml` `compass.manifest.*` — export file location, schema version, and a small safety margin
  (60 seconds) added to every freeze timestamp before it's considered "available" downstream.
- `config.yaml` `provenance.*` — the list of code files and config sections whose fingerprint gets
  stamped on each freeze.
- `TRENDORA_COMPASS_EXPORT_DIR` (optional env var, test-only) — lets automated tests redirect the export
  file location; not used in normal operation.
- `.gitignore` — the export file folder is now excluded from source control (it's regenerated output,
  like the database — never something to commit).
- No new required environment variables for normal operation; no changes to how the app is started.

## Known Limitations

- The pre-existing "engine calc code has no magic numbers" automated check currently fails, but on code
  this phase never touched (three unrelated files) — confirmed to already fail on the untouched project
  baseline, not something this work introduced or is responsible for fixing.
- A leftover, unrelated build-artifact folder (`apps/frontend/.next-verify/`, ~165 files) was discovered
  already checked into source control from an apparently different, older project session. It was left
  untouched (restoring it after an accidental local cleanup) since removing it is outside this
  iteration's scope — flagged here for the owner to decide on separately.
- The "Regenerate" button's availability (only for a past date, never "today") is a convenience gate in
  the page itself, not a hard backend restriction — a minor, low-risk gap noted in the frontend handoff.
