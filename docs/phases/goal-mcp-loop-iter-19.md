# Goal Iteration 19 — Fix the /stocks Sector-sort crash + the /api/data prefill OOM, then complete the browser-QA verification

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** mcp-loop
- **Iteration:** 19
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-01, J-12
- **Required-still-passing journeys:** J-03, J-04, J-05, J-10, J-11
- **Evidence Claim:** none (no new "Proven" claim is surfaced — the post-decompose gate passes automatically; goal.md loop rule)
- **Runs only after:** human `--acknowledge-regression` (prior verdict was REGRESSION — the loop halted for human review)
- **Anti-goal reminders (verbatim from docs/goal.md):**
  - A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked values MUST render a "not yet proven" state. *(critical)*
  - **Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha claims; never place or simulate orders. *(critical)*
  - A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation for the same as-of date — not merely that the page renders. *(critical)*
  - **No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of; never introduce lookahead anywhere. *(critical)*
  - No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the post-decompose gate. *(critical)*
  - No hard-coded credentials, API keys, or tokens in source files. *(critical)*
  - **Resilience to data-shape and data-scale change:** widening the data basis (new nulls, broader pools, deeper history) must never crash an existing page or exhaust a service's memory — every existing consumer of a widened field is re-validated, the UI degrades gracefully (contained error boundary, honest "—"/NA placeholder, never a blank application-error page), and unbounded whole-table ORM loads are forbidden on the deep basis. *(critical)*

## GOAL

Restore the `/stocks` leaderboard (the product's headline page) so sorting/filtering by "Sector" on the broadened 30-year universe no longer crashes the whole app, fix the `/api/data` bar-prefill OOM that hangs the backend under load, then run the canonical browser-QA lane to completion so J-01 returns to passing and J-12 is cleanly verified.

## BACKGROUND

Iter-18's sanctioned 30-year / 548-pool basis swap landed correctly, but it also shipped one unsanctioned REGRESSION and one operator-diagnosed stability defect, both rooted in the widened data basis:

1. **J-01 crash (the verdict driver).** The broadened pool makes `scoring.py:377` `cfg.stock_sectors.get(ticker)` return `null` for ~78% of rows (names with no mapped GICS sector). That null flows into the unguarded `/stocks` sort comparator (`app/stocks/page.tsx:93` `a.sector.localeCompare(b.sector)`), which throws an uncaught `TypeError` the moment a user clicks the "Sector" column — and with no `error.tsx`/`global-error.tsx`, the entire page (nav included) collapses to a blank "Application error." `git diff` on the component is empty and `tsc` stayed green (because `api.ts:279` typed `sector: string`), so both the "empty diff = no regression" heuristic and the type-checker gave false comfort (iter-18 lesson). This is a prior-passing interaction (live since iter-2), hence a REGRESSION — the rubric's rule 1 top priority.

2. **Backend OOM (operator addendum, blocking).** The canonical browser-QA lane did not merely "crash at exit 70" — the dev backend OOM'd and hung on its first `/api/data` visit: `prices.py:82-84` `prefill()` materializes all 3,270,066 `daily_prices` rows as hydrated ORM objects (~6.8 GB peak) against the 6144 MB `ulimit -v` cap, and ≥6 concurrent `/api/data` probes ran that prefill simultaneously (the `compute_coverage` single-flight did not serialize them). **The prefill fix MUST ship alongside the sector-null fix** — the browser-QA lane cannot complete (and thus cannot verify the sector fix or J-12) unless the backend survives `/api/data`. goal.md's "fast platform" sequencing names exactly this: "(1) the iter-19 regression pass = sector-null crash fix + item A (unblocks browser-QA)."

Depth is **full** (mandatory): prior verdict was REGRESSION (the iter-18 evaluator explicitly recommends FULL for iter-19), and this iteration changes a backend data-load path plus adds crash containment — it needs the full 11-step pipeline, specifically the auditor + ux-regression-reviewer + phase-closure-auditor gates that CAUGHT the iter-18 regression while `status.json`/`qa.md` falsely reported "zero blockers / ready to ship."

The sector-null fix and the OOM fix are ONE causally-coupled change-set (not two independent risky journeys — rubric rule 5): the OOM fix is a prerequisite for verifying the sector fix, and it is guarded by `test_bar_cache.py`'s byte-identical snapshot tests. J-12 is **verification-only** — its capability (broadened universe + `resolve_candidate` staleness gate + `/methodology` timeline) already landed and was unit-verified in iter-18; it is `partial` solely because the crashed lane never captured its browser assertions. So the risk is concentrated in one diagnosable, revertible change-set.

## IN SCOPE

### Backend
- [ ] **Bound the bar prefill OOM (goal.md fast-platform §A — blocking).** Rewrite `apps/backend/app/engine/prices.py:82-84` `prefill()`: replace `select(DailyPrice).order_by(symbol, date).all()` (3.27M hydrated ORM rows in one shot) with a **streamed, column-projected** load — `select(DailyPrice.symbol, DailyPrice.date, DailyPrice.open, DailyPrice.high, DailyPrice.low, DailyPrice.close, DailyPrice.volume).order_by(DailyPrice.symbol, DailyPrice.date)` iterated with `.yield_per(batch)` (idiom: `forward_testing.py:367-378` `_streamed_existing_keys`), building lightweight records — a module-level `NamedTuple`/`__slots__` class `Bar` with **exactly** the attribute names consumers read (`.date/.open/.high/.low/.close/.volume`). Apply the same record type to the lazy per-symbol path at `prices.py:115`.
- [ ] **No inline literals:** batch size from config (`research.read_batch_size`, currently 2000, or a new `data_manager.prefill_batch_size`).
- [ ] **Preserve byte-identity (the correctness gate):** keep `ORDER BY symbol, date` and the `expected_symbols` semantics so `tests/test_bar_cache.py`'s snapshot tests stay green; any new param threaded through `prefilled_bar_cache → prefill` MUST be **OPTIONAL** (the monkeypatch shims at `test_bar_cache.py:91` and `:256` and the 2-arg call at `:102` depend on the current signature).
- [ ] **Serialize cold-key coverage computes.** Verify/fix the `compute_coverage` single-flight (`apps/backend/app/engine/data_manager.py:611-745`, `_compute_coverage_uncached` at `:758`) so only ONE cold prefill runs at a time — the OOM log proved ≥6 concurrent `/api/data` prefills got through (either the lock scope excludes `_compute_coverage_uncached`'s prefill or probes bypass it). Enforce one cold compute at a time.
- [ ] **Fix the stale comment.** `config.yaml` `server.memory_cap_mb` comment ("~1.3M-row" → the real 3.27M figure); keep the 6144 MB cap as the OOM guard.
- [ ] **(Growth leeway — design in now, cheap; optional per §A):** give `prefill` two optional bounds `symbols=` and `min_date=`, both defaulting to today's behavior (load-everything), so the cache can scale sub-linearly with future pool growth.
- [ ] **Record the measurement.** Add the item-A before/after numbers to `reports/perf-budgets.md`: the cold `/api/data` path completes ≤ 60 s **without OOM** under the 6144 MB cap; retained footprint drops from ~3+ GB ORM to ~0.4–0.5 GB.
- [ ] **Sector field stays null (do NOT change the backend).** `scoring.py:377`'s `null` for unmapped names is the honest absence, not a bug — never fabricate a GICS sector. The fix is downstream (type + guard + honest "Unassigned" label).

### Frontend
- [ ] **Guard the sector sort comparator.** `apps/frontend/app/stocks/page.tsx:93` → `(a.sector ?? "").localeCompare(b.sector ?? "")` (null sorts deterministically together, never throws).
- [ ] **Fix the sector filter vocabulary.** `apps/frontend/app/stocks/page.tsx:354-358` — map `null` to an explicit **"Unassigned"** bucket (never a literal `null`/empty option); filtering by "Unassigned" selects the null-sector rows.
- [ ] **Correct the contract type.** `apps/frontend/lib/api.ts:279` `sector: string` → `sector: string | null`, then re-validate EVERY consumer of `row.sector` (sort/filter/format/display/`.localeCompare`) that `tsc` now flags (iter-18 lesson — the widened field must be re-checked at every call site even where the file's git diff is empty).
- [ ] **Add crash containment.** New `apps/frontend/app/error.tsx` AND `apps/frontend/app/global-error.tsx` so any future uncaught client exception degrades to a contained error card with the nav preserved — never a blank application-error page (anti-goal #8).
- [ ] **(Non-blocking carry — F1):** confirm whether the Full-history chart plots pre-2018 weekly bars for >8y names (e.g. `/stocks/NVDA`) and widen the x-domain to `first_available_date` if not.

### New user-facing capability
No net-new capability — this RESTORES a broken one and hardens the app. The user can again sort and filter the `/stocks` leaderboard by "Sector" (with an honest "Unassigned" bucket for unmapped pool names) without crashing, and any future client error shows a contained card instead of wiping the whole app.

### New information displayed
An honest **"Unassigned"** sector label (replacing what would render as a null option) for pool names with no mapped GICS sector. No new computed value.

### New user actions
None new (restores the existing Sector sort control + Sector filter dropdown).

### UI surface changes
`/stocks` leaderboard (crash-fixed sort + filter); a contained error card (`error.tsx`/`global-error.tsx`) that replaces the blank "Application error" page. No new pages, no nav changes.

### Product surface delta
The product stops crashing on the deep basis: `/stocks` survives Sector-sort with ~78% null sectors, the backend survives `/api/data` cold-path prefills without OOM/hang, and uncaught client errors degrade gracefully. This is the anti-goal-#8 "resilience to data-shape and data-scale change" contract made real and verified end-to-end.

### Blueprint conformance
No new surfaces. J-01's fix lives on `/stocks` (its registered home). `error.tsx`/`global-error.tsx` are route-level Next.js error infrastructure, not nav surfaces. J-12's verification exercises `/methodology` (its registered home) + `/stocks` membership counts + the `/data` `stale_series` card — all existing homes. The OOM fix is backend-internal (no new endpoint). An additive **iter-19 clarification paragraph** is appended to `runs/goal-session-mcp-loop/state/blueprint.md` documenting all of the above; it makes no nav-skeleton change and registers no new value, so no re-approval is requested.

### Data-contract additions
**None.** The OOM fix re-serves **byte-identical** bars from the SAME `daily_prices` value via the SAME endpoints — the lightweight `Bar` record is an internal load representation gated by `test_bar_cache.py`'s snapshot tests; it computes and serves nothing new (goal.md §A: "a projection or cache re-serves stored values, never recomputes"). The `sector` field is already part of the registered `GET /api/stocks` scores value (`scoring:score_stocks`); iter-19 only corrects its TS type to reflect its real nullability and adds an honest "Unassigned" display label — no new computing module, no new endpoint, no new displayed value.

## OUT OF SCOPE

- **No new "Proven" edge / no Evidence Claim / no ledger writes.** Both ledgers stay all-FAIL from the iter-18 sanctioned reset. J-02 and J-06/J-07/J-08/J-09 remain `partial` **by design** — re-certifying edges on the 30-year basis is separate, later evidence work (goal.md data-basis provision; iter-17 lesson). The evaluator must NOT read these partials as regressions.
- **No new features, pages, or nav sections.**
- **Fast-platform items B–K are deferred.** iter-19 lands **item A only** (the OOM), per goal.md's sequencing. Do NOT refactor the other `.all()` sites in `prices.py` — `:115` is in scope only to adopt the `Bar` record type; `:253/:292/:312` are per-symbol-bounded — leave them.
- **J-13** (Data Manager 548 legend) and **J-14** (deep index/macro display) — sequenced later; still `unknown`, not this iteration.
- **J-15/J-16 as passing journeys** — iter-19 lands item A and records its measurement, but does NOT claim the full perf-budget contracts (those need the measurement harness + budgets table across every endpoint + items B–K).
- **Do NOT fabricate a GICS sector** for unmapped pool names — null renders as honest "Unassigned", never an invented sector.

## DEFINITION OF DONE

- [ ] **J-01 passes via browser-qa-agent:** `/stocks` Sector-sort (ascending AND descending) on the default ~78%-null-sector state completes with **no crash and the sidebar nav intact**; the Sector FILTER dropdown shows "Unassigned" (not a null option) and filtering by it works; every leaderboard row still shows an evidence status. UT-21 re-verified with a fresh, correctly-labeled, md5-distinct screenshot of the sorted leaderboard.
- [ ] **J-12 passes via browser-qa-agent:** the `/methodology` membership timeline shows entries/exits across the deep history; a mid-history-IPO name is absent-before / present-after its `min_history_bars` accrual; the `/data` `stale_series` reason card renders in frame (target scrolled into view or full-page capture — iter-14 lesson).
- [ ] **Backend survives the FULL canonical browser-qa lane** (including `/api/data`) with no OOM/hang; the cold `/api/data` path completes under the 6144 MB `server.memory_cap_mb` cap; the item-A before/after measurement is recorded in `reports/perf-budgets.md`.
- [ ] **Crash containment verified:** `error.tsx` + `global-error.tsx` exist and contain an uncaught client error to a card with nav preserved (not a blank app).
- [ ] **Required-still-passing journeys J-03, J-04, J-05, J-10, J-11 remain green** — in particular J-10's `/stocks/{ticker}` chart renders **byte-identical bars** after the prefill rewrite (`test_bar_cache.py` snapshot tests green).
- [ ] **No anti-goal violation** — especially #8 (no crash / no OOM on the widened basis; graceful degradation), #1 (still zero "Proven" chips; both ledgers all-FAIL; `proven_signals={}`), #2 (no buy/sell/price-target/return-promise/alpha language — the UT-29 sweep completes product-wide), #3 (displayed bars/numbers byte-identical), #5 (determinism / no-lookahead preserved).
- [ ] **Unit/integration tests pass; no regressions** — `test_bar_cache.py` byte-identical snapshot tests green; the optional new prefill param leaves the monkeypatch shims (`:91`, `:256`) and 2-arg call (`:102`) working.
- [ ] **`status.json` + `goal-mcp-loop-iter-19-qa.md` reconciled** against the ACTUAL completed evidence set (no "zero blockers" claim that contradicts a `-fail-`-named frame); the **auditor re-runs** and explicitly reads + reconciles the ux-regression-reviewer and phase-closure-auditor verdicts.
- [ ] Dev handoff written at `docs/handoffs/goal-mcp-loop-iter-19-dev.md`.

## TESTING REQUIREMENTS

- **Browser (canonical `browser-qa-agent` lane — run to COMPLETION; the iter-18 lane crashed at exit 70 with tasks #18–22 pending):**
  - **J-01:** `/stocks` Sector-sort asc + desc on the default (~78% null-sector) state → no crash, nav intact, sorted rows render; Sector filter dropdown shows "Unassigned" and filtering works.
  - **J-12:** `/methodology` membership timeline entries/exits; a mid-history-IPO name absent-before/present-after; the `/data` `stale_series` reason card in frame.
  - **Regression smoke:** J-03 (evidence badges on `/stocks`), J-04 + J-05 (`/evidence` rows + regime label), J-10 (`/stocks/{ticker}` Full-history chart renders byte-identical bars), J-11 (`/evidence` all-FAIL, no stale edge value anywhere).
  - **Deferred iter-18 checks:** Watchlist negative paths (unknown-ticker 404, duplicate 409); Backtest 2005-02-25 as-of floor.
  - **HIGHEST PRIORITY (goal.md-critical):** the full four-quadrant P1 anti-goal-#2 **language sweep (UT-29)** — only ~25% executed in iter-18; complete it product-wide (no return-promise / price-target / buy-sell / alpha language anywhere).
  - **Screenshot hygiene (recurring iter-3/11/13/14 lesson):** scroll each asserted element into frame OR use full-page / element-clip capture (a scrolled-viewport capture returns a blank ~5855-byte frame); `md5sum` the PNGs to confirm they are DISTINCT and correctly labeled; open the ACTUAL asserted frame (never trust a PASS label, a DOM-text line, or a reused frame); keep BOTH services up for the whole run and confirm the frontend reaches the backend (no "Backend unavailable" pill). If a verification artifact is missing, read `engine.log` for where the pipeline died before scoring.
- **Unit / integration:**
  - `tests/test_bar_cache.py` byte-identical snapshot tests MUST stay green (the prefill rewrite's correctness gate); the optional new param must not break the monkeypatch shims or the 2-arg call.
  - A targeted test asserting the streamed, column-projected prefill returns the SAME rows/order as the prior whole-table load for a sample symbol set.
  - A concurrency test asserting the `compute_coverage` single-flight runs ≤1 cold `_compute_coverage_uncached` prefill at a time.
  - Frontend: a type-check / test proving `StockRow.sector: string | null` and that the sector comparator + filter handle null without throwing.
- **Error cases:**
  - `/stocks` with null-sector rows sorted by "Sector" → contained, no crash.
  - A forced uncaught client error → `error.tsx`/`global-error.tsx` card with nav preserved (not a blank app).
  - Cold `/api/data` under concurrent probes → completes without OOM under the 6144 MB cap.

## NOTES

- **Depth = full is mandatory.** Prior verdict REGRESSION (evaluator explicitly recommends FULL for iter-19); backend data-load-path change + crash containment need the full pipeline. Eval item 4 REQUIRES the auditor to re-run and reconcile the ux-regression verdict — the iter-18 auditor ran with the backend down and missed the crash sitting in its own cited evidence folder.
- **Runs only after `--acknowledge-regression`** (REGRESSION halts the loop for human review).
- **No Evidence Claim block** — no new "Proven" claim is surfaced, so the post-decompose gate passes automatically (goal.md loop rule).
- **Coupled-change justification (rubric rule 5):** the sector-null crash fix and the OOM prefill fix are ONE causally-coupled change-set, not two independent risky journeys — the OOM fix is a prerequisite for verifying the sector fix (the browser-QA lane hangs on `/api/data` without it) and is guarded by byte-identical snapshot tests; J-12 is verification-only. Risk is concentrated, diagnosable, and revertible.
- **LESSON (iter-18 — data-contract widening):** when a widened field introduces nulls, enumerate and re-validate EVERY consumer (sort/filter/format/`.localeCompare`/`.toFixed`/`.map`) even when the component file's git diff is empty, and flip the TS type to `| null` so the compiler flags unguarded call sites — the "empty diff = no regression" heuristic AND `tsc` both gave false comfort in iter-18.
- **LESSON (iter-18 operator addendum — OOM):** ONLY `prices.py:84` is unbounded; the other `.all()` sites (`:253/:292/:312`) are per-symbol-bounded — do NOT refactor them. Any batch/bounds param threaded through `prefilled_bar_cache → prefill` must be OPTIONAL; preserve `ORDER BY symbol, date` + the `.date/.open/.high/.low/.close/.volume` attribute names for the snapshot tests. Also verify the coverage single-flight actually serializes (the log proved ≥6 concurrent prefills).
- **LESSON (iter-17 — sanctioned data-basis reset):** J-02/J-06/J-07/J-08/J-09 are `partial` because the ledger was reset to all-FAIL on the 30-year basis — goal.md-sanctioned, NOT a regression, and iter-19 does no evidence work, so they correctly STAY partial. The evaluator must not read them as regressions.
- **LESSON (iter-2/4/5/6 — harness):** confirm a `browser-qa-agent` telemetry record + a non-empty evidence dir exist and the AUDITOR ran before scoring; reconcile the canonical `ui-test-results.md` against any parallel `qa.md`; a single empty-leaderboard or "Backend unavailable" frame invalidates a run.
- **Scope guard:** iter-19 lands fast-platform **item A only** (the OOM), exactly as goal.md sequences it. Items B–K and J-15/J-16 as journey contracts are deferred to later iterations.
