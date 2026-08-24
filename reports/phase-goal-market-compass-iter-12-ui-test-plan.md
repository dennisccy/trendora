# Phase goal-market-compass-iter-12 — UI Test Plan

**Phase:** goal-market-compass-iter-12 (J-11 Stage B1 CLEANUP)
**Date:** 2026-08-24
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255
**Backend URL:** http://localhost:8255 (`GET /api/health`, `GET /api/compass?as_of=<date>`)

**Not executed this iteration.** Maintenance isolation (ruling A5/A13, session-level) forbids
booting any application service, browser QA, or the replay lane for the whole of iter-12 —
nothing below has been run, clicked, or observed. This plan is authored so an operator, or the
first future iteration allowed to boot the app (Stage G is the earliest candidate), can execute
it. No step below implies anything has already passed.

---

## Scope note (read before executing)

The phase spec's own Goal-Mode-Metadata reads `**Frontend Present:** no` — this iteration's four
jobs (migration-utility fix, `basis_disclosure` A4-bis fail-open close, a `models.py` comment
correction, and a static honesty re-check of `compass-manifest-strip.tsx`'s `preFreezeEra` branch)
touched zero frontend files and shipped no new page, route, or control. `reports/phase-goal-market-compass-iter-12-ui-surface-map.md`
and the matching user-visible-changes report are both empty ("Not mapped/observed — maintenance
isolation"), so there is no UI-surface-map row to derive a NEW-surface (`UT-01`-style) case from.

Per the ui-test-designer "Backend-only phase handling" rule, this document instead emits exactly
one `UT-<journey-id>` regression case for every journey named on EITHER the phase spec's own
`Required-still-passing journeys:` line OR its `Target journeys:` line — read from
`docs/phases/goal-market-compass-iter-12.md`'s own Goal Mode Metadata block:

> **Target journeys:** J-11

> **Required-still-passing journeys:** none mechanically re-verifiable this iteration —
> maintenance isolation (ruling A5, still active) keeps the browser-QA lane and the
> deterministic-replay lane shut, so no journey can be replayed. For evaluator awareness only:
> **J-05, J-06** (manifest freeze/integrity — the direct owner of the table `models.py`'s comment
> and the migration utility describe) and **J-08** (retrospective `basis` disclosure at `/market`
> / `/?asof=`) are the journeys whose Data-Contract value this iteration's read-path fix touches,
> and should be the first re-verified once Stage G reopens the browser/replay lanes. **J-01, J-04,
> J-10** stay `passing` per `iteration-state.md`'s "Do not redo" list — untouched by this
> iteration.

**This line is not treated as empty, and its "stay passing / Do not redo" framing is not treated
as an exemption from writing a case.** The line opens with the word "none" but goes on to name six
journeys by ID. This project's own binding lesson (carried in the `ui-test-designer` agent
instructions, sourced from an ops-hardening iter-40/41 incident) exists precisely to stop a hedged
"none … but see these names" line — or a line that tells the reader a named journey doesn't need
checking — from suppressing coverage; that exact misreading, applied blindly, was the root cause of
a 5-consecutive-ESCALATE session where journeys silently rotted unverified while every gate
reported clean. So every journey ID literally named on either line is a candidate for a case:
**J-01, J-04, J-05, J-06, J-08, J-10, J-11**.

**Exclusion criterion used below (the same one iter-11's ui-test-designer used for J-11, not a new
one invented for this report):** a journey is excluded ONLY when `docs/goal.md`'s OWN entry for
that journey states its Walkthrough is waived / it has no UI surface of its own — an objective,
checkable fact about the journey, never a spec-line's suggestion that this iteration chooses not to
recheck it. Checked directly against `docs/goal.md`, lines noted below:

- **J-10** (line ~934): *"Walkthrough: waived — raw-layer incident repair with no UI surface change
  of its own."* → **excluded**.
- **J-11** (line ~935): *"Walkthrough: waived — maintenance repair of the derived layer with no UI
  surface of its own."* → **excluded**. (Matches the exact precedent already established for this
  same journey in `reports/phase-goal-market-compass-iter-11-ui-test-plan.md`.)
- **J-01** (line ~235): *"Walkthrough: a `[NEW]`-flagged walkthrough of the shrunken Unassigned
  filter and the methodology disclosure…"* — a real walkthrough exists → **case written** (UT-J-01).
- **J-04** (line ~350): *"Walkthrough: a `[NEW]`-flagged walkthrough of one candidate's
  why/cautions/checklist/what-would-change…"* — a real walkthrough exists → **case written**
  (UT-J-04).
- **J-05** (line ~424): real walkthrough exists → **case written** (UT-J-05).
- **J-06** (line ~478): real walkthrough exists → **case written** (UT-J-06).
- **J-08** (line ~548): real walkthrough exists → **case written** (UT-J-08).

**Grounding.** Each case below is derived directly from that journey's own "Steps:"/"Acceptance:"
prose in `docs/goal.md`'s "Must-have user journeys" section, cross-checked against the CURRENT
frontend source (`apps/frontend/components/compass-manifest-strip.tsx`,
`apps/frontend/components/compass-focus-section.tsx`, `apps/frontend/app/stocks/page.tsx`,
`apps/frontend/app/stocks/[ticker]/page.tsx`, `apps/frontend/app/methodology/page.tsx`,
`apps/frontend/components/sidebar.tsx`, `apps/frontend/app/page.tsx`, `apps/frontend/lib/basis-disclosure-label.ts`
— all read directly for this report, none copied from iter-11's report without re-checking) and
against this iteration's own live-read-only evidence
(`runs/goal-market-compass-iter-12/j11-stage-b1-live-reverification.json`,
`docs/handoffs/goal-market-compass-iter-12-dev.md`) for J-05/J-06/J-08's specific row data.
`git log` on the relevant frontend files shows no commit since iter-11's own report was written,
and this iteration's dev handoff confirms zero frontend files were touched — so the two findings
iter-11 recorded (below) still hold and are independently re-confirmed here, not merely copied.

**J-01 and J-04 caveat:** neither journey's code was touched by this iteration, and no fresh
per-row live evidence for `/stocks` or the focus section was produced this iteration (the dev
handoff's evidence is entirely `next_session_manifests`-scoped). This session's AG-9 J-10 exception
is exhausted and "any further live fetch" is explicitly OUT OF SCOPE for this iteration, so neither
case below reproduces J-01's or J-04's original data-mutating setup steps (J-01 step 1's
remove+backfill) — both are scoped to **observational, read-only** checks of already-serving state,
using the acceptance criterion's threshold language rather than an invented specific value. Do not
assume a specific live percentage or ticker; read it live in step at execution time.

---

## Two findings that change how UT-J-05/UT-J-06/UT-J-08 must be executed (unchanged since iter-11, independently re-confirmed for this report)

**Finding 1 — the `"unverifiable"` badge text is not reachable on ANY currently-stored live
manifest.** Re-derived this iteration (`docs/handoffs/goal-market-compass-iter-12-dev.md`'s TC-20/
TC-23, `j11-stage-b1-live-reverification.json`): all 24 live manifest rows evaluated read-only
against the FIXED `basis_disclosure` give `{unverifiable: 8, rebuilt: 9, available: 5,
unavailable: 2}`. Every one of the 8 `unverifiable` rows (ids 1-8, as_of 2026-08-12/2026-07-23/
2026-04-01/2026-03-31/2026-03-30/2005-04-01/2001-04-17/1996-02-01) ALSO has `mode: null` — the
TC-23 overlap is complete (8/8). `compass-manifest-strip.tsx`'s `preFreezeEra` branch
(`view.mode === null`, lines 146-149) renders ONLY the static sentence "This manifest predates the
freeze/integrity block — no stamps were recorded for it." and NEVER reaches `BasisLine` (that call
is in the `else` branch, line 186) — so the new `"Basis: unverifiable"` label, though correctly
implemented and fixture-proven (`test_manifest_invariants.py`'s `test_a4bis_*` cluster), has no live
row it can currently render on. Treat its absence in every step below as the correct, expected,
currently-unreachable-by-coincidence state, not a failed check.

**Finding 2 — J-08's "market relocation" has not been built yet.** Re-checked directly for this
report: `apps/frontend/app/` has **no** `market/` directory (confirmed via directory listing);
`apps/frontend/components/sidebar.tsx`'s `NAV` array has exactly one entry, `{ href: "/", label:
"Dashboard" }` — **no** `/market` entry; `apps/frontend/app/page.tsx` renders `<PageHeading
title="Dashboard" subtitle="The daily snapshot at a glance" />`. This is a pre-existing gap this
iteration did not touch or regress (this iteration's diff is `compass.py`, `j11_schema_migration.py`,
`models.py`, and their tests only — zero frontend files, per the dev handoff's "Files Changed").
**UT-J-08 below is scoped to only the `?asof=` / retrospective-manifest subset of J-08 that is
actually reachable today, on `/`** — it does not test a `/market` URL, which would 404.

---

## Test Cases

---

### UT-J-01 — Sector attribution stays honest and near-complete on `/stocks` (regression, observational)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks`, `/stocks/[ticker]`, `/methodology`

**Preconditions:**
- Frontend running at http://localhost:3255, backend running and reachable at
  http://localhost:8255/api/health
- No login required
- **Observational only.** This iteration produced no fresh sector data and did not touch
  `universe.pool_sector_aliases` or `scoring.score_stocks`. This session's AG-9 J-10 exception is
  exhausted and any further live fetch/backfill is explicitly OUT OF SCOPE this iteration, so this
  case reads the sector labels already stored from the run that originally landed J-01, rather than
  reproducing J-01's own Step 1 (a seed-safe Remove + backfill over the last two trading days).

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Confirm the page heading reads "Stocks" with a subtitle mentioning "ranked by Leadership"
3. Locate the "Sector" filter control (labeled "Sector", `aria-label="Filter by sector"`) above the
   table and open its dropdown
4. Select the "Unassigned" option
5. Note the number of rows shown with the filter applied, then clear the filter back to "All" and
   note the total row count
6. With the filter cleared, find any row in the table whose Sector column is NOT "Unassigned" and
   note its ticker and displayed sector text
7. Navigate to `http://localhost:3255/stocks/<that ticker>` (replace `<that ticker>` with the
   ticker noted in step 6)
8. Read the Sector value shown in that page's header area
9. Navigate to `http://localhost:3255/methodology`
10. Locate the "Stock sector labels" card

**Expected Result:**
- Step 2: page loads with a populated table, no console error, no blank page
- Step 5: the "Unassigned"-filtered row count divided by the total row count is **at most 5%**
  (J-01's acceptance bar — record the actual observed percentage; do not assume any specific
  number, just confirm the ratio is ≤5%)
- Step 8: the Sector text on the stock detail page is **identical** to the Sector text noted from
  the leaderboard row in step 6 — both must reflect the same stored `sector` field, never an
  independently derived or differing value
- Step 10: a card titled "Stock sector labels" (`data-testid="universe-sector-basis"`) is visible
  and its body text discloses that stock sector labels come from a two-source basis (a curated
  config mapping first, a committed universe-pool snapshot fallback second) and explicitly states
  the labels are current-only (no point-in-time / historical sector history)
- No step shows a blank, `null`, or `undefined` sector value anywhere — an unmapped symbol renders
  the word "Unassigned", never a fabricated sector name

---

### UT-J-04 — Next-session focus explains why, why-not, and what-would-change-it (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/` (Next-session focus card)

**Preconditions:**
- Frontend/backend running as above
- **Observational only** — this iteration touched no code in `compass.evaluate_selection` or the
  focus-section component

**Steps:**
1. Navigate to `http://localhost:3255/`
2. Scroll to the "Next-session focus" card (`data-testid="compass-focus-section"`)
3. If candidate cards are shown (`data-testid="compass-candidate-list"`), open the first candidate
   card and read its Leadership / Entry / Risk fields
4. Within that same card, click "Eligibility checklist" to expand it
5. Within the same card, click "What would change this" to expand it
6. Read the "Invalidation:" line at the bottom of the card
7. Click "Not priority (N)" below the candidate list/empty message to expand it

**Expected Result:**
- Step 2: the card renders titled "Next-session focus" — it must NOT show the red "Next-session
  focus is unavailable — backend not reachable" state (`data-testid="compass-focus-unavailable"`);
  if that DOES appear, the backend is not actually reachable (a service/connectivity problem, not
  this journey's own regression)
- Step 3: if `selection.candidates` is non-empty, each of Leadership/Entry/Risk shows a word plus a
  one-decimal numeric score in parentheses (e.g. "Strong (7.2)") — never a bare number with no
  word, never blank. If `selection.candidates` is empty instead, the card shows explanatory text at
  `data-testid="compass-focus-empty"` (the served `candidates_empty_reason`) — never a bare empty
  grid with no explanation
- Step 4: every checklist row shows a condition label, an "actual vs threshold" numeric pair, and a
  colored Badge reading exactly one of: Pass, Miss, Supportive, Neutral, Unknown, NA — never blank
- Step 5: every "what would change this" row shows a condition, an actual-vs-threshold pair, and
  the word "met" or "not met" — never blank
- Step 6: the Invalidation line shows non-empty text
- Step 7: the disclosure expands to a list of ticker entries (`data-testid="compass-why-not-<TICKER>"`),
  each naming its failed condition(s) with actual/threshold/distance values — OR, if there are zero
  entries, the exact text "No near-miss names this session."
- Nowhere on the page does a single composite "fit score" appear, and no imperative trade-advice
  wording ("buy", "you should enter") appears anywhere in the card

---

### UT-J-05 — Frozen next-session manifest still serves its full provenance stamps after this iteration's read-path work (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/` (Dashboard page, "Manifest" card)

**Preconditions:**
- Frontend running at http://localhost:3255, backend running and reachable at
  http://localhost:8255/api/health
- No login required
- **This case is observational only.** It reads the already-stored frontier manifest for as_of
  `2026-08-12` (live row id 23: version 6, mode `at_ingest`, `frozen: true`, `basis_status:
  rebuilt`, per `runs/goal-market-compass-iter-12/j11-stage-b1-live-reverification.json`, captured
  2026-08-24) — it does not run a fresh backfill or mutate any data. This iteration's before/after
  fingerprint (`j11-stage-b1-cleanup-fingerprint-diff.json`) proves this row's stored bytes are
  unchanged by this iteration's work; this case is the live confirmation that the running app
  actually renders that unchanged row correctly, not merely that the DB row is intact.

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
7. Click "Versions" to expand (`data-testid="compass-manifest-versions"`)

**Expected Result:**
- Step 2: page loads with no error boundary, no blank card
- Step 4: mode badge reads "at ingest" (`ok`/green variant); "version 6" badge visible; frozen
  badge reads "frozen" (`ok`/green); the prospective-eligible badge reads "not prospective-eligible"
  (matches the live row — only a fresh live freeze's version 1 can ever read "prospective-eligible")
- Step 5: all four hash chips show a truncated monospace value ending in "…" — none read "—" (an
  empty/missing hash would mean the migration silently dropped or nulled a column)
- Step 6: "Dataset stamp" shows a non-"—" value; "Members" shows a positive integer
- Step 7: the versions list shows 6 entries (`data-testid="compass-manifest-version-1"` through
  `"compass-manifest-version-6"`), each with its own mode/eligibility/timestamp; version 1's row is
  still present, listed, and readable — NOT hidden or dropped

---

### UT-J-06 — Basis disclosure reports honestly across all four states after the A4-bis fail-open close (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/?asof=<date>`

**Preconditions:**
- Frontend/backend running as above
- Read **Finding 1** above before starting — it governs step 9's expected result
- Four concrete rows to check, all read directly from this iteration's own live re-verification
  evidence (`runs/goal-market-compass-iter-12/j11-stage-b1-live-reverification.json`, captured
  2026-08-24, confirmed zero live writes since by this iteration's own fingerprint diff):
  - **(a)** as_of `2020-03-20` — mode `retrospective`, `generation_json` present, `basis_status:
    available` (row id 19)
  - **(b)** as_of `2026-08-10` — mode `retrospective`, `generation_json` present, `basis_status:
    rebuilt` (row id 21)
  - **(c)** as_of `2026-08-05` — mode `retrospective`, `generation_json` present, `basis_status:
    unavailable` (two stored versions at this as_of, ids 12/14 — either version's badge reads the
    same status)
  - **(d)** as_of `2026-03-30` — mode `null` (pre-freeze-era), `generation_json` degenerate,
    `basis_status: unverifiable` per the backend, but see Finding 1 for what actually renders

**Steps:**
1. Navigate to `http://localhost:3255/?asof=2020-03-20`
2. Confirm the page text "Data as-of 2020-03-20" is visible; in the "Manifest" card, read the badge
   at `data-testid="compass-manifest-basis"`
3. Navigate to `http://localhost:3255/?asof=2026-08-10`
4. Confirm the page text "Data as-of 2026-08-10"; read the Basis badge and its detail text
5. Navigate to `http://localhost:3255/?asof=2026-08-05`
6. Confirm the page text "Data as-of 2026-08-05"; read the Basis badge and its detail text
7. Navigate to `http://localhost:3255/?asof=2026-03-30`
8. Confirm the page text "Data as-of 2026-03-30"; read the "Manifest" card

**Expected Result:**
- Step 2: badge reads exactly "Basis: available" (`ok`/green variant)
- Step 4: badge reads exactly "Basis: rebuilt" (`warn`/amber variant); the faint gray detail text
  beside it reads "the source scanner run was recreated after this manifest was frozen"
- Step 6: badge reads exactly "Basis: unavailable" (`danger`/red variant); the faint gray detail
  text reads "the underlying scanner run for this as-of is no longer stored"
- Step 8: the card renders the text "This manifest predates the freeze/integrity block — no stamps
  were recorded for it." (`data-testid="compass-manifest-pre-freeze-era"`) — **no** badge row and
  **no** `compass-manifest-basis` element at all. Per Finding 1, this is the CORRECT, expected
  rendering — it is not evidence the A4-bis fix is broken; the fix's correctness for exactly this
  row is proven at the fixture level (`test_manifest_invariants.py`'s `test_a4bis_*` cluster and
  `test_tc9_*`/`test_tc10_*`), not by anything the live UI can currently show
- Across all four navigations: no console error, no crash, no blank badge, and never the literal
  text "Basis: undefined" or "Basis: null"

---

### UT-J-08 — Retrospective `?asof=` view still serves the exact historical manifest, never a newer one (regression, scoped)

**Type:** regression
**Priority:** P1
**Surface:** `/`, `/?asof=`

**Scope note — read before executing:** per **Finding 2** above, the `/market` route and the
"Today"/"Market" sidebar split described in goal.md's full J-08 acceptance do not exist in the
current codebase. This case therefore covers only the "history never lies" / retrospective-
manifest subset of J-08 that is reachable today, on the existing `/` page. **Do not navigate to a
`/market` URL** — it will 404; that is a pre-existing gap, not something this iteration touched.

**Preconditions:**
- Frontend/backend running as above
- as_of `2020-03-20` is a genuinely retrospective, pre-feature historical run date (mode
  `retrospective`, `generation_json` present, confirmed from this iteration's live re-verification
  dump)

**Steps:**
1. Navigate to `http://localhost:3255/?asof=2020-03-20`
2. Confirm the page text "Data as-of 2020-03-20"
3. In the "Manifest" card, confirm the mode badge reads "retrospective"
4. Open a NEW browser tab and navigate DIRECTLY to `http://localhost:3255/?asof=2020-03-20` (a
   fresh full page load, not a client-side link click)
5. Confirm the FIRST rendered content already shows "Data as-of 2020-03-20"
6. In the left sidebar, click "Dashboard" (the only nav item)
7. Confirm the URL no longer carries `?asof=` and the page shows the current latest as-of date

**Expected Result:**
- Steps 2-3: the exact stored `2020-03-20` manifest is served — its payload's `as_of` field equals
  `2020-03-20`, never a newer manifest's contents
- Step 5: no visible flash/repaint from "Latest" data to the historical view — the first paint on a
  cold/fresh load is already `2020-03-20`-scoped
- Step 7: returning to "Dashboard" (no `asof` param) shows the current/latest session state; the
  sidebar's own links no longer carry `?asof=2020-03-20`

---

## Excluded: J-10, J-11 — no browser case written

Both journeys' own `docs/goal.md` entries state their Walkthrough is explicitly waived:

- **J-10:** *"Walkthrough: waived — raw-layer incident repair with no UI surface change of its
  own."*
- **J-11** (this iteration's own Target journey): *"Walkthrough: waived — maintenance repair of the
  derived layer with no UI surface of its own."*

This matches the exact precedent already established in this project for these same two journeys:
`reports/phase-goal-market-compass-iter-7-ui-test-plan.md` excluded J-10 on this ground, and
`reports/phase-goal-market-compass-iter-11-ui-test-plan.md` excluded J-11 on this ground.
Inventing a click path for a journey `docs/goal.md` itself declares has none would mean testing
something that cannot exist — the eleven Stage-C-readiness checklist items this iteration proves
for J-11 (DDL-derived migration correctness, fail-closed `basis_disclosure`, zero-write
fingerprint, `preFreezeEra` honesty) are code/DB/fixture-level facts, already covered by the
fixture tests and live-DB evidence cited in `docs/handoffs/goal-market-compass-iter-12-dev.md`, not
by anything a browser can observe. No `UT-J-10` or `UT-J-11` row appears above.

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-J-01 | Sector attribution stays honest and near-complete | regression | P1 | `/stocks`, `/stocks/[ticker]`, `/methodology` |
| UT-J-04 | Next-session focus explains why/why-not/what-would-change | regression | P1 | `/` |
| UT-J-05 | Frozen manifest still serves full provenance stamps | regression | P1 | `/` |
| UT-J-06 | Basis disclosure honest across all four states post A4-bis fix | regression | P1 | `/`, `/?asof=` |
| UT-J-08 | Retrospective `?asof=` serves the exact historical manifest (scoped — no `/market`) | regression | P1 | `/`, `/?asof=` |

**Zero NEW-surface test cases** — this iteration is backend-only (`Frontend Present: no`), zero
frontend files were modified, and there is no UI-surface-map row to derive a `UT-01`-style case
from.

**Zero `UT-J-10` / `UT-J-11` cases** — both journeys' own `docs/goal.md` entries explicitly waive
their Walkthrough ("no UI surface of its own"); see the exclusion note above.

**All 5 test cases are P1.** J-05/J-06/J-08 are named on the phase spec's `Required-still-passing
journeys:` line as the journeys whose Data-Contract value this iteration's read-path fix directly
touches. J-01/J-04 are also named on that line (as "stay passing… untouched by this iteration") —
that framing is a claim about this iteration's own scope, not a signal that they need no regression
coverage, so both still get a real case per the binding "named journey gets a case" rule; UT-J-01
and UT-J-04 are additionally marked **observational-only** since no fresh live evidence for
`/stocks` or the focus section exists this iteration and no further live fetch/backfill is
authorized this session (AG-9 exhausted).

**Before executing:** re-read the two findings above. Neither is a defect in this iteration's
work — both are honest, evidence-grounded observations about what the current live dataset can and
cannot show through the UI today, so that whoever runs this plan does not mistake an expected,
currently-unreachable state (the new `"unverifiable"` badge; the `/market` route) for a failure.
