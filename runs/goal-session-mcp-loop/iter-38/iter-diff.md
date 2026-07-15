# Iteration diff (bounded)

Files changed: 11. Shown in full: 11.

```diff
diff --git a/apps/backend/app/api/watchlist.py b/apps/backend/app/api/watchlist.py
index 5c4b51e..7811c1c 100644
--- a/apps/backend/app/api/watchlist.py
+++ b/apps/backend/app/api/watchlist.py
@@ -35,6 +35,7 @@ from app.config import Config, get_config
 from app.db import get_session
 from app.engine.prices import close_on, latest_data_date
 from app.engine.snapshot_serving import filtered_stock_rows, resolved_run
+from app.engine.watchlist_xray import build_xray_payload
 from app.models import Watchlist
 
 router = APIRouter(tags=["watchlist"])
@@ -95,7 +96,14 @@ def _enrich(entry: Watchlist, rows_by_ticker: dict[str, dict], session: Session,
 @router.get("/watchlist")
 def list_watchlist(session: Session = Depends(get_session)) -> dict:
     """Every watchlist entry (newest first), each enriched LIVE with its current canonical
-    scores/setup/invalidation and an honest price-since-added. `503` when no price data exists."""
+    scores/setup/invalidation and an honest price-since-added. `503` when no price data exists.
+
+    iter-38 (J-23 / B-204): ADDITIVELY carries `xray` — the watchlist concentration X-ray (pairwise
+    correlation, deterministic clusters, effective-number-of-bets, sector/theme/setup concentration),
+    computed once alongside this SAME response by `app.engine.watchlist_xray.build_xray_payload`. The
+    existing `asof_date` + `entries[]` shape is unchanged (additive-only — see test_api_watchlist.py's
+    shape test)."""
+    cfg = get_config()
     asof = latest_data_date(session)
     if asof is None:
         raise HTTPException(status_code=503, detail="no price data available")
@@ -103,10 +111,12 @@ def list_watchlist(session: Session = Depends(get_session)) -> dict:
         select(Watchlist).order_by(Watchlist.created_at.desc(), Watchlist.id.desc())
     ).all()
     # Item D (iter-24): scope the canonical-row fetch to exactly THIS caller's watchlist tickers.
-    rows_by_ticker = _canonical_rows(session, get_config(), (entry.ticker for entry in entries))
+    tickers = [entry.ticker for entry in entries]
+    rows_by_ticker = _canonical_rows(session, cfg, tickers)
     return {
         "asof_date": asof.isoformat(),
         "entries": [_enrich(entry, rows_by_ticker, session, asof) for entry in entries],
+        "xray": build_xray_payload(session, cfg, tickers, asof),
     }
 
 
diff --git a/apps/backend/app/config.py b/apps/backend/app/config.py
index 2cef887..32b8eb3 100644
--- a/apps/backend/app/config.py
+++ b/apps/backend/app/config.py
@@ -2319,6 +2319,63 @@ def _default_evidence() -> "EvidenceCfg":
     return EvidenceCfg()
 
 
+class WatchlistXrayCfg(BaseModel):
+    """goal-mcp-loop iter-38 (J-23 / backlog B-204) — the watchlist concentration X-ray tunables. EVERY
+    number the canonical `app.engine.watchlist_xray:build_xray_payload` composer (and the ONE shared
+    ENB/correlation helper it calls, `app.engine.concentration`) reads lives here (anti-goal: No magic
+    numbers):
+
+      - `corr_window_days` — the trailing `bars_asof_window` lookback (bars <= as-of) each watchlist
+        member's return series is computed over (default ~126, about 6 trading months).
+      - `cluster_threshold` — the Pearson correlation at/above which two members join the same
+        deterministic connected-component cluster (no ML).
+      - `min_overlap_days` — the honesty floor: a member whose own trailing return series has fewer
+        than this many observations renders NA throughout the matrix/clusters/ENB rather than a
+        fabricated correlation.
+
+    Default-populated (a config predating this key still loads unchanged, mirroring `ChartBarsCfg` /
+    `ServerOpsCfg`). Every value MUST be positive; `min_overlap_days` MUST be <= `corr_window_days` (an
+    unreachable floor is a config error); `cluster_threshold` MUST be a valid Pearson bound in [-1, 1]
+    — validated at boot, never a silent default."""
+
+    model_config = ConfigDict(extra="allow")
+    corr_window_days: int = 126
+    cluster_threshold: float = 0.7
+    min_overlap_days: int = 60
+
+    @model_validator(mode="after")
+    def _validate(self) -> "WatchlistXrayCfg":
+        if self.corr_window_days <= 0:
+            raise ValueError("watchlist.xray.corr_window_days must be positive")
+        if self.min_overlap_days <= 0:
+            raise ValueError("watchlist.xray.min_overlap_days must be positive")
+        if self.min_overlap_days > self.corr_window_days:
+            raise ValueError(
+                f"watchlist.xray.min_overlap_days ({self.min_overlap_days}) must be <= "
+                f"corr_window_days ({self.corr_window_days})"
+            )
+        if not (-1.0 <= self.cluster_threshold <= 1.0):
+            raise ValueError(
+                f"watchlist.xray.cluster_threshold must be in [-1, 1], got {self.cluster_threshold}"
+            )
+        return self
+
+
+class WatchlistCfg(BaseModel):
+    """goal-mcp-loop iter-38 top-level `watchlist:` config block. Currently holds only `xray` (B-204);
+    default-populated so a config / inline test fixture predating this block still loads unchanged."""
+
+    model_config = ConfigDict(extra="allow")
+    xray: WatchlistXrayCfg = Field(default_factory=WatchlistXrayCfg)
+
+
+def _default_watchlist() -> "WatchlistCfg":
+    """The built-in default watchlist config — used when a config predating this block (or an inline
+    test fixture) omits `watchlist`. The real `config.yaml` restates it explicitly as the single
+    documented source."""
+    return WatchlistCfg()
+
+
 class Config(BaseModel):
     """Validated view of config.yaml. Only the iter-1-consumed sections are typed/validated;
     scaffolded sections ride along via extra="allow" so they can be tuned without code edits."""
@@ -2378,6 +2435,11 @@ class Config(BaseModel):
     # check only). Default-populated so a config / inline test fixture predating it still loads
     # unchanged; the real `config.yaml` restates it explicitly as the single documented source.
     data_quality: DataQualityCfg = Field(default_factory=_default_data_quality)
+    # goal-mcp-loop iter-38 (J-23 / backlog B-204) — the watchlist concentration X-ray tunables (the
+    # correlation window, cluster threshold, and overlap-history honesty floor). Default-populated so a
+    # config / inline test fixture predating this block still loads unchanged; the real `config.yaml`
+    # restates it explicitly as the single documented source.
+    watchlist: WatchlistCfg = Field(default_factory=_default_watchlist)
 
     @field_validator("themes")
     @classmethod
diff --git a/apps/backend/tests/test_api_watchlist.py b/apps/backend/tests/test_api_watchlist.py
index 849cdf6..582456d 100644
--- a/apps/backend/tests/test_api_watchlist.py
+++ b/apps/backend/tests/test_api_watchlist.py
@@ -12,6 +12,8 @@ independent without touching any snapshot table.
 """
 from __future__ import annotations
 
+import json
+
 import pytest
 from fastapi import HTTPException
 from fastapi.testclient import TestClient
@@ -21,6 +23,7 @@ from sqlmodel import Session, select
 import main
 from app.db import create_db_and_tables, make_engine
 from app.engine.prices import latest_data_date
+from app.engine.setups import ALL_STATUSES
 from app.models import (
     ForwardReturn,
     ScannerResult,
@@ -35,6 +38,10 @@ REASON = "ANET — strong leader, watching pullback"
 _SCORE_BLOCKS = ("leadership", "entry_quality", "risk")
 _CANONICAL_KEYS = ("leadership", "entry_quality", "risk", "setup", "invalidation")
 _SNAPSHOT_MODELS = (ScannerRun, ScannerResult, SectorScoreRow, ThemeScoreRow, ForwardReturn)
+_ENTRY_KEYS = {
+    "id", "ticker", "date_added", "asof_date_added", "reason", "price_since_added",
+    "sector", "leadership", "entry_quality", "risk", "setup", "invalidation",
+}
 
 
 @pytest.fixture
@@ -172,3 +179,67 @@ def test_watchlist_raises_503_when_no_price_data(tmp_path):
         with pytest.raises(HTTPException) as post_exc:
             add_watchlist(WatchlistCreate(ticker=TICKER, reason=REASON), session)
         assert post_exc.value.status_code == 503
+
+
+# --------------------------------------------------------------------------------------------------
+# iter-38 (J-23 / backlog B-204) — the additive `xray` concentration field.
+# --------------------------------------------------------------------------------------------------
+def test_xray_field_is_additive_existing_shape_unchanged(clean_watchlist):
+    """The additive `xray` field never disturbs the EXISTING `asof_date`/`entries[]` shape (iter-7
+    contract) — a single-entry watchlist is `status: "insufficient"` (a correlation view needs a pair)."""
+    with TestClient(main.app) as client:
+        client.post("/api/watchlist", json={"ticker": TICKER, "reason": REASON})
+        body = client.get("/api/watchlist").json()
+    assert set(body.keys()) == {"asof_date", "entries", "xray"}
+    assert set(body["entries"][0].keys()) == _ENTRY_KEYS  # unchanged per-entry shape
+    assert body["xray"]["status"] == "insufficient"
+    assert body["xray"]["tickers"] == [TICKER]
+
+
+def test_xray_status_ok_with_two_watchlist_entries(clean_watchlist):
+    """Two real, long-tenured watchlist entries produce a full `status: "ok"` X-ray: a symmetric
+    matrix, all-six setup-status concentration, and an ENB within the exact [1, 2] bound that holds for
+    ANY two-asset correlation matrix regardless of the real historical correlation value."""
+    with TestClient(main.app) as client:
+        client.post("/api/watchlist", json={"ticker": TICKER, "reason": REASON})
+        client.post("/api/watchlist", json={"ticker": "AAPL", "reason": "benchmark leader"})
+        body = client.get("/api/watchlist").json()
+    xray = body["xray"]
+    assert xray["status"] == "ok"
+    assert set(xray["tickers"]) == {TICKER, "AAPL"}
+    # self-correlation is ~1.0 for any real, non-degenerate stock series (never fabricated NA)
+    assert xray["correlation_matrix"][TICKER][TICKER] == pytest.approx(1.0, abs=1e-6)
+    assert xray["correlation_matrix"]["AAPL"]["AAPL"] == pytest.approx(1.0, abs=1e-6)
+    cross = xray["correlation_matrix"][TICKER]["AAPL"]
+    assert cross == xray["correlation_matrix"]["AAPL"][TICKER]  # symmetric
+    assert -1.0 <= cross <= 1.0
+    assert xray["effective_number_of_bets"] is not None
+    assert 1.0 <= xray["effective_number_of_bets"] <= 2.0  # exact math bound for exactly 2 assets
+    assert sum(len(c) for c in xray["clusters"]) == 2
+    assert sum(e["count"] for e in xray["setup_concentration"]) == 2
+    assert {e["status"] for e in xray["setup_concentration"]} == set(ALL_STATUSES)
+
+
+def test_xray_no_proven_or_advice_language(clean_watchlist):
+    """Anti-goals: the X-ray is descriptive only — no proven-language, no position-advice language."""
+    with TestClient(main.app) as client:
+        client.post("/api/watchlist", json={"ticker": TICKER, "reason": REASON})
+        client.post("/api/watchlist", json={"ticker": "AAPL", "reason": "benchmark leader"})
+        raw = json.dumps(client.get("/api/watchlist").json()).lower()
+    for banned in ("proven", "trim", "rebalance"):
+        assert banned not in raw
+    import re
+
+    for word in ("add", "reduce", "buy", "sell"):
+        assert re.search(rf"\b{word}\b", raw) is None
+
+
+def test_xray_determinism_same_asof_repeated_calls(clean_watchlist):
+    """Determinism (anti-goal #5): repeated reads against the same frozen seed reproduce the X-ray
+    byte-identically — never a wall-clock- or ordering-dependent value."""
+    with TestClient(main.app) as client:
+        client.post("/api/watchlist", json={"ticker": TICKER, "reason": REASON})
+        client.post("/api/watchlist", json={"ticker": "AAPL", "reason": "benchmark leader"})
+        first = client.get("/api/watchlist").json()["xray"]
+        second = client.get("/api/watchlist").json()["xray"]
+    assert first == second
diff --git a/apps/frontend/app/watchlist/page.tsx b/apps/frontend/app/watchlist/page.tsx
index 2a7a8ad..f54ea72 100644
--- a/apps/frontend/app/watchlist/page.tsx
+++ b/apps/frontend/app/watchlist/page.tsx
@@ -2,15 +2,18 @@
 
 import { useEffect, useState } from "react";
 import Link from "next/link";
-import { AlertTriangle, Plus, Star, Trash2 } from "lucide-react";
+import { AlertTriangle, Network, Plus, Star, Trash2 } from "lucide-react";
 
 import { useAsOfHref } from "@/components/asof-provider";
+import { CorrelationHeatmap } from "@/components/correlation-heatmap";
 import { EmptyState } from "@/components/empty-state";
 import { PageHeading } from "@/components/page-heading";
 import { ScoreBadge } from "@/components/score-badge";
 import { Badge } from "@/components/ui/badge";
 import { Card } from "@/components/ui/card";
+import { InfoTooltip } from "@/components/ui/info-tooltip";
 import { formatIsoDate } from "@/lib/dates";
+import { sectorLabel } from "@/lib/sector-label";
 import { cn } from "@/lib/utils";
 import {
   addWatchlistEntry,
@@ -18,6 +21,7 @@ import {
   removeWatchlistEntry,
   type WatchlistEntry,
   type WatchlistResponse,
+  type WatchlistXray,
 } from "@/lib/api";
 
 type State =
@@ -229,6 +233,8 @@ export default function WatchlistPage() {
               </tbody>
             </table>
           </Card>
+
+          <WatchlistXraySection xray={state.data.xray} />
         </>
       ) : null}
     </div>
@@ -310,3 +316,157 @@ function WatchlistSkeleton() {
     </Card>
   );
 }
+
+/**
+ * J-23 (backlog B-204) — the watchlist concentration X-ray: how correlated, clustered, and
+ * concentrated the watchlist really is. Purely descriptive (no advice / no proven-language) — reads
+ * the `xray` field `GET /api/watchlist` already carries, verbatim; no separate fetch, no browser-side
+ * correlation/ENB recompute. Fewer than two names renders a distinct "not enough names yet" state
+ * (same visual family as the zero-entries EmptyState above, different copy) — the "Backend
+ * unavailable" page-level error state already covers this section since it rides the same response.
+ */
+function WatchlistXraySection({ xray }: { xray: WatchlistXray }) {
+  if (xray.status === "insufficient") {
+    return (
+      <EmptyState
+        icon={Network}
+        title="Not enough names yet for an X-ray"
+        description="Add at least one more stock to your watchlist to see how concentrated it is — pairwise correlation, clusters, and effective independent bets, all read from your saved list."
+      />
+    );
+  }
+
+  return (
+    <Card className="space-y-4 p-4" data-testid="watchlist-xray">
+      <div>
+        <h2 className="text-sm font-semibold text-text">Concentration X-ray</h2>
+        <p className="mt-0.5 text-xs text-text-faint">
+          Descriptive only — how correlated, clustered, and concentrated your watchlist really is. No
+          recommendations.
+        </p>
+      </div>
+
+      <div className="flex flex-wrap items-center gap-2">
+        <span className="num text-lg font-semibold text-text" data-testid="watchlist-xray-enb">
+          {xray.effective_number_of_bets === null ? "NA" : `≈ ${xray.effective_number_of_bets.toFixed(1)}`}
+        </span>
+        <span className="text-xs text-text-muted">
+          effective independent bets (over the last {xray.window_days} trading days)
+        </span>
+        <InfoTooltip
+          label="What is effective independent bets?"
+          content={
+            <>
+              How many genuinely independent positions your watchlist behaves like, derived from the
+              eigenvalues of the pairwise correlation matrix over the trailing {xray.window_days} trading
+              days. Perfectly correlated names count as one bet; fully independent names each count as
+              their own. A name with under {xray.min_overlap_days} days of overlapping history is
+              excluded and shown as NA.
+            </>
+          }
+        />
+      </div>
+
+      <CorrelationHeatmap xray={xray} />
+
+      <div data-testid="watchlist-xray-clusters">
+        <h3 className="text-xs font-semibold uppercase tracking-wide text-text-faint">Clusters</h3>
+        <p className="mt-0.5 text-[11px] text-text-faint">
+          Names grouped when their correlation is at or above {xray.cluster_threshold.toFixed(2)}.
+        </p>
+        <div className="mt-1.5 flex flex-wrap gap-2">
+          {xray.clusters.map((cluster) => (
+            <Badge key={cluster.join("-")} variant={cluster.length > 1 ? "accent" : "default"}>
+              {cluster.join(" · ")}
+            </Badge>
+          ))}
+        </div>
+      </div>
+
+      <ConcentrationBars
+        title="Sector concentration"
+        testId="watchlist-xray-sector"
+        entries={xray.sector_concentration.map((e) => ({
+          key: e.sector ?? "unassigned",
+          label: sectorLabel(e.sector),
+          count: e.count,
+          pct: e.pct,
+        }))}
+      />
+      <ConcentrationBars
+        title="Theme concentration"
+        testId="watchlist-xray-theme"
+        entries={xray.theme_concentration.map((e) => ({ key: e.slug, label: e.name, count: e.count, pct: e.pct }))}
+      />
+      <ConcentrationBars
+        title="Shared setup"
+        testId="watchlist-xray-setup"
+        entries={xray.setup_concentration.map((e) => ({
+          key: e.status,
+          label: e.status,
+          count: e.count,
+          pct: e.pct,
+          variant: setupVariant(e.status), // the SAME status->color mapping the table's Setup column uses
+        }))}
+      />
+    </Card>
+  );
+}
+
+/** A small horizontal bar list shared by the sector / theme / setup concentration breakdowns. Zero-
+ *  count entries are hidden (the backend payload may carry all six setup statuses for a stable shape;
+ *  only what's actually present on the watchlist is worth showing). An entry MAY carry a `variant` —
+ *  used ONLY for setup status, which already has an established meaning-bearing color (reused from
+ *  `setupVariant`, the SAME mapping the table's Setup column uses); sector/theme names carry no such
+ *  established meaning, so their label stays plain text rather than an arbitrary/misleading color. The
+ *  bar fill is ALWAYS the existing `accent` token — no new color scale. */
+function ConcentrationBars({
+  title,
+  entries,
+  testId,
+}: {
+  title: string;
+  entries: {
+    key: string;
+    label: string;
+    count: number;
+    pct: number;
+    variant?: "ok" | "warn" | "danger" | "accent" | "default";
+  }[];
+  testId: string;
+}) {
+  const present = entries.filter((e) => e.count > 0);
+  return (
+    <div data-testid={testId}>
+      <h3 className="text-xs font-semibold uppercase tracking-wide text-text-faint">{title}</h3>
+      {present.length === 0 ? (
+        <p className="mt-1 text-xs text-text-faint">None on this watchlist.</p>
+      ) : (
+        <div className="mt-1.5 space-y-1">
+          {present.map((e) => (
+            <div key={e.key} className="flex items-center gap-2 text-xs">
+              {e.variant ? (
+                <Badge variant={e.variant} className="w-32 shrink-0 justify-start truncate">
+                  {e.label}
+                </Badge>
+              ) : (
+                <span className="w-32 shrink-0 truncate text-text-muted" title={e.label}>
+                  {e.label}
+                </span>
+              )}
+              <div className="h-2 flex-1 overflow-hidden rounded-full bg-surface-2">
+                <div
+                  className="h-full rounded-full bg-accent"
+                  style={{ width: `${Math.round(e.pct * 100)}%` }}
+                />
+              </div>
+              <span className="num w-16 shrink-0 text-right text-text-faint">
+                {e.count} · {Math.round(e.pct * 100)}%
+              </span>
+            </div>
+          ))}
+        </div>
+      )}
+    </div>
+  );
+}
diff --git a/apps/frontend/lib/api.ts b/apps/frontend/lib/api.ts
index 9597b21..be50c49 100644
--- a/apps/frontend/lib/api.ts
+++ b/apps/frontend/lib/api.ts
@@ -1065,9 +1065,63 @@ export interface WatchlistEntry {
   price_since_added: number | null; // fraction; null = NA, never fabricated
 }
 
+// --- watchlist concentration X-ray (iter-38, J-23 / backlog B-204) --------------------------
+/** One sector's share of the watchlist. `sector` is nullable (a stock with no mapped GICS sector) —
+ *  render its label via the EXISTING `sectorLabel()` helper (`lib/sector-label.ts`, the ONE place
+ *  that maps null -> "Unassigned"), never a second null-handling rule. Single-valued: `pct` sums to
+ *  1.0 across every returned entry. */
+export interface WatchlistXraySectorConcentration {
+  sector: string | null;
+  count: number;
+  pct: number;
+}
+
+/** One theme's share of the watchlist. Multi-valued (a stock may carry several themes, or none) —
+ *  `pct` is share-of-watchlist, NOT a partition (entries need not sum to 1.0). Only themes with >= 1
+ *  watchlist member are listed. */
+export interface WatchlistXrayThemeConcentration {
+  slug: string;
+  name: string;
+  count: number;
+  pct: number;
+}
+
+/** One setup status's share of the watchlist — always all six canonical statuses (0 where absent),
+ *  mirroring the dashboard's own `summarize_candidates` "a number always renders" contract. */
+export interface WatchlistXraySetupConcentration {
+  status: string;
+  count: number;
+  pct: number;
+}
+
+/** GET /api/watchlist's additive `xray` field (B-204): the watchlist concentration X-ray, computed
+ *  ONCE engine-side by `app.engine.watchlist_xray.build_xray_payload` and re-read VERBATIM here — NO
+ *  browser-side correlation/ENB recompute (B-204's named dominant failure mode). `status ===
+ *  "insufficient"` (fewer than 2 watchlist names) means every list/matrix field below is empty; the
+ *  page renders a distinct "not enough names yet" state rather than an empty matrix. A `null`
+ *  `correlation_matrix[a][b]` cell is an HONEST NA (undefined pairwise correlation — insufficient own
+ *  history, missing bars, or zero-variance series), never a fabricated 0. `effective_number_of_bets`
+ *  is `null` only when NO member has enough usable history to compute it at all. */
+export interface WatchlistXray {
+  status: "ok" | "insufficient";
+  window_days: number; // the trailing correlation window (config watchlist.xray.corr_window_days)
+  min_overlap_days: number; // the honesty floor below which a member's row/column is NA throughout
+  cluster_threshold: number; // the Pearson correlation at/above which two members join a cluster
+  tickers: string[]; // every watchlist ticker, sorted — the matrix's row/column vocabulary
+  history_days: Record<string, number>; // observed own-history length per ticker, capped at window_days
+  correlation_matrix: Record<string, Record<string, number | null>>;
+  clusters: string[][]; // deterministic connected components; a lone name is its own singleton cluster
+  effective_number_of_bets: number | null;
+  enb_member_count: number; // how many members contributed to the ENB computation
+  sector_concentration: WatchlistXraySectorConcentration[];
+  theme_concentration: WatchlistXrayThemeConcentration[];
+  setup_concentration: WatchlistXraySetupConcentration[];
+}
+
 export interface WatchlistResponse {
   asof_date: string;
   entries: WatchlistEntry[];
+  xray: WatchlistXray;
 }
 
 /** GET /api/watchlist — every saved entry (newest first), enriched live. Throws on non-200 so the
diff --git a/config.yaml b/config.yaml
index 2e093ed..f36d61f 100644
--- a/config.yaml
+++ b/config.yaml
@@ -1303,6 +1303,19 @@ server:
   memory_cap_mb: 6144                      # ulimit -v virtual-memory cap (MB) for the backend process: clears the one-copy ~3.27M-row bar prefill (iter-19: now a streamed, column-projected load — retained footprint ~0.4-0.5 GB, not the ~6.8 GB whole-table ORM `.all()` load this cap used to barely clear) + headroom; a pathological N-copy spike is OOM-killed as ONE process, never a VM-wide swap freeze
   malloc_arena_max: 2                      # iter-27 (anti-goal #8): MALLOC_ARENA_MAX exported by start-backend.sh. glibc otherwise creates up to 8*ncpus (128 on a 16-core host) independent malloc arenas, each retaining freed-but-unreturned address space; across the uvicorn threadpool + parallel backfill workers that fragments VSZ and pins the ulimit -v ceiling on a SECOND full-universe rebuild. Capping to 2 arenas bounds that fragmentation (the dominant VSZ lever behind the iter-26/iter-27 rebuild crash) — byte-identical outputs (allocator layout only, never a stored/served value)
 
+# ----------------------------------------------------------------------------------------
+# goal-mcp-loop iter-38 (J-23 / backlog B-204) — the watchlist concentration X-ray. EVERY tunable the
+# canonical app.engine.watchlist_xray:build_xray_payload composer (and the ONE shared ENB/correlation
+# helper it calls, app.engine.concentration) reads lives here (anti-goal: No magic numbers) — the
+# trailing correlation window, the connected-component cluster threshold, and the per-member
+# overlap-history honesty floor (below which a member renders NA rather than a fabricated correlation).
+# Computed fresh on every GET /api/watchlist read; no persisted field (watchlist storage schema untouched).
+watchlist:
+  xray:
+    corr_window_days: 126        # ~6 trading months trailing bars_asof_window lookback (bars <= as-of)
+    cluster_threshold: 0.7       # Pearson correlation at/above which two members join the same cluster
+    min_overlap_days: 60         # a member's own return series shorter than this renders NA throughout
+
 # ----------------------------------------------------------------------------------------
 # iter-12 CONSUMED — Methodology / Glossary catalog (J-12). The SINGLE config-backed source that
 # EXPLAINS every setup status + the VCP pattern: a plain-language meaning, the exact thresholds that
diff --git a/apps/backend/app/engine/concentration.py b/apps/backend/app/engine/concentration.py
new file mode 100644
index 0000000..c5d0a3a
--- /dev/null
+++ b/apps/backend/app/engine/concentration.py
@@ -0,0 +1,79 @@
+"""app.engine.concentration — the ONE canonical effective-number-of-bets / pairwise-correlation
+helper (goal-mcp-loop iter-38, J-23 / backlog B-204).
+
+PURE module: no database, no I/O, no wall-clock dependency — every function takes plain numeric
+inputs and returns plain numeric outputs. This is the SINGLE implementation of both computations in
+the codebase (Data Contract keystone; B-204's "share B-104's helper" trap): the watchlist
+concentration X-ray (`app.engine.watchlist_xray`) is the first consumer; the future B-104 evidence
+correlation audit imports these SAME two functions rather than writing a second ENB/correlation
+implementation. Do NOT add a second `effective_number_of_bets` or `correlation_matrix` anywhere else
+in the codebase.
+
+`correlation_matrix(series_by_name)` computes the pairwise Pearson correlation over every pair of
+named return series. Two series of different lengths are aligned on their TRAILING overlap (the last
+`min(len_a, len_b)` observations of each) — the natural alignment for return series that are both
+bounded trailing windows ending at the same as-of date (see `app.engine.prices.bars_asof_window`, the
+composer's bar source). An undefined pair — fewer than 2 overlapping observations, or either series
+has zero variance over the overlap — renders an honest `None`, never a fabricated 0.0 (anti-goal: No
+fabricated data).
+
+`effective_number_of_bets(corr_matrix)` computes the classic ENB statistic `(Σλ)² / Σλ²` over the
+eigenvalues of a CLEAN, real-valued, symmetric correlation matrix (every cell defined — the caller is
+responsible for building this "honest sub-matrix" by excluding any name whose row/column carries an
+undefined pairwise correlation; see `watchlist_xray.build_xray_payload`). A fully independent set of N
+names yields ENB == N (identity matrix); a fully redundant set (every pair correlation 1.0) yields
+ENB == 1 (one effective bet) — "how many genuinely independent positions this set behaves like."
+"""
+from __future__ import annotations
+
+from typing import Optional, Sequence
+
+import numpy as np
+
+
+def _pair_correlation(x: Sequence[float], y: Sequence[float]) -> Optional[float]:
+    """Pearson correlation between two return series, aligned on their TRAILING overlap (the last
+    `min(len(x), len(y))` observations of each — both series are trailing windows ending at the same
+    as-of date, so this is a real date alignment, not an arbitrary truncation). `None` (honest NA) when
+    the overlap is under 2 observations or either series has zero variance over it — a correlation is
+    mathematically undefined in both cases, never fabricated as 0.0."""
+    n = min(len(x), len(y))
+    if n < 2:
+        return None
+    xs = np.asarray(x[-n:], dtype=float)
+    ys = np.asarray(y[-n:], dtype=float)
+    if xs.std() == 0.0 or ys.std() == 0.0:
+        return None
+    corr = float(np.corrcoef(xs, ys)[0, 1])
+    return None if np.isnan(corr) else corr
+
+
+def correlation_matrix(series_by_name: dict[str, Sequence[float]]) -> dict[str, dict[str, Optional[float]]]:
+    """The full pairwise Pearson correlation matrix over `series_by_name` (name -> return series).
+    Returns a nested dict keyed both ways (`matrix[a][b] == matrix[b][a]`), every name present as both
+    a row and a column, including the self pair (diagonal). An undefined pair (see `_pair_correlation`)
+    is `None` — always render this as NA, never as 0.0 or 1.0."""
+    names = list(series_by_name)
+    return {a: {b: _pair_correlation(series_by_name[a], series_by_name[b]) for b in names} for a in names}
+
+
+def effective_number_of_bets(corr_matrix: Sequence[Sequence[float]]) -> Optional[float]:
+    """`(Σλ)² / Σλ²` over the eigenvalues of a clean NxN correlation matrix (`numpy.linalg.eigvalsh` —
+    the matrix is real-symmetric by construction). The caller passes the "honest sub-matrix": only
+    names with a fully-defined pairwise correlation against every other included name (see
+    `watchlist_xray.build_xray_payload`) — this function does NOT itself handle `None`/NA cells.
+
+    N == 0 -> `None` (nothing to measure). N == 1 -> `1.0` (a single name is trivially "1 independent
+    bet" — handled directly rather than through the general eigenvalue ratio)."""
+    arr = np.asarray(corr_matrix, dtype=float)
+    n = arr.shape[0]
+    if n == 0:
+        return None
+    if n == 1:
+        return 1.0
+    eigenvalues = np.linalg.eigvalsh(arr)
+    sum_lambda = float(eigenvalues.sum())
+    sum_lambda_sq = float(np.square(eigenvalues).sum())
+    if sum_lambda_sq == 0.0:
+        return None
+    return (sum_lambda**2) / sum_lambda_sq
diff --git a/apps/backend/app/engine/watchlist_xray.py b/apps/backend/app/engine/watchlist_xray.py
new file mode 100644
index 0000000..ec396ae
--- /dev/null
+++ b/apps/backend/app/engine/watchlist_xray.py
@@ -0,0 +1,227 @@
+"""app.engine.watchlist_xray — the watchlist concentration X-ray composer (goal-mcp-loop iter-38,
+J-23 / backlog B-204).
+
+`build_xray_payload(session, cfg, tickers, asof)` is a PURE-COMPOSITION read: it re-reads price bars
+via the bounded `app.engine.prices.bars_asof_window` (bars <= as-of, NEVER a whole-table load) and the
+SAME canonical snapshot rows `GET /api/stocks` serves (`app.engine.snapshot_serving.filtered_stock_rows`),
+and composes them with the ONE canonical ENB/correlation helper (`app.engine.concentration`) into the
+additive `xray` field `GET /api/watchlist` attaches to its EXISTING response. It recomputes NO
+already-registered value — sector / themes / setup status are read verbatim from the canonical row;
+price history goes through the SAME bounded accessor every other bounded reader uses; setup counts
+reuse `app.engine.setups.summarize_candidates` (the dashboard's own candidate-count tally) rather than
+a second tally.
+
+Honesty floor: a ticker whose OWN trailing return series (over `watchlist.xray.corr_window_days`) has
+fewer than `watchlist.xray.min_overlap_days` observations is excluded from every correlation/cluster/
+ENB computation — its row/column in the served matrix is `None` throughout (never a fabricated
+correlation). `effective_number_of_bets` is computed over the "honest sub-matrix": only tickers whose
+correlation against EVERY OTHER included ticker is defined (this also excludes a zero-variance series).
+
+Sector concentration groups by the RAW stored `sector` (including `None`) — it does NOT bucket a null
+sector to a literal "Unassigned" string here; that display mapping is the EXISTING frontend
+`sectorLabel()` helper's job (`lib/sector-label.ts`, the single place that maps null -> "Unassigned",
+iter-19). This module only guarantees the null-sector group is counted like any other, never dropped,
+never a crash.
+
+Fewer than 2 watchlist tickers -> `status: "insufficient"` (a correlation view needs at least a pair);
+every list/matrix field is empty and no price/snapshot read is attempted.
+"""
+from __future__ import annotations
+
+from datetime import date as date_cls
+from typing import Iterable, Optional
+
+from sqlmodel import Session
+
+from app.config import Config
+from app.engine.concentration import correlation_matrix, effective_number_of_bets
+from app.engine.prices import bars_asof_window, closes
+from app.engine.setups import ALL_STATUSES, summarize_candidates
+from app.engine.snapshot_serving import filtered_stock_rows, resolved_run
+
+# A correlation view is only meaningful with at least a pair — not a config tunable, a mathematical floor.
+_MIN_TICKERS_FOR_MATRIX = 2
+
+
+def _returns(closes_: list[float]) -> list[float]:
+    """Day-over-day simple returns, ascending — one entry shorter than the input close series. A
+    non-positive prior close (impossible for real equity data, but defended against so a corrupt/odd
+    bar never raises a division error — anti-goal: never crash on a data-shape surprise) is honestly
+    skipped rather than fabricating a return."""
+    out: list[float] = []
+    for i in range(1, len(closes_)):
+        prior = closes_[i - 1]
+        if prior and prior > 0:
+            out.append(closes_[i] / prior - 1)
+    return out
+
+
+def _connected_components(
+    tickers: list[str], matrix: dict[str, dict[str, Optional[float]]], threshold: float
+) -> list[list[str]]:
+    """Deterministic correlation-threshold clustering (connected components; no ML — B-204). An edge
+    joins two DIFFERENT tickers when their correlation is defined and `>= threshold` (POSITIVE
+    correlation only — the concentration risk this X-ray discloses is names moving TOGETHER; a strongly
+    negative correlation is diversifying, not concentrating). A ticker with no qualifying edge
+    (including every NA/insufficient-history ticker) is its own singleton cluster. Clusters and their
+    members are sorted for a fully deterministic, byte-identical output regardless of input order."""
+    parent = {t: t for t in tickers}
+
+    def find(x: str) -> str:
+        while parent[x] != x:
+            parent[x] = parent[parent[x]]
+            x = parent[x]
+        return x
+
+    def union(a: str, b: str) -> None:
+        ra, rb = find(a), find(b)
+        if ra != rb:
+            parent[ra] = rb
+
+    for i, a in enumerate(tickers):
+        for b in tickers[i + 1 :]:
+            corr = matrix[a][b]
+            if corr is not None and corr >= threshold:
+                union(a, b)
+
+    groups: dict[str, list[str]] = {}
+    for t in tickers:
+        groups.setdefault(find(t), []).append(t)
+    clusters = [sorted(members) for members in groups.values()]
+    clusters.sort(key=lambda members: members[0])
+    return clusters
+
+
+def _sector_concentration(canonical_rows: dict[str, dict], tickers: list[str]) -> list[dict]:
+    """Sector concentration over the watchlist's OWN tickers, grouped by the raw stored `sector`
+    (nullable, single-valued — every ticker contributes to exactly one bucket, so `pct` always sums to
+    1.0 across the returned entries). A missing canonical row (defensive — should not happen for a
+    validated watchlist entry) degrades to the same null-sector bucket, never a crash."""
+    total = len(tickers)
+    counts: dict[Optional[str], int] = {}
+    for ticker in tickers:
+        row = canonical_rows.get(ticker)
+        sector = row["sector"] if row else None
+        counts[sector] = counts.get(sector, 0) + 1
+    entries = [{"sector": sector, "count": count, "pct": count / total} for sector, count in counts.items()]
+    # Deterministic order: highest count first; the null-sector bucket sorts after every named sector
+    # (the `sector is None` boolean sorts True-after-False), then alphabetically among ties.
+    entries.sort(key=lambda e: (-e["count"], e["sector"] is None, e["sector"] or ""))
+    return entries
+
+
+def _theme_concentration(canonical_rows: dict[str, dict], tickers: list[str]) -> list[dict]:
+    """Theme concentration over the watchlist's OWN tickers. A stock may carry zero, one, or several
+    themes (multi-membership, unlike sector) — `pct` is share-of-watchlist per theme, NOT a partition
+    (entries need not sum to 100%). Only themes with >= 1 watchlist member are listed (the full theme
+    catalog is not restated here)."""
+    total = len(tickers)
+    counts: dict[str, dict] = {}
+    for ticker in tickers:
+        row = canonical_rows.get(ticker)
+        if not row:
+            continue
+        for theme in row.get("themes") or []:
+            entry = counts.setdefault(theme["slug"], {"name": theme["name"], "count": 0})
+            entry["count"] += 1
+    entries = [
+        {"slug": slug, "name": v["name"], "count": v["count"], "pct": v["count"] / total}
+        for slug, v in counts.items()
+    ]
+    entries.sort(key=lambda e: (-e["count"], e["slug"]))
+    return entries
+
+
+def _setup_concentration(canonical_rows: dict[str, dict], tickers: list[str]) -> list[dict]:
+    """Shared-setup count: how many watchlist names currently classify to each of the six canonical
+    setup statuses (`app.engine.setups`), reusing the SAME `summarize_candidates` the dashboard's
+    candidate counts use — never a second setup-status tally. Always all six statuses (0 where absent),
+    mirroring `summarize_candidates`'s own "a number always renders" contract."""
+    total = len(tickers)
+    rows = [canonical_rows[t] for t in tickers if t in canonical_rows]
+    counts = summarize_candidates(rows)
+    return [
+        {"status": status, "count": counts[status], "pct": counts[status] / total} for status in ALL_STATUSES
+    ]
+
+
+def _insufficient_payload(cfg: Config, tickers: list[str]) -> dict:
+    xray_cfg = cfg.watchlist.xray
+    return {
+        "status": "insufficient",
+        "window_days": xray_cfg.corr_window_days,
+        "min_overlap_days": xray_cfg.min_overlap_days,
+        "cluster_threshold": xray_cfg.cluster_threshold,
+        "tickers": tickers,
+        "history_days": {},
+        "correlation_matrix": {},
+        "clusters": [],
+        "effective_number_of_bets": None,
+        "enb_member_count": 0,
+        "sector_concentration": [],
+        "theme_concentration": [],
+        "setup_concentration": [],
+    }
+
+
+def build_xray_payload(session: Session, cfg: Config, tickers: Iterable[str], asof: date_cls) -> dict:
+    """The additive `xray` field `GET /api/watchlist` attaches to its existing response — see the
+    module docstring for the full contract. `tickers` may be given in any order; the response is always
+    deterministically sorted regardless (byte-identical across repeated calls with the same inputs)."""
+    ticker_list = sorted({t for t in tickers if t})
+    xray_cfg = cfg.watchlist.xray
+    if len(ticker_list) < _MIN_TICKERS_FOR_MATRIX:
+        return _insufficient_payload(cfg, ticker_list)
+
+    # Bounded per-symbol reads (bars <= as-of, trailing corr_window_days) — never a whole-table load.
+    history_days: dict[str, int] = {}
+    returns_by_ticker: dict[str, list[float]] = {}
+    for ticker in ticker_list:
+        bars = bars_asof_window(session, ticker, asof, xray_cfg.corr_window_days)
+        returns = _returns(closes(bars))
+        history_days[ticker] = len(returns)
+        returns_by_ticker[ticker] = returns
+
+    # The honesty floor: only tickers with enough OWN history enter the correlation computation.
+    sufficient = [t for t in ticker_list if history_days[t] >= xray_cfg.min_overlap_days]
+    series_by_name = {t: returns_by_ticker[t] for t in sufficient}
+    sub_matrix = correlation_matrix(series_by_name) if series_by_name else {}
+
+    # Compose the FULL matrix over every watchlist ticker; any cell touching an insufficient-history
+    # ticker (or a zero-variance pair `correlation_matrix` itself flagged) is honestly None.
+    full_matrix: dict[str, dict[str, Optional[float]]] = {
+        a: {b: sub_matrix.get(a, {}).get(b) for b in ticker_list} for a in ticker_list
+    }
+
+    clusters = _connected_components(ticker_list, full_matrix, xray_cfg.cluster_threshold)
+
+    # The "honest sub-matrix" for ENB: sufficient tickers whose correlation against every OTHER
+    # sufficient ticker is defined (excludes a zero-variance series, which `correlation_matrix` already
+    # marked None throughout its row/column).
+    enb_eligible = [t for t in sufficient if all(full_matrix[t][o] is not None for o in sufficient)]
+    enb = None
+    if enb_eligible:
+        ordered = sorted(enb_eligible)
+        enb_matrix = [[full_matrix[a][b] for b in ordered] for a in ordered]
+        enb = effective_number_of_bets(enb_matrix)
+
+    # Sector / theme / setup concentration read the SAME canonical rows GET /api/stocks serves —
+    # recomputes no score/sector/setup/theme value.
+    run = resolved_run(session, None, cfg)
+    canonical_rows = {row["ticker"]: row for row in filtered_stock_rows(session, run, ticker_list, cfg)}
+
+    return {
+        "status": "ok",
+        "window_days": xray_cfg.corr_window_days,
+        "min_overlap_days": xray_cfg.min_overlap_days,
+        "cluster_threshold": xray_cfg.cluster_threshold,
+        "tickers": ticker_list,
+        "history_days": history_days,
+        "correlation_matrix": full_matrix,
+        "clusters": clusters,
+        "effective_number_of_bets": enb,
+        "enb_member_count": len(enb_eligible),
+        "sector_concentration": _sector_concentration(canonical_rows, ticker_list),
+        "theme_concentration": _theme_concentration(canonical_rows, ticker_list),
+        "setup_concentration": _setup_concentration(canonical_rows, ticker_list),
+    }
diff --git a/apps/backend/tests/test_concentration.py b/apps/backend/tests/test_concentration.py
new file mode 100644
index 0000000..ccc8be9
--- /dev/null
+++ b/apps/backend/tests/test_concentration.py
@@ -0,0 +1,127 @@
+"""app.engine.concentration — the ONE ENB / pairwise-correlation helper (iter-38, J-23 / B-204).
+
+Pure math, DB-free — every expected value below is hand-derived so the test asserts an exact number
+(anti-pattern: "something returned"). The B-204 fixture (two perfectly correlated synthetic return
+series + one independent series -> ENB close to the intuitive "2 independent things") is the headline
+sanity check the phase spec names explicitly.
+"""
+from __future__ import annotations
+
+import numpy as np
+import pytest
+
+from app.engine.concentration import correlation_matrix, effective_number_of_bets
+
+
+# --- correlation_matrix -----------------------------------------------------------------------
+def test_correlation_matrix_perfect_positive():
+    series = {"A": [1.0, 2.0, 3.0, 4.0, 5.0], "B": [2.0, 4.0, 6.0, 8.0, 10.0]}
+    matrix = correlation_matrix(series)
+    assert matrix["A"]["B"] == pytest.approx(1.0)
+    assert matrix["B"]["A"] == pytest.approx(1.0)
+    assert matrix["A"]["A"] == pytest.approx(1.0)
+    assert matrix["B"]["B"] == pytest.approx(1.0)
+
+
+def test_correlation_matrix_perfect_negative():
+    series = {"A": [1.0, 2.0, 3.0, 4.0, 5.0], "B": [10.0, 8.0, 6.0, 4.0, 2.0]}
+    matrix = correlation_matrix(series)
+    assert matrix["A"]["B"] == pytest.approx(-1.0)
+    assert matrix["B"]["A"] == pytest.approx(-1.0)
+
+
+def test_correlation_matrix_zero_variance_is_honest_none_never_fabricated():
+    series = {"A": [1.0, 2.0, 3.0], "FLAT": [5.0, 5.0, 5.0]}
+    matrix = correlation_matrix(series)
+    assert matrix["A"]["FLAT"] is None
+    assert matrix["FLAT"]["A"] is None
+    assert matrix["FLAT"]["FLAT"] is None  # self-correlation of a constant series is also undefined
+
+
+def test_correlation_matrix_too_short_is_honest_none():
+    series = {"A": [1.0], "B": [2.0]}
+    matrix = correlation_matrix(series)
+    assert matrix["A"]["B"] is None
+    assert matrix["B"]["A"] is None
+
+
+def test_correlation_matrix_empty_series_is_honest_none():
+    series = {"A": [], "B": [1.0, 2.0, 3.0]}
+    matrix = correlation_matrix(series)
+    assert matrix["A"]["B"] is None
+
+
+def test_correlation_matrix_aligns_on_trailing_overlap():
+    # B (3 points, perfectly increasing) is aligned against A's LAST 3 points, which are ALSO
+    # perfectly increasing — but A's FIRST 3 points are deliberately decreasing "noise" that must be
+    # ignored by trailing-overlap alignment, or the correlation would come out negative instead of +1.
+    a = [9.0, 5.0, 1.0, 10.0, 20.0, 30.0]  # last 3: [10, 20, 30] (increasing); first 3: decreasing
+    b = [1.0, 2.0, 3.0]                     # increasing — matches a's LAST 3, not its first 3
+    matrix = correlation_matrix({"A": a, "B": b})
+    assert matrix["A"]["B"] == pytest.approx(1.0)
+
+
+def test_correlation_matrix_single_name_self_pair_only():
+    matrix = correlation_matrix({"A": [1.0, 2.0, 3.0]})
+    assert matrix == {"A": {"A": pytest.approx(1.0)}}
+
+
+# --- effective_number_of_bets -----------------------------------------------------------------
+def test_enb_identity_matrix_equals_n_exactly():
+    # N fully independent names: identity correlation matrix -> ENB == N exactly.
+    identity = np.eye(4).tolist()
+    assert effective_number_of_bets(identity) == pytest.approx(4.0)
+
+
+def test_enb_all_ones_matrix_equals_one_exactly():
+    # N fully redundant (perfectly correlated) names -> ENB == 1 exactly (one effective bet).
+    ones = [[1.0, 1.0, 1.0], [1.0, 1.0, 1.0], [1.0, 1.0, 1.0]]
+    assert effective_number_of_bets(ones) == pytest.approx(1.0)
+
+
+def test_enb_two_names_zero_correlation_equals_two_exactly():
+    matrix = [[1.0, 0.0], [0.0, 1.0]]
+    assert effective_number_of_bets(matrix) == pytest.approx(2.0)
+
+
+def test_enb_hand_derived_two_correlated_plus_one_independent():
+    # matrix [[1,1,0],[1,1,0],[0,0,1]]: hand-derived eigenvalues {2, 0, 1} -> (Sum(lambda))^2 / Sum(lambda^2)
+    # = 3^2 / (4+0+1) = 9/5 = 1.8 exactly — the B-204 fixture's exact target for an IDEALIZED
+    # (correlation exactly 1.0 / exactly 0.0) two-correlated-plus-one-independent construction.
+    matrix = [[1.0, 1.0, 0.0], [1.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
+    assert effective_number_of_bets(matrix) == pytest.approx(1.8)
+
+
+def test_enb_single_name_is_one():
+    assert effective_number_of_bets([[1.0]]) == 1.0
+
+
+def test_enb_empty_is_none():
+    assert effective_number_of_bets([]) is None
+
+
+# --- B-204 fixture: full pipeline from synthetic RETURN series through both functions -----------
+def test_b204_fixture_two_correlated_one_independent_series():
+    """The phase-spec-named B-204 sanity check: two PERFECTLY correlated synthetic return series (B is
+    an exact positive scalar multiple of A, so their Pearson correlation is exactly 1.0) plus one
+    INDEPENDENT series (a fresh random draw) -> ENB close to the intuitive "2 independent things" (one
+    correlated pair behaving as one bet, plus one independent name) — matching the hand-derived exact
+    1.8 for the idealized {corr=1, corr=0} case (see test_enb_hand_derived_two_correlated_plus_one_independent)
+    within a wide, justified tolerance for the real (not exactly 0) sample correlation of two
+    independent 200-point draws (standard error ~1/sqrt(200) ~ 0.07, so the loose |corr| < 0.25 bound
+    below is a >3-sigma margin — deterministically seeded, never flaky)."""
+    rng = np.random.default_rng(20240601)  # the project's committed determinism seed
+    base = rng.normal(0, 1, size=200).tolist()
+    correlated_a = base
+    correlated_b = [3.0 * v for v in base]  # a positive scalar multiple -> correlation exactly 1.0
+    independent = rng.normal(0, 1, size=200).tolist()  # a fresh, unrelated draw
+
+    matrix = correlation_matrix({"A": correlated_a, "B": correlated_b, "C": independent})
+    assert matrix["A"]["B"] == pytest.approx(1.0, abs=1e-9)
+    assert abs(matrix["A"]["C"]) < 0.25
+    assert abs(matrix["B"]["C"]) < 0.25
+
+    names = ["A", "B", "C"]
+    enb_matrix = [[matrix[r][c] for c in names] for r in names]
+    enb = effective_number_of_bets(enb_matrix)
+    assert 1.5 < enb < 2.2  # close to the hand-derived idealized 1.8, never near 1 (fully redundant) or 3 (independent)
diff --git a/apps/backend/tests/test_watchlist_xray.py b/apps/backend/tests/test_watchlist_xray.py
new file mode 100644
index 0000000..afaaedf
--- /dev/null
+++ b/apps/backend/tests/test_watchlist_xray.py
@@ -0,0 +1,254 @@
+"""app.engine.watchlist_xray — the watchlist concentration X-ray composer (iter-38, J-23 / B-204).
+
+FAST synthetic tests: tiny hand-made DBs (no seed boot), mirroring the `test_iter33_dynamic_universe.py`
+/ `test_bars_windowing.py` synthetic-DB pattern. The B-204 numeric fixture (ENB ≈ 2 from exact
+correlation/eigenvalue math) is proven directly against `app.engine.concentration` in
+`test_concentration.py`; this file proves the COMPOSER'S OWN responsibilities: bounded reads, the
+`min_overlap_days` honesty floor (never a fabricated correlation), null-sector grouping (never a crash,
+never dropped), the shared-setup reuse of `summarize_candidates`, multi-membership theme concentration,
+determinism, and the insufficient-watchlist / missing-bars / empty error cases.
+"""
+from __future__ import annotations
+
+import json
+from datetime import date, datetime, timedelta, timezone
+
+import numpy as np
+import pytest
+from sqlmodel import Session
+
+from app.config import load_config
+from app.db import create_db_and_tables, make_engine
+from app.engine.setups import ALL_STATUSES
+from app.engine.watchlist_xray import build_xray_payload
+from app.models import DailyPrice, ScannerResult, ScannerRun
+
+ASOF = date(2026, 1, 30)
+
+
+def _engine(tmp_path, name: str):
+    engine = make_engine(f"sqlite:///{tmp_path / name}")
+    create_db_and_tables(engine)
+    return engine
+
+
+def _mk_run(session: Session, asof: date) -> ScannerRun:
+    """Minimal valid ScannerRun row (mirrors test_iter33_dynamic_universe.py's `_mk_run`)."""
+    run = ScannerRun(
+        asof_date=asof, created_at=datetime.now(timezone.utc), provider="seed", benchmark="SPY",
+        regime_score=50.0, regime_label="Choppy", regime_components_json="{}",
+        new_high_low_json="{}", candidate_counts_json="{}",
+    )
+    session.add(run)
+    session.commit()
+    session.refresh(run)
+    return run
+
+
+def _mk_result(
+    session: Session, run_id: int, ticker: str, *, sector: str | None, themes: list[dict], status: str
+) -> None:
+    """A ScannerResult whose `record_json` carries the minimum keys `filtered_stock_rows` /
+    `build_xray_payload` actually read (ticker/sector/themes/setup) — unlike the bare `"{}"` some other
+    synthetic fixtures use (those never exercise `filtered_stock_rows`' JSON rehydration path)."""
+    record = {"ticker": ticker, "sector": sector, "themes": themes, "setup": {"status": status, "reason": "fixture"}}
+    session.add(ScannerResult(
+        run_id=run_id, ticker=ticker, name=ticker, sector=sector,
+        leadership_score=50.0, leadership_bucket="C",
+        entry_quality_score=50.0, entry_quality_bucket="C",
+        risk_score=50.0, risk_bucket="C",
+        setup_status=status, rank=1, record_json=json.dumps(record),
+    ))
+    session.commit()
+
+
+def _insert_prices(session: Session, symbol: str, closes_: list[float], end: date) -> None:
+    """Consecutive daily bars ending exactly at `end` (calendar days — the composer only cares about
+    ordering and `date <= asof`, mirroring `test_bars_windowing.py`'s synthetic fixture)."""
+    start = end - timedelta(days=len(closes_) - 1)
+    rows = [
+        {
+            "symbol": symbol, "date": start + timedelta(days=i),
+            "open": c, "high": c, "low": c, "close": c, "volume": 1_000_000.0,
+        }
+        for i, c in enumerate(closes_)
+    ]
+    session.execute(DailyPrice.__table__.insert(), rows)
+    session.commit()
+
+
+def _linear_series(n: int, start: float = 100.0, step: float = 1.0) -> list[float]:
+    return [start + step * i for i in range(n)]
+
+
+# --- insufficient-watchlist (0-1 names) --------------------------------------------------------
+def test_insufficient_watchlist_zero_names(tmp_path):
+    cfg = load_config()
+    engine = _engine(tmp_path, "zero.db")
+    with Session(engine) as session:
+        payload = build_xray_payload(session, cfg, [], ASOF)
+    assert payload["status"] == "insufficient"
+    assert payload["tickers"] == []
+    assert payload["correlation_matrix"] == {}
+    assert payload["clusters"] == []
+    assert payload["effective_number_of_bets"] is None
+    assert payload["sector_concentration"] == []
+
+
+def test_insufficient_watchlist_one_name_no_crash(tmp_path):
+    cfg = load_config()
+    engine = _engine(tmp_path, "one.db")
+    with Session(engine) as session:
+        _mk_run(session, ASOF)
+        _insert_prices(session, "SOLO", _linear_series(200), ASOF)
+        payload = build_xray_payload(session, cfg, ["SOLO"], ASOF)
+    assert payload["status"] == "insufficient"
+    assert payload["tickers"] == ["SOLO"]
+    assert payload["effective_number_of_bets"] is None
+
+
+# --- sufficient-history pair: correlation / clusters / ENB ---------------------------------------
+def test_two_names_sufficient_history_correlate_and_render_ok(tmp_path):
+    cfg = load_config()
+    engine = _engine(tmp_path, "two.db")
+    aaa = _linear_series(200, start=100.0, step=1.0)
+    bbb = [2.0 * v for v in aaa]  # a pure positive scalar multiple -> IDENTICAL returns -> corr == 1.0 exactly
+    with Session(engine) as session:
+        _mk_run(session, ASOF)
+        _insert_prices(session, "AAA", aaa, ASOF)
+        _insert_prices(session, "BBB", bbb, ASOF)
+        payload = build_xray_payload(session, cfg, ["AAA", "BBB"], ASOF)
+    assert payload["status"] == "ok"
+    assert payload["tickers"] == ["AAA", "BBB"]
+    assert payload["correlation_matrix"]["AAA"]["BBB"] == pytest.approx(1.0, abs=1e-9)
+    assert payload["correlation_matrix"]["BBB"]["AAA"] == pytest.approx(1.0, abs=1e-9)
+    assert payload["clusters"] == [["AAA", "BBB"]]  # one merged cluster
+    assert payload["effective_number_of_bets"] == pytest.approx(1.0, abs=1e-9)  # fully redundant pair
+    assert payload["enb_member_count"] == 2
+
+
+def test_uncorrelated_pair_is_two_separate_clusters_and_enb_two(tmp_path):
+    cfg = load_config()
+    engine = _engine(tmp_path, "uncorr.db")
+    rng = np.random.default_rng(20240601)
+    a = (1000.0 + np.cumsum(rng.normal(0, 1, size=200))).tolist()
+    b = (1000.0 + np.cumsum(rng.normal(0, 1, size=200))).tolist()  # a fresh, independent draw
+    with Session(engine) as session:
+        _mk_run(session, ASOF)
+        _insert_prices(session, "IND1", a, ASOF)
+        _insert_prices(session, "IND2", b, ASOF)
+        payload = build_xray_payload(session, cfg, ["IND1", "IND2"], ASOF)
+    corr = payload["correlation_matrix"]["IND1"]["IND2"]
+    assert corr is not None and abs(corr) < 0.3  # ~uncorrelated (loose, deterministic-seed bound)
+    assert payload["clusters"] == [["IND1"], ["IND2"]]  # no qualifying edge -> two singletons
+    assert 1.0 <= payload["effective_number_of_bets"] <= 2.0  # exact math bound for any 2-asset pair
+
+
+# --- the min_overlap_days honesty floor ---------------------------------------------------------
+def test_short_history_member_is_honest_na_never_fabricated(tmp_path):
+    cfg = load_config()
+    engine = _engine(tmp_path, "short.db")
+    with Session(engine) as session:
+        _mk_run(session, ASOF)
+        _insert_prices(session, "OLD", _linear_series(200), ASOF)
+        _insert_prices(session, "NEW", _linear_series(10), ASOF)  # far under min_overlap_days
+        payload = build_xray_payload(session, cfg, ["OLD", "NEW"], ASOF)
+    assert payload["status"] == "ok"
+    assert payload["history_days"]["NEW"] == 9  # 10 closes -> 9 returns
+    assert payload["history_days"]["NEW"] < cfg.watchlist.xray.min_overlap_days
+    assert payload["correlation_matrix"]["OLD"]["NEW"] is None
+    assert payload["correlation_matrix"]["NEW"]["OLD"] is None
+    assert payload["correlation_matrix"]["NEW"]["NEW"] is None  # excluded from the honest sub-matrix too
+    assert payload["clusters"] == [["NEW"], ["OLD"]]  # NEW has no qualifying edge -> its own singleton
+    assert payload["effective_number_of_bets"] == 1.0  # only OLD is ENB-eligible -> a single "1 bet"
+    assert payload["enb_member_count"] == 1
+
+
+def test_missing_bars_member_is_na_not_a_crash(tmp_path):
+    cfg = load_config()
+    engine = _engine(tmp_path, "missing.db")
+    with Session(engine) as session:
+        _mk_run(session, ASOF)
+        _insert_prices(session, "HASDATA", _linear_series(200), ASOF)
+        # "NODATA" has literally zero stored bars for the whole window.
+        payload = build_xray_payload(session, cfg, ["HASDATA", "NODATA"], ASOF)
+    assert payload["status"] == "ok"
+    assert payload["history_days"]["NODATA"] == 0
+    assert payload["correlation_matrix"]["NODATA"]["HASDATA"] is None
+    assert payload["correlation_matrix"]["HASDATA"]["NODATA"] is None
+
+
+# --- sector / theme / setup concentration --------------------------------------------------------
+def test_sector_concentration_groups_null_sector_without_crash(tmp_path):
+    cfg = load_config()
+    engine = _engine(tmp_path, "sector.db")
+    with Session(engine) as session:
+        run = _mk_run(session, ASOF)
+        _mk_result(session, run.id, "TECH1", sector="Technology", themes=[], status="Actionable")
+        _mk_result(session, run.id, "TECH2", sector="Technology", themes=[], status="Actionable")
+        _mk_result(session, run.id, "NOSEC", sector=None, themes=[], status="Avoid")
+        for ticker in ("TECH1", "TECH2", "NOSEC"):
+            _insert_prices(session, ticker, _linear_series(200), ASOF)
+        payload = build_xray_payload(session, cfg, ["TECH1", "TECH2", "NOSEC"], ASOF)
+    by_sector = {e["sector"]: e for e in payload["sector_concentration"]}
+    assert by_sector["Technology"]["count"] == 2
+    assert by_sector[None]["count"] == 1  # the null-sector bucket — grouped, never dropped, never crashed
+    assert by_sector[None]["pct"] == pytest.approx(1 / 3)
+    assert sum(e["count"] for e in payload["sector_concentration"]) == 3  # every ticker counted once
+
+
+def test_setup_concentration_reuses_summarize_candidates_all_six_statuses(tmp_path):
+    cfg = load_config()
+    engine = _engine(tmp_path, "setup.db")
+    with Session(engine) as session:
+        run = _mk_run(session, ASOF)
+        _mk_result(session, run.id, "A1", sector="Technology", themes=[], status="Actionable")
+        _mk_result(session, run.id, "A2", sector="Technology", themes=[], status="Actionable")
+        _mk_result(session, run.id, "B1", sector="Health Care", themes=[], status="Avoid")
+        for ticker in ("A1", "A2", "B1"):
+            _insert_prices(session, ticker, _linear_series(200), ASOF)
+        payload = build_xray_payload(session, cfg, ["A1", "A2", "B1"], ASOF)
+    statuses = {e["status"] for e in payload["setup_concentration"]}
+    assert statuses == set(ALL_STATUSES)  # always all six, 0 where absent (mirrors summarize_candidates)
+    by_status = {e["status"]: e["count"] for e in payload["setup_concentration"]}
+    assert by_status["Actionable"] == 2
+    assert by_status["Avoid"] == 1
+    assert by_status["Breakout-watch"] == 0
+
+
+def test_theme_concentration_counts_multi_membership(tmp_path):
+    cfg = load_config()
+    engine = _engine(tmp_path, "theme.db")
+    with Session(engine) as session:
+        run = _mk_run(session, ASOF)
+        _mk_result(session, run.id, "T1", sector="Technology", themes=[{"slug": "ai", "name": "AI"}], status="Actionable")
+        _mk_result(
+            session, run.id, "T2", sector="Technology",
+            themes=[{"slug": "ai", "name": "AI"}, {"slug": "cloud", "name": "Cloud"}], status="Actionable",
+        )
+        _mk_result(session, run.id, "T3", sector="Technology", themes=[], status="Actionable")
+        for ticker in ("T1", "T2", "T3"):
+            _insert_prices(session, ticker, _linear_series(200), ASOF)
+        payload = build_xray_payload(session, cfg, ["T1", "T2", "T3"], ASOF)
+    by_slug = {e["slug"]: e for e in payload["theme_concentration"]}
+    assert by_slug["ai"]["count"] == 2
+    assert by_slug["cloud"]["count"] == 1
+    assert by_slug["ai"]["pct"] == pytest.approx(2 / 3)
+    assert "cloud" in by_slug and "ai" in by_slug and len(payload["theme_concentration"]) == 2  # T3 contributes nothing
+
+
+# --- determinism ----------------------------------------------------------------------------------
+def test_determinism_byte_identical_regardless_of_input_order(tmp_path):
+    cfg = load_config()
+    engine = _engine(tmp_path, "det.db")
+    aaa = _linear_series(200, start=100.0, step=1.0)
+    bbb = [2.0 * v for v in aaa]
+    with Session(engine) as session:
+        run = _mk_run(session, ASOF)
+        _mk_result(session, run.id, "AAA", sector="Technology", themes=[], status="Actionable")
+        _mk_result(session, run.id, "BBB", sector="Health Care", themes=[], status="Avoid")
+        _insert_prices(session, "AAA", aaa, ASOF)
+        _insert_prices(session, "BBB", bbb, ASOF)
+        first = build_xray_payload(session, cfg, ["BBB", "AAA"], ASOF)  # reversed input order
+        second = build_xray_payload(session, cfg, ["AAA", "BBB"], ASOF)
+    assert first == second
diff --git a/apps/frontend/components/correlation-heatmap.tsx b/apps/frontend/components/correlation-heatmap.tsx
new file mode 100644
index 0000000..56d5e0b
--- /dev/null
+++ b/apps/frontend/components/correlation-heatmap.tsx
@@ -0,0 +1,93 @@
+import { cn } from "@/lib/utils";
+import type { WatchlistXray } from "@/lib/api";
+
+/**
+ * J-23 (backlog B-204) — the pairwise return-correlation matrix inside the watchlist X-ray.
+ *
+ * READ-ONLY presentation of `xray.correlation_matrix`, served verbatim by `GET /api/watchlist` — NO
+ * browser-side correlation recompute (B-204's named dominant failure mode). Cells reuse the app's
+ * EXISTING sign tokens (`text-pos` / `text-neg` / muted), the SAME family `price_since_added` already
+ * uses on this page — never a new color scale. An undefined/insufficient-history pair renders an
+ * honest NA cell (`—`, muted, dashed border) rather than a fabricated number.
+ */
+
+function fmtCorr(value: number | null): string {
+  if (value === null || value === undefined) return "—";
+  return value.toFixed(2);
+}
+
+function cellTextClass(value: number | null): string {
+  if (value === null || value === undefined) return "text-text-faint";
+  if (value > 0) return "text-pos";
+  if (value < 0) return "text-neg";
+  return "text-text-muted";
+}
+
+function cellTitle(rowTicker: string, colTicker: string, value: number | null, xray: WatchlistXray): string {
+  if (rowTicker === colTicker) {
+    return `${rowTicker}: ${xray.history_days[rowTicker] ?? 0} of ${xray.window_days} trailing days available`;
+  }
+  if (value === null) {
+    const rowDays = xray.history_days[rowTicker] ?? 0;
+    const colDays = xray.history_days[colTicker] ?? 0;
+    return (
+      `${rowTicker} vs ${colTicker}: not enough overlapping history for a correlation ` +
+      `(${rowTicker}: ${rowDays}d, ${colTicker}: ${colDays}d of the trailing ${xray.window_days}d window; ` +
+      `need >= ${xray.min_overlap_days}d each)`
+    );
+  }
+  return `${rowTicker} vs ${colTicker}: ${value.toFixed(3)} correlation over the trailing ${xray.window_days} trading days`;
+}
+
+export function CorrelationHeatmap({ xray }: { xray: WatchlistXray }) {
+  const { tickers, correlation_matrix } = xray;
+  return (
+    <div className="overflow-x-auto" data-testid="watchlist-xray-matrix">
+      <table className="w-full border-collapse text-xs">
+        <thead>
+          <tr>
+            <th className="px-2 py-1 text-left">
+              <span className="sr-only">Ticker</span>
+            </th>
+            {tickers.map((ticker) => (
+              <th key={ticker} className="num px-2 py-1 text-center font-medium text-text-muted">
+                {ticker}
+              </th>
+            ))}
+          </tr>
+        </thead>
+        <tbody>
+          {tickers.map((rowTicker) => (
+            <tr key={rowTicker}>
+              <th scope="row" className="num px-2 py-1 text-left font-medium text-text-muted">
+                {rowTicker}
+              </th>
+              {tickers.map((colTicker) => {
+                const value = correlation_matrix[rowTicker]?.[colTicker] ?? null;
+                const isSelf = rowTicker === colTicker;
+                return (
+                  <td
+                    key={colTicker}
+                    data-testid="watchlist-xray-cell"
+                    data-row={rowTicker}
+                    data-col={colTicker}
+                    data-na={value === null ? "yes" : "no"}
+                    title={cellTitle(rowTicker, colTicker, value, xray)}
+                    className={cn(
+                      "num border px-2 py-1 text-center tabular-nums",
+                      isSelf ? "bg-surface-2" : "bg-surface",
+                      value === null ? "border-dashed border-border" : "border-border",
+                      cellTextClass(value),
+                    )}
+                  >
+                    {fmtCorr(value)}
+                  </td>
+                );
+              })}
+            </tr>
+          ))}
+        </tbody>
+      </table>
+    </div>
+  );
+}
```
