# Goal Iteration 18 — Live browser-QA re-verification of J-74 (multi-hue availability heatmap) + J-76 (price-chart hover box)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 18
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** no (re-verification only — NO code changes this iteration)
- **Target journeys:** J-74, J-76
- **Required-still-passing journeys:** J-61, J-70, J-20, J-45, J-42, J-05, J-06 (and the critical J-18 single-date-selector invariant)
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **No lookahead.** Scoring for a snapshot dated D MUST use only price bars with date ≤ D; forward returns MUST use only bars with date > D. … Chart **visualization** MAY render bars dated > D strictly as a labelled forward/after-as-of display; this display path MUST NOT feed any score, bucket, setup status, pattern flag, factor value, or ranking … and the moving-average lines drawn past D are visualization only, never as-of signals. *(critical)*
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request. … *(extends Single source of truth)*
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them. The same symbol's score MUST NOT differ between two views. *(critical)*
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code. (For J-74: the heat scale / contrast classes are design tokens, not scattered hex.)
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey. (For J-76: an absent MA renders "NA", never a fabricated number.)
  - **Exactly one date selector** (coherence invariant 5 / *No page-local or second date state*): the global as-of control drives every date-scoped page; the heatmap cell-click prefills the JOB FORM only (never `setAsOf`); the price-chart hover box holds no date state. *(critical)*

## GOAL

Capture the live browser evidence that closes J-74 (the availability heatmap renders a clearly-separated multi-hue coverage scale with a legend and legible per-bucket day numbers) and J-76 (the stock-detail price chart shows a per-bar hover detail box), upgrading both from `unknown` to passing — with no code changes.

## BACKGROUND

Iter-17 already built J-74 and J-76: the diffs are source-verified correct against the spec, coherence is COHERENCE-PASS, review is PASS, `tsc --noEmit` is clean, `npm run build` is clean, and the backend diff is empty. The only reason the iteration could not be declared done is that **browser-QA was SKIPPED entirely (0/9 tests; Chrome MCP / DevTools port 9222 was unavailable — ECONNREFUSED)**, so there is zero live screenshot evidence and both target journeys stay `unknown` (strict rule: no Must-have marked passing without positive live evidence). The browser environment (backend :8835, frontend :3835, Chrome DevTools :9222) is now being brought up by the pump. This iteration is therefore a pure live re-verification pass over two isolated frontend surfaces — depth **lean**, no developer code work, no backend, no new unit tests. The evaluator's iter-17 next-step recommendation is exactly this.

**Lessons applied (from this session's ledger — surfaced so QA/evaluator do not repeat them):**
- **iter-17 lesson (env down → SKIP):** before scoring, confirm `:3835` / `:8835` / `:9222` are actually reachable; if browser-QA again reports "SKIPPED / Chrome MCP unavailable" with an empty evidence dir, that is an env failure (CONTINUE), not a code failure — do NOT upgrade `unknown` targets to `passing` on source review alone.
- **iters 3/7/10/13/15/17 evidence-hygiene lesson:** `md5sum` the evidence dir FIRST; one capture per claimed surface; full-VIEWPORT for any close-up (zoomed/cropped close-ups have repeatedly degraded to byte-identical BLANK PNGs and to images mislabeled vs their filename). View pixels per capture — never trust a filename.
- **iter-16 lesson (J-74 seed buckets):** the committed seed only exercises full-coverage days, so heatmap buckets 0–3 are not reachable from live data — they are acceptably source-verified per the iter-16 lesson (the `BUCKET_CLASS` / `BUCKET_TEXT_CLASS` static maps are provably correct without a live render of every branch). Buckets 4–5 + the legend + the snapshot ring marker DO require a live full-viewport capture.
- **iter-16 lesson (J-18 near the as-of control):** J-18 is the critical invariant in this surface family; the cheap decisive check is static — confirm `asof-provider.tsx` / `asof-switcher.tsx` / `asof-calendar.tsx` are byte-untouched (they are not in any iter-17/18 diff) and the heatmap cell-click calls `onPrefillRange` into the job form only (never `setAsOf`).

## IN SCOPE

### Backend
- [ ] None. No backend change this iteration (the iter-17 backend diff was empty and stays empty).

### Frontend (if applicable)
- [ ] None. No frontend code change this iteration. The J-74 (`availability-heatmap.tsx`, `tailwind.config.ts`, `globals.css`) and J-76 (`price-chart.tsx`) code is already committed and source-verified from iter-17; this iteration only EXERCISES it live and captures evidence. If browser-QA surfaces a genuine rendering defect (e.g. a Next dev-overlay error badge, an unreadable bucket, the hover box obscuring the J-20 marker / J-45 bands), record it honestly — that would make this CONTINUE and feed a real fix into iter-19, not a silent pass.

### New user-facing capability
None new — this iteration verifies capabilities delivered in iter-17.

### New information displayed
None new.

### New user actions
None new.

### UI surface changes
None — the `/data` availability heatmap and the `/stocks/[ticker]` price chart are re-exercised, not changed.

### Product surface delta
No change to the product surface. This iteration converts already-shipped-but-unverified work (`unknown`) into evidenced, passing journeys.

### Blueprint conformance
No new surfaces. Both target journeys already have their registered homes in `blueprint.md`: J-74 under **Data Manager `/data`** (per-date availability heatmap) and J-76 under **Stock Detail `/stocks/[ticker]`** (price-chart hover box). Both are tagged in the Information Architecture and Data Contract as built-in-iter-17 surfaces (re-verified iter-18). No nav-skeleton change; no `blueprint.reapproval-requested`.

### Data-contract additions
None. No NEW displayed value is introduced. The heatmap re-renders the SAME `GET /api/data/availability` payload; the hover box reads the SAME already-served `GET /api/stocks/{ticker}/bars` arrays (the `%` change is a pre-registered display derivation of two served closes, not a stored canonical value). No second computation, no second endpoint.

## OUT OF SCOPE

- Any code change to `availability-heatmap.tsx`, `price-chart.tsx`, `tailwind.config.ts`, `globals.css`, or any backend file — UNLESS browser-QA surfaces a genuine rendering defect, in which case stop and report it (do not silently fix-and-pass in a lean re-verify pass).
- J-78, J-73, J-72, J-75, J-77 (the rest of the J-72..J-78 extension) — deferred to iter-19+ per the standing plan (J-78 + J-73 lean next, then the backend cluster J-72 / J-75 / J-77 at full depth).
- Touching the as-of control (`asof-provider.tsx` / `asof-switcher.tsx` / `asof-calendar.tsx`) — they are out of scope and must stay byte-untouched (J-18 invariant).
- J-22 / J-23 / J-24 — data-walled, non-vetoing, unchanged.

## DEFINITION OF DONE

- [ ] Target journeys J-74 and J-76 pass via browser-qa-agent against the LIVE frontend, with distinct, full-viewport, md5-verified screenshots (one per claimed surface).
- [ ] Required-still-passing journeys (J-61, J-70, J-20, J-45, J-42, J-05, J-06) remain green — smoke them live.
- [ ] The critical J-18 single-date-selector invariant is re-confirmed: heatmap cell-click prefills the job form only (as-of indicator stays "Latest", URL stays `/data`), the hover box holds no date state, and `asof-provider/switcher/calendar` are byte-untouched.
- [ ] No anti-goal violation introduced (none can be — no code changes).
- [ ] No new unit tests required (no code change); the existing suite is unaffected. No full-pytest gate needed (backend diff empty).
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-18-dev.md` noting "no-op developer turn — re-verification only; iter-17 code unchanged."
- [ ] If, and only if, the browser-QA environment is again unavailable (Chrome :9222 / :3835 / :8835 unreachable, empty evidence dir), the iteration records that honestly as an environment failure (CONTINUE) — J-74/J-76 stay `unknown`, NOT upgraded to passing on source review alone.

## TESTING REQUIREMENTS

- **Browser (primary gate this iteration):**
  - **J-74** — On `/data`, open the **Per-date availability** heatmap. Capture a full-viewport image showing: (a) a clearly-separated **multi-hue** coverage scale (low→high across distinct hues — slate→blue→cyan/teal→green→amber — NOT a near-uniform teal opacity wash); (b) **day numbers legible against every visible bucket** (the seed exercises high-coverage buckets 4–5 live; buckets 0–3 are source-verified per the iter-16 lesson — note that explicitly, do not fabricate low-coverage data to force them); (c) a **legend** mapping each colour to its coverage level; (d) the **snapshot-day ring/marker** distinct from non-snapshot days. Confirm **hover shows exact figures** (date `yyyy-MM-dd`, symbols-with-bars / total, snapshot yes/no). Confirm a **cell click prefills the job-form Start/End** and the as-of indicator stays **"Latest"** (URL stays `/data`) — the J-18 check. Confirm the J-70 carry-overs are intact in the same capture: **descending months** (newest first) and **two-up-per-row** layout.
  - **J-76** — On `/stocks/NVDA`: move the crosshair across the price chart and capture the **hover detail box** showing that bar's **date (`yyyy-MM-dd`), open/high/low/close, volume, % change, and each rendered moving-average value** (e.g. 20/50/150/200-DMA). Set a **historical as-of D** (via the global switcher) so a post-D forward region exists, then capture the box over a forward bar **labelled "after as-of (display only)"** (J-20 visualization-only). Confirm the box **does not obscure** the J-20 as-of marker / forward divider or the J-45 regime bands. Move the cursor **off the chart** and confirm the box disappears. Confirm an absent MA reads **"NA"**, never a fabricated number.
  - **Required-still-passing smoke (live):** J-61 (heatmap reads `GET /api/data/availability`, hover-exact figures), J-70 (descending months + two-up + legible day numbers), J-20 (full-path chart through latest with as-of marker), J-45 (regime bands behind the stock-detail chart), J-42 (every displayed date reads `yyyy-MM-dd`, including the hover-box date), J-05 (stock detail explainable scores/breakdowns intact), J-06 (score consistency across pages).
- **Unit/integration:** none new — no code path changed this iteration. The existing suite is unaffected; no targeted or full-pytest run is required (backend diff empty). Do NOT gate the evaluator on any pytest run.
- **Error cases:** N/A for new code (none). Verification-only error checks: the heatmap renders an empty/low-coverage day as the lowest bucket hue (never filled/fabricated); the hover box renders an absent MA as "NA"; a forward bar is labelled, never treated as an as-of signal.

## NOTES

- This iteration exists solely because iter-17's browser-QA SKIPPED on an unavailable Chrome MCP / DevTools :9222 (ECONNREFUSED). The code is done and source-clean; the gap is live evidence only. Depth is **lean** (re-verification of two isolated frontend surfaces; no backend, no new tests, no full-pytest gate) per the iter-17 evaluator recommendation.
- **First action for browser-QA:** confirm `:3835` (frontend), `:8835` (backend `GET /api/health` Ready), and `:9222` (Chrome DevTools) are reachable BEFORE running. If any is down, do not fabricate evidence — record the honest SKIP; the evaluator will return CONTINUE (env failure) and this same re-verify spec can be re-dispatched.
- **Evidence hygiene (recurring this session):** `md5sum` the entire evidence dir as the first QA step; require one distinct capture per claimed surface; full-VIEWPORT for any close-up; verify each filename matches its pixels. Reject any regression-journey PASS that rests on a recycled/byte-identical/mislabeled image.
- **Server cleanup discipline (project memory):** never broad-`pkill` `next dev` / `uvicorn` on this multi-project machine — kill by port only. The pump owns bringing the env up.
- After J-74/J-76 close green with no regression and coherence stays clean, the J-72..J-78 scope still has J-78, J-73, J-72, J-75, J-77 outstanding — the next iteration should be J-78 (one-line `config.yaml` `index_chart.default_range` 6M→all, line ~305) bundled with J-73 (synchronous `?asof` URL hydration — touches `asof-provider.tsx`, the J-18/J-43/J-50 invariant core, handle with care), then the backend cluster J-72 / J-75 / J-77 at full depth. This is NOT a GOAL_ACHIEVED candidate yet (those five remain failing).
