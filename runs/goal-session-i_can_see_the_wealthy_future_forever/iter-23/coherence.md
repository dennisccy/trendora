**Verdict:** COHERENCE-PASS

## Coherence Audit — iter-23 (goal-i_can_see_the_wealthy_future_forever)

**Iteration:** 23
**Target journey:** J-35 (Expand-universe job)
**Snapshot SHA:** b14b739fafcf42a6ab1016d567ecdec0c4f80ea7
**Audited:** 2026-06-07

---

## Step 1 — Data Contract check

### Registered values examined

**J-22 — Universe membership (single source: `universe.json` → `config.universe.symbols`)**

The Data Contract for J-22 specifies that the universe value is served by `GET /api/methodology`
(`resolved_size` = `len(config.universe.symbols)`) and `GET /api/data` (`universe_count` =
`len(cfg.universe.symbols)`), both reading the same resolved `config.universe.symbols` field.

The iter-23 diff introduces `_merge_committed_universe` in `apps/backend/app/config.py` (line ~1190),
which runs only at config load time for the DEFAULT config and merges `universe.json` members INTO
`config.universe.symbols` (a union, not a recompute). Both `universe_count` and `resolved_size`
continue to read `len(cfg.universe.symbols)` — the same field, same module path. No second universe
computation is introduced. The merge is a READ of the committed artifact into the config object that
all endpoints already read — consistent with "the running app reads this; it never recomputes membership."

**J-35 — New values (screen result + run row)**

Two new descriptive job-control values are introduced:
- Per-candidate screen result (passers + omitted-with-reason): surfaced on `GET /api/data/jobs/{job_id}`
  via `JobProgress.passers`, `omitted_total`, and `omitted` — the blueprint's J-35 Data-Contract row
  registers exactly this canonical path.
- Expand-kind run row: recorded on `GET /api/data` (append-only `DataProviderRun`) — also registered
  in the J-35 row.

Neither is a duplicate of any previously registered value. Both are genuine NEW descriptive job-control
values.

**`screen_reasons` — single-source check**

The diff removes the `screen_reasons` function body from `apps/backend/scripts/screen_universe.py` and
places ONE definition in the new `apps/backend/app/engine/universe_screen.py:26`. The script now
re-exports it: `from app.engine.universe_screen import screen_reasons  # noqa: ... (re-exported)`.
The data_manager imports it: `from app.engine.universe_screen import ... screen_reasons`. No second
definition exists anywhere in the tree — `grep "def screen_reasons"` returns exactly one hit:
`apps/backend/app/engine/universe_screen.py:26`. This is a consolidation from two copies to one, which
IMPROVES coherence (removes the prior duplicate). Not a violation.

**J-33 / J-34 — Import provider catalog + resumable checkpoint**

No new computation paths for these registered values are introduced. The `expand` job kind reuses the
existing `_FETCH_KINDS` chunked-fetch engine (`_chunk_plan`, `_start_checkpoint`, `_advance_checkpoint`,
`_finalize_checkpoint`, the `RateLimitError` → backoff → `resumable` path) and the existing
`import_checkpoints` table — no fork. `compute_provider_availability` is unchanged.

**Other canonical values (scores, buckets, setups, forward returns, factor lab, event study)**

The diff touches no file under `app/engine/` that computes scores, buckets, regime, sectors, themes,
forward returns, or research analytics — only `data_manager.py` and the new `universe_screen.py`. No
new computation path for any blueprint-registered value was found.

**Conclusion — Step 1:** No duplicate computation, no non-canonical source, no unregistered value that
duplicates an existing concept. The two new J-35 descriptive values are registered in the blueprint's
Data Contract. **No Part A violation.**

---

## Step 2 — Information Architecture check

**New routes/pages:** None. The diff adds no directory under `apps/frontend/app/`. The filesystem
confirms the route set is unchanged: `backtest`, `data`, `methodology`, `research`, `scanner-runs`,
`sectors`, `stocks`, `themes`, `watchlist` — identical to the prior iteration.

**Changes to `/data` page:** Additive only — a new `expand` option in the existing job-kind `<Select>`,
source-eligibility gating, and the `ExpandScreenResult` sub-component on the existing job card. All
changes live within the existing `/data` page component (`apps/frontend/app/data/page.tsx`).

**Navigation reachability:** The sidebar (`apps/frontend/components/sidebar.tsx`) carries
`{ href: "/data", label: "Data Manager", icon: Database }` — a persistent top-level sidebar entry.
`/data` is 1 click from any page. The `expand` job kind is a new option within that existing page
(0 additional clicks beyond reaching `/data`). Reachability is ≤ 2 clicks — confirmed.

**No parallel shell:** No new layout wrapper was introduced. The expand feature lives inside the
established `/data` page shell.

**No duplicate home:** The expand job kind's progress and screen-result surface is on the existing
`/data` job card — consistent with the blueprint's IA note: "additive only, no new page/route/nav entry."
The universe value itself continues to be served by the existing J-22 homes (`/api/methodology`,
`/api/data`) — no second home for any entity.

**Conclusion — Step 2:** No hidden feature, no undiscoverable route, no duplicate home, no parallel
shell. **No Part B violation.**

---

## Step 3 — Advisory observations (WARN only)

None identified. The `ExpandScreenResult` component follows the same visual patterns (badges, alert
blocks, scrollable lists) established by the existing job-card components. The panel title text
("Start a fetch / backfill / expand job") is updated consistently. The `DataJobKind` union type in
`lib/api.ts` gains `"expand"` — consistent with all other kind strings.

The new `apps/backend/app/engine/universe_screen.py` module consolidates `screen_reasons` from two
locations into one — this is an improvement over the prior state. No advisory note warranted.

---

## Summary

| Check | Result | Notes |
|---|---|---|
| Part A — Data Contract | PASS | `screen_reasons` consolidated to one definition; J-35 new values registered; universe_count single source preserved |
| Part B — Information Architecture | PASS | No new routes; expand is additive within `/data`; sidebar link unchanged |
| Part C — Advisory | PASS | No formatting drift or labelling inconsistency observed |

**Verdict: COHERENCE-PASS** — iter-23 (J-35 Expand-universe) is coherent with the blueprint. All
changes are additive within the existing approved `/data` (Data Manager) home; no value is computed
or served from a new non-canonical path; navigation is unchanged.
