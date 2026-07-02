# Goal Iteration 16 — 30-year Stooq seed, Part A: staged ingest + validation (no runtime change)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** mcp-loop
- **Iteration:** 16
- **Mode:** next
- **Depth:** full
- **Frontend Present:** no
- **Target journeys:** J-10
- **Required-still-passing journeys:** J-01, J-02, J-05, J-09
- **Anti-goal reminders:**
  - A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked values MUST render a "not yet proven" state. *(critical)*
  - **Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha claims; never place or simulate orders. *(critical)*
  - A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation for the same as-of date — not merely that the page renders. *(critical)*
  - **No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of; never introduce lookahead anywhere. *(critical)*
  - No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the post-decompose gate. *(critical)*
  - No hard-coded credentials, API keys, or tokens in source files. *(critical)*
  - From the improvement direction, verbatim: "no fabricated data (missing history / dead names stay absent)" and "Stooq needs no API key" — any key, if the endpoint demands one, is read from the environment only, never persisted.

## GOAL

Stage the complete ~30-year Stooq price seed for the full ~548-name pool (plus every ETF/index/proxy the engine needs) as a **committed, validated, side-by-side data asset** — with ZERO runtime change — so the next iteration can perform the atomic data-basis swap and the sanctioned evidence-ledger reset.

## BACKGROUND

Iter-15 closed with GOAL_ACHIEVED (J-01..J-09 all passing); the human operator then extended `docs/goal.md` with four NEW Must-have journeys **J-10..J-13** (30-year Stooq history over a broadened 548-name point-in-time dynamic universe) plus a detailed engineering direction whose suggested sequencing starts with data prep. This iteration is **Part A of that direction: ingest + validate + commit the new seed, staged side-by-side** — deliberately isolated from the swap because:

1. **The fetch is the one external, non-deterministic step.** Verified in code: `apps/backend/scripts/ingest_seed.py` is currently Yahoo-only with NO `--provider` flag (its own docstring records that Stooq *bulk* download is captcha/key-gated); the keyless per-symbol `StooqProvider` (`apps/backend/app/data_providers/stooq_provider.py`, `make_provider("stooq")`) exists and is test-covered, BUT `config.yaml`'s import catalog marks stooq "free CSV nominally, but key-gated for this IP (iter-3 lesson)". Whether Stooq's free CSV endpoint serves this environment ~590 full-span requests is unknowable until tried — so it must be probed and run in an iteration whose success criteria honestly accommodate a rate-cap or hard gate, without contaminating a swap/reset.
2. **The swap must be atomic with the sanctioned ledger reset.** goal.md ("Data-basis change (sanctioned ledger reset)") invalidates EVERY pre-refresh certified claim the moment the basis changes; pairing the basis flip with the reset in one later iteration (iter-17) avoids ever displaying stale "Proven" numbers on new data (anti-goals #1/#3/#4). Staging the data first keeps iter-17 fully offline and deterministic against a committed asset.
3. **Precedent:** iters 9/10/12 were accepted as backend/enablement milestones with no journey flips ("build the economy first, then widen the scan" was delivered the same way). J-10 does NOT flip this iteration — it stays `unknown` (enablement only); J-11/J-12/J-13 become tracked as `unknown` (unbuilt by design).

Lessons applied: iter-12 ("verify the precondition against the actual code" — done, see the code facts above); iter-9 (for a zero-frontend iteration the non-regression proof is byte-identity of the shared value's canonical outputs + unedited green suites, not a browser pass); iter-9b/10 ledger footguns are moot here because this iteration performs **zero referee submissions**.

## IN SCOPE

### Backend (tooling + committed data only — ZERO `apps/backend/app/**` runtime change)

- [ ] **Extend `apps/backend/scripts/ingest_seed.py`** (surgical; the existing default Yahoo path and its current behavior stay intact):
  - `--provider stooq|yahoo` (default `yahoo`, preserving current usage); `stooq` routes through the EXISTING `app.data_providers.make_provider("stooq")` / `StooqProvider.get_daily(symbol, start, end)` — the free per-symbol CSV endpoint (`stooq.com/q/d/l/`, `.us` suffix mapping, caret-preserved indexes), no credential in source. If the endpoint demands a key from this IP, read `STOOQ_API_KEY` from the environment only (never persisted, never committed); absent key + gated endpoint = honest documented failure.
  - `--out <dir>` staging destination (this run writes `apps/backend/data/seed-stooq-30y/` with the same layout as the live seed: `prices/*.csv` + `meta.json`); the default remains the live seed dir so historical usage is unchanged.
  - `--symbols-set pool` → the de-duplicated union of `read_pool()` (`apps/backend/data/seed/universe_pool.csv`, ~548 names) ∪ `all_seed_symbols(config)` (the ETFs/index/sector/industry/volatility sets, ^VIX, index-chart legend symbols, macro proxies) — ~590 symbols; the current default symbol set stays unchanged.
  - `--start 1996-01-01 --end <pinned>`: pin `--end` to the most recent COMPLETED trading day at run start (e.g. `2026-06-30`) and record it in the staged `meta.json`; **resume runs MUST reuse the manifest's pinned end** so all symbols share one consistent window bound (per-name first bar stays each name's real first bar — never padded).
  - **Fetch priority order** (so a rate-cap secures the most load-bearing names first): (1) benchmarks/controls — index ETFs incl. SPY/QQQ, sector/industry/volatility ETFs, ^VIX + macro proxies + legend symbols; (2) the 122 current `universe.symbols`; (3) remaining pool names alphabetical.
  - **Resumable + polite:** skip symbols whose staged CSV already exists and reaches the pinned end (manifest-driven); inter-request sleep ≥1s; on a rate-limit/limit-page/non-CSV/"N/D" response, record the failure, write the progress manifest, and stop gracefully with a non-zero exit and an honest message. NEVER fabricate, pad, splice vendors, or hand-edit a bar. A symbol Stooq lacks is recorded and honestly omitted (it simply never enters the universe later).
- [ ] **Probe-first go/no-go** (before the full ~590-symbol run): fetch AAPL + SPY + NVDA full-span via the new path and verify (a) a real CSV body, not a limit/captcha page; (b) depth — AAPL/SPY first bar ≤ 1996-01-05; (c) schema `date,open,high,low,close,volume`; (d) adjusted basis — no ~10x/~4x one-day close gap across NVDA 2024-06-10 (10:1) and AAPL 2020-08-31 (4:1). **On probe hard-failure: halt the fetch, capture the exact response as evidence, document the blocker in the dev handoff (External Integration Testing honesty, `.claude/core.md`), and still land the tooling + validation suite.** Do NOT silently substitute providers — goal.md names Stooq explicitly; escalation is the human's decision.
- [ ] **Validation suite** (new test module, e.g. `apps/backend/tests/test_seed_staged_30y.py`) over the STAGED directory (pytest-skips with a clear reason if the staged dir is absent, i.e. probe-blocked):
  - schema identity, strictly-ascending unique dates, positive prices, non-negative volumes for every staged CSV;
  - depth/honesty anchors: AAPL + MSFT first bar ≤ 1996-01-05; NVDA first bar in 1999 (real IPO, not 1996); post-IPO names honestly short — COIN ≈ 2021-04-14, ARM ≈ 2023-09-14, HOOD ≈ 2021-07-29 (small tolerance; first bar must never PRECEDE the real listing — no fabricated early rows);
  - split continuity: bounded |1-day close return| across NVDA 2024-06-10 and AAPL 2020-08-31 (back-adjusted basis, no seam);
  - cross-vendor sanity: staged daily RETURNS for AAPL/NVDA/SPY agree with the committed live seed over the 2021-01→2026-05 overlap within a small tolerance (both bases are fully adjusted, so returns must match);
  - manifest agreement: staged `meta.json` per-symbol first/last/bars match the CSVs on disk.
- [ ] **Commit the staged asset:** `apps/backend/data/seed-stooq-30y/prices/*.csv` + `meta.json` (provider, pinned window, per-symbol coverage, failures list, cap events). Expect ~150–250 MB of plain CSVs (same format as the live seed; one-time cost). The staged tree is read by NOTHING at runtime.
- [ ] **Coverage manifest artifact** for iter-17's planning: `reports/phase-goal-mcp-loop-iter-16-seed-coverage.md` — fetched/missing/short-history counts by priority tier, pool names Stooq lacks entirely, ETF/index coverage (call out ^VIX explicitly — if Stooq lacks it, record the gap for an iter-17 decision; indexes carry no split/dividend adjustment so the single-basis rule is an equities concern), rate-cap events + resume instructions.

### Frontend

None. (`Frontend Present: no` — zero UI change; stages 5/6/8 write N/A stubs per workflow.)

### New user-facing capability

None this iteration (enablement). After iter-17's swap this asset becomes the product's price basis: ~30-year charts/backtests for long-tenured names, honest short history for post-IPO names, and a broadened 548-name point-in-time universe.

### New information displayed

None. Every displayed number on every page stays byte-identical.

### New user actions

None.

### UI surface changes

None.

### Product surface delta

None visible. Measurable capability delta: a committed, schema-validated, honestly-bounded ~30-year × ~590-symbol Stooq price seed staged for the sanctioned basis migration, plus a provider-routed, resumable ingest tool.

### Blueprint conformance

No new surfaces. (Blueprint updated additively: J-10..J-13 rows added to the feature/journey homes table — all under EXISTING nav homes (Stocks/Backtest, Evidence, Methodology, Data Manager); an iter-16 clarification paragraph registers the staged asset as internal-only. No nav-skeleton change.)

### Data-contract additions

None. No new displayed value, no new computing module, no new endpoint. Both evidence ledgers (`certified-claims.jsonl`, `staging-ledger.jsonl`) MUST remain byte-identical — this iteration performs zero referee submissions (any claim certified pre-swap would be measured on the retiring basis and is worthless; the sanctioned reset in goal.md "Loop mechanics" governs re-certification AFTER the swap). Accordingly this spec carries no Evidence Claim block, so the post-decompose gate passes through automatically.

## OUT OF SCOPE

- ANY change under `apps/backend/app/**` or `apps/frontend/**` — `config.provider` stays `seed`, `SeedProvider` still reads `data/seed/`, `seed_loader.load_prices` still loads `all_seed_symbols` only, `walk_forward.history_years` stays 2, `config.yaml` byte-identical.
- The basis swap itself, DB rebuild, snapshot backfill, and the **sanctioned evidence-ledger reset + regeneration + frozen-golden refresh** (all iter-17, atomic).
- The `resolve_candidate` recency/staleness gate (iter-17, lands with the pool broadening it protects).
- Chart windowing/downsampling and `/bars` range/interval params (J-10 performance leg — after the swap).
- Data Manager changes: Fetch-over-548 wiring, "Expand universe" removal, availability-legend clarity (J-13 — after the 548 pool is the committed default).
- Any referee submission, any ledger write (canonical OR staging), any `## Evidence Claim`-gated promotion.
- Splicing Stooq-deep history onto the existing Yahoo-recent CSVs (goal.md forbids a mixed-vendor adjustment seam), or any provider substitution without human sanction.

## DEFINITION OF DONE

- [ ] `apps/backend/scripts/ingest_seed.py` supports `--provider stooq` (via `make_provider`), `--out`, `--symbols-set pool`, pinned `--end`, priority ordering, resume-skip, and graceful rate-cap stop — unit-tested with a stubbed client (`StooqProvider` is client-injectable), existing Yahoo-path behavior unregressed.
- [ ] The live probe (AAPL/SPY/NVDA full-span) was executed against real Stooq and its outcome is recorded with evidence in the dev handoff — this satisfies the External Integration Testing requirement (≥1 real-system check).
- [ ] **On probe success:** the staged seed is committed at `apps/backend/data/seed-stooq-30y/` with priority tiers 1–2 complete (all controls/ETFs/^VIX-or-documented-gap + all 122 current universe names at full Stooq depth) and tier 3 run to cap-or-completion; the validation suite is green over the staged data; the coverage manifest reports exact counts and any cap events with proven resume behavior (a re-run skips completed symbols).
- [ ] **On probe hard-failure (endpoint key-gated for this IP):** the blocker is documented with the exact response evidence; the tooling + validation suite still land (staged-data tests skip with a stated reason); the dev handoff flags the decision needed from the human (provide `STOOQ_API_KEY` via environment, or amend goal.md's provider choice) — an honest partial completion the evaluator scores as such.
- [ ] Zero diff (byte-identical): `apps/backend/app/**`, `apps/frontend/**`, `config.yaml`, `runs/goal-session-mcp-loop/state/certified-claims.jsonl`, `runs/goal-session-mcp-loop/state/staging-ledger.jsonl` — the non-regression proof for J-01..J-09.
- [ ] Existing suites pass UNEDITED (`test_referee.py`, `test_forward_walk.py`, `test_evidence.py`, `test_staging_ledger_routing.py`, `test_seed_integrity.py`, `test_stooq_provider.py`); no test pins refreshed this iteration (the live seed did not change).
- [ ] Required-still-passing journeys J-01, J-02, J-05, J-09 remain green (deterministic replay / byte-identity).
- [ ] No anti-goal violation introduced (in particular: no fabricated/padded/spliced bars; no credential in source; ledgers untouched).
- [ ] Dev handoff written at `docs/handoffs/goal-mcp-loop-iter-16-dev.md` (What Was Built / Files Changed / Tests Run / Known Issues incl. live-fetch honesty / Suggested Next Phase = the iter-17 swap+reset).

## TESTING REQUIREMENTS

- Browser: none required (`Frontend Present: no`; zero UI diff). Non-regression for J-01, J-02, J-05, J-09 via deterministic replay of stored golden scripts plus the byte-identity evidence above; J-03/J-04/J-06/J-07/J-08 are covered by the same zero-app-diff argument (no regression mechanism).
- Unit/integration:
  - New staged-seed validation suite (schema, depth anchors, post-IPO honesty, split continuity, returns cross-check, manifest agreement) — green on staged data, or skipped-with-reason if probe-blocked.
  - Ingest unit tests with a stubbed/injected client: provider routing, staging layout, priority ordering, pinned-end manifest reuse, resume-skip of complete CSVs.
  - ≥1 real live-fetch check against Stooq (the probe), outcome documented either way.
- Error cases (unit-tested via the injectable client):
  - Rate-limit / "Exceeded the daily hits limit" / non-CSV body → graceful resumable stop, manifest written, non-zero exit, NO partial/fabricated CSV row.
  - Unknown symbol "N/D" → recorded failure, symbol omitted, run continues.
  - Resume with a mixed manifest (some complete, some missing) → only missing symbols fetched, pinned end reused.

## NOTES

- **Depth = full** per the iter-15 evaluator's explicit recommendation ("If the continuous-improvement loop extends the goal again, the next iteration should run full") and because this is structural, externally-dependent foundation work that warrants the auditor/closure guards. This is a goal-reopening iteration: goal.md gained human-authored J-10..J-13 (commit e029e5a), so GOAL_ACHIEVED is not currently declarable — J-10..J-13 are unbuilt.
- **For the evaluator:** no journey flips this iteration by design (mirrors the accepted iter-9/10/12 enablement pattern). Expected journey deltas: J-10 tracked `unknown` with its Part-A prerequisite delivered (or honestly blocked); J-11/J-12/J-13 newly tracked `unknown`; J-01..J-09 carried passing on byte-identity + replay. The honest-blocked outcome (Stooq gated for this IP) is a legitimate iteration result — score it CONTINUE with the escalation question surfaced, not as a failure to be papered over.
- **Roadmap after this iteration (for context, not scope):** iter-17 = the ATOMIC swap — flip the seed dir, broaden `load_prices` to the pool, add the `resolve_candidate` staleness gate, rebuild the DB, bounded snapshot backfill (coarser deep-history cadence per goal.md §F), the SANCTIONED ledger reset/regeneration, frozen-golden + seed-window test-pin refresh (`test_evidence.py`, `test_staging_ledger_routing.py`, `test_seed_integrity.py`, `test_bar_cache.py` offset comment), survivorship-label span update. iter-18+ = re-certification promotions gate-first on the new committed basis (staging → explicit `"ledger":"canonical"` winners; honest-stop on non-PASS), chart performance (J-10 perf leg), membership-timeline verification (J-12), Data Manager coherence (J-13).
- **Code facts grounding this spec** (verified this planning pass): `stooq_provider.py` + `make_provider("stooq")` exist (keyless, client-injectable, `ProviderUnavailableError` on any failure); `ingest_seed.py` is Yahoo-only today with `--start/--end` args and writes `data/seed/prices/` + `meta.json`; `universe_pool.csv` holds ~548 symbols at `apps/backend/data/seed/universe_pool.csv`; live seed = 162 CSVs, 13 MB, window 2021-01-04→2026-05-28; `all_seed_symbols` = universe ∪ ETFs ∪ ^VIX ∪ legend ∪ macro proxies.
- **Size note for the release-manager:** the staged commit adds ~150–250 MB of plain-text CSVs (largest single file ~0.5 MB — no per-file limit concern). One-time; iter-17 retires the old 13 MB tree when it swaps.
