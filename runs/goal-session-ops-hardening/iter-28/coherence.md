# Iteration 28 — Coherence Audit

**Iteration:** goal-ops-hardening-iter-28
**Date:** 2026-07-27
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Data Contract check

Iteration scope per the spec and blueprint iter-28 paragraph: relocate `_DEFAULT_DRIFT_REPORT_PATH`
(`apps/backend/app/config.py`) and `config.yaml`'s `data_quality.drift.report_path` from the closed
`goal-session-mcp-loop` folder to this session's own `runs/goal-session-ops-hardening/state/`, plus a
golden-script assertion fix (test infra, not a Data Contract value). No new Data Contract row was
claimed and none was needed.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Backend readiness / boot phase + preflight verdict (`readiness.severity.drift` component) | OK | `apps/backend/app/config.py:2286` (only the path string literal changed); `app.engine.drift` / `resolve_drift_report_path()` untouched — confirmed no diff hunk touches `app/engine/drift.py` |
| `GET /api/data`'s additive `drift` field | OK | same computing module/endpoint, no diff to the endpoint handler |
| Coverage payload (`coverage_status`: current/stale/not_yet_computed) | OK — pre-existing, documentation-only touch | `apps/frontend/app/data/page.tsx:759-764` already renders the "Coverage as of a prior scan (version {stale_dataset_version})" label (built iter-27); `README.md`'s Data Manager bullet was only reworded to describe this already-registered, already-built value — no new producer, no new fetch |
| drift-report.json artifact itself | OK | `git diff --stat -M` shows a pure rename (`runs/goal-session-mcp-loop/state/drift-report.json` → `runs/goal-session-ops-hardening/state/drift-report.json`), "similarity index 100%", zero content diff — byte-identical, confirms the spec's "moves ... byte-identically" claim |

No new function/endpoint computes any registered value independently of its canonical module. No new
UI surface reads a registered value from a non-canonical source (no frontend file is in the diff at
all — confirmed by `git diff --stat` against the snapshot SHA: only `apps/backend/app/config.py`,
`config.yaml`, `README.md`, plus the excluded-path set `journey-scripts/J-06.json` (test artifact),
`state/blueprint.md` (narrative), `state/drift-report.json` (renamed artifact), and harness
bookkeeping (`telemetry.jsonl`, `trace/*`, `iter-28/*`) changed).

## Information Architecture check

No new page, route, or nav entry was introduced or claimed by the spec, and none is present in the
diff — confirmed by `git diff --stat` showing zero touches under `apps/frontend/`. Checked
`apps/frontend/components/sidebar.tsx` is unmodified (not in the diff); the existing 11-item nav
skeleton is unaffected.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no new surface this iteration) | OK | `git diff --stat` shows no `apps/frontend/*` file changed; `sidebar.tsx` absent from the diff |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- Minor documentation-lag note (not a violation): the Data Contract table's "Backend readiness / boot
  phase + preflight verdict" row (`state/blueprint.md:339`) does not itself carry an iter-28-dated
  sentence naming the drift-path relocation — only the free-text iter-28 narrative paragraph
  (`state/blueprint.md:278`) documents it. The invariant (same computing module, same two endpoints)
  is intact regardless, so this is cosmetic bookkeeping, not a coherence defect; the next iteration
  touching that row can fold in a one-line mention for consistency with the row's own convention of
  per-iteration append notes.
- No other advisory issues found: no label/formatting drift, no parallel shell, no unregistered new
  value. This iteration's own review report (`reports/reviews/goal-ops-hardening-iter-28-review.md`)
  independently confirms the same scope (config relocation + golden-script fix, zero frontend touch),
  consistent with this audit's findings.
