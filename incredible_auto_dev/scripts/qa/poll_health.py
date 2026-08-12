"""Canonical GET /api/health 1 Hz poller (ops-hardening iter-66, J-07, TC-4/TC-5).

The SINGLE, checked-in health-poll drill script this session's dev evidence-drills AND its J-07
browser-qa test case both run through -- no more per-iteration throwaway copies
(runs/goal-ops-hardening-iter-N/evidence-drill/poll_health.py, iter-53 through iter-65, each a byte-for-
byte-similar re-copy) and no more ad hoc curl/bash subprocess-per-poll loops (the browser-qa lane's own
supplementary drills, iter-65's Addendum 31: "this agent's own ad hoc bash/curl loop, not `poll_health.py`"
-- disagreed with the dev-side counter by ~40x on the same window, 8/240 vs 1/1057, because a
subprocess-per-poll (`date` + `python3`/`curl` forked each second) pays real fork/exec overhead under CPU
contention that a single long-lived HTTP client never does).

Single `urllib` client, ONE poll per second, no subprocess spawned per poll. Runs until the sibling
`STOP_FILE` appears (mirrors the prior per-iteration scripts' own stop-file convention, e.g.
runs/goal-ops-hardening-iter-65/evidence-drill/poll_health.py) OR, when `--count N` is given, for exactly
N polls then exits (useful for a bounded unit-testable/scripted run).

CSV schema (TC-4, byte-for-byte, shared by every caller -- the dev evidence-drill AND the J-07 browser-qa
test case cite the SAME column names so their raw CSVs are directly comparable):

    timestamp, http_status, elapsed_s, breach_over_2s, load_avg_1m

  - timestamp       -- ISO-8601 UTC, the poll's OWN start instant (`datetime.now(timezone.utc)`).
  - http_status      -- the response status code, or 0 on a timeout/connection error (never fabricated).
  - elapsed_s        -- wall-clock seconds for this ONE poll (three decimal places).
  - breach_over_2s   -- "1" iff `elapsed_s > HEALTH_CEILING_S` (the owner-amended relaxed ceiling during a
                        bounded background-compute window, docs/goal.md's "Additional binding notes"),
                        else "0" -- pre-computed here so a downstream reconciliation never re-derives the
                        threshold from a magic number of its own.
  - load_avg_1m      -- `os.getloadavg()[0]` (the 1-minute load average) sampled at the SAME instant as the
                        poll (TC-5: always populated/non-null on Linux -- `os.getloadavg` is unavailable
                        only on Windows, where this project does not run in CI/dev per project-template.md).

`os.cpu_count()` (the IN SCOPE ask's other host-load figure) is a HOST CONSTANT for the whole run, not a
per-poll observation -- recording it as a 6th per-row column would repeat the same integer on every line
for no benefit and would break the TC-4/TC-5 fixed 5-column schema those tests assert against. It is
instead written ONCE, alongside the run's own poll count and URL, to a sibling `<OUT>.meta.json` file next
to the CSV -- satisfying "record... os.cpu_count()" without duplicating a constant onto every row.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Optional

HEALTH_CEILING_S = 2.0  # the owner-amended relaxed ceiling during a bounded background-compute window
CSV_FIELDS = ["timestamp", "http_status", "elapsed_s", "breach_over_2s", "load_avg_1m"]


def host_load_avg_1m() -> Optional[float]:
    """The 1-minute load average, or None on a platform without `os.getloadavg` (never fabricated)."""
    try:
        return os.getloadavg()[0]
    except (AttributeError, OSError):  # pragma: no cover -- Linux (this project's only target) always has it
        return None


def poll_once(url: str, timeout: float = 5.0) -> dict:
    """One GET request against `url`, timed. `http_status` is 0 on a timeout/connection error (a starved
    client is distinct from a slow-but-answering server -- never conflated). Never raises."""
    ts = datetime.now(timezone.utc)
    t0 = time.monotonic()
    status = 0
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
            resp.read()
    except urllib.error.HTTPError as exc:
        status = exc.code
    except Exception:  # noqa: BLE001 -- record as a non-answer (status 0), never crash the poller
        status = 0
    elapsed_s = time.monotonic() - t0
    return {
        "timestamp": ts.isoformat(),
        "http_status": status,
        "elapsed_s": round(elapsed_s, 3),
        "breach_over_2s": 1 if elapsed_s > HEALTH_CEILING_S else 0,
        "load_avg_1m": host_load_avg_1m(),
    }


def run(
    url: str, out_path: str, stop_file: Optional[str], *, count: Optional[int] = None,
    interval_s: float = 1.0,
) -> int:
    """Poll `url` once per `interval_s` seconds, appending one CSV row per poll to `out_path`, until either
    `count` polls have run (when given) or `stop_file` appears on disk. Writes `<out_path>.meta.json` with
    the run's host-constant `cpu_count` + summary counts once polling stops. Returns the row count."""
    rows_written = 0
    with open(out_path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        writer.writeheader()
        fh.flush()
        while True:
            if count is not None and rows_written >= count:
                break
            if stop_file is not None and os.path.exists(stop_file):
                break
            t_poll_start = time.monotonic()
            row = poll_once(url)
            writer.writerow(row)
            fh.flush()
            rows_written += 1
            if count is not None and rows_written >= count:
                break
            remaining = interval_s - (time.monotonic() - t_poll_start)
            if remaining > 0:
                time.sleep(remaining)

    meta = {
        "url": url,
        "rows": rows_written,
        "cpu_count": os.cpu_count(),
        "health_ceiling_s": HEALTH_CEILING_S,
    }
    with open(out_path + ".meta.json", "w") as fh:
        json.dump(meta, fh, indent=2)
    return rows_written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", nargs="?", default="http://localhost:8255/api/health")
    parser.add_argument("out", nargs="?", default="poll_health.csv")
    parser.add_argument("stop_file", nargs="?", default="STOP")
    parser.add_argument(
        "--count", type=int, default=None,
        help="poll exactly N times then exit, instead of running until stop_file appears",
    )
    args = parser.parse_args()
    rows = run(args.url, args.out, args.stop_file if args.count is None else None, count=args.count)
    print(f"poll_health: wrote {rows} rows to {args.out}")


if __name__ == "__main__":
    main()
