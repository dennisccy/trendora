"""Analyse a drill's health-poll CSV and attribute every slow/unanswered poll to a finalize-tail phase.

Phase windows are reconstructed from the backend log's own `J-05 finalize-tail (sub-)phase timing`
lines: each is emitted at the phase's END and carries `elapsed=`, so [end - elapsed, end] is the
window. Attribution is by ANCHOR timestamp, never by nearest-preceding-line (iter-51's binding lesson:
uvicorn access lines carry no timestamp of their own).

Usage: analyze.py <drill_out_dir> [backend_log]
"""
import csv, json, os, re, sys
from datetime import datetime

OUT = sys.argv[1]
LOG = sys.argv[2] if len(sys.argv) > 2 else "/home/dennis-chan/Git/trendora/logs/backend.log"

summary = json.load(open(os.path.join(OUT, "summary.json")))
job_started = summary["job_started_epoch"]
JOB = summary["job_id"]

rows = list(csv.DictReader(open(os.path.join(OUT, "health-polls.csv"))))
tot = len(rows)
non = [r for r in rows if r["http_code"] == "000"]
ok = [r for r in rows if r["http_code"] == "200"]
other = [r for r in rows if r["http_code"] not in ("000", "200")]
lat = sorted(float(r["total_s"]) for r in ok)


def pct(p):
    return lat[min(len(lat) - 1, int(p * len(lat)))] if lat else 0.0


print("=" * 96)
print(f"job              : {JOB}  target={summary['target']}  status={summary['status']}")
print(f"job wall-clock   : {summary['job_seconds']}s")
print(f"process          : {summary['vmpeak']}")
print(f"health polls     : {tot}   (HTTP 200: {len(ok)}, non-200: {len(other)} "
      f"{sorted({r['http_code'] for r in other})})")
print(f"NON-ANSWERS      : {len(non)}   <-- TC-1 (client 5.0s timeout, the `curl code=000` class)")
if lat:
    print(f"latency (200s)   : min {lat[0]:.3f} / median {pct(0.5):.3f} / p90 {pct(0.90):.3f} / "
          f"p99 {pct(0.99):.3f} / max {lat[-1]:.3f}  (seconds)")
    print(f"polls > 2.0s     : {sum(1 for v in lat if v > 2.0)} / {len(ok)}   <-- TC-3 ceiling")
    print(f"polls > 1.0s     : {sum(1 for v in lat if v > 1.0)} / {len(ok)}")
    print(f"polls > 0.5s     : {sum(1 for v in lat if v > 0.5)} / {len(ok)}")

# ---- phase windows from the backend log ---------------------------------------------------------
ts_re = re.compile(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d),(\d\d\d) ")
ph_re = re.compile(r"finalize-tail (sub-)?phase timing: job=(\w+) phase=(\S+)"
                   r"(?: (?:horizon|claim)=(\S+))?.*?elapsed=([0-9.]+)s")
windows = []
with open(LOG, errors="replace") as fh:
    for line in fh:
        m_ts, m_ph = ts_re.match(line), ph_re.search(line)
        if not (m_ts and m_ph) or m_ph.group(2) != JOB:
            continue
        end = datetime.strptime(m_ts.group(1), "%Y-%m-%d %H:%M:%S").timestamp() + int(m_ts.group(2)) / 1000
        elapsed = float(m_ph.group(5))
        is_sub = bool(m_ph.group(1))
        name = m_ph.group(3) + (f"[{m_ph.group(4)}]" if m_ph.group(4) else "")
        windows.append((end - elapsed, end, name, elapsed, is_sub))
windows.sort()

print("\n--- finalize-tail phases (from logs/backend.log, this job) ---")
total = 0.0
for lo, hi, name, el, is_sub in windows:
    marker = ""
    if not is_sub:
        total += el
        marker = "  *counted in tail total"
    print(f"  {'  sub ' if is_sub else 'PHASE '}t+{lo - job_started:8.1f}s .. t+{hi - job_started:8.1f}s  "
          f"{name:<45} {el:9.2f}s{marker}")
print(f"\n  finalize-tail TOTAL (top-level phases): {total:.2f}s   vs the 1,200s budget "
      f"-> {'WITHIN' if total <= 1200 else f'OVER by {total - 1200:.2f}s'}")


def attribute(epoch):
    hits = [n for lo, hi, n, _, is_sub in windows if lo <= epoch <= hi and not is_sub]
    return hits[-1] if hits else "(outside any timed finalize-tail phase)"


if non:
    print(f"\n--- where the {len(non)} non-answers fall ---")
    counts = {}
    for r in non:
        t = int(r["epoch_ms"]) / 1000
        where = attribute(t)
        counts[where] = counts.get(where, 0) + 1
        print(f"  t+{t - job_started:8.1f}s   {where}")
    print("  totals:", counts)
else:
    print("\n--- ZERO non-answers (TC-1 met on this drill) ---")

slow = [r for r in ok if float(r["total_s"]) > 2.0]
if slow:
    print(f"\n--- where the {len(slow)} polls > 2.0s fall (TC-3) ---")
    counts = {}
    for r in slow:
        where = attribute(int(r["epoch_ms"]) / 1000)
        counts[where] = counts.get(where, 0) + 1
    for k, v in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"  {v:4d}  {k}")
print("=" * 96)
