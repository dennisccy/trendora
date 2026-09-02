# Phase goal-market-compass-iter-39 — UI Surface Map

**Phase:** goal-market-compass-iter-39
**Date:** 2026-09-02
**Written by:** ui-impact-analyst

---

## File Classification

| File | Category | UI Impact | Explanation |
|------|----------|-----------|-------------|
| `apps/frontend/lib/api.ts` | frontend-direct (shared TS data contract) | direct | Widens `CompassSelection.why_not_totals` and `WhyNotEntry.reason`/`.cap_rank`/`.cap` from required to optional. This is the type file every compass-consuming component imports; the widening itself renders nothing, but it is what makes the downstream guard fix (below) type-check and is the root of the crash it repairs. |
| `apps/frontend/components/compass-focus-section.tsx` | frontend-direct | direct | The "Not priority" `Disclosure` summary in the Next-session focus card now calls a new guarded helper instead of dereferencing `selection.why_not_totals.excluded_by_cap_uncapped` unguarded. This is the actual crash fix and the one place the visible text differs. |
| `apps/frontend/lib/why-not-summary.ts` (new) | frontend-direct (pure helper, no JSX) | direct (backs the row above) | New pure function `whyNotSummary()` producing the exact disclosure string for both the degraded and fully-counted cases. Not itself rendered; imported only by `compass-focus-section.tsx`. |
| `apps/frontend/lib/why-not-summary.test.ts` (new) | test (no direct UI) | none | Plain-node fixture test (TC-14) for `whyNotSummary()`. Verifies the string logic; does not render anything a user sees. |
| `runs/goal-session-market-compass/journey-scripts/J-04.json`, `J-05.json`, `J-06.json`, `J-07.json` | test-infrastructure (QA golden scripts) | none | Restored byte-exact to pre-iter-38 content (undoing the iter-38 same-day edits that had moved their target dates/steps). These are automated-test fixtures consumed by the deterministic replay lane, not application code — no UI surface is affected by this restoration itself, but it corrects which URLs/text the automated regression suite checks against. |
| `runs/goal-session-market-compass/state/blueprint.md` | config/docs | none | Additive iter-39 note recording that the frontend TS interface's optionality now matches what was always true of the stored data. Documentation only. |

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/` | Whole Today page render (state band, summary, what-changed, rotation, focus section, manifest strip) | Bug fix / regression repair | iter-38 declared `why_not_totals`/`reason`/`cap_rank`/`cap` as required TS fields, but `/api/compass` replays each stored manifest verbatim and 34/36 stored rows (21/23 distinct dates) predate those fields — the unguarded read threw and the whole page fell to the `error.tsx` boundary (AG-8 violation) | Navigate to `http://localhost:3255/?asof=2026-08-11`; verify the page renders the "Market state" band, summary card, "What changed" card, leadership rotation card, "Next-session focus" card, and manifest strip in full, with NO "Something went wrong on this page" card visible anywhere on the page |
| `/` | `CompassFocusSection` — "Not priority" `Disclosure` summary, pre-iter-38 date | Changed behavior (new text variant) | New `whyNotSummary()` helper renders an honest degraded string instead of crashing when `selection.why_not_totals` is `undefined` | On `http://localhost:3255/?asof=2026-08-11`, locate the "Not priority (...)" disclosure summary text inside the "Next-session focus" card and verify it reads exactly `Not priority (20 shown — held-back counts unavailable for this manifest version)` |
| `/` | `CompassFocusSection` → `WhyNotList` → `WhyNotLeadIn`, pre-iter-38 date | Changed behavior (guard confirmed safe, no code change) | `entry.reason`/`.cap_rank`/`.cap` are now optional; the existing `entry.reason !== "excluded_by_cap"` check already short-circuits safely on `undefined` | On `http://localhost:3255/?asof=2026-08-11`, click the "Not priority (...)" summary to expand it; verify each listed ticker's entry shows its `failed_conditions` list (or its own empty text) with NO "— ranked #N of the above-floor names, cap ..." lead-in sentence, and no error is thrown (page stays rendered) |
| `/` | `CompassFocusSection` — "Not priority" `Disclosure` summary, post-iter-38 (frontier) date | Regression check (unchanged) | Confirms the fix introduces zero visible change on the one manifest that already carries `why_not_totals` | Navigate to `http://localhost:3255/?asof=2026-08-12`; verify the "Not priority" summary reads exactly `Not priority (20 shown of 52 held back — 27 cap-excluded, 25 below-floor near-miss)`, byte-identical to before this fix |
| `/` | `CompassFocusSection` → `WhyNotList` → `WhyNotLeadIn`, post-iter-38 (frontier) date | Regression check (unchanged) | Confirms the "ranked #N" lead-in still renders on the one manifest version that has the data | On `http://localhost:3255/?asof=2026-08-12`, expand "Not priority" and verify at least one entry shows a "— ranked #N of the above-floor names, cap 20" lead-in sentence with a real rank and cap number |
| `/` (looped) | Whole Today page render, all 21 previously-crashing dates | Bug fix / regression repair (breadth check) | TC-3 requires the fix be proven across every previously-crashing date, not a sample | In a scripted loop, load each of `http://localhost:3255/?asof=<date>` for the 21 dates listed in the user-visible-changes report; verify none shows the "Something went wrong on this page" card and `curl http://localhost:8255/api/compass?as_of=<date>` returns HTTP 200 for each |
| `/market` | Full page (regime × phase, sectors, themes) | Regression check (unchanged) | J-08 requires `/market` still renders its full former inventory unchanged after this fix, since it consumes the same `CompassResponse` shape indirectly via navigation from `/` | From `http://localhost:3255/?asof=2026-08-10`, click the "Full market context (regime × phase, sectors, themes)" link (`data-testid="compass-state-band-market-link"`) in the "Market state" card; verify it navigates to `http://localhost:3255/market?asof=2026-08-10` and the page renders sector/theme content with no error card |

---

## Backend-Only Changes (No UI Impact)

- `runs/goal-session-market-compass/journey-scripts/J-04.json`, `J-05.json`, `J-06.json`,
  `J-07.json` — restored byte-exact to HEAD `ab3cca63` (undoing iter-38 same-day edits that had
  moved their target dates/assertions/step counts) — these are automated QA replay fixtures, not
  application code; no UI surface is affected by the restoration itself.
- `runs/goal-session-market-compass/state/blueprint.md` — additive documentation note recording
  the TS-interface optionality correction — no UI surface affected.
- No backend (`apps/backend/`) source file changed this iteration — `evaluate_selection` and
  `_select_why_not_display` in `app/engine/compass.py` were confirmed correct and left untouched,
  per the spec's explicit "Do not redo" instruction.

---

## Summary

- **Frontend surfaces changed:** 1 route (`/`), all within the existing "Next-session focus" card.
- **New pages/routes:** 0.
- **Modified components:** 1 (`CompassFocusSection`'s "Not priority" `Disclosure`, via the new
  `apps/frontend/lib/why-not-summary.ts` helper); the shared type file `apps/frontend/lib/api.ts`
  also changed but renders nothing itself.
- **Navigation changes:** no.
- **Backend-only changes:** 0 backend source files; 2 non-UI artifacts (4 restored QA golden
  scripts counted as one restoration batch, 1 doc note) with no UI impact.
