"""TC-11 / audit finding F1 — capture the degrade rendering ACTUALLY RENDERED (iter-59 audit-fix pass).

The audit's F1 stands because UT-02/UT-03 SKIPPED: arming `TRENDORA_FAULT_INJECT_MEMORY_ERROR=regime_lab`
needs a backend restart, and the browser-QA agent's hard rule forbids restarting the app. So TC-11 had
zero visual evidence — the tooltip, the NA placeholder and the containment of the degraded column were
proven only by code read and `tsc`. The audit's own recommendation is that the DEVELOPER pre-arm a
fault-injected backend, because the lane structurally cannot. That is what this script does, end to end,
in one bounded run:

  1. restart the backend through scripts/start-backend.sh with the fault armed (AG-10 caps intact);
  2. drive a real browser to /research/regime-lab under an `asof` whose cache key is a guaranteed MISS,
     so the page's OWN request enters compute_regime_lab and really degrades — a cached all-history key
     would render the clean payload and prove nothing;
  3. screenshot the rendered tables, and read back the degraded cell's text and its `title` tooltip from
     the live DOM, so the claim "renders an honest placeholder, never a fabricated number" is quoted from
     the page rather than asserted;
  4. leave the backend DISARMED and serving, so nothing downstream inherits a fault-injected process.

Usage: capture_degrade_ui.py <out_dir> <asof>
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

REPO = "/home/dennis-chan/Git/trendora"
OUT, ASOF = sys.argv[1], sys.argv[2]
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
    """Block until GET /api/health reports state == 'ready'.

    Not cosmetic: while readiness is 'initializing' the research pages deliberately replace their whole
    body with the WarmingState card (`shouldShowWarming`, components/warming-state.tsx), so a screenshot
    taken during a post-restart warm-up shows that card and NOTHING about the degrade rendering. The
    first attempt at this capture produced exactly that false negative.
    """
    t0 = time.time()
    last = None
    while time.time() - t0 < timeout:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/api/health", timeout=10) as r:
                # The field is `readiness` — reading a non-existent `state` key silently never matches
                # and burns the whole timeout, which is how the first run of this script "hung".
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
        # The lab defaults to ANALYSIS MODE = "All history" (a cached, all-history cache key). The
        # degrade under test lives on the as-of-scoped key, so the mode toggle must be clicked —
        # loading the page with ?asof alone leaves the request all-history and proves nothing.
        try:
            page.get_by_role("button", name="As of date").click(timeout=15000)
        except Exception as exc:  # noqa: BLE001
            out["mode_toggle_error"] = str(exc)[:200]
        page.wait_for_timeout(8000)
        out["page_url"] = page.url
        out["heading"] = page.locator("h1, h2").first.inner_text()
        cells = page.locator('[title*="unavailable" i]')
        out["cells_with_unavailable_tooltip"] = cells.count()
        out["sample_degraded_cells"] = [
            {"text": cells.nth(i).inner_text().strip(), "title": cells.nth(i).get_attribute("title")}
            for i in range(min(3, cells.count()))]
        body = page.locator("body").inner_text()
        out["error_boundary_text_present"] = any(
            s in body for s in ("Application error", "Unhandled Runtime Error", "Internal Server Error"))
        out["warming_up_banner_present"] = "Warming up" in body
        out["by_label_table_present"] = page.locator('[data-testid="regime-lab-by-label"]').count() > 0
        out["by_decile_table_present"] = page.locator('[data-testid="regime-lab-by-decile"]').count() > 0
        shot = os.path.join(OUT, f"TC-11-{tag}.png")
        page.screenshot(path=shot, full_page=False)
        out["screenshot"] = shot
        t = page.locator('[data-testid="regime-lab-by-label"]')
        if t.count():
            t.first.screenshot(path=os.path.join(OUT, f"TC-11-{tag}-by-label-table.png"))
            out["screenshot_table"] = os.path.join(OUT, f"TC-11-{tag}-by-label-table.png")
        browser.close()
    return out


result = {"asof_requested": ASOF}

# ---- TREATMENT arm first (fault ARMED), because the arm has a precondition the control does not: the
# as-of's cache key must still be a MISS. Running the control first would COMPUTE and CACHE that key,
# after which regime_lab_cached returns the cached clean payload and compute_regime_lab — where the
# fault site lives — is never entered at all. (That is exactly how the first attempt at this capture
# silently disarmed itself.) So: pick a still-uncached as-of under the armed process, prove the degrade
# at the API, screenshot it, and only then disarm and re-shoot the SAME as-of as the control.
result["boot_armed_seconds"] = restart({"TRENDORA_FAULT_INJECT_MEMORY_ERROR": "regime_lab"})
result["ready_wait_armed"] = wait_ready()

candidates = [ASOF] + [d for d in os.environ.get("TC11_ASOF_CANDIDATES", "").split(",") if d]
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

# ---- CONTROL arm (fault DISARMED, SAME as-of). Without it, a screenshot of NA cells cannot be told
# apart from "this as-of has no data anyway".
result["boot_control_seconds"] = restart({"TRENDORA_FAULT_INJECT_MEMORY_ERROR": ""})
result["ready_wait_control"] = wait_ready()
result["api_control"] = api_shape(f"/api/research/regime-lab?view=pooled&as_of={ASOF}")
result["ui_control"] = capture("control-clean")
# the process is already DISARMED here, so nothing downstream inherits a fault-injected backend.

with open(os.path.join(OUT, "tc11-degrade-ui.json"), "w") as fh:
    json.dump(result, fh, indent=1)
print(json.dumps(result, indent=1))
