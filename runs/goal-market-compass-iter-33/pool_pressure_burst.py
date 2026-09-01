#!/usr/bin/env python3
"""pool_pressure_burst.py -- iter-32 J-09: replicate Addendum 40/41's "original-methodology
replica" burst (5 workers, the SAME 6-endpoint _POOL_PRESSURE_ENDPOINTS mix, 1.0-2.0s jittered
pacing, sustained for duration_s), OR a wide-N simultaneous-connection burst (TC-4: fire N
requests at once, repeated a few times) against ONE light endpoint. Records every response
(status + elapsed) to a results file so server-side vs client-side failures are distinguishable.

Usage:
  replica mode: python3 pool_pressure_burst.py replica <base_url> <duration_s> <out_jsonl>
  concurrent mode: python3 pool_pressure_burst.py concurrent <base_url> <n_simultaneous> <rounds> <out_jsonl>
"""
import concurrent.futures
import json
import random
import sys
import time
import urllib.request
import urllib.error

_POOL_PRESSURE_ENDPOINTS = (
    "/api/backtest",
    "/api/watchlist",
    "/api/sectors",
    "/api/themes",
    "/api/stocks",
    "/api/data/availability",
)

def _get(url, timeout=15.0):
    t0 = time.time()
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            resp.read()
            return {"url": url, "status": resp.status, "elapsed_s": round(time.time() - t0, 3), "error": None}
    except urllib.error.HTTPError as exc:
        return {"url": url, "status": exc.code, "elapsed_s": round(time.time() - t0, 3), "error": None}
    except Exception as exc:
        return {"url": url, "status": None, "elapsed_s": round(time.time() - t0, 3), "error": exc.__class__.__name__ + ":" + str(exc)}

def replica_worker(worker_id, base_url, stop_at, results, lock):
    endpoint = _POOL_PRESSURE_ENDPOINTS[worker_id % len(_POOL_PRESSURE_ENDPOINTS)]
    url = base_url + endpoint
    while time.time() < stop_at:
        r = _get(url)
        r["worker_id"] = worker_id
        r["ts_utc"] = time.time()
        with lock:
            results.append(r)
        time.sleep(random.uniform(1.0, 2.0))

def run_replica(base_url, duration_s, out_path):
    import threading
    results = []
    lock = threading.Lock()
    stop_at = time.time() + duration_s
    threads = [threading.Thread(target=replica_worker, args=(i, base_url, stop_at, results, lock)) for i in range(5)]
    start_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    end_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(out_path, "w") as fh:
        for r in results:
            fh.write(json.dumps(r) + "\n")
    non200 = [r for r in results if r["status"] != 200]
    print(f"replica burst: start={start_iso} end={end_iso} requests={len(results)} non200={len(non200)}")
    return results

def run_concurrent(base_url, n, rounds, out_path):
    url = base_url + "/api/health"
    all_results = []
    start_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    for rnd in range(rounds):
        with concurrent.futures.ThreadPoolExecutor(max_workers=n) as ex:
            futs = [ex.submit(_get, url) for _ in range(n)]
            round_results = [f.result() for f in futs]
        for r in round_results:
            r["round"] = rnd
        all_results.extend(round_results)
        time.sleep(1.0)
    end_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(out_path, "w") as fh:
        for r in all_results:
            fh.write(json.dumps(r) + "\n")
    non200 = [r for r in all_results if r["status"] != 200]
    errors = [r for r in all_results if r["error"]]
    print(f"concurrent burst: start={start_iso} end={end_iso} total_requests={len(all_results)} non200={len(non200)} client_errors={len(errors)}")
    return all_results

if __name__ == "__main__":
    mode = sys.argv[1]
    base_url = sys.argv[2]
    if mode == "replica":
        duration_s = float(sys.argv[3])
        out_path = sys.argv[4]
        run_replica(base_url, duration_s, out_path)
    elif mode == "concurrent":
        n = int(sys.argv[3])
        rounds = int(sys.argv[4])
        out_path = sys.argv[5]
        run_concurrent(base_url, n, rounds, out_path)
    else:
        print("unknown mode", file=sys.stderr)
        sys.exit(2)
