# Goal Iteration 30 — J-18 pre-registration registry + gate enforcement (governance keystone)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** mcp-loop
- **Iteration:** 30
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-18
- **Required-still-passing journeys:** J-01, J-02, J-03, J-05, J-06, J-07, J-08, J-09, J-11
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

Ship the pre-registration registry (J-18 / backlog **B-901**): a `/research/registry` page listing every registered hypothesis, and the post-decompose gate refusing any Evidence Claim that has no matching registration row — making ad-hoc data mining structurally impossible for every future iteration.

## BACKGROUND

All 16 built journeys (J-01..J-16) are passing and J-17..J-25 are unbuilt; GOAL_ACHIEVED now depends solely on J-17..J-25 (iter-29 evaluator). Per the priority rubric this iteration takes the **unblocker** (rule 3): B-901 is the governance keystone the backlog marks as a hard dependency edge — "B-903/B-901 before opening any wide scan" — and J-19's graveyard (B-902) reads its lineage links, so it unblocks the most downstream work. It is taken **alone** (rule 5: never bundle two risky journeys; this one touches the certification gate). No journey regressed and iter-29 coherence was COHERENCE-PASS, so no consolidation pass is owed (rules 1–2 clear).

**Depth = full** is forced by the structural triggers in "Picking depth": the iteration crosses backend + frontend, adds a new served value + a new page, and — the load-bearing part — modifies the cross-cutting post-decompose gate (`project-extensions/gates/verify_claim.py`), the choke point that certifies every future edge. It also needs new backend fixture tests beyond browser smoke (the gate refuse/proceed cases). The prior evaluator's next-step also specified iter-30 FULL.

The binding spec is backlog card **B-901** (`docs/improvement-backlog.md` §Track 9). Key card constraints carried here verbatim: **Dominant failure mode = scope-creep (a registry, not a workflow engine)**; **Traps** = fuzzy matching (exact selectors or refuse — fuzziness reopens the mining door), editing rows (append status changes only), retroactive registration to launder a mined result (registration dates are audit trail); **Do NOT touch** = referee statistics; ledgers.

## IN SCOPE

### Backend
- [ ] New append-only state file `runs/goal-session-mcp-loop/state/pre-registrations.jsonl` — one JSON object per row: `id`, the claim **selectors** (`kind` + the `_CLAIM_SELECTOR_KEYS` subset the claim carries + `horizon` + `direction`), `rationale`, `registered_by`, `registered_date`, `source` (e.g. `proposer-guidance §4.1`, `certified-claims.jsonl`, `staging-ledger.jsonl`, backlog card id), and `status` (a descriptive vocabulary — e.g. `registered` / `tested` / `closed` — NEVER proven-language).
- [ ] New **single** loader module `app.engine.registry` (pure read of the one file; config-resolved path `evidence.registry.path` with a `TRENDORA_REGISTRY_PATH` env override, mirroring `app.engine.evidence.resolve_ledger_path()` — no path literal). Exposes `load_registrations()` and a pure `match_registration(claim)` that returns the matching row or `None` by **EXACT** selector-set equality (no fuzzy/superset matching). Missing/empty file ⇒ honest empty list, never a crash (anti-goal #8).
- [ ] **Backfill** the registry: the UNION of the proposer-guidance §4.1 (4 rows) + §4.2 (3 rows) pre-registered candidates AND every distinct claim selector-set in `certified-claims.jsonl` (7) + `staging-ledger.jsonl` (7), deduplicated by hypothesis, each labeled with its `source` and current `status` (historical rows flagged as backfills, e.g. `registered_by: backfill`). Include the closed `ma_stack` FAIL as a `closed` row.
- [ ] New serving endpoint `GET /api/research/registry` (thin handler in `app/api/research.py` or a small `app/api/registry.py`) returning the loader output verbatim (re-format only — no recompute).
- [ ] **Gate teeth** — extend `project-extensions/gates/verify_claim.py`: BEFORE `tools.verify_edge` runs for each claim, when `evidence.registry.enforce` is `true`, cross-check the claim against the registry via the SAME `app.engine.registry.match_registration`. No match ⇒ **refuse the claim (block, exit 3) BEFORE any referee computation** — `verify_edge` is never called, no ledger write, no Bonferroni-bar tightening — with a clear message naming the registry requirement. A match ⇒ proceed to the referee unchanged. Enforcement OFF ⇒ current behavior exactly.
- [ ] Config: add `evidence.registry.path` and `evidence.registry.enforce` (documented, no magic numbers). Set `enforce: true` **only after** the backfill is verified complete (B-901 step 4 "flip after verification"). Export `TRENDORA_REGISTRY_PATH` (or `REGISTRY_PATH`) from `run-goal.sh` alongside `LEDGER_PATH` / `STAGING_LEDGER_PATH` at both dispatch sites so the gate resolves the same file the endpoint serves.
- [ ] Backend tests (the B-901 DoD gate fixtures): (a) a claim whose exact selectors match a registry row → gate cross-check proceeds to the referee; (b) an unregistered claim → refused BEFORE `verify_edge` is invoked (assert `verify_edge` not called / ledger unchanged), message names the registry; (c) a **near-miss** claim (one selector differs) → refused (proves matching is EXACT, not fuzzy); (d) loader + endpoint return the same backfilled rows (single-source); (e) missing-file ⇒ empty, no crash.

### Frontend
- [ ] New page `apps/frontend/app/research/registry/page.tsx` reading ONLY `GET /api/research/registry`: a table of every registration with selectors, rationale, registration date, source, and status; historical backfills visibly **labeled as such**. Honest empty/loading/error states; no proven-language, no badges, no numbers presented as edges.
- [ ] Make `/research/registry` discoverable from `/research` in ≤2 clicks (a governance/process entry on the Research hub — extend `lib/research-labs.ts` or add a small governance group on `app/research/page.tsx`). No existing lab/route added, removed, or renamed.

### New user-facing capability
The user can browse the complete pre-registration registry at `/research/registry` — every hypothesis the system has ever registered/tested, with its economic rationale and audit-trail date — and the loop now structurally refuses to certify any edge that was not pre-registered.

### New information displayed
The registry table: each registered hypothesis's selectors, rationale, registration date, source, and status (with historical backfills labeled). No numeric edge, no proven/confidence language.

### New user actions
Navigate to `/research/registry` (via the Research hub) and read/scan the registry. No forms or mutations — the page is read-only (registrations are appended by the gate/tooling, never edited in the UI).

### UI surface changes
One new read-only page under Research (`/research/registry`) + one discoverable hub entry pointing to it. No shell/nav-skeleton rewrite.

### Product surface delta
Trendora gains its institutional pre-registration memory and a machine-enforced anti-data-mining guarantee: pre-registration now *binds* because a machine checks it, not a convention.

### Blueprint conformance
`/research/registry` lives under the **existing Research** top-level nav section (the same pattern as every current lab, which is reached from the `/research` hub, none in the sidebar) — an additive page under an existing home, registered as J-18's home in `blueprint.md`. Because this introduces the first of four forthcoming Research **governance/process** surfaces (registry now; graveyard J-19 / budget J-17 / referee-audit J-22 to follow) and the iter-29 blueprint paragraph pre-committed that new `/research/*` sub-routes carry a re-approval note, a one-line `blueprint.reapproval-requested` is written this iteration so the human can weigh in on how the governance grouping is organized before more of them land (run-goal.sh auto-approves and continues by default).

### Data-contract additions
ONE new value, registered in `blueprint.md`:
- **Pre-registration registry** (every registered hypothesis: id, claim selectors, rationale, registered-by/date, source, status) — **computing module:** `app.engine.registry:load_registrations` (the SINGLE append-only read of `state/pre-registrations.jsonl`); **serving endpoint:** `GET /api/research/registry` (the ONE endpoint the page reads). The gate (`verify_claim.py`, a non-HTTP consumer) and the future B-902 graveyard read the SAME file via the SAME loader module — not a second computation or endpoint. The value carries NO proven-language; proven-ness still flows only from `verdict.status==PASS` on the pre-existing evidence-status value.

## OUT OF SCOPE

- J-17 (budget panel, B-903), J-19 (graveyard, B-902), J-22 (referee-audit, B-102), J-20/J-21 (daily-ops), J-23/J-24/J-25 (risk analytics) — one risky journey per iteration (rubric rule 5). J-19 reads this registry's lineage next.
- **Do NOT touch referee statistics or either ledger.** `app.mcp.tools:verify_edge`, `app.engine.referee`, `app.engine.ledger`, `certified-claims.jsonl`, and `staging-ledger.jsonl` stay byte-identical; the canonical Bonferroni divisor stays 8. The gate change is a pre-check that either lets the existing `verify_edge` run unchanged or short-circuits before it.
- NO `## Evidence Claim` this iteration — it certifies nothing (pure governance/UX). The post-decompose gate passes it through automatically.
- No fuzzy/partial selector matching; no UI edit/delete of registry rows; no retroactive registration of any un-pre-registered result; no re-submission of a closed FAIL.
- No new proven/confidence language anywhere.
- No workflow-engine scope creep (B-901 dominant failure mode) — a registry + a loader + a gate check + a page, nothing more.

## DEFINITION OF DONE

- [ ] Target journey **J-18 passes**: `/research/registry` lists every registered hypothesis (selectors, rationale, registration date, source, status, backfills labeled) — verified via browser-qa-agent (J-18 step 1).
- [ ] Gate fixture (backend test) proves J-18 step 2: an Evidence Claim whose EXACT selectors match a registry row proceeds to the referee.
- [ ] Gate fixture (backend test) proves J-18 step 3: an unregistered claim is REFUSED **before** any referee computation (`verify_edge` not called; no ledger write), with a message naming the registry requirement.
- [ ] Exact-match fixture: a near-miss claim (one differing selector) is refused (no fuzzy matching).
- [ ] Single-source assertion: the page (via `GET /api/research/registry`) and the gate (via `app.engine.registry`) read the same file/loader.
- [ ] Backfill complete: registry contains the proposer-guidance §4.1/§4.2 rows ∪ every distinct claim from both ledgers (≥14 ledger-derived rows), each with source + status; append-only (no deletion path).
- [ ] `evidence.registry.enforce: true` in config, flipped only after backfill verification.
- [ ] No proven-language introduced (registry status vocabulary is descriptive) — anti-goal #1 upheld.
- [ ] Both evidence ledgers byte-identical; `verify_edge` + referee/ledger modules git-unchanged; divisor stays 8.
- [ ] Required-still-passing journeys (J-01, J-02, J-03, J-05, J-06, J-07, J-08, J-09, J-11) remain green via deterministic replay.
- [ ] No anti-goal violation introduced.
- [ ] Unit/integration + gate fixture tests pass; no regressions.
- [ ] `[NEW]`-flagged demo-narrator walkthrough of the registry + a refused unregistered claim produced (viewable via `demo.sh mcp-loop --session-live`).
- [ ] Dev handoff written at `docs/handoffs/goal-mcp-loop-iter-30-dev.md`.

## TESTING REQUIREMENTS

- **Browser (browser-qa-agent):** J-18 step 1 only — `/research/registry` renders the registry table with selectors + rationale + registration date + source + status, backfills labeled; discoverable from `/research` in ≤2 clicks; honest empty/error states; no proven-language. (Steps 2 & 3 are the gate mechanism and are NOT browser-testable — the gate is a CLI/backend script; they are fixture-proven below. Make this split explicit so the journey is not scored on a browser proof of the gate.)
- **Unit/integration (backend):** the gate registry cross-check must be covered: registered→proceed, unregistered→refuse-before-referee (assert `verify_edge` uncalled + ledger unchanged), near-miss→refuse (exact match), loader==endpoint single-source, missing-file→empty-no-crash. Assert exact refusal message content (names the registry requirement).
- **Error cases:** unregistered Evidence Claim (rejected before referee); near-miss selector claim (rejected); empty/absent registry file (empty page, no crash); enforcement-off path (existing behavior preserved, byte-identical).
- **Regression (replay):** re-verify J-01/02/03/05/06/07/08/09/11 — the evidence-status readers and Research-home journeys most exposed to the gate/`/research` change; confirm `GET /api/evidence` + both ledgers unchanged.

## NOTES

- **Enforcement is safe to turn on now.** The gate refuses only iterations that carry a `## Evidence Claim`; J-18 and all of J-17..J-25 carry none, and the evidence frontier is at a sanctioned plateau (staging closed, canonical divisor 8, no promotable candidate — goal.md), so no current or near-term work submits a claim. The `enforce: true` flip therefore blocks nothing today while permanently closing the ad-hoc-mining door. It does NOT affect this iteration's own gate run (iter-30 has no claim, and the config flip lands in the developer step, after this spec's gate check).
- **Backfill completeness matters more than the flip.** Sequence hard: backfill → verify count/content → only then set `enforce: true`. If a legitimately-registered hypothesis is ever missed, the graceful path is the B-406 revisit protocol (register a NEW row), not a silent bypass — but an incomplete backfill would wrongly refuse a future revisit, so the completeness assertion is a gate on the flip.
- **Lesson application (iter-9 / iter-9b / iter-12, evidence-machinery):** the ledgers and `verify_edge` are the shared certification economy — the regression proof for this iteration is that `certified-claims.jsonl` + `staging-ledger.jsonl` + `test_referee`/`test_ledger`/`test_staging_ledger_routing` stay byte-identical/unedited, NOT a browser pass. If any of those had to change, that IS the regression signal.
- **Lesson application (iter-13 / iter-20 / iter-22, gate-touching + Frontend-Present):** the registry PAGE is the browser-verifiable half; the gate refuse/proceed is fixture-verified. Do not let an audit-applied UI fix land after the browser lane without a re-run, and do not flip J-18 to passing on code-verification alone if the browser lane skipped the page (rm -rf .next + confirm both prod services up before browser-qa).
- **Scope discipline (B-901 dominant failure mode = scope-creep):** build a registry, a loader, a gate check, and a read-only page — resist adding a mutation/withdrawal UI, approval workflow, or family/quota accounting (those are B-903/B-404/B-406, separate journeys).
- References: goal slice `runs/goal-session-mcp-loop/iter-30/goal-slice.md` (J-18 verbatim); binding card `docs/improvement-backlog.md` §B-901 (lines ~2894–2925); blueprint `runs/goal-session-mcp-loop/state/blueprint.md` (Data Contract + IA updated this iteration); iter-29 next-step recommendation (start with J-18).
