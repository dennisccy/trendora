# goal-mcp-loop-iter-18 Execution Plan (re-dispatch — closeout)

This is a **re-dispatch** of an iteration whose heavy engineering is already complete, reviewer-confirmed,
and disk-verified: the atomic 30-year/548-pool basis swap, the staleness gate (J-12), the sanctioned
ledger reset (J-11, 7 canonical + 7 staging rows, all honest FAIL, register_date 2026-07-03), bars
windowing (J-10), and the frontend chart-range-control + staleness UI. The prior review verdict was
**FAIL** on exactly ONE blocking item (DoD "H" — run the full backend suite to real counts) — **that item
is now MET**: both chained fix-verification ledgers, which were still running when the last dev/review
pass happened, have SINCE completed GREEN:
- `reports/qa/goal-mcp-loop-iter-18-fixverify.log` → `SUMMARY[fixverify] rc=0` — 9 passed in 8237.06s (2:17:17), ended 2026-07-06T16:18:45Z
- `reports/qa/goal-mcp-loop-iter-18-dispatch10-verify.log` → `SUMMARY[dispatch10] rc=0` — 14 passed in 19036.67s (5:17:16), ended 2026-07-06T21:36:32Z

No pytest process is currently running. `docs/handoffs/goal-mcp-loop-iter-18-dev.md` and
`runs/goal-mcp-loop-iter-18/status.json` still show the OLD "pending" state (written before these two logs
finished) — **this dispatch's job is to close that gap out**, not to redo any engineering. Do not relaunch
the DB rebuild, backfill, or `regenerate_ledgers.py` (spec Hard Rules 1–2) — none of that is in scope again.

## What to Build

**Already complete — reviewer-confirmed correct, do NOT redo (see `docs/handoffs/goal-mcp-loop-iter-18-dev.md`
"Files Changed" for the full landed diff):** atomic seed swap (590 CSVs → `data/seed/prices/`, `meta.json`
regenerated), pool-broadened `load_prices` (587 symbols / 3.27M bars), the `resolve_candidate` staleness
gate (`stale_series`, `max_staleness_days`), the bounded snapshot backfill (410 runs, disclosed cadence),
both ledgers regenerated via `verify_edge` (all-FAIL, honest-stop honored), `walk_forward.history_years: 30`,
`/bars` windowing/downsample/`range` param, and the frontend Stock Detail chart-range toggle + `/data`
staleness cards. The prior review independently re-verified all of this plus the frontend suite (8/8) and
`tsc --noEmit` green.

**Remaining this dispatch:**

- **1. Developer — transcribe + close out (documentation only, no source changes expected):**
  - Transcribe both green `SUMMARY[fixverify]` / `SUMMARY[dispatch10]` results verbatim into the
    `docs/handoffs/goal-mcp-loop-iter-18-dev.md` "Dispatch-10 fix-verification results" subsection
    (currently a "Pending" placeholder at the end of the file) — replace the placeholder, do not
    append a redundant new dispatch section.
  - Update the handoff's "Known Issues" item 1 (still reads "Full backend suite — NOT yet complete") to
    reflect the real completed state: GRAND TOTAL passed=1364/failed=10/error=11/skipped=4 (collected 1381)
    at the raw sweep, with BOTH triage buckets (6 loaded_engine + 9 nonfixture) now fixed and each
    independently re-verified green (9 passed / 14 passed above) — zero net failures remain, DO-NOT-EDIT
    trio (`test_referee.py`, `test_online_fdr.py`, `test_forward_walk.py`) untouched throughout.
  - Update `runs/goal-mcp-loop-iter-18/status.json`: `current_step` → `dev_complete`, `tests_run: true`,
    clear the two now-resolved `blockers` entries.
  - Refresh `reports/phase-goal-mcp-loop-iter-18-implementation-summary.md` with a short closeout note
    (full suite complete, both fix-verify ledgers green, ready for review/QA).
  - **If (and only if) transcription surfaces anything other than rc=0/all-passed in either log**,
    triage narrowly per the spec's DO-NOT-EDIT rule and report — do not paper over a red result.
  - Do not touch application/engine code, config.yaml, the seed data, or either ledger — none of that
    is open work.
- **2. Reviewer — re-verify the fix batches, not the whole diff from scratch:** confirm the two log
  files above are genuinely green on disk (not a transcription claim), spot-check that dispatch-9's
  6 loaded_engine fixes (`test_market_phase.py`, `test_scoring.py`, `test_api_research.py` ×3,
  `test_data_manager_concurrency_load.py`) and dispatch-10's 2 fixes (`test_warmup.py` timeout
  600→3000s, `test_iter27_rebuild_mdd.py` coverage bound) are faithful re-targets (not masked/weakened
  assertions), and confirm the DO-NOT-EDIT trio is still byte-unmodified. The rest of the diff was
  already reviewer-approved last pass — do not re-litigate it absent a specific reason.
- **3. QA — run the canonical browser-qa lane for the FIRST time this iteration** (`browser_checks_run`
  is still `false`; no evidence directory exists yet). This is the single largest remaining piece of
  work in the whole iteration. See Key Test Scenarios below — drawn directly from the phase spec's
  TESTING REQUIREMENTS.
- **4. Auditor — final skeptical PASS / PASS_WITH_GAPS / FAIL** against the full Definition of Done,
  including the pre-registered honest-all-FAIL interpretation for J-06..J-09/J-02 (data-basis provision,
  not a regression — see spec NOTES).

## Agents Required

- developer: yes -- transcription/status closeout only (item 1 above); no new engineering, no rebuilds.
- backend work: yes -- verification/documentation of already-implemented backend changes; zero new backend code expected.
- frontend work: no -- the chart-range control + staleness UI already shipped and were reviewer-confirmed; no new frontend code this dispatch. (Browser *verification* of that UI is required — see QA below — but that is a QA activity, not new frontend implementation.)

Frontend Present: yes

## Files to Create/Modify

- `docs/handoffs/goal-mcp-loop-iter-18-dev.md` -- transcribe both green fix-verify SUMMARYs; resolve the stale "full suite NOT yet complete" Known Issue bullet
- `runs/goal-mcp-loop-iter-18/status.json` -- `current_step: dev_complete`, `tests_run: true`, clear resolved blockers
- `reports/phase-goal-mcp-loop-iter-18-implementation-summary.md` -- closeout note
- `reports/reviews/goal-mcp-loop-iter-18-review.md` -- new reviewer pass (supersedes the prior FAIL)
- `reports/qa/goal-mcp-loop-iter-18-qa.md` + a screenshot evidence directory (e.g. `reports/qa/goal-mcp-loop-iter-18-evidence/`) -- first browser-qa run this iteration
- No other source files are expected to change. The full already-landed diff (backend engine/config/tests + frontend) is enumerated in the dev handoff's existing "Files Changed" section and was already reviewer-approved; do not re-touch it absent a genuine defect found during re-verification.

## UI Evolution (Frontend Present: yes)

- New user-facing capability: a Stock Detail chart range toggle ("Recent" ↔ "Full history") that reaches back to each symbol's real first bar (AAPL/MSFT to 1996-01-02, NVDA to its 1999-01-22 IPO), with post-IPO names (ARM/COIN/HOOD) honestly showing only their short real history; `/data` gains a fourth staleness diagnostic.
- New information displayed: honest depth caption ("N bars · as of DATE · history since FIRST_AVAILABLE_DATE" + weekly-downsampling disclosure beyond ~8y); the `stale_series` exclusion reason + `max_staleness_days` threshold on `/data` and the membership timeline; regenerated `/evidence` content (7 rows, all honest FAIL, register date 2026-07-03 — zero "Proven" chips anywhere product-wide); broadened membership counts on `/stocks`.
- New user actions: click the Recent/Full-history segmented toggle on `/stocks/{ticker}`.
- UI surface changes: `/stocks/{ticker}` chart header (toggle + caption); `/data` diagnostics (new reason card, 5-column grid) + membership timeline table (new "stale" column); `/evidence` content regenerated (structure unchanged); `/backtest` as-of window deepens (same page, honestly floored at 2005-02-25). No new pages.
- Navigation changes: none.

## Visual Requirements (Frontend Present: yes)

- Component patterns: the range toggle reuses the existing segmented-control idiom already used for the Regime toggle on the same page (hover/focus-visible/active states, `aria-pressed`, persisted via the same `usePersistedToggle` pattern); evidence rows/badges reuse the existing `evidence-status-badge` / `ClaimRow` components untouched in structure — only their content is regenerated.
- Layout: no layout changes — the toggle sits inline with the existing chart header/toolbar; the `/data` reason-card grid widens from 4 to 5 columns to fit the new card.
- Key visual effects: consistent with Trendora's existing minimal, data-dense, evidence-first style; a FAIL/"Not yet proven" state must read calm and honest, never alarming or hyped.
- States to handle: loading skeleton on every range switch (state resets, no stale chart shown mid-fetch); honest short-history state for post-IPO names; honest FAIL/"Not yet proven" state on every score/edge surface (this run, that is ALL of them); 404 only for genuinely unknown tickers, never a fabricated row.

## Key Test Scenarios

Drawn from the phase spec's TESTING REQUIREMENTS — this is the browser-qa lane's primary checklist since it has not run at all yet this iteration:

- **J-10 (deep history, `/stocks/AAPL` or `/MSFT`):** default chart bounded (~5y trailing) with caption disclosing first available date **1996-01-02**; "Full history" opt-in renders the deep span (weekly-downsampled beyond the threshold, real bars only, never synthesized); **NVDA first bar 1999-01-22**; one post-IPO name (**ARM 2023-09-14 / COIN 2021-04-14 / HOOD 2021-07-29**) honestly short; `/stocks` + `/evidence` stay responsive; `/backtest` window honestly floors at **2005-02-25** (SPY's real first committed bar — a disclosed floor, not a defect).
- **J-11 (`/evidence`):** exactly 7 rows, every register date **2026-07-03**, every verdict an honest **FAIL** with its real p/edge (spot-check ≥1 row byte-for-byte against `runs/goal-session-mcp-loop/state/certified-claims.jsonl`); factor-lab/combination-lab/stock-detail surfaces all read "Not yet proven"; **ZERO "Proven" text and ZERO retired values** (old +21.34% / +8.91% / +6.36% / +6.12% / +4.69% / +3.33% / p=0.0004998 / register dates 2026-06-30 or 07-01) anywhere in the app.
- **J-12 (`/methodology`, `/data`):** membership timeline shows entries/exits across the deep history; a mid-history-IPO name is absent before `min_history_bars` and present after; the `stale_series` exclusion reason + threshold are surfaced.
- **J-01/J-03/J-04/J-05 regression (FRESH pixels — byte-identity carry is NOT available this iteration):** `/stocks` — every row's three scores each carry a visible status (all "Not yet proven" IS a passing state for J-01); J-03 — honest marking product-wide including FAIL rows on `/evidence`; J-04 — the Breakout-watch row still carries its "Regime: Risk-on" label with an honest FAIL verdict; J-05 — all 7 rows render hypothesis/verdict/control/date/linkbacks end-to-end. J-02 — verify the drill affordance renders its honest not-proven state (the actual drill is structurally un-exercisable this iteration — a partial/not-a-regression per spec NOTES, not a fail).
- **Broadened-pool honesty check:** open a leaderboard/detail page for a name outside the legacy ~122-symbol set; confirm it renders honestly (no crash, no fabricated metadata).
- **Anti-goal sweep:** zero buy/sell/price-target/return-promise language anywhere; zero credentials in source.
- **Screenshot hygiene (iter-3/11/13/14/15 lessons — treat violations as a verification gap, not evidence):** full-page or element-clip captures, md5-distinct, with the asserted element actually composed in frame.
- **Backend (should already be green — confirm, don't re-run the full multi-hour sweep):** the two fix-verify logs above are the authoritative real counts; DO-NOT-EDIT trio (`test_referee.py`, `test_online_fdr.py`, `test_forward_walk.py`) untouched; frontend suite (8/8) + `tsc --noEmit` green (already independently confirmed by the prior review pass).

## Assumptions and Flags

- No scope creep: this dispatch is pure closeout of an already-approved plan. J-13 (`/data` 548-pool Fetch default, Expand removal) and J-14 surfacing (deep index/macro overlays) remain explicitly OUT OF SCOPE per goal.md sequencing — do not drift into them.
- Diff base for reviewer/auditor (iter-17 lesson, recurring): diff against current `HEAD` + untracked files, NOT the recorded `runs/goal-session-mcp-loop/iter-18/snapshot-sha` (that snapshot is a mid-flight WIP capture that already contains most of this work and will hide the iteration if used as the base).
- No pre-build Evidence-Claim gate applies: the spec deliberately carries no `## Evidence Claim` block — the in-iteration replay through `verify_edge` on the rebuilt DB IS the referee certification (goal.md's sanctioned-reset mechanism).
- Any post-browser-qa fix (should none be needed) requires a browser-qa RE-RUN before closeout (iter-13 lesson) — do not let a late fix ride on stale screenshots.
- The all-FAIL evidence ledger is the CORRECT, honest outcome of this iteration, not a defect — do not let any agent try to "improve" the verdicts; the honest-stop guard forbids forcing a PASS.
