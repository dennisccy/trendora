#!/usr/bin/env python3
"""vmpeak_sampler.py -- iter-32 J-09 raw evidence capture.

Samples /proc/<pid>/status (VmPeak/VmSize/VmRSS) for a target PID at a fixed interval,
alongside GET /api/health readiness, and appends one CSV row per sample. Never overwrites
prior rows (append mode) -- this file IS the durable raw evidence iter-25's figure lacked.

Usage: python3 vmpeak_sampler.py <pid> <health_url> <csv_path> <interval_s> <duration_s> [label]
Runs for exactly duration_s seconds (or until the target process exits), then exits 0.
"""
import csv
import datetime
import os
import sys
import time
import urllib.request

def read_status(pid):
    path = f"/proc/{pid}/status"
    vals = {"VmPeak": "", "VmSize": "", "VmRSS": ""}
    try:
        with open(path) as fh:
            for line in fh:
                for key in vals:
                    if line.startswith(key + ":"):
                        vals[key] = line.split()[1]  # kB value
    except FileNotFoundError:
        return None
    return vals

def read_readiness(url):
    try:
        with urllib.request.urlopen(url, timeout=3) as resp:
            import json
            body = json.load(resp)
            return body.get("readiness", "")
    except Exception as exc:
        return f"ERR:{exc.__class__.__name__}"

def main():
    pid = int(sys.argv[1])
    health_url = sys.argv[2]
    csv_path = sys.argv[3]
    interval_s = float(sys.argv[4])
    duration_s = float(sys.argv[5])
    label = sys.argv[6] if len(sys.argv) > 6 else ""

    new_file = not os.path.exists(csv_path)
    start = time.time()
    with open(csv_path, "a", newline="") as fh:
        writer = csv.writer(fh)
        if new_file:
            writer.writerow(["iso_utc", "elapsed_s", "label", "pid", "VmPeak_kB", "VmSize_kB", "VmRSS_kB", "readiness"])
        while True:
            now = time.time()
            elapsed = now - start
            if elapsed > duration_s:
                break
            status = read_status(pid)
            if status is None:
                writer.writerow([datetime.datetime.now(datetime.timezone.utc).isoformat(), f"{elapsed:.2f}", label, pid, "PROC_EXITED", "", "", ""])
                fh.flush()
                break
            readiness = read_readiness(health_url)
            writer.writerow([
                datetime.datetime.now(datetime.timezone.utc).isoformat(),
                f"{elapsed:.2f}", label, pid,
                status["VmPeak"], status["VmSize"], status["VmRSS"], readiness,
            ])
            fh.flush()
            time.sleep(interval_s)

if __name__ == "__main__":
    main()
