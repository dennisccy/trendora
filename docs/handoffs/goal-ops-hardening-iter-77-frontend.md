# goal-ops-hardening-iter-77 Frontend Handoff

**Phase:** goal-ops-hardening-iter-77
**Date:** 2026-08-13
**Agent:** developer
**Status:** complete

## What Was Built

- **Staleness disclosure (J-04/J-07).** The global readiness badge and preflight banner now render a
  short, factual "as of Ns ago" annotation whenever the SAME `GET /api/health` poll's `stale_for_s` field
  is `> 0` (a stale cached readiness/preflight/background-compute read). No annotation for a fresh/
  synchronous compute (`stale_for_s === 0`) or when the poll itself fails (`state === null`/`unavailable`)
  — the formatter (`lib/staleness-annotation.ts`) enforces this: it returns `null` for anything other than
  a finite, positive value, so callers can never accidentally render a stale or fabricated number.
- **Badge-row layout fix (iter-76/e).** At a 1280×800 viewport with a background-compute chip also shown,
  the readiness pill no longer gets pushed off-screen — the header's badge row now wraps onto a second line
  when its content does not fit on one, instead of overflowing past the visible top bar. The header stays a
  fixed 56px (`h-14`-equivalent) on every page/width where everything already fits — it only grows when the
  row actually wraps.
- **`scorecard-row-<horizon>d` test hook.** `/backtest`'s forward-test scorecard rows each now carry a
  stable `data-testid` (e.g. `scorecard-row-1d`) — no visible change, purely a QA/golden-replay selector
  hook, closing a fragile bare-text-token match in the J-07 golden.

## Files Changed

- `apps/frontend/lib/api.ts` -- `HealthStatus.stale_for_s: number` added.
- `apps/frontend/lib/staleness-annotation.ts` (new) -- pure formatter.
- `apps/frontend/lib/staleness-annotation.test.ts` (new) -- unit tests (see dev handoff's "Tests Run" for
  why they run via a mirror-verify on this dev box, not directly).
- `apps/frontend/components/readiness-provider.tsx` -- `ReadinessContextValue.staleForS` added.
- `apps/frontend/components/health-badge.tsx` -- renders the annotation (`data-testid="readiness-staleness"`).
- `apps/frontend/components/preflight-banner.tsx` -- renders the annotation
  (`data-testid="preflight-staleness"`) on both the GO strip and the DEGRADED/NO-GO banner.
- `apps/frontend/app/layout.tsx` -- header `h-14` → `min-h-14`, badge row gets `flex-wrap`.
- `apps/frontend/app/backtest/page.tsx` -- `ScorecardSection` rows get `data-testid`.

## UI Evolution

- **New user-facing capability:** anyone viewing the readiness badge or preflight banner can now see how
  stale the displayed status is, whenever it is genuinely stale.
- **New information displayed:** `stale_for_s` as "as of Ns ago", read verbatim from the existing
  `GET /api/health` payload (no new endpoint, no client-side computation).
- **New user actions:** none — both surfaces remain read-only status displays.
- **UI surface changes:** global readiness badge (every page, top bar) and preflight banner gain the
  annotation + the layout wrap fix; `/backtest`'s scorecard rows gain an invisible test hook.
- **Navigation changes:** none.

## Visual Verification (live, this dev pass)

Screenshotted live at 1280×800 with a real background-compute window in flight (triggered via
`GET /api/backtest?as_of=...` for several not-yet-computed dates against the running dev backend):
`reports/qa/goal-ops-hardening-iter-77-evidence/dev-verify-TC-5-ready-pill-plus-compute-chip-1280x800.png`
shows the "Ready" pill, the "as of 0s ago" annotation, and the "background compute running (5)" chip all
on-screen simultaneously, wrapped onto a second line beneath the provider/seed/symbol badges. The preflight
banner's own "GO — today's board is current. (as of 0s ago)" is visible in the same frame.

`reports/qa/goal-ops-hardening-iter-77-evidence/TC-8-data-fault-injection-honest-fallback.png` shows the
`/data` honest-fallback state (unrelated surface, captured this round as housekeeping — see dev handoff).

## Known Issues

- No dedicated component-render unit test for the layout wrap or the scorecard testid: this frontend has no
  Jest/RTL (or any component-rendering framework) installed — the established convention here (see e.g.
  `lib/background-compute-panel-branch.test.ts`) is pure-logic extraction tested via `node:assert`, which I
  followed for the staleness FORMATTER (`lib/staleness-annotation.test.ts`), but pure CSS wrapping behavior
  and a static JSX attribute have no equivalent pure-logic surface to extract. Both are verified live (see
  above) and are covered by the browser-qa-agent's own TC-5/TC-6 pass and by J-07's golden replay
  (`scorecard-row-1d`).
- `node lib/staleness-annotation.test.ts` cannot execute directly on this dev box (Node built without
  TypeScript type-stripping — the same pre-existing, documented limitation every other `lib/*.test.ts` file
  in this repo already has). Mirror-verified with a byte-equivalent plain-JS copy: 6/6 assertions passed.

---

## Fix Notes (developer, 2026-08-13, FIX MODE — audit FAIL)

Two frontend-side changes, both from `docs/handoffs/goal-ops-hardening-iter-77-audit.md`:

- **Finding F1 — the staleness annotation no longer contradicts itself.** The audit measured the live
  steady state: with `readiness.refresh_interval_seconds: 0.5`, most served `stale_for_s` values are
  sub-second (11 of 15 sampled values round to zero), so the disclosure was rendering "as of 0s ago" on
  almost every page view. Sub-second staleness now reads **"as of <1s ago"**; one second and above is
  unchanged ("as of 1s ago", "as of 483s ago"). The annotation still appears only when the served value is
  genuinely `> 0`, is still a pure re-format of that field with no client-side computation (AG-3), and
  still renders nothing at all when the health poll fails. Verified live at capture time: `GET /api/health`
  returned `stale_for_s` 0.168 / 0.192 / 0.211 and both surfaces read "as of <1s ago"
  (`reports/demo/goal-ops-hardening-iter-77/step-01.png` — the "Ready" pill, the annotation next to it, and
  the banner's "GO — today's board is current. (as of <1s ago)" all visible at 1280×800).
  No golden or demo expectation needed rewriting: every assertion matches on the `as of` token, not the
  number.

- **Findings B1/B2 — `apps/frontend/next.config.mjs` now guards production builds.** A `next build` is
  refused when it would write into the live `.next` without `NEXT_PUBLIC_API_URL` (which bakes
  `lib/api.ts`'s `http://localhost:8000` fallback into the bundle and makes every page render "Backend
  unavailable"), or into any dist directory a live server is currently serving. This is build-time only —
  no runtime code, no component, no page behavior changes. Anyone running a verification build should use
  `NEXT_DIST_DIR=.next-verify npx next build`; the refusal message says so.

**Frontend verification this pass:** the formatter's unit tests were executed for real this time rather
than mirror-checked — the project's own TypeScript transpiles `lib/staleness-annotation.ts` +
`lib/staleness-annotation.test.ts` and Node runs the result: **7/7 passed** (including the new sub-second
boundary cases at 0.053 / 0.128 / 0.499 → "<1s", and 0.505 → "as of 1s ago"). The frontend was rebuilt and
restarted through `scripts/start-frontend.sh` (production build, 29 routes) and all eight journey goldens
replay PASS against it.
