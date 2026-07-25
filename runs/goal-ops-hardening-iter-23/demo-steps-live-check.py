#!/usr/bin/env python3
"""Throwaway live-verification for the 4 distinct new demo-JSON goto+expect pairs
(n=8..12, n=10/12 share a URL) added to reports/goal-session-ops-hardening-demo.json
this iteration. Not part of any pipeline artifact -- confirms the `verified: true`
claim on each new step is honest (iter-16 lesson: check testable copy against the
real, current app, never assert from memory) before the dev handoff is written.
Reuses demo_runner.py's own pure `_do_action`/`_check_expect` helpers read-only.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path("/home/dennis-chan/Git/trendora")
sys.path.insert(0, str(REPO_ROOT / "scripts" / "automation" / "lib"))
import demo_runner as dr  # noqa: E402

BASE_URL = "http://localhost:3255"

CHECKS = [
    (8, "/stocks/AAPL", {"text": "Leadership"}),
    (9, "/backtest", {"text": "expanding window"}),
    (10, "/backtest", {"text": "expanding window"}),
    (11, "/backtest?asof=2026-07-20", {"text": "expanding window"}),
    (12, "/backtest?asof=2026-07-20", {"text": "expanding window"}),
]


def main() -> int:
    from playwright.sync_api import sync_playwright

    ok = True
    with sync_playwright() as pw:
        browser = dr._launch_chromium(pw, headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()
        for n, url, exp in CHECKS:
            try:
                dr._do_action(page, {"type": "goto", "url": url}, BASE_URL, 8000)
                passed = dr._check_expect(page, exp, 8000)
            except Exception as exc:  # noqa: BLE001
                passed = False
                print(f"step {n} {url} -> ERROR {exc}")
            status = "OK" if passed else "MISSING"
            if not passed:
                ok = False
            print(f"step {n:2d} {url:<30s} expect={exp['text']!r:<25s} -> {status}")
        context.close()
        browser.close()
    print("\nALL PASS" if ok else "\nAT LEAST ONE MISSING")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
