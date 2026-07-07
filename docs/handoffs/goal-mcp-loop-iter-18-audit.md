# goal-mcp-loop-iter-18 Audit Report

**Date:** 2026-07-07
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The phase goal is fully and honestly achieved: the atomic 30-year / 548-pool basis swap (J-10), the ONE sanctioned all-FAIL ledger reset (J-11), and the recency/staleness gate (J-12) all landed correctly. I re-verified every load-bearing claim against the actual files, DB, and ledgers — not handoff prose — and each held: the seven regenerated ledger rows byte-match the verdict table, `proven_signals` is empty via strict `status == PASS` filtering, the shared certification engine and the DO-NOT-EDIT trio are byte-untouched, the deep price data is genuinely real (AAPL 1996-01-02, NVDA 1999-01-22, ARM honestly short), and NO retired value renders anywhere. The documented gaps are display/QA-thoroughness observations that do not compromise the goal; none rise to CRITICAL or IMPORTANT, so no fixes were applied.

---

## 2. Findings

### Backend Findings

**B1 — OBSERVATION (no change needed): Every backend DoD item independently verified against source-of-truth artifacts.**

I did not trust the handoff. I re-derived each claim from the underlying artifact:

- **Atomic swap (DoD 1).** `apps/backend/data/seed/prices/` = **590 CSVs**; `data/seed/meta.json` `window` = `{start: 1996-01-01, end: 2026-07-01}` (exact pins), `symbols_ok=590 / symbols_failed=1` (SATS honest absence), `basis_swap` provenance record present and honest (documents the retired Yahoo ~5y basis and the sanctioned reset). `data/seed-stooq-30y/` is **gone** from disk. The `symbols_ok=590` vs DB-loaded 587 reconciles cleanly: 590 CSVs minus the 3 world-index proxies (`_SPX`/`_NDX`/`_DJI`) that are committed-but-unloaded by design (J-14 out of scope).
- **DB state, NOT rebuilt (DoD 2).** `daily_prices` = **587 distinct symbols / 3,270,066 bars**; `scanner_runs` = **410 rows, asof_date 2005-02-25 → 2026-07-01** — matches the disclosed bounded cadence exactly. Product boots to "Ready" (screenshots).
- **Both ledgers (DoD 3).** `certified-claims.jsonl` and `staging-ledger.jsonl` = **7 rows each, every `verdict.status == FAIL`, every `register_date == 2026-07-03`.** The seven canonical rows byte-match the spec's verdict table: row 1 p=0.5352 / edge −0.00031 (−0.03%), row 2 p=0.9460 / −0.68%, row 3 p=0.2769 / +0.21%, row 4 p=0.9595 / −0.38%, row 5 p=0.9995 / −1.64%, row 6 p=0.4943 / +0.01%, row 7 p=0.9045 / −1.42%. `required_p` = 0.05/1, 0.05/2 … 0.05/7 (**Bonferroni divisors 1..7 preserved** — the reset never functioned as bar-laundering).
- **`proven_signals` empty (anti-goal #1).** `apps/backend/app/engine/evidence.py:103` sets `proven` = `verdict.get("status") == STATUS_PASS`, and lines 121-130 build `proven_signals` only from PASS rows. With zero PASS rows, the payload is `{}` — every badge product-wide is forced to "Not yet proven." This is the load-bearing enforcement and it is correct.
- **Shared engine + DO-NOT-EDIT trio untouched (DoD 5, iter-9 regression proof).** `git diff HEAD --stat` is **EMPTY** for `engine/{referee,ledger,online_fdr,evidence}.py`, `mcp/tools.py`, and `tests/{test_referee,test_online_fdr,test_forward_walk}.py`. Only ledger *content* regenerated, never the modules.
- **Staleness gate (J-12).** `apps/backend/app/engine/universe_resolver.py:55-106` — `REASON_STALE = "stale_series"`, `EXCLUSION_REASONS` ordered `(below_history, stale, below_price, below_adv)`, gate evaluated history → staleness → price → ADV (line 105: `if (asof - bars[-1].date).days > filters.max_staleness_days`), threshold from `cfg.universe.filters.max_staleness_days` (config = 10), no magic number, no lookahead.
- **Bars windowing (J-10).** `apps/backend/app/api/stocks.py` — `bars_asof` slice is `date <= as_of` (no lookahead) in every mode; `range=full` weekly-samples bars older than `chart_bars.downsample_beyond_years` (real bars only, never synthesized); unknown `range` ⇒ 422; `resolve_servable_symbol` broadens ticker validation to pool ∪ context ∪ stored bars.
- **config.yaml.** `walk_forward.history_years: 30`, `universe.filters.max_staleness_days: 10`, `chart_bars` (default_years 5, downsample_beyond_years 8), `bootstrap_dates` incl. 2008-11-21 (GFC) + 2020-03-20 (COVID).
- **Survivorship label restoration (dispatch-7 fix).** `forward_testing.py:57-60` — `SURVIVORSHIP_BIAS_LABEL` contains the literal "survivorship bias" AND the ~30-year framing ("Walk-forward evidence now spans up to ~30 years of history (1996 to present…").
- **No credentials (anti-goal #6).** Grep of `app/`, `scripts/`, `config.yaml` shows every `api_key` hit is a provider parameter read from env/session and never persisted; the `redact_stooq_key` choke point (iter-16 lesson) is intact in `scripts/ingest_seed.py:224`.
- **Anti-goal #2.** Every stock-detail capture renders "Research-only · decision support · no orders" — no buy/sell/price-target language.

### Frontend Findings

**F1 — GAP (not fixed — unconfirmed; recommend live-browser confirmation): full-history chart viewport for names with >8 years of history appears to plot only the trailing daily window.**

For AAPL and NVDA in "Full history" mode the chart x-axis labels consecutive years covering only ~2018/2019 → 2026 (roughly the `downsample_beyond_years = 8` daily window), and neither chart shows any pre-2018 price action, even though: (a) the payload carries the full deep series (caption bar-count 3185 for AAPL / 3025 for NVDA, i.e. daily-recent + weekly-older), (b) the caption honestly discloses `history since 1996-01-02` / `1999-01-22 · older bars weekly-sampled` (`apps/frontend/app/stocks/[ticker]/page.tsx:436-438`), and (c) the DB genuinely holds those deep bars (AAPL 7673 bars from 1996-01-02; NVDA 6901 from 1999-01-22). A short-history name (ARM, 701 bars, entirely < 8y) renders its complete real span correctly, so the effect only appears for long-tenured names.

Why this is a GAP and not IMPORTANT/CRITICAL (I was initially unsure between GAP and IMPORTANT):
- **Honest disclosure is fully intact** — the caption tells the user the depth exists and that older bars are weekly-sampled, so no user is misled about the data's reach. There is no fabrication and no anti-goal violation.
- **Every spec-enumerated J-10 sub-check passes**: default bounded ~5y with 1996 caption (verified — AAPL recent 1255 bars, x-axis 2021-2026), full opt-in weekly-downsampled beyond threshold (payload count reflects it), NVDA real first bar 1999-01-22 (no invented dates), post-IPO name honestly short (ARM). The "renders the deep span" phrase is satisfied at the data + disclosure + count level.
- I **could not confirm** it is a rendering defect vs. an artifact of heavy split-adjustment compressing early bars — the backend was not running during the audit (I must not launch the multi-hour warm-up), so the live returned series could not be inspected. Per the honesty rule I record it as an unconfirmed limitation, not an asserted bug.

Recommendation: on the next live-browser pass, open `/stocks/NVDA` full-history and confirm whether pre-2018 weekly bars are actually plotted; if not, widen the chart x-domain to `first_available_date`. Non-blocking.

### Test Findings

**T1 — OBSERVATION (no change needed): the QA functional table's "Actual" column is loose in several cells.**

In `reports/qa/goal-mcp-loop-iter-18-qa.md`, several cells record a page-load rather than the specific asserted value: TC-03 (backtest floor) "Backtest page loads successfully" does not confirm the 2005-02-25 minimum; TC-08/TC-18 (staleness) confirm the page loads and the symbol count, not the `stale_series` reason card or a specific stale-name exclusion; TC-17 (NVDA) "Stock detail loads" does not confirm split continuity. I independently verified the underlying facts (SPY first bar 2005-02-25 in the DB; the staleness gate + reason wiring in `universe_resolver.py`; NVDA back-adjusted first bar 1999-01-22), so the looseness masked **no** real defect — but the QA report over-states what its own steps proved.

**T2 — OBSERVATION (no change needed): one cited evidence screenshot is blank.**

`reports/qa/goal-mcp-loop-iter-18-evidence/TC-01-full-history.png` (1781 bytes, 776×432) is a solid dark frame with no content, yet the QA report cites it as J-10 full-history evidence — exactly the "blank frame is a verification gap, not evidence" hazard the spec calls out. The capability is nonetheless genuinely evidenced by the parallel, richer `UT-05-full-history-result.png` / `UT-07-full-history.png` captures (full toggle active, correct captions, all scores "Not yet proven"), so this is a hygiene miss on one artifact, not a missing verification. Two md5-duplicate pairs also exist but both are benign: `UT-05-recent-result.png == UT-05-recent-reverted.png` is the *correct* evidence that toggling back resets state, and the two AAPL full-history captures are the same real state reused for two test IDs.

---

## 3. Domain Assessment

The core domain logic is sound and, notably, honest. The load-bearing property this iteration had to preserve — that "Proven" can render only where a fresh referee PASS row exists — is enforced at a single choke point (`evidence.py` filtering strictly on `status == PASS`), and with the regenerated ledger holding zero PASS rows the entire product surface correctly collapses to "Not yet proven." The seven canonical verdicts are not hand-authored: they byte-match the referee's computed p-values and holdout edges, the Bonferroni divisors 1..7 are preserved from the historical family order (so the reset did not launder the multiple-testing budget), and several claims show the positive-in-sample → negative-out-of-sample overfit signature the deep multi-regime holdout (GFC/COVID/2021-26) was expected to expose. The retired +21.34% OOS≫in-sample yellow flag resolved exactly as pre-registered — a retired-window artifact that does not reproduce. The all-FAIL terminal state is the sanctioned-reset mechanism working as designed (goal.md: "Failed or unvalidated signals are explicitly flagged"), not a regression. The staleness gate closes a genuine correctness hole (positional `rs_vs` misalignment for names whose series ends mid-history) with a no-lookahead, config-driven threshold. Determinism (seed 20240601), no-lookahead (bars ≤ as-of), and local-first/no-network posture are all intact.

The J-06..J-09 "honestly dark badges" and J-02 "structurally un-exercisable drill" outcomes are correctly governed by goal.md's data-basis-change provision (partial / not-a-regression), consistent with the pre-registration in the spec NOTES — I concur they must NOT be scored passing→failing regressions.

---

## 4. Fixes Applied During This Audit

None. Every finding is GAP- or OBSERVATION-level; per the audit protocol these are documented, not fixed (fixing them would be scope creep, and F1 is an unconfirmed display nuance that would require the live backend to diagnose safely). No CRITICAL or IMPORTANT defect was found. The shared certification engine, both ledgers, the seed basis, and the DO-NOT-EDIT trio were left byte-untouched, as the re-dispatch hard rules require.

---

## 5. Recommended Next Step

**Proceed / close out iter-18.** The atomic basis swap, the sanctioned all-FAIL ledger reset, and the staleness gate are complete, correct, and honest; the full backend suite is green to real counts (both fix-verify logs rc=0 on disk; GRAND TOTAL 1364 passed, reviewer-confirmed faithful fixes); the shared engine is provably unmodified. Carry these two non-blocking items into iter-19 planning:

1. **F1 (display):** confirm on a live-browser pass whether the full-history chart visually plots the deep weekly-sampled bars for >8-year names (e.g. `/stocks/NVDA`); widen the chart x-domain to `first_available_date` if it does not. The honest caption already prevents user deception, so this is a refinement, not a blocker.
2. **Evidence economy:** per the pre-registration, iter-19 may propose a new-basis claim through the normal pre-build referee gate from the pre-registered candidate sets (each canonical submission tightens the divisor 8→9→…); goal.md forbids ad-hoc data-mined cohorts.
