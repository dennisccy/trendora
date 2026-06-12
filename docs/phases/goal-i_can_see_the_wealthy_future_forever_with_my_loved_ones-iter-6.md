# Goal Iteration 6 — Dashboard indexes & regime card: full history + as-of marker (J-49) + the /stocks nested-button fix

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 6
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-49
- **Required-still-passing journeys:** J-13, J-20, J-44, J-45, J-48
- **Anti-goal reminders:**
  - **Full-history market context never looks ahead.** The dashboard major-indexes & regime card MAY
    render stored bars and stored regime bands dated after the selected as-of **strictly as
    display-only context** behind a visible as-of marker; that rendering MUST NOT feed any as-of-scoped
    computed value (score, count, bucket, gate, aggregate, or evidence figure — all of which stay
    derived from data dated ≤ D), and the stock-detail regime bands MUST stay clamped at the resolved
    as-of date (J-45). *(extends No lookahead + Regime overlays read stored regime only)*
  - **Regime overlays read stored regime only.** The dashboard index-chart bands and the stock-detail
    bands MUST be built from the persisted per-run regime values (label + score from the immutable runs);
    no endpoint, view, or client may recompute a regime, and the same date MUST show the same regime
    label/color on every surface. The stock-detail bands MUST NOT render past the resolved as-of date;
    the dashboard card renders the full stored history behind a visible as-of marker (J-49 — see
    *Full-history market context never looks ahead*). *(extends No recompute in the read path + Single
    source of truth)*
  - **The index chart is honest and never data-gated.** A configured index series without stored bars
    MUST be omitted with no synthesized line; the chart MUST render fully from the committed ETFs without
    DIA; the normalized % series MUST be computed server-side from stored bars (the frontend only
    re-formats, no client-side return math). *(extends No fabricated data)*
  - **No lookahead.** Scoring for a snapshot dated D MUST use only price bars with date ≤ D; forward
    returns MUST use only bars with date > D. *(critical — first sentences; the J-49 full-history
    rendering is the blessed display-only exception defined above)*
  - **No magic numbers.** Every threshold/preset comes from config — the J-49 marker is positional
    (drawn at D), not a new tunable; do not invent one. *(abbreviated; full text in docs/goal.md)*

## GOAL

While viewing a historical date, the dashboard's Major indexes & regime card now shows the full stored
market history through the latest date with a clearly visible vertical as-of marker at D — "where am I
viewing" stays unmistakable, the market's whole path stays visible, and the stock-detail chart's bands
remain clamped exactly as before.

## BACKGROUND

Iter-5 landed J-48/J-50/J-54 (frontend-only, COHERENCE-PASS); the evaluator's recommendation for iter-6
is **J-49 at lean depth** with the iter-5 nested-button defect bundled in. Verified current state:
`apps/frontend/components/major-indexes-card.tsx` passes the global `asOf` to both `fetchIndexes` and
`fetchRegimeHistory`, and `components/index-regime-chart.tsx` filters regime points to `date <=
asofDate` ("bands never paint past it") — i.e. the card is clamped today (J-44 as originally built).
J-49 amends J-44: the card renders the **full stored history** regardless of the global as-of, read from
the **same single-source endpoints** (`GET /api/indexes` → `engine/indexes.py:compute_index_series`;
`GET /api/regime-history` → `engine/regime_history.py:get_regime_history`) with the as-of clamp made
**optional for this surface only** — same stored values, nothing recomputed, no second path. A vertical
as-of marker is drawn at D while historical (the J-20 divider treatment `price-chart.tsx` already uses);
**J-45 is explicitly NOT amended** — the stock-detail bands still stop at D. Because this touches
`apps/backend/` read endpoints, the **full backend pytest suite is a gate** this iteration.

Also bundled (iter-5 evaluator finding, lessons.md "Applies to" match): `SortHeader` in
`apps/frontend/app/stocks/page.tsx` nests `TermInfo`'s `InfoTooltip` `<button>`
(`components/ui/info-tooltip.tsx:62`) inside the sort `<button>` — invalid DOM producing the new
"1 error" Next dev-overlay badge on every iter-5 `/stocks` capture, and an info-icon click bubbles into
a sort. Fix it here before J-51 repeats the pattern on the samples table headers.

Lessons applied (from `state/lessons.md` + project memory):
- **iter-5:** never nest an interactive `TermInfo`/`InfoTooltip` trigger inside another interactive
  element; QA + evaluator treat a dev-overlay error badge appearing vs prior captures of the same page
  as a must-explain regression signal.
- **iter-2 + memory:** the full pytest suite takes ~35–46 min — run it to completion in the foreground
  of the dev turn or explicitly hand it to the pump; never two invocations concurrently; a subagent
  cannot finish it (10-min Bash cap).
- **Memory (config fixtures):** a NEW required typed config field must be added to EVERY inline test
  config dict (now FIVE files incl. `test_indexes.py`) — prefer **no new config key**; if one is
  unavoidable make it optional-with-default and grep the section key across `apps/backend/tests`.
- **iter-0/iter-3:** browser-qa receives the goal.md journey text verbatim; fresh non-blank captures;
  the evaluator md5-spot-checks evidence.
- **iter-4:** the card can render below the fold — require a **scrolled-to capture** of the card.
- **Memory:** the global as-of `<select>` needs the native-setter + bubbled change event under Chrome
  MCP; backend slow-boot is RESOLVED (serve-fast lifespan, iter-28) so the one required backend restart
  is safe on a warm DB — kill by port only, never broad `pkill`.

## IN SCOPE

### Backend
- [ ] **Clamp-optional serving on `GET /api/indexes`** (`apps/backend/app/api/indexes.py` +
  `app/engine/indexes.py:compute_index_series`): add ONE optional boolean query param (e.g.
  `clamp=false` or `full=true` — pick one name and use it on BOTH endpoints) that serves the normalized
  index display series over **all stored bars through the latest date**. Default (param absent)
  preserves today's clamped behavior byte-for-byte, so every existing consumer is untouched. The
  response still echoes the resolved `asof_date` (the client draws the marker from it). Same engine
  function, same stored bars, same normalization — the param only widens the served window; no second
  compute path, nothing recomputed. Unknown-range-preset 422, invalid-`as_of` degradation, and honest
  omission of bar-less series (DIA) all unchanged in both modes.
- [ ] **Clamp-optional serving on `GET /api/regime-history`** (`apps/backend/app/api/regime_history.py`
  + `app/engine/regime_history.py:get_regime_history`): same single param; full mode returns the entire
  stored per-run regime series (labels + scores read VERBATIM from immutable `scanner_runs`, never
  recomputed), default stays clamped (the stock-detail consumer keeps it — J-45).
- [ ] **Unit tests** (`tests/test_api_indexes.py`, `tests/test_regime_history.py`, and
  `tests/test_indexes.py` where the engine seam is tested): (a) default requests are clamped exactly as
  before (regression pin); (b) full mode returns rows dated after `as_of` through the latest stored
  date; (c) the overlapping ≤-D range is **value-identical** between modes (no second path); (d)
  invalid `as_of` + unknown preset behavior unchanged; (e) no new required config key (or, if truly
  unavoidable, optional-with-default + every inline test config updated).

### Frontend
- [ ] **`components/major-indexes-card.tsx`**: request **full history** from both endpoints regardless
  of the global as-of (always pass the new param for this surface); keep passing the resolved as-of and
  an is-historical signal down to the chart; range presets / toggle / legend behavior unchanged
  (re-normalization per J-44 still applies to the full-history series).
- [ ] **`components/index-regime-chart.tsx`**: for this surface, stop filtering regime points to
  `date <= asofDate`; render lines + step-function bands through the latest stored date; draw a
  **clearly visible vertical as-of marker at D while historical** (reuse the J-20 as-of-divider visual
  treatment from `price-chart.tsx` — same line style/label family so the product reads as one design);
  **no marker at latest**; switching range presets re-normalizes and the marker stays at D; hover still
  shows the exact stored six-value label + score per date. Same-date band colors stay identical to the
  stock-detail surface (shared `lib/regime.ts` mapping — do not fork it).
- [ ] **Stock-detail chart untouched**: no change to `price-chart.tsx` band clamping or its data
  requests — the detail chart keeps the default (clamped) endpoint behavior. J-45 and J-20 must read
  exactly as before.
- [ ] **Nested-button fix on `/stocks`** (`app/stocks/page.tsx` `SortHeader`, lines ~383–395): move the
  `TermInfo` info affordance OUT of the sort `<button>` — render it as a sibling (label + sort
  affordance inside the button, info trigger beside it) or switch the tooltip trigger to a non-button
  element with proper keyboard/aria semantics. Clicking the info icon must NOT trigger a sort
  (stopPropagation where needed). Keep the existing sort semantics intact: exactly one visible
  indicator, `aria-sort` + `data-testid` markers, `#` restores stored rank (J-48 must still pass).

### New user-facing capability
While browsing historically, the dashboard market card keeps the whole stored market path visible —
the user sees where D sits inside the full history (vertical marker) instead of having the future
amputated — while every as-of-scoped number on the page stays strictly ≤ D. On `/stocks`, opening a
column-header definition tooltip no longer accidentally re-sorts the table.

### New information displayed
The post-as-of segment of the index % lines and regime bands (display-only market context) and a
vertical as-of marker at D on the dashboard card while historical. No new computed values — every
point is the same stored bar / stored regime row already served.

### New user actions
None new — the existing as-of switcher, range presets, and card toggle now compose with the
full-history rendering; the `/stocks` header info icon becomes safely clickable (no sort side-effect).

### UI surface changes
Dashboard Major indexes & regime card (full history + marker); `/stocks` table header internals
(sort/info affordances un-nested — visual layout essentially unchanged). No new pages, no nav changes.

### Product surface delta
The dashboard becomes an honest time-machine cockpit: historical browsing keeps full market context
with an unmistakable "you are here" marker, while the stock-detail chart demonstrates the deliberate
contrast (clamped bands = analysis surface; dashboard card = context surface). The leaderboard loses
its only invalid-DOM defect.

### Blueprint conformance
No new pages or nav sections. All work lives under the existing **Dashboard** home (`/`) and the
existing **Stocks** home (`/stocks`) registered in `blueprint.md`. The IA Dashboard line and the two
Data Contract rows ("Regime history series", "Normalized index display series") already carry the J-49
TARGET text; their tags are flipped to "[TARGET — iter-6 in flight]" (additive bookkeeping edit, no
re-approval needed — same convention the iter-5 coherence audit accepted).

### Data-contract additions
**None.** J-49 amends the two already-registered contract rows — same computing modules
(`indexes:compute_index_series`, `regime_history:get_regime_history`), same serving endpoints
(`GET /api/indexes`, `GET /api/regime-history`) — the clamp simply becomes optional per surface.
No new value, no new endpoint, no second way to compute or fetch anything. The nested-button fix is
data-free UI chrome.

## OUT OF SCOPE

- **J-51 / J-52** (research samples endpoint family + `/research/samples` drill-down + dated new-tab
  rows) — planned for iter-7.
- **J-53** (parallel multi-date backfill ~2× + per-stage timings in job status) — planned for iter-8 at
  **full** depth, mirroring J-46/iter-3.
- The one-shot best-effort J-22/J-23/J-24 + **DIA** data fetch — deferred to the J-53 iteration, which
  exercises `/data` jobs anyway (recorded again so it is not forgotten; J-49 is explicitly NOT gated on
  DIA).
- **Any amendment to J-45 / the stock-detail chart**: its regime bands stay clamped at the resolved
  as-of; `price-chart.tsx` data behavior unchanged beyond zero.
- New config keys (none should be needed — presets/symbols already live in `config.index_chart`);
  persisting any marker/range state beyond the existing card-toggle persistence; URL-serializing the
  range preset.
- Changing `asof-provider.tsx` state semantics, the as-of switcher, or any J-50 href behavior.
- Any visual redesign of the `/stocks` table beyond un-nesting the two affordances.

## DEFINITION OF DONE

- [ ] Target journey **J-49** passes via browser-qa-agent against the goal.md journey text verbatim
  (all six steps, incl. the `/stocks/NVDA` clamped-bands contrast leg), with fresh, non-blank,
  **scrolled-to** captures of the card both historical (marker visible, data past D visible) and at
  latest (no marker).
- [ ] Required-still-passing journeys remain green: **J-44 re-judged together with J-49 under its
  amended acceptance** (config-listed series, server-side normalization, legend, step bands, three risk
  families, hover label+score, config presets, persisted default-ON toggle, honest DIA omission — the
  step-6 clamp clause is superseded); **J-45** re-verified at the same historical D (detail bands stop
  at D); **J-20** unchanged (forward region display-only, no bands); **J-13** still passes (as-of
  switcher re-points pages; historical indicator); **J-48** still passes after the SortHeader
  restructure (default rank order, toggle, single indicator, `#` restore).
- [ ] Nested-button defect fixed: no React DOM-nesting error on `/stocks` (the dev-overlay "1 error"
  badge present in every iter-5 capture is **gone**), and clicking a header info icon opens the
  definition without changing the sort (QA asserts both explicitly).
- [ ] No anti-goal violation introduced: no post-as-of value feeds any as-of-scoped figure (dashboard
  regime panel, counts, evidence all still ≤ D); nothing recomputed in the read path; same-date regime
  label/color identical on both surfaces.
- [ ] Unit tests pass: new clamp-optional tests green; **full backend pytest suite green** (backend
  touched ⇒ suite is a gate; ~35–46 min — foreground in the dev turn or handed to the pump, never two
  concurrently); `cd apps/frontend && npx tsc --noEmit` clean (ESLint not installed — not a gate).
- [ ] Dev handoff written at
  `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-6-dev.md`, including
  the `git diff --stat`, the param name chosen, and an explicit statement of where the full suite ran.

## TESTING REQUIREMENTS

- Browser (journey by ID, goal.md steps verbatim):
  - **J-49**: set the global as-of to a historical D (native-setter technique); on `/` the card renders
    index lines AND regime bands extending past D through the latest stored date; a clearly visible
    vertical marker sits at D (scrolled-to capture); switch a range preset — lines re-normalize, marker
    stays at D; return to latest — marker gone, card reads exactly as J-44; open `/stocks/NVDA` at the
    same D — detail bands still stop at D, forward region band-free (J-45/J-20 contrast in one capture).
  - **J-44 (amended)**: legend/series from config, hover tooltip shows `yyyy-MM-dd` + per-index % + the
    exact stored regime label + score, toggle off→reload→still off→on, DIA absent from legend without
    error.
  - **J-48 + nested-button**: default order = stored rank; sort Leadership asc/desc with one indicator;
    `#` restores rank with identical values; click the Leadership header's info icon — tooltip opens,
    sort state does NOT change; assert the dev-overlay error badge is absent on `/stocks`.
  - **J-13**: historical browse across `/`, `/stocks` with indicator; return to latest restores.
  - Capture hygiene: fresh per-journey screenshots (md5-distinct where the asserted content differs);
    below-the-fold sections captured scrolled-to.
- Unit/integration: clamp-optional behavior on both endpoints (default-clamped regression pin,
  full-mode through-latest, overlapping-range value identity, invalid `as_of` / unknown preset
  unchanged); the existing no-lookahead, snapshot-immutability, and regime suites all green via the
  **full pytest suite** (the iteration gate).
- Error cases: invalid `as_of` still degrades exactly as today on both endpoints (never a crash or a
  fabricated date); unknown range preset still 422s; a configured series with no stored bars stays
  honestly omitted in full mode too; the card still renders when `regime-history` returns empty
  (existing catch path).

## NOTES

- Prior verdict CONTINUE (iter-5); this follows the evaluator's iter-6 recommendation exactly (J-49 at
  lean + the bundled nested-button fix). Remaining batch plan (context, not binding): iter-7 →
  J-51+J-52 (samples endpoint family + `/research/samples`, count-coherence contract), iter-8 → J-53 at
  **full** depth + the one-shot J-22/J-23/J-24 + DIA best-effort fetch.
- A backend restart on :8835 IS required this iteration (new query param must be served). Safe on the
  warm DB (serve-fast lifespan since iter-28); restart by killing the port's process only — never broad
  `pkill` (multi-project machine). Do not run two pytest invocations concurrently with the restart QA.
- Implementation hint, not mandate: `index-regime-chart.tsx` already receives `asofDate` ("bands never
  paint past it" comment at line 59) — repurpose that prop's doc to "marker position while historical"
  for this surface and keep the clamping semantics where the detail chart consumes shared band
  primitives (`regime-band-primitive.ts` is shared — verify the detail path is unaffected before
  touching it).
- For the evaluator: the J-49 "no post-as-of value feeds any as-of figure" check is best corroborated
  by the unchanged dashboard regime panel / candidate counts at historical D (same numbers as iter-4's
  historical captures of that date) plus the value-identity unit test, not by the chart pixels alone.
