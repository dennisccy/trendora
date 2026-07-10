# Goal Iteration 26 — Fast, honest data jobs (fast-platform item F: window the scoring inputs)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** mcp-loop
- **Iteration:** 26
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes (no frontend *source* change — the browser lane runs to verify the existing `/data` job-progress surface renders honestly on the optimized backend and to replay the required-still-passing journeys)
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

Make the data jobs (Backfill + warmup) materially faster on the 30-year basis by bounding the scoring-input window, while every displayed score/forward-return stays **byte-identical** and the `/data` job progress stays honest — flipping J-16 unknown → passing.

## BACKGROUND

J-16 is the last tractable unbuilt journey and the iter-25 evaluator's explicit priority-1 ("fast-platform data-jobs perf … the byte-identity-gated scoring-window change … FULL"). Nothing regressed and iter-25 coherence was COHERENCE-PASS, so no consolidation is owed; the priority rubric selects J-16 (rules 4/5: smaller, self-contained, and it must NOT be bundled with the J-02/J-06/J-07/J-08/J-09 evidence re-certification — two risky changes in one diff are undiagnosable). Fast-platform **items A** (bar-prefill stream, iter-19) and **B** (SQLite pragmas, iter-24; mmap OOM fixed iter-25) are already landed; the remaining piece is **item F** — the 2–8 s/date CPU driver. Confirmed unbuilt against the tree: `grep max_lookback` finds nothing in `apps/backend/app/` or `config.yaml`; `scoring.py:113` (`_raw_components`) and `scoring.py:339` (pass-3) both call `bars_asof(...)`, which returns each member's *whole* ascending series ≤ D (≈5,300 bars on late dates) into every indicator whose longest lookback is only ~252 bars (`indicators.high_window_52w`); and `warmup.py`'s `backfill_forward_returns(engine, cfg)` runs *after* the `with bar_cache(session):` block closes. Depth is **full** because this changes the shared scoring computing module behind every displayed score, requires a dedicated byte-identity harness beyond browser smoke, and touches the `/data` job-progress surface — exactly the risky data-path change the audit/ux-regression/closure guards exist for (evaluator: "FULL … the exact risky byte-identity-gated data-path change").

## IN SCOPE

### Backend
- [ ] Add config `indicators.max_lookback_bars` (a bounded int, no inline literal) = the TRUE maximum lookback across `_raw_components` (`scoring.py:119-135`) AND the pass-3 detectors (VCP / pullback / flat-base / hist_volatility / vol_contraction / downside_vol) **plus a safety margin** (start ~320 = `high_window_52w` 252 + margin; the byte-identity harness is the authority — if it shows ANY diff, widen, never accept drift).
- [ ] Slice each member's as-of series to the last `max_lookback_bars` bars (`bars[-N:]`) BEFORE indicator computation at both `bars_asof(...)` sites in scoring (`scoring.py:113` in `_raw_components` and `scoring.py:339` in pass-3). A member with < N bars keeps its whole (short) series — short-history NA propagation is unchanged.
- [ ] Move `warmup.py`'s `backfill_forward_returns(engine, cfg)` INSIDE the shared `bar_cache` context that already wraps the snapshot loop, so its per-(run,symbol) `close_on`/`bars_after` reads slice the already-loaded lightweight cache instead of issuing ~330k bounded queries. This is a load-scope change only: forward returns still slice bars **> as-of** and scoring still slices **≤ as-of** — no-lookahead preserved (anti-goal #5); the realized forward-return values stay byte-identical.
- [ ] Commit the measured before → after per-date-backfill + full-warmup timings to `reports/perf-budgets.md` as the never-regress J-16 budgets. The measurement must exercise a REAL deep-history cadence date (the current `measure-perf.sh --backfill-days 5` hits empty 2005 ranges = a 0.23 s no-op — extend the harness with a config-driven bounded cadence date/subset, no literals, OR time `score_stocks` on a fixed late cadence date over the full pool; same host, prod mode, baseline = window disabled, after = window enabled).

### Frontend (if applicable)
- [ ] No frontend source change. The browser lane verifies the EXISTING `/data` job-progress surface still shows honest live progress (never "done early", no fabricated/partial-marked-complete) on the faster backend, and that the storage card + availability legend render byte-identical.

### New user-facing capability
Backfill/warmup data jobs complete materially faster (≥30%) on the deep basis; the committed budgets in `reports/perf-budgets.md` gain the before/after job-timing rows that make future regressions catchable.

### New information displayed
None in the UI. The only new displayed content is the before/after job-timing rows in `reports/perf-budgets.md` (a committed report + the J-16 walkthrough source, not a UI value). `/data` displays no new value.

### New user actions
None. Existing Fetch/Backfill/warmup jobs, unchanged controls — only faster.

### UI surface changes
None. No frontend source change; `/data` job-progress panel, storage card, and availability legend are byte-identical.

### Product surface delta
Jobs run faster and progress stays honest; nothing visually new. The user-visible contract is speed + preserved honesty, verified by browser-qa on `/data` and by the byte-identity gate on every score.

### Blueprint conformance
J-16's canonical home is `/data` (job progress + committed job-timing budgets) — already registered in `blueprint.md`'s Information-Architecture homes table. No new page, no nav-skeleton change. A short additive iter-26 clarification paragraph is appended to `blueprint.md` documenting the internal compute-path change (no new Data Contract row, no re-approval).

### Data-contract additions
**None.** `indicators.max_lookback_bars` bounds the INPUT window of the SAME `scoring:score_stocks` computing module serving the already-registered three per-stock scores via the EXISTING `GET /api/stocks` / `GET /api/stocks/{ticker}`; it re-serves those values byte-identically (harness-gated). The warmup-cache-scope change re-serves the already-registered realized forward-return value byte-identically. No new computing module, no new serving endpoint, no second computation of any value in the Data Contract — every reader keeps reading its one registered canonical source.

## OUT OF SCOPE

- The evidence re-certification of J-02 / J-06 / J-07 / J-08 / J-09 — a SEPARATE risky referee-gated change; never bundled with item F (rubric rule 5). This iteration does ZERO evidence work.
- **No `## Evidence Claim`** — this is pure performance/correctness; the post-decompose gate auto-passes. No ledger write, no canonical promotion; both ledgers stay byte-identical all-FAIL; the canonical Bonferroni divisor stays 8.
- Fast-platform items already landed (A, B, C, D, G, H) and items deferred to their own iterations: **E** (lean leaderboard summary DTO), **I** (frontend interaction costs — heatmap memo / leaderboard debounce), **J** (`record_json` shrink), and anything past F.
- Deleting the dead-duplicate `index-regime-chart.tsx` / `major-indexes-card.tsx` (coherence-WARN carry-forward) — defer to a dedicated tidy iteration.
- Hardening / down-weighting the non-terminal QA lane (recurring weak-evidence flag) — a separate tidy iteration, not this perf change.
- No new UI value, no new endpoint, no nav change, no `/bars` or chart change.

## DEFINITION OF DONE

- [ ] `indicators.max_lookback_bars` is added to config and both scoring `bars_asof` sites (`:113`, `:339`) slice to it before indicator computation.
- [ ] **Byte-identity harness (correctness gate):** `score_stocks` output is byte-identical windowed vs unwindowed over ≥3 dates × the full pool (0 diffs). Harness is committed and green.
- [ ] `warmup.py` `backfill_forward_returns` runs inside the shared `bar_cache` context; the forward-return backfill output is byte-identical to the pre-change path.
- [ ] The existing scoring / bar-cache / forward-return unit tests are **UNEDITED and green** (`tests/test_bar_cache.py` byte-identical snapshots; scoring + forward-return suites). An EDITED expectation test is itself the regression signal (iter-9 lesson) — if one must change, stop and treat it as drift.
- [ ] Per-date backfill on a real deep-history cadence date improves ≥ 30% vs the committed baseline on the same host (network fetch time excluded); recorded in `reports/perf-budgets.md`.
- [ ] A full warmup pass (or a fixed ≥10-date deep-history representative subset, same subset both runs, if a full 124-date pass can't be run twice within budget) improves ≥ 30%; recorded as never-regress budgets.
- [ ] Peak process RSS during warmup/backfill stays under the 6144 MB `server.memory_cap_mb` cap — no memory regression (anti-goal #8).
- [ ] Target journey J-16 passes via browser-qa-agent (`/data` job progress = honest live progress, never "done early").
- [ ] Required-still-passing journeys J-01, J-03, J-04, J-05, J-10, J-12, J-13, J-15 replay green on the optimized backend.
- [ ] No anti-goal violation introduced; both ledgers byte-identical all-FAIL; divisor stays 8.
- [ ] Unit/targeted tests pass; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-mcp-loop-iter-26-dev.md`.

## TESTING REQUIREMENTS

- **Browser (canonical browser-qa-agent, live):** J-16 — `/data` job-progress renders honest live progress on the faster backend (never "done early"; no partial data marked complete); storage card + availability legend byte-identical. Replay J-01 (`/stocks` scores), J-03 (unproven/noise marking), J-04 (Dashboard regime), J-05 (`/evidence` all-FAIL ledger), J-10 (deep-history chart), J-12 (universe/membership counts), J-13 (`/data` legend), J-15 (perf budgets / storage card + cold-path `/data`).
- **Unit/integration:** the byte-identity harness (`score_stocks` windowed vs unwindowed, ≥3 dates × full pool, 0 diff) is the primary correctness gate; `tests/test_bar_cache.py` byte-identical snapshots UNEDITED; scoring unit tests UNEDITED; forward-return backfill byte-identity; the warmup path exercises the cache-wrapped backfill. Run the TARGETED relevant suites — do NOT pin the full ~2 h 30-year pytest fixture as a hard mid-pipeline gate (iter-23 lesson); confirm the full green on an idle box as a deferred, non-blocking follow-up.
- **Error cases:** a member with fewer than `max_lookback_bars` bars scores byte-identically (short series returns whole series; NA propagation unchanged); a cadence date with 0 eligible members is an honest no-op, not a failure; forward-return no-lookahead holds (scoring ≤ as-of, forward returns > as-of).
- **Performance measurement:** same host, PROD mode (`start-backend.sh` / `start-frontend.sh` — not `dev.sh --reload`); baseline (window disabled) vs after (window enabled) over the SAME real deep-history cadence date/subset; peak RSS sampled and confirmed < 6144 MB.

## NOTES

- **Applied lessons (episodic memory):**
  - **iter-9** — for a backend refactor of a *shared value's computing module* (here `scoring:score_stocks`), the regression proof is NOT a browser pass: it is (a) the shared value's canonical output byte-identical (the harness) and (b) the module's existing default-path tests UNEDITED and green. If a scoring/bar-cache expectation test has to be edited to pass, that edit IS the regression signal — fix the window, do not re-baseline the test.
  - **iter-24** — a change near the prefill / cache path can OOM the process without touching the Python heap; a `/api/health` boot is a DIFFERENT code path and gives a false "cold path OK". The J-13/J-15 replay MUST include the cold-path `/data` repro (stop backend → cold start → load `/data` as the FIRST request, ≥2×) and confirm no OOM under 6144 MB.
  - **iter-23** + auto-memory ("30-year test suite slow, not the product") — the full 30-year pytest fixture is ~2 h (`123 passed in 7156 s`); pin targeted tests only, defer the full-suite green.
  - **iter-2 / iter-13 / iter-20** — never accept a QA/status.json "ready to ship" over an empty evidence dir or a CLOSURE-FAIL; trust the canonical browser-qa CONTENT + ux-regression + closure. `md5`-scan the evidence dir for reused/relabeled frames.
- **Operational preconditions before the browser lane:** `rm -rf apps/frontend/.next`; bring up BOTH prod-mode services and confirm HTTP-200 reachability BEFORE dispatching browser-qa (iter-20/21 lesson). Auto-memory: clear `/tmp/pytest-of-*` before each test phase (the 30-year pytest temp exhausts `/tmp` every ~2–3 phases; allow-rule is in `settings.local.json`).
- **Coherence:** iter-25 coherence-audit is COHERENCE-PASS; this iteration adds no Data Contract row and no nav-skeleton change, so the appended `blueprint.md` iter-26 paragraph needs no re-approval.
- **On GOAL_ACHIEVED:** even on a clean J-16 pass this iteration does NOT reach GOAL_ACHIEVED — J-02 / J-06 / J-07 / J-08 / J-09 remain sanctioned-partial (30-year all-FAIL ledgers; no staging winner clears divisor-8 today) and are the next, separate work per the evaluator's priority-2.
