# Iteration diff (bounded)

Files changed: 8. Shown in full: 8.

```diff
diff --git a/apps/backend/app/engine/session_delta.py b/apps/backend/app/engine/session_delta.py
index dd99e020..fb3a882a 100644
--- a/apps/backend/app/engine/session_delta.py
+++ b/apps/backend/app/engine/session_delta.py
@@ -19,6 +19,15 @@ unchanged behavior) and `app.engine.compass.build_rotation` (`session_delta.rota
 `rotation_top_k`-capped, both directions) both build from — one query pair per manifest build, two
 capped consumers. Sector/theme-kind `changes[]` entries additionally carry this signed `delta`
 (direction-word wording is compass.py's concern — it owns `compass.vocabulary`, this module does not).
+
+`_stock_changes` (goal-market-compass iter-40, J-15): classifies the FULL stock-kind bucket-crossing
+list against `stock_score_min_change` BEFORE applying the `max_stock_items` display bound, so every
+evaluated crossing lands in exactly one of shown / suppressed / residual; `compute_delta` serves the
+partition as `session_delta.stock_accounting = {evaluated_count, shown_count, suppressed_count,
+residual_count}` (`evaluated_count == shown_count + suppressed_count + residual_count`) -- mirroring how
+J-13 (iter-36) closed the same hole for the sector/theme kinds. `max_stock_items` keeps its existing
+value and stays the DISPLAY cap only; new-to-universe members keep their pre-existing unconditional
+display priority and stay outside this accounting (they are never subject to the threshold).
 """
 from __future__ import annotations
 
@@ -214,11 +223,17 @@ def _theme_changes(pairs: list[tuple[dict, float]], cfg: Config) -> tuple[list[d
 
 def _stock_changes(
     session: Session, current: ScannerRun, previous: ScannerRun, as_of_iso: str, cfg: Config
-) -> tuple[list[dict], list[dict]]:
+) -> tuple[list[dict], list[dict], dict]:
     """Stock-kind entries are leadership-BUCKET crossings (TC-5) plus new-to-universe members (TC-7,
-    reported unconditionally — never as a score change). Bounded to `max_stock_items` total (new members
-    prioritized) so this producer never evaluates, ranks, or displays the full ~500+ member universe in
-    one pass (AG-8)."""
+    reported unconditionally — never as a score change, always prioritized ahead of crossings and
+    unconditionally exempt from the threshold, unchanged from before). `changes`/`suppressed` stay
+    bounded to `max_stock_items` total DISPLAY entries (new members prioritized) so this producer never
+    RANKS OR DISPLAYS the full ~500+ member universe in one pass (AG-8) — but every evaluated bucket
+    crossing is still CLASSIFIED (goal-market-compass iter-40, J-15): the third return value,
+    `stock_accounting`, accounts for the full `crossing_pairs` list computed below (no second
+    materialization, no new query) so a crossing lands in exactly one of shown / suppressed / residual
+    (`evaluated_count == shown_count + suppressed_count + residual_count`) — nothing above
+    `stock_score_min_change` vanishes uncounted past the display cap the way it did before this change."""
     threshold = cfg.compass.delta.stock_score_min_change
     max_items = cfg.compass.delta.max_stock_items
     cur_rows = session.exec(
@@ -258,12 +273,26 @@ def _stock_changes(
     new_pairs.sort(key=lambda pair: pair[1], reverse=True)
     crossing_pairs.sort(key=lambda pair: pair[1], reverse=True)
     bounded_new = new_pairs[:max_items]
-    bounded_crossings = crossing_pairs[: max(max_items - len(bounded_new), 0)]
+    available_slots = max(max_items - len(bounded_new), 0)
+
+    # J-15: classify the FULL crossing_pairs list (unchanged threshold semantics) BEFORE applying the
+    # max_stock_items display bound, so every evaluated crossing lands in exactly one bucket. `_classify`
+    # preserves the magnitude-desc order already applied above, so `meets_threshold` is still most-moved
+    # first -- the display bound then splits it into the shown head and the residual tail.
+    meets_threshold, suppressed = _classify(crossing_pairs, threshold)
+    shown_crossings = meets_threshold[:available_slots]
+    residual_crossings = meets_threshold[available_slots:]
 
     changes = [entry for entry, _magnitude in bounded_new]
-    crossing_changes, suppressed = _classify(bounded_crossings, threshold)
-    changes.extend(crossing_changes)
-    return changes, suppressed
+    changes.extend(shown_crossings)
+
+    stock_accounting = {
+        "evaluated_count": len(crossing_pairs),
+        "shown_count": len(shown_crossings),
+        "suppressed_count": len(suppressed),
+        "residual_count": len(residual_crossings),
+    }
+    return changes, suppressed, stock_accounting
 
 
 def compute_delta(
@@ -300,15 +329,23 @@ def compute_delta(
         _breadth_changes(current_run, previous_run, as_of_iso, cfg),
         _sector_changes(sector_pairs, cfg),
         _theme_changes(theme_pairs, cfg),
-        _stock_changes(session, current_run, previous_run, as_of_iso, cfg),
     ):
         changes.extend(changes_part)
         suppressed.extend(suppressed_part)
 
+    # goal-market-compass iter-40 (J-15): `_stock_changes` also returns the stock-kind accounting object
+    # -- computed in the SAME pass over `crossing_pairs` above, no second query, no second materialization.
+    stock_changes, stock_suppressed, stock_accounting = _stock_changes(
+        session, current_run, previous_run, as_of_iso, cfg
+    )
+    changes.extend(stock_changes)
+    suppressed.extend(stock_suppressed)
+
     return {
         "prior_as_of": previous_run.asof_date.isoformat(),
         "gap_days": (current_run.asof_date - previous_run.asof_date).days,
         "changes": changes,
         "suppressed": suppressed,
         "suppressed_count": len(suppressed),
+        "stock_accounting": stock_accounting,
     }
diff --git a/apps/backend/tests/test_session_delta.py b/apps/backend/tests/test_session_delta.py
index dc5cb023..fe7dded3 100644
--- a/apps/backend/tests/test_session_delta.py
+++ b/apps/backend/tests/test_session_delta.py
@@ -404,6 +404,139 @@ def test_compute_delta_reuses_precomputed_pairs_no_second_query(engine, cfg, two
         assert id(entry) in theme_entry_ids
 
 
+# --- iter-40 (J-15): stock-kind accounting (shown / suppressed / residual close against evaluated) ----
+
+
+def test_stock_accounting_present_and_closes_exactly_on_two_runs_fixture(engine, cfg, two_runs):
+    """`two_runs` has exactly one bucket crossing (AAPL, above threshold) and one new-to-universe member
+    (NEWC, outside the accounting) -- well under `max_stock_items` (10), so nothing is bounded: the whole
+    crossing is shown, nothing suppressed or residual."""
+    run_a_id, run_b_id = two_runs
+    with Session(engine) as session:
+        run_a = session.get(ScannerRun, run_a_id)
+        run_b = session.get(ScannerRun, run_b_id)
+        result = compute_delta(session, run_b, run_a, cfg)
+    accounting = result["stock_accounting"]
+    assert accounting == {
+        "evaluated_count": 1, "shown_count": 1, "suppressed_count": 0, "residual_count": 0,
+    }
+    assert accounting["evaluated_count"] == (
+        accounting["shown_count"] + accounting["suppressed_count"] + accounting["residual_count"]
+    )
+
+
+def test_no_prior_run_state_has_no_stock_accounting_key(engine, cfg):
+    """The explicit no-prior-run early return stays byte-identical to before this iteration -- no
+    `stock_accounting` key is fabricated when there is nothing to account for (mirrors `rotation`'s own
+    no-prior-run absence, iter-36)."""
+    with Session(engine) as session:
+        run = _mk_run(session, date(2024, 1, 1), 50.0, 40.0, 45.0)
+        session.commit()
+        session.refresh(run)
+        result = compute_delta(session, run, None, cfg)
+    assert "stock_accounting" not in result
+
+
+def test_zero_stock_crossings_yields_explicit_zero_accounting(engine, cfg):
+    """Fixture (c) from the goal text step 8: zero stock-kind crossings evaluated -> an explicit,
+    honest all-zero `stock_accounting`, never a blank/missing block."""
+    with Session(engine) as session:
+        run_a = _mk_run(session, date(2024, 3, 1), 50.0, 40.0, 45.0)
+        run_b = _mk_run(session, date(2024, 3, 8), 50.0, 40.0, 45.0)  # no ScannerResult rows on either side
+        session.commit()
+        session.refresh(run_a)
+        session.refresh(run_b)
+        result = compute_delta(session, run_b, run_a, cfg)
+    assert result["stock_accounting"] == {
+        "evaluated_count": 0, "shown_count": 0, "suppressed_count": 0, "residual_count": 0,
+    }
+
+
+@pytest.fixture()
+def many_crossings_run(engine, cfg):
+    """Fixture (a) from the goal text step 8: MORE above-threshold bucket crossings (12) than
+    `max_stock_items` (10, the live config value) plus 3 below-threshold crossings -- so the accounting
+    must show exactly 10, hold 2 back as residual (never dropped uncounted), and count the 3 as
+    suppressed. All 15 tickers get a DISTINCT magnitude so shown-vs-residual is unambiguous
+    (most-moved-first, ties never arise)."""
+    with Session(engine) as session:
+        run_a = _mk_run(session, date(2024, 4, 1), 50.0, 40.0, 45.0)
+        run_b = _mk_run(session, date(2024, 4, 8), 50.0, 40.0, 45.0)
+        # 12 above-threshold crossings (magnitude 8.5 .. 19.5, all >= stock_score_min_change 8.0), bucket C -> A
+        for i in range(12):
+            ticker = f"X{i:02d}"
+            _mk_result(session, run_a.id, ticker, 50.0, "C")
+            _mk_result(session, run_b.id, ticker, 50.0 + 8.5 + i, "A")
+        # 3 below-threshold crossings (magnitude 1.0 .. 3.0, all < 8.0), bucket C -> B
+        for i in range(3):
+            ticker = f"Y{i:02d}"
+            _mk_result(session, run_a.id, ticker, 50.0, "C")
+            _mk_result(session, run_b.id, ticker, 50.0 + 1.0 + i, "B")
+        session.commit()
+        session.refresh(run_a)
+        session.refresh(run_b)
+        return run_a.id, run_b.id
+
+
+def test_more_crossings_than_cap_close_via_shown_suppressed_residual(engine, cfg, many_crossings_run):
+    assert cfg.compass.delta.max_stock_items == 10  # the live config value this fixture is built against
+    assert cfg.compass.delta.stock_score_min_change == 8.0
+    run_a_id, run_b_id = many_crossings_run
+    with Session(engine) as session:
+        run_a = session.get(ScannerRun, run_a_id)
+        run_b = session.get(ScannerRun, run_b_id)
+        result = compute_delta(session, run_b, run_a, cfg)
+    accounting = result["stock_accounting"]
+    assert accounting == {
+        "evaluated_count": 15, "shown_count": 10, "suppressed_count": 3, "residual_count": 2,
+    }
+    stock_changes = _by_kind(result["changes"], KIND_STOCK)
+    assert len(stock_changes) == 10  # display cap held, exactly as before this iteration
+    shown_labels = {c["label"] for c in stock_changes}
+    # the two LOWEST-magnitude above-threshold movers (X00 magnitude 8.5, X01 magnitude 9.5) are bumped
+    # into the residual bucket -- never shown, never silently dropped, never counted as suppressed
+    assert "X00 leadership bucket" not in shown_labels
+    assert "X01 leadership bucket" not in shown_labels
+    # the highest-magnitude mover (X11, magnitude 19.5) is always shown
+    assert "X11 leadership bucket" in shown_labels
+    # the 3 below-threshold crossings are counted as suppressed, never shown, never residual
+    suppressed_stock = [s for s in result["suppressed"] if s["kind"] == KIND_STOCK]
+    assert len(suppressed_stock) == 3
+    assert all(s["magnitude"] < cfg.compass.delta.stock_score_min_change for s in suppressed_stock)
+
+
+def test_new_to_universe_reduces_available_display_slots_for_crossings(engine, cfg):
+    """Fixture (b) from the goal text step 8: new-to-universe members keep their existing unconditional
+    display priority -- they consume display slots ahead of crossings, so they reduce how many above-
+    threshold crossings can be SHOWN, but they never appear in `stock_accounting` (only crossings are
+    "evaluated" against the threshold) and never turn a crossing into a fabricated suppression."""
+    with Session(engine) as session:
+        run_a = _mk_run(session, date(2024, 5, 1), 50.0, 40.0, 45.0)
+        run_b = _mk_run(session, date(2024, 5, 8), 50.0, 40.0, 45.0)
+        # 2 new-to-universe members (present only in run_b) -- unconditional priority, outside accounting
+        for i in range(2):
+            _mk_result(session, run_b.id, f"NEW{i}", 70.0, "C")
+        # 12 above-threshold crossings (magnitude 8.5 .. 19.5)
+        for i in range(12):
+            ticker = f"X{i:02d}"
+            _mk_result(session, run_a.id, ticker, 50.0, "C")
+            _mk_result(session, run_b.id, ticker, 50.0 + 8.5 + i, "A")
+        session.commit()
+        session.refresh(run_a)
+        session.refresh(run_b)
+        result = compute_delta(session, run_b, run_a, cfg)
+    accounting = result["stock_accounting"]
+    # 2 display slots go to the new-to-universe members first (unconditional), leaving 8 of the 10
+    # max_stock_items slots for crossings -- so 8 shown, 4 residual, 0 suppressed (all 12 clear threshold)
+    assert accounting == {
+        "evaluated_count": 12, "shown_count": 8, "suppressed_count": 0, "residual_count": 4,
+    }
+    stock_changes = _by_kind(result["changes"], KIND_STOCK)
+    assert len(stock_changes) == 10  # 2 new-to-universe + 8 shown crossings, display cap unchanged
+    new_entries = [c for c in stock_changes if c["from"] == "new"]
+    assert len(new_entries) == 2
+
+
 def test_compute_delta_without_precomputed_pairs_matches_precomputed_call(engine, cfg, two_runs):
     """Omitting `sector_pairs`/`theme_pairs` (every pre-iter-36 caller) yields the SAME `changes`/
     `suppressed` values as passing them explicitly -- backward-compatible default."""
diff --git a/apps/frontend/components/compass-focus-section.tsx b/apps/frontend/components/compass-focus-section.tsx
index 0041f907..e9b21e90 100644
--- a/apps/frontend/components/compass-focus-section.tsx
+++ b/apps/frontend/components/compass-focus-section.tsx
@@ -133,6 +133,21 @@ function WhyNotLeadIn({ entry }: { entry: WhyNotEntry }) {
   );
 }
 
+/** The `failed.gating` suffix (goal-market-compass iter-40 — AG-8 regression repair per the iter-39
+ *  evaluator's finding). Reviewed: `WhyNotFailedCondition.gating` is OPTIONAL (`lib/api.ts`) -- absent,
+ *  not `false`, on every `failed_conditions` entry served from a manifest minted before the iter-38
+ *  `rule_version` bump (all 21 pre-iter-38 stored as-of dates). The prior `failed.gating ? "" : "
+ *  — advisory"` truthiness read treated `undefined` the same as `false`, mislabeling 26 stored
+ *  leadership-floor misses "— advisory" though they were never checked. This is a genuine 3-state
+ *  render: `undefined` ("not recorded for this manifest version") is distinct from BOTH `true` (gating,
+ *  no suffix) and `false` (advisory). */
+function gatingSuffix(gating: boolean | undefined): string {
+  if (gating === undefined) {
+    return " — not recorded";
+  }
+  return gating ? "" : " — advisory";
+}
+
 function WhyNotList({ entries }: { entries: WhyNotEntry[] }) {
   if (entries.length === 0) {
     return <p className="pt-1 text-xs text-text-faint">No near-miss names this session.</p>;
@@ -148,7 +163,7 @@ function WhyNotList({ entries }: { entries: WhyNotEntry[] }) {
               {entry.failed_conditions.map((failed, index) => (
                 <li key={index}>
                   {failed.condition}: {failed.actual.toFixed(1)} vs {failed.threshold.toFixed(1)} (distance{" "}
-                  {failed.distance.toFixed(1)}){failed.gating ? "" : " — advisory"}
+                  {failed.distance.toFixed(1)}){gatingSuffix(failed.gating)}
                 </li>
               ))}
             </ul>
diff --git a/apps/frontend/components/compass-whatchanged-card.tsx b/apps/frontend/components/compass-whatchanged-card.tsx
index c038f73b..fac0b6e6 100644
--- a/apps/frontend/components/compass-whatchanged-card.tsx
+++ b/apps/frontend/components/compass-whatchanged-card.tsx
@@ -7,6 +7,7 @@ import { Badge } from "@/components/ui/badge";
 import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
 import { Disclosure } from "@/components/ui/disclosure";
 import { formatIsoDate } from "@/lib/dates";
+import { stockResidualDisclosureText, stockShownCapDisclosureText } from "@/lib/stock-accounting-summary";
 import type { CompassResponse, SessionDeltaChange } from "@/lib/api";
 
 const KIND_LABEL: Record<SessionDeltaChange["kind"], string> = {
@@ -35,6 +36,11 @@ export function CompassWhatChangedCard({ compass }: { compass: CompassResponse |
 
   const { session_delta } = compass;
   const noPriorRun = session_delta.prior_as_of === null;
+  // goal-market-compass iter-40 (J-15): both `null` when `session_delta.stock_accounting` is absent (a
+  // manifest frozen before this field existed) -- the card then renders nothing new, exactly as before
+  // this iteration (AG-8).
+  const stockCapText = stockShownCapDisclosureText(session_delta.stock_accounting);
+  const stockResidualText = stockResidualDisclosureText(session_delta.stock_accounting);
 
   return (
     <Card data-testid="compass-whatchanged-card">
@@ -73,6 +79,13 @@ export function CompassWhatChangedCard({ compass }: { compass: CompassResponse |
             ))}
           </ul>
         )}
+        {/* goal-market-compass iter-40 (J-15, TC-4b): discloses its own bound instead of truncating
+            silently -- only when the display cap actually held something back this session. */}
+        {stockCapText !== null ? (
+          <p className="text-xs text-text-faint" data-testid="compass-whatchanged-stock-cap">
+            {stockCapText}
+          </p>
+        ) : null}
         <Disclosure summary={`Suppressed moves (${session_delta.suppressed_count})`}>
           {session_delta.suppressed.length === 0 ? (
             <p className="pt-1 text-xs text-text-faint">No moves were suppressed this session.</p>
@@ -89,6 +102,16 @@ export function CompassWhatChangedCard({ compass }: { compass: CompassResponse |
             </ul>
           )}
         </Disclosure>
+        {/* goal-market-compass iter-40 (J-15, TC-4): a residual disclosure, VISIBLY DISTINCT from the
+            "Suppressed moves" line above -- an above-threshold mover held back by the display cap is a
+            different thing from a below-threshold one; count only, no per-name list (AG-8). Renders only
+            when `session_delta.stock_accounting` is present (absent on manifests frozen before this field
+            existed, TC-5); shows an explicit zero rather than nothing when nothing was held back. */}
+        {stockResidualText !== null ? (
+          <p className="text-xs text-text-muted" data-testid="compass-whatchanged-stock-residual">
+            {stockResidualText}
+          </p>
+        ) : null}
       </CardContent>
     </Card>
   );
diff --git a/apps/frontend/lib/api.ts b/apps/frontend/lib/api.ts
index cd6da4db..d13d67f7 100644
--- a/apps/frontend/lib/api.ts
+++ b/apps/frontend/lib/api.ts
@@ -948,6 +948,22 @@ export interface SessionDeltaSuppressed {
   threshold: number;
 }
 
+/** The stock-kind accounting object (goal-market-compass iter-40, J-15): every stock-kind bucket
+ *  crossing the producer evaluates lands in exactly one bucket — `evaluated_count ==
+ *  shown_count + suppressed_count + residual_count`. `shown_count` is how many crossing entries are
+ *  actually present in `session_delta.changes` (kind `stock`, new-to-universe entries excluded — they
+ *  carry unconditional priority and are never subject to the threshold, so they are outside this
+ *  accounting exactly as before this field existed); `suppressed_count` is crossings below
+ *  `compass.delta.stock_score_min_change`; `residual_count` is crossings that met the threshold but were
+ *  bumped by the `compass.delta.max_stock_items` display cap — a count only, never a per-name list
+ *  (AG-8). */
+export interface SessionDeltaStockAccounting {
+  evaluated_count: number;
+  shown_count: number;
+  suppressed_count: number;
+  residual_count: number;
+}
+
 /** The `session_delta` CONTENT block (J-02). `prior_as_of`/`gap_days` are both `null` for the
  *  earliest stored run — the explicit no-prior-run state; never a fabricated comparison. */
 export interface SessionDelta {
@@ -962,6 +978,11 @@ export interface SessionDelta {
   // historical as-of can legitimately have a non-null `prior_as_of` and NO `rotation` — consumers must
   // branch on its absence and show an honest placeholder (AG-8), never dereference it unguarded.
   rotation?: CompassRotation;
+  // iter-40 (J-15) — additive and OPTIONAL for the SAME reason as `rotation` above: every
+  // `next_session_manifests` row frozen before this field existed has no `stock_accounting` key at all
+  // (never backfilled — AG-12). Consumers MUST branch on its absence and render nothing new, never
+  // dereference it unguarded.
+  stock_accounting?: SessionDeltaStockAccounting;
 }
 
 /** One cited fact backing a narrative sentence (J-03) — spot-checkable against the canonical
@@ -1042,13 +1063,20 @@ export interface CompassCandidate {
  *  `_qualifier_checks` computes for every candidate checklist row: `true` only for `leadership_min_score`
  *  (the sole candidacy gate), `false` for the advisory `entry_min_score`/`risk_max_score` qualifiers
  *  (they annotate a caution and never remove a row from candidacy, and never explain a why-not entry's
- *  `reason` on their own). */
+ *  `reason` on their own).
+ *
+ *  OPTIONAL (goal-market-compass iter-40 — AG-8 regression repair per the iter-39 evaluator's finding):
+ *  `gating` is absent, not `false`, on every `failed_conditions` entry served from a manifest minted
+ *  before the iter-38 `rule_version` bump (all 21 pre-iter-38 stored as-of dates) — it was never a
+ *  required field on the stored data, only mis-declared as one here. A reader MUST treat `undefined` as
+ *  "not recorded for this manifest version", distinct from both `true` and `false`, never defaulted to
+ *  either. */
 export interface WhyNotFailedCondition {
   condition: string;
   threshold: number;
   actual: number;
   distance: number;
-  gating: boolean;
+  gating?: boolean;
 }
 
 /** The closed reason vocabulary for a `WhyNotEntry` (J-14) — reuses `selection_disposition`'s EXISTING
diff --git a/config.yaml b/config.yaml
index d6f0bf78..970e13e2 100644
--- a/config.yaml
+++ b/config.yaml
@@ -1422,7 +1422,7 @@ compass:
     stock_score_min_change: 8.0      # leadership-score points a bucket-crossing stock must move to report a "stock" change
     top_k: 5                         # max sector-kind and max theme-kind change entries shown (most-moved first; mirrors the existing Top-Sectors/Top-Themes "top 5" convention)
     rotation_top_k: 5                # goal-market-compass iter-36 (J-13): max GAINING and max LOSING rows shown per side of session_delta.rotation.{sector,theme} -- independent of top_k above (session_delta.changes stays unchanged); above-threshold movers beyond this cap are counted in that side's residual_count, never dropped uncounted
-    max_stock_items: 10              # max stock-kind change entries evaluated/shown (bounds both compute and display — AG-8)
+    max_stock_items: 10              # max stock-kind change entries SHOWN (goal-market-compass iter-40, J-15: display cap only -- every evaluated bucket crossing is still classified as shown/suppressed/residual via session_delta.stock_accounting, never dropped uncounted; AG-8's bound on ranking/displaying the full universe stays intact since _stock_changes already iterates every member and materializes only the small crossing list)
     velocity_flat_band: 2.0          # |regime-score delta| below this reads as "little changed" in the narrative's direction sentence
     stress_velocity_flat_band: 5.0   # goal-market-compass iter-28 (J-07): |severity delta| below this reads as "little changed" for state_band.stress (a dedicated key -- severity is a different 0-100 scale than the regime score, not a reuse of velocity_flat_band above). state_band.breadth reuses breadth_min_change_pts below unchanged.
     pbear_bands:                     # filtered P(bear) -> narrative state word (ascending min, like market_phase.phase_edges)
diff --git a/apps/frontend/lib/stock-accounting-summary.test.ts b/apps/frontend/lib/stock-accounting-summary.test.ts
new file mode 100644
index 00000000..46a74c95
--- /dev/null
+++ b/apps/frontend/lib/stock-accounting-summary.test.ts
@@ -0,0 +1,76 @@
+/**
+ * Unit tests for the What-changed card's stock-accounting disclosure helpers
+ * (lib/stock-accounting-summary.ts) — goal-market-compass iter-40, J-15.
+ *
+ * No test framework is installed in this frontend; these run under Node's native TS type-stripping:
+ *   node lib/stock-accounting-summary.test.ts
+ *
+ * Covers the two manifest shapes named in the TESTING REQUIREMENTS: an OLD (absent-field) fixture and a
+ * NEW (present-field) fixture, plus the residual-zero and residual-positive branches.
+ */
+import assert from "node:assert";
+
+import { stockResidualDisclosureText, stockShownCapDisclosureText } from "./stock-accounting-summary.ts";
+
+let passed = 0;
+function check(name: string, fn: () => void) {
+  fn();
+  passed += 1;
+  console.log(`  ok - ${name}`);
+}
+
+// --- old fixture: stock_accounting absent (pre-iter-40 manifest) -> render nothing new, no throw -----
+
+check("undefined stock_accounting yields no residual disclosure (old manifest, AG-8)", () => {
+  assert.strictEqual(stockResidualDisclosureText(undefined), null);
+});
+
+check("undefined stock_accounting yields no shown-cap disclosure (old manifest, AG-8)", () => {
+  assert.strictEqual(stockShownCapDisclosureText(undefined), null);
+});
+
+check("omitting stock_accounting entirely (optional field) behaves identically to passing undefined", () => {
+  assert.strictEqual(stockResidualDisclosureText(), null);
+  assert.strictEqual(stockShownCapDisclosureText(), null);
+});
+
+// --- new fixture, residual_count > 0 (the frontier-pair shape: 10 shown, 43 suppressed, 4 residual) ---
+
+check("present stock_accounting with residual > 0 discloses the held-back count", () => {
+  const summary = stockResidualDisclosureText({
+    evaluated_count: 57, shown_count: 10, suppressed_count: 43, residual_count: 4,
+  });
+  assert.strictEqual(summary, "4 more stock moves held back by the display cap");
+});
+
+check("present stock_accounting with residual > 0 discloses the shown-top-N cap", () => {
+  const summary = stockShownCapDisclosureText({
+    evaluated_count: 57, shown_count: 10, suppressed_count: 43, residual_count: 4,
+  });
+  assert.strictEqual(summary, "Showing the top 10 stock moves");
+});
+
+check("residual_count === 1 is singular ('move', not 'moves')", () => {
+  const summary = stockResidualDisclosureText({
+    evaluated_count: 11, shown_count: 10, suppressed_count: 0, residual_count: 1,
+  });
+  assert.strictEqual(summary, "1 more stock move held back by the display cap");
+});
+
+// --- new fixture, residual_count === 0 (nothing held back this session) ------------------------------
+
+check("present stock_accounting with residual === 0 still discloses an explicit zero (never blank)", () => {
+  const summary = stockResidualDisclosureText({
+    evaluated_count: 3, shown_count: 3, suppressed_count: 0, residual_count: 0,
+  });
+  assert.strictEqual(summary, "0 more stock moves held back by the display cap");
+});
+
+check("present stock_accounting with residual === 0 omits the shown-top-N cap entirely", () => {
+  const summary = stockShownCapDisclosureText({
+    evaluated_count: 3, shown_count: 3, suppressed_count: 0, residual_count: 0,
+  });
+  assert.strictEqual(summary, null);
+});
+
+console.log(`\n${passed} passed`);
diff --git a/apps/frontend/lib/stock-accounting-summary.ts b/apps/frontend/lib/stock-accounting-summary.ts
new file mode 100644
index 00000000..b72863dc
--- /dev/null
+++ b/apps/frontend/lib/stock-accounting-summary.ts
@@ -0,0 +1,48 @@
+/**
+ * goal-market-compass iter-40 (J-15) — pure disclosure-text helpers for the What-changed card's
+ * stock-kind accounting (`compass-whatchanged-card.tsx`), extracted so the optional-field guard is
+ * unit-testable under this project's plain-node convention (`node lib/stock-accounting-summary.test.ts`,
+ * no test framework installed) — mirrors the `why-not-summary.ts` extraction from iter-39.
+ *
+ * `session_delta.stock_accounting` is OPTIONAL: absent on every `next_session_manifests` row frozen
+ * before this field existed (never backfilled — AG-12). Both helpers return `null` for that case so the
+ * card renders nothing new, never a crash and never a fabricated count (AG-8).
+ *
+ * `StockAccountingLike` mirrors `SessionDeltaStockAccounting` (lib/api.ts) as its OWN local type
+ * (dependency-free, so this module runs under plain `node` without pulling in api.ts's fetch machinery).
+ */
+export interface StockAccountingLike {
+  evaluated_count: number;
+  shown_count: number;
+  suppressed_count: number;
+  residual_count: number;
+}
+
+/**
+ * The residual disclosure — distinct text from the existing "Suppressed moves (N)" line (TC-4): an
+ * above-threshold stock mover held back by the display cap is a DIFFERENT thing from a below-threshold
+ * one, and the reader must be able to tell them apart. Renders even at `residual_count === 0` (an
+ * explicit, honest zero — never a blank) whenever `stock_accounting` is present; `null` (render nothing)
+ * only when the field itself is absent (TC-5).
+ */
+export function stockResidualDisclosureText(stockAccounting?: StockAccountingLike): string | null {
+  if (stockAccounting === undefined) {
+    return null;
+  }
+  const n = stockAccounting.residual_count;
+  return `${n} more stock move${n === 1 ? "" : "s"} held back by the display cap`;
+}
+
+/**
+ * The "showing top N" disclosure beside the shown stock entries (TC-4b, goal text step 4) — only when
+ * the display cap actually held something back this session (`residual_count > 0`); omitted entirely
+ * when `residual_count === 0` or `stock_accounting` is absent, so an unbounded session shows no
+ * unnecessary caveat.
+ */
+export function stockShownCapDisclosureText(stockAccounting?: StockAccountingLike): string | null {
+  if (stockAccounting === undefined || stockAccounting.residual_count === 0) {
+    return null;
+  }
+  const n = stockAccounting.shown_count;
+  return `Showing the top ${n} stock move${n === 1 ? "" : "s"}`;
+}
```
