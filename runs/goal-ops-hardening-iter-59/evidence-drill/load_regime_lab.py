"""Concurrent Regime-Lab request load for TC-3/TC-4/TC-5 (ops-hardening iter-59) -- a process that does
NOTHING else. Adapted from iter-54/55's `load_research.py` (which alternated Factor Lab / Factor
Combination); this iteration's target read is `GET /api/research/regime-lab` -- the confirmed iter-58 crash
frame (`_regime_lab_members_by_horizon`) sits behind this endpoint.

One outstanding request at a time is deliberate (same reasoning as the Factor Lab drill this mirrors): a
single concurrent CPU-bound Python compute contending with the ingest's own is the scenario under test, not
connection-queueing from a request flood.

CSV columns: epoch_ms, endpoint, http_code (000 == no answer within the timeout), total_s, bytes,
regime_lab_status (parsed from the JSON body's `regime_lab_status` field when present and the response was
JSON -- "absent" on a clean 200, "unavailable" on a degraded 200, "parse_error:<msg>" if the body was not
valid JSON, "n/a" on non-200).
"""
import http.client
import json
import socket
import sys
import time

base, out_path, duration_s = sys.argv[1], sys.argv[2], float(sys.argv[3])
host, port = base.split("://")[1].split(":")[0], int(base.rsplit(":", 1)[1])

PATH = "/api/research/regime-lab?view=pooled"
TIMEOUT = 600.0   # a cold heavy recompute legitimately takes minutes; never count it as a failure
GAP = 2.0         # brief pause between requests so this is a repeating page load, not a flood

end = time.time() + duration_s
with open(out_path, "w", buffering=1) as fh:
    fh.write("epoch_ms,endpoint,http_code,total_s,bytes,regime_lab_status\n")
    while time.time() < end:
        t0 = time.monotonic()
        epoch_ms = int(time.time() * 1000)
        code, nbytes, rl_status = "000", 0, "n/a"
        conn = None
        try:
            conn = http.client.HTTPConnection(host, port, timeout=TIMEOUT)
            conn.request("GET", PATH)
            resp = conn.getresponse()
            body = resp.read()
            nbytes = len(body)
            code = str(resp.status)
            if code == "200":
                try:
                    parsed = json.loads(body)
                    rl_status = parsed.get("regime_lab_status", "absent")
                except Exception as exc:  # noqa: BLE001 -- disclose, never hide a parse failure
                    rl_status = f"parse_error:{exc}"
        except (socket.timeout, TimeoutError, OSError, http.client.HTTPException) as exc:
            code = "000"
            nbytes = 0
            sys.stderr.write(f"{PATH}: {exc}\n")
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass
        fh.write(f"{epoch_ms},{PATH},{code},{time.monotonic() - t0:.3f},{nbytes},{rl_status}\n")
        time.sleep(GAP)
