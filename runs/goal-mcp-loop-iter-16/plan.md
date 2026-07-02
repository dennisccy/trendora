# goal-mcp-loop-iter-16 Execution Plan

**Phase:** 30-year Stooq seed, Part A — staged ingest + validation, ZERO runtime change.
**Target journey:** J-10 (enablement only — stays `unknown`; J-11/J-12/J-13 newly tracked `unknown`). Required-still-passing: J-01, J-02, J-05, J-09 (proven by byte-identity + unedited green suites, not browser runs).
**Goal alignment:** implements goal.md "Improvement direction: 30-year Stooq history" §A step 1 (data prep), deliberately isolated from the iter-17 atomic swap + sanctioned ledger reset. No drift detected. Blueprint already carries the J-10..J-13 homes rows and the iter-16 internal-asset clarification (`runs/goal-session-mcp-loop/state/blueprint.md` lines ~78–81, ~208) — verify-only, do NOT edit.

## What to Build

- **Extend `apps/backend/scripts/ingest_seed.py`** (surgical; default Yahoo path byte-compatible with today):
  - `--provider stooq|yahoo` (default `yahoo`). `stooq` routes through the EXISTING `app.data_providers.make_provider("stooq")` → `StooqProvider.get_daily(symbol, start, end)` (keyless free CSV, `.us` mapping, caret-preserved indexes, raises `ProviderUnavailableError` on any failure — never fabricates). If the endpoint demands a key for this IP, read `STOOQ_API_KEY` from the environment ONLY; absent key + gated endpoint = honest documented failure. No credential ever in source or committed.
  - `--out <dir>` staging destination (this run: `apps/backend/data/seed-stooq-30y/` with live-seed layout `prices/*.csv` + `meta.json`; default stays the live seed dir).
  - `--symbols-set pool` → de-duplicated union of `read_pool()` (`apps/backend/app/engine/universe_screen.py`; reads `apps/backend/data/seed/universe_pool.csv`, ~548 names) ∪ `all_seed_symbols(config)` (`apps/backend/app/seed_loader.py`: universe ∪ index/sector/industry/volatility ETFs ∪ ^VIX ∪ index-chart legend ∪ macro proxies) — ~590 symbols. Current default symbol set unchanged.
  - `--start 1996-01-01 --end <pinned>`: pin end to the most recent COMPLETED trading day at run start; record it in staged `meta.json`; resume runs MUST reuse the manifest's pinned end. Per-name first bar = the name's real first bar, never padded.
  - Fetch priority order: (1) benchmarks/controls (index ETFs incl. SPY/QQQ, sector/industry/volatility ETFs, ^VIX, macro proxies, legend symbols); (2) the 122 current `universe.symbols`; (3) remaining pool names alphabetical.
  - Resumable + polite: manifest-driven skip of symbols whose staged CSV already reaches the pinned end; inter-request sleep ≥1s; on rate-limit / limit-page / non-CSV / "N/D": record failure, write progress manifest, stop gracefully with non-zero exit and honest message. NEVER fabricate, pad, splice vendors, or hand-edit a bar; a symbol Stooq lacks is recorded and honestly omitted.
- **Probe-first go/no-go** before the full ~590-symbol run: fetch AAPL + SPY + NVDA full-span via the new path; verify (a) real CSV body, (b) AAPL/SPY first bar ≤ 1996-01-05, (c) schema `date,open,high,low,close,volume`, (d) adjusted basis (no ~10x/~4x one-day close gap at NVDA 2024-06-10 / AAPL 2020-08-31). On probe hard-failure: halt the fetch, capture the exact response as evidence, document the blocker in the dev handoff, and STILL land the tooling + validation suite. Do NOT substitute providers — escalation is the human's decision.
- **Validation suite** — new `apps/backend/tests/test_seed_staged_30y.py` over the STAGED dir (pytest-skip with a clear reason if the staged dir is absent): schema identity; strictly-ascending unique dates; positive prices; non-negative volumes; depth anchors (AAPL + MSFT first bar ≤ 1996-01-05; NVDA first bar in 1999; COIN ≈ 2021-04-14, ARM ≈ 2023-09-14, HOOD ≈ 2021-07-29 with small tolerance and never BEFORE real listing); split continuity (bounded |1-day close return| across NVDA 2024-06-10, AAPL 2020-08-31); cross-vendor returns agreement with the committed live seed for AAPL/NVDA/SPY over the 2021-01→2026-05 overlap; staged `meta.json` per-symbol first/last/bars match the CSVs.
- **On probe success, commit the staged asset** at `apps/backend/data/seed-stooq-30y/` (prices + meta.json with provider, pinned window, per-symbol coverage, failures, cap events). ~150–250 MB of plain CSVs, sanctioned one-time cost (largest file ~0.5 MB). Read by NOTHING at runtime.
- **Coverage manifest** `reports/phase-goal-mcp-loop-iter-16-seed-coverage.md` for iter-17 planning: fetched/missing/short-history counts by priority tier, pool names Stooq lacks, ETF/index coverage (^VIX called out explicitly — gap recorded if absent), rate-cap events + resume instructions.

## Agents Required

- backend-data (developer): yes -- all of the above: ingest tooling, probe, staged fetch + commit, validation suite, coverage manifest, dev handoff.
- frontend-ux: no -- zero UI change; every displayed number stays byte-identical.

Frontend Present: no

## Files to Create/Modify

- `apps/backend/scripts/ingest_seed.py` -- add `--provider/--out/--symbols-set`, pinned-end manifest, priority ordering, resume-skip, graceful rate-cap stop (existing Yahoo default behavior intact).
- `apps/backend/tests/test_ingest_seed.py` (new; or similarly named) -- ingest unit tests with a stubbed/injected client (StooqProvider is client-injectable).
- `apps/backend/tests/test_seed_staged_30y.py` (new) -- staged-seed validation suite (skips-with-reason if staged dir absent).
- `apps/backend/data/seed-stooq-30y/prices/*.csv` + `apps/backend/data/seed-stooq-30y/meta.json` (new, probe-success branch) -- the committed staged asset.
- `reports/phase-goal-mcp-loop-iter-16-seed-coverage.md` (new) -- coverage manifest.
- `docs/handoffs/goal-mcp-loop-iter-16-dev.md` (new) -- dev handoff incl. live-probe evidence either way; Suggested Next Phase = iter-17 swap+reset.
- MUST NOT change (byte-identical): `apps/backend/app/**`, `apps/frontend/**`, `config.yaml`, `runs/goal-session-mcp-loop/state/certified-claims.jsonl`, `runs/goal-session-mcp-loop/state/staging-ledger.jsonl`. Zero referee submissions, zero ledger writes.

## UI Evolution

N/A — backend/data-only iteration; no UI surface, action, or navigation change.

## Key Test Scenarios

- Ingest unit (stubbed client, no network): `--provider stooq` routes via `make_provider`; `--out` writes staging layout (`prices/` + `meta.json`); priority ordering tier1→tier2→tier3; resume reuses the manifest's pinned end; resume-skip fetches only symbols missing/short of pinned end; rate-limit / non-CSV body → manifest written, non-zero exit, NO partial/fabricated CSV row; "N/D" unknown symbol → failure recorded, run continues; default Yahoo invocation unregressed.
- Live probe (real Stooq, the ≥1 real-system check per External Integration Testing): AAPL/SPY/NVDA full-span outcome documented in the handoff with evidence — success (depth/schema/adjustment verified) or honest blocker (exact response captured).
- Staged validation suite green over committed staged data (probe-success branch) — or skipped-with-stated-reason (probe-blocked branch).
- Existing suites pass UNEDITED, no pins refreshed: `test_referee.py`, `test_forward_walk.py`, `test_evidence.py`, `test_staging_ledger_routing.py`, `test_seed_integrity.py`, `test_stooq_provider.py`.
- Non-regression J-01/J-02/J-05/J-09: byte-identity of `apps/backend/app/**`, `apps/frontend/**`, `config.yaml`, both ledgers (git diff clean on those paths) + green unedited suites. No browser checks required.

## Assumptions & Scope Guards

- Pinned `--end` = most recent completed trading day at run start (today 2026-07-01 → expect 2026-06-30), recorded in staged meta and reused on resume.
- `read_pool` lives in `apps/backend/app/engine/universe_screen.py` (verified; some prose references say `universe_resolver` — use the actual location). `universe_pool.csv` has ~548–550 symbols; exact counts go in the coverage manifest.
- The current `ingest_seed.py` builds its own symbol list (universe + 4 ETF groups, missing ^VIX/legend/macro proxies); do not change that default — the pool set is only under `--symbols-set pool`.
- Honest-blocked outcome (Stooq gated for this IP) is a legitimate result: land tooling + skipping tests, capture evidence, surface the human decision (`STOOQ_API_KEY` via env, or amend goal.md's provider choice). Never substitute providers silently.
- OUT OF SCOPE (iter-17+): any `apps/backend/app/**` or `apps/frontend/**` change; the basis swap, DB rebuild, snapshot backfill, sanctioned ledger reset/regeneration, frozen-golden refresh; `resolve_candidate` staleness gate; chart windowing / `/bars` params; Data Manager changes; any referee submission or ledger write; splicing Stooq history onto Yahoo CSVs.
