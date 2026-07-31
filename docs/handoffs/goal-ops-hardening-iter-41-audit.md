# goal-ops-hardening-iter-41 Audit Report

**Date:** 2026-07-31
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The iteration's two headline closures landed for real: six required-still-passing journeys got
genuine, dated, this-iteration browser evidence (deterministic replay, `engine.log` 05:33:16→05:34:33,
6 journeys / 0 failed, six screenshots I opened and confirmed show the live app), and
`_BarCache.prefill`'s per-row memory cost fell a measured 51.5% with byte-identical `Bar` output.
But the *headline guard* this iteration shipped to prevent a repeat of iter-40 did not actually
prevent iter-40: feeding iter-40's own committed results artifact through the new merger still
produced a clean `SKIPPED` headline, because the guard only detects a *missing row*, and iter-40's
failure shape is a *present row that says SKIP*. I fixed that (B1, with tests). Two gaps remain
unfixed and are documented: the iteration's own **target** journeys J-05/J-07 received zero
browser-qa rows while the merged headline still reads a clean `PASS`, and `prefill`'s accumulator
was compressed, not bounded — it is still O(all rows) resident.

---

## 2. Findings

### Backend / Pipeline-tooling Findings

**B1 — CRITICAL (fixed): the new missing-required-journey guard does not catch iter-40's actual
failure shape, so an all-SKIP regression run still merged into a clean `SKIPPED` headline**

`incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py:159-173`
(`missing_required_journeys`) tests only for a required journey with **no row at all**
(`if tid not in present_ids`). The DoD line is stronger — *"An **all-SKIP**/zero-executed regression
run can no longer merge into a clean `SKIPPED`/`PASS` headline"* — and so is TESTING REQUIREMENTS
(*"`merge_ui_test_results.py` **all-SKIP-detection** test"*) and the spec's own wording for DoD item
2 (*"fresh, **non-`SKIP`** mechanical verification"*).

I reproduced the hole against the real artifact rather than a synthetic one. Feeding
`reports/phase-goal-ops-hardening-iter-40-ui-test-results.md` — the exact file whose clean headline
this whole iteration exists to make impossible — through the shipped merger with iter-40's own
required set:

```
headline verdict: SKIPPED
has Missing section: False
**Overall:** 0/8 journeys passed (8 skipped)
```

That file carries a row for every one of the seven required journeys, all reading
`SKIP` / `"Not executed — dispatch instructions state frontend is not available"`. Because a row
*exists*, `missing_required_journeys` returns `[]`, no BLOCKED forcing happens, `compute_overall`
returns `SKIPPED`, and `goal_gate.py::cmd_results` (`goal_gate.py:153-161`, which blocks only on
FAIL/DEFERRED/BLOCKED cells or a BLOCKED headline) returns 0 — achievement unblocked. The guard as
shipped would have passed iter-40 unchanged.

**Fix applied** (`merge_ui_test_results.py`, the only file I touched):
`skipped_required_journeys()` (line 176) — a required journey whose row's verdict is a literal
`SKIP` counts as unverified; `merge()` (lines 239-240) forces `BLOCKED` on either shape; the
existing "Missing Required Journeys" section and `**Overall:**` line now report both. Only literal
`SKIP` trips it: a `DEFERRED-BUDGET` row parses to an empty verdict and is deliberately untouched
(SPEED-15 rung 2 keeps its own semantics, and `goal_gate.py::_DEFERRED_CELL_RE` already blocks on
those).

**Post-fix verification** (all commands re-run after the change):

| Command | Result |
|---|---|
| `python3 .../merge_ui_test_results.py self-test` | **22 passed, 0 failed** (was 20; +2 new) |
| iter-40 artifact re-merged (repro above) | headline now **BLOCKED**, `8 skipped, 7 required-unverified`, gap section present |
| iter-41's own merged file re-merged with its required set | still **PASS**, no gap section — no false positive on this run |
| `python3 .../goal_gate.py self-test` | passed |
| `python3 .../closure_gate.py self-test` | 10 passed, 0 failed |
| `python3 .../artifact_schemas.py self-test` | passed |
| `python3 .../lint_contracts.py self-test` | passed, current-tree lint clean |
| `bash incredible_auto_dev/tests/automation/test-replay-lane.sh` | **65 passed, 0 failed** |
| `bash incredible_auto_dev/tests/automation/test-closure-gate.sh` | **18 passed, 0 failed** |

New self-tests: `all_skip_required_journeys_block_clean_skipped` (iter-40's exact shape) and
`mixed_skip_and_pass_blocks_only_on_the_skip` (which also asserts a **non**-required journey's SKIP
row must NOT trip the guard, so the change cannot manufacture false BLOCKEDs). `git diff` on the
file confirms my delta is confined to the new helper, the two-line `merge()` wiring, the section
text, and the two tests — nothing else.

**B2 — IMPORTANT (gap): the iteration's target journeys J-05 and J-07 got zero browser-qa rows, and
the merged headline still reads a clean `PASS`**

DoD item 1 is *"Target journeys J-05, J-07 pass … via browser-qa-agent"*; TESTING REQUIREMENTS lists
*"Browser: J-05, J-07 (targets)"*; TC-4 demands a fresh dated artifact per journey. None exists.

- `reports/phase-goal-ops-hardening-iter-41-ui-test-plan.md:24-29` states outright that J-05/J-07
  are *"intentionally NOT given `UT-J-XX` rows here, matching the ui-test-designer's fixed scope
  (required-still-passing journeys only)."*
- The A2 fix (`incredible_auto_dev/agents/ui-test-designer/body.md`, "Backend-only phase handling")
  keys entirely off the `Required-still-passing journeys:` metadata line; it has no notion of
  `Target journeys:`. So on any backend-only iteration, a target journey structurally cannot get a
  test case.
- `goal-iter-lean.sh:781` dispatched the LLM lane with `_llm_set="$TARGET_JOURNEYS …"` = `J-05,J-07`,
  but with no test-plan case to execute the agent stood down:
  `…-ui-test-results.llm.md:9` `**Browser QA Verdict:** SKIPPED`, line 24 `**Overall:** 0/0 tests
  passed`, and an empty results table at lines 33-37.
- The replay lane covered only the six required journeys (`engine.log:6495`
  `Regression (deterministic replay): J-01 J-03 J-04 J-06 J-08 J-09`) even though golden scripts
  `runs/goal-session-ops-hardening/journey-scripts/J-05.json` and `J-07.json` both exist and were
  replayed in iters 38/39 (`engine.log:5552`, `:6081` include J-05). **J-05 therefore has *less*
  evidence this iteration than in the three before it** — promoting it to "target" moved it out of
  the replay set and into a lane that ran nothing.
- Consequence: `reports/phase-goal-ops-hardening-iter-41-ui-test-results.md:8-10` headlines
  `PASS`, `6/6 journeys passed (0 skipped)` with no mention that two of the eight in-scope journeys
  were never exercised. Neither `goal_gate.py` nor `closure_gate.py` has any target-journey notion,
  and my B1 fix (correctly scoped to the spec's A3 bullet) does not cover targets either.

J-07 is not entirely evidence-free this iteration — the wedge drill supplies real data for its
steps 2/3 (58 `/api/health` polls, all 200, max 1.73 s; VmPeak 2,446,836 kB, 9.8% under the 2650 MB
cap). J-05 has essentially none.

**Not fixed deliberately.** The obvious one-liner — pass `TARGET_JOURNEYS` alongside
`REQUIRED_JOURNEYS` into `replay_lane_merge_results`'s `--required` — has a real false-positive
mode: on a normal front-end iteration a target journey is verified under a **new-surface**
`UT-01`/`UT-02` row, not `UT-J-05`, so the guard would force `BLOCKED` on correctly-verified work
and block future iterations. Shipping that as an unrequested audit change would trade one CRITICAL
for another. See §5 for the recommended shape.

**B3 — GAP: `_BarCache.prefill`'s accumulator was compressed ~2x, not bounded — the whole table is
still resident**

The IN SCOPE bullet reads *"stop accumulating every row into one resident `by_symbol` dict"*, the
phase title says *"close the last unbounded whole-table load"*, and goal.md's J-05 acceptance says
*"no code path streams the full `daily_prices` table into RAM."* What shipped
(`apps/backend/app/engine/prices.py:220-244`) still walks every row of `daily_prices` into one
resident `by_symbol` dict; only the per-row representation changed (`_SymbolColumns` at
`prices.py:77-121`: five `array.array('d')` columns plus a `list[date_cls]`). Memory is still
strictly O(row count) — at ~165 bytes/row instead of ~380 — so it scales with the deep basis exactly
as before, just with a smaller constant. TC-6's own acceptance bar ("*lower* than the unbounded
baseline") is met; the prose bullet's stronger claim is not.

The developer disclosed this honestly and unprompted in `reports/perf-budgets.md:5360-5366`
(*"this bounds the PER-ROW memory cost of the accumulator, not the fact that the whole table is
loaded"*), which is why this is a GAP and not a dishonesty finding. What is *not* accurate is the QA
report's anti-goal table (`reports/qa/goal-ops-hardening-iter-41-qa.md:133`), which records AG-8 as
`✓ PASS` under the heading *"no whole-table loads."* The goal-evaluator should not read
iter-29/d as closed.

**B4 — OBSERVATION: the iteration's stated root cause #1 is not what voided iter-40's browser lane**

The spec's BACKGROUND names the wrong `BACKEND_HEALTH_URL` as root cause #1. iter-40's own log shows
the browser lane *did* run (`engine.log` 02:20:43 `[browser-qa] Running browser QA for:
goal-ops-hardening-iter-40`) and died on the **frontend** probe: `Waiting for frontend at
http://localhost:3255 … Warning: frontend did not become ready within 90s (last status: 000)` —
20 minutes later the demo lane found the same frontend ready in 0 s. The backend health URL was
never the blocker (the frontend URL is separate, and `ensure_services_running`'s backend probe is
already permissive — `common.sh:1262` passes `ready_re='^[1-5][0-9][0-9]$'`, so a 404 has always
counted as "up"). Root cause #2 *is* real: iter-40's
`reports/phase-goal-ops-hardening-iter-40-ui-test-plan.md` is the bare N/A stub with zero `UT-J-`
rows, and this iteration genuinely fixed that. Net: the health-URL fix is a real latent-bug fix but
was not load-bearing; the frontend-readiness race that actually voided iter-40 is untouched, and the
only compensating control against it is the merge guard — which is why B1 mattered.

**B5 — OBSERVATION: `resolve_backend_health_url` hardcodes a project-specific path into the neutral
framework source**

`incredible_auto_dev/scripts/automation/lib/common.sh:387-394` returns
`http://localhost:${port}/api/health` unconditionally. That is Trendora's route baked into the
shared framework library, where the previous value was the framework-generic `/health` — one wrong
default swapped for another for any other project on this framework. It mirrors `demo_runner.py`'s
existing iter-39 precedent so it is at least consistent, and `CHAIN_BACKEND_HEALTH_URL` still wins;
a `config/`-sourced value would be the clean home.

**B6 — OBSERVATION: `array.array('d')` is stricter about NULLs than the `list[Bar]` it replaced**

`prices.py:227-236` appends raw column values into `array.array('d')`, which raises `TypeError` on
`None`, where the old `Bar(d, o, h, lo, c, v)` would have accepted it. `app/models.py:98-102`
declares all five numeric columns non-Optional (NOT NULL at the DB level), so this cannot fire on
the current schema — but AG-8's text names "new nulls" explicitly as a widening to survive, and this
path would now crash rather than degrade. Worth one line of defensiveness the next time this file is
opened; not worth reopening it now.

### Frontend Findings

None — `Frontend Present: no`, and I confirmed zero frontend files in `git status`.

### Test Findings

**T1 — OBSERVATION (accepted): TC-6's byte-identity test is fixture-scoped, and the identity holds
for a non-obvious reason worth recording**

`apps/backend/tests/test_bar_cache.py:99-144` compares an in-test reimplementation of the pre-iter-41
body against the shipped `prefill` over the 2-symbol `tiny_engine` fixture. I traced why the
identity generalizes rather than taking the green test at face value: `DailyPrice.open/high/low/
close/volume` are all declared `float` (`app/models.py:98-102`), SQLite applies REAL affinity, and
`array('d')` stores IEEE-754 doubles — so values round-trip bit-exactly, including the `volume`
column that a naive reading might expect to come back as an `int` and change type. Slice semantics
also hold: `_SymbolColumns.__getitem__` returns a `list[Bar]` for a slice and a real `Bar` for an
index, matching every call site (`bars_asof` `full[:cut]`, `bars_asof_window`
`full[max(0,cut-lookback):cut]`, `bars_after` `full[cut:cut+limit]`, `close_on` `full[cut-1].close`).
`_dates_by_symbol[symbol] = cols.dates` aliases one list (`prices.py:244`); I checked every use in
the file — all are whole-list assignments or `bisect` reads, never in-place mutation — so the alias
cannot desynchronize the columns.

**T2 — OBSERVATION: the storage change trades resident memory for per-call CPU and transient
allocation on the read path, and nothing measures it**

Where a prefilled `list[Bar]` made `full[:cut]` a pointer-copy of already-built objects,
`_SymbolColumns` now *constructs* every `Bar` on each slice. A `bars_asof` call over a ~7.5k-bar
series builds 7.5k NamedTuples and 5 boxed floats each instead of copying 7.5k pointers. iter-26/27
already moved the hot callers onto bounded accessors (`bars_asof_window`, `close_on`), which limits
the blast radius, and the live-DB suites still pass — but no before/after latency figure was
recorded next to the memory one, and J-05/J-06 both carry latency budgets. Not a defect; a
measurement that would be cheap to add the next time this path is touched.

**T3 — OBSERVATION: the dev's own process note is the most valuable line in the handoff**

`docs/handoffs/goal-ops-hardening-iter-41-dev.md:318-325` records that
`test_faulthandler_sigusr1_diagnostic.py` shipped never having been executed while twenty other
commands were listed in "Tests Run" — the same "green report over unrun verification" shape this
iteration exists to close, reproduced inside its own diff. The reviewer caught it, the dev fixed and
re-verified it 3/3, and disclosed the mechanism rather than the symptom. That is the right behavior
and it should survive into the next iteration's planning rather than being closed as "fixed."

---

## 3. Domain Assessment

**Verification lane (A1-A4).** The mechanism now works end-to-end for the required set, and I
verified that empirically rather than from the handoff: `engine.log:6495-6496` shows the replay lane
executing exactly `J-01 J-03 J-04 J-06 J-08 J-09` in 77 s with 0 failures, the six evidence PNGs are
dated 05:33-05:34 today, and opening `J-09-verify.png` shows the real `/data` page with the
`background compute running (1)` chip in the top bar — precisely J-09's own assertion. This is the
first iteration in five with genuine journey evidence. TC-2 is soundly met: I traced both halves —
`resolve_backend_health_url` (`common.sh:387-394`) fixes the URL handed to the agent, and
`common.sh:1262`'s `ready_re='^[1-5][0-9][0-9]$'` already meant only a connection failure (empty
code), never a 404, reads as "down."

**The gate that was supposed to make this durable was the weakest part.** A verification lane that
works *this* run is worth much less than a gate that cannot report clean when it doesn't. The A3
guard was the durable half, and as shipped it missed the only real-world instance available to test
it against (B1). The lesson generalizes past this iteration: when a fix is written to prevent a
specific past incident, the incident's own artifact is the regression fixture — it was sitting
committed in `reports/`, and running it would have taken thirty seconds.

**Memory bound (B5/B6).** Engineering quality is high — `Sequence`-conformant, duck-types against
`list[Bar]` so the cache-poisoning test still passes, zero changes to any read method, honest scope
note in the perf table. The measurement is methodologically sound (separate subprocess per arm,
`/proc/<pid>/status`, identical `N_SYMBOLS`/`N_ROWS` in both arms). What it is not is a *bound*
(B3), and the difference matters for a session whose Success Criteria is phrased in terms of
unbounded loads.

**Diagnostics (C7/C8) and D9.** Correct and honestly reported. C7 is opt-in and default-off
(`main.py:54-66`), the drill did not reproduce the freeze, and both the README and perf-budgets say
so plainly without claiming a fix — the TC-5 outcome (b) written as specified. C8's CSV carries a
`phase` column with 28 `post_terminal` rows, all `health=200`. D9's count floor
(`data_manager.py:4094-4134`) is a clean addition to the existing throttle with no new persisted
field.

**Anti-goals.** AG-9: no network paths added; drills ran offline against a throwaway DB. AG-10:
`git status` on `scripts/` and `project-extensions/` is empty — launch scripts and `host-guard.env`
are byte-untouched, and the drill used the same tightened 2650 MB cap, never widened. The 570 MB
`drill.db` is correctly gitignored (`.gitignore:66`). AG-8: improves materially but is not closed
(B3). AG-3: the six replayed journeys assert displayed values, so it holds for what was tested.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Critical | `incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py` | Added `skipped_required_journeys()` and wired it into `merge()` so a required journey whose only row reads `SKIP` forces a `BLOCKED` headline, not a clean `SKIPPED`/`PASS` — closing the all-SKIP half of DoD item 3. Section text and `**Overall:**` line report both shapes. Two self-tests added (iter-40's exact all-SKIP shape; a mixed case asserting non-required SKIP rows do not trip the guard). Verified: self-test 22/22, iter-40's own artifact now merges to `BLOCKED` (`7 required-unverified`), iter-41's own merged file unchanged at `PASS`, plus `goal_gate`/`closure_gate`/`artifact_schemas`/`lint_contracts` self-tests and `test-replay-lane.sh` 65/65 + `test-closure-gate.sh` 18/18 all green. |

No handoff claim was invalidated by this fix; the dev handoff's A3 description remains accurate for
the zero-row case it covered.

---

## 5. Recommended Next Step

Proceed to the goal-evaluator, with three things carried explicitly:

1. **Do not score J-05 or J-07 from this iteration's merged `PASS` headline.** That headline covers
   six journeys; the two the iteration *targeted* have no rows (B2). J-05 in particular is now
   *less* verified than in iters 38/39. J-07 has partial non-browser evidence from the wedge drill
   (health polls + VmPeak) that can be scored on its own merits for steps 2/3.
2. **Close the target-journey hole next iteration** — this is the same class as B1 and the last one
   left. The durable shape is a journey→row mapping the gate can trust: have the
   `ui-test-designer` emit a `UT-J-XX` case for **target** journeys too on a backend-only spec
   (where, by construction, there is no new-surface case to carry them), then extend the merge guard
   to targets. Extending the guard alone is not safe — on a normal iteration a target journey rides
   a `UT-NN` new-surface row and would be falsely flagged.
3. **Reopen or re-scope iter-29/d rather than closing it.** `_BarCache.prefill` is ~2x cheaper per
   row and still O(all rows) resident (B3). Either amend goal.md's J-05 acceptance to a per-row
   budget the current design satisfies, or plan the real bound (per-symbol streaming / on-demand
   load) as a future iteration's one risky action. Correct the QA report's AG-8 row either way.

Also worth a line in the next spec: iter-40's proximate cause — the frontend failing its 90 s
readiness window mid-restart (B4) — is still unaddressed. With B1 in place it now produces a loud
`BLOCKED` instead of a silent clean run, which is the right failure mode, but the underlying race
will keep costing iterations until the browser lane waits for or re-probes a restarting frontend.
