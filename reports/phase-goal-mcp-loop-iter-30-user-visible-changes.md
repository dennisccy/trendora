# Phase goal-mcp-loop-iter-30 — User-Visible Changes

**Phase:** goal-mcp-loop-iter-30
**Date:** 2026-07-13
**Written by:** ui-impact-analyst

---

## Summary

This iteration ships J-18 / backlog B-901 — the pre-registration registry — as a genuine full-stack
change: one new page, one hub-page update, one new backend endpoint the new page consumes, and one
backend-only governance mechanism (a certification gate check) with no browser-facing counterpart at all.
Nothing about any *existing* page, component, or displayed value changed: the evidence ledger, referee,
and both ledger files are all asserted byte-identical before/after (dev handoff + `test_evidence.py`'s
frozen-golden test, 14/14 passing).

---

## What Users Can Now Do

- Browse the complete pre-registration registry at `/research/registry` — a table listing every hypothesis
  the system has ever registered or tested (11 rows today), each showing its exact selectors, economic
  rationale, registration date, source/provenance, and status.
- Discover the registry from the Research hub: open `/research`, scroll to a new "Governance & process"
  section below the existing ten-lab grid, and click the "Pre-registration registry" card — one click from
  the hub (≤2 clicks from anywhere the hub itself is reachable).
- See at a glance which registry rows are historical backfills versus freshly registered: every backfilled
  row carries a small "backfill" pill next to its status badge (currently all 11 rows, since the registry
  was constructed entirely by backfilling the two evidence ledgers plus the proposer-guidance candidate
  list).
- Read each row's selectors as compact, readable `key=value` chips instead of raw JSON — e.g. a factor row
  shows chips like `kind=factor`, `factor=vcp_contraction`, `decile=10`, `horizon=60`, `direction=positive`;
  a combination row's multi-leg `condition` array renders as one chip with legs joined by `+` (e.g.
  `condition=rs_spy_3m:top:quintile+atr_pct:bottom:tertile`).

## What Changed in the Visible UI

- **`/research` (Research hub):** a new "Governance & process" heading and a single card ("Pre-registration
  registry", with a book icon and a one-line description ending "The gate refuses to certify anything that
  isn't here") now appear below the existing 10-lab grid. The existing ten lab cards and their reading
  order are completely unchanged — the new section lives separately, not as an 11th lab entry.
- **New page `/research/registry`:** a "Back to Research" link with a back-arrow icon, a page title
  ("Pre-registration registry") and subtitle explaining the gate, then a table with five columns: Selectors,
  Rationale, Registered, Source, Status.
- **Status column styling:** status renders as a neutral/muted-gray badge (values seen today: "tested" or
  "closed") — deliberately NOT the green/red PASS-FAIL coloring `/evidence` uses, so this column is never
  mistaken for a proven/not-proven signal.
- **Three explicit fetch states** on the new page: a pulsing loading skeleton (8 placeholder rows), a
  contained "Backend unavailable" error card if the API call fails, and a "No registrations yet" empty-state
  card if the registry file is ever absent or empty (not expected today, but the page will show this
  instead of crashing).

## What Old Behavior Changed

None. No existing page, component, form, or displayed value behaves differently after this iteration:

- The Evidence page (`/evidence`), the Dashboard, `/stocks`, `/stocks/{ticker}`, and every existing
  Research lab render exactly as before — none of their source files were touched.
- `GET /api/evidence` and both evidence ledger files (`certified-claims.jsonl`, `staging-ledger.jsonl`) are
  asserted byte-identical before and after this iteration (dev handoff's live smoke test + the frozen-golden
  `test_evidence.py` suite, 14/14 passing).
- The existing `RESEARCH_LABS` array that drives the ten lab cards on `/research` is untouched; no lab was
  added, removed, reordered, or renamed.

## Not Visible Yet

- **The certification gate's enforcement has no UI and never will, by design.** Starting this iteration,
  `project-extensions/gates/verify_claim.py` refuses to certify any future Evidence Claim whose exact
  selectors don't match a row in the registry — but this check runs only inside the automated goal-mode
  development pipeline (a backend/CLI script invoked between iterations), never inside anything a browser
  user touches. No page, button, or API response exposes this check running or its outcome; a future
  blocked claim would surface only in that later iteration's own dev/review artifacts, not anywhere in the
  product UI. Today it blocks nothing (no current or near-term iteration submits an Evidence Claim), so
  there is nothing to observe even indirectly yet.
- **The `evidence.registry.enforce` config flag** that turns the above check on (now `true` in
  `config.yaml`, flipped only after the backfill was verified complete) is likewise backend/pipeline-only —
  no page reads or displays this flag's value.
- **The registry is read-only by design.** There is intentionally no UI to add, edit, or delete a
  registration — new rows can only be appended by the gate/tooling. If a user expects a "register new
  hypothesis" form, none exists (matches the plan's explicit scope boundary against workflow-engine
  creep).
