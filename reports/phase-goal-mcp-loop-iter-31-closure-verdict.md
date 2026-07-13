# Phase goal-mcp-loop-iter-31 — Closure Verdict

**Phase:** goal-mcp-loop-iter-31
**Date:** 2026-07-13
**Written by:** phase-closure-auditor

---

**Verdict:** CLOSURE-PASS

---

## Standard Pipeline Gate Checks

| Artifact | Status | Verdict |
|----------|--------|---------|
| Review report (`reports/reviews/goal-mcp-loop-iter-31-review.md`) | exists | PASS |
| QA report (`reports/qa/goal-mcp-loop-iter-31-qa.md`) | exists | PASS |
| Audit report (`docs/handoffs/goal-mcp-loop-iter-31-audit.md`) | exists | PASS_WITH_GAPS (accepted class: PASS WITH GAPS) |

None of these were taken on faith — the following load-bearing claims were independently re-run/re-inspected in the actual working tree during this closure audit:

- `cd apps/backend && .venv/bin/python -m pytest tests/test_graveyard.py tests/test_api_graveyard.py tests/test_registry.py -q` → **45 passed**, 0 failed (matches dev/review/QA/audit claims exactly).
- `npx tsc --noEmit` (frontend) → **exit 0**, clean.
- `git diff --stat` against every file named OUT OF SCOPE in the plan (`evidence.py`, `referee.py`, `ledger.py`, `app/mcp/tools.py`, `project-extensions/gates/verify_claim.py`, `config.py`, `config.yaml`) → **empty**, none touched.
- `git status` on all three ledger/registry state files (`certified-claims.jsonl`, `staging-ledger.jsonl`, `pre-registrations.jsonl`) → **empty**, byte-identical, satisfying the DoD's regression-proof item.
- `data-testid` attributes named across the UI artifacts (`research-governance-link-graveyard`, `graveyard-row`, `graveyard-verdict`, `graveyard-permanent`) → confirmed present verbatim in `apps/frontend/app/research/page.tsx` and `apps/frontend/app/research/graveyard/page.tsx`, not just asserted in reports.
- `verdictKindVariant()` in `apps/frontend/app/research/graveyard/page.tsx:152-155` → confirmed to return only `"danger"`/`"warn"`/`"default"`, **never** `"accent"` — the safety-critical anti-goal #1 guarantee (no FAIL/INSUFFICIENT ever styled as "Proven") holds in source, not just in the QA/audit narrative.
- All new files (`apps/backend/app/engine/graveyard.py`, `apps/backend/app/api/graveyard.py`, `apps/frontend/app/research/graveyard/page.tsx`, `apps/frontend/lib/graveyard.ts`) and the `main.py` router wiring (two additive lines, alphabetically placed) → confirmed present exactly as every handoff describes.

---

## UI Visibility Artifact Checks

| Artifact | Exists | Non-Empty | Non-Vague | Status |
|----------|--------|-----------|-----------|--------|
| `reports/phase-goal-mcp-loop-iter-31-implementation-summary.md` | yes | yes (71 lines) | yes — specific features, explicit "None" for backend-only/incomplete items | OK |
| `reports/phase-goal-mcp-loop-iter-31-user-visible-changes.md` | yes | yes (38 lines) | yes — 6 concrete new capabilities, plain language | OK |
| `reports/phase-goal-mcp-loop-iter-31-ui-surface-map.md` | yes | yes (63 lines) | yes — full file classification table + affected-surface table with per-row test guidance | OK |
| `reports/phase-goal-mcp-loop-iter-31-ui-test-plan.md` | yes | yes (512 lines) | yes — 14 fully-specified cases (UT-01…UT-14), exact steps + byte-exact expected values | OK |
| `reports/phase-goal-mcp-loop-iter-31-ui-test-results.md` | yes | yes (174 lines) | yes — real execution evidence; 11 screenshots on disk in `reports/qa/goal-mcp-loop-iter-31-evidence/` with timestamps matching the report | OK |
| `reports/phase-goal-mcp-loop-iter-31-what-to-click.md` | yes | yes (100 lines) | yes — 8 numbered steps, each with an exact expected outcome | OK |

`Frontend Present: yes` (plan.md line 114; phase spec metadata line 10) is honored throughout — none of the six artifacts degrade to an N/A stub, and all six describe the same concrete feature (the `/research/graveyard` page) with mutually consistent detail.

---

## Cross-Reference Checks

- [x] user-visible-changes lists ≥1 specific capability — lists 6 (graveyard page, six-field row detail, "permanent" marker, revisit-protocol panel + row links, lineage deep-link, staging-ledger visibility)
- [x] ui-surface-map has specific route/component entries — `/research/graveyard` (new), `/research` (hub card), `/research/registry` (row anchor), each with `data-testid` and a "what to test" cell — never "the whole app"
- [x] ui-test-plan has specific steps with exact actions and expected results — all 14 cases carry numbered steps and literal expected strings (e.g., `bonferroni ÷1`, exact chip text, exact panel copy) — never "test the form"
- [x] ui-test-results shows execution evidence (or SKIPPED with documented reason) — 11/14 executed with screenshots + live DOM/`eval` measurements; 2 SKIPPED with specific non-workaroundable reasons (UT-10: permission-system denied a live-ledger file rename; UT-11: the Chrome MCP tool exposes no network-throttle action); 1 FAILED (UT-07) with a detailed root-cause writeup, not hand-waved
- [x] what-to-click has ≥3 numbered steps with exact expected outcomes — 8 steps, each with an "Expect:" line
- [x] implementation-summary claims are consistent with ui-test-results evidence — consistent, with one timing caveat documented below (Non-Blocking Note 1)

---

## Blocking Issues

None.

---

## Non-Blocking Notes

1. **UT-07 (P1 happy-path) reads FAIL in the browser-qa-agent's own artifact; the fix that resolves it lives one stage later, in the audit, and I independently confirmed the fix is real.** `reports/phase-goal-mcp-loop-iter-31-ui-test-results.md` records **Browser QA Verdict: FAIL** — clicking a graveyard row's Lineage link correctly navigated to `/research/registry#registration-<id>` but did not auto-scroll to the target row (`window.scrollY` stayed `0`) on client-side (SPA) navigation. `docs/handoffs/goal-mcp-loop-iter-31-audit.md` (finding F1) diagnosed the same root cause, applied a fix (a guarded `useEffect` in `apps/frontend/app/research/registry/page.tsx` that scrolls a `#registration-<id>` hash target into view once rows mount), and re-verified it live (scrollY `584` on the deep-link path vs. `0` before; scrollY `0`/unchanged on the no-hash regression control; `tsc --noEmit` clean; all 45 backend tests still passing). I independently re-read `apps/frontend/app/research/registry/page.tsx:43-58` in the current working tree and confirmed this exact effect is present, matches the audit's description, and is listed in `runs/goal-mcp-loop-iter-31/status.json`'s `changed_files`. This is a genuine, verified fix, not a paper claim.
   The one loose end: `ui-test-results.md` itself was never regenerated to show a clean re-run of UT-07 — read in isolation, that single file still says FAIL. This is not treated as blocking because (a) the audit report is transparent about the timeline ("the historical browser-QA UT-07 FAIL... [was] accurate when written; a browser-QA re-run would now pass UT-07"), (b) the fix is independently confirmed present and correct by this gate, not merely asserted, and (c) the phase-closure-auditor instructions accept an Audit verdict of PASS/PASS WITH GAPS as a passing gate on their own terms. Recommend (non-blocking, matching the audit's own §5(a) suggestion): a follow-up browser-qa-agent pass to record a clean, passing UT-07 evidence frame so the artifact trail is fully self-consistent without requiring a reader to cross-reference the audit report.

2. **UT-10 (missing/empty-ledger empty state) and UT-11 (loading skeleton) were SKIPPED, not executed live in-browser.** Both have specific, non-workaroundable, documented reasons (UT-10: the permission system correctly denied renaming live shared-state ledger files; UT-11: the available Chrome MCP tool has no network-throttle action, confirmed via its own help listing). Both paths are logic-covered by passing backend fixture tests (`test_graveyard.py::test_missing_ledger_files_degrade_to_empty_payload_no_crash`, `::test_empty_ledger_files_degrade_to_empty_payload_no_crash`), and the corresponding frontend components (`GraveyardEmptyState`, `GraveyardSkeleton`) are confirmed wired in `apps/frontend/app/research/graveyard/page.tsx`. The audit (finding F2) classified this as GAP-level, not blocking; I concur — this matches the skill's documented-reason exception for SKIPPED cases, and the analogous "backend unavailable" degraded-render path (UT-09) did pass live, exercising closely related code.

3. **`user-visible-changes.md`'s claim that the Lineage link "lands precisely on that hypothesis's own row... not just the top of the page"** was false at the moment ui-impact-analyst wrote it (drafted before browser QA ran) but is true of the current working tree following the audit's fix (see Note 1). No artifact edit is needed — flagging only so a future reader understands this specific claim is backed by the audit's fix-plus-verification, not by `ui-test-results.md` alone.

4. The UX regression report (`reports/phase-goal-mcp-loop-iter-31-ux-regression.md`) independently flagged the same Lineage-scroll issue under "Broken Capabilities" with verdict **UX-REGRESSION-WARN** — a non-blocking verdict class per this gate's own rules, and superseded by the same audit fix described in Note 1. Its discoverability, prior-journey-regression, and UI/backend-parity sections are all clean with no flags.
