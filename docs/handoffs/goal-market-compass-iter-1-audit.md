# goal-market-compass-iter-1 Audit Report

**Date:** 2026-08-20
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-01's backend half is correct and is now **verified live, not merely unit-tested**: on the fresh
2026-08-12 run, `GET /api/stocks` serves `0/539` null sectors (0.00% vs. the 78.4% baseline, target
≤5%), and a full DOM sweep of all 539 leaderboard rows finds zero "Unassigned". The disclosure half
shipped **invisible** — nested inside a section the J-22 honest-universe gate strips from every
response, so TC-5 as the spec words it ("given `GET /api/methodology` is fetched … the response
contains a disclosure") did not hold, and its API-layer test silently `pytest.skip()`ped. I fixed
that during this audit (B1); the disclosure now renders on `/methodology` and TC-5 passes
unconditionally. Remaining gaps are honest and non-blocking: the browser-QA lane's own J-01
precondition is destructive and unexecutable in this environment (T2), and TC-3's honest-null case
has no live counterexample because every resolved member is now covered by one of the two sources.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (fixed): the two-source disclosure shipped unreachable — TC-5 did not hold at the
layer it is specified against**

`app/engine/methodology.py` put `sector_basis` inside `_universe_selection()`'s returned dict. That
whole section is popped by the J-22 honest-universe gate at `apps/backend/app/api/methodology.py:41`
(and identically by the MCP tool at `app/mcp/tools.py:701`) whenever `data/seed/universe.json` is
absent — which is this repo's actual, permanent state (confirmed: `git ls-files apps/backend/data/seed/`
lists `meta.json`, `macro/`, `prices/`, `universe_pool.csv`, and no `universe.json`).

Consequences, all verified rather than inferred:

- `GET /api/methodology` served top-level keys `['entries', 'glossary', 'intro']` — no
  `universe_selection`, therefore no `sector_basis`. The spec's TC-5 is worded against exactly this
  call, so **the DEFINITION OF DONE item "TC-1 through TC-8 all hold" was false.**
- The API-layer TC-5 test guarded itself with `pytest.skip()` on the same gate, so the failure was
  invisible in a green test run. A test that skips in the only environment that exists is not
  coverage.
- The spec's own "New information displayed" and "UI surface changes" deliverables were undelivered:
  no user could read the disclosure on `/methodology` (browser-QA independently confirmed
  `[data-testid="universe-sector-basis"]` absent, its UT-J-01 step 4 "not observable").

The dev handoff documented this honestly as out-of-scope, but documenting an undelivered deliverable
does not deliver it — especially since the phase spec explicitly authorised the alternative:
*"Extend the methodology universe/data section (`_universe_selection` **or a sibling section**)"*.

**Fix applied.** `sector_basis` moved out of the gated section into the sibling top-level key the
spec permitted:
- `apps/backend/app/engine/methodology.py:73` emits `payload["sector_basis"]`, produced by the new
  `_sector_basis()` (`:79`) — same module, same endpoint, same single config read, one home only
  (removed from `_universe_selection`'s dict; a new test asserts it is never duplicated back).
- `apps/backend/app/api/methodology.py` gate **logic unchanged** — only a docstring note recording
  that the gate is scoped to the *screen claim* and must not pop `sector_basis`. This preserves J-22
  exactly: the suppressed claim is "the universe is a reproducible screen result", while this prose
  claims only how a descriptive label resolves from two sources that both exist today (the curated
  config map and the committed `universe_pool.csv`).
- Frontend: `MethodologyCatalog.sector_basis?: string` (`apps/frontend/lib/api.ts:1337`) and a
  standalone `SectorBasisCard` (`apps/frontend/app/methodology/page.tsx:293`), rendered
  unconditionally rather than inside the gated `UniverseSelectionCard`.

**Verification (per the post-fix contract):**
- `pytest tests/test_methodology.py tests/test_api_methodology.py -q` → **25 passed, 0 skipped, 0
  failed** (previously 22 passed / **1 skipped** — the skip was TC-5 itself).
- Live: `curl http://localhost:8255/api/methodology` → top-level keys
  `['entries', 'glossary', 'intro', 'sector_basis']`, full prose served, `universe_selection` still
  correctly absent (gate intact).
- Live browser at 1440×900: `[data-testid="universe-sector-basis"]` present and visible (top 318px,
  height 144px), full prose rendered, `[data-testid="universe-selection"]` still absent, no error
  card, glossary + 9 entry cards intact. Evidence:
  `reports/qa/goal-market-compass-iter-1-evidence/AUDIT-01-methodology-sector-basis-visible.png`.
- `tsc --noEmit` → exit 0.
- Two regression tests added: `test_sector_basis_is_a_sibling_of_universe_selection_not_nested_in_it`
  and `test_sector_basis_survives_the_honest_universe_gate`.

**B2 — OBSERVATION: `resolve_pool_sector` rebuilds its valid-sector set per row and would silently
degrade on a one-shot iterable**

`apps/backend/app/engine/universe_screen.py:124` evaluates `set(valid_sectors)` inside the per-row
call, and `pool_sector_map` (`:127`) calls it once per pool row — 548 set rebuilds per invocation of
an 11-element set. Harmless today. The latent trap: the parameter is typed `Iterable[str]`, so a
generator would be consumed by the first row and every subsequent row would silently resolve to
`None` — a whole-pool coverage collapse with no exception. The sole caller
(`scoring.py:303-304`) passes `cfg.etfs.sector.values()`, a re-iterable dict view, so nothing is
broken now. Not fixed (OBSERVATION-level; fixing is scope creep). One-line fix when next touched:
hoist `valid = set(valid_sectors)` into `pool_sector_map` and pass the materialised set down.

**B3 — OBSERVATION: the performance note in the dev handoff is measured and is a non-issue**

The handoff flagged the extra per-call `read_pool()` as an open question. Measured:
`pool_sector_map()` = **0.58 ms/call**, i.e. ~4.3 s added across an entire ~7,500-date 30-year
cadence rebuild. No action needed; recorded so a future perf pass does not re-open it.

**B4 — OBSERVATION: `sector_basis` was added to `UniverseSelectionCfg` as a required field, which
breaks frozen archived drill configs**

`apps/backend/app/config.py:1807` makes `sector_basis: str` required. `config.yaml` was updated, and
`methodology.universe_selection` is `Optional[...] = None` so configs omitting the block are fine.
But frozen ops-hardening drill copies do carry the block without the new key — confirmed:
`runs/goal-ops-hardening-iter-43/fault-drill/config.faultdrill.yaml` has `universe_selection` and no
`sector_basis`, so loading it now raises a `ValidationError`. These are archived artifacts from a
closed session, loaded by no product path or test; flagged only so a future drill replay is not
mystified.

### Frontend Findings

**F1 — OBSERVATION: the Sector filter's "Unassigned" option is now correctly absent, and goal.md's
J-01 step 2 can no longer be executed as literally written**

goal.md's J-01 step 2 says *"select the Sector filter's 'Unassigned' option; assert the Unassigned
share … is at most 5%"*. The option list is derived from the data present
(`apps/frontend/app/stocks/page.tsx:402-405`, `Array.from(new Set(rows.map(r => sectorLabel(r.sector))))`),
so with zero unassigned rows the option honestly disappears — never fabricated, exactly the behaviour
the plan required ("never fabricated to zero if a genuine gap remains" — and no gap remains). The
assertion itself is satisfied at 0%; I verified it instead by a full DOM sweep of all 539 rendered
rows. The journey step's wording should be amended to "assert the Unassigned share is ≤5%, selecting
the filter option only if it is present".

### Test Findings

**T1 — GAP: the TC-8 test mutates a session-scoped shared fixture DB and never restores it**

`apps/backend/tests/test_scoring.py:578` (`test_historical_row_sector_not_rewritten_by_pool_fallback`)
rewrites a stored `ScannerResult`'s `sector` and `record_json` and `session.commit()`s at `:603-605`
with no restore. `loaded_engine` is `scope="session"` (`apps/backend/tests/conftest.py:41`), so the
mutation persists for the remainder of any full-suite run.

I checked the blast radius rather than assuming it: the test is last in its file, and of the six
`loaded_engine` files that sort after `test_scoring.py`
(`test_sectors`, `test_staging_ledger_routing`, `test_themes`, `test_triad_scan`,
`test_universe_resolver`, `test_universe_screen`) none reads `ScannerResult.sector` or `record_json`
content — `test_universe_screen.py:86` only counts rows, which the mutation does not change. So no
current test provably breaks. It remains latent pollution that will bite whenever a sector-sensitive
test is added downstream. Not fixed: GAP-level, and verifying a fix would require re-running
`test_scoring.py`'s ~50-70-minute `loaded_engine` fixture, which this audit will not spend. Fix when
next in that file: restore the original `sector`/`record_json` in a `finally`.

**T2 — IMPORTANT (gap, not fixable in source): the J-01 browser precondition is destructive and
unexecutable in this environment — it caused unrecoverable data loss**

The browser-QA verdict for this iteration was **FAIL**, and its root cause is the journey definition,
not the product. goal.md's J-01 step 1 (and the spec's TESTING REQUIREMENTS) mandate a seed-safe
Remove of "the last two trading days" followed by a backfill of the same range. In this environment
those two dates (2026-08-13/14) were **entirely user-added bars with no committed seed beneath them**
(`seed_latest_date` is 2026-08-12), so:

- The Remove permanently destroyed 1,174 bars, 18 snapshots and 30,439 forward returns.
- The bars-only "Backfill snapshots" job then correctly refused to fabricate snapshots for dates that
  no longer had bars (`data_manager._trading_days` derives the calendar from stored SPY bars), so it
  returned "no new snapshots", `0/0`.
- Restoring them would require the "Fetch + backfill" job kind, which makes live Yahoo Finance calls —
  correctly refused by the browser-QA agent under AG-9.

The product behaved correctly and honestly at every step; the *precondition* is unsafe. It blocked
UT-04/UT-05 (both P1) and produced the FAIL. **This is why DEFINITION OF DONE item 2 ("J-01 passes
via browser-qa-agent") is formally unmet, even though I have since verified the journey's substance
live** (see §3). Amending it requires an owner/goal.md edit, which is out of an auditor's remit —
recommended wording in §5.

**T3 — OBSERVATION: both pre-existing test failures the handoff flagged are genuinely unrelated —
independently confirmed, not accepted on the handoff's word**

- `test_no_magic_numbers::test_engine_calc_code_has_no_magic_numbers`: re-run here; offenders are
  only in `indicators.py`, `forward_testing.py`, `research.py`. `git diff --name-only HEAD -- apps/`
  shows all three untouched by this iteration *and* by my audit fix. `methodology.py` and
  `scoring.py`, which the iteration does touch, are not among the offenders.
- `test_scoring::test_risk_budget_values_ride_the_row_but_enter_no_score`: the triggering value is
  `config.yaml:745` `atr_pct: 0.15`, which `git blame` traces to `63cba98d7` (2026-05-29) — three
  months old; the iteration's `config.yaml` diff is `10 insertions, 0 deletions` and contains no
  `scores`/`weights`/`atr_pct` line; and the test itself was introduced by `b6f22d49` (2026-07-15) in
  the archived mcp-loop session. Genuinely pre-existing. The handoff's diagnosis (the assertion set
  wrongly includes deliberately-reused `atr_pct`/`downside_vol`) is plausible and belongs in a
  tracked backlog item, not in J-01.

**T4 — OBSERVATION: the reviewer's one open issue is now closed with evidence**

The reviewer's MINOR note was that `tests/test_sectors.py` (named in the DoD's no-regression list)
was never run. I ran its two fixture-free config-construction tests — the only plausible break-point
for a newly-required `sector_basis` field — `2 passed`. The remaining seven exercise
`app.engine.sectors` (sector-ETF ranking), a module absent from the changed-files list, behind the
~1-hour `loaded_engine` fixture; not re-run, and no mechanism exists by which they could be affected.

---

## 3. Domain Assessment

**The descriptive-only guarantee (TC-4) is structural, not merely empirical — this is the strongest
result of the audit.** I traced `score_stocks` end to end rather than trusting the fixture:
`pool_sectors` has exactly three occurrences in `scoring.py` — the import (`:49`), the compute-once
block (`:303-304`), and one read at `:458` inside the row's `"sector"` field. I then read the
remainder of the function past row assembly: the risk-budget percentile pass reads `row["risk_budget"]`
only, the sort key is `(-row["leadership"]["score"], row["ticker"])`, and ranks are positional.
**`row["sector"]` is never read again.** The fallback therefore *cannot* move a score, bucket, or
setup status — the monkeypatch fixture confirms a property the code structure already guarantees.
`Stock.sector_id` / `stock_sector_etf` / `rs_sector` are untouched separate machinery.

**Coverage is verified on real data at three independent levels.** (1) Applying the exact production
expression `cfg.stock_sectors.get(t) or pool_sectors.get(t)` over the real 539-member resolved
universe: `0/539` unassigned. (2) Live API on the fresh run: `GET /api/stocks` at as-of 2026-08-12
serves `0/539` null. (3) Full browser DOM sweep of all 539 rendered leaderboard rows: zero
"Unassigned". Target was ≤5%; delivered 0.00% from a 78.4% baseline.

**A genuine fresh run exists, produced offline by the product's own boot path.** When I launched
`scripts/dev.sh` (the host-guarded launcher — AG-10 respected; no launch script was modified), the
backend lifespan's persist-latest-snapshot step created run 3081 for as-of 2026-08-12 under this
iteration's code, from committed seed bars with `provider: seed` (AG-9 respected — no network). This
is the fresh run the browser-QA lane failed to produce, obtained without any destructive action.

**Historical immutability (TC-8) is proven on production data, not just by a synthetic test.** Run
3049 (as-of 2026-08-11, created 2026-08-14, scored under the pre-fallback code) still reads
`422/539 = 78.29%` null after this iteration shipped, while run 3081 (as-of 2026-08-12, created
under the new code) reads `0/539`. Stored rows are served verbatim and are never re-resolved.

**Cross-surface consistency (TC-2) holds on all three surfaces.** DELL (curated) = `Technology` and
GRMN (pool fallback, previously "Unassigned") = `Consumer Discretionary`, identical across the
`/stocks` leaderboard cell, the `/stocks/GRMN` detail page (which shows the sector and contains no
"Unassigned"), `GET /api/stocks`, and `GET /api/stocks/{ticker}`.

**AG-8 consumer re-validation — done, and the iteration did not do it.** AG-8 requires that
"consumers of widened fields are re-validated". `ScannerResult.sector` just went from ~21.7% to 100%
populated on new runs, and it has real downstream consumers the iteration never exercised:
`research.py:2355` `_event_study_by_sector` and `forward_testing.py:2202`. I exercised the live path:
`GET /api/research/event-study` → HTTP 200 in 13.2 s, 8 sector rows, honest `low_sample: true` and
`risk_adjusted: null` on thin samples. No crash, no fabricated value. AG-8 holds — but it holds by
luck of a well-built consumer, not because this iteration checked.

**An honest limitation the disclosure does not yet cover (worth a future card).**
`_event_study_by_sector` aggregates members across many as-of dates and skips rows with
`sector is None`. Pre-iteration dates therefore contribute only the 122 curated names while
post-iteration dates contribute all 539 — the by-sector evidence silently spans two labelling
regimes across a date boundary. This is the direct and *deliberate* consequence of TC-8's immutability
requirement (the spec chose not to rewrite history, correctly), and every displayed number is a
correct aggregate of stored rows, so no anti-goal is breached. But the new `sector_basis` prose
discloses only that the mapping is *current-only*; it does not disclose that *coverage itself* changed
on a date boundary. Recommended as a backlog card alongside B-114.

**Anti-goals.** AG-3 correctness verified live at three levels (above). AG-7: no credential, key, or
token anywhere in the diff. AG-9: the fallback reads a committed local CSV; the fresh run used
`provider: seed`; no network call added. AG-10: `git diff HEAD -- scripts/ project-extensions/` is
empty — no HOST-GUARD block touched, and all heavy work ran inside the script-launched backend.
AG-11: the change adds a descriptive string, no composite number. AG-12/AG-13: not implicated.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/backend/app/engine/methodology.py` | `sector_basis` removed from `_universe_selection()`'s dict; new `_sector_basis()` producer; `build_catalog` emits it as a sibling top-level key (the spec's own permitted alternative) so the J-22 gate cannot hide it |
| 2 | Important | `apps/backend/app/api/methodology.py` | Docstring only — records that the gate is scoped to the screen claim and must not pop `sector_basis`. **Gate logic unchanged; J-22 fully preserved** |
| 3 | Important | `apps/frontend/lib/api.ts` | `sector_basis` moved off `UniverseSelection` onto `MethodologyCatalog` as an optional top-level field |
| 4 | Important | `apps/frontend/app/methodology/page.tsx` | Disclosure moved out of the gated `UniverseSelectionCard` into a standalone, always-rendered `SectorBasisCard` |
| 5 | Important | `apps/backend/tests/test_api_methodology.py` | TC-5 API test de-skipped and re-pointed at the top-level key (it could never run before); added `test_sector_basis_survives_the_honest_universe_gate` |
| 6 | Important | `apps/backend/tests/test_methodology.py` | TC-5 catalog tests re-pointed at the top-level key; added `test_sector_basis_is_a_sibling_of_universe_selection_not_nested_in_it` (one home, never duplicated) |
| 7 | — | `docs/handoffs/…-dev.md`, `…-frontend.md` | Supersession notes added: their "cannot be visually verified" Known Issue no longer holds for `sector_basis` |

**Evidence for every fix above:** `pytest tests/test_methodology.py tests/test_api_methodology.py -q`
→ 25 passed / 0 skipped / 0 failed; broader batch with `test_glossary.py test_config.py
test_no_magic_numbers.py` → 117 passed, 1 failed (the pre-existing magic-numbers failure in three
untouched files, T3); `tsc --noEmit` → exit 0; live `curl` and live Chrome DOM assertions as recorded
in B1.

**Scope check on my own diff:** `git diff HEAD` over the six files I touched is 143 insertions /
5 deletions, entirely the relocation, its docstrings, and its tests. Nothing else changed.

**Environment note (deliberate, disclosed):** this audit left the dev services running
(backend :8255, frontend :3255), and the backend's own boot created snapshot run 3081 for as-of
2026-08-12 — an additive, offline, seed-provider run under this iteration's code. No stored row was
modified or deleted by the audit.

---

## 5. Recommended Next Step

**Proceed to the next iteration** (goal.md's suggested J-02/J-03/J-04 engine cluster). J-01's goal is
achieved: the pool-CSV fallback is correct, descriptive-only by construction, live-verified at 0.00%
Unassigned on a fresh run, and the two-source disclosure is now actually readable on `/methodology`.

Carry these forward — none blocks the next iteration:

1. **Amend J-01's step 1 in `docs/goal.md` before it is re-run (owner action, T2).** The current
   wording is destructive and unexecutable here. Replace "the last two trading days" with a range
   that has committed-seed bars beneath it (`seed_latest_date` is 2026-08-12), or drop the
   Remove+backfill precondition entirely — the backend's own boot produces the latest missing
   snapshot from seed bars, which is how this audit obtained its fresh run. Also soften step 2 so the
   "Unassigned" filter option is selected only when present (F1).
2. **Note the unrecovered data loss (T2).** Bars, snapshots and forward returns for 2026-08-13/14 are
   permanently gone; only a live "Fetch + backfill" (network, requires a goal.md amendment under
   AG-9) can restore them. The dataset is currently sound and current to its seed at 2026-08-12.
3. **File a backlog card next to B-114** for the by-sector coverage discontinuity described in §3 —
   pre-iteration dates contribute 122 names to by-sector evidence, post-iteration dates contribute
   539, and nothing discloses that boundary.
4. **Two small hygiene items when next in those files:** restore the mutated row in the TC-8 test
   (T1), and hoist the `set(valid_sectors)` build out of the per-row path (B2).
5. **Consider running the offline "Expand" job** to build `data/seed/universe.json` — no journey
   requires it, but it would make the pre-existing Universe Selection card (membership rule,
   thresholds, per-date rule) visible on `/methodology` for the first time. This is now genuinely
   optional: the J-01 disclosure no longer depends on it.
