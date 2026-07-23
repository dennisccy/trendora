# Operator evidence — `demo.sh ops-hardening --session-live` walkthrough RUN (2026-07-23)

**Produced by:** the goal-mode operator (pump), per the owner-approved recovery plan (Phase 5).
**Why it matters:** the `[NEW]`-flagged session walkthrough is named in the Acceptance of J-05, J-06
and J-07 ("viewable via `demo.sh ops-hardening --session-live`"), and the iter-12 decomposer proved
no autonomous mechanism produces it — it is owner/operator-run. Until today it had never been run;
the iter-13 and iter-14 evaluators both held journeys `partial` partly on this gap.

## What ran

- Command: `bash scripts/automation/demo.sh ops-hardening --session-live`
  (delegates to `demo-phase.sh ops-hardening --session`, the deterministic Playwright
  session-mode runner over the stored demo scripts).
- When: 2026-07-23, immediately after the iter-14 goal-evaluation, against the live services
  (backend :8255 freshly booted on the post-J-07 code, frontend :3255).
- Result: **exit code 0 — "[demo] Walkthrough complete."** All **7 steps** of the whole-product
  tour executed and their per-step "Notice:" assertions rendered:
  1. (intro/home)
  2. Data Manager honest status — badge "Ready" with a green dot, visible on every page
  3. Run history — a zero-work run explained plainly, not silently marked done
  4. Scanner Runs — real backfilled dates, each opening its stored leaderboard
  5. Wide date range accepted on the backfill form
  6. No range cap — an eleven-year span accepted with no warning or truncation
  7. **Aggregates computed once, at ingest — the summary line lists "forward aggregates" among
     the things refreshed by that run** (the J-07/AG-8 recovery, demonstrated on the live surface)

- Full console transcript retained by the session harness (task output
  `b4wsoddjg.output` in the pump scratchpad); this file is the durable pointer.

## Honest scope

This was a headless operator run proving the walkthrough EXISTS, EXECUTES END-TO-END, and its
step assertions hold against the live product — the "viewable via" acceptance clause. The owner can
re-watch it live at any time with the same command. Whether this closes the walkthrough clause for
J-05/J-06/J-07 is the goal-evaluator's scoring call, not the operator's.
