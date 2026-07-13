# goal-mcp-loop-iter-29 Dev Handoff

**Phase:** goal-mcp-loop-iter-29
**Date:** 2026-07-13
**Agent:** developer
**Status:** complete

## What Was Built

**Nothing — this is a deliberate verify-only iteration, and the DoD is satisfied by an empty diff.**
Per the iter spec's IN SCOPE section ("None — zero backend source change" / "None — zero frontend
source change") and the coordinator note, the goal of this pass is narrower than iter-28's: iter-28
established (and documented) the plateau finding that the complete pre-registered candidate set is
empirically exhausted (7/7 canonical + 7/7 staging FAIL). The owner then acted on that finding at
commit `eb19cee` — a **docs-only** amendment to `docs/goal.md` that re-scopes J-02/J-06/J-07/J-08/J-09
to **outcome-neutral** acceptance (passes in EITHER the "Proven" or the honest "Not yet proven" state,
so long as the surfacing is honest and correct). Iter-29's job is to confirm that the product surface —
unchanged since iter-28, when browser-qa already captured every one of these assertions live — now
satisfies that new contract, so the evaluator/journey-history can flip these five from `partial` to
`passing` with no code touched. No `## Evidence Claim` was authored, submitted, or promoted.

### Verification performed

1. **Product-source / ledger byte-identity**, checked two ways:
   - Against the iteration snapshot (`runs/goal-session-mcp-loop/iter-29/snapshot-sha` =
     `6492189a1cf9be5c4905f55ac9b69a510fe66901`, a pre-iteration stash-style commit whose first parent
     is current HEAD `eb19cee`):
     `git diff 6492189a1cf9be5c4905f55ac9b69a510fe66901 --stat -- apps/ config.yaml
     apps/backend/data/seed runs/goal-session-mcp-loop/state/certified-claims.jsonl
     runs/goal-session-mcp-loop/state/staging-ledger.jsonl` → **empty output**.
   - Against HEAD directly: `git diff HEAD --stat` over the same path set → **empty output**.
   - Confirmed HEAD (`eb19cee`) itself is docs-only (`git show --stat eb19cee` touches exactly one
     file, `docs/goal.md`, 286 insertions / 99 deletions) — so no application code has changed since
     iter-27 (`ec2ec0b`, the last CONTINUE verdict with a working, QA-verified runtime).
   - `apps/backend/app/**`, `apps/frontend/**`, `config.yaml`, `apps/backend/data/seed/**`, and both
     `certified-claims.jsonl` / `staging-ledger.jsonl` are byte-identical to HEAD and to the iteration
     snapshot.
2. **No Evidence Claim registered.** `grep -n "## Evidence Claim" docs/phases/goal-mcp-loop-iter-29.md`
   returns no match (only descriptive prose mentions it, never as a heading). The post-decompose gate
   therefore passes automatically and the canonical Bonferroni divisor stays at **8**.
3. **Targeted frozen-golden ledger tests** (the only tests this iteration runs — NOT the full suite,
   which is ~10-11h at the 30-year basis and would fork-lock the host, per standing session guidance):

   ```
   cd apps/backend && .venv/bin/python -m pytest \
     tests/test_evidence.py::test_canonical_ledger_frozen_golden \
     tests/test_staging_ledger_routing.py::test_committed_staging_ledger_is_the_regenerated_30y_discovery \
     -v
   ```

   Result: **2 passed in 0.19s**. Both pin the ledgers byte-for-byte — 7 canonical entries (strict
   Bonferroni divisors 1..7, register_date 2026-07-03, all FAIL, `proven_signals == {}`) and 7 staging
   entries (register_date 2026-07-03, LORD++ economy, all FAIL). Neither test needed edits.
4. **Fresh byte-match of the four DoD-named claim rows**, read directly from
   `runs/goal-session-mcp-loop/state/certified-claims.jsonl` (not carried from iter-28's summary — re-verified
   this pass so the handoff cites current, not stale, numbers):

   | Journey | cohort | horizon | holdout_edge | p_value | divisor | status |
   |---|---|---|---|---|---|---|
   | J-06 | vcp_contraction D10 | 20 | −0.003773 | 0.959520 | 4 | FAIL |
   | J-07 | vcp_contraction D10 | 60 | −0.016364 | 0.999500 | 5 | FAIL |
   | J-08 | rs_spy_3m×high_proximity composite | 20 | +0.000080 | 0.494253 | 6 | FAIL |
   | J-09 | rs_spy_3m D10 | 60 | −0.014155 | 0.904548 | 7 | FAIL |

   All four byte-match the iter spec's DoD-named approximations exactly (≈ −0.38%/−1.64%/+0.01%/−1.42%
   and their p-values). All four `status: FAIL`; ledger-wide `grep -c '"status": "FAIL"'` = 7 of 7, zero
   `PASS`. J-02 (the `/stocks/{ticker}` inline-badge honesty check) has no single ledger row to
   byte-match — its acceptance is the general property that with 0 PASS rows in the ledger, every score's
   badge on that page reads "Not yet proven" with no proof panel; that is a browser-qa assertion, not a
   ledger-row lookup.

### Why journey status flips are not made here

Flipping J-02/J-06/J-07/J-08/J-09 from `partial` to `passing` in
`runs/goal-session-mcp-loop/state/journey-history.json` is the goal-evaluator's job, not the developer's
— this pass supplies the verification evidence (zero diff, targeted tests, byte-matched ledger rows) that
the evaluator and the downstream browser-qa lane need to make that call under the new outcome-neutral
acceptance. `journey-history.json` was not touched by this pass.

## Files Changed

None (product code). `git diff HEAD` is empty on all product source (`apps/backend/app/**`,
`apps/frontend/**`, `config.yaml`, `apps/backend/data/seed/**`) and on both evidence ledgers. The only
files written by this developer pass are this handoff and `runs/goal-mcp-loop-iter-29/status.json`.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_evidence.py::test_canonical_ledger_frozen_golden tests/test_staging_ledger_routing.py::test_committed_staging_ledger_is_the_regenerated_30y_discovery -v`

Result: **2 passed, 0 failed** (0.19s). This is the DoD-relevant targeted invocation only, matching
iter-28's precedent — the full suite (~10-11h at this data basis) was intentionally NOT run per standing
session guidance (a concurrent full pytest run fork-locks the host; the reviewer verifies tests).

No backend/frontend services were started for this pass. Rationale: zero application code has changed
since iter-27's last QA-verified working state (HEAD's only new commit, `eb19cee`, touches only
`docs/goal.md`), so there is no new code path a service-startup smoke test could catch that wasn't
already covered by iter-27's passing QA — and the iter spec's own TESTING REQUIREMENTS section assigns
live-service verification explicitly to the browser-qa lane ("Bring up BOTH prod-mode services and
confirm reachability BEFORE dispatching browser-qa... `rm -rf apps/frontend/.next` first"), not to this
developer pass. This mirrors iter-28's handoff, which used the identical rationale and passed review
without issue. (Confirmed separately: no trendora backend/frontend process is currently running on this
host, so there is no stale-process state for the browser-qa lane to inherit.)

## Known Issues

- None introduced by this pass — zero code touched.
- Carried forward from iter-27/28 and explicitly OUT OF SCOPE here (do not bundle): B1
  `IndicatorsCfg._validate` `max_needed` guard hole; T1/F1 browser-qa backend-lifecycle permission;
  `rm -rf .pytest-tmp-iter27/` scratch cleanup.
- The actual PASS/FAIL determination for J-02, J-06, J-07, J-08, J-09 against their new outcome-neutral
  acceptance depends on a fresh browser-qa capture per the iter spec's TESTING REQUIREMENTS (md5-distinct
  PNGs, full-page/element-clip captures for below-the-fold `/evidence` rows and factor-lab/
  factor-combination badges — iter-14 lesson: a scrolled-viewport capture can return a blank frame). This
  developer pass confirms the product surface and underlying data are unchanged and byte-correct; it does
  not itself drive a browser, per the developer agent's scope on this lean iteration.
