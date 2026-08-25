# Iteration State — market-compass

**After iteration:** 16 · **Date:** 2026-08-25 · **Verdict:** STALLED

## Journeys

3 passing (J-01 J-04 J-10) · 6 partial (J-02 J-03 J-05 J-06 J-09 J-11) · 2 failing (J-07 J-08) — 11 total. Iter-16 ran under MAINTENANCE ISOLATION (browser QA + replay lane forbidden by contract), so NO journey was tested and every status is carried, not re-verified. J-11 re-stamped `spec_hash` `54e9cdd8…`→`e7927ff5…` (owner's two 2026-08-25 rulings, committed `346ed65a`). Anti-goal ledger: 7 total, **1 unresolved (AG-8, minor)**.

## Active blockers

- **OWNER DECISION (human) — Stage D.** `J-11 STAGE D READY: YES` (first YES this session) · `AUTHORIZED: NO`. The owner's 2026-08-25 ruling ends this step verbatim: "Even if the subsequent readiness evaluation returns `READY: YES`, STOP for owner review… Stage D remains forbidden until a later explicit owner instruction." Options: (a) instruct Stage D + `--resume`; (b) order a non-destructive tidy-up run first; (c) change the plan in `docs/goal.md`.
- **OWNER AUTHORIZATION (human) — the pre-boot guard is INERT on the live DB (headline; auditor B2, evaluator-confirmed).** Built correctly and wired at `warmup.py:107` inside `ensure_latest_snapshot` before `run_scan` — but `register_j11_incident_boundary` has NO production caller (grep: only its definition, its tests, 2 docstrings), `maintenance_boundaries` does not exist in the live file (still exactly 24 tables), and `evaluate_boundary_for_date` returns `blocked=False` on an empty table (`j11_preboot_guard.py:143-145`). So booting the backend today still writes a `ScannerRun` onto 2026-08-12. The ruling's literal "proven on disposable test state" gate IS met; its stated purpose is NOT achieved in production ⇒ **maintenance isolation stays ACTIVE**. Arming it needs a live write outside the two-cell authorization. Danger window = now until Stage D completes (`run_scan` is create-once, so the boot path self-heals once the 11 dates hold runs).
- Non-blocking riders for the next run, none can change the gate's answer: (1) re-run readiness WITH `volume_override` at `run_j11_iter16_stage_d_readiness.py:247-248` — the honest label is **AVB-A**, not the recorded AVB-B, and the handoff's "correcting AVB shifts other tickers' percentiles" claim is a scale artifact (A/B = exactly 2.7930001226 as run vs 1.0000002 with the volume supplied) — **do not inherit it**; (2) bound the AG-8 whole-table `select(MaintenanceBoundary)` at `j11_preboot_guard.py:143`; (3) add a test named for "table present, empty, latest date is an incident date" (auditor T1); (4) `build_review_packet` must union untracked files — it advertised "Files changed: 5" while hiding all 7 new source files (auditor P1); (5) iter-16's code/tests/evidence were still untracked at scoring time.

## Last 2 verdicts

- iter 16: STALLED — owner-ordered sequence executed in order and stopped where the owner said to; the ONE authorized write (AVB volume 1,549,436→554,757 and 10,350,885→3,706,010) proven isolated by the evaluator's own re-hash of all 3.31M price rows; `READY: YES`; guard inert on the live DB.
- iter 15: STALLED — AVB convention settled on real fetched evidence as AVB-C (`READY: NO`); every route past it owner-owned; zero live DB writes; auditor B1 (boot-path hazard) escalated above it.

## Do not redo

- **The AVB two-cell volume correction** — EXECUTED and verified in iter-16; authorized ONCE and now spent. `daily_prices` is certified immutable again at the NEW baseline. Never re-run `run_j11_avb_correction.py`.
- **Stage C bounded clear** (iter-13) and **Stage B1** (manifest FK migration + `basis_disclosure` fail-closed fix, iter-10/11) — complete and closed; owner-accepted 4-item DDL residual; no second live rewrite. Iter-11's REGRESSION verdict stands (A14).
- **J-10** — CLOSED by owner ruling; never reopen, never retry EA/EQR. Its AVB dollar-volume defect is now CORRECTED in the raw layer under the separate 2026-08-25 ruling — that is not a reopening.
- **AG-9 dated exception #2** (AVB fetch) — CONSUMED and EXHAUSTED by iter-15 (`runs/goal-market-compass-iter-15/j11-avb-provider-fetch-evidence.json`). Any further fetch needs a NEW dated amendment. Iter-16 made zero network calls.
- **Evidence dirs iter-9…iter-16** — byte-preserved historical evidence; iter-15's `j11-stage-d-readiness.json` (AVB-C, `ready: false`) stays historically accurate for the PRE-correction state, never edited.
- **Hash recipes, settled** — `sha256` over `repr(row)` per row via `sqlite3 mode=ro`: AVB OHLC-only `757c3c63…c8fd3`, AVB other-dates `53bca571…c14f`, non-AVB `78146554…4997`, manifest row-dump `bb954b60…6d2a2e6`, manifest DDL `9f653c81…c501ee`. Quote the recipe beside any fingerprint.
