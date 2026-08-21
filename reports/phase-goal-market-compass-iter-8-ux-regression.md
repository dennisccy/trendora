# Phase goal-market-compass-iter-8 — UX Regression Review

**Date:** 2026-08-21

**Verdict:** UX-REGRESSION-PASS

Backend-only iteration (`Frontend Present: no`). J-10's redesigned per-symbol recovery gate has no
UI surface by design (`docs/goal.md`: "Walkthrough: waived — data-layer repair with no UI surface
change of its own"), and the diff proves it: zero files under `apps/frontend/` touched, zero files
under `apps/backend/app/api/` (route handlers) touched. No new capability needed UI exposure this
iteration, no shared UI component was touched, and the one incidental data-consequence (see UI vs
Backend Parity below) is honestly reported as partial/not-yet everywhere it appears. UI verification
of J-01–J-04 is correctly, unconditionally deferred to iteration 9 / J-11 Stage G — the database is
still 567/587 symbols short for the two incident dates, so a browser check now would test a known,
deliberately-unrepaired state, not a regression.

## New Capability Discoverability

| Capability | Where it lives | UI surface expected? | Assessment |
|---|---|---|---|
| Per-symbol path-agreement + bridge-dispersion gate (`check_adjustment_convention_per_symbol`, `_compute_symbol_verdict`) | `apps/backend/app/engine/j10_recovery.py` | No | Invoked only by a standalone one-time incident-recovery script, never a request path any page calls. Spec explicitly waives J-10's walkthrough. Correctly not surfaced — nothing to discover. |
| Bridge-applying provider wrapper (`_BridgeApplyingProvider`) | same file | No | Internal transform on the insert path only. Correctly not surfaced. |
| Persisted per-pair evidence artifact (`j10-convention-evidence.json`) | `runs/goal-market-compass-iter-8/` | No | Internal orchestration record, never served by any endpoint (spec's own "Data-contract additions: None"). Correctly not surfaced. |

One nuance worth recording precisely, not a discoverability gap: `GET /api/compass?as_of=2026-08-12`
(a pre-existing endpoint the frontend's compass UI already calls, route file untouched this
iteration) now returns HTTP 200 instead of 400, as an incidental consequence of the 40 rows this
iteration restored — not a code change to the endpoint or a new capability. Zero clicks changed,
because nothing in the click path changed. This is **not** a hidden capability worth flagging,
because it is not being held back from users by a missing nav entry — it is correctly held back by
the explicit, spec-mandated J-11 Stage G gate, and every artifact that mentions it (dev handoff Known
Issue #5, `user-visible-changes.md`, `ui-surface-map.md`, `what-to-click.md`) says so plainly rather
than implying readiness.

## Regression Risk

Files changed this iteration (per dev handoff + independently confirmed via `git show --stat` on
commit `47d50d04`): `apps/backend/app/engine/j10_recovery.py`, `apps/backend/app/data_providers/yahoo_provider.py`,
`apps/backend/tests/test_j10_recovery.py`, `apps/backend/tests/test_provider_clients.py`, plus
non-code artifacts (`assumptions.md`, evidence JSON, dev handoff, `status.json`).

Prior UI-building iterations and the frontend files they own (`docs/handoffs/goal-market-compass-iter-{1,2,3}-frontend.md`):

| Prior feature | Files it owns | Touched this iteration? | Risk |
|---|---|---|---|
| iter-1: methodology page `sector_basis` disclosure | `apps/frontend/lib/api.ts`, `apps/frontend/app/methodology/page.tsx` | No | None |
| iter-2: compass dashboard cards | `apps/frontend/components/compass-summary-card.tsx`, `compass-whatchanged-card.tsx`, `compass-focus-section.tsx`, `ui/disclosure.tsx`, `app/page.tsx`, methodology `CompassSelectionCard` | No | None |
| iter-3: manifest strip + confirm modal | `apps/frontend/components/compass-manifest-strip.tsx`, `lib/format-fact.ts`, `app/page.tsx` | No | None |

Intersection between this iteration's diff and any prior UI feature's files: **empty**, confirmed by
direct comparison, not just by the ui-surface-map's assertion.

Backend-side sharing, checked specifically because two of this iteration's files sit on shared
modules:
- `j10_recovery.py` is a standalone module — `grep -rln "j10_recovery" apps/backend/app` returns only
  itself and one docstring cross-reference in `yahoo_provider.py`; no route handler imports it.
- `yahoo_provider.py`'s `make_provider`/`YahooProvider` **is** on the shared live-data path
  (`apps/backend/app/config.py`, `apps/backend/app/engine/data_manager.py` both reference it) — so in
  principle a behavior change here could regress other journeys that fetch live Yahoo data. I checked
  this directly rather than trusting the surface map's "docstring-only" label: `git diff
  46eb7311..47d50d04 -- apps/backend/app/data_providers/yahoo_provider.py` shows the diff is
  literally confined to the module-level docstring's prose — zero lines of executable code changed.
  Risk: **none**.

**Conclusion: no regression risk from component sharing.** The reviewer's independent report
(`reports/reviews/goal-market-compass-iter-8-review.md`) corroborates the same zero-frontend,
zero-config, zero-model finding.

### A note on evidence hygiene, not a regression finding

`reports/phase-goal-market-compass-iter-8-ui-test-results.md` (merged) carries a results table showing
`UT-J-01` and `UT-J-04` both `PASS`, with screenshot evidence — sourced from
`reports/phase-goal-market-compass-iter-8-regression-replay-results.md`. That data is **not
admissible** and I am not treating it as evidence of anything, in either direction:

- `reports/phase-goal-market-compass-iter-8-ui-test-plan.md` (same iteration) explicitly specifies
  **zero** `UT-` test cases, on the grounds that the union of `Target journeys` (J-10, no UI surface)
  and `Required-still-passing journeys` (none, deliberately) with a browser-observable surface is
  empty — and states plainly "Nothing gates a P1 browser-QA verdict this iteration."
- `reports/qa/goal-market-compass-iter-8-qa.md` §5 records browser checks **SKIPPED**, citing the
  same lane gate.
- `reports/qa/goal-market-compass-iter-8-evidence/INVALID-forbidden-lane.md` documents why the PASS
  rows exist anyway: `runs/goal-session-market-compass/iter-8/depth-dispatched` read `lean` instead of
  this spec's own `Depth: full` at developer-dispatch time, and lean depth auto-enables
  `CHAIN_LEAN_PARALLEL_BROWSER_QA`, which launched a deterministic replay against J-01/J-04 the moment
  `developer.done` was stamped — starting a frontend and a second backend, against the database this
  spec (TC-19, Definition of Done, Out of Scope) unconditionally forbids testing this iteration. The
  out-of-band audit (`docs/handoffs/goal-market-compass-iter-8-audit.md`) independently confirmed the
  replay caused no `daily_prices`/manifest/provenance mutation, and returned **ESCALATE** for this and
  a related same-vendor-tautology finding — a process verdict, not a claim that the 40 restored rows
  are unsafe.
- `depth-dispatched` now reads `full` (confirmed by direct read) and the reviewer's report notes it as
  "already remediated," but that correction happened after the forbidden lane had already run once.

Net effect on this report: I make **no claim, positive or negative,** about J-01/J-04's current state
from anything produced this iteration. Had the forbidden lane's rows read FAIL instead of PASS, that
would equally be inadmissible noise from a run against a database 567/587 symbols short of complete —
not a regression signal either. The one thing worth flagging for whoever next regenerates
`ui-test-results.md`: the merged file itself carries the quarantined PASS rows forward with a
`**Browser QA Verdict:** BLOCKED` headline but a `2/2 PASS` table underneath and no inline pointer to
`INVALID-forbidden-lane.md` — a reader who opens only that one file, not the evidence directory, could
walk away thinking J-01/J-04 were cleanly reverified this iteration. They were not. This is a
documentation-propagation gap, not a UX regression, and the audit has already logged the underlying
depth-demotion bug as a framework follow-up — I am not duplicating that escalation, only making sure
this report does not inherit the same misreading.

## UI vs Backend Parity

| Backend capability (this iteration) | Served by an endpoint? | Displayed to a user? | Gap? |
|---|---|---|---|
| Per-symbol convention gate + bridge transform | No | No | No — internal orchestration only, matches spec's explicit "no UI surface" scope. |
| Persisted per-pair evidence JSON | No | No | No — spec's own "Data-contract additions: None" confirmed by ui-impact-analyst. |
| 40 restored `daily_prices` rows (data, not code) | Indirectly, via pre-existing `GET /api/compass` | Not yet, correctly | No gap — see below. |

The only place backend state moved without an accompanying UI signal is the incidental
`GET /api/compass?as_of=2026-08-12` 400→200 flip. This is not a parity gap in the sense this report
exists to catch (a capability quietly built and left undiscoverable while being marketed as done) —
every artifact that surfaces this fact caveats it as partial and not-yet-verified: the dev handoff's
Known Issue #5 states outright "iteration 9 should not assume the replay will pass just because the
endpoint now serves," and `docs/goal.md`'s J-10/J-11 responsibility boundary places the actual
repaired-state UI claim in a not-yet-run J-11 Stage G. Nothing here asks a user to trust a page that
isn't ready.

## Flags

### Hidden Capabilities
None. J-10 has no user-facing capability this iteration; its UI walkthrough is explicitly and
correctly waived by the phase spec.

### Undiscoverable Capabilities
None.

### Potential Regressions
None from component sharing (see Regression Risk table above — zero intersection with any prior UI
feature's files; the one shared backend file's edit is docstring-only, independently verified).
J-01–J-04's actual current state is genuinely unknown from this iteration's own evidence (the only
attempt was the forbidden, quarantined replay lane, addressed above) — that is an intentional,
spec-mandated unknown, not a regression finding, and re-verification is already scheduled
unconditionally for iteration 9 / J-11 Stage G.

### Visual Consistency
N/A. Zero frontend files touched, zero new pages or components rendered this iteration — nothing to
assess against the DESIGN SYSTEM tokens or prior pages' visual style.

## Recommendation

No action required for this iteration's own scope — the UI correctly has no new surface, no
regression risk was found, and the one partial data-consequence is honestly labeled everywhere it
appears rather than being presented as delivered. Two non-blocking forward notes, both already known
elsewhere in the pipeline and not new escalations from this report:

1. When `ui-test-results.md` is next regenerated, propagate the `INVALID-forbidden-lane.md` marker
   inline into the merged file (not only the evidence directory) so a reader of that single file isn't
   misled by its `2/2 PASS` table — the audit already logged the root cause (depth-demotion silently
   enabling a forbidden lean-mode parallel browser-QA lane) as framework follow-up work.
2. Iteration 9 / J-11 Stage G should perform the deferred J-01–J-04 browser verification against
   whatever coverage state actually exists by then — tracked already in `docs/goal.md`'s lane gate and
   this iteration's own OUT OF SCOPE section; nothing new to add here.
