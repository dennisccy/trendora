# Iteration 8 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

The keystone read-path consolidation landed cleanly: the five live read endpoints
(`/api/dashboard`, `/api/stocks`, `/api/stocks/{ticker}`, `/api/sectors`, `/api/themes`) plus
`/bars` and the watchlist now serve canonical values from the persisted **immutable snapshot** for a
resolved as-of date (computed once, then read from storage — never recomputed per request), and a
global top-bar as-of switcher time-travels the whole dashboard. **J-15** and **J-13** are newly
passing, verified directly from on-disk evidence + source. No previously-green journey regressed and
no critical anti-goal was violated; coherence is **COHERENCE-PASS**. This is *not* GOAL_ACHIEVED:
the goal was re-opened (commit `ed7712b`) with five new Must-haves and **J-12, J-14, J-16 remain
unbuilt by design** (explicitly out of scope this iter) → **CONTINUE**.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Daily dashboard | passing | passing | `TC-12-J13-dashboard-latest.png` (regime Risk-on 74.32, counts 0/8/1, top sectors+themes, breadth 65.57%, as-of 2026-05-28); QA TC-13 |
| J-02 Stock Leaderboard + filters | passing | passing | QA TC-13 (Technology filter 122→58 rows, all Technology) |
| J-03 Theme Leaderboard | passing | passing | themes served from stored `ThemeScoreRow`; engine untouched; historical themes re-point (Defense A/100 @2025-04-04) |
| J-04 Sector Leaderboard | passing | passing | sectors served from stored `SectorScoreRow`; engine untouched; historical sectors re-point (XLP/XLU defensive @2025-04-04) |
| J-05 Stock Detail | passing | passing | detail served from stored `record_json`; `/bars` slices `bars_asof(D)`; logic untouched |
| J-06 Score consistency (coherence) | passing | passing (strengthened) | list & detail BOTH read `stored_stock_rows` → byte-identical; unit `TC-04` at latest AND 2025-04-04 |
| J-07 Risk-Off suppresses Actionable | passing | passing | `TC-12-J13-dashboard-historical-2025-04-04.png` (Risk-off 6.30, **Actionable 0**); QA TC-13 both Risk-off runs Actionable=0 |
| J-08 Immutable run history | passing | passing | `models.py` untouched; `runs.py` untouched; `run_scan` create-once (resolver only APPENDED) |
| J-09 System Health evidence | passing | passing | `forward_testing.py`/`system_health.py` not re-pointed (out of scope), byte-identical untouched |
| J-10 Control-group honesty | passing | passing | forward-testing path untouched |
| J-11 Watchlist persistence | passing | passing | `_canonical_rows` reads the SAME latest stored snapshot rows `/api/stocks` serves; unit TC-05 |
| J-12 Glossary + inline | (new) failing | failing | OUT OF SCOPE this iter — `/methodology` not built |
| **J-13 Global as-of switcher** | (new) failing | **passing** (target) | `TC-12-J13-dashboard-historical-2025-04-04.png` + `-stocks-historical-2025-04-04.png` + indicator + md5-identical restore |
| J-14 Backtest scorecard | (new) failing | failing | OUT OF SCOPE this iter — `/backtest` not built |
| **J-15 Snapshot-served reads** | (new) failing | **passing** (target) | `TC-11-J15-stocks-latest.png`; keystone no-recompute test; warm API 20–100ms |
| J-16 VCP detection | (new) failing | failing | OUT OF SCOPE this iter — VCP detector/filter/breakdown not built |

**Score:** 13 / 16 Must-have journeys passing (J-13 + J-15 newly passing this iter; J-12, J-14, J-16
remain unbuilt by design).

## Verification (skeptical, evidence-grounded)

The dedicated browser-qa **SKIPPED an 8th consecutive time** (HTTP-000, frontend down at its probe);
QA mode-2 self-healed (booted backend on :8835 with `CORS_ORIGINS`, frontend on :3835) and persisted
**5 distinct evidence PNGs**. I reconciled every target claim from on-disk evidence + source, not
summaries:

- **J-13 (verified from PNGs I viewed directly):** the switcher genuinely re-points stored snapshots —
  dashboard regime **Risk-on 74.32 → Risk-off 6.30**, breadth **65.57% → 0.82%**, leadership rotates
  from semis (SOXX/WGMI/SMH; Semiconductors theme) to defensives (XLP/XLU/XLF; Defense theme); the
  stocks leaderboard top rotates **MU/ARM/MRVL → KTOS/NOC/PLTR**. The amber **"Viewing as-of
  2025-04-04 (historical)"** indicator + per-page "Data as-of 2025-04-04" render; reset-to-latest is
  **md5-identical** (`f353ee88…`) to the latest stocks view (clean restore). The defensive rotation on
  a Risk-off day is internally consistent — a real historical snapshot, not a fabrication.
- **J-15 (verified from source + test):** the keystone `test_repointed_handlers_serve_persisted_date_without_recompute`
  monkeypatches `score_stocks/score_regime/score_sectors/score_themes` (as `run_scan` references them)
  to **raise**, then asserts all four re-pointed handlers still serve a persisted date — proving they
  read storage, never recompute (a far stronger proof than served==stored value-equality). Warm API
  20–100ms (far under the ~1.5 s budget); `stored_stock_rows` is shared by list & detail → byte-identical.
- **Read-path regression (the iteration's real risk):** the `scanner.py` diff **only APPENDS** the
  resolver after line 173 — `run_scan` is untouched, so its iter-5/6 create-once / immutable /
  no-lookahead properties are inherited unchanged, and the iter-5 faithful-equality guarantee
  (stored == live for latest) makes the re-pointed latest payloads byte-identical to the former
  on-request compute. `models.py` is git-clean (immutability surface untouched).

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| No lookahead *(critical)* | OK | inherited from untouched `run_scan`; `/bars` slices `bars_asof(D)`; `test_resolve_run_on_demand_has_no_lookahead` + bars guard pass |
| Snapshots immutable *(critical)* | OK | `models.py` untouched; `test_resolve_run_create_once_then_immutable` (no UPDATE/no duplicate on 2nd view); INSERT-only `run_scan` |
| Single source of truth *(critical)* | OK | serving layer reads stored rows, computes nothing; coherence Part A PASS; list==detail==watchlist from same stored row |
| No recompute in read path *(critical)* | OK | keystone monkeypatch-to-raise test; all live-engine imports removed from the 5 endpoints + watchlist |
| On-demand snapshots immutable & lookahead-free *(critical)* | OK | `resolve_run` create-once via `run_scan` (bars ≤ D); unit-proven |
| Risk-Off gates Actionable *(critical)* | OK | historical 2025-04-04 Risk-off shows **Actionable 0** (PNG); QA TC-13 both Risk-off runs Actionable=0; scanner untouched |
| No magic numbers | OK | engine raises semantic `AsOfError` (no status literal); HTTP map lives in serving layer; `test_no_magic_numbers` passes |
| No fabricated data | OK | bad as-of → explicit 4xx (future→400, before-history→400, unparseable→422, no-data→503); runs count 11→11 unchanged (QA TC-03) |
| No order/execution path *(critical)* | OK | grep matched only a watchlist comment disclaiming orders; no broker/order code |
| No secrets in source | OK | grep clean |
| Honest limitations surfaced | OK | breadth labelled "universe-relative" on both views (PNGs) |

**Coherence:** `COHERENCE-PASS` (read path consolidated onto the one canonical persister; J-06
byte-identity preserved; watchlist moved onto the same source as `/api/stocks`; no new route, no nav
change). No structural veto.

## Next-Step Recommendation

**iter-9 at full depth — J-14 (Backtest / Time-Machine + per-date forward-test scorecard).** It
builds directly on this iteration's as-of resolver (`resolve_run`) plus the existing forward-testing
engine (iter-6): pick a historical as-of date, render its full as-of scan from the canonical snapshot,
and show a per-date forward-test scorecard — realized 1/5/10/20/60-day returns, excess vs
SPY/QQQ/sector, and a random same-sector control — computed **only from seed bars after D**
(no-lookahead), with sample size and partial/NA horizons shown honestly. This adds a new `/backtest`
nav entry, so it will need `blueprint.reapproval-requested`. Unit-prove the post-D forward boundary
on the per-date scorecard (reuse the iter-6 `bars_after` date>D partition). After J-14: **J-16 (VCP
detected pattern)** then **J-12 (config-backed glossary incl. the VCP entry)** finish the new round.

**Runner-owner debt (NON-gating, NOT product — now chronic across iters 3–8, do not re-attempt via
spec):** (a) the dedicated browser-qa has SKIPPED on the HTTP-000/CORS flap **8 consecutive
iterations** — fix it in the runner (own/await/self-heal the frontend AND launch the backend with
`CORS_ORIGINS=http://localhost:<frontend-port>`); (b) the audit handoff has been **missing 8
consecutive full-depth iters** (`reports/audits/` still does not exist) — emit it from the runner
script, not the DoD.

## Halt Justification (if halting)

Not halting. CONTINUE: two target journeys (J-13, J-15) newly passing, no regression, no critical
anti-goal violated, COHERENCE-PASS — but three Must-haves (J-12, J-14, J-16) remain unbuilt by
design, with a clear, tractable next step (J-14). Not GOAL_ACHIEVED (not all 16 pass); not REGRESSION
(nothing previously-green failed); not STALLED (clear progress + next work); not ESCALATE (already
full depth).
