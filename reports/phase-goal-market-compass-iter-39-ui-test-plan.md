# Phase goal-market-compass-iter-39 — UI Test Plan

**Phase:** goal-market-compass-iter-39
**Date:** 2026-09-02
**Written by:** ui-impact-analyst (combined mode)
**Frontend URL:** http://localhost:3255
**Backend URL:** http://localhost:8255

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from the phase spec's own TC-XX functional test IDs. -->

---

### UT-01 — Today page loads without errors at the latest date (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend running at http://localhost:3255, backend running at http://localhost:8255.
- No `?asof` param — default view shows the latest stored date (frontier, `2026-08-12`).

**Steps:**
1. Navigate to `http://localhost:3255/`
2. Wait for the page to fully load (skeleton cards replaced by real content).

**Expected Result:**
- The heading "Today" with subtitle "The ten-second read after the close" is visible.
- A badge reading "Data as-of 2026-08-12" (or the current frontier date) is visible next to the heading.
- No "Something went wrong on this page" card and no "Backend unavailable" card appear anywhere.
- The "Market state", summary, "What changed", leadership rotation, "Next-session focus", and manifest strip cards all render below the heading.
- No console errors.

---

### UT-02 — Pre-iter-38 historical date renders fully with the honest degraded "Not priority" text (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` → Next-session focus card

**Preconditions:**
- Frontend/backend running as above.
- `2026-08-11` is a genuine pre-iter-38 stored manifest row (no `why_not_totals`, no `reason`/`cap_rank`/`cap` on its `why_not[]` entries).

**Steps:**
1. Navigate to `http://localhost:3255/?asof=2026-08-11`
2. Wait for the page to fully load.
3. Scroll to the "Next-session focus" card and read the disclosure summary line below the candidate cards / empty-state text.
4. Click the "Not priority (...)" disclosure summary line to expand it.

**Expected Result:**
- No "Something went wrong on this page" card appears anywhere on the page (this was the AG-8 crash before this fix).
- The disclosure summary text reads exactly: `Not priority (20 shown — held-back counts unavailable for this manifest version)`
- After expanding, a list of ticker entries appears. NONE of them shows a "— ranked #N of the above-floor names, cap ..." lead-in sentence (that data is honestly absent for this manifest version — never fabricated).
- Each entry still shows its own `failed_conditions` list (or renders with none, per its own data) with no exception thrown and no blank section.

---

### UT-03 — Frontier date's "Not priority" text is byte-identical to before this fix (happy path / regression)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` → Next-session focus card

**Preconditions:**
- `2026-08-12` is the post-iter-38 frontier manifest (v10) — the one row that already carries `why_not_totals` and per-entry `reason`/`cap_rank`/`cap`.

**Steps:**
1. Navigate to `http://localhost:3255/?asof=2026-08-12`
2. Scroll to the "Next-session focus" card's disclosure summary line.
3. Click the "Not priority (...)" summary line to expand it.

**Expected Result:**
- The disclosure summary text reads exactly: `Not priority (20 shown of 52 held back — 27 cap-excluded, 25 below-floor near-miss)` — the same string this manifest showed before this iteration's fix.
- After expanding, at least one entry shows a "— ranked #N of the above-floor names, cap 20" lead-in sentence with a real numeric rank and cap value (not blank, not "undefined").

---

### UT-04 — Backend-unreachable state still shows an honest error card, not a crash (error)

**Type:** error
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Stop the backend process (e.g. `Ctrl+C` the process started by `scripts/start-backend.sh`, or otherwise make `http://localhost:8255/api/health` fail).

**Steps:**
1. With the backend stopped, navigate to `http://localhost:3255/` (or refresh if already open).
2. Wait a few seconds for the fetch to fail.

**Expected Result:**
- A red-bordered card reading "Backend unavailable" appears, with the text "The Today page could not load the market regime from the API. Nothing is fabricated — confirm the backend is running and reload."
- No blank page and no generic Next.js crash screen.
- Restart the backend (`bash scripts/start-backend.sh`) before continuing to the remaining test cases.

---

### UT-05 — J-04: candidate reasoning and "Not priority" click-through on two historical dates (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/` → Next-session focus card

**Preconditions:**
- Journey script `J-04.json` restored to its original (pre-iter-38-edit) targets.

**Steps:**
1. Navigate to `http://localhost:3255/?asof=2026-07-23`
2. Verify the text "Strong leader (81.2)" is visible somewhere on the page (a candidate card verdict/score).
3. Click the "Not priority (20)" disclosure summary text to expand it.
4. Verify the text "TRV" appears in the expanded list.
5. Navigate to `http://localhost:3255/?asof=2026-03-30`
6. Verify the text "REGIME_RISK_OFF" is visible on the page.

**Expected Result:**
- All three text assertions above are met, in order, with no error card at any step.

---

### UT-06 — J-05/J-06: a frozen manifest's provenance timestamp is immutable across repeat visits (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/` → manifest strip

**Preconditions:**
- Journey scripts `J-05.json`/`J-06.json` restored to their original `2025-04-15` target.

**Steps:**
1. Navigate to `http://localhost:3255/?asof=2025-04-15`
2. Verify the text "MCD" is visible on the page (a manifest cohort/candidate ticker).
3. Verify the text "Basis: available" is visible in the manifest strip.
4. Verify the exact text `2026-08-20T11:41:00.381102+00:00` is visible in the manifest strip's provenance detail.
5. Reload the page (F5) and repeat steps 2–4.

**Expected Result:**
- All three text values are present on both the first load and the reload, byte-identical — confirming the frozen manifest's provenance timestamp is not re-minted or altered merely by viewing it (AG-12/AG-17).
- No error card at any step.

---

### UT-07 — J-07: the Today page's ten-second read and market-link navigation (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`, `/market`

**Preconditions:**
- Journey script `J-07.json` restored to its original 7-step content.

**Steps:**
1. Navigate to `http://localhost:3255/`
2. Verify the text "Risk-on" is visible on the page.
3. Verify the exact text "Universe breadth: 59.8% of the universe above its 50-day average" is visible.
4. Click the "Full market context (regime × phase, sectors, themes)" link (`data-testid="compass-state-band-market-link"`) in the "Market state" card.
5. Verify the text "severity-velocity line" is visible on the resulting `/market` page.
6. Navigate back to `http://localhost:3255/` and verify the element with `data-testid="compass-state-band-regime-direction"` contains the text "little changed", the element with `data-testid="compass-state-band-stress-direction"` contains "little changed", and the element with `data-testid="compass-state-band-breadth-direction"` contains "little changed".
7. Navigate to `http://localhost:3255/?asof=2026-08-03`
8. Verify the exact text "Conditions are improving since the prior session (+4.7 regime-score points)." is visible.

**Expected Result:**
- All text/element assertions above pass in order, with no error card at any step and real values shown (never placeholders).

---

### UT-08 — All 21 previously-crashing dates load without error, looped (regression / breadth)

**Type:** regression
**Priority:** P1
**Surface:** `/` (all cards)

**Preconditions:**
- Frontend/backend running.

**Steps:**
1. For each date in this list — `1996-01-02`, `1996-02-01`, `2001-04-17`, `2005-04-01`, `2018-11-20`, `2019-03-01`, `2020-01-02`, `2020-03-20`, `2022-06-15`, `2025-04-15`, `2026-01-02`, `2026-03-30`, `2026-03-31`, `2026-04-01`, `2026-07-01`, `2026-07-23`, `2026-08-01`, `2026-08-03`, `2026-08-05`, `2026-08-10`, `2026-08-11` — navigate to `http://localhost:3255/?asof=<date>` and wait for load.
2. For each date, also run `curl -s -o /dev/null -w "%{http_code}" "http://localhost:8255/api/compass?as_of=<date>"`.

**Expected Result:**
- None of the 21 page loads shows the "Something went wrong on this page" card.
- Every one of the 21 curl calls returns `200`.

---

### UT-09 — J-14: the full "Not priority" list is visible on the frontier date, not cropped (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` → Next-session focus card

**Preconditions:**
- `2026-08-12` is the frontier manifest (v10) with the full why-not detail.

**Steps:**
1. Navigate to `http://localhost:3255/?asof=2026-08-12`
2. Click the "Not priority (20 shown of 52 held back — 27 cap-excluded, 25 below-floor near-miss)" summary to expand it.
3. Scroll down through the expanded list until the last (20th) entry is visible — do not stop at entry #20 without confirming it is actually the last one.
4. Take a full-page screenshot (or full-element screenshot of the expanded list) covering every visible entry.

**Expected Result:**
- The screenshot shows at least one entry whose text includes a "— ranked #N of the above-floor names, cap 20" lead-in (a cap-excluded name, with its rank and the cap value both legible).
- The screenshot shows at least one entry with no such lead-in but with a `failed_conditions` line naming a floor/distance value (a below-floor near-miss name).
- Neither name is cropped or cut off at the bottom edge of the captured image.

---

### UT-10 — "Not priority" detail is reachable with zero extra navigation from the home page (UX)

**Type:** ux
**Priority:** P2
**Surface:** `/` → Next-session focus card

**Steps:**
1. Navigate to `http://localhost:3255/` (home / latest date).
2. Without clicking any sidebar link, scroll down to the "Next-session focus" card.
3. Locate the "Not priority (...)" disclosure line.

**Expected Result:**
- The "Not priority (...)" text is visible on the home page itself with zero additional navigation (0 clicks from home to find it — only scrolling).
- Clicking it expands the list in place (no page navigation, no new tab).

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Today page loads at latest date | smoke | P1 | `/` |
| UT-02 | Pre-iter-38 date renders + degraded text | happy-path | P1 | `/` focus card |
| UT-03 | Frontier date text unchanged | happy-path | P1 | `/` focus card |
| UT-04 | Backend-unreachable error card | error | P2 | `/` |
| UT-05 | J-04 candidate reasoning click-through | regression | P1 | `/` focus card |
| UT-06 | J-05/J-06 manifest immutability | regression | P1 | `/` manifest strip |
| UT-07 | J-07 ten-second read + market link | regression | P1 | `/`, `/market` |
| UT-08 | 21-date crash-free loop | regression | P1 | `/` |
| UT-09 | J-14 full why-not list, not cropped | happy-path | P1 | `/` focus card |
| UT-10 | Zero-extra-nav discoverability | ux | P2 | `/` focus card |

**P1 tests must all pass for browser QA verdict to be PASS.**
