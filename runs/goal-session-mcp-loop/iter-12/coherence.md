**Verdict:** COHERENCE-PASS

## Iteration: goal-mcp-loop-iter-12

### Summary

Pure backend-internal discovery iteration (Frontend Present: no). The combination staging exploration
introduces no new displayed value and no new serving endpoint. All coherence contracts remain intact.

---

## Step 1 — Data Contract Check

**Canonical value: Evidence status + certified-claim (GET /api/evidence → proven_signals)**

Canonical source: `app.engine.referee:certify_edge` via `app.mcp.tools:verify_edge`; read-side
`app.engine.evidence:build_evidence_payload`; served by `GET /api/evidence`.

Diff findings:

1. `apps/backend/app/engine/triad_scan.py` — new functions `_combination_staging_candidates` and
   `explore_combination_staging` added. Both write ONLY to the internal staging ledger
   (`ledger=LEDGER_STAGING`), never to the canonical `evidence.ledger_path`. A fail-closed `ValueError`
   guard refuses any call that would point the exploration at the canonical ledger path. `verify_edge`
   remains the sole ledger writer. No new computation of any displayed value.

2. `config.yaml` — new `combination_candidates` block added under `triad`. This is a config-only
   registration of the pre-registered candidate set; it is consumed only by the new staging explorer
   and introduces no new serving endpoint or display value.

3. `runs/goal-session-mcp-loop/state/staging-ledger.jsonl` — 3 new entries (combination cohort
   verdicts). These are internal-only records, never served by `GET /api/evidence`, never read by any
   page, never displayed.

4. `runs/goal-session-mcp-loop/state/certified-claims.jsonl` — NO changes (git diff empty). The five
   canonical entries remain byte-identical. `proven_signals` stays `{leadership_score}`.

5. `apps/backend/app/api/`, `apps/frontend/`, `apps/backend/app/engine/evidence.py` — NO changes
   (git diff empty). The `GET /api/evidence` endpoint and all UI surfaces are untouched.

**Result: no Data Contract violations.** The staging ledger is a distinct internal artifact
(documented in the iter-9/iter-10/iter-12 blueprint clarifications); it is never served or displayed.
No duplicate computation of any contract value. No non-canonical source.

No new displayed values were introduced, so there is nothing to register as unregistered.

---

## Step 2 — Information Architecture Check

The UI surface map at
`reports/phase-goal-mcp-loop-iter-12-ui-surface-map.md` reads: "No UI surfaces affected."

The diff confirms: no changes to `components/sidebar.tsx`, `App.tsx`, any router, or any frontend
file. No new routes or pages were added. All nav sections remain as registered in the blueprint IA.

**Result: no IA violations.**

---

## Step 3 — Subjective Observations (advisory)

None. This is a backend-only, no-display iteration. No formatting, labelling, or layout to assess.

---

## Evidence trail

- Canonical ledger diff: empty (byte-identical).
- Staging ledger diff: 3 new internal-only combination verdicts (2 FAIL, 1 PASS — recorded for
  iter-13 to evaluate promotion eligibility; never served or displayed).
- Frontend diff: empty.
- API diff: empty.
- New code paths: `triad_scan.py:_combination_staging_candidates` (config reader, no display) and
  `triad_scan.py:explore_combination_staging` (staging-only writer, fail-closed against canonical).
