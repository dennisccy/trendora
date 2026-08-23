# Iteration State — market-compass

**After iteration:** 11 · **Date:** 2026-08-23 · **Verdict:** REGRESSION

## Journeys

3 passing (J-01 J-04 J-10) · 6 partial (J-02 J-03 J-05 J-06 J-09 J-11) · 2 failing (J-07 J-08) — 11 total

## Active blockers

- **OWNER DECISION (blocking everything).** The authorized `next_session_manifests` migration removed
  the FK constraint **and** dropped three `DEFAULT` clauses (`version`, `frozen`, `prospective_eligible`)
  **and** moved `version` from ordinal 9 to 3 — beyond ruling A1 / AG-18's "and nothing else". Live,
  unrepairable without a second authorization; no stored value changed (24 rows × 28 columns verified).
  Options: accept in writing / corrective rebuild / record as an accepted deviation. Evidence:
  `runs/goal-market-compass-iter-11/j11-stage-b1-premigration-ddl.json` vs live `sqlite_master`; audit
  finding B1. **Ruling A6's Stage C gate is NOT cleared.**
- Maintenance isolation (ruling A5) stays ACTIVE: no app boot, no browser QA, no replay lane until
  Stage G. `docs/goal.md`'s Loop-mechanics gate shuts every other product/research lane until then.
- Uncommitted: the migration script, its 10 evidence files and both fixes (QA wrongly claimed otherwise).

## Last 2 verdicts

- iter 11: REGRESSION — Stage B1 genuinely completed and re-verified live (FK gone, 24/24 rows
  identical, `basis_disclosure` fails closed on all 8 no-basis rows), but the migration exceeded its
  written authorization on the live DB and that breach is unresolved.
- iter 10: STALLED — two Stage-C precondition items were false on the live DB; every unblock path was
  an owner decision. That decision arrived as rulings A1-A7 and drove iter-11.

## Do not redo

- **J-10 is CLOSED** (owner, 2026-08-23): 585 restored / EA + EQR unrestorable. Do not reopen, retry,
  or re-fetch; AG-9's exception is exhausted. Re-verified read-only in iter-11.
- **The live FK removal is DONE** — no `FOREIGN KEY` clause, `foreign_key_check` empty under
  `PRAGMA foreign_keys=ON`. Do not migrate again except as an owner-ordered corrective rebuild.
- **`basis_disclosure` fail-closed fix is DONE** (`compass.py`, ruling A4): four degenerate branches
  return `"unverifiable"` (+ the auditor's non-object guard); 96 targeted tests pass.
- **Frontend `basis.status` 4-literal union + `lib/basis-disclosure-label.ts` are DONE** (tsc clean).
- Stages B (inventory) and B2 (frozen engine identity) shipped in iter-10 — do not rebuild them.
- Never run the full backend suite, boot any service, or copy `trendora.db`.
