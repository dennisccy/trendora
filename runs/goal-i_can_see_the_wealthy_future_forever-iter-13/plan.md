# goal-i_can_see_the_wealthy_future_forever-iter-13 Execution Plan

**Target journey:** J-30 — Volatility as a first-class factor family on the `/research` Factor Lab
(level: ATR% + HV · change/contraction: VCP-style compression ratio · downside/semivol), decile +
rank-IC + by-regime, raw and downside-risk-adjusted.
**Depth:** full — **crosses the critical scoring/snapshot path** and requires a **DB regen** + a
re-verify of the critical **J-07 Risk-Off gate** and **J-06 score consistency** after regen.
**Type:** NEW stored factor values (not a read-only slice like iter-10/11/12). Blueprint already
updated additively by the decomposer (IA row 80, Data-Contract row 174) — **no nav change, no
`blueprint.reapproval-requested`**. The decile/rank-IC/by-regime analysis OVER the new factors is the
**existing** `compute_factor_lab` value — **no new research function, no new endpoint.**

## Verified codebase findings (this planning pass)

- `indicators.py` has ATR%, SMA, RS, MA-stack, dist-from-high, vol-trend — **no HV, no independent
  contraction, no downside/semivol** (the three new measures are genuinely absent). ✔ spec accurate.
- `scoring.py:146` `entry_quality.contraction = _neg(atr)` (= −ATR%, NOT an independent contraction).
  Bars are read once per stock via `bars_asof(... ≤ asof)` (lines 110, 323); `hi/lo/series` already in
  hand at line ~128 → the three new values compute from the SAME as-of bars (no extra round-trip, no
  lookahead). `_build_score` (line 162) is the weighted sum; weight keys are the closed sets at
  `config.py:85-92` — the new values touch **none** of them.
- `models.py:135` `ScannerResult` already carries the append-only typed-column precedent
  (`is_vcp`, `is_pullback_to_rising_dma`, `is_flat_base_breakout`) — the exact pattern the new columns follow.
- `config.py:97` `FACTOR_TYPED_COLUMNS` + `parse_factor_source` (102) + `_factor_lab_sources_resolve`
  (943) already resolve a **bare-column** factor `source` by set-membership and fail boot loudly on a
  typo → **Option A (typed columns) needs only to extend the set**, no validator branch.
- `research.py:_extract_factor_value` (134) column branch is `getattr(res, column)` and
  `_factor_observations` (183) **already excludes `None`** → the new Optional columns flow through the
  read path unchanged; short-history → NA → excluded honestly. **`research.py` needs no logic change**
  (only the line-136 "never NULL" docstring note becomes "never NULL for the score columns; the
  volatility columns may be NULL → excluded").
- `config.yaml:586-596` factor catalog — the existing `atr_pct` entry
  (`family: volatility, direction: lower_better, source: risk.components.atr_pct.raw`) is the template
  the three new entries copy. Frontend dropdown is config-driven and already renders `factor.family`.

## What to Build

### Backend — indicator math (`app/engine/indicators.py`, modify)

Add three pure, DB-free, NA-graceful functions, each taking its window(s) as **arguments** (periods
come from config — No magic numbers; only structural literals `0/1/2/100`/`0.5`):

- **`hist_volatility(closes, window)`** — stdev of daily simple returns over `window`, expressed as a
  **percent** (comparable to ATR%). NA if fewer than `window + 1` bars.
- **`vol_contraction(closes, recent, prior)`** — continuous VCP-style compression ratio =
  recent realized vol / prior realized vol over the two config windows. **`< 1` = volatility drying up
  = contracting** (the VCP thesis, continuous). NA on insufficient history **or a zero prior**.
  *(The dev MAY instead derive a continuous value from `patterns.detect_vcp`'s contraction internals if
  that ties more tightly to the VCP definition — either way: continuous, price/volume only, ≤ D,
  config-windowed. It MUST NOT mutate `detect_vcp`, the VCP flag, the setup status, or any score.)*
- **`downside_vol(closes, window)`** — trailing downside semideviation about **MAR=0**:
  `sqrt(mean(min(r, 0)**2))` over `window` daily returns, **negative leg only** (NEVER total vol). NA on
  insufficient history. **Distinct** from `research.py:_downside_deviation` (that one is over *forward*
  returns for the risk-adjusted column; this is a *pre-snapshot stock characteristic*, bars ≤ D).

### Backend — store on the immutable snapshot (`app/engine/scoring.py` + `app/models.py`, modify)

- In `score_stocks`'s per-stock loop, compute `hv` / `vcp_contraction` / `downside_vol` from the bars
  already read for that stock (≤ asof) and **store them on the `ScannerResult` row**.
- **Storage = Option A (RECOMMENDED): typed `Optional[float]` columns on `ScannerResult`** — add
  `hv`, `vcp_contraction`, `downside_vol` as `Field(default=None)` (the `is_vcp` precedent; a fresh DB
  from `create_all` carries them — no Alembic). Catalog `source` = the bare column name.
  - *(Alternative, only if the dev prefers: a non-scored `record_json["volatility"].components` block +
    extend `FACTOR_SOURCE_BLOCKS` AND add a parallel `volatility.*` branch to `_factor_lab_sources_resolve`
    with a config-declared allowlist so boot stays loud. This is strictly more code than Option A — pick
    it only with cause.)*
- **HARD CONSTRAINT (the keystone of this iteration):** the three values **MUST NOT enter any weighted
  score.** They are not added to `config.scores.{leadership,entry_quality,risk}.weights` and never pass
  through `_build_score`. Consequence that MUST hold and be tested: every stock's Leadership / Entry
  Quality / Risk score, A–E bucket, setup status, candidate counts, regime label, and the
  **Risk-Off→Actionable gate** are **byte-identical** before and after this change. *(Single source of
  truth + Risk-Off gating — critical; the single biggest risk is a volatility value leaking into a
  weighted score.)*

### Backend — config (`config.yaml` + `app/config.py`, modify)

- `config.yaml` → under `indicators`: add `hv_window`, `semivol_window`, `vol_contraction_recent`,
  `vol_contraction_prior` (positive ints).
- `config.yaml` → under `research.factor_lab.factors`: add three entries, all `family: volatility`,
  `direction: lower_better`, copying the `atr_pct` template:
  - `{ key: hv,              label: "Historical volatility (HV)",        family: volatility, direction: lower_better, source: hv }`
  - `{ key: vcp_contraction, label: "Volatility contraction (VCP-style)", family: volatility, direction: lower_better, source: vcp_contraction }`
  - `{ key: downside_vol,    label: "Downside volatility (semivol)",     family: volatility, direction: lower_better, source: downside_vol }`
- `app/config.py` → extend `FACTOR_TYPED_COLUMNS` (line 97) with `"hv"`, `"vcp_contraction"`,
  `"downside_vol"` so the bare-column sources resolve at boot (`IndicatorsCfg` already allows extra keys
  for the new windows; the dev MAY add typed int fields instead — either is fine). **No change to the
  component-source validator** is needed under Option A.
- Keep `test_no_magic_numbers` green (it scans `indicators.py`, `scoring.py`, `research.py`): windows +
  labels live in config; the only new literals are structural.

### Backend — DB regeneration (operational; after the scoring change)

Existing snapshots predate the new values, so regenerate so every immutable snapshot carries them and
the forward-return pool stays intact. **Per project memory:**
- Stop the backend **by port 8835** (`fuser -k 8835/tcp` — NEVER a broad `pkill`; multi-project machine).
- Delete `apps/backend/data/trendora.db`, reboot so `db.create_all` + `scanner.bootstrap_runs` rebuild
  all snapshots and `forward_testing.backfill_run_forward_returns` repopulates returns.
- Run the **full** backend pytest **ONCE** after regen (~14 min heavy walk-forward boot; **do NOT run
  two pytest invocations concurrently**).

### Frontend (`apps/frontend/app/research/page.tsx`, modify — recommended, low-risk)

- **Core acceptance needs no code change** — the three new volatility factors appear in the existing
  config-driven dropdown automatically; selecting each renders its decile table (raw + downside-risk-
  adjusted) + rank-IC + by-regime split via the existing `FactorLab` component.
- **Recommended:** group the dropdown `<option>`s by `factor.family` (native `<optgroup>` keyed off the
  config-driven family already in the payload) so J-30 step 1 ("select the **volatility family**") is
  obvious. **Purely presentational, config-driven** — derive groups from `data.factors`; do NOT
  hard-code a volatility factor list in the frontend; no recompute, no new value.

## Agents Required

- developer: **yes** — backend (indicator math + scoring/snapshot store + model columns + config +
  config typing) and the recommended frontend `<optgroup>`, plus unit/integration tests + the DB regen.
  Single full-depth iteration on the critical path.
- backend-data: **yes**  ·  frontend-ux: **yes** (presentational dropdown grouping only)

## Frontend Present

yes

## Files to Create/Modify

- `apps/backend/app/engine/indicators.py` — **modify.** Add `hist_volatility`, `vol_contraction`,
  `downside_vol` (pure, config-windowed, NA-graceful).
- `apps/backend/app/engine/scoring.py` — **modify.** Compute the three values from the per-stock as-of
  bars and store them on the `ScannerResult` row. **Do NOT touch `_build_score` or any weights dict.**
- `apps/backend/app/models.py` — **modify.** Add `hv`/`vcp_contraction`/`downside_vol` as
  `Optional[float] = Field(default=None)` columns on `ScannerResult` (the `is_vcp` append-only precedent).
- `config.yaml` — **modify.** Add the four `indicators` windows + three `research.factor_lab.factors`
  entries (`family: volatility`). No existing tunable or weight touched.
- `apps/backend/app/config.py` — **modify.** Extend `FACTOR_TYPED_COLUMNS` with the three column names
  (and optionally type the new `IndicatorsCfg` windows).
- `apps/backend/app/engine/research.py` — **modify (doc only).** Update the `_extract_factor_value`
  line-136 "never NULL" note to reflect the new Optional volatility columns. **No logic change** —
  None already excluded at `_factor_observations:183`.
- `apps/frontend/app/research/page.tsx` — **modify (recommended).** `<optgroup>`-by-`family` dropdown
  grouping (presentational, config-driven). `lib/api.ts` likely unchanged (`family` already typed).
- `apps/backend/tests/test_indicators.py` — **modify.** Exact values on a known fixed series + NA on
  short history for all three functions (periods from config).
- `apps/backend/tests/test_scoring.py` — **modify.** The **score-invariance regression keystone** (see
  Key Test Scenarios). Protects J-06/J-07.
- `apps/backend/tests/test_config.py` — **modify.** The three new factor sources RESOLVE at boot; an
  unresolvable/typo source raises `ConfigError` loudly; `test_no_magic_numbers` stays green.
- `apps/backend/tests/test_research.py` — **modify.** `compute_factor_lab` populates deciles + rank-IC +
  `by_regime` for each new factor on the seed; low-sample → NA + `n`; risk-adjusted is downside-only;
  the read-only patch-to-raise keystone still passes.
- `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-13-dev.md` — **create.** Dev handoff.

## UI Evolution (Frontend Present: yes)

- **New user-facing capability:** on `/research`, pick each of the **four** volatility measures (ATR%,
  HV, VCP-style contraction, downside/semivol) at any horizon and read whether — and in which
  **direction** — that measure sorted realized forward returns in this universe, on a downside-risk-
  adjusted basis, overall and split by regime, with honest `n`/NA. Volatility graduates from a single
  ATR% factor to a labelled **family of four**.
- **New information displayed:** decile table (raw mean + downside-risk-adjusted + `n`) + rank-IC
  `{value, n}` + by-regime split for three NEW factors, rendered by the existing Factor-Lab surface.
- **New user actions:** select the new measures from the factor dropdown (and, with the optgroup, see
  them grouped under a **Volatility** family heading). No new date control, no new mutation.
- **UI surface changes:** `/research` Factor Lab only — additive catalog members + optional dropdown
  grouping. No new page, route, endpoint, or nav entry.
- **Navigation changes:** none (J-18 / blueprint preserved).

## Visual Requirements (Frontend Present: yes)

- **Component patterns:** reuse the existing `FactorLab` decile `<table>`, rank-IC display,
  `RegimeEffectivenessTable`, `SampleSize`, and the NA cell treatment **verbatim** — the new factors
  render through them with zero new component. Optional `<optgroup>` styled like the existing `<select>`.
- **Layout:** unchanged `/research` page; dark analytical-workstation tokens only; numbers
  monospace/tabular.
- **Key visual effects:** existing colour-graded returns + warn-token NA chips + the page's
  survivorship-bias + descriptive-not-predictive `CaveatBanner` (must stay visible for J-30).
- **States to handle:** loading skeleton; "Backend unavailable" error card; **honest NA** — a low-sample
  regime (e.g. Strong risk-on / Defensive at n=0) or a downside-undefined decile (all-non-negative →
  `risk_adjusted` NA) renders **NA + n**, never a fabricated 0. Option lists come from the payload — no
  hard-coded factor/family list in the frontend.

## Key Test Scenarios

- **Score-invariance regression (CRITICAL keystone — protects J-06/J-07):** assert the three scores +
  A–E buckets + setup status + candidate counts + regime label for a representative scored set are
  **byte-identical** with the volatility additions present (the new values never enter `_build_score`
  or any weight sum). Reviewer/auditor must confirm in source that none of
  `hv`/`vcp_contraction`/`downside_vol` appears in any `config.scores.*.weights` and `_build_score` is
  unchanged.
- **Indicator math:** exact values for `hist_volatility` / `vol_contraction` / `downside_vol` on a known
  fixed series; NA on short history; `vol_contraction` NA on a zero prior; `downside_vol` uses the
  negative leg only (an all-up series → 0/NA per definition, never penalising upside).
- **Config boot:** the three typed-column sources resolve at boot; a typo source → `ConfigError` loudly
  (never a silent default); `test_no_magic_numbers` stays green (only structural literals added).
- **`compute_factor_lab` over the new factors:** populated deciles + numeric rank-IC + `by_regime` for
  `hv`/`vcp_contraction`/`downside_vol` on the seed; low-sample decile/regime → NA + `n`; the
  risk-adjusted column is **downside-only** (None when a decile has no downside / n<2).
- **Read-only keystone (regression):** the existing `test_research.py` patch-to-raise on
  `run_scan`/`score_stocks`/`detect_*`/`score_regime` still passes — the lab recomputes nothing.
- **Error cases:** unknown factor key → endpoint **422** (existing behaviour, extended catalog); a
  factor-NULL observation is EXCLUDED (never bucketed/fabricated); short-history stock → NA volatility
  values that propagate to honest NA, never a fabricated 0.
- **Browser (browser-qa-agent; serialized with qa on shared Chrome; de-dup every shot by sha256):**
  - **J-30:** on `/research`, select each of the four volatility measures (`atr_pct`, `hv`,
    `vcp_contraction`, `downside_vol`) → each renders a populated decile table (raw mean **and**
    downside-risk-adjusted, each with `n`), a numeric rank-IC with `n`, and the by-regime split;
    capture at least one **honest-NA** cell (target an empty/low-sample **regime** — e.g. Strong
    risk-on / Defensive at n=0 — or a downside-undefined decile; **NOT** horizon shrinkage, per the
    iter-11 lesson that `n` is ~horizon-independent in this seed); the survivorship-bias +
    descriptive-not-predictive labels are visible; "risk" is downside-only.
  - **Contraction cross-check:** `vcp_contraction`'s decile/IC is read from the SAME stored
    `forward_returns` the System Health VCP-vs-non-VCP breakdown uses (no recomputation); state the
    reported **direction honestly** — if contraction does NOT predict, that is a valid honest finding
    (acceptance is descriptive, per "rather than assuming the textbook relationship").
  - **J-18 (regression risk):** toggle the global as-of date → the Factor-Lab tables stay
    **byte-identical** with **zero** `as_of`-param requests (extend the iter-11 check to the new factors).
  - **J-25 / J-27 (regression):** decile table + rank-IC + regime split still render and re-point on
    factor change.
  - **CRITICAL post-regen:** **J-07** — open the seeded Risk-Off run → confirm **zero** stocks
    "Actionable"; **J-06** — NVDA's Leadership/Entry/Risk (number + bucket) are byte-identical on
    `/stocks` and `/stocks/NVDA`.
- **Required-still-passing (re-verify green):** J-02, J-05, J-08, J-09, J-12, J-16, J-18, J-19, J-25, J-27.
- **Suite:** full backend `pytest` runs **once** after the DB regen (~14 min — do NOT run two pytest
  invocations concurrently); frontend `npm run build` typechecks.

## Notes / Scope Discipline

- **This iteration touches the critical scoring/snapshot path** (unlike iter-10/11/12, which were pure
  read-only slices). The guard is the **score-invariance regression test** + a source check that no new
  value enters any weight. The new values are stored *for lab consumption only* — they ride the canonical
  `/api/stocks` + `/api/stocks/{ticker}` rows but **do NOT** touch the `/stocks` leaderboard UI, the
  stock-detail score breakdowns, or the badge registry (the leaderboard pattern registry is hardcoded —
  iter-9 lesson — and is **not** in scope here; the factor dropdown is config-driven, so the new factors
  auto-appear with no registry edit).
- **Out of scope (do NOT build):** J-29 event study / MAE-MFE excursion path / `return/MAE` (this iter's
  risk-adjusted column stays the existing downside-return-deviation ratio); J-31 synthesis; any new date
  control or as-of state on `/research`; adding any volatility value to a weighted score, the stock-detail
  breakdowns, or the leaderboard.
- **DO NOT autonomously fetch, probe, or retry J-22/J-23/J-24** — they remain externally Yahoo-429
  data-walled and auto-heal only on operator confirmation of a reachable no-key egress. J-30 is
  **compute-only over the committed seed — NOT data-walled.**
- **Coherence:** the new per-stock volatility values are registered in the Data Contract (blueprint row
  174) with ONE computing module (`scoring:score_stocks`) + ONE storage (the immutable snapshot), read
  verbatim by `compute_factor_lab` — NOT a second computation of any existing value and NOT a new
  endpoint. The decile/IC/by-regime analysis stays the existing `compute_factor_lab` value. Expect
  COHERENCE-PASS.
- **Process expectation (this session):** a full-depth iter here typically produces no `-audit.md` and
  writes `status.json` at the phase-namespace path
  `runs/goal-i_can_see_the_wealthy_future_forever-iter-13/status.json` (NOT under
  `runs/goal-session-.../iter-13/`). Verify the critical seams **in source**; do not block on absent
  audit/status artifacts.
- **GOAL_ACHIEVED is not autonomously reachable** while J-22/J-23/J-24 stay data-walled. Autonomous
  runway after J-30: **J-29** (event study; needs the post-snapshot MAE/MFE excursion path) → **J-31**
  (synthesis; needs J-29 + J-27).
- **No phase-spec / goal drift detected.** J-30 maps exactly to goal capability #30 (volatility family)
  and the J-30 journey; the blueprint iter-13 rows (80, 174) match this plan; the anti-goals
  (read-only lab, downside-only risk, no lookahead, single source of truth, no magic numbers, Risk-Off
  gating) are all explicitly guarded above.
