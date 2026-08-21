# goal-market-compass-iter-8 Audit Report

**Date:** 2026-08-21
**Auditor:** Out-of-band forensic audit — read-only, skeptical, evidence-based
**Commissioned by:** project owner, as a corrective control for the missing post-dev audit lane
**Scope:** iteration 8's live writes to `apps/backend/data/trendora.db`, the redesigned J-10 gate, and
the iter-7 audit fixes (B2/B3/B5/B6 + the zero-evidence fail-open)

---

## 1. Executive Verdict

**Verdict:** ESCALATE

**The database write itself is sound.** Every one of the 40 restored rows is inside the authorized
envelope, the bridge arithmetic reproduces exactly from the persisted per-pair evidence, the write path
is provably INSERT-only, no surviving row was overwritten, and the redesigned per-symbol gate is
genuinely fail-closed under adversarial probing. **The evaluator should NOT read this verdict as a
reason to roll back the 40 rows** — nothing about them is unsafe, and the recovery logic is
substantively correct.

ESCALATE is returned because the iteration's *process controls* failed in exactly the two ways this
iteration's own spec pre-registered as escalation triggers, and because the iteration's headline
evidentiary claim does not survive verification:

1. `Depth: full` was silently dispatched as `lean` (third demotion this session), and
2. a **forbidden deterministic-replay lane ran against J-01 and J-04** — which the spec's DEFINITION OF
   DONE, TC-19 and OUT OF SCOPE all prohibit unconditionally — starting a frontend and a second backend
   on the host that froze from exactly that on 2026-08-20, and
3. the gate's "cross-vendor agreement" result is a **same-vendor tautology**: the stored comparison
   series is itself Yahoo-sourced, not Stooq-sourced, so the gate compared Yahoo raw close against Yahoo
   raw close and was structurally incapable of failing.

I weighed `PASS WITH PROCESS DEFECT` seriously. That verdict is defined as available "only if the
database write and recovery logic are substantively sound but the **depth-demotion/process issue**
remains." The write and logic are sound — but a second, previously-unreported violation occurred during
this iteration, and two load-bearing statements in the dev handoff are factually wrong. That exceeds the
narrow allowance. Per the honesty rule, where genuinely unsure between two levels I take the higher one
and say so.

---

## 2. Findings

### Backend / Evidence Findings

**B1 — IMPORTANT (gap, cannot be fixed read-only): the convention gate performed a same-vendor
comparison, so its "agree" verdict is not the cross-vendor evidence the contract requires.**

`docs/goal.md` J-10 step 2a frames the gate on the premise that the stored bars are Stooq's
split/dividend-adjusted series ("Stooq's bars are split/dividend-adjusted (seed manifest: 'REAL
split/dividend-adjusted EOD OHLCV')"). That premise does not hold for the window actually compared.

Evidence, three independent lines:

- `apps/backend/data/seed/meta.json` — the committed Stooq seed's window is `1996-01-01 .. 2026-07-01`.
  The comparison window (`2026-08-04 .. 2026-08-10`, `j10-convention-evidence.json`) is five to six
  weeks **past** the seed boundary, so none of it comes from the Stooq seed.
- `data_provider_runs` — every non-seed fetch that ever populated that window is `provider='yahoo'`
  (ids 297, 528, 529; run 528 fetched `2026-08-05..2026-08-13`, 3571 bars). Across the whole table the
  provider tally is `seed: 508, yahoo: 34, stooq: 1` — and the single `stooq` run (id 541) fetched
  **zero** bars (`symbols_failed: 587`, the proof-of-work block).
- Float32 fingerprint test on `daily_prices.close`, sampled 400 rows per date:

  | date | float32-exact | interpretation |
  |---|---|---|
  | 2000-06-15 | 1.7% | Stooq seed (base rate) |
  | 2020-06-15 | 2.0% | Stooq seed |
  | 2026-07-01 | 3.8% | Stooq seed — last seed day |
  | **2026-07-02** | **100.0%** | **Yahoo — first post-seed day** |
  | 2026-08-05 | 100.0% | Yahoo (comparison window) |
  | 2026-08-10 | 100.0% | Yahoo (comparison window) |
  | 2026-08-11 / 08-12 | 100.0% | Yahoo (iter-8 restored) |

  The discontinuity lands exactly on the seed boundary. Values such as `312.4100036621094` are float32
  round-trips of `312.41` — Yahoo's chart-API precision artifact, absent from the Stooq seed era.

Consequence: all 88 pairs are bit-identical (`stored_close == fallback_close` exactly, ratio `1.0`
exactly, zero pairs differing). That is not "no ex-dividend event has separated the two series yet" —
it is the same vendor, the same field, re-fetched. The gate's discriminating power was never exercised.

**This does not make the write unsafe — it makes it safer.** The relevant integrity question is whether
the restored bars sit on the same scale as the bars adjacent to the gap. They do, by construction: the
adjacent stored bars (`2026-07-02 .. 2026-08-10`) and the restored bars are both Yahoo raw close. No
scale discontinuity was introduced at 2026-08-11/12, which is precisely what goal.md's "an untransformed
insert would leave a scale discontinuity at exactly these two dates" clause exists to prevent. The gate
accidentally validated the right thing (continuity with the adjacent series) while claiming to have
validated a different thing (cross-vendor convention agreement).

Severity note: I considered CRITICAL and chose IMPORTANT, because no data is corrupted and the phase's
build objective (a correctly-constructed fail-closed gate) was met. What failed is the *demonstration*,
not the mechanism.

**B2 — IMPORTANT (gap): the dev handoff asserts a cross-vendor fact that the evidence contradicts.**

`docs/handoffs/goal-market-compass-iter-8-dev.md:175-180`: *"Stooq's stored close and Yahoo's raw
`get_daily` close are byte-identical for every sampled (symbol, date) pair in this window — no
ex-dividend/adjustment event has retroactively separated the two series yet for any of these 20 names."*
And `:191-194`: *"iteration 7's delta was a uniform multiplicative offset (comparing Stooq-adjusted
against Yahoo-adjusted...)"*.

Both are wrong on the same point: the stored side is Yahoo, not Stooq (see B1). The handoff's Known
Issue 6 correctly declines to claim vendor *interchangeability*, but the sentence above asserts a
measured cross-vendor *identity*, which is a stronger claim and is unsupported. Under AG-9 step 2a
("no surface, artifact, narrative, methodology page, or future study may cite this recovery as
vendor-equivalence evidence"), this sentence is exactly the kind of statement a later study could cite.
It must be corrected before the handoff is treated as evidence.

**B3 — GAP (observation, out of J-10 scope): a genuine vendor-convention discontinuity exists at the
seed boundary, and nothing has ever examined it.**

`daily_prices` changes vendor between 2026-07-01 (Stooq, split/dividend-adjusted) and 2026-07-02
(Yahoo, raw close) — a real, un-bridged, un-gated splice created by the ordinary fetch path across
2026-07-17 .. 2026-08-14, long before this incident. It is **not** iter-8's doing and is outside J-10's
authorization. Recorded here because it is the discontinuity the owner's gate was designed to catch, it
is still unexamined, and any future convention work should start from this fact rather than from the
handoff's assumption that post-seed history is Stooq.

### Database-Mutation Findings

**B4 — IMPORTANT (gap): the mutation accounting in the handoff is materially incomplete.**

The handoff reconciles three tables (`daily_prices`, `scanner_runs`, `next_session_manifests`) and states
"no other table (`daily_prices`, `next_session_manifests`) was touched by it." In fact **11 tables and
roughly 4,600 rows** were written on 2026-08-21. Full reconciliation is in section 4; every write is
classifiable and none is unauthorized, but the iteration must not be described as having accounted for
its writes when it enumerated three tables out of eleven.

**B5 — IMPORTANT (gap): the 2026-05-12 `ScannerRun` is mischaracterized as unrelated to the incident.**

The handoff states (`:245`, `:266-267`) that 2026-05-12 is *"a date wholly unrelated to this incident"*
and *"appears to be a pre-existing, unrelated cadence gap, not something this iteration's drill or
recovery work created or is responsible for."*

That is contradicted by evidence the module's own docstring cites. `data_provider_runs` id=538 — the
iter-5 drill's removal record — records `cascade.snapshot_dates` =
`['2026-05-12', '2026-05-13', '2026-07-10', '2026-07-13', '2026-07-24', '2026-07-27', '2026-08-03',
'2026-08-05', '2026-08-10', '2026-08-11', '2026-08-12']`. **2026-05-12 is one of the 11 ScannerRun
snapshots the iter-5 drill destroyed.** It is not a pre-existing cadence gap; it is unrepaired drill
damage that the backend boot warmup opportunistically re-filled.

This changes the meaning of the side effect rather than its safety. Verified independently:
- run 3149's forward returns reach `2026-08-07 .. 2026-08-10` at the longest horizon (h=60) and
  **zero rows** measure on or after 2026-08-11 — so none of its arithmetic touches the still-damaged
  region. Its inputs and outputs are entirely within intact data.
- It created no `data_provider_runs` row, no `daily_prices` row, and no manifest row.

It also reframes recovery completeness: **3 of the 11 drill-destroyed snapshots now exist**
(2026-05-12, 2026-08-11, 2026-08-12; 2026-08-10 was restored earlier as run 3114). Eight remain absent:
2026-05-13, 2026-07-10, 2026-07-13, 2026-07-24, 2026-07-27, 2026-08-03, 2026-08-05.

### Process Findings

**P1 — IMPORTANT: a forbidden deterministic-replay lane ran against J-01 and J-04.**

The spec forbids this three times over — DEFINITION OF DONE ("No browser-QA or deterministic-replay lane
runs against J-01, J-02, J-03, or J-04 this iteration, **regardless of the recovery's outcome**"), TC-19
("no browser-QA or deterministic-replay evidence file for any of the four exists under this iteration's
QA evidence directory"), and OUT OF SCOPE. It ran anyway:

- `reports/qa/goal-market-compass-iter-8-evidence/J-01-verify.png` (01:40:01 local = **00:40:01 UTC**)
- `reports/qa/goal-market-compass-iter-8-evidence/J-04-verify.png` (01:40:08 local = 00:40:08 UTC)
- `reports/phase-goal-market-compass-iter-8-regression-replay-results.md` — "Browser QA Verdict: PASS,
  2/2 journeys passed", listing UT-J-01 and UT-J-04
- `runs/goal-session-market-compass/iter-8/.bqa-replay-state` — `_use_replay=yes`,
  `R_REPLAY=J-01\ J-04\ `, `FRONTEND_AVAILABLE=yes`, `QA_FRONTEND_REQUIRED=yes`,
  `FRONTEND_URL=http://localhost:3255`; `.bqa-replay-rc` = `0`

It started **both** a backend and a frontend, which OUT OF SCOPE separately forbids ("Starting the
frontend, or starting more than one backend process at a time"), on the host that froze from memory
overcommit on 2026-08-20. This is the developer-independent orchestration layer: `developer.done` is
stamped 00:38:55 UTC and `.bqa-replay-pid` 00:38:55 UTC — the lane launched the instant dev finished,
after the handoff was written (00:36:08 UTC), so the developer neither ran it nor could have reported it.

This is the direct consequence of the depth demotion: lane selection follows the dispatched depth
config, not the spec's TC-19 prohibition. It is a recurrence of the pattern the spec named as an
escalation trigger, and a recurrence of the iter-6 failure whose evidence sits quarantined at
`reports/qa/goal-market-compass-iter-6-evidence/INVALID-damaged-database.md` — this time with **no
quarantine marker**, against a database whose recovery is 3.4% complete. The PASS recorded in that
replay-results file must not be treated as journey evidence.

**P2 — IMPORTANT: `Depth: full` was dispatched as `lean`; no reviewer or QA lane ran.**

`docs/phases/goal-market-compass-iter-8.md:9` reads `Depth: full` (with an explicit Full-trigger-1
justification at `:10-16`). `runs/goal-session-market-compass/iter-8/depth-dispatched` reads `lean`,
written 2026-08-20 23:38:49 UTC at decomposer time, before the developer's dispatch. Confirmed
consequences: **no `reports/reviews/goal-market-compass-iter-8-review.md` exists** and **no
`reports/qa/goal-market-compass-iter-8-qa.md` exists** — only a `review-packet.md` that was prepared and
never consumed. The developer flagged this honestly and declined to edit the marker (Known Issue 7),
which was the correct call.

**This audit is supplemental independent scrutiny. It is NOT proof that the engine satisfied the
full-depth requirement, and `lean` must not be normalized as `full`.** The evaluator must receive both
facts.

### Test Findings

**T1 — OBSERVATION: evidence-persistence ordering is proven on the stop path only.**

`test_gated_recovery_persists_evidence_before_any_verdict_is_used`
(`apps/backend/tests/test_j10_recovery.py:595`) asserts persistence when zero symbols pass — a good
choice, since it proves persistence is not bolted onto the success path. Ordering on the *success* path
is guaranteed textually (`j10_recovery.py:869-873`: the write precedes the `passing` computation) but is
not separately asserted. Adequate as built; noted for completeness.

---

## 3. Domain Assessment

The redesigned gate is well built. `_compute_symbol_verdict` (`j10_recovery.py:482-599`) is a pure
function, which is what made genuine adversarial testing possible, and the ladder ordering is correct:
`<2 comparable pairs → inconclusive`, then the **mismatch branch**, then the `MIN_COMPARABLE_PAIRS`
floor, then `agree`. Placing the mismatch branch *before* the evidence floor is exactly what iter-7's
audit finding B1 required, and it holds under test (a 2-pair wildly-disagreeing symbol returns
`mismatch`, not `inconclusive`).

I probed the fail-open directly against the real module (in-memory fixtures only; the production
database was never opened for write):

| adversarial input | verdict | bridge |
|---|---|---|
| both series empty | inconclusive | None |
| stored only / fallback only | inconclusive | None |
| 1 comparable pair, perfect match | inconclusive | None |
| 2 comparable pairs, perfect match | inconclusive | None |
| 3 comparable pairs, perfect match (at floor) | agree | 1.0 |
| fallback all zero / all negative | inconclusive | None |
| stored all zero (the old B4 `TypeError` case) | inconclusive | None |
| uniform 2× offset over 5 pairs | agree | 2.0 |

`agree` is unreachable below three genuinely comparable pairs, and a non-positive price on either side
never becomes a comparable pair — which also incidentally retires carried finding B4, since a zero
stored close can no longer reach the reason-string formatter. The uniform-2× case returning `agree` with
bridge 2.0 is correct and intended: invariance to a uniform multiplicative offset is the entire point of
the redesign.

The bridge direction is right. `bridge_factor = mean(stored/fallback)`, applied as
`fallback_value × factor`, lands the restored bar on the stored scale. `_BridgeApplyingProvider`
(`:767-811`) multiplies open/high/low/close and passes `volume=b.volume` through untouched, satisfying
goal.md's "volume is not a price and is not scaled" verbatim — verified with a non-unit factor (1.05 →
`o=10.5 h=12.6 l=9.45 c=11.55 vol=555.0`, volume unmoved).

Architecturally the "single write path" constraint holds: the transform is a provider *wrapper* injected
into the pre-existing `run_bounded_recovery_fetch` → `data_manager.run_data_job` engine, so no second
insert path was created. The diff is tightly scoped — `git diff --stat` shows four files, with
`yahoo_provider.py` docstring-only (8 lines) and no change to `models.py`, `db.py`, `app/config.py` or
`config.yaml`.

Where the domain work falls short is not the mechanism but the epistemics: the gate was run against an
input pair that could not disagree (finding B1), so this iteration proves the gate is *correctly built*
and does **not** prove it is *discriminating on real cross-vendor data*. The developer came close to
saying this — "this precommitment was not tested against a close call on the real run" — but attributed
the clean result to genuine cross-vendor agreement rather than to same-vendor identity.

---

## 4. Complete Database Mutation Reconciliation

All writes on 2026-08-21 (UTC), reconstructed from row timestamps and id ranges. Local file mtimes are
BST (UTC+1); DB timestamps are naive UTC.

| # | Table | Rows | Time (UTC) | Classification |
|---|---|---|---|---|
| 1 | `daily_prices` | **+40** (ids 3311385-3311424) | 00:10:17-00:10:58 | **Authorized recovery write** |
| 2 | `data_provider_runs` | +2 (542 yahoo fetch, 543 backfill) | 00:10:17, 00:10:58 | Authorized provenance record |
| 3 | `import_checkpoints` | +1 | 00:10:17 | Expected fetch-engine bookkeeping |
| 4 | `forward_aggregate_cache` | +5 | 00:12:33 | Expected derived-cache refresh |
| 5 | `scanner_runs` | +1 (id 3148, as_of 2026-08-12) | 00:26:04 | **Expected derived-state rebuild** (J-10 step 3) |
| 6 | `scanner_runs` | +1 (id 3149, as_of **2026-05-12**) | 00:26:13 | **Incidental product side effect** — see B5 |
| 7 | `scanner_runs` | +1 (id 3150, as_of 2026-08-11) | 00:28:16 | **Expected derived-state rebuild** (J-10 step 3) |
| 8 | `scanner_results` | +1,620 (539+542+539) | with 5/6/7 | Derived children of the three runs |
| 9 | `sector_scores` | +93 (31×3) | with 5/6/7 | Derived children |
| 10 | `theme_scores` | +33 (11×3) | with 5/6/7 | Derived children |
| 11 | `forward_returns` | +2,791 (2,771 for run 3149; 20 for run 3150; 0 for 3148) | with 5/6/7 | Derived children — 2,771 of these attach to the out-of-scope 2026-05-12 run |
| 12 | `membership_timeline_cache` | 1 (sole row, replaced) | 00:39:51 | Incidental — **caused by the forbidden replay lane (P1)** |
| 13 | `coverage_snapshot` | 1 (sole row, replaced) | 00:39:54 | Incidental — replay lane |
| 14 | `availability_cache` | 1 (sole row, replaced) | 00:39:55 | Incidental — replay lane |
| 15 | `market_phase_cache` | +2 | 00:40:05 | Incidental — replay lane |
| 16 | `event_study_cache` | +9 | 00:44:51 | Incidental — replay lane (backend still warm ~4 min after) |

**Unexplained / out-of-scope mutations: none.** Every write above is attributable and explained. Rows
12-16 were caused by the forbidden lane (P1) and post-date the developer's own post-state verification
(00:36:08 UTC), so nothing in the iteration verified them — this audit is their first accounting.

**Objective 1 — authorized scope: VERIFIED CLEAN.**
- Exactly 40 rows on exactly two dates: `2026-08-11` (20) and `2026-08-12` (20). No other date.
- Exactly 20 distinct symbols, set-equal to `CONVENTION_CHECK_SAMPLE_SYMBOLS`, all ⊆ `RECOVERY_SYMBOLS`.
  Zero symbols outside the authorized set; zero partial (one-date-only) restorations.
- `MAX(date)` = `2026-08-12`; rows on/after `2026-08-13` = **0**. Frontier never advanced.
- The 40 ids are **contiguous at the very tail of the table** (`MAX(id)` = 3311424) — a pure append.
- **No surviving row overwritten**, established three ways: (a) the driver's own machine-recorded
  pre/post snapshot shows `rows_before_2026_08_11` = 3,309,204 → 3,309,204 and
  `sum_close_before_2026_08_11` = 481248846.4362307 → 481248846.4362307, bit-identical; (b) total rows
  3,309,204 → 3,309,244 = +40 exactly, which I confirmed live; (c) the write path is a plain
  `insert(DailyPrice.__table__)` (`data_manager.py:3233`) filtered by the `_existing_dates` skip guard
  (`:2818-2828`, `:3213-3215`) — INSERT-only, no UPDATE or upsert anywhere on the path.

**Objective 4 — field-level integrity: VERIFIED.** `daily_prices` stores open/high/low/close/volume.
All four price fields were transformed (`j10_recovery.py:807-810`); volume was not. OHLC invariants
(`low ≤ min(open,close)`, `high ≥ max(open,close)`, `high ≥ low`) hold on **all 40 rows, zero
violations**; zero null or negative volumes. Field-level convention compatibility is *provable* here
rather than merely plausible, because — per finding B1 — the restored fields come from the same provider
method and field as every adjacent stored bar. One honest caveat: since every bridge factor was exactly
1.0, the transform was the identity on live data, so the live run cannot empirically distinguish scaled
from unscaled volume; that distinction rests on the code and on the unit test using a 1.05 factor.

**Objective 5 — the 2026-05-12 `ScannerRun`: confirmed benign, but wrongly labelled.** It changed no
`daily_prices` row (zero rows written after 00:10:58; totals unchanged), changed no manifest, and
performed **no network fetch** (no `data_provider_runs` row exists after id 543, whose `finished_at` is
00:12:33 — 14 minutes before the run was created). It was computed from already-committed data. It is
nonetheless a persistent, out-of-scope mutation carrying 3,355 child rows, and — contra the handoff — it
is unrepaired iter-5 drill damage, not an unrelated cadence gap (B5). **This iteration must not be
described as having made "no out-of-scope writes."**

---

## 5. Objective-by-Objective Results

| # | Objective | Result |
|---|---|---|
| 1 | Authorized scope | **PASS** — 40 rows, 20 authorized symbols, exactly 2 authorized dates, pure append, no overwrite, frontier not advanced |
| 2 | Per-symbol fail-closed evidence | **PASS** — verified by adversarial probe, not by population argument; `agree` unreachable below 3 comparable pairs; thresholds are module literals with no parameter on any function; authorized-date assertion enforced in code (B6) |
| 3 | Bridge calibration | **PASS on arithmetic, FAILS as cross-vendor evidence** — recomputation matches all 20 records exactly (see below); inputs come solely from the persisted artifact; single provider instance used for both calibration and fetch; **but** the comparison was Yahoo-vs-Yahoo (B1) |
| 4 | Field-level price integrity | **PASS** — all four price fields bridged, volume never scaled, OHLC invariants hold on 40/40 rows |
| 5 | DB mutation accounting | **RECONCILED by this audit** — 11 tables, ~4,600 rows; none unauthorized; handoff's own accounting incomplete (B4) |
| 6 | Manifest / provenance integrity | **PASS** — see below |
| 7 | Recovery completeness | **20 restored / 567 still pending** — confirmed by independent recomputation; idempotent |
| 8 | Audit the audit fixes (B2/B3/B5/B6 + fail-open) | **PASS** — all four resolved and adversarially verified |

**Objective 3 — bridge re-derivation (independent, from the persisted artifact only).** I recomputed
`mean(stored/fallback)`, `(max−min)/mean` dispersion, and the rebased path-agreement max delta for all
20 symbols from `runs/goal-market-compass-iter-8/j10-convention-evidence.json`, and compared against the
recorded values at `<1e-12`: **20/20 match, zero discrepancies.** 88 pairs total, 88 comparable, zero
pairs with a missing fallback. Every symbol: `bridge_factor = 1.0`, `dispersion = 0.0`,
`path_delta = 0.0`. The developer's "every bridge factor was exactly 1.0" is confirmed — and confirmed
to be exactly 1.0 because `stored_close == fallback_close` bit-for-bit on all 88 pairs, which is the
same-vendor artifact of B1, not measured cross-vendor agreement. No second live provider query supplied
a calibration input: `run_gated_recovery` calls the check once and, with `fetch_provider` omitted,
reuses the *same provider instance* for the restoration fetch (`j10_recovery.py:882`).

**CVX specifically (charter objective 6).** iter-7 reported CVX at ~0.865% mismatch; iter-8 returns
`agree` with 5 comparable pairs and a bridge of exactly 1.0. **iter-8 does prove iter-7's number was a
series-crossover artifact rather than a genuine raw-close mismatch** — but the correct explanation is
not the one in the handoff. The stored side was always Yahoo's **raw** close; iter-7 compared it against
Yahoo's **adjusted** close (`get_adjusted_close`), so the ~0.865% on CVX and ~0.643% on XOM is the
accumulated dividend adjustment *within a single vendor* — which is exactly why both offenders were
high-yield energy names and why the deltas were uniform within each symbol. It was never Stooq-adjusted
vs Yahoo-adjusted. B2's "one series, end to end" fix removed the crossover and the artifact vanished, as
designed. CVX's five pairs (190.39999389648438, 186.41000366210938, 189.22999572753906,
186.55999755859375, 194.91000366210938) are bit-identical on both sides.

**Objective 6 — manifest / provenance integrity: PASS.** `next_session_manifests` holds 24 rows,
`MAX(id)` = 24, `MAX(as_of)` = 2026-08-12 — unchanged. **All 24 `created_at` values are ≤ 2026-08-20
14:54:02**, i.e. every row predates iteration 8; no row was created or re-created. **Zero rows have
`prospective_eligible = 1`** — no eligibility upgrade occurred, and none could have: manifest 23
(as_of 2026-08-12, version 6) remains `prospective_eligible = 0`. All `available_at_utc` values predate
the iteration. The driver's own pre/post snapshot records `manifest_hashes_identical: True` and a stable
24-row hash tuple. At the file layer, every export under
`apps/backend/data/exports/next_session_manifests/` has an mtime ≤ 2026-08-20 15:50:58 local — **no
export file was rewritten**, so AG-12 holds at both the row and file layers. Repair activity did not
make any old artifact prospective; artifacts from the damaged interval remain governed by AG-17, and
`reports/qa/goal-market-compass-iter-6-evidence/` is byte-unchanged (all mtimes ≤ 2026-08-20 21:47:50).

On the reported `GET /api/compass?as_of=2026-08-12` → HTTP 200: I could not call it (starting the
backend is prohibited under this charter), but the code path corroborates the report exactly.
`compass.basis_disclosure` (`compass.py:1100-1115`) returns `{"status": "unavailable"}` when no
`ScannerRun` exists for the as-of, and `{"status": "rebuilt", "detail": "the source scanner run was
recreated after this manifest was frozen"}` when the current run's `created_at` differs from the
manifest's recorded `source_run_created_at`. Manifest 23 points at `source_run_id` 3081, which the
iter-5 drill deleted (id 3081 appears in run 538's `cascade.run_ids`); run 3148 for 2026-08-12 now
exists with `created_at` 2026-08-21 00:26:04. The endpoint therefore serves with an honest `rebuilt`
disclosure and does not mutate the frozen content — as reported. Note that it serves **only because of
the backend-boot side effect**, not because of the developer's explicit backfill, which created zero
snapshots.

**Objective 7 — completeness semantics.** Independently recomputed against the live database using the
module's own constants: `RECOVERY_SYMBOLS` = 587 (MNST excluded), fully restored = 20, **still missing =
567**, restored set set-equal to the sample, zero partial restorations. **iter-8 is not J-10 completion.
The correct state is `20 restored / 567 still pending` (3.4%).** The mechanism working is not the same
as the journey being done, and the developer was right to decline the mid-task instruction to widen the
sample after seeing a good result — the spec's OUT OF SCOPE forbids exactly that, with no carve-out for
a favourable early result, and declining was the correct call. Idempotency is verified two ways:
`still_missing_symbols()` recomputes from live state and now excludes all 20 restored symbols, and
`run_bounded_recovery_fetch` intersects any caller-supplied list with that live set
(`j10_recovery.py:739-742`), so a re-run cannot re-request or re-write a restored symbol.

**Objective 8 — the audit fixes, independently verified.**

| Fix | Status | Verification |
|---|---|---|
| **B2** (validated series == inserted series) | **RESOLVED** | Both calibration and restoration call `provider.get_daily` (`:643`, via `run_bounded_recovery_fetch`); `get_adjusted_close` is unreferenced by the live gate. `test_per_symbol_check_uses_get_daily_never_get_adjusted_close` (`:484`) installs a provider whose `get_adjusted_close` calls `pytest.fail` — a real crossover trap, not an assertion about intent |
| **B3** (per-pair evidence persisted, auditable) | **RESOLVED** | 23 KB artifact exists with all 88 pairs; `convention_evidence_to_dict` serializes every field with no summarization; written at `:869-871` **before** `passing` is computed at `:873`. `test_gated_recovery_persists_evidence_before_any_verdict_is_used` (`:595`) proves persistence on the *stop* path. I re-derived every published number from this artifact alone |
| **B5** (thresholds not caller-overridable) | **RESOLVED** | `inspect.signature(run_gated_recovery)` = `{session, engine, config, convention_provider, fetch_provider, api_key, evidence_path}` — no tolerance, dispersion, sample or window parameter. `_compute_symbol_verdict` takes `{symbol, window_dates, stored, fallback}` and reads thresholds from module globals only. `test_gated_recovery_has_no_threshold_or_scope_override_parameters` (`:771`) pins the exact parameter set with set equality |
| **B6** (authorized dates asserted at the transform) | **RESOLVED** | `_BridgeApplyingProvider.get_daily` (`:802-806`) raises `RecoveryScopeError` on any bar outside `[RECOVERY_START, RECOVERY_END]`. Probed live: a 2026-08-13 bar is refused; a symbol with no passing factor is refused |
| **Zero-evidence fail-open** | **IMPOSSIBLE** | Ten degenerate inputs probed (table in §3); `agree` never returned below 3 comparable pairs; mismatch never downgraded by a coverage gap; an empty sample or window yields `verdicts=()` → `passing={}` → `stopped_reason` set with no write-capable call reachable |

Also verified: `validate_recovery_scope` refuses all five out-of-envelope request shapes (date after the
window, range extending before it, MNST, wrong vendor, empty symbol list).

**Test runs (targeted single files, one process at a time, detached and polled in-turn per host-safety
constraints):**
- `.venv/bin/python -m pytest tests/test_j10_recovery.py -q` → **37 passed** in 2.04s
- `.venv/bin/python -m pytest tests/test_provider_clients.py -q` → **50 passed** in 0.12s

Both match the handoff's reported counts. The full suite was never invoked. Peak memory headroom
remained ~21 GB available.

---

## 6. Fixes Applied During This Audit

**None — by charter.** This was a read-only forensic pass. No source file, database row, manifest,
threshold, symbol set, or goal.md text was modified; no network fetch was performed; no recovery write
was made; no backend or frontend was started. All database access used `file:...?mode=ro` URIs, and all
write-path probing used in-memory SQLite fixtures.

Findings B1-B5 and P1-P2 are therefore carried forward as unresolved, for the evaluator and owner.

---

## 7. Recommended Next Step

**The evaluator may proceed to read this iteration's result, but must not accept it as a clean
full-depth pass, and must not accept the J-01/J-04 replay PASS as journey evidence.**

Carry forward to the evaluator, explicitly:

1. **`Depth: full` was dispatched as `lean`** (`depth-dispatched` = `lean` vs spec line 9 = `Depth:
   full`), the third demotion this session. No reviewer report and no QA report exist for iteration 8.
   This audit is supplemental scrutiny, **not** evidence that the full-depth requirement was met.
2. **A forbidden replay lane ran against J-01 and J-04**, starting a frontend and a second backend. Its
   `PASS` verdict in `reports/phase-goal-market-compass-iter-8-regression-replay-results.md` was
   produced against a database that is 3.4% recovered and carries no quarantine marker. It should be
   quarantined the way iter-6's equivalent evidence was, and TC-19 should be treated as violated.
3. **The recovery is 20/587 — `20 restored / 567 still pending`.** iter-8 is not J-10 completion. The
   developer's decision to hold AG-9's exception open rather than declare it exhausted is correct and
   should stand.
4. **Two statements in the dev handoff are factually wrong** and should be corrected before the handoff
   is cited as evidence: the "Stooq stored close vs Yahoo raw close are byte-identical" claim (the
   stored side is Yahoo — B1/B2), and the "2026-05-12 is wholly unrelated to this incident" claim (it is
   one of the 11 snapshots the iter-5 drill destroyed — B5).
5. **The iteration made out-of-scope writes.** Roughly 4,600 rows across 11 tables, including a
   2026-05-12 `ScannerRun` with 3,355 child rows and five cache tables written by the forbidden lane. All
   are benign and now reconciled, but the iteration must not be described as having made none.

Recommended work for iteration 9, in priority order:

- **Fix the depth arbiter first**, before any further recovery batch. Three silent demotions in one
  session means the spec's depth contract is not being honoured, and it is what let the forbidden lane
  run. This is framework work, deliberately out of the present charter's scope.
- **Re-run the convention gate against a window that actually spans the vendor boundary** if a genuine
  cross-vendor convention proof is wanted — for example stored bars at or before 2026-07-01 (Stooq seed)
  against a Yahoo fetch of the same dates. The current gate is correctly built and would then be
  meaningfully exercised. Note this needs a fresh dated goal.md amendment: AG-9's exception authorizes a
  comparison fetch only over "already-surviving trading days (≤ 2026-08-10)" for the proven-missing
  symbols, and the owner should decide whether a seed-era comparison window is in or out.
- **Then** run further precommitted batches against the remaining 567 symbols, each sample fixed and
  documented before it runs.
- Record the seed-boundary vendor discontinuity (B3) as a known, pre-existing, unexamined data property
  so no future study mistakes post-2026-07-01 history for Stooq-adjusted data.

---

## 8. Addendum — `docs/goal.md` was amended while this audit was running

`docs/goal.md` changed at **2026-08-21 08:14:45 local**, mid-audit, by the owner (+108 lines, uncommitted
at the time of writing). I did not make this edit and have not modified the file. The amendment adds
J-10 steps **2b/2c/2d** and **5a**, a **Completion rule**, a **Traps this journey must actually prove**
list, and a Constraints entry on depth demotion. It was clearly written in response to iteration 8.

It independently corroborates most of this audit, arriving at the same conclusions from the owner's side:

- **5a** now requires that recovery verification "reconcile **all** database mutations caused by the
  verification procedure itself," classify each as authorized/incidental, and never claim "no
  out-of-scope writes" when the application produced an unrelated persistent row. That is finding B4 and
  charter objective 5, now contract.
- The **Completion rule** states J-10 "does **NOT** close merely because the recovery mechanism has been
  demonstrated on 20 names," forbids inventing a partial-completion threshold, and step 6 now reads that
  "a partial restoration does not exhaust the exception." That matches objective 7 and this audit's
  `20 restored / 567 still pending`.
- **2d** confirms the 20 restored symbols "stay restored… Do not delete or revert them merely to restart
  the recovery," and requires the next pass to be idempotent over them — consistent with this audit's
  finding that the 40 rows are sound and with the idempotency I verified.
- **2b** clarifies that the anti-goodharting rule caps the *methodology-validation sample*, not the
  *recovery population*, so it "does not cap recovery at the first 20 symbols." Note for the record: the
  iteration-8 developer's refusal to widen was correct **under the spec as written at the time** (its
  OUT OF SCOPE forbade widening the comparison sample after seeing a result, with no carve-out); the
  amendment resolves a genuine ambiguity going forward rather than reversing a bad call.
- The **Traps** list items 9 and 10 name exactly this audit's objective-5 reconciliation requirement and
  the depth-demotion prohibition, and the new Constraints entry records the demotion count as three
  (iters 2, 6, 8), matching finding P2.

**One correction the evaluator must carry into the amended contract.** Under "Recorded finding — the
one-series rule worked (iteration 8, keep this)", goal.md now states: *"Yahoo's raw close matched
Stooq's stored close exactly over the overlap window."* Per findings **B1** and **B2**, the stored side
of that comparison is **not** Stooq — it is Yahoo, fetched by `data_provider_runs` ids 297/528/529 on
2026-08-04..2026-08-14, five to six weeks past the Stooq seed's 2026-07-01 boundary, and carrying
Yahoo's float32 fingerprint on 100% of sampled rows versus ~2-4% in the seed era. The developer's
mischaracterization has been adopted into the goal contract.

The amendment's **operative conclusions are unaffected and remain correct**: the one-series rule did fix
the CVX false mismatch (the artifact was Yahoo-`adjclose`-vs-stored-raw-close, a crossover *within one
vendor* rather than between two — see §5), and the finding is indeed "NOT grounds for removing,
weakening, or skipping the convention gate." Only the vendor attribution in that one sentence is wrong.
It should be corrected before any future study cites it, because as written it reads as measured
cross-vendor evidence and AG-9 step 2a forbids this recovery being cited that way.

I have **not** edited `docs/goal.md` — amending the goal contract is the owner's action, and this
charter is read-only.
