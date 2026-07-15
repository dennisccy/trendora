# Goal Iteration 36 — Certifier calibration: referee placebo + lookahead-tripwire audit (J-22)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** mcp-loop
- **Iteration:** 36
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-22
- **Required-still-passing journeys:** J-01, J-03, J-05, J-11, J-17, J-18, J-19, J-20
- **Anti-goal reminders (verbatim from docs/goal.md):**
  - A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked values MUST render a "not yet proven" state. *(critical)*
  - **Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha claims; never place or simulate orders. *(critical)*
  - A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation for the same as-of date — not merely that the page renders. *(critical)*
  - **No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of; never introduce lookahead anywhere. *(critical)*
  - No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the post-decompose gate. *(critical)*
  - No hard-coded credentials, API keys, or tokens in source files. *(critical)*
  - **Resilience to data-shape and data-scale change:** widening the data basis (new nulls, broader pools, deeper history) must never crash an existing page or exhaust a service's memory — every existing consumer of a widened field is re-validated, the UI degrades gracefully (contained error boundary, honest "—"/NA placeholder, never a blank application-error page), and unbounded whole-table ORM loads are forbidden on the deep basis. *(critical)*

## GOAL

Deliver `/research/referee-audit` — a read-only panel that shows the certifier's measured **empirical false-pass rate (with a binomial CI) vs the configured α** over seeded null factors, plus a **lookahead-contaminated-factor tripwire** labeled "expected: rejected" — computed by an **isolated** audit job against a throwaway ledger and re-read verbatim, so the user can see the certifier itself is calibrated (or loudly see that it is not).

## BACKGROUND

J-22 is the **4th and final governance surface** (backlog **B-102**), architecturally adjacent to J-17 (budget), J-18 (registry), and J-19 (graveyard) already shipped — the `/research` hub's "Governance & process" grouping already reserves its card (`apps/frontend/app/research/page.tsx:80-81` comment: "referee-audit still to follow"). Depth is **full** (self-check #4 triggers): it crosses backend (a seeded null-factor generator + a `certify_edge` harness + a persisted artifact + a config block + a new endpoint) and frontend (a new page); it touches the certification/referee machinery under a **data-integrity dominant failure mode** — the real `certified-claims.jsonl` / `staging-ledger.jsonl` and the real Thresholdout budget must stay **byte-identical** (leaking test rows would poison the Bonferroni divisor and silently corrupt every evidence badge); and it needs new tests beyond browser smoke (a fast seeded CI test proving determinism + isolation + tripwire-caught). Target selection follows the rubric: no regressed/failing journeys and iter-35 coherence = COHERENCE-PASS (no consolidation owed), so this is forward progress on an unknown journey (rule 3) — J-22 completes the governance cluster and reuses existing `certify_edge`/`ledger` machinery, the most tractable next surface; the risk-analytics cluster (J-23/J-24/J-25) is newer territory, deferred one-risky-journey-per-iter (rule 5). This is the standing iter-32/33/35 recommendation ("J-22 = the 4th + final governance surface, next"). iter-35 ended CONTINUE with CLOSURE-PASS (its required set was **live**-re-verified via browser-qa — the iter-35 lesson), so the deterministic-replay lean closeout is hygiene, NOT remediation, and is batched into a later lean pass; iter-35 explicitly sanctioned "go straight to FULL J-22 and batch the replay into the next lean pass."

## IN SCOPE

### Backend
- [ ] New PURE module `app/engine/referee_audit.py`:
  - **Generator (seeded):** null factors = per-date random permutation of a real factor's cross-section (kills any signal while preserving the distribution — B-102 How #1); plus one **lookahead-contaminated factor** whose value equals the realized forward return at `contaminated_factor_horizon` (the "perfect crime" a broken harness would certify instantly).
  - **Harness:** run each candidate through the referee (`app.engine.referee:certify_edge` / `app.mcp.tools:verify_edge`) against an **ISOLATED throwaway `ledger_path`** and/or a fresh in-memory `RefereeState` — the real ledgers + the real Thresholdout budget are NEVER touched or charged (`verify_edge` already takes an explicit `ledger_path` so the economies never share a file — `tools.py:475/493`).
  - **Report builder:** empirical false-pass count/rate + a **binomial confidence interval vs the configured α**, the contaminated-factor verdict tagged **"expected: rejected"**, the run date, and the run parameters (seed, `n_null_trials`, `contaminated_factor_horizon`).
  - **Persistence + single reader:** persist the dated artifact via a new `resolve_referee_audit_path()` (config `research.referee_audit.report_path`, env `TRENDORA_REFEREE_AUDIT_PATH`, REPO_ROOT-resolved — mirroring `resolve_ledger_path` / `resolve_drift_report_path`); `read_referee_audit_report()` re-reads it verbatim (missing/unparseable ⇒ honest empty/None, never a 500).
- [ ] Config block `research.referee_audit` (typed cfg; defaults present): `n_null_trials` (200 offline / 20 CI), `seed`, `contaminated_factor_horizon`, `report_path`.
- [ ] A config-seeded **job/trigger** to run the audit and persist the artifact (job-style — the panel re-reads, never recomputes). **Bound it** (anti-goal #8 / iter-24-26 lesson): reuse existing per-cohort bounded forward-return paths; NO unbounded whole-table ORM load; the 200-trial run is offline. The **CI variant** uses a tiny synthetic price fixture and **MUST NOT import the full seed** (B-102 explicit trap).
- [ ] New endpoint `GET /api/research/referee-audit` (thin router `app/api/referee_audit.py`, wired like `budget`/`registry`/`graveyard`): re-reads the persisted artifact verbatim; missing/empty ⇒ honest empty snapshot (200, never 500).

### Frontend
- [ ] New page `apps/frontend/app/research/referee-audit/page.tsx` (read-only): shows `n_null_trials`, the empirical false-pass rate + CI, the configured α, the contaminated-factor verdict labeled **"expected: rejected"**, the run date, and the run parameters — re-reading `GET /api/research/referee-audit` verbatim (no client recompute). A **prominent red tripwire failure state** if the contaminated factor is NOT caught (never hidden). Honest empty state when no artifact exists. Contained "Backend unavailable" card (nav intact) when the backend is down.
- [ ] Add the 4th **"Referee audit"** card/link to the EXISTING `/research` "Governance & process" grouping (`research/page.tsx:80-134`; `data-testid="research-governance-link-referee-audit"`) — additive, no nav-skeleton change.
- [ ] Additive client fetch `fetchRefereeAudit` in `lib/api.ts` for the new endpoint (no second fetch path for any existing value).

### New user-facing capability
The user can open `/research/referee-audit` and see the certifier's measured false-pass rate against α plus the lookahead tripwire result — evidence that the certifier itself is honest (or a loud, un-hideable signal that it is not).

### New information displayed
Number of null trials; empirical false-pass rate + binomial confidence interval; configured α; contaminated-factor verdict ("expected: rejected"); run date; run parameters (seed, horizon).

### New user actions
None (read-only panel; the audit runs as a config-seeded job, not a UI action). One new nav card/link on the `/research` hub.

### UI surface changes
One new page `/research/referee-audit`; one new card in the EXISTING `/research` "Governance & process" grouping.

### Product surface delta
The governance cluster is complete: the product now discloses not only what is proven (`/evidence`), what is pre-registered (`/research/registry`), what is dead (`/research/graveyard`), and the statistical budget (`/research/budget`), but also whether the **certifier itself** is calibrated — closing the "who audits the auditor" gap.

### Blueprint conformance
The new page lives under the EXISTING Research top-level nav → "Governance & process" grouping (approved at iter-30, which explicitly named "J-22 referee-audit to follow"; hub-reached in ≤2 clicks, same pattern as registry/graveyard/budget). **No nav-skeleton change; no `blueprint.reapproval-requested` filed.** The IA homes table gains the J-22 row (done in this iteration's blueprint edit).

### Data-contract additions
ONE new value — the **referee-audit report artifact** (null-trial count; empirical false-pass rate + binomial CI; configured α; lookahead-contaminated-factor verdict tagged "expected: rejected"; run date + params). Computed once by `app.engine.referee_audit:build_referee_audit_report` (the isolated harness), served by the new `GET /api/research/referee-audit` (the ONE reader = the `/research/referee-audit` page). It is a fresh calibration report — NOT a recompute or second source of any existing value, and it **pollutes no canonical value** (throwaway ledger + separate budget; referee constants untouched). Registered in `blueprint.md`'s Data Contract in this iteration's edit.

## OUT OF SCOPE

- Any `## Evidence Claim` / any evidence work — J-22 **certifies nothing; it audits the certifier** and carries NO proven-language. The post-decompose gate passes automatically; the canonical Bonferroni divisor stays 8; both real ledgers stay 7/7 FAIL and byte-identical.
- Any change to the real `certified-claims.jsonl`, `staging-ledger.jsonl`, `pre-registrations.jsonl`, or the real Thresholdout budget accounting (**the dominant failure mode** — they MUST be byte-identical before/after).
- Tuning ANY referee default constant (`DEFAULT_ALPHA_PER_TEST`, `DEFAULT_ALPHA_BUDGET`, noise scale, etc.) — auditing ≠ tuning (the card's keystone trap: never tune constants until the audit "looks right").
- The risk-analytics journeys J-23 (B-204 concentration), J-24 (B-201 risk card), J-25 (B-205 drawdown/dry-spell) — the next cluster (one risky journey per iter, rule 5).
- The B-204 referee-settings sweep (which "shares the audit harness") and any B-113-sentinel enrichment — deferred follow-ons that plug into THIS harness later.
- The deterministic-replay hygiene closeout of the ~14 byte-identity-carried journeys + folding `J-20.json`/`J-21.json` into the golden set — batched into a later lean pass (iter-35 CLOSURE-PASS ⇒ hygiene, not remediation).

## DEFINITION OF DONE

- [ ] **J-22 passes via browser-qa:** `/research/referee-audit` shows the null-trial count, the empirical false-pass rate + CI, the configured α, the contaminated-factor verdict labeled "expected: rejected", the run date, and the run parameters — all re-read from the persisted artifact.
- [ ] **Isolation proven (dominant failure mode):** `git diff HEAD` is EMPTY on `certified-claims.jsonl`, `staging-ledger.jsonl`, and `pre-registrations.jsonl`; the real Thresholdout budget accounting is untouched — verified after the audit run.
- [ ] `/evidence` renders unchanged (0 PASS, 7 FAIL; no new claim appeared from the audit) — browser-verified (J-22 step 4).
- [ ] The lookahead-contaminated factor is REJECTED by the referee, OR the panel renders a prominent red tripwire failure state (never hidden) — browser-verified.
- [ ] A fast **seeded** CI/integration test passes in seconds: the same seed reproduces the false-pass rate exactly (determinism); the tripwire is caught; the harness writes only a throwaway ledger and leaves the real state files byte-identical (isolation); it does NOT import the full seed.
- [ ] Required-still-passing journeys J-01, J-03, J-05, J-11, J-17, J-18, J-19, J-20 remain green — **LIVE-re-verified via the browser-qa lane** (a FULL iter has no deterministic-replay lane; live re-verification reaches CLOSURE-PASS — the iter-35 pattern), or the closure one-liner replay run inline.
- [ ] No anti-goal violation introduced (no proven-language on the panel; determinism preserved via config seeds; no credentials; bounded harness — no OOM / whole-table load; honest degradation on missing artifact / backend-down).
- [ ] Unit/integration tests pass; no regressions.
- [ ] `blueprint.md` Data Contract carries the referee-audit report artifact row (done in this spec's blueprint edit).
- [ ] Dev handoff written at `docs/handoffs/goal-mcp-loop-iter-36-dev.md`.

## TESTING REQUIREMENTS

- **Browser:** J-22 (`/research/referee-audit`) — all displayed fields from the artifact (null-trial count, false-pass rate + CI, α, run date, params); the "expected: rejected" contaminated-factor verdict; the honest empty state; the red tripwire failure state when the contaminated factor is not caught; the contained backend-unavailable card. Then the required-still-passing set **J-01, J-03, J-05, J-11, J-17, J-18, J-19, J-20** live-re-verified. **Confirm `apps/frontend/.next/BUILD_ID` postdates the new page source (force a rebuild) BEFORE trusting any "card/page missing" observation** (iter-20/21/35 stale-prod-build trap).
- **Unit/integration:** the seeded harness (same seed ⇒ identical false-pass rate — determinism); the isolation guarantee (real ledgers + Thresholdout budget byte-identical after N trials; the harness writes only a throwaway ledger); the binomial-CI computation; the contaminated-factor rejection (tripwire-caught); the endpoint's honest empty/missing-artifact path (200, never 500). **The CI variant uses a tiny synthetic fixture and MUST NOT import the full seed.**
- **Error cases:** missing/unparseable artifact ⇒ honest empty panel (never a 500 / blank crash); contaminated factor slips through ⇒ prominent red tripwire (never hidden); backend down ⇒ contained "Backend unavailable" card with nav intact (anti-goal #8).

## NOTES

- **Depth = full, justified (self-check #4):** backend+frontend boundary crossing; touches the certification/referee machinery with a DATA-INTEGRITY dominant failure mode (real ledgers/budget must stay byte-identical); needs new tests beyond browser smoke (seeded determinism + isolation). NOT ESCALATE-forced (prior verdict CONTINUE) — the triggers independently mandate full.
- **Isolation is the crux** (B-102 dominant failure mode + Traps): run `certify_edge` / `verify_edge` against a THROWAWAY `ledger_path` and/or a fresh `RefereeState`; NEVER the real ledgers, NEVER the real Thresholdout budget, NEVER tuning referee constants. Verify byte-identity of all three real state files + the budget. This is the session's recurring "git diff HEAD on the certification economy must be EMPTY" regression-proof (iter-9 lesson) — here it is also the journey's own pass criterion.
- **OOM guardrails (iter-24 + iter-26 lessons; anti-goal #8):** the harness runs `certify_edge` (block-bootstrap) up to 200× — bound it, reuse existing per-cohort bounded forward-return paths, NO unbounded whole-table ORM load. The 200-trial run is OFFLINE (persisted artifact); browser-qa reads the artifact and does NOT re-run 200 trials live. The CI variant uses a tiny synthetic fixture and never imports the full seed.
- **Artifact reproducibility (assumption logged in `runs/goal-session-mcp-loop/state/assumptions.md`):** J-22's "run the job" + "reproduces exactly" acceptance is satisfied by a bounded/offline SEEDED run that persists the artifact (the panel + browser-qa read the persisted artifact) plus the seeded fast CI test proving exact reproduction — NOT a live 200-trial browser-driven run (mirrors the iter-35 J-21 two-halves decomposition).
- **Canonical-lane discipline (iter-13/20/22/31 lesson):** if the auditor fixes the rendered panel AFTER the browser-qa lane runs, re-run the canonical browser-qa lane against the fix before closure — an audit self-check is not the DoD-named lane, else J-22 lands `partial`.
- **Required-still-passing rationale:** J-01/J-03/J-05/J-11 are the direct readers of the evidence-status/ledger value the audit harness must NOT pollute (byte-identity is the dominant risk); J-17/J-18/J-19 are the three sibling governance surfaces under the same Research grouping the new page joins; J-20 is the cross-cutting preflight banner that renders on the new page.
- **Scope contingency (card sizes B-102 at ~2 iters — "split: harness+CI first, panel second"):** default here is the WHOLE J-22 in one FULL iter (matches the session norm — J-17/18/19/21 each landed passing in one full iter; J-21 is the closest precedent: a new artifact-producing module + reader landed clean in one full iter). IF the harness proves larger than one iter can safely carry, the sanctioned fallback is the card's split — land harness+CI+artifact here (J-22 → `partial`) and ride the panel into the next iter; do NOT bundle any second journey to compensate.
- **Module convention:** follow the session's governance pattern (dedicated `app/engine/referee_audit.py` + `app/api/referee_audit.py`, as budget/registry/graveyard each used a dedicated module), rather than appending to the large existing `research.py` — same "standard lab triple" the B-102 card intends.
