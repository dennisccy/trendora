# goal-ops-hardening-iter-16 Frontend Handoff

**Phase:** goal-ops-hardening-iter-16
**Date:** 2026-07-23
**Agent:** developer
**Status:** complete (code + type-check; browser verification pending — see "Known Issues")

## What Was Built

- **`evidence_status` / `evidence_generated_at` disclosure on the existing `/backtest` page.** No new
  page, panel, or route — the existing bottom evidence section (`EvidenceAggregateSection`, rendered by
  `BacktestResults` in `app/backtest/page.tsx`) now honestly discloses whether the forward-tested evidence
  it's showing is the current version (`ready` — unchanged rendering, regression guard), a labeled
  last-good PRIOR version while a newer one warms in the background (`refreshing` — new banner), or has
  never been computed at all for this date (`not_yet_computed` — new empty state, replacing today's
  silent `{evidence ? (...) : null}` omission).
- **New small presentational component: `RefreshingEvidenceBanner`** (`app/backtest/page.tsx`, local to
  this file — not exported, single call site). Renders ABOVE the still-fully-populated evidence section
  (never replacing it, never a skeleton) when `evidence_status === "refreshing"`: a `Card` + spinning
  `Loader2`, warn-toned (`border-warn`/`text-warn`), reading "Refreshing — showing the last complete
  evidence" plus the served generation timestamp (`evidence_generated_at`, formatted via the EXISTING
  `formatIsoDateTime` helper from `lib/dates.ts` — no new date-formatting logic).
  - This deliberately borrows `WarmingState`'s / this same page's `SurvivorshipBanner`'s established
    Card+Loader2 warn-toned LOOK as a visual reference only. It is **NOT** wired to `useReadiness()` — that
    hook is a distinct, boot-time warm-up concept (whether the background historical cadence warm-up has
    finished); this banner is about a single request's OWN served-evidence-version disclosure, which can
    be `refreshing` long after boot warm-up has completed. Reusing `useReadiness()` here would have been
    semantically wrong, not just redundant.
- **`not_yet_computed` → the existing `EmptyState` component**, reused via its `title`/`description`/
  `icon` props (the SAME component this page already calls in `ScorecardSection`, so no new dashed-border
  empty-state pattern was invented). Renders IN PLACE of the evidence section (where the silent
  `{evidence ? (...) : null}` used to render nothing), reading "Backtest evidence not yet computed — run
  an ingest to populate the forward-tested evidence for this date. No numbers are fabricated in the
  meantime."
- **`ready` state is visually unchanged** — no banner, no empty state, the evidence section renders
  exactly as it did before this iteration (regression guard, TC-12).
- **`lib/api.ts`** — `BacktestResponse` gains the two new fields (typed as a literal union
  `"ready" | "refreshing" | "not_yet_computed"` for `evidence_status`, so a typo/new state value would be
  a compile error, not a silent runtime string mismatch).

## Audit correction (2026-07-23, auditor pass — supersedes the banner body copy described above)

The `RefreshingEvidenceBanner`'s BODY copy was corrected during the audit. Its heading
("Refreshing — showing the last complete evidence"), tone, `data-testid`, Card/`Loader2` treatment and
position (above the still-populated evidence section) are UNCHANGED — only two sentences that asserted
facts the system cannot know were replaced:

- removed *"A newer dataset version is still being warmed."* — `refreshing` only means the current
  `_dataset_version` stamp differs from the served (complete) version's stamp. Any new `ScannerRun` /
  `ForwardReturn` row bumps that stamp (`research.py:1532`), so this state persists with **no warm
  running at all** and does not self-heal.
- removed *"This updates automatically once the new version finishes warming"* — `BacktestPage`'s only
  effect depends on `[asOf, readiness]` (`page.tsx:73-92`) and `readiness` is a plain string that does
  not change while the backend stays `ready`; there is no poll. The page updates on a reload / as-of
  change only (browser QA's own UT-04 needed a reload).

The replacement states only what the resolver knows plus an accurate instruction. See
`docs/handoffs/goal-ops-hardening-iter-16-audit.md` finding F1. `npx tsc --noEmit` re-run: 0 errors. The
new wording has NOT been re-screenshotted in a browser (services were down at audit time) — the UT-02
screenshot still shows the old body text.

## New user-facing capability

None new to WHAT a user can DO — this is a read-only status disclosure. A user now SEES an honest, labeled
signal for whether the Backtest evidence panel is showing a slightly-stale-but-labeled prior version
during a dataset refresh, or an explicit "not yet computed" message on a never-warmed store — instead of
either an invisible multi-minute wait blocking the page (the OLD cold-MISS behavior this iteration's
backend half eliminates) or a silently-blank section with no explanation.

## Files Changed

- `apps/frontend/lib/api.ts` -- `BacktestResponse` interface gains `evidence_status` (literal union) and
  `evidence_generated_at` (`string | null`), each documented inline.
- `apps/frontend/app/backtest/page.tsx` --
  - Added `Loader2` to the existing `lucide-react` import.
  - Added `formatIsoDateTime` to the existing `@/lib/dates` import.
  - `BacktestResults`'s bottom evidence-section render block restructured into a 3-way branch on
    `backtest.evidence_status` (see "What Was Built").
  - New local component `RefreshingEvidenceBanner`.

## Visual / Design System compliance

- Component library only: `Card` (existing `components/ui/card`), `Loader2` icon (`lucide-react`,
  already used elsewhere on this page for `WarmingState`) — no raw `<div>` soup, no new UI primitive.
- Color tokens only: `border-warn` / `text-warn` (refreshing banner, matching `WarmingState`/
  `SurvivorshipBanner`'s existing warn treatment) and `border-dashed border-border-strong` /
  `text-text-faint` / `text-text` / `text-text-muted` (via the existing `EmptyState` component's own,
  unmodified styling) — no arbitrary hex/pixel values introduced.
- Typography/spacing: reuses the existing `text-sm`/`space-y-1`/`gap-3`/`p-4` scale already used by the
  sibling `WarmingState`/`SurvivorshipBanner` components on this same page — no new scale values.
- Motion: `animate-spin` on `Loader2`, the SAME treatment `WarmingState` already uses for its own spinner
  — no new transition/animation introduced.
- Responsive: no new breakpoint-sensitive layout — the banner and empty state both render as simple
  full-width blocks inside the page's existing `space-y-4` column, matching every other section on this
  page (`SurvivorshipBanner`, `WarmingState`, `ScorecardSection`'s own `EmptyState` use).
- States handled: `ready` (unchanged, TC-12), `refreshing` (banner + populated section, TC-10),
  `not_yet_computed` (empty state, no horizon numbers, rest of page — scorecard, leadership lists, as-of
  scan summary — unaffected since none of those read `evidence_by_horizon`, TC-11). Loading/error states
  for the PAGE overall (`BacktestSkeleton`, the "Backend unavailable" card) are pre-existing and untouched
  — this iteration only touches what happens once a response HAS arrived.

## Tests Run

- `cd apps/frontend && npx tsc --noEmit -p tsconfig.json` — **0 errors.** No new dependency was added; no
  `package.json`/build-config change was needed.
- No frontend test runner is configured in this project beyond ad hoc `node <file>.test.ts` scripts for
  pure `lib/*.ts` utilities (confirmed via `package.json` — no `"test"` script, no jest/vitest
  devDependency) and none of the existing `.test.ts` files exercise React components — there is no
  existing harness to unit-test `backtest/page.tsx` against, and building one is out of this iteration's
  scope. Verification for the new UI states is via the backend-level tests
  (`test_forward_testing_serving_split.py`'s `test_backtest_route_is_latest_never_reaches_ingest_or_compute`
  /`..._not_yet_computed_is_honest_200` prove the exact response shapes the frontend branches on) plus the
  manual "What to Click" steps below, pending live browser verification (see "Known Issues").

## Known Issues

1. **No live browser verification this session.** Services are down and agents cannot start them this
   session (see the backend dev handoff's "Known Issues" #2 for the full operational constraint). The
   TypeScript compiles cleanly and the exact response shapes the three branches key off
   (`evidence_status`/`evidence_by_horizon`/`evidence_generated_at`) are proven correct at the backend
   layer, but the actual RENDERED banner/empty-state have not been screenshotted or DOM-asserted in a real
   browser this session. **Manual verification once the operator has services running** (this doubles as
   TC-10/TC-11/TC-12's browser-qa evidence):
   - **`ready` (TC-12):** load `/backtest` with a warm backend — confirm no refreshing banner and no
     "not yet computed" empty state appear; the forward-tested evidence section renders its normal
     populated numbers exactly as before this iteration.
   - **`refreshing` (TC-10):** on `/data`, start a small single-day backfill; while its finalize warm is
     still running, load/reload `/backtest` — confirm a warn-toned banner reading "Refreshing — showing
     the last complete evidence" plus a generation timestamp appears ABOVE the still-fully-populated
     evidence section (never a spinner in place of it).
   - **`not_yet_computed` (TC-11):** on a store where no forward-aggregate warm has ever completed for the
     latest date (a fresh install, or a from-scratch test DB) load `/backtest` — confirm the empty state
     reading "Backtest evidence not yet computed" appears in place of the evidence section, with no
     horizon numbers, while the scorecard / leadership lists / as-of scan summary above render normally.
2. **`evidence_generated_at`'s exact wall-clock display was not screenshotted.** `formatIsoDateTime`
   renders `yyyy-MM-dd HH:mm:ss`; this is the SAME formatter already used elsewhere in the codebase for
   run/scan timestamps, so no new formatting risk is expected, but this specific call site is new.

## What to Click (operator manual test)

1. Start the backend (`scripts/start-backend.sh`) and frontend (`scripts/start-frontend.sh`), never
   `dev.sh` per this iteration's measurement conditions.
2. Navigate to `/backtest`. Confirm the bottom "Forward-tested evidence" section renders its normal
   numbers with no banner above it (the `ready` state — unchanged from before this iteration).
3. Navigate to `/data`. Pick a trading day the coverage panel shows as not-yet-snapshotted; start a
   `backfill` job for just that one day; watch its progress panel.
4. While that job is still running, navigate back to `/backtest` (or reload it). Confirm a small warn-
   toned card now appears directly above the evidence section, reading "Refreshing — showing the last
   complete evidence" with a timestamp — and that the evidence section below it still shows real numbers
   (not blank, not a spinner).
5. Wait for the `/data` job to finish, then reload `/backtest` again. Confirm the refreshing banner is
   gone and the evidence section shows the SAME kind of populated numbers as step 2 (now the NEW version).
