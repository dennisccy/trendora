# Phase goal-i_can_see_the_wealthy_future_forever-iter-21 — UI Test Results

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-21 (J-33 — Import source picker)
**Date:** 2026-06-05
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** FAIL

<!-- FAIL: a P1 test (UT-08) fails on the principal anti-goal — the pasted session-only key is echoed back
     in the GET /api/data/jobs/{id} response and rendered in the UI job-card error list. -->

**Overall:** 12/13 tests passed, **1 failed (UT-08, P1)**, 0 skipped.

> **Headline:** The J-33 import-source picker, availability line, session-key field, up-front key-required
> rejection, default-source preservation, subtitle fix, and the J-18 "one date selector" guarantee all work
> as designed. **However, a single critical defect fails the principal anti-goal:** when a fetch fails
> against a key-in-URL provider (Tiingo/Finnhub/Alpha Vantage), the provider's HTTP error message embeds the
> request URL **including the pasted key as a `?token=…` query parameter**, and that message is **echoed back
> in `GET /api/data/jobs/{id}` and rendered in the Job-progress error list**. The anti-goal requires the key
> be *"never echoed back in any response"*. Persistence layers (DB, run log, disk, committed files) and the
> frontend (memory-only, masked, no storage, cleared on completion) are all clean — the leak is purely the
> backend echoing the key inside error strings.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Data Manager loads | smoke | P1 | Heading + coverage card (6 metrics) + fetch card + Job-progress "No job…" card, no backend error | All present; health badge cleared; no error card | **PASS** | `UT-01-data-manager-loaded.png` |
| UT-02 | Import source shows for fetch only | happy-path | P1 | No source select for backfill; switching to fetch reveals it with the 5-source config catalog + availability suffixes | Confirmed; source appears between Job-kind and Start; options = Yahoo Finance·available, Tiingo/Finnhub/Alpha Vantage/Stooq·needs key; default=yahoo | **PASS** | `UT-02-import-source-fetch.png` |
| UT-03 | Import source shows for "Fetch + backfill" | happy-path | P1 | Source select + availability line visible for `both` | Backfill hides both; `both` shows both (toggle correct) | **PASS** | (DOM-verified) |
| UT-04 | Availability line reflects source | happy-path | P1 | Yahoo → "available" green + reason; Tiingo → "needs key" amber + env-var reason; text changes per source | Yahoo: "Yahoo Finance: available · no key required" green `rgb(52,211,153)`; Tiingo: "Tiingo: needs key · set $TIINGO_API_KEY…" amber `rgb(251,191,36)` | **PASS** | (DOM-verified) |
| UT-05 | Session key field appears for needs-key | happy-path | P1 | Masked field + "Session API key for Tiingo" label + exact caption + "or set $TIINGO_API_KEY" placeholder; absent for Yahoo | All exact matches; absent for Yahoo; reappears empty on return | **PASS** | `UT-05-tiingo-session-key-field.png` |
| UT-06 | Key masked, never pre-filled | validation | P2 | Field empty initially; typed value masked (type=password), not plaintext | Initial empty; DOM value=typed, type=password, plaintext absent from rendered text | **PASS** | (DOM-verified) |
| UT-07 | Needs-key blank key rejected up front | validation | P2 | Inline `role="alert"` + warn icon naming the source/env var; no job starts; key not echoed | "source 'tiingo' requires a key; set $TIINGO_API_KEY or paste a session key" + svg icon; "No job has been started"; no echo | **PASS** | `UT-07-blank-key-rejected.png` |
| UT-08 | Walled fetch → explicit error, **no key echoed** | error | **P1** | Failed/partial badge, error box "(no data fabricated)", failures + 0 bars, **no API key string anywhere in the job card** | Honest-error path correct (status=failed, "20 errors (no data fabricated)", 158/158 0 ok 158 failed, 0 new bars, header echoes `tiingo`) **BUT pasted key `?token=<key>` echoed in 20 error lines (job card + API response)** | **FAIL** | `UT-08-FAIL-key-leak-in-job-card-errors.png` |
| UT-09 | Header echoes source id, never a key | ux | P2 | Fetch header `… · <source> · …`; backfill omits source segment | Fetch header echoes `tiingo`/`yahoo` and shows **no key in the hint** (PASS); **but backfill header does NOT omit the source — shows `… · yahoo · …`** (deviation — see Finding #2) | **PASS\*** | (DOM-verified) |
| UT-10 | Backfill hides source/key, still runs (J-17) | regression | **P1** | No source/key controls; backfill runs to terminal; header `backfill job · <start> → <end>` with **no** source segment | Controls hidden ✓; ran end-to-end ✓ (status ok, 5 snapshots/5 dates, 3200 fwd returns — J-17 intact); **header shows `backfill job · yahoo · …`** (source segment NOT omitted — Finding #2) | **PASS\*** | (DOM-verified) |
| UT-11 | Default source preselected (J-17) | regression | P2 | Source pre-selected to first catalog entry (Yahoo) with no manual selection; unchanged fetch runs `yahoo` | Fresh fetch-switch defaults to `yahoo`; live Yahoo fetch header echoed `yahoo` without manual selection | **PASS** | (DOM-verified) |
| UT-12 | Subtitle wording fix | regression | P3 | Subtitle ends "…grow the Backtest evidence."; no "System Health evidence" | "…new snapshot dates become selectable in the global as-of switcher and grow the Backtest evidence." — "System Health evidence" absent | **PASS** | (DOM-verified) |
| UT-13 | Exactly one date select (J-18) | regression | **P1** | Exactly 1 date `<select>` app-wide (header as-of); Start/End are `type=date` inputs; source/kind selects are not date controls | 1 date select ("View as-of date"); Job kind + Import source are non-date selects; Start/End are `type=date` inputs — J-18 intact | **PASS** | (DOM-verified) |

\* **PASS with documented deviation** — see Finding #2 (backfill header source segment). The verdict-relevant
core of each test passes (UT-09: header echoes source and never shows a key; UT-10: J-17 backfill regression intact).

---

## Failed Tests

### UT-08 — Walled fetch surfaces an explicit error, but **leaks the pasted session key** (🔴 CRITICAL — anti-goal violation)

**Verdict:** FAIL (P1)
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-21-evidence/UT-08-FAIL-key-leak-in-job-card-errors.png`

**Steps taken:**
1. On `/data`, set Job kind → "Fetch EOD prices", Import source → "Tiingo · needs key".
2. Typed a known sentinel session key `QA21_SECRET_d4e9f7a2` into the masked "Session API key" field (held in React memory, masked, absent from body text — verified).
3. Clicked **Start**. Job ran against Tiingo (no env key; the pasted session key was used for the request).
4. Job reached terminal status `failed` (158/158 symbols, 0 ok, 158 failed). Tiingo returns `403 Forbidden` per symbol.
5. Inspected the rendered Job-progress card, `GET /api/data/jobs/{id}`, the DB, and the backend log for the sentinel.

**What PASSED within UT-08 (the honest-error machinery is correct):**
- Header hint echoes the chosen source id: `fetch job · tiingo · 2021-01-04 → 2021-01-08`.
- Status badge = **failed** (not "ok").
- Error box present: **"20 errors (no data fabricated)"**.
- "Symbols fetched 158/158 (0 ok, 158 failed)" and **"0 new price bars"** — **no fabricated bars** (the "No fabricated data" / "Live fetch is real-data-only" anti-goals hold).

**Expected (the failing assertion):** *"No API key string appears anywhere in the job card"* (UT-08), and per the
phase spec — DoD: *"the pasted key is not echoed back"*; Testing req: *"assert the key string is absent from …
`GET /api/data/jobs/{id}` …"*; Anti-goal: a pasted key is held in memory for the run only and *"never written to
disk, the run log, the DB, or any committed file, **and never echoed back in any response**."*

**Actual (the violation):** The pasted session key is **echoed back** in the per-symbol error messages. Each of
the 20 surfaced errors reads (verbatim):

```
NVDA: tiingo request failed for 'NVDA': Client error '403 Forbidden' for url
'https://api.tiingo.com/tiingo/daily/NVDA/prices?token=QA21_SECRET_d4e9f7a2&format=json&startDate=2021-01-04&endDate=2021-01-08'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/403
```

The key `QA21_SECRET_d4e9f7a2` appears as `?token=QA21_SECRET_d4e9f7a2`:
- **In the UI job-card error list** — rendered as visible `<li>` text **and** stored in each `<li>`'s `title` attribute.
- **In `GET /api/data/jobs/{id}`** — `errors` array, all 20 entries contain the key (`SENTINEL in full JSON response: True`).

#### Leak map (where the key did / did not appear)

| Surface | Leaked? | Evidence |
|--------|:------:|----------|
| UI Job-progress error list (text + `<li> title`) | 🔴 **YES** | `UT-08-FAIL-key-leak-in-job-card-errors.png`; tree-walk found key in 5 visible `<li>` + their `title` attrs |
| `GET /api/data/jobs/{id}` → `errors[]` | 🔴 **YES** | 20/20 errors contain the key; `SENTINEL in full JSON response: True` |
| `GET /api/data` (overview, incl. `sources`) | ✅ no | `SENTINEL count in GET /api/data: 0` |
| DB `data_provider_runs` (all columns incl. `message` JSON) | ✅ no | latest tiingo row id=6 `message` = summary only; full-table `LIKE` scan = **0 rows** |
| Backend run log (`/tmp/fanout-backend-8835.log`) | ✅ no | `grep -c` = **0** |
| Repo / committed files | ✅ no | repo-wide scan (excl. node_modules/.next/.git) = nothing |
| Frontend storage (localStorage / sessionStorage / cookies) | ✅ no | all empty of the key; only cookie is Next.js HMR hash |
| Header hint (`PanelTitle`) | ✅ no | shows source id only, never the key |
| Session key `<input>` | ✅ masked, cleared | `type=password`; value cleared to `""` on job completion |

#### Root cause (for the developer — not fixed by QA)

- `apps/backend/app/data_providers/tiingo_provider.py:46` builds `params = {"token": self._api_key, "format": "json"}` — the key travels as a URL query parameter.
- `apps/backend/app/data_providers/_http.py` `fetch_json()` wraps any transport/status error as
  `raise ProviderUnavailableError(f"{label} request failed for {symbol!r}: {exc}")`. For an `httpx.HTTPStatusError`,
  `str(exc)` **includes the full request URL** — i.e. `…?token=<key>…`. The key is thereby embedded in the
  `ProviderUnavailableError` message, which flows into `JobProgress.errors` → `GET /api/data/jobs/{id}` → the UI.
- This is **systemic** to every key-in-URL provider added in J-33: Tiingo (`?token=`), Finnhub (`?token=`),
  Alpha Vantage (`?apikey=`). Any of them will leak the pasted key on a failed fetch via the same shared helper.

**Suggested direction (advisory):** redact the key/query string in provider error messages before raising
(e.g. sanitize the URL or scrub the configured env-var/token value out of `{exc}` in `_http.py`), and/or pass the
key via an HTTP header instead of a query param where the provider supports it. The job-error pipeline should also
treat error strings as untrusted for secrets before persisting/serving them.

**Severity:** Critical — directly violates the iteration's **principal** anti-goal ("Import keys are env-or-session,
never persisted … and never echoed back in any response") and two explicit Definition-of-Done / Testing items.

---

## Secondary Finding (non-failing, but a documented deviation)

### Finding #2 — Backfill (and any source-omitted) job's header shows the **default** source `yahoo` instead of omitting it (Medium)

**Affects:** UT-09 (backfill sub-assertion) and UT-10 (header sub-assertion). Both tests' **core** purposes pass,
so they are recorded PASS\*; this is the one unmet sub-bullet in each.

**Observed:** A backfill-only job (no source selected; the source/key controls are correctly hidden for backfill)
renders the Job-progress header as **`backfill job · yahoo · 2021-01-04 → 2021-01-08`**. The UI test plan (UT-10)
and surface map (UT-09) expect a backfill-only job to **omit** the source segment: `backfill job · <start> → <end>`.

**Root cause:** `apps/backend/app/api/data.py:75` does `source = payload.source or cfg.data_manager.default_source`,
applying the `yahoo` default to **every** job kind (including backfill, for which the frontend deliberately sends no
source). `create_job` stores that defaulted `source` on the in-memory `JobProgress`, and the header
(`page.tsx:469` `job.source ? … : ""`) then renders it. The frontend rendering logic is correct (it *would* omit an
empty source) — the backend just never leaves it empty.

**Why it's not verdict-failing:** purely a cosmetic/labelling inaccuracy in the *live* header. It is **not** an
anti-goal or J-17 regression: the backfill ran correctly (5 snapshots), no key/fabrication/second-date-control is
involved, and the **persisted** `data_provider_runs` row for the backfill correctly records `provider='seed'`
(not `yahoo`) — so the misleading `yahoo` exists only in the transient job header, never in the DB.

**Suggested direction (advisory):** don't default `source` for non-fetch kinds (leave `JobProgress.source = None`
for backfill), or suppress the header source segment when the kind doesn't fetch.

---

## Passed Tests (summary)

- **UT-01 (PASS):** `/data` loads fully hydrated — "Data Manager" heading, "Dataset coverage" card with all 6 metrics (PRICE HISTORY 2021-01-04→2026-05-28, UNIVERSE 122, SYMBOLS 158, TRADING DAYS 1356, SNAPSHOT DATES 12, BACKFILL GAPS 1344), the fetch/backfill card, and "Job progress — No job has been started this session." No backend-unavailable card; health badge cleared.
- **UT-02 (PASS):** Backfill shows no source control; switching to "Fetch EOD prices" reveals the **config-driven** Import-source select (between Job kind and Start) listing exactly the 5 catalog sources, each suffixed `· available` / `· needs key`, default-selected to `yahoo`. (Options use the full config labels, e.g. "Yahoo Finance"; order follows the config catalog — exactly the "from config" requirement.)
- **UT-03 (PASS):** Round-trip backfill→both confirms the toggle: backfill hides source + availability line; `both` shows them.
- **UT-04 (PASS):** Availability line is dynamic — Yahoo "available" in green `rgb(52,211,153)` (+ "no key required"); Tiingo "needs key" in amber `rgb(251,191,36)` (+ "set $TIINGO_API_KEY or paste a session key"); text updates on source change.
- **UT-05 (PASS):** Tiingo reveals a masked `type=password` field, aria-label "Session API key", label "Session API key for Tiingo", placeholder "or set $TIINGO_API_KEY", and the exact caption "Held in memory for this run only — never written to disk, the database, the run log, or a cookie, and never echoed back." Yahoo hides it; switching back re-shows it empty.
- **UT-06 (PASS):** Field initially empty (not server-prefilled); typed `test-secret-123` is held in the DOM value but rendered masked (type=password) and absent from rendered body text.
- **UT-07 (PASS):** Tiingo + blank key + Start → inline `role="alert"` "source 'tiingo' requires a key; set $TIINGO_API_KEY or paste a session key" with a warning-triangle svg; **no job started**; key not echoed. (Up-front client/`400`-gate rejection.)
- **UT-09 (PASS\*):** Fetch header echoes the source id (`fetch job · tiingo · …`, `fetch job · yahoo · …`) and the header hint never contains a key. *(Backfill-omits-source sub-point deviates — Finding #2.)*
- **UT-10 (PASS\*):** Backfill hides the source/key controls and **runs end-to-end (J-17 intact)** — status ok, 5 snapshots over 5 dates, 3200 forward returns. *(Header source-segment sub-point deviates — Finding #2.)*
- **UT-11 (PASS):** On a fresh fetch-switch the Import source is pre-selected to the first catalog entry `yahoo` (the config `default_source`) with no manual selection; a Yahoo fetch ran with the header echoing `yahoo` un-prompted — preserving prior single-provider behavior.
- **UT-12 (PASS):** Subtitle reads "…new snapshot dates become selectable in the global as-of switcher and grow the **Backtest** evidence." The stale "System Health evidence" phrase is gone.
- **UT-13 (PASS):** Exactly **one** date `<select>` app-wide — the global header "View as-of date" switcher. Job kind and Import source are non-date selects; "Job start date"/"Job end date" are `type=date` job-parameter inputs. The J-33 source/key controls add **no** date state — **J-18 not regressed**.

---

## Notes on test execution

- **Native-setter pattern:** every `<select>` change (Job kind, Import source) used the native value setter +
  bubbling `change` event, then asserted against the live DOM, per MEMORY `react-controlled-select-needs-native-setter`.
  The Chrome MCP `select` action does not fire React's `onChange` on this frontend.
- **Stale-tab state (no defect):** the first `/data` load showed leftover form state (fetch/tiingo + a pre-filled
  key field) from a previously-open browser tab kept alive by the persistent Chrome session. A genuine fresh load
  (navigate away → back) reset to the correct default (backfill, no source/key controls) with **empty** localStorage,
  sessionStorage, and no key cookie — confirming the app does **not** persist form/key state. Not a bug.
- **UT-08 provider substitution (rationale):** The plan's UT-08 uses Yahoo, but Yahoo currently returns slow
  empty-200 responses on this IP (≈10–20 s/symbol, "ok" with 0 bars — no error), so across 158 symbols it neither
  reaches a terminal *error* state nor exercises the honest-error contract within a QA window (it would take ≈30–50 min
  and likely end "ok, 0 bars"). The honest-error contract (and the key-leak anti-goal) was therefore exercised with a
  **genuinely-erroring** provider — Tiingo + a sentinel session key (403 per symbol, terminal in <1 min). This matches
  the test plan's environment caveat (a successful/clean live fetch is not autonomously reachable; validate the honest
  error/unavailable path). The Yahoo attempt's running-state evidence (header `fetch job · yahoo · …`, 0 fabricated
  bars) was captured and supports UT-09/UT-11.
- **Concurrent-job model:** the backend `_JOBS` registry has no single-job guard (the "Job running…" lock is
  frontend-only); reloading `/data` frees the Start button. The slow Yahoo attempt continued harmlessly server-side
  (0 writes) while later tests ran.

---

## Environment

- **Frontend URL:** http://localhost:3835
- **Backend:** http://localhost:8835 (`/api/data` healthy; note: there is no `/health` route — returns 404, not a defect)
- **Browser:** Chrome via `mcp__plugin_superpowers-chrome_chrome__use_browser` (Chrome DevTools Protocol)
- **Test Date:** 2026-06-05
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-21-evidence/`
  - `UT-01-data-manager-loaded.png`, `UT-02-import-source-fetch.png`, `UT-05-tiingo-session-key-field.png`,
    `UT-07-blank-key-rejected.png`, `UT-08-FAIL-key-leak-in-job-card-errors.png`
- **Backend log inspected:** `/tmp/fanout-backend-8835.log` (the running backend's stdout/stderr; the path named in
  the task note, `/tmp/browser-qa-backend-8835.log`, did not exist in this run).
</content>
</invoke>
