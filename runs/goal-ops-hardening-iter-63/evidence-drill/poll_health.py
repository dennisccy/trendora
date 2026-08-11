"""1 Hz GET /api/health poller -- writes epoch_ms,total_s,http_code to tc5-health-poll.csv, mirroring
iter-53/54/57/58/59/61's own drill format (reused verbatim by reconcile_drill.py). 5.0s client timeout
distinguishes a slow SERVER answer from a starved client (http_code=000 on timeout/connection error).
Runs until the sibling file STOP_FILE appears.
"""
import csv
import os
import sys
import time
import urllib.request
import urllib.error

URL = "http://localhost:8255/api/health"
OUT = sys.argv[1] if len(sys.argv) > 1 else "tc5-health-poll.csv"
STOP_FILE = sys.argv[2] if len(sys.argv) > 2 else "STOP"

with open(OUT, "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["epoch_ms", "total_s", "http_code"])
    fh.flush()
    while not os.path.exists(STOP_FILE):
        t0 = time.monotonic()
        epoch_ms = int(time.time() * 1000)
        code = "000"
        try:
            req = urllib.request.Request(URL, method="GET")
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                code = str(resp.status)
                resp.read()
        except urllib.error.HTTPError as e:
            code = str(e.code)
        except Exception:
            code = "000"
        total_s = time.monotonic() - t0
        w.writerow([epoch_ms, f"{total_s:.3f}", code])
        fh.flush()
        # 1 Hz cadence measured from poll START to next poll START, floor 0 (never negative sleep).
        remaining = 1.0 - total_s
        if remaining > 0:
            time.sleep(remaining)
