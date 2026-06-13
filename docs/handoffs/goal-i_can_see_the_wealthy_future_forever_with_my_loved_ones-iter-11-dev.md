# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-11 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-11
**Date:** 2026-06-13
**Agent:** developer
**Status:** complete

## What Was Built

J-58 — `/sectors` ETF rows are now named/described from config (no bare "KRE") and each row's
expanded panel lists its universe members. This mirrors the already-shipped J-57 Themes member
pattern verbatim (no second path invented). All additions are **reference metadata** on the existing
Sector-score Data Contract row — **no canonical value (score/rank/components/RS/dist/trend) changed**
(proven byte-identical in tests).

- **Config catalog (`config.yaml`)**: `etfs.industry` converted from a bare ticker list to a
  `ticker -> {name, description}` catalog (name required, description optional). New `stock_industries`
  section: config-defined, many-to-many `stock -> [industry-ETF tickers]` membership (same shape as
  `themes`).
- **Config validator (`config.py`)**: new `IndustryETFEntry` model (`name` required `min_length=1`,
  `description` optional); `etfs.industry` is now `dict[str, IndustryETFEntry]`. New `stock_industries:
  dict[str, list[str]]` field (default-empty) + `_stock_industries_valid` model-validator (every key
  in-universe; every value ticker in the `etfs.industry` catalog) — malformed/stray entries raise an
  explicit `ConfigError`, never a silent default.
- **Sectors engine (`engine/sectors.py`)**: reads each industry ETF's `name`/`description` from the
  catalog (replaced the `name = ticker` fallback); resolves each ranked ETF's member list (sector →
  `stock_sectors`, industry → `stock_industries`); attaches `description` + `members` to each row dict.
  Members are sorted for determinism. Additive only — the score math is untouched.
- **Model (`models.py`)**: `SectorScoreRow` gained `description: Optional[str] = None` and
  `members_json: str = "[]"` (the stored-copy pattern already on `ThemeScoreRow`; defaults make a row
  constructed/read without them render the honest empty state, not crash).
- **Persist (`engine/scanner.py`)**: `run_scan` writes `description` + `json.dumps(members)` into each
  stored `SectorScoreRow` once, into the immutable snapshot.
- **Serve (`engine/snapshot_serving.py`)**: `_sector_row` echoes `description` + `members`
  (`json.loads(row.members_json or "[]")`) verbatim from the stored row — no read-path recompute. The
  `or "[]"` guard makes a legacy NULL render the empty state.
- **Seed (`seed_loader.py`)**: `add_etf` gained an optional `name` param; industry ETFs are seeded with
  their config display name (the canonical leaderboard name still comes from `SectorScoreRow.name`).
- **Frontend (`lib/api.ts`, `app/sectors/page.tsx`)**: `SectorRow` type extended with
  `description: string | null` + `members: string[]`; the expanded `<tr>` renders the description line
  and an expandable `+n` member list (verbatim port of the `/themes` member block — `MEMBER_PREVIEW_LIMIT
  = 6`, dated new-tab `useAsOfHref` links with `target="_blank"` + `rel="noopener noreferrer"`,
  `data-testid="sector-member-link"` / `"sector-members-toggle"`). Member links + `+n` live in the
  separate, non-clickable expanded `<tr>` with `stopPropagation` (iter-5 hazard). Zero members → explicit
  empty state (`data-testid="sector-members-empty"`, "No universe members are mapped to this ETF").
  Industry membership is labelled "config-defined".

## Files Changed

- `config.yaml` — `etfs.industry` list → `{name, description}` catalog; new `stock_industries` section.
- `apps/backend/app/config.py` — `IndustryETFEntry` model; `etfs.industry` typed as a catalog;
  `stock_industries` field + `_stock_industries_valid` validator.
- `apps/backend/app/engine/sectors.py` — name/description from catalog; member-list resolution; `description`+`members` on each row; docstring note. Scores byte-identical.
- `apps/backend/app/models.py` — `SectorScoreRow.description` + `.members_json` (defaulted).
- `apps/backend/app/engine/scanner.py` — persist `description` + `members_json` into the snapshot.
- `apps/backend/app/engine/snapshot_serving.py` — `_sector_row` echoes `description` + `members`.
- `apps/backend/app/seed_loader.py` — `add_etf` optional `name`; industry ETFs seeded with config name.
- `apps/frontend/lib/api.ts` — `SectorRow` gains `description` + `members`.
- `apps/frontend/app/sectors/page.tsx` — description line + expandable member list + empty state (port of `/themes`).
- Tests (fixture sweep — grepped, not a fixed list): `tests/test_config.py`, `tests/test_config_engine.py`,
  `tests/test_sectors.py`, `tests/test_themes.py`, `tests/test_indexes.py`, `tests/test_api_engine.py`.
  Every inline config dict carrying `etfs.industry` updated to the catalog shape; `stock_industries`
  added where exercised. `tests/test_data_manager.py`'s `SectorScoreRow(...)` construction needs no
  change (new columns default) and now doubles as a legacy-row (empty-members/null-description) case.

## New Tests Added

- `test_config.py`: industry catalog loads with name/description; **missing-name** and **blank-name**
  raise `ConfigError`; `stock_industries` **out-of-universe key** and **unknown-ETF-ticker** raise;
  `stock_industries` optional (default-empty); real config catalog + memberships are all valid.
- `test_sectors.py`: industry ETF name/description from config (KRE != bare ticker); member lists trace
  to the correct mapping (sector → `stock_sectors`, industry → `stock_industries`); **unmapped KRE has
  empty members** (honest empty state, still config-named); **byte-identical canonical-value guard**
  (the no-recompute proof — only `description`+`members` keys added, ranking intact, 31 rows);
  synthetic AAA→SMH member + unmapped BBB.
- `test_api_engine.py`: `/api/sectors` serves config name + description + members verbatim; KRE empty;
  XLK null-description + `stock_sectors` members; every served member is a real universe symbol;
  **re-served stored run is byte-identical** (snapshot immutability) + new fields present on every row.
  (The pre-existing `test_api_sectors_equals_engine_output` already proves served == engine byte-for-byte,
  now covering the new fields automatically.)

## Tests Run

Command (targeted, run by the developer):
- `cd apps/backend && .venv/bin/python -m pytest tests/test_config.py tests/test_config_engine.py -q`
  → **95 passed in 4.22s** (all J-58 config-validation tests included: malformed/blank name, stray
  ETF ticker, out-of-universe key, optional-default, real-config catalog).
- `cd apps/backend && .venv/bin/python -m pytest tests/test_sectors.py tests/test_themes.py tests/test_indexes.py -q`
  → **25 passed in 410s** (incl. ALL new J-58 sector tests: name/description from config, member-list
  resolution from the correct mapping, unmapped-KRE empty state, the BYTE-IDENTICAL canonical-value
  guard, and the synthetic AAA→SMH/unmapped-BBB case).
- `test_api_engine.py` (full module) and `test_scanner.py`+`test_data_manager.py`+`test_seed_integrity.py`
  EXCEEDED the 590s subagent Bash cap during the `loaded_engine` warm-up (SIGTERM/exit 143 — a
  TIMEOUT, NOT a failure; this is the documented heavy-suite runtime constraint). The developer re-ran
  the directly-relevant subsets by keyword (`-k "sector or Sector"` on `test_api_engine.py`; the sector
  row-count test on `test_scanner.py`) — see Fix Notes for those subset results. The FULL `test_api_engine.py`,
  `test_scanner.py`, and `test_data_manager.py` modules are part of the full-suite hand-off to the pump.
- Live end-to-end persist/serve check (fast, no warm-up): loaded the real seed, ran one `run_scan`, read
  back the stored `SectorScoreRow`s and the `/api/sectors` serve payload directly. Confirmed:
  SMH stored+served name "Semiconductors (VanEck)" + description + 27 members (incl. NVDA);
  KRE config-named "Regional Banks (SPDR)" with **empty** members; XLK (sector) null description + 58
  `stock_sectors` members. This is the strongest direct proof of the round-trip + serve-verbatim path.

Frontend: `npx tsc --noEmit` → **exit 0 (clean)**. (`next lint`/eslint is not configured in this
project — no eslint.config.js; the sectors changes are a verbatim style port of the passing `/themes`
page, so the design system is consistent.)

## HANDED TO THE PUMP — full suite

Per project memory (full pytest ~35-45 min, 639 tests, heavy walk-forward warm-up — a subagent cannot
finish it inside the 10-min Bash cap; a dev-turn background run dies on turn-end) the **full suite is
handed to the pump**:

```
cd apps/backend && .venv/bin/python -m pytest tests/ -q
```

Verified-green modules the pump can trust as already-passing for this change: `test_config.py`,
`test_config_engine.py` (full, 95 passed); and the directly-affected `test_sectors.py`,
`test_themes.py`, `test_indexes.py`, `test_api_engine.py` (targeted — see Fix Notes for the final
combined result). The pump should run the WHOLE suite to catch any cross-module fixture miss; the new
required-but-defaulted `SectorScoreRow` columns + the catalog config shape were swept across all inline
configs (grep `etfs.industry` / `SectorScoreRow(` / `stock_sectors` confirmed the surface).

## Subset Verification Results (heavy modules)

The heavy modules that timed out at the 590s cap were re-run as name-scoped subsets (one warm-up each)
and all passed:
- `pytest tests/test_api_engine.py -k "sector or Sector"` → **4 passed, 14 deselected in 384s**. Covers
  `test_api_sectors_equals_engine_output` (served == engine byte-for-byte, now including `description`
  + `members`), the new `test_api_sectors_serves_config_name_description_and_members`, the new
  `test_api_sectors_reserved_run_is_byte_identical` (snapshot immutability), and
  `test_dashboard_top_sectors_match_sectors_endpoint`.
- `pytest tests/test_scanner.py -k "sector or Sector or count or row"` → **1 passed, 9 deselected in 30s**.
  Confirms the sector row-count assertion (`len(config.etfs.sector) + len(config.etfs.industry)`) still
  holds with the dict-shaped `etfs.industry`.

`test_data_manager.py` (incl. its `SectorScoreRow(...)` construction that now relies on the new column
defaults) was NOT run to completion in-turn (it is a large module that overruns the cap) — it is part
of the full-suite hand-off to the pump. The construction was inspected manually: it omits the two new
columns, which default to `None` / `"[]"`, so it constructs fine and doubles as a legacy-row case.

## Known Issues

- KRE ("Regional Banks (SPDR)") is genuinely member-less in the real config (the universe contains no
  regional bank). This is the intended honest empty-state demonstrator — not a bug. Banks in the
  universe (JPM, GS) are mapped to the broad Banks ETF (KBE).
- No DB migration tool is used (SQLModel `create_all`); the two new columns appear on a fresh DB. A
  pre-existing `trendora.db` from before this iteration would lack the columns — for the live host,
  delete/rebuild the dev DB or let the next fresh boot create them. Stored runs predating the columns
  render honestly (null description, empty members) and are never mutated (snapshot immutability).
- The combined `loaded_engine` warm-up makes the sectors/themes/api modules slow (~5 min each warm-up);
  this is pre-existing infrastructure behavior, not introduced here.

## Post-dev fix (2026-06-13) — QA-fixture builder missed the new `stock_industries` section

**Symptom:** the full backend suite failed ONE test:
`tests/test_data_manager.py::test_qa_fixture_builder_writes_only_to_temp_and_not_committed_seed`
with `ConfigError: stock_industries keys not present in universe.symbols: ['ADBE','ADI','AMAT',...]`.

**Root cause:** `apps/backend/scripts/build_qa_fixture_db.py::build_fixture()` narrows the committed
config's `universe.symbols` down to four members `{ANET, DELL, MU, AMD}` and prunes `themes` to keep the
narrowed config valid, but it did NOT prune the new (iter-11) `stock_industries` section. The new
`_stock_industries_valid` validator requires every `stock_industries` KEY to be in `universe.symbols`,
so its ~89 now-orphaned keys made the fixture config invalid. This is the "a new validated config
section must be handled at EVERY config-narrowing site" lesson (project memory).

**Fix (one site, ~6 lines):** in `build_qa_fixture_db.py`, right after the `themes`-pruning block, added
an equivalent key-filter for `stock_industries`: keep only entries whose KEY is in the narrowed
`member_set`. The VALUES are `etfs.industry` tickers (NOT universe members, untouched by the narrowing),
so they are left as-is. An empty result is fine (the section is optional, defaults to `{}`).

**Other narrowing sites checked (grepped `stock_industries` / `universe"]["symbols"` / `raw["themes"]`
across `apps/backend/scripts` + `apps/backend/tests`):**
- `apps/backend/tests/test_data_manager.py:_merge_committed_universe` test — GROWS the universe (union,
  adds ZZZA/ZZZB); never narrows, so no key can fall out. Not affected.
- `apps/backend/tests/test_config.py::test_empty_universe_raises` — operates on the synthetic
  `MINIMAL_VALID` fixture and expects a `ConfigError` anyway. Not affected.
- `apps/backend/scripts/apply_universe_to_config.py` — a MANUAL developer script (not in the test suite)
  that rewrites the committed `config.yaml` from a fresh universe screen and self-validates loudly via
  `load_config()`. It does not exercise the failing path; left untouched per the "only fix a site that
  would actually fail the new validator" rule. (If a future re-screen ever drops a `stock_industries`-
  mapped stock, that script will fail loudly at its own `load_config` re-validation, which is desired.)

**Files changed:** `apps/backend/scripts/build_qa_fixture_db.py` (only).

**Targeted verification (full suite left to the pump):**
`pytest tests/test_data_manager.py::test_qa_fixture_builder_writes_only_to_temp_and_not_committed_seed
tests/test_config.py tests/test_config_engine.py -q` → **96 passed in 4.56s** (the previously-failing
fixture test now passes; no validator regressions).
