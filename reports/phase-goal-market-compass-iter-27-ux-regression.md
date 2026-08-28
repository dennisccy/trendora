# Phase goal-market-compass-iter-27 — UX Regression Review

**Date:** 2026-08-28

**Verdict:** UX-REGRESSION-PASS

---

## Scope note

`Frontend Present: no` in the phase spec and QA report means zero frontend *files* changed — but
ui-impact-analyst deliberately did not take the trivial backend-only shortcut: it produced full
`user-visible-changes.md` and `ui-surface-map.md` reports because the backend reorder makes a
previously-unreachable frontend display state reachable for the first time. Per the pump coordinator's
note, this review applies the full discoverability/regression/parity process rather than the
backend-only pass-through.

## New Capability Discoverability

There is one "new" reachability, not a new capability: the manifest strip's `"unavailable"` Basis badge
(`CompassManifestStrip` → `BasisLine`, `data-testid="compass-manifest-basis"`, red/danger variant,
label "Basis: unavailable") has existed in the frontend since iter-11
(`apps/frontend/lib/basis-disclosure-label.ts`) but was structurally unreachable through the live route
until this iteration's backend fix.

- **Navigation path: 0 clicks from home.** The Manifest card lives directly on `/` (the Today page,
  which is the application's home route) — not behind any submenu, tab, or secondary nav. Any as-of date
  whose manifest trips the new condition would surface the badge on first page load, no extra
  interaction required. This is the best possible discoverability outcome under the skill's click-depth
  rubric.
- **Label clarity:** "Basis: unavailable" plus its detail text ("the underlying scanner run for this
  as-of is no longer stored," per `app/engine/compass.py:1147`) is domain-appropriate for this
  analytics tool's existing vocabulary — it uses the same "scanner run" term the neighboring "rebuilt"
  badge's detail text already uses ("the source scanner run was recreated after this manifest was
  frozen"), so a user who already understands the "rebuilt" badge will read "unavailable" consistently.
  This label was reviewed and shipped in iter-11, not authored this iteration, so it is not a new
  discoverability risk — noted for completeness only.
- **Visual consistency:** the `danger` badge variant (`border-neg bg-surface-2 text-neg`,
  `apps/frontend/components/ui/badge.tsx:14`) is used pervasively elsewhere in the product (health-badge,
  score-badge, market-phase-card, stocks/[ticker], watchlist, evidence, research pages) — this is not a
  bespoke, unexercised style. Even though this specific instance cannot be triggered live this iteration
  (see below), the visual language it reuses is already validated across many other live pages.
- **Live reachability of this specific state:** honestly not exercised through the browser this
  iteration — no as-of date in the canonical database currently has a frozen manifest whose backing
  `ScannerRun` is missing, and manufacturing that condition is explicitly forbidden (binding DB-safety
  scoping carried from iter-26). QA's UT-04 recorded this correctly as "not live-reproducible, automated
  substitute" (pytest evidence, `-k unavailable`, 1 passed) rather than papering over the gap with a
  fabricated screenshot. This is the phase's own accepted scope boundary (spec's DEFINITION OF DONE
  explicitly authorizes fixture-level proof for the unavailable state), not a discoverability defect —
  the badge is reachable in code and CSS the moment a qualifying as-of date exists; there is simply no
  such date to click to right now.

No "hidden capability" or "undiscoverable capability" flag applies: there is nothing to navigate to that
isn't already exactly where a user would expect it (the Today page's Manifest card, alongside its three
sibling Basis states).

## Regression Risk

Two files changed with UI-adjacent surface: `apps/backend/app/api/compass.py` (route reorder) and
`apps/backend/app/engine/compass.py` (new pure-read helper + refactored existing-row check). Both feed
only `GET /api/compass`, consumed only by `CompassManifestStrip` on the Today page.

| Prior feature | Shared component | Risk assessment |
|---|---|---|
| iter-11 Basis disclosure (available/rebuilt/unverifiable states) | `CompassManifestStrip` → `BasisLine`, `basis-disclosure-label.ts` | **Low, verified.** UT-02 ("available" on 2025-04-15) and UT-03 ("rebuilt" on 2026-08-12 frontier) both PASS live against the reordered route — exact badge color, label, and detail text unchanged from pre-fix behavior. |
| Manifest regenerate action (`POST /api/compass/regenerate`, `RegenerateConfirmModal`) | `CompassManifestStrip`'s regenerate button/modal | **Low, verified.** Spec explicitly leaves `compass_regenerate` untouched; UT-05 confirms live — modal opens, Cancel closes it, badges/version unchanged, DB row count for the date confirmed still 2 after cancel. |
| J-01, J-04, J-05, J-10, J-11 (required-still-passing journeys) | N/A — no shared frontend component, but these journeys read data whose engine module (`app/engine/compass.py`) was touched | **Low, verified.** Deterministic replay lane: 5/5 PASS (`phase-goal-market-compass-iter-27-regression-replay-results.md`). Dev handoff's 93/93 backend test run includes every J-06 test-list item these journeys depend on (time-safety, rebuild survival, reproducibility, create-once concurrency, cohort reproducibility, prospective-eligibility, availability-fence, tamper detection, hash-scope separation, disposition partition, schema conformance) — all unmodified and passing. |
| Every other route's self-heal (`/`'s own compass-summary/what-changed/focus cards via a different fetch, `/stocks`, `/sectors`, `/themes`, dashboard, market-phase) | `snapshot_serving.resolved_run`, `scanner.run_scan` | **None — confirmed byte-identical.** `git diff --stat` on `snapshot_serving.py`/`scanner.py` shows zero lines changed (dev handoff). The fix is scoped to the compass route's own call ordering only. |

No component shared with a prior-phase feature shows any behavior change beyond the one intended new
reachability. No "potential regression" flag applies.

## UI vs Backend Parity

| Backend capability | UI exposure |
|---|---|
| `basis.status == "unavailable"` reachable via `GET /api/compass` for a manifest whose source run was removed | **Fully surfaced.** The frontend already renders this exact state (iter-11 shipped code, unit-tested) — this iteration only fixes backend reachability; zero frontend changes were needed or made. Full parity: nothing the backend can now report is left unrendered. |
| `latest_manifest_for_date` helper / route reorder (internal control-flow only) | N/A — no independent externally observable behavior beyond the basis-status field above. |

No gap: this is the rare case where UI capability already exceeded backend reachability, and the
backend caught up to it. Nothing new needs to be built in the frontend.

## Flags

### Hidden Capabilities
None.

### Undiscoverable Capabilities
None. The affected badge sits on the home page (`/`) at 0 clicks, alongside its three sibling states.

### Potential Regressions
None identified. All components shared with prior-phase features (available/rebuilt badges, regenerate
button/modal, required-still-passing journeys J-01/J-04/J-05/J-10/J-11) were regression-tested live or
via deterministic replay and passed with byte-identical behavior to before this iteration.

### Visual Consistency
- New reachability uses only pre-existing, already-consistent design tokens (`danger` badge variant,
  used across health-badge, score-badge, market-phase-card, and multiple other pages) — no arbitrary
  values introduced, no new component authored.
- No frontend files changed this iteration, so there is no new page/component to check against the
  design system baseline.

### Standing Gaps (pre-existing, not caused by this iteration)
- `/market` (J-08) returns HTTP 404 — `apps/frontend/app/market/` does not exist. Unbuilt journey,
  unrelated to this iteration's backend-only compass route change. Re-flagged for visibility per the
  pump coordinator's note, not counted against this iteration's verdict.
- J-07 remains failing, also unrelated and untouched by this iteration.

## Recommendation

No action required for this iteration. The one substantive limitation — the "unavailable" badge cannot
currently be exercised through a live click-path because no qualifying as-of date exists in the
canonical database — is an honest, explicitly-scoped, and correctly-disclosed boundary (both in the
dev handoff and in QA's UT-04), not a UX defect: the badge is reachable in the running code the moment a
qualifying date exists, and its styling is already proven consistent elsewhere in the product. When a
future iteration is authorized to create (or naturally encounters) a frozen-manifest/missing-run
condition on the canonical DB, a browser screenshot of this exact badge would close the last piece of
live visual evidence, but that is a nice-to-have, not a blocking gap.

Carried forward for a future iteration's scope (not this one): J-08 (`/market`) is still unbuilt (404),
and J-07 is still failing — both pre-existing and explicitly out of scope here.
