# Goal Iteration 27 — Memory-harden the full-universe backfill/rebuild so J-16 data jobs never exhaust the service

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** mcp-loop
- **Iteration:** 27
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes (verification only — no frontend source change planned; the `/data` job-progress surface is re-verified, not modified)
- **Target journeys:** J-16
- **Required-still-passing journeys:** J-01, J-03, J-04, J-05, J-10, J-12, J-13, J-15
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked values MUST render a "not yet proven" state. *(critical)*
  - **Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha claims; never place or simulate orders. *(critical)*
  - A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation for the same as-of date — not merely that the page renders. *(critical)*
  - **No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of; never introduce lookahead anywhere. *(critical)*
  - No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the post-decompose gate. *(critical)*
  - No hard-coded credentials, API keys, or tokens in source files. *(critical)*
  - **Resilience to data-shape and data-scale change:** widening the data basis (new nulls, broader pools, deeper history) must never crash an existing page or exhaust a service's memory — every existing consumer of a widened field is re-validated, the UI degrades gracefully (contained error boundary, honest "—"/NA placeholder, never a blank application-error page), and unbounded whole-table ORM loads are forbidden on the deep basis. *(critical)*

## GOAL

The full-universe (322-date × 541-member) "Rebuild snapshots" / backfill job runs to a verified completed state under the `ulimit -v 6291456` cap without exhausting memory, so J-16's data jobs are fast, honest about progress, and never crash the backend — resolving the unresolved critical anti-goal #8 violation that halted iter-26.

## BACKGROUND

iter-26 was scored **REGRESSION**: driving J-16's own job path (the full-universe "Rebuild snapshots" backfill) reproduced a `MemoryError` that took the entire backend down — an **unresolved critical anti-goal #8 violation** (decision-tree rule 1). This iteration is the dedicated memory-hardening + fix-verification recovery pass the iter-26 evaluator asked for: **no new feature or evidence work.** Per the priority rubric, the unresolved critical anti-goal outranks all forward work, and fixing it also unblocks the 8 required-still-passing journeys that were SKIPPED behind the wedged backend last iteration (carried unverified, not regressed).

**Precise root cause (from the coordinator hand-off + iter-26 audit §5.4 — do not re-diagnose):** the crash is **virtual-address-space (VSZ) exhaustion, NOT an RSS overflow.** The dying process pinned **VSZ at exactly 6144 MB** (the `ulimit -v` ceiling derived from `server.memory_cap_mb`) while **RSS was only ~4932 MB**. The `MemoryError` frame is `apps/backend/app/engine/prices.py:191` `_BarCache.bars_asof` (the `full[:cut]` slice), reached via `regime._index_ma_stack` during `data_manager._compute_one_backfill_date → scanner.compute_run_payload → regime.score_regime`. The **dominant VSZ driver is pre-existing code iter-26 never touched**: the whole-universe prefill in `data_manager._do_backfill` (holds all 541 members' bars) plus the per-(symbol,date) transient `full[:cut]` slices piled on top across the deep-history dates. An audit fix-mode pass already removed a *real but non-dominant* allocation regression iter-26 introduced (cache-aware `close_on`/`bars_after` materializing `full[:cut]`), byte-identity-verified — so the remaining work is bounding/streaming the pre-existing whole-universe prefill and/or the regime `full[:cut]` allocation.

**Two measurement failures let this through — iter-27 must not repeat them (lessons iter-26 / iter-26b):** (1) the perf evidence sampled peak **RSS** and passed; the failure is **VSZ** — this iteration MUST sample `VmPeak`/`VmSize` (and `VmRSS`) from `/proc/self/status` under a literal `ulimit -v 6291456`. (2) the benchmark used a **12-date subset**; the crash requires the **full 322-date universe rebuild shape** (all 541 members prefilled + deep-history dates). A subset benchmark cannot catch it.

Depth is **full**: prior depth was full; this is a REGRESSION-recovery pass over cross-cutting backend memory/compute paths (`prices.py`/`_BarCache`, `regime.py`, `data_manager` backfill/prefill) under a strict byte-identity gate; it needs the full 11-step pipeline whose audit / ux-regression / closure gates are the ones that caught iter-24 and iter-26 (the QA lane fail-opened past both).

## IN SCOPE

### Backend
- [ ] **Bound/stream the dominant VSZ allocation on the full-universe rebuild path** (audit §5.4 + goal.md fast-platform item A). The unbounded whole-universe prefill in `data_manager._do_backfill` and/or the regime `_index_ma_stack` `full[:cut]` slice (`prices.py:191` `_BarCache.bars_asof`) must stop reserving address space proportional to the entire pool × full history at once. Preferred, byte-identity-safe directions (developer picks the minimal set that clears the memory budget):
  - Window the regime consumer: `regime._index_ma_stack` needs only its bounded MA-stack lookback, not the entire `full[:cut]` history — return/consume a bounded recent slice so no per-(symbol,date) call allocates the full deep history.
  - Give `prefill` the OPTIONAL `symbols=` / `min_date=` bounds from goal.md item A (load only pool ∪ benchmarks; a bounded date-range caller passes `min(target_dates) − max_lookback`), **both defaulting to today's behavior** so `test_bar_cache.py`'s byte-identical snapshot shims (monkeypatch at `:91`/`:256`; 2-arg call at `:102`) stay green.
  - Any new parameter threaded through `prefilled_bar_cache → prefill` MUST be OPTIONAL and preserve `ORDER BY symbol, date` and the returned attribute names (`.date/.open/.high/.low/.close/.volume`).
- [ ] **Byte-identity gate the change** — per-(symbol,date) snapshots, forward returns, and membership resolve to identical values vs the pre-fix path. The gate is `apps/backend/tests/test_scoring_window.py` + the `test_forward_testing.py` cache-awareness cases (existing), extended if needed with a bounded harness that compares `score_stocks` / `score_regime` output over ≥3 dates × the full pool, windowed-vs-unwindowed. ANY diff ⇒ an indicator/consumer silently depends on deeper history ⇒ widen the bound, never accept drift.
- [ ] **Measure the crashing shape** — run the **full 322-date × 541-member universe rebuild** under a literal `ulimit -v 6291456`, sampling **`VmPeak`/`VmSize` AND `VmRSS`** from `/proc/self/status`, and record before→after numbers in `reports/perf-budgets.md` as a **never-regress budget** (both VSZ and RSS must sit under 6144 MB with margin). This must run **in a single foreground agent turn** (background processes are reaped at turn end — do NOT background-and-wait across turns); if the entire warmup exceeds a single foreground window, the repro must still exercise the full-universe prefill (all 541 members) plus the deep-history cadence dates where `full[:cut]` slices are largest, since peak footprint is reached there.

### Frontend (if applicable)
- [ ] None planned — no frontend source change. Re-verify only that the `/data` job-progress surface still shows honest live progress (never "done early") and that a genuinely-down backend degrades to the single contained "Backend unavailable" card with nav/shell intact (anti-goal #8; the iter-25 boundary, not the iter-18/24 blank app-error crash).

### New user-facing capability
None new. The user-visible outcome is a restored one: the Data Manager rebuild/backfill job completes without crashing the backend, and every core page/API stays reachable during and after a full-universe job.

### New information displayed
None. The only report edit is the before→after full-universe VSZ/RSS memory budget appended to `reports/perf-budgets.md` (a report, not a UI value).

### New user actions
None.

### UI surface changes
None (verification-only on `/data`).

### Product surface delta
The product stops crashing under its own heaviest offline job on the deep basis; no experience is added, one is de-regressed.

### Blueprint conformance
No new surfaces. J-16's home is the EXISTING `/data` (job progress) + the committed budgets in `reports/perf-budgets.md`, both already in the Information Architecture. An additive **iter-27 clarification** is registered in `blueprint.md` documenting the internal memory-path hardening (same values, same modules, same endpoints, byte-identical). No nav-skeleton change — no re-approval requested.

### Data-contract additions
**None.** This is an INTERNAL compute/memory-path change beneath already-registered values (the three per-stock scores `scoring:score_stocks`; the regime score `regime:score_regime`; realized forward returns; bars; `data_manager.compute_availability` / `compute_coverage` / `compute_capacity`). Every registered value re-serves byte-identically from its existing single computing module and single serving endpoint — read from those canonical sources; introduce no second computation or endpoint.

## OUT OF SCOPE

- **No new feature or evidence work.** No `## Evidence Claim` (the post-decompose gate passes automatically); both ledgers stay byte-identical all-FAIL; the canonical Bonferroni divisor stays 8; J-02/J-06/J-07/J-08/J-09 remain **sanctioned-partial (NOT regressed)** — their re-certification is the separate priority-2 work, never bundled here (rubric rule 5).
- **Do NOT rebuild or re-litigate the iter-26 scoring-window feature** (goal.md item F, in the WIP at commit `907cd6d`). It is correct and byte-identity-gated by `test_scoring_window.py`; build the memory fix on top of it.
- **Do NOT run the full pytest suite** (~10–11 h at the 30-year data basis — test-only cost, out of scope). Gate byte-identity via the targeted tests named above.
- **Do NOT refactor the per-symbol-bounded `.all()` sites** in `prices.py` (`:115` lazy per-symbol, `:253`, `:292`, `:312`) — only the unbounded whole-universe prefill / regime `full[:cut]` path is in scope (iter-18 addendum).
- No new displayed value, no new endpoint, no nav-skeleton change.

## DEFINITION OF DONE

- [ ] Target journey **J-16 passes via browser-qa-agent**: the full-universe "Rebuild snapshots" / backfill job is driven live past the previously-crashing deep-history dates to a verified completed (or monotonically-advancing, no-early-"done") state with the backend surviving and every endpoint still 200 — no `MemoryError`, no wedged backend.
- [ ] **Cold `GET /api/data` no-OOM repro passes** (mandatory, iter-24 lesson): stop backend → cold-start → load `/data` as the FIRST request, ≥2×; backend survives, `/data` renders populated, downstream `/stocks` loads, `/api/health` 200 after.
- [ ] The full 322-date × 541-member rebuild under literal `ulimit -v 6291456` records **peak `VmPeak`/`VmSize` < 6144 MB AND peak `VmRSS` < 6144 MB** with margin, committed as a before→after never-regress budget in `reports/perf-budgets.md`.
- [ ] Per-(symbol,date) snapshots, forward returns, and membership are **byte-identical** to the pre-fix path (`test_scoring_window.py` + `test_forward_testing.py` cache-awareness cases green; any windowed-vs-unwindowed harness reports 0 diffs).
- [ ] All 8 Required-still-passing journeys (J-01, J-03, J-04, J-05, J-10, J-12, J-13, J-15) re-verified **live PASS** by the canonical browser-qa lane (closing the iter-26 skipped-behind-the-outage gap).
- [ ] Critical **anti-goal #8 violation is RESOLVED (`resolved=true`)**, re-verified by the canonical browser-qa lane (an engine-level ablation fix is NOT sufficient — iter-24 lesson).
- [ ] Determinism + no-lookahead preserved (scoring ≤ as-of, forward returns > as-of); no anti-goal violation introduced.
- [ ] Targeted unit tests pass; no regressions in the byte-identity suite.
- [ ] Dev handoff written at `docs/handoffs/goal-mcp-loop-iter-27-dev.md`.

## TESTING REQUIREMENTS

- **Browser (canonical browser-qa-agent, live):**
  - **J-16** — drive the `/data` "Rebuild snapshots" / backfill job over the full universe; confirm it advances past the deep-history dates that crashed iter-26 (dot-com / GFC / COVID / recent) with the backend surviving and honest live progress (counter advances, never premature "done"). md5-distinct full-page evidence frames.
  - **J-13 / J-15 cold-path** — stop → cold-start → `/data` as FIRST request ×2, no OOM (the iter-24/25 sequence).
  - **Live replay** — J-01, J-03, J-04, J-05, J-10, J-12 against the fixed build.
- **Unit/integration (targeted — NOT the full suite):** `apps/backend/tests/test_scoring_window.py` (scoring-window byte-identity), `test_forward_testing.py` cache-awareness cases, `test_bar_cache.py` snapshot byte-identity (the OPTIONAL-param preservation gate). Confirm the memory-bound path re-serves byte-identical values.
- **Memory measurement:** the full 322-date × 541-member universe rebuild under `ulimit -v 6291456`, sampling `VmPeak`/`VmSize` + `VmRSS` from `/proc/self/status`; before→after appended to `reports/perf-budgets.md`.
- **Error cases:** a genuinely-down backend must degrade to ONE contained "Backend unavailable" card (nav/shell intact, no fabricated values, no blank application-error page); the running job must never mark partial/fabricated data complete or report "done early."

## NOTES

- **Lessons in force (surface to developer/reviewer/QA):**
  - *iter-26:* an RSS-only probe on a 12-date subset structurally cannot catch a VSZ ceiling hit on the full shape — sample BOTH VSZ and RSS under the real `ulimit -v` on the full-universe long-job.
  - *iter-26b:* decompose so the target path itself (not just a heavier fallback) exercises the crashing full-universe shape; a verified crash on any driven path is a journey failure + critical anti-goal #8 regardless of causation.
  - *iter-24:* a critical anti-goal fix applied after the canonical browser-qa lane ran must be **re-verified by that lane** before the violation counts resolved; a `/api/health` boot is a DIFFERENT code path and gives a false "cold path OK" — use the stop→cold-start→`/data`-first repro.
  - *iter-18 addendum:* only the whole-universe prefill / regime `full[:cut]` path is unbounded; the other `prices.py` `.all()` sites are per-symbol-bounded — do not touch them; new prefill params must be OPTIONAL to keep `test_bar_cache.py` shims green.
  - *iter-25:* md5-scan the evidence dir for reused/relabeled frames; an error-card frame cited under a PASS invalidates that citation.
- **Host constraints (do not misread as product defects):**
  - **Backend cold start ≈ 130 s**; the harness health-probe window (~48 s) is too short — a "backend failed to become healthy" line is a harness timeout, not a product defect. Wait for readiness (non-HTTP `ss -tln` poll preserves true first-request semantics) before dispatching QA.
  - **Background processes are reaped at agent turn end** — the memory measurement and repro must run in-turn (foreground); do not structure any step as background-and-wait across turns.
  - **Triggering the 322-date rebuild destroys the environment for later steps unless the memory issue is actually fixed first** — land + unit-verify the bound before driving the live full-universe job.
- **Base state:** build on the iter-26 WIP (commit `907cd6d`, unpushed; remote at `eaf42d1`) which already carries the correct scoring-window feature + the audit's byte-identity-verified removal of iter-26's own `close_on`/`bars_after` allocation regression. The remaining fix is the pre-existing whole-universe prefill / regime `full[:cut]` VSZ driver.
- **Reachability after this iteration:** GOAL_ACHIEVED remains out of reach afterward — J-02/J-06/J-07/J-08/J-09 stay sanctioned-partial (no staging winner clears divisor-8 today), which is the separate priority-2 evidence work, not this pass.
