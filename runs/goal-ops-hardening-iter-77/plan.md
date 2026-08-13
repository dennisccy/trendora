# goal-ops-hardening-iter-77 Execution Plan

## Context

Target journeys: J-04, J-07, J-09 (return fresh evidence). Required-still-passing: J-01, J-03,
J-05, J-06, J-08. Depth: **full** (mandatory — prior verdict ESCALATE; this is the engine's only
deterministic escape from the SPEED-9 evidence backstop that demoted iter-75/76 to empty-diff
evidence-only rounds). Frontend Present: **yes**.

This round exists specifically to restore the code lane after two consecutive empty-diff rounds.
Six concrete, disjoint items carry over from iter-72 through iter-76: (1) an un-root-caused
intermittent asset-less-frontend defect in `scripts/start-frontend.sh` (iter-72/c, quiet-but-
unfixed for 4 rounds), (2) the badge/banner's first `stale_for_s` UI consumer (the field has been
served by `GET /api/health` since iter-71 but never rendered), (3) a layout defect that hides the
"Ready" pill at 1280×800 when the background-compute chip is also shown (iter-76/e), (4) two
goldens (`J-07.json` step 4, `J-09.json` step 3) that need real `data-testid` selectors instead of
a fragile text-token match, (5) a walkthrough-recorder defect saving byte-identical before/after
frames (iter-76/d), and (6) three small housekeeping items (stale `goldens-regen-pending` listing,
a stray zero-byte `=` file, TC-7's fault-injection evidence capture). All six are independently
verifiable — a partial landing (e.g. the frontend-race fix lands but the badge annotation doesn't)
still produces real, checkable evidence, unlike the last two rounds.

No drift from `docs/goal.md`: this directly serves Key Capability 5 (distinguishable backend
states + persistent logfile — J-04) and Key Capability 3 (ingest-time aggregate maintenance
disclosure — J-07/J-09), and stays inside the explicitly frozen boundary — `app.engine.readiness`'s
cache/staleness/tick logic and `compute_forward_aggregates` are NOT touched; this iteration adds
only a UI consumer of an already-registered, already-served Data Contract field
(`stale_for_s: float >= 0`, blueprint.md's existing "Backend readiness" row) plus a test-hook
attribute on an already-displayed value (`scorecard.by_horizon[]`). Confirmed against the actual
code: `apps/frontend/lib/api.ts`'s `HealthStatus` interface does not yet declare `stale_for_s`,
`ReadinessContextValue` (`readiness-provider.tsx`) does not yet expose it, and neither
`health-badge.tsx` nor `preflight-banner.tsx` renders it — so this really is a net-new consumer,
not a duplicate.

## What to Build

- **Root-cause the intermittent asset-less-frontend defect** (`scripts/start-frontend.sh`). The
  script's own comment already flags that only *verification* builds are isolated via
  `NEXT_DIST_DIR` — the live-serving build-if-stale → `next build` → `next start` sequence has no
  lock against a SECOND concurrent invocation of the script racing on the SAME `.next` dist dir
  (one process's `next build` still writing while another's `next start` serves a partial payload).
  Instrument to confirm or rule out this specific mechanism first (per the iter-77 assumption-
  ledger entry); if instrumentation names a different cause, fix that instead. Either way: name the
  cause explicitly in the dev handoff, and close it with a lock/guard serializing the build → start
  sequence per dist-dir (e.g. a flock on a path derived from `$DIST_DIR`). Add a regression test
  (TC-2) that simulates or directly exercises two concurrent invocations and asserts the served page
  is always a fully-built payload, never mid-build.
- **Render `stale_for_s` on the readiness badge and preflight banner.** Thread the already-served
  `GET /api/health` field through the SAME single shared poll (no second fetch, no second endpoint):
  add `stale_for_s: number` to `HealthStatus` in `apps/frontend/lib/api.ts`; expose it on
  `ReadinessContextValue` in `readiness-provider.tsx` (populated from the shared `tick()`'s
  `fetchHealth()` call, mirroring how `warmup`/`preflight`/`backgroundCompute` are already threaded);
  render a short "as of {N}s ago"-style annotation in `health-badge.tsx` and `preflight-banner.tsx`,
  shown ONLY when `stale_for_s > 0` — no annotation for a synchronous/fresh compute
  (`stale_for_s === 0`) or when the health poll fails (`useReadiness()` surfaces `null`/error state
  honestly; never render a stale or fabricated number in that case).
- **Fix the badge-row layout so the "Ready" pill stays visible at 1280×800 alongside the
  "background compute running (N)" chip.** Root cause per the code read: `app/layout.tsx`'s header
  wraps `<AsOfSwitcher />` + `<HealthBadge />` in a single `flex flex-1 items-center justify-end
  gap-3` row with NO `flex-wrap`, while `HealthBadge`'s OWN internal row already uses `flex-wrap` —
  but that inner wrap only engages if the outer row constrains its width, which it doesn't, so at
  1280px the combined content (switcher + pill + chip + provider/seed/symbol badges) can overflow
  past the right edge instead of wrapping, effectively hiding earlier elements. Confirm this
  diagnosis with a real screenshot before fixing; the fix should let the badge row wrap onto a
  second line within the header (or otherwise guarantee the pill's visibility) without breaking the
  `h-14` sticky header on pages/widths where everything already fits. Verify with a 1280×800
  screenshot showing both the pill and the chip on-screen (TC-5).
- **Strengthen the J-07/J-09 goldens.** `apps/frontend/app/backtest/page.tsx`'s `ScorecardSection`
  (line ~559, reading `data.scorecard.by_horizon`) needs `data-testid="scorecard-row-<horizon>d"` on
  each rendered per-horizon row. Then update
  `runs/goal-session-ops-hardening/journey-scripts/J-07.json` step 4 (currently a bare `{"type":
  "expect", "text": "1d"}` token match) to assert
  `[data-testid="scorecard-row-1d"]` instead. `J-09.json` step 3 already uses a real CSS selector
  (`[data-testid="background-compute-idle"], [data-testid="background-compute-active-row"]`, per
  spec this was strengthened at iter-76 but never executed) — no golden edit needed there, just run
  it through the deterministic replay lane this round as proof.
- **Fix the walkthrough recorder's before/after capture** (`scripts/automation/lib/demo_runner.py`
  — `_settle_for_capture` at line ~1432 plus its call sites around lines 1671/1782/1917 in the
  walkthrough-recording path). Today the "after" screenshot for a state-changing step appears to be
  taken on a fixed settle timeout that fires whether or not the state change has actually landed in
  the DOM, producing byte-identical before/after frames (iter-76/d). Fix it to wait for a concrete
  signal that the change is visible (e.g. poll for the expected post-action DOM state within a
  budget, not just a blind `wait_for_timeout`) before capturing. Add a unit test (TC-9) asserting
  before/after frames differ when the underlying state genuinely differs (e.g. a J-05 backfill
  before/after).
- **Housekeeping (small, disjoint, ride-along per spec rule 7):**
  - Clear `runs/goal-session-ops-hardening/state/goldens-regen-pending` of its stale J-05..J-09
    listing once this round confirms all five still pass on their current/strengthened goldens.
  - Delete the stray zero-byte `=` file at the repo root; `grep -r` first to confirm nothing
    references it (nothing found in the current codebase check).
  - Capture the TC-7 `/data` honest-fallback live-browser evidence for
    `TRENDORA_FAULT_INJECT_MEMORY_ERROR=data_overview_endpoint` (the deliberately-unguarded hook at
    `apps/backend/app/api/data.py:119`, `data_manager._fault_inject_memory_error`) — screenshot the
    honest fallback copy, file it as evidence; do not remove the hook.

## Agents Required

- backend-data: yes — the `start-frontend.sh` race investigation/fix and its regression test are
  shell + Playwright/pytest-level work; the `data-testid` selector plumbing touches a React
  component but the golden JSON edits and TC-7 evidence capture are harness-level.
- frontend-ux: yes — `stale_for_s` badge/banner rendering (`health-badge.tsx`,
  `preflight-banner.tsx`, `readiness-provider.tsx`, `lib/api.ts`), the 1280px layout fix
  (`layout.tsx` + `health-badge.tsx`), and the `scorecard-row-<horizon>d` testid
  (`app/backtest/page.tsx`).

## Frontend Present: yes

## Files to Create/Modify

- `scripts/start-frontend.sh` -- add a lock/guard serializing build-if-stale → `next build` →
  `next start` per dist-dir (or fix whatever different cause instrumentation names); do not touch
  the existing HOST-GUARD block.
- `apps/backend/tests/test_start_frontend_script.py` (create if it does not already exist; check
  first) -- TC-1 (5 consecutive fresh launches, zero asset-less occurrences) and TC-2 (concurrent-
  invocation race regression test).
- `apps/frontend/lib/api.ts` -- add `stale_for_s: number` to the `HealthStatus` interface (no new
  endpoint, no field rename).
- `apps/frontend/components/readiness-provider.tsx` -- add `staleForS: number | null` to
  `ReadinessContextValue`, populated from the SAME shared `tick()` poll.
- `apps/frontend/components/health-badge.tsx` -- render the "as of {N}s ago" annotation when
  `staleForS > 0`; participate in the layout fix.
- `apps/frontend/components/preflight-banner.tsx` -- render the same annotation on the banner under
  the same condition.
- `apps/frontend/app/layout.tsx` -- header row layout fix so the readiness pill stays visible at
  1280×800 alongside the background-compute chip.
- `apps/frontend/app/backtest/page.tsx` (`ScorecardSection`, ~line 559) -- add
  `data-testid="scorecard-row-<horizon>d"` per rendered row.
- Frontend component/unit tests (Jest/RTL, exact file per existing convention — check
  `apps/frontend/**/__tests__` or co-located `*.test.tsx` before creating a new file) -- staleness
  annotation rendering (shown/hidden per `stale_for_s`), the 1280px layout assertion, and the
  scorecard testid presence.
- `runs/goal-session-ops-hardening/journey-scripts/J-07.json` -- step 4: replace the `"1d"` text
  match with the `scorecard-row-1d` selector.
- `scripts/automation/lib/demo_runner.py` -- fix `_settle_for_capture` / its walkthrough call sites
  so "after" captures wait for the actual DOM change, not a blind timeout.
- `scripts/automation/tests/` (or wherever `demo_runner.py`'s own `_t_*` unit tests live, in-file
  per the existing convention) -- TC-9: before/after frames differ when state differs.
- `runs/goal-session-ops-hardening/state/goldens-regen-pending` -- clear the stale listing.
- Repo root `=` file -- delete (after confirming no references).
- `docs/handoffs/goal-ops-hardening-iter-77-dev.md` -- dev handoff (required by DoD), naming the
  frontend-race root cause explicitly.

## UI Evolution

- New user-facing capability: anyone viewing the readiness badge or preflight banner during a
  background-compute window can now see how stale the displayed status is; the "Ready" pill no
  longer disappears at common viewport widths while a compute chip is shown.
- New information displayed: `stale_for_s` as a short "as of {N}s ago" annotation on the badge and
  banner.
- New user actions: none — both surfaces stay read-only status displays.
- UI surface changes: global readiness badge (every page, top bar) and preflight banner gain the
  staleness annotation + layout fix; `/backtest`'s scorecard rows gain a stable `data-testid` with
  no visible change.
- Navigation changes: none.

## Visual Requirements

- Component patterns: reuse the existing `Badge` component (`components/ui/badge.tsx`) and its
  existing variant convention (`default`/`ok`/`warn`/`accent`/`danger`) — the staleness annotation
  is inline text within/near the existing pill, not a new component type.
- Layout: keep the sticky `h-14` header; the fix must let the badge row's content wrap or otherwise
  stay visible within the header at 1280×800 rather than overflowing off-screen — do not remove the
  existing `flex-wrap` already present inside `HealthBadge`, extend the wrapping behavior to the
  outer row that currently blocks it.
- Key visual effects: none new — factual, calm text annotation matching the existing "never hype"
  copy convention (no color change, no animation) for the staleness note.
- States to handle: no annotation when `stale_for_s === 0` (fresh/synchronous) or when the health
  poll fails (`state === null`/`unavailable` — never show a stale or fabricated number); the
  1280px layout must hold with 0, 1, and multiple simultaneous badges/chips present.

## Key Test Scenarios

- TC-1: 5 consecutive fresh `start-frontend.sh` launches (no concurrent invocation) each serve a
  fully-styled `/` with zero asset-less occurrences.
- TC-2: two concurrent `start-frontend.sh` invocations against the same `.next` dist dir never
  serve a partial/mid-build payload — regression test exercises or simulates the race directly.
- TC-3/TC-4: `stale_for_s > 0` renders the "as of {N}s ago" annotation on both badge and banner,
  `stale_for_s === 0` renders none, and the rendered value matches the raw `GET /api/health` JSON
  for the same poll exactly (AG-3).
- TC-5: 1280×800 viewport with a background-compute window in flight — screenshot shows both the
  "Ready"/status pill AND the "background compute running (N)" chip on-screen simultaneously.
- TC-6: `/backtest`'s populated scorecard rows each carry `data-testid="scorecard-row-<horizon>d"`
  matching configured horizons.
- TC-7: J-07.json step 4 and J-09.json step 3 both PASS via deterministic replay against this
  iteration's fresh frontend build (replay timestamp postdates the deploy).
- TC-8: `TRENDORA_FAULT_INJECT_MEMORY_ERROR=data_overview_endpoint` armed → `/data` renders the
  honest-fallback copy ("Dataset coverage could not load from the API. No figures are shown rather
  than fabricated"), screenshot captured and filed.
- TC-9: walkthrough recorder's before/after frame pair for a journey whose state genuinely changes
  (e.g. J-05 backfill) are NOT byte-identical.
- TC-10: `state/goldens-regen-pending` is cleared of the stale J-05..J-09 listing once all eight
  journeys confirm passing.
- TC-11: the stray `=` file no longer exists; no test/script references it.
- TC-12: full required-still-passing regression (J-01, J-03, J-05, J-06, J-08) shows no regression
  via deterministic replay; any FAIL is corroborated by an LLM re-check citing an opened frame and
  timestamp bracket before a "transient/environment" label is accepted (iter-73/iter-76 lesson).
- Target journeys J-04, J-07, J-09 pass via browser-qa-agent with fresh (non-carried) evidence for
  the badge annotation, badge layout, and scorecard testid surfaces this iteration changed.

## Out of Scope (matches phase spec's own OUT OF SCOPE — no drift)

- iter-33/g, the Regime Lab — deferred again, needs owner direction.
- Any change to `app.engine.readiness`'s cache/staleness/tick logic or to
  `compute_forward_aggregates` — both frozen; this iteration only adds a UI consumer of already-
  served output.
- Re-running J-07 step 3 (VmPeak/margin) or step 4 (induced-pressure drill) as a fresh drill —
  carried per iteration-state; evaluator's call given this round's non-empty diff.
- Re-running J-08's or J-09's full database-cross-check acceptance drill — already done fresh at
  iters 75/76; this round's J-09 pass only confirms the badge/layout change doesn't disturb the
  already-verified disclosure.
- Owner-blocked items: the 2-second health-ceiling scope, B-1107's concurrency cap, sign-off to
  edit `browser-qa-phase.sh`, and the finish-now-vs-housekeeping-first policy question.
- Regenerating any golden script content beyond the two named selector upgrades (J-07 step 4) —
  golden regeneration is never the right remedy for a harness/environment defect (iter-73 lesson).
- The remaining ~60-item "CARRIED, untouched" backlog (iter-29/b onward) — none is a regression or
  an unblocker for J-04/J-07/J-09.
