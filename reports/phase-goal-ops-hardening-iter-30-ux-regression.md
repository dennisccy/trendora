# Phase goal-ops-hardening-iter-30 — UX Regression Review

**Date:** 2026-07-29

**Verdict:** UX-REGRESSION-FAIL

## Scope note — why this isn't the plain backend-only pass

`Frontend Present: no` is accurate for this iteration's own diff: `plan.md`, `reports/phase-goal-ops-hardening-iter-30-user-visible-changes.md`,
and `reports/phase-goal-ops-hardening-iter-30-ui-surface-map.md` all correctly show zero frontend files
touched, and `compute_forward_aggregates`'s byte-identity is proven by 38 fixture assertions
(`test_compute_forward_aggregates_byte_identical_to_pre_rewrite_reference` + the cross-width test), so the
`/backtest` page this function feeds is unaffected. That part of the boilerplate ("no new UI, nothing to
review") would be correct on its own.

But this iteration's own mandatory regression spot-check (TC-5, a P1 DoD item) — executed live by
browser-qa-agent, `reports/phase-goal-ops-hardening-iter-30-ui-test-results.llm.md` — found that opening
`/research/factor-lab` crashes and **terminates the entire backend process**, not just the one page. That
is a live, user-reachable availability finding squarely inside this reviewer's remit ("look at the product
from a user's perspective... flag when capabilities are... broken"), so I am writing the full report rather
than the short-circuit.

## New Capability Discoverability

None to assess. This iteration ships no new user-facing capability, information, action, or UI surface
(confirmed identically by `plan.md`, `docs/phases/goal-ops-hardening-iter-30.md`'s own "Frontend" /
"New user-facing capability" / "New information displayed" / "New user actions" / "UI surface changes"
sections, and `reports/phase-goal-ops-hardening-iter-30-user-visible-changes.md`). `compute_forward_aggregates`
keeps its exact signature and is proven byte-identical to its pre-chunk output, so there is nothing new for
a user to find.

## Regression Risk

| Prior feature | Shared component | Risk level | Evidence |
|---|---|---|---|
| `/backtest` page ("Backtest evidence serves from storage only" — J-08) | `compute_forward_aggregates` (`forward_testing.py`), consumed via `GET /api/backtest` | **Low** | Byte-identity fixture tests (TC-2: 30 cases across widths/horizons/`as_of`, plus 8 more across chunk widths = 38 total) prove the payload this page renders is unchanged. Deterministic replay `UT-J-08` PASSED (`reports/phase-goal-ops-hardening-iter-30-regression-replay-results.md`). |
| MCP `query_backtest` | same producer | N/A (not a UI surface) | — |
| Ingest finalize warm (background) | same producer | **Resolved this iteration** | Browser-qa-agent's TC-01 live-triggered the real warm path against the full deep basis (3.9M+ `forward_returns` / 781K+ `scanner_results` rows) and found **zero** `MemoryError` lines carrying a `forward_testing.py`/`compute_forward_aggregates`/`stock_obs`/`ret_by_run_symbol` frame, boot banner cited at `logs/backend.log:131633`. This is the one genuine, verified reliability improvement this iteration delivers. |
| `/research/factor-lab` page (Factor Lab, "a nav page two clicks from the dashboard" per iter-29's own audit) | Sibling accumulator shape in `research.py`'s `_all_factor_observations_by_horizon` — **not touched by this iteration's diff** | **Critical — pre-existing, reconfirmed, and apparently worse** | See below. |

### The Factor Lab finding, in detail

This is not a new bug introduced by this iteration's diff — `git diff` for this iteration touches only
`forward_testing.py`/`config.py`/`config.yaml`/tests/`perf-budgets.md`, never `research.py`. But it is a
regression this iteration's own required TC-5 spot-check re-exercised and found **materially worse** than
the last time it was measured:

- **iter-29's audit** (`docs/handoffs/goal-ops-hardening-iter-29-audit.md`, finding B2, CRITICAL) found
  `/research/factor-lab` returning HTTP 500 on every visit (4/4 requests) from a `MemoryError` in
  `_all_factor_observations_by_horizon` — but explicitly recorded **"The process survives** (uvicorn logs
  `Exception in ASGI application`)" and recommended this exact function as "next iteration's scope."
- **This iteration's spec deliberately deferred that recommendation again** (`docs/phases/goal-ops-hardening-iter-30.md`
  Out of Scope: "`research.py`'s `_all_factor_observations_by_horizon`... a separate, already-identified
  redesign; this iteration only regression-spot-checks `/research/factor-lab` still works (TC-5), it does
  not fix that function") — a defensible call under goal.md's rule 5 (never bundle two risky changes), but
  it means the CRITICAL finding from iter-29 shipped into iter-30 unresolved for a second consecutive
  iteration.
- **iter-30's own live TC-5 run** (`reports/phase-goal-ops-hardening-iter-30-ui-test-results.llm.md`) found
  the SAME `MemoryError` (`research.py:583`, `_all_factor_observations_by_horizon` → `pools[h].append(...)`)
  but this time the **entire Uvicorn process shut down** (`logs/backend.log` lines 132303-132305:
  "Waiting for application shutdown." / "Application shutdown complete." / "Finished server process
  [3667601]"; `ss -tlnp` confirmed port 8255 no longer listening). Every single page and journey —
  `/backtest`, `/evidence`, `/data`, this iteration's own target journeys J-06/J-07, and all six
  required-still-passing journeys (J-01, J-03, J-04, J-05, J-08, J-09) — was unreachable for the remainder
  of the QA run. Browser-qa-agent polled `GET /api/health` for 6+ more minutes; it never came back on its
  own within the observation window, and TC-07 (the J-06 deterministic replay, itself a P1 DoD item) had to
  be **SKIPPED** as a direct consequence.
- Browser-qa-agent's own report is appropriately hedged on causation (it does not claim this iteration's
  diff caused the crash, and confirms `research.py` is untouched), but does note the timing: TC-5 ran
  immediately after TC-1's own full-basis forward-aggregate warm, with backend RSS already at ~3.0-3.3 GB
  (down from a historical ~5.5 GB peak, not cold) when the Factor Lab request started, climbing to ~5.8 GB
  before the crash. Whether or not this iteration's own warm contributed to the memory pressure that tipped
  a "survives" 500 into a full process death, the observed behavior is a genuine escalation over the last
  measured baseline (iter-29), on a page reachable in two ordinary clicks from the dashboard.
- Per `docs/phases/goal-ops-hardening-iter-30.md`'s own TC-9 process requirement, the browser-qa report
  cites exact log line numbers throughout (boot banner `logs/backend.log:131633`; traceback
  `132233-132302`; shutdown `132303-132305`) — this citation discipline is followed correctly and is not
  itself a finding.

**Why this belongs in a UX regression review, not just an audit:** a "regression spot-check" whose own
result is "the checked page takes the whole product down" is definitionally the worst possible outcome for
a discoverability/availability review — it is not that a capability is hard to find, it is that finding it
(two clicks from the dashboard, per iter-29's own audit) breaks every other capability for several minutes.

### Reporting-integrity flag (audit contradiction)

`reports/phase-goal-ops-hardening-iter-30-ui-test-results.md` (the merged/"canonical" artifact this
reviewer's own instructions list as a primary input) states **"Browser QA Verdict: PASS... 6/6 journeys
passed (0 skipped)"** and lists only the six required-still-passing regression journeys (J-01/03/04/05/08/09)
from the deterministic replay lane. It does not mention TC-5 at all. The actual browser-qa-agent report,
`reports/phase-goal-ops-hardening-iter-30-ui-test-results.llm.md`, states **"Browser QA Verdict: FAIL...
3/5 tests passed (1 failed, 1 skipped)"** and is where the backend-crashing TC-5 finding and the resulting
TC-7 SKIP live. These are two different test scopes (deterministic replay of required journeys vs. the
live functional-test-plan TC items) merged under the same file-naming convention, but a downstream reader
who consults only the non-`.llm` file — which is the one named in this reviewer's own standard input list
— would see "PASS, 6/6" and never learn the backend fell over. This is worth fixing at the merge-script
level (`merge_ui_test_results.py`) so a P1 FAIL from either source surfaces in the canonical file's headline
verdict, not just in a sibling file an ordinary read wouldn't reach.

## UI vs Backend Parity

No gap. This iteration adds no new backend capability visible to any consumer — `compute_forward_aggregates`
is proven byte-identical pre/post-chunk (TC-2), so there is nothing for the UI to newly surface. The one
externally observable effect, if fully realized, is purely a reliability property (no more `MemoryError` in
this one producer), which is not something a UI element would represent either way.

## Flags

### Hidden Capabilities
None. No new capability shipped this iteration.

### Undiscoverable Capabilities
None. No new capability shipped this iteration.

### Potential Regressions
- **`/research/factor-lab`** (reachable two clicks from the dashboard, per iter-29's own audit) — CRITICAL,
  pre-existing (not caused by this iteration's diff) but reconfirmed live during this iteration's own
  required TC-5 spot-check, and observed this time to crash the **entire backend process** rather than
  survive as a page-level 500 (the behavior iter-29's audit measured five days ago). Every page and journey
  in the product was unreachable for 6+ minutes as a direct consequence, and this iteration's own TC-07
  (J-06 deterministic replay, a P1 DoD item) could not even be attempted because of it. This is the second
  consecutive iteration this exact CRITICAL finding has shipped unresolved despite iter-29's audit
  explicitly recommending it as "next iteration's scope."
- **Reporting-integrity gap**: the canonical `reports/phase-goal-ops-hardening-iter-30-ui-test-results.md`
  reports "PASS, 6/6" and omits the P1 FAIL entirely; only the sibling `.llm.md` file carries it. See
  "Reporting-integrity flag" above.

### Visual Consistency
Not applicable — no UI files were touched this iteration and no new page or component was introduced.

## Recommendation

1. **Do not let this iteration's genuine win (J-07's own `compute_forward_aggregates` fix, which live-verified
   at zero `MemoryError` against the full deep basis) obscure that the product currently has a
   two-clicks-from-dashboard page that can take the entire service down.** This is functionally identical in
   user impact to the exact failure class J-07/AG-8 exist to prevent, just in the sibling function iter-29's
   audit already named (`_all_factor_observations_by_horizon`, `research.py:502-589`). Recommend the next
   iteration take this as its target rather than deferring a third time — the severity trend (survivable 500
   → full process death) argues against further deferral.
2. **Fix `merge_ui_test_results.py` (or the merge step's convention) so a P1 FAIL discovered by
   browser-qa-agent cannot be merged into a canonical report that reads "PASS."** Anyone (including a future
   ux-regression-reviewer or the goal-evaluator) who reads only the non-`.llm` file for this iteration would
   conclude UI regression testing was clean; it was not.
3. Consider, for the eventual Factor Lab fix, whether the product needs some form of backend
   auto-recovery/supervision — a single page load currently has no bounded blast radius short of "the whole
   process dies and stays dead until something external restarts it." That is a separate (infrastructure)
   concern from the `research.py` fix itself, but worth naming since a correct chunking fix removes the
   trigger, not necessarily the exposure to whatever else could someday raise an unhandled `MemoryError` in
   a request thread.
