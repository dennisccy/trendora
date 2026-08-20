# goal-market-compass-iter-1 Execution Plan

_Scope check: this iteration is exactly goal.md's own named next step (J-01, "unblocks candidate
sector context" for J-04) and matches its suggested build order. No drift from the phase spec —
IN SCOPE/OUT OF SCOPE below mirror `docs/phases/goal-market-compass-iter-1.md` verbatim; nothing
from J-02..J-08, B-114's full history, or the curated `config.stock_sectors` map is touched._

## What to Build

- Add `universe.pool_sector_aliases` (`dict[str, str]`, default `{}`) to the `UniverseCfg` config
  model and to `config.yaml`'s `universe:` block — a normalization seam for future pool-CSV sector
  name mismatches; today's 11 pool sector names already equal `etfs.sector`'s 11 names verbatim, so
  it stays a no-op identity map (TC-6 proves this).
- Add a ticker → pool-CSV-sector lookup helper beside the existing `universe_screen.read_pool()`
  reader (which already returns `{symbol, sector, source}` per row) — reuse that ONE parser, never a
  second CSV reader. Normalize the resolved name through `pool_sector_aliases`, then validate it is a
  member of `etfs.sector`'s valid set; an unrecognized name degrades to `None`, never a crash or a
  stray string (TC-7, AG-8).
- Wire the fallback into `scoring.score_stocks`'s row assembly: curated `cfg.stock_sectors` first,
  the new pool-CSV fallback second, else `None` (renders "Unassigned"). `Stock.sector_id`,
  `stock_sector_etf`, and every `rs_sector` / score input stay completely untouched — this remains a
  descriptive-only field, proven by TC-4's byte-identity fixture.
- Add config-authored two-source sector-basis prose (curated list first, pool-CSV fallback second,
  current-only limitation, B-114 referenced as still open) to the methodology config, and surface it
  through the engine's methodology producer into `GET /api/methodology` — following that module's
  existing "resolve everything live from config, never hardcode a string" pattern.
- Render the new disclosure on `/methodology`, extending the existing `UniverseSelectionCard`-style
  section — no new page, route, or nav entry.
- Zero code change to `/stocks` — its Sector cell and "Unassigned" filter already read the stored
  value as-is; it will simply show far fewer "Unassigned" rows once the backend fallback lands.
- TC-1 through TC-8 unit/integration coverage (coverage %, cross-surface consistency, honest null,
  byte-identity fixture, methodology disclosure content, alias identity no-op, resilience on an
  unresolvable pool sector name, historical-row immutability).
- Dev handoff at `docs/handoffs/goal-market-compass-iter-1-dev.md` citing TC-4 and TC-1 by name.

## Agents Required

- developer: yes -- implements both the backend wiring (config, engine fallback, methodology
  producer) and the frontend disclosure render (`/methodology`) in one pass; this project's roster
  has a single `developer` agent covering both, not a backend/frontend split.

## Frontend Present

yes

## Files to Create/Modify

- `apps/backend/app/config.py` -- add `pool_sector_aliases: dict[str, str] = {}` to `UniverseCfg`
  (~line 56-58); add the sector-basis prose field(s) to the methodology config model
  (`UniverseSelectionCfg` ~line 1786, or a sibling block under `MethodologyCfg` ~line 1837),
  following the existing `membership_rule: str` pattern (plain prose resolved live, never re-typed).
- `config.yaml` -- add `universe.pool_sector_aliases: {}` under the existing `universe:` block
  (~line 131-140); add the new sector-basis prose under the existing `methodology.universe_selection`
  config block.
- `apps/backend/app/engine/universe_screen.py` -- add the ticker→pool-sector lookup helper beside
  `read_pool()` (~line 86-101), applying `pool_sector_aliases` and validating against `etfs.sector`.
- `apps/backend/app/engine/scoring.py` -- wire the fallback into the `"sector"` field in row assembly
  (currently `"sector": cfg.stock_sectors.get(ticker)` at ~line 445); no other line in this file
  changes.
- `apps/backend/app/engine/methodology.py` -- extend `_universe_selection()` (~line 126-160) or add a
  sibling section wired into `build_catalog()` (~line 36-68) to return the two-source disclosure.
- `apps/frontend/app/methodology/page.tsx` -- extend `UniverseSelectionCard` (~line 237) with the new
  disclosure content, reading `state.data.universe_selection`'s new field(s).
- `apps/backend/tests/test_scoring.py` -- TC-4 byte-identity fixture (leadership/entry_quality/risk
  scores, bucket, setup_status unchanged pre/post fallback), TC-6 alias-identity no-op.
- `apps/backend/tests/test_sectors.py` -- fallback-resolution and TC-1/TC-3/TC-7 coverage as
  applicable to the sector-lookup helper.
- `apps/backend/tests/test_methodology.py` / `apps/backend/tests/test_api_methodology.py` -- TC-5
  disclosure-content assertions.
- `docs/handoffs/goal-market-compass-iter-1-dev.md` -- new dev handoff (developer agent writes this).

## UI Evolution

- New user-facing capability: on `/stocks`, the leaderboard Sector column and "Unassigned" filter
  become materially more informative — pool-only names that were never in the curated list now show
  their real sector; a name absent from both sources still honestly shows "Unassigned". No new
  control is added; this is a data-completeness upgrade to an existing surface.
- New information displayed: `/methodology`'s universe/data section gains a short, config-backed
  disclosure naming the two-source sector basis (curated first, pool-CSV fallback second) and stating
  it is current-only (no point-in-time sector history; B-114 referenced as still open).
- New user actions: none — no new buttons, forms, or filters.
- UI surface changes: `/methodology` gains one new disclosure subsection inside the existing
  Universe Selection card (existing card, new content). `/stocks` leaderboard and stock detail header
  are visually unchanged in layout — only the underlying data completeness improves.
- Navigation changes: none.

## Visual Requirements

- Component patterns: reuse the existing `UniverseSelectionCard` card/section styling on
  `/methodology` for the new disclosure subsection — no new component-library element introduced.
- Layout: no layout change; the new content is one additional prose subsection within the existing
  methodology page flow, consistent with the existing threshold-row / TermInfo presentation.
- Key visual effects: none new — match the page's existing minimal, data-dense, dark styling; a text
  disclosure does not warrant glow, gradient, or glass treatment.
- States to handle: normal/present state only for the methodology disclosure (it is config-authored
  and ships with the code, so no loading/error/empty variant is needed beyond the page's existing
  methodology-fetch handling). On `/stocks`, the "Unassigned" filter must keep rendering an honest
  count — smaller after this change, but never fabricated to zero if a genuine gap remains (a symbol
  in neither source is still "Unassigned").

## Key Test Scenarios

- TC-1 (coverage): after a seed-safe Remove + backfill of the last two trading days on `/data`,
  `GET /api/stocks` at the new latest as-of shows ≤5% of resolved members with `sector: null` (was
  78.4% before).
- TC-2 (cross-surface consistency): DELL (curated) and one newly-covered pool-only ticker render the
  identical stored sector string on the `/stocks` leaderboard cell, the `/stocks/{ticker}` detail
  header, and `GET /api/stocks`.
- TC-3 (honest null): a ticker present in neither `config.stock_sectors` nor the pool CSV serves
  `sector: null` and renders "Unassigned" — never a fabricated value.
- TC-4 (byte-identity fixture): the same as-of scored before and after the fallback wiring yields
  byte-identical `leadership`, `entry_quality`, `risk`, `bucket`, and `setup_status` for every stock.
- TC-5 (methodology disclosure): `GET /api/methodology`'s universe/data section names both sources
  (curated first, pool-CSV fallback second) and states the current-only limitation.
- TC-6 (alias identity no-op): with `pool_sector_aliases` left at its default empty mapping, a
  pool-only ticker's served sector equals the raw pool-CSV `sector` value unchanged.
- TC-7 (resilience): a synthetic fixture pool sector name outside `etfs.sector`'s valid set degrades
  to `sector: null` / "Unassigned" rather than raising or displaying an unrecognized string (AG-8).
- TC-8 (historical immutability): a `ScannerResult` row from a run created before this iteration's
  backfill reads unchanged after shipping — historical rows are not rewritten.
- Browser (J-01, all six spec steps via browser-qa-agent): seed-safe Remove + backfill on `/data`,
  then the `/stocks` Unassigned-share check, the two-ticker cross-surface spot-check, the
  `/methodology` two-source disclosure check, and the null-symbol `GET /api/stocks` check.
