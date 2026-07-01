# goal-mcp-loop-iter-15 Dev Handoff

**Phase:** goal-mcp-loop-iter-15
**Date:** 2026-07-01
**Agent:** developer
**Status:** complete

## What Was Built

Target journey **J-09** — surface a **7th** referee-certified canonical edge: the pre-registered
relative-strength `rs_spy_3m` top-decile **60-day-horizon** factor claim as a "Proven" badge on
`/research/factor-lab` and a new row on `/evidence`. This is a **near-zero application-code** iteration —
the certification was done by the pre-build gate and the read-side machinery is already general.

- **(Gate — verified only, not developer code)** The post-decompose gate had already certified the
  `## Evidence Claim` and appended **row 7** to `runs/goal-session-mcp-loop/state/certified-claims.jsonl`
  (`factor rs_spy_3m d10 h60`, `ledger=canonical`, `status=PASS`, `deflation=bonferroni`,
  `deflation_divisor=7`, `required_p=0.0071428571428571435`, `holdout_edge=0.21344270202534893`,
  `control_excess=0.21344270202534893`, `p_value=0.0004997501249375312`, `register_date=2026-07-01`,
  `block_length=87`). The honest-stop guard did **not** fire (it is a PASS). The gate is the ONLY writer —
  I hand-edited nothing in the ledger. `git diff` on the ledger confirms exactly one added line (row 7);
  rows 1–6 are byte-identical.
- **No frontend source change.** The existing general per-horizon matcher `resolveCohortEvidence` lights
  `rs_spy_3m` h60 automatically once the ledger has row 7, and the `/evidence` `ClaimRow` renders the row
  through the EXISTING signal-less `factor` branch. Verified live: `GET /api/evidence` serves 7 claims, the
  `rs_spy_3m` h60 row byte-matches the ledger, and `proven_signals` stays `{leadership_score}` (the claim is
  signal-less — `rs_spy_3m` ∉ the three score columns, so no `/stocks` inline badge lights).
- **Frontend unit test (the one intentional code edit)** — added a mirrored `resolveCohortEvidence` case for
  the `rs_spy_3m` D10 h60 cohort ("Proven" + href `/evidence#factor-rs_spy_3m-d10-h60`; "Not yet proven" at
  h1/h5/h10/h20), a `claimSurface`/`claimAnchorId` case pinning the `/evidence` row rendering + deep-link
  anchor, a `rsSpy3mH60Row()` PASS fixture (byte-matches ledger row 7), and a `ledgerClaims7()` full-current
  ledger accessor. Reconciled the negative case (o) so its now-backed `rs_spy_3m` example reads as a
  no-cross-horizon-leak negative against the full 7-entry ledger.
- **Backend golden-fixture refresh (TEST-ONLY, contingency triggered)** — three tests that read the LIVE
  canonical ledger pinned it at 6 entries; refreshed them to the 7-entry reality (exactly as iter-11 did
  4→5 and iter-13 did 5→6). No `app/**` or `config.yaml` change.
- **Blueprint** — VERIFY-ONLY: the J-09 journey-homes row and the iter-15 Data-Contract clarification were
  already present and correct in `runs/goal-session-mcp-loop/state/blueprint.md`. Nothing added; no
  nav-skeleton change ⇒ no `blueprint.reapproval-requested`.

## Files Changed

- `apps/frontend/lib/evidence.test.ts` -- ADDED the J-09 block: `rsSpy3mH60Row()` fixture (byte-matches
  ledger row 7), `ledgerClaims7()` accessor, check (ee) `resolveCohortEvidence` rs_spy_3m h60 → Proven +
  href / h1/h5/h10/h20 → Not yet proven, check (ff) `claimSurface`+`claimAnchorId` for the row + anchor;
  reconciled the negative case (o) to resolve against `ledgerClaims7()` with an updated comment. TEST-ONLY.
- `apps/backend/tests/test_evidence.py` -- TEST-ONLY golden refresh of `test_canonical_ledger_frozen_golden`
  (live canonical ledger 6→7: count, statuses, divisors `[1..7]`, factor/kind lists, + a new entries[6]
  block asserting the rs_spy_3m h60 verdict bytes; payload count 6→7; `proven_signals` still
  `{leadership_score}`). The tmp-fixture tests in this file are UNTOUCHED.
- `apps/backend/tests/test_staging_ledger_routing.py` -- TEST-ONLY golden refresh of the two LIVE-canonical
  reads: `test_rejection_offsets_on_live_canonical_ledger` (`[1,2,4,5,6]`/6 → `[1,2,4,5,6,7]`/7) and the
  "canonical untouched" tail of `test_committed_staging_ledger_is_the_frozen_multi_horizon_discovery`
  (6 → 7). The staging-ledger determinism assertions in that test are UNTOUCHED and byte-identical.
- `docs/handoffs/goal-mcp-loop-iter-15-dev.md`, `docs/handoffs/goal-mcp-loop-iter-15-frontend.md`,
  `reports/phase-goal-mcp-loop-iter-15-implementation-summary.md` -- NEW docs.

**Byte-identical (NOT edited), confirmed via git:** `apps/backend/app/engine/{referee,ledger,forward_walk}.py`,
`apps/backend/app/mcp/tools.py`, `apps/backend/app/engine/evidence.py`, `apps/frontend/lib/evidence.ts`,
`apps/frontend/lib/factor-lab-evidence.ts`, `apps/frontend/app/research/_labs.tsx`,
`apps/frontend/app/evidence/page.tsx`, `config.yaml`. The `certified-claims.jsonl` change is the gate's
row-7 append (not mine).

## Tests Run

- **Frontend unit:** `cd apps/frontend && npx --offline tsx lib/evidence.test.ts` → **39 passed** (37 prior
  + 2 new J-09 cases). No frontend source change — the new cases pass against the unchanged `evidence.ts`
  general matcher (iter-8 "don't special-case" upheld).
- **Backend:** `cd apps/backend && .venv/bin/python -m pytest <targets> -q`
  - `test_evidence.py` + `test_referee.py` → **24 passed** (referee/ledger determinism tests UNEDITED)
  - `test_staging_ledger_routing.py` → **19 passed** (2:20 — engine-fixture heavy)
  - `test_online_fdr.py` + `test_forward_walk.py` + `test_config.py` → **80 passed**
  - The 3 live-ledger golden tests: FAILED before the refresh (7 vs 6) → PASS after (correct golden update).
- **Live read-path (with cleanup):** `build_evidence_payload` on the live ledger → 7 claims,
  `proven_signals=['leadership_score']`, `rs_spy_3m` h60 row byte-matches ledger row 7; the running backend
  logged `GET /api/evidence 200 OK`. Backend stopped, port freed, no stray uvicorn.

## Known Issues

- **Yellow flag (documented, not a blocker):** the `rs_spy_3m` h60 holdout edge **+0.2134** is implausibly
  large (iter-10 auditor B3). It is honest to surface ONLY because the canonical gate re-certified it
  out-of-sample (row 7 PASS, p 0.0004998 ≪ `required_p` 0.007143, beats the SPY control). The
  coherence-auditor and phase auditor should scrutinize it; the honest-stop guard governs any non-PASS. It
  passed — this is the audit focus of the iteration, not a defect.
- **Browser verification is the browser-qa-agent's lane.** As developer I verified the read path
  (unit + live API); the actual factor-lab "Proven" badge render + `/evidence` row screenshot (J-09, and the
  J-05/J-06/J-07 re-verify) are for the browser lane. No frontend source change was needed, so no browser
  re-run was triggered by me.
- **Frontend test runner:** this machine's Node (v22.22.1) has no built-in TS loader (`ERR_NO_TYPESCRIPT`),
  so the documented `node lib/*.test.ts` fails; use `npx --offline tsx lib/evidence.test.ts` (tsx is cached
  in `~/.npm/_npx`). Same environment note as prior iterations.
