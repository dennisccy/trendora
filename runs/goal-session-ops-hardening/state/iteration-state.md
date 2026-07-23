# Iteration State — ops-hardening

**After iteration:** 12 · **Date:** 2026-07-23 · **Verdict:** CONTINUE

## Journeys

4 passing (J-01 J-03 J-04 J-05) · 1 partial (J-06 — target; G1/G2 CLOSED, but its own budget is breached) · 0 failing — 5 total.

## Active blockers

- **J-06 over-budget endpoint (AGENT-tractable — the one thing keeping this from STALLED).**
  `GET /api/indexes?full=true` on `/data` reads 2257.7/2148.2/2138.7 ms vs its ≤1.5 s budget on a VERIFIABLY
  idle host (`perf-budgets.md` "### G2 (closure)") — real 43–51% overage, not ambient; was ~0.87 s in iter-6.
  Fix = goal.md aggregation candidate #7 (normalized index series → keyed cache warmed at ingest), OR an owner
  budget-raise. J-06 step 2 "assert every measurement is within budget" fails → stays partial.
- **AG-8 critical, UNRESOLVED — OWNER call, hard-blocks GOAL_ACHIEVED.** `forward_aggregates_cached` →
  `compute_forward_aggregates` unbounded `ScannerResult` load (`forward_testing.py:826`) OOMs under the 6144 MB
  cap. Reconfirmed live 3-for-3 iter-12 (runs 120/121/122; `logs/backend.log:26920/27185/27233`) but caught
  internally — ZERO client 500s this time (smaller than iter-11's two). Owner: rewrite, amend, or defer.
- **Owner/framework, also blocking GOAL_ACHIEVED:** `[NEW] demo.sh --session-live` walkthrough (decomposer
  PROVED no autonomous mechanism — human run-once / wording amendment / framework record-mode) ·
  `HOST_GUARD_REQUIRE_MARKERS` · the `/api/indexes` budget-raise-vs-fix choice.
- **Services:** operator note + dev handoff say backend :8255 / frontend :3255 UP, host-guard caps live.

## Last 2 verdicts

- iter 12: CONTINUE — J-06 G1/G2 gaps closed, but G2 confirms `/api/indexes?full=true` genuinely 43–51% over
  its ≤1.5 s budget on an idle host → J-06 stays partial (scored on the contract, not measurement-happened).
- iter 11: ESCALATE — J-06 stayed partial; lean lanes mis-read a live per-process memory exhaustion as ambient.

## Do not redo
- **iter-12 diff EMPTY** (`iter-diff.md` "(no changes)", scan CLEAN); only `perf-budgets.md`. **G1 CLOSED**
  (sweep ~1734-1826) · **G2 CLOSED in canonical artifact** (3 idle readings ~1866-1905) · **TC-4 correction DONE**.
- **J-05 4-of-7 on zero-new-date runs = design-consistent; J-05 contract INTACT — do not re-open.**
  **Heavy-ingest test settled, do NOT re-run** (iter-9). **Boot budget DONE** (iter-11: 1.364 s).
- **Do NOT touch** `health.py`, `readiness.py`, `main.py` boot, `warmup.py`, `max_range_days`, `/evidence`
  drawdown warm, `server.memory_cap_mb`. **AG-8 fix is OWNER-scoped — do not invent it. AG-10 held both sides.**
- **Process:** never hand-edit past artifacts; never patch `scripts/automation/*`; score J-01/J-03/J-05 from the
  LLM lane (golden-replay step-02 fill flake is a framework item).
