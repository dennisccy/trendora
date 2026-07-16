# goal-mcp-loop-iter-41 Execution Plan

## Context (read before building)

Goal-mode session `mcp-loop`, FULL iteration 41. Target: **J-25** (backlog **B-205**) — a
phase-conditional **drawdown & dry-spell expectations panel** inside each certified claim's card on
`/evidence`. J-25 is the LAST unbuilt Must-have journey — landing it (+ the iter-42 lean closeout)
makes GOAL_ACHIEVED reachable. Full binding spec: `docs/improvement-backlog.md` card **B-205**
(lines ~1041-1077) — read it before implementing; this plan summarizes it but B-205 is authoritative
on traps/config surface. It carries **no Evidence Claim** (B-205: "must not introduce proven-language
anywhere") — the post-decompose gate passes automatically; both ledgers stay byte-identical 7/7 FAIL,
canonical divisor stays 8.

**Working tree: verified CLEAN at HEAD `3768228`** (iter-40 showcase commit). `git status
--porcelain` shows only untracked bookkeeping (the iter-41 phase spec, `runs/goal-mcp-loop-iter-41/`,
dispatch req files) — no parked/uncommitted work to reconcile this time.

**Outcome-neutral, unlike J-02/J-06/J-07/J-08/J-09.** The panel is descriptive cohort history and
renders for ANY claim regardless of PASS/FAIL verdict (today's ledger is 7/7 FAIL) — so this journey
CAN fully pass on the current ledger. Do not apply the iter-28 "honest-absence" re-scope logic here;
it doesn't apply.

**Systemic replay-lane gap (recurring iter-33/36/38/40).** A FULL iteration routes through
`run-phase.sh`, which has no deterministic-replay lane. Per the spec's own NOTES, the "required-
still-passing golden replay" DoD line is structurally unsatisfiable here and is DEFERRED to iter-42's
lean closeout. THIS iteration's required-still-passing set (J-01, J-02, J-04, J-05, J-11, J-10, J-13,
J-15, J-16, J-20) is satisfied by **live browser-qa re-verification**, not a golden replay — do not
let any stage claim "replay ran" without evidence (the exact iter-33/36 CLOSURE-FAIL trap).

**HARD PRECONDITION carried from iter-40's eval.** iter-40's canonical browser-qa lane SKIPped all 16
tests on a Chrome-MCP DevTools port-binding outage. If it recurs here, fall back to demo-narrator
(Playwright) frames + functional-QA frames + the auditor's byte-match instead of defaulting J-25 to
`unknown` (iter-40 lesson).

**One risky element only (full-depth justification).** The stored-column addition + its full-universe
backfill is the one risky element crossing backend+frontend+data-model; everything else (aggregation,
API field, UI panel) is mechanical additive work on top of it.

## What to Build

### Backend

- **Two new append-only nullable columns on `ForwardReturn`** (`apps/backend/app/models.py`
  ~L327-393, right after `max_drawdown`): `underwater_days: Optional[int]` and
  `time_to_recover_days: Optional[int]`. Docstring mirrors the `max_drawdown` (iter-27/J-86) note
  verbatim in structure: computed ONCE in `_insert_run_forward_returns`, same no-lookahead NA gate
  (non-None iff `realized_return` exists), forward-side only, read verbatim downstream. Register both
  in `db._ADDITIVE_COLUMNS` (`apps/backend/app/db.py` L108-124 — mirror the exact
  `("forward_returns", "max_drawdown", "ALTER TABLE forward_returns ADD COLUMN max_drawdown FLOAT")`
  tuple, `INTEGER`, nullable) so a live DB that is NOT rebuilt this pass still degrades honestly
  (NULL) instead of 500ing.
- **Two new pure helpers in `forward_testing.py`** (beside `max_drawdown` at L185-217, same file
  section as `forward_return`/`forward_excursions`): `underwater_days(bars_after_list, entry_close,
  horizon)` and `time_to_recover_days(bars_after_list, entry_close, horizon)`. **REUSE `max_drawdown`
  verbatim for DD-depth — do not fork it** (B-205 ★ Do NOT touch). Nail down ONE definite semantic in
  the docstring and mirror `max_drawdown`'s running-peak pattern (seeded at `entry_close`) for
  "underwater" (close below the running high-water mark) so the three measures stay conceptually
  consistent; `time_to_recover_days` = bars from the max-drawdown trough until close first returns to
  the entry level within the horizon, **NA (never a fabricated horizon-sentinel) if it never
  recovers**. Same NA gate as `forward_return` (`entry_close` None/0, or `< horizon` post-bars).
  Fixture-test against constructed series with known underwater spans / recovery points (mirror
  `test_backfill_populates_max_drawdown_same_na_gate` at `test_forward_testing.py:852`).
- **Wire into `_insert_run_forward_returns`** (`forward_testing.py` L289-346, right beside the
  existing `mdd = max_drawdown(post_bars, entry_close, horizon)` call at L329): call both new helpers
  on the SAME `post_bars`/`entry_close`/`horizon` already in hand — **zero extra bar reads** — and
  pass `underwater_days=...`, `time_to_recover_days=...` into the `ForwardReturn(...)` constructor.
  This is the SINGLE shared INSERT path (both the cadence-wide `_backfill` and the per-run
  `backfill_run_forward_returns` used by `data_manager.py`'s memory-hardened backfill job route
  through it), so this one change point covers every caller automatically.
- **New aggregation `compute_drawdown_expectations(session, claim, cfg)`** in `forward_testing.py` —
  resolve the claim's cohort observations via the SAME selectors `app.engine.samples:compute_samples`
  uses (no second cohort resolver — map the claim's `kind`/`factor`/`slice_kind`/`decile`/`horizon` or
  `condition` selectors onto `compute_samples`'s kwargs exactly as `/api/research/samples` does).
  Check what `compute_samples`'s row shape already exposes vs. what needs an additive read straight
  from `ForwardReturn` (`realized_return`, `max_drawdown`, the two new columns, plus each
  observation's `asof_date` for the phase join) — extend read-only, never forking a second resolver.
  Join each observation to its **causal phase at entry** via
  `app.engine.market_phase:phase_context_by_date(session, as_of, cfg)` (L646-667, keyed by ISO
  `asof_date` — the SAME causal timeline `compute_market_phase` reads, never the smoothed/retrospective
  one). Emit per-phase `{median, p90, n}` for the four measures. **Loss-streak trap (B-205 named):**
  the longest run of consecutive NEGATIVE cohort forward-returns must be counted at the
  **walk-forward cadence** (iterate cadence `asof_date`s in order), NOT daily — daily double-counts
  overlapping horizons. Attach `"survivorship_bias": SURVIVORSHIP_BIAS_LABEL` (the existing
  module-level constant at `forward_testing.py:57`, already reused verbatim across `research.py` —
  do not author new caveat prose). Per-phase distribution floor reuses the EXISTING
  `wf.min_sample` (30, `config.py` L731); loss-streak floor is the NEW `wf.streak_min_n`. Below-floor
  cells render `"insufficient (n=…)"`, never a fabricated distribution.
- **Config additions** — `WalkForwardCfg` (`config.py` L719-749) gains `underwater_horizons:
  list[int]` and `streak_min_n: int` (both required, validated positive in `_validate`, mirroring the
  existing `horizons`/`min_sample` checks). `config.yaml` `walk_forward:` block (L772-791) sets both.
  **Ripple (iter-40 precedent):** adding required `WalkForwardCfg` fields will break every inline
  `walk_forward` config fixture across the 9 files that construct one (`test_forward_testing.py`,
  `test_warmup.py`, `test_config.py`, `test_indexes.py`, `test_sectors.py`,
  `test_iter20_research_cluster.py`, `test_research.py`, `test_config_engine.py`, `test_themes.py`) —
  extend each fixture with the 2 new keys, exactly as iter-40 did for `IndicatorsCfg.gap_window`/
  `.worst_window_days`.
- **`GET /api/evidence` additive `expectations` field, NOT a new endpoint:**
  - `apps/backend/app/api/evidence.py` — add `session: Session = Depends(get_session)` (mirror
    `themes.py`/`sectors.py`) and thread config through to `build_evidence_payload`.
  - `apps/backend/app/engine/evidence.py`'s `build_evidence_payload(ledger_path: str, ...)` —
    **CRITICAL:** add `session`/`config` as OPTIONAL keyword-only params defaulting to `None`. ~13
    existing call sites (`test_evidence.py` incl. the frozen-golden `test_canonical_ledger_frozen_
    golden` at L561, `test_graveyard.py`, `test_api_graveyard.py`, `test_api_budget.py`,
    `test_budget_accounting.py`) call `build_evidence_payload(str(ledger))` with ONE positional arg
    and MUST stay green **unedited** (the DoD's "an edit to an existing test is itself the regression
    signal" rule, iter-9 precedent). When `session` is `None`, `expectations` must be absent/empty per
    claim — honest, never a crash. Only the real `/evidence` route (which now passes session+config)
    attaches real expectations. Missing/empty ledger or an unresolvable cohort ⇒ honest empty/NA
    `expectations`, always 200.
- **Full-universe backfill of the two new columns — NOT deferrable this iteration.**
  `_insert_run_forward_returns` is idempotent on `(run_id, symbol, horizon)` — re-running the cadence
  backfill will **skip** every already-inserted historical row, so the new columns will NOT populate
  on old data just by re-running it. The established path (iter-27 `max_drawdown` / iter-40
  `risk_budget` precedent, `db.py:117-122`'s own comment: "existing rows read NULL until the next
  confirm-gated rebuild") is: delete `apps/backend/data/trendora.db` (+ `-shm`/`-wal`) and let a fresh
  full boot + background warmup recompute EVERY snapshot + forward-return row from scratch (a fresh
  DB's `existing` set starts empty, so every row gets the new columns for free, and the deep
  historical phases — Correction/Bear 2000/2008/2020/2022 — get real coverage to clear the per-phase
  floor). **Unlike iter-40, which explicitly deferred its DB rebuild as a "Known Issue," this
  iteration's DoD requires the backfill to complete under the 6144 MB cap on the FULL-universe shape
  with BOTH VSZ and RSS sampled** (iter-26 lesson: RSS-only on a subset doesn't count) and a new
  `reports/perf-budgets.md` entry — reuse the exact measurement methodology already on record there
  (`MALLOC_ARENA_MAX=2`, `ulimit -v 6291456`, VmPeak/VmRSS from `/proc/<pid>/status`, two consecutive
  runs). Also re-measure `/api/evidence` + `/evidence` against the J-15 budget and record it. **Do not
  defer this step again** — flag it loudly to the reviewer if turn-budget forces a deferral.

### Frontend

- **`apps/frontend/lib/evidence.ts`** — extend `CertifiedClaim` (L31-41) with an `expectations` field
  (nullable; per-phase object of the four measures × `{median, p90, n}` or an `"insufficient"`
  marker, plus `survivorship_bias: string`). Keep the file's existing PURE/dependency-free convention.
- **`apps/frontend/lib/api.ts`** — nullable-field discipline (iter-18/19 lesson): type every new
  numeric field `number | null` and route consumers through a guarded NA render — never an unguarded
  `.toFixed`/sort call that crashes the card on `null`.
- **`apps/frontend/app/evidence/page.tsx`** — extend `ClaimRow` (L151-227) with a new panel section
  (inside the same `CardContent`, after the existing `<dl>` Field grid) rendering the per-phase table:
  phase × {max-DD depth, underwater duration, time-to-recover, longest losing streak}, each
  median/p90 + `n`. Reads `claim.expectations` **verbatim** — no client-side recompute. Thin phases
  render `"insufficient (n=…)"`. Copy is strictly historical ("historically saw…"), plus a visible
  walk-forward-cadence method note and the `survivorship_bias` caveat read verbatim from the payload
  (reuse the SAME rendering treatment `evidence-panels.tsx` already gives `survivorship_bias`
  elsewhere — do not author new caveat prose client-side). **Below the fold inside the claim card** —
  flag for browser-qa's capture discipline (see Key Test Scenarios).

**Out of scope (do not build):** any `## Evidence Claim` / new certified edge; forking `max_drawdown`
or the phase-timeline computation; reusing `market_phase`'s trailing `time_underwater` severity
component as the forward duration (a different, causal-trailing concept — do not conflate); any change
to Leadership/Entry Quality/Risk/regime/existing forward-return aggregates; nav/route changes; the
backtest-page panel and the B-1203 Sunday sheet (deferred); CVaR (B-206), phase-transition cards
(B-207), sequence-risk Monte Carlo (B-208).

## Agents Required

- developer: yes -- implement backend (model columns + `_ADDITIVE_COLUMNS`, pure helpers, INSERT-path
  wiring, `compute_drawdown_expectations` aggregation, config, `/api/evidence` additive field) AND
  frontend (`CertifiedClaim` type, `ClaimRow` expectations panel) in one TDD pass, plus the full-
  universe DB rebuild under the memory cap. This project's agent catalog has a single `developer`
  agent that handles both sides (no separate backend/frontend agent types exist here).
- backend-data: yes -- `models.py`, `db.py`, `forward_testing.py`, `market_phase.py` (read-only
  reuse), `samples.py` (read-only reuse), `config.py`, `config.yaml`, `api/evidence.py`,
  `engine/evidence.py`, backend fixture/unit tests, the full-universe DB rebuild + memory measurement.
- frontend-ux: yes -- `lib/evidence.ts`, `lib/api.ts` nullable typing, `app/evidence/page.tsx`
  expectations panel.

## Frontend Present
Frontend Present: yes

## Files to Create/Modify

- `apps/backend/app/models.py` -- `ForwardReturn`: add `underwater_days`, `time_to_recover_days`
  (nullable), docstring mirroring the `max_drawdown` note.
- `apps/backend/app/db.py` -- `_ADDITIVE_COLUMNS`: two new ALTER tuples for the new columns.
- `apps/backend/app/engine/forward_testing.py` -- `underwater_days()`, `time_to_recover_days()` pure
  helpers; wire both into `_insert_run_forward_returns`; new `compute_drawdown_expectations(session,
  claim, cfg)` aggregation (cohort via `samples.compute_samples`, phase join via
  `market_phase.phase_context_by_date`, walk-forward-cadence loss-streak, `survivorship_bias` via the
  existing `SURVIVORSHIP_BIAS_LABEL`).
- `apps/backend/app/config.py` -- `WalkForwardCfg`: add `underwater_horizons: list[int]`,
  `streak_min_n: int`, folded into `_validate`.
- `config.yaml` -- `walk_forward.underwater_horizons` / `.streak_min_n` values.
- `apps/backend/app/api/evidence.py` -- add `Depends(get_session)`, thread session+config into
  `build_evidence_payload`.
- `apps/backend/app/engine/evidence.py` -- `build_evidence_payload`: optional keyword-only
  `session`/`config` params (default `None`, backward-compatible); attach `expectations` per claim
  only when a session is provided.
- `apps/backend/tests/test_forward_testing.py` -- fixture tests for both new pure helpers (known
  underwater spans/recovery points, NA path); `compute_drawdown_expectations` fixture cohort ->
  exact per-phase median/p90/n; insufficient-phase path; walk-forward-cadence loss-streak
  double-count-avoidance fixture; no-lookahead test (a later bar changes no stored value/phase
  label); `max_drawdown` reuse (not refork) proof; `walk_forward` fixture extended with the 2 new
  keys.
- `apps/backend/tests/test_evidence.py` -- new tests for the additive `expectations` field
  (session-provided vs. session-omitted paths); confirm `test_canonical_ledger_frozen_golden` and
  every other existing `build_evidence_payload(str(ledger))` call stays unedited and green.
- `apps/backend/tests/test_warmup.py`, `test_config.py`, `test_config_engine.py`, `test_indexes.py`,
  `test_sectors.py`, `test_themes.py`, `test_iter20_research_cluster.py`, `test_research.py` --
  extend inline `walk_forward` fixtures with the 2 new required keys (mechanical, iter-40 precedent).
- `apps/frontend/lib/evidence.ts` -- `CertifiedClaim.expectations` field + supporting types.
- `apps/frontend/lib/api.ts` -- nullable typing for any newly-surfaced fields.
- `apps/frontend/app/evidence/page.tsx` -- `ClaimRow` expectations panel.
- `reports/perf-budgets.md` -- new full-universe backfill measurement (VSZ+RSS, two runs) +
  `/api/evidence`/`/evidence` latency re-check against the J-15 budget.
- `runs/goal-session-mcp-loop/state/blueprint.md` -- additive Data Contract row (drawdown
  expectations) + IA-table clarification row (existing `/evidence` claim cards; no nav change; no
  `blueprint.reapproval-requested`).
- `docs/handoffs/goal-mcp-loop-iter-41-dev.md` -- required dev handoff (DoD line item).

## UI Evolution

- New user-facing capability: on any certified claim's `/evidence` card, the user can read what
  following that cohort's methodology has historically felt like — drawdown depth, time underwater,
  time to recover, and worst losing streak — broken out by the market phase at entry, with honest
  sample sizes.
- New information displayed: per-phase median/p90 of max-drawdown depth, underwater duration,
  time-to-recover, and longest losing streak, each with `n`; `"insufficient (n=…)"` for thin phases;
  a walk-forward-cadence method note; the survivorship-bias caveat.
- New user actions: none — purely descriptive, read-only, no controls (anti-goals #1/#2 boundary).
- UI surface changes: one new additive section inside the EXISTING `/evidence` `ClaimRow` cards. No
  new page, no new route.
- Navigation changes: none.

## Visual Requirements

- Component patterns: reuse the existing `Card`/`CardContent`/`dl`/`Field` primitives `ClaimRow`
  already uses (page.tsx L160-226) — no new UI primitives. A small per-phase table/grid consistent
  with the existing `Field` label styling (`text-xs uppercase tracking-wide text-text-faint`).
  `Badge` for phase labels, mirroring the existing regime `Badge` usage in the same row.
  Rendered figures use the `num` class as `fmtSigned`/other numeric fields in this file already do.
  Reuse whatever component `evidence-panels.tsx` already uses for `survivorship_bias` text rather
  than inventing a new caveat treatment.
- Layout: additive block appended inside the existing claim `CardContent`, below the current `<dl>`
  grid — a compact table (phase rows × the four measures) rather than a second nested card.
- Key visual effects: none new — match the codebase's minimal, data-dense styling; no hype color.
- States to handle: a phase below the floor renders `"insufficient (n=…)"` text (not a blank cell);
  no `expectations` at all (session-less payload edge, or an unresolvable cohort) renders nothing for
  the panel section (graceful, matches the `RiskBudgetCard`'s `return null`-when-absent precedent from
  iter-40) rather than an error boundary; a `null` `underwater_days`/`time_to_recover_days` anywhere
  routes through a guarded NA render, never an unguarded crash (iter-18/19 lesson). No new loading
  state (rides the existing `/evidence` fetch + `EvidenceSkeleton`).

## Key Test Scenarios

- **Browser (canonical browser-qa-agent):** open a certified claim on `/evidence`, scroll the
  expectations panel into frame (**below the fold — use full-page or element-clip capture, `md5`-check
  for reused/blank frames**, the iter-3/11/13/14 lesson), assert per-phase median/p90/n render for all
  four measures, a below-floor phase reads `"insufficient (n=…)"`, and copy is historical with zero
  forecast/promise phrasing.
- **Regression (required-still-passing, LIVE browser-qa, not golden replay this iteration):** `/evidence`
  still renders the 7 claim rows with byte-correct verdict/control/registration fields (J-05); "Not yet
  proven" badges (J-01); no-stale-edge invariant on the 0-PASS ledger (J-11); regime-labeled claim rows
  (J-04); the score drill (J-02); `/stocks/{ticker}` deep history (J-10); `/data` (J-13); the "GO"
  preflight strip (J-20); no latency regression vs. the J-15 budget (J-15, J-16 — record fresh numbers).
- **Unit:** `underwater_days`/`time_to_recover_days` fixture series with KNOWN spells/recovery -> exact
  stats; NA on `< horizon` post-bars (never a fabricated 0); `max_drawdown` reuse (call-count or
  byte-identity proof it is not reforked); `compute_drawdown_expectations` fixture cohort -> exact
  per-phase median/p90/n; below-floor phase -> `"insufficient"`; loss-streak at walk-forward cadence
  (fixture proving daily overlap does NOT double-count); no-lookahead (a later bar changes no stored
  value or phase label); existing `forward_testing`/`scoring` expectation tests UNEDITED and green;
  `GET /api/evidence` `claims`/`proven_signals` unchanged apart from the additive `expectations` field.
- **Correctness spot-check (anti-goal #3, distinct from fixture-exactness above):** after the
  full-universe rebuild, pick one real cell actually SERVED by `/api/evidence` (e.g. a Correction-phase
  median max-DD depth for one claim's cohort) and independently re-derive it offline from the same
  stored `ForwardReturn` rows + causal phase timeline; byte-match required — mirrors iter-40's gap-p95
  served-value spot check, not just an isolated fixture assertion.
- **Language / no-badge audit (anti-goals #1/#2):** grep the new panel copy and confirm it contains no
  "Proven"/"Not yet proven" badge or status chip and no buy/sell/trim/reduce/rebalance/target verb; the
  spec's own metadata confirms no `## Evidence Claim` is registered this iteration (gate auto-passes,
  divisor stays 8, both ledgers stay byte-identical 7/7 FAIL) — verify with a ledger diff, not an
  assumption.
- **Memory:** the full-universe new-column backfill stays under the 6144 MB `ulimit -v` cap, VSZ+RSS
  sampled on both of two consecutive runs (iter-26 lesson — RSS-only on a subset does not count); no
  whole-table ORM load introduced.
- **Error cases:** missing/empty ledger -> `GET /api/evidence` still 200 with honest empty
  `expectations`; a cohort resolving to zero observations, or a phase with none -> honest empty/
  "insufficient" panel, never a 500 or fabricated cell; a `null` new field -> guarded NA render, never
  an unguarded crash of the claim card.
