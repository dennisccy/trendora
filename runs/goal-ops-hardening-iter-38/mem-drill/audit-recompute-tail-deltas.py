"""ops-hardening iter-38 AUDIT (finding B1) -- recompute the two-arm finalize-tail-only VmPeak deltas
from the raw monitor CSVs, without trusting either arm's reported anchor.

Why: `two-arm-summary.json` (and `reports/perf-budgets.md`'s canonical table) anchored the FALLBACK arm's
"tail-only" delta on its FIRST CAPTURED SAMPLE (3,320,896 KB) and labelled that value "VmPeak at
end-of-backfill-stage". It is not: the fallback monitor started ~32 s AFTER that job was submitted, i.e.
mid backfill-compute stage. The live arm's anchor (3,370,480 KB) IS a genuine end-of-backfill-stage
reading, so the two published numbers were not measuring the same interval.

Two independent checks are run:
  (1) TIMESTAMP RECONSTRUCTION -- each monitor CSV's mtime is the moment the sampler wrote the file
      (immediately after its last sample), so sample_epoch = mtime - (last_elapsed_s - row_elapsed_s).
      Cross-check: applying it to the LIVE arm reproduces the published 3,370,480 KB anchor exactly.
  (2) ANCHOR-FREE CHECK -- the fallback arm's VmPeak is flat from t=62.6 s to job completion (~263 s),
      so its finalize-tail delta is 0.0 MB under ANY anchor at or after t=62.6 s; the accompanying VmRSS
      collapse (3.10 GB -> 1.56 GB) is the pre-iter-37 stage-exit cache release, i.e. the stage boundary
      itself. No timestamp arithmetic is needed for the qualitative conclusion.

Usage: python3 audit-recompute-tail-deltas.py   (run from this directory)
"""
import csv
import datetime as dt
import os

JOBS = {
    "live": {
        "csvs": ["arm-live-monitor-final.csv"],
        "job_start": "2026-07-30T11:59:16.242398+00:00",
        "backfill_stage_seconds": 84.2691,
        "job_end": "2026-07-30T12:01:17.596434+00:00",
    },
    "fallback": {
        "csvs": ["arm-fallback-monitor-final.csv", "arm-fallback-monitor-final2.csv"],
        "job_start": "2026-07-30T12:10:57.341186+00:00",
        "backfill_stage_seconds": 95.09,
        "job_end": "2026-07-30T12:16:14.372725+00:00",
    },
}


def load(path):
    with open(path) as fh:
        return list(csv.DictReader(fh))


def mtime_utc(path):
    return dt.datetime.fromtimestamp(os.path.getmtime(path), dt.timezone.utc)


for arm, meta in JOBS.items():
    job_start = dt.datetime.fromisoformat(meta["job_start"])
    stage_end = job_start + dt.timedelta(seconds=meta["backfill_stage_seconds"])
    peak = 0
    anchor_val = None
    print(f"== {arm} arm  (job {meta['job_start']} -> {meta['job_end']}, backfill stage "
          f"{meta['backfill_stage_seconds']}s, stage end {stage_end.isoformat()})")
    for path in meta["csvs"]:
        rows = load(path)
        last = float(rows[-1]["elapsed_s"])
        seg_end = mtime_utc(path)
        seg_start = seg_end - dt.timedelta(seconds=last)
        print(f"   {path}: {len(rows)} samples, reconstructed window "
              f"{seg_start.isoformat()} .. {seg_end.isoformat()} "
              f"(starts {(seg_start - job_start).total_seconds():.1f}s after job start)")
        for r in rows:
            epoch = seg_start + dt.timedelta(seconds=float(r["elapsed_s"]))
            vm = int(r["vmpeak_kb"])
            peak = max(peak, vm)
            if epoch <= stage_end:
                anchor_val = vm
    if anchor_val is None:
        print("   NO sample at or before the backfill-stage end -- anchor unavailable from this CSV")
    else:
        print(f"   VmPeak at end-of-backfill-stage: {anchor_val} KB")
    print(f"   VmPeak overall (through job completion): {peak} KB")
    if anchor_val is not None:
        print(f"   FINALIZE-TAIL-ONLY delta: {(peak - anchor_val) / 1024:.1f} MB")
    print()

# anchor-free corroboration for the fallback arm
fb = load("arm-fallback-monitor-final.csv") + load("arm-fallback-monitor-final2.csv")
flat_from = next(r for r in fb if int(r["vmpeak_kb"]) >= 3565104)
print("anchor-free check (fallback): VmPeak first reaches its overall peak 3565104 KB at monitor "
      f"t={flat_from['elapsed_s']}s and never rises again through job completion -> tail delta 0.0 MB "
      "for ANY anchor at or after that sample; VmRSS collapses 3,101,404 -> 1,564,872 KB just after it "
      "(the pre-iter-37 stage-exit cache release).")
print("live overall peak 3604964 KB vs fallback overall peak 3565104 KB -> live is "
      f"{(3604964 - 3565104) / 1024:.1f} MB (1.1%) higher.")
