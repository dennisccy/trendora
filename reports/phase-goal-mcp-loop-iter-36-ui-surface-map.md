# goal-mcp-loop-iter-36 — UI Surface Map

**Phase:** goal-mcp-loop-iter-36
**Date:** 2026-07-14
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/research/referee-audit` | Loading skeleton (`data-testid="referee-audit-skeleton"`) | New component | Brief render before the `GET /api/research/referee-audit` fetch resolves | Navigate to `/research/referee-audit` on a throttled connection (or with DevTools network throttling on) and confirm a pulsing 4-card skeleton grid (`data-testid="referee-audit-skeleton"`) renders before the real content appears. |
| `/research/referee-audit` | Backend-unavailable card (`data-testid="referee-audit-error"`) | New component | Honest degradation when the API call fails/network-errors | Stop the backend, navigate to `/research/referee-audit`, and confirm a red-bordered card with the text "Backend unavailable" appears (`data-testid="referee-audit-error"`), with the page header and "Back to Research" link still present. |
| `/research/referee-audit` | Honest empty state (`data-testid="referee-audit-empty"`) | New component | No artifact has ever been persisted at the configured `report_path` | Set `TRENDORA_REFEREE_AUDIT_PATH` to a nonexistent file path (or move the real `runs/goal-session-mcp-loop/state/referee-audit-report.json` aside), restart the backend, reload `/research/referee-audit`, and confirm the card reading "No audit run yet" (`data-testid="referee-audit-empty"`) appears, explaining the harness runs as a config-seeded offline job, not a UI action. |
| `/research/referee-audit` | Unreadable-artifact state (`data-testid="referee-audit-unreadable"`) | New component | A corrupt/unparseable artifact must degrade honestly, distinct from "never run" | Overwrite the file at the configured `report_path` with invalid content (e.g. the literal text `not-json`), reload `/research/referee-audit`, and confirm an **amber** (not red) card reading "Audit artifact unreadable" appears (`data-testid="referee-audit-unreadable"`), visually distinct from both the empty state and the tripwire state. |
| `/research/referee-audit` | Stat summary grid (`data-testid="referee-audit-grid"`) | New component (core J-22 display) | Surfaces the 4 headline calibration metrics from the persisted artifact | With the real committed artifact in place (default state — no setup needed), load `/research/referee-audit` and confirm the grid shows: null trials **"200"** with subtext "source factor: leadership_score" (`data-testid="referee-audit-null-trials-value"`); false-pass rate **"0.08"** with subtext "16 of 200 trials · 95% CI [0.04984, 0.126]" (`data-testid="referee-audit-false-pass-rate-value"`); α **"0.05"** (`data-testid="referee-audit-alpha-value"`); run date **"2026-07-01"** with subtext "seed 20240601 · contaminated horizon 5d" (`data-testid="referee-audit-run-date-value"`). |
| `/research/referee-audit` | Tripwire card (`data-testid="referee-audit-tripwire"`) | New component (core J-22 safety signal) — **this is the current live state** | The real offline run found the lookahead-contaminated factor was NOT rejected by the referee | With the real committed artifact in place (default state — no setup needed), load `/research/referee-audit` and confirm a red card (`border-neg bg-neg/10`, `data-testid="referee-audit-tripwire"`) reads "Tripwire: the lookahead-contaminated factor was NOT rejected," shows a **"PASS"** badge styled in `danger`/red (`data-testid="referee-audit-contaminated-status"` — must NOT use the `accent` "Proven" color), and the text "expected: rejected" appears next to the badge. |
| `/research/referee-audit` | Calm confirmation card (`data-testid="referee-audit-contaminated-caught"`) | New component — not the current live state; requires a fixture | Quiet confirmation state for when the contaminated factor IS correctly rejected | Point `TRENDORA_REFEREE_AUDIT_PATH` at a fixture JSON with `contaminated_verdict.status` set to `"FAIL"` (or `"INSUFFICIENT"`) so `contaminated_caught` computes `true`, restart the backend, reload the page, and confirm a plain (non-red) card with a green shield-check icon (`data-testid="referee-audit-contaminated-caught"`) reads "Lookahead-contaminated factor: caught" in place of the tripwire card. |
| `/research` | New "Referee audit" governance card (`data-testid="research-governance-link-referee-audit"`) | Added navigation | 4th and final card in the "Governance & process" cluster (registry/graveyard/budget/referee-audit) | Load `/research`, confirm the "Governance & process" section shows 4 cards ending with "Referee audit" (shield-check icon, same border/hover style as the other 3), click it, and confirm the browser navigates to `/research/referee-audit`. |

<!-- Change Type key used above: New component | Added navigation -->

---

## Backend-Only Changes (No UI Impact)

As with prior governance-cluster iterations in this session, most backend production code below is not itself a UI file but is directly in the serving chain for the one new page/endpoint pair above — listed here with the feed-through made explicit rather than claimed as isolated:

- `apps/backend/app/engine/referee_audit.py` (NEW) — the harness: seeded null-factor generator (`permute_null_observations`), the lookahead-contaminated-factor construction, the isolated orchestrator (`run_referee_audit`, runs against a throwaway `ledger_path`, never the real ledgers), the Wilson-score binomial CI (`binomial_ci`), the report builder (`build_referee_audit_report`), and the resolver/writer/reader trio. No UI file itself, but `read_referee_audit_report()` is confirmed the *only* function the new endpoint calls — single source for every value in the stat grid and verdict cards above.
- `apps/backend/app/api/referee_audit.py` (NEW) — the thin `GET /api/research/referee-audit` router. Directly UI-serving: `fetchRefereeAudit()` in `lib/api.ts` calls exactly this path.
- `apps/backend/app/config.py` (MODIFIED) — new `RefereeAuditCfg` (`n_null_trials`, `seed`, `contaminated_factor_horizon`, `report_path`), nested as `ResearchCfg.referee_audit`. Not a UI file, but confirmed feed-through: three of its values are rendered verbatim in the stat grid's subtext (`n_null_trials` → "200", `seed` → "20240601", `contaminated_factor_horizon` → "5d").
- `config.yaml` (MODIFIED) — the committed `research.referee_audit:` block (`n_null_trials: 200`, `seed: 20240601`, `contaminated_factor_horizon: 5`, `report_path`). Same feed-through as above — these are the exact committed values the real offline run used and the exact numbers a user reads on the page today.
- `apps/backend/main.py` (MODIFIED) — one import + `application.include_router(referee_audit.router, prefix="/api")`. Wiring only — makes the endpoint reachable; carries no rendered content of its own.

Genuinely backend-only, zero UI surface affected (test files only):
- `apps/backend/tests/test_referee_audit.py` (NEW) — 41 unit tests for the harness (permutation math, Wilson CI, determinism, isolation, orchestration).
- `apps/backend/tests/test_api_referee_audit.py` (NEW) — 5 endpoint tests (honest-empty, honest-unreadable, verbatim serving).

Not source code, but worth flagging since it is the literal data behind every "current live state" row above:
- `runs/goal-session-mcp-loop/state/referee-audit-report.json` (new, git-untracked, produced by the one-off offline run — not source) — the real persisted report every value in the surface map's "current real state" cells traces to, verbatim.
- `runs/goal-session-mcp-loop/state/referee-audit-throwaway-ledger.jsonl` (new, git-untracked — not source) — the disposable 201-entry audit trail from that run; never read by the endpoint or any UI surface.

---

## Summary

- **Frontend surfaces changed:** 2 (`/research/referee-audit` — new page with 7 distinct visual states/components; `/research` hub — gains 1 new nav card)
- **New pages/routes:** 1 (`/research/referee-audit`)
- **Modified components:** 1 existing page file modified (`apps/frontend/app/research/page.tsx`), 1 new page component (`apps/frontend/app/research/referee-audit/page.tsx`), 1 new types-only file (`apps/frontend/lib/referee-audit.ts`), 1 typed API-client file extended (`apps/frontend/lib/api.ts` — new `fetchRefereeAudit()` + 3 re-exported types)
- **Navigation changes:** yes — 1 new card added to the existing `/research` "Governance & process" grid; no nav-skeleton change, no new top-level route group
- **Backend-only changes:** 2 test files (zero UI impact); all other backend production files feed the one new page/endpoint pair described above (see feed-through notes)
