# Goal Iteration 21 — Import source picker: a config-driven, key-aware provider catalog on the Data Manager (J-33)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever
- **Iteration:** 21
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-33
- **Required-still-passing journeys:** J-17 (the existing Data Manager fetch/backfill must keep working — same page + engine), J-18 (exactly one date selector — the import source/key controls add NO date state; import dates stay job parameters). Plus structurally carried (zero change to their paths): J-01–J-16, J-19–J-21, J-25–J-32, and J-15 (read path untouched).
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **Import keys are env-or-session, never persisted.** The import provider catalog and each provider's key-requirement + env-var name MUST come from config (no hardcoded provider list in code); a provider key MUST be read from the environment, or — if the user pastes one into the import UI — held **in memory for that run only**, **never written to disk, the run log, the DB, or any committed file, and never echoed back** in any response. The import's date inputs are **job parameters, not a second date control** (the single global as-of switcher stays the only date selector). *(extends Live fetch is real-data-only + Exactly one date selector)*
  - **Live fetch is real-data-only.** The Data Manager MUST use the config-selected live provider to fetch real EOD bars; on a provider failure it MUST surface an explicit error and MUST NOT synthesize prices to fill a gap or force a successful run. *(extends No fabricated data)*
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey.
  - **No secrets in source.** No hard-coded credentials, API keys, or tokens anywhere; the default seed path requires none, and any live-provider key is read only from the environment.
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code. (Here: the provider catalog + every job limit live in `config.yaml`.)
  - **Exactly one date selector.** The frontend MUST NOT maintain a second, independent date state; every date-scoped page reads the single global as-of control.

## GOAL

A user on `/data` can open an **Import source** control, see a **config-driven catalog** of EOD providers (Yahoo, Tiingo, Finnhub, Alpha Vantage, Stooq) each marked **available** (env key present, or no key needed) or **needs key** (with a **session-only** paste field), pick a source, and start an import against it — and on a provider failure read an explicit error/unavailable state, never a fabricated bar. A pasted key is held in memory for the run only and is verifiably absent from `/api/data`, the run history, and the database.

## BACKGROUND

The operator re-scoped `docs/goal.md` (commit `d3e5076`, 2026-06-04) to add three new Must-have import journeys — **J-33** (selectable, key-aware provider source), **J-34** (chunked, rate-limit-resilient, resumable import), **J-35** (Expand-universe from the Data Manager). The iter-20 evaluation (CONTINUE) confirmed all three are **unbuilt in source** (the iter-20 "session-complete" framing was stale — written 90s after the re-scope commit) and recommended **full depth, build order J-33 → J-34 → J-35**, all offline-testable with an **injected provider** stub. `goal.md` (lines 838–844) is explicit: the catalog + key-detection + chunk/resume/checkpoint + expand-screen **machinery is buildable and fully testable offline**; only the *successful live-fetch outcome* is data-gated (recorded NA/non-halting when every provider is Yahoo-429 walled).

This iteration delivers **J-33 only** — the foundation the other two build on. The chain is strictly ordered (J-34's chunked/resumable import threads the source J-33 selects; J-35's Expand job runs as a chunked/resumable import over the selected source), and each journey crosses backend + frontend + config + new tests, so per the decomposer rule *"smaller iterations are easier for the evaluator to score"* they are split one-per-iteration: **iter-21 → J-33**, iter-22 → J-34, iter-23 → J-35.

Why **full** depth: J-33 crosses backend + frontend + config, extends the **provider abstraction** (new provider clients), introduces a new typed config catalog with boot validation, and needs real unit tests beyond browser smoke (catalog-from-config, env-detection, **key-never-persisted**, provider-failure → explicit error). The iter-20 eval explicitly recommended full.

**Current state (code-verified this iteration):**
- `apps/backend/app/api/data.py` — `JobCreate` is `kind: Literal["fetch","backfill","both"]` + `start`/`end` only. **No `source`/`api_key`.**
- `config.yaml` — `provider: seed` (offline boot/runtime default) + `data_manager.live_provider: stooq` (single hardcoded live provider). **No catalog, no `needs_key`/`env_var`.** `config.py` constrains the live provider to a 2-value Literal.
- `apps/backend/app/data_providers/` — `base.py` (`PriceProvider.get_daily` / `ProviderUnavailableError` / `Bar`), `seed_provider.py`, `stooq_provider.py`; `make_provider(name)` resolves only `seed`/`stooq`.
- `apps/backend/app/engine/data_manager.py` — `_do_fetch` calls `make_provider(cfg.data_manager.live_provider)`; the in-memory `JobProgress` + persisted `DataProviderRun` carry no key.
- `apps/frontend/app/data/page.tsx` — JobForm has Start/End/Job-kind only; **no source picker**. The subtitle (line 141) still says "grow the System Health evidence" (stale since the iter-17 System-Health retirement — opportunistic fix while editing this page).

**Lessons applied (from `lessons.md` / journey-history / MEMORY):**
- **iter-20 lesson:** evaluate against the *current* `goal.md`; a dev handoff that *claims* a capability is not proof — confirm it in source. (This spec targets the code-verified-unbuilt J-33; the developer must actually wire it, not restate the vision.)
- **journey-history J-18 WATCH note (the principal risk):** the J-33/34/35 import work "adds import date inputs + a session-key paste — they MUST stay job parameters (not a 2nd viewing-date state) and the key MUST be session-only (never persisted)."
- **MEMORY `data-provider-access-constraints` + iter-3 lesson:** Yahoo 429-walls this IP; Stooq now gates its free CSV behind a key (returns an HTML "apikey required" page). So a **successful live fetch is externally data-walled and non-halting** — tests MUST use an **injected/mocked provider**, never a live network call; the catalog must reflect key requirements honestly (Stooq may need a key in this environment).
- **MEMORY `react-controlled-select-needs-native-setter`:** the Chrome-MCP `select` action does not fire React `onChange` on this frontend — browser QA must use the native-setter + bubbling-change pattern, then assert live DOM.
- **Process note (iters 2/3/6/9–19):** full-depth goal iters here typically produce no `-audit.md` handoff and write `status.json` to the **phase-namespace** path `runs/goal-i_can_see_the_wealthy_future_forever-iter-21/status.json` (not under `runs/goal-session-.../iter-21/`). The evaluator should verify seams in source and check BOTH namespace paths.

## IN SCOPE

### Backend

- [ ] **Config provider catalog (`config.yaml` + `apps/backend/app/config.py`).** Add a config-driven catalog of import sources under `data_manager.providers` — a list, each entry: `id` (e.g. `yahoo`, `stooq`, `tiingo`, `finnhub`, `alpha_vantage`), `label` (display name), `needs_key` (bool), `env_var` (the environment variable name to read the key from; required when `needs_key: true`), and `supports_market_cap` (bool — **consumed by J-35's expand-eligibility gate**; declared now so the catalog schema is stable, default documented). Add `data_manager.default_source` (the import source used when a job omits `source` — preserves J-17 fetch behavior). Add a typed `ProviderCatalogEntry` (and a `ProviderCatalogCfg`) Pydantic/SQLModel config model with **boot validation** raising `ConfigError`: unique `id`s, `env_var` present whenever `needs_key`, `default_source` ∈ the catalog. **Retire the 2-value `Literal` constraint** on the live/import provider (validate against the catalog instead). The offline boot/runtime `provider: seed` stays unchanged (it is the default offline provider, **not** an import source — keep it out of the import catalog).
- [ ] **Provider clients (`apps/backend/app/data_providers/`).** Extend `make_provider(name, *, api_key: Optional[str] = None, seed_dir=...)` to resolve every catalog `id`. Keep `seed` + `stooq`. Add **thin, real EOD clients** behind the existing `PriceProvider.get_daily` contract — `yahoo_provider.py` (no-key; the canonical runbook source listed first in the goal), `tiingo_provider.py`, `finnhub_provider.py`, `alpha_vantage_provider.py` (key-aware via `api_key`). Each is a single documented GET → parse JSON to `Bar`s sorted ascending; **any non-OK status, network error, or unparseable body → `ProviderUnavailableError`** (never a fabricated/placeholder bar). Lazy-import each (as `stooq` is today) so boot pulls in no HTTP path. A `needs_key` provider constructed with neither an env key nor a passed `api_key` raises `ProviderUnavailableError` with an explicit "key required" message — never a silent fallback.
- [ ] **Env-detected availability (`apps/backend/app/engine/data_manager.py`).** Add `compute_provider_availability(cfg)` → for each catalog entry, `{id, label, needs_key, env_var, supports_market_cap, available, reason}` where `available = (not needs_key) or bool(os.environ.get(env_var))`, evaluated **at request time**. It returns only the env-var **name** + a boolean + a human reason — **never the env value and never any key**.
- [ ] **Thread `source` + session-only `api_key` through the job (`api/data.py` + `data_manager.py`).** `JobCreate` gains `source: Optional[str]` (defaults to `cfg.data_manager.default_source`; validated ∈ catalog) and `api_key: Optional[str]` (the pasted **session-only** key, request-only). `run_data_job` / `start_data_job` / `_do_fetch` accept and forward them: `make_provider(source, api_key=api_key)` replaces `make_provider(cfg.data_manager.live_provider)`. The selected **`source` id MAY be recorded** on `DataProviderRun` (`_provider_label` → the chosen source id, not secret); the **`api_key` MUST NOT** be stored on `JobProgress`, in the `_persist_run` detail JSON, on `DataProviderRun`, or in any log. Selecting a `needs_key` source with neither an env key nor a pasted key → explicit `400` ("source `<id>` requires a key; set `$<ENV_VAR>` or paste a session key"), never a silent no-op or fabrication. Unknown `source` → `400`/`422`.
- [ ] **Extend `GET /api/data`** to include a `sources` array (the `compute_provider_availability` output). The job-status (`GET /api/data/jobs/{id}`) and run-history responses MUST NOT contain the key.

### Frontend

- [ ] **Import-source control (`apps/frontend/app/data/page.tsx`).** In the JobForm (shown when the job kind involves a fetch — `fetch`/`both`), add an **Import source** `<Select>` populated **from `data.sources`** (the `GET /api/data` availability list) — **no hardcoded provider list in the component**. Each option shows its availability ("available" / "needs key"). When a `needs_key` source with no env key is selected, render a **session-only key paste field** (`type="password"`), held in component `useState` **memory only** — never written to `localStorage`, the URL, or a cookie; cleared on unmount / job completion. Send the selected `source` + the pasted `api_key` with the job start.
- [ ] **`apps/frontend/lib/api.ts`** — add a `ProviderSource` type + the `sources` field to `DataOverviewResponse`; extend `startDataJob(kind, start, end, opts?: { source?; api_key? })` to send `source`/`api_key` in the POST body (omit `api_key` when blank).
- [ ] **Opportunistic cleanup:** fix the stale `/data` subtitle (line 141 "grow the System Health evidence" → "grow the Backtest evidence", the open iter-17 minor advisory).

### New user-facing capability

On `/data` the user can choose **which provider** an import fetches from, see at a glance which providers are ready (env key present / no key needed) vs which need a key, and paste a key for the run without it ever being saved. A failed import shows an explicit error/unavailable state, never invented prices.

### New information displayed

The **import provider catalog** with per-source availability ("available" / "needs key" + the env-var name) on `/data`.

### New user actions

Select an import source from the catalog; paste a session-only API key for a key-required source; start a fetch/backfill/both job against the chosen source.

### UI surface changes

`/data` JobForm gains an Import-source selector + a conditional session-only key field. No new page, route, or nav entry.

### Product surface delta

The Data Manager stops being hardwired to a single live provider — imports become **source-selectable and key-aware**, the operator-facing foundation for the resilient import (J-34) and the universe expansion (J-35) that unblocks J-22.

### Blueprint conformance

Lives under the **existing `/data` (Data Manager) home** (J-17) — additive only. **No nav-skeleton change → no `blueprint.reapproval-requested` marker.** `blueprint.md` gets an additive iter-21 note + one new Data-Contract row (below).

### Data-contract additions

- **NEW value — Import provider catalog + env-detected availability** (per source: `id`, `label`, `needs_key`, `env_var` name, `supports_market_cap`, `available`, `reason`). Computed once by `app.engine.data_manager:compute_provider_availability` (config-driven; reads `os.environ` for presence only). Served by `GET /api/data` (extended payload field `sources`). The catalog definition lives in `config.yaml` `data_manager.providers` (single source). **No key value is ever computed into, stored in, or served by this value.** This is descriptive availability metadata — **not** a duplicate of any canonical score/return/bucket.
- The **`source` (provider id) + `api_key`** are **job parameters** on `POST /api/data/jobs` (the key is request-only / session-only, never persisted) — not a viewing-date or canonical-value addition.

## OUT OF SCOPE

- **J-34** (chunked / rate-limit-resilient / **resumable** import, durable checkpoint, 429 backoff, Resume action) — iter-22. This iteration keeps the existing single-shot fetch loop; it only makes the *source* selectable. Do NOT build checkpoint/resume/backoff machinery here.
- **J-35** (Expand-universe job kind, `universe_pool.csv` screen) — iter-23. Do NOT add an `expand` job kind here. (The `supports_market_cap` catalog field is declared now but consumed only in J-35.)
- **Any live network call in tests or the pipeline.** A successful live fetch is externally Yahoo/Stooq data-walled and **non-halting** — prove the catalog/availability/key/error machinery with an **injected/mocked provider** only. Do NOT autonomously probe live providers; do NOT autonomously retry J-22/J-23/J-24.
- Any change to the scoring / snapshot / forward-test / research / read-serving paths (`scoring.py`, `scanner.py`, `regime.py`, `patterns.py`, `buckets.py`, `forward_testing.py`, `research.py`, `snapshot_serving.py`, the as-of provider, `/stocks`/`/backtest`/`/research` pages). J-33 is confined to the provider package + `/data` + config → **no DB regen**.
- Persisting a pasted key anywhere, or adding a second viewing-date control.

## DEFINITION OF DONE

- [ ] **J-33 passes via browser-qa-agent** on `/data`: the Import-source control lists the config catalog with correct availability; a needs-key source reveals a session-only key field; selecting a source + starting a fetch produces a real attempt that, when the provider is unavailable, shows an explicit error/unavailable state (no fabricated bar); the pasted key is not echoed back; **no date control is added** (J-18).
- [ ] **Required-still-passing journeys remain green:** J-17 (fetch/backfill still works; `source` omitted ⇒ defaults to `default_source`), J-18 (exactly one date `<select>`; import dates + source/key are job parameters, not a viewing-date state). The 29 carried journeys are unaffected (no source change to their paths).
- [ ] **No anti-goal violation introduced** — in particular, a unit test proves a pasted key is **absent from the DB (`DataProviderRun`, all columns), absent from `GET /api/data` and `GET /api/data/jobs/{id}`, and never logged**.
- [ ] **Unit/integration tests pass; no regressions** (full backend suite green; run pytest **once** — see MEMORY `backend-test-suite-runtime`, ~14 min).
- [ ] Frontend typechecks / builds clean (do NOT run `npm run build` against the live `next dev` `.next` — MEMORY `browser-qa-dead-shell-next-cache` / iter-15 lesson; build to a separate dir or before starting dev, and confirm `GET /_next/static/chunks/main-app.js` → 200 + the health badge clears before browser QA).
- [ ] `blueprint.md` updated (additive iter-21 note + the new Data-Contract row). No reapproval marker written.
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-21-dev.md`.

## TESTING REQUIREMENTS

- **Browser (J-33, by ID):**
  - On `/data`, open the **Import source** control → assert the catalog renders from config (the named sources appear) with per-source availability ("available" / "needs key"). Use the native-setter + bubbling-change pattern for the `<select>` (MEMORY `react-controlled-select-needs-native-setter`), then assert live DOM.
  - Select a **needs-key** source with no env key → the **session-only key paste field** appears.
  - Confirm **no date/as-of control** was added (exactly one date `<select>` exists app-wide — the global switcher in the header; `/data` import dates remain `type="date"` job-parameter inputs) — **J-18**.
  - Start a **fetch** against a selected source while the provider is walled → an **explicit error / unavailable** job state renders ("no data fabricated"), with **no fabricated bar** and the key not echoed in the job card or run history.
  - Confirm the existing **backfill** path still runs end-to-end (J-17): default source, offline/deterministic, snapshots created.
- **Unit/integration (code paths that MUST have tests):**
  - Catalog is **config-driven** (the provider list comes from `config.yaml`, not a hardcoded list) and **boot validation** raises `ConfigError` on: missing `env_var` when `needs_key`, duplicate `id`, `default_source` ∉ catalog.
  - `compute_provider_availability` is **env-detected**: a `needs_key` source is `available` only when its `env_var` is set; a no-key source is always `available`; the env value / key is **never** in the output.
  - `make_provider` resolves every catalog `id`; each new client raises `ProviderUnavailableError` on a non-OK / unparseable HTTP response (**mocked HTTP — no live call**) and never returns a fabricated bar; a `needs_key` provider with no key raises an explicit error.
  - **Key-never-persisted (the principal anti-goal):** run a job (injected/mocked provider) with a pasted `api_key`; assert the key string is absent from every `DataProviderRun` column, from `GET /api/data`, from `GET /api/data/jobs/{id}`, and from logs.
  - `source` omitted ⇒ defaults to `cfg.data_manager.default_source` (J-17 fetch behavior preserved); unknown `source` ⇒ `400`/`422`; `needs_key` source with no env/pasted key ⇒ explicit `400`.
- **Error cases that must be rejected/handled:** unknown source; needs-key source without a key; provider failure (→ `ProviderUnavailableError` surfaced explicitly, job `failed`/`partial`, zero fabricated bars); malformed catalog at boot (→ `ConfigError`).

## NOTES

- **Principal anti-goal risk = "Import keys are env-or-session, never persisted"** (and J-18 "exactly one date selector"). The journey-history J-18 WATCH note flags this exact iteration. Verify in source (not just QA): the key is request-only, never on `JobProgress`/`DataProviderRun`/detail-JSON/logs/responses, and the new source/key controls add **no** date state.
- **Live fetch is data-walled & non-halting.** Per `goal.md` 779–782/838–844 and MEMORY `data-provider-access-constraints` (Yahoo 429) + iter-3 lesson (Stooq now key-gated), a *successful* live import is not autonomously reachable. J-33's **machinery** (catalog, availability, key handling, explicit-error path) is expected to go **green offline** with an injected/mocked provider; the *live-fetch outcome* is recorded honestly as NA/rate-limited and MUST NOT halt the loop, drive STALLED, or veto GOAL_ACHIEVED. Reflect key requirements honestly in the catalog (Stooq may be `needs_key` in this environment).
- **Sequencing:** after J-33 lands green and nothing regresses → iter-22 builds **J-34** (chunked/durable-checkpoint/resumable import, 429→backoff→Resume) on this source foundation; iter-23 builds **J-35** (Expand-universe job over `universe_pool.csv` + the config screen, gated to `supports_market_cap` sources) — the operator-facing path that auto-unblocks J-22. After all three go green offline, **GOAL_ACHIEVED is reachable** on the buildable set (32/32 buildable), with the live-fetch outcome of J-22/23/24/33/34/35 recorded as honestly blocked (NA) / non-halting.
- **Process expectation:** a `-audit.md` handoff is typically not produced for full-depth iters in this session, and `status.json` is written to the **phase-namespace** path `runs/goal-i_can_see_the_wealthy_future_forever-iter-21/status.json`. Not a defect — verify seams in source and check both namespace paths.
- **No DB regen** — J-33 touches no scoring/snapshot/forward-side path, so the 29 carried journeys' stored values are byte-identical and cannot regress.
