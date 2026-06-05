# goal-i_can_see_the_wealthy_future_forever-iter-21 Execution Plan

**Journey:** J-33 — Import real data from a selectable, key-aware provider source (the foundation iter-22 J-34 + iter-23 J-35 build on).
**Depth:** full. **Frontend:** yes. **DB regen:** NO (confined to the provider package + `/data` + config — zero scoring/snapshot/forward-side touch, so the 29 carried journeys are byte-identical and cannot regress).

Goal-alignment: J-33 is a Must-have journey in `docs/goal.md` (lines 762–782) + Key Capability #20. Spec is on-goal — no scope drift. J-34/J-35 are explicitly OUT OF SCOPE.

---

## What to Build

**Backend**
- **Config provider catalog** (`config.yaml` + `apps/backend/app/config.py`). Add `data_manager.providers` — a list, each entry `{id, label, needs_key: bool, env_var: str, supports_market_cap: bool}` for `yahoo`, `stooq`, `tiingo`, `finnhub`, `alpha_vantage`. Add `data_manager.default_source` (used when a job omits `source`). New typed `ProviderCatalogEntry` + `ProviderCatalogCfg` Pydantic models with **boot validation → `ConfigError`**: unique `id`s; `env_var` present whenever `needs_key`; `default_source ∈ catalog`. **Retire the 2-value `Literal`** on the import/live provider (`DataManagerCfg.live_provider`) — validate the import source against the catalog instead. The top-level `provider: seed` (offline boot default) **stays unchanged** and `seed` is **not** in the import catalog.
- **Provider clients** (`apps/backend/app/data_providers/`). Extend `make_provider(name, *, api_key: Optional[str] = None, seed_dir=...)` to resolve every catalog `id` (keep `seed` + `stooq`). Add thin, lazy-imported EOD clients `yahoo_provider.py` (no-key), `tiingo_provider.py`, `finnhub_provider.py`, `alpha_vantage_provider.py` (key-aware) behind the existing `PriceProvider.get_daily` contract — each a single documented GET → parse JSON → ascending `Bar`s; **any non-OK status / network error / unparseable body → `ProviderUnavailableError`** (never a fabricated bar). A `needs_key` provider constructed with no env key **and** no passed `api_key` raises `ProviderUnavailableError` with an explicit "key required" message.
- **Env-detected availability** (`apps/backend/app/engine/data_manager.py`). Add `compute_provider_availability(cfg)` → per catalog entry `{id, label, needs_key, env_var, supports_market_cap, available, reason}` where `available = (not needs_key) or bool(os.environ.get(env_var))`, evaluated at request time. Returns the env-var **name** + boolean + human reason ONLY — never the env value, never any key.
- **Thread `source` + session-only `api_key` through the job** (`api/data.py` + `data_manager.py`). `JobCreate` gains `source: Optional[str]` (default `cfg.data_manager.default_source`; validated ∈ catalog) and `api_key: Optional[str]` (request-only). `validate_job_request` / `start_data_job` / `run_data_job` / `_do_fetch` accept + forward them; `make_provider(source, api_key=api_key)` replaces `make_provider(cfg.data_manager.live_provider)`. `_provider_label` records the **chosen source id** (not secret). `needs_key` source with neither env nor pasted key → explicit **400** ("source `<id>` requires a key; set `$<ENV_VAR>` or paste a session key"); unknown source → **400/422**.
- **Extend `GET /api/data`** to add a `sources` array (the `compute_provider_availability` output). `GET /api/data/jobs/{id}` + run-history responses MUST NOT contain the key.

**Frontend**
- **Import-source control** (`apps/frontend/app/data/page.tsx`). In `JobForm` (shown when kind is `fetch`/`both`), add an **Import source** `<Select>` populated **from `data.sources`** (no hardcoded provider list). Each option shows availability ("available" / "needs key"). When a `needs_key` source with no env key is selected, render a **session-only key paste field** (`type="password"`) held in component `useState` **memory only** (never `localStorage`/URL/cookie; cleared on unmount + on job completion). Send `source` + `api_key` with the job start.
- **`apps/frontend/lib/api.ts`** — add a `ProviderSource` type + `sources` field on `DataOverviewResponse`; extend `startDataJob(kind, start, end, opts?: { source?; api_key? })` to send `source`/`api_key` (omit `api_key` when blank).
- **Opportunistic cleanup** — `page.tsx:141` subtitle "grow the System Health evidence" → "grow the Backtest evidence" (the open iter-17 minor advisory).

---

## Agents Required
- **developer: yes** — backend (config catalog + typed models + boot validation; provider clients; availability; job threading; `/api/data` extension) **and** frontend (source picker + session-only key field + `api.ts` + subtitle fix). One developer pass covers both.
- backend-data: **yes**
- frontend-ux: **yes**

## Frontend Present
yes

---

## Files to Create/Modify
- `config.yaml` — add `data_manager.providers` (5-source catalog) + `data_manager.default_source`.
- `apps/backend/app/config.py` — `ProviderCatalogEntry` + `ProviderCatalogCfg` models; retire `live_provider` 2-value `Literal`; boot validation (unique ids / `env_var`-when-`needs_key` / `default_source ∈ catalog`).
- `apps/backend/app/data_providers/__init__.py` — `make_provider(name, *, api_key=None, seed_dir=...)` resolves every catalog id.
- `apps/backend/app/data_providers/yahoo_provider.py` *(new)*, `tiingo_provider.py` *(new)*, `finnhub_provider.py` *(new)*, `alpha_vantage_provider.py` *(new)* — thin EOD clients (mirror `stooq_provider.py`'s raise-never-fabricate contract; JSON parse; lazy-imported).
- `apps/backend/app/engine/data_manager.py` — `compute_provider_availability(cfg)`; thread `source`/`api_key` through `validate_job_request`/`run_data_job`/`start_data_job`/`_do_fetch`; `_provider_label` → chosen source id.
- `apps/backend/app/api/data.py` — `JobCreate.source`/`api_key`; `/api/data` `sources`; 400 for needs-key-without-key; pass through to engine.
- `apps/frontend/app/data/page.tsx` — Import-source `<Select>` + conditional session-only key field; subtitle fix.
- `apps/frontend/lib/api.ts` — `ProviderSource` type; `sources` on `DataOverviewResponse`; `startDataJob` `opts`.
- Tests: `apps/backend/tests/` — new unit/integration tests (see Key Test Scenarios). Frontend behaviour covered by browser QA.
- `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-21-dev.md` — dev handoff.
- `blueprint.md` — **already updated** (iter-21 note line 92, J-33 row line 127, Data-Contract row line 186). Developer **verifies only**; do NOT duplicate; **do NOT write `blueprint.reapproval-requested`** (additive under the approved `/data` home).

---

## UI Evolution
- **New user-facing capability:** choose *which provider* an import fetches from; see at a glance which providers are ready (env key present / no key needed) vs which need a key; paste a key for the run without it ever being saved.
- **New information displayed:** the import provider catalog with per-source availability ("available" / "needs key" + the env-var name) on `/data`.
- **New user actions:** select an import source; paste a session-only API key for a key-required source; start a fetch/backfill/both job against the chosen source.
- **UI surface changes:** `/data` `JobForm` gains an Import-source selector + a conditional session-only key field. No new page/route.
- **Navigation changes:** none.

## Visual Requirements
- **Component patterns:** reuse the existing `Select` (`@/components/ui/select`, native-`<select>` wrapper already used for Job kind) for the source picker; reuse `FIELD` styling + a `type="password"` `<input>` for the key paste (mirror the existing date inputs). Reuse `Badge`/`statusVariant` idiom for the per-source availability tag.
- **Layout:** additive rows inside the existing `JobForm` `Card` — no layout restructure.
- **Key visual effects:** dark analytical workstation tokens already in the file (`--surface-2`, `--border`, `--accent`, `--pos`/`--neg`/`--warn`); availability uses `text-pos` (available) / `text-warn` (needs key). Numbers stay `num`/tabular.
- **States to handle:** source list empty/loading (reuse existing skeleton/error states); needs-key-no-env (reveal key field); key field is write-only (value never echoed back from the API into the field); clear key on unmount + job completion.

---

## Key Test Scenarios

**Browser (J-33, by ID — `Frontend Present: yes`):**
- On `/data`, open the **Import source** control → catalog renders from config (named sources appear) with per-source availability. Use the **native-setter + bubbling-`change`** pattern for the `<select>` then assert live DOM (MEMORY `react-controlled-select-needs-native-setter` — the Chrome-MCP `select` action does NOT fire React `onChange` on this frontend).
- Select a **needs-key** source with no env key → the **session-only key paste field** appears.
- Confirm **no date/as-of control was added** — exactly one date `<select>` app-wide (the global header switcher); `/data` import dates stay `type="date"` job-parameter inputs (**J-18**).
- Start a **fetch** against a selected source while the provider is walled → explicit **error / unavailable** job state ("no data fabricated"), no fabricated bar, key not echoed in the job card or run history.
- Existing **backfill** path still runs end-to-end (J-17): default source, offline/deterministic, snapshots created.

**Unit/integration (MUST have tests):**
- Catalog is **config-driven** (list comes from `config.yaml`, not code) and **boot validation raises `ConfigError`** on: missing `env_var` when `needs_key`, duplicate `id`, `default_source ∉ catalog`.
- `compute_provider_availability` is **env-detected**: needs-key source `available` only when its `env_var` is set; no-key source always `available`; the env value / key never in the output.
- `make_provider` resolves every catalog `id`; each new client raises `ProviderUnavailableError` on a non-OK / unparseable response (**mocked HTTP — no live call**) and never returns a fabricated bar; a needs-key provider with no key raises an explicit error.
- **Key-never-persisted (THE principal anti-goal):** run a job (injected/mocked provider) with a pasted `api_key`; assert the key string is **absent from every `DataProviderRun` column, from `GET /api/data`, from `GET /api/data/jobs/{id}`, and from logs**.
- `source` omitted ⇒ defaults to `cfg.data_manager.default_source` (J-17 fetch preserved); unknown `source` ⇒ 400/422; needs-key source with no env/pasted key ⇒ explicit **400**.

Run pytest **once** (full suite ~14 min — MEMORY `backend-test-suite-runtime`; do not run two pytest invocations concurrently). Frontend: build to a separate dir or before starting `next dev`; confirm `GET /_next/static/chunks/main-app.js` → 200 + the health badge clears before browser QA (MEMORY `browser-qa-dead-shell-next-cache`).

---

## Critical Guardrails & Documented Assumptions

1. **Principal anti-goal — "Import keys are env-or-session, never persisted."** Verify *in source* (not just QA): `api_key` is request-only — never on `JobProgress`, never in `_persist_run`'s detail JSON, never on `DataProviderRun` (any column), never logged, never in any response. The catalog/availability value carries only the env-var **name** + a boolean + a human reason.
2. **Principal anti-goal — J-18 "exactly one date selector."** The new source/key controls add **NO date state**. Import dates stay `type="date"` job-parameter inputs; the only date `<select>` remains the global header switcher. (journey-history flags this exact iteration as the J-18 WATCH item.)
3. **`default_source` MUST be a no-key source** (assumption: **`yahoo`**, no-key, listed first in the goal) so an omitted-`source` `fetch`/`both` job never 400s — otherwise J-17's fetch path regresses. (Today's `live_provider: stooq` is being superseded by the catalog; Stooq is `needs_key` in this environment per the iter-3 lesson.)
4. **Config-fixture fan-out (MEMORY `config-fixtures-need-new-required-keys`).** Adding required typed fields (`providers`, `default_source`) to the config schema means updating **all** inline test config dicts (MINIMAL_VALID, VALID, and the per-test sector/theme dicts) — otherwise the suite fails at collection. Account for this before claiming green.
5. **Live fetch is data-walled & non-halting.** A *successful* real import is NOT autonomously reachable (Yahoo 429-walls this IP; Stooq is key-gated — MEMORY `data-provider-access-constraints`). Prove ALL machinery (catalog, availability, key handling, explicit-error path) **offline with an injected/mocked provider** — **no live network call in tests or the pipeline**. The live-fetch outcome is recorded honestly as NA/rate-limited and MUST NOT halt the loop, drive STALLED, or veto GOAL_ACHIEVED. Do NOT autonomously probe live providers or retry J-22/23/24.
6. **No fabricated data.** Every provider failure path raises `ProviderUnavailableError` and surfaces an explicit error/unavailable job state — zero synthesized bars.
7. **Out of scope (do NOT build):** J-34 checkpoint/resume/backoff machinery; J-35 `expand` job kind / `universe_pool.csv` screen; any change to scoring/snapshot/forward/research/read-serving paths; persisting any key; a second viewing-date control. `supports_market_cap` is declared in the catalog now but consumed only by J-35.

## Process notes
- A `-audit.md` handoff is typically not produced for full-depth iters in this session; `status.json` is written to the phase-namespace path `runs/goal-i_can_see_the_wealthy_future_forever-iter-21/status.json`. Verify seams in source; check both namespace paths.
- Definition of Done (spec): J-33 browser-green; J-17 + J-18 still green; key-never-persisted unit test; full backend suite green (run once); frontend builds clean; blueprint verified (no reapproval marker); dev handoff written.
