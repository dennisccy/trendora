# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 2. Shown in full: 2.

```diff
diff --git a/apps/backend/app/engine/data_manager.py b/apps/backend/app/engine/data_manager.py
index cd2fa001..6ddc9599 100644
--- a/apps/backend/app/engine/data_manager.py
+++ b/apps/backend/app/engine/data_manager.py
@@ -43,7 +43,7 @@ from contextlib import nullcontext
 from dataclasses import dataclass, field
 from datetime import date as date_cls, datetime, timedelta, timezone
 from pathlib import Path
-from typing import Callable, Optional
+from typing import Callable, Iterable, Optional
 
 from sqlalchemy import delete, func, insert
 from sqlalchemy.engine import Engine
@@ -2236,6 +2236,92 @@ def clear_snapshot_set(session: Session) -> dict:
     return {"runs_cleared": runs_cleared, "bars_before": bars_before, "bars_after": bars_after}
 
 
+# --------------------------------------------------------------------------------------------------
+# goal-market-compass iter-13 -- J-11 Stage C: the bounded, EXACT-DATE-FILTERED specialization of
+# `clear_snapshot_set` above (docs/goal.md J-11 step 11's OWNER AUTHORIZATION block, ruling C6: "Use
+# `clear_snapshot_dates(EXACT_INCIDENT_DATE_SET)` ... never `clear_snapshot_set()`"). SAME
+# child-before-parent deletion order, SAME whole-row-delete discipline, SAME `daily_prices`-untouched
+# assertion -- but scoped to only the `ScannerRun`s whose `asof_date` is IN `exact_date_set`, never the
+# entire snapshot history. This function NEVER calls `clear_snapshot_set` (which takes no date filter).
+# --------------------------------------------------------------------------------------------------
+def clear_snapshot_dates(session: Session, exact_date_set: Iterable[date_cls]) -> dict:
+    """DELETE only the Layer-2 derived-state rows owned (by `run_id`) by a `ScannerRun` whose
+    `asof_date` is one of `exact_date_set` (J-11 Stage C). For each date: freshly queries the CURRENT
+    `ScannerRun` for that `asof_date` (never a cached/prior inventory -- iter-9's "never inherit a prior
+    claim without re-checking it" lesson); no run -> a documented zero-row no-op for that date, never an
+    error; a run exists -> deletes every `ForwardReturn` / `ScannerResult` / `SectorScoreRow` /
+    `ThemeScoreRow` row whose `run_id` equals that run's id, then the `ScannerRun` row itself --
+    children before parents, mirroring `clear_snapshot_set`'s own order exactly. Never deletes a row
+    keyed only by `measured_date`/other-date membership outside this run-owned scope -- that population
+    is either already absent (the original incident's own defensive sweep already removed it) or Stage
+    E's repair target, never Stage C's (runs/goal-session-market-compass/state/assumptions.md, iter-13
+    entry #1).
+
+    Asserts the `daily_prices` row count is identical immediately before and after the WHOLE batch
+    (mirrors `clear_snapshot_set`'s `bars_before == bars_after` invariant; `daily_prices` is never even
+    referenced by a DELETE here). Never calls `compass.get_or_create_manifest`, `scanner.run_scan`,
+    `scanner.persist_run_payload`, or `_refresh_ingest_aggregates` -- issues DELETE statements only
+    (ruling C8: Stage C is deletion only).
+
+    Returns `{per_date: {date_iso: {run_id, deleted: {table: count}}}, totals: {table: count},
+    bars_before, bars_after}` -- the caller's own mutation-accounting evidence is built from this plus
+    the pre-declared intended-delete-set (`app.engine.j11_stage_c.capture_intended_delete_set`), never
+    from a second independent count."""
+    bars_before = int(session.scalar(select(func.count()).select_from(DailyPrice)) or 0)
+    per_date: dict[str, dict] = {}
+    totals: dict[str, int] = {
+        "scanner_runs": 0,
+        "forward_returns": 0,
+        "scanner_results": 0,
+        "sector_scores": 0,
+        "theme_scores": 0,
+    }
+    for one_date in exact_date_set:
+        key = one_date.isoformat()
+        run = session.exec(select(ScannerRun).where(ScannerRun.asof_date == one_date)).first()
+        if run is None:
+            per_date[key] = {
+                "run_id": None,
+                "deleted": {
+                    "scanner_runs": 0, "forward_returns": 0, "scanner_results": 0,
+                    "sector_scores": 0, "theme_scores": 0,
+                },
+            }
+            continue
+        run_id = run.id
+        deleted = {
+            "forward_returns": int(
+                session.scalar(select(func.count()).select_from(ForwardReturn).where(ForwardReturn.run_id == run_id)) or 0
+            ),
+            "scanner_results": int(
+                session.scalar(select(func.count()).select_from(ScannerResult).where(ScannerResult.run_id == run_id)) or 0
+            ),
+            "sector_scores": int(
+                session.scalar(select(func.count()).select_from(SectorScoreRow).where(SectorScoreRow.run_id == run_id)) or 0
+            ),
+            "theme_scores": int(
+                session.scalar(select(func.count()).select_from(ThemeScoreRow).where(ThemeScoreRow.run_id == run_id)) or 0
+            ),
+        }
+        # children first (FK order), then the parent run. Whole-row deletes; daily_prices never referenced.
+        session.execute(delete(ForwardReturn).where(ForwardReturn.run_id == run_id))
+        session.execute(delete(ScannerResult).where(ScannerResult.run_id == run_id))
+        session.execute(delete(SectorScoreRow).where(SectorScoreRow.run_id == run_id))
+        session.execute(delete(ThemeScoreRow).where(ThemeScoreRow.run_id == run_id))
+        session.execute(delete(ScannerRun).where(ScannerRun.id == run_id))
+        deleted["scanner_runs"] = 1
+        per_date[key] = {"run_id": run_id, "deleted": deleted}
+        for table_name, count_value in deleted.items():
+            totals[table_name] += count_value
+    session.commit()
+    bars_after = int(session.scalar(select(func.count()).select_from(DailyPrice)) or 0)
+    if bars_after != bars_before:
+        raise RuntimeError(
+            f"Stage C bounded clear corrupted the price seed: {bars_before} bars before, {bars_after} after"
+        )
+    return {"per_date": per_date, "totals": totals, "bars_before": bars_before, "bars_after": bars_after}
+
+
 # --------------------------------------------------------------------------------------------------
 # Import provider catalog + env-detected availability (J-33) — descriptive metadata, NO key value
 # --------------------------------------------------------------------------------------------------
diff --git a/docs/goal.md b/docs/goal.md
index dfe2b99d..2a4f56ce 100644
--- a/docs/goal.md
+++ b/docs/goal.md
@@ -1344,6 +1344,101 @@ manifest artifact (it must be self-describing and self-caveating).
          retroactively turn iter-11 into a clean PASS. The honest lineage to preserve is: *iter-11
          migration — primary goal succeeded, stored state preserved, unauthorized DDL residual detected,
          REGRESSION recorded, owner later accepted the exact residual instead of ordering a second rewrite.*
+
+       ## OWNER AUTHORIZATION — J-11 Stage C (owner, 2026-08-24)
+
+       **Stage C is AUTHORIZED.** Iteration 12's evaluator independently re-derived all thirteen of
+       ruling A12's readiness conditions, found no unresolved technical blocker, and halted STALLED
+       solely because A12 reserves the destructive step for an explicit owner instruction. This is that
+       instruction. **The authorization is narrow.** It authorizes ONLY the incident-bounded destructive
+       clear already defined by this J-11 contract, for the exact 11 incident dates. It does **NOT**
+       authorize Stage D or any later stage, automatically or by implication.
+       - **C1 — Date-set boundary.** The authorized set is EXACTLY the 11 dates enumerated in the
+         "**The incident date set — all 11, not the 8 currently absent**" bullet above. For the avoidance
+         of doubt they are `2026-05-12, 2026-05-13, 2026-07-10, 2026-07-13, 2026-07-24, 2026-07-27,
+         2026-08-03, 2026-08-05, 2026-08-10, 2026-08-11, 2026-08-12`. **If this restatement and that
+         authoritative bullet ever disagree, STOP** — do not reconcile them by choosing one. No date may
+         be added, inferred from current cadence, selected from a range, or reached by historical-density
+         backfill. No "all affected-looking dates". No full-history clear. **The exact 11-date set is the
+         sole authorization boundary.**
+       - **C2 — Fresh preflight is mandatory, before the first destructive statement.** Re-run the Stage C
+         preflight required by step 13 and re-derive live state; do NOT trust iteration-10/11/12 counts
+         merely because they were certified. Freeze a NEW Stage C attempt identity. Capture at minimum:
+         current git HEAD; the goal.md / J-11 contract identity hash; engine identity; config identity;
+         the exact 11-date set; `daily_prices` fingerprint; `scanner_runs` inventory by exact incident
+         date; `scanner_results`, `sector_scores`, `theme_scores` inventories; the `forward_returns`
+         inventory relevant to affected runs/dates; manifest row count, full-row fingerprint, DDL
+         fingerprint and index set; provider-run state; watchlist/user-state counts and fingerprints
+         already protected by J-11; and the ledger/prereg/evidence fingerprints already defined. Persist
+         it as Stage C pre-delete evidence. **If the fresh preflight materially differs from the certified
+         iteration-12 state, or any B/B1/B2 invariant no longer holds, STOP before deletion.**
+       - **C3 — Manifest preconditions re-proven before deletion.** 24 rows; no live FK on
+         `source_run_id`; values unchanged from the certified state; the four owner-accepted DDL residuals
+         unchanged; the three original indexes unchanged; `source_run_id` provenance values unchanged; no
+         manifest regenerated, rebound or upgraded since certification. Do **not** treat `source_run_id`
+         as a live relational identity and do **not** "repair" orphan values.
+       - **C4 — Layer boundary. Stage C clears Layer 2 ONLY.** Layer 1 (canonical inputs — `daily_prices`
+         and provider provenance) is **preserved**; Layer 2 (`scanner_runs`, `scanner_results`,
+         `sector_scores`, `theme_scores`, and the associated forward-return derived state) is the
+         **authorized incident-bounded clear**; Layer 3 (manifests, audits, recovery provenance, ledgers,
+         preregistrations, incident evidence) is **preserved**. Expected new canonical-input writes:
+         **ZERO**. Do not modify stock/universe reference data, ETFs, sectors, industries, themes, theme
+         membership, macro series, provider source rows, or J-10 recovery evidence. **No Yahoo/Stooq or
+         any network work belongs in Stage C. J-10 is CLOSED and MUST NOT reopen.**
+       - **C5 — Immutable evidence and user state.** Do not delete, mint, regenerate, version-increment,
+         rehash or re-export manifests; do not modify `source_run_id`, `source_run_created_at` or
+         `prospective_eligible`; do not rewrite evidence ledgers, referee history, preregistration state,
+         incident evidence, J-10 provenance, or historical evaluator verdicts. **Iteration 11's REGRESSION
+         remains historical truth.** Do not touch the watchlist, user configuration/state, saved
+         selections, or unrelated caches with no dependency on cleared derived state — classify before
+         touching if a dependency is uncertain. "Cleanup" is never permission for a broad reset.
+       - **C6 — Bounded mechanism only.** Use `clear_snapshot_dates(EXACT_INCIDENT_DATE_SET)` or the
+         narrowest canonical equivalent already prescribed above — **never** `clear_snapshot_set()` or any
+         path semantically equivalent to clearing the whole snapshot/forward-return history. The clear must
+         be **mechanically constrained** to the 11 dates. Re-derive actual FK/dependency ordering from the
+         current code and schema and use the safest bounded child-before-parent order; do not guess
+         ownership from table names. Invariant: after Stage C **no surviving derived object may falsely
+         claim to be authoritative for one of the 11 incident dates on the strength of pre-repair run
+         state** — but do not delete unrelated derived history merely because it references an affected
+         measured date unless this contract explicitly classifies it as part of the incident repair.
+       - **C7 — Forward returns.** Clear only what must be removed before canonical Stage D/E
+         reconstruction, following this contract exactly. **Do not perform the final global/create-once
+         forward-return repair in Stage C** unless this contract explicitly assigns that action to Stage C.
+         The sequence stays C (bounded clear) → D (exact 11-date canonical regeneration) → E (canonical
+         forward-return hole repair) → F (dependency-aware cache handling) → G (final serving/replay
+         verification). **Do not collapse C→G into one developer action.**
+       - **C8 — No manifest creation during Stage C. Stage C is deletion only.** Any regeneration path
+         capable of calling `get_or_create_manifest(...)` must NOT run. No historical manifest may be
+         created for the seven incident dates that currently have none, and no new version minted for the
+         four dates that already carry manifests. Existing manifests stay byte/value invariant.
+       - **C9 — Restart safety.** Freeze the attempt identity, record pre-state, record the exact intended
+         delete set, record actual delete counts, and persist a completion marker **only after
+         verification**. Never infer "resume from halfway" from partial table counts. If Stage C fails
+         mid-flight: STOP, inventory actual live state, do not continue to Stage D, and do not pretend
+         Stage C completed — then follow the restart/retry contract in step 13.
+       - **C10 — Stage C stands alone, and STOPS.** The Stage C iteration must be scoped to Stage C only;
+         **if the decomposer combines C with D or broader J-11 work, the decomposition must be corrected
+         before developer execution.** Maintenance isolation, `Depth: full` and depth enforcement remain
+         in force throughout — full depth means developer, reviewer, static/file-scoped QA, auditor,
+         coherence and evaluator, **not** application-service execution. After the bounded clear completes
+         and is independently verified, **STOP THE ENGINE** and return exactly
+         `J-11 STAGE C COMPLETE: YES/NO` and `J-11 STAGE D AUTHORIZED: NO`. Successful Stage C is **not**
+         implicit authorization for Stage D: no ScannerRun regeneration, no sector/theme rebuild, no
+         forward-return backfill, no cache invalidation or re-warm, no service start, no `GET /api/compass`,
+         no J-01/J-02/J-03, no Stage G. The owner inspects Stage C mutation accounting first.
+       - **C11 — Two recorded framework findings stay out of Stage C.** (a) The `goal_gate.py` duplicate
+         J-ID journey-hashing defect (a nested `- **J-NN ...` bullet is read as a journey heading, letting a
+         later duplicate block overwrite the earlier one) is REAL: it does not block this already-ratified
+         Stage C, but it **must be fixed before any future reliance on journey-hash drift for edited
+         J-10/J-11 text, and before GOAL_ACHIEVED certification**. Do not pull that fix into the Stage C
+         destructive iteration unless the Stage C decomposer itself must edit J-10/J-11 contract text in a
+         way whose safety depends on that gate. (b) The manifest-migration live-vs-model column-list defect
+         is REAL but **not a Stage C blocker** — the migration does not run in Stage C and the live/model
+         column sets are known equal; it is a **mandatory precondition/fix before any future live
+         manifest-table migration**. **Do not touch the manifest migration in Stage C.**
+       - **C12 — No redesign.** This run executes the already-ratified contract. Do not redesign J-10,
+         J-11, candidate thresholds, manifest semantics, research architecture, Tapeology integration, or
+         the prospective/OOS rules. No speculative goal hardening.
     12. **Stage B2 — freeze ONE engine identity for the whole attempt (owner, 2026-08-21).** J-11's
        claim is that the incident set ends up as one internally consistent current-engine derivation;
        that claim must be testable. Before Stage C, freeze the intended current engine identity and
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-market-compass/session.json        |  2 +-
 .../goal-session-market-compass/state/assumptions.md | 16 ++++++++++++++++
 runs/goal-session-market-compass/state/lessons.md    | 14 +-------------
 .../state/lessons.md.archive.md                      | 20 ++++++++++++++++++++
 runs/goal-session-market-compass/telemetry.jsonl     | 15 +++++++++++++++
 runs/goal-session-market-compass/trace/.next-step    |  2 +-
 runs/goal-session-market-compass/trace/trace.jsonl   |  3 +++
 7 files changed, 57 insertions(+), 15 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
