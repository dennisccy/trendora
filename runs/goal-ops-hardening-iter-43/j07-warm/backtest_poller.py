"""ops-hardening iter-39 FIX PASS (TC-3, audit finding B5) -- a 1 Hz `GET /api/backtest?as_of=<date>`
poller that records each request's START and END epoch, so "a previously-cached read was IN FLIGHT across
the MemoryError abort instant" becomes a checkable interval containment rather than a prose claim.

iter-39's first pass could only report "before + after, plus a concurrent health poll spanning the
instant" (audit B5: "the evidence is strong but does not literally satisfy TC-3's wording"). With the
abort now injected deterministically, its log line carries a precise timestamp, so a request whose
[start, end] interval CONTAINS that timestamp literally satisfies TC-3.

Usage: <venv python> backtest_poller.py <port> <as_of> <out_jsonl> <stop_file> [interval_seconds]
Runs until <stop_file> exists. One JSONL record per request: start/end epoch, HTTP status, byte length.

`interval_seconds` defaults to 1.0 (the 1 Hz cadence TC-2's health poll uses). Pass 0.0 for BACK-TO-BACK
requests: with no sleep between them the poller's in-flight intervals tile the whole drill window, so
"a previously-cached read was in flight AT the abort instant" is guaranteed rather than left to a
1 s sampling gap (the first fix-pass run missed containment by 74 ms — see run-1's artifacts).
"""
import json
import sys
import time
import urllib.request
from pathlib import Path

PORT, AS_OF, OUT, STOP = sys.argv[1], sys.argv[2], Path(sys.argv[3]), Path(sys.argv[4])
INTERVAL = float(sys.argv[5]) if len(sys.argv) > 5 else 1.0
URL = f"http://127.0.0.1:{PORT}/api/backtest?as_of={AS_OF}"

n_ok = n_bad = 0
with OUT.open("w") as fh:
    while not STOP.exists():
        t0 = time.time()
        try:
            with urllib.request.urlopen(URL, timeout=30) as resp:
                body = resp.read()
                status, nbytes, err = resp.status, len(body), None
        except Exception as exc:  # noqa: BLE001 -- record the miss, keep polling
            status, nbytes, err = 0, 0, str(exc)
        t1 = time.time()
        n_ok += status == 200
        n_bad += status != 200
        fh.write(json.dumps({
            "start_epoch": round(t0, 3), "end_epoch": round(t1, 3),
            "start_utc": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(t0)) + f".{int(t0 % 1 * 1000):03d}Z",
            "end_utc": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(t1)) + f".{int(t1 % 1 * 1000):03d}Z",
            "http_status": status, "bytes": nbytes, "error": err,
        }) + "\n")
        fh.flush()
        if INTERVAL:
            time.sleep(INTERVAL)

print(f"BACKTEST_POLLS_200={n_ok} BACKTEST_POLLS_NON200={n_bad}")
