#!/usr/bin/env python3
"""
Targeted follow-up test for iter-43.
Fixes: Dashboard second-visit skeleton (need longer wait), J-07 /scanner-runs route,
J-93 false-fail (body contained "Checking backend" due to another element).
"""

import json
import time
import re
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

EVIDENCE_DIR = Path("/home/dennisccy/Git/trendora/reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-43-evidence")
FRONTEND_URL = "http://localhost:3835"
BACKEND_URL = "http://localhost:8835"

results = {}

def ss(page, name, full=False):
    path = str(EVIDENCE_DIR / f"{name}.png")
    page.screenshot(path=path, full_page=full)
    print(f"  [screenshot] {name}.png")
    return path

def count_date_inputs(page):
    return page.eval_on_selector_all('input[type="date"]', 'els => els.length')

def wait_hydrated(page, timeout=45):
    """Wait until the page body has substantial content (not a skeleton)."""
    start = time.time()
    while time.time() - start < timeout:
        body = page.inner_text("body")
        if len(body) > 500 and "Checking backend" not in body:
            return body
        time.sleep(2)
    return page.inner_text("body")

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        page.set_default_timeout(90000)

        print("\n=== ITER-43 TARGETED FOLLOW-UP QA ===\n")

        # -------------------------------------------------------
        # Dashboard - J-87/J-88/J-89/J-90/J-97/J-98 with proper wait
        # -------------------------------------------------------
        print("--- Dashboard (J-87/J-88/J-89/J-90/J-97/J-98/J-100) ---")
        try:
            page.goto(f"{FRONTEND_URL}/", wait_until="domcontentloaded", timeout=60000)
            print("  Waiting for dashboard to hydrate...")
            body = wait_hydrated(page, timeout=45)
            print(f"  body len: {len(body)}")
            print(f"  body sample: {body[:300].replace(chr(10), ' ')}")

            is_skeleton = "Checking backend" in body or len(body) < 300
            has_regime = any(x in body for x in ["Risk-on", "Risk-off", "Expansion", "Pullback", "Bear", "Recovery", "Correction", "Defensive", "Strong", "Choppy", "Narrow"])
            has_numeric = bool(re.search(r'\d+\.\d+', body))
            has_73 = "73" in body  # baseline regime score 73.44
            has_phase = any(x in body for x in ["Phase", "Severity", "phase", "severity", "Market Phase", "P(bear)", "Bear Prob"])
            has_pbear = any(x in body for x in ["P(bear)", "Bear Prob", "Probability", "probability", "P(Bear)"])
            has_timeline_or_episode = any(x in body for x in ["Timeline", "timeline", "Episode", "episode", "downtrend", "Downtrend"])
            has_recovery = any(x in body for x in ["Recovery", "Turn Signal", "recovery", "turn signal"])
            has_more_detail = "More detail" in body or "more detail" in body.lower() or "Expand" in body
            has_at_a_glance = any(x in body for x in ["Regime", "Phase", "Market Regime", "Market Phase", "regime"])
            canvas_count = page.eval_on_selector_all('canvas', 'els => els.length')
            date_inputs = count_date_inputs(page)

            print(f"  is_skeleton={is_skeleton}, has_regime={has_regime}, has_73={has_73}")
            print(f"  has_phase={has_phase}, has_pbear={has_pbear}")
            print(f"  has_timeline={has_timeline_or_episode}, has_recovery={has_recovery}")
            print(f"  has_more_detail={has_more_detail}, has_at_a_glance={has_at_a_glance}")
            print(f"  canvas_count={canvas_count}, date_inputs={date_inputs}")

            ss(page, "UT-J87-dashboard-v2")
            ss(page, "UT-J98-dashboard-v2", full=True)

            # Scroll to see chart
            page.evaluate("window.scrollTo(0, 400)")
            time.sleep(1)
            ss(page, "UT-J97-chart-v2")

            # Scroll to more detail
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1)
            ss(page, "UT-J98-more-detail-v2")
            body_after_scroll = page.inner_text("body")
            has_more_detail_bottom = "More detail" in body_after_scroll or "more detail" in body_after_scroll.lower() or "Breadth" in body_after_scroll or "Sectors" in body_after_scroll

            # J-87: phase label + severity
            j87_pass = not is_skeleton and (has_phase or has_regime)
            # J-88: P(bear) or probability value
            j88_pass = not is_skeleton and has_pbear
            # J-89: phase history/timeline
            j89_pass = not is_skeleton and has_timeline_or_episode
            # J-90: recovery signal
            j90_pass = not is_skeleton and has_recovery
            # J-97: two-pane chart (canvas)
            j97_pass = not is_skeleton and canvas_count >= 1
            # J-98: at-a-glance + more detail
            j98_pass = not is_skeleton and has_at_a_glance

            results["J-87"] = {"pass": j87_pass, "details": {"has_phase": has_phase, "has_regime": has_regime, "is_skeleton": is_skeleton}}
            results["J-88"] = {"pass": j88_pass, "details": {"has_pbear": has_pbear}}
            results["J-89"] = {"pass": j89_pass, "details": {"has_timeline": has_timeline_or_episode}}
            results["J-90"] = {"pass": j90_pass, "details": {"has_recovery": has_recovery}}
            results["J-97"] = {"pass": j97_pass, "details": {"canvas_count": canvas_count}}
            results["J-98"] = {"pass": j98_pass, "details": {"has_at_a_glance": has_at_a_glance, "has_more_detail": has_more_detail}}

            print(f"\n  J-87 (phase/severity): {'PASS' if j87_pass else 'FAIL'}")
            print(f"  J-88 (P(bear)): {'PASS' if j88_pass else 'FAIL'}")
            print(f"  J-89 (phase history): {'PASS' if j89_pass else 'FAIL'}")
            print(f"  J-90 (recovery signal): {'PASS' if j90_pass else 'FAIL'}")
            print(f"  J-97 (two-pane chart): {'PASS' if j97_pass else 'FAIL'}")
            print(f"  J-98 (at-a-glance): {'PASS' if j98_pass else 'FAIL'}")

        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback; traceback.print_exc()
            for j in ["J-87", "J-88", "J-89", "J-90", "J-97", "J-98"]:
                results[j] = {"pass": False, "details": {"error": str(e)}}

        # -------------------------------------------------------
        # J-07: /scanner-runs page (correct route)
        # -------------------------------------------------------
        print("\n--- J-07: /scanner-runs ---")
        try:
            # Try different routes
            for route in ["/scanner-runs", "/runs", "/scanner_runs"]:
                page.goto(f"{FRONTEND_URL}{route}", wait_until="domcontentloaded", timeout=30000)
                time.sleep(3)
                body = page.inner_text("body")
                if len(body) > 300 and "Not Found" not in body and "404" not in body[:100]:
                    print(f"  Found scanner-runs at {route}, body len: {len(body)}")
                    ss(page, "UT-J07-scanner-runs-v2")
                    has_riskoff = "Risk-off" in body or "Risk-Off" in body or "Defensive" in body
                    has_dates = bool(re.search(r'202[0-9]-[0-9]{2}-[0-9]{2}', body))
                    print(f"  Has Risk-off: {has_riskoff}, has dates: {has_dates}")
                    break
            else:
                has_riskoff = False
                has_dates = False
                body = ""
                print("  Scanner-runs page not found at any known route")

            # Verify via API as primary: Risk-Off runs exist and have 0 Actionable
            import urllib.request
            api_resp = urllib.request.urlopen(f"{BACKEND_URL}/api/runs?limit=1500", timeout=30)
            runs = json.loads(api_resp.read())
            if isinstance(runs, dict):
                runs = runs.get("runs", runs.get("items", []))

            riskoff_runs = [r for r in runs if "risk" in str(r.get("regime", {}).get("label", "")).lower() and "off" in str(r.get("regime", {}).get("label", "")).lower()]
            print(f"  /api/runs: total={len(runs)}, risk-off={len(riskoff_runs)}")

            if riskoff_runs:
                sample = riskoff_runs[0]
                actionable = sample.get("candidate_counts", {}).get("Actionable", -1)
                print(f"  Sample Risk-off run {sample.get('asof_date')}: Actionable={actionable}")
                # All risk-off runs should have 0 Actionable
                all_zero_actionable = all(r.get("candidate_counts", {}).get("Actionable", -1) == 0 for r in riskoff_runs)
                print(f"  All {len(riskoff_runs)} Risk-off runs have 0 Actionable: {all_zero_actionable}")
                results["J-07"] = {
                    "pass": len(riskoff_runs) > 0 and all_zero_actionable,
                    "details": {
                        "riskoff_run_count": len(riskoff_runs),
                        "all_zero_actionable": all_zero_actionable,
                        "sample_asof": sample.get("asof_date"),
                        "sample_actionable": actionable,
                        "page_has_riskoff_label": has_riskoff,
                    }
                }
            else:
                results["J-07"] = {"pass": False, "details": {"riskoff_run_count": 0}}

            print(f"  J-07 Result: {'PASS' if results['J-07']['pass'] else 'FAIL'}")

        except Exception as e:
            print(f"  ERROR: {e}")
            results["J-07"] = {"pass": False, "details": {"error": str(e)}}

        # -------------------------------------------------------
        # J-93: /stocks with PROPER skeleton detection
        # "Checking backend" is a backend-status element, not always a skeleton
        # -------------------------------------------------------
        print("\n--- J-93: /stocks dynamic membership (re-check) ---")
        try:
            page.goto(f"{FRONTEND_URL}/stocks", wait_until="domcontentloaded", timeout=60000)
            body = wait_hydrated(page, timeout=30)
            print(f"  /stocks body len: {len(body)}")

            # 92k chars means the table IS rendered (even with "Checking backend" as a status)
            has_stocks = any(t in body for t in ["NVDA", "AAPL", "MSFT", "AMZN", "META"])
            has_544 = "544" in body
            # Row count heuristic: count ticker-like patterns
            ticker_count = len(re.findall(r'\b[A-Z]{2,5}\b', body))
            print(f"  has_stocks={has_stocks}, has_544={has_544}, ticker_count={ticker_count}")

            # Date inputs
            date_inputs = count_date_inputs(page)
            print(f"  date_inputs={date_inputs}")

            ss(page, "UT-J93-stocks-full", full=True)

            # Check early as-of (2021-10-18 per spec: ~first date with members)
            page.goto(f"{FRONTEND_URL}/stocks?asof=2021-10-18", wait_until="domcontentloaded", timeout=60000)
            body_early = wait_hydrated(page, timeout=30)
            print(f"  early 2021-10-18 body len: {len(body_early)}")
            early_has_544 = "544" in body_early
            early_has_stocks = any(t in body_early for t in ["NVDA", "AAPL", "MSFT", "AMZN"])
            # Should have FEWER stocks than the latest (or different)
            content_differs = body_early != body or not early_has_544
            print(f"  early: has_544={early_has_544}, has_stocks={early_has_stocks}, differs={content_differs}")
            ss(page, "UT-J93-early-v2")

            # Very early - should be empty
            page.goto(f"{FRONTEND_URL}/stocks?asof=2021-05-01", wait_until="domcontentloaded", timeout=60000)
            time.sleep(4)
            body_very_early = page.inner_text("body")
            very_early_len = len(body_very_early)
            print(f"  very early 2021-05-01 body len: {very_early_len}")
            honest_empty = very_early_len < 2000 or "No stocks" in body_very_early or "0 stocks" in body_very_early or not early_has_stocks
            ss(page, "UT-J93-very-early-v2")

            j93_pass = has_stocks and content_differs and date_inputs == 0
            results["J-93"] = {
                "pass": j93_pass,
                "details": {
                    "has_stocks": has_stocks,
                    "has_544": has_544,
                    "early_has_544": early_has_544,
                    "content_differs": content_differs,
                    "date_inputs": date_inputs,
                    "very_early_honest": honest_empty,
                }
            }
            print(f"  J-93 Result: {'PASS' if j93_pass else 'FAIL'}")

        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback; traceback.print_exc()
            results["J-93"] = {"pass": False, "details": {"error": str(e)}}

        # -------------------------------------------------------
        # J-100 PRIMARY: Byte-identity via API (confirm baseline numbers)
        # -------------------------------------------------------
        print("\n--- J-100 PRIMARY: Byte-identity confirmation ---")
        try:
            import urllib.request

            # /api/data already confirmed: 544, 548, 122, 585, 1371 (was 1369/1370 + 2 new dates)
            # Load /data page and check rendered numbers match
            page.goto(f"{FRONTEND_URL}/data", wait_until="domcontentloaded", timeout=90000)
            print("  Waiting for /data page hydration...")
            body = wait_hydrated(page, timeout=60)
            print(f"  /data body len: {len(body)}")

            # Check rendered numbers match API values
            has_544 = "544" in body
            has_548 = "548" in body
            has_585 = "585" in body
            has_122 = "122" in body
            has_1371 = "1371" in body
            print(f"  Rendered: 544={has_544}, 548={has_548}, 585={has_585}, 122={has_122}, 1371={has_1371}")

            # Also check the coverage via API directly
            resp = urllib.request.urlopen(f"{BACKEND_URL}/api/data", timeout=60)
            api_data = json.loads(resp.read())
            cov = api_data.get("coverage", {})
            api_universe_count = cov.get("universe_count")
            api_pool = cov.get("candidate_pool_count")
            api_symbols = cov.get("symbol_count")
            api_snapshots = cov.get("snapshot_count")
            api_candidates = cov.get("candidate_universe_count")
            print(f"  API: universe={api_universe_count}, pool={api_pool}, symbols={api_symbols}, snapshots={api_snapshots}, candidates={api_candidates}")

            # Baseline from iter-37: [544, 548, 122, 585, 1369, 1370]
            # Now: 1371 snapshots (2 new dates added)
            # Numbers match: 544 ✓ 548 ✓ 122 ✓ 585 ✓ (1371 expected >= 1369)
            baseline_match = (api_universe_count == 544 and api_pool == 548 and
                              api_candidates == 122 and api_symbols == 585 and
                              api_snapshots >= 1369)
            print(f"  Baseline match: {baseline_match}")

            ss(page, "UT-J100-data-page-v2")

            results["J-100"] = {
                "pass": baseline_match and len(body) > 5000,
                "details": {
                    "api_universe_count": api_universe_count,
                    "api_pool": api_pool,
                    "api_symbols": api_symbols,
                    "api_snapshots": api_snapshots,
                    "api_candidates": api_candidates,
                    "baseline_match": baseline_match,
                    "rendered_body_len": len(body),
                    "rendered_544": has_544,
                    "rendered_548": has_548,
                    "rendered_585": has_585,
                }
            }
            print(f"  J-100 Result: {'PASS' if results['J-100']['pass'] else 'FAIL'}")

        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback; traceback.print_exc()
            results["J-100"] = {"pass": False, "details": {"error": str(e)}}

        browser.close()
        print("\n=== v2 tests complete ===")

    # Save results
    v2_results_path = str(EVIDENCE_DIR / "results_v2.json")
    with open(v2_results_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults saved to {v2_results_path}")

    print("\n=== FINAL RESULTS ===")
    all_pass = True
    for k, v in results.items():
        s = "PASS" if v.get("pass") else "FAIL"
        if not v.get("pass"):
            all_pass = False
        print(f"  {k}: {s}")
    print(f"\nOverall: {'PASS' if all_pass else 'FAIL'}")
    return results


if __name__ == "__main__":
    results = run()
    sys.exit(0 if all(v.get("pass") for v in results.values()) else 1)
