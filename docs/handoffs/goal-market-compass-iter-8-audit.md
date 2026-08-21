# goal-market-compass-iter-8 Audit Report

**Date:** 2026-08-21
**Auditor:** Hard audit pass — skeptical, evidence-based (in-pipeline lane, `full` depth)

**Note on the prior out-of-band audit.** An owner-commissioned out-of-band audit of this iteration
exists in git at commit `47d50d04` (`docs/handoffs/goal-market-compass-iter-8-audit.md`, 509 lines,
verdict ESCALATE); it is deleted in the working tree because this file replaces it at the same path.
I read it and treated every one of its findings as a claim to re-derive, not a fact to inherit. Where
I confirm it below, I confirm it from evidence I gathered myself (different route where possible);
where I extend or correct it, I say so. Its substance is preserved in this report and its original
text remains recoverable at `git show 47d50d04:docs/handoffs/goal-market-compass-iter-8-audit.md`.

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The iteration's build work and its first live write to the production database are **sound**: the
redesigned per-symbol gate is genuinely fail-closed, the 40 restored rows sit inside the authorized
envelope as a pure append with no surviving row overwritten, and all 20 bridge factors re-derive from
the persisted per-pair artifact to `<1e-12`. What does **not** hold up is the iteration's *evidence
narrative* and its *process controls*: the gate's headline "agreement" result is a same-vendor
tautology (the stored comparison series is Yahoo, not Stooq), the mutation accounting named 3 of 14
tables actually written, and the spec's TC-19 was violated **twice** — the second time **during this
very full-depth re-run**, which overwrote quarantined incident evidence that AG-17 protects.

I fixed what was fixable inside this lane (restored the destroyed evidence byte-for-byte from git,
preserved the recurrence evidence alongside it, and appended dated corrections to the dev handoff for
all three false claims). I considered **FAIL** and rejected it: the phase's build objective was met,
no data is corrupted, and after this audit no CRITICAL finding remains unresolved. **J-10 itself is
not complete** — `20 restored / 567 still pending` — and `docs/goal.md` is explicit that recovery
"cannot leave J-10 complete at `20/587`".

---

## 2. Definition of Done — risk-ranked verification

Full code trace performed for every item touching data mutation, state transitions or persistence,
for every item any artifact contradicts, and for every item my own probing raised. Mechanical items
already executed against the running system by QA are accepted with citation.

| # | DoD item | Result | Basis |
|---|---|---|---|
| 1 | Two-part gate, per symbol, thresholds as module literals | **MET** | Full trace. `j10_recovery.py:349-385` (three frozen literals), `:482-599` (`_compute_symbol_verdict`), `:602-660` (orchestration). Ladder order verified: `<2 comparable → inconclusive` (`:531`), **mismatch branch** (`:554-572`), **then** the `MIN_COMPARABLE_PAIRS` floor (`:576`), then `agree`. Both metrics recomputed by me from the live artifact for all 20 symbols — exact match |
| 2 | Evidence persisted before any verdict is interpreted (B3) | **MET for this run** | Full trace. `:868-871` writes the artifact; `:873` is the first line that reads a verdict. `runs/goal-market-compass-iter-8/j10-convention-evidence.json` exists, 20 symbols / 88 pairs; I re-derived every published number from it alone. See **B4** for the residual structural gap |
| 3 | Bridge applied to all four price fields, volume never scaled, no raw insert | **MET** | Full trace. `_BridgeApplyingProvider.get_daily` (`:807-810`) multiplies `open/high/low/close`, passes `volume=b.volume`; the sink `data_manager.py:3214-3224` writes exactly those Bar fields. All 40 live rows satisfy `low ≤ min(open,close)`, `high ≥ max(open,close)`, zero non-positive or non-integer volumes |
| 4 | Same provider method/field for calibration and restoration (B2) | **MET** | Full trace. Calibration `:643` `provider.get_daily(...)` → `b.close`; restoration `run_bounded_recovery_fetch` → `run_data_job` → `_fetch_symbol_with_retry` → `provider.get_daily` (`data_manager.py:3036`). `get_adjusted_close` is unreferenced by the live gate. Caveat at **B5** |
| 5 | Thresholds not parameters on the production entry point (B5) | **MET** | Full trace. `run_gated_recovery` signature (`:831-840`) = `{session, engine, config, convention_provider, fetch_provider, api_key, evidence_path}`; pinned by set-equality in `test_j10_recovery.py:771-779` |
| 6 | Live gated recovery ran; honest per-symbol outcome; non-restored named | **MET** (spec-literal) | Full trace + live DB. 20/20 sampled symbols `agree`, so "requested but not restored" is correctly empty; 567 recorded as *never attempted*. Note the journey-level consequence in §6 |
| 7 | `RECOVERY_SYMBOLS` (587, MNST excluded) and `RECOVERY_SOURCE` read unchanged | **MET** | Full trace. Parsed both sides of `47d50d04`: set size 587 → 587, **zero added, zero removed**; no diff line touches `RECOVERY_SOURCE`/`RECOVERY_DATES`/`RECOVERY_START`/`RECOVERY_END` |
| 8 | Step 5 (a)-(f) executed directly by the developer and recorded | **MET** | Recorded in the dev handoff's step-5 table with an honest PARTIAL on (a) and (f). The `GET /api/compass?as_of=2026-08-12` → 200 was executed against a single transiently-started backend, as the spec's NOTES authorize. Corroborated by QA §3 and by the DB state I re-queried |
| 9 | AG-9 exception NOT declared exhausted on a partial result | **MET** | Handoff "Step 6 — exception closure" declines exhaustion explicitly and correctly |
| 10 | AG-17 holds: no manifest change; incident records byte-unchanged | **PARTIAL** | Manifest half **MET** by my own query: `next_session_manifests` = 24 rows, `MAX(as_of)` = 2026-08-12, `SUM(prospective_eligible)` = **0**. `reports/qa/goal-market-compass-iter-6-evidence/` byte-unchanged (git-clean, all mtimes ≤ 2026-08-20 21:47:50). **Failed** for this iteration's own quarantined evidence — see **P1** |
| 11 | No Yahoo/Stooq interchangeability wording anywhere | **MET** (letter) / **at risk** (spirit) | `grep` finds only the disclaimer at dev handoff `:403`. But the handoff asserts a measured cross-vendor *identity*, which is the stronger claim AG-9 step 2a is guarding — see **B1** |
| 12 | `_parse_adjusted_close` synthetic-payload tests, one per branch (T2) | **MET** | My own run: `pytest tests/test_provider_clients.py -q` → **50 passed in 0.13s**. Six new branch tests present (`test_yahoo_adjusted_close_*`) |
| 13 | 27 pre-existing tests (restructured where required, reasons documented) + new tests pass | **MET** | My own run: `pytest tests/test_j10_recovery.py -q` → **37 passed in 2.12s**. 15 pre-existing unchanged + 12 replaced (reason documented in the handoff) + 22 new |
| 14 | **No browser-QA or deterministic-replay lane runs against J-01–J-04 (TC-19)** | **VIOLATED — twice** | Full trace. See **P1/P2**. This is the one DoD item that is definitively unmet |
| 15 | Coherence check confirms no new displayed value/endpoint/route/second write path (TC-18) | **NO ARTIFACT; substance verified by me** | `runs/goal-session-market-compass/iter-8/coherence.md` does not exist (iters 1-4, 6, 7 all have one). I traced it directly instead: no route/endpoint added, no new computing module, and the transform is a *provider wrapper* injected into the pre-existing `run_data_job` engine — single write path intact. See **P4** |
| 16 | `reports/qa/goal-market-compass-iter-6-evidence/` byte-unchanged | **MET** | git-clean; all mtimes ≤ 2026-08-20 21:47:50 |
| 17 | `depth-dispatched` reads `full` | **MET now, NOT at dispatch time** | Reads `full` today; read `lean` at `47d50d04`. The developer flagged this honestly (Known Issue 7) and correctly declined to edit the marker |
| 18 | Dev handoff written | **MET** | `docs/handoffs/goal-market-compass-iter-8-dev.md` (now carrying my appended corrections) |

**Live database state — verified independently, read-only (`file:…?mode=ro`), never opened for write:**
`daily_prices` MAX(date) = **2026-08-12**; 20 rows on 2026-08-11 and 20 on 2026-08-12; **0** rows on
or after 2026-08-13; the 40 rows occupy ids **3311385-3311424, contiguous at the table tail**
(MAX(id) = 3311424), total 3,309,204 → **3,309,244** (+40 exactly, a pure append);
`data_provider_runs` MAX(id) = **543**; `next_session_manifests` **24** rows, MAX(as_of)
**2026-08-12**, 0 eligible; `scanner_runs` **3121** rows, MAX(id) 3150, MAX(asof_date) **2026-08-12**.
Every value the coordinator pre-registered as expected is confirmed.

---

## 3. Findings

### Backend / Evidence Findings

**B1 — IMPORTANT (fixed): the gate's "agreement" result is a same-vendor tautology; the handoff
asserts a cross-vendor identity the evidence contradicts.**

`docs/handoffs/goal-market-compass-iter-8-dev.md:175-180` states *"Stooq's stored close and Yahoo's
raw `get_daily` close are byte-identical for every sampled (symbol, date) pair in this window"*, and
`:191-194` explains iteration 7's CVX delta as *"comparing Stooq-adjusted against Yahoo-adjusted"*.
**The stored side is Yahoo, not Stooq.** I established this four ways, independently:

1. `apps/backend/data/seed/meta.json` — the committed Stooq seed's window ends **2026-07-01**; the
   comparison window (2026-08-04 … 2026-08-10) is five to six weeks past it.
2. `data_provider_runs` provider tally, whole table: `seed: 508, yahoo: 34, stooq: 1`. The one
   `stooq` row is **id 541, `status='failed'`, `symbols_ok=0, symbols_failed=587`** — Stooq has never
   written a bar here. There are **zero** `seed`-provider rows with `kind: "fetch"`, so every bar
   after the seed boundary came from a `yahoo` fetch (ids 527/528/529 cover 2026-08-03 … 2026-08-13).
3. Float32 round-trip fingerprint on `daily_prices.close` (400-row samples per date): 2000-06-15
   **1.7%**, 2020-06-15 **2.0%**, 2026-07-01 **3.8%**, then 2026-07-02 **100.0%**, 2026-08-05
   **100.0%**, 2026-08-10 **100.0%**, 2026-08-11/12 **100.0%**. The discontinuity lands exactly on
   the seed boundary.
4. All **88 of 88** pairs in the evidence artifact have `stored_close == fallback_close` bit-for-bit
   and `ratio` exactly `1.0` — the signature of one vendor re-fetched, not two vendors coinciding.

Consequence: the gate ran against an input pair that **could not disagree**, so this run proves the
gate is correctly *built*, not that it is *discriminating*. Crucially, this does not make the write
unsafe — it makes it safer: restored bars and adjacent surviving bars are both Yahoo raw close, so no
scale discontinuity was introduced at the two recovery dates, which is the property that actually
mattered. Severity: I weighed CRITICAL and chose IMPORTANT — no data is corrupted and the build
objective was met; what failed is the demonstration, not the mechanism.

*Fix applied:* correction **C1** appended to the dev handoff, including the corrected CVX explanation
(iter-7's ~0.865% was Yahoo-`adjclose`-vs-Yahoo-raw — an intra-vendor crossover, which is exactly why
B2's one-series fix dissolved it).

*Unfixable here — owner action required:* the mischaracterization has been carried into
`docs/goal.md` under "Recorded finding — the one-series rule worked (iteration 8, keep this)", which
now reads *"Yahoo's raw close matched Stooq's stored close exactly over the overlap window."*
Amending the goal contract is the owner's action; I did not touch `docs/goal.md`. The finding's
operative conclusions are unaffected — only the vendor attribution is wrong.

**B2 — IMPORTANT (fixed): the 2026-05-12 `ScannerRun` is unrepaired drill damage, not an unrelated
cadence gap.**

The handoff calls it *"a date wholly unrelated to this incident"* (`:245`, `:266-267`). I read
`data_provider_runs` id=538 — the drill's own removal record — directly:
`cascade.snapshot_count: 11`, `cascade.snapshot_dates: ['2026-05-12', '2026-05-13', '2026-07-10',
'2026-07-13', '2026-07-24', '2026-07-27', '2026-08-03', '2026-08-05', '2026-08-10', '2026-08-11',
'2026-08-12']`. **2026-05-12 is the first entry.** Benign but mislabelled: run 3149's forward returns
span 2026-05-13 … 2026-08-10 (2,771 rows) with **zero** rows measuring on or after 2026-08-11, so
none of its arithmetic reads the damaged region; it created no `daily_prices`, manifest or
`data_provider_runs` row. *Fix applied:* correction **C2**.

**B3 — IMPORTANT (fixed): mutation accounting named 3 tables; 14 tables and ~4,602 rows were
written.**

The handoff states "no other table (`daily_prices`, `next_session_manifests`) was touched". My own
reconciliation of all 2026-08-21 writes: `daily_prices` +40, `data_provider_runs` +2,
`import_checkpoints` +1, `forward_aggregate_cache` +5, `event_study_cache` +9, `scanner_runs` +3
(3148 = 2026-08-12, 3149 = **2026-05-12**, 3150 = 2026-08-11), `scanner_results` +1,620,
`sector_scores` +93, `theme_scores` +33, `forward_returns` +2,791, plus four cache tables written by
the forbidden replay lane (`membership_timeline_cache`, `coverage_snapshot`, `availability_cache`
each 1 sole row replaced; `market_phase_cache` +2). **14 distinct tables, ≈4,602 rows; every write
attributable, none unauthorized.** This also refines the out-of-band audit, which counted "11 tables"
— its own table lists 14 distinct tables across 16 rows. *Fix applied:* correction **C3**, with the
full table.

**B4 — GAP (observation): `evidence_path` is optional on the production entry point, so B3's
guarantee rests on driver discipline — the exact weakness B5 was raised to remove.**

`run_gated_recovery(..., evidence_path: Optional[Path] = None)` (`j10_recovery.py:839`); when omitted,
a live run computes verdicts and acts on them with **nothing persisted**. This run passed a real path,
and the spec's DoD is therefore met — but the next batch against the remaining 567 symbols could omit
it silently. B5's own rationale ("precommitted lives in operator discipline, not code") applies here
verbatim. Not fixed: making it mandatory is a signature change beyond this audit's remit, and it would
break the tests that legitimately omit it. Recommended for iteration 9.

**B5 — GAP: `fetch_provider` remains caller-settable, so a vendor-level crossover is still reachable
even though the method/field crossover is closed.**

`run_gated_recovery` accepts `fetch_provider: Optional[PriceProvider] = None` (`:837`), defaulting to
`convention_provider`. The live run correctly omitted it, giving one provider instance for both roles.
But B2's fix guarantees the same *method and field* (`get_daily` → `close`), not the same *vendor
object*: a caller passing a different provider would calibrate on one vendor and insert another,
while `validate_recovery_scope` still sees the hardcoded `source="yahoo"` string and passes.
Exploiting this needs a code diff at the call site, so it sits inside the risk model B5 accepted — but
it is worth an assertion (e.g. refuse a `fetch_provider` that is not the `convention_provider`).

**B6 — GAP: `run_bounded_recovery_fetch` remains public and un-gated.**

A direct call with a raw provider inserts unbridged values with no convention check at all,
side-stepping `run_gated_recovery` entirely. Pre-existing since iter-6, exercised legitimately by
tests, and it requires new caller code — so this is defence-in-depth, not a live hole. Recorded
because the live recovery driver is an *uncommitted ad-hoc script* (see B8), which makes "the next
driver calls the wrong function" a more realistic failure mode than it would otherwise be.

**B7 — OBSERVATION (pre-existing, outside J-10): a genuine, un-gated vendor discontinuity exists in
`daily_prices` at the seed boundary.**

The series changes vendor between 2026-07-01 (Stooq seed, split/dividend-adjusted) and 2026-07-02
(Yahoo raw close) — created by ordinary fetches in mid-August, long before this incident, and never
examined by any convention gate. It is not iter-8's doing and is outside its authorization. Recorded
because it is precisely the discontinuity the owner's gate was designed to catch, and because any
future convention work must start from this fact rather than from the assumption that post-seed
history is Stooq.

**B8 — OBSERVATION: the live run is not reproducible from the repository.**

No recovery driver script is committed (none for iter-7 either), and `runs/goal-market-compass-iter-8/plan.md`
— named in this lane's own dispatch as the execution plan — does not exist. The machine-readable
trail (`j10-convention-evidence.json` + `data_provider_runs` 542/543) is adequate for audit, so this
is a reproducibility gap, not an evidence gap.

### Process / Pipeline Findings (no frontend surface this iteration)

**P1 — CRITICAL (fixed): the forbidden replay lane ran a SECOND time, at `full` depth, and overwrote
quarantined incident evidence that AG-17 protects.**

This is new — no other lane in this pipeline caught it, and it post-dates the out-of-band audit.
`reports/qa/goal-market-compass-iter-8-evidence/INVALID-forbidden-lane.md` was placed at 08:30 today
and states the two screenshots "stay; they are labelled invalid". At **12:53-12:55 the same day** —
inside the full-depth re-dispatch commissioned to add this very audit lane — the UI/replay chain ran
end to end again and **re-executed the J-01/J-04 deterministic replay**, overwriting both files:

| file | quarantined bytes (`47d50d04`) | bytes written 12:54-12:55 |
|---|---|---|
| `J-01-verify.png` | md5 `bd13782d00c37abd0a0ee4a17eeb852d` | md5 `eaacb5973639ca0dd96c695b968534fb` |
| `J-04-verify.png` | md5 `9e9cc6fe68e08e08ab496d6be6c081bd` (134,545 B) | md5 `190d16c0f5f8f0df0ec38396a68ee418` (134,514 B) |

Corroborating chain: `…-ui-surface-map.md` 12:53:06 → `…-ui-test-plan.md` 12:53:57 →
`…-what-to-click.md` 12:54:12 → the two PNGs 12:54:58 / 12:55:02 → `…-regression-replay-results.md`
re-written 12:55:02 (byte-identical content, same `PASS` rows for UT-J-01/UT-J-04) → merged
`…-ui-test-results.md` 13:01:14. A Next.js frontend was started for it
(`fanout-frontend-8255.log`: "Ready in 270ms" … "Killed") and a backend start was attempted
(`fanout-backend-8255.log`, created 12:48:07, empty) — both forbidden by this spec's OUT OF SCOPE on
a host under a standing memory constraint. AG-17 is a *critical* anti-goal and forbids the incident
record being "deleted, rewritten, or silently superseded"; the specific files that note names were
silently superseded.

**Mitigating fact, verified:** the second lane made **no database writes**.
`apps/backend/data/trendora.db-wal` has not been written since 2026-08-21 01:44:51 local, and every
derived/cache row created on 2026-08-21 carries a timestamp ≤ 00:44:51 UTC.

Severity: I weighed IMPORTANT and chose CRITICAL per the honesty rule, because protected incident
evidence was destroyed under a *critical* anti-goal — while noting the loss was recoverable from git,
which is why it could be fixed here. *Fix applied:* originals restored byte-for-byte from `47d50d04`
(hashes re-verified post-restore), the second run's bytes preserved as
`INVALID-rerun-2026-08-21T1254-J-0{1,4}-verify.png` so the recurrence evidence is not destroyed
either, and a dated addendum appended to `INVALID-forbidden-lane.md`.

**P2 — IMPORTANT (gap, not fixable in this iteration): TC-19 is violated at BOTH depths.**

The quarantine note attributes the first occurrence to lean depth auto-enabling
`CHAIN_LEAN_PARALLEL_BROWSER_QA`. **`depth-dispatched` now reads `full`, and the replay lane ran
anyway.** So the depth arbiter is not the whole mechanism: the pipeline's UI/replay chain has no
awareness of the spec's TC-19 prohibition or of `docs/goal.md`'s lane gate at either depth. The DoD
item is unmet and cannot be closed by anything inside this iteration — it is upstream framework work
on the lane gate, not just the depth arbiter.

**P3 — IMPORTANT (gap): a factual error in the review report will otherwise propagate to the
evaluator.**

`reports/reviews/goal-market-compass-iter-8-review.md` (NOTE item) records the forbidden lane as
"already remediated (depth-dispatched now reads full)". Per P1/P2 that is wrong: the marker was
corrected **and the lane ran again afterwards**. The ux-regression report inherits the same framing
("that correction happened after the forbidden lane had already run once"). Both were written before,
or without sight of, the 12:54 recurrence. I did not edit either report — a lane's own verdict is not
rewritten by a later lane — so the evaluator must take the correction from here.

**P4 — GAP: TC-18 has no coherence artifact.**

`runs/goal-session-market-compass/iter-8/coherence.md` does not exist, while iterations 1-4, 6 and 7
all have one. The coherence-auditor may still run before the evaluator; as of this audit the DoD item
has no artifact behind it. I traced the substance myself and it holds — no new endpoint, route,
displayed value or computing module, and `run_data_job` remains the single write path (the bridge is
a provider *wrapper* injected into it, `j10_recovery.py:882-885`).

### Test Findings

**T1 — OBSERVATION: evidence-persistence ordering is proven on the stop path only.**
`test_gated_recovery_persists_evidence_before_any_verdict_is_used` (`test_j10_recovery.py:595-620`)
asserts persistence when zero symbols pass — a good choice, since it proves persistence is not bolted
onto the success path. Ordering on the *success* path is guaranteed textually (`:869-871` precedes
`:873`) but not separately asserted. Adequate as built.

**T2 — OBSERVATION: nothing pins that a live run must persist evidence.** No test fails if
`evidence_path` is omitted, because omission is legal (see B4). The B5 signature-pin test would be the
natural place to add the complementary constraint.

**T3 — OBSERVATION: 12 of the 27 pre-existing tests were replaced, not adapted.** The redesign
genuinely required it (different function name, different return shape, different provider method) and
the handoff documents the reason; 15 untouched scope-guard/fetch/backfill tests still pass. Net 37.
Worth recording plainly so "all 27 pre-existing tests pass" is not read as "the same 27 tests".

---

## 4. Domain Assessment

The gate is well built, and it is well built in the way that matters: `_compute_symbol_verdict`
(`:482-599`) is a **pure** function, which is what made genuine adversarial testing possible instead
of fixture-shaped happy paths. The ladder ordering is correct and load-bearing — the mismatch branch
sits *before* the `MIN_COMPARABLE_PAIRS` floor, so a genuine disagreement can never be downgraded to
"inconclusive" by a coverage gap, which is exactly what iter-7's audit finding B1 demanded, and
`test_symbol_verdict_mismatch_still_wins_over_a_coverage_gap` constructs precisely that input.

I probed the fail-open question directly against the code path rather than by population argument:
`agree` is unreachable below three genuinely comparable pairs (`<2` → early return; 2 → floor return),
a pair is comparable only when **both** sides are present and strictly positive (`:520-524`), so a
zero or negative price never becomes evidence and the carried `TypeError` finding B4 from iter-7 can
no longer be reached; an empty sample or window yields `verdicts=()` → `passing={}` → `stopped_reason`
with no write-capable call reachable (`:874-881`). Only `verdict == "agree"` symbols enter `passing`
(`:873`), `_BridgeApplyingProvider` refuses any symbol without a factor (`:792-797`), and the B6 date
assertion (`:802-806`) refuses any bar outside `[RECOVERY_START, RECOVERY_END]` before transforming
it. `validate_recovery_scope` receives hardcoded module constants for the dates and a symbol list
already intersected with `still_missing_symbols()`, so no caller input can widen the envelope. The
answer to every unhappy-path question the coordinator posed is: no.

The bridge direction is right — `bridge_factor = mean(stored/fallback)` applied as
`fallback × factor` lands the restored bar on the stored scale — and volume is genuinely untouched in
code and in the test that uses a non-unit factor. Idempotency holds two ways: `still_missing_symbols`
excludes any symbol already holding **both** dates (all 20 do), and `run_bounded_recovery_fetch`
re-intersects any caller list with live state (`:739-742`); the second-invocation test pins the exact
provider call count (3, never 4) so a redundant restore fetch would fail it.

Test quality is high: assertions are exact rather than permissive (`verdict == "agree"`, exact bridge
values, `requested_symbols == ["AAPL"]`, `sorted(closes) == [201.5, 202.5]`), the B2 test installs a
provider whose `get_adjusted_close` calls `pytest.fail` — a real crossover trap rather than an
assertion about intent — and the degenerate inputs the iter-7 lesson asked for are all genuinely
constructed. I re-ran both files myself: **37 passed** and **50 passed**.

Where the domain work falls short is epistemic, not mechanical. The gate was run against an input pair
that could not disagree (B1), so this iteration establishes that the mechanism is correct and
establishes nothing about its discriminating power on real cross-vendor data. The developer came
close to saying so — *"this precommitment was not tested against a close call on the real run"* — but
then attributed the clean result to genuine cross-vendor agreement rather than to same-vendor
identity, and that attribution has since propagated into `docs/goal.md`. The developer's refusal to
widen the sample mid-run was **correct** under the spec as written at the time; `docs/goal.md`'s
2026-08-21 amendment (step 2b) has since clarified that the anti-goodharting rule caps the
*methodology-validation sample*, not the *recovery population*, which resolves a real ambiguity going
forward rather than reversing a bad call.

---

## 5. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Critical | `reports/qa/goal-market-compass-iter-8-evidence/J-01-verify.png`, `J-04-verify.png` | Restored the quarantined bytes destroyed by the second forbidden replay lane, from commit `47d50d04`. Verified post-restore: md5 `bd13782d00c37abd0a0ee4a17eeb852d` / `9e9cc6fe68e08e08ab496d6be6c081bd`, both equal to the committed blobs; `git status` on the directory no longer reports them modified |
| 2 | Critical | `reports/qa/goal-market-compass-iter-8-evidence/INVALID-rerun-2026-08-21T1254-J-01-verify.png`, `…-J-04-verify.png` | Preserved the second lane's bytes under explicit quarantine names **before** restoring, so nothing was deleted and the recurrence remains evidenced (md5 `eaacb597…` / `190d16c0…`) |
| 3 | Critical | `reports/qa/goal-market-compass-iter-8-evidence/INVALID-forbidden-lane.md` | Appended a dated addendum recording the recurrence at `full` depth, the before/after hashes, the corroborating timestamp chain, the service starts, the correction to the "already remediated" reading, and what was restored/preserved. Original text left byte-unchanged |
| 4 | Important | `docs/handoffs/goal-market-compass-iter-8-dev.md` | Appended "AUDITOR CORRECTIONS" §C1 (Yahoo-vs-Yahoo, with all four evidence lines and the corrected CVX explanation), §C2 (2026-05-12 is drill damage, with dpr 538's cascade list), §C3 (full 14-table / ~4,602-row mutation reconciliation). Original developer prose left intact as the record of what was believed |

**Post-fix verification.** No source file was touched — `git status --short apps/ config.yaml
docs/goal.md` is empty, and my working-tree diff is exactly the four artifacts above. Both targeted
test files re-run after the fixes, one process at a time, detached and polled in-turn:
`pytest tests/test_j10_recovery.py -q` → **37 passed in 2.12s**;
`pytest tests/test_provider_clients.py -q` → **50 passed in 0.13s**. Every factual claim added to the
handoff was produced by a read-only query I ran myself (`file:…?mode=ro`); the database was never
opened for write, no service was started, no recovery or fetch was run, and `docs/goal.md` was not
edited. Host memory stayed ≥ 20 GiB available throughout.

---

## 6. Recommended Next Step

**Do not read this verdict as a reason to touch the 40 restored rows.** They are sound, and
`docs/goal.md` 2d is explicit that the 20 restored symbols stay restored. Equally, **do not read this
iteration as J-10 completion**: the correct state is `20 restored / 567 still pending` (3.4%), and
goal.md's Completion rule states recovery "cannot leave J-10 complete at `20/587`". The AG-9 exception
stays open, correctly.

Carry forward to the evaluator, explicitly:

1. **TC-19 was violated twice — the second time inside this full-depth re-run, which overwrote
   quarantined evidence.** The claim in the review report that it was "already remediated" is wrong
   (P3). The `PASS` rows for UT-J-01/UT-J-04 must not enter `journey-history.json` at either
   occurrence, and quarantine remains symmetric: a `FAIL` there would have been expected damage, not
   a regression.
2. **`Depth: full` was dispatched as `lean`** at `47d50d04` (third demotion this session). It reads
   `full` now, and this in-pipeline audit, reviewer and QA lanes did run — but P2 shows correcting the
   marker did **not** stop the forbidden lane, so the depth arbiter alone is not the fix.
3. **The gate's result is a same-vendor tautology (B1).** iter-8 proves the gate is correctly built;
   it proves nothing about cross-vendor discrimination. The dev handoff is corrected; **`docs/goal.md`
   still carries the wrong attribution** and only the owner can amend it.
4. **The iteration made out-of-scope writes** — ~4,602 rows across 14 tables, including a 2026-05-12
   `ScannerRun` with 3,355 child rows (unrepaired drill damage, not an unrelated gap) and four cache
   tables written by the forbidden lane. All benign, now reconciled; the iteration must not be
   described as having made none.

Priority work for iteration 9, in order:

- **Fix the lane gate before any further recovery batch.** Nothing in the pipeline consults TC-19 or
  `docs/goal.md`'s "no lane against the damaged database" rule at either depth. This is upstream
  framework work and it is what let a forbidden replay destroy quarantined evidence.
- **If a genuine cross-vendor convention proof is wanted, run the gate across the seed boundary**
  (stored bars ≤ 2026-07-01 versus a Yahoo fetch of the same dates). The mechanism is ready and would
  finally be exercised. This needs a fresh dated goal.md amendment — AG-9's exception authorizes the
  comparison fetch only over surviving days ≤ 2026-08-10.
- **Then** run further precommitted batches against the remaining 567 symbols, each sample fixed and
  documented before it runs, under goal.md's clarified 2b.
- Close **B4** (make evidence persistence non-optional on the production entry point) and **B5** (pin
  `fetch_provider` to the calibration provider) while the module is open — both are small, and both
  convert a discipline guarantee into a code guarantee, which is the whole point of B3/B5.
- Record **B7** (the 2026-07-01/02 vendor splice) as a known, pre-existing, unexamined data property
  so no future study mistakes post-seed history for Stooq-adjusted data.
