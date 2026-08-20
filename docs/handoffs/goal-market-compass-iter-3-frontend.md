# goal-market-compass-iter-3 Frontend Handoff

**Phase:** goal-market-compass-iter-3
**Date:** 2026-08-20
**Agent:** developer
**Status:** complete

## What Was Built

- **Manifest strip** (`apps/frontend/components/compass-manifest-strip.tsx`, new) — the last of the
  compass cards on `/`, rendered after the existing Next-session-focus section and still above the
  unmodified `<DashboardBody>`. Reads ONLY `GET /api/compass`'s extended payload; renders no threshold,
  word map, or derived count of its own.
  - Mode/version/frozen/prospective-eligible badges + freeze timestamp.
  - Four truncated-with-title hash chips (engine identity, candidate rule, cohort rule, manifest
    config) — full value always reachable via the native `title` tooltip.
  - Dataset stamp, universe pool hash, member count, profile.
  - A basis-disclosure line (available / rebuilt / unavailable — three distinct `Badge` variants).
  - An expandable audit table (`Disclosure`): the comparison cohort (every non-selected member, with
    its closed-vocabulary disposition column) and, under its own always-visible research-only label,
    the near-threshold shadow cohort (no disposition column — it never gates selection). Both carry the
    `cohort_semantics` caveat text and the evidence/survivorship/sector-basis caveats verbatim.
  - A versions list (rendered only once more than one version exists for the `as_of`).
  - A confirm-gated "Regenerate manifest" control, actionable only while viewing a historical date
    (`asOf !== null`, from the existing sole `useAsOf()` provider) — while on "Latest" the button is
    replaced with an explanatory line instead. The confirm modal reuses the established J-69 in-page
    pattern (`Card` + fixed overlay, persistently-visible Confirm button outside any scroll region — no
    Dialog primitive in this project), colocated in the same file, mirroring `RebuildConfirmModal`
    (`apps/frontend/app/data/page.tsx`).
  - Its own independent honest "unavailable" state when `compass === null` (matching the other three
    compass cards' existing precedent) and a dedicated "pre-freeze era" state when `mode === null` (a
    legacy iter-2 row with no freeze/integrity block recorded).
  - `generation.preflight_verdict` is deliberately NEVER rendered here (AG-13) — it stays reachable only
    via the raw API response.
- **TC-36 float-display fix** — `apps/frontend/lib/format-fact.ts` (new) exports `formatFactValue`: a
  number renders `.toFixed(2)`, everything else renders via `String(...)` unchanged (no behavior change
  for strings/booleans/null). Applied in `compass-summary-card.tsx`'s "Show cited facts" disclosure
  (was raw `String(fact.value)`).
- **`apps/frontend/lib/api.ts`** — `CompassResponse` extended with every new field (`version`, `mode`,
  `frozen`, `comparison_cohort`, `near_threshold_shadow`, `generation`, both rule-identity hashes +
  configs, `manifest_config_hash` + subset, `dataset`, `universe`, `caveats`, `prospective_eligible`,
  `available_at_utc`, `manifest_hash`, `basis`, `versions`) plus nine new supporting interfaces
  (`CompassGeneration`, `CompassCohortRow`, `CompassComparisonCohortRow`, `CompassAtrPct`,
  `CompassThemeMembership`, `CompassDatasetStamp`, `CompassUniverseBlock`, `CompassCaveats`,
  `CompassBasisDisclosure`, `CompassVersionSummary`). New `regenerateManifest(asOf)` — a POST with
  `as_of`/`confirm=true` as query params (mirrors the existing `withAsOf`/`sendJSON` conventions).

## Files Changed

- `apps/frontend/components/compass-manifest-strip.tsx` -- new (manifest strip + colocated confirm
  modal).
- `apps/frontend/lib/format-fact.ts` -- new (TC-36 formatter).
- `apps/frontend/lib/format-fact.test.ts` -- new (7 checks, plain node script per this project's
  frontend test convention).
- `apps/frontend/lib/api.ts` -- extended `CompassResponse` + new types + `regenerateManifest`.
- `apps/frontend/components/compass-summary-card.tsx` -- TC-36 fix (uses `formatFactValue`).
- `apps/frontend/app/page.tsx` -- renders `<CompassManifestStrip compass={state.compass} asOf={asOf} />`
  after `CompassFocusSection`, before `DashboardBody`.

## Tests Run

Command: `cd apps/frontend && npx tsc --noEmit -p tsconfig.json` -- zero errors.
Command: `cd apps/frontend && NEXT_PUBLIC_API_URL=http://localhost:8000 NEXT_DIST_DIR=.next-verify npx next build`
-- compiled successfully, all 29 routes generated, types valid (per this project's build guard, a
verification build must target a throwaway dist dir, never the live `.next`; cleaned up afterward).
Command: `cd apps/frontend && npx tsx lib/format-fact.test.ts` -- 7 passed. All 20 other pre-existing
`lib/*.test.ts` suites also re-run clean (no regression from the `api.ts` type additions).

### Live verification

Started the real backend + a real production frontend build (`scripts/start-backend.sh` /
`scripts/start-frontend.sh`) against the full 591-symbol committed-seed database and drove the actual
browser:

- `/` renders the manifest strip fully populated against real data: 539 comparison-cohort rows + 26
  near-threshold-shadow rows, all four hash chips, dataset/universe stamps, a 5-entry versions list
  (from repeated manual regenerate calls during this verification pass), correct basis line.
- Extracted the FULL rendered text of the manifest strip and confirmed no readiness/preflight token
  ("Ready", "GO", "DEGRADED", "NO-GO", "Initializing", "Backend unavailable") appears anywhere inside it
  -- those tokens appear only in the separate, pre-existing top chrome bar shown by the SAME page load
  (AG-13 / TC-31, verified empirically, not just by code inspection).
- Stepped to a historical `?asof=2026-08-05` date: the "Regenerate is available only for..." message was
  replaced by an enabled "Regenerate manifest" button (confirming the `asOf !== null` gate works); on
  "Latest" the button is absent and the explanatory line shows instead.
- Clicked "Regenerate manifest", confirmed in the modal (extracted its text -- correct content), clicked
  "Regenerate manifest" in the modal footer -- the strip updated in place to "version 2 / retrospective /
  not prospective-eligible" with a fresh timestamp, no page reload, no crash.
- Verified `regime_score_delta` in the Summary card's cited facts renders `6.27` (clean, TC-36) against
  real computed data, not a raw floating-point artifact.
- This live pass caught and fixed a real bug before handoff: the backend's regenerate-route response
  initially lacked `basis`/`versions` (only the GET route had them), which would have crashed this
  component the first time a user actually clicked Regenerate (`view.versions.length` on `undefined`).
  Backend fixed to serve both fields identically on both routes; re-verified live afterward.

## Known Issues

- No dedicated UI treatment exists yet for "the current frontier has no manifest at all" (a 404 from
  `GET /api/compass`) beyond the pre-existing generic "unavailable" state every compass card already
  shows on any fetch failure -- this iteration's spec (J-07) explicitly defers the Today-page's final
  "not yet frozen" composition to a later iteration. The current behavior is honest (never fabricates
  data) but not maximally informative.
- The manifest strip's audit table has no pagination/virtualization -- a 539-row table renders in full
  on a wide universe. No performance issue was observed live (page interactive well within a couple of
  seconds), but this is worth watching if the universe grows substantially.
- Regenerate-control gating uses `asOf !== null` (the as-of switcher's own "not Latest" state) as the
  proxy for "non-frontier as_of", per the plan's own suggested approach -- this is not a byte-for-byte
  guarantee that the CURRENT server-side frontier and the client's notion of "Latest" are always the
  same instant (a session boundary crossing between page load and click could theoretically drift them
  by one day); the backend's own `regenerate_manifest` has no such restriction (it will happily
  regenerate the actual live frontier's manifest too, per its own contract), so this is a UI-only
  convenience gate, not a safety guarantee, and was not felt necessary to harden further this iteration.
