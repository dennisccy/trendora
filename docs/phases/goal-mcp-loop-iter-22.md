# Goal Iteration 22 — Deep, vendor-labeled index/macro context on the 30-year basis (J-14)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** mcp-loop
- **Iteration:** 22
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-14
- **Required-still-passing journeys:** J-01, J-03, J-04, J-05, J-10, J-12, J-13
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

Surface the committed deep index context — the equity-index benchmarks `^SPX`/`^NDX`/`^DJI` (deep to 1996) and the `^VIX` / FRED-macro-proxy overlays — across the deep 30-year window on the Dashboard major-indexes chart, each **labeled with its honest data vendor** (Stooq / Yahoo / FRED-macro proxy), and disclose the same per-series vendor on `/data`.

## BACKGROUND

J-13 (iter-21) was the last non-evidence journey to land; J-14 is the most-ready forward feature and the iter-21 evaluator's #1 recommendation. Its entire data basis is already committed and validated: iter-17 staged the deep index/macro series and iter-18 swapped them into `data/seed/` with per-series vendor records in `meta.json` (`^SPX`/`^NDX`/`^DJI`→`stooq`, `^VIX`→`yahoo`, `^TNX`/`^DXY`/`^VXN`→`fred-macro-proxy`) — so this is a surfacing + disclosure journey with **no human blocker and no referee gate** (no new "Proven" claim → the post-decompose gate passes automatically, like iter-20).

Target selection followed the priority rubric: no journey is regressed (rule 1 n/a); coherence was COHERENCE-PASS so no consolidation is owed (rule 2 n/a); among the three remaining forward tracks J-14 is the smallest well-scoped, lowest-blast-radius step (rule 4) — the fast-platform perf work (J-15/J-16) is a cross-cutting backend refactor, and the evidence re-cert (J-02/J-06/J-07/J-08/J-09) is blocked on a precondition that does not currently exist (both 30-year ledgers are all-FAIL; there is **no** staging winner clearing the canonical Bonferroni divisor-8 bar, so "promote the winner" cannot be planned without a discovery pass first — iter-12 lesson). J-14 is one journey, not two risky ones (rule 5), and is not human-blocked (rule 6).

**Depth = full** is justified by the depth triggers (cited per self-check): the iteration crosses backend (config + `compute_index_series` + load-scope/DB rebuild) and frontend (chart legend + `/data` disclosure), registers a **new Data Contract value** (the per-series vendor label), ships a **new user-facing surface**, and makes a **data-path change** (new index/benchmark symbols loaded into `daily_prices`, currently 0 rows) that needs byte-identity verification — beyond a browser smoke check. The prior evaluator also recommended FULL. (Prior verdict was CONTINUE, not ESCALATE, so full is a justified choice, not a forced one.)

**Grounding evidence gathered this planning pass** (so downstream agents don't re-discover it):
- The deep series are committed CSVs (`data/seed/prices/_SPX.csv` … `_VXN.csv`; on-disk `_`-prefix maps from the canonical `^`-symbol via `seed_provider.symbol_to_filename`) and carry `vendor` in `data/seed/meta.json` `symbols[]` (caret keys). But they have **0 rows in `daily_prices`** today (`SPY`/`AAPL` are loaded; `^SPX`/`^VIX` are not) — they are not yet in the load scope.
- `all_seed_symbols` (`app/seed_loader.py:48`) enumerates `config.index_chart.symbols` (today: SPY/QQQ/IWM/RSP/DIA — all ETFs) + `etfs.*` + macro proxies; adding `^SPX`/`^NDX`/`^DJI` to `index_chart.symbols` both loads them and renders them.
- The canonical index-display value is `app.engine.indexes:compute_index_series` → `GET /api/indexes`, consumed by `components/major-indexes-card.tsx` and the J-97 cross-view card (`/api/indexes?full=true`); `index_chart.default_range` is already `"all"`, so the deep window renders by default.
- `/data` already has a `MacroFeedPanel` (served by `GET /api/data` `macro`) — a distinct existing value (FRED macro feed catalog), NOT the vendor label.

## IN SCOPE

### Backend
- [ ] Add the deep equity-index benchmarks `^SPX`, `^NDX`, `^DJI` to `config.index_chart.symbols` (repo-root `config.yaml:298`) with honest legend/display names (e.g. "S&P 500 Index (^SPX)", "Nasdaq 100 Index (^NDX)", "Dow Jones (^DJI)") — this both (a) brings them into `all_seed_symbols` → `price_load_symbols` → `load_prices`, and (b) renders them as normalized-% lines on the major-indexes chart. Do **not** add them to `etfs.index` (that set is the RS/scoring benchmark universe — the deep index must NOT become a scored candidate or an RS benchmark).
- [ ] Ensure the deep index/macro series are actually loaded into `daily_prices` — currently `^SPX`/`^NDX`/`^DJI`/`^VIX` (+ `^TNX`/`^DXY`/`^VXN`) are 0 rows. Rebuild the DB (`data/trendora.db` via the load path / `data_manager` rebuild) so the committed CSVs populate `daily_prices`. A committed CSV with no bars stays honestly omitted (existing `load_prices` contract — a missing fixture is not a failure; never fabricated).
- [ ] Extend `app.engine.indexes:compute_index_series` to attach two **additive** fields to each emitted series entry: `vendor` (the display vendor read from `data/seed/meta.json` `symbols[].vendor` — `stooq`→"Stooq", `yahoo`→"Yahoo", `fred-macro-proxy`→"FRED-macro proxy") and `first` (the series' real first bar date, for the deep-window disclosure). Read the vendor from the SINGLE existing meta reader (`data_manager` seed-meta path over `meta.json`) — do NOT add a second meta-parse path. Series with no meta vendor record (SPY/QQQ/IWM/RSP/DIA) get `vendor: null` (honest omission — never a fabricated vendor).
- [ ] Keep the normalized-% `points` for the existing SPY/QQQ/IWM/RSP/DIA lines **byte-identical** (the change is additive fields + additional deep series; no existing line's math changes).

### Frontend
- [ ] `components/major-indexes-card.tsx` (+ `index-regime-chart.tsx` / the J-97 cross-view card as needed): render the new deep benchmark lines across the deep window (the `"all"` range already spans full history; verify a benchmark line extends before SPY's 2005 start) and show each series' **vendor label** in the legend/tooltip. Show a vendor label ONLY where `vendor` is present; render nothing (not a fabricated vendor) for the ETF lines whose `vendor` is null. Re-validate every existing consumer of the `/api/indexes` series shape for the additive `vendor`/`first` keys (iter-18 lesson — new fields must not break a consumer).
- [ ] `/data` (`app/data/page.tsx`): add a small **index/benchmark vendor-disclosure** panel that lists each deep index/benchmark/macro series with its vendor, read from the SAME `GET /api/indexes` payload (an additional reader — not a re-parse of `meta.json`, not a new `/api/data` field). A `fred-macro-proxy` series must read as an honest **"FRED-macro proxy"** (optionally with its committed `note`) and NEVER as a market index.

### New user-facing capability
The user can see the market's deep index context — the S&P 500 / Nasdaq 100 / Dow benchmarks charted back to the 1990s (beyond the ETFs' ~2005 floor) plus the volatility/macro overlays — and can see, per series, exactly which vendor supplied it, so the honest data provenance of the 30-year basis is visible rather than implicit.

### New information displayed
- Deep `^SPX`/`^NDX`/`^DJI` normalized-% benchmark lines on the Dashboard major-indexes chart, extending across the full 30-year window.
- A per-series **vendor label** (Stooq / Yahoo / FRED-macro proxy) on the chart legend/tooltip and in a `/data` disclosure panel, plus each series' honest first-bar date.

### New user actions
None beyond the existing chart range/hover controls — this is context + disclosure, not a new interaction.

### UI surface changes
- Dashboard `/` major-indexes & regime card: additional deep benchmark lines + vendor labels.
- `/data`: a new index/benchmark vendor-disclosure panel.

### Product surface delta
The 30-year basis stops being an invisible backend fact and becomes visible, honestly-sourced market context: the headline benchmarks reach back three decades and every index/macro series wears its vendor badge — reinforcing the product's skeptical, evidence-first, "show your sources" posture.

### Blueprint conformance
J-14's homes are already registered in `blueprint.md` Information Architecture: **Dashboard `/` (major-indexes & regime card) + `/data` (vendor/macro disclosure)** — both existing homes, reachable in ≤2 clicks. **No nav-skeleton change** (no re-approval file needed). This iteration adds an "iter-22 clarification" note to the blueprint documenting the additive value registration.

### Data-contract additions
ONE new displayed value, registered additively in `blueprint.md` this iteration:

| Value | Computed once by | Served by |
|---|---|---|
| **Index/benchmark/macro series vendor label + honest first-bar window** (per series: vendor ∈ {Stooq, Yahoo, FRED-macro proxy}; the series' real first date) | `app.engine.indexes:compute_index_series` (sole assembler; reads the single vendor source `data/seed/meta.json` `symbols[].vendor` via the existing `data_manager` seed-meta reader — no second parse) | `GET /api/indexes` (the existing canonical index-display endpoint; additive `vendor`/`first` fields) |

Both surfaces (Dashboard chart legend + `/data` disclosure) READ this one endpoint — never a second computation or endpoint. The existing `/api/data` `macro` catalog value is unchanged; the macro proxies' vendor is disclosed through the SAME new `/api/indexes` field as every other series (single source, keeping them coherent).

## OUT OF SCOPE

- **Evidence re-certification (J-02/J-06/J-07/J-08/J-09).** Both 30-year ledgers are all-FAIL; there is no staging winner clearing the canonical Bonferroni divisor-8 bar. That track needs a separate discovery iteration (re-run the pre-registered staging exploration on the new basis) BEFORE any canonical promotion — do NOT append a canonical `## Evidence Claim` here (iter-10/iter-12 footgun: a FAIL permanently tightens the bar; iter-9b: an omitted `"ledger"` key silently re-stages).
- **Fast-platform perf budgets (J-15/J-16).** Separate iteration.
- **Re-fetching `^TNX`/`^DXY`/`^VXN` from Yahoo.** goal.md §H forbids it — they are deterministic FRED-macro proxies coherent with `data/seed/macro/`; a Yahoo re-fetch would desync them and silently change their meaning. Keep them exactly as committed; only DISCLOSE their vendor.
- **Any change to the FRED macro catalog / `MacroFeedPanel` computation** (existing `/api/data` `macro` value) — only ADD the vendor disclosure that reads `/api/indexes`.
- **Regime VIX-gate behavior** — pre-existing; not J-14 (J-04 remains passing and is in the regression set).
- **Any intra-series vendor splice** — forbidden (no adjustment seam); each series is single-vendor.
- Adding the deep indices to `etfs.index` / any scoring/RS/universe path.

## DEFINITION OF DONE

- [ ] Target journey **J-14 passes via browser-qa-agent**, with md5-distinct, correctly-labeled full-page/element-clip screenshots showing: (a) the Dashboard major-indexes chart rendering a deep benchmark line (`^SPX`) that extends before SPY's 2005 start; (b) the per-series vendor label (Stooq / Yahoo / FRED-macro proxy) visible on the chart legend/tooltip; (c) the `/data` vendor-disclosure panel listing each series' vendor.
- [ ] **Correctness (anti-goal #3):** a deep series' displayed first-bar date byte-matches `meta.json` (`^SPX` first = `1996-01-02`); a `fred-macro-proxy` series is labeled "FRED-macro proxy" and never presented as a market index.
- [ ] `GET /api/indexes` returns **byte-identical** normalized-% `points` for the existing SPY/QQQ/IWM/RSP/DIA lines (verified by a unit/API test); the only diff is additive `vendor`/`first` fields + the new deep series.
- [ ] **No index/benchmark symbol leaks** into the `/stocks` leaderboard or the universe count — J-01 `/stocks` and J-12 `/data`+`/stocks` counts remain unchanged (deep indices are not scored candidates).
- [ ] Required-still-passing journeys **J-01, J-03, J-04, J-05, J-10, J-12, J-13 remain green** on live canonical replay.
- [ ] No anti-goal violation introduced (no return/price/buy-sell language in the new vendor/disclosure copy; no fabricated bars or vendors; determinism/no-lookahead preserved; graceful degrade on a missing series/vendor).
- [ ] Unit/integration tests pass; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-mcp-loop-iter-22-dev.md`.

## TESTING REQUIREMENTS

- **Browser (canonical `browser-qa-agent` lane, live):** J-14 (deep-benchmark chart lines across the deep window + per-series vendor labels; `/data` vendor-disclosure panel). Live-replay the regression set: J-01 (`/stocks` leaderboard, no leaked index rows, no crash), J-03 (all "Not yet proven" — no new "Proven" leaked), J-04 (Dashboard regime label + evidence affordance intact after the chart gains lines), J-05 (`/evidence` ledger), J-10 (`/stocks/{ticker}` deep-history chart + `/backtest`), J-12 (`/data` "Universe" count == `/stocks` count, unchanged), J-13 (`/data` availability legend + 548 reflection unchanged).
  - **Harness discipline (iter-20/21 lessons — mandatory):** `rm -rf apps/frontend/.next` before serving; confirm BOTH prod-mode services (`:3255` frontend, `:8255` backend) are reachable BEFORE dispatching QA; the canonical lane must RUN LIVE (not code-inspect) and write a non-empty, md5-distinct evidence dir; do not accept a QA/status "ready to ship" over an empty evidence dir or a CLOSURE-FAIL.
- **Unit/integration:**
  - `compute_index_series`: the new deep series (`^SPX`/`^NDX`/`^DJI`) are included when loaded; each emitted series carries the correct `vendor` (from `meta.json`) and honest `first`; the existing SPY/QQQ/IWM/RSP/DIA `points` are byte-identical (freeze/golden the existing lines).
  - Load scope: `all_seed_symbols`/`price_load_symbols` include `^SPX`/`^NDX`/`^DJI` (+ `^VIX`); a post-rebuild `daily_prices` has bars for them; the deep indices are absent from the scored universe/leaderboard.
  - Vendor mapping: `stooq`→"Stooq", `yahoo`→"Yahoo", `fred-macro-proxy`→"FRED-macro proxy".
- **Error cases:**
  - A configured index symbol with no committed CSV / no bars → honestly omitted from the chart (no fabricated line), consistent with the existing DIA-omission contract.
  - A series with no `meta.json` vendor record (the ETFs) → `vendor: null` → the UI renders no vendor label (never a fabricated vendor).
  - Unknown range preset → existing 422 behavior preserved.

## NOTES

- **No `## Evidence Claim`** in this spec — J-14 surfaces context/provenance, not a "Proven" edge; the post-decompose gate passes automatically (mirrors iter-20's pure-surfacing case). Do NOT introduce any certified claim here.
- **Applied lessons:**
  - *iter-18 / iter-19 (data-shape widening):* the new `vendor`/`first` keys and the null-vendor case for ETF lines must be handled through honest, contained rendering — show a vendor label only where present, never fabricate one; re-validate EVERY `/api/indexes` consumer (`major-indexes-card`, `index-regime-chart`, the J-97 cross-view card) for the additive fields. Adding new symbols to `daily_prices` must not crash any page (anti-goal #8).
  - *iter-11 / iter-13 / iter-14 (screenshot hygiene):* scroll the asserted chart line / vendor label into frame and prefer full-page or element-clip captures; md5-check the evidence PNGs so a below-the-fold `/data` panel or a legend chip is genuinely pixel-visible, not a relabeled top-of-page frame.
  - *iter-21 (replay vs golden script):* if a required-still-passing replay's golden script asserts the exact major-indexes legend set, the added deep-benchmark lines are an INTENDED additive surface change — refresh the stale assertion; a changed legend is not a regression (verify against the journey's own golden script + confirm the substantive capability holds).
- **Symbol naming caveat for the developer:** the canonical symbol is the caret form (`^SPX`), the committed CSV is the underscore form (`_SPX.csv`) via `seed_provider.symbol_to_filename`, and `meta.json` `symbols[]` keys on the caret form — key the vendor lookup consistently on the canonical `^`-symbol.
- **Why depth is full (self-check #4):** crosses backend+frontend, registers a new Data Contract value, ships a new user-facing surface, and makes a byte-identity-gated data-path change (new symbols in `daily_prices` + DB rebuild) — each a full-cycle trigger; prior evaluator also recommended full.
