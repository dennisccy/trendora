# Goal iter-16 — UI Test Results (Browser QA)

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-16
**Date:** 2026-06-03
**Written by:** browser-qa-agent
**Mode:** goal-mode lean re-verify — J-31 synthesis-capstone cross-page travel (no code change expected)

---

**Browser QA Verdict:** PASS

<!-- PASS: J-31 full cross-page travel captured green on a clean, hydrated build; all Required-still-passing journeys verified live or carried. No anti-goal violation. -->

**Overall:** 13 / 13 journeys PASS (0 FAIL, 0 SKIP) — Target J-31 + 12 Required-still-passing.

The defining J-31 acceptance — the **full multi-step cross-page browser travel** (Factor Lab + Setup & Pattern Lab evidence → "View the names expressing this on the leaderboard →" cross-link → pre-filtered `/stocks` (DOM-asserted) → open a row → `/stocks/[ticker]` detail) — was **actually captured end-to-end** on a hydrated shell with DOM/network assertions at each step. Per the iter-4 conversion bar, this converts **J-31 `partial → passing`**.

---

## Pre-flight (gating) — hydration gate PASSED

The iter-15 SKIP was an environmental `.next` clobber (dead un-hydrated shell). This run confirmed the shell is **alive and hydrated BEFORE any UT case**:

| Check | Result |
|---|---|
| `GET /_next/static/chunks/main-app.js` | **HTTP 200** — real 6.4 MB dev chunk (`eval-source-map` header), not an HTML error page |
| `.next/BUILD_ID` | absent (dev mode) |
| `GET /api/health` | `{"status":"ok","db_ok":true,"provider":"seed","seed_latest_date":"2026-05-28","symbol_count":158}` |
| `/stocks` rendered | 122 row-links, full nav, A–E score badges, **no "Checking backend…" / dead-shell markers** |
| Live DOM | `asof-indicator:"Latest"`, count `122 / 122`, `as of 2026-05-28` |
| Ports | uvicorn:8835, next-server:3835 |

Evidence: `UT-PREFLIGHT-stocks-hydrated.png`. The developer's iter-16 env remediation (stop-by-port → `rm -rf .next` → clean restart) held; **no `npm run build` was run against the live dev `.next`**.

### Environmental note (mid-test backend restart — not a code defect)

During the Factor-Lab phase the backend (uvicorn pid 265265 on :8835) received an external **"Shutting down"** signal and exited cleanly (confirmed in `/tmp/fanout-backend-8835.log` — it had just served `factor-lab?factor=vcp_contraction` → 200, then shut down). This is an external process termination, **not a crash and not caused by the test**. The event study's honest "Backend unavailable" banner surfaced correctly (no fabricated data — anti-goal respected). The backend was restarted by port (`scripts/start-backend.sh`, CHAIN_BACKEND_PORT=8835, CORS for :3835), health 200 in 3s, and **every J-31 travel capture below ran against the healthy backend + hydrated frontend**.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-31 | Synthesis travel end-to-end | journey (target) | P1 | Lab evidence → cross-link → pre-filtered `/stocks` (DOM-asserted) → Stock Detail, no recompute/fabrication | Full travel captured; every step DOM/network-asserted; cross-link click → `/stocks?pattern=vcp__only` → 4/122 [STX,TSLA,TSM,ORCL] → STX detail | **PASS** | J31-step1-2, J31-step3-4, J05-J06-J20-stx-detail-latest |
| UT-J-25 | Factor Lab — decile + rank-IC (raw & risk-adj) | journey | P1 | Decile table (mean + downside risk-adj + n), numeric rank-IC, NA on low-sample, survivorship label | 10-decile table both columns + n; pooled IC shown; survivorship/descriptive labels; re-points on factor change | **PASS** | J25-J27-factorlab-leadership, J30-factorlab-vcp-contraction |
| UT-J-27 | Factor Lab — regime-conditioned | journey | P1 | Per-regime IC + top−bottom spread (raw & risk-adj), NA when n<min | By-regime table: Risk-on n=732 +0.02, Choppy n=122 −0.12, Risk-off n=242 −0.06; **NA on n=0 regimes** | **PASS** | J25-J27-factorlab-leadership |
| UT-J-29 | Setup & Pattern Lab — event study | journey | P1 | Distribution/expectancy/MAE-MFE/risk-adj/by-regime/by-sector; honest NA+n | VCP (n=27) full structure, honest NA (sub-threshold); pullback (n=163) **populated** mean/median/%pos/dispersion/expectancy/MAE/MFE/risk-adj, best-exit 60d, NA on low-sample regimes | **PASS** | J29-eventstudy-populated, J31-step1-2 |
| UT-J-30 | Volatility factor family | journey | P1 | Volatility-family decile (raw+risk-adj) + rank-IC, regime-conditioned | `vcp_contraction` decile re-points (D1 0.26–0.64 +5.85%/+0.89), IC −0.02 n=1217; D1 strongest risk-adj — consistent w/ VCP event-study expectancy | **PASS** | J30-factorlab-vcp-contraction |
| UT-J-28 | More detected patterns | journey | P1 | ≥2 new patterns, filterable, forward-tested | `pullback_to_rising_dma` (9) + `flat_base_breakout` (3) in registry/filter; pullback event-study populated; deep-link 9/122 asserted | **PASS** | J28-stocks-pullback-deeplink-9of122 |
| UT-J-16 | VCP — detected/explained/filterable | journey | P1 | VCP filter → flagged names w/ badge+reason+invalidation; pivot on detail | Filter `vcp__only` → 4 flagged [STX,TSLA,TSM,ORCL]; STX detail VCP badge, **pivot $905.39**, "VCP invalid below last-contraction low $816.98"; VCP ≠ setup (STX = Extended) | **PASS** | J31-step3-4, J05-J06-J20-stx-detail-latest |
| UT-J-02 | Stock Leaderboard filters | journey | P1 | Filter narrows visible rows; honest empty-state if none | Two deep-links DOM-asserted vs ground truth: **vcp→4/122**, **pullback→9/122**, exact ticker sets, badges present | **PASS** | J31-step3-4, J28-stocks-pullback-deeplink-9of122 |
| UT-J-05 | Stock Detail — explainable scores | journey | P1 | 3 scores A–E + 0–100 + ≥3 named components; invalidation level | STX: Leadership A/91.53 (**7 comp**), Entry E/32.11 (**5 comp**), Risk E/51.87 (**7 comp**, incl. honest "Earnings gap: NA"); "Invalid below the 50-DMA at $606.96" | **PASS** | J05-J06-J20-stx-detail-latest |
| UT-J-06 | Score consistency (coherence) | journey | P1 | Same scores leaderboard ↔ detail | STX leaderboard A/91.53,E/32.11,E/51.87 === detail A/91.53,E/32.11,E/51.87 (page states "identical to the leaderboard; single source of truth") | **PASS** | J31-step3-4, J05-J06-J20-stx-detail-latest |
| UT-J-20 | Chart full path through latest + as-of marker | journey | P1 | At historical D, chart extends to latest; D marked, post-D labelled; scores ≤ D | As-of 2025-11-28: chart includes 2026 dates (through latest 2026-05-28), **"Forward — after as-of 2025-11-28 (display only)"**, "bars ≤ 2025-11-28"; scores re-point A/90.70,E/38.47,E/59.71 | **PASS** | J20-stx-detail-historical-asof-marker |
| UT-J-18 | Exactly one date control | journey (principal anti-goal) | P1 | Filter persists across as-of toggle; page re-points; **page URL carries only sector/setup/pattern, never a date**; one date selector | Toggle Latest→2025-11-28 on `/stocks?pattern=vcp__only`: filter persists, re-points 4→2 (real snapshot), **URL params=[pattern] only, `url_has_date_param:false`**; network transmits the single global date via `as_of=` (snapshot-served read, not a 2nd date state) | **PASS** (see nuance) | J31-step3-4 (before 4/122), J18-after-historical-vcp-2of122 |
| UT-J-15 | Fast loads from persisted snapshot — filters must not refetch | journey | P1 | Filter change re-filters client-side; no per-request recompute; coherent values | Filter change (vcp__only→__all__): **0 `/api/stocks` requests** (`refetch_occurred:false`), count 122/122 from already-loaded data; values coherent with detail (J-06) | **PASS** | (network-asserted; see J-15 detail) |

---

## J-31 — Synthesis travel (the defining capture, step by step)

**Narrative chosen:** the textbook VCP synthesis — the `vcp_contraction` volatility factor (J-30) ↔ the VCP pattern event-study ↔ the names expressing VCP today.

1. **Factor Lab** (`/research`) — default `leadership_score`: 10-decile table (raw mean + downside risk-adjusted, each with n), pooled rank-IC, by-regime split, multi-factor cohort. Changed factor → **`vcp_contraction`**: decile ranges/means/risk-adj and pooled IC all **re-pointed** (leadership +0.00 n=1218 → vcp_contraction −0.02 n=1217; D1 mean +1.73%→+5.85%, risk-adj +0.21→+0.89). Distinct fingerprints + distinct shots prove the re-point. *(J-25/J-27/J-30 evidence)*
2. **Setup & Pattern Lab** (`/research`) — subject **VCP**: full event-study structure renders (per-horizon distribution + **Expectancy + Mean MAE + Mean MFE + Return/downside-dev + Return/MAE**, by-regime, by-sector) with **honest NA + n=27 ⚠** on every cell (n below the min-sample threshold). Additionally captured a **populated** subject `pullback_to_rising_dma` (n=163) showing real numbers (60d best-exit: mean +2.45%, MAE −14.13%, MFE +18.05%, ret/downside-dev +0.22) with honest NA only on its low-sample regime cells. *(J-29 evidence — both the honest-NA and the populated-numbers cases)*
3. **Cross-link click** — `data-testid="subject-leaderboard-link"` href `/stocks?pattern=vcp__only` clicked → navigated to the pre-filtered leaderboard. *(J-31 step 3)*
4. **DOM-assert** — `pattern_filter:"vcp__only"` ("VCP only"), sector/setup `__all__`, **count `4 / 122`**, visible tickers **[STX, TSLA, TSM, ORCL]** (exact ground-truth match), all 4 rows carry a VCP badge. *(J-31 step 4 / J-02 / J-16)*
5. **Open row → Stock Detail** — clicked STX → `/stocks/STX`: three A–E scores + raw 0–100 + named components (7/5/7), concrete invalidation ("Invalid below the 50-DMA at $606.96"), VCP badge + pivot $905.39 + "VCP invalid below the last-contraction low at $816.98", price+MA(20/50/150/200)+volume chart through the latest date. Scores **identical to the leaderboard** (J-06). *(J-31 step 5 / J-05 / J-06 / J-20)*

Every step read canonical stored values; no recomputed or fabricated number; low-sample lab cells shown as NA + n, not hidden.

---

## J-18 — nuance (principal anti-goal, honest network finding)

**Verdict: PASS on the actual anti-goal.** Measured reality on the as-of toggle (Latest → 2025-11-28) over the deep-linked `/stocks?pattern=vcp__only`:

- (a) **Filter stays intact** — `pattern_filter` remained `vcp__only`; sector/setup remained `__all__`. ✓
- (b) **Page re-points by date** — indicator → "Viewing as-of 2025-11-28 (historical)", data badge → "as of 2025-11-28", VCP-flagged set **4 → 2** ([STX, ISRG]). The re-pointed count is the **real** historical snapshot (API `/api/stocks?as_of=2025-11-28` returns exactly [STX, ISRG], 122 rows — no fabrication). ✓
- (c) **No date in the page URL** — after the toggle the URL stayed `/stocks?pattern=vcp__only`; `url_param_keys:["pattern"]`, `url_has_date_param:false`. Exactly one date selector (the global switcher); the frontend holds no second, independent date state. ✓

**Observed-network honesty note (discrepancy with the iter-16 spec's literal wording):** the spec's DoD/testing line asks for "**zero** `as_of`/date query param on the `/api/stocks` fetch." The **actual (and correct) implementation transmits the single global date** to the API: the toggle fired exactly one request `GET /api/stocks?as_of=2025-11-28` (confirmed via `performance.getEntriesByType('resource')`; `lib/api.ts:withAsOf` appends `?as_of=` only for a historical date, Latest sends nothing). This `as_of` is the **single global as-of being read** to fetch that date's immutable snapshot (the iter-8 snapshot-served-reads design that J-13/J-15 depend on) — it is **not** a second, independent date state and is **not** written to the page URL. The governing anti-goal ("Exactly one date selector … the frontend MUST NOT maintain a second, independent date state … `/stocks` carries only `sector`/`setup`/`pattern`, never a date") is therefore **fully satisfied**. The spec's literal "zero `as_of` on the fetch" does not match the codebase and would be impossible while still re-pointing by date via a query param; it is flagged here for the auditor rather than rubber-stamped, and is assessed as **not an anti-goal violation**.

---

## J-15 — warm load / filters must not refetch (network-asserted)

After a filter change (`vcp__only` → `__all__`) with the resource-timing buffer cleared immediately before: **0 `/api/stocks` requests** fired (`refetch_occurred:false`); the table re-filtered the already-fetched snapshot client-side (count → 122/122) and the URL cleaned to `/stocks` (still no date param). This proves the leaderboard is served from the persisted snapshot and re-filters without per-request recompute — the warm-path guarantee. (Wall-clock load budget not benchmarked: the server is in Next dev mode — on-demand compilation — so a `<1.5 s` timing is not a fair measurement here; the substantive snapshot-served + no-refetch + coherence criteria are met.)

---

## Skipped Tests

None. (Pre-flight hydration gate passed; the one mid-test backend shutdown was remediated by restart, and all captures ran healthy.)

---

## Anti-goal compliance (spot-checked during the travel)

- **Exactly one date selector** — verified (J-18): one global switcher; `/stocks` URL date-free; no second date state. No page-local date dropdown on the travel surfaces.
- **Single source of truth / no recompute in read path** — STX scores identical leaderboard ↔ detail (J-06); filters re-filter without refetch (J-15); lab figures derived once from stored evidence (read-only labels present).
- **No fabricated data** — backend-down surfaced an explicit "Backend unavailable" state (no fake figures); low-sample lab cells show NA + n (VCP n=27 all-NA; pullback low-sample regimes NA); zero-match honesty available; historical re-point count matched the real snapshot.
- **Research lab read-only & honest** — survivorship-bias + "descriptive, not predictive" labels render on Factor Lab and event study.

---

## Environment

- **Frontend URL:** http://localhost:3835 (Next.js 15 dev, hydrated; `main-app.js` → 200)
- **Backend URL:** http://localhost:8835 (FastAPI/uvicorn; restarted mid-run by port, health ok, seed_latest_date 2026-05-28, 158 symbols)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), exclusive Trendora tab, serialized against cross-project Tapeology tabs (:3650); tab-index shift handled (tab tracked by stable id)
- **As-of for travel:** Latest (2026-05-28) for the forward capture; 2025-11-28 for the J-18/J-20 historical cross-checks
- **Test Date:** 2026-06-03
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-16-evidence/`
- **Evidence integrity:** 10 screenshots, **all sha256-distinct** (iter-6 byte-identical-shot guard cleared); J-18 before(4/122)/after(2/122) pair is distinct; every "before/after" and re-point claim grounded on distinct shots + a live DOM/network assertion.

### Evidence files
- `UT-PREFLIGHT-stocks-hydrated.png` — hydration gate (122/122, Latest)
- `UT-J25-J27-factorlab-leadership.png` — Factor Lab default (decile + IC + by-regime)
- `UT-J30-factorlab-vcp-contraction.png` — Factor Lab re-pointed to `vcp_contraction` (J-25/J-30)
- `UT-J31-step1-2-research-vcp-synthesis.png` — Factor Lab + VCP event study + cross-link (J-31 step 1–2)
- `UT-J29-eventstudy-populated.png` — populated event study (pullback n=163, J-29)
- `UT-J31-step3-4-stocks-vcp-deeplink-4of122.png` — cross-link landing, 4/122 VCP (J-31 step 3–4 / J-18 "before")
- `UT-J05-J06-J20-stx-detail-latest.png` — STX detail at Latest (J-05/J-06/J-20 baseline)
- `UT-J20-stx-detail-historical-asof-marker.png` — STX detail at 2025-11-28, forward/as-of marker (J-20)
- `UT-J18-after-historical-vcp-2of122-filter-persists.png` — J-18 toggle: filter persists, re-points 2/122
- `UT-J28-stocks-pullback-deeplink-9of122.png` — second deep-link, 9/122 pullback (J-02/J-28)

---

## Notes for evaluator / auditor

- **J-31 conversion bar met (iter-4 lesson):** the defining multi-step cross-page travel was *actually* captured (not a single-surface render), with DOM/network assertions and distinct, sha256-deduped shots → **J-31 `partial → passing`** (expected board: **28/31**).
- **No source change required or made** — this was a verify-only re-run; the only edits are this report + evidence. `git diff -- apps/` remains empty (the developer's handoff confirmed the same). The one functional surprise (mid-test backend shutdown) was environmental and remediated by restart.
- **GOAL_ACHIEVED remains not autonomously reachable** — J-22 (~500 names), J-23 (intraday bars), J-24 (timeframe selector) stay externally Yahoo-429 data-walled (backend `symbol_count:158`, no 1D/1h/15m/5m selector on the chart — correctly absent). Not retried (pointless per iters 7/8). Expect CONTINUE→STALLED on the data-walled remainder absent an operator egress confirmation or a `docs/goal.md` scope edit.
