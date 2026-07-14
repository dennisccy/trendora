# Phase goal-mcp-loop-iter-33 — UX Regression Review

**Date:** 2026-07-14

**Verdict:** UX-REGRESSION-PASS

---

## Summary

J-20 (backlog B-301) ships one canonical daily preflight verdict (`GO`/`DEGRADED`/`NO-GO` + plain-language
reasons), computed once on the backend and rendered as a layout-level `PreflightBanner` mounted a single
time in `apps/frontend/app/layout.tsx`. This review independently re-verified the claims in the dev/frontend
handoffs and the browser-QA report against the actual diffs and component source (not just the prose) —
`git diff` on `app/layout.tsx`, `readiness-provider.tsx`, `health.py`, plus a full read of the new
`preflight-banner.tsx` and the untouched `health-badge.tsx`. Every claim checked out. No hidden or
undiscoverable capability, no confirmed regression, no UI/backend parity gap beyond what goal.md explicitly
scopes out for this iteration.

## New Capability Discoverability

**Capability:** the daily preflight verdict banner (`GO`/`DEGRADED`/`NO-GO` + reasons).

- **Navigation path:** none needed — and that is correct, not a gap. This is cross-cutting layout chrome,
  the same category as the pre-existing `HealthBadge`, not a page or feature a user navigates to. It is
  mounted exactly once in the root layout (`git diff apps/frontend/app/layout.tsx` shows a 2-line addition:
  one import + `<PreflightBanner />` inserted between `</header>` and `<main>`), and `layout.tsx` is
  confirmed the only `layout.tsx` under `apps/frontend/app/`, wrapping all 27 routes. The banner therefore
  appears on **0 clicks** from any page load — a stronger discoverability posture than the 2-click bar this
  review normally applies, because no click is required at all.
- **Label clarity:** plain-language, non-technical throughout — "GO — today's board is current.",
  "DEGRADED — treat today's board with caution.", "NO-GO — do not rely on today's board." (the last
  confirmed byte-verbatim in `preflight-banner.tsx` L77, matching the DoD's mandated exact phrase). No
  jargon, no score/edge language (correctly avoids anti-goals #1/#2).
- **Visual feedback:** three structurally distinct, color-coded states verified directly in
  `preflight-banner.tsx` — GO uses `border-pos/40 bg-pos/5 text-pos` (a verbatim match to the existing
  "quiet positive" token combination already used in `market-phase-card.tsx` L233 — confirmed by direct
  grep, not just asserted by the handoff); DEGRADED uses `border-warn bg-warn/10 text-warn`; NO-GO uses
  `border-neg bg-neg/10 text-neg`. Browser QA (UT-06, UT-13, UT-14) confirms these render as md5-distinct,
  pixel-visible frames identically across all five required surfaces.
- **First-load / error honesty:** `loading` renders a neutral "Checking board status…" strip before the
  first poll resolves (structurally guaranteed by React's render order — `ReadinessProvider` initializes
  `loading=true`/`preflight=null` and only flips `loading` false inside the first `tick()`'s `finally`,
  confirmed by direct source read), and a failed poll (`preflight === null`) renders an honest NO-GO
  fallback rather than a blank page. Neither state is a fabricated GO. Browser QA UT-12 confirms the
  backend-down path live (organically, then in a controlled stop/restart).

No hidden capability, no undiscoverable capability, no label confusion.

## Regression Risk

The touched files are unusually high-leverage (root layout wrapping every route, the shared readiness
context, the single health endpoint), so this review verified the diffs directly rather than relying on the
handoffs' description of them:

| Shared component | Prior feature it serves | This iteration's change | Verified risk |
|---|---|---|---|
| `apps/frontend/components/health-badge.tsx` | J-40 readiness badge (Ready/Initializing/Unavailable pill + provider/seed/symbol-count badges) | **None** — `git status`/`git diff` confirm zero changes to this file | **None.** Untouched at the file level, and UT-09 additionally regression-tests it live (identical text/color/position across GO and DEGRADED screenshots). |
| `apps/frontend/app/layout.tsx` | Every route in the app (27 pages) | 2-line diff: one import, one `<PreflightBanner />` insertion between `</header>` and `<main>` | **Low, well-contained.** The banner sits outside `<main>` in normal document flow (no `fixed`/`absolute`), so it structurally cannot overlap page content — it can only push content down, which is the spec-intended behavior on loud days and was itself regression-tested (UT-11 PASS: content never clipped/hidden, GO vs DEGRADED pairs compared directly). |
| `apps/frontend/components/readiness-provider.tsx` | J-40 readiness state/warmup, read by `HealthBadge` and the Backtest/Research "warming up" states | Purely additive: one new `preflight` field piggybacked on the SAME existing `fetchHealth()` call inside the existing `tick()`; `state`/`warmup` set-calls and cadence logic are byte-for-byte unchanged in the diff | **Low.** Confirmed via `git diff` — no restructuring of the existing state machine, no second fetch introduced. |
| `apps/backend/app/api/health.py` | Every frontend consumer of `GET /api/health` (readiness badge, warmup states, and now the new banner) | Additive `preflight` key appended to the response dict; all pre-existing keys (`status`, `db_ok`, `readiness`, `warmup`, `poll_interval_seconds`, etc.) are untouched in the diff, and the new field is wrapped in its own try/except so a `compute_preflight` failure degrades to an honest NO-GO rather than blanking the whole payload | **Low.** Byte-identity of the pre-existing keys is structurally evident from the diff itself (a dedicated shape/byte-identity test is also named in the dev handoff). |
| `/data` page's own pre-existing warning/error banner (`app/data/page.tsx`) | Data Manager's own "Backend unavailable" card and job-status coloring | Not touched by this iteration's diff at all (confirmed absent from `git status`) | **None.** Spatially separated from the new layout-level strip (the new banner sits above `<main>`; `/data`'s own card renders inside its own content). UT-08 confirms no visual collision live. |

**Required-still-passing journeys (J-01, J-02, J-04, J-05, J-11, J-13, J-18):** golden replay scripts for
all seven exist on disk (`runs/goal-session-mcp-loop/journey-scripts/`). J-11 specifically was investigated
per the plan (iter-32 had only covered 6-of-7) and live-verified PASS via `demo_runner.py`. Browser QA's
UT-09/UT-10/UT-11/UT-20 directly regression-test the surfaces these journeys depend on (readiness badge,
leaderboard "Not yet proven" badges, evidence ledger FAIL rows, sidebar's 11 nav items) across both GO and
DEGRADED/NO-GO states, all PASS. The full deterministic-replay-lane run itself (`goal-iter-lean.sh`) is
noted in `reports/qa/goal-mcp-loop-iter-33-qa.md` as executing in the next pipeline step, after this
review — that is expected pipeline ordering, not a gap in this report.

**Note on iteration numbering:** this codebase has hosted more than one goal-mode session over time (the
current `mcp-loop` session, and earlier `i_can_see_the_wealthy_future*` sessions that reached
`GOAL_ACHIEVED` and share `apps/frontend`/`apps/backend`). One of those earlier sessions also had its own,
unrelated "iter-33" (visible in a stale in-code comment on `app/data/page.tsx` referencing "iter-33
(J-93/J-94)" and in `reports/phase-goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-33-*`
files dated Jun 29). That is a coincidence of iteration-number reuse across sessions, not related to this
phase's diff — confirmed `app/data/page.tsx` is absent from the current `git status`. Flagged here only so
a future reader isn't confused by the same "iter-33" label appearing twice in the repo's history.

No potential regressions found.

## UI vs Backend Parity

| Backend capability | UI exposure | Assessment |
|---|---|---|
| `compute_preflight`'s `verdict` (`GO`/`DEGRADED`/`NO-GO`) | Rendered as the banner headline on every route | Full parity |
| `compute_preflight`'s `reasons` list | Rendered verbatim as bullets in the loud states | Full parity |
| `compute_preflight`'s per-component breakdown (`components: {servability, freshness, integrity}` each with `ok`/`severity`/`detail`) | Not shown as a separate structured element — only the flattened `reasons` strings are rendered | **Intentional, not a gap.** goal.md's "New information displayed" explicitly scopes this to "the verdict + its reasons list... No new numbers, scores, or edges." The reasons text already names the specific failing check in plain language (e.g. "Latest data (2026-07-01) is 6 trading day(s) old..." is self-evidently the freshness component) — a separate components readout would be redundant with what the spec asked for. |
| `as_of`/`reference` (the freshness anchor date) | Not shown as a standalone value (only implicitly, inside a DEGRADED/NO-GO freshness reason string) | **Minor, non-blocking.** Not requested by the DoD or the Data Contract row's UI reader spec (which names only the layout banner as the one reader, for verdict+reasons). No action needed. |
| Verdict-history log (`preflight-verdict-history.jsonl`) | No page reads or displays it | **Intentional, out of scope.** goal.md's OUT OF SCOPE section explicitly defers this to a future "B-307 digest" journey; the "Not Visible Yet" section of `user-visible-changes.md` states this plainly and accurately rather than hiding the gap. |
| B-113 sentinel, B-304 drift (J-21), B-103 time-machine inputs | Not built, so not reflected in the banner | **Explicitly out of scope** per goal.md — the composer leaves a config+one-branch seam for each, confirmed present in `compute_preflight`'s structure per the dev handoff. |

All backend capability that this iteration's Definition of Done requires to be user-visible is user-visible,
identically, on every required surface. The gaps that exist are named honestly in `user-visible-changes.md`
and map cleanly to journeys/backlog cards goal.md has explicitly deferred (J-21/B-304, B-113, B-103, B-307) —
this is the documented "ship with whatever inputs exist and add the rest as they land" design B-301 called
for, not an unaddressed parity hole.

## Flags

### Hidden Capabilities
None.

### Undiscoverable Capabilities
None.

### Potential Regressions
None.

### Visual Consistency
- New `PreflightBanner` uses only existing DESIGN SYSTEM tokens (`--pos`/`--warn`/`--neg`, confirmed present
  verbatim in `apps/frontend/app/globals.css` L14-16) — no arbitrary hex or pixel values found in
  `preflight-banner.tsx`.
- The GO state's token combination is a verbatim reuse of `market-phase-card.tsx`'s established "quiet
  positive" pattern (confirmed by direct grep match), not an invented one-off.
- The loud DEGRADED/NO-GO treatment is stylistically consistent with `/data`'s own pre-existing
  danger/warning language (same `--neg`/`--warn` token family) while remaining spatially distinct (layout
  strip above `<main>` vs. a `Card`-wrapped error block inside page content), so the two can't be confused
  even when both could theoretically be visible at once.
- `data-testid="preflight-banner"` / `data-verdict="<state>"` mirrors `HealthBadge`'s existing
  `data-testid="readiness-badge"` / `data-state="<state>"` convention — consistent component pattern.
- Minor, non-blocking stylistic note: the loud banner states render a bold text headline with no icon,
  whereas `/data`'s own error card and the `DateInput` inline-error both pair `--neg` text with an
  `AlertTriangle` icon. This is a cosmetic inconsistency only (the banner's meaning is already unambiguous
  from the "DEGRADED"/"NO-GO" wording and color), not something goal.md requires, and not worth blocking on.

## Recommendation

No action required. The single new capability is discoverable with zero clicks (ambient layout chrome,
correctly not a nav item), its three states are visually distinct and use established design tokens
faithfully, and the shared components it touches (`layout.tsx`, `readiness-provider.tsx`, `health.py`) were
independently verified via diff inspection to be either untouched (`health-badge.tsx`) or purely additive,
with the one behavioral side effect (content shifting down on loud days) both spec-mandated and
regression-tested. UI/backend parity is complete for everything this iteration's DoD requires; the
remaining backend-only detail (component breakdown, reference date, verdict-history log) is explicitly and
correctly scoped to future journeys (J-21/B-304, B-113, B-103, B-307) in goal.md itself.
