**Verdict:** COHERENCE-PASS

# Coherence Audit — iter-12 (Methodology / Glossary, J-12)

- **Session:** i_can_see_the_wealthy_future
- **Iteration:** 12 — Methodology / Glossary: a config-backed catalog of every setup status + the VCP pattern, surfaced as `/methodology` AND inline `/stocks` badge tooltips (J-12, the final Must-have)
- **Snapshot SHA audited:** `7fa50cac8ed477f6fa0d116ab9ee43410a96b0e6` (`git diff <sha>` + uncommitted working tree)
- **Auditor:** coherence-auditor

This is the goal-completing iteration: it adds one read-only, config-backed glossary surface and changes
no canonical computation. The design is deliberately additive — it rides existing seams (the new value
reads config, not the scoring engine; the existing files keep an empty diff). I checked the landed diff
against the blueprint's pre-registered iter-12 Data-Contract row (`blueprint.md:97`), the new IA home
(`blueprint.md:44,76`), and the iteration spec's "Data-contract additions" / "Blueprint conformance".
**No objective Part A or Part B violation.** Only minor advisory notes.

---

## Part A — Data Contract (the "numbers don't match" gate) — PASS

The blueprint registers ONE additive value this iter: **Setup & pattern catalog** (`blueprint.md:97`) →
computing module `app.engine.methodology:build_catalog(config)`, serving endpoint `GET /api/methodology`.
The landed code conforms exactly.

### A1 — The catalog computes NO score; it reads config and resolves refs ✓
- `build_catalog(config)` (`apps/backend/app/engine/methodology.py:36-67`) iterates `config.methodology.entries`
  and, per threshold row, either passes a `text` rule verbatim or resolves a `ref` to its **live config
  value** via `resolve_ref` (`methodology.py:30`). It computes/stores no score/return/bucket — there is
  no scoring/regime/forward-testing import (only `Config, MethodologyThreshold, resolve_ref` from
  `app.config` and `ALL_STATUSES` from `app.engine.setups`, `methodology.py:18-19`). This is a pure
  config read + format, exactly as registered.
- **Matching-config keystone (no drift, no re-typed number).** `resolve_ref` (`apps/backend/app/config.py:441-451`)
  traverses the **loaded `Config`** tree by dotted path and returns the same value the engines read —
  the displayed threshold IS the canonical value, not a second copy. Confirmed against `config.yaml`: every
  numeric `ref` targets a real canonical block — `decision_rules.actionable.{leadership,entry,risk}`,
  `decision_rules.watch.leadership`, `decision_rules.extended.{leadership,entry}`, `decision_rules.avoid_risk`
  (the SAME `decision_rules` block `app.engine.setups:classify_setup` reads) and
  `patterns.vcp.{min_contractions,max_base_depth_pct,contraction_shrink_ratio,max_last_contraction_pct,pivot_proximity_pct,volume_dryup_ratio}`
  (the SAME `patterns.vcp` block `app.engine.patterns:detect_vcp` reads). `methodology.py` holds no
  threshold literal (added to `CALC_FILES`, `test_no_magic_numbers.py` diff).
- **Honest-failure, never a silent number.** A boot `model_validator` (`config.py:552-568`,
  `_methodology_refs_resolve`) resolves every threshold `ref` and raises `ValueError`→`ConfigError` on any
  unresolvable path — an unresolved reference fails the boot loudly (anti-goal: No fabricated data).

### A2 — The catalog `meaning` is a DISTINCT value, not a second source of `setup.reason` ✓
This was the spec's explicit coherence question. The catalog `meaning` is the **generic** definition of a
status/pattern (served by `/api/methodology`); the per-row `setup.reason` is the **per-stock,
component-enriched** sentence (from `setups._REASONS`, served on the stock row). They are different
displayed values, not two sources of one:
- `setups.py` has an **empty diff** — `_REASONS` is untouched (confirmed below).
- On `/stocks`, the per-row reason still renders in the Reason column from `row.setup.reason`
  (`apps/frontend/app/stocks/page.tsx:304`); the badge tooltip renders the catalog `meaning`
  (`page.tsx:291`, `setupMeaning.get(row.setup.status)`). Two columns, two sources, no overlap.

### A3 — No existing canonical value gains a second computation/source (empty-diff keystone) ✓
`git diff <sha> --stat` over the engine + every pre-existing router is **empty** — `models.py`,
`scanner.py`, `scoring.py`, `setups.py`, `patterns.py`, `forward_testing.py`, and all nine routers
(`dashboard`, `stocks`, `sectors`, `themes`, `runs`, `system_health`, `backtest`, `watchlist`, `health`)
are byte-unchanged. So no per-stock score, bucket, setup status, VCP flag, theme membership, sector/theme
score, regime, forward-return aggregate, scorecard, or watchlist value is recomputed or re-served from a
new path. J-01–J-11 and J-13–J-16 cannot structurally regress. `GET /api/methodology` is the sole new
endpoint (`main.py:17,77`), serving `build_catalog(get_config())` verbatim (`api/methodology.py:21`).

### A4 — The `/stocks` filter-vocabulary change introduces no divergence ✓
The Setup-filter dropdown options now come from the catalog's `kind:setup` entries
(`stocks/page.tsx:111-117`), with graceful fallback to the statuses present in the data on a catalog
failure (protects J-02/J-15). This is **display vocabulary** (the list of selectable statuses), not a
recomputation of any stock's status — the actual filter still matches on the **server-computed**
`row.setup.status` (`stocks/page.tsx:133`), and the catalog itself reads the canonical `ALL_STATUSES`
(`methodology.py:19,56`) so the vocabulary cannot diverge from the engine's status set. The catalog is
fetched non-blocking and independently of the as-of date (`stocks/page.tsx:82-90`). `lib/api.ts`
`fetchMethodology` hits the one canonical `/api/methodology` (`lib/api.ts:529-531`); no client-side
computation.

**Unregistered values:** none. The one new displayed value (the catalog) is registered in the Data
Contract this iter (`blueprint.md:97`). No A5 note.

---

## Part B — Information Architecture (the "where do I find it / why is it everywhere" gate) — PASS

The blueprint adds ONE new home this iter: **Methodology** → `/methodology` (`blueprint.md:44,76`).

### B1 — Navigation path exists (≤2 clicks) ✓
`apps/frontend/components/sidebar.tsx:37` adds `{ href: "/methodology", label: "Methodology", icon: BookOpen }`
to the persistent sidebar `NAV` array, placed after Watchlist (matches the goal.md IA ordering and the
updated blueprint skeleton). It is a **top-level link → 1 click** from any page; `isActive`
(`sidebar.tsx:42-43`) lights its active state via `pathname.startsWith("/methodology")`. Reachable and
discoverable.

### B2 — No duplicate home, no parallel shell ✓
- `/methodology` is a brand-new entity (the J-12 glossary) — no pre-existing page covers it, so there is
  no duplicate home to consolidate.
- The page (`apps/frontend/app/methodology/page.tsx`) lives under the App-Router tree and renders inside
  the existing layout shell (left sidebar + main content); it composes the established components
  `PageHeading`, `Card`, `Badge`, `EmptyState` and the standard loading/error/empty idioms
  (`page.tsx:46-88`). It invents no nav and no parallel shell. The `kind` chip (`kindVariant`/`kindLabel`,
  `page.tsx:22-28`) is a pure palette-token switch, not per-entry copy; every entry's content comes from
  the fetched catalog (no hard-coded status/pattern list — config-driven-UI anti-goal satisfied).

### B3 — Nav-skeleton change protocol followed ✓
The new top-level section correctly triggered a fresh `blueprint.reapproval-requested` marker (present,
432 bytes, written this iter), and the blueprint diff updates the IA skeleton (`blueprint.md:43-44`), the
new narrative paragraph (`blueprint.md:53-58`), the feature/journey-home table (`blueprint.md:76`), the
Data-Contract row (`blueprint.md:97`), and the iter-12 serving note (`blueprint.md:122`) consistently with
the landed code.

---

## Part C — Advisory (WARN-level only; non-blocking)

- **Tooltip vs native-title asymmetry on the VCP badge (minor).** On `/stocks`, the setup badge's catalog
  meaning is reached via the accessible `InfoTooltip` (hover/focus/click), while the VCP badge keeps its
  per-row reason as a native `title` and exposes the catalog VCP meaning via a *second* adjacent
  `InfoTooltip` (`stocks/page.tsx:293-300`). This is per the spec (per-row reason stays verbatim; catalog
  meaning is additive) and is correct, but two affordances on one badge is a small UX inconsistency worth a
  glance next time the badges are touched. No coherence rule implicated.
- **Threshold formatting is self-consistent but page-local.** `/methodology` renders numeric rows as
  `label cmp value unit` (`methodology/page.tsx:128-137`). These are config *definition* values (e.g.
  "Max base depth ≤ 35%"), a different displayed value from any per-stock score/return, so there is no
  cross-page single-value formatting conflict — noted only for completeness.

Neither note creates required tidy-up work; both are optional.

---

## Evidence index

- Engine assembler: `apps/backend/app/engine/methodology.py:18-19,30,36-67`
- Resolver + boot validator + typed models: `apps/backend/app/config.py:403-451,507,552-568`
- Endpoint + registration: `apps/backend/app/api/methodology.py:18-21`; `apps/backend/main.py:17,77`
- Config catalog (refs target canonical blocks): `config.yaml` `methodology:` section
- Frontend client: `apps/frontend/lib/api.ts:500-531`
- New page (existing shell, no hard-coded copy): `apps/frontend/app/methodology/page.tsx`
- `/stocks` tooltip + filter-vocabulary (server-status filter preserved): `apps/frontend/app/stocks/page.tsx:82-117,133,291-304`
- Nav link (1 click): `apps/frontend/components/sidebar.tsx:37`
- Empty-diff keystone: `git diff <sha> --stat` over engine + 9 routers = empty
- Reapproval marker: `runs/goal-session-i_can_see_the_wealthy_future/state/blueprint.reapproval-requested` (present)
- Blueprint registration: `blueprint.md:43-44,53-58,76,97,122`

**Bottom line:** The iteration adds exactly one new value (the config-backed catalog) with one computing
module and one serving endpoint, registered in the Data Contract; it recomputes/​re-serves no existing
canonical value (empty-diff proven), and the catalog `meaning` is correctly distinct from the per-row
`setup.reason`. The new `/methodology` home is reachable in one click, sits in the existing shell, and its
nav-skeleton change carried the required reapproval marker. **COHERENCE-PASS.**
