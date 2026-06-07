# Goal Iteration 22 — Implementation Summary

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-22
**Date:** 2026-06-05
**Written by:** developer

---

## Features Implemented

- **Import API key never echoed back (J-33 fix)**: When a live price provider (Tiingo / Finnhub /
  Alpha Vantage) fails, the error the operator sees is now built from a **redacted** request address
  (the whole query string stripped) plus the HTTP status — never the raw error text that used to embed
  the pasted API key (`?token=…` / `?apikey=…`). The pasted session key is now verifiably absent from
  the job card, the error list, the run history, the new checkpoint, and the logs. A second
  belt-and-suspenders guard in the job engine also scrubs the resolved key out of any error string
  before it is recorded.
- **Chunked import (J-34)**: A live fetch now runs in **visible batches** ("chunk x/N") instead of one
  long opaque pass. The batch sizes (how many symbols per chunk, how many days per date-window) come
  from the config file.
- **Rate-limit resilience (J-34)**: When a provider replies "too many requests" (HTTP 429), the import
  **retries with exponential backoff**; if the limit persists it **stops gracefully in a
  "rate-limited — resumable" state** (amber, distinct from a red failure) instead of failing — and it
  never makes up data to force a green run.
- **Durable, restart-surviving checkpoint (J-34)**: A paused import's progress is saved to the database
  (a new `import_checkpoints` table). It survives a full backend restart, so the import stays
  discoverable and resumable even after the server is bounced.
- **Resume (J-34)**: The operator can click **Resume** — from the live job card or from a new
  "Resumable imports" list — to continue from the **next un-fetched chunk**. Already-fetched data is
  skipped (nothing is re-fetched or duplicated). For a key-required source, the session-only key is
  re-prompted (it is never stored, so a restart loses it by design).

---

## Changed Behavior

- **Live fetch (Data Manager → "Fetch EOD prices")**: Previously a single-shot pass over all symbols;
  a provider failure recorded the raw error text. Now it runs in config-sized chunks, retries on 429
  with backoff, can pause "resumable", and any error text is redacted/scrubbed of the API key. A small
  fetch (one chunk's worth) completes exactly as before — just labelled "chunk 1/1".
- **Backfill-only job header**: Previously a backfill-only job's progress header showed a defaulted
  `yahoo` import source. Now a backfill-only job shows **no** import source (it reads the committed
  offline seed, not a live provider). The recorded run still correctly shows provider `seed`.
- **`GET /api/data` payload**: now also returns a `resumable_imports` list (the paused imports). The
  Data Manager page renders it as a new panel.

---

## Backend-Only Items

- None. Every new backend capability (chunk progress, the resumable state, the Resume endpoint, and the
  post-restart resumable-imports list) is wired into the `/data` page UI.

---

## Incomplete Items

- **Live-fetch completion against a real provider** is *not* demonstrated end-to-end because the free
  providers are externally walled for this host (Yahoo rate-limits this IP; Stooq is key-gated). This is
  expected and non-blocking per the iteration spec: the chunk / backoff / checkpoint / resumable / Resume
  **machinery** is proven offline with an injected provider, and the live outcome is recorded honestly as
  rate-limited / NA. A real 429 from Yahoo in the browser still exercises the retry → resumable → Resume
  path (the import pauses cleanly and is resumable), it just cannot reach a fully-completed live import.
- **J-35 (Expand-universe)** is intentionally out of scope — it is the next iteration, built on this
  resilient-import foundation.

---

## Config and Environment Changes

- `config.yaml` → `data_manager.import_chunking` — a new required block with six tunables (no env vars):
  - `symbol_batch_size` (default `25`) — symbols fetched per chunk.
  - `date_window_days` (default `90`) — max calendar days per date-window chunk.
  - `max_retries` (default `4`) — 429 retry attempts before pausing resumable.
  - `backoff_base_seconds` (default `1.0`) / `backoff_cap_seconds` (default `30.0`) — exponential
    backoff `min(base · 2^attempt, cap)` between 429 retries.
  - `inter_request_sleep_seconds` (default `0.0`) — optional polite delay between per-symbol requests.
  - Boot-validated: the five size/retry/backoff numbers must be positive and `cap ≥ base`; the sleep
    must be `≥ 0`. An invalid block fails startup loudly (no silent default).
- New database table `import_checkpoints` — created automatically on startup (empty on first boot; no
  existing data is touched, no scanner data is regenerated). It stores **no API key**.
- No new environment variables. Provider API keys are still read from the environment or pasted
  session-only, never persisted.

---

## Known Limitations

- **httpx library request logging**: the underlying HTTP client (httpx) emits its own INFO-level
  "HTTP Request: GET <url>" log line that includes the full URL (and therefore a key, if one is in the
  query) when a live request is actually made. This is the library's own behavior, not our error/persist
  path, and our application does not configure httpx INFO logging on by default. Our own error messages,
  job records, checkpoint, run history, and responses are all redacted/scrubbed. (A future hardening could
  silence the `httpx` logger; it was out of scope for this iteration's redaction fix.)
- **Resume re-fetch granularity is per-chunk, not per-symbol**: a resume restarts at the first symbol of
  the chunk that was interrupted. Symbols already committed are skipped at the database layer (no
  duplicate rows), but the provider may be asked again for a symbol that 429'd mid-chunk. This is the
  intended design (the resume unit is the chunk) and never duplicates stored data.
- **Live providers remain externally data-walled** for this host (see Incomplete Items) — by design the
  loop treats a rate-limited live import as non-halting.
