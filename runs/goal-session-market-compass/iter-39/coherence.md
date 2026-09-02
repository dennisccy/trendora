# Iteration 39 — Coherence Audit

**Iteration:** goal-market-compass-iter-39
**Date:** 2026-09-02
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Data Contract check

Scope: this iteration touches only the ALREADY-REGISTERED "Next-session manifest — CONTENT block"
row's `selection.why_not_totals` and `selection.why_not[].reason`/`.cap_rank`/`.cap` fields
(registered at the iter-38 blueprint note, `runs/goal-session-market-compass/state/blueprint.md`
lines 371-402). No backend file changed (`apps/backend/` diff is empty — confirmed via
`git diff 69e86ef2414dac97b2f6b67da3d06dc03ee981c6`), so the producer
(`app.engine.compass.build_manifest_payload` / `evaluate_selection`) and the serving endpoint
(`GET /api/compass`) are both untouched.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| `selection.why_not_totals` (held-back counts) | OK | `apps/frontend/lib/api.ts:1093-1104` widens `CompassSelection.why_not_totals` from required to optional — a TS type-contract fix, not a new computation; value still read only from the `CompassResponse` returned by `GET /api/compass` |
| `selection.why_not[].reason` / `.cap_rank` / `.cap` | OK | `apps/frontend/lib/api.ts:1062-1078` widens `WhyNotEntry.reason`/`.cap_rank`/`.cap` from required to optional; `compass-focus-section.tsx:123-134` (`WhyNotLeadIn`) is reviewed, unchanged in logic, and confirmed to already degrade safely on `undefined` |
| "Not priority" disclosure summary string | OK (re-format) | `apps/frontend/lib/why-not-summary.ts:39-49` (`whyNotSummary()`) is a pure formatting function extracted verbatim from the previous inline template-literal ternary in `compass-focus-section.tsx`; it takes `selection.why_not.length` and `selection.why_not_totals` — both already fetched from the canonical `GET /api/compass` response via `compass-focus-section.tsx:201-204` — and only arranges them into a display string (or a new degraded string when `why_not_totals` is `undefined`). No new arithmetic on canonical source data beyond the pre-existing sum (`excluded_by_cap_uncapped + below_floor_in_band_uncapped`), which iter-38 already performed inline; this is a location move, not a duplicate computation |

`why-not-summary.ts` declares its own local `WhyNotSummaryTotals` interface (structurally identical
to `api.ts`'s `WhyNotTotals`) rather than importing it, to keep the module dependency-free for the
plain-node test runner (documented at `why-not-summary.ts:12-15`, matching the existing
`basis-disclosure-label.ts` convention). This is a compile-time type mirror, not a second data path —
the runtime value still flows from the same `GET /api/compass` fetch through `compass.tsx`'s single
top-level call into `CompassFocusSection`'s props. No violation.

No new value/entity is introduced this iteration (confirmed against the spec's own "New information
displayed: None new" and "Data-contract additions: None" sections,
`docs/phases/goal-market-compass-iter-39.md:141-171`) and the diff confirms no new field name appears
anywhere in `apps/frontend/lib/api.ts` or `compass-focus-section.tsx`.

## Information Architecture check

No new page, route, or nav entry this iteration — the entire fix lives inside
`compass-focus-section.tsx`, already under the Today (`/`) canonical home (blueprint IA table row
`J-04 next-session candidates`). Confirmed by the diff: only `apps/frontend/lib/api.ts`,
`apps/frontend/components/compass-focus-section.tsx`, and the new pure helper
`apps/frontend/lib/why-not-summary.ts` (+ its test) changed under `apps/frontend/`; no file under
`apps/frontend/components/sidebar.tsx`, `apps/frontend/app/`, or any router config appears in the
diff.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/` — Next-session focus card ("Not priority" disclosure) | OK | No nav file changed (`git diff` shows no `sidebar.tsx`/`app/` router touch); feature already lives at its registered home per `blueprint.md` IA table row "J-04 next-session candidates (why / why-not)" → `/` |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- None. The change is a textbook narrow AG-8 repair: TS optionality widened to match what was
  always true of stored data, a guard confirmed (not newly written) safe for the already-correct
  `WhyNotLeadIn` case, and a mechanical extraction of an existing inline string into a testable pure
  function with a byte-identical fully-counted branch. No new surface, no new data path, no drift
  from the established Today-page shell.
