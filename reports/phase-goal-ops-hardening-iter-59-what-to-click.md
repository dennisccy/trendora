# Phase goal-ops-hardening-iter-59 — What to Click (Operator Verification Guide)

**Phase:** goal-ops-hardening-iter-59
**Time required:** ~5 minutes
**Written by:** ui-impact-analyst (combined mode)

---

## Prerequisites

- Frontend running at `http://localhost:3255`
- Backend running at `http://localhost:8255` (start it with `scripts/start-backend.sh` if not already up)
- No login required
- Shell access to the backend host is needed for steps 4-6 (restarting with a test-only environment
  variable). If you only have a browser, do steps 1-3 and 7 and skip 4-6.

---

## Verification Steps

1. Open `http://localhost:3255/research/regime-lab` in your browser
   - **Expect:** The page loads with the heading "Research — Regime Lab", and two tables appear: "By
     regime label" and "By regime-score decile". No red error card, no blank page.

2. In the "By regime label" table, hover any cell in the "Fwd 20d" column that shows a number (not "NA")
   - **Expect:** A tooltip/hover card appears showing the underlying figures for that cell. This confirms
     normal cells still render real numbers exactly as before this phase (the fix is provably byte-identical
     under normal conditions).

3. Hover any cell that already shows "NA" (if one exists in the current data)
   - **Expect:** A tooltip appears reading either "Low sample — n below the 30 minimum" or "No
     observations"/"No stored drawdown — NA" — the two ORIGINAL reasons a cell is NA. (If no such cell
     exists in the current dataset, skip this step — it is not required for a pass.)

4. Stop the backend, then restart it with the test-only environment variable set:
   `TRENDORA_FAULT_INJECT_MEMORY_ERROR=regime_lab scripts/start-backend.sh`
   - **Expect:** The backend starts normally (same boot behavior as any other restart).

5. Reload `http://localhost:3255/research/regime-lab`
   - **Expect:** The page STILL loads successfully — no red "Backend unavailable" card, no crash. Every
     "Fwd Xd"/"MDD Xd" cell in both tables now shows "NA". Hover any of them.
   - **Expect (tooltip text):** "Temporarily unavailable — degraded under memory pressure" — this is the
     new behavior this phase adds. This exact wording, distinct from step 3's wording, is the pass
     criterion.

6. Stop the backend and restart it again WITHOUT the environment variable:
   `scripts/start-backend.sh`
   - **Expect:** Normal restart, no special flag needed.

7. Reload `http://localhost:3255/research/regime-lab` one more time
   - **Expect:** Real numbers are back in the "Fwd Xd"/"MDD Xd" columns — the "Temporarily unavailable"
     state was transient and tied only to the fault-injection flag, not a stuck/cached state.

---

## What "Working Correctly" Looks Like

- Under normal conditions, `/research/regime-lab` looks and behaves exactly as it did before this phase —
  no visible change at all.
- Only when the backend is deliberately started with `TRENDORA_FAULT_INJECT_MEMORY_ERROR=regime_lab` does
  the page show "NA" cells with the new "Temporarily unavailable — degraded under memory pressure"
  tooltip — and the page keeps working (no crash, no error card) while showing them.
- Restarting the backend without that flag immediately restores normal numbers — nothing gets stuck in the
  degraded state.

## Common Issues

- **Red "Backend unavailable" card instead of the tables**: the backend is not running or is unreachable.
  Confirm with `curl http://localhost:8255/api/health`.
- **Step 5 shows real numbers instead of "NA"**: the environment variable was not actually applied to the
  backend process — confirm the backend was fully stopped and restarted (not just reloaded) with the
  variable exported in the same shell/command that launched `scripts/start-backend.sh`.
- **Tooltip text doesn't match exactly**: hover directly over the "NA" text itself (not the surrounding
  cell padding) and wait a moment for the browser's native tooltip to appear.
