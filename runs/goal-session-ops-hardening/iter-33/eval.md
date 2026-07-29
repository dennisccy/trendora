# Iteration 33 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

A journey moved forward for the first time in five iterations. J-06 "Pages load only what they
need" is now passing. The launcher script that starts the web app had always started it in
"development" mode while every document called it "production" mode; this iteration fixed that,
and then measured all 11 pages in a real browser. Every page became usable in 28-51
milliseconds against a 3-second budget, with no error messages in the browser console. The
measurement also found one real problem: the Regime Lab page could sit on a blank grey
placeholder for 60-90 seconds the very first time it is opened after new data arrives, and once
showed a raw server error. The team fixed the display side inside this same iteration — the page
now says "Still computing — 6s elapsed", explains the wait, and offers a Retry button when the
load fails. I opened both pictures myself and they show exactly that. J-07 "Heavy aggregates
never take the service down" was deliberately left for the next iteration and is unchanged.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Backfill honors the requested range and explains zero-work | passing | passing (re-verified) | `reports/phase-goal-ops-hardening-iter-33-ui-test-results.md` row UT-J-01 PASS; `reports/qa/goal-ops-hardening-iter-33-evidence/J-01-verify.png` |
| J-03 No per-run range cap | passing | passing (re-verified; spot-checked) | row UT-J-03 PASS; `reports/qa/goal-ops-hardening-iter-33-evidence/J-03-verify.png` (opened: Data Manager renders under prod mode with real coverage figures — 1996-01-02 → 2026-07-22, 591 symbols, 5383 trading days, 1879 snapshot dates) |
| J-04 Non-blocking boot with visible status | passing | passing (re-verified) | row UT-J-04 PASS; `reports/qa/goal-ops-hardening-iter-33-evidence/J-04-verify.png` |
| J-05 Aggregates are precomputed at ingest, never on the fly | passing | passing (re-verified) | row UT-J-05 PASS; `reports/qa/goal-ops-hardening-iter-33-evidence/J-05-verify.png` |
| **J-06 Pages load only what they need** | **partial** | **passing** | row UT-J-06 PASS in `...-ui-test-results.md` (agrees with `...-ui-test-results.llm.md` 1/1 and the 6/6 replay file); `reports/qa/goal-ops-hardening-iter-33-evidence/J-06-regime-lab-warm.png` (opened); measurement section `reports/perf-budgets.md:4099-4270`; honest-status fix pictures `UT-11-fix-computing-notice.png`, `UT-11-fix-error-retry.png` (both opened); step-3 code audit `docs/handoffs/goal-ops-hardening-iter-33-dev.md:151-186`. Gap recorded as `capture-defect` / `evidence_makeup`: the `[NEW]`-flagged walkthrough is still missing (`reports/phase-goal-ops-hardening-iter-33-demo-results.md` has 8 steps, none flagged `[NEW]`, and was recorded before the fix landed) |
| J-07 Heavy aggregates never take the service down | partial | partial (carried, not tested) | Neither a target nor in this iteration's Required-still-passing set; no J-07 row in any results file, no J-07 screenshot in this iteration's evidence directory. `last_verified_iter` deliberately stays iter-32. The developer's own 8/8 dry-run (`docs/handoffs/goal-ops-hardening-iter-33-dev.md:137-149`) wrote to a scratch directory and is not a lane artifact, so I did not let it advance the record |
| J-08 Backtest evidence serves from storage only | passing | passing (re-verified; spot-checked) | row UT-J-08 PASS; `reports/qa/goal-ops-hardening-iter-33-evidence/J-08-verify.png` (opened — see note below) |
| J-09 The backend discloses its own background-compute activity | passing | passing (re-verified) | row UT-J-09 PASS; `reports/qa/goal-ops-hardening-iter-33-evidence/J-09-verify.png` |

Notes on the evidence, stated rather than rounded away:

- **The merged results file did NOT launder anything this run, and this is the first run where
  that is a fixed property rather than luck.** I compared `...-ui-test-results.md` (PASS, 7/7)
  against `...-ui-test-results.llm.md` (PASS, 1/1 — J-06 only) and
  `...-regression-replay-results.md` (PASS, 6/6): all three agree, 7 = 6 + 1, zero FAIL rows,
  zero reconciliation footers. The `_ROW_RE` bug four consecutive evaluators flagged as a
  pre-achievement blocker is now fixed (`incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py`
  line 40, `(?:UT|TC)-`), with a genuine RED-before test the auditor re-ran himself (T2, 7 passed).
- **The merged file's earlier FAIL headline was cured by a real re-run, not by a rewrite.** The
  auditor (F2) found the merged artifact still carried a pre-fix `FAIL` at 12:35. I checked the
  file times myself: the browser lane genuinely ran again afterwards (`...llm.md` 22:57, merged
  22:58, per-page pictures `UT-01…UT-11-result.png` at 20:43-20:45, replay at 20:29). So the
  PASS I am reading is a fresh execution, not an edited verdict.
- **J-08's picture shows an honest "Warming up" state, not its scorecard.** Its golden script
  asserts the text "Forward-tested evidence" as a hard assertion, and `demo_runner.py`'s check
  uses element visibility, which is independent of scroll position — so the text was present
  while the single 1280x800 frame captured at scroll position 0 does not include it. This is the
  same capture-framing limit iter-32 diagnosed on this same page, not a contradiction of J-08's
  status.
- **The recurring byte-identical-screenshot nit did NOT recur this run** (13 iterations running
  before this one). `J-01/J-03/J-04-verify.png` now have three distinct md5s
  (`98c55dba` / `0051ec47` / `b7deee5c`).
- **What "time-to-interactive" means in this sweep, plainly:** the recorded number is the
  browser's own document `loadEventEnd`, and each page's data-fetch latencies are recorded
  separately in the same section. The section says so itself and explains that Regime Lab's slow
  part is the async fetch, which `loadEventEnd` cannot see. J-06 step 1 asks for both numbers
  separately, so this satisfies it — but nobody should read "33 ms" as "the table was on screen
  in 33 ms".

## Anti-goal Check

Worked from `runs/goal-session-ops-hardening/iter-33/scan-report.md` (CLEAN) plus
`iter-diff.md`, and re-derived the load-bearing ones myself. Product-path changes since the
snapshot `197fe13f`: `apps/frontend/app/research/_labs.tsx` (modified),
`apps/frontend/lib/lab-load-panel.ts` + `.test.ts` (new),
`apps/backend/tests/test_start_frontend_script.py` (new), `reports/perf-budgets.md`, the three
scripts, and an owner host-guard commit. `git diff --stat` over `apps/backend/app` is EMPTY.

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 (nothing presented as proven without a ledger-backed claim) | OK | No proven language added. The new copy is the opposite: "nothing is shown in the meantime rather than a partial or fabricated result". The J-06 picture still carries the survivorship-bias / "descriptive evidence, not a predictive model" notice. |
| AG-2 (decision-quality only; no orders) | OK | No new claims, no order surfaces. Header still reads "Research-only · decision support · no orders" in every screenshot I opened. |
| AG-3 (displayed numbers must be correct) | OK | No engine/serving code changed, so served values cannot have moved. Cross-checked anyway: the J-06 picture's "Strong risk-on" 1-day cell reads +0.01% n=201789, matching the independently curl-fetched payload recorded at `reports/perf-budgets.md:4189` (n=201789, mean_return=0.0000746). |
| AG-4 (no overfit edges) | OK | No new "proven" pattern; no referee-facing change. |
| AG-5 (determinism / no lookahead) | OK | No change under `apps/backend/app` (auditor B1 confirmed independently); the new frontend module is a pure state resolver that fetches nothing. |
| AG-6 (no evidence-derived claim without a referee verdict) | OK | No evidence claims this iteration; goal.md's own loop mechanics exempt J-01…J-06 from evidence claims. |
| AG-7 (no hard-coded credentials) | OK | `scan-report.md`: CLEAN, no secret findings on added lines (3 untracked files scanned). I also eyeballed the new files: no config/env file added. |
| AG-8 (resilience; graceful degradation; no unbounded whole-table ORM loads) | **MINOR, unresolved (6 findings)** | Improved and worsened in different places. Improved: the one over-budget page found this run now shows an honest labelled wait and a Retry control (pictures opened). Not fixed: **iter-33/g** (NEW) the Regime Lab cold path blocks the request thread 60-90 s and once returned HTTP 200 carrying the body "Internal Server Error", undiagnosed; **iter-33/h** (NEW) four sibling research labs still have the exact unlabelled-skeleton shape that just failed as a P1. Carried untouched: iter-29/b (`warmup.py:194`), iter-29/d (`prices.py:141`), iter-31/e (Factor-Lab constant-factor residual), iter-32/f (`run_rows`). All minor: nothing crashed, no memory was exhausted, no value was fabricated, and AG-8's own remedy wording is met on the measured page. |
| AG-9 (offline-deterministic ingest; no paid services) | OK | No ingest change. `git diff` over `apps/frontend/package.json`, `package-lock.json`, `apps/backend/requirements.txt` and `pyproject.toml` is EMPTY — no dependency added, paid or otherwise. `lab-load-panel.ts` imports nothing. |
| AG-10 (host resource ceiling — hardware protection) | **PASS on its letter; MINOR new finding (iter-33/i)** | I verified the machine-checkable part myself: `git diff 197fe13f..HEAD` over `scripts/dev.sh` and `scripts/start-backend.sh` is EMPTY, so both HOST-GUARD blocks are byte-unchanged (the marker files named in `host-guard.env`). Caps moved in the SAFE direction this window: `HOST_GUARD_MEMORY_HIGH` 14G → 10G, CPU mask `0-3,8-11` unchanged (owner commit `afbd72f6`, recording hardware reset #6, dated today). New fact recorded: `start-frontend.sh` now runs a full multi-worker `next build` and is not a marker file, so the automated lanes can trigger a production build with no cap of its own; the auditor measured that it inherits the affinity mask in practice (`taskset -cp` → `0-3,8-11`). Nothing removed, weakened or bypassed, so not critical — but it needs an owner decision, not an agent guess. |

Coherence: `runs/goal-session-ops-hardening/iter-33/coherence.md` is **COHERENCE-WARN**, not FAIL —
no blocking violation, no new page/route/nav entry, no duplicate computation, budgets still live in
exactly one file. Its WARN is the sibling-lab inconsistency, recorded above as iter-33/h. A WARN is
not a veto, so it does not force a consolidation pass; I carried its advisory into the
recommendation instead.

## Next-Step Recommendation

Target J-07 "Heavy aggregates never take the service down" and finish it. Two things are left,
both small and both named in J-07's own text:

1. **Record how long the health check takes during a heavy warm-up, not just that it answers.**
   Last iteration counted 77 of 77 successful answers but wrote down no timing. Please record the
   timing and say plainly whether it is inside the written 0.1-second limit. Useful new fact from
   this run: on a quiet machine the health check measured 93.4 ms — inside the limit for the first
   time on record (`reports/perf-budgets.md:4261`). Under a busy machine with a browser running it
   measured 97.8-207.7 ms and is recorded as an honest WARN. That is enough to settle the
   long-standing owner question: the limit is met at rest and missed under load, so it should be
   written down that way rather than amended.
2. **Run the memory-pressure drill** (J-07 step 4), which has been postponed since iteration 14:
   squeeze memory during a warm-up in a throwaway process and show that the warm-up stops
   honestly while the same process keeps answering the health check. **Launch it only through
   `scripts/start-backend.sh` so the host caps apply** — the machine had hardware reset #6 today,
   and the caps were tightened this morning because of it.

Ride-alongs, never an iteration's goal: record the missing `[NEW]` walkthrough for J-06 (budgets
table next to live page loads) and for J-07 (crash-free warm-up plus healthy health check); give
J-06's picture a frame that shows the budgets table rather than one lab page; and re-take J-07's
picture so it shows the "Forward-tested evidence" tables.

Carried and worth naming, in priority order: the Regime Lab cold-start problem (iter-33/g — a
60-90 second blocking wait and one raw server error, both backend-side and both still open); the
four sibling research labs that still show an unlabelled placeholder (iter-33/h — the resolver is
already written and exported, so this is wiring, and three separate lanes flagged it); the two
UI-impact documents and the demo recording that were written before this iteration's fix landed and
now describe the wrong tree (`...-ui-surface-map.md`, `...-user-visible-changes.md`, both 11:08 —
the pipeline should regenerate these after any fix round that changes real UI); `warmup.py:194`
(what the readiness badge should say after a warm-up permanently fails — four iterations unmade);
`prices.py:141`; iter-31/e; iter-32/f; `J-07.json`'s literal `n=8869` assertion, which will break
for a non-defect reason the moment the data grows.

One owner decision, not urgent and not blocking: should `scripts/start-frontend.sh` be added to
the host-guard marker list now that it runs a full production build inside the automated lanes?

What should happen next, in one sentence: approve one more full-depth iteration that finishes
J-07 by recording the health-check timing and running the memory-pressure drill through the
capped launch script — after that, all eight journeys are candidates for a final achievement
check.
