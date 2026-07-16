# Iteration 41 — Coherence Audit

**Iteration:** goal-mcp-loop-iter-41
**Date:** 2026-07-16
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-WARN

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| **Phase-conditional drawdown & dry-spell expectations** (median/p90 of max-DD depth, underwater duration, time-to-recover, + walk-forward-cadence loss streak, split by causal phase-at-entry) — NEW value, pre-registered in `blueprint.md`'s Data Contract this iteration (iter-41 IA row + Data Contract row + "iter-41 clarification" paragraph, all present in `runs/goal-session-mcp-loop/state/blueprint.md`) | OK | Computed once: `apps/backend/app/engine/forward_testing.py:1187` (`compute_drawdown_expectations`) — the only production definition (`grep -rn "def compute_drawdown_expectations\b"` → 1 hit). Served via a cache wrapper over the SAME function: `forward_testing.py:1321` (`compute_drawdown_expectations_cached`, reuses the existing J-72 `EventStudyCache` table, MISS calls the canonical function at `:1357` and persists its output verbatim, HIT deserializes the identical payload — `test_forward_testing.py:1513` pins byte-identity between a fresh call and the cached call). Threaded into the payload at `apps/backend/app/engine/evidence.py:151-182` (`build_evidence_payload`, only when `session` is passed) and exposed as the additive `expectations` field on the EXISTING `GET /api/evidence` (`apps/backend/app/api/evidence.py:41-54`) — no new endpoint. Existing session-less call sites (~13, incl. the frozen-golden ledger test) still get byte-identical rows (`session=None` default, confirmed by the diff and `test_evidence.py:596` "read straight from `compute_drawdown_expectations`, never a second"). |
| — cohort resolution inside the above | OK — reused, not re-implemented | `forward_testing.py:457-471` calls the EXISTING `app.engine.samples.compute_samples` (same selectors `/api/research/samples` uses); `_claim_samples_kwargs` (`:352-369`) only renames selector keys, it does not decide cohort membership. |
| — `max_drawdown` (existing contract value: the stored drawdown-depth figure shown on Stocks/Themes/Sectors/Stock-Detail/Backtest) | OK — reused verbatim, not forked | `forward_testing.py:1379` test (`test_compute_drawdown_expectations_max_drawdown_reused_verbatim_not_recomputed`) plus the model docstring `models.py:637-652` confirm the stored `ForwardReturn.max_drawdown` column (written once in `_insert_run_forward_returns`, `forward_testing.py:284`) is the ONLY source read into the new aggregation (`:512`, `by_phase_mdd`). `time_to_recover_days` (`:243-275`) internally re-derives a running-peak series to locate the trough BAR INDEX only (which `max_drawdown` doesn't expose) — it never overrides or re-serves a drawdown-depth number; `test_time_to_recover_days_counts_bars_from_trough_to_entry_reclaim` pins that internal trough value against `max_drawdown`'s own return for identical inputs, so the two cannot silently diverge. |
| — causal phase-at-entry (existing contract value, part of the Market regime/phase row) | OK — reused, not recomputed | `forward_testing.py:463,494` calls the EXISTING `app.engine.market_phase.phase_context_by_date` (the one stored causal timeline `compute_market_phase` also reads) — no second phase classifier. The OUT-OF-SCOPE-flagged `market_phase.time_underwater` trailing-severity component is NOT touched or reused (confirmed absent from the diff and from `forward_testing.py`'s imports). |
| Leadership / Entry Quality / Risk scores, regime score, sector/theme scores, existing forward-return aggregates (all pre-existing contract rows) | OK — untouched | None of `scoring.py`, `regime.py`, `sectors.py`, `themes.py` appear in the diff's changed-file list (`git diff --stat` from snapshot `1564f151...`); only `forward_testing.py`, `models.py`, `db.py`, `config.py`/`config.yaml`, `api/evidence.py`, `engine/evidence.py` + tests + the two evidence frontend files changed. |

No new UI surface fetches any of the above from a non-canonical endpoint, and no client-side recomputation exists: `apps/frontend/app/evidence/page.tsx:1530-1626` (`DrawdownExpectationsPanel`/`DistributionCellView`/`LossStreakCellView`) and `apps/frontend/lib/evidence.ts:1784-1805` (`insufficientLabel`/`formatDays`/`formatStreak`) only re-format server-supplied `claim.expectations` numbers (rounding, unit suffixes, "insufficient (n=…)" copy) — never derive a median/p90/streak in the browser, which the skill explicitly permits. `lib/api.ts` changes are type re-exports only (`:1639-1654`).

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `DrawdownExpectationsPanel` inside `ClaimRow` on `/evidence` | OK | Additive section on the EXISTING `/evidence` route (`apps/frontend/app/evidence/page.tsx:1518`), which the blueprint's IA homes table already lists as J-25's canonical home ("Evidence [NEW]" nav section, J-05's existing home). `git diff` file list contains no `sidebar*`/`Nav*`/`app/layout.tsx` entry, and a direct grep of the diff for `sidebar\|Sidebar\|app/layout.tsx\|nav-item\|NavLink` returns zero code hits — no nav file touched, consistent with the iter spec's own "no new page, no new route, no nav change" and the code review's `navigation_updated: n/a`. |

No new route was created (no new file under `apps/frontend/app/` in the diff), no duplicate home for an existing entity (the existing `/evidence` `ClaimRow` field grid and verdict badge are confirmed unchanged/unshifted per the ui-surface-map's own regression-guard row), and no parallel shell — the panel is appended inside the page's existing `Card`/`CardContent` structure.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- **Phase badge inside the new table diverges from the app's single-source phase-color mapping.** `apps/frontend/app/evidence/page.tsx:1564` renders each phase cell as `<Badge variant="default">{row.phase}</Badge>` — a flat, uncolored badge — while every OTHER phase badge in the product (e.g. the Dashboard market-phase card) is severity-color-coded via the single-source `lib/phase.ts` `phasePosture`/`phaseVariant` mapping. This is the SAME entity (market phase) rendered with inconsistent visual treatment across pages (skill Part C: "same entity labelled differently across pages" / "visually drifts from the established style") — not a Data Contract violation, since the underlying phase VALUE is still sourced exclusively from the canonical `phase_context_by_date` (see Data Contract check above); only the color styling differs. Already caught independently by the code reviewer as MINOR (`reports/reviews/goal-mcp-loop-iter-41-review.md:22-27`), which recommends: color the phase `Badge` via `lib/phase.ts`'s `phasePosture` (or the existing `phaseVariant` mapping) so Bear/Correction/Pullback/Expansion/Recovery read consistently with every other phase badge in the app. Non-blocking; recorded here for the next iteration to tidy.

## Basis for this audit

- Blueprint: `runs/goal-session-mcp-loop/state/blueprint.md` (IA homes table row "J-25", Data Contract row "Phase-conditional drawdown & dry-spell expectations," and the "iter-41 clarification" paragraph — all three already present, registered ahead of/alongside this iteration's dev work; confirmed via `git diff 1564f151... -- runs/goal-session-mcp-loop/state/blueprint.md`, a clean +4-line append matching the established iter-38/iter-40 clarification-paragraph pattern, not a rewrite of any existing row).
- Iteration spec: `docs/phases/goal-mcp-loop-iter-41.md` ("Data-contract additions" / "Blueprint conformance" sections — both claim zero new endpoints/pages/nav changes; confirmed against the diff).
- Diff: `runs/goal-session-mcp-loop/iter-41/iter-diff.md` did not exist for this iteration, so this audit used `git diff 1564f15157088844872fe4717f24eeb2a64b4b84 -- . <standard exclusions>` (1828 lines, 20 files) plus its `--stat` of excluded paths (harness/`runs/*`/`reports/*` churn only, plus the blueprint.md +4 line append noted above; no lockfile changes).
- UI surface map: `reports/phase-goal-mcp-loop-iter-41-ui-surface-map.md` (cross-checked against the diff; consistent, including its own note of the mid-iteration `compute_drawdown_expectations_cached` addition and the phase-badge-color MINOR flag).
- Corroborating greps run directly against the working tree: `compute_drawdown_expectations`/`compute_drawdown_expectations_cached` have exactly one production definition each and one production call chain (`evidence.py` → cache wrapper → pure function); `underwater_days`/`time_to_recover_days` appear only in `models.py`/`db.py` (storage), `forward_testing.py` (the one computation site), and the two evidence frontend files (display) — no second computation path; no `sidebar`/nav/layout file in the diff; no out-of-scope `backtest` page changes (the two "backtest" hits in the diff are pre-existing README/docstring prose, not code changes).
