# Phase goal-mcp-loop-iter-21 — UX Regression Review

**Date:** 2026-07-08

**Verdict:** UX-REGRESSION-WARN

---

## Headline finding (read this first)

This is a verification-only iteration (confirmed zero-diff on all 5 J-13 files, independently by
dev, reviewer, and QA). Its actual target, **J-13, is spotless**: every DoD-named criterion
(job-kind picker, two-group legend, exact colors, distinguishing hover/tooltip) passed live against
real running services with computed-style precision, and I independently cross-checked the
CSS-variable values the browser-qa-agent read live (`--heat-0..5`, `--snapshot`) against the current
`apps/frontend/app/globals.css` source — they match exactly (`#39516f`→`#a6c8f2`, `#a78bfa`), which
rules out a repeat of iter-20's stale-`.next`-bundle problem (the single biggest risk this iteration
existed to retire). I also spot-checked the smallest evidence PNG (UT-12, 2988 bytes) and the UT-21
screenshot directly — both are valid, non-blank, on-topic captures, and all 12 evidence files have
distinct md5s (no reused/relabeled frame).

However, the canonical browser-qa-agent's **overall verdict for this iteration is FAIL** (2/22, one
P1: UT-16, UT-21), and one of those two — **UT-21 / J-12**, a required-still-passing
regression-replay journey this iteration exists specifically to close — deserves a more precise
root-cause than the browser-qa-agent's own conclusion. I independently read the backend and frontend
source and found that `/methodology`'s "Universe Selection" section is **not** a stale test-plan
reference to content that never existed (as `ui-test-results.md` concludes); it is a real, fully
wired component (`UniverseSelectionCard`, `apps/frontend/app/methodology/page.tsx:237-289`,
`data-testid="universe-selection"`) that is **deliberately suppressed** by an honesty gate
(`apps/backend/app/api/methodology.py:31-36`, "J-22") until a committed universe-screen record
(`apps/backend/data/seed/universe.json`) exists — and that file is confirmed absent from this repo
right now (only `universe_pool.csv` is present). This is correct, intentional, anti-fabrication
behavior — not a bug, and not caused by any file iter-20 or iter-21 touched (`methodology.py` /
`methodology/page.tsx` are outside both iterations' diffs) — but it does mean the **J-12 replay gap
iter-20 left open is not actually closed** by this iteration, just better diagnosed. The underlying
substantive claim J-12 cares about (universe count consistency) is independently verifiable and
holds via `/data` ("Universe (as of date): 541") vs. `/stocks` ("541/541") — confirmed live in
`ui-test-results.md` — just not through the specific page (`/methodology`) the test names. This
combination (J-13 clean; one required-replay journey's literal check un-closeable in this
environment, for a legitimate but currently-live reason) is why I land on **WARN, not PASS**: there
is a real, currently-live parity gap worth recording precisely, even though it is not a regression
and not blocking.

---

## New Capability Discoverability

No new capability ships this iteration (verification-only, zero diff — per the plan's UI Evolution
note, this section re-confirms iter-20's already-shipped J-13 surfaces, now with fresh live evidence
rather than carried-forward reasoning):

| Capability (shipped iter-20) | Navigation path | Discoverability | Evidence this iteration |
|---|---|---|---|
| Widened Fetch scope (~548-pool ∪ context, ~588 symbols) | None needed — surfaces automatically through the existing, unmodified "Symbols fetched X/Y" counter on the same "Start" button users already knew | N/A by design — correctly automatic, not hidden | UT-03/UT-05: live-confirmed "Symbols fetched 588/588" |
| Two-group availability legend ("Price data — cell fill" / "Scored snapshot — indicator") | Sidebar → Data Manager (1 click from Dashboard) → same "Per-date availability" card, same position as before | 1 click, unchanged position | UT-22: sidebar link visible without scroll at 1440×900, 1 click reaches `/data`, active state confirmed; UT-10: both legend rows read live at distinct, non-overlapping y-positions |
| Hover tooltip naming Fetch/Backfill per cell | Same calendar cell, no new control | Immediate on hover, no discovery burden | UT-13/UT-14: live `title`/`aria-label` reads match spec exactly, two distinct hover states confirmed with md5-distinct screenshots |
| "Expand universe" removal | N/A — a removal, not a capability to discover | Confirmed absent | UT-02/06/07: live DOM shows exactly 3 job-kind options, no ineligibility copy/alert under any of 10 combinations tested |

Labels are non-technical and match what the feature does: the panel title reads exactly "Start a
fetch / backfill job" and the explainer paragraph states Fetch "covers the full committed symbol
pool" (UT-08, live, exact match); the heatmap header blurb and caption explicitly name
Fetch→fills / Backfill→scores (UT-15, live, exact match). No label confusion found.

## Regression Risk

**This iteration's own footprint:** zero. `git diff HEAD` on all 5 J-13 files is empty, confirmed
independently by the developer, the reviewer, and QA; I did not find any additional file touched.
Since no source changed, this iteration cannot itself have introduced a regression in any shared
component — there is nothing new to assess a blast radius for.

**Required-still-passing journeys — the live replay this iteration exists to produce (iter-20
blanket-SKIPped all of these):**

| Journey | Test | Result | Notes |
|---|---|---|---|
| J-01 `/stocks` Sector sort | UT-17 | **PASS**, live | Two real clicks re-ordered 541 rows, sort icon + `aria-label` flipped both times, sidebar stayed mounted. Closes iter-20's gap cleanly. |
| J-03 "Not yet proven" badges | UT-18 | **PASS**, live | First 5 rows each show exactly 3× "Not yet proven", 0 occurrences of bare "Proven"/"PASS". Closes iter-20's gap cleanly. |
| J-05 `/evidence` ledger | UT-19 | **PASS**, live | Heading + claim-row list rendered, all-FAIL ledger (consistent with an untouched, all-FAIL ledger this iteration). Closes iter-20's gap cleanly. |
| J-10 `/stocks/{ticker}` deep history | UT-20 | **PASS**, live (with note) | 1255→3025 bars on toggle, both directions, no error. Minor test-wording note: the "history since" clause is a static per-ticker fact that doesn't itself change between Recent/Full — narrower than the test's literal wording, but the substantive regression check (wider range, no crash, clean restore) holds. Closes iter-20's gap. |
| J-12 universe-count consistency | UT-21 | **FAIL** (literal), **not a regression** (see Headline finding) | `/methodology` has no live "Universe Selection" section right now — correctly suppressed pending an offline screen commit, unrelated to any iter-20/21 change. Underlying consistency claim independently verified via `/data` (541) vs `/stocks` (541/541), which does match. Gap not fully closed as literally specified. |

**Shared-surface re-confirmation (carried from iter-20's own analysis, re-verified live where
possible this iteration):**
- `app/data/page.tsx` (Expand removal) — the J-37 gap-pull panel and Rebuild panel sit in untouched
  regions; live-confirmed the 3 surviving job kinds (Backfill/Fetch/Fetch+backfill) all still start
  and run correctly (UT-04/UT-03/UT-05), including a real completed Fetch+backfill run with no
  "Universe screen" block. Low risk, live-confirmed clean.
- `globals.css` / `tailwind.config.ts` design tokens — `grep` confirms `--heat-*`/`--snapshot` have
  no other consumer than `availability-heatmap.tsx`; `--pos`/`--neg`/`--warn` (used elsewhere, e.g.
  `/stocks` gain/loss coloring) are untouched. Low risk.
- Sidebar / layout / router — `git diff HEAD --stat` on `sidebar.tsx`/`layout.tsx` is empty; last
  actual edit to `sidebar.tsx` was iteration 1 of this session. All 11 routes remain reachable
  exactly as before. No risk.
- Anti-goal-8 honest-degrade path (UT-16) — **FAIL against literal expected text**, but I
  independently confirmed via source (`apps/frontend/app/data/page.tsx:412-414`,
  `components/availability-heatmap.tsx:225`) that `/data` has a coarser, page-level "Backend
  unavailable / Dataset coverage could not load..." gate that wraps the entire page body (job form +
  availability heatmap both fail to mount together), and this exact pattern
  (`<p className="font-medium">Backend unavailable</p>`) is used consistently across roughly 15 other
  pages in the app (stocks, evidence, methodology, sectors, scanner-runs, watchlist, backtest,
  research, themes, dashboard — confirmed via grep). This is a longstanding, deliberate, app-wide
  pattern, not something iter-20 or iter-21 introduced (`page.tsx` is zero-diff this iteration). The
  anti-goal's actual wording ("contained error boundary, honest placeholder, never a blank
  application-error page") is satisfied by this coarser gate — no crash, no fabrication, nav stayed
  usable. This reads as a test-wording granularity mismatch (the test names a narrower failure mode
  than the tooling could isolate — the browser-qa-agent itself flagged it lacks a
  request-interception primitive), not a regression. I agree with the browser-qa-agent's own
  self-assessment here.

## UI vs Backend Parity

| Backend capability | UI exposure | Assessment |
|---|---|---|
| Fetch job → `price_load_symbols` (548-pool ∪ context) | Automatic, via existing counter | Fully surfaced, live-confirmed 588/588 |
| `compute_availability` / `GET /api/data/availability` | Unchanged endpoint, re-encoded presentation | Byte-identical (test-enforced); live tooltip text quotes the exact same underlying figures |
| `kind:"expand"` job + `get_market_caps` | Not exposed in UI (by design) | Disclosed in `user-visible-changes.md`'s "Not Visible Yet"; acceptable per this phase's explicit scope, live-reconfirmed the "Candidate universe" tile reads "static" with no refresh claim |
| **`_universe_selection()` / `/methodology`'s "Universe Selection" section (J-22)** | **Coded, wired, 1-click reachable (`/methodology`) — but its content does not render in this running instance** | **New finding, not disclosed in `user-visible-changes.md`.** `GET /api/methodology` omits `universe_selection` whenever `apps/backend/data/seed/universe.json` (the committed offline screen record) is absent — confirmed absent right now. This is a deliberate, well-documented anti-fabrication gate ("the catalog's `universe_selection` section asserts the universe is a REPRODUCIBLE SCREEN RESULT... that claim is only true once the offline screen has actually run and committed its record... So the section is served ONLY when the committed screen record exists" — `apps/backend/app/api/methodology.py:8-14`), analogous in spirit to the "Not yet proven" score badges elsewhere. Not a defect, not caused by iter-20/21 (neither touches this file), but it is a real, currently-live gap: the IA surface `/methodology`'s Universe Selection block is inert for every user of this deployment until an operator runs `scripts/screen_universe.py` offline. |

This last row is why Step 3 of my process ("are any backend capabilities described as complete but
listed as not visible yet") surfaces a genuine, if narrow, gap: this capability isn't "complete but
undisclosed" in the sense of a defect — it is working as designed — but it also was not captured
anywhere in this iteration's (or, apparently, any prior iteration's) "Not Visible Yet" disclosures,
and a real user cannot currently see it. It was found only because this iteration's required
regression replay forced a live click-through of `/methodology` that iter-20's blanket SKIP never
reached.

## Flags

### Hidden Capabilities

- **(Informational, pre-existing, not caused by iter-20/21):** `/methodology`'s "Universe Selection"
  section (`UniverseSelectionCard`) is fully coded and reachable via the normal 1-click nav path
  (sidebar → Methodology), but renders nothing because its backing API field is suppressed pending an
  offline screen-record commit that has never happened in this repo (`apps/backend/data/seed/universe.json`
  is absent). This is the correct, intentional behavior of an anti-fabrication gate, not a bug — but
  it functions as a hidden capability for every current user of this environment. No action is owed
  by this iteration (out of scope, unrelated files); flagging for visibility per Step 3 of my
  process and for the auditor's awareness.

### Undiscoverable Capabilities

- None. All J-13 surfaces are exactly where they were before, live-reconfirmed in one click from
  Dashboard (UT-22).

### Potential Regressions

- **None caused by this iteration.** `git diff HEAD` is empty on every J-13 file; no shared component
  was touched, so there is no blast radius to assess for iter-21 itself.
- **UT-21 / J-12 (required-still-passing replay) did not close cleanly** — FAILED against its literal
  wording during live replay. Root cause (independently verified via source, more precise than
  `ui-test-results.md`'s own "stale test-plan reference" theory): a pre-existing, correctly-functioning
  honesty gate on `/methodology` (see UI vs Backend Parity), wholly unrelated to any file either
  iter-20 or iter-21 touched. **Not a regression** — nothing that used to work now fails; the
  section has presumably never rendered in this environment, gated by an environment/seed-data
  precondition rather than a code change. The underlying substantive claim (cross-page universe-count
  consistency) is independently verifiable and holds via `/data` (541) vs. `/stocks` (541/541). See
  Recommendation for how the test plan should account for this state.
- **UT-16 FAILED against its literal expected text** but not against the anti-goal-8 requirement
  itself (see Regression Risk above) — a test-wording granularity mismatch against a longstanding,
  consistently-applied, compliant degrade pattern, not a regression.

### Visual Consistency

- Consistent with the DESIGN SYSTEM: every color used is a CSS custom property in `globals.css`,
  registered in `tailwind.config.ts`; zero inline hex in either changed component (re-confirmed,
  matching iter-20's own ux-regression finding).
- I independently cross-checked the live computed-style values `ui-test-results.md` reports
  (`--heat-0:#39516f … --heat-5:#a6c8f2`, `--snapshot:#a78bfa`) against the current
  `apps/frontend/app/globals.css` source (lines 29-48) — they match exactly, confirming the live
  instance is serving the current build, not a stale one (the exact failure mode iter-20's
  ux-regression review had to catch and fix manually).
- All 6 density steps are visually and computationally distinct (monotonic brightening); the violet
  snapshot ring shares no hue family with the blue ramp or any other status color. I spot-checked the
  smallest evidence PNG (`UT-12-ring-vs-nonring-cells.png`, 2988 bytes) directly — it is a valid,
  tightly-cropped, non-blank capture showing a clear violet ring on one cell against two plain blue
  neighbors, not a corrupted or placeholder image.
- Dark-theme-only styling preserved; no new component type introduced (existing `Card`/`Select`
  reused, matching every other card on `/data` and consistent with prior-phase pages).
- Screenshot hygiene: all 12 evidence PNGs have distinct md5 hashes (verified directly); none match
  the known ~5855-byte blank-scrolled-viewport-frame signature; `file` confirms all are valid PNG
  image data at sane, non-degenerate dimensions.

## Recommendation

1. **No action required for J-13 itself.** This iteration's actual target is cleanly, live-verified
   PASS on every DoD-named criterion (UT-02/03/04/05, UT-10/11/12, UT-14), with md5-distinct,
   independently-spot-checked screenshot evidence.
2. **File a non-blocking test-plan correction for UT-21/J-12.** Do not simply relabel this "stale
   test-plan reference and drop it" — the `/methodology` Universe Selection section is real and
   correctly implemented, and will start rendering the moment an operator runs
   `scripts/screen_universe.py`. A future test-plan revision should either (a) retarget the
   cross-page consistency check at `/data` ("Universe (as of date)") vs. `/stocks` ("{visible} /
   {total}"), where the claim is actually verifiable in this environment right now, or (b) make the
   `/methodology`-specific check conditional on `apps/backend/data/seed/universe.json` existing, so
   "section correctly absent" is scored as a pass rather than a failure when the screen hasn't run.
3. **File a non-blocking test-plan note for UT-16**, either loosening its expected text to the actual
   (compliant) page-level "Backend unavailable" gate, or adding a request-interception-capable QA
   tool so the narrower "only the availability endpoint fails" scenario can be exercised distinctly
   from "the whole backend is down."
4. **For the auditor/evaluator:** of the 5 required-still-passing replay journeys, 4 (J-01/J-03/J-05/
   J-10) came back cleanly live-verified this iteration, genuinely closing iter-20's gap. J-12 did
   not close as literally specified — not due to a regression, but due to a pre-existing, unrelated,
   correctly-functioning data-availability gate on a different page. Whether to treat J-12 as still
   "passing" (byte-identity carry + the now-precisely-diagnosed non-regression explanation + the
   independently-verified substantive claim holding elsewhere) or to open a narrow follow-up is a
   judgment call outside this review's remit — flagging the precise facts so that call can be made
   deliberately rather than by accepting "stale test reference" at face value.
