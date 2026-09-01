# Phase goal-market-compass-iter-37 — UI Test Plan

**Phase:** goal-market-compass-iter-37
**Date:** 2026-09-01
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255

---

## Scope note (backend-only phase)

`reports/phase-goal-market-compass-iter-37-ui-surface-map.md` and
`reports/phase-goal-market-compass-iter-37-user-visible-changes.md` both report **Frontend
Present: no** — this iteration touches only `apps/backend/tests/test_manifest_invariants.py`
(a TC-24 fixture correction + a new `-O` subprocess unit test) and
`apps/backend/app/engine/compass.py` (`_assert_disposition_predicate`'s two bare `assert`
statements converted to explicit `if not cond: raise AssertionError(msg)` — same condition,
same message, same exception type). Zero `.tsx` files changed. Per the backend-only handling
rule, NEW-surface test-case generation (Step 1's smoke/happy-path/validation/error/UX
derivation from a UI surface map row) is suppressed — there is no surface map row to derive one
from.

That suppression does **not** cover regression coverage. `docs/phases/goal-market-compass-iter-37.md`'s
Goal Mode Metadata block carries both:
- **Target journeys:** J-13
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10,
  J-11, J-12

Together these name all thirteen Must-have journeys — every one gets exactly one row below.
Every test case is `UT-<journey-id>`, `Type: regression`, `Priority: P1`, with Steps and Expected
Result translated directly from that journey's own "Steps:"/"Acceptance:" text in `docs/goal.md`'s
"Must-have user journeys" section — not a generic "re-check journey X" placeholder.

**Why J-13 (this iteration's target) is still `regression` and not a new happy-path case:** J-13's
product code (the rotation section, `session_delta.rotation`, the signed delta/direction-word
fields) was built entirely in iteration 36 and is binding "Do not redo" this iteration. This
iteration's actual purpose for J-13 is evidence-only: retake the acceptance screenshot as a real
passenger through the pipeline (iter-36's own capture was measured single-colour — a failed
capture) and execute `journey-scripts/J-13.json` for the first time (its mtime, Sep 1 13:35, postdates
the 13:30 replay it was meant to cover, so it has never actually run). UT-J-13 below is written with
extra precision for exactly this reason — it is the surface the browser-qa-agent must capture and
measure this round.

Three journeys (J-09, J-10, J-11) carry the literal `docs/goal.md` marker `**Walkthrough:**
waived` in their own Acceptance text — J-09 and J-10 are explicitly "no UI surface of its own," so
their test cases below are evidence/API-based rather than browser-click-based, exactly as their own
Acceptance sections specify. J-11 is walkthrough-waived for its own maintenance steps but its
Stage G acceptance criteria explicitly authorize a browser-observable final check (the J-01/J-02/
J-03-style replay stays clean at the incident dates) — UT-J-11 below uses that browser check.

This iteration ships zero product code, zero config value, and zero served-field changes
(`apps/frontend/`, `warmup.py`, `prices.py`, `compass.selection.*` values, `session_delta.rotation`
logic all untouched — binding "Do not redo"). Every case below is a regression re-verification of
already-shipped, already-passing behavior.

---

## Test Cases

---

### UT-J-01 — Sector attribution stays honest and near-complete (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks`, `/methodology`

**Preconditions:**
- Frontend running at http://localhost:3255; backend running against the current database — no
  data mutation this iteration.
- At least one scanner run exists at the latest as-of.

**Steps:**
1. Navigate to `http://localhost:3255/stocks` (latest as-of, no `?asof` parameter).
2. In the Sector filter control, select the "Unassigned" option.
3. Note the "Unassigned" row count and the total resolved-member count shown on the page.
4. Clear the Sector filter, locate one stock row whose Sector cell is populated (any ticker) and
   note its Sector cell text.
5. Click into that stock's detail page.
6. Navigate to `http://localhost:3255/methodology`.

**Expected Result:**
- Step 3: the "Unassigned" count is at most 5% of the total resolved-member count (never 78% or
  higher — the pre-fix baseline).
- Step 5: the stock detail page's header Sector label matches the leaderboard Sector cell text
  noted in step 4 exactly (single stored source, no UI-derived value).
- Step 6: the `/methodology` page's universe/data section discloses the two-source sector basis
  (curated config first, pool snapshot fallback) and states it is current-only (no point-in-time
  sector history).
- No stock anywhere on `/stocks` shows a fabricated sector label — an unmapped symbol reads
  "Unassigned," never invented text.

---

### UT-J-02 — "What changed" reports honest session-over-session deltas (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend running at http://localhost:3255; at least two stored runs exist.

**Steps:**
1. Navigate to `http://localhost:3255/` (latest as-of).
2. Read the "What changed" card's header line.
3. Read every entry listed under "What changed," top to bottom.
4. Click the suppressed-moves disclosure (labeled e.g. "Show N suppressed moves").
5. Click any listed change entry's link-out.
6. Use the as-of switcher/date control to step to the earliest stored run in the list.

**Expected Result:**
- Step 2: the header names a specific prior session date (never blank) plus the gap in days to
  the current as-of, and that date is the run immediately preceding the current as-of.
- Step 3: entries are grouped in the order Market → Breadth → Sectors → Themes → Stocks.
- Step 4: the disclosure expands and the number of listed suppressed entries matches the count
  named on the toggle.
- Step 5: the browser navigates to the entry's drill surface carrying the current `?asof` value
  in the URL.
- Step 6: the card renders an explicit no-prior-run sentence (no deltas, no direction words) —
  never an empty card and never a fabricated comparison.

---

### UT-J-03 — Plain-English summary is deterministic and cited (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend running at http://localhost:3255.

**Steps:**
1. Navigate to `http://localhost:3255/` (latest as-of).
2. Read the plain-English summary card.
3. Click "Show cited facts" (the summary card's disclosure toggle).
4. Read every sentence's listed template id and cited facts.
5. Use the as-of switcher to select a pre-feature historical (retrospective) date.

**Expected Result:**
- Step 2: the summary card shows a state sentence plus direction, breadth, and focus-count
  sentences, all as served text.
- Step 4: every sentence lists a template id and its cited facts; no sentence contains an
  imperative trade verb, a forecast term, or a causal-attribution phrase.
- Step 5: the summary carries a visible retrospective stamp stating it was reconstructed under
  the current rule/config for that historical date.

---

### UT-J-04 — Candidate cards explain why, why-not, and what would change it (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend running at http://localhost:3255; at least one Next-session focus candidate exists at
  the latest as-of (10 candidates exist at the current frontier as-of `2026-08-12` per the dev
  handoff's live `GET /api/compass` round-trip — falls back to the honest-empty state otherwise,
  see Expected Result).

**Steps:**
1. Navigate to `http://localhost:3255/` (latest as-of).
2. Read the Next-session focus section's candidate count.
3. Click into one candidate card.
4. Read the card's Leadership/Entry/Risk labels, its reasons/cautions, its eligibility checklist,
   and its "what would change this" panel.
5. Scroll to the "Not priority" entries below the candidate cards.

**Expected Result:**
- Step 2: the candidate count equals both the count served by `GET /api/compass` and the count
  named in the summary's focus sentence (cross-check via browser devtools network tab or the
  summary card text).
- Step 4: each reason/caution cites a threshold and a stored actual value; the eligibility
  checklist rows each carry a verdict from {Pass, Miss, Supportive, Neutral, Unknown, NA}; the
  "what would change this" panel states each unmet rule's threshold and current value. A
  candidate whose Entry or Risk qualifier is unmet (but whose Leadership clears the floor) shows
  that qualifier as a **caution**, never as a reason it was excluded — only the leadership floor
  gates inclusion (J-12's corrected rule).
- Step 5: each "Not priority" entry names its failed condition(s) with distances — never a blank
  or generic explanation. If zero candidates exist, the section renders the explicit
  `candidates_empty_reason` state, never a bare empty list.

---

### UT-J-05 — Each close freezes one provenance-stamped manifest (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/` (manifest strip)

**Preconditions:**
- Frontend running at http://localhost:3255; the latest as-of already carries a frozen
  next-session manifest (this iteration mints no new manifest — binding scope; AG-12 byte-identity
  confirmed in the dev handoff).

**Steps:**
1. Navigate to `http://localhost:3255/` (latest as-of).
2. Scroll to the manifest strip at the bottom of the page.
3. Read the strip's mode, version, frozen state, and generation timestamp badges.
4. Click the "Audit table — comparison cohort (N) + near-threshold shadow (M)" disclosure to
   expand the detail table.

**Expected Result:**
- Step 3: the strip shows a well-formed mode (`at_ingest` or `retrospective`), a version number,
  a frozen indicator, and a generation timestamp — none blank or placeholder text.
- Step 4: the expanded table lists the stored candidates and a comparison-cohort row count
  consistent with (member count minus candidate count).

---

### UT-J-06 — A frozen manifest never changes (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend running at http://localhost:3255; a stored historical as-of with an existing frozen
  manifest is available (e.g. the same date used in UT-J-05).

**Steps:**
1. Navigate to `http://localhost:3255/` and use the as-of switcher to select the historical date
   with the existing frozen manifest.
2. Read the manifest strip's version number and stamps.
3. Reload the page (F5).
4. Read the manifest strip's version number and stamps again.

**Expected Result:**
- Step 4: the version number and every stamp (mode, generation timestamp, frozen flag) are
  byte-identical to step 2 — reloading the page never mints a new version and never mutates the
  displayed manifest.

---

### UT-J-07 — The Today page answers the ten-second read (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend running at http://localhost:3255.

**Steps:**
1. Navigate to `http://localhost:3255/` (latest as-of).
2. Read the page top to bottom.
3. Read the regime tile's label/score and the market-phase tile's phase/severity/P(bear) values.
4. Expand each tile's breakdown disclosure.
5. Look for a regime × phase cross-view chart anywhere on this page.
6. Click the named link-out for the cross-view chart (or navigate to
   `http://localhost:3255/market` if no explicit link is present).

**Expected Result:**
- Step 2: the body renders, in order: market-state band, plain-English summary, What changed,
  Leadership rotation, Next-session focus, manifest strip — with the readiness badge and
  preflight strip in the layout chrome above the body, not mixed into the body sections.
- Step 3: neither tile shows a blank or placeholder value.
- Step 4: each disclosure's component names and contributions are non-blank.
- Step 5: the regime × phase cross-view chart is absent from `/`.
- Step 6: the browser lands on `/market`, where the cross-view chart renders.
- Readiness/preflight tokens ("Ready," "GO," "DEGRADED," "NO-GO") appear only in the chrome, never
  inside the market-state/summary body sections, and vice versa for regime/phase tokens.

---

### UT-J-08 — The market surface relocates intact and history never lies (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/market`

**Preconditions:**
- Frontend running at http://localhost:3255.

**Steps:**
1. Navigate to `http://localhost:3255/market`.
2. Read the page contents.
3. Look at the left sidebar's navigation order.
4. Use the as-of switcher on `/market` (or navigate directly with a `?asof=` query parameter) to
   select any stored historical date well before the latest as-of.
5. Open `http://localhost:3255/?asof=<the same historical date used in step 4>` in a fresh browser
   tab.
6. Return to Latest (clear the `?asof` parameter, e.g. by clicking "Today"/"Latest" in the
   navigation).

**Expected Result:**
- Step 2: the two glance cards, the regime × phase cross-view card (with its hide toggle
  functional), three breadth cards, Top Sectors, Candidate Counts, Top Themes, and the full
  Market Phase & Severity card all render — no card missing.
- Step 3: "Today" is listed before "Market" in the sidebar, and whichever page is active is
  visually highlighted correctly.
- Step 4: the Today tiles show the selected historical date's stored values, the What-changed
  card compares that date against its predecessor (header names that predecessor date), and the
  manifest strip shows a manifest whose as-of equals the selected date carrying a visible
  "retrospective" label.
- Step 5: the freshly opened tab shows the historical date's data immediately — no
  latest-then-historical repaint — and sidebar links carry `?asof=<date>`.
- Step 6: the `?asof` parameter is gone from the URL and the strip shows the latest session's
  state.

---

### UT-J-09 — The backend fits the host (regression — evidence-based, walkthrough waived)

**Type:** regression
**Priority:** P1
**Surface:** Backend process + `reports/perf-budgets.md` (no UI route — `docs/goal.md`'s J-09
Acceptance carries the literal marker `**Walkthrough:** waived — deliberately backend-only (no UI
surface changes)`)

**Preconditions:**
- Backend started via `bash scripts/start-backend.sh`.
- This iteration touches neither `config.yaml` nor any memory-affecting code path — only
  `test_manifest_invariants.py` and `compass.py`'s `_assert_disposition_predicate` guard
  statements changed (binding scope). This is a pure regression re-check that iter-33/34's fix
  still holds, not a new measurement round.

**Steps:**
1. With the backend running, identify its process id (e.g. `pgrep -f uvicorn` or the PID file the
   launch script writes) and read `VmPeak` from `/proc/<pid>/status`.
2. Open `reports/perf-budgets.md` and locate the newest addendum.
3. Run `git diff --stat reports/perf-budgets.md` (or `git log -1 --format=%H -- reports/perf-budgets.md`
   against this iteration's commit range) to confirm the file was not touched this iteration.

**Expected Result:**
- Step 1: live `VmPeak_kB` read from `/proc/<pid>/status` is ≤ 2,621,440 kB (2.5 GB).
- Step 2: the newest addendum is still Addendum 45 (2026-09-01, market-compass iter-34, "J-09
  closing re-measurement"), recording ≤ 2,621,440 kB — no addendum has regressed or gone missing.
- Step 3: the file shows zero diff for this iteration — confirms this closing round did not
  silently touch or reopen J-09's already-closed memory work.

---

### UT-J-10 — Bounded recovery of the two incident trading days (regression — evidence-based, walkthrough waived)

**Type:** regression
**Priority:** P1
**Surface:** Backend DB + `/api/compass` (no UI route — `docs/goal.md`'s J-10 Acceptance carries
the literal marker `**Walkthrough:** waived — raw-layer incident repair with no UI surface change
of its own`)

**Preconditions:**
- Backend running against the current database. J-10 is CLOSED per the 2026-08-23 owner ruling
  (585 restored / 2 explicitly unrestorable: EA, EQR) — this iteration's two backend touches
  (test fixture, `compass.py` guard conversion) do not read or write `daily_prices`, so this is a
  pure regression re-check.

**Steps:**
1. Open a read-only (`mode=ro`) connection to `apps/backend/data/trendora.db` (or use an
   equivalent read-only query tool) and run
   `SELECT COUNT(*) FROM daily_prices WHERE date IN ('2026-08-11','2026-08-12')`.
2. Query `data_provider_runs` for rows tied to the 2026-08-11/2026-08-12 recovery.
3. Run `curl http://localhost:8000/api/compass?as_of=2026-08-12`.

**Expected Result:**
- Step 1: the row count reflects the accepted 585-restored terminal state (EA and EQR remain
  absent from `daily_prices` for those two dates — never silently backfilled under this
  iteration).
- Step 2: recovered rows are recorded with `provider='yahoo'` provenance, never relabelled as
  `stooq` or blended without attribution.
- Step 3: the endpoint returns a valid 200 response with a compass payload — never the pre-recovery
  400 that `GET /api/compass?as_of=2026-08-12` used to return. (This response is also the same one
  the iter-37 dev handoff cites, confirming `_assert_disposition_predicate` runs end-to-end with
  no error.)

---

### UT-J-11 — Incident-bounded derived state serves cleanly (regression — Stage G browser check)

**Type:** regression
**Priority:** P1
**Surface:** `/` via `?asof=2026-08-12` and `?asof=2026-08-05` (two of the 11 incident dates)

**Preconditions:**
- Frontend running at http://localhost:3255. J-11 is CLOSED per the 2026-08-27 owner ruling — the
  final serving/replay verification already passed. This is a regression re-check, not a rebuild.

**Steps:**
1. Navigate to `http://localhost:3255/?asof=2026-08-12`.
2. Read the Today tiles and the manifest strip on this page.
3. Read the What-changed card and the plain-English summary on this page.
4. Navigate to `http://localhost:3255/?asof=2026-08-05` (an incident date whose manifest was
   previously orphaned — 2 manifests, 0 surviving source runs before J-11).
5. Read the manifest strip's basis disclosure on this page.

**Expected Result:**
- Step 1: the page loads without a 400/500 error or blank screen.
- Step 2: the Today tiles show 2026-08-12's stored values (not a stale or repainted value from
  another date); the manifest strip shows a basis disclosure of "available" or "rebuilt" — never
  a silently stale claim.
- Step 3: the What-changed card compares 2026-08-12 against its correct predecessor run and the
  summary renders normally (no crash, no fabricated content) — the J-01/J-02/J-03-style checks
  replay clean at this incident date, matching J-11 Stage G's acceptance criterion.
- Step 5: the manifest strip shows the honest unknown/unverifiable basis state for this
  orphaned-manifest date — never a fabricated "available" claim (the A4/A4-bis fail-closed fix).

---

### UT-J-12 — Every frozen selection disposition is true (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/` (manifest strip audit table, Next-session focus candidate cards)

**Preconditions:**
- Frontend running at http://localhost:3255; backend running against the current database. J-12's
  `evaluate_selection` fix (leadership-only inclusion gate; entry/risk are advisory qualifiers
  that never gate membership) is already shipped and is binding "Do not redo" this iteration —
  this is a regression re-check, not a rebuild.

**Steps:**
1. Navigate to `http://localhost:3255/` (latest as-of, frontier `2026-08-12`).
2. Scroll to the manifest strip at the bottom of the page.
3. Click the "Audit table — comparison cohort (N) + near-threshold shadow (M)" disclosure to
   expand it.
4. In the "Comparison cohort (non-selected pool)" table, read the Leadership and Disposition
   columns for every visible row.
5. Click into one Next-session focus candidate card and read its eligibility checklist rows for
   Entry and Risk.

**Expected Result:**
- Step 4: every row whose Disposition column reads "below selection floor" has a Leadership value
  strictly below 80.0. Zero rows show a Leadership value at or above 80.0 labeled "below selection
  floor" — the pre-fix defect showed 37 of 539 such rows (highest HPE at 92.71); none should
  reproduce that pattern now.
- Step 4: any row with Leadership at or above 80.0 that is not itself a candidate instead shows
  Disposition "excluded by cap," never "below selection floor."
- Step 5: if the selected candidate's Entry or Risk checklist row shows "Miss" (unmet), that row
  is presented as a caution on the card, not as a reason the candidate was excluded — the
  candidate still appears in Next-session focus because only the leadership floor gates inclusion.

---

### UT-J-13 — Leadership rotation shows both directions with signed deltas (regression — this iteration's evidence target)

**Type:** regression
**Priority:** P1
**Surface:** `/` — "Leadership rotation" card, frontier as-of `2026-08-12`

**Preconditions:**
- Frontend running at http://localhost:3255; backend running against the current database. J-13's
  rotation section (`apps/frontend/components/compass-leadership-rotation-section.tsx`) is already
  shipped and is binding "Do not redo" this iteration. This iteration's sole purpose for J-13 is to
  retake the acceptance screenshot as a real passenger and run its golden script for the first
  time — iter-36's own capture (`UT-J-13-rotation-both-directions.png`) was measured single-colour
  (1683×1260, one distinct colour across 2.12M pixels), a failed capture.

**Steps:**
1. Navigate to `http://localhost:3255/` (no `?asof` — resolves to the latest/frontier as-of,
   `2026-08-12`).
2. Scroll down to the card titled "Leadership rotation," located directly below the "What
   changed" card and above "Next-session focus."
3. Within the "Sector rotation" subsection, read the "Gaining" side (left column) and the
   "Losing" side (right column) — each is a badge-labeled column in a two-column layout.
4. Read one row's text under whichever side is populated — the format is
   `<label>` then `<from> → <to> (<signed delta>) · <direction_word>` (e.g. "Regional Banks
   (SPDR)" showing "13 → 10 (-3) · improving").
5. Read a row under the opposite side (e.g. "Home Construction (iShares)" showing
   "21 → 25 (+4) · deteriorating").
6. Read the small accounting line directly below the Sector rotation rows — format "`N` of `M`
   shown · `S` below threshold · `R` beyond the display cap."
7. Repeat steps 3–6 for the "Theme rotation" subsection immediately below Sector rotation.
8. Scroll back up to the "What changed" card above and re-read its listed entries.

**Expected Result:**
- Step 2: the "Leadership rotation" card is visibly present, renders real text and colour (not a
  blank/white/single-colour card), and shows at least one populated row on at least one side of
  at least one of Sector/Theme.
- Step 3: both a "Gaining" badge and a "Losing" badge are visible side by side. A side with zero
  threshold-crossing movers instead shows the exact text "No sector gained ground beyond the
  threshold this session." or "No sector lost ground beyond the threshold this session." (or the
  theme-kind equivalents) — never a blank space.
- Step 4: the row shows a **signed** delta (a "-" for a rank that fell, i.e. improved) and a
  served direction word — e.g. "improving" — never an unsigned or missing delta.
- Step 5: the opposite-side row shows a "+" signed delta and a direction word such as
  "deteriorating" for a rank that rose (worsened) — confirming the section genuinely shows BOTH
  directions, not a repeat of one.
- Step 6: the accounting line's shown + suppressed + residual counts sum to the configured group
  total (31 for sector: 11 sector + 20 industry ETFs; 11 for theme) — no above-threshold mover is
  silently dropped.
- Step 8: the What-changed card's entries, ordering (Market → Breadth → Sectors → Themes →
  Stocks), and suppressed count are unchanged from UT-J-02's baseline — J-13's rotation section
  does not alter or duplicate What-changed's own content.
- **This is the surface the browser-qa-agent must capture and measure this iteration** as
  `reports/qa/goal-market-compass-iter-37-evidence/UT-J-13-rotation-both-directions.png` (or its
  iter-37-suffixed equivalent): `PIL.Image.getcolors()` must report more than one distinct colour
  (a single-colour result is an automatic FAIL, per the iter-36 lesson), file size must be
  comparable to healthy sibling captures in the same evidence directory, and the image must
  visibly show both a labelled "gaining" side and a labelled "losing" side with at least one row
  each — matching steps 4–5 above and `journey-scripts/J-13.json` steps 2–4 verbatim.

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-J-01 | Sector attribution stays honest and near-complete | regression | P1 | `/stocks`, `/methodology` |
| UT-J-02 | "What changed" reports honest deltas | regression | P1 | `/` |
| UT-J-03 | Plain-English summary is deterministic and cited | regression | P1 | `/` |
| UT-J-04 | Candidate cards explain why/why-not/what-would-change | regression | P1 | `/` |
| UT-J-05 | Each close freezes one provenance-stamped manifest | regression | P1 | `/` (manifest strip) |
| UT-J-06 | A frozen manifest never changes | regression | P1 | `/` |
| UT-J-07 | The Today page answers the ten-second read | regression | P1 | `/` |
| UT-J-08 | The market surface relocates intact | regression | P1 | `/market` |
| UT-J-09 | The backend fits the host (evidence-based, walkthrough waived) | regression | P1 | backend process, `reports/perf-budgets.md` |
| UT-J-10 | Bounded recovery of the incident days (evidence-based, walkthrough waived) | regression | P1 | backend DB, `/api/compass` |
| UT-J-11 | Incident-bounded derived state serves cleanly (Stage G) | regression | P1 | `/?asof=2026-08-12`, `/?asof=2026-08-05` |
| UT-J-12 | Every frozen selection disposition is true | regression | P1 | `/` (manifest strip audit table) |
| UT-J-13 | Leadership rotation shows both directions, signed deltas — **this iteration's evidence target** | regression | P1 | `/` (Leadership rotation card) |

**All thirteen cases are P1 — every Required-still-passing journey (J-01..J-12) plus this
iteration's own Target journey (J-13) must pass for the browser-QA/regression verdict to be PASS.
UT-J-13 carries the additional, iteration-specific requirement that its acceptance screenshot be
freshly captured and measured non-blank — a PASS row alone is not sufficient evidence per the
iter-36 lesson.**
