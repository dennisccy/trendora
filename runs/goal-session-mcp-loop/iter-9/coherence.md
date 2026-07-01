**Verdict:** COHERENCE-PASS

## Coherence Audit — goal-mcp-loop iter-9

**Iteration:** goal-mcp-loop-iter-9 (index 9)
**Snapshot SHA:** 811e1ae906fdaa8e69a1442ccb5809ba98a16429
**Audited:** 2026-07-01

---

### Overview

Iter-9 is a pure backend infrastructure milestone: the "sustainable trial economy" — an injectable,
default-off online-FDR (LORD++) deflation policy + a separate internal staging ledger. The iteration
carries no frontend changes, introduces no new displayed values, adds no new endpoints, and makes no
information-architecture change. The UI surface map explicitly confirms "N/A — Backend-only phase
(Frontend Present: no). No UI surfaces affected."

The blueprint's Data Contract was pre-amended with an iter-9 clarification block that explicitly
documents the new internal deflation-policy seam as "no displayed value, no new serving endpoint, no
nav-skeleton change" — exactly what the diff confirms.

---

### Step 1 — Data Contract check

The single contract value of concern is:

> **Evidence status + certified-claim** — computed by `app.engine.referee:certify_edge` via
> `app.mcp.tools:verify_edge`; served by `GET /api/evidence`.

**Duplicate computation?**

The new `apps/backend/app/engine/online_fdr.py:test_level` computes a per-trial significance
*level* (an input to the referee), not the proven-ness decision itself. Proven-ness still flows
solely from `verdict.status == PASS` inside `certify_edge`. No second computation of the contract
value was introduced.

The `referee.py` refactor makes deflation injectable with Bonferroni as the default — every existing
`certify_edge` call reproduces today's `required_p` byte-identically when `state.test_level is None`
(the default). This is a restructuring of the existing canonical module, not a duplicate.

**Non-canonical source?**

No frontend files were changed. `GET /api/evidence` is unmodified. The staging ledger
(`staging-ledger.jsonl`) is described in the blueprint clarification and in the spec as
"NEVER read by `GET /api/evidence`; never served, never displayed." The diff confirms no
new API endpoint and no UI fetch from any new path.

**New unregistered displayed values?**

None. The spec states "New information displayed: None" and no UI surface was touched.

Result: **no Part A violations**.

---

### Step 2 — Information Architecture check

**New routes or pages?**

None. The diff contains only Python backend files, `config.yaml`, the gate script, and the
harness entrypoint. Zero frontend or router files changed.

**Navigation reachability?**

No new nav entries needed; the IA is unchanged. The blueprint's nav skeleton is intact.

**Duplicate homes?**

None introduced.

**Parallel shell?**

None introduced.

Result: **no Part B violations**.

---

### Step 3 — Subjective observations (advisory)

None. There are no UI or formatting changes to assess.

---

### Summary

This iteration is a backend-only infrastructure milestone that strictly confines all changes to the
certification engine's internal seams (referee, ledger, verify_edge, gate, harness). The canonical
`/evidence` endpoint, every "Proven" badge, and the whole information architecture are untouched and
byte-identical. No coherence drift was introduced.
