## Iteration 0 — goal-i_can_see_the_wealthy_future-iter-0

**Date:** 2026-05-29T14:47:24Z
**Verdict:** CONTINUE
**Depth dispatched:** lean
**Journey deltas:**
- Newly passing: none
- Newly failing: none in the regression sense — all 11 (J-01…J-11) recorded `failing` (not-yet-implemented) as the greenfield baseline; first time each journey is seen, no prior passing state
- Regressed: none
- Anti-goal violations: none (no product code written this iteration; `git diff HEAD` empty)

**Reasoning:** Greenfield baseline independently verified — empty `git diff HEAD`, no `apps/`, no
`config.yaml`, only untracked goal-mode artifacts. Dev was an intentional no-op (review PASS); browser-QA
SKIPPED all 11 (frontend/backend not running) with `precondition-check.txt` as positive proof the app and
every route are absent. No `coherence.md` (a no-op baseline has no diff to audit) and therefore no
COHERENCE-FAIL veto; the baseline's structural deliverable is `state/blueprint.md`, awaiting human
approval. All journeys failing is the expected, correct baseline outcome — not a regression — so CONTINUE.

**Next-step recommendation:** iter-1 foundation at **full** depth — FastAPI health + config loader
(`config.yaml`, the no-magic-numbers contract) + SQLModel/SQLite + provider abstraction + deterministic
SeedProvider + the keystone one-shot Stooq EOD ingest → committed frozen seed spanning a risk-on AND a
risk-off stretch + Next.js 15 shell with the blueprint sidebar nav. Carry forward the keystone risk: the
seed must be real EOD history (spanning both regimes) — fabricating data to force green journeys would
violate the *No fabricated data* anti-goal.

## Iteration 1 — goal-i_can_see_the_wealthy_future-iter-1

**Date:** 2026-05-29T17:04:13Z
**Verdict:** CONTINUE
**Depth dispatched:** full
**Journey deltas:**
- Newly passing: none (no journey targeted — planned infrastructure foundation)
- Newly failing: none (all 11 were already `failing` at the iter-0 baseline; no regression sense)
- Regressed: none (no journey was previously passing)
- Anti-goal violations: none (all four engaged anti-goals verified directly against the working tree)

**Reasoning:** The planned `(infra)` foundation iteration met its Definition of Done, verified
independently of the handoffs: real `apps/backend`+`apps/frontend`, root `config.yaml` single-source,
8-table SQLModel schema, `PriceProvider`/`SeedProvider`, a committed **real-EOD** seed (158 symbols,
2021-01-04→2026-05-28) whose keystone test passes on real SPY bars (risk-off 87d + risk-on 337d), and
`/api/health` ok offline. Backend 25/25 pytest pass; frontend builds; QA Chrome MCP evidence
(TC-12/14/15 screenshots exist on disk) shows the dark shell renders and the health badge connects
(provider=seed, seed 2026-05-28, 158 symbols) with an honest "Backend unavailable" failure state.
Grep confirmed no secrets and no order/execution path; `coherence.md` is COHERENCE-PASS (no canonical
value introduced, single shell, IA verbatim) — so no structural veto and no consolidation debt. Not
GOAL_ACHIEVED (all 11 journeys still `failing` by design); not REGRESSION (nothing was passing, no
critical anti-goal broken); not STALLED (first real spine built, clear next step). → CONTINUE.

**Discrepancy noted (resolved):** the dedicated browser-qa report recorded SKIPPED ("frontend not
running") while the QA mode-2 report recorded a PASS with Chrome MCP screenshots. The evidence dir
contains the 3 PNGs (timestamped after a documented `next dev` restart), so the shell *is* verified to
render+connect; the SKIP reflects an earlier window when the managed dev server had exited. No journey
status depends on it (none targeted), but it is logged as a lesson.

**Next-step recommendation:** iter-2 at **full** depth — indicator engine (MAs/RS/ATR%/breadth/
distance-from-52w) via an as-of accessor (date ≤ d, no-lookahead groundwork), Market Regime engine
(0–100 + 6 labels), and Sector/industry leadership scoring; populate the empty `industries` rows and
wire the scaffolded `regime`/`scoring` config sections. Lights up **J-04** + the regime/top-sectors
parts of **J-01**. This is the first live test of the *Single source of truth* anti-goal (each canonical
value computed once, served from one endpoint) — reconcile `app.engine.*` vs `app/<module>/` naming.

## Iteration 2 — goal-i_can_see_the_wealthy_future-iter-2

**Date:** 2026-05-29T19:10:15Z
**Verdict:** CONTINUE
**Depth dispatched:** full
**Journey deltas:**
- Newly passing: **J-04** (Sector / industry Leaderboard)
- Newly failing: none
- Regressed: none (nothing was previously passing; J-01 staying `failing` is by design — partial advance only)
- Anti-goal violations: none

**Reasoning:** The first canonical values shipped as planned and I verified J-04 directly from on-disk
Chrome MCP evidence (TC-15-sectors.png / -expanded.png), not a summary: 31 sector/industry ETFs ranked by
Sector Score (93.67→7.17 non-increasing), top row SOXX bucket A with RS-vs-SPY +45.49% / dist-52w -0.11% /
"Strong uptrend", SPY excluded as benchmark, per-row component breakdown — every J-04 acceptance clause met.
J-01 partially advanced (regime label+score 74.32, universe-relative breadth, data-as-of, Top Sectors that
read the same `/api/sectors` as the leaderboard) with honest "pending" placeholders for candidate counts +
Top Themes, so it correctly stays `failing`. Anti-goals all hold (I re-ran the greps): no order/execution
path, no secrets in authored source, `NA=None` short-history (no fabrication), `models.py` unchanged + no
snapshot persistence (immutability surface untouched, deferred to iter-5), and single-source verified — one
`to_bucket`/`score_regime`/`score_sectors`, dashboard Top Sectors == leaderboard, frontend recomputes
nothing. Coherence is **COHERENCE-WARN** (no FAIL) → no veto, no consolidation-only CONTINUE. One journey
newly passing + tractable work remaining → CONTINUE.

**Discrepancies noted (non-blocking):** (1) browser-qa flap recurred (2nd time) — dedicated browser-qa
report SKIPPED (managed `next dev` 3835 down at its check) while QA mode-2 PASSed with the 5 evidence PNGs
present on disk (mtimes 19:54–19:59, after the 19:33 dev handoff); reconciled by viewing the screenshots
myself, per the iter-1 lesson. (2) No audit handoff was produced despite full depth; evaluation did not
depend on it (verified from git diff + greps + screenshots + coherence.md). Both flagged for the orchestrator.

**Next-step recommendation:** iter-3 at **full** depth — per-stock Leadership/Entry Quality/Risk scores
(explainable, A–E via the existing `to_bucket`), theme scoring, the Stock + Theme Leaderboards (**J-02**,
**J-03**), score consistency across pages (**J-06** — the harder live test of *Single source of truth*), and
real candidate counts + Top Themes to finish and flip **J-01** green. Fold in the cheap consolidation
tidy-ups now: amend the blueprint Data Contract so "market breadth %" canonical compute =
`app.engine.regime:score_regime` / serve `/api/dashboard` (iter-5 `summarize_run` must READ, not recompute);
register net-new-high/low under the regime row; and promote the shared score→label-via-edges helper out of
`regime.py` so `sectors.py` stops importing the private `_label_for` (review NOTE).

## Iteration 3 — goal-i_can_see_the_wealthy_future-iter-3

**Date:** 2026-05-29T21:48:48Z
**Verdict:** CONTINUE
**Depth dispatched:** full
**Journey deltas:**
- Newly passing: **J-01** (dashboard completed), **J-02** (Stock Leaderboard + filters), **J-03** (Theme Leaderboard), **J-06** (score consistency / single-source) — four in one iteration
- Newly failing: none
- Regressed: none (J-04 held green through the `labels.py` extraction)
- Anti-goal violations: none

**Reasoning:** The per-entity scoring spine landed as planned and I verified all five claimed-passing
journeys directly from the on-disk Chrome MCP PNGs (not summaries), because the browser-qa SKIP-vs-PASS
flap recurred a **third** time. TC-13 dashboard: regime Risk-on 74.32, candidate counts 0/8/1 (each a
number), 5 scored Top Sectors + 5 scored Top Themes, breadth 65.57% universe-relative, as-of 2026-05-28
(**J-01** ok). TC-10: 122 ranked rows w/ 3 bucketed scores + setup + reason; Health Care filter -> 7/122;
Actionable -> honest 0/122 empty-state (acceptance allows it) (**J-02** ok). TC-12: 11 themes non-increasing
A/100->E/3, top theme +28.38%/+61.22%/100% breadth/Strong uptrend, expandable members+breakdown (**J-03**
ok). TC-11: NVDA detail L E/47.48 EQ D/66.24 R E/33.79 — byte-identical to the list row (QA TC-02) and
guaranteed by construction (`/api/stocks/{ticker}` filters the same `score_stocks` result; coherence Part
A + list==detail unit guard) (**J-06** ok). TC-14: sectors ranked unchanged (**J-04** held). Anti-goals
all hold: `models.py` git-clean (immutability deferred), COHERENCE-PASS (both iter-2 WARN notes closed),
Risk-off->zero-Actionable exhaustively unit-tested, no-magic CALC_FILES extended, NA shown not fabricated,
no order path, no secrets. Four journeys newly passing + tractable work remaining -> CONTINUE. Not
GOAL_ACHIEVED: six journeys (J-05, J-07–J-11) remain unbuilt by design.

**Process gaps noted (non-blocking, for the orchestrator):** (1) **Audit handoff missing again** (3rd
time — also iter-2) despite full depth; evaluation did not depend on it. (2) **Browser-qa SKIP-vs-PASS
flap recurred a 3rd time** — dedicated browser-qa SKIPPED (frontend HTTP 000 on :3835 & :3836 at its
probe) while QA mode-2 started its own `next dev`, ran all 5 cases, and saved 9 PNGs (mtimes 22:07–22:35).
The iter-3 spec explicitly asked the orchestrator to harden `next dev` supervision; it did not take.
Reconciled by viewing the PNGs directly.

**Next-step recommendation:** iter-4 at **full** depth — **J-05** (full Stock Detail): price + MA candle
chart, volume series, theme-membership chips, and a **computed** (single-source, not FE-derived)
invalidation note ("below 50-DMA at $X"), built on the now-canonical three-score record and
`/api/stocks/{ticker}`. Needs a charting library (Lightweight-Charts/Recharts) + a backend bars/MA series
endpoint -> net-new surface across both tiers. Orchestrator should also fix the two recurring process gaps
(emit the audit handoff; keep `next dev` up for the dedicated browser-qa step).

## Iteration 4 — goal-i_can_see_the_wealthy_future-iter-4

**Date:** 2026-05-30T03:30:00Z
**Verdict:** CONTINUE
**Depth dispatched:** full
**Journey deltas:**
- Newly passing: **J-05** (full Stock Detail — populated price+MA chart + volume + theme chips + concrete invalidation note + 3 explainable score cards), reconciled from the on-disk QA PNGs I viewed directly
- Newly failing: none
- Regressed: none (J-01–J-04 hold; **J-06 re-proven at the contract level this iter** via unit list==detail guard incl. the new fields + coherence byte-identical)
- Anti-goal violations: none

**Reasoning:** iter-4 delivered J-05. Verified directly from on-disk QA evidence (viewed, not summarized):
`TC-10-stock-detail-NVDA.png` shows the completed `/stocks/NVDA` page — a POPULATED candlestick chart
("Price & moving averages") with MA overlay lines + a legend + a volume histogram; theme chips
(AI Data Centre / Semiconductors / Megacap Leaders); a concrete INVALIDATION note ("Invalid below the
50-DMA at $198.73" per QA + backend live smoke); and the three score cards (Leadership E/47.48, Entry
Quality D/66.24, Risk E/33.79) each with >=3 named components. `TC-11-unknown-ticker.png` shows the
honest "Unknown ticker" state (no chart, no fabrication). Backend: new canonical
`GET /api/stocks/{ticker}/bars` (no-lookahead `bars_asof`, `ma` keyed by every
`config.indicators.ma_periods` via `sma_series`, 404/503 honest); `invalidation`+`themes` computed once
in `score_stocks` and carried on the SHARED row so list==detail stays byte-identical (J-06).
Single-source proven end-to-end (`invalidation.level` 198.734 == `ma["50"][-1]`). 126/126 pytest,
COHERENCE-PASS, frontend builds; `models.py` git-diff empty, no order path, no secrets (re-verified by my
own `git diff`/greps). Not GOAL_ACHIEVED (J-07–J-11 unbuilt by design); not REGRESSION; not STALLED ->
**CONTINUE**.

**Evaluation-integrity note (disclosure):** an earlier pass of this evaluation ran during a transient
tool-output outage in which calls were *queued* (not failed) and a Read of the two evidence PNGs
spuriously returned "files do not exist" — which nearly drove a wrong `partial` cap on J-05. When the
harness recovered the calls flushed, confirming the PNGs are present (`ls`/Glob) and the chart is painted
(viewed directly). This entry, eval.md, journey-history.json and lessons.md all reflect the corrected
finding (J-05 passing). The demo-narrator's Playwright soft-notes ("invalidation"/"Unknown ticker" text
not found; click timeouts) are capture-timing artifacts of the non-gating showcase runner (frames at
00:13, after QA's 00:07 evidence), not defects.

**Process gaps (non-blocking, recurring):** (1) Dedicated browser-qa SKIP/PASS flap recurred a **4th**
time (SKIPPED on HTTP 000), but QA mode-2 self-healed and **persisted** the evidence — so no vacuum this
time; the structural fix (browser-qa must own/self-heal its frontend) is still owed. (2) **Audit handoff
missing a 4th time** at full depth (only dev + frontend handoffs exist), despite iter-4's explicit DoD.

**Next-step recommendation:** iter-5 at **full** depth — J-07 + J-08: scanner snapshots + Scanner Runs
list/detail with append-only immutability (`models.py` gains `scanner_run` + result rows — first real
test of the Snapshots-immutable critical anti-goal; seed a Risk-Off historical run + >=1 earlier run to
light up J-07 as a journey and the no-lookahead walk-forward groundwork). Fold in the two recurring
fixes: make the dedicated browser-qa own/self-heal its frontend (end the 4x flap), and emit the audit
handoff.

## Iteration 5 — goal-i_can_see_the_wealthy_future-iter-5

**Date:** 2026-05-30T05:30:00Z
**Verdict:** CONTINUE
**Depth dispatched:** full
**Journey deltas:**
- Newly passing: **J-07** (Risk-Off run → zero Actionable), **J-08** (immutable as-of run history; older differs from latest)
- Newly failing: none
- Regressed: none (J-01–J-06 held green; J-01–J-05 freshly re-shot this iter rather than carried; J-06 strengthened — now also proven across the NEW stored snapshot path)
- Anti-goal violations: none (all four criticals exercised this iter — immutable / no-lookahead / single-source / risk-off-gates-actionable — verified directly)

**Reasoning:** The immutable snapshot persistence spine landed cleanly and I verified both target
journeys from on-disk evidence (not summaries), because the browser-qa SKIP-vs-PASS flap recurred a
**5th** time. TC-11-scanner-runs-list.png (viewed): 3 dated runs DESC — 2026-05-28 Risk-on 74.32
(Actionable 0/Breakout 8/Pullback 1), 2025-04-04 Risk-off 6.30 (Actionable 0), 2022-10-07 Risk-off
8.34 (Actionable 0) — J-07's gate visible at the aggregate and J-08's ≥2-dated-runs met. TC-13-older
(regime 8.34) vs TC-13-latest (regime 74.32) are visibly different stored snapshots (J-08). The four
critical anti-goals are unit-proven AND I confirmed them in source: `scanner.py` calls each canonical
engine once and reads breadth/counts from `score_regime`/`summarize_candidates` (no 2nd formula —
the headline single-source risk, avoided), stores faithful `record_json` copies, and uses only INSERTs
(no UPDATE/merge/delete — immutability); `runs.py:64` serves STORED rows only, never the live engine
for a historical date (the exact bug J-08 guards). `git diff` confirms the existing live endpoints are
untouched (main.py only ADDS runs.router) so J-01–J-06 cannot regress; 143/143 pytest, frontend builds
all 10 routes, coherence.md = COHERENCE-PASS (no veto). Greps for order/execution path and secrets are
empty. Two journeys newly passing + tractable work remaining → CONTINUE. Not GOAL_ACHIEVED: J-09, J-10,
J-11 unbuilt by design.

**Process gaps (non-blocking, now chronic):** (1) **Audit handoff missing a 5th consecutive full-depth
iter** — `reports/audits/` does not even exist, despite iter-5 putting it in the spec's Definition of
Done. A DoD/spec-level ask has now demonstrably failed to fix this; the fix must move into the runner
script, not the spec. (2) **Browser-qa SKIP/PASS flap recurred a 5th time** (dedicated report 0/19
SKIPPED on HTTP 000; QA mode-2 self-healed the frontend on :3836 and persisted all 10 evidence PNGs).
Reconciled from on-disk evidence + unit/API proofs per the standing lesson. Neither gap affected the
verdict — evaluation rested on persisted evidence, unit/API tests, and direct source reads.

**Next-step recommendation:** iter-6 at **full** depth — J-09 + J-10: the walk-forward forward-testing
engine + System Health page. Add a SEPARATE append-only `forward_returns` table keyed to
`(run_id, ticker, horizon)` (never mutating the snapshot built this iter); replay as-of past dates with
strict no-lookahead and measure realized 1/5/10/20/60-day forward returns from bars with date > D
(unit-prove the boundary); aggregate forward return by bucket/setup/regime + excess vs SPY/QQQ/sector +
a random-same-sector control group, with `n` and the survivorship-bias label surfaced. Seed ≥1 mid-
history Risk-on run so the forward-return sample is meaningful. Orchestrator must finally (1) emit the
audit handoff from the runner and (2) make the dedicated browser-qa own/self-heal its frontend.

## Iteration 6 — goal-i_can_see_the_wealthy_future-iter-6

**Date:** 2026-05-30T05:45:00Z
**Verdict:** CONTINUE
**Depth dispatched:** full
**Journey deltas:**
- Newly passing: **J-09** (System Health forward-tested evidence), **J-10** (control-group honesty)
- Newly failing: none
- Regressed: none (J-01–J-08 all held; existing canonical endpoints + engines byte-identical untouched vs HEAD; J-08 freshly re-shot, J-07 live-confirmed both Risk-off runs still 0 Actionable)
- Anti-goal violations: none (all four criticals — no-lookahead forward boundary / immutable append-only / single-source verbatim / Risk-off-gates-Actionable — verified directly in source + unit-proven)

**Reasoning:** The keystone "prove its own usefulness" capability landed cleanly and I verified both
target journeys from on-disk evidence (not summaries), because the dedicated browser-qa SKIPPED a **6th**
consecutive time on an HTTP-000 flap. TC-14-system-health-j09.png (viewed): populated /system-health —
by-bucket A-E (A +6.00% n=24⚠ … E +2.05% n=772), Excess vs SPY/QQQ, by-setup, by-regime with BOTH
Risk-on (+2.63% n=732) and Risk-off (+10.55% n=242), each cell with n, survivorship banner (J-09).
TC-15-horizon-change-5d.png (viewed): selector re-fetches and changes figures (A +6.00%@20d → −1.09%@5d)
matching the API payload — re-format only. The control-group panel shows all 5 cohorts numeric+labelled+n
(Top-ranked +3.02% n=200, Random same-sector +1.52% n=285, SPY +1.52% n=10, QQQ +1.99% n=10, Sector ETF
+1.43% n=65) (J-10). Source-verified the three disciplines directly: `bars_after` strict date>D vs
`close_on`/`bars_asof` date≤D (disjoint partition, the no-lookahead proof); `_backfill` INSERT-only into
the SEPARATE append-only `forward_returns` table (models.py only APPENDS it) + idempotent; aggregates READ
`leadership_bucket`/`setup_status`/`sector`/`rank`/`regime_label` verbatim (no `to_bucket`/`score_*`
import). config.yaml holds every tunable (no magic numbers); control-group RNG re-seeded from
`control_group.seed`. 168/168 pytest (25 new), COHERENCE-PASS, frontend builds; greps for order-path and
secrets empty; `git diff HEAD` shows dashboard/stocks/sectors/themes/runs + scoring/regime/buckets/setups/
scanner all untouched (J-01–J-08 cannot regress). Two journeys newly passing + one tractable remaining →
CONTINUE. Not GOAL_ACHIEVED: J-11 (Watchlist) unbuilt by design.

**Process gaps (non-blocking, chronic — explicitly NON-gating runner-script scope per the iter-6 spec):**
(1) **Dedicated browser-qa SKIPPED a 6th consecutive time** (0/15, HTTP-000 on :3836); QA mode-2
self-healed its own frontend on :3836, ran 19/19 functional TCs, and persisted 4 evidence PNGs (note:
TC-14 == TC-16 by md5 — one full-page capture saved under two names; J-10 has no dedicated focused shot,
but the panel is present in the full-page image). (2) **Audit handoff missing a 6th consecutive full-depth
iter** — `reports/audits/` still does not exist. Neither affected the verdict (reconciled from persisted
PNGs + 25 unit/API proofs + direct source reads + git-diff, per the standing lesson and the spec's
explicit evaluator guidance). (3) Review NOTE: unused `horizon` param in `_control_groups()`
(forward_testing.py:300) — cosmetic, non-functional.

**Next-step recommendation:** iter-7 at **full** depth — **J-11 (Watchlist with persistence)**, the last
Must-have journey. Persisted `watchlist` table + POST/GET/DELETE `/api/watchlist` (the product's first
user-write/mutation surface); each entry carries date-added, free-text reason, current
Leadership/Entry/Risk + setup (**READ canonical, single-source — never recomputed**), price-since-added,
and an invalidation level; **MUST survive a backend restart** (DB-backed — the J-11 acceptance crux,
test add→restart→present). Graduate the `/watchlist` stub (sidebar link already present, no nav change).
Pair with a full 11-journey regression sweep + full-product coherence so the next evaluation can
legitimately reach GOAL_ACHIEVED. Runner owner should finally (a) make browser-qa own/await/self-heal its
frontend — ideally before this goal-completing iter so GOAL_ACHIEVED rests on a clean live browser sweep
— and (b) emit the audit handoff.

## Iteration 7 — goal-i_can_see_the_wealthy_future-iter-7

**Date:** 2026-05-30T06:29:04Z
**Verdict:** GOAL_ACHIEVED
**Depth dispatched:** full
**Journey deltas:**
- Newly passing: **J-11** (Watchlist with persistence) — the 11th and last Must-have journey
- Newly failing: none
- Regressed: none (J-01–J-10 all held; purely-additive diff — no engine or live-endpoint file touched per `git diff HEAD`; live backend serves their endpoints; all nav links render)
- Anti-goal violations: none (all four criticals + order-path/secrets fences re-verified directly in source and at runtime)

**Reasoning:** J-11 landed cleanly and I verified it to an exceptional standard — because the dedicated
browser-qa SKIPPED a **7th** consecutive time (HTTP-000) and QA captured only the Chrome
"ERR_CONNECTION_REFUSED" error page (the two pre-existing TC-14 evidence PNGs are md5-identical error shots,
not real UI proof), so there was NO carried-forward screenshot to reconcile from this time. I therefore
**booted the services myself and produced the missing evidence directly**: (1) a LIVE Chrome render of
`/watchlist` showing the ANET row with EVERY acceptance field (Ticker→/stocks/ANET, Added 2026-05-30, reason
verbatim, Leadership E/46.61, Entry E/57.69, Risk E/39.62, Setup Avoid, Since added +0.00% honest-frozen-seed,
Invalidation "Invalid below the 50-DMA at $148.38", Remove; header "Research-only · decision support · no
orders") — 4 distinct md5 PNGs in the iter-7 evidence dir; (2) the restart-persistence crux proven
**end-to-end LIVE** — I killed the backend (PID 340389) and rebooted it **twice**, ANET survived both, and the
row is physically in on-disk `apps/backend/data/trendora.db`, plus the file-backed unit test passes;
(3) single-source byte-equality of `/api/watchlist` vs `/api/stocks` (all 6 canonical fields) LIVE + unit;
(4) the full live journey Add-via-form → row → Remove → empty → re-Add → row; (5) live error paths
(unknown→404, duplicate→409, delete-missing→404); (6) 11/11 new watchlist unit tests pass under my own run
(179-suite green per QA). Coherence is **COHERENCE-PASS** (first write surface correctly READS the canonical
`score_stocks` row, stores no score), so no structural veto. `models.py` only APPENDS the user-mutable
`Watchlist` table — no snapshot row is ever touched (unit-proven), so the Snapshots-immutable critical
anti-goal and J-07/J-08 hold. All 11 journeys passing + no critical anti-goal + COHERENCE-PASS →
**GOAL_ACHIEVED**.

**Process gaps (non-blocking, chronic — runner-script scope, NOT product):** (1) **Dedicated browser-qa
SKIPPED a 7th consecutive time.** This iter surfaced a *second, concrete* root cause beyond "frontend down":
a **CORS_ORIGINS mismatch** — a backend launched without `CORS_ORIGINS` defaults to `http://localhost:3000`
and silently blocks the `:3835`/`:3836` frontend, so even a *running* frontend renders the honest "Backend
unavailable" card (I reproduced this, then fixed it by relaunching the backend with
`CORS_ORIGINS=http://localhost:3835`). The durable fix: the runner must set `CORS_ORIGINS` to the real
frontend port AND keep the frontend up. (2) **Audit handoff missing a 7th consecutive full-depth iter** —
`reports/audits/` still does not exist. Neither affected the verdict (I produced the live evidence myself).

**Next-step recommendation:** **Halt — goal achieved.** All 11 Must-have journeys pass, no critical anti-goal
is violated, coherence passes. If the user resumes for the explicitly-deferred nice-to-haves (config-editor
view #14, historical per-stock score charts #15), a single **lean** iteration suffices — neither is a
Must-have. Before any further browser-gated work, the runner owner should finally (a) make browser-qa
own/await/self-heal its frontend AND set `CORS_ORIGINS` to the frontend port, and (b) emit the audit handoff.

## Iteration 8 — goal-i_can_see_the_wealthy_future-iter-8

**Date:** 2026-05-31T00:54:30Z
**Verdict:** CONTINUE
**Depth dispatched:** full
**Journey deltas:**
- Newly passing: **J-13** (global as-of date switcher), **J-15** (snapshot-served reads) — the first two of the five newly-added Must-haves
- Newly failing: none (J-12, J-14, J-16 enter tracking as `failing`/unbuilt by design — they were added to goal.md in commit `ed7712b` after iter-7 and are explicitly OUT OF SCOPE this iter; not a regression sense)
- Regressed: none (J-01–J-11 all held green through the read-path re-point — the iteration's real risk)
- Anti-goal violations: none (all six engaged criticals — no-lookahead / immutable / single-source / **No recompute in the read path** / on-demand-immutable / Risk-Off-gates-Actionable — verified directly in source + unit-proven)

**Reasoning:** The keystone read-path consolidation landed cleanly: the five live read endpoints
(`/api/dashboard`, `/api/stocks`, `/api/stocks/{ticker}`, `/api/sectors`, `/api/themes`) + `/bars` +
watchlist now serve canonical values from the persisted IMMUTABLE snapshot for a resolved as-of date
(computed once, then read from storage), and a global top-bar as-of switcher time-travels the whole
dashboard. The dedicated browser-qa SKIPPED an **8th** consecutive time (HTTP-000); QA mode-2
self-healed (backend :8835 with `CORS_ORIGINS`, frontend :3835) and persisted 5 distinct PNGs, which
I reconciled directly. **J-13** verified from the PNGs I viewed: the switcher genuinely re-points
stored snapshots (dashboard Risk-on 74.32 → Risk-off 6.30; breadth 65.57% → 0.82%; leadership semis
SOXX/WGMI/SMH → defensives XLP/XLU/XLF; stocks MU/ARM/MRVL → KTOS/NOC/PLTR), shows the amber "Viewing
as-of 2025-04-04 (historical)" indicator + per-page "Data as-of 2025-04-04", and reset-to-latest is
md5-identical (`f353ee88…`) to the latest view (clean restore) — the defensive rotation on a Risk-off
day is internally consistent, a real historical snapshot not a fabrication. **J-15** verified from
source + test: the keystone `test_repointed_handlers_serve_persisted_date_without_recompute`
monkeypatches the four canonical engines to RAISE and asserts all four handlers still serve a
persisted date (proving storage-read, never recompute — stronger than value-equality); warm API
20–100ms. The read-path regression risk to J-01–J-11 was de-risked because the `scanner.py` diff only
APPENDS the resolver (`run_scan` untouched → create-once/immutable/no-lookahead inherited; iter-5
faithful-equality makes latest payloads byte-identical to the old on-request compute) and `models.py`
is git-clean. J-06 strengthened (list==detail==watchlist from the same stored row), J-07 re-proven on
a historical view (2025-04-04 Risk-off → Actionable 0). 196/196 pytest, COHERENCE-PASS, frontend
builds 10 routes; order-path/secrets greps empty. Two target journeys newly passing + tractable work
remaining → CONTINUE. Not GOAL_ACHIEVED: J-12, J-14, J-16 unbuilt by design (13/16 Must-haves pass).

**Process gaps (non-blocking, chronic — runner-script scope, NOT product; spec-level asks have proven
ineffective across iters 3–8):** (1) **Dedicated browser-qa SKIPPED an 8th consecutive time** (0/15,
HTTP-000 — and it probed the wrong health path `GET /health` rather than `/api/health`, plus the
runner-managed `next dev` died mid-test). QA mode-2 self-healed and persisted 5 distinct PNGs; I
reconciled from them + source + unit proofs per the standing lesson and the iter-8 spec's explicit
evaluator guidance. (2) **Audit handoff missing an 8th consecutive full-depth iter** — `reports/audits/`
still does not exist. Neither affected the verdict. (3) Minor doc nit (review + QA NOTE): the dev
handoff says the resolver suite is "12 passed" but `test_asof_resolver.py` has **10** tests (10 pass);
harmless count discrepancy, no code impact.

**Next-step recommendation:** **iter-9 at full depth — J-14 (Backtest / Time-Machine + per-date
forward-test scorecard).** Builds directly on this iter's `resolve_run` as-of resolver + the iter-6
forward-testing engine: pick a historical date, render its as-of scan from the canonical snapshot, and
show a per-date scorecard (realized 1/5/10/20/60-day returns, excess vs SPY/QQQ/sector, random
same-sector control) computed only from seed bars after D (no-lookahead), with n and partial/NA
horizons shown honestly. Adds a `/backtest` nav route → needs `blueprint.reapproval-requested`.
Unit-prove the post-D forward boundary on the per-date scorecard. Then J-16 (VCP), then J-12 (glossary
incl. the VCP entry) finish the new round. Runner owner should finally (a) make browser-qa
own/await/self-heal its frontend AND probe `/api/health` with `CORS_ORIGINS` set to the frontend port,
and (b) emit the audit handoff from the runner script.

## Iteration 9 — goal-i_can_see_the_wealthy_future-iter-9

**Date:** 2026-05-31T02:39:03Z
**Verdict:** CONTINUE
**Depth dispatched:** full
**Journey deltas:**
- Newly passing: none
- Newly failing: none
- Regressed: none
- Anti-goal violations: none (no apps/ code changed, so none could be introduced)

**Reasoning:** iter-9 produced **no product code — the developer step never executed (a silent pipeline
no-op).** Only the goal-decomposer (iter-9 J-14 spec + additive blueprint Backtest IA/Data-Contract rows +
`blueprint.reapproval-requested`) and the coherence-auditor (COHERENCE-PASS, with an explicit "implementation
absent — blueprint is ahead of the code" advisory) ran; developer / reviewer / QA / audit / browser-QA were
all skipped. I confirmed the absence from multiple independent sources, not from a missing handoff alone:
`git status` shows zero `apps/` diff and HEAD still at `acc00d5` (iter-8); `git stash list` empty and a
single worktree (code is not hidden elsewhere); `apps/backend/app/api/backtest.py`,
`apps/frontend/app/backtest/page.tsx`, and `apps/backend/tests/test_backtest*` are all absent;
`forward_testing.py`'s def list ends at the iter-6 `compute_forward_aggregates` (no `compute_run_scorecard`
/ `backfill_run_forward_returns` / `_insert_run_forward_returns`); `sidebar.tsx`/`lib/api.ts` have no
backtest entry; `grep -rln "backtest" apps/` is empty; and `status.json` is frozen at
`current_step="starting"`, `changed_files=[]`, `tests_run=false`. So **J-14 was not built** and has no
evidence (no QA, no screenshots, no tests). Because no `apps/` file changed, the 13 journeys green at iter-8
are byte-identical to the running `acc00d5` code and cannot have regressed (carried passing; `last_verified`
stays iter-8 — not behaviourally re-tested). 13/16 Must-haves pass, unchanged. Coherence is **COHERENCE-PASS**
(no veto). This is **CONTINUE** — not GOAL_ACHIEVED (J-12/J-14/J-16 failing), not REGRESSION (nothing broke),
not STALLED (the next step is fully specified and tractable — recent iters made real progress; a single
no-op is an execution miss, and the STALLED remedy "edit goal.md" would be wrong since the goal + spec are
sound), not ESCALATE (already full depth; the issue is an unexecuted dev step, not lean→full promotion).

**Root cause flagged for the runner owner (PRIMARY this iter):** a full-depth dispatch reached the
goal-evaluator with the dev/review/QA/audit/browser-QA steps entirely un-run and `status.json` stuck at
`current_step="starting"`, `changed_files=[]`. The pipeline must not be able to advance past coherence to
the evaluator when the developer step has produced nothing. (The two chronic non-gating debts persist —
dedicated browser-qa SKIPped 8+ iters; audit handoff / `reports/audits/` missing 8+ full-depth iters — but
they are secondary to the dev step not running at all this time.)

**Next-step recommendation:** **iter-10 (or a re-dispatch of iter-9) at full depth — IMPLEMENT J-14 from the
existing, already-coherent iter-9 spec.** No re-planning needed: `docs/phases/goal-...-iter-9.md` is correct,
the blueprint already carries the Backtest IA + Data-Contract rows, and `blueprint.reapproval-requested` is
already written — proceed straight to the developer step and run the full dev→review→QA→audit→browser-QA
chain. Build: the shared `_insert_run_forward_returns` refactor (iter-6 tests stay byte-green) +
`backfill_run_forward_returns` (create-once, INSERT-only) + `compute_run_scorecard` (reads stored
forward_returns + stored scanner_results verbatim) + `GET /api/backtest` via `snapshot_serving.resolved_run`;
`/backtest` page (date picker + as-of scan summary reusing the existing fetchDashboard/Sectors/Themes/Stocks
with `?as_of=D` — no second source — + the per-horizon scorecard) + the Backtest sidebar entry + `fetchBacktest`;
and the spec's keystone patch-to-raise read-path test, no-lookahead post-D boundary, honest partial/NA, and
create-once/immutable tests. A clean J-14 → 14/16 Must-haves pass; J-16 (VCP) then J-12 (glossary) finish the round.

## Iteration 10 — goal-i_can_see_the_wealthy_future-iter-10

**Date:** 2026-05-31T09:10:00Z
**Verdict:** CONTINUE
**Depth dispatched:** full
**Journey deltas:**
- Newly passing: **J-14** (Backtest / Time-Machine workspace + per-date forward-test scorecard) — the iter-9 silent dev no-op is fixed; J-14 actually implemented this iter
- Newly failing: none
- Regressed: none (J-13 global switcher + J-09/J-10 System Health re-shot LIVE and unchanged; the forward_testing refactor is behaviour-preserving; models.py + the 5 canonical read endpoints byte-identical)
- Anti-goal violations: none (all engaged criticals — no-lookahead post-D boundary / immutable INSERT-only / single-source + No-recompute-in-read-path / on-demand-create-once / honest-partial-NA / no-magic-numbers / no-order-path / no-secrets — verified in source + unit-proven + live)

**Reasoning:** iter-10 re-executed the iter-9 J-14 plan and landed it cleanly. I verified to gold
standard **despite a 9th consecutive dedicated browser-qa SKIP and — worse than iters 4–8 — ZERO QA
evidence PNGs** (the evidence dir did not even exist; QA mode-2 did not self-heal this time), so there
was nothing to reconcile from. I therefore produced the evidence myself: (1) ran the new suite —
**17/17 new J-14 tests PASS in my own official `.venv` pytest (exit 0, 229s)**, incl. the KEYSTONE
patch-`forward_return`-AND-`score_*`-to-raise (read path recomputes nothing — proven by the negative),
no-lookahead post-D boundary, create-once idempotent, honest partial/NA, group-by-stored-rank (single
source), and cross-check vs `compute_forward_aggregates`; (2) booted uvicorn :8835 on the seed and hit
the live API — latest = honest all-NA (`is_latest=true`, every `mean_return:null`/`n:0`), `?as_of=2022-10-07`
(full window) = NUMERIC cohort returns (n=20=`top_n`) + excess vs SPY/QQQ/sector + random-same-sector
control n=31 + all 5 control cohorts, invalid dates → 400/400/422; (3) drove Chrome to `next start`
:3835 and rendered BOTH scorecard states — the rendered cells equal the API payload **byte-for-byte,
re-formatted to %** (FE recomputes nothing), low-sample `n<30` ⚠, survivorship banner + "Viewing as-of
D" indicator, Backtest reachable in 1 click, honest "no numbers are fabricated" empty state on the
all-NA date; **no console errors**. Source-verified `backtest.py` + the 3 new `forward_testing` funcs
(`_insert_run_forward_returns` extract-method refactor → ONE forward-return formula;
`backfill_run_forward_returns` create-once INSERT-only; `compute_run_scorecard` reads stored rows +
reuses `_control_groups`) + `page.tsx` (scan summary reuses the existing canonical `fetch*` with
`?as_of=D` — no second source) + `sidebar.tsx` + `lib/api.ts`. `models.py` git-clean; order-path/secrets
greps empty. Frontend production build clean (11 routes incl `/backtest`). Coherence **COHERENCE-PASS**
(both refactors REDUCE duplication). 14/16 Must-haves pass; J-12 + J-16 unbuilt by design → CONTINUE.

**Process gaps (non-blocking, chronic — runner-script scope, NOT product/spec; ineffective via spec text
across iters 3–10):** (1) **Dedicated browser-qa SKIPped a 9th consecutive time** (0/15, frontend
reported down at `:3835`) AND — unlike iters 4–8 — produced **no evidence PNGs at all** (no QA mode-2
self-heal this run); I booted both services and captured the 4 evidence PNGs myself. (2) **Audit handoff
missing a 9th consecutive full-depth iter** (`reports/audits/` + `docs/handoffs/...-audit.md` absent;
`status.json` `current_step` stops at `qa_complete`). Neither affected the verdict (rested on my own test
run + live API + live browser render + source reads). (3) Minor review NOTE (non-functional):
`backtest.py:27` imports the private `_latest_stored_run_date` from `app.engine.scanner` — the only API
module reaching a private engine symbol; optionally expose a public helper.

**Next-step recommendation:** **iter-11 at full depth — J-16 (VCP detection).** A config-driven
price+volume VCP detector computed once per run with date ≤ D (no-lookahead), riding the immutable
snapshot row as a SEPARATE flag (NOT in the setup-status enum; never Actionable on its own — *critical*),
read identically on leaderboard + detail, with a `/stocks` VCP filter, a badge (reason + pivot/invalidation),
and a System Health VCP-vs-non-VCP forward-return breakdown (n; NA below `min_sample`). Then **J-12
(config-backed glossary / `/methodology`)** LAST so it documents the VCP entry (adds a nav route → needs
`blueprint.reapproval-requested`). Clean J-16 → 15/16, then J-12 → 16/16 and a legitimate GOAL_ACHIEVED
check. Runner owner should finally (a) make browser-qa own/await/self-heal its frontend with `CORS_ORIGINS`
set to the frontend port, and (b) emit the audit handoff.
