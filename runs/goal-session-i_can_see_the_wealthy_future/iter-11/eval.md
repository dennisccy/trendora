# Iteration 11 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

J-16 (VCP — the product's first detected price pattern) landed cleanly and is the iteration's target
journey: a config-driven `detect_vcp` rides each immutable snapshot row **alongside** (never replacing)
the setup status — filterable + explained on `/stocks`, identical badge+card on `/stocks/[ticker]`, and
a VCP-vs-non-VCP forward-return breakdown on `/system-health`. I verified it to gold standard despite a
**10th consecutive dedicated browser-qa SKIP** (HTTP-000 on :3835) — but unlike iter-10, BOTH QA mode-2
self-healed (3 md5-distinct PNGs + 17/17 functional TCs) AND the developer self-produced 4 PNGs, so I
reconciled from viewed evidence + my own fast-test run + direct source reads. **15/16 Must-haves pass.**
Not GOAL_ACHIEVED only because J-12 (`/methodology` glossary) is unbuilt **by design** (sequenced last so
it can document the VCP catalog entry).

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| **J-16** | failing (unbuilt) | **passing** | `reports/evidence/goal-i_can_see_the_wealthy_future-iter-11/{01-leaderboard-vcp-filtered,02-detail-STX-vcp,03-system-health-by-vcp,04-detail-ORCL-vcp}.png` (md5-distinct); keystone `test_vcp_served_from_storage_not_recomputed_keystone`; `test_vcp_is_a_pattern_not_a_status` |
| J-02 | passing | passing (re-verified live) | leaderboard PNG (VCP filter 4/122; ranking unchanged) + QA TC-17 (Setup=Extended→11/122; sector filter narrows) |
| J-05 | passing | passing (re-verified live) | STX + ORCL detail PNGs (chart + 3 scores w/ components + setup + invalidation + VCP card) |
| J-06 | passing | passing (re-verified live) | STX 91.53/32.11/51.87 & ORCL 53.60/47.81/45.46 detail==leaderboard; keystone asserts `detail.row.vcp == list-row.vcp` |
| J-07 | passing | passing (re-proven, data) | NEW `test_risk_off_run_vcp_flagged_rows_stay_watchlist_not_actionable`; `setups.py` byte-unchanged; flagged rows are Extended/Avoid (none Actionable) in evidence |
| J-08 | passing | passing (re-confirmed, source) | `models.py` only APPENDs `is_vcp`; `forward_returns` separate INSERT-only; `is_vcp==record_json.vcp.flagged` mirror test |
| J-09 | passing | passing (re-verified live) | system-health PNG: by-bucket (A +6.00% n=24⚠…) / by-setup / by-regime / excess panels intact alongside new by_vcp |
| J-10 | passing | passing (re-verified live) | system-health PNG: control-group comparison (top-ranked / random-same-sector / SPY / QQQ / sector ETF) intact |
| J-13 | passing | passing (re-verified) | QA TC-17 (global as-of switcher, 11 dates, re-points to 2022-10-07); switcher control visible in leaderboard PNG; as-of/snapshot code untouched |
| J-15 | passing | passing (re-proven, source) | keystone patch-to-raise proves read path serves stored (incl. VCP); `snapshot_serving.py` untouched |
| J-01 | passing | passing (carried) | dashboard code/endpoint untouched; deterministic DB rebuild reproduced identical canonical values (latest Risk-on; A +6.00% n=24) |
| J-03 | passing | passing (carried) | `themes.py`/`score_themes` untouched; DB rebuild reproduces |
| J-04 | passing | passing (carried) | `sectors.py`/`score_sectors` untouched; DB rebuild reproduces |
| J-11 | passing | passing (carried) | watchlist code untouched (`models.py` Watchlist INSERT/DELETE intact) |
| J-14 | passing | passing (carried) | `backtest.py`/`compute_run_scorecard` untouched (explicitly out of scope); DB rebuild reproduces forward_returns |
| J-12 | failing | failing (unbuilt **by design**) | OUT OF SCOPE this iter — `/methodology` sequenced NEXT so it can document the VCP entry |

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| VCP is a pattern, not a status *(critical)* | OK | `setups.py` byte-unchanged; `"VCP"∉ALL_STATUSES`; forced-flag-every-name → setup statuses byte-identical (`forced_status==baseline`); risk-off flagged rows stay `Risk-off-watchlist`; live: all 4 flagged are Extended/Avoid |
| No lookahead *(critical)* | OK | `detect_vcp` reads ONLY the passed as-of series (date ≤ D) — structurally cannot see future bars; `vcp` rides `record_json`, covered by `test_run_scan_no_lookahead` |
| Snapshots immutable *(critical)* | OK | `models.py` adds ONLY the append-only `is_vcp` column; no existing row UPDATEd; `forward_returns` separate; `is_vcp` faithfully mirrors `record_json.vcp.flagged` (mirror test) |
| Single source / no recompute in read path *(critical)* | OK | `api/`+`main.py` empty diff (no new endpoint); keystone patches `detect_vcp`+`score_*` to RAISE → reads still serve stored `vcp`/`by_vcp` |
| On-demand snapshots immutable & lookahead-free *(critical)* | OK | `run_scan` only adds the mirror; create-once/immutable/no-lookahead inherited unchanged |
| Risk-Off gates Actionable *(critical)* | OK | risk-off+VCP test: Actionable=0, flagged rows watchlist-only |
| No order/execution path *(critical)* | OK | brokerage/order grep empty |
| No magic numbers | OK | `patterns.py` in `CALC_FILES`; `8`/`35` added to forbidden ints; every threshold from `config.patterns.vcp` (typed `VcpCfg` validated) |
| No fabricated data / honest partial windows | OK | not-flagged → `pivot=None`/`level=None` + honest reason; `by_vcp` n=27 flagged ⚠ (<min_sample 30); survivorship label present |
| Scores explainable | OK | VCP badge carries reason + pivot + invalidation note (never a bare flag) |
| No secrets in source | OK | hard-coded-secret grep empty |

**Coherence:** COHERENCE-PASS (no structural veto; advisory notes only — no consolidation work handed forward).

## Next-Step Recommendation

**iter-12 at full depth — J-12 (`/methodology` config-backed glossary + inline setup/pattern tooltips),
the final Must-have.** Build a single config-backed catalog (setup statuses + the VCP pattern entry, each
with plain-language meaning + the exact config thresholds + a worked example) surfaced as (a) a new
`/methodology` nav route and (b) inline info tooltips on every setup/pattern badge — so an entry added to
config appears in both places with no code change (the VCP reason/thresholds are already config-backed to
make this trivial). It adds a **new nav route → requires `blueprint.reapproval-requested`**. Pair it with a
**full 16-journey regression sweep + full-product coherence** so the next evaluation can legitimately reach
GOAL_ACHIEVED (16/16). Full depth (new route + new IA home + reapproval + the goal-completing sweep is well
beyond lean scope).

**Runner-owner debt (NON-gating, chronic — runner-script scope, NOT product; spec text proven ineffective
across iters 3–11):** (1) dedicated browser-qa SKIPped a **10th** consecutive time (HTTP-000 on :3835 —
the runner probed `GET /health` (404) instead of the canonical `/api/health` (200) and tore both services
down before browser-qa ran); (2) the audit handoff (`reports/audits/` / `docs/handoffs/...-audit.md`) is
missing a **10th** full-depth iter (`status.json` `current_step=qa_complete`, `next_action=audit` — the
audit step never executed). Durable fixes belong in `scripts/automation/*.sh`. Neither affected this verdict.

## Halt Justification (if halting)

Not halting. CONTINUE: J-16 newly passing (progress), one tractable Must-have remains (J-12), no regression,
no critical anti-goal violation, COHERENCE-PASS. Not GOAL_ACHIEVED — J-12 is `failing` and the rules forbid
GOAL_ACHIEVED while any Must-have is not `passing`.
