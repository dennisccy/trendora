"""Corrected join: pre_receive_gap must be >= 0 (server clock == client clock, same host) -- for each
poll, pick the EARLIEST handler_compute (with sub-spans) entry whose t_received_wall is AT OR AFTER the
poll's own send timestamp, within a bounded window. This avoids nearest-neighbor mismatches caused by an
independent third-party caller (the goal-mode orchestrator's own pipeline health-checks, confirmed
concurrently polling the SAME backend during this drill, `goal-iter-lean.sh` PID 1312367) sometimes
landing closer in raw time than this poll's own true, later-arriving match.
"""
import csv
import json
from datetime import datetime, timezone

REPO = "/home/dennis-chan/Git/trendora"
SLICE = f"{REPO}/runs/goal-ops-hardening-iter-69/evidence-drill/health-watchdog-slice.jsonl"
TC1_CSV = f"{REPO}/runs/goal-ops-hardening-iter-69/evidence-drill/tc1-health-poll.csv"
TC3_CSV = f"{REPO}/runs/goal-ops-hardening-iter-69/evidence-drill/tc3-idle-poll.csv"


def parse_ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


entries = [json.loads(l) for l in open(SLICE) if l.strip()]
hc = [e for e in entries if e.get("type") == "handler_compute" and "db_reads_s" in e]
qw_by_ts = {e["timestamp"]: e["queue_wait_s"] for e in entries if e.get("type") == "queue_wait"}
hc.sort(key=lambda e: e["timestamp"])
hc_dt = [(parse_ts(e["timestamp"]), e) for e in hc]


def earliest_after(send_dt, max_wait=6.0):
    """The FIRST hc entry with t_received >= send_dt (gap >= 0), within max_wait seconds. Falls back to
    the nearest entry (any sign) only if nothing qualifies (keeps every poll matched -- TC-1's 'no
    missing sample' -- but flags the fallback so it can be reported honestly)."""
    best = None
    for t, e in hc_dt:
        gap = (t - send_dt).total_seconds()
        if 0 <= gap <= max_wait:
            if best is None or gap < best[0]:
                best = (gap, e)
    if best is not None:
        return best[1], best[0], False
    # fallback: nearest by absolute distance (should be rare/never)
    nearest = min(hc_dt, key=lambda te: abs((te[0] - send_dt).total_seconds()))
    gap = (nearest[0] - send_dt).total_seconds()
    return nearest[1], gap, True


def load_csv(path):
    return list(csv.DictReader(open(path)))


def full_join(rows, label):
    results = []
    fallback_count = 0
    for r in rows:
        send_ts = parse_ts(r["timestamp"])
        entry, gap, is_fallback = earliest_after(send_ts)
        if is_fallback:
            fallback_count += 1
        t_received = parse_ts(entry["timestamp"])
        pre_receive = (t_received - send_ts).total_seconds()
        qw = qw_by_ts.get(entry["timestamp"])
        elapsed = float(r["elapsed_s"])
        db_reads = entry["db_reads_s"]
        readiness = entry["readiness_s"]
        preflight = entry["preflight_s"]
        named_sum = pre_receive + qw + db_reads + readiness + preflight
        residual = elapsed - named_sum
        results.append({
            "poll_ts": r["timestamp"], "http_status": r["http_status"], "elapsed_s": elapsed,
            "matched_hc_ts": entry["timestamp"],
            "pre_receive_gap_s": round(pre_receive, 6), "queue_wait_s": round(qw, 6),
            "db_reads_s": round(db_reads, 6), "readiness_s": round(readiness, 6),
            "preflight_s": round(preflight, 6),
            "named_sum_s": round(named_sum, 6), "residual_s": round(residual, 6),
            "residual_pct": round(100 * residual / elapsed, 2) if elapsed else None,
            "is_breach": r["breach_over_2s"] == "1",
        })
    print(f"{label}: fallback (no gap>=0 match found) count: {fallback_count}/{len(rows)}")
    negatives = [r for r in results if r["pre_receive_gap_s"] < -0.001]
    print(f"{label}: rows with negative pre_receive_gap after fix: {len(negatives)}")
    return results


def pct(sorted_vals, p):
    if not sorted_vals:
        return None
    idx = min(int(len(sorted_vals) * p), len(sorted_vals) - 1)
    return sorted_vals[idx]


def summarize(vals):
    vals = sorted(vals)
    return {"p50": pct(vals, .5), "p90": pct(vals, .9), "p99": pct(vals, .99),
            "max": vals[-1] if vals else None, "min": vals[0] if vals else None, "n": len(vals)}


tc1_rows = load_csv(TC1_CSV)
tc3_rows = load_csv(TC3_CSV)
tc1_results = full_join(tc1_rows, "TC-1")
tc3_results = full_join(tc3_rows, "TC-3")

for label, results in [("TC-1", tc1_results), ("TC-3", tc3_results)]:
    print(f"\n=== {label} distributions (corrected join) ===")
    for field in ["pre_receive_gap_s", "queue_wait_s", "db_reads_s", "readiness_s", "preflight_s"]:
        vals = [r[field] for r in results]
        print(f"  {field}: {summarize(vals)}")
    breaches = [r for r in results if r["is_breach"]]
    print(f"  breaches: {len(breaches)}")
    if breaches:
        answered = [b for b in breaches if b["http_status"] != "0"]
        timeouts = [b for b in breaches if b["http_status"] == "0"]
        print(f"  answered breaches: {len(answered)}  timeouts: {len(timeouts)}")
        if answered:
            pcts = sorted(b["residual_pct"] for b in answered)
            print(f"  answered residual_pct: min={pcts[0]:.2f} p50={pct(pcts,.5):.2f} p90={pct(pcts,.9):.2f} max={pcts[-1]:.2f} mean={sum(pcts)/len(pcts):.2f}")
            dom = {"pre_receive_gap_s": 0, "queue_wait_s": 0, "db_reads_s": 0, "readiness_s": 0, "preflight_s": 0}
            for b in answered:
                shares = {k: b[k] for k in dom}
                dom[max(shares, key=shares.get)] += 1
            print(f"  dominant-component tally: {dom}")
            mean_shares = {k: sum(b[k] for b in answered) / len(answered) / (sum(b['elapsed_s'] for b in answered) / len(answered)) for k in dom}
            print(f"  mean share of elapsed_s per component (avg of components / avg elapsed): {mean_shares}")

json.dump(tc1_results, open(f"{REPO}/runs/goal-ops-hardening-iter-69/evidence-drill/tc1-full-join-fixed.json", "w"), indent=2)
json.dump(tc3_results, open(f"{REPO}/runs/goal-ops-hardening-iter-69/evidence-drill/tc3-full-join-fixed.json", "w"), indent=2)
json.dump([r for r in tc1_results if r["is_breach"]], open(f"{REPO}/runs/goal-ops-hardening-iter-69/evidence-drill/tc1-breaches-fixed.json", "w"), indent=2)

# print full breach table for TC-1
print("\n=== full TC-1 breach table (corrected) ===")
for b in tc1_results:
    if b["is_breach"]:
        print(json.dumps(b))
