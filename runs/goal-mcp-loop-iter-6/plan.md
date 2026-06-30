# goal-mcp-loop-iter-6 Execution Plan

> **Iteration type:** verification-integrity / **harness-only** fix. No product feature, no
> `apps/` change. The goal (decision-quality loop) is blocked from GOAL_ACHIEVED *only* because the
> canonical `browser-qa-agent` lane has not run for 2 iterations and the auditor for 3. This iteration
> repairs the four harness defects that abort the pipeline before those stages, so J-04 flips
> `partial → passing` and all five journeys are re-verified through the session-standard canonical lane.

> **Goal alignment:** Confirmed. `docs/goal.md` success criteria are already met in code (ledger holds
> 2 referee-certified PASS entries; every journey feature is built). The blocker is verification plumbing,
> not capability. This iteration advances the goal by restoring the verification standard. No scope creep —
> it is bounded to four named defects in `scripts/automation/**` with **zero `apps/` diff**.

## What to Build

Fix four harness defects (all confirmed in `runs/goal-session-mcp-loop/engine.log` at the iter-5 death
points `04:40:01` and `04:43:47`):

- **Defect #1 — `ui-impact-phase.sh` phantom success (load-bearing, same-run).** On agent rc==0 the script
  echoes "Done. Reports:" (L107–109) without verifying the artifacts exist; the stub fallback (L100–105)
  only fires on rc≠0. Add an rc==0 post-condition: if either `$USER_VISIBLE` or `$UI_SURFACE_MAP` is
  missing/empty, call `write_failed_artifact_stub` for both and `exit` non-zero — fail loudly at the source
  instead of a phantom "Done." that lets ui-test-design abort the whole Branch-UI chain.
- **Defect #2 — `ui-test-design-phase.sh` symmetric guard (defense-in-depth).** Add the same rc==0
  post-condition for its two outputs (`$UI_TEST_PLAN`, `$WHAT_TO_CLICK`). **Placement matters:** put it
  AFTER the existing signal-exit guard (L108–111) and the rc≠0 stub branch (L113–118), right before the
  final "Done." echo — so signal semantics (anti-pattern #20) are preserved; only `_utd_rc==0`-with-missing-file
  becomes a stub+non-zero.
- **Defect #3 — invalid-step abort (load-bearing, same-run).** `run-phase.sh:648` calls
  `update_status … "post_dev_parallel_complete"`, a value absent from the `PhaseStep` enum
  (`lib/verdicts.py` L91+), so `update_status` returns 1 and aborts the run before the sequential
  Step 4–7 retries and the auditor. **Primary fix (effective THIS run): register
  `POST_DEV_PARALLEL_COMPLETE = "post_dev_parallel_complete"` in the `PhaseStep` enum in
  `lib/verdicts.py`** — verdicts.py is a fresh subprocess per call, so the already-loaded L648 call in the
  running parent will now validate and the run continues. Also verify the new enum value doesn't break the
  `CURRENT_STEP → SKIP_*` mapping on a future resume (treat it like the post-fanout/`browser_qa_complete`
  checkpoint).
- **Defect #4 — unconditional SKIP flips (next-run robustness).** `run-phase.sh:645–647` set
  `SKIP_UI_IMPACT/SKIP_UI_TEST_DESIGN/SKIP_BROWSER_QA=true` even when `fanout_rc≠0`. Gate each on its
  artifact existing (e.g. only `SKIP_BROWSER_QA=true` when `reports/phase-${PHASE}-ui-test-results.md`
  exists) so a soft-failed fanout falls through to the sequential retry blocks. This is correct and required,
  but **its effect lands on the next dispatch/resume**, not mid-run (editing the running parent is unreliable).

**Same-run-effect strategy (critical for the developer):** `run-phase.sh` is the running parent of this
very iteration; bash tracks position by byte offset, so mid-run edits to it are unreliable. The two
load-bearing fixes (#1, #3) live in components re-invoked as **fresh subprocesses each step** — the child
script `ui-impact-phase.sh` and `lib/verdicts.py` — and take effect this run. With #1 fixed the fanout's
Branch-UI chain runs ui-impact → ui-test-design → browser-qa to completion in-fanout (producing the
canonical `…-ui-test-results.md`); with #3 fixed the post-fanout status update no longer aborts, so
ux-regression → auditor → closure proceed. #2 and #4 are robustness whose full effect may land next dispatch.

## Agents Required
- developer: yes — apply the four `scripts/automation/**` fixes (no `apps/` change), run the harness/unit
  checks, write the dev handoff. (Framework has a single `developer` agent; there is no separate
  `backend-data`/`frontend-ux` agent. No frontend-code work exists this iteration — the frontend is frozen.)

## Frontend Present
Frontend Present: yes

> `yes` is set **only** so `qa-phase.sh` does NOT skip the Chrome MCP / canonical `browser-qa-agent` lane —
> running that lane is the entire point of this iteration. It is **not** a request for UI code: the frontend
> is frozen and exercised verbatim. The downstream **canonical `browser-qa-agent` lane** is load-bearing;
> the QA agent's parallel Chrome MCP lane does NOT substitute (session standard).

## Files to Create/Modify
- `scripts/automation/ui-impact-phase.sh` — modify: add rc==0 post-condition (defect #1, same-run lever).
- `scripts/automation/ui-test-design-phase.sh` — modify: add rc==0 post-condition after the signal guard (defect #2).
- `scripts/automation/lib/verdicts.py` — modify: add `POST_DEV_PARALLEL_COMPLETE` to the `PhaseStep` enum (defect #3, same-run lever).
- `scripts/automation/run-phase.sh` — modify: L645–647 gate SKIP flags on artifact existence (defect #4); optionally align L648 to a valid step (robustness — not the same-run lever).
- `docs/handoffs/goal-mcp-loop-iter-6-dev.md` — create: dev handoff (files changed, tests run, zero-`apps/`-diff proof).

> Produced downstream by the pipeline, **not the developer** (do not pre-write): the canonical
> `reports/phase-goal-mcp-loop-iter-6-ui-test-results.md` (browser-qa-agent lane) and
> `docs/handoffs/goal-mcp-loop-iter-6-audit.md` (auditor). The fixes above are what unblock them this run.

## UI Evolution
- New user-facing capability: **None.** Frontend frozen; product is byte-identical to iter-5. The user's
  *indirect* gain is that all five evidence journeys are re-proven through the canonical lane and J-04 flips
  `partial → passing`.
- New information displayed: None. No new surface, no new value, no new endpoint.
- New user actions: None.
- UI surface changes: None (frozen).
- Navigation changes: None.

## Visual Requirements
No new UI is built. The existing, frozen surfaces are re-captured with **fresh, in-frame** pixels by the
canonical `browser-qa-agent` lane. Guidance for that lane (from the spec DEFINITION OF DONE):
- Surfaces exercised as-is: `/stocks` (J-01 evidence badges), `/stocks/{ticker}` (J-02 proof panel),
  `/evidence` (J-05 ledger list + claim→backing-surface round-trip), Dashboard `/` + `/evidence` (J-04 regime/phase).
- **J-02 capture:** the **expanded** proof panel — out-of-sample test result + control comparison
  (vs SPY/QQQ/sector-ETF/random) + certified-claim id + registration date — **scrolled into frame**
  (standing iter-3 below-the-fold lesson; not just the score cards).
- **J-04 capture:** Dashboard regime/phase observed, then the Breakout-watch claim on `/evidence` shown
  **scoped to and labeled with its regime** ("Regime: Risk-on"), scrolled into frame.
- **J-05 capture:** the round-trip (claim → backing surface → back) as a **DISTINCT** screenshot, not an
  md5 byte-duplicate of the `/evidence` list frame (iter-5 produced an identical dup).
- States: live data only; no new loading/empty/error treatment to add.

## Key Test Scenarios
- After the fix, `ui-impact-phase.sh` and `ui-test-design-phase.sh` **fail loudly** (non-zero + stub written)
  when the agent returns rc==0 but the expected artifact is missing/empty — never a phantom "Done."
- `verdicts.py validate-step post_dev_parallel_complete` exits 0; the post-fanout `update_status` advances the
  checkpoint and does **NOT** abort the run.
- A soft-failed fanout (`fanout_rc≠0`) leaves the relevant `SKIP_*` flags `false` so the sequential Step 4/5/6
  retry blocks re-run the missing steps.
- `./scripts/automation/run-evals.sh` (offline harness eval suite) remains **green** — no regressions.
- **Canonical lane (load-bearing):** `reports/phase-goal-mcp-loop-iter-6-ui-test-results.md` exists,
  `browser_checks_run=true`, is **not** all-SKIP, and carries fresh canonical UT-* for J-01…J-05 with the
  J-02/J-04/J-05 capture specifics above. **J-04 passes**; J-01/J-02/J-03/J-05 stay green.
- `docs/handoffs/goal-mcp-loop-iter-6-audit.md` exists with **PASS** or **PASS_WITH_GAPS**.
- **Zero `apps/` diff** (git-verified: `git diff --name-only -- apps/` is empty); the iter-5
  `scripts/start-frontend.sh` port-free fix is retained; harness edits confined to `scripts/automation/**`.
- No anti-goal violation; displayed numbers byte-match the certified-claims ledger / engine for the same
  as-of date; ledger unchanged at 2 PASS entries (no `## Evidence Claim` block → post-decompose gate auto-passes).
