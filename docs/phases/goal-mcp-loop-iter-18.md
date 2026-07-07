# Goal Iteration 18 — The atomic 30-year basis swap + sanctioned ledger reset (J-10 / J-11 / J-12)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** mcp-loop
- **Iteration:** 18
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-10, J-11, J-12
- **Required-still-passing journeys:** J-01, J-03, J-04, J-05 (contract sense on the REGENERATED ledger — a visible status on every score, honest not-proven marking product-wide, the regime-labeled FAIL row, and a complete ledger audit; **byte-identity carry is NOT available this iteration** — every displayed number recomputed on the new basis, so these must be re-verified with FRESH pixels). J-02 is structurally un-exercisable this iteration (no "Proven" badge exists to drill), and J-06..J-09's retired-window edges legitimately do not survive re-certification — BOTH are governed by goal.md's data-basis-change provision (partial / not-a-regression), NOT by survival of a passing state. See the pre-registration in NOTES.
- **Anti-goal reminders:**
  - A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked values MUST render a "not yet proven" state. *(critical)*
  - **Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha claims; never place or simulate orders. *(critical)*
  - A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation for the same as-of date — not merely that the page renders. *(critical)*
  - **No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of; never introduce lookahead anywhere. *(critical)*
  - No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the post-decompose gate. *(critical)*
  - No hard-coded credentials, API keys, or tokens in source files. *(critical)*

## GOAL

Flip the product onto the staged 30-year / 548-pool price basis in one atomic iteration — deep, honestly-bounded price history surfaced (J-10), BOTH evidence ledgers regenerated from scratch on the new data so no retired edge survives (J-11), and the broadened point-in-time universe hardened with a recency/staleness gate (J-12).

## BACKGROUND

Iter-16 staged the 548-name 30-year equities span and iter-17 completed its index/macro context; the iter-17 evaluator (CONTINUE) mandated iter-18 FULL as "the ATOMIC basis swap + sanctioned ledger reset — the session's highest-stakes write, now dispatchable unattended." This iteration executes goal.md's ONE sanctioned reset of the otherwise append-only ledger ("Data-basis change (sanctioned ledger reset)"): every certified claim was measured on the retired 2021→2026 window and MUST NOT be displayed post-swap unless it independently re-certifies on the new basis.

**Depth is `full`** — the iteration crosses backend+frontend, changes the price basis / data model, resets both ledgers, and adds new tests beyond a browser smoke (all "Picking depth" full-triggers), and the prior depth was already full.

**Target selection (rubric):** no journey is `regressed` and the last coherence verdict was COHERENCE-PASS, so rules 1–2 do not apply. J-10/J-11/J-12 are the three journeys whose data/engine basis IS this swap — they are NOT three independent risky changes but ONE atomic data-basis change (goal.md: "the swap happens once over one complete seed"). You cannot flip the seed without regenerating the ledger (old edges are invalid — J-11), loading the broadened pool (else deep history is missing — J-10/J-12), or adding the staleness gate (else stale `rs_vs` misaligns — a correctness/anti-goal issue — J-12). A joint failure therefore has a SINGLE diagnosis ("the swap failed"), so rule 5 is respected. J-13 and J-14-surfacing are separable frontend follow-ons and are OUT OF SCOPE.

### RE-DISPATCH CONTEXT (read first — the heavy work is ALREADY in the working tree and disk-verified; this dispatch VERIFIES + COMPLETES, it does NOT redo)

This is a re-dispatch of iter-18. The prior attempt executed the entire swap and reached **REVIEW = FAIL**, where the failure is **process-only, not code** — the one un-satisfied item was running the full backend suite to real counts (a fix-mode pass was killed by the 2-hour inflight timeout mid-sweep; see NOTES). The following were **independently re-verified on disk by the decomposer this dispatch** (not taken from any handoff):

- **Swap complete & atomic:** `data/seed/prices/` = **590 CSVs**; `data/seed/meta.json` window pins **1996-01-01 → 2026-07-01**; `data/seed/macro/` + `universe_pool.csv` preserved; the staged `data/seed-stooq-30y/` tree is retired from disk (git shows a **move**, 591 `D` entries, not a copy). Live `config.provider` stays `seed`.
- **Both ledgers regenerated to an HONEST ALL-FAIL state (the load-bearing J-11 step) — decomposer byte-verified against the files this dispatch:** `certified-claims.jsonl` = 7 rows, **every `verdict.status == FAIL`**, **every `register_date == 2026-07-03`**, divisors **1..7 preserved** (verbatim historical selectors incl. the ma_stack FAIL re-test); `staging-ledger.jsonl` = 7 rows, **all FAIL** (LORD++ economy honestly starving). **Zero PASS rows in either ledger** ⇒ `proven_signals` is **empty** ⇒ every score/edge surface product-wide reads "Not yet proven"/FAIL. (Row 1 still carries its written `signal=leadership_score` selector, but because its verdict is FAIL it lights no badge — proven-ness flows ONLY from `status==PASS`.) Full verdict table in NOTES.
- **Shared certification engine untouched (the iter-9 regression proof):** `git diff --stat` on `app/engine/{referee,ledger,online_fdr,evidence}.py` and `app/mcp/tools.py` is **EMPTY** — only ledger *content* regenerated, never the modules.
- **Code seams landed & grep-confirmed:** pool-broadened `load_prices` (`price_load_symbols`), `resolve_candidate` staleness gate (`REASON_STALE = "stale_series"`, `universe.filters.max_staleness_days: 10`, gate order history → staleness → price → ADV), `/bars` windowing + `resolve_servable_symbol` (also adopted by watchlist add), `config.yaml` `walk_forward.history_years: 30`.
- **Browser-qa lane has NOT run yet:** no `reports/phase-goal-mcp-loop-iter-18-ui-test-results.md`, no evidence dir, no PNGs; `status.json` `browser_checks_run: false`. **This is the primary remaining verification.**

**Hard rules for this dispatch (violating any risks corrupting the completed basis or fork-locking the host):**
1. **Never relaunch the DB rebuild or any heavy backfill.** The DB is complete and consistent under the bounded cadence; `load_prices`/backfill are create-once no-ops on it, but `kind=rebuild` CLEARS the pool first — do not run it, and never run two heavy jobs concurrently on this host.
2. **Do NOT re-run `scripts/regenerate_ledgers.py`.** The sanctioned reset already executed once, honestly (seed 20240601 ⇒ a second run reproduces identical verdicts for zero information and non-zero risk). The ledgers as they stand ARE this iteration's referee certification.
3. Fix any defect found during verification **surgically**; **any frontend fix applied AFTER the browser-qa lane runs requires a browser-qa RE-RUN** (iter-13 lesson).

**Lessons applied (session ledger):** iter-9 — for the shared certification engine, an UNEDITED green default-path suite is the regression proof (verified git-diff-EMPTY above); iter-9b/10/12 — ledger routing was EXPLICIT (`ledger="canonical"`/`"staging"` per replay); iter-11/13/14/15 — browser evidence must be full-page or element-clip captures, md5-distinct, with the asserted element composed in frame, open the actual money frame (never trust a PASS label), and any post-browser-qa fix requires a re-run; iter-16 — no network fetches, `redact_stooq_key` choke point stays; iter-17 — on a re-dispatch the recorded `snapshot-sha` under-represents the diff (use `HEAD` + untracked — see NOTES).

## IN SCOPE

Items marked `[x]` are DONE and disk-verified — **do not redo them**. Items marked `[ ]` are the remaining work of this dispatch.

### Backend

- [x] **Pre-flight basis-validation** — `tests/test_seed_staged_30y.py` retargeted to `data/seed/` post-swap. *(verify green in the full sweep)*
- [x] **A. Atomic seed swap** — 590 CSVs into `data/seed/prices/` via move; `meta.json` regenerated with per-series vendors + proxy disclaimer + honest SATS absence; macro/pool preserved byte-identical; staged dir retired; nothing reads `seed-stooq-30y/` at runtime (`config.provider: seed` unchanged).
- [x] **B. Pool-broadened price load** — `price_load_symbols` = pool ∪ context; DB rebuilt ONCE (587 symbols / ~3.27M bars). *(verify via `tests/test_seed_loader_pool.py`)*
- [x] **C. Recency/staleness gate (J-12)** — `REASON_STALE`/`stale_series`; `universe.filters.max_staleness_days: 10`; fixed gate order history → staleness → price → ADV; new `asof` param threaded to its call site + test call sites; surfaced on `/methodology` + `/data` diagnostics + membership-timeline counts; closes the `rs_vs` positional misalignment for names whose data ends mid-history. *(verify via `tests/test_universe_resolver.py` staleness suite)*
- [x] **D. Bounded snapshot backfill** — completed under the disclosed bounded cadence (~410 immutable runs 2005-02-25 → 2026-07-01; monthly deep + daily recent + quarterly walk-forward + bootstraps incl. GFC 2008-11 and COVID 2020-03; dot-com predates the SPY calendar floor — honestly not snapshot-able). **Do NOT relaunch or densify this dispatch.**
- [x] **E. Sanctioned ledger reset + regeneration (J-11)** — BOTH ledgers regenerated exclusively via `verify_edge` with explicit ledger routing; ALL FAIL, `register_date` 2026-07-03, divisors 1..7 preserved, `proven_signals` empty, zero hand-authored rows; honest-stop honored (zero retries, zero selector edits). **Do NOT re-run.**
- [x] **F. Depth actually used** — `walk_forward.history_years: 30` (window honestly floored at SPY's first committed bar 2005-02-25); `SURVIVORSHIP_BIAS_LABEL` names the ~30-year span with upper-bound framing.
- [x] **G. Bars endpoint windowing (J-10 performance)** — bounded default trailing window (`chart_bars.default_years`), explicit `range=full` opt-in, weekly SAMPLING of real stored bars beyond a threshold (real bars only, never synthesized; MA computed from the FULL daily series); additive payload keys; unknown `range` ⇒ 422; broadened ticker validation via `resolve_servable_symbol`; no-lookahead boundary untouched.
- [ ] **H. Run the FULL backend suite to REAL counts (review-CRITICAL; closes iter-17 audit gap B1).** The test files are already refreshed (frozen goldens `test_evidence.py` + `test_staging_ledger_routing.py` to the all-FAIL / 2026-07-03 / `proven_signals == {}` state; `test_seed_staged_30y.py` retargeted; `test_bars.py`/`test_bar_cache.py`/`test_data_manager*.py` refreshed; new `test_bars_windowing.py` + `test_seed_loader_pool.py`). What is OUTSTANDING is the *run*: execute the ENTIRE backend suite **sequentially and alone**, **record REAL pass/fail/skip counts + wall-clock time in the handoff**, and fix any residual retired-window pin the sweep exposes. **DO-NOT-EDIT** (an edit = a regression signal, not a fix): `test_referee.py`, `test_online_fdr.py`, `test_forward_walk.py`. **Runtime caveat (see NOTES escalation — load-bearing):** the deep-basis `loaded_engine` session fixture makes the full suite very slow (multi-hour; a prior run was killed by the 2-hour inflight timeout). Run it in the background with a keepalive, or chunk by test module, so real counts are actually recorded — and do NOT kill a buffered-but-progressing run mistaking it for hung.

### Frontend

- [x] **Stock Detail chart range control** (Recent ↔ Full history, server-side `range` param only, honest first-available-date + downsampling caption). *(verify in the browser lane)*
- [x] **Retired-value MIRROR fixtures/comments** in `apps/frontend/lib/evidence.test.ts` + `factor-lab-evidence.test.ts` repinned to explicitly-synthetic post-reset shapes; frontend suite + `tsc --noEmit` green. *(no further edit needed — just stop listing it as an open Known-Issue in the handoff)*
- [ ] **Verify a broadened-pool member renders honestly** — a name outside the legacy ~122 set shows a leaderboard row + detail page with honest reference data (no crash, no fabricated metadata). Confirm in the browser lane.

### New user-facing capability
Deep price history: a long-tenured name's chart/backtest window reaches back toward 1996 (or the name's real first bar); a post-IPO name honestly shows only its short real history; the evidence ledger shows only claims re-judged on the 30-year basis (this run: all honestly FAILED — every badge product-wide reads "Not yet proven"); the leaderboard reflects the broadened point-in-time universe.

### New information displayed
Deeper chart/backtest spans (same `daily_prices` value, deeper content); the regenerated `/evidence` rows (same evidence-status value, regenerated content, register dates 2026-07-03, honest FAIL verdicts); broadened membership counts on `/stocks` + the membership timeline; the ~30-year survivorship disclosure text; the new `stale_series` exclusion reason in the methodology/data diagnostics.

### New user actions
Chart range control (bounded default ↔ full-history opt-in) on Stock Detail.

### UI surface changes
`/stocks/{ticker}` chart range control + depth caption; `/evidence` content regenerated (rows/values/dates change; structure unchanged); `/backtest` as-of window deepens; `/methodology` + `/data` gain the staleness reason. **No new pages.**

### Product surface delta
The product stops being a ~5-year / ~122-name scanner and becomes a ~30-year / 548-pool point-in-time platform whose every "Proven" chip must be re-earned on the deep basis. This run, none re-certified — the deep multi-regime holdout (GFC, COVID, 2021-26) exposed the retired-window edges as non-reproducing, so the product now shows an honestly dark evidence layer: statuses everywhere, confident numbers nowhere. That IS the product working (goal.md Success Criteria: "Failed or unvalidated signals are explicitly flagged").

### Blueprint conformance
No new surfaces, no nav-skeleton change. J-10 lives at its registered homes (`/stocks/{ticker}` chart + `/backtest`), J-11 at `/evidence`, J-12 at `/methodology` + `/stocks` — all already in the blueprint homes table. The additive **iter-18 clarification paragraph is ALREADY present in `blueprint.md`** (written at first dispatch; decomposer-re-verified current this dispatch — it promises "same modules, same endpoints, content regenerated, no new displayed value," which the git-diff-EMPTY shared-engine check independently confirms). **No blueprint edit and no reapproval requested this dispatch** (no new displayed value to register, no nav-skeleton change).

### Data-contract additions
**None** — no new displayed value. Deep bars are the SAME `daily_prices` value (same module, same `GET /api/stocks/{ticker}/bars` endpoint — `range`/downsample are presentation params on that endpoint, never a second endpoint, never a client-side recompute); evidence status stays the SAME single-source value (`certify_edge` → `certified-claims.jsonl` → `GET /api/evidence`) with REGENERATED content; membership stays `resolve_members`/`resolve_candidate` (same module + serving path) with one added exclusion reason. Never introduce a second computation or endpoint for any of these. (The J-14 per-series vendor label in `meta.json` stays UNDISPLAYED and unregistered until the post-swap iteration that first surfaces it.)

## OUT OF SCOPE

- **J-13** (Data Manager 548-pool Fetch default, "Expand universe" removal, availability-legend clarification) — next iteration per goal.md sequencing. This iteration's `/data` change is limited to the staleness diagnostic surface — do not extend it.
- **J-14 steps 2–3** (rendering the deep `_SPX`/`_NDX`/`_DJI`/`_VIX` overlays + vendor labels on Dashboard/`/data`) — the swap carries their bars in the committed seed but does NOT wire them into `daily_prices`/charts; surfacing is its own iteration (which also registers the vendor-label Data Contract value).
- Any NEW evidence hypothesis, cohort, selector, or promotion beyond the already-executed verbatim replay + the two pre-registered explorers. No ad-hoc data-mined cohorts (anti-goal #4). Proposing a new-basis claim through the pre-build gate is iter-19+ work.
- Any network fetch (Stooq per-symbol endpoint remains IP-blocked; the basis is complete — goal.md §A says do NOT re-fetch).
- Re-densifying the snapshot pool beyond the disclosed bounded cadence (documented follow-on, NOT this dispatch).
- Market-cap refresh / `universe.json` regeneration, survivorship-free delisted-names feed, quantile spreads / regime-conditioned scan families (goal.md deferrals).
- Rewriting engine scoring/regime/research computation. **Re-doing any completed heavy step (swap, DB rebuild, ledger regen, backfill).**

## DEFINITION OF DONE

- [ ] Swap verified complete and atomic: 590-file 30y basis in `data/seed/` (window pins 1996-01-01 → 2026-07-01), macro/pool byte-preserved, `meta.json` vendor-complete, no duplicated staged tree, nothing reads `seed-stooq-30y/` at runtime *(re-verified this dispatch — keep true)*
- [ ] DB state verified (NOT rebuilt): 587 symbols / ~3.27M bars; ~410-run snapshot pool 2005-02-25 → 2026-07-01 under the config-disclosed cadence; boot + warm-up reach Ready
- [ ] BOTH ledgers verified as regenerated exclusively via `verify_edge` per the replay policy (7 canonical + 7 staging rows, all `verdict.status == FAIL`, `register_date` 2026-07-03, divisors 1..7 preserved, honest-stop honored, zero hand-authored rows, `proven_signals` empty) *(re-verified this dispatch — keep true)*
- [ ] **FULL backend suite run sequentially + alone with REAL pass/fail/skip counts + wall-clock recorded in the handoff (review-CRITICAL; retires iter-17 audit gap B1);** any residual retired-window pin it exposes is fixed; frontend suite + `tsc --noEmit` green
- [ ] Basis-independent suites (`test_referee.py`, `test_online_fdr.py`, `test_forward_walk.py`) UNEDITED and green; frozen-golden/pin suites refreshed and green; new gate/windowing/pool-loader tests green
- [ ] Target journeys J-10, J-11, J-12 pass via the canonical browser-qa-agent lane (fresh full-page or element-clip, md5-distinct captures with the asserted element composed in frame)
- [ ] J-11 verified in browser: NO retired edge value (+21.34% / +8.91% / +6.36% / +6.12% / +4.69% / +3.33% / p=0.0004998 / register 2026-06-30 or 07-01) rendered anywhere; every displayed edge/p/control/date byte-matches the regenerated ledger; non-reproducing claims read honest FAIL rows / "Not yet proven" badges
- [ ] Required-still-passing J-01, J-03, J-04, J-05 re-verified with FRESH pixels against the regenerated ledger (byte-identity carry is NOT available — everything recomputed); J-02 and J-06..J-09 judged per the data-basis pre-registration in NOTES (honest badges + correct numbers; partial / not-regression)
- [ ] No anti-goal violation — trivially checkable now: ZERO "Proven" chips may render anywhere; no buy/sell/price-target language; determinism seed 20240601 + no-lookahead preserved; no credentials
- [ ] Dev handoff updated at `docs/handoffs/goal-mcp-loop-iter-18-dev.md`: append a dispatch-2 section documenting the full-suite counts + wall-clock and the browser outcomes; DROP the resolved frontend-fixture Known-Issue bullet so the next agent does not re-do finished work

## TESTING REQUIREMENTS

- **Browser (canonical browser-qa-agent lane; backend up and STAYING up — iter-13 lesson; boot is fast, warm-up is a no-op sweep). This lane has NOT run yet (`browser_checks_run: false`, no evidence artifacts) — it is the primary remaining verification:**
  - **J-10:** `/stocks/AAPL` (or MSFT) — default chart bounded (~5y trailing) with the caption disclosing first available date **1996-01-02**; "Full history" opt-in renders the deep span (weekly-downsampled beyond the threshold, real bars only); **NVDA first bar 1999-01-22** (real IPO, no invented earlier dates); one post-IPO name (**ARM 2023-09-14 / COIN 2021-04-14 / HOOD 2021-07-29**) honestly short; `/stocks` + `/evidence` stay responsive. `/backtest` window deepened, honestly floored at **2005-02-25** (SPY's real first committed bar — a disclosed floor, NOT a defect).
  - **J-11:** `/evidence` renders ONLY regenerated rows — 7 rows, every register date **2026-07-03**, every verdict an honest **FAIL** with its real p/edge (spot-check ≥1 row byte-for-byte against `certified-claims.jsonl`); factor-lab / combination-lab / stock-detail surfaces read "Not yet proven" everywhere; **ZERO "Proven" text and ZERO retired values anywhere in the app.**
  - **J-12:** `/methodology` membership timeline shows entries/exits across the deep history; membership count reflects `resolve_members(D)` over the broadened pool; a mid-history-IPO name is absent before `min_history_bars` and present after; the `stale_series` exclusion reason + threshold surfaced.
  - **J-01/J-03/J-04/J-05 regression (contract sense, FRESH pixels):** `/stocks` — every row's three scores each carry a visible status (all "Not yet proven" IS a PASSING state for J-01); J-03 — honest marking product-wide (now trivially strong) incl. FAIL rows on `/evidence`; J-04 — the Breakout-watch row still carries its "Regime: Risk-on" label with an honest FAIL verdict; J-05 — 7 rows render hypothesis / OOS verdict / control / date / linkbacks end-to-end. J-02 — verify the drill AFFORDANCE renders its honest not-proven state (the Proven-drill itself is structurally un-exercisable — see NOTES).
  - **Screenshot hygiene (iter-3/11/13/14/15 lessons):** full-page or element-clip captures, md5-distinct, asserted element in frame — a relabeled or blank frame is a verification gap, not evidence.
- **Unit/integration (verify green):** staleness gate suite (boundary + new `stale_series` reason + `rs_vs` misalignment closed), pool-broadened loader, bars windowing/downsample + broadened-symbol validation (422 on unknown `range`; 404 only for truly unknown tickers), refreshed frozen goldens (regenerated all-FAIL values exactly; `proven_signals == {}`), seed-integrity on the new basis (window pins, NVDA/AAPL split continuity, no pre-1996 leakage, proxies byte-coherent with `data/seed/macro/`).
- **Full suite:** entire backend suite, sequential/alone/bounded, REAL counts in the handoff (the review-CRITICAL blocker); frontend suite green.
- **Error cases:** unknown ticker → 404 (never a fabricated row); invalid `as_of`/`range` params → 4xx/422; FAIL claims rendered honestly (already the live state — assert, do not retry them).

## NOTES

**Evidence-claim gate status:** this spec deliberately carries NO machine-readable `## Evidence Claim` block, so the post-decompose gate passes through. Pre-build certification was impossible-by-construction (the gate would have run against the OLD basis). goal.md's "Data-basis change (sanctioned ledger reset)" is the governing mechanism — the already-executed in-iteration replay through `verify_edge` on the rebuilt DB IS the referee certification. Anti-goals #1/#6 are upheld by the regenerated ledger itself: post-swap, "Proven" may render only where a FRESH referee PASS row exists — and none does.

**Canonical replay — policy AND executed outcome (register_date 2026-07-03; honest-stop honored: zero retries, zero selector edits, zero reorders). Decomposer byte-verified against `certified-claims.jsonl` this dispatch:**

| # | Claim (verbatim historical selectors) | Historical | Regenerated | p | required_p (divisor) | holdout edge |
|---|---|---|---|---|---|---|
| 1 | factor:leadership_score D10 h20 (signal=leadership_score) | PASS | **FAIL** | 0.5352 | 0.05 (÷1) | −0.03% |
| 2 | event-study:Breakout-watch × Risk-on h20 | PASS | **FAIL** | 0.9460 | 0.025 (÷2) | −0.68% |
| 3 | factor:ma_stack D10 h20 | FAIL | **FAIL** | 0.2769 | 0.0167 (÷3) | +0.21% |
| 4 | factor:vcp_contraction D10 h20 | PASS | **FAIL** | 0.9595 | 0.0125 (÷4) | −0.38% |
| 5 | factor:vcp_contraction D10 h60 | PASS | **FAIL** | 0.9995 | 0.01 (÷5) | −1.64% |
| 6 | combination:rs_spy_3m×high_proximity h20 | PASS | **FAIL** | 0.4943 | 0.0083 (÷6) | +0.01% |
| 7 | factor:rs_spy_3m D10 h60 | PASS | **FAIL** | 0.9045 | 0.0071 (÷7) | −1.42% |

Replaying the FULL family in order (including the ma_stack FAIL) preserved each claim's historical Bonferroni divisor (1..7) — the reset never functioned as bar-laundering. Staging: all 7 pre-registered explorer candidates FAIL under LORD++ (the economy honestly starving; several claims flipped positive-in-sample → negative-out-of-sample — the overfit signature the deep multi-regime holdout was expected to expose). The retired +21.34% OOS≫in-sample yellow flag (J-09, carried since iter-15) resolved exactly as pre-registered: a retired-window artifact that does not reproduce.

**Pre-registration for the iter-18 evaluator (grounded in the executed, disk-verified outcome):**
1. **All-FAIL is a legitimate, honest terminal state for this iteration — NOT a failure and NOT a regression.** goal.md: "J-01..J-09 remain valid contracts (honest badges, correct numbers) but their specific certified edges recompute." J-11's step-2 phrase "every row is one the referee re-passed" must be read via its acceptance bullets: rows come ONLY from the regenerated ledger, a non-reproducing edge reads "Not yet proven"/FAIL, and no retired value renders. A ledger of 7 honest FAILs satisfies that contract (the honest-stop guard forbids forcing a PASS).
2. **J-01/J-03/J-04/J-05 remain fully exercisable** in the honest-dark state: a status on every score (all "Not yet proven"), honest FAIL rows with regime labels and linkbacks, a complete ledger audit. Judge on FRESH pixels against the regenerated ledger — the byte-identity carry channel is NOT available this iteration.
3. **J-02 is structurally un-exercisable** (no "Proven" badge exists to drill — the iter-1 empty-ledger analogue). Score it per the data-basis provision (partial / not-a-regression), verify its affordance renders the honest not-proven state, and note that iter-19 may propose a new-basis claim through the normal pre-build gate from the pre-registered candidate sets (goal.md forbids ad-hoc cohorts; each canonical submission would tighten the divisor 8→9→…).
4. **J-06..J-09:** badges honestly dark, numbers byte-matching the regenerated FAIL rows = the provision working. Do NOT score passing→failing REGRESSION on edge non-survival.
5. **Expected honest deltas:** register dates 2026-07-03; cohort/control n's, block lengths, every edge/p changed; `/stocks` row count reflects the broadened membership; `/backtest` floor 2005-02-25. Correctness = byte-match against the REGENERATED ledger/engine, never a remembered value.

**Diff base for the coherence-auditor / evaluator (iter-17 lesson, recurring):** ALL of iter-18's PRODUCT work is uncommitted (`M`/`D`/`??` in `git status`), so **diff against current `HEAD` + untracked files** to capture the whole iteration (`git diff HEAD -- apps/ config.yaml runs/goal-session-mcp-loop/state/*.jsonl` plus the untracked list). Do **NOT** use the recorded `runs/goal-session-mcp-loop/iter-18/snapshot-sha` as the diff base: it is a mid-flight stash-merge WIP captured at re-dispatch that already contains attempt-1's work, so diffing against it hides the iteration.

**Escalation flags:**
- The heavy offline work is DONE — this dispatch must not repeat it. The one unacceptable end-state now is shipping with any retired value rendering, or corrupting the completed basis/ledgers by re-running the heavy steps.
- **Full-suite completion risk (review-CRITICAL blocker).** The mandatory full backend sweep was already killed once by the 2-hour inflight timeout mid-suite — the deep-basis session `loaded_engine` fixture makes the full suite multi-hour. This is a TEST-fixture characteristic, NOT a product problem (the product boots fast). Give this run adequate wall-clock budget (background run + `.pump-alive` keepalive per the session's known long-subagent pattern, or chunk by test module) so REAL counts are actually recorded; do NOT run it concurrently with anything else on this host, and do NOT kill a buffered-but-progressing run mistaking it for hung.
- If verification uncovers a material defect in the completed work (wrong numbers, a broken surface, a fabricated bar), fix surgically and re-verify; if the defect invalidates the swap itself, STOP and report precisely — do not half-revert.
- Scope-creep watch: do not drift into J-13 (`/data` beyond the staleness diagnostic) or J-14 surfacing while near the seed metadata. Demo lane: the demo-narrator should flag the deep-history chart + regenerated-ledger walkthroughs `[NEW]` (J-10/J-11 acceptance; non-gating).
