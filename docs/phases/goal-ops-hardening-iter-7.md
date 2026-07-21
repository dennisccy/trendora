# Goal Iteration 7 — Close out J-06: warm `/evidence`'s drawdown-expectations at ingest, reconfirm all 11 page budgets

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 7
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-06
- **Required-still-passing journeys:** J-01, J-03, J-04, J-05
- **Anti-goal reminders:**
  - **AG-1:** A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked values MUST render a "not yet proven" state. *(critical)*
  - **AG-2 — Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha claims; never place or simulate orders. *(critical)*
  - **AG-3:** A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation for the same as-of date — not merely that the page renders. *(critical)*
  - **AG-4 — No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **AG-5 — Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of; never introduce lookahead anywhere. *(critical)*
  - **AG-6:** No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the post-decompose gate. *(critical)*
  - **AG-7:** No hard-coded credentials, API keys, or tokens in source files. *(critical)*
  - **AG-8 — Resilience to data-shape and data-scale change:** widening the data basis (new nulls, broader pools, deeper history) must never crash an existing page or exhaust a service's memory — every existing consumer of a widened field is re-validated, the UI degrades gracefully (contained error boundary, honest "—"/NA placeholder, never a blank application-error page), and unbounded whole-table ORM loads are forbidden on the deep basis. *(critical)*
  - **AG-9 — Offline-deterministic ingest:** ingest jobs (fetch/backfill/rebuild) run only against the committed seed / local provider fixtures — no live external network calls or paid data services may be introduced without an explicit goal.md amendment. *(critical)*

## GOAL

`/evidence` loads within its committed budget on the FIRST view after an ingest (not only when warm),
closing J-06's last residual gap so every one of the session's 11 named pages is within budget under a
real browser — making J-06 the session's final passing Must-have journey.

## BACKGROUND

Iter-6 fixed J-06's Dashboard/Data-Manager real-browser latency violation and moved J-04/J-05 out of
`unknown`, but scored J-06 `partial`: audit B1 found `/evidence`'s one-time cold-recompute is ~73s on the
accumulated live dev DB (vs 9.5s on the committed seed) because the ingest finalize hook
(`_refresh_ingest_aggregates`, `app.engine.data_manager`) warms the `event_study_cache` research default
hot key but never the per-claim `drawdown_expectations` view slot the SAME table reserves for the
`/evidence` page's expectations panel — so the first `/evidence` view after any ingest still pays a lazy
cold miss. `reports/perf-budgets.md`'s own iter-6 CORRECTION section names the exact fix: "Extending the
finalize hook to warm those keys too (mirroring the existing event-study warm) would make the cold miss
never user-visible." Per the priority rubric this targets J-06 alone (rule 3/4 — the only
failing-or-partial journey left, and the smallest concrete change: one function, one existing warm
pattern) with J-01/J-03/J-04/J-05 carried as Required-still-passing (rule 5 — one change, not two risky
ones). **Depth is full**, citing trigger 1 (structural/cross-cutting): J-06's own acceptance requires a
real-browser re-measurement across all 11 named pages plus a written `reports/perf-budgets.md` update —
verifying the interaction between the ingest warm change, the `/evidence` consumption path
(`app.engine.evidence.build_evidence_payload` → `compute_drawdown_expectations_cached`), and the
committed-budgets artifact is something only a real-browser QA pass can confirm, not unit tests alone;
this is also the session's last failing/partial journey, where an accurate closure narrative
(ui-impact-analyst + phase-closure-auditor, only produced at full depth) matters most after two prior
iterations' documented closure-narrative drift.

**Lessons applied** (per `lessons.md`): (iter-3/iter-1) a new/extended warm trigger's honesty risk lives
in its NOT-YET-COMPUTED and mass-failure edges — gate `"drawdown_expectations"`'s appearance in
`aggregates_refreshed` on "actually warmed at least one key," never fabricate it on an empty ledger or a
fully-unresolvable cohort set (mirrors the existing `calendar_days`/`research_hot_keys` gating
convention). (iter-2) any count-changing ingest that should refresh a cache must actually do so — verify
the warm loop runs for `backfill`/`both`/`rebuild` (the same kinds the sibling `research_hot_keys` warm
already covers), not just the kind that happens to be exercised in dev. (iter-5) curl under-reports real
page latency — the `/evidence` first-view re-measurement for this iteration's DoD MUST be real-browser
(or, if the harness cannot easily automate a real cold-cache browser load, a same-process cold `curl`
taken immediately after an ingest with the finalize warm having just run — document which method was
used and why). (iter-6) always cross-check the merged QA verdict against the RAW
`ui-test-results.llm.md` browser-qa verdict, and never let a page's "warm" reading stand in for its FIRST
view after a state-changing action.

**Scope-selection deviation note:** none — this is a direct continuation of iter-6's own named next-step
item 1 (audit B1), the only remaining product gap on the only remaining non-passing journey.

## IN SCOPE

### Backend
- [ ] Extend `_refresh_ingest_aggregates` (`app.engine.data_manager`) with one more non-fatal warm step,
      after the existing `research_hot_keys` block: resolve the evidence ledger
      (`app.engine.evidence.resolve_ledger_path` + `read_entries`, excluding `forward_walk`-type entries
      — the SAME filter `build_evidence_payload` already applies), and for each claim call the EXISTING
      `app.engine.forward_testing.compute_drawdown_expectations_cached(session, claim, cfg)` — the SAME
      function `GET /api/evidence` already calls lazily. Append `"drawdown_expectations"` to the
      function's returned `refreshed` list only if at least one key was actually warmed (mirror the
      existing gating convention; an empty ledger or an all-unresolvable cohort set must NOT report this
      category as refreshed).
- [ ] Add a `prog.tick()` heartbeat stamp before each claim's warm call (mirroring every other per-item
      loop already in this function), wrapped in its own non-fatal try/except (log + continue to the next
      claim) so one unresolvable claim never blocks another or fails the ingest job.
- [ ] No new table, no new DB column, no new endpoint, no new module — this reuses the EXISTING
      `event_study_cache` table's reserved `drawdown_expectations` view slot and the EXISTING
      `compute_drawdown_expectations_cached` function verbatim.

### Frontend
None — no frontend file changes; `/evidence`'s rendered payload is byte-identical before and after (same
function, same values, only the warm TIMING moves earlier). `Frontend Present: yes` is set because the
fix's effect (a faster first view) is only confirmable live via browser-qa across all 11 J-06 pages (see
DEFINITION OF DONE / TESTING REQUIREMENTS) — not because any frontend file changes.

### New user-facing capability
None (no new feature). The user-visible effect is `/evidence` loading fast on the FIRST view after any
ingest, not only once someone else has already warmed it.

### New information displayed
None — `/evidence`'s claim rows and `expectations` panels are unchanged; only their compute timing moves.

### New user actions
None.

### UI surface changes
None — no page, panel, or card changes. Real-browser re-measurement only (see TESTING REQUIREMENTS).

### Product surface delta
`/evidence` moves from "fast only when already warm, ~73s on first view after an ingest on the grown
live basis" to "fast on every view, including the first one after an ingest" — closing J-06's last named
gap. No other page's behavior changes.

### Blueprint conformance
No new surfaces. `/evidence` is covered by the existing "Membership timeline / research hot-key caches"
Information Architecture / Data Contract row in `blueprint.md` (its "Served by" list now includes
`/evidence`, added this iteration as an additive edit — no nav-skeleton change, no reapproval needed).

### Data-contract additions
None new. This iteration extends the ALREADY-REGISTERED `aggregates_refreshed: list[str]` field's
enumerated value set with one more legal member, `"drawdown_expectations"` (blueprint.md updated) — same
field, same computing module (`_do_backfill`/`_refresh_ingest_aggregates`), same serving endpoints
(`GET /api/data`, `GET /api/data/jobs/{job_id}`). No second producer, no second endpoint, for this or any
other already-registered Data Contract value.

## OUT OF SCOPE

- Any change to `readiness.py`, `main.py`'s boot sequence, or `warmup.py` (unaffected this iteration;
  J-04's boot/readiness contract is settled — "Do not redo").
- Any change to `max_range_days`, `snapshot_cadence`, or the backfill range-cap logic (settled — "Do not
  redo").
- A second computing module, a second endpoint, or a second cache table for `drawdown_expectations`,
  `event_study_cache`, or any other already-registered Data Contract value.
- Loosening any committed budget number in `reports/perf-budgets.md` — only additive, honestly-measured
  rows.
- Retroactively editing iter-6's own point-in-time artifacts
  (`reports/phase-goal-ops-hardening-iter-6-user-visible-changes.md` /
  `-ui-surface-map.md`) — those stay as historical record; this iteration's OWN fresh
  ui-impact-analyst/closure artifacts (produced because depth=full) supersede them by describing the
  current, fixed state (see `assumptions.md`, iter-7 — goal-decomposer).
- Producing the `[NEW]`-flagged `demo.sh ops-hardening --session-live` walkthrough as developer/reviewer
  work — this is auto-produced by the session-mode `demo-narrator` step that runs after every dispatched
  iteration (per its own spec: session mode concatenates every `passing`/`already_passing` journey's
  steps and flags `new: true` when a journey's `last_passing_iter` is THIS iteration). Once J-06 flips to
  `passing` this iteration, that automatic pass supplies the walkthrough — no separate dev task (matches
  the iter-4/iter-5 precedent already logged in `assumptions.md`).
- Any expansion beyond `drawdown_expectations` warming — no other lazy cache (e.g., other
  `event_study_cache` non-default views, `market_phase_cache` beyond the latest key) is touched this
  iteration.

## DEFINITION OF DONE

- [ ] J-06 passes via browser-qa-agent: all 11 named pages (`/`, `/stocks`, `/stocks/AAPL`, `/sectors`,
      `/themes`, `/data`, `/evidence`, `/scanner-runs`, `/backtest`, `/watchlist`, one `/research` lab)
      load within their committed `reports/perf-budgets.md` budgets under a real browser, INCLUDING
      `/evidence`'s first view immediately after an ingest job completes.
- [ ] Required-still-passing journeys J-01, J-03, J-04, J-05 remain green (deterministic replay where a
      golden script exists; LLM fallback otherwise).
- [ ] No anti-goal violation introduced — in particular AG-3 (warmed values byte-identical to a live
      compute) and AG-8 (an unresolvable/empty-ledger cohort degrades to an honest omission, never a
      crash or fabricated panel).
- [ ] Unit tests pass; no regressions. `pytest apps/backend/tests/test_data_manager.py
      apps/backend/tests/test_forward_testing.py apps/backend/tests/test_api_backtest.py
      apps/backend/tests/test_mcp_window.py -v` runs to completion with 0 failures (closes iter-6's named
      open item 4).
- [ ] `reports/perf-budgets.md` gains one new dated section: the post-warm `/evidence` first-view
      measurement (method disclosed — real browser preferred, cold `curl` immediately post-ingest
      acceptable if browser automation of a true cold-cache first-load is impractical) plus a fresh
      reconfirmation of all 11 pages' existing budgets (no loosened numbers).
- [ ] `blueprint.md`'s Data Contract stays internally consistent with the shipped code (already updated
      this iteration by the decomposer; developer/reviewer confirm no drift).
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-7-dev.md`, and its "Known Issues"
      section does NOT restate iter-6's retracted "555.97s severe regression" framing — it describes the
      CURRENT, fixed first-view state.

## TESTING REQUIREMENTS

- Browser: J-06 (all 11 named pages, real browser, 3 reloads for any previously-marginal page;
  `/evidence` specifically measured on a FRESH first view right after an ingest, not only warm).
  Required-still-passing: J-01, J-03 (deterministic replay), J-04, J-05 (LLM acceptance).
- Unit/integration: `_refresh_ingest_aggregates`'s new warm step — exact-value coverage of the "actually
  warmed" gating, the non-fatal per-claim failure isolation, and byte-identity between the warmed value
  and a fresh `compute_drawdown_expectations` call.
- Error cases: empty ledger (zero claims), an unresolvable cohort (`compute_drawdown_expectations`
  returns `None` for one claim), and one claim's warm call raising an exception mid-loop.

Test-first contract:

- TC-1: given a backend that just completed a `backfill`/`both`/`rebuild` ingest job with a non-empty
  evidence ledger, when `_refresh_ingest_aggregates` runs, then its returned list includes
  `"drawdown_expectations"` and every ledger claim's `EventStudyCache` row for the `drawdown_expectations`
  view is present in the DB before the job is marked `completed`.
- TC-2: given the ingest-time warm has just run for a ledger with claims, when a user loads `/evidence`
  for the FIRST time afterward (fresh process or explicitly cleared in-process cache), then the page's
  main panel populates within its committed warm budget (≤3s page / Item I), not the prior ~73s cold-miss.
- TC-3: given the same ledger claims, when the ingest-warmed `GET /api/evidence` response is diffed
  against a freshly-computed (uncached) `compute_drawdown_expectations` call for the same claim, then the
  two `expectations` payloads are byte-identical field-for-field.
- TC-4: given a claim whose cohort is unresolvable (`compute_drawdown_expectations` returns `None`), when
  the ingest warm loop processes it, then the loop logs and continues to the next claim (no exception
  propagates), and that claim's row on `/evidence` renders with no `expectations` panel — never a crash,
  never a fabricated value.
- TC-5: given the evidence ledger is empty (zero claims) at ingest finalize time, when
  `_refresh_ingest_aggregates` runs, then it performs zero drawdown-expectations warm calls and does NOT
  append `"drawdown_expectations"` to the `refreshed` list (honest — matches the "actually computed"
  gating already used for every other member of that list).
- TC-6: given a warm backend in prod mode (`scripts/start-backend.sh` / `scripts/start-frontend.sh`),
  when each of the 11 J-06-named pages is loaded and timed in a real browser, then every page's
  time-to-interactive and on-load API latencies are within their `reports/perf-budgets.md` committed
  budgets, and the results (including the new `/evidence` first-view number) are recorded in that file.
- TC-7: given `pytest apps/backend/tests/test_data_manager.py apps/backend/tests/test_forward_testing.py
  apps/backend/tests/test_api_backtest.py apps/backend/tests/test_mcp_window.py -v`, when run to
  completion, then it reports 0 failures and 0 errors.
- TC-8: given J-01's and J-03's existing golden replay scripts, when replayed against this iteration's
  build, then both PASS end-to-end with no step failures attributable to this iteration's diff.

## NOTES

- Audit B1 (iter-6) is the direct source of this iteration's scope; its recommended fix (mirror the
  existing `data_manager.py:3138` event-study warm) is prescriptive enough that no further design
  ambiguity remains — implement it as named.
- The `[NEW]` `demo.sh ops-hardening --session-live` walkthrough item, deferred at iter-4/iter-5/iter-6,
  is expected to self-resolve this iteration via the automatic session-mode demo-narrator pass once J-06
  reaches `passing` (see OUT OF SCOPE). If the evaluator finds it still missing after this iteration, that
  is a framework/showcase-chain gap to flag to the human, not a product defect to re-plan here.
- If browser-qa cannot practically drive a true cold-cache FIRST-view measurement of `/evidence` (e.g. the
  harness reuses a long-lived backend process), a same-process `curl` taken immediately after triggering
  a real ingest job (so the warm step has just run) is an acceptable substitute — but the choice and its
  justification must be stated explicitly in `reports/perf-budgets.md`, not silently substituted (iter-5's
  curl-under-reports lesson applies to STEADY-STATE readings, not to confirming a one-time warm actually
  happened before first view).
- This is expected to be the session's final feature-closing iteration: if J-06 passes cleanly and closure
  is clean, the next evaluator pass should have no remaining blocker to GOAL_ACHIEVED other than the
  showcase/demo-narrator self-resolution above.
