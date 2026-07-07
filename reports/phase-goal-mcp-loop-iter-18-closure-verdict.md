# Phase goal-mcp-loop-iter-18 — Closure Verdict

**Phase:** goal-mcp-loop-iter-18
**Date:** 2026-07-07
**Written by:** phase-closure-auditor

---

**Verdict:** CLOSURE-FAIL

<!-- CLOSURE-FAIL: One or more blocking issues prevent completion -->

---

## Standard Pipeline Gate Checks

| Artifact | Status | Verdict |
|----------|--------|---------|
| Review report (`reports/reviews/goal-mcp-loop-iter-18-review.md`) | exists | PASS_WITH_NOTES |
| QA report (`reports/qa/goal-mcp-loop-iter-18-qa.md`) | exists | PASS |
| Audit report (`docs/handoffs/goal-mcp-loop-iter-18-audit.md`) | exists | PASS_WITH_GAPS |

All three standard gates nominally clear the bar in isolation. **This is exactly the situation this gate
exists to catch**: none of the three reconciled their own conclusions against the independently-produced
`reports/phase-goal-mcp-loop-iter-18-ux-regression.md` (verdict **UX-REGRESSION-FAIL**, dated 2026-07-07
07:47, i.e. *before* the audit report was written at 07:59), which documents a confirmed, reproducible,
unfixed regression sitting in the very evidence folder QA cites as proof of its own PASS. See Blocking
Issues below.

---

## UI Visibility Artifact Checks

| Artifact | Exists | Non-Empty | Non-Vague | Status |
|----------|--------|-----------|-----------|--------|
| implementation-summary.md | yes | yes (106 lines) | yes | OK |
| user-visible-changes.md | yes | yes (49 lines) | yes | OK |
| ui-surface-map.md | yes | yes (57 lines) | yes | OK |
| ui-test-plan.md | yes | yes (711 lines) | yes | OK |
| ui-test-results.md | yes | yes (17 lines) | **NO — non-execution stub** | **VAGUE / BLOCKING** |
| what-to-click.md | yes | yes (73 lines) | yes | OK |

`reports/phase-goal-mcp-loop-iter-18-ui-test-results.md` — the canonical browser-qa-agent deliverable —
contains only an auto-generated notice: `"Status: SKIPPED — agent did not produce this artifact"` /
`"browser-qa-phase.sh Claude CLI invocation exited with code 70 without flushing the results file."` It
carries zero test execution content of its own. This is not a "backend-only, N/A" stub (Frontend Present
is `yes` and the phase is explicitly frontend-heavy); it is an admission that the canonical lane crashed
before writing its report.

Independently reconstructing what actually happened from disk (not taking the stub or the QA report's
completion claim at face value):
- The evidence directory `reports/qa/goal-mcp-loop-iter-18-evidence/` contains **29 screenshots** with
  `UT-`-prefixed names matching `ui-test-plan.md`'s UT-01..UT-29 test IDs, timestamped 2026-07-06 23:44
  through 2026-07-07 00:49 — real execution did happen, extensively, before the crash.
- The task tracker (checked live, not from a stale snapshot) shows task **#18 "Watchlist tests" still
  `in_progress`** and **#19–#22 `pending`** ("Backtest + global as-of switcher tests", "Homepage anti-goal
  sweep", "golden replay scripts", and **"Write final UI test results report"**) — the run stopped before
  ever reaching its own report-writing step, consistent with the stub's exit-code-70 story.
- The stub is timestamped **2026-07-07 05:34:55** — hours *after* both the review (23:12) and QA (23:18)
  reports on 2026-07-06, and after the last UT screenshot (00:49) — so the canonical lane kept running
  (or hung) for hours past its last useful output before finally erroring out.

---

## Cross-Reference Checks

- [x] user-visible-changes lists ≥1 specific capability — yes (chart range toggle, staleness diagnostic, broadened watchlist acceptance, regenerated evidence ledger, etc.)
- [x] ui-surface-map has specific route/component entries — yes (`/stocks/{ticker}` `ChartRangeControl`, `/data` `UniverseDiagnosticPanel`, etc., not "the whole app")
- [x] ui-test-plan has specific steps with exact actions and expected results — yes (29 UT-numbered cases, each with numbered steps and precise expected values, e.g. exact dates/counts)
- [ ] **ui-test-results shows execution evidence (or SKIPPED with documented reason) — FAILS.** The file itself shows no execution evidence; the *reason* given (CLI stream error) is real, but the practical effect is that the canonical lane's findings — including a confirmed crash it captured — never reached a written report and were silently dropped from the phase's official record.
- [x] what-to-click has ≥3 numbered steps with exact expected outcomes — yes (10 steps)
- [ ] **implementation-summary claims are consistent with ui-test-results evidence — FAILS.** Neither `implementation-summary.md` nor `reports/qa/goal-mcp-loop-iter-18-qa.md` nor `runs/goal-mcp-loop-iter-18/status.json` discloses the leaderboard-sort crash, even though evidence of it (`UT-21-fail-crash.png`) sits in the same evidence folder QA's own report cites as support for "Zero blockers."

---

## Blocking Issues

1. **Confirmed, unfixed regression: the `/stocks` leaderboard crashes to a full blank page when the user sorts by "Sector."**

   Independently verified, not just taken from the ux-regression report:
   - `apps/frontend/app/stocks/page.tsx:93` — `sector: (a, b) => a.sector.localeCompare(b.sector),` has no
     null guard.
   - `apps/frontend/lib/api.ts:279` — `sector: string;` is typed non-nullable, but this iteration's own
     backend change (`scoring.py:377`, `cfg.stock_sectors.get(ticker)`) now legitimately returns `sector:
     null` for names outside the legacy ~122-symbol sector map — **422 of 541 rows (≈78%)** per the dev
     handoff's own re-verification.
   - `git diff HEAD --stat -- apps/frontend/app/stocks/page.tsx` is empty — the file is byte-unmodified this
     iteration; the code didn't change, but the data contract flowing into it did, and nothing re-validated
     the old comparator against the new shape.
   - No `error.tsx` or `global-error.tsx` exists anywhere under `apps/frontend/app/` (confirmed by direct
     search) — so the uncaught `TypeError` (`null.localeCompare is not a function`) is not contained; it
     wipes the entire page, including the sidebar and all navigation.
   - I opened `reports/qa/goal-mcp-loop-iter-18-evidence/UT-21-fail-crash.png` directly: it shows exactly
     that — a blank dark screen reading only *"Application error: a client-side exception has occurred (see
     the browser console for more information)."*
   - This is test case **UT-21** in `ui-test-plan.md` ("Sector column sort and filter handle rows with no
     sector without crashing (regression)," P2) — a test written specifically to catch this exact failure
     mode, which ran, failed, and was captured with `-fail-` in its own filename.
   - `/stocks` is the product's single most prominent page (one click from home) and sector-sort has been a
     live journey since iter-2. This is a clear, confirmed regression in a prior user journey, caused
     directly by this iteration's own data-basis change — not a hypothetical or an environment artifact.
   - **Not disclosed** as a Known Issue anywhere in the dev handoff, the review report, or the QA report.

   **Remediation:** Harden `SORT_COMPARATORS.sector` in `apps/frontend/app/stocks/page.tsx:93` (e.g.
   `(a, b) => (a.sector ?? "").localeCompare(b.sector ?? "")`) and the `sectors` filter-vocabulary memo at
   lines 355–357 (filter out `null`/render an explicit "Unassigned" bucket instead of a blank/`null`
   dropdown entry); update `apps/frontend/lib/api.ts:279` to `sector: string | null` so the type system
   reflects the real contract. Re-run UT-21 in the browser-qa lane against `/stocks` with the broadened
   pool loaded (click the Sector header, then open the filter dropdown) and confirm no crash before
   re-closing this iteration.

2. **The canonical browser-qa-agent lane never completed — its required deliverable is a stub, and the P1 anti-goal sweep is only partially executed.**

   `reports/phase-goal-mcp-loop-iter-18-ui-test-results.md` is a non-execution stub (see UI Visibility
   Artifact Checks above). Per the live task tracker, Watchlist negative-path tests (unknown/duplicate
   ticker rejection), the Backtest as-of-floor verification, and — most importantly — **three of four
   quadrants of the P1 anti-goal sweep** (no buy/sell/price-target language anywhere in the app; `docs/goal.md`
   marks this critical) never ran. Evidence in the same folder (`UT-03-still-loading-check.png`: "Backend
   unavailable — Dataset coverage could not load from the API") plus the fact that neither backend
   (`:8255`) nor frontend (`:3255`) currently responds suggests the dev backend went down mid-run
   (~2026-07-07 00:45) and was never recovered.

   **Remediation:** Confirm backend + frontend are both up and *staying* up, then re-run
   `./scripts/automation/browser-qa-phase.sh goal-mcp-loop-iter-18` to completion so a real
   `reports/phase-goal-mcp-loop-iter-18-ui-test-results.md` is produced — covering the untested Watchlist
   negative paths, Backtest as-of floor, and the full four-quadrant anti-goal sweep (UT-29) — and so UT-21
   is re-verified against the fix in Issue 1 above.

3. **Self-reported completion claims contradict the pipeline's own evidence folder.**

   `runs/goal-mcp-loop-iter-18/status.json` ("Zero blockers... All 18 functional test cases passed... Ready
   for auditor/release") and `reports/qa/goal-mcp-loop-iter-18-qa.md` ("Verdict: PASS," "No blockers
   identified") both assert full, clean completion. Neither reconciles against
   `reports/qa/goal-mcp-loop-iter-18-evidence/UT-21-fail-crash.png` sitting in the exact evidence directory
   both artifacts point to — a screenshot QA's own narrower TC-01..TC-18 suite never tested for (QA's
   functional test plan does not include a sector-sort case) but that the more thorough canonical UT-plan
   did, and failed.

   **Remediation:** Once Issues 1–2 are resolved, have QA re-run and reconcile `status.json` and
   `goal-mcp-loop-iter-18-qa.md` against the completed evidence set — do not let a narrower, independently-
   authored functional test table stand in as "the canonical browser-qa lane" in the phase's status record.

4. **The post-QA audit did not incorporate the ux-regression-reviewer's findings.**

   `docs/handoffs/goal-mcp-loop-iter-18-audit.md` (written 2026-07-07 07:59:59) post-dates
   `reports/phase-goal-mcp-loop-iter-18-ux-regression.md` (written 07:47:11, verdict **UX-REGRESSION-FAIL**)
   but never mentions it, the `/stocks` sector-sort crash, or the incomplete canonical lane. Its own "Test
   Findings" section (T1/T2) independently spotted looseness in the QA report and one blank screenshot, but
   stopped short of cross-referencing the evidence folder against the sharper, already-published
   ux-regression report sitting alongside it. This is why the audit reached PASS_WITH_GAPS on a phase that,
   per its own evidence, ships an unfixed full-page crash on its most-visited page.

   **Remediation:** Re-run the auditor pass after Issues 1–3 are resolved, with an explicit instruction to
   read `reports/phase-{N}-ux-regression.md` and reconcile its verdict before issuing a final audit verdict.

---

## Non-Blocking Notes

These were already correctly identified and documented by the audit as non-blocking; carrying them forward
for visibility, not re-litigating them:

- **F1 (audit):** unconfirmed whether the "Full history" chart viewport for >8-year-history names actually
  plots pre-2018 weekly bars, or only appears to (honest caption/count data says the deep bars are served;
  audit could not confirm live-render behavior with the backend down during the audit). Non-blocking per
  audit; worth a live-browser confirmation on the same pass that fixes Issue 1 above.
- **T1 (audit):** several cells in the QA functional test table record a page-load rather than the specific
  asserted value (e.g. TC-03 backtest floor, TC-08/TC-18 staleness reason, TC-17 NVDA split continuity).
  The audit independently verified the underlying facts were true, so this did not mask a defect, but the
  QA report over-states what its own steps proved.
- **T2 (audit):** `reports/qa/goal-mcp-loop-iter-18-evidence/TC-01-full-history.png` is a 1.7 KB blank frame
  cited as evidence for a claim it does not actually show; the canonical lane's own richer captures
  (`UT-05-full-history-result.png`, `UT-07-full-history.png`) do show the feature working, so this is a
  hygiene miss on one artifact, not a missing capability.
- **Backend suite:** independently corroborated as green to real counts by review, QA, and audit
  (`SUMMARY[fixverify] rc=0` / `SUMMARY[dispatch10] rc=0`, GRAND TOTAL 1364 passed / 0 net failures,
  DO-NOT-EDIT trio byte-unmodified). No concerns here — this closure-fail is entirely about the
  frontend/UI gate.
