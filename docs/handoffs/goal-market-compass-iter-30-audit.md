# goal-market-compass-iter-30 Audit Report

**Date:** 2026-09-01
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The phase goal is genuinely achieved: `as_of=2026-08-12` version 7 exists, carries a real
`state_band`, and the default landing view (`/`, no `asof`) renders all three direction badges as
"little changed" instead of "NA" with no contradiction against the Summary card — I re-derived the
three deltas from the raw `scanner_runs` / `market_phase_cache` rows myself and they match the stored
manifest and the screenshot exactly. AG-12, AG-17 and AG-9 hold at the true final post-all-lanes state
(my own re-derivation: 26 baseline rows × 29 columns, **zero** field mismatches; exactly one new row
in the whole table). Two IMPORTANT items remain unresolved and neither is fixable inside this
iteration's scope: (B1) minting version 7 on an **incident date** silently removed the `Basis: rebuilt`
disclosure from every served surface for 2026-08-12, which collides with `docs/goal.md:1020` ("For the
4 dates that DO have manifests … do not regenerate them"); and (B2) J-11's regression golden was
**edited after** the deterministic replay lane failed on it and has never been executed since.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (gap — needs owner ruling): minting v7 on an incident date erased that date's
`Basis: rebuilt` disclosure from every served surface**

2026-08-12 is one of the eleven iter-5 incident dates (`docs/goal.md:962-964`). Its current
`ScannerRun` (id 3158) was recreated during the recovery on `2026-08-26 10:53:02.010362`, while
versions 1–6 recorded `source_run_created_at` of `2026-08-20T04:40:05` (v2–v6) or nothing at all (v1).
`basis_disclosure` (`apps/backend/app/engine/compass.py:1216-1293`) therefore reported **`rebuilt`**
for the served manifest before this iteration. Version 7 was frozen from the already-rebuilt run, so
its recorded timestamp equals the current run's and the same function now returns **`available`**
(verified in the DB: v7's `generation_json.source_run_created_at` = `2026-08-26T10:53:02.010362+00:00`
= `scanner_runs.created_at` for id 3158).

That value change is *correct for version 7*, but its consequence is not neutral:

- `GET /api/compass` serves **only the latest version** (`apps/backend/app/api/compass.py:69-73`,
  `latest_manifest_for_date`), and the `versions` array it attaches carries only
  `version/mode/frozen/prospective_eligible/generated_at` — **no per-version basis**
  (`apps/backend/app/api/compass.py:42-56`). Confirmed visually in
  `reports/qa/goal-market-compass-iter-30-evidence/UT-J-11-result.png`: one `Basis: available` chip,
  and a v1–v7 strip with no basis column.
- So after this iteration **no served surface anywhere discloses that 2026-08-12's underlying run was
  destroyed and rebuilt.** Before it, the Today page for that date said so.
- `docs/goal.md:1020-1027` (J-11 step 4) states, for the four incident dates that already have
  manifests — 2026-08-05, 08-10, 08-11 and **08-12** — "do not regenerate them", and names "the
  existing read-time **basis disclosure**" as "the sanctioned mechanism for surfacing that a stored
  source run was rebuilt".

Two legitimate readings conflict, and the choice changes the product (judgment-rubrics §3):
(a) that clause binds only the J-11 incident-rebuild operation, and a manifest freshly minted over
the owner-accepted post-recovery canonical data (`J-11 DATA RECOVERY: COMPLETE`, `docs/goal.md:2008`)
honestly reports `available`; or (b) it is a standing instruction protecting the disclosure on those
four dates, which this iteration violated as a side effect. Nothing in the phase spec, the plan, the
dev handoff or the review report notices the tension — the browser-qa lane framed it purely as a
"stale golden script" (`reports/phase-goal-market-compass-iter-30-ui-test-results.llm.md:78-83`).

**Not fixed, and not fixable here:** reverting is forbidden (AG-12 — rows are never deleted), and
surfacing per-version basis would require product code changes the spec put out of scope ("binding Do
not redo"). This needs an owner ruling. Rated IMPORTANT rather than CRITICAL because no data was lost
or mutated, the chip is accurate about the artifact it describes, and the phase goal is unaffected —
I was genuinely between GAP and IMPORTANT and took the higher level.

**B2 — IMPORTANT (gap): J-11's regression golden was rewritten after the replay lane failed on it and
has never been executed since**

`runs/goal-session-market-compass/journey-scripts/J-11.json` was modified at
`2026-09-01 01:51:59` — after the deterministic replay lane recorded
`UT-J-11 … step 01 expected "Basis: rebuilt" did not appear | FAIL`
(`reports/phase-goal-market-compass-iter-30-regression-replay-results.md`). The edit flips the step
order and changes the `?asof=2026-08-12` expectation from `"Basis: rebuilt"` to `"Basis: available"`
(`git diff runs/goal-session-market-compass/journey-scripts/J-11.json`). The merged results file then
reports `16/16 journeys passed` and the replay report carries a reconciliation footnote declaring the
FAIL "a golden-script false positive".

This is the exact pattern the spec's own lessons section cites for J-07 ("iter-29b lesson: a golden
written AFTER replay is not coverage", `docs/phases/goal-market-compass-iter-30.md:69-72`), recurring
this round on J-11. Concretely:

- DoD item 2 requires the required-still-passing journeys green via **deterministic replay** (LLM
  fallback only "where no golden exists"). J-11 *has* a golden; it went red in replay and green only
  through the LLM lane.
- The repaired golden's assertions have never been run. I linted it —
  `demo_runner.py --mode lint … --journeys "J-07,J-11"` → `J-07 ok` / `J-11 ok` — which proves syntax,
  not behaviour.

Mitigating evidence (why this is IMPORTANT, not CRITICAL): the *substance* is verified. The LLM lane
captured both dates live (`GET /api/compass?as_of=2026-08-12` → `basis: available`, version 7;
`?as_of=2026-08-11` → `basis: rebuilt`, version 3), and I confirmed both from the database
independently (v3 of 2026-08-11 records `2026-08-14T20:47:21` against a current run created
`2026-08-26 10:53:01` → `rebuilt`). The screenshot
`reports/qa/goal-market-compass-iter-30-evidence/UT-J-11-result.png` shows the `Basis: available` chip
that the new assertion targets.

**Not fixed — and the reason is itself a finding I am recording honestly (rubric §5, "explicit list of
what was NOT re-verified"):** re-running the golden requires starting the canonical backend against
the 8.4 GB live database during the audit lane. Boot warmup is a writer (`docs/goal.md:1098-1101`) and
`get_or_create_manifest` mints a version 1 for any manifest-less historical `as_of` on a plain GET
(`apps/backend/app/engine/compass.py:1170-1182`). Starting it would put a write risk on the exact
final-state AG-12/TC-5 evidence I had just certified, for the marginal gain of re-confirming an
assertion already verified live with a screenshot. **The next iteration's replay lane must execute
J-11 first and report the result before J-11 is treated as replay-green.**

**B3 — OBSERVATION (fixed): the iteration's changed-file record omitted the J-11 golden**

`runs/goal-market-compass-iter-30/status.json`'s `changed_files` listed only the test file and
`J-07.json`; the reviewer's summary likewise states "Only code change is one new fixture-scoped unit
test … plus the J-07.json regression golden"
(`reports/reviews/goal-market-compass-iter-30-review.md`). Both predate the 01:51:59 J-11 edit, so
neither is dishonest — but the record downstream agents read was incomplete. Fixed: appended
`runs/goal-session-market-compass/journey-scripts/J-11.json` to `changed_files` (see §4).

**B4 — OBSERVATION: `status.json` reports `browser_checks_run: false`**

Browser checks demonstrably ran (16 evidence PNGs, 01:41–01:51). I did not flip the flag — it is a
gate input, and changing gate inputs is outside an audit's remit. Recording it so the discrepancy is
not read later as "no browser evidence exists".

### Frontend Findings

**F1 — GAP (documented, explicitly out of scope): the badge/Summary contradiction still exists on 16
of 18 stored dates, one click away**

Only `2026-08-12` (this iteration) and `2026-08-03` (iter-29) have a latest manifest with a non-null
`state_band`. For the other **16** as-of dates the latest version's `state_band_json` is NULL, so
`DirectionBadge` renders `word ?? "NA"`
(`apps/frontend/components/compass-state-band-card.tsx:27-33`) while the Summary card on the same
screen states a real comparison — e.g. 2026-08-11 v3's narrative reads "Conditions are little changed
since the prior session (+0.8 regime-score points)." beside three "NA" badges. The spec explicitly
excluded backfilling other dates (`docs/phases/goal-market-compass-iter-30.md:150-151`), and J-07's
own success criterion is scoped to `/` "without navigating", so this is a GAP, not a failure — but it
is the honest caveat the evaluator needs: the contradiction was closed on the landing view, not
eliminated from the product.

**F2 — OBSERVATION: the action that delivered this capability is not reachable from the UI at the
default view**

The manifest card states "Regenerate is available only for a stored historical date — step the as-of
switcher off 'Latest' first" (visible in `UT-J-11-result.png`). Version 7 therefore came from an
out-of-band operator `POST`, not from a product path. This does not recur for future dates —
`build_manifest_payload` has included `state_band` since iter-28
(`apps/backend/app/engine/compass.py:724-725`) and every ingest-finalize freeze goes through it
(`compass.py:1182`) — so new frontier dates get real words automatically. Each of F1's 16 legacy dates
would need its own operator action.

### Test Findings

**T1 — OBSERVATION: the new unit test asserts vocabulary membership, not the expected words**

`apps/backend/tests/test_manifest_invariants.py:897` asserts
`direction_word in cfg.compass.vocabulary.direction_words.values()`. With the fixture's inputs the
expected values are determined (regime 50→58 = +8 > 2.0 → "improving"; severity 25→45, negated → −20,
|20| > 5.0 → "deteriorating"; breadth unchanged → "little changed"), so exact-word assertions were
available and would additionally catch a polarity swap in the stress band. Line 898
(`is not None`) is unreachable-by-construction after line 897. The test does bite for the invariant it
was written for — `json.loads(None)` raises and the `isinstance(delta, float)` assert fails if
`state_band` ever regresses to the no-comparison shape — and the 11 pre-existing state_band tests
already cover word classification, so tightening this is a nice-to-have, not a defect. I ran it
standalone: `pytest tests/test_manifest_invariants.py -k regenerate_on_frontier -q` → **1 passed** in
0.44s.

**T2 — OBSERVATION: `apps/frontend/.next-verify/` is tracked in git (228 files, 160 MB)**

The QA verification build dirtied ~100 MB of tracked webpack packs this iteration. Pre-existing since
iter-3 (`git log -- apps/frontend/.next-verify`), unrelated to this work — repo hygiene note only.

---

## 3. Domain Assessment

I re-derived the served numbers from raw state rather than trusting any handoff:

| Band | Inputs (from `scanner_runs` / `market_phase_cache`) | Delta | Flat band | Word |
|------|---------------------------------------------------|-------|-----------|------|
| regime | 73.44 (08-11) → 73.18 (08-12) | −0.26 | 2.0 (`config.yaml:1410`) | little changed ✓ |
| stress | severity 26.03 → 25.85 | −0.18 | 5.0 (`config.yaml:1411`) | little changed ✓ |
| breadth | 57.38 → 59.84 above-50DMA | +2.46 | 5.0 (`config.yaml:1405`) | little changed ✓ |

Every value matches version 7's stored `state_band_json` to the floating-point bit, and each |delta|
is genuinely inside its configured flat band — "little changed" is the honest word here, not a
degraded fallback, and the word map is read verbatim from `config.yaml:1428-1431`. The rendered page
agrees: I read `reports/qa/goal-market-compass-iter-30-evidence/UT-02-result.png` myself — three
"little changed" badges, regime 73.18, severity 25.85, breadth 59.8%, and the Summary line "Conditions
are little changed since the prior session (-0.3 regime-score points)." AG-3 and TC-3/TC-4 hold.

**Anti-goals, re-verified independently at the true final state (I am the last lane, so this is the
TC-5 re-derivation the dev handoff deferred):**

- **AG-12** — the 26 rows in `runs/goal-market-compass-iter-29/evidence/manifests-pre-mint.csv`
  compared field-by-field against the live DB: **26 rows × 29 columns, 0 mismatches**. The only rows
  not in that baseline are id 27 (iter-29's mint) and id 28 (this iteration's). Table total = **28**;
  `as_of=2026-08-12` holds exactly versions 1–7 (ids 1, 9, 10, 11, 13, 23, 28). Read through the live
  WAL snapshot with `-wal`/`-shm` present, after every lane had finished.
- **TC-7 / TC-8 (safe set)** — the row-count arithmetic closes this without needing each lane's
  self-report: 27 pre-existing + 1 = 28, and no as-of other than 2026-08-12 gained a version. Since a
  plain `GET /api/compass` on a manifest-less historical date *would* have minted one
  (`compass.py:1170-1182`), this is a real check, not a formality: no lane tripped it.
- **AG-17** — v7 `prospective_eligible = 0`, `available_at_utc = 2026-09-01T00:13:07.835199` (mint
  time, not backdated); no earlier row's eligibility changed (covered by the byte-identity run).
- **AG-9** — newest `data_provider_runs` row is id 549, `2026-08-23`; **zero** `scanner_runs` created
  since 2026-08-30; `MAX(daily_prices.date)` still 2026-08-12. No network fetch happened.
- **AG-13** — market vocabulary stays on the market surface (`little changed`, `Risk-on`,
  `Expansion`); readiness tokens (`Ready`, `GO`) stay in the chrome; v7's `preflight_verdict: "GO"`
  sits in the provenance block, not in the market/narrative blocks.
- **Export integrity** — I ran `compass.verify_manifest_hash()` over
  `apps/backend/data/exports/next_session_manifests/2026-08-12_v7.json` myself: **True**, 355,700
  bytes, `version: 7`, `prospective_eligible: false`, `state_band` identical to the stored row.

**Definition-of-Done trace** (full trace where risk/contradiction warranted it; the mechanical display
items accepted on the reviewer's PASS plus an executed QA row, cited):

1. **J-07 at the default view** — full trace done (my own delta recomputation + screenshot read);
   also replay row `UT-J-07 … PASS` and LLM rows UT-02/UT-03 with screenshots. **Met.**
2. **Required-still-passing journeys** — J-01/J-04/J-05/J-06/J-08/J-10 PASS in deterministic replay
   (`…-regression-replay-results.md`); **J-11 red in replay, green only via the LLM lane after its
   golden was rewritten** → see B2. **Partially met.**
3. **No anti-goal violation** — full trace done, above. **Met at the storage/serving layer**, with
   B1's interpretive question open.
4. **Unit tests / no regressions** — 52 + 37 + 17 = 106 passed across the three targeted files (dev,
   QA, and the reviewer each re-ran them independently); I re-ran the new test standalone.
   `test_no_magic_numbers.py`'s single pre-existing red is confined to `indicators.py`,
   `forward_testing.py`, `research.py` (last touched `0c445647`), all untouched here. **Met.**
5. **J-07 golden updated before replay and exercised** — `J-07.json` mtime `01:14:16` precedes both
   the dev self-verify capture (`01:14:56`) and the pipeline replay evidence (`01:45`); the replay row
   is PASS. The three new steps are genuinely scoped: `resolve_spec` returns a single non-degrading
   `css` spec for a `{"css": …}` target (`scripts/automation/lib/demo_runner.py:131-132`), and the
   testid sits on the element whose entire text is `word ?? "NA"`
   (`compass-state-band-card.tsx:27-33`) — so `:has-text("little changed")` cannot pass while the
   badge reads "NA". **Met.**
6. **Dev handoff with row counts and the mint ledger** — present and accurate for the dev lane; the
   cross-lane ledger it explicitly deferred is closed by my final re-derivation above. **Met.**

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Observation | `runs/goal-market-compass-iter-30/status.json` | Appended `runs/goal-session-market-compass/journey-scripts/J-11.json` to `changed_files`, which had omitted the iteration's third changed file (B3). |

Verification for fix 1: the file re-reads as valid JSON with the three paths present and every other
key byte-unchanged; `git diff` on my working tree touches nothing else. No code, test, golden or
manifest row was modified by this audit — deliberately: B1 cannot be fixed without violating AG-12 or
the spec's code freeze, and B2's fix (re-running the J-11 golden) would have required starting a
writer against the canonical database after I had certified its final immutability state.

---

## 5. Recommended Next Step

Proceed — the iteration's own goal is closed and the evidence holds. Carry these into iter-31:

1. **Owner ruling on B1** (blocking for J-11's final status, not for this iteration): does minting a
   new manifest version on one of the four incident dates that already had manifests — thereby
   replacing that date's served `Basis: rebuilt` with `Basis: available` — conflict with
   `docs/goal.md:1020`? If it does, the remedy is a product change (surface per-version basis in the
   `versions` strip), never a mutation of any stored row.
2. **Run J-11's repaired golden first in the next replay lane** and report the result explicitly; only
   then may J-11 be described as deterministic-replay green (B2).
3. **Decide the scope for F1** — 16 of 18 stored dates still show "NA" badges beside a Summary card
   stating a real comparison. Either accept it explicitly (J-07's criterion is landing-view only) or
   plan a bounded, AG-12-safe backfill; do not let it stay implicit.
4. Optional, cheap: tighten the new test's three assertions to the exact expected words (T1).
