# Phase goal-mcp-loop-iter-35 — UI Test Plan

**Phase:** goal-mcp-loop-iter-35
**Date:** 2026-07-14
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255

---

## Environment Note (read before running any test below)

At the time this plan was written, the live artifact file the drift feature reads —
`runs/goal-session-mcp-loop/state/drift-report.json` (relative to repo root; absolute path
`/home/dennis-chan/Git/trendora/runs/goal-session-mcp-loop/state/drift-report.json`) — **already
exists on disk with `status: "drift"` for 435 symbols**, all sharing the single mismatching date
`2006-05-12` (left over from dev/test activity earlier this iteration, not a real vendor
re-adjustment). This means, **before you touch anything**, `/data` may already show the loud amber
drift card and the site-wide banner may already read `DEGRADED`. That is expected residue, not a
bug — but it also means you cannot infer a test's pass/fail from "the card is currently loud/quiet"
alone. Every test case below gives its own exact precondition (what the artifact file must contain,
or must be absent) so results are deterministic regardless of what is on disk when you start.

Two more facts that make every fixture step below reliable:
- **No backend/frontend restart is ever required** after changing the artifact file. Both
  `GET /api/data` and `GET /api/health` (which the site-wide banner reads) call the single reader
  `read_drift_report()` fresh on every request — it is a tiny-file read, never cached.
- The `/data` page's drift card only re-fetches on page mount (initial load, or after a job on that
  page completes) — **a hard refresh (F5) is required** to see an externally-changed artifact file.
  The site-wide banner, by contrast, is on its own poll loop (2s while warming, backing off to 30s
  once ready per `config.yaml`'s `health_poll_interval_seconds` / `health_poll_idle_interval_seconds`)
  and will pick up a changed artifact **within 30 seconds without any manual action**, in addition to
  updating immediately on a page navigation/refresh.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — `/data` loads and the new drift card renders in some valid state (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running and reachable (the page must not show the red "Backend unavailable" card)
- No specific artifact fixture required — test with whatever is currently on disk

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Wait for the page to finish loading (the "Dataset coverage" card is visible, not a loading skeleton)
3. Locate the card titled "Live-vs-seed drift" (it has a two-arrow/compare icon next to the title) —
   it sits directly below the "Storage footprint" card and directly above the "Rebuild snapshots for
   current universe" panel

**Expected Result:**
- The page renders without a blank screen, without a browser console error, and without the red
  "Backend unavailable" box
- The "Live-vs-seed drift" card is present and shows exactly one of these four states (any one is a
  PASS for this smoke test — only a crash, a missing card, or an empty card body is a FAIL):
  - Gray text "No fetch has run yet — nothing to compare against the committed seed."
  - Green-dot text "The most recent fetch matched the committed seed over the last `N` common date(s)."
  - An amber box headed "Live-vs-seed drift detected — the provider re-adjusted already-committed
    history for `N` symbol(s)." with a list below it
  - An amber box reading "The drift report exists but could not be read. Re-run a Fetch job to
    regenerate it."
- Directly under the card's title, a gray one-line explanation is visible without hovering or
  clicking anything (starts with "Byte/fixed-precision compares the last N dates…")

---

### UT-02 — Drift card shows the honest "no fetch yet" state when the artifact is absent (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend is running at http://localhost:3255; backend running and reachable
- The file `runs/goal-session-mcp-loop/state/drift-report.json` does **not** exist — rename or delete
  it if present (e.g. move it to `drift-report.json.bak`)
- (This is the same artifact-absent setup UT-09 needs — you can verify both in the same pass.)

**Steps:**
1. Confirm the file `runs/goal-session-mcp-loop/state/drift-report.json` is absent
2. Navigate to `http://localhost:3255/data`
3. Locate the "Live-vs-seed drift" card

**Expected Result:**
- The card shows the exact gray text: "No fetch has run yet — nothing to compare against the
  committed seed." (`data-testid="drift-status-absent"`)
- No amber/warning styling is present on this card
- No affected-symbol list is shown
- This state is visually distinct from the green "clean" state (no green dot, no "matched the
  committed seed" wording) — the two must not be confused with each other

---

### UT-03 — Drift card names the exact symbol + dates when an adjustment seam is detected (happy path — core capability)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend is running at http://localhost:3255; backend running and reachable
- Overwrite `runs/goal-session-mcp-loop/state/drift-report.json` with exactly this content:
  ```json
  {"status": "drift", "reference": "2026-07-10", "overlap_days": 20, "affected": [{"symbol": "AAPL", "mismatching_dates": ["2026-07-08", "2026-07-09"], "classification": "adjustment_seam"}, {"symbol": "MSFT", "mismatching_dates": ["2026-07-07"], "classification": "adjustment_seam"}]}
  ```

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Locate the "Live-vs-seed drift" card
3. Read the card's heading line and the list beneath it

**Expected Result:**
- The card renders with an amber/warning border and background (`data-testid="drift-status-drift"`),
  matching the same amber tone used elsewhere on this page (e.g. the "Rebuild" panel's absent-member
  warning)
- The heading text reads exactly: "Live-vs-seed drift detected — the provider re-adjusted
  already-committed history for 2 symbols."
- The list shows exactly two rows, in this content (order not required to match exactly, but both
  rows and all details must be present):
  - "AAPL: 2026-07-08, 2026-07-09 — adjustment seam"
  - "MSFT: 2026-07-07 — adjustment seam"
- A symbol NOT in the fixture (e.g. "GOOGL") does not appear anywhere in the card
- The word "adjustment seam" appears once per listed symbol

---

### UT-04 — Drift card shows the clean/quiet state after a clean overlap (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend is running at http://localhost:3255; backend running and reachable
- Overwrite `runs/goal-session-mcp-loop/state/drift-report.json` with exactly this content:
  ```json
  {"status": "clean", "reference": "2026-07-10", "overlap_days": 20, "affected": []}
  ```

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Locate the "Live-vs-seed drift" card

**Expected Result:**
- The card shows a small green dot followed by the exact text: "The most recent fetch matched the
  committed seed over the last 20 common date(s)." (`data-testid="drift-status-clean"`)
- No amber/warning styling anywhere on the card
- No affected-symbol list is shown
- The number "20" matches `config.yaml`'s `data_quality.drift.overlap_days` value, rendered verbatim
  (not hardcoded UI copy)

---

### UT-05 — Drift card degrades honestly when the artifact is corrupted, never crashes (error)

**Type:** error
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- Frontend is running at http://localhost:3255; backend running and reachable
- Overwrite `runs/goal-session-mcp-loop/state/drift-report.json` with the literal text `not-json`
  (no quotes, not valid JSON)

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Locate the "Live-vs-seed drift" card
3. Confirm the rest of the page still renders (scroll past the card)

**Expected Result:**
- The card shows an amber box with the exact text: "The drift report exists but could not be read.
  Re-run a Fetch job to regenerate it." (`data-testid="drift-status-unreadable"`)
- The page does NOT crash, does NOT show a blank white screen, and does NOT silently show the
  "clean" or "no fetch yet" text instead (a corrupted file must never be treated as fine)
- Every other panel on `/data` ("Dataset coverage", "Storage footprint", "Rebuild snapshots for
  current universe", the availability heatmap, job panels) still renders normally around it
- Optional bonus check (same artifact, cross-surface): reload any other page (e.g.
  `http://localhost:3255/`) and confirm the site-wide banner's amber "DEGRADED" box lists the reason
  "Drift report is unreadable: the artifact exists but could not be parsed." — the two surfaces read
  the identical artifact and must never disagree

---

### UT-06 — Drift card degrades gracefully when a field is present-but-null (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- Frontend is running at http://localhost:3255; backend running and reachable
- Overwrite `runs/goal-session-mcp-loop/state/drift-report.json` with exactly this content (a
  syntactically valid "clean" report, but with `overlap_days` explicitly null):
  ```json
  {"status": "clean", "reference": "2026-07-10", "overlap_days": null, "affected": []}
  ```

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Locate the "Live-vs-seed drift" card

**Expected Result:**
- The card still renders the green-dot "clean" line, but with an em dash placeholder instead of a
  number: "The most recent fetch matched the committed seed over the last — common date(s)."
- No crash, no "NaN", no "null", no "undefined" text is shown anywhere on the card
- No amber/warning styling is triggered by the missing number alone (the `status` is still `"clean"`)

---

### UT-07 — Site-wide preflight banner surfaces the drift DEGRADED reason on a page other than `/data` (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` (and every page — layout-mounted banner)

**Preconditions:**
- Frontend is running at http://localhost:3255; backend running and reachable
- Overwrite `runs/goal-session-mcp-loop/state/drift-report.json` with the SAME two-symbol drift
  fixture used in UT-03:
  ```json
  {"status": "drift", "reference": "2026-07-10", "overlap_days": 20, "affected": [{"symbol": "AAPL", "mismatching_dates": ["2026-07-08", "2026-07-09"], "classification": "adjustment_seam"}, {"symbol": "MSFT", "mismatching_dates": ["2026-07-07"], "classification": "adjustment_seam"}]}
  ```

**Steps:**
1. Navigate directly to `http://localhost:3255/` (the Dashboard) — do NOT visit `/data` first
2. Observe the thin strip immediately below the top header bar (above the page's main content)
3. If it still reads the quiet green "GO" strip, wait up to 30 seconds without touching anything,
   then look again (the health poll picks up the file change on its own cadence)

**Expected Result:**
- The banner changes to the loud amber box (`data-testid="preflight-banner"`,
  `data-verdict="DEGRADED"`)
- The banner's bold heading reads exactly: "DEGRADED — treat today's board with caution."
- The bulleted reasons list beneath it contains this exact line: "Live-vs-seed drift detected
  (adjustment seam) for: AAPL, MSFT."
- This is visible on the Dashboard without ever navigating to `/data` — the warning is site-wide, not
  page-local
- The banner is still present (same amber state) after navigating to any other page (e.g.
  `/stocks`), confirming it is mounted once at the layout level, not per-page

---

### UT-08 — Preflight banner recovers to GO after a clean fetch supersedes the drifted one (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` (and every page)

**Preconditions:**
- Frontend is running at http://localhost:3255; backend running and reachable
- Start from the DEGRADED state (either continue directly from UT-07, or overwrite the artifact
  fresh): confirm `http://localhost:3255/` currently shows the amber `DEGRADED` banner
- Then overwrite `runs/goal-session-mcp-loop/state/drift-report.json` with the clean fixture:
  ```json
  {"status": "clean", "reference": "2026-07-11", "overlap_days": 20, "affected": []}
  ```

**Steps:**
1. With the banner showing DEGRADED, replace the artifact file with the clean fixture above
2. Wait up to 30 seconds without touching the page, or press F5 to refresh immediately
3. Observe the banner

**Expected Result:**
- The banner returns to the quiet strip: green dot + exact text "GO — today's board is current."
  (`data-verdict="GO"`)
- The amber box and its bulleted reasons list are gone entirely — no leftover reason text
- Navigating to `http://localhost:3255/data` and reloading shows the drift card's green "clean" line
  (UT-04's expected text), confirming both surfaces recovered together from the same artifact

---

### UT-09 — J-20 non-regression: banner stays GO, unchanged, when the drift artifact is absent (regression — load-bearing)

**Type:** regression
**Priority:** P1
**Surface:** `/` (and every page)

**Preconditions:**
- Frontend is running at http://localhost:3255; backend running and reachable
- The file `runs/goal-session-mcp-loop/state/drift-report.json` does **not** exist (same setup as
  UT-02 — rename/delete it if present)
- All other readiness inputs are healthy (fresh committed seed, no induced servability/freshness/
  integrity breach)

**Steps:**
1. Confirm the artifact file is absent
2. Navigate to `http://localhost:3255/` and, separately, to two other pages (e.g. `/stocks` and
   `/data`)
3. Observe the banner on each

**Expected Result:**
- On every page, the banner reads the quiet strip "GO — today's board is current."
  (`data-verdict="GO"`), with no bulleted reasons list at all
- This must be indistinguishable from the pre-iter-35 banner behavior — the new drift input must
  never turn a previously-clean board DEGRADED or NO-GO just because no fetch has ever run. This is
  the single most important non-regression property this iteration must not break: an operator who
  never runs a Fetch job should see byte-identical banner behavior to before this phase shipped

---

### UT-10 — J-13 non-regression: existing `/data` panels and drift-card placement are unbroken (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- Frontend is running at http://localhost:3255; backend running and reachable
- Any drift-artifact state is acceptable for this test (content is not being checked here, only
  surrounding layout/content)

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Locate the "Dataset coverage" card (the first card on the page) and read its metric tiles
3. Scroll down and note the vertical order of cards from top to bottom

**Expected Result:**
- The "Dataset coverage" card shows all of its existing metric tiles with numeric values (not blank):
  "Price history", "Universe (as of date)", "Candidate universe", "Symbols", "Trading days",
  "Snapshot dates", "Backfill gaps"
- The card order from top to bottom is: "Dataset coverage" → "Storage footprint" → **"Live-vs-seed
  drift" (new)** → "Rebuild snapshots for current universe" → the rest of the existing panels — the
  new card is additive in this one slot; no existing card moved, split, or disappeared
- No layout shift, overlap, or visual clipping is introduced by the new card

---

### UT-11 — J-01 non-regression: Stocks leaderboard evidence badges are unaffected (regression)

**Type:** regression
**Priority:** P3
**Surface:** `/stocks`

**Preconditions:**
- Frontend is running at http://localhost:3255; backend running and reachable

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Observe the leaderboard rows

**Expected Result:**
- The "Stocks" leaderboard loads with ranked rows (heading "Stocks" is visible)
- At least one row shows an evidence badge (`data-testid="evidence-badge"`) reading either "Proven"
  or "Not yet proven"
- No visual regression, no missing rows, no console error — this iteration touched no code on this
  page

---

### UT-12 — J-05 non-regression: Evidence ledger page is unaffected (regression)

**Type:** regression
**Priority:** P3
**Surface:** `/evidence`

**Preconditions:**
- Frontend is running at http://localhost:3255; backend running and reachable

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Observe the page content

**Expected Result:**
- The page heading "Evidence" is visible, with the subtitle mentioning "Proven" / "Not yet proven"
- The page shows existing certified-claim rows (`data-testid="evidence-claim-row"`) — it must NOT
  show the red "could not load from the API" error card, and (since the ledger is not empty) it
  should NOT show the "No certified claims yet" empty state either
- Optional stronger check (requires filesystem access, not just the browser): the file
  `runs/goal-session-mcp-loop/state/certified-claims.jsonl` still has exactly the same line count it
  had before this iteration's dev work — this iteration introduces no Evidence Claim and must not add
  any new ledger entry

---

### UT-13 — Drift card is discoverable without any hover or click interaction (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/data` (reached from any page via the sidebar)

**Preconditions:**
- Frontend is running at http://localhost:3255; backend running and reachable

**Steps:**
1. From any page (e.g. the Dashboard at `http://localhost:3255/`), look at the left sidebar
2. Click the "Data Manager" link in the sidebar
3. Without clicking, hovering, or scrolling anything, look directly below the "Live-vs-seed drift"
   card's title

**Expected Result:**
- "Data Manager" is reachable in exactly 1 click from any page (it is always present in the
  persistent left sidebar, not nested in a submenu)
- Clicking it navigates to `http://localhost:3255/data`
- The explanatory sentence below the card's title is visible immediately, with no interaction
  required: "Byte/fixed-precision compares the last N dates a Fetch job returns against the
  committed seed. A mismatch means the live provider silently re-adjusted already-committed history
  (an adjustment seam) — descriptive integrity reporting, recomputes nothing, never auto-repairs or
  re-fetches."
- The card's title itself, "Live-vs-seed drift", is plain language — a first-time reader does not
  need external documentation to understand what the card is for once they read the sentence beneath
  it

---

### UT-14 — Backend-unavailable fallback on `/data` still works with the new card present (error)

**Type:** error
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is stopped, or made unreachable from the frontend, for this test only

**Steps:**
1. With the backend unreachable, navigate to `http://localhost:3255/data`
2. Observe the page content

**Expected Result:**
- The page shows the existing red-bordered error card with the heading "Backend unavailable" and the
  body text: "Dataset coverage could not load from the API. No figures are shown rather than
  fabricated values. Confirm the backend is running and retry."
- The "Live-vs-seed drift" card does NOT render at all in this state (it is nested inside the same
  successful-load branch as every other `/data` panel) — there is no partial/broken drift card
  fragment, no second error box, and no crash
- Restoring the backend and reloading returns the page to normal (one of UT-01's four valid card
  states reappears)

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Drift card renders in some valid state | smoke | P1 | `/data` |
| UT-02 | Drift card: absent/"no fetch yet" state | smoke | P1 | `/data` |
| UT-03 | Drift card: names symbol + dates on drift | happy-path | P1 | `/data` |
| UT-04 | Drift card: clean/quiet state | happy-path | P1 | `/data` |
| UT-05 | Drift card: corrupted artifact degrades honestly | error | P2 | `/data` |
| UT-06 | Drift card: null field degrades gracefully | validation | P2 | `/data` |
| UT-07 | Banner: surfaces drift DEGRADED reason site-wide | happy-path | P1 | `/` (layout) |
| UT-08 | Banner: recovers to GO after clean fetch | happy-path | P1 | `/` (layout) |
| UT-09 | Banner: GO unchanged when artifact absent (J-20) | regression | P1 | `/` (layout) |
| UT-10 | `/data` existing panels + card placement (J-13) | regression | P2 | `/data` |
| UT-11 | Leaderboard evidence badges unaffected (J-01) | regression | P3 | `/stocks` |
| UT-12 | Evidence ledger page unaffected (J-05) | regression | P3 | `/evidence` |
| UT-13 | Drift card discoverable, no hover needed | ux | P2 | `/data` |
| UT-14 | Backend-unavailable fallback still works | error | P2 | `/data` |

**P1 tests must all pass for browser QA verdict to be PASS.** P1 covers: the card renders (UT-01,
UT-02), the two core new states are correct (UT-03, UT-04), the banner correctly surfaces and clears
the new reason (UT-07, UT-08), and the load-bearing non-regression property that an untouched board
stays GO (UT-09).
