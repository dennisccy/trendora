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
