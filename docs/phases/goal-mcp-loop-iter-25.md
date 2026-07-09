# Goal Iteration 25 — Verify the `/data` cold-load OOM fix; recover J-13, close J-15

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** mcp-loop
- **Iteration:** 25
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-13, J-15
- **Required-still-passing journeys:** J-01, J-03, J-04, J-05, J-10, J-11, J-12, J-14
- **Evidence Claim:** none (no new "proven" signal is surfaced; both ledgers stay byte-identical all-FAIL, canonical Bonferroni divisor stays 8 — the post-decompose gate passes automatically per the blueprint LOOP RULE)
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked values MUST render a "not yet proven" state. *(critical)*
  - **Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha claims; never place or simulate orders. *(critical)*
  - A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation for the same as-of date — not merely that the page renders. *(critical)*
  - **No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of; never introduce lookahead anywhere. *(critical)*
  - No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the post-decompose gate. *(critical)*
  - No hard-coded credentials, API keys, or tokens in source files. *(critical)*
  - **Resilience to data-shape and data-scale change:** widening the data basis (new nulls, broader pools, deeper history) must never crash an existing page or exhaust a service's memory — every existing consumer of a widened field is re-validated, the UI degrades gracefully (contained error boundary, honest "—"/NA placeholder, never a blank application-error page), and unbounded whole-table ORM loads are forbidden on the deep basis. *(critical)* — **THIS is the anti-goal iter-24 violated; this iteration exists to prove it is now upheld (`resolved=true`).**

## GOAL

Prove — via the canonical `browser-qa-agent` on a live, cold-started prod-mode backend — that the already-applied `mmap_size_bytes: 0` fix eliminates the iter-24 cold `GET /api/data` OOM crash, so **J-13 returns to passing** and target **J-15 flips partial→passing**, with anti-goal #8 confirmed upheld and CLOSURE re-cleared.

## BACKGROUND

iter-24 was scored **REGRESSION**: its fast-platform item-B SQLite tuning set `mmap_size_bytes=1 GB` per pooled connection, and at `pool_size=10 + max_overflow=20` just ~6 live connections exhausted the `server.memory_cap_mb=6144` `ulimit -v` (virtual-address-space) cap — OOM-crashing the backend (MemoryError → PyO3 panic killing uvicorn) on the very first cold `GET /api/data` load after any restart, reproduced 2/2 by the canonical browser-qa lane. That broke prior-passing **J-13** (its `/data` surface crashes cold) and failed target **J-15**'s own "cold `/api/data` completes ≤60 s without OOM under the 6144 MB cap" criterion — a **critical anti-goal #8** violation. Both independent gates fired (UX-REGRESSION-FAIL, CLOSURE-FAIL) while the QA report fail-opened to PASS (the iter-18/iter-24 pattern).

The auditor already applied the fix in-tree and it is committed at HEAD: I verified `config.yaml:108` reads `mmap_size_bytes: 0` (mmap disabled), clean vs HEAD, with `pool_size`/`max_overflow`/`memory_cap_mb` unchanged — and the auditor's engine-level ablation measured a 471 MB peak. **But an engine/code-level fix is NOT journey evidence until the DoD-named canonical lane re-runs** (session lesson iter-13/20/22/24). So this iteration ships **no new feature code**; it is a fix-VERIFICATION + artifact-reconciliation pass only.

**Why full, not lean (rubric depth trigger):** the gates that CAUGHT this regression and must formally re-clear it — `ux-regression-reviewer`, `auditor`, and `phase-closure-auditor` — run ONLY in the full 11-step pipeline; a lean cycle (developer→reviewer→browser-qa) cannot re-clear a CLOSURE-FAIL or flip a critical anti-goal to `resolved=true`. Prior verdict was REGRESSION (not ESCALATE), but recovering a critical-anti-goal regression is exactly the "hardening pass" full-depth trigger.

**Lessons carried in (episodic memory — Applies-to matches this plan):**
- *iter-24:* any change to SQLite `mmap_size`/pool sizing must satisfy `mmap_size_bytes × (pool_size + max_overflow) < ulimit -v`; a **browser-qa cold-path repro (stop backend → load `/data` as the FIRST request, twice) is the only reliable catch** — an `/api/health` boot is a DIFFERENT code path and gives a false "cold path OK." An audit-applied fix for a CRITICAL anti-goal that landed after the browser-qa lane already ran MUST be re-verified by a fresh browser-qa run, never accepted on engine-level proof.
- *iter-20:* pre-empt with `rm -rf apps/frontend/.next` and confirm BOTH prod services reachable (HTTP-200) BEFORE dispatching browser-qa; never accept a QA/`status.json` "ready to ship" over an empty evidence dir or a CLOSURE-FAIL.
- *iter-22:* an audit-fix pass that changes a rendered surface must regenerate `ui-test-results.md` AND `ux-regression.md` against the fixed build — a `qa.md` TC-* retest does NOT satisfy the "pass via browser-qa-agent" DoD.
- *iter-11/13/14/15:* `md5`-distinct, full-page or element-clip screenshots only; open the actual asserted frame; never trust a PASS label or a DOM-text line alone. A `-fail-`-named frame in the evidence dir invalidates any "zero blockers" prose.
- *iter-23:* do NOT pin the slow 30-year pytest fixture (~10-11 h, fork-locks the box) as a hard DoD gate.

## IN SCOPE

### Backend
- [ ] **No backend source change.** The `mmap_size_bytes: 0` fix (`config.yaml:108`) is ALREADY applied and committed at HEAD — do NOT re-implement, re-tune, or resize `pool_size`/`max_overflow`/`cache_size`/`memory_cap_mb`. Confirm it is still present at run start; if (and only if) it is somehow absent, restore exactly `mmap_size_bytes: 0` and nothing else.

### Frontend (if applicable)
- [ ] **No frontend source change.** The `/data` storage card, availability legend, and every other surface are unchanged from iter-24. Operational only: `rm -rf apps/frontend/.next` before the browser-qa lane to dodge the `start-frontend.sh` staleness-stamp trap (iter-20), then serve a fresh prod build.

### Verification & artifact reconciliation (the actual work — non-code)
- [ ] Bring up BOTH prod-mode services (`scripts/start-backend.sh` / `scripts/start-frontend.sh`, never `dev.sh`) and confirm HTTP-200 on `:8255` / `:3255` BEFORE dispatching the browser-qa lane.
- [ ] Drive the **cold-path** sequence live: stop the backend → cold-start → load `/data` as the FIRST request, at least twice → confirm NO OOM/crash (backend stays up; `/data` renders).
- [ ] Correct `reports/perf-budgets.md`'s cold-path claim with a REAL fresh-restart `/api/data` measurement (audit B2): the cold path completes ≤ 60 s without OOM under the 6144 MB cap.
- [ ] Add the crash → fix → re-verify note to `reports/phase-goal-mcp-loop-iter-25-implementation-summary.md` and `reports/phase-goal-mcp-loop-iter-25-user-visible-changes.md`.
- [ ] Regenerate `runs/goal-mcp-loop-iter-25/status.json` so it does not carry a stale `qa_verdict=PASS` / `blockers=[]` while closure is unresolved (the iter-24 contradiction).

### New user-facing capability
None. This is a recovery/verification pass — the user-visible outcome is that `/data` no longer crashes the backend on a cold load (J-13 restored) and the platform's measured budgets hold cold as well as warm (J-15).

### New information displayed
None. No new value, panel, or field.

### New user actions
None.

### UI surface changes
None. `/data` and all core pages are byte-identical to iter-24; the only behavioral change is the absence of the cold-load crash.

### Product surface delta
`/data` is reliable on a cold backend again — the leaderboard/data pages no longer risk a whole-backend outage via the `/api/data` cold path. No visible content changes.

### Blueprint conformance
No new surfaces. J-13's canonical home is `/data`; J-15 is cross-cutting latency + the `/data` DB-capacity storage card + `reports/perf-budgets.md` — both already registered under the Data Manager section of the Information Architecture. `blueprint.md` gains only an additive iter-25 running-log clarification (verification-only; no contract change, no nav change).

### Data-contract additions
None. The `mmap_size_bytes: 0` change is an internal SQLite-engine config beneath the existing registered values; it introduces no displayed value and no endpoint. Both evidence ledgers stay byte-identical all-FAIL (no `## Evidence Claim`).

## OUT OF SCOPE

- **Any new feature code / any re-implementation of the mmap fix.** It is applied and committed; touching it re-opens the regression.
- **Any pool/pragma/cap resizing** beyond the applied `mmap_size_bytes: 0` (no `pool_size`, `max_overflow`, `cache_size`, `memory_cap_mb` changes).
- **Evidence / ledger work.** J-02, J-06, J-07, J-08, J-09 stay sanctioned-partial (no new-basis staging winner clears Bonferroni divisor-8 today); this iteration does ZERO evidence work.
- **J-16** (data-jobs ≥30% perf, goal.md item F) — needs the risky byte-identity-gated scoring-window change; NEVER bundled with a regression-recovery pass (rubric rule 5).
- **Non-blocking follow-ups (do NOT bundle, per iter-24 eval):** F1 (`/data` no-retry desync — add an auto-retry so a transient failure doesn't strand the page beside a green readiness badge, P3); T1 (cadence-aware backfill range in `scripts/measure-perf.sh`).
- **Deleting the dead-duplicate `index-regime-chart.tsx` / `major-indexes-card.tsx`** (coherence-WARN carry-forward) — defer to a dedicated tidy iteration.
- **The full ~10-11 h 30-year pytest fixture** as a blocking gate (iter-23 lesson).

## DEFINITION OF DONE

- [ ] **J-13 passes via `browser-qa-agent`:** the cold-path sequence (stop → cold-start → `/data` as the FIRST request, ≥2×) completes with NO OOM/crash — the backend stays up and `/data` renders — verified LIVE by the canonical lane (the iter-24 cold-path cases, incl. UT-16 → UT-06 → UT-05, flip FAIL→PASS) with a non-empty, `md5`-distinct evidence dir.
- [ ] **J-15 passes via `browser-qa-agent`:** its "cold `/api/data` completes ≤ 60 s without OOM under the 6144 MB cap" acceptance criterion is browser-verified green, and the warm budgets recorded in `reports/perf-budgets.md` still hold (pages ≤ 3 s warm; `/api/stocks` ≤ 1.5 s; `/api/stocks/{ticker}` ≤ 0.3 s; `/api/data` ≤ 1.5 s warm; `/api/health` ≤ 0.1 s).
- [ ] Required-still-passing **J-03, J-04, J-05, J-11, J-14** are freshly LIVE-replayed green (not byte-identity carry — the iter-24 crash aborted their replay); smoke **J-01, J-10, J-12** re-confirmed on the surviving backend.
- [ ] **Anti-goal #8 confirmed UPHELD (`resolved=true`):** no blank application-error page and no memory exhaustion on the cold `/data` path; no other anti-goal violated.
- [ ] `reports/perf-budgets.md` cold-path claim corrected with a REAL fresh-restart `/api/data` measurement; `implementation-summary.md` + `user-visible-changes.md` carry the crash/fix/re-verify note; `status.json` regenerated with no PASS/`blockers=[]`-while-closure-unresolved contradiction.
- [ ] Existing byte-identity / API unit tests remain green **unedited** (they are the regression proof for the untouched values); no new tests are required (zero source change); the full 30-year fixture is NOT a blocking gate.
- [ ] `ux-regression-reviewer` → UX-REGRESSION-PASS and `phase-closure-auditor` → CLOSURE-PASS on the FIXED build.
- [ ] Dev handoff written at `docs/handoffs/goal-mcp-loop-iter-25-dev.md`.

## TESTING REQUIREMENTS

- **Browser (canonical `browser-qa-agent`, LIVE, prod mode, both services HTTP-200 first; `rm -rf apps/frontend/.next` first):**
  - **Cold-path (P1, the crux):** stop backend → cold-start → `GET /data` as the FIRST request, at least twice → assert the backend does NOT OOM/crash and `/data` renders (re-drive the iter-24 UT-16 → UT-06 → UT-05 sequence to FAIL→PASS; UT-06 = missing-data diagnostic renders; UT-05 = a single contained error card when the backend is genuinely unreachable, never a blank app-error page).
  - **Storage card (P1):** UT-01/UT-02 — the `/data` storage-footprint card renders and its values match the `GET /api/data` `capacity` payload.
  - **Required-still-passing live replay:** J-03 (`/stocks` + `/evidence` "Not yet proven"), J-04 (Dashboard Regime + evidence link), J-05 (`/evidence` all-FAIL ledger rows), J-11 (both ledgers all-FAIL, no stale edge), J-14 (deep vendor-labeled index/macro context) — each freshly captured, not carried.
  - **Smoke:** J-01 (`/stocks` leaderboard, Sector-sort no crash, `541/541`), J-10 (Full/Recent deep-history toggle), J-12 (`/data` `541` == `/stocks` `541/541`).
  - All P1 cases must EXECUTE (not be code-inspected); every referenced screenshot must be `md5`-distinct and full-page or element-clip (open the actual asserted frame — no reused/blank frames).
- **Unit/integration:** the existing byte-identity suites remain green UNEDITED — `test_bar_cache.py` (prefill byte-identity), `test_api_engine.py::test_filtered_stock_rows_byte_identical_to_full_scan_row`, `test_health.py` readiness-equivalence, `test_data_manager.py` diagnostic query-count independence. An EDIT to any of these expectation tests is itself a regression signal (iter-9 economy). No new tests (zero source change).
- **Error cases:** cold or unreachable backend → exactly one contained error card on `/data` (never a blank application-error page — anti-goal #8); with `mmap_size_bytes: 0`, virtual-memory exhaustion under the 6144 MB cap must be impossible on the cold `/api/data` prefill.

## NOTES

- **The fix is already in the tree — verify, do not re-do.** `config.yaml:108 = mmap_size_bytes: 0` at HEAD (`665565a`). The developer's job this iteration is the non-code reconciliation above + the handoff; inventing a code change violates surgical-changes discipline and re-opens the regression.
- **Two-lane discipline (iter-4/5):** check both the canonical `reports/phase-goal-mcp-loop-iter-25-ui-test-results.md` AND `reports/qa/goal-mcp-loop-iter-25-qa.md`; the canonical lane is the terminal gate. A QA-lane PASS does not substitute for it.
- **Ops (from session memory):** the 30-year pytest fixture exhausts `/tmp` every few phases — clear `/tmp/pytest-of-*` before any backend test run; free `:3255`/`:8255` before binding.
- **On a clean run:** J-13 returns to passing and J-15 flips partial→passing. GOAL_ACHIEVED is still NOT reachable this iteration — J-02/J-06/J-07/J-08/J-09 remain sanctioned-partial (no staging winner clears divisor-8 today) and J-16 is deliberately unbuilt — so the evaluator should expect CONTINUE on success, not GOAL_ACHIEVED.
- **Process flag for the evaluator (carry-forward from iter-24):** the QA agent graded the cold-path DoD line PASS from the dev handoff's later-invalidated claim while its own browser-qa lane read FAIL — trust the browser-qa CONTENT + ux-regression + closure over `status.json`/QA prose.
