# Goal Iteration 8 — Finish J-22: run the universe expansion (data wall cleared)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever
- **Iteration:** 8
- **Mode:** normal
- **Depth:** full
- **Frontend Present:** yes (no new frontend code — the iter-7 Universe-Selection card + /data Universe metric auto-surface once the screen record exists)
- **Target journeys:** J-22
- **Required-still-passing journeys:** J-07, J-08, J-01, J-02, J-03, J-04, J-05, J-06, J-09, J-12, J-13, J-14, J-16, J-17, J-18, J-19
- **Anti-goal reminders (verbatim from docs/goal.md):**
  - **Universe screen is reproducible & honest.** Universe membership MUST come from the config-recorded screen (no hand-curated list masquerading as a screen); expansion MUST use real committed data only (no fabricated history); breadth and walk-forward labels stay "universe-relative" / survivorship-biased to current membership. *(extends No magic numbers + No fabricated data)*
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey.
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code.
  - **Risk-Off must gate Actionable.** When the regime is Risk-Off, the scanner MUST mark zero stocks "Actionable" (watchlist-only). *(critical)*
  - **No lookahead.** Scoring for a snapshot dated D MUST use only price bars with date ≤ D; forward returns MUST use only bars with date > D. *(critical)*
  - **Snapshots are immutable.** A persisted `scanner_run` and its result rows MUST never be updated or overwritten after creation; forward returns live in a separate append-only table keyed to the snapshot. *(critical)*
  - **On-demand / range backfill stays immutable & lookahead-free.** Snapshots created for a date range are create-once: an existing snapshot MUST be read, never overwritten; an as-of-D snapshot MUST use only bars with date ≤ D. *(critical)*
  - **Single source of truth / No recompute in the read path.** The resolved universe is computed once (the committed screen) and read identically by `/api/methodology` and `/api/data`; the API/frontend never recompute membership or market cap.
  - **No secrets in source.** No hard-coded credentials, API keys, or tokens; the live OHLCV/market-cap fetch uses Yahoo's free no-key endpoints; the crumb is fetched at runtime and never stored or committed.
  - **Honest limitations surfaced.** Breadth/new-high-low remain "universe-relative"; walk-forward evidence remains survivorship-biased to current membership.

## GOAL

Execute the already-built J-22 universe-expansion runbook now that the data feed is reachable: replace the curated 122-name universe with the **transparent, config-screened ~400–500-name universe** (real committed OHLCV + market cap), so `/methodology` surfaces the real Universe-Selection screen, `/data` shows the grown coverage count, and the deeper forward-test sample feeds every downstream surface — all from real data, nothing fabricated.

## BACKGROUND

iter-7 built the **complete, tested, auto-healing J-22 infrastructure** (offline `screen_universe.py` + `apply_universe_to_config.py`, the `methodology.universe_selection` config schema with live `ref` thresholds, the `GET /api/methodology` payload + a self-enforcing honest gate that hides the section until a real `data/seed/universe.json` exists, `seed_loader` market-cap population, single-source `universe_count` on `GET /api/data`, the `/methodology` Universe-Selection card + `/data` Universe metric, and unit tests). The **one** step that never ran was the offline fetch of real OHLCV + market cap for the ~380 new candidates — Yahoo returned a hard HTTP 429 from this egress across three fix cycles, so iter-7 correctly **STALLED** (it refused to fabricate, honoring *No fabricated data*; verdict was non-regression, infra committed-ready).

**The blocker has cleared.** Re-probed live at plan time (2026-06-02): Yahoo chart API returns real OHLCV (HTTP 200), and the cookie+crumb flow returns real market-cap quote data (crumb acquired; `/v7/finance/quote` served real fields) — both no-key halves the screen needs are reachable. (Stooq remains apikey/captcha-gated, but the screen tool uses Yahoo, not Stooq — irrelevant.) This iteration therefore **runs the committed finish runbook** (dev handoff §4), regenerates the seed over the expanded universe, and verifies J-22 + the regression set. No new feature code is expected — only the data step, a possible config-only bootstrap-date swap, and verification.

**Lessons applied (from `state/lessons.md`):**
- *iter-7 (probe-and-gate / auto-heal):* a fresh bulk external fetch MUST be gated on a single polite probe FIRST and built to auto-heal. The probe is GREEN at plan time; the dev MUST re-confirm with ONE polite request at step start, and if the wall has re-imposed, **halt cleanly (do not fabricate, do not blind-loop)**. The screen tool's built-in 429-aware backoff handles transient throttling mid-run; only a hard persistent wall is a halt.
- *iter-3 (Stooq unusable):* do not route the screen through Stooq live-fetch (apikey-gated); the screen uses the no-key Yahoo path — confirmed reachable.
- *iter-6 (shared-browser corruption):* if both the `qa` agent and `browser-qa-agent` drive Chrome, serialize access (one vacates before the other captures), assert live DOM/URL state immediately before each capture, and de-dup evidence by sha256.
- *Project memory:* the full pytest suite is ~14 min (heavy walk-forward boot) — run it **once**, never two concurrently; kill dev servers **by port** (8835/3835), never a broad `pkill`.

## IN SCOPE

### Backend (data + verification — the iter-7 infra is already built; this EXECUTES it)
- [ ] **Probe-gate (re-confirm reachability):** one polite, no-retry Yahoo request at step start. If HTTP 429 / hard-walled, **halt honestly** (STALLED) — do NOT fabricate, do NOT blind-loop. (Plan-time probe is GREEN; this guards against re-imposition between plan and dispatch.)
- [ ] **Run the screen + ingest:** `apps/backend/.venv/bin/python apps/backend/scripts/screen_universe.py --screen --end 2026-05-29` — fetch real EOD OHLCV (Yahoo chart, no key) + real market cap (Yahoo quote via the no-key cookie+crumb flow) for the ~380 NEW candidates from the committed `data/seed/universe_pool.csv` (548 names; existing committed CSVs are reused, only new names hit the network). Apply the config screen from `universe.filters` (`min_market_cap` $2B / `min_dollar_vol` $50M / `min_price` $10). Keep passers (~400–500) as the universe; **log + OMIT** any candidate that fails to fetch, returns an empty/partial series, lacks a market cap, or fails a threshold — **never fabricate**. Writes `data/seed/universe.json` (per-member screen-pass record), the new per-symbol price CSVs, and refreshes `data/seed/meta.json`. Keep the **date window aligned to the existing seed** (this is a universe-WIDTH expansion, not a date-range extension).
- [ ] **Apply to config:** `apps/backend/.venv/bin/python apps/backend/scripts/apply_universe_to_config.py` — rewrite `config.yaml` `universe.symbols` + `stock_sectors` + (pruned) `themes` from `universe.json`, preserving every section comment, then re-load + re-validate (every member has a sector; every theme member is in the universe; themes stay non-empty).
- [ ] **Re-verify the Risk-Off seam (critical, J-07/J-08):** confirm BOTH seeded bootstrap dates `2022-10-07` and `2025-04-04` still resolve to a **Risk-Off (or Defensive)** regime label under the expanded universe (the regime engine's breadth / new-high-low iterates `universe.symbols`, so a wider universe can shift breadth). If a date's label flipped off Risk-Off, **swap it for another real Risk-Off seed date** in `scanner.bootstrap_dates` (config-only — no code, no fabricated run) so a seeded Risk-Off run with **zero Actionable** still exists.
- [ ] **Regenerate the seed deterministically:** delete `apps/backend/data/trendora.db`, reboot the backend (the lifespan regenerates snapshots **create-once ≤ D** + forward returns **append-only > D** over the new universe — immutable, lookahead-free), then run the **FULL pytest suite ONCE**. The 3 previously-skipped committed-record tests (screen-pass / matches-config / market-cap-from-storage) must now **activate and pass**.

### Frontend (no new code — verify auto-surfaced rendering)
- [ ] No code change. Once `data/seed/universe.json` exists, the honest gate opens: `/methodology` renders the **Universe Selection** card (membership rule + the three thresholds formatted from the API values + resolved size ≈ 500) and `/data` shows the **Universe** coverage metric ≈ 500. Verify both render the REAL screened values and read the SAME resolved universe.

### New user-facing capability
The user can read the **actual, reproducible universe-selection screen** on `/methodology` (the membership rule + the exact `min_market_cap` / `min_dollar_vol` / `min_price` thresholds from config + the resolved member count ≈ 500) and see the grown coverage on `/data` — and every leaderboard/theme/sector/System-Health surface now spans ~400–500 real names instead of 122, with a deeper forward-test sample.

### New information displayed
The `/methodology` Universe-Selection section becomes **visible** (it was honestly hidden at 122) showing the real screen + resolved size; `/data` Universe count ≈ 500; System Health forward-test sample size (n) grows; leaderboards list ~400–500 ranked names.

### New user actions
None. (No new buttons/forms — the screen + ingest is an offline dev-run operation, not a request-path action.)

### UI surface changes
No new pages or components. The previously-suppressed Universe-Selection card on `/methodology` and the Universe metric on `/data` now populate with real data. Existing leaderboards/dashboard/System-Health/Backtest render the wider universe unchanged in layout.

### Product surface delta
Trendora's universe stops being a curated 122-name list and becomes a **transparent, config-recorded ~500-name screen result** — the credibility foundation the goal's vision and the *Universe-screen-honest* anti-goal demand, and the larger sample that makes the downstream `/research` labs' evidence trustworthy.

### Blueprint conformance
No nav-skeleton change. J-22's homes — `/methodology` (Universe-Selection rule) and `/data` (grown coverage count) — are **existing** Information-Architecture homes already registered in `blueprint.md`. No `blueprint.reapproval-requested` is written this iteration. The J-22 status notes in `blueprint.md` are updated (data wall cleared → finishing) as an additive/status edit only.

### Data-contract additions
**None.** The "Universe membership + selection screen" Data-Contract row was registered in iter-7 (computed once, offline, by the screen+ingest step; served by `GET /api/methodology` for the rule+thresholds+size and `GET /api/data` for the member count — both reading the SAME resolved universe). This iteration **populates** that contract with real screened data; it introduces no new displayed value and **no second computation path** for any existing value.

## OUT OF SCOPE

- **J-23 / J-24** (multi-timeframe / intraday bars + chart timeframe selector) — a separate iteration; they need fresh **intraday** Yahoo fetches and a timeframe-aware store, distinct from this daily-width expansion.
- **J-25–J-31** (`/research` Factor Lab + Setup & Pattern Lab + volatility family + synthesis) — the next wave; they require adding `/research` to the nav skeleton **and a blueprint re-approval**. Not built here. (Recommended immediately after J-22 — see NOTES.)
- **Extending the date grid.** J-22 grows universe **width** only; the bootstrap / forward-test date range is unchanged (new names get committed bars over the existing seed window).
- Any change to scoring / regime / scanner / forward-testing **logic**, or to weights/thresholds/bucket edges. The engines are untouched; only universe membership (data) grows. The only permitted config edit is the bootstrap-date swap IF a Risk-Off label flipped.
- Committing any API key or crumb. No secret enters source.

## DEFINITION OF DONE

- [ ] `config.universe.symbols` spans **~400–500 real names** (not 122), each with committed daily OHLCV; `data/seed/universe.json` (the committed screen-pass record) exists; **every member passes the recorded screen** (`min_market_cap` / `min_dollar_vol` / `min_price` from `universe.filters`).
- [ ] `GET /api/methodology` serves the `universe_selection` section (membership rule + the three thresholds resolved **live** from `universe.filters` via `ref`, no re-typed numbers + `resolved_size` ≈ 500); the `/methodology` Universe-Selection card renders it; `GET /api/data` `universe_count` ≈ 500 — both read the **same** resolved universe (single source, no drift).
- [ ] **J-22 passes via browser-qa-agent:** `/methodology` shows the universe-selection rule + the three config thresholds + ~400–500 resolved size; `/data` coverage shows the grown universe count; the screen is config-driven (matches `universe.filters`), not a hand-curated code list.
- [ ] **J-07 re-verified (critical):** both Risk-Off bootstrap dates still label Risk-Off (or Defensive) with **zero Actionable** (a config-only swap was applied if a label flipped); **J-08** immutable run history intact (older runs differ from latest; rows never mutated).
- [ ] **Required-still-passing journeys green** (regression sweep over the expanded universe): J-01–J-06 (scan surfaces render + score coherence holds), J-09 (System Health evidence; n **grew**), J-12 (methodology, now WITH the Universe-Selection card), J-13/J-14/J-18 (one global as-of control still drives every page), J-16 (VCP), J-17 (Data Manager coverage), J-19 (attribution). Journeys assert structural/relational properties, so the wider universe must not break them.
- [ ] **No anti-goal violation:** no fabricated bars/caps (every fetch/threshold failure is logged + omitted, never synthesized); thresholds come from config (no magic numbers; `test_no_magic_numbers` green over the expanded universe); breadth + walk-forward labels stay "universe-relative" / survivorship-biased; no secret committed (crumb runtime-only); snapshots immutable + lookahead-free; no order/execution path.
- [ ] The **full pytest suite passes ONCE** over the regenerated, expanded universe — including the 3 now-active committed-record tests and `test_seed_integrity` (the risk-on AND risk-off guarantees).
- [ ] New committed seed artifacts present: the new per-symbol price CSVs, `data/seed/universe.json`, refreshed `data/seed/meta.json`, and regenerated `config.yaml`.
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-8-dev.md` (state plainly whether the live fetch succeeded, how many candidates passed vs were omitted-and-why, and whether a bootstrap date was swapped).

## TESTING REQUIREMENTS

- **Browser (browser-qa-agent):**
  - **J-22 (primary):** `/methodology` Universe-Selection card shows the membership rule + the three thresholds + resolved size ~400–500; `/data` Universe coverage ≈ same count; both consistent (single source).
  - **Regression spot-checks:** J-07 (open a seeded Risk-Off bootstrap run → Risk-Off label + **0 Actionable**); J-01 + J-02 (dashboard + leaderboard render ranked rows on the ~500-name universe); J-09 (System Health renders, n grew); J-12 (methodology glossary intact + the new card); J-17 (`/data` coverage). Assert live DOM/URL state before each capture; de-dup screenshots by sha256 (iter-6 lesson).
- **Unit/integration (full pytest, run ONCE):** the 3 now-active committed-record tests (`test_universe_screen.py`: screen predicate; single-source universe size across `/api/data` ↔ `/api/methodology` ↔ config; committed record passes-screen + matches-config + market-cap-from-storage); `test_methodology.py` / `test_api_methodology.py` (Universe-Selection section present + honest gate); `test_no_magic_numbers.py`; `test_config.py`; `test_seed_integrity` (risk-on + risk-off stretches present); the no-lookahead + snapshot-immutability suites.
- **Error cases:** a candidate that fails to fetch / returns an empty-or-partial series / lacks a market cap / fails a threshold is **logged + OMITTED**, never fabricated (the screen predicate's failure paths are unit-asserted); a forced provider failure surfaces an explicit error and fabricates no prices/caps/scores; if the bulk fetch hard-walls (persistent 429 through backoff) and < ~400 names pass, **halt honestly** rather than pad or fabricate to reach 500.

## NOTES

- **Data-wall status at plan time: CLEARED (live-verified 2026-06-02).** Yahoo chart API → HTTP 200 + real OHLCV (`regularMarketPrice` populated); Yahoo `/v7/finance/quote` via the no-key cookie+crumb flow → real market-cap quote data (crumb acquired at runtime). This is precisely the unblock the iter-7 STALLED was waiting for. The dev MUST still re-probe with ONE polite request at step start (the limit is IP/volume-sensitive and could re-impose); the screen tool's 429-aware backoff (max_retries) absorbs transient throttling mid-run.
- **This is a "finish the committed runbook" iteration, not a new build.** All J-22 code (screen tool, config schema + ref validation, `/api/methodology` payload + honest gate, `seed_loader` cap population, single-source `universe_count`, frontend card/metric, unit tests) was built and committed in iter-7 (37→38 passed / 3 skipped). iter-8 runs the data step (handoff §4), regenerates the seed, and verifies. The only expected source edit is the **config-only** bootstrap-date swap, and only if a Risk-Off label flipped.
- **Heavy-op discipline (project memory):** the full walk-forward pytest boot is ~14 min — run it **once**, after the db regenerate; never launch two pytest invocations concurrently. Kill/restart dev servers **by port** (backend 8835 / frontend 3835), never a broad `pkill -f "next dev" / "uvicorn"` on this shared machine.
- **Process note for the evaluator (iter-2/3/6 lessons):** full-depth iters in this session have sometimes finished without a `status.json` / `auditor` handoff; verify the J-22 critical seams directly in source/state (universe size via `yaml.safe_load`; `universe.json` present; `/api/methodology` serves `universe_selection`; both Risk-Off bootstrap runs show 0 Actionable) rather than trusting a handoff, and de-dup any before/after evidence by sha256.
- **Next after J-22:** open the compute-only `/research` labs (J-25 Factor Lab decile + rank-IC first). That wave adds a NEW `/research` sidebar home and therefore REQUIRES the decomposer to add `/research` to the nav skeleton AND write `blueprint.reapproval-requested`. Front-load that approval next so a future data-feed outage can never fully stall the loop (iter-7 lesson) — the labs run over the now-larger stored seed with no external fetch.
