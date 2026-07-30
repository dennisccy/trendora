"""ops-hardening iter-37 (J-07 steps 1-3) -- concurrent monitor: samples VmPeak, background_compute
status, and re-reads the ALREADY-cached baseline as_of (2026-07-21) each cycle, asserting it stays
byte-identical to the pre-warm baseline captured before the trigger. Runs until the background warm's
`active` list empties (or a bounded max iteration count), then exits. Writes monitor.csv."""
import csv
import json
import subprocess
import sys
import time
from pathlib import Path

PID = sys.argv[1]
PORT = sys.argv[2]
OUT_DIR = Path(sys.argv[3])
MAX_ITERS = int(sys.argv[4]) if len(sys.argv) > 4 else 40
SLEEP_S = float(sys.argv[5]) if len(sys.argv) > 5 else 3.0

baseline_path = OUT_DIR / "baseline-2026-07-21.json"
baseline_bytes = baseline_path.read_bytes()

status_path = Path(f"/proc/{PID}/status")
rows = []
for i in range(1, MAX_ITERS + 1):
    epoch = time.time()
    status_text = status_path.read_text()
    vmpeak = next((line.split()[1] for line in status_text.splitlines() if line.startswith("VmPeak:")), "")
    vmhwm = next((line.split()[1] for line in status_text.splitlines() if line.startswith("VmHWM:")), "")

    health = subprocess.run(
        ["curl", "-s", f"http://127.0.0.1:{PORT}/api/health"], capture_output=True, text=True, timeout=10,
    ).stdout
    try:
        health_json = json.loads(health)
        active = health_json["background_compute"]["active"]
    except Exception:
        active = []
    n_active = len(active)
    hdone = active[0]["horizons_done"] if active else -1
    htotal = active[0]["horizons_total"] if active else -1

    probe = subprocess.run(
        ["curl", "-s", f"http://127.0.0.1:{PORT}/api/backtest?as_of=2026-07-21"],
        capture_output=True, timeout=10,
    ).stdout
    match = 1 if probe == baseline_bytes else 0

    rows.append([epoch, vmpeak, vmhwm, n_active, hdone, htotal, match])
    print(f"[{i}] epoch={epoch:.1f} vmpeak={vmpeak} n_active={n_active} hdone={hdone}/{htotal} baseline_match={match}")

    if n_active == 0 and i > 1:
        print(f"warm appears done at iteration {i}")
        break
    time.sleep(SLEEP_S)

with (OUT_DIR / "monitor.csv").open("w", newline="") as fh:
    writer = csv.writer(fh)
    writer.writerow(["epoch_s", "vmpeak_kb", "vmhwm_kb", "bg_active", "horizons_done", "horizons_total", "baseline_matches"])
    writer.writerows(rows)

n_mismatch = sum(1 for r in rows if r[6] == 0)
print(f"TOTAL_SAMPLES={len(rows)} MISMATCHES={n_mismatch}")
