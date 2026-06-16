**Verdict:** COHERENCE-PASS

## Iteration 25 — Coherence Audit

**Session:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
**Iteration index:** 25
**Iter name:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-25
**Target journey:** J-83 (as-of SSR seeding — server/client hydration parity)
**Depth:** lean (frontend-only; backend diff empty, confirmed)

---

## Step 1 — Data Contract check

**No violations found.**

This iteration introduces no new displayed value, no new endpoint, and no new computation. The changes
are:

1. `apps/frontend/middleware.ts` (untracked new file) — reads the request `?asof` query param,
   shape-validates it via the shared `isValidIsoDate`, and forwards it as the `x-asof` request header
   only when valid. This is a transport mechanism for the ONE existing global as-of value; it creates no
   second value, no second date state, and no new endpoint.

2. `apps/frontend/app/layout.tsx` — reads the `x-asof` header via `next/headers()` and passes it as
   `initialAsOf` into `AsOfProvider`. Server-component only; no `"use client"` added. Still no new value.

3. `apps/frontend/components/asof-provider.tsx` — the EXISTING single `asOf` `useState` lazy
   initializer now prefers `initialAsOf` (server-forwarded) over `readAsofFromUrl()` (client fallback).
   Grep of the diff confirms exactly ONE `asOf` useState remains (the `const [asOf, setAsOfState] =
   useState<string | null>(...)` line is unchanged; only its initializer argument is modified). No new
   `useState` for a date, no new date source.

4. `apps/frontend/lib/dates.ts` — adds `ASOF_PARAM = "asof"` and `ASOF_HEADER = "x-asof"` as exported
   constants. The `ASOF_PARAM` literal was previously a module-scoped `const` inside `asof-provider.tsx`
   — it is moved (not duplicated) so the Edge-runtime middleware can import it without a `"use client"`
   boundary. The value is identical; `asof-provider.tsx` now imports it from `@/lib/dates` (confirmed in
   the diff). One name, one owner — asof-provider remains the sole `?asof` reader/writer.

The "Resolved as-of date + available dates (ONE global state)" Data Contract row in `blueprint.md`
carries the additive J-83 annotation (confirmed: blueprint.md is in the diff). No row duplicated, no
second date source registered.

**Data Contract invariants held:**
- Exactly one date selector (coherence invariant 5): one `asOf` useState, asof-provider sole owner — confirmed.
- No recompute in the read path (invariant 2): no new computation, the header is a transport of the URL value.
- No secrets in source: middleware forwards only shape-valid ISO dates, never provider keys — confirmed in `middleware.ts:31-39`.

---

## Step 2 — Information Architecture check

**No violations found.**

No new page, route, or navigational surface is introduced. The middleware runs transparently across all
app pages. The `app/layout.tsx` server-component change adds a header read; it does not alter the nav
skeleton, add a nav link, or create a new UI section.

J-83 is cross-cutting hardening of the existing "J-13/J-43 top-bar as-of switcher" home documented in
the blueprint's Information Architecture. The IA nav skeleton (Dashboard / Stocks / Themes / Sectors /
Scanner Runs / Backtest / Watchlist / Methodology / Research / Data Manager) is unchanged.

No feature requires a nav path that is missing. No duplicate home. No parallel shell.

---

## Step 3 — Advisory observations

**WARN (minor, non-blocking):** `middleware.ts` and several other iter-25 artifacts are untracked
(not yet staged/committed). This is normal working-tree state during an active iteration and has no
coherence bearing — it is noted for completeness only.

**Note (out-of-scope, non-blocking):** The uncommitted `apps/backend/data/seed/meta.json` change and
the untracked `apps/backend/data/seed/universe.json` are the visible artifacts of the J-84 failed Yahoo
market-cap fetch (the J-84 401 premise). The iter-25 spec explicitly calls these out-of-scope and
states J-84 owns them. They do not affect the Data Contract or IA for this iteration.

---

## Summary

| Check | Result |
|---|---|
| Part A — Data Contract | PASS — no duplicate computation, no non-canonical source, no new unregistered value |
| Part B — Information Architecture | PASS — no new route, no missing nav path, no duplicate home, no parallel shell |
| Part C — Advisory | minor working-tree / out-of-scope note only (non-blocking) |

**Verdict:** COHERENCE-PASS
