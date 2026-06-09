# goal-i_can_see_the_wealthy_future_forever-iter-26 Execution Plan

This is the **last buildable wave**. Four Data-Manager journeys (J-37, J-38, J-39, J-35) are
already BUILT, source-proven, and 601-tests-green; they sit at `partial` only because their defining
multi-step browser flows were never captured end-to-end (the live host carries no insufficient
universe member, and the only selectable import sources are live-walled: Yahoo-429 / key-gated). The
single new code enabler is a **deterministic, env-gated, offline `seed` import source** plus a
**throwaway fixture DB** so the browser can drive a real pull / expand to completion offline. J-38 also
needs a tiny Resume-without-key UX fix. After all four capture green with no regression, GOAL_ACHIEVED
becomes reachable (J-22/J-23/J-24 stay honestly NA / non-halting).

## What to Build

- **Backend — env-gated `seed` import source (the only new code).** When `TRENDORA_ENABLE_SEED_IMPORT_SOURCE`
  is set, `compute_provider_availability` appends exactly one catalog entry
  `{id:"seed", label:"Seed (offline test data)", needs_key:false, env_var:null, supports_market_cap:true, available:true, reason:...}`.
  When the flag is unset the entry is ABSENT. `make_provider("seed", ...)` already resolves to
  `SeedProvider` (no change). A `source=="seed"` job must dispatch through the EXISTING J-34 chunked
  engine + the EXISTING `screen_reasons`/expand predicate — NO second fetch path, NO second screen rule.
- **Backend — accept `seed` as a valid job source.** The `validate_job_request`/`start_data_job` source
  gate (`data_manager.py:805-823`) validates `source` against `cfg.data_manager.provider_by_id`. The
  env-gated `seed` source is NOT in the committed `config.yaml` catalog, so the validator must also accept
  `seed` **only when the env flag is set** (mirror the same gate the availability list uses). It needs no
  key (`needs_key:false`) and `supports_market_cap:true` so it passes the expand eligibility gate.
- **Backend (QA-owned) — fixture DB builder.** A small seed-builder script under `apps/backend` (e.g.
  `scripts/build_qa_fixture_db.py`) that writes a THROWAWAY/temp DB seeded with: (a) one universe member
  with **no history**, (b) one with **thin history** (below `indicators.min_history_bars`), (c) one with an
  **intra-series date gap** — and bars the `seed` source can supply to complete a pull/expand. MUST NOT
  mutate the committed `apps/backend/data/seed/` tree or the live host DB.
- **Frontend — J-38 Resume-without-key UX fix (the iter-25 UT-11 FAIL).** Verify the existing
  `ResumeControl` inline-error path (`page.tsx:1265,1275-1276,1321-1325` — `role="alert"`) actually renders
  on a 400, and that `onResumed`/`loadOverview` runs ONLY on success (already gated: line 1274 sits after
  the `await` inside the `try`). If any reload path can drop the row on a FAILED resume, gate it so a
  failed resume never reloads the list. Surgical: no new state, no new component.
- **No other frontend change.** J-37 diagnostic+pull panel, J-39 remove/confirm-preview, and J-35 expand
  are already built — this iter only CAPTURES their flows against the `seed` source + fixture.

## Agents Required

- backend-data: yes -- env-gated `seed` import source in `compute_provider_availability` + source-validator
  acceptance gate; the QA fixture-DB builder script; unit tests for both gates (present-when-flag /
  absent-without-flag, `seed` job dispatches through the existing engine + screen, key-leak regression,
  gap-exact + idempotent pull constructor, fixture writes only to a temp DB).
- frontend-ux: yes -- the small J-38 Resume-without-key inline-error verification/gate on `/data` only.

## Frontend Present

Frontend Present: yes

## Files to Create/Modify

- `apps/backend/app/engine/data_manager.py` -- env-gated `seed` entry in `compute_provider_availability`; accept `seed` in the `start_data_job`/`validate_job_request` source gate when the flag is set (no second fetch/screen path).
- `apps/backend/scripts/build_qa_fixture_db.py` (new) -- builds a throwaway fixture DB with no-history / thin / intra-series-gap members; never mutates committed seed or the live host DB.
- `apps/backend/tests/test_data_manager.py` -- `seed` present-only-when-flagged / absent-otherwise; `seed` job routes through the J-34 engine + screen predicate; gap-exact + idempotent (INSERT-new-only) pull constructor; fixture-builder writes only to temp.
- `apps/backend/tests/test_api_data.py` -- `seed` source surfaced in `GET /api/data` under the flag; `seed` job dispatch via `POST /api/data/jobs`; REAL-httpx key-leak regression through the pull/retry/resume job-status surface (sentinel + `?token=`/`?apikey=` ABSENT).
- `apps/frontend/app/data/page.tsx` -- J-38 `ResumeControl`: confirm/gate the inline `role="alert"` error on a 400 and that a FAILED resume never reloads-away the row.

## UI Evolution

- New user-facing capability (production): none. The four target journeys' capabilities already exist on `/data`; this iter makes their flows demonstrable offline and fixes one error-feedback gap.
- New information displayed (production): none. The `seed` source appears in the source picker ONLY in the QA harness (env-gated, off by default, never in the committed catalog).
- New user actions: none new. The J-38 Resume control now shows a visible inline error on a needs-key-without-key failure (existing button, clearer feedback).
- UI surface changes: `/data` (Data Manager) only — the J-38 Resume control's failed-state feedback. No new pages, panels, routes, or nav entries.
- Navigation changes: none. All work homes on the existing approved `/data` page (sidebar, 1 click). No `blueprint.reapproval-requested`.

## Visual Requirements

- Component patterns: reuse the EXISTING `/data` components — the unified `UnfinishedImportsPanel` / `ResumeControl`, the `MissingDataDiagnosticPanel`, the remove/confirm-preview surface, and the existing source picker. No new component.
- Layout: unchanged dense dark `/data` Data Manager page (sidebar + main content); additive feedback only.
- Key visual effects: the inline error uses the existing `role="alert"` + `text-neg` treatment already present on `ResumeControl`; no new effects.
- States to handle on the Resume control: failed (visible inline error, row STAYS), success (continues from `next_chunk_index`, list refreshes), busy (existing spinner). Empty diagnostic → existing clean empty-state.

## Out of Scope (flagged — exclude)

- **Shipping `seed` enabled in production** — it stays OFF by default and ABSENT from the committed
  `config.yaml` catalog (test/dev harness affordance only).
- **J-22 / J-23 / J-24** — externally Yahoo-429 data-walled, NON-HALTING / NON-VETOING per `docs/goal.md`
  lines 989–1012. Do NOT autonomously re-probe a live provider.
- Any change to the diagnostic computation, pull-job constructor, expand screen rule, universe artifact
  writer, J-39 removal/cascade logic, or the J-34 engine — all integration-proven; capture, do not rebuild.
- Any live network fetch in the capture path (captures run against the offline `seed` source).
- Any new page, route, sidebar entry, or second date control; any DB regen; any change to
  scoring/scanner/regime/patterns/forward_testing/research or the `/stocks` · `/backtest` · `/research`
  pages (J-06/J-07/J-15 must stay byte-identical).
- The legacy `resumable_imports` array deprecation (advisory carry-over) — do NOT action unless it
  surfaces a visible duplicate in the browser.

## Key Test Scenarios

- **Env-fix gate BEFORE any UI** (MEMORY `browser-qa-dead-shell-next-cache`, `dev-server-cleanup-by-port`):
  stop strays BY PORT (no broad `pkill`), `rm -rf apps/frontend/.next`, restart `next dev`, confirm
  `GET /_next/static/chunks/main-app.js` → 200 + health badge cleared. Never run a prod `npm run build`
  against the live dev `.next`. Serialize Chrome access (no concurrent qa + browser-qa on the shared tab).
- **J-37:** against the fixture, the diagnostic renders ALL THREE categories (no-history / thin /
  intra-series-gap) each with the exact shortfall + symbol; **Pull the missing data** (and **Pull all
  missing**) constructs a job whose `symbols` + `[start,end]` EQUAL the diagnosed gap (assert via the
  network request body — NOT the whole universe/window); the job runs to COMPLETION over `seed`; the
  diagnostic row clears/shrinks and the J-36 coverage table reflects the new bars. Honest empty-state +
  provider-failure no-fabrication paths stay green.
- **J-38:** a SUCCESSFUL Resume continues from `next_chunk_index` (the never-captured success leg —
  survives a restart); a needs-key Resume-without-key → 400 shows a VISIBLE inline error AND the row STAYS
  (the UT-11 fix); Retry, Dismiss-preserves-audit (Run history unchanged), key re-prompt, key-not-echoed
  (sentinel only as `type=password` value, 0× in job card / unfinished panel). Capture DISTINCT sha256
  before/after shots (no iter-25 byte-identical collisions).
- **J-39:** confirm-preview (removable bars + range + protected committed-seed breakdown + dependent
  cascade) via the **preview** endpoint on the LIVE host (deletes nothing — MEMORY
  `j39-live-host-has-user-added-nvda-bars`); the destructive confirm + consistency cascade + seed-only
  refusal captured against the **fixture** (NEVER destructive on a real live symbol).
- **J-35:** a `seed`-source expand runs end-to-end → passers + omitted-with-reason list + a GROWN
  universe-count, with `/methodology` size matching.
- **J-18 (watch risk):** DOM-assert exactly ONE date `<select>` (the global as-of) on `/data`; the J-38 fix
  and the `seed` source add ZERO date state.
- **J-33 key-leak (critical):** a REAL-httpx error path through the pull/retry/resume job-status surface
  asserts the session key + `?token=`/`?apikey=` are ABSENT from `GET /api/data/jobs/{id}` + the job card
  (MEMORY `httpx-error-leaks-url-query-key`).
- **Unit/integration:** `seed` exposed in `compute_provider_availability` ONLY when the flag is set
  (assert both states); a `source=="seed"` job dispatches through `start_data_job` / the J-34 engine + the
  `screen_reasons` predicate (no fork); the pull constructor is per-`(symbol,date)` idempotent
  (INSERT-new-only, re-run stores no duplicate); the fixture builder writes only to a temp DB.
- **No regressions:** full backend suite green (heavy ~14 min — MEMORY `backend-test-suite-runtime`; don't
  run two pytest invocations concurrently). No `table=True` model is expected; if one is added, update
  `tests/test_db.py:37` in the SAME change (iter-22 lesson). J-06/J-07/J-15/J-08/J-34/J-36 stay green; no
  DB regen.
- **Dev handoff** at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-26-dev.md`, stating
  honestly that the live-provider paths were NOT exercised (data-walled, non-halting) and the captures ran
  against the deterministic `seed` source + fixture DB.

## Assumptions

- The `seed` import source is exposed via the SINGLE existing `compute_provider_availability` producer
  (env-gated append) and the SINGLE existing source-validation gate — no parallel catalog or second
  serving path is introduced, so no Data-Contract value row is added (blueprint-conforming; a one-line
  advisory note in the blueprint's `/data` section is permissible but not required).
- The J-38 Resume inline-error wiring already exists (`page.tsx:1265,1275-1276,1321-1325`) and `onResumed`
  already fires only on success; the frontend work is verification + a defensive gate, not a rewrite.
- The fixture DB is built/booted by the QA harness on a temp path; it is not committed and never touches
  the live host `apps/backend/data/trendora.db` or `apps/backend/data/seed/`.
