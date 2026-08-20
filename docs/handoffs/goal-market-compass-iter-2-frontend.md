# goal-market-compass-iter-2 Frontend Handoff

**Phase:** goal-market-compass-iter-2
**Date:** 2026-08-20
**Agent:** developer
**Status:** complete

## What Was Built

Three new Today-page (`/`) sections (J-02/J-03/J-04) and one new `/methodology` disclosure card, all
reading ONLY the new `GET /api/compass` (and, for methodology, `GET /api/methodology`) endpoints — no
client-side threshold comparison, delta computation, or word selection anywhere.

- **`CompassSummaryCard`** (`apps/frontend/components/compass-summary-card.tsx`) — J-03. Renders
  `compass.narrative.sentences` verbatim (state/direction/breadth/focus-count, plus the retrospective
  stamp when present) inside a "Summary" card, with a "Show cited facts" `Disclosure` listing each
  sentence's `template_id` and its named facts. No wording is assembled client-side.
- **`CompassWhatChangedCard`** (`compass-whatchanged-card.tsx`) — J-02. Header names the prior session's
  date + day gap (when one exists); an ordered change list (kind `Badge` + label + a link to the
  server-supplied `drill_href`, which already carries `?asof`, + from→to values); the explicit
  no-prior-run empty state; the quiet-pair "No meaningful changes this session." state; a
  "Suppressed moves (N)" `Disclosure` listing each suppressed entry's magnitude vs. threshold.
- **`CompassFocusSection`** (`compass-focus-section.tsx`) — J-04, the largest of the three. Each
  candidate card shows the three served word+score pairs (`leadership_word`/`entry_word`/`risk_word`,
  each paired with its raw score — there is no bucket letter in this payload, per the exact data
  contract, so `ScoreBadge` is not used here), the `reasons` list, the `cautions` list (rendered in
  `text-warn`), an "Eligibility checklist" `Disclosure` (condition, actual vs threshold, and a `Badge`
  colored by the served `verdict`), a "What would change this" `Disclosure` (condition, actual vs
  threshold, met/not-met), and the `invalidation` note verbatim. Below the candidate grid, a
  "Not priority (N)" `Disclosure` renders every why-not entry's `failed_conditions` with their
  `distance`, or an honest "passed every qualifier, cut only by the focus-list cap" line when
  `failed_conditions` is empty. **Code-audit note (TC-18)**: `compass-focus-section.tsx:70-93`
  (checklist + what-would-change rendering) maps ONLY over served `condition`/`threshold`/`actual`/
  `verdict`/`met` fields — grep confirms no threshold literal or rule table exists anywhere in this
  file.
- **Shared `Disclosure`** (`apps/frontend/components/ui/disclosure.tsx`) — extracted from `page.tsx`'s
  previously-local `<details>` component. It was about to gain a 3rd/4th call site with the three new
  cards above (rule of three), so this is a right-sized extraction: `page.tsx` now imports it from
  `@/components/ui/disclosure` instead of defining it inline; its two pre-existing call sites (the
  Market Regime and Market Phase glance cards' "Why this ... — component breakdown" disclosures) are
  functionally and visually unchanged.
- **`apps/frontend/app/page.tsx` wiring** — `DashboardPage`'s existing effect gained a fifth,
  independently-tolerant fetch (`fetchCompass`, alongside the pre-existing `phase`/`sectors`/`themes`
  fetches — same try/catch-to-`null` pattern, same as-of). The three new components are rendered as
  siblings ABOVE `<DashboardBody .../>`, which is called with the exact same props as before (a code
  diff shows its own function definition is untouched) — satisfying "rendered above the existing,
  unmodified dashboard body" both visually and by construction. Loading state is the existing full-page
  `DashboardSkeleton`; each new card independently renders its own honest "... is unavailable — backend
  not reachable" state when `compass` resolves to `null` (its own fetch failed) even though the rest of
  the page loaded fine.
- **`apps/frontend/lib/api.ts`** — `CompassResponse` and every nested type (`SessionDelta`,
  `SessionDeltaChange`, `SessionDeltaSuppressed`, `NarrativeFact`, `NarrativeSentence`, `Narrative`,
  `ChecklistVerdict`, `ChecklistRow`, `WhatWouldChangeRow`, `CompassCandidate`,
  `WhyNotFailedCondition`, `WhyNotEntry`, `CompassSelection`) plus `fetchCompass(asof?, signal?)`,
  following the exact `getJSON(withAsOf(...))` pattern every other as-of-aware fetcher already uses.
  Also added `CompassSelectionBasis` and `MethodologyCatalog.compass_selection` for the methodology
  card below.
- **`apps/frontend/app/methodology/page.tsx`** — new `CompassSelectionCard` component, an exact
  structural mirror of the existing `SectorBasisCard` (same `Card`/icon/`Badge` header shape,
  `data-testid="compass-selection-basis"`), additionally rendering the served `thresholds` list via the
  SAME `ThresholdRow` component every other threshold list on the page already uses. Rendered
  unconditionally right after `SectorBasisCard`, gated only on `state.data.compass_selection` being
  present (never on the J-22 universe-screen gate, matching `SectorBasisCard`'s own precedent).

## Files Changed

- `apps/frontend/lib/api.ts` -- new types + `fetchCompass`; `CompassSelectionBasis` + `MethodologyCatalog.compass_selection`
- `apps/frontend/components/compass-summary-card.tsx` -- new
- `apps/frontend/components/compass-whatchanged-card.tsx` -- new
- `apps/frontend/components/compass-focus-section.tsx` -- new
- `apps/frontend/components/ui/disclosure.tsx` -- new, extracted from `page.tsx`
- `apps/frontend/app/page.tsx` -- fetch `compass`, render three new sections above unchanged `DashboardBody`, import shared `Disclosure`
- `apps/frontend/app/methodology/page.tsx` -- new `CompassSelectionCard`

## Tests Run

Command: `cd apps/frontend && node_modules/.bin/tsc --noEmit` (the established project convention —
there is no `npm test`/unit-test framework in this frontend).
Result: clean, zero type errors across the whole project (all new files + every existing file that
imports them).

`npm run lint` (`next lint`) was attempted but this project's own build guard
(`next.config.mjs:116`) refuses to run without `NEXT_PUBLIC_API_URL` set / a throwaway dist dir — this
is a pre-existing project guard unrelated to this change, and `tsc --noEmit` is the documented
verification command per prior dev handoffs' own precedent, so lint was not separately run.

Live browser verification (via `superpowers-chrome` against `./scripts/dev.sh`'s real dev boot, port
3255, backend 8255, real committed seed data, 591 symbols, as-of 2026-08-12):
- `/` — all three new cards render correctly above the pre-existing dashboard body; zero console
  errors (only the routine React DevTools notice); "Show cited facts" and "Not priority (20)"
  disclosures both expand and render correct, matching content (spot-checked against the raw
  `GET /api/compass` JSON).
- `/methodology` — the new "Next-session focus" card renders with its four live-resolved thresholds;
  glossary search for "why-not" returns exactly the new `today_compass`-category term.
- Screenshots captured during this session (not committed; local verification artifacts only).

## Known Issues

- The Next-session focus section currently renders its honest EMPTY state against the live latest run
  (2026-08-12) — zero candidates clear the combined leadership+entry+risk qualifier bar today (see the
  backend dev handoff's Known Issues #1 for the full analysis; this is a real, spec-prescribed threshold
  outcome, not a frontend bug). The empty-state rendering itself (`CompassFocusSection`'s
  `candidates_empty_reason` branch) IS live-verified and correct. Browser-qa-agent will need a
  synthetic/historical as-of fixture to exercise the populated candidate-card UI (checklist badges,
  cautions, what-would-change panel) — TC-21 already anticipates exactly this kind of fixture need.
- No frontend unit-test framework exists in this project (confirmed via `package.json`'s `scripts`
  block: only `dev`/`build`/`start`/`lint`); `tsc --noEmit` plus live browser verification is this
  iteration's full frontend verification, consistent with prior iterations' own precedent.
