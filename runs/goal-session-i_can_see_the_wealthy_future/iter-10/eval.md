# Iteration 10 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

Iteration 10 **fixed the iter-9 silent dev no-op and actually implemented J-14** — the Backtest /
Time-Machine workspace (`/backtest`) + the per-date forward-test scorecard endpoint
(`GET /api/backtest` → `compute_run_scorecard`). I verified J-14 to gold standard **despite a 9th
consecutive dedicated browser-qa SKIP and ZERO QA evidence PNGs**: I ran the new tests myself
(17/17 pass, exit 0), booted the services, hit the live API, and drove a real browser to render
both scorecard states — then produced the missing evidence PNGs. Coherence is **COHERENCE-PASS**
(the two refactors *reduce* duplication). **14/16 Must-haves now pass**; J-12 and J-16 remain
unbuilt by design → CONTINUE.

## What I verified first-hand (browser-qa SKIPped + no carried PNGs, so I produced the evidence)

**Implementation is real (the iter-9 failure mode is fixed).** `git status` + `status.json`
(`current_step="qa_complete"`, `tests_run=true`, 10 changed files) confirm a genuine execution.
New: `app/api/backtest.py`, `test_api_backtest.py`, `test_backtest_scorecard.py`,
`app/backtest/page.tsx`, `components/forward-return.tsx`; modified: `forward_testing.py` (+191),
`main.py`, `sidebar.tsx`, `lib/api.ts`, `system-health/page.tsx`. **`models.py` untouched.**

1. **Unit/API (my own `.venv` pytest run — exit 0, 229s): 17/17 new J-14 tests pass**, including
   the **keystone** (`test_backtest_keystone_serves_persisted_date_without_recompute` /
   `test_scorecard_keystone_recomputes_nothing`) which patches `forward_return` **and** the
   `score_*` engines to **raise** and asserts the scorecard still serves from stored rows — proving
   "no recompute in the read path" by the negative, not by value-equality; plus no-lookahead post-D
   boundary, create-once idempotent, honest partial/NA, group-by-stored-rank (single source), and a
   cross-check that `compute_run_scorecard` equals `compute_forward_aggregates` filtered to the run.
2. **Live API (freshly-booted uvicorn on :8835, committed seed):**
   - `GET /api/backtest` (latest 2026-05-28) → `is_latest=true`, every horizon `mean_return:null /
     n:0` — **honest all-NA, no fabricated 0%**.
   - `GET /api/backtest?as_of=2022-10-07` (full window) → **NUMERIC** cohort returns at 1/5/10/20/60d
     (n=20=`top_n`), excess vs SPY/QQQ/sector, random-same-sector control n=31, all 5 control cohorts.
   - Invalid dates → `2999-01-01`→400, `1900-01-01`→400, `not-a-date`→422 — **never** a fabricated
     scorecard.
   - Single-source cross-check: `/api/dashboard?as_of=2022-10-07` = Risk-off 8.34, Actionable 0.
3. **Live browser render (`next start` on :3835, Chrome via MCP) of BOTH states:** the rendered
   scorecard cells equal the API payload **byte-for-byte, re-formatted to %** (FE recomputes
   nothing); low-sample `n<30` flagged ⚠; survivorship banner + "Viewing as-of D (historical/latest)"
   indicator present; **Backtest reachable in 1 click** from the sidebar (between Scanner Runs and
   System Health); the all-NA latest date shows the honest "No numbers are fabricated to fill the
   gap" empty state. **No console errors** anywhere in the session.

## Journey Results This Iteration

| Journey | Prior | This Iter | Evidence |
|---------|-------|-----------|----------|
| **J-14** Backtest + forward-test scorecard | failing | **passing (NEW)** | evidence/J14-backtest-2022-10-07-numeric-scorecard.png, J14-backtest-latest-all-NA.png + my 17/17 test run + live API |
| J-13 global as-of switcher (guard) | passing | passing (live re-shot) | evidence/J13-dashboard-historical-2022-10-07.png (Risk-on 74.32→Risk-off 8.34) |
| J-09 System Health evidence (refactor guard) | passing | passing (live re-shot) | evidence/J09-J10-system-health-after-refactor.png (A +6.00% n=24…E +2.05% n=772, byte-matches iter-6) |
| J-10 control-group honesty (refactor guard) | passing | passing (live) | evidence/J09-J10-system-health-after-refactor.png |
| J-01 dashboard | passing | passing (live) | dashboard render + /backtest scan summary |
| J-03 themes / J-04 sectors | passing | passing (live) | /backtest scan summary ranked-with-scores (latest + 2022-10-07) |
| J-06 coherence / J-15 snapshot-served | passing | passing | UI==API byte-match + keystone patch-to-raise tests |
| J-02, J-05, J-07, J-08, J-11 | passing | passing (carried; code paths untouched) | iter-8/7/6 evidence; J-07/J-08 invariants re-confirmed via live API |
| J-12 glossary, J-16 VCP | failing | failing (unbuilt — OUT OF SCOPE) | — |

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| No lookahead *(critical)* | OK | `compute_run_scorecard`/`backfill_run_forward_returns` measure only `forward_returns` (date>D), entry=`close_on(D)` (date≤D) — unit-proven (`test_backfill_run_is_no_lookahead_and_insert_only`) + source |
| Snapshots immutable *(critical)* | OK | INSERT-only into the append-only `forward_returns`; `models.py` git-clean; no UPDATE of any snapshot row — unit-proven (create-once tests) + git diff |
| Single source / no recompute in read path *(critical)* | OK | `compute_run_scorecard` READS stored `scanner_results` (bucket/setup/sector/rank verbatim) + `forward_returns`, reuses `_control_groups`; keystone patch-to-raise passes; FE cells == API byte-for-byte |
| On-demand snapshots create-once & lookahead-free *(critical)* | OK | `resolved_run` (iter-8) + idempotent `backfill_run_forward_returns` (2nd call inserts 0) — unit-proven |
| Honest forward-test for partial windows | OK | NA→`null`/`n=0`, low-sample ⚠; live all-NA latest + numeric 2022-10-07; no fabricated number |
| No fabricated data | OK | invalid as-of → explicit 400/400/422; "Backend unavailable"/empty states never synthesize figures |
| No magic numbers | OK | horizons/`min_sample`/`top_n` from `config.walk_forward`; `test_no_magic_numbers` green (scans `forward_testing.py`) |
| No order/execution path *(critical)* | OK | grep clean (only a `watchlist.py` comment explicitly disclaiming orders) |
| No secrets in source | OK | grep clean |
| Honest limitations (survivorship) | OK | label carried verbatim by the payload and rendered in the banner (live-confirmed) |

**Coherence:** COHERENCE-PASS — `/backtest` matches the iter-9-approved blueprint rows; the INSERT
formula is consolidated into one helper (`_insert_run_forward_returns`) and the display helpers into
one module (`forward-return.tsx`) — both reduce duplication. No structural veto.

## Next-Step Recommendation

**iter-11 at full depth — J-16 (VCP detection).** Build the config-driven Volatility Contraction
Pattern detector (progressively shallower pullbacks + volume dry-up into a pivot near the highs;
thresholds from `config`), computed **once per run, price+volume only, with date ≤ D (no-lookahead)**,
riding the **immutable snapshot row as a SEPARATE flag** ALONGSIDE the setup status — it must NOT enter
the setup-status enum and MUST NOT by itself promote a name to "Actionable" *(critical anti-goal)*. Add:
the VCP flag (+ pivot/invalidation level) on the stored row read identically on leaderboard + detail;
a **VCP filter** on `/stocks`; a VCP **badge** with reason + invalidation; and a **VCP-vs-non-VCP**
forward-return breakdown on System Health (with `n`, NA below `min_sample`) as a new forward-test
dimension. Unit-prove: VCP computed once (single source), no-lookahead, separate-from-status, and the
forward-test dimension reads stored flags verbatim. Then **J-12 (config-backed glossary / `/methodology`)**
LAST so it can document the VCP catalog entry — that iter adds a nav route and will need a
`blueprint.reapproval-requested`. A clean J-16 → 15/16; then J-12 → 16/16 and a legitimate
GOAL_ACHIEVED check.

Why full: J-16 is a new detected-pattern engine on the snapshot row + a leaderboard filter + a badge +
a detail surface + a System Health breakdown + a forward-test dimension + new unit tests, and it touches
a *critical* anti-goal (pattern-not-status) — well beyond lean scope.

**Runner-owner debt (NON-gating, NOT product/spec scope — unchanged across iters 3–10; flagged, not
re-litigated):** (1) the dedicated browser-qa SKIPped a **9th** consecutive time (frontend reported
down at `:3835`; **no evidence PNGs produced at all this time** — worse than iters 4–8 where QA mode-2
self-healed and persisted shots — so I produced the live evidence myself); (2) the **audit handoff is
missing a 9th** consecutive full-depth iter (`reports/audits/` still absent — and `docs/handoffs/...-audit.md`
absent). Durable fixes belong in `scripts/automation/*.sh` (own/await/self-heal the frontend; set
`CORS_ORIGINS` to the frontend port; emit the audit handoff), not in the spec.

## Halt Justification

Not halting. CONTINUE: J-14 newly passing (real progress), no regression (additive + a
behaviour-preserving refactor — J-13/J-09/J-10 live-confirmed unchanged), no critical anti-goal
violated, COHERENCE-PASS. Not GOAL_ACHIEVED — J-12 and J-16 are still `failing` (unbuilt by design).
Not STALLED — the next step (J-16) is fully specified and tractable, and this iter made concrete
progress. Not REGRESSION — nothing that was passing broke.
