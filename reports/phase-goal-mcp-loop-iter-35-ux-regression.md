# Phase goal-mcp-loop-iter-35 — UX Regression Review

**Date:** 2026-07-14

**Verdict:** UX-REGRESSION-PASS

---

## New Capability Discoverability

| Capability | Path from home (`/`) | Clicks | Assessment |
|---|---|---|---|
| `DriftReportPanel` card on `/data` | Sidebar → "Data Manager" (`href="/data"`, confirmed present in `apps/frontend/components/sidebar.tsx:44`, unchanged this iteration) → card is inline in the page's existing vertical panel stack, no scroll-gated tab/accordion | 1 | Discoverable. `/data` is J-13's already-registered nav home; the card needs no extra navigation beyond what J-13 already established. |
| Site-wide preflight banner showing the drift reason | None — `PreflightBanner` is mounted once in `apps/frontend/app/layout.tsx:47` alongside `Sidebar` (`layout.tsx:36`), so it renders on every route automatically | 0 | Maximally discoverable — confirmed live on `/` and `/stocks` without visiting `/data` first (browser-qa UT-07). |
| Explanatory copy for what the drift check does | Directly under the card title, always rendered | 0 | Verified in code: `PanelTitle`'s `hint` prop (`apps/frontend/app/data/page.tsx:549-556`) renders as a plain `<p>` beneath the `<h2>`, not a hover-gated tooltip. Browser-qa UT-13 independently confirms this ("present in the DOM without any hover/click simulated... it is plain static text, not a tooltip"). **Note:** `reports/phase-goal-mcp-loop-iter-35-user-visible-changes.md` (line 14) describes this as something "Users can hover... for an explanatory tooltip" — that phrasing is inaccurate; the real behavior is strictly more discoverable (zero-interaction, always-visible text) than a hover tooltip would be. Net effect on users is positive; flagged only as a documentation-accuracy nit, not a UX defect. |
| Label clarity | "Live-vs-seed drift" heading + full-sentence explanation ("Byte/fixed-precision compares the last N dates a Fetch job returns against the committed seed...") | — | Matches the technical-but-explained register already established on this page (`Storage footprint`, `Rebuild snapshots for current universe`). Appropriate for this product's operator/analyst persona; no consumer-facing ambiguity. |

No new controls were added (read-only report), so there is no action/button discoverability to assess — confirmed by both `user-visible-changes.md` and a direct read of the component (no `<button>`/`<form>` in `DriftReportPanel`).

### Visual consistency

- `DriftReportPanel` reuses the page's existing `Card`/`PanelTitle` components (same pattern as `StorageCapacityPanel`, `RebuildPanel`) — confirmed via diff, no new one-off layout primitives.
- Token usage confirmed against the diff: `text-pos` for clean (with the same `h-1.5 w-1.5 rounded-full bg-pos` dot `PreflightBanner`'s own GO strip uses), `border-warn bg-warn/10 text-warn` for drift/unreadable — byte-identical class combination to `preflight-banner.tsx`'s `LoudBanner` DEGRADED treatment (`components/preflight-banner.tsx:72`). No arbitrary hex/pixel values introduced.
- Severity-to-color mapping is correct: `config.yaml`'s `readiness.severity.drift: degraded` (not `no-go`) correctly corresponds to amber (`border-warn`) styling in both the card and the banner, not the red `border-neg` NO-GO treatment — verified in both the config diff and the component code.
- This is visually consistent with prior-phase pages; no deviation from the established DESIGN SYSTEM tokens found.

---

## Regression Risk

| Shared component | Prior feature it serves | This iteration's change | Risk |
|---|---|---|---|
| `apps/frontend/components/preflight-banner.tsx` | J-20 (site-wide trust banner, built iter-33) | **Zero file diff** (confirmed via `git diff HEAD --stat`) — behavior changes only because the backend payload it already renders generically now carries a 4th possible reason string | Low. This is the banner working exactly as iter-33 designed it (generic `reasons.map()`, no hardcoded strings) — confirmed live: UT-07 (new reason appears verbatim, cross-page), UT-08 (recovers to GO), UT-09 (byte-identical GO-with-zero-reasons when the new artifact is absent, the load-bearing non-regression property). |
| `apps/frontend/components/readiness-provider.tsx`, `apps/frontend/app/layout.tsx`, `apps/frontend/components/sidebar.tsx` | J-20 banner mount point; global nav (all journeys) | **Zero file diff**, confirmed | Low. |
| `apps/frontend/app/data/page.tsx` (existing panels: Dataset coverage, Storage footprint, Rebuild snapshots, Job progress) | J-13 (`/data` Data Manager home) | Purely additive insert (`+70/-0` lines) — new `DriftReportPanel` slotted between `StorageCapacityPanel` and the `RebuildPanel`/coverage-diagnostic banner; no existing card moved, restructured, or removed | Low. Verified live: UT-10 confirms exact heading order `Dataset coverage → Storage footprint → Live-vs-seed drift → Rebuild snapshots...` and all 7 coverage tiles still present. |
| `app/engine/readiness.py::compute_preflight` | J-20 (feeds the banner via `/api/health`) | New 4th `_apply("drift", ...)` component added after `integrity`; servability/freshness/integrity composition confirmed untouched | Low. Backend regression tests (`test_readiness.py`, 24/24 passing per QA report) explicitly re-verify worst-severity composition across all four components and that an absent/clean drift artifact leaves `ok=True`. |
| `app/engine/data_manager.py::_run_job` / `_run_chunked_fetch` | J-16 (Fetch job pipeline) | New `overlap_sink` accumulator threaded through the chunked-fetch loop + new `_check_drift` post-fetch stage, gated to run only on a genuinely-completed fetch (not on `resumable` pause or skip-fetch/backfill-only resume) | Medium code-surface / Low observed risk. This is the one file in this diff that touches core fetch-pipeline control flow rather than being purely additive. Mitigated by 4 new dedicated wiring tests in `test_data_manager_jobs_pipeline.py` (18/18 passing per QA report, explicitly asserting the stage fires on completion and does NOT fire on the two paths where it must stay inert) and by the byte-identity DoD check (fresh-seed/no-fetch state leaves preflight, `/api/health`, and the other three components identical to iter-34's baseline). **Residual note (not a confirmed regression):** browser-qa's drift-state tests (UT-03/04/05/06) exercised the UI by writing the drift-report JSON artifact directly rather than by clicking the `/data` page's actual "Fetch" job control and observing a live provider call complete end-to-end. The backend wiring is proven by integration tests; the UI rendering is proven by direct artifact injection; but no single browser-driven observation this iteration captured the full "operator clicks Fetch → job completes → card updates" click-path for the new stage specifically. Worth a spot-check in a future iteration's QA pass, not blocking here. |
| `app/config.py::ReadinessCfg._validate` | All journeys (boot-time config gate) | `required_components` extended to include `"drift"` | Low. Verified via `test_config.py` (68/68) and `test_config_engine.py` (46/46) per the QA report, plus a live service boot (browser-qa's Finding 1 rebuild + subsequent 14/14 passing tests prove the app boots and serves correctly with the extended config). |
| `GET /api/data` (`app/api/data.py::data_overview`) | J-13 | Additive `"drift"` key only | Low. `test_api_data.py` 45/45 passing including 2 new drift-field tests; UT-14 confirms the existing backend-unavailable fallback path is unaffected (drift testids simply absent, no partial/broken fragment). |
| J-01 (`/stocks` leaderboard), J-05 (`/evidence` ledger page) | Unrelated journeys | No files on these pages' code paths appear in this iteration's diff | None. Confirmed live and unaffected: UT-11 (1623 evidence badges, banner GO), UT-12 (7 claim rows, ledger file line count unchanged at 7 — confirms this iteration wrote no new ledger entry, consistent with the DoD's "no Evidence Claim" scope). |

No confirmed regression in any prior-phase user journey.

---

## UI vs Backend Parity

`reports/phase-goal-mcp-loop-iter-35-implementation-summary.md` states "Backend-Only Items: None" — independently verified by reading the code:

| Backend capability | UI exposure |
|---|---|
| `app.engine.drift.build_drift_report` / `write_drift_report` (new comparator, fetch-pipeline-triggered) | Surfaced via the single `read_drift_report()` reader, consumed verbatim by both readers below — no third path. |
| `compute_preflight`'s new `drift` component | Surfaced site-wide via `PreflightBanner`'s generic `reasons` list (0-click visibility, every page). |
| `GET /api/data`'s additive `drift` field | Surfaced via the new `DriftReportPanel` card on `/data` (1-click visibility from home). |
| `config.yaml`'s `data_quality.drift.overlap_days: 20` | Rendered verbatim in the clean-state card copy ("...last 20 common date(s)") — confirmed not hardcoded (UT-04 explicitly checks this ties to config, and UT-06 confirms a null value degrades to an em-dash rather than a stale hardcoded number). |
| `config.yaml`'s `readiness.severity.drift: degraded` | Correctly drives amber (not red) styling in both the card and the banner (see Visual consistency above). |

The one backend-only lever is `data_quality.drift.enabled` (an on/off switch with no in-app admin toggle). This is consistent with the rest of the product, which has no admin-settings screen anywhere — every other operational knob (freshness thresholds, severities, overlap window, etc.) is also config-only. `user-visible-changes.md` discloses this explicitly rather than glossing over it. Not treated as a gap.

No UI capability outruns what the backend actually computes, and no backend capability is silently withheld from the UI. Full parity.

---

## Flags

### Hidden Capabilities
None.

### Undiscoverable Capabilities
None. Both new surfaces (the `/data` card and the banner's new reason) are reachable in ≤1 click from home, and the banner surface requires 0 clicks.

### Potential Regressions
None confirmed. See the Regression Risk table above for the one residual, non-blocking note: the Fetch-job UI trigger's full live click-path was not separately exercised by browser-qa this iteration (drift states were tested via direct artifact injection instead of triggering a real Fetch job through the job panel), though the underlying pipeline wiring is proven by dedicated backend integration tests. Recommend a live-Fetch-job UI spot-check in a future iteration touching this area, not a blocker for this one.

### Visual Consistency
- New `/data` card matches the established `Card`/`PanelTitle` pattern and reuses exact pre-existing tokens (`text-pos`, `border-warn`, `bg-warn/10`, `text-warn`) — no arbitrary values.
- Severity→color mapping (`degraded` → amber, not red) is correctly wired end-to-end from `config.yaml` through to both the card and the banner.
- Minor documentation nit (not a UX defect): `user-visible-changes.md` characterizes the card's explanatory copy as a "hover... tooltip," but it is actually always-visible static text (verified in code and by browser-qa UT-13) — the real implementation is more discoverable than that description implies, not less.

---

## Recommendation

No action required for this phase to ship. Two non-blocking notes for future reference (neither changes the verdict):
1. Correct the "hover for tooltip" phrasing in `user-visible-changes.md` to "always-visible explanatory text" the next time that report is touched, so future readers don't undersell the feature's discoverability.
2. In a future iteration that revisits the Fetch-job UI, consider a browser-qa pass that drives the actual "Fetch" job control end-to-end (rather than injecting the drift-report artifact directly) to close the residual gap between "the wiring is unit/integration-tested" and "an operator clicking Fetch in the browser was observed producing the card update."
