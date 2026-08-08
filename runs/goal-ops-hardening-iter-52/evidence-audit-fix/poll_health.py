"""Dedicated /api/health poller — a process that does NOTHING else.

Addendum 12 polled from a thread inside a busy Python process, so a "no answer" could not be
distinguished from the CLIENT thread itself being starved. This process runs one poll loop and
nothing else: one socket per poll, 5.0s client timeout (the SAME failure class Addendum 11/12
counted as `curl code=000`), and it records the connect/first-byte split so a slow SERVER is
distinguishable from a slow client.

CSV columns: epoch_ms, http_code (000 == no answer within the timeout), total_s, connect_s, ttfb_s
"""
import http.client
import socket
import sys
import time
from urllib.parse import urlparse

url, out_path, duration_s = sys.argv[1], sys.argv[2], float(sys.argv[3])
u = urlparse(url)
host, port, path = u.hostname, u.port or 80, u.path or "/"
TIMEOUT = 5.0
PERIOD = 1.0

end = time.time() + duration_s
with open(out_path, "w", buffering=1) as fh:
    fh.write("epoch_ms,http_code,total_s,connect_s,ttfb_s\n")
    while time.time() < end:
        t0 = time.monotonic()
        epoch_ms = int(time.time() * 1000)
        code, connect_s, ttfb_s = "000", 0.0, 0.0
        conn = None
        try:
            conn = http.client.HTTPConnection(host, port, timeout=TIMEOUT)
            conn.connect()
            connect_s = time.monotonic() - t0
            conn.request("GET", path)
            resp = conn.getresponse()
            ttfb_s = time.monotonic() - t0
            resp.read()
            code = str(resp.status)
        except (socket.timeout, TimeoutError, OSError, http.client.HTTPException):
            code = "000"
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass
        total_s = time.monotonic() - t0
        fh.write(f"{epoch_ms},{code},{total_s:.3f},{connect_s:.3f},{ttfb_s:.3f}\n")
        rest = PERIOD - (time.monotonic() - t0)
        if rest > 0:
            time.sleep(rest)
