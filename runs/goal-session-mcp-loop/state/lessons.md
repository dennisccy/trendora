# Goal Session mcp-loop — Lessons Learned

Append-only ledger of takeaways from prior iterations. The goal-evaluator
appends one entry per iteration; the goal-decomposer reads this file before
planning each iteration to avoid repeating known pitfalls.

Each entry should be 1-3 sentences capturing a non-obvious lesson — surprising
failures, regression triggers, or decisions that worked well. Avoid
restating the verdict (the evaluator-log.md already does that).

## iter-0 — 2026-06-29T20:53:00Z

**Verdict:** ESCALATE
**Lesson:** The lean pipeline silently produced NO browser-QA evidence this iteration — telemetry.jsonl had no `browser-qa-agent` record (the sequence jumped reviewer → goal-evaluator), status.json stayed at `current_step: dev_complete` / `browser_checks_run: false`, and neither `reports/phase-<iter>-ui-test-results.md` nor the expected SKIPPED stub (goal-iter-lean.sh:392) was written. Do not infer journey pass/fail from the developer's static code scan; confirm the browser-qa-agent actually ran before scoring, and seed journeys as `unknown` (not `failing`) when it did not.
**Applies to:** any lean iteration / any baseline iter-0 — the evaluator should verify a `browser-qa-agent` telemetry record + a non-empty evidence dir BEFORE recording journey verdicts; a missing ui-test-results file should drive ESCALATE (force full), per goal-iter-lean.sh's own design intent (lines 185, 396).

## iter-1 — 2026-06-29T22:37:16Z

**Verdict:** CONTINUE
**Lesson:** The read-side "Proven" path is built but cannot light up yet: the real ledger writer `app.mcp.tools.verify_edge` appends a cohort-selector `claim` with NO `signal` key, while the read side keys `proven_signals` on `claim.get("signal")` (fail-safe). So even a genuine referee PASS would map to NO UI signal and stay "Not yet proven" — the first certified iteration MUST stamp the canonical signal key (`leadership_score`/`entry_quality_score`/`risk_score`) on the written claim, or J-01/J-02's Proven badge will silently never appear despite a passing ledger entry. (Also: against an empty ledger, J-05 steps 2-3 — populated claim row + claim->surface linkback — are structurally un-exercisable, so J-05 caps at `partial` until ≥1 claim is certified; don't score it `passing` on the empty-state surface alone.)
**Applies to:** the first certified iteration and any iter proposing a `## Evidence Claim` / touching `app.mcp.tools.verify_edge`, `app.engine.evidence`, or the `/evidence` page — verify the writer stamps `claim.signal` and that a PASS actually flips a badge end-to-end (browser-verified), not just that the ledger row exists.

## iter-2 — 2026-06-30T01:08:00Z

**Verdict:** CONTINUE
**Lesson:** A FULL iteration's QA agent returned PASS / "READY TO SHIP" while SKIPPING every browser test (frontend stuck on "Checking backend..." → empty leaderboard at /stocks), justifying it with build+units+API-curl alone; status.json honestly recorded browser_checks_run=false and no audit handoff was produced. This is exactly the over-trust the iter-1 lesson warned against: a certified ledger row + green build/units/API is NOT proof the user-facing badge flip and proof-drill render. The root cause was harness connectivity (frontend :3255 could not reach backend :8255), not application code — but it silently nullified the iteration's entire verification value.
**Applies to:** any goal-mode iteration whose Definition of Done is user-journey/browser-verification — treat browser_checks_run=false OR an all-SKIP ui-test-results.md as a HARD verification gap (journeys stay unknown/partial, never passing), regardless of a QA PASS. Before re-running the browser lane, confirm the frontend can actually reach the backend (service-start order, API base URL, health proxy) — a single empty-leaderboard screenshot is the tell.

## iter-3 — 2026-06-30T02:42:00Z

**Verdict:** CONTINUE
**Lesson:** Browser-QA captured four screenshots named for the expanded "Why proven?" proof panel (UT-07/UT-08/TC-05/UT-16) that were byte-identical full-page-top frames — the panel renders BELOW the fold and was never actually in any captured viewport. J-02 was only confirmable because the identical OOS values (PASS/+6.36%/p=0.0004998/n=12,297/vs SPY/registered 2026-06-30) render in a clear frame on /evidence (UT-12, single source of truth) AND the in-panel linkback navigated (UT-09). A screenshot named for a disclosure/expander proves nothing about the expanded state unless the target element was scrolled into the viewport first.
**Applies to:** any iter that browser-verifies an expand/disclose/drill-down/below-the-fold interaction — next up J-04's regime-conditioned evidence panel. The browser-qa-agent must scroll the target element into frame before capturing, and the evaluator should treat a panel-named screenshot that only frames the page header as a visual-evidence gap (lean on an independent same-value render + a confirmed in-component link as corroboration, never the named screenshot alone).

## iter-4 — 2026-06-30T04:05:00Z

**Verdict:** CONTINUE
**Lesson:** There are TWO independent browser lanes and they can DISAGREE: the canonical
`browser-qa-agent` (writes `reports/phase-<iter>-ui-test-results.md`, UT-* screenshots) and the QA
agent's own Chrome MCP run (writes `reports/qa/<iter>-qa.md`, TC-* screenshots). In iter-4 the canonical
lane reported all 11 SKIP ("frontend not running") while the QA lane PASSED 15/15 with real working
screenshots — root cause: a stale `next-server` held :3255 serving an old bundle, and `start-frontend.sh`
(unlike `dev.sh`) does NOT `fuser -k` the port before binding, so whichever lane ran first hit EADDRINUSE
/ stale UI. The fix is operational: free :3255 before the browser-qa lane binds. Evaluator discipline: a
parallel QA-lane PASS (even with genuine pixels) does NOT substitute for the canonical lane on the
terminal GOAL_ACHIEVED gate — withhold success until the canonical lane renders all journeys and the
post-QA audit handoff exists (the audit stage stopped at `qa_complete` in both iter-3 and iter-4).
**Applies to:** any browser-verified iteration, especially the terminal GOAL_ACHIEVED gate — check both
`ui-test-results.md` (canonical) AND `<iter>-qa.md` (QA lane); reconcile a SKIP-vs-PASS split via the
port; and confirm `start-frontend.sh` frees the frontend port before binding.

## iter-5 — 2026-06-30T05:30:00Z

**Verdict:** CONTINUE
**Lesson:** The iter-4 diagnosis ("canonical lane SKIPs because a stale next-server holds the frontend port") was only ONE of the failure modes, and not the one that bit iter-5. The iter-5 port-free fix to `scripts/start-frontend.sh` is correct but the canonical browser-qa-agent lane never reached the port-binding step: per `runs/goal-session-mcp-loop/engine.log` L402-413 the post-dev parallel **Branch-UI** chain aborted upstream at `ui-test-design` ("phase-*-user-visible-changes.md not found" even though `ui-impact-phase.sh` reported writing it), so browser-qa-agent + ux-regression + closure never ran AND `reports/phase-*-iter-5-ui-test-results.md` was wholly absent (not all-SKIP). Separately, the `update_status` call with `invalid step 'post_dev_parallel_complete'` (L412-413, also iter-4 L343) makes the "sequential retry" fallback bail, which is why the AUDITOR has now failed to run three iterations running (iter-3/4/5). Net: when a verification artifact is missing, read `engine.log` to find WHERE the pipeline actually died — don't assume the previously-hypothesised cause; and never let QA-parallel-lane (`reports/qa/*-qa.md`) UT-*-named screenshots stand in for the canonical lane (`reports/phase-*-ui-test-results.md`), especially when they contain byte-identical duplicates (UT-07≡UT-09 here).
**Applies to:** any goal-mode iteration whose DoD depends on the canonical browser-qa-agent lane or the post-QA auditor running — i.e. any iter that must flip a journey partial→passing via fresh canonical pixels, or that lists the audit handoff as a DoD item. Check `engine.log` for `Branch-UI ... aborting chain` and `invalid step 'post_dev_parallel_complete'` before trusting any GOAL_ACHIEVED.

## iter-6 — 2026-06-30T06:30:00Z

**Verdict:** GOAL_ACHIEVED
**Lesson:** A harness defect that must take effect *mid-run* has to live in a component re-invoked as a fresh subprocess each step — here the child scripts (`ui-impact-phase.sh`/`ui-test-design-phase.sh` rc==0 post-condition guards) and `lib/verdicts.py` (the `post_dev_parallel_complete` enum) fixed the canonical-lane + auditor aborts the same run, whereas the `run-phase.sh:645-651` parent edit only lands on the next dispatch (bash tracks a running parent by byte offset). Three straight iters stalled because the real death points (engine.log: ui-impact phantom "Done" → ui-test-design missing-file abort at 04:40:01, and the invalid-step abort at 04:43:47) sat two steps upstream of the port fix iter-5 chased. Separately, `browser_checks_run` in status.json is a DEAD flag — no harness path ever sets it true — so never gate GOAL_ACHIEVED on it; judge on the canonical `…-ui-test-results.md` + engine.log.
**Applies to:** any goal-mode iteration that repairs the verification harness mid-run, and any future goal-evaluator run that sees `browser_checks_run:false` despite a real canonical-lane PASS.

## iter-8 — 2026-06-30T22:12:00Z

**Verdict:** GOAL_ACHIEVED
**Lesson:** A GENERAL read-side cohort matcher (`resolveCohortEvidence` in `apps/frontend/lib/evidence.ts`) lights "Proven" on EVERY certified cohort it matches — including a score-column factor (`leadership_score`) that also appears as a factor-lab row. The spec's parenthetical only named vcp_contraction, but lighting leadership_score too is HONEST and correct (it has a genuine PASS ledger entry; anti-goal #1 only bans UNBACKED "Proven"), NOT a defect — provided the badge deep-links via `claimAnchorId` to the row's REAL `signal-…` anchor and not a `factor-…` cohort anchor the row never carries. Do not "fix" this by special-casing the matcher to vcp-only; suppressing a true status would be the dishonest move.
**Applies to:** any iter that touches the factor-lab evidence matcher / `resolveCohortEvidence` / `claimAnchorId`, or adds a new certified cohort whose factor doubles as a score-column row — expect (and allow) every certified cohort to read "Proven", and assert the deep-link lands on the row's actual anchor.

## iter-9 — 2026-07-01T01:52:58Z

**Verdict:** CONTINUE
**Lesson:** For a backend-only refactor of a *shared value's computing module* (here referee/ledger/verify_edge behind every "Proven" badge), the regression proof is NOT a browser pass — it is (a) the shared value's canonical output being git-UNMODIFIED / byte-identical (`certified-claims.jsonl` + `GET /api/evidence` frozen-golden) and (b) the module's existing default-path tests being UNEDITED and green (`git diff test_referee.py` == 0 lines). An unedited passing suite is the strongest possible proof "defaults reproduce today"; if a future iter had to EDIT those expectation tests, that is itself the regression signal. Judge on this, never on the dead `browser_checks_run` flag or a SKIPPED browser lane (which is correct for a no-frontend-diff iter).
**Applies to:** any iter touching `apps/backend/app/engine/{referee,ledger,forward_walk}.py` or `app/mcp/tools.py:verify_edge` (the shared certification engine) — especially the upcoming iter-10/iter-11 that reuse this economy.

## iter-9b — 2026-07-01T01:52:58Z

**Verdict:** CONTINUE
**Lesson:** iter-9 flipped the gate's default ledger to `"staging"` (`project-extensions/gates/verify_claim.py`) — the conservative direction (a forgotten key ⇒ "not shown as proven", never "wrongly proven"). But this is a real footgun for the very next iterations: a J-07/J-08 winner meant for the user-facing badge that omits `"ledger":"canonical"` in its `## Evidence Claim` gets certified into the internal staging ledger and SILENTLY never surfaces on `/evidence` or the factor lab — the journey would fail to build with no gate error. The badge-bound claim MUST set `"ledger":"canonical"` explicitly.
**Applies to:** iter-10 (J-07 multi-horizon) and iter-11 (J-08 combination) — any iter whose Evidence Claim is intended to light a user-facing "Proven" badge.

## iter-10 — 2026-07-01T04:19:25Z

**Verdict:** CONTINUE
**Lesson:** When a staging discovery clears the bar at the block-bootstrap p-FLOOR (`p = 1/(B+1) = 0.00049975`), the p-value alone cannot rank winners — it is saturated. iter-10 found THREE h60 PASSes all at the identical p-floor, so the `holdout_edge` magnitude is the tiebreaker: `rs_spy_3m` h60's `+0.2134` edge is implausibly large (auditor B3 flagged it) next to `vcp_contraction` h60's modest `+0.089`. For canonical promotion prefer the signal-less winner with the more credible, modest edge — a p-floor PASS with an outsized edge is a yellow flag, not the strongest candidate. Two mechanical traps on promotion: (1) the gate defaults an omitted `"ledger"` key to `staging`, so a promotion `## Evidence Claim` MUST set `"ledger":"canonical"` EXPLICITLY or the winner is silently re-certified into staging and never surfaces; (2) a canonical PASS permanently appends to `certified-claims.jsonl` and tightens the user-facing Bonferroni divisor (5→6) forever — so promote only a candidate whose recorded raw p already clears required_p=0.010 (the iter-8 ma_stack bar-tightening disaster is the counter-example).
**Applies to:** any iteration that promotes a staging discovery to the canonical ledger via a `## Evidence Claim` — iter-11 (J-07 vcp_contraction h60), iter-12+ (J-08 combinations), and any future canonical "Proven"-badge write.

## iter-11 — 2026-07-01T06:31:31Z

**Verdict:** CONTINUE
**Lesson:** browser-qa PASS 15/15 and an AUDITOR PASS claiming "scrolled-into-frame screenshots" both passed unchallenged, but `md5sum reports/qa/goal-mcp-loop-iter-11-evidence/*.png` collapsed 11 PNGs into 3 distinct images — one factor-lab-top + one evidence-top + one backend-unavailable, relabeled across every UT id. NONE of them shows the asserted h60 chip, h60 /evidence row, or vcp h20 chip scrolled into the viewport (the exact iter-3 lesson the spec cited verbatim). J-07 still legitimately passed because its assertions were DOM/JS-eval based against a live backend and converged with a byte-exact `git diff` on certified-claims.jsonl + green unit tests — so the pixel gap was a documentation-hygiene issue, not a functional failure. Takeaway: (1) always md5 the evidence PNGs — a screenshot referenced by N test ids can be one reused capture; (2) do NOT trust an auditor's "screenshots show X" claim without spot-checking pixels; (3) when pixels are weak, ground the pass in the DOM assertions + the byte-exact ledger/unit-test triangle, not the images.
**Applies to:** any iter surfacing an evidence badge/row that must be "scrolled into view" (factor-lab / factor-combination / evidence rows below the fold); any evaluation where the browser-qa report references the same-named or same-size screenshot across multiple assertions.

## iter-12 — 2026-07-01T07:59:28Z

**Verdict:** CONTINUE
**Lesson:** The iter-11 evaluator's next-step ("iter-12 promote a combination whose recorded raw p clears the divisor-6 bar") rested on a FALSE premise — it assumed a combination staging exploration already existed the way the single-factor one did after iter-10. It did not: `config.triad.candidates`, `_staging_candidates`, `explore_multi_horizon_staging`, and the staging ledger were ALL single-factor-only, so NO combination had ever been certified and no recorded p existed. Blind-promoting anyway would have been the iter-8 `ma_stack` disaster (a canonical FAIL permanently tightens the Bonferroni bar AND blocks the iteration). The decomposer correctly verified the precondition against the actual code/ledger and inserted a discovery iteration (register set → explore into staging → record p) before promotion. Domain aside: the two "obvious" anchor pairs (low-ATR filter over momentum / over leadership) FAILED OOS with negative holdout edge; only the non-obvious `rs_spy_3m + high_proximity` (leaders also near their 52-wk high) passed — the referee doing its honest job.
**Applies to:** any iter whose spec says "promote the staging winner" or "clear the divisor-N bar" — VERIFY the recorded staging verdict actually exists (grep the staging ledger for a matching cohort with a recorded `p_value`) before recommending or attempting a canonical promotion; never trust a prior evaluator's recommendation that a basis exists. Also: any promote-a-winner iter must set `"ledger":"canonical"` EXPLICITLY (omitted key silently re-stages).

## iter-13 — 2026-07-01T10:17:36Z

**Verdict:** CONTINUE
**Lesson:** A fix the auditor applies AFTER the browser-qa lane has already run does NOT count toward journey verification unless a browser-qa RE-RUN follows — the closure gate correctly caught this (audit fixed the `/evidence` hash-scroll at 10:51, browser run was 10:17-10:33, no re-run → CLOSURE-FAIL, verdict left unverifiable). Separately, the browser-qa DOM-text assertions silently diverged from the saved pixels: UT-03 asserted a `<a data-proven=true>Proven</a>` element but its screenshot (md5 e866ea14, reused by UT-01/04/11) is a relabeled DEFAULT-state frame showing the FAILED rs_spy_3m × atr_pct pair reading 'Not yet proven'. For a terminal GOAL gate, open the actual claimed-'Proven' screenshot and confirm the CERTIFIED selection is composed in-frame — do not trust the PASS label or the DOM-text line.
**Applies to:** any terminal/GOAL_ACHIEVED-candidate iteration; any iter where the auditor applies a UI fix post-browser-qa (require a re-run before the evaluator can treat the journey as passing); any iter whose evidence PNGs collapse to a few md5s (verify the badge-flip frame actually shows the asserted state + selection, and that the backend was up — a 'Backend unavailable' pill on an /evidence capture invalidates a fail-safe 'Not yet proven' reading).

## iter-14 — 2026-07-01T12:22:00Z

**Verdict:** GOAL_ACHIEVED
**Lesson:** The recurring "blank/relabeled deep-link screenshot" failure (iter-3/11/13) was finally defeated not by fixing the scroll but by changing the CAPTURE MODE: a headless-Chrome *viewport* screenshot taken while the window is programmatically scrolled below the fold returns a ~5855-byte blank dark frame (a compositing/repaint artifact), whereas a **full-page** capture renders the scrolled-to element cleanly. For any below-the-fold / deep-link / disclosure verification, prefer full-page or element-clip captures over a scrolled viewport capture, and md5-check to spot the tell-tale identical tiny blank frames. Separately, the terminal gate was made trustworthy by opening the actual "Proven" frame and confirming the CERTIFIED selection was composed in-frame (leg 2 = high_proximity, not the config-default atr_pct) — never trust a PASS label or a DOM-text line alone for a GOAL gate.
**Applies to:** any iter verifying a below-the-fold, deep-link, or disclosure element via browser-qa screenshots; any terminal GOAL_ACHIEVED gate that hinges on a single "Proven"/success frame.

## iter-15 — 2026-07-01T13:32:59Z

**Verdict:** GOAL_ACHIEVED
**Lesson:** The phase audit's F1 declared "no screenshot shows the rs_spy_3m h60 money frame," but the /evidence money frame WAS captured — in `UT-01-initial.png` (md5 583c1b11, 379 KB, full-page), an un-referenced capture the audit missed while focused on the QA-report-cited frames (TC-02/TC-03) and the reused 5855-byte blank frames. When a report claims a visual gap, independently `md5sum` every evidence PNG and open the LARGEST distinct captures before accepting "pixels are weak" — the money frame is often in an un-cited full-page shot. Separately: a canonical claim whose out-of-sample edge (+0.2134) is ~10× its in-sample edge (0.0204) — the opposite of normal OOS shrinkage — is a real data-quality yellow flag; it is honest to surface ONLY because it is a genuine referee PASS out-of-sample + displayed verbatim + the seeded-data/engine magnitude is out of scope (anti-goal #5 determinism). It is NOT an anti-goal violation, but every future canonical promotion with OOS≫in-sample should get the same auditor scrutiny.
**Applies to:** any future evaluation that must confirm a "Proven" chip/ledger-row is pixel-visible (md5 + view the largest distinct PNGs, don't trust the report's cited frame or an audit's "missing frame" claim); and any iter promoting a new canonical `certified-claims.jsonl` row whose holdout edge greatly exceeds its in-sample edge.

## iter-16 — 2026-07-02T00:04:05Z

**Verdict:** STALLED
**Lesson:** Two non-obvious takeaways. (1) A pre-registered evaluator guidance in an iteration spec ("score it CONTINUE") can be mechanically self-contradictory by evaluation time: iter-16's own dev handoff + audit both mandated "iter-17 must NOT be scheduled until the human resolves the blocker," yet CONTINUE is precisely what schedules it (run-goal.sh:1499). When every remaining journey is gated on a human action, STALLED — exercised early under the charter's "cannot identify productive next work" provision — is the only verdict whose mechanics honor the evidence; write the eval so the halt reads as loop-viability, not iteration failure. (2) The audit caught a latent env-key leak (httpx HTTPStatusError messages embed the FULL request URL incl. query params, which flowed verbatim into the committed staging meta.json via failure records) — any tool that persists exception text into a committed artifact must redact env-sourced query credentials at the persistence choke points, and the "never persisted" unit test must exercise the FAILURE path, not just construction.
**Applies to:** any future honest-blocked/external-dependency iteration where the unblock is human-only (prefer STALLED-with-menu over CONTINUE-into-a-wall); any tool persisting exception/URL text into committed manifests while carrying env credentials as query params (redact at choke points + test the failure path); the iter-17 swap spec (staged asset + green test_seed_staged_30y.py are hard preconditions — verify the dir exists before planning the swap).

## iter-17 — 2026-07-02T23:48:35Z

**Verdict:** CONTINUE
**Lesson:** The iter-18 sanctioned ledger reset will invalidate ALL seven currently-passing certified edges (J-02/J-04/J-06/J-07/J-08/J-09's specific +6.36%/+6.12%/+3.33%/+8.91%/+4.69%/+21.34% claims) — a mechanical "prior-passing journey now failing → REGRESSION" reading would falsely halt the session; goal.md's data-basis-change provision pre-authorizes this transition ("J-01..J-09 remain valid contracts... but their specific certified edges recompute"), so the iter-18 evaluator must judge honest-badge/correct-number on the REGENERATED ledger, not survival of retired-window edge values. Separately: on a re-dispatched iteration the recorded snapshot-sha can be a mid-flight stash-merge that already CONTAINS the first attempt's work, so `git diff <snapshot>` under-represents the iteration — diff against HEAD + untracked instead (the coherence-auditor caught this; future snapshot capture should run strictly before decompose/dev on re-dispatch).
**Applies to:** iter-18 (the atomic swap + ledger reset — its evaluator and decomposer MUST carry the pre-registration above); any future data-basis change; any re-dispatched/resumed iteration's coherence-auditor or evaluator choosing a diff base.

## iter-18 — 2026-07-07T09:20:00Z

**Verdict:** REGRESSION
**Lesson:** A data-basis / pool-broadening change that makes a backend field newly-nullable (here `scoring.py:377` `cfg.stock_sectors.get(ticker)` → `null` for ~78% of the broadened 548-pool rows) can silently REGRESS a byte-UNMODIFIED frontend consumer into a full-page crash: `apps/frontend/app/stocks/page.tsx:93`'s `a.sector.localeCompare(b.sector)` sort comparator throws an uncaught TypeError on the null, and with no `error.tsx`/`global-error.tsx` it wipes the entire `/stocks` page (nav included). `git diff HEAD` on the component is empty, and `tsc` stayed green only because `api.ts:279` typed `sector: string` (non-nullable) — so BOTH the "empty diff = no regression" heuristic and the type-checker gave false comfort. Two facts compounded it: (a) QA's own functional table had no sector-sort case and the auditor ran with the backend down, so both reported PASS while a `UT-21-fail-crash.png` sat in the cited evidence folder — the ux-regression + closure gates were the only ones that caught it; (b) `status.json`/`qa.md` prose ("zero blockers, ready to ship") directly contradicted a `-fail-`-named screenshot in their own evidence directory.
**Applies to:** any iteration that WIDENS a data contract to introduce nulls/new shapes into an existing served field — enumerate and re-validate EVERY existing consumer (sort/filter/format/`.localeCompare`/`.toFixed`/`.map`) of that field even when those component files have zero diff, and flip the field's TS type to `| null` so the compiler flags the unguarded call sites; also, for evaluators: always reconcile self-reported "zero blockers" against the actual evidence directory (open every `-fail-` frame) and against the ux-regression/closure verdicts, never against status.json/QA prose.

## iter-18 — operator addendum (backend OOM root cause; not recorded in eval.md) — 2026-07-07T13:30:00Z

**Verdict:** REGRESSION (same iteration as above; SECOND unsanctioned defect, distinct from the sector-sort crash)
**Lesson:** The canonical browser-qa lane did not merely "crash at exit 70" — the dev backend under test OOM'd and hung. Trigger chain (from `/tmp/fanout-backend-8255.log`, a transient file — quoted here so the root cause survives): `GET /api/data` → `app/api/data.py:119 data_overview` → `data_manager.py:731 compute_coverage` → `:792 _compute_coverage_uncached` → `prefilled_bar_cache` (`prices.py:206`) → `prices.py:84 prefill` → `session.exec(select(DailyPrice).order_by(symbol, date)).all()` → **MemoryError** (raised inside SQLModel row construction), repeated for ≥6 CONCURRENT `/api/data` probes. The prefill materializes ALL 3,270,066 `daily_prices` rows as hydrated ORM objects (~6.8 GB peak measured for the equivalent load) against the 6144 MB `ulimit -v` cap set by `scripts/start-backend.sh` (`server.memory_cap_mb`; its config.yaml comment still says "~1.3M-row" — stale, the table is 3.27M rows on the 30y basis). eval.md item 2's "keep BOTH services up and staying up" is impossible without fixing this — a re-run browser-qa lane WILL hang the backend the same way on its first `/api/data` visit. The prescriptive fix is **item A of goal.md's "Improvement direction (engineering): fast platform on the deep basis" section** (stream the prefill with `.yield_per` + column-project to lightweight Bar records; ALSO verify the `compute_coverage` single-flight actually serializes cold-key prefills — the log proves ≥6 ran concurrently). Scope containment: ONLY `prices.py:84` is unbounded — the other `.all()` sites in prices.py (`:115` per-symbol lazy, `:253`, `:292`, `:312`) are per-symbol-bounded, do NOT refactor them; any batch/bounds param threaded through `prefilled_bar_cache → prefill` must be OPTIONAL (`test_bar_cache.py` monkeypatch shims at `:91` and `:256` and the 2-arg call at `:102` depend on the current signature), and `ORDER BY symbol, date` + the returned attribute names (`.date/.open/.high/.low/.close/.volume`) must be preserved so `test_bar_cache.py`'s byte-identical snapshot tests stay green.
**Applies to:** iter-19 — the prefill fix MUST ship alongside the /stocks sector-null fix (both blocking; the browser-qa lane completion in eval.md item 2 depends on the backend surviving `/api/data`); any future full-pool prefill / cache-warm path on the deep basis.

## iter-19 — 2026-07-07T16:05:00Z

**Verdict:** CONTINUE
**Lesson:** The durable FIX for a data-contract-widening regression (the iter-18 sector-null crash) is to flip the TS type at the API-contract boundary to `| null` (`lib/api.ts` StockRow.sector) so `tsc --noEmit` mechanically enumerates every unguarded consumer, then route ALL null-handling through ONE shared helper (`lib/sector-label.ts` `sectorLabel`/`compareSectors`, null -> honest "Unassigned"). BUT the shared helper only covers call sites that adopt it: a SEPARATELY-typed pre-existing nullable field silently keeps its old behavior — `return-attribution.tsx`'s already-`string|null` `PerStockRow.sector` still renders a blank omission, not "Unassigned" (audit F3), because it was already guarded a different way and never touched. So after widening a field, grep EVERY structurally-distinct nullable of the same concept, not just the one type you widened. Also a framework-trust signal: the gates that CAUGHT (iter-18) and CLEARED (iter-19) this interaction/data-contract regression were ux-regression + closure + audit — NOT review/QA/status.json, which in iter-18 reported "ready to ship / zero blockers" with the crash frame sitting in their own cited evidence folder.
**Applies to:** any iter widening a data field with new nulls/broader pools/deeper history (anti-goal #8); any iter touching `apps/frontend/lib/api.ts` shared row types or adding a `sectorLabel`-style display helper; evaluators weighing which pipeline gate to trust for interaction/data-contract regressions.

## iter-20 — 2026-07-08T09:30:00Z

**Verdict:** CONTINUE
**Lesson:** On a Frontend-Present visual-only iteration, the canonical browser-qa lane can record a blanket SKIP (both services down at precondition, `curl 000`) while the QA report still self-reports PASS by grading browser-typed cases (TC-03..12/TC-16) from *code inspection* and asserting "frontend is running" — a false-completion pattern. Two root causes compounded: (a) `scripts/start-frontend.sh`'s `.next/.qa-serve-base` staleness stamp checks only the baked backend URL, never frontend-source freshness, so it silently served a STALE pre-iter-20 bundle (caught only because the ux-regression reviewer forced `rm -rf .next` and drove the live DOM); (b) both services happened to be fully down when browser-qa checked. The closure + audit + ux-regression triad caught it (CLOSURE-FAIL / T3-T5 / WARN) while status.json + qa.md read "complete/ready". Do NOT flip a target journey to `passing` on code-verification + a non-canonical live DOM check when the evidence dir is empty and closure FAILED — mark it `partial` and require a clean canonical browser-qa re-run.
**Applies to:** any Frontend-Present iteration whose content is visual/UX; any iter where `reports/phase-*-ui-test-results.md` is a blanket SKIP or the evidence dir is empty; always pre-empt with `rm -rf apps/frontend/.next` + confirm both prod services reachable BEFORE dispatching browser-qa; never accept a QA/status "ready to ship" over an empty evidence dir or a CLOSURE-FAIL.

## iter-21 — 2026-07-08T12:40:00Z

**Verdict:** CONTINUE
**Lesson:** A required-still-passing replay journey can literally FAIL a P1 UT case without being
a regression — verify against the journey's OWN canonical golden script, not the test-plan wording.
Iter-21's UT-21 (J-12) FAILED because it looks for a universe count on `/methodology`, but
`runs/goal-session-mcp-loop/journey-scripts/J-12.json` has ZERO `/methodology` references (it targets
`/data` x3 + `/stocks` x1), and the `/methodology` Universe Selection section is correctly suppressed
by the pre-existing J-22 anti-fabrication gate (`apps/backend/app/api/methodology.py:35-36` pops
`universe_selection` when `apps/backend/data/seed/universe.json` is absent — it is). The substantive
claim held live (`/data` 541 == `/stocks` 541/541). Before calling any P1 UT failure a regression:
(1) grep the journey's golden script for the failing page/assertion; (2) find the source-level cause
and check `git diff` shows the implicated files were untouched this iter; (3) confirm the substantive
capability elsewhere. A stale test reference is a test-plan defect (retarget it), not a `passing->failing`.
Second takeaway (positive): the browser-qa-agent correctly overrode a stale dispatch `SKIP` flag by
independently re-verifying reachability (both services 200) — this is the fix for the iter-0/2/4/13/20
blanket-SKIP failure mode; an empty evidence dir over a real live stack is the anti-pattern, not this.
**Applies to:** any iter whose DoD includes required-still-passing replays or carries forward a UT
test-plan verbatim; any journey whose surface depends on an environment/seed-data precondition
(`universe.json`, committed screen records) that gates content behind an honesty check; and any
browser-qa dispatch where the precondition probe may race service startup.

## iter-22 — 2026-07-08T18:20:00Z

**Verdict:** CONTINUE
**Lesson:** An in-pipeline audit-FAIL -> dev-fix cycle re-runs review/QA/audit but does NOT
automatically re-invoke the canonical `browser-qa-agent` or the `ux-regression-reviewer`.
When the fix touches the actual rendered UI (here: `minBarSpacing: 0.02` on
`phase-cross-view-chart.tsx` to surface the deep 1996 chart window — the exact defect
UT-03/ux-regression measured), both of those gates' reports-of-record stay frozen at their
pre-fix FAIL, and phase-closure correctly FAILs on the stale contradiction (`ui-test-results.md`
= FAIL, `ux-regression.md` = UX-REGRESSION-FAIL) even though review/QA/audit all re-PASS and the
fix is genuinely correct (verified here by QA TC-01 + auditor pixel pre/post compare + my own read
of TC-01-chart-area.png showing lines rebased to ~0% at the 1996 far-left). The QA agent's own
TC-* retest is NOT a substitute for the DoD-named `browser-qa-agent` lane. Result: the target
journey advances to `partial`, not `passing`, and the next iter is a verification-only re-run —
the recurring iter-13/iter-20 tax. Corollary for the DEVELOPER doing an audit-fail fix pass on a
rendered surface: request a fresh canonical browser-qa + ux-regression re-run as part of the same
fix pass, not just review/QA/audit, or closure will bounce it.
**Applies to:** any iter where an audit/review FAIL is remediated by a dev fix pass that changes a
user-visible rendered surface (chart config, layout, a component's visible output) — the fix pass
must regenerate the `browser-qa-agent` `ui-test-results.md` and the `ux-regression.md` against the
fixed build before closure can pass; a `qa.md` TC-* retest does not satisfy the "pass via
browser-qa-agent" DoD.

## iter-23 — 2026-07-09T01:00:00Z

**Verdict:** CONTINUE
**Lesson:** A DoD line that pins a specific SLOW test as a green gate (`test_api_indexes.py` at "backend pytest green") is a trap when that test has never actually run to completion — on its first-ever run (the ~2h 30y/590-symbol fixture) it surfaced a latent test-only defect (KeyError:'^TNX', a full/clamped symbol-symmetry assertion that is invalid for a symbol honestly omitted before its first bar in clamped mode). Worse, the same spec put `apps/backend/` OUT OF SCOPE, so fixing the pinned test to meet the DoD contradicted the scope fence; the auditor resolved it pragmatically as a test-only fix + in-process KeyError reproduction (the literal "12 passed" full re-run was reasonably deferred as the fixture fork-locks the box). It did not gate J-14 (its own two direct assertions were in the passing 11, and the default browser path is unaffected).
**Applies to:** any spec author / decomposer writing a verification-only or backend-frozen iteration — do NOT cite a slow, rarely/never-completed test as a hard DoD gate unless it has been confirmed green at least once; if a pinned test can only pass by touching frozen source, the DoD and the scope fence contradict — resolve it in the spec, not mid-audit. Also: full-vs-clamped (or full-history-vs-as-of) API symmetry assertions must tolerate honest pre-first-bar omission.

## iter-24 — 2026-07-09T18:40:00Z

**Verdict:** REGRESSION
**Lesson:** A SQLite performance pragma can OOM the process without touching the Python heap: `mmap_size_bytes: 1073741824` (1 GB) reserves that much *virtual address space PER connection*, so with `pool_size=10 + max_overflow=20` just ~6 live pooled connections blew past the `server.memory_cap_mb=6144` `ulimit -v` (RLIMIT_AS) cap and crashed the first cold `GET /api/data` load after every restart (MemoryError in `cursor.fetchmany()` -> PyO3 panic; VmSize pinned exactly at 6144 MB while VmRSS was only ~2.9 GB — the fingerprint of *virtual*, not physical, exhaustion). The cap was sized (iter-19) only against the Python-heap bar prefill and never re-derived when item B added per-connection mmap reservations. Any change to SQLite `mmap_size` or pool sizing must satisfy the invariant `mmap_size_bytes × (pool_size + max_overflow) < ulimit -v` — and a browser-qa cold-path repro (stop backend -> load /data as the FIRST request, twice) is the only reliable catch; a `/api/health` boot is a DIFFERENT code path and gives a false "cold path OK". Second lesson (recurring, now iter-18 + iter-24): the QA agent graded the cold-path DoD line PASS from the dev handoff's claim while its own browser-qa lane read FAIL and reproduced the crash 2/2 — a critical anti-goal caught only because the ux-regression + closure gates read the browser-qa *content*, not the QA verdict line. And the auditor's own engine-level ablation fix is NOT journey evidence: a critical-anti-goal fix applied after the canonical lane ran must be re-verified by that lane before the violation counts as resolved.
**Applies to:** any iter touching `apps/backend/app/db.py` pragmas/pool sizing, `config.yaml` `database.*` or `server.memory_cap_mb`, or `app/engine/prices.py` prefill; and any iter where an audit-applied fix for a CRITICAL anti-goal lands after the browser-qa lane already ran (must dispatch a verification-only re-run, not accept engine/code-level proof).

## iter-25 — 2026-07-09T19:30:00Z

**Verdict:** CONTINUE
**Lesson:** The non-terminal QA lane has now produced weak/wrong evidence in THREE consecutive iterations that only the canonical browser-qa + ux-regression + closure lanes caught: iter-18 (graded "18/18 pass, zero blockers" over its own crash screenshot), iter-24 (graded cold-path TC-10 PASS from a later-invalidated dev claim while its own browser-qa read FAIL), and iter-25 (cited TC-02-storage-card.png which is byte-identical md5 3fe10a6b to the UT-06 "Backend unavailable" ERROR card — an error frame presented as proof of a working storage card — plus marked an over-budget /api/health 0.210s PASS). The recurring per-iteration flag has NOT fixed the lane; the pattern is now robust enough to act on structurally. What worked this iter: the auditor md5-scanned the whole evidence dir, caught the mis-cite, re-pointed it to the valid canonical frames (UT-04/UT-01), and left the bad file in place as a documented trail rather than overwriting it (deleting evidence would itself be tampering).
**Applies to:** any iteration's evaluation — keep weighting the canonical browser-qa CONTENT + ux-regression + closure over status.json/qa.md prose, and always md5-scan the evidence dir for reused/relabeled frames (a `-fail-`/error-card frame cited under a PASS invalidates that citation); and a future planner should consider a dedicated tidy iteration to harden or formally down-weight the QA lane rather than re-flagging it every recovery pass.

## iter-26 — 2026-07-10T14:30:00Z

**Verdict:** REGRESSION
**Lesson:** A perf iteration whose DoD asserts "no memory regression under the 6144 MB cap" measured only peak **RSS** on a 12-date subset — but the deep-basis full-universe (322-date x 541-member) "Rebuild snapshots" job crashes on **VSZ** exhaustion at the `ulimit -v` ceiling (RSS ~4.93 GB stayed under its cap while VSZ pinned at exactly 6144 MB). RSS-only probes on a subset shape structurally cannot catch a VSZ ceiling hit on the full shape. This is the SECOND VSZ/`ulimit -v` backend crash this session (iter-24 was mmap x pool). Any iteration touching `prices.py`/`_BarCache`/`data_manager.py` backfill/prefill or the regime `full[:cut]` path MUST measure the full-universe long-job under the real `ulimit -v`, sampling BOTH VSZ and RSS, or its "no memory regression" claim is unsubstantiated at the shape that matters.
**Applies to:** any iter touching the bar cache / prefill / backfill / regime scoring paths, or asserting a memory/perf budget on the deep 30-year basis.

## iter-26b — 2026-07-10T14:30:00Z

**Verdict:** REGRESSION
**Lesson:** When a target journey's pre-registered path is a no-op on the seed (the J-16 Backfill pre-fill range 2005-02-28->03-07 was a genuine 0/0 no-op), the QA fallback ("Rebuild snapshots for current universe") is a MUCH heavier full-universe job that can surface latent memory bombs the narrow path never would. A verified crash on the fallback path still counts as a journey failure AND a critical anti-goal #8 violation — the causation may be pre-existing, but the verdict (halt for human review) does not depend on causation. Decompose J-16-style perf/backfill iterations with a real, non-empty deep-history cadence date/subset so the target path itself (not just a fallback) exercises the crashing shape.
**Applies to:** any perf/backfill/warmup iteration where the journey's own job path may be a seed no-op; any iter whose fallback test path is heavier than the pre-registered one.

## iter-27 — 2026-07-12T10:30:00Z

**Verdict:** CONTINUE
**Lesson:** The deterministic `scan-report.md` runs over the FULL iteration diff, which now includes the vendored `incredible_auto_dev/` framework subtree pulled in via squash-merge. That subtree ships judgment-eval test fixtures whose whole PURPOSE is to contain planted fake credentials (`tests/judgment/{auditor,reviewer,goal-evaluator}/case-*` — e.g. `case-05-secret-committed`, `case-04-paid-service-live-key`, using the AWS-doc example key `AKIAIOSFODNN7EXAMPLE` + fictional `lv_live_`/`qs_live_` keys). These reliably light up as CRITICAL `secret-assignment`/`aws-access-key` findings but are NOT product anti-goal-#7 violations — they are disjoint framework tooling, not Trendora source, and not authored by the iteration's dev work. Always split the scan-report by path prefix: only findings under the product namespace (`apps/`, `config.yaml`, `data/`, `scripts/` product paths) can constitute a product secret; findings under `incredible_auto_dev/` are framework-fixture false positives (reviewer + auditor + coherence all treat that subtree as out-of-scope).
**Applies to:** any iter whose commit range includes a framework-subtree pull / squash-merge, or any evaluator reading a CRITICAL scan-report — check the finding PATHS before treating a secret hit as an anti-goal violation.

## iter-27b — 2026-07-12T10:30:00Z

**Verdict:** CONTINUE
**Lesson:** The actual resolving fix for the iter-26 full-universe VSZ crash was glibc allocator hygiene (`MALLOC_ARENA_MAX=2` exported before `exec uvicorn` + `gc.collect()`/`malloc_trim(0)` in the backfill `finally`), NOT the read-side windowing alone — the isolated harness (~3.4 GB peak) structurally could not reproduce the live 6 GB ceiling hit, so windowing byte-identity tests passed but could not PROVE the crash resolved. The proof had to come from the live canonical browser-qa lane driving 2+ consecutive full-universe rebuilds in one long-lived process (cross-run arena accumulation was the driver). When a memory fix's own harness admits it can't reproduce the failing shape, the fix is unproven until the live lane drives the exact crashing scenario.
**Applies to:** any iter touching `data_manager` backfill / `_BarCache` prefill / long-running job memory; do not accept an isolated-harness "under cap" as resolution of a live OOM — require the live full-shape repro.

## iter-28 — 2026-07-12T22:45:00Z

**Verdict:** STALLED
**Lesson:** The browser-qa lane graded the five all-FAIL evidence journeys (J-02/J-06/J-07/J-08/J-09) as "PASS" by scoring only the honest-status half ("Not yet proven" badge is correct + numbers byte-match the FAIL verdict) — but each journey's acceptance requires a *Proven* certified edge to surface/drill, which the all-FAIL ledger cannot provide. A journey whose title is "certified edge surfaced" is NOT passed by an honest "no edge here" state, however correct; that is anti-goal #1 upheld, not journey acceptance. When a journey's success criterion is the PRESENCE of a proven artifact, an honest-absence screenshot is `partial`, never `passing`.
**Applies to:** any future evaluator scoring J-02/J-06/J-07/J-08/J-09 (or any "surface a certified/proven X" journey) against an all-FAIL ledger — do not let a browser-qa PASS on the honest-status half flip the journey to passing; the achievement gate needs a real PASS certified-claim, which is human-unblock-gated here.

## iter-29 — 2026-07-13T06:48:16Z

**Verdict:** CONTINUE
**Lesson:** md5-collisions among deterministic `-verify.png` REPLAY frames are benign when the colliding journeys legitimately share an endpoint (J-04/05/06/07/08/09-verify all ended on the `/evidence` top viewport = one identical frame; J-13/14-verify both ended on `/data`). This is NOT the iter-11/13/25 reused-frame failure: the discriminator is (a) each TARGET journey's CITED evidence is a distinct fresh capture, and (b) opening ONE colliding frame shows a real, byte-correct page (J-05-verify.png was a genuine `/evidence` with leadership_score FAIL -0.03% matching the ledger), and (c) replay PASS is assertion-driven, not screenshot-driven. Don't panic at the dup-md5 scan, but do open one to confirm it isn't a shared ERROR page — and flag element-clip captures as the fix so each journey's frame is independently distinct.
**Applies to:** any evaluator reading merged browser-qa + deterministic-replay evidence dirs; especially lean verify-only iters where several journeys share `/evidence` or `/data` as their endpoint.

## iter-29b — 2026-07-13T06:48:16Z

**Verdict:** CONTINUE
**Lesson:** A STALLED plateau (iter-28: five evidence journeys with no promotable edge, all unblock paths human-owned) was correctly resolved NOT by more code but by an OWNER goal.md amendment (eb19cee) that re-scoped the journeys to outcome-neutral acceptance + pulled backlog cards as new journeys. The evaluator's job on the follow-up lean pass is to verify the EXISTING product now satisfies the NEW contract (against the current goal text / fresh spec_hash), not to re-litigate the old strict contract — and to remember the amendment can ADD Must-have journeys (J-17..J-25), so a clean flip of the old five does NOT mean GOAL_ACHIEVED. Always re-hash the journey set after a goal.md edit and add any newly-appeared Must-haves as `unknown`.
**Applies to:** any iteration immediately following a STALLED-with-menu verdict that the owner resolved via a goal.md re-scope/extension.

## iter-30 — 2026-07-13T12:58:19Z

**Verdict:** CONTINUE
**Lesson:** A DoD that asserts a DERIVED row count without computing it ("Backfill complete: ... ≥14 ledger-derived rows") creates a false-shortfall trap: the correct dedup here is 11 (14 raw ledger entries − 3 cross-ledger duplicate selector-sets, since `match_registration` must resolve one exact selector-set to ONE row), so an evaluator skimming "11 < 14" could wrongly read a complete backfill as incomplete. The binding completeness bar is the round-trip property ("every distinct claim across both ledgers matches exactly one backfilled row via the real matcher"), NOT a literal count — the dev/reviewer/auditor all re-derived 11 independently and were right to ship it over fabricating 3 phantom rows to hit the number.
**Applies to:** any future iter whose spec/DoD asserts a derived count (ledger rows, symbol counts, test counts) — verify the count against the data, and never treat a documented, test-proven "correct dedup below the estimate" as a shortfall; also any iter touching `app.engine.registry` / the pre-registration backfill.

## iter-31 — 2026-07-13T19:20:00Z

**Verdict:** CONTINUE
**Lesson:** The "audit-fix landed but the canonical browser-qa lane was never re-run against it" verification gap recurred a 4th time (iter-13/20/22/31), and this time the QA lane actively fail-opened around it — it deferred ALL browser tests, graded PASS purely from the 22 backend unit tests, and wrote "ready to ship" while the browser-qa-agent's own artifact read FAIL on UT-07. The saving grace was closure independently re-reading the fix in the working tree (CLOSURE-PASS with a transparent Non-Blocking Note), but the pattern is durable: a green QA verdict here can rest on unit tests alone, so the evaluator must always cross-read the browser-qa `ui-test-results.md` verdict directly rather than trusting `qa.md`/`status.json` (status.json even carried `browser_checks_run: false` while 11 browser tests had in fact run). When the canonical lane's last recorded word on a target journey is FAIL and only the auditor re-checked the fix, score the journey `partial`, not `passing`.
**Applies to:** any iteration where browser-qa returns FAIL and a later stage (audit) applies + self-verifies a fix without the canonical browser-qa lane being re-run; and any iteration whose `qa.md` grades PASS while deferring the browser lane.
