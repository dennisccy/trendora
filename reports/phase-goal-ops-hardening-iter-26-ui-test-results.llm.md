# Goal Iteration 26 — UI Test Results

**Phase:** goal-ops-hardening-iter-26
**Date:** 2026-07-26
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All smoke and happy-path tests pass. -->

**Overall:** 1/1 tests passed (0 skipped)

Lean-mode scope: this run tests ONLY J-09 (Chrome MCP, live). J-01, J-03–J-08 are explicitly
out of scope for this dispatch — verified separately via deterministic golden-script replay
(`runs/goal-session-ops-hardening/journey-scripts/{J-01,J-03..J-08}.json`); not re-driven here.

Iter-26 shipped no new user-facing capability for J-09 — a backend test-coverage addition plus a
pure-function extraction of `LastOutcomeSummary`'s render decision (byte-identical for the
`completed` case). Per the iter-26 spec's Testing Requirements, this is a **regression-only** J-09
pass: confirm the existing idle/active/unknown panel states and the global readiness badge still
render exactly as before. No new live capture of a genuinely failed background compute is required
(out of scope this iteration; the failure round-trip is covered by backend/frontend unit tests, not
browser QA — see NOTES/assumption ledger in the iter-26 spec).

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-09 | Backend discloses its own background-compute activity (regression pass) | regression | P1 | Readiness badge reads plain `Ready` at idle; `/data`'s `BackgroundComputePanel` renders the idle-no-outcome state honestly, and — once a real BCW is triggered and completes — the idle-with-last-outcome state with correct as-of key, `completed` badge (positive styling), and real measured duration, matching the live `/api/health` payload verbatim; process-lifetime disclosure present throughout | All of the above observed live and cross-checked against `GET /api/health` — see steps below | PASS | `reports/qa/goal-ops-hardening-iter-26-evidence/UT-J-09-01-data-page-top-badge.png`, `UT-J-09-readiness-badge.outerHTML.txt`, `UT-J-09-data-panel-completed-lastoutcome.outerHTML.txt`, `UT-J-09-health-snapshot.json` |

---

## Passed Tests

### UT-J-09 — The backend discloses its own background-compute activity (regression pass)
**Verdict:** PASS
**Evidence:**
- `reports/qa/goal-ops-hardening-iter-26-evidence/UT-J-09-01-data-page-top-badge.png` (readiness badge, top of `/data`, "Ready" state)
- `reports/qa/goal-ops-hardening-iter-26-evidence/UT-J-09-readiness-badge.outerHTML.txt` (badge DOM, `data-state="ready"`)
- `reports/qa/goal-ops-hardening-iter-26-evidence/UT-J-09-data-panel-completed-lastoutcome.outerHTML.txt` (panel DOM, idle + last-outcome state)
- `reports/qa/goal-ops-hardening-iter-26-evidence/UT-J-09-health-snapshot.json` (live `GET /api/health` payload captured at the same moment as the DOM extraction above)
- `reports/qa/goal-ops-hardening-iter-26-evidence/UT-J-09-scrolled-panel.png` (confirmed BLANK — see screenshot-blindness note below; kept as evidence of the blindness, not of panel content)

**Steps taken and observations:**

1. **Steady-state Ready + no fabricated detail.** Navigated to `http://localhost:3255/data` fresh.
   `GET /api/health` at the same time showed `background_compute: {"active": [], "recent_outcomes": []}`
   (backend was recently restarted by the coordinator — process-lifetime history was empty). DOM
   extraction of `[data-testid="readiness-badge"]` showed `data-state="ready"` and text `Ready`, plain,
   with no background-compute detail appended — correct, since idle carries no in-flight detail to show.
   `BackgroundComputePanel` (`[data-testid="background-compute-panel"]`) rendered
   `data-testid="background-compute-idle"` = "No background compute running. Last outcome: none yet."
   plus the process-lifetime footer — matches the pre-existing "idle, none-yet" state captured in
   iter-25's evidence (`UT-J-09-06-idle-none-yet-post-restart.html`).

2. **Trigger one real BCW the way a user does.** Per J-09 step 2, navigated to `/backtest?asof=2001-04-17`
   (a historical date whose forward-aggregate evidence was not yet cached for the current dataset
   version). The `/backtest` request returned immediately (page rendered; J-08 unchanged). Polling
   `GET /api/health` in the following seconds showed the window had already dispatched and completed
   (`started_at` 18:31:49.882, `finished_at` 18:31:51.714, `duration_ms` 1832) — this dataset's
   remaining lazy-compute gaps resolve in under 2s, faster than the round-trip needed to reliably
   catch the "active" in-flight badge/panel state via browser navigation + capture. (See NOTES below —
   this is expected and does not indicate a defect; the active-state code path is byte-frozen and
   untouched by this iteration's diff.)

3. **Idle-with-completed-last-outcome regression (the state this iteration's refactor actually
   touches).** Triggered a second BCW at `/backtest?asof=1999-11-02` (also completed before poll,
   `duration_ms` 1623). Re-navigated to `/data` and extracted the panel DOM. It rendered:
   `data-testid="background-compute-last-outcome"` containing a badge with text "completed" and
   classes `border-pos bg-surface-2 text-pos` (the positive/"ok" styling), `as-of 1999-11-02`, and
   `1.6s`. Cross-checked against the live `GET /api/health` snapshot captured at the same moment:
   `recent_outcomes[0] = {asof_key: "1999-11-02", outcome: "completed", duration_ms: 1623, reason: null}`.
   `1623ms → "1.6s"` and `outcome: "completed" → badge "completed"/pos-styling` match exactly —
   confirms `resolveLastOutcomeSummary` (the new `background-compute-last-outcome.ts` extraction this
   iteration wired into `LastOutcomeSummary`) renders the `completed` case byte-identically to the
   pre-refactor inline logic (TC-6: no visual regression from the extraction). No reason text is
   rendered for the completed case (correct — only `failed` carries a `reasonText`, per TC-5, which is
   the same code path this iteration's new unit test exercises at the code level).
   Process-lifetime disclosure ("Since the last backend restart — this history is process-lifetime
   only, never persisted.") remained present and unchanged throughout.

4. **Correctness / single-source cross-check (AG-3).** Every value rendered in the panel and badge
   at every observed poll matched the corresponding `GET /api/health` `background_compute` field
   read at the same time — no discrepancy found. No fabricated percentage or estimated finish time was
   observed anywhere (only real elapsed/duration figures), consistent with J-09 step 6.

**Screenshot-blindness (per coordinator note):** the `BackgroundComputePanel` is the last panel on
`/data`, ~25000px down a DEGRADED-banner-lengthened page (`document.documentElement.scrollHeight`
measured 25247px at capture time — the ticker-by-ticker preflight drift list adds most of that
height). A `scrollIntoView` + screenshot of the panel returned a screenshot with exactly **1 unique
pixel color** (confirmed via `PIL.Image.getcolors`) — a solid blank frame, exactly as flagged. That
file (`UT-J-09-scrolled-panel.png`) is kept as evidence of the blindness itself, not of panel
content. Panel and badge state were instead verified via `outerHTML` DOM extraction, cross-checked
field-for-field against the live `GET /api/health` payload sampled at the same moment (see steps
1–4) — no visual evidence was treated as sufficient on its own for the below-the-fold panel.

**No new live failure capture (by design this iteration):** J-09 step 4's "failed" branch was not
re-triggered live — the iter-26 spec explicitly scopes this to backend (`TC-4`) and frontend
(`TC-5`) unit/code-level round-trip tests rather than a live 5-concurrent-BCW memory-pressure
trigger (unsafe on this host, tracked as backlog B-1107). This is consistent with the Testing
Requirements' "no new capture of a live failure state required" instruction and is not treated as a
gap in this browser QA pass.

---

## Failed Tests

None.

---

## Skipped Tests

None. Frontend (http://localhost:3255) and backend (http://localhost:8255/api/health, readiness
`ready`) were both live and verified before testing; Chrome MCP was available and used for all
steps above.

---

## Golden Replay Script

`runs/goal-session-ops-hardening/journey-scripts/J-09.json` — re-verified against the live app this
iteration (unchanged from the prior iteration's script; every `expect.text` value was independently
confirmed present in the current build during this run: "Time-machine" on `/backtest`,
"(historical)" after clicking "Previous available date", "Background compute" and "process-lifetime
only, never persisted" on `/data`). Linted clean:
`python3 scripts/automation/lib/demo_runner.py --mode lint --scripts-dir runs/goal-session-ops-hardening/journey-scripts --journeys J-09` → `J-09 ok`. Left in place (overwrite not needed — content
already current).

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255 (`/api/health` → `readiness: "ready"`, `db_ok: true`)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`)
- **Test Date:** 2026-07-26
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-26-evidence/`
