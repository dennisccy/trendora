# Iteration 25 — Coherence Audit

**Iteration:** goal-mcp-loop-iter-25
**Date:** 2026-07-09
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Summary

iter-25 is a verification-only recovery pass for the iter-24 REGRESSION (the `mmap_size_bytes: 0` cold-path
OOM fix, already committed at HEAD before this iteration started). Confirmed via
`git diff 0717e7f3c347a9f5ccae938d1b96545f0874bf4c -- . <noise-exclusions>`: the noise-excluded diff is
**completely empty (0 lines)** — no bounded `iter-diff.md` existed, so the full command was run directly.
A separate scoped check (`git diff <snapshot-sha> --stat -- apps/backend apps/frontend config.yaml`) is
also empty, confirming zero source changes anywhere, including `config.yaml` itself (the `mmap_size_bytes: 0`
line at `config.yaml:108` predates this iteration's snapshot and carries an "iter-24 audit" comment). The
only files touched this iteration, per the excluded-path stat, are: `reports/perf-budgets.md` (+84, the
corrected live cold-restart measurement), `runs/goal-session-mcp-loop/state/blueprint.md` (+2, the iter-25
running-log clarification paragraph), `runs/goal-session-mcp-loop/state/project-story.md` (narrative
update), and harness telemetry/trace bookkeeping. This is exactly what the iteration spec
(`docs/phases/goal-mcp-loop-iter-25.md`) declared in scope ("No backend source change" / "No frontend
source change" / "UI surface changes: None"), and what `reports/phase-goal-mcp-loop-iter-25-ui-surface-map.md`
independently corroborates ("Frontend surfaces changed: 0", "Modified components: 0", "Navigation changes: no").
With zero source diff, neither a Part A (Data Contract) nor a Part B (Information Architecture) violation
is structurally possible this iteration — there is no new computation, no new endpoint, no new UI surface,
and no new page/route to check.

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| DB capacity snapshot (`db_file_bytes`/`daily_prices_rows`/`scanner_results_rows`/`forward_returns_rows`) — re-verified cold, not recomputed | OK | No source change (`apps/backend/app/engine/data_manager.py` absent from the diff). `reports/perf-budgets.md`'s new "Cold `/api/data` path" section records the SAME canonical `GET /api/data` `capacity` payload byte-identical cold vs. warm vs. every prior recorded figure in the file (`db_file_bytes 1307414528`, `daily_prices_rows 3293160`, `scanner_results_rows 165755`, `forward_returns_rows 821054`) — a live re-read of the existing single endpoint, not a second computation path. |
| Evidence status / certified-claim (proven-ness) | OK — untouched | No `## Evidence Claim` this iteration (confirmed in the iter spec's metadata); both ledgers stay byte-identical all-FAIL per the spec and the blueprint's iter-25 clarification. Not present in the diff. |
| Every other registered Data Contract row (scores, regime, sectors, themes, forward-return aggregates, research cohorts, index/macro vendor labels) | OK — untouched | Not present in the diff at all; zero backend/frontend files changed. |

No new displayed value is introduced. The blueprint's iter-25 clarification paragraph
(`runs/goal-session-mcp-loop/state/blueprint.md`, appended below the Data Contract table) is itself
additive documentation only — it does not add or alter a Data Contract table row, consistent with the
"no contract change" framing in both the spec and the clarification text itself.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/data` cold-boot request path (re-verification of existing surface, no new page) | OK | Already registered as J-13's canonical home (`/data`, Data Manager nav section) and J-15's storage-card home in `blueprint.md`'s IA homes table — unchanged this iteration. `reports/phase-goal-mcp-loop-iter-25-ui-surface-map.md` confirms "New pages/routes: 0" / "Navigation changes: no"; the sidebar/nav component itself is absent from the diff. |

No new feature/page/route exists this iteration to evaluate for reachability, duplicate-home, or
parallel-shell violations.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- **Carried-forward WARN (not new, not touched by this iteration):** `apps/frontend/components/index-regime-chart.tsx`
  and `apps/frontend/components/major-indexes-card.tsx` are still present in the tree (confirmed via
  filesystem check) and remain dead code first flagged at iter-22, carried at iter-23 and iter-24's
  coherence audits. iter-25's own spec explicitly keeps their deletion out of scope ("Deleting the
  dead-duplicate `index-regime-chart.tsx` / `major-indexes-card.tsx` (coherence-WARN carry-forward) —
  defer to a dedicated tidy iteration"), and the empty source diff confirms neither file was touched —
  correctly deferred, not worsened. Still recommended: delete both in the next tidy-up iteration.
- No formatting-drift or inconsistent-label issues found: this iteration touched no rendered surface, so
  there is nothing new to compare for label/format consistency.
