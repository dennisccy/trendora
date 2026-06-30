# goal-mcp-loop-iter-6 Dev Handoff

**Phase:** goal-mcp-loop-iter-6
**Date:** 2026-06-30
**Agent:** developer
**Status:** complete

## What Was Built

This is a **verification-integrity / harness-only** iteration. No product feature, **zero `apps/` change**.
It repairs four defects in the post-dev verification pipeline that aborted the run before the canonical
`browser-qa-agent` lane and the auditor could execute (root-caused from `runs/goal-session-mcp-loop/engine.log`
death points `04:40:01` and `04:43:47`).

- **Defect #1 — `ui-impact-phase.sh` phantom success (same-run lever).** Added an rc==0 post-condition:
  after the agent returns 0, the script now asserts both `user-visible-changes` and `ui-surface-map`
  reports exist and are non-empty. If either is missing/empty it writes SKIPPED stubs and exits non-zero
  ("fail loud at the source") instead of printing a phantom `[ui-impact] Done.` that lets the next stage
  abort on a missing file.
- **Defect #2 — `ui-test-design-phase.sh` symmetric guard (defense-in-depth).** Added the same rc==0
  post-condition for `ui-test-plan` and `what-to-click`. **Placed AFTER** the existing signal-exit guard
  (exit 130/137/143) and the rc≠0 stub branch, so signal semantics (anti-pattern #20) are preserved — only
  a genuine rc==0-with-missing-file becomes a stub + non-zero exit.
- **Defect #3 — invalid-step abort (same-run lever).** Registered
  `POST_DEV_PARALLEL_COMPLETE = "post_dev_parallel_complete"` in the `PhaseStep` enum in `lib/verdicts.py`.
  `run-phase.sh:649` calls `update_status … "post_dev_parallel_complete"` after the parallel fanout;
  previously this value was not in the whitelist, so `update_status` returned 1 and aborted the run before
  the sequential Step 4–7 retries and the auditor. Because `verdicts.py` is invoked as a fresh subprocess on
  every `update_status` call, this enum edit takes effect **this run** even though `run-phase.sh` is mid-flight.
- **Defect #4 — unconditional SKIP flips (next-run robustness).** `run-phase.sh` post-fanout block now gates
  each `SKIP_UI_IMPACT / SKIP_UI_TEST_DESIGN / SKIP_BROWSER_QA=true` on the corresponding artifact actually
  existing (`-s`), so a soft-failed fanout falls through to the sequential Step 4/5/6 retry blocks instead of
  being silently skipped. Also added a `post_dev_parallel_complete` arm to the resume `CURRENT_STEP → SKIP_*`
  mapping (mirrors `browser_qa_complete`) so the new checkpoint resumes correctly on a future dispatch.

**Same-run-effect strategy (per plan):** the two load-bearing fixes (#1 in the child script
`ui-impact-phase.sh`, #3 in `lib/verdicts.py`) live in components re-invoked as **fresh subprocesses each
step**, so they take effect on this very run. #2 and #4 are robustness whose full effect may land on the
next dispatch/resume (editing the running `run-phase.sh` parent mid-run is unreliable — bash tracks position
by byte offset).

## Files Changed

> Repo layout note: top-level `scripts/` is a **symlink** to `incredible_auto_dev/scripts` (same inode,
> verified), so `git diff` reports these under `incredible_auto_dev/scripts/automation/...`. They are the
> same files the plan refers to as `scripts/automation/...`.

- `scripts/automation/lib/verdicts.py` — added `POST_DEV_PARALLEL_COMPLETE` to the `PhaseStep` enum (defect #3).
- `scripts/automation/ui-impact-phase.sh` — added rc==0 post-condition: missing/empty report → stub + non-zero exit (defect #1).
- `scripts/automation/ui-test-design-phase.sh` — added symmetric rc==0 post-condition after the signal guard (defect #2).
- `scripts/automation/run-phase.sh` — gated post-fanout SKIP flips on artifact existence + added `post_dev_parallel_complete` resume arm (defect #4).
- `scripts/automation/run-evals.sh` — added the TDD tests for the fixes (see Tests Run).

## Tests Run

Command: `./scripts/automation/run-evals.sh`
Result: **60 passed, 0 failed** (exit 0).

New tests added (TDD red → green — confirmed all 3 failed before the fixes, pass after):
1. `verdicts.py validate-step post_dev_parallel_complete` exits 0 (post-fanout checkpoint accepted) + the
   existing negative case (invalid step still rejected) still holds.
2. Structural guard check: both `ui-impact-phase.sh` and `ui-test-design-phase.sh` carry the rc==0 `-s`
   post-condition for their two outputs.
3. Behavioral check: the real `write_failed_artifact_stub` helper writes a stub on a missing artifact and is
   a no-op (content preserved) when the artifact is present.

Additional developer verification (not in the eval suite):
- Extracted and executed the **real guard bytes** from both phase scripts against a temp tree:
  rc==0 + missing artifact → SKIPPED stubs written + exit 1; rc==0 + present artifacts → no-op, exit 0,
  content preserved; mixed (one missing) → fail loud. All passed.
- Defect #4 SKIP-gating: all artifacts present → all `SKIP_*=true`; any artifact missing → that `SKIP_*`
  stays `false` (sequential retry runs). Resume arm: `post_dev_parallel_complete` maps identically to
  `browser_qa_complete`.
- `bash -n` clean on all three modified shell scripts; `verdicts.py` rejects a bogus step.

## Zero-`apps/`-diff proof

- `git diff --name-only -- apps/` → **empty**; `git status --short -- apps/` → empty. `apps/` is a real
  top-level directory with no changes.
- All modifications are confined to the harness (`scripts/automation/**`, tracked as
  `incredible_auto_dev/scripts/automation/**`).
- The iter-5 `scripts/start-frontend.sh` port-free fix was **not touched** (no diff).

## Known Issues

- **Empty-file edge:** `write_failed_artifact_stub` is intentionally a no-op when a file already exists (to
  preserve partial agent output). So if an agent leaves a **0-byte** report (vs. wholly absent), the new
  guard still fails loud (non-zero exit) but does not overwrite the empty file with stub text. The real
  failure mode seen in `engine.log` was a **wholly-absent** file, which the guard fully handles (stub
  written). This nuance is acceptable and faithful to the plan ("missing/empty" → fail loud); I did not
  modify `write_failed_artifact_stub` (out of scope).
- **Full app-stack startup not exercised by the developer.** This iteration changes only harness
  orchestration scripts — no `apps/`, no service-start code. The frontend/backend are frozen and unchanged
  from iter-5. Starting the stack here would risk interfering with the in-progress pipeline's own
  service management (and the corrupt-`.next` hazard, anti-pattern #20). The downstream canonical
  `browser-qa-agent` lane — which this iteration exists to unblock — starts and exercises the frozen
  frontend itself; that is where live UI verification happens.
- **Ledger unchanged:** no `## Evidence Claim` block in the spec, so the post-decompose gate auto-passes and
  the certified-claims ledger stays at its 2 PASS entries. Displayed numbers are unchanged (no recompute).

## Suggested Next Phase

With #1 (ui-impact fail-loud) and #3 (valid checkpoint step) active this run, the fanout's Branch-UI chain
(ui-impact → ui-test-design → browser-qa) should run to completion and the post-fanout `update_status` should
no longer abort — so the canonical `reports/phase-goal-mcp-loop-iter-6-ui-test-results.md` and the
`docs/handoffs/goal-mcp-loop-iter-6-audit.md` should be produced, J-04 should flip `partial → passing`, and
J-01/J-02/J-03/J-05 should re-confirm green. If the canonical lane + auditor still do not run after this fix,
honor the spec's ESCALATION FLAG: treat the session as STALLED and hand the harness to a human rather than
loop a 4th time on the same path.
