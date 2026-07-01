# Goal iter-9 — Implementation Summary

**Phase:** goal-mcp-loop-iter-9
**Date:** 2026-07-01
**Written by:** developer

---

## Features Implemented

- **Sustainable trial economy (internal, off by default)**: The platform gained a private "practice
  ledger" for testing new statistical claims. Today, every claim the platform tests permanently makes the
  bar for *proving* the next one harder — a single running counter that only ever tightens — so a wide,
  ongoing search eventually can't certify anything. This change adds a separate, isolated **staging**
  place to run exploratory tests under an *online false-discovery-rate* economy that **earns back testing
  capacity every time it finds a real edge**, so exploration can keep going. It is **switched off by
  default**, so nothing about today's behavior changes yet — it is the foundation the next two iterations
  (multi-horizon and multi-factor "proven" edges) will build on.

- **The proving engine now supports a pluggable "how strict" rule**: The referee that decides whether an
  edge is real can now be told which strictness policy to use. The default is exactly today's rule
  (strict Bonferroni), reproduced identically; the new online-FDR rule is available only for the internal
  staging area.

- **An honest "which ledger" router in the pre-build gate**: When a future iteration proposes a claim, it
  can mark it for the internal staging ledger (the default) or, for a deliberately promoted winner, the
  real user-facing ledger. Anything unrecognized or misconfigured is **blocked**, never quietly approved.

---

## Changed Behavior

- **None visible.** This is a backend-infrastructure iteration with **zero user-visible change by
  design**. The Evidence page, every "Proven / Not yet proven" badge, and the `/api/evidence` data are
  **byte-for-byte identical** to before. The four existing certified claims (leadership-score, a
  Breakout-watch setup, ma_stack, vcp_contraction) are untouched, and the only inline "Proven" badge
  remains the leadership score — exactly as before.

- Internally, the referee records which strictness policy each verdict used (for the audit trail). On the
  default path this value is `"bonferroni"`, unchanged.

---

## Backend-Only Items

- **Online-FDR (LORD++) staging economy** (`app/engine/online_fdr.py` + the staging ledger) — a complete,
  tested statistical engine that is **never served to any endpoint and never displayed**. It exists to
  enable the future J-07 (multi-horizon) and J-08 (multi-factor combination) "proven" edges; those
  user-facing surfaces are explicitly out of scope for this iteration.

- **Per-claim ledger routing in the gate** — a claim can target the staging vs the canonical ledger; used
  by the automated pipeline, not by any user-facing screen.

---

## Incomplete Items

- **None for this iteration's scope.** iter-9 is deliberately *only* Part A (build the economy first).
  Opening the search wider (multi-horizon scans, multi-factor combinations, raising scan limits) and the
  user-facing J-07 / J-08 "proven" surfaces are the **next** iterations (iter-10, iter-11) and were
  correctly excluded here — doing them first would risk permanently tightening the real "Proven" bar.

---

## Config and Environment Changes

- `config.yaml` → `evidence.staging_ledger_path` — the location of the internal staging ledger.
  Default: `runs/goal-session-mcp-loop/state/staging-ledger.jsonl` (a NEW internal file; not yet created —
  a missing ledger is treated as empty, so the first staging claim starts clean).
- `config.yaml` → `evidence.fdr` — the online-FDR economy settings. Default: `enabled: false` (so
  everything stays strict Bonferroni), plus the LORD++ tunables (`alpha: 0.05`, `w0_fraction: 0.5`,
  `gamma_exponent: 1.6`, `gamma_terms: 1000`). A bad value here is a **loud config error**, never a silent
  weakening.
- `STAGING_LEDGER_PATH` — a new environment variable the goal-mode runner exports alongside the existing
  `LEDGER_PATH`, so the pre-build gate can route a claim to the staging ledger.
- No database migration, no schema change.

---

## Known Limitations

- The online-FDR economy is **off by default and fenced to staging**. This is intentional and load-bearing:
  false-discovery-rate control is statistically *weaker* than the family-wise (Bonferroni) guarantee the
  user-facing "Proven" badge relies on, so it must never touch the canonical ledger. The canonical bar
  stays strict Bonferroni even if someone turns the economy on.
- Because the staging ledger is never displayed, there is no UI to inspect it this iteration — that is by
  design (exploration is internal until a winner is deliberately promoted to canonical in a later iteration).
- Determinism and no-lookahead are preserved end to end (the new module is pure — no randomness, no clock,
  no I/O; the referee's sealed-holdout procedure on the default path is unchanged).
