# Iteration Summary — goal-i_can_see_the_wealthy_future_forever-iter-21

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-06-05
**Iteration:** 21

## In plain words

**What you can do now:** See the day's market at a glance; browse ranked stocks, sectors, and themes and filter by sector, setup, or chart pattern using shareable links; open any stock for a plain-English scorecard that matches between the list and the detail page, plus the price that would prove the idea wrong; rewind the whole app to any past day with one shared date control and watch a price chart keep drawing past it; read forward-tested track-record evidence by score grade, benchmark, and control group on the Backtest page as of any past day; explore the Research area to test whether a signal sorts future returns — by group, by market mood, as a multi-signal blend, and across a volatility family, each viewable all-history or rewound to a point in time; study any setup or pattern's full track record; jump from a finding to the names behind it and on to the scorecard; keep a restart-proof watchlist; grow the dataset by date; and look up every label in a plain-language glossary — always with honest "not enough data yet" marks.

**What changed this time:** The Data Manager gained a new Import source picker: you can now choose which data provider an import pulls from (Yahoo, Tiingo, Finnhub, Alpha Vantage, or Stooq), see at a glance which ones are ready versus which need a key, and paste a key just for that run. The picker, the availability tags, and the paste field all work — but this feature is not finished yet: when a provider rejects the request, a key you pasted can still appear inside the job's error messages, so it needs a small safety fix before it can be trusted.

**What's next:** First a focused safety fix so a pasted key never shows up anywhere, then an import that pauses and resumes when a data source is busy or rate-limited.

## Headline

Built the config-driven import-source picker on Data Manager; a pasted key leaks into job errors — fix-first next iter.

## Direction

**Signal:** holding
**Why:** This iter built the J-33 import-source picker (config-driven provider catalog, env-detected availability, session-only key field, four raise-never-fabricate EOD clients) — browser-verified 12/13 with J-17 backfill and J-18 one-date-control both re-confirmed — but it lands at *partial*, not passing, because a pasted session key leaks into the job-status error list (root cause: `_http.py:42` wraps `str(httpx.HTTPStatusError)`, which embeds the `?token=`/`?apikey=` URL for tiingo/finnhub/alpha_vantage). No prior-passing journey regressed and the violation is minor/contained/non-durable, so the evaluator returned CONTINUE with a mandatory fix-first iter-22. Net direction is steady: real capability landed but the journey has not crossed the line, and the leak fix plus J-34/J-35 remain buildable.

**Trend (last 5 iters):**
- Newly passing this iter: none (J-33 advanced failing → partial, not passing)
- Newly passing in last 5 iters total: J-32 (iter-19), J-26 (iter-18), J-09/J-10 (iter-17, re-delivered in their relocated Backtest home)
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: 1 — iter-21 pasted-import-key echoed in the job-status error list (minor, contained, **unresolved**)
- Iters with no journey state change: 0 of last 5

**Latest evaluator reasoning:** This is NOT GOAL_ACHIEVED and NOT REGRESSION, despite dev/review/coherence all passing. The skeptical catch this iter was that QA and browser-QA BOTH returned FAIL on a verified breach of the iteration's PRINCIPAL anti-goal: a pasted session-only API key is echoed back in `GET /api/data/jobs/{id}` (`errors[]`) and rendered in the `/data` job card. The verdict turns on severity: this is a credential reflected only to the same user's own transient in-memory job-status within the session they pasted it, nothing durable or external — so it is a minor / non-halting anti-goal violation, NOT a "committed-secret / external-exposure / backdoor" critical that maps to REGRESSION. So CONTINUE with a mandatory fix-first consolidation; the unresolved violation is the safety net — it vetoes any future GOAL_ACHIEVED until cleared.

## What was done

- Built the config-driven import-provider catalog (`ProviderCatalogEntry` + `DataManagerCfg.providers`/`default_source` in `config.yaml`/`config.py`) with boot validation raising `ConfigError` on a duplicate id, a missing `env_var` when `needs_key`, or `default_source` not in the catalog; retired the old 2-value `live_provider` Literal.
- Added four thin, lazy-imported EOD provider clients (Yahoo no-key; Tiingo/Finnhub/Alpha Vantage key-aware) behind `PriceProvider.get_daily` via a shared `_http.fetch_json`; any non-OK status / network error / unparseable body raises `ProviderUnavailableError` — never a fabricated bar.
- Added env-detected `compute_provider_availability` (returns the env-var name + a boolean + a reason only — never the key value) and threaded a request-only `source` + session-only `api_key` through the job; `GET /api/data` now returns a `sources` availability array; unknown source and needs-key-without-key both return an explicit 400.
- Added the `/data` Import-source `<select>` (populated from `data.sources`, no hardcoded list), a per-source availability line, and a conditional session-only `type="password"` key field held in React memory only (cleared on completion/unmount); fixed the stale "System Health" → "Backtest" subtitle.
- Re-verified the required-still-passing journeys: J-17 backfill ran end-to-end (status ok, 5 snapshots over 5 dates, 3200 forward returns) and J-18 held (exactly one date `<select>` app-wide); full backend suite 502 passed / 4 skipped, frontend typechecks clean, no DB regen.
- Browser QA 12/13 PASS — but UT-08 (P1) FAILED: a pasted session key is echoed in `GET /api/data/jobs/{id}` `errors[]` and rendered in the job card (QA report independently FAIL on TC-05/TC-07/TC-11; status.json status = blocked).

## What's left

- Journey J-33 (Import real data from a selectable, key-aware provider source) **partial** — the pasted session key leaks into job-status `errors[]` (root cause `_http.py:42` wrapping `str(httpx.HTTPStatusError)`, which embeds the `?token=`/`?apikey=` URL for tiingo/finnhub/alpha_vantage); a redaction fix + a real-httpx-error regression test gate it to passing.
- Open **minor anti-goal violation (unresolved)** — pasted import key echoed in the job-status error list; it vetoes any future GOAL_ACHIEVED until cleared (the leak is contained: DB, run-history, `/api/data`, backend log, committed files, and frontend storage are all clean).
- Journey J-34 (Chunked, rate-limit-resilient import that resumes from the last completed chunk) failing/unbuilt — iter-22 target; the fix must precede it because J-34's per-chunk error reporting would inherit the same leak.
- Journey J-35 (Expand the universe from the Data Manager) failing/unbuilt — iter-23 target; the operator path that auto-unblocks J-22.
- Journey J-22 (~500-name expanded universe) failing — externally data-walled (Yahoo 429), non-halting; auto-unblocks via J-35 or operator confirmation of a reachable egress.
- Journeys J-23 (multi-timeframe intraday bars) and J-24 (chart timeframe selector) failing — data-walled, non-halting; J-24 depends on J-23.
- Non-blocking deviation (Finding #2): a backfill job's header shows the defaulted `yahoo` source instead of omitting it (cosmetic in the transient header; the persisted run correctly records `seed`).
- Nits: `__PYTEST_RESULT__` placeholder left unsubstituted in the dev handoff; blueprint Data-Contract row says `ProviderCatalogCfg` vs the implemented `ProviderCatalogEntry`; `tsconfig.json` cosmetic churn.

## Next step

**full** depth, **iter-22 = FIX-FIRST consolidation then J-34**. (1) Fix the leak (gates J-33 → passing): in `_http.py` derive the error message from a redacted URL (`exc.request.url.copy_with(query=None)` + `response.status_code`) instead of raw `str(exc)`, and/or pass keys via an `Authorization` header, and/or scrub the resolved key value; treat job error strings as untrusted-for-secrets. (2) Add a **real-httpx-error** (key-in-URL) regression test through `get_daily` → `JobProgress.errors` → `GET /api/data/jobs/{id}` asserting the sentinel is absent (closes the mocked-provider blind spot that let it pass the 502-green suite). (3) Re-run browser-QA UT-08. (4) Then build **J-34** (chunked / durable-checkpoint / resumable / 429-backoff / Resume) on the now-safe foundation — the fix MUST precede J-34 because J-34's per-chunk error reporting would inherit the same leak. (5) Fold in non-blocking nits: Finding #2 (backfill header defaults to `yahoo`), the `__PYTEST_RESULT__` placeholder, the blueprint `ProviderCatalogCfg` → `ProviderCatalogEntry` name, the `tsconfig.json` churn. iter-23 = J-35 (auto-unblocks J-22). Do NOT autonomously re-probe J-22/J-23/J-24.

## Quick verify

From `reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-21-what-to-click.md`:

1. Open `http://localhost:3835/data` in your browser.
2. Read the grey subtitle directly under "Data Manager".
3. In the "Start a fetch / backfill job" card, confirm "Job kind" reads "Backfill snapshots", then look at the form.
4. Change the "Job kind" dropdown to "Fetch EOD prices".
5. With "Yahoo · available" selected, read the small availability line below the form row.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-i_can_see_the_wealthy_future_forever-iter-21.md |
| Dev handoff | — | docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-21-dev.md |
| Frontend handoff | — | docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-21-frontend.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-i_can_see_the_wealthy_future_forever-iter-21-review.md |
| Browser QA | FAIL | reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-21-ui-test-results.md |
| User-visible changes | — | reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-21-user-visible-changes.md |
| What to click | — | reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-21-what-to-click.md |
| UI surface map | — | reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-21-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-21-ui-test-plan.md |
| QA | FAIL | reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-21-qa.md |
| Status | blocked | runs/goal-i_can_see_the_wealthy_future_forever-iter-21/status.json |
| Journey history | — | runs/goal-session-i_can_see_the_wealthy_future_forever/state/journey-history.json |
