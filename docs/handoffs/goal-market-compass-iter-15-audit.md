# goal-market-compass-iter-15 Audit Report

**Date:** 2026-08-25
**Auditor:** Hard audit pass — skeptical, evidence-based, re-derived rather than adjudicated

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The phase goal was achieved. I re-derived the headline finding from primary evidence — the live
database (read-only) plus this iteration's fetch artifact — and reached `AVB-C` independently: the
calibration window and the two J-10-recovered bars genuinely disagree on AVB's volume convention, so
`J-11 STAGE D READY: NO` is correct and mechanically derived, not label-patched. Iteration 14's
price-only tautology is genuinely closed, the readiness artifact is produced by committed code, and
the whole-iteration zero-write proof holds — I re-verified every figure of the safety envelope myself
and my own work added zero writes.

The verdict is PASS_WITH_GAPS rather than PASS because of **B1**: booting the backend at all — or a
single `GET /api/compass?as_of=<incident date>` — silently performs the exact Stage D-class write
this whole contract is withholding authorization for, and irreversibly destroys the readiness gate's
own central precondition. That hazard is pre-existing and outside this iteration's scope, but the
readiness contract it produced is silent about it, and it is the single most consequential thing an
owner reading `READY: NO` needs to know before the browser/replay lanes reopen.

**`J-11 STAGE D READY: NO`** — quoted verbatim from
`runs/goal-market-compass-iter-15/j11-stage-d-readiness.json` (`"ready": false`,
`"blocking_reasons": ["avb_classification_blocks:AVB-C"]`), the same artifact and the same value the
dev handoff, review, and QA quote.

**`J-11 STAGE D AUTHORIZED: NO`** — confirmed unconditional in code, not prose:
`app/engine/j11_stage_d.py:485` sets `"authorized": False` inside `stage_d_readiness_verdict`, and
`:900` re-sets it unconditionally after the verdict is built, with the comment "unconditional,
regardless of what the inputs say". The artifact carries `"authorized": false`. Stage D was not
executed, started, or approached under any code path.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (gap — not fixable within this audit's boundaries): booting the backend, or one
`GET /api/compass?as_of=<incident date>`, performs the unauthorized Stage D-class write and
irreversibly breaks this iteration's own readiness gate. The readiness contract does not say so.**

This is the ui-test-designer's trap, re-derived from the call sites — and it is materially broader
than "mints a manifest".

The write path, traced end to end:

- `apps/backend/main.py:100` — the FastAPI lifespan calls `ensure_latest_snapshot(engine, config)`
  **synchronously on every boot**, with no maintenance/read-only guard of any kind anywhere around
  it (`main.py:85-113`).
- `apps/backend/app/engine/warmup.py:89-92` — that resolves `latest = latest_data_date(session)` and
  calls `run_scan(session, latest, cfg)`.
- Live, read-only: `SELECT MAX(date) FROM daily_prices` = **`2026-08-12`** — one of the 11 incident
  dates, currently holding **zero** `ScannerRun` rows because Stage C cleared it.
- `apps/backend/app/engine/scanner.py:235-239` — `run_scan` finds no existing run for that date and
  falls through to `compute_run_payload` + **`persist_run_payload`**, i.e. a `ScannerRun` INSERT,
  stamped with the *current* engine identity, outside every identity-freeze/compare call site this
  module family exists to enforce.
- `main.py:113` then launches `start_warmup`, whose cadence loop plus `backfill_forward_returns`
  writes further rows.

The request path is the same wire: `apps/backend/app/api/compass.py:60-61` → `resolved_run` →
`scanner.py:338-348` `resolve_run` → `run_scan` (same INSERT), then
`app/engine/compass.py:1042-1066` `get_or_create_manifest(..., producer="on_demand_get")`, which
create-once-mints a version-1 manifest for any **historical** as-of that lacks one.

Consequences, both irreversible:

1. `checks["all_incident_dates_zero_scanner_runs"]` (`app/engine/j11_stage_d.py:424-429`) — the
   genuinely Stage-D-specific precondition of the gate this iteration just certified — flips to
   `False` permanently. Stage C's bounded clear is on the binding "do not redo" list, so it cannot be
   undone.
2. `checks["manifest_row_count_unchanged"]` (`j11_stage_d.py:399`) breaks forever for the incident
   dates that have no manifest yet, because AG-12 forbids deleting or mutating a stored manifest row.
   I enumerated them read-only: exactly **7** of the 11 have none — `2026-05-12, 2026-05-13,
   2026-07-10, 2026-07-13, 2026-07-24, 2026-07-27, 2026-08-03` (the other four, `08-05/10/11/12`,
   already carry manifests, 24 rows in total). That matches the ui-test-designer's count exactly.

Mitigating facts, verified rather than assumed: the minted manifest would carry
`prospective_eligible: 0` (the `producer == "ingest_finalize"` / `version == 1` derivation excludes
an `on_demand_get` mint), so it would not fabricate *prospective* evidence — but it would still be an
AG-12-immutable Layer-3 row pinned to a knowingly-pending pre-Stage-G state, which is exactly what
AG-17 protects against. And the current state is clean: no backend or frontend port is listening, no
uvicorn process exists, and the database is byte-identical to the coordinator's capture — so the
isolation has genuinely held and this has not fired.

**Answer to the coordinator's question: yes, this deserves an explicit guard in the Stage D/G
contract — and the guard cannot be `/api/compass`-scoped.** A request-level guard is too late: `main.py:100`
trips the wire before any request arrives. The guard has to be pre-boot (a maintenance/read-only mode
that makes `ensure_latest_snapshot`, `start_warmup`, and `run_scan`-on-resolve refuse while any
incident date sits at zero `ScannerRun`s), and it must be in place *before* Stage G reopens the
browser and deterministic-replay lanes.

**Not fixed, deliberately.** Changing application boot behaviour is a design decision for the owner,
sits outside this audit's read-only / no-regeneration / no-service-boot boundary, and is explicitly
out of scope for iteration 15 ("Any application-service boot, browser-QA run, or deterministic-replay
run"). This is escalation, not a regression introduced here.

**B2 — GAP: the readiness producer's staleness check is timestamp-only, so it cannot detect two
inputs captured against different database states.**
`app/engine/j11_stage_d.py:792` (`_MAX_ARTIFACT_GENERATION_SKEW_SECONDS = 6h`), `:809-841`, `:892-897`.
Spec Goal 7 asked it to fail closed when "the two artifacts' own db-file fingerprints/generation
timestamps disagree"; only the timestamp half exists. The docstring's justification is accurate as
far as the preflight gate goes — I read `j11-stage-d-preflight-gate.json` and it carries only
`comparison` and `verdict`, no db fingerprint — but the AVB diagnostic *does* carry one
(`zero_write_proof.db_file_true_start/end`), so the stronger check is one emitted field away. Any
DB mutation between the two captures inside a 6-hour window passes as "consistent". Immaterial for
this run: actual skew 81.9s, and the whole-iteration TRUE-start/TRUE-end bracket independently proves
the DB never changed across both captures. Not fixed — closing it means changing the preflight
script's output shape and re-running it against the live DB, which this audit is forbidden to do.

**B3 — GAP: the AVB-D fail-closed override reports the wrong "underlying" label.**
`apps/backend/scripts/run_j11_avb_bridge_diagnostic.py:222-232`. The block sets
`classification["classification"] = "AVB-D"` at line 224, then at line 231 interpolates
`{classification['classification']}` into the sentence "Underlying convention/impact classification
(informational only, NOT trusted as the basis for readiness): …" — which therefore always prints
`AVB-D`, discarding the real underlying label. The label, `stage_d_ready_per_avb`, and the named
`missing_dates` are all correct, and `classification['reasoning']` still carries the original text
(the RHS is evaluated before assignment), so only the explanatory prose loses information. The branch
was not taken this run (`sufficient_evidence: true`). Documented, not fixed — fixing it without
re-running the producer would put committed code out of step with the committed evidence it produced,
and re-running is outside this audit's boundaries.

**B4 — OBSERVATION: the `avb_daily_prices_sha256` mismatch is genuinely unresolvable, and the target
figure is not reproducible from anything on disk.**
I did not accept the developer's "hash-recipe difference" claim on its word. I computed nine
candidate recipes against the live AVB rows, read-only: the module recipe sorted
(`d572f838…`, matching `app/engine/j11_stage_d.py:553-576`), the same unsorted, full-row JSON,
full-row `repr`, date/close/volume JSON, date/close/volume `repr`, the whole-table variant
(`572691…3451a`), and six-date-only JSON and `repr`. **None** produces `0257c56d…0b11cd`. A repo-wide
grep shows the excerpt exists only in the iteration-15 spec, this iteration's own artifacts, and the
QA report — it appears in **no prior committed artifact**, and no AVB-scoped fingerprint existed
before this iteration, so the spec set up a comparison that could not succeed by construction.
Corroborated benign two independent ways: the DB file is byte-identical to the coordinator's capture
(mtime `1787591622`, size `8,365,871,104`, `-wal` 0), and I read AVB's six stored bars live and they
match the quoted values exactly. Recording it as an unresolved mismatch rather than forcing a match
is the correct handling — the honest answer here is "unknown", and the developer gave it.

**B5 — OBSERVATION: `maintenance_isolation_env` is not a usable isolation instrument, and nobody
reconciled what it recorded.**
`runs/goal-market-compass-iter-15/j11-stage-d-preflight.json` records
`maintenance_isolation_env: {present: false, value: null}` — as does iteration 14's. Meanwhile the
engine process genuinely carries `CHAIN_MAINTENANCE_ISOLATION=true` (read from
`/proc/<engine.pid>/environ`). The field can only ever observe the invoking subprocess's environment,
which is not where the operator sets it, so `present: false` is an artifact of how the script is
launched, not evidence isolation was off. Worth naming because both the handoff and the QA report
assert "Maintenance Isolation: ACTIVE" without reconciling against the one machine-readable signal
this iteration captured, which says `false` — the same "captured but never compared" shape iteration
13 was caught on.

**B6 — OBSERVATION (checked, immaterial): representation B mixes bases across the ADV window.**
`j11_avb_diagnostic.py:629-654` substitutes provider close *and* provider volume for the two
recovered dates while every other bar keeps the stored basis. I checked whether that biases the
trace: every consumer downstream (`ur._adv_dollar`, `scoring._avg_dollar_volume`) reads
`close × volume`, and `(provider_close × provider_volume)` is arithmetically identical to
`(provider_close · bridge) × (provider_volume / bridge)` — the stored-basis correction. So the two
formulations give the same number and the trace is unbiased. `admission_changed` is `False` on both
dates independently. No impact.

### Test Findings

**T1 — GAP: QA's zero-write table prints a fingerprint that is not the value it labels.**
`reports/qa/goal-market-compass-iter-15-qa.md:121-122` shows `0257c56d…0b11cd` as the whole-table
`daily_prices` fingerprint (the real derived value is `572691772b…9223451a`), and marks the AVB row
"(match) ✅ Unchanged", conflating "unchanged start→end" (true) with "matches the owner capture"
(false — the reconciliation artifact records `matches_owner_capture: false`). QA discloses the
mismatch honestly in its own Known Issues #1, so this is inaccuracy in the headline table, not
concealment.

**T2 — OBSERVATION: per-file test counts are wrong in the handoff and were copied into QA.**
I reran the exact targeted command myself: **157 passed, 0 failed in 6.07s** — the aggregate is
correct and reproducible. The breakdown is not: measured `test_j11_avb_diagnostic.py` = 36 (handoff
and QA claim 45), pre-existing files = 51 (handoff claims 42), `test_j11_stage_c_preflight.py` = 21
(QA table says 19). This confirms and extends the reviewer's MINOR finding. Separately, the handoff
says the zero-write proof carries "24 checks"; the artifact carries 25, all passing.

**T3 — positive finding: the deleted tautology test was genuinely broadened, not narrowed.**
I checked this structurally rather than by reading the claim. Across the entire commit, exactly one
function disappeared from any file: `test_tc22_representations_a_b_c_formulas_and_volume_equality` —
the test that asserted `rep["volume_a_equals_b"] is True` and `rep["B"]["volume"] == stored_volume`,
i.e. the literal bug. It is replaced by three tests covering `volume_a_equals_b` as `False`
(`test_tc12_…`, provider volume 350k vs stored 500k), `True` (`test_representation_b_can_also_prove_…`,
where the two independently-sourced values happen to agree), and `None`
(`test_tc13_…_fails_closed_…`). Every other pre-existing `def` in all six modified files is still
present. Assertions throughout are tight (`is True` / `is False` / `is None`, exact values,
`pytest.approx` on ratios), not loose.

**T4 — positive finding: label reachability is not reverse-engineered to AVB's answer.**
All four per-date labels (`raw+raw`, `bridged+compensating`, `bridged+raw`, `mixed/indeterminate`)
and all four `classify_avb` labels have their own dedicated fixture. Critically, the
`bridged+compensating` and `bridged+raw` fixtures are built from hypothesis arithmetic on synthetic
values (`provider_close = 100.0`, `provider_volume = 1_000_000.0`, `bridge_factor = 2.793`), **not**
from AVB's real numbers — so the branch that iteration 14 could never reach is proven reachable
independently of the data that happens to reach it. `test_mixed_indeterminate_when_evidence_matches_no_hypothesis`
proves the classifier does not force a shape into the nearest label.

---

## 3. Domain Assessment

**I re-derived the headline finding independently, from the live database and the fetch artifact, not
from the diagnostic's output.** Read-only query against `daily_prices` for AVB's six permitted dates,
combined with `j11-avb-provider-fetch-evidence.json`, applying the ratio tests myself:

| date | stored_close | provider_close | close_ratio | stored_volume | provider_volume | volume_ratio | dollar_volume_ratio | label |
|---|---|---|---|---|---|---|---|---|
| 2026-08-05 | 189.6100 | 67.8876 | 2.7930 | 591,600 | 1,652,268 | 0.3581 | 1.0000 | bridged+compensating |
| 2026-08-06 | 186.5500 | 66.7920 | 2.7930 | 642,300 | 1,794,050 | 0.3580 | 0.9999 | bridged+compensating |
| 2026-08-07 | 187.5500 | 67.1500 | 2.7930 | 666,100 | 1,860,448 | 0.3580 | 1.0000 | bridged+compensating |
| 2026-08-10 | 183.8400 | 65.8217 | 2.7930 | 451,300 | 1,260,545 | 0.3580 | 0.9999 | bridged+compensating |
| 2026-08-11 | 181.7600 | 65.0770 | 2.7930 | 1,549,436 | 1,549,436 | **1.0000** | **2.7930** | bridged+raw |
| 2026-08-12 | 179.7900 | 64.3716 | 2.7930 | 10,350,885 | 10,350,885 | **1.0000** | **2.7930** | bridged+raw |

`bridge_factor = 2.7930001225759193`, `1/bridge_factor = 0.358037936…`. **My derivation matches the
coordinator's stated figures and the artifact exactly.** The 2026-08-12 dollar volume is
`$1,860,985,686` stored against the provider's `$666,303,475` — a 2.793× overstatement, reproduced in
the artifact's own `counterfactual_representations_by_date`.

Two independent corroborations I found that no lane cited: the stored closes for 08-11/12 carry long
float tails (`183.22001534990548`, `181.08999902870366`) while the calibration-window closes are
clean seed values — the signature of a value *computed* as `fallback_close × bridge_factor`; and the
stored volumes for those two dates are **bit-exactly** the provider's, which is only possible if J-10
wrote the provider's volume through untouched. Both confirm the mechanism the classifier infers.

**The classifier reaches AVB-C mechanically.** I traced the path rather than trusting the label:
`compute_provider_comparison` (`j11_avb_diagnostic.py:316-381`) only *measures*;
`classify_date_from_provider_comparison` (`:384-415`) decides from four symmetric
`_within_relative_tolerance` comparisons against `1.0`, `bridge_factor`, and `1/bridge_factor`, with
a single shared tolerance constant (`_RATIO_RELATIVE_TOLERANCE = 0.01`, `:101`) that reuses the same
1% band the original calibration check already applied inline;
`classify_local_convention_with_volume_evidence` (`:418-542`) requires every date in a window to
agree or the window is `mixed/indeterminate`; the calibration window resolves `bridged+compensating`
and the recovered window `bridged+raw`, so `evidence_backed_classes` has length 2 →
`internally_consistent: False` → `classify_avb` (`:910-914`) → **AVB-C**. There is no AVB-specific
constant, no hardcoded label, and no prior-iteration answer encoded anywhere in the module; the
bridge factor is read verbatim from the persisted J-10 evidence and never re-derived.

**It genuinely fails closed.** `_within_relative_tolerance` (`:104-112`) returns `False` — never
`True` — for a `None` value, a `None` target, or a zero target. A missing/partial provider record
makes `compute_counterfactual_representations` set `evidence_available: False`, `B.close`/`B.volume`
to `None`, and `volume_a_equals_b` to `None` (`:577-621`), never a stored-volume copy and never the
arithmetic fallback. A date without fetched evidence classifies `mixed/indeterminate` and never falls
back to the price-only method. And the diagnostic script applies a second, independent AVB-D override
when the fetch artifact itself reports `sufficient_evidence: false`. Two independent fail-closed
layers, both verified in source.

**Could the label have been anything else?** No. AVB-D is excluded — the fetch returned all six dates
with non-null close and volume (`missing_dates: []`, `fetch_error: null`). AVB-A and AVB-B both
require internal consistency, which is contradicted by direct measurement on both windows. The
implementation reaches AVB-C on internal inconsistency *before* consulting material impact, which is
slightly stricter than the spec's literal wording ("…for a window that materially affects Stage D
output"); that is a fail-closed deviation, and it is moot here because material impact was found
anyway (4 other pool tickers' liquidity percentile shifted on 08-11, 35 on 08-12, recorded in
`classification.material_signals`). **AVB-C is the only defensible label.**

**Safety envelope — re-derived, not inherited.** Live read-only queries at audit time:
`daily_prices` 3,310,374 · `scanner_runs` 3,117 (34 stamped `6261ca17…`, ids 3113 and 3115-3147;
3,083 NULL; 0 other) · `forward_returns` 6,797,728 · `data_provider_runs` 549 ·
`next_session_manifests` 24 · `watchlist` 6 · **zero** `ScannerRun` rows on all 11 incident dates ·
DB mtime `1787591622`, size `8,365,871,104`, `-wal` 0 bytes. Every figure matches the coordinator's
capture and the iteration's own TRUE-start/TRUE-end snapshots. The zero-write proof's 25 checks all
pass, including the exact 34-row legacy id set. `manifest_ddl_sha256` re-derives to
`9f653c8147…7fc501ee` (matches the owner excerpt). `forward_returns_measured_into_incident_total` =
16,614 (TC-2). Grep across every new and changed engine module and script finds **zero**
`session.add` / `session.commit` / `session.delete` / `flush` / `persist_run_payload` / `run_scan`
call sites — only docstring mentions (TC-23). All three DB-touching scripts open
`sqlite:///file:…?mode=ro&uri=true` with `PRAGMA query_only=ON`.

**The fetch stayed inside AG-9 dated exception #2.** `docs/goal.md`'s amendment was written at 09:17
local, *before* the phase spec (09:40), the plan (09:51), and the fetch (10:26 local / 09:26 UTC) —
so the authorization genuinely preceded the act, and the amendment is the owner's uncommitted edit,
correctly absent from the developer's commit. Grep confirms exactly one `.get_daily` call site in the
entire diff (`j11_avb_provider_fetch.py:98`) and exactly one place constructing a live provider
(`run_j11_avb_provider_fetch.py:78`); the module calls `get_daily` once, with no retry loop and no
per-date fetch, filters strictly to the six permitted dates, and discards anything else. Fields
recorded are `date`/`close`/`volume` only. `get_daily` is the canonical raw-close path (Yahoo's
`quote.close`), not `get_adjusted_close` — like-for-like as the amendment required. Nothing was
written to any table (`data_provider_runs` still 549 — the fetch left no DB trace at all), J-10 was
not reopened, and the bridge diagnostic requires `--provider-fetch-evidence-path` with no fallback
default, so no later step can re-fetch. **I performed no network fetch of my own.**

**Process deviations — investigated independently, both clean.** Commit `17eb97ce`: 30 files, all
added or modified, none deleted or renamed; it touches no `iter-13`/`iter-14` path and does not touch
`docs/goal.md`; 8,007 insertions against 71 deletions. On the `git stash`/`pop` cycle, I did not
accept "nothing was lost" as a claim — I diffed the symbol table of every modified file against its
pre-iteration version at `14383d8f` and found exactly one function missing anywhere: the disclosed
tautology test (T3). The only other deleted line in the test files was a duplicate
`from app.models import ScannerRun` import, consolidated into the surviving
`from app.models import NextSessionManifest, ScannerRun`. `git stash list` is empty. Iteration 14's
`j11-stage-d-readiness.json` has been touched by exactly one commit in its entire history (`b2c49192`,
iteration 14's own) — byte-preserved, and correctly quoted verbatim with
`stale_artifact_superseded: true` and a `superseded_by` pointer. Evidence directories for iterations
9, 11, 12, 13 and 14 are all `git status --porcelain` clean, before and after my own test run.

**Identity honesty (Goal 9).** The artifact carries `readiness_time_only: true`, `authorizing: false`,
`reusable_for_stage_d_execution: false`, and an honest comparison recording `matches: true` against
iteration 14's `53d2ffd1…`. I checked whether "no drift" is credible given that this iteration changed
two engine files: `provenance.engine_files` covers `compass.py`, `session_delta.py`, and
`engine_identity.py` — none of which this iteration touched — so an unchanged identity is the correct
result, not a stale read. `freeze_stage_d_attempt_identity` is unchanged and still takes no path
parameter; the prior value is injected purely for comparison and never substitutes for the fresh
computation.

---

## 4. Fixes Applied During This Audit

None. No CRITICAL or IMPORTANT defect was found *in what this iteration built*.

The one IMPORTANT-severity item (B1) is a pre-existing application-boot hazard whose remedy is a
design decision for the owner and whose fix would require changing service boot behaviour — outside
this audit's read-only, no-service-boot, no-regeneration boundary. B2 and B3 are GAP-level and their
fixes would require re-running the evidence-producing scripts against the live database, which this
audit is forbidden to do; fixing the code without re-running would leave committed code out of step
with the committed evidence it produced.

My own work performed zero writes: DB mtime `1787591622`, size `8,365,871,104`, `-wal` 0 bytes at the
end of this audit, identical to the start; all historical evidence directories still report zero
`git status --porcelain` lines after my test run; no `git checkout` restore was needed. I ran the
targeted suite exactly once, as a single pytest process (157 passed in 6.07s), never the full backend
suite, and triggered `/api/compass` for no date.

---

## 5. Recommended Next Step

**Stop here and return to the owner. Do not run Stage D.** `J-11 STAGE D READY: NO` is correct and
evidence-grounded; `J-11 STAGE D AUTHORIZED: NO` stands unconditionally. The AVB question is now
settled as a *measurement* — the two recovered bars carry provider-raw volume against a bridged
close, inflating their dollar volume by exactly 2.7930× — but the *decision* it forces is the owner's:
whether Stage D regenerates against today's stored representation, against a corrected one, or not at
all. This iteration correctly refused to make that call, and no lane should make it for them.

Before any next iteration touches Stage D, three things need owner input, in priority order:

1. **B1 first, and before anything reopens the browser or deterministic-replay lanes.** The Stage D/G
   contract needs an explicit pre-boot guard, not a `/api/compass`-level one. As things stand, the
   first person to start the backend for any reason writes a `ScannerRun` for 2026-08-12 and
   permanently fails the readiness gate that iteration 15 just certified. Maintenance isolation is
   currently the *only* thing preventing this, and it is an operator convention rather than a code
   guard.
2. **The AVB convention decision itself** — the substantive blocker that AVB-C names.
3. **B2 and B3** — small, surgical, and best folded into whichever iteration next re-runs these
   scripts, so code and evidence are regenerated together rather than drifting apart.

Two figures the owner may want to re-issue: the `avb_daily_prices_sha256` excerpt `0257c56d…0b11cd`
(B4) cannot be reproduced by the recipe the spec mandated and matches nothing on disk, so it cannot
serve as a verification target in a future spec; and `maintenance_isolation_env` (B5) reports on the
wrong process and should not be read as an isolation instrument.
