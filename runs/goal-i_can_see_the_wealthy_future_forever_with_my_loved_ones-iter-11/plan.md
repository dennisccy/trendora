# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-11 Execution Plan

Single-journey, full-depth iteration. Target: **J-58** — `/sectors` ETF rows named/described
from config (no bare "KRE") + expandable universe-member list per row. This is the **Sectors-side
mirror of the already-shipped J-57 Themes member pattern** — re-use that implementation verbatim;
do NOT invent a second path. Aligned with goal.md Capability #5 (named/described ETFs + member lists).

## What to Build
- **Config catalog:** convert `etfs.industry` from a bare ticker list into a `ticker -> {name, description}`
  catalog (mirrors `etfs.sector`'s ticker->name shape, plus a `description`). Add a new `stock_industries`
  section mapping each in-universe stock -> one or more industry-ETF tickers (many-to-many, exactly like
  `themes:`). Honestly config-defined reference data — no name/description/mapping literal in code.
- **Config validator:** type/validate the new `etfs.industry` catalog shape and `stock_industries` mapping
  in `apps/backend/app/config.py`; malformed entry (e.g. missing `name`) raises an explicit `ConfigError` —
  NO silent default. Keep the engine read backward-typed so a fixture miss fails loudly.
- **Sectors engine:** read industry ETF `name`/`description` from the new catalog (replace the
  `name = ticker` fallback at `sectors.py:75`); resolve each ranked ETF's **member list** — sector ETFs from
  the existing `stock_sectors` mapping (stocks whose sector == this ETF's sector name), industry ETFs from
  the new `stock_industries` mapping (stocks mapped to this ETF ticker). Additive metadata ONLY — the
  score / rank / components / RS-vs-SPY / dist-52w / trend stay **byte-identical**.
- **Model:** add `description: Optional[str]` + `members_json: str` columns to `SectorScoreRow`
  (the stored-copy pattern already on `ThemeScoreRow`).
- **Persist + serve:** `run_scan` writes `description` + `json.dumps(members)` into each stored
  `SectorScoreRow` (once, into the immutable snapshot); `snapshot_serving._sector_row` echoes
  `description` + `members` verbatim. `/api/sectors` row shape gains `description` + `members` — no new
  endpoint, no recompute in the read path.
- **Frontend:** extend `SectorRow` type (`description: string | null`, `members: string[]`); render the
  config description in each expanded row panel + an expandable `+n` universe-member list mirroring
  `/themes` — dated new-tab member links via `useAsOfHref`, explicit empty state when zero members,
  industry membership labelled "config-defined".

## Agents Required
- backend-data: yes -- config catalog + `stock_industries` mapping, validator, sectors engine member
  resolution + name/description from catalog, `SectorScoreRow` columns, `run_scan` persistence,
  `snapshot_serving` echo, byte-identical-score regression tests, fixture sweep across ALL inline configs.
- frontend-ux: yes -- `SectorRow` type extension + `/sectors/page.tsx` expanded-panel description line and
  expandable member list (verbatim port of the `/themes` `ThemeRows` member block).
- developer: yes -- one developer owns both backend + frontend per the standard pipeline.

## Frontend Present: yes

## Files to Create/Modify
- `config.yaml` -- `etfs.industry` list -> `ticker: {name, description}` catalog; add `stock_industries:` many-to-many section.
- `apps/backend/app/config.py` -- type/validate the new `etfs.industry` catalog (`IndustryETF` model w/ `name`+`description`) and `stock_industries: dict[str, list[str]]`; explicit error on malformed entry; validate member tickers are in-universe + ETF tickers exist in the catalog (mirror the `themes`/`stock_sectors` validators).
- `apps/backend/app/engine/sectors.py` -- read name/description from the catalog (replace `name=ticker` at L75); resolve member list per ETF (sector->`stock_sectors`, industry->`stock_industries`); attach `description`+`members` to each row dict; scores untouched.
- `apps/backend/app/models.py` -- add `description: Optional[str] = None` + `members_json: str` to `SectorScoreRow`.
- `apps/backend/app/engine/scanner.py` -- in the `SectorScoreRow(...)` construction (~L165) add `description=row["description"]`, `members_json=json.dumps(row["members"])`.
- `apps/backend/app/engine/snapshot_serving.py` -- `_sector_row` echoes `description=row.description` and `members=json.loads(row.members_json)`.
- `apps/frontend/lib/api.ts` -- extend `SectorRow` with `description: string | null` and `members: string[]`.
- `apps/frontend/app/sectors/page.tsx` -- import `useAsOfHref`+`Link`; add `MEMBER_PREVIEW_LIMIT`; in the expanded `<tr>` render the description line + the expandable member list (port the `/themes` member block, with `data-testid` renamed to `sector-member-link` / `sector-members-toggle`); explicit empty state for zero members.
- Tests (sweep — grep, do not trust a fixed list): `apps/backend/tests/test_sectors.py`, `test_config.py`, `test_config_engine.py`, `test_db.py`, `test_api_engine.py`, `test_themes.py`, `test_indexes.py` and ANY other inline config dict carrying `etfs`/`stock_sectors` or any `SectorScoreRow(...)` construction site.

## UI Evolution
- **New user-facing capability:** On `/sectors`, the user reads what every ETF actually is (config name +
  description, no bare "KRE") and, by expanding a row, sees exactly which universe stocks belong to that
  sector/industry — each opening the dated stock detail in a new tab.
- **New information displayed:** per expanded ETF row — the config **description** line; the **universe-member
  list** (sector members from `stock_sectors`, industry members from `stock_industries`), labelled config-defined.
- **New user actions:** expand a row's `+n` control to reveal all members; click a member ticker to open its
  dated stock detail in a new tab.
- **UI surface changes:** `/sectors` only — the ranked table is unchanged; the **expanded panel** under each
  row gains the description + member list. No new page.
- **Navigation changes:** none (Sectors is already a nav home; J-04's page).

## Visual Requirements
- **Component patterns:** re-use existing `Card` / `table` / `Badge` / `ScoreBadge` / `ComponentBreakdown` /
  `EmptyState`; member tickers are `next/link` chips (port the `/themes` chip styling verbatim); `+n` is a
  real `<button>`. NO new component invented.
- **Layout:** unchanged ranked table; member chips + `+n` live in the **separate, non-clickable expanded
  `<tr>`** (NOT inside the `role="button"` summary row — iter-5 nested-interactive hazard), with
  `onClick={(e) => e.stopPropagation()}` on each chip / toggle.
- **Key visual effects:** match the established `/themes` + existing `/sectors` styling (border chips,
  `hover:border-accent`, focus-visible ring); no ad-hoc effects.
- **States to handle:** loading skeleton (exists); backend-error card (exists); zero ranked rows (exists);
  **NEW** zero-member empty state per ETF — an explicit honest line ("No universe members are mapped to this
  ETF") rendered inside the expanded panel, never fabricated members; NULL `description` (stored run predating
  the column) renders the row's ticker/name without a description line, no crash.

## Key Test Scenarios
- **J-58 browser:** load `/sectors`; an industry row formerly bare "KRE" now shows a config name; expand a
  sector ETF row AND an industry ETF row; member list renders (sector members trace to `stock_sectors`,
  industry members trace to `stock_industries`); an unmapped ETF (if any) shows the explicit empty state with
  **zero** fabricated members; member anchors carry `target="_blank"` + `rel="noopener noreferrer"` and an
  `href` carrying `?asof` while historical / clean at latest. Capture md5-DISTINCT screenshots (no byte-dup
  passed off as different surfaces — iter-3/7/10 evidence-hygiene lesson).
- **Byte-identical guard (the no-recompute proof):** `test_sectors.py` asserts the score / rank / components /
  rs_vs_spy / dist_from_52w_high_pct / trend_label of every row are **identical** to a baseline computed
  before the metadata was attached. This is the central anti-regression assertion — J-04 / J-06 must not move.
- **Config validation:** new `etfs.industry` catalog + `stock_industries` validate; a malformed entry
  (missing `name`, or an `stock_industries` ticker not in the catalog / not in universe) raises an explicit
  config error — no silent default.
- **Round-trip / immutability:** `SectorScoreRow` round-trips `description` + `members_json`; `/api/sectors`
  echoes them verbatim from the stored snapshot; a re-served stored run is byte-identical (no read-path recompute).
- **Required-still-passing:** J-04 (same page ranking/RS/dist/trend), J-03/J-57 (themes member pattern this
  mirrors), J-06 (no canonical value moved), J-02/J-05/J-13 (as-of), J-50 (hrefs carry `?asof`).

## Risks / Open Questions / Assumptions
- **Full pytest gate is ~34-46 min and cannot finish in a subagent (10-min Bash cap; bg run dies on
  turn-end).** Per project memory + the iter spec: the developer runs the **targeted** modules
  (`test_sectors.py`, `test_db.py`, `test_config*.py`, `test_api_engine.py`, `test_themes.py`) and hands the
  **full suite to the pump**. Never run two suites concurrently. QA/audit must confirm the full suite was
  handed off, not skipped.
- **Fixture-sweep blast radius (project memory: "Config fixtures need new required keys"):** the new required
  `SectorScoreRow.members_json` column + the new config shapes (`etfs.industry` catalog, `stock_industries`)
  break EVERY inline test config dict and EVERY `SectorScoreRow(...)` construction site that omits them. The
  count GROWS over time — **grep `etfs`, `stock_sectors`, and `SectorScoreRow(` across `apps/backend/tests/`,
  do NOT trust a fixed list of files.** Keep the engine read backward-typed so a miss fails loudly.
- **Backward-compat for `description`:** make `description` `Optional` (NULL-able) so a stored run predating
  the column renders honestly (ticker/name only, empty members) WITHOUT mutating prior snapshots. `members_json`
  is required on new rows; old rows lacking it render the empty state honestly. Do NOT back-fill / mutate old
  snapshots (coherence invariant 3: snapshot immutability).
- **`etfs.industry` is consumed elsewhere as a bare list** (e.g. iteration over tickers in sectors.py L74,
  possibly indexes/regime/data-manager). Changing it list->dict will break any `for t in cfg.etfs.industry`
  call site that expects strings. **Grep `etfs.industry` across `apps/backend/app/` before changing the shape**
  and update every consumer to iterate `.items()` / `.keys()` as appropriate. This is the highest-risk
  refactor in the iteration — flag for the reviewer.
- **ASSUMPTION — member-link testid naming:** the new member chip / toggle use `data-testid="sector-member-link"`
  and `"sector-members-toggle"` (paralleling `/themes`' `theme-member-link` / `theme-members-toggle`), so the
  browser-qa-agent can target them unambiguously. If the test designer prefers a different name, it is cosmetic.
- **ASSUMPTION — `MEMBER_PREVIEW_LIMIT = 6`** reused from `/themes` for a consistent preview length across the
  two leaderboards. Recorded here rather than blocking.
- **ASSUMPTION — empty-state copy:** "No universe members are mapped to this ETF" (the iter spec's wording),
  shown inside the expanded panel. Honest, never fabricated.
- **Scope guard (in spec, restated):** NO change to Sector Score / rank / components / RS / dist-52w / trend /
  bucketing (byte-identical, asserted). NO second endpoint (members ride `GET /api/sectors`). NO sortable
  member columns / member search (no J-48 view transform requested). The jobs-pipeline cluster
  (J-59/J-60/J-66/J-67), heatmap (J-61), as-of calendar (J-62), event-study (J-63) are OUT — separate
  iterations. The industry membership is config-curated reference data, NOT a rule-based screen (the screen
  anti-goal governs the universe, not this mapping). Data-walled J-22/J-23/J-24 unchanged (non-halting NA).
- **Coherence:** additive reference metadata on the EXISTING Sector-score Data Contract row + the existing
  Sectors IA home — no new canonical value, no new endpoint, no new/moved page. Expect COHERENCE-PASS.
