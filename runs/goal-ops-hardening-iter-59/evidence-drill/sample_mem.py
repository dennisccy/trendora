"""Continuous VmPeak/VmHWM/VmRSS sampler for TC-4 (ops-hardening iter-59 fix pass).

Addendum 25's TC-4 figure was a SINGLE /proc read taken once, after the job reached terminal — a valid
LOWER bound on the true peak, but not the peak itself (the auditor recorded exactly that reservation).
This process samples the same four /proc/<pid>/status fields at a fixed cadence for the whole drill, so
the reported TC-4 number is the maximum of a real time series rather than one opportunistic read.

A process that does NOTHING else, for the same reason poll_health.py is standalone: a sampler sharing a
busy interpreter cannot distinguish "the server was starved" from "the sampler was starved".

CSV columns: epoch_ms, vmpeak_kb, vmhwm_kb, vmrss_kb, vmsize_kb  (blank row values == pid gone)
"""
import sys
import time

pid, out_path, duration_s = sys.argv[1], sys.argv[2], float(sys.argv[3])
PERIOD = 1.0
FIELDS = ("VmPeak", "VmHWM", "VmRSS", "VmSize")

end = time.time() + duration_s
with open(out_path, "w", buffering=1) as fh:
    fh.write("epoch_ms,vmpeak_kb,vmhwm_kb,vmrss_kb,vmsize_kb\n")
    while time.time() < end:
        t0 = time.monotonic()
        vals = {k: "" for k in FIELDS}
        try:
            with open(f"/proc/{pid}/status") as st:
                for line in st:
                    for k in FIELDS:
                        if line.startswith(k + ":"):
                            vals[k] = line.split()[1]
        except Exception:  # noqa: BLE001 — pid gone is a normal terminal condition, recorded as blanks
            pass
        fh.write(f"{int(time.time() * 1000)},{vals['VmPeak']},{vals['VmHWM']},"
                 f"{vals['VmRSS']},{vals['VmSize']}\n")
        rest = PERIOD - (time.monotonic() - t0)
        if rest > 0:
            time.sleep(rest)
