# Phase goal-ops-hardening-iter-27 — UX Regression Review

**Date:** 2026-07-27

**Verdict:** UX-REGRESSION-WARN

---

## Summary

This is a hardening-only iteration (no new page/route/nav) closing two ESCALATE-flagged anti-goal
findings: an unhandled `IntegrityError` under concurrent `/backtest` races (AG-8, J-07/J-08), and the
`/data` Coverage panel silently showing an all-zero empty state for a populated database (AG-3, J-05).
The one piece of new UI — a `CoveragePanel` "stale" notice — is well-scoped, visually consistent, and
already 1 click from home. The WARN comes from two things: (1) the browser-QA agent that was supposed to
independently verify J-05/J-07/J-08 (the exact journeys this iteration targets) was killed by an account
quota before writing anything for them, leaving only developer self-verification as evidence; (2) the
deterministic replay's one FAIL (J-06, unrelated on its face to this iteration's diff) traces — on my own
investigation below — to a shared, cross-session test artifact rather than to anything this iteration
shipped, but I could not get live confirmation because both services were down when I checked.

---

## New Capability Discoverability

There is no new interactive capability this iteration (spec and both dev handoffs are explicit: "New user
actions: None"). The one new thing users can perceive is a passive disclosure:

- **`/data` Coverage panel "stale" notice.** Already 1 click from the home page via the persistent left
  sidebar's "Data Manager" link (confirmed directly in `reports/qa/goal-ops-hardening-iter-27-evidence/J-06-verify.png`,
  which shows the sidebar with `Data Manager` as the last item). No new nav entry was added, and none was
  needed — this is an enhancement of a panel already on an existing, discoverable page, not a new
  capability requiring its own entry point. I read the actual implementation
  (`apps/frontend/app/data/page.tsx:752-833`, function `CoveragePanel`) and confirmed the notice renders
  unconditionally whenever `coverage_status === "stale"`, directly below the panel title, with no user
  action required to reveal it — this is the correct discoverability shape for an honesty fix (nothing to
  "find," it just tells the truth when the condition occurs).
- **Backtest concurrency fix.** Correctly has zero UI surface (confirmed in the ui-surface-map: "reliability
  fix, no new visible element"). There is nothing to discover because the fix's entire purpose is the
  *absence* of a crash under a specific race — appropriately not surfaced as a new element.

No hidden or undiscoverable capabilities found.

### Visual consistency

I read the new notice's classes directly: `border-b border-border bg-surface-2 px-4 py-2 text-xs
text-text-muted` (`page.tsx:761`). This exactly matches the muted/informational-note pattern already used
elsewhere in the SAME file (e.g. `macro-default-off-note` at `page.tsx:708`, and other `border-border
bg-surface-2 ... text-text-muted` blocks at lines 659/1327/1334/1341) — no arbitrary values introduced. It
deliberately does NOT reuse the `border-warn`/`text-warn`/`bg-surface-2` alarm treatment the same file uses
elsewhere for genuine warnings (e.g. the `gap_count > 0` case, and the cache-absent banner at line ~994),
which matches the spec's explicit requirement that this is "a routine, expected state, not an error." The
cropped live screenshot (`runs/goal-ops-hardening-iter-27/coverage-stale-label-only.png`) confirms the
rendered text and tone match the spec's exact wording. This is a well-executed, design-system-conformant
change.

---

## Regression Risk

| Shared component | Prior feature it serves | This iteration's change | Risk |
|---|---|---|---|
| `apps/frontend/app/data/page.tsx` — `CoveragePanel` (line 752) | J-05 (Data Manager coverage panel) | +15 lines, one new conditional notice block, no change to the existing metric grid or the other states | Low — I read the diff region directly; it is isolated to the `CoveragePanel` function body, additive only |
| Same file — `LastOutcomeSummary` (line 3587) | J-09 (background-compute badge, refactored last iteration) | Not touched this iteration (confirmed by line-range read; the two functions are ~2,800 lines apart in this 3,676-line file) | Low — and J-09 in fact PASSED in this iteration's replay |
| `apps/backend/app/engine/forward_testing.py` — `_insert_run_forward_returns` | J-07 (background aggregate compute never takes the service down), J-08 (backtest evidence serving) | The binding freeze was deliberately lifted for this ONE function; dev handoff traces the happy-path body as byte-identical (same operations/order/values, only a `try/except` + bookkeeping wrapper added) and provides a live two-request race reproduction showing HTTP 200 on both, zero new ASGI exceptions, and a normal evidence page render | Medium — the code-level reasoning and the developer's own live repro are sound, but this is exactly the module a prior iteration's own QA caught a live 500 in, and **no independent browser-QA verification of J-07/J-08 exists this iteration** (see gap below) |
| `apps/backend/app/engine/data_manager.py` — `coverage_from_storage` | J-05 | New fallback branch added after the two existing (unchanged) lookups; 4 pre-existing tests updated only to account for 3 additive new fields (assertions unwrapped via a strip helper, not weakened) | Low-Medium — same evidence-gap caveat as above applies to J-05 specifically |

### The evidence gap that matters most

J-05, J-07, and J-08 are literally the three journeys this iteration exists to fix (per the phase spec's
own Definition of Done: "J-05, J-07, J-08 pass via browser-qa-agent, re-verified with both fixes in
place"). The merged `ui-test-results.md` has **zero rows for any of them** — the browser-QA agent was
killed by a quota before writing anything beyond the deterministic replay lane (J-01/J-03/J-04/J-06/J-09).
What stands in for QA evidence is the developer's own live verification (a real concurrent-curl race
reproduction + a real browser screenshot of the stale label, both documented in
`docs/handoffs/goal-ops-hardening-iter-27-dev.md`) — useful corroborating evidence, but not the independent
adjudication the pipeline's own Definition of Done calls for. I am not treating this as a confirmed
regression (the developer's evidence is concrete and specific, not a vague "should be fine"), but the gap
itself is real and should not be silently closed out as if browser-QA had run.

### J-06 "DEGRADED" FAIL — investigated, most likely environmental, not fully closed

J-06 step 1 (`goto /`, expect text `"DEGRADED"`) failed in both the LLM-lane's abbreviated pass and the
deterministic replay — actual: no "DEGRADED" text on the home page. This assertion is about the
layout-level `PreflightBanner` (`apps/frontend/components/preflight-banner.tsx`), which reads a composite
GO/DEGRADED/NO-GO verdict from `compute_preflight` (`apps/backend/app/engine/readiness.py`) — a function
this iteration's diff never touches (only `forward_testing.py` and `data_manager.py` were changed). I
traced the actual evidence:

- The screenshot `reports/qa/goal-ops-hardening-iter-27-evidence/J-06-verify.png` shows a healthy, fully
  rendered dashboard — sidebar, regime/phase cards, chart, all present — with the banner reading **"GO —
  today's board is current."** and badges "Ready" / "provider: seed". This is not a blank, frozen, or
  broken frame; the page works, the banner just carries a different (and less alarming) verdict than the
  golden script expects.
- `compute_preflight`'s `drift` component reads a single shared artifact,
  `runs/goal-session-mcp-loop/state/drift-report.json`, whose path is set in the single project-wide
  `config.yaml` (`readiness.drift.report_path`) — i.e. it is not scoped per goal-mode session. `git log
  --follow` on that file shows it toggling between `"status": "clean"` and `"status": "drift"` across many
  past commits attributed to the `ops-hardening` session itself (iters 2, 4, 8, 9, 16, etc.), and `git
  diff HEAD` shows it is **currently modified in the working tree** (uncommitted), changed from the last
  committed `"status": "drift"` state to `"status": "clean"` — evidence that something (very plausibly a
  concurrent goal-mode session on this shared host — several other sessions' iter-26/27 handoffs exist
  with very recent timestamps) is actively mutating this shared file right now, for reasons unrelated to
  this iteration's own diff.
- This iteration's spec explicitly forbids any ingest/fetch (AG-9, offline-deterministic), so iter-27's own
  work cannot be what regenerated the drift artifact.

Taken together, this is best explained as cross-session contamination of a shared, unscoped test fixture,
not a UI regression this iteration introduced. However, I was **not able to independently confirm this
live**: both backend (`:8255`) and frontend (`:3255`) were down when I checked (`curl` connection-refused
on both), so I could not re-poll `/api/health` myself to see the current `preflight.verdict` or check
whether the state is still in flux. I am reporting this as a well-evidenced but not fully closed-out
finding, per the coordinator's framing — not as a confirmed pass or fail.

---

## UI vs Backend Parity

- All three new backend fields (`coverage_status`, `stale_dataset_version`, `stale_computed_at`) are
  consumed by the frontend — I confirmed this directly in `apps/frontend/lib/api.ts` (interface fields
  added) and `apps/frontend/app/data/page.tsx:759-766` (the conditional render keyed on
  `coverage_status === "stale"`). `implementation-summary.md`'s "Backend-Only Items: None" and
  `user-visible-changes.md`'s "Not Visible Yet: None" both check out against the actual code.
- The backtest concurrency fix has no UI-facing value to surface (it is a pure reliability fix) — the
  ui-surface-map and implementation-summary correctly agree there is nothing to expose.
- No parity gap found.

---

## Flags

### Hidden Capabilities
- None.

### Undiscoverable Capabilities
- None.

### Potential Regressions
- **`app.engine.forward_testing._insert_run_forward_returns`** (serves J-07/J-08): freeze deliberately
  lifted for a narrowly-scoped, well-reasoned fix; code-level risk assessed Low-Medium, but **unverified by
  independent browser-QA this iteration** — only developer self-verification exists. Recommend re-running
  browser-QA for J-07/J-08 before treating this finding as fully closed.
- **`app.engine.data_manager.coverage_from_storage`** (serves J-05): same caveat — the code change and the
  developer's own screenshot are convincing, but the pipeline's own Definition of Done calls for
  browser-qa-agent verification that did not happen this iteration.
- **Shared, unscoped `runs/goal-session-mcp-loop/state/drift-report.json`** feeding the layout-level
  `PreflightBanner` shown on every page (including "/"): demonstrated (via `git log --follow` /
  `git diff`) to be mutated by more than one goal-mode session's activity on this host, causing the
  GO/DEGRADED/NO-GO text a golden script expects to change for reasons entirely outside any one session's
  own iteration diff. Not a UX regression from this iteration's shipped code, but a real fragility in how
  J-06's golden assertion is scoped — flagging for awareness since it will keep producing
  UNADJUDICATED-looking FAILs like this one across sessions.

### Visual Consistency
- The new "stale" notice matches the established DESIGN SYSTEM tokens and this page's own existing muted-
  note convention exactly (`border-border`/`bg-surface-2`/`text-text-muted`); it correctly avoids the
  `border-warn`/`text-warn` alarm treatment reserved for real warnings elsewhere in the same file. No
  arbitrary values found. Consistent with prior-phase visual style.

---

## Recommendation

1. Treat J-05/J-07/J-08 as **not yet independently QA-verified** for this iteration — the developer's live
   reproduction is good corroborating evidence but should not be read as equivalent to a completed
   browser-qa-agent pass. Re-run browser-QA for these three journeys before final close-out.
2. Do not score the J-06 "DEGRADED" FAIL as a confirmed regression from this iteration's diff — the
   evidence (screenshot shows a healthy page; the diff never touches readiness/drift code; the shared
   drift-report artifact is independently shown to be in flux from cross-session activity) points away
   from it. But do not score it as benign either, since live re-confirmation was not possible at review
   time (both services were down).
3. Non-blocking, longer-term: consider scoping `readiness.drift.report_path` (and any other shared
   test-state artifact under `runs/goal-session-<other-session>/...`) per goal-mode session, so one
   session's fetch/drift activity cannot flip another session's golden-script assertions.
