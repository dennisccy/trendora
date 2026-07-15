# Goal Iteration 38 — Watchlist concentration X-ray (J-23 / B-204)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** mcp-loop
- **Iteration:** 38
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-23
- **Required-still-passing journeys:** J-01, J-02, J-03, J-05, J-10, J-13, J-20
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

The `/watchlist` page gains a descriptive **concentration X-ray** — a pairwise return-correlation matrix, deterministic correlation-threshold clusters, sector/theme concentration bars, a shared-setup count, and a headline **"effective independent bets ≈ N.N (over the last W trading days)"** with its window stated — so the owner can see how concentrated their list really is, with honest NA for thin-history names and **zero advice or proven-language**.

## BACKGROUND

iter-37 (lean deterministic-replay closeout) ended CONTINUE and explicitly recommended **iter-38 = FULL J-23** (backlog **B-204**, watchlist concentration X-ray) as the first of the three remaining risk-analytics journeys (J-23 → J-24 → J-25). iter-37 coherence was **COHERENCE-PASS**, so no consolidation is owed. Target selection follows the rubric: no journey is `regressed`, the last coherence was not FAIL, and among the three unbuilt journeys J-23 has a self-contained binding card (B-204 `Depends on: none`) and is the single risky surface this iteration ships (rule 5 — never two risky journeys). Depth is **full** because the iteration crosses backend + frontend, introduces a NEW served value that needs the audit / ux-regression / closure guards, and requires new non-browser tests (the ENB fixture) beyond a browser smoke — and the prior evaluator explicitly mandated full for J-23.

The binding B-204 card names the **UI-recompute** dominant failure mode and a specific single-source trap: the ENB helper must be **one** shared module, the "same ENB formula as B-104 (`ENB = (Σλ)²/Σλ² over the correlation matrix's eigenvalues`)". B-104 (the *evidence correlation audit* the journey text references) is a Q3 card that is **not built** — no ENB helper exists anywhere in the codebase today. Per the B-204 trap ("share B-104's helper — build whichever card lands first, reuse in the second"), J-23 lands first and **creates the one canonical ENB/correlation helper**; B-104 will import it later. (Logged to `assumptions.md`.)

## IN SCOPE

### Backend
- [ ] Add the **single canonical ENB/correlation helper** — one pure module (proposed `app.engine.concentration`) exposing `effective_number_of_bets(corr_matrix)` = `(Σλ)²/Σλ²` over the correlation-matrix eigenvalues (`numpy.linalg.eigvalsh`) and a pairwise `correlation_matrix(series_by_name)` (Pearson over aligned daily returns; undefined/zero-variance pair → honest NA, never a fabricated 0). This is the ONE ENB implementation — the future B-104 evidence correlation audit imports the SAME helper. Do NOT write a second ENB.
- [ ] Add a PURE X-ray composer `app.engine.watchlist_xray:build_xray_payload(session, cfg, tickers, asof)` that computes, over the watchlist tickers only: the pairwise return-correlation matrix over the trailing `watchlist.xray.corr_window_days` window (return series from bounded per-symbol `app.engine.prices:bars_asof_window` reads — bars ≤ as-of; NEVER a whole-table ORM load), a deterministic correlation-threshold cluster grouping (connected components at `watchlist.xray.cluster_threshold`; no ML), the ENB (via the shared helper over the honest sub-matrix), sector + theme concentration (read from the SAME canonical snapshot rows `GET /api/stocks` serves via `snapshot_serving:filtered_stock_rows`; null `sector` → "Unassigned" bucket via the existing sector-label helper), and a count of names sharing the same detected setup. Honest NA for any member with `< watchlist.xray.min_overlap_days` overlapping history.
- [ ] Serve the payload as an ADDITIVE `xray` field on the EXISTING `GET /api/watchlist` (computed once, with the watchlist response — **no new endpoint**). Existing `asof_date` + `entries[]` shape stays byte-identical (additive-only).
- [ ] Config surface (typed, no inline literals): `watchlist.xray.{corr_window_days (default ~126), cluster_threshold, min_overlap_days}` in `config.yaml` + the typed config model.
- [ ] No watchlist storage-schema change — the X-ray is computed on read (B-204 "Do NOT touch: watchlist storage schema").

### Frontend
- [ ] Add an **X-ray section** on `/watchlist`: pairwise correlation matrix heatmap (NA cells rendered honestly, never a fabricated value), the cluster groupings, sector/theme concentration bars, the shared-setup count, and the headline "effective independent bets ≈ N.N" with the trailing window **explicitly stated**. The section re-reads the served `xray` payload **verbatim** — NO browser-side correlation/ENB recompute (the B-204 UI-recompute failure mode).
- [ ] Add the additive `WatchlistXray` type in `lib/api.ts`; the page reads `data.xray`. Empty / too-short watchlist → an honest empty/insufficient state (never a crash, never a blank error page).

### New user-facing capability
The owner can see the real concentration of their watchlist — how many *independent* bets it actually represents, which names move together, and where sector/theme/setup crowding sits.

### New information displayed
Pairwise return-correlation matrix; correlation-threshold clusters; effective-number-of-bets headline + its window; sector and theme concentration bars; count of names sharing the same detected setup.

### New user actions
None — a read-only descriptive section. The existing add / remove / reason controls are unchanged.

### UI surface changes
One additive X-ray section on the existing `/watchlist` page. No new page, no new route.

### Product surface delta
`/watchlist` evolves from a flat save-list into a save-list that discloses its own concentration risk — descriptively, with no recommendations.

### Blueprint conformance
`/watchlist` is an EXISTING top-level nav section (Information Architecture "Navigation skeleton"). The X-ray is an additive section on that existing page — **no new page, no nav-skeleton change** (no `blueprint.reapproval-requested` filed). A J-23 row is added to the IA "Feature / journey homes" table (additive).

### Data-contract additions
ONE new displayed value — the **watchlist concentration X-ray payload** — registered in `blueprint.md`:
- **Computed once by:** `app.engine.watchlist_xray:build_xray_payload` (which imports the ONE canonical ENB/correlation helper `app.engine.concentration` — the same helper the future B-104 evidence correlation audit reads; never a second ENB/correlation implementation).
- **Served by:** additive `xray` field on the EXISTING `GET /api/watchlist` (no new endpoint).
- **Single reader:** the `/watchlist` X-ray section (re-reads verbatim; never recomputes in the browser).
It RECOMPUTES no already-registered value — scores/sector/setup/themes are read from the canonical `snapshot_serving:filtered_stock_rows` rows (`GET /api/stocks`), and price series from the bounded `prices:bars_asof_window`. Carries NO proven-language.

## OUT OF SCOPE

- The **B-104** evidence correlation audit surface on `/evidence` (Q3) — this iteration builds ONLY the shared ENB/correlation helper it will later reuse; it does not add any `/evidence` X-ray.
- Any "trim / add / reduce / rebalance" recommendation or position advice (B-204 anti-goal boundary — advice language banned).
- Any position-tracking concept: quantity, cost-basis, P&L, order/buy/sell/broker — the watchlist stays a research save-list.
- Persisting any X-ray field or changing the `watchlist` table schema (computed on read).
- J-24 (B-201 per-stock risk-budget card) and J-25 (B-205 phase-conditional drawdown/dry-spell) — separate risk-analytics journeys, one risky surface per iteration.
- Any `## Evidence Claim` / referee submission — J-23 carries NONE (divisor stays 8; both ledgers byte-identical).
- Fancy clustering / ML — clusters are deterministic correlation-threshold connected components only.

## DEFINITION OF DONE

- [ ] **J-23 passes via browser-qa** — all three journey steps: (1) with several correlated names + one unrelated name on the watchlist, the X-ray shows a pairwise correlation view, cluster groupings, sector/theme concentration, and a headline "effective independent bets" figure with its window stated; (2) a spot-checked pair correlation matches an offline computation over the same window; (3) a name with insufficient overlapping history renders **NA** in the matrix rather than a fabricated value.
- [ ] **Required-still-passing J-01, J-02, J-03, J-05, J-10, J-13, J-20 remain green**, re-verified by the deterministic golden-script replay run **inline** in this iteration (the closure one-liner) OR by an immediately-following lean verify pass — so the iter-33 / iter-36 FULL-iter replay gap does not reopen.
- [ ] `GET /api/watchlist` carries an additive `xray` field; the existing `asof_date` + `entries[]` shape is byte-identical (additive-only; existing watchlist API tests stay green).
- [ ] ENB is computed by exactly ONE shared helper (grep confirms no second ENB implementation); the X-ray payload AND the rendered section contain **no proven-language** ("Proven"/"Not yet proven" absent) and **no advice language** ("trim"/"add"/"reduce"/"rebalance" absent).
- [ ] Unit/integration tests pass, including the B-204 fixture (two perfectly correlated + one independent synthetic series → **ENB ≈ 2**, clusters correct) and a spot-checked pairwise correlation matching an offline computation over the same window; no regression in the backend suite.
- [ ] No `## Evidence Claim` registered; `certified-claims.jsonl` + `staging-ledger.jsonl` byte-identical (7/7 FAIL); canonical Bonferroni divisor stays 8.
- [ ] No anti-goal violation introduced (see Anti-goal reminders — especially #1 no proven-language, #2 no advice, #3 numbers correct, #5 window uses bars ≤ as-of anchored to the seed as-of, #8 bounded reads + honest NA + no crash on empty/short watchlist).
- [ ] Dev handoff written at `docs/handoffs/goal-mcp-loop-iter-38-dev.md`.

## TESTING REQUIREMENTS

- **Browser (by ID):** J-23 (all three steps above). Required-still-passing re-verified (inline deterministic replay or lean follow-on): **J-01, J-02, J-03, J-05, J-10, J-13, J-20**.
- **Unit/integration:**
  - The shared ENB helper: the B-204 fixture (two perfectly correlated + one independent → ENB ≈ 2) + clusters correct.
  - Pairwise correlation spot-check vs an offline computation over the same window (anti-goal #3).
  - `GET /api/watchlist` additive `xray` shape; existing `entries[]`/`asof_date` unchanged.
  - Null-`sector` concentration bucketed as "Unassigned" — not a crash (iter-18/19 nullable-field lesson).
  - Determinism: the same seed/as-of reproduces the X-ray byte-identically (anti-goal #5).
- **Error cases (must be rejected / degrade honestly, never fabricated, never 500):**
  - A member with `< min_overlap_days` overlapping history → NA in the matrix (no fabricated correlation).
  - Empty watchlist (0–1 names) → honest empty/insufficient X-ray state (200, never 500).
  - A name whose bars are absent for the window → NA row, no crash.

## NOTES

- **Depth = full**, triggers: crosses backend (new engine module + shared helper + additive payload) AND frontend (new UI section); introduces a NEW served value needing audit/ux-regression/closure guards; needs new non-browser tests (ENB fixture). Prior evaluator (iter-37) explicitly recommended FULL for J-23.
- **Single-source / build-order call (logged to `assumptions.md`):** the journey says "the ENB helper is the same module used by the evidence correlation audit," but that audit (B-104) is UNBUILT — no ENB helper exists yet. Per the B-204 trap, J-23 lands first and CREATES the one canonical ENB/correlation helper; B-104 reuses it later. Do NOT write a second ENB implementation.
- **B-204 dominant failure mode = UI-recompute:** correlations / clusters / ENB MUST be computed engine-side and re-read verbatim by the page — never recomputed in the browser.
- **Nullable-field lesson (iter-18 / iter-19):** `sector` is legitimately null for ~78% of pool names; the sector-concentration consumer is a NEW consumer of that nullable field — bucket null → "Unassigned" via the existing sector-label helper, never crash or silently omit.
- **Bounded-read / OOM discipline (iter-24 / iter-26 / iter-27, anti-goal #8):** read each watchlist name's return series via the bounded per-symbol `prices:bars_asof_window` (last `corr_window_days` bars ≤ as-of) — never a whole-table ORM load. The watchlist is small, so this is cheap.
- **Determinism (anti-goal #5):** anchor the correlation window to the deterministic seed as-of (`latest_data_date`), never `date.today()`; use bars ≤ as-of only.
- **Systemic replay-gap flag (iter-33 + iter-36 both CLOSURE-FAILed on it):** a FULL iter routes through `run-phase.sh`, which has NO deterministic-replay lane. Run the closure one-liner replay INLINE for the required-still-passing set OR follow iter-38 with a lean verify pass (the iter-34 / iter-37 pattern). Durable fix (framework, not owed to this iter): add the replay lane to `run-phase.sh` / the full path of `run-goal.sh`.
- **Audit-fix partial-trap (iter-13 / 20 / 22 / 31):** if the auditor fixes the rendered X-ray surface AFTER the canonical browser-qa lane runs, request a FRESH browser-qa + ux-regression re-run in the same pass — an audit self-check is not the DoD-named lane, and closure will bounce a stale FAIL.
- **Stale prod-build trap (iter-20 / 21 / 35):** before trusting any "X-ray section missing" observation, confirm `apps/frontend/.next/BUILD_ID` postdates the touched frontend source (force `rm -rf apps/frontend/.next` rebuild).
- **Environment:** before any test/command that writes temp files, export `TMPDIR`/`TMP`/`TEMP` to the pipeline-isolated scratch dir as instructed by the dispatch.
