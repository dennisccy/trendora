# goal-i_can_see_the_wealthy_future_forever-iter-27 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-27
**Date:** 2026-06-09
**Agent:** developer
**Status:** complete

## What Was Built

**No production code was written.** This is a **capture-only** iteration. The build for J-35 /
J-37 / J-38 / J-39 is DONE and committed at HEAD `77d0816` (`git diff --stat HEAD -- apps/ config.yaml`
is empty — re-verified). The deliverable is **browser-QA harness wiring** to the throwaway fixture DB +
the env-gated offline `seed` import source so the four target flows are *reachable* and can be captured
end-to-end — the exact thing that was missing in iters 23/24/25/26 (the dedicated browser-qa-agent ran
against the LIVE host with the seed env flags unset, so no insufficient member, no resumable checkpoint,
and no `seed` source existed).

I **verified the entire harness end-to-end at the API layer** (fixture build → fixture-wired backend on
a throwaway port → `seed` source present → all three diagnostic categories → gap-exact pull-to-completion
→ seed expand → resume-needs-key-400) so the QA/browser step cannot fail the same way again. **No code
defect surfaced, so no production source or test was changed** (per the spec's conditional-fix rule).

---

## THE HARNESS RECIPE (QA/browser-qa-agent MUST follow this verbatim — do NOT run against the live host)

> The four target flows are ONLY reachable against the fixture DB with the three env flags set. Running
> the browser-qa-agent against the live host (`:8835`) with the seed env unset is the iter-23/24/25/26
> recurrence — it makes every target unreachable and all four stay `partial`. Follow these steps exactly.

### Step 0 — Stop strays BY PORT ONLY (shared machine — MEMORY `dev-server-cleanup-by-port`)
NEVER broad `pkill -f "next dev"` / `pkill -f "uvicorn"`. Kill only the QA ports you intend to reuse:
```bash
# Find and kill ONLY the listener on the QA backend/frontend ports you will reuse.
# (Default project offset → backend 8835 / frontend 3835. The live dev server may be there;
#  the browser-qa harness is expected to (re)claim those ports for the fixture-wired backend.)
for P in 8835 3835; do
  PID=$(ss -ltnp 2>/dev/null | grep ":$P " | grep -oP 'pid=\K[0-9]+' | head -1)
  [ -n "$PID" ] && kill "$PID" && echo "killed pid $PID on :$P"
done
```

### Step 1 — Clear the prod-build dead shell (MEMORY `browser-qa-dead-shell-next-cache`)
```bash
rm -rf apps/frontend/.next
```

### Step 2 — Build the throwaway fixture DB + narrowed config + seed overlay
```bash
cd apps/backend
.venv/bin/python scripts/build_qa_fixture_db.py --out /tmp/trendora_qa_fixture_iter27
```
It prints a final JSON line. Its `env` block carries the **three values** you must export
(VERIFIED this run — yours will match if `--out` is the same):
```json
"env": {
  "TRENDORA_ENABLE_SEED_IMPORT_SOURCE": "1",
  "TRENDORA_CONFIG": "/tmp/trendora_qa_fixture_iter27/config.yaml",
  "TRENDORA_SEED_IMPORT_DIR": "/tmp/trendora_qa_fixture_iter27/seed_overlay"
}
```
The fixture narrows `universe.symbols` to **ANET / DELL / MU / AMD** so the diagnostic renders all three
categories — **no_history ANET** (0 bars), **thin DELL** (40/200 bars), **intra_series_gap MU**
(10 missing days `2025-12-04..2025-12-17`) — and seeds a `market_caps.csv` so a `seed` expand can screen.
It writes ONLY under `/tmp/trendora_qa_fixture_iter27/` and **NEVER mutates the committed seed tree or the
live `trendora.db`**.

### Step 3 — (Re)start the backend WITH the three env values, on the QA backend port
```bash
cd apps/backend
OUT=/tmp/trendora_qa_fixture_iter27
TRENDORA_ENABLE_SEED_IMPORT_SOURCE=1 \
TRENDORA_CONFIG="$OUT/config.yaml" \
TRENDORA_SEED_IMPORT_DIR="$OUT/seed_overlay" \
.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8835 --app-dir "$(pwd)"
# (ASGI app is `main:app` with --app-dir apps/backend, per scripts/start-backend.sh — NOT `app.main:app`.)
```
The fixture `config.yaml` already points `database.url` at `$OUT/qa_fixture.db`, so the backend boots
against the fixture DB automatically.

### Step 4 — Restart the frontend, confirm it is NOT a dead shell BEFORE any UI capture
```bash
cd apps/frontend && npm run dev   # (or the project dev script) on the QA frontend port 3835
```
Then VERIFY (a dead-shell / down result is SKIPPED → **re-wire**, do not accept the partials):
```bash
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3835/_next/static/chunks/main-app.js   # expect 200
# and confirm the "Checking backend…" health badge has cleared on the /data page before driving UI
```

### Step 5 — GATE before any expand/pull: assert the `seed` source reached the running backend
```bash
curl -s http://localhost:8835/api/data | python3 -c "import sys,json; d=json.load(sys.stdin); \
print('seed source present:', any(s['id']=='seed' for s in d['sources'])); \
print('universe_count:', d['coverage']['universe_count']); \
print('diagnostic categories:', list(d['coverage']['diagnostic'].keys()))"
# EXPECT: seed source present: True | universe_count: 4 | categories incl no_history/thin/intra_series_gaps
```
If `seed source present` is False, the env flag did NOT reach the running backend → **re-wire** (do not
attempt the captures).

---

## VERIFIED THIS RUN (API-layer proof the four flows are reachable — re-capture each in the BROWSER)

Booted a fixture-wired backend on a throwaway port and exercised each flow live (then killed it; the live
`:8835`/`:3835` were left untouched). Results:

- **`seed` source present in the picker** — `available=True, needs_key=False` (was ABSENT in iters 23-26).
- **J-37 three-category diagnostic** — exact shortfalls:
  - `no_history`: ANET, `bars_have=0 / bars_needed=200`, pull range `2025-06-30..2026-05-28`
  - `thin`: DELL, `bars_have=40 / bars_needed=200`
  - `intra_series_gap`: MU, `missing_day_count=10`, gap `2025-12-04..2025-12-17`
- **J-37 gap-exact pull-to-completion** — `POST /api/data/jobs {kind:fetch, source:seed, symbols:["MU"],
  start:2025-12-04, end:2025-12-17}` → `status=ok, symbols_ok=1, bars_fetched=10` (EXACTLY the diagnosed
  gap, NOT the whole universe/window) → **the MU `intra_series_gap` diagnostic row CLEARED** afterward.
- **J-35 seed expand end-to-end** — `POST /api/data/jobs {kind:expand, source:seed, start:2025-06-30,
  end:2026-05-28}` → **17 passers, 531 omitted-with-reason** (`empty_series`, `no_market_cap` — honest, no
  fabrication) of 548 candidates, 27550 new bars; wrote a grown `universe.json` (17 members) + `meta.json`
  to the OVERLAY (never the committed seed).
- **J-38 needs-key resume 400** — `POST /api/data/jobs/{id}/resume` for a needs-key source with no key
  returns `400 "source '<x>' requires a key; set $<ENV_VAR> or paste a session key"` — the detail echoes
  only the env-var NAME, never a key value (J-33 scrub holds). The frontend `resume-error` alert
  (`role="alert" data-testid="resume-error"`, `apps/frontend/app/data/page.tsx:1332`) renders it inline
  and the row is retained — both present at HEAD.

### Capture notes for the browser-qa-agent (per-target)
- **J-37:** capture the three diagnostic rows (distinct hydrated shot), click the MU row's "Pull the
  missing data", poll to completion, then capture the row CLEARED + J-36 coverage updated. Assert the
  fired `POST /api/data/jobs` body has `symbols:["MU"]` + `[2025-12-04, 2025-12-17]` (gap-exact, NOT whole
  universe). Distinct before/after sha.
- **J-38:** the fixture does NOT pre-seed a resumable checkpoint. To capture the SUCCESSFUL
  Resume-from-`next_chunk_index`, drive a `seed`-source import that the harness pauses into a `resumable`
  checkpoint (or use the existing J-34 capture mechanism), then Resume and capture continue-from-checkpoint
  (distinct before/after sha). Separately capture the needs-key Resume-without-key → 400 → visible inline
  `resume-error` alert → row retained (use a needs-key source id for that one).
- **J-39:** confirm-preview removable-user-bars + protected-seed breakdown + cascade via the
  **non-destructive PREVIEW** path on the LIVE host (`POST /api/data/remove/preview`) — NEVER the
  destructive `POST /api/data/remove` on a real live symbol (MEMORY `j39-live-host-has-user-added-nvda-bars`:
  NVDA has 6 user-added bars; a live destructive remove cascades ~5 snapshots and `trendora.db` is
  gitignored/unrestorable). The destructive confirm + whole-row cascade is captured ONLY against the
  throwaway fixture DB. Also capture the wholly-seed-scope refusal (explicit reason).
- **J-35:** capture the expand result panel — passers (17) + omitted-with-reason list + grown universe
  count. NOTE: `/api/data universe_count` reflects `config.universe.symbols` (the narrowed 4), so the
  GROWN count is read from the **expand job's result panel** (`passers` / `universe_members:17` in the
  overlay `meta.json`), not from a live `universe_count` re-read — capture the result panel's grown count.

### Watch-risk re-verification (must STAY green)
- **J-18 (flagged):** on `/data` and any date-scoped page, `document.querySelectorAll('select, input[type=date]')`
  → exactly ONE global as-of `<select>` per page. The seed source / expand / pull / resume controls add
  ZERO new date state; the job/action date inputs are job PARAMETERS, not a second date control.
- **J-33 (key scrub):** on every new pull/retry/resume/expand error string, grep the job-status response
  `GET /api/data/jobs/{id}` `errors[]` AND the job card AND run history — the sentinel +
  `?token=`/`?apikey=` must be ABSENT (real-httpx assertion; MEMORY `httpx-error-leaks-url-query-key`).

---

## Files Changed

- `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-27-dev.md` -- this handoff (the verbatim
  fixture-build + env-export + clean-boot recipe).
- `reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-27-implementation-summary.md` -- operator summary.
- `runs/goal-i_can_see_the_wealthy_future_forever-iter-27/status.json` -- status → `dev_complete`.

**No `apps/` or `config.yaml` change** — `git diff --stat HEAD -- apps/ config.yaml` stays EMPTY (capture-only).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q` (run ONCE — full suite ~14 min per
MEMORY `backend-test-suite-runtime`).
Result: see `reports/phase-...-implementation-summary.md` / status.json — the existing suite stays green;
no test was added because no defect surfaced.

## Known Issues

- The fixture does NOT pre-seed a resumable `seed`-source checkpoint for J-38's SUCCESSFUL-Resume capture
  (only the no_history/thin/gap members + a market-cap overlay). The browser-qa-agent must DRIVE a
  pause-into-resumable (or reuse the J-34 checkpoint path) to capture the continue-from-`next_chunk_index`
  before/after — the needs-key-400 half is reachable directly. Flagged so QA does not assume a pre-seeded
  checkpoint exists.
- J-35 grown universe count is read from the **expand result panel** (`passers` / overlay `meta.json
  universe_members`), NOT from a live `/api/data universe_count` re-read — `universe_count` reflects the
  loaded `config.universe.symbols` (narrowed to 4), which the expand does not hot-reload. This is the
  intended fixture behavior, not a defect; QA should assert against the result panel's grown count.
- All API-layer verification was done on a throwaway port (`:8899`) which was killed afterward; the live
  `:8835`/`:3835` were never touched. The browser-qa-agent re-wires the QA ports to the fixture itself.
