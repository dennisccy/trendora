# Phase goal-market-compass-iter-32 — UI Test Plan

**Phase:** goal-market-compass-iter-32
**Date:** 2026-09-01
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255
**Backend URL:** http://localhost:8255

---

## Scope note (backend-only iteration — read before using this plan)

`reports/phase-goal-market-compass-iter-32-ui-surface-map.md` confirms **zero** UI surfaces changed
this iteration (`Frontend Present: no`; `apps/frontend/**` and `apps/backend/app/**` are both
byte-unchanged). Per this agent's Backend-only phase handling rule, no NEW-surface smoke /
happy-path / validation / error / UX test cases are generated — there is no UI surface map row to
derive them from.

However, the phase spec's Goal Mode Metadata names journeys on **both** the `Target journeys:` line
(`J-09`) and the `Required-still-passing journeys:` line (`J-01, J-02, J-03, J-04, J-05, J-06, J-07,
J-08, J-10, J-11`) — eleven distinct journey IDs in total, none overlapping. Per the binding
ops-hardening iter-40/41 lesson (a journey promoted to a `Target journeys:` line with no
`Required-still-passing` counterpart previously shipped with **zero** verification, silently, across
five consecutive ESCALATE-graded iterations), every one of these eleven journeys gets its own
regression test case below — `UT-J-01` through `UT-J-11` — derived from that journey's own
Steps/Acceptance text in `docs/goal.md`'s "Must-have user journeys" section.

**Every step below is read-only** and uses only the three as-of values this iteration is authorized
to request against `/api/compass*` (`docs/phases/goal-market-compass-iter-32.md` OUT OF SCOPE):
no `?asof` param (frontier, 2026-08-12), `?asof=2025-04-15`, `?asof=1996-02-01`. No step performs a
`/data` Remove, a backfill, a manifest regenerate, or any other mutating action — several of these
journeys' own original "Steps" text (J-01 step 1, J-05 step 1, J-06 steps 1–4) call for exactly that
kind of mutation, which this iteration's spec explicitly forbids (no new manifest mint, no backfill).
Those steps are intentionally **not** reproduced; this plan instead re-verifies the *already-produced,
already-frozen* state each journey's Acceptance criteria describe, which is what "still passing" means
for a re-measurement iteration that touches no product code. J-09, J-10, and J-11 each explicitly
**waive their own UI Walkthrough** in `docs/goal.md` (J-09: "deliberately backend-only... demo
requirement... replaced by the dated VmPeak measurement"; J-10: "raw-layer incident repair with no UI
surface change of its own"; J-11: "maintenance repair of the derived layer with no UI surface of its
own") — their test cases below are correspondingly framed as non-destructive read/API checks rather
than a browser click-path, consistent with their own acceptance text.

---

## Test Cases

---

### UT-J-01 — Sector attribution stays honest and near-complete (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Frontend running at http://localhost:3255, backend running at http://localhost:8255
- No `/data` Remove or backfill is performed as part of this check (out of scope this iteration)

**Steps:**
1. Navigate to `http://localhost:3255/stocks` (no `?asof` — latest/frontier run)
2. In the filter row, open the "Sector" dropdown (`aria-label="Filter by sector"`) and note the
   total row count shown in the table before changing the filter
3. Select the "Unassigned" option from the Sector dropdown
4. Expect the resulting Unassigned row count divided by the total row count noted in step 2 to be
   at most 5%
5. Pick any one row still visible after the filter is reset to "All sectors" whose Sector column
   shows a real sector name (not "Unassigned"); click that row to open its stock detail page
6. On the stock detail page, expect the header's sector value to match the Sector cell shown for
   that ticker back on the `/stocks` leaderboard
7. Open `http://localhost:8255/api/stocks` in a new browser tab, use the browser's Find (Ctrl+F) to
   locate the same ticker's JSON entry, and expect its `"sector"` field to equal the sector value
   shown in the UI in steps 5–6

**Expected Result:**
- The Unassigned filter share is ≤ 5% of resolved members (this was ~78% before the J-01 fix landed)
- The leaderboard Sector cell, the stock detail header, and the raw `GET /api/stocks` JSON all show
  the identical stored sector label for the spot-checked ticker — no UI-side derivation
- No stock row shows a blank or literal `null` sector cell — every unmapped row reads "Unassigned"

---

### UT-J-02 — "What changed" still reports honest session-over-session deltas (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend running at http://localhost:3255, backend running at http://localhost:8255

**Steps:**
1. Navigate to `http://localhost:3255/` (no `?asof` — latest/frontier run, 2026-08-12)
2. Locate the "What changed" card and read its header line naming the prior stored session date
   and the day gap
3. Expect every visible change entry in the card to be ordered market → breadth → sectors → themes
   → stocks
4. Click the "Suppressed moves (N)" disclosure to expand it
5. Expect the number of listed suppressed entries inside the disclosure to equal the count N shown
   in its own header text

**Expected Result:**
- The "What changed" card renders with a header naming a specific prior date and a numeric day gap
  (never blank, never a raw error)
- Change entries appear in the fixed market → breadth → sectors → themes → stocks order
- The "Suppressed moves (N)" disclosure expands to show exactly N entries, each visibly below its
  kind's threshold — the header count and the listed-entry count match exactly

---

### UT-J-03 — Plain-English summary stays deterministic and cited (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend running at http://localhost:3255, backend running at http://localhost:8255

**Steps:**
1. Navigate to `http://localhost:3255/` (no `?asof` — latest/frontier run)
2. Locate the summary card and expect it to render a state sentence plus direction, breadth, and
   focus-count sentences as plain text (no blank card, no "undefined")
3. Click the "Show cited facts" disclosure to expand it
4. Expect every sentence listed inside to show its cited facts (not the fallback "— no cited
   facts." text)
5. Navigate to `http://localhost:3255/?asof=1996-02-01` (a pre-frontier historical date, part of
   this iteration's authorized as-of set)
6. Expect the summary card to carry a visible retrospective stamp naming that it was reconstructed
   under the current rule/config

**Expected Result:**
- The summary card's sentences render as served text with no fabricated or missing clause
- The "Show cited facts" disclosure lists a template id and facts for every sentence — never the
  "no cited facts" fallback for a normal run
- At `?asof=1996-02-01`, the summary card visibly identifies itself as a retrospective
  reconstruction — the retrospective stamp must be present, not silently absent

---

### UT-J-04 — Next-session candidates still show why, why-not, and what-would-change (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend running at http://localhost:3255, backend running at http://localhost:8255
- The latest run has at least one candidate in the "Next-session focus" section (already true from
  prior iterations)

**Steps:**
1. Navigate to `http://localhost:3255/` (no `?asof` — latest/frontier run)
2. Scroll to the "Next-session focus" card and open the first candidate card
3. Expect the card to show Leadership / Entry / Risk labels plus its reasons and cautions
4. Click the "Eligibility checklist" disclosure to expand it
5. Expect each checklist row to carry a verdict from the set Pass / Miss / Supportive / Neutral /
   Unknown / NA, each with a threshold and an actual value shown
6. Click the "What would change this" disclosure to expand it
7. Expect it to list each selection/qualifier rule with a threshold, current value, and a met/unmet
   verdict
8. Click the "Not priority (N)" disclosure to expand it
9. Expect it to list N excluded names, each naming its failed condition(s)

**Expected Result:**
- The candidate card shows Leadership/Entry/Risk plus reasons/cautions with no placeholder or
  missing field
- "Eligibility checklist" rows all carry one of the six fixed verdicts with threshold + actual value
- "What would change this" lists concrete rules with threshold/current/met-unmet — never a blank
  panel
- "Not priority (N)" lists exactly N names, each with a stated reason — no bare empty list, no
  fabricated reason

---

### UT-J-05 — Frozen next-session manifest still shows its provenance stamps (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend running at http://localhost:3255, backend running at http://localhost:8255
- This check does NOT perform a `/data` Remove+backfill (out of scope this iteration) — it
  re-reads the manifest already frozen by a prior iteration's ingest

**Steps:**
1. Navigate to `http://localhost:3255/` (no `?asof` — latest/frontier run, 2026-08-12)
2. Scroll to the "Manifest" card (manifest strip)
3. Expect it to show a mode badge (e.g. "at ingest"), a "version N" badge, and a "frozen" badge
4. Expect its expanded candidates table to list the stored candidates with Leadership/Entry/Risk
   columns populated

**Expected Result:**
- The "Manifest" card renders the frozen stamps for the frontier as-of: mode, version, and
  "frozen" (not "not frozen")
- The candidates table shows real Leadership/Entry/Risk values for each row — no blank cells, no
  loading spinner stuck indefinitely

---

### UT-J-06 — A frozen manifest still never changes (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/` (manifest strip) + `GET /api/compass`

**Preconditions:**
- Frontend running at http://localhost:3255, backend running at http://localhost:8255
- This check reuses the phase's own TC-5 byte-identity spot-check inputs — no new manifest is
  minted by this test

**Steps:**
1. Open `http://localhost:8255/api/compass` (no `as_of` param — frontier) in a browser tab and
   save/copy the full JSON response text
2. Open `http://localhost:3255/` and confirm the manifest strip's version badge (e.g. "version 1")
3. Reload `http://localhost:8255/api/compass` a second time and compare the JSON byte-for-byte
   against the copy from step 1
4. Repeat steps 1 and 3 for `http://localhost:8255/api/compass?as_of=2025-04-15`

**Expected Result:**
- Both re-fetches of `GET /api/compass` (frontier and `as_of=2025-04-15`) return byte-identical
  JSON to the first fetch — no field, hash, or stamp differs between requests
- The manifest strip's version badge shown in the browser matches the `version` field in the JSON

---

### UT-J-07 — The Today page still answers the ten-second read from served values only (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend running at http://localhost:3255, backend running at http://localhost:8255

**Steps:**
1. Navigate to `http://localhost:3255/` (no `?asof` — latest/frontier run)
2. Expect the page body to render, top to bottom: the "Market state" card, the summary card, "What
   changed", "Leadership rotation", "Next-session focus", and the "Manifest" card — with the
   readiness/preflight strip in the chrome above all of them
3. In the "Market state" card, expect a Regime tile (label + score) and a Phase tile (phase,
   severity, P(bear))
4. Expect the preflight banner/badge chrome (if present) to show only "Ready"/"GO"/"DEGRADED"/
   "NO-GO" tokens, and expect none of those four tokens to appear anywhere inside the "Market
   state" card itself
5. Confirm the regime × phase cross-view chart (a chart titled "Regime × phase cross-view" or
   similar) is NOT present anywhere on `/`
6. On the "Market state" card, click the link that navigates to the Market page

**Expected Result:**
- All six body sections render in the fixed order with no missing section and no crash
- The Regime and Phase tiles show real values (not blank/NA unless the underlying data is genuinely
  absent)
- Readiness vocabulary ("Ready"/"GO"/"DEGRADED"/"NO-GO") and market-state vocabulary never share a
  surface — no readiness token appears inside the Market state card
- The cross-view chart is absent from `/`; clicking the link navigates to `http://localhost:3255/market`

---

### UT-J-08 — The Market page still holds the full relocated surface, and history still isn't lied about (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/market`

**Preconditions:**
- Frontend running at http://localhost:3255, backend running at http://localhost:8255

**Steps:**
1. Navigate to `http://localhost:3255/market`
2. Expect the page to render the two glance cards, the "Regime × phase cross-view" card (or its
   "Show regime × phase cross-view" collapsed toggle), and the full former More-detail inventory:
   three breadth cards, "Top Sectors", "Candidate Counts", "Top Themes", and "Market Phase &
   Severity"
3. In the left sidebar, expect "Today" to be listed first and "Market" second, and expect "Market"
   to be highlighted as the active link while on `/market`
4. Navigate to `http://localhost:3255/?asof=2025-04-15` (a pre-frontier historical date from this
   iteration's authorized as-of set)
5. Expect the Today tiles to show 2025-04-15's stored values, the "What changed" header to name a
   prior date strictly before 2025-04-15, and the Manifest card to show a visible "retrospective"
   label
6. Click "Today" in the sidebar (or remove the `?asof` param) to return to the latest view
7. Expect the URL's `?asof` parameter to be gone and the Manifest card to show the latest session's
   frozen state again

**Expected Result:**
- `/market` still shows every card that was on the former dashboard — no card silently dropped
- Sidebar order is Today, then Market, with correct active-route highlighting
- At `?asof=2025-04-15`, all served values are that date's stored values and the Manifest card is
  visibly labeled "retrospective" — never the latest manifest's contents
- Returning to Latest clears `?asof` and restores the frontier state

---

### UT-J-09 — Backend memory footprint re-measurement leaves no displayed value moved (regression)

**Type:** regression
**Priority:** P1
**Surface:** N/A — backend-only; Walkthrough explicitly waived per J-09's own acceptance text in
`docs/goal.md` ("deliberately backend-only... demo requirement... replaced by the dated VmPeak
measurement")

**Preconditions:**
- Backend running at http://localhost:8255 with `database.pragmas.cache_size: -65536` (unchanged
  since iter-4; this iteration re-verifies, does not re-set it)

**Steps:**
1. Open `http://localhost:8255/api/compass` (frontier) and `http://localhost:8255/api/dashboard`
   (frontier) and save the JSON responses
2. Open `reports/perf-budgets.md` and locate the newest addendum (Addendum 43)
3. Expect the addendum to cite a raw sampler evidence file path under
   `runs/goal-market-compass-iter-32/` with UTC start/end capture timestamps, a measured VmPeak
   figure in kB, and its comparison to the ≤ 2,621,440 kB (2.5 GB) target
4. Re-fetch `http://localhost:8255/api/compass` and `http://localhost:8255/api/dashboard` and
   compare each byte-for-byte against the copies saved in step 1

**Expected Result:**
- Addendum 43 exists, is appended below Addendum 42 (Addenda 40/41/42 unedited), and states an
  honest measured VmPeak figure (never a fabricated or rounded-to-pass number) plus the
  concurrent-load and byte-identity results
- The re-fetched `GET /api/compass` and `GET /api/dashboard` responses are byte-identical to the
  first fetch — proving the `cache_size` re-verification moved zero displayed value

---

### UT-J-10 — The two recovered trading days stay intact, and nothing outside them moved (regression)

**Type:** regression
**Priority:** P1
**Surface:** N/A — backend-only, raw-layer only; Walkthrough explicitly waived per J-10's own
acceptance text in `docs/goal.md` ("raw-layer incident repair with no UI surface change of its own")

**Preconditions:**
- Backend running at http://localhost:8255
- This check performs no live fetch and no backfill (AG-9's exception for J-10 is exhausted; J-10
  is CLOSED per the owner ruling in `docs/goal.md`) — read-only verification only

**Steps:**
1. Open `http://localhost:8255/api/compass` (no `as_of` param — the frontier date is 2026-08-12,
   one of the two dates J-10 recovered) and confirm the request returns HTTP 200, not a 400
2. In the response JSON, note the `generation` block's dataset/frontier fields
3. Open `reports/perf-budgets.md`'s Addendum 43 (or the iter-32 dev handoff at
   `docs/handoffs/goal-market-compass-iter-32-dev.md`) and locate the re-derived manifest
   row-count census this iteration performs
4. Expect the census to report the same row count / distinct `as_of` count / max id as the prior
   iteration's census (28 rows / 18 distinct `as_of` / max id 28) — i.e., nothing new was minted

**Expected Result:**
- `GET /api/compass` for the frontier date (2026-08-12, one of J-10's two recovered dates) serves
  HTTP 200 with a well-formed manifest — not the 400 the iter-5 drill originally caused
- The manifest census in the dev handoff shows no drift from the prior iteration's count — the
  raw-layer recovery remains intact and nothing outside the authorized scope was touched this
  iteration

---

### UT-J-11 — The regenerated derived state for the incident dates still serves cleanly (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/` at the frontier as-of (2026-08-12) — the one incident date this iteration is
authorized to view live; Walkthrough explicitly waived per J-11's own acceptance text in
`docs/goal.md` ("maintenance repair of the derived layer with no UI surface of its own"); J-11's own
text places "the final repaired-state J-01/J-02/J-03 replay" under its own Stage G acceptance, which
is exactly what `UT-J-01`/`UT-J-02`/`UT-J-03` above already exercise at this same frontier date

**Preconditions:**
- Backend running at http://localhost:8255; J-11 is recorded CLOSED / PASSING in `docs/goal.md`
  (owner ruling, 2026-08-27) — this is a re-verification, not a re-run of the recovery

**Steps:**
1. Navigate to `http://localhost:3255/` (no `?asof` — frontier, 2026-08-12, one of J-11's 11
   regenerated incident dates)
2. Confirm the page loads with no error boundary, no crash, and no "backend not reachable" fallback
   text on any card
3. Confirm the "What changed", summary, and "Next-session focus" cards each render real content
   (per `UT-J-02`/`UT-J-03`/`UT-J-04` above) rather than an empty/error state
4. Open `http://localhost:8255/api/compass` and confirm the manifest's `version` field is unchanged
   from the value recorded in the iter-31 (or earlier) evidence — i.e., no new manifest version was
   minted merely by this page load

**Expected Result:**
- The Today page for the frontier date (one of the 11 incident dates J-11 regenerated) renders
  cleanly end to end — no stale-derived-state error, no crash
- The manifest `version` field is unchanged by this read-only visit — confirming the "verification
  must not itself mint a manifest" trap named in J-11's own Acceptance text still holds

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-J-01 | Sector attribution regression | regression | P1 | `/stocks` |
| UT-J-02 | What-changed regression | regression | P1 | `/` |
| UT-J-03 | Plain-English summary regression | regression | P1 | `/` |
| UT-J-04 | Next-session candidates regression | regression | P1 | `/` |
| UT-J-05 | Frozen manifest stamps regression | regression | P1 | `/` |
| UT-J-06 | Frozen manifest immutability regression | regression | P1 | `/` + `/api/compass` |
| UT-J-07 | Today ten-second read regression | regression | P1 | `/` |
| UT-J-08 | Market page relocation regression | regression | P1 | `/market` |
| UT-J-09 | Backend memory re-measurement byte-identity | regression | P1 | backend-only (Walkthrough waived) |
| UT-J-10 | Recovered trading days intact | regression | P1 | backend-only (Walkthrough waived) |
| UT-J-11 | Regenerated derived state serves cleanly | regression | P1 | `/` at frontier (Walkthrough waived) |

**All eleven test cases are P1** — this is a `Depth: full` iteration (prior verdict ESCALATE), and
`docs/goal.md`'s loop-mechanics guidance calls for widening regression to refresh goldens and catch
drift on exactly this kind of round. Per this iteration's own out-of-scope constraints, none of these
cases performs a `/data` Remove, backfill, or manifest regenerate — they re-verify already-produced
state using only the three pre-authorized `as_of` values. The authoritative pass/fail record for these
same journeys is the deterministic replay lane
(`reports/phase-goal-market-compass-iter-32-regression-replay-results.md`); this plan gives an operator
(or a browser-QA agent) an independent, manual way to spot-check the same claims through the real UI.
