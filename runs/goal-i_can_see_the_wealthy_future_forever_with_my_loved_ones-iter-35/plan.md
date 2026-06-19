# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-35 Execution Plan

## Context (read before acting)
This is a **data-regeneration / verification** iteration, NOT source-code work. J-93 (`failing`)
and J-96 (`partial`) share ONE non-code root cause: the per-date `universe_resolver` was integrated
into `score_stocks` in iter-33 (proven correct, no-lookahead, COHERENCE-PASS), but `/stocks` and the
J-96 timeline serve the IMMUTABLE persisted `ScannerResult` snapshots, which were last built by the
**iter-27** rebuild over the OLD static 122-member universe. The honest fix named by the J-93/J-96
acceptance is the J-85 confirm-gated regenerate-from-scratch rebuild over the per-date membership.

**The J-85 rebuild has ALREADY been run and COMPLETED by the operator/pump** (job `eb48cbf1`,
1369/1369 dates after a 3-date backfill repair). This was verified live during planning:
`GET /api/stocks?as_of=` returns **0 rows @ 2021-01-04, 495 @ 2021-10-25, 504 @ 2022-02-01,
544 @ 2026-06-16** — the dynamic universe now slides. So the rebuild is a **COMPLETED PREREQUISITE**.
This plan does **NOT** call for triggering another `kind:"rebuild"` (never a casual action — ~11h,
clears ~1370 snapshots; MEMORY.md). The remaining work is verification only.

## What to Build
- **Nothing new to build.** No source code change, no frontend change, no new endpoint/column/table/config.
  The resolver, scoring repoint, forward-return repoint, `universe_count`-contract migration, J-94
  diagnostic, J-96 timeline, and J-85 rebuild orchestration all landed in iter-33 and are unit-correct.
- **Verify the completed rebuild persisted the dynamic per-date universe** end-to-end so J-93 flips
  `failing → passing` and J-96 flips `partial → passing` on live differential evidence.
- **Conditional, non-speculative fix only:** if (and only if) verification reveals a genuine
  orchestration bug (resolver not consulted per-date inside the rebuild's `_do_backfill`/`score_stocks`
  path; a per-date persist crash), apply a minimal fix + add the matching regression test that drives the
  REAL rebuild orchestration entry point (not a hand-rolled stand-in — iter-15 lesson). Do NOT plan code
  changes speculatively — verify first. Live probe already indicates the persisted data is correct, so
  no code change is expected.

## Agents Required
- **backend-data: no** — no backend source change is expected (rebuild already complete, resolver/scoring
  unit-correct in iter-33). Engaged ONLY if verification surfaces a real orchestration bug (then minimal
  fix + regression test). The developer step's primary job is verification + the dev handoff, not coding.
- **frontend-ux: no** — zero frontend diff. `/stocks`, the `/data` J-96 timeline + J-94 diagnostic, and
  every other affected surface already render; the gap was purely the stored snapshot data they read.

## Frontend Present: yes
(Browser checks ARE required. J-93 and J-96 acceptance mandate LIVE browser-qa-agent differential
evidence — two byte-DISTINCT `/stocks` frames with DIFFERENT row counts, and the `/data` membership
timeline rendered into the viewport. The iteration changes user-facing DATA on existing pages even
though there is no frontend code diff, so this is `yes` per the "any user-facing data change ⇒ yes" rule.
This intentionally overrides the spec's metadata line `Frontend Present: no`, which contradicts its own
Definition-of-Done requiring live browser evidence for J-93/J-96 — see Scope Notes.)

## Files to Create/Modify
- `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-35-dev.md` -- dev handoff:
  records the rebuild is a completed prerequisite, the seed-safety + differential verification evidence,
  the targeted-test GREEN results, and that the backend source diff is empty.
- `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-35-test.log` -- nohup-async
  full backend suite log, terminated by a `PYTEST_EXIT=<code>` flush line.
- `reports/phase-goal-...-iter-35-ui-test-results.md` (browser-qa-agent) -- live J-93/J-96 differential
  evidence + required-still-passing live smoke.
- (Only IF a real orchestration bug is found) a minimal source fix under `apps/backend/app/engine/` or
  `apps/backend/app/engine/data_manager.py` + a regression test driving the real rebuild entry point.
  **Not expected.**

## UI Evolution
- New user-facing capability: stepping the single global as-of across the seed window now makes the scored
  stock universe on `/stocks` (and Themes / Sectors / Scanner-Runs / Backtest evidence / Research) actually
  **SLIDE** — honestly empty/very-small before the ~2021-10-18 warm-up boundary, rising to full (~495–544)
  from ~2022-01, reflecting D's point-in-time membership. (Capability already coded; now truthful in the
  served data.)
- New information displayed: none NEW. The same J-96 membership-timeline step function, SIZE / Entries /
  Exits / Excl. columns, and J-94 per-date coverage diagnostic now display the REAL dynamic membership
  instead of a flat 122. The J-93 `/stocks` row count now varies with the as-of date.
- New user actions: none. The confirm-gated "Rebuild snapshots for the current universe" control (J-85)
  already exists and was EXECUTED once (operator-confirmed) before this iteration; no affordance is added.
- UI surface changes: none (no frontend diff). Affected surfaces — `/stocks`, `/data` (J-96 timeline +
  J-94 diagnostic), and incidentally Themes / Sectors / Scanner-Runs / Backtest / Research — all already
  built; their served data changed after the rebuild.
- Navigation changes: none.

## Visual Requirements
- No new components or layout. All affected pages already use the existing component patterns (Stocks
  leaderboard table on `/stocks`, the Data Manager coverage/timeline panels on `/data`). No new visual
  effects. States to confirm during QA: the honest EMPTY state on `/stocks` at an early date (n=0, never
  padded), and the populated step-function / entries-exits state on the `/data` timeline at a full date.

## Operational Note (rebuild = completed prerequisite)
- Do **NOT** trigger another `kind:"rebuild"`. It is destructive (~11h, clears ~1370 snapshots; MEMORY.md)
  and is already done (job `eb48cbf1`, 1369/1369 dates).
- Seed-safety to CONFIRM (not re-run): the rebuild's `clear_snapshot_set` returned `bars_before == bars_after`
  and the committed `daily_prices` seed row count is unchanged. This is asserted by the existing
  `test_iter27_rebuild_mdd.py` suite + can be spot-checked against the job record / DB.
- Live env precondition for browser QA: confirm `:8835` (backend, up — returned the differential counts),
  `:3835` (frontend — currently DOWN, must be brought up by port, never broad `pkill`), and `:9222`
  (Chrome DevTools) reachable BEFORE scoring; backend needs `CORS_ORIGINS` incl. `:3835`. Fall back to
  Playwright if Chrome MCP CDP times out (iter-34 precedent) — do NOT hard-SKIP a target journey, or it
  stays stuck `partial`/`failing` (iter-17/25/30 lesson).

## Key Test Scenarios
- **J-93 (must flip failing → passing) — GENUINE DIFFERENTIAL:** md5sum the evidence dir FIRST; capture TWO
  byte-DISTINCT `/stocks` frames with DIFFERENT row counts — an early date before the ~2021-10-18 warm-up
  (e.g. 2021-01-04) showing the honest empty/very-small universe, and a full date (e.g. 2022-02-01 or latest)
  showing full membership (~495–544). REJECT byte-identical frames (the iter-33/34 trap, md5 ae9c2e38).
- **J-96 (must flip partial → passing):** scroll the below-the-fold `/data` membership-timeline panel into
  the viewport and VIEW the pixels — the step function RISES from the warm-up boundary (no longer flat 122),
  the SIZE column varies by date, Entries/Exits are populated (not all "—"), and the THREE honesty labels
  (survivorship / warm-up / universe-relative) remain verbatim. A blank/skeleton or flat-122 frame is rejected.
- **J-06 reconciliation (now critical):** the J-94 diagnostic admitted count at latest and the snapshot-served
  `/stocks` row count AGREE at the same instant (within the documented benchmark-vs-stocks-only distinction);
  NVDA Leadership/Entry/Risk identical on `/stocks` list and `/stocks/NVDA` detail.
- **Required-still-passing (live smoke, must stay green):** J-18 (CRITICAL — 0 `input[type=date]`, single
  global switcher, no second date state), J-07 (CRITICAL — a Risk-Off date → 0 Actionable), J-08/J-15/J-85
  (immutability + snapshot-served reads; rebuild panel render-only), J-87/J-88/J-89/J-90/J-91/J-92 (regime /
  ETF / market-phase machinery is stocks-only-exempt and must be unperturbed by the rebuild), J-36/J-37/J-39.
  Resolve any sort/control by `aria-label`, never visible `text()` (iter-27/28).
- **Unit/integration (re-run GREEN):** `test_iter27_rebuild_mdd.py` (13 tests — whole-row clear never touches
  `daily_prices`; `bars_before == bars_after` seed-safety; deterministic create-once; no in-place UPDATE),
  the 14 `universe_resolver` tests (tail-invariance / warm-up / excluded-by-reason), `test_no_magic_numbers`,
  no-lookahead. If the rebuild revealed the resolver is not consulted per-date, add a regression test driving
  the REAL rebuild orchestration entry point asserting persisted per-date `ScannerResult` sizes vary
  (empty early → full ~2022-01) — NOT expected given the live probe.
- **Anti-goal guards (must NOT be violated):** no in-place snapshot UPDATE (create-once only), strict
  no-lookahead preserved, committed seed never deleted, no fabricated early membership.
- **Full backend suite:** re-run to `0 failed, EXIT 0`. Hand to the pump `nohup`-async; gate the next
  evaluator on the FLUSHED `0 failed, EXIT 0` line, NEVER block the evaluator on the in-flight suite
  (iter-11/29 lesson). Re-run any single `F` in `test_warmup.py` / `test_data_manager_jobs_pipeline.py` /
  a `scanner_runs`-touching module IN ISOLATION on a quiet host before attributing it to this iteration
  (documented slow-boot / warm-up-contention flake — iter-30/34).

## Scope Notes / Flags
- **Spec metadata vs DoD contradiction (flagged):** the spec header says `Frontend Present: no`, but its
  own Definition of Done and Testing Requirements mandate LIVE browser-qa-agent differential evidence for
  J-93 and J-96. This plan sets `Frontend Present: yes` so the browser gate actually runs — a backend-only
  `no` would skip the very evidence the iteration requires. This is consistent with the orchestrator rule
  "If the phase adds any user-facing data or capability, Frontend Present MUST be yes."
- **Out of scope (excluded):** any frontend change; any new endpoint/stored column/config section/table;
  any change to resolver/scoring/forward-return formulas (iter-33, proven correct); the J-95 REAL
  backward-history fetch + the true point-in-time index-constituent feed (data-walled, honestly
  blocked-NA / non-vetoing — J-95 stays `passing` on its buildable render-only legs, must not regress);
  J-22/J-23/J-24 (data-walled, non-vetoing, unchanged); re-committing the regenerated snapshots into the
  optional Capability-34 snapshot seed.
- **GOAL_ACHIEVED candidacy (evaluator's call, not this plan's):** after J-93 and J-96 close green on LIVE
  differential evidence, J-06 reconciliation holds, the full suite flushes `0 failed, EXIT 0`, zero
  regressions, and COHERENCE-PASS, EVERY buildable Must-have (J-01..J-21, J-25..J-96) is passing — with
  J-22/J-23/J-24 and the J-95 real-fetch/constituent-feed legs honestly blocked-NA (non-vetoing).
