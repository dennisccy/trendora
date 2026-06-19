# Goal Iteration 35 — Verify the regenerated dynamic point-in-time universe slides on /stocks (J-93) and the membership timeline (J-96)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 35
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** no
- **Target journeys:** J-93, J-96
- **Required-still-passing journeys:** J-06, J-18, J-07, J-94, J-08, J-15, J-85, J-87, J-88, J-89, J-90, J-91, J-92
- **Anti-goal reminders (verbatim from docs/goal.md):**
  - **No lookahead.** Scoring for a snapshot dated D MUST use only price bars with date ≤ D; forward returns MUST use only bars with date > D. The walk-forward MUST be unit-tested to prove no future bar influences an as-of score. *(critical)*
  - **Snapshots are immutable.** A persisted `scanner_run` and its result rows MUST never be updated or overwritten after creation; forward returns live in a separate append-only table keyed to the snapshot. A **wholesale regenerate-from-scratch of the entire snapshot set** (e.g. after a universe expansion — J-85) IS permitted as a deterministic, operator-triggered, confirm-gated **create-once rebuild** — every snapshot is cleared then recomputed reproducibly with strict no-lookahead — but an **existing snapshot MUST never be UPDATED or overwritten in place**, and the rebuild changes no canonical formula (only the universe membership it scans over). *(critical)*
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them. The same symbol's score MUST NOT differ between two views. *(critical)*
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request.
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey. (A sub-threshold / short-history name is excluded with a reason — never scored on padded values; an empty/small early universe shows n=0, never a fabricated membership.)
  - **the committed seed is never deletable** — `clear_snapshot_set` deletes only the snapshot layer, asserting `bars_before == bars_after`; the committed PRICE seed is never touched.
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code.
  - **Risk-Off must gate Actionable.** When the regime is Risk-Off, the scanner MUST mark zero stocks "Actionable" (watchlist-only). *(critical)*
  - **Exactly one date selector** — the single global as-of switcher stays the only date control; this iteration introduces NO second/page-local date state.
  - **Honest limitations surfaced.** Walk-forward / membership evidence MUST be labelled as carrying survivorship bias (current-constituent candidate pool); the warm-up boundary stated; breadth metrics labelled "universe-relative".

## GOAL

Confirm — on live, differential, rendered evidence — that after the (already-completed) J-85 regenerate-from-scratch rebuild, the `/stocks` leaderboard now serves D's point-in-time resolved universe (J-93: row count slides from 0 in the warm-up to ~495+ at a full date) and the `/data` membership timeline now shows a rising step function with populated entries/exits (J-96), with the J-06 single-source contract reconciled and no anti-goal regression.

## BACKGROUND

The iter-34 evaluator marked J-93 `failing` and J-96 `partial` for one shared, non-code reason: the per-date `universe_resolver` was integrated into `score_stocks` in iter-33 (proven correct, no-lookahead, COHERENCE-PASS), but `/stocks` and the J-96 timeline serve the IMMUTABLE persisted `ScannerResult` snapshots, which were last built by the iter-27 J-85 rebuild over the OLD static 122-member universe — so every as-of date showed a flat 122. The honest fix J-93's own acceptance names is the J-85 confirm-gated regenerate-from-scratch snapshot rebuild over the per-date membership. **That ~11h destructive rebuild has ALREADY been run and COMPLETED out-of-band by the operator** (job `eb48cbf1…`, plus a small backfill repair for transient SQLite-lock failures) BEFORE this iteration. The iter-35 dev step was therefore verification-only with an EMPTY source diff (`git diff HEAD -- apps/backend/app apps/frontend apps/backend/tests` is empty) and confirmed at the data layer that the store now slides (stored ScannerResult rows == served `/api/stocks` rows: 0 @2021-01-04 / 495 @2021-10-25 / 504 @2022-02-01 / 544 @2026-06-16; `scanner_runs` holds 1369 snapshot dates; `daily_prices` bar count 793,218 == the pre-rebuild backup, proving the committed seed was never touched; resolver-direct latest == 544 == served). Depth is **lean** (NOT full, superseding the iter-34 "full" recommendation): the rebuild — the only full-warranting action — is already done, the dev diff is empty, and there is no code/data-model change for the 11-step pipeline to add value over; the remaining work is purely a live browser-QA differential confirmation plus a required-still-passing re-verification.

## IN SCOPE

### Backend
- [ ] None. No source change. The persisted dynamic membership is already regenerated and correct; this iteration only VERIFIES it.

### Frontend (if applicable)
- [ ] None. No frontend change — the J-93/J-96 surfaces (`/stocks` leaderboard, `/data` membership timeline) already render the served data; only the underlying snapshot DATA changed (via the completed rebuild).

### New user-facing capability
The `/stocks` leaderboard and the `/data` membership timeline now reflect the genuine point-in-time universe: an early as-of date honestly shows zero/fewer scored names (the deterministic warm-up), and the membership grows to the full resolved set at later dates — the dynamic universe the J-93/J-94/J-96 cluster promised, now actually served end-to-end.

### New information displayed
Nothing structurally new is added. The EXISTING `/stocks` row set and the EXISTING `/data` membership-timeline step function + entries/exits now carry the correct, dynamic, as-of-dependent values instead of the stale flat 122.

### New user actions
None.

### UI surface changes
None (no markup change). Existing surfaces: `/stocks` leaderboard (and `/themes`, `/sectors`, `/scanner-runs`, which read the same per-date snapshots), the `/data` Data Manager membership-timeline + per-date coverage-diagnostic panels.

### Product surface delta
The product becomes internally consistent: the J-94 per-date coverage diagnostic (~544 admitted at latest), the resolver-direct count, and the served `/stocks` membership now AGREE — closing the iter-34 inconsistency where the diagnostic said 544 while `/stocks` served 122.

### Blueprint conformance
No new surfaces. J-93 lives on the existing **Stocks** home (`/stocks`, and the same per-date snapshots feed `/themes` / `/sectors` / `/scanner-runs`); J-96 lives on the existing **Data Manager** coverage home (`/data`). Both are already registered in `blueprint.md` Information Architecture (the `Stocks` and `Data Manager` nodes carry the `J-93/J-94 [TARGET iter-33]` and `J-94 … J-96 … [TARGET iter-33]` annotations). No nav-skeleton change; no `blueprint.reapproval-requested` written.

### Data-contract additions
None. Every value this iteration verifies is already registered in `blueprint.md` Data Contract:
- "Universe membership + selection screen" → `universe_resolver` (the PRIMARY universe path) → the scored `ScannerResult` rows ARE the persisted membership; `universe_count` already migrated to as-of-dependence (`members-resolved-at-D`).
- "J-96 — Dynamic-universe membership timeline" → `data_manager._membership_timeline` → `compute_coverage` → the additive `membership_timeline` field on `GET /api/data`.
This iteration introduces NO new value and NO second computation/endpoint — it reads the single canonical source. The J-06 single-source contract is the load-bearing check: the resolver-direct count, the J-94 diagnostic admitted count, and the served `/stocks` membership must reconcile.

## OUT OF SCOPE

- **Triggering ANY `kind:"rebuild"` (or any destructive `/data` regenerate/clear/remove action).** The J-85 confirm-gated regenerate-from-scratch rebuild is ~11h, CLEARS the snapshot layer (~1370 daily snapshots), and is ALREADY COMPLETE — it is a finished prerequisite, NOT pending work. Browser-QA and dev MUST NOT re-trigger it; verification is strictly read-only. (A DB backup exists at `apps/backend/data/trendora.db.pre-iter35-rebuild.bak`.)
- Any code change to `universe_resolver.py`, `scoring.py`, `forward_testing.py`, the `/data` coverage producer, or any frontend component — the resolver is correct and the data is regenerated; no fix is expected.
- The J-95 real backward-history fetch and the true point-in-time index-constituent feed (data-walled, honest blocked-NA, non-halting).
- J-22 / J-23 / J-24 (data-walled, non-vetoing).
- Manufacturing any further work beyond closing J-93/J-96 — these are the last two non-passing buildable journeys.

## DEFINITION OF DONE

- [ ] **J-93 passes** via browser-qa-agent on GENUINE DIFFERENTIAL evidence: at least TWO byte-DISTINCT (md5-distinct) `/stocks` frames at different as-of dates showing DIFFERENT row counts — an early/warm-up date (e.g. 2021-01-04, well before the ~2021-10-18 boundary) showing 0 scored names (honest empty, never padded) vs a full date (e.g. 2022-02-01) showing ~495–504 rows. The captured row count MUST match the live `GET /api/stocks?as_of=` count, not contradict it.
- [ ] **J-96 passes** via browser-qa-agent: the `/data` membership-timeline step function is scrolled INTO the viewport and VIEWED rising from ~0 at the warm-up start to ~495+ at a full date (NOT a flat 122 line), with Entries/Exits populated (not all "—") and all three honesty labels rendered verbatim (pool survivorship-bias, warm-up boundary, universe-relative breadth).
- [ ] **J-06 single-source reconciliation** confirmed SAME-INSTANT: the resolver-direct count (`universe_resolver.resolve_members` at latest ≈ 544), the J-94 `/data` per-date coverage-diagnostic admitted count, and the served `/stocks` count at the same as-of agree (within the documented stocks-only-vs-benchmark distinction); a single ticker (e.g. NVDA) shows identical leadership/entry/risk scores on the `/stocks` list and the `/stocks/NVDA` detail.
- [ ] Required-still-passing journeys remain green (live smoke): J-18 (CRITICAL — 0 `input[type=date]` on /backtest, single global switcher), J-07 (CRITICAL — a Risk-Off run shows 0 Actionable), J-08/J-15/J-85 (immutable run history + snapshot-served reads + the rebuild panel still confirm-gated and NOT triggered), J-87/J-88/J-89/J-90/J-91/J-92 (regime / market-phase / ETF / research machinery is stocks-only-exempt and must be unperturbed by the rebuild), J-94 (the diagnostic the reconciliation reads).
- [ ] No anti-goal violation introduced (no lookahead, snapshots immutable, single source, no fabricated early membership, committed seed intact, Risk-Off gate holds, exactly one date selector).
- [ ] The source diff stays EMPTY (this is a data-verification iteration); confirm `git diff HEAD -- apps/backend/app apps/frontend apps/backend/tests` is empty.
- [ ] Full backend suite re-run nohup-async (handed to the pump); GOAL_ACHIEVED candidacy gates on the FLUSHED `0 failed` / `PYTEST_EXIT=0` line, NEVER blocking the evaluator on the in-flight suite (iter-11/29/30). Re-run any single `test_warmup.py` / `test_data_manager_jobs_pipeline.py` / `scanner_runs`-touching `F` in isolation before attributing a regression (documented slow-boot / warm-up-contention flake).
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-35-dev.md` (already present — verification-only, no fix).

## TESTING REQUIREMENTS

- **Browser (named journeys, by ID):**
  - **J-93** — step the single global as-of from an EARLY warm-up date (≤ ~2021-10-15) to a FULL date (~2022-02-01) and capture two byte-DISTINCT `/stocks` frames with DIFFERENT row counts (0 → ~495+); confirm the count matches `GET /api/stocks?as_of=` live; confirm the early date is honestly empty (no fabricated rows).
  - **J-96** — scroll the `/data` membership-timeline below-the-fold panel into the viewport and VIEW the pixels: rising step function (not flat 122), populated Entries/Exits, and the three honesty labels verbatim. Reject any empty-skeleton / flat-line / coverage-table-mislabelled frame (iter-18/33 precedent).
  - **Required-still-passing smoke:** J-06 (NVDA leaderboard == detail at a full-universe date + count reconciliation), J-18 (CRITICAL, 0 date inputs), J-07 (CRITICAL, Risk-Off → 0 Actionable), J-85 (rebuild panel render-only, NOT triggered), J-87/J-88 (Dashboard market-phase panel unchanged at a same date), J-08 (scanner-runs history), J-94 (coverage diagnostic).
- **Unit/integration:** No new tests (empty diff). Re-confirm the existing keystone tests stay green on the rebuilt DB: `tests/test_universe_resolver.py` + `tests/test_no_magic_numbers.py` (resolver causality / tail-invariance / no-magic-number) and `tests/test_iter27_rebuild_mdd.py` (whole-row snapshot clear never touches `daily_prices`, `bars_before == bars_after` seed-safety, deterministic create-once, no in-place UPDATE). Then the full suite to `PYTEST_EXIT=0` nohup-async.
- **Error cases / invariants to re-assert (read-only):** an early as-of (before the warm-up boundary) yields an honestly EMPTY stock universe (n=0), never a fabricated membership or a padded 0%; the resolver admits a name only on the first date it clears price + ADV + ≥200-bar history (strictly causal, ≤ D only); a Risk-Off snapshot still marks zero Actionable; the committed price seed bar count is unchanged from the backup.

## NOTES

- **Grounding (verified this planning step):** the dev handoff and the persisted-store probe confirm the membership SLIDES (stored ScannerResult rows == served `/api/stocks` rows = 0/495/504/544; warm-up last-empty 2021-10-15, first-populated 2021-10-18; `daily_prices` 793,218 == pre-rebuild backup; resolver-direct latest == 544 == served). The live HTTP endpoint was non-responsive (HTTP 000, ports :8835/:3835/:9222 not listening) during this planning step because the full backend suite was running concurrently and the env was not up — this is the documented load/contention condition (iter-32 J-94 timeout; iter-30/33 env-down), NOT a defect. **The browser-qa step MUST bring the env up first** (backend :8835 + frontend :3835 + Chrome :9222) and confirm reachability before scoring; per the iter-17/25 lesson a UI journey CANNOT be upgraded to passing without live rendered evidence, so if Chrome :9222 is unreachable the browser-qa-agent should fall back to Playwright (as it successfully did in iter-34) rather than hard-SKIP.
- **THE REBUILD IS DONE — DO NOT RE-RUN IT.** Per MEMORY.md and the iter-34 evaluator, a `kind:"rebuild"` is ~11h, destructive (clears ~1370 snapshots), and operator-gated. It has already completed for this fix. Any agent that re-triggers it causes data loss and an ~11h disruption for zero benefit. Verification is strictly read-only against the already-regenerated DB.
- **Lesson applied (iter-34, episodic memory):** "A backend feature can be built, unit-correct, and coherence-clean yet still FAIL its user-facing acceptance because the persisted snapshot layer it feeds was never regenerated … the fix is not code — it is running the J-85 rebuild … assert the ROW COUNT / step-function actually changes with the as-of, and reconcile a direct-resolver diagnostic against the served stored membership." This iteration is exactly the post-rebuild verification that closes that gap. The "two byte-distinct frames" guard is insufficient by itself — the two frames must show DIFFERENT ROW COUNTS.
- **Lesson applied (iter-33):** a QA report can claim "PASS" on hollow evidence (byte-identical J-93 frames, an empty-skeleton `/data` frame). md5sum the evidence dir FIRST; open every cited frame; a differential journey REQUIRES two byte-distinct frames with different counts, and a below-the-fold `/data` panel must be scrolled into view and the rendered pixels viewed (iter-18: the membership timeline / heatmap sits below the fold).
- **Lesson applied (iter-11/29/30):** never block the goal-evaluator on the in-flight full suite; hand it to the pump nohup-async and gate GOAL_ACHIEVED candidacy on the flushed `0 failed` line; re-run a single `test_warmup.py` / jobs-pipeline `F` in isolation before calling it a regression (the iter-34 EXIT=1 was the documented warm-up single-flight contention flake on a byte-unchanged backend).
- **Why lean, not full (supersedes the iter-34 recommendation):** the iter-34 evaluator recommended `full` because triggering + verifying the rebuild touches the snapshot/scanner determinism surface. The rebuild has since been completed out-of-band and the iter-35 dev diff is empty — there is no code or data-model change left for the 11-step pipeline to add value over, so the correct cycle is lean (developer no-op → reviewer → browser-qa). The determinism/immutability surface is still re-asserted via the `test_iter27_rebuild_mdd.py` + resolver tests and the full-suite gate.
- **Path to GOAL_ACHIEVED:** if J-93 flips `failing → passing` and J-96 flips `partial → passing` on genuine live differential evidence, the J-06 reconciliation holds, the required-still-passing journeys stay green, and the full suite flushes `0 failed`, then every buildable Must-have (J-01..J-21, J-25..J-96) is passing and only J-22/J-23/J-24 (+ the J-95 real-fetch / constituent-feed legs) stay honestly blocked-NA (non-vetoing per goal.md) — the next evaluation is a GOAL_ACHIEVED candidate. This iteration plans no further work beyond closing J-93/J-96.
