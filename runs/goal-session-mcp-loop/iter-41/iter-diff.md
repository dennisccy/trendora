# Iteration diff (bounded)

Files changed: 20. Shown in full: 18.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/app/engine/forward_testing.py` (43 lines not shown)
- `apps/backend/tests/test_forward_testing.py` (181 lines not shown)

```diff
diff --git a/README.md b/README.md
index f558ee4..5645cba 100644
--- a/README.md
+++ b/README.md
@@ -12,6 +12,7 @@ Current capabilities:
 - **Evidence tracking**: Every Leadership, Entry Quality, and Risk score on the Stocks leaderboard and on each stock detail page shows an evidence-status chip — "Not yet proven" (muted) or "Proven" (linked) — immediately below the score badge, so a reader always knows at a glance whether hard, out-of-sample statistical evidence currently backs each score. An **Evidence** page, reachable in one click from the left navigation sidebar (ShieldCheck icon, after Research), lists every claim the platform has tested; each row shows its hypothesis, out-of-sample verdict, control comparison versus SPY, registration date, and forward-walk score-to-date. When a claim is certified, a **"Why proven?"** disclosure toggle appears below the affected score's badge on its stock detail page; opening it reveals an auditable proof panel with the out-of-sample test result, the SPY benchmark control, and a direct link to the matching Evidence ledger row — supporting a full round trip from the Stocks leaderboard through a stock's proof panel to the Evidence ledger and back. On the Research factor lab, every factor row shows a compact strip of five **"Evidence (D10 · per horizon)"** chips — one per tested holding period (1d, 5d, 10d, 20d, 60d) — each resolved independently to "Proven" (with a direct deep-link to the ledger entry) or "Not yet proven" (no link); a factor that was tested and rejected (such as ma_stack) shows "Not yet proven" at every horizon — a failed test never looks confident. The **Dashboard Market Regime card** links directly to the Evidence page so a reader can jump from the current regime straight to whatever is certified in it. Following the platform's move to a deeper, up-to-30-year price history, every one of the platform's seven previously-certified claims was honestly re-examined from scratch on the new data, and none currently hold up out-of-sample — every score, setup, and factor cohort across the product therefore currently reads "Not yet proven" rather than displaying a number that no longer holds. This is the evidence system working as designed: an edge that only held on shorter history is retired rather than left on display, and a fetch failure degrades the same safe way — never fabricating evidence.
 - **Point-in-time stock universe**: the set of stocks the scanner scores is recomputed for the date you are viewing, drawn from a broadened candidate pool of roughly 548 names — a name only qualifies once it has enough price history, a sufficient share price, adequate trading liquidity, and a price feed that hasn't gone stale (stopped updating for more than 10 calendar days), all measured from data on or before that date. Before enough history has accumulated for a given date the leaderboard is honestly empty (0 rows); the universe grows as more names clear the history bar across the platform's now up-to-30-year price history. The universe count on Data Manager changes in real time as you step the global date switcher — and the count shown on the coverage diagnostic always agrees with the count served on the leaderboard. All leaderboard pages (Stocks, Themes, Sectors), Backtest evidence, and Research surfaces reflect only the names that qualify at the viewed date. The Data Manager membership timeline renders a true step-function curve: the SIZE column varies by date, and the Entries and Exits columns are populated with real membership changes rather than dashes.
 - **Stock detail**: full price + moving-average + volume chart (extending through the latest seed date with an as-of marker for historical views) with **optional market-regime bands** in the background (toggle default-on, persists) and a **chart-range toggle** — Recent (a bounded ~5-year trailing window, the default) or Full history (the stock's entire real history back to its actual first trading day, as early as 1996 for the longest-tenured names) — with a header caption disclosing the exact bar count, the as-of date, and the stock's first available date; Full-history view is honestly thinned to weekly bars beyond a set age so it stays responsive, and a recently-listed stock's short real history is shown as-is, never padded with invented earlier prices. A **Realized forward returns** panel above the chart shows the five horizon returns (1d / 5d / 10d / 20d / 60d) colour-graded for the resolved as-of date, each accompanied by its paired **max-drawdown figure** (the worst peak-to-trough decline within that window) colour-graded by loss magnitude to match the leaderboard exactly; per-score component breakdowns (the Leadership breakdown shows the actual distance-below-52w-high percentage — e.g., `-0.53%` — matching the leaderboard column for that stock), theme membership, setup status, plain-language reason, and a concrete invalidation level. A **crosshair hover detail box** tracks the cursor over the price chart and displays the exact date, open, high, low, close, volume, percentage change, and each moving-average value for the bar under the cursor — bars that fall after the selected as-of date are clearly labelled as display-only; the box disappears when the cursor leaves the chart.
+- **Risk budget**: every stock detail page shows a **Risk budget card**, sitting directly below the "Theme & invalidation" card and above the pattern cards (VCP, etc.), captioned "Descriptive only; not a recommendation" — no buy/sell/trim wording. It answers "how much can this hurt" with ATR%, downside-only volatility, an overnight-gap profile (the near-worst p95 gap as the headline figure, with median and worst gap shown as supporting detail) plus the overnight share of 20-day return variance, the single worst historical 20-trading-day window in the stock's whole price history, and the exact distance to its invalidation level — every number carries a **"pXX of universe" percentile chip** showing how that figure ranks against the rest of the scanned universe. The same five headline numbers — ATR%, Downside vol, Gap p95, Worst 20d, and Dist. to invalidation — appear as sortable, right-aligned columns on the `/stocks` leaderboard (inserted between the existing "High proximity" and "Setup" columns), each carrying the same inline info-icon definition used by every other column and reading the identical stored figures as the detail card so the leaderboard and the detail page can never disagree. A stock with too little trading history honestly shows "NA — insufficient history" on the affected tiles or cells instead of a fabricated number, and the Methodology glossary documents all three new metrics — overnight-gap profile, worst 20-day window, and distance-to-invalidation % — including the exact 20-trading-day window each is computed over.
 - **Theme leaderboard**: ranked by score; each theme shows member tickers, basket returns, breadth, and trend label — clicking "+n" expands to reveal every remaining member in place, and every member name is a link that opens the dated stock detail in a new tab without disturbing the themes page. The leaderboard shows **five realized forward-return columns (1d / 5d / 10d / 20d / 60d)** and five paired **max-drawdown columns** — the equal-weight average across a theme's member stocks — colour-graded by loss magnitude (faint red for shallow losses, saturated red for deep losses) with "NA" shown in muted text. All ten columns are sortable; NA values always sort to the bottom.
 - **Sectors leaderboard**: every ETF row shows its config-defined display name (e.g. "Semiconductors (VanEck)" rather than "SMH") and RS-vs-SPY, distance from 52-week high, and trend label. Expanding any row reveals a plain-language description of what that industry group represents plus the exact universe stocks mapped to that sector or industry — displayed as dated ticker chips. Up to six chips appear immediately; clicking "+N" reveals all remaining members and "Show fewer" collapses back. ETFs with no mapped universe members display an explicit empty message — nothing is invented. Every chip opens the stock's dated detail page in a new tab and carries the `?asof` parameter when browsing a historical date. The leaderboard shows **five realized forward-return columns (1d / 5d / 10d / 20d / 60d)** and five paired **max-drawdown columns** for each sector/industry ETF — colour-graded by loss magnitude (faint red for shallow losses, saturated red for deep losses), sortable with NA values always at the bottom, matching Backtest values exactly.
 - **Immutable scanner-run history**: append-only snapshots; opening a past run shows exactly what the scanner said on that date.
diff --git a/apps/backend/app/api/evidence.py b/apps/backend/app/api/evidence.py
index 968032d..3405f11 100644
--- a/apps/backend/app/api/evidence.py
+++ b/apps/backend/app/api/evidence.py
@@ -6,22 +6,29 @@ proven-ness — it re-displays the referee's verdicts verbatim. An absent/empty
 empty payload (`{"claims": [], "proven_signals": {}}`), never a 500 — the fail-safe the whole evidence
 frame rests on (an unbacked signal must render "Not yet proven", never a confident number).
 
-No DB/session is needed (the evidence comes from the append-only ledger file, not the snapshot DB). The
-ledger path is config/env-driven via the resolver (anti-goal: No magic numbers — no path literal here).
+The ledger path is config/env-driven via the resolver (anti-goal: No magic numbers — no path literal
+here). A DB session is threaded through (iter-41, J-25) so `build_evidence_payload` can ADDITIVELY attach
+each claim's phase-conditional drawdown/dry-spell `expectations` (`app.engine.forward_testing.
+compute_drawdown_expectations`) — the snapshot DB itself is still never written by this route.
 """
 from __future__ import annotations
 
-from fastapi import APIRouter
+from fastapi import APIRouter, Depends
+from sqlmodel import Session
 
+from app.config import get_config
+from app.db import get_session
 from app.engine.evidence import build_evidence_payload, resolve_ledger_path
 
 router = APIRouter(tags=["evidence"])
 
 
 @router.get("/evidence")
-def get_evidence() -> dict:
+def get_evidence(session: Session = Depends(get_session)) -> dict:
     """The certified-claims ledger payload: `claims` (the ledger rows the Evidence page renders —
-    hypothesis, out-of-sample verdict, control comparison, registration date, forward-walk score-to-date)
-    plus the `proven_signals` map the inline status badge reads. READ-ONLY — recomputes no proven-ness.
-    Empty/absent ledger ⇒ `{"claims": [], "proven_signals": {}}` (200, never 500)."""
-    return build_evidence_payload(resolve_ledger_path())
+    hypothesis, out-of-sample verdict, control comparison, registration date, forward-walk score-to-date,
+    and the additive iter-41 `expectations` drawdown/dry-spell panel) plus the `proven_signals` map the
+    inline status badge reads. READ-ONLY — recomputes no proven-ness; the snapshot DB is read-only here
+    too (`compute_drawdown_expectations` is a pure read-compose). Empty/absent ledger ⇒
+    `{"claims": [], "proven_signals": {}}` (200, never 500)."""
+    return build_evidence_payload(resolve_ledger_path(), session=session, config=get_config())
diff --git a/apps/backend/app/config.py b/apps/backend/app/config.py
index 17941cf..a917a93 100644
--- a/apps/backend/app/config.py
+++ b/apps/backend/app/config.py
@@ -722,7 +722,18 @@ class WalkForwardCfg(BaseModel):
     `horizons` (trading days), the `min_sample` honesty threshold, the default served `horizon`, the
     `control_group` block, and the `attribution` block (J-19) — so no walk-forward literal lives in calc
     code (anti-goal: No magic numbers). Promoted from the iter-1 scaffolded passthrough to a typed
-    section."""
+    section.
+
+    iter-41 (J-25) ADDITIVE keys, consumed by `app.engine.forward_testing.compute_drawdown_expectations`
+    (the `/evidence` phase-conditional drawdown/dry-spell expectations panel):
+      - `underwater_horizons` — the forward horizon(s) the expectations panel is willing to report the
+        underwater-duration / time-to-recover measures for (a claim whose own horizon is outside this list
+        yields no expectations — an honest scope gate, mirroring how `horizons` gates which horizons the
+        engine serves at all). Every element must be positive.
+      - `streak_min_n` — the loss-streak honesty floor: a phase's longest-losing-streak cell needs at least
+        this many WALK-FORWARD-CADENCE dates (not raw per-observation n, which `min_sample` already floors)
+        before it is shown as a real value rather than "insufficient (n=…)". Distinct from `min_sample`
+        because cadence dates are far fewer than per-observation rows."""
 
     model_config = ConfigDict(extra="allow")
     history_years: int
@@ -732,6 +743,8 @@ class WalkForwardCfg(BaseModel):
     default_horizon: int
     control_group: ControlGroupCfg
     attribution: AttributionCfg
+    underwater_horizons: list[int] = Field(min_length=1)
+    streak_min_n: int
 
     @model_validator(mode="after")
     def _validate(self) -> "WalkForwardCfg":
@@ -746,6 +759,10 @@ class WalkForwardCfg(BaseModel):
                 f"walk_forward.default_horizon ({self.default_horizon}) must be one of "
                 f"walk_forward.horizons ({self.horizons})"
             )
+        if any(h <= 0 for h in self.underwater_horizons):
+            raise ValueError("walk_forward.underwater_horizons must all be positive")
+        if self.streak_min_n <= 0:
+            raise ValueError("walk_forward.streak_min_n must be positive")
         return self
 
 
diff --git a/apps/backend/app/db.py b/apps/backend/app/db.py
index 7435b15..31aea2e 100644
--- a/apps/backend/app/db.py
+++ b/apps/backend/app/db.py
@@ -121,6 +121,14 @@ _ADDITIVE_COLUMNS: tuple[tuple[str, str, str], ...] = (
     # or rewrites data; existing forward_returns rows read NULL until the next confirm-gated rebuild
     # repopulates them (the J-85 rebuild is the create-once path that recomputes forward returns).
     ("forward_returns", "max_drawdown", "ALTER TABLE forward_returns ADD COLUMN max_drawdown FLOAT"),
+    # iter-41 (J-25): the two append-only "dry spell" columns on forward_returns — days below the running
+    # high-water mark, and days from the max-drawdown trough back to the entry level (<= 0 case handled by
+    # NULL, never a fabricated sentinel). NULLABLE INTEGER (matches `Optional[int] = Field(default=None)` —
+    # a fresh DB carries them from the model; an existing live DB gains them in place so a non-fresh read of
+    # /api/evidence does not 500). Existing forward_returns rows read NULL until the next confirm-gated
+    # rebuild repopulates them (mirrors the max_drawdown / J-86 precedent directly above).
+    ("forward_returns", "underwater_days", "ALTER TABLE forward_returns ADD COLUMN underwater_days INTEGER"),
+    ("forward_returns", "time_to_recover_days", "ALTER TABLE forward_returns ADD COLUMN time_to_recover_days INTEGER"),
 )
 
 
diff --git a/apps/backend/app/engine/evidence.py b/apps/backend/app/engine/evidence.py
index 629f63c..08093e1 100644
--- a/apps/backend/app/engine/evidence.py
+++ b/apps/backend/app/engine/evidence.py
@@ -34,8 +34,11 @@ from __future__ import annotations
 
 import os
 from pathlib import Path
+from typing import Optional
 
-from app.config import REPO_ROOT, get_config
+from sqlmodel import Session
+
+from app.config import REPO_ROOT, Config, get_config
 from app.engine.ledger import FORWARD_WALK_TYPE, read_entries
 from app.engine.referee import STATUS_PASS
 
@@ -107,7 +110,12 @@ def _claim_row(entry: dict) -> dict:
     }
 
 
-def build_evidence_payload(ledger_path: str) -> dict:
+def build_evidence_payload(
+    ledger_path: str,
+    *,
+    session: Optional[Session] = None,
+    config: Optional[Config] = None,
+) -> dict:
     """Project the certified-claims ledger at `ledger_path` into the read-only `/api/evidence` payload.
 
       - `claims`: every ORIGINAL claim row, read verbatim. Forward-walk MONITORING records
@@ -116,13 +124,35 @@ def build_evidence_payload(ledger_path: str) -> dict:
         AND that NAME a `signal`. A signal absent from this map is, by definition, "Not yet proven".
 
     A missing/empty ledger ⇒ `{"claims": [], "proven_signals": {}}`. RECOMPUTES NOTHING — every verdict
-    field is re-displayed exactly as the referee wrote it."""
+    field is re-displayed exactly as the referee wrote it.
+
+    `session` / `config` (iter-41, J-25) are OPTIONAL keyword-only params, default `None` — EVERY existing
+    call site (~13, incl. the frozen-golden `test_canonical_ledger_frozen_golden`) calls this with ONE
+    positional `ledger_path` arg and MUST stay green unedited. When `session` is `None` (the default), NO
+    `expectations` key is attached to any row — the row dict is BYTE-IDENTICAL to before this iteration.
+    Only when `session` is provided (the real `/evidence` route) does each claim additionally carry the
+    phase-conditional drawdown/dry-spell `expectations` payload from
+    `app.engine.forward_testing.compute_drawdown_expectations` (an honestly-absent key when that returns
+    `None` — an unresolvable cohort or a zero-observation cohort — never a crash, never a fabricated
+    panel)."""
     claims: list[dict] = []
     proven_signals: dict[str, dict] = {}
     for entry in read_entries(ledger_path):
         if not isinstance(entry, dict) or entry.get("type") == FORWARD_WALK_TYPE:
             continue
         row = _claim_row(entry)
+        if session is not None:
+            # lazy import — app.engine.forward_testing sits BELOW this module in the dependency graph
+            # (this module never imported it before), so a module-level import is safe here; kept lazy
+            # anyway so the session-less (majority of existing) call sites pay no import cost. The CACHED
+            # entry point (not the pure `compute_drawdown_expectations`) — /api/evidence renders EVERY
+            # claim's panel on one page load, so an uncached per-claim cohort resolution multiplies the
+            # J-15 latency budget by the claim count (see the cache's own docstring for the measurement).
+            from app.engine.forward_testing import compute_drawdown_expectations_cached
+
+            expectations = compute_drawdown_expectations_cached(session, row["claim"], config)
+            if expectations is not None:
+                row["expectations"] = expectations
         claims.append(row)
         signal = row["signal"]
         if row["proven"] and signal:
diff --git a/apps/backend/app/engine/forward_testing.py b/apps/backend/app/engine/forward_testing.py
index eed9123..043c693 100644
--- a/apps/backend/app/engine/forward_testing.py
+++ b/apps/backend/app/engine/forward_testing.py
@@ -33,10 +33,11 @@ benchmark symbols) comes from config — no walk-forward literal lives here (ant
 """
 from __future__ import annotations
 
+import json
 import random
 from calendar import monthrange
 from collections import defaultdict
-from datetime import date as date_cls, timedelta
+from datetime import date as date_cls, datetime, timedelta, timezone
 from statistics import mean, median, stdev
 from typing import Optional, Union
 
@@ -48,7 +49,7 @@ from app.config import Config, get_config
 from app.engine.prices import bars_after, bars_asof, close_on, latest_data_date
 from app.engine.scanner import run_scan
 from app.engine.setups import ALL_STATUSES
-from app.models import ForwardReturn, ScannerResult, ScannerRun
+from app.models import EventStudyCache, ForwardReturn, ScannerResult, ScannerRun
 
 # The honest caveat carried on every payload (anti-goal: Honest limitations surfaced). iter-18: the
 # basis now spans ~30 years (1996 -> present, per-name real listing depth) over the broadened
@@ -216,6 +217,68 @@ def max_drawdown(bars_after_list: list, entry_close: Optional[float], horizon: i
     return min(drawdowns)
 
 
+def underwater_days(bars_after_list: list, entry_close: Optional[float], horizon: int) -> Optional[int]:
+    """iter-41 (J-25): the count of the FIRST `horizon` post-snapshot bars (date > D, from `bars_after`)
+    whose CLOSE sits below the RUNNING high-water mark — the SAME running-peak convention `max_drawdown`
+    uses (seeded at the as-of-D `entry_close`; a bar that prints a new HIGH raises the peak for THAT
+    bar's own close-check too, mirroring `max_drawdown`'s bar-by-bar order of operations exactly: the
+    peak is updated with `bar.high` BEFORE the bar's own close is compared to it). A bar that closes
+    exactly AT its own freshly-raised peak (`close == running_peak`) is NOT counted underwater.
+
+    Shares the EXACT no-lookahead NA gate as `forward_return`/`max_drawdown`: returns None (NA) — NEVER
+    a fabricated 0 — when `entry_close` is missing or zero, or when fewer than `horizon` post-snapshot
+    bars exist. Only the first `horizon` post-bars matter, so the result is unchanged when later bars
+    are removed (the keystone no-lookahead-of-the-future-tail property)."""
+    if entry_close is None or entry_close == 0:
+        return None
+    if len(bars_after_list) < horizon:
+        return None
+    window = bars_after_list[:horizon]
+    running_peak = entry_close
+    count = 0
+    for bar in window:
+        if bar.high > running_peak:
+            running_peak = bar.high
+        if bar.close < running_peak:
+            count += 1
+    return count
+
+
+def time_to_recover_days(bars_after_list: list, entry_close: Optional[float], horizon: int) -> Optional[int]:
+    """iter-41 (J-25): the number of bars from the max-drawdown TROUGH (the SAME running-peak trough
+    `max_drawdown` identifies as the worst peak-to-trough drop, over the FIRST `horizon` post-snapshot
+    bars) until the close FIRST returns to/above the entry level (`close >= entry_close`), counted
+    within the SAME `horizon`-bar window. 0 when the trough bar's own close already sits at/above the
+    entry level. None (NA — never a fabricated horizon-sentinel) when the close never recovers to the
+    entry level within the window, or when the shared NA gate applies.
+
+    Internally re-derives the SAME running-peak per-bar drawdown series `max_drawdown` computes, ONLY to
+    locate the trough's bar INDEX (which `max_drawdown` does not expose) — it does not re-implement or
+    alter the canonical `max_drawdown` function itself (never forked; `test_time_to_recover_days_
+    counts_bars_from_trough_to_entry_reclaim` pins the located trough's value against `max_drawdown`'s
+    own return value for the SAME inputs).
+
+    Shares the EXACT no-lookahead NA gate as `forward_return`/`max_drawdown`. Only the first `horizon`
+    post-bars matter, so the result is unchanged when later bars are removed (the keystone no-lookahead-
+    of-the-future-tail property)."""
+    if entry_close is None or entry_close == 0:
+        return None
+    if len(bars_after_list) < horizon:
+        return None
+    window = bars_after_list[:horizon]
+    running_peak = entry_close
+    drawdowns: list[float] = []
+    for bar in window:
+        if bar.high > running_peak:
+            running_peak = bar.high
+        drawdowns.append(bar.low / running_peak - 1)
+    trough_index = min(range(len(drawdowns)), key=lambda i: drawdowns[i])  # first index at the worst drop
+    for offset, bar in enumerate(window[trough_index:]):
+        if bar.close >= entry_close:
+            return offset
+    return None  # never recovered within the horizon window
+
+
 # --------------------------------------------------------------------------------------------------
 # Walk-forward as-of date set (cadence intersected with real seed trading days)
 # --------------------------------------------------------------------------------------------------
@@ -327,6 +390,12 @@ def _insert_run_forward_returns(
             # once here beside mae/mfe via the pure helper that shares the EXACT NA gate — so a row's
             # max_drawdown is non-None iff realized_return is (never a fabricated 0 for a short window).
             mdd = max_drawdown(post_bars, entry_close, horizon)
+            # iter-41 (J-25): the two "dry spell" columns over the SAME post_bars/entry_close/horizon
+            # already in hand — zero extra bar reads. underwater_days shares the EXACT NA gate as
+            # max_drawdown (non-None iff realized is); time_to_recover_days is additionally None when the
+            # close never reclaims the entry level within the window (never a fabricated sentinel).
+            uw_days = underwater_days(post_bars, entry_close, horizon)
+            ttr_days = time_to_recover_days(post_bars, entry_close, horizon)
             session.add(
                 ForwardReturn(
                     run_id=run.id,
@@ -339,6 +408,8 @@ def _insert_run_forward_returns(
                     mae=excursions["mae"] if excursions else None,
                     mfe=excursions["mfe"] if excursions else None,
                     max_drawdown=mdd,
+                    underwater_days=uw_days,
+                    time_to_recover_days=ttr_days,
                 )
             )
             existing.add((run.id, symbol, horizon))
@@ -987,3 +1058,325 @@ def compute_run_scorecard(session: Session, run: ScannerRun, config: Optional[Co
         "survivorship_bias": SURVIVORSHIP_BIAS_LABEL,
         "scorecard": {"by_horizon": by_horizon},
     }
+
+
+# --------------------------------------------------------------------------------------------------
+# Drawdown & dry-spell expectations (iter-41, J-25) — phase-conditional historical distributions over
+# ONE certified claim's cohort, additively served on GET /api/evidence. Pure read-compose: resolves the
+# cohort via the SAME `app.engine.samples.compute_samples` selectors the Research labs publish (no
+# second cohort resolver), reads each observation's STORED `max_drawdown` / `underwater_days` /
+# `time_to_recover_days` VERBATIM off `ForwardReturn` (recomputes no existing canonical value), and joins
+# to the CAUSAL phase-at-entry via `app.engine.market_phase.phase_context_by_date` (the SAME causal
+# timeline `compute_market_phase` reads — never a smoothed/retrospective one).
+#
+# `app.engine.samples` imports `SURVIVORSHIP_BIAS_LABEL` FROM this module, and `app.engine.market_phase`
+# imports `app.engine.research` which ALSO imports FROM this module — so a MODULE-LEVEL import of either
+# back into this file would be circular. Both are LAZY-imported inside `compute_drawdown_expectations`,
+# mirroring `app.engine.research`'s own established "lazy import (avoids a market_phase<->research
+# cycle)" pattern for the identical reason.
+# --------------------------------------------------------------------------------------------------
+
+# The ledger claim's own selector-field name -> the `compute_samples` kwarg name (identity when
+# unlisted). Mirrors `app.mcp.tools._CLAIM_SELECTOR_KEYS` / `drill_samples`'s translation — the SAME
+# vocabulary `/api/research/samples` accepts and `app.mcp.tools.assemble_claim_observations` (the
+# referee's own cohort assembly) already applies. A pure key rename/repackage: the cohort MEMBERSHIP
+# RULE stays 100% inside `compute_samples` — this decides nothing about who is IN a cohort, only which
+# keyword each already-stored selector value arrives under. Kept as a small local mirror (rather than an
+# import from `app.mcp.tools`) because `app.mcp.tools` sits ABOVE this module in the dependency graph
+# (it imports FROM `app.engine.samples`/`research`, which import FROM this module) — importing it here
+# would invert that layering.
+_CLAIM_SELECTOR_KEYS = (
+    "factor", "slice_kind", "decile", "regime", "sector", "condition", "cohort", "single_index",
+    "subject", "view", "setup", "pattern", "phase", "dimension", "family", "velocity_sign",
+    "regime_decile", "severity_decile", "factor_decile",
+)
+_CLAIM_KWARG_RENAMES = {"factor": "factor_key", "cohort": "cohort_kind", "subject": "subject_key"}
+
+# The walk-forward-cadence method note (B-205 trap): a loss streak counted per-observation (per ticker
+# per date) would double-count multiple names sharing one snapshot date, or overlapping-horizon returns,
+# as if they were independent consecutive "days". Collapsing to one mean-return-per-date point first
+# avoids both.
+LOSS_STREAK_METHOD_NOTE = (
+    "Longest losing streak is counted at the walk-forward cadence (one point per snapshot date — the "
+    "cohort's mean forward return that date), not per name per day, so multiple names sharing a "
+    "snapshot date are never double-counted as separate consecutive losses."
+)
+
+
+def _claim_samples_kwargs(claim: dict) -> Optional[dict]:
+    """Translate a ledger claim's cohort selectors into `compute_samples` kwargs (module note above).
+    Returns None for a malformed `condition` leg (never raises — an honest unresolvable cohort)."""
+    kwargs: dict = {}
+    for key in _CLAIM_SELECTOR_KEYS:
+        if key not in claim:
+            continue
+        if key == "condition":
+            parsed = []
+            for spec in claim["condition"]:
+                parts = spec.split(":")
+                if len(parts) != 3:
+                    return None
+                parsed.append({"factor": parts[0], "side": parts[1], "quantile": parts[2]})
+            kwargs["conditions"] = parsed
+            continue
+        kwargs[_CLAIM_KWARG_RENAMES.get(key, key)] = claim[key]
+    return kwargs
+
+
+def _median_p90(values: list[float]) -> dict:
+    """{median, p90} of `values` via linear-interpolation percentiles — the SAME 'standard definition'
+    `app.engine.indicators._percentile` uses for the risk-budget gap profile (J-24), mirrored locally
+    (a two-line formula) rather than imported cross-domain."""
+    ordered = sorted(values)
+    n = len(ordered)
+
+    def _pct(p: float) -> float:
+        if n == 1:
+            return ordered[0]
+        rank = p * (n - 1)
+        lower = int(rank)
+        upper = min(lower + 1, n - 1)
+        frac = rank - lower
+        return ordered[lower] + (ordered[upper] - ordered[lower]) * frac
+
+    return {"median": _pct(0.5), "p90": _pct(0.9)}
+
+
+def _distribution_cell(values: list[float], floor: int) -> dict:
+    """One `{median, p90, n, insufficient}` cell — an honest 'insufficient' (no median/p90, never a
+    fabricated distribution) below `floor`."""
+    n = len(values)
+    if n < floor:
+        return {"median": None, "p90": None, "n": n, "insufficient": True}
+    stats = _median_p90(values)
+    return {"median": stats["median"], "p90": stats["p90"], "n": n, "insufficient": False}
+
+
+def _longest_negative_streak(ordered_dated_returns: list[tuple]) -> int:
+    """The longest run of consecutive entries in `ordered_dated_returns` (ALREADY sorted ascending by
+    date) whose return is < 0. Pure sequence scan; 0 when no entry is negative or the list is empty."""
+    best = 0
+    current = 0
+    for _date, ret in ordered_dated_returns:
+        if ret < 0:
+            current += 1
+            best = max(best, current)
+        else:
+            current = 0
+    return best
+
+
+def _loss_streak_cell(dated_returns: list[tuple], floor: int) -> dict:
+    """One `{value, n, insufficient}` loss-streak cell at the WALK-FORWARD CADENCE (the B-205 trap):
+    `dated_returns` (`[(snapshot_date_iso, forward_return), ...]`, any order) is first collapsed to ONE
+    MEAN cohort return per distinct date (so multiple tickers sharing a snapshot date contribute a SINGLE
+    data point, never inflating the streak), sorted chronologically, then the longest run of consecutive
+    NEGATIVE dates is counted (`_longest_negative_streak`). `n` is the number of distinct cadence dates
+    examined — the honesty floor for THIS measure is `streak_min_n`, deliberately smaller than the
+    per-observation `min_sample` floor the other three measures use."""
+    by_date: dict[str, list[float]] = defaultdict(list)
+    for d, ret in dated_returns:
+        by_date[d].append(ret)
+    ordered = sorted((d, mean(rets)) for d, rets in by_date.items())
+    n = len(ordered)
+    if n < floor:
+        return {"value": None, "n": n, "insufficient": True}
+    return {"value": _longest_negative_streak(ordered), "n": n, "insufficient": False}
+
+
+def compute_drawdown_expectations(
+    session: Session, claim: dict, config: Optional[Config] = None
+) -> Optional[dict]:
+    """iter-41 (J-25) — the SINGLE canonical phase-conditional drawdown & dry-spell expectations payload
+    for ONE certified-claims ledger `claim` (Data Contract value, additive on `GET /api/evidence`). For
+    the claim's own cohort (resolved via the SAME `compute_samples` selectors the Research labs publish)
+    at the claim's own `horizon`, groups the STORED `max_drawdown` / `underwater_days` /
+    `time_to_recover_days` (read VERBATIM — recomputes nothing) by the CAUSAL phase-at-entry
+    (`phase_context_by_date`, keyed by the observation's own snapshot date), and emits per configured
+    phase label a `{median, p90, n}` cell for each of the three distribution measures plus a
+    walk-forward-cadence longest-losing-streak cell. EVERY configured `market_phase.labels` value is
+    emitted (padded, even at n=0) so a cohort that never saw a phase still discloses that honestly.
+
+    Returns None — the caller (`build_evidence_payload`) then omits the `expectations` key entirely, the
+    honest 'no panel' signal — when: the claim's `horizon` is missing or outside the configured
+    `walk_forward.underwater_horizons` scope, the cohort selectors are malformed/unresolvable (an unknown
+    kind, an out-of-range decile, a malformed combination `condition`, …), or the cohort resolves to zero
+    observations with BOTH a snapshot date and a realized forward return. Never raises into the caller —
+    `GET /api/evidence` always stays 200."""
+    cfg = config or get_config()
+    wf = cfg.walk_forward
+    horizon = claim.get("horizon")
+    if horizon not in wf.underwater_horizons:
+        return None
+    kwargs = _claim_samples_kwargs(claim)
+    if kwargs is None:
+        return None
+
+    # lazy imports — both `samples` and `market_phase` import FROM this module at load time (see the
+    # module note above), so a module-level import of either back into this file would be circular.
+    from app.engine.market_phase import phase_context_by_date
+    from app.engine.samples import compute_samples
+
+    try:
+        samples = compute_samples(
+            session, kind=claim.get("kind"), horizon=horizon, config=cfg, as_of=None, **kwargs
+        )
+    except ValueError:
+        return None  # an unknown kind / unresolvable / malformed cohort selector -> honest empty
+
+    rows = [r for r in samples["rows"] if r.get("snapshot_date") and r.get("forward_return") is not None]
+    if not rows:
+        return None
+
+    # ONE additive read of the SAME (ticker, horizon, snapshot-date) rows `compute_samples` already
+    # resolved — the cohort MEMBERSHIP is unchanged; this only fetches the three stored columns
+    # `compute_samples`'s own row shape does not carry. `ForwardReturn.asof_date` is stored verbatim on
+    # each row (no ScannerRun join needed) and is the SAME date `_run_date_map` derives `snapshot_date`
+    # from, so the (symbol, asof_date-ISO) key matches every `compute_samples` row exactly.
+    tickers = sorted({r["ticker"] for r in rows})
+    fr_stmt = select(
+        ForwardReturn.symbol, ForwardReturn.asof_date, ForwardReturn.max_drawdown,
+        ForwardReturn.underwater_days, ForwardReturn.time_to_recover_days,
+    ).where(ForwardReturn.horizon == horizon, ForwardReturn.symbol.in_(tickers))
+    stored_by_key = {
+        (symbol, asof_date.isoformat()): (mdd, uw, ttr)
+        for symbol, asof_date, mdd, uw, ttr in session.exec(fr_stmt).all()
+    }
+
+    # the SAME causal timeline `compute_market_phase` reads (all-history — the expectations panel is
+    # descriptive over the claim's WHOLE tested cohort, not scoped to a single "today" as-of).
+    phases = phase_context_by_date(session, as_of=None, config=cfg)
+
+    by_phase_mdd: dict[str, list[float]] = defaultdict(list)
+    by_phase_uw: dict[str, list[float]] = defaultdict(list)
+    by_phase_ttr: dict[str, list[float]] = defaultdict(list)
+    by_phase_returns: dict[str, list[tuple]] = defaultdict(list)
+
+    for row in rows:
+        date_iso = row["snapshot_date"]
+        ctx = phases.get(date_iso)
+        if ctx is None:
+            continue  # no causal phase classification for this date (short benchmark window) -> excluded
+        phase = ctx["phase"]
+        by_phase_returns[phase].append((date_iso, row["forward_return"]))
+        stored = stored_by_key.get((row["ticker"], date_iso))
+        if stored is None:
+            continue
+        mdd, uw, ttr = stored
+        if mdd is not None:
+            by_phase_mdd[phase].append(mdd)
+        if uw is not None:
+            by_phase_uw[phase].append(uw)
+        if ttr is not None:
+            by_phase_ttr[phase].append(ttr)
+
+    by_phase = [
+        {
+            "phase": phase,
+            "n": len(by_phase_returns.get(phase, [])),
+            "max_drawdown": _distribution_cell(by_phase_mdd.get(phase, []), wf.min_sample),
+            "underwater_days": _distribution_cell(by_phase_uw.get(phase, []), wf.min_sample),
+            "time_to_recover_days": _distribution_cell(by_phase_ttr.get(phase, []), wf.min_sample),
+            "loss_streak": _loss_streak_cell(by_phase_returns.get(phase, []), wf.streak_min_n),
+        }
+        for phase in cfg.market_phase.labels
+    ]
+
+    return {
+        "horizon": horizon,
+        "min_sample": wf.min_sample,
+        "streak_min_n": wf.streak_min_n,
+        "survivorship_bias": SURVIVORSHIP_BIAS_LABEL,
+        "method_note": LOSS_STREAK_METHOD_NOTE,
+        "by_phase": by_phase,
+    }
+
+
+# --- cached serving (J-72 performance layer) — REQUIRED because /api/evidence calls this ONCE PER CLAIM ---
+# `compute_drawdown_expectations` resolves a full research cohort (`compute_samples`, the SAME cost a
+# Factor/Combination/Event-study lab request pays), which costs several hundred ms to ~1s+ on the deep
+# 30-year/590-symbol basis. `/api/evidence` renders EVERY claim's panel on ONE page load (7 claims today),
+# so an uncached call multiplies that cost by the claim count — measured ~9.4s total for 7 claims,
+# regressing the J-15 latency budget by ~3x. Every OTHER research-derived aggregate in this codebase (the
+# Factor/Combination/Event-study/Regime/Phase-Severity/Regime-Phase-Factor labs) already solves this
+# EXACT problem the SAME way: serve from the shared `EventStudyCache` table (J-72), keyed by
+# `(subject, view, asof_key, dataset_version, horizon)`, computed once and refreshed automatically when
+# the dataset changes. This reuses that SAME table (a namespaced `subject` prevents any cross-feature
+# collision) rather than adding a parallel cache mechanism.
+_DD_EXPECTATIONS_VIEW = "drawdown_expectations"  # the EventStudyCache `view` slot reserved for this feature
+_DD_EXPECTATIONS_ASOF_KEY = "all"  # this aggregation is always all-history (mirrors research._ASOF_ALL)
+
+
+def _drawdown_expectations_cache_subject(claim: dict) -> str:
+    """A STABLE, BOUNDED `EventStudyCache.subject` for ONE claim: a namespaced SHA-256 of its canonical
+    (sorted-key) JSON, so distinct claims never collide, identical claims always hit the SAME row, and an
+    arbitrarily long combination `condition` list never risks a column-length surprise. The `dd_exp:`
+    namespace prefix guarantees no collision with another feature's subject on this SHARED cache table."""
+    import hashlib
+
+    canonical = json.dumps(claim, sort_keys=True, default=str)
+    return f"dd_exp:{hashlib.sha256(canonical.encode()).hexdigest()}"
+
+
+def compute_drawdown_expectations_cached(
+    session: Session, claim: dict, config: Optional[Config] = None
+) -> Optional[dict]:
+    """Serve `compute_drawdown_expectations` from the shared J-72 `EventStudyCache` (a pure performance
+    layer — No recompute in the read path): a HIT for the current `(subject, view, asof_key,
+    dataset_version, horizon)` key deserializes and returns the stored payload; a MISS computes it ONCE via
+    `compute_drawdown_expectations`, persists it (a `None` result is cached too — an honestly-unresolvable
+    cohort is still a stable answer for this dataset version, and caching it avoids re-paying the SAME
+    expensive miss every request), prunes stale rows for this claim, and returns it. The returned payload
+    is BYTE-IDENTICAL to a fresh `compute_drawdown_expectations(...)` call. `GET /api/evidence` calls THIS
+    function, never the uncached one directly."""
+    cfg = config or get_config()
+    horizon = claim.get("horizon")
+    if horizon not in cfg.walk_forward.underwater_horizons:
+        return None  # the same scope gate compute_drawdown_expectations applies — skip the DB round-trip
+
+    # lazy import — app.engine.research imports FROM this module, so a module-level import back would be
+    # circular (mirrors this file's other lazy imports of market_phase/samples, immediately above).
+    from app.engine.research import _dataset_version
... [diff_bound] apps/backend/app/engine/forward_testing.py: 43 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/app/models.py b/apps/backend/app/models.py
index baec1f1..3a19595 100644
--- a/apps/backend/app/models.py
+++ b/apps/backend/app/models.py
@@ -360,7 +360,21 @@ class ForwardReturn(SQLModel, table=True):
     default `None` (backward-compatible; a fresh frozen-seed DB carries it from the start; an existing
     live DB gains it via the `db._ADDITIVE_COLUMNS` ALTER). Read VERBATIM by the read path
     (`/api/stocks`, `/api/stocks/{ticker}`, `/api/themes`, `/api/sectors`) and aggregated read-only by
-    Backtest + the Research event study — never recomputed when served."""
+    Backtest + the Research event study — never recomputed when served.
+
+    `underwater_days` / `time_to_recover_days` (iter-41, J-25) are the NEW append-only "dry spell" columns —
+    the count of the FIRST `horizon` post-snapshot bars (date > D, via `bars_after`) whose close sits below
+    the RUNNING high-water mark (seeded at the as-of-D `entry_close`, the SAME running-peak convention
+    `max_drawdown` uses), and the number of bars from the max-drawdown trough until the close first returns
+    to the entry level within the horizon (NA — never a fabricated horizon-sentinel — if it never recovers
+    in-window). Both are computed ONCE in the SAME `_insert_run_forward_returns` INSERT path via the pure
+    `underwater_days` / `time_to_recover_days` helpers, sharing the EXACT no-lookahead NA gate as
+    `forward_return`/`max_drawdown` (`underwater_days` is non-None iff `realized_return` exists;
+    `time_to_recover_days` is additionally None within an existing row when no recovery occurs in-window —
+    never a fabricated value). Forward-side only — no snapshot row is ever UPDATEd. `Optional[int]`, default
+    `None` (backward-compatible; a fresh frozen-seed DB carries them from the start; an existing live DB
+    gains them via the `db._ADDITIVE_COLUMNS` ALTER). Read VERBATIM by
+    `app.engine.forward_testing.compute_drawdown_expectations` — never recomputed when served."""
 
     __tablename__ = "forward_returns"
     # iter-24 fast-platform item C: the explicit `ix_forward_returns_run_symbol` index that used to live
@@ -391,6 +405,12 @@ class ForwardReturn(SQLModel, table=True):
     # Computed once with realized_return, same no-lookahead NA gate; None on short history. Read verbatim
     # by the stocks/themes/sectors/detail read path and aggregated read-only by Backtest + Research.
     max_drawdown: Optional[float] = Field(default=None)  # true peak-to-trough drawdown over first h post-bars (<= 0)
+    # iter-41 (J-25) append-only "dry spell" columns — days below the running high-water mark, and days from
+    # the max-drawdown trough back to the entry level (None if never recovered in-window). Computed once with
+    # realized_return, same no-lookahead NA gate; None on short history. Read verbatim by
+    # compute_drawdown_expectations (the /evidence expectations panel) — never recomputed elsewhere.
+    underwater_days: Optional[int] = Field(default=None)  # bars below the running high-water mark, first h post-bars
+    time_to_recover_days: Optional[int] = Field(default=None)  # bars from the MDD trough to entry-level recovery (NA if none)
 
 
 # --- iter-20 event-study derived-aggregate cache (J-72 — a PERFORMANCE cache, not a snapshot) -----
diff --git a/apps/backend/tests/test_config.py b/apps/backend/tests/test_config.py
index 71e3526..e55e38d 100644
--- a/apps/backend/tests/test_config.py
+++ b/apps/backend/tests/test_config.py
@@ -163,6 +163,8 @@ MINIMAL_VALID = {
         "history_years": 2, "asof_cadence": "quarterly", "horizons": [1, 5, 10, 20, 60],
         "min_sample": 30, "default_horizon": 20,
         "control_group": {"seed": 20240601, "top_n": 20, "peers_per_sector": 5},
+        # iter-41 (J-25): required drawdown-expectations tunables (the /evidence panel).
+        "underwater_horizons": [1, 5, 10, 20, 60], "streak_min_n": 10,
         "attribution": {
             "top_contributors_k": 5,
             "rank_bands": [
diff --git a/apps/backend/tests/test_config_engine.py b/apps/backend/tests/test_config_engine.py
index 10e1b10..a37ed45 100644
--- a/apps/backend/tests/test_config_engine.py
+++ b/apps/backend/tests/test_config_engine.py
@@ -159,6 +159,8 @@ VALID = {
         "history_years": 2, "asof_cadence": "quarterly", "horizons": [1, 5, 10, 20, 60],
         "min_sample": 30, "default_horizon": 20,
         "control_group": {"seed": 20240601, "top_n": 20, "peers_per_sector": 5},
+        # iter-41 (J-25): required drawdown-expectations tunables (the /evidence panel).
+        "underwater_horizons": [1, 5, 10, 20, 60], "streak_min_n": 10,
         "attribution": {
             "top_contributors_k": 5,
             "rank_bands": [
diff --git a/apps/backend/tests/test_db.py b/apps/backend/tests/test_db.py
index 3f5e26f..562840c 100644
--- a/apps/backend/tests/test_db.py
+++ b/apps/backend/tests/test_db.py
@@ -222,6 +222,53 @@ def test_additive_migration_backfills_max_drawdown_on_existing_forward_returns(t
     create_db_and_tables(make_engine(f"sqlite:///{db}"))  # idempotent — a second run must not error
 
 
+def test_additive_migration_backfills_dry_spell_columns_on_existing_forward_returns(tmp_path):
+    """iter-41 (J-25) REGRESSION: the new `forward_returns.underwater_days` / `.time_to_recover_days`
+    columns added to the ALREADY-CREATED forward_returns table must be registered in `_ADDITIVE_COLUMNS`,
+    else an existing offline-first DB never gains them and `GET /api/evidence` 500s with `no such column`.
+    Build a LEGACY forward_returns table (with max_drawdown but WITHOUT the two new columns), then assert
+    create_db_and_tables backfills both in place (nullable, idempotent), and an existing row reads NULL
+    (honest NA — never a fabricated 0)."""
+    from sqlalchemy import inspect, text
+
+    from app.db import _ADDITIVE_COLUMNS, create_db_and_tables, make_engine
+
+    registered = {(t, c) for t, c, _ddl in _ADDITIVE_COLUMNS}
+    assert ("forward_returns", "underwater_days") in registered
+    assert ("forward_returns", "time_to_recover_days") in registered
+
+    db = tmp_path / "legacy_iter41.db"
+    engine = make_engine(f"sqlite:///{db}")
+    with engine.begin() as conn:
+        # LEGACY forward_returns WITH max_drawdown (iter-27) but WITHOUT the iter-41 dry-spell columns.
+        conn.execute(text(
+            "CREATE TABLE forward_returns ("
+            "id INTEGER PRIMARY KEY, run_id INTEGER, symbol TEXT, horizon INTEGER, asof_date DATE, "
+            "entry_close FLOAT, measured_date DATE, realized_return FLOAT, mae FLOAT, mfe FLOAT, "
+            "max_drawdown FLOAT)"
+        ))
+        conn.execute(text(
+            "INSERT INTO forward_returns (run_id, symbol, horizon, asof_date, entry_close, measured_date, "
+            "realized_return, mae, mfe, max_drawdown) VALUES "
+            "(1, 'AAA', 5, '2024-01-05', 100.0, '2024-01-12', 0.05, -0.02, 0.07, -0.03)"
+        ))
+    before = {c["name"] for c in inspect(engine).get_columns("forward_returns")}
+    assert "underwater_days" not in before
+    assert "time_to_recover_days" not in before
+
+    create_db_and_tables(engine)  # applies the additive backfill
+
+    after = {c["name"] for c in inspect(make_engine(f"sqlite:///{db}")).get_columns("forward_returns")}
+    assert "underwater_days" in after
+    assert "time_to_recover_days" in after
+    with engine.begin() as conn:
+        row = conn.execute(text(
+            "SELECT underwater_days, time_to_recover_days FROM forward_returns"
+        )).one()
+        assert row[0] is None and row[1] is None  # honest NA on the pre-existing row
+    create_db_and_tables(make_engine(f"sqlite:///{db}"))  # idempotent — a second run must not error
+
+
 def test_every_model_column_on_existing_table_is_covered_by_additive_registry(tmp_path):
     """GUARD against the iter-29 class of bug: for each table that already exists in an OLDER DB, every
     column the current SQLModel defines must EITHER be creatable on a pre-existing table via an
diff --git a/apps/backend/tests/test_evidence.py b/apps/backend/tests/test_evidence.py
index d313a6f..512e6e5 100644
--- a/apps/backend/tests/test_evidence.py
+++ b/apps/backend/tests/test_evidence.py
@@ -15,9 +15,15 @@ fail-safe contract:
 """
 from __future__ import annotations
 
+from datetime import date, datetime, timedelta, timezone
 from pathlib import Path
 
-from app.config import REPO_ROOT
+import pytest
+from sqlmodel import Session
+
+import app.engine.market_phase as market_phase
+from app.config import REPO_ROOT, load_config
+from app.db import create_db_and_tables, make_engine
 from app.engine.evidence import (
     LEDGER_PATH_ENV,
     _resolve_signal,
@@ -25,6 +31,7 @@ from app.engine.evidence import (
     resolve_ledger_path,
 )
 from app.engine.ledger import append_entry
+from app.models import ForwardReturn, ScannerResult, ScannerRun
 
 
 def _pass_entry(signal: str | None, factor: str = "leadership_score") -> dict:
@@ -533,6 +540,83 @@ def test_build_payload_excludes_forward_walk_monitoring_records(tmp_path):
     assert list(payload["proven_signals"].keys()) == ["leadership_score"]
 
 
+# ==================================================================================================
+# additive `expectations` field (iter-41, J-25) — session-provided vs. session-omitted paths
+# ==================================================================================================
+@pytest.fixture()
+def evidence_dd_engine(tmp_path, monkeypatch):
+    """A minimal hand-built engine with ONE resolvable leadership_score observation at horizon 20, dated
+    into a monkeypatched 'Expansion' phase — just enough for `compute_drawdown_expectations` (fully unit-
+    tested on its own in test_forward_testing.py) to return a non-None payload for the SAME
+    decile-10/horizon-20 claim shape `_pass_entry` builds above."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'evidence_dd.db'}")
+    create_db_and_tables(engine)
+    d = date(2025, 1, 10)
+    with Session(engine) as session:
+        run = ScannerRun(
+            asof_date=d, created_at=datetime.now(timezone.utc), provider="seed", benchmark="SPY",
+            regime_score=50.0, regime_label="Risk-on", regime_components_json="[]",
+            new_high_low_json="{}", candidate_counts_json="{}",
+        )
+        session.add(run)
+        session.flush()
+        session.add(ScannerResult(
+            run_id=run.id, ticker="AAA", name="AAA", sector="Technology",
+            leadership_score=90.0, leadership_bucket="A",
+            entry_quality_score=50.0, entry_quality_bucket="C",
+            risk_score=50.0, risk_bucket="C",
+            setup_status="Actionable", rank=1, record_json="{}",
+        ))
+        session.add(ForwardReturn(
+            run_id=run.id, symbol="AAA", horizon=20, asof_date=d, entry_close=100.0,
+            measured_date=d + timedelta(days=40), realized_return=0.02,
+            max_drawdown=-0.05, underwater_days=3, time_to_recover_days=5,
+        ))
+        session.commit()
+
+    def _fake_ctx(session=None, as_of=None, config=None):
+        return {d.isoformat(): {"phase": "Expansion", "severity": 10.0, "p_bear": 0.05}}
+
+    monkeypatch.setattr(market_phase, "phase_context_by_date", _fake_ctx)
+    return engine
+
+
+def test_build_payload_session_omitted_no_expectations_key(tmp_path):
+    """DEFAULT (session=None, EVERY existing call site's shape): a claim row carries NO `expectations`
+    key at all — not even `None` — the literal 'absent' the DoD requires, proving the ~13 existing
+    positional-only call sites (incl. the frozen-golden test) see a byte-identical row."""
+    ledger = tmp_path / "certified-claims.jsonl"
+    append_entry(str(ledger), _pass_entry("leadership_score"))
+    payload = build_evidence_payload(str(ledger))
+    assert "expectations" not in payload["claims"][0]
+
+
+def test_build_payload_session_provided_attaches_expectations(tmp_path, evidence_dd_engine):
+    """When a session IS provided (the real `/evidence` route), a resolvable claim's row additively
+    carries `expectations` — read straight from `compute_drawdown_expectations`, never a second
+    computation, never a client-visible recompute."""
+    ledger = tmp_path / "certified-claims.jsonl"
+    append_entry(str(ledger), _pass_entry("leadership_score"))  # factor=leadership_score, decile=10, h=20
+    with Session(evidence_dd_engine) as session:
+        payload = build_evidence_payload(str(ledger), session=session, config=load_config())
+    row = payload["claims"][0]
+    assert "expectations" in row
+    assert row["expectations"]["horizon"] == 20
+    exp_phase = next(p for p in row["expectations"]["by_phase"] if p["phase"] == "Expansion")
+    assert exp_phase["n"] == 1
+
+
+def test_build_payload_session_provided_unresolvable_claim_no_expectations_key(tmp_path, evidence_dd_engine):
+    """A session IS provided but the claim's cohort is unresolvable (an unknown factor) — the row still
+    carries NO `expectations` key (graceful, matches the session-omitted case; never a crash, never a
+    fabricated panel)."""
+    ledger = tmp_path / "certified-claims.jsonl"
+    append_entry(str(ledger), _pass_entry("leadership_score", factor="does_not_exist_factor"))
+    with Session(evidence_dd_engine) as session:
+        payload = build_evidence_payload(str(ledger), session=session, config=load_config())
+    assert "expectations" not in payload["claims"][0]
+
+
 def test_resolve_ledger_path_env_override(tmp_path, monkeypatch):
     override = tmp_path / "override-ledger.jsonl"
     monkeypatch.setenv(LEDGER_PATH_ENV, str(override))
diff --git a/apps/backend/tests/test_forward_testing.py b/apps/backend/tests/test_forward_testing.py
index 3ed70d9..51bc5bc 100644
--- a/apps/backend/tests/test_forward_testing.py
+++ b/apps/backend/tests/test_forward_testing.py
@@ -23,20 +23,28 @@ import pytest
 from sqlalchemy import func
 from sqlmodel import Session, select
 
+import app.engine.market_phase as market_phase
 from app.config import load_config
 from app.db import create_db_and_tables, make_engine
 from app.engine.forward_testing import (
+    _claim_samples_kwargs,
+    _drawdown_expectations_cache_subject,
     backfill_forward_returns,
+    compute_drawdown_expectations,
+    compute_drawdown_expectations_cached,
     compute_forward_aggregates,
     forward_excursions,
     forward_return,
     max_drawdown,
+    time_to_recover_days,
+    underwater_days,
     walk_forward_asof_dates,
 )
 from app.engine.prices import bar_cache, bars_after, bars_asof, close_on, latest_data_date
 from app.engine.scanner import run_scan
 from app.models import (
     DailyPrice,
+    EventStudyCache,
     ForwardReturn,
     ScannerResult,
     ScannerRun,
@@ -326,6 +334,86 @@ def test_max_drawdown_within_mae_relationship():
     assert mdd <= ex["mae"] <= 0
 
 
+# ==================================================================================================
+# underwater_days / time_to_recover_days — pure no-lookahead "dry spell" math (iter-41, J-25)
+# ==================================================================================================
+def test_underwater_days_counts_closes_below_running_peak():
+    """The running peak is seeded at entry (mirrors max_drawdown) and raised by each bar's HIGH before
+    that SAME bar's close is checked against it — a bar that closes exactly AT its own fresh peak is not
+    counted underwater; every other bar whose close sits below the running peak is."""
+    # entry 100; bar0 high102/low98/close99 (peak->102, 99<102 underwater);
+    # bar1 high101/low85/close90 (peak stays 102, 90<102 underwater);
+    # bar2 high105/low92/close105 (peak->105, close==peak -> NOT underwater);
+    # bar3 high112/low108/close110 (peak stays 105... wait 112>105 -> peak->112, 110<112 underwater)
+    post = _ex_bars([(102, 98, 99), (101, 85, 90), (105, 92, 105), (112, 108, 110)])
+    assert underwater_days(post, 100.0, 4) == 3  # bar0, bar1, bar3 underwater; bar2 closes at its own peak
+
+
+def test_underwater_days_seeded_at_entry_first_bar_below_entry():
+    """The peak is seeded at entry_close, so a FIRST bar entirely below entry is measured against the
+    entry itself (not fabricated as 'above peak')."""
+    post = _ex_bars([(98, 90, 92)])  # high/low/close all below entry 100 -> peak stays 100, 92<100
+    assert underwater_days(post, 100.0, 1) == 1
+
+
+def test_underwater_days_na_when_fewer_than_h_post_bars_or_no_entry():
+    """Shares the EXACT no-lookahead NA gate as forward_return/max_drawdown: None — never a fabricated
+    0 — when fewer than `horizon` post-bars exist or the entry is missing/zero."""
+    post = _ex_bars([(110, 95, 105), (120, 90, 115)])
+    assert underwater_days(post, 100.0, 3) is None
+    assert underwater_days([], 100.0, 1) is None
+    assert underwater_days(post, None, 1) is None
+    assert underwater_days(post, 0.0, 1) is None
+
+
+def test_underwater_days_unchanged_when_later_bars_removed():
+    """No-lookahead: removing bars dated > d+h does not change the h-day underwater count."""
+    full = _ex_bars([(110, 95, 105), (120, 90, 115), (300, 5, 200), (90, 80, 85)])
+    truncated = _ex_bars([(110, 95, 105), (120, 90, 115)])
+    assert underwater_days(full, 100.0, 2) == underwater_days(truncated, 100.0, 2)
+
+
+def test_time_to_recover_days_counts_bars_from_trough_to_entry_reclaim():
+    """time_to_recover = bars from the max_drawdown TROUGH (the SAME running-peak trough max_drawdown
+    identifies) until close first reaches >= entry_close, within the horizon window."""
+    # entry 100; trough is bar1 (worst peak-to-trough drop) as established by max_drawdown's own math.
+    post = _ex_bars([(102, 98, 99), (101, 85, 90), (95, 88, 93), (105, 92, 104)])
+    mdd = max_drawdown(post, 100.0, 4)
+    assert mdd == pytest.approx(85 / 102 - 1)  # confirms the trough is bar1 (peak 102 by then)
+    # bar1 close=90 (no), bar2 close=93 (no), bar3 close=104 (recovers) -> 2 bars after the trough
+    assert time_to_recover_days(post, 100.0, 4) == 2
+
+
+def test_time_to_recover_days_zero_when_trough_bar_itself_recovers():
+    """0 when the trough bar's OWN close already sits at/above the entry level (never a fabricated
+    positive count for an immediate same-bar reclaim)."""
+    post = _ex_bars([(130, 95, 129)])  # single bar: low 95 is the trough, but close 129 >= entry 100
+    assert time_to_recover_days(post, 100.0, 1) == 0
+
+
+def test_time_to_recover_days_na_when_never_recovers_in_window():
+    """None (NA — never a fabricated horizon-sentinel) when the close never reclaims the entry level
+    within the horizon window."""
+    post = _ex_bars([(102, 98, 99), (101, 85, 90), (95, 88, 93), (99, 92, 96)])  # never closes >= 100 again
+    assert time_to_recover_days(post, 100.0, 4) is None
+
+
+def test_time_to_recover_days_na_when_fewer_than_h_post_bars_or_no_entry():
+    """Shares the EXACT no-lookahead NA gate as forward_return/max_drawdown."""
+    post = _ex_bars([(110, 95, 105), (120, 90, 115)])
+    assert time_to_recover_days(post, 100.0, 3) is None
+    assert time_to_recover_days([], 100.0, 1) is None
+    assert time_to_recover_days(post, None, 1) is None
+    assert time_to_recover_days(post, 0.0, 1) is None
+
+
+def test_time_to_recover_days_unchanged_when_later_bars_removed():
+    """No-lookahead: removing bars dated > d+h does not change the h-day time-to-recover."""
+    full = _ex_bars([(102, 98, 99), (101, 85, 90), (95, 88, 93), (105, 92, 104), (300, 5, 250)])
+    truncated = _ex_bars([(102, 98, 99), (101, 85, 90), (95, 88, 93), (105, 92, 104)])
+    assert time_to_recover_days(full, 100.0, 4) == time_to_recover_days(truncated, 100.0, 4) == 2
+
+
 # ==================================================================================================
 # Hand-built snapshot fixture for the aggregation proofs (no engine — exact values by construction)
 # ==================================================================================================
@@ -1045,3 +1133,460 @@ def test_stored_scores_identical_with_and_without_forward_returns(backfilled_eng
     assert stored == live_now  # the snapshot's scores never changed when forward returns landed
     # and the pre-backfill fingerprint's scores match too (the definitive before/after equality)
     assert stored == before["fingerprint"]["lead_by_ticker"]
+
+
+# ==================================================================================================
+# _claim_samples_kwargs — pure claim-selector -> compute_samples kwarg translation (iter-41, J-25)
+# ==================================================================================================
+def test_claim_samples_kwargs_factor_claim():
+    claim = {
+        "decile": 10, "direction": "positive", "factor": "vcp_contraction", "horizon": 20,
+        "kind": "factor", "slice_kind": "decile",
+    }
+    assert _claim_samples_kwargs(claim) == {"factor_key": "vcp_contraction", "slice_kind": "decile", "decile": 10}
+
+
+def test_claim_samples_kwargs_combination_claim_parses_condition_and_renames_cohort():
+    # the EXACT shape of the real promoted composite claim in certified-claims.jsonl.
+    claim = {
+        "cohort": "composite",
+        "condition": ["rs_spy_3m:top:quintile", "high_proximity:top:tertile"],
+        "direction": "positive", "horizon": 20, "kind": "combination", "ledger": "canonical",
+    }
+    assert _claim_samples_kwargs(claim) == {
+        "cohort_kind": "composite",
+        "conditions": [
+            {"factor": "rs_spy_3m", "side": "top", "quantile": "quintile"},
+            {"factor": "high_proximity", "side": "top", "quantile": "tertile"},
+        ],
+    }
+
+
+def test_claim_samples_kwargs_event_study_claim():
+    # the EXACT shape of the real Breakout-watch x Risk-on promoted claim in certified-claims.jsonl.
+    claim = {
+        "direction": "positive", "horizon": 20, "kind": "event-study", "regime": "Risk-on",
+        "slice_kind": "regime", "subject": "Breakout-watch", "view": "pooled",
+    }
+    assert _claim_samples_kwargs(claim) == {
+        "subject_key": "Breakout-watch", "slice_kind": "regime", "regime": "Risk-on", "view": "pooled",
+    }
+
+
+def test_claim_samples_kwargs_malformed_condition_returns_none():
+    claim = {"kind": "combination", "cohort": "composite", "condition": ["not-three-parts"], "horizon": 20}
+    assert _claim_samples_kwargs(claim) is None
+
+
+def test_claim_samples_kwargs_ignores_non_selector_claim_fields():
+    """`direction` / `signal` / `ledger` / `horizon` / `kind` are NOT selector keys (they are handled
+    separately by the caller) — they must never leak into the compute_samples kwargs dict."""
+    claim = {
+        "kind": "factor", "factor": "leadership_score", "signal": "leadership_score",
+        "slice_kind": "total", "horizon": 20, "direction": "positive",
+    }
+    assert _claim_samples_kwargs(claim) == {"factor_key": "leadership_score", "slice_kind": "total"}
+
+
+# ==================================================================================================
+# compute_drawdown_expectations — phase-conditional drawdown & dry-spell expectations (iter-41, J-25)
+# ==================================================================================================
+DD_H = 20  # forward horizon used throughout this fixture (in config.walk_forward.horizons)
+
+
+def _dd_cfg(min_sample: int = 3, streak_min_n: int = 2):
+    """The real config with REDUCED min_sample / streak_min_n floors so a small hand-built fixture can
+    exercise both the 'sufficient' and 'insufficient' cells cheaply (mirrors test_research.py's own
+    `min_sample`-reduction technique for the identical reason)."""
+    cfg = load_config()
+    wf = cfg.walk_forward.model_copy(update={"min_sample": min_sample, "streak_min_n": streak_min_n})
+    return cfg.model_copy(update={"walk_forward": wf})
+
+
+def _add_dd_fr(session, run, symbol, horizon, ret, mdd=None, uw=None, ttr=None):
+    """A ForwardReturn row carrying its OWN run's REAL asof_date (unlike the generic `_add_fr` helper
+    above, which hardcodes a fixed date for tests that never read `ForwardReturn.asof_date` directly).
+    `compute_drawdown_expectations` reads `ForwardReturn.asof_date` verbatim (no ScannerRun join) to key
+    its lookup, exactly as the real `_insert_run_forward_returns` INSERT path keeps it in sync with
+    `run.asof_date` — this fixture must do the same or the join would silently miss every row."""
+    session.add(ForwardReturn(
+        run_id=run.id, symbol=symbol, horizon=horizon,
+        asof_date=run.asof_date, entry_close=100.0,
+        measured_date=run.asof_date + timedelta(days=horizon * 2),
+        realized_return=ret, max_drawdown=mdd, underwater_days=uw, time_to_recover_days=ttr,
+    ))
+
+
+# Expansion phase: 4 dates, ticker AAA — fully populated except the 3rd date's time_to_recover_days
+# (honest NA, never recovered in-window). Values chosen so median/p90 are exact by construction.
+_EXP_DATES = [date(2025, 1, 10), date(2025, 2, 10), date(2025, 3, 10), date(2025, 4, 10)]
+_EXP_MDD = [-0.05, -0.10, -0.15, -0.20]
+_EXP_UW = [2, 4, 6, 8]
+_EXP_TTR = [3, 5, None, 10]
+_EXP_RET = [0.01, -0.01, -0.02, 0.03]  # date order pos/neg/neg/pos -> longest negative streak == 2
+
+# Correction phase: 2 dates, tickers BBB/DDD — BBB fully populated, DDD's THREE dry-spell/MDD columns are
+# NULL (a live DB not yet rebuilt) so the phase's return-count (both count) and its distribution n (BBB
+# only) diverge on purpose — proving the null columns are excluded from those measures, never crashed.
+_CORR_DATES = [date(2025, 5, 10), date(2025, 6, 10)]
+_CORR_TICKERS = ["BBB", "DDD"]
+_CORR_MDD = [-0.30, None]
+_CORR_UW = [15, None]
+_CORR_TTR = [1, None]
+_CORR_RET = [-0.05, -0.08]  # both negative -> a 2-long streak (n=2 dates clears the reduced streak floor)
+
+_UNCLASSIFIED_DATE = date(2025, 7, 10)  # ticker CCC — deliberately ABSENT from the mocked phase map
+
+
+def _fake_phase_ctx(session=None, as_of=None, config=None):
+    """The served `market_phase` timeline, monkeypatched (mirrors test_regime_phase_factor.py /
+    test_phase_severity_lab.py's established pattern) so the by-phase join is exact by construction — the
+    UNCLASSIFIED date is deliberately absent, mirroring a warm-up-head date with insufficient benchmark
+    history (an honest gap, never a fabricated phase)."""
+    ctx = {
+        _EXP_DATES[0].isoformat(): {"phase": "Expansion", "severity": 10.0, "p_bear": 0.05},
+        _EXP_DATES[1].isoformat(): {"phase": "Expansion", "severity": 12.0, "p_bear": 0.05},
+        _EXP_DATES[2].isoformat(): {"phase": "Expansion", "severity": 15.0, "p_bear": 0.06},
+        _EXP_DATES[3].isoformat(): {"phase": "Expansion", "severity": 11.0, "p_bear": 0.05},
+        _CORR_DATES[0].isoformat(): {"phase": "Correction", "severity": 55.0, "p_bear": 0.40},
+        _CORR_DATES[1].isoformat(): {"phase": "Correction", "severity": 58.0, "p_bear": 0.42},
+    }
+    if as_of is None:
+        return dict(ctx)
+    return {d: v for d, v in ctx.items() if date.fromisoformat(d) <= as_of}
+
+
+@pytest.fixture()
+def dd_expectations_engine(tmp_path, monkeypatch):
+    engine = make_engine(f"sqlite:///{tmp_path / 'dd_expectations.db'}")
+    create_db_and_tables(engine)
+    with Session(engine) as session:
+        for d, mdd, uw, ttr, ret in zip(_EXP_DATES, _EXP_MDD, _EXP_UW, _EXP_TTR, _EXP_RET):
+            run = _add_run(session, d, "Risk-on")
+            _add_result(session, run.id, "AAA", "A", "Actionable", "Technology", 1)
+            _add_dd_fr(session, run, "AAA", DD_H, ret, mdd=mdd, uw=uw, ttr=ttr)
+        for d, ticker, mdd, uw, ttr, ret in zip(
+            _CORR_DATES, _CORR_TICKERS, _CORR_MDD, _CORR_UW, _CORR_TTR, _CORR_RET
+        ):
+            run = _add_run(session, d, "Risk-off")
+            _add_result(session, run.id, ticker, "C", "Avoid", "Technology", 1)
+            _add_dd_fr(session, run, ticker, DD_H, ret, mdd=mdd, uw=uw, ttr=ttr)
+        # a valid observation with NO causal phase entry (excluded, never fabricated into a bucket).
+        run = _add_run(session, _UNCLASSIFIED_DATE, "Risk-on")
+        _add_result(session, run.id, "CCC", "B", "Breakout-watch", "Technology", 1)
+        _add_dd_fr(session, run, "CCC", DD_H, 0.10, mdd=-0.02, uw=1, ttr=2)
+        session.commit()
+    monkeypatch.setattr(market_phase, "phase_context_by_date", _fake_phase_ctx)
+    return engine
+
+
+_FACTOR_CLAIM = {
+    "kind": "factor", "factor": "leadership_score", "slice_kind": "total", "horizon": DD_H,
+    "direction": "positive",
+}
+
+
+def _by_phase(payload, phase):
+    return next(row for row in payload["by_phase"] if row["phase"] == phase)
+
+
+def test_compute_drawdown_expectations_exact_per_phase_median_p90_n(dd_expectations_engine):
+    """Expansion (n=4, >= the reduced floor): exact median/p90 for max_drawdown / underwater_days (both
+    fully populated) and time_to_recover_days (3 of 4 populated — the 3rd date's None is excluded from
+    ITS OWN n, honest NA) — hand-computed via the SAME linear-interpolation percentile the risk-budget
+    gap profile uses (J-24). The loss streak is counted at the walk-forward cadence."""
+    with Session(dd_expectations_engine) as session:
+        payload = compute_drawdown_expectations(session, _FACTOR_CLAIM, _dd_cfg())
+    assert payload is not None
+    assert payload["horizon"] == DD_H
+    assert payload["min_sample"] == 3
+    assert payload["streak_min_n"] == 2
+    assert payload["survivorship_bias"]  # non-empty, the shared module-level caveat constant
+    assert payload["method_note"]
+
+    exp = _by_phase(payload, "Expansion")
+    assert exp["n"] == 4
+    mdd = exp["max_drawdown"]
+    assert mdd["insufficient"] is False and mdd["n"] == 4
+    assert mdd["median"] == pytest.approx(-0.125)
+    assert mdd["p90"] == pytest.approx(-0.065)
+    uw = exp["underwater_days"]
+    assert uw["insufficient"] is False and uw["n"] == 4
+    assert uw["median"] == pytest.approx(5)
+    assert uw["p90"] == pytest.approx(7.4)
+    ttr = exp["time_to_recover_days"]
+    assert ttr["insufficient"] is False and ttr["n"] == 3  # the None (3rd date) excluded from ITS OWN n
+    assert ttr["median"] == pytest.approx(5)
+    assert ttr["p90"] == pytest.approx(9)
+    streak = exp["loss_streak"]
+    assert streak["insufficient"] is False and streak["n"] == 4
+    assert streak["value"] == 2  # d2,d3 (both negative) are the longest consecutive run
+
+
+def test_compute_drawdown_expectations_insufficient_phase_and_null_columns_excluded(dd_expectations_engine):
+    """Correction (n=2 returns, >= the streak floor but < the distribution floor): the phase-level `n`
+    counts BOTH dates (every observation with a realized return), but max_drawdown/underwater_days/
+    time_to_recover_days each carry n=1 (only BBB — DDD's stored dry-spell/MDD columns are NULL,
+    simulating a live DB not yet rebuilt) and read 'insufficient' — never crash, never a fabricated
+    distribution over the missing values. The loss-streak floor is satisfied independently of the
+    distribution floor (the two floors are genuinely separate honesty gates)."""
+    with Session(dd_expectations_engine) as session:
+        payload = compute_drawdown_expectations(session, _FACTOR_CLAIM, _dd_cfg())
+    corr = _by_phase(payload, "Correction")
+    assert corr["n"] == 2  # both BBB and DDD counted (each had a realized return)
+    for measure in ("max_drawdown", "underwater_days", "time_to_recover_days"):
+        cell = corr[measure]
+        assert cell["n"] == 1 and cell["insufficient"] is True
+        assert cell["median"] is None and cell["p90"] is None
+    streak = corr["loss_streak"]
+    assert streak["n"] == 2 and streak["insufficient"] is False
+    assert streak["value"] == 2  # both dates negative -> a 2-long streak
+
+
+def test_compute_drawdown_expectations_every_configured_phase_padded(dd_expectations_engine):
+    """Every configured `market_phase.labels` value is emitted, in config order, even at n=0 (a cohort
+    that never saw Pullback/Bear/Recovery still discloses that honestly rather than omitting the row)."""
+    with Session(dd_expectations_engine) as session:
+        payload = compute_drawdown_expectations(session, _FACTOR_CLAIM, _dd_cfg())
+    assert [row["phase"] for row in payload["by_phase"]] == [
+        "Expansion", "Pullback", "Correction", "Bear", "Recovery",
+    ]
+    for phase in ("Pullback", "Bear", "Recovery"):
+        row = _by_phase(payload, phase)
+        assert row["n"] == 0
+        for measure in ("max_drawdown", "underwater_days", "time_to_recover_days"):
+            assert row[measure] == {"median": None, "p90": None, "n": 0, "insufficient": True}
+        assert row["loss_streak"] == {"value": None, "n": 0, "insufficient": True}
+
+
+def test_compute_drawdown_expectations_unclassified_date_excluded_never_fabricated(dd_expectations_engine):
+    """A valid observation whose snapshot date carries NO causal phase entry (mirrors a warm-up-head date
+    with insufficient benchmark history) is EXCLUDED from every phase bucket — never fabricated into one,
+    and never silently inflates a phase's n."""
+    with Session(dd_expectations_engine) as session:
+        payload = compute_drawdown_expectations(session, _FACTOR_CLAIM, _dd_cfg())
+    total_classified = sum(row["n"] for row in payload["by_phase"])
+    assert total_classified == 6  # 4 Expansion + 2 Correction; the unclassified CCC date is excluded
+
+
+def test_compute_drawdown_expectations_max_drawdown_reused_verbatim_not_recomputed(dd_expectations_engine):
+    """The served max_drawdown values are the STORED figures read VERBATIM — proven structurally: this
+    fixture carries NO `DailyPrice` bar at all, so recomputing a drawdown from bars would be impossible
+    (no price series exists to read). The served Expansion median exactly matches the hand-set stored
+    values, confirming a pure read, never a recompute."""
+    with Session(dd_expectations_engine) as session:
+        assert session.scalar(select(func.count()).select_from(DailyPrice)) == 0
+        payload = compute_drawdown_expectations(session, _FACTOR_CLAIM, _dd_cfg())
+    assert _by_phase(payload, "Expansion")["max_drawdown"]["median"] == pytest.approx(-0.125)
+
+
+def test_compute_drawdown_expectations_none_when_horizon_outside_underwater_horizons(dd_expectations_engine):
+    """A claim's horizon outside the configured `underwater_horizons` scope yields no panel — an honest
+    scope gate, never a crash or a cross-horizon-mismatched figure."""
+    cfg = load_config()
+    wf = cfg.walk_forward.model_copy(update={"underwater_horizons": [1, 5]})  # 20 excluded
+    cfg = cfg.model_copy(update={"walk_forward": wf})
+    with Session(dd_expectations_engine) as session:
+        assert compute_drawdown_expectations(session, _FACTOR_CLAIM, cfg) is None
+
+
+def test_compute_drawdown_expectations_none_when_cohort_unresolvable(dd_expectations_engine):
+    """An unknown factor key (`compute_samples` raises ValueError) resolves to None — never a 500, never
+    a crash into the caller."""
+    claim = {**_FACTOR_CLAIM, "factor": "does_not_exist_factor"}
+    with Session(dd_expectations_engine) as session:
+        assert compute_drawdown_expectations(session, claim, _dd_cfg()) is None
+
+
+def test_compute_drawdown_expectations_none_when_zero_observations(tmp_path):
+    """A validly-resolvable cohort with zero matching observations (no stored ForwardReturn at this
+    claim's horizon) is an honest empty panel (None), never a fabricated one."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'empty_cohort.db'}")
+    create_db_and_tables(engine)
+    with Session(engine) as session:
+        run = _add_run(session, date(2025, 1, 10), "Risk-on")
+        _add_result(session, run.id, "AAA", "A", "Actionable", "Technology", 1)
+        _add_dd_fr(session, run, "AAA", 5, 0.02)  # only horizon 5 stored; the claim below asks for h=20
+        session.commit()
+    with Session(engine) as session:
... [diff_bound] apps/backend/tests/test_forward_testing.py: 181 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_indexes.py b/apps/backend/tests/test_indexes.py
index 140d8b6..5f15ab8 100644
--- a/apps/backend/tests/test_indexes.py
+++ b/apps/backend/tests/test_indexes.py
@@ -114,6 +114,8 @@ _CFG = {
         "history_years": 2, "asof_cadence": "quarterly", "horizons": [1, 5, 10, 20, 60],
         "min_sample": 30, "default_horizon": 20,
         "control_group": {"seed": 20240601, "top_n": 20, "peers_per_sector": 5},
+        # iter-41 (J-25): required drawdown-expectations tunables (the /evidence panel).
+        "underwater_horizons": [1, 5, 10, 20, 60], "streak_min_n": 10,
         "attribution": {
             "top_contributors_k": 5,
             "rank_bands": [
diff --git a/apps/backend/tests/test_sectors.py b/apps/backend/tests/test_sectors.py
index 040d918..94e13da 100644
--- a/apps/backend/tests/test_sectors.py
+++ b/apps/backend/tests/test_sectors.py
@@ -149,6 +149,8 @@ _SYNTH_CFG = {
         "history_years": 2, "asof_cadence": "quarterly", "horizons": [1, 5, 10, 20, 60],
         "min_sample": 30, "default_horizon": 20,
         "control_group": {"seed": 20240601, "top_n": 20, "peers_per_sector": 5},
+        # iter-41 (J-25): required drawdown-expectations tunables (the /evidence panel).
+        "underwater_horizons": [1, 5, 10, 20, 60], "streak_min_n": 10,
         "attribution": {  # J-19: attribution is a required walk_forward sub-section
             "top_contributors_k": 5,
             "rank_bands": [
diff --git a/apps/backend/tests/test_themes.py b/apps/backend/tests/test_themes.py
index 9a763e0..3af85fe 100644
--- a/apps/backend/tests/test_themes.py
+++ b/apps/backend/tests/test_themes.py
@@ -150,6 +150,8 @@ _SYNTH_CFG = {
         "history_years": 2, "asof_cadence": "quarterly", "horizons": [1, 5, 10, 20, 60],
         "min_sample": 30, "default_horizon": 20,
         "control_group": {"seed": 20240601, "top_n": 20, "peers_per_sector": 5},
+        # iter-41 (J-25): required drawdown-expectations tunables (the /evidence panel).
+        "underwater_horizons": [1, 5, 10, 20, 60], "streak_min_n": 10,
         "attribution": {  # J-19: attribution is a required walk_forward sub-section
             "top_contributors_k": 5,
             "rank_bands": [
diff --git a/apps/frontend/app/evidence/page.tsx b/apps/frontend/app/evidence/page.tsx
index 09086a6..cf22310 100644
--- a/apps/frontend/app/evidence/page.tsx
+++ b/apps/frontend/app/evidence/page.tsx
@@ -5,10 +5,21 @@ import Link from "next/link";
 import { AlertTriangle, ShieldCheck } from "lucide-react";
 
 import { PageHeading } from "@/components/page-heading";
+import { fmtMdd } from "@/components/forward-return";
 import { Badge } from "@/components/ui/badge";
 import { Card, CardContent } from "@/components/ui/card";
 import { cn } from "@/lib/utils";
-import { claimAnchorId, claimSurface, regimeLabel } from "@/lib/evidence";
+import {
+  claimAnchorId,
+  claimSurface,
+  formatDays,
+  formatStreak,
+  insufficientLabel,
+  regimeLabel,
+  type DistributionCell,
+  type DrawdownExpectations,
+  type LossStreakCell,
+} from "@/lib/evidence";
 import { fetchEvidence, type CertifiedClaim, type EvidenceLedgerResponse } from "@/lib/api";
 
 type State =
@@ -221,11 +232,117 @@ function ClaimRow({ claim }: { claim: CertifiedClaim }) {
             )}
           </Field>
         </dl>
+
+        <DrawdownExpectationsPanel expectations={claim.expectations} />
       </CardContent>
     </Card>
   );
 }
 
+/** J-25 — the phase-conditional drawdown & dry-spell expectations panel: an additive section inside the
+ *  SAME claim card, below the existing field grid. Renders NOTHING when `expectations` is absent/null
+ *  (mirrors the Stock-detail RiskBudgetCard's "return null when absent" precedent, iter-40) — never an
+ *  error boundary, never a blank placeholder. Reads `claim.expectations` VERBATIM — no client-side
+ *  recompute; every figure is the served median/p90/streak, re-formatted only. Renders for ANY claim
+ *  regardless of its PASS/FAIL verdict (outcome-neutral, J-25) — descriptive history, never a forecast. */
+function DrawdownExpectationsPanel({
+  expectations,
+}: {
+  expectations: DrawdownExpectations | null | undefined;
+}) {
+  if (!expectations) {
+    return null;
+  }
+  return (
+    <div className="space-y-2 border-t border-border pt-3" data-testid="evidence-expectations-panel">
+      <div>
+        <h3 className="text-xs font-semibold uppercase tracking-wide text-text-faint">
+          Historical drawdown &amp; dry-spell expectations ({expectations.horizon}-day hold)
+        </h3>
+        <p className="mt-0.5 text-xs text-text-faint">
+          What following this cohort&rsquo;s methodology has historically felt like, by market phase at
+          entry — descriptive history only, never a forecast or a promise.
+        </p>
+      </div>
+      <div className="overflow-x-auto">
+        <table className="w-full min-w-[560px] border-collapse text-sm" data-testid="evidence-expectations-table">
+          <thead>
+            <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-text-faint">
+              <th className="py-1.5 pr-3 font-medium">Phase</th>
+              <th className="py-1.5 pr-3 text-right font-medium">Max-DD depth</th>
+              <th className="py-1.5 pr-3 text-right font-medium">Underwater</th>
+              <th className="py-1.5 pr-3 text-right font-medium">Time to recover</th>
+              <th className="py-1.5 text-right font-medium">Longest losing streak</th>
+            </tr>
+          </thead>
+          <tbody>
+            {expectations.by_phase.map((row) => (
+              <tr key={row.phase} className="border-b border-border last:border-b-0" data-testid="evidence-expectations-phase-row">
+                <td className="py-1.5 pr-3">
+                  <Badge variant="default">{row.phase}</Badge>
+                </td>
+                <td className="py-1.5 pr-3 text-right">
+                  <DistributionCellView cell={row.max_drawdown} format={fmtMdd} />
+                </td>
+                <td className="py-1.5 pr-3 text-right">
+                  <DistributionCellView cell={row.underwater_days} format={formatDays} />
+                </td>
+                <td className="py-1.5 pr-3 text-right">
+                  <DistributionCellView cell={row.time_to_recover_days} format={formatDays} />
+                </td>
+                <td className="py-1.5 text-right">
+                  <LossStreakCellView cell={row.loss_streak} />
+                </td>
+              </tr>
+            ))}
+          </tbody>
+        </table>
+      </div>
+      <p className="text-xs text-text-faint" data-testid="evidence-expectations-method-note">
+        {expectations.method_note}
+      </p>
+      <p className="text-xs text-text-faint" data-testid="evidence-expectations-survivorship">
+        {expectations.survivorship_bias}
+      </p>
+    </div>
+  );
+}
+
+/** One median/p90/n distribution cell — "insufficient (n=…)" below the server's honesty floor (never a
+ *  fabricated distribution), otherwise the median with the p90 + n alongside. `format` re-displays a
+ *  served number only (never computes one) — the SAME `fmtMdd`/`formatDays` helpers other evidence
+ *  surfaces already use. */
+function DistributionCellView({
+  cell,
+  format,
+}: {
+  cell: DistributionCell;
+  format: (value: number | null | undefined) => string;
+}) {
+  if (cell.insufficient) {
+    return <span className="num text-text-faint">{insufficientLabel(cell.n)}</span>;
+  }
+  return (
+    <span className="num text-text">
+      {format(cell.median)} <span className="text-text-faint">(p90 {format(cell.p90)})</span>{" "}
+      <span className="text-text-faint">n={cell.n}</span>
+    </span>
+  );
+}
+
+/** The longest-losing-streak cell — "insufficient (n=…)" below the (independent, smaller) streak floor,
+ *  otherwise the streak length + the cadence-date count it was counted over. */
+function LossStreakCellView({ cell }: { cell: LossStreakCell }) {
+  if (cell.insufficient) {
+    return <span className="num text-text-faint">{insufficientLabel(cell.n)}</span>;
+  }
+  return (
+    <span className="num text-text">
+      {formatStreak(cell.value)} <span className="text-text-faint">(n={cell.n})</span>
+    </span>
+  );
+}
+
 function Field({ label, children }: { label: string; children: React.ReactNode }) {
   return (
     <div className="space-y-1">
diff --git a/apps/frontend/lib/api.ts b/apps/frontend/lib/api.ts
index 129e326..2335b26 100644
--- a/apps/frontend/lib/api.ts
+++ b/apps/frontend/lib/api.ts
@@ -9,7 +9,11 @@ import { resolveApiBase } from "@/lib/api-base";
 import type { BudgetResponse, BudgetSpendPoint, CanonicalBudget, StagingBudget } from "@/lib/budget";
 import type {
   CertifiedClaim,
+  DistributionCell,
+  DrawdownExpectations,
   EvidenceLedgerResponse,
+  LossStreakCell,
+  PhaseExpectations,
   ProvenSignal,
 } from "@/lib/evidence";
 import type { GraveyardEntry, GraveyardResponse, RevisitProtocol } from "@/lib/graveyard";
@@ -25,6 +29,11 @@ import type {
 // aggregate) — do not confuse the two.
 export type { CertifiedClaim, EvidenceLedgerResponse, ProvenSignal };
 
+// Re-export the additive drawdown & dry-spell expectations types (goal-mcp-loop iter-41, J-25) — the
+// nullable `median`/`p90`/`value` numeric fields route every consumer through the guarded
+// `formatDays`/`formatStreak`/`fmtMdd` formatters (never an unguarded `.toFixed` on a possibly-null value).
+export type { DistributionCell, DrawdownExpectations, LossStreakCell, PhaseExpectations };
+
 // Re-export the pre-registration registry types (goal-mcp-loop iter-30, J-18) alongside `fetchRegistry`.
 export type { PreRegistrationRow, RegistryResponse };
 
diff --git a/apps/frontend/lib/evidence.test.ts b/apps/frontend/lib/evidence.test.ts
index 020a9c5..c17f852 100644
--- a/apps/frontend/lib/evidence.test.ts
+++ b/apps/frontend/lib/evidence.test.ts
@@ -34,8 +34,11 @@ import {
   combinationEvidenceAnchor,
   evidenceAnchor,
   factorCohortFromClaim,
+  formatDays,
   formatEvidencePct,
   formatPValue,
+  formatStreak,
+  insufficientLabel,
   proofFieldsFor,
   regimeLabel,
   resolveCohortEvidence,
@@ -955,4 +958,27 @@ check("claimSurface + claimAnchorId render the rs_spy_3m h60 /evidence row hones
   assert.strictEqual(resolveEvidenceStatus("leadership_score", {}).proven, false);
 });
 
+// --- drawdown & dry-spell expectations formatters (goal-mcp-loop iter-41, J-25) -------------------------
+check("insufficientLabel renders the exact honest-floor copy", () => {
+  assert.strictEqual(insufficientLabel(0), "insufficient (n=0)");
+  assert.strictEqual(insufficientLabel(7), "insufficient (n=7)");
+});
+
+check("formatDays renders one decimal + 'd', and an em dash for null/undefined/non-finite", () => {
+  assert.strictEqual(formatDays(5), "5.0d");
+  assert.strictEqual(formatDays(7.4), "7.4d");
+  assert.strictEqual(formatDays(0), "0.0d");
+  assert.strictEqual(formatDays(null), "—");
+  assert.strictEqual(formatDays(undefined), "—");
+  assert.strictEqual(formatDays(Number.NaN), "—");
+});
+
+check("formatStreak renders a rounded integer, and an em dash for null/undefined/non-finite", () => {
+  assert.strictEqual(formatStreak(2), "2");
+  assert.strictEqual(formatStreak(0), "0");
+  assert.strictEqual(formatStreak(3.0), "3");
+  assert.strictEqual(formatStreak(null), "—");
+  assert.strictEqual(formatStreak(undefined), "—");
+});
+
 console.log(`\n${passed} evidence-badge resolver checks passed.`);
diff --git a/apps/frontend/lib/evidence.ts b/apps/frontend/lib/evidence.ts
index 7b874d7..cea8c8d 100644
--- a/apps/frontend/lib/evidence.ts
+++ b/apps/frontend/lib/evidence.ts
@@ -24,10 +24,57 @@ export interface Verdict {
   [key: string]: unknown;
 }
 
+/** One `{median, p90, n, insufficient}` distribution cell (iter-41, J-25) — max-drawdown depth /
+ *  underwater duration / time-to-recover, per phase. `insufficient` true means `n` sits below the
+ *  server's honesty floor (`DrawdownExpectations.min_sample`) — `median`/`p90` are then null (never a
+ *  fabricated distribution); the panel renders "insufficient (n=…)" instead. */
+export interface DistributionCell {
+  median: number | null;
+  p90: number | null;
+  n: number;
+  insufficient: boolean;
+}
+
+/** One longest-losing-streak cell (iter-41, J-25), counted at the WALK-FORWARD CADENCE (one point per
+ *  snapshot date, never per name per day). `n` is the number of distinct cadence dates examined — its
+ *  own honesty floor is `DrawdownExpectations.streak_min_n` (deliberately smaller than the per-
+ *  observation `min_sample` the other three measures use). `insufficient` true means `value` is null. */
+export interface LossStreakCell {
+  value: number | null;
+  n: number;
+  insufficient: boolean;
+}
+
+/** One market-phase row of the expectations panel — every configured `market_phase.labels` value is
+ *  always present (padded, even at n=0), in config order. */
+export interface PhaseExpectations {
+  phase: string;
+  n: number;
+  max_drawdown: DistributionCell;
+  underwater_days: DistributionCell;
+  time_to_recover_days: DistributionCell;
+  loss_streak: LossStreakCell;
+}
+
+/** The phase-conditional drawdown & dry-spell expectations payload for ONE certified claim (iter-41,
+ *  J-25) — additive on `GET /api/evidence`, read VERBATIM from `app.engine.forward_testing.
+ *  compute_drawdown_expectations` (never recomputed client-side). Descriptive history only — renders for
+ *  ANY claim regardless of its PASS/FAIL verdict (outcome-neutral; see goal.md J-25). */
+export interface DrawdownExpectations {
+  horizon: number;
+  min_sample: number;
+  streak_min_n: number;
+  survivorship_bias: string;
+  method_note: string;
+  by_phase: PhaseExpectations[];
+}
+
 /** One certified-claims ledger row, read VERBATIM from `GET /api/evidence`. `claim` is the hypothesis
  *  (the cohort selectors); `proven` is true ONLY for a PASS verdict; `signal` is the UI signal key the
  *  PASS backs (null for a real signal-less writer entry — fail-safe). `forward_walk` is the forward-walk
- *  score-to-date (null until a certified claim is monitored). */
+ *  score-to-date (null until a certified claim is monitored). `expectations` (iter-41, J-25) is ADDITIVE
+ *  and OPTIONAL — the backend omits the key entirely (never a fabricated panel) when the cohort could not
+ *  be resolved; a `null`/`undefined` value must render nothing for the panel section (never an error). */
 export interface CertifiedClaim {
   signal: string | null;
   claim: Record<string, unknown>;
@@ -38,6 +85,7 @@ export interface CertifiedClaim {
   verdict: Verdict;
   proven: boolean;
   forward_walk: unknown | null;
+  expectations?: DrawdownExpectations | null;
 }
 
 /** A proven claim row, as stored in the served `proven_signals` map (keyed by signal). Same shape as a
@@ -200,6 +248,35 @@ export function formatPValue(value: number | null | undefined): string {
   return Number(value.toPrecision(4)).toString();
 }
 
+// --- drawdown & dry-spell expectations formatters (goal-mcp-loop iter-41, J-25) -------------------------
+// PURE, read-only display formatters for the additive `expectations` panel. They re-format a served
+// number only — they never compute a median/p90/streak client-side (that stays 100% server-side in
+// `compute_drawdown_expectations`).
+
+/** The exact honest-floor copy every below-floor cell renders — "insufficient (n=…)". */
+export function insufficientLabel(n: number): string {
+  return `insufficient (n=${n})`;
+}
+
+/** Format a day-count DISTRIBUTION value (underwater-duration / time-to-recover median/p90) — one
+ *  decimal place + "d" (a median/p90 of day-counts is legitimately fractional, e.g. "7.4d"); a
+ *  null/non-finite value renders an em dash (never a fabricated 0). */
+export function formatDays(value: number | null | undefined): string {
+  if (value == null || !Number.isFinite(value)) {
+    return "—";
+  }
+  return `${value.toFixed(1)}d`;
+}
+
+/** Format a loss-streak length — always a true integer count (no interpolation, unlike the distribution
+ *  cells); a null/non-finite value renders an em dash. */
+export function formatStreak(value: number | null | undefined): string {
+  if (value == null || !Number.isFinite(value)) {
+    return "—";
+  }
+  return `${Math.round(value)}`;
+}
+
 // --- claim-row presentation (goal-mcp-loop iter-4) — regime label + honest title/linkback --------------
 // PURE, read-only helpers the `/evidence` ClaimRow consumes to deliver J-04 (regime-conditioned evidence,
 // "clearly labeled with the regime it holds in") WITHOUT regressing J-05 (the leadership score row's title
diff --git a/config.yaml b/config.yaml
index 18bd75c..55742a1 100644
--- a/config.yaml
+++ b/config.yaml
@@ -789,6 +789,14 @@ walk_forward:
       - { label: "1–10",  min: 1,  max: 10 }
       - { label: "11–50", min: 11, max: 50 }
       - { label: "51+",   min: 51, max: null }   # open top band (all remaining ranks)
+  # iter-41 (J-25) CONSUMED — the /evidence phase-conditional drawdown/dry-spell expectations panel
+  # (forward_testing.compute_drawdown_expectations). underwater_horizons scopes which forward horizons the
+  # panel reports underwater-duration / time-to-recover for (defaults to the full horizons set so every
+  # certified claim's own horizon is covered); streak_min_n is the loss-streak honesty floor, counted in
+  # walk-forward-cadence dates (far fewer than min_sample's per-observation count, so it needs its own,
+  # smaller floor).
+  underwater_horizons: [1, 5, 10, 20, 60]
+  streak_min_n: 10
 
 # ----------------------------------------------------------------------------------------
 # iter-18 (J-10 performance) — GET /api/stocks/{ticker}/bars presentation bounding on the deep
```
