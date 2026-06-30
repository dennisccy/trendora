# Phase goal-mcp-loop-iter-3 — Implementation Summary

**Phase:** goal-mcp-loop-iter-3
**Date:** 2026-06-30
**Written by:** developer

---

## Features Implemented

This was a **verification iteration**, not a feature iteration. Nothing new was added to the product
itself. The work made the automated **browser test lane** reliable so it can prove — with a real
browser and real screenshots — that the evidence layer shipped in earlier iterations actually works
for a user.

- **Reliable QA browser start-up**: The script that launches the website for automated testing now
  serves a **pre-built, finished copy** of the site (fast and consistent) instead of compiling pages
  on demand the first time each one is opened. This removes the start-up flakiness that twice caused
  the browser tests to be skipped without verifying anything.

---

## Changed Behavior

- **How the website is started during automated QA**: Previously the QA harness started the site in
  "development" mode, which compiles each page the first time it is visited and runs a heavier set of
  background processes. Now QA starts the site in "production serve" mode from a build prepared in
  advance, so every page is ready instantly and the test tool never catches a half-loaded page.
  *This only affects the automated test start-up — it does not change anything a real user sees, and
  the developer hot-reload workflow (`scripts/dev.sh`) is unchanged.*

- **What the user can now see proven in the browser** (already built before, now demonstrated end-to-end):
  - The Stocks leaderboard shows a green **"Proven"** badge on the Leadership score for all ~120 rows.
  - Entry Quality and Risk honestly show **"Not yet proven"**.
  - Opening a stock and clicking **"Why proven?"** reveals the supporting evidence: an out-of-sample
    **PASS**, a **+6.36%** edge, a very small p-value (~0.0005), a sample of **12,297**, a comparison
    **vs SPY**, and the certified-claim id and registration date.
  - The **Evidence** page lists that certified claim and links back to the Stocks leaderboard.
  - All displayed numbers match the backend exactly (not just "the page rendered").

---

## Backend-Only Items

- None. No backend code was changed. The evidence data the page reads was already complete and correct.

---

## Incomplete Items

- **J-04 (regime-conditioned evidence)** — intentionally **deferred** (out of scope this iteration).
  There is no regime-scoped certified claim yet, so there is nothing "proven" to show for it. It is the
  remaining journey before the overall goal can be declared achieved.

---

## Config and Environment Changes

- **No new environment variables or settings for operators.** Internally, the QA start script writes a
  small marker file (`apps/frontend/.next/.qa-serve-base`) recording which backend address the prepared
  build was made for, so it knows when it must rebuild. This is automatic and needs no operator action.
- The QA frontend is still reached at `http://localhost:3255` and the backend at `http://localhost:8255`
  (unchanged).

---

## Known Limitations

- **The original failure could not be reproduced on demand.** When started cleanly, both the website and
  the backend come up quickly and correctly (the backend answers in well under a second; the website is
  ready in about a quarter-second). The earlier test-lane failures appeared only under the heavier load
  of the full automated pipeline. The fix therefore removes the *category* of start-up flakiness rather
  than patching a single reproducible bug.

- **Test-runner quirk in this environment.** The frontend's small unit tests are written to run with a
  Node command that, on this machine's Node build, lacks TypeScript support. They were run instead by
  compiling with the project's own TypeScript compiler — all 21 frontend checks pass. A QA run that uses
  the exact documented command may need the same compile-first fallback.

- **A finished build must exist before the fast start.** The start script builds one automatically if it
  is missing (about 18 seconds, within the test budget). The developer prepared this build in advance so
  the immediate test run starts instantly.

---

## Bottom line for operators

No product behavior changed for end users. The change makes the automated browser tests dependable, and
the developer has already confirmed in a real browser that the "Proven / Not yet proven" badges, the
"Why proven?" proof drill-down, and the Evidence ledger all render with correct, backend-matching numbers.
The remaining work toward the overall goal is the regime-conditioned evidence journey (J-04).
