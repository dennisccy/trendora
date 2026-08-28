# goal-market-compass-iter-26 — UI Test Results

**Phase:** goal-market-compass-iter-26
**Date:** 2026-08-28
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 2/2 tests passed (0 skipped)

---

## Scope note (read before the table)

Per the pump coordinator note and the iteration spec's own BACKGROUND section, this run does
**not** execute J-05 step 1 / J-06 steps 1-3 literally (the destructive "remove the last two
trading days" drill) — that drill's dates resolve today to 2026-08-11/2026-08-12, whose removal
caused this session's core incident, and the AG-9 recovery exception is exhausted. The iteration
spec deliberately proves those steps through the isolated-engine fixture suite instead (cited
below from `docs/handoffs/goal-market-compass-iter-26-dev.md`), and routes live, safe evidence
through **read-only rendering** of the manifest strip plus the **one already-authorized additive
write** the developer performed this iteration (`POST /api/compass/regenerate?as_of=2025-04-15`,
minting version 2). I did not repeat that write — I independently re-verified its resulting state
live (browser + API), since re-triggering it would push `next_session_manifests` to 26 rows and
break the iteration's own TC-12 accounting (exactly one new row this iteration). I also did not
navigate to, or request `/api/compass?as_of=` for, any of the 7 manifest-less incident dates
(2026-05-12, 2026-05-13, 2026-07-10, 2026-07-13, 2026-07-24, 2026-07-27, 2026-08-03) or any other
manifest-less date — doing so would create-once mint a new manifest row and also break TC-12.

Row-count check (read-only `sqlite3 -readonly`, before and after my entire QA session):
`daily_prices` 3,310,374 → 3,310,374 (unchanged), `scanner_runs` 3,128 → 3,128 (unchanged),
`next_session_manifests` 25 → 25 (unchanged — still exactly one v1 + one v2 row for
`as_of=2025-04-15`, matching the developer's own before/after claim). My QA session performed
zero writes to the canonical database.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-05 | Each close freezes one provenance-stamped next-session manifest, exported byte-consistently | smoke/regression | P1 | Frontier-date manifest is fully stamped (mode, version, frozen, prospective_eligible, generation, both rule hashes, manifest_config_hash, dataset stamp, universe block, both content/manifest hashes); export file bytes match served payload and `manifest_hash` recomputation reproduces the embedded value; the manifest strip on `/` renders these stamps and the comparison/shadow cohort counts identically to `GET /api/compass` | Live `GET /api/compass?as_of=2026-08-12` (current frontier, version 6) carries every required field, well-formed; independently re-serialized and dict-compared against the on-disk export `2026-08-12_v6.json` — structurally identical, both `manifest_hash` (`9bc08cfb...`) and `content_hash` match embedded values on both sides. Manifest strip on `/` (latest) matches the API verbatim: mode "at ingest", version 6, frozen, "not prospective-eligible", all 4 hash-chip prefixes, dataset stamp `r3112-f6761224`, universe pool hash prefix, Members 539, comparison cohort (539) = members(539) − candidates(0), shadow (26). Note: the literal "version:1 / prospective_eligible:true" wording in J-05 step 2 does not hold for the *current* live frontier — this date's history includes 5 post-freeze regenerate cycles from the J-10/J-11 incident-recovery window (v2–v6, all `prospective_eligible:false` per AG-17), and the live `basis` correctly reads `rebuilt` ("the source scanner run was recreated after this manifest was frozen"). This is expected, AG-17-correct behavior, not a defect — the true at-ingest/version-1/eligible=true case is proven by fixture (`test_api_compass.py::test_compass_route_serves_every_new_field_directly`, `test_manifest_invariants.py::test_tc21_available_at_utc_never_earlier_than_generated_at_plus_margin`, `test_tc18_no_later_bar_resolves_at_ingest_mode`), cited in the dev handoff and re-run green (103 passed, 0 failed) this iteration. Steps 1 (live drill), 5, 6, 7 (create-once / retrospective-mint drills) were not executed live for the reasons in the Scope note above; cited instead from dev-handoff TC-3/TC-4/TC-7/TC-8/TC-9 fixture coverage. | PASS | `reports/qa/goal-market-compass-iter-26-evidence/UT-J-05-result.png` |
| UT-J-06 | A frozen manifest never changes — later data, rebuilds, and regeneration are safe | smoke/regression | P1 | Version 1 of the `as_of=2025-04-15` manifest stays byte-identical after the confirm-gated regenerate action; version 2 mints with its own mode/generation timestamp/`available_at_utc`/`manifest_hash` and `prospective_eligible:false`; the UI lists both versions with their own stamps; the basis disclosure reflects the true rebuild/removal state read-time, never a 404 or recompute | Loaded `/?asof=2025-04-15` live (independently, not trusting the dev's screenshots) and diffed the rendered manifest strip against `GET /api/compass?as_of=2025-04-15`: mode "retrospective", version 2, frozen, "not prospective-eligible", Frozen 8/28/2026 1:45:04 PM — byte-matches `generation.generated_at` "2026-08-28T12:45:04.938308+00:00"; all 4 hash-chip prefixes, dataset stamp `r3158-f6814320`, universe pool hash, Members 531, comparison cohort (521) = 531−10 candidates, shadow (28), Basis: available — all match the API verbatim. VERSIONS section lists v1 (retrospective, not eligible, `2026-08-20T11:41:00.381102+00:00` — unchanged from its pre-regenerate value) and v2 (retrospective, not eligible, `2026-08-28T12:45:04.938308+00:00`) side by side, exactly matching the API's `versions` array. `prospective_eligible:false` on both v1 and v2 confirms AG-17/AG-12 (a regenerated manifest is never eligible, and v1's own ineligibility — already true before the incident-recovery lineage even applies here — is preserved). The confirm-gated "Regenerate manifest" control is visibly present on this historical as-of (I did not click it — re-triggering would mint an unauthorized v3 this iteration); separately observed that on "Latest" the control is replaced with "Regenerate is available only for a stored historical date — step the as-of switcher off 'Latest' first," confirming the frontier's manifest cannot be regenerated from the live view at all, a stricter guard than the journey requires. Also incidentally observed the live "rebuilt" basis-disclosure state (see UT-J-05 basis note) — a real, currently-materialized instance of the J-06 step 3 acceptance's non-"available" basis rendering. Steps 1-3 (further backfill / remove-data / restore-and-relabel drills) not executed live for the reasons in the Scope note; cited instead from dev-handoff TC-7/TC-8/TC-9 fixture coverage and the honest B2 finding (`basis.status=="unavailable"` is real, unit-tested, but currently unreachable via the live route because `resolved_run`'s self-heal always recreates a missing run first — a pre-existing condition, not a regression). | PASS | `reports/qa/goal-market-compass-iter-26-evidence/UT-J-06-result.png` |

---

## Passed Tests

### UT-J-05 — Each close freezes one provenance-stamped next-session manifest, exported byte-consistently
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-26-evidence/UT-J-05-result.png` (full-page capture of `/` at latest as-of, showing Summary/What-changed/Next-session-focus plus the full Manifest strip and its VERSIONS v1-v6 list)
- Live `GET /api/compass?as_of=2026-08-12` served every required field (mode, version, frozen, prospective_eligible, generation block, `available_at_utc`, engine identity, `candidate_rule_hash`, `cohort_rule_hash`, `manifest_config_hash`, dataset stamp, universe block, `content_hash`, `manifest_hash`); parsed both the served payload (stripped of the read-time-only `basis`/`versions` fields) and the on-disk export `apps/backend/data/exports/next_session_manifests/2026-08-12_v6.json` as JSON and confirmed dict equality, with `manifest_hash` `9bc08cfba04fc2dcab7eeb35f7b695834ef69da5ca3b6634acca4c605d5769c3` and `content_hash` `3aff17d15a91466e15a7272a841ca4f0e619b7cff4412bc08c33abfc25ae954a` identical on both sides — independently corroborates the dev handoff's own byte-equality claim.
- Manifest strip on `/` (Chrome MCP, no query param = latest) renders "at ingest / version 6 / frozen / not prospective-eligible", "Frozen 8/20/2026, 3:50:57 PM", all 4 hash-chip prefixes, "Dataset stamp: r3112-f6761224", "Universe pool: 4f7aeca5be…", "Members: 539", "Profile: core" (the config default label for a null `universe_profile`), "Basis: rebuilt" with detail text, and "Audit table — comparison cohort (539) + near-threshold shadow (26)" — every value cross-checked equal to the live API's `generation.engine_identity`, `candidate_rule_hash`, `cohort_rule_hash`, `manifest_config_hash`, `dataset.stamp`, `universe.pool_hash`, `universe.member_count`, `comparison_cohort` length, and `near_threshold_shadow` length.
- Confirmed a real, honest deviation from J-05 step 2's literal wording (current frontier is v6/ineligible/rebuilt, not v1/eligible/available) traces entirely to the J-10/J-11 incident-recovery history on this exact date, is AG-17-correct, and is not something this iteration's scope authorizes touching further.

### UT-J-06 — A frozen manifest never changes — later data, rebuilds, and regeneration are safe
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-26-evidence/UT-J-06-result.png` (full-page capture of `/?asof=2025-04-15`, showing the "Viewing as-of 2025-04-15 (historical)" chrome, the retrospective banner, all 10 next-session candidate cards, and the full Manifest strip with both VERSIONS rows and the visible "Regenerate manifest" control)
- Independently (not from the dev's own screenshots) loaded `/?asof=2025-04-15` and diffed the rendered manifest strip against a fresh `GET /api/compass?as_of=2025-04-15` call: version 2's stamps, hashes, dataset stamp, universe counts, and Basis all match verbatim; the VERSIONS list shows v1 (`2026-08-20T11:41:00.381102+00:00`, retrospective, not eligible) unchanged from its pre-regenerate value and v2 (`2026-08-28T12:45:04.938308+00:00`, retrospective, not eligible) alongside it — exactly the API's `versions` array, and exactly TC-6's acceptance ("version 1 remains readable and byte-identical with its flag unchanged, and the UI lists both versions with their stamps").
- Did **not** click "Regenerate manifest" (present and visibly confirm-gated) — the write it would perform was already exercised once this iteration by the developer, and repeating it would both violate this iteration's TC-12 row-count accounting and be operationally wasteful; the read-only verification above already independently confirms the acceptance criteria against the live database.
- Confirmed `daily_prices`/`scanner_runs`/`next_session_manifests` row counts identical before and after my entire QA session (25/25 manifests, still exactly v1+v2 for `as_of=2025-04-15`) — my testing added zero canonical-DB rows.
- Wrote a golden replay script for this journey (see below); intentionally did **not** write one for UT-J-05, since the frontier/"latest" manifest's version number, hashes, and timestamps are expected to change on every future ingest cycle, and a hard-coded text assertion against "latest" would go stale and risk a false REGRESSION signal in a later iteration. J-05's live-testable acceptance is adequately re-verifiable next time by re-running the same read-only spot-check pattern (no golden needed to make that fast, since it's already a single `curl`+`jq`).

---

## Golden Replay Scripts

- `runs/goal-session-market-compass/journey-scripts/J-06.json` — written and lint-passed
  (`demo_runner.py --mode lint`). Anchored on `/?asof=2025-04-15` (permanently historical,
  AG-12-immutable): step 1 asserts the frozen candidate name "MCD" renders; step 2 asserts v1's
  permanently-fixed generation timestamp `2026-08-20T11:41:00.381102+00:00` renders — a value
  that can never legitimately change again under AG-12, so this script should stay valid
  indefinitely even if a future iteration mints v3+ for this date.
- No golden script written for J-05 — see reasoning above (frontier/"latest" values drift every
  iteration by design; a script anchored there would not stay valid).

---

## Failed Tests

None.

---

## Skipped Tests

None at the journey level (both J-05 and J-06 produced a PASS verdict). Sub-steps that were not
executed live are documented per-test above and in the Scope note, each with its fixture-test
citation from `docs/handoffs/goal-market-compass-iter-26-dev.md`:
- J-05 steps 1 (live ingest-freeze drill), 5-7 (ScannerRun engine_identity NULL-state spot-check,
  create-once re-run, retrospective create-once-on-GET) — forbidden this iteration (destructive or
  additional-manifest-mint actions); cited from dev-handoff TC-3/TC-4/TC-7/TC-8/TC-9.
- J-06 steps 1-3 (further backfill, remove-data cascade, restore-and-relabel) — forbidden this
  iteration; cited from dev-handoff TC-7/TC-8/TC-9 and the honest B2 finding (basis "unavailable"
  is real but currently unreachable live, a pre-existing condition).

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chrome via MCP (headless, pinned profile)
- **Test Date:** 2026-08-28
- **Evidence directory:** `reports/qa/goal-market-compass-iter-26-evidence/`
- **Canonical DB:** `apps/backend/data/trendora.db` — reused the pump-provided live services;
  zero writes performed by this QA session (row counts verified identical before/after).
