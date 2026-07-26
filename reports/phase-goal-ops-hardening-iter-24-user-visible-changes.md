# Phase goal-ops-hardening-iter-24 — User-Visible Changes

**Phase:** goal-ops-hardening-iter-24
**Date:** 2026-07-26
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now see, on **every page** (via the existing top-bar status area next to the "Ready / Initializing… / Snapshot pending / Backend unavailable" pill), whether the backend is currently running a background historical-evidence compute — a small badge reading **"background compute running (N)"** appears the instant one starts and disappears the instant it finishes. Nothing to click; this is a live, read-only indicator.
- Users can now open the **Data Manager page (`/data`)** and see full detail on background compute activity in a new **"Background compute" panel**, placed directly after the existing Run History panel:
  - Each currently-running window: which as-of date it's for, how long it has been running (elapsed time), and how many of the required calculation steps are done (e.g. "horizons 2/5"), plus its dataset version.
  - The most recently finished window's outcome: succeeded or failed, its duration, and — if it failed — the reason.
  - When nothing has ever run since the backend last started: an explicit "No background compute running. Last outcome: none yet." message instead of a blank panel.
- Users can now understand that this history is **not permanent** — the panel always shows a one-line disclosure ("Since the last backend restart — this history is process-lifetime only, never persisted.") so nobody mistakes the empty state after a restart for "nothing ever happened."

---

## What Changed in the Visible UI

- The top-bar `HealthBadge` (rendered in the app's root layout, so it appears on every page) now conditionally renders one additional badge, `background compute running (N)`, immediately after the existing readiness pill, whenever at least one background compute window is in flight. It is absent whenever none is active, and it appears alongside — never replacing or hiding — the existing readiness pill, in any readiness state (Ready, Initializing, Snapshot pending, or Backend unavailable).
- The Data Manager page (`/data`) gained one new panel, **"Background compute"** (`BackgroundComputePanel`), positioned in the existing vertical panel stack right after the pre-existing `RunHistoryPanel`. It uses the same Card/PanelTitle/Badge visual language as the neighboring `JobProgressPanel` and `RunHistoryPanel` — no new visual style was introduced.
- The panel's hint text (via the existing `PanelTitle` info-hint pattern) explains in plain language what this background compute is: the automatic evidence compute that a historical `/backtest` request can trigger when that date's evidence isn't ready yet.

---

## What Old Behavior Changed

- None. This is purely additive: the existing readiness pill, warmup indicator, provider/seed/symbol badges, and every other panel on `/data` (Job Progress, Run History, Macro Feed, Storage Capacity, Drift Report, Rebuild, Universe Diagnostics, Membership Timeline, Backward History, Missing Data) render exactly as before. No existing field, label, or layout was removed or altered.
- The underlying `/backtest` (and MCP `query_backtest`) behavior for a historical as-of that isn't ready yet is unchanged — it still returns within the existing response-time budget while a background compute proceeds; only the ability to *see* that compute happening is new.

---

## Not Visible Yet

- None. Everything the backend now tracks (dispatch registry bookkeeping, bounded outcome history, the new `background_compute` field on `GET /api/health`) is wired all the way through to the top-bar badge and the new Data Manager panel in this same iteration — there is no backend-only capability left stranded without a UI surface.

<!-- Note: `startup.background_compute_history_size` (config.yaml) is an operator-facing config value, not a UI control — it has no UI surface by design (it's read at backend startup, not exposed as a setting anyone edits in the app). -->
