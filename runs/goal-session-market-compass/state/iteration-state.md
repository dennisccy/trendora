# Iteration State — market-compass

**After iteration:** 6 · **Date:** 2026-08-20 · **Verdict:** ESCALATE

## Journeys

2 passing (J-01 J-04 — carried on durability, NOT re-verified) · 5 partial (J-02 J-03 J-05 J-06 J-09, plus target J-10) · 2 failing (J-07 J-08) — 10 total

## Active blockers

- **J-10 recovery, now UNBLOCKED — do this next.** Stooq serves a JS proof-of-work challenge; all 587 requests 404'd. Owner amended `docs/goal.md` mid-iter-6: J-10 step 2a + the AG-9 vendor addendum authorise **`yahoo`** for these two dates only. Owner: dev. Change `apps/backend/app/engine/j10_recovery.py:83` (`RECOVERY_SOURCE`), then BUILD step 2a's fail-closed adjustment-convention check (read-only comparison fetch, held in memory, never written; disagree or can't check ⇒ write nothing and stop). Label restored rows `yahoo`; make no vendor-interchangeability claim anywhere.
- **Data still damaged.** `daily_prices` max 2026-08-10; 0 rows for 2026-08-11/12; `GET /api/compass?as_of=2026-08-12` = HTTP 400. goal.md Loop-mechanics insert #2 still gates every lane until J-10 verification passes.
- **Depth demotion is a live hazard.** iter-6 spec said `full`; engine ran `lean`; that enabled the forbidden browser-QA replay against the damaged DB (quarantined at `reports/qa/goal-market-compass-iter-6-evidence/INVALID-damaged-database.md`) and skipped the audit lane. Next iteration MUST be full.
- **Host safety.** A second goal-mode engine shares this 26.7 GB host and it froze once on two concurrent backends. Sequence backends; never two at once. Owner: dev.
- **Owner questions, none blocking:** J-09 accept 3.44 GB vs re-bound `_BarCache.prefill` vs new target; J-06 step 2 "underlying run unavailable" wording; J-01 step 1-2 rewording; empty "next-session focus" acceptability; NEW — include MNST in the retry? (excluded from the 587 on conflicting evidence).

## Last 2 verdicts

- iter 6: ESCALATE — J-10's mechanism built and unit-proven (15/15) but the authorised Stooq fetch failed vendor-side with zero DB side effects (I verified); spec asked full, engine ran lean, so the audit lane never ran and a contract-forbidden lane did.
- iter 5: (no verdict — superseded by the owner before evaluation after its drill permanently deleted 2026-08-11/2026-08-12; see `state/incident-2026-08-20-iter-5-superseded.md`).

## Do not redo

- **J-10 steps 1, 4, 7 are DONE** — the 587-symbol missing set is derived and cross-validated from three sources (`j10_recovery.py` `RECOVERY_SYMBOLS`); provenance is recorded via `data_provider_runs` id=541 + the iter-6 handoff; work is on `goal/market-compass`. Do NOT re-derive the missing set.
- **The fail-closed scope guard EXISTS and is tested** (`j10_recovery.py`, `tests/test_j10_recovery.py`, 15/15). Do not rebuild it — only swap `RECOVERY_SOURCE` and add step 2a's convention check.
- **Do NOT retry Stooq, defeat its bot challenge, or try a third vendor.** `LocalStooqArchiveProvider` cannot help (its bundle ends 2026-07-01, the seed boundary).
- **Do NOT build destructive-drill isolation/sandbox infrastructure** — goal.md Constraints record it as a deferred defect, explicitly not this cycle's build.
- **AG-12/AG-17 held through iter-6** — 24 manifest rows + export files hash-identical, iter-5 artifacts byte-untouched. Do not re-audit; do not delete the quarantined INVALID evidence.
- **J-01/J-04's iter-6 PASS rows are unusable** (damaged-DB lane). Re-verify J-01..J-04 with the browser lane only AFTER recovery passes; also record the 4 overdue walkthroughs and fix the stale J-01 golden (fails on a wrapped "Consumer Discretionary" cell).
