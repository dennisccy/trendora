# Iteration 39 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** lean

## Summary

iter-39 is the FULL-depth fix of the iter-38 J-97 cache-staleness defect, and the fix is genuinely correct at the backend cache layer: a `SCHEMA_VERSION = "s1"` payload-schema token is folded into the `MarketPhaseCache` key via a new `_cache_version()` helper (`f"{_dataset_version(session)}|{SCHEMA_VERSION}"`), applied to BOTH `market_phase_cached` and `retrospective_cached`, so every pre-iter-38 bare-stamp row (missing `timeline_full`) becomes a guaranteed MISS and is recomputed once WITH the field — with every served value byte-identical (verified by genuine cache-HIT-probing unit tests, 16 green). BUT browser-QA was SKIPPED entirely (Chrome MCP CDP timeout, no Playwright fallback, ZERO screenshots, empty evidence dir), so there is NO live rendered proof the J-97 bottom pane now populates or that the J-98 at-a-glance restructure renders/expands. Per the strict standing rule (a UI journey is not marked passing without positive LIVE render evidence — iter-17/25/30/36), J-97 cannot flip to passing and J-98 cannot flip to passing on inference; this is the established iter-36→37 lean-live-reverify path, not a regression and not a stall.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-97 (two-pane synced cross-view) | failing (iter-38, live empty pane) | **failing — cause fixed at API/cache layer, byte-identity proven; NO live render evidence (browser-QA SKIPPED)** | dev handoff + `git diff market_phase.py` + `test_market_phase.py::test_cache_hit_on_old_schema_row_now_serves_timeline_full` (PASS); QA TC-01 PASS; **NO screenshot — evidence dir EMPTY** |
| J-98 (Dashboard at-a-glance restructure) | partial (iter-38) | **partial — held (embeds the now-cause-fixed J-97 chart); NO live render evidence (browser-QA SKIPPED)** | QA TC-07..TC-10 SKIPPED (Chrome MCP timeout); **NO screenshot** |
| J-87 (Market Phase & Severity card) | passing (iter-37) | passing (carried — `?full=false` card byte-identical; `test_card_payload_byte_identical_after_schema_fix` PASS) | iter-37 UT-08-dashboard.png + byte-identity test |
| J-88 (forward Hamilton P(bear)) | passing (iter-37) | passing (carried — card payload byte-identical) | iter-37 evidence + byte-identity test |
| J-89 (phase-history timeline + fenced retrospective) | passing (iter-34) | passing (carried — `retrospective_cached` switched to `_cache_version` but `test_retrospective_payload_byte_identical_after_schema_fix` PASS: smoothed/true-bear fence unchanged) | iter-34 evidence + retrospective byte-identity test |
| J-90 (recovery-turn signal + edge study) | passing (iter-34) | passing (carried — no diff touches the recovery path) | iter-34 evidence |
| J-18 (exactly one date control — CRITICAL) | passing (iter-37) | passing (carried — backend-only 2-file diff adds no date `useState`/`setAsOf`/window-keydown; frontend byte-unchanged) | iter-37 UT-05-stocks-loaded.png + diff inspection |
| J-07 (Risk-Off → 0 Actionable — CRITICAL) | passing (iter-37) | passing (carried — diff touches no scoring/regime/scanner/gate path) | iter-37 UT-08-dashboard.png + diff inspection |
| J-06 (single source of truth) | passing (iter-37) | passing (carried — no canonical value recomputed; `timeline_full` read verbatim from `_timeline_series`) | iter-37 UT-06-nvda-detail.png |
| J-44/J-49 (top pane / regime card) | passing (iter-31) | passing (carried — top pane untouched) | iter-31 dashboard-fullpage.png |
| J-13/J-43/J-01 (as-of / deep-link / dashboard) | passing (iter-31) | passing (carried — no frontend/route change) | iter-31 evidence |
| J-99 (membership-timeline pagination/filter) | ABSENT | ABSENT — unbuilt buildable Must-have (no positive evidence) | — |
| J-100 (bounded-resource backend) | ABSENT | ABSENT — unbuilt buildable Must-have (no positive evidence) | — |
| J-22 / J-23 / J-24 | unknown (blocked-NA) | unchanged blocked-NA — data-walled, NON-VETOING (goal.md:105-108) | — |

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| No lookahead | OK | `timeline_full` read verbatim from the existing `_timeline_series` (strictly causal per point); no new derivation. The crux test asserts byte-identity to a fresh `compute_market_phase` — no-lookahead intact. |
| Single source of truth | OK | `_cache_version()` is a KEY-DERIVATION helper (returns a cache-key string), NOT a value; `timeline_full` still computed exclusively by `compute_market_phase`/`_timeline_series` and served verbatim from the one endpoint (coherence Part A PASS). No second computation, no client-side severity/phase/P(bear) math. |
| No recompute in the read path | OK | The cache stays a pure performance layer; only the KEY string changed. One-time bounded recompute on the first HIT-miss per previously-cached as-of (one market-phase compute, not a scan). |
| No fabricated data | OK | An as-of with no causal phase history serves an honest-empty `timeline_full` (empty list), not a fabricated series (test_market_phase error-case legs). |
| Snapshots are immutable | OK | No scanner_run / ScannerResult / snapshot touched; diff is the engine cache helper + tests only. |
| Chart pane-zoom is a view transform, not a date control | OK | No frontend diff; no new date `useState`/`setAsOf`/window-keydown added (grep clean). The synced-zoom from iter-38 is unchanged. |
| No magic numbers | OK | `SCHEMA_VERSION = "s1"` is a string cache token in the data-providers/cache layer, not a calculation literal; no float literal in calc code. The lone ever-recorded violation (iter-20 minor magic-number) stays resolved since iter-21. |
| Risk-Off must gate Actionable | OK | Diff touches no scanner/gate path. |
| Scores must be explainable | OK | No score path touched. |

**Coherence:** COHERENCE-PASS (iter-39 coherence.md — surgical backend cache-key correctness fix; no Data Contract or IA violation; no advisory issues). No structural veto.

## Next-Step Recommendation

iter-40 **LEAN live re-verification** (NO code rework — the backend cache fix is correct, byte-identity proven, 16 targeted tests green). Bring up backend `:8835` (WAIT for `GET /api/health` "ready" — the warm-up precomputes the phase cache; the first `?full=true` per previously-cached as-of pays one bounded recompute by design), frontend `:3835`, Chrome `:9222`; **fall back to Playwright if Chrome MCP CDP is unreachable** (iter-34/iter-37 precedent — this is the SAME Chrome MCP CDP-timeout that blocked iter-38, so plan the Playwright fallback up front). `md5sum` the evidence dir FIRST and REJECT any blank/skeleton/byte-identical frame.

Capture on LIVE non-skeleton evidence:
- **J-97** — bottom pane populated at the LIVE current as-of (phase-colored bands + 0–100 severity line + filtered P(bear) line + as-of marker); the synced zoom as **two byte-DISTINCT before/after frames** (UT-04/UT-10, skipped every iter so far); an early-as-of (no causal phase history) honest-EMPTY bottom pane (never a fabricated severity/phase/probability). Confirm `GET /api/market-phase?full=true` at the live current as-of returns `timeline_full` on a cache HIT (re-confirm against the running backend, not a fresh-compute date — the iter-38 masking trap).
- **J-98** — first-paint compact at-a-glance (Market Regime label+score; Market Phase & Severity label+0–100 severity+band+filtered P(bear)), each with its named component breakdown reachable (no bare number); the More-detail expand (UT-12); an as-of change updating BOTH compact figures (UT-18).

Required-still-passing LIVE smoke: J-18 (0 native `input[type=date]`, CRITICAL), J-07 (Risk-Off → 0 Actionable, CRITICAL), J-06 (compact figures == served; pane-1 series == card series for the overlap window — single source), J-44/J-49 (top pane unchanged), J-87/J-88 (card phase/severity/P(bear) unchanged), J-89/J-90 (timeline + retrospective fence + recovery-turn unchanged).

After J-97 flips to passing and J-98 flips to passing on LIVE rendered evidence with COHERENCE-PASS, build **J-99 (lean)** then **J-100 (full)** — they are unbuilt buildable Must-haves and block GOAL_ACHIEVED (iter-22 lesson). Only after J-97..J-100 all pass with a GREEN full suite + COHERENCE-PASS is the next evaluation a GOAL_ACHIEVED candidate (J-22/J-23/J-24 stay honestly blocked-NA, non-vetoing per goal.md:105-108).

Suite gate (iter-11/29/37 lessons): the iter-39 full suite was at ~87%+ with ZERO failures at evaluation time but had NOT flushed the terminal `0 failed, EXIT 0` line; it is NOT load-bearing for this CONTINUE (iter-39 is not a GOAL_ACHIEVED candidate). For any future GOAL_ACHIEVED candidacy, gate on the FLUSHED line (nohup-async via the pump; never block the evaluator on the in-flight stream) and re-run any single `test_warmup.py` / `test_data_manager_jobs_pipeline.py` F in isolation before attributing it.

## Halt Justification (if halting)

N/A — not halting. CONTINUE.
