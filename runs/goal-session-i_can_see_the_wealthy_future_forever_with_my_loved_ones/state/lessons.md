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
