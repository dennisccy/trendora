"""Concurrent research-request load for TC-2 — a process that does NOTHING else.

TC-2's shape, verbatim from the spec: "the same drill as TC-1 but with a concurrent
`GET /research/factor-lab?all=true` or `GET /research/factor-combination` request issued mid-warm
(mirroring UT-08's own shape)". This process keeps ONE heavy research request outstanding at a time,
alternating the two endpoints back-to-back for the whole finalize tail — a user repeatedly loading
Factor Lab / Factor Combination while an ingest job runs.

One outstanding request at a time is deliberate: UT-08's finding (19/892) came from a single concurrent
CPU-bound Python compute contending with the ingest's own, not from a request flood. A flood would
measure connection queueing instead of the GIL contention TC-2 is about.

CSV columns: epoch_ms, endpoint, http_code (000 == no answer within the timeout), total_s, bytes
"""
import http.client
import socket
import sys
import time

base, out_path, duration_s = sys.argv[1], sys.argv[2], float(sys.argv[3])
host, port = base.split("://")[1].split(":")[0], int(base.rsplit(":", 1)[1])

ENDPOINTS = [
    "/api/research/factor-lab?all=true",
    "/api/research/factor-combination",
]
TIMEOUT = 600.0   # a cold heavy recompute legitimately takes minutes; never count it as a failure
GAP = 2.0         # brief pause between requests so this is a repeating page load, not a flood

end = time.time() + duration_s
i = 0
with open(out_path, "w", buffering=1) as fh:
    fh.write("epoch_ms,endpoint,http_code,total_s,bytes\n")
    while time.time() < end:
        path = ENDPOINTS[i % len(ENDPOINTS)]
        i += 1
        t0 = time.monotonic()
        epoch_ms = int(time.time() * 1000)
        code, nbytes = "000", 0
        conn = None
        try:
            conn = http.client.HTTPConnection(host, port, timeout=TIMEOUT)
            conn.request("GET", path)
            resp = conn.getresponse()
            body = resp.read()
            nbytes = len(body)
            code = str(resp.status)
        except (socket.timeout, TimeoutError, OSError, http.client.HTTPException) as exc:
            code = "000"
            nbytes = 0
            sys.stderr.write(f"{path}: {exc}\n")
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass
        fh.write(f"{epoch_ms},{path},{code},{time.monotonic() - t0:.3f},{nbytes}\n")
        time.sleep(GAP)
