# Goal Iteration 21 — Clean canonical browser-QA re-verification of J-13 (Data Manager 548-pool + availability legend)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** mcp-loop
- **Iteration:** 21
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-13
- **Required-still-passing journeys:** J-01, J-03, J-05, J-10, J-12
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

Produce the clean canonical browser-QA evidence trail that flips **J-13** `partial → passing` — the already-committed iter-20 Data Manager work (548-pool Fetch scope, "Expand universe" removed, collision-free two-group availability legend) is verified live against running services, closure formally re-clears, and the three unreplayed regression journeys (J-05/J-10/J-12) are live-replayed. **No new feature code.**

## BACKGROUND

The iter-20 J-13 code landed **complete and independently verified correct** (review PASS, audit PASS_WITH_GAPS "deliverable correct; gaps are verification-chain only", coherence COHERENCE-PASS, scan CLEAN, and a live Chrome DOM/computed-style check by the ux-regression reviewer) and is now **committed at HEAD `aac9abc`**. The only reason J-13 sits at `partial` and not `passing` is a verification-chain failure, not a product defect: the canonical `browser-qa-agent` lane recorded a **blanket SKIP** (both services unreachable at precondition — `curl 000` on `:3255`/`:8255`), the evidence directory is **empty**, and **phase-closure returned CLOSURE-FAIL** on exactly that gap; the QA report meanwhile self-reported PASS by grading browser-typed cases from *code inspection* (iter-20 lesson). Per the priority rubric this is the top target: no journey is `regressed` (rule 1 n/a) and iter-20 coherence was COHERENCE-PASS (rule 2 — no consolidation owed), and completing J-13 is the unblocker (rule 3) that removes the last non-evidence `partial` and makes GOAL_ACHIEVED reachable, with the **smallest possible change set — zero code** (rule 4). The blocker is services-down + a stale-bundle harness trap = **operationally fixable, NOT human-owned** (no credentials/network/paid-service/sanction), so this is a CONTINUE, not STALLED. Depth is **full** because closure FAILED and must formally re-clear and the QA artifact contradiction needs a fresh QA/audit/ux-regression pass — the closure + audit + ux-regression gates run ONLY in the full pipeline (the lean cycle is developer → reviewer → browser-qa, with no closure/audit/ux-regression stage), so full is required to satisfy the DoD, not optional; the prior evaluator explicitly recommended full.

## IN SCOPE

This is a **verification-only** iteration — like a baseline pass, it carries **no source-code changes**; the developer stage is a no-op and the value comes from the browser-qa / QA / closure / audit / ux-regression stages executing against live services.

### Backend
- [ ] **No backend source changes.** The iter-20 J-13 backend change (the generic Fetch symbol-set repoint from `all_seed_symbols(cfg)` to `price_load_symbols(cfg, seed_dir)` in `app/engine/data_manager.py`) is committed at HEAD `aac9abc` and MUST be preserved, not re-implemented. `git diff HEAD -- apps/backend/app/engine/data_manager.py` must stay empty.

### Frontend
- [ ] **No frontend source changes.** The iter-20 J-13 frontend changes (Expand-universe removal + dead-code cleanup in `app/data/page.tsx`; two-group split legend, blue single-hue density ramp `#a6c8f2` top, violet `#a78bfa` snapshot ring, Fetch→fills/Backfill→scores caption+tooltip in `components/availability-heatmap.tsx`; color tokens in `app/globals.css` + `tailwind.config.ts`) are committed at HEAD `aac9abc` and MUST be preserved, not re-implemented. `git diff HEAD` on those paths must stay empty.

### Verification work (operational — no code)
- [ ] **Dodge the staleness trap first:** `rm -rf apps/frontend/.next` before starting the frontend (the `start-frontend.sh` `.qa-serve-base` stamp checks only the baked backend URL, not FE-source freshness — it silently served a stale pre-iter-20 bundle in iter-20; audit O1).
- [ ] **Bring up BOTH prod-mode services and confirm reachability BEFORE dispatching browser-qa:** `scripts/start-backend.sh` (`:8255`) then `scripts/start-frontend.sh` (`:3255`) — never `dev.sh`. Confirm `curl :8255/health` and `curl :3255` return 200 (not `000`) and keep both up for the whole run.
- [ ] **Re-run the canonical `browser-qa-agent` lane, executing (not code-inspecting)** the J-13 UI plan against the live stack: all 22 UT cases, at minimum the 14 P1 cases (UT-01,02,03,04,05,10,11,12,14,17,18,19,20,21 — same coverage as `reports/phase-goal-mcp-loop-iter-20-ui-test-plan.md`; the ui-test-designer regenerates the equivalent plan for iter-21), writing `reports/phase-goal-mcp-loop-iter-21-ui-test-results.md` with real md5-distinct, full-page/element-clip screenshots into the iteration evidence dir.
- [ ] **Live-replay the three iter-20 replay-gap journeys** — J-05 (UT-19 `/evidence`), J-10 (UT-20 `/stocks/{ticker}` deep-history chart), J-12 (UT-21 `/methodology`↔`/stocks` universe count) — plus the J-01 (UT-17 Sector-sort) + J-03 (UT-18 "Not yet proven") smoke.
- [ ] **Reconcile the QA report:** its Browser-Checks section must reflect the REAL browser run (no code-inspection PASS while services were down) and agree with `ui-test-results.md` on service reachability.
- [ ] **Re-run phase-closure → CLOSURE-PASS.**

### New user-facing capability
None new. This iteration produces the missing verification evidence for the capability J-13 already ships (the user can already distinguish, on `/data`, a fully-scored day from a fetched-but-unscored backfill-gap day, and the Fetch job covers the full ~548/588 pool).

### New information displayed
None. No new computed or displayed value. The availability figures still come from the single existing `compute_availability` → `GET /api/data/availability` source (byte-identical); no copy or encoding changes.

### New user actions
None. No controls added or removed this iteration (the Expand-option removal already shipped in iter-20).

### UI surface changes
None. `/data` and every other surface are byte-identical to HEAD `aac9abc`.

### Product surface delta
None functionally new — the product experience is exactly the committed iter-20 state; this iteration only proves it renders correctly against live services and formally clears the verification gates.

### Blueprint conformance
J-13's canonical home `/data` (Data Manager) is already registered in `blueprint.md`'s Information Architecture, and the iter-20 clarification already documents the presentation-only legend re-encode + internal Fetch-scope wiring reading the SAME `GET /api/data/availability` value. **No blueprint edit is required** — this iteration introduces no new displayed value, no new page, no nav-skeleton change, and no code diff, so there is nothing new to register (no reapproval requested).

### Data-contract additions
**None.** No `## Evidence Claim` (pure verification — no new "proven" status; the post-decompose gate passes automatically). Both ledgers stay untouched and all-FAIL. No new value, module, or endpoint.

## OUT OF SCOPE

- **Any source-code change** — this is verification-only. Do NOT reopen or "improve" the J-13 UI/UX/backend implementation (it is verified correct); do NOT refactor the availability heatmap, the Fetch-scope wiring, or the color tokens.
- **The `start-frontend.sh` freshness-stamp gap (audit O1).** File it as a non-blocking tooling follow-up; do NOT fix it inside this iteration (it is out of J-13's scope and would add code to a verification-only pass). The operational `rm -rf .next` workaround is sufficient here.
- **Re-certifying the sanctioned-partial evidence journeys J-02 / J-06 / J-07 / J-08 / J-09** on the 30-year basis — they remain goal.md-sanctioned `partial` (Data-basis-change provision); re-certifying is a separate, riskier, referee-gated new-basis staging-discovery + honest-promotion iteration (see NOTES). Not this iteration.
- **J-14** (deep index/macro context + vendor labels), **J-15 / J-16** (fast-platform perf budgets) — sequenced separately; unbuilt.
- **Any `## Evidence Claim`, referee submission, or ledger write.**

## DEFINITION OF DONE

- [ ] **Target journey J-13 passes via the canonical `browser-qa-agent` lane**, executed live (not code-inspection): (1) the job-kind picker has no "Expand universe" option and Fetch / Backfill / Fetch+backfill all start without error (UT-02/03/04/05); (2) the availability legend renders two labeled groups, the density top ("full") bucket is blue `rgb(166,200,242)` not amber `rgb(240,180,41)`, and the snapshot ring is violet `rgb(167,139,250)` not green `rgb(52,211,153)` — no encoding collision (UT-10/11/12); (3) hover distinguishes a bars-but-no-snapshot day from a snapshot day, each tooltip naming Fetch and Backfill (UT-14).
- [ ] `reports/phase-goal-mcp-loop-iter-21-ui-test-results.md` exists with an **overall PASS** and **all 14 P1 cases PASS**; `browser-qa-agent` has a telemetry record for this iteration (not a jumped/SKIPPED lane).
- [ ] The iteration evidence directory (`reports/qa/goal-mcp-loop-iter-21-evidence/`) is **non-empty** and its PNGs are **md5-distinct and correctly labeled** — a capture actually shows the two-group legend scrolled into frame, and distinct captures show the no-snapshot (backfill-gap) cell hover vs the snapshot cell hover (no reused frame relabeled across assertions; no ~5855-byte blank scrolled-viewport frames).
- [ ] **Required-still-passing journeys live-replay green:** J-01 (UT-17), J-03 (UT-18), J-05 (UT-19), J-10 (UT-20), J-12 (UT-21) — closing the iter-20 replay gap; no `passing → failing`.
- [ ] The QA report's Browser-Checks section is **reconciled** against the real browser run (no code-inspection PASS asserted while services were down); it does not contradict `ui-test-results.md` on reachability.
- [ ] **phase-closure returns CLOSURE-PASS**; the auditor incorporates the ux-regression verdict; ux-regression returns UX-REGRESSION-PASS.
- [ ] **`git diff HEAD` on the J-13 implementation files is empty** (`apps/backend/app/engine/data_manager.py`, `apps/frontend/app/data/page.tsx`, `apps/frontend/components/availability-heatmap.tsx`, `apps/frontend/app/globals.css`, `apps/frontend/tailwind.config.ts`) — proving this was verification-only.
- [ ] No anti-goal violation introduced (esp. #2 no return/price/buy-sell language in the rendered legend/caption/tooltip copy — re-confirmed live; #3 availability numbers byte-identical; #8 `/data` renders without crash and degrades gracefully if the API fails — UT-16).
- [ ] J-13-relevant backend unit tests pass (`apps/backend/tests/test_data_manager.py` incl. `test_compute_availability_byte_identical_after_fetch_scope_widening`); no regressions. (Do NOT run the full ~10 h 30-year suite — see NOTES.)
- [ ] Dev handoff written at `docs/handoffs/goal-mcp-loop-iter-21-dev.md` (a verification-only, no-code handoff is expected — it records the re-run outcome, not a code change).

## TESTING REQUIREMENTS

- **Operational preconditions (do these before dispatching browser-qa):**
  1. `rm -rf apps/frontend/.next` (staleness-stamp trap).
  2. Start `scripts/start-backend.sh` (`:8255`), then `scripts/start-frontend.sh` (`:3255`) in prod mode (never `dev.sh`). The item-A OOM fix (iter-19) means `/api/data` now survives its cold path under the 6144 MB cap, so both services stay up.
  3. Confirm reachability (`curl :8255/health` → 200, `curl :3255` → 200; NOT `000`) BEFORE any browser case runs.
- **Browser (canonical `browser-qa-agent` lane) — execute, do not code-inspect:**
  - **J-13** on `/data`: no "Expand universe" option + Fetch/Backfill/Both start (UT-02/03/04/05); two-group split legend with non-amber top bucket + non-green snapshot indicator (UT-10/11/12); hover distinguishes backfill-gap vs snapshotted day, naming Fetch→fills / Backfill→scores (UT-14); `/data` loads with required panels + no "Backend unavailable" card (UT-01); availability card degrades honestly on API failure (UT-16).
  - **Regression replay (live):** J-01 (UT-17 `/stocks` Sector-sort, the iter-18 crash driver — highest-value smoke), J-03 (UT-18 "Not yet proven" badges intact), J-05 (UT-19 `/evidence` renders), J-10 (UT-20 `/stocks/{ticker}` Full-history deep chart), J-12 (UT-21 universe count consistent across `/methodology` and `/stocks`).
- **Unit/integration:** re-run the J-13-relevant backend tests only — `apps/backend/tests/test_data_manager.py` (incl. the byte-identical availability test), and the fetch-scope tests (`test_data_manager_jobs_pipeline.py`) — to confirm no drift on the committed code. These are fast; do NOT invoke the whole suite.
- **Error cases:** `/data` must not crash and must contain any client error in the `error.tsx` boundary (never a blank application-error page); if `GET /api/data/availability` fails, the availability card shows the honest "could not load … No cells are shown rather than fabricated values." fallback while the rest of the page stays usable (UT-16, anti-goal #8).

## NOTES

- **Primary reference — the iter-20 lesson (directly applicable):** "Do NOT flip a target journey to `passing` on code-verification + a non-canonical live DOM check when the evidence dir is empty and closure FAILED — mark it `partial` and require a clean canonical browser-qa re-run. Always pre-empt with `rm -rf apps/frontend/.next` + confirm both prod services reachable BEFORE dispatching browser-qa; never accept a QA/status 'ready to ship' over an empty evidence dir or a CLOSURE-FAIL." This iteration exists to satisfy exactly that requirement — the evaluator will look for a NON-empty iter-21 evidence dir + CLOSURE-PASS, not a QA prose PASS.
- **Both lanes + port hygiene (iter-2 / iter-4 / iter-5 lessons):** confirm the frontend can actually reach the backend before re-running; free `:3255`/`:8255` of any stale `next-server`/backend before binding (`start-frontend.sh` does not `fuser -k`); check BOTH the canonical `reports/phase-goal-mcp-loop-iter-21-ui-test-results.md` AND the QA lane `reports/qa/goal-mcp-loop-iter-21-qa.md`, and reconcile any SKIP-vs-PASS split via the port — a QA-lane PASS never substitutes for the canonical lane on this near-terminal gate. If any verification artifact is missing, read `engine.log` to find WHERE the pipeline died (`Branch-UI ... aborting chain`, `invalid step`) rather than assuming.
- **Screenshot hygiene (iter-3 / iter-11 / iter-13 / iter-14 lessons — recurring):** the availability legend + heatmap sit below the fold on `/data`. Scroll the legend and the two hovered cells into frame BEFORE capture; prefer **full-page or element-clip** captures (a scrolled-viewport capture returns ~5855-byte blank dark frames); `md5sum` the evidence PNGs so one reused capture is not relabeled across the three J-13 assertions. A capture must actually show the two-group legend and the distinguished snapshot / no-snapshot cells in frame.
- **`browser_checks_run` is a dead flag (iter-6 lesson):** no harness path reliably sets it, so judge J-13 on the canonical `ui-test-results.md` P1 pass + md5-distinct pixels + a real `browser-qa-agent` telemetry record + CLOSURE-PASS — not on the flag. (Reconciling the QA Browser-Checks section per the eval is still required, but the pass verdict rests on the canonical lane, not the boolean.)
- **Test-suite cost + box safety (session memory):** the 30-year basis makes the FULL pytest suite ~10–11 h (test-only; the product itself boots fast) and its temp files exhaust `/tmp` every ~2–3 phases — run ONLY the J-13-relevant backend tests above, clear `/tmp/pytest-of-*` before a test run if needed, and never launch the full/concurrent suite (it fork-locks the host). The reviewer/QA verify the targeted tests; that is sufficient for a zero-code-diff iteration.
- **UI branch must run despite a zero code diff:** because iter-21 changes no source, the ui-impact-analyst may see "no UI changes." Treat the ALREADY-COMMITTED iter-20 J-13 surfaces (`/data` legend/heatmap/job form + the J-01/J-03/J-05/J-10/J-12 regression surfaces) as the surfaces-under-test and run the full J-13 + regression plan regardless — the purpose of this iteration IS the browser verification, so the UI branch must not be skipped.
- **Evidence journeys are future work, not this iteration.** J-02 / J-06 / J-07 / J-08 / J-09 stay sanctioned-partial (goal.md "Data-basis change" provision) until a genuine edge re-certifies on the 30-year basis — a separate riskier iteration (re-run the pre-registered staging exploration on the new data → promote ONLY a winner whose recorded block-bootstrap `p` clears the canonical Bonferroni bar, currently divisor 8, with margin, via an explicit `"ledger":"canonical"` `## Evidence Claim`; honor the honest-stop guard). Do NOT casually append a canonical claim (each permanently tightens the bar — iter-8 ma_stack / iter-10 footgun).
- **On a clean run J-13 flips `partial → passing`.** No Must-have journey then remains `failing`, and GOAL_ACHIEVED becomes reachable for the next evaluation (with J-02/J-06/J-07/J-08/J-09 sanctioned-partial and J-14/J-15/J-16 unknown, the evaluator decides whether the extended goal is met or the loop continues to those).
- **References:** iter-20 eval `runs/goal-session-mcp-loop/iter-20/eval.md` (§Next-Step Recommendation — the six-step re-run recipe this spec operationalizes); iter-20 closure `reports/phase-goal-mcp-loop-iter-20-closure-verdict.md`; the committed J-13 code at HEAD `aac9abc`; the canonical J-13 plan `reports/phase-goal-mcp-loop-iter-20-ui-test-plan.md` (22 UT / 14 P1).
