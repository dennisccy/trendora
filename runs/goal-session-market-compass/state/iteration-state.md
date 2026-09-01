# Iteration State — market-compass

**After iteration:** 31 · **Date:** 2026-09-01 · **Verdict:** ESCALATE

## Journeys

10 passing (J-01 J-02 J-03 J-04 J-05 J-06 J-07 J-08 J-10 J-11) · 1 partial (J-09) — 11 total

## Active blockers

- **J-09 "The backend fits the host" is the ONLY journey left, and it is dev-owned, NOT owner-owned.** `reports/perf-budgets.md`'s iter-25 AUDIT CORRECTION says the blocking 3,064,772 kB (~2.92 GB) VmPeak "is also not independently corroborated: no sampler log or /proc capture from this run survives"; a second goal-mode engine (tensteps) held the host through the burst; load was ~2x the documented Method. Step 2 needs a `/proc/<pid>/status` reading.
- **J-09 NEXT ACTION** = clean re-measurement on a quiet host, raw evidence SAVED, appended dated beside the old figures. Only if THAT still misses 2,621,440 kB does its own "stop for owner review" clause fire — never widen the target to pass. SAFETY: it load-bursts the machine a goal-mode run froze on 2026-08-20; nothing else of ours may run during it. AG-10 is critical and owner-set.
- **Dev-owned, ride-along:** `journey-scripts/J-02.json` (mtime 03:35:14) and `J-03.json` (03:35:18) were overwritten AFTER the replay lane ran (03:31:03) and have NEVER been executed — lint-only. Run both FIRST next round, report results verbatim, do not edit them again afterwards.

## Last 2 verdicts

- iter 31: ESCALATE — J-02 + J-03 closed on evidence re-derived read-only from stored manifest row 28; spec asked `full`, engine ran `lean` (8th demotion); the last journey is the riskiest in the project.
- iter 30: CONTINUE — J-07 closed; three journeys still open; depth held at full.

## Do not redo

- **J-02 and J-03 are DONE** — `passing`, all 6 steps each (`iter-31/eval.md`); their owed `[NEW]` walkthroughs are `evidence_makeup` capture tasks, never an iteration goal. Do not rebuild `session_delta.py`, `compass.build_narrative`, `compass-whatchanged-card.tsx`, `compass-summary-card.tsx`.
- **The handoff's "empty comparison_cohort / near_threshold_shadow" Observation is WRONG** — row 28 stores 539 cohort + 25 shadow entries (top-level columns, not inside `selection`). Do not chase it as a defect.
- **Zero new manifest mints:** 28 rows / 18 `as_of` / max id 28, re-verified read-only after every lane. A live `GET /api/compass?as_of=<D>` on a manifest-less D mints a permanent row — name the exact as-of set in the plan, permit no other, never backfill the 16 word-less dates.
- **J-11 closed** (owner ruling 2026-08-27; `J-11.json` now has a real executed pass), **J-10 closed** at 585 restored / 2 unrestorable (EA, EQR), **J-07 closed** — do not reopen any, and do not touch `build_state_band`, `build_manifest_payload`, `_derive_prospective_eligible`, `_severity_at`, `compass.vocabulary.direction_words`.
- `test_no_magic_numbers.py`'s red failure (`indicators.py`/`forward_testing.py`/`research.py`, untouched since `0c445647`) is pre-existing and out of scope — fix-or-waive is the owner's call.
