# Phase goal-i_can_see_the_wealthy_future_forever-iter-22 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-22
**Date:** 2026-06-07
**Written by:** ui-impact-analyst

All visible changes land on the **existing `/data` (Data Manager)** page. No new page, route, or
navigation entry was added.

---

## What Users Can Now Do

- See **how far a large import has progressed** — when a data import runs in chunks, the live job card now
  shows a `chunk X/N` badge so the user can watch it advance through the symbol/date batches.
- **Recognize a rate-limit pause as recoverable, not a failure** — when a data provider rate-limits the
  import, the job card now shows an amber *"rate-limited — resumable"* state (distinct from a red *failed*
  state) with how many symbols are done vs remaining.
- **Resume a paused import** by clicking the amber **Resume** button on the job card; the import continues
  from the next un-fetched chunk without re-fetching or duplicating any data already saved.
- **Resume an import even after the backend was restarted** — a new **"Resumable imports"** panel lists
  paused imports that survived a restart (the in-memory job is gone but the saved progress persists), each
  with its own Resume button.
- **Re-supply a session-only API key when resuming a key-gated source** — if the import used a provider that
  needs a key and no key is set in the environment, Resume reveals a masked (password) field to paste the
  key for that one action; it is cleared the instant Resume is submitted and never stored.

---

## What Changed in the Visible UI

- The **job card** (`JobProgressPanel`) now renders a `chunk X/N` badge beside the status badge whenever the
  job is chunked.
- The **job card status badge** now shows *"rate-limited — resumable"* in amber when a job is paused by a
  rate limit, in addition to the existing running / ok / partial / failed states.
- A new **amber callout** on the job card states the pause point (chunk X/N), symbols done vs remaining, and
  hosts the **Resume** button.
- A new **"Resumable imports" panel card** appears below the job card listing each paused import with its
  source, date range, chunk X/N, symbols done / remaining / failed, bars-so-far, and a Resume button. The
  panel is hidden entirely when nothing is paused.
- The **Resume control** conditionally shows a masked session-only API key field (only for a needs-key
  source with no environment key).

---

## What Old Behavior Changed

- **Job progress header source label:** a *backfill-only* (seed/backfill) job no longer shows an "import
  source" in its progress header — the source line now appears only for fetch-kind jobs. Previously a
  backfill job could surface a source label that did not correspond to a fetch.
- **Import provider errors no longer leak the API key:** error messages surfaced from a failed/rate-limited
  import (on the job card, job-status response, and run history) are now redacted — the provider URL's query
  string (which carried `?token=…` / `?apikey=…`) is stripped before the message is shown. Previously a
  failing key-gated fetch could surface the pasted key in the error text. (Security fix — gates J-33.)

---

## Not Visible Yet

- **A fully-completed live chunked import is not reachable in this environment** — the external providers
  available to this host are rate-limited (Yahoo 429) or key-gated (Stooq), so the *success* end-state of a
  multi-chunk live import cannot be demonstrated offline. The chunk indicator, amber resumable state, Resume
  affordance, and post-restart resumable-imports list are all exercisable; a real Yahoo 429 drives the
  retry → resumable → Resume path. This is the spec's expected non-halting outcome, not a missing UI.
