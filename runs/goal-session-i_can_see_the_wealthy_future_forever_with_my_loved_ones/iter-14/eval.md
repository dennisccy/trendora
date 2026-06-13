# Iteration 14 Evaluation

**Verdict:** GOAL_ACHIEVED
**Depth Recommendation For Next Iteration:** full

## Summary

Iter-14 (full depth) shipped J-63 — the event study is now overlap-honest, defaulting to first-trigger **Episodes** with a one-click **Episodes ⇄ Pooled** toggle, both modes disclosing n + unique-symbols + episode-count. This was the LAST buildable Must-have journey. With J-63 verified passing — and independently re-derived against the live backend — every buildable Must-have (J-01..J-21, J-25..J-67) is passing/already_passing, J-22/J-23/J-24 stay honestly blocked-NA (data-walled, non-vetoing per goal.md), no anti-goal is violated, and coherence is COHERENCE-PASS. All three GOAL_ACHIEVED conditions hold; the loop halts with success.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-63 | failing | **passing** | reports/qa/.../iter-14-evidence/UT-03-result.png (episodes drill-down, 106 obs, first-trigger rows); UT-09-result.png (pooled, 180); UT-14-glossary.png (Episode + Pooled entries); UT-01-result.png (/research Episodes default); + live re-derivation (see below) |
| J-29 (req-still-passing) | passing | passing (unchanged) | lab renders all figures in both modes (UT-12); backend builder additively extended, pooled byte-identical |
| J-51 / J-64 / J-65 (req-still-passing) | passing | passing (unchanged) | samples count-coherence both modes (live: 707/707 episodes, 2242/2242 pooled); sort/filter intact (UT-13); N= chips carry view + new-tab |
| J-25/J-26/J-27/J-30/J-31/J-32 (req-still-passing) | passing/already_passing | passing (unchanged) | other /research labs read unchanged; J-32 scope-mode orthogonal to view toggle |
| J-12 / J-47 (req-still-passing) | passing | passing (unchanged) | /methodology served 122 config terms incl. Episode + Pooled (live-verified) |
| J-18 / J-06 (req-still-passing) | passing | passing (unchanged) | view is a cohort/mode selector — no second date state (diff-verified, orthogonal to ?asof/scope) |
| J-01..J-21, J-25..J-62, J-64..J-67 | passing/already_passing | carried (no diff touching them) | full backend suite 787 passed / 4 skipped / 0 failed |
| J-22 / J-23 / J-24 | unknown (blocked-NA) | unknown (blocked-NA) | data-walled, non-vetoing per goal.md "Data-dependent journeys (non-halting)" |

### Independent live re-derivation of J-63 (binding proof, not the QA tables)

Against the running backend (`http://localhost:8835`, iter-14 working tree, warmup 10/10 ok):
- **Default view = episodes** — `GET /api/research/event-study?subject=Risk-off-watchlist&horizon=1` (no view param) → `view=episodes`.
- **Disclosure values present in both modes** — `n`, `unique_symbols`, `episode_count`.
- **episodes_n < pooled_n for a persisting subject** — Risk-off-watchlist h=1: episodes n=707 < pooled n=2242; `episode_count=707` and `unique_symbols=122` identical in both modes (view-independent).
- **Count-coherence SAME-INSTANT in BOTH modes** — event-study n == samples total == len(rows): episodes 707/707/707, pooled 2242/2242/2242.
- **422 on invalid view on BOTH endpoints** — `view=bogus` → HTTP 422, detail "unknown view 'bogus'; valid views are ['episodes', 'pooled']".
- **Pooled figures real and mode-specific** — Actionable h=1 by_regime Strong-risk-on: episodes n=3/0.004351719227508433 vs pooled n=7/0.006088009982285679 (matches QA TC-14 byte-for-byte; pooled routes through the unchanged `_event_study_members` path).
- **Glossary config-backed** — `/api/methodology` served 122 terms (≥100) including "Episode" and "Pooled (per-signal-day)".

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| No lookahead | OK | Episode collapse is a pure grouping of stored ≤D observations; no bar/return touched. |
| Snapshots are immutable | OK | No stored column/table/migration added; no `scanner_runs` UPDATE in the diff. |
| Single source of truth / No recompute in read path | OK | One shared `_event_study_observation_set` builder feeds aggregate + samples; pooled byte-identical via unchanged `_event_study_members`; episode path is SELECT-only grouping (no `run_scan/score_*/detect_*/forward_*`, diff-verified; read-only assertion test green). |
| No magic numbers | OK | config.yaml diff is only two glossary term additions; no scoring/threshold literal; no validated section change; episode-consecutiveness/win boundary are structural rules. |
| No fabricated data | OK | Low-sample cells stay NA + n; no synthesized row; episode rows carry stored return/MAE/MFE/regime/sector verbatim. |
| No order/execution path | OK | None added (research-module change only). |
| No secrets in source | OK | Diff swept — no key/secret/token literal. |
| Glossary copy lives in one catalog | OK | Episode/Pooled added to config `methodology.terms`; no hardcoded per-entry copy in the frontend. |
| Exactly one date selector (J-18) | OK | `view` is a cohort/mode selector independent of `asofCutoff`/`scope`/`?asof` (source-verified); no second date state. |
| Episode mode recomputes nothing (J-63) | OK | Deterministic collapse of the same stored rows; pooled byte-identical; both modes disclose n + unique symbols + episode count; count-coherent both modes (live-verified). |

No anti-goal violation, critical or minor. `anti_goal_violations: []`.

## Next-Step Recommendation

Halt — goal achieved. Every buildable Must-have journey is passing/already_passing; J-22/J-23/J-24 remain honestly blocked-NA (data-walled, non-vetoing). If the repository owner later makes a cap-capable EOD provider reachable, J-22 auto-unblocks via the J-35 Data Manager Expand-universe job (and J-23/J-24 via the committed intraday runbook) with no code change. The depth recommendation (full) applies only if the session is resumed in-place with new journeys appended to goal.md (the J-55..J-67 extension pattern) — there is no next iteration otherwise.

## Halt Justification

GOAL_ACHIEVED. All three conditions hold, each grounded in concrete evidence:

1. **Every Must-have journey is passing or already_passing.** After J-63 flipped to `passing` this iteration, journey-history shows zero buildable journeys failing/partial/regressed. The only non-passing journeys are J-22/J-23/J-24 (`unknown`/blocked-NA), which goal.md's "Data-dependent journeys (non-halting)" section states verbatim "**MUST NOT halt the loop, drive a STALLED verdict, or veto GOAL_ACHIEVED**" (goal.md lines 1931-1937) — confirmed by the iter-4 and iter-8 evaluators and the mandated one-shot best-effort fetch already attempted (Yahoo cap endpoint 401; zero data fabricated).

2. **No critical anti-goal violation exists.** The iter-14 diff was swept against every anti-goal (table above); `anti_goal_violations` is empty. The only review note is a trivial unused `_episode_count` helper (dead code, NOTE severity — non-blocking).

3. **Coherence is COHERENCE-PASS.** iter-14/coherence.md reports 0 Data-Contract and 0 Information-Architecture violations: pooled is byte-identical via the unchanged canonical path, one shared observation-set builder feeds both the aggregate and the samples drill-down, and there is no new endpoint, route, stored column, nav section, duplicate home, or second date state.

Corroborating gates: review PASS_WITH_NOTES, QA PASS (25/25), browser-QA PASS (16/16 with 4 evaluator-viewed distinct full-size screenshots), full backend pytest **787 passed, 4 skipped, 0 failed** (0:54:25, log tail confirmed) including the pooled byte-identity guard, count-coherence-in-both-modes, and episode-collapse determinism tests. The engine's audit/ux-regression/closure handoffs were absent for this fresh full-depth iteration (the known `post_dev_parallel_complete` quirk); the verdict is grounded in the artifacts that do exist plus independent live re-derivation, which together cover the audit/closure intent.
