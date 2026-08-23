# Iteration State — market-compass

**After iteration:** 9 · **Date:** 2026-08-23 · **Verdict:** CONTINUE

## Journeys

3 passing (J-01 J-04 J-10) · 5 partial (J-02 J-03 J-05 J-06 J-09) · 2 failing (J-07 J-08) · 1 unknown (J-11) — 11 total

## Active blockers

- **J-11 is the ONLY actionable journey** (dev). Prerequisite now met: J-10's raw layer is repaired. `docs/goal.md` Loop-mechanics keeps every normal product/research/browser lane shut until **J-11 Stage G**, which exclusively owns the J-01/J-02/J-03 replay. Spec: `docs/goal.md` J-11 stages A–G.
- Derived layer is **mixed-basis** (dev): `ScannerRun`s 3148/3150 (2026-08-11/12) are iter-8's 20-symbol basis; six aggregate caches were refreshed on the 585-symbol basis. J-11 must clear BOTH.
- **AVB** (dev): the only bridge-transformed symbol (×2.793) — price on stored scale, volume unscaled ⇒ `close*volume` reads ~2.79× high on the 2 recovery dates (`scoring._avg_dollar_volume`, `universe_resolver._adv_dollar`, `universe_screen` liquidity gate).
- **Do not re-run** `apps/backend/scripts/run_j10_population_recovery.py` (human): AG-9's exception is exhausted, the script has no guard and will fetch live. Needs a new dated `docs/goal.md` amendment.
- Untracked at eval time (dev): that driver + `runs/goal-market-compass-iter-9/j10-population-*.json`. Confirm the release step commits them — the evidence file is J-10's only admissible calibration record.
- Forbidden-lane defect (human/framework): unfixed in `scripts/automation/`; iter-9 avoided it via the new `Maintenance isolation: required` contract, which held (no boot-warmup row, no replay lane — verified).
- Non-blocking owner questions: J-09's 3.44 GB; J-06 "run unavailable" wording; J-01 test-step rewording; empty next-session-focus; whether MNST joins the recovery list.

## Last 2 verdicts

- iter 9: CONTINUE — J-10 reached its raw-layer terminal state (585/587 restored, EA+EQR named unrestorable, all verified by my own read-only SQL); full depth and maintenance isolation both held; 0 new anti-goals.
- iter 8: CONTINUE — first real restoration (20/587) through the owner's gate; one AG-17 breach found and fixed in-iteration; its cause left open.

## Do not redo

- **J-10 recovery — DONE, do not reopen.** 585/587 restored; EA/EQR unrestorable for evidenced external reasons. No third vendor, no re-fetch, no threshold change is permitted.
- **Frozen, read unchanged, never re-derive:** `RECOVERY_SYMBOLS` (587), `RECOVERY_DATES`, `RECOVERY_SOURCE`, `PATH_AGREEMENT_TOLERANCE` .005, `BRIDGE_DISPERSION_BOUND` .015, `MIN_COMPARABLE_PAIRS_PER_SYMBOL` 3, `CONVENTION_CHECK_SAMPLE_SYMBOLS` (20).
- **iter-8 audit gaps B1/B2/B3/B5/B6 and iter-9 gaps 1–3 are CLOSED** in `j10_recovery.py` (`evidence_path` required, provider-source mismatch guard, ungated back door shut) — do not regress.
- **iter-8's 20 symbols** are byte-unchanged and idempotently skipped — never re-fetch or overwrite.
- **`reports/qa/goal-market-compass-iter-8-evidence/`** is quarantined incident evidence (AG-17): byte-unchanged, md5s verified — never touch, clean, or regenerate.
- **J-09's config half (`cache_size` −65536) landed in iter-4** as an honest miss; do not re-tune it.
