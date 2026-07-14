# Goal Iteration 33 — Single daily preflight verdict (GO/DEGRADED/NO-GO) guards every decision surface

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** mcp-loop
- **Iteration:** 33
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-20
- **Required-still-passing journeys:** J-01, J-02, J-04, J-05, J-11, J-13, J-18
- **Anti-goal reminders:** (restated verbatim from `docs/goal.md`; all eight hold — the load-bearing ones for this iteration are #1, #2, #3, #5, #8)
  - A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked values MUST render a "not yet proven" state. *(critical)*
  - **Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha claims; never place or simulate orders. *(critical)*
  - A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation for the same as-of date — not merely that the page renders. *(critical)*
  - **No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of; never introduce lookahead anywhere. *(critical)*
  - No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the post-decompose gate. *(critical)*
  - No hard-coded credentials, API keys, or tokens in source files. *(critical)*
  - **Resilience to data-shape and data-scale change:** widening the data basis (new nulls, broader pools, deeper history) must never crash an existing page or exhaust a service's memory — every existing consumer of a widened field is re-validated, the UI degrades gracefully (contained error boundary, honest "—"/NA placeholder, never a blank application-error page), and unbounded whole-table ORM loads are forbidden on the deep basis. *(critical)*

## GOAL

Ship one canonical daily **preflight verdict** — `GO / DEGRADED / NO-GO` with a plain-language reasons list — computed once in the backend and rendered as an unmissable banner on every decision surface (dashboard, `/stocks`, stock detail, `/watchlist`, `/evidence`, research), so a stale or corrupted board can never be silently trusted.

## BACKGROUND

J-01..J-19 all pass; J-20..J-25 are unbuilt. The iter-32 evaluator (CONTINUE, full) named **J-20 (B-301, the daily-ops keystone)** as the best next target: it is the single risky new surface that other daily-ops journeys read (J-21/B-304 drift will *feed into* this verdict as it lands — priority-rubric rule 3, unblocker). Coherence was COHERENCE-PASS last iter, so no consolidation is owed. Per rule 5 this iteration carries exactly ONE risky surface (J-20 alone); J-22 and the B-113/B-304/B-103 monitors are deferred.

**Depth = full** (justified by three triggers from "Picking depth", and the iter-32 eval's explicit recommendation): this crosses the backend↔frontend boundary (new pure verdict composer + config + additive `/api/health` field + append-only history) and (new layout-level cross-cutting banner + provider extension); it introduces a NEW served value read on every page; and B-301 requires a **per-input-combination fixture matrix** test (beyond browser smoke). This is not ESCALATE-forced (prior verdict was CONTINUE), but full on the merits.

**Binding spec is backlog card B-301** (`docs/improvement-backlog.md` — read in full). Its **dominant failure mode is "UI-recompute (the verdict must be ONE computed value)"** and its trap is "pages computing their own mini-readiness." The single-source design falls out of the existing shell: `apps/frontend/app/layout.tsx` already wraps every page in `ReadinessProvider` (which polls the ONE `GET /api/health`) + a header `HealthBadge`. Mounting the preflight banner **once** in that root layout makes it appear on every surface with zero per-page logic. B-301 also says explicitly: "**ship with whatever inputs exist and add the rest as they land**" — the enriching monitors B-113 (sentinel), B-304 (drift = J-21), B-103 (time-machine) are **not built yet**, so this iteration composes the verdict from the inputs that exist now (snapshot servability, data freshness, DB/ledger integrity) and leaves a clean seam for the rest.

**Lessons carried into this iteration** (episodic memory — see NOTES for how each is honored):
- **Single-source discipline** (blueprint compute-once-serve-verbatim; B-301 "UI-recompute" failure mode): the banner reads ONLY the `/api/health` `preflight` field via the existing provider — never a second fetch, never a per-page recompute.
- **iter-13/20/22/31 "audit-fix-not-canonically-re-run = partial" trap**: J-20 renders a NEW surface; if any audit fix touches the banner *after* the browser-qa lane runs, the canonical lane MUST be re-run against the final build before closure (or J-20 lands `partial`).
- **iter-11/13/14/25 reused-frame / blank-viewport capture**: the GO-vs-DEGRADED/NO-GO frames must be md5-distinct and pixel-show the banner text; prefer full-page/element-clip captures.
- **iter-18/24/26 anti-goal #8 crashes were all on load paths**: the `preflight` field rides the ~2 s-polled `/api/health`; it MUST stay cheap (small-file JSONL reads for ledger integrity; the existing item-G-memoized readiness inputs) — **no whole-table ORM load**, DB-down → honest verdict not a crash.

## IN SCOPE

### Backend
- [ ] New PURE composer `app.engine.readiness:compute_preflight(session, config, ...)` returning `{verdict: "GO"|"DEGRADED"|"NO-GO", reasons: [<plain-language strings>], components: {<input>: {ok, severity, detail}}, as_of/reference}`. It **composes over inputs that exist now**:
  - **snapshot servability** — reuse the existing readiness signal (latest data date has a persisted run; the same `compute_readiness` liveness check) — no second computation.
  - **data freshness** — latest bar age vs a **deterministic** config-resolved reference, **market-calendar aware** (reuse the SPY trading-day calendar the engine already builds), threshold `readiness.freshness_max_age_days`. See Data-contract additions + NOTES for the determinism requirement (NO wall-clock `date.today()`).
  - **DB/ledger integrity quick-check** — DB reachable AND the canonical/staging/registry JSONL files exist and parse (tiny-file reads only — never an ORM whole-table scan).
- [ ] Config-driven **component→severity mapping** (which breached input forces `DEGRADED` vs `NO-GO`), plus `readiness.freshness_max_age_days` — new `readiness:` config block in `config.yaml` + a typed `ReadinessCfg` in `app/config.py` (no literals in the module; mirrors the existing `startup:`/`StartupCfg` pattern). Severity map must make BOTH a `DEGRADED` and a `NO-GO` state inducible for the test matrix.
- [ ] **Extensibility seam:** adding a future input (B-113/B-304/B-103) must be a config-entry + one component branch, not a rewrite — leave the monitors' own logic untouched (B-301 "Do NOT touch: individual monitors' logic — the verdict composes").
- [ ] Serve the verdict as an **additive `preflight` field on the EXISTING `GET /api/health`** (`app/api/health.py`) — the single readiness/health path (B-301: "serve via existing health/readiness path (single source)"; "health payload shape (additive)"). NO new endpoint. `compute_readiness`'s existing `state`/`warmup` output stays **byte-identical** (J-40 readiness badge + warming states must not regress).
- [ ] Small **append-only verdict-history** log written **only on a verdict transition** (not on every poll — bounded growth), config-resolved path, honest + deterministic (B-301 DoD "verdict history recorded"; serves the future B-307 digest). Minimal; not on the journey-critical browser path.

### Frontend
- [ ] New layout-level `PreflightBanner` component mounted **once** in `apps/frontend/app/layout.tsx` (in the shell, above `<main>`), reading the `preflight` field via the EXISTING `ReadinessProvider` context (extend the provider to expose `preflight` from the SAME single `/api/health` poll — do NOT add a second fetch path; add the `preflight` type to `lib/api.ts` `HealthStatus`).
- [ ] Banner states per the DESIGN SYSTEM tokens (`--pos`/success, `--warning`, `--danger`): **GO = quiet** (a thin, non-intrusive strip that does not disrupt existing page layout — protects the required-still-passing set); **DEGRADED = loud** amber banner listing the concrete reasons; **NO-GO = loud** danger banner listing the reasons and containing the **exact phrase "do not rely on today's board"**. Honest degradation: backend-down / empty-or-unparseable ledger → an honest `DEGRADED`/`NO-GO` with the reason (never a fabricated `GO`, never a blank crash).

### New user-facing capability
Every decision surface now carries one canonical readiness verdict: at a glance the user knows whether today's board is safe to trust (`GO`), suspect (`DEGRADED`), or must not be relied upon (`NO-GO`), with the concrete reasons — a risk-officer kill-switch UX.

### New information displayed
The `GO/DEGRADED/NO-GO` verdict + its reasons list, identical on every page (one source). No new numbers, scores, or edges — descriptive operational status only.

### New user actions
None — the banner is read-only status (no buttons/forms; it gates *trust*, not orders — anti-goal #2). It is discoverable simply by being present on every page.

### UI surface changes
One new cross-cutting layout-level banner in the app shell (`app/layout.tsx`), visible on dashboard, `/stocks`, `/stocks/{ticker}`, `/watchlist`, `/evidence`, `/research`, and every other page. No new page, no nav change.

### Product surface delta
The product gains a persistent, single-source safety verdict — the "is the board safe today?" answer that daily operation hangs on. Later journeys (J-21 drift, and B-113/B-103 monitors) enrich the SAME verdict rather than adding parallel indicators.

### Blueprint conformance
The preflight banner is a **cross-cutting layout-level chrome element** (like the existing `HealthBadge`), NOT a new page and NOT a new nav section — so **no nav-skeleton change and no `blueprint.reapproval-requested`**. `blueprint.md` is edited additively: a J-20 row is added to the Information Architecture homes table (canonical home = the app-shell layout banner + the `GET /api/health` `preflight` field), and an iter-33 clarification paragraph is appended.

### Data-contract additions
ONE new displayed value, registered in `blueprint.md`'s Data Contract in this same change:

| Value | Computed once by | Served by | Reader |
|---|---|---|---|
| **Daily preflight verdict** — `GO/DEGRADED/NO-GO` + reasons list | `app.engine.readiness:compute_preflight` (pure composition over the existing readiness servability signal + data-freshness + DB/ledger integrity; extensible for B-113/B-304/B-103) — recomputes NO canonical value | additive `preflight` field on the EXISTING `GET /api/health` (the single readiness/health path; no new endpoint) | ONE reader: the layout-level `PreflightBanner`, mounted once in `app/layout.tsx`, fed by the existing `ReadinessProvider` — no per-page recompute |

Notes for the Data Contract row: carries **NO proven-language** (it is operational trust status, never a "Proven"/"Not yet proven" signal — that still flows solely from `verdict.status==PASS` via `GET /api/evidence`); **deterministic** (freshness anchored to a config/seed-derived reference, never wall-clock); DB-down / empty-or-unparseable ledger → honest `DEGRADED`/`NO-GO`, never a blank crash (anti-goal #8); does NOT re-fetch or re-derive `latest_data_date`, snapshot servability, or the ledger files anywhere except inside this one composer.

## OUT OF SCOPE

- **B-113 sentinel-anomaly detectors, B-304 live-vs-seed drift monitor (= J-21, the NEXT journey), B-103 time-machine, B-302 alerting, B-307 digest** — the composer only leaves a seam for them; building any is a separate journey (rule 5: never bundle a second risky surface). J-21 will *feed* the verdict later; do not start it here.
- **Any evidence/ledger write or Evidence Claim** — this iteration ships NO `## Evidence Claim`, does ZERO evidence work; `certified-claims.jsonl` / `staging-ledger.jsonl` / `pre-registrations.jsonl` stay byte-identical; canonical Bonferroni divisor stays 8; no closed FAIL re-submitted.
- **Any change to `compute_readiness`'s existing `state`/`warmup` output** — J-40's readiness badge + warming states must stay byte-identical (add `compute_preflight` alongside, don't mutate the readiness contract).
- **Any new page or nav section** — the banner is layout chrome only.
- **Per-page/mini readiness** — B-301's explicit trap; one payload, one reader, no page-local logic.

## DEFINITION OF DONE

- [ ] **J-20 passes via browser-qa-agent.** Step 1: the SAME quiet `GO` banner is pixel-visible on dashboard, `/stocks`, a stock detail, `/watchlist`, and `/evidence` (one md5-distinct frame per surface). Step 2: under the controlled inducement, EVERY listed surface shows the SAME `DEGRADED`/`NO-GO` banner with the concrete reasons; the `NO-GO` banner contains the exact text **"do not rely on today's board"** (md5-distinct GO-vs-induced frames). Step 3: the verdict + reasons come from the ONE `/api/health` `preflight` field — no page computes its own (DOM/asserted).
- [ ] **Correctness matrix:** a backend fixture test drives each input combination and asserts the exact mapped verdict (`GO`, `DEGRADED`, `NO-GO`) per the configured severity map.
- [ ] **Single-source:** the `preflight` value is produced only by `compute_preflight` and served only on `GET /api/health`; the banner reads only the provider context (no second client fetch/compute) — verified by test/inspection.
- [ ] **No anti-goal violation:** banner carries no proven-language / no buy-sell-order language (#1/#2); DB-down + empty/unparseable-ledger → honest verdict, no blank crash, no whole-table ORM load on the health path (#8); freshness deterministic, no wall-clock (#5).
- [ ] **Required-still-passing green:** J-01, J-02, J-04, J-05, J-11, J-13, J-18 re-verified (deterministic replay); the GO banner does not disrupt their surfaces. **J-11 gets a dedicated golden replay** (`runs/goal-session-mcp-loop/journey-scripts/J-11.json`) to close the iter-32 6-of-7 replay gap.
- [ ] `compute_readiness` `state`/`warmup` output byte-identical (J-40 not regressed).
- [ ] Unit/integration tests pass; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-mcp-loop-iter-33-dev.md`.

## TESTING REQUIREMENTS

- **Browser (J-20, the target):** on each of dashboard `/`, `/stocks`, `/stocks/{ticker}`, `/watchlist`, `/evidence` — (1) healthy state shows the identical quiet `GO` banner; (2) after the controlled inducement (config/env lever that points freshness stale — see NOTES), the identical `DEGRADED`/`NO-GO` banner with reasons, `NO-GO` containing "do not rely on today's board"; (3) the banner value is single-source. Capture md5-distinct full-page/element-clip frames per surface per state; restore the healthy state afterward.
- **Required-still-passing replay:** J-01, J-02, J-04, J-05, J-11, J-13, J-18 (J-11 dedicated).
- **Unit/integration:**
  - `compute_preflight` per-input-combination fixture matrix → exact verdict + reasons (the B-301 correctness bar).
  - Severity-map / freshness-threshold config wiring (verdict changes with config, not with a literal).
  - `compute_readiness` `state`/`warmup` unchanged (snapshot/byte-identity test).
  - Health payload additive-`preflight` shape test; single-source (no second read path).
  - Verdict-history append-on-transition (appends on change, not on every poll).
- **Error cases (must be rejected / degrade honestly, never a fabricated GO):** DB unreachable → `NO-GO`/`DEGRADED` with the DB reason; missing or unparseable ledger file → the integrity reason; freshness beyond the configured max age → the mapped stale verdict; the health probe must not raise or blank under any of these (anti-goal #8).

## NOTES

- **Freshness-anchor interpretation (logged to `assumptions.md`, iter-33 — goal-decomposer).** B-301 says "data freshness (latest bar age vs expectation)… market-calendar aware," but Trendora is offline/deterministic against a **frozen committed seed** (goal.md Constraints), so "now"/"expectation" is undefined and a wall-clock `date.today()` would (a) make GO impossible (the seed is always "stale" vs real today) and (b) break determinism (anti-goal #5). **Chosen reading:** freshness is anchored to a **deterministic config-resolved reference** (default = the seed's own latest available date, so a fully-loaded seed reads `GO`), counted in trading days via the existing SPY calendar, and the induced-stale test state is produced by a **config/env override** (lower `readiness.freshness_max_age_days`, or pin the reference forward) — never `date.today()`. Reversible.
- **Inducement lever for the test.** Because B-113 sentinel is unbuilt, the freshness component is the available lever for J-20 step 2. Use a controlled config/env override to force the stale (DEGRADED/NO-GO) verdict deterministically, then restore GO — do NOT mutate committed seed data.
- **Post-lane fix discipline (iter-13/20/22/31 trap).** J-20 is a rendered surface. If review/audit applies any fix to the banner or verdict *after* the canonical browser-qa lane runs, dispatch a fresh browser-qa + ux-regression re-run against the final build before closure — a `qa.md`/`status.json` PASS over a stale browser-qa FAIL does NOT satisfy "pass via browser-qa-agent," and J-20 would land `partial`, not `passing`.
- **Pre-QA hygiene (iter-20 lesson).** `rm -rf apps/frontend/.next` and confirm BOTH prod-mode services reachable before dispatching browser-qa; a layout-level change is exactly the case a stale `.next` bundle hides.
- **Anti-goal #8 on the health path (iter-18/24/26).** The two prior critical #8 crashes were unbounded load paths. The `preflight` field rides the ~2 s-polled `/api/health`; keep every integrity read to small-file JSONL + the already-memoized readiness inputs — no `select(...).all()` whole-table load.
- **Showcase deliverable (J-20 goal.md acceptance).** A `[NEW]`-flagged walkthrough of the GO and induced NO-GO states across two surfaces, viewable via `demo.sh mcp-loop --session-live`, is produced by the showcase/demo-narrator step of the goal loop — noted here so it is not missed; the binary executor gate is the browser-qa + matrix above.
- **Carry-forwards (do NOT bundle):** readme-maintainer to add the budget-panel bullet (iter-32 coherence advisory) + a preflight bullet; audit B1 (mirror `verify_edge`'s `use_fdr` gate in `budget_accounting._staging_section` only if `evidence.fdr.enabled` becomes a runtime toggle).
- **Path to goal:** J-20 is one of six remaining (J-20..J-25). After it, ~5 one-surface iterations (J-21 drift → J-22 certifier-audit → J-23/J-24/J-25 risk analytics) close the goal — a tractable path, not a plateau.
