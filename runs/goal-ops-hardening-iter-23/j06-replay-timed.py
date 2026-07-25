#!/usr/bin/env python3
"""Throwaway timing instrument for the corrected J-06.json replay (iter-23, TC-8).

demo_runner.py's own `--mode verify` records only a PASS/FAIL verdict + one
end-state screenshot per journey -- no per-step elapsed time. The iter-23 spec's
DoD requires the elapsed time of J-06's slowest step to be recorded in the dev
handoff, so this script drives the SAME action/expect semantics by importing the
pure, already-reviewed helpers straight from the committed demo_runner.py
(_do_action, _check_expect, _default_timeout, normalize_url, _launch_chromium) --
zero duplication of browser-automation logic, and demo_runner.py itself is
untouched (read-only import, matches iter-22's own pattern of scratch
measurement scripts under runs/goal-ops-hardening-iter-<N>/ rather than editing
product/framework code).

Not a pipeline artifact -- a disclosed, one-off measurement script, kept here for
reproducibility alongside its output CSV.
"""
from __future__ import annotations

import csv
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path("/home/dennis-chan/Git/trendora")
sys.path.insert(0, str(REPO_ROOT / "scripts" / "automation" / "lib"))
import demo_runner as dr  # noqa: E402

BASE_URL = "http://localhost:3255"
SCRIPT_PATH = REPO_ROOT / "runs/goal-session-ops-hardening/journey-scripts/J-06.json"
OUT_CSV = REPO_ROOT / "runs/goal-ops-hardening-iter-23/j06-replay-timed.csv"


def main() -> int:
    data = json.loads(SCRIPT_PATH.read_text(encoding="utf-8"))
    errs = dr.validate_script(data)
    if errs:
        print("INVALID SCRIPT:", errs)
        return 2

    default_tmo = data.get("default_timeout_ms", 8000)
    steps = data["steps"]
    rows = []

    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = dr._launch_chromium(pw, headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()
        overall_verdict = "PASS"
        for step in steps:
            n = int(step.get("n", 0))
            action = step["action"]
            exp = step.get("expect")
            tmo = max(1000, min(int(step.get("timeout_ms", default_tmo)), 20000))
            t0 = time.perf_counter()
            verdict = "PASS"
            detail = ""
            try:
                dr._do_action(page, action, BASE_URL, tmo)
                if exp:
                    ok = dr._check_expect(page, exp, tmo)
                    if not ok:
                        verdict = "FAIL"
                        detail = f"expect {dr._expect_desc(exp)} did not appear"
            except Exception as exc:  # noqa: BLE001
                verdict = "FAIL"
                detail = str(exc).splitlines()[0][:160]
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            rows.append({
                "n": n, "url": action.get("url", ""), "timeout_ms_budget": tmo,
                "elapsed_ms": round(elapsed_ms, 2), "verdict": verdict, "detail": detail,
            })
            print(f"step {n:2d} {action.get('url', ''):<28s} "
                  f"elapsed={elapsed_ms:8.2f}ms budget={tmo}ms verdict={verdict} {detail}")
            if verdict == "FAIL":
                overall_verdict = "FAIL"
                break
        context.close()
        browser.close()

    with OUT_CSV.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["n", "url", "timeout_ms_budget", "elapsed_ms", "verdict", "detail"])
        w.writeheader()
        w.writerows(rows)

    slowest = max(rows, key=lambda r: r["elapsed_ms"]) if rows else None
    print(f"\nOVERALL: {overall_verdict}  steps={len(rows)}")
    if slowest:
        print(f"SLOWEST: step {slowest['n']} {slowest['url']} = {slowest['elapsed_ms']:.2f} ms "
              f"(budget {slowest['timeout_ms_budget']} ms)")
    print(f"CSV written: {OUT_CSV}")
    return 0 if overall_verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
