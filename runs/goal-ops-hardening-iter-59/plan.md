# goal-ops-hardening-iter-59 Execution Plan

## What to Build

- **Profile `compute_regime_lab`'s peak memory under a concurrent forward-aggregate warm** (`apps/backend/
  app/engine/research.py:4361`), confirming or correcting the diagnosis already stated in the spec: unlike
  `compute_factor_lab_all`, which processes one `(factor, horizon)` at a time and releases it,
  `compute_regime_lab` calls `_regime_lab_members_by_horizon(session, horizons, as_of, cfg=cfg)` ONCE
  (research.py:4399) and retains **all** horizons' observation pools (`pools: dict[int, list[dict]]`)
  simultaneously, then further retains `members_by_h[h]` (the post-episode-collapse set) for every horizon
  before the by-label/by-decile loops run. That is the same all-at-once-retention shape iter-46/49/50/51
  already bounded for `_all_factor_observations_by_horizon` / `compute_forward_aggregates`. Measure first
  — do not assume the diagnosis is correct without a live reproduction (the spec's own binding discipline).
- **Bound `compute_regime_lab` so a horizon that cannot complete under memory pressure degrades only that
  horizon (isolate-and-continue), never an uncaught `MemoryError` reaching `GET /api/research/regime-lab`
  as a 500.** The proven pattern to mirror is `compute_factor_lab_all`'s per-`(factor, horizon)` loop
  (research.py:1404-1475): a `try/except MemoryError` (plus a broader `except Exception` per the iter-50
  audit B4 lesson — one entry's OTHER failure must not 500 the whole response either) around the
  memory-heavy per-horizon work (the episode collapse + label/decile aggregation for that horizon), each
  restructured to build-process-release ONE horizon before moving to the next, instead of holding every
  horizon's pool in RAM at once. `data_manager._fault_inject_memory_error(...)` is the existing test-only
  hook (research.py:3915-area) to reuse for the injection test, same convention as
  `compute_factor_lab_all`'s `_fault_inject_memory_error("factor_lab_all")`.
- **Byte-identity requirement:** every horizon that DOES complete must still equal the pinned pre-fix
  reference output exactly — this is a memory-bounding refactor, not a behavior or number change. Follow
  `compute_factor_lab_all`'s own precedent test shape for the equality fixture.
- **CONDITIONAL new payload fields** (only if the profiling pass shows a partial-degrade signal is
  genuinely needed): `by_horizon[].status: "unavailable"` on both `by_label[].by_horizon[]` and
  `by_decile[].by_horizon[]` entries for the horizon(s) that degraded, plus a whole-response
  `regime_lab_status: "unavailable"` flag when at least one horizon degraded — same computing module
  (`compute_regime_lab`), same endpoint (`GET /api/research/regime-lab`), no second producer, no new table.
  Mirrors the ALREADY-SHIPPED Factor Lab sibling fields (`by_horizon[].status`,
  `factors_status: "unavailable"`, research.py:1474/4092). If the profiling pass finds no partial-degrade
  signal is needed (e.g. the bound alone keeps every horizon inside the memory budget in practice), do NOT
  add these fields — record "no field added, profiling showed X" in the dev handoff and drop the
  `[TARGET]` tag note.
- **`regime_lab_cached`'s cache-write discipline** (research.py, the `EventStudyCache`-backed wrapper
  around `compute_regime_lab`) needs the SAME "never cache a degraded payload" guard `factor_lab_all_cached`
  already has (research.py ~4108-4120, `_degraded` check before persisting) — a degraded response must
  never be written to `EventStudyCache` and served stale after the pressure clears. Reuse or closely mirror
  that existing check; do not introduce a second cooldown/degrade-tracking mechanism unless the profiling
  pass shows the single-flight/cooldown apparatus is also needed (Factor Lab's `_FACTOR_LAB_ALL_LOCK` /
  `_degraded_cooldown_*` machinery) — only add it if a live reproduction shows the same repeated-doomed-
  compute amplification risk Factor Lab had; otherwise keep the fix to the isolate-and-continue bound plus
  the never-cache-degraded guard, per rule 5's "one risky product-code action" discipline.
- **Frontend, CONDITIONAL on the backend shipping the status fields:** `/research/regime-lab`
  (`apps/frontend/app/research/_labs.tsx`, `RegimeLabByLabelTable` at line 4020 and `RegimeLabDecileTable`
  at line 4108, rendered from `RegimeLabPage` at line 4238) — extend the existing NA-cell convention
  (`na = cell.low_sample || cell.n === 0 || value === null`, used identically at ~8 call sites in this
  file) to also treat `status === "unavailable"` as NA, with a distinct tooltip/label ("temporarily
  unavailable — degraded under memory pressure" or similar honest copy) so the affected horizon's column
  renders a contained placeholder, never a blank crash, never a fabricated number — mirroring whatever
  rendering convention the Factor Lab uses for its own `status`/`factors_status` fields (grep
  `apps/frontend/app/research/_labs.tsx` and `apps/frontend/lib/factor-lab-evidence.ts` for the exact
  existing pattern before writing new logic — do not invent a new visual language for this). If the
  backend ships no new field this iteration, skip this file entirely and record why in the dev handoff.
- **Developer executes J-05 step 3 directly** (per the iter-58 evaluator's explicit assignment — browser-QA
  may not restart the app): after a completed backfill, restart via `scripts/start-backend.sh` (host-guard
  caps unchanged), confirm `/data` cold renders the persisted coverage payload within its committed budget
  with no `daily_prices`-scale prefill (`logs/backend.log` check). This is verification of already-built,
  evaluator-confirmed code (iter-8/iter-9) — no code change expected. If a genuine defect surfaces, file it
  as a note for iteration 60 rather than fixing it alongside the regime-lab bound (rule 5: one risky
  product-code action this iteration).
- **`journey-scripts/J-05.json` golden-date re-verification:** confirm the currently-reserved date
  (`2010-11-02`, rotated twice in iter-58 per its dev handoff) still holds 0 `scanner_runs` rows
  immediately before any lane uses it this iteration; rotate again in the same commit if a prior lane
  already consumed it. The developer's OWN step-3 restart-and-cold-check exercise must use a DIFFERENT,
  already-ingested date so it never consumes the golden's reserved precondition date (iter-55 lesson, now
  TC-12).
- **Drill-reporting discipline (binding this iteration, not a reminder):** every latency/health-poll drill
  (the J-07 warm+concurrent-request measurement; any J-05 restart timing) must publish its raw log's line
  count (`wc -l`), single slowest answer (value + timestamp), and a measurement window bounded by the job's
  own logged OPEN/CLOSED markers — reconciled against the raw log before any "zero failures"/"N polls"
  claim lands in `reports/perf-budgets.md`, the dev handoff, or `status.json`. iter-58's Addendum 24 is the
  template to follow exactly (segmented table: whole log / pre-window / during-window / post-window,
  reconciled sum == `wc -l`).
- **Full 8-journey browser/replay lane runs LAST**, after all code (including any coherence-auditor
  audit-fix) lands. Any post-lane finding needing a further code change is filed as a note for iteration 60,
  not applied inside this dispatch (TC-7/TC-9's ordering rule).
- **`demo.sh ops-hardening --session-live` walkthrough** for both J-05 and J-07, `[NEW]`-flagged, with
  every captured frame opened and visually confirmed (not merely hashed for distinctness) before being
  cited as evidence (iter-58 lesson, now TC-10).

## Agents Required
- backend-data: yes -- the `compute_regime_lab` memory-bounding fix (research.py), the CONDITIONAL
  `by_horizon[].status`/`regime_lab_status` fields, the never-cache-degraded guard on `regime_lab_cached`,
  the byte-identity fixture test, the `MemoryError`-injection test, J-05 step 3's live restart-and-verify,
  the golden-date re-verification/rotation, and every drill's raw-log reconciliation.
- frontend-ux: yes -- CONDITIONAL `/research/regime-lab` degrade-column rendering (only if the backend
  ships the status fields this round); otherwise this agent's scope is empty and that must be stated
  explicitly in the dev handoff rather than silently skipped.

## Frontend Present: yes

(Conditional per the phase spec's own metadata line — the regime-lab degrade UI ships only if profiling
shows it is needed. Browser-QA must still exercise both target journeys' full acceptance steps regardless
of whether the conditional UI change ships, since J-05/J-07 acceptance does not hinge on that UI delta
alone — it hinges on the backend never 500ing and the restart-and-cold-load behavior.)

## Files to Create/Modify

- `apps/backend/app/engine/research.py` -- bound `compute_regime_lab` / `_regime_lab_members_by_horizon`
  usage to process-and-release one horizon at a time; per-horizon `try/except MemoryError` + `except
  Exception` isolate-and-continue; CONDITIONAL `by_horizon[].status` / `regime_lab_status` fields;
  `regime_lab_cached`'s never-cache-degraded guard.
- `apps/backend/tests/` (the research test file covering `compute_regime_lab`, likely
  `test_research.py` or similar -- confirm exact filename before writing) -- byte-identity fixture test
  (every horizon × `{as_of` scoped, unscoped`}` vs a pinned pre-fix reference); `MemoryError`-injection
  isolate-and-continue test mirroring the existing `spawned_backend_fault_injected` pattern; a
  never-500/degrades-honestly test for `GET /api/research/regime-lab` under injected pressure.
- `apps/frontend/app/research/_labs.tsx` -- CONDITIONAL: `RegimeLabByLabelTable` (line 4020) /
  `RegimeLabDecileTable` (line 4108) NA-cell extension for `status === "unavailable"`.
- `runs/goal-session-ops-hardening/journey-scripts/J-05.json` -- re-verify/rotate the golden date if
  consumed; record in `_notes`.
- `reports/perf-budgets.md` -- new dated addendum: TC-4 VmPeak-vs-8192MB margin, TC-5's segmented
  health-poll drill (Addendum 24's table format), J-05 step-3 restart-and-cold-load timing.
- `docs/handoffs/goal-ops-hardening-iter-59-dev.md` -- dev handoff (required by DoD).
- `docs/handoffs/goal-ops-hardening-iter-59-frontend.md` -- only if the conditional frontend change ships;
  otherwise the dev handoff must explicitly record "no frontend change, profiling showed X."

## UI Evolution

- New user-facing capability: none new — this closes a reliability gap (a page that could 500 under
  concurrent memory pressure now degrades honestly instead) and executes an already-built verification step
  (cold-restart coverage rendering), not new capability.
- New information displayed: CONDITIONAL — an honest per-horizon "temporarily unavailable" marker on
  `/research/regime-lab`, only if the backend profiling pass determines it is needed. Mirrors the existing
  Factor Lab convention; not a new kind of information for the product.
- New user actions: none.
- UI surface changes: `/research/regime-lab` only (conditional degrade-state rendering). No new page,
  route, or nav entry.
- Navigation changes: none.

## Visual Requirements

- Component patterns: reuse the EXISTING NA-cell rendering already used ~8x in `_labs.tsx`
  (`na = cell.low_sample || cell.n === 0 || value === null` → muted `"—"` span with an explanatory
  `title` tooltip) — extend the same predicate/component, do not introduce a new cell type or visual
  treatment. Check `apps/frontend/lib/factor-lab-evidence.ts` and the Factor Lab's own `status`-aware
  rendering (if it exists there) for the closest sibling precedent before writing new markup.
- Layout: unchanged — `RegimeLabByLabelTable` / `RegimeLabDecileTable` keep their existing table structure;
  only the per-cell NA condition and its tooltip copy change.
- Key visual effects: none new — this is a data-honesty fix within existing table styling, not a new visual
  surface.
- States to handle: the new "unavailable" NA state must read distinctly (via tooltip copy) from the
  existing "low sample" and "no observations" NA states — factual, no reassurance language, per AG's
  standing "never hype" rule. Never a blank cell with no explanation.

## Key Test Scenarios

- TC-1 through TC-12 as specified verbatim in `docs/phases/goal-ops-hardening-iter-59.md`'s Testing
  Requirements section — do not paraphrase or drop any; TC-9 (host-guard `git diff --stat` empty) and TC-12
  (golden-date rotation discipline) are easy to silently skip and must be explicitly checked.
- Byte-identity: `compute_regime_lab`'s bounded implementation vs. the pinned pre-fix reference, every
  configured `walk_forward.horizons` value, both `as_of`-scoped and unscoped (TC-6).
- Concurrency: a forward-aggregate warm covering all horizons running concurrently with
  `GET /api/research/regime-lab` never returns a raw 500 — either full byte-identical success or an honest
  per-horizon `unavailable` marker (TC-3).
- Memory: VmPeak stays under 8192 MB through the warm+concurrent-request scenario, margin recorded (TC-4).
- Availability: `GET /api/health` polled at 1 Hz throughout the same scenario, 0 non-200, ≤2s relaxed
  ceiling, raw-log-reconciled before any claim is written (TC-5).
- J-05 step 3 (previously unexecuted): `kill -9` the backend after a completed backfill, restart via
  `scripts/start-backend.sh`, cold `/data` load renders persisted coverage within budget with no
  `daily_prices`-scale prefill in `logs/backend.log` (TC-1); `/scanner-runs` and the home market-phase card
  serve stored values with no new `scanner_results`/`forward_returns` rows created by the page load itself
  (TC-2, watermark before/after).
- Full 8-journey regression (J-01, J-03, J-04, J-06, J-08, J-09 required-still-passing + J-05, J-07
  targets) via the browser/replay lane, run LAST after all code lands (TC-7/ordering rule).
- Injected-`MemoryError` unit test for the bounded `compute_regime_lab` path, isolate-and-continue
  confirmed at the unit level (mirrors `_fault_inject_memory_error` convention).
- Frontend (conditional): `status === "unavailable"` on a horizon column renders the contained placeholder,
  never blank, never fabricated (TC-11) — only if the field ships.

## Out of Scope (flagged, matches phase spec's own OUT OF SCOPE section — no drift)

- Moving heavy compute into its own process (owner-blocked, 9 rounds running).
- Whether the 20-minute finalize budget applies under live traffic (owner-blocked).
- Regime Lab's broader UI/feature backlog beyond the conditional degrade marker.
- Re-measuring `/api/regime-history`'s existing latency reading.
- `TI-1`/`TI-2` test-infrastructure tickets.
- The long-carried CARRIED-list items (iter-29/b through iter-57/l) — untouched.
- Any live-fetch drill trigger — all ingest this iteration is Backfill against the committed seed only
  (AG-9).

No drift found between the phase spec and `docs/goal.md`: this iteration directly serves J-05 (Key
Capability 4/6 — instant-serving boot, per-page minimal loading) and J-07 (Key Capability 3 — ingest-time
aggregate maintenance without taking the service down), stays inside the "compute at ingest, serve from
storage" improvement direction, and does not touch `memory_cap_mb`/`host-guard.env` values (TC-9 enforces
this). The owner's 2026-07-31 amendment already re-set the 8192 MB ceiling this iteration must stay under
without weakening.
