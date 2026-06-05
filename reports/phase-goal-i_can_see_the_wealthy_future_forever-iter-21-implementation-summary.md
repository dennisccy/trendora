# Goal Iteration 21 — Implementation Summary

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-21
**Date:** 2026-06-05
**Written by:** developer

---

## Features Implemented

- **Import-source picker on the Data Manager (`/data`)**: when you choose a job kind that fetches
  ("Fetch EOD prices" or "Fetch + backfill"), the form now shows an **Import source** dropdown listing
  the configured data providers — **Yahoo Finance, Tiingo, Finnhub, Alpha Vantage, Stooq**. Each option
  is tagged **"available"** (ready to use) or **"needs key"** (a credential is required).
- **Per-source availability at a glance**: under the picker, a line states whether the selected source
  is available or needs a key, and names the environment variable the key would come from (e.g.
  "set `$TIINGO_API_KEY` or paste a session key"). Yahoo needs no key and is the default.
- **Session-only key paste field**: when you pick a "needs key" source that has no key in the
  environment, a password field appears so you can paste a key for **this run only**. The key is held
  in the browser's memory, sent with the job, and then dropped — it is **never saved** to disk, the
  database, the run history, a cookie, the URL, or any server log, and is **never shown back** to you.
- **Source-selectable imports**: a fetch now pulls from the provider you chose (previously the Data
  Manager was hardwired to a single provider). If the chosen provider can't return real data, the job
  shows an **explicit error / unavailable** state and **invents no prices** — exactly as before.
- **New provider clients** (backend): thin, real end-of-day clients for Yahoo, Tiingo, Finnhub, and
  Alpha Vantage. Each returns real price bars or raises an explicit "unavailable" error; none ever
  fabricate a price. (The existing offline seed and Stooq clients are kept.)

---

## Changed Behavior

- **Starting a fetch/backfill job**: Previously the job took only a date range and a kind. Now a
  fetch-type job also carries the chosen **import source** (and, if needed, a session-only key). A
  backfill-only job is unchanged — it still reads the offline committed data and needs no source/key.
- **`GET /api/data` payload**: Previously returned dataset coverage + run history. Now also returns a
  **`sources`** list (the provider catalog with availability) so the UI can render the picker from
  config — there is no hardcoded provider list in the app.
- **Run history "provider" column**: for a fetch run it now records the **chosen source id** (e.g.
  `yahoo`) rather than a single fixed provider name. (Never the key.)
- **`/data` page subtitle**: corrected the stale wording "grow the System Health evidence" →
  "grow the Backtest evidence" (System Health was retired in iter-17).

---

## Backend-Only Items

- None. Every backend capability added this iteration (the provider catalog, availability, source/key
  job parameters) is wired into the `/data` UI.

---

## Incomplete Items

- **J-34 (chunked / resumable import) and J-35 (Expand-universe)** are intentionally **out of scope**
  this iteration — they are the next two iterations (iter-22, iter-23) and build on this source
  foundation. No checkpoint/resume/backoff machinery and no `expand` job kind were added here.
- **A *successful* live import is not reachable from this environment** and was not attempted (see
  Known Limitations) — by design, all of this iteration's machinery is proven offline.

---

## Config and Environment Changes

- **`config.yaml` → `data_manager.providers`** (new): the import-source catalog. Each entry has an
  `id`, a display `label`, whether it `needs_key`, the `env_var` name its key is read from, and a
  `supports_market_cap` flag (declared now, used by the future Expand-universe feature). This is the
  single source of the provider list — the app hardcodes no providers.
- **`config.yaml` → `data_manager.default_source`** (new): the source used when a job omits one.
  Set to `yahoo` (no key needed) so a fetch with no source chosen still works.
- **`config.yaml` → `data_manager.live_provider`** (removed): superseded by the catalog +
  `default_source`.
- **Provider API-key environment variables** (read only if you choose that source, never required for
  the default offline path): `TIINGO_API_KEY`, `FINNHUB_API_KEY`, `ALPHAVANTAGE_API_KEY`,
  `STOOQ_API_KEY`. None are committed; the default seed/Yahoo path needs none. A key may also be pasted
  into the UI for a single run instead of setting an env var.
- **`apps/frontend/next.config.mjs` → `NEXT_DIST_DIR`** (new, optional): lets a verification build
  write to a throwaway directory instead of `.next` (defaults to `.next`); a convenience for CI, no
  runtime effect.

---

## Known Limitations

- **A successful *live* fetch is externally data-walled and was not exercised live.** Yahoo rate-limits
  this server's IP and Stooq's free endpoint is key-gated here, so an actually-successful real import is
  not autonomously reachable. This is expected and non-blocking: per the goal, the **machinery**
  (catalog, availability, key handling, explicit-error path) is proven **offline with a mocked/injected
  provider**, and a live-fetch outcome is recorded honestly as unavailable/rate-limited. The provider
  clients themselves are real (one documented HTTP call each); only the network outcome is gated.
- **Stooq is marked "needs key"** in this environment (honest — its free CSV is IP-gated here). The
  Stooq client still calls the free endpoint; the key requirement is enforced as a gate before the job
  runs (so selecting Stooq without a key is rejected with a clear message rather than silently failing).
- The `supports_market_cap` catalog flag is **declared but not yet consumed** — it exists so the J-35
  Expand-universe gate (iter-23) has a stable schema to read.
