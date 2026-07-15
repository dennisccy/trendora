# Phase goal-mcp-loop-iter-36 — UI Test Plan

**Phase:** goal-mcp-loop-iter-36 — Certifier calibration: referee placebo + lookahead-tripwire audit (J-22)
**Date:** 2026-07-14
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255
**Backend URL:** http://localhost:8255 (both confirmed reachable at plan-authoring time)

---

## Notes before you start

- **No validation-type tests in this plan.** This phase ships zero forms and zero user actions — `/research/referee-audit` is 100% read-only (the phase spec states "New user actions: none" verbatim). The manual-UI-test-plan-generator skill scopes validation tests to "one per form added or changed"; since no form was added, none is written here.
- **Stale-build trap:** before trusting any "card/page missing" observation, confirm `apps/frontend/.next/BUILD_ID` postdates `apps/frontend/app/research/referee-audit/page.tsx` and `apps/frontend/app/research/page.tsx`. This was true at plan-authoring time (BUILD_ID newer than both source files); if you see a 404 or the old 3-card grid, force a rebuild before assuming a bug (this is a recurring trap from iterations 20/21/35).
- **As-of date query param:** if the app's header shows a historical "as-of" date (not "latest"), navigation links may carry an `?asof=YYYY-MM-DD` query parameter. That is expected behavior, not a bug — the test steps below assume the default "latest" date.
- **Real data is already live:** the real offline audit run has already executed and its artifact is persisted at `runs/goal-session-mcp-loop/state/referee-audit-report.json`. No setup is needed for the default/happy-path tests (UT-01, UT-03, UT-04, UT-05, UT-10, UT-11, UT-12, UT-13) — you will see the real committed numbers immediately. Several tests below (UT-06, UT-07, UT-08, UT-09) deliberately override this state and must be reverted afterward — each such test says so explicitly.
- Several tests require stopping/restarting the backend. The backend on this environment binds deterministically to port **8255** whenever it is started via `./scripts/start-backend.sh` from the repo root (no extra flags needed) — confirmed by directly probing it during plan authoring.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — Referee-audit page loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research/referee-audit`

**Preconditions:**
- Frontend running at http://localhost:3255, backend running at http://localhost:8255
- The real committed artifact is in place (default repo state — no setup needed)

**Steps:**
1. Navigate to `http://localhost:3255/research/referee-audit`
2. Wait for the page to fully load
3. Open the browser DevTools console (F12) and check for errors

**Expected Result:**
- Page renders without a blank screen, without a Next.js error boundary, and without a 404
- The heading "Referee audit" is visible at the top of the page
- Directly below the heading, subtitle text beginning "Is the certifier itself calibrated?" is visible
- A "Back to Research" link with a left-arrow icon is visible above the heading
- The 4-card stat grid is visible below the heading (confirms the page settled into its loaded "ok" state, not stuck on a loading spinner)
- No errors appear in the browser console

---

### UT-02 — Loading skeleton renders before content (smoke)

**Type:** smoke
**Priority:** P3 (transient, timing-dependent state — informational, non-blocking for the overall verdict)
**Surface:** `/research/referee-audit`

**Preconditions:**
- Frontend running at http://localhost:3255, backend running at http://localhost:8255
- Chrome DevTools available for network throttling

**Steps:**
1. Open Chrome DevTools → Network tab → set throttling to "Slow 3G" (or the slowest available preset)
2. Navigate to `http://localhost:3255/research/referee-audit`
3. Observe the page in the moment immediately after navigation, before the API response resolves
4. Set throttling back to "No throttling" once observed

**Expected Result:**
- A pulsing 4-card skeleton grid appears, occupying the same layout position the real stat grid will fill
- Each skeleton card shows three pulsing gray placeholder bars (title-width, value-width, subtext-width)
- Once the throttled fetch resolves, the skeleton is fully replaced by the real 4-stat grid — it does not remain on screen indefinitely and does not overlap with the real content

---

### UT-03 — Stat summary grid displays the exact calibration values (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/referee-audit`

**Preconditions:**
- Frontend running at http://localhost:3255, backend running at http://localhost:8255
- The real committed artifact is in place (default state — no setup needed; do not set `TRENDORA_REFEREE_AUDIT_PATH`)

**Steps:**
1. Navigate to `http://localhost:3255/research/referee-audit`
2. Wait for the 4-card stat grid to render below the page heading
3. Read the first card, titled "Null trials"
4. Read the second card, titled "Empirical false-pass rate"
5. Read the third card, titled "Configured α"
6. Read the fourth card, titled "Run date"

**Expected Result:**
- "Null trials" card shows the large number **"200"**, with smaller text underneath reading "source factor: leadership_score"
- "Empirical false-pass rate" card shows **"0.08"**, with smaller text underneath reading "16 of 200 trials · 95% CI [0.04984, 0.126]"
- "Configured α" card shows **"0.05"**, with smaller text underneath reading "the significance level the null trials are judged against"
- "Run date" card shows **"2026-07-01"**, with smaller text underneath reading "seed 20240601 · contaminated horizon 5d"
- All four cards show real numbers immediately — no "—" placeholders, no perpetual loading spinner

---

### UT-04 — Tripwire failure card renders for the real live data (happy path / safety-critical)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/referee-audit`

**Preconditions:**
- Frontend running at http://localhost:3255, backend running at http://localhost:8255
- The real committed artifact is in place (default state — the contaminated factor's real verdict is "PASS", i.e. it was NOT caught)

**Steps:**
1. Navigate to `http://localhost:3255/research/referee-audit`
2. Scroll (if needed) to the verdict card directly below the 4-card stat grid
3. Note the card's border and background color
4. Read the card's heading text
5. Read the badge shown next to the phrase "instead it certified"
6. Read the paragraph of body text below the heading
7. Look for a smaller line of text below the paragraph

**Expected Result:**
- A card with a red border and a light-red/pink background tint is visible — this is the LOUD failure treatment, not the plain calm card
- Heading reads exactly: **"Tripwire: the lookahead-contaminated factor was NOT rejected"**
- A warning-triangle icon appears to the left of the heading
- The badge reads **"PASS"** and is colored red/danger — the same red family as the card border, never blue/accent
- Body paragraph includes the phrase **"expected: rejected"** and ends with **"treat every certified claim from this basis with suspicion until this is investigated"**
- A smaller line of text below the paragraph reads: "certified: holdout edge +0.0914 beats the control out-of-sample and is significant after multiple-testing deflation (p=0.0004998 < alpha/1=0.05)"
- The plain/calm confirmation card (green shield-check icon, "Lookahead-contaminated factor: caught" heading) is **NOT** present anywhere on the page

---

### UT-05 — Contaminated-status badge never uses "Proven"-style coloring (UX / anti-goal check)

**Type:** ux
**Priority:** P1 (elevated from the default P3 for UX tests — this directly verifies a *critical* anti-goal from `docs/goal.md`: a value must never be presented as proven unless backed by a passing certified claim)
**Surface:** `/research/referee-audit`

**Preconditions:**
- Frontend running at http://localhost:3255, backend running at http://localhost:8255
- Real committed artifact in place (default state, contaminated status is "PASS")

**Steps:**
1. Navigate to `http://localhost:3255/evidence` first and note the blue/accent color reserved for a "Proven" signal elsewhere in the product (used as a color reference only — no claim rows are expected there today)
2. Navigate to `http://localhost:3255/research/referee-audit`
3. Locate the badge reading "PASS" inside the red verdict card
4. Compare its color against the accent/"Proven" color noted in step 1
5. Read the full page for any use of the word "Proven" applied to the contaminated factor

**Expected Result:**
- The "PASS" badge on the referee-audit page is rendered in red/danger styling — it never matches the blue/accent "Proven" color from step 1, even though the underlying technical status is literally the string "PASS"
- No text anywhere on `/research/referee-audit` describes the contaminated factor's result as "Proven" or "proven"
- The badge sits immediately next to the plain-English caption "expected: rejected," making it immediately clear to a first-time reader that "PASS" here is bad news, not confirmation

---

### UT-06 — Calm confirmation card renders when the contaminated factor IS caught (happy path — alternate fixture state)

**Type:** happy-path
**Priority:** P2 (not today's live default state — requires a fixture swap; secondary path to the primary tripwire flow in UT-04)
**Surface:** `/research/referee-audit`

**Preconditions:**
- Frontend running at http://localhost:3255
- You can stop/restart the backend process from a terminal at the repo root

**Steps:**
1. Copy the real artifact file (`runs/goal-session-mcp-loop/state/referee-audit-report.json`) to a new file, e.g. `/tmp/referee-audit-fixture-caught.json`, and in the copy change the `"status"` field inside `"contaminated_verdict"` from `"PASS"` to `"FAIL"`
2. Stop the running backend (e.g., `fuser -k 8255/tcp` or Ctrl+C in its terminal)
3. From the repo root, start it with the override: `TRENDORA_REFEREE_AUDIT_PATH=/tmp/referee-audit-fixture-caught.json ./scripts/start-backend.sh`
4. Navigate to `http://localhost:3255/research/referee-audit`
5. Inspect the verdict card below the stat grid

**Expected Result:**
- A plain (non-red) card is visible in place of the tripwire card, with a green shield-check icon next to the heading **"Lookahead-contaminated factor: caught"**
- Body text reads "Verdict:" followed by a badge showing **"FAIL"**, still colored in red/danger (never blue/accent — consistent with UT-05: even a caught/correct verdict badge is not styled as "Proven")
- The red tripwire card from UT-04 is **NOT** present
- **Revert after this test:** stop the backend (`fuser -k 8255/tcp`) and restart it cleanly with `./scripts/start-backend.sh` (no `TRENDORA_REFEREE_AUDIT_PATH` set) to return to serving the real artifact

---

### UT-07 — Honest empty state when no artifact has ever been persisted (error / honest degradation)

**Type:** error
**Priority:** P2
**Surface:** `/research/referee-audit`

**Preconditions:**
- Frontend running at http://localhost:3255
- You can stop/restart the backend process from a terminal at the repo root

**Steps:**
1. Stop the running backend (`fuser -k 8255/tcp` or Ctrl+C in its terminal)
2. From the repo root, start it pointed at a path that does not exist: `TRENDORA_REFEREE_AUDIT_PATH=/tmp/referee-audit-does-not-exist.json ./scripts/start-backend.sh`
3. Navigate to `http://localhost:3255/research/referee-audit`
4. Inspect the page content

**Expected Result:**
- A card is visible with heading **"No audit run yet"**
- Body text explains the harness "runs as a config-seeded offline job (`python -m app.engine.referee_audit`), never as a UI action here"
- No stat grid and no tripwire/calm verdict card appear; no JavaScript error boundary or blank page appears
- The page heading "Referee audit" and the "Back to Research" link remain visible above the empty-state card
- **Revert after this test:** stop the backend (`fuser -k 8255/tcp`) and restart it cleanly with `./scripts/start-backend.sh` (no env override) to return to serving the real artifact

---

### UT-08 — Unreadable artifact renders a distinct amber degraded state (error / honest degradation)

**Type:** error
**Priority:** P2
**Surface:** `/research/referee-audit`

**Preconditions:**
- Frontend running at http://localhost:3255
- You can stop/restart the backend process from a terminal at the repo root

**Steps:**
1. Create a file at `/tmp/referee-audit-corrupt.json` containing only the literal text `not-json` (invalid JSON, no quotes)
2. Stop the running backend (`fuser -k 8255/tcp` or Ctrl+C in its terminal)
3. From the repo root, start it pointed at the corrupt file: `TRENDORA_REFEREE_AUDIT_PATH=/tmp/referee-audit-corrupt.json ./scripts/start-backend.sh`
4. Navigate to `http://localhost:3255/research/referee-audit`
5. Inspect the card's border color and text

**Expected Result:**
- A card with an **amber/yellow** border and background is visible — amber, not red, and visibly different from both the UT-07 empty-state card and the UT-04 red tripwire card
- Heading reads **"Audit artifact unreadable"**
- Body text instructs: "Re-run the offline harness (`python -m app.engine.referee_audit`) to regenerate it"
- No stat grid and no verdict card are shown
- **Revert after this test:** stop the backend (`fuser -k 8255/tcp`) and restart it cleanly with `./scripts/start-backend.sh` (no env override) to return to serving the real artifact

---

### UT-09 — Backend unavailable shows a contained error card, navigation stays intact (error / anti-goal resilience)

**Type:** error
**Priority:** P1 (elevated from the default P2 for error tests — verifies a *critical* anti-goal: the UI must degrade gracefully on backend failure, "never a blank application-error page")
**Surface:** `/research/referee-audit`

**Preconditions:**
- Frontend running at http://localhost:3255
- Backend currently reachable (it will be stopped as part of this test)

**Steps:**
1. Stop the backend process (`fuser -k 8255/tcp` or Ctrl+C in its terminal)
2. Navigate to `http://localhost:3255/research/referee-audit` (or reload if already on the page)
3. Wait a few seconds for the fetch to fail
4. Inspect the page for an error card
5. Click the "Back to Research" link
6. From the Research hub, click any other card (e.g., "Certification-budget accounting") to confirm the rest of the site still attempts normal navigation

**Expected Result:**
- A contained card with a red border is visible, reading **"Backend unavailable"** with body text "The referee-audit report could not load from the API. Confirm the backend is running and reload."
- The card does NOT take over the whole page — the page heading "Referee audit," subtitle, and "Back to Research" link remain visible above it
- No blank white screen and no unhandled crash/error-boundary page appears
- Clicking "Back to Research" successfully navigates to `/research` and the hub page (including its nav) still renders
- **Revert after this test:** restart the backend with `./scripts/start-backend.sh` from the repo root before running any further tests

---

### UT-10 — New "Referee audit" card is discoverable on `/research` and navigates correctly (UX — new capability)

**Type:** ux
**Priority:** P1 (elevated from the default P3 for UX tests — this is the phase's entire new user-facing capability; the Definition of Done explicitly requires "the 4th governance card appears on `/research` and navigates correctly")
**Surface:** `/research`

**Preconditions:**
- Frontend running at http://localhost:3255, backend running at http://localhost:8255

**Steps:**
1. Navigate to `http://localhost:3255/research`
2. Scroll down to the section headed **"Governance & process"**
3. Count the cards in that section
4. Locate the 4th card, positioned immediately after "Certification-budget accounting"
5. Read its icon, heading, and description text
6. Click the 4th card

**Expected Result:**
- The "Governance & process" section shows exactly **4 cards**, in this order: "Pre-registration registry," "Negative-results graveyard," "Certification-budget accounting," **"Referee audit"**
- The 4th card shows a shield-check icon, heading **"Referee audit,"** and description text beginning "Is the certifier itself calibrated?"
- The card has the same border-highlight-on-hover visual treatment as its 3 siblings (border and background change color when you hover over it)
- Clicking the card navigates the browser to `http://localhost:3255/research/referee-audit`
- The referee-audit page loads successfully (heading "Referee audit" visible) — confirms the link is wired correctly, not a dead link or 404

---

### UT-11 — Existing 3 governance cards are unchanged (regression)

**Type:** regression
**Priority:** P3
**Surface:** `/research`

**Preconditions:**
- Frontend running at http://localhost:3255, backend running at http://localhost:8255

**Steps:**
1. Navigate to `http://localhost:3255/research`
2. In the "Governance & process" section, read the heading and description text of the first 3 cards: "Pre-registration registry," "Negative-results graveyard," "Certification-budget accounting"
3. Click "Pre-registration registry" and confirm it navigates to `/research/registry`
4. Navigate back to `http://localhost:3255/research`, click "Negative-results graveyard," confirm it navigates to `/research/graveyard`
5. Navigate back to `http://localhost:3255/research`, click "Certification-budget accounting," confirm it navigates to `/research/budget`

**Expected Result:**
- All 3 existing cards show the same heading text, description text, icon, and hover styling they had before this phase — nothing about them changed
- Each of the 3 links still navigates to its own page (`/research/registry`, `/research/graveyard`, `/research/budget`) without a 404 or error
- The cards did not move or get reordered relative to each other — the new "Referee audit" card was appended as a 4th card after them, not inserted between them

---

### UT-12 — Preflight banner still renders on the new referee-audit page (regression — required-still-passing J-20)

**Type:** regression
**Priority:** P2 (elevated from the default P3 — the phase spec explicitly names J-20, the cross-cutting preflight banner, as required to still render correctly on this new page)
**Surface:** `/research/referee-audit`

**Preconditions:**
- Frontend running at http://localhost:3255, backend running and healthy at http://localhost:8255

**Steps:**
1. Navigate to `http://localhost:3255/research/referee-audit`
2. Look at the very top of the browser viewport, above the "Referee audit" page heading (this banner is shared across every page in the product, not specific to this one)
3. Read the banner's text and note its color

**Expected Result:**
- A thin banner strip is visible at the very top of the page, above the page heading
- With a healthy backend and current data, it reads **"GO — today's board is current."** in a quiet green-tinted strip
- Only one banner is visible (not duplicated), and it does not overlap or push the "Referee audit" heading off-screen
- The same banner (same text, same styling) is visible if you navigate to any other `/research/*` page, e.g. `/research/budget`

---

### UT-13 — `/evidence` remains unchanged after the audit ran — isolation proof (regression — dominant failure mode)

**Type:** regression
**Priority:** P1 (elevated from the default P3 for regression tests — this is the Definition of Done's dominant-failure-mode gate: "Isolation proven... verified after the audit run." The real certified-claims ledger must never be polluted by the audit's throwaway trials.)
**Surface:** `/evidence`

**Preconditions:**
- Frontend running at http://localhost:3255, backend running at http://localhost:8255
- The offline referee-audit harness has already run at least once (true by default — the real artifact exists)

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Read the page heading and subtitle
3. Inspect the page body for either a list of individual claim rows or a single empty-state card
4. If the empty-state card is shown, read its heading and body text

**Expected Result:**
- Page heading reads **"Evidence"**; subtitle mentions "the single source of proven-ness"
- A single empty-state card is shown, with heading **"No certified claims yet"** and body text stating every signal "currently reads Not yet proven"
- No individual claim row appears anywhere on the page — confirming the audit's 200 null trials and 1 contaminated-factor trial never leaked into the real certified-claims ledger as a new visible entry
- This is the exact same empty state the page showed before this phase shipped — no new "Proven" badge, no new row, nothing added

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Referee-audit page loads without errors | smoke | P1 | `/research/referee-audit` |
| UT-02 | Loading skeleton renders before content | smoke | P3 | `/research/referee-audit` |
| UT-03 | Stat summary grid shows exact calibration values | happy-path | P1 | `/research/referee-audit` |
| UT-04 | Tripwire failure card renders for real live data | happy-path | P1 | `/research/referee-audit` |
| UT-05 | Contaminated badge never uses "Proven" styling | ux | P1 | `/research/referee-audit` |
| UT-06 | Calm confirmation card when factor is caught (fixture) | happy-path | P2 | `/research/referee-audit` |
| UT-07 | Honest empty state when no artifact exists | error | P2 | `/research/referee-audit` |
| UT-08 | Unreadable artifact shows distinct amber state | error | P2 | `/research/referee-audit` |
| UT-09 | Backend unavailable shows contained card, nav intact | error | P1 | `/research/referee-audit` |
| UT-10 | New "Referee audit" card discoverable and navigates | ux | P1 | `/research` |
| UT-11 | Existing 3 governance cards unchanged | regression | P3 | `/research` |
| UT-12 | Preflight banner still renders on new page | regression | P2 | `/research/referee-audit` |
| UT-13 | `/evidence` unchanged after audit ran (isolation) | regression | P1 | `/evidence` |

**P1 tests (UT-01, UT-03, UT-04, UT-05, UT-09, UT-10, UT-13) must all pass for browser QA verdict to be PASS.**
