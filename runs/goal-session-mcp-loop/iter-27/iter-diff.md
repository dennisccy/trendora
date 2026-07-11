# Iteration diff (bounded)

Files changed: 384. Shown in full: 63.

**Excluded paths** (data/lock/binary — content not shown; the secret scanner
still scanned them; Read a file directly if it matters):
- `incredible_auto_dev/tests/judgment/auditor/case-01-clean-pass/tree/reports/qa/goal-afx01-iter-3-evidence/UT-01-summary-mixed.png` (4 diff lines)
- `incredible_auto_dev/tests/judgment/auditor/case-01-clean-pass/tree/reports/qa/goal-afx01-iter-3-evidence/UT-02-summary-empty.png` (4 diff lines)
- `incredible_auto_dev/tests/judgment/auditor/case-02-documented-gap-not-fail/tree/reports/qa/goal-afx02-iter-3-evidence/UT-01-import-success.png` (4 diff lines)
- `incredible_auto_dev/tests/judgment/auditor/case-02-documented-gap-not-fail/tree/reports/qa/goal-afx02-iter-3-evidence/UT-02-import-error.png` (4 diff lines)
- `incredible_auto_dev/tests/judgment/auditor/case-03-qa-green-spec-contradiction/tree/reports/qa/goal-afx03-iter-3-evidence/UT-01-grouped-list.png` (4 diff lines)
- `incredible_auto_dev/tests/judgment/auditor/case-03-qa-green-spec-contradiction/tree/reports/qa/goal-afx03-iter-3-evidence/UT-02-reload-persists.png` (4 diff lines)
- `incredible_auto_dev/tests/judgment/auditor/case-04-paid-service-live-key/tree/reports/qa/goal-afx04-iter-3-evidence/UT-01-backup-badge.png` (4 diff lines)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-01-clean-goal-achieved/tree/reports/qa/goal-fixt01-iter-2-evidence/UT-01-add-item.png` (4 diff lines)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-01-clean-goal-achieved/tree/reports/qa/goal-fixt01-iter-2-evidence/UT-02-mark-done.png` (4 diff lines)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-01-clean-goal-achieved/tree/reports/qa/goal-fixt01-iter-2-evidence/UT-03-filter-open.png` (4 diff lines)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-02-first-failure-continue/tree/reports/qa/goal-fixt02-iter-2-evidence/UT-01-add-item.png` (4 diff lines)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-02-first-failure-continue/tree/reports/qa/goal-fixt02-iter-2-evidence/UT-02-mark-done.png` (4 diff lines)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-02-first-failure-continue/tree/reports/qa/goal-fixt02-iter-2-evidence/UT-03-filter-open-fail.png` (4 diff lines)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-03-regression-broken-journey/tree/reports/qa/goal-fixt03-iter-2-evidence/UT-01-add-item.png` (4 diff lines)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-03-regression-broken-journey/tree/reports/qa/goal-fixt03-iter-2-evidence/UT-02-mark-done-fail.png` (4 diff lines)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-03-regression-broken-journey/tree/reports/qa/goal-fixt03-iter-2-evidence/UT-03-filter-open.png` (4 diff lines)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-04-goal-drift-void-pass/tree/reports/qa/goal-fixt04-iter-2-evidence/UT-01-add-item.png` (4 diff lines)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-04-goal-drift-void-pass/tree/reports/qa/goal-fixt04-iter-2-evidence/UT-03-filter-open.png` (4 diff lines)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-05-secret-committed/tree/reports/qa/goal-fixt05-iter-2-evidence/UT-01-add-item.png` (4 diff lines)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-05-secret-committed/tree/reports/qa/goal-fixt05-iter-2-evidence/UT-02-mark-done.png` (4 diff lines)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-05-secret-committed/tree/reports/qa/goal-fixt05-iter-2-evidence/UT-03-filter-open.png` (4 diff lines)
- `reports/goal-session-mcp-loop-index.html` (41 diff lines)
- `reports/perf-budgets.md` (156 diff lines)
- `runs/goal-session-mcp-loop/engine.pid` (7 diff lines)
- `runs/goal-session-mcp-loop/session.json` (16 diff lines)
- `runs/goal-session-mcp-loop/state/blueprint.md` (13 diff lines)
- `runs/goal-session-mcp-loop/state/project-story.md` (29 diff lines)
- `runs/goal-session-mcp-loop/summary.md` (51 diff lines)
- `runs/goal-session-mcp-loop/telemetry.jsonl` (29 diff lines)
- `runs/goal-session-mcp-loop/trace/.next-step` (7 diff lines)
- `runs/goal-session-mcp-loop/trace/trace.jsonl` (31 diff lines)
- `diff --git areports/demo/goal-mcp-loop-iter-27/step-01.png breports/demo/goal-mcp-loop-iter-27/step-01.png` (4 diff lines)
- `diff --git areports/demo/goal-mcp-loop-iter-27/step-02.png breports/demo/goal-mcp-loop-iter-27/step-02.png` (4 diff lines)
- `diff --git areports/demo/goal-mcp-loop-iter-27/step-03.png breports/demo/goal-mcp-loop-iter-27/step-03.png` (4 diff lines)
- `diff --git areports/demo/goal-mcp-loop-iter-27/step-04.png breports/demo/goal-mcp-loop-iter-27/step-04.png` (4 diff lines)
- `diff --git areports/demo/goal-mcp-loop-iter-27/step-05.png breports/demo/goal-mcp-loop-iter-27/step-05.png` (4 diff lines)
- `diff --git areports/demo/goal-mcp-loop-iter-27/step-06.png breports/demo/goal-mcp-loop-iter-27/step-06.png` (4 diff lines)
- `diff --git areports/demo/goal-mcp-loop-iter-27/step-07.png breports/demo/goal-mcp-loop-iter-27/step-07.png` (4 diff lines)
- `diff --git areports/demo/goal-mcp-loop-iter-27/step-08.png breports/demo/goal-mcp-loop-iter-27/step-08.png` (4 diff lines)
- `diff --git areports/qa/goal-mcp-loop-iter-27-evidence/CRITICAL-backend-wedged-data-page.png breports/qa/goal-mcp-loop-iter-27-evidence/CRITICAL-backend-wedged-data-page.png` (4 diff lines)
- `diff --git areports/qa/goal-mcp-loop-iter-27-evidence/TC-01-stocks-leaderboard.png breports/qa/goal-mcp-loop-iter-27-evidence/TC-01-stocks-leaderboard.png` (4 diff lines)
- `diff --git areports/qa/goal-mcp-loop-iter-27-evidence/TC-07-data-page-initial.png breports/qa/goal-mcp-loop-iter-27-evidence/TC-07-data-page-initial.png` (4 diff lines)
- `diff --git areports/qa/goal-mcp-loop-iter-27-evidence/TC-07-data-page-loaded.png breports/qa/goal-mcp-loop-iter-27-evidence/TC-07-data-page-loaded.png` (4 diff lines)
- `diff --git areports/qa/goal-mcp-loop-iter-27-evidence/TC-07-job-form.png breports/qa/goal-mcp-loop-iter-27-evidence/TC-07-job-form.png` (4 diff lines)
- `diff --git areports/qa/goal-mcp-loop-iter-27-evidence/TC-07-rebuild-section.png breports/qa/goal-mcp-loop-iter-27-evidence/TC-07-rebuild-section.png` (4 diff lines)
- `diff --git areports/qa/goal-mcp-loop-iter-27-evidence/UT-01-data-loaded.png breports/qa/goal-mcp-loop-iter-27-evidence/UT-01-data-loaded.png` (4 diff lines)
- `diff --git areports/qa/goal-mcp-loop-iter-27-evidence/UT-02-checkpoint-start-3of322.png breports/qa/goal-mcp-loop-iter-27-evidence/UT-02-checkpoint-start-3of322.png` (4 diff lines)
- `diff --git areports/qa/goal-mcp-loop-iter-27-evidence/UT-02-completed-ok-322of322.png breports/qa/goal-mcp-loop-iter-27-evidence/UT-02-completed-ok-322of322.png` (4 diff lines)
- `diff --git areports/qa/goal-mcp-loop-iter-27-evidence/UT-02-confirm-dialog-viewport.png breports/qa/goal-mcp-loop-iter-27-evidence/UT-02-confirm-dialog-viewport.png` (4 diff lines)
- `diff --git areports/qa/goal-mcp-loop-iter-27-evidence/UT-02-confirm-dialog.png breports/qa/goal-mcp-loop-iter-27-evidence/UT-02-confirm-dialog.png` (4 diff lines)
- `diff --git areports/qa/goal-mcp-loop-iter-27-evidence/UT-02-job-started.png breports/qa/goal-mcp-loop-iter-27-evidence/UT-02-job-started.png` (4 diff lines)
- `diff --git areports/qa/goal-mcp-loop-iter-27-evidence/UT-02-post-both-runs-stocks.png breports/qa/goal-mcp-loop-iter-27-evidence/UT-02-post-both-runs-stocks.png` (4 diff lines)
- `diff --git areports/qa/goal-mcp-loop-iter-27-evidence/UT-02-post-completion-data-page.png breports/qa/goal-mcp-loop-iter-27-evidence/UT-02-post-completion-data-page.png` (4 diff lines)
- `diff --git areports/qa/goal-mcp-loop-iter-27-evidence/UT-02-post-completion-stocks-page.png breports/qa/goal-mcp-loop-iter-27-evidence/UT-02-post-completion-stocks-page.png` (4 diff lines)
- `diff --git areports/qa/goal-mcp-loop-iter-27-evidence/UT-02-run1-confirm-modal-2.png breports/qa/goal-mcp-loop-iter-27-evidence/UT-02-run1-confirm-modal-2.png` (4 diff lines)
- `diff --git areports/qa/goal-mcp-loop-iter-27-evidence/UT-02-run1-confirm-modal.png breports/qa/goal-mcp-loop-iter-27-evidence/UT-02-run1-confirm-modal.png` (4 diff lines)
- `diff --git areports/qa/goal-mcp-loop-iter-27-evidence/UT-02-run1-initial.png breports/qa/goal-mcp-loop-iter-27-evidence/UT-02-run1-initial.png` (4 diff lines)
- `diff --git areports/qa/goal-mcp-loop-iter-27-evidence/UT-02-run1-ok.png breports/qa/goal-mcp-loop-iter-27-evidence/UT-02-run1-ok.png` (4 diff lines)
- `diff --git areports/qa/goal-mcp-loop-iter-27-evidence/UT-02-run1-started.png breports/qa/goal-mcp-loop-iter-27-evidence/UT-02-run1-started.png` (4 diff lines)
- `diff --git areports/qa/goal-mcp-loop-iter-27-evidence/UT-02-run2-ok.png breports/qa/goal-mcp-loop-iter-27-evidence/UT-02-run2-ok.png` (4 diff lines)
- `diff --git areports/qa/goal-mcp-loop-iter-27-evidence/UT-04-cancel-result.png breports/qa/goal-mcp-loop-iter-27-evidence/UT-04-cancel-result.png` (4 diff lines)
- `diff --git areports/qa/goal-mcp-loop-iter-27-evidence/UT-05-reenabled.png breports/qa/goal-mcp-loop-iter-27-evidence/UT-05-reenabled.png` (4 diff lines)
- `diff --git areports/qa/goal-mcp-loop-iter-27-evidence/UT-05-regime-breakdown.png breports/qa/goal-mcp-loop-iter-27-evidence/UT-05-regime-breakdown.png` (4 diff lines)
- `diff --git areports/qa/goal-mcp-loop-iter-27-evidence/UT-05-running-disabled.png breports/qa/goal-mcp-loop-iter-27-evidence/UT-05-running-disabled.png` (4 diff lines)
- `diff --git areports/qa/goal-mcp-loop-iter-27-evidence/UT-06-UT-07-stocks-sector-sorted.png breports/qa/goal-mcp-loop-iter-27-evidence/UT-06-UT-07-stocks-sector-sorted.png` (4 diff lines)
- `diff --git areports/qa/goal-mcp-loop-iter-27-evidence/UT-06-dashboard.png breports/qa/goal-mcp-loop-iter-27-evidence/UT-06-dashboard.png` (4 diff lines)
- `diff --git areports/qa/goal-mcp-loop-iter-27-evidence/UT-06-regime-breakdown.png breports/qa/goal-mcp-loop-iter-27-evidence/UT-06-regime-breakdown.png` (4 diff lines)
- `diff --git areports/qa/goal-mcp-loop-iter-27-evidence/UT-08-UT-09-evidence-ledger.png breports/qa/goal-mcp-loop-iter-27-evidence/UT-08-UT-09-evidence-ledger.png` (4 diff lines)
- `diff --git areports/qa/goal-mcp-loop-iter-27-evidence/UT-09-evidence-empty-state.png breports/qa/goal-mcp-loop-iter-27-evidence/UT-09-evidence-empty-state.png` (4 diff lines)
- `diff --git areports/qa/goal-mcp-loop-iter-27-evidence/UT-10-AAPL-full-history.png breports/qa/goal-mcp-loop-iter-27-evidence/UT-10-AAPL-full-history.png` (4 diff lines)
- `diff --git areports/qa/goal-mcp-loop-iter-27-evidence/UT-10-aapl-full-history.png breports/qa/goal-mcp-loop-iter-27-evidence/UT-10-aapl-full-history.png` (4 diff lines)
- `diff --git areports/qa/goal-mcp-loop-iter-27-evidence/UT-10-aapl-initial.png breports/qa/goal-mcp-loop-iter-27-evidence/UT-10-aapl-initial.png` (4 diff lines)
- `diff --git areports/qa/goal-mcp-loop-iter-27-evidence/UT-10-aapl-top.png breports/qa/goal-mcp-loop-iter-27-evidence/UT-10-aapl-top.png` (4 diff lines)
- `diff --git areports/qa/goal-mcp-loop-iter-27-evidence/UT-11-membership-timeline-2.png breports/qa/goal-mcp-loop-iter-27-evidence/UT-11-membership-timeline-2.png` (4 diff lines)
- `diff --git areports/qa/goal-mcp-loop-iter-27-evidence/UT-11-membership-timeline-3.png breports/qa/goal-mcp-loop-iter-27-evidence/UT-11-membership-timeline-3.png` (4 diff lines)
- `diff --git areports/qa/goal-mcp-loop-iter-27-evidence/UT-11-membership-timeline-4.png breports/qa/goal-mcp-loop-iter-27-evidence/UT-11-membership-timeline-4.png` (4 diff lines)
- `diff --git areports/qa/goal-mcp-loop-iter-27-evidence/UT-11-membership-timeline-5.png breports/qa/goal-mcp-loop-iter-27-evidence/UT-11-membership-timeline-5.png` (4 diff lines)
- `diff --git areports/qa/goal-mcp-loop-iter-27-evidence/UT-11-membership-timeline-fullpage.png breports/qa/goal-mcp-loop-iter-27-evidence/UT-11-membership-timeline-fullpage.png` (4 diff lines)
- `diff --git areports/qa/goal-mcp-loop-iter-27-evidence/UT-11-membership-timeline.png breports/qa/goal-mcp-loop-iter-27-evidence/UT-11-membership-timeline.png` (4 diff lines)
- `diff --git areports/qa/goal-mcp-loop-iter-27-evidence/UT-12-availability-legend-retry.png breports/qa/goal-mcp-loop-iter-27-evidence/UT-12-availability-legend-retry.png` (4 diff lines)
- `diff --git areports/qa/goal-mcp-loop-iter-27-evidence/UT-12-availability-legend.png breports/qa/goal-mcp-loop-iter-27-evidence/UT-12-availability-legend.png` (4 diff lines)
- `diff --git areports/qa/goal-mcp-loop-iter-27-evidence/UT-15-data-manager-nav.png breports/qa/goal-mcp-loop-iter-27-evidence/UT-15-data-manager-nav.png` (4 diff lines)

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `incredible_auto_dev/scripts/automation/run-benchmark.sh` (147 lines not shown)
- `incredible_auto_dev/scripts/automation/run-judgment-evals.sh` (155 lines not shown)
- `incredible_auto_dev/scripts/automation/run-phase.sh` (66 lines not shown)
- `incredible_auto_dev/scripts/start-backend.sh` (36 lines not shown)
- `incredible_auto_dev/tests/automation/test-benchmark-runner.sh` (491 lines not shown)
- `incredible_auto_dev/tests/automation/test-goal-retro.sh` (334 lines not shown)
- `incredible_auto_dev/tests/automation/test-quota-retry.sh` (114 lines not shown)
- `incredible_auto_dev/tests/automation/test-tmp-cleanup.sh` (133 lines not shown)
- `incredible_auto_dev/tests/judgment/README.md` (192 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-01-clean-pass/case.env` (10 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-01-clean-pass/expected.txt` (7 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-01-clean-pass/notes.md` (38 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-01-clean-pass/source/change.patch` (58 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-01-clean-pass/tree/app.py` (145 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-01-clean-pass/tree/docs/goal.md` (73 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-01-clean-pass/tree/docs/handoffs/goal-afx01-iter-3-dev.md` (36 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-01-clean-pass/tree/docs/phases/goal-afx01-iter-3.md` (46 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-01-clean-pass/tree/reports/qa/goal-afx01-iter-3-qa.md` (62 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-01-clean-pass/tree/reports/qa/goal-afx01-iter-3-test-plan.md` (85 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-01-clean-pass/tree/reports/reviews/goal-afx01-iter-3-review.md` (30 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-01-clean-pass/tree/runs/goal-afx01-iter-3/plan.md` (41 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-01-clean-pass/tree/runs/goal-afx01-iter-3/status.json` (19 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-01-clean-pass/tree/static/app.js` (16 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-01-clean-pass/tree/templates/index.html` (33 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-01-clean-pass/tree/test_items.py` (93 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-02-documented-gap-not-fail/case.env` (10 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-02-documented-gap-not-fail/expected.txt` (7 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-02-documented-gap-not-fail/notes.md` (46 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-02-documented-gap-not-fail/source/change.patch` (133 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-02-documented-gap-not-fail/tree/app.py` (184 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-02-documented-gap-not-fail/tree/docs/goal.md` (74 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-02-documented-gap-not-fail/tree/docs/handoffs/goal-afx02-iter-3-dev.md` (48 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-02-documented-gap-not-fail/tree/docs/phases/goal-afx02-iter-3.md` (53 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-02-documented-gap-not-fail/tree/reports/qa/goal-afx02-iter-3-qa.md` (70 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-02-documented-gap-not-fail/tree/reports/qa/goal-afx02-iter-3-test-plan.md` (99 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-02-documented-gap-not-fail/tree/reports/reviews/goal-afx02-iter-3-review.md` (42 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-02-documented-gap-not-fail/tree/runs/goal-afx02-iter-3/plan.md` (44 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-02-documented-gap-not-fail/tree/runs/goal-afx02-iter-3/status.json` (19 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-02-documented-gap-not-fail/tree/static/app.js` (16 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-02-documented-gap-not-fail/tree/templates/index.html` (37 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-02-documented-gap-not-fail/tree/test_items.py` (114 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-03-qa-green-spec-contradiction/case.env` (10 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-03-qa-green-spec-contradiction/expected.txt` (7 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-03-qa-green-spec-contradiction/notes.md` (53 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-03-qa-green-spec-contradiction/source/change.patch` (125 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-03-qa-green-spec-contradiction/tree/app.py` (141 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-03-qa-green-spec-contradiction/tree/docs/goal.md` (77 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-03-qa-green-spec-contradiction/tree/docs/handoffs/goal-afx03-iter-3-dev.md` (39 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-03-qa-green-spec-contradiction/tree/docs/phases/goal-afx03-iter-3.md` (56 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-03-qa-green-spec-contradiction/tree/reports/qa/goal-afx03-iter-3-qa.md` (64 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-03-qa-green-spec-contradiction/tree/reports/qa/goal-afx03-iter-3-test-plan.md` (84 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-03-qa-green-spec-contradiction/tree/reports/reviews/goal-afx03-iter-3-review.md` (42 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-03-qa-green-spec-contradiction/tree/runs/goal-afx03-iter-3/plan.md` (49 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-03-qa-green-spec-contradiction/tree/runs/goal-afx03-iter-3/status.json` (19 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-03-qa-green-spec-contradiction/tree/static/app.js` (74 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-03-qa-green-spec-contradiction/tree/templates/index.html` (38 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-03-qa-green-spec-contradiction/tree/test_items.py` (88 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-04-paid-service-live-key/case.env` (10 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-04-paid-service-live-key/expected.txt` (7 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-04-paid-service-live-key/notes.md` (54 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-04-paid-service-live-key/source/change.patch` (120 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-04-paid-service-live-key/tree/app.py` (177 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-04-paid-service-live-key/tree/docs/goal.md` (74 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-04-paid-service-live-key/tree/docs/handoffs/goal-afx04-iter-3-dev.md` (41 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-04-paid-service-live-key/tree/docs/phases/goal-afx04-iter-3.md` (53 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-04-paid-service-live-key/tree/reports/qa/goal-afx04-iter-3-qa.md` (64 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-04-paid-service-live-key/tree/reports/qa/goal-afx04-iter-3-test-plan.md` (69 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-04-paid-service-live-key/tree/reports/reviews/goal-afx04-iter-3-review.md` (48 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-04-paid-service-live-key/tree/runs/goal-afx04-iter-3/plan.md` (44 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-04-paid-service-live-key/tree/runs/goal-afx04-iter-3/status.json` (19 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-04-paid-service-live-key/tree/static/app.js` (16 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-04-paid-service-live-key/tree/templates/index.html` (34 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/case-04-paid-service-live-key/tree/test_items.py` (95 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/tools/base/app.py` (141 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/tools/base/static/app.js` (16 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/tools/base/templates/index.html` (32 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/tools/base/test_items.py` (82 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/tools/make_screenshots.py` (273 lines not shown)
- `incredible_auto_dev/tests/judgment/auditor/tools/regen.sh` (159 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-01-clean-goal-achieved/case.env` (10 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-01-clean-goal-achieved/expected.txt` (7 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-01-clean-goal-achieved/notes.md` (21 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-01-clean-goal-achieved/source/iter.patch` (77 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-01-clean-goal-achieved/tree/docs/goal.md` (63 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-01-clean-goal-achieved/tree/docs/handoffs/goal-fixt01-iter-2-dev.md` (35 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-01-clean-goal-achieved/tree/docs/phases/goal-fixt01-iter-2.md` (44 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-01-clean-goal-achieved/tree/reports/phase-goal-fixt01-iter-2-ui-test-results.md` (52 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-01-clean-goal-achieved/tree/reports/reviews/goal-fixt01-iter-2-review.md` (22 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-01-clean-goal-achieved/tree/runs/goal-fixt01-iter-2/status.json` (19 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-01-clean-goal-achieved/tree/runs/goal-session-fixt01/iter-2/coherence.md` (18 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-01-clean-goal-achieved/tree/runs/goal-session-fixt01/iter-2/iter-diff.md` (83 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-01-clean-goal-achieved/tree/runs/goal-session-fixt01/iter-2/scan-report.md` (9 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-01-clean-goal-achieved/tree/runs/goal-session-fixt01/state/evaluator-log.md` (40 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-01-clean-goal-achieved/tree/runs/goal-session-fixt01/state/journey-history.json` (41 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-02-first-failure-continue/case.env` (10 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-02-first-failure-continue/expected.txt` (7 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-02-first-failure-continue/notes.md` (19 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-02-first-failure-continue/source/iter.patch` (78 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-02-first-failure-continue/tree/docs/goal.md` (63 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-02-first-failure-continue/tree/docs/handoffs/goal-fixt02-iter-2-dev.md` (34 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-02-first-failure-continue/tree/docs/phases/goal-fixt02-iter-2.md` (44 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-02-first-failure-continue/tree/reports/phase-goal-fixt02-iter-2-ui-test-results.md` (58 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-02-first-failure-continue/tree/reports/reviews/goal-fixt02-iter-2-review.md` (23 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-02-first-failure-continue/tree/runs/goal-fixt02-iter-2/status.json` (19 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-02-first-failure-continue/tree/runs/goal-session-fixt02/iter-2/coherence.md` (18 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-02-first-failure-continue/tree/runs/goal-session-fixt02/iter-2/iter-diff.md` (84 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-02-first-failure-continue/tree/runs/goal-session-fixt02/iter-2/scan-report.md` (9 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-02-first-failure-continue/tree/runs/goal-session-fixt02/state/evaluator-log.md` (38 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-02-first-failure-continue/tree/runs/goal-session-fixt02/state/journey-history.json` (40 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-03-regression-broken-journey/case.env` (10 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-03-regression-broken-journey/expected.txt` (7 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-03-regression-broken-journey/notes.md` (19 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-03-regression-broken-journey/source/iter.patch` (92 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-03-regression-broken-journey/tree/docs/goal.md` (63 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-03-regression-broken-journey/tree/docs/handoffs/goal-fixt03-iter-2-dev.md` (33 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-03-regression-broken-journey/tree/docs/phases/goal-fixt03-iter-2.md` (43 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-03-regression-broken-journey/tree/reports/phase-goal-fixt03-iter-2-ui-test-results.md` (60 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-03-regression-broken-journey/tree/reports/reviews/goal-fixt03-iter-2-review.md` (23 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-03-regression-broken-journey/tree/runs/goal-fixt03-iter-2/status.json` (19 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-03-regression-broken-journey/tree/runs/goal-session-fixt03/iter-2/coherence.md` (18 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-03-regression-broken-journey/tree/runs/goal-session-fixt03/iter-2/iter-diff.md` (98 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-03-regression-broken-journey/tree/runs/goal-session-fixt03/iter-2/scan-report.md` (9 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-03-regression-broken-journey/tree/runs/goal-session-fixt03/state/evaluator-log.md` (38 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-03-regression-broken-journey/tree/runs/goal-session-fixt03/state/journey-history.json` (41 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-04-goal-drift-void-pass/case.env` (10 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-04-goal-drift-void-pass/expected.txt` (7 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-04-goal-drift-void-pass/notes.md` (24 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-04-goal-drift-void-pass/source/goal-old.md` (63 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-04-goal-drift-void-pass/source/iter.patch` (63 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-04-goal-drift-void-pass/tree/docs/goal.md` (65 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-04-goal-drift-void-pass/tree/docs/handoffs/goal-fixt04-iter-2-dev.md` (30 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-04-goal-drift-void-pass/tree/docs/phases/goal-fixt04-iter-2.md` (42 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-04-goal-drift-void-pass/tree/reports/phase-goal-fixt04-iter-2-ui-test-results.md` (47 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-04-goal-drift-void-pass/tree/reports/reviews/goal-fixt04-iter-2-review.md` (22 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-04-goal-drift-void-pass/tree/runs/goal-fixt04-iter-2/status.json` (19 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-04-goal-drift-void-pass/tree/runs/goal-session-fixt04/iter-2/coherence.md` (18 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-04-goal-drift-void-pass/tree/runs/goal-session-fixt04/iter-2/iter-diff.md` (69 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-04-goal-drift-void-pass/tree/runs/goal-session-fixt04/iter-2/journeys-changed.md` (14 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-04-goal-drift-void-pass/tree/runs/goal-session-fixt04/iter-2/scan-report.md` (9 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-04-goal-drift-void-pass/tree/runs/goal-session-fixt04/state/assumptions.md` (12 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-04-goal-drift-void-pass/tree/runs/goal-session-fixt04/state/evaluator-log.md` (38 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-04-goal-drift-void-pass/tree/runs/goal-session-fixt04/state/journey-history.json` (41 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-05-secret-committed/case.env` (10 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-05-secret-committed/expected.txt` (7 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-05-secret-committed/notes.md` (29 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-05-secret-committed/source/iter.patch` (96 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-05-secret-committed/tree/docs/goal.md` (63 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-05-secret-committed/tree/docs/handoffs/goal-fixt05-iter-2-dev.md` (37 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-05-secret-committed/tree/docs/phases/goal-fixt05-iter-2.md` (43 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-05-secret-committed/tree/reports/phase-goal-fixt05-iter-2-ui-test-results.md` (52 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-05-secret-committed/tree/reports/reviews/goal-fixt05-iter-2-review.md` (22 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-05-secret-committed/tree/runs/goal-fixt05-iter-2/status.json` (19 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-05-secret-committed/tree/runs/goal-session-fixt05/iter-2/coherence.md` (18 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-05-secret-committed/tree/runs/goal-session-fixt05/iter-2/iter-diff.md` (102 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-05-secret-committed/tree/runs/goal-session-fixt05/iter-2/scan-report.md` (15 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-05-secret-committed/tree/runs/goal-session-fixt05/state/evaluator-log.md` (38 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-05-secret-committed/tree/runs/goal-session-fixt05/state/journey-history.json` (41 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/tools/make_screenshots.py` (217 lines not shown)
- `incredible_auto_dev/tests/judgment/goal-evaluator/tools/regen.sh` (140 lines not shown)
- `incredible_auto_dev/tests/judgment/reviewer/case-01-clean-pass/case.env` (10 lines not shown)
- `incredible_auto_dev/tests/judgment/reviewer/case-01-clean-pass/expected.txt` (7 lines not shown)
- `incredible_auto_dev/tests/judgment/reviewer/case-01-clean-pass/notes.md` (26 lines not shown)
- `incredible_auto_dev/tests/judgment/reviewer/case-01-clean-pass/source/change.patch` (58 lines not shown)
- `incredible_auto_dev/tests/judgment/reviewer/case-01-clean-pass/tree/app.py` (145 lines not shown)
- `incredible_auto_dev/tests/judgment/reviewer/case-01-clean-pass/tree/docs/goal.md` (73 lines not shown)
- `incredible_auto_dev/tests/judgment/reviewer/case-01-clean-pass/tree/docs/handoffs/goal-rfx01-iter-3-dev.md` (36 lines not shown)
- `incredible_auto_dev/tests/judgment/reviewer/case-01-clean-pass/tree/docs/phases/goal-rfx01-iter-3.md` (46 lines not shown)
- `incredible_auto_dev/tests/judgment/reviewer/case-01-clean-pass/tree/runs/goal-rfx01-iter-3/status.json` (19 lines not shown)
- `incredible_auto_dev/tests/judgment/reviewer/case-01-clean-pass/tree/static/app.js` (16 lines not shown)
- `incredible_auto_dev/tests/judgment/reviewer/case-01-clean-pass/tree/templates/index.html` (33 lines not shown)
- `incredible_auto_dev/tests/judgment/reviewer/case-01-clean-pass/tree/test_items.py` (93 lines not shown)
- `incredible_auto_dev/tests/judgment/reviewer/case-02-minor-nit-not-fail/case.env` (10 lines not shown)
- `incredible_auto_dev/tests/judgment/reviewer/case-02-minor-nit-not-fail/expected.txt` (7 lines not shown)
- `incredible_auto_dev/tests/judgment/reviewer/case-02-minor-nit-not-fail/notes.md` (35 lines not shown)
- `incredible_auto_dev/tests/judgment/reviewer/case-02-minor-nit-not-fail/source/change.patch` (72 lines not shown)
- `incredible_auto_dev/tests/judgment/reviewer/case-02-minor-nit-not-fail/tree/app.py` (152 lines not shown)
- `incredible_auto_dev/tests/judgment/reviewer/case-02-minor-nit-not-fail/tree/docs/goal.md` (73 lines not shown)
- `incredible_auto_dev/tests/judgment/reviewer/case-02-minor-nit-not-fail/tree/docs/handoffs/goal-rfx02-iter-3-dev.md` (33 lines not shown)
- `incredible_auto_dev/tests/judgment/reviewer/case-02-minor-nit-not-fail/tree/docs/phases/goal-rfx02-iter-3.md` (46 lines not shown)
- `incredible_auto_dev/tests/judgment/reviewer/case-02-minor-nit-not-fail/tree/runs/goal-rfx02-iter-3/status.json` (19 lines not shown)
- `incredible_auto_dev/tests/judgment/reviewer/case-02-minor-nit-not-fail/tree/static/app.js` (16 lines not shown)
- `incredible_auto_dev/tests/judgment/reviewer/case-02-minor-nit-not-fail/tree/templates/index.html` (35 lines not shown)
- `incredible_auto_dev/tests/judgment/reviewer/case-02-minor-nit-not-fail/tree/test_items.py` (94 lines not shown)
- `incredible_auto_dev/tests/judgment/reviewer/case-03-hardcoded-credential/case.env` (10 lines not shown)
- `incredible_auto_dev/tests/judgment/reviewer/case-03-hardcoded-credential/expected.txt` (7 lines not shown)
- `incredible_auto_dev/tests/judgment/reviewer/case-03-hardcoded-credential/notes.md` (38 lines not shown)
- `incredible_auto_dev/tests/judgment/reviewer/case-03-hardcoded-credential/source/change.patch` (136 lines not shown)
- `incredible_auto_dev/tests/judgment/reviewer/case-03-hardcoded-credential/tree/app.py` (187 lines not shown)
- `incredible_auto_dev/tests/judgment/reviewer/case-03-hardcoded-credential/tree/docs/goal.md` (73 lines not shown)
- `incredible_auto_dev/tests/judgment/reviewer/case-03-hardcoded-credential/tree/docs/handoffs/goal-rfx03-iter-3-dev.md` (36 lines not shown)
- `incredible_auto_dev/tests/judgment/reviewer/case-03-hardcoded-credential/tree/docs/phases/goal-rfx03-iter-3.md` (46 lines not shown)
- `incredible_auto_dev/tests/judgment/reviewer/case-03-hardcoded-credential/tree/runs/goal-rfx03-iter-3/status.json` (19 lines not shown)
- `incredible_auto_dev/tests/judgment/reviewer/case-03-hardcoded-credential/tree/static/app.js` (16 lines not shown)
- `incredible_auto_dev/tests/judgment/reviewer/case-03-hardcoded-credential/tree/templates/index.html` (32 lines not shown)
- `incredible_auto_dev/tests/judgment/reviewer/case-03-hardcoded-credential/tree/test_items.py` (106 lines not shown)
- `incredible_auto_dev/tests/judgment/reviewer/case-04-spec-contradiction/case.env` (10 lines not shown)
- `incredible_auto_dev/tests/judgment/reviewer/case-04-spec-contradiction/expected.txt` (7 lines not shown)
- `incredible_auto_dev/tests/judgment/reviewer/case-04-spec-contradiction/notes.md` (36 lines not shown)
- `incredible_auto_dev/tests/judgment/reviewer/case-04-spec-contradiction/source/change.patch` (102 lines not shown)
- `incredible_auto_dev/tests/judgment/reviewer/case-04-spec-contradiction/tree/app.py` (153 lines not shown)
- `incredible_auto_dev/tests/judgment/reviewer/case-04-spec-contradiction/tree/docs/goal.md` (73 lines not shown)
- `incredible_auto_dev/tests/judgment/reviewer/case-04-spec-contradiction/tree/docs/handoffs/goal-rfx04-iter-3-dev.md` (42 lines not shown)
- `incredible_auto_dev/tests/judgment/reviewer/case-04-spec-contradiction/tree/docs/phases/goal-rfx04-iter-3.md` (49 lines not shown)
- `incredible_auto_dev/tests/judgment/reviewer/case-04-spec-contradiction/tree/runs/goal-rfx04-iter-3/status.json` (19 lines not shown)
- `incredible_auto_dev/tests/judgment/reviewer/case-04-spec-contradiction/tree/static/app.js` (29 lines not shown)
- `incredible_auto_dev/tests/judgment/reviewer/case-04-spec-contradiction/tree/templates/index.html` (32 lines not shown)
- `incredible_auto_dev/tests/judgment/reviewer/case-04-spec-contradiction/tree/test_items.py` (100 lines not shown)
- `incredible_auto_dev/tests/judgment/reviewer/tools/base/app.py` (141 lines not shown)
- `incredible_auto_dev/tests/judgment/reviewer/tools/base/static/app.js` (16 lines not shown)
- `incredible_auto_dev/tests/judgment/reviewer/tools/base/templates/index.html` (32 lines not shown)
- `incredible_auto_dev/tests/judgment/reviewer/tools/base/test_items.py` (82 lines not shown)
- `incredible_auto_dev/tests/judgment/reviewer/tools/regen.sh` (111 lines not shown)
- `diff --git adocs/handoffs/goal-mcp-loop-iter-27-audit.md bdocs/handoffs/goal-mcp-loop-iter-27-audit.md` (158 lines not shown)
- `diff --git adocs/handoffs/goal-mcp-loop-iter-27-dev.md bdocs/handoffs/goal-mcp-loop-iter-27-dev.md` (203 lines not shown)
- `diff --git adocs/phases/goal-mcp-loop-iter-27.md bdocs/phases/goal-mcp-loop-iter-27.md` (120 lines not shown)
- `diff --git areports/phase-goal-mcp-loop-iter-27-closure-verdict.md breports/phase-goal-mcp-loop-iter-27-closure-verdict.md` (179 lines not shown)
- `diff --git areports/phase-goal-mcp-loop-iter-27-demo-results.md breports/phase-goal-mcp-loop-iter-27-demo-results.md` (30 lines not shown)
- `diff --git areports/phase-goal-mcp-loop-iter-27-demo-script.md breports/phase-goal-mcp-loop-iter-27-demo-script.md` (63 lines not shown)
- `diff --git areports/phase-goal-mcp-loop-iter-27-demo.json breports/phase-goal-mcp-loop-iter-27-demo.json` (110 lines not shown)
- `diff --git areports/phase-goal-mcp-loop-iter-27-implementation-summary.md breports/phase-goal-mcp-loop-iter-27-implementation-summary.md` (84 lines not shown)
- `diff --git areports/phase-goal-mcp-loop-iter-27-iteration-summary.md breports/phase-goal-mcp-loop-iter-27-iteration-summary.md` (92 lines not shown)
- `diff --git areports/phase-goal-mcp-loop-iter-27-summary.html breports/phase-goal-mcp-loop-iter-27-summary.html` (370 lines not shown)
- `diff --git areports/phase-goal-mcp-loop-iter-27-ui-surface-map.md breports/phase-goal-mcp-loop-iter-27-ui-surface-map.md` (101 lines not shown)
- `diff --git areports/phase-goal-mcp-loop-iter-27-ui-test-plan.md breports/phase-goal-mcp-loop-iter-27-ui-test-plan.md` (520 lines not shown)
- `diff --git areports/phase-goal-mcp-loop-iter-27-ui-test-results.md breports/phase-goal-mcp-loop-iter-27-ui-test-results.md` (266 lines not shown)
- `diff --git areports/phase-goal-mcp-loop-iter-27-user-visible-changes.md breports/phase-goal-mcp-loop-iter-27-user-visible-changes.md` (101 lines not shown)
- `diff --git areports/phase-goal-mcp-loop-iter-27-ux-regression.md breports/phase-goal-mcp-loop-iter-27-ux-regression.md` (155 lines not shown)
- `diff --git areports/phase-goal-mcp-loop-iter-27-what-to-click.md breports/phase-goal-mcp-loop-iter-27-what-to-click.md` (118 lines not shown)
- `diff --git areports/qa/goal-mcp-loop-iter-27-qa.md breports/qa/goal-mcp-loop-iter-27-qa.md` (212 lines not shown)
- `diff --git areports/qa/goal-mcp-loop-iter-27-test-plan.md breports/qa/goal-mcp-loop-iter-27-test-plan.md` (340 lines not shown)
- `diff --git areports/reviews/goal-mcp-loop-iter-27-review.md breports/reviews/goal-mcp-loop-iter-27-review.md` (64 lines not shown)
- `diff --git aruns/goal-mcp-loop-iter-27/plan.md bruns/goal-mcp-loop-iter-27/plan.md` (182 lines not shown)
- `diff --git aruns/goal-mcp-loop-iter-27/status.json bruns/goal-mcp-loop-iter-27/status.json` (39 lines not shown)
- `diff --git aruns/goal-session-mcp-loop/iter-27/.steps/coherence.done bruns/goal-session-mcp-loop/iter-27/.steps/coherence.done` (7 lines not shown)
- `diff --git aruns/goal-session-mcp-loop/iter-27/.steps/decomposer.done bruns/goal-session-mcp-loop/iter-27/.steps/decomposer.done` (7 lines not shown)
- `diff --git aruns/goal-session-mcp-loop/iter-27/coherence.md bruns/goal-session-mcp-loop/iter-27/coherence.md` (68 lines not shown)
- `diff --git aruns/goal-session-mcp-loop/iter-27/goal-slice.md bruns/goal-session-mcp-loop/iter-27/goal-slice.md` (682 lines not shown)
- `diff --git aruns/goal-session-mcp-loop/iter-27/journey-history.pre.json bruns/goal-session-mcp-loop/iter-27/journey-history.pre.json` (188 lines not shown)
- `diff --git aruns/goal-session-mcp-loop/iter-27/snapshot-sha bruns/goal-session-mcp-loop/iter-27/snapshot-sha` (8 lines not shown)

```diff
diff --git a/apps/backend/app/config.py b/apps/backend/app/config.py
index 1316d07..a153bca 100644
--- a/apps/backend/app/config.py
+++ b/apps/backend/app/config.py
@@ -551,6 +551,16 @@ class ServerOpsCfg(BaseModel):
                                      one-copy ~3.27M-row bar prefill (iter-19: a streamed, column-projected
                                      load — retained footprint ~0.4-0.5 GB) + headroom, so a pathological
                                      N-copy spike is OOM-killed as ONE process rather than swap-thrashing the VM.
+      - `malloc_arena_max`         — the `MALLOC_ARENA_MAX` glibc allocator cap the start script exports
+                                     (iter-27, anti-goal #8). By default glibc creates up to `8 x ncpus`
+                                     independent malloc arenas (up to 128 on this 16-core host); each retains
+                                     its own freed-but-not-returned address space, so a long-lived
+                                     multi-threaded server (uvicorn threadpool + the parallel backfill workers)
+                                     fragments VSZ across many arenas and pins the `ulimit -v` ceiling on a
+                                     second full-universe rebuild. Capping the arena count bounds that
+                                     fragmentation — the dominant VSZ lever behind the iter-26/iter-27
+                                     rebuild crash — while leaving all computed values byte-identical (it only
+                                     changes how the allocator lays out memory, never what is stored/served).
 
     Default-populated (a config predating it — and the inline test fixtures — still loads unchanged). Every
     value MUST be positive; an invalid block raises `ValueError` at load, never a silent default."""
@@ -560,6 +570,7 @@ class ServerOpsCfg(BaseModel):
     timeout_keep_alive_seconds: int = 65
     graceful_timeout_seconds: int = 120
     memory_cap_mb: int = 6144
+    malloc_arena_max: int = 2
 
     @model_validator(mode="after")
     def _validate(self) -> "ServerOpsCfg":
@@ -569,6 +580,7 @@ class ServerOpsCfg(BaseModel):
                 "timeout_keep_alive_seconds": self.timeout_keep_alive_seconds,
                 "graceful_timeout_seconds": self.graceful_timeout_seconds,
                 "memory_cap_mb": self.memory_cap_mb,
+                "malloc_arena_max": self.malloc_arena_max,
             }.items() if v <= 0
         )
         if bad:
diff --git a/apps/backend/app/engine/data_manager.py b/apps/backend/app/engine/data_manager.py
index 84b7265..7afb151 100644
--- a/apps/backend/app/engine/data_manager.py
+++ b/apps/backend/app/engine/data_manager.py
@@ -27,6 +27,9 @@ from __future__ import annotations
 
 import copy
 import csv
+import ctypes
+import ctypes.util
+import gc
 import hashlib
 import json
 import os
@@ -2367,6 +2370,36 @@ def _cleanup_orphan_run(session: Session, d: date_cls) -> None:
         session.rollback()
 
 
+def _release_process_memory() -> None:
+    """iter-27 (J-16, anti-goal #8) — after a heavy full-universe backfill/rebuild stage finishes, return
+    the just-freed memory to the OS so a SECOND consecutive full-universe rebuild in the SAME long-lived
+    server process starts from a lean baseline instead of stacking on the first run's retained address space.
+
+    Root cause this addresses (iter-27 audit finding B2, re-confirmed here by a two-run in-process probe):
+    the per-job `_BarCache` object IS dropped when `_do_backfill`'s `with prefilled_bar_cache(...)` block
+    exits — the accumulation is NOT a leaked Python object. It is at the process VSZ / glibc malloc-arena
+    level: the ~1.5 GB of `Bar` lists (plus per-(date,symbol) transients and SQLAlchemy result buffers) are
+    freed back to the allocator's arenas, but glibc does not automatically return that (fragmented) address
+    space to the OS — so run 1 leaves VmSize inflated and run 2 re-allocates on top of it, pinning VSZ at
+    the `ulimit -v` ceiling and wedging the backend (the reproduced iter-26/iter-27 crash signature).
+
+    Two best-effort, fully byte-identity-NEUTRAL steps (they change WHEN freed memory is returned, never any
+    computed value): `gc.collect()` reclaims the now-unreferenced cache/transients deterministically (not at
+    the next cyclic-GC threshold, so they cannot linger resident into the next job's prefill), and glibc
+    `malloc_trim(0)` hands the emptied arenas' pages back to the OS. Paired with the `MALLOC_ARENA_MAX` cap
+    the start script exports (which bounds how many independently-fragmenting arenas glibc creates across the
+    server's worker threads on a many-core host — the dominant VSZ lever), consecutive rebuilds stay under
+    the cap with margin. `malloc_trim` is glibc-only; on any other libc the `gc.collect()` still runs and the
+    trim is silently skipped."""
+    gc.collect()
+    try:
+        libc_name = ctypes.util.find_library("c") or "libc.so.6"
+        libc = ctypes.CDLL(libc_name)
+        libc.malloc_trim(0)  # glibc: return free heap/arena pages to the OS (no-op elsewhere)
+    except (OSError, AttributeError):  # non-glibc / symbol absent — gc.collect() above already ran
+        pass
+
+
 def _do_backfill(session: Session, cfg: Config, prog: JobProgress, *, eng: Engine) -> None:
     """For each in-range trading day with bars but NO snapshot, create the immutable snapshot then INSERT
     its realized forward returns (bars > D). No scan/return math is re-implemented and no snapshot is
@@ -2497,43 +2530,51 @@ def _do_backfill(session: Session, cfg: Config, prog: JobProgress, *, eng: Engin
     # once-loaded cache instead of re-issuing a per-symbol lazy load EVERY snapshot date / per worker
     # session (the iter-36 defect that broke load-once for no-bar candidates). Byte-identical served values.
     pool_symbols = {row["symbol"] for row in read_pool()}
-    with prefilled_bar_cache(session, expected_symbols=pool_symbols) as shared_cache:
-        if workers <= 1 or len(targets) <= 1:
-            # serial baseline (workers=1) — compute + persist inline, one date at a time, in order. A
-            # per-date compute failure is caught here (isolated), not raised — the rest still run.
-            for d in targets:
-                compute_error: Optional[str] = None
-                payload: Optional[dict] = None
-                secs = 0.0
-                try:
-                    _, payload, secs = _compute_one_backfill_date(eng, cfg, d, shared_cache)
-                except Exception as exc:  # noqa: BLE001 — isolate this date's compute failure
-                    compute_error = str(exc)
-                _persist_isolated(d, payload, secs, compute_error)
-            return
-        # PARALLEL: fan out the per-date compute; persist results IN DATE ORDER on this thread as they
-        # arrive. A worker compute exception is captured PER DATE (never raised out of the drain loop, so
-        # it never aborts the whole stage or deadlocks); the `with ThreadPoolExecutor` joins every worker
-        # before returning, so no thread outlives the job (the iter-28 determinism lesson).
-        pending: dict[date_cls, tuple[Optional[dict], float, Optional[str]]] = {}
-        next_idx = 0
-        with ThreadPoolExecutor(max_workers=min(workers, len(targets))) as pool:
-            future_to_date = {
-                pool.submit(_compute_one_backfill_date, eng, cfg, d, shared_cache): d for d in targets
-            }
-            for future in as_completed(future_to_date):
-                d = future_to_date[future]
-                try:
-                    _, payload, secs = future.result()
-                    pending[d] = (payload, secs, None)
-                except Exception as exc:  # noqa: BLE001 — capture this date's compute failure, keep draining
-                    pending[d] = (None, 0.0, str(exc))
-                # drain any now-contiguous prefix in target (date) order, so writes are strictly ordered.
-                while next_idx < len(targets) and targets[next_idx] in pending:
-                    cur = targets[next_idx]
-                    cur_payload, cur_secs, cur_err = pending.pop(cur)
-                    _persist_isolated(cur, cur_payload, cur_secs, cur_err)
-                    next_idx += 1
+    # iter-27 (anti-goal #8): the `with prefilled_bar_cache(...)` block drops the ~1.5 GB shared `_BarCache`
+    # on exit, but glibc retains that freed address space by default — so a SECOND consecutive full-universe
+    # rebuild in the same long-lived process stacks on run 1's inflated VSZ and hits the `ulimit -v` ceiling.
+    # `_release_process_memory()` (gc.collect + malloc_trim) in the `finally` returns it to the OS on EVERY
+    # exit path (serial `return`, parallel fall-through, or an exception), so each rebuild starts lean.
+    try:
+        with prefilled_bar_cache(session, expected_symbols=pool_symbols) as shared_cache:
+            if workers <= 1 or len(targets) <= 1:
+                # serial baseline (workers=1) — compute + persist inline, one date at a time, in order. A
+                # per-date compute failure is caught here (isolated), not raised — the rest still run.
+                for d in targets:
+                    compute_error: Optional[str] = None
+                    payload: Optional[dict] = None
+                    secs = 0.0
+                    try:
+                        _, payload, secs = _compute_one_backfill_date(eng, cfg, d, shared_cache)
+                    except Exception as exc:  # noqa: BLE001 — isolate this date's compute failure
+                        compute_error = str(exc)
+                    _persist_isolated(d, payload, secs, compute_error)
+                return
+            # PARALLEL: fan out the per-date compute; persist results IN DATE ORDER on this thread as they
+            # arrive. A worker compute exception is captured PER DATE (never raised out of the drain loop, so
+            # it never aborts the whole stage or deadlocks); the `with ThreadPoolExecutor` joins every worker
+            # before returning, so no thread outlives the job (the iter-28 determinism lesson).
+            pending: dict[date_cls, tuple[Optional[dict], float, Optional[str]]] = {}
+            next_idx = 0
+            with ThreadPoolExecutor(max_workers=min(workers, len(targets))) as pool:
+                future_to_date = {
+                    pool.submit(_compute_one_backfill_date, eng, cfg, d, shared_cache): d for d in targets
+                }
+                for future in as_completed(future_to_date):
+                    d = future_to_date[future]
+                    try:
+                        _, payload, secs = future.result()
+                        pending[d] = (payload, secs, None)
+                    except Exception as exc:  # noqa: BLE001 — capture this date's compute failure, keep draining
+                        pending[d] = (None, 0.0, str(exc))
+                    # drain any now-contiguous prefix in target (date) order, so writes are strictly ordered.
+                    while next_idx < len(targets) and targets[next_idx] in pending:
+                        cur = targets[next_idx]
+                        cur_payload, cur_secs, cur_err = pending.pop(cur)
+                        _persist_isolated(cur, cur_payload, cur_secs, cur_err)
+                        next_idx += 1
+    finally:
+        _release_process_memory()
 
 
 # --------------------------------------------------------------------------------------------------
diff --git a/apps/backend/app/engine/prices.py b/apps/backend/app/engine/prices.py
index 7814045..a95b15b 100644
--- a/apps/backend/app/engine/prices.py
+++ b/apps/backend/app/engine/prices.py
@@ -190,6 +190,48 @@ class _BarCache:
         cut = bisect.bisect_right(self._dates_by_symbol[symbol], d)
         return full[:cut]
 
+    def bars_asof_window(
+        self, session: Session, symbol: str, d: date_cls, lookback: int
+    ) -> list[Bar]:
+        """iter-27 (J-16 memory fix): the trailing `lookback` bars with date <= `d` — BYTE-IDENTICAL to
+        `self.bars_asof(session, symbol, d)[-lookback:]` (same rows, same order) but computed WITHOUT
+        ever materializing the full `<= d` prefix (`full[:cut]`) as an intermediate allocation. On a late
+        as-of date a symbol's `<= d` prefix can carry ~5,300 bars while a caller (regime's MA-stack /
+        breadth / 52-week-high inputs) only reads a bounded trailing window (`cfg.indicators
+        .max_lookback_bars`) — this accessor slices `full[max(0, cut - lookback):cut]` directly, a list
+        slice that allocates exactly `min(lookback, cut)` elements, never the larger `cut`-length prefix
+        `bars_asof` builds (only to have a caller immediately discard everything but its own tail).
+
+        Boundary cases (all fall out of the one formula, no special-casing needed):
+          - `cut == 0` (d before the symbol's first bar, or a no-bar symbol): `max(0, 0 - lookback) == 0`,
+            so `full[0:0] == []` — matches `bars_asof(...)[-lookback:]` on an empty list.
+          - `cut == len(full)` (d on/after the symbol's last bar): identical to slicing the full series'
+            tail.
+          - `lookback >= cut` (fewer than `lookback` bars available on/before `d`, e.g. a short-history
+            symbol near its point-in-time entry): `max(0, cut - lookback) == 0`, so the WHOLE `<= d`
+            prefix is returned — matching `full[:cut][-lookback:]` on a list shorter than `lookback`."""
+        full = self._by_symbol.get(symbol)
+        if full is None:
+            # lazy load (defensive — a pre-filled cache rarely reaches here): the SAME load-ensure path
+            # `bars_asof` uses (already per-symbol bounded — this call site adds no new unbounded query).
+            with self._load_lock:
+                full = self._by_symbol.get(symbol)
+                if full is None:
+                    stmt = (
+                        select(
+                            DailyPrice.date, DailyPrice.open, DailyPrice.high,
+                            DailyPrice.low, DailyPrice.close, DailyPrice.volume,
+                        )
+                        .where(DailyPrice.symbol == symbol)
+                        .order_by(DailyPrice.date)
+                    )
+                    full = [Bar(*row) for row in session.exec(stmt).all()]
+                    self._by_symbol[symbol] = full
+                    self._dates_by_symbol[symbol] = [bar.date for bar in full]
+        dates = self._dates_by_symbol[symbol]
+        cut = bisect.bisect_right(dates, d)
+        return full[max(0, cut - lookback):cut]
+
     def bars_after(
         self, session: Session, symbol: str, d: date_cls, limit: Optional[int] = None
     ) -> list[Bar]:
@@ -374,6 +416,39 @@ def bars_asof(session: Session, symbol: str, d: date_cls) -> list[DailyPrice] |
     return list(session.exec(stmt).all())
 
 
+def bars_asof_window(
+    session: Session, symbol: str, d: date_cls, lookback: int
+) -> list[DailyPrice] | list[Bar]:
+    """The trailing `lookback` bars for `symbol` with date <= `d`, ascending — BYTE-IDENTICAL to
+    `bars_asof(session, symbol, d)[-lookback:]` (same rows, same order; the same backward no-lookahead
+    boundary, date <= d). `bars_asof` itself and every other existing consumer are UNCHANGED — this is
+    an ADDITIVE, bounded sibling for callers that only ever read a trailing window off the end of the
+    as-of series (iter-27, J-16 memory fix: `regime.py`'s MA-stack/breadth/52-week-high inputs, bounded
+    to `cfg.indicators.max_lookback_bars` — the same canonical bound `scoring.py` already validated).
+
+    When a `bar_cache(session)` context is active, this slices the once-loaded cached series directly
+    (`_BarCache.bars_asof_window` — never materializes the discarded earlier prefix). Otherwise it runs
+    a bounded `WHERE date <= d ORDER BY date DESC LIMIT lookback` query and reverses the (at most
+    `lookback`-row) result to ascending order: the DESC + LIMIT + reverse round-trip returns exactly the
+    same rows, in the same order, as `ORDER BY date ASC` over the full `<= d` prefix truncated to its
+    last `lookback` rows — without the database (or this process) ever materializing the earlier,
+    discarded rows. Fewer than `lookback` bars on/before `d` (short history, or `d` before the first
+    bar) returns whatever is available, ascending — the same short-list behavior as `[-lookback:]`."""
+    cache = _BAR_CACHES.get(id(session))
+    if cache is not None:
+        return cache.bars_asof_window(session, symbol, d, lookback)
+    stmt = (
+        select(DailyPrice)
+        .where(DailyPrice.symbol == symbol)
+        .where(DailyPrice.date <= d)
+        .order_by(DailyPrice.date.desc())
+        .limit(lookback)
+    )
+    rows = list(session.exec(stmt).all())
+    rows.reverse()
+    return rows
+
+
 def close_on(session: Session, symbol: str, d: date_cls) -> Optional[float]:
     """The close of the latest bar with **date <= `d`** (the as-of close on D), or None when the
     symbol has no bar on/before D. This is the single-bar form of `bars_asof(session, symbol, d)[-1]
diff --git a/apps/backend/app/engine/regime.py b/apps/backend/app/engine/regime.py
index 9328da1..973082d 100644
--- a/apps/backend/app/engine/regime.py
+++ b/apps/backend/app/engine/regime.py
@@ -25,7 +25,7 @@ from sqlmodel import Session
 from app.config import Config, get_config
 from app.engine import indicators as ind
 from app.engine.labels import label_for
-from app.engine.prices import bars_asof, closes
+from app.engine.prices import bars_asof_window, close_on, closes
 
 
 def _pct(fraction: Optional[float]) -> Optional[float]:
@@ -33,10 +33,19 @@ def _pct(fraction: Optional[float]) -> Optional[float]:
 
 
 def _index_ma_stack(session: Session, asof: date_cls, cfg: Config) -> Optional[float]:
-    """Mean bullish MA-stack fraction across the configured broad-index ETFs."""
+    """Mean bullish MA-stack fraction across the configured broad-index ETFs.
+
+    iter-27 (J-16 memory fix): `ma_stack` only ever reads a trailing window off the end of `closes`
+    (the longest configured MA period), so this reads through the bounded `bars_asof_window` — trailing
+    `cfg.indicators.max_lookback_bars` bars, the canonical bound already validated `>= max(ma_periods)`
+    (`IndicatorsCfg._validate`) — instead of `bars_asof`'s whole `<= asof` prefix. Byte-identical result
+    (`bars_asof_window(...) == bars_asof(...)[-max_lookback_bars:]` by construction); see
+    `test_scoring_window.py`."""
     values: list[float] = []
+    lookback = cfg.indicators.max_lookback_bars
     for symbol in cfg.etfs.index:
-        stack = ind.ma_stack(closes(bars_asof(session, symbol, asof)), cfg.indicators.ma_periods)
+        bars = bars_asof_window(session, symbol, asof, lookback)
+        stack = ind.ma_stack(closes(bars), cfg.indicators.ma_periods)
         if stack is not None:
             values.append(stack)
     return (sum(values) / len(values)) if values else None
@@ -45,12 +54,23 @@ def _index_ma_stack(session: Session, asof: date_cls, cfg: Config) -> Optional[f
 def _universe_stats(session: Session, asof: date_cls, cfg: Config) -> dict:
     """Single pass over the universe: breadth above the short/long DMA + net new-high/low.
     Symbols without enough history for a given metric are excluded from that metric's
-    denominator (universe-relative, never fabricated)."""
+    denominator (universe-relative, never fabricated).
+
+    iter-27 (J-16 memory fix): every metric below reads only a trailing window off the end of `series`
+    (`sma`'s `breadth_short_ma`/`breadth_long_ma`, and the `high_window_52w`-bar `window` slice) — so
+    this reads through the bounded `bars_asof_window` (trailing `max_lookback_bars` = 320 bars) instead
+    of `bars_asof`'s whole `<= asof` prefix (up to ~5,300 bars on a late date, per symbol, across the
+    full universe — the dominant per-(symbol,date) VSZ driver on the full-universe rebuild). `320 >=
+    breadth_long_ma (200)` and `320 >= high_window_52w (252)` (validated: both are covered by
+    `max(ma_periods)=200`/`high_window_52w` in `IndicatorsCfg._validate`'s `max_needed`), so `len(series)
+    >= icfg.high_window_52w` and `series[-icfg.high_window_52w:]` below stay byte-identical — windowing
+    only truncates bars OLDER than the tail these reads ever touch."""
     icfg = cfg.indicators
     above_short = above_long = new_highs = new_lows = 0
     eval_short = eval_long = eval_hl = 0
+    lookback = icfg.max_lookback_bars
     for symbol in cfg.universe.symbols:
-        series = closes(bars_asof(session, symbol, asof))
+        series = closes(bars_asof_window(session, symbol, asof, lookback))
         if not series:
             continue
         last = series[-1]
@@ -85,11 +105,15 @@ def _universe_stats(session: Session, asof: date_cls, cfg: Config) -> dict:
 
 
 def _latest_vix(session: Session, asof: date_cls, cfg: Config) -> Optional[float]:
+    """iter-27 (J-16 memory fix): the old body (`closes(bars_asof(...))[-1]`) built the WHOLE `<= asof`
+    prefix only to read its last close. `close_on` is the already-optimized (iter-26) single-value
+    accessor for exactly this read — O(1) via `_BarCache.close_on`'s bisect+index when a cache is
+    active, a single-row `LIMIT 1` query otherwise — byte-identical (same `<= asof` boundary, same
+    "no bar -> None" behavior as the old empty-series check)."""
     symbols = cfg.etfs.volatility
     if not symbols:
         return None
-    series = closes(bars_asof(session, symbols[0], asof))
-    return series[-1] if series else None
+    return close_on(session, symbols[0], asof)
 
 
 def score_regime(session: Session, asof: date_cls, config: Optional[Config] = None) -> dict:
diff --git a/apps/backend/app/engine/scoring.py b/apps/backend/app/engine/scoring.py
index fb6c010..d5e4e56 100644
--- a/apps/backend/app/engine/scoring.py
+++ b/apps/backend/app/engine/scoring.py
@@ -42,7 +42,7 @@ from app.engine import indicators as ind
 from app.engine.buckets import to_bucket
 from app.engine.normalize import cross_sectional_percentiles
 from app.engine.patterns import detect_flat_base_breakout, detect_pullback_to_rising_dma, detect_vcp
-from app.engine.prices import bars_asof, closes, highs, lows, volumes
+from app.engine.prices import bars_asof, bars_asof_window, closes, highs, lows, volumes
 from app.engine.regime import score_regime
 from app.engine.sectors import score_sectors
 from app.engine.universe_resolver import resolve_members
@@ -110,15 +110,16 @@ def _raw_components(
     window_1m = icfg.rs_windows["1m"]
     window_3m = icfg.rs_windows["3m"]
 
-    bars = bars_asof(session, ticker, asof)
     # iter-26 (J-16, fast-platform item F): a 30-year bars_asof series can carry ~5,300 bars on a
     # late as-of date, but every component below reads only a TRAILING window off the end (the
-    # largest is `high_window_52w`, 252). Slicing to the last `max_lookback_bars` bars BEFORE any
-    # indicator runs is byte-identical (every consumer already computes from the series' end — see
-    # `test_scoring_window.py`) and avoids feeding thousands of irrelevant older bars through them. A
-    # member with fewer than max_lookback_bars bars keeps its whole (shorter) series — short-history
-    # NA propagation is unaffected.
-    bars = bars[-icfg.max_lookback_bars:]
+    # largest is `high_window_52w`, 252). iter-27 (J-16 memory fix): read the bounded trailing window
+    # DIRECTLY via `bars_asof_window` instead of the two-step `bars_asof(...)` + `bars[-N:]` slice, so
+    # the discarded older prefix (up to ~5,300 bars, per ticker, per date, across the full universe —
+    # a per-(date,symbol) transient-allocation driver on the full-universe rebuild) is never
+    # materialized in the first place. Mathematically identical to the old two-step slice (byte-
+    # identity: `test_scoring_window.py`); a member with fewer than max_lookback_bars bars still keeps
+    # its whole (shorter) series — short-history NA propagation is unaffected.
+    bars = bars_asof_window(session, ticker, asof, icfg.max_lookback_bars)
     series = closes(bars)
     vols = volumes(bars)
     hi, lo = highs(bars), lows(bars)
@@ -344,11 +345,12 @@ def score_stocks(session: Session, asof: date_cls, config: Optional[Config] = No
 
         # as-of bars read ONCE (date <= asof, no lookahead), reused for BOTH the invalidation level
         # and the VCP detector — no extra DB round-trip.
-        bars = bars_asof(session, ticker, asof)
         # iter-26 (J-16, item F): same bounded trailing-window slice as `_raw_components` above — every
         # pattern detector below reads only a trailing window (the largest min_history_bars is 90),
-        # well within max_lookback_bars — byte-identical, see `test_scoring_window.py`.
-        bars = bars[-icfg.max_lookback_bars:]
+        # well within max_lookback_bars. iter-27 (J-16 memory fix): read it directly via
+        # `bars_asof_window` (never materializes the discarded older prefix) — byte-identical, see
+        # `test_scoring_window.py`.
+        bars = bars_asof_window(session, ticker, asof, icfg.max_lookback_bars)
         inv_closes = closes(bars)
         # invalidation level: the canonical `sma` over the config invalidation period (the level ==
         # the chart's MA-series endpoint).
diff --git a/apps/backend/tests/test_scoring_window.py b/apps/backend/tests/test_scoring_window.py
index 0b716c0..9e01a9e 100644
--- a/apps/backend/tests/test_scoring_window.py
+++ b/apps/backend/tests/test_scoring_window.py
@@ -14,18 +14,32 @@ boundary date where at least one resolved member genuinely has fewer than `max_l
 (the short-history path). Modeled on `test_bar_cache.py`'s `test_cached_snapshot_equals_uncached_row_level`
 / `test_bootstrap_snapshots_equal_with_cache` idiom (a real seed load, real `score_stocks` calls, full
 dict equality) rather than inventing a new comparison style.
+
+iter-27 (J-16 memory fix) adds two sibling proofs to the same file:
+  - `bars_asof_window(session, symbol, d, lookback)` (the new additive `prices.py` accessor that avoids
+    materializing the whole `<= d` prefix) is BYTE-IDENTICAL to `bars_asof(session, symbol, d)[-lookback:]`
+    — both the default (no-context) path and the cache-active path, for a long- and a short-history
+    symbol, covering the boundary cases from the plan (empty/no-bar symbol, `d` before the first bar, `d`
+    after the last bar, `lookback` larger than available history).
+  - `score_regime` (now routed through `bars_asof_window` at its three call sites) is BYTE-IDENTICAL with
+    the committed windowed config (320) vs. an effectively-disabled window — over the same >= 3 real
+    cadence dates the `score_stocks` harness above uses.
 """
 from __future__ import annotations
 
+from datetime import date, timedelta
+
 import pytest
 from sqlmodel import Session
 
 from app.config import Config, load_config
 from app.db import create_db_and_tables, make_engine
 from app.engine.data_manager import _trading_days
-from app.engine.prices import bar_cache, bars_asof
+from app.engine.prices import bar_cache, bars_asof, bars_asof_window
+from app.engine.regime import score_regime
 from app.engine.scoring import score_stocks
 from app.engine.universe_resolver import resolve_members
+from app.models import DailyPrice
 from app.seed_loader import load_seed
 
 # An effectively-"disabled" window: larger than any real bar series in the committed seed (~30 years is
@@ -130,3 +144,117 @@ def test_score_stocks_windowed_equals_unwindowed_for_short_history_member(seed_e
     unwindowed_by_ticker = {r["ticker"]: r for r in unwindowed["rows"]}
     for ticker in short_history_tickers:
         assert windowed_by_ticker[ticker] == unwindowed_by_ticker[ticker]
+
+
+# ==================================================================================================
+# iter-27 (J-16 memory fix) — score_regime windowed-vs-unwindowed (the regime routing gate)
+# ==================================================================================================
+def test_score_regime_windowed_equals_unwindowed_across_dates(seed_engine):
+    """The iter-27 correctness gate for `regime.py`'s new `bars_asof_window`/`close_on` routing:
+    `score_regime(D)` is BYTE-IDENTICAL with the committed windowed config (max_lookback_bars=320) vs.
+    an effectively-unwindowed config, over the SAME 3 real, well-spread cadence dates x the full pool
+    the `score_stocks` harness above uses — 0 diffs across every value `score_regime` returns (index
+    MA-stack, universe breadth, new-high/low, the VIX gate)."""
+    engine, cfg, trading = seed_engine
+    windowed_cfg = cfg  # config.yaml's real committed value (320)
+    unwindowed_cfg = _with_max_lookback_bars(cfg, DISABLED_WINDOW)
+
+    n = len(trading)
+    assert n >= 20, "the seed calendar should have plenty of trading days"
+    indexes = sorted({n // 5, n // 2, n - 5})
+    assert len(indexes) == 3, "the 3 sample indexes must be distinct"
+    dates = [trading[i] for i in indexes]
+
+    # Guard against a VACUOUS pass: on the deepest (latest) date, at least one of the regime engine's OWN
+    # inputs (an index ETF, a universe symbol, or the VIX symbol) must genuinely carry MORE than
+    # `max_lookback_bars` own bars — otherwise windowed vs unwindowed would compare two configs that slice
+    # nothing differently here, proving nothing about the new `_index_ma_stack`/`_universe_stats` routing.
+    deepest = dates[-1]
+    with Session(engine) as probe_session:
+        regime_symbols = list(cfg.etfs.index) + list(cfg.universe.symbols) + list(cfg.etfs.volatility)
+        deep_counts = [len(bars_asof(probe_session, s, deepest)) for s in regime_symbols]
+    assert deep_counts and max(deep_counts) > cfg.indicators.max_lookback_bars, (
+        f"expected >= 1 regime input symbol with > {cfg.indicators.max_lookback_bars} bars on {deepest} "
+        f"(max found: {max(deep_counts) if deep_counts else 0}) — the windowing path would be untested"
+    )
+
+    for d in dates:
+        with Session(engine) as windowed_session:
+            windowed = score_regime(windowed_session, d, windowed_cfg)
+        with Session(engine) as unwindowed_session:
+            unwindowed = score_regime(unwindowed_session, d, unwindowed_cfg)
+        assert windowed == unwindowed, f"windowed vs unwindowed score_regime diverged on {d}"
+        assert windowed["score"] is not None, f"the sample date {d} should produce a regime score"
+
+
+# ==================================================================================================
+# iter-27 (J-16 memory fix) — bars_asof_window direct unit coverage (default + cache-active paths)
+# ==================================================================================================
+@pytest.fixture()
+def window_price_engine(tmp_path):
+    """A hand-built two-symbol DB for `bars_asof_window` unit coverage: "SHORT" (5 gapped bars, the same
+    shape `test_forward_testing.py`'s `tiny_price_engine` uses) and "LONG" (60 consecutive daily bars) —
+    enough for a `lookback` to both TRUNCATE (LONG) and EXCEED available history (SHORT). A third,
+    never-inserted symbol ("NOBAR") covers the empty-cache / zero-bar case."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'window.db'}")
+    create_db_and_tables(engine)
+    short_days = [date(2024, 1, d) for d in (2, 3, 4, 5, 8)]  # a gap at the 6th/7th (weekend-like)
+    long_days = [date(2024, 2, 1) + timedelta(days=i) for i in range(60)]  # consecutive, no gap
+    with Session(engine) as session:
+        for i, d in enumerate(short_days):
+            c = float(10 + i)
+            session.add(
+                DailyPrice(symbol="SHORT", date=d, open=c, high=c + 1, low=c - 1, close=c, volume=100.0 + i)
+            )
+        for i, d in enumerate(long_days):
+            c = float(100 + i)
+            session.add(
+                DailyPrice(symbol="LONG", date=d, open=c, high=c + 1, low=c - 1, close=c, volume=1000.0 + i)
+            )
+        session.commit()
+    return engine, short_days, long_days
+
+
+def _tail_via_bars_asof(session: Session, symbol: str, d: date, lookback: int) -> list[tuple]:
+    """The reference definition `bars_asof_window` must match exactly: the ordinary `bars_asof(...)[-
+    lookback:]` slice's `(date, close)` pairs, same order — computed the OLD (unbounded-prefix) way."""
+    full = bars_asof(session, symbol, d)
+    tail = full[-lookback:] if lookback > 0 else []
+    return [(b.date, b.close) for b in tail]
+
+
+def test_bars_asof_window_matches_tail_slice_default_and_cached(window_price_engine):
+    """`bars_asof_window` is BYTE-IDENTICAL to `bars_asof(...)[-lookback:]`, in BOTH the default
+    (no-context) path and the cache-active path — the same cache-vs-default pairing style
+    `test_forward_testing.py`'s `close_on`/`bars_after` cache-awareness tests use — covering every
+    boundary case from the iter-27 plan: a lookback that truncates a long series (`cut > lookback`), a
+    lookback that EXCEEDS a short series' whole history (`cut < lookback`), `d` before the symbol's
+    first bar (`cut == 0`), `d` on/after the last bar (`cut == len(full)`), and a symbol with NO bars at
+    all (empty cache)."""
+    engine, short_days, long_days = window_price_engine
+    probes = [
+        ("LONG", long_days[45], 10),                      # mid-series: lookback (10) truncates a 46-bar prefix
+        ("LONG", long_days[-1], 10),                       # cut == len(full): the last bar itself
+        ("LONG", long_days[-1] + timedelta(days=5), 10),   # d strictly after the last bar: cut == len(full)
+        ("LONG", long_days[0], 10),                        # cut == 1: lookback (10) exceeds the 1-bar prefix
+        ("SHORT", short_days[2], 10),                       # lookback (10) EXCEEDS SHORT's whole history (5 bars)
+        ("SHORT", date(2023, 12, 31), 10),                 # d before SHORT's first bar: cut == 0
+        ("NOBAR", date(2024, 6, 1), 10),                   # a symbol with zero bars: empty cache, cut == 0
+    ]
+    with Session(engine) as plain:
+        reference = {p: _tail_via_bars_asof(plain, p[0], p[1], p[2]) for p in probes}
+    with Session(engine) as plain2:
+        uncached = {
+            p: [(b.date, b.close) for b in bars_asof_window(plain2, p[0], p[1], p[2])] for p in probes
+        }
+    assert uncached == reference
+    with Session(engine) as cached_session, bar_cache(cached_session):
+        cached = {
+            p: [(b.date, b.close) for b in bars_asof_window(cached_session, p[0], p[1], p[2])]
+            for p in probes
+        }
+    assert cached == reference
+    # sanity: the truncating, whole-history, and empty cases actually exercise different branches.
+    assert len(reference[("LONG", long_days[45], 10)]) == 10  # truncated
+    assert len(reference[("SHORT", short_days[2], 10)]) == 3  # whole (SHORT's <= d prefix is 3 bars)
+    assert reference[("NOBAR", date(2024, 6, 1), 10)] == []
diff --git a/config.yaml b/config.yaml
index 9952a70..800dd17 100644
--- a/config.yaml
+++ b/config.yaml
@@ -1231,6 +1231,7 @@ server:
   timeout_keep_alive_seconds: 65           # uvicorn keep-alive idle timeout (a heavy /api/data warm read is ~10s; this bounds an idle-kept connection generously above that)
   graceful_timeout_seconds: 120            # uvicorn --timeout-graceful-shutdown: bound how long a heavy in-flight request may delay shutdown
   memory_cap_mb: 6144                      # ulimit -v virtual-memory cap (MB) for the backend process: clears the one-copy ~3.27M-row bar prefill (iter-19: now a streamed, column-projected load — retained footprint ~0.4-0.5 GB, not the ~6.8 GB whole-table ORM `.all()` load this cap used to barely clear) + headroom; a pathological N-copy spike is OOM-killed as ONE process, never a VM-wide swap freeze
+  malloc_arena_max: 2                      # iter-27 (anti-goal #8): MALLOC_ARENA_MAX exported by start-backend.sh. glibc otherwise creates up to 8*ncpus (128 on a 16-core host) independent malloc arenas, each retaining freed-but-unreturned address space; across the uvicorn threadpool + parallel backfill workers that fragments VSZ and pins the ulimit -v ceiling on a SECOND full-universe rebuild. Capping to 2 arenas bounds that fragmentation (the dominant VSZ lever behind the iter-26/iter-27 rebuild crash) — byte-identical outputs (allocator layout only, never a stored/served value)
 
 # ----------------------------------------------------------------------------------------
 # iter-12 CONSUMED — Methodology / Glossary catalog (J-12). The SINGLE config-backed source that
diff --git a/incredible_auto_dev/.claude/agents/auditor.md b/incredible_auto_dev/.claude/agents/auditor.md
index 96ce32f..8ff3e29 100644
--- a/incredible_auto_dev/.claude/agents/auditor.md
+++ b/incredible_auto_dev/.claude/agents/auditor.md
@@ -2,7 +2,7 @@
 name: auditor
 description: Post-QA auditor. Reads the phase spec, all handoffs, QA report with functional test results, and actual implementation code. Skeptically assesses whether the phase goal was truly achieved. Applies fixes for critical issues found. Writes audit report with PASS, PASS_WITH_GAPS, or FAIL verdict.
 model: claude-opus-4-8
-disallowed_tools: ["Bash(rm -rf /*)", "Bash(rm -rf /)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
+disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
 version: 1.1.1
 last_updated: 2026-07-03
 ---
diff --git a/incredible_auto_dev/.claude/agents/browser-qa-agent.md b/incredible_auto_dev/.claude/agents/browser-qa-agent.md
index 6865f75..749d9bd 100644
--- a/incredible_auto_dev/.claude/agents/browser-qa-agent.md
+++ b/incredible_auto_dev/.claude/agents/browser-qa-agent.md
@@ -2,7 +2,7 @@
 name: browser-qa-agent
 description: Browser QA agent. Executes user-visible UI tests through browser automation using Chrome MCP. Tests real workflows, not just page loads. Records pass/fail with evidence. Runs after ui-test-designer completes.
 model: claude-sonnet-5
-disallowed_tools: ["Bash(rm -rf /*)", "Bash(rm -rf /)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
+disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
 version: 1.0.2
 last_updated: 2026-07-04
 ---
diff --git a/incredible_auto_dev/.claude/agents/coherence-auditor.md b/incredible_auto_dev/.claude/agents/coherence-auditor.md
index a774fc7..75629ff 100644
--- a/incredible_auto_dev/.claude/agents/coherence-auditor.md
+++ b/incredible_auto_dev/.claude/agents/coherence-auditor.md
@@ -2,7 +2,7 @@
 name: coherence-auditor
 description: Coherence auditor (goal mode). Audits each iteration's diff against the session blueprint (information architecture + data contract). Hard-fails only on objective rules — a contract value recomputed in a new code path, a contract value served from a non-canonical endpoint, or a new feature with no navigation path / a duplicate home for an existing entity. Subjective issues are advisory. Runs after the iteration's dispatch and before the goal-evaluator.
 model: claude-sonnet-5
-disallowed_tools: ["Bash(rm -rf /*)", "Bash(rm -rf /)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
+disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
 version: 1.0.3
 last_updated: 2026-07-04
 ---
diff --git a/incredible_auto_dev/.claude/agents/demo-narrator.md b/incredible_auto_dev/.claude/agents/demo-narrator.md
index 2c25c16..3cc275c 100644
--- a/incredible_auto_dev/.claude/agents/demo-narrator.md
+++ b/incredible_auto_dev/.claude/agents/demo-narrator.md
@@ -3,7 +3,7 @@ name: demo-narrator
 description: Per-iteration product demonstrator. Authors a machine-executable demo-script JSON (steps + plain-language narration) from the iteration's already-verified UI flows — it does NOT drive a browser. The deterministic Playwright runner (demo_runner.py) executes that JSON to produce the live walkthrough and the recorded screenshot gallery. Flags steps added or changed this iteration as `[NEW]`. Showcase, not QA — a failed step is a soft note, never a hard pipeline fail. Modes (selected by the dispatch wrapper) - record / live (this iteration's working surface) and session (the whole working product across iterations).
 model: claude-sonnet-5
 tools: [Read, Glob, Grep, Write]
-disallowed_tools: ["Bash(rm -rf /*)", "Bash(rm -rf /)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
+disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
 version: 2.0.0
 last_updated: 2026-05-22
 ---
diff --git a/incredible_auto_dev/.claude/agents/developer.md b/incredible_auto_dev/.claude/agents/developer.md
index 98bc103..b6615cb 100644
--- a/incredible_auto_dev/.claude/agents/developer.md
+++ b/incredible_auto_dev/.claude/agents/developer.md
@@ -2,7 +2,7 @@
 name: developer
 description: Implementation agent. Reads the execution plan from runs/<phase>/plan.md, implements changes following TDD. Handles both backend and frontend work. On retry, reads existing review/QA reports and fixes only the listed issues. Writes dev handoff when complete.
 model: claude-sonnet-5
-disallowed_tools: ["Bash(rm -rf /*)", "Bash(rm -rf /)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
+disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
 version: 1.1.1
 last_updated: 2026-07-03
 ---
diff --git a/incredible_auto_dev/.claude/agents/goal-decomposer.md b/incredible_auto_dev/.claude/agents/goal-decomposer.md
index 6769a37..f7c9c20 100644
--- a/incredible_auto_dev/.claude/agents/goal-decomposer.md
+++ b/incredible_auto_dev/.claude/agents/goal-decomposer.md
@@ -3,7 +3,7 @@ name: goal-decomposer
 description: Goal-mode iteration planner. Reads docs/goal.md (with Must-have user journeys + Anti-goals), the journey-history, and codebase state, then writes the next iteration spec to docs/phases/goal-<sid>-iter-<N>.md. Picks lean or full depth. Has a baseline mode (Mode: baseline) for iteration 0 that writes a verify-only spec.
 model: claude-opus-4-8
 tools: [Read, Glob, Grep, Bash, Write]
-disallowed_tools: ["Bash(rm -rf /*)", "Bash(rm -rf /)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
+disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
 version: 1.3.0
 last_updated: 2026-07-07
 ---
diff --git a/incredible_auto_dev/.claude/agents/goal-evaluator.md b/incredible_auto_dev/.claude/agents/goal-evaluator.md
index 9d8633c..aee0353 100644
--- a/incredible_auto_dev/.claude/agents/goal-evaluator.md
+++ b/incredible_auto_dev/.claude/agents/goal-evaluator.md
@@ -3,7 +3,7 @@ name: goal-evaluator
 description: Goal-mode iteration evaluator. Reads iteration outputs (handoffs, browser test results, evidence screenshots) plus accumulated journey-history. Produces a structured verdict (GOAL_ACHIEVED / CONTINUE / ESCALATE / REGRESSION / STALLED) and updates journey-history.json. Skeptical and evidence-grounded; the run-goal.sh outer loop relies on this agent's verdict to decide whether to halt.
 model: claude-opus-4-8
 tools: [Read, Glob, Grep, Bash, Write]
-disallowed_tools: ["Bash(rm -rf /*)", "Bash(rm -rf /)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
+disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
 version: 1.4.0
 last_updated: 2026-07-07
 ---
diff --git a/incredible_auto_dev/.claude/agents/goal-proposer.md b/incredible_auto_dev/.claude/agents/goal-proposer.md
index e18e0b1..1510fe7 100644
--- a/incredible_auto_dev/.claude/agents/goal-proposer.md
+++ b/incredible_auto_dev/.claude/agents/goal-proposer.md
@@ -3,7 +3,7 @@ name: goal-proposer
 description: Goal-mode continuous-improvement proposer (opt-in, default-off). After every Must-have journey passes, surveys the whole product via the project read/MCP tools + project-extensions/proposer-guidance.md, ranks improvements by the project usefulness lens, keeps only hold-out survivors, writes an enhancement-proposals backlog, and surgically appends the best as new Must-have journeys into docs/goal.md AUTO:journeys so goal mode keeps improving. Writes proposer-result.json (the honest dry/extended stop signal). Dispatched ONLY when the project provides proposer-guidance.md.
 model: claude-opus-4-8
 tools: [Read, Glob, Grep, Bash, Write, Edit]
-disallowed_tools: ["Bash(rm -rf /*)", "Bash(rm -rf /)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
+disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
 version: 1.1.0
 last_updated: 2026-07-08
 ---
diff --git a/incredible_auto_dev/.claude/agents/iteration-summarizer.md b/incredible_auto_dev/.claude/agents/iteration-summarizer.md
index 23fad31..a449407 100644
--- a/incredible_auto_dev/.claude/agents/iteration-summarizer.md
+++ b/incredible_auto_dev/.claude/agents/iteration-summarizer.md
@@ -3,7 +3,7 @@ name: iteration-summarizer
 description: Post-iteration summarizer. Reads the iteration's artifacts (dev handoff, review, browser QA, goal evaluator output, journey history, evaluator log) and writes a single conclusive iteration-summary.md that answers what was done, what's left, and what direction the project is moving. Runs near the end of every iteration (phase-mode Step 10.5 and goal-mode after goal-evaluator). Source of truth for the human-readable HTML renderer.
 model: claude-sonnet-5
 tools: [Read, Write]
-disallowed_tools: ["Bash(rm -rf /*)", "Bash(rm -rf /)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
+disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
 version: 1.1.0
 last_updated: 2026-07-07
 ---
diff --git a/incredible_auto_dev/.claude/agents/orchestrator.md b/incredible_auto_dev/.claude/agents/orchestrator.md
index df5ecde..5fe2a2e 100644
--- a/incredible_auto_dev/.claude/agents/orchestrator.md
+++ b/incredible_auto_dev/.claude/agents/orchestrator.md
@@ -2,7 +2,7 @@
 name: orchestrator
 description: Phase execution planner. When invoked by run-phase.sh, reads CLAUDE.md and the phase spec, then writes a concise execution plan to runs/<phase>/plan.md. The shell script (run-phase.sh) drives the dev/review/QA loop; the orchestrator's job is planning only.
 model: claude-sonnet-5
-disallowed_tools: ["Bash(rm -rf /*)", "Bash(rm -rf /)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
+disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
 version: 1.0.0
 last_updated: 2026-05-04
 ---
diff --git a/incredible_auto_dev/.claude/agents/phase-closure-auditor.md b/incredible_auto_dev/.claude/agents/phase-closure-auditor.md
index 412630e..1ffc6ba 100644
--- a/incredible_auto_dev/.claude/agents/phase-closure-auditor.md
+++ b/incredible_auto_dev/.claude/agents/phase-closure-auditor.md
@@ -2,7 +2,7 @@
 name: phase-closure-auditor
 description: Phase closure auditor. Validates that all required UI visibility artifacts exist, are non-vague, and are consistent with each other. Blocks phases from completing when UI artifacts are missing or the feature is backend-only but described as complete product capability. Final gate before finalize.
 model: claude-sonnet-5
-disallowed_tools: ["Bash(rm -rf /*)", "Bash(rm -rf /)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
+disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
 version: 1.0.0
 last_updated: 2026-05-04
 ---
diff --git a/incredible_auto_dev/.claude/agents/product-manager.md b/incredible_auto_dev/.claude/agents/product-manager.md
index 7b6aee0..1fb1af6 100644
--- a/incredible_auto_dev/.claude/agents/product-manager.md
+++ b/incredible_auto_dev/.claude/agents/product-manager.md
@@ -3,7 +3,7 @@ name: product-manager
 description: Optional architecture and planning agent. Reads phase specs and existing code to produce detailed implementation plans. Does NOT write code. Use before developer agent when a phase is complex or when you need to validate that a proposed approach fits the architecture.
 model: claude-sonnet-5
 tools: [Read, Glob, Grep, WebSearch]
-disallowed_tools: ["Bash(rm -rf /*)", "Bash(rm -rf /)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
+disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
 version: 1.0.0
 last_updated: 2026-05-04
 ---
diff --git a/incredible_auto_dev/.claude/agents/qa.md b/incredible_auto_dev/.claude/agents/qa.md
index 80d01c1..be21ef9 100644
--- a/incredible_auto_dev/.claude/agents/qa.md
+++ b/incredible_auto_dev/.claude/agents/qa.md
@@ -2,7 +2,7 @@
 name: qa
 description: QA agent with two modes: (1) test plan generation — reads phase spec and produces a structured functional test plan before QA runs; (2) QA validation — runs tests, verifies artifacts, executes the functional test plan, does Chrome MCP browser checks when Frontend Present is yes, and writes a QA report. Use after reviewer passes.
 model: claude-haiku-4-5
-disallowed_tools: ["Bash(rm -rf /*)", "Bash(rm -rf /)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
+disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
 version: 1.1.1
 last_updated: 2026-07-03
 ---
diff --git a/incredible_auto_dev/.claude/agents/readme-maintainer.md b/incredible_auto_dev/.claude/agents/readme-maintainer.md
index 95753c2..6f849bb 100644
--- a/incredible_auto_dev/.claude/agents/readme-maintainer.md
+++ b/incredible_auto_dev/.claude/agents/readme-maintainer.md
@@ -3,7 +3,7 @@ name: readme-maintainer
 description: Project README maintainer (goal mode). After each iteration, refreshes the project-root README.md so it reflects the current capabilities of the whole project and carries an accurate "How to run" section. Edits only marker-delimited AUTO blocks so hand-written prose is preserved, and grounds every install/run/test command in .claude/project-template.md. Non-blocking showcase/maintenance step — never gates the pipeline.
 model: claude-sonnet-5
 tools: [Read, Write, Edit, Glob, Grep]
-disallowed_tools: ["Bash(rm -rf /*)", "Bash(rm -rf /)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
+disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
 version: 1.0.0
 last_updated: 2026-06-04
 ---
diff --git a/incredible_auto_dev/.claude/agents/release-manager.md b/incredible_auto_dev/.claude/agents/release-manager.md
index 586e714..da21a54 100644
--- a/incredible_auto_dev/.claude/agents/release-manager.md
+++ b/incredible_auto_dev/.claude/agents/release-manager.md
@@ -2,7 +2,7 @@
 name: release-manager
 description: Git and GitHub release agent. Creates feature branches, commits changes, pushes to origin, opens PRs, and merges them. Only invoked by the user or orchestrator after all review and QA pass. Requires gh CLI to be authenticated.
 model: claude-haiku-4-5
-disallowed_tools: ["Bash(rm -rf /*)", "Bash(rm -rf /)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)"]
+disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)"]
 version: 1.0.0
 last_updated: 2026-05-04
 ---
diff --git a/incredible_auto_dev/.claude/agents/retro-analyst.md b/incredible_auto_dev/.claude/agents/retro-analyst.md
new file mode 100644
index 0000000..5661985
--- /dev/null
+++ b/incredible_auto_dev/.claude/agents/retro-analyst.md
@@ -0,0 +1,75 @@
+---
+name: retro-analyst
+description: Post-session retrospective analyst. Reads ONLY the frozen retro-input.md evidence digest at terminal halts and drafts 1-5 candidate framework-improvement items for human triage. Proposals only — never edits the roadmap. Non-blocking showcase-class step.
+model: claude-haiku-4-5
+tools: [Read, Write]
+disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
+version: 1.0.0
+last_updated: 2026-07-10
+---
+
+# Retro Analyst
+
+You turn one finished goal-mode session's frozen evidence digest into 1-5 CANDIDATE framework-improvement items for a human to triage. You are the drafting step of the EVO-2 feedback loop: a deterministic collector already froze everything you may use into a single file; you propose, a human decides. You never schedule work, never edit the roadmap, and never gate the pipeline — a weak or empty report must cost the session nothing.
+
+## Input — exactly ONE file
+
+Read ONLY the retro-input.md path given in your dispatch prompt (`runs/goal-session-<sid>/state/retro-input.md`). That file is the complete evidence boundary for this task.
+
+- Do NOT read telemetry.jsonl, journey-history.json, lessons.md, evaluator-log.md, iteration artifacts, docs/improvement-roadmap.md, or any other file. The digest exists precisely so you read one small file instead of session history (token policy).
+- The digest's stable sections are: `## Outcome`, `## Verdict sequence`, `## Agent economics`, `## Friction counters`, `## Lessons tail`, `## Halt context`.
+- Counters marked `unknown (<why>)` are gaps, not zeros. Never treat an `unknown` as a number; you MAY cite the `unknown (<why>)` line itself as evidence of an instrumentation gap worth fixing.
+
+## What counts as a signal
+
+Draft an item only when the digest shows recurring or structural FRAMEWORK pain — something a change to the pipeline, agents, scripts, or instrumentation could reduce for every future session:
+
+- A friction counter greater than zero (quota pauses, attempt-1 review FAILs, malformed-verdict rewrites).
+- A verdict-sequence pattern (a long CONTINUE run ending STALLED, repeated ESCALATE/REGRESSION churn).
+- An economics outlier (one agent dominating wall time or cost).
+- A lessons-tail entry describing pipeline/tooling pain (flaky dispatch, retry loops, missing evidence).
+- An `unknown (<why>)` counter — propose fixing the missing source, not the number.
+
+Product-specific pain (a fragile module in the app being built, a failing journey) is NOT a framework item — the goal loop itself handles those. If a lessons entry is about the product, skip it.
+
+## Candidate item shape
+
+Number items RETRO-1 … RETRO-5, at most 5, each ≤20 lines, in this exact shape (the roadmap's §4 item fields, proposal-weight):
+
+```
+### RETRO-<n> · <short title>
+- **Proposed:** P0|P1|P2 · Effort S|M|L · Risk LOW|MED|HIGH
+- **Problem:** <1-2 sentences — the recurring pain and who hits it>
+- **Evidence:** <digest section name> — "<exact line(s) quoted from retro-input.md>"
+- **Sketch:** <2-6 lines — a plausible direction, not a full spec>
+- **Verify idea:** <one line — how an implementer would prove it worked>
+```
+
+Hard rule: no Evidence line → no item. Every Evidence entry names the digest section and quotes the line(s) verbatim, e.g. `Evidence: Friction counters — "Quota pauses: 3"`. Zero items is a valid output: when nothing recurred, the Candidate items body is exactly `nothing recurred worth proposing` plus one sentence saying why (e.g. all counters zero, lessons product-only).
+
+## Output
+
+Write exactly ONE file — the output path from your dispatch prompt (`reports/goal-session-<sid>-retro.md`), overwriting any existing file:
+
+```
+# Session retro — <sid>
+
+> **PROPOSALS ONLY** — a human promotes candidates into docs/improvement-roadmap.md §16
+> per EVO-1; nothing here is scheduled work.
+
+**Session:** <sid> · **Terminal status:** <from Outcome> · **Iterations:** <from Outcome>
+
+## Candidate items
+
+<RETRO-n blocks, or the zero-item line>
+```
+
+- Whole report ≤120 lines.
+- NEVER edit docs/improvement-roadmap.md or any file other than the output path.
+- No tool use beyond Read and Write. No Bash, no agents, no URLs.
+- Write the report and STOP. Do not print the report to chat.
+
+## Token and Questioning Policy
+
+Apply `.claude/core.md` strictly. Agent-specific guidance:
+- Do NOT ask the user clarifying questions. If the digest is degraded (sections missing, counters unknown), work with what is present — degraded input usually means fewer or zero items, and that is a correct outcome.
diff --git a/incredible_auto_dev/.claude/agents/reviewer.md b/incredible_auto_dev/.claude/agents/reviewer.md
index 8f49860..92906c2 100644
--- a/incredible_auto_dev/.claude/agents/reviewer.md
+++ b/incredible_auto_dev/.claude/agents/reviewer.md
@@ -3,7 +3,7 @@ name: reviewer
 description: Code reviewer. Reads dev handoffs and diffs to assess implementation quality against the phase spec and project standards. Writes a structured review report. NEVER implements fixes directly — only writes the report with actionable fix tasks. Use after implementation completes and before QA.
 model: claude-sonnet-5
 tools: [Read, Glob, Grep, Bash, Write, Edit]
-disallowed_tools: ["Bash(rm -rf /*)", "Bash(rm -rf /)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
+disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
 version: 1.1.2
 last_updated: 2026-07-04
 ---
diff --git a/incredible_auto_dev/.claude/agents/ui-impact-analyst.md b/incredible_auto_dev/.claude/agents/ui-impact-analyst.md
index ea91d8c..e717a66 100644
--- a/incredible_auto_dev/.claude/agents/ui-impact-analyst.md
+++ b/incredible_auto_dev/.claude/agents/ui-impact-analyst.md
@@ -2,7 +2,7 @@
 name: ui-impact-analyst
 description: Post-dev UI impact analyst. Reads the phase diff and handoffs, maps code changes to user-visible UI surfaces, identifies what changed for users vs what is backend-only. Produces user-visible-changes and ui-surface-map reports. Runs after dev+review passes.
 model: claude-sonnet-5
-disallowed_tools: ["Bash(rm -rf /*)", "Bash(rm -rf /)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
+disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
 version: 1.0.0
 last_updated: 2026-05-04
 ---
diff --git a/incredible_auto_dev/.claude/agents/ui-test-designer.md b/incredible_auto_dev/.claude/agents/ui-test-designer.md
index 30ad297..90ceb8b 100644
--- a/incredible_auto_dev/.claude/agents/ui-test-designer.md
+++ b/incredible_auto_dev/.claude/agents/ui-test-designer.md
@@ -2,7 +2,7 @@
 name: ui-test-designer
 description: UI test designer. Converts UI impact analysis into a practical human-readable test plan with exact click paths and a 5-minute operator verification guide. Runs after ui-impact-analyst completes.
 model: claude-sonnet-5
-disallowed_tools: ["Bash(rm -rf /*)", "Bash(rm -rf /)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
+disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
 version: 1.0.0
 last_updated: 2026-05-04
 ---
diff --git a/incredible_auto_dev/.claude/agents/ux-regression-reviewer.md b/incredible_auto_dev/.claude/agents/ux-regression-reviewer.md
index 3f4214a..9ffc6cc 100644
--- a/incredible_auto_dev/.claude/agents/ux-regression-reviewer.md
+++ b/incredible_auto_dev/.claude/agents/ux-regression-reviewer.md
@@ -2,7 +2,7 @@
 name: ux-regression-reviewer
 description: UX regression reviewer. Checks whether the UI evolved appropriately with the phase's new capabilities. Flags features that exist in backend but are invisible or undiscoverable in the UI. Flags existing user journeys that may have regressed. Runs after browser QA and before the main auditor.
 model: claude-sonnet-5
-disallowed_tools: ["Bash(rm -rf /*)", "Bash(rm -rf /)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
+disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
 version: 1.0.0
 last_updated: 2026-05-04
 ---
diff --git a/incredible_auto_dev/.claude/anti-patterns.md b/incredible_auto_dev/.claude/anti-patterns.md
index 516d6e8..0081f35 100644
--- a/incredible_auto_dev/.claude/anti-patterns.md
+++ b/incredible_auto_dev/.claude/anti-patterns.md
@@ -283,4 +283,25 @@ This is especially bad for AI-agent scripts: the wrapped `claude` keeps consumin
 
 **Prevention (project side, optional but better):** give build/QA/typecheck commands their own dist dir so they never touch the dev build. Next.js reads `distDir` from `next.config.{js,ts}` (NOT an env var by default), so wire it through config — e.g. `distDir: process.env.NEXT_DIST_DIR || '.next'` — and run builds with `NEXT_DIST_DIR=.next-qa next build`. Agents MUST NOT run a production `next build` while the demo/QA `next dev` is up unless the build is isolated this way.
 
-**Detection:** a frontend start log (e.g. `/tmp/fanout-frontend-<port>.log`) showing `MODULE_NOT_FOUND` / `Cannot find module` with a `GET / 500` and a `.next/server/...` require stack is the signature. `_next_build_is_corrupt` in `common.sh` greps for exactly this.
+**Detection:** the frontend start log (`$QA_FRONTEND_LOG` — under the run's `CHAIN_TMPDIR`, e.g. `.../fanout-frontend-<port>.log`) showing `MODULE_NOT_FOUND` / `Cannot find module` with a `GET / 500` and a `.next/server/...` require stack is the signature. `_next_build_is_corrupt` in `common.sh` greps for exactly this.
+
+---
+
+## 21. Shared /tmp accumulation and cross-job pytest tmp races
+
+**Pattern:** Nothing sets `TMPDIR`, so every tool the agents run (pytest, playwright/chromium, `mktemp`) writes into shared `/tmp`. pytest's default basetemp `/tmp/pytest-of-<user>/` is keyed on the USER, not the run — concurrent pipeline jobs (different projects, same machine, same user) share it and race pytest's own "keep last 3, rmtree older" pruning (`Directory not empty`, lock races, stale undeletable dirs). Meanwhile the harness's own temp files pile up forever: kept-on-failure `claude-quota-*.log`s, telemetry usage sidecars leaked on every non-success path, and per-role service logs (`fanout-*`, `demo-*`, `goal-iter-*`) that no cleanup path ever targeted. Cleanup ran only on run-phase.sh's success path — never on `fail()`, quota/transport/signal exits, or lean goal iterations.
+
+**Why it fails:** `/tmp` is a shared namespace with no run identifier, so no cleanup step can safely delete anything (it might belong to a concurrent job) — and agents could not delete anyway (see the rm-ban fix: deny-rule over-match + Claude Code's built-in rm working-directory containment). The only "cleanup" was pytest pruning itself, which is exactly the thing that races.
+
+**Prevention:** per-run tmp isolation via `lib/chain-tmp.sh`:
+- Every entry script (run-phase.sh, run-goal.sh, goal-iter-lean.sh) calls `chain_tmp_init <run-id>`, which creates `/tmp/iad.<id>.<pid>` and exports it as `TMPDIR`/`TMP`/`TEMP`; a nested script ADOPTS the inherited dir (owner-guarded). NEW pipeline entry scripts MUST do the same.
+- Cleanup is an EXIT trap (fires on success, fail(), quota 75, transport 70, signal exits) plus `chain_tmp_rotate` at the goal-mode iteration boundary — after `_join_showcase_tail`, never right after the evaluator (the async showcase tail still writes there).
+- New `mktemp` calls MUST use a `"${TMPDIR:-/tmp}/…"` template, never a hardcoded `/tmp/...` template.
+- Files deliberately kept for debugging MUST be moved to `$CHAIN_TRACE_DIR` (`_quota_preserve_failure_log`), never left in tmp.
+- The ONLY sanctioned fixed-name /tmp files are the two quota sentinels (`/tmp/{claude,codex}-quota-exhausted`) — quota is account-global, every concurrent job must see the same sentinel, and `chain_tmp_janitor` never matches their names.
+- `chain_tmp_janitor` (entry-script start) reaps strays: `iad.*` dirs that are old AND whose owner pid is dead, legacy loose temp files, and `/tmp/pytest-of-$USER` entries older than `CHAIN_TMP_MAX_AGE_HOURS` (default 24h).
+
+**Example (bad):** `tmp_log=$(mktemp /tmp/claude-quota-XXXXXX.log)` + keep-on-failure with no reaper — one leaked file per failed/quota invocation, forever.
+**Example (good):** `tmp_log=$(mktemp "${TMPDIR:-/tmp}/claude-quota-XXXXXX.log")`; on failure `_quota_preserve_failure_log "$tmp_log" claude-failure` moves it under `runs/<phase>/trace/`.
+
+**Detection:** `ls /tmp/pytest-of-$(id -un)` showing many numbered dirs, or `/tmp` littered with `claude-quota-*.log` / `<role>-<port>.log` files older than a day. During a healthy run there should be exactly ONE `/tmp/iad.*` dir per live pipeline job, and it disappears when the run exits.
diff --git a/incredible_auto_dev/.claude/architecture/agents.md b/incredible_auto_dev/.claude/architecture/agents.md
index bfaebae..6f3b455 100644
--- a/incredible_auto_dev/.claude/architecture/agents.md
+++ b/incredible_auto_dev/.claude/architecture/agents.md
@@ -1,6 +1,6 @@
 # Agents
 
-The framework defines 19 agents in `.claude/agents/` (rendered from `agents/<name>/`). Each agent has a `model_tier` in its `agent.yaml`, resolved via `config/model-tiers.yaml`. Twelve serve the phase pipeline; four are goal-mode agents (goal-decomposer, goal-evaluator, coherence-auditor, goal-proposer); three are showcase/maintenance agents (iteration-summarizer, demo-narrator, readme-maintainer).
+The framework defines 20 agents in `.claude/agents/` (rendered from `agents/<name>/`). Each agent has a `model_tier` in its `agent.yaml`, resolved via `config/model-tiers.yaml`. Twelve serve the phase pipeline; four are goal-mode agents (goal-decomposer, goal-evaluator, coherence-auditor, goal-proposer); four are showcase/maintenance agents (iteration-summarizer, demo-narrator, readme-maintainer, retro-analyst — the last runs only at terminal goal-session halts, model_tier light, drafting improvement proposals from `state/retro-input.md`).
 
 ## Model Tiers
 
@@ -117,7 +117,7 @@ The framework defines 19 agents in `.claude/agents/` (rendered from `agents/<nam
 - **Output:** `reports/phase-{N}-closure-verdict.md`
 - **Role:** Final gate before finalize. Validates all UI artifacts exist, are non-vague, and are consistent. Blocks false completion.
 
-## Goal Mode Agents (4 — plus 3 showcase agents documented in CLAUDE.md and their agent files)
+## Goal Mode Agents (4 — plus 4 showcase agents documented in CLAUDE.md and their agent files)
 
 These agents are invoked only by the goal-mode pipeline (`run-goal.sh` and `goal-iter-lean.sh`). Phase mode does not use them. See [`goal-mode.md`](goal-mode.md) for how they fit into the loop.
 
@@ -152,7 +152,7 @@ model: <claude-model-id>
 tools: [...]                         # optional — Claude Code tool list
 version: 1.0.0
 last_updated: YYYY-MM-DD
-disallowed_tools: ["Bash(rm -rf *)"] # optional — added to default deny list
+disallowed_tools: ["WebFetch"]       # optional — added to default deny list
 max_budget_usd: 1.50                 # optional — per-invocation hard cap
 ---
 ```
diff --git a/incredible_auto_dev/.claude/architecture/goal-mode.md b/incredible_auto_dev/.claude/architecture/goal-mode.md
index 9de7184..b55718d 100644
--- a/incredible_auto_dev/.claude/architecture/goal-mode.md
+++ b/incredible_auto_dev/.claude/architecture/goal-mode.md
@@ -85,6 +85,8 @@ After the evaluator runs, the verdict directly drives the loop:
 
 **Quota exhaustion is NOT a halt.** The wrapped `claude_with_quota_retry` library transparently sleeps until the quota resets, then resumes the same agent invocation. Telemetry records the quota pause for observability.
 
+**Per-iteration tmp hygiene.** The engine owns a per-run tmp dir (`lib/chain-tmp.sh`, exported as `TMPDIR`): session-scoped at startup, then rotated to `/tmp/iad.goal-<sid>-iter-<N>.<pid>` at each iteration boundary — immediately after `_join_showcase_tail`, because the previous iteration's async showcase tail keeps writing demo logs until that join (never clean right after the evaluator). The `[run-goal] Tmp cleanup: cleared …` log line marks the step. Both dispatch depths adopt the engine's dir (owner-guarded), and the engine's EXIT trap removes the final dir on any halt. A startup janitor reaps strays from crashed sessions. See `.claude/anti-patterns.md` #21.
+
 **Blueprint approval pause (opt-in).** By default the blueprint is **auto-approved** (`AUTO_APPROVE_BLUEPRINT=true`): the gate touches `state/blueprint.approved`, clears any `state/blueprint.reapproval-requested` marker, and the run stays unattended. Pass `--require-blueprint-approval` to enable the checkpoint: then at the top of the loop, before the first building iteration (and again only when the decomposer flags a *structural* blueprint change), the loop sets `session.json.status = AWAITING_BLUEPRINT_APPROVAL` and exits 0 so the human can review `state/blueprint.md`; `--resume` continues (resuming counts as approval and creates `state/blueprint.approved`). The gate sits at the top of the loop precisely so the baseline-drafted blueprint is never re-drafted out from under the human.
 
 **GitHub auth preflight (`AWAITING_GITHUB_AUTH`).** Once before the loop (on both fresh-start and `--resume`), if the session will push (`push_per_iter` or `--auto-release`), `run-goal.sh` calls `check_git_push_access` (`lib/common.sh`) — a `GIT_TERMINAL_PROMPT=0` + ssh-BatchMode `git ls-remote origin` that tests git's real credential path without ever prompting. On failure: in an interactive terminal it runs `gh auth login` + `gh auth setup-git`, re-verifies, and continues; otherwise it sets `session.json.status = AWAITING_GITHUB_AUTH` and exits 0 (resumable, like the blueprint pause). This converts the old failure mode — a per-iter `git push` blocking forever on a username/password prompt when the GitHub HTTPS session expired — into a fail-fast preflight. The per-iter push itself is also wrapped in `GIT_TERMINAL_PROMPT=0`, so a session that expires mid-run fails that push fast and non-fatally rather than hanging. Bypass with `CHAIN_SKIP_GITHUB_PREFLIGHT=true`.
diff --git a/incredible_auto_dev/.claude/architecture/pipeline.md b/incredible_auto_dev/.claude/architecture/pipeline.md
index 67ce232..91fb195 100644
--- a/incredible_auto_dev/.claude/architecture/pipeline.md
+++ b/incredible_auto_dev/.claude/architecture/pipeline.md
@@ -140,3 +140,5 @@ Key contracts:
 - **Fallback to sequential.** Backend-only phases (`Frontend Present: no`) and resume runs where any of Steps 4–7 already completed skip the fanout block entirely and run the original sequential Step 4 → 5 → 6 → 6.5 → 7 blocks, each booting and tearing down its own services.
 
 Goal mode: full iterations dispatch through `run-phase.sh --no-finalize`, so the fanout runs there too. Lean iterations (`goal-iter-lean.sh`) have no parallelisable surface — dev → review → browser-qa → demo is strictly sequential — and run as today.
+
+**Per-run tmp isolation** (`lib/chain-tmp.sh`): `run-phase.sh` initializes `/tmp/iad.<phase>.<pid>` and exports it as `TMPDIR`, so pytest basetemps, chromium profiles, dispatch temp logs, and `_qa_log_path` service logs all land in one per-run dir (adopted, not re-created, when nested under run-goal.sh). The un-numbered cleanup block after Step 10.5 announces the dir; the actual removal happens in an EXIT trap that fires on EVERY exit path (success, `fail()`, quota 75, transport 70, signal aborts) and, on non-success, first archives bounded service-log tails to `runs/<phase>/service-logs/`. A janitor at startup reaps strays from crashed runs (age- and pid-liveness-gated). See `.claude/anti-patterns.md` #21.
diff --git a/incredible_auto_dev/.claude/hooks/guard-dangerous-commands.sh b/incredible_auto_dev/.claude/hooks/guard-dangerous-commands.sh
index 54d054f..368aa62 100644
--- a/incredible_auto_dev/.claude/hooks/guard-dangerous-commands.sh
+++ b/incredible_auto_dev/.claude/hooks/guard-dangerous-commands.sh
@@ -10,8 +10,13 @@ CMD="${1:-}"
 [ -z "$CMD" ] && exit 0
 
 DANGEROUS_PATTERNS=(
-  # Destructive recursive deletes — system and home paths
-  "rm -rf /"
+  # Destructive recursive deletes — system and home paths.
+  # NOTE: deliberately NO bare "rm -rf /" entry — as a fixed-substring match it
+  # hits EVERY absolute-path rm, including the /tmp cleanup the permission
+  # allow-list explicitly permits (on the Codex backend this hook is the real
+  # enforcement gate, so the false positive banned /tmp removals outright).
+  # Bare `rm -rf /` and `rm -rf /<non-tmp>` are caught by the anchored regex
+  # `^rm -rf /(?!tmp)` in DANGEROUS_REGEXES below.
   "rm -rf ~"
   "rm -rf /home"
   "rm -rf /root"
@@ -75,8 +80,10 @@ done
 DANGEROUS_REGEXES=(
   # mv/cp targeting system directories
   "^(mv|cp) .+ /(etc|usr|boot|lib|var|root|sys|proc)(/|$)"
-  # rm -rf with any absolute path (other than /tmp)
-  "^rm -rf /(?!tmp)"
+  # rm -rf with any absolute path (other than /tmp) — anchored at command
+  # start OR after a shell chain separator (;, &&, ||, |, &), so `x && rm -rf /etc`
+  # is caught while `rm -rf /tmp/...` cleanup stays permitted.
+  "(^|[;&|][[:space:]]*)rm -rf /(?!tmp)"
   # chown with absolute path targets
   "^(sudo )?chown .+ /(etc|usr|home|root|var|boot)"
   # docker run mounting host filesystem sensitive directories
diff --git a/incredible_auto_dev/.claude/model-orchestration.md b/incredible_auto_dev/.claude/model-orchestration.md
index a4cfd3c..3849299 100644
--- a/incredible_auto_dev/.claude/model-orchestration.md
+++ b/incredible_auto_dev/.claude/model-orchestration.md
@@ -132,6 +132,7 @@ An agent's claim about its own work is a hypothesis, not evidence.
 | `CHAIN_DISPATCH_REQUEUE_ON_TIMEOUT` | default `true`; one requeue after an interactive inflight timeout before pausing | `lib/interactive-dispatch.sh` |
 | `CHAIN_LEAN_PARALLEL_COHERENCE` | default `true`; lean iterations run the coherence audit concurrently with browser-qa | `goal-iter-lean.sh` |
 | `CHAIN_ASYNC_SHOWCASE` | default `true`; demo/summary/README/renders run in the background overlapping the next decomposer (CONTINUE/ESCALATE only; joined + committed before the next executor dispatch) | `run-goal.sh` |
+| `CHAIN_SESSION_RETRO` | default `true`; terminal halts (GOAL_ACHIEVED/STALLED/REGRESSION_HALT/BUDGET_EXHAUSTED) freeze a deterministic evidence snapshot to `state/retro-input.md` AND then dispatch the retro-analyst (light tier) to draft `reports/goal-session-<sid>-retro.md` improvement proposals from it (EVO-2); the drafting dispatch is skipped when the digest is missing; resumable pauses never fire either step; non-blocking — set `false` to disable both | `run-goal.sh`, `lib/retro_collect.sh` |
 | `CHAIN_AGENT_EFFORT` | opt-in experiment, e.g. `developer=high`; **judges are refused by a hardcoded guard**; auto-reverted by the telemetry tripwire on quality movement | `lib/agent_permissions.py` |
 
 If you disable a gate/routing knob for an experiment, **re-enable it in the same session**
diff --git a/incredible_auto_dev/.claude/settings.json b/incredible_auto_dev/.claude/settings.json
index a849c51..e6cc891 100644
--- a/incredible_auto_dev/.claude/settings.json
+++ b/incredible_auto_dev/.claude/settings.json
@@ -84,6 +84,8 @@
       "Bash(rm -rf *.egg-info*)",
       "Bash(rm -rf coverage*)",
       "Bash(rm -rf /tmp/*)",
+      "Bash(rm /tmp/*)",
+      "Bash(rm -f /tmp/*)",
       "Bash(chmod +x *)",
       "Bash(chmod -x *)",
       "Bash(chmod u+x *)",
@@ -150,7 +152,6 @@
     ],
     "deny": [
       "Bash(rm -rf /)",
-      "Bash(rm -rf /*)",
       "Bash(rm -rf ~)",
       "Bash(rm -rf ~/)",
       "Bash(rm -rf ~/*)",
@@ -205,6 +206,9 @@
       "Bash(apt-get upgrade*)",
       "Bash(apt dist-upgrade*)",
       "Bash(apt-get dist-upgrade*)"
+    ],
+    "additionalDirectories": [
+      "/tmp"
     ]
   },
   "hooks": {
diff --git a/incredible_auto_dev/CLAUDE.md b/incredible_auto_dev/CLAUDE.md
index 587432d..80a83f2 100644
--- a/incredible_auto_dev/CLAUDE.md
+++ b/incredible_auto_dev/CLAUDE.md
@@ -41,7 +41,7 @@ pipeline chain (orchestrator, developer, reviewer, qa, auditor, release-manager,
 product-manager), the UI chain (ui-impact-analyst, ui-test-designer, browser-qa-agent,
 phase-closure-auditor, ux-regression-reviewer), goal mode (goal-decomposer, goal-evaluator,
 coherence-auditor, goal-proposer), and showcase (iteration-summarizer, demo-narrator,
-readme-maintainer). Roles, inputs, and verdict contracts live in each agent file; the
+readme-maintainer, retro-analyst). Roles, inputs, and verdict contracts live in each agent file; the
 catalog with model tiers is [`.claude/architecture/agents.md`](.claude/architecture/agents.md).
 
 **Skills** (reusable methodologies) live in `.claude/skills/` — each agent's body names
diff --git a/incredible_auto_dev/README.md b/incredible_auto_dev/README.md
index 03a2e0a..90a9d7a 100644
--- a/incredible_auto_dev/README.md
+++ b/incredible_auto_dev/README.md
@@ -343,6 +343,7 @@ Iteration name `goal-<sid>-iter-<N>` is used as the "phase name" so existing scr
 | `coherence-auditor` | standard | (goal mode) | Audits each iteration's diff against the blueprint (information architecture + data contract); hard-fails only on objective drift |
 | `goal-proposer` | strong | (goal mode, opt-in) | After every Must-have journey passes, surveys the whole product through the project's usefulness lens (`project-extensions/proposer-guidance.md`), writes an enhancement-proposals backlog, and appends the best survivors as new Must-have journeys in `docs/goal.md` AUTO:journeys — runs only when that guidance file exists |
 | `readme-maintainer` | standard | (goal mode) | After each iteration, refreshes the project-root README's marker-delimited AUTO blocks so capabilities and "How to run" stay accurate; non-blocking showcase step, never gates the pipeline |
+| `retro-analyst` | light | (goal mode, terminal halts) | At a terminal goal-session halt, reads ONLY the frozen `state/retro-input.md` evidence digest and drafts 1-5 candidate framework-improvement proposals to `reports/goal-session-<sid>-retro.md` for human triage; proposals only, non-blocking, never edits the roadmap |
 
 Model tiers: each agent's `model_tier` lives in `agents/<name>/agent.yaml`; tiers resolve to model ids in `config/model-tiers.yaml`. Edit, then `python3 scripts/automation/sync-cli-assets.py` and commit the regenerated mirrors.
 
@@ -443,6 +444,8 @@ bash scripts/automation/render-summary.sh --session-index <sid>        # re-rend
 | `runs/goal-session-<sid>/state/journey-history.json` | Per-journey pass/fail/regressed status across iterations |
 | `runs/goal-session-<sid>/telemetry.jsonl` | Structured event log for the session — see [`docs/goal-mode-telemetry.md`](docs/goal-mode-telemetry.md) |
 
+**Temp-file hygiene:** every run gets its own `/tmp/iad.<run-id>.<pid>` dir, exported as `TMPDIR`, so pytest/playwright/service-log temp files are isolated per run and removed on exit (goal mode clears the previous iteration's dir at each iteration boundary). A startup janitor sweeps strays from crashed runs, including stale `/tmp/pytest-of-$USER` entries. Knobs: `CHAIN_TMPDIR_DISABLE=true` (leave the environment alone), `CHAIN_TMP_JANITOR=false` (skip the sweep), `CHAIN_TMP_MAX_AGE_HOURS=24` (janitor age gate). See `.claude/anti-patterns.md` #21.
+
 ## Subrepo Usage
 
 This framework is designed to be added to project repos as a submodule or subtree. Framework files live under `.claude/`, `scripts/`, `config/`, and `templates/` -- directories that do not conflict with typical project layouts. Project-specific docs go in `docs/`.
diff --git a/incredible_auto_dev/adapters/claude/sync.py b/incredible_auto_dev/adapters/claude/sync.py
index 5cbaf91..16b16bf 100644
--- a/incredible_auto_dev/adapters/claude/sync.py
+++ b/incredible_auto_dev/adapters/claude/sync.py
@@ -270,6 +270,12 @@ def render_settings_json() -> str:
         "allow": list(perms.get("allow", [])),
         "deny": list(perms.get("deny", [])),
     }
+    # Additional working directories (policy `additionalDirectories`). Claude
+    # Code's built-in rm containment only permits deletion inside the session's
+    # working directories — /tmp must be granted here or agents can create
+    # temp files (pytest, playwright, logs) they can never remove.
+    if perms.get("additionalDirectories"):
+        settings["permissions"]["additionalDirectories"] = list(perms["additionalDirectories"])
     settings["hooks"] = _hooks_block_for_claude()
     # ensure_ascii=False keeps em-dashes and other unicode readable
     return json.dumps(settings, indent=2, ensure_ascii=False) + "\n"
diff --git a/incredible_auto_dev/agents/retro-analyst/agent.yaml b/incredible_auto_dev/agents/retro-analyst/agent.yaml
new file mode 100644
index 0000000..3aa43e0
--- /dev/null
+++ b/incredible_auto_dev/agents/retro-analyst/agent.yaml
@@ -0,0 +1,11 @@
+name: retro-analyst
+description: Post-session retrospective analyst. Reads ONLY the frozen retro-input.md evidence
+  digest at terminal halts and drafts 1-5 candidate framework-improvement items for human triage.
+  Proposals only — never edits the roadmap. Non-blocking showcase-class step.
+model_tier: light
+tools_allowed:
+- Read
+- Write
+version: 1.0.0
+last_updated: '2026-07-10'
+body: body.md
diff --git a/incredible_auto_dev/agents/retro-analyst/body.md b/incredible_auto_dev/agents/retro-analyst/body.md
new file mode 100644
index 0000000..deb5a3d
--- /dev/null
+++ b/incredible_auto_dev/agents/retro-analyst/body.md
@@ -0,0 +1,66 @@
+
+# Retro Analyst
+
+You turn one finished goal-mode session's frozen evidence digest into 1-5 CANDIDATE framework-improvement items for a human to triage. You are the drafting step of the EVO-2 feedback loop: a deterministic collector already froze everything you may use into a single file; you propose, a human decides. You never schedule work, never edit the roadmap, and never gate the pipeline — a weak or empty report must cost the session nothing.
+
+## Input — exactly ONE file
+
+Read ONLY the retro-input.md path given in your dispatch prompt (`runs/goal-session-<sid>/state/retro-input.md`). That file is the complete evidence boundary for this task.
+
+- Do NOT read telemetry.jsonl, journey-history.json, lessons.md, evaluator-log.md, iteration artifacts, docs/improvement-roadmap.md, or any other file. The digest exists precisely so you read one small file instead of session history (token policy).
+- The digest's stable sections are: `## Outcome`, `## Verdict sequence`, `## Agent economics`, `## Friction counters`, `## Lessons tail`, `## Halt context`.
+- Counters marked `unknown (<why>)` are gaps, not zeros. Never treat an `unknown` as a number; you MAY cite the `unknown (<why>)` line itself as evidence of an instrumentation gap worth fixing.
+
+## What counts as a signal
+
+Draft an item only when the digest shows recurring or structural FRAMEWORK pain — something a change to the pipeline, agents, scripts, or instrumentation could reduce for every future session:
+
+- A friction counter greater than zero (quota pauses, attempt-1 review FAILs, malformed-verdict rewrites).
+- A verdict-sequence pattern (a long CONTINUE run ending STALLED, repeated ESCALATE/REGRESSION churn).
+- An economics outlier (one agent dominating wall time or cost).
+- A lessons-tail entry describing pipeline/tooling pain (flaky dispatch, retry loops, missing evidence).
+- An `unknown (<why>)` counter — propose fixing the missing source, not the number.
+
+Product-specific pain (a fragile module in the app being built, a failing journey) is NOT a framework item — the goal loop itself handles those. If a lessons entry is about the product, skip it.
+
+## Candidate item shape
+
+Number items RETRO-1 … RETRO-5, at most 5, each ≤20 lines, in this exact shape (the roadmap's §4 item fields, proposal-weight):
+
+```
+### RETRO-<n> · <short title>
+- **Proposed:** P0|P1|P2 · Effort S|M|L · Risk LOW|MED|HIGH
+- **Problem:** <1-2 sentences — the recurring pain and who hits it>
+- **Evidence:** <digest section name> — "<exact line(s) quoted from retro-input.md>"
+- **Sketch:** <2-6 lines — a plausible direction, not a full spec>
+- **Verify idea:** <one line — how an implementer would prove it worked>
+```
+
+Hard rule: no Evidence line → no item. Every Evidence entry names the digest section and quotes the line(s) verbatim, e.g. `Evidence: Friction counters — "Quota pauses: 3"`. Zero items is a valid output: when nothing recurred, the Candidate items body is exactly `nothing recurred worth proposing` plus one sentence saying why (e.g. all counters zero, lessons product-only).
+
+## Output
+
+Write exactly ONE file — the output path from your dispatch prompt (`reports/goal-session-<sid>-retro.md`), overwriting any existing file:
+
+```
+# Session retro — <sid>
+
+> **PROPOSALS ONLY** — a human promotes candidates into docs/improvement-roadmap.md §16
+> per EVO-1; nothing here is scheduled work.
+
+**Session:** <sid> · **Terminal status:** <from Outcome> · **Iterations:** <from Outcome>
+
+## Candidate items
+
+<RETRO-n blocks, or the zero-item line>
+```
+
+- Whole report ≤120 lines.
+- NEVER edit docs/improvement-roadmap.md or any file other than the output path.
+- No tool use beyond Read and Write. No Bash, no agents, no URLs.
+- Write the report and STOP. Do not print the report to chat.
+
+## Token and Questioning Policy
+
+Apply `.claude/core.md` strictly. Agent-specific guidance:
+- Do NOT ask the user clarifying questions. If the digest is degraded (sections missing, counters unknown), work with what is present — degraded input usually means fewer or zero items, and that is a correct outcome.
diff --git a/incredible_auto_dev/benchmarks/experiments.md b/incredible_auto_dev/benchmarks/experiments.md
new file mode 100644
index 0000000..52f646c
--- /dev/null
+++ b/incredible_auto_dev/benchmarks/experiments.md
@@ -0,0 +1,52 @@
+# Benchmark experiments ledger (EVO-3)
+
+**APPEND-ONLY.** Entries below the marker line are never edited or deleted once
+written. A bad entry is corrected by APPENDING a dated correction line under
+it — never by rewriting history. Pre-registration only proves anything
+(ground rule G8: prediction precedes execution) if the record is immutable.
+
+How entries get here (written by `scripts/automation/run-benchmark.sh`):
+
+- **PRE** — appended after the runner's refusal gates pass and BEFORE the
+  engine launches: date · framework sha (+dirty flag) · fixture · one-line
+  hypothesis · the metric(s) and predicted direction/size (taken from the
+  `--predict` predicates when given, otherwise stated inside the hypothesis
+  itself and graded manually later).
+- **POST** — appended after results extraction, under the same session id:
+  results file path · headline numbers · per-predicate evaluations · a
+  `verdict-vs-prediction:` line. With `--predict` predicates the verdict is
+  computed mechanically (all true → CONFIRMED, all false → REFUTED, else
+  MIXED). Without predicates the line reads
+  `MANUAL — append CONFIRMED|REFUTED|MIXED after review`: the runner never
+  self-grades a free-text hypothesis — read the results JSON, then append your
+  verdict as a new dated line under the POST entry.
+
+Entry format contract (grep-able; pinned by
+`tests/automation/test-benchmark-runner.sh`): PRE entries start
+`## PRE <session-id>`, POST entries start `## POST <session-id>`.
+
+<!-- entries are appended below this line — do not edit anything beneath it -->
+
+---
+
+## PRE bench-20260710-2110 · 2026-07-10T21:10:26Z
+- framework-sha: b172cea005aa8225299b1f7160ae87a946a06a20 (dirty: false)
+- fixture: todo-app · max-iter 2
+- hypothesis: Baseline @ b172cea005aa: chain reaches GOAL_ACHIEVED with 3/3 journeys within --max-iter 2 on the todo-app fixture
+- metrics + prediction (mechanical --predict): final_status==GOAL_ACHIEVED;journeys_passing_after>=3
+
+## POST bench-20260710-2110 · 2026-07-10T21:10:28Z
+- results: benchmarks/results/20260710-211028-b172cea005aa.json
+- headline: status=ABORTED last_verdict=unknown (last_verdict null/absent in session.json) journeys=0/0 iters=0 engine_exit=2 wall=2s cost=unknown
+- predicate: final_status==GOAL_ACHIEVED → false (final_status='ABORTED')
+- predicate: journeys_passing_after>=3 → false (journeys_passing_after=0)
+- verdict-vs-prediction: REFUTED
+- correction 2026-07-10: INFRA FAILURE, not a chain result — the slice-(b) runner
+  exported the invalid `CHAIN_AGENT_BACKEND=headless` (quota-retry.sh accepts
+  interactive|claude|codex; headless dispatch = `claude`), so the engine aborted at
+  the first dispatch after 2s with ZERO agent spend (economics empty; the bad value
+  is visible in the results JSON's chain_env). Runner + test fixed to export
+  `claude` in the same commit that carries this line. The offline suite could not
+  catch this: its stub engines echo the env var without validating it against the
+  real quota-retry contract. Any rerun is a fresh PRE/POST pair under fresh user
+  approval (G9) — this entry stays as the record of the aborted attempt.
diff --git a/incredible_auto_dev/benchmarks/fixtures/todo-app/.claude/project-template.md b/incredible_auto_dev/benchmarks/fixtures/todo-app/.claude/project-template.md
new file mode 100644
index 0000000..b62d420
--- /dev/null
+++ b/incredible_auto_dev/benchmarks/fixtures/todo-app/.claude/project-template.md
@@ -0,0 +1,176 @@
+# Project Configuration — todo-app (EVO-3 benchmark fixture)
+
+Filled for THIS app. Agents read this file to understand the stack, commands,
+and constraints. The scaffold is deliberately bare — see docs/goal.md for what
+to build.
+
+---
+
+## PROJECT GOAL
+
+```
+Goal document: docs/goal.md
+```
+
+---
+
+## PROJECT
+
+```
+Name:        todo-app
+Description: Single-page personal todo list backed by one local JSON file
+Repository:  none — the benchmark runner copies this tree to a scratch dir and runs `git init` there
+```
+
+---
+
+## STACK
+
+```
+Backend:
+  Language:   Python 3.14
+  Framework:  Flask 3
+  ORM/DB lib: none — plain JSON file read/written via helpers in app.py
+  Migrations: N/A
+  Test runner: pytest
+  Package mgr: pip (inside .venv/)
+  Venv/env:   .venv/ at the project root — create with:
+              python3 -m venv .venv && .venv/bin/pip install flask pytest
+
+Frontend:
+  Enabled:    yes
+  Framework:  none — server-rendered template + vanilla JS (static/app.js)
+  Language:   JavaScript (vanilla), HTML via Flask/Jinja template
+  Styling:    plain CSS (none yet — add inline or a small static/style.css)
+  Package mgr: none — no node, no build step
+
+Database:
+  Type:       JSON file
+  Location:   todos.json beside app.py — created at runtime, never committed
+
+Services:
+  Backend URL:  http://127.0.0.1:5177
+  Frontend URL: N/A — same Flask server serves the page and static assets
+  Health check: http://127.0.0.1:5177/health
+```
+
+---
+
+## DESIGN SYSTEM
+
+```
+Component library: none — hand-written HTML/CSS only
+Icon library:      none — text labels suffice
+
+Visual style:      minimal-light, single column
+Color mode:        light
+
+Color palette:
+  Background:      #ffffff
+  Surface:         #f6f6f6 — list rows / panels
+  Border:          #dddddd
+  Primary:         #2563eb — buttons and active filter
+  Success:         #16a34a — done state accents
+  Danger:          #dc2626
+  Text primary:    #1f2937
+  Text muted:      #6b7280
+
+Typography:
+  Font family:     system-ui stack; no webfonts
+  Scale:           browser defaults; headings one step up
+
+Spacing:           multiples of 8px; the page stays one centered column
+
+Effects (use sparingly):
+  - done items: strikethrough + muted text
+  - no animations required
+```
+
+---
+
+## TEST COMMANDS
+
+```
+Backend tests:  .venv/bin/python -m pytest -q
+Frontend tests: N/A
+Migrations:     N/A
+Lint:           N/A
+```
+
+---
+
+## SERVICE START COMMANDS
+
+```
+Start backend:  .venv/bin/python app.py    # serves http://127.0.0.1:5177
+Start frontend: N/A — the backend serves the page
+```
+
+---
+
+## PHASE SPECS
+
+```
+Phase spec directory:   docs/phases/
+Phase spec naming:      goal mode writes goal-<sid>-iter-<N>.md here
+```
+
+---
+
+## ROADMAP
+
+Goal mode drives this project from docs/goal.md; there is no phase roadmap.
+
+| Phase | Name | Status |
+|-------|------|--------|
+| — | (iterations decomposed from docs/goal.md) | — |
+
+---
+
+## ARCHITECTURE PRINCIPLES
+
+```
+- Single-file Flask app: all routes and store helpers live in app.py; no blueprints
+  or packages unless a journey forces it.
+- todos.json is the ONLY state, and all reads/writes go through the store helper(s)
+  in app.py — never open the file elsewhere.
+- No build step: static/app.js is plain vanilla JS served as-is.
+- No new runtime dependencies beyond Flask (pytest is test-only).
+- The port is fixed at 5177 — do not change it.
+```
+
+---
+
+## DATA MODEL RULES
+
+```
+- todos.json holds a JSON array of todo objects.
+- Each todo carries a stable id, its text, and a done boolean.
+- If timestamps are ever added, they are UTC ISO 8601 strings.
+```
+
+---
+
+## GIT WORKFLOW
+
+```
+Branch naming:      main only — the benchmark scratch repo commits directly to main
+PR title format:    N/A — no remote, no PRs in benchmark runs
+Main branch:        main
+Never commit:
+  - todos.json      (runtime store)
+  - .venv/
+  - __pycache__/
+  - .pytest_cache/
+```
+
+---
+
+## NOTES FOR AGENTS
+
+```
+- This project is the framework's EVO-3 benchmark fixture: the journeys in
+  docs/goal.md are deliberately unimplemented in the scaffold; building them
+  IS the task.
+- Keep changes lean — the benchmark budget is 2 lean iterations.
+```
diff --git a/incredible_auto_dev/benchmarks/fixtures/todo-app/.gitignore b/incredible_auto_dev/benchmarks/fixtures/todo-app/.gitignore
new file mode 100644
index 0000000..e57d7fc
--- /dev/null
+++ b/incredible_auto_dev/benchmarks/fixtures/todo-app/.gitignore
@@ -0,0 +1,5 @@
+# Runtime artifacts — never committed (see docs/goal.md anti-goals)
+todos.json
+__pycache__/
+.venv/
+.pytest_cache/
diff --git a/incredible_auto_dev/benchmarks/fixtures/todo-app/README.md b/incredible_auto_dev/benchmarks/fixtures/todo-app/README.md
new file mode 100644
index 0000000..39227d7
--- /dev/null
+++ b/incredible_auto_dev/benchmarks/fixtures/todo-app/README.md
@@ -0,0 +1,47 @@
+# todo-app — EVO-3 benchmark fixture (bare scaffold)
+
+This directory is the **fixture project** for the framework's automated benchmark
+harness (`docs/improvement-roadmap.md` EVO-3). It is a runnable but deliberately
+BARE Flask scaffold: the Must-have journeys in `docs/goal.md` (add a todo, toggle
+done with persistence, filter open/done) are **intentionally unimplemented**. The
+benchmark measures the goal-mode chain BUILDING those journeys, not verifying
+pre-built ones — feature code checked in here would corrupt the measurement.
+
+What ships: `app.py` (shell page, `/health`, and the runtime-created `todos.json`
+store primitive), a minimal `templates/index.html` + `static/app.js` shell,
+scaffold tests (`test_app.py` — green on the bare tree), a filled
+`.claude/project-template.md`, and a goal_lint-clean `docs/goal.md`.
+
+## How the benchmark consumes it (slice (b), not yet built)
+
+`scripts/automation/run-benchmark.sh` will: copy this directory to a scratch dir →
+`git init` there → run `run-goal.sh --session-id bench-<date> --max-iter 2`
+headless → extract metrics into `benchmarks/results/`. Never run the engine
+against this directory in place, and never `git init` here — the scratch copy is
+the run target. Every benchmark run spends real API tokens (G9: confirm with the
+user first).
+
+## Hand-verify the scaffold
+
+```bash
+cd benchmarks/fixtures/todo-app
+python3 -m venv .venv && .venv/bin/pip install flask pytest    # once
+.venv/bin/python -m pytest -q                                  # 3 tests green
+.venv/bin/python app.py &                                      # serves 127.0.0.1:5177
+curl -s http://127.0.0.1:5177/health                           # {"status":"ok"}
+curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:5177/  # 200
+kill %1
+python3 ../../../scripts/automation/lib/goal_lint.py docs/goal.md  # exit 0, silent
+```
+
+`todos.json` (runtime store), `.venv/`, `__pycache__/`, and `.pytest_cache/` are
+gitignored; delete them freely.
+
+## Nesting note
+
+The `.claude/project-template.md` and `docs/goal.md` in this tree are FIXTURE
+CONTENT for the app-under-benchmark (same precedent as `tests/judgment/*/tree/`).
+Framework tooling — `sync-cli-assets.py`, the eval suite — must never treat them
+as this repo's own configuration. The fixture is authored independently of the
+judgment fixtures: same proven stack shape, zero shared files, so the two eval
+assets can never drift into coupling.
diff --git a/incredible_auto_dev/benchmarks/fixtures/todo-app/app.py b/incredible_auto_dev/benchmarks/fixtures/todo-app/app.py
new file mode 100644
index 0000000..a0c2a56
--- /dev/null
+++ b/incredible_auto_dev/benchmarks/fixtures/todo-app/app.py
@@ -0,0 +1,42 @@
+"""Todo — EVO-3 benchmark fixture, BARE scaffold.
+
+Deliberately implements NO journey from docs/goal.md (no add, no toggle, no
+filter): the benchmark measures the goal-mode chain BUILDING those features.
+This file provides only the shell page, the health endpoint, and the
+JSON-file store primitive the features will grow on; mutations are the
+chain's work.
+
+Run: .venv/bin/python app.py  ->  http://127.0.0.1:5177/
+"""
+import json
+from pathlib import Path
+
+from flask import Flask, jsonify, render_template
+
+BASE_DIR = Path(__file__).resolve().parent
+
+app = Flask(__name__)
+app.config.setdefault("DATA_FILE", str(BASE_DIR / "todos.json"))
+
+
+def load_todos():
+    """Return the todo list, creating the JSON store on first use."""
+    store = Path(app.config["DATA_FILE"])
+    if not store.exists():
+        store.write_text("[]", encoding="utf-8")
+    return json.loads(store.read_text(encoding="utf-8"))
+
+
+@app.route("/")
+def index():
+    load_todos()  # materialize the store at runtime; nothing rendered from it yet
+    return render_template("index.html")
+
+
+@app.route("/health")
+def health():
+    return jsonify(status="ok")
+
+
+if __name__ == "__main__":
+    app.run(host="127.0.0.1", port=5177)
diff --git a/incredible_auto_dev/benchmarks/fixtures/todo-app/docs/goal.md b/incredible_auto_dev/benchmarks/fixtures/todo-app/docs/goal.md
new file mode 100644
index 0000000..a899a33
--- /dev/null
+++ b/incredible_auto_dev/benchmarks/fixtures/todo-app/docs/goal.md
@@ -0,0 +1,68 @@
+# Project Goal
+
+## Vision
+A single-page personal todo list: add tasks, mark them done, and filter the list —
+one small Flask app that keeps everything in one local JSON file.
+
+## Target Users
+One person tracking their own tasks in a browser on their own machine.
+
+## Success Criteria
+- All Must-have journeys below pass in a real browser.
+- Todos survive a server restart (the JSON store is the only state).
+
+## Key Capabilities
+1. Add a todo from the page.
+2. Toggle a todo between open and done, persisted across reloads.
+3. Filter the list to open or done todos.
+
+## Non-Goals
+- Multi-user support, sharing, or sync.
+- Any storage other than the single local JSON file.
+
+## Constraints
+- Stack is fixed: Flask + vanilla JS + pytest; no new runtime dependencies beyond Flask.
+- Server binds 127.0.0.1:5177; storage is todos.json beside app.py, created at runtime.
+
+## Design Direction
+- Visual style: minimal-clean, single column, readable at a glance.
+- Mood: calm, utilitarian.
+- Reference: a plain paper checklist.
+
+## Product Shape
+
+### Navigation / information architecture
+- One page at / — header, add form, todo list, filter controls. The only other route is /health.
+
+### Canonical values (single source of truth)
+- The todo collection: read and written ONLY through the JSON-store helper(s) in app.py;
+  every view of the list (full, open, done) derives from that one store.
+
+## Must-have user journeys
+
+- **J-01: Add a todo via the form**
+  - Steps:
+    1. Visit http://127.0.0.1:5177/
+    2. Type "buy milk" into the new-todo input.
+    3. Submit the add form.
+  - Acceptance: "buy milk" appears as an item in the todo list, and it is still listed after a page reload.
+
+- **J-02: Toggle a todo done**
+  - Steps:
+    1. With "buy milk" listed, click its done control.
+    2. Observe the item's visual state change.
+    3. Reload the page.
+  - Acceptance: the item shows a visibly distinct done treatment (strikethrough or checked marker) both before and after the reload.
+
+- **J-03: Filter open vs done**
+  - Steps:
+    1. Add a second todo "walk dog", then mark "walk dog" done.
+    2. Click the "Open" filter control.
+    3. Click the "Done" filter control.
+  - Acceptance: the Open view shows "buy milk" but not "walk dog"; the Done view shows "walk dog" but not "buy milk".
+
+## Anti-goals
+
+- No user accounts, sessions, or auth of any kind — the app must never ask for credentials.
+- No external network calls, third-party services, or paid APIs at runtime — storage is
+  the local todos.json file only, and every page asset is served from 127.0.0.1:5177.
diff --git a/incredible_auto_dev/benchmarks/fixtures/todo-app/static/app.js b/incredible_auto_dev/benchmarks/fixtures/todo-app/static/app.js
new file mode 100644
index 0000000..8f8737a
--- /dev/null
+++ b/incredible_auto_dev/benchmarks/fixtures/todo-app/static/app.js
@@ -0,0 +1,5 @@
+// Bare scaffold — no behavior yet. The goal-mode chain grows this file as it
+// implements the docs/goal.md journeys (add-form wiring, done toggle, filters).
+document.addEventListener("DOMContentLoaded", () => {
+  // intentionally empty
+});
diff --git a/incredible_auto_dev/benchmarks/fixtures/todo-app/templates/index.html b/incredible_auto_dev/benchmarks/fixtures/todo-app/templates/index.html
new file mode 100644
index 0000000..887c28f
--- /dev/null
+++ b/incredible_auto_dev/benchmarks/fixtures/todo-app/templates/index.html
@@ -0,0 +1,18 @@
+<!doctype html>
+<html lang="en">
+<head>
+  <meta charset="utf-8">
+  <meta name="viewport" content="width=device-width, initial-scale=1">
+  <title>Todo</title>
+</head>
+<body>
+  <header>
+    <h1>Todo</h1>
+  </header>
+  <main id="app">
+    <!-- Bare scaffold: the goal-mode chain builds the add form, the todo
+         list, and the filter controls here (docs/goal.md J-01..J-03). -->
+  </main>
+  <script src="/static/app.js"></script>
+</body>
+</html>
diff --git a/incredible_auto_dev/benchmarks/fixtures/todo-app/test_app.py b/incredible_auto_dev/benchmarks/fixtures/todo-app/test_app.py
new file mode 100644
index 0000000..a77cac5
--- /dev/null
+++ b/incredible_auto_dev/benchmarks/fixtures/todo-app/test_app.py
@@ -0,0 +1,35 @@
+"""Scaffold tests — green on the BARE fixture (no journey features yet).
+
+These three tests pin the scaffold contract the goal-mode chain starts from:
+the app imports, the shell page serves, the health endpoint answers, and the
+JSON store materializes at runtime. The chain grows this file as it
+implements the journeys in docs/goal.md.
+"""
+import pytest
+
+import app as todo_app
+
+
+@pytest.fixture()
+def client(tmp_path):
+    todo_app.app.config["DATA_FILE"] = str(tmp_path / "todos.json")
+    todo_app.app.config["TESTING"] = True
+    with todo_app.app.test_client() as c:
+        yield c
+
+
+def test_app_imports():
+    assert todo_app.app.name == "app"
+
+
+def test_index_serves_shell_and_creates_store(client, tmp_path):
+    resp = client.get("/")
+    assert resp.status_code == 200
+    assert b"Todo" in resp.data
+    assert (tmp_path / "todos.json").exists()
+
+
+def test_health(client):
+    resp = client.get("/health")
+    assert resp.status_code == 200
+    assert resp.get_json() == {"status": "ok"}
diff --git a/incredible_auto_dev/benchmarks/results/20260710-211028-b172cea005aa.json b/incredible_auto_dev/benchmarks/results/20260710-211028-b172cea005aa.json
new file mode 100644
index 0000000..604cf16
--- /dev/null
+++ b/incredible_auto_dev/benchmarks/results/20260710-211028-b172cea005aa.json
@@ -0,0 +1,35 @@
+{
+  "meta": {
+    "date_utc": "2026-07-10T21:10:26Z",
+    "framework_sha": "b172cea005aa8225299b1f7160ae87a946a06a20",
+    "framework_dirty": false,
+    "fixture": "todo-app",
+    "session_id": "bench-20260710-2110",
+    "max_iter": 2,
+    "hypothesis": "Baseline @ b172cea005aa: chain reaches GOAL_ACHIEVED with 3/3 journeys within --max-iter 2 on the todo-app fixture",
+    "predict": [
+      "final_status==GOAL_ACHIEVED",
+      "journeys_passing_after>=3"
+    ],
+    "chain_env": {
+      "CHAIN_AGENT_BACKEND": "headless",
+      "CHAIN_BENCH_MAX_ITER": "2",
+      "CHAIN_BENCH_SESSION_ID": "bench-20260710-2110"
+    },
+    "model_tiers_sha256": "1d096808ad8eb0b5fcc863b8c71403dced292d24c4e8021d940abda52e298896"
+  },
+  "outcome": {
+    "engine_exit_code": 2,
+    "final_status": "ABORTED",
+    "last_verdict": "unknown (last_verdict null/absent in session.json)",
+    "iterations_used": 0,
+    "journeys_passing_after": 0,
+    "journeys_total": 0,
+    "attempt1_review_fails": 0,
+    "malformed_verdicts": 0,
+    "wall_seconds": 2
+  },
+  "economics": {
+    "agents": {}
+  }
+}
diff --git a/incredible_auto_dev/docs/improvement-roadmap.md b/incredible_auto_dev/docs/improvement-roadmap.md
index ea91623..7855701 100644
--- a/incredible_auto_dev/docs/improvement-roadmap.md
+++ b/incredible_auto_dev/docs/improvement-roadmap.md
@@ -189,15 +189,66 @@ the system measures itself, and how it survives the next model change.
   tell the user it may be stale.
 
 ### EVO-2 · Automatic post-session retrospective
-- **Priority:** P0 · **Effort:** L (2 slices) · **Risk:** MED · **Status:** TODO
+- **Priority:** P0 · **Effort:** L (2 slices) · **Risk:** MED · **Status:** DONE
+  *(slice (a) — deterministic collector + terminal-halt wiring — implemented 2026-07-10:
+  `scripts/automation/lib/retro_collect.sh` (new) writes `state/retro-input.md` with the
+  stable sections Outcome / Verdict sequence / Agent economics / Friction counters /
+  Lessons tail / Halt context; sourceless counters are the literal `unknown (<why>)`.
+  Wired into `write_session_summary` (`run-goal.sh:1263-1273` after slice (b)'s edits)
+  behind `CHAIN_SESSION_RETRO` (default `true`; documented in
+  `.claude/model-orchestration.md` knob table), firing on
+  GOAL_ACHIEVED/STALLED/REGRESSION_HALT/BUDGET_EXHAUSTED only, non-blocking.
+  Slice (a) certified 2026-07-10 by a non-implementer session per G8: 23/23 asserts +
+  full evals green, wiring claims re-verified against code, digest judged sufficient
+  as the drafting agent's sole input — no collector amendments needed.
+  Slice (b) — drafting agent — implemented 2026-07-10 by that certifying session: new
+  `agents/retro-analyst/` (model_tier light, tools [Read, Write]) reads ONLY the digest
+  and writes `reports/goal-session-<sid>-retro.md` — ≤5 candidate items in this file's
+  §4 shape, each citing its exact digest line, PROPOSALS-ONLY banner, zero items a
+  valid output, report ≤120 lines. Dispatched by `_run_retro_analyst`
+  (`run-goal.sh:329`, the summarizer wrapper pattern) from inside write_session_summary
+  immediately after the collector — same knob + same terminal filter + digest-exists
+  guard, non-blocking (a failed dispatch prints one warning, changes no exit code).
+  No `templates/retro.md` was needed — body.md carries the report skeleton (the Files
+  line below listed it as an either/or with the agent). Tests:
+  `tests/automation/test-goal-retro.sh` now 32 asserts (the stub plays the drafting
+  model: both-files DoD on STALLED, neither file on AWAITING_PUMP/knob-off, broken
+  collector → no orphan dispatch, failed dispatch → exit codes unchanged + one
+  warning), still registered in `run-evals.sh` §2c.
+  ABORT_MALFORMED call-site audit (slice (b) optional step): NOT changed. Every
+  session.json status consumer falls through safely on an unknown status EXCEPT
+  `run-goal.sh:1176` (`AWAITING_PUMP|ABORTED) _join_showcase_tail --kill`), which
+  special-cases "ABORTED" — passing ABORT_MALFORMED would flip that halt from
+  reap-immediately to bounded-join, so per the audit gate the call site
+  (`run-goal.sh:2245-2251`) still passes "ABORTED" and malformed-x2 halts still get NO
+  retro. A future slice shipping the rename must extend that case list plus the three
+  status-enum docs (`.claude/workflow.md:305`, `skills/goal-interactive-dispatch.md:147`,
+  `docs/goal-mode-telemetry.md:37/:115` — the last already omits ABORT_MALFORMED as an
+  emitted halt reason today, pre-existing drift, not introduced here).
+  Slice (b) certified DONE 2026-07-10 by a fresh non-implementer session per G8:
+  32/32 retro asserts + 93/93 evals green; agent contract (light tier, tools exactly
+  [Read, Write], digest-only input, ≤5 §4-shape items with verbatim evidence quotes,
+  PROPOSALS-ONLY banner, zero-items valid, ≤120 lines, never edits the roadmap),
+  wiring guards, the `run-goal.sh:1176` ABORTED special-case, and all three catalog
+  surfaces (CLAUDE.md list, agents.md count 20, README row) re-verified against code;
+  `sync-cli-assets --check` clean; plus one user-approved (G9) real light-tier smoke
+  dispatch (claude-haiku-4-5) against a collector-built synthetic digest — well-formed
+  4-item report, verbatim evidence quotes, product-only lesson correctly skipped, no
+  stray writes. EVO-2 complete; body archiving left to a future tidy pass (REL-1
+  precedent).)*
 - **Problem:** every session generates evidence about what hurt (halts, quota pauses,
   review-FAIL loops, wall-time spikes, lessons) — and none of it flows back into
   framework improvements. The feedback loop is the evolution engine's core.
 - **Current state:** terminal halts are decided in the verdict/halt switch
-  (`run-goal.sh:1777-1919`); the showcase tail is the proven non-blocking pattern
-  (forked for CONTINUE, inline for halts, `run-goal.sh:1601-1612` / `:1770-1775`);
-  wall/token aggregation exists (`lib/analyze_telemetry.py`, `build_wall_report` ~`:273`,
-  JSON output supported); lessons tail inlining exists (`:520-525`).
+  (`run-goal.sh:2066-2210`), but EVERY halt — terminal and resumable — funnels through
+  `write_session_summary()` (`run-goal.sh:1123`), the single choke point slice (a) wired
+  (AWAITING_* pauses and the GOAL_ACHIEVED+proposer-extended `continue` never reach a
+  terminal summary); the showcase tail is the proven non-blocking pattern (forked for
+  CONTINUE `run-goal.sh:2063`, inline for halts `:1900`); wall/token aggregation exists
+  (`lib/analyze_telemetry.py`, `build_wall_report` `:273`, `--json` output supported);
+  lessons tail inlining exists (`run-goal.sh:1469`); verdict-per-iteration telemetry:
+  `iter_end` `:1945`, `deterministic_gate` rewrites `:1883`, `review_verdict`
+  (`goal-iter-lean.sh:210`).
 - **Change spec:**
   1. **Slice (a) — deterministic collector + wiring.** New
      `scripts/automation/lib/retro_collect.sh` (or `.py`): writes
@@ -210,7 +261,7 @@ the system measures itself, and how it survives the next model change.
      `CHAIN_SESSION_RETRO` (default `true`, escape hatch documented). Sandbox test
      asserting it runs on STALLED and not on AWAITING_PUMP.
   2. **Slice (b) — drafting agent.** Light-tier dispatch (reuse the
-     `_run_iteration_summarizer` wrapper pattern, `run-goal.sh:244-277`) reading ONLY
+     `_run_iteration_summarizer` wrapper pattern, `run-goal.sh:251`) reading ONLY
      `retro-input.md`, writing `reports/goal-session-<sid>-retro.md`: 1-5 candidate
      framework-improvement items in this file's §4 item format, each citing its
      evidence line from retro-input. PROPOSALS ONLY — the agent never edits this
@@ -230,7 +281,87 @@ the system measures itself, and how it survives the next model change.
   catalog count in CLAUDE.md ("19 agents"), flag it — CLAUDE.md is ask-first class.
 
 ### EVO-3 · Automated benchmark harness
-- **Priority:** P0 · **Effort:** L (3 slices) · **Risk:** MED · **Status:** TODO
+- **Priority:** P0 · **Effort:** L (3 slices) · **Risk:** MED · **Status:** IN-PROGRESS
+  *(slice (a) — fixture project — implemented 2026-07-10:
+  `benchmarks/fixtures/todo-app/` is a runnable but deliberately BARE Flask +
+  vanilla-JS + pytest scaffold — shell page + `/health` on fixed port 5177, storage
+  = one runtime-created `todos.json`, journeys deliberately UNIMPLEMENTED (the
+  benchmark measures the chain BUILDING them, not verifying pre-built ones).
+  `docs/goal.md` carries J-01 add / J-02 toggle+persist / J-03 filter with numbered
+  steps + browser-observable Acceptance lines and 2 checkable anti-goals —
+  goal_lint exit 0 (clean, not just <2) and validate_goal_file-compatible. Nested
+  `.claude/project-template.md` truthfully filled for THIS app (fixture content,
+  never a sync-cli-assets target — judgment-fixture nesting precedent); scaffold
+  tests green (3/3: import, GET / 200 + runtime store creation, /health 200) via a
+  gitignored `.venv/` (system python 3.14 ships no flask/pytest); README documents
+  the slice-(b) consumption contract (copy → scratch dir → git init →
+  `run-goal.sh --session-id bench-<date> --max-iter 2`) and hand-verification.
+  Authored independently of tests/judgment/** — zero shared files, so the two eval
+  assets cannot drift into coupling. No runner, no `benchmarks/results/`, no
+  engine runs (every benchmark run is G9 ask-first spend). Slices (b) runner +
+  (c) compare/baseline remain; slice (a) certification per G8 folds into the
+  slice-(b) session.)*
+  *(slice (b) — runner + pre-registration ledger — implemented 2026-07-10, same
+  session as the G8 fresh-eyes certification of slice (a) (certified: fixture
+  tests 3/3 green, app boots on 5177 with `/` and `/health` → 200, goal_lint
+  exit 0, journeys confirmed browser-observable and genuinely unimplemented in
+  the scaffold — no todo logic in `app.py`/`app.js` — and `run-evals.sh` green;
+  certifier was not slice (a)'s implementer. One recorded nit, no edit: the
+  fixture project-template's "commits directly to main" line vs the engine's
+  default `goal/<sid>` push branch — fixture prose, no behavioral effect).
+  `scripts/automation/run-benchmark.sh`: always prints plan + cost estimate,
+  then REFUSES without `--yes-spend` (G9), without `--hypothesis` (G8), and on
+  a dirty framework tree unless `--allow-dirty` (recorded as
+  `framework_dirty:true` + diffstat) — every refusal BEFORE any side effect.
+  Run sequence: PRE entry appended to `benchmarks/experiments.md` (append-only
+  ledger, created this slice) BEFORE the engine launches → scratch repo =
+  subrepo set (`.claude/ scripts/ config/ templates/ CLAUDE.md` [+`.mcp.json`])
+  + fixture overlay (fixture files win collisions, so its project-template
+  replaces the framework placeholder; `.venv`/`__pycache__`/`.pytest_cache`/
+  `todos.json` excluded) + fresh git repo (main, deterministic goal-chain
+  author) with a LOCAL BARE origin, so the engine's ls-remote preflight and
+  push-per-iter exercise their real code paths with zero network → engine
+  `run-goal.sh --session-id bench-<UTCdate-hhmm> --max-iter 2` headless
+  (nonzero/paused engine = recorded RESULT, not a runner crash) → results JSON
+  `benchmarks/results/<UTCts>-<sha12>.json` (meta: every CHAIN_* env var at
+  launch + model-tiers sha256; outcome: journeys passing/total from
+  journey-history, attempt-1 review FAILs + malformed verdicts counted with
+  `retro_collect.sh`'s exact telemetry semantics, wall seconds; economics:
+  `analyze_telemetry.py --json` embedded verbatim; missing sources = literal
+  `unknown (<why>)`), validated for required keys before success → POST entry
+  with headline + per-predicate evaluations. `--predict` comparisons over
+  top-level result keys make verdict-vs-prediction mechanical (all true
+  CONFIRMED / all false REFUTED / else MIXED); without predicates the POST line
+  is the literal MANUAL instruction — the runner never self-grades free text.
+  Engine command injectable via `CHAIN_BENCH_ENGINE_CMD` — a documented TEST
+  SEAM strictly DOWNSTREAM of the spend gates (G5) and recorded in `chain_env`,
+  so a stubbed run is visibly stubbed. 40 offline assertions in
+  `tests/automation/test-benchmark-runner.sh` (registered in run-evals §2c,
+  ~0.9s, suite 95/95): refusals-before-side-effects, scratch layout + canary
+  exclusions, results schema/counts vs a stub engine's known artifacts,
+  PRE-precedes-engine asserted BY the stub, all four verdict paths,
+  keep/cleanup rules. ZERO engine runs this session (G6/G9). Slice (c) —
+  `benchmark_compare.py` + docs + the first REAL baseline run (G9
+  user-approved spend) — remains; slice (b) certification per G8 folds into
+  the slice-(c) session.)*
+  *(slice (b) certified 2026-07-10 by a fresh non-implementer session per G8
+  (the slice-(c) session): 40/40 runner asserts + full evals green; gate order
+  re-verified against code — both refusals + the dirty-tree check fire before
+  ANY side effect (first write is the PRE append, `run-benchmark.sh:183`), PRE
+  strictly precedes engine launch, and the `CHAIN_BENCH_ENGINE_CMD` seam is
+  consulted only downstream of every gate with its value recorded in
+  `chain_env`; live refusal probes on the real repo (no flags and
+  --hypothesis-only → exit 2, plan printed, ledger byte-identical, no results
+  dir) plus a dirty-tree refusal re-proven on a clone; ZERO-SPEND dry assembly
+  (`CHAIN_BENCH_ENGINE_CMD='true'`) run inside a discarded git clone so the
+  probe's PRE/POST entries landed in the clone's ledger — the real append-only
+  ledger kept zero probe trace, nothing was ever deleted from it. Assembled
+  scratch verified: subrepo set + fixture overlay (fixture project-template won
+  the collision; `.venv`/`todos.json`/`benchmarks` excluded; 1 commit on main,
+  deterministic author, local bare origin ls-remote-reachable), then proven
+  AGENT-RUNNABLE exactly as the chain finds it — venv bootstrap per the fixture
+  project-template, pytest 3/3, app boot with `/health` 200 on port 5177,
+  goal_lint exit 0 inside scratch. No runner defects found; no edits needed.)*
 - **Problem:** "did my framework change help or hurt?" currently has no answer a weaker
   maintainer can trust. The per-session tripwire compares within a session; nothing
   compares across framework versions.
@@ -292,7 +423,9 @@ the system measures itself, and how it survives the next model change.
   3. Resync mirrors + `sync-cli-assets.py --cli claude --check`.
   4. Update the table in `.claude/model-orchestration.md` in the SAME commit.
   5. `./scripts/automation/run-evals.sh` green.
-  6. Run REL-1 judgment fixtures (mark "pending REL-1" until it ships).
+  6. Run REL-1 judgment fixtures: `./scripts/automation/run-judgment-evals.sh
+     --yes-spend` (G9: user-approved spend; the runner prints the estimate and
+     refuses without the flag).
   7. Run EVO-3 benchmark before/after (mark "pending EVO-3" until it ships).
   8. First-session watchlist: `gate-report.md` appears on any GOAL_ACHIEVED;
      `[escalation]` lines in the engine log; per-model rows in
@@ -635,7 +768,26 @@ benchmark (or a real session's telemetry) before AND after (G8).
 ## 10. P1 — Reliability & weaker-model hardening
 
 ### REL-1 · Judgment eval fixtures (golden verdict cases)
-- **Priority:** P1 · **Effort:** L (slice per judge) · **Risk:** LOW · **Status:** TODO
+- **Priority:** P1 · **Effort:** L (slice per judge) · **Risk:** LOW · **Status:** DONE
+  *(slice (a) — goal-evaluator cases + runner — implemented 2026-07-09; slice (b) —
+  reviewer cases, scratch-git diff representation, runner per-judge builders —
+  implemented 2026-07-09 (user-directed follow-on session); slice (c) — auditor cases +
+  phase-audit.sh runner builder — certified and confirm-run 2026-07-10 by a fresh
+  session (not the implementer) per G8, closing all three slices.
+  Confirmed real runs (user-approved spend):
+  (a) 2026-07-09, judge = claude-opus-4-8 @ effort max: 5/5 verdict classes correct —
+  case-01-clean-goal-achieved → GOAL_ACHIEVED (342s), case-02-first-failure-continue →
+  CONTINUE (234s), case-03-regression-broken-journey → REGRESSION (262s),
+  case-04-goal-drift-void-pass → CONTINUE (322s), case-05-secret-committed →
+  REGRESSION (196s).
+  (b) 2026-07-09, judge = claude-sonnet-5 @ effort max: 4/4 verdict classes correct —
+  case-01-clean-pass → PASS (172s), case-02-minor-nit-not-fail →
+  PASS_WITH_NOTES (149s), case-03-hardcoded-credential → FAIL (177s),
+  case-04-spec-contradiction → FAIL (192s).
+  (c) 2026-07-10, judge = claude-opus-4-8 @ effort max: 4/4 verdict classes correct —
+  case-01-clean-pass → PASS (220s), case-02-documented-gap-not-fail →
+  PASS_WITH_GAPS (352s), case-03-qa-green-spec-contradiction → FAIL (325s),
+  case-04-paid-service-live-key → FAIL (328s).)*
 - **Problem:** the single biggest retirement risk is silent judge regression — a weaker
   evaluator/reviewer/auditor emitting plausible-but-wrong verdicts. The eval suite
   checks parsers and gates, not judgment.
diff --git a/incredible_auto_dev/hooks/guard-dangerous-commands.sh b/incredible_auto_dev/hooks/guard-dangerous-commands.sh
index 54d054f..368aa62 100644
--- a/incredible_auto_dev/hooks/guard-dangerous-commands.sh
+++ b/incredible_auto_dev/hooks/guard-dangerous-commands.sh
@@ -10,8 +10,13 @@ CMD="${1:-}"
 [ -z "$CMD" ] && exit 0
 
 DANGEROUS_PATTERNS=(
-  # Destructive recursive deletes — system and home paths
-  "rm -rf /"
+  # Destructive recursive deletes — system and home paths.
+  # NOTE: deliberately NO bare "rm -rf /" entry — as a fixed-substring match it
+  # hits EVERY absolute-path rm, including the /tmp cleanup the permission
+  # allow-list explicitly permits (on the Codex backend this hook is the real
+  # enforcement gate, so the false positive banned /tmp removals outright).
+  # Bare `rm -rf /` and `rm -rf /<non-tmp>` are caught by the anchored regex
+  # `^rm -rf /(?!tmp)` in DANGEROUS_REGEXES below.
   "rm -rf ~"
   "rm -rf /home"
   "rm -rf /root"
@@ -75,8 +80,10 @@ done
 DANGEROUS_REGEXES=(
   # mv/cp targeting system directories
   "^(mv|cp) .+ /(etc|usr|boot|lib|var|root|sys|proc)(/|$)"
-  # rm -rf with any absolute path (other than /tmp)
-  "^rm -rf /(?!tmp)"
+  # rm -rf with any absolute path (other than /tmp) — anchored at command
+  # start OR after a shell chain separator (;, &&, ||, |, &), so `x && rm -rf /etc`
+  # is caught while `rm -rf /tmp/...` cleanup stays permitted.
+  "(^|[;&|][[:space:]]*)rm -rf /(?!tmp)"
   # chown with absolute path targets
   "^(sudo )?chown .+ /(etc|usr|home|root|var|boot)"
   # docker run mounting host filesystem sensitive directories
diff --git a/incredible_auto_dev/policy/permissions.yaml b/incredible_auto_dev/policy/permissions.yaml
index ad0c0dc..42ec13e 100644
--- a/incredible_auto_dev/policy/permissions.yaml
+++ b/incredible_auto_dev/policy/permissions.yaml
@@ -55,6 +55,8 @@ allow:
 - Bash(rm -rf *.egg-info*)
 - Bash(rm -rf coverage*)
 - Bash(rm -rf /tmp/*)
+- Bash(rm /tmp/*)
+- Bash(rm -f /tmp/*)
 - Bash(chmod +x *)
 - Bash(chmod -x *)
 - Bash(chmod u+x *)
@@ -119,8 +121,12 @@ allow:
 - Skill(superpowers-chrome:browsing)
 - mcp__plugin_superpowers-chrome_chrome__use_browser
 deny:
+# NOTE: no `Bash(rm -rf /*)` entry here — `*` matches ANY suffix, so that pattern
+# swallows every absolute path including /tmp (deny always beats allow, so it
+# nullified the `Bash(rm -rf /tmp/*)` allow above). Root/home wipes are covered
+# by the exact `Bash(rm -rf /)` below, the enumerated system dirs, and Claude
+# Code's built-in rm circuit breaker (fires even in bypassPermissions mode).
 - Bash(rm -rf /)
-- Bash(rm -rf /*)
 - Bash(rm -rf ~)
 - Bash(rm -rf ~/)
 - Bash(rm -rf ~/*)
@@ -175,5 +181,15 @@ deny:
 - Bash(apt-get upgrade*)
 - Bash(apt dist-upgrade*)
 - Bash(apt-get dist-upgrade*)
+# Claude Code has a BUILT-IN rm containment (independent of allow/deny rules
+# and hooks): `rm` may only delete inside the session's allowed working
+# directories. Verbatim runtime error without this: "rm in '/tmp/x' was
+# blocked. For security, Claude Code may only remove files from the allowed
+# working directories for this session". Tools can CREATE /tmp files freely
+# (pytest, playwright, service logs), so without this grant agents accumulate
+# tmp files they can never remove — the allow rules above are necessary but
+# not sufficient. Rendered into settings permissions.additionalDirectories.
+additionalDirectories:
+- /tmp
 codex_default_sandbox: workspace-write
 codex_default_approval: on-request
diff --git a/incredible_auto_dev/scripts/automation/goal-iter-lean.sh b/incredible_auto_dev/scripts/automation/goal-iter-lean.sh
index eeb9f3a..f4dc8b9 100755
--- a/incredible_auto_dev/scripts/automation/goal-iter-lean.sh
+++ b/incredible_auto_dev/scripts/automation/goal-iter-lean.sh
@@ -86,6 +86,12 @@ record_telemetry_event "iter_dispatch" "$(jq -cn --arg n "$ITER_NAME" --arg d "l
 
 ensure_phase_ports
 
+# Per-run tmp isolation: adopt the engine's CHAIN_TMPDIR (run-goal.sh sets it)
+# or create our own for standalone invocations. chain_tmp_cleanup is
+# owner-guarded, so under run-goal.sh the trap below removes nothing — the
+# engine rotates the dir at its iteration boundary instead.
+chain_tmp_init "$ITER_NAME"
+
 # ── Cleanup any stray dev server processes on exit ────────────────────────
 cleanup_iter_servers() {
   local _be_port="${CHAIN_BACKEND_PORT:-8000}"
@@ -104,7 +110,7 @@ cleanup_iter_servers() {
     fi
   fi
 }
-trap cleanup_iter_servers EXIT
+trap 'cleanup_iter_servers; chain_tmp_cleanup' EXIT
 
 # ── Step 1: Developer ─────────────────────────────────────────────────────
 run_developer() {
diff --git a/incredible_auto_dev/scripts/automation/lib/agent_permissions.py b/incredible_auto_dev/scripts/automation/lib/agent_permissions.py
index eb0c0bb..8a4a2c8 100644
--- a/incredible_auto_dev/scripts/automation/lib/agent_permissions.py
+++ b/incredible_auto_dev/scripts/automation/lib/agent_permissions.py
@@ -48,9 +48,28 @@ HARD_DEFAULT_DENIALS_NON_RELEASE: tuple[str, ...] = (
 
 # Tools denied for ALL agents (release-manager included). For dangerous
 # operations that should never happen mid-pipeline.
+#
+# NOTE: deliberately NO `Bash(rm -rf /*)` entry. In Claude Code permission
+# patterns `*` matches any suffix, so that pattern denies EVERY absolute-path
+# rm — including the /tmp cleanup the settings allow-list explicitly permits
+# (deny always beats allow). Root/home protection comes from the exact
+# `Bash(rm -rf /)` plus the enumerated system dirs below, mirroring
+# policy/permissions.yaml, plus Claude Code's built-in rm circuit breaker.
 HARD_DEFAULT_DENIALS_ALL: tuple[str, ...] = (
-    "Bash(rm -rf /*)",
     "Bash(rm -rf /)",
+    "Bash(rm -rf ~)",
+    "Bash(rm -rf ~/*)",
+    "Bash(rm -rf /home*)",
+    "Bash(rm -rf /root*)",
+    "Bash(rm -rf /etc*)",
+    "Bash(rm -rf /usr*)",
+    "Bash(rm -rf /var*)",
+    "Bash(rm -rf /boot*)",
+    "Bash(rm -rf /lib*)",
+    "Bash(rm -rf /opt*)",
+    "Bash(rm -rf /srv*)",
+    "Bash(rm -rf /sys*)",
+    "Bash(rm -rf /proc*)",
     "Bash(git push --force origin main)",
     "Bash(git push --force origin master)",
     "Bash(git push -f origin main)",
@@ -561,6 +580,35 @@ def _self_test() -> int:
         pd = disallowed_for("plain", agents_dir=d)
         assert "Bash(git push *)" in pd
 
+        # rm-ban regression (the /tmp cleanup bug): Claude Code pattern `*`
+        # matches ANY suffix and deny beats allow, so a default denial like
+        # "Bash(rm -rf /*)" silently swallowed every /tmp removal. Assert no
+        # default denial matches a legitimate /tmp cleanup for ANY agent class,
+        # while root/system-dir wipes stay denied.
+        def _bash_pat_matches(pattern: str, cmd: str) -> bool:
+            if not (pattern.startswith("Bash(") and pattern.endswith(")")):
+                return False
+            body = pattern[5:-1]
+            if body.endswith("*"):
+                return cmd.startswith(body[:-1])
+            return cmd == body
+
+        for _agent in ("plain", "developer", "release-manager"):
+            _dl = disallowed_for(_agent, agents_dir=d)
+            _tmp_hits = [
+                p for p in _dl
+                if p in HARD_DEFAULT_DENIALS_ALL + HARD_DEFAULT_DENIALS_NON_RELEASE
+                and _bash_pat_matches(p, "rm -rf /tmp/pytest-of-user/pytest-1")
+            ]
+            assert not _tmp_hits, f"{_agent}: default denial swallows /tmp removals: {_tmp_hits}"
+            assert "Bash(rm -rf /)" in _dl, f"{_agent}: exact-root denial missing"
+            assert "Bash(rm -rf /home*)" in _dl and "Bash(rm -rf /etc*)" in _dl, (
+                f"{_agent}: system-dir denials missing"
+            )
+            assert any(_bash_pat_matches(p, "rm -rf /home/someone") for p in _dl), (
+                f"{_agent}: /home wipe must stay denied"
+            )
+
         assert budget_for("developer", agents_dir=d) == 2.5
         assert budget_for("plain", agents_dir=d) is None
         assert budget_for("release-manager", agents_dir=d) is None
diff --git a/incredible_auto_dev/scripts/automation/lib/benchmark_compare.py b/incredible_auto_dev/scripts/automation/lib/benchmark_compare.py
new file mode 100644
index 0000000..0fa70bc
--- /dev/null
+++ b/incredible_auto_dev/scripts/automation/lib/benchmark_compare.py
@@ -0,0 +1,335 @@
+"""
+benchmark_compare.py — EVO-3 slice (c): delta table + verdict between two
+benchmark results JSONs written by scripts/automation/run-benchmark.sh.
+
+Compares OLD (baseline) against NEW (candidate) over the metrics a framework
+change is supposed to move, and renders one plain-text delta table:
+
+    wall_seconds · est. cost (economics agents total
+    gen_ai.usage.total_cost_usd) · total tokens in/out · journeys passing ·
+    attempt-1 review FAILs · malformed verdicts · final status / last verdict
+    (absolute old → new, plus % where meaningful)
+
+Verdict rule (EVO-3, docs/improvement-roadmap.md):
+    REGRESS   wall +>25% OR cost +>25% OR journeys-passing dropped
+    OK        otherwise — requires all three of those inputs comparable
+    UNKNOWN   any of those three inputs missing or the literal
+              "unknown (<why>)" on either side: that metric is INCOMPARABLE
+              and the tool refuses to guess a number to force a verdict.
+              (A comparable metric that WOULD have regressed is still
+              reported as a note — the signal is shown, never graded.)
+Non-verdict rows (tokens, review FAILs, malformed verdicts, status strings)
+may be unknown without affecting the verdict; they render as-is.
+
+Exit codes: 0 OK · 3 REGRESS · 4 UNKNOWN · 2 usage error / unreadable input.
+
+CLI:
+    python3 benchmark_compare.py <old.json> <new.json>
+    python3 benchmark_compare.py --self-test
+"""
+from __future__ import annotations
+
+import json
+import sys
+from pathlib import Path
+
+REGRESS_PCT = 25.0  # wall/cost regress threshold: strictly greater than +25%
+
+# (row label, extractor key, kind) — kind drives formatting and verdict role.
+_NUMERIC_ROWS = (
+    ("wall_seconds", "wall_seconds"),
+    ("est_cost_usd", "cost"),
+    ("tokens_in", "tokens_in"),
+    ("tokens_out", "tokens_out"),
+    ("journeys_passing", "journeys_passing"),
+    ("attempt1_review_fails", "attempt1_review_fails"),
+    ("malformed_verdicts", "malformed_verdicts"),
+)
+_STRING_ROWS = (
+    ("final_status", "final_status"),
+    ("last_verdict", "last_verdict"),
+)
+_VERDICT_INPUTS = ("wall_seconds", "cost", "journeys_passing")
+
+
+def _is_unknown(v) -> bool:
+    return v is None or (isinstance(v, str) and v.startswith("unknown ("))
+
+
+def _numeric(v):
+    """Return the value as a number, or None when it is not comparable."""
+    if isinstance(v, bool) or _is_unknown(v):
+        return None
+    return v if isinstance(v, (int, float)) else None
+
+
+def extract(results: dict) -> dict:
+    """Flatten one results JSON into the compared metric set. Missing paths
+    become the literal 'unknown (<why>)' — the same convention the runner
+    itself uses — so the renderer and verdict logic see one shape."""
+    meta = results.get("meta") or {}
+    outcome = results.get("outcome") or {}
+    economics = results.get("economics") or {}
+
+    def out_key(key):
+        return outcome[key] if key in outcome else f"unknown ({key} absent from outcome)"
+
+    sid = meta.get("session_id")
+    total = {}
+    agents = economics.get("agents")
+    if isinstance(agents, dict) and isinstance(agents.get(sid), dict):
+        total = agents[sid].get("total") or {}
+
+    def eco_key(key):
+        v = total.get(key)
+        return v if v is not None else f"unknown (economics agents total lacks {key})"
+
+    return {
+        "sha": meta.get("framework_sha", "unknown (meta.framework_sha absent)"),
+        "date": meta.get("date_utc", "unknown (meta.date_utc absent)"),
+        "wall_seconds": out_key("wall_seconds"),
+        "cost": eco_key("gen_ai.usage.total_cost_usd"),
+        "tokens_in": eco_key("gen_ai.usage.input_tokens"),
+        "tokens_out": eco_key("gen_ai.usage.output_tokens"),
+        "journeys_passing": out_key("journeys_passing_after"),
+        "journeys_total": out_key("journeys_total"),
+        "attempt1_review_fails": out_key("attempt1_review_fails"),
+        "malformed_verdicts": out_key("malformed_verdicts"),
+        "final_status": out_key("final_status"),
+        "last_verdict": out_key("last_verdict"),
+    }
+
+
+def _fmt(v) -> str:
+    if isinstance(v, float):
+        return f"{v:.4f}".rstrip("0").rstrip(".")
+    return str(v)
+
+
+def _delta_cell(old, new) -> str:
+    a, b = _numeric(old), _numeric(new)
+    if a is None or b is None:
+        return "incomparable"
+    d = b - a
+    cell = f"{d:+.4f}".rstrip("0").rstrip(".") if isinstance(d, float) else f"{d:+d}"
+    if d and a > 0:
+        cell += f" ({(d / a) * 100:+.1f}%)"
+    return cell
+
+
+def compare(old: dict, new: dict) -> tuple[str, list[str], list[str]]:
+    """Verdict over two extract() dicts.
+    Returns (verdict, reasons, notes): reasons explain the verdict; notes
+    carry regress-worthy signals seen while the verdict is UNKNOWN."""
+    unknown = []
+    regress = []
+    for key in _VERDICT_INPUTS:
+        a, b = _numeric(old[key]), _numeric(new[key])
+        if a is None or b is None:
+            side = "old" if a is None else "new"
+            unknown.append(f"{key} incomparable ({side}: {_fmt(old[key] if a is None else new[key])})")
+            continue
+        if key == "journeys_passing":
+            if b < a:
+                regress.append(f"journeys_passing dropped {_fmt(a)}→{_fmt(b)}")
+        elif a > 0:
+            pct = (b - a) / a * 100
+            if pct > REGRESS_PCT:
+                regress.append(f"{key} {pct:+.1f}% (>+{REGRESS_PCT:.0f}%)")
+        elif b > a:  # old == 0, new > 0: % undefined — refuse to grade it
+            unknown.append(f"{key} incomparable (old is 0, % undefined)")
+    if unknown:
+        notes = [f"would REGRESS on the comparable inputs: {'; '.join(regress)}"] if regress else []
+        return "UNKNOWN", unknown, notes
+    if regress:
+        return "REGRESS", regress, []
+    return "OK", ["no verdict input regressed"], []
+
+
+def render(old: dict, new: dict, old_path: str, new_path: str) -> tuple[str, int]:
+    """Full report text + exit code for one comparison."""
+    lines = [
+        f"[benchmark-compare] old: {old_path} (sha {str(old['sha'])[:12]} · {old['date']})",
+        f"[benchmark-compare] new: {new_path} (sha {str(new['sha'])[:12]} · {new['date']})",
+        "",
+        f"{'metric':<22} {'old':>18} {'new':>18}  delta",
+    ]
+    for label, key in _NUMERIC_ROWS:
+        o, n = old[key], new[key]
+        if key == "journeys_passing":
+            o = f"{_fmt(o)}/{_fmt(old['journeys_total'])}"
+            n = f"{_fmt(n)}/{_fmt(new['journeys_total'])}"
+        lines.append(f"{label:<22} {_fmt(o):>18} {_fmt(n):>18}  "
+                     f"{_delta_cell(old[key], new[key])}")
+    for label, key in _STRING_ROWS:
+        arrow = f"{_fmt(old[key])} → {_fmt(new[key])}"
+        if old[key] == new[key]:
+            arrow += "  (unchanged)"
+        lines.append(f"{label:<22} {arrow}")
+    verdict, reasons, notes = compare(old, new)
+    lines.append("")
+    lines.append(f"verdict: {verdict} ({'; '.join(reasons)})")
+    for note in notes:
+        lines.append(f"note: {note}")
+    code = {"OK": 0, "REGRESS": 3, "UNKNOWN": 4}[verdict]
+    return "\n".join(lines), code
+
+
+def run_compare(old_path: str, new_path: str) -> int:
+    loaded = []
+    for path in (old_path, new_path):
+        try:
+            loaded.append(json.loads(Path(path).read_text(encoding="utf-8")))
+        except (OSError, ValueError) as e:
+            print(f"[benchmark-compare] ERROR unreadable results JSON: {path}: {e}",
+                  file=sys.stderr)
+            return 2
+        if not isinstance(loaded[-1], dict):
+            print(f"[benchmark-compare] ERROR not a results object: {path}",
+                  file=sys.stderr)
+            return 2
+    text, code = render(extract(loaded[0]), extract(loaded[1]), old_path, new_path)
+    print(text)
+    return code
+
+
+# ── self-test ─────────────────────────────────────────────────────────────────
+
+_BASE = {
+    "meta": {"date_utc": "2026-07-10T00:00:00Z", "framework_sha": "a" * 40,
+             "session_id": "bench-20260710-0000"},
+    "outcome": {"engine_exit_code": 0, "final_status": "GOAL_ACHIEVED",
+                "last_verdict": "GOAL_ACHIEVED", "iterations_used": 2,
+                "journeys_passing_after": 3, "journeys_total": 3,
+                "attempt1_review_fails": 1, "malformed_verdicts": 0,
+                "wall_seconds": 9000},
+    "economics": {"agents": {"bench-20260710-0000": {"total": {
+        "gen_ai.usage.input_tokens": 140000,
+        "gen_ai.usage.output_tokens": 70000,
+        "gen_ai.usage.total_cost_usd": 3.20,
+    }}}},
+}
+
+
+def _variant(**outcome_or_special) -> dict:
+    """Deep-copied _BASE with outcome keys (or cost=/sid=) overridden."""
+    r = json.loads(json.dumps(_BASE))
+    for k, v in outcome_or_special.items():
+        if k == "cost":
+            r["economics"]["agents"][r["meta"]["session_id"]]["total"][
+                "gen_ai.usage.total_cost_usd"] = v
+        elif k == "no_agents":
+            r["economics"]["agents"] = {}
+        else:
+            r["outcome"][k] = v
+    return r
+
+
+def _verdict(old: dict, new: dict) -> tuple[str, int]:
+    text, code = render(extract(old), extract(new), "old.json", "new.json")
+    v = next(l for l in text.splitlines() if l.startswith("verdict: "))
+    return v.split()[1], code
+
+
+def _self_test() -> int:
+    import contextlib
+    import io
+    import tempfile
+
+    # 0. identical pair (the baseline-vs-baseline sanity): all deltas 0 → OK 0
+    text, code = render(extract(_BASE), extract(_BASE), "a.json", "b.json")
+    assert code == 0 and "verdict: OK" in text, text
+    for row in ("wall_seconds", "est_cost_usd", "tokens_in", "tokens_out",
+                "journeys_passing", "attempt1_review_fails", "malformed_verdicts",
+                "final_status", "last_verdict"):
+        assert any(l.startswith(row) for l in text.splitlines()), f"row missing: {row}"
+    data_rows = [l for l in text.splitlines()
+                 if l.split() and l.split()[0] in dict(_NUMERIC_ROWS)]
+    assert all(("+0" in l) or l.rstrip().endswith(" 0") or " 0 " in l for l in data_rows) \
+        and "incomparable" not in text, f"identical pair must show zero deltas:\n{text}"
+    assert "(unchanged)" in text
+
+    # 1. wall +>25% → REGRESS 3; exactly +25% is NOT a regress (strictly greater)
+    assert _verdict(_BASE, _variant(wall_seconds=11251)) == ("REGRESS", 3)
+    assert _verdict(_BASE, _variant(wall_seconds=11250)) == ("OK", 0)
+    # improvement direction never regresses
+    assert _verdict(_BASE, _variant(wall_seconds=100)) == ("OK", 0)
+
+    # 2. cost +>25% → REGRESS; +25% exactly → OK
+    assert _verdict(_BASE, _variant(cost=4.01)) == ("REGRESS", 3)
+    assert _verdict(_BASE, _variant(cost=4.00)) == ("OK", 0)
+
+    # 3. journeys-passing dropped → REGRESS (any drop, no threshold)
+    assert _verdict(_BASE, _variant(journeys_passing_after=2)) == ("REGRESS", 3)
+    assert _verdict(_BASE, _variant(journeys_passing_after=4)) == ("OK", 0)
+
+    # 4. literal unknown on a verdict input (either side) → UNKNOWN 4
+    unk = "unknown (journey-history.json missing)"
+    assert _verdict(_BASE, _variant(journeys_passing_after=unk)) == ("UNKNOWN", 4)
+    assert _verdict(_variant(journeys_passing_after=unk), _BASE) == ("UNKNOWN", 4)
+    assert _verdict(_BASE, _variant(wall_seconds="unknown (x)")) == ("UNKNOWN", 4)
+
+    # 5. missing economics (no agents entry) → cost incomparable → UNKNOWN
+    assert _verdict(_BASE, _variant(no_agents=True)) == ("UNKNOWN", 4)
+
+    # 6. UNKNOWN outranks REGRESS, but the regress signal survives as a note
+    both = _variant(wall_seconds=20000, journeys_passing_after=unk)
+    text, code = render(extract(_BASE), extract(both), "o", "n")
+    assert code == 4 and "verdict: UNKNOWN" in text
+    assert "would REGRESS" in text and "wall_seconds" in text, text
+
+    # 7. unknown on a NON-verdict row does not affect the verdict
+    tokenless = _variant()
+    del tokenless["economics"]["agents"][_BASE["meta"]["session_id"]]["total"][
+        "gen_ai.usage.input_tokens"]
+    assert _verdict(_BASE, tokenless) == ("OK", 0)
+
+    # 8. old wall of 0 with a nonzero new: % undefined → UNKNOWN, never a guess
+    assert _verdict(_variant(wall_seconds=0), _variant(wall_seconds=500)) == ("UNKNOWN", 4)
+    assert _verdict(_variant(wall_seconds=0), _variant(wall_seconds=0)) == ("OK", 0)
+
+    # 9. file-level: unreadable / non-JSON / non-object → 2; good pair round-trips
+    with tempfile.TemporaryDirectory() as tmp:
+        d = Path(tmp)
+        (d / "old.json").write_text(json.dumps(_BASE), encoding="utf-8")
+        (d / "new.json").write_text(json.dumps(_variant(wall_seconds=11251)),
+                                    encoding="utf-8")
+        (d / "junk.json").write_text("not json", encoding="utf-8")
+        (d / "list.json").write_text("[1,2]", encoding="utf-8")
+
+        def _run(*argv) -> tuple[int, str, str]:
+            out, err = io.StringIO(), io.StringIO()
+            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
+                rc = main(list(argv))
+            return rc, out.getvalue(), err.getvalue()
+
+        rc, out, _ = _run(str(d / "old.json"), str(d / "new.json"))
+        assert rc == 3 and "verdict: REGRESS" in out
+        rc, _, err = _run(str(d / "missing.json"), str(d / "new.json"))
+        assert rc == 2 and "unreadable" in err
+        rc, _, err = _run(str(d / "junk.json"), str(d / "new.json"))
+        assert rc == 2 and "unreadable" in err
+        rc, _, err = _run(str(d / "list.json"), str(d / "new.json"))
+        assert rc == 2 and "not a results object" in err
+
+    # 10. usage errors → 2
+    with contextlib.redirect_stderr(io.StringIO()):
+        assert main([]) == 2
+        assert main(["one.json"]) == 2
+        assert main(["a", "b", "c"]) == 2
+
+    print("self-test passed")
+    return 0
+
+
+def main(argv: list[str]) -> int:
+    if argv and argv[0] == "--self-test":
+        return _self_test()
+    if len(argv) != 2 or argv[0] in ("-h", "--help"):
+        print(__doc__, file=sys.stderr)
+        return 2
+    return run_compare(argv[0], argv[1])
+
+
+if __name__ == "__main__":
+    sys.exit(main(sys.argv[1:]))
diff --git a/incredible_auto_dev/scripts/automation/lib/chain-tmp.sh b/incredible_auto_dev/scripts/automation/lib/chain-tmp.sh
new file mode 100644
index 0000000..415985b
--- /dev/null
+++ b/incredible_auto_dev/scripts/automation/lib/chain-tmp.sh
@@ -0,0 +1,267 @@
+#!/usr/bin/env bash
+# chain-tmp.sh — per-run TMPDIR isolation, owner-guarded cleanup, and a
+# janitor for strays. Sourced by lib/common.sh so every pipeline script gets
+# these; safe under `set -euo pipefail`.
+#
+# Why: multiple pipeline jobs (different projects) run concurrently on one
+# machine as the same user. Tools the agents run (pytest, playwright/chromium,
+# mktemp) write to shared /tmp and race each other's pruning (see
+# .claude/anti-patterns.md #21). Giving each run its own short-lived dir —
+# exported as TMPDIR — removes the sharing entirely; cleanup is then a single
+# owner-guarded rm.
+#
+# API:
+#   chain_tmp_init <run-id>    create+export, or ADOPT an inherited dir (nested)
+#   chain_tmp_cleanup          remove the dir iff THIS process created it
+#   chain_tmp_rotate <run-id>  cleanup (if owner) + fresh init — iteration boundary
+#   chain_tmp_janitor          sweep strays from crashed/legacy runs (age+liveness)
+#
+# Knobs:
+#   CHAIN_TMPDIR_DISABLE=true    leave the environment completely untouched
+#   CHAIN_TMP_JANITOR=false      disable the janitor sweep
+#   CHAIN_TMP_MAX_AGE_HOURS=24   janitor age gate
+#   CHAIN_TMP_ROOT=/tmp          base dir (tests point this at a scratch dir)
+#
+# NOTE the /tmp/{claude,codex}-quota-exhausted sentinels (lib/quota-retry.sh)
+# are INTENTIONALLY shared across concurrent jobs (quota is account-global):
+# they stay in /tmp and the janitor never matches these names.
+
+# chain_tmp_init <run-id> — creates /tmp/iad.<sanitized-id>.<pid> (SHORT path
+# on purpose: unix sockets created under TMPDIR — e.g. Chromium's — have a
+# 108-char path limit), exports TMPDIR/TMP/TEMP + CHAIN_TMPDIR +
+# CHAIN_TMPDIR_OWNER_PID. Idempotent: when CHAIN_TMPDIR is already set and
+# exists (run-phase.sh nested under run-goal.sh), the inherited dir is adopted
+# WITHOUT taking ownership. Never fails the caller.
+chain_tmp_init() {
+  [[ "${CHAIN_TMPDIR_DISABLE:-false}" == "true" ]] && return 0
+  if [[ -n "${CHAIN_TMPDIR:-}" && -d "${CHAIN_TMPDIR:-}" ]]; then
+    export TMPDIR="$CHAIN_TMPDIR" TMP="$CHAIN_TMPDIR" TEMP="$CHAIN_TMPDIR"
+    return 0
+  fi
+  local id="${1:-run}"
+  id="$(printf '%s' "$id" | tr -c 'a-zA-Z0-9._-' '-' | cut -c1-60)"
+  # ${BASHPID:-$$} for BOTH the name suffix and the owner record, so name and
+  # owner always agree even when init runs in a subshell.
+  local dir="${CHAIN_TMP_ROOT:-/tmp}/iad.${id}.${BASHPID:-$$}"
+  if ! mkdir -p "$dir" 2>/dev/null; then
+    echo "[chain-tmp] WARNING: cannot create $dir — keeping the shared default tmp." >&2
+    return 0
+  fi
+  chmod 700 "$dir" 2>/dev/null || true
+  export CHAIN_TMPDIR="$dir"
+  export CHAIN_TMPDIR_OWNER_PID="${BASHPID:-$$}"
+  export TMPDIR="$dir" TMP="$dir" TEMP="$dir"
+  return 0
+}
+
+# chain_tmp_cleanup — remove CHAIN_TMPDIR iff this exact process created it.
+# ${BASHPID:-$$} (not $$) so a stray call from a subshell can never delete the
+# dir out from under the main script. Path-shape guard against a corrupted var.
+chain_tmp_cleanup() {
+  [[ -n "${CHAIN_TMPDIR:-}" ]] || return 0
+  [[ "${CHAIN_TMPDIR_OWNER_PID:-}" == "${BASHPID:-$$}" ]] || return 0
+  case "$CHAIN_TMPDIR" in
+    */iad.*) rm -rf -- "$CHAIN_TMPDIR" 2>/dev/null || true ;;
+  esac
+  return 0
+}
+
+# chain_tmp_rotate <run-id> — iteration boundary for long-lived engines
+# (run-goal.sh): drop the current dir (owner-guarded) and start a fresh one.
+chain_tmp_rotate() {
+  [[ "${CHAIN_TMPDIR_DISABLE:-false}" == "true" ]] && return 0
+  chain_tmp_cleanup
+  unset CHAIN_TMPDIR CHAIN_TMPDIR_OWNER_PID
+  chain_tmp_init "${1:-run}"
+}
+
+# chain_tmp_janitor — reap strays owned by this user:
+#   1. iad.* dirs older than the gate AND whose embedded owner pid is dead
+#      (mtime alone is unsafe: writes to files INSIDE a dir don't touch the
+#      dir's mtime, so a >24h live goal session could look stale).
+#   2. legacy loose files in the base dir from pre-TMPDIR runs (quota/usage
+#      mktemp leftovers, per-role service logs) — age-gated.
+#   3. entries under /tmp/pytest-of-$USER (numbered basetemp dirs, garbage-*,
+#      stale .lock) — age-gated so a live concurrent run (minutes old) is safe.
+# NEVER touches the quota sentinels (no pattern matches their fixed names:
+# 'claude-quota-??????.log' requires a 6-char suffix plus '.log', which
+# 'claude-quota-exhausted' has neither of).
+chain_tmp_janitor() {
+  [[ "${CHAIN_TMP_JANITOR:-true}" == "true" ]] || return 0
+  local max_age_hours="${CHAIN_TMP_MAX_AGE_HOURS:-24}"
+  [[ "$max_age_hours" =~ ^[0-9]+$ ]] || max_age_hours=24
+  local mmin=$(( max_age_hours * 60 ))
+  local base="${CHAIN_TMP_ROOT:-/tmp}"
+
+  local d pid
+  for d in "$base"/iad.*; do
+    [[ -e "$d" ]] || continue
+    [[ -O "$d" ]] || continue
+    [[ -n "$(find "$d" -maxdepth 0 -mmin "+$mmin" 2>/dev/null)" ]] || continue
+    pid="${d##*.}"
+    if [[ "$pid" =~ ^[0-9]+$ ]] && kill -0 "$pid" 2>/dev/null; then
+      continue   # owning process still alive — never touch, whatever the age
+    fi
+    rm -rf -- "$d" 2>/dev/null || true
+  done
+
+  local pat
+  for pat in 'claude-quota-??????.log' 'codex-quota-??????.log' \
+             'claude-usage-??????.json' 'codex-usage-??????.json' \
+             'qa-backend*.log' 'qa-frontend*.log' \
+             'browser-qa-backend*.log' 'browser-qa-frontend*.log' \
+             'fanout-backend*.log' 'fanout-frontend*.log' \
+             'demo-backend*.log' 'demo-frontend*.log' \
+             'goal-iter-backend*.log' 'goal-iter-frontend*.log'; do
+    find "$base" -maxdepth 1 -type f -name "$pat" -uid "$(id -u)" \
+      -mmin "+$mmin" -exec rm -f {} + 2>/dev/null || true
+  done
+
+  local pyroot="$base/pytest-of-$(id -un)"
+  if [[ -d "$pyroot" && -O "$pyroot" ]]; then
+    find "$pyroot" -mindepth 1 -maxdepth 1 -uid "$(id -u)" -mmin "+$mmin" \
+      -exec rm -rf {} + 2>/dev/null || true
+    rmdir "$pyroot" 2>/dev/null || true   # remove the root only if now empty
+  fi
+  return 0
+}
+
+# ── Self-test (only when invoked directly: `bash chain-tmp.sh self-test`) ────
+# Hermetic and fast: everything runs against a scratch CHAIN_TMP_ROOT.
+# Lifecycle subtests run in CHILD bash processes so ownership semantics
+# (owner pid vs non-owner) are exercised for real, not simulated.
+if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
+  case "${1:-}" in
+    self-test)
+      _p=0; _f=0
+      _ok()  { _p=$((_p+1)); echo "  OK: $*"; }
+      _bad() { _f=$((_f+1)); echo "  FAIL: $*" >&2; }
+      T=$(mktemp -d)
+      SELF="${BASH_SOURCE[0]}"
+
+      # init: creates the named dir, exports the TMPDIR family, records owner
+      if CHAIN_TMP_ROOT="$T" bash -c '
+           source "'"$SELF"'"
+           chain_tmp_init "goal-x-iter-1"
+           [[ "$CHAIN_TMPDIR" == "'"$T"'/iad.goal-x-iter-1.$BASHPID" ]] || exit 1
+           [[ -d "$CHAIN_TMPDIR" ]] || exit 2
+           [[ "$TMPDIR" == "$CHAIN_TMPDIR" && "$TMP" == "$CHAIN_TMPDIR" && "$TEMP" == "$CHAIN_TMPDIR" ]] || exit 3
+           [[ "$CHAIN_TMPDIR_OWNER_PID" == "$BASHPID" ]] || exit 4
+           chain_tmp_cleanup
+           [[ ! -d "$CHAIN_TMPDIR" ]] || exit 5'; then
+        _ok "init creates+exports+owns; owner cleanup removes"
+      else
+        _bad "init/cleanup lifecycle (subtest exit $?)"
+      fi
+
+      # adopt: a second init in the same process must keep the first dir;
+      # an init in a CHILD process must adopt (no second dir, no ownership)
+      if CHAIN_TMP_ROOT="$T" bash -c '
+           source "'"$SELF"'"
+           chain_tmp_init "outer"
+           prev="$CHAIN_TMPDIR"
+           chain_tmp_init "other"
+           [[ "$CHAIN_TMPDIR" == "$prev" ]] || exit 1
+           bash -c "source \"'"$SELF"'\"; chain_tmp_init nested; chain_tmp_cleanup"
+           [[ -d "$prev" ]] || exit 2                      # child cleanup must be a no-op
+           n=$(ls -d "'"$T"'"/iad.* 2>/dev/null | wc -l)
+           [[ "$n" -eq 1 ]] || exit 3                      # child must not mint a second dir
+           chain_tmp_cleanup
+           [[ ! -d "$prev" ]] || exit 4'; then
+        _ok "adopt: same-process re-init and child init reuse the dir; non-owner cleanup no-op"
+      else
+        _bad "adopt semantics (subtest exit $?)"
+      fi
+
+      # sanitize: hostile run-id cannot escape the base dir
+      if CHAIN_TMP_ROOT="$T" bash -c '
+           source "'"$SELF"'"
+           chain_tmp_init "../evil id/x"
+           b="$(basename "$CHAIN_TMPDIR")"
+           [[ "$b" == iad.* && "$CHAIN_TMPDIR" != *"/../"* && "$(dirname "$CHAIN_TMPDIR")" == "'"$T"'" ]] || exit 1
+           chain_tmp_cleanup'; then
+        _ok "init sanitizes hostile run-ids"
+      else
+        _bad "run-id sanitization (subtest exit $?)"
+      fi
+
+      # rotate: old dir goes, fresh dir comes
+      if CHAIN_TMP_ROOT="$T" bash -c '
+           source "'"$SELF"'"
+           chain_tmp_init "iter-0"; a="$CHAIN_TMPDIR"; touch "$a/x.log"
+           chain_tmp_rotate "iter-1"; b="$CHAIN_TMPDIR"
+           [[ ! -d "$a" && -d "$b" && "$b" == *iter-1* ]] || exit 1
+           chain_tmp_cleanup'; then
+        _ok "rotate clears the previous dir and exports a fresh one"
+      else
+        _bad "rotate (subtest exit $?)"
+      fi
+
+      # disable knob: env left completely untouched
+      if CHAIN_TMP_ROOT="$T" bash -c '
+           source "'"$SELF"'"
+           CHAIN_TMPDIR_DISABLE=true chain_tmp_init "x"
+           [[ -z "${CHAIN_TMPDIR:-}" && -z "${TMPDIR:-}" ]]'; then
+        _ok "CHAIN_TMPDIR_DISABLE leaves the environment untouched"
+      else
+        _bad "disable knob created state"
+      fi
+
+      # cleanup path-shape guard: refuses to rm a non-iad path
+      if CHAIN_TMP_ROOT="$T" bash -c '
+           source "'"$SELF"'"
+           mkdir -p "'"$T"'/notiad"
+           CHAIN_TMPDIR="'"$T"'/notiad" CHAIN_TMPDIR_OWNER_PID="$BASHPID" chain_tmp_cleanup
+           [[ -d "'"$T"'/notiad" ]]'; then
+        _ok "cleanup refuses a non-iad path"
+      else
+        _bad "cleanup removed a non-iad path"
+      fi
+
+      # janitor: age + pid-liveness + pattern safety (incl. sentinels)
+      mkdir -p "$T/iad.dead.999999999" "$T/iad.live.$$" "$T/iad.fresh.999999998"
+      touch -d '2 days ago' "$T/iad.dead.999999999" "$T/iad.live.$$"
+      : > "$T/claude-quota-AbC123.log";  touch -d '2 days ago' "$T/claude-quota-AbC123.log"
+      : > "$T/claude-quota-XyZ789.log"                          # fresh — must survive
+      : > "$T/fanout-backend-3101.log"; touch -d '2 days ago' "$T/fanout-backend-3101.log"
+      : > "$T/claude-usage-Qq1Ww2.json"; touch -d '2 days ago' "$T/claude-usage-Qq1Ww2.json"
+      : > "$T/claude-quota-exhausted";  touch -d '2 days ago' "$T/claude-quota-exhausted"
+      : > "$T/codex-quota-exhausted";   touch -d '2 days ago' "$T/codex-quota-exhausted"
+      _pyroot="$T/pytest-of-$(id -un)"
+      mkdir -p "$_pyroot/garbage-1" "$_pyroot/pytest-7"
+      touch -d '2 days ago' "$_pyroot/garbage-1"
+      # Call the function directly — it is already defined above. Do NOT
+      # `source "$SELF"` from a subshell of this script: there BASH_SOURCE==$0
+      # and $1 is still "self-test", so the sourced copy re-enters this arm
+      # and recurses forever.
+      CHAIN_TMP_ROOT="$T" chain_tmp_janitor
+      [[ ! -d "$T/iad.dead.999999999" ]]      && _ok "janitor reaps old dir with dead pid"    || _bad "old dead-pid dir survived"
+      [[ -d "$T/iad.live.$$" ]]               && _ok "janitor keeps old dir with LIVE pid"    || _bad "live-pid dir was reaped"
+      [[ -d "$T/iad.fresh.999999998" ]]       && _ok "janitor keeps fresh dir"                || _bad "fresh dir was reaped"
+      [[ ! -f "$T/claude-quota-AbC123.log" ]] && _ok "janitor reaps old quota log"            || _bad "old quota log survived"
+      [[ -f "$T/claude-quota-XyZ789.log" ]]   && _ok "janitor keeps fresh quota log"          || _bad "fresh quota log reaped"
+      [[ ! -f "$T/fanout-backend-3101.log" ]] && _ok "janitor reaps old service log"          || _bad "old service log survived"
+      [[ ! -f "$T/claude-usage-Qq1Ww2.json" ]] && _ok "janitor reaps old usage sidecar"       || _bad "old usage sidecar survived"
+      if [[ -f "$T/claude-quota-exhausted" && -f "$T/codex-quota-exhausted" ]]; then
+        _ok "janitor NEVER touches the quota sentinels"
+      else
+        _bad "a quota sentinel was deleted"
+      fi
+      [[ ! -d "$_pyroot/garbage-1" ]]         && _ok "janitor reaps old pytest-of entry"      || _bad "old pytest-of entry survived"
+      [[ -d "$_pyroot/pytest-7" ]]            && _ok "janitor keeps fresh pytest-of entry"    || _bad "fresh pytest-of entry reaped"
+
+      # janitor disable knob
+      mkdir -p "$T/iad.dead2.999999997"; touch -d '2 days ago' "$T/iad.dead2.999999997"
+      CHAIN_TMP_ROOT="$T" CHAIN_TMP_JANITOR=false chain_tmp_janitor
+      [[ -d "$T/iad.dead2.999999997" ]]       && _ok "CHAIN_TMP_JANITOR=false disables the sweep" || _bad "janitor ran while disabled"
+
+      rm -rf "$T"
+      echo "[chain-tmp self-test] ${_p} pass, ${_f} fail"
+      [[ "$_f" -eq 0 ]] || exit 1
+      ;;
+    *)
+      echo "Usage: $0 self-test" >&2
+      exit 2
+      ;;
+  esac
+fi
diff --git a/incredible_auto_dev/scripts/automation/lib/common.sh b/incredible_auto_dev/scripts/automation/lib/common.sh
index bd32d13..222a436 100644
--- a/incredible_auto_dev/scripts/automation/lib/common.sh
+++ b/incredible_auto_dev/scripts/automation/lib/common.sh
@@ -310,6 +310,10 @@ source "$(dirname "${BASH_SOURCE[0]}")/project-gates.sh"
 # step_done_valid, step_invalidate_from, chain_tree_hash, goal_iter_dir)
 # shellcheck source=checkpoint.sh
 source "$(dirname "${BASH_SOURCE[0]}")/checkpoint.sh"
+# Per-run TMPDIR isolation + cleanup + janitor (defines chain_tmp_init,
+# chain_tmp_cleanup, chain_tmp_rotate, chain_tmp_janitor)
+# shellcheck source=chain-tmp.sh
+source "$(dirname "${BASH_SOURCE[0]}")/chain-tmp.sh"
 
 # Deterministic port offset (0..999) derived from the project directory so that
 # multiple projects sharing this subtree each land in their own port range.
@@ -464,14 +468,17 @@ reclaim_canonical_phase_ports() {
   return 0
 }
 
-# Return a project-scoped /tmp log path to avoid cross-project log clobbering
+# Return a project-scoped log path to avoid cross-project log clobbering
 # when multiple projects share this subtree (each project has a unique port
 # offset, so using the port as a discriminator gives a stable per-project path).
+# Lands in the per-run CHAIN_TMPDIR when the pipeline initialized one
+# (chain_tmp_init), so run-end cleanup is a single rm; legacy shared /tmp
+# otherwise (standalone step-script invocations).
 # Usage: _qa_log_path <role>  (role e.g. "qa-backend" or "browser-qa-frontend")
 _qa_log_path() {
   local role="$1"
   local port="${CHAIN_BACKEND_PORT:-${CHAIN_FRONTEND_PORT:-0}}"
-  echo "/tmp/${role}-${port}.log"
+  echo "${CHAIN_TMPDIR:-/tmp}/${role}-${port}.log"
 }
 
 # Parse the TCP port out of a localhost URL (http://localhost:3836/… -> 3836).
@@ -1001,14 +1008,20 @@ cleanup_phase_artifacts() {
   # at the old path — never touch runs/<phase>/{plan,status,summary}.json etc.
   rm -f "$REPO_ROOT/runs/$phase/summary.html" 2>/dev/null || true
   rm -f "$REPO_ROOT/runs/goal-session-"*"/index.html" 2>/dev/null || true
-  # /tmp logs from QA and browser-qa (both legacy shared paths and current
-  # port-scoped paths written by _qa_log_path)
-  rm -f /tmp/qa-backend.log /tmp/qa-frontend.log /tmp/browser-qa-backend.log /tmp/browser-qa-frontend.log 2>/dev/null || true
+  # Service logs from qa / browser-qa / fanout / demo / goal-iter boots, in BOTH
+  # locations: legacy shared /tmp (fixed and port-scoped names from pre-TMPDIR
+  # runs) and the current per-run CHAIN_TMPDIR (written by _qa_log_path).
+  local _role _port _dir
   local _backend_port="${CHAIN_BACKEND_PORT:-0}"
   local _frontend_port="${CHAIN_FRONTEND_PORT:-0}"
-  rm -f "/tmp/qa-backend-${_backend_port}.log" "/tmp/qa-frontend-${_backend_port}.log" \
-        "/tmp/browser-qa-backend-${_backend_port}.log" "/tmp/browser-qa-frontend-${_backend_port}.log" \
-        2>/dev/null || true
+  for _dir in /tmp ${CHAIN_TMPDIR:+"$CHAIN_TMPDIR"}; do
+    for _role in qa browser-qa fanout demo goal-iter; do
+      rm -f "$_dir/${_role}-backend.log" "$_dir/${_role}-frontend.log" 2>/dev/null || true
+      for _port in "$_backend_port" "$_frontend_port"; do
+        rm -f "$_dir/${_role}-backend-${_port}.log" "$_dir/${_role}-frontend-${_port}.log" 2>/dev/null || true
+      done
+    done
+  done
   # Fix extensionless screenshots in evidence dirs (Chrome MCP naming drift).
   # Rename to .png if the file is a valid PNG; remove otherwise.
   local evidence_dir
@@ -1359,6 +1372,33 @@ EOF
       unset -f curl 2>/dev/null || true
       unset CHAIN_FRONTEND_DIR CHAIN_FRONTEND_HEAL_TIMEOUT CHAIN_KILL_GRACE_SECONDS 2>/dev/null || true
       rm -rf "$_ROOT"
+
+      echo "[common.sh self-test] _qa_log_path CHAIN_TMPDIR scoping"
+      _q=$(CHAIN_TMPDIR="/x/y" CHAIN_BACKEND_PORT=8123 _qa_log_path "qa-backend")
+      if [[ "$_q" == "/x/y/qa-backend-8123.log" ]]; then _t_ok "_qa_log_path uses CHAIN_TMPDIR"; else _t_bad "_qa_log_path: got $_q"; fi
+      _q=$(CHAIN_TMPDIR="" CHAIN_BACKEND_PORT=8123 _qa_log_path "qa-backend")
+      if [[ "$_q" == "/tmp/qa-backend-8123.log" ]]; then _t_ok "_qa_log_path legacy /tmp fallback"; else _t_bad "_qa_log_path fallback: got $_q"; fi
+
+      echo "[common.sh self-test] cleanup_phase_artifacts role-log sweep"
+      _CROOT=$(mktemp -d)
+      mkdir -p "$_CROOT/repo/apps" "$_CROOT/tmpd"
+      for _r in qa browser-qa fanout demo goal-iter; do
+        : > "$_CROOT/tmpd/${_r}-backend-99911.log"
+        : > "$_CROOT/tmpd/${_r}-frontend-99912.log"
+      done
+      : > "$_CROOT/tmpd/keep-me.txt"
+      # Subshell: repoint REPO_ROOT at scratch so the repo-root globs are inert.
+      ( REPO_ROOT="$_CROOT/repo" CHAIN_TMPDIR="$_CROOT/tmpd" \
+        CHAIN_BACKEND_PORT=99911 CHAIN_FRONTEND_PORT=99912 \
+        cleanup_phase_artifacts "selftest-phase" ) >/dev/null 2>&1 || true
+      if ls "$_CROOT/tmpd"/*-9991[12].log >/dev/null 2>&1; then
+        _t_bad "cleanup left role logs in CHAIN_TMPDIR"
+      else
+        _t_ok "cleanup removed all role logs from CHAIN_TMPDIR"
+      fi
+      if [[ -f "$_CROOT/tmpd/keep-me.txt" ]]; then _t_ok "cleanup kept unrelated file"; else _t_bad "cleanup removed unrelated file"; fi
+      rm -rf "$_CROOT"
+
       echo "[common.sh self-test] ${_t_pass} pass, ${_t_fail} fail"
       [[ "$_t_fail" -eq 0 ]] || exit 1
       ;;
diff --git a/incredible_auto_dev/scripts/automation/lib/interactive-dispatch.sh b/incredible_auto_dev/scripts/automation/lib/interactive-dispatch.sh
index 6bfea54..6540fb2 100644
--- a/incredible_auto_dev/scripts/automation/lib/interactive-dispatch.sh
+++ b/incredible_auto_dev/scripts/automation/lib/interactive-dispatch.sh
@@ -121,6 +121,15 @@ _interactive_invoke() {
   local prompt
   prompt="$(_interactive_extract_prompt "$@")"
 
+  # Pump-mode TMPDIR bridge: interactive subagents execute in the PUMP session's
+  # environment — the engine's exported TMPDIR never reaches them. Relay it as a
+  # prompt instruction instead (the only lever the Task tool offers). Belt and
+  # braces: an agent may ignore it; chain_tmp_janitor sweeps whatever still
+  # lands in shared /tmp.
+  if [[ -n "${CHAIN_TMPDIR:-}" && -d "${CHAIN_TMPDIR:-}" ]]; then
+    prompt+=$'\n\n'"Environment note: this pipeline run isolates temp files. Before running tests or any command that writes temporary files, run: export TMPDIR=\"$CHAIN_TMPDIR\" TMP=\"$CHAIN_TMPDIR\" TEMP=\"$CHAIN_TMPDIR\""
+  fi
+
   # Optional per-dispatch model override (escalation ladder / two-key confirm).
   # Empty means "no override — the subagent's frontmatter tier applies".
   local model_override="${CHAIN_MODEL_OVERRIDE:-}"
diff --git a/incredible_auto_dev/scripts/automation/lib/quota-retry.sh b/incredible_auto_dev/scripts/automation/lib/quota-retry.sh
index a3ee9c8..21af5c4 100644
--- a/incredible_auto_dev/scripts/automation/lib/quota-retry.sh
+++ b/incredible_auto_dev/scripts/automation/lib/quota-retry.sh
@@ -154,9 +154,39 @@ DISPATCH_UNAVAILABLE_EXIT_CODE=70
 
 # Sentinel file paths — per CLI so Claude and Codex don't trip over each other
 # on machines where both are configured.
+# INTENTIONALLY fixed names in shared /tmp, NOT ${TMPDIR}/CHAIN_TMPDIR: quota
+# exhaustion is account-global, so every concurrent pipeline job on this
+# machine must see the same sentinel. chain_tmp_janitor (lib/chain-tmp.sh)
+# never matches these names.
 _QUOTA_SENTINEL="/tmp/claude-quota-exhausted"
 _CODEX_QUOTA_SENTINEL="/tmp/codex-quota-exhausted"
 
+# Remove a telemetry usage sidecar and clear its env exports. Called on every
+# non-success return/continue path so sidecars can never leak; the success
+# paths forward the sidecar to telemetry first and remove it themselves.
+_quota_discard_sidecar() {
+  [[ -n "${1:-}" ]] && rm -f "$1" 2>/dev/null
+  unset CHAIN_CLAUDE_USAGE_SIDECAR CHAIN_CODEX_USAGE_SIDECAR
+  return 0
+}
+
+# Preserve a kept-for-debugging failure log where per-run tmp cleanup can't
+# destroy it: move into $CHAIN_TRACE_DIR (runs/<phase>/trace — beside the
+# replay trace) when tracing is on; otherwise leave it in ${TMPDIR:-/tmp}.
+# Echoes the final path for the operator-facing "saved to" message.
+_quota_preserve_failure_log() {
+  local log="$1" label="${2:-cli-failure}"
+  if [[ -f "$log" && -n "${CHAIN_TRACE_DIR:-}" && -d "${CHAIN_TRACE_DIR:-}" && -w "${CHAIN_TRACE_DIR:-}" ]]; then
+    local dest="$CHAIN_TRACE_DIR/${label}-$(date +%Y%m%d%H%M%S)-$$.log"
+    if mv -- "$log" "$dest" 2>/dev/null; then
+      printf '%s\n' "$dest"
+      return 0
+    fi
+  fi
+  printf '%s\n' "$log"
+  return 0
+}
+
 # Resolve the runtime cap for the CURRENT agent (seconds; empty = caller keeps
 # its flat global). Shared by the headless timeout and the interactive inflight
 # check so both backends bound a hung agent the same way — a hung 20-minute
@@ -504,7 +534,7 @@ _claude_invoke() {
       _quota_run_pre_retry_hook
     fi
 
-    tmp_log=$(mktemp /tmp/claude-quota-XXXXXX.log)
+    tmp_log=$(mktemp "${TMPDIR:-/tmp}/claude-quota-XXXXXX.log")
 
     # Run claude, stream output to terminal AND capture to temp file.
     # PIPESTATUS[0] gives claude's exit code even through the pipe.
@@ -583,7 +613,7 @@ _claude_invoke() {
     if [[ "$CHAIN_TELEMETRY_TOKENS" == "true" ]]; then
       _renderer_path="$(dirname "${BASH_SOURCE[0]}")/claude_stream_renderer.py"
       if [[ -f "$_renderer_path" ]]; then
-        _sidecar=$(mktemp /tmp/claude-usage-XXXXXX.json)
+        _sidecar=$(mktemp "${TMPDIR:-/tmp}/claude-usage-XXXXXX.json")
         export CHAIN_CLAUDE_USAGE_SIDECAR="$_sidecar"
         _claude_extra_args+=(--output-format stream-json --verbose --include-partial-messages)
       else
@@ -644,6 +674,7 @@ _claude_invoke() {
           timeout_retry_count=$((timeout_retry_count + 1))
           echo "[quota-retry] $(date -Iseconds) Retrying in place (timeout retry $timeout_retry_count/${CHAIN_CLAUDE_TIMEOUT_RETRIES:-1})..." >&2
           rm -f "$tmp_log"
+          _quota_discard_sidecar "${_sidecar:-}"
           continue
         fi
         echo "[quota-retry] $(date -Iseconds) If artifacts were written before the hang, downstream steps can still proceed." >&2
@@ -690,6 +721,7 @@ _claude_invoke() {
       if [[ $stream_retry_count -gt $max_stream_retries ]]; then
         echo "[quota-retry] $(date -Iseconds) Stream-transient error persisted after $max_stream_retries retries. Giving up (exit $exit_code)." >&2
         rm -f "$tmp_log"
+        _quota_discard_sidecar "${_sidecar:-}"
         return "$exit_code"
       fi
       # Exponential-ish backoff: base * retry_count
@@ -697,6 +729,7 @@ _claude_invoke() {
       echo "[quota-retry] $(date -Iseconds) Transient stream failure detected (retry $stream_retry_count/$max_stream_retries). Sleeping ${stream_sleep}s before retry..." >&2
       sleep "$stream_sleep" || true
       rm -f "$tmp_log"
+      _quota_discard_sidecar "${_sidecar:-}"
       continue
     fi
 
@@ -715,11 +748,12 @@ _claude_invoke() {
         echo "─────────────────────────────────────────────────────────────────────" >&2
         tail -n 30 "$tmp_log" >&2
         echo "─────────────────────────────────────────────────────────────────────" >&2
-        echo "[quota-retry] $(date -Iseconds) Full output saved to: $tmp_log" >&2
+        echo "[quota-retry] $(date -Iseconds) Full output saved to: $(_quota_preserve_failure_log "$tmp_log" claude-failure)" >&2
         echo "════════════════════════════════════════════════════════════════════" >&2
       else
         rm -f "$tmp_log"
       fi
+      _quota_discard_sidecar "${_sidecar:-}"
       return "$exit_code"
     fi
 
@@ -733,8 +767,6 @@ _claude_invoke() {
     reset_str=$(_quota_extract_reset_string "$tmp_log")
     [[ -n "$reset_str" ]] && echo "[quota-retry] $(date -Iseconds) Reset indicator: '$reset_str'" >&2
 
-    echo "[quota-retry] $(date -Iseconds) Output saved to: $tmp_log" >&2
-
     # Long-duration limits (monthly / org-wide) cannot be retried in a few
     # hours — fail fast so the operator can rerun on the next billing window.
     # Without this branch, the loop burns CHAIN_CLAUDE_FALLBACK_SLEEP_SECONDS
@@ -744,17 +776,22 @@ _claude_invoke() {
       echo "[quota-retry] $(date -Iseconds) Long-duration limit detected (monthly/org). Skipping retry — limit will not reset in the retry window." >&2
       echo "[quota-retry] $(date -Iseconds) Re-run this step after the billing window resets." >&2
       rm -f "$tmp_log"
+      _quota_discard_sidecar "${_sidecar:-}"
       return $QUOTA_EXHAUSTED_EXIT_CODE
     fi
 
     if [[ "$CHAIN_DISABLE_AUTO_WAIT" == "true" ]]; then
       echo "[quota-retry] $(date -Iseconds) CHAIN_DISABLE_AUTO_WAIT=true — not retrying." >&2
+      echo "[quota-retry] $(date -Iseconds) Output saved to: $(_quota_preserve_failure_log "$tmp_log" claude-quota)" >&2
+      _quota_discard_sidecar "${_sidecar:-}"
       return $QUOTA_EXHAUSTED_EXIT_CODE
     fi
 
     retry_count=$((retry_count + 1))
     if [[ $retry_count -gt $max_retries ]]; then
       echo "[quota-retry] $(date -Iseconds) Max quota retries ($max_retries) reached. Giving up (exit $QUOTA_EXHAUSTED_EXIT_CODE)." >&2
+      echo "[quota-retry] $(date -Iseconds) Output saved to: $(_quota_preserve_failure_log "$tmp_log" claude-quota)" >&2
+      _quota_discard_sidecar "${_sidecar:-}"
       return $QUOTA_EXHAUSTED_EXIT_CODE
     fi
 
@@ -774,6 +811,12 @@ _claude_invoke() {
       echo "[quota-retry] $(date -Iseconds) Parsed reset time. Wake at: $wake_time (sleep ${sleep_secs}s incl. ${CHAIN_CLAUDE_RESET_BUFFER_SECONDS}s buffer)" >&2
     fi
 
+    # Reset time parsed — this attempt's log/sidecar are done with. Without
+    # this, every quota sleep leaked one claude-quota-*.log + usage sidecar
+    # (the loop re-mints both on the next attempt).
+    rm -f "$tmp_log"
+    _quota_discard_sidecar "${_sidecar:-}"
+
     # Write sentinel so other pipeline stages can coordinate
     local reset_epoch=$(( $(date +%s) + sleep_secs ))
     _quota_write_sentinel "$reset_epoch"
@@ -921,7 +964,7 @@ _codex_invoke() {
       rm -f "$_CODEX_QUOTA_SENTINEL"
     fi
 
-    tmp_log=$(mktemp /tmp/codex-quota-XXXXXX.log)
+    tmp_log=$(mktemp "${TMPDIR:-/tmp}/codex-quota-XXXXXX.log")
     local sleep_start
     sleep_start=$(date +%s)
 
@@ -942,7 +985,7 @@ _codex_invoke() {
     if [[ "$CHAIN_TELEMETRY_TOKENS" == "true" ]]; then
       _renderer_path="$(dirname "${BASH_SOURCE[0]}")/codex_stream_renderer.py"
       if [[ -f "$_renderer_path" ]]; then
-        _sidecar=$(mktemp /tmp/codex-usage-XXXXXX.json)
+        _sidecar=$(mktemp "${TMPDIR:-/tmp}/codex-usage-XXXXXX.json")
         export CHAIN_CODEX_USAGE_SIDECAR="$_sidecar"
         # Reuse the Claude env var name so telemetry.sh's existing helper picks it up
         export CHAIN_CLAUDE_USAGE_SIDECAR="$_sidecar"
@@ -1007,12 +1050,14 @@ _codex_invoke() {
       if [[ $stream_retry_count -gt $max_stream_retries ]]; then
         echo "[quota-retry/codex] Transient stream error persisted after $max_stream_retries retries. Giving up." >&2
         rm -f "$tmp_log"
+        _quota_discard_sidecar "${_sidecar:-}"
         return "$exit_code"
       fi
       local stream_sleep=$(( CHAIN_CODEX_STREAM_RETRY_SLEEP * stream_retry_count ))
       echo "[quota-retry/codex] Transient stream failure (retry $stream_retry_count/$max_stream_retries). Sleeping ${stream_sleep}s..." >&2
       sleep "$stream_sleep" || true
       rm -f "$tmp_log"
+      _quota_discard_sidecar "${_sidecar:-}"
       continue
     fi
 
@@ -1022,21 +1067,26 @@ _codex_invoke() {
         echo "[quota-retry/codex] $(date -Iseconds) *** Codex exited with code $exit_code (not quota) ***" >&2
         echo "[quota-retry/codex] Last 30 lines:" >&2
         tail -n 30 "$tmp_log" >&2
-        echo "[quota-retry/codex] Full output: $tmp_log" >&2
+        echo "[quota-retry/codex] Full output: $(_quota_preserve_failure_log "$tmp_log" codex-failure)" >&2
       else
         rm -f "$tmp_log"
       fi
+      _quota_discard_sidecar "${_sidecar:-}"
       return "$exit_code"
     fi
 
     # Quota exhaustion
     echo "[quota-retry/codex] $(date -Iseconds) *** CODEX QUOTA / RATE LIMIT DETECTED ***" >&2
     if [[ "$CHAIN_DISABLE_AUTO_WAIT" == "true" ]]; then
+      echo "[quota-retry/codex] Output saved to: $(_quota_preserve_failure_log "$tmp_log" codex-quota)" >&2
+      _quota_discard_sidecar "${_sidecar:-}"
       return $QUOTA_EXHAUSTED_EXIT_CODE
     fi
     retry_count=$((retry_count + 1))
     if [[ $retry_count -gt $max_retries ]]; then
       echo "[quota-retry/codex] Max quota retries ($max_retries) reached. Giving up." >&2
+      echo "[quota-retry/codex] Output saved to: $(_quota_preserve_failure_log "$tmp_log" codex-quota)" >&2
+      _quota_discard_sidecar "${_sidecar:-}"
       return $QUOTA_EXHAUSTED_EXIT_CODE
     fi
 
@@ -1049,6 +1099,11 @@ _codex_invoke() {
       echo "[quota-retry/codex] retry-after parsed: ${sleep_secs}s" >&2
     fi
 
+    # Retry-after parsed — this attempt's log/sidecar are done with (the loop
+    # re-mints both on the next attempt; without this every quota sleep leaked one).
+    rm -f "$tmp_log"
+    _quota_discard_sidecar "${_sidecar:-}"
+
     local reset_epoch=$(( $(date +%s) + sleep_secs ))
     echo "$reset_epoch" > "$_CODEX_QUOTA_SENTINEL"
     echo "[quota-retry/codex] Sleeping ${sleep_secs}s before retry ${retry_count}/${max_retries}..." >&2
diff --git a/incredible_auto_dev/scripts/automation/lib/retro_collect.sh b/incredible_auto_dev/scripts/automation/lib/retro_collect.sh
new file mode 100644
index 0000000..ae0c0bb
--- /dev/null
+++ b/incredible_auto_dev/scripts/automation/lib/retro_collect.sh
@@ -0,0 +1,276 @@
+#!/usr/bin/env bash
+# retro_collect.sh — deterministic session-retro evidence collector (EVO-2 slice a).
+#
+# Usage: retro_collect.sh <session-dir> <terminal-status>
+#
+# Freezes end-of-session evidence into <session-dir>/state/retro-input.md so the
+# retro drafting agent (EVO-2 slice b) can propose framework improvements from
+# ONE self-contained file. run-goal.sh's write_session_summary invokes this as a
+# subprocess on TERMINAL halts only (GOAL_ACHIEVED | STALLED | REGRESSION_HALT |
+# BUDGET_EXHAUSTED), guarded by CHAIN_SESSION_RETRO and non-blocking (`|| ...`).
+# Note: ABORT_MALFORMED halts arrive at that choke point as status "ABORTED"
+# (run-goal.sh halt switch), indistinguishable from Ctrl-C — so they do NOT get
+# a retro in slice (a).
+#
+# Contract:
+#   - Deterministic: pure read/format of existing artifacts. No model dispatch.
+#   - Every number cites a real source (telemetry.jsonl, session.json,
+#     state/*.md, iter-*/ markers). A counter with no reliable source is the
+#     literal `unknown (<why>)` — never a guess.
+#   - Missing inputs degrade to explicit "none recorded" lines; still exit 0.
+#   - Writes ONLY <session-dir>/state/retro-input.md; never mutates its inputs.
+#   - Exits nonzero only for unusable arguments (missing/invalid session dir).
+#
+# Section layout is a STABLE contract — slice (b)'s agent reads only this file.
+# Do not rename or reorder the `## ` headers without updating that consumer.
+
+set -uo pipefail
+
+SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
+
+SESSION_DIR="${1:-}"
+TERMINAL_STATUS="${2:-unknown}"
+
+if [[ -z "$SESSION_DIR" || ! -d "$SESSION_DIR" ]]; then
+  echo "[retro-collect] Usage: retro_collect.sh <session-dir> <terminal-status> (got: '${SESSION_DIR:-}')" >&2
+  exit 2
+fi
+
+TELEMETRY="$SESSION_DIR/telemetry.jsonl"
+SESSION_JSON="$SESSION_DIR/session.json"
+LESSONS_FILE="$SESSION_DIR/state/lessons.md"
+OUT="$SESSION_DIR/state/retro-input.md"
+mkdir -p "$SESSION_DIR/state"
+
+# Read one scalar field out of session.json; prints nothing when the file or
+# the key is absent (callers substitute their own `unknown (<why>)` text).
+_sj() {
+  python3 -c "
+import json, sys
+try:
+    v = json.load(open(sys.argv[1])).get(sys.argv[2])
+except Exception:
+    sys.exit(0)
+print('' if v is None else v)
+" "$SESSION_JSON" "$1" 2>/dev/null || true
+}
+
+_sid="$(_sj session_id)"
+[[ -z "$_sid" ]] && { _sid="$(basename "$SESSION_DIR")"; _sid="${_sid#goal-session-}"; }
+
+# ── Outcome fields ────────────────────────────────────────────────────────────
+_final_verdict="$(_sj last_verdict)"
+[[ -z "$_final_verdict" ]] && _final_verdict="unknown (last_verdict absent from session.json)"
+_iters="$(_sj total_iterations)"
+[[ -z "$_iters" ]] && _iters="$(_sj current_iter)"
+[[ -z "$_iters" ]] && _iters="unknown (total_iterations/current_iter absent from session.json)"
+_halted_at="$(_sj finished_at)"
+[[ -z "$_halted_at" ]] && _halted_at="unknown (finished_at absent from session.json)"
+
+# ── Verdict sequence ──────────────────────────────────────────────────────────
+# Primary source: telemetry iter_end events (FINAL post-gate verdicts).
+# Fallback: iter-*/.evaluated markers (raw pre-gate verdicts, labeled as such).
+_verdict_seq=""
+_verdict_src=""
+if [[ -f "$TELEMETRY" ]]; then
+  _verdict_seq="$(python3 -c "
+import json, sys
+out = []
+for raw in open(sys.argv[1], encoding='utf-8'):
+    raw = raw.strip()
+    if not raw:
+        continue
+    try:
+        e = json.loads(raw)
+    except Exception:
+        continue
+    if e.get('event') != 'iter_end':
+        continue
+    it = e.get('iter')
+    if it is None:
+        name = e.get('iter_name') or ''
+        it = name.rsplit('-', 1)[-1] if '-' in name else '?'
+    out.append(f\"iter {it}: {e.get('verdict', '?')}\")
+print('\n'.join(out))
+" "$TELEMETRY" 2>/dev/null || true)"
+  _verdict_src="telemetry iter_end events (final post-gate verdicts)"
+fi
+if [[ -z "$_verdict_seq" ]]; then
+  _verdict_seq="$(python3 -c "
+import glob, json, os, re, sys
+rows = []
+for p in glob.glob(os.path.join(sys.argv[1], 'iter-*', '.evaluated')):
+    try:
+        d = json.load(open(p))
+        rows.append((int(d.get('iter', -1)), d.get('verdict', '?')))
+    except Exception:
+        continue
+print('\n'.join(f'iter {i}: {v}' for i, v in sorted(rows)))
+" "$SESSION_DIR" 2>/dev/null || true)"
+  _verdict_src="iter-*/.evaluated markers (raw pre-gate verdicts)"
+fi
+if [[ -z "$_verdict_seq" ]]; then
+  _verdict_seq="none recorded (no iter_end events in telemetry.jsonl, no iter-*/.evaluated markers)"
+  _verdict_src="—"
+fi
+
+# ── Agent economics ───────────────────────────────────────────────────────────
+# From analyze_telemetry.py --json (claude_usage events). Rendered as a markdown
+# table; degrades to an explicit "none recorded" line.
+_econ_table="none recorded (telemetry.jsonl missing)"
+_wall_block="(per-step wall breakdown unavailable)"
+if [[ -f "$TELEMETRY" ]]; then
+  _econ_table="$(python3 "$SCRIPT_DIR/analyze_telemetry.py" --json "$TELEMETRY" 2>/dev/null | python3 -c "
+import json, sys
+try:
+    data = json.load(sys.stdin)
+except Exception:
+    data = {}
+rows = []
+for sid, s in data.items():
+    for agent, r in sorted((s.get('by_agent') or {}).items()):
+        rows.append((agent, r))
+    total = s.get('total')
+    if total:
+        rows.append(('TOTAL', total))
+if not rows:
+    sys.exit(0)
+print('| Agent | Invocations | Wall (s) | In tokens | Out tokens | Est. cost (USD) |')
+print('|---|---|---|---|---|---|')
+for agent, r in rows:
+    print('| {} | {} | {} | {} | {} | {:.4f} |'.format(
+        agent,
+        r.get('invocations', 0),
+        round(int(r.get('duration_ms', 0) or 0) / 1000),
+        r.get('gen_ai.usage.input_tokens', 0),
+        r.get('gen_ai.usage.output_tokens', 0),
+        float(r.get('gen_ai.usage.total_cost_usd', 0) or 0)))
+" 2>/dev/null || true)"
+  [[ -z "$_econ_table" ]] && _econ_table="none recorded (no claude_usage events in telemetry.jsonl — token telemetry may be off)"
+  _wall_block="$(python3 "$SCRIPT_DIR/analyze_telemetry.py" --wall "$TELEMETRY" 2>/dev/null || echo "(per-step wall breakdown unavailable)")"
+fi
+
+# ── Friction counters ─────────────────────────────────────────────────────────
+# Quota pauses: session.json quota_pause_count (written by write_session_summary
+# just before this collector runs); fallback to the raw counter file.
+_quota="$(_sj quota_pause_count)"
+if [[ -z "$_quota" ]]; then
+  _quota="$(cat "$SESSION_DIR/.quota-pause-count" 2>/dev/null || true)"
+fi
+[[ -z "$_quota" ]] && _quota="unknown (quota_pause_count absent from session.json and .quota-pause-count missing)"
+
+# Attempt-1 review FAILs: review_verdict telemetry events (goal-iter-lean.sh)
+# with attempt==1 and verdict==FAIL.
+_review_fails="unknown (telemetry.jsonl missing)"
+# Malformed verdicts: deterministic_gate events whose raw verdict is not a valid
+# token. The gates' .malformed-verdict-count file only tracks CONSECUTIVE
+# strikes and is reset on every well-formed verdict (lib/goal-gates.sh), so it
+# cannot serve as a session total.
+_malformed="unknown (telemetry.jsonl missing)"
+if [[ -f "$TELEMETRY" ]]; then
+  read -r _review_fails _malformed <<<"$(python3 -c "
+import json, sys
+VALID = {'GOAL_ACHIEVED', 'CONTINUE', 'ESCALATE', 'REGRESSION', 'STALLED'}
+review_fails = malformed = 0
+for raw in open(sys.argv[1], encoding='utf-8'):
+    raw = raw.strip()
+    if not raw:
+        continue
+    try:
+        e = json.loads(raw)
+    except Exception:
+        continue
+    ev = e.get('event')
+    if ev == 'review_verdict' and e.get('attempt') == 1 and e.get('verdict') == 'FAIL':
+        review_fails += 1
+    elif ev == 'deterministic_gate' and e.get('raw') not in VALID:
+        malformed += 1
+print(review_fails, malformed)
+" "$TELEMETRY" 2>/dev/null || echo "unknown unknown")"
+  [[ "$_review_fails" == "unknown" ]] && _review_fails="unknown (telemetry.jsonl unreadable)"
+  [[ "$_malformed" == "unknown" ]] && _malformed="unknown (telemetry.jsonl unreadable)"
+fi
+
+# ── Lessons tail ──────────────────────────────────────────────────────────────
+if [[ -s "$LESSONS_FILE" ]]; then
+  _lessons_tail="$(tail -n 20 "$LESSONS_FILE" 2>/dev/null || echo "none recorded (state/lessons.md unreadable)")"
+elif [[ -f "$LESSONS_FILE" ]]; then
+  _lessons_tail="none recorded (state/lessons.md is empty)"
+else
+  _lessons_tail="none recorded (state/lessons.md missing)"
+fi
+
+# ── Halt context ──────────────────────────────────────────────────────────────
+_halt_ctx="$(python3 -c "
+import json, sys
+try:
+    d = json.load(open(sys.argv[1]))
+except Exception:
+    print('none recorded (session.json missing or unreadable)')
+    sys.exit(0)
+ctx = {k: d.get(k) for k in ('status', 'last_verdict')}
+if 'parked_wip_sha' in d:
+    ctx['parked_wip_sha'] = d['parked_wip_sha']
+print(json.dumps(ctx, indent=2))
+" "$SESSION_JSON" 2>/dev/null || echo "none recorded (session.json missing or unreadable)")"
+
+# ── Assemble (single write; only file this script creates) ────────────────────
+cat > "$OUT" <<EOF
+# Retro input — session ${_sid}
+
+Deterministic end-of-session evidence snapshot (EVO-2 slice a). Generated by
+scripts/automation/lib/retro_collect.sh — no model wrote this. Counters marked
+\`unknown (<why>)\` had no reliable source; treat them as gaps, not zeros.
+
+## Outcome
+
+- **Terminal status:** ${TERMINAL_STATUS}
+- **Final verdict:** ${_final_verdict}
+- **Iterations used:** ${_iters}
+- **Halted at (UTC):** ${_halted_at}
+
+## Verdict sequence
+
+Source: ${_verdict_src}
+
+\`\`\`
+${_verdict_seq}
+\`\`\`
+
+## Agent economics
+
+Source: analyze_telemetry.py --json telemetry.jsonl (claude_usage events)
+
+${_econ_table}
+
+Per-step wall breakdown (analyze_telemetry.py --wall):
+
+\`\`\`
+${_wall_block}
+\`\`\`
+
+## Friction counters
+
+- **Quota pauses:** ${_quota} (source: session.json quota_pause_count / .quota-pause-count)
+- **Attempt-1 review FAILs:** ${_review_fails} (source: telemetry review_verdict events, attempt 1)
+- **Malformed-verdict rewrites:** ${_malformed} (source: telemetry deterministic_gate events with an invalid raw verdict; the gates' .malformed-verdict-count only tracks consecutive strikes)
+
+## Lessons tail
+
+Last 20 lines of state/lessons.md:
+
+\`\`\`
+${_lessons_tail}
+\`\`\`
+
+## Halt context
+
+session.json halt-relevant fields:
+
+\`\`\`json
+${_halt_ctx}
+\`\`\`
+EOF
+
+echo "[retro-collect] Wrote $OUT"
+exit 0
diff --git a/incredible_auto_dev/scripts/automation/qa-phase.sh b/incredible_auto_dev/scripts/automation/qa-phase.sh
index cd24b6d..e508dea 100755
--- a/incredible_auto_dev/scripts/automation/qa-phase.sh
+++ b/incredible_auto_dev/scripts/automation/qa-phase.sh
@@ -5,7 +5,8 @@
 # Self-bootstrapping: if services are not running, this script can start
 # them automatically using CHAIN_START_BACKEND_CMD / CHAIN_START_FRONTEND_CMD
 # env vars, or the conventional scripts/start-backend.sh and scripts/start-frontend.sh.
-# Logs for auto-started services are written to /tmp/qa-{backend,frontend}.log.
+# Logs for auto-started services are written via _qa_log_path (per-run
+# CHAIN_TMPDIR when set, else /tmp): <dir>/qa-{backend,frontend}-<port>.log.
 set -e
 
 SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
diff --git a/incredible_auto_dev/scripts/automation/run-benchmark.sh b/incredible_auto_dev/scripts/automation/run-benchmark.sh
new file mode 100755
index 0000000..fb4b18e
--- /dev/null
+++ b/incredible_auto_dev/scripts/automation/run-benchmark.sh
@@ -0,0 +1,541 @@
+#!/usr/bin/env bash
+# run-benchmark.sh — EVO-3 slice (b): spend-gated goal-mode benchmark runner.
+#
+# Copies the framework's documented subrepo set + the todo-app fixture into a
+# scratch git repo (with a LOCAL BARE origin, so the engine's GitHub preflight
+# and push-per-iter exercise their real code paths with zero network), runs
+# the goal engine there capped at 2 iterations, extracts a results JSON, and
+# keeps a pre-registered PRE/POST record in benchmarks/experiments.md.
+#
+# ── SPEND WARNING (ground rule G9) ────────────────────────────────────────────
+# A REAL benchmark run dispatches ~2 lean goal-mode iterations of a tiny app:
+# several HOURS of wall clock and order-of-DOLLARS of API spend. The script
+# always prints the plan + estimate first and REFUSES to run without
+# --yes-spend. It also REFUSES without --hypothesis: the PRE ledger entry is
+# written BEFORE the engine launches (G8 — prediction precedes execution).
+#
+# Usage:
+#   ./scripts/automation/run-benchmark.sh              # plan + estimate, refuse (exit 2)
+#   ./scripts/automation/run-benchmark.sh \
+#       --hypothesis '<one-line prediction>' [--predict '<expr>']... \
+#       --yes-spend [--keep-scratch] [--results-dir DIR] [--allow-dirty]
+#
+# Flags:
+#   --hypothesis STR   One-line prediction. REQUIRED to run (G8).
+#   --predict EXPR     Machine-checkable predicate over the scalar keys of the
+#                      results JSON's meta+outcome blocks; repeatable. Grammar:
+#                      KEY OP VALUE with OP one of == != >= <= > <  (e.g.
+#                      'journeys_passing_after>=3', 'final_status==STALLED').
+#                      All true → CONFIRMED, all false → REFUTED, anything
+#                      else (mix, unknown key, unknown value) → MIXED.
+#                      Without any --predict the POST verdict line is MANUAL —
+#                      the runner never self-grades a free-text hypothesis.
+#   --yes-spend        Actually run (G9: the user has approved the estimate).
+#   --keep-scratch     Keep the scratch workspace on success (it is always
+#                      kept when the engine exits nonzero or the runner fails).
+#   --results-dir DIR  Where the results JSON lands (default:
+#                      benchmarks/results/ in this repo; tests override).
+#   --allow-dirty      Run despite a dirty framework working tree, recording
+#                      framework_dirty:true + a diffstat line in the results.
+#                      Without it a dirty tree refuses: results attributed to
+#                      a sha the tree does not match are worthless. When the
+#                      dirt is a previous run's ledger/results, commit those
+#                      first instead.
+#
+# Exit codes:
+#   0  benchmark protocol completed — results JSON + POST ledger entry
+#      written. The ENGINE's exit code (possibly nonzero: a paused or halted
+#      engine is still a RESULT) is recorded inside the results JSON.
+#   2  refused (no --yes-spend / no --hypothesis / dirty tree) or usage error.
+#      Refusals fire BEFORE any side effect: no scratch, no ledger append,
+#      no results file.
+#   1  runner failure (assembly/extraction crashed); scratch kept, path printed.
+#
+# ── TEST SEAM (CHAIN_BENCH_ENGINE_CMD) ────────────────────────────────────────
+# When CHAIN_BENCH_ENGINE_CMD is set, it is run (bash -c, cwd=scratch, with
+# CHAIN_AGENT_BACKEND=claude and CHAIN_BENCH_SESSION_ID /
+# CHAIN_BENCH_MAX_ITER exported) INSTEAD of the real
+# `run-goal.sh --session-id <sid> --max-iter 2`. This exists ONLY so the
+# offline suite (tests/automation/test-benchmark-runner.sh) can drive stub
+# engines. The spend/hypothesis/dirty gates sit UPSTREAM of the seam, so it
+# cannot be used to dodge them (G5) — and the seam value lands in the results
+# JSON's chain_env block, so a stubbed run is visibly stubbed.
+#
+# Scratch workspace layout (mktemp -d under $TMPDIR):
+#   <work>/scratch             framework subrepo set (.claude/ scripts/ config/
+#                              templates/ CLAUDE.md [+ .mcp.json]) + fixture
+#                              overlay (fixture files WIN collisions — its
+#                              .claude/project-template.md replaces the
+#                              framework placeholder), fresh git repo on main
+#                              (deterministic author), origin = local bare repo
+#   <work>/scratch-origin.git  the local bare origin (satisfies the engine's
+#                              ls-remote preflight + per-iter push, no network)
+#   <work>/engine.log          engine stdout/stderr (also streamed live)
+#
+# Ledger format contract (grep-able): PRE entries start `## PRE <session-id>`,
+# POST entries start `## POST <session-id>` — pinned by the test suite.
+set -euo pipefail
+
+REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
+LIB="$REPO_ROOT/scripts/automation/lib"
+FIXTURE="$REPO_ROOT/benchmarks/fixtures/todo-app"
+LEDGER="$REPO_ROOT/benchmarks/experiments.md"
+
+log() { echo "[benchmark] $*"; }
+
+# ── Arguments ─────────────────────────────────────────────────────────────────
+YES_SPEND=false
+KEEP_SCRATCH=false
+ALLOW_DIRTY=false
+HYPOTHESIS=""
+RESULTS_DIR="$REPO_ROOT/benchmarks/results"
+declare -a PREDICTS=()
+while [[ $# -gt 0 ]]; do
+  case "$1" in
+    --yes-spend)    YES_SPEND=true ;;
+    --keep-scratch) KEEP_SCRATCH=true ;;
+    --allow-dirty)  ALLOW_DIRTY=true ;;
+    --hypothesis)
+      [[ -n "${2:-}" ]] || { echo "--hypothesis needs a value" >&2; exit 2; }
+      HYPOTHESIS="$2"; shift ;;
+    --predict)
+      [[ -n "${2:-}" ]] || { echo "--predict needs a value" >&2; exit 2; }
+      PREDICTS+=("$2"); shift ;;
+    --results-dir)
+      [[ -n "${2:-}" ]] || { echo "--results-dir needs a value" >&2; exit 2; }
+      RESULTS_DIR="$2"; shift ;;
+    -h|--help) grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
+    *) echo "unknown flag: $1 (see --help)" >&2; exit 2 ;;
+  esac
+  shift
+done
+
+FRAMEWORK_SHA="$(git -C "$REPO_ROOT" rev-parse HEAD 2>/dev/null || echo "unknown (not a git repo)")"
+
+# ── Plan + estimate (always printed — the G9 confirmation surface) ────────────
+cat <<PLAN
+[benchmark] plan:
+  fixture:    benchmarks/fixtures/todo-app  (copied with the framework subrepo set into a scratch repo)
+  engine:     run-goal.sh --session-id bench-<UTCdate-hhmm> --max-iter 2  (headless; local bare origin)
+  framework:  sha ${FRAMEWORK_SHA}
+  records:    results JSON under ${RESULTS_DIR} + PRE/POST entries in benchmarks/experiments.md
+  estimate:   ~2 lean goal-mode iterations of a tiny app — several HOURS wall clock,
+              order-of-DOLLARS API spend (rough ±3x; every dispatched agent bills real tokens)
+PLAN
+
+# ── Refusal gates — all BEFORE any side effect ────────────────────────────────
+if ! $YES_SPEND; then
+  echo
+  echo "[benchmark] REFUSING to run: a benchmark run spends real API tokens (ground rule G9)."
+  echo "            Re-run with --yes-spend after the user has approved the estimate above,"
+  echo "            plus --hypothesis '<one-line prediction>' (G8)."
+  exit 2
+fi
+if [[ -z "$HYPOTHESIS" ]]; then
+  echo
+  echo "[benchmark] REFUSING to run: no --hypothesis given. Prediction precedes execution"
+  echo "            (ground rule G8): the PRE entry in benchmarks/experiments.md is written"
+  echo "            BEFORE the engine launches, and it needs your one-line prediction."
+  exit 2
+fi
+DIRTY=false
+DIFFSTAT=""
+_porcelain="$(git -C "$REPO_ROOT" status --porcelain 2>/dev/null || true)"
+if [[ -n "$_porcelain" ]]; then
+  if ! $ALLOW_DIRTY; then
+    echo
+    echo "[benchmark] REFUSING to run: the framework working tree is dirty — results would be"
+    echo "            attributed to sha ${FRAMEWORK_SHA}, which the tree does not match."
+    echo "            Commit first (including any previous run's ledger/results), or pass"
+    echo "            --allow-dirty to run anyway with framework_dirty:true recorded."
+    exit 2
+  fi
+  DIRTY=true
+  _stat="$(git -C "$REPO_ROOT" diff HEAD --stat 2>/dev/null | tail -n1 | sed 's/^ *//')"
+  _untracked="$(grep -c '^??' <<<"$_porcelain" || true)"
+  DIFFSTAT="${_stat:-no tracked changes}; ${_untracked} untracked path(s)"
+  log "WARNING: running on a dirty tree (--allow-dirty): $DIFFSTAT"
+fi
+if [[ ! -d "$FIXTURE" ]]; then
+  echo "[benchmark] fixture missing: $FIXTURE — broken checkout?" >&2
+  exit 1
+fi
+
+# ── Side effects begin: pre-registration, then scratch assembly ───────────────
+SESSION_ID="bench-$(date -u +%Y%m%d-%H%M)"
+NOW_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
+log "session: $SESSION_ID (framework sha ${FRAMEWORK_SHA})"
+
+if [[ ! -f "$LEDGER" ]]; then
+  # Normally committed with the framework; recreate a minimal header if absent
+  # so the append-only record never silently lands nowhere.
+  mkdir -p "$(dirname "$LEDGER")"
+  {
+    echo "# Benchmark experiments ledger (EVO-3)"
+    echo
+    echo "**APPEND-ONLY.** (Header auto-recreated by run-benchmark.sh — the committed"
+    echo "version in the framework repo carries the full entry-format contract.)"
+    echo
+    echo "<!-- entries are appended below this line — do not edit anything beneath it -->"
+  } > "$LEDGER"
+  log "ledger was missing — recreated header: $LEDGER"
+fi
+{
+  printf -- '\n---\n\n'
+  printf '## PRE %s · %s\n' "$SESSION_ID" "$NOW_UTC"
+  printf -- '- framework-sha: %s (dirty: %s)\n' "$FRAMEWORK_SHA" "$DIRTY"
+  if [[ "$DIRTY" == "true" ]]; then
+    printf -- '- framework-diffstat: %s\n' "$DIFFSTAT"
+  fi
+  printf -- '- fixture: todo-app · max-iter 2\n'
+  printf -- '- hypothesis: %s\n' "$HYPOTHESIS"
+  if [[ ${#PREDICTS[@]} -gt 0 ]]; then
+    printf -- '- metrics + prediction (mechanical --predict): %s\n' "$(IFS=';'; echo "${PREDICTS[*]}")"
+  else
+    printf -- '- metrics + prediction: stated in the hypothesis (free text — POST verdict will be MANUAL)\n'
+  fi
+} >> "$LEDGER"
+log "PRE entry appended to benchmarks/experiments.md (prediction registered before execution)"
+
+WORK="$(mktemp -d "${TMPDIR:-/tmp}/bench-${SESSION_ID}.XXXXXX")"
+SCRATCH="$WORK/scratch"
+ORIGIN="$WORK/scratch-origin.git"
+# From here on, any runner failure keeps the scratch for forensics.
+trap '_rc=$?; if [[ $_rc -ne 0 ]]; then echo "[benchmark] FAILED (rc=$_rc) — scratch workspace kept for forensics: '"$WORK"'" >&2; fi' EXIT
+mkdir -p "$SCRATCH"
+log "scratch workspace: $WORK"
+
+# Framework subrepo set (README "Subrepo Usage"): .claude/ scripts/ config/
+# templates/ + CLAUDE.md (+ .mcp.json when present). Deliberately NOT copied:
+# .git, runs/, reports/, docs/, tests/, benchmarks/ (recursion!), and the
+# neutral sources (agents/ skills/ commands/ hooks/ policy/) — the runtime
+# reads the rendered .claude/ tree.
+for d in .claude scripts config templates; do
+  if [[ ! -d "$REPO_ROOT/$d" ]]; then
+    echo "[benchmark] framework dir missing from subrepo set: $d" >&2
+    exit 1
+  fi
+  cp -a "$REPO_ROOT/$d" "$SCRATCH/"
+done
+cp "$REPO_ROOT/CLAUDE.md" "$SCRATCH/"
+if [[ -f "$REPO_ROOT/.mcp.json" ]]; then
+  cp "$REPO_ROOT/.mcp.json" "$SCRATCH/"
+fi
+
+# Fixture overlay — fixture files WIN collisions (tar extract overwrites), so
+# the fixture's filled .claude/project-template.md replaces the framework
+# placeholder and its docs/goal.md becomes the scratch goal file. Runtime dirs
+# (.venv/ __pycache__/ .pytest_cache/) and the runtime store (todos.json) are
+# never part of the benchmark input.
+( cd "$FIXTURE" \
+  && tar --exclude='.venv' --exclude='__pycache__' --exclude='.pytest_cache' \
+         --exclude='todos.json' -cf - . ) \
+  | ( cd "$SCRATCH" && tar -xf - )
+
+git -C "$SCRATCH" init -q -b main
+git -C "$SCRATCH" add -A
+git -C "$SCRATCH" -c user.name="goal-chain" -c user.email="goal-chain@localhost" \
+  commit -q -m "chore(bench): scratch assembly — framework @ ${FRAMEWORK_SHA:0:12} + todo-app fixture"
+git init -q --bare "$ORIGIN"
+git -C "$SCRATCH" remote add origin "$ORIGIN"
+log "scratch repo ready (1 commit on main; origin = local bare $ORIGIN)"
+
+# ── Engine launch ─────────────────────────────────────────────────────────────
+# Environment honesty: everything CHAIN_* in the engine's environment is
+# recorded in the results JSON — results are only comparable when config is
+# visible. The exports below are part of that environment on purpose.
+# "claude" IS the headless dispatch backend (quota-retry.sh accepts
+# interactive|claude|codex only); pinning it keeps a production pump's
+# CHAIN_AGENT_BACKEND=interactive from leaking into the benchmark engine.
+export CHAIN_AGENT_BACKEND=claude
+export CHAIN_BENCH_SESSION_ID="$SESSION_ID"
+export CHAIN_BENCH_MAX_ITER=2
+CHAIN_ENV_LINES="$(env | LC_ALL=C sort | grep '^CHAIN_' || true)"
+
+ENGINE_LOG="$WORK/engine.log"
+ENGINE_RC=0
+_t0="$(date +%s)"
+if [[ -n "${CHAIN_BENCH_ENGINE_CMD:-}" ]]; then
+  log "TEST SEAM active — running CHAIN_BENCH_ENGINE_CMD instead of run-goal.sh (recorded in results)"
+  ( cd "$SCRATCH" && bash -c "$CHAIN_BENCH_ENGINE_CMD" ) 2>&1 | tee "$ENGINE_LOG" || ENGINE_RC=$?
+else
+  log "launching engine: run-goal.sh --session-id $SESSION_ID --max-iter 2 (headless)"
+  ( cd "$SCRATCH" && bash scripts/automation/run-goal.sh --session-id "$SESSION_ID" --max-iter 2 ) \
+    2>&1 | tee "$ENGINE_LOG" || ENGINE_RC=$?
+fi
+_t1="$(date +%s)"
+WALL_SECONDS=$(( _t1 - _t0 ))
+log "engine exit code: $ENGINE_RC (a nonzero/paused engine is a RESULT, recorded as such)"
+
+# ── Results extraction ────────────────────────────────────────────────────────
+if [[ -f "$REPO_ROOT/config/model-tiers.yaml" ]]; then
+  TIERS_SHA256="$(sha256sum "$REPO_ROOT/config/model-tiers.yaml" | awk '{print $1}')"
+else
+  TIERS_SHA256="unknown (config/model-tiers.yaml missing)"
+fi
+TELEMETRY="$SCRATCH/runs/goal-session-$SESSION_ID/telemetry.jsonl"
+if [[ -f "$TELEMETRY" ]]; then
+  AGENTS_JSON="$(python3 "$LIB/analyze_telemetry.py" --json "$TELEMETRY")"
+  TELEMETRY_MISSING=""
+else
+  AGENTS_JSON='{}'
+  TELEMETRY_MISSING="telemetry.jsonl missing"
+fi
+
+case "$FRAMEWORK_SHA" in
+  *" "*) _sha12="nosha" ;;
+  *)     _sha12="${FRAMEWORK_SHA:0:12}" ;;
+esac
+mkdir -p "$RESULTS_DIR"
+RESULTS_FILE="$RESULTS_DIR/$(date -u +%Y%m%d-%H%M%S)-${_sha12}.json"
+
+_predicts=""
+if [[ ${#PREDICTS[@]} -gt 0 ]]; then
+  _predicts="$(printf '%s\n' "${PREDICTS[@]}")"
+fi
+
+# One python pass builds + validates the results JSON, evaluates the --predict
+# predicates, and appends the POST ledger entry. Everything crosses via env —
+# no shell interpolation into code.
+BENCH_RESULTS_FILE="$RESULTS_FILE" \
+BENCH_REPO_ROOT="$REPO_ROOT" \
+BENCH_SCRATCH="$SCRATCH" \
+BENCH_LEDGER="$LEDGER" \
+BENCH_SESSION_ID="$SESSION_ID" \
+BENCH_DATE_UTC="$NOW_UTC" \
+BENCH_FRAMEWORK_SHA="$FRAMEWORK_SHA" \
+BENCH_DIRTY="$DIRTY" \
+BENCH_DIFFSTAT="$DIFFSTAT" \
+BENCH_HYPOTHESIS="$HYPOTHESIS" \
+BENCH_PREDICTS="$_predicts" \
+BENCH_CHAIN_ENV="$CHAIN_ENV_LINES" \
+BENCH_TIERS_SHA256="$TIERS_SHA256" \
+BENCH_ENGINE_RC="$ENGINE_RC" \
+BENCH_WALL_SECONDS="$WALL_SECONDS" \
+BENCH_MAX_ITER=2 \
+BENCH_AGENTS_JSON="$AGENTS_JSON" \
+BENCH_TELEMETRY_MISSING="$TELEMETRY_MISSING" \
+python3 - <<'PYEOF'
+import json
+import os
+import sys
+import time
+
+env = os.environ
+sid = env["BENCH_SESSION_ID"]
+scratch = env["BENCH_SCRATCH"]
+repo_root = env["BENCH_REPO_ROOT"]
+sess_dir = os.path.join(scratch, "runs", f"goal-session-{sid}")
+
+def unknown(why):
+    return f"unknown ({why})"
+
+# outcome — session.json
+final_status = last_verdict = iterations_used = unknown("scratch session.json missing")
+session_path = os.path.join(sess_dir, "session.json")
+if os.path.isfile(session_path):
+    try:
+        s = json.load(open(session_path, encoding="utf-8"))
+    except Exception:
+        s = None
+        final_status = last_verdict = iterations_used = unknown("scratch session.json unreadable")
+    if isinstance(s, dict):
+        final_status = s.get("status") if s.get("status") is not None else unknown("status absent from session.json")
+        last_verdict = s.get("last_verdict") if s.get("last_verdict") is not None else unknown("last_verdict null/absent in session.json")
+        iterations_used = s.get("current_iter") if isinstance(s.get("current_iter"), int) else unknown("current_iter absent from session.json")
+
+# outcome — journey-history.json ({"journeys": {id: {"status": ...}}};
+# passing statuses per lib/goal_gate.py PASSING_STATUSES)
+journeys_passing = journeys_total = unknown("journey-history.json missing")
+jh_path = os.path.join(sess_dir, "state", "journey-history.json")
+if os.path.isfile(jh_path):
+    try:
+        jh = json.load(open(jh_path, encoding="utf-8"))
+        journeys = jh.get("journeys")
+        if isinstance(journeys, dict):
+            journeys_total = len(journeys)
+            journeys_passing = sum(
+                1 for j in journeys.values()
+                if isinstance(j, dict) and j.get("status") in {"passing", "already_passing"}
+            )
+        else:
+            journeys_passing = journeys_total = unknown("journeys key malformed in journey-history.json")
+    except Exception:
+        journeys_passing = journeys_total = unknown("journey-history.json unreadable")
+
+# outcome — telemetry counters (mirrors lib/retro_collect.sh semantics)
+VALID = {"GOAL_ACHIEVED", "CONTINUE", "ESCALATE", "REGRESSION", "STALLED"}
+attempt1_review_fails = malformed_verdicts = unknown("telemetry.jsonl missing")
+tel_path = os.path.join(sess_dir, "telemetry.jsonl")
+if os.path.isfile(tel_path):
+    rf = mf = 0
+    try:
+        for raw in open(tel_path, encoding="utf-8"):
+            raw = raw.strip()
+            if not raw:
+                continue
+            try:
+                e = json.loads(raw)
+            except Exception:
+                continue
+            ev = e.get("event")
+            if ev == "review_verdict" and e.get("attempt") == 1 and e.get("verdict") == "FAIL":
+                rf += 1
+            elif ev == "deterministic_gate" and e.get("raw") not in VALID:
+                mf += 1
+        attempt1_review_fails, malformed_verdicts = rf, mf
+    except Exception:
+        attempt1_review_fails = malformed_verdicts = unknown("telemetry.jsonl unreadable")
+
+chain_env = {}
+for line in env["BENCH_CHAIN_ENV"].splitlines():
+    if "=" in line:
+        k, v = line.split("=", 1)
+        chain_env[k] = v
... [diff_bound] incredible_auto_dev/scripts/automation/run-benchmark.sh: 147 more diff lines omitted — Read the file for full detail
diff --git a/incredible_auto_dev/scripts/automation/run-evals.sh b/incredible_auto_dev/scripts/automation/run-evals.sh
index 3083bb6..62bff03 100755
--- a/incredible_auto_dev/scripts/automation/run-evals.sh
+++ b/incredible_auto_dev/scripts/automation/run-evals.sh
@@ -119,6 +119,15 @@ else
   _fail "self-test: common.sh (kill-tree / self-heal)"
 fi
 
+# Per-run tmp isolation helpers: init/adopt, owner-guarded cleanup, rotate, and
+# the age+pid-liveness janitor (incl. never-touch-the-quota-sentinels).
+if bash scripts/automation/lib/chain-tmp.sh self-test >/dev/null 2>&1; then
+  _pass "self-test: chain-tmp.sh (tmpdir init/cleanup/rotate/janitor)"
+else
+  bash scripts/automation/lib/chain-tmp.sh self-test || true
+  _fail "self-test: chain-tmp.sh"
+fi
+
 # Parallel two-branch runner (previously had a self-test that nothing invoked).
 if bash scripts/automation/lib/parallel.sh self-test >/dev/null 2>&1; then
   _pass "self-test: parallel.sh"
@@ -138,6 +147,8 @@ _run_self_test scripts/automation/lib/goal_gate.py self-test
 _run_self_test scripts/automation/lib/goal_lint.py self-test
 _run_self_test scripts/automation/lib/scan_diff.py self-test
 _run_self_test scripts/automation/lib/diff_bound.py self-test
+# Benchmark results comparator (EVO-3): delta table + REGRESS/OK/UNKNOWN verdict.
+_run_self_test scripts/automation/lib/benchmark_compare.py --self-test
 if bash scripts/automation/lib/goal-gates.sh --self-test >/dev/null 2>&1; then
   _pass "self-test: goal-gates.sh (verdict gates + two-key confirm, stubbed dispatch)"
 else
@@ -147,7 +158,7 @@ fi
 
 # ── 2c. Standalone unit-test scripts (API-free by design) ────────────────────
 _log "2c. tests/automation unit tests"
-for _t in tests/automation/test-quota-retry.sh tests/automation/test-install-gate.sh tests/automation/test-goal-checkpoints.sh tests/automation/test-goal-async-tail.sh tests/automation/test-intent-checkpoint.sh tests/automation/test-doc-drift.sh tests/automation/test-github-preflight.sh; do
+for _t in tests/automation/test-quota-retry.sh tests/automation/test-install-gate.sh tests/automation/test-goal-checkpoints.sh tests/automation/test-goal-async-tail.sh tests/automation/test-intent-checkpoint.sh tests/automation/test-doc-drift.sh tests/automation/test-github-preflight.sh tests/automation/test-tmp-cleanup.sh tests/automation/test-goal-retro.sh tests/automation/test-benchmark-runner.sh; do
   if bash "$_t" >/dev/null 2>&1; then
     _pass "unit: $_t"
   else
@@ -167,6 +178,19 @@ if bash .claude/hooks/guard-dangerous-commands.sh "rm -rf /" >/dev/null 2>&1; th
 else
   _pass "hook: guard-dangerous-commands blocks 'rm -rf /'"
 fi
+# Regression guard for the /tmp rm ban: the old fixed-substring "rm -rf /"
+# pattern matched EVERY absolute-path rm — on the Codex backend (where this
+# hook is the real gate) that banned the allow-listed /tmp cleanup outright.
+if bash .claude/hooks/guard-dangerous-commands.sh "rm -rf /tmp/pytest-of-user/pytest-1" >/dev/null 2>&1; then
+  _pass "hook: guard-dangerous-commands allows /tmp cleanup (rm-ban regression)"
+else
+  _fail "hook: guard-dangerous-commands wrongly blocks /tmp cleanup (rm-ban regression)"
+fi
+if bash .claude/hooks/guard-dangerous-commands.sh "cd /x && rm -rf /etc" >/dev/null 2>&1; then
+  _fail "hook: guard-dangerous-commands FAILED to block chained 'rm -rf /etc'"
+else
+  _pass "hook: guard-dangerous-commands blocks chained 'rm -rf /etc'"
+fi
 _lint_tmp=$(mktemp /tmp/eval-lint-XXXX.py); echo "x = 1" > "$_lint_tmp"
 if bash .claude/hooks/post-edit-lint.sh "$_lint_tmp" >/dev/null 2>&1; then
   _pass "hook: post-edit-lint accepts a valid .py file"
diff --git a/incredible_auto_dev/scripts/automation/run-goal.sh b/incredible_auto_dev/scripts/automation/run-goal.sh
index 9c770a4..ac8c683 100755
--- a/incredible_auto_dev/scripts/automation/run-goal.sh
+++ b/incredible_auto_dev/scripts/automation/run-goal.sh
@@ -318,6 +318,51 @@ When finished, STOP." \
   record_agent_invocation_end "iteration-summarizer" "$_sum_start" "$_sum_rc"
 }
 
+# Run the retro-analyst agent at a terminal session halt (EVO-2 slice b).
+# Reads ONLY state/retro-input.md (the collector's frozen digest) and drafts
+# reports/goal-session-<sid>-retro.md — 1-5 candidate framework-improvement
+# proposals for human triage. Non-blocking showcase-class step: a failed or
+# skipped dispatch never changes halt behavior or an engine exit code. The
+# caller (write_session_summary) gates on CHAIN_SESSION_RETRO + the terminal-
+# status filter; this function additionally requires the digest to exist so
+# the agent can never dispatch without its single input.
+_run_retro_analyst() {
+  local agent_file="$REPO_ROOT/.claude/agents/retro-analyst.md"
+  local retro_input="$GOAL_SESSION_DIR_LOCAL/state/retro-input.md"
+  local retro_report="$REPO_ROOT/reports/goal-session-${SESSION_ID}-retro.md"
+  [[ -f "$agent_file" ]] || { echo "[run-goal] Warning: retro-analyst agent missing, skipping retro draft"; return 0; }
+  [[ -f "$retro_input" ]] || { echo "[run-goal] Warning: no retro-input.md (collector failed or skipped) — retro-analyst not dispatched."; return 0; }
+  mkdir -p "$REPO_ROOT/reports"
+
+  cd "$REPO_ROOT"
+  # record_* pair (not a bare export): attributes telemetry/trace to this agent
+  # and clears CHAIN_CURRENT_AGENT afterwards so attribution can't bleed into
+  # later inline calls.
+  record_agent_invocation_start "retro-analyst"
+  local _retro_start=$CHAIN_AGENT_START_EPOCH
+  local _retro_rc=0
+  claude_with_quota_retry -p "You are the retro-analyst agent.
+
+Session ID: $SESSION_ID
+Retro input (your ONLY input file): $retro_input
+Output path (the retro report): $retro_report
+Agent instructions: .claude/agents/retro-analyst.md  <-- read this first
+(CLAUDE.md is already in your system prompt -- do not Read it again.)
+
+Apply the TOKEN AND QUESTIONING POLICY from .claude/core.md strictly.
+
+Read the retro input file and NOTHING else. Draft at most 5 candidate
+framework-improvement items per your agent instructions — proposals only,
+each citing its exact evidence line from the retro input; zero items is a
+valid outcome. Never edit docs/improvement-roadmap.md or any other file.
+
+Write the report to: $retro_report
+
+Write the report and STOP." \
+    || { _retro_rc=$?; echo "[run-goal] Warning: retro-analyst dispatch failed (non-blocking) — no retro report." >&2; }
+  record_agent_invocation_end "retro-analyst" "$_retro_start" "$_retro_rc"
+}
+
 # Maintain the PROJECT's README.md so it always reflects current capabilities and
 # carries a How-to-run section. Non-blocking — failures only log. Runs every
 # iteration in goal mode (headless or interactive). The agent edits only
@@ -1209,6 +1254,24 @@ $(python3 "$SCRIPT_DIR/lib/analyze_telemetry.py" --wall "$GOAL_SESSION_DIR_LOCAL
 EOF
   record_telemetry_event "session_end" "$(jq -cn --arg fv "$final_verdict" --argjson ti $total_iterations --argjson wt $wall_time --argjson qp $quota_pauses '{final_verdict:$fv, total_iterations:$ti, wall_time_seconds:$wt, quota_pause_count:$qp}' 2>/dev/null || printf '{"final_verdict":"%s","total_iterations":%d}' "$final_verdict" "$total_iterations")"
   echo "[run-goal] Session summary: $SUMMARY_FILE"
+  # Session retro (EVO-2 slice a): freeze a deterministic evidence snapshot
+  # (state/retro-input.md) for the retro drafting agent on TERMINAL halts only.
+  # Resumable pauses (AWAITING_*, GATE_BLOCKED) and ABORTED — which is also how
+  # an ABORT_MALFORMED halt arrives here (the halt switch passes "ABORTED") —
+  # produce nothing. Non-blocking: a broken collector must never change halt
+  # behavior or an engine exit code. Disable with CHAIN_SESSION_RETRO=false.
+  if [[ "${CHAIN_SESSION_RETRO:-true}" != "false" ]]; then
+    case "$final_verdict" in
+      GOAL_ACHIEVED|STALLED|REGRESSION_HALT|BUDGET_EXHAUSTED)
+        bash "$SCRIPT_DIR/lib/retro_collect.sh" "$GOAL_SESSION_DIR_LOCAL" "$final_verdict" \
+          || echo "[run-goal] Warning: session retro collector failed (non-blocking) — no retro-input.md." >&2
+        # EVO-2 slice (b): draft improvement proposals from the frozen digest.
+        # Same knob + terminal filter as the collector; the wrapper itself
+        # refuses to dispatch when retro-input.md is absent (collector failed).
+        _run_retro_analyst
+        ;;
+    esac
+  fi
   _render_session_index_html
   local _idx_html="$REPO_ROOT/reports/goal-session-${SESSION_ID}-index.html"
   [[ -f "$_idx_html" ]] && echo "[run-goal] Session HTML: file://$_idx_html"
@@ -1219,7 +1282,15 @@ EOF
 # not available to a later /goal-pause). Cleaned up on any exit, including the
 # on_abort path below (which exits 130 → the EXIT trap fires).
 echo "$$" > "$ENGINE_PID_FILE" 2>/dev/null || true
-trap '_join_showcase_tail --kill 2>/dev/null; rm -f "$ENGINE_PID_FILE" 2>/dev/null || true' EXIT
+# Composed EXIT trap (single trap owner — never add a second `trap … EXIT`, it
+# would silently drop earlier cleanup): join/kill the showcase tail FIRST so
+# nothing is still writing into the tmp dir, then remove pid file + tmp dir.
+_goal_engine_on_exit() {
+  _join_showcase_tail --kill 2>/dev/null || true
+  rm -f "$ENGINE_PID_FILE" 2>/dev/null || true
+  chain_tmp_cleanup
+}
+trap _goal_engine_on_exit EXIT
 
 # Trap: on SIGINT/SIGTERM, write ABORTED summary. Kill the background showcase
 # tail FIRST so Ctrl-C never blocks on a non-gating summary/README agent.
@@ -1231,6 +1302,12 @@ on_abort() {
 }
 trap on_abort INT TERM
 
+# Per-run tmp isolation (lib/chain-tmp.sh): one session-scoped dir now (covers
+# the baseline + the first decomposer); the loop rotates to a per-iteration dir
+# at each iteration boundary below. Janitor sweeps strays from crashed runs.
+chain_tmp_init "goal-${SESSION_ID}"
+chain_tmp_janitor
+
 # Verify we can push to GitHub before the loop starts (once; fresh + resume).
 # Fails fast / pauses here rather than stalling on a credential prompt mid-run.
 preflight_github_access
@@ -1601,6 +1678,16 @@ Do NOT write code or implement anything. The iteration spec and any blueprint ed
   # ~6-13 min saving comes from.
   _join_showcase_tail
 
+  # Tmp hygiene boundary — the per-iteration cleanup step. The previous
+  # iteration's background showcase tail has just been joined (its demo
+  # services killed), so nothing is writing to the previous tmp dir any more.
+  # Clear it and start this iteration's own dir — one call site covers BOTH
+  # the lean and full dispatch paths below. (Do NOT clean right after the
+  # evaluator: the async showcase tail forked at step 4c still writes there.)
+  _prev_tmp="${CHAIN_TMPDIR:-}"
+  chain_tmp_rotate "$ITER_NAME"
+  echo "[run-goal] Tmp cleanup: cleared ${_prev_tmp:-(none)} — iteration tmp dir: ${CHAIN_TMPDIR:-(disabled)}"
+
   # 3. Dispatch. Reset the per-iteration exit code first: _exec_rc is a plain
   # shell var, so a stale 70 from a prior iteration would otherwise survive into
   # this one (the `:-0` default only fills an UNSET var) and mis-fire the
diff --git a/incredible_auto_dev/scripts/automation/run-judgment-evals.sh b/incredible_auto_dev/scripts/automation/run-judgment-evals.sh
new file mode 100755
index 0000000..be998af
--- /dev/null
+++ b/incredible_auto_dev/scripts/automation/run-judgment-evals.sh
@@ -0,0 +1,549 @@
+#!/usr/bin/env bash
+# run-judgment-evals.sh — REL-1 judgment eval runner (golden verdict cases).
+#
+# Dispatches each frozen fixture under tests/judgment/<judge>/case-*/ to the
+# CURRENTLY CONFIGURED judge model at its configured effort and compares the
+# verdict CLASS it emits against the case's expected.txt. Wording is never
+# compared — only the class. This is the harness's defense against silent judge
+# regression (a weaker or retuned judge emitting plausible-but-wrong verdicts).
+#
+# ── SPEND WARNING (ground rule G9) ────────────────────────────────────────────
+# Every case is a real strong-tier agent dispatch that costs real API tokens.
+# The script REFUSES to run without an explicit --yes-spend flag, and always
+# prints a cost estimate first. It is deliberately NOT registered as a check in
+# run-evals.sh (that suite only bash -n's this file via its §1 syntax sweep).
+#
+# Usage:
+#   ./scripts/automation/run-judgment-evals.sh                  # plan + estimate, then refuse (exit 2)
+#   ./scripts/automation/run-judgment-evals.sh --yes-spend      # run every case
+#   ./scripts/automation/run-judgment-evals.sh --list           # enumerate cases, no dispatch
+#   ./scripts/automation/run-judgment-evals.sh --yes-spend --judge goal-evaluator --case case-01-clean-goal-achieved
+#   ./scripts/automation/run-judgment-evals.sh --yes-spend --judge reviewer
+#   ./scripts/automation/run-judgment-evals.sh --yes-spend --judge auditor
+#   ./scripts/automation/run-judgment-evals.sh --yes-spend --keep-sandbox   # keep per-case sandboxes for inspection
+#
+# Model/effort/permission resolution mirrors the engine (lib/quota-retry.sh):
+# everything resolves through lib/agent_permissions.py for the judge's agent
+# name, honoring the same env knobs (CHAIN_MODEL_OVERRIDE,
+# CHAIN_DISABLE_MODEL_ROUTING, CHAIN_EFFORT_OVERRIDE,
+# CHAIN_DISABLE_EFFORT_OVERRIDE, CHAIN_DISABLE_PERMISSION_ISOLATION,
+# CHAIN_CLAUDE_DISABLE_CACHE_HYGIENE). Each supported judge has a dispatch
+# builder (_prepare_<judge>) that reconstructs the engine's dispatch prompt for
+# that judge VERBATIM over the fixture tree:
+#   goal-evaluator — run-goal.sh Step 3, with the same deterministic
+#     pre-evaluator derivations (goal-slice, journey digest, drift note,
+#     journey-history.pre.json, log tails). NOT re-derived: scan-report.md /
+#     iter-diff.md — the engine builds those from live git state, which a frozen
+#     fixture cannot have; the fixtures carry them pre-generated by the same
+#     scanners (see tests/judgment/README.md).
+#   reviewer — goal-iter-lean.sh run_reviewer (goal-mode lean review), including
+#     the real review_diff_hint from lib/common.sh. The builder first rebuilds
+#     the engine-time repo state as a scratch git repo inside the sandbox:
+#     HEAD = the pre-iteration baseline (tree with source/change.patch
+#     reverse-applied), working tree = the case's post-iteration state left
+#     UNCOMMITTED — so the production `git diff HEAD` command the prompt embeds
+#     shows exactly the fixture's diff, like a live review moment.
+#   auditor — phase-audit.sh (run-phase.sh Step 9; goal-mode full depth routes
+#     through the same script with PHASE = the iter name). Same scratch-git
+#     state rebuild as the reviewer — at audit time the iteration's work is
+#     still uncommitted (commits happen at finalize / the goal push step) — so
+#     the auditor's own `git diff` and test runs see the live audit moment. The
+#     builder also enforces phase-audit.sh's preflight: the fixture's QA report
+#     must exist and carry a passing verdict, else production would never have
+#     dispatched the auditor at all.
+#
+# Each case runs in a throwaway sandbox: the fixture tree is COPIED in (judge
+# writes land there, never in the repo or the fixture) and the framework's
+# read-only assets (CLAUDE.md, .claude/, scripts/, config/, agents/) are
+# symlinked in so the judge reads the same instructions it reads in production.
+#
+# Exit codes: 0 all cases passed · 1 at least one case failed/errored ·
+#             2 refused (no --yes-spend) or usage error
+set -euo pipefail
+
+REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
+cd "$REPO_ROOT"
+LIB="$REPO_ROOT/scripts/automation/lib"
+JUDGMENT_ROOT="$REPO_ROOT/tests/judgment"
+
+YES_SPEND=false
+KEEP_SANDBOX=false
+LIST_ONLY=false
+JUDGE_FILTER=""
+CASE_FILTER=""
+while [[ $# -gt 0 ]]; do
+  case "$1" in
+    --yes-spend)   YES_SPEND=true ;;
+    --keep-sandbox) KEEP_SANDBOX=true ;;
+    --list)        LIST_ONLY=true ;;
+    --judge)       JUDGE_FILTER="${2:?--judge needs a value}"; shift ;;
+    --case)        CASE_FILTER="${2:?--case needs a value}"; shift ;;
+    -h|--help)     grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
+    *) echo "unknown flag: $1 (see --help)" >&2; exit 2 ;;
+  esac
+  shift
+done
+
+# Per-case billed-token estimates for the G9 cost line. Deliberately rough and
+# conservative: an evaluator dispatch is a multi-turn agentic session that
+# re-reads its context each turn (mostly at cache-read rates). Override via env
+# when you have telemetry that says otherwise.
+: "${CHAIN_JUDGE_EVAL_EST_IN_TOK:=350000}"
+: "${CHAIN_JUDGE_EVAL_EST_OUT_TOK:=25000}"
+
+# $/MTok by model family (input output). Source: claude-api skill model table,
+# cached 2026-06-24. Unknown models fall back to Opus pricing (conservative).
+_price_for_model() {
+  case "$1" in
+    claude-fable-*)  echo "10 50" ;;
+    claude-opus-*)   echo "5 25" ;;
+    claude-sonnet-*) echo "3 15" ;;
+    claude-haiku-*)  echo "1 5" ;;
+    *)               echo "5 25" ;;
+  esac
+}
+
+# ── Judge/case discovery ─────────────────────────────────────────────────────
+declare -a JUDGES=()
+for d in "$JUDGMENT_ROOT"/*/; do
+  [[ -d "$d" ]] || continue
+  name="$(basename "$d")"
+  [[ "$name" == "tools" ]] && continue
+  compgen -G "$d/case-*" >/dev/null || continue
+  [[ -n "$JUDGE_FILTER" && "$name" != "$JUDGE_FILTER" ]] && continue
+  JUDGES+=("$name")
+done
+if [[ ${#JUDGES[@]} -eq 0 ]]; then
+  echo "no judges found under tests/judgment/ (filter: '${JUDGE_FILTER:-none}')" >&2
+  exit 2
+fi
+# Fail BEFORE any spend if a judge directory has no dispatch builder below
+# (e.g. slice (c) auditor cases landing ahead of their runner support).
+for judge in "${JUDGES[@]}"; do
+  case "$judge" in
+    goal-evaluator|reviewer|auditor) ;;
+    *) echo "judge '$judge' has cases but no dispatch builder in this runner" >&2; exit 2 ;;
+  esac
+done
+
+declare -a CASES=()   # entries: judge|case_dir
+for judge in "${JUDGES[@]}"; do
+  for case_dir in "$JUDGMENT_ROOT/$judge"/case-*/; do
+    [[ -d "$case_dir" ]] || continue
+    cname="$(basename "$case_dir")"
+    [[ -n "$CASE_FILTER" && "$cname" != "$CASE_FILTER" ]] && continue
+    [[ -f "$case_dir/expected.txt" && -f "$case_dir/case.env" && -d "$case_dir/tree" ]] || {
+      echo "malformed case (needs expected.txt, case.env, tree/): $case_dir" >&2; exit 2; }
+    CASES+=("$judge|${case_dir%/}")
+  done
+done
+if [[ ${#CASES[@]} -eq 0 ]]; then
+  echo "no cases matched (judge='${JUDGE_FILTER:-any}', case='${CASE_FILTER:-any}')" >&2
+  exit 2
+fi
+
+# ── Engine-mirroring resolution (lib/quota-retry.sh semantics) ───────────────
+_resolve_effort() {  # $1 = agent name
+  if [[ -n "${CHAIN_EFFORT_OVERRIDE:-}" ]]; then
+    echo "$CHAIN_EFFORT_OVERRIDE"
+  elif [[ "${CHAIN_DISABLE_EFFORT_OVERRIDE:-false}" != "true" ]]; then
+    python3 "$LIB/agent_permissions.py" effort "$1" 2>/dev/null || echo "max"
+  else
+    echo "max"
+  fi
+}
+_resolve_model() {   # $1 = agent name; empty ⇒ no --model flag (ambient default)
+  if [[ "${CHAIN_DISABLE_MODEL_ROUTING:-false}" == "true" ]]; then
+    echo ""
+  elif [[ -n "${CHAIN_MODEL_OVERRIDE:-}" ]]; then
+    echo "$CHAIN_MODEL_OVERRIDE"
+  else
+    python3 "$LIB/agent_permissions.py" model "$1" 2>/dev/null || echo ""
+  fi
+}
+
+# ── Plan + cost estimate (always printed — the G9 confirmation surface) ──────
+echo "[judgment-evals] plan:"
+TOTAL_EST=0
+for entry in "${CASES[@]}"; do
+  judge="${entry%%|*}"; case_dir="${entry##*|}"
+  model="$(_resolve_model "$judge")"
+  effort="$(_resolve_effort "$judge")"
+  read -r p_in p_out <<<"$(_price_for_model "${model:-ambient-default}")"
+  est=$(awk -v i="$CHAIN_JUDGE_EVAL_EST_IN_TOK" -v o="$CHAIN_JUDGE_EVAL_EST_OUT_TOK" \
+            -v pi="$p_in" -v po="$p_out" 'BEGIN{printf "%.2f", (i*pi + o*po)/1e6}')
+  TOTAL_EST=$(awk -v a="$TOTAL_EST" -v b="$est" 'BEGIN{printf "%.2f", a+b}')
+  printf '  %-16s %-36s expected=%-13s model=%-18s effort=%-6s ~$%s\n' \
+    "$judge" "$(basename "$case_dir")" "$(head -n1 "$case_dir/expected.txt")" \
+    "${model:-(ambient default)}" "$effort" "$est"
+done
+echo "[judgment-evals] estimated cost: ~\$${TOTAL_EST} total" \
+     "(assumes ~${CHAIN_JUDGE_EVAL_EST_IN_TOK} billed input + ~${CHAIN_JUDGE_EVAL_EST_OUT_TOK} output tokens per case;"
+echo "                 rough ±3x — agentic sessions vary. Override via CHAIN_JUDGE_EVAL_EST_IN_TOK/_OUT_TOK.)"
+
+$LIST_ONLY && exit 0
+
+if ! $YES_SPEND; then
+  echo
+  echo "[judgment-evals] REFUSING to run: this spends real API tokens (ground rule G9)."
+  echo "                 Re-run with --yes-spend after the user has approved the estimate above."
+  exit 2
+fi
+
+command -v claude >/dev/null 2>&1 || { echo "claude CLI not found on PATH" >&2; exit 1; }
+
+# ── Per-judge dispatch builders ──────────────────────────────────────────────
+# Each builder runs inside the per-case loop with SANDBOX / case_dir /
+# SESSION_ID / CURRENT_ITER / ITER_NAME / DEPTH in scope, and must set:
+#   PROMPT       — the engine's dispatch prompt for this judge, verbatim
+#   VERDICT_FILE — where that judge writes its verdict artifact
+
+_prepare_goal_evaluator() {
+  # Engine path layout (run-goal.sh), rooted at the sandbox
+  GOAL_SESSION_DIR="$SANDBOX/runs/goal-session-${SESSION_ID}"
+  ITER_DIR="$GOAL_SESSION_DIR/iter-${CURRENT_ITER}"
+  JOURNEY_HISTORY="$GOAL_SESSION_DIR/state/journey-history.json"
+  EVALUATOR_LOG="$GOAL_SESSION_DIR/state/evaluator-log.md"
+  LESSONS_FILE="$GOAL_SESSION_DIR/state/lessons.md"
+  ASSUMPTIONS_FILE="$GOAL_SESSION_DIR/state/assumptions.md"
+  GOAL_FILE="$SANDBOX/docs/goal.md"
+  ITER_SPEC_PATH="$SANDBOX/docs/phases/${ITER_NAME}.md"
+  GOAL_SLICE_PATH="$ITER_DIR/goal-slice.md"
+  COHERENCE_OUTPUT="$ITER_DIR/coherence.md"
+  VERDICT_FILE="$ITER_DIR/eval.md"
+  mkdir -p "$ITER_DIR"
+
+  # Deterministic pre-evaluator derivations, exactly as run-goal.sh step 3c does
+  cp "$JOURNEY_HISTORY" "$ITER_DIR/journey-history.pre.json" 2>/dev/null || true
+  _spec_targets="$(grep -m1 -E 'Target journeys:' "$ITER_SPEC_PATH" 2>/dev/null | sed -E 's/.*Target journeys:\*?\*?[[:space:]]*//' | tr -d ' ')" || _spec_targets=""
+  python3 "$LIB/goal_gate.py" goal-slice "$GOAL_FILE" \
+    --history "$JOURNEY_HISTORY" ${_spec_targets:+--targets "$_spec_targets"} \
+    --out "$GOAL_SLICE_PATH" 2>/dev/null \
+    || cp "$GOAL_FILE" "$GOAL_SLICE_PATH" 2>/dev/null || GOAL_SLICE_PATH="$GOAL_FILE"
+  JOURNEY_DIGEST=$(python3 "$LIB/goal_gate.py" digest "$JOURNEY_HISTORY" 2>/dev/null || echo "(journey digest unavailable — read $JOURNEY_HISTORY)")
+  python3 "$LIB/goal_gate.py" hash-journeys "$GOAL_FILE" \
+    --history "$JOURNEY_HISTORY" --out-changed "$ITER_DIR/journeys-changed.md" \
+    >/dev/null 2>&1 || true
+  if [[ -f "$EVALUATOR_LOG" && -s "$EVALUATOR_LOG" ]]; then
+    EVALUATOR_LOG_TAIL_5=$(tail -n 300 "$EVALUATOR_LOG")
+  else
+    EVALUATOR_LOG_TAIL_5="(no entries yet — first evaluation)"
+  fi
+  if [[ -f "$ASSUMPTIONS_FILE" && -s "$ASSUMPTIONS_FILE" ]]; then
+    ASSUMPTIONS_TAIL=$(tail -n 200 "$ASSUMPTIONS_FILE")
+  else
+    ASSUMPTIONS_TAIL="(no assumptions recorded yet)"
+  fi
+
+  # The engine's goal-evaluator dispatch prompt (run-goal.sh Step 3), verbatim.
+  # Unquoted heredoc: $VARs expand; \` keeps literal backticks like the engine's
+  # escaped backticks inside its double-quoted prompt string.
+  PROMPT=$(cat <<PROMPT_EOF
+You are the goal-evaluator agent for goal-mode iteration evaluation.
+
+Session ID: $SESSION_ID
+Iteration index: $CURRENT_ITER
+Iter name: $ITER_NAME
+Depth dispatched: $DEPTH
+
+Project goal (SLICED — vision + anti-goals + target/failing journeys verbatim; stable passing journeys digested): $GOAL_SLICE_PATH
+  Full goal file: $GOAL_FILE — Read it ONLY if a digested journey becomes relevant.
+Iter spec: $ITER_SPEC_PATH
+Agent instructions: .claude/agents/goal-evaluator.md  <-- read this first
+(CLAUDE.md is already in your system prompt — do not Read it again.)
+
+Iteration artifacts (read what exists):
+  Deterministic diff scan (FULL diff — secrets/deps/license): $ITER_DIR/scan-report.md
+  Bounded diff view (complete file list; hunks capped, header lists omissions): $ITER_DIR/iter-diff.md
+  Dev handoff: docs/handoffs/${ITER_NAME}-dev.md
+  Review report: reports/reviews/${ITER_NAME}-review.md
+  QA report: reports/qa/${ITER_NAME}-qa.md (full mode only)
+  Audit handoff: docs/handoffs/${ITER_NAME}-audit.md (full mode only)
+  Browser QA results: reports/phase-${ITER_NAME}-ui-test-results.md
+  Evidence: reports/qa/${ITER_NAME}-evidence/
+  Coherence audit: $COHERENCE_OUTPUT  <-- COHERENCE-FAIL vetoes GOAL_ACHIEVED and drives a consolidation CONTINUE
+  Goal-edit drift note: $ITER_DIR/journeys-changed.md  <-- if present, each listed journey's prior pass is VOID until re-verified against the CURRENT goal text (your step 3)
+
+Journey state (inline digest — your methodology's section A table starts here):
+\`\`\`
+$JOURNEY_DIGEST
+\`\`\`
+
+Prior session state:
+  Journey history: $JOURNEY_HISTORY  <-- update this with new state (full atomic write)
+  Evaluator log: $EVALUATOR_LOG  <-- append a new entry; do not overwrite or read the full file (last 5 entries pre-trimmed below)
+  Lessons file: $LESSONS_FILE  <-- append a brief lesson entry capturing a non-obvious takeaway (1-3 sentences). Skip if nothing surprising happened.
+  Assumption ledger: $ASSUMPTIONS_FILE  <-- append an entry when a scoring decision required interpreting an ambiguous goal (step 5b of your instructions). Skip when none — zero entries is normal.
+
+Recent evaluator log entries (last 5, pre-trimmed):
+\`\`\`
+$EVALUATOR_LOG_TAIL_5
+\`\`\`
+
+Recent assumption entries (pre-trimmed):
+\`\`\`
+$ASSUMPTIONS_TAIL
+\`\`\`
+
+Apply the TOKEN AND QUESTIONING POLICY from .claude/core.md strictly.
+
+Write your verdict to: $VERDICT_FILE
+
+The verdict line MUST appear at the top of $VERDICT_FILE and start exactly with:
+**Verdict:** GOAL_ACHIEVED
+  or **Verdict:** CONTINUE
+  or **Verdict:** ESCALATE
+  or **Verdict:** REGRESSION
+  or **Verdict:** STALLED
+
+Also include a 'Depth Recommendation For Next Iteration:' line: lean or full.
+
+Then update $JOURNEY_HISTORY (full atomic write) and append an entry to $EVALUATOR_LOG.
+STOP.
+PROMPT_EOF
+)
+}
+
+_prepare_reviewer() {
+  # Rebuild the engine-time repo state as a scratch git repo inside the sandbox:
+  # HEAD = the pre-iteration baseline (tree with source/change.patch
+  # reverse-applied), working tree = the case's post-iteration state left
+  # UNCOMMITTED. The production reviewer reviews exactly this state — work is
+  # committed only at the push step, AFTER evaluation — so the `git diff HEAD`
+  # command its prompt embeds shows precisely the fixture's authored diff.
+  # (Derived by tests/judgment/reviewer/tools/regen.sh; frozen in the fixture.)
+  git -C "$SANDBOX" init -q -b main
+  git -C "$SANDBOX" apply -R "$case_dir/source/change.patch"
+  git -C "$SANDBOX" add -A
+  git -C "$SANDBOX" -c user.name="goal-chain" -c user.email="goal-chain@localhost" \
+    commit -q -m "chore(goal): iter $((CURRENT_ITER - 1)) (base app, journeys J-01..J-03)"
+  git -C "$SANDBOX" apply "$case_dir/source/change.patch"
+
+  # Engine path layout (goal-iter-lean.sh), rooted at the sandbox
+  ITER_SPEC_PATH="$SANDBOX/docs/phases/${ITER_NAME}.md"
+  DEV_HANDOFF="$SANDBOX/docs/handoffs/${ITER_NAME}-dev.md"
+  VERDICT_FILE="$SANDBOX/reports/reviews/${ITER_NAME}-review.md"
+  mkdir -p "$SANDBOX/reports/reviews"
+
+  # The real production diff instruction (REVIEW_DIFF_EXCLUDE_PATTERNS and all),
+  # from the same function the engine's prompt substitutes in.
+  DIFF_HINT="$(bash -c "source '$LIB/common.sh' && review_diff_hint HEAD")"
+
+  # The engine's reviewer dispatch prompt (goal-iter-lean.sh run_reviewer),
+  # verbatim.
+  PROMPT=$(cat <<PROMPT_EOF
+You are the reviewer agent for goal-mode lean iteration.
+
+Iteration: $ITER_NAME
+Iter spec: $ITER_SPEC_PATH
+Dev handoff: $DEV_HANDOFF
+Project template: .claude/project-template.md
+Agent instructions: .claude/agents/reviewer.md  <-- read this first
+(CLAUDE.md is already in your system prompt — do not Read it again.)
+
+$DIFF_HINT
+
+Apply the TOKEN AND QUESTIONING POLICY from .claude/core.md strictly.
+
+Write your review report to: $VERDICT_FILE
+
+The report MUST start with a line matching exactly:
+**Verdict:** PASS
+  or
+**Verdict:** PASS_WITH_NOTES
+  or
+**Verdict:** FAIL
+PROMPT_EOF
+)
+}
+
+_prepare_auditor() {
+  # Rebuild the engine-time repo state exactly like _prepare_reviewer: at audit
+  # time (run-phase.sh Step 9, before finalize; goal mode commits at the push
+  # step after evaluation) the iteration's work is still UNCOMMITTED on top of
+  # the committed baseline — so the auditor's post-fix `git diff` self-check
+  # and any test runs see a live audit moment.
+  git -C "$SANDBOX" init -q -b main
+  git -C "$SANDBOX" apply -R "$case_dir/source/change.patch"
+  git -C "$SANDBOX" add -A
+  git -C "$SANDBOX" -c user.name="goal-chain" -c user.email="goal-chain@localhost" \
+    commit -q -m "chore(goal): iter $((CURRENT_ITER - 1)) (base app, journeys J-01..J-03)"
+  git -C "$SANDBOX" apply "$case_dir/source/change.patch"
+
+  # Engine path layout (phase-audit.sh, PHASE = the iter name), rooted at the
+  # sandbox. phase_spec_path resolves docs/phases/<phase>.md first — the
+  # fixture uses that exact name.
+  SPEC="$SANDBOX/docs/phases/${ITER_NAME}.md"
+  PLAN_FILE="$SANDBOX/runs/${ITER_NAME}/plan.md"
+  DEV_HANDOFF="$SANDBOX/docs/handoffs/${ITER_NAME}-dev.md"
+  FRONTEND_HANDOFF="$SANDBOX/docs/handoffs/${ITER_NAME}-frontend.md"
+  REVIEW_REPORT="$SANDBOX/reports/reviews/${ITER_NAME}-review.md"
+  QA_REPORT="$SANDBOX/reports/qa/${ITER_NAME}-qa.md"
+  TEST_PLAN="$SANDBOX/reports/qa/${ITER_NAME}-test-plan.md"
+  STATUS_FILE="$SANDBOX/runs/${ITER_NAME}/status.json"
+  VERDICT_FILE="$SANDBOX/docs/handoffs/${ITER_NAME}-audit.md"
+
+  # phase-audit.sh's preflight, verbatim semantics: QA must exist AND pass
+  # before the auditor is ever dispatched. A fixture failing this is malformed.
+  if [[ ! -f "$QA_REPORT" ]] || ! python3 "$LIB/verdicts.py" check-verdict "$QA_REPORT"; then
+    echo "malformed auditor case (QA report missing or not passing — production never dispatches the auditor): $case_dir" >&2
+    exit 2
+  fi
+
+  # Optional context lines, built exactly like phase-audit.sh builds them.
+  HANDOFF_CONTEXT="Dev handoff: $DEV_HANDOFF"
... [diff_bound] incredible_auto_dev/scripts/automation/run-judgment-evals.sh: 155 more diff lines omitted — Read the file for full detail
```
