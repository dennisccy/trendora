# Iter-11 (J-58) Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-11  
**Date:** 2026-06-13  
**Frontend Present:** yes

## Phase Goal

On `/sectors`, every ranked ETF row is named and described from config (no bare tickers like "KRE"), and each row's expanded panel lists its universe members with an explicit empty state when unmapped — sector members from `stock_sectors`, industry members from a new config-curated `stock_industries` mapping.

## Test Cases

### TC-01 — Industry ETF names resolve from config catalog

**Type:** api  
**Preconditions:** Backend is running; `config.yaml` contains `etfs.industry` as a `ticker: {name, description}` catalog (not a bare list).

**Steps:**
1. Call `GET /api/sectors`
2. Inspect the JSON response for an industry-type row (check `sector_type == "industry"`)
3. Verify the `name` field matches the config catalog entry (e.g., "SMH" → configured name, not the bare ticker)

**Expected outcome:** Industry ETF rows show configured display names, not bare tickers.  
**Pass criteria:** Every industry row in the response has `name` equal to the value in `config.yaml:etfs.industry[ticker].name`; no row has `name == ticker`.

---

### TC-02 — Industry ETF descriptions are served from config

**Type:** api  
**Preconditions:** Backend is running; `config.yaml` contains `etfs.industry` with both `name` and `description` fields per ticker.

**Steps:**
1. Call `GET /api/sectors`
2. Inspect the JSON response for an industry row
3. Verify the `description` field is present and matches the config

**Expected outcome:** Each industry row includes a `description` field from config.  
**Pass criteria:** Every industry row has a non-null `description` field matching `config.yaml:etfs.industry[ticker].description`; no row is missing the field.

---

### TC-03 — Sector ETF members resolve from stock_sectors mapping

**Type:** api  
**Preconditions:** Backend is running with fresh scan; `config.yaml` contains both `stock_sectors` and `stock_industries` mappings; at least one sector-type row exists in the `/api/sectors` response.

**Steps:**
1. Call `GET /api/sectors`
2. Find a sector-type row (check `sector_type == "sector"`)
3. Inspect the `members` array in the response
4. Verify each member ticker is a stock in the universe where `stock_sectors[ticker] == this_sector_name`

**Expected outcome:** Sector ETF rows list only stocks whose `stock_sectors` mapping matches that sector.  
**Pass criteria:** Every member in the `members` array for a sector ETF matches a stock in `config.yaml:stock_sectors` with the same sector name; no extraneous tickers.

---

### TC-04 — Industry ETF members resolve from stock_industries mapping

**Type:** api  
**Preconditions:** Backend is running with fresh scan; `config.yaml` contains the `stock_industries` section mapping stocks to industry ETF tickers.

**Steps:**
1. Call `GET /api/sectors`
2. Find an industry-type row
3. Inspect the `members` array
4. Verify each member is a stock mapped to this ETF ticker in `config.yaml:stock_industries[ticker]`

**Expected outcome:** Industry ETF rows list only stocks explicitly mapped to that ETF in `stock_industries`.  
**Pass criteria:** Every member in the `members` array for an industry ETF exists in `config.yaml:stock_industries[etf_ticker]`; no fabricated members.

---

### TC-05 — Unmapped ETF shows explicit empty-state members

**Type:** api  
**Preconditions:** Backend is running; at least one ETF in the response has no mapped members (either no entries in `stock_sectors` for that sector or no entries in `stock_industries` for that industry ticker).

**Steps:**
1. Call `GET /api/sectors`
2. Find an ETF row with `members: []`
3. Verify the response includes the row but with an empty members array

**Expected outcome:** An unmapped ETF is not omitted from the response; it appears with an empty members list.  
**Pass criteria:** The response includes all ranked ETF rows, including those with `members: []` (empty array, not missing field); no row is silently excluded.

---

### TC-06 — SectorScoreRow persists and serves description + members_json

**Type:** artifact  
**Preconditions:** Database has fresh `SectorScoreRow` records after a successful scan; `description` and `members_json` columns exist in the schema.

**Steps:**
1. Inspect the database: `SELECT ticker, description, members_json FROM sector_score_row LIMIT 5`
2. Verify each row has non-null `description` and `members_json` (may be `[]` but not NULL)
3. Verify the `members_json` is valid JSON that deserializes to a list of strings

**Expected outcome:** Each `SectorScoreRow` stores the snapshot's description and members list as written at scan time.  
**Pass criteria:** Every row in `sector_score_row` has `description IS NOT NULL` and `members_json IS NOT NULL` and is valid JSON; no exceptions on deserialization.

---

### TC-07 — /sectors page displays industry ETF config names

**Type:** browser  
**Preconditions:** Frontend is running on `http://localhost:3000`; backend is running with fresh scan; at least one industry ETF row is visible in the page.

**Steps:**
1. Navigate to `http://localhost:3000/sectors`
2. Wait for the ranked table to load
3. Locate a row with `sector_type == "industry"` (e.g., "SMH", "KRE")
4. Read the displayed name in the table row
5. Verify it matches the config name (not the bare ticker)

**Expected outcome:** Industry ETF rows show their configured display names.  
**Pass criteria:** At least one industry row displays a name that differs from the ticker (e.g., "SMH" displays "Semiconductors" or similar, not "SMH"); visual inspection confirms legibility.

---

### TC-08 — Expanding an ETF row reveals config description

**Type:** browser  
**Preconditions:** Frontend and backend are running; user is on `/sectors` with the table loaded.

**Steps:**
1. Locate an industry ETF row (e.g., "SMH")
2. Click the expand/collapse toggle for that row (or click the row itself if it has an expand affordance)
3. Wait for the expanded panel to render
4. Inspect the rendered content for a description line

**Expected outcome:** The expanded panel displays the config description for that ETF.  
**Pass criteria:** The expanded `<tr>` contains text matching the configured description (e.g., "Semiconductors ETF" or the configured text); no placeholder or missing text.

---

### TC-09 — Expanding an ETF row reveals member list

**Type:** browser  
**Preconditions:** Frontend and backend are running; user is on `/sectors` with an expanded row visible.

**Steps:**
1. Expand an industry ETF row
2. Inspect the expanded panel for a members section
3. Count the visible member tickers
4. Verify they match the config mapping for this ETF

**Expected outcome:** The expanded panel displays a list of member tickers, capped by a preview limit (e.g., first 6), with a "+N more" toggle if the full list is longer.  
**Pass criteria:** At least one member ticker is visible; if more than the preview limit exist, a "+N more" or "Show all" button is present; visible members are accurate.

---

### TC-10 — Member links open in new tabs with ?asof date parameter

**Type:** browser  
**Preconditions:** Frontend and backend are running; an ETF row is expanded and members are visible; the page is in historical mode (with `?asof` in the URL).

**Steps:**
1. Navigate to `/sectors?asof=2026-05-15` (or any historical date)
2. Expand an ETF row with members
3. Inspect a member ticker link element (`<a>` tag)
4. Verify the `href` contains `?asof=2026-05-15` and `target="_blank"`

**Expected outcome:** Member links carry the historical date parameter and open in a new tab.  
**Pass criteria:** At least one member link has `target="_blank"`, `rel="noopener noreferrer"`, and `href` containing the same `?asof=` date as the page.

---

### TC-11 — Member links at latest date are clean (no ?asof)

**Type:** browser  
**Preconditions:** Frontend and backend are running; user is on `/sectors` without any `?asof` parameter (latest date mode).

**Steps:**
1. Navigate to `/sectors` (no query string)
2. Expand an ETF row with members
3. Inspect a member ticker link
4. Verify the `href` does NOT contain `?asof`

**Expected outcome:** Member links at the latest date do not carry a date parameter.  
**Pass criteria:** At least one member link has `href` pointing to `/stocks/[TICKER]` (no `?asof=` suffix).

---

### TC-12 — Unmapped ETF shows explicit empty-state text

**Type:** browser  
**Preconditions:** Frontend and backend are running; at least one ETF in the response has no members; user is on `/sectors`.

**Steps:**
1. Locate an ETF row with zero mapped members (check API response or expand a row)
2. Expand that row
3. Inspect the expanded panel for an empty-state message

**Expected outcome:** The panel displays a user-facing empty-state message instead of fabricated data.  
**Pass criteria:** The expanded panel contains text like "No universe members are mapped to this ETF" or similar; no fake/placeholder members are shown.

---

### TC-13 — Config validation rejects malformed etfs.industry catalog

**Type:** api  
**Preconditions:** Backend is running; attempting to start with a malformed `config.yaml`.

**Steps:**
1. Create a malformed config entry (e.g., missing `name` in an industry ETF: `{description: "..."}` without `name`)
2. Attempt to start the backend
3. Observe the error output

**Expected outcome:** Backend startup fails with an explicit config validation error.  
**Pass criteria:** Error message mentions the missing `name` field or similar; backend does not silently default or crash with an obscure error.

---

### TC-14 — Config validation rejects stock_industries ticker not in catalog

**Type:** api  
**Preconditions:** Config contains a stock_industries entry referencing an ETF ticker that doesn't exist in `etfs.industry`.

**Steps:**
1. Add an entry to `stock_industries` mapping a stock to a ticker not in `etfs.industry` (e.g., `stock_industries: {AAPL: ["NONEXISTENT"]}`).
2. Attempt to start the backend
3. Observe the error output

**Expected outcome:** Backend startup fails with an explicit validation error about the missing ETF.  
**Pass criteria:** Error message indicates the invalid ticker reference; backend does not silently accept or create a default entry.

---

### TC-15 — Byte-identical scores: new metadata does not recompute rank

**Type:** artifact  
**Preconditions:** Backend has fresh scan records; a baseline comparison dataset exists without the metadata attached.

**Steps:**
1. Extract from the current scan: `SELECT ticker, name, score, rank, components, rs_vs_spy, dist_from_52w_high_pct, trend_label FROM sector_score_row ORDER BY rank`
2. Compare each field (except `description`, `members_json`) to a pre-metadata baseline
3. Verify every score, rank, and component is byte-identical

**Expected outcome:** Adding description and member metadata does not change any scored value.  
**Pass criteria:** All numeric fields (`score`, `rank`, `rs_vs_spy`, `dist_from_52w_high_pct`) and string fields (`components`, `trend_label`) match the baseline byte-for-byte; no rank reordering.

---

### TC-16 — Required journeys remain green (J-04: sector ranking unchanged)

**Type:** browser  
**Preconditions:** Frontend and backend are running; user is on `/sectors`.

**Steps:**
1. Navigate to `/sectors`
2. Inspect the ranked table row order
3. Verify the rows are ranked by score (highest score → lowest)
4. Spot-check that at least one sector ETF and one industry ETF are in their expected rank positions

**Expected outcome:** Sector/industry ETF ranking is unchanged from the previous iteration.  
**Pass criteria:** The ranked order matches the expected order from J-04 (no rows reordered or skipped).

---

## Summary

**Total test cases:** 16  
**API tests:** 8 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-13, TC-14, TC-15)  
**Browser tests:** 7 (TC-07, TC-08, TC-09, TC-10, TC-11, TC-12, TC-16)  
**Artifact checks:** 1 (TC-06 shares with API but listed for database verification)

**Key validation areas:**
- Config catalog structure and validation (malformed entries rejected)
- Member resolution from correct mappings (sector→`stock_sectors`, industry→`stock_industries`)
- Round-trip persistence and serve-through (snapshot immutability, no recompute)
- Frontend display of names, descriptions, and member lists with proper affordances
- Byte-identical scoring (no rank/metadata recompute in the read path)
- Explicit empty-state handling (unmapped ETFs, no fabricated members)
- Required journey stability (J-04, J-06, J-50 remain passing)
