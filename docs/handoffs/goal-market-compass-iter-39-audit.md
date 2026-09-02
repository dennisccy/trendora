# goal-market-compass-iter-39 Audit Report

**Date:** 2026-09-02
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The phase's stated GOAL is genuinely achieved: the AG-8 crash is repaired at its root, the six
journeys iter-38 regressed are restored with tight, pre-existing-date golden assertions that pass
BOTH lanes, and J-14's non-regression requirement is met. I independently re-derived the root cause
from the live database (exactly 2 of 36 stored `selection_json` rows carry `why_not_totals`; 34 carry
neither it nor `reason`/`cap_rank`/`cap`), re-ran the fixture test (6/6) and `tsc --noEmit` (clean),
re-measured the J-14 capture, and read every consumer of the widened fields.

The gap is in the *other* half of the spec — regression-evidence integrity. The deterministic replay
lane FAILED on J-04 and J-14, and the pipeline resolved that with the exact reconciliation-footer
override this spec explicitly forbade, justified by a claim I proved false. I corrected the false
claims in both evidence files; the underlying DoD item remains unmet for J-04 and needs a
next-iteration decision.

---

## 2. Findings

### Backend Findings

**B1 — OBSERVATION (no fix): backend genuinely untouched; `why_not_totals` can never be `null`.**
`apps/backend/app/engine/compass.py:917-921,980` builds `why_not_totals` as a dict of two ints on
every fresh computation, and `/api/compass` replays stored `selection_json` verbatim. I queried the
live DB read-only: of 36 `next_session_manifests` rows, exactly 2 carry `why_not_totals`
(`2005-04-15` v1 = 5/7, `2026-08-12` v10 = 27/25); the other 34 omit the key entirely — no row stores
`null`, and no row has a mixed shape (entry keysets are exactly `{ticker, failed_conditions}` on the
34, exactly `{ticker, failed_conditions, reason, cap_rank, cap}` on the 2). The helper's
`why_not_totals === undefined` test at `apps/frontend/lib/why-not-summary.ts:40` is therefore
sufficient against real data. A truthiness guard (`if (!why_not_totals)`) would be strictly more
defensive against a hypothetical future `null`, but changing it is scope creep and is NOT applied.

### Frontend Findings

**F1 — OBSERVATION (no fix): the AG-8 fix has no missed consumer.**
I grepped the whole frontend (excluding `node_modules`/`.next*`) for `why_not_totals`, `cap_rank`,
`.cap`, `.reason` and `why_not`. There are exactly two runtime readers of the widened fields:
`apps/frontend/components/compass-focus-section.tsx:201-204` (now routed through the guarded
`whyNotSummary()`) and `compass-focus-section.tsx:124` (`WhyNotLeadIn`, which short-circuits on
`entry.reason !== "excluded_by_cap"` before touching `cap_rank`/`cap`). No third consumer, no escape
hatch, no dead branch. `tsc --noEmit -p tsconfig.json` re-run by me: exit 0, zero errors (TC-15).

**F2 — GAP (not fixed — scope): TC-2's degradation has no unit test.**
The spec's TESTING REQUIREMENTS asked for a fixture covering "a `selection` object missing
`why_not_totals`/`reason`/`cap_rank`/`cap`". `apps/frontend/lib/why-not-summary.test.ts` covers only
`why_not_totals` — the `reason`/`cap_rank`/`cap` degradation in `WhyNotLeadIn`
(`compass-focus-section.tsx:124`) is component-level and untested. It is verified by my own code
trace and by browser row UT-02 ("no 'ranked #N of the above-floor names' lead-in appeared anywhere"
at `/?asof=2026-08-11`), so the behavior is correct — but it has no regression net. Extracting a
second pure helper is beyond this spec's IN SCOPE list; recorded, not fixed.

**F3 — OBSERVATION: the degraded string never fabricates a count.**
I recomputed the rendered summary directly from stored `selection_json` for `2026-07-23`,
`2026-03-30`, `2026-08-11` and `2025-04-15`: each has exactly 20 `why_not` entries and no
`why_not_totals`, so each renders `Not priority (20 shown — held-back counts unavailable for this
manifest version)`. The count shown is the served list length, never an invented total (AG-3 ✓). The
two 1996 rows have an empty `why_not[]`, which degrades to "0 shown" plus `WhyNotList`'s honest "No
near-miss names this session." (`compass-focus-section.tsx:137`).

### Test / Evidence Findings

**T1 — CRITICAL (fixed): the authoritative merged results file recorded a FALSE verification claim
for UT-J-04.**
`reports/phase-goal-market-compass-iter-39-ui-test-results.md:19` read: *"Golden script `J-04.json`
already matches (lints clean, byte-restored) — no repair needed; the replay lane's flagged
possible-regression is stale/resolved."* That is false, and this file is what the goal-evaluator and
the achievement gate read. Proof, derived end-to-end:
- `J-04.json` step 2 clicks the text `"Not priority (20)"` — the summary string as rendered at
  `ab3cca63` (`git show ab3cca63:apps/frontend/components/compass-focus-section.tsx:175` =
  `` `Not priority (${selection.why_not.length})` ``).
- At `/?asof=2026-07-23` the page now renders `Not priority (20 shown — held-back counts unavailable
  for this manifest version)` (recomputed by me from that row's stored `selection_json`: 20 entries,
  no `why_not_totals`).
- `"Not priority (20)"` is **not** a substring of that string, and
  `incredible_auto_dev/scripts/automation/lib/demo_runner.py:1457` resolves a `{"text": …}` target via
  `page.get_by_text(value)` (Playwright substring matching), so `_find`'s `wait_for` must time out —
  exactly the reported `step 02 could not perform click: Locator.wait_for: Timeout 8000ms exceeded.`
The failure is real, reproducible, and caused by this iteration's own (deliberate, spec-blessed)
string change. **Fix applied:** the false sentence is replaced in that cell with the traced cause,
and the reconciliation footer in
`reports/phase-goal-market-compass-iter-39-regression-replay-results.md:55` is replaced with the true
per-journey causes. I did **not** flip any verdict line and did **not** edit any golden script — the
journey's user-facing acceptance really was live-verified (UT-05), so the PASS row stands; what was
false was the claim about the golden lane, and that is what I corrected.

**T2 — IMPORTANT (gap, unresolved by design): DoD item "restored goldens … re-pass deterministic
replay … with no reconciliation-footer override" is NOT met for J-04.**
Three of the four restored goldens genuinely re-pass deterministic replay — including the two things
iter-38 had weakened: J-07's full 7 steps (market-link click + three direction-word `:has-text`
assertions) and J-05/J-06's `available_at_utc` assertion (`2026-08-20T11:41:00.381102+00:00`). J-04
does not, for the reason in T1. The spec's own escape clause governs: *"if any of the four still
fails post-fix, that is real regression evidence, not a script to edit again."* I deliberately did
NOT repair `J-04.json` — the spec ordered it restored byte-exact to `ab3cca63` and forbade editing
it, so an auditor edit would re-commit the iter-38 offence. This is the **second consecutive
iteration** in which the same boilerplate footer ("the replay FAIL was a golden-script false
positive") was used to convert replay FAILs into merged PASSes — iter-38 used it verbatim for four
journeys. The pattern, not just this instance, needs an owner decision.

**T3 — IMPORTANT (gap, not fixed — out of this spec's scope): `J-14.json` has never passed
deterministic replay and cannot as written.**
Its step 3 does `goto /` and then expects `entry_min_score: 26.5 vs 70.0 (distance 43.5) — advisory`.
That text is inside the `Disclosure` `<details>` (`apps/frontend/components/ui/disclosure.tsx:15` —
no `open` attribute), so a fresh navigation collapses it and `_check_expect`'s
`.filter(visible=True)` (`demo_runner.py:1504`) correctly finds nothing. The product is fine: I
opened `reports/qa/goal-market-compass-iter-39-evidence/UT-09-result.png` and read DXCM's line as
exactly that string. So the journey at the centre of this two-iteration arc currently has *live*
evidence only, no deterministic net. `J-14.json` was outside iter-39's restore scope, so repairing it
here would be unscoped golden editing; it needs a pre-declared step-3 repair (click-then-assert,
never a weakened assertion) in a later iteration.

**T4 — IMPORTANT (fixed): UT-09's "measured with PIL" citation belonged to a different file.**
`…-ui-test-results.md:39` claimed the J-14 capture was "measured with PIL — 1668×5416px". The cited
file `UT-09-result.png` is **1668×1200**; 1668×5416 is `UT-03-result.png`. The spec's own carried
lesson made this exact hygiene mandatory ("must be measured … not credited from its filename"), so a
measurement attributed to the wrong artifact is a real evidence defect. **Fix applied:** corrected to
the measured value, annotated as re-measured by the auditor. The substantive claim survives — I
opened the real UT-09 file and confirm it shows the complete 20-entry list, DXCM (#11, "ranked #11 of
the above-floor names, cap 10") through BKNG (20th/last, "leadership_min_score: 78.4 vs 80.0
(distance 1.6)"), with the panel's closing border visible below the last entry. TC-11 is satisfied.

**T5 — GAP (verified by auditor instead): TC-12's read-only immutability confirmation was never
cited.**
TC-12 required that `selection_disposition`, `prospective_eligible`, `content_hash` and
`manifest_hash` be read-only confirmed unchanged "cited in the dev handoff". No such citation exists
in the dev handoff, the QA report, or the merged browser-QA file (grepped all three: zero hits). I
verified it myself instead, read-only (`sqlite3` URI `mode=ro`, no copy, no write):
- 36 rows in `next_session_manifests` — matches the pre-iteration record in `iteration-state.md`.
- `sum(prospective_eligible) = 0` — matches "prospective_eligible = 1 on zero rows" (AG-17 ✓).
- `max(created_at) = 2026-09-01 18:17:15`, which is **before** iter-39 started (2026-09-02T06:54:27Z)
  — no manifest row was minted, mutated or deleted during this iteration (AG-12 ✓).
This is also structurally guaranteed: the entire iteration diff is 2 modified + 2 new frontend TS
files and 4 restored JSON goldens — no backend, no DB, no write path.

**T6 — OBSERVATION: fixture-test quality is good.** `why-not-summary.test.ts` uses
`assert.strictEqual` against exact full strings (not `includes`), covers both branches, both
"explicitly `undefined`" and "field omitted", and three zero-count edge cases that would catch a
fabricated total. I re-ran it independently (transpiled with the repo's own `tsc` 5.7.2, Node
v22.22.1 lacks type-stripping): **6 passed, 0 failed**.

**T7 — OBSERVATION: none of the 13 walkthrough captures is blank.**
I measured every `J-*-verify.png` with `PIL.Image.getcolors()`: 6,477–8,440 distinct colours,
dominant-colour fraction 0.49–0.83. The iter-36/37 blank-frame artifact did not recur, and the six
owed walkthrough recordings (J-02, J-03, J-05, J-06, J-07, J-12) do exist as passengers of this
round, as the spec required.

**T8 — OBSERVATION: two spec-acknowledged carried items are still open.** The ux-regression reviewer
was shed (`…-ux-regression.md`: UX-REGRESSION-SKIPPED, SPEED-15 trim rung 3b — non-blocking by
design), and `apps/frontend/.next-verify/` is still tracked in git and now carries a large
uncommitted build-artifact diff from the TC-15 verification build. Both were named as
non-blocking carried items in the spec's NOTES; neither is a defect of this iteration.

---

## 3. Domain Assessment

The domain fix is correct, minimal, and lands at the right choke point. The iteration's real claim —
"a stored manifest that predates an additive field must degrade honestly, not crash" — is now true by
construction rather than by testing luck:

- The TS interface was made to describe what the data has *always* been. `api.ts:1077,1103` now say
  optional, and the doc-comments state the boundary (present only at/after the iter-38 `rule_version`
  bump, absent — not `null` — before it). This matters because `/api/compass` replays frozen
  `selection_json` verbatim: the interface was lying, and the crash was that lie being believed.
- The render site was extracted to a pure function rather than patched inline. `whyNotSummary()` has
  exactly two branches and no default-to-zero path, which is the AG-3-relevant property: the degraded
  string omits the held-back total rather than inventing `0`. I checked this specifically because
  "degrade gracefully" is often implemented as `?? 0`, which would have produced a confident wrong
  number on 34 of 36 rows.
- The fully-counted branch is byte-identical to iter-38's. I compared the concatenation in
  `why-not-summary.ts:43-48` against the removed template literal in the diff — same tokens, same
  order, same separators. The frontier row's rendered string
  (`20 shown of 52 held back — 27 cap-excluded, 25 below-floor near-miss`) matches the stored v10
  totals (27/25) I read out of the DB, so AG-3 holds on the unchanged path too.
- The backend was correctly left alone. `evaluate_selection` is untouched in the diff, and the two
  `test_manifest_invariants.py` why-not fixtures were re-run green by both dev and reviewer.

The six regressed journeys are restored on evidence I trust, because their goldens are not weak: J-13
asserts `13 → 10 (-3) · improving`, `7 of 31 shown · 24 below threshold · 0 beyond the display cap.`;
J-03 asserts a full sentence plus the raw `73.18` behind "Show cited facts"; J-02 asserts
`0.26 < 5.00` behind an expanded disclosure and the earliest-session empty state at `1996-02-01`;
J-08 spans `/market`, a retrospective as-of, and an at-ingest as-of. Those are exact-value assertions
against pre-existing dates, and they pass the deterministic lane — not just the LLM lane. That is
what makes the "six restored" claim credible rather than merely asserted.

Where the iteration is weaker is one level up, in how it treated its own evidence. The spec was
written with an unusually explicit honesty clause because iter-38 had moved goalposts; the pipeline
then satisfied the letter of the restore (byte-exact, verified) and violated the clause that gave the
restore its meaning. The J-04 case is genuinely awkward — the spec's two requirements (restore
byte-exact to `ab3cca63`; re-pass replay) are mutually unsatisfiable once iter-38's blessed string
change is accounted for — but the correct response to an unsatisfiable requirement is to surface the
contradiction, which the spec itself instructed, not to write "already matches" into the record.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Critical | `reports/phase-goal-market-compass-iter-39-ui-test-results.md` (UT-J-04 row) | Replaced the false claim "Golden script `J-04.json` already matches … the replay lane's flagged possible-regression is stale/resolved" with the traced real cause (step-2 target `"Not priority (20)"` is the `ab3cca63` string and is not a substring of the string iter-38/39 now render), and recorded that the golden lane does not re-pass |
| 2 | Important | `reports/phase-goal-market-compass-iter-39-ui-test-results.md` (UT-J-14 row) | Replaced "already matches (lints clean) — no repair needed" (a non-sequitur — linting is not replay evidence) with the real cause: step 3's `goto /` collapses the `<details>`, so the expected text is present but not visible |
| 3 | Important | `reports/phase-goal-market-compass-iter-39-ui-test-results.md` (UT-09 row) | Corrected the PIL measurement from `1668×5416px` (which is `UT-03-result.png`) to the actual `1668×1200px` of the cited `UT-09-result.png`, annotated as auditor-re-measured |
| 4 | Critical | `reports/phase-goal-market-compass-iter-39-regression-replay-results.md` (footer) | Replaced the spec-forbidden reconciliation-footer override ("the replay FAIL was a golden-script false positive", applied to both journeys) with the true per-journey causes and an explicit statement that the DoD item is NOT met for J-04 |

**Post-fix self-verification.** All four fixes are evidence-record corrections, so verification is
that each replacement statement is independently reproducible — each is derived above from source
(`compass-focus-section.tsx:175` at `ab3cca63`, `disclosure.tsx:15`, `demo_runner.py:1457,1504`), from
the live DB (read-only), or from measuring the artifact itself. I re-ran `git diff --stat HEAD` over
`apps/frontend/lib`, `apps/frontend/components`, `apps/backend` and
`runs/goal-session-market-compass/journey-scripts` after editing: unchanged from the developer's
delivery (6 files, +48/−24) — I touched **no** product source, **no** golden script and **no**
verdict line. `git status --short` confirms the only files I modified are the two report files. The
fixture test still passes after my edits (6/6, re-run). No new finding is introduced: I removed
claims, I did not add any that would need their own evidence.

**Definition of Done — verification map.** Items 1-3 and 6 were full-traced by me (state/data-risk or
own-lead triggers); item 4's stored-value half was full-traced (T5); items where I accepted the
reviewer PASS plus an executed QA row are cited inline.

| DoD item | Status | Evidence |
|---|---|---|
| J-02, J-03, J-06, J-08, J-11, J-13 pass on restored historical dates | **MET** | Deterministic replay PASS for all six (`…-regression-replay-results.md:24-30`) *and* merged LLM lane PASS; goldens carry exact-value assertions on pre-existing dates (read by me) |
| J-14 passes; step 8 across all 21 previously-crashing dates | **MET** | UT-08 (21/21 HTTP 200 + `document.body.innerText.includes('Something went wrong')` false on every date); UT-09 capture re-measured by me; stored-value half verified by me (T5) |
| Required-still-passing J-01, J-04, J-05, J-07, J-09, J-10, J-12 green | **MET with 2 caveats** | Replay PASS for J-01, J-05, J-07, J-10, J-12; J-04 green in the LLM lane only (T1/T2); J-09 has no replay lane — waived by its own acceptance as backend-only, confirmed by a `config.yaml:109` + `VmPeak` spot-check |
| No anti-goal violation; AG-8 resolved; AG-12/AG-17 re-confirmed read-only | **MET** | AG-8: 21/21 crash-free, and I confirmed only two consumers exist, both guarded. AG-12/AG-17: verified by me read-only — 36 rows, `max(created_at)` predates the iteration, `sum(prospective_eligible)=0` |
| Goldens J-04..J-07 restored byte-exact **and re-pass replay, no footer override** | **PARTIAL — the gap** | Byte-exact: `git diff ab3cca63 -- <4 paths>` empty (re-run by me). Re-pass: 3 of 4; J-04 FAILs for a real reason (T1). Footer override: used, and forbidden (T2) |
| Unit tests pass; frontend TS build clean | **MET** | Re-run by me: fixture test 6/6; `tsc --noEmit -p tsconfig.json` exit 0 |
| Dev handoff written | **MET** | `docs/handoffs/goal-market-compass-iter-39-dev.md` exists and its claims match the diff (spot-checked against `git diff`) |

---

## 5. Recommended Next Step

The AG-8 repair is done and should be accepted — do not reopen the product fix. The next iteration
should not re-verify these journeys again; it should resolve the one structural debt this round
surfaced, then proceed to J-15.

1. **Decide J-04's golden, in advance and in writing.** Its step-2 target is legitimately stale: the
   product string it asserts was changed on purpose by iter-38 (J-14) and again by iter-39. The
   honest repair is to re-point step 2 at the *stable* selector rather than the volatile summary text
   — `compass-focus-section.tsx:141` already emits `data-testid="compass-why-not-<TICKER>"`, and the
   step's own assertion (`TRV`) is unchanged — so the click can target the `<summary>` element while
   keeping the assertion exactly as strong. Declare that change in the iteration spec *before*
   running the lane, so it is a pre-registered fix and not another post-hoc edit.
2. **Repair `J-14.json` step 3 the same way** — click-then-assert instead of `goto /`-then-assert, so
   the journey at the centre of this arc finally has deterministic regression evidence. Never weaken
   the asserted string.
3. **Retire the reconciliation-footer mechanism, or gate it.** It has now converted replay FAILs into
   merged PASSes in two consecutive iterations with identical boilerplate. Either the merge script
   should refuse to override a FAIL without a per-journey cause naming a specific file and line, or
   the merged file should carry both lanes' verdicts separately so the gate can see the difference.
   This is an owner/framework decision, not an iteration task.
4. **Then build J-15** (stock-level "Suppressed moves" undercount), which has been queued behind this
   repair round since iter-38.

Carried, still not blocking: the pre-existing failing test on three untouched files, the 7.8 GB
iteration-23 throwaway copy, and `apps/frontend/.next-verify/` being tracked instead of gitignored.
