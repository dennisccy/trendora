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
