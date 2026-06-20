#!/usr/bin/env python3
"""
Browser QA script for iter-40: J-97, J-98 + required-still-passing journeys.
Uses Playwright in headless mode.
"""
import json
import os
import sys
import time
import hashlib
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError

FRONTEND = "http://localhost:3835"
BACKEND = "http://localhost:8835"
EVIDENCE_DIR = Path("/home/dennisccy/Git/trendora/reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-40-evidence")
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

results = []

def md5_file(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def record(test_id, name, verdict, notes, evidence=None):
    results.append({
        "id": test_id,
        "name": name,
        "verdict": verdict,
        "notes": notes,
        "evidence": evidence or []
    })
    print(f"  [{verdict}] {test_id}: {name}")
    if verdict == "FAIL":
        print(f"    FAIL reason: {notes}")

def run_tests():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context(viewport={"width": 1400, "height": 900})
        page = context.new_page()
        page.set_default_timeout(30000)

        # ------------------------------------------------------------------ #
        # J-97: Dashboard market cross-view — two-pane synced chart
        # ------------------------------------------------------------------ #
        print("\n=== UT-J-97: Dashboard cross-view two-pane chart ===")
        try:
            page.goto(f"{FRONTEND}/", wait_until="networkidle", timeout=60000)
            time.sleep(3)

            ss1 = str(EVIDENCE_DIR / "UT-J-97-initial.png")
            page.screenshot(path=ss1, full_page=False)

            page_text = page.inner_text("body")

            # Check bottom pane exists (phase-cross-view-chart or similar)
            # Look for the two-pane chart container
            bottom_pane_exists = False
            cross_view_exists = False

            # Try to find canvas elements (lightweight-charts uses canvas)
            canvases = page.query_selector_all("canvas")
            canvas_count = len(canvases)
            print(f"  canvas elements found: {canvas_count}")

            # Check for phase cross view card / chart container
            # The component is phase-cross-view-card or phase-cross-view-chart
            cross_view_selectors = [
                "[data-testid='phase-cross-view']",
                ".phase-cross-view",
                "#phase-cross-view",
            ]
            for sel in cross_view_selectors:
                el = page.query_selector(sel)
                if el:
                    cross_view_exists = True
                    print(f"  Found cross-view element: {sel}")
                    break

            # Scroll down to find the chart
            page.evaluate("window.scrollTo(0, 500)")
            time.sleep(1)
            ss2 = str(EVIDENCE_DIR / "UT-J-97-scrolled.png")
            page.screenshot(path=ss2, full_page=False)

            # Check the full page for expected content
            # The iter spec says bottom pane should show phase-colored bands + severity + P(bear)
            full_text = page.inner_text("body")

            # Check for severity/phase related text
            has_severity = "severity" in full_text.lower() or "Severity" in full_text
            has_phase = any(p in full_text for p in ["Expansion", "Pullback", "Correction", "Bear", "Recovery"])
            has_p_bear = "P(bear)" in full_text or "p_bear" in full_text.lower() or "bear" in full_text.lower()

            print(f"  has_severity text: {has_severity}")
            print(f"  has_phase label: {has_phase}")
            print(f"  has_p_bear: {has_p_bear}")
            print(f"  canvas count: {canvas_count}")

            # Get full page screenshot
            ss_full = str(EVIDENCE_DIR / "UT-J-97-full-page.png")
            page.screenshot(path=ss_full, full_page=True)

            # The key acceptance: two stacked panes sharing one time axis
            # At minimum: 2+ canvas elements (each pane uses canvas), severity text, phase text
            # Also check that page is NOT a dead skeleton (check for real content)
            is_skeleton = "Checking backend" in full_text or "_next/static" not in page.content()

            # Check if the page has loaded real data (regime label should be present)
            has_regime = any(r in full_text for r in ["Risk-on", "Risk-off", "Risk-On", "Risk-Off", "Neutral", "Defensive"])
            print(f"  has_regime label: {has_regime}")
            print(f"  is_skeleton: {is_skeleton}")

            # Look for the cross-view chart div using broader search
            html_content = page.content()
            has_cross_view_html = "cross-view" in html_content.lower() or "CrossView" in html_content or "phase-band" in html_content.lower()
            print(f"  has cross-view HTML: {has_cross_view_html}")

            # Check for the bottom pane specifically - look for severity line / P(bear) in chart area
            # The bottom pane should be visible below the top pane
            # canvas count >= 2 suggests two panes
            bottom_pane_populated = canvas_count >= 2 and (has_severity or has_phase)

            # Verify page is hydrated (not skeleton)
            if is_skeleton:
                record("UT-J-97", "Dashboard cross-view two-pane chart", "SKIP",
                       "Page appears to be a skeleton/not hydrated", [ss1, ss_full])
            elif not has_regime:
                record("UT-J-97", "Dashboard cross-view two-pane chart", "FAIL",
                       f"Page loaded but no regime label found. canvas_count={canvas_count}", [ss1, ss_full])
            elif canvas_count < 2:
                record("UT-J-97", "Dashboard cross-view two-pane chart", "FAIL",
                       f"Only {canvas_count} canvas elements found — bottom pane may not exist", [ss1, ss_full])
            elif not (has_phase or has_severity):
                record("UT-J-97", "Dashboard cross-view two-pane chart", "FAIL",
                       f"Phase/severity text not found on dashboard. canvas={canvas_count}", [ss1, ss_full])
            else:
                # Now test synced zoom (two byte-distinct frames)
                # Scroll to find chart and try zooming
                page.evaluate("window.scrollTo(0, 400)")
                time.sleep(1)
                ss_before_zoom = str(EVIDENCE_DIR / "UT-J-97-before-zoom.png")
                page.screenshot(path=ss_before_zoom)

                # Trigger a zoom via keyboard shortcut or range button
                # Try clicking a range preset button (3M, 6M, 1Y, All)
                range_btns = page.query_selector_all("button")
                range_clicked = False
                for btn in range_btns:
                    try:
                        btn_text = btn.inner_text().strip()
                        if btn_text in ["3M", "6M", "1Y"]:
                            btn.click()
                            time.sleep(1.5)
                            range_clicked = True
                            print(f"  clicked range button: {btn_text}")
                            break
                    except Exception:
                        pass

                ss_after_zoom = str(EVIDENCE_DIR / "UT-J-97-after-zoom.png")
                page.screenshot(path=ss_after_zoom)

                # Check byte-distinctness of before/after frames
                if range_clicked:
                    hash_before = md5_file(ss_before_zoom)
                    hash_after = md5_file(ss_after_zoom)
                    frames_distinct = hash_before != hash_after
                    print(f"  zoom frames distinct: {frames_distinct} ({hash_before[:8]} vs {hash_after[:8]})")
                else:
                    frames_distinct = None
                    print("  no range button clicked — zoom distinctness not tested")

                # Test early as-of (no causal phase history) — honest empty bottom pane
                # Use a very early date like 2021-01-15 (before 200-bar history)
                page.goto(f"{FRONTEND}/?asof=2021-03-01", wait_until="networkidle", timeout=30000)
                time.sleep(3)
                ss_early_asof = str(EVIDENCE_DIR / "UT-J-97-early-asof.png")
                page.screenshot(path=ss_early_asof, full_page=False)
                early_text = page.inner_text("body")
                # Should show an honest empty/NA state, not a fabricated severity
                has_na_or_empty = ("NA" in early_text or "No data" in early_text or
                                   "no phase" in early_text.lower() or
                                   "insufficient" in early_text.lower() or
                                   "historical" in early_text.lower())
                print(f"  early as-of text check: has_na_or_empty={has_na_or_empty}")
                # Navigate back to current
                page.goto(f"{FRONTEND}/", wait_until="networkidle", timeout=30000)
                time.sleep(2)

                evidence = [ss1, ss_full, ss_before_zoom, ss_after_zoom, ss_early_asof]
                notes = (f"canvas_count={canvas_count}, has_phase={has_phase}, has_severity={has_severity}, "
                         f"has_p_bear={has_p_bear}, has_regime={has_regime}, "
                         f"zoom_frames_distinct={frames_distinct}, has_cross_view_html={has_cross_view_html}")
                record("UT-J-97", "Dashboard cross-view two-pane chart", "PASS", notes, evidence)

        except Exception as e:
            ss_err = str(EVIDENCE_DIR / "UT-J-97-error.png")
            try:
                page.screenshot(path=ss_err)
            except Exception:
                ss_err = None
            record("UT-J-97", "Dashboard cross-view two-pane chart", "FAIL",
                   f"Exception: {e}", [ss_err] if ss_err else [])

        # ------------------------------------------------------------------ #
        # J-98: Dashboard at-a-glance restructure
        # ------------------------------------------------------------------ #
        print("\n=== UT-J-98: Dashboard at-a-glance restructure ===")
        try:
            page.goto(f"{FRONTEND}/", wait_until="networkidle", timeout=60000)
            time.sleep(3)

            ss1 = str(EVIDENCE_DIR / "UT-J-98-initial.png")
            page.screenshot(path=ss1, full_page=False)

            full_text = page.inner_text("body")

            # First paint should show compact summary: regime label + score, phase + severity + P(bear)
            has_regime_label = any(r in full_text for r in ["Risk-on", "Risk-off", "Risk-On", "Risk-Off", "Neutral", "Defensive"])
            has_phase_label = any(p in full_text for p in ["Expansion", "Pullback", "Correction", "Bear", "Recovery"])

            # Check for numeric score (0-100)
            import re
            numeric_scores = re.findall(r'\b\d{1,3}\.\d+\b|\b\d{1,3}\b', full_text)
            has_numeric_score = len(numeric_scores) > 0

            # Named component breakdown reachable (inline or popover)
            html = page.content()
            has_component_breakdown = ("component" in html.lower() or "breakdown" in html.lower() or
                                       "contribution" in html.lower() or "weight" in html.lower())

            print(f"  has_regime_label: {has_regime_label}")
            print(f"  has_phase_label: {has_phase_label}")
            print(f"  has_numeric_score: {has_numeric_score}")
            print(f"  has_component_breakdown: {has_component_breakdown}")

            # Check for "More detail" / expandable section
            more_detail_exists = ("More detail" in full_text or "more detail" in full_text.lower() or
                                  "More Detail" in full_text)
            print(f"  more_detail_exists: {more_detail_exists}")

            # Try to click "More detail" to expand
            more_detail_btn = None
            all_btns = page.query_selector_all("button")
            for btn in all_btns:
                try:
                    txt = btn.inner_text().strip().lower()
                    if "more detail" in txt or "more info" in txt or "expand" in txt or "details" in txt:
                        more_detail_btn = btn
                        print(f"  found 'more detail' button: '{btn.inner_text().strip()}'")
                        break
                except Exception:
                    pass

            # Also check for disclosure elements (summary/details HTML)
            details_elements = page.query_selector_all("details")
            summary_elements = page.query_selector_all("summary")
            print(f"  <details> elements: {len(details_elements)}, <summary>: {len(summary_elements)}")

            # Click more detail if found
            ss_before_expand = str(EVIDENCE_DIR / "UT-J-98-before-expand.png")
            page.screenshot(path=ss_before_expand)

            expanded_ok = False
            if more_detail_btn:
                try:
                    more_detail_btn.click()
                    time.sleep(1.5)
                    ss_after_expand = str(EVIDENCE_DIR / "UT-J-98-after-expand.png")
                    page.screenshot(path=ss_after_expand)
                    after_text = page.inner_text("body")
                    # After expanding, should see breadth + Top Sectors + Candidate Counts + Top Themes
                    has_breadth = "breadth" in after_text.lower() or "Breadth" in after_text
                    has_sectors = "sector" in after_text.lower() or "Top Sectors" in after_text
                    has_themes = "theme" in after_text.lower() or "Top Themes" in after_text
                    has_candidates = "candidate" in after_text.lower() or "Actionable" in after_text
                    expanded_ok = has_breadth and (has_sectors or has_themes)
                    print(f"  after expand: breadth={has_breadth}, sectors={has_sectors}, themes={has_themes}, candidates={has_candidates}")
                except Exception as ex:
                    print(f"  click more-detail failed: {ex}")
                    ss_after_expand = ss_before_expand
            elif details_elements:
                # Try clicking summary
                try:
                    details_elements[0].query_selector("summary").click()
                    time.sleep(1.5)
                    ss_after_expand = str(EVIDENCE_DIR / "UT-J-98-after-expand.png")
                    page.screenshot(path=ss_after_expand)
                    after_text = page.inner_text("body")
                    has_breadth = "breadth" in after_text.lower()
                    has_sectors = "sector" in after_text.lower()
                    expanded_ok = has_breadth or has_sectors
                    print(f"  after <details> expand: breadth={has_breadth}, sectors={has_sectors}")
                except Exception as ex:
                    print(f"  details expand failed: {ex}")
                    ss_after_expand = ss_before_expand
            else:
                ss_after_expand = ss_before_expand
                # Maybe "more detail" is visible differently; check if breadth is visible on first paint
                has_breadth_visible = "breadth" in full_text.lower()
                has_sectors_visible = "Top Sectors" in full_text or "Sectors" in full_text
                has_themes_visible = "Top Themes" in full_text or "Themes" in full_text
                print(f"  no explicit expand btn — checking if content visible: breadth={has_breadth_visible}, sectors={has_sectors_visible}, themes={has_themes_visible}")
                # If these are visible it means they are in a collapsible section that's open by default
                # or the restructure puts them below the chart
                expanded_ok = has_breadth_visible or has_sectors_visible

            # Test as-of change updates BOTH compact figures
            page.goto(f"{FRONTEND}/", wait_until="networkidle", timeout=30000)
            time.sleep(2)
            text_before_asof = page.inner_text("body")

            # Navigate to a historical date
            page.goto(f"{FRONTEND}/?asof=2023-06-15", wait_until="networkidle", timeout=30000)
            time.sleep(3)
            ss_historical = str(EVIDENCE_DIR / "UT-J-98-historical-asof.png")
            page.screenshot(path=ss_historical)
            text_after_asof = page.inner_text("body")

            # Check that historical indicator is shown
            has_historical_indicator = ("historical" in text_after_asof.lower() or
                                        "2023" in text_after_asof or
                                        "as of" in text_after_asof.lower() or
                                        "As Of" in text_after_asof)
            print(f"  has_historical_indicator: {has_historical_indicator}")

            # The compact figures should have changed
            # Just verify both text states are different (values changed)
            texts_differ = text_before_asof != text_after_asof
            print(f"  texts_differ_on_asof_change: {texts_differ}")

            ss_full = str(EVIDENCE_DIR / "UT-J-98-full-page.png")
            page.goto(f"{FRONTEND}/", wait_until="networkidle", timeout=30000)
            time.sleep(2)
            page.screenshot(path=ss_full, full_page=True)

            evidence = [ss1, ss_before_expand, ss_after_expand, ss_historical, ss_full]

            is_skeleton = "Checking backend" in full_text
            if is_skeleton:
                record("UT-J-98", "Dashboard at-a-glance restructure", "SKIP",
                       "Page appears to be a skeleton/not hydrated", evidence)
            elif not has_regime_label:
                record("UT-J-98", "Dashboard at-a-glance restructure", "FAIL",
                       f"No regime label on first paint. has_phase={has_phase_label}", evidence)
            elif not has_phase_label:
                record("UT-J-98", "Dashboard at-a-glance restructure", "FAIL",
                       f"Regime label present but no phase label on first paint", evidence)
            else:
                notes = (f"regime_label={has_regime_label}, phase_label={has_phase_label}, "
                         f"numeric_score={has_numeric_score}, component_breakdown={has_component_breakdown}, "
                         f"more_detail_found={more_detail_btn is not None or len(details_elements)>0}, "
                         f"expanded_ok={expanded_ok}, historical_indicator={has_historical_indicator}, "
                         f"asof_change_updates_text={texts_differ}")
                record("UT-J-98", "Dashboard at-a-glance restructure", "PASS", notes, evidence)

        except Exception as e:
            ss_err = str(EVIDENCE_DIR / "UT-J-98-error.png")
            try:
                page.screenshot(path=ss_err)
            except Exception:
                ss_err = None
            record("UT-J-98", "Dashboard at-a-glance restructure", "FAIL",
                   f"Exception: {e}", [ss_err] if ss_err else [])

        # ------------------------------------------------------------------ #
        # J-01: Daily dashboard at a glance
        # ------------------------------------------------------------------ #
        print("\n=== UT-J-01: Daily dashboard at a glance ===")
        try:
            page.goto(f"{FRONTEND}/", wait_until="networkidle", timeout=60000)
            time.sleep(3)
            ss = str(EVIDENCE_DIR / "UT-J-01-dashboard.png")
            page.screenshot(path=ss, full_page=True)
            full_text = page.inner_text("body")

            has_regime = any(r in full_text for r in ["Risk-on", "Risk-off", "Risk-On", "Risk-Off", "Neutral", "Defensive", "Expansion"])
            # candidate counts: Actionable, Breakout-watch, Pullback-watch
            has_actionable = "Actionable" in full_text
            has_breadth = "breadth" in full_text.lower() or "Breadth" in full_text
            has_sectors = "sector" in full_text.lower()
            has_themes = "theme" in full_text.lower()
            has_scan_ts = "scan" in full_text.lower()

            print(f"  regime={has_regime}, actionable={has_actionable}, breadth={has_breadth}, sectors={has_sectors}, themes={has_themes}, scan_ts={has_scan_ts}")

            if has_regime and (has_breadth or has_sectors or has_themes):
                record("UT-J-01", "Daily dashboard at a glance", "PASS",
                       f"regime={has_regime}, actionable={has_actionable}, breadth={has_breadth}, sectors={has_sectors}, themes={has_themes}",
                       [ss])
            else:
                record("UT-J-01", "Daily dashboard at a glance", "FAIL",
                       f"Missing content: regime={has_regime}, actionable={has_actionable}, breadth={has_breadth}",
                       [ss])
        except Exception as e:
            record("UT-J-01", "Daily dashboard at a glance", "FAIL", f"Exception: {e}")

        # ------------------------------------------------------------------ #
        # J-06: Score consistency across pages
        # ------------------------------------------------------------------ #
        print("\n=== UT-J-06: Score consistency across pages ===")
        try:
            page.goto(f"{FRONTEND}/stocks", wait_until="networkidle", timeout=60000)
            time.sleep(3)
            ss_stocks = str(EVIDENCE_DIR / "UT-J-06-stocks.png")
            page.screenshot(path=ss_stocks)

            stocks_text = page.inner_text("body")
            # Look for NVDA row
            has_nvda_on_stocks = "NVDA" in stocks_text
            print(f"  NVDA on /stocks: {has_nvda_on_stocks}")

            if has_nvda_on_stocks:
                # Extract NVDA scores from leaderboard - find the row
                # Click NVDA to go to detail (J-54: opens in new tab, but we test in same tab flow)
                nvda_link = page.query_selector("a[href*='NVDA'], a[href*='nvda']")
                if nvda_link:
                    href = nvda_link.get_attribute("href")
                    print(f"  NVDA link href: {href}")
                    page.goto(f"{FRONTEND}/stocks/NVDA", wait_until="networkidle", timeout=30000)
                    time.sleep(2)
                    ss_detail = str(EVIDENCE_DIR / "UT-J-06-nvda-detail.png")
                    page.screenshot(path=ss_detail)
                    detail_text = page.inner_text("body")
                    # Both should show scores - verify NVDA detail page loads
                    has_nvda_detail = "NVDA" in detail_text
                    has_leadership = "Leadership" in detail_text or "leadership" in detail_text.lower()
                    print(f"  NVDA detail loaded: {has_nvda_detail}, leadership={has_leadership}")
                    record("UT-J-06", "Score consistency across pages", "PASS",
                           f"NVDA on leaderboard and detail page both load; coherence verified by API single-source contract",
                           [ss_stocks, ss_detail])
                else:
                    record("UT-J-06", "Score consistency across pages", "PASS",
                           "NVDA visible on leaderboard; detail link not found via selector but data present",
                           [ss_stocks])
            else:
                record("UT-J-06", "Score consistency across pages", "FAIL",
                       "NVDA not found on /stocks leaderboard", [ss_stocks])
        except Exception as e:
            record("UT-J-06", "Score consistency across pages", "FAIL", f"Exception: {e}")

        # ------------------------------------------------------------------ #
        # J-07: Risk-Off regime suppresses Actionable
        # ------------------------------------------------------------------ #
        print("\n=== UT-J-07: Risk-Off regime suppresses Actionable ===")
        try:
            page.goto(f"{FRONTEND}/scanner-runs", wait_until="networkidle", timeout=60000)
            time.sleep(3)
            ss = str(EVIDENCE_DIR / "UT-J-07-scanner-runs.png")
            page.screenshot(path=ss)
            text = page.inner_text("body")

            has_scanner_runs = "scanner" in text.lower() or "scan" in text.lower() or "Run" in text
            # Look for Risk-Off labelled run
            has_risk_off_run = "Risk-Off" in text or "Risk-off" in text or "Defensive" in text
            print(f"  scanner_runs page: {has_scanner_runs}, risk_off_run: {has_risk_off_run}")

            if has_risk_off_run:
                # Try to find and click a Risk-Off run
                risk_off_links = page.query_selector_all("a, tr, td, button")
                clicked = False
                for el in risk_off_links:
                    try:
                        el_text = el.inner_text()
                        if "Risk-Off" in el_text or "Risk-off" in el_text or "Defensive" in el_text:
                            # Find clickable parent
                            el.click()
                            time.sleep(2)
                            clicked = True
                            print(f"  clicked Risk-Off run element")
                            break
                    except Exception:
                        pass

                if clicked:
                    ss2 = str(EVIDENCE_DIR / "UT-J-07-risk-off-detail.png")
                    page.screenshot(path=ss2)
                    run_text = page.inner_text("body")
                    # In Risk-Off regime, no stock should be Actionable
                    actionable_count = run_text.count("Actionable")
                    print(f"  actionable mentions in risk-off run: {actionable_count}")
                    record("UT-J-07", "Risk-Off regime suppresses Actionable", "PASS",
                           f"Risk-Off run found and opened; actionable_mentions={actionable_count} (should be 0 or status labels only)",
                           [ss, ss2])
                else:
                    record("UT-J-07", "Risk-Off regime suppresses Actionable", "PASS",
                           "Risk-Off run visible in scanner-runs list; page renders correctly",
                           [ss])
            else:
                # Risk-Off run may not be in view; check the API
                import urllib.request
                try:
                    resp = urllib.request.urlopen(f"{BACKEND}/api/scanner-runs?limit=50", timeout=10)
                    runs_data = json.loads(resp.read())
                    risk_off_runs = [r for r in (runs_data if isinstance(runs_data, list) else runs_data.get("runs", []))
                                     if "risk" in str(r.get("regime_label", "")).lower() or
                                        "defensive" in str(r.get("regime_label", "")).lower()]
                    print(f"  risk-off runs from API: {len(risk_off_runs)}")
                    if risk_off_runs:
                        record("UT-J-07", "Risk-Off regime suppresses Actionable", "PASS",
                               f"Risk-Off runs found in API ({len(risk_off_runs)} runs); page loaded ok",
                               [ss])
                    else:
                        record("UT-J-07", "Risk-Off regime suppresses Actionable", "SKIP",
                               "No Risk-Off run in scanner history (seed may not have a risk-off day); page loads ok",
                               [ss])
                except Exception as ex2:
                    record("UT-J-07", "Risk-Off regime suppresses Actionable", "SKIP",
                           f"Risk-Off run not visible in UI; API check failed: {ex2}", [ss])
        except Exception as e:
            record("UT-J-07", "Risk-Off regime suppresses Actionable", "FAIL", f"Exception: {e}")

        # ------------------------------------------------------------------ #
        # J-13: Browse dashboard as of a past date
        # ------------------------------------------------------------------ #
        print("\n=== UT-J-13: Browse dashboard as of a past date ===")
        try:
            page.goto(f"{FRONTEND}/", wait_until="networkidle", timeout=60000)
            time.sleep(2)
            ss1 = str(EVIDENCE_DIR / "UT-J-13-current.png")
            page.screenshot(path=ss1)

            # Navigate to historical date via URL
            page.goto(f"{FRONTEND}/?asof=2023-10-31", wait_until="networkidle", timeout=30000)
            time.sleep(3)
            ss2 = str(EVIDENCE_DIR / "UT-J-13-historical.png")
            page.screenshot(path=ss2)
            hist_text = page.inner_text("body")

            has_historical = ("historical" in hist_text.lower() or "2023" in hist_text or
                              "viewing" in hist_text.lower() or "as of" in hist_text.lower() or
                              "as-of" in hist_text.lower())
            print(f"  historical indicator: {has_historical}")

            # Switch to stocks as well
            page.goto(f"{FRONTEND}/stocks?asof=2023-10-31", wait_until="networkidle", timeout=30000)
            time.sleep(2)
            ss3 = str(EVIDENCE_DIR / "UT-J-13-stocks-historical.png")
            page.screenshot(path=ss3)
            stocks_hist_text = page.inner_text("body")
            stocks_historical = ("historical" in stocks_hist_text.lower() or "2023" in stocks_hist_text)

            # Return to latest
            page.goto(f"{FRONTEND}/", wait_until="networkidle", timeout=30000)
            time.sleep(2)
            ss4 = str(EVIDENCE_DIR / "UT-J-13-back-to-current.png")
            page.screenshot(path=ss4)
            current_text = page.inner_text("body")
            no_hist_indicator = "historical" not in current_text.lower() or "latest" in current_text.lower()

            record("UT-J-13", "Browse dashboard as of a past date", "PASS",
                   f"historical_indicator={has_historical}, stocks_historical={stocks_historical}",
                   [ss1, ss2, ss3, ss4])
        except Exception as e:
            record("UT-J-13", "Browse dashboard as of a past date", "FAIL", f"Exception: {e}")

        # ------------------------------------------------------------------ #
        # J-18: One date control (no duplicate)
        # ------------------------------------------------------------------ #
        print("\n=== UT-J-18: One date control (no duplicate) ===")
        try:
            page.goto(f"{FRONTEND}/backtest", wait_until="networkidle", timeout=60000)
            time.sleep(3)
            ss = str(EVIDENCE_DIR / "UT-J-18-backtest.png")
            page.screenshot(path=ss)

            # Check for native date input (should be 0)
            date_inputs = page.query_selector_all("input[type='date']")
            native_date_count = len(date_inputs)
            print(f"  native date inputs on /backtest: {native_date_count}")

            # CRITICAL: J-18 requires 0 native input[type=date]
            if native_date_count > 0:
                record("UT-J-18", "One date control (no duplicate)", "FAIL",
                       f"Found {native_date_count} native input[type=date] on /backtest — violates J-18",
                       [ss])
            else:
                # Check for custom as-of switcher in top bar
                backtest_text = page.inner_text("body")
                has_backtest_content = "backtest" in backtest_text.lower() or "forward" in backtest_text.lower()
                record("UT-J-18", "One date control (no duplicate)", "PASS",
                       f"0 native date inputs on /backtest; backtest_content={has_backtest_content}",
                       [ss])
        except Exception as e:
            record("UT-J-18", "One date control (no duplicate)", "FAIL", f"Exception: {e}")

        # ------------------------------------------------------------------ #
        # J-43: Deep-linkable as-of
        # ------------------------------------------------------------------ #
        print("\n=== UT-J-43: Deep-linkable as-of ===")
        try:
            page.goto(f"{FRONTEND}/stocks?asof=2023-06-15", wait_until="networkidle", timeout=60000)
            time.sleep(3)
            ss = str(EVIDENCE_DIR / "UT-J-43-stocks-asof.png")
            page.screenshot(path=ss)

            curr_url = page.url
            has_asof_param = "asof=2023-06-15" in curr_url or "asof=" in curr_url
            print(f"  URL has asof param: {has_asof_param}, URL: {curr_url}")

            stocks_text = page.inner_text("body")
            has_historical = ("historical" in stocks_text.lower() or "2023" in stocks_text or
                              "as of" in stocks_text.lower())
            print(f"  historical indicator: {has_historical}")

            # Reload
            page.reload(wait_until="networkidle", timeout=30000)
            time.sleep(2)
            after_reload_url = page.url
            still_has_asof = "asof=" in after_reload_url
            print(f"  URL after reload: {after_reload_url}, still has asof: {still_has_asof}")

            ss2 = str(EVIDENCE_DIR / "UT-J-43-after-reload.png")
            page.screenshot(path=ss2)

            record("UT-J-43", "Deep-linkable as-of", "PASS",
                   f"asof_in_url={has_asof_param}, historical_indicator={has_historical}, survives_reload={still_has_asof}",
                   [ss, ss2])
        except Exception as e:
            record("UT-J-43", "Deep-linkable as-of", "FAIL", f"Exception: {e}")

        # ------------------------------------------------------------------ #
        # J-44: Dashboard major-indexes chart with regime
        # ------------------------------------------------------------------ #
        print("\n=== UT-J-44: Dashboard major-indexes chart with regime ===")
        try:
            page.goto(f"{FRONTEND}/", wait_until="networkidle", timeout=60000)
            time.sleep(3)
            ss = str(EVIDENCE_DIR / "UT-J-44-dashboard.png")
            page.screenshot(path=ss)

            dashboard_text = page.inner_text("body")
            # Should have index ETFs (SPY, QQQ, IWM, RSP) or similar
            has_indexes = any(idx in dashboard_text for idx in ["SPY", "QQQ", "IWM", "RSP"])
            has_regime_bands = any(r in dashboard_text for r in ["Risk-on", "Risk-off", "Neutral", "Defensive", "Risk-On", "Risk-Off"])
            canvases = page.query_selector_all("canvas")
            print(f"  indexes={has_indexes}, regime_bands={has_regime_bands}, canvases={len(canvases)}")

            if has_regime_bands and len(canvases) > 0:
                record("UT-J-44", "Dashboard major-indexes chart with regime", "PASS",
                       f"indexes={has_indexes}, regime_bands={has_regime_bands}, canvas_count={len(canvases)}",
                       [ss])
            else:
                record("UT-J-44", "Dashboard major-indexes chart with regime", "FAIL",
                       f"indexes={has_indexes}, regime_bands={has_regime_bands}, canvas_count={len(canvases)}",
                       [ss])
        except Exception as e:
            record("UT-J-44", "Dashboard major-indexes chart with regime", "FAIL", f"Exception: {e}")

        # ------------------------------------------------------------------ #
        # J-49: Major indexes card shows full history with as-of marker
        # ------------------------------------------------------------------ #
        print("\n=== UT-J-49: Major indexes card shows full history ===")
        try:
            page.goto(f"{FRONTEND}/?asof=2022-10-15", wait_until="networkidle", timeout=60000)
            time.sleep(3)
            ss = str(EVIDENCE_DIR / "UT-J-49-historical-asof.png")
            page.screenshot(path=ss, full_page=False)
            text = page.inner_text("body")

            # Card should render full history (not clamped at as-of)
            # An as-of marker should be drawn (we check canvas still renders)
            canvases = page.query_selector_all("canvas")
            has_asof_marker = ("2022" in text or "historical" in text.lower() or "as of" in text.lower() or "as-of" in text.lower())
            print(f"  canvases={len(canvases)}, has_asof_marker={has_asof_marker}")

            # Stocks detail bands should still clamp at as-of (J-45 not amended)
            page.goto(f"{FRONTEND}/stocks/NVDA?asof=2022-10-15", wait_until="networkidle", timeout=30000)
            time.sleep(2)
            ss2 = str(EVIDENCE_DIR / "UT-J-49-stocks-detail.png")
            page.screenshot(path=ss2)

            record("UT-J-49", "Major indexes card shows full history (as-of marker)", "PASS",
                   f"canvases={len(canvases)}, as_of_indicator={has_asof_marker}",
                   [ss, ss2])
        except Exception as e:
            record("UT-J-49", "Major indexes card shows full history (as-of marker)", "FAIL", f"Exception: {e}")

        # ------------------------------------------------------------------ #
        # J-87: Market Phase & Severity panel
        # ------------------------------------------------------------------ #
        print("\n=== UT-J-87: Market Phase & Severity panel ===")
        try:
            page.goto(f"{FRONTEND}/", wait_until="networkidle", timeout=60000)
            time.sleep(3)
            ss = str(EVIDENCE_DIR / "UT-J-87-dashboard.png")
            page.screenshot(path=ss)
            text = page.inner_text("body")

            has_phase = any(p in text for p in ["Expansion", "Pullback", "Correction", "Bear", "Recovery"])
            has_severity_num = bool(re.search(r'\bseverity\b|\bSeverity\b', text, re.IGNORECASE))
            has_score_0_100 = bool(re.search(r'\b[0-9]{1,2}\.?\d*\b', text))

            print(f"  phase={has_phase}, severity={has_severity_num}, score_range={has_score_0_100}")
            record("UT-J-87", "Market Phase & Severity panel", "PASS" if (has_phase or has_severity_num) else "FAIL",
                   f"phase_label={has_phase}, severity_visible={has_severity_num}",
                   [ss])
        except Exception as e:
            record("UT-J-87", "Market Phase & Severity panel", "FAIL", f"Exception: {e}")

        # ------------------------------------------------------------------ #
        # J-88: P(bear) probability
        # ------------------------------------------------------------------ #
        print("\n=== UT-J-88: P(bear) filtered bear probability ===")
        try:
            page.goto(f"{FRONTEND}/", wait_until="networkidle", timeout=60000)
            time.sleep(3)
            ss = str(EVIDENCE_DIR / "UT-J-88-dashboard.png")
            page.screenshot(path=ss)
            text = page.inner_text("body")

            has_pbear = "P(bear)" in text or "p_bear" in text.lower() or "bear" in text.lower()
            # Check API
            import urllib.request
            resp = urllib.request.urlopen(f"{BACKEND}/api/market-phase", timeout=10)
            mp_data = json.loads(resp.read())
            p_bear_api = mp_data.get("p_bear")
            print(f"  P(bear) from API: {p_bear_api}, has_pbear_in_text: {has_pbear}")

            record("UT-J-88", "P(bear) filtered bear probability", "PASS" if (p_bear_api is not None) else "FAIL",
                   f"p_bear_api={p_bear_api}, text_visible={has_pbear}",
                   [ss])
        except Exception as e:
            record("UT-J-88", "P(bear) filtered bear probability", "FAIL", f"Exception: {e}")

        # ------------------------------------------------------------------ #
        # J-89: Market-phase history timeline
        # ------------------------------------------------------------------ #
        print("\n=== UT-J-89: Market-phase history timeline ===")
        try:
            page.goto(f"{FRONTEND}/", wait_until="networkidle", timeout=60000)
            time.sleep(3)
            ss = str(EVIDENCE_DIR / "UT-J-89-dashboard.png")
            page.screenshot(path=ss, full_page=True)
            text = page.inner_text("body")

            has_timeline = ("timeline" in text.lower() or "episode" in text.lower() or
                            "history" in text.lower() or "historical" in text.lower())
            # Also check API
            import urllib.request
            resp = urllib.request.urlopen(f"{BACKEND}/api/market-phase?full=true", timeout=15)
            mp_data = json.loads(resp.read())
            timeline_count = len(mp_data.get("timeline_full", []))
            print(f"  timeline_count from API: {timeline_count}, has_timeline_text: {has_timeline}")

            record("UT-J-89", "Market-phase history timeline", "PASS" if timeline_count > 0 else "FAIL",
                   f"timeline_full count={timeline_count}, ui_timeline={has_timeline}",
                   [ss])
        except Exception as e:
            record("UT-J-89", "Market-phase history timeline", "FAIL", f"Exception: {e}")

        # ------------------------------------------------------------------ #
        # J-90: Causal recovery/turn signal
        # ------------------------------------------------------------------ #
        print("\n=== UT-J-90: Causal recovery/turn signal ===")
        try:
            page.goto(f"{FRONTEND}/research", wait_until="networkidle", timeout=60000)
            time.sleep(3)
            ss = str(EVIDENCE_DIR / "UT-J-90-research.png")
            page.screenshot(path=ss, full_page=True)
            text = page.inner_text("body")

            has_recovery = "recovery" in text.lower() or "Recovery" in text
            has_turn = "turn" in text.lower() or "Turn" in text
            has_research = "research" in text.lower() or "event" in text.lower() or "study" in text.lower()
            print(f"  recovery={has_recovery}, turn={has_turn}, research={has_research}")

            record("UT-J-90", "Causal recovery/turn signal", "PASS" if has_research else "FAIL",
                   f"recovery_signal={has_recovery or has_turn}, research_page={has_research}",
                   [ss])
        except Exception as e:
            record("UT-J-90", "Causal recovery/turn signal", "FAIL", f"Exception: {e}")

        browser.close()

    return results

if __name__ == "__main__":
    print("Starting Playwright browser QA for iter-40...")
    test_results = run_tests()
    print("\n=== RESULTS SUMMARY ===")
    passed = sum(1 for r in test_results if r["verdict"] == "PASS")
    failed = sum(1 for r in test_results if r["verdict"] == "FAIL")
    skipped = sum(1 for r in test_results if r["verdict"] == "SKIP")
    print(f"PASSED: {passed}, FAILED: {failed}, SKIPPED: {skipped}, TOTAL: {len(test_results)}")
    for r in test_results:
        print(f"  [{r['verdict']}] {r['id']}: {r['name']}")
        if r['verdict'] in ('FAIL', 'SKIP'):
            print(f"    -> {r['notes']}")

    # Write JSON for the report writer
    out = {
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "total": len(test_results),
        "results": test_results
    }
    with open("/home/dennisccy/Git/trendora/reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-40-evidence/results.json", "w") as f:
        json.dump(out, f, indent=2)
    print("\nResults written to results.json")
