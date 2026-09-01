# Goal Iteration 37 — Closing round: genuinely run full depth, replay J-13's golden, retake its blank screenshot, land two carried robustness repairs

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** market-compass
- **Iteration:** 37
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — prior evaluator verdict was ESCALATE (mandatory, no exceptions)
- **Frontend Present:** no
- **Target journeys:** J-13
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10, J-11, J-12
- **Anti-goal reminders:**
  - **AG-1:** A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked values MUST render a "not yet proven" state. *(critical)*
  - **AG-3:** A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation for the same as-of date — not merely that the page renders. *(critical)*
  - **AG-8 — Resilience to data-shape and data-scale change:** widening the data basis must never crash an existing page or exhaust memory — consumers of widened fields are re-validated, the UI degrades gracefully (contained error boundary, honest "—"/NA placeholder), and unbounded whole-table ORM loads are forbidden (the delta engine reads column-projected selects, never full record_json sweeps). *(critical)*
  - **AG-11 — No new composite candidate number:** no "fit", "conviction", "match", "probability of success", or any new blended score may be attached to candidates, the market, or the manifest; candidate presentation is limited to the existing three scores/buckets, config word maps, and structured reason/caution codes. *(critical)*
  - **AG-12 — Manifest immutability:** a stored `next_session_manifests` row and its exported file are never mutated or deleted by any later ingest, rebuild, data removal, config change, or code change; corrections happen only as new version rows; a historical view never substitutes a newer manifest. *(critical)*
  - **AG-15 — No outcome-tuned selection:** the selection rule and its thresholds must not be chosen or revised from realized forward returns within this goal; no Evidence Claim is introduced for it; any future selection-edge claim goes through the pre-registration registry and referee. *(critical)*

## GOAL

Close out the J-13 "Leadership rotation" delivery honestly: run this iteration through the genuine full-depth pipeline (not a silent lean substitution), produce a real, non-blank acceptance screenshot of the already-shipped rotation panel, execute J-13's golden script for the first time, and land two small, already-scoped robustness repairs — with zero new feature work.

## BACKGROUND

Iteration 36 built J-13 correctly (evaluator re-derived all 9 rotation rows against stored ranks; 31/31 sector and 11/11 theme accounting closes exactly) but returned **ESCALATE**, not GOAL_ACHIEVED, for two reasons that have nothing to do with correctness: (1) the spec read `Depth: full` yet every downstream agent was dispatched as a lean iteration — the fourth documented time this exact silent-drop failure mode has hit this session (`docs/goal.md`'s own loop-mechanics note already names iters 2, 6, 8; this is the fourth), and iter-35's binding "Do not redo" note explicitly required any such drop to be surfaced, which nobody did; (2) J-13's sole acceptance screenshot, `UT-J-13-rotation-both-directions.png`, is a 1683×1260 image with exactly one distinct colour across all 2.12M pixels — a failed capture, measured (not eyeballed) by the evaluator per the iter-36 lesson on never crediting a screenshot from its filename. The evaluator's own binding next-step, carried verbatim into `iteration-state.md`'s "Do not redo" block, names this a **closing round with no new feature work**: (1) genuinely run the full checking team, proven by the presence of the four full-only artifacts, never a marker; (2) retake the rotation screenshot as a passenger; (3) replay the J-13 golden, which was written at 13:35 — five minutes after the 13:30 replay run — and has therefore never actually executed. Per `docs/goal.md`'s own loop-mechanics rule ("`Depth: full` must never silently become `lean`… inability to run the required full-depth lanes MUST be surfaced explicitly and MUST NOT silently fall back to `lean`"), this iteration must produce hard evidence that the full lanes ran: `docs/handoffs/goal-market-compass-iter-37-audit.md`, `reports/qa/goal-market-compass-iter-37-qa.md`, `reports/phase-goal-market-compass-iter-37-ux-regression.md`, and `reports/phase-goal-market-compass-iter-37-closure-verdict.md` must all exist on disk — `.steps/*.done` markers are NOT a depth signal (iter-34 lesson) and must not be treated as one.

Two small, already-identified robustness repairs ride along per the evaluator's explicit "carry along, never a round of their own" instruction: `test_manifest_invariants.py`'s TC-24 fixture (line ~933) sets HPE's risk score to `58.9`, below the `60.0` risk_max_score ceiling, so the row actually *clears* the risk qualifier while its own comment claims it "fails BOTH qualifiers" — the iter-35 lesson on multi-condition fixtures applies directly (a fixture that doesn't isolate each failing condition is green and blind). Separately, `compass.py`'s `_assert_disposition_predicate` (added at iter-35 for J-12, currently two bare `assert` statements guarding that `below_selection_floor`/`excluded_by_cap` labels are truthful by construction) can be silently stripped by Python's `-O`/`-OO` flag, defeating the guard's entire purpose; converting the two `assert` statements to explicit raises fixes this without touching the predicate's logic or any served value.

Depth is `full` because the prior verdict was `ESCALATE` — mandatory per this session's own repeated-depth-drop history, with no exception available. Target selection follows the evaluator's binding next-step and the "Do not redo" block verbatim (priority rubric: an evaluator-issued closing instruction on an already-passing journey's outstanding verification debt outranks manufacturing new scope from a journey list that currently has zero FAILING/PARTIAL entries). Required-still-passing is widened to all twelve other Must-have journeys, consistent with the framework's own guidance to widen the regression set to a full pass after an ESCALATE — this also refreshes every golden script and catches selector drift.

## IN SCOPE

### Backend
- [ ] `apps/backend/tests/test_manifest_invariants.py` TC-24 fixture (`test_tc24_leadership_min_score_is_the_only_gate_regardless_of_qualifiers`, ~line 933): raise the HPE row's risk score above the `compass.selection.risk_max_score` (60.0) ceiling — currently `58.9`, which passes — so the row genuinely fails BOTH the entry (`21.5` < `70.0`) and risk qualifiers as the test's own comment claims, while its leadership score (`92.7`) still clears the `80.0` floor unchanged.
- [ ] `apps/backend/app/engine/compass.py`'s `_assert_disposition_predicate` (the two `assert` statements guarding `below_selection_floor` / `excluded_by_cap` truthfulness): replace each bare `assert cond, msg` with an explicit `if not cond: raise <Error>(msg)` so the guard cannot be silently removed by `-O`/`-OO`. No change to the predicate's logic, inputs, or any computed/served value — output must be byte-identical for every existing fixture and for a live `/api/compass` read.
- [ ] Add a unit test proving the converted guard still raises when invoked under `-O` (assertions stripped) against a deliberately-constructed cohort row that violates the predicate.

### Frontend
None — J-13's Leadership rotation UI is already built and is binding "Do not redo"; no `.tsx` file changes this iteration. The only frontend-adjacent activity is a fresh, honest screenshot capture of the already-shipped panel via the genuinely-run full-depth QA/ux-regression lanes.

### New user-facing capability
None — closing/hardening round only.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None — same rendered page, same DOM, same served fields. This round changes no UI code; it only proves (with a real, measured screenshot and a genuinely-run visual-change review) that the panel J-13 already shipped renders correctly.

### Product surface delta
None — this iteration is process/evidence integrity plus two backend robustness repairs, not a product change.

### Blueprint conformance
No new surfaces. J-13's canonical home stays `/` — Leadership rotation section (Today), already registered in `runs/goal-session-market-compass/state/blueprint.md`.

### Data-contract additions
None. The guard-statement conversion touches no served field, computing module boundary, or endpoint — `_assert_disposition_predicate` is an internal correctness check inside the already-registered `evaluate_selection`/`build_manifest_payload` producer; it adds, moves, or recomputes no Data Contract value. The fixture fix touches only test code.

## OUT OF SCOPE

- Any change to `compass.selection.*` threshold VALUES, `evaluate_selection`'s membership/ordering logic, or J-12's disposition vocabulary — J-12 is CLOSED (binding "Do not redo").
- Any change to `session_delta.rotation` computation, `_rotation_kind`, `_attach_rank_direction_words`, or any other J-13 product logic — J-13's product work is DONE (binding "Do not redo").
- Any touch to `warmup.py` / `prices.py` — J-09 stays closed (binding "Do not redo").
- Any mutation, relabeling, re-hashing, or deletion of a stored `next_session_manifests` row or export file (AG-12/AG-17) — v1..v9 (and every other prior version) keep their bytes exactly.
- The third pre-existing `assert` in `compass.py` (`"expected exactly one gating qualifier check…"`) — confirmed via `git blame` to be a different, unflagged check; not one of the "two guard statements" the evaluator named across iters 35-36. Leave untouched this round.
- J-04's screenshot crop fix (18 rounds owed) and the eight journeys' owed `[NEW]`-flagged walkthrough recordings — evidence-only work, never a round's purpose (binding "Do not redo").
- The five older non-blocking owner questions (J-06 "underlying run unavailable" wording; J-01's first two test steps; empty "next-session focus" acceptability; MNST recovery-list membership; 12-August "rebuilt" note) and the other carried items (pre-existing red `test_no_magic_numbers.py` failures on 3 untouched files; iteration-23 throwaway copy, 7.8 GB; `apps/frontend/.next-verify/` tracked in git; J-01/J-04 automatic re-check assertion gaps; the rotation-panel-vs-what-changed-list row-count owner question) — none is this round's purpose.

## DEFINITION OF DONE

- [ ] J-13 passes via browser-qa-agent with a **non-blank** acceptance screenshot for the Leadership rotation panel (verified by measuring distinct pixel colours, e.g. `PIL.Image.getcolors()` — a single-colour result is a failed capture, per the iter-36 lesson)
- [ ] The four full-depth-only artifacts exist on disk: `docs/handoffs/goal-market-compass-iter-37-audit.md`, `reports/qa/goal-market-compass-iter-37-qa.md`, `reports/phase-goal-market-compass-iter-37-ux-regression.md`, `reports/phase-goal-market-compass-iter-37-closure-verdict.md`
- [ ] `journey-scripts/J-13.json`'s file mtime is strictly earlier than this iteration's replay run, and the replay lane's results file records J-13 as `PASS` (not merely present on disk)
- [ ] Required-still-passing journeys J-01..J-12 remain green (deterministic replay + LLM fallback) with 0 FAIL, 0 skipped
- [ ] No anti-goal violation introduced (AG-8, AG-11, AG-12, AG-15, AG-17 re-verified given the `compass.py` touch)
- [ ] `test_manifest_invariants.py` TC-24's HPE fixture genuinely fails both the entry and risk qualifiers (risk score raised above 60.0); unit tests pass with no regressions
- [ ] The two converted guard statements in `_assert_disposition_predicate` raise unconditionally, including under `python -O`, proven by a new unit test
- [ ] Dev handoff written at `docs/handoffs/goal-market-compass-iter-37-dev.md`

## TESTING REQUIREMENTS

- Browser: J-13 (full re-verification with a real, measured screenshot); regression smoke across J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10, J-11, J-12.
- Unit/integration: `test_manifest_invariants.py::test_tc24_leadership_min_score_is_the_only_gate_regardless_of_qualifiers` (corrected HPE fixture); a new test proving `_assert_disposition_predicate` raises under `-O`; `test_no_magic_numbers.py` continues to pass for `compass.py` (no new inline literal introduced by the guard conversion).
- Error cases: a comparison-cohort row deliberately constructed to violate the disposition predicate must raise a real, non-optimizable error, not silently pass.

Test-first contract scenarios:

- TC-1: given the corrected `test_manifest_invariants.py` TC-24 fixture (HPE risk score raised above `60.0`, entry score unchanged at `21.5`), when `evaluate_selection` runs the test, then the HPE row's qualifier checks show `entry_min_score.met == False` AND `risk_max_score.met == False` (both genuinely fail), while HPE's `selection_disposition` is not `below_selection_floor` (leadership `92.7` clears the `80.0` floor).
- TC-2: given a comparison-cohort row deliberately constructed in a new unit test to violate `_assert_disposition_predicate`'s invariant (e.g. a row labeled `below_selection_floor` with `leadership_score` above the floor), when the function is called under a Python interpreter invoked with `-O` (assertions stripped), then it still raises a real exception rather than returning silently.
- TC-3: given J-13's Leadership rotation section rendered at the frontier as-of (`2026-08-12`) in a real browser, when browser-qa-agent captures `UT-J-13-rotation-both-directions.png` (or its iter-37 equivalent), then the resulting image is NOT single-colour (measured via pixel-colour count, comparable file size to sibling captures in the same evidence directory) and visibly shows both a labelled "gaining" side and a labelled "losing" side with at least one row each.
- TC-4: given `journey-scripts/J-13.json`, when the deterministic replay lane runs this iteration, then the golden's file mtime is strictly earlier than the replay run's start timestamp and the merged results file records J-13 as `PASS`.
- TC-5: given this spec's `**Depth:** full` line, when the engine dispatches iteration 37, then `runs/goal-market-compass-iter-37/depth-dispatched` reads `full`, and all four full-only artifacts named in DEFINITION OF DONE exist on disk with non-trivial content (not empty stubs).
- TC-6: given J-01 through J-12's stored goldens and the current `/api/compass`-served payload, when the full regression replay runs this iteration, then all twelve journeys report `PASS` with 0 FAIL and 0 skipped in the merged results file.
- TC-7: given the `next_session_manifests` table's rows for every existing `(as_of, version)` pair, when this iteration's two backend changes land, then every pre-existing row and export file remains byte-identical (AG-12) — confirmed by unchanged md5 checksums pre- vs post-iteration.

## NOTES

- **Lesson applied (iter-36, twice):** never credit `UT-J-13-rotation-both-directions.png` (or any acceptance screenshot) from its filename or a PASS row alone — measure it (distinct pixel colours / file size vs. siblings) before citing it as evidence. Also check `journey-scripts/*.json` mtimes against the replay run's start time before crediting coverage — a golden written after the replay it's meant to cover has never executed.
- **Lesson applied (iter-34):** `.steps/*.done` markers are NOT a depth signal (only the lean lane writes them); verify full-depth dispatch by the presence of the four full-only artifact FILES and by `iter-37/depth-dispatched` / the trace's dispatch-args phrasing, never by marker absence or presence.
- **Lesson applied (iter-35):** a multi-condition gate's test fixture must isolate each condition — this is exactly what the HPE risk-score fix restores for TC-24 (currently confounded: risk passes when the comment says it should fail).
- **Session history note (not an instruction to the engine):** `Depth: full` has silently become `lean` four times in this session (iters 2, 6, 8, 36) despite an explicit spec line and a binding "surface any drop" instruction each time. This spec cannot itself declare `Depth enforcement: required` or `Maintenance isolation: required` — those are operator-only lines (see CLAUDE.md / goal-decomposer agent instructions on anti-pattern 25) — so if this recurs a fifth time, that is a fact for the evaluator to surface and, if the human judges it necessary, for the human to address via `CHAIN_REQUIRE_FULL_DEPTH` on the next invocation. (A prior session note recorded this session had that flag deliberately turned off for a now-resolved, unrelated STALLED condition at iter 23; whether it should be re-armed for this distinct, recurring failure mode is the human's call, not this spec's.)
- No new Evidence Claim, referee entry, or forward-return code is touched — the post-decompose referee gate passes automatically per `docs/goal.md`'s loop mechanics.
