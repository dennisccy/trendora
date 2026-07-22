# Operator (pump) evidence — J-04 step 6 crash/interrupted-progress verification

**Produced by:** the goal-mode interactive pump (the human operator's session), not by an agent lane.
**Why it exists:** the round-3 auditor (`docs/handoffs/goal-ops-hardening-iter-9-audit.md`) stated that
J-04 step 6 was the single item standing between iter-9 and a PASS, that it could only be closed by a
real backend kill/restart cycle, and that the cycle had to run against a backend restarted **after** the
F1 checkpoint fix + the auditor's own B1 follow-up landed (the live process at that moment predated both).
The auditor explicitly asked the pump to perform the cycle. Agents in this pipeline cannot start or stop
services — the permission classifier blocks them — so the pump ran it and recorded the raw observations here.

## Sequence actually executed

| Step | Timestamp (BST) | Action / observation |
|---|---|---|
| 1 | 18:36:23 | Backend restarted from the current tree via `CHAIN_BACKEND_PORT=8255 CHAIN_FRONTEND_PORT=3255 bash scripts/start-backend.sh` → **pid 1870770**, `GET /api/health` 200. This process includes F1 (`_checkpoint_run_record`) and the auditor's B1 call site. |
| 2 | 18:36:5x | Started a multi-date backfill: `POST /api/data/jobs {"kind":"backfill","start":"2019-03-01","end":"2019-06-28"}` → `job_id c5f1a3781a7848dea5b6f432319cd063`, status `running`. |
| 3 | ~18:38:40 | Let it run ~90 s so checkpoints could land (throttle is one UPDATE per 10 s). Live job status at that moment: `snapshots_created 79`, `dates_done 84/84`, `forward_returns_inserted 182720`, chunk 2/2. |
| 4 | **18:38:43** | **`kill -9 1870770`** — hard crash, no shutdown hook, `_finalize_run_record()` never reached. Confirmed within 4 s: port 8255 no longer listening. |
| 5 | ~18:39:2x | Backend restarted the same way; `GET /api/health` → 200. |
| 6 | after restart | Read the run row back from the canonical endpoint `GET /api/data`. |

## Result — the row for the killed job (id 114)

```json
{"id": 114, "kind": "backfill", "start": "2019-03-01", "end": "2019-06-28",
 "status": "interrupted", "snapshots_created": 59, "dates_done": 64, "dates_total": 84,
 "calendar_days": 120, "non_trading_days": 36, "already_snapshotted": 5, "error_other": 0}
```

The row is marked `interrupted` **and carries the last checkpointed progress** — 59 snapshots, 64 of 84
dates, with the calendar breakdown preserved. The frozen values are lower than the live counters at the
instant of the kill (79 / 84), which is the expected behaviour of a 10 s-throttled checkpoint: it reports
the last durably persisted position, not an optimistic in-memory one.

## Contrast — the pre-fix control, same failure mode

Run id 113 is browser-QA's earlier killed job from this same iteration, produced by a backend running
pre-F1 code:

```json
{"id": 113, "kind": "backfill", "start": "2025-06-01", "end": "2026-07-17",
 "status": "interrupted", "snapshots_created": 0, "dates_done": 0, "dates_total": 0,
 "calendar_days": null, "non_trading_days": null, "already_snapshotted": null}
```

Same endpoint, same crash mechanism, all zeros/nulls — the exact defect the browser lane reported as the
J-04 step 6 failure. The two rows sit side by side in the same response, so the before/after is directly
comparable without trusting any narrative.

## Scope and honesty notes

- This is **API-level evidence from the canonical `GET /api/data` endpoint**, gathered by the operator. It
  is not a browser-lane pass: nobody re-drove the `/data` page UI after this cycle. The frontend already
  renders these fields (`apps/frontend/app/data/page.tsx:2612`, verified by the developer and reviewer),
  but the rendered surface was not re-observed after the fix.
- Treat this as the operator half of J-04 step 6 — sufficient to show the persisted data is now real,
  and to distinguish the fix working from the earlier stale-code false negative. Whether that is enough to
  score the journey `passing` is the goal-evaluator's call, not the pump's; the auditor's instruction was
  "do not let the evaluator flip J-04 to passing on the fix alone", and this file is offered as the
  missing runtime observation rather than as a substitute verdict.
- No product code, tests, or agent artifacts were modified by the pump. The only pump actions were service
  start/stop, one HTTP POST to start the backfill, and HTTP GETs to read state.
- Host conditions during the cycle: idle-band temperatures, 1 Hz host-guard sampler live, thermal watchdog
  armed; no trip, no reset.
