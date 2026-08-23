# Phase goal-market-compass-iter-11 — UI Test Plan

**Phase:** goal-market-compass-iter-11 (J-11 Stage B1-completion)
**Date:** 2026-08-23
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255
**Backend URL:** http://localhost:8255 (`GET /api/health`, `GET /api/compass?as_of=<date>`)

**Not executed this iteration.** Maintenance isolation (ruling A5) forbids booting any
application service, browser QA, or the replay lane for the whole of iter-11 — nothing below
has been run, clicked, or observed. This plan is authored so an operator, or the first future
iteration allowed to boot the app (Stage G is the earliest candidate), can execute it. No step
below implies anything has already passed.

---

## Scope note (read before executing)

The phase spec's own Goal-Mode-Metadata line reads `**Frontend Present:** yes`, but the
dispatching coordinator's operational note for this run states the intended reading is
`Frontend Present: no` ("no NEW UI surface this iteration") and directs this document to follow
the "Backend-only phase handling" rule exactly. This matches the phase spec's own body text
verbatim: "New user-facing capability: None", "New user actions: None", "UI surface changes:
None structurally" — the frontend diff this iteration is a type-widening + a mechanical ternary
extraction, not a new page, route, or control. `reports/phase-goal-market-compass-iter-11-ui-surface-map.md`
and the matching user-visible-changes report are both empty ("Not mapped/observed — maintenance
isolation"), so there is no UI-surface-map row to derive a NEW-surface (`UT-01`-style) case from.
Per the "Backend-only phase handling" rule, this document instead emits exactly one
`UT-<journey-id>` regression case for every journey named on EITHER the phase spec's own
`Required-still-passing journeys:` line OR its `Target journeys:` line.

This iteration's phase-spec metadata line reads, in full:

> **Required-still-passing journeys:** none mechanically re-verifiable this iteration —
> maintenance isolation ... keeps the browser-QA lane and the deterministic-replay lane shut, so
> no journey can be replayed. For evaluator awareness: **J-05, J-06** (manifest freeze/integrity
> — the direct schema owner of the table this iteration migrates) and **J-08** (retrospective
> `basis` disclosure at `/market` / `/?asof=`) are the journeys whose Data-Contract value this
> iteration's work touches, and should be the first ones re-verified once Stage G reopens the
> browser/replay lanes.

> **Target journeys:** J-11

**This line is NOT treated as empty.** It opens with the word "none" but goes on to explicitly
name J-05, J-06, and J-08 as the journeys this iteration's work touches. This project's own
binding lesson (carried in the `ui-test-designer` agent instructions, sourced from an
ops-hardening iter-40/41 incident) exists precisely to stop a hedged "none ... but see these
names" line from being read as a bare, contentless "none" — that exact misreading, applied
blindly, was the root cause of a 5-consecutive-ESCALATE session where journeys silently rotted
unverified while every gate reported clean. So: **J-05, J-06, J-08** each get a regression case
below. **J-11** (the Target journey) does **not** — see the explicit exclusion note before the
test cases.

**Grounding.** `docs/goal.md` has no checked-in Playwright/replay script for J-05, J-06, or J-08
(`runs/goal-session-market-compass/journey-scripts/` only holds `J-01.json`–`J-04.json`), so each
case below is derived directly from that journey's own "Steps:"/"Acceptance:" prose in
`docs/goal.md`'s "Must-have user journeys" section, cross-checked against the CURRENT live
evidence artifacts this iteration produced (`runs/goal-market-compass-iter-11/j11-stage-b1-postmigration-dump.json`,
all 24 rows read directly for this report) and the current frontend source
(`apps/frontend/components/compass-manifest-strip.tsx`, `apps/frontend/components/sidebar.tsx`,
`apps/frontend/app/page.tsx`) — not copied verbatim from goal.md's more general phrasing, because
two of goal.md's literal example values are now stale (see the two flagged findings below).

---

## Two findings that change how these tests must be executed (read before running UT-J-06/UT-J-08)

**Finding 1 — the new `"unverifiable"` badge is not reachable on ANY currently-stored live
manifest.** Read directly from `runs/goal-market-compass-iter-11/j11-stage-b1-postmigration-dump.json`
(all 24 rows, post-migration): the 8 rows with `generation_json` NULL are ids 1-8 —
as_of `2026-08-12` v1, `2026-07-23` v1, `2026-04-01` v1, `2026-03-31` v1, `2026-03-30` v1,
`2005-04-01` v1, `2001-04-17` v1, `1996-02-01` v1. **Every one of these 8 rows ALSO has `mode:
NULL` and `frozen: false`** — i.e. they are all pre-existing "pre-freeze-era" rows (predating the
freeze/integrity block entirely, not merely missing a basis). `compass-manifest-strip.tsx`'s
`CompassManifestStrip` computes `const preFreezeEra = view.mode === null` and, when true, renders
the paragraph *"This manifest predates the freeze/integrity block — no stamps were recorded for
it."* **instead of** `<BasisLine basis={view.basis} />` — the Basis badge, and therefore this
iteration's new `"Basis: unverifiable"` label, never renders for these 8 rows at all. This is
pre-existing, untouched code (this iteration did not change `preFreezeEra`'s logic), and the
backend fix itself is independently correct and proven by fixture tests
(`test_manifest_invariants.py` TC-9–TC-13, cited in the dev handoff) — but it means **no step
below can show an operator the literal `"Basis: unverifiable"` badge on today's live data.**
Treat its absence in every step below as the correct, expected, currently-unreachable-by-
coincidence state, not a failed check.

**Finding 2 — J-08's "market relocation" has not been built yet.** goal.md's J-08 acceptance
describes a root page renamed "Today", a new `/market` route receiving the former dashboard body,
and a sidebar listing "Today" then "Market". Read directly from the current codebase for this
report: `apps/frontend/app/` has **no** `market/` directory; `apps/frontend/components/sidebar.tsx`'s
`NAV` array has **no** `/market` entry and labels `/` `"Dashboard"` (not `"Today"`);
`apps/frontend/app/page.tsx` renders `<PageHeading title="Dashboard" subtitle="The daily snapshot
at a glance" />`. `runs/goal-session-market-compass/state/blueprint.md` itself marks both `Today
(/)` and `Market (/market)` as **`[TARGET]`** — i.e. planned, not yet landed. This is a
pre-existing gap this iteration did not touch or regress. **UT-J-08 below is scoped to only the
`?asof=` / retrospective-manifest subset of J-08 that is actually reachable today, on `/`** — it
does not test a `/market` URL, which would 404.

---

## Test Cases

---

### UT-J-05 — Frozen next-session manifest still serves its full provenance stamps after the schema migration (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/` (Dashboard page, "Manifest" card)

**Preconditions:**
- Frontend running at http://localhost:3255, backend running and reachable at
  http://localhost:8255/api/health
- The live `apps/backend/data/trendora.db`'s `next_session_manifests` table has already been
  migrated to the FK-free schema by this iteration's script (true in the current live DB per the
  dev handoff — `docs/handoffs/goal-market-compass-iter-11-dev.md`)
- No login required
- **This case is observational only.** It reads the ALREADY-STORED frontier manifest for as_of
  `2026-08-12` (live row id 23: version 6, mode `at_ingest`, `frozen: true`) — it does not run a
  fresh backfill or mutate any data. This iteration's own scope forbids further live-data-mutating
  operations against the shared database ("Any further live fetch" is explicitly OUT OF SCOPE),
  so this regression check verifies the migration preserved a manifest that was already frozen in
  an earlier iteration, rather than reproducing J-05's original freeze workflow from scratch.

**Steps:**
1. Navigate to `http://localhost:3255/`
2. Confirm the page heading reads "Dashboard" with subtitle "The daily snapshot at a glance"
3. Scroll to the "Manifest" card (`data-testid="compass-manifest-strip"`)
4. Within the badge row (`data-testid="compass-manifest-badges"`), read the mode badge, the
   version badge, the frozen badge, and the prospective-eligible badge
   (`data-testid="compass-manifest-prospective-eligible"`)
5. Read the four hash chips labeled "Engine identity", "Candidate rule", "Cohort rule", "Manifest
   config"
6. Read the "Dataset stamp:", "Universe pool", "Members:", "Profile:" line
7. Expand "Versions" (`data-testid="compass-manifest-versions"`)

**Expected Result:**
- Step 2: page loads with no error boundary, no blank card
- Step 4: mode badge reads "at ingest" (`ok`/green variant); "version 6" badge visible; frozen
  badge reads "frozen" (`ok`/green); the prospective-eligible badge reads "not prospective-eligible"
  (matches the live row: `prospective_eligible: false` — only a fresh live freeze's version 1 can
  ever read `true`, and this is a later regenerated version)
- Step 5: all four hash chips show a truncated monospace value ending in "…" — none read "—"
  (an empty/missing hash would mean the migration silently dropped or nulled a column)
- Step 6: "Dataset stamp" shows a non-"—" value; "Members" shows a positive integer
- Step 7: the versions list shows 6 entries
  (`data-testid="compass-manifest-version-1"` through `"compass-manifest-version-6"`), each with
  its own mode/eligibility/timestamp; version 1's row is still present, listed, and readable —
  NOT hidden or dropped by the migration (AG-18: "all 24 rows ... survive exactly")

---

### UT-J-06 — Frozen manifests remain byte-stable and basis disclosure still reports honestly after the fail-closed fix (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`, `/?asof=`

**Preconditions:**
- Frontend/backend running as above
- Read **Finding 1** above before starting — it directly governs what this case can and cannot
  show
- Two concrete rows to check (both read directly from the live post-migration dump for this
  report, not invented):
  - **(a)** as_of `2020-03-20` — mode `retrospective`, `frozen: true`, `generation_json` PRESENT
    (this row is NOT one of the 8 NULL-generation_json rows)
  - **(b)** as_of `2026-03-30` — mode NULL, `frozen: false`, `generation_json` NULL (one of the 8
    rows this iteration's fail-closed fix targets)

**Steps:**
1. Navigate to `http://localhost:3255/?asof=2020-03-20`
2. Confirm the page text "Data as-of 2020-03-20" is visible
3. Scroll to the "Manifest" card; read the mode badge
4. Within the same card, read the basis line (`data-testid="compass-manifest-basis"`)
5. Navigate to `http://localhost:3255/?asof=2026-03-30`
6. Confirm the page text "Data as-of 2026-03-30" is visible
7. Scroll to the "Manifest" card

**Expected Result:**
- Step 3: mode badge reads "retrospective" (`default` variant)
- Step 4: a `Badge` is visible reading exactly one of the three PRE-EXISTING labels — "Basis:
  available" (`ok`/green), "Basis: rebuilt" (`warn`/amber), or "Basis: unavailable" (`danger`/red)
  — never blank, and never "Basis: unverifiable" (this row's `generation_json` is present, so it
  cannot reach the new fail-closed branch). If `basis.detail` is non-null its text renders in
  faint gray beside the badge.
- Step 7: the card renders the text "This manifest predates the freeze/integrity block — no
  stamps were recorded for it." (`data-testid="compass-manifest-pre-freeze-era"`) — **no** badge
  row, **no** hash chips, and **no** `compass-manifest-basis` element at all for this row. This is
  the CORRECT, expected rendering per Finding 1 above — it is not evidence the fail-closed fix is
  broken; the fix's correctness for exactly this row is proven at the fixture level
  (`test_manifest_invariants.py` TC-9/TC-10, both exercising a NULL `generation_json` row), not by
  anything the live UI can currently show.
- Across both navigations: no console error, no crash, no blank card — the schema migration and
  the `basis_disclosure` fail-closed fix introduce no regression in either rendering path

---

### UT-J-08 — Retrospective `?asof=` view still serves the exact historical manifest, never a newer one (regression, scoped)

**Type:** regression
**Priority:** P1
**Surface:** `/`, `/?asof=`

**Scope note — read before executing:** per **Finding 2** above, the `/market` route and the
"Today"/"Market" sidebar split described in goal.md's full J-08 acceptance do not exist in the
current codebase. This case therefore covers only the "history never lies" / retrospective-
manifest subset of J-08 that is reachable today, on the existing `/` page (registered as J-05/J-06's
home in `runs/goal-session-market-compass/state/blueprint.md`). **Do not navigate to a `/market`
URL** — it will 404; that is a pre-existing gap, not something this iteration touched.

**Preconditions:**
- Frontend/backend running as above
- as_of `2020-03-20` is a genuinely retrospective, pre-feature historical run date (mode
  `retrospective`, `frozen: true`, confirmed from the live dump)

**Steps:**
1. Navigate to `http://localhost:3255/?asof=2020-03-20`
2. Confirm the page text "Data as-of 2020-03-20"
3. In the "Manifest" card, confirm the mode badge reads "retrospective"
4. Open a NEW browser tab and navigate DIRECTLY to `http://localhost:3255/?asof=2020-03-20`
   (a fresh full page load, not a client-side link click)
5. Confirm the FIRST rendered content already shows "Data as-of 2020-03-20"
6. In the left sidebar, click "Dashboard" (the top nav item)
7. Confirm the URL no longer carries `?asof=` and the page shows the current latest as-of date

**Expected Result:**
- Steps 2-3: the exact stored `2020-03-20` manifest is served — its payload's `as_of` field equals
  `2020-03-20`, never a newer manifest's contents
- Step 5: no visible flash/repaint from "Latest" data to the historical view — the first paint on
  a cold/fresh load is already `2020-03-20`-scoped (no latest-then-D repaint)
- Step 7: returning to "Dashboard" (no `asof` param) shows the current/latest session state; the
  sidebar's own links no longer carry `?asof=2020-03-20`

---

## Excluded: J-11 (Target journey) — no browser case written

`docs/goal.md`'s own J-11 entry states its Walkthrough acceptance item verbatim: **"Walkthrough:
waived — maintenance repair of the derived layer with no UI surface of its own."** (line ~1383).
This matches the exact precedent already established in this project for an identically-shaped
journey: `reports/phase-goal-market-compass-iter-7-ui-test-plan.md` excluded J-10 on the same
grounds (J-10's own entry: "Walkthrough: waived — data-layer repair with no UI surface change of
its own"). Inventing a click path for a journey goal.md itself declares has none would mean
testing something that cannot exist — the six Stage-C-precondition acceptance items this
iteration re-proves for J-11 (schema DDL, `pragma_foreign_key_check`, byte-equality dumps,
mutation accounting) are DB/schema/API-level facts, not renderable UI state; they are already
covered by the fixture tests and the live-DB evidence artifacts cited in
`docs/handoffs/goal-market-compass-iter-11-dev.md`, not by anything a browser can observe. No
`UT-J-11` row appears below.

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-J-05 | Frozen manifest survives the schema migration intact | regression | P1 | `/` |
| UT-J-06 | Basis disclosure still honest post fail-closed fix | regression | P1 | `/`, `/?asof=` |
| UT-J-08 | Retrospective `?asof=` serves the exact historical manifest (scoped — no `/market`) | regression | P1 | `/`, `/?asof=` |

**Zero NEW-surface test cases** — consistent with the dispatch coordinator's "no NEW UI surface
this iteration" reading, an empty UI surface map, and "New user-facing capability: None" /
"UI surface changes: None structurally" in the phase spec's own body text. No `UT-01`-style case
exists in this plan.

**Zero `UT-J-11` case** — J-11 (this iteration's own Target journey) has no UI surface of its own
by goal.md's own explicit declaration; see the exclusion note above.

**All 3 test cases are P1** — J-05, J-06, and J-08 are each named on the phase spec's own
`Required-still-passing journeys:` metadata line as the journeys whose Data-Contract value this
iteration's work touches.

**Before executing:** re-read the two findings above. Neither is a defect in this iteration's
work — both are honest, evidence-grounded observations about what the current live dataset can
and cannot show through the UI today, so that whoever runs this plan does not mistake an
expected, currently-unreachable state (the new `"unverifiable"` badge; the `/market` route) for a
failure.
