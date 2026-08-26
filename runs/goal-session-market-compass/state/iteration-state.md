# Iteration State — market-compass

**After iteration:** 19 · **Date:** 2026-08-26 · **Verdict:** CONTINUE

## Journeys

3 passing (J-01 J-04 J-10) · 6 partial (J-02 J-03 J-05 J-06 J-09 J-11) · 2 failing (J-07 J-08) — 11 total. No journey tested this iteration (maintenance isolation forbade browser QA + replay); all statuses carried, not re-verified. Anti-goal ledger: 7 total, 0 unresolved.

## Active blockers

- **J-11 Stage E is the next AUTHORIZED step** (owner ruling 2026-08-26, commit `5fe72f5c`, items 1/7/8/9 approve D→G). Owner: dev. No new human approval is needed to start it.
- **App + browser lane stay OFF until Stage G passes** (ruling item 4 + Loop mechanics). Owner: human operator — keep `CHAIN_MAINTENANCE_ISOLATION=true` and `CHAIN_REQUIRE_FULL_DEPTH=true` on every resume.
- **Stage G design blocked until the stamp question is settled** (auditor B1): `engine_identity` `53d2ffd1…` is just the current engine's stamp and cannot prove attempt membership. Use the recorded set — `scanner_runs` ids **3148–3158**, created 2026-08-26 10:52:55.552946 → 10:53:02.010362Z — and assert no twelfth run carries that stamp. Owner: owner ruling in `docs/goal.md`.
- **Two live write paths still unguarded, deferred by ruling item 5:** `scanner.resolve_run` (`scanner.py:338-347`) and `data_manager`'s backfill. Post-Stage-G hardening. Owner: owner.

## Last 2 verdicts

- iter 19: CONTINUE — Stage D executed live and cleanly (11 runs, ids 3148-3158, one stamp); evaluator re-derived every figure read-only and cross-diffed the whole DB against iter-18's end sweep: exactly the 4 authorized tables changed. Nothing failed, so the ruling's STOP trigger never fired.
- iter 18: STALLED — boundary ACTIVE + guard ARMED achieved, but Stage D was not yet authorized.

## Do not redo

- **Stage D is DONE and verified** — never re-run `run_j11_stage_d_execute.py`, re-freeze the identity, or restamp any run. Evidence: `runs/goal-market-compass-iter-19/j11-stage-d-execute-*.json`.
- **Do not re-derive** raw-price immutability, manifest immutability, or the legacy/NULL run populations for iterations ≤19: `daily_prices` fingerprint `80441b37…` unchanged, all 24 manifests content-identical to the iter-16 certified baseline, identity split 34/3083/11 intact.
- **Do not create or re-arm** the `maintenance_boundaries` row — live, ACTIVE, exactly 11 dates, verified.
- **Do not touch** `apps/backend/app/api/*`, `scoring.py`, `sectors.py`, `compass.py`, `data_manager.py` — their untouched state is the only basis J-01/J-04/J-10 carry forward on.
- **The identity equality is settled, not a defect** — recomputed from disk, mathematically forced (provenance files last changed iter-12, `config.yaml` iter-4). See the Stage G blocker above instead.
- **J-04's screenshot is a known capture defect** (`evidence_makeup: true`) — re-capture as a passenger task when browser QA resumes, never as an iteration goal.
