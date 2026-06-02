# goal-i_can_see_the_wealthy_future_forever-iter-8 Execution Plan

> **Iteration type: FINISH-THE-RUNBOOK (data + verification), not a new build.**
> All J-22 infrastructure was built & committed in iter-7 (screen tool, config schema + `ref`
> validation, `/api/methodology` payload + honest gate, `seed_loader` cap population, single-source
> `universe_count`, frontend card/metric, unit tests — 38 passed / 3 skipped). iter-7 correctly
> **STALLED** on a Yahoo HTTP 429 wall (it refused to fabricate). The wall was **re-verified CLEARED
> at plan time (2026-06-02)**. This iteration EXECUTES the committed runbook (iter-7 dev handoff §4),
> regenerates the seed over the expanded universe, and verifies J-22 + the regression set. The **only
> expected source edit** is a config-only bootstrap-date swap, and only if a Risk-Off label flipped.

## What to Build

- **Probe-gate (re-confirm reachability FIRST).** One polite, **no-retry** Yahoo request at step start
  (chart + crumb). If HTTP 429 / hard-walled, **halt honestly → STALLED** — do NOT fabricate, do NOT
  blind-loop. (Plan-time probe is GREEN; this guards against re-imposition between plan and dispatch.)
- **Run the screen + ingest.** `apps/backend/.venv/bin/python apps/backend/scripts/screen_universe.py
  --screen --end 2026-05-29` — fetch real EOD OHLCV (Yahoo chart, no key) + real market cap (Yahoo
  quote via the no-key cookie+crumb flow) for the ~380 NEW candidates in the committed
  `data/seed/universe_pool.csv` (550 names; existing committed CSVs are reused, only new names hit the
  network). Apply the config screen from `universe.filters` (`min_market_cap` $2B / `min_dollar_vol`
  $50M / `min_price` $10). Keep passers (~400–500) as the universe; **log + OMIT** any candidate that
  fails to fetch / returns an empty-or-partial series / lacks a market cap / fails a threshold —
  **never fabricate**. The tool's built-in 429-aware backoff absorbs transient throttling; a hard
  persistent wall is a clean halt. Writes `data/seed/universe.json`, the new per-symbol price CSVs,
  and refreshes `data/seed/meta.json`. **Date window stays aligned to the existing seed** (universe-
  WIDTH expansion, not a date-range extension).
- **Apply to config.** `apps/backend/.venv/bin/python apps/backend/scripts/apply_universe_to_config.py`
  — rewrite `config.yaml` `universe.symbols` + `stock_sectors` + (pruned) `themes` from
  `universe.json`, preserving every section comment, then re-load + re-validate (every member has a
  sector; every theme member is in the universe; themes stay non-empty).
- **Re-verify the Risk-Off seam (critical — J-07/J-08).** Confirm BOTH seeded bootstrap dates
  `2022-10-07` and `2025-04-04` still resolve to a **Risk-Off (or Defensive)** label under the wider
  universe (regime breadth / new-high-low iterates `universe.symbols`, so a wider universe can shift
  breadth). If a date flipped off Risk-Off, **swap it for another real Risk-Off seed date** in
  `scanner.bootstrap_dates` — **config-only, no code, no fabricated run** — so a seeded Risk-Off run
  with **zero Actionable** still exists.
- **Regenerate the seed deterministically.** Delete `apps/backend/data/trendora.db`, reboot the
  backend (the lifespan regenerates snapshots **create-once ≤ D** + forward returns **append-only > D**
  over the new universe — immutable, lookahead-free), then run the **FULL pytest suite ONCE**. The 3
  previously-skipped committed-record tests (screen-pass / matches-config / market-cap-from-storage)
  must now **activate and pass**.
- **Verify frontend auto-surfaces (no code change).** Once `data/seed/universe.json` exists the honest
  gate opens: `/methodology` renders the **Universe Selection** card (rule + the three thresholds
  formatted from API values + resolved size ≈ 500) and `/data` shows the **Universe** metric ≈ 500.
  Verify both render REAL screened values and read the SAME resolved universe.
- **Commit** the new per-symbol CSVs + `universe.json` + refreshed `meta.json` + regenerated
  `config.yaml`. (Release-manager handles the actual commit per the normal pipeline.)

## Agents Required

- developer: **yes** — runs the runbook (probe-gate → screen+ingest → apply-to-config → Risk-Off
  re-verify → db regen → full pytest once), verifies frontend auto-surface, writes the dev handoff.
  - backend-data: **yes** (the entire data step + verification)
  - frontend-ux: **no** (NO new frontend code — iter-7 already shipped the card/metric; this only
    verifies they auto-populate once the screen record exists)

## Frontend Present

yes

> User-visible change is real (the previously-hidden Universe-Selection card + grown coverage metric
> auto-surface, and every leaderboard/theme/sector/System-Health surface now spans ~400–500 names), so
> **browser QA IS required** (J-22 primary + the J-07/J-01/J-02/J-09/J-12/J-17 regression spot-checks).

## Files to Create/Modify

- `apps/backend/data/seed/universe.json` — **NEW** committed per-member screen-pass record (written by
  the screen tool; presence opens the honest gate).
- `apps/backend/data/seed/<SYMBOL>.csv` (~380 new) — **NEW** committed daily OHLCV for the new screened
  names (existing committed CSVs reused untouched).
- `apps/backend/data/seed/meta.json` — refreshed seed metadata (date window + symbol count).
- `config.yaml` — regenerated `universe.symbols` (~400–500) + `stock_sectors` + pruned `themes`;
  **plus** a `scanner.bootstrap_dates` swap **only if** a Risk-Off label flipped (config-only).
- **No `.py` / `.tsx` / `.ts` source edits expected.** If a code change beyond the bootstrap-date swap
  appears necessary, that is a signal something drifted — flag it, do not silently broaden scope.

## UI Evolution (Frontend Present: yes)

- **New user-facing capability:** the actual, reproducible universe-selection screen becomes readable
  on `/methodology` (it was honestly hidden at 122); every leaderboard / theme / sector / System-Health
  surface now spans ~400–500 real names with a deeper forward-test sample.
- **New information displayed:** `/methodology` Universe-Selection card (membership rule + the three
  config thresholds, live-`ref` from `universe.filters`, + resolved size ≈ 500); `/data` Universe count
  ≈ 500; System Health forward-test `n` grows; leaderboards list ~400–500 ranked names.
- **New user actions:** none (the screen+ingest is an offline dev-run, not a request-path action).
- **UI surface changes:** no new pages/components — the previously-suppressed `/methodology` card and
  `/data` Universe metric now populate with real data; existing surfaces render the wider universe with
  layout unchanged.
- **Navigation changes:** none. J-22's homes (`/methodology`, `/data`) are existing IA homes already in
  `blueprint.md`. No `blueprint.reapproval-requested` this iteration.

## Visual Requirements (Frontend Present: yes)

- **Component patterns:** no new components — the existing shadcn/ui `Card` + `Badge` Universe-Selection
  card and the `/data` coverage metric auto-populate. Numbers in monospace tabular-nums; palette tokens
  only.
- **Layout:** unchanged — `/data` coverage grid already widened to 6 metrics in iter-7; `/methodology`
  card sits above the setup/pattern glossary.
- **Key visual effects:** none new; display-only currency formatting (`$2B` / `$50M` / `$10`) of API
  values — the frontend NEVER recomputes membership, size, or a threshold.
- **States to handle:** honest gate preserved (card simply absent until `universe.json` exists — no
  fabricated fallback); existing loading/error/empty treatments untouched.

## Key Test Scenarios

**Backend (full pytest, run ONCE after the db regen — boot is ~14 min):**
- `config.universe.symbols` spans **~400–500 real names** (not 122), each with committed daily OHLCV;
  `data/seed/universe.json` exists; **every member passes the recorded screen** ($2B / $50M / $10 from
  `universe.filters`). → the 3 now-active `test_universe_screen.py` committed-record tests pass.
- `GET /api/methodology` serves `universe_selection` (rule + 3 thresholds resolved live via `ref`, no
  re-typed numbers, + `resolved_size` ≈ 500); `GET /api/data` `universe_count` ≈ 500 — both read the
  **same** resolved universe (single source, no drift). → `test_methodology.py` / `test_api_methodology.py`.
- **No anti-goal violation:** `test_no_magic_numbers` green over the expanded universe; `test_config`
  green; `test_seed_integrity` green (BOTH risk-on AND risk-off stretches present); no-lookahead +
  snapshot-immutability suites green.
- **Error paths:** a candidate that fails to fetch / returns empty-or-partial / lacks a market cap /
  fails a threshold is **logged + OMITTED**, never fabricated (the `screen_reasons` predicate failure
  paths are unit-asserted); if the bulk fetch hard-walls and < ~400 names pass, **halt honestly** rather
  than pad or fabricate.

**Browser (browser-qa-agent — assert live DOM/URL state before each capture; de-dup screenshots by
sha256 per the iter-6 shared-browser lesson):**
- **J-22 (primary):** `/methodology` Universe-Selection card shows the membership rule + the three
  thresholds + resolved size ~400–500; `/data` Universe coverage ≈ same count; both consistent (single
  source); screen is config-driven (matches `universe.filters`), not a hand-curated code list.
- **J-07 (critical):** open a seeded Risk-Off bootstrap run → Risk-Off (or Defensive) label + **0
  Actionable**. **J-08:** older runs differ from latest; rows never mutated.
- **Regression spot-checks:** J-01 + J-02 (dashboard + leaderboard render ranked rows on the ~500-name
  universe); J-09 (System Health renders, `n` grew); J-12 (methodology glossary intact + the new card);
  J-17 (`/data` coverage). Required-still-passing full set: J-01–J-06, J-09, J-12, J-13/J-14/J-18 (one
  global as-of control drives every page), J-16 (VCP), J-17, J-19. Journeys assert structural/relational
  properties, so the wider universe must not break them.

## Assumptions (documented per token policy — not blocking questions)

1. **`--end 2026-05-29`** (per spec) aligns to the existing seed's end-of-window — this is a universe-
   WIDTH expansion, so new names get committed bars over the existing date window; the bootstrap /
   forward-test date grid is unchanged.
2. The committed `universe_pool.csv` (550 candidates) and both runbook scripts are present and unchanged
   from iter-7 (verified at plan time); the screen reuses existing committed CSVs and fetches only NEW
   names (deliberate, documented in iter-7 handoff — minimizes 429 exposure, preserves the proven seed).
3. ~400–500 passers is the success band. If the fetch succeeds but fewer than ~400 names pass the screen
   honestly, that is a real result to surface — **not** a reason to loosen thresholds or pad the list.

## Risks / Flags

- **HARD DEPENDENCY: Yahoo reachability at dispatch.** This whole iteration is gated on the no-key Yahoo
  OHLCV + market-cap endpoints. Plan-time probe was GREEN (2026-06-02), but the limit is IP/volume-
  sensitive. The dev MUST re-probe with ONE polite request at step start; **if re-walled, halt honestly
  (STALLED) — never fabricate, never blind-loop.** This is the iter-7-designed behavior, not a defect; a
  blind dev retry against a closed wall must NOT be attempted (iter-7 lesson).
- **Heavy-op discipline (project memory):** full walk-forward pytest boot is ~14 min — run it **once**,
  after the db regen; never two pytest invocations concurrently. Kill/restart dev servers **by port**
  (backend 8835 / frontend 3835), never a broad `pkill`.
- **Shared-browser corruption (iter-6 lesson):** if both `qa` and `browser-qa-agent` drive Chrome,
  serialize access (one vacates before the other captures), assert live DOM/URL immediately before each
  capture, and de-dup evidence by sha256.
- **Evaluator process note:** full-depth iters here have sometimes finished without a `status.json` /
  auditor handoff — verify the J-22 critical seams directly in source/state (universe size via
  `yaml.safe_load`; `universe.json` present; `/api/methodology` serves `universe_selection`; both
  Risk-Off bootstrap runs show 0 Actionable) rather than trusting a handoff alone.

## Scope alignment (no drift)

The spec faithfully advances goal journey **J-22** (transparent, rule-based ~400–500-name universe) and
honors every named anti-goal (no fabricated data, no magic numbers, Risk-Off gates Actionable, no
lookahead, immutable snapshots, single source / no read-path recompute, no secrets, honest limitations).
**Correctly out of scope** (excluded): J-23/J-24 (multi-timeframe/intraday bars), J-25–J-31 (`/research`
labs — those require adding `/research` to the nav skeleton **and a blueprint re-approval**, recommended
as the immediate next wave), date-grid extension, and any change to scoring/regime/scanner/forward-test
logic or to weights/thresholds/bucket edges. The only permitted config edit is the Risk-Off bootstrap-
date swap, and only if a label flipped.
