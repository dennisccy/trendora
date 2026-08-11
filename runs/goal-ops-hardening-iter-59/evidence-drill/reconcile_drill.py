"""Deterministic drill reconciler — ops-hardening iter-59 fix pass (audit finding B1, DoD item 6).

Why this file exists. The iteration spec promoted the drill-reporting discipline from a reminder to a
BINDING DoD/TC line precisely because iters 57 and 58 kept losing failures inside hand-drawn window
boundaries — and the iter-59 audit found the same defect a third time in Addendum 25 (a false
"slowest answered poll" cell, a 3x-understated breach count, and phase windows derived by assuming the
finalize tail began when the job was POSTed while comparing BST log stamps to UTC poll epochs without
converting). The fix that actually holds is not a more careful human: it is to compute every published
figure from the raw artifacts, so no boundary can be chosen by hand at write-up time.

Everything below is derived, never asserted:
  * the measurement window comes from the job's OWN `ingest heavy-warm window OPEN/CLOSED` markers in
    logs/backend.log (TC-5's literal requirement — "read from the job's own markers, never hand-picked");
  * log stamps are naive local time, so they are converted to UTC through the host tz database
    (zoneinfo), never a hardcoded +1 — that hardcode is what broke Addendum 25;
  * the segmented table's row counts must sum to the data-row count, which must equal `wc -l` - 1;
    the script FAILS LOUDLY (non-zero exit) if either identity breaks, so a reconciliation error can
    never be silently published as a clean table;
  * the slowest ANSWERED poll is reported separately from the non-answers, because collapsing the two
    is what let Addendum 25 print "no answered poll exceeded a few hundred ms" over a 3.399s answer.

Usage: reconcile_drill.py <drill_out_dir> <job_id> [backend_log]
Writes <drill_out_dir>/reconciliation.md and prints it.
"""
import csv
import json
import os
import re
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

OUT = sys.argv[1]
JOB = sys.argv[2]
BACKEND_LOG = sys.argv[3] if len(sys.argv) > 3 else "/home/dennis-chan/Git/trendora/logs/backend.log"

HEALTH_CSV = os.path.join(OUT, "tc5-health-poll.csv")
LOAD_CSV = os.path.join(OUT, "tc3-regime-lab-poll.csv")
MEM_CSV = os.path.join(OUT, "tc4-vmpeak.csv")

RELAXED_CEILING_S = 2.0          # owner amendment 2026-07-31, bounded-background-compute window
MEMORY_CAP_MB = 8192             # config.yaml server.memory_cap_mb (AG-10; untouched this iteration)

LOG_TS = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\s")
LOCAL_TZ = ZoneInfo(open("/etc/timezone").read().strip()) if os.path.exists("/etc/timezone") else None


def log_stamp_to_utc(line):
    """Parse a backend.log stamp (naive LOCAL time) and return an aware UTC datetime."""
    m = LOG_TS.match(line)
    if not m:
        return None
    naive = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S,%f")
    return naive.replace(tzinfo=LOCAL_TZ).astimezone(timezone.utc)


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z" if dt else "n/a"


# ---------------------------------------------------------------------------------------------------
# 1. The measurement window + phase spans, read from the JOB'S OWN markers
# ---------------------------------------------------------------------------------------------------
open_dt = closed_dt = None
phases = []           # (phase_name, end_dt, elapsed_s)
with open(BACKEND_LOG, errors="replace") as fh:
    for line in fh:
        if JOB not in line:
            continue
        if "ingest heavy-warm window OPEN" in line:
            open_dt = log_stamp_to_utc(line)
        elif "ingest heavy-warm window CLOSED" in line:
            closed_dt = log_stamp_to_utc(line)
        else:
            m = re.search(r"finalize-tail phase timing: .*phase=(\S+) elapsed=([\d.]+)s", line)
            if m:
                phases.append((m.group(1), log_stamp_to_utc(line), float(m.group(2))))

# Phase spans are derived from each phase's own completion stamp and its own logged elapsed —
# never from "the job was POSTed at X so the tail must have started at X" (Addendum 25's error).
phase_spans = []
for name, end_dt, elapsed in phases:
    if end_dt is None:
        continue
    start_dt = end_dt - __import__("datetime").timedelta(seconds=elapsed)
    phase_spans.append((name, start_dt, end_dt, elapsed))


def attribute(dt):
    """Which of the job's OWN logged phases contains this instant? Never a hand-drawn bucket."""
    for name, s, e, _ in phase_spans:
        if s <= dt <= e:
            return name
    if open_dt and dt < open_dt:
        return "BEFORE heavy-warm window OPEN"
    if closed_dt and dt > closed_dt:
        return "AFTER heavy-warm window CLOSED"
    return "inside heavy-warm window, between logged phases"


# ---------------------------------------------------------------------------------------------------
# 2. The health poll log — every published figure derived here
# ---------------------------------------------------------------------------------------------------
with open(HEALTH_CSV) as fh:
    raw_lines = fh.read().splitlines()
wc_l = len(raw_lines)
rows = list(csv.DictReader(raw_lines))
assert len(rows) == wc_l - 1, f"reconciliation broken: {len(rows)} data rows vs wc -l {wc_l}"

for r in rows:
    r["dt"] = datetime.fromtimestamp(int(r["epoch_ms"]) / 1000, tz=timezone.utc)
    r["total_s"] = float(r["total_s"])

answered = [r for r in rows if r["http_code"] != "000"]
non_answers = [r for r in rows if r["http_code"] == "000"]
non_200 = [r for r in answered if r["http_code"] != "200"]
slowest = max(answered, key=lambda r: r["total_s"]) if answered else None
over_ceiling = [r for r in answered if r["total_s"] > RELAXED_CEILING_S]
over_1s = [r for r in answered if r["total_s"] > 1.0]
breaches = sorted(non_answers + over_ceiling, key=lambda r: r["dt"])

# Segmented table — boundaries are the job's own markers, so the segmentation cannot be tuned.
seg = {"pre-window (before OPEN)": [], "during window (OPEN..CLOSED)": [], "post-window (after CLOSED)": []}
for r in rows:
    if open_dt and r["dt"] < open_dt:
        seg["pre-window (before OPEN)"].append(r)
    elif closed_dt and r["dt"] > closed_dt:
        seg["post-window (after CLOSED)"].append(r)
    else:
        seg["during window (OPEN..CLOSED)"].append(r)
seg_total = sum(len(v) for v in seg.values())
assert seg_total == len(rows) == wc_l - 1, (
    f"segment reconciliation broken: {seg_total} != {len(rows)} != wc -l {wc_l} - 1")

# ---------------------------------------------------------------------------------------------------
# 3. TC-3 (regime-lab responses) and TC-4 (VmPeak time series)
# ---------------------------------------------------------------------------------------------------
load_rows = []
if os.path.exists(LOAD_CSV):
    with open(LOAD_CSV) as fh:
        for r in csv.DictReader(fh):
            r["dt"] = datetime.fromtimestamp(int(r["epoch_ms"]) / 1000, tz=timezone.utc)
            load_rows.append(r)

vmpeak_kb = 0
mem_samples = 0
if os.path.exists(MEM_CSV):
    with open(MEM_CSV) as fh:
        for r in csv.DictReader(fh):
            if r["vmpeak_kb"]:
                mem_samples += 1
                vmpeak_kb = max(vmpeak_kb, int(r["vmpeak_kb"]))

# ---------------------------------------------------------------------------------------------------
# 4. Emit
# ---------------------------------------------------------------------------------------------------
L = []
w = L.append
w(f"# Drill reconciliation — job `{JOB}`\n")
w("_Generated by `reconcile_drill.py`. Every figure below is derived from the raw artifacts named "
  "here; no window boundary, count or worst-case value is chosen by hand._\n")
w(f"- Host local timezone (for the BST->UTC conversion): `{LOCAL_TZ}`")
w(f"- `wc -l {os.path.basename(HEALTH_CSV)}` = **{wc_l}** ({wc_l - 1} data rows + 1 header)")
w(f"- Heavy-warm window OPEN (job's own marker): **{iso(open_dt)}**")
w(f"- Heavy-warm window CLOSED (job's own marker): **{iso(closed_dt)}**")
if open_dt and closed_dt:
    w(f"- Window duration: **{(closed_dt - open_dt).total_seconds():.2f}s**")
w("")

w("## TC-5 — health poll, whole log\n")
w("| Figure | Value |")
w("|---|---|")
w(f"| Poll span | {iso(rows[0]['dt'])} -> {iso(rows[-1]['dt'])} |")
w(f"| Total polls (data rows) | {len(rows)} |")
w(f"| HTTP 200 | {len(answered) - len(non_200)} |")
w(f"| Answered non-200 | {len(non_200)} |")
w(f"| Non-answers (`000`, 5.0s client ceiling) | **{len(non_answers)}** |")
if slowest:
    w(f"| **Slowest ANSWERED poll** | **{slowest['total_s']:.3f}s at {iso(slowest['dt'])}** "
      f"(HTTP {slowest['http_code']}; phase per the job's own markers: {attribute(slowest['dt'])}) |")
w(f"| Answered polls > {RELAXED_CEILING_S}s relaxed ceiling | {len(over_ceiling)} |")
w(f"| Answered polls > 1.0s | {len(over_1s)} |")
w(f"| **Total polls breaching the {RELAXED_CEILING_S}s ceiling** (non-answers + slow answers) | "
  f"**{len(breaches)} of {len(rows)}** |")
w("")

w("## TC-5 — segmented by the job's OWN OPEN/CLOSED markers (sum must equal the data-row count)\n")
w("| Segment | Polls | Non-answers | Answered >2s | Slowest answered |")
w("|---|---|---|---|---|")
for name, group in seg.items():
    g_ans = [r for r in group if r["http_code"] != "000"]
    g_slow = max(g_ans, key=lambda r: r["total_s"]) if g_ans else None
    g_slow_cell = f"{g_slow['total_s']:.3f}s at {iso(g_slow['dt'])}" if g_slow else "n/a"
    g_non = len([r for r in group if r["http_code"] == "000"])
    g_over = len([r for r in g_ans if r["total_s"] > RELAXED_CEILING_S])
    w(f"| {name} | {len(group)} | {g_non} | {g_over} | {g_slow_cell} |")
w(f"| **Reconciled sum** | **{seg_total}** (== data rows {len(rows)} == `wc -l` {wc_l} - 1) | | | |")
w("")

if breaches:
    w("## TC-5 — every breaching poll, attributed to the phase the JOB itself logged\n")
    w("| UTC timestamp | HTTP | elapsed | Phase (from the job's own markers) |")
    w("|---|---|---|---|")
    for r in breaches:
        elapsed_cell = ("no answer (client timeout)" if r["http_code"] == "000"
                        else f"{r['total_s']:.3f}s")
        w(f"| {iso(r['dt'])} | {r['http_code']} | {elapsed_cell} | {attribute(r['dt'])} |")
    w("")
else:
    w("## TC-5 — breaching polls\n\n**None.** Every poll answered inside the "
      f"{RELAXED_CEILING_S}s relaxed ceiling.\n")

w("## Phase spans, derived from each phase's OWN completion stamp and OWN logged elapsed\n")
w("| Phase | Start (UTC) | End (UTC) | Elapsed |")
w("|---|---|---|---|")
for name, s, e, elapsed in phase_spans:
    w(f"| `{name}` | {iso(s)} | {iso(e)} | {elapsed:.2f}s |")
w("")

w("## TC-3 — concurrent `GET /api/research/regime-lab` responses\n")
if load_rows:
    w("_`sent` is the request's own start instant and `answered` is `sent + elapsed`; a multi-minute cold "
      "compute spans several phases, so BOTH ends are attributed rather than filing the whole request "
      "under whatever phase happened to be running when it was issued._\n")
    codes_all = {}
    statuses_all = {}
    for r in load_rows:
        codes_all[r["http_code"]] = codes_all.get(r["http_code"], 0) + 1
        statuses_all[r["regime_lab_status"]] = statuses_all.get(r["regime_lab_status"], 0) + 1
    w(f"- Total responses: **{len(load_rows)}** · HTTP codes: "
      f"{', '.join(f'`{k}` x{v}' for k, v in sorted(codes_all.items()))} · `regime_lab_status`: "
      f"{', '.join(f'`{k}` x{v}' for k, v in sorted(statuses_all.items()))}")
    _lt = sorted((float(r['total_s']) for r in load_rows))
    w(f"- Elapsed: min {_lt[0]:.3f}s · median {_lt[len(_lt) // 2]:.3f}s · max {_lt[-1]:.3f}s")
    w("")
    # The full per-response series lives in the raw CSV; the table prints only the rows that carry
    # information a reader would otherwise have to take on trust — the cold computes and the extremes.
    _slowest = sorted(load_rows, key=lambda r: -float(r["total_s"]))[:6]
    _shown = {id(r) for r in _slowest} | {id(r) for r in load_rows[:2]} | {id(load_rows[-1])}
    shown_rows = [r for r in load_rows if id(r) in _shown]
    w(f"_Showing the first 2, the {len(_slowest)} slowest and the last of {len(load_rows)} responses; "
      f"the complete series is the raw CSV `{os.path.basename(LOAD_CSV)}`._\n")
    w("| sent (UTC) | answered (UTC) | HTTP | elapsed | bytes | `regime_lab_status` | Phase at send | Phase at answer |")
    w("|---|---|---|---|---|---|---|---|")
    for r in shown_rows:
        end_dt = r["dt"] + __import__("datetime").timedelta(seconds=float(r["total_s"]))
        w(f"| {iso(r['dt'])} | {iso(end_dt)} | {r['http_code']} | {float(r['total_s']):.3f}s | "
          f"{r['bytes']} | `{r['regime_lab_status']}` | {attribute(r['dt'])} | {attribute(end_dt)} |")
    codes = {r["http_code"] for r in load_rows}
    w("")
    w(f"- Distinct HTTP codes across ALL {len(load_rows)} responses: {sorted(codes)}; "
      f"any 5xx: **{'YES' if any(c.startswith('5') for c in codes) else 'NO'}**; "
      f"any non-answer: **{'YES' if '000' in codes else 'NO'}**")
else:
    w("_No regime-lab response rows captured._")
w("")

w("## TC-4 — VmPeak, maximum of a sampled time series (not a single opportunistic read)\n")
if mem_samples:
    w(f"- Samples with a live pid: **{mem_samples}**")
    w(f"- **VmPeak max: {vmpeak_kb:,} kB = {vmpeak_kb / 1024:.2f} MB**")
    w(f"- Declared `server.memory_cap_mb`: **{MEMORY_CAP_MB} MB** -> "
      f"**{vmpeak_kb / 1024 / MEMORY_CAP_MB * 100:.1f}% of cap, "
      f"{100 - vmpeak_kb / 1024 / MEMORY_CAP_MB * 100:.1f}% margin**")
else:
    w("_No memory samples captured._")
w("")

text = "\n".join(L) + "\n"
with open(os.path.join(OUT, "reconciliation.md"), "w") as fh:
    fh.write(text)
print(text)
print(json.dumps({
    "wc_l": wc_l, "data_rows": len(rows), "non_answers": len(non_answers),
    "slowest_answered_s": slowest["total_s"] if slowest else None,
    "slowest_answered_at": iso(slowest["dt"]) if slowest else None,
    "over_ceiling": len(over_ceiling), "breaches": len(breaches),
    "open": iso(open_dt), "closed": iso(closed_dt),
    "vmpeak_kb": vmpeak_kb, "regime_lab_responses": len(load_rows),
}, indent=1))
