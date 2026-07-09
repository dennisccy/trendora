# Phase goal-mcp-loop-iter-25 — UX Regression Review

**Date:** 2026-07-09

**Verdict:** UX-REGRESSION-PASS

<!-- PASS: zero new UI surface (confirmed independently — git diff HEAD --stat -- apps/backend
     apps/frontend config.yaml returns empty), so there is nothing new to hide or make undiscoverable.
     The iteration's entire purpose — proving the iter-24 cold-path OOM crash (which broke J-13 and
     failed J-15, a CRITICAL anti-goal #8 violation) is fixed — is backed by fresh, live, non-carried
     canonical browser-qa evidence (two independent cold-restart repros, both clean, backend survived,
     downstream pages loaded, error boundary intact). One evidence-integrity defect was found and is
     flagged below, but it lives in the non-terminal QA lane and does not undermine the canonical
     (terminal) lane's own clean, distinct evidence for the same claim — so it does not change the
     verdict, per this iteration's own two-lane discipline rule. -->

## New Capability Discoverability

**None to assess — by design.** Independently confirmed via `git diff HEAD --stat -- apps/backend apps/frontend config.yaml` (empty output) that this iteration shipped zero source changes. `user-visible-changes.md` and `ui-surface-map.md` both agree: no new page, button, field, panel, or endpoint. The only user-visible delta is the *absence* of a crash under a specific cold-boot sequence — not a discoverable capability, and the reports are honest about this ("Not Visible Yet" section: "There is no on-screen indicator of this fix — nothing new appears anywhere").

- Nothing to flag as hidden or undiscoverable, because nothing new was built.
- The existing "Data Manager" nav entry (from prior iterations) was re-confirmed unchanged and still reachable in 1 click from the Dashboard's persistent left sidebar (browser-qa UT-07, verified via `a[href="/data"]` click + heading assertion, screenshots `UT-07-dashboard-nav.png` / `UT-07-data-manager-reached.png`, distinct md5s). No navigation regression.

## Regression Risk

This iteration exists specifically to re-verify a **confirmed CRITICAL regression from iter-24**: the `mmap_size_bytes=1GB` × 30-connection pool exhausted the 6144 MB `ulimit -v` cap and OOM-crashed the entire backend on the first cold `/data` load after any restart — breaking prior-passing **J-13** and failing target **J-15**. The prior `phase-goal-mcp-loop-iter-24-ux-regression.md` (UX-REGRESSION-FAIL) identified three specific risk items; status of each, checked against this iteration's fresh evidence:

| Shared component / path | Prior feature it serves | iter-24 finding | iter-25 status |
|---|---|---|---|
| `/data` cold-path request (`GET /api/data` → coverage/diagnostic/capacity computation, SQLite pragma+pool config) | **J-13** — Data Manager coverage + availability legend | CRITICAL — confirmed 2/2 crash on cold boot | **RESOLVED, freshly verified live.** `ui-test-results.md` UT-02/UT-03: backend killed, confirmed down (curl code 000), cold-started, readiness confirmed via a non-HTTP port-listening check (preserving true "first request" semantics — the same rigor the iter-13/20/22/24 lesson demands), then `/data` opened as the actual first request. Both runs: real content rendered in ~10.2s/~10.5s (Storage footprint, coverage, heatmap, vendor panel all populated), no blank page, no error card. Two independent reproductions, not a fluke. |
| Whole backend process (every page's API calls) | J-01, J-03, J-04, J-05, J-10, J-12, J-14, and J-15 itself | HIGH — Rust-panic variant could take the whole process down, cascading to every other journey | **RESOLVED, confirmed via downstream check.** Both UT-02 and UT-03 opened `/stocks` immediately after the cold `/data` load and confirmed "541/541" rendered and `curl /api/health` returned 200 afterward — proving the *whole process* survived, not just the one request. All required-still-passing journeys (J-03, J-04, J-05, J-11, J-14) were **freshly live-replayed this run, not carried over** (per the iter-22 lesson embedded in this phase's own notes), and all passed (UT-08–UT-14). |
| `/data`'s error-card boundary (anti-goal #8's "never a blank application-error page") | Existing negative-path contract | Not itself broken, but exercised under crash conditions | **Confirmed still holds.** UT-06: backend stopped and left down, exactly one red-bordered "Backend unavailable" card rendered (verbatim copy match), full page shell/nav intact around it, no duplicate/stacked card, no blank page. |
| `/data` page's readiness-badge / page-content desync (no auto-retry in `loadOverview`) | Pre-existing design gap, newly *exposed* (not caused) by the iter-24 crash | MEDIUM, non-blocking — flagged as follow-up F1 | **Correctly left unaddressed, and correctly disclosed as such.** The phase spec explicitly lists "F1 (`/data` no-retry desync...)" under "Non-blocking follow-ups (do NOT bundle, per iter-24 eval)" — this is deliberate scope discipline, not a dropped ball. Since the crash itself no longer occurs, this specific trigger path can't recur, but the underlying no-retry design gap is still latent for any *other* future transient backend hiccup. Tracked, not silently lost — no action needed this iteration. |

**Components from other prior phases, re-confirmed clean (untouched by this iteration's zero diff, but re-checked live since J-14/J-01/J-10/J-12 required fresh replay):**
- iter-22's `IndexVendorPanel` / chart vendor labels (J-14) — UT-14 fresh live pass, all vendor disclosures present (Stooq/Yahoo/FRED-macro proxy correctly distinguished).
- iter-20's availability-heatmap two-group legend and "Expand universe" removal were **not** re-driven step-by-step this run (the golden script for J-13 was deliberately left unchanged — see `ui-test-results.md`'s "Golden Replay Scripts" section, which explains this iteration's J-13 re-verification was scoped specifically to the cold-path resilience story, not the job-form/legend flow). This is a reasonable, disclosed scoping choice given zero source diff and that no iteration since iter-20 touched the job-form or legend code — residual regression risk here is low, but it means the legend/dropdown itself was not freshly re-observed this run.

## UI vs Backend Parity

| Backend capability this iteration | UI exposure | Status |
|---|---|---|
| None — zero new backend code (the `mmap_size_bytes: 0` fix was already applied and committed in iter-24; this iteration only re-verifies it) | N/A | **Correct parity of "nothing new."** `implementation-summary.md` ("Features Implemented: None... No new screens, buttons, data, or capabilities were added") and `user-visible-changes.md` ("What Users Can Now Do: Nothing new") agree exactly — no gap between what was built and what is claimed visible. |
| The fix itself (removal of the per-connection mmap reservation) | No dedicated UI element (correctly) | **Correctly backend-only, honestly disclosed.** A stability fix that restores previously-intended behavior does not need its own UI affordance; `user-visible-changes.md`'s "Not Visible Yet" section says so explicitly rather than silently omitting it. |

No parity gap. Nothing was built that should have been surfaced and wasn't.

## Flags

### Hidden Capabilities
- None. No new capability was added this iteration.

### Undiscoverable Capabilities
- None. Existing "Data Manager" nav entry re-confirmed at 1 click from home (UT-07).

### Potential Regressions

- **Evidence-integrity defect in the QA lane (not the canonical/terminal lane) — worth correcting, does not block this iteration.** Computed md5 hashes of every screenshot in `reports/qa/goal-mcp-loop-iter-25-evidence/`: `TC-02-storage-card.png` (cited in `reports/qa/goal-mcp-loop-iter-25-qa.md` TC-02, "Storage card values match API payload... PASS") is **byte-for-byte identical** (md5 `3fe10a6b962f65a6a2a858fedf8db22b`) to `UT-06-backend-unavailable.png` — the canonical lane's own screenshot of the *"Backend unavailable"* error card (a genuinely different state: a red-bordered error card, not a populated storage-footprint card). Two screenshots of visually distinct content essentially cannot share an md5 by coincidence, so `TC-02-storage-card.png` is either a stale/reused file or was never actually captured against a loaded storage card. This is exactly the failure mode the project's own carried-forward lesson (iter-11/13/14/15: "never trust a PASS label or DOM-text line alone... a `-fail-`-named frame in the evidence dir invalidates any 'zero blockers' prose") warns against.
  - **Why this does not change the verdict:** the CANONICAL (terminal) lane makes the identical claim — storage-card values matching the live `GET /api/data` capacity payload — with its own distinct, valid evidence: `ui-test-results.md` UT-04, backed by `UT-03-run2-data-fullpage.png` (md5 `54a454a796b9ec5a040b541aa283c9f5`, unique, showing real values: DB file 1.22 GB, Price bars 3,293,160, Scanner rows 166,213, Forward returns 823,409), corroborated independently by `UT-02-run1-data-fullpage.png` (md5 `f8793ca9c4707b91694fa466d21eb371`, also unique). Per this iteration's own explicitly stated two-lane discipline ("the canonical lane is the terminal gate; a QA-lane PASS does not substitute for it"), the reverse holds too: a QA-lane citation defect doesn't invalidate a clean, independently-evidenced canonical PASS on the same claim.
  - **Recommendation:** the QA lane should re-capture or re-cite the correct screenshot for TC-02 before this evidence directory is treated as a clean historical record — a future session or auditor skimming `qa.md` at face value would currently be shown an error card as "proof" of a working storage card.
  - Not flagged as CRITICAL/blocking because (a) it is confined to the non-terminal QA lane, (b) the terminal canonical lane's equivalent evidence is solid and independently verified above, (c) no actual product/UI behavior is called into question — the storage card genuinely works, per the canonical lane.
- **F1 (readiness-badge / `/data` page-content desync after a backend hiccup)** — correctly still open, correctly not addressed this iteration (explicitly listed as a non-blocking P3 follow-up in the phase's OUT OF SCOPE section). Flagged here only so it isn't lost track of: since this iteration removes the ONE trigger that was exposing it (the OOM crash), the desync itself can't currently be observed, but the underlying no-auto-retry gap in `loadOverview` (`page.tsx`) remains for any *future* transient backend failure. No action required now.
- No other shared-component regressions found. `status.json`'s `qa_verdict: PASS` / `blockers: []` this time is **consistent** with the actual resolved state (unlike iter-24's contradictory PASS-while-regressed record) — both the canonical browser-qa lane and the QA lane independently agree the fix holds, and my own md5/timestamp-level spot check of the canonical lane's cold-restart evidence corroborates it.

### Visual Consistency
- **No drift, confirmed independently.** `git diff HEAD --stat -- apps/frontend` is empty — every existing page (`/data`, `/stocks`, `/stocks/{ticker}`, `/evidence`, Dashboard, etc.) is byte-identical to iter-24. No new component, no new color/spacing token, nothing to check against the DESIGN SYSTEM because nothing changed. The `StorageCapacityPanel`/`CoveragePanel`/availability-heatmap components carried forward from iter-20/22/24 render exactly as before (re-confirmed live via UT-01–UT-05 screenshots).
- Carried-forward, out-of-scope tech-debt item (not this iteration's concern, mentioned for continuity only): the coherence-WARN "dead-duplicate `index-regime-chart.tsx` / `major-indexes-card.tsx`" noted in this phase's own OUT OF SCOPE section remains un-deleted, deferred to "a dedicated tidy iteration" as planned — not a UX regression, just a known pending cleanup.

## Recommendation

**No action required to ship this iteration.** The one regression this iteration exists to recover from (the cold-path OOM crash breaking J-13 and J-15) is genuinely fixed and freshly, live-verified by the canonical browser-qa lane with strong, non-carried evidence (two independent cold-restart reproductions, real content, backend survival, downstream page load, error-boundary integrity). Discoverability is unaffected (nothing new was added; existing nav is unchanged and reachable in 1 click). UI/backend parity is exact (nothing built, nothing claimed visible that isn't).

One follow-up worth a lightweight correction, non-blocking:
1. **Re-capture or re-cite `TC-02-storage-card.png` in `reports/qa/goal-mcp-loop-iter-25-qa.md`.** It is currently byte-identical to the canonical lane's `UT-06-backend-unavailable.png` (backend-unavailable error card), not a screenshot of the loaded storage card it's cited to support. The underlying capability is independently and validly proven elsewhere (canonical lane UT-04), so this does not block closure — but the QA-lane record should not stand uncorrected, since it currently misrepresents its own evidence.

Carry-forward reminders (already correctly scoped out of this iteration, not new asks): F1 (`/data` no-retry desync, P3) and the dead-duplicate chart-component cleanup remain tracked for a future iteration.
