# Iteration 20 — Coherence Audit

**Iteration:** goal-market-compass-iter-20
**Date:** 2026-08-27
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Scope note

Iteration 20 is a backend-only, no-user-visible-surface maintenance iteration (J-11 Stage E: the
live, global create-once `forward_returns` hole repair over the retained + Stage-D-rebuilt
`scanner_runs` population). The iter spec's own "New user-facing capability / New information
displayed / New user actions / UI surface changes / Product surface delta" fields are all `None`,
and the ui-surface-map (`reports/phase-goal-market-compass-iter-20-ui-surface-map.md`) confirms
maintenance isolation was held — no application-service boot, no browser QA. I independently
verified rather than took the spec's word for it:

- `git status --porcelain -uall` shows exactly four new backend files (`apps/backend/app/engine/
  j11_stage_e_execute.py`, `apps/backend/scripts/run_j11_stage_e_execute.py`,
  `apps/backend/tests/test_j11_stage_e_execute.py`, `apps/backend/tests/
  test_j11_stage_e_execute_cli_script.py`) plus docs/reports/runs artifacts — **zero** files under
  `apps/frontend/`, zero `.tsx`/`.ts`/`.jsx`/`.css` files anywhere in the change set.
- `runs/goal-session-market-compass/state/blueprint.md` is **not** in the modified-files list —
  confirmed untouched, matching the spec's "Blueprint conformance" claim.
- The diff caveat in the dispatch note is real and was followed: the bounded `iter-diff.md` doesn't
  exist for this iteration (only `goal-slice.md`/`depth-dispatched`/`snapshot-sha` are present under
  `runs/goal-session-market-compass/iter-20/`), and the four source files are untracked so `git diff
  <sha>` would show nothing — I read all four files directly rather than relying on a diff.

Because there is no new UI surface, no new endpoint, and no new displayed value, Part B (Information
Architecture) has nothing to check this iteration — there is no route/page/feature to place in the
nav. Part A (Data Contract) reduces to: does the write path duplicate or bypass any registered
canonical computation? It does not (below).

## Data Contract check

`forward_returns`/`/backtest` is explicitly **not** a row in `blueprint.md`'s Data Contract table — I
re-verified this directly against the blueprint text (it predates this session, from `ops-hardening`,
and this session's Data Contract rows are: Next-session manifest CONTENT/FREEZE blocks, Engine
identity, Stock sector label, Regime label+score, Market phase/severity/P(bear), Breadth,
Sector/theme scores, Stock leadership/entry/risk, Evidence ledger, Coverage payload, Run summary,
Readiness/preflight — no forward-return row among them). So there is no registered value for this
iteration to duplicate via a new forward-return computation. The two registered values Stage E's
verification logic *touches* (read-only, for drift-detection, never re-derived) are:

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Engine identity | OK — reuses the SAME registered canonical function | `j11_stage_e_execute.py:252` (CLI) calls `engine_identity.compute_engine_identity(cfg)`, the exact function `blueprint.md`'s "Engine identity" row names; used only to compare against Stage D's frozen value, never to mint a new identity or serve a UI value |
| Next-session manifest (FREEZE/INTEGRITY block) | OK — read-only diff against a stored dump, not a recomputation | `j11_stage_e_execute.py:176-192` (`confirm_manifests_unchanged`) calls `j11_schema_migration.dump_table`/`diff_dumps` — a byte-level snapshot comparison, not a second implementation of `build_manifest_payload`; zero manifest rows created or changed (`mutation-accounting.json`: `manifests_unchanged: true`, 24 rows before/after) |
| forward_returns (untracked, pre-existing from ops-hardening) | OK — single canonical write path only | `j11_stage_e_execute.py:319` calls ONLY `forward_testing.backfill_run_forward_returns(session, run, config)` — the pre-existing canonical create-once function. `forward_testing.py` itself is unmodified (confirmed: not in `git status`; also OUT OF SCOPE explicitly forbids touching it). Static AST tests (`test_tc3_module_never_references_backfill_forward_returns`, `test_tc3_cli_script_never_references_backfill_forward_returns`) prove the whole-database entry point `backfill_forward_returns()` is never imported or called by the new module/script — no second write path was introduced |

No duplicate computation, no non-canonical serving path (there is no serving path at all — nothing
from this iteration is exposed via any endpoint), and no new displayed value was introduced, so A4/A5
("new unregistered value") don't apply either.

## Information Architecture check

Not applicable — zero new pages/routes/features this iteration. No entry needed in the table; there
is nothing to place in the nav skeleton, and nothing to check for reachability.

## Assessment of the coordinator-flagged auditor findings

The dispatch asked me to independently judge whether the auditor's findings (a)-(c) are coherence
matters or purely quality ones. All three are quality/evidence-strength findings internal to a
backend maintenance script's own verification logic, not coherence violations under Part A or Part B:

- **(a) Structural cascade explanation (`data_manager._cascade_targets`) vs. the calendar-enumeration
  reasoning.** This is about *why* zero retained-run insertions occurred and about the per-symbol
  (not single-SPY-calendar) resolution of `measured_date` — a correctness/rigor question about an
  untracked, backend-only value. It touches no registered Data Contract row and no UI. Not a
  coherence matter.
- **(b) Three tautological/vacuous verification checks** (`population_a_pre_was_zero`,
  `population_c_latest_run_observable_ceiling_respected`, `population_b_never_decreased` on an empty
  pre-map). These are internal assertion-strength weaknesses in the module's own self-checks, not a
  second computation of any canonical value and not an alternate serving path. Not a coherence
  matter — a test/verification-rigor matter, already captured by the auditor as T2 (gap, not fixed,
  deferred to Stage F/G).
- **(c) The TC-6 test fix.** The auditor's own account (`docs/handoffs/goal-market-compass-iter-20-
  audit.md` §4, "Fixes Applied") and my own read of `test_j11_stage_e_execute.py:428-501` confirm the
  fix touched only the test file (plus the dev handoff doc) — `j11_stage_e_execute.py` and
  `run_j11_stage_e_execute.py` are stated byte-identical to what the live run executed (`diff -q`
  silent, per the audit report), and `git status` shows exactly one version of each production file,
  consistent with that claim. No second implementation of any registered value was introduced by the
  fix-and-restore cycle. Not a coherence matter.

None of the four backend-only source files register a new displayed value, read an existing
registered value from a non-canonical path, or introduce any navigable surface. The blueprint's
"Blueprint conformance" note for this iteration ("No new surfaces... no second computation, no new
endpoint, no new page... `blueprint.md` is not edited this iteration") holds under independent
verification.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The auditor's T2/B1/B2/B3 findings (tautological checks, weak "unrestamped" comparison, content-
  level instrument gaps for 5 of 8 out-of-scope tables, missing cross-iteration sweep artifact) are
  real evidence-rigor gaps worth tightening when Stage F forks this module, per the auditor's own
  "Recommended Next Step" — but they are quality/test-rigor matters for the auditor/reviewer lane, not
  coherence-gate matters, since Stage E introduces no duplicate computation and no new surface. Carried
  here only so the record shows this gate considered them and reached an independent conclusion, as
  the dispatch requested.
- No unregistered-but-new displayed value exists to flag (nothing is displayed this iteration).
