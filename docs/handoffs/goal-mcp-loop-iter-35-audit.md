# goal-mcp-loop-iter-35 Audit Report

**Date:** 2026-07-14
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-21 (B-304 overlap check) is genuinely delivered: a new PURE `app.engine.drift` module byte/fixed-precision compares a fetch's returned bars against the committed seed CSVs, persists a single artifact, and that one artifact is re-read verbatim by both `compute_preflight` (a new 4th `drift` component that forces DEGRADED) and the additive `GET /api/data` field feeding the `/data` `DriftReportPanel`. The single-source contract, determinism (deterministic `prog.end` anchor, never `date.today()`), no-auto-repair, no-key-leak (structural — `Bar` carries no credential field), graceful degradation, and the J-20 non-regression (absent artifact ⇒ drift `ok` ⇒ GO unchanged) are all verified in the actual code and by tests I re-ran myself. Three GAP-level limitations remain (documented below); none compromises the phase goal in the current deterministic committed-seed deployment, so no fix was applied.

---

## 2. Findings

### Backend Findings

**B1 — GAP (observation): overlap window is trimmed over the last N *fetched* bars, not the last N bars *common to fetch and seed* — `apps/backend/app/engine/data_manager.py:2270-2278`**
The spec's IN SCOPE wording is "take the last `overlap_days` dates COMMON to both the fetch and the committed seed." The pure `build_drift_report` (`drift.py:100-105`) implements exactly that and is correct. But the integration path pre-trims the accumulator in `_run_chunked_fetch` (`overlap_sink`, `del bucket[:-overlap_days]`) to the last `overlap_days` *fetched* bars *before* `build_drift_report` intersects with the seed. When a fetch extends more than `overlap_days` trading days *beyond* the seed's last date, the newest `overlap_days` fetched bars are all beyond-seed dates, so the in-seed overlap dates get trimmed away and the comparison sees fewer (or zero) common dates.
- **Reachability:** Not reachable in the current deployment — the committed seed *is* the latest data (the board is never behind the seed) and goal-mode runs no live provider that adds dates past the seed. It requires a real live provider fetching a window that reaches >`overlap_days` (default 20) trading days past the committed seed's last date.
- **Blast radius even when reached:** Drift is still *detected* in the realistic Stooq whole-history re-adjustment case, because a whole-history back-adjustment also shifts the newest common date, which is always compared — the trimming reduces the *count* of listed dates, not the detection. A total miss needs a re-adjustment localized to *only* older overlap dates *and* a beyond-seed fetch — contrived.
- **Not fixed:** GAP-level and deployment-unreachable; a correct fix (bounding the accumulator by the seed's date range) is non-trivial because the accumulator cannot see the seed's dates at accumulation time, and a looser bound risks the anti-goal-#8 memory ceiling that caused the iter-24/26 crashes. Fixing it here would be scope creep on a working implementation. Recommend a bounded follow-on if a live provider that can outrun the seed is ever wired in.

**B2 — GAP (observation): no regression test asserts the API key/provider URL is absent from the written drift artifact (anti-goal #7) — `apps/backend/tests/test_data_manager_jobs_pipeline.py` (drift wiring block ~L552-668)**
Already raised by the reviewer (MINOR) and QA (TC-23). I confirmed the code is structurally safe: the `Bar` dataclass (`app/data_providers/base.py:31-39`) has only `date/open/high/low/close/volume` — no credential field — and the persisted report dict is built solely from those bars plus `overlap_days`, `prog.end.isoformat()`, and the constant `"adjustment_seam"`. The session key never enters the artifact; `_check_drift`'s error path additionally runs `scrub(...)` before `_record_error`. So this is a missing hardening test, not a defect. Not fixed (GAP; would be additive test-only work the reviewer already logged for follow-up).

### Frontend Findings

**F1 — OBSERVATION: `user-visible-changes.md` describes the card's explanatory copy as a hover "tooltip," but it renders as always-visible static text — `reports/phase-goal-mcp-loop-iter-35-user-visible-changes.md:14`**
Flagged by the ux-regression reviewer. The real behavior (`PanelTitle` `hint` rendered as a plain `<p>`) is strictly *more* discoverable than a hover tooltip, so the net user effect is positive. Documentation-accuracy nit only; the component itself is correct.

### Test Findings

**T1 — OBSERVATION: browser-qa induced the drift/clean/unreadable UI states by writing the drift artifact directly, not by driving the `/data` "Fetch" control end-to-end — `reports/phase-goal-mcp-loop-iter-35-ux-regression.md:37`**
The full `operator clicks Fetch → live provider returns re-adjusted bars → job completes → card updates` click-path was not captured in a single browser observation. It is, however, proven in two halves: the fetch→artifact half by the integration test `test_drift_stage_writes_report_on_completed_fetch_end_to_end` (a real fetch through `_run_job` asserting exact symbol + dates), and the artifact→UI half by browser-qa's direct-injection tests (UT-03/04/05/06) plus the banner test UT-07. Acceptable decomposition; a live click-path spot-check is worth a future QA pass but is not blocking.

**T2 — OBSERVATION: the inline regression-replay report was not produced.** The spec's own NOTES pre-authorize the iter-36 lean-verify fallback for this (a `run-phase.sh` structural gap, not a code defect), and the reviewer scored it accordingly. Required-still-passing journeys were re-verified via browser-qa (J-20/J-13/J-01/J-05) and the wiring tests (J-16) instead.

---

## 3. Domain Assessment

The core domain logic is correct and faithful to B-304's binding intent.

- **Comparator (the B-304 trap):** `_fixed(value) = f"{value:.6f}"` with exact string inequality — a genuine fixed-precision compare matching the seed CSV's own precision, never `abs(a-b) < eps`. `test_small_price_delta_is_flagged_never_smoothed_by_a_tolerance_window` (a 1-cent delta) and `test_mismatch_in_any_single_ohlcv_field_is_sufficient` lock this in and would fail loudly if anyone "simplified" it to a tolerance window. Verified by re-running: 13/13 in `test_drift.py`.
- **Single source:** both readers call `drift_module.read_drift_report()` (`readiness.py:323`, `api/data.py:145`). No recompute, no second parse path. Confirmed by reading both.
- **Determinism / no key leak / no DB scan on the poll:** reference is `prog.end.isoformat()` (deterministic job parameter); the artifact holds only OHLCV-derived data; `compute_preflight` reads the drift artifact as a tiny-file read (mirrors the existing `_ledger_file_ok` integrity component), never a DB query. All confirmed in code.
- **Fetch-pipeline gating (the safety-critical surface):** `_check_drift` runs only inside the fetch branch, gated `overlap_sink is not None and prog.status != "resumable"`, and is unreachable on the `skip_fetch` resume-at-backfill elif. The bounded per-symbol accumulator (`del bucket[:-overlap_days]`) respects the anti-goal-#8 memory lesson. The 4 wiring tests (`test_drift_stage_*`) — which I re-ran (4/4 passed) — prove it fires on a completed fetch, stays inert on a resumable pause (`read_drift_report() is None`), and does not re-run on a skip-fetch resume (artifact byte-stable under a telltale provider).
- **J-20 non-regression:** absent artifact ⇒ `_apply("drift", True, …)` ⇒ verdict/reasons unchanged. Note the DoD's "`GET /api/health` byte-identical" phrasing is imprecise — the payload does gain the (spec-mandated) 4th `drift` component; the load-bearing property (verdict stays GO, `reasons` stays empty, servability/freshness/integrity untouched) holds and is asserted by `test_preflight_fixture_matrix` and `test_health.py`.

**Independent verification I ran this pass** (TMPDIR-isolated): `test_drift.py` 13/13; `test_data_manager_jobs_pipeline.py -k drift` 4/4; `test_api_data.py -k drift` 2/2; `test_readiness.py` ReadinessCfg validation subset 5/5. The `config.py` diff is purely the drift additions (no entanglement with the — now-gone — stray iter-26 WIP), and the dev handoff's three stray `.iter35-*.tmp` probe files are already deleted. The heavy `loaded_engine`-backed `compute_preflight` drift assertions match my direct code trace exactly and were independently reported green by QA (24/24) and re-derived by the reviewer against a light engine.

---

## 4. Fixes Applied During This Audit

None. Every finding is GAP- or OBSERVATION-level; per the auditor rules these are documented as known limitations rather than fixed (fixing them would be scope creep, and the B1 accumulator change specifically risks the anti-goal-#8 memory ceiling on a working implementation).

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | No code changes made during this audit. |

---

## 5. Recommended Next Step

**Proceed.** J-21's binding acceptance is met with journey-level browser evidence (ux-regression PASS) and passing unit/integration tests; the phase goal — a silently re-adjusted board becomes visible and blocks GO — is achieved. Carry these into the session's follow-on (the pre-authorized lean iter-36 or the backlog):
1. The regression-replay report (T2) — close via the iter-36 lean-verify pass already anticipated by the spec.
2. Add the anti-goal-#7 artifact-scrub regression test (B2) — cheap, additive hardening.
3. If/when a live provider that can fetch past the committed seed is wired in, revisit the overlap-window accumulator bound (B1) so the compared window is the last N *common* dates, not the last N *fetched* bars — with a memory bound that still honors anti-goal #8.
