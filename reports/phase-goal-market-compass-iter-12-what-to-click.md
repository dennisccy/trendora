# Phase goal-market-compass-iter-12 — What to Click (Operator Verification Guide)

**Phase:** goal-market-compass-iter-12 (J-11 Stage B1 CLEANUP)
**Time required:** ~5 minutes
**Written by:** ui-test-designer

**Not executed this iteration.** Maintenance isolation forbids booting any service this
iteration — nothing below has been clicked or observed yet. This guide is written for whoever
next starts the app (earliest: J-11 Stage G) to confirm this iteration's backend-only work (the
migration-utility fix, the `basis_disclosure` A4-bis fail-open close, and the `models.py` comment
correction) didn't regress the manifest strip, the basis-disclosure line, the sector labels, or
the next-session focus card. This iteration shipped no new UI — there is no new capability to
prioritize, only regression checks, scoped to the journeys named on the phase spec's `Required-
still-passing journeys:` and `Target journeys:` lines (J-01, J-04, J-05, J-06, J-08 — see
`reports/phase-goal-market-compass-iter-12-ui-test-plan.md` for why J-10/J-11 are excluded).

---

## Prerequisites

- Frontend running at `http://localhost:3255`, backend running and reachable at
  `http://localhost:8255/api/health`
- No login required
- No new seed data needed — every step below reads data that already exists in the live database;
  this iteration's own before/after fingerprint proves zero live-database writes occurred

---

## Verification Steps

1. Open `http://localhost:3255/` in your browser
   - **Expect:** Page heading "Dashboard" with subtitle "The daily snapshot at a glance" loads, no
     error page, no blank screen

2. Scroll down to the "Manifest" card and read its top badge row
   - **Expect:** A mode badge reading "at ingest" (green), a "version 6" badge, a "frozen" badge
     (green), and a "not prospective-eligible" badge. Below that, four labeled hash chips
     ("Engine identity", "Candidate rule", "Cohort rule", "Manifest config") each show a truncated
     value ending in "…" — **none should read a bare "—"**. This confirms this iteration's fixed
     migration code didn't change anything on the already-migrated live table.

3. Scroll to the "Next-session focus" card
   - **Expect:** Card titled "Next-session focus" renders — either candidate cards with Leadership/
     Entry/Risk words and scores, or (if none clear the bar this session) an explanatory sentence.
     It must NOT show the red "Next-session focus is unavailable — backend not reachable" message.

4. Navigate to `http://localhost:3255/?asof=2020-03-20`
   - **Expect:** Page text "Data as-of 2020-03-20" appears; the "Manifest" card's mode badge reads
     "retrospective"; below it, a "Basis:" badge reads "Basis: available" (green)

5. Navigate to `http://localhost:3255/?asof=2026-08-10`
   - **Expect:** Page text "Data as-of 2026-08-10" appears; the Basis badge reads "Basis: rebuilt"
     (amber) with the detail text "the source scanner run was recreated after this manifest was
     frozen" beside it — this exercises this iteration's actual A4-bis fix path (a valid, parseable
     timestamp that legitimately doesn't match)

6. Navigate to `http://localhost:3255/?asof=2026-03-30`
   - **Expect:** Page text "Data as-of 2026-03-30" appears, and the "Manifest" card shows the
     sentence *"This manifest predates the freeze/integrity block — no stamps were recorded for
     it."* — **this is correct, not broken.** See "If Something Looks Wrong" below if you expected
     a new "Basis: unverifiable" badge here instead.

7. Click "Dashboard" in the left sidebar
   - **Expect:** URL loses the `?asof=` parameter; the page returns to showing the latest session's
     data

8. Navigate to `http://localhost:3255/stocks`
   - **Expect:** Page heading "Stocks" loads with a populated leaderboard table; open the "Sector"
     filter dropdown, select "Unassigned" — the filtered row count should be a small minority of
     the total (at most 5%), not the majority

---

## What "Working Correctly" Looks Like

- The manifest strip on `/` renders fully (badges, hash chips, versions) with no "—" placeholders
  where a real hash/value used to be — the strongest signal this iteration's fixed migration code
  didn't disturb the already-migrated live table
- Every manifest's "Basis:" line (when shown at all — see step 6) reads one of exactly four labels:
  "Basis: available" (green), "Basis: rebuilt" (amber), "Basis: unavailable" (red), or "Basis:
  unverifiable" (neutral gray) — never blank, never a raw `undefined`/`null` string
- The "Next-session focus" card never shows a bare composite score or advice-style wording — every
  candidate reason cites a threshold and a stored actual value
- The `/stocks` Sector filter's "Unassigned" bucket stays small (≤5% of rows), not the dominant
  majority it was before J-01 originally shipped

## If Something Looks Wrong

- **Manifest card is blank, or a hash chip reads "—" where it used to show a value**: this would be
  a genuine regression in the (fixture-only, never-run-live) migration fix or an unrelated live-data
  problem — check `runs/goal-market-compass-iter-12/j11-stage-b1-cleanup-fingerprint-diff.json`
  (should say `identical_except_capture_timestamps: true`) before assuming a fresh regression.
- **You expected to see a "Basis: unverifiable" badge and don't**: expected on today's data. All 8
  manifests with no recorded generation basis also predate the freeze/integrity block entirely
  (step 6's row is one of them), so they show the older "predates the freeze/integrity block"
  message instead of any Basis badge. This is proven correct at the fixture level
  (`apps/backend/tests/test_manifest_invariants.py`'s `test_a4bis_*` cluster), not by anything
  visible today.
- **Navigating to `http://localhost:3255/market` 404s**: expected — that route has not been built
  yet (a pre-existing gap, not something this iteration touched). Use `/?asof=<date>` on `/`
  instead, per steps 4-6 above.
- **Basis badge is missing on a manifest that has a mode badge (not the "predates the freeze" text)**:
  this WOULD be a genuine regression — the badge should always render for any row whose `mode` is
  set. Flag it.
- **"Next-session focus" shows the red "unavailable — backend not reachable" message**: check the
  backend is actually up at `http://localhost:8255/api/health` first; if it's up and the message
  still shows, flag it — this iteration didn't touch this code path, so this would be an unrelated
  regression worth investigating separately.
