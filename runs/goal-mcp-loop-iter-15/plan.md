# goal-mcp-loop-iter-15 Execution Plan

Surface a **7th** referee-certified canonical edge (target journey **J-09**): the pre-registered
relative-strength `rs_spy_3m` top-decile **60-day-horizon** factor claim as a "Proven" badge on
`/research/factor-lab` and a new row on `/evidence`. Depth: **full** — it writes a permanent canonical
ledger row that tightens the user-facing Bonferroni divisor **6 → 7 forever**, and the candidate carries a
documented **yellow flag** (holdout edge +0.2134 is implausibly large — iter-10 auditor B3), so the
auditor / closure / ux-regression gates must scrutinize it. Near-zero application code, high verification rigor.

**Precondition already satisfied by the pipeline:** the post-decompose gate has ALREADY certified the
`## Evidence Claim` and appended **row 7** to `runs/goal-session-mcp-loop/state/certified-claims.jsonl`:
`factor rs_spy_3m d10 h60`, `ledger=canonical`, `status=PASS`, `deflation=bonferroni`,
`deflation_divisor=7`, `required_p=0.0071428…`, `holdout_edge=0.21344270202534893`,
`control_excess=0.21344270202534893`, `p_value=0.0004997501249375312`, `register_date=2026-07-01`,
`block_length=87`. The honest-stop guard did **not** fire (it is a PASS). The gate is the ONLY writer —
no hand-editing of the ledger.

## What to Build

- **(Gate — already done, verify only)** Confirm ledger row 7 is present, `status=PASS`, `divisor=7`,
  `required_p ≈ 0.007143`, and its bytes match the values above. No developer code.
- **Frontend unit test (the one intentional code edit)** — add a `resolveCohortEvidence` case for the
  `rs_spy_3m` D10 h60 cohort ("Proven" + href `/evidence#factor-rs_spy_3m-d10-h60`; "Not yet proven" at
  h1/h5/h10/h20), mirroring the existing `vcp_contraction` h60 case (m2). Reconcile the ONE existing
  negative case that currently uses `rs_spy_3m` as an *unbacked* example so it targets a still-unproven
  horizon (the iter-11 case-(o) swap).
- **No frontend source change** — the general per-horizon matcher lights `rs_spy_3m` h60 automatically once
  the ledger has row 7; the `/evidence` `ClaimRow` renders the row generically. A surgical read-side fix is
  applied **only if** browser QA finds a real gap (not expected; re-run the browser lane after any such fix).
- **No backend/engine change** — `apps/backend/app/engine/{referee,ledger,forward_walk}.py`,
  `apps/backend/app/mcp/tools.py:verify_edge`, `apps/backend/app/engine/evidence.py`, and `config.yaml` stay
  **byte-identical**; the referee/ledger determinism (expectation) tests stay **UNEDITED and green** (that
  unedited-passing suite is the "defaults reproduce" / no-regression proof — iter-9 lesson).
- **(Contingency, TEST-ONLY)** If a frozen-golden backend test pins the canonical ledger to 6 entries,
  refresh it to the 7-entry reality (statuses, divisors `[1..7]`, row-7 bytes, `proven_signals` still
  `{leadership_score}`) — a golden-fixture refresh, exactly as iter-11 did for 4→5. **No `app/**` change.**
- **Blueprint — reconcile, do NOT duplicate.** `runs/goal-session-mcp-loop/state/blueprint.md` already
  contains the J-09 journey-homes row (L77) and the iter-15 Data-Contract clarification (L202). Verify they
  are correct and present; add nothing new. No nav-skeleton change ⇒ no `blueprint.reapproval-requested`.
- **Dev handoff** at `docs/handoffs/goal-mcp-loop-iter-15-dev.md`.

## Agents Required

- developer: yes -- adds the mirrored `evidence.test.ts` case, reconciles case (o), applies the TEST-ONLY
  backend golden refresh only if needed, verifies the blueprint, writes the handoff. Near-zero feature code.
- backend-data: no -- ledger row 7 was written by the post-decompose GATE (already on disk); NO
  engine/referee/ledger/`online_fdr`/`triad_scan`/`evidence.py`/`api/evidence.py`/`config.yaml` edit. Only a
  possible TEST-ONLY golden-fixture refresh (6→7) in the backend expectation tests.
- frontend-ux: yes -- but NO frontend source change: the existing general `resolveCohortEvidence` +
  per-horizon `factorHorizonBadges` + the `/evidence` `ClaimRow` surface the row/badge automatically. Scope
  is the mirrored unit-test case plus browser verification of the badge/row.

## Frontend Present

Frontend Present: yes

## Files to Create/Modify

- `apps/frontend/lib/evidence.test.ts` -- ADD the `rs_spy_3m` h60 "Proven" case (mirror case (m2), ~L422-442)
  + a `rsSpy3mH60Row()` PASS fixture (mirror `vcpContractionH60Row()`, ~L365-391) appended to `ledgerClaims()`
  (~L396-404); reconcile the negative case (o) at ~L458 so its `rs_spy_3m` example uses a still-unproven
  horizon (h1/h5/h10/h20). TEST-ONLY.
- `docs/handoffs/goal-mcp-loop-iter-15-dev.md` -- NEW dev handoff.
- `runs/goal-mcp-loop-iter-15/plan.md` -- this plan.
- `apps/backend/tests/test_evidence.py` and/or `apps/backend/tests/test_staging_ledger_routing.py` --
  CONTINGENCY, TEST-ONLY: refresh the frozen-golden canonical-ledger snapshot 6→7 IF it pins the count;
  keep `proven_signals == {leadership_score}`. No `app/**` change.
- `runs/goal-session-mcp-loop/state/blueprint.md` -- VERIFY-ONLY (J-09 row + iter-15 clarification already
  present; reconcile, do not duplicate).
- **MUST stay byte-identical (do NOT edit):** `apps/backend/app/engine/{referee,ledger,forward_walk}.py`,
  `apps/backend/app/mcp/tools.py`, `apps/backend/app/engine/evidence.py`, `apps/frontend/lib/evidence.ts`,
  `apps/frontend/lib/factor-lab-evidence.ts`, `apps/frontend/app/research/_labs.tsx`,
  `apps/frontend/app/evidence/page.tsx`, `config.yaml`, and `certified-claims.jsonl` (gate-only writer).

## UI Evolution

- New user-facing capability: the user sees that the 3-month relative-strength (`rs_spy_3m`) leadership
  factor carries a referee-certified out-of-sample edge **specifically at the 60-day hold** (a NON-20
  horizon), auditable from both the Research factor-lab badge and the Evidence ledger row — with every
  uncertified horizon of the same factor honestly marked "Not yet proven".
- New information displayed: a 7th certified-claim row on `/evidence` for `rs_spy_3m` D10 @ h60 (hypothesis
  incl. the 60-day horizon, out-of-sample PASS verdict, SPY control, registration date, forward-walk
  score-to-date, "Backs: Research factor lab →"); a "Proven" badge on the `rs_spy_3m` h60 cohort in
  `/research/factor-lab`.
- New user actions: none new — reuses the existing badge → ledger deep-link and the existing factor/horizon
  selection on `/research/factor-lab`.
- UI surface changes: one additional claim row on the existing `/evidence` ledger; one additional "Proven"
  badge state on the existing `rs_spy_3m` factor view (h60 cohort). No new pages/panels.
- Navigation changes: none — J-09 lives on the existing `/research/factor-lab` + `/evidence` homes (same as
  J-06/J-07), already in the IA / nav skeleton.

## Visual Requirements

- Component patterns: reuse the existing `ClaimRow` (verdict-status Badge + `<dl>` fields) on `/evidence` and
  the existing per-horizon evidence chip strip on the factor lab (compact `{h}d {status}` pills carrying
  `data-factor` / `data-horizon` / `data-proven`). No new components.
- Layout: unchanged — the existing `/evidence` ledger list and the existing `/research/factor-lab` table with
  its per-horizon Evidence column.
- Key visual effects: consistent with the existing minimal, data-dense, evidence-first style; the "Proven"
  chip reads as a quiet proven-✓ pill, the uncertified horizons as the honest muted "Not yet proven" state —
  calm and unmissable, never hype.
- States to handle: Proven (`rs_spy_3m` h60), Not yet proven (`rs_spy_3m` h1/h5/h10/h20). The `/evidence`
  capture MUST show a live backend (no "Backend unavailable" pill — it invalidates any fail-safe
  "Not yet proven" reading; iter-14 lesson).

## Key Test Scenarios

- **J-09 (browser, primary):** `/evidence` shows the new `rs_spy_3m` h60 row with all standard fields;
  `/research/factor-lab` `rs_spy_3m` **h60** cohort shows a "Proven" badge deep-linking to
  `#factor-rs_spy_3m-d10-h60`; h1/h5/h10/h20 read "Not yet proven". Open the ACTUAL "Proven" frame and confirm
  it is the `rs_spy_3m` h60 cohort (not a relabeled default-state or other-horizon frame — iter-13 lesson).
- **Byte-match (anti-goal #3):** the displayed edge / p-value / SPY control on the new `/evidence` row
  byte-match `certified-claims.jsonl` row 7 (holdout +0.2134 → "+21.34%", control +0.2134, p 0.0004998,
  register 2026-07-01, divisor 7) — read the ledger file directly, never trust the rendered label alone.
- **Signal-less no-leak (J-01/J-02/J-03):** `proven_signals` stays `{leadership_score}`; ZERO new `/stocks`
  inline score badges light; `rs_spy_3m` ∉ the three score columns.
- **Required-still-passing (J-01..J-08):** re-verify shared surfaces — J-05 (`/evidence` now 7 rows), J-06
  (`vcp_contraction` h20) and J-07 (`vcp_contraction` h60) badges via the same matcher/page.
- **Frontend unit:** the new case asserts `rs_spy_3m` h60 → "Proven" + href `/evidence#factor-rs_spy_3m-d10-h60`
  and "Not yet proven" at h1/h5/h10/h20; case (o) reconciled; all existing frontend assertions stay green.
- **Backend:** engine/referee/ledger/config byte-identical; referee/ledger determinism tests UNEDITED and
  green; the seeded (20240601) block-bootstrap p reproduces at the floor 0.00049975; any golden-fixture
  refresh is TEST-ONLY and keeps `proven_signals == {leadership_score}`.
- **Error cases:** uncertified `rs_spy_3m` horizons read "Not yet proven"; a signal-less claim MUST NOT enter
  `proven_signals`; the gate MUST block a non-PASS canonical claim (block path honored, not worked around).

## Assumptions & Landmines

- **`"ledger":"canonical"` is load-bearing** (iter-9b/iter-10) — already honored: the gate wrote row 7 to the
  canonical ledger, not staging. An omitted key would silently re-stage and never surface.
- **Yellow flag — scrutinize, don't rubber-stamp** (iter-10 auditor B3, load-bearing): the +0.2134 holdout
  edge is implausibly large. It is honest to surface ONLY because the canonical gate re-certified it
  out-of-sample (row 7 PASS, p 0.0004998 ≪ required_p 0.007143, beats the SPY control). The coherence-auditor
  and phase auditor MUST scrutinize it; the honest-stop guard governs any non-PASS. This is not a blocker —
  it passed — but it is the explicit audit focus of this iteration.
- **General matcher — do NOT special-case** (iter-8): `resolveCohortEvidence` lights every certified cohort
  it matches; expect `rs_spy_3m` h60 to light automatically and assert the deep-link lands on the real
  `factor-rs_spy_3m-d10-h60` anchor. No factor-specific branch.
- **Regression proof for a shared-value iteration** (iter-9): the proof of no regression is the engine's
  canonical output being byte-identical + the referee/ledger expectation tests unedited-and-green, alongside
  the browser pass — NOT the dead `browser_checks_run` flag.
- **Screenshot hygiene** (iter-11/13/14): md5 every evidence PNG (distinct, correctly labeled), use full-page
  or element-clip captures with the target scrolled into frame — never a scrolled headless viewport capture
  (returns a ~5855-byte blank frame). A "Backend unavailable" pill on an `/evidence` capture invalidates a
  fail-safe "Not yet proven" reading.
- **Blueprint already carries J-09** — the J-09 row (L77) + iter-15 clarification (L202) are present;
  reconcile only, do not re-author or duplicate.

## Out of Scope (excluded — no scope creep)

- Any change to referee/ledger/evidence-resolver/`verify_edge`/FDR/staging engine code, or `config.yaml`
  (must stay byte-identical — anti-goal #5 determinism).
- Any new page, route, serving endpoint, computing module, or nav section.
- Any `/stocks` inline score-badge change (`rs_spy_3m` is signal-less; `proven_signals` MUST stay
  `{leadership_score}`).
- Any additional canonical Evidence Claim beyond the single `rs_spy_3m` h60 promotion (each canonical claim
  permanently tightens the Bonferroni bar — do not casually append another).
- The proposer-backlog `leadership_score` h60 (score-column fallback) and the speculative
  horizon-term-structure view — backlog only, not this iteration.
- Re-submitting / re-slicing the cohort if the gate had blocked (honest-stop) — moot here, the gate PASSED.
