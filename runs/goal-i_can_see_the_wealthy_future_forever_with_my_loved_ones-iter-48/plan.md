# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-48 Execution Plan

Completes the iter-47 J-105 streaming fix. iter-47 streamed the seven `select(ForwardReturn)…all()`
reads but left the **sibling `select(ScannerResult)…all()` reads** in the same two builders unstreamed,
each materializing ~609K ORM rows. Because **Factor Lab is UNCACHED** (it recomputes every request),
J-25 still HTTP-500s with a `MemoryError` at `research.py:216` on the live 3.3 GB DB; `_combination_observations`
(line 421) is a latent cold-miss OOM masked only by the EventStudyCache hit. This iteration streams both,
keeping every served figure byte-identical, restoring J-25 and closing J-104/J-105.

## What to Build
- Stream `_factor_observations` (`apps/backend/app/engine/research.py:216`): replace
  `session.exec(select(ScannerResult).where(ScannerResult.run_id.in_(runs_with_fr))).all()` with a
  `yield_per(batch)`-streamed iteration over the **full `ScannerResult` ORM row** (NOT a narrow column
  projection — `_extract_factor_value` needs `record_json` for component factors), `batch =
  cfg.research.read_batch_size`. Add `.order_by(ScannerResult.id)` to lock the prior implicit `.all()`
  row order so every observation/decile/rank-IC/`by_regime` figure is byte-identical.
- Stream `_combination_observations` (`research.py:421`): apply the identical `yield_per(batch)` +
  `.order_by(ScannerResult.id)` to the same `select(ScannerResult)…all()`, keeping `record_json`
  available, so the factor-combination cold-miss path can never reintroduce the OOM. Composite /
  strict-overlap cohort figures stay byte-identical.
- Audit (record in handoff, no change expected): confirm the other ScannerResult/ScannerRun reads are
  already bounded/streamed — `_regime_setup_pattern_observations` (1533, column-projected + `yield_per`),
  `_recovery_turn_observation_set` (1771, run-id-bounded + cached), `select(ScannerRun)…all()` at line ~220
  and line 2378 (bounded to `runs_with_fr`, not the full table), lines 833/986/2044 (column-projected).
  If any is found to also OOM on the live DB under the streamed standard, stream it the same way (still no
  figure change).
- Add deep-equality byte-identity tests mirroring the existing `test_research_streaming.py` (iter-47):
  the streamed `_factor_observations`/`_combination_observations` produce the byte-identical observation
  list AND `compute_factor_lab` / `compute_factor_combination` payloads vs the prior `.all()` reference —
  across as-of / all-history, a **column** factor AND a **component** (`record_json`) factor, and a
  **zero-N** cohort; chunk-independent under `read_batch_size=1` and a huge batch.

## Agents Required
- backend-data: yes -- stream the two `select(ScannerResult)…all()` reads in `research.py`, add the
  byte-identity tests, write the dev handoff with the ScannerResult/ScannerRun audit.
- frontend-ux: no -- no frontend source change is expected (`apps/frontend` diff empty).
- developer: yes -- backend-only; surgical two-read streaming + tests + handoff.

## Frontend Present: yes

(No frontend code changes. `Frontend Present: yes` is set ONLY to force the browser-QA live
render-capture step — the iter-42/43 lesson: a backend-only fix whose acceptance is a RENDERED lab
loading would otherwise auto-skip browser-QA. The acceptance is "the Factor Lab page renders real figures
on the live full dataset.")

## Files to Create/Modify
- `apps/backend/app/engine/research.py` -- stream `_factor_observations` (line ~216) and
  `_combination_observations` (line ~421): `yield_per(batch)` over full ScannerResult ORM rows +
  `.order_by(ScannerResult.id)`; `record_json` preserved; reuse `cfg.research.read_batch_size`.
- `apps/backend/tests/test_research_streaming.py` -- extend (mirror iter-47 shape) with the ScannerResult
  byte-identity / chunk-independence proofs for both builders, incl. a component (`record_json`) factor
  and a zero-N cohort. (New file allowed if a separate module is cleaner — match repo convention.)
- `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-48-dev.md` -- dev
  handoff including the ScannerResult/ScannerRun `.all()` audit.

## UI Evolution
- New user-facing capability: the Factor Lab decile/rank-IC view (`/research/factor-lab`) loads with real
  figures on the full live dataset instead of an HTTP 500 / "Backend unavailable" banner — restoring J-25
  and closing the last iter-46-affected lab.
- New information displayed: none. Every figure is byte-identical to the pre-iter-46 aggregation — this is
  a memory-safety property, not a new value.
- New user actions: none.
- UI surface changes: none — `/research/factor-lab` and `/research/factor-combination` are unchanged in
  structure; they merely render successfully (no skeleton/error) on the live DB.
- Navigation changes: none. Work lives under the existing Research IA home (blueprint.md 339–344). No
  `blueprint.reapproval-requested`.

## Visual Requirements
- Component patterns: unchanged — existing Research lab Cards / decile DataTable / `N=` chips render as-is
  once the endpoint serves 200.
- Layout: unchanged — `/research` hub + lazy-loaded sub-route panels (`_labs.tsx`).
- Key visual effects: none added.
- States to handle: the existing loading skeleton and the honest "Backend unavailable — No figures are
  shown rather than fabricated values" error banner must continue to behave; the fix removes the genuine
  fault (MemoryError) that was tripping the error state on a healthy backend.

## Out of Scope (flagged — exclude)
- Any change to a canonical score / return / membership / aggregate VALUE — figures MUST stay
  byte-identical (assert it). Single-source-of-truth / no-recompute anti-goals.
- Adding any new table, endpoint, config key (beyond reusing the existing `research.read_batch_size`), or
  magic-number literal in a CALC_FILE (`test_no_magic_numbers` blanket-forbids literals; `read_batch_size`
  already exists from iter-47, boot-validated ≥1 — reuse it).
- Re-triggering the J-85 `kind:rebuild` (~11h, destructive — the data is correct; MEMORY).
- Any **caching of Factor Lab itself** — the fix is to make the UNCACHED recompute memory-safe (streamed),
  not to introduce a new cache.
- Data-walled J-22/J-23/J-24 (provider-gated; stay honestly blocked-NA, non-vetoing per goal.md:105–108).

## Key Test Scenarios
- **J-25 (browser-qa, live):** open `/research/factor-lab`, pick a **column** factor (e.g. RS 3m) AND a
  **component** factor (one reading `record_json`), pick a horizon; the decile table (D1…D10 mean return +
  risk-adjusted + n) and a numeric rank-IC render with real figures; no skeleton/"Loading…"/"Backend
  unavailable"; HTTP 200; backend log shows **no `MemoryError` at research.py:216**.
- **J-26 / factor-combination:** `/research/factor-combination` renders the Combined cohort (cold-miss safe).
- **J-104:** all five heavy labs serve HTTP 200 (event-study, factor-lab, factor-combination,
  regime×setup×pattern, downtrend-opportunity) — one heavy fetch at a time.
- **J-51/J-63/J-65:** a Factor Lab `N=` chip opens `/research/samples` in a new tab; drill-down
  total == published cell N (count coherence).
- **J-29/J-77/J-91/J-103:** re-render with real figures — MUST STAY passing (quiet, warmed,
  single-fetch backend).
- **CRITICAL J-18 / J-07 / J-06:** 0 native `input[type=date]` on the research surfaces (single global
  as-of); Risk-Off → 0 Actionable on the snapshot-served fast path; single-source diagnostic/served
  reconcile.
- **Unit/integration:** deep-equality byte-identity of streamed `_factor_observations` vs `.all()`
  reference (observation list + full `compute_factor_lab`: deciles, rank_ic, by_regime, n_total) and of
  `_combination_observations` (composite + strict_overlap), across as-of / all-history, column factor,
  component factor, zero-N; honored `as_of` cutoff identical (param is `?as_of=` with an underscore —
  verify spelling before trusting any curl-based "ignores param" FAIL, iter-45 lesson); existing
  `test_research.py` / `test_samples.py` / `test_research_streaming.py` stay green.
- **Error cases:** unknown factor key → 422 (unchanged); a genuine fault surfaces the honest "Backend
  unavailable" banner (never fabricated data); a zero-N cohort shows honest NA, never a fabricated row.

## Operational / Evidence Hygiene (carry into QA — prior-iteration lessons)
- **Browser-QA Playwright fallback PLANNED UP FRONT** (Chrome MCP CDP has emptied the evidence dir on
  iters 38/39/40/42). **md5sum the evidence dir FIRST**; reject "Loading…"/"Backend unavailable"/skeleton
  frames as non-evidence.
- Bring up a FRESH `:8835` (wait health "ready" so warm-up finishes), `:3835`, `:9222`. **NEVER run the
  full backend suite concurrently with the heavy-lab browser probes** — its RAM/CPU pressure exacerbated
  the factor-lab OOM and yields false timeouts (iter-47); run the suite **nohup-async AFTER** the live
  probes. Fetch **one** heavy lab at a time; allow ~50–60s for the factor-lab cold compute over ~598K rows
  before the first response. If a lab shows "Backend unavailable", check whether uvicorn is hung (CPU still
  pegged) and re-run the touched modules in isolation before calling REGRESSION.
- **GOAL_ACHIEVED-candidacy gate:** the FLUSHED full backend suite must show `0 failed, EXIT 0`. Run it
  nohup-async; **never block the evaluator on the in-flight suite** (iter-11/29/37 lesson) — answer a
  CLAIMED dispatch promptly with "v1 green + targeted byte-identity tests green + full re-run in progress".
  Re-run any isolated `test_warmup.py` / `test_watchlist_persistence.py` /
  `test_data_manager_jobs_pipeline.py` E/F before attributing a suite failure (slow-boot/contention flake).

## Goal Alignment & Drift Check
No drift. This iteration directly completes the J-105 contract (goal.md:2379–2388 — "the read path never
materializes an unbounded full table … every served figure byte-identical") and the J-104 acceptance
("all five heavy labs load reliably"), restoring J-25 (goal.md:999) after the acknowledged iter-46
regression. It honors every quoted anti-goal: byte-identical figures (Single source of truth / No recompute),
no new config key or magic number, no fabricated data, no immutable-snapshot or Risk-Off-gate change.
Coherence was COHERENCE-PASS for iter-47, so this is the completion of the same J-105 work, not a forced
consolidation pass.
