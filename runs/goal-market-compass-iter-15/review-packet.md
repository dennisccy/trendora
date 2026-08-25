# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 1. Shown in full: 1.

```diff
diff --git a/docs/goal.md b/docs/goal.md
index 85300d83..90ba53a3 100644
--- a/docs/goal.md
+++ b/docs/goal.md
@@ -1659,6 +1659,34 @@ manifest artifact (it must be self-describing and self-caveating).
     convention matches, never written and never used to repair anything. Every other bound is
     unchanged (the same two dates, the same proven-missing rows, fail-closed, idempotent,
     self-closing on verification). A third vendor requires a new dated amendment.
+  - **Dated exception #2 — AVB convention diagnostic (owner, 2026-08-25 — single-use, self-closing,
+    DIAGNOSTIC ONLY).** J-11 Stage D readiness is blocked at **AVB-D** because the persisted J-10
+    evidence kept close-comparison data but **discarded the corresponding provider volume**, so the
+    price/volume convention for AVB's two recovered bars cannot be settled from anything already on
+    disk. This authorizes **exactly one** bounded, read-only comparison fetch to settle it, and
+    **nothing else**:
+    - **Symbol:** `AVB` only. **Dates:** exactly `2026-08-05, 2026-08-06, 2026-08-07, 2026-08-10,
+      2026-08-11, 2026-08-12` — six dates, no others, none inferred from a range or cadence.
+    - **Fields:** `date`, `close`, `volume` only. Use the **canonical Yahoo provider path Trendora
+      already uses**, so the comparison is like-for-like; vendor is `yahoo` (the vendor addendum above
+      also permits `stooq`, but **no retry into another provider** is authorized here beyond that).
+    - **Purpose:** compare provider close and volume against the already-stored Trendora close and
+      volume and the persisted J-10 bridge factor, to determine whether the stored representation is
+      raw+raw, bridged price + raw volume, bridged price + compensating volume, or indeterminate.
+    - **This is NOT ingest and NOT recovery.** No write to `daily_prices` or **any** database table; no
+      persistence, no backfill, no repair, no normalization, no "improvement" of AVB data, no dataset
+      advancement, no population-wide fetch. **J-10 is NOT reopened** — its own exception stays
+      exhausted and this amendment grants it nothing. The observations live **only** in a new
+      iteration-15 evidence artifact outside the database.
+    - **Auditable provenance required** in that artifact: provider, symbol, requested dates/window,
+      raw returned close, raw returned volume, capture timestamp, the bridge factor used, and the
+      comparison formulas applied.
+    - **Fail closed.** If the provider cannot supply sufficient evidence, classify honestly as
+      **AVB-D** and stop — do not guess, do not substitute adjacent-day statistics for the direct
+      comparison, and do not broaden the fetch to make an answer available.
+    - **Exhausted** the moment that comparison artifact is written. Normal AG-9 applies again
+      automatically; any later live fetch, **including of these same six dates**, requires a new dated
+      amendment. This is not a standing "diagnostic fetch allowed" path.
 - **AG-10 — Host resource ceiling (hardware protection), carried from ops-hardening:** heavy compute MUST be
   launched only via the project launch scripts, which MUST apply the host caps declared in
   `project-extensions/host-guard/host-guard.env` whenever present (CPU-affinity mask, BLAS/OMP thread caps)
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-market-compass-iter-15/status.json       |  4 +-
 .../state/assumptions.md                           | 92 ++++------------------
 .../state/assumptions.md.archive.md                | 79 +++++++++++++++++++
 runs/goal-session-market-compass/state/lessons.md  | 24 +-----
 .../state/lessons.md.archive.md                    | 33 ++++++++
 runs/goal-session-market-compass/telemetry.jsonl   | 15 ++++
 runs/goal-session-market-compass/trace/.next-step  |  2 +-
 runs/goal-session-market-compass/trace/trace.jsonl |  3 +
 8 files changed, 151 insertions(+), 101 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
