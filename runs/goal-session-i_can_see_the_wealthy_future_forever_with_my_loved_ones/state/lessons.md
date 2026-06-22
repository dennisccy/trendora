# Goal Session i_can_see_the_wealthy_future_forever_with_my_loved_ones — Lessons Learned

Append-only ledger of takeaways from prior iterations. The goal-evaluator
appends one entry per iteration; the goal-decomposer reads this file before
planning each iteration to avoid repeating known pitfalls.

Each entry should be 1-3 sentences capturing a non-obvious lesson — surprising
failures, regression triggers, or decisions that worked well. Avoid
restating the verdict (the evaluator-log.md already does that).

## iter-0 — 2026-06-11T08:41:43+01:00

**Verdict:** CONTINUE
**Lesson:** The browser-qa agent invented its own journey list instead of reading docs/goal.md — ~20 IDs got fabricated descriptions (J-22/23/24 graded as "broker/orders/portfolio", J-14 as "Research page") and some evidence was recycled byte-identical or misfiled (UT-J-17-data-manager.png is actually the Research Factor Lab; the real Data Manager/VCP captures landed in stray reports/qa/goal-iter-0-evidence/). The raw screenshots were mostly genuine and sufficient, but every verdict had to be re-derived from them + the dev source-scan; J-42's PASS was an overclaim (only the displayed-dates leg was checked — /data still has native type="date" inputs).
**Applies to:** every future browser-qa dispatch (pass the goal.md journey text verbatim into the QA prompt; evaluator must md5-spot-check evidence and grade against goal.md acceptance, never the QA table) and any iter touching J-42 (acceptance includes validated ISO text inputs + one shared formatter, not just ISO-looking output). Also: the full pytest suite (~14 min) was skipped at baseline (collect-only) — iter-1's gate must run it once.

## iter-1 — 2026-06-11T10:55:47+01:00

**Verdict:** CONTINUE
**Lesson:** A Next.js App Router URL↔state sync needs `searchParams` in the serialize effect's dependency array: in `asof-provider.tsx` the deep-link restore (`setAsOf(D)`) raced the serializer, which first stripped `?asof` (state still null), then re-ran against a stale `searchParams` closure showing the old param, saw current===next, and early-returned — leaving deep links permanently stripped even though the state restored correctly. HTTP-200 smoke tests of `?asof` URLs cannot catch this; only a post-hydration `window.location.href` assertion did. Separately: ESLint is genuinely not installed in `apps/frontend` — `npm run lint` DoD lines are unfulfillable; use `tsc --noEmit` as the frontend gate.
**Applies to:** any iter touching `components/asof-provider.tsx` or adding URL-serialized client state; any iter spec writing a frontend lint DoD; browser-QA of deep-link behavior (assert post-hydration URL, not navigation-time URL).

## iter-2 — 2026-06-11T13:35:00+01:00

**Verdict:** CONTINUE
**Lesson:** A dev-turn background full-pytest run does NOT survive the turn ending — iter-2's suite run was torn down mid-flight and the pump had to re-run the identical command to get real numbers (639/4/0 in 2044s). Also note the full suite now takes ~34 min, not the ~14 min in older project memory (test_api_indexes alone needs 229s of warm-seed boot).
**Applies to:** any iter that gates handoff on the full backend suite (i.e., all of them) — either run pytest to completion in the foreground within the dev turn, or explicitly hand the run to the pump; budget ~35 min and never run two invocations concurrently. Especially relevant to the upcoming J-46 performance iteration, whose benchmark baseline should use these real timings.

## iter-3 — 2026-06-11T18:40:00+01:00

**Verdict:** CONTINUE
**Lesson:** Browser-QA evidence can silently degrade to byte-identical BLANK captures (8 iter-3 PNGs shared md5 23fe5583…, a 7278-byte dark rectangle) while the written claims are still correct — the iter-3 resumable/Resume/backfill claims were all verifiable against persistent backend state instead (`data_provider_runs` row id 30 and `import_checkpoints` id 22 in apps/backend/data/trendora.db, read-only). Also: IPv6 SYN-SENT timeouts to alphavantage.co stretch the alpha_vantage+demo rate-limit technique from ~3 min to ~16 min per chunk attempt (5×15s timeout per symbol), and the engine's audit/ux-regression/closure steps never ran (non-fatal `invalid step 'post_dev_parallel_complete'` after the parallel fanout — no audit handoff exists for any iteration of this session).
**Applies to:** any iter relying on /data job-card screenshots (md5-check captures; corroborate via the run log + import_checkpoints); any browser-QA budgeting the alpha_vantage demo-key throttle; framework owner re the skipped audit/closure steps in goal-mode full depth.

## iter-4 — 2026-06-11T21:15:12+01:00

**Verdict:** GOAL_ACHIEVED
**Lesson:** A served-payload claim can be corroborated with NO running backend:
`apps/backend/.venv/bin/python -c "from app.config import load_config; from app.engine.methodology
import build_catalog; ..."` rebuilds the exact `GET /api/methodology` glossary from the committed
`config.yaml` in seconds (118 terms, per-category counts byte-matching QA's live capture). Also: QA
captured /methodology only at top scroll, so the below-the-fold Glossary section never appears in
any screenshot — when a target section renders below the fold, require a scrolled-to capture or
treat the DOM-extraction + offline-rebuild pair as the primary record. Finally, dev-handoff counts
drift (handoff said 111 authored/120 served; committed reality 109/118) — always recount from the
committed artifact, never from the handoff.
**Applies to:** any future evaluation of catalog/config-served content (methodology, glossary,
provider catalog); any browser-QA plan whose acceptance target sits below the first viewport.

## iter-5 — 2026-06-12T10:27:25+01:00

**Verdict:** CONTINUE
**Lesson:** Wrapping an existing labelled header in a clickable affordance can nest interactive
elements: `SortHeader`'s `<button>` in `apps/frontend/app/stocks/page.tsx` wraps `TermInfo`, whose
`InfoTooltip` trigger is itself a `<button>` (components/ui/info-tooltip.tsx:62) — invalid DOM that
surfaced as a NEW red "1 error" Next dev-overlay badge visible in every iter-5 /stocks capture
(absent in iter-2 captures), and the inner info-click bubbles into a sort. QA passed all journeys
without reporting the badge.
**Applies to:** any iter making header labels / badges / table cells clickable around `TermInfo`/
`InfoTooltip` (J-51 samples table headers are next); evaluators + browser-qa should treat a
dev-overlay error badge appearing in a capture (vs prior iterations' captures of the same page) as a
must-explain regression signal even when every journey leg passes.

## iter-6 — 2026-06-12T12:49:57+01:00

**Verdict:** CONTINUE
**Lesson:** An evidence filename can show something entirely different from its name: `UT-J-44-toggle-off.png` actually captures the honest "Backend unavailable" dashboard from a mid-session backend death, not a toggle state — and the Chrome MCP session then got cross-contaminated with another project's app (Tapeology, port 3650). QA disclosed it honestly, but the toggle-persistence leg was silently left unverified behind a plausibly-named file. Capture fragile multi-step legs (toggle->reload cycles) EARLY in a browser session, and evaluators must view pixels per capture, never trust filenames.
**Applies to:** any iter whose QA session restarts the backend on :8835 or runs long (>30 min) browser sessions on this multi-project machine; the J-44 toggle off->reload->still-off cycle specifically still needs an opportunistic re-verification.

## iter-7 — 2026-06-12T17:05:00+01:00

**Verdict:** CONTINUE
**Lesson:** Published research Ns DRIFT between backend boots: the background warm-up matures additional forward returns, so QA captured n_total=20832/D1=2083 while the evaluator's fresh boot read 20954/2095 (+122 = one snapshot's universe). Count-coherence (samples total == aggregate n) must therefore be asserted same-instant against the live aggregate, never against a hardcoded N from an earlier capture or report. Separately, the md5 duplicate-evidence failure recurred a third time (UT-J-26-combination-lab.png + UT-J-51-initial.png are byte-copies of UT-J-25-factor-lab.png) — QA reused one /research capture under three evidence names.
**Applies to:** any iter asserting an exact N/count across page reloads or backend restarts (J-53's job-progress counts especially); every evaluator/QA pass — md5sum the evidence dir FIRST and require one capture per claimed surface.

## iter-8 — 2026-06-12T21:41:07+01:00

**Verdict:** GOAL_ACHIEVED
**Lesson:** Performance-ratio claims must be re-derived from the raw stored fields, never trusted from a report: QA's TC-02 "4.5x speedup" was the INVERSE of the truth (data_provider_runs id 32: elapsed 10.27s vs per_date_seconds_sum 2.28s = 0.22x), and tiny 3-5-date backfills over early-2021 dates are write-dominated (trivial per-date compute, ~8-9s serialized forward-return inserts) so the job-card ratio honestly reads <1 even though the parallel win is real (independently re-benchmarked at 4.09x on compute-dominated dates). Judge an advisory ">=2x" on the workload the optimization targets and corroborate via the benchmark + DB, not a micro-job's display line.
**Applies to:** any agent evaluating speedup/perf acceptance from job timings or QA tables — recompute every ratio from the persisted payload fields (per_date_seconds_sum / elapsed_seconds), and pick benchmark date ranges with enough bar history that compute, not DB writes, dominates.

## iter-9 — 2026-06-13T02:33:06+01:00

**Verdict:** CONTINUE
**Lesson:** An overflow/truncation affordance can be DORMANT against the live data even though the code is correct: the J-56 '+n' theme-chip overflow can never render because config max theme membership (3, verified by counting config.yaml theme members per ticker) exactly equals THEME_PREVIEW_LIMIT — yet browser-QA's table claimed the leg was observed. Before accepting (or demanding live proof of) a "+n / show more" leg, compute the data ceiling from config/API first; if the ceiling ≤ preview limit, grade the leg on code review + the substantive "full membership readable in place" outcome, and never fabricate data to force it. Contrast J-57, whose +21 overflow WAS live-exercisable (27 members > 6 preview).
**Applies to:** any iter adding preview-limit/overflow UI (J-58 sector member lists reuse the J-57 mechanics; J-64 samples table) and any QA/evaluator pass grading a "+n" or truncation leg — check max cardinality in the served data before trusting an "observed" claim.

## iter-10 — 2026-06-13T03:33:21+01:00

**Verdict:** CONTINUE
**Lesson:** The evidence-byte-duplication that goal.md/the spec explicitly warned against recurred AGAIN despite the warning: the QA agent reused the one `/research` Factor Lab capture (md5 4cf9a48c) under THREE filenames — `UT-J-25-J-26-J-29-research.png`, `UT-J-51-J-52-samples-with-ticker-links.png`, AND `UT-J-65-research-initial.png` — so the J-51/J-52 "samples-with-ticker-links" filename actually shows the Factor Lab page, not a samples table; the genuine J-52 ticker-link evidence had to be recovered from `UT-J-64-ticker-filter-aapl.png` (which really does show the 28 AAPL rows). The substance was fully verifiable from the distinct J-64 captures + source (page.tsx:568-585 `target=_blank`, sample-link.tsx:49-50), so the verdict stood — but the J-51/J-52 evidence pointer in this session's QA is mislabeled and an evaluator who trusted filenames would have been misled.
**Applies to:** every browser-qa dispatch on this session (md5sum the evidence dir FIRST, and validate filename-vs-content for any capture whose bytes are shared — never accept a regression-journey PASS on a recycled/mislabeled image; recover the real evidence from a sibling capture or from source). Especially relevant when a regression journey's "own" capture shares bytes with an unrelated surface.

## iter-11 — 2026-06-13T05:40:00+01:00

**Verdict:** CONTINUE
**Lesson:** Two lessons from the J-58 re-run. (1) A NEW validated config section (here `stock_industries`, whose `_stock_industries_valid` validator requires every key to be in `universe.symbols`) must be pruned at EVERY config-narrowing site, not just the inline test dicts — the prior run's lone full-suite failure was `apps/backend/scripts/build_qa_fixture_db.py::build_fixture()` narrowing `universe.symbols` to 4 members and pruning `themes` but not `stock_industries`, so ~89 orphaned keys made the fixture config invalid. When adding a validated config section, grep for both inline configs (`tests/`) AND every script that narrows/screens the committed config (`apps/backend/scripts/build_qa_fixture_db.py`, `apply_universe_to_config.py`). (2) Operational: the goal-evaluator dispatch must NEVER block on the in-flight full pytest suite — iter-11's first run aborted here when the pump blocked ~6h waiting on the ~46-min suite plus a follow-up. Hand the suite to the pump as a background run and gate the evaluator on the flushed terminal summary line, not the live stream.
**Applies to:** any iter adding a new validated `config.yaml` section or a new required column (grep every config-narrowing site, not a fixed list); and any FULL-depth iter whose dev hands a long pytest suite to the pump (background it; never block the evaluator on it).

## iter-12 — 2026-06-13T15:14:18Z

**Verdict:** CONTINUE
**Lesson:** A new column on an EXISTING SQLModel table (here data_provider_runs.job_id and import_checkpoints.completed_stages_json) MUST be registered in apps/backend/app/db.py `_ADDITIVE_COLUMNS` — `SQLModel.metadata.create_all` only creates MISSING TABLES, never ALTERs an existing one, so the persistent live DB (apps/backend/data/trendora.db) silently lacks the column and every read touching that table 500s, while fresh-DB unit tests stay green and hide it. The QA pipeline caught it only because it hit the live DB; the offline suite did not. The fix added a guard test (test_every_model_column_on_existing_table_is_covered_by_additive_registry) that fails CI on any future unregistered column — verify it tracks NEW_COLUMNS_THIS_SESSION going forward.
**Applies to:** any iter adding a column/field to an existing table in apps/backend/app/models.py — grep `_ADDITIVE_COLUMNS` in db.py for the new column name before declaring done, and exercise a real (non-fresh) DB read of the affected endpoint, not just the unit suite.

## iter-14 — 2026-06-13T19:33:01Z

**Verdict:** GOAL_ACHIEVED
**Lesson:** A GOAL_ACHIEVED candidate can be confirmed soundly even when the engine skips the audit/ux-regression/closure steps (the known `post_dev_parallel_complete` quirk leaves those handoffs absent) AND the QA report carries a shared-bytes evidence smell (iter-14: TC-02/TC-09/TC-13 all md5 fd4070b1, 3 identical captures) — because the goal-evaluator can re-derive the binding J-63 acceptance directly against the live backend: default view=episodes, episodes_n<pooled_n for a persisting subject, count-coherence SAME-INSTANT in BOTH modes (event-study n == samples total), 422 on invalid view, and config-served glossary terms. The browser-QA UT evidence (distinct, 16 tests) plus that live re-derivation outweigh the QA narrative tables; never halt or downgrade GOAL_ACHIEVED solely on absent closure handoffs or duplicate QA screenshots when the live API and the green full suite (787/4/0 incl. the pooled byte-identity + both-modes count-coherence tests) corroborate.
**Applies to:** any final-iteration GOAL_ACHIEVED candidate, especially fresh full-depth iters whose audit/closure handoffs are absent, or any iter whose QA evidence dir shows shared-md5 captures — re-derive the load-bearing acceptance against the running backend rather than trusting the QA table.

## iter-15 — 2026-06-14T13:30:00Z

**Verdict:** CONTINUE
**Lesson:** A journey marked "passing" on offline equality/failure-isolation tests (J-67, iter-12) can still be broken in the LIVE orchestration: the iter-12 tests failed the per-date COMPUTE, but the real `_do_backfill` crash needed a per-date PERSIST failure AFTER an earlier date had already committed on the SHARED session (`scanner.persist_run_payload` commits at scanner.py:205, `forward_testing.backfill_run_forward_returns` at forward_testing.py:289; a later `session.rollback()` then hit the invalid 'committed' state). J-68 fixed it with a fresh per-date `Session(eng)` the orchestrator owns. When a regression test "passes" but the field bug persists, suspect the test stubs a different failure point than production hits.
**Applies to:** any iter touching `apps/backend/app/engine/data_manager.py` `_do_backfill` / session-transaction boundaries, or any "we already tested this" reliability journey — make the regression test drive the REAL orchestration entry point, not a hand-rolled stand-in.

## iter-15 — 2026-06-14T13:30:01Z

**Verdict:** CONTINUE
**Lesson:** Recurring (iters 3/7/10/13/15): zoomed/cropped browser-QA close-ups degraded to blank byte-identical captures (iter-15: a whole cluster of 6830-byte modal + button-state PNGs shared one md5; UT-09-modal.png was solid dark). The full-VIEWPORT captures (UT-01-result.png, UT-13-run-history.png) were genuine. When close-ups are blank, do NOT take the journey on faith OR fail it — corroborate via the live backend (curl the endpoint) + re-running the targeted tests + the DOM-text the QA report extracts; the substance held here (J-69 live: single-ended -> 400, range-only -> 200 seed-protected).
**Applies to:** any goal-mode evaluation gating a UI journey on Chrome-MCP evidence; always md5sum the evidence dir first and prefer live-backend + test corroboration over a single screenshot.

## iter-16 — 2026-06-14T15:30:00Z

**Verdict:** GOAL_ACHIEVED
**Lesson:** A "two isolated frontend files" lean iteration can still carry a critical anti-goal at its center — J-71 added keyboard as-of stepping, the exact surface the J-18 single-global-as-of invariant guards. The cheap, decisive check was static, not visual: `grep` the diff for `window/document.addEventListener` keydown (must be none) and confirm `asof-calendar.tsx` keeps exactly ONE `useState` (the `view` month cursor, not an as-of value) with `asof-provider.tsx`/`asof-switcher.tsx` byte-untouched. Also: when the committed seed only exercises a subset of a styling map's branches (here density buckets 4-5; buckets 0-3 never appear because every day has full coverage), verify the unexercised branches at source level (the `BUCKET_TEXT_CLASS` map) rather than recording the journey partial — a static className map's correctness is provable without a live render of every branch.
**Applies to:** any future iter touching the as-of control (`asof-calendar.tsx` / `asof-switcher.tsx` / `asof-provider.tsx`) or adding keyboard/interaction handlers near the global date state; and any UI-styling iter whose density/bucket branches aren't all reachable from the committed seed.

## iter-17 — 2026-06-15T01:10:00Z

**Verdict:** CONTINUE
**Lesson:** Browser-QA can hard-SKIP (0/9, empty evidence dir) when Chrome DevTools :9222 is unreachable
(ECONNREFUSED) — the pipeline then stops at `dev_complete` with `browser_checks_run:false` and the
evaluator gets NO live screenshots. Even a perfectly source-verified, COHERENCE-PASS, review-PASS,
tsc-clean frontend iteration CANNOT be GOAL_ACHIEVED in that state: the strict rule forbids marking a
Must-have passing without positive live evidence, so target journeys stay `unknown` and the correct call
is CONTINUE (env failure, not code failure) — verify the env is actually down before concluding, then
recommend a cheap lean re-QA pass with no code rework rather than re-running dev.
**Applies to:** any iteration where `reports/phase-<iter>-ui-test-results.md` reads "SKIPPED / Chrome MCP
unavailable" and the evidence dir is empty — especially lean frontend-only iters whose only gate is the
browser smoke; confirm :3835/:8835/:9222 reachability before scoring, and never upgrade `unknown` target
journeys to `passing` on source review alone.

## iter-18 — 2026-06-15T11:00:00Z

**Verdict:** CONTINUE
**Lesson:** The availability-heatmap blank/wrong-frame capture trap recurred a 7th time (iters 3/5/7/9/13/15/17 -> 18): on /data the colored multi-hue grid sits BELOW the fold, so default and naive-scroll screenshots land on either a blank dark frame (the 5742-byte signature) or the per-symbol COVERAGE TABLE (`J-74-fullvp-heatmap-with-legend.png` showed ADI/AMAT/AMD rows, not cells). The J-74 multi-hue PASS was salvageable only because the live DOM computed-CSS rgb values matched the committed `globals.css --heat-0..5` hex to the digit (rgb extraction can't be faked from source alone) — but the spec's screenshot DoD was not met. Future heatmap QA must scroll the colored grid explicitly into the viewport and capture full-viewport, then VIEW the pixels; a coverage-table or blank frame is a rejected capture, not evidence.
**Applies to:** any iter capturing the `/data` per-date availability heatmap (J-61/J-70/J-74) or any below-the-fold surface — and the general rule that DOM/computed-CSS extraction can substitute for a degraded screenshot ONLY when it carries render-only signal (live rgb/aria values), never on source review alone.

## iter-20 — 2026-06-15T15:30:00Z

**Verdict:** CONTINUE
**Lesson:** The full-suite gate has TWO guard tests that fire on additive backend changes the targeted-module dev runs miss: (1) `test_db.py::test_create_all_produces_expected_tables` asserts `set(SQLModel.metadata.tables.keys())` equals an exact expected-tables set — so ANY new `table=True` model (here the standalone `event_study_cache` J-72 cache table) must be added to the expected set even though a standalone table correctly avoids the `_ADDITIVE_COLUMNS` trap; and (2) `test_no_magic_numbers.py::test_engine_calc_code_has_no_magic_numbers` blanket-forbids EVERY float/complex literal in `CALC_FILES` — even a semantically-harmless `0.0` sort-tie SENTINEL (here `research.py:1435-1436` in `_rsp_rank_key`) is rejected; sentinels in calc files must be a named/sourced module constant, not an inline `0.0`. Both passed every targeted module run and only the full suite caught them.
**Applies to:** any iter adding a new `table=True` SQLModel (add it to `test_db.py`'s expected-tables set) OR any iter writing a float/int literal into an `apps/backend/app/engine/` CALC_FILE — including throwaway sentinels/defaults in sort keys or `... if x is not None else 0.0` fallbacks (source them from config or a named constant). Run the FULL suite, not just targeted modules, before claiming a GOAL_ACHIEVED candidate.

## iter-21 — 2026-06-15T21:05:00Z

**Verdict:** GOAL_ACHIEVED
**Lesson:** The cleanest no-magic-numbers fix for a `(is_not_none, value)` sort-tuple under `reverse=True` is to make the `None` fallback the `is_not_none` boolean ITSELF (`value if present else present`), not a sourced numeric constant — the boolean is structural to the sort (a differing first tuple element short-circuits before the fallback is ever cross-compared with a float), so it carries no literal AND is provably byte-identical to the old `0.0` sentinel (the sentinel was only ever consulted between two both-None rows, which compare equal either way). Verify such a refactor by re-deriving the ordering over randomized inputs, not just by trusting the suite.
**Applies to:** any future iter that trips `test_no_magic_numbers.py` on a sort-key/None-handling float sentinel in the engine CALC_FILES (research.py / scoring), or that adds a standalone create_all table — remember the new table must ALSO be added to `test_db.py`'s expected-tables set (`RESEARCH_CACHE_TABLES`-style group), the new-table analog of the `_ADDITIVE_COLUMNS` pattern; both of these guard tests surface ONLY in the full suite, never in a targeted module run.

## iter-22 — 2026-06-16T00:18:22Z

**Verdict:** CONTINUE
**Lesson:** On an in-place resume after a prior GOAL_ACHIEVED, "every journey in journey-history.json is green" is NOT sufficient for GOAL_ACHIEVED when goal.md has queued *new buildable* Must-haves (here J-81/J-82) that have no journey-history entry yet — they count as `unknown` Must-haves with no positive evidence and must drive CONTINUE. Check goal.md's full Must-have list (esp. the "J-79…J-82 are NOT data-dependent" block at goal.md:2146-2152) against journey-history keys, not just the entries that exist. Genuinely data-walled journeys (J-22/J-23/J-24, goal.md:2172) stay non-vetoing `unknown`; newly-queued buildable ones do not.
**Applies to:** any in-place resume / any iteration where docs/goal.md was extended with new Must-haves (commit that touches goal.md before the iter) — diff the goal's Must-have IDs against journey-history before considering GOAL_ACHIEVED.

## iter-23 — 2026-06-16T02:28:09Z

**Verdict:** CONTINUE
**Lesson:** Any iter that ADDITIVELY attaches a field to a served payload that has a `served == engine_output` byte-equality guard (here `apps/backend/tests/test_api_engine.py::test_api_{themes,sectors}_equals_engine_output` comparing `/api/themes` & `/api/sectors` to `score_themes`/`score_sectors`) WILL turn the full suite red — J-81's `forward_returns` key (read verbatim from the separate `forward_returns` table, NOT computed by the score engine) tripped exactly these two guards even though it is byte-identical to Backtest and COHERENCE-PASS. The dev updated the J-82c contract test but missed the J-81 byte-equality guards. Before declaring a backend-touching iter done, grep the changed endpoint name (`/api/themes`, `/api/sectors`, etc.) across `apps/backend/tests` for `== expected` / `equals_engine_output` byte-equality asserts and update them in the SAME iter (compare modulo the additive key). This is the 2nd consecutive "correct additive feature trips a pre-existing blanket guard" full-suite-red (iter-20 J-77 magic-numbers was the 1st) — both cost a one-test consolidation iter.
**Applies to:** any iter that adds a field to `/api/themes`, `/api/sectors`, `/api/stocks`, `/api/dashboard`, or any endpoint covered by a `served == score_*(...)` byte-equality test in `apps/backend/tests/test_api_engine.py`; any backend-touching iter gated on a GREEN full suite for GOAL_ACHIEVED.

## iter-24 — 2026-06-16T04:00:55Z

**Verdict:** GOAL_ACHIEVED
**Lesson:** A correct *additive* snapshot-served field (read verbatim from a separate append-only table — here `forward_returns` from `_leadership_returns`) repeatedly trips blanket `served == engine_output` byte-equality guards that compare the served payload to the live score function (which never computes that field). This recurred at exactly the same shape three times: J-75 on /api/stocks (iter-20→21), then J-81 on /api/themes + /api/sectors (iter-23→24). The blessed, single-source-preserving fix is to strip ONLY the additive key, keep the canonical byte-equality, then separately assert the additive field's config-driven shape — never loosen the equality. Whenever a future iter attaches a new additive field to a scored endpoint payload, update its `test_api_*_equals_engine_output` guard IN THE SAME ITER so the full-suite gate never goes red afterward.
**Applies to:** any iter that additively attaches a non-canonical served field (forward_returns, future enrichments) to a scored endpoint payload (/api/stocks, /api/themes, /api/sectors) — pair it with the matching test_api_engine.py byte-equality guard update in the same iteration.

## iter-25 — 2026-06-16T23:46:13Z

**Verdict:** CONTINUE
**Lesson:** A React hydration mismatch is ONLY observable at runtime in a live browser console — neither source review nor SSR-boundary HTML inspection (server HTML carrying the right chrome/hrefs) can PROVE its absence, only its plausibility. J-83's load-bearing positive evidence was the browser-qa-agent's live console capture (nextjs-portal shadow root has no error dialog; "Hydration failed"/"server rendered HTML"/"did not match" absent) on direct-open + reload + new-tab; the dev's own SSR HTML evidence was necessary-but-not-sufficient. Pair this with the iter-17/18 failure mode (Chrome :9222 down -> hard-SKIP -> journey stuck `unknown`): a hydration/SSR journey CANNOT be upgraded to passing without a live console capture, so confirm :3835/:8835/:9222 reachability before scoring such an iteration.
**Applies to:** any iter touching SSR/URL hydration, `app/layout.tsx`, `middleware.ts`, or the `asof-provider` lazy initializer — and any future journey whose acceptance is "no console error" (runtime-only evidence required; never accept source review alone).

## iter-26 — 2026-06-17T02:12:24Z

**Verdict:** CONTINUE
**Lesson:** The QA report DEFERRED all browser tests for J-84 as "verification-only / backend not running", but the separate browser-qa-agent report showed it had itself started a backend via `scripts/start-backend.sh`, triggered a real `POST /api/data/jobs kind=expand source=yahoo` job that went `status=resumable` live, and captured 8/8 PASS with a genuine 1.17MB full-page render (UT-02-result.png) — far stronger evidence than QA implied. Always read `reports/phase-<iter>-ui-test-results.md` directly; do not let the QA report's defer downgrade a journey when browser-QA actually ran live. Separately: a deleted/rebuilt SEED artifact is not automatically a fabrication red flag — here the corrupt 0-member `universe.json` (the literal HTTP-401 bug residue) was removed and `meta.json` rebuilt to the true price manifest, which un-corrupts the bug and RE-ENABLES J-39 seed-window protection (coherence classified both as moves toward honesty). Verify the direction (toward vs away from honesty) before treating a seed-file diff as suspect.
**Applies to:** any iter where the QA report and browser-qa-agent report disagree on whether live browser evidence exists; any iter touching `apps/backend/data/seed/` (read coherence + the diff direction before flagging fabrication); the upcoming J-85 snapshot-rebuild + J-86 forward_returns-column iters.

## iter-27 — 2026-06-17T07:00:00Z

**Verdict:** CONTINUE
**Lesson:** A browser-QA "sort does not reorder" FAIL can be a SELECTOR false-negative, not a code defect: the iter-27 run drove `//th//button[normalize-space(text())='5d']`, but the `SortHeader` button's label lives in a nested `<span>`, so XPath `text()` matches nothing — and even a fallback JS `.click()` can resolve the wrong node. Always resolve sort buttons by their `aria-label` ("Sort by 5d", "Sort by 5d MDD"), and before calling sort a regression, check the git diff: if `onSort`/`SortHeader`/the sort memo are byte-unchanged (iter-27 only added an additive `mdd_` comparator branch), a "new" sort failure is far more likely a test artifact than a regression. SEPARATELY real and source-confirmable: `forward-return.tsx mddClass()` returns a flat `text-neg` for all negatives, so the spec's "colour-graded by magnitude" leg genuinely fails — verify colour-grading claims against the helper source, not a screenshot.
**Applies to:** any iter adding/verifying client-side sortable columns under the J-48 view-transform contract (`SortHeader` + `comparatorFor`); any iter whose browser-QA resolves table-header buttons by visible text; any colour-grading acceptance leg (check the `*Class()` helper source).

## iter-28 — 2026-06-17T09:00:00Z

**Verdict:** GOAL_ACHIEVED
**Lesson:** Tailwind v3.4 opacity modifiers (`text-neg/40`) are a silent NO-OP when the palette token is a plain hex CSS var with no `<alpha-value>` channel — they generate ZERO CSS rule, so a "graded" colour built that way renders flat. The token-faithful way to grade a single design token by intensity is a `color-mix(in_srgb,var(--neg)_N%,var(--text-muted))` arbitrary-value utility (compiles to real per-band rgb, no new hex). The dev caught this empirically against the built `layout.css` rather than trusting the spec's suggested `text-neg/40` wording.
**Applies to:** any future iter that proposes Tailwind opacity-modifier utilities (`text-x/NN`, `bg-x/NN`) for a graded/intensity colour scale on this frontend — verify the modifier actually emits CSS, or use `color-mix` over the design token instead.

## iter-28b — 2026-06-17T09:00:00Z

**Verdict:** GOAL_ACHIEVED
**Lesson:** A browser-QA "sort does not reorder" FAIL on this leaderboard was AGAIN a selector false-negative (iter-27 -> iter-28): `SortHeader` labels live in a nested `<span>`, so XPath `//th//button[text()='5d']` matches nothing while `button[aria-label^="Sort by 5d"]` resolves correctly. Before recording a sort regression, confirm (a) the sort code path (comparatorFor/onSort/SortHeader/sorted memo) is byte-unchanged in the git diff and (b) QA resolved the header by `aria-label`, not visible `text()`.
**Applies to:** any iter that re-verifies or touches leaderboard column sorting on /stocks, /themes, /sectors, or /research/samples.

## iter-29 — 2026-06-17T23:30:00Z

**Verdict:** CONTINUE
**Lesson:** On this 1369-run daily-history host, any `test_market_phase.py` test using the `loaded_engine` seed fixture (line 318+: 2022-bear reproduction, gate-invariance, cache, API repoint/error) boots the heavy backend and cannot finish under a subagent Bash cap (saw SIGTERM/143 and a SIGKILL `exit=137` on the nohup full-suite wrapper). The fix that worked: independently re-run ONLY the FAST synthetic + config-validation tests (test_market_phase.py lines 92–307: no-lookahead tail-invariance, determinism, filter causality, disclosure-cap, the six config-validation legs) + `test_no_magic_numbers` + `test_db::test_create_all_produces_expected_tables` — these (18+1+1 here) cover every anti-goal-critical leg in ~20s with no backend boot, and verify the dev's green claims without trusting the killed suite. `exit=137` in `/tmp/mp_full_suite.log` is the known background-helper harness-kill, NOT a test failure — do not treat it as RED.
**Applies to:** any goal-mode iter on this daily-history host that adds backend tests gated by a seed-loading fixture (`loaded_engine`-style) and whose full pytest suite is the GOAL_ACHIEVED gate — split fast (no-boot) vs slow (seed-boot) tests; verify anti-goal legs via the fast set; on a GOAL_ACHIEVED-candidate iteration, additionally require a flushed `0 failed, EXIT 0` from a `nohup`-launched full suite via the pump.

## iter-30 — 2026-06-18T01:30:00Z

**Verdict:** CONTINUE
**Lesson:** A FULL-depth backend+frontend iteration can land a correct, coherent, test-green backend (J-89/J-90: fence + tail-invariance + count-coherence all verifiable offline) yet still NOT advance any journey to `passing` because browser-QA was SKIPPED (Chrome MCP ECONNREFUSED :9222) — UI journeys (timeline overlay, fenced retrospective sub-view, recovery-turn badge, /research lab toggles + N= drill-down) require LIVE evidence and stay `unknown` without it (the iter-17 precedent). When the env is down, the cheapest forward move is a LEAN live-only re-verification next iter, not a re-build. Separately: the iter-30 full-suite single `F` was `test_data_manager_jobs_pipeline.py` (a module the diff never touched) — it passed deterministically in isolation (3/3, 72s), the known scanner_runs-race / slow-boot flake under contended full-suite + concurrent warm-up. Always pin the F's ordinal to a test name and re-run it isolated before attributing a suite failure to the iteration.
**Applies to:** any iter whose target journeys are UI-facing when Chrome MCP / :9222 may be down (verify env health BEFORE dispatching full depth — a lean live pass is cheaper than re-running the full pipeline); and any iter reading a single full-suite `F` in `test_data_manager_jobs_pipeline.py` / scanner_runs-touching modules (re-run isolated, treat a deterministic-pass-in-isolation as a pre-existing flake, never an iteration regression).

## iter-32 — 2026-06-18T05:40:00Z

**Verdict:** CONTINUE
**Lesson:** Any iter that additively adds a top-level key to the `GET /api/data` overview payload (iter-32: J-92's `macro` block) trips `tests/test_api_data.py::test_get_data_overview_shape`, which asserts STRICT exact-set equality `set(payload) == {coverage, runs, sources, resumable_imports, unfinished_imports, job_progress}` — this is a THIRD instance of the same over-strict-blanket-guard family as `test_api_engine.py` (iter-23) and `_rsp_rank_key` no-magic (iter-20). The dev correctly remembered the `MACRO_TABLES` `test_db.py` guard but missed this sibling shape guard. When adding a key to ANY endpoint covered by an exact-`set(payload)==` assert, update that guard in the SAME iter (add the key or compare as a superset), not a consolidation iter later.
**Applies to:** any iter adding a field to `GET /api/data`, `/api/research/*`, or `/api/*/engine` payloads — grep for `set(payload) ==` / `set(...) == {` / `served == score_` byte-equality guards across `apps/backend/tests/` before declaring the suite the GOAL_ACHIEVED gate.

## iter-33 — 2026-06-18T19:57:11Z

**Verdict:** CONTINUE
**Lesson:** A QA report can claim "10/10 browser PASS" while the actual evidence is hollow: of the 3 captured frames, the two J-93 as-of-slide frames (`TC-14-stocks-current.png` / `TC-14-stocks-early-date.png`) were BYTE-IDENTICAL (md5 ae9c2e38, only Latest/122) and the J-94/J-96 `/data` frame (`TC-16`) was an un-hydrated EMPTY-SKELETON page — and the remaining "browser" rows were verified by "handoff documents / code inspection," not live interaction. The phase-closure-auditor independently caught this as CLOSURE-FAIL (missing `ui-test-results.md`) even though the QA verdict was PASS. Always md5sum the evidence dir AND open every frame cited for a NEW journey; a differential journey (membership slides with as-of) REQUIRES two byte-distinct frames, and a feature-render journey requires the rendered pixels, not a loading skeleton. Also: the captured /stocks frame showed 122/122 while the dev claimed the resolved latest universe is 120 (RPD/DNN price-gated) — a screenshot that contradicts the implementation's own stated behaviour is itself a red flag the capture predates or bypasses the new code path.
**Applies to:** any iter whose target is a per-as-of / differential UI behaviour (membership/universe sliding, date-stepping) or a new below-the-fold `/data` panel (timeline / coverage diagnostic); and any iter where the QA verdict is PASS but status.json shows `closure_failed` / a CLOSURE-FAIL verdict exists — trust the closure auditor and the pixels over the QA prose.

## iter-34 — 2026-06-18T22:57:00Z

**Verdict:** CONTINUE
**Lesson:** A backend feature can be BUILT, unit-correct, and coherence-clean (the iter-33 `universe_resolver` passes 14 tests, is no-lookahead + no-magic-number) yet still FAIL its user-facing acceptance because the **persisted snapshot layer it feeds was never regenerated**. `score_stocks` (scoring.py:249) was repointed to `resolve_members` in iter-33, but `/stocks` serves the IMMUTABLE stored `ScannerResult` snapshots (api/stocks.py — "no recompute in the read path"), and those were built by the iter-27 J-85 rebuild over the OLD static 122-member universe. Result: `/stocks` + the J-96 membership timeline show a flat 122 at EVERY as-of (incl. 2021-01-04), while the J-94 diagnostic (which calls the resolver directly) correctly shows the dynamic ~544. The fix is not code — it is running the J-85 confirm-gated regenerate-from-scratch rebuild (~11h, destructive, operator-gated per MEMORY.md). For any iteration that changes WHAT a scan iterates/computes, the acceptance is only met after the snapshots are rebuilt; QA's "two byte-distinct frames" guard is insufficient — assert the ROW COUNT / step-function actually changes with the as-of, and reconcile a direct-resolver diagnostic against the served stored membership (they will silently disagree until the rebuild runs).
**Applies to:** any iter changing the universe/membership the scanner iterates or any canonical computation feeding stored `ScannerResult` snapshots (`scoring.py`, `universe_resolver.py`, `forward_testing.py`) — the change is only user-visible after a J-85 rebuild persists it; verify the served `/stocks` row count and the `/data` membership-timeline step function actually slide with the as-of, and reconcile the resolver-direct diagnostic vs the snapshot-served membership.

## iter-35 — 2026-06-19T12:30:00+00:00

**Verdict:** REGRESSION
**Lesson:** The J-85 rebuild that FIXED J-93 (dynamic universe now slides 0->544 on /stocks) simultaneously REGRESSED the /data page: `compute_coverage` (apps/backend/app/engine/data_manager.py:531) always computes the J-96 `_membership_timeline` (:469-528), which loops ALL ~1369 snapshot dates calling `universe_resolver.resolve_with_reasons()` per date (:514) with NO result cache. That loop was cheap when every date resolved a trivial static-122 set but is intractable (>300s, 0 bytes) once each date resolves up to 544 members — so `GET /api/data` hangs and the whole /data page (J-94 diagnostic + J-96 timeline) renders only un-hydrated skeletons. A correct DATA-volume increase exposed a latent O(dates×pool) read-path cost; the served VALUES are correct, only delivery is too slow. Fix is a read-path cache/precompute-during-warmup/pagination (byte-identical served block), never another rebuild or resolver-math change.
**Applies to:** any iter that runs the J-85 rebuild or otherwise grows the snapshot set; any change touching `compute_coverage` / `_membership_timeline` / `universe_resolver.resolve_with_reasons`; and any GOAL_ACHIEVED candidacy that depends on the /data page rendering — a data-regeneration iteration must smoke `GET /api/data` for response time, not just verify the DB-direct values.

## iter-36 — 2026-06-19T17:30:00+00:00

**Verdict:** CONTINUE
**Lesson:** A backend-only read-path fix whose ENTIRE PURPOSE is to restore a previously-broken PAGE RENDER (here: making `GET /api/data` responsive so the /data J-94 diagnostic + J-96 timeline hydrate again) will be AUTO-SKIPPED by the framework's browser-QA on a "Frontend Present: no" metadata flag — even though the iter spec's TESTING REQUIREMENTS + DoD explicitly demand LIVE re-render evidence, and plan.md/QA/audit all warned NOT to skip it (audit logged it as GAP F1). The "Frontend Present: no" auto-skip keys off "did frontend FILES change," not "is a user-facing render the acceptance criterion." So the fix lands byte-identical and verified at the API layer (dev ~12s, QA ~15.6s, audit 0 byte-mismatches) yet the regressed/partial journeys CANNOT flip to passing — the strict rule (no UI journey passing without positive live render evidence) forces a separate lean live-re-verify iteration (the iter-30->31, iter-33->34 pattern repeats a third time). Do NOT mark J-94 passing / J-96 passing on "the endpoint is fast and the components are byte-unchanged so it's expected to render" — expected is not verified.
**Applies to:** any goal-mode iter that is backend-only (Frontend Present: no) but whose target/regressed journey is a RENDERED page (hydration restore, perf fix that unblocks a render, an endpoint a page depends on) — expect browser-QA to AUTO-SKIP, plan a lean live re-verify next iter, and never flip a UI journey to passing from API-layer evidence alone. To avoid the wasted round-trip, the decomposer could set `Frontend Present: yes` (or otherwise force the browser-QA step) on such restore-a-render iterations so the live evidence is captured in the SAME iteration.

## iter-37 — 2026-06-19T23:10:00+00:00

**Verdict:** GOAL_ACHIEVED
**Lesson:** A read-path cache optimization that is byte-identical for the COMMON case can still silently break a performance/correctness invariant for an UNHANDLED edge case — here iter-36's `_BarCache.trailing_count` cold-miss path was byte-identical for symbols WITH bars but re-issued a per-date lazy load for zero-bar candidate-pool symbols (never recorded by `prefill`), breaking the J-46 load-once-per-job invariant. The served VALUE was correct (0 trailing bars either way) so targeted QA and coherence both passed; only the FULL suite's `test_bar_cache::test_kdate_backfill_loads_each_symbol_at_most_once` (which asserts load-COUNT, not value) caught it (`assert 3 == 1`). The fix records an empty `[]` series up front for no-bar expected symbols (descriptive, not fabricated). Two takeaways: (1) when an optimization is justified by "byte-identical served value", ALSO assert the load/compute-count invariant it claims to preserve — a value-equality test cannot catch a load-count regression; (2) the standing flushed-GREEN-full-suite gate earned its keep — it caught a regression that 4 layers of targeted/coherence/review checks missed.
**Applies to:** any iter touching `apps/backend/app/engine/prices.py` `_BarCache` / `prefilled_bar_cache` / the resolver's `trailing_count` path, or any future read-path caching/precompute optimization justified by byte-identity — pair the value-equality assertion with a load/compute-count assertion, and gate on the FLUSHED full suite (not just targeted modules) before any GOAL_ACHIEVED candidacy.

## iter-38 — 2026-06-20T14:20:00Z

**Verdict:** CONTINUE
**Lesson:** An additive field added to a CACHED payload is INVISIBLE at every already-cached key until the cache is invalidated — and the existing cache key may not invalidate on a SCHEMA change. iter-38 added `timeline_full` to `compute_market_phase`'s payload, but `market_phase_cached` (apps/backend/app/engine/market_phase.py:810-811) keys on `(asof_key, _dataset_version)` where `_dataset_version` tracks DATA changes (backfill/removal), NOT the payload schema. So every pre-iter-38 cache row (incl. the LIVE current as-of under the unchanged `r1370-f3078889` stamp) was served verbatim WITHOUT `timeline_full`, and `market_phase_full_cached` (a pass-through) returned it field-less → `GET /api/market-phase?full=true` had no `timeline_full` → the J-97 chart's entire bottom pane (phase bands + severity + P(bear)) rendered EMPTY. Two compounding traps: (1) the QA report's TC-01 "1056 points returned" was a FRESH compute at a DIFFERENT as-of (2025-12-31, a cache MISS) which MASKED the bug — only the browser-qa-agent's (and my) probe of the LIVE CURRENT as-of (a cache HIT) exposed it; a cache-correctness check MUST hit the already-cached production key, not a fresh-compute date. (2) `test_no_magic_numbers`/coherence/review all passed because the engine code is correct in isolation — the defect lives entirely in the cache-vs-schema mismatch. When adding any additive field to a cached payload, bump a payload-SCHEMA-version component of the cache key (not just the data-version stamp) or prune rows lacking the new field, and unit-test the additive field against an already-populated cache row, not a fresh compute.
**Applies to:** any iter adding an additive field to a payload served through a `*_cached` helper keyed on `_dataset_version` (`market_phase_cached`, `event_study_cached`, the J-72 research aggregate cache, `MembershipTimelineCache`, the `retrospective` cache); and any QA/evaluator verifying such a field — probe the LIVE current as-of (a cache HIT) and md5sum/key-diff the actual cached row, never a fresh-compute date that masks a stale cache.

## iter-39 — 2026-06-20T15:42:16Z

**Verdict:** CONTINUE
**Lesson:** A correct, byte-identity-proven backend fix whose ENTIRE purpose is to flip a render-gated UI journey to passing still CANNOT flip it when browser-QA auto-skips — and the Chrome MCP CDP WebSocket timeout that empties the evidence dir is now RECURRENT on this host (iter-38 AND iter-39 both lost all render evidence to it; only iter-34/iter-37 escaped, via the Playwright fallback). The iter-39 spec set `Frontend Present: yes` specifically to force the live step in the SAME iter (iter-36 lesson), but the browser-qa-agent hit the CDP timeout and did NOT fall back to Playwright, so the full-depth dev pass produced a verified-correct fix that still leaves J-97 `failing` / J-98 `partial`. The cache fix itself is exemplary: `SCHEMA_VERSION="s1"` folded into the `MarketPhaseCache` key via `_cache_version()` (`market_phase.py`), unit-tested by SEEDING a genuine old-schema bare-stamp row with `timeline_full` stripped (a real cache HIT) — not the iter-38 fresh-compute mask that hid the bug.
**Applies to:** Any render-gated iter on this host (esp. Dashboard `/` market-phase chart / at-a-glance) — the dispatcher/QA MUST plan the Playwright fallback UP FRONT, not after Chrome MCP CDP times out, or the render evidence is lost and the journey cannot flip despite a correct fix. Also: any iter adding an ADDITIVE field to a CACHED payload must bump a payload-SCHEMA token in the cache key (not just the data-version stamp) and unit-test against an ALREADY-POPULATED old-schema cache row, never a fresh compute.

## iter-40 — 2026-06-20T18:37:33Z

**Verdict:** CONTINUE
**Lesson:** Two compounding evidence-capture lessons crystallized. (1) The Chrome MCP CDP WebSocket timeout has now emptied the evidence dir on iter-38 AND iter-39 and was avoided on iter-34/37/40 ONLY because the browser-qa-agent planned the Playwright fallback UP FRONT (per the spec NOTES) instead of waiting for Chrome MCP to time out first — a backend-correct, code-byte-unchanged fix still cannot flip a UI journey to passing without live render evidence, so the fallback MUST be pre-planned on every render-evidence iteration on this host. (2) A differential sub-leg (J-97 synced-zoom UT-04/UT-10) has silently produced a BYTE-IDENTICAL before/after pair (md5 e54ebb63...) across THREE consecutive iters (38/39/40) — a recurring false-positive trap: a "before/after" pair that is the same file proves nothing. QA must `md5sum` differential pairs and re-capture until they differ; the evaluator must `md5sum`-check any cited differential pair, not trust the filename suffix.
**Applies to:** any goal-mode iter that captures live render evidence via browser-qa on this host (always pre-plan the Playwright fallback), and any iter whose acceptance includes a differential leg — a synced zoom/pan, an as-of change updating a figure, a sort reorder (md5sum the pair; reject byte-identical "before"/"after").

## iter-42 — 2026-06-21T01:10:00Z

**Verdict:** CONTINUE
**Lesson:** A `Frontend Present: no` backend-only iteration auto-skips browser-QA (status.json `browser_checks_skipped_reason`), which is THE recurring blocker on a GOAL_ACHIEVED-candidate that is itself a *byte-identity property* (J-100, and before it J-94/J-96 in iter-36/39): the deliverable's whole claim is "no served value changed", which is only provable by re-rendering the protected surfaces — yet the framework skips exactly that render. Byte-identity at the compute layer (audit deep-equal, no payload key added) is necessary but NOT sufficient to flip the required-still-passing RENDERED journeys to "freshly verified"; it forces a lean live re-verify next iter (the iter-36→37 / iter-39→40 / iter-42→43 pattern). The fix the decomposer keeps trying — forcing browser-QA on a `no` flag — does not apply cleanly when there is genuinely no frontend diff, so plan the next-iter LEAN live re-verify (with the Playwright fallback up front, since Chrome MCP CDP has emptied the evidence dir on iters 38/39/40) as the closing half of every backend-only hardening pair.
**Applies to:** any backend-only iteration (`Frontend Present: no`) whose acceptance is "served values stay byte-identical" over RENDERED surfaces — its GOAL_ACHIEVED candidacy needs BOTH the flushed `0 failed, EXIT 0` suite AND a follow-up lean live re-render at the pre-change numbers; do not declare done on compute-layer byte-identity alone.

## iter-43 — 2026-06-21T03:40:00Z

**Verdict:** GOAL_ACHIEVED
**Lesson:** A backend-only optimization that changes NO served value still cannot flip its journey to passing without a SEPARATE live-render iteration, because a `Frontend Present: no` iteration auto-skips browser-QA — this "backend-only pair" cost a full round-trip THREE times (iter-36->37, iter-39->40, iter-42->43). To close a byte-identity-property journey (like J-100) in ONE iteration, set `Frontend Present: yes` on the SAME iteration that ships the backend change (it forces the render-capture step without requesting frontend edits), and plan the Playwright fallback up front (Chrome MCP CDP refused on iters 38/39/40/42/43; live evidence was captured only when Playwright was pre-planned).
**Applies to:** any goal-mode iter whose acceptance is "served values are byte-identical at the RENDER layer" after a backend-only perf/cache change — decompose it as a single `Frontend Present: yes` iteration with the Playwright fallback pre-planned, not a backend-only iter + a follow-up verify iter.

## iter-44 — 2026-06-22T11:18:00Z

**Verdict:** CONTINUE
**Lesson:** On an as-of change to a PRE-history date (e.g. ?asof=2021-01-04), the Dashboard re-enters a "Checking backend…" skeleton while it re-fetches, and a screenshot taken too early captures that skeleton instead of the rendered "Not enough history… reported NA, never fabricated" card — exactly what happened to iter-44's J-101b honest-empty leg (UT-09-2021-01-04.png). The leg still passed because that NA-honest empty behavior is pre-existing already-passing (J-09/J-87) and iter-44 didn't touch it, but a future iter whose ACCEPTANCE depends on the rendered honest-empty state must wait for the NA card to hydrate before capturing, and reject a "Checking backend…" frame as evidence.
**Applies to:** any iter capturing an early/pre-history as-of honest-empty leg on the Dashboard cross-view or Market-Phase card (J-09/J-87/J-101b and successors); and any backend-cached additive-field change to /api/market-phase — the s1->s2 SCHEMA_VERSION bump must be unit-tested against a real old-schema cache HIT, not a fresh compute (iter-38/39/44 keystone).

## iter-45 — 2026-06-22T14:31:00Z

**Verdict:** CONTINUE
**Lesson:** Two browser-QA failure modes masqueraded as code regressions and BOTH were false. (1) UT-09 "severity-velocity ignores ?asof" was a wrong-PARAM-SPELLING false-negative: the QA curled `?asof=` but the FastAPI endpoint declares `as_of: Optional[str] = Query(...)` (underscore), so the unrecognized param was silently dropped → `asof_date: null` is the CORRECT response, and `test_severity_velocity.py::test_as_of_filter_shrinks_pool_no_recompute` passing proves the filter works. The real frontend sends `as_of=` via `withAsOf` in `apps/frontend/lib/api.ts`. (2) UT-03/UT-04 (factor-lab stuck "Loading…", event-study HTTP 500/timeout) + UT-24/UT-25 skips were a HUNG LIVE BACKEND, not iter-45 code — the smoking gun was that PID 72189 was STILL at ~25% CPU at evaluation time AND even a "PASS"-marked relocated lab (UT-10) showed the same "Backend unavailable" banner in its screenshot. The labs' honest no-fabrication error state under load is correct behaviour. Running the touched research modules in ISOLATION on the quiet host (`test_research.py`+`test_samples.py` 108/108, `test_severity_velocity.py` 15/15) was the decisive disambiguator between genuine code breakage and live-backend contention.
**Applies to:** any iter that (a) adds a new FastAPI endpoint with an `as_of`-style query param — verify the EXACT param spelling the browser-QA used before trusting a curl-based "ignores param" FAIL; and (b) splits/relocates heavy `/research/*` (or `/api/data`) labs onto a contended live backend — when browser-QA shows "Backend unavailable"/500/timeout on the heavy labs, check whether the live backend is hung (CPU still pegged) and re-run the touched test modules in isolation before calling REGRESSION. Heavy-research browser-QA MUST run on a freshly-restarted, warmed, single-fetch-at-a-time backend.

## iter-46 — 2026-06-22T17:40:00Z

**Verdict:** REGRESSION
**Lesson:** A previously-GOAL_ACHIEVED product can REGRESS with ZERO code change: `_event_study_members_by_horizon` (apps/backend/app/engine/research.py:823) materializes the WHOLE `select(ForwardReturn).where(horizon.in_(horizons)).all()` into ORM objects — byte-identical since iter-20 — and it now MemoryErrors on the live DB because the J-85 rebuild + restored daily-history backfills grew `forward_returns` to ~3.08M rows (one all-history request peaks at ~5.3 GiB RSS, reproduced directly) and this shared host's available RAM oscillates 3-16 GiB. The full pytest suite never catches it because it runs on small fixtures, not the 3.3 GB live DB. Two skip causes coexisted and MUST be separated: a freshly-warmed-idle-backend MemoryError at the FIRST fetch is a real defect; a "Backend unavailable" under a concurrent full-suite is contention (re-verifiable). Verify scale-bounded read paths against the LIVE data volume, not just fixtures, before declaring GOAL_ACHIEVED.
**Applies to:** any iter that adds an unbounded `.all()` / full-table ORM materialization over `forward_returns` / `scanner_results` (research labs, factor-lab, event-study, warm-up `backfill_forward_returns`); any GOAL_ACHIEVED-candidate evaluation after a data-volume-growing op (J-85 rebuild / backfills) — re-probe the heavy read paths against the live DB.

## iter-47 — 2026-06-22T18:30:00Z

**Verdict:** CONTINUE
**Lesson:** A "stream the heavy read path" memory-safety fix can be HALF-DONE and look complete: iter-47 streamed every `select(ForwardReturn)…all()` but left the sibling `select(ScannerResult)…all()` in the SAME builders (`_factor_observations` research.py:216, `_combination_observations` research.py:421) materializing ~609K ORM rows. The bug only surfaced on the ONE lab that is UNCACHED (factor-lab / J-25) — factor-combination and regime-setup-pattern serve from the J-104 EventStudyCache, so they never rebuild the observation set and the same unstreamed `.all()` is a latent cold-miss OOM, invisible to a warm-cache QA pass. When fixing an OOM in a per-observation builder, grep EVERY unbounded `.all()` in the function (FR AND ScannerResult AND ScannerRun), and probe the UNCACHED lab cold — a cache hit will mask the defect on its siblings.
**Applies to:** any iter touching `apps/backend/app/engine/research.py` observation builders / heavy-lab read paths; any "stream the read path" memory-safety refactor; verifying labs that serve from EventStudyCache (cold-miss vs warm-hit divergence).
