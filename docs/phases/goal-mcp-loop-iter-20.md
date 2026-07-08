# Goal Iteration 20 — Data Manager coherence with the 548 pool + unambiguous availability legend (J-13)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** mcp-loop
- **Iteration:** 20
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-13
- **Required-still-passing journeys:** J-01, J-03, J-05, J-10, J-12
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

On `/data`, the generic **Fetch** job keeps the whole committed ~548-name pool fresh, the "Expand universe" job option is gone, and the per-date availability heatmap's legend unmistakably separates its two distinct signals (price-data completeness = cell fill vs. scored-snapshot exists = indicator) so no two encodings look alike while meaning different things.

## BACKGROUND

The iter-19 CONTINUE closed the iter-18 regression and stabilized the backend on the 30-year / 548-pool basis (the `/api/data` OOM was fixed by fast-platform item A), so the loop resumes forward feature work. The iter-19 evaluator's primary recommendation is **J-13** — "a self-contained IA/UX journey now unblocked by the stable `/data` path." Per the priority rubric: there are **no regressed journeys** (J-01 recovered iter-19) and iter-19 coherence was **COHERENCE-PASS** (no consolidation owed), so the next chunk is unbuilt Must-have work; among the ready candidates (J-13, J-14, J-15/J-16) **J-13 has the smallest, most self-contained change set** (rule 4) and ships pure UX/correctness/navigation clarity with **no new "proven" claim** (no `## Evidence Claim` — the post-decompose gate passes automatically). The still-`partial` evidence journeys (J-02/J-06/J-07/J-08/J-09) are goal.md-**sanctioned partial** on the reset ledger and are deliberately NOT targeted here: re-certifying an edge is referee-gated and risky, each canonical promotion permanently tightens the Bonferroni bar, and the honest-stop guard forbids forcing — they wait for a dedicated new-basis staging-discovery + honest-promotion iteration (see NOTES). Depth is **full** because the change crosses backend (Fetch job scope) + frontend (legend re-encode + interlinked dead-code removal) and touches the data-fetch path — exactly the data-contract-adjacent class where the ux-regression + closure + audit guards proved their worth catching iter-18 (iter-18/iter-19 lessons); prior evaluator also recommended full.

## IN SCOPE

### Backend
- [ ] **Point the generic Fetch symbol set at the committed 548 pool.** In `app/engine/data_manager.py` `_run_job` (the fresh-fetch symbol-set branch at ~`:2959-2960`), replace the ~122-based default `symbols = all_seed_symbols(cfg)` with the **existing** `all_seed_symbols ∪ read_pool` union helper `symbols = price_load_symbols(cfg, seed_dir)` (defined `seed_loader.py:188`, already the exact scope `load_prices` uses since iter-18/J-12; `cfg` and `seed_dir` are both in scope at this call site — the sibling `is_expand` branch at `:2955` already uses `read_pool(seed_dir)`). This covers **every** pool name (J-13 step 1) WITHOUT dropping the context symbols (benchmarks/ETFs/`^VIX`/macro proxies) the old `all_seed_symbols` default kept fresh — prefer this union over raw `read_pool(seed_dir)`, which would silently stop refreshing the context series (an honest-coverage regression; iter-18 lesson). Do NOT touch the `is_expand` or `symbols_override` (J-37 gap-pull) branches.
- [ ] **Leave the availability data path byte-identical.** `data_manager.compute_availability` (`:878`) and `GET /api/data/availability` (`app/api/data.py:141-149`) — which emit `symbols_with_bars` / `total_symbols` / `snapshot_exists` — are UNCHANGED. J-13 is a presentation-only clarity change; the served numbers must stay byte-identical.
- [ ] The backend still accepting `kind:"expand"` is fine (harmless; `scripts/screen_universe.py` remains the offline escape hatch) — do NOT rip out the backend expand job or `get_market_caps`.

### Frontend
- [ ] **Remove the "Expand universe" job option and its now-dead supporting code** in `apps/frontend/app/data/page.tsx`: the `<option value="expand">Expand universe</option>` (`:2122`) plus the code that only existed to support it — `isExpandKind` (`:240`) and its use in `isFetchKind` (`:242`), `sourceIneligibleForExpand` (`:246`), the `handleStart` market-cap guard (`:386-389`), the `JobForm` `isExpandKind`/`sourceIneligibleForExpand` props + disabled wiring (`:493-494`, `:2047-2048`, `:2068-2069`, `:2087`), the source-eligibility option suffix + amber "cannot supply market cap" alert (`:2135-2187`), the panel title/copy mentioning expand (`:2091`, `:2216-2217`), the `JobProgressPanel` expand branch (`isExpand` `:2396`, `showFetch` `:2399`, `{isExpand ? <ExpandScreenResult/> : null}` `:2515`), and the `ExpandScreenResult` component (`:2537+`). Remove ONLY code your removal makes unused; leave unrelated `/data` controls (fetch / backfill / both, the J-37 gap-pull, rebuild) intact and working. `npx tsc --noEmit` (or the frontend typecheck) must be clean — no dangling reference.
- [ ] **Market-cap decision (conscious, honest):** Expand was the only on-demand market-cap refresh (J-84 `get_market_caps` → `universe.json`). Since market cap is display-only (the per-date resolver drops it), take the **minimal honest choice**: accept the committed/static caps and ensure no `/data` copy implies caps are still on-demand-refreshable. Fabricate no data; hide no gap.
- [ ] **Clarify the per-date availability legend** in `apps/frontend/components/availability-heatmap.tsx` so the two orthogonal signals never collide:
  - Split the single legend row (`:231-247`) into **two labeled groups**: **"Price data — cell fill"** (the density buckets) vs **"Scored snapshot — indicator"** (the ring/marker).
  - Make the density ramp a **monotonic single-hue scale** so the **top ("full") bucket is no longer amber** — amber (`--heat-5` `#f0b429`, `globals.css:30`) is the page's warning color and currently collides perceptually with the 75–<100% green (`--heat-4` `#4cc35a`, `:29`). Adjust `--heat-0..5` (+ `--heat-text-*` for contrast) in `apps/frontend/app/globals.css` and, if needed, `tailwind.config.ts`.
  - Give the snapshot indicator an **unambiguous non-green treatment** (today it is `ring-2 ring-pos`, `:321`, and `--pos` `#34d399` is green — it collides with the green density fills). Pick a treatment that reads distinctly regardless of the cell's fill.
  - Update the caption (`:335-337`) + the per-cell tooltip/`title` (`:306-307`) + the header blurb (`:197-198`) to state each meaning plainly and name the **Fetch → fills / Backfill → scores** workflow.

### New user-facing capability
The user can tell at a glance, on `/data`, whether a given trading day (a) has complete stored price data and (b) has an immutable scored snapshot — as two clearly-separate signals — and understands that Fetch fills price data while Backfill produces scored snapshots. Keeping the seed fresh via the generic Fetch now covers the whole 548-name pool.

### New information displayed
No new computed value. The same `symbols_with_bars` / `total_symbols` / `snapshot_exists` from `GET /api/data/availability` are re-encoded for clarity (two labeled legend groups; collision-free color/indicator). The clarified caption/tooltip text is new copy over existing data.

### New user actions
None added. One option is REMOVED (the "Expand universe" job kind); the fetch / backfill / both / gap-pull / rebuild actions are unchanged.

### UI surface changes
`/data` only: the job-kind picker loses "Expand universe" (and its source-eligibility alert), and the availability heatmap's legend + color ramp + snapshot indicator + caption/tooltip are re-encoded. No new page, no route change.

### Product surface delta
The Data Manager stops advertising a job kind that is redundant now the 548 pool is the committed default, and its most information-dense widget (the availability heatmap) becomes unambiguous — a day that is "full but not yet scored" (a backfill gap) is now visually and textually distinct from a fully-scored day.

### Blueprint conformance
J-13's canonical home `/data` (Data Manager) is already registered in `blueprint.md`'s Information Architecture (feature-homes table, J-13 row). No new page, no nav-skeleton change. An additive **iter-20 clarification** paragraph is added to `blueprint.md` documenting that this is a presentation-only clarity change + internal Fetch-job-scope wiring reading the SAME `GET /api/data/availability` value — no new displayed value, no new endpoint, no re-approval requested.

### Data-contract additions
**None.** J-13 introduces no new displayed value: the availability figures still come from the single existing `compute_availability` → `GET /api/data/availability` source (byte-identical), and the Fetch-scope change is internal job wiring (what a future Fetch covers), not a served value. The "Expand universe" removal deletes a surface, adds none. No `## Evidence Claim` (pure UX/correctness/navigation — no new "proven" status).

## OUT OF SCOPE

- Any `## Evidence Claim` / referee submission / ledger write — J-13 surfaces no "proven" status; both ledgers stay untouched and all-FAIL.
- Re-certifying the sanctioned-partial evidence journeys J-02 / J-06 / J-07 / J-08 / J-09 on the 30-year basis (needs a separate new-basis staging-discovery + honest-promotion iteration — see NOTES).
- J-14 (deep index/macro context + vendor labels), J-15 / J-16 (fast-platform perf budgets) — sequenced separately.
- Ripping out the backend `kind:"expand"` job, `get_market_caps`, or `scripts/screen_universe.py` (keep them as the offline escape hatch).
- Folding a fresh market-cap refresh into the Fetch job or a new dedicated action (a follow-on only if fresh caps are later shown to matter; static committed caps are honest for now).
- Any change to `compute_availability`'s numbers or semantics, or to the `/stocks`/`/methodology` universe surfaces.

## DEFINITION OF DONE

- [ ] Target journey J-13 passes via browser-qa-agent (all three steps: 548-pool Fetch scope; two-group split legend; hover distinguishes a bars-but-no-snapshot date from a snapshot date).
- [ ] The generic Fetch job's target symbol set is a **superset of the committed 548 pool** (every pool name covered) AND still includes the context symbols — asserted by a backend unit/integration test (count + membership).
- [ ] The `<option value="expand">` is absent from the `/data` job-kind picker (DOM-verified) and the job form still starts a fetch / backfill / both without error.
- [ ] The availability legend renders **two labeled groups** ("Price data — cell fill" and "Scored snapshot — indicator"); the density top bucket is **not amber** and the snapshot indicator is **not green** (no encoding collision) — DOM/computed-style verified.
- [ ] `compute_availability` output (`symbols_with_bars` / `total_symbols` / `snapshot_exists`) is byte-identical to before the change — asserted by a backend test (anti-goal #3).
- [ ] Required-still-passing journeys J-01, J-03, J-05, J-10, J-12 remain green (deterministic replay).
- [ ] No anti-goal violation introduced (esp. #1 no fabricated data from the Expand removal / caps honestly static; #2 no buy-sell/return language in new legend/caption/tooltip copy; #3 availability numbers byte-identical; #8 `/data` does not crash and degrades gracefully).
- [ ] Frontend typecheck (`tsc --noEmit`) clean — no dangling reference from the removed Expand code.
- [ ] Unit tests pass; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-mcp-loop-iter-20-dev.md`.

## TESTING REQUIREMENTS

- **Browser (canonical browser-qa-agent lane):**
  - **J-13** on `/data`: (1) the job-kind picker has no "Expand universe" option and a fetch/backfill still starts; (2) the availability legend shows two labeled groups with no amber "full" bucket and a non-green snapshot indicator; (3) hover a date with bars but **no** snapshot (a backfill gap) and a date **with** a snapshot — the tooltip + legend make the difference obvious and name the Fetch→fills / Backfill→scores workflow.
  - Regression replay: **J-01** (`/stocks` leaderboard + Sector sort — the iter-18 crash driver, highest-value smoke), **J-03** (honest "Not yet proven" marking), **J-05** (`/evidence` ledger renders), **J-10** (`/stocks/{ticker}` deep-history chart), **J-12** (broad point-in-time universe on `/methodology` + `/stocks`).
  - Keep BOTH prod-mode services up for the whole run (`start-backend.sh` / `start-frontend.sh`, never `dev.sh`); the item-A OOM fix (iter-19) means `/api/data` now survives, but confirm the backend stays up.
- **Unit/integration:**
  - Backend: the generic Fetch symbol set ⊇ the 548 pool (and retains context symbols); `compute_availability` fields byte-identical (a fixed-DB snapshot assertion).
  - Frontend: a component/DOM assertion that the availability legend renders two labeled groups and that the density top bucket and the snapshot indicator use distinct, non-colliding tokens.
- **Error cases:** removing the Expand option must not break the job form (fetch/backfill/both still start; `tsc --noEmit` clean, no dangling `isExpandKind`/`ExpandScreenResult`/`sourceIneligibleForExpand`); market caps continue to display honestly as committed/static (no fabricated or dead-name data); an uncaught `/data` client error still degrades to the contained `error.tsx` boundary, never a blank application-error page (anti-goal #8).

## NOTES

- **Screenshot hygiene (iter-3 / iter-11 / iter-13 / iter-14 lessons — recurring).** The availability legend + heatmap sit below the fold on `/data`. Scroll the legend and the two hovered cells into frame BEFORE capture, prefer **full-page** (not scrolled-viewport, which yields ~5855-byte blank frames) or element-clip captures, and `md5sum` the evidence PNGs so one reused capture is not relabeled across the three J-13 assertions. A capture must actually show the two-group legend and the distinguished snapshot/no-snapshot cells.
- **Which gates to trust (iter-18 / iter-19 lesson).** For this data-contract-adjacent, dead-code-removal iteration, the **ux-regression + closure + audit** gates are the ones that caught iter-18 and cleared iter-19 — do not accept a status.json/QA "ready to ship" over a `-fail-` frame in the evidence folder; reconcile self-reported blockers against the actual evidence dir and the ux-regression/closure verdicts.
- **Honest-coverage guard (iter-18 lesson).** Using `price_load_symbols(cfg, seed_dir)` (the `all_seed_symbols ∪ read_pool` union) rather than raw `read_pool(seed_dir)` is deliberate: raw `read_pool` would drop the benchmark/ETF/`^VIX`/macro context the current default keeps fresh — a silent coverage regression. The union is the exact scope `load_prices` already uses.
- **Evidence journeys are future work, not this iteration.** J-02 / J-06 / J-07 / J-08 / J-09 stay sanctioned-partial (goal.md "Data-basis change" provision) until a genuine edge re-certifies on the 30-year basis. That is a separate riskier iteration: re-run the pre-registered staging exploration on the new data → promote ONLY a winner whose recorded block-bootstrap `p` clears the canonical Bonferroni bar (currently divisor 8) with margin, via an explicit `"ledger":"canonical"` `## Evidence Claim`; honor the honest-stop guard (report, never force). Do NOT casually append a canonical claim (each permanently tightens the bar — iter-8 ma_stack / iter-10 footgun).
- **Non-blocking carry-forwards from iter-19 (do NOT reopen here):** F1 Full-history chart x-domain widening; B1 a genuine cold-restart `/api/data` re-repro; B2 sample VmSize (not RSS) in `perf-budgets.md`; T1 re-run `tests/test_scanner.py` + `tests/test_bars.py` when a seed-load budget allows; F3 `return-attribution.tsx` null-sector "Unassigned" consistency.
- **Reference:** iter-19 eval `runs/goal-session-mcp-loop/iter-19/eval.md` (primary J-13 recommendation); goal.md §G "Data Manager page coherence with the 548 default" (exact change list); goal.md J-13 acceptance.
