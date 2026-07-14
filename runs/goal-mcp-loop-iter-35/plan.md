# goal-mcp-loop-iter-35 Execution Plan

Journey: **J-21** — live-vs-seed drift monitor (overlap check). When a live fetch re-adjusts a symbol's
already-committed history, the platform detects it, names the symbol + mismatching dates as an
"adjustment seam" in a single drift-report artifact, and the daily preflight verdict (J-20) degrades to
`DEGRADED` with that reason. Binding spec: backlog **B-304**, overlap check (a) only (distribution-envelope
and the B-113-dependent seam scan are explicitly deferred — B-113 doesn't exist yet). Depth = **full** (per
the iter spec's own trigger: crosses backend+frontend, touches the data-integrity-sensitive FETCH path,
feeds the cross-cutting J-20 verdict, needs a fixture-matrix beyond browser smoke). No `## Evidence Claim`
— the post-decompose gate passes automatically; canonical Bonferroni divisor stays 8.

Verified against `docs/goal.md`: J-21 is a genuine Must-have journey (goal.md lines 400-410) and its
acceptance matches this spec's DoD exactly (overlap-only scope, single-source drift artifact, readiness
degrade/recover, no auto-repair). Required-still-passing (J-20, J-13, J-16, J-01, J-05) matches the DoD.
No scope creep detected — IN SCOPE / OUT OF SCOPE in the phase spec already tightly bounds the work to J-21's
binding acceptance.

## What to Build

- **New PURE module `app/engine/drift.py`** (backend):
  - `build_drift_report(fetched_bars, seed_bars, *, overlap_days, reference) -> dict` — byte/fixed-precision
    OHLCV compare (never loose float) over the last `overlap_days` dates common to a fetch and the
    **committed seed CSVs** (`data/seed/prices/{symbol}.csv` — confirmed 590 files on disk; NOT the DB,
    which is insert-new-only). Returns `{status: "clean"|"drift", reference, overlap_days, affected:[{symbol,
    mismatching_dates, classification:"adjustment_seam"}]}`. Never mutates/reconciles/re-fetches.
  - `resolve_drift_report_path()` — mirrors `app/engine/evidence.py:resolve_ledger_path()` exactly (confirmed
    pattern at evidence.py:47-59: env override `TRENDORA_LEDGER_PATH` else config path resolved against
    `REPO_ROOT`). New env var `TRENDORA_DRIFT_REPORT_PATH`, config default `config.data_quality.drift.report_path`.
  - `write_drift_report()` / `read_drift_report()` — single writer/reader pair; missing file ⇒ inert
    (treated as clean/None); unparseable ⇒ honest degraded reason, never raises.
- **Wire into the fetch pipeline** — `app/engine/data_manager.py::_run_job` (function at line 2995).
  Confirmed exact seam: `if prog.status != "resumable": prog.complete_stage("fetch")` (~line 3090). Add the
  drift check as a post-fetch validation stage immediately after that guard, so it does NOT run on a
  `resumable` pause. Also confirm it's skipped on the `elif skip_fetch and is_resume:` resume-at-backfill
  branch (no re-fetch occurred, nothing new to compare). Scrub via the existing `_make_scrubber` discipline
  (line 1895) — the artifact/logs must never contain the session API key.
- **`app/engine/readiness.py::compute_preflight`** (function at line 216) — add a fourth `_apply("drift", ok,
  detail)` call using the existing `_apply` helper (defined at line 251), placed after the existing
  `integrity` component (~lines 298-306). `ok` when the artifact is absent or `status=="clean"`; breached when
  `status=="drift"`, detail naming the affected symbols. Severity from `config.readiness.severity["drift"]`.
  The existing servability/freshness/integrity `_apply` calls and their composition logic stay byte-identical.
- **`app/config.py::ReadinessCfg._validate`** (line 566; `required_components` set at line 567, currently
  `{"servability", "freshness", "integrity"}`) — extend to include `"drift"`.
- **`GET /api/data`** (`app/api/data.py::data_overview`, line 95) — add `"drift": read_drift_report()`
  alongside the existing `"capacity": data_manager.compute_capacity(...)` line (140), same additive pattern.
- **`config.yaml`** — new top-level `data_quality:` block (`drift.enabled`, `drift.overlap_days`,
  `drift.report_path`), mirroring the `evidence:` block's path-config shape (lines 1066-1073). Add
  `drift: degraded` to the existing `readiness.severity` map (currently lines 1250-1255, only servability/
  freshness/integrity). No magic numbers in code.
- **Frontend: new drift-report section on `/data`** (`apps/frontend/app/data/page.tsx`) — a new card
  mirroring the existing `StorageCapacityPanel` pattern (confirmed at line 752: `Card` + `PanelTitle` +
  grid of stat cells), reading the new additive `drift` field from the SAME `/api/data` client call already
  in use (no new fetch). Quiet/neutral when clean or absent; loud when `status=="drift"` (list each affected
  symbol + mismatching dates + "adjustment seam" label). Degrades gracefully on a missing field.
  - **Confirmed: `preflight-banner.tsx` and `layout.tsx` need ZERO changes.** `PreflightBanner` (read in
    full) already renders `preflight.reasons` generically as a bulleted list — a new "drift" reason string
    from `compute_preflight` will surface automatically once the backend component exists. Do not touch
    `readiness-provider.tsx` or `layout.tsx`.
- **Tests** (see Key Test Scenarios) + **dev handoff** at `docs/handoffs/goal-mcp-loop-iter-35-dev.md`.

**`blueprint.md` is already fully updated by the goal-decomposer — confirmed, no developer edit needed.**
The J-21 Information-Architecture row (line 89), the full Data Contract row for "Live-vs-seed drift report"
(line 118), and the "iter-35 clarification" paragraph (line 264) are all present verbatim in
`runs/goal-session-mcp-loop/state/blueprint.md`. This matches the iter-32/33 precedent.

## Agents Required

- **backend-data: yes** -- new `app/engine/drift.py`; `data_manager._run_job` fetch-stage wiring;
  `compute_preflight` drift component; `ReadinessCfg._validate` extension; additive `GET /api/data` field;
  `config.yaml` `data_quality.drift` block + `readiness.severity.drift`; fixture-matrix + resilience +
  byte-identity tests.
- **frontend-ux: yes** -- new drift-report card on `/data`, reading the additive field from the existing
  API client. No changes needed to the preflight banner (already generic) or layout.

(A single `developer` agent dispatch handles both streams, per this project's normal pattern.)

## Frontend Present

Frontend Present: yes

## Files to Create/Modify

Backend:
- `apps/backend/app/engine/drift.py` -- NEW. `build_drift_report`, `resolve_drift_report_path`,
  `write_drift_report`, `read_drift_report`.
- `apps/backend/app/engine/data_manager.py` -- wire the post-fetch drift-check stage into `_run_job`
  (~line 3090, immediately after the `prog.complete_stage("fetch")` guard); do not touch chunk/checkpoint
  logic otherwise.
- `apps/backend/app/engine/readiness.py` -- add the `_apply("drift", ...)` call in `compute_preflight`
  (after the existing integrity component, ~line 298-306).
- `apps/backend/app/config.py` -- extend `ReadinessCfg._validate`'s `required_components` (line 567) to
  include `"drift"`; add a typed `data_quality` config section (new `DataQualityCfg`/`DriftCfg`, mirroring
  the `evidence` block's pattern) wired into the `Config` aggregator.
- `apps/backend/app/api/data.py` -- add `"drift": read_drift_report()` to `data_overview` (line 140 area).
- `config.yaml` -- new `data_quality:` block; add `drift: degraded` to `readiness.severity`.
- `apps/backend/tests/test_drift.py` -- NEW. `build_drift_report` fixture matrix (re-adjusted/clean/
  byte-vs-loose-float trap); path-resolution env/config/REPO_ROOT tests; missing/unparseable resilience.
- `apps/backend/tests/test_readiness.py` -- extend. `compute_preflight` drift `ok`-when-absent-or-clean,
  breached-when-drift with configured severity + affected symbols in reasons, worst-severity composition
  across all 4 components; `ReadinessCfg._validate` boot-accepts/rejects the `drift` component.
- `apps/backend/tests/test_api_data.py` -- extend. Additive `drift` field present + equals
  `read_drift_report()`; honest empty/absent snapshot on a cold DB (200, never 500).
- `apps/backend/tests/test_data_manager_jobs_pipeline.py` (or `test_data_manager.py`, match whichever
  already covers `_run_job` fetch-stage completion) -- extend. Post-fetch stage runs on a completed fetch;
  does NOT run on a `resumable` pause or the skip-fetch/backfill-only resume path.

Frontend:
- `apps/frontend/app/data/page.tsx` -- add a new drift-report card (mirror `StorageCapacityPanel`'s
  `Card`/`PanelTitle` pattern), reading `state.data.drift` from the existing `/api/data` payload.
- `apps/frontend/lib/api.ts` -- add the `drift` field type to the `/api/data` response type (mirror how
  `capacity`/`DataCapacity` was added).

Do NOT touch: `apps/frontend/components/preflight-banner.tsx`, `apps/frontend/components/
readiness-provider.tsx`, `apps/frontend/app/layout.tsx` (already generic — renders any reason string),
`runs/goal-session-mcp-loop/state/blueprint.md` (already current), `app/engine/evidence.py`,
`app/engine/referee.py`, `app/engine/ledger.py` (no evidence/ledger work this iteration).

## UI Evolution

- New user-facing capability: an operator running a Fetch job can see, on `/data`, whether the freshly
  fetched bars silently diverge from the validated committed seed — and the site-wide preflight banner
  turns `DEGRADED` with that reason until the mismatch stands.
- New information displayed: a `/data` drift-report section (overall clean/drift status; on drift, the
  affected-symbol list with mismatching dates + "adjustment seam" label). The existing preflight banner
  gains a fourth possible reason source with no shape change (it already renders reasons generically).
- New user actions: none — read-only report, produced by the existing Fetch job; no new controls.
- UI surface changes: `/data` gains one read-only card. No new page, no new nav entry (J-13's already-
  registered Data Manager home).
- Navigation changes: none.

## Visual Requirements

- Component patterns: mirror `StorageCapacityPanel` exactly — `Card` + `PanelTitle` (with a hint tooltip
  explaining "descriptive integrity report, recomputes nothing") + a stat grid for the clean state; for the
  drift state, a listing (symbol → mismatching dates → "adjustment seam") similar in weight to the existing
  `RebuildPanel`/coverage-absent amber banner pattern already on this page.
- Layout: additive card within the existing `/data` page's vertical stack of panels (same column as
  `StorageCapacityPanel`, availability heatmap, job panels) — no layout restructuring.
- Key visual effects / tokens: use the project's actual tokens — `--pos` (clean/quiet), `--warn` (drift —
  matches the preflight banner's `DEGRADED` amber, `border-warn bg-warn/10 text-warn`), consistent with
  `preflight-banner.tsx`'s existing `LoudBanner` treatment. No new tokens needed.
- States to handle: no-fetch-yet / absent artifact (quiet neutral, not alarming — "no fetch has run yet",
  distinct from "clean"); clean (quiet, green-ish); drift (loud, amber, lists every affected symbol +
  dates); missing/unparseable artifact or backend-unavailable (contained honest fallback — never a blank
  crash, consistent with the page's existing `state.kind === "error"` handling).

## Key Test Scenarios

- **Browser (J-21, primary):** (1) a controlled fetch with one symbol's overlap region re-adjusted produces
  a `/data` drift report naming that symbol, the exact mismatching dates, and "adjustment seam"; (2) the
  preflight banner reads `DEGRADED` with that drift reason while the mismatch stands; (3) a clean fetch
  renders the report green/clean and the banner recovers to `GO`. Capture md5-distinct frames per surface
  per the iter-14/25 lesson (a stale/error frame cited under a PASS invalidates the citation).
- **Browser (required-still-passing):** J-20 (banner still composes GO/DEGRADED/NO-GO correctly with the
  4th component added — reuse the existing induced-DEGRADED mechanism plus this iteration's new drift
  induction), J-13 (`/data` coverage/legend un-regressed by the new card), J-01 (leaderboard evidence
  badges unaffected), J-05 (evidence ledger unaffected — this iteration touches no ledger).
- **Backend — `build_drift_report` fixture matrix:** (i) re-adjusted overlap → detected, correct symbol,
  exact mismatching dates, `adjustment_seam` classification; (ii) clean overlap → `status=="clean"`, empty
  `affected`; (iii) a byte/fixed-precision compare catches a real seam that a loose float compare would
  miss (the named B-304 trap — write this test to fail if someone "fixes" the comparator to `==` on floats
  with tolerance).
- **Backend — path resolution:** `resolve_drift_report_path` honors env override, config default, and
  REPO_ROOT resolution; `write_drift_report`/`read_drift_report` round-trip; missing file ⇒ inert; a
  corrupted/unparseable file ⇒ honest degraded read, never raises.
- **Backend — `compute_preflight`:** drift `ok` when the artifact is absent or `status=="clean"` (GO
  unchanged); a `status=="drift"` artifact forces the configured severity with affected symbols named in
  `reasons`; worst-severity composition is still correct across all four components (servability, freshness,
  integrity, drift).
- **Backend — inert on the committed seed (J-20 non-regression, load-bearing):** with no fetch run (fresh
  seed, absent artifact), the drift component is `ok` and the preflight verdict, `GET /api/health` payload,
  and the other three components are byte-identical to iter-34's baseline (confirmed this session: iter-34
  ended with `"preflight": {"verdict": "GO", "reasons": []}`, all three components `ok: true`, symbol_count
  590, warmup 89/89).
- **Backend — config validation:** `ReadinessCfg._validate` boot-accepts a `readiness.severity` including
  `drift`; rejects a config missing the `drift` component (extend the existing required-component test).
- **Backend — `GET /api/data`:** additive `drift` field present, equals `read_drift_report()` verbatim;
  honest empty/absent snapshot on a cold DB (200, never 500).
- **Backend — fetch pipeline wiring:** the post-fetch drift stage runs on a completed fetch and does NOT
  run on a `resumable` pause or the skip-fetch/backfill-only resume path.
- **Error cases:** a loose float compare must NOT silently pass a real re-adjustment; a fetch must NEVER
  auto-reconcile drifted data; the artifact must never contain a provider URL/query credential or the
  session API key (grep the written artifact in the test); a missing/unparseable artifact degrades honestly,
  never crashes `/data` or the health poll.
- **Regression:** existing preflight tests (servability/freshness/integrity) stay green; no unrelated test
  breakage.

## Notes / Risks for the Developer

- **Pre-existing uncommitted state collides with this iteration's own target files — carried forward from
  iter-33, still unresolved.** At dispatch time, `apps/backend/app/config.py`, `config.yaml`,
  `apps/backend/app/engine/{prices,scoring,warmup}.py`, and several test files (`test_config.py`,
  `test_config_engine.py`, `test_forward_testing.py`, `test_indexes.py`, `test_sectors.py`, `test_themes.py`,
  `test_warmup.py`) are already modified but uncommitted, plus untracked `test_scoring_window.py`,
  `docs/phases/goal-mcp-loop-iter-26.md`, `reports/qa/goal-mcp-loop-iter-26-test-plan.md`, and
  `runs/goal-mcp-loop-iter-26/`. This is the same stray, apparently-abandoned iter-26 WIP (looks like the
  goal.md fast-platform §F "window the scoring inputs" experiment) that iter-33's plan already flagged as
  unrelated — it has now persisted through iterations 33, 34, and into this dispatch despite iter-34's dev
  handoff recording an empty `git diff HEAD --stat` at its own completion. **Both files this iteration must
  edit (`config.py`, `config.yaml`) are already dirty.** Before editing, read the existing diff so this
  iteration's `data_quality`/`readiness.severity` additions are cleanly separable; do not fold the stray
  iter-26 content into this iteration's commit, and do not destructively discard it without confirming it's
  safe to drop (it may be salvageable work someone intended to return to).
- **Regression-replay DoD line (systemic, framework-level, carried from iter-33/34):** a FULL iteration
  routes through `run-phase.sh`, which has no deterministic-replay-lane machinery (that lane lives only in
  `goal-iter-lean.sh`). If time allows, satisfy it directly: the replay tool is a standalone script,
  `scripts/automation/lib/demo_runner.py --mode verify`, reading golden scripts from
  `runs/goal-session-mcp-loop/journey-scripts/{J-01,J-05,J-13,J-20}.json` (all four confirmed present on
  disk) and should write `reports/phase-goal-mcp-loop-iter-35-regression-replay-results.md`. If not
  completed this iteration, the spec's own fallback applies: the evaluator scores J-21 on its own canonical
  browser-qa evidence regardless, and a lean verify-only iter-36 (the iter-34 pattern) closes the gap.
  J-16 has no golden script — re-verify it via a live fetch-job run instead.
- **Post-lane fix discipline (iter-13/20/22/31 trap):** if review/audit applies any fix to the drift
  section or banner composition *after* the canonical browser-qa lane runs, a fresh browser-qa +
  ux-regression-reviewer re-run against the final build is required — a stale pre-fix browser-qa FAIL does
  not satisfy the DoD; J-21 would land `partial`, not `passing`.
- **Out of scope, confirmed no drift from goal.md:** the distribution-envelope check (b) and the
  B-113-dependent junction seam scan (c) are NOT built here (B-113 doesn't exist); no auto-repair/
  reconcile/re-fetch of drifted data; no Evidence Claim, no ledger write (`certified-claims.jsonl` /
  `staging-ledger.jsonl` stay byte-identical, divisor stays 8); no nav-skeleton change; no wall-clock time
  anywhere in the drift reference (determinism, anti-goal #5).
