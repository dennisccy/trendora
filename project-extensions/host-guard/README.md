# host-guard — keep goal mode from hard-resetting this machine

## The incident (2026-07-20 / 2026-07-21)

The host — a **GEEKOM A7 Max mini-PC** (AMD Ryzen 9 7940HS, 16 threads, 27 GB RAM,
BIOS 1.26 2025-09-15) — hard-reset **instantly** twice while the `ops-hardening`
goal-mode session ran:

| Crash | Last evidence of life | Next kernel booting | What was running |
|---|---|---|---|
| Jul 20 19:17 | journal healthy at 19:17:01 | 19:19:52 | iter-5 measurement passes hammering `/api/backtest` (~1.5-1.7M rows × 5 horizons per request) |
| Jul 21 10:33 | `.pump-alive` mtime 10:33:18 | 10:33:47 (≈ POST time) | iter-8 developer: full-universe rebuild + second heavy backfill, VmPeak sampling |
| Jul 25 13:09 | hwmon.csv.1 row 13:09:21 — Tctl 78 °C, PPT 24 W, 17.5 G avail | 13:09:41 | goal sessions active; benign readings at T-0 |
| Jul 27 20:46 | hwmon.csv row 20:46:28 — Tctl 74 °C, PPT 34 W, 19.4 G avail | 20:46:48 | tapeology goal-desk iter-8 live (project had NO host-guard) |
| Jul 28 01:07 | hwmon.csv row 01:07:52 — Tctl 88 °C, PPT 29 W, 15.2 G avail, psi_mem 0.00 | 01:08:33 | BOTH engines mid-iteration (trendora iter-29 strong-tier full-rerun); unconfined interactive pumps |
| Jul 29 14:02 | tapeology hwmon.csv row 14:02:45 — Tctl 73-76 °C, PPT 18-32 W, 14.7 G avail, load 1.5 | 14:03:25 | BOTH engines mid-iteration under the NEW per-session caps (trendora iter-33 goal-evaluator; tapeology iter-19 browser-qa, 66 min in) — see "Why #6 happened anyway" |

No OOM-killer events, no thermal warnings, no panic (`kernel.panic=0` — a panic would
*hang*, never reboot), no watchdog armed (`RuntimeWatchdogUSec=0`), pstore empty.
**Software cannot instant-reset this machine** → power/VRM/thermal transient trip in
the mini-PC hardware. Crash #2 happened *despite* `start-backend.sh`'s `ulimit -v`
cap → not plain memory exhaustion. The same box previously survived 8 days of
sustained scalar pytest marathons — the killer is the **bursty all-core AVX
power-spike profile** of unrestricted-backfill/rebuild workloads, not sustained load.

**Incidents #3–#5 (2026-07-25/27/28)** reproduced the signature WITH 1 Hz forensics:
every reset struck at benign temperature, low package power, ample free RAM, and
zero memory pressure — confirming a millisecond-scale power transient that no
sampler can catch; only capping how many cores a burst can light works. Root
cause of the RECURRENCE despite this guard: (a) both goal sessions ran
`agent_backend: interactive`, and interactive-pump dispatches execute OUTSIDE
the engine self-wrap (children of the unconfined CLI session); (b) tapeology
had no host-guard at all. Fixed 2026-07-28: host-guard upstreamed into the
framework (fully generic), tapeology declares its own env with the complementary
mask `4-7,12-15`, pump confinement is machine-enforced AND self-healing
(`HOST_GUARD_REQUIRE_PUMP_CONFINED=1` — the engine auto-confines the running
CLI in place via `host-guard-adopt.sh`, no special launch needed;
`host-guard-exec.sh` remains the optional from-birth wrapper), a thermal
iteration gate waits out heat-soak between iterations, and CPU boost is
disabled host-wide (hardware ladder item 1 — see below for revert).

### Why #6 happened anyway (2026-07-29) — and what changed

Reset #6 struck with **every per-session control working as designed**. Three
holes, all of the same shape — *nothing could see more than one scope at a time*:

1. **The complementary masks were the bug, not the fix.** trendora held
   `0-3,8-11` and tapeology `4-7,12-15`. Each session's preflight, iteration
   gate, and doctor row were green. Their union is all 16 CPUs — every physical
   core available to a single burst, exactly the condition the mask was supposed
   to prevent. The 2026-07-28 entry below (and the framework docs) *recommended*
   this arrangement; that advice was wrong. Memory had the same shape: 14G + 14G
   declared against 27.3G installed, neither project ever wrong on its own.
2. **The QA browser could escape confinement.** Chrome-MCP reconnects to and
   adopts browsers it did not spawn, and its detached Chrome outlives it
   (reparented to init, out of reach of any descendant walk). A browser born
   before confinement kept an all-CPU mask indefinitely — and ran headed, paying
   for GPU compositing and a full raster pool. tapeology iter-19 was 66 minutes
   into browser-qa at T-0.
3. **The guard's own hardware premise had lapsed.** CPU boost was disabled live
   on 2026-07-28 as hardware ladder item 1, but `/etc/tmpfiles.d/cpufreq-boost.conf`
   was never actually installed, so the 2026-07-29 reboot silently re-enabled it.
   Nothing checked. The box ran all of 2026-07-29 with the mitigation off.

Fixed 2026-07-29 (framework, Stage E below): a **machine-global budget** in
`~/.config/iad/host-guard-host.env` that every session's mask must be a subset of
and every live session's union must fit inside, backed by a registry of live
guarded contexts (junior session pauses, senior continues); **both projects moved
onto the shared mask `0-3,8-11`** with `MemoryHigh` 10G each; a **browser
confinement pass** run before every QA dispatch and on both exits of
`host-guard-adopt.sh`; **engine-mode QA forced headless**; and a **boost check**
in preflight, the iteration gate, and a new `doctor.sh --only cpu-boost` row.
Framework docs: `incredible_auto_dev/docs/host-guard.md`; failure-mode entry:
`.claude/anti-patterns/26-per-scope-caps-no-machine-aggregate.md`.

Contract: `docs/goal.md` **AG-10** + the "Host-guard cap enforcement" binding note.

## Files

| File | Role |
|---|---|
| `host-guard.env` | Single source for every cap value (mask, threads, memory, sampler). Absent or `HOST_GUARD_ENABLED=0` ⇒ every hook no-ops. |
| `hwmon-log.sh` | Forwarder to the framework sampler (`scripts/automation/host-guard/hwmon-log.sh`, shared by all projects since 2026-07-28) — same CLI (`run|start|stop|status|watch`), same output: 1 Hz, fsync per line → `logs/hwmon/hwmon.csv` (+ `.csv.1` ring). |
| `README.md` | This file. |

Enforcement points (outside this directory):

- **`scripts/automation/run-goal.sh` self-wrap** (framework-generic since
  2026-07-28) — re-execs the whole engine under a `systemd-run --user` scope
  with `AllowedCPUs=$HOST_GUARD_CPU_LIST` (cgroup cpuset — inherited by every
  descendant, cannot be widened from inside) + CPUQuota/MemoryHigh/TasksMax,
  plus `taskset -c` belt-and-braces (also the fallback when no user bus).
  Confines every engine child in **headless** runs.
- **`scripts/automation/host-guard-adopt.sh`** (new 2026-07-28) — confines the
  ALREADY-RUNNING interactive pump in place: scope adoption (busctl
  StartTransientUnit + set-property) for the memory/task/quota ceilings, plus
  `taskset -a` across the whole tree for the hard CPU mask. No special launch
  command needed; invoked by `/goal` at session start and by the engine gate
  on an unconfined pump. This closes the gap that let resets #3–#5 happen.
- **`scripts/automation/host-guard-exec.sh`** (new 2026-07-28, optional) —
  from-birth wrapper: `host-guard-exec.sh claude` launches the CLI inside the
  scope AND sets the BLAS/OMP thread-cap env vars (not injectable into a live
  process). The fallback when in-place adoption fails.
- **`run-goal.sh` `preflight_host_guard`** — pauses the session
  (`AWAITING_HOST_GUARD`, resumable) if the sampler is dead and cannot be
  auto-started, the affinity wrap did not take effect, or (once
  `HOST_GUARD_REQUIRE_MARKERS=1`) a file in `HOST_GUARD_MARKER_FILES` lost its
  HOST-GUARD block.
- **`run-goal.sh` `host_guard_iteration_gate`** (new 2026-07-28, top of loop) —
  (a) thermal cooldown: waits between iterations while Tctl ≥ 90 °C until
  ≤ 80 °C (bounded 30 min, then proceeds loudly); (b) with
  `HOST_GUARD_REQUIRE_PUMP_CONFINED=1`, verifies the pump's `Cpus_allowed_list`
  (via the `pid=` line in `.pump-alive`, or the CLI root captured at engine
  launch), auto-confines it in place when too wide, and pauses only when that
  fails.
- **`scripts/dev.sh` / `scripts/start-backend.sh` cap blocks** — goal-mode work,
  next iteration (goal.md binding note): SMT-aware `taskset`, BLAS/OMP/numexpr
  thread caps, and (dev.sh backend subshell) `ulimit -v` + `MALLOC_ARENA_MAX`.
  Flip `HOST_GUARD_REQUIRE_MARKERS=1` in `host-guard.env` the moment they land.

## Daily use

```bash
bash project-extensions/host-guard/hwmon-log.sh status   # is forensics running?
bash project-extensions/host-guard/hwmon-log.sh watch    # live temps/power while testing
tail -2 logs/hwmon/hwmon.csv                             # after any reset: last pre-crash second
```

Idle baseline (2026-07-21, this box): Tctl 43-50 °C, GPU edge ~40 °C, PPT 9-31 W,
NVMe 39 °C, DIMMs 40-42 °C.

## Ladder status (update on every stage run)

| Stage | Status | When | Evidence |
|---|---|---|---|
| 0 | **GREEN** | 2026-07-21 ~21:35 | owner-run in the prior Claude session (mask, `ulimit -v`=6442450944, thread vars + `MALLOC_ARENA_MAX=2` confirmed on live PIDs) |
| A | **GREEN** | 2026-07-21 ~21:35 | `measure-perf.sh` warm passes, budgets green |
| B | **GREEN** | 2026-07-21 ~21:35 | 14.5 min back-to-back 2024 backfills: 116 snapshots + 310k fwd returns, maxTctl 88 °C (<95 abort), PPT ≤56 W, VmPeak 5.47 G of 6.29 G cap, health ≤3 s, **no reset**. NOTE: the sampler csv was recreated 22:04, so those rows now live only in that session's transcript, not `hwmon.csv`. |
| C | **IN PROGRESS** | 2026-07-21 22:47→ | supervised `/goal-step` (ops-hardening iter-8). Pump session pinned to `0-3,8-11` (children inherit), BLAS/OMP/MKL=4, 1 Hz sampler live, auto-kill watchdog armed at the abort criteria below. Owner explicitly authorized the live TC-1/TC-2 heavy-ingest measurement at 22:5x. Session peak so far: Tctl 88 °C / PPT 56 W / DIMM 48 °C / NVMe 43 °C. |
| D | **LANDED** | 2026-07-28 | After resets #3–#5: host-guard upstreamed to the framework (engine self-wrap now cpuset `AllowedCPUs` + taskset; preflight generic via `HOST_GUARD_MARKER_FILES`); pump confinement enforced AND self-healing (`HOST_GUARD_REQUIRE_PUMP_CONFINED=1`; in-place adoption via `host-guard-adopt.sh`, `host-guard-exec.sh` as optional from-birth wrapper); thermal iteration gate; tapeology guarded with complementary mask `4-7,12-15`; `MemoryHigh` 18G→14G per project (two engines fit in 27 G); CPU boost disabled host-wide + persisted (hardware ladder item 1). NOTE: cpuset is NOT delegated to user units on this host (`cpu memory pids` only) — `taskset` is the effective CPU mask everywhere; scope adoption still applies the memory/task/quota ceilings. Evidence: 17/17 sandboxed guard tests, 137/137 offline evals. NEXT: supervised Stage-B-shape re-verify under the new caps, then resume both sessions and run the 7-day zero-unclean-shutdown soak. **SUPERSEDED in part by Stage E: the complementary-mask advice in this row caused reset #6.** |
| E | **LANDED (framework)** | 2026-07-29 | After reset #6 (both projects confined, still unbounded together): machine-global aggregate budget (`~/.config/iad/host-guard-host.env`: `HOST_GUARD_GLOBAL_CPU_LIST="0-3,8-11"`, `_MEMORY_BUDGET="22G"`, `REQUIRE_BOOST_OFF=1`) enforced at preflight + every iteration gate against a live-session registry (`lib/host-guard-registry.sh`; register-before-verify, junior pauses on a total order, pid/starttime/boot-id staleness); both projects now share mask `0-3,8-11` with `MemoryHigh` 10G; QA-browser confinement pass (`host-guard/browser-confine.sh`) before every browser dispatch and on BOTH exits of `host-guard-adopt.sh`; engine-mode QA forced headless; boost verified read-only + two new doctor rows (`host-guard`, `cpu-boost`) + `mcp-affinity`. Evidence: 63/63 + 61/61 new sandboxed guard tests, full offline eval suite green. **OWNER ACTION OUTSTANDING: re-apply and PERSIST boost-off (the hardware ladder item that lapsed) — see "Boost persistence" in the framework docs; until then the engine pauses AWAITING_HOST_GUARD by design.** NEXT: subtree-pull both projects, supervised concurrent `/goal-step`, then the 7-day zero-unclean-shutdown soak. |

## Verification ladder (run before widening anything; user present, work saved)

Abort criteria at every stage: **Tctl ≥ 95 °C sustained 10 s, any DIMM ≥ 85 °C, or
NVMe ≥ 75 °C → kill the load, drop to the hardware ladder below.**

- **Stage 0** — start a backend via each launcher; on the live PID verify:
  `taskset -cp <pid>` = the mask; `/proc/<pid>/limits` address space = 6442450944;
  `NUM_THREADS` vars + `MALLOC_ARENA_MAX=2` in `/proc/<pid>/environ`.
- **Stage A** (crash #1 shape) — `scripts/measure-perf.sh` warm passes against the
  capped backend; expect budgets green, Tctl < 90 °C, bounded PPT.
- **Stage B** (crash #2 shape) — full-universe rebuild + immediate second heavy
  backfill in the same capped process. A `/api/health` hang here is the known
  iter-8 MemoryError livelock (product bug): restart the backend; still a
  stability PASS if no reset.
- **Stage C** — `/goal-step`: exactly one supervised goal iteration under caps.

Interpretation: reset at Tctl < 80 °C → not thermal → hardware ladder items 1-3;
reset again → hardware fault, RMA path. No reset but Tctl > 90 °C → items 1-2
before ever widening the mask. No reset + Tctl ≤ 85 °C → resume goal mode;
widen the mask ONE notch (`0-5,8-13`) only via this same ladder.

## Hardware ladder (manual, sudo/physical; only when routed here)

1. **Boost off (biggest software lever) — APPLIED PERMANENTLY 2026-07-28** (owner
   decision after resets #3–#5 proved the transient trip):
   `echo 0 | sudo tee /sys/devices/system/cpu/cpufreq/boost`, persisted across
   reboots by `/etc/tmpfiles.d/cpufreq-boost.conf` containing
   `w /sys/devices/system/cpu/cpufreq/boost - - - - 0`. Locks clocks near base
   (~20-30 % peak throughput cost; goal mode is mostly API-bound).
   **To revert:** `echo 1 | sudo tee /sys/devices/system/cpu/cpufreq/boost`
   (immediate) and `sudo rm /etc/tmpfiles.d/cpufreq-boost.conf` (stops
   re-applying at boot).
2. **BIOS:** check GEEKOM A7 Max support page for a BIOS newer than 1.26
   (2025-09-15); in setup choose the "Balanced"/"Quiet" performance profile
   (firmware-level PPT cap).
3. **memtest86+ overnight** — rules out DDR5/EXPO instability (two SODIMMs).
4. **GEEKOM support / RMA** if a capped workload still resets at low temperature —
   attach both incident timestamps + `logs/hwmon/hwmon.csv{,.1}` tails.

## Boot persistence (optional)

The sampler survives goal-mode restarts (the preflight auto-starts it) but not a
reboot by itself. For always-on forensics:

```bash
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/hwmon-log.service <<'EOF'
[Unit]
Description=host-guard hwmon 1Hz sampler
[Service]
ExecStart=/usr/bin/bash /home/dennis-chan/Git/trendora/project-extensions/host-guard/hwmon-log.sh run
Restart=always
[Install]
WantedBy=default.target
EOF
systemctl --user daemon-reload && systemctl --user enable --now hwmon-log
loginctl enable-linger   # keep it running when logged out
```

(Safe to combine since 2026-07-28: `start`/`status` now detect a fresh csv from
an external sampler and refuse to double-run, so the unit and the engine
preflight's auto-start coexist. Installed as the standing setup on this host
2026-07-28 — the sampler now survives reboots and runs even when no goal
session is active.)
