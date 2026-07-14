# goal-mcp-loop-iter-33 Frontend Handoff

**Phase:** goal-mcp-loop-iter-33
**Date:** 2026-07-14
**Agent:** developer
**Status:** complete

## What Was Built

The frontend half of J-20 / backlog B-301: a single, cross-cutting `PreflightBanner` that appears on
every page automatically (mounted once in the app shell), reading the SAME `/api/health` poll the
existing `ReadinessProvider`/`HealthBadge` already use — no second fetch, no per-page recompute.

- **`ReadinessProvider`** (`components/readiness-provider.tsx`) extended: `ReadinessContextValue` now
  also exposes `preflight: PreflightStatus | null`, populated from the SAME `fetchHealth()` call `tick()`
  already makes. On a failed poll it is set to `null` (honest — mirrors the existing `state="unavailable"`
  / `warmup=null` degrade), never a fabricated value.
- **`lib/api.ts`** types: `PreflightVerdict` (`"GO" | "DEGRADED" | "NO-GO"`), `PreflightComponent`
  (`{ok, severity, detail}`), `PreflightStatus` (`{verdict, reasons, components, as_of, reference}` —
  `as_of`/`reference` carry the identical value, served under both names per the spec's ambiguous
  naming), and the `preflight: PreflightStatus` field added to `HealthStatus`.
- **`PreflightBanner`** (new, `components/preflight-banner.tsx`) — a `"use client"` component reading
  ONLY `useReadiness()`:
  - **loading** (first poll not yet resolved): a neutral thin strip, "Checking board status…" — mirrors
    `HealthBadge`'s own loading placeholder; never a fabricated GO.
  - **`preflight === null`** (the poll itself failed / backend unreachable): renders the SAME loud NO-GO
    treatment with an honest "Backend is unavailable — the preflight check could not run." reason — never
    a blank crash.
  - **`GO`**: a quiet, thin, non-intrusive strip (`border-pos/40 bg-pos/5 text-pos` — mirrors
    `market-phase-card.tsx`'s established "quiet positive" token combination) with a small dot + "GO —
    today's board is current."
  - **`DEGRADED`** / **`NO-GO`**: a loud, full-width banner (`border-warn bg-warn/10 text-warn` /
    `border-neg bg-neg/10 text-neg` — mirrors the established warning treatment already used on `/data`,
    extended with the `neg` token for the more severe state) with a bold headline and a bulleted list of
    the exact `reasons` strings from the payload, verbatim — no client-side wording invented. `NO-GO`'s
    headline always reads "NO-GO — do not rely on today's board." (the exact required phrase).
  - Every state carries `data-testid="preflight-banner"` + `data-verdict="<state>"` for deterministic
    test/QA selectors (mirrors `HealthBadge`'s existing `data-testid="readiness-badge"` /
    `data-state="..."` convention); `role="status"` for the quiet states, `role="alert"` for the loud ones.
  - No buttons, forms, or interactive elements anywhere — read-only status only (anti-goal #2: it gates
    trust, not orders).
- **`app/layout.tsx`**: `<PreflightBanner />` mounted ONCE, between the sticky `<header>` and `<main>`,
  inside the content-column `<div>` (so it spans the content area, not the sidebar) — every route gets it
  automatically with zero per-page code. No nav change, no new page (cross-cutting chrome, like the
  existing `HealthBadge`).

## Visual / UX notes

- GO is deliberately understated (small text, thin strip, no layout disruption) so it never competes for
  attention on a healthy day — this protects the pixel/DOM assertions of every other required-still-passing
  journey (J-01, J-02, J-04, J-05, J-11, J-13, J-18), all confirmed still passing with the banner mounted
  (see the dev handoff's "Tests Run" section for the live verification log).
- DEGRADED/NO-GO are loud by design (full-width, bold headline, bulleted reasons) — this is the intended,
  spec-mandated behavior (a "risk-officer kill-switch UX"), not a bug to soften.
- All colors/spacing/typography come from the project's existing DESIGN SYSTEM tokens (`--pos`/`--warn`/
  `--neg`, the `surface`/`border` families, the standard `text-xs`/`text-sm` scale) — no arbitrary hex or
  pixel values were introduced.

## Files Changed

- `apps/frontend/lib/api.ts` -- added the `PreflightVerdict`/`PreflightComponent`/`PreflightStatus` types
  and the `preflight` field on `HealthStatus`.
- `apps/frontend/components/readiness-provider.tsx` -- exposes `preflight` from the existing poll.
- `apps/frontend/components/preflight-banner.tsx` (new) -- the banner component (all four states).
- `apps/frontend/app/layout.tsx` -- mounts `<PreflightBanner />` once in the shell.

## Tests Run

`npx tsc --noEmit` (in `apps/frontend`) -- clean, no type errors.

Live browser verification (Chrome, via `superpowers-chrome`) against the dev server (`scripts/dev.sh`,
port 3255) -- see the dev handoff's "Tests Run" section for the full log; summarized:
- GO banner text confirmed pixel-visible on `/`, `/evidence`, `/stocks`, `/stocks/NVDA` (screenshot
  captured on `/`).
- DEGRADED banner (with the exact backend-computed reason) confirmed on `/watchlist` after a controlled
  config override (screenshot captured); the rest of the Watchlist page rendered normally underneath.
- NO-GO banner containing the exact phrase "do not rely on today's board" confirmed on `/stocks/NVDA`
  after a controlled integrity-breach override (screenshot captured); the rest of the stock-detail page
  (scores, chart, realized-returns cards) rendered normally underneath, including its own unrelated "Not
  yet proven" evidence badges -- confirming no interference between the two systems.
- Healthy GO state restored and re-confirmed before finishing.

No dedicated frontend unit-test runner is configured for this project (`.claude/project-template.md`'s
Frontend test command is unfilled — a known, pre-existing gap noted in the iter-30/31/32 handoffs); the
TypeScript compiler + live browser verification above are the available correctness gates.

## Known Issues

- The canonical prod-mode browser-qa pass (via `scripts/start-backend.sh` / `scripts/start-frontend.sh`,
  with a fresh `apps/frontend/.next` per the plan's "Pre-QA hygiene" note) is the next pipeline stage's
  job — my own verification above used `dev.sh` (dev-mode `next dev`) for iteration speed. The component
  exercises the same code paths either way, but the canonical QA lane should still re-run against the prod
  bundle before this journey is declared `passing` (per the iter-13/20/22/31 "audit-fix-not-canonically-
  re-run" lesson already called out in the plan).
- No new loading/empty/error visual states beyond what's described above were needed — the banner has no
  data-table/list content of its own (it renders a fixed small set of strings), so there is no separate
  "empty state" to design.
