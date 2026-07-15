# Phase goal-mcp-loop-iter-36 — UX Regression Review

**Date:** 2026-07-15

**Verdict:** UX-REGRESSION-PASS

---

## New Capability Discoverability

| Capability | Path from home (`/`) | Clicks | Assessment |
|---|---|---|---|
| `/research/referee-audit` page | Sidebar → "Research" (`apps/frontend/components/sidebar.tsx:38`, `href="/research"`, unchanged this iteration, mounted globally in `layout.tsx`) → new "Referee audit" card in the "Governance & process" grid | 2 | Discoverable. Matches the exact click-depth of its 3 siblings (registry/graveyard/budget), confirmed live by browser-qa UT-10 (`window.location.href` verified `/research/referee-audit` after the click, full content loaded). |
| 4th "Referee audit" card on `/research` | Same page, appended after "Certification-budget accounting" in the existing `Governance & process` grid (`data-testid="research-governance-link-referee-audit"`) | 0 (already on the hub) | Confirmed via diff (`git diff HEAD -- apps/frontend/app/research/page.tsx`): purely additive — new icon import (`ShieldCheck`) + one new `<Link>` block appended after the existing budget card; the other 3 cards' JSX is byte-identical. Browser-qa UT-11 independently confirms all 3 siblings still navigate correctly and the new card is 4th, own row, not inserted between existing cards. |
| Stat grid / verdict content on the new page | Renders automatically on page load, no further interaction needed | 0 | All 4 stat cards + the verdict card (tripwire or calm) render without any user action — read-only by design, confirmed by both the spec ("New user actions: none") and browser-qa UT-03/UT-04. |
| Label clarity | "Referee audit" heading, shield-check icon; card description "Is the certifier itself calibrated? ..." | — | Consistent register with the 3 sibling cards ("Pre-registration registry," "Negative-results graveyard," "Certification-budget accounting") — all use the same technical-but-explained voice appropriate to this product's quant/analyst audience. No label-vs-function mismatch: the page does exactly what the card promises (false-pass rate, CI, α, tripwire verdict). |

No new interactive controls were added (fully read-only report; the underlying audit job runs offline via CLI, never a UI action) — confirmed in code (no `<button>`/`<form>` in `apps/frontend/app/research/referee-audit/page.tsx`) and explicitly disclosed in `user-visible-changes.md`. There is therefore no action/button discoverability gap to assess.

### Visual consistency

- Page shell (`space-y-4` → `space-y-2` wrapper, `BackToResearch` link, `PageHeading`) is structurally identical to `research/budget/page.tsx`, `research/graveyard/page.tsx`, and `research/registry/page.tsx` (verified via grep across all four files — same `space-y-4`/`space-y-2`/`PageHeading` shape).
- "Backend unavailable" card uses `border-neg bg-surface p-5 text-sm text-neg` — **byte-identical class string** to `research/budget/page.tsx:56` and `research/graveyard/page.tsx:61`. No new one-off error-state pattern invented.
- The tripwire failure card's `border-neg bg-neg/10` treatment is not a novel invention either — it is the exact same class pair the site-wide `PreflightBanner`'s own NO-GO state uses (`components/preflight-banner.tsx:72`: `isNoGo ? "border-neg bg-neg/10 text-neg" : ...`). This is a well-judged reuse: the new page borrows the platform's most severe existing visual vocabulary for its own most severe state, rather than introducing a new "danger" idiom.
- The amber "unreadable artifact" state (`border-warn bg-warn/10`) matches the exact token pair `app/data/page.tsx` uses for its own drift-unreadable degraded states (lines 826, 850).
- `contaminatedStatusVariant()` deliberately never returns `"accent"` (the color reserved for "Proven" elsewhere, e.g. `evidence-status-badge.tsx`) — confirmed in source and independently by browser-qa UT-05 via a full design-token cross-check (`--accent` teal vs `--neg` red, disjoint). This is the one place a naive implementation could have leaked proven-looking styling onto an anti-goal-sensitive badge, and it was avoided correctly.
- No arbitrary hex/pixel values found in the new page; all styling routes through existing Tailwind design-system utility classes already used elsewhere in the governance cluster.

---

## Regression Risk

| Shared component | Prior feature it serves | This iteration's change | Risk |
|---|---|---|---|
| `apps/frontend/app/research/page.tsx` | J-18 (registry, iter-30), J-19 (graveyard, iter-31), J-17 (budget, iter-32) — the 3 existing governance cards | `git diff HEAD` shows `+34/-4` lines: a comment update + 1 new icon import + 1 new `<Link>` card block appended after budget's. The existing 3 cards' JSX is untouched byte-for-byte. | Low. Confirmed additive-only by diff inspection; confirmed live by browser-qa UT-11 (all 3 siblings still navigate to their correct pages with matching headings, order preserved). |
| `apps/frontend/lib/api.ts` | Every journey that calls a `fetch*` helper from this file (most of the product) | `git diff HEAD` shows purely additive: new type imports/re-exports + one new `fetchRefereeAudit()` function appended after `fetchBudget()`. No existing function body modified. | Low. Confirmed by diff; no existing exported symbol changed signature or behavior. |
| `apps/backend/app/config.py` (`ResearchCfg`) | All journeys (shared boot-time config object) | New `referee_audit: RefereeAuditCfg` field with `default_factory`, mirrors `DriftCfg`'s exact iter-35 pattern (nested, default-populated, `extra="allow"`, boot-validated). A config file predating this block still loads unchanged. | Low. Purely additive field; no existing `ResearchCfg` field touched. Backend regression run (`test_config.py`, `test_config_engine.py` + 251 tests across the governance/referee/drift test files together, per the dev handoff) reported 0 failures. |
| `apps/backend/main.py` | Router wiring for every existing endpoint | One new import + one new `include_router(referee_audit.router, ...)` line, placed immediately after the existing `budget.router` registration. No existing router registration touched. | Low. |
| Site-wide `PreflightBanner` / `readiness-provider.tsx` / `layout.tsx` | J-20 (iter-33) — single daily preflight verdict on every page | **Zero file diff** (confirmed: these files do not appear in `git diff HEAD --stat`, and `grep -rn "referee_audit\|RefereeAudit"` across `readiness.py` + all three frontend files returns zero matches). The referee-audit report is deliberately NOT wired into `compute_preflight` — it is a one-off calibration check on the certifier itself, not a daily data-freshness signal, so this is the architecturally correct boundary, not an oversight. | None. Confirmed live by browser-qa UT-12: the "GO" banner renders identically (single instance, correct text) on `/research/referee-audit`, `/research`, `/evidence`, and `/research/budget`. |
| `/evidence` page + the 3 real ledger files (`certified-claims.jsonl`, `staging-ledger.jsonl`, `pre-registrations.jsonl`) | J-03/J-05/J-11 (evidence ledger, honest-marking, re-certification invariant) | New isolated harness writes only to a throwaway `ledger_path`; the real files are never opened for writing per the dev handoff and per `git diff HEAD` on those 3 paths being empty. | Low. Independently corroborated three ways per browser-qa UT-13: (1) `/evidence` still shows exactly 7 FAIL / 0 PASS rows, (2) `git diff HEAD` on all 3 real ledger files is empty, (3) `/research/budget` still reads "Total trials to date: 7 / Bonferroni divisor 8" — if the 200+1 audit trials had leaked into the canonical ledger, this counter would have moved. |

**Evidence-trail gap worth flagging for the auditor (not a code-level regression):** the phase spec's DoD explicitly requires the 8-journey required-still-passing set (J-01, J-03, J-05, J-11, J-17, J-18, J-19, J-20) to be "LIVE-re-verified via the browser-qa lane" this iteration. The actual dispatched browser-qa test plan (UT-01–UT-13) is scoped to J-22 and its directly-touched regression surfaces (governance cards, preflight banner, evidence-ledger isolation) — it does **not** contain a live navigation to `/stocks`, which is the page J-01 ("every score shows an evidence status") and J-11 (the stale-proven-edge invariant) both depend on. The browser-qa report itself flags this explicitly and defers the closure decision to the auditor/goal-evaluator rather than fabricating coverage. Weighing this against actual risk: `/stocks`, `app.engine.evidence`, and every stock-scoring code path are **absent from this iteration's diff** (only `config.py`, `main.py`, `research/page.tsx`, and `api.ts` were touched, none of which `/stocks` depends on), so the code-level regression risk to J-01/J-11 is genuinely low — this reads as a verification-coverage gap on journeys the diff never touches, not a suspected functional break. J-03/J-05/J-17/J-18/J-19/J-20 all received at least partial live corroboration this iteration (UT-09, UT-11, UT-12, UT-13). Golden-replay scripts exist for all 8 journeys and `journey-history.json` currently records all 8 as `"status": "passing"` (last verified iter-34/iter-35). Recommend the auditor either dispatch one supplemental live `/stocks` check or explicitly invoke the DoD's own documented fallback ("the closure one-liner replay run inline") before closing the iteration — not a blocker for this UX review's verdict given the low code-level risk.

No confirmed regression in any prior-phase user journey.

---

## UI vs Backend Parity

| Backend capability | UI exposure |
|---|---|
| `app.engine.referee_audit.build_referee_audit_report` (null-trial count, false-pass rate, binomial CI, α, contaminated verdict, run date, run params) | Surfaced verbatim via the single `read_referee_audit_report()` reader → `GET /api/research/referee-audit` → `fetchRefereeAudit()` → the stat grid + verdict cards. Confirmed single-source (no second recompute path) both in the endpoint's own docstring and by browser-qa UT-03 (`curl`-cross-checked against the live page). |
| `n_null_trials`, `seed`, `contaminated_factor_horizon` (config-sourced) | Rendered verbatim in the stat grid's subtext ("200", "seed 20240601", "contaminated horizon 5d") — confirmed by UT-03. |
| Contaminated-factor tripwire (`contaminated_caught`) | Surfaced as either the loud red `TripwireCard` or the calm `CalmContaminatedCard`, never hidden — confirmed live for the real (tripwire) state by UT-04 and for the fixture (caught) state by UT-06. |
| Honest empty / unreadable-artifact states | Both built and surfaced with visually distinct treatment (plain card vs. amber card) — confirmed live by UT-07/UT-08. |
| `n_insufficient_null` (count of null trials that came back "insufficient data") | **Computed and typed, not displayed.** Present in `apps/backend/app/engine/referee_audit.py` (report field, lines 107/241/266/333/350/367) and in the frontend's `RefereeAuditResponse` type (`apps/frontend/lib/referee-audit.ts:41`), but no JSX in `page.tsx` reads or renders it. This is a genuine backend-to-UI gap, but a minor one: it is not among the DoD's required displayed fields (trial count, false-pass rate + CI, α, verdict, run date/params — all of which do render), the real persisted artifact's value is currently `0` (so nothing is visibly being suppressed today), and `user-visible-changes.md` already self-discloses this exact gap rather than glossing over it. Not blocking; worth a 1-line addition to the stat grid's false-pass-rate subtext in a future touch of this page if a run ever produces a nonzero value operators would want to see without reading the JSON artifact directly. |
| `TRENDORA_REFEREE_AUDIT_PATH` env override | Deployment-only lever, no in-app setting — consistent with the rest of the product (no admin-settings screen anywhere; every other operational knob, e.g. `TRENDORA_DRIFT_REPORT_PATH` from iter-35, is config/env-only too). Not treated as a gap. |
| Offline audit job trigger (`python -m app.engine.referee_audit`) | No UI trigger anywhere, by design (J-22 is explicitly read-only; "New user actions: none" in both the spec and `user-visible-changes.md`). Not a gap — this is the intended, documented product boundary, identical in shape to how the drift check (iter-35) and every other governance job in this cluster works. |

No UI capability outruns what the backend actually computes. One minor, self-disclosed, non-blocking backend-computed field (`n_insufficient_null`) has no display slot yet.

---

## Flags

### Hidden Capabilities
None. The new page and its nav card are both reachable and were both live-verified reachable by browser-qa.

### Undiscoverable Capabilities
None. `/research/referee-audit` is 2 clicks from home via the persistent sidebar → Research → card, identical click-depth to its 3 already-shipped siblings.

### Potential Regressions
None confirmed by code diff or by browser-qa's live checks. One evidence-trail completeness note (not a code-level regression): J-01 and J-11, both dependent on `/stocks`, received no live browser-qa navigation this iteration despite being named in the DoD's required-still-passing set — see "Regression Risk" above for the full reasoning on why this reads as low actual risk (the diff never touches `/stocks` or the evidence-scoring engine) even though the live-verification artifact the DoD calls for is incomplete as of this review.

### Visual Consistency
- New page fully matches the established governance-page shape (`PageHeading`, `Card`/`CardContent`, identical spacing rhythm) used by budget/graveyard/registry.
- Error/empty/unreadable states reuse byte-identical class strings from sibling pages rather than inventing new ones.
- The tripwire's red treatment deliberately reuses the site's own NO-GO banner color pair, correctly signaling severity through an already-established visual language.
- The contaminated-factor badge correctly avoids the "Proven" (`accent`) color family in all verdict states, including the current real PASS state — the one place this page could have accidentally created an anti-goal violation, and it did not.
- No arbitrary/one-off values found.

---

## Recommendation

No action required for this phase to ship. Two non-blocking notes for the auditor/future iterations:
1. Close the evidence-trail gap on J-01/J-11 before final closure — either a quick supplemental live `/stocks` browser-qa check, or an explicit invocation of the DoD's own documented "closure one-liner replay run inline" fallback — given both journeys are named in this iteration's required-still-passing set but received no live navigation in the dispatched UT-01–13 test plan. Code-level risk is low (diff never touches `/stocks`), so this is a paperwork/evidence closure item, not a suspected defect.
2. Consider giving `n_insufficient_null` a display slot (e.g., folded into the false-pass-rate card's subtext) the next time this page is touched, so a future nonzero run doesn't leave a computed value invisible without reading the raw JSON artifact.
