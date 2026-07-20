#!/usr/bin/env bash
# measure-perf.sh — iter-24 fast-platform item K: the committed perf-measurement harness.
#
# Curl-times WARM latencies for the four J-15 endpoints (GET /api/stocks, /api/stocks/{ticker},
# /api/data, /api/health) and the four J-15 pages (/stocks, /stocks/{ticker}, /data, /evidence — HTTP
# response time as a warm-load proxy; true browser interactivity is verified separately by the
# browser-qa-agent), times ONE bounded K-date backfill job via the existing jobs API, reads the
# additive DB-capacity snapshot off GET /api/data, and appends every measured row to
# reports/perf-budgets.md so the growth/perf slope is visible run-over-run (goal.md J-15/J-16).
#
# Runs against PROD MODE ONLY (scripts/start-backend.sh / scripts/start-frontend.sh — this script does
# NOT start them; bring them up first, UNLESS you pass --boot, see below). `next dev`'s per-route
# compile is not product latency, so this script refuses to measure against a `next dev` frontend (no
# reliable way to detect that from here, so it just documents the requirement — see the header + --help).
#
# iter-5 (J-06 capstone) additions:
#   --boot   TC-1: measure backend cold-boot wall time (process start -> first GET /api/health HTTP
#            200) on the warm committed-seed DB. Off by default (a normal run still expects the
#            backend already warm/running, unchanged). When passed, this script refuses to run if
#            something already answers on the backend port (a cold-boot measurement needs a REAL
#            process start — never stomping a live instance), then launches
#            scripts/start-backend.sh itself and leaves it running afterward so the rest of this
#            script's warm measurements proceed normally against it. The frontend is still never
#            started by this script — bring it up yourself.
#   Also captures the 7 previously-unmeasured pages/endpoints named in goal.md J-06: the Dashboard
#   cluster (/api/dashboard, /api/market-phase, /api/sectors, /api/themes, /api/indexes?full=true,
#   /api/regime-history?full=true, /api/market-phase?full=true — the cross-view chart's own calls),
#   /api/sectors, /api/themes, /api/runs, /api/backtest, /api/watchlist, /api/research/event-study —
#   and their pages (/, /sectors, /themes, /scanner-runs, /backtest, /watchlist,
#   /research/event-study).
#
# Usage:
#   bash scripts/start-backend.sh &
#   bash scripts/start-frontend.sh &
#   # wait for both to answer 200, then:
#   bash scripts/measure-perf.sh [--ticker AAPL] [--backfill-days 5] [--out reports/perf-budgets.md]
#   # OR, to also measure cold-boot (TC-1) and let this script start the backend itself:
#   bash scripts/start-frontend.sh &
#   bash scripts/measure-perf.sh --boot [--out reports/perf-budgets.md]
#
# Every bound/scope this script uses (the backfill window size, the default ticker, the boot poll
# interval/timeout/budget) is a NAMED default below or a flag override — never a bare literal buried
# in logic (goal.md item K's own rule).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Deterministic per-project port fallback (mirrors start-backend.sh / start-frontend.sh / dev.sh).
_port_root="$REPO_ROOT"
[[ "$_port_root" == */incredible_auto_dev ]] && _port_root="${_port_root%/incredible_auto_dev}"
_offset=$(printf '%s' "$_port_root" | sha1sum | cut -c1-4)
_offset=$((16#$_offset % 1000))
BACKEND_PORT="${CHAIN_BACKEND_PORT:-$((8000 + _offset))}"
FRONTEND_PORT="${CHAIN_FRONTEND_PORT:-$((3000 + _offset))}"
BACKEND_URL="http://localhost:${BACKEND_PORT}"
FRONTEND_URL="http://localhost:${FRONTEND_PORT}"

# Named defaults (script-level "config" — no bare literal buried in logic below).
DEFAULT_TICKER="AAPL"
DEFAULT_BACKFILL_DAYS=5
DEFAULT_OUT="$REPO_ROOT/reports/perf-budgets.md"
DEFAULT_BACKFILL_POLL_TIMEOUT_S=120
# iter-5 TC-1: cold-boot measurement bounds. TIMEOUT is this SCRIPT's own safety bound (so a wedged
# boot fails loud instead of polling forever); BUDGET is the PRODUCT's committed ceiling (goal.md
# Success Criteria: "process start -> first GET /api/health HTTP 200 in <= 5 seconds").
DEFAULT_BOOT_TIMEOUT_S=30
DEFAULT_BOOT_POLL_INTERVAL_S=0.1
DEFAULT_BOOT_BUDGET_S=5
# iter-5 TC-2/TC-5/TC-6/TC-9/TC-10/TC-11/TC-12: the generic newly-committed budgets, matching every
# existing non-tiny-payload endpoint/page already on file (e.g. `/api/stocks`/`/api/data` <= 1.5 s;
# `/stocks`/`/data`/`/evidence` <= 3 s) — a single named default, not 11 more hand-copied numbers.
DEFAULT_API_BUDGET_S=1.5
DEFAULT_PAGE_BUDGET_S=3

TICKER="$DEFAULT_TICKER"
BACKFILL_DAYS="$DEFAULT_BACKFILL_DAYS"
OUT_FILE="$DEFAULT_OUT"
SKIP_BACKFILL=0
MEASURE_BOOT=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --ticker) TICKER="$2"; shift 2 ;;
    --backfill-days) BACKFILL_DAYS="$2"; shift 2 ;;
    --out) OUT_FILE="$2"; shift 2 ;;
    --skip-backfill) SKIP_BACKFILL=1; shift ;;
    --boot) MEASURE_BOOT=1; shift ;;
    -h|--help)
      sed -n '2,43p' "$0"
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

if ! command -v jq >/dev/null 2>&1; then
  echo "measure-perf.sh requires jq (JSON parsing) — not found on PATH." >&2
  exit 1
fi

_curl_timed() {
  # $1 = URL. Prints "<seconds> <http_code>" (space-separated) on stdout; the response body is
  # discarded (this is a LATENCY probe, not a content check — /api/data availability etc. read the
  # body separately via a plain curl when a value is actually needed).
  curl -s -o /dev/null -w "%{time_total} %{http_code}" "$1"
}

_require_200() {
  local label="$1" seconds="$2" code="$3"
  if [[ "$code" != "200" ]]; then
    echo "  WARNING: $label returned HTTP $code (expected 200) — recording the timing anyway (${seconds}s)." >&2
  fi
}

echo "== measure-perf.sh — backend :${BACKEND_PORT}, frontend :${FRONTEND_PORT} ==" >&2

# iter-5 TC-1: backend cold-boot wall time (process start -> first GET /api/health HTTP 200) on the
# warm committed-seed DB. Off by default — see --boot in --help.
boot_line="skipped (pass --boot to measure cold-boot-to-health)"
if [[ "$MEASURE_BOOT" -eq 1 ]]; then
  echo "-- TC-1: backend cold-boot timing (process start -> first GET /api/health HTTP 200) --" >&2
  # Refuse to stomp a live instance — a cold-boot measurement needs a REAL process start; if something
  # already answers here, this script would either fail to bind the port or (worse) silently measure
  # the wrong process's startup.
  existing_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 1 "$BACKEND_URL/api/health" 2>/dev/null || echo "000")
  if [[ "$existing_code" == "200" ]]; then
    echo "measure-perf.sh --boot: $BACKEND_URL/api/health already answers 200 — stop the running backend first (this measurement needs a real cold process start)." >&2
    exit 1
  fi
  boot_start=$(date +%s.%N)
  bash "$REPO_ROOT/scripts/start-backend.sh" >/dev/null 2>&1 &
  boot_pid=$!
  boot_code="000"
  boot_deadline=$(( $(date +%s) + DEFAULT_BOOT_TIMEOUT_S ))
  while [[ "$boot_code" != "200" && $(date +%s) -lt $boot_deadline ]]; do
    sleep "$DEFAULT_BOOT_POLL_INTERVAL_S"
    boot_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 0.5 "$BACKEND_URL/api/health" 2>/dev/null || echo "000")
  done
  boot_end=$(date +%s.%N)
  boot_elapsed=$(awk "BEGIN {printf \"%.3f\", $boot_end - $boot_start}")
  if [[ "$boot_code" == "200" ]]; then
    boot_holds=$(awk "BEGIN {print ($boot_elapsed <= $DEFAULT_BOOT_BUDGET_S) ? \"yes\" : \"NO\"}")
    boot_line="**${boot_elapsed}s** (process start -> first HTTP 200), launcher pid ${boot_pid} — holds <= ${DEFAULT_BOOT_BUDGET_S}s budget: ${boot_holds}"
    echo "  boot-to-health: ${boot_elapsed}s (holds <= ${DEFAULT_BOOT_BUDGET_S}s: ${boot_holds})" >&2
  else
    boot_line="FAILED — no HTTP 200 within ${DEFAULT_BOOT_TIMEOUT_S}s of process start (last code: ${boot_code})"
    echo "  measure-perf.sh --boot: $boot_line" >&2
  fi
fi

# Confirm both services are reachable BEFORE measuring (never silently measure a dead endpoint as 0s).
for probe in "$BACKEND_URL/api/health" "$FRONTEND_URL/"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "$probe" || echo "000")
  if [[ "$code" != "200" ]]; then
    echo "measure-perf.sh: $probe did not answer 200 (got $code)." >&2
    echo "Bring up prod mode first: scripts/start-backend.sh and scripts/start-frontend.sh (never dev.sh)." >&2
    exit 1
  fi
done

# One warm-up hit per endpoint/page BEFORE timing (a cold first hit is a DIFFERENT, separately-tracked
# measurement — see reports/perf-budgets.md's Item A section; this script measures the WARM path only).
for warm in "$BACKEND_URL/api/health" "$BACKEND_URL/api/stocks" "$BACKEND_URL/api/stocks/${TICKER}" \
            "$BACKEND_URL/api/data" "$FRONTEND_URL/stocks" "$FRONTEND_URL/stocks/${TICKER}" \
            "$FRONTEND_URL/data" "$FRONTEND_URL/evidence"; do
  curl -s -o /dev/null "$warm" || true
done

echo "-- warm endpoint latencies --" >&2
read -r health_s health_code <<<"$(_curl_timed "$BACKEND_URL/api/health")"
_require_200 "/api/health" "$health_s" "$health_code"
read -r stocks_s stocks_code <<<"$(_curl_timed "$BACKEND_URL/api/stocks")"
_require_200 "/api/stocks" "$stocks_s" "$stocks_code"
read -r detail_s detail_code <<<"$(_curl_timed "$BACKEND_URL/api/stocks/${TICKER}")"
_require_200 "/api/stocks/${TICKER}" "$detail_s" "$detail_code"
read -r data_s data_code <<<"$(_curl_timed "$BACKEND_URL/api/data")"
_require_200 "/api/data" "$data_s" "$data_code"

echo "-- warm page latencies (HTTP response time; browser-qa-agent verifies true interactivity) --" >&2
read -r stocks_page_s stocks_page_code <<<"$(_curl_timed "$FRONTEND_URL/stocks")"
_require_200 "/stocks (page)" "$stocks_page_s" "$stocks_page_code"
read -r detail_page_s detail_page_code <<<"$(_curl_timed "$FRONTEND_URL/stocks/${TICKER}")"
_require_200 "/stocks/${TICKER} (page)" "$detail_page_s" "$detail_page_code"
read -r data_page_s data_page_code <<<"$(_curl_timed "$FRONTEND_URL/data")"
_require_200 "/data (page)" "$data_page_s" "$data_page_code"
read -r evidence_page_s evidence_page_code <<<"$(_curl_timed "$FRONTEND_URL/evidence")"
_require_200 "/evidence (page)" "$evidence_page_s" "$evidence_page_code"

# --- iter-5 (J-06 capstone): the 7 previously-unmeasured pages' backing endpoints + their pages ----
# NAMED endpoint/page maps (label -> URL), measured with the SAME warm-up-then-timed pattern as the
# endpoints above — a loop rather than 18 more hand-copied blocks (TC-2..TC-12 name this many pairs at
# once; this is the 3rd+ occurrence of the identical warm+timed-hit shape). Order is a fixed array
# (bash associative arrays are unordered) so the appended table always reads in the TC-2..TC-12 sequence.
NEW_ENDPOINT_ORDER=(
  "GET /api/dashboard" "GET /api/market-phase" "GET /api/sectors" "GET /api/themes"
  "GET /api/indexes?full=true" "GET /api/regime-history?full=true" "GET /api/market-phase?full=true"
  "GET /api/runs" "GET /api/backtest" "GET /api/watchlist" "GET /api/research/event-study"
)
declare -A NEW_ENDPOINT_URL=(
  ["GET /api/dashboard"]="$BACKEND_URL/api/dashboard"
  ["GET /api/market-phase"]="$BACKEND_URL/api/market-phase"
  ["GET /api/sectors"]="$BACKEND_URL/api/sectors"
  ["GET /api/themes"]="$BACKEND_URL/api/themes"
  ["GET /api/indexes?full=true"]="$BACKEND_URL/api/indexes?full=true"
  ["GET /api/regime-history?full=true"]="$BACKEND_URL/api/regime-history?full=true"
  ["GET /api/market-phase?full=true"]="$BACKEND_URL/api/market-phase?full=true"
  ["GET /api/runs"]="$BACKEND_URL/api/runs"
  ["GET /api/backtest"]="$BACKEND_URL/api/backtest"
  ["GET /api/watchlist"]="$BACKEND_URL/api/watchlist"
  # the real first-load call: no subject/horizon (backend picks the default) — `view=episodes` is the
  # page's own initial state (apps/frontend/app/research/_labs.tsx's EventStudyLab effect).
  ["GET /api/research/event-study"]="$BACKEND_URL/api/research/event-study?view=episodes"
)
NEW_PAGE_ORDER=(
  "/ (Dashboard)" "/sectors" "/themes" "/scanner-runs" "/backtest" "/watchlist" "/research/event-study"
)
declare -A NEW_PAGE_URL=(
  ["/ (Dashboard)"]="$FRONTEND_URL/"
  ["/sectors"]="$FRONTEND_URL/sectors"
  ["/themes"]="$FRONTEND_URL/themes"
  ["/scanner-runs"]="$FRONTEND_URL/scanner-runs"
  ["/backtest"]="$FRONTEND_URL/backtest"
  ["/watchlist"]="$FRONTEND_URL/watchlist"
  ["/research/event-study"]="$FRONTEND_URL/research/event-study"
)

echo "-- iter-5: warm-up hits (the 11 not-yet-measured endpoints/pages) --" >&2
for label in "${NEW_ENDPOINT_ORDER[@]}"; do curl -s -o /dev/null "${NEW_ENDPOINT_URL[$label]}" || true; done
for label in "${NEW_PAGE_ORDER[@]}"; do curl -s -o /dev/null "${NEW_PAGE_URL[$label]}" || true; done

echo "-- iter-5: warm endpoint latencies (TC-2, TC-5, TC-6, TC-9, TC-10, TC-11, TC-12) --" >&2
declare -A NEW_ENDPOINT_RESULT=()
for label in "${NEW_ENDPOINT_ORDER[@]}"; do
  read -r seconds code <<<"$(_curl_timed "${NEW_ENDPOINT_URL[$label]}")"
  _require_200 "$label" "$seconds" "$code"
  NEW_ENDPOINT_RESULT["$label"]="${seconds}|${code}"
done

echo "-- iter-5: warm page latencies (HTTP response time; the browser-qa lane verifies true interactivity) --" >&2
declare -A NEW_PAGE_RESULT=()
for label in "${NEW_PAGE_ORDER[@]}"; do
  read -r seconds code <<<"$(_curl_timed "${NEW_PAGE_URL[$label]}")"
  _require_200 "$label (page)" "$seconds" "$code"
  NEW_PAGE_RESULT["$label"]="${seconds}|${code}"
done

echo "-- DB capacity snapshot (from GET /api/data's additive 'capacity' field) --" >&2
data_body=$(curl -s "$BACKEND_URL/api/data")
db_file_bytes=$(echo "$data_body" | jq -r '.capacity.db_file_bytes')
daily_prices_rows=$(echo "$data_body" | jq -r '.capacity.daily_prices_rows')
scanner_results_rows=$(echo "$data_body" | jq -r '.capacity.scanner_results_rows')
forward_returns_rows=$(echo "$data_body" | jq -r '.capacity.forward_returns_rows')

backfill_line="skipped (--skip-backfill)"
if [[ "$SKIP_BACKFILL" -eq 0 ]]; then
  echo "-- bounded ${BACKFILL_DAYS}-date backfill timing (via the jobs API) --" >&2
  gap_first=$(echo "$data_body" | jq -r '.coverage.gap_first // empty')
  gaps_preview_last=$(echo "$data_body" | jq -r ".coverage.gaps_preview[${BACKFILL_DAYS}-1]? // .coverage.gaps_preview[-1]? // empty")
  price_end=$(echo "$data_body" | jq -r '.coverage.price_end // empty')

  if [[ -n "$gap_first" && -n "$gaps_preview_last" ]]; then
    backfill_start="$gap_first"
    backfill_end="$gaps_preview_last"
    backfill_kind_note="a real backfill gap"
  elif [[ -n "$price_end" ]]; then
    backfill_start=$(date -d "$price_end - ${BACKFILL_DAYS} days" +%Y-%m-%d)
    backfill_end="$price_end"
    backfill_kind_note="the trailing ${BACKFILL_DAYS} days (no gap on this DB — an idempotent no-op backfill; still a real, honest timing)"
  else
    echo "  no price data yet on this backend — skipping the backfill timing." >&2
    backfill_start=""
  fi

  if [[ -n "${backfill_start:-}" ]]; then
    job_body=$(curl -s -X POST "$BACKEND_URL/api/data/jobs" \
      -H "Content-Type: application/json" \
      -d "{\"kind\":\"backfill\",\"start\":\"${backfill_start}\",\"end\":\"${backfill_end}\"}")
    job_id=$(echo "$job_body" | jq -r '.job_id // empty')
    if [[ -z "$job_id" ]]; then
      echo "  WARNING: backfill job did not start (response: $job_body)." >&2
      backfill_line="job failed to start"
    else
      start_ts=$(date +%s.%N)
      status="running"
      deadline=$(( $(date +%s) + DEFAULT_BACKFILL_POLL_TIMEOUT_S ))
      while [[ "$status" == "running" && $(date +%s) -lt $deadline ]]; do
        sleep 0.2
        poll_body=$(curl -s "$BACKEND_URL/api/data/jobs/${job_id}")
        status=$(echo "$poll_body" | jq -r '.status // "running"')
      done
      end_ts=$(date +%s.%N)
      elapsed=$(awk "BEGIN {printf \"%.2f\", $end_ts - $start_ts}")
      dates_total=$(echo "$poll_body" | jq -r '.dates_total // 0')
      snapshots_created=$(echo "$poll_body" | jq -r '.snapshots_created // 0')
      # `coverage.gaps_preview` lists every trading day with bars-but-no-snapshot -- but the backfill
      # job itself only targets CADENCE-ELIGIBLE dates in range (sparser for deep history; the coverage
      # gap list is not cadence-filtered). So a "real gap" pick can still legitimately resolve to 0
      # eligible dates on an already-fully-warmed backend -- report what ACTUALLY happened, not the
      # a-priori guess.
      if [[ "$dates_total" == "0" ]]; then
        backfill_kind_note="0 cadence-eligible dates in this exact range (the coverage gap list is not cadence-filtered; this backend's cadence is already fully warm) -- an honest no-op, not a failure"
      fi
      backfill_line="${backfill_start} → ${backfill_end} (${backfill_kind_note}): status=${status}, ${dates_total} date(s) covered, ${snapshots_created} snapshot(s) created, ${elapsed}s wall time"
    fi
  fi
fi

timestamp="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
host_info="$(uname -srm 2>/dev/null || echo unknown)"

{
  echo ""
  # iter-5: this title used to hardcode "(iter-24)" regardless of which iteration actually ran the
  # script, so every re-run silently mislabeled its own fresh measurements as iter-24's (iter-25's own
  # dev handoff had to work around this by transcribing to a scratch file instead of appending
  # directly). Fixed here: the title now carries the real measurement timestamp instead of a frozen
  # iteration number — the "items B/C/D/G/H/K" methodology reference is historical and stays accurate.
  echo "## Mechanical backend + page pass — items B/C/D/G/H/K methodology, re-measured $timestamp"
  echo ""
  echo "Measured $timestamp on this host ($host_info) via \`scripts/measure-perf.sh\` against PROD MODE"
  echo "(\`start-backend.sh\`/\`start-frontend.sh\`, backend :${BACKEND_PORT} / frontend :${FRONTEND_PORT})."
  echo ""
  echo "**Warm endpoint latencies:**"
  echo ""
  echo "| Endpoint | Wall time | Budget |"
  echo "|---|---|---|"
  echo "| \`GET /api/health\` | ${health_s}s | ≤ 0.1 s |"
  echo "| \`GET /api/stocks\` | ${stocks_s}s | ≤ 1.5 s |"
  echo "| \`GET /api/stocks/${TICKER}\` | ${detail_s}s | ≤ 0.3 s |"
  echo "| \`GET /api/data\` | ${data_s}s | ≤ 1.5 s |"
  echo ""
  echo "**Warm page latencies (HTTP response time; the browser-qa lane verifies true interactivity):**"
  echo ""
  echo "| Page | Wall time | Budget |"
  echo "|---|---|---|"
  echo "| \`/stocks\` | ${stocks_page_s}s | ≤ 3 s |"
  echo "| \`/stocks/${TICKER}\` | ${detail_page_s}s | ≤ 3 s |"
  echo "| \`/data\` | ${data_page_s}s | ≤ 3 s |"
  echo "| \`/evidence\` | ${evidence_page_s}s | ≤ 3 s |"
  echo ""
  echo "**DB capacity snapshot** (item K; from \`GET /api/data\`'s additive \`capacity\` field):"
  echo ""
  echo "| Metric | Value |"
  echo "|---|---|"
  echo "| DB file size | ${db_file_bytes} bytes |"
  echo "| \`daily_prices\` rows | ${daily_prices_rows} |"
  echo "| \`scanner_results\` rows | ${scanner_results_rows} |"
  echo "| \`forward_returns\` rows | ${forward_returns_rows} |"
  echo ""
  echo "**Bounded backfill timing** (item K harness; \`--backfill-days ${BACKFILL_DAYS}\`): ${backfill_line}"
  echo ""
} >> "$OUT_FILE"

# iter-5 (J-06 capstone): a SEPARATE, freshly-dated section for the boot timing + the 7
# previously-unmeasured pages — appended to the SAME file (TC-15: no second budgets artifact anywhere).
{
  echo ""
  echo "## J-06 capstone — boot-to-health + the 7 previously-unmeasured pages (iter-5)"
  echo ""
  echo "Measured $timestamp on this host ($host_info) via \`scripts/measure-perf.sh\` (extended this"
  echo "iteration) against PROD MODE (\`start-backend.sh\`/\`start-frontend.sh\`, backend"
  echo ":${BACKEND_PORT} / frontend :${FRONTEND_PORT})."
  echo ""
  echo "**TC-1 — backend cold-boot wall time (process start -> first \`GET /api/health\` HTTP 200):**"
  echo ""
  echo "${boot_line}"
  echo ""
  echo "**Warm endpoint latencies (TC-2, TC-5, TC-6, TC-9, TC-10, TC-11, TC-12 — generic <= ${DEFAULT_API_BUDGET_S}s"
  echo "API budget, matching this file's existing \`/api/stocks\`/\`/api/data\` budgets):**"
  echo ""
  echo "| Endpoint | Wall time | Budget | Holds? |"
  echo "|---|---|---|---|"
  for label in "${NEW_ENDPOINT_ORDER[@]}"; do
    IFS='|' read -r seconds code <<<"${NEW_ENDPOINT_RESULT[$label]}"
    holds=$(awk "BEGIN {print ($seconds <= $DEFAULT_API_BUDGET_S) ? \"yes\" : \"NO\"}")
    echo "| \`${label}\` | ${seconds}s | <= ${DEFAULT_API_BUDGET_S} s | ${holds} (HTTP ${code}) |"
  done
  echo ""
  echo "**Warm page latencies (HTTP response time; the browser-qa lane verifies true interactivity —"
  echo "TC-2's Dashboard TTI budget is <= 3 s; the rest share the generic <= ${DEFAULT_PAGE_BUDGET_S}s page budget):**"
  echo ""
  echo "| Page | Wall time | Budget | Holds? |"
  echo "|---|---|---|---|"
  for label in "${NEW_PAGE_ORDER[@]}"; do
    IFS='|' read -r seconds code <<<"${NEW_PAGE_RESULT[$label]}"
    holds=$(awk "BEGIN {print ($seconds <= $DEFAULT_PAGE_BUDGET_S) ? \"yes\" : \"NO\"}")
    echo "| \`${label}\` | ${seconds}s | <= ${DEFAULT_PAGE_BUDGET_S} s | ${holds} (HTTP ${code}) |"
  done
  echo ""
} >> "$OUT_FILE"

echo "== appended measurements to $OUT_FILE ==" >&2
