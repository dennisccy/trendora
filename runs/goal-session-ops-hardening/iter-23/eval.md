# Iteration 23 Evaluation

**Verdict:** GOAL_ACHIEVED
**Depth Recommendation For Next Iteration:** lean

## Summary

A zero-product-diff closeout that actually closed what it targeted. The two agent-tractable findings from
iter-22's second-key CONFIRM reject are gone: the session demo manifest `demo.sh ops-hardening
--session-live` really reads now carries five `[NEW]`-flagged, verified steps for J-06/J-07/J-08 (it had
zero), purely additive (60 insertions, 0 deletions, existing 7 steps byte-unchanged); and J-06's golden
script's undisclosed `default_timeout_ms` 8000→18000 loosening is reverted to 8000 after an investigation I
re-derived myself from the database and `logs/backend.log`. The third finding was already fixed by the
operator (`reports/perf-budgets.md:3714`). All 7 Must-have journeys are `passing` with this-iteration
evidence, all 7 `spec_hash`es match `goal_gate hash-journeys`, coherence is COHERENCE-PASS, the diff scan is
CLEAN, and zero anti-goal violations are unresolved.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 | passing | passing (re-verified) | `reports/phase-goal-ops-hardening-iter-23-ui-test-results.md` UT-J-01 PASS · `reports/qa/goal-ops-hardening-iter-23-evidence/J-01-verify.png` (evaluator opened: /data landing, Ready badge, 1996-01-02 → 2026-07-22, universe 540) |
| J-03 | passing | passing (re-verified) | UT-J-03 PASS · `J-03-verify.png` (expect `412 calendar days`) |
| J-04 | passing | passing (re-verified) | UT-J-04 PASS · `J-04-verify.png` (expects `provider: seed`, `Run history`); live non-blocking restart via `scripts/start-backend.sh` this dispatch, readiness `ready` / warmup 89/89 |
| J-05 | passing | passing (re-verified) | UT-J-05 PASS · `J-05-verify.png` (evaluator opened: "Immutable snapshot — as of 2025-05-15 … never recomputed for today") |
| J-06 | passing | passing (re-verified, 2 gaps closed) | UT-J-06 PASS (LLM lane, 11/11 pages, every expect verbatim) · `J-06-backtest-fullpage.png`, `J-06-research-event-study-fullpage.png` · replay re-pass at the restored 8000 ms, slowest step 2098.60 ms (`runs/goal-ops-hardening-iter-23/j06-replay-timed.csv`) · demo step `n=8` |
| J-07 | passing | passing (re-verified, walkthrough gap closed) | UT-J-07 PASS · fresh 26.80 s BCW, HTTP 200 / readiness `ready` throughout, VmPeak flat 4,974,536 kB (20.9 % headroom under the 6144 MB cap) · `J-08-refreshing-2026-07-08-viewport.png` (top bar reads `Ready`) · demo step `n=9` |
| J-08 | passing | passing (re-verified, walkthrough gap closed) | UT-J-08 PASS · `J-08-refreshing-2026-07-08-domtext.md:106-110` (banner) + `J-08-ready-after-warm-2026-07-08.png` (evaluator opened: banner gone, own evidence) · demo steps `n=10/11/12` |

**Nothing I inherited.** Load-bearing facts I re-derived personally:

- **The J-06 timeout revert is justified.** I queried `forward_aggregate_cache` directly: the only
  background-compute window anywhere near the undisclosed 08:41-local edit is the 2026-07-20 one committing
  `07:31:59.453030 → 07:32:56.164427` UTC, and **no row exists between 07:32:56 and 09:27:55** — nothing
  overlapped. `logs/backend.log:77525/77533` then show J-06's own `/backtest` step at `07:41:21.653184Z`
  and `07:41:21.948696Z` at `total_ms=30.64` / `44.65`. There was never a basis for 18000 ms.
- **The J-07 demo figures are the true measurement.** I re-tallied
  `runs/goal-ops-hardening-iter-22/bcw-measure.csv` myself: 29 rows, 29/29 HTTP 200, `bt_latency_s` max
  **7.1191** exactly, `hp_latency_s` max **0.253**, `vmpeak_kb` flat **2,631,612**, readiness `ready` in
  every sample, 0 breaches of the amended 8.0 s / 2.0 s BCW ceilings.
- **This iteration's BCW was real.** `forward_aggregate_cache` shows asof `2026-07-08` horizons 20 and 60
  committing at `09:27:55.910616` and `09:28:08.836658` UTC — matching the QA timeline to the microsecond,
  with horizons 1/5/10 pre-dating it (06:44–06:50), i.e. a genuinely incomplete 3/5 start state.
- **An apparent AG-3 discrepancy, resolved on the merits rather than waved through.** The refreshing banner
  read "evidence as of 2026-07-08, generated 2026-07-24 16:54:54", yet **no such row exists in the DB
  today** — which looks like a fabricated timestamp until you read `forward_testing.py:1135-1156`: the
  iter-16 cutover contract deletes the prior `dataset_version`'s rows for an `asof_key` at the exact moment
  the current version becomes complete. The served payload was real and complete when served and was
  legitimately pruned by the 09:28:08 horizon-60 write. That is also affirmative proof of J-08's "never
  mixes versions" clause and of AG-5 (same-key, older generation — never a newer as-of).
- **`--session-live` reads the file that was fixed.** `demo-phase.sh:78` sets
  `DEMO_JSON_OUT="reports/goal-session-${SID}-demo.json"`; `demo_runner.py:1076/1094` treats `session-live`
  as a live browser mode. The manifest now has J-06×1, J-07×1, J-08×3 steps, all `new: true` /
  `verified: true`, 8/8 `highlights` at the cap, valid strict JSON, every required key present.

## Anti-goal Check

Basis: `iter-23/scan-report.md` (**CLEAN**), `iter-23/iter-diff.md` (**"(no changes)"**), plus my own
`git diff HEAD --stat` (6 files: `demo.json` +60/−0, `J-06.json` one line, and 4 harness/bookkeeping files)
and `git status --porcelain` (untracked = handoff/spec/review/evidence/run-tracking only). `git diff HEAD --
apps/` and `git status --porcelain -- apps/` are both **empty**.

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 proven-language | OK | No product change; no displayed value added. I read all 5 new narrations — no proven/edge/confidence claim appears. |
| AG-2 decision-quality only | OK | No return promise, price target, buy/sell signal or order simulation in the new narration; UI untouched. |
| AG-3 displayed numbers correct | OK | The two re-verified J-06 assertions (`$304.89` invalidation level, `"Setup & Pattern event study"` heading) confirmed live by developer (API + HTML), reviewer (Playwright) and browser-qa (Chrome MCP DOM). The demo's cited figures match the raw CSV exactly (my own tally). The one apparent mismatch — a served `generated_at` with no surviving row — is explained by the cutover pruning at `forward_testing.py:1135-1156`, not by fabrication. |
| AG-4 no overfit edges | OK | No evidence claim introduced; the referee gate is untouched. |
| AG-5 no lookahead | OK | Zero compute diff. Positively evidenced: the fallback served the same `asof_key` at an OLDER generation, and the post-warm page renders 20d/60d as `— n=0` because those windows have not elapsed against the seed max 2026-07-22. |
| AG-6 referee gate | OK | No evidence-derived claims this iteration (goal.md Loop mechanics: J-01…J-06 carry none). |
| AG-7 no hard-coded credentials | OK | scan-report CLEAN; I additionally grepped the new untracked scripts (`runs/goal-ops-hardening-iter-23/*.py`, `*.sh`) for key/secret/token/password/bearer patterns — zero hits. |
| AG-8 resilience / no unbounded loads | OK | Zero product diff, so no new load path. Observed and disclosed below: two auxiliary panels degraded to honest placeholders during the BCW — which is the *required* AG-8 shape (contained boundary, never a blank application-error page), not a violation. B-1107 (multi-BCW memory risk) stays owner-backlogged, unchanged. |
| AG-9 offline-deterministic ingest | OK | No backfill/fetch/rebuild job was submitted. The BCW was triggered by *viewing* an incomplete historical date (the existing lazy dispatch). Every capture's top bar reads `provider: seed`. No manifest/dependency file changed. |
| AG-10 host resource ceiling | OK | One backend restart, via `scripts/start-backend.sh` only. Caps `/proc`-verified live on PID 1134166: `Max address space 6442450944` (= 6144 MB), `Cpus_allowed_list 0-3,8-11`, `MALLOC_ARENA_MAX=2`, `OMP/OPENBLAS_NUM_THREADS=4`. Zero `scripts/` paths in the diff, so no launcher could have been weakened. |
| Licenses / paid SaaS | OK | No LICENSE, `package.json`, `requirements*.txt` or `pyproject.toml` appears in the diff or in `git status`. |

**Coherence:** `iter-23/coherence.md` = **COHERENCE-PASS** (no blocking violation; one advisory citation-precision nit). No structural veto.
**Goal-edit drift:** no `journeys-changed.md`; all 7 `spec_hash`es equal the current `goal_gate hash-journeys` output.
**Pipeline health:** review `PASS_WITH_NOTES` (one MINOR), browser QA `PASS` 7/7, replay 4/4 — no fail-open signal.

## Things I state plainly rather than round away

1. **One cosmetic citation nit is still open, and I chose not to spawn an iteration for it.** Demo step
   `n=9` cites "7.1191 s" / "0.2530 s"; `perf-budgets.md:3630` prints "7.119 s" / "0.253 s". The reviewer
   flagged it MINOR against TC-2's "verbatim in perf-budgets.md" wording. Two facts decide it: the iteration
   spec's *own* BACKGROUND (line 114) instructed exactly those 4-decimal figures, and they are **exact**
   against the source-of-truth `bcw-measure.csv` the spec named (max `bt_latency_s` = 7.1191, max
   `hp_latency_s` = 0.253). Same single measurement, higher precision — not a second source and not the
   "28.06 s" failure mode. Trimming to 3 decimals is a good follow-up; it is not a goal blocker.
2. **J-07's evidence this iteration is thinner than iter-22's, and the QA agent said so itself.** There is
   no dense per-second sample series inside this iteration's own 26.80 s window (the poller launched after
   the window closed), and step 4 (induced memory-pressure abort) was not re-triggered. Both still rest on
   iter-22's 29-sample measurement and its organic `MemoryError` episode. I accept that because the product
   code is byte-identical since, and I re-derived the iter-22 numbers myself.
3. **New observation: during the BCW, two auxiliary panels degraded.** The refreshing capture shows "Scan
   summary unavailable for this date — the dashboard endpoint did not respond" and "Stock data
   unavailable"; both render correctly post-warm. That copy is pre-existing product code
   (`apps/frontend/app/backtest/page.tsx:335-345`, untouched this iteration), so it is a transient runtime
   condition, not a code change — and it is exactly AG-8's and J-06's honest-degradation requirement rather
   than a breach. It is the first time this session's evidence records it; worth a look, not a blocker.
4. **`J-01/J-03/J-04-verify.png` are byte-identical to each other** (md5 `7d8f6681`, also matching iter-22's
   `J-01-verify.png`). Cause verified, not assumed: all three scripts END on `/data`, so the final viewport
   frame is the same deterministic page-top. The gate is the scripted DOM expects, which ARE distinct
   (`no new snapshots` / `412 calendar days` / `Run history`). Framework note, recurring since iter-16.
5. **The demo manifest's J-08 "refreshing" step will not render a refreshing banner at an arbitrary future
   playback**, because that date's compute has since completed and the state is not reproducible without a
   fresh version bump. The developer disclosed this and wrote the step's `point_out` in the past tense with
   a robust `expect` (`expanding window`, true in both states). Logged in `assumptions.md`.

## Next-Step Recommendation

**HALT — goal achieved (first key).** The deterministic gates and the second fresh-context CONFIRM run next.
Nothing blocking remains. Non-blocking follow-ups, in priority order, if the loop re-opens (LEAN suffices —
every item is zero-product-diff except #3):
1. Trim demo step `n=9`'s "7.1191 s" / "0.2530 s" to "7.119 s" / "0.253 s" (reviewer's MINOR; one-line edit).
2. Capture replay evidence at the *asserting* step or element-scoped, so `J-01/J-03/J-04-verify.png` stop
   being one image (framework, recurring since iter-16).
3. OWNER, optional: backlog card B-1107 (global dispatch cap for concurrent BCWs) — the one item that would
   re-open the goal if AG-8's "exhaust a service's memory" is read literally; see `assumptions.md` iter-22.
4. Carried, unaffected: retarget `test_forward_testing_serving_split.py`'s four `is_latest` monkeypatches
   BEFORE removing the dangling imports at `backtest.py:75` / `mcp/tools.py:38`; run `test_api_backtest.py`
   TC-11 + `test_data_manager.py` heavy fixtures off the constrained box.
5. Investigate why the backend was found DOWN at this dispatch's start with no crash traceback in
   `logs/backend.log` (developer's Known Issues). Not journey-affecting — J-04's restart path handled it —
   but an unexplained stop deserves a look.

## Halt Justification

`GOAL_ACHIEVED` per decision tree C.3, reached only after C.1 and C.2 were tested and rejected:

- **Rejected REGRESSION (C.1):** no journey moved `passing`/`already_passing` → `failing`; the diff contains
  zero `apps/` paths by two independent baselines, so no product behaviour could have moved; zero unresolved
  anti-goal violations (9 historical, all `resolved: true`). The single J-06.json change is a *tightening*
  (18000 → 8000 ms) that the replay then passed with 74 % margin.
- **Rejected STALLED (C.2):** there is no blocker. The human-owned decision that drove the iter-20/21 halts
  (the budget amendment) is settled and committed, and the two findings this iteration owned were both
  agent-tractable and are both closed with cited evidence I re-derived.
- **Rejected ESCALATE (C.4):** review is `PASS_WITH_NOTES` with browser results present — no fail-open; no
  journey failed twice; the lean iteration surfaced no cross-cutting ambiguity.
- **Rejected CONTINUE (C.5):** the only work I can identify is one cosmetic decimal trim, one framework
  screenshot-capture improvement, and owner-owned optional items. Manufacturing an iteration for those is
  precisely the "vague acceptance criteria → infinite loop" anti-pattern.
- **C.3 satisfied:** all 7 Must-have journeys `passing` with this-iteration evidence I personally opened or
  re-derived; `coherence.md` = COHERENCE-PASS; no `journeys-changed.md`; all 7 `spec_hash`es match the
  current `docs/goal.md` (verified with `goal_gate.py hash-journeys`, exact match on every journey).

This is the first key. The second fresh-context CONFIRM evaluator should re-examine, in particular, item 1
and item 2 of "Things I state plainly" — those are where I exercised judgment rather than read a number.
