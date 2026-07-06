# Trendora Improvement Backlog — one year of pre-registered directions

**Authored:** 2026-07-06, by Claude Fable 5, in discussion with the project owner.
**Audience:** the project owner, and the (possibly weaker) AI models that will plan and execute future work after Fable 5 is unavailable.
**Scope:** ~112 ideas in 12 tracks ≈ 250–350 goal-mode iterations — sized to sustain more than one year of evolution even when many ideas die honestly (referee FAILs, audits that gate tracks out, declined paid data).

This document is a **reference backlog**, not a spec. Nothing in it is implemented by editing product code directly. Every idea becomes real the same way all Trendora work becomes real: the owner pastes (a polished version of) the idea's journey block into `docs/goal.md`, and goal mode implements it.

---

**Contents:** §0 Read this first (operating rules, replenishment protocol, non-directions) · §1 Non-negotiable constraints · §2 Flagship 10 · §3 Twelve-month sequence · §4 The idea-card template · Tracks: **T1** Validation & certification integrity (B-101…117) · **T2** Risk & capital-preservation analytics (B-201…212) · **T3** Live-operation readiness (B-301…309) · **T4** Research depth + adaptive arc (B-401…424) · **T5** Fundamentals & events (B-501…508) · **T6** Macro & cross-asset (B-601…606) · **T7** Small/mid-cap, isolated & gated (B-701…705) · **T8** Explainability & decision UX (B-801…806) · **T9** Research-process infrastructure (B-901…907) · **T10** Gated ML (B-1001…1004) · **T11** Product hardening (B-1101…1106) · **T12** Investor workflow (B-1201…1208) · Appendices: **A** Statistical guardrails · **B** Data-source catalog · **C** goal.md interop formats · **D** Engine map & recipes. ◇ marks attrition-buffer descriptive cards (schedule anytime).

---

## 0. READ THIS FIRST (especially if you are not Fable 5)

You are working on a system a person uses to make **real-money investment decisions**. The most damaging thing you can do is not "failing to build a feature" — it is **making the system confidently wrong**: minting an overfit "Proven" badge, introducing lookahead, recomputing a number in the UI so two surfaces disagree, or letting a stale data feed render a normal-looking board. Every rule below exists to prevent one of those.

**Reading order before touching ANY idea:**
1. This section and §1 (constraints).
2. Appendix C (goal.md interop formats — journey syntax, Evidence Claim JSON, ledger routing).
3. Appendix D (map of the Trendora engine — where things plug in, which tests will break, operational notes).
4. `docs/goal.md` in full (the live goal file — anti-goals and loop mechanics are binding).
5. The one idea card you are working on, including its **Traps** and **Do NOT touch** fields.

**Operating rules:**
- **This document is the pre-registration registry.** Do not invent and test hypotheses that are not on an idea card here (or in `project-extensions/proposer-guidance.md` §4.x candidate tables) without the owner's explicit sign-off recorded in this file. Data-mined surprises are precisely what the referee exists to kill; do not feed it ad-hoc candidates.
- **One idea at a time.** Pick the card, do what it says, stop. Do not "improve" neighboring code, do not add features the card doesn't name (scope creep is a documented failure mode of weaker models — the card's Do-NOT-touch field is binding).
- **When a referee verdict is FAIL or INSUFFICIENT, the hypothesis goes to the graveyard** (Appendix A §A7). Never re-run it with tweaked selectors (different decile, different horizon, different regime slice) to get a PASS. That is p-hacking, and the whole product's honesty rests on not doing it.
- **If you are unsure whether something crosses an anti-goal, stop and ask the owner.** Unknown is a first-class answer in this project.
- **Status discipline:** when an idea is pasted into goal.md, mark its card `IN-GOAL.MD`; when its journey passes, `DONE`; when the owner rejects it, `REJECTED`; when its hypothesis dies at the referee, `GRAVEYARD (date, verdict)`. Keep the card — dead ideas are information.

**Status legend:** `PROPOSED` · `IN-GOAL.MD` · `DONE` · `REJECTED` · `GRAVEYARD`

**How an idea becomes reality (the full loop):**
1. Owner (with any model's help) picks a card — default order: Flagship 10 (§2), then by quarter (§3).
2. Discuss and polish: adjust scope, resolve the card's open choices, check the Dependencies field is satisfied.
3. If the card has an **Anti-goal boundary** flag: the owner explicitly approves the amendment text and adds it to goal.md's Anti-goals section first (or rejects the idea).
4. Copy the card's **Ready-to-paste journey block** into `docs/goal.md`: human-curated journeys go above the `<!-- AUTO:journeys -->` marker; replace `J-XX` with the next unused journey number; keep the session id in the Walkthrough line correct (`mcp-loop` today).
5. If the card carries an **Evidence Claim**, it rides inside the journey's step 1 (house style) and the post-decompose gate will referee it BEFORE code is built. A non-PASS verdict blocks the iteration — that is working as designed, not an error to route around.
6. Run goal mode (`./scripts/automation/run-goal.sh --session-id mcp-loop` or `/goal` inside Claude Code).
7. Update the card's Status here.

**Replenishment protocol (what to do when the backlog thins):** at each quarterly review (card B-1202) — or whenever a track dies — regenerate supply instead of improvising: (a) read the graveyard and the enhancement-proposals backlog for near-misses whose *preconditions changed* (new data span, new machinery); (b) walk Appendix B for data sources not yet exploited; (c) for each candidate, write a NEW card in this file using the §4 template, with an economic rationale BEFORE any data is touched; (d) get the owner's sign-off on the new cards; only then test. New cards must respect the non-directions list below.

**Explicit NON-directions (do not propose these; the owner has ruled them out):**
- No intraday/high-frequency anything — Trendora is an end-of-day system.
- No options, futures, or other derivatives; no crypto; no FX trading.
- No order placement, brokerage integration, or order simulation.
- No price targets or forecast language anywhere ("this stock will…" is banned output).
- No news/social-media sentiment scraping (unreliable free sources; revisit only if the owner asks).
- No Hong Kong market coverage; no ETF *strategy* targets (ETFs remain data inputs for sector/theme context only).
- Small/mid-caps ONLY inside the isolated Track 7 namespace — never mixed into the large-cap surfaces.

**Standing assumption:** iteration 18 of session `mcp-loop` (the 30-year / 548-name point-in-time basis swap, journeys J-10–J-14) has landed. If it has not, finish it first; several cards below lean on the deep basis and say so in Dependencies.

---

## 1. Non-negotiable constraints (bind every idea in this file)

### 1.1 The anti-goals (from `docs/goal.md:353-368` — the live copy wins if they diverge)

1. A score, ranking, or "edge" MUST NOT be presented as proven/confident unless backed by a **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked values MUST render "not yet proven". *(critical)*
2. **Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha claims; never place or simulate orders. *(critical)*
3. A journey passes ONLY if the **displayed numbers are correct** — matching the engine's computation for the same as-of date — not merely that the page renders. *(critical)*
4. **No overfit edges:** anything surfaced as "proven" must have survived the referee (sealed out-of-sample holdout + controls + multiple-testing correction). *(critical)*
5. **Determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of. *(critical)*
6. No iteration ships if its evidence-derived claims lack a passing referee verdict from the post-decompose gate. *(critical)*
7. No hard-coded credentials, API keys, or tokens in source files. *(critical)*

### 1.2 Engineering invariants (enforced by tests and gates; violating them fails the pipeline)

- **No lookahead, ever.** Read-side uses `bars_asof(D)` (≤ D); forward-side uses bars strictly > D. New data sources must model **publication lag** (a value is usable only from the date it was actually available — see the `config.macro.series` `publication_lag_days` pattern) and, where the source revises history (FRED! Stooq adjustments!), the card must say how that is handled.
- **No magic numbers.** Every threshold/window/weight comes from `config.yaml` (`test_no_magic_numbers` enforces this). House convention for new behavior: **config-gated, default OFF**, so shipping the code changes nothing until the flag is deliberately flipped.
- **Single source of truth (Data Contract).** A contract value is computed in ONE place and every surface re-reads it verbatim. Never recompute in the UI; never add a second endpoint serving the same value. The coherence auditor hard-fails this. Each card's **Canonical value** field declares what it computes where, and who reads it.
- **Immutable history.** Snapshots (`ScannerRun`/`ScannerResult`), `forward_returns`, and both evidence ledgers are append-only. Corrections happen by appending new state (e.g., lifecycle events), never by rewriting rows.
- **NA over fabrication.** Missing data renders as honest NA/`n=0`; never pad, interpolate, or fabricate bars.
- **Ledger routing:** per-iteration Evidence Claims default to the **staging** ledger (online-FDR economy). The user-facing `/evidence` page serves ONLY the canonical ledger (strict Bonferroni); promotion is a deliberate act (`"ledger":"canonical"`), typically of a staging survivor with a recorded rationale.
- **FAIL is final for that hypothesis.** Graveyard it. A revisit needs a *materially* changed precondition (new data span, genuinely different hypothesis) recorded on a new card (see B-406).
- **Test-suite discipline:** the full pytest suite takes ~10 hours on the 30-year basis. New tests MUST use small synthetic fixtures, never the full seed. Never run the full suite as a dispatcher/pump; the reviewer lane owns test verification. Frozen-golden tests (Appendix D §D4) may only be refreshed when a card explicitly sanctions it — regenerate from the new honest state; never hand-edit expected values.
- **Language bans in user-facing text:** alert/journal/report templates must not contain imperative trade verbs ("sell", "exit", "buy now", "act") — factual event statements only ("close 172.10 is below the invalidation level 175.32"). No wealth-projection language ("your portfolio would be worth…").
- **Small/mid-cap isolation (Track 7):** separate universe pool file, separate config namespace, separate surfaces behind a switcher; zero changes to large-cap defaults; shared code only where explicitly listed on the card.
- **One data-basis change per window.** Seed swaps, pool refreshes, and fundamentals ingestion each trigger pin/golden cascades; schedule them apart (weak models handle one cascade at a time, at best).

---

## 2. Flagship 10 — start here, in this order

| # | Card | One line | Why first |
|---|------|----------|-----------|
| 1 | B-101 | Execution-timing (next-open) + cost/slippage realism overlay | Every displayed edge is currently gross, close-on-signal-date — optimistic in a way no EOD human can trade. Re-price the truth before building anything on it. |
| 2 | B-301 (+B-304) | Daily preflight go/no-go + data alarms + live-vs-seed drift | A stale or silently-corrupted board is the most probable first real-money loss. One canonical readiness verdict, unmissable everywhere. |
| 3 | B-102 | Referee placebo / lookahead-tripwire battery | Calibrate the certifier's false-pass rate before minting more "Proven" badges with it. |
| 4 | B-109 | Phase-stratified re-validation of existing certified edges | Know today which edges evaporate in Bear/Correction phases — not during one. |
| 5 | B-110 | Risk-off gate efficacy study | The hard gate is the product's most action-like output and is uncertified. Certify it or caveat it honestly. |
| 6 | B-201 + B-202 | Per-stock risk-budget card + invalidation-style evidence study | Exits are the core capital-preservation decision; move them from folklore to conditional-outcome evidence. |
| 7 | B-305 | Forward-walk edge-health + claim lifecycle/demotion policy | A stale "Proven" badge is silent risk accumulation. Define active → under-review → retired, and show it. |
| 8 | B-204 | Watchlist exposure X-ray | The owner's realized risk is concentration; nothing surfaces it today. |
| 9 | B-205 | Phase-conditional drawdown depth, duration, and loss-streak expectations | Pre-commit the psychology so a normal dry spell doesn't cause capitulation at the lows. |
| 10 | B-903 (+B-901) | Certification-budget accounting + generalized pre-registration registry | Governance every later study consumes; build it before the year's statistical budget is quietly spent. |

Runner-up: **B-505 EDGAR earnings-calendar ingestion** — small, unlocks the permanently-NA `gap_climax` risk component, the B-209 earnings-gap flags, and later PEAD (B-506).

---

## 3. Twelve-month sequence (dependency-aware)

Quarters are pacing suggestions, not deadlines. Rules: capital-preservation work leads; alpha claims only after the realism overlay (B-101) exists; **one data-basis change per window**; descriptive labs (marked ◇ in the track indexes) are the anytime attrition-buffer pool — schedule one whenever a planned card is blocked.

| Window | Theme | Cards (order within window matters where arrows shown) |
|--------|-------|--------------------------------------------------------|
| **Q1** | Numbers true, board safe | B-101 → B-102 → B-103 · B-301+B-304 · B-113 (sentinel) · B-106 (CIs) · B-105→B-104 deferred to Q3 if tight · B-107 (DSR/PBO) · B-903+B-901 (governance) · B-904 (CI guard) · B-308 (backup/DR) · establish B-1202 ritual at quarter end |
| **Q2** | Risk analytics + governance + sanctioned alpha | B-109 → B-110 · B-201+B-202 · B-204 · B-205 · B-305 (lifecycle) · B-401 (quantile spreads) → B-402 (factor×regime) · B-505 (earnings calendar) · B-112 paid-feed **decision** (integration waits for Q4) · B-303 journal (if amendment approved) · B-601 (ALFRED vintage audit — precondition for all of T6) · B-1201 monthly pack · B-1205 exports · first T11 fillers (B-1101, B-1103) |
| **Q3** | Fundamentals + selective depth | B-501 (company-facts) → B-502/B-503 (quality/value, staging) · B-506 (PEAD) · B-507 (buybacks) · B-403 (sector cohorts) · B-404 (α-split) · B-413 (decay/cadence) + B-211 (turnover) · B-602 (macro enablement study) · B-604 (VIX term structure) · B-605 (credit velocity) · B-701 (small/mid-cap audit — gate) · B-801/B-802/B-804 (explainability) · B-104 (claim-correlation) + B-105 (referee sensitivity) · adaptive arc opens: B-422 (calibration) → B-421 (orthogonalization) |
| **Q4** | Expansion from surplus | B-1001 (ML charter) → B-1002 (GBT baseline) → B-1003 (meta-labeling) · B-407 (residual momentum) · B-408 (path quality) · B-409 (reversal — needs B-101) · B-411 (seasonality, staging-only) · B-420 (adaptive weights) → B-423 (shadow variants) · B-424 (cost-aware thresholds) · B-702..705 (small/mid build — ONLY if B-701 passed and owner gated it in) · B-112 integration (if approved) · B-1204 (replay trainer) · remaining T8/T11/T12 |

**Hard dependency edges (never violate):** B-101 before B-409/B-424 and before promoting any h1/h5 claim · B-601 before B-602 · B-505 before B-209/B-506 · B-701 before B-702-705 · B-1001 before B-1002/B-1003 · B-903/B-901 before opening any wide scan · B-305's lifecycle states before any "edge health" UI claims · amendment approval before B-203/B-212/B-303/B-1206.

---

## 4. The idea-card template (contract for every card below)

Each card carries these fields, in this order. P1/P2 cards carry all of them; P3 cards may compress prose but MUST still carry the safety-critical fields marked ★.

- **Header line:** `#### B-NNN · Title` then Track/Quarter/Priority/Status.
- **Difficulty** — EASY (mechanical, an existing pattern to copy) / MEDIUM (multi-module, needs care) / HARD (do not attempt without a design discussion with the owner). Plus ★ **Dominant failure mode**: the one trap most likely to sink a weaker model here — `UI-recompute` | `lookahead` | `p-hack` | `scope-creep` | `boundary` | `data-integrity`.
- **What** — the feature/study in plain words.
- **Why it protects capital** — the real-money justification.
- **Data** — existing tables, or the exact free source (URL, fields, publication lag), or paid (vendor, ~cost, what it unlocks, free fallback). Costs are "last known — verify current pricing".
- **Plugs in at** — modules/files, using Appendix D's map.
- **Config surface** — new keys and defaults (default OFF unless stated).
- **How** — numbered steps; ends with `Size: ~N iterations; split at: <first natural cut>`.
- ★ **Evidence Claim & ledger** — the draft claim JSON + routing (staging vs canonical) + how many referee trials the card is budgeted + on-FAIL behavior; or exactly `N/A — this card must not introduce proven-language anywhere`.
- ★ **Canonical value** — what new contract value (if any) is computed, in exactly one place, and the list of readers. "None — re-reads existing payloads" is the common, good answer.
- ★ **Anti-goal boundary** — `none`, or the flag **BOUNDARY** + the exact amendment sentence the owner must approve into goal.md's Anti-goals before this card may proceed.
- ★ **Tests that will break** — named frozen goldens/pins this card will trip + the sanctioned refresh procedure.
- ★ **Do NOT touch** — negative scope; binding.
- **Acceptance / DoD** — measurable bullets (what the goal-evaluator should be able to verify).
- **Ready-to-paste journey block** — fenced, in the house style (numbered Steps; 4-part Acceptance: Consistency / Correctness / Honest status & anti-goals / Walkthrough). Replace `J-XX` with the next free journey number at paste time.
- ★ **Traps** — card-specific lookahead/p-hack/recompute traps, concretely.
- **Depends on** — card IDs and/or external preconditions.

---

## Track 1 — Validation & certification integrity (make the numbers true)

Real-money principle: before adding anything new, make sure what the system already shows is *true at human-tradable terms* and that the machinery that stamps "Proven" is itself calibrated. Most of this track is Q1.

| Card | Title | Pri | Qtr |
|------|-------|-----|-----|
| B-101 | Execution-timing (next-open) + cost/slippage realism overlay | P1 | Q1 |
| B-102 | Referee placebo / lookahead-tripwire battery | P1 | Q1 |
| B-103 | As-of time-machine reproducibility audit | P1 | Q1 |
| B-104 | Claim-correlation / effective-independent-bets audit | P2 | Q3 |
| B-105 | Referee-hyperparameter sensitivity audit | P2 | Q3 |
| B-106 | Bootstrap confidence intervals on lab headline stats | P2 | Q1 |
| B-107 | Deflated Sharpe + PBO honesty panel | P2 | Q1 |
| B-108 | Signal parameter-sensitivity lab | P2 | Q2–Q3 |
| B-109 | Phase-stratified re-validation of certified edges | P1 | Q2 |
| B-110 | Risk-off gate efficacy study | P1 | Q2 |
| B-111 | Survivorship-bias quantification + universe-reconstruction audit | P1 | Q2 |
| B-112 | Survivorship-free data feed (paid) — decision then integration | P1/P2 | Q2/Q4 |
| B-113 | Data-quality sentinel: value-level anomaly detection | P1 | Q1 |
| B-114 | Point-in-time sector-membership honesty + pre-2005 control coverage | P2 | Q3 |
| B-115 | Reproducibility receipts ("re-run this proof") | P2 | Q2 |
| B-116 | Corporate-actions / adjustment-event awareness on charts | P3 | Q3 |
| B-117 | ◇ Universe composition drift dashboard | P3 | any |

---

#### B-101 · Execution-timing (next-open) + cost/slippage realism overlay
**Track:** T1 · **Quarter:** Q1 · **Priority:** P1 · **Status:** PROPOSED
**Difficulty:** MEDIUM · **Dominant failure mode:** lookahead (timing convention), UI-recompute

**What:** Today every forward return is *gross* and enters at the **close of the signal date D** (`forward_testing.forward_return`: entry = close ON D, exit = close of the h-th bar after D). A human reading the board after the close can trade the **next session's open** at the earliest, and pays spread + slippage. This card adds (a) a second entry convention `next_open` (entry = open of the first bar strictly after D), and (b) a config-driven cost model (per-side cost in basis points, optionally banded by dollar-volume), then displays gross vs realistic **side by side, clearly labeled**, on `/backtest`, the factor/combination labs, and evidence detail panels.

**Why it protects capital:** the overnight gap between close-D and next-open is systematically adverse for momentum-flavored signals (strong closes gap up). The owner is otherwise making decisions on returns nobody can capture. This single card re-prices every number in the product toward the truth; the critic pass rated the timing haircut larger than any commission assumption.

**Data:** existing — `daily_prices` already stores open/high/low/close/volume (adjusted, one consistent basis).

**Plugs in at:** `apps/backend/app/engine/forward_testing.py` (`forward_return`, `forward_excursions`, aggregation + control groups); `data_manager.run_data_job` BACKFILL mode for the new-convention rows; read surfaces via existing endpoints (`/backtest`, `/research/*`, `/evidence` detail).

**Config surface:** `walk_forward.entry_convention_variants: ["close_d","next_open"]` (compute both); `costs.enabled: false`, `costs.per_side_bps: <owner sets, suggest 5–10>`, `costs.adv_bands: []` (optional refinement). Display of the realistic variant is gated by `costs.enabled` OR a `display.realism_overlay` flag — default OFF until verified.

**How:**
1. Extend the forward-return computation with an `entry_convention` dimension; `next_open` uses the open of the first bar **strictly after** D; if that bar doesn't exist yet, the value is honest NA.
2. Backfill `next_open` rows for the whole history as an append-only variant (new rows keyed by convention; existing rows untouched).
3. Add a cost-haircut helper applied at **aggregation time** in the engine (costs are parameters, not stored data): realistic = next_open return − 2 × per_side_bps (entry+exit), config-driven.
4. Surface side-by-side "Gross (close→close)" vs "Realistic (next-open, −costs)" columns with the convention printed in the column header; evidence detail shows the realistic figure as an *informational overlay* clearly marked "not the certified statistic".
5. Document in `/methodology` (the catalog completeness assertion will require an entry — add it).
Size: ~3 iterations; split at: (1) engine convention + backfill, (2) cost model + aggregates, (3) surfaces + methodology.

**Evidence Claim & ledger:** `N/A — this card must not introduce proven-language anywhere.` It adds honesty context to existing displays. (Separately: once this lands, the owner may choose to re-certify flagship claims under the realistic convention — that would be a NEW pre-registered claim set, its own card at that time.)

**Canonical value:** realistic-return aggregates are computed in `forward_testing.py` (one place) and served through the existing payloads as additional fields; readers: backtest page, lab tables, evidence detail. No new endpoint.

**Anti-goal boundary:** none.

**Tests that will break:** aggregation-shape tests around backtest payloads (additive fields — extend, don't rewrite); any pinned expected returns in fast fixtures gain a convention dimension. Sanctioned refresh: regenerate fixture expectations from the synthetic fixture itself, never from the real seed.

**Do NOT touch:** existing `forward_returns` rows (append-only); the certified ledgers (recorded statistics stay exactly as certified — the overlay NEVER rewrites or restates a ledger row's numbers as if certified); referee defaults.

**Acceptance / DoD:**
- Both conventions visible side-by-side on `/backtest` and factor lab with explicit labels; toggling `costs.enabled` changes only the realistic column.
- Spot-check: for a known symbol/date, realistic return = (exit close ÷ next open − 1) − 2×bps, matching a hand computation.
- Evidence detail shows the overlay marked "informational — certified statistic unchanged".

**Ready-to-paste journey block:**
```markdown
- **J-XX: Every displayed edge can be read at human-tradable timing and cost**
  - Steps:
    1. Enable `walk_forward.entry_convention_variants` incl. `next_open` and set `costs.per_side_bps` in config; rebuild the affected backfill.
    2. Visit `/backtest` and `/research/factor-lab`; assert each headline forward-return figure appears twice: "Gross (close→close)" and "Realistic (next-open, − costs)", with the convention named in the header.
    3. Open a certified claim's detail on `/evidence`; assert the realistic overlay renders beside the certified statistic and is labeled "informational — not the certified statistic".
    4. Pick one (symbol, as-of, horizon) row and assert the displayed realistic value equals the engine's recomputation for the same inputs.
  - Acceptance:
    - **Consistency (single source):** both conventions are computed only in `forward_testing.py` aggregation and re-read verbatim by every surface; no UI recomputation; no new serving endpoint.
    - **Correctness:** the spot-checked realistic value byte-matches the engine computation (next-open entry, cost haircut from config).
    - **Honest status / anti-goals:** ledger rows and "Proven" badges are unchanged; the overlay adds context only; no return promise or buy/sell language; determinism + no-lookahead preserved (`next_open` uses the first bar strictly AFTER the as-of date).
    - **Walkthrough:** a `[NEW]`-flagged demo-narrator walkthrough of the gross-vs-realistic columns on `/backtest` and one evidence overlay, viewable via `demo.sh mcp-loop --session-live`.
```

**Traps:** entering at D's own open is lookahead (the signal needs D's close) — it must be the first bar AFTER D. Don't apply costs to stored rows (parameters change; stored data must not). NA when the next bar doesn't exist yet — never substitute close-D. Opens are on the same adjusted basis as closes in this feed — do not "unadjust" anything.

**Depends on:** iter-18 landed (30y basis).

---

#### B-102 · Referee placebo / lookahead-tripwire battery
**Track:** T1 · **Quarter:** Q1 · **Priority:** P1 · **Status:** PROPOSED
**Difficulty:** MEDIUM · **Dominant failure mode:** data-integrity (leaking test artifacts into the real ledgers/budget)

**What:** The referee (`referee.py`) stamps "Proven" but has never been negatively controlled. Build a battery that (a) runs **known-null synthetic factors** (seeded random cross-sections; date-shuffled versions of real factors) through `certify_edge` many times and measures the **empirical false-pass rate** against the configured α; (b) runs a **deliberately lookahead-contaminated factor** (e.g., a "factor" equal to the next 5-day return, which a broken harness would certify instantly) and asserts the sealed-holdout + control machinery rejects it or — if it passes — raises a loud tripwire that the harness leaks. Results render on a small `/research` "Referee audit" panel with run date, and a fast synthetic-fixture version runs in CI.

**Why it protects capital:** every future badge inherits its credibility from this calibration. If the certifier's false-pass rate is 15% when α says 5%, the owner is trading on noise with a certificate on it.

**Data:** existing bars; synthetic factors generated with seeds from config.

**Plugs in at:** `referee.certify_edge` (called with throwaway ledger paths); a new `engine/research.py` compute + `api/research.py` endpoint + `/research/referee-audit` page (standard lab triple); a fast CI test with a small synthetic price fixture.

**Config surface:** `research.referee_audit.n_null_trials` (suggest 200 offline / 20 CI), `seed`, `contaminated_factor_horizon` — defaults present but the panel computes only when invoked (job-style, results persisted to a small state file so the page re-reads, never recomputes).

**How:**
1. Generator: seeded null factors (per-date random permutation of a real factor's values kills any signal while preserving distribution) + the contaminated factor (value = realized forward return, the perfect crime).
2. Harness: run each through `certify_edge` against an **isolated throwaway ledger** and **without charging the real Thresholdout budget** (separate budget object).
3. Report: false-pass count/rate + binomial CI vs α; contaminated-factor verdict with expected outcome REJECT.
4. Persist a dated report artifact; panel re-reads it verbatim. CI variant: tiny fixture, few trials, asserts rate within loose bounds and tripwire = caught.
Size: ~2 iterations; split at: harness+CI test first, panel second.

**Evidence Claim & ledger:** `N/A — this card must not introduce proven-language anywhere.` It certifies nothing; it audits the certifier.

**Canonical value:** the audit report artifact (one state file) computed by the job; the panel is its only reader.

**Anti-goal boundary:** none.

**Tests that will break:** none existing; adds new fast tests. Do not let the CI variant import the full seed.

**Do NOT touch:** the real `certified-claims.jsonl` / `staging-ledger.jsonl`; the real Thresholdout budget accounting; referee default constants (auditing ≠ tuning).

**Acceptance / DoD:** empirical false-pass rate reported with CI and compared to α; contaminated factor caught (or tripwire prominently red); CI test green in seconds; panel shows run date and parameters.

**Ready-to-paste journey block:**
```markdown
- **J-XX: The certifier itself is calibrated (placebo + tripwire audit)**
  - Steps:
    1. Run the referee-audit job (config-seeded null factors + one lookahead-contaminated factor) against an isolated throwaway ledger.
    2. Visit `/research/referee-audit`; assert it shows: number of null trials, empirical false-pass rate with a confidence interval, the configured α, and the contaminated-factor verdict labeled "expected: rejected".
    3. Assert the page states the run date and that results come from the persisted audit artifact.
    4. Assert `/evidence` is unchanged (no new claims appeared from the audit).
  - Acceptance:
    - **Consistency (single source):** the panel re-reads the persisted audit artifact verbatim; nothing is recomputed in the UI; the real ledgers and Thresholdout budget are untouched (byte-identical before/after).
    - **Correctness:** the displayed false-pass rate equals the artifact's; re-running with the same seed reproduces it exactly.
    - **Honest status / anti-goals:** no proven-language is introduced; if the contaminated factor is NOT caught, the panel renders a prominent failure state (never hides it); determinism preserved via config seeds.
    - **Walkthrough:** a `[NEW]`-flagged demo-narrator walkthrough of the referee-audit panel, viewable via `demo.sh mcp-loop --session-live`.
```

**Traps:** writing audit rows into the real ledgers (instantly poisons the Bonferroni divisor); charging the real reusable-holdout budget; using unseeded randomness (breaks determinism); tuning referee constants until the audit "looks right" (the audit reports, the owner decides).

**Depends on:** none.

---

#### B-103 · As-of time-machine reproducibility audit
**Track:** T1 · **Quarter:** Q1 · **Priority:** P1 · **Status:** PROPOSED
**Difficulty:** EASY–MEDIUM · **Dominant failure mode:** data-integrity

**What:** a recurring job that samples K historical as-of dates, recomputes the full snapshot from `bars_asof(D)` with the current engine, and **byte-compares** against the stored immutable `ScannerResult.record_json`. Report per-date: identical / differs (with field-level diff summary) / stored-under-different-engine-version. Turns "deterministic, no-lookahead" from a design claim into a continuously verified property.

**Why it protects capital:** silent nondeterminism or an unnoticed engine-behavior change quietly invalidates every backtest and certified claim built on stored snapshots.

**Data:** existing (`daily_prices`, stored `scanner_runs`/`scanner_results`).

**Plugs in at:** a new `data_manager` job mode (pattern exists: FETCH/BACKFILL/rebuild) writing a dated report artifact; surfaced on `/data` and feeding the B-301 preflight verdict.

**Config surface:** `data_quality.time_machine.sample_dates` (K, default e.g. 8), `seed`, `enabled: false`.

**How:** (1) job samples dates deterministically (seeded) across eras incl. the bootstrap crisis dates; (2) recompute via the same `scoring.score_stocks` path with bars ≤ D; (3) compare canonical JSON (stable key order) and record a diff report; (4) classify diffs using the engine-version stamp when B-306 lands (before that, any diff = red). Size: ~1–2 iterations.

**Evidence Claim & ledger:** `N/A — this card must not introduce proven-language anywhere.`
**Canonical value:** the audit report artifact; readers: `/data` panel, B-301 preflight.
**Anti-goal boundary:** none.
**Tests that will break:** none; add a fast synthetic-fixture test (store → recompute → identical).
**Do NOT touch:** stored snapshots (read-only audit; NEVER "fix" a stored row to match).

**Acceptance / DoD:** report lists K dates with verdicts; a deliberate synthetic perturbation in the test fixture is detected; `/data` shows last-audit date + result.

**Ready-to-paste journey block:**
```markdown
- **J-XX: Stored history reproduces byte-for-byte (time-machine audit)**
  - Steps:
    1. Run the time-machine audit job over the config-seeded sample of historical as-of dates.
    2. Visit `/data`; assert an audit section shows: dates checked, per-date verdict (identical / differs / different-engine-version), and the run timestamp.
    3. Assert the overall verdict feeds the readiness state (a "differs" verdict must not leave readiness fully green).
  - Acceptance:
    - **Consistency (single source):** the panel re-reads the persisted audit artifact; the audit reads stored snapshots and bars read-only.
    - **Correctness:** for an "identical" date, an independent recompute of one stock's record matches the stored record exactly.
    - **Honest status / anti-goals:** diffs are surfaced, never suppressed; stored history is never modified; determinism + no-lookahead preserved (recompute uses bars ≤ D only).
    - **Walkthrough:** a `[NEW]`-flagged demo-narrator walkthrough of the audit section on `/data`, viewable via `demo.sh mcp-loop --session-live`.
```

**Traps:** recomputing with bars beyond D (lookahead in the auditor itself); comparing floats with naive string equality — canonicalize exactly the way `record_json` was produced; "repairing" stored rows (immutable history).
**Depends on:** B-306 (engine-version stamps) improves classification but is not required to start.

---

#### B-104 · Claim-correlation / effective-independent-bets audit
**Track:** T1 · **Quarter:** Q3 · **Priority:** P2 · **Status:** PROPOSED
**Difficulty:** MEDIUM · **Dominant failure mode:** UI-recompute

**What:** for every certified (and staging-surviving) cohort, extract its per-date excess-return series over the shared window; compute the pairwise correlation matrix and an **effective number of independent bets** (ENB = (Σλ)²/Σλ² over the correlation matrix's eigenvalues). Display on `/evidence`: "5 certified claims ≈ 2.1 independent bets", plus the matrix heatmap.

**Why it protects capital:** five momentum-flavored certificates feel like five reasons to act; if they are one bet in five costumes, the owner is unknowingly concentrated. This is a prop-desk staple the product lacks.

**Data:** existing (per-date cohort edges are already produced by the forward-testing/referee machinery).
**Plugs in at:** `engine/research.py` compute + endpoint + a section on `/evidence` (or a lab page linked from it); reuses stored `forward_returns`.
**Config surface:** `evidence.correlation_audit.min_overlap_dates` (floor for honest pairs; below it render NA).

**How:** (1) reconstruct per-date excess series per claim from stored data (same selectors the referee used — reuse its cohort extraction, do not re-implement); (2) correlation on overlapping dates only, NA under the floor; (3) ENB + heatmap payload persisted; UI re-reads. Size: ~1–2 iterations.

**Evidence Claim & ledger:** `N/A — this card must not introduce proven-language anywhere.`
**Canonical value:** the correlation/ENB payload computed in the engine; readers: evidence page.
**Anti-goal boundary:** none.
**Tests that will break:** none; fast fixture test with two constructed cohorts (identical → ENB 1; orthogonal → ENB 2).
**Do NOT touch:** ledgers; referee cohort-extraction semantics (reuse, don't fork).

**Acceptance / DoD:** ENB and matrix render with n-overlap labels; constructed-fixture sanity passes; insufficient overlap renders NA, not 0.

**Ready-to-paste journey block:**
```markdown
- **J-XX: Certified claims disclose how independent they really are**
  - Steps:
    1. Visit `/evidence`; locate the claim-correlation section.
    2. Assert it shows a pairwise correlation view over the certified claims' per-date excess series and a headline "effective independent bets" figure with the overlap window stated.
    3. Assert pairs below the config overlap floor render an honest NA.
  - Acceptance:
    - **Consistency (single source):** the section re-reads one engine-computed payload; per-date series come from the same cohort extraction the referee uses.
    - **Correctness:** the displayed ENB equals the engine value for the same matrix; a spot-checked pair correlation matches an offline computation.
    - **Honest status / anti-goals:** no proven-language added or removed; low-overlap honesty preserved (NA, labeled).
    - **Walkthrough:** a `[NEW]`-flagged demo-narrator walkthrough of the correlation section, viewable via `demo.sh mcp-loop --session-live`.
```

**Traps:** re-implementing cohort extraction slightly differently from the referee (two sources of truth); correlating over non-overlapping windows; presenting ENB as advice ("diversify!") — it is a disclosure.
**Depends on:** none (better after B-101 so realistic series exist too).

---

#### B-105 · Referee-hyperparameter sensitivity audit
**Track:** T1 · **Quarter:** Q3 · **Priority:** P2 · **Status:** PROPOSED
**Difficulty:** MEDIUM · **Dominant failure mode:** p-hack (the audit must never become tuning)

**What:** sweep the referee's own knobs — holdout fraction (e.g., 0.20→0.40), embargo length, block length, Thresholdout noise — and re-run the verdicts of the EXISTING canonical claims under each setting (isolated ledgers, no budget charge). Output a verdict-stability table: which PASSes are robust to the referee's arbitrary choices, which flip.

**Why it protects capital:** a claim that is PASS only at exactly holdout=0.30 is a coincidence with a certificate. The owner should see which certificates are knife-edge.

**Data / plugs in at:** existing ledgers (parameters recorded per row) + `referee.py` invoked with overrides; results as a section of the B-102 referee-audit panel.
**Config surface:** `research.referee_audit.sweep` grid (small, fixed — a pre-registered grid, not a search).

**How:** (1) read each canonical claim's recorded selectors; (2) re-run `certify_edge` across the fixed grid with throwaway ledgers/budget; (3) persist stability table; panel re-reads. Size: ~1–2 iterations.

**Evidence Claim & ledger:** `N/A — this card must not introduce proven-language anywhere.`
**Canonical value:** the stability-table artifact; reader: referee-audit panel.
**Anti-goal boundary:** none.
**Tests that will break:** none; fast fixture test (a strong synthetic edge stays PASS across the grid; a marginal one flips — assert the table records both).
**Do NOT touch:** real ledgers/budget; referee defaults (report, don't retune); the grid once registered (changing it after seeing results is p-hacking the audit).

**Acceptance / DoD:** stability table per canonical claim across the registered grid; flips visually prominent; owner-facing note auto-added to a flipped claim's evidence detail ("verdict sensitive to referee settings — see audit").

**Ready-to-paste journey block:**
```markdown
- **J-XX: Certified verdicts disclose their sensitivity to the referee's own settings**
  - Steps:
    1. Run the referee sensitivity sweep over the pre-registered grid against isolated ledgers.
    2. Visit `/research/referee-audit`; assert a stability table lists each canonical claim × grid setting with its re-run verdict.
    3. For any claim whose verdict flips within the grid, open its `/evidence` detail and assert a visible sensitivity note links to the audit.
  - Acceptance:
    - **Consistency (single source):** the table re-reads the persisted sweep artifact; evidence detail reads the same artifact for its note.
    - **Correctness:** one grid cell re-verified independently matches the table.
    - **Honest status / anti-goals:** canonical verdicts/badges unchanged by the audit; flips disclosed, never hidden; real budget untouched.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of the stability table and one sensitivity note, viewable via `demo.sh mcp-loop --session-live`.
```

**Traps:** the deadly one — using the sweep to pick friendlier referee settings for future claims. The grid is fixed, the defaults stay, the output is disclosure. Also: budget/ledger isolation, as in B-102.
**Depends on:** B-102 (shares the audit harness).

---

#### B-106 · Bootstrap confidence intervals on lab headline stats
**Track:** T1 · **Quarter:** Q1 · **Priority:** P2 · **Status:** PROPOSED
**Difficulty:** EASY–MEDIUM · **Dominant failure mode:** UI-recompute (a second, divergent bootstrap)

**What:** lab tables show bare means (mean forward return per decile/cohort). Add block-bootstrap confidence intervals to headline stats — computed by extending the **referee's existing moving-block bootstrap module** (single owner of bootstrap logic) with a generic CI helper.

**Why it protects capital:** a +2.1% mean over n=34 dates and a +2.1% over n=400 read identically today. CIs make thin evidence look thin.

**Data / plugs in at:** existing stored series; `referee.py`'s bootstrap internals refactored into a small shared helper (same module or a sibling it owns); lab computes in `engine/research.py`, pages re-read.
**Config surface:** `research.ci.n_resamples` (e.g., 1000 offline), `ci_level: 0.90`; below `walk_forward.min_sample` render NA (no CI on vapor).

**How:** (1) extract/reuse the block-bootstrap core (identical block-length inference as the referee); (2) add CI computation to lab payloads; (3) render as ± bands/whiskers with n printed. Size: ~1–2 iterations.

**Evidence Claim & ledger:** `N/A — this card must not introduce proven-language anywhere.`
**Canonical value:** CI fields inside existing lab payloads (computed once, engine-side).
**Anti-goal boundary:** none.
**Tests that will break:** lab payload-shape tests (additive fields). Fixture test: constructed series with known variance → CI within tolerance; n<floor → NA.
**Do NOT touch:** referee verdict logic; do not write a *second* bootstrap implementation anywhere.

**Acceptance / DoD:** every headline mean in factor/combination/event-study labs carries a CI band + n, or an honest NA under the floor; one spot-checked CI matches an offline run with the same seed.

**Ready-to-paste journey block:**
```markdown
- **J-XX: Lab headline statistics carry honest uncertainty bands**
  - Steps:
    1. Visit `/research/factor-lab` for any factor; assert each decile's mean forward return renders with a confidence interval and its sample size.
    2. Find a cohort with n below the configured floor; assert it renders NA for the CI (never a bare mean presented as solid).
    3. Assert the event-study lab's headline stats carry the same treatment.
  - Acceptance:
    - **Consistency (single source):** CIs are computed in the engine's single bootstrap module (the referee's) and re-read verbatim; no UI or second-module computation.
    - **Correctness:** a spot-checked CI reproduces offline with the same seed and block length.
    - **Honest status / anti-goals:** thin samples render NA; no proven-language changes; determinism via config seed.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of CI bands in the factor lab, viewable via `demo.sh mcp-loop --session-live`.
```

**Traps:** an i.i.d. bootstrap on autocorrelated overlapping-horizon returns (must be the block bootstrap with the referee's block-length rule); CIs on n<30; recomputing in the frontend.
**Depends on:** none.

---

#### B-107 · Deflated Sharpe + PBO honesty panel
**Track:** T1 · **Quarter:** Q1 · **Priority:** P2 · **Status:** PROPOSED
**Difficulty:** MEDIUM · **Dominant failure mode:** scope-creep (these are diagnostics, not a new certification bar)

**What:** for each canonical claim, compute two literature-standard overfitting diagnostics and show them on its evidence detail: **Deflated Sharpe Ratio** (Bailey & López de Prado — deflates the observed Sharpe by the number of trials, from the ledger's own trial accounting, and non-normality) and **PBO** (probability of backtest overfitting via combinatorially symmetric cross-validation over the claim's per-date series). Label clearly: "diagnostics — the referee verdict remains the certification bar."

**Why it protects capital:** DSR/PBO are the standard external yardsticks a skeptical quant would apply; showing them pre-empts self-deception and makes the evidence page audit-grade.

**Data / plugs in at:** ledger rows (n_trials) + per-date series (same extraction as B-104); compute in `engine/research.py`; evidence detail re-reads.
**Config surface:** `evidence.diagnostics.pbo_partitions` (e.g., S=16), `enabled`.
**How:** (1) DSR from recorded Sharpe, trials, skew/kurtosis of the series; (2) PBO via CSCV partitions of dates; (3) persist per-claim diagnostics; render with plain-language one-liners ("DSR>0: the Sharpe survives selection-bias deflation"). Size: ~2 iterations.

**Evidence Claim & ledger:** `N/A — this card must not introduce proven-language anywhere.`
**Canonical value:** per-claim diagnostics payload (engine-computed); reader: evidence detail.
**Anti-goal boundary:** none.
**Tests that will break:** none; fixture tests with constructed series (pure noise → PBO ≈ 0.5, DSR ≤ 0; strong stable signal → PBO low, DSR > 0).
**Do NOT touch:** verdict logic; badges (a bad DSR does not un-prove a claim — it informs the owner and the B-305 lifecycle discussion).

**Acceptance / DoD:** every canonical claim's detail shows DSR + PBO with n and the diagnostics disclaimer; fixture sanity passes.

**Ready-to-paste journey block:**
```markdown
- **J-XX: Every certified claim carries external overfitting diagnostics (DSR + PBO)**
  - Steps:
    1. Visit `/evidence` and open each canonical claim's detail.
    2. Assert each shows a Deflated Sharpe Ratio and a Probability-of-Backtest-Overfitting figure, each with a one-line plain-language reading and the computation's n.
    3. Assert the panel states these are diagnostics and the referee verdict remains the certification bar.
  - Acceptance:
    - **Consistency (single source):** diagnostics are computed once in the engine from the same per-date series/trial counts the ledger records; the UI re-reads them.
    - **Correctness:** one claim's DSR reproduces offline from the recorded inputs.
    - **Honest status / anti-goals:** badges unchanged; adverse diagnostics are displayed, never suppressed; no forecast language.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of one claim's diagnostics, viewable via `demo.sh mcp-loop --session-live`.
```

**Traps:** using a trials count other than the ledger's own accounting (understates deflation); PBO partitions chosen after seeing results (fix S in config first); letting diagnostics silently gate anything (owner-facing information only, by design).
**Depends on:** B-104's series extraction helper (shareable).

---

#### B-108 · Signal parameter-sensitivity lab
**Track:** T1 · **Quarter:** Q2–Q3 · **Priority:** P2 · **Status:** PROPOSED
**Difficulty:** MEDIUM · **Dominant failure mode:** p-hack (a sensitivity scan is one step from a grid search)

**What:** perturb the *product's own* config parameters (pattern thresholds, `decision_rules` cutoffs, phase edges, regime weights) by ±10–25% on a bounded evaluation window and report how downstream conclusions move (setup counts, cohort stats, phase timelines). A "knife-edge report": which of the product's opinions depend delicately on an arbitrary constant.

**Why it protects capital:** decision rules with cliff behavior (Actionable at L≥80 but not 79) are silent fragility; the owner should know which displayed opinions are robust.

**Data / plugs in at:** stored bars/snapshots on a bounded window; new lab triple (`/research/sensitivity`); read-only recomputation in a sandbox path (never writes snapshots).
**Config surface:** `research.sensitivity.param_grid` (FIXED, pre-registered list of parameters and ±steps), `window_years` (bound compute).
**How:** (1) registered grid only; (2) sandboxed recompute per setting on the bounded window; (3) tornado-style summary per parameter; persist artifact; page re-reads. Size: ~2 iterations.

**Evidence Claim & ledger:** `N/A — this card must not introduce proven-language anywhere.`
**Canonical value:** sensitivity artifact; reader: the lab page.
**Anti-goal boundary:** none.
**Tests that will break:** none; fixture test that a deliberately cliff-shaped rule is flagged.
**Do NOT touch:** live config values (the lab NEVER writes config); stored snapshots; and do not extend the grid ad hoc after results — additions are new pre-registrations.

**Acceptance / DoD:** report ranks parameters by conclusion-fragility with plain-language notes; zero writes outside the artifact.

**Ready-to-paste journey block:**
```markdown
- **J-XX: The product discloses which of its opinions are knife-edge on a config constant**
  - Steps:
    1. Run the sensitivity job over the pre-registered parameter grid on the bounded window.
    2. Visit `/research/sensitivity`; assert a per-parameter summary shows how setup counts and headline cohort stats move under ±perturbation, ranked by fragility.
    3. Assert the page names the evaluated window and grid, and that live config is unchanged.
  - Acceptance:
    - **Consistency (single source):** the page re-reads the persisted artifact; perturbed recomputes run in a sandbox that writes nothing else.
    - **Correctness:** one perturbed cell re-verified independently matches the artifact.
    - **Honest status / anti-goals:** no proven-language; no auto-tuning (config untouched); determinism (fixed grid, seeded sampling if any).
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of the fragility ranking, viewable via `demo.sh mcp-loop --session-live`.
```

**Traps:** the lab must never become an optimizer — no "best value" column, no auto-apply; unbounded windows (10h-class compute); leaking sandbox snapshots into real tables.
**Depends on:** none.

---

#### B-109 · Phase-stratified re-validation of certified edges
**Track:** T1 · **Quarter:** Q2 · **Priority:** P1 · **Status:** PROPOSED
**Difficulty:** MEDIUM · **Dominant failure mode:** UI-recompute / thin-sample dishonesty

**What:** for each canonical claim, decompose its holdout and forward-walk evidence **by market phase** (Expansion/Pullback/Correction/Bear/Recovery, from the existing `market_phase` engine) and attach the composition to the claim: "certified on a window that was 61% Expansion; Bear-phase evidence: n=4 (insufficient)". Reuses the existing `regime-phase-factor` machinery — this is a *re-slicing of existing certified evidence*, not new claims.

**Why it protects capital:** the user's earlier "market phases" direction, pointed at the sharpest question: the current claims were certified on a mostly-benign window; the owner must see how much Bear-phase evidence actually backs each badge BEFORE the next bear market tests it live.

**Data / plugs in at:** existing ledgers + `forward_returns` + phase timeline; compute in `engine/research.py` reusing the phase-conditioning paths; evidence detail + badges gain a composition line.
**Config surface:** `evidence.phase_breakdown.min_n_per_phase` (honesty floor).
**How:** (1) reconstruct claim per-date series (B-104 helper); (2) join to the causal phase timeline; (3) per-phase edge, n, CI (B-106 helper); (4) persist; evidence detail re-reads; a compact composition ribbon appears near the badge. Size: ~2 iterations.

**Evidence Claim & ledger:** `N/A` — no new claims; this annotates existing ones. (If a phase-conditioned cohort later deserves its OWN certification, that is B-405, pre-registered.)
**Canonical value:** per-claim phase-composition payload; readers: evidence detail, badge ribbon.
**Anti-goal boundary:** none.
**Tests that will break:** evidence payload-shape tests (additive). Fixture: constructed claim spanning two synthetic phases → correct split.
**Do NOT touch:** verdicts/badges (composition is context, not a re-verdict); phase-engine logic.

**Acceptance / DoD:** every canonical claim shows phase composition with per-phase n and honest "insufficient" markers; the two phases with n below floor render NA.

**Ready-to-paste journey block:**
```markdown
- **J-XX: Every certified edge discloses its market-phase evidence composition**
  - Steps:
    1. Visit `/evidence`; open each canonical claim's detail.
    2. Assert a phase-composition section shows, per market phase: the share of the certification window, the claim's edge in that phase, and the per-phase sample size — with phases under the configured floor rendered "insufficient (n=…)".
    3. Assert the factor-lab badge for the claim links to or displays the same composition summary.
  - Acceptance:
    - **Consistency (single source):** the composition payload is computed once in the engine (reusing the referee's cohort extraction and the causal phase timeline) and re-read by both surfaces.
    - **Correctness:** one phase cell re-verified offline matches; the phase timeline used is the stored causal one.
    - **Honest status / anti-goals:** verdicts unchanged; thin phases say "insufficient", never a bare number; no forecast language ("this will work in a bear market" is banned — only historical composition is stated).
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of one claim's phase composition, viewable via `demo.sh mcp-loop --session-live`.
```

**Traps:** using a *retrospective* phase labeling instead of the stored causal timeline (lookahead); presenting a favorable phase slice as a new "Proven in Expansion!" badge (that's a new claim — needs B-405's pre-registration); dropping insufficient phases from the display (they are the point).
**Depends on:** B-104 helper; phase timeline (exists).

---

#### B-110 · Risk-off gate efficacy study
**Track:** T1 · **Quarter:** Q2 · **Priority:** P1 · **Status:** PROPOSED
**Difficulty:** MEDIUM · **Dominant failure mode:** p-hack (this is a single pre-registered policy claim; keep it that way)

**What:** the regime engine's Risk-off label **hard-gates every stock to `Risk-off-watchlist`** — the closest thing the product has to telling the owner "stand down". It has never been certified. Event-study: at each historical entry into Risk-off, compare forward outcomes (1/5/20/60d, MAE/max-drawdown) of the names that WOULD have been Actionable but were gated, vs their unconditional behavior and vs SPY — i.e., did the gate historically avoid damage, and at what opportunity cost? One pre-registered claim through the referee (staging first): "the risk-off gate's suppressed cohort underperforms its own unconditional baseline over h=20" (direction: the gate helps).

**Why it protects capital:** if the gate is protective, the owner gains justified confidence to respect it in a drawdown; if it isn't, the owner learns the product's most action-like output is decoration. Either answer changes real behavior.

**Data / plugs in at:** stored snapshots (setup statuses + regime labels per as-of), `forward_returns`; event-study lab machinery (`kind: "event-study"` cohorts exist); referee via the standard gate.
**Config surface:** none new beyond a pre-registered candidate row (Appendix references; also mirror into `proposer-guidance.md` §4.x per house convention).
**How:** (1) enumerate historical Risk-off entry dates from the stored regime series; (2) build the suppressed cohort (names whose scores met Actionable thresholds but were gated); (3) event-study stats + controls; (4) ONE claim, pre-registered, staging ledger; (5) surface on `/methodology` (gate description) + regime lab with the evidence badge reflecting the verdict, including a FAIL displayed honestly ("gate effect not certified"). Size: ~2 iterations.

**Evidence Claim & ledger:** staging; 1 trial; on FAIL → graveyard + the methodology page states the gate is a design choice without certified protective effect (that honesty IS the deliverable either way).
```json
{"kind": "event-study", "subject": "risk_off_gate_suppressed", "setup": "would_be_actionable", "horizon": 20, "direction": "negative"}
```
(`direction: negative` = the suppressed cohort's forward return is adversely different from baseline — i.e., gating helped. Exact selector names to match the event-study lab's existing cohort grammar; keep the hypothesis EXACTLY this one.)

**Canonical value:** the event-study cohort stats (engine lab payload) + the ledger row; readers: methodology page, regime lab.
**Anti-goal boundary:** none (describing a gate's historical effect is decision-quality; imperative "obey the gate" language stays banned).
**Tests that will break:** none expected; staging-ledger routing test covers the new row shape only if selectors extend the grammar — if a new `subject` kind is needed, extend `drill_samples` parsing + its tests (fixture-based).
**Do NOT touch:** the gate's live behavior (no threshold changes here — that would be B-108/adaptive-arc territory); canonical ledger (staging only, promotion is the owner's later call).

**Acceptance / DoD:** entry dates enumerated deterministically; cohort construction documented on the lab page; one referee verdict recorded; both PASS and FAIL render honestly where the gate is described.

**Ready-to-paste journey block:**
```markdown
- **J-XX: The Risk-off hard gate carries certified (or honestly absent) evidence of its protective effect**
  - Steps:
    1. The iteration carries a machine-readable `## Evidence Claim` for the risk-off suppressed cohort —
       `{"kind":"event-study","subject":"risk_off_gate_suppressed","setup":"would_be_actionable","horizon":20,"direction":"negative"}` —
       routed to the staging ledger, so the post-decompose gate referees it BEFORE any code is built; a non-PASS verdict blocks the iteration (and if the owner instead wants the honest-FAIL surfaced, that is a separate no-claim iteration).
    2. Visit `/research/event-study` (or the regime lab) and locate the risk-off gate study; assert it shows the suppressed cohort's forward outcomes vs its unconditional baseline and vs SPY, with sample sizes and the entry-date list.
    3. Visit `/methodology` at the Risk-off gate description; assert it now carries the evidence status for the gate's protective effect ("Proven" only if a PASS entry backs it; otherwise "Not yet proven").
  - Acceptance:
    - **Consistency (single source):** the study payload is computed once in the research engine; the methodology badge resolves through the existing evidence-status path; no new serving endpoint.
    - **Correctness:** displayed cohort stats byte-match the engine computation; entry dates derive from the stored causal regime series.
    - **Honest status / anti-goals:** a FAIL/INSUFFICIENT verdict renders as "Not yet proven" — never hidden; no imperative language ("obey the gate") anywhere; determinism + no-lookahead preserved (cohort formed from information ≤ each entry date).
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of the gate study and its methodology badge, viewable via `demo.sh mcp-loop --session-live`.
```

**Traps:** defining "would-be Actionable" using any post-gate information (must be recomputed from the same as-of snapshot fields, ≤ D); trying alternative horizons/subjects after a FAIL (graveyard means graveyard); overlapping episodes double-counting dates (use the episode machinery's non-overlap conventions).
**Depends on:** none (B-101 makes the numbers more honest but is not blocking).

---

#### B-111 · Survivorship-bias quantification + universe-reconstruction audit
**Track:** T1 · **Quarter:** Q2 · **Priority:** P1 · **Status:** PROPOSED
**Difficulty:** MEDIUM · **Dominant failure mode:** data-integrity (a community membership list is imperfect — disclose, don't over-trust)

**What:** the survivorship label exists (`SURVIVORSHIP_BIAS_LABEL`, `pool_survivorship()`); the **number** does not. Two deliverables: (a) **reconstruction audit** — compare the resolver's per-date membership against a free historical S&P 500 constituents list (community-maintained GitHub datasets exist; verify license) to measure what fraction of true point-in-time members are absent from our pool at 1996/2000/2008/2015; (b) **bias bounding** — estimate the optimism this induces per horizon (era-sliced cohort comparisons + a synthetic-attrition experiment that randomly removes names matching historical delisting rates), and print the resulting band on `/backtest` and `/methodology` next to the existing label ("edges shown are upper bounds; estimated survivorship inflation ≈ X–Y%/yr for this era").

**Why it protects capital:** "upper bound" is currently a vibe; this makes it a magnitude the owner can mentally subtract — and it directly informs whether B-112's paid feed is worth the money.

**Data:** free — e.g., the "S&P 500 Historical Components & Changes" community CSV (GitHub, license-check; imperfect — the audit reports agreement, not gospel) + existing pool/bars.
**Plugs in at:** `universe_resolver` (read-only comparison), `forward_testing.py` disclosure strings, a `/research` or `/data` audit section.
**Config surface:** `data_quality.survivorship_audit.reference_list_path`, era cut dates (fixed list).
**How:** (1) ingest reference membership list as a data file with provenance note; (2) per-era coverage stats (members-in-pool / true members); (3) synthetic-attrition experiment (seeded); (4) band computation + disclosure strings; (5) surface. Size: ~2 iterations.

**Evidence Claim & ledger:** `N/A — this card must not introduce proven-language anywhere.`
**Canonical value:** the audit artifact (coverage + band); readers: backtest page, methodology, data page.
**Anti-goal boundary:** none.
**Tests that will break:** none; fixture tests for the coverage math.
**Do NOT touch:** the resolver's gates (measurement, not modification); never fabricate bars for dead names.

**Acceptance / DoD:** per-era coverage table + bias band displayed with method notes and the reference list's provenance/limitations; label text extended, not replaced.

**Ready-to-paste journey block:**
```markdown
- **J-XX: Survivorship bias is quantified — coverage per era and an estimated optimism band**
  - Steps:
    1. Visit the survivorship audit section (Data or Research); assert a per-era table shows the fraction of true index members present in our pool at the registered era dates, citing the reference list and its limitations.
    2. Visit `/backtest`; assert the survivorship disclosure now includes the estimated optimism band with a link to the method.
    3. Assert the synthetic-attrition method page states its seed and assumptions.
  - Acceptance:
    - **Consistency (single source):** all surfaces re-read the one audit artifact.
    - **Correctness:** one era's coverage figure re-verified by hand against the reference CSV matches.
    - **Honest status / anti-goals:** the band is presented as an estimate with method caveats; no bar fabrication; the existing upper-bound label is strengthened, never softened.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of the coverage table and the backtest disclosure, viewable via `demo.sh mcp-loop --session-live`.
```

**Traps:** treating the community list as ground truth (it has errors — report agreement rates, keep the language calibrated); letting the synthetic-attrition experiment quietly become a "corrected returns" display (we disclose a band; we do NOT adjust displayed returns).
**Depends on:** none. Feeds the B-112 decision.

---

#### B-112 · Survivorship-free data feed (paid) — decision, then integration
**Track:** T1 · **Quarter:** decision Q2, integration Q4 · **Priority:** P1 (decision) / P2 (build) · **Status:** PROPOSED
**Difficulty:** HARD (integration) · **Dominant failure mode:** data-integrity (vendor splice, adjustment-basis mixing)

**What:** goal.md itself names this the out-of-scope follow-on (`docs/goal.md:521-523`): a true point-in-time feed — historical index membership + **delisted names' prices** — via a paid vendor. Phase 1 (Q2, ~half an iteration + owner discussion): a written decision memo comparing vendors with B-111's measured bias as the benefit side. Phase 2 (Q4, only if approved): staged integration exactly like the iter-16→18 basis swap — new seed directory, validation report, atomic swap, **sanctioned ledger reset** (the goal.md §"Data-basis change" provision), membership timeline from vendor data.

**Why it protects capital:** kills the product's #1 disclosed bias at the root instead of bounding it. Every certified edge after the swap is an honest estimate, not an upper bound.

**Data (verify current pricing; last known mid-2025):** **Norgate Data** US Platinum ≈ US$50/mo — delisted stocks + historical index constituents, clean survivorship-free design, prices only. **Sharadar** (Nasdaq Data Link) Core US bundle ≈ US$60/mo — SEP prices incl. delisted + **SF1 fundamentals** (strong synergy with Track 5) + TICKERS metadata. **EODHD** ≈ US$20–80/mo tiers — cheaper, coverage of delisted/PIT less rigorous. Recommendation seed for the memo: **Sharadar if Track 5 fundamentals are wanted anyway (one vendor, two tracks); Norgate if prices/constituents only.** Free fallback: stay on Stooq + B-111's disclosed band.

**Plugs in at:** `scripts/ingest_seed.py` provider abstraction (a new provider adapter), `data/seed-*` staging directory pattern, `universe_resolver` (vendor membership replaces the static pool for deep history), `seed_loader`, the ledger-reset provision + frozen-golden refresh procedure.
**Config surface:** `provider: "<vendor>"` variant; membership-source key; everything default-off until the atomic swap iteration.
**How (phase 2 sketch, mirror iter-16→18):** ingest to staging dir → validation report (schema, adjustment basis, spot-check known splits, coverage vs current seed) → membership timeline build → atomic swap + DB rebuild → sanctioned ledger reset + re-certification of surviving claims → pins/goldens refresh → disclosure updates (`pool_survivorship` flips to `point_in_time_feed_available: true`). Size: decision 0.5; integration ~5 iterations; split at each arrow.

**Evidence Claim & ledger:** `N/A` for the swap itself; the post-swap **re-certification sweep** re-runs existing claims under the reset provision (that sweep is sanctioned by goal.md's basis-change clause, not new hypothesis mining).
**Canonical value:** none new (same contract values, truer inputs).
**Anti-goal boundary:** none — but **paid-service approval is required by CLAUDE.md**: the decision memo + explicit owner sign-off IS that approval gate.
**Tests that will break:** the full pin/golden cascade (`test_seed_ingest.py` window/count pins, `test_evidence.py` frozen goldens, staging routing, bar-cache offsets) — the iter-18 playbook is the sanctioned refresh procedure; schedule NOTHING else data-basis-shaped in the same window.
**Do NOT touch:** never splice vendor history onto Stooq CSVs per-symbol (one adjustment basis end-to-end per name — mixed-vendor seams are the named cardinal sin); never fabricate data for names the vendor lacks.

**Acceptance / DoD (phase 2):** validation report committed; swap atomic; ledgers reset per provision; membership timeline shows real entries AND exits (delisted names exit on their true dates); survivorship disclosure updated truthfully.

**Ready-to-paste journey block:** *(phase 2; phase 1 is a memo, no journey)*
```markdown
- **J-XX: The evidence basis is survivorship-free — delisted names live in the history, honestly**
  - Steps:
    1. Visit the Data Manager; assert the price basis names the vendor, the span, and that delisted names are present with their true last trading dates.
    2. Visit the membership timeline; assert historical exits (delistings/removals) appear on their real dates, not only entries.
    3. Visit `/evidence`; assert the ledger was reset under the sanctioned basis-change provision and only re-certified claims show "Proven".
    4. Visit `/backtest`; assert the survivorship disclosure now states point-in-time membership with delisted coverage (no longer "upper bound only").
  - Acceptance:
    - **Consistency (single source):** membership and prices come from the one vendored basis; every surface re-reads the same resolver/ledger outputs; no dual-basis mixing anywhere.
    - **Correctness:** a spot-checked delisted name's last bar matches the vendor's record; a spot-checked split day is continuous on the adjusted basis.
    - **Honest status / anti-goals:** pre-reset claims are not displayed as proven; names the vendor lacks render honest absence; no fabricated bars; determinism + no-lookahead preserved.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of the new basis disclosure, a delisted name's timeline, and the reset evidence page, viewable via `demo.sh mcp-loop --session-live`.
```

**Traps:** vendor splice (see Do-NOT-touch); running the swap concurrently with any other pin-refreshing work; treating the reset as optional (stale p-values on a changed basis are the exact dishonesty goal.md's provision exists to prevent); forgetting `data_manager` FETCH must also route through the new provider or live updates re-introduce the seam.
**Depends on:** B-111 (benefit quantification), owner's paid approval, iter-18 playbook familiarity.

---

#### B-113 · Data-quality sentinel: value-level anomaly detection
**Track:** T1 · **Quarter:** Q1 · **Priority:** P1 · **Status:** PROPOSED
**Difficulty:** MEDIUM · **Dominant failure mode:** data-integrity

**What:** `data_manager` already reports **presence** problems (coverage gaps, staleness, thin history). This card adds **value-level** detectors: day-over-day adjusted-close jumps unexplained by the return distribution (the *adjustment-seam* signature — Stooq back-adjusts entire histories when dividends occur, so a fresh fetch appended to an old seed can shift levels); stale-price runs (N identical closes); zero-volume runs; high<low or nonpositive values; volume spikes with zero price movement. Per-symbol anomaly list on `/data`, and a boolean feed into the B-301 preflight verdict.

**Why it protects capital:** the failure mode is silent: one seam or a stretch of stale prices and every indicator downstream is wrong while the board looks normal. This is the difference between a data feed and a *supervised* data feed.

**Data / plugs in at:** existing `daily_prices`; a new detector pass in `engine/data_manager.py` (beside the existing availability/gap categorization) writing an anomalies artifact; `/data` UI section; readiness input.
**Config surface:** `data_quality.sentinel.*` thresholds (jump z-score, stale-run length, zero-volume run length) — all config, no literals.
**How:** (1) detectors as pure functions over per-symbol series (fixture-testable); (2) job mode + artifact; (3) `/data` panel with severity tiers; (4) readiness consumes "critical anomalies present". Size: ~2 iterations.

**Evidence Claim & ledger:** `N/A — this card must not introduce proven-language anywhere.`
**Canonical value:** anomalies artifact; readers: data page, readiness (B-301).
**Anti-goal boundary:** none.
**Tests that will break:** none; fixture tests per detector (construct a seam, a stale run, etc., assert detection).
**Do NOT touch:** the prices themselves — the sentinel reports; it NEVER auto-"repairs" data (repair = fabrication).

**Acceptance / DoD:** each detector has a fixture proof; `/data` lists anomalies with symbol/date/kind/severity; a critical anomaly degrades readiness.

**Ready-to-paste journey block:**
```markdown
- **J-XX: Value-level data anomalies are detected, listed, and degrade readiness**
  - Steps:
    1. Run the data-quality sentinel job.
    2. Visit `/data`; assert an anomalies section lists any findings with symbol, date, kind (seam / stale-run / zero-volume / invalid-bar / spike), and severity — or an explicit "no anomalies detected as of <date>".
    3. Assert the readiness/preflight state reflects critical anomalies (not fully green when one exists).
  - Acceptance:
    - **Consistency (single source):** the panel re-reads the sentinel artifact; readiness consumes the same artifact.
    - **Correctness:** a fixture-planted seam is detected at the right date in tests; thresholds come from config.
    - **Honest status / anti-goals:** no auto-repair of data; absence of anomalies is stated with its as-of date, never implied.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of the anomalies section, viewable via `demo.sh mcp-loop --session-live`.
```

**Traps:** auto-correcting values (never); thresholds as literals; flagging legitimate splits as seams when the vendor basis is consistent — the seam detector targets *unexplained* jumps (document the distinction in the panel's method note).
**Depends on:** none. Feeds B-301, B-304.

---

#### B-114 · Point-in-time sector-membership honesty + pre-2005 control coverage
**Track:** T1 · **Quarter:** Q3 · **Priority:** P2 · **Status:** PROPOSED
**Difficulty:** MEDIUM · **Dominant failure mode:** data-integrity

**What:** two related honesty audits on deep history. (a) **Sector drift:** today's sector map is applied across 30 years; GICS reclassifications (notably 2018's Communication Services) make deep-history sector RS and the *random-same-sector* control group subtly wrong. Measure sensitivity: recompute affected stats excluding known-reclassified names; disclose on methodology; optionally introduce a dated sector map if a free source suffices. (b) **Control coverage:** verify which control instruments actually have bars in each era of the 30y window (the deep-context work noted SPY's depth limits in this feed); render an honest per-era control-coverage table, and where the primary control is absent, show which fallback (vendor-labeled index proxy) backed the comparison.

**Why it protects capital:** controls are the "against what?" of every certificate; a control that silently thins out pre-2005 weakens exactly the era that contains two crashes.

**Data / plugs in at:** existing bars + `forward_testing._control_groups`; methodology page; evidence detail footnotes.
**Config surface:** `data_quality.control_coverage.eras` (fixed date cuts).
**How:** (1) per-era bar-coverage table for SPY/QQQ/sector ETFs/index proxies; (2) annotate claims whose windows include thin-control eras; (3) sector-drift sensitivity pass with a documented reclassified-names list; (4) disclosures. Size: ~2 iterations.

**Evidence Claim & ledger:** `N/A — this card must not introduce proven-language anywhere.`
**Canonical value:** coverage/sensitivity artifacts; readers: methodology, evidence detail.
**Anti-goal boundary:** none.
**Tests that will break:** none; fixture tests for the coverage table.
**Do NOT touch:** control-group selection logic (measure first; changing controls is a separate owner decision).

**Acceptance / DoD:** per-era control-coverage table live; affected claims footnoted; sector-drift sensitivity summary with the exclusion list published.

**Ready-to-paste journey block:**
```markdown
- **J-XX: Deep-history comparisons disclose control coverage and sector-map drift**
  - Steps:
    1. Visit `/methodology`; assert a control-coverage table shows, per era, which benchmark/control instruments have real bars and which comparisons fall back to labeled proxies.
    2. Open a certified claim whose window includes a thin-control era; assert its detail carries the coverage footnote.
    3. Assert the sector-drift note states the reclassification sensitivity result and its method.
  - Acceptance:
    - **Consistency (single source):** both surfaces re-read the one coverage artifact.
    - **Correctness:** one era's coverage row re-verified against raw bar counts matches.
    - **Honest status / anti-goals:** absent controls are disclosed, never silently substituted; proxies remain vendor-labeled; no verdict changes.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of the coverage table and one footnoted claim, viewable via `demo.sh mcp-loop --session-live`.
```

**Traps:** back-projecting today's sector labels and calling it "point-in-time"; swapping controls quietly to friendlier ones (any control change is a new owner-approved decision + re-certification question).
**Depends on:** none.

---

#### B-115 · Reproducibility receipts ("re-run this proof")
**Track:** T1 · **Quarter:** Q2 · **Priority:** P2 · **Status:** PROPOSED
**Difficulty:** EASY–MEDIUM · **Dominant failure mode:** data-integrity (budget/ledger hygiene)

**What:** one command (script + MCP tool) that takes a ledger row id, replays its cohort/control extraction and referee computation **from the recorded parameters** against the current seed, and emits a receipt: verdict match / statistic drift / inputs changed (engine hash, data basis). Evidence detail shows the last receipt date + result per claim. Generalizes the forward-walk's reproduce contract into user-facing auditability — "audit the proof" becomes *re-running* it, not reading JSON.

**Why it protects capital:** certificates age (data revisions, engine changes). A one-command re-proof catches drift the moment anyone looks, and is the owner's tool for "do I still believe this?"

**Data / plugs in at:** ledgers + `referee.py` (replay path with recorded params), MCP server tool beside `verify_edge`, evidence detail field.
**Config surface:** none material.
**How:** (1) replay = verification of a RECORDED verdict with its RECORDED parameters — by design it does **not** charge the Thresholdout budget and does **not** append ledger rows (document this distinction in code comments and the method note); (2) receipt artifact per run; (3) surface. Size: ~1–2 iterations.

**Evidence Claim & ledger:** `N/A — this card must not introduce proven-language anywhere.`
**Canonical value:** receipt artifacts; reader: evidence detail.
**Anti-goal boundary:** none.
**Tests that will break:** none; fixture test: certify on fixture → replay → verdict match; perturb fixture → drift detected.
**Do NOT touch:** budget accounting; ledger append paths (receipts live beside, not inside).

**Acceptance / DoD:** replaying every canonical claim produces receipts; a deliberate fixture perturbation yields a drift receipt; evidence detail shows receipt status.

**Ready-to-paste journey block:**
```markdown
- **J-XX: Any certified claim can be re-proven on demand, with a receipt**
  - Steps:
    1. Invoke the reproduce command/tool for each canonical ledger row.
    2. Assert each produces a receipt stating: verdict match or drift, the recomputed statistic vs the recorded one, the engine/config identity, and the run date.
    3. Visit `/evidence`; assert each claim's detail shows its latest receipt status and date.
  - Acceptance:
    - **Consistency (single source):** the receipt is computed by the same referee code path with the recorded parameters; the UI re-reads receipts verbatim.
    - **Correctness:** a receipt's recomputed statistic matches an independent offline replay.
    - **Honest status / anti-goals:** drift is displayed prominently on the claim (never hidden); replays never mint or modify claims and never spend the certification budget.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of one receipt from command to evidence detail, viewable via `demo.sh mcp-loop --session-live`.
```

**Traps:** letting replays append to ledgers or charge budget (they're read-only proofs); replaying with *current defaults* instead of recorded parameters (that's B-105's sweep, a different tool); treating drift as an error to auto-fix (it's a finding for the owner + B-305 lifecycle).
**Depends on:** B-306 (engine-version stamp) sharpens the "inputs changed" classification; not blocking.

---

#### B-116 · Corporate-actions / adjustment-event awareness on charts *(P3, condensed)*
**Track:** T1 · **Quarter:** Q3 · **Priority:** P3 · **Status:** PROPOSED
**Difficulty:** EASY · **Dominant failure mode:** data-integrity

**What & why:** the feed is back-adjusted, so dividend/split effects hide inside "price" moves and vendor re-adjustments shift whole histories. Mark detected adjustment events (from B-113's seam detector; from vendor metadata after B-112) on price charts as small annotations, so a gap or level shift is not misread as a trading signal.
**How:** chart annotation layer reading the sentinel/vendor artifact; no new computation. Size: ~1 iteration.
★ **Evidence Claim:** `N/A — must not introduce proven-language.` ★ **Canonical value:** none — re-reads B-113/B-112 artifacts. ★ **Boundary:** none. ★ **Tests:** chart payload additive fields only. ★ **Do NOT touch:** price data; indicator math.
**Journey (paste-ready):**
```markdown
- **J-XX: Charts disclose adjustment events so they are not misread as signals**
  - Steps:
    1. Open a stock detail chart for a name with a detected adjustment event; assert a labeled marker appears at the event date with a plain-language tooltip.
    2. Assert the marker's source (sentinel detection or vendor metadata) is named.
  - Acceptance:
    - **Consistency (single source):** markers re-read the existing anomaly/vendor artifact; no recomputation.
    - **Correctness:** marker dates match the artifact.
    - **Honest status / anti-goals:** annotations are factual ("vendor adjustment event"), no signal language.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of one annotated chart, viewable via `demo.sh mcp-loop --session-live`.
```
**Traps:** inventing ex-div dates we don't actually have (only mark what an artifact evidences). **Depends on:** B-113 (or B-112 for vendor metadata).

---

#### B-117 · ◇ Universe composition drift dashboard *(P3, condensed, attrition-buffer)*
**Track:** T1 · **Quarter:** any · **Priority:** P3 · **Status:** PROPOSED
**Difficulty:** EASY · **Dominant failure mode:** UI-recompute

**What & why:** a small research page showing the resolved point-in-time universe's composition over 30 years — member count, sector weights, median dollar-volume — so factor-performance differences across eras can be read against what the universe *was* (e.g., tech-heavy late-90s). Pure description; uses the membership timeline + stored snapshots.
**How:** one engine compute + lab page (standard triple). Size: ~1 iteration.
★ **Evidence Claim:** `N/A — must not introduce proven-language.` ★ **Canonical value:** one composition payload; reader: the page. ★ **Boundary:** none. ★ **Tests:** fixture with a constructed membership timeline. ★ **Do NOT touch:** resolver logic.
**Journey (paste-ready):**
```markdown
- **J-XX: The point-in-time universe's composition over time is visible**
  - Steps:
    1. Visit the universe-composition page; assert charts show member count and sector weights across the full history at the walk-forward cadence.
    2. Pick one historical date and assert its member count matches the membership timeline for the same date.
  - Acceptance:
    - **Consistency (single source):** the page re-reads one engine-computed composition payload derived from the canonical membership timeline.
    - **Correctness:** the spot-checked date matches the timeline.
    - **Honest status / anti-goals:** description only; no proven-language; survivorship caveat repeated on-page.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of the composition charts, viewable via `demo.sh mcp-loop --session-live`.
```
**Traps:** recomputing membership in the page instead of re-reading the timeline. **Depends on:** iter-18's membership timeline.

## Track 2 — Risk & capital-preservation analytics

The product scores entries; almost nothing quantifies *staying alive*: how much a name can hurt, how correlated the owner's picks are, what drawdowns and dry spells to expect, and which exit style actually preserves capital. All descriptive/evidence work — anything prescriptive is boundary-flagged.

| Card | Title | Pri | Qtr |
|------|-------|-----|-----|
| B-201 | Per-stock risk-budget card | P1 | Q2 |
| B-202 | Invalidation-style evidence study (50-DMA vs ATR-trail vs structure-low) | P1 | Q2 |
| B-203 | Position-risk arithmetic panel (stateless) — BOUNDARY | P2 | Q2+ |
| B-204 | Watchlist exposure X-ray | P1 | Q2 |
| B-205 | Phase-conditional drawdown & dry-spell expectations | P1 | Q2 |
| B-206 | CVaR / expected shortfall in labs | P2 | Q2 |
| B-207 | Phase-transition outcome cards | P2 | Q3 |
| B-208 | Sequence-risk Monte Carlo (resampled history) | P2 | Q3 |
| B-209 | Earnings-gap risk flags | P2 | Q3 (needs B-505) |
| B-210 | Liquidity & capacity honesty per name | P2 | Q2 |
| B-211 | ◇ Decile turnover / persistence (human tradability) | P2 | Q3 |
| B-212 | Pre-commitment if-then card — BOUNDARY | P3 | Q4 |

---

#### B-201 · Per-stock risk-budget card
**Track:** T2 · **Quarter:** Q2 · **Priority:** P1 · **Status:** PROPOSED
**Difficulty:** EASY–MEDIUM · **Dominant failure mode:** UI-recompute

**What:** a compact "how much can this hurt" card on every stock detail (and a column set on `/stocks`): ATR% (exists), downside semideviation (exists as stored factor), **overnight-gap profile** (distribution of |open − prior close| moves: median, p95, worst; % of 20d return variance occurring overnight), **worst-20d window** in the name's history vs the universe median, and distance-to-invalidation as a % (exists, reframed). All computed in the engine at snapshot time (new stored components — additive), rendered with universe-percentile context ("gap risk: p87 of universe").

**Why it protects capital:** entry quality is half the decision; the other half is "what is the plausible damage if I'm wrong" — currently scattered or absent (gap risk entirely absent, and gaps are exactly what invalidation levels cannot protect against).

**Data:** existing OHLCV.
**Plugs in at:** `engine/indicators.py` (new pure functions: gap stats, worst-window), `scoring.py` stored factors (pattern at `scoring.py:368`), `ScannerResult` additive fields, stock-detail UI + leaderboard columns; methodology entries (catalog completeness assertion will demand them).
**Config surface:** `indicators.gap_window`, `indicators.worst_window_days: 20` etc. — all config.
**How:** (1) pure indicator functions with fixture tests; (2) store at snapshot time (append-only, new fields NA for historical rows until a sanctioned backfill); (3) card UI + columns; (4) methodology entries. Size: ~2 iterations; split: engine+storage first, UI second.

**Evidence Claim & ledger:** `N/A — this card must not introduce proven-language anywhere.`
**Canonical value:** the new risk components, computed once at snapshot time; readers: stock detail, leaderboard, later B-203/B-1203.
**Anti-goal boundary:** none (descriptive risk facts).
**Tests that will break:** snapshot payload-shape tests (additive); methodology completeness test until entries are added — add them in the same iteration.
**Do NOT touch:** existing score weights (these are display components, not new score inputs — feeding them into the Risk score is a separate pre-registered decision).

**Acceptance / DoD:** card renders for every stock with percentile context and honest NA for short-history names; one spot-checked gap-p95 matches offline computation; methodology documents each component.

**Ready-to-paste journey block:**
```markdown
- **J-XX: Every stock shows an honest "how much can this hurt" risk-budget card**
  - Steps:
    1. Open `/stocks/{ticker}` for a liquid name; assert a risk card shows ATR%, downside volatility, an overnight-gap profile (median / p95 / worst), the worst historical 20-day window, and distance-to-invalidation — each with a universe-percentile context label.
    2. Open a short-history name; assert components without sufficient history render NA with the reason.
    3. Assert `/methodology` documents each new component's formula and window.
  - Acceptance:
    - **Consistency (single source):** all card values come from the stored snapshot record (computed once at scan time); the leaderboard columns re-read the same fields; no UI recomputation.
    - **Correctness:** a spot-checked gap-profile value byte-matches the engine's computation for the same as-of.
    - **Honest status / anti-goals:** no new proven-language (descriptive stats, no badges); NA over fabrication for thin history; no position advice.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of the risk card on one stock, viewable via `demo.sh mcp-loop --session-live`.
```

**Traps:** computing gap stats in the frontend from bars (UI-recompute); percentile context must be cross-sectional at the same as-of (not across time); worst-window on adjusted prices spanning an adjustment seam — cite B-113/B-116 markers in the tooltip when applicable.
**Depends on:** none.

---

#### B-202 · Invalidation-style evidence study (50-DMA vs ATR-trail vs structure-low)
**Track:** T2 · **Quarter:** Q2 · **Priority:** P1 · **Status:** PROPOSED
**Difficulty:** MEDIUM · **Dominant failure mode:** p-hack (three styles ≠ a style grid-search; pre-register exactly these)

**What:** the product's one exit primitive is "invalid below the 50-DMA". Measure — as an **event study of level-breach events**, not simulated trading — which of three pre-registered invalidation styles best separates "breach that meant real further damage" from "shakeout that recovered": (a) current 50-DMA, (b) ATR-multiple trail (k×ATR below the highest close since the setup date, k from config), (c) structure-low (most recent swing low). Per style: breach frequency, post-breach forward outcomes (did decline continue?), whipsaw rate (breach then recovery above entry within h), average loss depth at breach. One pre-registered staging claim on the strongest *ex-ante* hypothesis: ATR-trail breaches are more informative (more reliably followed by further decline) than 50-DMA breaches at h=20.

**Why it protects capital:** exits, not entries, decide account survival. Today's 50-DMA line is folklore inherited from the methodology; this card turns "where should I honestly stop believing" into measured conditional outcomes.

**Data:** existing bars + stored snapshots (setup dates/cohorts) + `forward_returns`/excursion machinery (MAE/MFE exist).
**Plugs in at:** event-study lab machinery (`engine/research.py` + `drill_samples` grammar), pure level-computation helpers in `indicators.py`; a lab page section; the stock-detail invalidation panel gains a "styles compared" link (display only — the product's live invalidation stays 50-DMA unless the owner later changes `decision_rules`).
**Config surface:** `research.invalidation_study.atr_k`, `swing_lookback` — fixed up front (pre-registered), never tuned to results.
**How:** (1) compute the three levels per setup event historically (path-dependent trail computed causally from bars ≤ each date); (2) detect breach events per style; (3) event-study outcomes + whipsaw stats per style; (4) the ONE claim through staging; (5) surface comparison table with CIs (B-106). Size: ~2–3 iterations; split: levels+events, then stats+claim, then UI.

**Evidence Claim & ledger:** staging; 1 trial; on FAIL → graveyard (the comparison table still ships as descriptive stats — the *claim* dies, the *measurement* remains honest).
```json
{"kind": "event-study", "subject": "invalidation_breach_atr_trail", "setup": "vs_50dma_breach", "horizon": 20, "direction": "negative"}
```
(Exact selector names to fit the event-study grammar; the hypothesis sentence is fixed BEFORE running: "post-breach 20-day forward returns after ATR-trail breaches are lower than after 50-DMA breaches on the same cohort.")

**Canonical value:** the per-style event stats payload (engine); readers: lab page, stock-detail link.
**Anti-goal boundary:** none — measuring breach outcomes is decision-quality; the card does NOT tell the user which stop to use, it shows which breach meant what, historically.
**Tests that will break:** none expected; `drill_samples` grammar tests if a selector kind is added (fixture-based).
**Do NOT touch:** `config.decision_rules.invalidation` live behavior; the displayed invalidation level's computation (changing the product's actual stop style is a separate owner decision informed by this card).

**Acceptance / DoD:** three styles computed causally; per-style breach/outcome/whipsaw table with n and CIs; the pre-registered claim's verdict recorded; live invalidation unchanged.

**Ready-to-paste journey block:**
```markdown
- **J-XX: Invalidation styles carry measured breach-outcome evidence (50-DMA vs ATR-trail vs structure-low)**
  - Steps:
    1. The iteration carries a machine-readable `## Evidence Claim` —
       `{"kind":"event-study","subject":"invalidation_breach_atr_trail","setup":"vs_50dma_breach","horizon":20,"direction":"negative"}` —
       routed to the staging ledger; the post-decompose gate referees it BEFORE code is built; a non-PASS verdict blocks the iteration.
    2. Visit the invalidation study on the research event-study surface; assert a per-style table shows breach frequency, post-breach forward outcomes, whipsaw rate, and loss depth at breach — each with sample sizes and confidence intervals.
    3. Open `/stocks/{ticker}`; assert the invalidation panel links to the study and the LIVE invalidation level is unchanged (still the documented 50-DMA rule).
  - Acceptance:
    - **Consistency (single source):** the comparison payload is computed once in the research engine from stored snapshots and bars; the detail-page link re-reads it; live invalidation still comes from the existing engine path.
    - **Correctness:** one style's breach list for one name re-verified offline matches (levels computed causally from bars ≤ each date).
    - **Honest status / anti-goals:** no "use this stop" language — outcomes are stated, choices are the owner's; a FAIL verdict leaves the table descriptive with "Not yet proven" on the comparison claim; no lookahead in trail computation.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of the style-comparison table and the stock-detail link, viewable via `demo.sh mcp-loop --session-live`.
```

**Traps:** the ATR trail must be computed forward-in-time from the setup date using only bars ≤ each evaluation date (an easy lookahead bug: using the max close of the whole window); tuning `atr_k` after seeing results (pre-register one k; a second k is a new registered hypothesis); reading "lower whipsaw" as automatically better (tighter stops breach more — the table reports the trade-off, the claim tests one direction on one metric).
**Depends on:** B-106 (CIs); B-101 improves realism of outcome stats (not blocking).

---

#### B-203 · Position-risk arithmetic panel (stateless) — **BOUNDARY**
**Track:** T2 · **Quarter:** Q2+ (after amendment approval) · **Priority:** P2 · **Status:** PROPOSED
**Difficulty:** EASY · **Dominant failure mode:** boundary (quietly becoming a position tracker or advisor)

**What:** an explicitly user-invoked calculator on the stock detail page: the owner types an account size and a risk fraction; the panel computes — pure arithmetic, nothing stored — "risking R% of A at the displayed invalidation distance d% implies a position no larger than N shares ≈ $X (Y% of account)". Plus the gap caveat from B-201: "note: p95 overnight gap for this name is g% — a gap through the level would exceed the planned risk by ~Z".

**Why it protects capital:** the most common retail failure is size, not selection. The system knows the invalidation distance; letting the owner do this arithmetic by hand every time invites the exact error the calculator prevents. Kept stateless so it can never become a portfolio/P&L feature.

**Data / plugs in at:** displayed snapshot fields only (invalidation distance, price, B-201 gap stats); one frontend panel + one tiny engine endpoint OR pure-frontend arithmetic — **decision: compute in the frontend from displayed canonical values** (it is user-input arithmetic, not a contract value; document this exception in the card and code comment).
**Config surface:** none (inputs are user-typed; nothing persisted).
**How:** (1) amendment approved first; (2) panel with two inputs + derived outputs + gap caveat; (3) unit tests on the arithmetic; (4) explicit "arithmetic, not advice" label. Size: ~1 iteration.

**Evidence Claim & ledger:** `N/A — this card must not introduce proven-language anywhere.`
**Canonical value:** none — consumes displayed canonical values plus user input; produces nothing stored. (This is the sanctioned exception to "compute in engine": user-local arithmetic on user-local inputs.)
**Anti-goal boundary:** **BOUNDARY — requires goal.md amendment before proceeding.** Proposed amendment sentence to add under Anti-goals:
> - **Personal-risk arithmetic exception (owner-approved <date>):** an explicitly user-invoked, stateless calculator MAY display arithmetic combining user-entered inputs (account size, risk fraction) with already-displayed factual levels — e.g., the maximum position size consistent with the entered risk at the displayed invalidation distance — provided nothing is persisted, no recommendation or imperative verbs appear, and the output is labeled "arithmetic on your inputs, not advice". *(scoped exception to "decision-quality only")*
**Tests that will break:** none.
**Do NOT touch:** watchlist storage (no quantities/cost basis anywhere — its docstring's exclusions stay true); no persistence of inputs (not even localStorage defaults without the owner asking).

**Acceptance / DoD:** panel computes correctly (unit-tested examples); refresh loses inputs (statelessness demonstrated); label present; gap caveat wired to B-201 values.

**Ready-to-paste journey block:**
```markdown
- **J-XX: A stateless risk-arithmetic panel turns invalidation distance into a size ceiling**
  - Steps:
    1. Confirm goal.md's Anti-goals section contains the owner-approved personal-risk arithmetic exception (this journey is invalid without it).
    2. On `/stocks/{ticker}`, open the risk-arithmetic panel; enter an account size and risk fraction; assert the panel shows the implied maximum position (shares, $, % of account) derived from the displayed invalidation distance, plus the p95-gap caveat.
    3. Reload the page; assert the inputs are gone (nothing persisted).
    4. Assert the panel is labeled "arithmetic on your inputs — not advice" and contains no imperative verbs.
  - Acceptance:
    - **Consistency (single source):** the invalidation distance and gap statistic are read from the same snapshot payload the page already displays; the panel introduces no new served value.
    - **Correctness:** the arithmetic matches the unit-tested formula for the entered examples.
    - **Honest status / anti-goals:** complies with the scoped exception exactly (stateless, labeled, no recommendations); no P&L, no persistence, no order language.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of entering inputs and reading the ceiling, viewable via `demo.sh mcp-loop --session-live`.
```

**Traps:** "helpfully" persisting the account size (that is a position-tracker back door — forbidden); adding "suggested risk %" defaults (advice); extending to multi-position aggregation (that is B-204's descriptive job, not this calculator's).
**Depends on:** owner-approved amendment; B-201 (gap caveat).

---

#### B-204 · Watchlist exposure X-ray
**Track:** T2 · **Quarter:** Q2 · **Priority:** P1 · **Status:** PROPOSED
**Difficulty:** MEDIUM · **Dominant failure mode:** UI-recompute

**What:** the watchlist is the owner's de-facto "what I'm in / watching" set, and nothing tells them how *concentrated* it is. Add an X-ray section on `/watchlist`: pairwise return-correlation matrix (trailing window, config), a simple cluster grouping (correlation-threshold clustering — deterministic, no fancy ML), **effective number of bets** (same ENB formula as B-104, one shared helper), sector/theme concentration bars, and count of names sharing the same detected setup/pattern. Purely descriptive; strong wording: "your watchlist behaves like ~2.3 independent positions".

**Why it protects capital:** correlation is the silent killer of "diversified" retail portfolios — five leaders from one theme gap down together. This is the highest-value 1-iteration risk view in the whole backlog.

**Data / plugs in at:** existing bars + watchlist table + snapshot fields; compute in a new engine function (research or watchlist module), served with the watchlist payload; UI section.
**Config surface:** `watchlist.xray.corr_window_days` (e.g., 126), `cluster_threshold`, `min_overlap_days` (NA floor).
**How:** (1) engine computation (correlation, clusters, ENB, concentrations) with honest NA for short-history members; (2) additive payload; (3) UI (matrix heatmap + summary line). Size: ~1–2 iterations.

**Evidence Claim & ledger:** `N/A — this card must not introduce proven-language anywhere.`
**Canonical value:** the X-ray payload computed engine-side with the watchlist response; reader: watchlist page.
**Anti-goal boundary:** none (describes the owner's own list; no advice — "reduce X" language banned).
**Tests that will break:** watchlist payload-shape tests (additive). Fixture: two perfectly correlated + one independent synthetic series → ENB ≈ 2, clusters correct.
**Do NOT touch:** watchlist storage schema (no new persisted fields; the X-ray is computed on read).

**Acceptance / DoD:** X-ray renders with matrix, clusters, ENB, concentration bars; NA handling for freshly-listed names; fixture sanity green.

**Ready-to-paste journey block:**
```markdown
- **J-XX: The watchlist discloses its real concentration (correlations, clusters, effective bets)**
  - Steps:
    1. Add several correlated names and one unrelated name to the watchlist.
    2. Visit `/watchlist`; assert the X-ray shows a pairwise correlation view, cluster groupings, sector/theme concentration, and a headline "effective independent bets" figure with its window stated.
    3. Assert names with insufficient overlapping history render NA in the matrix rather than a fabricated value.
  - Acceptance:
    - **Consistency (single source):** the X-ray payload is computed once, engine-side, with the watchlist response; the page re-reads it; the ENB helper is the same module used by the evidence correlation audit.
    - **Correctness:** a spot-checked pair correlation matches an offline computation over the same window.
    - **Honest status / anti-goals:** descriptive only — no "trim/add" recommendations; honest NA; no proven-language.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of the X-ray on a demo watchlist, viewable via `demo.sh mcp-loop --session-live`.
```

**Traps:** computing correlations in the browser (UI-recompute); a second ENB implementation (share B-104's helper — build whichever card lands first, reuse in the second); advice language.
**Depends on:** none (shares a helper with B-104).

---

#### B-205 · Phase-conditional drawdown & dry-spell expectations
**Track:** T2 · **Quarter:** Q2 · **Priority:** P1 · **Status:** PROPOSED
**Difficulty:** MEDIUM · **Dominant failure mode:** lookahead (phase labels must be the causal ones)

**What:** historical **distributions** — never point forecasts — of what following this methodology has felt like, conditional on the market phase at entry: max-drawdown depth AND duration (time-underwater, which the product does not compute today — MDD depth exists, duration does not), time-to-recover, and **loss-streak lengths** (consecutive setups with negative h-forward returns) for the flagship cohorts and each certified claim. Rendered as "expectation-setting" panels: "In Correction phases, top-decile entries historically saw a median max-DD of −X% (p90: −Y%), typical underwater time N weeks, and losing streaks up to K setups (n=…)".

**Why it protects capital:** the most likely way the owner loses money with a *valid* process is abandoning it at the bottom of a normal dry spell. Pre-committed, phase-conditional expectations are the antidote — this is drawdown psychology, quantified.

**Data / plugs in at:** `forward_returns` + excursions + causal phase timeline; extend `forward_testing.py` aggregation with duration/underwater/streak statistics; surfaces: evidence detail (per claim), backtest page, and later the B-1203 Sunday sheet.
**Config surface:** `walk_forward.underwater_horizons`, `streak_min_n` (honesty floors).
**How:** (1) underwater/duration/streak computations as pure aggregation helpers (fixture-tested); (2) phase-conditioning via the stored causal timeline; (3) per-cohort panels with n everywhere; (4) plain-language framing strings reviewed against the language bans. Size: ~2 iterations.

**Evidence Claim & ledger:** `N/A — this card must not introduce proven-language anywhere.` (Distributions of history, labeled as such.)
**Canonical value:** the expectations payload per cohort/claim; readers: evidence detail, backtest, Sunday sheet later.
**Anti-goal boundary:** none — wording is the guardrail: "historically saw", never "expect to lose at most" (no promise language in either direction).
**Tests that will break:** aggregation payload tests (additive); fixture: constructed return series with known streaks/underwater spells → exact stats.
**Do NOT touch:** MDD depth computation (reuse it; do not fork).

**Acceptance / DoD:** panels render for flagship cohorts + every canonical claim with per-phase n and floors; fixture exactness; language audit passes (no promise verbs).

**Ready-to-paste journey block:**
```markdown
- **J-XX: Drawdown and dry-spell expectations are visible, phase-conditional, and honest**
  - Steps:
    1. Open a certified claim's detail on `/evidence`; assert an expectations panel shows historical distributions (median / p90) of max-drawdown depth, underwater duration, time-to-recover, and longest losing streak — split by market phase at entry, each with sample size.
    2. Assert phases below the honesty floor render "insufficient (n=…)".
    3. Assert the wording is historical ("historically saw"), with no forward-promise phrasing.
  - Acceptance:
    - **Consistency (single source):** the payload is computed once in the forward-testing aggregation from stored returns/excursions and the causal phase timeline; surfaces re-read it.
    - **Correctness:** one cell (e.g., Correction-phase median depth) re-verified offline matches.
    - **Honest status / anti-goals:** distributions of history only — no forecasts, no reassurance language; thin cells say insufficient; phase labels are the stored causal ones.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of one claim's expectations panel, viewable via `demo.sh mcp-loop --session-live`.
```

**Traps:** labeling phases retrospectively (must join to the causal timeline as-of each entry date); streaks across overlapping horizons double-count — define the setup sequence at the walk-forward cadence and say so in the method note; turning this into "maximum you can lose" language (it is a historical distribution, and survivorship-biased at that — carry the B-111 caveat).
**Depends on:** phase timeline (exists); B-111's caveat text.

---

#### B-206 · CVaR / expected shortfall in labs
**Track:** T2 · **Quarter:** Q2 · **Priority:** P2 · **Status:** PROPOSED
**Difficulty:** EASY · **Dominant failure mode:** UI-recompute

**What:** cohort tables show mean/MDD; add tail measures: CVaR/ES at config levels (mean of the worst q% of per-setup h-forward returns) and p5/p95 columns, per cohort × horizon, with the same n-floors as everything else.

**Why it protects capital:** means hide tails; two cohorts with equal means and different left tails are different products for a real account.

**Data / plugs in at:** existing per-setup forward returns; one aggregation helper in `forward_testing.py`; lab/backtest columns.
**Config surface:** `walk_forward.cvar_levels: [0.05, 0.10]`.
**How:** helper + columns + methodology entry. Size: ~1 iteration.
**Evidence Claim & ledger:** `N/A — must not introduce proven-language.`
**Canonical value:** CVaR fields in existing aggregation payloads; readers: labs, backtest.
**Anti-goal boundary:** none. **Tests:** additive payload; fixture with constructed tail → exact CVaR. **Do NOT touch:** existing MDD/mean logic.
**Acceptance / DoD:** CVaR columns with n-floors across labs; fixture exactness; methodology entry.

**Ready-to-paste journey block:**
```markdown
- **J-XX: Cohort statistics include tail risk (CVaR), not only means and max drawdown**
  - Steps:
    1. Visit `/research/factor-lab`; assert each decile row shows CVaR at the configured levels alongside mean and max drawdown, with sample size.
    2. Assert cohorts under the n-floor render NA for CVaR.
    3. Assert `/methodology` documents the CVaR definition and levels.
  - Acceptance:
    - **Consistency (single source):** CVaR is computed in the one forward-testing aggregation helper; all surfaces re-read it.
    - **Correctness:** one cohort's CVaR re-verified offline matches.
    - **Honest status / anti-goals:** thin samples say NA; descriptive only.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of the new columns, viewable via `demo.sh mcp-loop --session-live`.
```

**Traps:** computing tails on n<30 (floor them); mixing levels (5% CVaR labeled 10%).
**Depends on:** none.

---

#### B-207 · Phase-transition outcome cards
**Track:** T2 · **Quarter:** Q3 · **Priority:** P2 · **Status:** PROPOSED
**Difficulty:** MEDIUM · **Dominant failure mode:** lookahead / small-n honesty

**What:** for each phase transition the timeline records (Expansion→Pullback, Pullback→Correction, Correction→Bear, any→Recovery), a factual outcome card: historical frequency, what followed (median/p90 further drawdown, duration, % that deepened one more phase, % that resolved up), breadth/velocity context at past transitions, and the current phase's card pinned on the dashboard when a transition fires. Strictly "what history did", no instructions.

**Why it protects capital:** transitions are when the owner must act calmly; a card of base rates ("Pullback→Correction happened X of Y times; when it did, median further damage was Z%") replaces panic with priors. Event-study machinery + the causal timeline already exist — this is composition.

**Data / plugs in at:** phase timeline + index bars + forward stats; `engine/research.py` compute; dashboard + market-phase page.
**Config surface:** `market_phase.transition_cards.min_n`.
**How:** enumerate historical transitions (causal timeline), outcome stats per transition type with n, card payload, UI on `/market-phase` + dashboard pin on fresh transitions. Size: ~2 iterations.
**Evidence Claim & ledger:** `N/A — must not introduce proven-language.` (Base rates, labeled.)
**Canonical value:** transition-cards payload; readers: dashboard, market-phase page.
**Anti-goal boundary:** none (facts, not playbook instructions — owner-authored plans belong to B-1206).
**Tests:** fixture timeline with constructed transitions → exact counts. **Do NOT touch:** phase-engine thresholds.
**Acceptance / DoD:** all transition types carry cards with n; small-n transitions say insufficient; dashboard pin appears only on a fresh transition (causally detected).

**Ready-to-paste journey block:**
```markdown
- **J-XX: Market-phase transitions show their historical base rates, calmly**
  - Steps:
    1. Visit `/market-phase`; assert each transition type shows: historical count, median and p90 further drawdown, typical duration, and how often it deepened vs resolved — each with sample size.
    2. Assert transition types below the configured n render "insufficient history" instead of statistics.
    3. On a date where the causal timeline records a fresh transition, assert the dashboard pins that transition's card.
  - Acceptance:
    - **Consistency (single source):** cards re-read one engine payload derived from the stored causal timeline.
    - **Correctness:** one transition type's count re-verified against the timeline matches.
    - **Honest status / anti-goals:** base rates only — no instructions, no forecasts; n everywhere; timeline is the causal one.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of the transition cards, viewable via `demo.sh mcp-loop --session-live`.
```

**Traps:** counting transitions from a retrospectively-smoothed phase series (must be the causal one); overlapping episodes; implying the current transition will follow the median (banned phrasing — "historically, this transition…").
**Depends on:** phase timeline (exists).

---

#### B-208 · Sequence-risk Monte Carlo (resampled history)
**Track:** T2 · **Quarter:** Q3 · **Priority:** P2 · **Status:** PROPOSED
**Difficulty:** MEDIUM · **Dominant failure mode:** boundary-adjacent wording (this must never read as a wealth projection)

**What:** for a chosen cohort (e.g., flagship top-decile at walk-forward cadence), block-bootstrap the **historical sequence** of per-period cohort returns (reusing the referee's block machinery via B-106's helper) and display the resulting **distribution of resampled historical paths**: spread of horizon outcomes, max-drawdown distribution, probability-of-N-consecutive-losing-periods — explicitly framed: "resampled orderings of the PAST, not projections of the future."

**Why it protects capital:** sequence risk (same returns, unlucky order) is invisible in mean tables; seeing that history's own returns, reshuffled, produce −35% drawdown paths in the p90 tail calibrates the owner's sizing instinct better than any lecture.

**Data / plugs in at:** stored cohort period-returns; B-106 bootstrap helper; a lab section (backtest page or its own research card).
**Config surface:** `research.sequence_mc.n_paths`, `block_length_rule: referee`, `seed`.
**How:** (1) per-period cohort return series (walk-forward cadence); (2) seeded block resampling; (3) distribution stats + fan-style display with the framing banner; (4) method note. Size: ~1–2 iterations.
**Evidence Claim & ledger:** `N/A — must not introduce proven-language.`
**Canonical value:** the MC artifact (seeded, reproducible); reader: the page.
**Anti-goal boundary:** none IF wording holds — the framing banner and the absence of currency-denominated "your wealth" paths are the compliance mechanism (percent space only, cohort-labeled).
**Tests:** seeded reproducibility; fixture series → known drawdown distribution bounds. **Do NOT touch:** referee block-length logic (reuse).
**Acceptance / DoD:** distribution panels render with seed + n_paths + block length stated; banner present; percent-space only.

**Ready-to-paste journey block:**
```markdown
- **J-XX: Sequence risk is visible — resampled orderings of history, honestly framed**
  - Steps:
    1. Open the sequence-risk section for a flagship cohort; assert it shows the distribution of resampled-path outcomes and max-drawdowns (e.g., median / p90) and the probability of K consecutive losing periods, in percent space.
    2. Assert the banner states these are resampled orderings of historical returns, not projections, and names the seed, path count, and block length.
    3. Re-run with the same seed; assert identical results (determinism).
  - Acceptance:
    - **Consistency (single source):** the artifact is computed once, engine-side, using the referee's block-bootstrap machinery; the page re-reads it.
    - **Correctness:** the seeded run reproduces byte-identically.
    - **Honest status / anti-goals:** no wealth-path or projection language; percent space; cohort and survivorship caveats carried.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of the distribution panel and its framing, viewable via `demo.sh mcp-loop --session-live`.
```

**Traps:** i.i.d. resampling (destroys autocorrelation — block bootstrap only); dollar-denominated displays ("$100k would have become…" is banned); letting anyone read the p50 path as "expected".
**Depends on:** B-106 helper.

---

#### B-209 · Earnings-gap risk flags
**Track:** T2 · **Quarter:** Q3 (after B-505) · **Priority:** P2 · **Status:** PROPOSED
**Difficulty:** EASY–MEDIUM · **Dominant failure mode:** lookahead (event dates must be knowable as-of)

**What:** with earnings dates ingested (B-505), (a) flag "reported earnings within the last N days / earnings expected within M days (where a forward date is known from filings/8-K patterns)" on stock detail and leaderboard; (b) revive the permanently-NA `gap_climax` risk component with real event-conditioned gap data (its formula slot already exists in the Risk score, weight currently inert); (c) show each name's historical earnings-day gap distribution beside the B-201 gap profile.

**Why it protects capital:** invalidation levels are useless through an earnings gap; the single most preventable retail loss is holding an oversized position into a binary event unknowingly.

**Data:** B-505's earnings-date table (free, EDGAR-derived, publication-lagged).
**Plugs in at:** `scoring.py` risk components (`gap_climax` slot), snapshot fields, stock detail/leaderboard flags.
**Config surface:** `earnings.recent_days`, `upcoming_days`, `gap_climax` weight (currently inert — enabling it is a scoring change: config-gated, default keep-inert until the owner flips it after review).
**How:** (1) as-of join: only filing-confirmed dates ≤ as-of are known; forward "expected" dates only where derivable from official filings ≤ as-of (else absent — no scraped calendars); (2) flags + fields; (3) earnings-day gap history panel; (4) `gap_climax` computation behind its config weight. Size: ~2 iterations.
**Evidence Claim & ledger:** `N/A — must not introduce proven-language.` (If earnings-conditioned *edges* are later wanted → B-506 PEAD, pre-registered.)
**Canonical value:** earnings flags/fields computed at snapshot time; readers: detail, leaderboard, watchlist alerts (B-302).
**Anti-goal boundary:** none.
**Tests:** fixture with synthetic filing dates → correct flags at each as-of; no-date names render nothing (never a guess). **Do NOT touch:** score weights' live values (adding the computation ≠ turning it on).
**Acceptance / DoD:** flags correct against fixture; gap-history panel renders; `gap_climax` computes when enabled and stays inert by default; historical as-ofs only use dates knowable then.

**Ready-to-paste journey block:**
```markdown
- **J-XX: Earnings proximity is flagged and earnings-gap history is visible per name**
  - Steps:
    1. Open `/stocks/{ticker}` for a name with a filing-confirmed recent earnings date; assert an "earnings within last N days" flag with the date and its source filing.
    2. Assert the risk card shows the name's historical earnings-day gap distribution beside its ordinary gap profile.
    3. For a historical as-of BEFORE a then-unannounced earnings date, assert no forward flag is shown (only information knowable at that as-of).
  - Acceptance:
    - **Consistency (single source):** flags/fields are computed at snapshot time from the ingested earnings-date table; all surfaces re-read them.
    - **Correctness:** the flagged date matches the source filing record.
    - **Honest status / anti-goals:** unknown forward dates render as absent, never guessed; no advice language; publication-lag causality respected (a date is usable only from when its filing existed).
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of the flags and gap-history panel, viewable via `demo.sh mcp-loop --session-live`.
```

**Traps:** the classic lookahead: using the earnings date's existence before it was filed (join on filing availability date, not event date); scraping unofficial calendars (banned — official filings only, or absent); flipping `gap_climax` weight on silently (owner decision).
**Depends on:** B-505.

---

#### B-210 · Liquidity & capacity honesty per name
**Track:** T2 · **Quarter:** Q2 · **Priority:** P2 · **Status:** PROPOSED
**Difficulty:** EASY · **Dominant failure mode:** none serious (keep it descriptive)

**What:** per-name tradability facts: ADV$ (exists as a gate input — surface it), a **spread proxy from OHLC** (Corwin–Schultz high–low estimator — implementable from existing bars; cite the formula in methodology), and "days-to-exit at 10% ADV participation" for standard notional bands (config list, e.g., $10k/$50k/$250k — generic bands, not the owner's account).
**Why it protects capital:** the realistic overlay (B-101) uses config cost assumptions; this shows per-name reality, so a thin name's badge doesn't read like SPY's. Also the honesty base for T7 small-caps later.
**Data / plugs in at:** bars; `indicators.py` pure functions; snapshot fields + risk card row + leaderboard column.
**Config surface:** `liquidity.participation_pct`, `notional_bands`.
**How:** estimator + fields + UI + methodology entry. Size: ~1 iteration.
**Evidence Claim & ledger:** `N/A — must not introduce proven-language.`
**Canonical value:** liquidity fields at snapshot time; readers: detail/leaderboard/T7 later.
**Anti-goal boundary:** none (generic bands keep it impersonal; the personal version is B-203's calculator).
**Tests:** estimator fixture vs hand-computed value. **Do NOT touch:** universe ADV gate thresholds.
**Acceptance / DoD:** fields render with method note; estimator fixture-exact; bands from config.

**Ready-to-paste journey block:**
```markdown
- **J-XX: Every name shows honest tradability: dollar volume, estimated spread, days-to-exit**
  - Steps:
    1. Open `/stocks/{ticker}`; assert the risk card shows ADV$, the OHLC-estimated spread with its method named, and days-to-exit at the configured participation for the configured notional bands.
    2. Compare a mega-cap and a thin name; assert the contrast is visible and each value carries its window.
  - Acceptance:
    - **Consistency (single source):** values are stored snapshot fields; surfaces re-read them.
    - **Correctness:** one spread estimate re-verified offline matches.
    - **Honest status / anti-goals:** descriptive; generic bands (no personal account data); NA where history is insufficient.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough contrasting two names' tradability, viewable via `demo.sh mcp-loop --session-live`.
```

**Traps:** presenting the spread proxy as a quoted spread (it's an estimate — label it); personalizing bands (keep generic).
**Depends on:** none.

---

#### B-211 · ◇ Decile turnover / persistence (human tradability) *(condensed)*
**Track:** T2 · **Quarter:** Q3 · **Priority:** P2 · **Status:** PROPOSED
**Difficulty:** EASY · **Dominant failure mode:** UI-recompute

**What & why:** per factor: what fraction of the top decile changes between consecutive walk-forward dates, and the median tenure of a name in D10. A high-churn factor is uncapturable by a weekly-cadence human regardless of its certified edge — this number belongs next to every factor-lab badge. Complements B-413 (signal-decay) with a simpler membership view.
**How:** compute from stored snapshots' factor deciles across dates; one payload; factor-lab column + methodology note. Size: ~1 iteration.
★ **Evidence Claim:** `N/A — must not introduce proven-language.` ★ **Canonical value:** turnover fields in factor-lab payload. ★ **Boundary:** none. ★ **Tests:** fixture with constructed membership → exact turnover. ★ **Do NOT touch:** decile assignment logic (read stored).
**Journey (paste-ready):**
```markdown
- **J-XX: Every factor discloses its top-decile turnover and typical tenure**
  - Steps:
    1. Visit `/research/factor-lab` for a factor; assert the top-decile panel shows period-over-period membership turnover and median tenure, with the cadence named.
    2. Assert a high-churn factor and a stable factor display visibly different figures.
  - Acceptance:
    - **Consistency (single source):** turnover comes from the one engine payload over stored deciles.
    - **Correctness:** one period's turnover re-verified against stored membership matches.
    - **Honest status / anti-goals:** descriptive; no tradability *advice*, just the number and cadence.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of the turnover figures, viewable via `demo.sh mcp-loop --session-live`.
```
**Traps:** comparing deciles across different universe sizes without noting membership changes (state the denominator). **Depends on:** none.

---

#### B-212 · Pre-commitment if-then card — **BOUNDARY** *(condensed)*
**Track:** T2 · **Quarter:** Q4 · **Priority:** P3 · **Status:** PROPOSED
**Difficulty:** EASY · **Dominant failure mode:** boundary (product-generated action language)

**What & why:** an exportable/printable card per watchlist name composing **owner-authored** if-then plan text with displayed factual levels: "IF close < 175.32 (displayed invalidation) THEN [owner's own words]". Behavioral pre-commitment beats in-the-moment judgment; the product supplies facts, the OWNER supplies every action verb.
★ **Anti-goal boundary: BOUNDARY — amendment required:**
> - **Pre-commitment card exception (owner-approved <date>):** the product MAY compose owner-authored if-then plan text with already-displayed factual levels into an exportable card, provided every action phrase is verbatim owner input and the product contributes only factual conditions. *(scoped exception to "decision-quality only")*
**How:** owner-notes input (persisted as plain text notes — no quantities), card renderer, export/print. Size: ~1 iteration. ★ **Evidence Claim:** `N/A — must not introduce proven-language.` ★ **Canonical value:** none new (levels re-read from snapshots). ★ **Tests:** template test asserting product-side text contains no imperative verbs. ★ **Do NOT touch:** watchlist schema beyond a nullable owner-notes text field (no qty/price fields).
**Journey (paste-ready):**
```markdown
- **J-XX: Pre-commitment cards compose owner-authored plans with displayed facts**
  - Steps:
    1. Confirm goal.md carries the owner-approved pre-commitment exception.
    2. On a watchlist name, enter owner plan text; export the card; assert it renders the displayed invalidation level as the IF condition and the owner's verbatim text as the THEN.
    3. Assert the product-generated portion contains only factual conditions (template test green).
  - Acceptance:
    - **Consistency (single source):** levels re-read from the same snapshot payload the page displays.
    - **Correctness:** the exported level matches the displayed one for the same as-of.
    - **Honest status / anti-goals:** all action language is owner-authored; product text is factual; nothing beyond the notes text is persisted.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of authoring and exporting one card, viewable via `demo.sh mcp-loop --session-live`.
```
**Traps:** templating "helpful" default actions (forbidden — empty means empty); adding quantity fields. **Depends on:** amendment; B-201/B-202 enrich the facts side.

---

## Track 3 — Live-operation readiness

The owner will look at this board on real mornings. This track makes "can I trust the board *today*?" a computed answer, defines what happens when certified edges age, and makes the system survivable (backups, version stamps, refresh runbooks).

| Card | Title | Pri | Qtr |
|------|-------|-----|-----|
| B-301 | Daily preflight go/no-go verdict (kill-switch UX) | P1 | Q1 |
| B-302 | Alerting: factual event notifications | P1 | Q2 |
| B-303 | Decision journal (decision-quality fields only) — BOUNDARY | P2 | Q2+ |
| B-304 | Live-vs-seed drift monitor | P1 | Q1 |
| B-305 | Certified-claim lifecycle: edge health, demotion, retirement | P1 | Q2 |
| B-306 | Engine-version stamping + mixed-version policy | P2 | Q2 |
| B-307 | Weekly evidence digest | P2 | Q2 |
| B-308 | Backup / disaster-recovery runbook | P2 | Q1 |
| B-309 | Universe-pool refresh runbook | P2 | Q3 |

---

#### B-301 · Daily preflight go/no-go verdict (kill-switch UX)
**Track:** T3 · **Quarter:** Q1 · **Priority:** P1 · **Status:** PROPOSED
**Difficulty:** MEDIUM · **Dominant failure mode:** UI-recompute (the verdict must be ONE computed value)

**What:** extend `readiness.py` into a composite **preflight verdict** — `GO / DEGRADED / NO-GO` with a reasons list — computed from: data freshness (latest bar age vs expectation), snapshot existence for the current as-of, critical sentinel anomalies (B-113), drift alarms (B-304), last time-machine result (B-103), and DB/ledger integrity quick-checks. Rendered as an **unmissable banner on every decision surface** (layout-level component): green is quiet; DEGRADED/NO-GO states say plainly "do not rely on today's board" with the reasons.

**Why it protects capital:** the fastest real-money failure is trusting a normal-looking board fed by a stale or corrupted pipeline. One canonical verdict, everywhere, is the risk-officer feature.

**Data / plugs in at:** `engine/readiness.py` (`compute_readiness` exists — extend), inputs from B-113/B-304/B-103 artifacts; `/health` payload; a layout-level frontend banner.
**Config surface:** `readiness.freshness_max_age_days` (market-calendar aware), component severity mapping (which inputs can force NO-GO vs DEGRADED).
**How:** (1) composite verdict function with reasons (pure, fixture-tested per input combination); (2) serve via existing health/readiness path (single source); (3) banner component reading ONLY that payload, present on dashboard/stocks/detail/watchlist/research/evidence; (4) verdict history logged (small append-only) for the digest. Size: ~2 iterations; split: verdict+API, then banner sweep.

**Evidence Claim & ledger:** `N/A — this card must not introduce proven-language anywhere.`
**Canonical value:** THE preflight verdict (one computation in readiness); readers: every page banner, B-302 alerts, B-307 digest.
**Anti-goal boundary:** none.
**Tests that will break:** health payload shape (additive); add per-combination verdict fixtures.
**Do NOT touch:** individual monitors' logic (they feed it; the verdict composes).

**Acceptance / DoD:** all listed surfaces show the banner from the single payload; forcing each input (fixture/config) produces the mapped verdict; reasons listed verbatim; verdict history recorded.

**Ready-to-paste journey block:**
```markdown
- **J-XX: A single daily preflight verdict guards every decision surface**
  - Steps:
    1. With a healthy state, visit the dashboard, `/stocks`, a stock detail, `/watchlist`, and `/evidence`; assert each shows the same quiet GO state from the readiness payload.
    2. Induce a critical condition in a controlled way (e.g., point freshness at a stale fixture or plant a critical sentinel anomaly in the test environment); assert every surface now shows the same DEGRADED/NO-GO banner with the concrete reasons, including the words "do not rely on today's board" for NO-GO.
    3. Assert the verdict and reasons come from one endpoint (no page computes its own).
  - Acceptance:
    - **Consistency (single source):** one readiness computation; every banner re-reads it verbatim; no per-page logic.
    - **Correctness:** each induced input maps to its configured verdict exactly as the fixture matrix specifies.
    - **Honest status / anti-goals:** degraded states are loud, never suppressed; language is factual; no auto-trading implications (it gates *trust*, not orders).
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of GO and induced NO-GO states across two surfaces, viewable via `demo.sh mcp-loop --session-live`.
```

**Traps:** pages computing their own "mini-readiness" (single source!); freshness ignoring weekends/holidays (market-calendar aware age); making NO-GO too easy (alarm fatigue) — severity mapping is config the owner reviews.
**Depends on:** B-113, B-304, B-103 enrich it; ship with whatever inputs exist and add the rest as they land.

---

#### B-302 · Alerting: factual event notifications
**Track:** T3 · **Quarter:** Q2 · **Priority:** P1 · **Status:** PROPOSED
**Difficulty:** MEDIUM · **Dominant failure mode:** boundary (imperative language in templates)

**What:** a job computes alert events after each data update; an in-app alert inbox lists them; optional delivery via config (SMTP email or a self-hosted push like ntfy — default OFF, secrets via environment, never committed). Event types: readiness verdict change (B-301), market phase/regime change, **watchlist invalidation breach** (close crossed below the displayed level — factual statement), fresh certified-claim or lifecycle state change (B-305), critical data anomaly (B-113). Every template is factual-declarative; a unit test (`test_alert_templates_no_imperatives`) asserts no banned verbs ("sell", "buy", "exit", "act now").

**Why it protects capital:** the owner cannot watch the board all day; the dangerous events (breach, phase turn, NO-GO) must find them. Factual wording keeps it decision-quality.

**Data / plugs in at:** existing payloads (readiness history, phase timeline, watchlist + snapshots, ledger/lifecycle, sentinel); new `alerts` append-only table + job (data_manager job pattern); `/alerts` inbox UI + badge in nav; optional delivery adapter.
**Config surface:** `alerts.enabled_events[...]`, `alerts.delivery: none|smtp|webhook`, environment-variable names for credentials (documented, never values).
**How:** (1) event detectors as pure functions over payload diffs (fixture-tested); (2) append + dedupe (an event fires once per state change); (3) inbox UI; (4) delivery adapter behind config; (5) template language test. Size: ~2–3 iterations; split: detectors+inbox, then delivery.

**Evidence Claim & ledger:** `N/A — this card must not introduce proven-language anywhere.`
**Canonical value:** the alerts table (append-only); readers: inbox, delivery adapter, B-1207 ack trail.
**Anti-goal boundary:** none — wording constraint is binding (see test).
**Tests that will break:** none; adds detector fixtures + the template language test.
**Do NOT touch:** secrets in files (env only — anti-goal #7); alert text free of advice.

**Acceptance / DoD:** each event type fires exactly once per state change in fixtures; inbox renders history; language test green; delivery works when configured and is silent when off.

**Ready-to-paste journey block:**
```markdown
- **J-XX: Material events reach the owner as factual alerts**
  - Steps:
    1. In a controlled environment, cause a watchlist name's close to cross below its displayed invalidation level as of the next data update; assert an alert appears in `/alerts` stating the ticker, the close, the level, and the as-of date — with no imperative verbs.
    2. Cause a phase transition in the fixture timeline; assert a phase-change alert fires once (and not again on re-runs without a change).
    3. Assert the template language test exists and passes (banned verbs absent from every template).
  - Acceptance:
    - **Consistency (single source):** alerts derive from the same canonical payloads the pages display (levels from snapshots, phases from the causal timeline); the inbox re-reads the append-only alerts table.
    - **Correctness:** the alert's numbers byte-match the source payload for the same as-of.
    - **Honest status / anti-goals:** factual-declarative wording only; deduped (no alarm spam); no credentials in source; delivery default off.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of the inbox with a breach and a phase-change alert, viewable via `demo.sh mcp-loop --session-live`.
```

**Traps:** recomputing breach levels in the alert job (read the snapshot's level); firing on every run instead of on state *change*; "helpful" phrasing drifting into advice; committing an SMTP password (env only).
**Depends on:** B-301 (verdict events), B-305 (lifecycle events) — ship with the subset that exists.

---

#### B-303 · Decision journal (decision-quality fields only) — **BOUNDARY**
**Track:** T3 · **Quarter:** Q2+ (after amendment) · **Priority:** P2 · **Status:** PROPOSED
**Difficulty:** EASY–MEDIUM · **Dominant failure mode:** boundary (quietly becoming a position ledger)

**What:** a private journal where the owner records decisions **about their own process**: date + as-of, ticker, decision kind (entered / passed / exited / reduced — as *categorical facts about the owner's choice*, no quantities or prices), thesis text, "invalidation acknowledged" checkbox, checklist adherence, free notes. Each entry deep-links the as-of snapshot so later review sees exactly what the board showed. A review view lists past entries beside what the stored snapshots showed afterward (descriptive; **no P&L computation anywhere**).

**Why it protects capital:** the loop "what did I decide, against what evidence, and what did I learn" is how a discretionary user improves. Excluding quantities/prices/P&L keeps it a *journal*, not a portfolio tracker — that exclusion is load-bearing for the anti-goals.

**Data / plugs in at:** new append-only `journal` table; UI on watchlist/detail + a `/journal` review page; snapshot deep-links via existing as-of routing.
**Config surface:** none material.
**How:** (1) amendment first; (2) schema WITHOUT qty/price/P&L columns (enforced by test); (3) entry UI + review page; (4) review view joins entries to stored snapshots (read-only). Size: ~2 iterations.

**Evidence Claim & ledger:** `N/A — this card must not introduce proven-language anywhere.`
**Canonical value:** journal rows (owner-authored facts); readers: journal page, B-1201 monthly pack (counts only).
**Anti-goal boundary:** **BOUNDARY — amendment required:**
> - **Decision-journal exception (owner-approved <date>):** the product MAY persist owner-entered decision records (date, ticker, decision category, thesis, checklist acknowledgments, free text) for later self-review, provided records contain no quantities, prices, or cost basis, and the product never computes profit/loss or portfolio value from them. *(scoped exception to "decision-quality only")*
**Tests that will break:** none; add a schema test asserting the forbidden columns don't exist and an API test rejecting quantity-like fields.
**Do NOT touch:** watchlist schema; no P&L math anywhere (also keep it out of the monthly pack — counts and adherence rates only).

**Acceptance / DoD:** entries persist and deep-link their as-of; review page renders decision vs subsequent stored snapshots; schema/API tests enforce the exclusions.

**Ready-to-paste journey block:**
```markdown
- **J-XX: A decision journal records the owner's choices — without ever becoming a position ledger**
  - Steps:
    1. Confirm goal.md carries the owner-approved decision-journal exception.
    2. From a stock detail, record a decision (category + thesis + invalidation acknowledged); assert it appears in `/journal` deep-linked to the exact as-of snapshot.
    3. Attempt to submit a quantity/price via the API; assert it is rejected.
    4. Open the review view weeks later (or with fixture time): assert it shows the entry beside what stored snapshots showed since — with no P&L or value computation anywhere.
  - Acceptance:
    - **Consistency (single source):** the review view re-reads stored snapshots for context; the journal table is append-only.
    - **Correctness:** the deep-linked snapshot is the one for the entry's as-of.
    - **Honest status / anti-goals:** complies with the scoped exception exactly (no qty/price/P&L, enforced by tests); descriptive review only.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of recording and reviewing one decision, viewable via `demo.sh mcp-loop --session-live`.
```

**Traps:** "just one" price field (the back door — refuse); computing hypothetical returns of journaled decisions (that is P&L in costume); surfacing journal stats as system performance (it measures the owner's process, nothing else).
**Depends on:** amendment approval.

---

#### B-304 · Live-vs-seed drift monitor
**Track:** T3 · **Quarter:** Q1 · **Priority:** P1 · **Status:** PROPOSED
**Difficulty:** MEDIUM · **Dominant failure mode:** data-integrity

**What:** when the live provider (`provider: stooq`) fetches new bars, three checks before the board trusts them: (a) **overlap check** — the last N common dates between fetch and committed seed must byte-match (a mismatch = the vendor re-adjusted history → adjustment seam if appended); (b) **distribution check** — today's computed score/indicator distributions vs their historical percentile envelopes (a wholesale shift = schema or adjustment break); (c) **seam scan** — B-113's detectors on the merged series' junction region. Results feed B-301; a failed overlap check forces DEGRADED with the affected symbols listed.

**Why it protects capital:** the seed is validated history; the live feed is where silent breakage enters. Stooq's whole-history re-adjustment on dividends means "append-only new rows" can create a level seam at the junction — exactly the invisible-poison case.

**Data / plugs in at:** `data_manager.run_data_job` FETCH path (post-fetch validation stage), B-113 detectors, readiness input; `/data` report section.
**Config surface:** `data_quality.drift.overlap_days`, distribution-envelope parameters, severity mapping.
**How:** (1) overlap comparator; (2) envelope stats from stored history (computed once, cached artifact); (3) junction seam scan; (4) artifact + readiness wiring + UI. Size: ~2 iterations.

**Evidence Claim & ledger:** `N/A — this card must not introduce proven-language anywhere.`
**Canonical value:** drift-report artifact; readers: data page, readiness.
**Anti-goal boundary:** none.
**Tests that will break:** none; fixtures: re-adjusted overlap → detected; shifted distribution → flagged; clean fetch → green.
**Do NOT touch:** the fetched data itself (report + gate trust; never auto-reconcile — reconciliation is an owner decision, possibly a B-112-style re-basis).

**Acceptance / DoD:** all three checks run on every FETCH; fixture matrix passes; affected-symbol lists precise; readiness reflects severity.

**Ready-to-paste journey block:**
```markdown
- **J-XX: Live data cannot silently diverge from the validated seed**
  - Steps:
    1. Run a live fetch in a controlled environment where one symbol's overlap region was re-adjusted; assert the drift report names the symbol, the mismatching dates, and classifies it as an adjustment seam.
    2. Assert readiness degrades with that reason while the mismatch stands.
    3. Run a clean fetch; assert the report is green and readiness recovers.
  - Acceptance:
    - **Consistency (single source):** the drift artifact is computed in the fetch pipeline once; data page and readiness re-read it.
    - **Correctness:** the reported mismatch dates match the fixture's construction.
    - **Honest status / anti-goals:** no auto-repair or silent acceptance; the affected names are listed; determinism preserved.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of a seam detection and the readiness effect, viewable via `demo.sh mcp-loop --session-live`.
```

**Traps:** comparing floats loosely enough to miss real seams (byte-compare the vendor strings or fixed-precision decimals, matching how the seed was written); envelope check on too-short history (floors); auto-"fixing" by re-fetching everything (that's a basis change — owner territory).
**Depends on:** B-113 detectors.

---

#### B-305 · Certified-claim lifecycle: edge health, demotion, retirement
**Track:** T3 · **Quarter:** Q2 · **Priority:** P1 · **Status:** PROPOSED
**Difficulty:** MEDIUM–HARD (policy + mechanism) · **Dominant failure mode:** scope-creep (keep the policy small and explicit)

**What:** claims are certified once but live forever; `forward_walk.py` already re-scores them on new data — nothing *acts* on it. Define the lifecycle: **active → under-review → retired**, with config-registered triggers (e.g., forward-walk score below threshold for K consecutive evaluations; reproducibility receipt drift (B-115); basis change pending) and **two-key transitions**: the system *proposes* under-review/retirement with evidence, the owner *confirms* (except basis-change auto-retire, which goal.md's reset provision already sanctions). State events append to a lifecycle log beside the ledger (the ledger itself stays append-only and untouched); badges render state: "Proven — under review (forward-walk deteriorating)"; retired claims keep their history but stop backing "Proven" anywhere.

**Why it protects capital:** a stale "Proven" badge is silent risk accumulation — the single most dangerous UI element in the product two years from now. This card is the difference between a ledger and a *living* evidence system.

**Data / plugs in at:** `forward_walk` outputs, B-115 receipts; new append-only `lifecycle-events.jsonl`; evidence resolution path (status = ledger PASS ∧ lifecycle state active/under-review; retired ⇒ "Not yet proven (retired <date>)"); `/evidence` UI states; B-302 alert events.
**Config surface:** `evidence.lifecycle.forward_walk_threshold`, `consecutive_k`, trigger enable flags.
**How:** (1) policy doc section in `/methodology` (states, triggers, who confirms); (2) event log + state resolution; (3) trigger evaluation job proposing transitions; (4) owner-confirm UI affordance (writes the confirmed event); (5) badge/status rendering + alert wiring. Size: ~3 iterations; split: policy+log+resolution, triggers, UI/confirm.

**Evidence Claim & ledger:** `N/A — this card must not introduce proven-language anywhere` (it *governs* existing proven-language).
**Canonical value:** the lifecycle state per claim (resolved in ONE place alongside evidence status); readers: every badge, evidence page, alerts, digest.
**Anti-goal boundary:** none — it strengthens anti-goal #1.
**Tests that will break:** evidence-status resolution tests (extend); frozen goldens NOT touched (ledger unchanged). Fixtures: trigger matrix → proposed transitions; retired claim → badge flips everywhere.
**Do NOT touch:** ledger rows; referee; auto-retiring without the owner's key (basis-change case excepted, already sanctioned).

**Acceptance / DoD:** policy documented; a fixture claim walks active→under-review→retired with correct badge behavior at each step; owner-confirm required and recorded; alerts fire on transitions.

**Ready-to-paste journey block:**
```markdown
- **J-XX: Certified claims age honestly — health, review, and retirement are visible states**
  - Steps:
    1. Visit `/methodology`; assert the lifecycle policy section states the three states, the registered triggers, and the two-key confirmation rule.
    2. In a controlled environment, drive a claim's forward-walk score below the threshold for K evaluations; assert the system proposes "under review", the evidence detail shows the proposal with its evidence, and the badge reads "Proven — under review".
    3. Confirm retirement as the owner; assert the claim's badges everywhere flip to "Not yet proven (retired <date>)" while its ledger history remains visible.
    4. Assert each transition appended an event to the lifecycle log and fired an alert.
  - Acceptance:
    - **Consistency (single source):** lifecycle state is resolved in one place with evidence status; every badge re-reads the resolved status; the ledger is untouched.
    - **Correctness:** trigger evaluations match the configured thresholds on fixture data.
    - **Honest status / anti-goals:** no unbacked "Proven" survives retirement; transitions are evidence-carrying and owner-confirmed; history is preserved, never rewritten.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of one full lifecycle on a fixture claim, viewable via `demo.sh mcp-loop --session-live`.
```

**Traps:** editing ledger rows (append lifecycle events instead); auto-retirement without the owner key; forgetting one badge reader (the resolution must be central so this is impossible — if any surface resolves proven-ness itself, that surface is the bug); alarm-threshold tuning to avoid uncomfortable reviews (thresholds are pre-registered config).
**Depends on:** forward_walk (exists), B-115 (enriches triggers), B-302 (alerts).

---

#### B-306 · Engine-version stamping + mixed-version policy
**Track:** T3 · **Quarter:** Q2 · **Priority:** P2 · **Status:** PROPOSED
**Difficulty:** EASY–MEDIUM · **Dominant failure mode:** data-integrity

**What:** stamp every new `ScannerRun` with an **engine identity hash** (engine source files + the scoring-relevant config subset). A report shows the version composition of stored history; policy (documented in methodology + enforced as a readiness input): when a scoring-affecting change ships, historical snapshots become *mixed-version* — the policy names the sanctioned responses (full re-scan job, or explicit disclosure banner on affected eras) and B-103's time-machine audit uses the stamp to classify diffs ("expected: engine changed" vs "unexplained").

**Why it protects capital:** without stamps, an engine change quietly turns the evidence pool into apples-and-oranges and nobody can prove when it happened. This is provenance for computations, complementing data provenance (`meta.json`).

**Data / plugs in at:** `scanner.py` run creation (additive column), hash helper (deterministic file+config digest), `/data` or `/scanner-runs` version report, readiness input, B-103 classification.
**Config surface:** list of files/config-keys included in the hash (explicit, versioned).
**How:** (1) hash helper + stamp; (2) composition report; (3) policy doc; (4) readiness flag when latest snapshot's version ≠ current engine (means: displayed board computed by older code). Size: ~1–2 iterations.
**Evidence Claim & ledger:** `N/A — must not introduce proven-language.`
**Canonical value:** the stamp per run; readers: reports, B-103, readiness.
**Anti-goal boundary:** none. **Tests:** hash determinism fixture; stamp presence on new runs. **Do NOT touch:** historical rows (old runs simply lack stamps — render "pre-stamping era", never backfill fake stamps).
**Acceptance / DoD:** new runs stamped; report shows composition; policy documented; readiness reflects current-vs-latest mismatch.

**Ready-to-paste journey block:**
```markdown
- **J-XX: Every snapshot names the engine that computed it, and mixed history is disclosed**
  - Steps:
    1. Trigger a new scan; assert the run records an engine identity hash and `/scanner-runs` displays it.
    2. Visit the version-composition report; assert it shows which date ranges of stored history were computed under which engine identity, with pre-stamping history labeled as such.
    3. Assert the documented mixed-version policy names the sanctioned responses to a scoring-affecting change.
  - Acceptance:
    - **Consistency (single source):** the stamp is computed once at run creation; all displays re-read it.
    - **Correctness:** re-hashing the same tree reproduces the stamp (determinism).
    - **Honest status / anti-goals:** old rows are labeled, never backfilled; disclosure over silence.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of the stamp and the composition report, viewable via `demo.sh mcp-loop --session-live`.
```

**Traps:** hashing the whole repo (noisy — the explicit file/key list is the contract); "backfilling" stamps onto old rows (fabrication); forgetting config in the hash (two engines with different weights are different engines).
**Depends on:** none; B-103 and B-112 consume it.

---

#### B-307 · Weekly evidence digest *(condensed)*
**Track:** T3 · **Quarter:** Q2 · **Priority:** P2 · **Status:** PROPOSED
**Difficulty:** EASY · **Dominant failure mode:** UI-recompute (compose, don't recompute)

**What & why:** a generated weekly artifact (markdown/HTML under a reports path, listed in-app): readiness history for the week, phase/regime narrative (factual), setup-status deltas, watchlist events (breaches, adds), evidence changes (new claims, lifecycle transitions, forward-walk movements), data-quality notes, certification-budget spend (B-903). The owner's Monday-morning five-minute read. **Everything is re-read from existing artifacts; the digest computes nothing new.**
**How:** digest job + template + `/reports` list UI. Size: ~1–2 iterations.
★ **Evidence Claim:** `N/A — must not introduce proven-language.` ★ **Canonical value:** none new (a composition). ★ **Boundary:** none — language rules apply (factual, no advice). ★ **Tests:** template language test (share B-302's banned-verb list); golden digest on fixture state. ★ **Do NOT touch:** source artifacts.
**Journey (paste-ready):**
```markdown
- **J-XX: A weekly digest composes the week's material facts in five minutes of reading**
  - Steps:
    1. Generate the digest for a fixture week; assert it contains: readiness summary, phase/regime changes, setup deltas, watchlist events, evidence/lifecycle changes, data-quality notes, and budget spend — each traceable to its source surface.
    2. Assert every number in the digest matches its source payload (spot-check two).
    3. Assert the digest renders in-app under reports and contains no imperative verbs.
  - Acceptance:
    - **Consistency (single source):** the digest re-reads canonical artifacts; zero new computation.
    - **Correctness:** spot-checked figures byte-match sources.
    - **Honest status / anti-goals:** factual narrative; degraded weeks are stated plainly; no advice.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of one digest, viewable via `demo.sh mcp-loop --session-live`.
```
**Traps:** recomputing stats "for convenience"; smoothing bad weeks into pleasant prose. **Depends on:** richer once B-301/305/903 exist; can ship earlier with fewer sections.

---

#### B-308 · Backup / disaster-recovery runbook *(condensed)*
**Track:** T3 · **Quarter:** Q1 · **Priority:** P2 · **Status:** PROPOSED
**Difficulty:** EASY · **Dominant failure mode:** scope-creep (keep it boring)

**What & why:** the DB is rebuildable from the seed, but the **ledgers, lifecycle log, journal, alerts, and state files are not** — they are the system's irreplaceable memory. Nightly backup script (DB snapshot + `state/*.jsonl` + journal) with rotation, `PRAGMA integrity_check`, and a **documented, fixture-tested restore drill**. Runbook page in docs.
**How:** script + cron/systemd note + restore test on fixtures + runbook. Size: ~1 iteration.
★ **Evidence Claim:** `N/A`. ★ **Canonical value:** none. ★ **Boundary:** none. ★ **Tests:** restore-drill fixture test (backup → wipe sandbox → restore → byte-compare state files). ★ **Do NOT touch:** originals during restore drills (sandbox only).
**Journey (paste-ready):**
```markdown
- **J-XX: The system's irreplaceable memory survives a disk loss (backup + restore drill)**
  - Steps:
    1. Run the backup; assert the archive contains the DB and every state artifact (ledgers, lifecycle, journal, alerts) with a manifest and integrity-check result.
    2. In a sandbox, restore from the archive; assert the state files byte-match the originals and the app boots against the restored DB.
    3. Assert the runbook documents schedule, rotation, and the restore steps just executed.
  - Acceptance:
    - **Consistency (single source):** the manifest lists exactly the canonical state files; restore reproduces them verbatim.
    - **Correctness:** byte-compare passes in the drill.
    - **Honest status / anti-goals:** no credentials in the runbook; drill uses a sandbox.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of backup output and the drill result, viewable via `demo.sh mcp-loop --session-live`.
```
**Traps:** backing up the DB but not `state/` (the ledgers ARE the product's honesty); untested restores. **Depends on:** none.

---

#### B-309 · Universe-pool refresh runbook *(condensed)*
**Track:** T3 · **Quarter:** Q3 · **Priority:** P2 · **Status:** PROPOSED
**Difficulty:** MEDIUM · **Dominant failure mode:** data-integrity (an "innocent" pool add is a basis change)

**What & why:** `universe_pool.csv` is a frozen "current members" list that stales as indexes rebalance. Define the semi-annual refresh: fetch current constituents, diff against the pool, and — the load-bearing step — run a **dry-run impact report** BEFORE committing: each added name brings its full history, which shifts decile boundaries, cohort stats, and potentially certified-claim inputs. The report quantifies those shifts; the owner approves; the refresh lands alone in its window (the one-basis-change rule), with pins refreshed per the sanctioned procedure.
**How:** diff tool + dry-run impact job (sandbox DB) + runbook + first executed refresh. Size: ~2 iterations.
★ **Evidence Claim:** `N/A`. ★ **Canonical value:** none new. ★ **Boundary:** none (paid not needed; constituents from the same public sources the pool was built from). ★ **Tests:** impact-report fixture (add a synthetic name → report shows the shifts). ★ **Do NOT touch:** the pool without the report + owner approval; other basis-sensitive work in the same window.
**Journey (paste-ready):**
```markdown
- **J-XX: Universe-pool refreshes are impact-assessed, owner-approved, and isolated**
  - Steps:
    1. Run the pool-refresh dry run; assert it lists adds/removes and quantifies the impact on decile boundaries and flagship cohort statistics BEFORE any commit.
    2. Apply an approved refresh; assert the membership timeline reflects new names at their true first bars and the impact report is archived.
    3. Assert the runbook states the cadence, the approval gate, and the one-basis-change-per-window rule.
  - Acceptance:
    - **Consistency (single source):** membership still resolves solely through the resolver over the (new) pool.
    - **Correctness:** the applied diff matches the approved report.
    - **Honest status / anti-goals:** no silent pool edits; shifts disclosed before commitment; determinism preserved.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of the dry-run report and the applied refresh, viewable via `demo.sh mcp-loop --session-live`.
```
**Traps:** treating a pool add as harmless (it back-propagates through 30 years of deciles); refreshing in the same window as any other basis work. **Depends on:** iter-18 membership machinery.

## Track 4 — Research depth on existing machinery

All alpha-flavored work in one place, in three tiers: (a) the four directions goal.md itself defers to "later phases" (`docs/goal.md:452-454`) — start here, they are pre-sanctioned; (b) new pre-registered hypotheses; (c) ◇ descriptive labs that cannot "fail" (the attrition buffer); plus (d) the **adaptive-methodology arc** — the deepest and most dangerous work in this file, gated hardest.

**Standard claim flow for every card in this track unless stated otherwise:** ONE pre-registered hypothesis → **staging ledger** → on FAIL/INSUFFICIENT: graveyard, update the card, move on (the descriptive table still ships) → promotion to canonical only by owner decision with recorded rationale. New factors follow the **new-factor recipe** (Appendix D §D6). Mirror each new candidate row into `project-extensions/proposer-guidance.md` §4.x per house convention.

| Card | Title | Pri | Qtr |
|------|-------|-----|-----|
| B-401 | Quantile-spread (D10−D1) evidence | P1 | Q2 |
| B-402 | Factor×regime conditioned claims | P1 | Q2 |
| B-403 | Sector event-study cohorts | P2 | Q3 |
| B-404 | Scoped α-split hypothesis families | P2 | Q3 |
| B-405 | Phase-conditioned certified edge: recovery-turn | P1 | Q2–Q3 |
| B-406 | Held-proposals revisit protocol | P1 | Q2 |
| B-407 | New factor: residual momentum | P2 | Q4 |
| B-408 | New factor: momentum path-quality (frog-in-the-pan) | P2 | Q4 |
| B-409 | Short-term reversal entry overlay (needs B-101) | P3 | Q4 |
| B-410 | Defensive low-downside-vol cohort evidence | P2 | Q3 |
| B-411 | Seasonality scan — strictly bounded | P3 | Q4 |
| B-412 | New factor: Amihud illiquidity (honest long-shot) | P3 | Q4 |
| B-413 | Signal-decay / optimal-cadence study | P2 | Q3 |
| B-414 | Breadth-thrust event study | P3 | Q3 |
| B-415 | ◇ Setup-status transition study | P2 | any |
| B-416 | ◇ Score noise-floor study | P2 | any |
| B-417 | ◇ Cross-sectional dispersion monitor | P3 | any |
| B-418 | ◇ Multi-day follow-through entry study | P2 | any |
| B-419 | ◇ Index-membership event study | P3 | any |
| B-420 | ADAPTIVE: regime/phase-conditioned score weights | P2 | Q4 |
| B-421 | ADAPTIVE: factor orthogonalization / redundancy | P2 | Q3 |
| B-422 | ADAPTIVE: score-band outcome calibration | P1 | Q3 |
| B-423 | ADAPTIVE: shadow methodology-variant harness | P2 | Q4 |
| B-424 | ADAPTIVE: cost-aware setup thresholds | P2 | Q4 |

---

#### B-401 · Quantile-spread (D10−D1) evidence
**Track:** T4 · **Quarter:** Q2 · **Priority:** P1 · **Status:** PROPOSED
**Difficulty:** MEDIUM · **Dominant failure mode:** p-hack

**What:** today's certified cohorts are single deciles (D10). A quantile **spread** (D10 minus D1 of the same factor) is the standard academic form: it nets out market drift and tests whether the factor *orders* the cross-section. Extend the claim grammar with `slice_kind: "decile_spread"` (cohort = per-date D10 mean minus D1 mean), the referee consuming the differential series, and the factor lab displaying spread rows. Pre-register TWO spreads maximum, chosen from already-certified factors (e.g., `vcp_contraction` h20, `rs_spy_3m` h60) — factors whose D10 already passed, asking the sharper question "is it ordering, not just a good top bucket?"

**Why it protects capital:** a D10 edge that vanishes in spread form was probably market beta in costume; a spread-confirmed factor is structurally stronger evidence for leaning on that factor's top decile.

**Data / plugs in at:** stored deciles + `forward_returns`; `triad_scan.py` selector translation, `referee.py` cohort extraction (differential series), `drill_samples` grammar, factor-lab UI spread rows. Sanctioned by goal.md's deferred list.
**Config surface:** the two pre-registered spread candidates in `config.triad.candidates` form (mirrored to proposer-guidance §4.1 style).
**How:** (1) grammar + extraction for spreads (fixture: constructed factor where D10−D1 is positive by design); (2) the two claims through staging; (3) lab spread rows with badges resolving through the existing evidence path. Size: ~2 iterations.

**Evidence Claim & ledger:** staging; 2 trials (registered together); on FAIL → graveyard per spread.
```json
{"kind": "factor", "factor": "vcp_contraction", "slice_kind": "decile_spread", "deciles": [10, 1], "horizon": 20, "direction": "positive"}
```
```json
{"kind": "factor", "factor": "rs_spy_3m", "slice_kind": "decile_spread", "deciles": [10, 1], "horizon": 60, "direction": "positive"}
```
**Canonical value:** spread cohort stats via existing lab payloads; badges via existing evidence resolution.
**Anti-goal boundary:** none.
**Tests that will break:** `drill_samples`/staging-routing grammar tests — extend with the new `slice_kind` (fixtures).
**Do NOT touch:** existing D10 claims; the candidate list after registration.

**Acceptance / DoD:** spread rows render with n/CI; two verdicts recorded; badges correct for PASS and non-PASS.

**Ready-to-paste journey block:**
```markdown
- **J-XX: Factor evidence graduates to quantile spreads (D10−D1)**
  - Steps:
    1. The iteration carries a machine-readable `## Evidence Claim` for a pre-registered decile-spread cohort —
       `{"kind":"factor","factor":"vcp_contraction","slice_kind":"decile_spread","deciles":[10,1],"horizon":20,"direction":"positive"}` —
       routed to the staging ledger; the post-decompose gate referees it BEFORE any code is built; a non-PASS verdict blocks the iteration.
    2. Visit `/research/factor-lab` for the factor; assert a spread row (D10−D1) renders with its per-date differential statistics, sample size, and confidence interval.
    3. Assert the spread row's evidence badge resolves through the existing evidence-status path ("Proven" only on a PASS entry; otherwise "Not yet proven").
  - Acceptance:
    - **Consistency (single source):** the spread series is computed once by the referee/lab extraction; the badge resolves via the existing evidence payload; no new serving endpoint.
    - **Correctness:** one date's D10−D1 value re-verified from stored deciles matches.
    - **Honest status / anti-goals:** only the pre-registered spreads are tested; a FAIL renders honestly; no return promises.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of the spread row and its badge, viewable via `demo.sh mcp-loop --session-live`.
```

**Traps:** testing spreads of many factors "while we're at it" (two, registered, period); building the differential from misaligned dates (both legs must exist on the same date or the date is dropped — document the rule); interpreting spread PASS as licence to short D1 (the product is long-only decision support; the spread is evidence about ordering, and the journey must not add short-side language).
**Depends on:** none.

---

#### B-402 · Factor×regime conditioned claims
**Track:** T4 · **Quarter:** Q2 · **Priority:** P1 · **Status:** PROPOSED
**Difficulty:** MEDIUM · **Dominant failure mode:** p-hack (the conditioning grid explodes combinatorially — fixed candidates only)

**What:** goal.md's deferred list says "regime conditioning (reuse the `regime-phase-factor` kind first)". Pre-register a SMALL candidate set (≤3) of factor×regime cohorts with economic rationales — e.g., `rs_spy_3m` D10 conditioned on **Risk-on regimes** (relative strength should work best when breadth supports it), `vcp_contraction` D10 in **Choppy/Narrow** regimes (contraction setups resolve better from consolidation tape). Route through staging; surface in the regime-phase-factor lab with regime-scoped badges (J-04's display convention already exists).

**Why it protects capital:** conditioning tells the owner WHEN a factor deserves weight — and B-109 will already have shown which unconditional claims have thin bad-phase evidence; this is its constructive counterpart.

**Data / plugs in at:** existing `regime-phase-factor` 3-way machinery, stored regime series, triad candidates config; referee via standard gate.
**Config surface:** the ≤3 registered rows with rationale strings.
**How:** (1) register candidates (config + proposer-guidance mirror); (2) claims through staging (the referee already counts independent holdout DATES — regime-conditioning thins dates; expect INSUFFICIENT on rare regimes and accept it); (3) lab/badge surfacing. Size: ~2 iterations.

**Evidence Claim & ledger:** staging; ≤3 trials; on FAIL/INSUFFICIENT → graveyard (an INSUFFICIENT on a rare regime is an honest "not enough history", not an invitation to loosen the referee).
```json
{"kind": "regime-phase-factor", "factor": "rs_spy_3m", "slice_kind": "decile", "decile": 10, "regime": "risk_on", "horizon": 60, "direction": "positive"}
```
**Canonical value:** conditioned cohort stats via the existing lab; badges regime-scoped per J-04 convention.
**Anti-goal boundary:** none.
**Tests that will break:** selector-grammar tests if the kind's config form extends (fixtures).
**Do NOT touch:** the candidate set after registration; regime label definitions (conditioning consumes them, never adjusts them to help a claim).

**Acceptance / DoD:** ≤3 verdicts recorded; regime-scoped badges correct; INSUFFICIENT outcomes displayed as such in the lab.

**Ready-to-paste journey block:**
```markdown
- **J-XX: A factor edge is certified conditional on market regime, honestly scoped**
  - Steps:
    1. The iteration carries a machine-readable `## Evidence Claim` —
       `{"kind":"regime-phase-factor","factor":"rs_spy_3m","slice_kind":"decile","decile":10,"regime":"risk_on","horizon":60,"direction":"positive"}` —
       from the pre-registered candidate set, routed to staging; the gate referees it BEFORE code; non-PASS blocks.
    2. Visit `/research/regime-phase-factor`; assert the conditioned cohort renders its stats with the regime named, sample size, and CI.
    3. Assert its badge is regime-scoped (per the J-04 convention) and reads "Proven" only from a PASS entry; other regimes for the same factor read "Not yet proven".
  - Acceptance:
    - **Consistency (single source):** conditioned stats come from the existing 3-way lab computation; badges resolve through the existing evidence path.
    - **Correctness:** one conditioned cell re-verified offline matches; regime labels join causally (label as-of each date).
    - **Honest status / anti-goals:** only registered candidates tested; thin regimes render INSUFFICIENT honestly; scope labels always visible.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of the conditioned cohort and its scoped badge, viewable via `demo.sh mcp-loop --session-live`.
```

**Traps:** scanning the full factor×regime cross-product (the named anti-pattern — registered rows only); joining regimes retrospectively (causal series only); reacting to INSUFFICIENT by merging regimes post hoc (that's a new hypothesis — register or drop).
**Depends on:** B-109 (context; not blocking).

---

#### B-403 · Sector event-study cohorts *(medium detail)*
**Track:** T4 · **Quarter:** Q3 · **Priority:** P2 · **Status:** PROPOSED
**Difficulty:** MEDIUM · **Dominant failure mode:** p-hack (11 sectors × anything = a scan)

**What:** the last goal-sanctioned deferred item: event-study cohorts sliced by sector. Pre-register ≤2 sector-scoped hypotheses with real rationales — e.g., VCP-pattern events in **Technology** (growth names consolidate then trend more cleanly than utilities) at h=20. Uses the event-study lab's sector slice; standard staging flow.
**Why:** sector context is the owner's daily mental model; sector-scoped evidence makes the sector pages more than descriptive.
**Plugs in at:** event-study lab + sector slice selectors (goal.md names this the intended reuse); B-114's sector-map caveat applies — carry its footnote on deep history.
**Config:** ≤2 registered rows. **How:** register → staging claims → sector-page badge linkage. Size: ~1–2 iterations.
**Evidence Claim & ledger:** staging; ≤2 trials; FAIL → graveyard.
```json
{"kind": "event-study", "subject": "vcp", "sector": "technology", "horizon": 20, "direction": "positive"}
```
**Canonical value:** existing lab payloads. **Boundary:** none. **Tests:** selector grammar fixtures. **Do NOT touch:** sector map (B-114 owns its honesty).
**Acceptance / DoD:** ≤2 verdicts; sector-scoped badges; deep-history footnote present.
**Journey (paste-ready):**
```markdown
- **J-XX: A sector-scoped event edge is certified with honest sector-map caveats**
  - Steps:
    1. The iteration carries `{"kind":"event-study","subject":"vcp","sector":"technology","horizon":20,"direction":"positive"}` from the registered set, routed to staging; the gate referees BEFORE code; non-PASS blocks.
    2. Visit the event-study lab filtered to the sector; assert cohort stats render with n/CI and the sector-map caveat footnote for deep history.
    3. Assert the sector page links the claim and its badge resolves through the existing evidence path.
  - Acceptance:
    - **Consistency (single source):** sector slicing uses the existing lab selectors; badges via existing resolution.
    - **Correctness:** one cohort stat re-verified offline matches.
    - **Honest status / anti-goals:** only registered sector hypotheses tested; caveat displayed; non-PASS honest.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of the sector-scoped study, viewable via `demo.sh mcp-loop --session-live`.
```
**Traps:** running all 11 sectors and reporting the best (the textbook sin); ignoring B-114 (today's sector labels are wrong deep in history — the footnote is mandatory).
**Depends on:** B-114 (caveat text).

---

#### B-404 · Scoped α-split hypothesis families *(medium detail)*
**Track:** T4 · **Quarter:** Q3 · **Priority:** P2 · **Status:** PROPOSED
**Difficulty:** MEDIUM · **Dominant failure mode:** scope-creep (this is governance plumbing, not new claims)

**What:** the fourth sanctioned item: partition the certification budget into **named hypothesis families** (e.g., `factor-decile`, `spreads`, `conditioned`, `events`, `fundamental`) with per-family α allocations, so one family's heavy testing doesn't consume the whole system's credibility budget. Extend ledger rows with a `family` field, the deflation accounting to operate per family scope (each family's Bonferroni divisor counts its own trials; the global honesty story documented), and the budget UI (B-903) to show spend per family.
**Why:** it makes the year's research *sustainable* — Track 5's fundamental factors shouldn't tighten the bar retroactively for Track 4's spreads, and vice versa; and it makes "we can afford N more tests this quarter" a per-lane answer.
**Plugs in at:** `referee.py` deflation accounting, `ledger.py` row schema (additive field), `verify_claim.py` gate (family from the claim JSON), B-903 UI.
**Config:** family definitions + α allocations (owner-approved; documented in methodology).
**How:** (1) design note in methodology (the statistical story must be written BEFORE code); (2) additive schema + per-family accounting; (3) gate parsing; (4) budget UI. Size: ~2 iterations.
**Evidence Claim & ledger:** `N/A` itself (infrastructure) — but every future claim JSON gains an optional `"family"` selector documented in Appendix C.
**Canonical value:** per-family spend figures (B-903 payload). **Boundary:** none. **Tests:** staging-routing + ledger tests extend (fixtures asserting per-family divisors). **Do NOT touch:** existing rows (they keep their recorded global deflation — honest history; only NEW rows carry families).
**Acceptance / DoD:** methodology documents the scheme; new claims carry families; per-family divisors verified in fixtures; budget UI splits spend.
**Journey (paste-ready):**
```markdown
- **J-XX: The certification budget is partitioned into named hypothesis families**
  - Steps:
    1. Visit `/methodology`; assert the α-split scheme is documented: family names, allocations, and how per-family deflation composes with the global honesty story.
    2. Submit (in a controlled test) a staging claim carrying `"family":"spreads"`; assert its recorded `required_p` reflects the family's own trial count and allocation.
    3. Visit the budget view; assert spend renders per family and historical (pre-family) rows are labeled as global-scheme entries.
  - Acceptance:
    - **Consistency (single source):** family accounting lives in the referee/ledger layer only; the UI re-reads it.
    - **Correctness:** fixture divisors match hand computation.
    - **Honest status / anti-goals:** existing rows unmodified; the scheme never loosens any existing verdict; every verdict still records its deflation and required_p for audit.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of the family view, viewable via `demo.sh mcp-loop --session-live`.
```
**Traps:** using the split to *retry* dead hypotheses under a fresh family (graveyard is global); allocating α after seeing which family is "hot" (allocations are set at registration, changed only at quarterly reviews with rationale).
**Depends on:** B-903 (UI home); design note first.

---

#### B-405 · Phase-conditioned certified edge: recovery-turn
**Track:** T4 · **Quarter:** Q2–Q3 · **Priority:** P1 · **Status:** PROPOSED
**Difficulty:** MEDIUM · **Dominant failure mode:** small-n honesty (recoveries are rare)

**What:** the market-phase machinery (the owner's earlier direction) produced a **recovery-turn signal** (P(bear) crosses below 0.40 while the index reclaims its 50-day trailing MA) and a downtrend-episode study — as labs, never as certified evidence. Pre-register ONE claim: recovery-turn events are followed by positive index-cohort forward returns at h=60 vs control. Route staging. Surface the verdict on the recovery-turn lab and the market-phase panel (badge per house convention). Expect modest n (recoveries are rare — 30y basis helps: 2000, 2008, 2011, 2018, 2020, 2022); if INSUFFICIENT, display that honestly — "signal exists, evidence insufficient" is a legitimate, valuable state.

**Why it protects capital:** re-entering after a bear is the second-hardest decision (after exiting into one); a certified — or honestly uncertified — recovery signal calibrates it.

**Data / plugs in at:** existing recovery-turn detection (causal), index bars, event-study machinery, referee gate.
**Config surface:** one registered candidate row.
**How:** enumerate historical recovery-turn dates from the causal series → event cohort → claim → badge. Size: ~1–2 iterations.
**Evidence Claim & ledger:** staging; 1 trial; INSUFFICIENT is a likely and acceptable outcome — record it, keep the lab descriptive.
```json
{"kind": "event-study", "subject": "recovery_turn", "horizon": 60, "direction": "positive"}
```
**Canonical value:** existing lab payloads + evidence resolution. **Boundary:** none. **Tests:** selector fixtures. **Do NOT touch:** recovery-turn thresholds (0.40 / 50-day are config — tuning them to fatten the event list is p-hacking).
**Acceptance / DoD:** verdict recorded; badge on lab + phase panel correct for the actual outcome; event list visible with dates.

**Ready-to-paste journey block:**
```markdown
- **J-XX: The recovery-turn signal carries certified (or honestly insufficient) evidence**
  - Steps:
    1. The iteration carries `{"kind":"event-study","subject":"recovery_turn","horizon":60,"direction":"positive"}` (pre-registered), routed to staging; the gate referees BEFORE code; non-PASS blocks (an INSUFFICIENT outcome may instead ship as a no-claim iteration displaying the insufficiency).
    2. Visit `/research/recovery-turn-edge`; assert the historical event dates render with cohort forward stats, n, and CI.
    3. Visit `/market-phase`; assert the recovery-turn signal's description carries the evidence badge resolved from the ledger ("Proven" only on PASS; otherwise "Not yet proven", including the insufficient case with its n).
  - Acceptance:
    - **Consistency (single source):** event dates come from the stored causal phase series; stats from the existing lab computation; badge via existing resolution.
    - **Correctness:** the event-date list matches the causal series exactly.
    - **Honest status / anti-goals:** rare-event thinness is displayed, never padded; thresholds untouched; no timing advice language.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of the event list and the phase-panel badge, viewable via `demo.sh mcp-loop --session-live`.
```
**Traps:** widening the signal definition to harvest more events (fixed config); overlapping-event double counting; reading INSUFFICIENT as failure (it is honest scarcity — say exactly that in the UI).
**Depends on:** 30y basis (more historical recoveries).

---

#### B-406 · Held-proposals revisit protocol
**Track:** T4 · **Quarter:** Q2 · **Priority:** P1 · **Status:** PROPOSED
**Difficulty:** EASY (procedure) · **Dominant failure mode:** p-hack (retry laundering)

**What:** the enhancement-proposals backlog holds scored survivors that were never promoted. Codify the revisit rule and apply it once: a held/graveyarded hypothesis may be re-tested ONLY when a **material precondition changed** — new data span covering ≥2 additional years OOS, a data-basis change (the iter-18 30y swap qualifies — it reset the ledgers), or a genuinely different hypothesis — and the revisit is recorded as a NEW registered candidate citing the old verdict. Apply the protocol now to the held list: **eligible after the basis change:** `high_proximity` D10 (was the strongest positive-IC candidate) — register and run once through staging; `leadership_score` h60 (held for badge-interaction reasons — needs an owner UX decision first, not statistics); the **term-structure panel** (a view, not a claim — build when ≥3 factors hold multi-horizon claims). **Stay dead:** `ma_stack` (closed FAIL — permanent), `hv` D10 (drawdown-toxic), `up_down_vol` (weak), `entry_quality` inverse (confusing-UX, owner explicitly not interested unless re-raised).

**Why it protects capital:** the graveyard only works if there's a wall between "new evidence justifies one more look" and "keep rolling until it passes". This card IS the wall, written down.

**Plugs in at:** this document (protocol §0 cross-ref), proposer-guidance §4.x (registered revisit rows), standard gate.
**Evidence Claim & ledger:** for the one eligible revisit now: staging; 1 trial.
```json
{"kind": "factor", "factor": "high_proximity", "slice_kind": "decile", "decile": 10, "horizon": 20, "direction": "positive"}
```
**Canonical value:** none new. **Boundary:** none. **Tests:** none. **Do NOT touch:** closed-FAIL entries (no basis change resurrects a *closed* referee FAIL unless the owner explicitly rules the old verdict inapplicable and records why).
**Acceptance / DoD:** protocol text merged into §0/this card; revisit rows registered with citations; the high_proximity verdict recorded either way.
**Journey (paste-ready):**
```markdown
- **J-XX: A held proposal is revisited under the recorded revisit protocol (high_proximity)**
  - Steps:
    1. The iteration carries `{"kind":"factor","factor":"high_proximity","slice_kind":"decile","decile":10,"horizon":20,"direction":"positive"}`, registered as a protocol-compliant revisit (citing the pre-basis-change context), routed to staging; the gate referees BEFORE code; non-PASS blocks.
    2. Visit `/research/factor-lab` for high_proximity; assert its top-decile cohort renders with the verdict-backed badge state.
    3. Assert the revisit registration (old context cited, new precondition named) is visible in the pre-registration record.
  - Acceptance:
    - **Consistency (single source):** standard lab payload + evidence resolution.
    - **Correctness:** cohort stats re-verify offline.
    - **Honest status / anti-goals:** the revisit is registered with its justification; a FAIL closes it; no serial retries.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of the revisited cohort and its registration note, viewable via `demo.sh mcp-loop --session-live`.
```
**Traps:** treating every quarter as a "material change" (the protocol names what qualifies); reviving closed FAILs; skipping the citation (the registry must show the full lineage).
**Depends on:** iter-18 (the qualifying basis change).

---

#### B-407 · New factor: residual momentum *(full exemplar of the new-factor recipe — B-408/409/410/412 follow the same path)*
**Track:** T4 · **Quarter:** Q4 · **Priority:** P2 · **Status:** PROPOSED
**Difficulty:** MEDIUM · **Dominant failure mode:** lookahead (beta estimation window)

**What:** plain momentum (rs_spy) mixes stock-specific strength with market beta — in rallies, high-beta junk tops the ranks. **Residual momentum** regresses each name's daily returns on SPY over a trailing window (e.g., 252d, ending at as-of), then ranks by the **cumulative residual** over the momentum window (e.g., trailing 126d minus the most recent 21d, the standard skip-month). Economic rationale: stock-specific momentum (analyst underreaction, fundamental drift) persists; beta-driven momentum mean-reverts with the market — residual momentum historically carries similar return with materially lower drawdowns (Blitz et al.). Implement per the **new-factor recipe (Appendix D §D6)**: pure indicator → stored factor → factor-lab visibility (descriptive first) → ONE pre-registered staging claim.

**Data / plugs in at:** existing bars; `indicators.py` (rolling regression helper — keep it simple OLS, window from config), `scoring.py:368` stored-factors block, `config.research.factor_lab.factors` entry, methodology entry.
**Config surface:** `indicators.resid_momentum: {beta_window: 252, momentum_window: 126, skip_days: 21}`.
**How:** recipe steps 1–6 (§D6); then the claim. Size: ~2 iterations (factor+lab, then claim).
**Evidence Claim & ledger:** staging; 1 trial; FAIL → graveyard (factor stays visible in the lab as descriptive).
```json
{"kind": "factor", "factor": "resid_momentum", "slice_kind": "decile", "decile": 10, "horizon": 60, "direction": "positive"}
```
**Canonical value:** the stored factor column (computed at snapshot time); readers: factor lab (and nothing else until certified + owner decision).
**Anti-goal boundary:** none.
**Tests that will break:** methodology completeness (add the entry); factor-lab config tests (additive).
**Do NOT touch:** the three score blends (a new factor NEVER enters scoring by default — that requires certification + an explicit owner decision + the adaptive-arc shadow process).

**Acceptance / DoD:** factor computes NA-gracefully for short-history names (needs beta_window + momentum_window bars); decile monotonicity visible in lab (or honestly not); claim verdict recorded.

**Ready-to-paste journey block:**
```markdown
- **J-XX: Residual momentum joins the factor lab with pre-registered evidence**
  - Steps:
    1. The iteration carries `{"kind":"factor","factor":"resid_momentum","slice_kind":"decile","decile":10,"horizon":60,"direction":"positive"}` (pre-registered with its economic rationale), routed to staging; the gate referees BEFORE code where the factor's cohort data already exist, or the claim rides the second iteration after the factor is stored — never certify on in-sample preview numbers.
    2. Visit `/research/factor-lab` for resid_momentum; assert decile rows render with n/CI and the factor's method note (beta window, momentum window, skip period).
    3. Assert names with insufficient history render NA and are excluded from deciles (never zero-filled).
    4. Assert the three displayed scores are unchanged (the factor is lab-only until a separate owner decision).
  - Acceptance:
    - **Consistency (single source):** the factor is computed once at snapshot time and stored; the lab re-reads stored values.
    - **Correctness:** one name's residual-momentum value re-verified offline (same windows, bars ≤ as-of) matches.
    - **Honest status / anti-goals:** lab-only; badge honest to the verdict; no score-blend changes; no-lookahead (all windows end at as-of).
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of the new factor's lab page, viewable via `demo.sh mcp-loop --session-live`.
```

**Traps:** estimating beta over a window that includes the as-of date's *future* bars (all windows end AT as-of); skipping the skip-month (short-term reversal contaminates it); z-scoring residuals cross-sectionally *after* seeing forward returns (any normalization is defined ex ante in the indicator).
**Depends on:** none. **Note:** this card is the exemplar — B-408/B-409/B-410/B-412 reference this structure.

---

#### B-408 · New factor: momentum path-quality ("frog in the pan") *(recipe card)*
**Track:** T4 · **Quarter:** Q4 · **Priority:** P2 · **Status:** PROPOSED · **Difficulty:** MEDIUM · **Failure mode:** p-hack (one smoothness definition, chosen ex ante)

**What & rationale:** among names with similar trailing returns, those that got there **smoothly** (many small moves — high information-discreteness in the continuous direction) historically continue better than jump-driven ones (Da/Gurun/Warachka's "frog in the pan": gradual information gets underreacted to). Factor: sign-consistency ratio = fraction of up days within the momentum window, or ID = sign(ret) × (%neg − %pos days); pick ONE definition ex ante (recommend %-up-days for explainability), stored per §D6, lab-first, then one staging claim **conditioned on positive 6m return** (the hypothesis is about *quality among movers*, not the whole universe): top-decile path-quality among positive-momentum names, h=60, positive.
**Config:** `indicators.path_quality: {window: 126, skip_days: 21, definition: "pct_up_days"}`.
**Evidence Claim & ledger:** staging; 1 trial:
```json
{"kind": "factor", "factor": "path_quality", "slice_kind": "decile", "decile": 10, "condition": ["rs_spy_6m:top:0.5"], "horizon": 60, "direction": "positive"}
```
(the `condition` leg uses the combination grammar `factor:side:quantile` that `drill_samples` already parses.)
★ **Canonical value:** stored factor; lab reader only. ★ **Boundary:** none. ★ **Tests:** methodology completeness; lab config. ★ **Do NOT touch:** score blends.
**Acceptance / DoD:** per B-407's pattern. **Journey:** copy B-407's block, substituting the factor name/claim JSON and method note (windows + definition).
**Traps:** trying both smoothness definitions and keeping the better (register ONE); conditioning leg computed at a different as-of than the factor (same snapshot).
**Depends on:** none.

---

#### B-409 · Short-term reversal entry overlay *(recipe card; realism-gated)*
**Track:** T4 · **Quarter:** Q4 · **Priority:** P3 · **Status:** PROPOSED · **Difficulty:** MEDIUM · **Failure mode:** cost-blindness (h5 edges die to timing/costs)

**What & rationale:** buying strength after a 1-week pop pays a worse price than after a quiet week; short-term reversal (weekly losers bounce) is the classic entry-timing overlay. Factor: trailing 5-day return (stored, lab-first). **Hard rule: this claim is only meaningful under the B-101 realistic convention** — close-to-close gross h5 reversal edges are exactly what next-open timing + costs erase; the referee input series for this claim must be the realistic-convention series, and the card may not proceed until B-101 exists.
**Config:** `indicators.st_reversal_window: 5`.
**Evidence Claim & ledger:** staging; 1 trial — decile-1 (weekly losers) **within quality names** (condition on Leadership top half — the hypothesis is entry timing for leaders, not knife-catching):
```json
{"kind": "factor", "factor": "st_reversal", "slice_kind": "decile", "decile": 1, "condition": ["leadership_score:top:0.5"], "horizon": 10, "direction": "positive", "convention": "next_open_net"}
```
(the `convention` selector is new — B-101 must define it in the claim grammar; document in Appendix C when built.)
★ **Canonical value:** stored factor. ★ **Boundary:** none. ★ **Tests:** grammar extension fixtures. ★ **Do NOT touch:** score blends; the gross-convention default for other claims.
**Traps:** certifying gross (the whole point is net); extending to h1 (microstructure noise, banned by the EOD non-direction).
**Depends on:** **B-101 (hard)**.

---

#### B-410 · Defensive low-downside-vol cohort evidence *(recipe card — factor already stored)*
**Track:** T4 · **Quarter:** Q3 · **Priority:** P2 · **Status:** PROPOSED · **Difficulty:** EASY–MEDIUM · **Failure mode:** honest-expectations (raw-return edge may not exist)

**What & rationale:** `downside_vol` is already computed and stored (`scoring.py:368`) — no new factor needed. The low-volatility anomaly says the LOWEST-downside-vol decile historically delivers market-like returns with materially lower drawdowns — a *capital-preservation* cohort. Register ONE claim on decile 1 (lowest downside vol), h=60, direction positive vs control — and say in the registration: the raw-return edge may honestly FAIL; the triad's drawdown/frequency profile is the real prize and ships descriptively regardless (factor-lab MDD columns already exist).
**Evidence Claim & ledger:** staging; 1 trial:
```json
{"kind": "factor", "factor": "downside_vol", "slice_kind": "decile", "decile": 1, "horizon": 60, "direction": "positive"}
```
★ **Canonical value:** existing stored factor; lab. ★ **Boundary:** none. ★ **Tests:** none new. ★ **Do NOT touch:** Risk-score weights (downside_vol feeding the Risk score is a separate adaptive-arc question).
**Traps:** flipping to decile 10 "because the signal was there" (inverse = new hypothesis); selling it as "safe stocks" in UI copy (say "historically lower drawdown cohort", n-labeled).
**Depends on:** none.

---

#### B-411 · Seasonality scan — strictly bounded *(condensed; highest p-hack risk in T4)*
**Track:** T4 · **Quarter:** Q4 · **Priority:** P3 · **Status:** PROPOSED · **Difficulty:** MEDIUM · **Failure mode:** p-hack (seasonality is the canonical false-positive factory)

**What & rationale:** calendar effects are mostly mined noise; test exactly ONE with a real prior: **turn-of-month** (last trading day + first 3 of each month, institutional flow-driven) on the index/universe at h≈4 days aggregate, event-study form, staging only. Registration text must state: no month-of-year scans, no day-of-week scans, no holiday effects — those are banned as unregistered fishing.
**Evidence Claim & ledger:** staging; 1 trial:
```json
{"kind": "event-study", "subject": "turn_of_month", "horizon": 4, "direction": "positive"}
```
★ **Canonical value:** lab payload. ★ **Boundary:** none. ★ **Tests:** selector fixture. ★ **Do NOT touch:** anything else calendar-shaped.
**Traps:** "while we're here" calendar scans; overlapping event windows double-counting.
**Depends on:** none. Expect fragility; a FAIL closes seasonality for the year.

---

#### B-412 · New factor: Amihud illiquidity — honest long-shot *(condensed recipe card)*
**Track:** T4 · **Quarter:** Q4 · **Priority:** P3 · **Status:** PROPOSED · **Difficulty:** EASY · **Failure mode:** honest-expectations

**What & rationale:** Amihud illiquidity = mean(|daily return| ÷ dollar volume) over a window — the classic illiquidity-premium measure. **In a large-cap universe the premium is weak-to-absent; register it expecting a likely FAIL** — the factor still earns its keep as a *risk/tradability descriptor* (it enriches B-210's liquidity view and T7's small-cap audit where it matters far more). Store per §D6; lab; one staging claim decile-10 (most illiquid within our universe) h=60 positive.
```json
{"kind": "factor", "factor": "amihud_illiq", "slice_kind": "decile", "decile": 10, "horizon": 60, "direction": "positive"}
```
**Config:** `indicators.amihud_window: 63`. ★ **Do NOT touch:** score blends; universe ADV gates.
**Traps:** infinity/NA handling on zero-volume days (skip them, don't zero-fill); reading a FAIL as "delete the factor" (keep it as descriptor).
**Depends on:** none. Cross-refs: B-210, B-701.

---

#### B-413 · Signal-decay / optimal-cadence study
**Track:** T4 · **Quarter:** Q3 · **Priority:** P2 · **Status:** PROPOSED
**Difficulty:** MEDIUM · **Dominant failure mode:** UI-recompute

**What:** for every lab factor: rank-IC (already computed at fixed horizons) extended into a **decay curve** — IC at h ∈ {1,5,10,20,40,60} — plus the half-life summary ("IC halves by ~h30"). One panel answering: how fast does each signal's information die, and therefore what re-scoring cadence and holding horizon does each factor actually support? Pairs with B-211's turnover view (information decay vs membership churn).

**Why it protects capital:** trading a 60-day signal weekly churns costs for nothing; trading a 10-day signal monthly holds dead weight. Cadence is a risk decision and today it's a guess.

**Data / plugs in at:** stored factors + forward returns at existing horizons (h=40 requires either adding the horizon to `walk_forward.horizons` — a config+backfill decision — or interpolating honestly by skipping it; prefer skipping, use the five existing horizons); factor-lab payload + a decay panel.
**Config surface:** none new if using existing horizons.
**How:** IC-by-horizon computation in the lab engine (reuse the existing rank-IC machinery per horizon — do not fork it); decay panel + half-life; methodology note. Size: ~1–2 iterations.
**Evidence Claim & ledger:** `N/A — must not introduce proven-language` (decay curves are descriptive; they inform owner cadence choices).
**Canonical value:** decay payload per factor; reader: factor lab. **Boundary:** none. **Tests:** fixture with constructed decaying signal → known curve. **Do NOT touch:** rank-IC definition.
**Acceptance / DoD:** every lab factor shows its decay curve with n per point; half-life stated with method note; no cadence *advice* text (numbers, not instructions).
**Journey (paste-ready):**
```markdown
- **J-XX: Every factor shows how fast its information decays across horizons**
  - Steps:
    1. Visit `/research/factor-lab` for any factor; assert a decay panel plots rank-IC across the configured horizons with sample sizes, plus a stated half-life summary.
    2. Compare a fast-decay and a slow-decay factor; assert the difference is visible and each point carries n.
    3. Assert `/methodology` documents the decay computation and its horizons.
  - Acceptance:
    - **Consistency (single source):** decay values reuse the existing per-horizon rank-IC computation; the panel re-reads one payload.
    - **Correctness:** one factor's h=20 IC matches the existing lab value exactly (same machinery).
    - **Honest status / anti-goals:** descriptive; no cadence recommendations; thin horizons NA.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of two contrasting decay curves, viewable via `demo.sh mcp-loop --session-live`.
```
**Traps:** forking a second IC implementation (reuse); adding horizons ad hoc (a horizons change is a config+backfill decision with pin consequences — separate, owner-approved).
**Depends on:** none.

---

#### B-414 · Breadth-thrust event study *(condensed)*
**Track:** T4 · **Quarter:** Q3 · **Priority:** P3 · **Status:** PROPOSED · **Difficulty:** EASY–MEDIUM · **Failure mode:** small-n honesty

**What & rationale:** the regime engine already computes universe breadth; a **breadth thrust** (Zweig form: breadth ratio crossing from <0.40 to >0.615 within 10 sessions) is a rare, historically bullish regime event. Event-study the thrust dates → forward index/universe returns. n will be SMALL (single digits over 30y) — the likely outcome is honest INSUFFICIENT, which is itself a worthwhile display ("famous signal, insufficient in-sample evidence").
```json
{"kind": "event-study", "subject": "breadth_thrust", "horizon": 60, "direction": "positive"}
```
(staging; 1 trial; INSUFFICIENT acceptable and displayed.)
**Config:** thrust thresholds as registered constants. ★ **Do NOT touch:** breadth computation. **Traps:** loosening thresholds to manufacture events; overlapping thrusts.
**Depends on:** breadth series (exists).

---

#### B-415 · ◇ Setup-status transition study *(condensed, attrition-buffer)*
**Track:** T4 · **Quarter:** any · **Priority:** P2 · **Status:** PROPOSED · **Difficulty:** EASY · **Failure mode:** UI-recompute

**What & why:** a Markov transition matrix over the 6 setup statuses at walk-forward cadence: where do `Breakout-watch` names go next, how long do names stay `Extended`, what fraction of `Avoid` names would actually have hurt (descriptive efficacy of the label), median time-in-status. Answers "what do these labels *do* over time" — pure description from stored snapshots, cannot fail, high explanatory value for the owner.
**How:** transition counting over stored `ScannerResult` sequences; one payload; a lab panel + methodology note. Size: ~1 iteration.
★ **Evidence Claim:** `N/A — must not introduce proven-language` (the `Avoid` outcome table is descriptive; a *claim* about Avoid's protective effect would be a registered event-study, cf. B-110's pattern). ★ **Canonical value:** transitions payload; lab reader. ★ **Boundary:** none. ★ **Tests:** fixture sequence → exact matrix. ★ **Do NOT touch:** `classify_setup` rules.
**Journey (paste-ready):**
```markdown
- **J-XX: Setup statuses show their transition behavior and time-in-status**
  - Steps:
    1. Visit the setup-transition panel; assert a 6×6 transition matrix renders at the walk-forward cadence with row counts, plus median time-in-status per label.
    2. Assert the post-status outcome table (e.g., what followed `Avoid`) shows distributions with n, labeled descriptive.
  - Acceptance:
    - **Consistency (single source):** one engine payload over stored snapshots.
    - **Correctness:** one matrix cell re-verified against stored sequences matches.
    - **Honest status / anti-goals:** descriptive; no label is called "proven" anything; n everywhere.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of the matrix, viewable via `demo.sh mcp-loop --session-live`.
```
**Traps:** cadence mixing (transitions defined at snapshot cadence only). **Depends on:** none.

---

#### B-416 · ◇ Score noise-floor study *(condensed, attrition-buffer)*
**Track:** T4 · **Quarter:** any · **Priority:** P2 · **Status:** PROPOSED · **Difficulty:** EASY · **Failure mode:** none serious

**What & why:** day-over-day distribution of |Δscore| per component and per composite when nothing material changed — the **noise floor**. Output: "a Leadership change under ±4 points is within normal daily jitter". Consumed by B-804 (score-diff view highlights only super-noise changes) and the owner's intuition.
**How:** consecutive-snapshot deltas over history; percentile floors per score; payload + methodology note. Size: ~1 iteration.
★ **Evidence Claim:** `N/A`. ★ **Canonical value:** noise-floor payload (B-804 reads it). ★ **Boundary:** none. ★ **Tests:** fixture with constant inputs → floor ≈ 0. ★ **Do NOT touch:** score computations.
**Journey (paste-ready):**
```markdown
- **J-XX: Score jitter has a measured noise floor**
  - Steps:
    1. Visit the noise-floor panel; assert per-score daily-change distributions render with the stated floor percentiles and window.
    2. Assert the floors are served as one payload (the score-diff view will consume the same values).
  - Acceptance:
    - **Consistency (single source):** one payload; downstream consumers re-read it.
    - **Correctness:** one score's floor re-verified offline matches.
    - **Honest status / anti-goals:** descriptive; floors labeled as historical jitter, not significance tests.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of the distributions, viewable via `demo.sh mcp-loop --session-live`.
```
**Traps:** conflating universe-membership changes with score jitter (exclude membership-change days per name). **Depends on:** none.

---

#### B-417 · ◇ Cross-sectional dispersion monitor *(condensed, attrition-buffer)*
**Track:** T4 · **Quarter:** any · **Priority:** P3 · **Status:** PROPOSED · **Difficulty:** EASY

**What & why:** time series of cross-sectional dispersion (std of universe 20d returns; interquartile range of factor values): high dispersion = a stock-picker's tape, low = index-driven. Chart + "current percentile" context chip on the dashboard. Description only.
**How:** dispersion series from stored snapshots; payload + chart + chip. Size: ~1 iteration.
★ **Evidence Claim:** `N/A`. ★ **Canonical value:** dispersion payload; dashboard + lab read it. ★ **Boundary:** none. ★ **Tests:** fixture exactness. ★ **Do NOT touch:** regime inputs (dispersion is context, not a regime component — feeding it into regime would be a registered change).
**Journey (paste-ready):**
```markdown
- **J-XX: Cross-sectional dispersion is visible as market context**
  - Steps:
    1. Visit the dashboard; assert a dispersion chip shows the current value and its historical percentile with the window named.
    2. Open the dispersion chart; assert the full series renders at walk-forward cadence.
  - Acceptance:
    - **Consistency (single source):** chip and chart re-read one payload.
    - **Correctness:** one date's value re-verified offline matches.
    - **Honest status / anti-goals:** context only; no "favorable environment" advice phrasing.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of chip + chart, viewable via `demo.sh mcp-loop --session-live`.
```
**Depends on:** none.

---

#### B-418 · ◇ Multi-day follow-through entry study *(condensed, attrition-buffer)*
**Track:** T4 · **Quarter:** any (best after B-101) · **Priority:** P2 · **Status:** PROPOSED · **Difficulty:** EASY–MEDIUM

**What & why:** when a setup flag fires at D, compare historical outcomes of entering at D+1 open vs D+2 vs D+3 (realistic convention once B-101 exists): does patience systematically cost or pay per setup type? Directly actionable *knowledge* for the owner's own timing habits — displayed as distributions, no recommendation.
**How:** event-anchored outcome table by entry lag; lab panel. Size: ~1 iteration.
★ **Evidence Claim:** `N/A` (descriptive; a lag-claim could be registered later). ★ **Canonical value:** one payload. ★ **Boundary:** none — no "wait N days" instruction text. ★ **Tests:** fixture with constructed gap pattern. ★ **Do NOT touch:** setup definitions.
**Journey (paste-ready):**
```markdown
- **J-XX: Entry-lag outcomes are measured per setup type**
  - Steps:
    1. Visit the follow-through panel; assert per-setup tables show outcome distributions for entry at D+1/D+2/D+3 with n and the return convention named.
    2. Assert no instruction language appears (distributions only).
  - Acceptance:
    - **Consistency (single source):** one engine payload from stored setups + bars.
    - **Correctness:** one cell re-verified offline matches.
    - **Honest status / anti-goals:** descriptive; convention labeled; no timing advice.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of one setup's lag table, viewable via `demo.sh mcp-loop --session-live`.
```
**Depends on:** B-101 (for the realistic convention; can ship gross-labeled before, but prefer after).

---

#### B-419 · ◇ Index-membership event study *(condensed, attrition-buffer)*
**Track:** T4 · **Quarter:** any (after B-111) · **Priority:** P3 · **Status:** PROPOSED · **Difficulty:** EASY–MEDIUM

**What & why:** S&P 500 additions/deletions are the classic flow-driven event; B-111 already ingests a historical membership list — reuse it: event-study forward returns around addition/deletion dates for names we have bars for. Data caveat carried loudly (community list imperfection + our survivor-only price coverage biases the deletion leg badly — say so; the addition leg is the readable one).
**How:** event extraction from the membership reference + lab study. Size: ~1 iteration.
★ **Evidence Claim:** `N/A` initially (data-quality caveats argue against certifying; keep descriptive). ★ **Canonical value:** one payload. ★ **Boundary:** none. ★ **Tests:** fixture events. ★ **Do NOT touch:** universe resolver (this is a study, not membership logic).
**Journey (paste-ready):**
```markdown
- **J-XX: Index-membership changes are studied with their data caveats stated**
  - Steps:
    1. Visit the membership-event study; assert addition events render forward-outcome distributions with n and the reference list's provenance note.
    2. Assert the deletion leg carries the explicit survivor-coverage caveat (delisted names absent → biased) rather than a clean-looking table.
  - Acceptance:
    - **Consistency (single source):** events come from the same reference data B-111 ingested.
    - **Correctness:** one event's date matches the reference record.
    - **Honest status / anti-goals:** caveats are load-bearing and visible; no certified language.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of the study and caveats, viewable via `demo.sh mcp-loop --session-live`.
```
**Depends on:** B-111 (reference data). B-112 would fix the deletion leg properly.

---

### The adaptive-methodology arc (B-420…B-424) — heaviest gates in this file

The product's scores, weights, and thresholds are static config. This arc asks whether they should *adapt* — the highest-ceiling and highest-overfitting-risk direction in the backlog. **Arc-wide gates, binding on every card:** (1) everything runs in the **shadow harness** (B-423) against history — live config stays byte-identical until a canonical PASS **plus** an explicit owner two-key change; (2) every variant is pre-registered here before computation (max 3 per study); (3) staging-only claims; (4) each card's registration includes the sentence "we expect most of this to fail honestly — a null result is a finding"; (5) any surviving change ships config-gated, default-off, with the old behavior one flag away.

**Recommended order:** B-422 (descriptive calibration) → B-421 (structure analysis) → B-423 (harness) → B-420 (conditioned weights) → B-424 (cost-aware thresholds).

---

#### B-422 · ADAPTIVE: score-band outcome calibration *(descriptive; do first)*
**Track:** T4 · **Quarter:** Q3 · **Priority:** P1 · **Status:** PROPOSED · **Difficulty:** EASY–MEDIUM · **Failure mode:** UI-recompute

**What & why:** what does "Leadership 82 / bucket A" *mean* in outcomes? Per score band (the existing A–E buckets) × horizon: historical forward-return distribution, hit rate, MDD — a calibration table ("A-bucket names: median +X% @h20, hit rate Y%, n=…"). Purely descriptive; instantly improves how the owner reads every number on the board, and it is the baseline any adaptive variant must beat.
**How:** band-conditioned aggregation over stored snapshots + forward returns (machinery exists); calibration panel on methodology + score tooltips. Size: ~1–2 iterations.
★ **Evidence Claim:** `N/A — must not introduce proven-language` (bands are NOT certified by this — the table is history, labeled). ★ **Canonical value:** calibration payload; readers: methodology panel, tooltips, B-423 baseline. ★ **Boundary:** none — banned phrasing: "A means you'll make X%" (historical distributions only). ★ **Tests:** fixture bands → exact table. ★ **Do NOT touch:** bucket edges.
**Journey (paste-ready):**
```markdown
- **J-XX: Score bands carry their historical outcome calibration**
  - Steps:
    1. Visit `/methodology`; assert a calibration table shows, per score band × horizon: outcome distribution summary, hit rate, max-drawdown stats, and n.
    2. Hover/expand a score on `/stocks`; assert the tooltip cites the same band figures (re-read, not recomputed).
    3. Assert wording is historical-distribution only, with the survivorship caveat carried.
  - Acceptance:
    - **Consistency (single source):** one calibration payload; tooltips re-read it.
    - **Correctness:** one band cell re-verified offline matches.
    - **Honest status / anti-goals:** no promise language; bands not presented as certified; n everywhere.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of the calibration table and one tooltip, viewable via `demo.sh mcp-loop --session-live`.
```
**Traps:** treating calibration as certification (it is descriptive history); band edges drifting (edges are config — the table names the edges it used). **Depends on:** none.

---

#### B-421 · ADAPTIVE: factor orthogonalization / redundancy analysis *(descriptive)*
**Track:** T4 · **Quarter:** Q3 · **Priority:** P2 · **Status:** PROPOSED · **Difficulty:** MEDIUM · **Failure mode:** scope-creep (analysis ONLY — no weight changes)

**What & why:** the score blends contain near-duplicates (ma_stack appears in Leadership, Entry-Quality's `structure`, and inverted in Risk's `below_ma`; rs_spy windows overlap). Compute the component-correlation structure and effective dimensionality of each blend; identify redundant pairs and dead weights (components whose removal barely moves the composite). Output: a structure report **proposing** candidate pruned blends — which become *registered variants* for B-423, never direct changes.
**How:** correlation/PCA over stored component raws; report page. Size: ~1–2 iterations.
★ **Evidence Claim:** `N/A`. ★ **Canonical value:** structure-report artifact. ★ **Boundary:** none. ★ **Tests:** fixture with a planted duplicate component → flagged. ★ **Do NOT touch:** weights, blends, config (the report proposes; B-423 tests; the owner decides).
**Journey (paste-ready):**
```markdown
- **J-XX: Score blends disclose their internal redundancy structure**
  - Steps:
    1. Visit the blend-structure report; assert per-score component-correlation matrices and an effective-dimensionality figure render, with redundant pairs highlighted.
    2. Assert proposed pruned variants are listed as registered candidates for the shadow harness — and that live weights are unchanged.
  - Acceptance:
    - **Consistency (single source):** the report re-reads one artifact over stored component values.
    - **Correctness:** one correlation re-verified offline matches.
    - **Honest status / anti-goals:** analysis only; no live changes; candidates registered before any testing.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of the structure report, viewable via `demo.sh mcp-loop --session-live`.
```
**Traps:** "just tweaking" a weight because the analysis makes it obvious (the harness + owner gate exist precisely because obvious-looking prunes overfit). **Depends on:** none.

---

#### B-423 · ADAPTIVE: shadow methodology-variant harness
**Track:** T4 · **Quarter:** Q4 · **Priority:** P2 · **Status:** PROPOSED · **Difficulty:** HARD — design discussion with the owner required · **Failure mode:** data-integrity (shadow leaking into live) + p-hack

**What:** the machinery that makes adaptive questions answerable safely: define a **methodology variant** as a config overlay (weights/thresholds diff), recompute scores/setups/cohorts under the variant across history in a **sandbox** (separate tables or DB file — zero writes to live), and compare decision-quality outcomes vs the live baseline: forward outcomes of each variant's Actionable set, drawdown profile, turnover (churn cost proxy), with CIs and walk-forward discipline (variant evaluated only on data after each simulated as-of). Max 3 registered variants per study; results feed owner decisions; **live behavior never changes here.**

**Why it protects capital:** every "should we adjust X?" question for the rest of the product's life gets a safe, honest answer path instead of a YOLO config edit. This is the capstone card of the arc — and the one that MUST be discussed with the owner before building (its design decides how trustworthy every later comparison is).

**Data / plugs in at:** `scoring.py`/`setups.py` invoked with overlay configs in a sandbox context; comparison aggregates via forward-testing helpers; a variants report page; registration rows in this file + proposer-guidance.
**Config surface:** `research.variants.registry` (the ≤3 registered overlays with rationales), sandbox path settings.
**How:** (1) owner design discussion (sandbox mechanism, metrics, walk-forward protocol); (2) overlay + sandbox recompute; (3) comparison report with CIs + turnover; (4) registration discipline wiring. Size: ~3 iterations; split: sandbox+one variant, then metrics report, then registry/UX.
**Evidence Claim & ledger:** comparisons are descriptive; if a variant is to be *claimed* superior, that claim is registered and refereed (the comparison series through the standard gate, staging) before any owner decision to adopt.
**Canonical value:** variant-comparison artifacts; reader: report page. **Boundary:** none.
**Tests that will break:** none — new sandbox tests (fixture: identity overlay reproduces baseline byte-identically — THE load-bearing test).
**Do NOT touch:** live tables/config from any harness code path (enforced by test: run harness → assert live DB byte-identical).

**Acceptance / DoD:** identity-overlay test green; one registered variant compared end-to-end with walk-forward metrics + CIs + turnover; report renders; live untouched (verified).

**Ready-to-paste journey block:**
```markdown
- **J-XX: Methodology variants are compared in shadow, never in production**
  - Steps:
    1. Register a variant overlay (e.g., a pruned Entry-Quality blend from the structure report) with its rationale; run the shadow harness across history.
    2. Visit the variants report; assert baseline vs variant render: Actionable-set forward outcomes, drawdown profile, turnover, with CIs and the walk-forward protocol named.
    3. Assert the identity-overlay check is part of CI (variant = baseline config reproduces baseline results byte-identically).
    4. Assert live scores/setups/config are byte-identical before and after the run.
  - Acceptance:
    - **Consistency (single source):** comparisons re-read harness artifacts; the harness reuses the live engine code paths with overlay config (no forked scoring logic).
    - **Correctness:** the identity check passes; one variant cell re-verified offline matches.
    - **Honest status / anti-goals:** live behavior unchanged; ≤3 registered variants; no variant presented as better without a refereed claim; walk-forward discipline stated.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of one baseline-vs-variant report, viewable via `demo.sh mcp-loop --session-live`.
```

**Traps:** forking scoring logic for the sandbox (same code, different config+storage — or the comparison is meaningless); evaluating variants in-sample (each as-of's variant scores use bars ≤ as-of, outcomes after); registry sprawl (3 max, then the quarterly review decides); the subtle one — choosing variants AFTER peeking at their historical outcomes (registration precedes computation, always).
**Depends on:** B-421/B-422 (candidates + baseline), owner design discussion.

---

#### B-420 · ADAPTIVE: regime/phase-conditioned score weights *(via harness)*
**Track:** T4 · **Quarter:** Q4 · **Priority:** P2 · **Status:** PROPOSED · **Difficulty:** HARD · **Failure mode:** p-hack

**What & rationale:** ONE registered hypothesis (not a weight search): "in Risk-off/Bear phases, a defensive re-weighting (Risk score weight ↑, Leadership ↓ — exact overlay registered ex ante) produces an Actionable set with materially better drawdown profile at equal-or-better forward outcomes." Run as a B-423 variant; claim the comparison through staging if results support it; adoption is an owner decision, config-gated with the static blend one flag away.
★ **Evidence Claim:** the registered comparison claim (staging) if pursued past description. ★ **Do NOT touch:** live weights without canonical PASS + owner two-key. **Traps:** iterating overlay weights (ONE registered overlay; a second try is a new quarter's registration); conditioning on retrospective phases (causal series only).
**Depends on:** B-423 (hard), B-109 (context).

---

#### B-424 · ADAPTIVE: cost-aware setup thresholds *(via harness)*
**Track:** T4 · **Quarter:** Q4 · **Priority:** P2 · **Status:** PROPOSED · **Difficulty:** MEDIUM–HARD · **Failure mode:** p-hack

**What & rationale:** under the B-101 realistic convention, does the Actionable set still clear a meaningful bar net of timing+costs — and would ONE registered stricter variant (e.g., `actionable.leadership ≥ 85` instead of 80, fewer-but-stronger signals with less churn) fare better *net*? Run both through B-423 with realistic returns; report; owner decides. The deliverable is the honest net-of-costs picture of the product's central label.
★ **Evidence Claim:** registered comparison (staging) if pursued. ★ **Do NOT touch:** live `decision_rules` without the full gate. **Traps:** threshold grids (ONE variant); judging on gross returns (the entire point is net).
**Depends on:** B-101 (hard), B-423 (hard).

## Track 5 — Fundamentals & events (free-first: SEC EDGAR)

The product is OHLCV-only: `market_cap` is a frozen scalar, the `gap_climax` risk component is permanently NA, and no value/quality dimension exists. SEC EDGAR provides fundamentals and filing events **free** — the engineering keystone is **publication-lag causality**: every fact is usable only from its **filing date**, never its period-end date. The `config.macro.series` publication-lag pattern is the house template. Ingestion (B-501, B-505) is a data-basis-class change — schedule it alone in its window.

| Card | Title | Pri | Qtr |
|------|-------|-----|-----|
| B-501 | EDGAR company-facts ingestion (fundamentals table) | P1 | Q3 |
| B-502 | Fundamentals transparency panel (surface before scoring) | P1 | Q3 |
| B-503 | Quality factor family (profitability, accruals) | P2 | Q3 |
| B-504 | Value composite factor | P2 | Q3–Q4 |
| B-505 | Earnings-calendar ingestion (filing/announcement dates) | P1 | **Q2** (pulled forward) |
| B-506 | Post-earnings-announcement drift (PEAD) study | P2 | Q3 |
| B-507 | Buyback / dilution factor (shares outstanding) | P2 | Q4 |
| B-508 | Insider Form 4 aggregate (staging-only) | P3 | Q4 |

---

#### B-501 · EDGAR company-facts ingestion (fundamentals table)
**Track:** T5 · **Quarter:** Q3 · **Priority:** P1 · **Status:** PROPOSED
**Difficulty:** MEDIUM–HARD · **Dominant failure mode:** lookahead (period-end vs filing date — THE classic fundamental-data sin)

**What:** ingest quarterly/annual XBRL facts for the ~548-name pool from SEC EDGAR into a new `fundamentals` table keyed `(symbol, metric, period_end, filed_date)`. Start with a SMALL registered metric set: revenues, net income, total assets, stockholders' equity, operating cash flow, capex, cost of revenue, shares outstanding. Loader honors the same staged/validated/committed discipline as price seeds; a `bars_asof`-style accessor (`facts_asof(symbol, D)`) returns only facts **filed on or before D**.

**Why it protects capital:** unlocks the entire quality/value dimension (B-503/504/507) and event awareness — on honest, free data. Done wrong (period-end joins), it would poison every downstream claim with lookahead; that is why ingestion is its own carefully-gated card.

**Data (free):** bulk: `https://www.sec.gov/Archives/edgar/daily-index/xbrl/companyfacts.zip` (all companies, one download — preferred for the initial 548-name load); per-company: `https://data.sec.gov/api/xbrl/companyfacts/CIK{10digit}.json`; ticker→CIK map: `https://www.sec.gov/files/company_tickers.json`. Requirements: descriptive `User-Agent` header with contact email; ~10 req/s courtesy limit; facts carry `filed` dates and `form` types (10-Q/10-K) — the `filed` date IS the publication lag, per fact, exactly.

**Plugs in at:** a new ingest script beside `scripts/ingest_seed.py` (staged directory → validate → commit), new model/table, `facts_asof` accessor in the engine data layer (pattern: `macro_series` with `publication_lag_days`, but here the lag is exact per row); Data Manager availability view gains a fundamentals coverage section.
**Config surface:** `fundamentals.metrics` (the registered US-GAAP tag list, incl. fallback tags per metric — XBRL tag drift across filers is the main mess), `fundamentals.enabled: false` (nothing reads it until flipped).
**How:** (1) CIK mapping for the pool (log unmapped names honestly); (2) bulk parse → staged CSVs (metric set only) with `filed` preserved; (3) validation report: coverage per name/metric/era, duplicate-fact resolution rule (latest filing before D wins; restatements therefore apply only from their own filing dates — state this rule in methodology); (4) load + accessor + tests; (5) Data Manager coverage panel. Size: ~3 iterations; split: mapping+staging, validate+load, accessor+coverage UI.

**Evidence Claim & ledger:** `N/A — this card must not introduce proven-language anywhere.` (It is data plumbing; claims come later, pre-registered.)
**Canonical value:** the `fundamentals` table + `facts_asof` accessor — THE single read path for every downstream fundamental consumer.
**Anti-goal boundary:** none.
**Tests that will break:** none existing; new fixture tests: a fact filed 45 days after period-end is invisible at period-end+30 and visible at filed+0; restatement supersedes only after its own filed date.
**Do NOT touch:** price seed and its pins (different basis, but respect the one-basis-change-per-window rule anyway); scoring (nothing consumes fundamentals yet).

**Acceptance / DoD:** coverage report per metric/era; `facts_asof` fixture-proven causal; unmapped/missing names honestly listed; Data Manager shows fundamentals coverage.

**Ready-to-paste journey block:**
```markdown
- **J-XX: Fundamental facts exist with exact filing-date causality**
  - Steps:
    1. Visit the Data Manager; assert a fundamentals section shows per-metric coverage (names covered, era span, last update) and lists pool names without EDGAR coverage honestly.
    2. For one symbol, query the facts accessor at a date between a quarter's period-end and its filing date (test environment); assert the quarter's facts are absent; at the filing date, assert they appear.
    3. Assert `/methodology` documents the metric set, the restatement rule (facts apply from their own filing dates), and the EDGAR provenance.
  - Acceptance:
    - **Consistency (single source):** all fundamental reads go through the one accessor over the one table.
    - **Correctness:** a spot-checked fact (value + filed date) matches the EDGAR record for that accession.
    - **Honest status / anti-goals:** period-end lookahead is impossible by construction (fixture-proven); missing coverage renders as absence, never zeros; no scoring changes.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of the coverage panel and the causality demonstration, viewable via `demo.sh mcp-loop --session-live`.
```

**Traps:** joining on `period_end` (the sin — always `filed`); trusting one US-GAAP tag per metric (filers vary — registered fallback tag lists, coverage-reported); backfilling "obvious" missing quarters (absence is honest); hammering the API without the bulk file (use the zip); forgetting the User-Agent (SEC blocks).
**Depends on:** none. Enables B-502/503/504/507; B-505 is independent (submissions, not XBRL).

---

#### B-502 · Fundamentals transparency panel *(surface before scoring)*
**Track:** T5 · **Quarter:** Q3 · **Priority:** P1 · **Status:** PROPOSED
**Difficulty:** EASY · **Dominant failure mode:** UI-recompute

**What:** before any fundamental factor exists, show the raw ingested facts on stock detail: revenue/net-income trend, shares outstanding, equity, operating cash flow — as-of aware (only facts filed ≤ the page's as-of), EDGAR-provenance-labeled, with filing dates visible. The owner sees exactly what the system knows and since when.

**Why it protects capital:** trust before use — surfacing the raw data first lets the owner sanity-check coverage/quality before any factor built on it can influence decisions. (Same sequencing the macro feed used: vendor-labeled context first.)

**Data / plugs in at:** B-501's accessor; stock-detail panel; as-of routing (exists).
**Config surface:** `fundamentals.display.metrics` subset.
**How:** panel + as-of wiring + provenance labels. Size: ~1 iteration.
**Evidence Claim & ledger:** `N/A — must not introduce proven-language.`
**Canonical value:** none new (re-reads accessor). **Boundary:** none. **Tests:** as-of panel fixture (facts appear only after filed dates). **Do NOT touch:** scores/setups.
**Acceptance / DoD:** panel renders per name with filed dates; historical as-of shows only then-known facts; uncovered names show honest absence.

**Ready-to-paste journey block:**
```markdown
- **J-XX: Raw fundamentals are visible per stock, as-of aware and provenance-labeled**
  - Steps:
    1. Open `/stocks/{ticker}` for a covered name; assert a fundamentals panel shows the registered metrics with period-ends AND filing dates, labeled "SEC EDGAR".
    2. Switch the global as-of to a date before a recent filing; assert that filing's facts disappear from the panel.
    3. Open an uncovered name; assert the panel states "no EDGAR coverage" rather than rendering blanks as zeros.
  - Acceptance:
    - **Consistency (single source):** the panel re-reads the facts accessor; no derived metrics computed in the UI.
    - **Correctness:** one displayed value matches the stored fact for the same accession.
    - **Honest status / anti-goals:** as-of causality visible and enforced; absence honest; no valuation commentary.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of the panel and the as-of disappearance, viewable via `demo.sh mcp-loop --session-live`.
```

**Traps:** computing ratios in the panel (derived metrics are factor territory — engine-side, later cards); showing period-end as if it were availability.
**Depends on:** B-501.

---

#### B-503 · Quality factor family (profitability, accruals)
**Track:** T5 · **Quarter:** Q3 · **Priority:** P2 · **Status:** PROPOSED
**Difficulty:** MEDIUM · **Dominant failure mode:** lookahead + p-hack (families invite scans — TWO registered claims only)

**What:** two quality factors with the strongest priors, per the §D6 recipe on `facts_asof` data: **gross profitability** = (revenue − cost of revenue) / total assets (Novy-Marx — the quality anchor) and **accruals** = (net income − operating cash flow) / total assets (Sloan — low accruals = high earnings quality). Lab-first; then exactly TWO registered staging claims (family `fundamental` if B-404 landed): gross-profitability D10 h=60 positive; accruals **D1** (lowest accruals) h=60 positive.

**Why it protects capital:** quality is the defensive fundamental dimension — historically its payoff concentrates in drawdowns, which is exactly the owner's stated priority; and both factors have decades of literature behind them (real priors, not mining).

**Data / plugs in at:** B-501 facts; factor computation at snapshot time using **facts filed ≤ as-of** (point-in-time by construction); stored per §D6; factor-lab entries; methodology entries with formulas + literature one-liners.
**Config surface:** `fundamentals.factors.gross_profitability` / `accruals` (tag lists via B-501 config; staleness rule: use the latest annual/quarterly fact filed within N days — registered).
**How:** recipe + the two claims. Size: ~2 iterations.
**Evidence Claim & ledger:** staging; 2 trials (registered together); FAIL → graveyard per factor (lab stays descriptive).
```json
{"kind": "factor", "factor": "gross_profitability", "slice_kind": "decile", "decile": 10, "horizon": 60, "direction": "positive"}
```
```json
{"kind": "factor", "factor": "accruals", "slice_kind": "decile", "decile": 1, "horizon": 60, "direction": "positive"}
```
**Canonical value:** stored factor columns; lab reader. **Boundary:** none. **Tests:** methodology completeness; NA fixtures (names without required facts excluded from deciles, never zero-filled). **Do NOT touch:** score blends; the metric definitions after registration.
**Acceptance / DoD:** factors compute causally (fixture: value changes only at filing dates); decile tables with n/CI; two verdicts recorded.

**Ready-to-paste journey block:**
```markdown
- **J-XX: Quality factors (gross profitability, accruals) join the lab with registered evidence**
  - Steps:
    1. The iteration carries the two pre-registered `## Evidence Claim` blocks (gross_profitability D10 h60 positive; accruals D1 h60 positive), routed to staging; the gate referees them BEFORE any surfacing of proven-language; non-PASS blocks the claim-bearing step.
    2. Visit `/research/factor-lab` for each; assert decile rows render with n/CI, the formula, and the "facts filed ≤ as-of" causality note.
    3. Assert names lacking the required facts are excluded with an honest exclusion count.
  - Acceptance:
    - **Consistency (single source):** factors computed once at snapshot time from the facts accessor; lab re-reads stored values.
    - **Correctness:** one name's factor value re-verified offline (same facts, same as-of) matches.
    - **Honest status / anti-goals:** point-in-time by filing date; exclusions visible; badges honest to verdicts; scores unchanged.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of both factors' lab pages, viewable via `demo.sh mcp-loop --session-live`.
```

**Traps:** period-end joins (again — it will try to sneak in via "latest quarter"); mixing annual and quarterly facts inconsistently (registered staleness rule); adding ROE/asset-growth "while we're here" (they are FUTURE registrations, listed in the replenishment pool, not this card).
**Depends on:** B-501.

---

#### B-504 · Value composite factor *(medium detail)*
**Track:** T5 · **Quarter:** Q3–Q4 · **Priority:** P2 · **Status:** PROPOSED · **Difficulty:** MEDIUM · **Failure mode:** honest-expectations + lookahead

**What & rationale:** a value composite — mean of cross-sectional ranks of earnings yield (net income / market cap), FCF yield ((OCF − capex) / market cap), book-to-market (equity / market cap) — computed with `facts_asof` numerators and **as-of price × shares** denominators. Registered honestly: in a mega-cap growth-heavy universe, long-only value D10 may well FAIL — a null is a finding (it tells the owner value tilts add little here). ONE claim: D10 h=60 positive.
```json
{"kind": "factor", "factor": "value_composite", "slice_kind": "decile", "decile": 10, "horizon": 60, "direction": "positive"}
```
**Plugs in at:** §D6 recipe; market cap from as-of close × latest filed shares outstanding (replaces the frozen scalar for THIS factor only — do not touch the universe filter's market_cap source in this card).
**Config:** `fundamentals.factors.value_composite` legs + staleness. ★ **Tests:** NA fixtures; causality fixture. ★ **Do NOT touch:** universe gates; score blends; leg list after registration.
**Traps:** stale-share-count market caps around splits (shares outstanding facts lag — document; the adjusted-price basis and raw share counts must be reconciled: use split-adjusted shares implied by the vendor basis, or compute cap from unadjusted-consistent pairs — write the reconciliation note BEFORE coding); negative-equity names (exclude, count, disclose).
**Depends on:** B-501. **Journey:** B-503's pattern with this factor/claim.

---

#### B-505 · Earnings-calendar ingestion (filing/announcement dates) — **pulled forward to Q2**
**Track:** T5 · **Quarter:** Q2 · **Priority:** P1 · **Status:** PROPOSED
**Difficulty:** EASY–MEDIUM · **Dominant failure mode:** lookahead (only dates knowable as-of count)

**What:** ingest per-name **event dates** from EDGAR submissions metadata (`https://data.sec.gov/submissions/CIK{10digit}.json`): 8-K filings with Item 2.02 (results announcements) and 10-Q/10-K filing dates. Historical announcement dates enable B-209's flags and B-506's PEAD; small, independent of XBRL ingestion (B-501), hence Q2.

**Why it protects capital:** the earliest cheap step toward "never hold an oversized position into a binary event unknowingly" (B-209) — the single most preventable retail loss.

**Data (free):** submissions JSON per CIK (recent + archived pages); fields: form type, filing date, items (for 8-K). Same User-Agent/rate rules as B-501.
**Plugs in at:** ingest script (staged/validated/committed) → `earnings_events` table (symbol, event_date=filing date, form, items); accessor `events_asof`; Data Manager coverage note.
**Config surface:** `earnings.forms: ["8-K:2.02","10-Q","10-K"]`.
**How:** CIK map (share B-501's) → fetch submissions → extract → stage/validate (coverage per name/era) → load + accessor + fixtures. Size: ~1–2 iterations.
**Evidence Claim & ledger:** `N/A — must not introduce proven-language.`
**Canonical value:** the events table + accessor; readers: B-209 flags, B-506, digest.
**Anti-goal boundary:** none. **Tests:** causality fixture (an event is knowable only from its filing date — trivially true here since the event IS a filing; the trap is *forward* dates: we store none). **Do NOT touch:** any scraped "expected earnings date" source (banned — official filings only; forward expectations stay absent).
**Acceptance / DoD:** per-name event histories with coverage stats; accessor causal; no forward-looking dates fabricated.

**Ready-to-paste journey block:**
```markdown
- **J-XX: Official earnings/filing event dates are ingested with honest coverage**
  - Steps:
    1. Visit the Data Manager; assert an events section shows per-name counts of ingested 8-K(2.02)/10-Q/10-K dates and era coverage, EDGAR-labeled.
    2. For one name, assert its event list matches EDGAR's submissions record (spot-check one accession).
    3. Assert no "upcoming/expected earnings" dates exist anywhere (only filed history).
  - Acceptance:
    - **Consistency (single source):** all event reads go through the one accessor.
    - **Correctness:** spot-checked dates match EDGAR.
    - **Honest status / anti-goals:** filed history only; no scraped calendars; absence honest.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of the events coverage, viewable via `demo.sh mcp-loop --session-live`.
```

**Traps:** conflating period-end with announcement (use filing dates); inventing forward dates from historical periodicity (B-209 may only say "last reported X days ago" and, where a company has *filed* a forward notice, that — nothing else).
**Depends on:** none. Enables B-209, B-506.

---

#### B-506 · Post-earnings-announcement drift (PEAD) study
**Track:** T5 · **Quarter:** Q3 · **Priority:** P2 · **Status:** PROPOSED
**Difficulty:** MEDIUM · **Dominant failure mode:** lookahead (event-day return needs care) + p-hack

**What:** the classic Bernard–Thomas anomaly, with a free surprise proxy: for each announcement event (B-505), the **announcement-day abnormal return** (name return minus SPY, on the first trading day ≥ the 8-K date) proxies the surprise; hypothesis: strong-positive-surprise names drift upward over the following h=60. ONE registered staging claim on the top-surprise-decile cohort. Event-study lab surfacing with the proxy's limitations stated (no analyst-estimate data — the proxy conflates surprise with reaction).

**Why it protects capital:** PEAD is among the most replicated anomalies; if it survives our referee at realistic timing (entry AFTER the reaction day — see traps), it is a legitimate, understandable edge; if it fails net, that is worth knowing before the owner ever chases post-earnings moves.

**Data / plugs in at:** B-505 events + bars; event-study machinery; referee gate.
**Config surface:** registered row: surprise window (day 0 = first trading day ≥ filing), surprise decile, horizon.
**How:** event join (calendar-aware day-0 rule, fixture-tested) → surprise ranking per earnings season → cohort → claim. Size: ~2 iterations.
**Evidence Claim & ledger:** staging; 1 trial.
```json
{"kind": "event-study", "subject": "earnings_surprise_proxy", "slice_kind": "decile", "decile": 10, "horizon": 60, "direction": "positive"}
```
**Canonical value:** lab payloads. **Boundary:** none. **Tests:** day-0 mapping fixtures (weekend/holiday filings). **Do NOT touch:** entry timing — the cohort's forward window starts at day-0 CLOSE at the earliest (the surprise must be fully observable), and under B-101's convention, day+1 open.
**Acceptance / DoD:** event mapping fixture-proven; cohort stats with n/CI; verdict recorded; proxy limitation note on the lab page.

**Ready-to-paste journey block:**
```markdown
- **J-XX: Post-earnings drift is tested with an honest, free surprise proxy**
  - Steps:
    1. The iteration carries `{"kind":"event-study","subject":"earnings_surprise_proxy","slice_kind":"decile","decile":10,"horizon":60,"direction":"positive"}` (pre-registered), routed to staging; the gate referees BEFORE code; non-PASS blocks.
    2. Visit the event-study lab's PEAD view; assert surprise-decile cohorts render forward stats with n/CI, and the page states the proxy definition and its limitation (no estimate data; reaction-based).
    3. Assert the cohort's forward window begins only after the surprise is fully observable (documented day-0 close rule).
  - Acceptance:
    - **Consistency (single source):** events from the one accessor; stats from the lab engine; badge via existing resolution.
    - **Correctness:** one event's day-0 mapping and abnormal return re-verified offline match.
    - **Honest status / anti-goals:** proxy limits disclosed; no estimate-data pretense; entry-timing honesty; verdict rendered truthfully.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of the PEAD view, viewable via `demo.sh mcp-loop --session-live`.
```

**Traps:** including day-0's return in the forward window (that is buying yesterday's news backwards — the drift window starts after day 0); re-slicing surprise thresholds after results (ONE registered decile rule); ignoring names whose 8-K filed after hours vs before open (the "first trading day ≥ filing" rule handles it — keep it mechanical and documented).
**Depends on:** B-505; B-101 (realistic timing preferred).

---

#### B-507 · Buyback / dilution factor (shares outstanding) *(medium detail)*
**Track:** T5 · **Quarter:** Q4 · **Priority:** P2 · **Status:** PROPOSED · **Difficulty:** EASY–MEDIUM · **Failure mode:** lookahead + split handling

**What & rationale:** year-over-year change in shares outstanding (from `facts_asof`, dei/us-gaap share facts): decile 1 (largest reduction = net buybacks) historically outperforms heavy diluters — a clean, slow, well-documented signal. §D6 recipe; ONE claim: D1 h=60 positive.
```json
{"kind": "factor", "factor": "share_count_change", "slice_kind": "decile", "decile": 1, "horizon": 60, "direction": "positive"}
```
**Config:** `fundamentals.factors.share_count_change: {window_days: 365}`. ★ **Tests:** split fixture — a 4:1 split must NOT read as 4× dilution (compare split-adjusted counts; reconcile with the price basis the same way B-504 does — share the reconciliation helper). ★ **Do NOT touch:** blends; registration.
**Traps:** raw share counts across splits (the fixture exists because this WILL be gotten wrong otherwise); mixing share classes (registered tag rule: use dei EntityCommonStockSharesOutstanding first, fallbacks documented).
**Depends on:** B-501 (+ B-504's reconciliation helper). **Journey:** B-503's pattern.

---

#### B-508 · Insider Form 4 aggregate *(condensed; staging-only, honest long-shot)*
**Track:** T5 · **Quarter:** Q4 · **Priority:** P3 · **Status:** PROPOSED · **Difficulty:** MEDIUM · **Failure mode:** data noise + lookahead

**What & why:** aggregate insider net-buying from Form 4 filings (EDGAR full-text/daily indexes; parse transaction codes P/S) into a per-name trailing z-score. Literature says open-market clustered buys carry modest signal; data is noisy and parsing is fiddly — descriptive lab first, then at most ONE registered claim (D10 net-buying h=60 positive) if the descriptive view looks sane. Usable-from = Form 4 filing date (2-business-day rule makes lag short).
★ **Evidence Claim:** deferred — register only after the descriptive stage, as its own quarterly-review decision. ★ **Canonical value:** insider-aggregate table + accessor. ★ **Boundary:** none. ★ **Tests:** parser fixtures (P vs S codes, derivative rows excluded); causality fixture. ★ **Do NOT touch:** anything else — this card is deliberately self-contained.
**Traps:** counting derivative/option exercises as conviction buys (exclude; registered code list); survivor-parsing only recent filings (state coverage era honestly).
**Depends on:** B-501's CIK plumbing. **Journey:** transparency-panel pattern (B-502) for the descriptive stage.

---

## Track 6 — Macro & cross-asset context

Macro is **already wired but default-off** (`config.macro`: 4 FRED series with `publication_lag_days`, optional severity/HMM legs). The track's rule: **revision honesty first (B-601), enablement only on evidence (B-602)**, then careful extensions. All series free (FRED/ALFRED, CBOE).

| Card | Title | Pri | Qtr |
|------|-------|-----|-----|
| B-601 | FRED vintage/revision honesty audit (ALFRED) — precondition | P1 | Q2 |
| B-602 | Macro enablement study (flip the flags only on proof) | P1 | Q3 |
| B-603 | Extended FRED series set | P2 | Q3 |
| B-604 | VIX term-structure context (VIX vs VIX3M) | P2 | Q3 |
| B-605 | Credit-spread velocity early-warning study | P2 | Q3 |
| B-606 | Cross-asset causal dashboard panel | P3 | Q3–Q4 |

---

#### B-601 · FRED vintage/revision honesty audit (ALFRED) — precondition for T6
**Track:** T6 · **Quarter:** Q2 · **Priority:** P1 · **Status:** PROPOSED
**Difficulty:** MEDIUM · **Dominant failure mode:** lookahead (revised macro data is time-travel in disguise)

**What:** FRED serves **current-vintage** values: revised history. A macro study on revised UNRATE "knows" things nobody knew at the time — `publication_lag_days` does not fix revisions. Audit each wired + planned series using **ALFRED** (`https://alfred.stlouisfed.org`, `realtime_start/realtime_end` on the FRED API): quantify first-print vs final revisions; classify series — market-derived (T10Y2Y, BAMLH0A0HYM2, DTWEXBGS, VIX: effectively unrevised → lag-only is honest) vs statistical (UNRATE, NFCI, ICSA: revised → require vintage data or a registered conservative padding rule). Output: per-series revision profile + a binding policy in methodology + config corrections.

**Why it protects capital:** without this, B-602 could "prove" macro improves phase detection using information from the future — a certificate-shaped lie. The critic pass rated T6 structurally unsound without this card.

**Data (free):** ALFRED vintages via `fred/series/observations` with `realtime_start`/`realtime_end`; no key needed for reasonable use (key optional/free).
**Plugs in at:** macro ingest path (vintage-aware fetch option), `config.macro.series` (per-series `revision_policy: none|vintage|padded`), methodology disclosure, B-602's protocol.
**How:** (1) vintage pulls per series; (2) revision-magnitude report (first-print vs final, sign-flip rate); (3) policy + config; (4) where `vintage` is required, store first-print series for study use. Size: ~2 iterations.
**Evidence Claim & ledger:** `N/A — must not introduce proven-language.`
**Canonical value:** the revision-profile artifact + per-series policy; readers: methodology, B-602/603.
**Anti-goal boundary:** none. **Tests:** fixture with a constructed revised series → padded/vintage access returns only what was knowable. **Do NOT touch:** current-vintage display series (dashboards may show today's best data — the CAUSAL STUDY series is what must be vintage-honest; keep the two clearly separated).
**Acceptance / DoD:** every macro series carries a revision profile + policy; study-path accessors are vintage-honest by fixture proof.

**Ready-to-paste journey block:**
```markdown
- **J-XX: Macro series are revision-honest — vintage-aware where it matters**
  - Steps:
    1. Visit `/methodology` (macro section); assert each series lists its revision profile (typical first-print vs final change) and its policy (market-derived: lag-only; statistical: vintage or padded).
    2. In the test environment, query the study-path accessor for a revised series at a historical date; assert it returns the value knowable THEN (first print), not today's revised value.
    3. Assert display surfaces may show current-vintage data but are labeled as such, distinct from the study path.
  - Acceptance:
    - **Consistency (single source):** one macro accessor per purpose (study vs display), policies from config.
    - **Correctness:** the fixture's vintage lookup matches the constructed truth.
    - **Honest status / anti-goals:** no revised-data time travel in any causal computation; policies disclosed.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of the revision profiles and the vintage demonstration, viewable via `demo.sh mcp-loop --session-live`.
```

**Traps:** auditing once and then ingesting current-vintage anyway (the accessor split is the deliverable, not the report); padding rules invented per-study (registered in config, once).
**Depends on:** none. **Blocks:** B-602, B-603 study use.

---

#### B-602 · Macro enablement study (flip the flags only on proof)
**Track:** T6 · **Quarter:** Q3 · **Priority:** P1 · **Status:** PROPOSED
**Difficulty:** MEDIUM–HARD · **Dominant failure mode:** p-hack (a yes/no question, not a search)

**What:** the two dormant flags (`macro.enable.severity`, `macro.enable.regime_switching`) each add a macro leg to an existing computation. The study: recompute the phase/severity/P(bear) history WITH each leg (vintage-honest inputs per B-601) in a sandbox and compare against the live baseline on **pre-registered criteria**: does macro-enabled severity rank future realized drawdowns better (rank correlation between severity at D and forward max-drawdown), and does macro-informed P(bear) classify subsequent bear phases better (Brier score)? Report; if a leg wins clearly, the owner flips the flag (config change, two-key); if not, the flags stay off and the study closes.

**Why it protects capital:** phase/severity gates real risk posture; adding macro because it "should help" is exactly the kind of unexamined change this system exists to prevent. This is the template for every future "should we turn X on?" question.

**Data / plugs in at:** existing macro legs (`_macro_severity_legs`, HMM observation extension), sandbox recompute (B-423's discipline, though this predates the full harness — a phase-engine-scoped sandbox suffices), comparison report page.
**Config surface:** registered criteria + thresholds (what "clearly better" means, written BEFORE computing — e.g., rank-correlation improvement ≥ registered delta on the full 30y).
**How:** (1) register criteria; (2) vintage-honest input series; (3) sandbox recompute per leg; (4) report with CIs; (5) owner decision recorded either way. Size: ~2 iterations.
**Evidence Claim & ledger:** `N/A` (a config-governance study; its statistics are reported with CIs but it mints no cohort badge). If the owner wants a certified claim about severity's drawdown-ranking power, that is a separate registered claim.
**Canonical value:** the comparison artifact. **Boundary:** none. **Tests:** sandbox isolation (live phase history byte-identical after runs); criteria fixtures. **Do NOT touch:** live flags within the study; HMM/severity parameters (enabling a leg ≠ retuning the engine).
**Acceptance / DoD:** criteria registered before compute; both legs evaluated on 30y; report + recorded decision; live untouched until the decision.

**Ready-to-paste journey block:**
```markdown
- **J-XX: The dormant macro legs are enabled only on registered, vintage-honest evidence**
  - Steps:
    1. Assert the study's criteria (metrics + thresholds) are registered and visible BEFORE results (methodology or the report page's registration section, dated).
    2. Visit the enablement report; assert baseline vs macro-enabled severity/P(bear) comparisons render on the registered metrics with CIs, computed from vintage-honest inputs.
    3. Assert the recorded decision (flags flipped or kept off) cites the criteria outcome, and the live configuration matches the decision.
  - Acceptance:
    - **Consistency (single source):** comparisons re-read the study artifact; live phase history is untouched by the study.
    - **Correctness:** one comparison metric re-verified offline matches.
    - **Honest status / anti-goals:** criteria precede results; vintage honesty per B-601; a "no improvement" outcome is displayed as plainly as a win.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of the report and the decision record, viewable via `demo.sh mcp-loop --session-live`.
```

**Traps:** choosing metrics after seeing results; retuning HMM emissions "to give macro a fair chance" (a different, registered study); running on revised data because vintage is tedious (B-601 exists so this excuse doesn't).
**Depends on:** **B-601 (hard)**.

---

#### B-603 · Extended FRED series set *(medium detail)*
**Track:** T6 · **Quarter:** Q3 · **Priority:** P2 · **Status:** PROPOSED · **Difficulty:** EASY–MEDIUM · **Failure mode:** scope-creep (context ≠ signal)

**What & rationale:** add four registered series to `config.macro.series`, each with lag + revision policy per B-601: **DFII10** (10y real yield — the discount-rate context growth equities live under), **T5YIE** (5y breakeven inflation), **NFCI** (financial conditions; revised — vintage policy), **ICSA** (initial claims — the fastest labor turn signal; revised). Display in macro context surfaces; **no computation consumes them** until a registered study (they join B-602-style protocols or a registered severity-leg candidacy later).
**Plugs in at:** macro ingest/config/display (the pattern exists end-to-end). Size: ~1 iteration.
★ **Evidence Claim:** `N/A`. ★ **Canonical value:** series rows via the existing macro path. ★ **Boundary:** none. ★ **Tests:** lag fixtures per series. ★ **Do NOT touch:** severity/regime inputs (display-only until registered).
**Traps:** letting a new series quietly join a computation ("it was right there") — the enable path is registered study → owner flag.
**Depends on:** B-601 policies. **Journey:** macro-context pattern — assert series display with lag/revision labels and that no engine computation reads them (config off).

---

#### B-604 · VIX term-structure context (VIX vs VIX3M) *(medium detail)*
**Track:** T6 · **Quarter:** Q3 · **Priority:** P2 · **Status:** PROPOSED · **Difficulty:** EASY–MEDIUM · **Failure mode:** small-n honesty

**What & rationale:** the VIX/VIX3M ratio (backwardation = near-term fear exceeding medium-term — historically a stress regime marker) from free sources (FRED `VIXCLS` + `VXVCLS`, or CBOE history CSVs). Ship as: (a) context chip + series on the market-phase page; (b) ONE registered event study: backwardation-onset episodes (ratio crossing above 1.0, registered threshold) → forward index outcomes, staging claim direction negative at h=20.
```json
{"kind": "event-study", "subject": "vix_backwardation_onset", "horizon": 20, "direction": "negative"}
```
**Plugs in at:** macro-series pattern (market-derived: lag-only) + event-study machinery. Size: ~1–2 iterations.
★ **Canonical value:** series + episode payloads. ★ **Boundary:** none. ★ **Tests:** episode extraction fixtures (crossing rule, no overlap). ★ **Do NOT touch:** the regime engine's VIX gate (this is context + a study, not a new gate — gating changes go through the adaptive arc).
**Traps:** threshold shopping around 1.0 (registered); double-counting persistent backwardation as many onsets (crossing rule).
**Depends on:** B-601 (classification: market-derived). **Journey:** context chip + episode study + honest verdict rendering, per the standard pattern.

---

#### B-605 · Credit-spread velocity early-warning study *(medium detail)*
**Track:** T6 · **Quarter:** Q3 · **Priority:** P2 · **Status:** PROPOSED · **Difficulty:** EASY–MEDIUM · **Failure mode:** p-hack (reuse the registered velocity pattern)

**What & rationale:** `BAMLH0A0HYM2` (HY OAS) is already wired; spread LEVEL is slow, spread **velocity** (rapid widening) is the early-warning shape — and the codebase already has the velocity pattern (`severity_velocity`, OLS slope over K snapshots). Compute spread velocity with the SAME transform (reuse, don't fork); ONE registered event study: rapid-widening onsets (velocity above registered threshold) → forward index outcomes at h=20, direction negative; display velocity beside the spread on macro surfaces.
```json
{"kind": "event-study", "subject": "credit_spread_widening_onset", "horizon": 20, "direction": "negative"}
```
**Plugs in at:** velocity helper reuse + macro display + event-study machinery. Size: ~1 iteration.
★ **Canonical value:** velocity series + episode payload. ★ **Boundary:** none. ★ **Tests:** velocity fixture (constructed widening → onset detected once). ★ **Do NOT touch:** severity weights (candidate status only, registered later if ever).
**Traps:** inventing a second slope definition (reuse `severity_velocity`'s); onset overlap.
**Depends on:** B-601 (market-derived classification). **Journey:** standard context + study pattern.

---

#### B-606 · Cross-asset causal dashboard panel *(condensed)*
**Track:** T6 · **Quarter:** Q3–Q4 · **Priority:** P3 · **Status:** PROPOSED · **Difficulty:** EASY · **Failure mode:** UI-recompute

**What & why:** one panel composing what now exists across surfaces: yield curve, real yield, breakevens, HY spread + velocity, dollar, VIX + term structure — each as current value + sparkline + historical percentile, phase-band overlaid, every series lag/revision-labeled. Pure composition of already-served values; the owner's one-glance macro context.
**How:** panel re-reading existing macro payloads; zero new computation. Size: ~1 iteration.
★ **Evidence Claim:** `N/A`. ★ **Canonical value:** none new. ★ **Boundary:** none. ★ **Tests:** none material. ★ **Do NOT touch:** series computations.
**Journey (paste-ready):**
```markdown
- **J-XX: One causal cross-asset panel composes the macro context**
  - Steps:
    1. Visit the cross-asset panel; assert each configured series renders current value, sparkline, historical percentile, and its lag/revision label, with market-phase bands overlaid.
    2. Assert every value byte-matches its source surface (spot-check two series).
  - Acceptance:
    - **Consistency (single source):** the panel re-reads existing macro payloads; no recomputation.
    - **Correctness:** spot-checks match sources.
    - **Honest status / anti-goals:** labels carried; context only, no signals.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of the panel, viewable via `demo.sh mcp-loop --session-live`.
```
**Depends on:** B-603/604/605 enrich it; can ship with today's four series.

## Track 7 — Small/mid-cap expansion (ISOLATED, hard-gated)

Owner's constraint, verbatim intent: *interesting but higher risk — must not impact the current US large-cap scope.* Binding isolation rules: separate pool file, separate config namespace, separate scan runs keyed by universe profile, surfaces behind a switcher that **defaults to large-cap**, zero changes to large-cap defaults or claims. **B-701's audit is a hard gate: no other T7 card may start until it passes AND the owner explicitly gates the track in.** Expect the audit to conclude that free Stooq data is marginal here (small-cap delisting rates make survivorship bias far worse than in large caps) — in which case the honest outcomes are "park the track" or "fund B-112's vendor, which includes delisted small caps".

| Card | Title | Pri | Qtr |
|------|-------|-----|-----|
| B-701 | Feasibility & bias audit (THE gate) | P1 | Q3 |
| B-702 | Isolated pool + resolver profile + config namespace | P2 | Q4 |
| B-703 | Parallel leaderboard behind a universe switcher | P2 | Q4 |
| B-704 | Factor-transfer replication of certified large-cap edges | P2 | Q4 |
| B-705 | Small-cap risk surfaces (liquidity/spread/gap) | P2 | Q4 |

---

#### B-701 · Small/mid-cap feasibility & bias audit — THE gate
**Track:** T7 · **Quarter:** Q3 · **Priority:** P1 · **Status:** PROPOSED
**Difficulty:** MEDIUM · **Dominant failure mode:** data-integrity (over-optimism about free coverage)

**What:** a written, numbers-first audit BEFORE any build: (1) assemble a candidate small/mid list (S&P 400/600-style membership from free public lists); (2) measure Stooq bulk-archive coverage: how many names have bars, history depth distribution, ADV/price distributions vs configured gates; (3) estimate the survivorship damage: small-cap index turnover/delisting rates (documented sources) vs our surviving-names-only feed — expect materially worse than large-cap; (4) liquidity reality: what fraction passes sane tradability floors (B-210's measures); (5) verdict memo with three options costed: build on free data with loud bias disclosure / fund the B-112 vendor (delisted small caps included) / park the track.

**Why it protects capital:** the owner called this direction higher-risk; the audit converts that instinct into numbers before any capital — or engineering budget — touches it. A parked track on honest grounds is a success outcome.

**Data:** Stooq bulk archive (already local: `data/d_us_txt`), free membership lists (community-maintained; provenance-noted), index methodology documents for turnover rates.
**Plugs in at:** analysis scripts + a memo committed to docs; no product surface changes.
**Config surface:** none (audit only).
**How:** list → coverage stats → bias estimate → liquidity stats → memo + owner decision recorded on this card. Size: ~1–2 iterations.
**Evidence Claim & ledger:** `N/A — this card must not introduce proven-language anywhere.`
**Canonical value:** none (a memo). **Anti-goal boundary:** none. **Tests:** none (scripted analysis with committed outputs). **Do NOT touch:** any product code, any large-cap artifact.
**Acceptance / DoD:** memo with the four measurements + three costed options; owner decision recorded (gate open / vendor first / parked).

**Ready-to-paste journey block:**
```markdown
- **J-XX: The small/mid-cap track is gated by a numbers-first feasibility audit**
  - Steps:
    1. Read the committed audit memo; assert it quantifies: candidate-list size and provenance, Stooq coverage (names with bars, history-depth distribution), estimated delisting/survivorship severity vs large-caps, and tradability pass rates against the configured gates.
    2. Assert the memo presents the three options with costs and a recommendation, and records the owner's decision.
    3. Assert no product surface or large-cap artifact changed in this iteration.
  - Acceptance:
    - **Consistency (single source):** the memo's numbers come from committed analysis outputs (re-runnable scripts).
    - **Correctness:** one coverage figure re-verified against the archive matches.
    - **Honest status / anti-goals:** bias severity stated plainly; "park" is presented as a first-class outcome; zero product changes.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of the memo's key tables, viewable via `demo.sh mcp-loop --session-live`.
```

**Traps:** letting enthusiasm pre-build "just the pool file" before the gate decision; underestimating survivorship (small-cap indexes turn over hard — the audit must cite turnover sources, not guess).
**Depends on:** none. **Blocks:** B-702–B-705.

---

#### B-702 · Isolated pool + resolver profile + config namespace *(condensed)*
**Track:** T7 · **Quarter:** Q4 · **Priority:** P2 · **Status:** PROPOSED · **Difficulty:** MEDIUM · **Failure mode:** scope-creep (leakage into large-cap paths)

**What & why:** the plumbing, isolation-first: `data/seed/universe_pool_smallcap.csv`; a `universe_profile` dimension on scan runs (`largecap` default everywhere); `config.universe_profiles.smallcap.*` gates (stricter relative liquidity floors, lower min_price per the audit); resolver parameterized by profile (same code, profile-selected pool + gates); scans runnable per profile; **large-cap behavior byte-identical** (the load-bearing test: run the full large-cap pipeline before/after — identical outputs).
★ **Evidence Claim:** `N/A`. ★ **Canonical value:** profile-keyed runs (additive dimension). ★ **Boundary:** none. ★ **Tests:** the byte-identity test above + profile-resolver fixtures. ★ **Do NOT touch:** large-cap pool/gates/defaults; existing claims.
Size: ~2 iterations. **Traps:** "sharing" a tuned gate back to large-cap config; forgetting the default profile in ANY existing query path (every existing read must resolve to largecap unchanged).
**Journey:** assert a smallcap scan exists keyed by profile; assert every pre-existing surface still reads largecap; assert the byte-identity test passed. **Depends on:** B-701 gate open.

---

#### B-703 · Parallel leaderboard behind a universe switcher *(condensed)*
**Track:** T7 · **Quarter:** Q4 · **Priority:** P2 · **Status:** PROPOSED · **Difficulty:** EASY–MEDIUM · **Failure mode:** UI-recompute / default drift

**What & why:** `/stocks` gains a profile switcher (default largecap, choice not persisted server-side); smallcap view renders the same board shape from smallcap runs, with a permanent banner: "experimental universe — worse data quality (see audit); evidence badges are large-cap claims and do NOT apply here" (badges suppressed or explicitly scoped).
★ **Evidence Claim:** `N/A`. ★ **Canonical value:** none new (profile-keyed reads). ★ **Boundary:** none. ★ **Tests:** default-profile snapshot tests. ★ **Do NOT touch:** large-cap default rendering; badge resolution semantics (scoping only).
Size: ~1 iteration. **Traps:** letting large-cap badges light smallcap rows (claims are universe-scoped — surface must say so); making smallcap the sticky default.
**Journey:** switcher present; default largecap; smallcap banner + badge scoping asserted. **Depends on:** B-702.

---

#### B-704 · Factor-transfer replication of certified large-cap edges *(condensed)*
**Track:** T7 · **Quarter:** Q4 · **Priority:** P2 · **Status:** PROPOSED · **Difficulty:** MEDIUM · **Failure mode:** p-hack (replication set = the canonical claims, nothing else)

**What & why:** replication is the strongest science available to the track: re-run EXACTLY the canonical large-cap claims (same factor, decile, horizon, direction) on the smallcap universe as registered replications (family `smallcap` per B-404). Outcomes: transfers (edge is robust across cap tiers — strong evidence) / doesn't (cap-specific — also a finding). Loud survivorship caveat from B-701 on every result.
★ **Evidence Claim:** staging, family smallcap; N trials = number of canonical claims, registered as a batch:
```json
{"kind": "factor", "factor": "<each canonical claim's selectors>", "universe_profile": "smallcap", "...": "unchanged"}
```
★ **Canonical value:** existing lab payloads, profile-keyed. ★ **Boundary:** none. ★ **Tests:** selector grammar with profile dimension. ★ **Do NOT touch:** the large-cap claims; the replication set (no "and also these three new factors").
Size: ~1–2 iterations. **Traps:** adding non-replication hypotheses to the batch; comparing across universes without the bias caveat (smallcap survivorship inflation is worse — the memo's number rides along).
**Journey:** replication batch registered → verdicts rendered per claim with the caveat; large-cap surfaces untouched. **Depends on:** B-702, B-404 (families), B-701's caveat numbers.

---

#### B-705 · Small-cap risk surfaces *(condensed)*
**Track:** T7 · **Quarter:** Q4 · **Priority:** P2 · **Status:** PROPOSED · **Difficulty:** EASY · **Failure mode:** none serious

**What & why:** before anyone acts on the smallcap board: B-201's risk card + B-210's tradability measures computed for the smallcap profile — where they matter far more (spreads and gaps are the whole story in small caps). Mandatory before the smallcap leaderboard loses its "experimental" banner (it likely never does).
★ **Evidence Claim:** `N/A`. ★ **Canonical value:** profile-keyed snapshot fields (same components). ★ **Boundary:** none. ★ **Tests:** reuse component fixtures. ★ **Do NOT touch:** large-cap thresholds.
Size: ~1 iteration. **Traps:** copying large-cap percentile context across universes (percentiles are within-profile).
**Journey:** smallcap detail shows risk card + tradability with within-profile percentiles. **Depends on:** B-702; B-201/B-210 built.

---

## Track 8 — Explainability & decision UX

Numbers the owner cannot interrogate breed either blind trust or blind doubt. This track makes every score, badge, and change *inspectable* — all of it re-reading existing canonical values.

| Card | Title | Pri | Qtr |
|------|-------|-----|-----|
| B-801 | Per-stock score waterfall | P1 | Q3 |
| B-802 | "What would change this label" panel | P1 | Q3 |
| B-803 | Historical-analog viewer (drill_samples lens) | P2 | Q4 |
| B-804 | As-of score-diff view ("what changed & why") | P2 | Q3 |
| B-805 | P(bear) reliability diagram | P2 | Q3 |
| B-806 | Per-factor economic-rationale pages | P2 | Q3–Q4 |

---

#### B-801 · Per-stock score waterfall
**Track:** T8 · **Quarter:** Q3 · **Priority:** P1 · **Status:** PROPOSED
**Difficulty:** EASY–MEDIUM · **Dominant failure mode:** UI-recompute

**What:** for each of the three scores on a stock detail: a waterfall of its components — each component's cross-sectional percentile, its config weight, and its contribution to the composite — read from the stored snapshot record (the components are computed at scan time; if any component values are not currently persisted in `record_json`, extend the snapshot additively at scan time — never recompute in the UI). NA components shown with the renormalization note (the engine already renormalizes available weights).

**Why it protects capital:** "Leadership 82" becomes "RS-vs-sector p91 × 0.2 + MA-stack p88 × …" — the owner can spot when a score is driven by one hot component vs broad strength, which changes how much to trust it.

**Data / plugs in at:** `scoring._raw_components`/pass-2 percentiles (persisted per name at scan time), `config.scores.*.weights`, stock-detail UI.
**Config surface:** none new.
**How:** (1) verify/extend component persistence (additive snapshot fields); (2) waterfall UI reading stored values + config weights; (3) NA/renormalization display. Size: ~1–2 iterations.
**Evidence Claim & ledger:** `N/A — must not introduce proven-language.`
**Canonical value:** component percentiles as stored snapshot fields; readers: detail page (and B-804).
**Anti-goal boundary:** none. **Tests:** snapshot-shape additive; fixture asserting waterfall sums to the composite under renormalization. **Do NOT touch:** scoring math.
**Acceptance / DoD:** waterfall reconciles exactly to the displayed score for every name (fixture + spot check); NA handling visible.

**Ready-to-paste journey block:**
```markdown
- **J-XX: Every score explains itself as a component waterfall**
  - Steps:
    1. Open `/stocks/{ticker}`; expand the Leadership score; assert a waterfall lists each component's percentile, weight, and contribution, summing (under the documented renormalization) to the displayed score.
    2. Find a name with an NA component; assert the waterfall shows it as NA with the renormalization note rather than a fabricated value.
    3. Repeat for Entry Quality and Risk.
  - Acceptance:
    - **Consistency (single source):** all waterfall values are stored snapshot fields plus config weights; the UI performs no scoring computation.
    - **Correctness:** the reconciliation to the displayed composite is exact for the spot-checked names.
    - **Honest status / anti-goals:** NA components visible; no new proven-language; weights shown are the live config's.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of one stock's three waterfalls, viewable via `demo.sh mcp-loop --session-live`.
```

**Traps:** recomputing percentiles in the UI "because the fields weren't stored" (extend storage instead); showing weights from a stale config copy (read live config; the B-306 stamp tells you which engine computed the stored values).
**Depends on:** none.

---

#### B-802 · "What would change this label" panel
**Track:** T8 · **Quarter:** Q3 · **Priority:** P1 · **Status:** PROPOSED
**Difficulty:** EASY–MEDIUM · **Dominant failure mode:** boundary-adjacent wording (facts about rules, not coaching)

**What:** setup statuses come from `classify_setup` over documented config thresholds. Per stock: show the rule distances — "Actionable requires Leadership ≥ 80 (now 76), Entry ≥ 70 (now 81), Risk ≤ 60 (now 55): one condition short" — plus which regime gate applies (Risk-off hard gate note when active). Pure rule arithmetic against stored scores; zero prediction.

**Why it protects capital:** kills the "why isn't this Actionable?" black-box feeling, and it teaches the methodology by exposure — the owner learns the rules by seeing them applied.

**Data / plugs in at:** stored scores + `config.decision_rules` + regime state; detail-page panel.
**Config surface:** none new.
**How:** rule-evaluation trace (engine-side, additive to the detail payload — the same code path as `classify_setup`, exposing its comparisons); panel UI. Size: ~1 iteration.
**Evidence Claim & ledger:** `N/A — must not introduce proven-language.`
**Canonical value:** the rule-trace in the detail payload (produced by the same classifier code — no parallel rule copy).
**Anti-goal boundary:** none — wording stays factual ("requires X, currently Y"); never "needs 4 more points, watch for it" (coaching drift).
**Tests:** classifier-trace fixtures (every status, every gate). **Do NOT touch:** `classify_setup` semantics (expose, don't alter).
**Acceptance / DoD:** trace matches the classifier verdict for every fixture status incl. the Risk-off gate; panel renders distances factually.

**Ready-to-paste journey block:**
```markdown
- **J-XX: Every setup label shows exactly which rules it met and missed**
  - Steps:
    1. Open a non-Actionable name; assert the panel lists each Actionable condition with its threshold and the name's current value, marking met/unmet.
    2. During a Risk-off regime (or fixture), assert the panel states the hard gate and that it overrides other conditions.
    3. Assert the trace is produced by the same classifier code path (no separate rule table in the frontend).
  - Acceptance:
    - **Consistency (single source):** the trace rides the detail payload from the classifier itself; the UI re-renders it.
    - **Correctness:** trace verdict equals the displayed setup status for all spot-checks.
    - **Honest status / anti-goals:** factual rule distances only; no coaching or prediction language; gate visibility honest.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of met/unmet conditions on two names, viewable via `demo.sh mcp-loop --session-live`.
```

**Traps:** re-implementing the rules in the frontend (they WILL drift); "almost Actionable" framing that reads as a nudge (state distances, not encouragement).
**Depends on:** none.

---

#### B-803 · Historical-analog viewer (drill_samples lens) *(medium detail)*
**Track:** T8 · **Quarter:** Q4 · **Priority:** P2 · **Status:** PROPOSED · **Difficulty:** MEDIUM · **Failure mode:** boundary (a forecast in costume — the critic's exact warning)

**What & rationale:** "names that looked like this, then what?" — nearest neighbors of the current stock's factor vector among historical snapshots (registered distance metric over the standard factor set), showing the neighbors' subsequent outcome **distribution** (n, spread, MDD — never a mean presented alone). Built as a thin lens over the existing `drill_samples` cohort machinery. Framing is load-bearing: "historical analogs' outcomes varied widely — distribution shown; this is not a forecast"; evidence badges appear ONLY where a registered claim actually backs a cohort (usually none — the viewer is exploratory).
**Plugs in at:** `drill_samples` + a similarity function (engine-side, registered metric: standardized Euclidean over the registered factor list); a detail-page section.
**Config:** `research.analogs: {k: 25, factors: [registered list], standardization: zscore}`.
★ **Evidence Claim:** `N/A — must not introduce proven-language` (exploratory; any claim about analog cohorts would be a registered event-study). ★ **Canonical value:** analog payload (engine). ★ **Boundary:** none IF framing holds (distribution + disclaimer mandatory, mean-only display banned). ★ **Tests:** metric fixture (identical vector → distance 0); NA factor handling. ★ **Do NOT touch:** `drill_samples` semantics.
Size: ~2 iterations. **Traps:** presenting the analogs' mean forward return as the headline (distribution or nothing); letting k or the factor list be tweaked per query (registered); implying causality.
**Journey:** analogs render with distances, outcome distribution, honest n, the disclaimer, and no mean-only headline. **Depends on:** none.

---

#### B-804 · As-of score-diff view ("what changed & why") *(medium detail)*
**Track:** T8 · **Quarter:** Q3 · **Priority:** P2 · **Status:** PROPOSED · **Difficulty:** EASY–MEDIUM · **Failure mode:** UI-recompute

**What & rationale:** between two as-of dates (default: latest vs previous snapshot): per-stock score/label changes decomposed by component (B-801's stored fields diffed), filtered against B-416's noise floor — "changes within normal jitter" collapsed by default, super-noise changes highlighted with their driving components. Watchlist gets a "what changed since you saved it" strip.
**Plugs in at:** stored snapshots (two dates) + noise-floor payload; diff computed engine-side; leaderboard/watchlist/detail surfaces.
**Config:** `display.diff.noise_floor_multiple: 1.0`.
★ **Evidence Claim:** `N/A`. ★ **Canonical value:** the diff payload (engine). ★ **Boundary:** none. ★ **Tests:** fixture diffs incl. membership changes (a name entering the universe is "new", not "+82 points"). ★ **Do NOT touch:** snapshots.
Size: ~1–2 iterations. **Traps:** diffing across universe-membership changes naively; recomputing components in the UI; treating the noise floor as significance (it's jitter context — say so).
**Journey:** diff view renders component-attributed changes with jitter-collapsed rows and honest membership handling. **Depends on:** B-801 (stored components), B-416 (floor).

---

#### B-805 · P(bear) reliability diagram *(condensed)*
**Track:** T8 · **Quarter:** Q3 · **Priority:** P2 · **Status:** PROPOSED · **Difficulty:** EASY–MEDIUM · **Failure mode:** small-n honesty

**What & why:** the HMM's P(bear) is the product's only probability — is it calibrated? Reliability diagram: bin historical P(bear) values, and per bin, the realized frequency of Bear/Correction phase within the following h days (causal labels), with bin counts. Scoped exactly to this one probability (the critic's fix for the vague "confidence calibration" idea).
**How:** binning + realized-frequency computation over the stored causal series; a market-phase-page panel. Size: ~1 iteration.
★ **Evidence Claim:** `N/A`. ★ **Canonical value:** calibration payload. ★ **Boundary:** none. ★ **Tests:** fixture with constructed probabilities → known bins. ★ **Do NOT touch:** HMM parameters (a badly calibrated diagram is a FINDING for the owner/B-1004 discussion, not a license to retune here).
**Journey (paste-ready):**
```markdown
- **J-XX: The bear-probability's historical calibration is visible**
  - Steps:
    1. Visit `/market-phase`; assert a reliability panel bins historical P(bear) and shows, per bin, the realized bear/correction frequency over the stated horizon with bin counts.
    2. Assert small bins render their n prominently and the panel states the causal labeling rule.
  - Acceptance:
    - **Consistency (single source):** the panel re-reads one calibration payload over the stored causal series.
    - **Correctness:** one bin re-verified offline matches.
    - **Honest status / anti-goals:** miscalibration displayed plainly; no parameter changes; n everywhere.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of the diagram, viewable via `demo.sh mcp-loop --session-live`.
```
**Traps:** labeling realized phases retrospectively; hiding the ugly bins. **Depends on:** phase series (exists).

---

#### B-806 · Per-factor economic-rationale pages *(condensed)*
**Track:** T8 · **Quarter:** Q3–Q4 · **Priority:** P2 · **Status:** PROPOSED · **Difficulty:** EASY · **Failure mode:** scope-creep (documentation, not marketing)

**What & why:** every lab factor gets a rationale page: the economic WHY (one paragraph, literature one-liner), formula + windows, its pre-registration lineage (registered claims, verdicts, graveyard links), decay/turnover stats (B-413/B-211 cross-links). This is the pre-registration culture made visible — a factor without a written prior is a red flag by construction.
**How:** extend the methodology catalog structure (completeness assertion updated) + links from lab pages. Size: ~1–2 iterations.
★ **Evidence Claim:** `N/A`. ★ **Canonical value:** catalog entries. ★ **Boundary:** none — tone rule: rationale ≠ endorsement ("the hypothesis is…", never "this works"). ★ **Tests:** methodology completeness (every lab factor has a rationale section). ★ **Do NOT touch:** factor math.
**Journey:** every lab factor links to a rationale page carrying prior, formula, lineage (verdicts incl. FAILs), cross-stats; completeness asserted. **Depends on:** none (richer after B-413/B-902).

---

## Track 9 — Research-process infrastructure (the weak-model era's guardrails)

Cheap cards that govern everything else. Build B-901/B-903/B-904 in Q1 — they are load-bearing for the whole year.

| Card | Title | Pri | Qtr |
|------|-------|-----|-----|
| B-901 | Generalized pre-registration registry (+ gate cross-check) | P1 | Q1 |
| B-902 | Negative-results graveyard page | P1 | Q2 |
| B-903 | Certification-budget accounting UI | P1 | Q1 |
| B-904 | Fast-test discipline CI guard | P1 | Q1 |
| B-905 | Weak-model contribution checklist | P2 | Q2 |
| B-906 | Data-source catalog upkeep | P3 | ongoing |
| B-907 | Replenishment protocol (executable form) | P2 | Q2 |

---

#### B-901 · Generalized pre-registration registry (+ gate cross-check)
**Track:** T9 · **Quarter:** Q1 · **Priority:** P1 · **Status:** PROPOSED
**Difficulty:** MEDIUM · **Dominant failure mode:** scope-creep (a registry, not a workflow engine)

**What:** one machine-readable registry consolidating every registered hypothesis: the proposer-guidance §4.x tables, this backlog's claim JSONs, revisit registrations (B-406), and future quarterly additions — as an append-only `state/pre-registrations.jsonl` (id, claim selectors, rationale, registered-by/date, source card, status). A `/research/registry` page renders it. **The teeth:** the post-decompose gate (`verify_claim.py`) cross-checks every incoming Evidence Claim against the registry and **refuses claims with no registration row** (config-gated enforcement, on after backfill).

**Why it protects capital:** pre-registration only binds if it is checked by a machine, not a convention. This single hook makes ad-hoc data mining *structurally* impossible for every future model working on the system — the highest-leverage governance card in the file.

**Data / plugs in at:** new state file + loader; `verify_claim.py` (registry lookup before referee); registry page (lab triple); backfill of existing registrations (proposer-guidance tables + already-certified claims as historical rows).
**Config surface:** `evidence.registry.enforce: false → true` after backfill.
**How:** (1) schema + backfill; (2) page; (3) gate cross-check behind flag; (4) flip after verification. Size: ~2 iterations.
**Evidence Claim & ledger:** `N/A — must not introduce proven-language.`
**Canonical value:** the registry file; readers: gate, registry page, B-902 lineage links.
**Anti-goal boundary:** none. **Tests:** gate fixtures (registered claim passes lookup; unregistered claim refused with a clear message). **Do NOT touch:** referee statistics; ledgers.
**Acceptance / DoD:** registry complete for all existing registrations; page renders; enforcement on and fixture-proven.

**Ready-to-paste journey block:**
```markdown
- **J-XX: Every evidence claim must match a pre-registration — enforced by the gate**
  - Steps:
    1. Visit `/research/registry`; assert it lists every registered hypothesis with selectors, rationale, registration date, source, and status (incl. historical backfills labeled as such).
    2. In the test environment, submit an iteration claim matching a registry row; assert the gate proceeds to the referee.
    3. Submit a claim with no registry row; assert the gate refuses it BEFORE any referee computation, with a message naming the registry requirement.
  - Acceptance:
    - **Consistency (single source):** the page and the gate read the same registry file.
    - **Correctness:** lookup matching is exact on selectors (fixture-proven).
    - **Honest status / anti-goals:** enforcement is on; refusals are loud; the registry is append-only (withdrawn registrations get status rows, never deletions).
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of the registry and a refused unregistered claim, viewable via `demo.sh mcp-loop --session-live`.
```

**Traps:** fuzzy matching (exact selectors or refuse — fuzziness reopens the mining door); editing rows (append status changes); registering retroactively to launder a mined result (registration dates are part of the audit trail — the quarterly review checks for suspicious same-day register-and-run patterns on surprising results).
**Depends on:** none. **Feeds:** B-404, B-406, B-902, every claim card.

---

#### B-902 · Negative-results graveyard page *(condensed)*
**Track:** T9 · **Quarter:** Q2 · **Priority:** P1 · **Status:** PROPOSED · **Difficulty:** EASY · **Failure mode:** UI-recompute

**What & why:** FAILs/INSUFFICIENTs live in the ledgers/registry but nothing makes them *browsable* — so a future model (or the owner in month 9) re-derives a dead idea from scratch. A `/research/graveyard` page: every non-PASS verdict + closed proposals, with selectors, verdict, date, deflation context, and the registry-lineage link ("registered as…, refused revisit unless…"). The system's institutional memory of what does NOT work.
**How:** read-compose from ledgers + registry; page. Size: ~1 iteration.
★ **Evidence Claim:** `N/A`. ★ **Canonical value:** none new (composition). ★ **Boundary:** none. ★ **Tests:** fixture rows render. ★ **Do NOT touch:** source files.
**Journey (paste-ready):**
```markdown
- **J-XX: Dead hypotheses are browsable so nobody retries them blindly**
  - Steps:
    1. Visit `/research/graveyard`; assert every non-PASS verdict renders with selectors, verdict kind, date, and its registration lineage.
    2. Assert closed proposals (e.g., the ma_stack closed FAIL) appear with their "permanent" marking.
    3. Assert each entry links to the revisit-protocol rule (B-406) stating what would qualify a re-test.
  - Acceptance:
    - **Consistency (single source):** the page re-reads ledgers + registry verbatim.
    - **Correctness:** one entry matches its ledger row.
    - **Honest status / anti-goals:** failures displayed as first-class information; no deletion path exists.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of the graveyard, viewable via `demo.sh mcp-loop --session-live`.
```
**Depends on:** B-901 (lineage links; can ship reading ledgers only).

---

#### B-903 · Certification-budget accounting UI *(condensed)*
**Track:** T9 · **Quarter:** Q1 · **Priority:** P1 · **Status:** PROPOSED · **Difficulty:** EASY–MEDIUM · **Failure mode:** UI-recompute

**What & why:** the honesty machinery spends real budgets — the Bonferroni divisor grows with every trial, Thresholdout charges the reusable holdout, LORD++ spends wealth. None of it is visible, so nothing stops a well-meaning model from quietly spending the year's statistical credibility in a month. A budget panel (on `/evidence` or `/research`): trials to date, current required_p, Thresholdout budget remaining, LORD++ wealth trajectory, spend-over-time chart — per family once B-404 lands. The quarterly review reads it; alerts (B-302) on threshold crossings.
**How:** the accounting exists inside referee/ledger machinery — expose it as one payload + panel. Size: ~1 iteration.
★ **Evidence Claim:** `N/A`. ★ **Canonical value:** budget payload (from the same accounting the referee uses — no parallel bookkeeping). ★ **Boundary:** none. ★ **Tests:** fixture claims → expected spend figures. ★ **Do NOT touch:** the accounting itself.
**Journey (paste-ready):**
```markdown
- **J-XX: The statistical budget is visible before it is spent**
  - Steps:
    1. Visit the budget panel; assert it shows: total trials, the current canonical required_p, Thresholdout budget remaining, and staging FDR wealth, each with a spend-over-time view.
    2. Submit a fixture claim in the test environment; assert the panel's figures move exactly as the referee's accounting dictates.
  - Acceptance:
    - **Consistency (single source):** the panel re-reads the referee/ledger accounting; no parallel computation.
    - **Correctness:** fixture spend matches hand computation.
    - **Honest status / anti-goals:** budget pressure is displayed, never smoothed; no proven-language.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of the budget panel, viewable via `demo.sh mcp-loop --session-live`.
```
**Depends on:** none. **Feeds:** B-404, B-1202.

---

#### B-904 · Fast-test discipline CI guard *(condensed)*
**Track:** T9 · **Quarter:** Q1 · **Priority:** P1 · **Status:** PROPOSED · **Difficulty:** EASY · **Failure mode:** scope-creep

**What & why:** the full suite already takes ~10 hours on the 30y basis; one careless real-seed test per month doubles it by year-end. A CI-stage guard: (a) new/changed test files must not import/open the real seed or production DB (static check with an explicit allowlist for the few sanctioned deep tests); (b) a per-file runtime budget on the fast lane (measured, configurable); violations fail CI with a message pointing at the synthetic-fixture pattern docs.
**How:** guard script + CI wiring + a short "how to write a fast test here" doc section. Size: ~1 iteration.
★ **Evidence Claim:** `N/A`. ★ **Canonical value:** none. ★ **Boundary:** none. ★ **Tests:** the guard's own fixtures (a violating test file is caught). ★ **Do NOT touch:** existing sanctioned deep tests (allowlist them explicitly).
**Journey:** a deliberately violating test file fails the guard with the instructive message; the allowlist is documented; the fast lane's runtime is reported. **Depends on:** none.

---

#### B-905 · Weak-model contribution checklist *(condensed)*
**Track:** T9 · **Quarter:** Q2 · **Priority:** P2 · **Status:** PROPOSED · **Difficulty:** EASY

**What & why:** a docs page (linked from `/methodology` and this file) with the end-to-end recipes a future model needs verbatim: add-a-factor (§D6 mirrored), add-a-lab, register-and-claim, refresh-a-golden (sanctioned path), the language bans, the do-not-touch defaults. Every recipe as a checklist with the exact files and the tests that prove each step. This card exists because instructions that live only in Fable 5's head are worthless in month 7.
**How:** write the doc; cross-link; keep in sync at quarterly reviews. Size: ~1 iteration.
★ **Evidence Claim:** `N/A`. ★ **Canonical value:** none. ★ **Boundary:** none. ★ **Tests:** none (docs). ★ **Do NOT touch:** n/a.
**Journey:** page exists, recipes complete (spot-execute one recipe end-to-end on a fixture as the acceptance demonstration). **Depends on:** Appendix D of this file (source material).

---

#### B-906 · Data-source catalog upkeep *(condensed)*
**Track:** T9 · **Quarter:** ongoing · **Priority:** P3 · **Status:** PROPOSED · **Difficulty:** EASY

**What & why:** Appendix B of this file is the data map; sources rot (URLs, rate limits, pricing). A quarterly-review checklist item: verify each catalog row (URL alive, terms unchanged, pricing current), update the appendix, note changes in the review record. No product surface.
★ All safety fields: `N/A` (documentation task). **Depends on:** B-1202 cadence.

---

#### B-907 · Replenishment protocol (executable form) *(condensed)*
**Track:** T9 · **Quarter:** Q2 · **Priority:** P2 · **Status:** PROPOSED · **Difficulty:** EASY

**What & why:** §0's replenishment protocol turned into an executable checklist used at each quarterly review (B-1202): inputs (graveyard, proposals backlog, budget panel, Appendix B, track statuses) → steps (harvest near-misses with changed preconditions; scan unexploited sources; draft new cards with rationale-before-data; owner sign-off; register via B-901) → outputs (new cards in this file + registry rows + updated track indexes). Includes the "suspicious pattern" check: any same-day register-and-run on a surprising winner gets flagged for owner review.
★ All safety fields: `N/A` (procedure + doc). **Journey:** first executed replenishment produces ≥1 new owner-approved card end-to-end. **Depends on:** B-901, B-902, B-903, B-1202.

---

## Track 10 — Gated machine learning (Q4, charter-first)

ML earns its place here only as a *disciplined comparison against strong baselines*, never as a black box feeding the board. **B-1001's charter binds every other card; nothing ML-derived ever surfaces without the full evidence path.** Expect INSUFFICIENT/FAIL outcomes and say so in every registration — with n≈120 quarterly walk-forward dates, most ML claims will honestly lack power. That is the system working.

| Card | Title | Pri | Qtr |
|------|-------|-----|-----|
| B-1001 | Anti-overfit ML charter | P1(gate) | Q4 |
| B-1002 | GBT ranker vs linear-blend baseline | P2 | Q4 |
| B-1003 | Meta-labeling: setup-failure filter study | P2 | Q4 |
| B-1004 | k-state HMM regime upgrade (conditional) | P3 | Q4+ |

---

#### B-1001 · Anti-overfit ML charter *(the gate)*
**Track:** T10 · **Quarter:** Q4 · **Priority:** P1 · **Status:** PROPOSED · **Difficulty:** EASY (writing) / HARD (discipline) · **Failure mode:** p-hack

**What:** a one-page charter merged into `/methodology`, binding all ML work: (1) features = registered, stored factors only (no feature mining); (2) validation = purged, embargoed walk-forward CV only — never random splits on overlapping series; (3) ONE model family + ONE registered hyperparameter grid per study, fixed ex ante; (4) staging-only claims; nothing ML touches a user-facing surface without canonical PASS + owner two-key; (5) stability requirements (feature-importance rank stability across folds; a model whose story changes per fold is noise); (6) honest-power statement in every registration (with ~120 independent dates, expect INSUFFICIENT); (7) no deep nets (sample sizes make them indefensible here); (8) all ML runs in the B-423 sandbox discipline.
**How:** write, review with owner, merge; the charter's existence is then cited by B-1002/1003/1004 registrations. Size: ~0.5–1 iteration.
★ **Evidence Claim:** `N/A`. ★ **Canonical value:** none. ★ **Boundary:** none. ★ **Tests:** none (policy; its teeth are the registry + gates). ★ **Do NOT touch:** n/a.
**Journey:** charter section renders in `/methodology`; B-1002's registration cites it clause-by-clause. **Depends on:** none. **Blocks:** B-1002/1003/1004.

---

#### B-1002 · GBT ranker vs linear-blend baseline
**Track:** T10 · **Quarter:** Q4 · **Priority:** P2 · **Status:** PROPOSED
**Difficulty:** HARD · **Dominant failure mode:** p-hack / lookahead (CV leakage on overlapping horizons)

**What:** the honest ML question: does a gradient-boosted tree ranker over the EXISTING stored factors beat the hand-weighted Leadership blend at ranking the cross-section? Protocol: features = registered factor set at each as-of; target = h=60 forward return rank; purged+embargoed walk-forward CV (train strictly before, purge the overlap window, test after); metrics = rank-IC and top-decile cohort outcomes vs the Leadership baseline's, with CIs; feature-importance stability across folds reported. If (and only if) the out-of-fold top-decile cohort looks materially better, register ONE staging claim on the model-score top-decile cohort. The model NEVER surfaces scores to users in this card regardless of outcome.

**Why it protects capital:** either outcome pays: a win (after the referee) means the blend leaves real ordering information on the table; a loss retires the "should we ML this?" question with evidence instead of vibes.

**Data / plugs in at:** stored factors + forward returns; B-423 sandbox; a research report page; scikit-learn/lightgbm-class dependency (adding a dependency = owner approval note in the iteration).
**Config surface:** the registered grid (small: depth × trees × learning rate, ≤ 12 combos), CV windows, purge/embargo lengths — all ex ante.
**How:** (1) registration citing the charter; (2) CV harness with purge/embargo (fixture-proven: a deliberately leaky split is caught by the harness's own overlap assertion); (3) train/evaluate; (4) report (IC, cohort stats, importance stability); (5) optional single claim if criteria met. Size: ~2–3 iterations.
**Evidence Claim & ledger:** staging; ≤1 trial, only if the registered promotion criteria are met:
```json
{"kind": "factor", "factor": "ml_rank_gbt_v1", "slice_kind": "decile", "decile": 10, "horizon": 60, "direction": "positive"}
```
**Canonical value:** the study artifact; reader: report page. The model score is NOT a stored snapshot factor unless/until certified + owner-approved (then it enters via §D6 like any factor).
**Anti-goal boundary:** none (nothing user-facing changes).
**Tests that will break:** none; new harness fixtures (leak detection, determinism via seeds).
**Do NOT touch:** scoring/leaderboard; the registered grid after first results ("just one more depth" is the classic sin).

**Acceptance / DoD:** leak-detection fixture green; out-of-fold report with CIs + stability; baseline comparison honest (including a possible loss); decision recorded.

**Ready-to-paste journey block:**
```markdown
- **J-XX: A GBT ranker is tested against the Leadership blend under charter discipline**
  - Steps:
    1. Assert the study's registration cites the ML charter and fixes: feature list, target, CV protocol (purge/embargo lengths), the hyperparameter grid, and the promotion criteria — dated BEFORE results.
    2. Visit the study report; assert out-of-fold rank-IC and top-decile cohort outcomes render for model vs baseline with CIs, plus feature-importance stability across folds.
    3. Assert the leak-detection check (purged/embargoed splits) is part of the harness tests and passes.
    4. Assert no user-facing score or surface changed.
  - Acceptance:
    - **Consistency (single source):** the report re-reads the study artifact; features come from stored snapshot factors only.
    - **Correctness:** one fold's metrics re-verified offline match; seeds make the run reproducible.
    - **Honest status / anti-goals:** a losing model is reported as plainly as a winning one; no surface changes; any claim goes to staging under the registered criteria only.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of the comparison report, viewable via `demo.sh mcp-loop --session-live`.
```

**Traps:** random-split CV on overlapping-horizon targets (the leak — purge+embargo or nothing); grid creep; retraining after peeking at the test windows; celebrating in-fold numbers (out-of-fold only, everywhere).
**Depends on:** B-1001, B-423, B-901.

---

#### B-1003 · Meta-labeling: setup-failure filter study *(medium detail)*
**Track:** T10 · **Quarter:** Q4 · **Priority:** P2 · **Status:** PROPOSED · **Difficulty:** HARD · **Failure mode:** p-hack

**What & rationale:** López de Prado's meta-labeling, pointed defensively: given an Actionable setup (the primary signal stays untouched), a small classifier predicts "this instance fails" (hits invalidation before reaching a registered gain threshold) from registered features (risk components, phase, dispersion, gap profile). Study question: does filtering the lowest-confidence tercile improve the cohort's drawdown profile without gutting its returns? Same charter discipline as B-1002 (purged CV, fixed grid, out-of-fold only). Descriptive report first; optional single registered claim on the filtered cohort.
```json
{"kind": "event-study", "subject": "actionable_meta_filtered", "horizon": 20, "direction": "positive"}
```
★ **Do NOT touch:** `classify_setup` / the displayed Actionable label (the filter is a STUDY; adoption would be an owner decision surfaced as a clearly-labeled secondary view, its own future card). **Traps:** label definition drift (the "failure" definition is registered ex ante); leaking outcome-window information into features (features strictly ≤ as-of).
**Depends on:** B-1001, B-423, B-201 (features). Size: ~2 iterations.

---

#### B-1004 · k-state HMM regime upgrade *(conditional; condensed)*
**Track:** T10 · **Quarter:** Q4+ · **Priority:** P3 · **Status:** PROPOSED · **Difficulty:** HARD · **Failure mode:** scope-creep

**What & why:** ONLY if B-602 shows the current 2-state HMM leaves clear calibration on the table (B-805's diagram informs this): a registered study of a 3-state variant (e.g., calm-bull / choppy / stress) on a registered observation set, compared via B-602-style pre-registered criteria (classification of subsequent phases, Brier). Owner design discussion mandatory before any code. Live phase engine untouched until canonical-grade evidence + two-key.
★ All the B-602 protocol rules apply verbatim. **Traps:** state-count shopping; emissions retuned per result. **Depends on:** B-602 outcome, B-805, owner discussion.

---

## Track 11 — Product hardening (slim, year-round filler)

Safe, always-available work for weak models; each card small, none touching decision logic.

| Card | Title | Pri | Qtr |
|------|-------|-----|-----|
| B-1101 | Performance budgets + regression checks | P2 | Q2+ |
| B-1102 | API contract snapshot + drift tests | P2 | Q2+ |
| B-1103 | Error-state UX sweep | P2 | Q2+ |
| B-1104 | DB maintenance & size monitoring | P3 | Q3+ |
| B-1105 | One-command rebuild with verification receipt | P2 | Q2+ |
| B-1106 | runs/ retention policy | P3 | Q3+ |

#### B-1101 · Performance budgets + regression checks *(condensed)*
**What & why:** the 30y basis made pages heavier (goal.md flagged charts); set measured budgets for the hot paths (`/stocks`, stock detail incl. chart, `/market-phase`, factor lab) against the fixture DB in CI; fail on regression beyond tolerance. Generalizes J-10's chart-performance acceptance product-wide.
**How:** timing harness + budget config + CI stage. Size: ~1 iteration. ★ **Claims/Canonical/Boundary:** `N/A`/none/none. ★ **Tests:** the harness itself. ★ **Do NOT touch:** endpoint behavior (measurement only; fixes are follow-up cards per finding).
**Journey:** budgets documented; CI report shows per-path timings vs budget; a deliberate fixture slowdown is caught. **Depends on:** none.

#### B-1102 · API contract snapshot + drift tests *(condensed)*
**What & why:** the frontend and MCP tools depend on payload shapes that only tests-by-usage protect; commit the FastAPI OpenAPI schema as a snapshot with a drift test — additive changes update the snapshot deliberately; breaking changes fail loudly with the diff.
**How:** schema export + snapshot test + refresh procedure note. Size: ~1 iteration. ★ Fields: `N/A`/none/none. ★ **Do NOT touch:** payloads (this card only observes).
**Journey:** snapshot committed; a fixture breaking-change is caught with a readable diff; the sanctioned refresh path is documented. **Depends on:** none.

#### B-1103 · Error-state UX sweep *(condensed)*
**What & why:** every surface must render an honest failure state (no blank panels, no stale-data-as-fresh): fault-injection fixtures per endpoint (5xx, timeout, empty, malformed) and a sweep asserting each page shows an explicit error/degraded state consistent with the B-301 banner language.
**How:** fault-injection harness + per-page assertions + fixes for gaps found. Size: ~2 iterations. ★ Fields: `N/A`/none/none. ★ **Do NOT touch:** API semantics.
**Journey:** injected faults on three key pages render explicit honest states; the sweep is in CI. **Depends on:** B-301 (language consistency).

#### B-1104 · DB maintenance & size monitoring *(condensed)*
**What & why:** SQLite under a growing 30y × 548 load: index audit (the `(symbol,date)` index exists — verify coverage for new query shapes), scheduled `VACUUM`/`ANALYZE` guidance, size/growth chart on `/data`, growth alarms into readiness at registered thresholds.
**How:** audit + job + panel. Size: ~1 iteration. ★ Fields: `N/A`/artifact/none. ★ **Do NOT touch:** schema.
**Journey:** size panel renders with growth trend; alarm fires at fixture threshold. **Depends on:** none.

#### B-1105 · One-command rebuild with verification receipt *(condensed)*
**What & why:** "rebuild the world" (DB from seed → backfills → warmup) exists as scattered jobs; wrap into one command emitting a **receipt**: row counts, span, checksums, snapshot count, warmup status — diffed against expected values (ties into B-103/B-306). The disaster-recovery and new-machine story in one artifact.
**How:** orchestrating script + receipt + fixture drill. Size: ~1 iteration. ★ Fields: `N/A`/receipt artifact/none. ★ **Do NOT touch:** the individual jobs' logic.
**Journey:** one command on a fixture seed produces a green receipt; a tampered fixture produces a red diff. **Depends on:** none.

#### B-1106 · runs/ retention policy *(condensed)*
**What & why:** `runs/goal-session-*` grows without bound (116 iterations already); a retention policy: what is永-keep (state/, ledgers, registries — NEVER pruned), what archives (old iteration working dirs → tar), what prunes after owner-approved age; a dry-run report before any deletion; policy documented.
**How:** policy doc + archive script with dry-run + first supervised run. Size: ~1 iteration. ★ Fields: `N/A`/none/none. ★ **Do NOT touch:** `state/` ever; anything without a dry-run + owner ack.
**Journey:** dry-run lists candidates correctly; state/ provably untouched; archive restorable. **Depends on:** none.

---

## Track 12 — Investor workflow (the ritual around the engine)

The system is only as good as the owner's weekly loop around it. Personal-process cards carry the same boundary discipline as everything else.

| Card | Title | Pri | Qtr |
|------|-------|-----|-----|
| B-1201 | Monthly review pack | P2 | Q2 |
| B-1202 | Quarterly strategy-review ritual (replenishment engine) | P1 | Q1-end, then quarterly |
| B-1203 | Sunday research sheet | P2 | Q3 |
| B-1204 | As-of replay trainer | P3 | Q4 |
| B-1205 | CSV/JSON exports | P2 | Q2 |
| B-1206 | Personal risk-policy display — BOUNDARY | P3 | Q3+ |
| B-1207 | Alert acknowledgment audit trail | P3 | Q3 |
| B-1208 | ◇ Watchlist outcome retrospective | P2 | Q3 |

#### B-1201 · Monthly review pack *(condensed)*
**What & why:** B-307's weekly digest, monthly and deeper: the month's phase/severity narrative (factual), edge-health trajectories per claim, graveyard additions, budget spend delta, data-quality summary, journal adherence counts (if B-303 exists — counts only, no P&L), notable universe events. Generated artifact under reports; the owner's month-end hour.
**How:** compose from existing artifacts (zero new computation), monthly job + page. Size: ~1 iteration. ★ Fields: `N/A`/none/none — language rules apply. ★ **Do NOT touch:** sources.
**Journey:** fixture month renders all sections; spot-checked figures byte-match sources; no imperative verbs. **Depends on:** B-307 pattern; richer with B-305/B-903.

#### B-1202 · Quarterly strategy-review ritual — the replenishment engine
**Track:** T12 · **Quarter:** Q1-end, then quarterly · **Priority:** P1 · **Status:** PROPOSED · **Difficulty:** EASY (tooling) / it's a ritual · **Failure mode:** skipping it

**What:** the institutionalized loop that keeps this backlog alive after Fable 5: a generated **review workbook** (one artifact) collating: track statuses from this file, the budget panel (B-903), graveyard additions (B-902), lifecycle states (B-305), data-source catalog checks (B-906), and open boundary decisions — plus the B-907 replenishment checklist. The owner + whatever model is available walk it together; outputs are recorded: card status updates in this file, new registered cards, re-prioritized quarters, retired tracks.
**Why:** the critic's sharpest structural point — a backlog without a review ritual is a list that rots. This card is why the file stays sufficient for a year and beyond.
**How:** workbook generator (compose; no new stats) + the documented ritual steps + calendar note. Size: ~1 iteration to build; recurs quarterly.
★ **Evidence Claim:** `N/A`. ★ **Canonical value:** the workbook artifact. ★ **Boundary:** none. ★ **Tests:** workbook fixture. ★ **Do NOT touch:** this file's history (reviews append status changes, never rewrite past decisions).
**Journey (paste-ready):**
```markdown
- **J-XX: A quarterly review workbook drives the backlog's living maintenance**
  - Steps:
    1. Generate the review workbook; assert it collates: per-track backlog statuses, certification-budget state, the quarter's graveyard additions, claim lifecycle states, data-source check results, and open boundary decisions.
    2. Assert the workbook embeds the replenishment checklist with space for recorded outcomes (new cards, retirements, re-prioritizations).
    3. Assert the completed workbook is archived and the backlog file's statuses were updated in the same change.
  - Acceptance:
    - **Consistency (single source):** every workbook figure re-reads its canonical artifact.
    - **Correctness:** spot-checked figures match sources.
    - **Honest status / anti-goals:** factual; skipped sections render as "not run", never silently absent.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of one workbook, viewable via `demo.sh mcp-loop --session-live`.
```
**Traps:** letting the workbook compute new statistics (compose only); reviews that don't write back (the recorded outcome IS the ritual). **Depends on:** richer with B-305/902/903; start at Q1-end regardless.

#### B-1203 · Sunday research sheet *(condensed)*
**What & why:** one printable/exportable sheet composing the owner's weekly session: preflight verdict, phase/regime + transition card if fresh, the Actionable/watch lists with each name's risk-budget card summary, watchlist X-ray headline (ENB, top cluster), upcoming-events flags (B-209), open alerts. Pure composition, print CSS, as-of stamped.
**How:** sheet endpoint/page reading existing payloads. Size: ~1 iteration. ★ Fields: `N/A`/none/none. ★ **Do NOT touch:** sources; no advice framing ("candidates", never "buys").
**Journey:** sheet renders all sections from canonical payloads with the as-of stamp; print layout verified; language check green. **Depends on:** B-301/B-201/B-204/B-209 (compose what exists; degrade gracefully).

#### B-1204 · As-of replay trainer *(condensed)*
**What & why:** judgment practice on immutable history: pick a past as-of (the switcher exists), see the board exactly as it was, step forward snapshot-by-snapshot with a "what happened next" reveal (prices, phase, setup outcomes). No scoring of the user, no gamification — a guided tour of the system's own honest record, which doubles as the best onboarding for a new model/human.
**How:** guided stepper UI over existing as-of routing + snapshots. Size: ~1–2 iterations. ★ Fields: `N/A`/none/none. ★ **Do NOT touch:** snapshots; no fabricated "you would have made X" (banned — show what the BOARD showed, then what prices did, period).
**Journey:** pick date → board renders as-of → step forward reveals subsequent stored states; no wealth language anywhere. **Depends on:** as-of infrastructure (exists).

#### B-1205 · CSV/JSON exports *(condensed)*
**What & why:** the owner's data belongs to the owner: export endpoints + buttons for the leaderboard (current as-of), evidence ledger view, watchlist (with X-ray summary), journal (if built), each export byte-consistent with the displayed data and stamped (as-of, engine version B-306, generation time).
**How:** export serializers reading the same payloads the pages render. Size: ~1 iteration. ★ Fields: `N/A`/none/none. ★ **Do NOT touch:** payload semantics (exports mirror, never extend).
**Journey:** each export downloads; spot-check rows byte-match the rendered surface; stamps present. **Depends on:** none.

#### B-1206 · Personal risk-policy display — **BOUNDARY** *(condensed)*
**What & why:** the owner writes a personal policy ("max N concurrent positions; no adds in Bear phase; risk ≤ 0.5%/idea"); the product stores it as **verbatim owner text** and renders it beside relevant surfaces (watchlist, Sunday sheet) — display only, no compliance evaluation, no product-generated policy.
★ **Anti-goal boundary — amendment required:**
> - **Personal-policy display exception (owner-approved <date>):** the product MAY store and display owner-authored policy text beside relevant surfaces, provided the text is rendered verbatim, the product neither generates policy statements nor evaluates compliance, and no quantities are computed from it. *(scoped exception to "decision-quality only")*
**How:** policy text storage + display slots. Size: ~1 iteration. ★ **Tests:** verbatim rendering; no evaluation code paths. ★ **Do NOT touch:** any computation on the policy text.
**Journey:** amendment confirmed; policy text renders verbatim where configured; no compliance indicators exist. **Depends on:** amendment. (Compliance *evaluation*, if the owner ever wants it, is a NEW boundary discussion — likely with B-303/B-204 as inputs.)

#### B-1207 · Alert acknowledgment audit trail *(condensed)*
**What & why:** alerts that can be missed are alerts that don't exist: an ack affordance per alert; append-only ack events (who=owner, when); an "unacknowledged critical alerts" counter that feeds the preflight banner (B-301) — critical alerts don't age out silently.
**How:** ack events + counter + banner wiring. Size: ~1 iteration. ★ Fields: `N/A`/ack-state payload/none. ★ **Do NOT touch:** alert content; no auto-ack.
**Journey:** ack an alert → recorded with timestamp; unacked critical alert visibly holds the preflight at DEGRADED-with-reason. **Depends on:** B-302, B-301.

#### B-1208 · ◇ Watchlist outcome retrospective *(condensed)*
**What & why:** the watchlist already stores `entry_close` and `price_since_added`; aggregate them honestly: distribution of saved-name outcomes vs SPY and vs the universe median over matched windows, by phase-at-add and by setup-at-add — **percent space, research-list framing** ("outcomes of names you saved", explicitly NOT portfolio returns — no position data exists), n-labeled. The owner learns what their *selection* habit adds or costs relative to the board's own cohorts.
**How:** aggregation over watchlist rows + stored snapshots/bars; a watchlist section. Size: ~1 iteration. ★ Fields: `N/A`/one payload/none — framing rule binding. ★ **Do NOT touch:** watchlist schema.
**Journey:** retrospective renders distributions vs benchmarks with the research-list disclaimer and n; a fixture confirms matched-window math. **Depends on:** none.

## Appendix A — Statistical guardrails cheatsheet (read before ANY claim work)

**A1. Walk-forward, always.** Anything evaluated on history must respect time's arrow: parameters/models are chosen using only data BEFORE each evaluation point; outcomes measured only AFTER it. The engine's conventions: scoring reads `bars_asof(D)` (≤ D); forward returns read bars strictly > D; the walk-forward cadence is quarterly over ~30 years ⇒ **~120 independent as-of dates**. That 120 is the system's fundamental statistical budget — most "why is this INSUFFICIENT?" questions end there.

**A2. Purge and embargo.** With overlapping forward windows (h=60 returns computed quarterly), adjacent training/testing samples share information. The referee's sealed holdout **purges** the overlap and **embargoes** a buffer after the split; any new CV harness (B-1002/1003) must do the same or its results are leakage, not evidence.

**A3. Sample floors.** `walk_forward.min_sample` (30) is the display floor; the referee separately requires enough independent holdout DATES (it counts dates, not correlated same-date names — 500 stocks on one crash day ≈ one observation). Below floors: render NA / expect INSUFFICIENT. Never lower a floor to make a result appear.

**A4. Multiple testing.** Every hypothesis ever tested tightens the bar for all: canonical ledger uses **Bonferroni** (`required_p = α / n_trials`, divisor grows monotonically); staging uses **LORD++ online-FDR** (a renewable "wealth" spent per test, replenished by discoveries). Practical rules: batch-register hypotheses (B-901) so the trial count is honest; check the budget panel (B-903) before proposing scans; families (B-404) partition the accounting but NEVER resurrect the graveyard.

**A5. Block bootstrap.** Return series are autocorrelated; i.i.d. resampling fabricates certainty. The referee's **circular moving-block bootstrap** (block length inferred from the series) is the house method — reuse it (B-106 helper) for any CI/resampling need. An i.i.d. bootstrap anywhere in this codebase is a bug.

**A6. External honesty diagnostics.** **Deflated Sharpe Ratio**: the observed Sharpe discounted for the number of trials and non-normality; DSR ≤ 0 means "consistent with selection luck". **PBO** (probability of backtest overfitting, via combinatorially symmetric cross-validation): the chance the in-sample winner underperforms out-of-sample; ≈50% = coin flip. Both are DIAGNOSTICS on `/evidence` (B-107) — the referee verdict remains the bar.

**A7. The graveyard rule.** FAIL/INSUFFICIENT closes the hypothesis. No selector tweaks, no horizon shopping, no threshold nudges, no "one more year of data" next month. Revisits ONLY via B-406's preconditions, registered, citing the corpse. This rule is what makes every surviving badge mean something.

**A8. P-hacking signatures (self-audit — if you catch yourself doing any of these, stop):** trying multiple deciles/horizons/regimes and reporting the winner · choosing metrics or CV splits after seeing results · re-running a FAILed claim with adjusted selectors · tuning config thresholds and re-testing in the same breath · widening/narrowing an event definition to harvest events · registering a hypothesis the same day its "surprising" result appears (B-907 flags this pattern) · quietly relaxing a floor or an α · comparing against the weakest control available.

**A9. Pre-claim checklist (every Evidence Claim, before the gate):**
1. Registry row exists (B-901) with an economic rationale written BEFORE any data peek.
2. Exactly ONE hypothesis; selectors final; direction stated.
3. Ledger routing chosen (staging default) and family named (post-B-404).
4. The cohort's expected independent-date count sanity-checked against A3.
5. Costs/timing convention stated (gross close-to-close vs B-101 realistic) — h≤10 claims: realistic only.
6. Survivorship caveat acknowledged (pre-B-112: edges are upper bounds).
7. On-FAIL plan: graveyard entry, card status update, no retry.
8. The journey block carries the claim verbatim in step 1 (house style).
9. Nothing in the UI will recompute the certified statistic (canonical-value declaration written).
10. The walkthrough line is present (`[NEW]`, `demo.sh`).

**A10. Language rules (user-facing text, binding):** no imperative trade verbs; no return promises or price targets; no wealth-path projections; distributions labeled as history ("historically saw"), never expectation ("you can expect"); "Proven" appears ONLY from a passing canonical ledger entry via the standard resolution path; insufficient evidence says so in words, never hides in absence.

---

## Appendix B — Data-source catalog (verify pricing/terms at use time; last checked 2026-07)

### Free sources

| Source | What | Access | Causality & quality notes |
|--------|------|--------|---------------------------|
| **Stooq** (current provider) | Adjusted daily OHLCV, US equities/indices, ~30y | Bulk archive (local at `data/d_us_txt`, the iter-16-18 basis); per-symbol network endpoint is IP-blocked for this host — use the `stooq-local` provider path | Back-adjusts WHOLE history on each dividend/split ⇒ committed seed drifts vs fresh fetches (seam risk — B-113/B-304 exist for this). One adjustment basis per name end-to-end; never splice vendors. |
| **SEC EDGAR company-facts** | XBRL fundamentals, all US filers | Bulk: `sec.gov/Archives/edgar/daily-index/xbrl/companyfacts.zip`; per-CIK: `data.sec.gov/api/xbrl/companyfacts/CIK{10d}.json`; descriptive User-Agent + contact email REQUIRED; ~10 req/s courtesy | Every fact carries its `filed` date — THE causality key (usable from filed, never period-end). Tag drift across filers ⇒ registered fallback tag lists (B-501). |
| **SEC EDGAR submissions** | Filing event dates (10-Q/10-K/8-K + items) | `data.sec.gov/submissions/CIK{10d}.json` (+archived pages) | 8-K Item 2.02 = results announcement. Filed history only; never fabricate forward dates. |
| **SEC ticker↔CIK map** | Symbol mapping | `sec.gov/files/company_tickers.json` | Tickers change; map as-of ingest, log unmapped honestly. |
| **FRED** | Macro series (T10Y2Y, BAMLH0A0HYM2, UNRATE, DTWEXBGS wired; DFII10, T5YIE, NFCI, ICSA, VIXCLS, VXVCLS candidates) | Free API key | **Current-vintage = revised history.** Market-derived series ≈ unrevised (lag-only OK); statistical series REQUIRE vintage handling (B-601). `publication_lag_days` per series is already the house pattern. |
| **ALFRED** | FRED vintages (first prints) | Same API with `realtime_start/realtime_end` | The fix for revision lookahead; study paths use this where B-601's policy says `vintage`. |
| **CBOE** | VIX / VIX3M history CSVs | cboe.com historical data pages | Market-derived; also on FRED (VIXCLS/VXVCLS). |
| **Community S&P 500 historical constituents** | Point-in-time membership approximation | GitHub datasets (search "S&P 500 historical components"); CHECK license | Imperfect, community-maintained — use for AUDITS (B-111/B-419) with agreement-rate framing, never as certified ground truth. |
| **Ken French data library** | Factor benchmark returns (HML/SMB/UMD…) | mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html | Unexploited so far — replenishment-pool candidate: external attribution context for our cohorts. Monthly, revised occasionally. |
| **Nasdaq Trader symbol directory** | Current listings metadata | nasdaqtrader.com symbol directory files | Listing status snapshots; useful for pool refresh (B-309). |

### Paid sources (each requires owner approval per CLAUDE.md; costs are last-known — verify)

| Vendor | ~Cost | Unlocks | Notes / fallback |
|--------|-------|---------|------------------|
| **Norgate Data** (US Platinum tier) | ≈ US$50/mo | **Delisted stocks + historical index constituents** — the survivorship fix (B-112); clean adjustment basis | Prices/membership only (no fundamentals). Fallback: stay on Stooq + B-111 disclosed bias band. |
| **Sharadar via Nasdaq Data Link** (Core US bundle: SEP+SF1+TICKERS) | ≈ US$60/mo | Delisted-inclusive prices AND standardized fundamentals — one vendor covering B-112 **and** Track 5's paid upgrade | The synergy pick if fundamentals matter (decision memo B-112). Fallback: EDGAR facts (free, messier tags). |
| **EODHD** | ≈ US$20–80/mo tiers | Cheaper EOD + fundamentals + some delisted coverage | Point-in-time rigor weaker than the two above — verify before trusting for survivorship claims. |

**Banned regardless of budget:** scraped unofficial earnings calendars; news/social sentiment feeds (owner's non-direction); any source whose history silently rewrites without vintages.

---

## Appendix C — goal.md interop reference (formats verified against `docs/goal.md` @ 2026-07-06)

### C1. Journey block, house style
Human-curated journeys go ABOVE the `<!-- AUTO:journeys -->` marker in `docs/goal.md`; only the goal-proposer writes between `<!-- AUTO:journeys -->` and `<!-- /AUTO:journeys -->`. Assign `J-XX` = the next unused journey number at paste time. Keep the Walkthrough line's session id current (`mcp-loop` today). Shape (verified against J-01 and J-06/J-09; the machine-era 4-part Acceptance is the safe default for everything new):

```markdown
- **J-XX: <Title>**
  - Steps:
    1. <numbered, concrete, assert-style steps; for claim-bearing iterations, step 1 carries the
       machine-readable `## Evidence Claim` JSON inline and states that the post-decompose gate
       certifies it BEFORE any code is built; a non-PASS verdict blocks the iteration>
    2. …
  - Acceptance:
    - **Consistency (single source):** <the canonical value(s) read verbatim; no new computing module
      or serving endpoint unless the card explicitly introduces one>
    - **Correctness:** <displayed numbers byte-match the engine computation for the same as-of>
    - **Honest status / anti-goals:** <"Proven" only from a passing ledger entry; NA/insufficient
      honesty; no forecast/imperative language; determinism + no-lookahead>
    - **Walkthrough:** a `[NEW]`-flagged demo-narrator walkthrough of <the new surface>, viewable via
      `demo.sh mcp-loop --session-live`.
```

### C2. Evidence Claim JSON forms (fenced under a `## Evidence Claim` heading in the iteration spec; inline in journey step 1)
- Factor decile: `{"kind":"factor","factor":"<key>","slice_kind":"decile","decile":10,"horizon":20,"direction":"positive"}`
- Explicit canonical promotion: add `"ledger":"canonical"` (default is staging).
- Combination/conditioned legs: `"condition":["<factor>:<side>:<quantile>", …]` (e.g., `"leadership_score:top:0.5"`).
- Regime-conditioned: `{"kind":"regime-phase-factor","factor":"<key>","slice_kind":"decile","decile":10,"regime":"<label>","horizon":20,"direction":"positive"}`.
- Event-study: `{"kind":"event-study","subject":"<registered-subject>","horizon":20,"direction":"positive"}`.
- New selector dimensions introduced by cards in this file (extend the grammar + its fixtures in the same iteration): `"slice_kind":"decile_spread","deciles":[10,1]` (B-401) · `"convention":"next_open_net"` (B-101/B-409) · `"universe_profile":"smallcap"` (B-704) · `"family":"<name>"` (B-404) · `"sector":"<key>"` (B-403).

### C3. Gate & ledger mechanics (what actually happens to a claim)
`verify_claim.py` (post-decompose gate) referees the claim BEFORE implementation: sealed out-of-sample holdout + SPY control + multiple-testing deflation → verdict appended to `runs/goal-session-<sid>/state/staging-ledger.jsonl` (default) or `certified-claims.jsonl` (explicit canonical) → **non-PASS = exit 3 = the iteration is blocked**. That is the system working; the response is the graveyard, not a retry. `/evidence` renders ONLY canonical; "Proven" badges resolve ONLY through the evidence-status path. After B-901: the gate first refuses any claim without a pre-registration row.

### C4. Registration mirrors
Every registered candidate ALSO gets a row in `project-extensions/proposer-guidance.md` §4.x (the pre-registered candidate tables — markdown rows with economic rationale), and post-B-901 a `state/pre-registrations.jsonl` row. One hypothesis, three synchronized records: this file's card, the guidance table, the registry.

---

## Appendix D — Trendora internals map (for models that have never seen this codebase)

### D1. End-to-end flow (all paths under `apps/backend/app/`)
`seed_loader.py` loads committed CSVs → `engine/universe_resolver.py` resolves point-in-time membership per as-of (4 gates: history/staleness/price/ADV over `data/seed/universe_pool.csv`) → `engine/scoring.py` computes everything per member in one pass (3 scores from `engine/indicators.py` components, setup status via `engine/setups.py`, invalidation level, patterns via `engine/patterns.py`, stored factors) → `engine/scanner.py` persists ONE immutable snapshot per as-of (`ScannerRun`/`ScannerResult`, `record_json` is the full record) → `engine/snapshot_serving.py` re-serves stored rows (never recomputes) → `engine/forward_testing.py` appends realized forward returns/excursions (close-on-D entry; horizons [1,5,10,20,60]; quarterly cadence; controls; MDD; survivorship label) → `api/*.py` FastAPI routes → Next.js pages in `apps/frontend/app/` → an MCP server (`app/mcp/server.py`) exposes read tools + `verify_edge`. Regime: `engine/regime.py` (6 labels; breadth+MA-stack+NH/NL+VIX gate). Market phase: `engine/market_phase.py` (5 phases, severity 0-100, 2-state HMM P(bear), velocity, episodes, recovery-turn — all causal). Research labs: `compute_*` in `engine/research.py` + `api/research.py` + `apps/frontend/app/research/<lab>/`. Evidence: `engine/referee.py` (sealed holdout + purge/embargo + block bootstrap + Bonferroni + Thresholdout) + `engine/ledger.py` + `engine/online_fdr.py` (LORD++) + `engine/forward_walk.py` (renewing holdout) + `engine/evidence.py` → `/evidence`. Data ops: `engine/data_manager.py` (FETCH/BACKFILL/rebuild jobs, availability/gap reports), `engine/readiness.py`, `engine/warmup.py`.

### D2. Where new things plug in
- **Indicator:** pure function in `engine/indicators.py` — window-as-argument, NA-graceful, zero literals.
- **Scoring component:** oriented raw in `scoring._raw_components` (≈`scoring.py:93`) + a weight key under `config.scores.<score>.weights`; cross-sectional keys auto-percentile in pass 2 (≈`:315`); macro-constant keys belong in `CONTEXTUAL_KEYS` (≈`:54`). **Never do this without the owner + adaptive-arc path.**
- **Stored (lab-only) factor:** the stored-factors block in `scoring.score_stocks` (≈`:368`) + additive `ScannerResult`/`record_json` field + `config.research.factor_lab.factors` entry.
- **Pattern:** detector in `engine/patterns.py` (same dict contract) + `config.patterns.<name>` + call in `score_stocks` (≈`:353`) + `is_<name>` mirror on `ScannerResult` (`models.py` ≈`:257`) + a methodology entry (completeness is asserted in `methodology.build_catalog` ≈`:58`).
- **Setup status:** `setups.ALL_STATUSES` + `classify_setup` + `config.decision_rules` + methodology entry.
- **Regime input:** `regime._universe_stats`/inputs (≈`:104`) + `config.regime.weights` (NA-renormalizing).
- **Severity leg:** raw dict in `market_phase._severity_reading` (≈`:197`) + `config.market_phase.weights` (macro legs show the pattern).
- **Research lab:** `compute_*` in `engine/research.py` + endpoint in `api/research.py` + page under `app/research/` — labs read stored `scanner_results`/`forward_returns` verbatim and reuse `walk_forward.min_sample`.
- **Certified edge:** cohort/control pair through `referee.certify_edge` via the `verify_claim.py` gate; NEVER call the referee ad hoc against real ledgers.
- **Macro series:** `config.macro.series` entry with `publication_lag_days` (+ revision policy per B-601).

### D3. Invariants the tests enforce (violate = pipeline fails)
No lookahead (`bars_asof` ≤ D read-side; > D forward-side) · no magic numbers (`test_no_magic_numbers` — config only) · immutable snapshots/ledgers (append-only) · single source of truth (list and detail rehydrate the same `record_json`; coherence auditor hard-fails recomputed contract values and non-canonical serving) · NA over fabrication · methodology catalog completeness.

### D4. Frozen goldens & pins (touch ONLY when a card sanctions it; regenerate from the new honest state, never hand-edit)
`tests/test_evidence.py::test_canonical_ledger_frozen_golden` (canonical ledger bytes) · `tests/test_staging_ledger_routing.py` (routing + row shapes) · `tests/test_seed_ingest.py` (seed window/count pins) · `tests/test_bar_cache.py` (offset-date pins) · methodology completeness assertions. The iter-18 basis swap is the worked example of a sanctioned cascade refresh.

### D5. Operational notes (hard-won; respect them)
- **The full pytest suite takes ~10 hours** on the 30y basis (test-only cost; the product boots fast). Never run it as the dispatcher/pump — the reviewer lane owns test verification. Write synthetic-fixture tests exclusively (B-904 guards this).
- Goal mode: headless `./scripts/automation/run-goal.sh --session-id mcp-loop`; interactive `/goal`, `/goal-status`, `/goal-step`, `/goal-pause`, `/goal-resume` inside Claude Code. Long-running subagents (>30 min) need the `.pump-alive` keepalive pattern in interactive mode.
- Demos: `demo.sh mcp-loop --session-live` (the Walkthrough acceptance depends on it).
- **One data-basis change per window** (seed swap, pool refresh, fundamentals ingest each own their window); run B-308 backups before any of them.
- The framework source lives in neutral `agents/`,`skills/`,… trees rendered into `.claude/` — never edit `.claude/` mirrors directly (framework work is out of scope for this backlog anyway).

### D6. The new-factor recipe (referenced by B-407/408/409/410/412, B-503/504/507)
1. Pure indicator function in `engine/indicators.py` (or a fundamentals transform reading ONLY `facts_asof`) — window/params as arguments from config; NA-graceful; fixture tests including a hand-computed value.
2. Config keys under `indicators.*` / `fundamentals.factors.*` — no literals anywhere.
3. Stored factor: compute in `score_stocks`'s stored-factors block at snapshot time; additive `record_json`/`ScannerResult` field; historical rows stay NA unless a sanctioned backfill card refreshes them.
4. Factor-lab entry in `config.research.factor_lab.factors` (typed column + component path) — the lab picks it up; deciles/rank-IC/MDD come free.
5. Methodology entry (formula, windows, economic rationale one-liner) — the completeness assertion fails the build without it.
6. Fixture tests: NA for short history; causality (value at D uses only data ≤ D); exclusion (NA names out of deciles, counted).
7. SEPARATELY (usually the next iteration): registry row (B-901) → Evidence Claim through the gate (staging; Appendix C) → badge resolves through the standard path.
8. NEVER add the factor to any score blend in the same breath — that path is: certified claim + owner decision + adaptive-arc shadow comparison (B-423).

---

*End of backlog. Maintain via the quarterly ritual (B-1202): update card statuses in place, append new registered cards per the replenishment protocol, and never rewrite recorded history — including the graveyard.*
