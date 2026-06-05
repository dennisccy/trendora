**Verdict:** COHERENCE-PASS

# Coherence Audit — iter-21 (J-33: import source picker on `/data`)

**Session:** i_can_see_the_wealthy_future_forever · **Iteration:** 21 · **Auditor:** coherence-auditor
**Snapshot audited:** `git diff 0df483135043d5eeaee4385644646200f346f768` + uncommitted working tree
**Scope built:** J-33 — config-driven, key-aware import provider catalog + env-detected availability on the existing `/data` (Data Manager) home.

No objective Data-Contract or Information-Architecture violation found. One advisory note (a *resolved* drift). Clean PASS.

---

## Step 1 — Data Contract check (the "numbers don't match" gate) → PASS

The iteration registers exactly **one new value**, and the implementation matches its registered contract row (blueprint.md:186) precisely:

| Registered (blueprint.md:186) | Implemented | OK |
|---|---|---|
| Computed once by `app.engine.data_manager:compute_provider_availability(cfg)` | `data_manager.py` `compute_provider_availability(config)` — the only producer | ✓ |
| Served by `GET /api/data` (extended `sources` field) | `api/data.py` `data_overview` adds `"sources": data_manager.compute_provider_availability(cfg)` — the only serving path | ✓ |
| Descriptive availability metadata, **not** a duplicate of any score/return/bucket | The value is `{id,label,needs_key,env_var,supports_market_cap,available,reason}` — provider readiness, conceptually distinct from every existing canonical value | ✓ |
| `source` + session-only `api_key` are **job parameters** on `POST /api/data/jobs` | `JobCreate.source/api_key` (api/data.py); threaded to `make_provider(source, api_key=...)` | ✓ |

- **No duplicate computation.** The new provider clients (`yahoo`/`tiingo`/`finnhub`/`alpha_vantage`, plus the kept `seed`/`stooq`) implement only the pre-existing `PriceProvider.get_daily` contract — they fetch raw EOD `Bar`s (the scanner's *input*), exactly like `seed`/`stooq` already do. They compute **no** Leadership/Entry-Quality/Risk score, no bucket, no forward return, no regime. No registered canonical value is recomputed in a new code path.
- **No non-canonical source.** The frontend renders `data.sources` **verbatim** (`page.tsx`: `sources.find(s => s.id === source)` → label / availability / reason re-displayed; `lib/api.ts` `ProviderSource` is a typed mirror). No client-side recomputation; no fetch of an existing value from a non-canonical endpoint.
- **No fabrication (invariant #8 honored).** Every new client raises `ProviderUnavailableError` and returns zero bars on any network/HTTP error, error payload, empty result, or unparseable/partial row (`yahoo_provider.py`, `tiingo_provider.py` `_parse`; same pattern in the others); a needs-key client built with no key raises an explicit "requires an API key" error — never a silent fallback or placeholder bar.
- **Key-never-persisted (Data-Contract note + principal anti-goal) holds.** The `api_key` is request-only: threaded as a thread kwarg → `run_data_job` local → `make_provider(source, api_key=key)`. It is **absent** from `JobProgress` (only the non-secret `source` id is recorded), from `JobProgress.to_dict()` / `GET /api/data/jobs/{id}`, from `_persist_run` / `DataProviderRun`, and from the `POST` echo (`api/data.py` returns `source`, never the key). `compute_provider_availability` reads `os.environ` for **presence only** (`bool(...)`), emitting the env-var **name** + a boolean + a human reason — never a key value. Frontend holds it in `useState` only (cleared on unmount + job completion; never localStorage/URL/cookie; omitted from the POST body when blank). The single source of truth for the availability value carries no secret — coherent with the contract.

No unregistered new value (the decomposer registered the catalog row this iteration; blueprint.md:186 + the additive iter-21 note at blueprint.md:92).

## Step 2 — Information Architecture check (the "where do I find it" gate) → PASS

- **No new page/route.** The only frontend `page.tsx` in the diff is the existing `apps/frontend/app/data/page.tsx` — the J-17 `/data` home. The Import-source `<select>`, availability line, and session-key field are additive elements inside the existing `JobForm`.
- **Reachable in 1 click; no parallel shell.** `/data` is already a top-level sidebar entry (blueprint.md:66). `git diff --name-only` confirms **no** sidebar/nav/layout/router file was touched; the page reuses the established shell components (`PageHeading`/`Card`/`PanelTitle`/`Select`). No invented parallel navigation.
- **No duplicate home.** The catalog/key controls extend the one Data-Manager home; no second "data" or "import" page was created.
- **No nav-skeleton change → no re-approval needed.** Confirmed `state/blueprint.reapproval-requested` is **absent** — correct for an additive-under-approved-home iteration (matches the iter-21 blueprint note, blueprint.md:92).

## Step 3 — Critical invariant #5 / J-18 (exactly one date selector) → PASS

The new source/key controls add **no date state**. The Import-source control is a provider `<select>` (not a date); the key field is `type="password"`; the Start/End inputs remain `type="date"` job parameters (unchanged); the page still reads the single global `useAsOf()` for any viewing date. No second date `<select>` or `as_of` state was introduced on `/data`. The blueprint's principal J-18 WATCH for this iteration is satisfied.

## Step 4 — Advisory observations (WARN-class, non-blocking) → none outstanding

- **Resolved drift (positive).** The `/data` subtitle was corrected from "grow the **System Health** evidence" → "grow the **Backtest** evidence" (`page.tsx:170`), closing the standing iter-17 advisory (System Health was retired then). This *improves* coherence rather than introducing drift — nothing to flag.
- Labels are consistent ("available" / "needs key" in the picker option, the `source-availability` line, and the backend `reason`; the job-progress header echoes the recorded `source` id). No formatting or label inconsistency observed.

---

## Conclusion

No objective Part-A (Data Contract) or Part-B (Information Architecture) violation. The new import-provider-availability value has exactly one computing function (`compute_provider_availability`) and one serving endpoint (`GET /api/data` `sources`); the feature lives in its blueprint-designated `/data` home with no new route, nav, parallel shell, or second date control; provider failures surface explicitly with zero fabrication; and the session key is never persisted, logged, or served. The product stayed coherent.

**Verdict: COHERENCE-PASS** — proceed to the goal-evaluator.
