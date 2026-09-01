# Iteration State — market-compass

**After iteration:** 32 · **Date:** 2026-09-01 · **Verdict:** CONTINUE

## Journeys

10 passing (J-01 J-02 J-03 J-04 J-05 J-06 J-07 J-08 J-10 J-11) · 1 partial (J-09) — 11 total

## Active blockers

- **J-09 "The backend fits the host" is the ONLY journey left. Re-measured cleanly this round and STILL A MISS: VmPeak 3,038,684 kB vs the 2,621,440 kB bar (+15.9%).** Raw capture survives at `runs/goal-market-compass-iter-32/j09-vmpeak-samples.csv` (80 rows, pid 1724495, 03:19:41Z-03:26:17Z); `reports/perf-budgets.md` Addendum 43 records it. No cap widened, nothing rounded.
- **J-09 NEXT ACTION is DEV-OWNED, not owner-owned.** The peak is a BOOT TRANSIENT: VmSize hits 3,038,684 kB at t+15.94s (still `initializing`), drops to 1,750,504 kB at t+20.94s, ends at 1,298,796 kB / VmRSS 725,856 kB. ~1.29 GB held ~5s during warm-up, then released — `apps/backend/app/engine/warmup.py:351` opens `with bar_cache(session):` around the cold cadence-date compute. Bound it to a `config.yaml` budget: that is `docs/goal.md` Constraints **(c)**, and `docs/goal.md:2396-2400` marks the Host-resource-fit block owner-authored **BINDING** work that "rides the nearest applicable slices", with (a) and (b) already landed at iter-5. (c) carries its own catch: read the iter-43 handoff first; if the bound breaks correctness, STOP and ask the owner. Then re-measure the same way and append one dated entry. NEVER move the 2.5 GB line. SAFETY: heaviest-memory code path on the host a goal-mode run froze 2026-08-20 — nothing else of ours running.
- **Dev-owned, ride-along (5th round of this defect family):** the replay lane was run WITHOUT `--results`, so its results file never existed; the reviewer (04:39) and QA (04:47) both certified it anyway — the auditor created it at 05:19. ALWAYS pass `--results <path>` and make the lane fail when the file is absent/empty. Also merge replay results into `ui-test-results.md` (it said 0/11 SKIPPED while the same ten journeys passed twice), and fix the wrong "no as_of outside the 3-value set" sentence still standing in Addendum 43.

## Last 2 verdicts

- iter 32: CONTINUE — J-09 re-measured honestly and still misses, but the miss is a 5-second start-up spike and the remaining lever is the owner's own binding Constraints (c), so not STALLED; depth held at `full`, zero DB writes, 10/10 replay PASS.
- iter 31: ESCALATE — J-02 + J-03 closed on evidence re-derived read-only from stored manifest row 28; spec asked `full`, engine ran `lean` (8th demotion).

## Do not redo

- **J-09's re-measurement is DONE and must NOT be repeated as an iteration goal.** The figure is clean, durably evidenced, and within 0.85% of iter-25's. Another measurement pass closes nothing — only bounding the warm-up allocation can.
- **"Owner-only" is WRONG for `docs/goal.md` Constraints (b)/(c)** — the dev handoff, QA and the auditor all said it; the goal text says binding scheduled work. Do not re-record it as a human-owned blocker.
- **Golden-script hygiene is clean** — all ten mtimes predate iter-32; `J-02.json`/`J-03.json` executed twice and passed. Do not edit any golden after a replay run.
- **Zero new manifest mints:** 28 rows / 18 `as_of` / max id 28, re-derived read-only; the `.db` file was never written this round (mtime 01:32 < start 04:03, WAL 0 bytes). A live `GET /api/compass?as_of=<D>` on a manifest-less D mints a permanent row — name the exact as-of set in the plan and permit no other. The next spec must ALSO authorize the goldens' own as-of set (`2026-03-30`, `2026-07-23`, `2026-08-03`, `2026-08-11`) — iter-32's spec forbade calls its own TC-7 mandated.
- **J-02, J-03, J-07, J-10, J-11 are closed** — do not rebuild `session_delta.py`, `compass.build_narrative`, `build_state_band`, `build_manifest_payload`, `_derive_prospective_eligible`, `_severity_at`, `compass.vocabulary.direction_words`, `compass-whatchanged-card.tsx`, `compass-summary-card.tsx`. Owed walkthroughs and J-04's candidate-card retake are `evidence_makeup` capture tasks, never an iteration goal.
- `test_no_magic_numbers.py`'s red failure (`indicators.py`/`forward_testing.py`/`research.py`) is pre-existing and out of scope — fix-or-waive is the owner's call.
