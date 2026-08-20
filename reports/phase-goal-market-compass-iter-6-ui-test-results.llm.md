# Phase goal-market-compass-iter-6 — UI Test Results

**Phase:** goal-market-compass-iter-6
**Date:** 2026-08-20
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** SKIPPED

<!-- SKIPPED: this lane is blocked by the goal contract's own lane gate (docs/goal.md,
     "Loop mechanics (for the iteration planner)", owner insert #2), NOT by frontend or
     Chrome MCP unavailability. Frontend was reported available at http://localhost:3255
     and Chrome MCP is available. The canonical database is knowingly damaged — the iter-5
     destructive-drill incident deleted daily_prices / scanner_runs rows for 2026-08-11 and
     2026-08-12, and the committed seed (window ending 2026-07-01) cannot restore them. Per
     docs/goal.md: "No developer, reviewer, QA, browser-QA, evaluator, coherence, research or
     proposer lane may run against the knowingly damaged database before J-10's post-recovery
     verification passes." J-10's recovery did NOT complete this iteration (the authorized
     Stooq fetch was blocked vendor-side — see UT-J-10). No browser was opened, no
     deterministic replay was run, no pytest was run, no service was started or restarted,
     and no golden replay script was written or overwritten this run. -->

**Overall:** 0/3 tests passed (3 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-02 | "What changed" reports meaningful session-over-session deltas with honest empties | journey | P1 | Not evaluated — lane gated by goal contract | Not executed. `docs/goal.md` (Loop mechanics, owner insert #2) forbids browser-QA from running against the knowingly damaged database before J-10's post-recovery verification passes; that verification did not complete this iteration. J-02's Acceptance depends on session-over-session data for exactly the deleted 2026-08-11/2026-08-12 window. | SKIP | none — no browser opened this run |
| UT-J-03 | The plain-English summary is deterministic, cited, and never invents a cause | journey | P1 | Not evaluated — lane gated by goal contract | Not executed. Same lane gate as UT-J-02. J-03's summary sentences are generated from the same manifest/session-delta substrate that depends on the deleted 2026-08-11/2026-08-12 price data. | SKIP | none — no browser opened this run |
| UT-J-10 | Bounded recovery of the two trading days the iter-5 drill deleted | journey | P1 | Not evaluated — recovery incomplete this iteration | Not executed. J-10 is itself the recovery/verification journey; its Acceptance requires the frontier to reach 2026-08-12 and `GET /api/compass?as_of=2026-08-12` to serve before "J-01/J-02/J-03 replay clean" can even be checked. This iteration's authorized Stooq fetch (AG-9's dated exception) was blocked vendor-side — all 587 requests returned 404 behind a JavaScript proof-of-work challenge — so the frontier is still 2026-08-10 and `GET /api/compass?as_of=2026-08-12` still returns 400. J-10's own Walkthrough requirement is separately waived in goal.md ("data-layer repair with no UI surface change of its own") — it was never a UI-testable journey. | SKIP | none — no browser opened this run |

---

## Skipped Tests

### UT-J-02 — "What changed" reports meaningful session-over-session deltas with honest empties
**Verdict:** SKIPPED
**Reason:** Lane gate, not infrastructure failure. `docs/goal.md`, section "Loop mechanics
(for the iteration planner)", owner insert #2 (2026-08-20, incident response), states
verbatim: *"No developer, reviewer, QA, browser-QA, evaluator, coherence, research or
proposer lane may run against the knowingly damaged database before J-10's post-recovery
verification passes."* The canonical database is missing `daily_prices` and `scanner_runs`
rows for 2026-08-11 and 2026-08-12 (deleted by the iter-5 destructive-drill incident; the
committed seed window ends 2026-07-01, so nothing local could restore them). J-10's recovery
did not complete this iteration (see UT-J-10), so this journey's precondition is unmet. J-02's
Acceptance requires the delta engine to serve correct session-over-session comparisons
anchored on the immediately preceding stored run — for the 2026-08-11/2026-08-12 window that
data no longer exists. **A failure of J-02 against this dataset would be expected damage from
the known incident, not a regression** (see Notes below on the already-invalidated evidence
from an earlier automatic replay). Frontend (http://localhost:3255) and Chrome MCP were both
available; this skip is a deliberate contract decision, not a technical one, and Chrome MCP
was never invoked.

### UT-J-03 — The plain-English summary is deterministic, cited, and never invents a cause
**Verdict:** SKIPPED
**Reason:** Same lane gate as UT-J-02 (`docs/goal.md`, Loop mechanics, owner insert #2). J-03's
summary sentences are generated from the same manifest/session-delta substrate that depends on
the deleted 2026-08-11/2026-08-12 price data, so it falls equally within the gate. A failure of
J-03 against this dataset would likewise be expected damage from the known incident, not a
regression. Not executed; Chrome MCP was never invoked.

### UT-J-10 — Bounded recovery of the two trading days the iter-5 drill deleted
**Verdict:** SKIPPED
**Reason:** J-10 is the recovery/verification journey itself, and its own Acceptance criteria
were not met this iteration: the authorized Stooq fetch (AG-9's dated exception, scoped to
exactly 2026-08-11 and 2026-08-12) was blocked vendor-side — all 587 requests returned 404
behind a JavaScript proof-of-work challenge — so the dataset frontier remains 2026-08-10 and
`GET /api/compass?as_of=2026-08-12` still returns 400. Per J-10's own Acceptance text, checking
that "J-01/J-02/J-03 replay clean" is itself one of the post-recovery verification steps and
cannot be performed before recovery succeeds — testing it now would be circular. Separately,
J-10's Walkthrough requirement is explicitly waived in `docs/goal.md` ("data-layer repair with
no UI surface change of its own; the demo requirement is replaced by the provenance record,
the verification evidence, and the J-01/J-02/J-03 live replay that proves the damage is
gone"), so this was never a UI-testable journey to begin with. Not executed; Chrome MCP was
never invoked.

---

## Notes — invalidated prior evidence (do not treat as a clean signal)

An earlier, separate automatic process in this same iteration — a lean-depth parallel
browser-QA replay, triggered by `CHAIN_LEAN_PARALLEL_BROWSER_QA` after iter-6's depth was
silently demoted full→lean — fired a deterministic J-01–J-04 replay at **18:15–18:16Z against
this same knowingly damaged database**, before this dispatch ran. That replay recorded
`REPLAY_FAILED=J-02 J-03` and produced screenshots (`J-01-verify.png`, `J-02-verify.png`,
`J-03-verify.png`, `J-04-verify.png`), now under
`reports/qa/goal-market-compass-iter-6-evidence/`.

That evidence is invalid and is already documented as such by the coordinator (pump), on the
iter-6 reviewer's recommendation, in
`reports/qa/goal-market-compass-iter-6-evidence/INVALID-damaged-database.md`. Per **AG-17**,
artifacts produced while the database was known to be damaged remain unusable as
prospective/out-of-sample evidence and must **not** be merged into `journey-history.json` and
must **not** be read as a regression signal — `REPLAY_FAILED=J-02 J-03` from that run is
expected damage from the known incident, not a genuine regression. This report's author did
not delete, alter, or rely on those files; they are referenced here only so the evaluator does
not mistake either that earlier run's FAIL rows, or this run's SKIP rows, for a clean
pass/fail signal on J-01/J-02/J-03/J-04.

**No journey — J-02, J-03, or J-10 — is marked PASS or FAIL by this report. All three are
SKIP**, for the reasons given above. No journey may be marked passing or failing from this
run. No golden replay script was written or overwritten this run for any of J-02, J-03, or
J-10 — a golden captured against a damaged dataset would poison future replays.

---

## Environment

- **Frontend URL:** http://localhost:3255 (reported available by dispatch; not contacted this
  run — no browser was opened)
- **Browser:** Chrome via MCP (available, but not invoked this run — lane gated before any
  browser action)
- **Test Date:** 2026-08-20
- **Evidence directory:** `reports/qa/goal-market-compass-iter-6-evidence/` (no new evidence
  written this run; it already holds the pre-existing invalidated J-01–J-04 screenshots and
  `INVALID-damaged-database.md` from the earlier, separate lean-depth parallel replay — see
  Notes above)
