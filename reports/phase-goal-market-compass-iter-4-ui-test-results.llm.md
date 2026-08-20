# goal-market-compass-iter-4 — UI Test Results

**Phase:** goal-market-compass-iter-4
**Date:** 2026-08-20
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: the one browser-testable journey this run (J-01, P1) passes. J-09 has no UI
     surface (goal.md: "Walkthrough: waived — deliberately backend-only") so it is
     recorded SKIPPED, not FAIL — a false click path would misrepresent what this lane
     checked. Its substantive documentary finding (target MISSED) is stated plainly below
     for the evaluator; it is not glossed over. -->

**Overall:** 1/2 tests passed (1 skipped — no UI surface)

---

## Scope note (lean mode)

Dispatched journeys this run: **J-01, J-09** (per dispatch instructions and the
coordinator's operational note). J-02/J-03/J-04 are stable-passing and digested in the
sliced goal file; they are covered by the deterministic replay lane, not re-driven here.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Sector attribution is honest and near-complete on new runs | regression | P1 | Unassigned share ≤5% of resolved members at latest as-of (was ~78%); two spot-checked names show identical sector across leaderboard/detail/API; `/methodology` discloses the two-source basis + current-only limitation; a symbol absent from both maps serves `sector: null` / "Unassigned", never fabricated | Verified live: `GET /api/stocks` at latest as-of (2026-08-12, 539 rows) returns **0 rows with `sector: null` (0.0% Unassigned)** — the frontend's "Filter by sector" `<select>` has no "Unassigned" option at all because zero rows currently qualify (stronger than the ≤5% bar, not a missing control). NVDA (`config.stock_sectors`-mapped → "Technology") and GRMN (pool-CSV-fallback, not in `config.stock_sectors` → "Consumer Discretionary") match identically across the leaderboard Sector cell, the stock detail header badge, and `GET /api/stocks`. `/methodology` → "Stock sector labels" discloses the exact two-source basis and current-only limitation, citing B-114. Step 1 (Remove+backfill on `/data`) was deliberately NOT re-executed live — see Passed Tests notes. Step 5's null-symbol case could not be exercised live (0/539 active members are currently null) — methodology text documents the guarantee; not re-verified via a live click path. | PASS | `reports/qa/goal-market-compass-iter-4-evidence/UT-J-01-result.png` |
| UT-J-09 | The backend fits the host — standing memory halves with zero behavior change | non-UI | P1 | Measured backend VmPeak at standing warm ≤ 2.5 GB (2,621,440 kB) | Not browser-observable — deliberately backend-only, no UI surface (goal.md: "Walkthrough: waived"). Documentary evidence only (cited below): VmPeak measured **3,439,100 kB**, a real 28.9% reduction from the 4,837,420 kB baseline, but **+817,660 kB (31.2%) OVER** the ≤2.5 GB target — **target MISSED**. Disclosed honestly per spec (appended dated, cap values untouched) rather than hidden or forced to pass. | SKIPPED | none (no UI surface) |

---

## Passed Tests

### UT-J-01 — Sector attribution is honest and near-complete on new runs
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-4-evidence/UT-J-01-result.png` (`/methodology` page showing the two-source sector-basis disclosure)

Journey steps executed against goal.md's J-01 (step 1 deliberately not re-executed live —
see below; step 6 is a dev-handoff fixture citation, not a browser-QA item):

- **Step 1 (Remove + backfill on `/data`) — SKIPPED BY DESIGN, not by failure.** The
  coordinator's standing operational note for this run explicitly prohibits re-running any
  backfill/ingest job in this lane: a second goal-mode engine is active on this host, which
  froze it this morning from memory overcommit + swap-thrash. Rather than invent a
  workaround, I verified the RESULT state the fix should already have produced — J-01 was
  implemented and browser-QA'd in a prior iteration (the pre-existing golden at
  `runs/goal-session-market-compass/journey-scripts/J-01.json`), and iter-4's own dev work
  (per `docs/handoffs/goal-market-compass-iter-4-dev.md`) touched only J-09,
  config-only — no backfill ran this iteration that could have reverted the sector fix.
- **Step 2 (Unassigned ≤5% at latest as-of):** `GET /api/stocks` (no `as_of` — resolves to
  the same date the frontend loads by default, `2026-08-12`, 539 rows) returns **0 rows
  with `sector: null` — 0.0% Unassigned**, versus the ~78% baseline goal.md cites. The
  frontend's `<select aria-label="Filter by sector">` currently lists only the 11 named
  GICS sectors + "All sectors" — no "Unassigned" option — because its option list is built
  from sectors actually present in the data and zero rows currently qualify. Confirmed via
  direct API read rather than a nonexistent dropdown option; this is a stronger result than
  the ≤5% bar, not a gap.
- **Step 3 (spot-check two names, one config-mapped, one pool-fallback):**
  Cross-referenced `config.yaml`'s `stock_sectors` map (121 explicit tickers) against the
  API to select **NVDA** (explicitly listed: `NVDA: Technology`) and **GRMN** (absent from
  `config.stock_sectors` — must resolve via the `universe_pool.csv` fallback). Checked
  across three surfaces:
  - Leaderboard Sector cell (via the `stocks-search` filter): NVDA → "Technology" (rank
    222); GRMN → "Consumer Discretionary" (rank 2)
  - Stock detail header badge: `/stocks/NVDA` → "Technology"; `/stocks/GRMN` →
    "Consumer Discretionary"
  - `GET /api/stocks` row: NVDA → `"Technology"`; GRMN → `"Consumer Discretionary"`

  All three surfaces agree for both names — single stored source, no UI-side derivation
  observed.
- **Step 4 (methodology discloses two-source basis + current-only limitation):**
  `/methodology` → "Stock sector labels" reads: *"Each stock's sector label is resolved
  from two sources, in order: the curated `config.stock_sectors` mapping (Trendora's
  original universe) first, then — for any name the curated map does not cover — a
  fallback to the sector recorded in the committed candidate pool (universe_pool.csv). A
  name present in neither source serves no sector ('Unassigned') — never a fabricated
  value. Both sources describe the CURRENT sector only: there is no point-in-time sector
  history... (tracked open as backlog item B-114)."* Matches the acceptance line in
  substance, including the B-114 reference.
- **Step 5 (unmapped symbol serves null, never fabricated):** Not directly exercisable
  live — 0/539 active universe members currently have a null sector, so there is no live
  example of a "symbol absent from both maps" to click through this run. The methodology
  text quoted above documents the guarantee; the underlying code behavior is what the
  feature's original fixture test asserts (not re-run here — this lane does not run
  pytest).

**Golden replay:** re-verified the existing golden's exact steps live
(`/stocks?asof=2026-08-12` → search "GRMN" → "Consumer Discretionary" appears) — they pass
against the running app. The deterministic-replay-lane FAIL does not reproduce live; it
looks like a replay-runner-side issue, not a product regression. Re-saved (content
unchanged, confirmed still correct) to
`runs/goal-session-market-compass/journey-scripts/J-01.json` and lint-checked clean via
`python3 scripts/automation/lib/demo_runner.py --mode lint --scripts-dir
runs/goal-session-market-compass/journey-scripts --journeys J-01` → `J-01 ok`.

---

## Failed Tests

None.

---

## Skipped Tests

### UT-J-09 — The backend fits the host — standing memory halves with zero behavior change
**Verdict:** SKIPPED
**Reason:** No UI surface. goal.md states explicitly for this journey: *"Walkthrough:
waived — deliberately backend-only (no UI surface changes); the demo requirement is
replaced by the dated VmPeak measurement and drill citations in the dev handoff."* There is
no click path to invent. Per the coordinator's standing operational note, I did not
re-run the VmPeak measurement or any backfill/ingest job in this lane — it was already
measured this iteration, and this host has an active memory-safety concern (a second
goal-mode engine is running; the host froze this morning from memory overcommit +
swap-thrash).

**Documentary evidence reviewed (not browser-verified):**
- `docs/handoffs/goal-market-compass-iter-4-dev.md` and `reports/perf-budgets.md`
  Addendum 40 (2026-08-20).
- `config.yaml`: `database.pragmas.cache_size` changed `-262144` → `-65536` (256 MB →
  64 MB per pooled connection); `pool_size` (24) / `max_overflow` (44) / every other
  `database:` key left byte-unchanged, per spec.
- Re-measured standing-warm VmPeak (original-methodology replica, backend started via
  `bash scripts/start-backend.sh`): **3,439,100 kB**, versus the Addendum 39 baseline of
  **4,837,420 kB** — a real **28.9% reduction**.
- **Acceptance bar is `≤ 2.5 GB` (2,621,440 kB). The measured 3,439,100 kB is +817,660 kB
  (31.2%) OVER that bar — the target is MISSED.** This is the developer's own honestly
  reported result, not a fabricated pass.
- Concurrent-load check (`test_data_manager_concurrency_load.py`) passed: 3 passed, zero
  `QueuePool` TimeoutErrors, against the new `cache_size`.
- Byte-identity spot check across `/api/dashboard`, `/api/stocks`, `/api/market-phase`,
  `/api/compass` at `as_of=2026-08-10`: all 4 endpoints byte-identical (md5-verified)
  before/after the config change — no displayed value moved.
- The miss was handled per the journey's own "Honest status & anti-goals" bullet: the new
  measurement was appended dated next to the old one (Addendum 40 beside Addendum 39, a
  purely additive 123 insertions / 0 deletions — nothing overwritten), and the target was
  NOT widened to force a pass. AG-10's hard cap (`memory_cap_mb` 8192) was left untouched;
  both measurements still carry comfortable margin against that hard cap — this is a miss
  of iter-4's own tighter standing-warm bar, not an AG-10 hard-cap breach.

**Judgment against the acceptance line as written** (per the coordinator's explicit
instruction): the Correctness bullet ("measured backend VmPeak at standing warm ≤ 2.5 GB")
is **NOT met**. The Consistency bullet and the honest-disclosure process bullet ARE met.
Recorded here as SKIPPED because browser QA has no UI surface to verify — a fabricated
click path would misrepresent what this lane checked — but the substantive miss above is
stated plainly, not hidden behind the SKIP label, for the evaluator to weigh.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chrome via MCP (headless, pinned profile/CDP port)
- **Test Date:** 2026-08-20
- **Evidence directory:** `reports/qa/goal-market-compass-iter-4-evidence/`
- **Journeys tested this run (lean mode):** J-01, J-09 (J-02/J-03/J-04 stable-passing,
  covered by deterministic replay per dispatch instructions)
