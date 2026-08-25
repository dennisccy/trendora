# Phase goal-market-compass-iter-15 — UI Test Plan

**Phase:** goal-market-compass-iter-15
**Date:** 2026-08-25
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255

---

## Status

This iteration is **backend-only** (`Frontend Present: no`). It performed a J-11 Stage D
readiness diagnostic: one bounded, authorized, read-only AVB provider fetch plus fixes to the
diagnostic/classifier/readiness-producer code. Zero frontend files changed, zero application-service
boot, zero browser-QA run, zero live database writes. Headline outcome: **`J-11 STAGE D READY: NO`**,
classification **AVB-C**; **`J-11 STAGE D AUTHORIZED: NO`** unconditionally. `reports/phase-goal-market-compass-iter-15-ui-surface-map.md`
records no surface as opened or changed this iteration, so **Step 1 (new-surface smoke/happy-path/
validation/error/UX test-case generation) is suppressed — there is no UI surface map row to derive one
from.**

Per the ui-test-designer's Backend-only phase handling, that suppression does **not** extend to
regression coverage for this phase's own journey metadata. The phase spec's `Target journeys:` line
names **J-11**, and its `Required-still-passing journeys:` line names **J-01 through J-10** (carried
"for evaluator awareness only" as unchanged: J-01/J-04/J-10 `passing`; J-02/J-03/J-05/J-06/J-09
`partial`; J-07/J-08 `failing`). Every one of those 11 journey IDs gets exactly one regression test
case below (`UT-J-01` .. `UT-J-11`), translated from that journey's own "Steps:"/"Acceptance:" text in
`docs/goal.md`'s "Must-have user journeys" section — never a generic "re-check journey X" placeholder.

**None of the steps below have been executed this iteration.** No browser-QA lane ran (maintenance
isolation is active). This plan is written for a future operator, or the Stage G run once J-11 is
authorized and reaches that stage, to execute once the backend and frontend are booted and maintenance
isolation has lifted. Do not treat any step below as already passed.

---

## Global preconditions & safety notes (apply to multiple test cases below)

- **Backend + frontend running** via the project's prod scripts, frontend reachable at
  `http://localhost:3255`.
- **Current known state (as of this writing, iteration 15, 2026-08-25 — re-derive, do not assume
  stale):** `scanner_runs` = 3,117 rows across 3,117 distinct as-of dates, none of them an incident
  date; `daily_prices` = 3,310,374 rows; 24 manifests, unchanged. The newest surviving stored run —
  i.e. the app's "Latest" as-of — sits at **2026-07-23**, about a month behind real calendar time. This
  is the authorized mid-repair state (J-10 raw-layer recovery complete; J-11 derived-state
  regeneration not yet authorized) — **it is not a bug, and no test case below treats it as one.**
  Treat "2026-07-23" as the value observed when this plan was written, not a fixed forever-expectation:
  once new normal sessions land, Latest will advance past it.
- **The 11 incident dates** (do not use ANY of these as a manually-chosen `?asof=` value in any test
  below unless the test explicitly says otherwise): `2026-05-12, 2026-05-13, 2026-07-10, 2026-07-13,
  2026-07-24, 2026-07-27, 2026-08-03, 2026-08-05, 2026-08-10, 2026-08-11, 2026-08-12`. Per J-11's own
  contract, 7 of these 11 dates currently have **no** stored manifest at all — requesting
  `GET /api/compass?as_of=<date>` (which the frontend's `?asof=` param drives) on one of those 7 would
  **mint a brand-new historical manifest**, an artifact this journey's contract forbids outside its own
  Stage G verification. The other 4 (2026-08-05, 2026-08-10, 2026-08-11, 2026-08-12) already carry a
  manifest that is known stale/orphaned pending J-11 regeneration. **Do not navigate to any of these 11
  dates as a general-purpose regression check** — UT-J-11 below is the one test case that deliberately
  checks the app's behavior AROUND this boundary without crossing it.
- **AVB's stored 2026-08-11/2026-08-12 dollar-volume convention** is a known, documented, unrepaired
  data condition this iteration diagnosed (classification AVB-C) but was explicitly forbidden to fix.
  No test case below asserts AVB's volume figures are correct, and none proposes repairing them.

---

## Test Cases

<!-- Test IDs use UT-J-<journey-id> per the Backend-only phase handling rule: every journey named on
     the phase spec's Required-still-passing / Target journeys lines gets exactly one regression row,
     Type regression, Priority P1. There are no sequential UT-01.. NEW-surface cases this iteration. -->

---

### UT-J-01 — Sector attribution stays honest and near-complete (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks`, `/methodology`, stock detail page

**Preconditions:**
- Backend + frontend running; at least one completed scan run already has `ScannerResult.sector`
  populated (true today — this regression check re-verifies already-landed behavior and does **not**
  require a fresh Remove/backfill drill).

**Steps:**
1. Navigate to `http://localhost:3255/stocks` with no `?asof` parameter (Latest as-of).
2. Find the Sector filter control and select its `"Unassigned"` option.
3. Note the number of rows shown and the total resolved-member count (visible elsewhere on the same
   page, e.g. an unfiltered count).
4. Clear the Sector filter. Click through to any single ticker's stock detail page.
5. Note the Sector value shown in that page's header.
6. Navigate to `http://localhost:3255/methodology`.

**Expected Result:**
- Step 3: Unassigned rows ÷ total resolved members is **≤ 5%** (this was ~78% before the journey that
  built this feature; a regression back toward that range is a fail).
- Step 5: the Sector value on the stock detail header equals the Sector cell shown for that same
  ticker on the `/stocks` leaderboard — one stored value, never two different labels for the same
  symbol.
- Step 6: the universe/data section on `/methodology` discloses the two-source sector basis (curated
  config mapping first, pool-snapshot fallback second) and states its current-only limitation (no
  point-in-time sector history).
- No symbol anywhere shows a fabricated (non-null, non-"Unassigned") sector label when neither source
  maps it — an unmapped symbol must read `null`/"Unassigned", never a guess.

---

### UT-J-02 — "What changed" deltas stay honest with correct empties (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Backend + frontend running; at least two stored sessions exist (true today — 3,117 stored runs).

**Steps:**
1. Navigate to `http://localhost:3255/` (Latest as-of).
2. Read the "What changed" card's header.
3. Read every entry listed in the card and note the order of their kinds.
4. Click the suppressed-moves disclosure control.
5. Use the as-of switcher to select the **earliest** stored run (not one of the 11 incident dates —
   the earliest stored run predates all of them).

**Expected Result:**
- Step 2: the header names a specific prior session date plus the gap in days; that named date is the
  stored run immediately preceding the current Latest as-of (no run exists between them).
- Step 3: entries are ordered market → breadth → sectors → themes → stocks; clicking any entry
  navigates to its drill surface carrying the current `?asof` value.
- Step 4: a suppressed-count number is shown, and it equals the number of entries listed under that
  disclosure.
- Step 5: an explicit "no prior run to compare" sentence renders — no delta figures, no direction
  words, nothing fabricated for the earliest run.

---

### UT-J-03 — Plain-English summary stays deterministic and cited (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Backend + frontend running.

**Steps:**
1. Navigate to `http://localhost:3255/` (Latest as-of).
2. Read the summary card in full.
3. Open the `"Show cited facts"` disclosure.
4. Re-read the full summary card text end to end, checking for banned language.
5. Use the as-of switcher to select the earliest stored run.
6. Use the as-of switcher to select any pre-frontier historical run date that is **not** one of the 11
   incident dates listed in "Global preconditions" above.

**Expected Result:**
- Step 2: the card shows a state sentence plus direction, breadth, and focus-count sentences.
- Step 3: every sentence lists a template id and its cited facts.
- Step 4: no sentence contains an imperative trade verb (e.g. "buy", "sell"), a forecast term (e.g.
  "will rise"), or a causal-attribution phrase (e.g. "because of", "due to").
- Step 5: the no-comparison sentence variant renders instead of a change sentence.
- Step 6: the summary card carries a visible "retrospective" stamp stating it was reconstructed under
  the current rule/config — never silently rendered as if it were a live/current-rule session.

---

### UT-J-04 — Candidate why/why-not explanations stay complete (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Backend + frontend running.

**Steps:**
1. Navigate to `http://localhost:3255/` (Latest as-of).
2. Count the cards in the "Next-session focus" section and compare against the number named in the
   summary card's focus sentence.
3. Open one candidate card.
4. Read its Leadership/Entry/Risk word labels, buckets, scores, reasons, and cautions.
5. Read its eligibility checklist.
6. Read its "what would change this" panel.
7. Scroll to the `"Not priority"` section and read a few entries.
8. Note the current market-state band's regime word (visible at the top of `/`).

**Expected Result:**
- Step 2: the two counts match exactly.
- Step 4: each reason and caution line cites both a threshold AND a stored actual value — never a bare
  claim with no number behind it.
- Step 5: every checklist row carries exactly one verdict from the fixed set {Pass, Miss, Supportive,
  Neutral, Unknown, NA} plus a threshold and an actual value.
- Step 6: the panel lists each selection/qualifier rule with threshold, current value, and met/unmet.
- Step 7: each `"Not priority"` entry names its failed condition(s) with distances; nowhere on the page
  (not as a card, not as a pick, not in any ordering) does a near-threshold "shadow cohort" name
  appear — it may only exist inside a separate manifest audit view under an explicit research-only
  label.
- Step 8: if the band reads Risk-off, every focus candidate carries a `REGIME_RISK_OFF` caution and the
  list is framed as "worth monitoring next session" with zero entry-advice wording. If the band is not
  Risk-off on the day this is run, record this sub-check as **not exercised today** rather than failed
  — it is conditional on market state, not always reachable.

---

### UT-J-05 — Ingest still freezes one provenance-stamped manifest (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/data`, `/`

**Preconditions:**
- Backend + frontend running. This drill is **seed-safe**: the "Remove" panel on `/data` removes
  derived scan snapshots only (cascading `ScannerRun` + children); it does not touch or require
  fetching raw `daily_prices` bars, so no network call is made and no live-data policy is implicated.

**Steps:**
1. Navigate to `http://localhost:3255/data`.
2. Using the seed-safe Remove panel, remove the two most-recently-covered trading days of snapshots
   (i.e. the two days immediately before the current frontier — **do not** advance the frontier past
   its current value; confirm the frontier date shown before and after this step is unchanged).
3. Run a backfill over that exact same removed range.
4. Read the backfill job's finalize step / the run record's "Refreshed:" line.
5. Navigate to `http://localhost:3255/` at the resulting frontier date and open the manifest strip.
6. Re-run the identical backfill range a second time (same dates, nothing new to do).

**Expected Result:**
- Step 4: the finalize step discloses a "next-session manifest" phase, and the "Refreshed:" line names
  it.
- Step 5: the manifest strip shows `mode: at_ingest`, `version: 1`, a frozen indicator, a
  `prospective_eligible: true` indicator, a generation timestamp, and candidate/comparison/shadow
  cohort counts where the comparison-cohort count equals (member count − candidate count).
- Step 6: no new manifest version is created — the strip still reads version 1 (create-once; a
  zero-work re-run must never mint a duplicate).

---

### UT-J-06 — Frozen manifest survives later data, rebuilds, and regeneration (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/data`, `/`

**Preconditions:**
- A frozen manifest already exists for some as-of `M` that is **not** one of the 11 incident dates —
  either freshly created via UT-J-05, or any pre-existing frozen manifest from normal prior operation.

**Steps:**
1. On `http://localhost:3255/data`, run a backfill over a **different** removed date (not `M`).
2. Navigate to `http://localhost:3255/?asof=M` and read the manifest strip.
3. On `/data`, remove snapshots over a range that includes `M`.
4. Return to `http://localhost:3255/?asof=M` and read the manifest strip again.
5. Backfill the removed range back.
6. Return to `/?asof=M` once more.
7. If a "Regenerate" action is available for `M`, trigger it (it should be confirm-gated — confirm the
   action).

**Expected Result:**
- Step 2: the manifest strip for `M` is unchanged from before step 1 (same version, same stamps,
  same bytes) — a backfill on an unrelated date must not touch it.
- Step 4: the strip still serves the same manifest verbatim, but now shows a "basis unavailable"
  read-time disclosure — never a 404, never a blank page, never a silent recompute.
- Step 6: the basis disclosure flips to "available" (or "rebuilt" if the underlying run's creation
  timestamp changed), while the manifest's stamps and version remain the unchanged original.
- Step 7: a version-2 manifest appears with its own generation timestamp and `prospective_eligible:
  false` (even if its mode would otherwise compute `at_ingest` — only the original version-1 minted by
  the ingest-finalize producer can ever be `true`); version 1 remains readable and byte-identical with
  its own flag unchanged; the UI lists both versions with their stamps.

---

### UT-J-07 — Today page still answers the ten-second read from served values (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Backend + frontend running; `reports/perf-budgets.md` exists with current committed latency figures.

**Steps:**
1. Navigate to `http://localhost:3255/` and time the load (navigation start to fully interactive).
2. Read the page body top to bottom.
3. Note the regime tile's label/score and the phase tile's phase/severity/P(bear).
4. Scan every element in the page chrome (above the body) and every element inside the market-state /
   regime / phase tiles for readiness vocabulary.
5. Confirm no regime × phase cross-view chart is rendered directly on this page; locate its named
   link-out and click it.

**Expected Result:**
- Step 1: page load and each on-load API call complete within the budgets currently recorded in
  `reports/perf-budgets.md` — compare against that file's live committed figures, not a hardcoded
  number.
- Step 2: the body renders, in this exact order: market-state band, plain-English summary, What
  changed, Leadership rotation, Next-session focus, manifest strip.
- Step 3: values equal `GET /api/dashboard` (regime) and `GET /api/market-phase` (phase) for the same
  as-of.
- Step 4: readiness/preflight tokens ("Ready", "GO", "DEGRADED", "NO-GO") appear only in the chrome,
  never inside the regime/phase tiles; regime/phase tokens appear nowhere in the chrome.
- Step 5: the link-out navigates to `http://localhost:3255/market`, where the cross-view chart does
  render.

---

### UT-J-08 — Market surface stays relocated intact; historical view never lies (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/market`, `/`

**Preconditions:**
- Backend + frontend running; at least one stored run exists that predates the 11 incident dates (true
  today — 3,117 stored runs, earliest well before 2026-05-12).

**Steps:**
1. Navigate to `http://localhost:3255/market`.
2. Look at the left sidebar's ordering and active-link highlighting.
3. Choose a stored historical run date `D` that is **not** one of the 11 incident dates (see "Global
   preconditions" above for the excluded list) — pick any early stored session. Navigate to
   `http://localhost:3255/?asof=D`.
4. Open `http://localhost:3255/?asof=D` directly in a fresh browser tab (not by clicking through from
   another page).
5. From that tab, click through to return to Latest (or clear the `?asof` param).

**Expected Result:**
- Step 1: two glance cards, a regime × phase cross-view card (its hide toggle persists across a
  reload), three breadth cards, Top Sectors, Candidate Counts, Top Themes, and the full Market Phase &
  Severity card are all present — nothing from the pre-relocation inventory is missing.
- Step 2: "Today" (→ `/`) is listed first, "Market" (→ `/market`) second; the active page's own link is
  highlighted.
- Step 3: the Today tiles show `D`'s stored values, the What-changed header names `D`'s predecessor
  run, and the manifest strip shows a manifest whose as-of equals `D` carrying a visible
  "retrospective" label.
- Step 4: the first rendered data is already `D`-scoped — no flash of Latest content before repainting
  to `D`; sidebar links in that tab carry `?asof=D`.
- Step 5: the URL no longer carries `?asof`, and the page shows the current Latest session's state.

---

### UT-J-09 — Backend memory change still serves byte-identical values (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/` (indirect — this journey's own Acceptance text states "Walkthrough: waived —
deliberately backend-only (no UI surface changes)"; there is no dedicated UI of its own to click)

**Preconditions:**
- Backend + frontend running.

**Steps:**
1. Navigate to `http://localhost:3255/` at the current Latest as-of.
2. Record the exact regime label + score, phase + severity + P(bear), and the three direction words
   (regime, stress, breadth) shown.
3. Compare those recorded values against `GET /api/dashboard` and `GET /api/market-phase` for the same
   as-of (this is the same equality check UT-J-07 performs — it is the only UI-observable trace of
   J-09's own guarantee).
4. Observe whether the page responds promptly or shows any sign of memory pressure (very slow first
   response, backend crash, 5xx error).

**Expected Result:**
- Step 3: all values match exactly — J-09's own change (shrinking `database.pragmas.cache_size`) is
  documented as performance-only; any mismatch here indicates some OTHER change moved a served value,
  which is itself a finding worth escalating.
- Step 4: no memory-pressure symptom; the page loads normally.

---

### UT-J-10 — Raw price recovery still doesn't destabilize normal serving (regression)

**Type:** regression
**Priority:** P1
**Surface:** none of its own (this journey's own Acceptance text states "Walkthrough: waived —
raw-layer incident repair with no UI surface change of its own... Final repaired-state `GET
/api/compass` serving and the J-01/J-02/J-03 replay belong exclusively to J-11 Stage G" — not yet
reached; this iteration's own conclusion was `J-11 STAGE D READY: NO`). Indirectly: `/stocks`, stock
detail pages, `/data` — surfaces that read the `daily_prices` table J-10 wrote into.

**Preconditions:**
- Backend + frontend running.

**Steps:**
1. Navigate to `http://localhost:3255/stocks` at the current Latest as-of.
2. Locate one of the symbols J-10's own verification record names as recovered/spot-checked (e.g.
   NVDA, AAPL, GRMN, AVB) and open its stock detail page.
3. Do **not** attempt to view any of the 11 incident dates for this symbol or any other (see "Global
   preconditions" above and UT-J-11 below) — J-10's raw recovery is not evidence that the
   derived/scored view for those dates is safe to render; that determination belongs to J-11 Stage G.

**Expected Result:**
- Step 1: `/stocks` loads normally, with no missing-price gaps, error banners, or blank rows for
  previously-affected symbols.
- Step 2: the stock detail page loads without error and shows a continuous price history up to the
  Latest as-of with no unexplained gap — J-10's bulk write into `daily_prices` (585 symbols, raw layer
  only) has not destabilized normal, non-incident-date serving.

---

### UT-J-11 — Incident-bounded derived state stays correctly un-regenerated; no premature exposure (regression)

**Type:** regression
**Priority:** P1
**Surface:** none of its own (this journey's own Acceptance text states "Walkthrough: waived —
maintenance repair of the derived layer with no UI surface of its own"). This check verifies the
**absence** of premature exposure rather than a feature working.

**Preconditions:**
- Backend + frontend running.
- **Hard safety note, read before running:** J-11's own Acceptance section names a trap —
  `compass.get_or_create_manifest` mints a brand-new historical manifest for ANY non-frontier as-of
  with no pre-existing one, regardless of caller. 7 of the 11 incident dates currently have no
  manifest. Do **not** manually navigate this test (or any other) to `?asof=` one of those 7 dates —
  doing so would itself create the forbidden artifact this journey's contract exists to prevent. This
  test case's steps below are deliberately designed to avoid that navigation.

**Steps:**
1. Navigate to `http://localhost:3255/` with **no** `?asof` parameter (Latest).
2. Note the as-of date shown.
3. If an as-of switcher / stored-run picker is visible on the page, open it (without selecting
   anything from it).
4. Close the picker without navigating anywhere from it.

**Expected Result:**
- Step 2: the Latest as-of is **not** one of the 11 incident dates listed in "Global preconditions"
  above. At the time this plan was written (2026-08-25) it was 2026-07-23; expect a date at or after
  that as new normal sessions land — never one of the 11 listed dates. This is the authorized
  mid-repair state (this iteration's own conclusion: `J-11 STAGE D READY: NO` / `J-11 STAGE D
  AUTHORIZED: NO`, classification AVB-C) and must **not** be reported as a bug.
- Step 3: if the picker lists any of the 11 incident dates at all, each must carry an explicit
  unavailable/orphaned/stale disclosure, never present as a normal, freshly-available session.
- **Escalate, do not silently note as fixed:** if any of the 11 incident dates appears anywhere in the
  app as a normal (non-disclosed, non-degraded) session with fresh scored/derived output, that
  indicates Stage D executed without authorization — this iteration's dev handoff states that did not
  happen, so this would be a genuine, reportable regression, not expected state.

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-J-01 | Sector attribution stays honest & near-complete | regression | P1 | `/stocks`, `/methodology` |
| UT-J-02 | What-changed deltas stay honest with correct empties | regression | P1 | `/` |
| UT-J-03 | Plain-English summary stays deterministic & cited | regression | P1 | `/` |
| UT-J-04 | Candidate why/why-not explanations stay complete | regression | P1 | `/` |
| UT-J-05 | Ingest still freezes one provenance-stamped manifest | regression | P1 | `/data`, `/` |
| UT-J-06 | Frozen manifest survives later data/rebuilds/regeneration | regression | P1 | `/data`, `/` |
| UT-J-07 | Today page still answers the ten-second read | regression | P1 | `/` |
| UT-J-08 | Market surface stays relocated intact; history never lies | regression | P1 | `/market`, `/` |
| UT-J-09 | Backend memory change still serves byte-identical values | regression | P1 | `/` (indirect) |
| UT-J-10 | Raw price recovery doesn't destabilize normal serving | regression | P1 | `/stocks`, stock detail |
| UT-J-11 | Incident derived state stays un-regenerated; no premature exposure | regression | P1 | `/` (absence check) |

**All 11 test cases are P1** per the ui-test-designer's Backend-only phase handling rule (every journey
named on the phase spec's `Required-still-passing journeys:` or `Target journeys:` line gets exactly
one `UT-J-<id>` row at `Type: regression`, `Priority: P1`). No new-surface (smoke/happy-path/
validation/error/UX) cases exist this iteration — `Frontend Present: no` and the UI surface map has no
row to derive one from.

**None of these 11 cases have been executed.** They must all be runnable and pass once a future
iteration boots the app and executes this plan (or J-11 reaches Stage G) before this phase's regression
posture can be called verified.
