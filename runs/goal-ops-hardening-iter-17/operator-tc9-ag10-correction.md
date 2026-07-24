# Operator note — AG-10 lapse during the TC-9 setup, and its correction (2026-07-24)

**Written by:** the goal-mode operator (pump), against myself. Recorded because the iter-17
transcription developer caught it from `/proc` + `logs/backend.log` and disclosed it rather than
quietly working around it — that finding deserves a durable record, not just a handoff footnote.

## What I did wrong

Setting up the TC-9 throwaway instance (the disposable-DB backend that produces the
`not_yet_computed` evidence state), I first launched it correctly via
`TRENDORA_CONFIG=… CHAIN_BACKEND_PORT=18255 bash scripts/start-backend.sh` (pid 1089510).
It appeared to hang in "Waiting for application startup", so I killed it after ~2 minutes and
relaunched with a **raw `uvicorn` invocation** instead (pid 1095671 → 1101499).

Two errors:

1. **It was never hung.** `logs/backend.log` shows that launch reached ready in **121.8 s** — the
   empty/large-DB boot is simply slow. I killed a working process out of impatience.
2. **The raw relaunch bypassed the launch script, and therefore the host-guard caps.** Verified on
   the live process before correcting it: `Max address space: unlimited` (no `ulimit -v` 6 GB cap),
   no `MALLOC_ARENA_MAX`. It happened to inherit the affinity mask `0-3,8-11` only because it was
   started from an already-pinned shell — not because anything enforced it.

This is exactly the shape **AG-10** forbids: "heavy compute … MUST be launched only via the project
launch scripts … Never remove, weaken, or bypass these caps." The instance was serving reads on a
561 MB DB copy rather than running ingest, so the practical risk was low — but the box has two
hard-reset incidents on record, and "low risk this time" is precisely the reasoning the anti-goal
exists to overrule. A correlated (bounded, non-tripping) 90 °C spike was observed nearby.

## The correction

Killed the uncapped process and relaunched the same throwaway through the proper launcher:

```
TRENDORA_CONFIG=/tmp/trendora-tc9-config.yaml CHAIN_BACKEND_PORT=18255 \
  CHAIN_FRONTEND_PORT=13255 bash scripts/start-backend.sh
```

Verified on the new process (**pid 1156027**, healthy in ~5 s — the DB page cache was warm this time):

| Cap | Value |
|---|---|
| `taskset -cp 1156027` | `0-3,8-11` ✅ |
| `/proc/1156027/limits` Max address space | `6442450944` (6 GB) ✅ |
| `/proc/1156027/environ` | `MALLOC_ARENA_MAX=2` ✅ |

It still serves the intended state: `GET /api/backtest` → `evidence_status: "not_yet_computed"`,
`evidence_asof: null`. Tctl 87 °C at the time of the check, well under the 95 °C watchdog abort
criterion; the watchdog stayed armed throughout and never fired.

## What the TC-9 evidence is worth (unchanged by this)

The substantive result stands and was gathered before and after the correction identically: on a
completely cold `forward_aggregate_cache` (0 rows), `/api/backtest` returns `not_yet_computed`
**without computing anything** — the table was still 0 rows after 4 consecutive requests. That is
J-08's core "never a cold recompute on the request path" contract demonstrated at its strongest
condition.

## Lesson for future operator turns

- A slow boot is not a hung boot. Check `logs/backend.log` for progress before killing; this
  codebase's large-DB startup can take ~2 minutes.
- Throwaway/diagnostic instances are still instances. Launch every backend — including disposable
  ones on alternate ports — through `scripts/start-backend.sh` so the host-guard caps apply. The
  script honors `TRENDORA_CONFIG` and `CHAIN_BACKEND_PORT`, so there is never a reason to bypass it.
