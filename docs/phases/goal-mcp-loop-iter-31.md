# Goal Iteration 31 — Negative-results graveyard page (J-19)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** mcp-loop
- **Iteration:** 31
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-19
- **Required-still-passing journeys:** J-01, J-03, J-04, J-05, J-06, J-08, J-09, J-11, J-18
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked values MUST render a "not yet proven" state. *(critical)*
  - **Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha claims; never place or simulate orders. *(critical)*
  - A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation for the same as-of date — not merely that the page renders. *(critical)*
  - **No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of; never introduce lookahead anywhere. *(critical)*
  - No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the post-decompose gate. *(critical)*
  - No hard-coded credentials, API keys, or tokens in source files. *(critical)*
  - **Resilience to data-shape and data-scale change:** widening the data basis (new nulls, broader pools, deeper history) must never crash an existing page or exhaust a service's memory — every existing consumer of a widened field is re-validated, the UI degrades gracefully (contained error boundary, honest "—"/NA placeholder, never a blank application-error page), and unbounded whole-table ORM loads are forbidden on the deep basis. *(critical)*

## GOAL

Ship **J-19**: a `/research/graveyard` page where a user can browse every dead hypothesis — every NON-PASS referee verdict across BOTH the canonical and staging ledgers — with its selectors, verdict kind, date, deflation context, and registration lineage, so nobody (a future model, or the owner in month 9) re-derives a dead idea from scratch.

## BACKGROUND

Per the iter-30 evaluator recommendation, J-19 (backlog **B-902**, EASY, "read-compose from ledgers + registry; page") is the best next target: it reads the pre-registration registry J-18 just built (iter-30, B-901) and consolidates the governance cluster — its dependency (B-901 lineage links) is satisfied and it is now cleanly unblocked (rubric rule 3: an unblocked journey that reuses an existing Data-Contract value + shares a page/nav home). Priority rubric top-down: no journey is regressed (rule 1 n/a); the last coherence verdict was COHERENCE-PASS so no consolidation is owed (rule 2 n/a); J-19 is the smallest ready governance surface and reuses `registry.match_registration` verbatim (rules 3–4). **Depth = full** because this iteration crosses the backend↔frontend boundary (a new composition module + endpoint AND a new page + types + governance card), requires new unit/integration tests beyond browser smoke, and ships a new `/research/*` served surface — the exact "new page + served value → FULL" trigger the iter-30 recommendation named. The prior evaluator returned CONTINUE (not ESCALATE), so full is chosen on the boundary-crossing trigger, not a forced escalation.

The graveyard is READ-ONLY composition — it introduces **no new canonical value** (B-902) and does **zero evidence work** (no `## Evidence Claim`; the canonical Bonferroni divisor stays 8). One deliberate contract evolution: the blueprint's iter-9/10/12 "staging ledger is internal-only, never served" invariant is narrowed so the staging ledger's NON-PASS verdicts become browsable (the graveyard's whole purpose). The honesty fence is preserved — the graveyard shows only non-PASS, staging carries 0 PASS, and `/evidence` + `proven_signals` + the "Proven" badge stay byte-identical. This interpretation call is logged in `runs/goal-session-mcp-loop/state/assumptions.md` (iter-31).

Applicable lessons (surfaced for dev/reviewer/QA/evaluator): **iter-9** — for a shared-value-adjacent iteration the regression proof is byte-identical ledger outputs + unchanged `/api/evidence`/`proven_signals` + unedited frozen-golden tests, NOT a browser pass. **iter-30** — do not gate on a literal derived count: the bar is "every non-PASS ledger entry appears and one round-trips byte-exact to its ledger row", not "14 rows" (today all 14 entries are FAIL: 7 canonical + 7 staging). **iter-11/13/14/25** — md5-distinct full-page/element-clip evidence frames; capture the ma_stack "permanent" marking and a resolved lineage link IN-FRAME, never trust a reused frame or a PASS label. **iter-20** — `rm -rf apps/frontend/.next` and confirm BOTH prod services reachable BEFORE dispatching browser-qa; never accept a status.json/QA "ready to ship" over an empty evidence dir or a CLOSURE-FAIL.

## IN SCOPE

### Backend
- [ ] New PURE read-compose module `app.engine.graveyard` (mirror `app.engine.registry`'s engine-free shape — filesystem read + dict work only, no DB session, no computation) exposing a `build_graveyard_payload()`-style function that:
  - Reads the **canonical** ledger via `app.engine.ledger:read_entries(app.engine.evidence.resolve_ledger_path())` and the **staging** ledger via `read_entries` over the config-resolved `evidence.staging_ledger_path` (honor the `STAGING_LEDGER_PATH` env the harness exports; mirror the canonical resolver — add NO new path literal, anti-goal: no magic numbers).
  - EXCLUDES forward-walk monitoring records (`type == "forward_walk"`) exactly as `build_evidence_payload` does.
  - FILTERS to NON-PASS verdicts (`verdict.status != "PASS"` → FAIL / INSUFFICIENT). Status-driven, never a hardcoded count (today all 14 are FAIL; a future PASS is excluded automatically).
  - Tags each entry with its origin ledger (`"canonical"` | `"staging"`) and re-displays the deflation context (`verdict.deflation` + `verdict.deflation_divisor`) VERBATIM — recomputes nothing.
  - Attaches registration lineage via the SAME `app.engine.registry:match_registration(entry["claim"])` the J-18 gate/registry-page use (id, status, source, rationale, registered_date). Do NOT reimplement selector matching — reuse `registry.claim_selectors`/`match_registration` so the graveyard, the registry page, and the gate can never disagree.
  - When a ledger entry's selector-set matches NO registration, renders an HONEST null lineage (no crash, no fabricated link).
  - Surfaces the "permanent" marking from the matched registry row's `status == "closed"` (re-displayed — e.g. the `ma_stack` closed FAIL — never a new computation).
  - A missing/empty ledger file ⇒ an empty graveyard, never a crash (anti-goal #8).
- [ ] The **revisit-protocol rule** (B-406 / §0) surfaced as a served constant so the page can render it and anchor each row to it — single source, one module-level constant (no proven-language): "A referee FAIL/INSUFFICIENT is final for that hypothesis; a re-test requires a **materially changed precondition** (a new data span covering ≥2 additional OOS years, a data-basis change, or a genuinely different hypothesis) and must be registered as a NEW candidate citing the closed verdict."
- [ ] New endpoint router `app.api.graveyard` serving `GET /api/research/graveyard` → the composition payload verbatim (e.g. `{"entries": [...], "revisit_protocol": {...}}`); 200-with-empty on a missing/empty ledger, never 500 (mirror `app.api.registry`).

### Frontend
- [ ] New page `apps/frontend/app/research/graveyard/page.tsx` mirroring `app/research/registry/page.tsx`'s shell exactly (loading skeleton / backend-unavailable card / honest empty state / `Back to Research` / `PageHeading`). Renders a table of graveyard rows: **Selectors** (verbatim key=value chips), **Verdict** (FAIL / INSUFFICIENT badge — NEUTRAL/negative styling, NEVER the accent/"Proven" evidence-badge styling), **Date**, **Deflation** (e.g. `bonferroni ÷8` / `lord++`), **Ledger** (canonical / staging), **Lineage** (link to its registry row / `/research/registry`), and a "permanent" marker on closed rows. A **Revisit-protocol** panel states the rule; each row links/anchors to it.
- [ ] `apps/frontend/lib/graveyard.ts` types (mirror `lib/registry.ts`) + a `fetchGraveyard` client in `lib/api.ts`.
- [ ] A governance card on `/research` linking to `/research/graveyard`, added to the EXISTING "Governance & process" grid (the section comment already reserves this slot); `data-testid="research-governance-link-graveyard"`.

### New user-facing capability
A user can browse the institutional memory of dead hypotheses: every non-PASS referee verdict, its selectors / verdict kind / date / deflation / origin ledger / registration lineage, closed proposals flagged permanent, and the revisit-protocol rule that governs when (if ever) a dead idea may be re-tested.

### New information displayed
The two ledgers' NON-PASS (FAIL/INSUFFICIENT) verdicts joined to their registration lineage — including, for the first time, the staging ledger's exploration failures — plus the revisit-protocol rule text.

### New user actions
Navigate Research → Graveyard; click a row's lineage link through to its registry row; click through to the revisit-protocol rule.

### UI surface changes
New `/research/graveyard` page; new governance card on `/research`.

### Product surface delta
The evidence layer gains its "what does NOT work" companion to `/evidence` ("what is proven") and `/research/registry` ("what is registered"): the negative-results graveyard makes failure first-class, browsable institutional memory instead of buried ledger lines.

### Blueprint conformance
`/research/graveyard` lives under the EXISTING **Research** top-level nav section's already-approved "Governance & process" grouping (the iter-30 `blueprint.reapproval-requested` covered exactly this registry→graveyard→budget→referee-audit grouping), hub-reached in ≤2 clicks — the same pattern as `/research/registry`. This is an **additive page, not a nav-skeleton change** — no new `blueprint.reapproval-requested` is filed. The J-19 home row is registered in `blueprint.md`'s Information Architecture.

### Data-contract additions
ONE new serving surface — the **negative-results graveyard composition** — registered in `blueprint.md`'s Data Contract: computed once by the new `app.engine.graveyard:build_graveyard_payload` (a PRESENTATION COMPOSITION reading BOTH ledgers via `ledger.read_entries` and attaching lineage via `registry.match_registration`; RECOMPUTES NO verdict), served by the new `GET /api/research/graveyard`. **No NEW canonical value** (B-902: composition only) — it re-serves already-canonical values (the certified-claims + staging verdicts + the registry rows) and never introduces a second computation of any of them. The one contract evolution is that the staging ledger's NON-PASS verdicts become browsable (blueprint iter-31 clarification documents the narrowed "staging internal-only" invariant + the preserved honesty fence).

## OUT OF SCOPE

- NO `## Evidence Claim`, NO referee submission, NO ledger write — the graveyard is READ-ONLY. `certified-claims.jsonl`, `staging-ledger.jsonl`, and `pre-registrations.jsonl` stay byte-identical; the canonical Bonferroni divisor stays 8.
- NO change to `/api/evidence`, `build_evidence_payload`, `proven_signals`, the "Proven" badge, or any score / regime / sector / theme / forward-return / index / capacity value.
- NO deletion or edit path for any graveyard entry (B-902: "no deletion path exists"; history is append-only).
- NO reviving / re-testing / re-submitting any closed FAIL (anti-goals #4/#6; the graveyard is the WALL against retry laundering, not a retry surface).
- NO new canonical value, NO new top-level nav section, NO change to any existing computing module or serving endpoint.
- J-17 (budget panel, B-903) and J-20–J-25 — deferred (one risky new surface per iteration; rubric rule 5).

## DEFINITION OF DONE

- [ ] **J-19 passes via browser-qa-agent:** `/research/graveyard` renders every non-PASS verdict (today 14: 7 canonical + 7 staging) with selectors + verdict kind + date + registration lineage; the `ma_stack` closed FAIL shows its "permanent" marking; each entry links to the revisit-protocol rule.
- [ ] **Correctness (anti-goal #3):** at least one graveyard entry's displayed selectors + verdict + date byte-match its row read directly from `certified-claims.jsonl` / `staging-ledger.jsonl` (round-trip, not a literal count — iter-30 lesson).
- [ ] **Single-source (no UI-recompute — B-902 failure mode):** the page re-reads `GET /api/research/graveyard` verbatim; no verdict or proven-ness recomputed client-side; lineage comes from `registry.match_registration`, not a reimplemented matcher.
- [ ] **Regression proof (iter-9 lesson):** `certified-claims.jsonl` + `staging-ledger.jsonl` + `pre-registrations.jsonl` stay byte-identical; `GET /api/evidence` + `proven_signals` unchanged; the canonical Bonferroni divisor stays 8.
- [ ] **Required-still-passing** J-01, J-03, J-04, J-05, J-06, J-08, J-09, J-11, J-18 remain green.
- [ ] **No anti-goal violation** — esp. #1 (no FAIL rendered as proven; verdict-kind + descriptive registry status carry NO proven-language), #3 (verdict numbers correct), #7 (no credentials), #8 (graceful degrade on empty/missing ledger + honest null lineage, never a blank crash).
- [ ] Unit/integration tests pass; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-mcp-loop-iter-31-dev.md`.

## TESTING REQUIREMENTS

- **Browser (J-19):** `/research/graveyard` renders all non-PASS rows with selectors/verdict/date/lineage; the `ma_stack` permanent marking is in-frame; a row's lineage link resolves to its registry row; the revisit-protocol rule is visible; discoverable from `/research` governance grid in ≤2 clicks; empty/backend-down honest state (contained card, nav intact). Full-page or element-clip captures, md5-distinct (iter-14 lesson).
- **Unit/integration:** `build_graveyard_payload` over fixture ledgers (canonical + staging) — non-PASS filter; lineage attachment via `match_registration`; honest null lineage when a selector-set is unregistered; forward-walk exclusion; ledger-origin + deflation tags re-displayed verbatim; "permanent" marking from a `status=="closed"` registry row; missing/empty ledger ⇒ empty payload (no crash). Endpoint test: `GET /api/research/graveyard` returns the composition verbatim and 200-on-empty. **Recommended cheap add (iter-30 audit-O1 carry-forward, directly load-bearing for lineage correctness):** an equality test asserting `app.engine.registry._CLAIM_SELECTOR_KEYS == app.mcp.tools._CLAIM_SELECTOR_KEYS` — drift insurance for the matcher the graveyard leans on.
- **Error cases:** missing/empty ledger file(s) ⇒ empty graveyard, 200 not 500; a ledger entry whose selectors match no registry row ⇒ honest "no registration lineage" (no crash, no fabricated link); a PASS entry (none today) ⇒ excluded from the graveyard.

## NOTES

- **Assumption logged** (`runs/goal-session-mcp-loop/state/assumptions.md`, iter-31): J-19's "every non-PASS verdict" + B-902's "read-compose from ledgers" leave open whether the STAGING ledger's non-PASS verdicts are in scope (the blueprint iter-9/10/12 declared staging "internal-only, never served") and whether composition is backend- or frontend-side. We chose to surface BOTH ledgers' non-PASS verdicts via a NEW backend composition endpoint (`GET /api/research/graveyard`) — the graveyard's purpose squarely includes staging explorations, the honesty fence is preserved, `/api/evidence` serves canonical-only so a frontend-only compose is impossible without a new served surface anyway, and B-902's "UI-recompute" failure-mode ban + the blueprint compute-once-serve-verbatim discipline both point to backend composition. Reversible: yes.
- **Coherence note for the coherence-auditor:** the staging-ledger surfacing is a *narrowing* of the prior "internal-only" invariant, documented in the blueprint iter-31 clarification; the honesty fence (no proven from staging; `/evidence`/`proven_signals`/"Proven" badge byte-identical) is intact. Not a nav-skeleton change (page lives under the existing, already-approved Research governance grouping) — no reapproval note filed.
- **Escalation flag:** none (prior verdict CONTINUE, full).
- ~7 more one-surface governance/ops/risk iterations (J-17, J-20–J-25) then close the goal — a tractable path, not a plateau.
