# goal-i_can_see_the_wealthy_future_forever-iter-21 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-21
**Date:** 2026-06-05
**Agent:** developer
**Status:** complete
**Journey:** J-33 (UI surface) — Import-source picker + session-only key field on `/data`

## What Was Built (UI)

On `/data` (Data Manager), inside the **"Start a fetch / backfill job"** card (`JobForm`):

- **Import source `<Select>`** — shown only when the Job kind involves a fetch (`Fetch EOD prices` /
  `Fetch + backfill`). Populated **entirely from `data.sources`** (the `GET /api/data` availability list) —
  **no hardcoded provider list in the component**. Each option reads `"{label} · available"` or
  `"{label} · needs key"`. `aria-label="Import source"`.
- **Per-source availability line** (`data-testid="source-availability"`) — under the picker: the selected
  source's label + an **"available"** (`text-pos`) / **"needs key"** (`text-warn`) tag + the server
  `reason` (e.g. "set $TIINGO_API_KEY or paste a session key"). Re-formatted from the API, verbatim reason.
- **Session-only key field** — a `type="password"` input (`aria-label="Session API key"`,
  `autoComplete="off"`) that appears **only** when the selected source `needs_key` **and** is **not**
  available (no env key). Held in component `useState` **memory only**; a caption states it is held for the
  run only and never written to disk/DB/log/cookie and never echoed back.
- **Job progress card** now shows the chosen `source` in its hint (confirms the source is recorded; the key
  never appears).
- **Subtitle fix**: "grow the System Health evidence" → "grow the Backtest evidence".

## Data Flow / State
- New parent state: `source` (defaults to the first catalog id = `yahoo` once `/api/data` loads) and
  `apiKey` (session-only).
- `startDataJob(kind, start, end, opts?)` sends `source` (when fetching) and `api_key` (only when the key
  field is visible **and** non-blank — a stale/irrelevant key is never transmitted).
- The key is **cleared** when the job leaves `running` (completion) and on component unmount. It is never
  put in `localStorage`, the URL, a cookie, or any persisted store.
- The frontend recomputes nothing — it re-formats the server's catalog/availability only.

## J-18 (exactly one date selector) — preserved
- The new **Import source** `<Select>` and the existing **Job kind** `<Select>` are **not** date controls.
  The `/data` job dates remain `type="date"` inputs (job parameters). The only **date** `<select>` app-wide
  is the global header as-of switcher — unchanged. No date state was added.

## Verification
- `npx tsc --noEmit` → 0 errors.
- `NEXT_DIST_DIR=.next-verify npx next build` → success; `/data` route compiles (5.55 kB). Built to a
  throwaway dir so the live `.next` was never clobbered (MEMORY `browser-qa-dead-shell-next-cache`); the
  throwaway dir was deleted afterward.

## For Browser QA (J-33)
- The Chrome-MCP `select` action does **not** fire React `onChange` on this frontend — use the
  **native-setter + bubbling `change`** pattern on the `<select>`, then assert the live DOM (MEMORY
  `react-controlled-select-needs-native-setter`).
- Steps: switch Job kind to **Fetch EOD prices** → the **Import source** picker appears with the config
  catalog (Yahoo/Tiingo/Finnhub/Alpha Vantage/Stooq) and per-source availability. Select a **needs-key**
  source (e.g. Tiingo or Stooq) with no env key → the **Session API key** password field appears. Confirm
  no new date control appeared (one date `<select>` app-wide = the header switcher). Start a **fetch**
  against a source while the provider is walled → an explicit **error/unavailable** job state (no
  fabricated bar; the pasted key is not echoed in the job card or run history). Confirm the existing
  **backfill** path still runs (default source, offline, snapshots created).
