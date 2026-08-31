# goal-market-compass-iter-28 Dev Handoff

**Phase:** goal-market-compass-iter-28
**Date:** 2026-08-28
**Agent:** developer
**Status:** complete (initial build)

## IMPORTANT — read this before reviewing

`iter-28/depth-dispatched` reads `lean` despite the spec's `Depth: full`. **No QA agent and no
independent auditor will run this iteration** — the reviewer is the last real gate before this ships.
Two things below are structural consequences of that, not implementation defects, and I want them
visible before anyone reads the DoD checklist:

1. **`state_band` cannot be exercised live this iteration, at all, under any authorized `as_of`.** See
   "Known Issues" #1 — this is the single most important thing in this handoff.
2. **TC-14's perf-budget addendum (`reports/perf-budgets.md`) was NOT written.** It requires a real
   browser's time-to-interactive measurement (DevTools/Playwright), which I do not have and which is
   QA's job in every other iteration. I did not fabricate a number. See "Known Issues" #2.

## What Was Built

### Backend — `state_band` (J-07 Data-Contract addition)
- New `app.engine.compass.build_state_band(session, current_run, previous_run, config)` — a 4th CONTENT
  producer alongside `session_delta`/`narrative`/`selection`, called once inside
  `build_manifest_payload` (compute-at-ingest, same producer, never recomputed at read).
- Three bands, each `{direction_word, delta}`:
  - **`regime`** — reuses the existing `_direction_word` helper verbatim (current vs previous
    `regime_score`, `compass.delta.velocity_flat_band`, **unchanged config key**).
  - **`stress`** — current vs previous stored market-phase `severity` (read via
    `market_phase.market_phase_cached` for BOTH dates — a warm cache hit for any date that was ever
    itself the frontier, never a fresh full-history recompute). `delta` is the literal
    `current_severity - previous_severity` (TC-2's exact equation, unflipped — positive means severity
    ROSE). Banded via a **NEW** config key `compass.delta.stress_velocity_flat_band` (default `5.0`).
  - **`breadth`** — current vs previous `breadth_above_50dma`, banded via the **REUSED** existing
    `compass.delta.breadth_min_change_pts` (no new key — the spec's NOTES explicitly authorized reuse
    "if the reading is sound"; it is: same 0–100-points-of-universe-breadth semantics `session_delta`'s
    own breadth-kind gate already uses).
  - No-prior-run OR a missing per-band input renders that band's `{direction_word: null, delta: null}` —
    never a fabricated word (mirrors `session_delta`/`narrative`'s own no-prior-run handling exactly).
- **Field paths landed match the blueprint's plan exactly**: `state_band.regime.direction_word`,
  `state_band.regime.delta`, `state_band.stress.direction_word`, `state_band.stress.delta`,
  `state_band.breadth.direction_word`, `state_band.breadth.delta`. No blueprint correction needed.
- Wired into `build_manifest_payload`'s content dict (additive `content_hash` scope — proven by
  `test_state_band_is_wired_into_manifest_payload_and_content_hash`, which tampers `state_band` and
  shows the recomputed hash changes) and into `_freeze_manifest`'s document + a new `state_band_json`
  column on `NextSessionManifest` (additive, nullable — `apps/backend/app/db.py`'s
  `_ADDITIVE_COLUMNS`, same mechanism every other iter-3+ freeze-block column uses).
  `manifest_row_payload` reads it back verbatim (a read, never a recompute).
- Schema (`docs/handoffs/trendora-next-session-manifest-v1.schema.json`): added
  `"state_band": {"type": ["object", "null"]}`, **not** added to `required` — additive, matching the
  precedent of `candidate_rule_config`/`cohort_rule_config` (both optional+nullable in this same
  schema), because every one of the 26 pre-iter-28 manifest rows will forever read `state_band: null`
  (AG-12: never backfilled) and must still validate. No `schema_version` bump (additive field, per the
  iter-11/12 precedent the spec cites).
- `provenance.engine_files`/`provenance.config_keys` needed no change — `compass.py` and
  `compass.delta` were already listed, and `stress_velocity_flat_band` is nested inside `compass.delta`.

### A deliberate design decision: `stress`'s word polarity is FLIPPED relative to its delta's sign
This is the one real judgment call in this iteration, so I'm calling it out on its own.

`compass.vocabulary.direction_words` is `up: "improving"`, `down: "deteriorating"`, `flat: "little
changed"` — value-laden words, not neutral "went up/down" labels. For `regime`/`breadth`, a HIGHER
value is healthier, so a positive delta correctly reads "improving". For `stress` (market-phase
`severity`), the polarity is the OPPOSITE: a RISING severity is deteriorating, not improving — this is
the engine's own existing, already-documented convention
(`app/engine/market_phase.py::_severity_velocity_at`'s docstring: "Sign convention POSITIVE = severity
worsening"). If I classified the raw, unflipped `stress` delta through the same up=improving rule
regime/breadth use, a market getting materially MORE stressed would render an "improving" badge — a
false claim about market direction, which is exactly what the Vision statement and AG-3 (displayed
values must be correct) exist to prevent.

So: **`state_band.stress.delta` is the literal, unflipped `current_severity - previous_severity`**
(satisfies TC-2's equation exactly as written), but **`state_band.stress.direction_word` classifies
the NEGATION of that delta** — severity falling (stress easing) reads "improving", severity rising
reads "deteriorating". Proven directly by
`test_state_band_regime_matches_direction_word_and_stress_flips_polarity` in `test_compass.py`, which
uses a fixture where regime rises (+8.0, "improving") AND severity also rises (+20.0) in the SAME pair
of runs, and asserts the two bands render OPPOSITE words for that one pair — the strongest test I could
write to prove the flip is deliberate, not an accidental inversion.

If a reviewer reads TC-2's "the flat-band classification of that delta" as requiring the RAW,
unflipped delta to drive the word too (not just the number), that is the one place my implementation
diverges from the most literal reading of the spec text — and I made that call in favor of AG-3
correctness over literal-text compliance. Flagging it explicitly rather than silently picking one.

### Frontend — `/` reorder + `/market` relocation (J-07 + J-08)
- **New `compass-state-band-card.tsx`**: regime tile (label+score from `GET /api/dashboard`, direction
  badge from `state_band.regime`, breakdown via the shared `ComponentBreakdown` against
  `dashboard.regime.components`) and phase tile (phase+severity+P(bear) from `GET /api/market-phase`,
  direction badge from `state_band.stress`, breakdown via `ComponentBreakdown` against
  `phase.components`), plus a breadth line (level from `dashboard.breadth.above_50dma_pct`, direction
  badge from `state_band.breadth` — no breakdown disclosure here, `/api/dashboard`'s breadth block
  carries no `components` array to break down). A labelled link-out ("Full market context...") to
  `/market`, `?asof`-aware via the existing `useAsOfHref`, sits where the cross-view chart used to be.
  Every tile degrades independently and honestly: `dashboard` is required (the page only renders this
  card once it has succeeded), `phase === null` / `!phase.available` render the SAME unavailable/NA
  states the old `PhaseGlanceCard` already used, and a `null` `compass` or `compass.state_band` (or a
  `null` on one specific band) renders that badge as literal "NA" — never fabricated, never a crash.
- **New `compass-leadership-rotation-section.tsx`**: filters the ALREADY-served
  `compass.session_delta.changes` to `kind ∈ {sector, theme, stock}` for display — no new computed
  value, no client threshold, no client word selection (reuses the exact list-row markup
  `CompassWhatChangedCard` already uses).
- **`apps/frontend/app/page.tsx`** (rewritten): body order is now market-state band → summary →
  what-changed → leadership rotation → next-session focus → manifest strip, exactly as specced. `/`
  fetches only `GET /api/dashboard`, `GET /api/market-phase`, `GET /api/compass` (verified by grep:
  `fetchSectors`/`fetchThemes` no longer appear anywhere in this file). `DashboardBody` and every
  subcomponent it owned (`RegimeGlanceCard`, `PhaseGlanceCard`, `SeverityBreakdown`,
  `PhaseCrossViewCard` usage, `MoreDetailSection`, `CandidateCountsCard`, `MetricCard`,
  `DashboardSkeleton`) are REMOVED from this file (verified: `PhaseCrossViewCard`/`MarketPhaseCard` do
  not appear in it at all).
- **New `apps/frontend/app/market/page.tsx`**: the removed `DashboardBody` tree moved verbatim (same
  component names, same endpoints — `fetchDashboard`/`fetchMarketPhase`/`fetchSectors`/`fetchThemes`,
  same persisted localStorage keys `trendora.dashboard.phaseCrossView` (inside `PhaseCrossViewCard`,
  untouched) and `trendora.dashboard.moreDetail` (inside the relocated `MoreDetailSection`) — both
  confirmed present verbatim by grep. The only things NOT verbatim are the outer wrapper: the default
  export is renamed `DashboardPage` → `MarketPage`, and the `PageHeading` now reads "Market" / "The
  full market context — regime, phase, breadth, sectors, and themes" (the old "Dashboard" heading no
  longer makes sense once the sidebar entry is renamed). Everything inside `DashboardBody` itself,
  including its own internal component names, is unchanged.
- **`apps/frontend/components/sidebar.tsx`**: `/` relabeled "Dashboard" → "Today" (icon: `Compass`); a
  new `{ href: "/market", label: "Market", icon: LayoutDashboard }` entry added immediately after it
  (reusing the old Dashboard icon, since it now represents the former dashboard body). Every other
  entry's route/order/label is byte-identical to before (diff-verified). `isActive`'s existing
  `href === "/" ? pathname === "/" : pathname.startsWith(href)` logic needed no change — `/market`
  correctly falls into the `startsWith` branch and never collides with `/`'s exact-match branch.
- **`apps/frontend/lib/api.ts`**: added `CompassStateBandEntry`/`CompassStateBand` types and
  `state_band: CompassStateBand | null` on `CompassResponse` (null covers the pre-iter-28-row case,
  mirroring `generation`/`candidate_rule_hash`'s own null-on-legacy-row pattern already in this file).

### Config
- `config.yaml`: added `compass.delta.stress_velocity_flat_band: 5.0` with an inline comment explaining
  the reuse-vs-new-key decision for both stress and breadth.
- `apps/backend/app/config.py`: `CompassDeltaCfg` gained the typed `stress_velocity_flat_band: float`
  field (validated `>= 0`, same pattern as `velocity_flat_band`); `_default_compass()`'s built-in
  default updated to match.

## Files Changed
- `apps/backend/app/config.py` — `CompassDeltaCfg.stress_velocity_flat_band` (new typed field + validator + default).
- `apps/backend/app/db.py` — `_ADDITIVE_COLUMNS`: `next_session_manifests.state_band_json` (additive ALTER).
- `apps/backend/app/models.py` — `NextSessionManifest.state_band_json: Optional[str]` (new column) + docstring update.
- `apps/backend/app/engine/compass.py` — `_flat_band_word` (extracted, generic), `_severity_at`, `build_state_band`; wired into `build_manifest_payload`, `_freeze_manifest`, `manifest_row_payload`.
- `apps/backend/tests/test_compass.py` — 9 new `build_state_band` fixture tests + module docstring/import (`hashlib`).
- `apps/backend/tests/test_api_compass.py` — 2 new route-level tests (`state_band` present + null-on-legacy-row).
- `config.yaml` — `compass.delta.stress_velocity_flat_band: 5.0`.
- `docs/handoffs/trendora-next-session-manifest-v1.schema.json` — additive `state_band` property.
- `apps/frontend/app/page.tsx` — rewritten: Today page, reordered body, sectors/themes fetches removed.
- `apps/frontend/app/market/page.tsx` — new: relocated `DashboardBody` verbatim.
- `apps/frontend/components/compass-state-band-card.tsx` — new.
- `apps/frontend/components/compass-leadership-rotation-section.tsx` — new.
- `apps/frontend/components/sidebar.tsx` — "Today"/"Market" nav entries.
- `apps/frontend/lib/api.ts` — `CompassStateBand*` types, `CompassResponse.state_band`.

## Tests Run

Backend (targeted files only, per project-template's resource contract — `loaded_engine`-dependent
`test_db.py` was deliberately excluded from my runs after an early combined run showed it pulls in the
full 30-year seed bootstrap; I confirmed separately that its one column-registry guard test
(`test_every_model_column_on_existing_table_is_covered_by_additive_registry`) is scoped to
`data_provider_runs`/`import_checkpoints`/`forward_returns` only and does not cover
`next_session_manifests`, so it provides no coverage of my change either way):

```
cd apps/backend && .venv/bin/python -m pytest tests/test_compass.py tests/test_api_compass.py -q
→ 54 passed

cd apps/backend && .venv/bin/python -m pytest tests/test_config.py tests/test_config_engine.py \
    tests/test_no_magic_numbers.py tests/test_manifest_invariants.py tests/test_ingest_finalize_compass.py -q
→ 180 passed, 1 failed
```

The one failure (`test_no_magic_numbers.py::test_engine_calc_code_has_no_magic_numbers`) flags literals
in `indicators.py`, `forward_testing.py`, and `research.py` — **files I never touched** (`git diff
--stat` confirms zero changes to any of the three; `compass.py`, the only engine file I edited, is NOT
in the failure list). This is a pre-existing, out-of-scope failure; I did not investigate or fix it
(touch-only-what-the-report-lists discipline, and no report names it — it just surfaced incidentally
because I ran the file it lives in).

Frontend:
```
cd apps/frontend && NEXT_DIST_DIR=.next-verify npx next build
→ ✓ Compiled successfully, ✓ types checked, ✓ 30/30 static pages generated, /market present in the route table
```
(Plain `npm run build` refuses to target the live `.next` dir without `NEXT_PUBLIC_API_URL` — an
existing guard from ops-hardening iter-77, unrelated to this iteration; its own error message names
the `NEXT_DIST_DIR=.next-verify` workaround I used, which is the sanctioned verification path.)
`npm run lint` could not run in this environment (interactive ESLint config prompt, no committed
`.eslintrc`) — pre-existing environment gap, not attempted to fix (lint is not the sanctioned test
command per project-template; `npm run build` is).

Live smoke test (backend + frontend started via the project scripts, stopped afterward):
- `GET /api/health` — `last_run_date`/`seed_latest_date` both `2026-08-12`, matches the coordinator's
  stated frontier.
- Pre-check: `next_session_manifests` 26 / `scanner_runs` 3128 / `daily_prices` 3310374 — exact match
  to the coordinator's stated baseline.
- `GET /api/compass` (NO `as_of` param — the only call I made against the live backend, SAFE per the
  binding gate) returned `as_of: 2026-08-12, version: 6, mode: at_ingest, state_band: null` — see Known
  Issue #1.
- Post-check: same three counts, unchanged (26 / 3128 / 3310374) — confirms this GET minted nothing.
- `/` and `/market` both returned HTTP 200 from the Next.js server; the raw HTML's sidebar nav hrefs are,
  in order, `/, /market, /stocks, /themes, /sectors, /scanner-runs, /backtest, /research, /evidence,
  /watchlist, /methodology, /data` — Today first, Market second, everything else unchanged (TC-17). The
  `/` HTML's nav entry for `href="/"` renders the `lucide-compass` icon immediately followed by
  `<span>Today`, confirming the label+icon wiring.
- Both servers stopped (`kill` on the exact PIDs `ss`/`ps` reported) before finishing; ports 8255/3255
  confirmed free afterward.

I did NOT run a real browser (no Chrome MCP tool available to the developer role) — I could not verify
rendered client-side content (tile values, badges, disclosures) visually, only that both routes 200 and
the SSR shell (chrome + sidebar) is correct. That's browser-QA's job in every other iteration; it is not
running this one.

## Known Issues

**1. (Load-bearing) `state_band` cannot be observed live, at all, this iteration — a structural
consequence of the binding safety gate, not a defect.** Every `as_of` value this iteration authorizes
for live testing — no param (Latest, `2026-08-12`), `2026-08-12`, `2025-04-15` — ALREADY carries a
manifest row minted before this iteration existed (2026-08-12 has v1–v6, 2025-04-15 has v1–v2).
`next_session_manifests` is create-once: a `GET /api/compass` for any of these three values returns the
EXISTING stored row unchanged, so `state_band` reads the entire-block `null` I verified live above,
never the happy-path three-word object. Nothing in this iteration's authorized live-testing surface can
trigger a NEW mint (that would require either a not-yet-manifested `as_of`, which is exactly what's
forbidden, or `POST /api/compass/regenerate`, which is explicitly out of scope). This means:
- TC-1/TC-2/TC-3/TC-4 (state_band correctness) are proven ONLY by the 9 new backend fixture tests in
  `test_compass.py` + 2 route tests in `test_api_compass.py` — not by anything a browser-qa lane could
  observe this iteration even if one ran.
- TC-6/TC-7/TC-8 (tile value/badge consistency) will be checkable for the label/score/phase/severity/
  P(bear) halves (all sourced from `dashboard`/`phase`, independent of `state_band`), but the
  "direction-word badge equals `state_band.<band>.direction_word`" half will show "NA" on every live
  check this iteration — which IS the correct served value (both sides are consistently `null`/"NA"),
  just not the interesting/differentiating case those TCs were written to exercise.
- The happy path (three real words + deltas) will first become live-observable whenever the frontier
  next advances past this iteration's build and a genuine `ingest_finalize` freeze mints a manifest
  through the now-state_band-aware `_freeze_manifest` — a future iteration's event, not something I can
  produce here without violating the safety gate. This is the exact same "pre-X-era" pattern this
  codebase already used for the iter-3 freeze/integrity block itself (pre-iter-3 rows read `mode: null`
  forever) — not a new kind of gap.

**2. TC-14 / the `reports/perf-budgets.md` addendum was not written.** It requires real
time-to-interactive + on-load API latency measurement (browser DevTools / Playwright timing), which
the developer role does not have tooling for and which every other iteration's perf-budget entries in
that 12,000+-line file were produced with real methodology (see the file's own iter-25 addendum and its
audit correction for how rigorous these entries are expected to be) — I chose not to add a
low-quality, curl-only approximation to that ledger rather than degrade its evidence quality. This DoD
item is unmet and needs either a browser-QA pass (not running this iteration) or explicit owner
acceptance that it's deferred.

**3. TC-13's "zero producer calls on warm GET" is proven at the pytest level** (the pre-existing,
unmodified `test_compass_route_computes_once_serves_from_storage_after` monkeypatches
`build_manifest_payload` — which now contains `build_state_band` too — and asserts zero calls on both a
first warm hit and a second one; still passing) — but the "no request to /api/sectors, /api/themes, or
any full-history series" half of TC-13 is verified only by code inspection (grep confirms neither fetch
call exists in `page.tsx` anymore), not by an actual captured browser network trace.

**4. Cosmetic deviation from "verbatim":** `/market`'s outer `PageHeading` text changed from
"Dashboard"/"The daily snapshot at a glance" to "Market"/"The full market context — regime, phase,
breadth, sectors, and themes", since the sidebar no longer calls it "Dashboard". Everything INSIDE
`DashboardBody` (the actual relocated content the spec's "verbatim" language is about) is unchanged.

**5. Backend perf/resource claim not independently re-measured this iteration** — `build_state_band`
adds one extra `market_phase_cached` read (for the previous run's severity) at freeze time only, which
is a cache lookup keyed by `(asof_key, dataset_version)`; for any date that was ever itself a stored
run's own compass freeze, this is a warm hit. I did not measure ingest-finalize wall-clock before/after
since no ingest ran live this iteration (would require advancing the frontier, out of scope).

## Anti-Goal Self-Check (developer's own pass — not a substitute for review)
- **AG-2**: no new imperative/forecast/advice language; `state_band` words are the SAME three-value
  vocabulary already banned-language-scanned by `_assert_no_banned_language` (unchanged scan, unchanged
  word map).
- **AG-3**: correctness proven by fixture tests for the computation; frontend never recomputes, always
  renders served values or honest NA (see Known Issue #1 for what "correctness" could NOT be checked
  live this iteration).
- **AG-8**: `state_band` null (whole-block or per-band) never crashes the route or the frontend — proven
  by `test_compass_route_state_band_null_on_pre_iter28_row` (backend) and the frontend's `stateBand?.
  <band>.direction_word ?? "NA"` optional-chaining pattern throughout `compass-state-band-card.tsx`. No
  new full-table/full-history read introduced — `_severity_at` reuses the existing per-date cached
  `market_phase_cached`, same bounded-read posture as the rest of `compass.py`.
- **AG-9**: `test_no_network_or_lookahead_imports_in_compass_module` (existing, unmodified, still
  passing) statically scans `compass.py` for banned network/lookahead identifiers — my additions
  introduced neither.
- **AG-11**: `state_band` is three independent word+delta pairs over existing scalars
  (`regime_score`/`severity`/`breadth_above_50dma`), never combined into one new blended number; no
  candidate/manifest field changed.
- **AG-12**: `state_band_json` is additive-only (ALTER TABLE ADD COLUMN); `_freeze_manifest` still only
  INSERTs; live-verified the 26 pre-existing manifest rows' total count is unchanged before/after my
  only live `GET /api/compass` call.
- **AG-13**: grep-confirmed no readiness/preflight token ("Ready"/"GO"/"DEGRADED"/"NO-GO") appears in
  `compass.py`, `compass-state-band-card.tsx`, `compass-leadership-rotation-section.tsx`, or the new
  `page.tsx`; `state_band`'s vocabulary is the pre-existing, already-audited `direction_words` map.
