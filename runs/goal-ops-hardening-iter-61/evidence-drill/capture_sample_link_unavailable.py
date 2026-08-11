"""goal-ops-hardening iter-61 (J-05/J-07 TC-4) — capture the shipped `sample-link.tsx` "Unavailable"
indicator (`data-testid="sample-link-unavailable"`, AlertTriangle + "Unavailable" text) actually
RENDERED under an armed fault, not just proven by unit test.

iter-60 shipped the fix (SampleLink's additive `unavailable` prop replacing the old `n=0` misleading
link) but captured zero visual evidence — the iter-59 `capture_degrade_ui.py` script this iteration
reuses the STRUCTURE of predates that fix and asserted the OLD `[title*="unavailable" i]` tooltip-cell
rendering (text "NA"), not the new element. This script:

  1. restarts the backend through scripts/start-backend.sh with the fault armed (AG-10 caps intact) --
     the frontend (already running via scripts/dev.sh) is left untouched and just reconnects;
  2. drives a real browser to /research/regime-lab under an `asof` whose cache key is a guaranteed MISS
     (armed FIRST -- see capture_degrade_ui.py's own comment on why order matters), in "As of date"
     analysis mode (the degrade lives on the as-of-scoped key, not the cached all-history default);
  3. screenshots the rendered page + the by-label table, and reads back the degraded element's own
     text/testid/title from the live DOM AND confirms no active `data-testid="sample-link"` link
     coexists in that same cell (exclusivity: never BOTH a broken link and a degrade badge);
  4. re-shoots the SAME as-of DISARMED (control) to prove the cohort holds a nonzero real observation
     count in the database when not faulted -- the concrete evidence TC-4 asks for;
  5. leaves the backend DISARMED and serving, so nothing downstream inherits a fault-injected process.

Usage: capture_sample_link_unavailable.py <out_dir> <asof> [candidate_asof2,candidate_asof3,...]
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

REPO = "/home/dennis-chan/Git/trendora"
OUT, ASOF = sys.argv[1], sys.argv[2]
CANDIDATES_EXTRA = sys.argv[3].split(",") if len(sys.argv) > 3 and sys.argv[3] else []
PORT = int(os.environ.get("CHAIN_BACKEND_PORT", "8255"))
FRONTEND = f"http://localhost:{os.environ.get('CHAIN_FRONTEND_PORT', '3255')}"
os.makedirs(OUT, exist_ok=True)


def health_up(timeout=3):
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{PORT}/api/health", timeout=timeout).read()
        return True
    except Exception:  # noqa: BLE001
        return False


def wait_ready(timeout=300):
    """Block until GET /api/health reports readiness == 'ready' -- the research pages replace their
    whole body with the WarmingState card while initializing, so a shot taken mid-warm-up shows that
    card and nothing about the degrade rendering (capture_degrade_ui.py's own documented false-negative)."""
    t0 = time.time()
    last = None
    while time.time() - t0 < timeout:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/api/health", timeout=10) as r:
                last = json.loads(r.read()).get("readiness")
            if last == "ready":
                return round(time.time() - t0, 1), last
        except Exception:  # noqa: BLE001
            pass
        time.sleep(2)
    return round(time.time() - t0, 1), last


def restart(env_extra):
    subprocess.run(["pkill", "-f", f"uvicorn main:app.*--port {PORT}"], capture_output=True)
    for _ in range(60):
        if not health_up(2):
            break
        time.sleep(0.5)
    env = dict(os.environ)
    env.update(env_extra)
    subprocess.Popen(["bash", f"{REPO}/scripts/start-backend.sh"], cwd=REPO, env=env,
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    t0 = time.time()
    while time.time() - t0 < 180:
        if health_up(5):
            return round(time.time() - t0, 3)
        time.sleep(0.25)
    raise SystemExit("backend never came back")


from playwright.sync_api import sync_playwright  # noqa: E402 — optional dep, imported where used


def api_shape(path):
    with urllib.request.urlopen(f"http://127.0.0.1:{PORT}{path}", timeout=900) as r:
        payload = json.loads(r.read())
    return {
        "regime_lab_status": payload.get("regime_lab_status", "ABSENT"),
        "degraded_cells": sum(
            1 for g in ("by_label", "by_decile") for row in (payload.get(g) or [])
            for c in (row.get("by_horizon") or []) if c.get("status") == "unavailable"),
        "by_label_rows": len(payload.get("by_label") or []),
    }


def capture(tag):
    """Load the page in 'As of date' analysis mode and quote what the DOM actually shows."""
    out = {}
    out["ready_wait_before_shot"] = wait_ready()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 1600})
        page.goto(f"{FRONTEND}/research/regime-lab?asof={ASOF}", wait_until="networkidle", timeout=180000)
        try:
            page.get_by_role("button", name="As of date").click(timeout=15000)
        except Exception as exc:  # noqa: BLE001
            out["mode_toggle_error"] = str(exc)[:200]
        page.wait_for_timeout(8000)
        out["page_url"] = page.url
        out["heading"] = page.locator("h1, h2").first.inner_text()

        unavailable = page.locator('[data-testid="sample-link-unavailable"]')
        out["unavailable_indicator_count"] = unavailable.count()
        out["sample_unavailable_indicators"] = [
            {
                "text": unavailable.nth(i).inner_text().strip(),
                "title": unavailable.nth(i).get_attribute("title"),
                "has_alert_icon": unavailable.nth(i).locator("svg").count() > 0,
                # exclusivity: this element must be a plain <span>, never wrapped in/alongside an <a>
                "wrapped_in_anchor": unavailable.nth(i).locator("xpath=ancestor::a").count() > 0,
            }
            for i in range(min(5, unavailable.count()))
        ]
        active_links = page.locator('[data-testid="sample-link"]')
        out["active_sample_link_count"] = active_links.count()

        body = page.locator("body").inner_text()
        out["error_boundary_text_present"] = any(
            s in body for s in ("Application error", "Unhandled Runtime Error", "Internal Server Error"))
        out["warming_up_banner_present"] = "Warming up" in body
        out["by_label_table_present"] = page.locator('[data-testid="regime-lab-by-label"]').count() > 0
        out["by_decile_table_present"] = page.locator('[data-testid="regime-lab-by-decile"]').count() > 0

        shot = os.path.join(OUT, f"TC-4-{tag}.png")
        page.screenshot(path=shot, full_page=False)
        out["screenshot"] = shot
        t = page.locator('[data-testid="regime-lab-by-label"]')
        if t.count():
            t.first.screenshot(path=os.path.join(OUT, f"TC-4-{tag}-by-label-table.png"))
            out["screenshot_table"] = os.path.join(OUT, f"TC-4-{tag}-by-label-table.png")
        # a tight crop around the FIRST unavailable indicator itself, so the AlertTriangle+text is
        # legible at full resolution without hunting through the whole-page shot.
        if unavailable.count():
            unavailable.first.screenshot(path=os.path.join(OUT, f"TC-4-{tag}-indicator-closeup.png"))
            out["screenshot_closeup"] = os.path.join(OUT, f"TC-4-{tag}-indicator-closeup.png")
        browser.close()
    return out


result = {"asof_requested": ASOF}

# ---- TREATMENT arm first (fault ARMED) -- the arm has a precondition the control does not: the as-of's
# cache key must still be a MISS. Running the control first would COMPUTE and CACHE that key, after which
# regime_lab_cached returns the cached clean payload and compute_regime_lab -- where the fault site lives
# -- is never entered. Pick a still-uncached as-of under the armed process, prove the degrade at the API,
# screenshot it, and only then disarm and re-shoot the SAME as-of as the control.
result["boot_armed_seconds"] = restart({"TRENDORA_FAULT_INJECT_MEMORY_ERROR": "regime_lab"})
result["ready_wait_armed"] = wait_ready()

candidates = [ASOF] + [d for d in CANDIDATES_EXTRA if d]
chosen, armed_shape = None, None
for cand in candidates:
    shape = api_shape(f"/api/research/regime-lab?view=pooled&as_of={cand}")
    result.setdefault("candidate_probe", []).append({"as_of": cand, **shape})
    if shape["degraded_cells"] > 0:
        chosen, armed_shape = cand, shape
        break
if chosen is None:
    raise SystemExit(f"no candidate as-of produced a cache MISS under the armed process: "
                      f"{result['candidate_probe']}")
ASOF = chosen
result["asof_used"] = ASOF
result["api_armed"] = armed_shape
result["ui_armed"] = capture("degrade-rendered")

# ---- CONTROL arm (fault DISARMED, SAME as-of). Proves the cohort holds a nonzero real observation
# count in the database -- without this, "NA"/"Unavailable" cannot be told apart from "this as-of has
# no data anyway" (the exact distinction TC-4 requires).
result["boot_control_seconds"] = restart({"TRENDORA_FAULT_INJECT_MEMORY_ERROR": ""})
result["ready_wait_control"] = wait_ready()
result["api_control"] = api_shape(f"/api/research/regime-lab?view=pooled&as_of={ASOF}")
result["ui_control"] = capture("control-clean")
# the process is already DISARMED here, so nothing downstream inherits a fault-injected backend.

with open(os.path.join(OUT, "tc4-sample-link-unavailable.json"), "w") as fh:
    json.dump(result, fh, indent=1)
print(json.dumps(result, indent=1))
