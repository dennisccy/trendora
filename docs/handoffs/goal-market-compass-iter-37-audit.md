# goal-market-compass-iter-37 Audit Report

**Date:** 2026-09-01
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The closing round achieved its substance: both backend robustness repairs are correct and
independently proven (I re-ran 125 tests across the changed file's own coverage and built a
negative control showing the new `-O` test genuinely discriminates), the J-13 acceptance
screenshot is a real capture (13,647 distinct colours, and I read the rotation panel out of the
image myself), J-13's golden executed for the first time in the deterministic replay lane, and
AG-12 holds (no manifest row or export file was created or touched this iteration). The depth
drop did **not** recur a fifth time — the engine log records `Depth arbiter: FULL pass granted`
and `Dispatching FULL pipeline`. The gaps are process-evidence, not correctness: one of the four
full-only artifacts the spec named as its proof (`…-ux-regression.md`) exists only as a 284-byte
"SKIPPED" stub because the wall-clock budget trim shed that reviewer, and the browser-qa agent
re-wrote `journey-scripts/J-13.json` **after** the replay it had just passed, re-breaking the very
mtime signal iter-36's lesson told the evaluator to use.

---

## 2. Findings

### Process / Evidence Findings

**P1 — IMPORTANT (gap): one of the four full-only artifacts is a skip stub, so the spec's own
proof-of-full-depth is 3-of-4 at audit time**

DEFINITION OF DONE item 2 / TC-5 requires all four full-only artifacts on disk "with non-trivial
content (not empty stubs)". Actual state:

| Artifact | State |
|---|---|
| `reports/qa/goal-market-compass-iter-37-qa.md` | PRESENT, 5,792 B, substantive |
| `reports/phase-goal-market-compass-iter-37-ux-regression.md` | PRESENT but **284 B skip stub** — `**Verdict:** UX-REGRESSION-SKIPPED … SPEED-15 trim rung 3b … this iteration exceeded its wall-clock budget, so this non-blocking reviewer was shed` |
| `docs/handoffs/goal-market-compass-iter-37-audit.md` | this file |
| `reports/phase-goal-market-compass-iter-37-closure-verdict.md` | **not yet written** — Step 10 runs after Step 9 (audit); pending, not lost |

`runs/goal-session-market-compass/engine.log:8041,8044` (15:26:56) records the shed explicitly:
`[iter-budget] This iteration has run 4935s — over the 3600s budget (checked at: qa-loop; mode:
trim)` then `Step 8/11 -- UX Regression: SKIPPED (iter-budget trim rung 3b … non-blocking reviewer
shed; closure + main auditors still run)`.

Two things must be said precisely, because they point in opposite directions:

1. **The failure mode the whole iteration was called to close did NOT recur.** `engine.log:7947-7951`
   (14:19:15-14:19:20) reads `Depth arbiter: FULL pass granted (reason: prior-verdict-ESCALATE)` →
   `Iter spec depth: full` → `Dispatching FULL pipeline via run-phase.sh --no-finalize`. The full-only
   lanes ui-impact (`…-user-visible-changes.md`, `…-ui-surface-map.md`), ui-test-design
   (`…-ui-test-plan.md`, `…-what-to-click.md`), browser-qa (`…-ui-test-results.md` + `.llm.md`) and
   QA all produced real artifacts. This was a genuine full dispatch, not a silent lean substitution.
2. **But the spec's chosen proof is not fully satisfied**, and `docs/goal.md`'s loop-mechanics rule
   is satisfied only in its "must be surfaced explicitly" half: the drop is written down in the log
   AND in the artifact itself, so nothing is hidden — but a shed lane is still a lane that did not run.

Not fixable inside the audit: re-running the UX-regression reviewer is an orchestration decision, and
manufacturing that artifact from the audit lane would destroy the independence that makes it worth
having. Reported for the evaluator/human to weigh.

**P2 — GAP: the J-13 golden was re-written 13 minutes AFTER the replay it passed, re-breaking the
mtime signal (the substance is fine; the signal is not)**

- The golden genuinely executed for the first time: `engine.log:8010` (14:59:16)
  `[browser-qa] Target journey J-13 has an on-file, lint-valid golden — routed into the deterministic
  replay set` and `engine.log:8013` `Regression (deterministic replay): J-01 J-02 J-03 J-04 J-05 J-06
  J-07 J-08 J-10 J-11 J-12 J-13`; `reports/phase-goal-market-compass-iter-37-regression-replay-results.md`
  records `UT-J-13 … PASS` with evidence `J-13-verify.png` (written 14:59:54).
- **But** `runs/goal-session-market-compass/journey-scripts/J-13.json` now has mtime
  **15:12:41**, i.e. 13 minutes *after* that replay. Cause is documented, not sinister:
  `runs/goal-session-market-compass/trace/0385-browser-qa-agent.log:13` lists the golden as
  "re-verified and re-written, lints clean".
- Content is provably unchanged: `git status --porcelain -- runs/goal-session-market-compass/journey-scripts/`
  is empty and `git diff HEAD` on `J-13.json` is empty, so the file on disk is byte-identical to the
  version committed in `ab3cca63` (iter-36) — exactly the bytes the 14:59 replay executed.

Consequence: DEFINITION OF DONE item 3's literal clause ("`J-13.json`'s file mtime is strictly
earlier than this iteration's replay run") reads **false** on today's disk, for the second iteration
running, even though its intent is met. The next evaluator applying the iter-36 lesson mechanically
will reach the wrong conclusion. The durable fix belongs upstream (browser-qa should not re-write a
golden it did not change, or should re-write it before the replay), not in an mtime edit — touching
the timestamp to make the check pass would be evidence tampering and was not done.

**P3 — OBSERVATION: `runs/goal-market-compass-iter-37/depth-dispatched` does not exist — the spec
named an artifact this framework version does not produce**

TC-5's first clause is unverifiable as written: `find runs -maxdepth 2 -name depth-dispatched` returns
exactly one hit in the entire repo (`runs/goal-market-compass-iter-10/depth-dispatched`), so no recent
iteration writes it. Depth is instead proven by `engine.log:7947-7951` (quoted in P1) — strictly
stronger evidence than a marker file, and consistent with the iter-34 lesson that markers are not a
depth signal.

**P4 — OBSERVATION: J-09 has no deterministic golden and was carried by the LLM/evidence lane**

`runs/goal-session-market-compass/state/golden-gaps` contains exactly `J-09`, and `engine.log:8017`
repeats the standing warning. The merged results file
(`reports/phase-goal-market-compass-iter-37-ui-test-results.md`) therefore carries J-09 as an
evidence-based row (VmPeak 2,292,200 kB ≤ 2,621,440 kB target; `reports/perf-budgets.md` newest
heading still `## Addendum 45` at line 12822 and `git status --porcelain -- reports/perf-budgets.md`
empty — both re-verified by me). This satisfies the DoD's "deterministic replay **+ LLM fallback**"
wording, but J-09's coverage remains the weakest of the thirteen and has been for several rounds.

**P5 — OBSERVATION: the spec's `Frontend Present: no` contradicts its own screenshot requirement; the
pipeline resolved it correctly**

`docs/phases/goal-market-compass-iter-37.md` declares `Frontend Present: no`, yet its DEFINITION OF
DONE demands a browser-captured acceptance screenshot — the QA report flags the clash in its own
header ("no (per phase spec); yes (per dispatch)"). The engine overrode the metadata rather than the
requirement: `engine.log:7992,8000,8006,8019` all read `[detect_frontend_in_plan] goal-mode journeys
present (J-13) — forcing browser lane despite plan`. Right outcome; the metadata line should have read
`yes` for an iteration whose sole acceptance artifact is a screenshot.

### Backend Findings

**B1 — GAP: only one of the two converted guard statements is exercised under `-O`**

`apps/backend/app/engine/compass.py:595-606` now has two explicit raises. The new test
(`tests/test_manifest_invariants.py:957-988`) constructs a row labelled `below_selection_floor` whose
`leadership_score` clears the floor — it exercises the **first** branch only. The
`excluded_by_cap` branch's raise (compass.py:602-606) is never executed under `-O` by any test. The
spec's TC-2 asked for one such row, so this is within scope-as-written; noting it because a future
`-O` re-strip of only the second statement would go undetected.

**B2 — GAP: one `-O`-strippable bare `assert` remains in production code, deliberately deferred**

`apps/backend/app/engine/compass.py:815` —
`assert len(gating_checks) == 1, "expected exactly one gating qualifier check (leadership_min_score)"`.
The spec put this exact statement OUT OF SCOPE this round, and it was correctly left untouched. Worth
recording precisely: `grep -rn "^\s*assert " apps/backend/app --include=*.py` now returns **exactly
one** line repo-wide — this one. The class of defect iter-37 set out to remove is one statement from
being fully gone.

**B3 — OBSERVATION: the converted guard now runs under `-O` in production, which is the intent, and
carries no new risk here**

`_assert_disposition_predicate` is on the served path (`compass.py:892`, inside
`evaluate_selection`, called from `build_manifest_payload` at `compass.py:934`), so a violation now
surfaces as a 500 even under `-O`. Behaviour is unchanged for this deployment (uvicorn does not run
with `-O`), and the predicate mirrors the partition that produced the labels
(`compass.py:864-865` uses the same `>= sel.leadership_min_score` comparison), so it is
tautologically consistent — it can only fire on a real partition regression, which is exactly what it
is for.

### Test Findings

**T1 — OBSERVATION: two small brittleness points in the new/edited tests**

- `tests/test_manifest_invariants.py:957` — `test_assert_disposition_predicate_raises_under_dash_o(cfg)`
  requests the `cfg` fixture and never uses it (the subprocess calls `load_config()` itself).
- `tests/test_manifest_invariants.py:949` — `candidate_by_ticker["HPE"]` would raise `KeyError`, not a
  readable assertion failure, if HPE ever landed in `excluded_by_cap` — an outcome the assertion two
  lines above (`:944`) explicitly permits. Harmless at `max_candidates: 10` with a two-row fixture.

**T2 — OBSERVATION: the QA report's screenshot measurement describes a superseded capture**

`reports/qa/goal-market-compass-iter-37-qa.md` cites `1668×4317`; the file on disk is `1683×4320`.
This is **not** a fabricated measurement: `stat` shows `Birth: 14:53:49` (QA's own capture, matching
its 14:54 report) and `Modify: 15:10:57` (browser-qa's re-capture after it worked around the tooling
bug). Both captures were non-blank. The report's phrasing "`PIL.getcolors()` reports >256x256x3 unique
colors" is nonetheless a paraphrase of the function's `maxcolors` argument, not a measured count —
the actual count (13,647) appears only in the browser-qa lane's report. Cite counts, not argument
defaults.

**T3 — OBSERVATION (valuable, carried): the root cause of iter-36's blank screenshot is now known**

`runs/goal-session-market-compass/trace/0385-browser-qa-agent.log:8`: the browser tool "returns a
single-colour frame after any scroll … on this page"; the workaround was `set_viewport` to the full
document height (1683×4320) so no scroll is involved. This is the tooling explanation the last two
iterations lacked and should be carried into the session lessons rather than re-derived a third time.

---

## 3. Domain Assessment

**DEFINITION OF DONE trace.** Items 1, 2, 3, 5, 6 and 7 involve evidence integrity, data
persistence, or contradicted claims, so each got a full trace; item 4 is accepted on cited
reviewer + executed-QA evidence.

1. **Non-blank J-13 acceptance screenshot — MET (traced).** I measured
   `reports/qa/goal-market-compass-iter-37-evidence/UT-J-13-rotation-both-directions.png` myself:
   1683×4320, 693,670 bytes, **13,647 distinct RGB colours** via `PIL.Image.getcolors()`. Against the
   iter-36 file in the same position: 1683×1260, 9,401 bytes, **1** distinct colour. I then cropped the
   image and read the panel visually rather than trusting the filename: the "Leadership rotation"
   section renders "Sector rotation" with a **Gaining** column (`Regional Banks (SPDR) 13 → 10 (-3) ·
   improving`, `Bitcoin Miners (Valkyrie) 29 → 26 (-3) · improving`, three more) and a **Losing**
   column (`Home Construction (iShares) 21 → 25 (+4) · deteriorating`, `Materials 12 → 16 (+4) ·
   deteriorating`), the accounting line `7 of 31 shown · 24 below threshold · 0 beyond the display cap.`,
   and a "Theme rotation" block with both sides. TC-3 is satisfied on measurement *and* on content.
2. **Four full-only artifacts — PARTIALLY MET.** See P1.
3. **Golden mtime < replay, replay records J-13 PASS — SUBSTANCE MET, LITERAL CHECK FAILS.** See P2.
4. **J-01..J-12 green, 0 FAIL / 0 skipped — MET (cited).** Reviewer PASS with `issues: []`
   (`reports/reviews/goal-market-compass-iter-37-review.md`), and the executed merged results file
   `reports/phase-goal-market-compass-iter-37-ui-test-results.md` records **13/13 PASS, 0 skipped**
   (twelve via the 14:59 deterministic replay, J-09 + J-13 re-verified by the LLM lane). Caveat P4.
5. **No anti-goal violation — MET (traced, not accepted on claim).**
   - *AG-12 / AG-17*: I queried the live DB read-only:
     `select count(*), max(created_at) from next_session_manifests` → **34 rows, newest
     `2026-09-01 12:34:12`** — i.e. every row predates this iteration's 14:19:20 start. Every file in
     `apps/backend/data/exports/next_session_manifests/` has an mtime at or before 12:50:50 (v9), and
     `git status --porcelain -- apps/backend/data/exports/` is empty. Nothing was frozen, mutated, or
     deleted this round.
   - *AG-11*: the diff adds no served field and no blended score — it is one fixture literal, two
     control-flow rewrites, and test code.
   - *AG-8*: no new ORM read of any kind; the guard iterates an already-built in-memory list.
   - *AG-15*: `config.yaml` is unchanged versus HEAD (`git status --porcelain -- config.yaml` empty),
     so no `compass.selection.*` threshold moved.
6. **TC-24 fixture genuinely fails both qualifiers — MET (traced).** `tests/test_manifest_invariants.py:935`
   is now `_mk_result(session, run.id, "HPE", 92.7, "A", 21.5, "E", 65.0, "C")`; `_mk_result`'s signature
   (`:51-54`) binds those to leadership / entry / **risk**, and `config.yaml:1441-1443` sets
   `leadership_min_score: 80.0`, `entry_min_score: 70.0`, `risk_max_score: 60.0`. So `21.5 < 70.0`
   (entry fails), `65.0 > 60.0` (risk now genuinely fails — it did **not** at 58.9), `92.7 ≥ 80.0`
   (floor still clears). The confound the iter-35 lesson warned about is gone. Better still, the fix is
   not left as a fixture literal that a reader must re-derive: `:949-951` now assert against the
   **served** `what_would_change` checklist (`entry_min_score.met is False`, `risk_max_score.met is
   False`), which `compass.py:685-692` builds straight from `_qualifier_checks` — the test now verifies
   the claim rather than implying it.
7. **Guard raises under `-O`, proven by a new unit test — MET, and the test is genuinely
   discriminating (traced with a negative control).** A passing test proves nothing until you show it
   can fail. I temporarily restored the pre-iter-37 bare `assert` in the first guard branch and re-ran
   only the new test:

   ```
   E  AssertionError: guard did not raise under -O; stdout='NO_RAISE\n' stderr=''
   FAILED tests/test_manifest_invariants.py::test_assert_disposition_predicate_raises_under_dash_o
   1 failed, 55 deselected in 0.85s
   ```

   The child process exited **0** and printed `NO_RAISE` — the guard was silently stripped, exactly the
   defect this round set out to remove. `compass.py` was restored immediately (md5 identical before and
   after: `563dde6e1c12e73e72e066417ba1f32b`; `git diff --stat` back to the iteration's own
   `10 insertions(+), 8 deletions(-)`).
8. **Dev handoff written — MET.** `docs/handoffs/goal-market-compass-iter-37-dev.md` exists and is
   unusually honest: it discloses that no `depth-dispatched` file existed at its hand-off time rather
   than passing over it, and it does not claim credit for downstream lanes.

**Independent test evidence (my own runs, not the dev's or QA's).** `compass.py` is a production file
and neither the developer nor QA ran its own test modules this iteration — only
`test_manifest_invariants.py`. I closed that hole:

| Command | Result |
|---|---|
| `.venv/bin/python -m pytest tests/test_manifest_invariants.py -q` | **56 passed** in 5.94s |
| `.venv/bin/python -m pytest tests/test_compass.py -q` | **50 passed** in 5.13s |
| `.venv/bin/python -m pytest tests/test_api_compass.py -q` | **19 passed** in 3.27s |
| `.venv/bin/python -m pytest tests/test_no_magic_numbers.py -q` | 1 passed, 1 failed — offenders are `indicators.py`, `forward_testing.py`, `research.py` only; **`compass.py` appears in zero offender lines** (pre-existing, explicitly out of scope) |

(Both compass test modules document that they deliberately avoid the heavy `loaded_engine` fixture, so
running them was safe under this project's "never run the full suite" rule.)

**Scope discipline.** `git diff --name-only HEAD -- apps/ config.yaml docs/ scripts/`, with the 55
`apps/frontend/.next-verify/` build-output files excluded, returns exactly
`apps/backend/app/engine/compass.py` and `apps/backend/tests/test_manifest_invariants.py`. Zero scope
creep; zero `.tsx` touched, as the binding "Do not redo" required. (The `.next-verify` churn is the
carried, known problem of a build directory tracked in git — regenerated by QA's verification build
every iteration. Still worth untracking one day; not this round's business.)

**Judgement on the domain logic.** The guard conversion is a pure control-flow rewrite: same
condition, same message, same exception type, same call site, no new literal. Nothing computed or
served can differ, and the 125 green tests plus the live `GET /api/compass` round-trips (dev's curl,
QA's browser check, browser-qa's 15:10 page load) confirm it end-to-end. The fixture repair is the
better of the two changes — it converts a test that was green and blind into one that is green and
looking at the served value.

---

## 4. Fixes Applied During This Audit

None. No CRITICAL or IMPORTANT finding was fixable in source: the two backend repairs are correct as
landed, and P1 (the shed UX-regression lane) is an orchestration/budget decision that the audit lane
must not paper over by writing the missing review itself.

The only file I touched was a **temporary, reverted** negative-control patch to
`apps/backend/app/engine/compass.py` (section 3, item 7), restored in the same command with md5
verified identical before and after. The repository is exactly as the developer left it.

---

## 5. Recommended Next Step

The product work for J-13 is done and now honestly evidenced — a real screenshot, a golden that has
actually executed, and two robustness repairs that are proven rather than asserted. What remains is
process debt, and it is small enough that it should ride along, never become a round of its own:

1. **Let the evaluator judge P1 on the facts, not the artifact count.** The depth dispatch was genuinely
   full (`engine.log:7947-7951`); one non-blocking reviewer was shed by the wall-clock trim and said so
   in writing. If the human wants that lane guaranteed, the lever is the budget/trim configuration or
   `CHAIN_REQUIRE_FULL_DEPTH` on the next invocation — the spec itself notes it cannot declare this.
2. **Stop the golden re-write from re-breaking the mtime signal (P2).** Either have browser-qa skip
   re-writing a golden whose content it did not change, or have the evaluator verify golden coverage by
   content identity (`git diff HEAD -- journey-scripts/`) plus the replay log line, rather than by mtime.
   Otherwise iter-38 will re-open a question that is already answered.
3. **Carry T3's tooling finding into the session lessons** — the single-colour-after-scroll screenshot
   bug and its `set_viewport`-to-full-height workaround, so no future round loses a screenshot to it.
4. **Two one-line hardening candidates** for whenever a round next touches this file legitimately:
   `compass.py:815`'s remaining bare `assert` (B2 — the last one in the whole backend), and an
   `excluded_by_cap` row in the `-O` test (B1).

None of these blocks closing the iteration.
