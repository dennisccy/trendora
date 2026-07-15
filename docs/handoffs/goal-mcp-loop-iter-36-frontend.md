# goal-mcp-loop-iter-36 Frontend Handoff

**Phase:** goal-mcp-loop-iter-36
**Date:** 2026-07-14
**Agent:** developer
**Status:** complete

## What Was Built

One new read-only page (`/research/referee-audit`) and one new nav card on the `/research` hub (J-22 /
backlog B-102) — the 4th and final card in the "Governance & process" grouping, now complete at 4/4.

- **`apps/frontend/lib/referee-audit.ts`** (new): types-only file mirroring `lib/budget.ts` /
  `lib/graveyard.ts`'s established pattern —
  - `RefereeAuditContaminatedVerdict` (a type alias for the existing `Verdict` from `lib/evidence.ts` —
    the contaminated factor's verdict is the SAME shape a certified-claims row's verdict carries).
  - `RefereeAuditReport` — `status: "ok" | "unreadable"` plus every artifact field (`n_null_trials`,
    `seed`, `alpha`, `source_factor`, `false_pass_count`/`rate`/`ci_low`/`ci_high`,
    `n_insufficient_null`, `contaminated_factor_horizon`, `contaminated_verdict`,
    `contaminated_expected_outcome`, `contaminated_caught`), all nullable — the `"unreadable"` fallback
    carries every field as `null` except `status`.
  - `RefereeAuditResponse` — `{ report: RefereeAuditReport | null }` (`null` = the harness has never run,
    distinct from `status: "unreadable"` = it ran but the artifact is corrupt).

- **`apps/frontend/lib/api.ts`** (modified): imports + re-exports the three types above; new
  `fetchRefereeAudit(signal?)` calling `GET /api/research/referee-audit` via the shared `getJSON` helper
  — mirrors `fetchBudget` / `fetchGraveyard` exactly (throws on network error / non-200, so the page
  renders an explicit "Backend unavailable" state; never fabricates data).

- **`apps/frontend/app/research/referee-audit/page.tsx`** (new): the read-only report page.
  - **Loading**: a 4-card skeleton (mirrors `BudgetSkeleton`).
  - **Error** (`data-testid="referee-audit-error"`): a contained "Backend unavailable" card, red border,
    nav intact — mirrors `budget`/`graveyard` pages' identical error card exactly.
  - **Honest empty** (`report === null`, `data-testid="referee-audit-empty"`): "No audit run yet" —
    explicitly states the harness is a config-seeded offline job (`python -m app.engine.referee_audit`),
    never a UI action here (so the page never offers a "run it" button — J-22 is read-only by design).
  - **Unreadable** (`report.status === "unreadable"`, `data-testid="referee-audit-unreadable"`): an amber
    (not red) degraded-parse state, distinct from both "never run" and the tripwire failure — mirrors
    `DriftReportPanel`'s own unreadable-artifact treatment on `/data`.
  - **Normal/report present**: a 4-stat grid (`data-testid="referee-audit-grid"`) — null trials + source
    factor, empirical false-pass rate + count + 95% CI, configured α, run date + seed/horizon — then
    EITHER:
    - **Calm** (`contaminated_caught === true`, `data-testid="referee-audit-contaminated-caught"`): a
      quiet card with a green shield-check icon, stating the contaminated factor was correctly rejected
      (or ruled insufficient), styling consistent with the rest of the evidence-status language — no
      celebration, just calm confirmation.
    - **Tripwire** (`contaminated_caught === false`, `data-testid="referee-audit-tripwire"`): a
      **prominent RED** (`border-neg bg-neg/10 text-neg`) card, never hidden, stating plainly that the
      contaminated factor was NOT rejected and the harness may be leaking signal. This is the state the
      REAL offline run actually produced (see the dev handoff) — live-verified via a real browser session,
      screenshot confirmed the exact intended loud treatment.
    - Both states render the `contaminated_expected_outcome` static "(expected: rejected)" label
      alongside the actual verdict status badge (`data-testid="referee-audit-contaminated-status"`,
      NEVER the `accent`/"Proven"-looking badge variant — even a PASS here maps to `danger`, since a PASS
      on the perfect-crime factor is alarming, not proof of anything).

- **`apps/frontend/app/research/page.tsx`** (modified): added the 4th "Referee audit" governance card
  (`data-testid="research-governance-link-referee-audit"`, `ShieldCheck` icon from `lucide-react`) —
  same `Card`/`Link` border/hover/focus classes as the registry/graveyard/budget cards immediately above
  it; no new visual pattern. Updated the section's explanatory comment to note the cluster is now
  complete (4/4). No nav-skeleton change.

## Design system compliance

- Component library: `Card`/`CardContent` (`@/components/ui/card`), `Badge` (`@/components/ui/badge`,
  variants `danger`/`warn`/`default` only — never `accent`, per the anti-goal-#1 discipline this codebase
  already enforces on the graveyard page), `PageHeading` — no raw HTML where a project component exists.
- Tokens only: `border-neg`/`bg-neg/10`/`text-neg` (the tripwire), `border-warn`/`bg-warn/10`/`text-warn`
  (unreadable), `text-pos` (calm shield icon), `text-text-muted`/`text-text-faint`, `text-xs`/`text-2xl`,
  `font-semibold` — all pre-existing tokens already used elsewhere on sibling governance pages; no
  arbitrary values introduced.
- States handled: loading (skeleton) / error (backend unavailable) / honest-empty (never run) /
  unreadable (corrupt artifact) / calm (caught) / tripwire (not caught) — six total, no bare
  happy-path-only render.
- Responsive: the stat grid is `grid-cols-1 sm:grid-cols-2 xl:grid-cols-4`, identical breakpoints to
  `BudgetGrid`; the report body is a single-column vertical stack otherwise.
- Interactive elements: the "Back to Research" link and the new hub card both carry the existing
  hover/focus-visible treatment already used by every sibling link on these pages (no new interaction
  pattern invented).
- No proven-language anywhere on the new page or card — every figure is descriptive calibration
  accounting; the single source of "Proven" stays `/evidence`, untouched by this page.

## Tests Run

Command: `cd apps/frontend && npx tsc --noEmit`
Result: clean, no errors (`RefereeAuditReport`/`RefereeAuditResponse` type-check correctly against
`fetchRefereeAudit`'s usage in the new page).

Command: `cd apps/frontend && npx next build` (via `scripts/start-frontend.sh`'s rebuild)
Result: compiled successfully; `/research/referee-audit` listed as a real route (3.51 kB, 126 kB First
Load JS) alongside the other `/research/*` sub-pages.

No frontend unit-test runner exists in this project for component-level tests (confirmed by the absence of
one in every prior iteration's frontend handoff) — coverage here is TypeScript strictness + the build +
live browser verification below.

## Live verification (real browser, not just curl)

Navigated a real Chrome session to the running frontend (port 3255, pointed at the running backend on
port 8255, which was itself serving the REAL persisted artifact from the offline harness run):

- `/research/referee-audit` rendered all 4 stat cards with the real values (200 null trials, source
  factor `leadership_score`; false-pass rate `0.08`, `16 of 200 trials`, CI `[0.04984, 0.126]`; α `0.05`;
  run date `2026-07-01`, seed `20240601`, contaminated horizon `5d`) and the prominent red tripwire card
  with the `PASS` badge and the full explanatory text — screenshot confirmed the exact intended treatment
  (no cropped/hidden content, correct dark-theme contrast, nav/header intact).
- `/research` showed all 4 governance cards including the new "Referee audit" one, in the correct grid
  position, matching the sibling cards' visual style exactly.
- Clicking the new hub card navigated correctly to `/research/referee-audit` (confirmed via
  `window.location.href` after the click).

**Not** independently verified by me: the honest-empty state, the unreadable state, and the calm
(caught=true) state — the REAL artifact happens to be in the tripwire state, so exercising the other three
states would require pointing `TRENDORA_REFEREE_AUDIT_PATH` at hand-built fixtures and a second browser
pass. The component logic for all four was written and type-checked, and the backend endpoint tests
(`test_api_referee_audit.py`) already prove the API layer serves each shape correctly (missing -> `{report:
null}`; corrupt -> `status: "unreadable"`; a fixture with `contaminated_verdict.status: "FAIL"` -> the
shape `CalmContaminatedCard` consumes) — but the QA/browser-qa lane should exercise these three states
live if full state-matrix coverage is required by the DoD's "Testing Requirements" (it lists all four
states as browser-check targets).

## Known Issues

1. See the dev handoff's "Known Issues" — the empirical false-pass rate and the tripwire firing are both
   honest findings from the real data, not frontend defects.
2. The three non-tripwire visual states (empty/unreadable/calm) were not live-browser-verified this
   session (see above) — recommend browser-qa exercise them via a fixture artifact if the DoD requires it.
3. No sparkline/history chart on this page (unlike `/research/budget`) — there is genuinely no
   time-series data to plot (one persisted run, not a spend-over-time ledger), so none was added
   (simplicity bar: no chart for data that doesn't exist yet).
