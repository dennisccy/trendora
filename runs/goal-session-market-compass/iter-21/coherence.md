# Iteration 21 — Coherence Audit

**Iteration:** goal-market-compass-iter-21
**Date:** 2026-08-27
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Diff-discovery note

`runs/goal-session-market-compass/iter-21/iter-diff.md` does not exist. `git diff
122b6a77e3adbbb22bd016194d2b376e8b679029 --stat -- .` (noise-excluded) returns **empty** for every
tracked path — this iteration's real content is four **untracked** new files, which `git diff <sha>`
never surfaces (the same tooling artifact flagged in iterations 19 and 20's coherence audits). Verified
via `git status --porcelain -uall` and read directly:

- `apps/backend/app/engine/j11_stage_f_execute.py` (751 lines, new)
- `apps/backend/scripts/run_j11_stage_f_execute.py` (434 lines, new)
- `apps/backend/tests/test_j11_stage_f_execute.py` (1,109 lines, new)
- `apps/backend/tests/test_j11_stage_f_execute_cli_script.py` (458 lines, new)

No path under `apps/frontend/` appears anywhere in `git status --porcelain -uall` (modified or
untracked). Zero tracked production files were modified (`git diff <sha> --stat` on tracked paths is
empty; the only ` M ` entries in `git status` are harness bookkeeping under `runs/goal-session-
market-compass/` — session.json, telemetry, trace, assumptions.md, lessons.md — outside review scope).

## Scope note

Iteration 21 executed J-11 Stage F: dependency-aware derived-cache invalidation. It is a backend-only,
no-UI maintenance iteration. The iter spec's own "New user-facing capability / New information
displayed / New user actions / UI surface changes / Product surface delta" fields are all `None`,
"Frontend Present" is `no`, and `reports/phase-goal-market-compass-iter-21-ui-surface-map.md` confirms
maintenance isolation was held for the whole iteration ("No surface was opened or inspected"). I
independently confirmed this rather than accepting the spec's framing — read the full new module and
CLI script, the dev handoff, and the auditor's PASS_WITH_GAPS report.

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Coverage payload (`data_manager.coverage_from_storage` → `GET /api/data`) | OK — untouched | `data_manager.py` shows zero ` M ` in `git status --porcelain -uall`; `j11_stage_f_execute.py` never imports or calls `coverage_from_storage` |
| Data-availability payload (`data_manager.availability_from_storage` → `GET /api/data/availability`, pre-existing, not itself a registered blueprint row) | OK — same single producer, same single endpoint, before and after | see "Availability" analysis below |
| Sector/theme/stock scores, market phase, breadth, regime, evidence, run summary (all other registered rows) | OK — not touched this iteration | none of `scoring.py`/`compass.py`/`sectors.py`/`themes.py`/`market_phase.py`/`research.py`'s public API/`app/api/*` appear in the diff; dev handoff + auditor (§3 "Scope") both grep-confirm zero production-file modification outside the four new files listed above |

**Availability — the item the coordinator flagged as most likely to bear on this gate's rules.** I
assessed this independently rather than deferring to the decomposer's "no Data Contract change" framing:

- `data_manager.availability_from_storage` (the sole existing computing/serving function behind `GET
  /api/data/availability`) is **not modified** — confirmed by `git status --porcelain -uall` (zero
  ` M ` entries for `apps/backend/app/engine/data_manager.py`) and independently by the auditor's own
  grep (audit report §3 "Scope": "grepping it against ... `data_manager.py` ... returns zero matches").
  `j11_stage_f_execute.py`'s module docstring (`:71-74`) states it "reads
  `data_manager.availability_from_storage`/`coverage_from_storage`'s DOCUMENTED behavior ... it does not
  modify a line of any of them" — I verified this against the actual diff, not merely the comment.
- The iteration's one write (`execute_stage_f_cache_disposition`, `j11_stage_f_execute.py:582-608`)
  deletes rows from `availability_cache`, a storage table `availability_from_storage` already read from
  before this iteration existed. No new table, no new column, no new endpoint, no new UI fetch, no
  client-side recomputation was added. Before and after Stage F, exactly one function computes/serves
  this value and exactly one endpoint exposes it — the definition of "canonical" the Data Contract
  protects is unchanged.
- What changed is the **data state** the one existing pipeline reads: a stale row that made
  `availability_from_storage`'s stamp-mismatch branch (`data_manager.py:1741-1747`/`:1760-1763`) serve
  pre-incident content labeled `stale: False` was deleted, so the same unmodified function now falls
  through to its own pre-existing `row is None` branch (`:1755-1761`) and serves the honest "not yet
  computed" sentinel instead. This is a **data-lifecycle transition through the single canonical path**,
  not a second code path computing the value differently — there is nothing to duplicate-compute-FAIL or
  non-canonical-source-FAIL against, because no second implementation and no second serving path exist
  at any point in this diff.
- Conclusion: this is outside Part A's rules on the merits, not merely by the decomposer's assertion.
  Part A exists to catch *structural* divergence — two live code paths that could disagree on the same
  displayed value. Whether the *one* path's current answer is factually correct at a point in time is
  AG-3/AG-8 territory (correctness of the served figure), which the auditor already adjudicated
  (PASS_WITH_GAPS, findings B1–B3) — a distinct concern from the coherence gate's "one source of truth
  structurally" mandate. I did not find grounds to treat it otherwise.
- No Data Contract row for "availability" exists in the blueprint today (it predates this session, is
  part of the "existing app shell, unchanged" platform the blueprint's own preamble describes, and this
  session's Data Contract table only enumerates values the compass work touches). That is consistent,
  not a gap this iteration created — see Advisory notes for one forward-looking suggestion.

No new function, service, endpoint, or client-side computation appears anywhere in the four new files
for any registered Data Contract value. The new module's internal analysis helpers
(`compute_live_stamp_for_table`, `evaluate_membership_timeline_incremental_reuse_safety`) dispatch to
the EXISTING stamp/version functions directly — `research._dataset_version` (`j11_stage_f_execute.py:480`),
`research._membership_dataset_version` (`:482`), `indexes.index_series_dataset_version` (`:484`), and
`data_manager._membership_bars_are_forward_only` (`:422`) — never reimplementing them. These are
maintenance-classification signals (is a cache row safe to keep?), never served to any endpoint or
displayed on any page, so they are not "displayed values" under Part A's scope in the first place.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no new page/route/feature this iteration) | N/A | `apps/frontend/components/sidebar.tsx` not touched (absent from `git status --porcelain -uall`); no file under `apps/frontend/` appears in the diff at all |

No new page, route, endpoint, or UI element was introduced. There is nothing for Part B's four rules
(no-nav-path / reachability / duplicate-home / parallel-shell) to evaluate against — the nav skeleton in
`runs/goal-session-market-compass/state/blueprint.md`'s Information Architecture section is unchanged
and unaffected.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- **Forward-looking suggestion, not a defect of this iteration.** `GET /api/data/availability` /
  `data_manager.availability_from_storage` has no explicit row in the blueprint's Data Contract table
  (only "Coverage payload" — a different endpoint/function — is registered for the `/data` surface).
  This iteration's central correctness finding (BACKGROUND finding 4) turns entirely on that function's
  behavior, so if a future iteration does meaningful product/UI work on the Data Manager page's
  availability heatmap, the decomposer should add an explicit Data Contract row for it at that time
  (mirrors Part A rule 5's spirit; not triggered here because this iteration displays nothing new).
- The auditor's B1 (stale `MembershipTimelineCache` docstring/field-comment at `models.py:695-701`,
  `:712`) is a documentation-hygiene gap, not a coherence violation: the module dispatches from the
  correct call site (`data_manager.py:884`) rather than trusting either stale comment, so no divergent
  live computation exists — confirmed independently by reading `CACHE_KEY_FAMILY` (`j11_stage_f_execute.py:131-139`)
  and `compute_live_stamp_for_table` (`:473-485`). Already tracked by the auditor for a future
  non-maintenance iteration; nothing further for this gate to add.
- The auditor's B2 (the `membership_timeline_cache` preservation proof is a snapshot of today's state,
  not a standing invariant) and B3 (deleting `event_study_cache`/`forward_aggregate_cache` removes two
  serve-a-prior-generation fallbacks whose post-Stage-G cold-path cost is undocumented) are real,
  already-recorded correctness/operational-risk gaps — but neither creates a second producer, a second
  endpoint, or a nav/duplicate-home problem, so neither is a Part A/B matter. Recommendation already on
  record in the auditor's report (§5, items 1–2) for the Stage G decomposer.
