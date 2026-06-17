#!/usr/bin/env python3
"""One-off, non-disruptive restoration of the full DAILY snapshot history.

Context: during iter-27 QA a full J-85 rebuild was triggered and then reverted; the backend
warm-up restored only the canonical cadence (~30 snapshots). This script ADDS back the missing
daily snapshots (and their forward returns incl. max_drawdown) WITHOUT clearing anything —
each `kind=backfill` job only computes dates that have no snapshot yet (idempotent). The latest
snapshot stays current throughout, so the site is usable while history fills in.

Runs the full price calendar in <=365-day chunks (max_range_days=370), one at a time, polling
each job to a terminal state before starting the next. Safe to re-run: already-present dates
are skipped.
"""
import json
import time
import urllib.request
import urllib.error
from datetime import date, timedelta

BASE = "http://localhost:8835"
CHUNK_DAYS = 360  # < max_range_days (370)
POLL_SECONDS = 30


def _get(path):
    with urllib.request.urlopen(BASE + path, timeout=30) as r:
        return json.loads(r.read().decode())


def _post(path, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(BASE + path, data=data, method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def log(msg):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)


def main():
    cov = _get("/api/data")["coverage"]
    start = date.fromisoformat(cov["price_start"])
    end = date.fromisoformat(cov["price_end"])
    log(f"price range {start} -> {end}; snapshot_count at start = {cov.get('snapshot_count')}")

    # Build <=CHUNK_DAYS windows over the full calendar.
    chunks = []
    cur = start
    while cur <= end:
        ce = min(cur + timedelta(days=CHUNK_DAYS - 1), end)
        chunks.append((cur, ce))
        cur = ce + timedelta(days=1)
    log(f"{len(chunks)} backfill chunks: " + ", ".join(f"{a}..{b}" for a, b in chunks))

    for i, (a, b) in enumerate(chunks, 1):
        log(f"--- chunk {i}/{len(chunks)}: backfill {a}..{b} ---")
        try:
            resp = _post("/api/data/jobs", {"kind": "backfill",
                                            "start": a.isoformat(), "end": b.isoformat()})
        except urllib.error.HTTPError as e:
            log(f"chunk {i} POST failed HTTP {e.code}: {e.read().decode()[:300]} — skipping")
            continue
        jid = resp.get("job_id")
        log(f"chunk {i} started job {jid} status={resp.get('status')}")
        # poll to terminal
        last = None
        while True:
            time.sleep(POLL_SECONDS)
            try:
                st = _get(f"/api/data/jobs/{jid}")
            except Exception as e:
                log(f"  poll error: {e}")
                continue
            status = st.get("status")
            prog = f"dates {st.get('dates_done')}/{st.get('dates_total')} snaps+{st.get('snapshots_created')} fr+{st.get('forward_returns_inserted')}"
            if prog != last:
                log(f"  {status}: {prog}")
                last = prog
            if status not in ("running", "queued", "pending", ""):
                log(f"chunk {i} terminal: status={status} msg={(st.get('message') or '')[:200]}")
                break
        cov2 = _get("/api/data")["coverage"]
        log(f"chunk {i} done; snapshot_count now = {cov2.get('snapshot_count')}")

    cov3 = _get("/api/data")["coverage"]
    log(f"RESTORE COMPLETE. final snapshot_count = {cov3.get('snapshot_count')} (trading_day_count={cov3.get('trading_day_count')})")


if __name__ == "__main__":
    main()
