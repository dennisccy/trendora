# goal-ops-hardening-iter-29 Frontend Handoff

**Phase:** goal-ops-hardening-iter-29
**Date:** 2026-07-27
**Agent:** developer
**Status:** complete

## What Was Built

One small, additive UI change on the existing `/evidence` page: when the backend cannot resolve one
claim's historical drawdown/dry-spell expectations (a transient per-claim compute failure, now caught and
isolated server-side by Fix 2 in the backend handoff), that ONE claim's card now discloses it honestly
instead of silently rendering nothing indistinguishable from "not applicable." No new page, no new nav
entry, no new user action — a passive disclosure inside the existing `DrawdownExpectationsPanel` section of
the existing Evidence claim card.

- **`apps/frontend/lib/evidence.ts`:**
  - `CertifiedClaim` gains one new optional field: `expectations_status?: "unavailable"` — present ONLY on
    a claim row whose per-claim drawdown-expectations compute raised an exception this request; absent,
    byte-unchanged, for a successful compute AND for every pre-existing honest-`None` case (an out-of-scope
    horizon, an unresolvable cohort, a zero-observation cohort).
  - New pure rendering-state resolver `resolveDrawdownExpectationsPanelState(claim)` — the single, testable
    authority for which of three states the panel renders (`"present"` / `"unavailable"` / `"absent"`).
    Mirrors this codebase's established extracted-decision-function pattern
    (`lib/background-compute-panel-branch.ts`, iter-24/25 J-09) rather than branching inline inside JSX —
    no React, no DOM, unit-testable under `node`/`tsx`.
- **`apps/frontend/app/evidence/page.tsx`:**
  - `DrawdownExpectationsPanel` now takes the whole `claim` (previously just `expectations`), calls the new
    resolver, and renders:
    - `"present"` — the existing table (deciles-by-phase / underwater / time-to-recover / loss-streak),
      byte-unchanged.
    - `"absent"` — renders nothing, byte-unchanged (the pre-existing honest-None cohort-unresolvable case
      — this is NOT a new state, just confirmed untouched).
    - `"unavailable"` — **NEW**: a small heading ("Historical drawdown & dry-spell expectations") plus one
      calm sentence, "Unavailable — monitored and refreshed as new data arrives." Styled with
      `text-text-faint` throughout — the SAME calm, non-alarming treatment the card's existing "Pending —
      monitored as new data matures" forward-walk cell already uses. Never a red/error/warning treatment:
      this is an expected transient state, not a system error. Carries `data-testid=
      "evidence-expectations-unavailable"` for QA/browser automation.

## UI Evolution Confirmation

- New user-facing capability: yes, as scoped in the plan — a per-claim honest failure disclosure.
- New information displayed: one new optional field, surfaced as one inline note, on the affected claim's
  card only.
- New user actions: none — passive disclosure, no new control, no new click path.
- UI surface changes: none at the page/nav level — purely additive inside the existing panel slot.
- Visual consistency: reuses the EXISTING claim-card / `Field` / `DrawdownExpectationsPanel` structure and
  the EXISTING `text-text-faint` honest-copy convention already established on this same card — no new
  component library usage, no new color/spacing/typography tokens, no new visual effect.

## States Handled

| State | Trigger | Rendering | Status |
|---|---|---|---|
| `present` | `claim.expectations` is a real payload | Full deciles-by-phase table | Unchanged |
| `absent` | No `expectations`, no `expectations_status` | Nothing (panel section omitted) | Unchanged |
| `unavailable` | `claim.expectations_status === "unavailable"` | Calm inline note, no table | **NEW this iteration** |

## Tests Run

No test framework is installed in this frontend beyond the repo's own `node lib/*.test.ts` convention; this
dev box's Node build (v22.22.1) lacks TypeScript type-stripping (`node lib/*.test.ts` →
`ERR_UNKNOWN_FILE_EXTENSION`, the same pre-existing limitation documented in prior iterations' handoffs).
Verified via `npx tsx`, available on this box:

```
cd apps/frontend && npx --no-install tsx lib/evidence.test.ts
```
4 new cases added (TC-5): `present` carries the expectations object verbatim; `unavailable` resolves
correctly; `absent` (the pre-existing no-field case) resolves correctly and stays that way; an explicit
assertion that `unavailable` and `absent` are DISTINCT `kind` values (the crux of TC-5 — a genuine compute
failure must not be indistinguishable from "not applicable"). **Result: 46 evidence-badge resolver checks
passed** (42 pre-existing + 4 new), 0 failed. RED confirmed first: before implementing the resolver, the
new test failed with `TypeError: resolveDrawdownExpectationsPanelState is not a function` while all 42
pre-existing checks still passed.

Sibling regression (a lib file that also imports from `evidence.ts`):
```
cd apps/frontend && npx --no-install tsx lib/factor-lab-evidence.test.ts
```
5 checks passed, unchanged.

Whole-project type-check:
```
cd apps/frontend && npx --no-install tsc --noEmit -p tsconfig.json
```
Zero errors — confirms the `CertifiedClaim` field addition and the `DrawdownExpectationsPanel` prop-shape
change (`expectations` → `claim`) did not break any other consumer (`components/evidence-status-badge.tsx`,
`components/score-proof-panel.tsx`, `lib/factor-lab-evidence.ts`, `lib/graveyard.ts`,
`lib/referee-audit.ts`, `app/research/graveyard/page.tsx`, `app/research/referee-audit/page.tsx`,
`app/research/budget/page.tsx`, `app/stocks/page.tsx`, `app/stocks/[ticker]/page.tsx`,
`app/research/_labs.tsx`, `lib/api.ts` — every file importing from `lib/evidence.ts`).

## Live Verification

Loaded `/evidence` against the live backend (started via `scripts/dev.sh`, port 3255) — HTTP 200, no
`application error` / `unhandled runtime error` / `500` marker in the returned HTML. On the current live
7-claim ledger every claim's `expectations` resolved successfully server-side this run (confirmed via
`GET /api/evidence`: all 7 rows carry `expectations`, none carry `expectations_status`), so the new
`"unavailable"` branch was not visually exercised live this iteration — its correctness rests on the 4
passing unit tests above (TC-5) plus the backend's own TC-4 proof that the field is set correctly when a
compute failure occurs. A full browser screenshot/DOM assertion of the `"unavailable"` note (requires
either a monkeypatched live failure or a mocked API response) is reviewer/QA scope per the plan.

## Known Issues

- The `"unavailable"` note's copy ("Unavailable — monitored and refreshed as new data arrives.") was
  written to match the card's existing calm honest-copy family rather than quoting a specific retry
  mechanism verbatim — it is accurate (the ingest-finalize warm loop does re-attempt every ledger claim on
  the next fetch/backfill/rebuild) but has not been proofread by a second reviewer for tone.
- No screenshot evidence of the new "unavailable" state was captured this iteration (see Live Verification
  above) — the live ledger's 7 claims all resolved successfully, so the branch was proven only at the unit
  level, not visually. Flagging for QA to exercise via a mocked/monkeypatched response if a visual proof is
  required for the walkthrough.
