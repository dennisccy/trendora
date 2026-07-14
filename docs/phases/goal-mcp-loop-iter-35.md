# Goal Iteration 35 — Live-vs-seed drift monitor (overlap check) feeding the preflight verdict

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** mcp-loop
- **Iteration:** 35
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-21
- **Required-still-passing journeys:** J-20, J-13, J-16, J-01, J-05
- **Evidence Claim:** NONE (J-21 introduces no proven-language and carries no Evidence Claim — B-304 "must not introduce proven-language anywhere"; the post-decompose gate passes automatically; canonical Bonferroni divisor stays 8)
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked values MUST render a "not yet proven" state. *(critical)*
  - **Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha claims; never place or simulate orders. *(critical)*
  - A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation for the same as-of date — not merely that the page renders. *(critical)*
  - **No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of; never introduce lookahead anywhere. *(critical)*
  - No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the post-decompose gate. *(critical)*
  - No hard-coded credentials, API keys, or tokens in source files. *(critical)*
  - **Resilience to data-shape and data-scale change:** widening the data basis (new nulls, broader pools, deeper history) must never crash an existing page or exhaust a service's memory — every existing consumer of a widened field is re-validated, the UI degrades gracefully (contained error boundary, honest "—"/NA placeholder, never a blank application-error page), and unbounded whole-table ORM loads are forbidden on the deep basis. *(critical)*

## GOAL

When a live fetch re-adjusts a symbol's already-committed history, the platform detects it, names the symbol and the mismatching dates as an adjustment seam in a single drift report, and the daily preflight verdict degrades to DEGRADED with that reason — so a silently-corrupted board can never be trusted.

## BACKGROUND

J-21 (backlog **B-304**, the live-vs-seed drift monitor) is the next unbuilt Must-have and the iter-34 evaluator's explicit next target; all 20 built journeys (J-01..J-20) are passing and the iter-34 coherence verdict was COHERENCE-PASS, so no regression or consolidation is owed (priority rubric rules 1-2 clear) — J-21 is picked alone (rules 3-5: one risky data-path surface, smallest coherent delivery, feeds the already-built J-20 preflight it shares a Data-Contract seam with). J-21's binding acceptance is the **overlap check**: byte-compare the last N common dates between a live fetch and the committed seed; a mismatch = the vendor re-adjusted history = an *adjustment seam* (B-304 check (a)). The result is a **drift-report artifact** computed once in the FETCH pipeline and re-read by both readiness (feeding the J-20 preflight verdict via the `compute_preflight` `_apply` seam at `readiness.py:251`) and the `/data` page — the single-source contract the journey demands.

**Depth = full** (triggers, per "Picking depth"): this crosses backend + frontend, touches the data-integrity-sensitive FETCH data-path (`data_manager._run_job`), feeds the cross-cutting J-20 preflight verdict that renders on every page, and needs new unit/integration tests beyond browser smoke (a three-case fixture matrix). It is exactly the risky new-served-surface class that needs the full audit / ux-regression / closure guards, and iter-34's recommendation named it FULL.

**Scope call (logged to `assumptions.md`):** B-304's card lists three post-fetch checks (overlap byte-compare / distribution-envelope / a B-113-detector junction seam scan) and its own DoD says "all three run on every FETCH," but J-21's journey acceptance exercises only the **overlap** check + the readiness effect, and the B-113 sentinel detectors the seam scan depends on **do not exist** (no sentinel/drift/quality module in `app/engine/`). This iteration scopes to the overlap check (the journey's binding contract); the distribution-envelope check and the B-113-dependent seam scan are deferred (see OUT OF SCOPE). The overlap byte-mismatch itself yields the "adjustment seam" classification J-21 requires — the deferred seam scan is an *additional* detector, not the source of that label.

**Applicable lessons (episodic memory):**
- **iter-24 / iter-26 (anti-goal #8 — the recurring backend crash):** any change on the fetch/backfill/prices path must not exhaust memory. The drift check MUST be a bounded per-symbol overlap-window compare (last N dates) and MUST NOT add a whole-table ORM load; `compute_preflight` reads the drift artifact as a **tiny-file read** on the ~2 s health poll — never a DB scan (mirror the existing `_ledger_file_ok` integrity check).
- **iter-33 / iter-34 (required-still-passing replay is structurally unsatisfiable by a FULL iter):** `run-phase.sh` has no deterministic-replay lane. The executor MUST either run the closure one-liner replay inline (write `reports/phase-goal-mcp-loop-iter-35-regression-replay-results.md` over the golden scripts J-01/J-05/J-13/J-20, which all exist) OR the session must follow with a lean verify pass (iter-36). See NOTES + DoD.
- **iter-16 (assumption ledger, freshness anchor):** the drift artifact's reference/timestamp must be a **deterministic** fetch/seed as-of anchor, never `date.today()` (anti-goal #5), matching the J-20 freshness-anchor precedent.

## IN SCOPE

### Backend
- [ ] New PURE module `app.engine.drift`:
  - `build_drift_report(fetched_bars, seed_bars, *, overlap_days, reference) -> dict` — the SINGLE overlap comparator. For each fetched symbol, take the last `overlap_days` dates COMMON to both the fetch and the **committed seed** (`data/seed/prices/{symbol}.csv` — the validated history, NOT the DB, which is INSERT-new-only and would not reflect a re-adjusted overlap), byte / fixed-precision compare OHLCV **exactly as the seed CSV was written** (never a loose float compare — the B-304 trap), and record each mismatching `{symbol, mismatching_dates, classification: "adjustment_seam"}`. Returns `{status: "clean"|"drift", reference, overlap_days, affected:[…]}`. NEVER mutates, reconciles, or re-fetches the fetched data (B-304 "Do NOT touch the fetched data").
  - `resolve_drift_report_path()` — env `TRENDORA_DRIFT_REPORT_PATH` else `config.data_quality.drift.report_path` (REPO_ROOT-resolved), mirroring `app.engine.evidence.resolve_ledger_path()` exactly.
  - `write_drift_report(report)` (the SINGLE persist) + `read_drift_report()` (the SINGLE reader both readers below call — no second parse path). Missing artifact ⇒ honest inert (treated as clean/None); unparseable artifact ⇒ honest degraded reason (never a crash).
- [ ] Wire the comparator into the FETCH pipeline: invoke `build_drift_report` + `write_drift_report` ONCE as a post-fetch validation stage in `data_manager._run_job`, immediately after the real fetch completes (`prog.complete_stage("fetch")` at ~`:3094`, guarded so it does NOT run on a `resumable` pause or the skip-fetch/backfill-only path), comparing the fetch's returned bars vs the committed-seed CSVs over `config.data_quality.drift.overlap_days`. The session/pasted API key stays request-only — it MUST NOT be written into the artifact or any log (anti-goal #7; the existing `_make_scrubber` discipline).
- [ ] `app.engine.readiness.compute_preflight`: add a `_apply("drift", ok, detail)` component (after `integrity`) that reads the persisted artifact via `read_drift_report()` — a tiny-file read, NO DB query/scan (anti-goal #8): `ok` when the artifact is absent OR `status=="clean"`; breached when `status=="drift"`, with `detail` naming the affected symbols. Severity from `config.readiness.severity["drift"]`. Worst-severity composition and the existing servability/freshness/integrity components stay byte-identical.
- [ ] `app.config.ReadinessCfg._validate` (config.py ~:556-577): extend the required + allowed component set from `{servability, freshness, integrity}` to include `drift`, so boot-validation requires and accepts the new severity key.
- [ ] `GET /api/data` (`data_overview`, `app/api/data.py`): add an additive `drift` field = `read_drift_report()` (the SAME reader — no recompute, no new endpoint), mirroring how the J-15 `capacity` field was added.
- [ ] `config.yaml`: new `data_quality.drift` block (`enabled`, `overlap_days`, `report_path`) + add `drift: degraded` to `readiness.severity` (a failed overlap forces DEGRADED — B-304). No magic numbers in code — every bound/threshold/path comes from config.

### Frontend
- [ ] New **drift report** section/card on `/data` (`apps/frontend/app/data/page.tsx`) reading the additive `drift` field from the EXISTING `/api/data` client (no new fetch path): quiet/neutral when clean or absent (no fetch has run yet), LOUD when `status=="drift"` — listing each affected symbol, its mismatching dates, and the "adjustment seam" classification. Degrades gracefully (contained, honest) on a missing/absent field — never a blank application-error page (anti-goal #8). NO proven-language.

### New user-facing capability
After this iteration a user (or operator) who runs a Fetch job sees, on `/data`, whether the freshly-fetched bars silently diverge from the validated seed — and if a symbol's history was re-adjusted, the drift report names the symbol + the exact mismatching dates as an adjustment seam, and the site-wide preflight banner turns DEGRADED with that reason until the mismatch stands. A clean fetch reads green and the banner recovers.

### New information displayed
A `/data` drift report section (overall clean/drift status; on drift, the affected-symbol list with mismatching dates + "adjustment seam" label). The existing preflight banner (J-20) gains a fourth reason source (drift) with no shape change.

### New user actions
None (no new controls — the drift report is produced by the existing Fetch job and displayed read-only; the preflight banner already renders reasons).

### UI surface changes
`/data` gains one read-only drift report section. The cross-cutting preflight banner (already mounted in `app/layout.tsx`) shows a drift reason when the artifact reports one — no new page, no new nav.

### Product surface delta
The Data Manager becomes a data-integrity console: it now discloses whether the live feed agrees with the validated seed, and that agreement gates the whole board's trust verdict. Silent vendor re-adjustment (the "invisible poison" B-304 targets) becomes visible and blocks GO.

### Blueprint conformance
`/data` is J-13's already-registered Information-Architecture home (Data Manager, in the nav skeleton); the drift report is an additive section on it, and the readiness/preflight reader is the existing cross-cutting chrome — **no nav-skeleton change, no reapproval note filed**. A J-21 row is added to the IA homes table and an iter-35 clarification paragraph is appended (additive edits).

### Data-contract additions
ONE new displayed value — the **live-vs-seed drift report** — registered in `blueprint.md`:
- **Computing module (single):** `app.engine.drift:build_drift_report`, invoked ONCE in the FETCH pipeline (`data_manager._run_job` post-fetch stage) and persisted via `resolve_drift_report_path()`.
- **Serving / reader (single):** `app.engine.drift:read_drift_report()` — read verbatim by (a) `app.engine.readiness:compute_preflight` (the new `_apply("drift",…)` component) and (b) an additive `drift` field on the EXISTING `GET /api/data`. No recompute anywhere; both readers re-read the one persisted artifact (single source).
This value never duplicates an existing Data-Contract value: it is a new integrity report, not a second computation of any score/regime/evidence/preflight value.

## OUT OF SCOPE

- **B-304 distribution-envelope check (b)** — comparing today's score/indicator distributions vs historical percentile envelopes. Not required by J-21's acceptance; it is a second risky sub-system (envelope stats + short-history floors). Deferred to a follow-on.
- **B-304 junction seam scan (c) via B-113 detectors** — B-113 (sentinel anomaly detectors) is UNBUILT (no sentinel module exists in `app/engine/`); it is its own card/journey. The overlap byte-mismatch already produces the "adjustment seam" classification J-21 requires.
- **Any auto-repair / auto-reconcile / re-fetch of drifted data** — B-304 "Do NOT touch the fetched data" (reconciliation is an owner decision, possibly a basis change). The monitor reports + gates trust; it never fixes.
- **Any Evidence Claim / referee submission / ledger write** — J-21 is pure data-integrity/UX; both ledgers stay byte-identical, divisor stays 8.
- **Any nav-skeleton change, any new top-level endpoint, any wall-clock time** (determinism — anti-goal #5).
- **Changing servability / freshness / integrity behavior** — those three preflight components must stay byte-identical; drift is purely additive.

## DEFINITION OF DONE

- [ ] **J-21 passes via browser-qa:** (step 1) a controlled fetch with one symbol's overlap region re-adjusted produces a `/data` drift report naming that symbol, the exact mismatching dates, and the "adjustment seam" classification; (step 2) the preflight banner reads DEGRADED with that drift reason while the mismatch stands; (step 3) a clean fetch renders the report green and the banner recovers to GO.
- [ ] **Single source proven:** the drift artifact is written once by the FETCH pipeline; both `compute_preflight` and `GET /api/data` re-read it via the SAME `read_drift_report()` (verified: no second parse path, no recompute).
- [ ] **Correctness:** the reported mismatching dates byte-match the fixture's constructed re-adjustment (anti-goal #3).
- [ ] **Inert on the committed seed (J-20 non-regression):** with no fetch run (fresh seed, absent artifact), the drift component is `ok` and the preflight verdict is UNCHANGED — GO stays GO, and the servability/freshness/integrity components + `GET /api/health` output are byte-identical to iter-34.
- [ ] **Required-still-passing green:** J-20 (preflight banner — directly touched by the new component), J-13 (`/data` surface), J-01, J-05 re-verified via deterministic golden replay (all four have golden scripts) AND/OR the live browser-qa lane; J-16 (the FETCH job path — directly modified) re-verified via a live fetch-job run (no golden script). Because a FULL iter's `run-phase.sh` path lacks the replay lane, the executor MUST run the closure one-liner replay inline (write `reports/phase-goal-mcp-loop-iter-35-regression-replay-results.md`) OR the session follows with a lean verify pass (iter-36) — see NOTES.
- [ ] **Anti-goals:** no proven-language introduced (drift is descriptive integrity, never a "Proven"/"Not yet proven" signal); no auto-repair; determinism preserved (deterministic artifact reference, no wall-clock); no API key persisted into the artifact/logs; `compute_preflight` does no DB scan on the health poll; the `/data` section + banner degrade gracefully on a missing artifact (no blank crash).
- [ ] Unit/integration tests pass; the existing preflight tests (servability/freshness/integrity) stay green; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-mcp-loop-iter-35-dev.md`.

## TESTING REQUIREMENTS

- **Browser (browser-qa-agent):** J-21 (the `/data` drift section in BOTH the clean and the drift state; the preflight banner reflecting DEGRADED-on-drift then recovering to GO). Required-still-passing: J-20 (banner still composes GO/DEGRADED/NO-GO with the added component), J-13 (`/data` coverage/legend un-regressed), J-01 (leaderboard), J-05 (evidence ledger). Capture md5-distinct frames per the iter-14/25 lesson (a `-fail-`/error frame cited under a PASS invalidates the citation).
- **Unit/integration (code paths that must have tests):**
  - `app.engine.drift.build_drift_report` — the fixture matrix: (i) re-adjusted overlap → detected, correct symbol, exact mismatching dates, `adjustment_seam` classification; (ii) clean overlap → `status=="clean"`, empty `affected`; (iii) byte/fixed-precision compare catches a real seam a loose float compare would miss (the B-304 trap).
  - `resolve_drift_report_path` / `write_drift_report` / `read_drift_report` — env override + config default + REPO_ROOT resolution; missing file ⇒ inert; unparseable ⇒ honest degraded, never raises.
  - `compute_preflight` — drift `ok` when artifact absent/clean (GO unchanged); `drift` status ⇒ the configured severity forces DEGRADED with the affected symbols in `reasons`; worst-severity composition still correct across all four components.
  - `ReadinessCfg._validate` — boot accepts `readiness.severity` with `drift`; rejects a config missing the `drift` component (extend the existing required-component test).
  - `GET /api/data` — additive `drift` field present, equals `read_drift_report()`, honest empty/absent snapshot on a cold DB (200, never 500).
  - The `data_manager._run_job` post-fetch stage runs on a completed fetch and NOT on a `resumable` pause / backfill-only path.
- **Error cases that must be rejected/handled:** a loose float compare must NOT silently pass a real re-adjustment (assert byte/fixed-precision); a fetch must NEVER auto-reconcile the drifted data; the drift artifact must never embed a provider URL/query credential or the session API key (anti-goal #7); a missing/unparseable artifact must degrade honestly, not crash the `/data` page or the health poll.

## NOTES

- **Systemic replay-lane flag (carry from iter-33/34, framework-level):** a FULL iteration routes through `run-phase.sh`, which has ZERO deterministic-replay-lane machinery (that lane lives only in `goal-iter-lean.sh`), so the "required-still-passing deterministic replay" DoD line is not auto-satisfied by this iter. Mitigation for iter-35: the executor runs the closure one-liner replay inline over the golden scripts (J-01/J-05/J-13/J-20 all present in `runs/goal-session-mcp-loop/journey-scripts/`) and writes `reports/phase-goal-mcp-loop-iter-35-regression-replay-results.md`; failing that, iter-36 is a lean verify pass (the iter-34 pattern, confirmed working 17/17). The evaluator should score J-21 on its OWN canonical browser-qa evidence (iter-33 J-20 precedent) and record any replay gap on the required set, not on J-21.
- **J-20 non-regression is the load-bearing safety property:** the drift component must be strictly additive and INERT until a fetch actually writes a drift artifact — so on the committed seed the preflight verdict, banner, and `/api/health` payload stay byte-identical to iter-34. Verify this explicitly (absent artifact ⇒ drift `ok` ⇒ GO).
- **B-113/B-103 co-evolution:** the deferred distribution-envelope + B-113 seam-scan enrichments plug into the SAME drift artifact and the SAME `compute_preflight` drift component when they land (never a parallel report or a second preflight indicator — mirrors the iter-33 B-301 "add inputs to the same verdict" discipline).
- **Operational:** if `run-goal.sh` exports ledger paths (`LEDGER_PATH`/`STAGING_LEDGER_PATH`) for the harness, add a `TRENDORA_DRIFT_REPORT_PATH` export alongside them so the browser-qa/gate lanes resolve the same artifact the fetch pipeline wrote (non-blocking if the config default already resolves under `runs/goal-session-mcp-loop/state/`).
- Assumption logged: `runs/goal-session-mcp-loop/state/assumptions.md` (iter-35 — overlap-only scope of B-304).
