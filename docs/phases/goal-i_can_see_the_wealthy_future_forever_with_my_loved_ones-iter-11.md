# Goal Iteration 11 — Sectors page: config-named/described ETFs with universe members (J-58)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 11
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-58
- **Required-still-passing journeys:** J-04 (Sectors leaderboard ranking/RS/dist/trend — same page), J-03 (Themes member pattern this mirrors), J-57 (themes expandable members — shares the helper convention), J-06 (score/membership consistency), J-02, J-05, J-13 (as-of), J-50 (hrefs carry `?asof`)
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **No order execution, no auto-trading, no brokerage integration, no capital deployment** — Trendora is decision-support and research only.
  - No machine-learning price prediction.
  - No social-media sentiment, and **no news/LLM catalyst enrichment in this session**.
  - Not the full US market, and **not a hand-picked list**: the universe is a reproducible, **rule-based liquidity / market-cap / price screen** recorded in config.
  - (Coherence anti-goals that bind this iteration:) The backend is the **single source of truth**; the frontend only re-formats values from the API and never recomputes a score, return, or bucket. **No scoring/threshold literal is hard-coded** — every tunable (now including industry names/descriptions + the stock→industry mapping) lives in `config.yaml`. **No fabricated data** — an ETF with no mapped universe member shows an explicit empty state, never invented members.

## RE-RUN NOTICE (read first)

This is a **re-run of iteration 11 with the SAME plan** — Target stays **J-58**, Depth stays **full**. The previous run of iter-11 **already implemented and verified J-58 end to end** (developer → reviewer → QA → browser-qa → coherence all PASSED; `coherence.md` returned **COHERENCE-PASS**, snapshot SHA `23832d73`). The engine then **aborted at the goal-evaluator step on an operational timeout — not a content failure** — so the evaluator never recorded J-58, and `journey-history.json` still lists it as `failing`. A single full-suite test failure (the QA fixture builder was missing the new `stock_industries` pruning) has since been **root-caused and fixed**. The correct action is to **re-affirm this spec and re-dispatch so the evaluator records J-58**, not to re-scope or switch targets. The implementation described in IN SCOPE below is already present on disk (config `etfs.industry` catalog + `stock_industries` mapping + validator; `SectorScoreRow.description`/`members_json`; `score_sectors` resolution; `snapshot_serving._sector_row` echo; `/sectors/page.tsx` member panel) — the full pipeline should re-verify it green (now with the fixture fix) rather than rebuild it.

## GOAL

On `/sectors`, every ranked ETF row is **named and described from config** (no more bare tickers like "KRE"), and each row's expanded panel lists its **universe members** — sector members from the existing `stock_sectors` mapping, industry members from a new config-curated stock→industry-group mapping (honestly labelled config-defined), with an explicit empty state when an ETF has no mapped member.

## BACKGROUND

J-58 is the last remaining failing journey with the smallest backend surface, and the iter-10 evaluator recommended it as the next target at **full** depth ("smallest backend surface, unblocks the Sectors page"). The lean view-transform vein (J-48/J-55/J-56/J-64/J-65) is exhausted; J-58 introduces new config **reference data** (industry ETF names/descriptions + a stock→industry-group mapping) plus a stored-once member list on each sector row, so it crosses config + backend + frontend and **requires the full pytest gate**. The work mirrors the already-passing J-57 Themes member pattern exactly (config-curated many-to-many membership, served-once member list, expandable `+n` panel with dated new-tab member links via `useAsOfHref`). The canonical compute path is `apps/backend/app/engine/sectors.py:score_sectors`; before this iteration an industry ETF's `name` fell back to the bare ticker and `etfs.industry` in `config.yaml` was a bare list (`SMH`, `KRE`, …), and `SectorScoreRow` carried neither a `description` nor a `members_json` column (those exist on `ThemeScoreRow`). The prior run already landed all of this (see RE-RUN NOTICE) and COHERENCE-PASS'd.

**Lessons that bind this iteration (apply them):**
- **Config fixtures need new required keys (project memory):** the new config structure for `etfs.industry` (list → catalog with name/description) plus the new `stock_industries` mapping section, AND the two new `SectorScoreRow` columns (`description`, `members_json`), must be present in **every** inline test config dict / row-construction site. Grep `etfs`/`stock_sectors`/`SectorScoreRow(` across `apps/backend/tests/` — there are **at least 6** files; the count GROWS, so grep, never trust a fixed list. **This is exactly the trap the prior run hit:** a QA fixture builder was missing the new `stock_industries` pruning and failed the full suite — that fixture has since been fixed; re-confirm the full sweep is consistent so the suite is green this time.
- **Backend test suite runtime (project memory / iter-2 lesson):** the full pytest suite is ~34–46 min and a subagent cannot finish it (10-min Bash cap; a dev-turn background run dies on turn-end). The developer runs the **targeted** modules (`test_sectors.py`, `test_db.py`, `test_config*.py`, `test_api_engine.py`) and hands the **full suite to the pump**. Never run two suites concurrently.
- **Snapshot immutability (coherence invariant 3):** `members_json` + `description` are a **stored copy** written once at `run_scan` time (like `ThemeScoreRow.members_json`), read verbatim by `/api/sectors` — never recomputed in the read path, never mutated after the run is created. The member list is config-derived reference data resolved at scan time and frozen into the immutable snapshot.
- **iter-5 nested-interactive hazard:** the member-ticker links and the `+n` toggle must live in the **separate, non-clickable expanded `<tr>`** (NOT nested inside the `role="button"` summary row), with `stopPropagation`, exactly as `/themes` does it. Re-use the `useAsOfHref` helper — do not author a second date-carrying path. (Already implemented this way in `/sectors/page.tsx`.)

## IN SCOPE

> Note: the prior run already landed every item below and they coherence-passed; the re-dispatch should verify them green (with the now-fixed QA fixture), correcting only any residual gap the re-run surfaces.

### Backend
- [ ] **Config (`config.yaml`, repo-root, loaded by `apps/backend/app/config.py`):** `etfs.industry` is a catalog mapping each industry ETF ticker → `{ name, description }` (mirroring `etfs.sector`'s ticker→name shape, extended with a description). A config section `stock_industries` maps each in-universe stock → one or more industry-group ETF tickers (many-to-many, like `themes` membership), honestly labelled config-defined. No name, description, or membership hardcoded in code. The config validator (`apps/backend/app/config.py`) types/validates the new shapes and raises an explicit `ConfigError`/`ValueError` on a malformed entry — `stock_industries` keys must be universe symbols and values must be `etfs.industry` tickers (no silent default).
- [ ] **Sectors engine (`apps/backend/app/engine/sectors.py:score_sectors`):** read each industry ETF's `name`/`description` from the new catalog (replacing the bare-ticker fallback); resolve each ranked ETF's **member list** — sector ETFs from the existing `stock_sectors` mapping (stocks whose sector == this ETF's sector name), industry ETFs from the new `stock_industries` mapping (stocks mapped to this ETF ticker) — as config-derived reference data. The score/rank/components/RS-vs-SPY/dist-52w/trend computation stays **byte-identical** (this is additive metadata only).
- [ ] **Model (`apps/backend/app/models.py`):** `SectorScoreRow` carries `description: Optional[str] = None` and `members_json: str = "[]"` (the stored-copy pattern already on `ThemeScoreRow`).
- [ ] **Persist + serve:** `run_scan` writes the description + member list into each stored `SectorScoreRow` (once, at scan time, into the immutable snapshot); `snapshot_serving._sector_row` / `sectors_payload` echo `description` + `members` verbatim from the stored row. `/api/sectors` shape gains `description` and `members` per row — no new endpoint, no recompute in the read path.
- [ ] **DB / fresh-boot:** a fresh DB and the existing seed compute the new columns on first scan (create-once); stored runs that predate the columns are handled honestly (NULL description → row still renders its ticker; empty member list → explicit empty state) without mutating prior snapshots (`members_json or "[]"` guard in `_sector_row`).

### Frontend
- [ ] **`apps/frontend/lib/api.ts`:** the `SectorRow` type carries `description: string | null` and `members: string[]`.
- [ ] **`apps/frontend/app/sectors/page.tsx`:** in each ETF row's expanded panel, render the config **description** alongside the existing `ticker — name` line, and an **expandable universe-member list** mirroring the J-57 themes pattern: a preview of the first `MEMBER_PREVIEW_LIMIT` (6) members, a `+n` control that reveals every remaining member in place (collapsible "Show fewer"), each member ticker a **dated new-tab link** built via `useAsOfHref` (`target="_blank"` + `rel="noopener noreferrer"`, carrying `?asof` while historical, clean at latest). Member links + the `+n` toggle live in the **separate non-clickable expanded `<tr>`** (iter-5 hazard) with `stopPropagation`. An ETF with **zero** mapped members shows an explicit honest empty state ("No universe members are mapped to this ETF" — never fabricated). Industry membership is labelled "Members (config-defined)" so the source is honest.

### New user-facing capability
The user can read what every sector and industry ETF on `/sectors` actually is (a plain-language name + description instead of a bare ticker like "KRE") and, by expanding a row, see exactly which universe stocks belong to that sector/industry group — each opening the dated stock detail in a new tab.

### New information displayed
Per ETF row (in the expanded panel): the config **description**; the **universe-member list** (sector members from `stock_sectors`; industry members from the new `stock_industries` mapping), honestly labelled config-defined, with an explicit empty state for an unmapped ETF.

### New user actions
Expand an ETF row's `+n` member control to reveal all members; click a member ticker to open its dated stock detail in a new tab.

### UI surface changes
`/sectors` only — the existing ranked table is unchanged; the **expanded panel** under each row gains the description line and the expandable member list. No new page, no nav change.

### Product surface delta
The Sectors leaderboard stops showing bare, un-explained industry tickers and becomes legible end-to-end — every ETF is named, described, and shows its membership, matching the legibility the Themes page already provides (J-57). No score, rank, or any canonical value changes.

### Blueprint conformance
All changes live on the existing **Sectors** Information-Architecture home (`/sectors`, nav-reachable, already J-04's home). No new top-level nav section, no new page, no moved home — additive only. The blueprint's Sectors IA line and Sector-score Data Contract row already register the two J-58 reference-metadata additions.

### Data-contract additions
No NEW canonical computed value (no score/return/bucket is introduced or recomputed). The additions are **reference metadata** attached to the already-registered **Sector/industry score** Data Contract row:
- **Industry-ETF display name + description** — config-defined reference data (`etfs.industry` catalog), resolved once by `sectors:score_sectors`, stored on each `SectorScoreRow`, served verbatim by `GET /api/sectors`. Read identically wherever shown; no second source.
- **Sector/industry ETF universe-member list** — sector members from the existing `stock_sectors` mapping, industry members from the new config-curated `stock_industries` mapping (many-to-many, like themes); resolved once by `sectors:score_sectors` into each stored `SectorScoreRow.members_json` (immutable snapshot copy), served verbatim by `GET /api/sectors`. Config-defined, honestly labelled; unmapped → explicit empty state, never fabricated.

These are already registered as additive notes on the existing Sector-score Data Contract row in `blueprint.md` (no new canonical-value row, no new endpoint).

## OUT OF SCOPE

- Any change to the Sector Score, rank, components, RS-vs-SPY, distance-from-52w-high, trend label, or bucketing — the scored values stay **byte-identical** (assert this in tests).
- A second/new endpoint for members or descriptions — they ride the existing `GET /api/sectors` payload.
- The jobs-pipeline cluster (J-59/J-60/J-66/J-67), the availability heatmap (J-61), the as-of calendar popover (J-62), and the event-study episode mode (J-63) — separate iterations.
- Any data-walled work (J-22/J-23/J-24) — unchanged, non-halting NA.
- Making the industry membership a *screen* (rule-based) — it is config-curated many-to-many reference data like themes, explicitly labelled config-defined (the rule-based liquidity screen anti-goal governs the **universe**, not this mapping).
- Sortable member columns or member search (no J-48-style view transform requested here).

## DEFINITION OF DONE

- [ ] J-58 passes via browser-qa-agent: every ranked ETF row shows a config name (no bare "KRE"); expanding a row shows its config description and its universe-member list; sector members come from `stock_sectors`, industry members from `stock_industries`; an unmapped ETF shows the explicit empty state; member tickers open the dated detail in a new tab (`?asof` while historical).
- [ ] Required-still-passing journeys remain green — especially J-04 (the same page's ranking/RS/dist/trend unchanged) and J-06 (no canonical value moved).
- [ ] No anti-goal violation introduced (single source of truth; no hardcoded names/mappings; no fabricated members; no recompute in the read path; snapshot immutability preserved).
- [ ] Unit/integration tests pass; **byte-identical** sector scores/ranks proven before-and-after (the additive metadata cannot move any canonical value); **full pytest suite green** with the now-fixed QA fixture builder (handed to the pump).
- [ ] Coherence audit returns COHERENCE-PASS (additive reference metadata on the existing Sector-score row; no second compute/serve path). *(Already COHERENCE-PASS in the prior run — re-confirm.)*
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-11-dev.md`.

## TESTING REQUIREMENTS

- **Browser (J-58):** load `/sectors`; assert an industry row (e.g. the row formerly bare "KRE") now shows a config name; expand a sector ETF row and an industry ETF row; assert the member list renders (sector members trace to `stock_sectors`; industry members trace to `stock_industries`); assert an unmapped ETF (if any) shows the explicit empty state and **zero fabricated** members; assert member-ticker anchors carry `target="_blank"` + `rel="noopener noreferrer"` and `href` carrying `?asof` while historical, clean at latest. Capture evidence with honest md5-distinct screenshots (iter-3/7/10 evidence-hygiene lesson — no byte-duplicate captures passed off as different surfaces).
- **Unit/integration:**
  - `test_config*.py` — the new `etfs.industry` catalog shape and `stock_industries` mapping validate; a malformed entry (bad key not in universe / value not an `etfs.industry` ticker / missing name) raises the explicit config error (no silent default).
  - `test_sectors.py` — `score_sectors` resolves each industry ETF's name/description from config and each ETF's member list from the correct mapping (sector→`stock_sectors`, industry→`stock_industries`); **assert the scores/ranks/components are byte-identical** to a baseline with the metadata stripped (the no-recompute guard).
  - `test_db.py` / `test_api_engine.py` — `SectorScoreRow` round-trips `description` + `members_json`; `/api/sectors` echoes them verbatim from the stored snapshot; a re-served stored run is byte-identical (snapshot immutability).
  - **Fixture sweep (the prior run's failure point — verify it is closed):** every inline test config dict that carries `etfs`/`stock_sectors`, and every QA/fixture config builder, gets the new `etfs.industry` catalog + `stock_industries` section (incl. the `stock_industries` pruning the prior run was missing); every `SectorScoreRow(...)` construction site gets the new columns. Grep `etfs`/`stock_sectors`/`SectorScoreRow(`/`stock_industries` across `apps/backend/tests/` — don't trust a fixed list (≥6 files).
- **Error cases:** malformed `etfs.industry` entry (missing name) → explicit config error; `stock_industries` key not in universe or value not an `etfs.industry` ticker → explicit config error; an industry ETF with no `stock_industries` member → empty member list → explicit UI empty state (never fabricated); a stored run predating the columns → NULL description / empty members rendered honestly without mutation.

## NOTES

- **Re-run, same plan.** See RE-RUN NOTICE at the top: J-58 was fully built and COHERENCE-PASS'd in the prior iter-11 run; the engine aborted at the evaluator on an operational timeout, and the one full-suite fixture failure has been fixed. Target = J-58 and Depth = full are unchanged by design. The pipeline should re-verify the existing implementation green and let the evaluator record J-58 — not re-scope.
- Depth = **full** per the iter-10 evaluator's explicit recommendation (new config reference data + backend + new model columns require the pytest gate; lean is not sufficient). Prior verdict was CONTINUE, not ESCALATE.
- Single-journey iteration (tight, easy to score) — the highest-risk jobs-pipeline cluster (J-59/J-60/J-66/J-67) is deliberately deferred to a later full iteration; J-58 is the smallest backend surface and unblocks the Sectors page first, per the evaluator.
- The implementation mirrors the **J-57 Themes** member pattern verbatim (`MEMBER_PREVIEW_LIMIT=6`, the expandable `+n` panel, the dated new-tab `useAsOfHref` member links, the separate non-clickable expanded `<tr>` — iter-5 lesson). This keeps J-50/J-54/J-57 consistent and the coherence surface clean.
- The blueprint's J-58 `[TARGET]` notes on the Sectors IA line and the Sector-score Data Contract row already register the two reference-metadata additions (additive edits, no nav-skeleton change → no re-approval needed). No `blueprint.reapproval-requested` marker is written.
