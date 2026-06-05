# Phase goal-i_can_see_the_wealthy_future_forever-iter-21 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-21 (J-33 — Import source picker)
**Date:** 2026-06-05
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now **choose which provider an import fetches from** on the Data Manager (`/data`): when the Job kind is **Fetch EOD prices** or **Fetch + backfill**, a new **Import source** dropdown appears, listing the configured providers (Yahoo, Tiingo, Finnhub, Alpha Vantage, Stooq).
- Users can now **see at a glance which providers are ready vs which need a key**: each dropdown option is tagged **"available"** (no key needed, or an environment key is present) or **"needs key"**, and a line under the picker repeats the selected source's status plus a plain-language reason (e.g. "set $TIINGO_API_KEY or paste a session key").
- Users can now **paste an API key for a key-required provider, for that run only**: when a "needs key" source with no environment key is selected, a masked **Session API key** field appears. The key is held in the browser for the run only — it is never saved to disk, the database, the run log, a cookie, or shown back.
- Users can now **start a fetch/backfill/both job against their chosen source** and watch the live job progress card, which now displays the chosen source id in its header.
- Users still get an **explicit error / unavailable state** when a provider fails — the job card shows the error count with "(no data fabricated)" and lists the errors, and no invented price bars are created.

---

## What Changed in the Visible UI

- The **"Start a fetch / backfill job"** card on `/data` now contains an **Import source** `<select>` (`aria-label="Import source"`), shown only for fetch-type jobs. It is populated entirely from the API catalog — there is no hardcoded provider list in the page.
- A new **per-source availability line** (`data-testid="source-availability"`) appears under the picker, showing the selected source's label, an "available"/"needs key" tag, and the server-provided reason.
- A new conditional **Session API key** field (`type="password"`, `aria-label="Session API key"`) appears only when a "needs key" source with no environment key is selected, with a caption stating the key is held for the run only and never persisted.
- The **Job progress** card header now includes the chosen source id (e.g. `fetch job · yahoo · 2024-01-01 → 2024-01-05`) when a source was selected.
- The **Data Manager page subtitle** was corrected: "…grow the System Health evidence" → "…grow the Backtest evidence" (stale wording left over from the iter-17 System-Health retirement).

---

## What Old Behavior Changed

- **Fetch / Fetch+backfill jobs**: previously every fetch was hardwired to a single live provider with no user choice. Now the job runs against the user-selected import source; if no source is chosen the job defaults to the configured `default_source` (Yahoo), so the existing fetch behavior (J-17) is preserved.
- **Selecting a key-required source with no key**: a fetch against a "needs key" source with neither an environment key nor a pasted key is now rejected up front with an explicit error message, rather than silently failing or fabricating data.
- **Backfill-only jobs**: unchanged — the Import source picker and key field stay hidden for the "Backfill snapshots" kind, and the offline/deterministic backfill path runs exactly as before.

---

## Not Visible Yet

- **`supports_market_cap` provider flag** — present in the configured catalog and carried through the availability data, but not surfaced anywhere in the UI this iteration. It is declared now and will be consumed by the J-35 Expand-universe gate (iter-23).
- **Resilient / resumable import (J-34)** — chunked fetch, 429 backoff, durable checkpoints, and a Resume action are not built this iteration; the existing single-shot fetch loop is unchanged. (iter-22)
- **Expand-universe job kind (J-35)** — no "expand" job kind or universe-pool screen exists yet. (iter-23)
- **A successful live import** is not autonomously reachable in this environment (Yahoo rate-limits this IP; Stooq is key-gated). All new machinery is verifiable offline; a live fetch will honestly show an unavailable/error state rather than a fabricated result.
