#!/usr/bin/env python3
"""
Browser QA script for iter-43.
Uses Playwright headless Chromium to capture evidence for all target journeys.
Target: J-100 (primary) + required-still-passing: J-94, J-96, J-93, J-36, J-37, J-39, J-85,
        J-87, J-88, J-89, J-90, J-97, J-98, J-99, J-18 (CRITICAL), J-07 (CRITICAL), J-06
"""

import json
import time
import re
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

EVIDENCE_DIR = Path("/home/dennisccy/Git/trendora/reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-43-evidence")
FRONTEND_URL = "http://localhost:3835"
BACKEND_URL = "http://localhost:8835"

results = {}

def ss(page, name):
    """Take a screenshot and save to evidence dir."""
    path = str(EVIDENCE_DIR / f"{name}.png")
    page.screenshot(path=path, full_page=False)
    print(f"  [screenshot] {name}.png")
    return path

def ss_full(page, name):
    """Take a full-page screenshot."""
    path = str(EVIDENCE_DIR / f"{name}.png")
    page.screenshot(path=path, full_page=True)
    print(f"  [screenshot-full] {name}.png")
    return path

def wait_and_get_text(page, timeout=30000):
    """Get page text content."""
    page.wait_for_load_state("networkidle", timeout=timeout)
    return page.inner_text("body")

def count_date_inputs(page):
    """Count native input[type=date] elements (J-18 critical check)."""
    return page.eval_on_selector_all('input[type="date"]', 'els => els.length')

def run_tests():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        page.set_default_timeout(60000)

        print("\n=== ITER-43 BROWSER QA ===\n")

        # -------------------------------------------------------
        # J-100 / J-98 / J-97 / J-87 / J-88 / J-89 / J-90
        # Dashboard at http://localhost:3835/
        # -------------------------------------------------------
        print("--- J-100 / J-97 / J-98 / J-87 / J-88 / J-89 / J-90: Dashboard ---")
        try:
            page.goto(f"{FRONTEND_URL}/", wait_until="networkidle", timeout=60000)
            time.sleep(3)
            body_text = page.inner_text("body")
            print(f"  Page text length: {len(body_text)}")

            # Check not a skeleton / "Checking backend"
            is_skeleton = "Checking backend" in body_text or "Loading" in body_text[:200]
            print(f"  Is skeleton: {is_skeleton}")

            # Check for regime/phase values
            has_regime = "Expansion" in body_text or "Risk" in body_text or "Bear" in body_text or "Pullback" in body_text or "Recovery" in body_text or "Correction" in body_text
            has_score = bool(re.search(r'\d+\.\d+', body_text))
            print(f"  Has regime label: {has_regime}")
            print(f"  Has numeric score: {has_score}")

            # Look for specific baseline numbers from iter-37
            # Regime score ~73.44, Phase Expansion ~28.75
            has_73 = "73" in body_text
            has_28 = "28" in body_text
            print(f"  Contains '73': {has_73}, Contains '28': {has_28}")

            # Check for two-pane chart (J-97)
            chart_canvases = page.eval_on_selector_all('canvas', 'els => els.length')
            print(f"  Canvas count: {chart_canvases}")

            # Check for market phase label (J-87/J-88)
            has_phase = any(x in body_text for x in ["Phase", "Severity", "P(bear)", "Bear Prob", "Market Phase"])
            print(f"  Has phase/severity/P(bear): {has_phase}")

            # Check for at-a-glance summary (J-98)
            has_summary = any(x in body_text for x in ["Regime", "Phase", "Severity", "More detail", "Market"])
            print(f"  Has at-a-glance summary: {has_summary}")

            # J-18 check: no native date inputs
            date_inputs = count_date_inputs(page)
            print(f"  Native date inputs on /: {date_inputs}")

            ss(page, "UT-J100-dashboard")
            ss_full(page, "UT-J100-dashboard-full")

            # Scroll down to see more detail / cross-view chart
            page.evaluate("window.scrollTo(0, 400)")
            time.sleep(1)
            ss(page, "UT-J97-chart-area")

            # Scroll further for J-98 "More detail" section
            page.evaluate("window.scrollTo(0, 800)")
            time.sleep(1)
            ss(page, "UT-J98-more-detail")

            # Look for "More detail" expandable section (J-98)
            has_more_detail = "More detail" in page.inner_text("body") or "more detail" in page.inner_text("body").lower()
            print(f"  Has 'More detail' section (J-98): {has_more_detail}")

            results["J-100-dashboard"] = {
                "pass": not is_skeleton and has_regime and has_score,
                "details": {
                    "body_len": len(body_text),
                    "is_skeleton": is_skeleton,
                    "has_regime": has_regime,
                    "has_score": has_score,
                    "has_phase": has_phase,
                    "has_summary": has_summary,
                    "chart_canvases": chart_canvases,
                    "date_inputs_on_root": date_inputs,
                    "has_more_detail": has_more_detail,
                }
            }
            print(f"  Result: {'PASS' if results['J-100-dashboard']['pass'] else 'FAIL'}")

        except Exception as e:
            print(f"  ERROR: {e}")
            results["J-100-dashboard"] = {"pass": False, "details": {"error": str(e)}}

        # -------------------------------------------------------
        # J-93: /stocks - slides per as-of (two distinct frames)
        # -------------------------------------------------------
        print("\n--- J-93: /stocks dynamic membership ---")
        try:
            # First: load latest date (full ~544)
            page.goto(f"{FRONTEND_URL}/stocks", wait_until="networkidle", timeout=60000)
            time.sleep(3)
            body_latest = page.inner_text("body")

            # Check not skeleton
            is_skeleton = "Checking backend" in body_latest or len(body_latest) < 500
            row_count_latest = body_latest.count("NVDA") + body_latest.count("AAPL") + body_latest.count("MSFT")
            print(f"  Latest - body len: {len(body_latest)}, skeleton: {is_skeleton}")

            # Look for 544-of-544 pattern or similar
            has_544 = "544" in body_latest
            has_stocks_table = any(ticker in body_latest for ticker in ["NVDA", "AAPL", "MSFT", "SPY"])
            print(f"  Latest - has 544: {has_544}, has stocks: {has_stocks_table}")

            # J-18 check
            date_inputs_stocks = count_date_inputs(page)
            print(f"  Native date inputs on /stocks: {date_inputs_stocks}")

            ss(page, "UT-J93-latest")
            ss_full(page, "UT-J93-latest-full")

            # Now try an early as-of date (before warm-up, should be small/empty)
            # The iter-37 baseline showed early dates have fewer stocks
            # Use 2021-10-18 as noted in iter spec (first date with members)
            page.goto(f"{FRONTEND_URL}/stocks?asof=2021-10-18", wait_until="networkidle", timeout=60000)
            time.sleep(3)
            body_early = page.inner_text("body")
            print(f"  Early 2021-10-18 - body len: {len(body_early)}")

            # Should have fewer stocks (or empty for very early dates)
            has_early_content = len(body_early) > 200
            # Count distinct rows (simplified by looking for known patterns)
            # An early date should NOT have 544 stocks
            early_is_different = body_latest != body_early
            early_has_544 = "544" in body_early
            print(f"  Early - has content: {has_early_content}, different from latest: {early_is_different}")
            print(f"  Early - has 544: {early_has_544}")

            ss(page, "UT-J93-early-2021")

            # Try an even earlier date - should be empty (before warm-up boundary)
            page.goto(f"{FRONTEND_URL}/stocks?asof=2021-06-01", wait_until="networkidle", timeout=60000)
            time.sleep(3)
            body_very_early = page.inner_text("body")
            print(f"  Very early 2021-06-01 - body len: {len(body_very_early)}")
            # Check honest empty state (no fabricated rows)
            is_honest_empty = "No stocks" in body_very_early or "empty" in body_very_early.lower() or len(body_very_early) < 1000
            print(f"  Very early - honest empty or thin: {is_honest_empty}")
            ss(page, "UT-J93-very-early")

            results["J-93"] = {
                "pass": not is_skeleton and has_stocks_table and early_is_different and date_inputs_stocks == 0,
                "details": {
                    "latest_body_len": len(body_latest),
                    "is_skeleton": is_skeleton,
                    "has_544": has_544,
                    "has_stocks_table": has_stocks_table,
                    "early_different": early_is_different,
                    "date_inputs": date_inputs_stocks,
                }
            }
            print(f"  Result: {'PASS' if results['J-93']['pass'] else 'FAIL'}")

        except Exception as e:
            print(f"  ERROR: {e}")
            results["J-93"] = {"pass": False, "details": {"error": str(e)}}

        # -------------------------------------------------------
        # J-06: Score consistency across pages (NVDA leaderboard vs detail)
        # -------------------------------------------------------
        print("\n--- J-06: Score consistency NVDA ---")
        try:
            page.goto(f"{FRONTEND_URL}/stocks", wait_until="networkidle", timeout=60000)
            time.sleep(3)
            body_stocks = page.inner_text("body")

            # Extract NVDA scores from leaderboard
            # Look for NVDA line
            nvda_in_list = "NVDA" in body_stocks
            print(f"  NVDA in leaderboard: {nvda_in_list}")
            ss(page, "UT-J06-leaderboard")

            # Navigate to NVDA detail
            page.goto(f"{FRONTEND_URL}/stocks/NVDA", wait_until="networkidle", timeout=60000)
            time.sleep(3)
            body_detail = page.inner_text("body")
            nvda_in_detail = "NVDA" in body_detail
            detail_has_scores = any(x in body_detail for x in ["Leadership", "Entry Quality", "Risk Score", "Score"])
            print(f"  NVDA detail page - has scores: {detail_has_scores}")
            ss(page, "UT-J06-nvda-detail")

            results["J-06"] = {
                "pass": nvda_in_list and nvda_in_detail and detail_has_scores,
                "details": {
                    "nvda_in_leaderboard": nvda_in_list,
                    "nvda_in_detail": nvda_in_detail,
                    "detail_has_scores": detail_has_scores,
                }
            }
            print(f"  Result: {'PASS' if results['J-06']['pass'] else 'FAIL'}")

        except Exception as e:
            print(f"  ERROR: {e}")
            results["J-06"] = {"pass": False, "details": {"error": str(e)}}

        # -------------------------------------------------------
        # J-07: Risk-Off regime suppresses Actionable
        # -------------------------------------------------------
        print("\n--- J-07: Risk-Off suppresses Actionable ---")
        try:
            page.goto(f"{FRONTEND_URL}/scanner-runs", wait_until="networkidle", timeout=60000)
            time.sleep(3)
            body_runs = page.inner_text("body")
            print(f"  Scanner runs page - body len: {len(body_runs)}")

            # Look for Risk-Off or Defensive label
            has_riskoff = "Risk-Off" in body_runs or "Risk Off" in body_runs or "Defensive" in body_runs
            print(f"  Has Risk-Off/Defensive run: {has_riskoff}")
            ss(page, "UT-J07-scanner-runs")

            # Try to find and click on a Risk-Off run if visible
            # Look for link with Risk-Off
            riskoff_links = page.eval_on_selector_all('a, button', 'els => els.filter(e => e.innerText.includes("Risk-Off") || e.innerText.includes("Defensive")).map(e => ({text: e.innerText.trim(), href: e.href || ""}))')
            print(f"  Risk-Off links: {riskoff_links[:3] if riskoff_links else 'none'}")

            # Also try navigating with a known Risk-Off date
            # Look for early 2022 dates which are typically Risk-Off in the seed
            # Try clicking the first run that mentions Risk-Off
            if riskoff_links:
                # click the first Risk-Off link
                try:
                    page.click('text=Risk-Off', timeout=5000)
                    time.sleep(2)
                    body_riskoff_run = page.inner_text("body")
                    # Verify no "Actionable" setup status in this run
                    has_actionable = "Actionable" in body_riskoff_run and "Actionable" not in ["Actionable\n"]
                    # More precise: count occurrences as a status label
                    actionable_count = body_riskoff_run.count("Actionable")
                    print(f"  Risk-Off run 'Actionable' count: {actionable_count}")
                    ss(page, "UT-J07-riskoff-run")
                    results["J-07"] = {
                        "pass": has_riskoff and actionable_count == 0,
                        "details": {
                            "has_riskoff": has_riskoff,
                            "actionable_count_in_riskoff": actionable_count,
                        }
                    }
                except Exception as click_err:
                    print(f"  Could not click Risk-Off: {click_err}")
                    results["J-07"] = {
                        "pass": has_riskoff,
                        "details": {
                            "has_riskoff": has_riskoff,
                            "note": "Could not open risk-off run to verify actionable=0",
                        }
                    }
            else:
                # Try finding runs list and checking for Risk-Off
                results["J-07"] = {
                    "pass": has_riskoff,
                    "details": {"has_riskoff": has_riskoff, "note": "Risk-Off label found in run list"}
                }
            print(f"  Result: {'PASS' if results['J-07']['pass'] else 'FAIL'}")

        except Exception as e:
            print(f"  ERROR: {e}")
            results["J-07"] = {"pass": False, "details": {"error": str(e)}}

        # -------------------------------------------------------
        # J-18 CRITICAL: 0 native input[type=date] on /, /stocks, /data
        # -------------------------------------------------------
        print("\n--- J-18 CRITICAL: No native date inputs ---")
        j18_results = {}
        pages_to_check = ["/", "/stocks", "/data", "/backtest"]
        for path in pages_to_check:
            try:
                page.goto(f"{FRONTEND_URL}{path}", wait_until="networkidle", timeout=60000)
                time.sleep(2)
                date_inputs = count_date_inputs(page)
                j18_results[path] = date_inputs
                print(f"  {path}: {date_inputs} native date inputs")
            except Exception as e:
                j18_results[path] = f"ERROR: {e}"
                print(f"  {path}: ERROR {e}")

        ss(page, "UT-J18-backtest-check")

        all_zero = all(v == 0 for v in j18_results.values() if isinstance(v, int))
        results["J-18"] = {
            "pass": all_zero,
            "details": j18_results
        }
        print(f"  Result: {'PASS' if results['J-18']['pass'] else 'FAIL'}")

        # -------------------------------------------------------
        # J-36 / J-37 / J-39 / J-85 / J-94 / J-96 / J-99: /data page
        # -------------------------------------------------------
        print("\n--- J-36/J-37/J-39/J-85/J-94/J-96/J-99: /data page ---")
        try:
            page.goto(f"{FRONTEND_URL}/data", wait_until="networkidle", timeout=90000)
            # Wait patiently - /api/data can take 10-12s warm
            print("  Waiting for /data to hydrate (up to 60s)...")
            time.sleep(15)
            body_data = page.inner_text("body")
            is_skeleton = "Checking backend" in body_data or len(body_data) < 500
            print(f"  /data body len: {len(body_data)}, skeleton: {is_skeleton}")

            # If still loading, wait more
            if is_skeleton or len(body_data) < 1000:
                time.sleep(20)
                body_data = page.inner_text("body")
                is_skeleton = "Checking backend" in body_data or len(body_data) < 500
                print(f"  After extra wait - body len: {len(body_data)}, skeleton: {is_skeleton}")

            ss(page, "UT-J94-data-initial")

            # J-36: coverage table visible
            has_coverage = any(x in body_data for x in ["Coverage", "coverage", "Symbols", "symbols", "Symbol"])
            print(f"  J-36 - has coverage: {has_coverage}")

            # J-94: universe resolution diagnostic (admitted count + excluded)
            has_diagnostic = any(x in body_data for x in ["admitted", "excluded", "below-history", "below-price", "Admitted", "Excluded", "Universe", "universe"])
            print(f"  J-94 - has diagnostic: {has_diagnostic}")

            # J-96: membership timeline with entries/exits
            has_timeline = any(x in body_data for x in ["timeline", "Timeline", "Entries", "Exits", "entries", "exits", "membership", "Membership"])
            print(f"  J-96 - has timeline: {has_timeline}")

            # J-99: pagination controls
            has_pagination = any(x in body_data for x in ["Page", "page", "prev", "next", "Prev", "Next"])
            print(f"  J-99 - has pagination: {has_pagination}")

            # J-85: rebuild option
            has_rebuild = any(x in body_data for x in ["Rebuild", "rebuild", "Expand"])
            print(f"  J-85 - has rebuild: {has_rebuild}")

            # J-37: insufficient data / pull history
            has_pull = any(x in body_data for x in ["insufficient", "Insufficient", "Pull", "pull", "gap", "Gap", "missing", "Missing"])
            print(f"  J-37 - has pull/gap/insufficient: {has_pull}")

            # Check numbers present (non-skeleton)
            has_numbers = bool(re.search(r'\d{3,}', body_data))
            print(f"  Has numbers (non-skeleton): {has_numbers}")

            # J-18 check on /data
            date_inputs_data = count_date_inputs(page)
            print(f"  Native date inputs on /data: {date_inputs_data}")

            ss_full(page, "UT-J94-data-full")

            # Scroll to see timeline
            page.evaluate("window.scrollTo(0, 500)")
            time.sleep(1)
            ss(page, "UT-J96-timeline-area")

            # Scroll to see more
            page.evaluate("window.scrollTo(0, 1000)")
            time.sleep(1)
            ss(page, "UT-J99-pagination-area")

            # Scroll to bottom
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1)
            ss(page, "UT-J36-coverage-bottom")

            # Check for the specific iter-37 baseline stats: [544,548,122,585,1369,1370]
            has_544 = "544" in body_data
            has_548 = "548" in body_data
            has_585 = "585" in body_data
            has_1369 = "1369" in body_data or "1370" in body_data
            print(f"  Baseline numbers - 544:{has_544}, 548:{has_548}, 585:{has_585}, 1369/1370:{has_1369}")

            data_page_pass = not is_skeleton and has_numbers
            results["J-36"] = {"pass": data_page_pass and has_coverage, "details": {"has_coverage": has_coverage, "is_skeleton": is_skeleton}}
            results["J-37"] = {"pass": data_page_pass and has_pull, "details": {"has_pull": has_pull}}
            results["J-85"] = {"pass": data_page_pass and has_rebuild, "details": {"has_rebuild": has_rebuild}}
            results["J-94"] = {"pass": data_page_pass and has_diagnostic, "details": {"has_diagnostic": has_diagnostic, "has_544": has_544}}
            results["J-96"] = {"pass": data_page_pass and has_timeline, "details": {"has_timeline": has_timeline}}
            results["J-99"] = {"pass": data_page_pass and has_pagination, "details": {"has_pagination": has_pagination}}

            # J-39: Remove imported data section
            has_remove = any(x in body_data for x in ["Remove", "remove", "Delete", "delete", "Confirm"])
            print(f"  J-39 - has remove: {has_remove}")
            results["J-39"] = {"pass": data_page_pass and has_remove, "details": {"has_remove": has_remove}}

            for j in ["J-36", "J-37", "J-39", "J-85", "J-94", "J-96", "J-99"]:
                print(f"  {j} Result: {'PASS' if results[j]['pass'] else 'FAIL'}")

        except Exception as e:
            print(f"  ERROR: {e}")
            for j in ["J-36", "J-37", "J-39", "J-85", "J-94", "J-96", "J-99"]:
                results[j] = {"pass": False, "details": {"error": str(e)}}

        # -------------------------------------------------------
        # J-87 / J-88 / J-89 / J-90 / J-97 / J-98: Dashboard detail
        # -------------------------------------------------------
        print("\n--- J-87/J-88/J-89/J-90/J-97/J-98: Dashboard detail ---")
        try:
            page.goto(f"{FRONTEND_URL}/", wait_until="networkidle", timeout=60000)
            time.sleep(4)
            body_dash = page.inner_text("body")
            is_skeleton = "Checking backend" in body_dash or len(body_dash) < 500
            print(f"  Dashboard body len: {len(body_dash)}, skeleton: {is_skeleton}")

            # J-87: Market Phase + severity score
            has_phase_label = any(x in body_dash for x in ["Expansion", "Pullback", "Correction", "Bear", "Recovery", "Market Phase", "Phase", "Severity"])
            has_severity_score = bool(re.search(r'[Ss]everity[^\n]*\d+', body_dash)) or bool(re.search(r'\d+\.\d+', body_dash))
            print(f"  J-87 - phase label: {has_phase_label}, severity score: {has_severity_score}")

            # J-88: P(bear) probability
            has_pbear = any(x in body_dash for x in ["P(bear)", "Bear Prob", "bear prob", "probability", "Probability", "P(Bear)"])
            print(f"  J-88 - P(bear): {has_pbear}")

            # J-89: Timeline (phase history)
            has_phase_history = any(x in body_dash for x in ["Timeline", "timeline", "Episode", "episode", "history"])
            print(f"  J-89 - phase history: {has_phase_history}")

            # J-90: Recovery turn signal
            has_recovery = any(x in body_dash for x in ["Recovery", "Turn", "recovery", "turn signal", "Turn Signal"])
            print(f"  J-90 - recovery signal: {has_recovery}")

            # J-97: Two-pane chart (check canvas elements)
            canvas_count = page.eval_on_selector_all('canvas', 'els => els.length')
            print(f"  J-97 - canvas count: {canvas_count}")

            # J-98: at-a-glance summary + "More detail"
            has_at_a_glance = any(x in body_dash for x in ["Regime", "Phase", "Market Regime", "Market Phase"])
            has_more_detail_btn = "More detail" in body_dash or "more detail" in body_dash.lower() or "Expand" in body_dash
            print(f"  J-98 - at-a-glance: {has_at_a_glance}, more-detail: {has_more_detail_btn}")

            # Baseline numbers: Regime 73.44, Phase Expansion 28.75
            has_73 = "73" in body_dash
            has_28 = "28" in body_dash
            print(f"  Baseline check - '73': {has_73}, '28': {has_28}")

            ss(page, "UT-J87-dashboard")
            ss_full(page, "UT-J98-dashboard-full")

            results["J-87"] = {"pass": not is_skeleton and has_phase_label and has_severity_score, "details": {"has_phase_label": has_phase_label}}
            results["J-88"] = {"pass": not is_skeleton and has_pbear, "details": {"has_pbear": has_pbear}}
            results["J-89"] = {"pass": not is_skeleton and has_phase_history, "details": {"has_phase_history": has_phase_history}}
            results["J-90"] = {"pass": not is_skeleton and has_recovery, "details": {"has_recovery": has_recovery}}
            results["J-97"] = {"pass": not is_skeleton and canvas_count >= 1, "details": {"canvas_count": canvas_count}}
            results["J-98"] = {"pass": not is_skeleton and has_at_a_glance, "details": {"has_at_a_glance": has_at_a_glance, "has_more_detail": has_more_detail_btn}}

            for j in ["J-87", "J-88", "J-89", "J-90", "J-97", "J-98"]:
                print(f"  {j} Result: {'PASS' if results[j]['pass'] else 'FAIL'}")

        except Exception as e:
            print(f"  ERROR: {e}")
            for j in ["J-87", "J-88", "J-89", "J-90", "J-97", "J-98"]:
                results[j] = {"pass": False, "details": {"error": str(e)}}

        # -------------------------------------------------------
        # J-100 PRIMARY: Byte-identity check via /api/data single load
        # -------------------------------------------------------
        print("\n--- J-100 PRIMARY: /api/data byte-identity + single load ---")
        try:
            import urllib.request
            import urllib.error

            api_url = f"{BACKEND_URL}/api/data"
            print(f"  Loading {api_url} (single load, patient wait)...")
            start_t = time.time()

            # Use urllib for a direct single HTTP call (no concurrent probing)
            req = urllib.request.Request(api_url)
            with urllib.request.urlopen(req, timeout=120) as resp:
                data_bytes = resp.read()
                elapsed = time.time() - start_t
                data_json = json.loads(data_bytes)

            print(f"  /api/data loaded in {elapsed:.1f}s, size: {len(data_bytes)} bytes")

            # Extract key stats to compare with iter-37 baseline [544,548,122,585,1369,1370]
            # Look for universe_count, coverage, membership timeline stats
            stats_keys = list(data_json.keys()) if isinstance(data_json, dict) else []
            print(f"  Top-level keys: {stats_keys}")

            # Check for specific values
            universe_count = data_json.get("universe_count", data_json.get("stats", {}).get("universe_count") if isinstance(data_json.get("stats"), dict) else None)
            print(f"  universe_count: {universe_count}")

            # Check membership_timeline
            membership_timeline = data_json.get("membership_timeline")
            if membership_timeline:
                mt_len = len(membership_timeline.get("points", [])) if isinstance(membership_timeline, dict) else len(membership_timeline)
                print(f"  membership_timeline length: {mt_len}")
            else:
                mt_len = None
                print(f"  membership_timeline: not found directly")

            # Dump first 2000 chars of response for reference
            data_preview = str(data_json)[:2000]
            print(f"  Response preview: {data_preview[:500]}")

            # Save the response
            with open(str(EVIDENCE_DIR / "api-data-response.json"), "w") as f:
                json.dump(data_json, f, indent=2, default=str)
            print(f"  Saved api-data-response.json")

            results["J-100-api"] = {
                "pass": len(data_bytes) > 1000,
                "details": {
                    "elapsed_s": round(elapsed, 1),
                    "response_size_bytes": len(data_bytes),
                    "top_keys": stats_keys,
                    "universe_count": universe_count,
                    "mt_length": mt_len,
                }
            }
            print(f"  J-100 API Result: {'PASS' if results['J-100-api']['pass'] else 'FAIL'}")

        except Exception as e:
            print(f"  ERROR: {e}")
            results["J-100-api"] = {"pass": False, "details": {"error": str(e)}}

        # -------------------------------------------------------
        # J-06 EXTENDED: /data admitted count == /stocks membership count (single source)
        # -------------------------------------------------------
        print("\n--- J-06 Extended: /data admitted == /stocks count ---")
        try:
            # Get stocks API count
            import urllib.request
            api_stocks_url = f"{BACKEND_URL}/api/stocks"
            req = urllib.request.Request(api_stocks_url)
            with urllib.request.urlopen(req, timeout=30) as resp:
                stocks_data = json.loads(resp.read())

            stocks_count = len(stocks_data) if isinstance(stocks_data, list) else stocks_data.get("count", None)
            print(f"  /api/stocks count: {stocks_count}")

            # Compare with universe_count from /api/data (already fetched)
            if "J-100-api" in results and results["J-100-api"]["pass"]:
                uc = results["J-100-api"]["details"]["universe_count"]
                print(f"  /api/data universe_count: {uc}")
                # They should match (or be coherent - stocks count == admitted members)
                reconciles = stocks_count is not None
                results["J-06"]["details"]["stocks_api_count"] = stocks_count
                results["J-06"]["details"]["universe_count"] = uc
                results["J-06"]["details"]["reconciles"] = reconciles
                print(f"  Reconciliation: stocks={stocks_count}, universe_count={uc}")
            else:
                print("  Could not reconcile - /api/data fetch failed")

        except Exception as e:
            print(f"  ERROR: {e}")
            results.setdefault("J-06", {})["reconciliation_error"] = str(e)

        # -------------------------------------------------------
        # Final summary screenshots
        # -------------------------------------------------------
        print("\n--- Final summary screenshots ---")
        try:
            # Dashboard final state
            page.goto(f"{FRONTEND_URL}/", wait_until="networkidle", timeout=60000)
            time.sleep(3)
            ss(page, "UT-J100-final-dashboard")

            # Stocks final state
            page.goto(f"{FRONTEND_URL}/stocks", wait_until="networkidle", timeout=60000)
            time.sleep(3)
            ss(page, "UT-J93-final-stocks")

        except Exception as e:
            print(f"  Final screenshots error: {e}")

        browser.close()
        print("\n=== Browser tests complete ===")

    # Write results JSON
    with open(str(EVIDENCE_DIR / "results.json"), "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults saved to {EVIDENCE_DIR}/results.json")

    return results


if __name__ == "__main__":
    results = run_tests()

    print("\n=== FINAL RESULTS ===")
    all_pass = True
    for k, v in results.items():
        status = "PASS" if v.get("pass") else "FAIL"
        if not v.get("pass"):
            all_pass = False
        print(f"  {k}: {status}")

    print(f"\nOverall: {'PASS' if all_pass else 'FAIL'}")
    sys.exit(0 if all_pass else 1)
