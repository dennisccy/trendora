# Goal Iteration 17 — 30-year basis, Part A2: deep index & macro context staged into the 30y seed (vendor-disclosed, no runtime change)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** mcp-loop
- **Iteration:** 17
- **Mode:** next
- **Depth:** full
- **Frontend Present:** no
- **Target journeys:** J-14
- **Required-still-passing journeys:** J-01, J-02, J-03, J-05, J-09
- **Anti-goal reminders:**
  - A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked values MUST render a "not yet proven" state. *(critical)*
  - **Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha claims; never place or simulate orders. *(critical)*
  - A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation for the same as-of date — not merely that the page renders. *(critical)*
  - **No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of; never introduce lookahead anywhere. *(critical)*
  - No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the post-decompose gate. *(critical)*
  - No hard-coded credentials, API keys, or tokens in source files. *(critical)*
  - From goal.md §H, verbatim: "no fabricated bars; the vendor mix is disclosed per series and a proxy is never presented as a market index; determinism + no-lookahead preserved." And: `^TNX`/`^DXY`/`^VXN` "are NOT external tickers — do NOT re-fetch them from Yahoo."

## GOAL

Complete the staged 30-year seed (`apps/backend/data/seed-stooq-30y/`) with its deep, honestly-sourced, per-series-vendor-disclosed index & macro context — `_SPX`/`_NDX`/`_DJI` deep from Stooq's local world bundle, `_VIX` deep from Yahoo, `_TNX`/`_DXY`/`_VXN` preserved as the app's FRED-macro proxies — so the staged asset is **swap-complete** and iter-18 can perform the atomic basis swap + sanctioned ledger reset once, over one complete seed, with ZERO runtime change this iteration.

## BACKGROUND

The iter-16 STALLED halt is resolved: the human operator unblocked the Stooq per-IP ACL by staging the 548-name equities span from the **local bulk archive** (commit `8be979d`, via the `--provider stooq-local` path reading `data/d_us_txt/`), then amended `docs/goal.md` (commit `9277dfc`) with §H ("Index & macro context for the deep basis") and the new Must-have **J-14**. §H gives an explicit sequencing instruction this spec obeys: *"Complete the seed's index/macro context BEFORE the swap so the swap happens once over one complete seed."* So iter-17 = §H (context completion, staging-side only); iter-18 = the atomic swap + sanctioned ledger reset (the iter-16 evaluator's roadmap, deferred one slot by the human's re-sequencing).

**RE-DISPATCH CONTEXT (read this first):** this is the second dispatch of iteration 17. The first execution ran plan → test-plan → dev, and dev substantially COMPLETED the scope below, but the run was interrupted BEFORE the `dev_complete` checkpoint landed — `runs/goal-mcp-loop-iter-17/status.json` sits at `current_step: test_plan_generated`, so the pipeline resumes at the dev step. The deliverables are ALREADY in the working tree. This decomposer re-verified the material facts against disk (not the handoff):

- `apps/backend/data/seed-stooq-30y/prices/` holds **590** CSVs (583 iter-16 equities + all 7 context series).
- `_SPX`/`_NDX`/`_DJI`: 1996-01-02 → 2026-07-01 (7,674 bars each; schema `date,open,high,low,close,volume`; vendor `stooq` in the manifest) — the 1789-era world-archive rows did not leak.
- `_VIX`: **the deep Yahoo branch already SUCCEEDED** — 1996-01-02 → 2026-07-01, 7,675 bars, vendor `yahoo`. The sanctioned fallback exists in code but was not needed.
- `_TNX`/`_DXY`/`_VXN`: byte-identical to the live seed (`cmp` verified), vendor `fred-macro-proxy`, honestly short (2021-01-04 → 2026-05-28).
- Staged `meta.json`: planned/ok/failed = **591/590/1** (SATS the only honest absence); exactly 7 vendor-tagged context records; window pins unchanged (`1996-01-01 → 2026-07-01`).
- Staged set ⊇ live caret set (`_DXY/_TNX/_VIX/_VXN` all covered) → the swap-completeness gate is materially satisfied; the committed test must prove it.
- Protected paths CLEAN: zero diff on `apps/backend/app/**`, `apps/frontend/**`, `config.yaml`, `data/seed/**`, and both evidence ledgers (7+7 rows byte-identical).
- Working-tree diff = exactly this iteration's scope: `scripts/ingest_seed.py` (+340), `tests/test_ingest_seed.py` (+472), `tests/test_seed_staged_30y.py` (+170), staged `meta.json` + 7 new CSVs, plus session bookkeeping.
- `docs/handoffs/goal-mcp-loop-iter-17-dev.md`, `reports/phase-goal-mcp-loop-iter-17-seed-coverage.md`, `-implementation-summary.md`, and the QA test plan all exist. **One known unfinished item:** the dev handoff's full-suite line still reads `FULL_SUITE_RESULT_PLACEHOLDER` — the interruption appears to have hit during/around that final full-suite verification.

**Directive to the resumed developer: VERIFY AND COMPLETE — do not rebuild.** Treat the working tree as the delivery. Re-run the targeted suites (`test_ingest_seed.py` offline set, `test_seed_staged_30y.py` over the real staged tree), re-verify protected-path byte-identity, fix only what re-verification finds, and replace the handoff placeholder with a REAL result. Run the backend suite in bounded, sequential invocations (per-suite targets; no massively concurrent single run) — the previous attempt likely died on a monolithic full-suite run. Re-invocations of `--stage-context` are idempotent by design (pinned window reused; note addendum appended exactly once); do not re-pull `_VIX` if the staged deep series validates.

Depth **full**: prior verdict STALLED with next-depth full recommended; this is data-integrity-critical staging feeding the session's highest-stakes write (the iter-18 swap), with tests well beyond browser smoke; the sibling iter-16 ran full and its AUDITOR caught B1 (env-key persistence) in exactly the script this iteration touches again; and the in-flight full-pipeline checkpoint (`test_plan_generated`) resumes cleanly only under full. Lessons applied: iter-9 (zero-frontend non-regression = byte-identity + unedited green suites, not a browser pass), iter-16 (redact env-sourced credentials at persistence choke points; test the FAILURE path), iter-16 audit B2 (cap `_solve_stooq_pow` iterations — this iteration touches the script, so it lands now), iter-12 (preconditions verified against disk/code — done above).

## IN SCOPE

Each item below is a required deliverable of iteration 17. Items marked *(delivered — verify)* are already in the working tree from the interrupted first execution; the resumed developer re-verifies them (targeted tests + spot checks) instead of rebuilding.

### Backend (tooling + committed staged data only — ZERO `apps/backend/app/**` runtime change)

- [ ] *(delivered — verify)* **World-bundle support in `apps/backend/scripts/ingest_seed.py`'s `stooq-local` path**: index plain `^xxx.txt` world-bundle files (e.g. `data/daily/world/indices/^spx.txt`) alongside `*.us.txt` in one index, mapping caret symbol → staged filename via the app's existing convention (`'^SPX' → '_SPX.csv'`); US-archive behavior byte-identical; REFUSED guards kept (missing dir; no recognized files; world-less archive refused for context staging). Implementation lives in the SCRIPT (`_LocalStooqBundleProvider`) — `app/**` untouched.
- [ ] *(delivered — verify)* **`_SPX.csv`, `_NDX.csv`, `_DJI.csv` staged** into `apps/backend/data/seed-stooq-30y/prices/` over the manifest's pinned window (`1996-01-01 → 2026-07-01`; not widened, not re-pinned). Pre-window archive rows CLIPPED (the world ^SPX file reaches 1789 with flat/monthly early rows — none may appear in the staged CSV). Index rows may carry volume 0 — non-negative, not positive, is the volume rule.
- [ ] *(delivered — verify)* **Deep `_VIX` from Yahoo** via the `--stage-context` context-merge mode (`run_context_merge`) — NEVER through `run_yahoo_ingest`'s manifest writer (which would clobber the staged stooq `meta.json`): ONE deep single pull, client-side clipped to the pinned end, MERGED into the existing manifest (583 equity records + window pins untouched). **Outcome already on disk: the deep branch succeeded** (7,675 bars, 1996-01-02 → 2026-07-01, byte-value-identical to the live series on all 1,357 overlap dates). The sanctioned fallback (live `_VIX.csv` copied VERBATIM, shortfall recorded) stays implemented + tested but unused. NEVER merge/splice two pulls into one series; never fabricate a bar.
- [ ] *(delivered — verify)* **The three FRED-macro proxies preserved:** `_TNX.csv`, `_DXY.csv`, `_VXN.csv` copied BYTE-IDENTICAL from `data/seed/prices/`. NOT re-fetched from Yahoo (§H: a Yahoo re-fetch would desync them from the FRED macro the app displays — ICE DXY ≈89 vs the app's ≈105). Deepening them via the FRED macro subsystem stays DEFERRED.
- [ ] *(delivered — verify)* **Per-series vendor disclosure in the staged `meta.json`** (§H): `vendor` recorded for every context series (`stooq` × 3, `yahoo` × 1, `fred-macro-proxy` × 3) alongside the per-symbol `{symbol, bars, first, last}` coverage records; the four prior caret failure entries resolved into coverage records with their real spans; accounting consistent (591/590/1); `note` EXTENDED with the mixed-vendor description incl. "a proxy is never presented as a market index"; copied/proxy series honestly record their real last bar (2026-05-28), never a pretended pinned-end coverage.
- [ ] *(delivered — verify)* **Extended staged validation suite** (`tests/test_seed_staged_30y.py`, +5 tests): context indexes deep/window-clipped/pinned-end/no-flat-OHLC-runs; proxies byte-identical to live; `_VIX` deep-XOR-verbatim-fallback (never a hybrid/splice); **swap-completeness: staged price-file set ⊇ live seed's (the load-bearing iter-18 gate)**; manifest vendor/window-pin/accounting agreement.
- [ ] *(delivered — verify)* **Audit B2 carry-forward:** `_solve_stooq_pow` bounded (`_POW_MAX_ITERATIONS`) with an honest, resumable failure at the cap + regression test.
- [ ] *(delivered — verify)* **B1 redaction discipline retained:** every NEW persistence path (context failure details, per-series notes, `_VIX` shortfall) routes through the `redact_stooq_key` choke point; the FAILURE path is exercised by a test (plants a key-bearing error, asserts nothing env-sourced reaches the committed manifest).
- [ ] *(delivered — verify)* **Coverage manifest** at `reports/phase-goal-mcp-loop-iter-17-seed-coverage.md`: final staged inventory (583 + 7 = 590), per-series vendor table, `_VIX` outcome, honest absences (SATS), and an explicit "Swap-complete: YES/NO" line with the staged⊇live check result.
- [ ] **REMAINING — complete the verification and the handoff:** re-run the targeted suites green (`test_ingest_seed.py` offline; `test_seed_staged_30y.py` over the real staged tree; the unedited DoD suites individually), run the backend suite in bounded sequential invocations, and REPLACE the `FULL_SUITE_RESULT_PLACEHOLDER` in `docs/handoffs/goal-mcp-loop-iter-17-dev.md` with the real command + counts. No placeholder may survive in any committed artifact.
- [ ] **Commit the staged additions** (7 context CSVs + merged `meta.json` + script/test changes) — the staged tree remains read by NOTHING at runtime (`config.provider: seed` untouched; `SeedProvider` still reads `data/seed/`).

### Frontend

None. (`Frontend Present: no` — zero UI change; stages 5/6/8 write N/A stubs per workflow.)

### New user-facing capability

None this iteration (enablement). After iter-17 the staged 30-year seed is COMPLETE — deep equities + deep vendor-disclosed index/macro context — so the iter-18 swap can light J-10..J-14's user-visible outcomes from one atomic flip.

### New information displayed

None. Every displayed number on every page stays byte-identical (zero `apps/**`/`config.yaml`/ledger diff).

### New user actions

None.

### UI surface changes

None.

### Product surface delta

None visible this iteration. Structurally: J-14 step 1 ("the seed carries deep index context across the 30-year window") is delivered into the STAGED basis; J-14 steps 2–3 (deep overlays rendering + vendor labels where surfaced) remain post-swap surfacing work.

### Blueprint conformance

No new surfaces. The J-14 homes row (canonical homes `/` Dashboard + `/data` Data Manager — both EXISTING nav sections) and the iter-17 clarification paragraph are ALREADY in `blueprint.md` (added at the first decompose pass, additive only; re-verified present at lines 82 and 211). No nav-skeleton change, no reapproval needed, no further blueprint edit this pass.

### Data-contract additions

None. The staged asset stays internal-only (read by nothing at runtime); no new displayed value, no new computing module, no new endpoint. The per-series `vendor` recorded in the staged `meta.json` is the future single source for the J-14 vendor label — it gets REGISTERED in the Data Contract only at the post-swap iteration that first displays it (documented in the blueprint's iter-17 clarification).

## Evidence Claim

None — this iteration ships no new "proven" claim (zero referee submissions; both ledgers stay byte-identical at 7+7 rows; any pre-swap claim would be measured on the retiring basis). The post-decompose gate passes through automatically.

## OUT OF SCOPE

- **The atomic swap + sanctioned ledger reset (iter-18):** seed-dir flip, pool-broadened `load_prices`, `resolve_candidate` recency/staleness gate, DB rebuild, bounded snapshot backfill, regeneration of BOTH ledgers, frozen-golden/seed-pin test refresh (`test_evidence.py`, `test_staging_ledger_routing.py`, `test_seed_integrity.py`, `test_bar_cache.py` comment), survivorship-label span update.
- Any change under `apps/backend/app/**`, `apps/frontend/**`, or `config.yaml` (incl. adding `_SPX/_NDX/_DJI` to `etfs.index`/`index_chart` — a swap/surfacing-time decision).
- Deepening the FRED macro series / regenerating the `_TNX/_DXY/_VXN` proxies (deferred macro-subsystem task; §H sanctions "preserve").
- Yahoo gap-fill for ANY equity (e.g. SATS): the equity basis is single-vendor Stooq (§A); names Stooq lacks stay honestly absent.
- Re-pulling `_VIX` or re-staging any context series that already validates on disk (idempotent verify-only resume).
- J-14 steps 2–3 (deep benchmark/vol overlays rendering, vendor labels in the UI) and its `[NEW]` demo walkthrough — post-swap surfacing.
- J-10 chart windowing/downsampling, J-12 membership hardening, J-13 Data Manager changes — all sequenced at/after the swap per goal.md.
- Re-probing Stooq's network endpoints (standing per-IP ACL — documented twice; the local bulk archives are the sanctioned access path).

## DEFINITION OF DONE

- [ ] `apps/backend/data/seed-stooq-30y/prices/` contains `_SPX.csv`, `_NDX.csv`, `_DJI.csv` (deep, window-clipped 1996-01-01 → 2026-07-01), `_VIX.csv` (deep Yahoo single-pull — already on disk; the sanctioned byte-identical fallback only if re-verification invalidates it), and `_TNX.csv`/`_DXY.csv`/`_VXN.csv` (byte-identical FRED-macro-proxy copies) — no fabricated, padded, or vendor-spliced bar anywhere.
- [ ] **Swap-complete:** the staged price-file set ⊇ the live seed's price-file set, proven by a committed passing test (the iter-18 gate).
- [ ] Staged `meta.json` records a `vendor` (stooq / yahoo / fred-macro-proxy) for every context series, per-symbol coverage matching disk, unchanged window pins, and honest failure/absence accounting (591/590/1, SATS only).
- [ ] Extended staged validation suite green over the real staged tree (prior checks + the new context checks); `_solve_stooq_pow` cap + regression test landed; redaction failure-path coverage intact.
- [ ] ZERO diff on `apps/backend/app/**`, `apps/frontend/**`, `config.yaml`, `data/seed/**`, `certified-claims.jsonl`, `staging-ledger.jsonl`; the unedited DoD suites (`test_referee.py`, `test_forward_walk.py`, `test_evidence.py`, `test_staging_ledger_routing.py`, `test_seed_integrity.py`, `test_seed_provider.py`) pass green unmodified — the byte-identity non-regression channel for J-01..J-09.
- [ ] Required-still-passing journeys J-01, J-02, J-03, J-05, J-09 remain green via that byte-identity channel; no anti-goal violation introduced.
- [ ] `reports/phase-goal-mcp-loop-iter-17-seed-coverage.md` present with the final inventory + vendor table + explicit swap-complete verdict.
- [ ] Dev handoff at `docs/handoffs/goal-mcp-loop-iter-17-dev.md` is COMPLETE — the `FULL_SUITE_RESULT_PLACEHOLDER` replaced with the real full-suite command + counts; honest External-Integration section for the Yahoo pull retained; NO placeholder text anywhere.

## TESTING REQUIREMENTS

- **Browser:** none — `Frontend Present: no`; stages 5/6/8 produce the sanctioned N/A stubs. Non-regression of J-01..J-09 rests on the byte-identity channel (zero-diff on protected paths + both ledgers) + unedited DoD suites green — per the iter-9/iter-16 precedent the evaluator has twice endorsed.
- **Unit/integration:**
  - world-archive indexer: offline unit tests on a synthetic `d_world_txt`-layout tree (plain `^xxx.txt` discovery, caret→`_XXX.csv` mapping, coexistence with `*.us.txt` indexing);
  - window clipping: pre-1996 archive rows (incl. flat/monthly 18xx-era rows) never reach a staged CSV;
  - manifest merge: context records merge without disturbing the 583 equity records, the pinned window, or provider identity; vendor field required for every context series; idempotent re-runs (note addendum exactly once, accounting stable);
  - proxy copies byte-identical; `_VIX` deep-XOR-fallback assertion; swap-completeness (staged ⊇ live);
  - `_solve_stooq_pow` iteration cap; redaction on the failure path (per iter-16: exercise FAILURE, not just construction);
  - the live Yahoo `_VIX` integration test (`@pytest.mark.integration` convention) — already passed live on the first execution; on resume it may pass again or skip-with-reason if Yahoo is unreachable, WITHOUT invalidating the already-staged deep series (the staged-tree validation is the gate on the committed data).
  - **Execution discipline:** run suites as bounded sequential targets (per-file), not one monolithic concurrent run; record real counts in the handoff.
- **Error cases:** missing/wrong `--archive-dir` → REFUSED (conflict exit); a window conflicting with the manifest's pinned end → `EXIT_CONFLICT`; a context series absent from its source → recorded honestly in the manifest, never fabricated; Yahoo unreachable → the sanctioned fallback branch (verbatim live copy), never a partial/spliced series; staging into a foreign-manifest dir REFUSED.

## NOTES

**For the evaluator (pre-registered, but judge on the evidence):** this is an enablement iteration in the iter-9/10/12/16 lineage — NO journey flips. J-14 becomes newly tracked (`unknown`; its step 1 data basis is delivered into the staged asset, steps 2–3 are post-swap). J-10..J-13 stay `unknown`, sequenced behind iter-18. This iteration was dispatched twice (first run aborted mid-dev-verification, before the `dev_complete` checkpoint); the second dispatch verifies + completes the same scope — score the DELIVERY, not the interruption. On success, CONTINUE is the mechanically correct verdict: the staged seed is swap-complete, so iter-18 (the atomic swap + sanctioned ledger reset, depth FULL, per the iter-16 eval's roadmap) is dispatchable unattended — the iter-16 STALLED rationale (human-only unblock) no longer holds. If re-verification finds the staged data invalid, that is an ordinary iteration failure — score it on its evidence.

**For iter-18 (forward pointer, not this scope):** the swap iteration MUST verify the swap-completeness test is green at its start, carry the sanctioned ledger reset atomically with the basis flip (goal.md "Data-basis change"), and expect the +21.34% J-09 yellow-flag edge to face honest re-certification on the new basis (a retired-window artifact will simply fail to re-certify — that is the system working).

**Assumptions recorded:** (1) `data/d_world_txt/` and `data/d_us_txt/` remain on the operator's disk (gitignored; needed only to re-run the world leg — the committed staged OUTPUT is self-sufficient for iter-18). (2) The manifest's pinned end stays 2026-07-01. (3) `data/seed/` (the live basis and the proxy/fallback copy source) is untouched this iteration. (4) The staged `_VIX` carries 7,675 bars vs the Stooq indexes' 7,674 — an inherited vendor quirk (Yahoo serves a 2026-05-25 Memorial-Day bar, consistent with the live seed's caret series), documented, not a defect.

**Lessons surfaced for the developer/reviewer:** iter-16 B1 (redact at persistence choke points; test the failure path), iter-16 B2 (cap `_solve_stooq_pow` — this iteration touches the script), iter-9 (an unedited passing default-path suite is the strongest "defaults reproduce today" proof — do not edit the DoD suites), iter-12 (verify preconditions against disk/code — re-done at this re-dispatch, results in BACKGROUND), goal.md §H verbatim (never re-fetch the FRED-macro proxies from Yahoo; a proxy is never presented as a market index).
