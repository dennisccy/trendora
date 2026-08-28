# Iteration 26 — Coherence Audit

**Iteration:** goal-market-compass-iter-26
**Date:** 2026-08-28
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Scope confirmation

Diffed against snapshot SHA `05155342fb6f0d866c28593a19d5772fa78c5335`:

```
git diff <sha> --stat -- . (noise-excluded)
 apps/backend/tests/test_api_compass.py         |  77 +++++++++-
 apps/backend/tests/test_manifest_invariants.py | 189 ++++++++++++++++++++++++-
 2 files changed, 258 insertions(+), 8 deletions(-)
```

Confirmed against the bounded diff (`runs/goal-session-market-compass/iter-26/iter-diff.md`, 2 files
shown in full — nothing truncated) and `git status --porcelain -uall`: the only tracked-file changes
this iteration are `apps/backend/tests/test_api_compass.py` and
`apps/backend/tests/test_manifest_invariants.py`. Zero production code (`apps/backend/app/**`), zero
frontend (`apps/frontend/**`) changed. Every other touched/untracked path is harness bookkeeping
(`runs/**`, `reports/**`, `docs/handoffs/**`, `docs/phases/**`, `state/blueprint.md`'s own iter-26
note) — outside review scope per the invocation prompt and the skill's exclusion list. This matches
the pump coordinator note exactly.

The one live action this iteration performed against the canonical database — `POST
/api/compass/regenerate?as_of=2025-04-15` via the existing manifest strip's confirm-gated control —
is a code-free data event: it exercises an already-built, already-registered action route through its
already-built, already-registered UI control. No code diff corresponds to it because none was needed.

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Next-session manifest — CONTENT block | OK | No new producer/endpoint in diff; tests only exercise `compass.get_or_create_manifest` / `compass.manifest_row_payload` (pre-existing, `apps/backend/app/engine/compass.py`, untouched this iteration) |
| Next-session manifest — FREEZE/INTEGRITY block (`basis`, hashes, provenance) | OK | New tests (`test_api_compass.py` TC-8/TC-9 test; `test_manifest_invariants.py` TC-2, TC-7) call only the registered `compass.basis_disclosure`, `compass.manifest_row_payload`, `compass.verify_manifest_hash`, and the `GET /api/compass` route function (`app.api.compass.compass`) — no second computation path introduced |
| `POST /api/compass/regenerate` (action route) | OK | Not touched in this diff; exercised live via its existing UI control only. Reviewer/dev handoff confirm INSERT-only, `v1` bytes unchanged (`docs/handoffs/goal-market-compass-iter-26-dev.md:175-178`) |

No new function, service, or endpoint was added anywhere in this iteration's diff (both changed files
are `apps/backend/tests/*`), so there is no candidate for "duplicate computation" or "non-canonical
source" to check — the rule has nothing to bite on. No new displayed value is introduced (spec's own
"New information displayed: None" is corroborated by the empty production diff).

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no new page/route this iteration) | OK | `apps/frontend/**` has zero diff lines against the snapshot SHA; sidebar/nav unchanged |

The regenerate action was triggered through the manifest strip's pre-existing confirm modal
(`data-testid="compass-manifest-regenerate-confirm-modal"` / `-confirm-button`, per the dev handoff),
which already lives at its blueprint-registered home (`/` — Today, manifest strip row). No parallel
shell, no duplicate home, no new nav entry.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- **Standing B2 finding, re-verified (not new, not a coherence violation):** `basis.status ==
  "unavailable"` is real, unit-tested code in `compass.basis_disclosure` that is structurally
  unreachable via the live `GET /api/compass` route, because `run_scan`'s self-heal recreates a
  missing `ScannerRun` before `basis_disclosure` ever observes it as absent (new evidence this
  iteration: `test_compass_route_never_404s_and_manifest_bytes_survive_a_removed_historical_run` in
  `apps/backend/tests/test_api_compass.py`, added after `test_regenerate_route_mints_version_2...`).
  This is a serving-path *honesty* question (does the route ever tell the truth about the
  "unavailable" state), not a duplicate-producer or non-canonical-source question — the value still
  has exactly one computing module and one serving endpoint, it just can't reach one of its own
  documented states given current self-heal ordering elsewhere in the code. Out of this gate's FAIL
  criteria; carried forward as-is (first flagged iter-3, re-confirmed iter-26) for the decomposer/AG-1
  honesty lens to pick up, not for this audit to block on.
- Blueprint's own iter-26 note (`state/blueprint.md`, appended this iteration) independently states
  "no IA change, no Data Contract row change" for this iteration — consistent with what the diff
  shows.
