# goal-mcp-loop-iter-36 — User-Visible Changes

**Phase:** goal-mcp-loop-iter-36
**Date:** 2026-07-14
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now open a brand-new page, `/research/referee-audit`, and see whether the platform's own statistical certifier is itself trustworthy — a "who audits the auditor" report that completes the Research hub's governance section at 4 of 4 cards.
- Users can see the certifier's empirical false-pass rate — how often it wrongly calls a deliberately meaningless ("null") pattern real — measured over 200 seeded trials, together with its 95% confidence interval, shown right next to the configured significance threshold (α) it is supposed to respect. Right now, with the real data on record, this reads: false-pass rate **0.08** (16 of 200 trials), 95% CI **[0.04984, 0.126]**, against α = **0.05**.
- Users can see whether an intentionally "cheating" factor — one whose value is literally its own future outcome, the "perfect crime" a broken certifier would rubber-stamp — was caught and rejected, labeled "expected: rejected" next to the actual verdict badge. Right now, with the real data on record, the run shows this factor was **NOT caught** (verdict: PASS) — the page renders this as a prominent, un-missable red "tripwire" warning card, never a quiet pass.
- Users can see the run date and run parameters behind the currently-displayed report — right now: run date **2026-07-01**, seed **20240601**, contaminated-factor horizon **5 days**, source factor **leadership_score**.
- Users can reach this new page from a brand-new 4th card, "Referee audit," in the `/research` hub's existing "Governance & process" section — clicking it navigates to `/research/referee-audit`. That section (previously 3 cards: Pre-registration registry, Negative-results graveyard, Certification-budget accounting) now shows 4.
- If the backend is unreachable, users see a contained "Backend unavailable" card on the page instead of a broken or blank page, with the rest of the site's navigation still intact.

No new *interactive* capability was added — this is a fully read-only report. There is no button, form, or setting anywhere in the product to trigger the underlying audit; it runs only as an offline, config-seeded job an operator runs from the command line, and the page always re-reads whatever that job last wrote.

---

## What Changed in the Visible UI

- `/research` now shows a 4th card in the "Governance & process" grid: **"Referee audit"** (shield-check icon), positioned immediately after the existing "Certification-budget accounting" card — identical border/hover/focus styling to its three siblings. The three existing cards did not move or change.
- New page `/research/referee-audit`: a page heading and subtitle explaining the check, a 4-stat summary row (null trials + source factor · false-pass rate + count + CI · configured α · run date + seed/horizon), and below it a single verdict card that is either a quiet, green-icon confirmation ("correctly rejected") or — as is the case with the real data currently on record — a loud red "tripwire" card stating the contaminated factor was **NOT** rejected and that certified claims from this basis should be treated with suspicion.
- The verdict badge next to the contaminated-factor result never uses the same visual style as a "Proven" claim elsewhere in the product — even when the verdict is technically "PASS" (as it is right now), the badge renders in the same red/danger styling as a failure, because a PASS on this deliberately-cheating factor is a red flag, not a proof of anything.
- Two further states exist on the same page for data conditions not currently on record: an "No audit run yet" honest-empty message, and an amber "artifact exists but could not be parsed" degraded state — both built and available, neither is what a user sees today given the real persisted artifact.

---

## What Old Behavior Changed

None. This phase is purely additive:
- No existing page's rendered values, layout, or navigation changed.
- No existing API endpoint's response shape changed.
- The three existing "Governance & process" cards (registry, graveyard, budget) are visually and behaviorally identical to before — only the section's explanatory code comment and the grid's card count grew.
- The site-wide "is today's board trustworthy" preflight banner is **unaffected** by this phase — unlike iter-35's drift check, this audit was confirmed NOT wired into the banner's underlying `compute_preflight`/`readiness` logic; it lives entirely on its own isolated report page.
- The real evidence ledger (`/evidence`), the real Thresholdout budget (`/research/budget`), the pre-registration registry, and the negative-results graveyard are all confirmed unchanged by this phase — the dev handoff reports the three real ledger files byte-identical before/after the audit ran, and `/api/evidence` still shows the same 0 PASS / 7 FAIL it showed before this phase.

---

## Not Visible Yet

- The audit run itself (`python -m app.engine.referee_audit`) has no UI trigger anywhere in the product — by design, this is a read-only panel. A user cannot re-run or refresh the calibration check from the product; that stays a command-line/operator action.
- `TRENDORA_REFEREE_AUDIT_PATH` (an optional environment variable that repoints which artifact file the panel reads) is a deployment-only lever — there is no in-app setting to change it, consistent with the rest of this product having no admin-settings screen.
- The backend computes and serves one field — `n_insufficient_null` (how many of the 200 null trials came back "insufficient data" rather than a clean pass/fail) — that is fully present in the API response and the frontend's type definitions, but is not displayed anywhere on the page. This does not violate anything the phase specification required (the required fields — trial count, false-pass rate + CI, α, verdict, run date/params — all do render), but it is a backend-computed value with no current UI element. In the real, live artifact this value happens to be 0, so nothing is visibly being hidden today, but the field itself has no display slot for a future run where it is nonzero.
- Two related ideas mentioned in this iteration's backlog card — a "referee-settings sweep" reusing this same harness, and further audit-enrichment work — were not built in any form this iteration (not even as unwired backend code). They remain future work, not a hidden capability of this phase.
