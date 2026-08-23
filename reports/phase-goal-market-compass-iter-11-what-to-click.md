# Phase goal-market-compass-iter-11 — What to Click (Operator Verification Guide)

**Phase:** goal-market-compass-iter-11 (J-11 Stage B1-completion)
**Time required:** ~5 minutes
**Written by:** ui-test-designer

**Not executed this iteration.** Maintenance isolation forbids booting any service this
iteration — nothing below has been clicked or observed yet. This guide is written for whoever
next starts the app (earliest: J-11 Stage G) to confirm this iteration's two backend fixes
(the live schema migration and the `basis_disclosure` fail-closed fix) show up correctly, and
that nothing else broke.

---

## Prerequisites

- Frontend running at `http://localhost:3255`, backend running and reachable at
  `http://localhost:8255/api/health`
- No login required
- No new seed data needed — every step below reads manifests that already exist in the live
  database (this iteration migrated their table's schema; it did not create, delete, or change
  any row's values)

---

## Verification Steps

1. Open `http://localhost:3255/` in your browser
   - **Expect:** Page heading "Dashboard" with subtitle "The daily snapshot at a glance" loads,
     no error page, no blank screen

2. Scroll down to the "Manifest" card and read its top badge row
   - **Expect:** A mode badge reading "at ingest" (green), a "version 6" badge, a "frozen" badge
     (green), and a "not prospective-eligible" badge. Below that, four labeled hash chips
     ("Engine identity", "Candidate rule", "Cohort rule", "Manifest config") each show a
     truncated value ending in "…" — **none should read a bare "—"**. This confirms this
     iteration's schema migration didn't silently drop a column.

3. In the same "Manifest" card, click "Versions" to expand it
   - **Expect:** 6 version rows listed (v1 through v6), each with its own mode/eligibility/date —
     version 1 is still there, unhidden, byte-preserved by the migration

4. Navigate to `http://localhost:3255/?asof=2026-03-30`
   - **Expect:** Page text "Data as-of 2026-03-30" appears, and the "Manifest" card shows the
     sentence *"This manifest predates the freeze/integrity block — no stamps were recorded for
     it."* — **this is correct, not broken.** This is one of the 8 manifests this iteration's
     fail-closed fix targets, but it also predates the freeze/integrity block entirely, so the
     app shows this older message instead of a Basis badge. See "If Something Looks Wrong" below
     if you expected to see a new "unverifiable" badge here.

5. Navigate to `http://localhost:3255/?asof=2020-03-20`
   - **Expect:** Page text "Data as-of 2020-03-20" appears; the "Manifest" card's mode badge
     reads "retrospective"; below it, a "Basis:" badge is visible reading one of "Basis:
     available" (green), "Basis: rebuilt" (amber), or "Basis: unavailable" (red) — **never
     blank**

6. Click "Dashboard" in the left sidebar
   - **Expect:** URL loses the `?asof=` parameter; the page returns to showing the latest
     session's data

---

## What "Working Correctly" Looks Like

- The manifest strip on `/` renders fully (badges, hash chips, versions) with no "—" placeholders
  where a real hash/value used to be — the strongest signal the schema migration preserved every
  column
- Every manifest's "Basis:" line (when shown at all — see step 4) reads one of exactly four
  labels: "Basis: available" (green), "Basis: rebuilt" (amber), "Basis: unavailable" (red), or
  "Basis: unverifiable" (neutral gray) — never blank, never a raw `undefined`/error string
- Switching `?asof=` between a historical date and back to "Dashboard" never shows a flash of the
  wrong date's data first

## If Something Looks Wrong

- **Manifest card is blank, or a hash chip reads "—" where it used to show a value**: the schema
  migration may have dropped a column — check `runs/goal-market-compass-iter-11/j11-stage-b1-postmigration-row-column-diff.json`
  for a live discrepancy before assuming a fresh regression.
- **You expected to see the new "Basis: unverifiable" badge and don't**: this is expected on
  today's data. All 8 manifests with no recorded basis also predate the freeze/integrity block
  entirely (step 4's row is one of them), so they show the older "predates the freeze/integrity
  block" message instead of a Basis badge at all — the new badge currently has no live manifest
  it can render on. This is proven correct at the fixture level
  (`apps/backend/tests/test_manifest_invariants.py` TC-9–TC-13), not by anything visible today.
- **Navigating to `http://localhost:3255/market` 404s**: expected — that route has not been built
  yet (a pre-existing gap, not something this iteration touched). Use `/?asof=<date>` on `/`
  instead, per step 5 above.
- **Basis badge is missing on a manifest that has a mode badge (not "predates the freeze" text)**:
  this WOULD be a genuine regression — the badge should always render for any row whose `mode` is
  set. Flag it.
