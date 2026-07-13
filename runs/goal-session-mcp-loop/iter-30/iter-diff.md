# Iteration diff (bounded)

Files changed: 15. Shown in full: 15.

```diff
diff --git a/apps/backend/app/config.py b/apps/backend/app/config.py
index a153bca..e7fc890 100644
--- a/apps/backend/app/config.py
+++ b/apps/backend/app/config.py
@@ -2101,24 +2101,52 @@ class FdrCfg(BaseModel):
         return self
 
 
+_DEFAULT_REGISTRY_PATH = "runs/goal-session-mcp-loop/state/pre-registrations.jsonl"
+
+
+class RegistryCfg(BaseModel):
+    """The pre-registration registry config (goal-mcp-loop iter-30; J-18 / backlog B-901). `path` is the
+    append-only `state/pre-registrations.jsonl` BOTH `GET /api/research/registry` (via
+    `app.engine.registry`) and the post-decompose gate (`verify_claim.py`, a non-HTTP consumer) read
+    through the SAME loader module (`app.engine.registry.load_registrations`) — so the registry page a
+    human browses and the machine cross-check an incoming Evidence Claim runs through can never disagree.
+    Resolved relative to `REPO_ROOT` when relative; the resolver (`app.engine.registry.resolve_registry_
+    path`, NOT this model) applies the runtime `TRENDORA_REGISTRY_PATH` override, mirroring
+    `EvidenceCfg.ledger_path` / `resolve_ledger_path()` exactly.
+
+    `enforce` is DEFAULT-OFF in code (mirrors `FdrCfg.enabled=False`) so a config / inline test fixture
+    predating this block still loads and behaves byte-identically: with `enforce=False` the gate's
+    registry cross-check is skipped entirely (the exact pre-iter-30 behavior). The real `config.yaml`
+    flips this to `true` ONLY after the backfill is verified complete (B-901's own sequencing — see the
+    dev handoff) — never before, and never as a formality (Critical Implementation Detail in the iter-30
+    plan)."""
+
+    model_config = ConfigDict(extra="allow")
+    path: str = Field(default=_DEFAULT_REGISTRY_PATH, min_length=1)
+    enforce: bool = False
+
+
 class EvidenceCfg(BaseModel):
-    """Read-side evidence config (goal-mcp-loop iter-1; iter-9 adds the staging economy). `ledger_path` is
-    the certified-claims ledger the read-only `GET /api/evidence` reads — the SAME append-only file the
-    post-decompose gate writes, so the UI's displayed proven-ness is consistent with what the referee
-    certified. Resolved relative to `REPO_ROOT` when relative; the resolver
-    (`app.engine.evidence.resolve_ledger_path`, NOT this model) applies the runtime `TRENDORA_LEDGER_PATH`
-    override. The path lives in config, never as a literal in the resolver/endpoint (anti-goal: No magic
-    numbers).
+    """Read-side evidence config (goal-mcp-loop iter-1; iter-9 adds the staging economy; iter-30 adds the
+    pre-registration registry). `ledger_path` is the certified-claims ledger the read-only `GET
+    /api/evidence` reads — the SAME append-only file the post-decompose gate writes, so the UI's displayed
+    proven-ness is consistent with what the referee certified. Resolved relative to `REPO_ROOT` when
+    relative; the resolver (`app.engine.evidence.resolve_ledger_path`, NOT this model) applies the runtime
+    `TRENDORA_LEDGER_PATH` override. The path lives in config, never as a literal in the resolver/endpoint
+    (anti-goal: No magic numbers).
 
     iter-9 adds the INTERNAL exploration seam — `staging_ledger_path` (a NEVER-served staging ledger the
     online-FDR economy explores in, so exploration cannot tighten the canonical Bonferroni bar) and `fdr`
-    (the DEFAULT-OFF LORD++ economy config). Both are default-populated so a config / inline test fixture
-    predating this block still loads unchanged, and default-off keeps canonical behavior byte-identical."""
+    (the DEFAULT-OFF LORD++ economy config). iter-30 adds `registry` (the DEFAULT-OFF pre-registration
+    gate cross-check config, `RegistryCfg`). All three are default-populated so a config / inline test
+    fixture predating any of these blocks still loads unchanged, and default-off keeps canonical/pre-
+    existing behavior byte-identical."""
 
     model_config = ConfigDict(extra="allow")
     ledger_path: str = Field(default=_DEFAULT_LEDGER_PATH, min_length=1)
     staging_ledger_path: str = Field(default=_DEFAULT_STAGING_LEDGER_PATH, min_length=1)
     fdr: FdrCfg = Field(default_factory=FdrCfg)
+    registry: RegistryCfg = Field(default_factory=RegistryCfg)
 
 
 def _default_evidence() -> "EvidenceCfg":
diff --git a/apps/backend/main.py b/apps/backend/main.py
index 6cc91ee..915a6c8 100644
--- a/apps/backend/main.py
+++ b/apps/backend/main.py
@@ -25,6 +25,7 @@ from app.api import (
     market_phase,
     methodology,
     regime_history,
+    registry,
     research,
     runs,
     sectors,
@@ -130,6 +131,8 @@ def create_app() -> FastAPI:
     application.include_router(market_phase.router, prefix="/api")
     # goal-mcp-loop iter-1 — the read-only certified-claims ledger surface (GET /api/evidence).
     application.include_router(evidence.router, prefix="/api")
+    # goal-mcp-loop iter-30 (J-18) — the read-only pre-registration registry (GET /api/research/registry).
+    application.include_router(registry.router, prefix="/api")
     return application
 
 
diff --git a/apps/backend/tests/test_config.py b/apps/backend/tests/test_config.py
index 49cfffd..5c5fb00 100644
--- a/apps/backend/tests/test_config.py
+++ b/apps/backend/tests/test_config.py
@@ -883,3 +883,35 @@ def test_malformed_fdr_block_in_full_config_raises(tmp_path):
     }
     with pytest.raises(ConfigError):
         load_config(_write(tmp_path, data))
+
+
+# ==================================================================================================
+# iter-30 — the pre-registration registry config (evidence.registry.{path,enforce}; J-18 / backlog B-901).
+# ==================================================================================================
+def test_real_config_activates_registry_enforcement_iter30():
+    """The real config.yaml carries the iter-30 pre-registration registry, ACTIVATED (`enforce: true`)
+    after the backfill was verified complete — the gate's teeth are on. The CODE default is still off
+    (proven by `test_registry_defaults_when_omitted`)."""
+    cfg = load_config()
+    assert cfg.evidence.registry.path.endswith("pre-registrations.jsonl")
+    assert cfg.evidence.registry.enforce is True
+
+
+def test_registry_defaults_when_omitted(tmp_path):
+    """A config OMITTING the `evidence.registry` block still loads (additive, default-populated) — so a
+    config / inline test fixture predating iter-30 is unaffected and stays default-OFF (the gate's
+    registry cross-check is skipped entirely, byte-identical to pre-iter-30 behavior)."""
+    cfg = load_config(_write(tmp_path, MINIMAL_VALID))
+    assert cfg.evidence.registry.enforce is False
+    assert cfg.evidence.registry.path  # the built-in default path
+
+
+def test_registry_config_omitted_inside_a_present_evidence_block(tmp_path):
+    """A full config that DOES carry `evidence` but omits the nested `registry` sub-block (e.g. an
+    iter-9-era fixture) still loads, default-populated and default-OFF — the same additive guarantee
+    `fdr`/`staging_ledger_path` already have."""
+    data = copy.deepcopy(MINIMAL_VALID)
+    data["evidence"] = {"ledger_path": "runs/x/certified-claims.jsonl"}
+    cfg = load_config(_write(tmp_path, data))
+    assert cfg.evidence.registry.enforce is False
+    assert cfg.evidence.registry.path.endswith("pre-registrations.jsonl")
diff --git a/apps/frontend/app/research/page.tsx b/apps/frontend/app/research/page.tsx
index 702e7f3..5b599e0 100644
--- a/apps/frontend/app/research/page.tsx
+++ b/apps/frontend/app/research/page.tsx
@@ -3,6 +3,7 @@
 import Link from "next/link";
 import {
   ArrowRight,
+  BookMarked,
   Boxes,
   Gauge,
   GitCompareArrows,
@@ -73,6 +74,35 @@ export default function ResearchHubPage() {
           );
         })}
       </div>
+
+      {/* goal-mcp-loop iter-30 (J-18) — Governance & process: the first of several forthcoming governance
+          surfaces (registry now; graveyard / budget / referee-audit to follow). Kept a SEPARATE section,
+          not an 11th RESEARCH_LABS entry — that array's reading order is a J-113 contract over the ten
+          analytical labs; a governance/process link is architecturally distinct, not a lab. */}
+      <div className="space-y-3">
+        <h2 className="text-sm font-semibold uppercase tracking-wide text-text-faint">Governance &amp; process</h2>
+        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3" data-testid="research-governance">
+          <Link
+            href={asofHref("/research/registry")}
+            data-testid="research-governance-link-registry"
+            className={cn(
+              "group flex flex-col gap-2 rounded-lg border border-border bg-surface p-4 transition-colors",
+              "hover:border-accent hover:bg-surface-2",
+              "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent",
+            )}
+          >
+            <div className="flex items-center gap-2">
+              <BookMarked className="h-5 w-5 text-accent" aria-hidden />
+              <h3 className="text-base font-semibold text-text">Pre-registration registry</h3>
+              <ArrowRight className="ml-auto h-4 w-4 text-text-faint transition-transform group-hover:translate-x-0.5 group-hover:text-accent" aria-hidden />
+            </div>
+            <p className="text-sm text-text-muted">
+              Every hypothesis the system has ever registered or tested — selectors, rationale,
+              registration date, and source. The gate refuses to certify anything that isn&apos;t here.
+            </p>
+          </Link>
+        </div>
+      </div>
     </div>
   );
 }
diff --git a/apps/frontend/lib/api.ts b/apps/frontend/lib/api.ts
index aef4290..4a07403 100644
--- a/apps/frontend/lib/api.ts
+++ b/apps/frontend/lib/api.ts
@@ -11,12 +11,16 @@ import type {
   EvidenceLedgerResponse,
   ProvenSignal,
 } from "@/lib/evidence";
+import type { PreRegistrationRow, RegistryResponse } from "@/lib/registry";
 
 // Re-export the read-side evidence types (goal-mcp-loop iter-1) so callers import them from the API client
 // alongside `fetchEvidence`. These are DISTINCT from `EvidenceAggregate` below (the Backtest forward-tested
 // aggregate) — do not confuse the two.
 export type { CertifiedClaim, EvidenceLedgerResponse, ProvenSignal };
 
+// Re-export the pre-registration registry types (goal-mcp-loop iter-30, J-18) alongside `fetchRegistry`.
+export type { PreRegistrationRow, RegistryResponse };
+
 /** The build-time configured backend base (`NEXT_PUBLIC_API_URL`, default localhost). The configured
  *  backend PORT (`NEXT_PUBLIC_API_PORT`) is read alongside so the runtime resolver can host-swap to the
  *  page's own host when the page is opened at a non-localhost (LAN-IP) origin (J-108). Both are inlined
@@ -349,6 +353,15 @@ export async function fetchEvidence(signal?: AbortSignal): Promise<EvidenceLedge
   return getJSON<EvidenceLedgerResponse>("/api/evidence", signal);
 }
 
+// --- pre-registration registry (goal-mcp-loop iter-30, J-18 / backlog B-901) ----------------
+/** GET /api/research/registry — the read-only pre-registration registry: every hypothesis ever
+ *  registered/tested, read VERBATIM from the SAME file + loader the post-decompose gate cross-checks an
+ *  incoming Evidence Claim against. Re-formats nothing; introduces no proven-language. Throws on network
+ *  error or non-200 so the page renders an explicit "Backend unavailable" state. */
+export async function fetchRegistry(signal?: AbortSignal): Promise<RegistryResponse> {
+  return getJSON<RegistryResponse>("/api/research/registry", signal);
+}
+
 // --- stock price/MA/volume series for the detail chart (iter-4) -----------------------------
 /** One ascending OHLCV bar. By default date <= as-of (no lookahead — the backend reads only
  *  `bars_asof`). With the J-20 `through=latest` opt-in the series extends through the latest seed bar
diff --git a/config.yaml b/config.yaml
index 800dd17..fa179d6 100644
--- a/config.yaml
+++ b/config.yaml
@@ -1085,6 +1085,25 @@ evidence:
     w0_fraction: 0.5        # initial alpha-wealth W0 = w0_fraction * alpha (0..1)
     gamma_exponent: 1.6     # polynomial spending-sequence decay exponent (> 1 so Σ γ_j converges)
     gamma_terms: 1000       # explicit terms for the ζ(gamma_exponent) normalizer (Euler–Maclaurin tail beyond)
+  # goal-mcp-loop iter-30 CONSUMED — the pre-registration registry (J-18 / backlog B-901): the append-only
+  # state/pre-registrations.jsonl BOTH GET /api/research/registry (via app.engine.registry) and the
+  # post-decompose gate (verify_claim.py) read through the SAME loader module, so the registry page a human
+  # browses and the machine cross-check an incoming Evidence Claim runs through can never disagree. `enforce`
+  # is the gate's teeth: when true, verify_claim.py refuses (BLOCKED, exit 3, before any referee computation)
+  # any Evidence Claim whose exact selectors do not match a registry row. ACTIVATED here (enforce: true) only
+  # after the backfill (11 rows — every proposer-guidance.md §4.1/§4.2 candidate ∪ every distinct claim
+  # selector-set in both ledgers, deduplicated) was verified complete against both ledgers (see the iter-30
+  # dev handoff) — it blocks nothing today because no current/near-term iteration submits a `## Evidence
+  # Claim` (goal.md's Evidence-frontier plateau note), and permanently closes the ad-hoc-mining door for every
+  # future one. A relative path resolves against the repo root; the runtime override TRENDORA_REGISTRY_PATH
+  # takes precedence when set; run-goal.sh exports it alongside LEDGER_PATH / STAGING_LEDGER_PATH.
+  registry:
+    path: runs/goal-session-mcp-loop/state/pre-registrations.jsonl
+    enforce: true            # iter-30: flipped true — the backfill (11 rows) is verified complete against
+                              # both ledgers (test_registry.py's round-trip tests) and the gate fixtures
+                              # (test_gate_registry_enforcement.py) prove registered/unregistered/near-miss
+                              # behave correctly. Blocks nothing today (no iteration currently carries a
+                              # ## Evidence Claim); closes the ad-hoc-mining door for every future one.
 
 # ----------------------------------------------------------------------------------------
 # Analyst-loop triad scan (app.engine.triad_scan / scan_product_triad). Tunables for the
diff --git a/incredible_auto_dev/scripts/automation/run-goal.sh b/incredible_auto_dev/scripts/automation/run-goal.sh
index f2ab364..d819abd 100755
--- a/incredible_auto_dev/scripts/automation/run-goal.sh
+++ b/incredible_auto_dev/scripts/automation/run-goal.sh
@@ -1636,6 +1636,7 @@ Do NOT write code or implement anything. The iteration spec and any blueprint ed
              SESSION_DIR="$GOAL_SESSION_DIR_LOCAL" \
              LEDGER_PATH="$GOAL_SESSION_DIR_LOCAL/state/certified-claims.jsonl" \
              STAGING_LEDGER_PATH="$GOAL_SESSION_DIR_LOCAL/state/staging-ledger.jsonl" \
+             TRENDORA_REGISTRY_PATH="$GOAL_SESSION_DIR_LOCAL/state/pre-registrations.jsonl" \
              GATE_VERDICT_PATH="$ITER_DIR/gate-post-decompose.json"
       run_project_gate post-decompose
     ) || _gate_rc=$?
@@ -2139,7 +2140,8 @@ PY
           export SESSION_ID REPO_ROOT GOAL_FILE \
                  SESSION_DIR="$GOAL_SESSION_DIR_LOCAL" \
                  LEDGER_PATH="$GOAL_SESSION_DIR_LOCAL/state/certified-claims.jsonl" \
-                 STAGING_LEDGER_PATH="$GOAL_SESSION_DIR_LOCAL/state/staging-ledger.jsonl"
+                 STAGING_LEDGER_PATH="$GOAL_SESSION_DIR_LOCAL/state/staging-ledger.jsonl" \
+                 TRENDORA_REGISTRY_PATH="$GOAL_SESSION_DIR_LOCAL/state/pre-registrations.jsonl"
           run_project_hook post-goal
         ) || echo "[run-goal] post-goal hook returned non-zero (non-fatal) — continuing." >&2
         # 2. dispatch the generic goal-proposer agent (works headless AND interactive pump).
diff --git a/project-extensions/gates/verify_claim.py b/project-extensions/gates/verify_claim.py
index 2675eb6..15cd1df 100644
--- a/project-extensions/gates/verify_claim.py
+++ b/project-extensions/gates/verify_claim.py
@@ -15,9 +15,19 @@ Per-claim ledger routing (iter-9): each Evidence Claim MAY carry an optional
     "canonical" (explicit, for a deliberately promoted winner) -> the user-facing
                 certified-claims ledger ($LEDGER_PATH), ALWAYS strict Bonferroni.
 
+Pre-registration cross-check (iter-30, J-18 / backlog B-901): BEFORE routing/referee,
+when config `evidence.registry.enforce` is true, each claim is cross-checked against
+the pre-registration registry ($TRENDORA_REGISTRY_PATH, via the SAME
+`app.engine.registry.match_registration` the registry page reads through) by EXACT
+selector-set equality — no fuzzy/superset matching. No match -> BLOCK (exit 3) BEFORE
+any referee computation: no `verify_edge` call, no ledger write, no Bonferroni-bar
+tightening. This is a PURE pre-check: a match (or enforcement off) falls through to
+the existing routing + `verify_edge` call completely unchanged.
+
     exit 0  => no claim, OR every claim CERTIFIED (PASS)        -> iteration may build
     exit 3  => a claim was NOT certified (FAIL / INSUFFICIENT), OR a routing failure
-               (unrecognized "ledger" value / the required *_LEDGER_PATH unset)
+               (unrecognized "ledger" value / the required *_LEDGER_PATH unset), OR
+               (enforcement on) a claim matched no pre-registration row
                -> block the iteration (FAIL-CLOSED — never a silent certification)
 
 A summary is written to $GATE_VERDICT_PATH when set. The referee counts independent
@@ -36,9 +46,19 @@ sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..",
 
 from sqlmodel import Session  # noqa: E402
 
+from app.config import get_config  # noqa: E402
 from app.db import get_engine  # noqa: E402
+from app.engine import registry as registry_mod  # noqa: E402
 from app.mcp import tools  # noqa: E402
 
+# The BLOCKED reason a claim gets when it matches no pre-registration row (enforcement on). Names the
+# registry requirement (the gate's message must be loud + actionable — B-901 DoD).
+_REGISTRY_BLOCK_REASON = (
+    "no matching pre-registration row in the registry (state/pre-registrations.jsonl, "
+    "GET /api/research/registry) — register this hypothesis's EXACT selectors at /research/registry "
+    "before submitting an Evidence Claim"
+)
+
 # A "## Evidence Claim" section runs until the next "## " heading (or EOF).
 _CLAIM_SECTION = re.compile(r"^##\s+Evidence Claim\b.*?(?=^\#\#\s|\Z)", re.MULTILINE | re.DOTALL)
 # Each fenced ```json { ... } ``` block inside it is one claim.
@@ -117,6 +137,16 @@ def main() -> int:
                 print(f"[gate] BLOCKED: {claim}  ({route_error})", file=sys.stderr)
                 blocked = True
                 continue
+            # Pre-registration cross-check (iter-30, J-18 / B-901) — a PURE pre-check, gated on
+            # evidence.registry.enforce. No match -> BLOCK before any referee computation (no verify_edge
+            # call, no ledger write). A match, or enforcement off, falls through completely unchanged.
+            if get_config().evidence.registry.enforce and registry_mod.match_registration(claim) is None:
+                results.append(
+                    {"claim": claim, "ledger": kind, "status": "BLOCKED", "reason": _REGISTRY_BLOCK_REASON}
+                )
+                print(f"[gate] BLOCKED: {claim}  ({_REGISTRY_BLOCK_REASON})", file=sys.stderr)
+                blocked = True
+                continue
             try:
                 status, reason = _verdict_fields(
                     tools.verify_edge(session, claim, ledger_path, register_date=register, ledger=kind)
diff --git a/apps/backend/app/api/registry.py b/apps/backend/app/api/registry.py
new file mode 100644
index 0000000..0bed31e
--- /dev/null
+++ b/apps/backend/app/api/registry.py
@@ -0,0 +1,32 @@
+"""GET /api/research/registry — the read-only pre-registration registry surface (goal-mcp-loop iter-30,
+J-18 / backlog B-901).
+
+Serves `app.engine.registry.load_registrations` verbatim (re-format only — no recompute): every
+hypothesis ever registered/tested, the SAME file + loader the post-decompose gate (`verify_claim.py`)
+cross-checks an incoming Evidence Claim against, so the registry page a human browses and the machine
+check can never disagree (the Data Contract single source of truth).
+
+No DB/session is needed (the registry comes from the append-only state file, not the snapshot DB). The
+registry path is config/env-driven via the resolver (anti-goal: No magic numbers — no path literal here).
+A missing/empty registry file returns 200 with an empty list, never a 500 (anti-goal: resilience to
+data-shape change) — the honest state before any backfill/registration has landed.
+
+This module carries NO proven-language: a registration's `status` is a descriptive process state
+("registered" / "tested" / "closed"), never a "Proven"/"Not yet proven" signal — that continues to flow
+solely from the certified-claims ledger via `app.engine.evidence` / `GET /api/evidence`.
+"""
+from __future__ import annotations
+
+from fastapi import APIRouter
+
+from app.engine.registry import load_registrations
+
+router = APIRouter(tags=["registry"])
+
+
+@router.get("/research/registry")
+def get_registry() -> dict:
+    """Every registered hypothesis, verbatim, in registration (append) order: `{"registrations": [...]}`.
+    READ-ONLY — recomputes nothing. An absent/empty registry file ⇒ `{"registrations": []}` (200, never
+    500)."""
+    return {"registrations": load_registrations()}
diff --git a/apps/backend/app/engine/registry.py b/apps/backend/app/engine/registry.py
new file mode 100644
index 0000000..f880473
--- /dev/null
+++ b/apps/backend/app/engine/registry.py
@@ -0,0 +1,119 @@
+"""The pre-registration registry — the read-side loader + exact-match checker (goal-mcp-loop iter-30,
+J-18 / backlog B-901).
+
+This module is the SINGLE source both `GET /api/research/registry` (via `app.api.registry`) and the
+post-decompose gate (`project-extensions/gates/verify_claim.py`, a non-HTTP consumer) read through — so
+the registry page a human browses and the machine check that refuses an unregistered Evidence Claim can
+never disagree. It is a PURE, engine-free module (mirrors `app.engine.evidence`'s shape): filesystem I/O
++ dict comparison only, no DB session, no computation.
+
+  - `load_registrations()` — every registered hypothesis, in append (registration) order. A missing/empty
+    file is an empty list, never a crash (anti-goal: resilience to data-shape change).
+  - `claim_selectors(claim)` — the EXACT selector-set one claim carries (`kind` + whichever
+    `_CLAIM_SELECTOR_KEYS` are present + `horizon` + `direction`), the SAME shape every registry row's
+    `selectors` field is stored as.
+  - `match_registration(claim)` — the registry row whose `selectors` EXACTLY equal the claim's
+    selector-set, or `None`. EXACT dict equality only — no fuzzy/superset matching (B-901's dominant
+    named trap: fuzziness reopens the ad-hoc-mining door a pre-registration requirement is meant to close).
+
+This module NEVER decides proven-ness (that is `app.engine.evidence`'s job alone, sourced from the
+certified-claims ledger) and introduces NO proven-language: a registration's `status` ("registered" /
+"tested" / "closed") is a descriptive PROCESS state, never a "Proven"/"Not yet proven" signal.
+
+The registry PATH is config/env-driven (anti-goal: No magic numbers — no path literal here): the runtime
+override `TRENDORA_REGISTRY_PATH`, else `config.evidence.registry.path` resolved against the repo root —
+mirroring `app.engine.evidence.resolve_ledger_path()` exactly.
+"""
+from __future__ import annotations
+
+import json
+import os
+from pathlib import Path
+
+from app.config import REPO_ROOT, get_config
+
+# The environment-variable NAME (the NAME only — never a path VALUE literal in code) the runtime registry
+# path may be overridden with. Mirrors `app.engine.evidence.LEDGER_PATH_ENV`.
+REGISTRY_PATH_ENV = "TRENDORA_REGISTRY_PATH"
+
+
+def resolve_registry_path() -> str:
+    """The pre-registrations file path: the `TRENDORA_REGISTRY_PATH` env override if set, else
+    `config.evidence.registry.path` resolved against `REPO_ROOT` when relative.
+
+    This MUST resolve to the SAME file the post-decompose gate reads (set by `run-goal.sh` alongside
+    `LEDGER_PATH`/`STAGING_LEDGER_PATH`), so the registry page and the gate's cross-check are always
+    reading identical state. No path literal lives here — the default lives in config (anti-goal: No
+    magic numbers). Mirrors `app.engine.evidence.resolve_ledger_path()` exactly."""
+    override = os.environ.get(REGISTRY_PATH_ENV)
+    if override:
+        return override
+    configured = Path(get_config().evidence.registry.path)
+    if not configured.is_absolute():
+        configured = REPO_ROOT / configured
+    return str(configured)
+
+
+def load_registrations(path: str | None = None) -> list[dict]:
+    """Every registered hypothesis, in append order. A missing file (or a file that does not exist yet)
+    is an empty registry (`[]`), never a crash — the honest default before any backfill/registration has
+    landed. Blank lines are skipped so a trailing newline never yields a phantom row.
+
+    `path` defaults to `resolve_registry_path()` (the endpoint's call shape); a caller (tests, or the
+    gate via `match_registration`) may pass an explicit path to read an isolated fixture file instead."""
+    target = path if path is not None else resolve_registry_path()
+    if not os.path.exists(target):
+        return []
+    rows: list[dict] = []
+    with open(target, "r", encoding="utf-8") as handle:
+        for line in handle:
+            line = line.strip()
+            if line:
+                rows.append(json.loads(line))
+    return rows
+
+
+# The claim selectors this module matches on — mirrors `app.mcp.tools._CLAIM_SELECTOR_KEYS` BYTE-FOR-BYTE.
+# Kept as a local literal (not imported) so this module stays engine-free / pure, exactly like
+# `app.engine.ledger._PASS_STATUS` mirrors `app.engine.referee.STATUS_PASS` "so this module stays
+# engine-free." `app.mcp.tools` is the source of truth for this tuple; update both together.
+_CLAIM_SELECTOR_KEYS = (
+    "factor", "slice_kind", "decile", "regime", "sector", "condition", "cohort", "single_index",
+    "subject", "view", "setup", "pattern", "phase", "dimension", "family", "velocity_sign",
+    "regime_decile", "severity_decile", "factor_decile", "asof",
+)
+
+
+def claim_selectors(claim: dict) -> dict:
+    """The EXACT selector-set one claim carries: `kind` + whichever `_CLAIM_SELECTOR_KEYS` the claim
+    dict has present + `horizon` + `direction` (defaulting the direction to `"positive"`, mirroring
+    `app.mcp.tools.verify_edge`'s own default when a claim omits it — every real Evidence Claim / ledger
+    row carries `horizon` explicitly, so no default is applied there). Display-routing keys a claim may
+    also carry (`signal`, `ledger`) are DELIBERATELY excluded — they route where a certified claim's
+    badge/ledger lands, they are not part of the hypothesis identity a registration matches on."""
+    selectors: dict = {"kind": claim.get("kind")}
+    for key in _CLAIM_SELECTOR_KEYS:
+        if key in claim:
+            selectors[key] = claim[key]
+    if "horizon" in claim:
+        selectors["horizon"] = claim["horizon"]
+    selectors["direction"] = claim.get("direction", "positive")
+    return selectors
+
+
+def match_registration(claim: dict, registrations: list[dict] | None = None) -> dict | None:
+    """The registry row whose `selectors` EXACTLY equal `claim`'s selector-set (`claim_selectors`), or
+    `None` when nothing matches — an unregistered hypothesis, OR a near-miss whose selectors differ by
+    even one value (e.g. a decile or horizon off by one). EXACT dict equality only, deliberately: fuzzy
+    or superset matching is B-901's named dominant trap (it would reopen the ad-hoc-mining door
+    pre-registration exists to close).
+
+    `registrations` defaults to `load_registrations()` (the committed/configured file) when omitted —
+    the gate's real call shape (`match_registration(claim)`); a caller (unit tests) may pass an explicit
+    fixture list instead so a loader test needs no on-disk file."""
+    wanted = claim_selectors(claim)
+    rows = load_registrations() if registrations is None else registrations
+    for row in rows:
+        if isinstance(row, dict) and row.get("selectors") == wanted:
+            return row
+    return None
diff --git a/apps/backend/tests/test_api_registry.py b/apps/backend/tests/test_api_registry.py
new file mode 100644
index 0000000..15e1536
--- /dev/null
+++ b/apps/backend/tests/test_api_registry.py
@@ -0,0 +1,66 @@
+"""GET /api/research/registry API tests (goal-mcp-loop iter-30, J-18 / backlog B-901).
+
+Mounts ONLY the registry router on a bare FastAPI app (NO lifespan) so the test needs NO seeded DB and NO
+walk-forward boot — the endpoint reads the append-only state file, not a snapshot (mirrors
+test_api_methodology.py's DB-free pattern exactly).
+"""
+from __future__ import annotations
+
+from fastapi import FastAPI
+from fastapi.testclient import TestClient
+
+from app.api import registry
+from app.engine.ledger import append_entry
+from app.engine.registry import REGISTRY_PATH_ENV, load_registrations
+
+
+def _client() -> TestClient:
+    app = FastAPI()
+    app.include_router(registry.router, prefix="/api")
+    return TestClient(app)
+
+
+def test_registry_endpoint_empty_on_missing_file(tmp_path, monkeypatch):
+    monkeypatch.setenv(REGISTRY_PATH_ENV, str(tmp_path / "missing" / "pre-registrations.jsonl"))
+    with _client() as client:
+        resp = client.get("/api/research/registry")
+    assert resp.status_code == 200
+    assert resp.json() == {"registrations": []}
+
+
+def test_registry_endpoint_serves_backfilled_rows_verbatim(tmp_path, monkeypatch):
+    path = tmp_path / "pre-registrations.jsonl"
+    row = {
+        "id": "factor-vcp_contraction-d10-h60",
+        "selectors": {
+            "kind": "factor", "factor": "vcp_contraction", "slice_kind": "decile", "decile": 10,
+            "horizon": 60, "direction": "positive",
+        },
+        "rationale": "Does the post-contraction expansion edge persist over a quarter?",
+        "registered_by": "backfill",
+        "registered_date": "2026-07-03",
+        "source": "proposer-guidance.md §4.1 #2; certified-claims.jsonl",
+        "status": "tested",
+    }
+    append_entry(str(path), row)
+    monkeypatch.setenv(REGISTRY_PATH_ENV, str(path))
+    with _client() as client:
+        resp = client.get("/api/research/registry")
+    assert resp.status_code == 200
+    body = resp.json()
+    assert len(body["registrations"]) == 1
+    served = body["registrations"][0]
+    # re-formats verbatim -- every field byte-matches what was written, nothing recomputed.
+    for key, value in row.items():
+        assert served[key] == value
+
+
+def test_registry_endpoint_equals_loader_output_directly(monkeypatch):
+    """Single-source assertion: the endpoint's response equals `load_registrations()` called directly
+    against the SAME (real, committed) file — the page and the gate can never disagree."""
+    monkeypatch.delenv(REGISTRY_PATH_ENV, raising=False)  # use the real config-resolved committed file
+    with _client() as client:
+        resp = client.get("/api/research/registry")
+    assert resp.status_code == 200
+    assert resp.json() == {"registrations": load_registrations()}
+    assert len(resp.json()["registrations"]) == 11  # the committed iter-30 backfill
diff --git a/apps/backend/tests/test_gate_registry_enforcement.py b/apps/backend/tests/test_gate_registry_enforcement.py
new file mode 100644
index 0000000..f44ae18
--- /dev/null
+++ b/apps/backend/tests/test_gate_registry_enforcement.py
@@ -0,0 +1,226 @@
+"""Post-decompose gate — pre-registration cross-check tests (goal-mcp-loop iter-30, J-18 / backlog B-901).
+
+Loads `project-extensions/gates/verify_claim.py` via `importlib.util.spec_from_file_location`, exactly as
+`test_staging_ledger_routing.py::_load_gate` already does. `tools.verify_edge` is monkeypatched to a spy
+stub (never touches the DB) so these tests need NO seeded DB / warm-up — they pin the GATE's pre-check
+DECISION only (call vs no-call), which is the load-bearing B-901 contract:
+
+  (a) a claim whose EXACT selectors match a registry row, with enforcement ON -> the gate proceeds to
+      `verify_edge` (the referee IS reached);
+  (b) an UNREGISTERED claim, enforcement ON -> refused BEFORE `verify_edge` runs (never called), the
+      target ledger file is left byte-identical (no write), and the BLOCKED reason names the registry;
+  (c) a NEAR-MISS claim (one differing selector — decile 10 -> 9), enforcement ON -> refused the same way
+      as (b), proving the match is EXACT, never fuzzy;
+  (d) enforcement OFF -> an unregistered claim still reaches `verify_edge` (byte-identical to the
+      pre-iter-30 gate behavior) — the regression guard for every iteration that predates its own
+      registry row being backfilled.
+"""
+from __future__ import annotations
+
+import importlib.util
+import json
+from pathlib import Path
+
+from sqlmodel import create_engine
+
+_REPO_ROOT = Path(__file__).resolve().parents[3]
+_GATE_PATH = _REPO_ROOT / "project-extensions" / "gates" / "verify_claim.py"
+
+_REGISTERED_CLAIM = {
+    "kind": "factor", "factor": "vcp_contraction", "slice_kind": "decile", "decile": 10,
+    "horizon": 60, "direction": "positive",
+}
+_UNREGISTERED_CLAIM = {
+    "kind": "factor", "factor": "hv", "slice_kind": "decile", "decile": 10,
+    "horizon": 20, "direction": "positive",
+}
+# A NEAR-MISS of _REGISTERED_CLAIM: one selector differs (decile 10 -> 9).
+_NEAR_MISS_CLAIM = {**_REGISTERED_CLAIM, "decile": 9}
+
+_FIXTURE_REGISTRY_ROW = {
+    "id": "factor-vcp_contraction-d10-h60",
+    "selectors": _REGISTERED_CLAIM,
+    "rationale": "fixture", "registered_by": "backfill", "registered_date": "2026-07-03",
+    "source": "fixture", "status": "tested",
+}
+
+
+def _load_gate():
+    """Mirrors test_staging_ledger_routing.py::_load_gate exactly."""
+    spec = importlib.util.spec_from_file_location("verify_claim_gate_registry_test", _GATE_PATH)
+    module = importlib.util.module_from_spec(spec)
+    spec.loader.exec_module(module)
+    return module
+
+
+def _write_spec(tmp_path: Path, claim: dict) -> Path:
+    spec_path = tmp_path / "iter-spec.md"
+    spec_path.write_text(
+        "# Fixture iteration spec\n\n## Evidence Claim\n```json\n" + json.dumps(claim) + "\n```\n",
+        encoding="utf-8",
+    )
+    return spec_path
+
+
+def _spy_verify_edge(calls):
+    def _fake(session, claim, ledger_path, *, register_date, ledger):
+        calls.append({"claim": claim, "ledger_path": ledger_path, "ledger": ledger})
+        return {"verdict": {"status": "PASS", "reason": "stub"}}
+    return _fake
+
+
+def _wire_gate(gate, monkeypatch, *, enforce: bool, registry_path: Path):
+    """Shared fixture wiring: a harmless in-memory engine (verify_edge is stubbed, so the session is never
+    queried), a fresh config with `evidence.registry.enforce` set explicitly, and the registry pointed at
+    an isolated fixture file — never the real committed one."""
+    from app.config import load_config
+
+    monkeypatch.setattr(gate, "get_engine", lambda: create_engine("sqlite://"))
+    cfg = load_config()  # a FRESH load (not the process cache) so mutating it is test-local
+    cfg.evidence.registry.enforce = enforce
+    monkeypatch.setattr(gate, "get_config", lambda: cfg)
+    monkeypatch.setenv(gate.registry_mod.REGISTRY_PATH_ENV, str(registry_path))
+
+
+def _seed_registry(path: Path, rows: list[dict]) -> None:
+    with open(path, "w", encoding="utf-8") as fh:
+        for row in rows:
+            fh.write(json.dumps(row) + "\n")
+
+
+# ==================================================================================================
+# (a) registered exact-match claim, enforcement ON -> proceeds to verify_edge
+# ==================================================================================================
+def test_registered_claim_reaches_verify_edge_when_enforced(tmp_path, monkeypatch):
+    gate = _load_gate()
+    registry_path = tmp_path / "pre-registrations.jsonl"
+    _seed_registry(registry_path, [_FIXTURE_REGISTRY_ROW])
+    _wire_gate(gate, monkeypatch, enforce=True, registry_path=registry_path)
+
+    calls: list[dict] = []
+    monkeypatch.setattr(gate.tools, "verify_edge", _spy_verify_edge(calls))
+
+    spec_path = _write_spec(tmp_path, _REGISTERED_CLAIM)
+    monkeypatch.setenv("SPEC_PATH", str(spec_path))
+    monkeypatch.setenv("STAGING_LEDGER_PATH", str(tmp_path / "staging-ledger.jsonl"))
+    monkeypatch.setenv("LEDGER_PATH", str(tmp_path / "certified-claims.jsonl"))
+    monkeypatch.delenv("GATE_VERDICT_PATH", raising=False)
+
+    rc = gate.main()
+
+    assert len(calls) == 1  # the referee WAS reached
+    assert calls[0]["claim"] == _REGISTERED_CLAIM
+    assert rc == 0  # the stub returns PASS -> the iteration is not blocked
+
+
+# ==================================================================================================
+# (b) unregistered claim, enforcement ON -> refused BEFORE verify_edge; ledger left untouched
+# ==================================================================================================
+def test_unregistered_claim_is_refused_before_verify_edge(tmp_path, monkeypatch):
+    gate = _load_gate()
+    registry_path = tmp_path / "pre-registrations.jsonl"
+    _seed_registry(registry_path, [_FIXTURE_REGISTRY_ROW])  # does NOT cover _UNREGISTERED_CLAIM
+    _wire_gate(gate, monkeypatch, enforce=True, registry_path=registry_path)
+
+    calls: list[dict] = []
+    monkeypatch.setattr(gate.tools, "verify_edge", _spy_verify_edge(calls))
+
+    spec_path = _write_spec(tmp_path, _UNREGISTERED_CLAIM)
+    staging_ledger = tmp_path / "staging-ledger.jsonl"
+    staging_ledger.write_text("", encoding="utf-8")  # pre-existing (empty) — must stay byte-identical
+    before = staging_ledger.read_bytes()
+
+    monkeypatch.setenv("SPEC_PATH", str(spec_path))
+    monkeypatch.setenv("STAGING_LEDGER_PATH", str(staging_ledger))
+    monkeypatch.setenv("LEDGER_PATH", str(tmp_path / "certified-claims.jsonl"))
+    verdict_path = tmp_path / "gate-verdict.json"
+    monkeypatch.setenv("GATE_VERDICT_PATH", str(verdict_path))
+
+    rc = gate.main()
+
+    assert calls == []  # verify_edge was NEVER called
+    assert staging_ledger.read_bytes() == before  # the target ledger is untouched (no write)
+    assert rc == 3  # BLOCKED
+    verdict = json.loads(verdict_path.read_text(encoding="utf-8"))
+    assert verdict["blocked"] is True
+    assert verdict["results"][0]["status"] == "BLOCKED"
+    # the message names the registry requirement (loud + actionable, not a bare "no").
+    reason = verdict["results"][0]["reason"]
+    assert "registry" in reason.lower() and "register" in reason.lower()
+
+
+# ==================================================================================================
+# (c) near-miss claim (one differing selector), enforcement ON -> refused the same way (EXACT match)
+# ==================================================================================================
+def test_near_miss_claim_is_refused_proving_exact_match(tmp_path, monkeypatch):
+    gate = _load_gate()
+    registry_path = tmp_path / "pre-registrations.jsonl"
+    _seed_registry(registry_path, [_FIXTURE_REGISTRY_ROW])
+    _wire_gate(gate, monkeypatch, enforce=True, registry_path=registry_path)
+
+    calls: list[dict] = []
+    monkeypatch.setattr(gate.tools, "verify_edge", _spy_verify_edge(calls))
+
+    # sanity: the near-miss really does differ from the registered row by exactly one selector.
+    assert _NEAR_MISS_CLAIM != _REGISTERED_CLAIM
+    assert _NEAR_MISS_CLAIM["decile"] == 9 and _REGISTERED_CLAIM["decile"] == 10
+
+    spec_path = _write_spec(tmp_path, _NEAR_MISS_CLAIM)
+    monkeypatch.setenv("SPEC_PATH", str(spec_path))
+    monkeypatch.setenv("STAGING_LEDGER_PATH", str(tmp_path / "staging-ledger.jsonl"))
+    monkeypatch.setenv("LEDGER_PATH", str(tmp_path / "certified-claims.jsonl"))
+    monkeypatch.delenv("GATE_VERDICT_PATH", raising=False)
+
+    rc = gate.main()
+
+    assert calls == []  # the near-miss never reaches the referee
+    assert rc == 3
+    assert not (tmp_path / "staging-ledger.jsonl").exists()  # no ledger ever created
+
+
+# ==================================================================================================
+# (d) enforcement OFF -> an unregistered claim still proceeds (byte-identical pre-iter-30 behavior)
+# ==================================================================================================
+def test_enforcement_off_unregistered_claim_still_proceeds(tmp_path, monkeypatch):
+    gate = _load_gate()
+    registry_path = tmp_path / "pre-registrations.jsonl"
+    _seed_registry(registry_path, [_FIXTURE_REGISTRY_ROW])  # present but irrelevant -- enforcement is off
+    _wire_gate(gate, monkeypatch, enforce=False, registry_path=registry_path)
+
+    calls: list[dict] = []
+    monkeypatch.setattr(gate.tools, "verify_edge", _spy_verify_edge(calls))
+
+    spec_path = _write_spec(tmp_path, _UNREGISTERED_CLAIM)
+    monkeypatch.setenv("SPEC_PATH", str(spec_path))
+    monkeypatch.setenv("STAGING_LEDGER_PATH", str(tmp_path / "staging-ledger.jsonl"))
+    monkeypatch.setenv("LEDGER_PATH", str(tmp_path / "certified-claims.jsonl"))
+    monkeypatch.delenv("GATE_VERDICT_PATH", raising=False)
+
+    rc = gate.main()
+
+    assert len(calls) == 1  # the pre-iter-30 behavior: no registry gate, straight to the referee
+    assert calls[0]["claim"] == _UNREGISTERED_CLAIM
+    assert rc == 0
+
+
+# ==================================================================================================
+# missing registry file, enforcement ON -> every claim refused (an absent registry registers nothing)
+# ==================================================================================================
+def test_missing_registry_file_enforced_refuses_every_claim(tmp_path, monkeypatch):
+    gate = _load_gate()
+    missing_registry = tmp_path / "does-not-exist" / "pre-registrations.jsonl"
+    _wire_gate(gate, monkeypatch, enforce=True, registry_path=missing_registry)
+
+    calls: list[dict] = []
+    monkeypatch.setattr(gate.tools, "verify_edge", _spy_verify_edge(calls))
+
+    spec_path = _write_spec(tmp_path, _REGISTERED_CLAIM)  # would have matched, HAD the file existed
+    monkeypatch.setenv("SPEC_PATH", str(spec_path))
+    monkeypatch.setenv("STAGING_LEDGER_PATH", str(tmp_path / "staging-ledger.jsonl"))
+    monkeypatch.setenv("LEDGER_PATH", str(tmp_path / "certified-claims.jsonl"))
+    monkeypatch.delenv("GATE_VERDICT_PATH", raising=False)
+
+    rc = gate.main()
+
+    assert calls == []
+    assert rc == 3  # fail-closed, never a silent pass-through on a missing registry
diff --git a/apps/backend/tests/test_registry.py b/apps/backend/tests/test_registry.py
new file mode 100644
index 0000000..c98aa6f
--- /dev/null
+++ b/apps/backend/tests/test_registry.py
@@ -0,0 +1,282 @@
+"""Pre-registration registry loader tests (goal-mcp-loop iter-30, J-18 / backlog B-901).
+
+`app.engine.registry` is the SINGLE pure loader both `GET /api/research/registry` and the post-decompose
+gate (`verify_claim.py`) read through. These tests pin:
+
+  - `resolve_registry_path` honors the `TRENDORA_REGISTRY_PATH` env override, else the config default
+    (mirrors `test_evidence.py`'s `resolve_ledger_path` tests exactly);
+  - `load_registrations` is honest about a missing/empty file (`[]`, never a crash) and reads real rows
+    in append order;
+  - `claim_selectors` builds the EXACT selector-set shape (`kind` + present cohort keys + `horizon` +
+    `direction`, excluding display-routing keys like `signal`/`ledger`);
+  - `match_registration` is EXACT-equality only: a real match returns the row, a near-miss (one differing
+    selector — proves matching is exact, never fuzzy) and a fully unregistered claim both return `None`;
+  - the COMMITTED backfill (`state/pre-registrations.jsonl`) is complete: 11 distinct rows (the union of
+    both ledgers' 14 raw entries, deduplicated by exact selector-set — 3 pairs are identical selector-sets
+    promoted staging->canonical, see the iter-30 dev handoff), append-only, every row's stated
+    `registered_date` is the ledgers' own 2026-07-03 register date (never a fabricated "today"), and every
+    row in BOTH real ledgers round-trips through `match_registration` back to a backfilled row.
+"""
+from __future__ import annotations
+
+import json
+from pathlib import Path
+
+from app.config import REPO_ROOT
+from app.engine.ledger import append_entry, read_entries
+from app.engine.registry import (
+    REGISTRY_PATH_ENV,
+    claim_selectors,
+    load_registrations,
+    match_registration,
+    resolve_registry_path,
+)
+
+_CANONICAL_LEDGER = REPO_ROOT / "runs/goal-session-mcp-loop/state/certified-claims.jsonl"
+_STAGING_LEDGER = REPO_ROOT / "runs/goal-session-mcp-loop/state/staging-ledger.jsonl"
+_COMMITTED_REGISTRY = REPO_ROOT / "runs/goal-session-mcp-loop/state/pre-registrations.jsonl"
+
+
+# ==================================================================================================
+# resolve_registry_path — env override, else config default (mirrors test_evidence.py verbatim)
+# ==================================================================================================
+def test_resolve_registry_path_env_override(tmp_path, monkeypatch):
+    override = tmp_path / "override-registry.jsonl"
+    monkeypatch.setenv(REGISTRY_PATH_ENV, str(override))
+    assert resolve_registry_path() == str(override)
+
+
+def test_resolve_registry_path_config_default(monkeypatch):
+    monkeypatch.delenv(REGISTRY_PATH_ENV, raising=False)
+    resolved = resolve_registry_path()
+    # the SAME file the post-decompose gate cross-checks against, resolved absolute against the repo root
+    assert resolved == str(REPO_ROOT / "runs/goal-session-mcp-loop/state/pre-registrations.jsonl")
+    assert Path(resolved).is_absolute()
+
+
+# ==================================================================================================
+# load_registrations — honest empty on missing/absent file, real rows in append order otherwise
+# ==================================================================================================
+def test_load_registrations_missing_file_is_empty(tmp_path):
+    assert load_registrations(str(tmp_path / "nope.jsonl")) == []
+
+
+def test_load_registrations_empty_file_is_empty(tmp_path):
+    path = tmp_path / "empty.jsonl"
+    path.write_text("", encoding="utf-8")
+    assert load_registrations(str(path)) == []
+
+
+def test_load_registrations_reads_rows_in_append_order(tmp_path):
+    path = str(tmp_path / "registry.jsonl")
+    append_entry(path, {"id": "a", "selectors": {"kind": "factor"}})
+    append_entry(path, {"id": "b", "selectors": {"kind": "event-study"}})
+    rows = load_registrations(path)
+    assert [r["id"] for r in rows] == ["a", "b"]
+
+
+def test_load_registrations_defaults_to_resolve_registry_path(tmp_path, monkeypatch):
+    override = tmp_path / "env-registry.jsonl"
+    append_entry(str(override), {"id": "z", "selectors": {"kind": "factor"}})
+    monkeypatch.setenv(REGISTRY_PATH_ENV, str(override))
+    # no explicit path -> resolves via resolve_registry_path() (the endpoint's own call shape)
+    assert [r["id"] for r in load_registrations()] == ["z"]
+
+
+# ==================================================================================================
+# claim_selectors — the EXACT selector-set shape (kind + present cohort keys + horizon + direction)
+# ==================================================================================================
+def test_claim_selectors_factor_cohort_shape():
+    claim = {
+        "kind": "factor", "factor": "vcp_contraction", "slice_kind": "decile", "decile": 10,
+        "horizon": 60, "direction": "positive", "ledger": "canonical",
+    }
+    # `ledger` is a display-ROUTING key, not part of the hypothesis identity -- excluded.
+    assert claim_selectors(claim) == {
+        "kind": "factor", "factor": "vcp_contraction", "slice_kind": "decile", "decile": 10,
+        "horizon": 60, "direction": "positive",
+    }
+
+
+def test_claim_selectors_excludes_signal_key():
+    claim = {
+        "kind": "factor", "factor": "leadership_score", "slice_kind": "decile", "decile": 10,
+        "horizon": 20, "direction": "positive", "signal": "leadership_score",
+    }
+    selectors = claim_selectors(claim)
+    assert "signal" not in selectors
+    assert selectors["factor"] == "leadership_score"
+
+
+def test_claim_selectors_combination_cohort_shape():
+    claim = {
+        "kind": "combination", "cohort": "composite",
+        "condition": ["rs_spy_3m:top:quintile", "atr_pct:bottom:tertile"],
+        "horizon": 20, "direction": "positive",
+    }
+    assert claim_selectors(claim) == claim  # every key here IS a selector key -- nothing dropped
+
+
+def test_claim_selectors_defaults_direction_positive_when_absent():
+    claim = {"kind": "factor", "factor": "ma_stack", "slice_kind": "decile", "decile": 10, "horizon": 20}
+    assert claim_selectors(claim)["direction"] == "positive"
+
+
+def test_claim_selectors_omits_horizon_when_claim_omits_it():
+    claim = {"kind": "factor", "factor": "ma_stack", "slice_kind": "decile", "decile": 10}
+    assert "horizon" not in claim_selectors(claim)
+
+
+# ==================================================================================================
+# match_registration — EXACT equality only: real match / near-miss (one differing selector) / no match
+# ==================================================================================================
+_FIXTURE_REGISTRATIONS = [
+    {
+        "id": "factor-vcp_contraction-d10-h60",
+        "selectors": {
+            "kind": "factor", "factor": "vcp_contraction", "slice_kind": "decile", "decile": 10,
+            "horizon": 60, "direction": "positive",
+        },
+        "rationale": "fixture", "registered_by": "backfill", "registered_date": "2026-07-03",
+        "source": "fixture", "status": "tested",
+    },
+]
+
+
+def test_match_registration_exact_match_returns_the_row():
+    claim = {
+        "kind": "factor", "factor": "vcp_contraction", "slice_kind": "decile", "decile": 10,
+        "horizon": 60, "direction": "positive", "ledger": "canonical",  # a routing key, irrelevant to match
+    }
+    matched = match_registration(claim, registrations=_FIXTURE_REGISTRATIONS)
+    assert matched is not None
+    assert matched["id"] == "factor-vcp_contraction-d10-h60"
+
+
+def test_match_registration_near_miss_decile_returns_none():
+    """A single differing selector (decile 10 -> 9) is a near-miss -- refused, proving EXACT matching,
+    never fuzzy/superset."""
+    claim = {
+        "kind": "factor", "factor": "vcp_contraction", "slice_kind": "decile", "decile": 9,
+        "horizon": 60, "direction": "positive",
+    }
+    assert match_registration(claim, registrations=_FIXTURE_REGISTRATIONS) is None
+
+
+def test_match_registration_near_miss_horizon_returns_none():
+    """A single differing selector (horizon 60 -> 61) is a near-miss -- refused."""
+    claim = {
+        "kind": "factor", "factor": "vcp_contraction", "slice_kind": "decile", "decile": 10,
+        "horizon": 61, "direction": "positive",
+    }
+    assert match_registration(claim, registrations=_FIXTURE_REGISTRATIONS) is None
+
+
+def test_match_registration_wholly_unregistered_claim_returns_none():
+    claim = {"kind": "factor", "factor": "hv", "slice_kind": "decile", "decile": 10, "horizon": 20}
+    assert match_registration(claim, registrations=_FIXTURE_REGISTRATIONS) is None
+
+
+def test_match_registration_empty_registry_returns_none():
+    claim = {
+        "kind": "factor", "factor": "vcp_contraction", "slice_kind": "decile", "decile": 10,
+        "horizon": 60, "direction": "positive",
+    }
+    assert match_registration(claim, registrations=[]) is None
+
+
+def test_match_registration_combination_leg_order_is_part_of_the_exact_match():
+    """`condition` list ORDER is part of the exact match (a known, accepted sharp edge -- normalizing it
+    would itself be a step toward fuzzy matching, B-901's named dominant trap)."""
+    registrations = [{
+        "id": "combination-x", "selectors": {
+            "kind": "combination", "cohort": "composite",
+            "condition": ["rs_spy_3m:top:quintile", "atr_pct:bottom:tertile"],
+            "horizon": 20, "direction": "positive",
+        },
+        "rationale": "fixture", "registered_by": "backfill", "registered_date": "2026-07-03",
+        "source": "fixture", "status": "tested",
+    }]
+    reordered = {
+        "kind": "combination", "cohort": "composite",
+        "condition": ["atr_pct:bottom:tertile", "rs_spy_3m:top:quintile"],  # legs swapped
+        "horizon": 20, "direction": "positive",
+    }
+    assert match_registration(reordered, registrations=registrations) is None
+
+
+def test_match_registration_defaults_to_load_registrations(tmp_path, monkeypatch):
+    """With `registrations` omitted, `match_registration` reads via `load_registrations()` (the gate's
+    real one-argument call shape)."""
+    path = tmp_path / "registry.jsonl"
+    append_entry(str(path), _FIXTURE_REGISTRATIONS[0])
+    monkeypatch.setenv(REGISTRY_PATH_ENV, str(path))
+    claim = {
+        "kind": "factor", "factor": "vcp_contraction", "slice_kind": "decile", "decile": 10,
+        "horizon": 60, "direction": "positive",
+    }
+    matched = match_registration(claim)
+    assert matched is not None and matched["id"] == "factor-vcp_contraction-d10-h60"
+
+
+# ==================================================================================================
+# The COMMITTED backfill (state/pre-registrations.jsonl) — completeness + no-deletion + round-trip
+# ==================================================================================================
+def test_committed_registry_backfill_is_complete_and_deduplicated():
+    """The DoD anchor: the committed registry is the UNION of proposer-guidance.md §4.1 (4) + §4.2 (3)
+    candidates and every distinct claim selector-set in BOTH ledgers (7 canonical + 7 staging = 14 raw
+    entries), deduplicated by EXACT selector-set — 3 pairs are identical selector-sets (a staging
+    candidate later promoted/re-tested under "ledger":"canonical" with the identical cohort selectors:
+    vcp_contraction d10 h60; rs_spy_3m d10 h60; the rs_spy_3m x high_proximity h20 combination). Since
+    `match_registration` returns ONE row for an exact selector-set, the registry cannot hold two rows
+    sharing an identical selector tuple -- 14 raw entries dedup to 11 distinct rows (see the iter-30 dev
+    handoff for the full reasoning; the spec's literal "≥14" undercounts the cross-ledger overlap)."""
+    assert _COMMITTED_REGISTRY.exists(), f"missing committed registry at {_COMMITTED_REGISTRY}"
+    rows = load_registrations(str(_COMMITTED_REGISTRY))
+    assert len(rows) == 11
+    # append-only: every row is a well-formed registration (no partial/malformed row).
+    required_fields = {"id", "selectors", "rationale", "registered_by", "registered_date", "source", "status"}
+    for row in rows:
+        assert required_fields.issubset(row.keys()), f"row missing fields: {row}"
+        assert row["registered_by"] == "backfill"
+        assert row["registered_date"] == "2026-07-03"  # the ledgers' own register_date, never today
+        assert row["status"] in ("tested", "closed")  # descriptive process vocabulary, NEVER proven-language
+    # ids are unique (stable, collision-free rows).
+    ids = [r["id"] for r in rows]
+    assert len(set(ids)) == len(ids)
+    # selector-sets are unique (the dedup requirement itself -- match_registration must resolve to ONE row).
+    # (a `condition` value is a list -- unhashable -- so compare via a canonical JSON string, not a tuple.)
+    selector_keys = [json.dumps(r["selectors"], sort_keys=True) for r in rows]
+    assert len(set(selector_keys)) == len(selector_keys)
+    # the one PERMANENTLY closed hypothesis (J-19's forward acceptance text: "the ma_stack closed FAIL").
+    ma_stack_rows = [r for r in rows if r["selectors"].get("factor") == "ma_stack"]
+    assert len(ma_stack_rows) == 1 and ma_stack_rows[0]["status"] == "closed"
+
+
+def test_committed_registry_round_trips_every_canonical_ledger_claim():
+    """Every claim in the LIVE canonical ledger matches a backfilled registry row -- the backfill's
+    completeness proven against real data, not just a hand-count."""
+    assert _CANONICAL_LEDGER.exists()
+    rows = load_registrations(str(_COMMITTED_REGISTRY))
+    for entry in read_entries(str(_CANONICAL_LEDGER)):
+        matched = match_registration(entry["claim"], registrations=rows)
+        assert matched is not None, f"canonical claim has NO registry match: {entry['claim']}"
+
+
+def test_committed_registry_round_trips_every_staging_ledger_claim():
+    """Every claim in the LIVE staging ledger matches a backfilled registry row too (both ledgers feed
+    the same registry -- a hypothesis tested under either economy is still a registered hypothesis)."""
+    assert _STAGING_LEDGER.exists()
+    rows = load_registrations(str(_COMMITTED_REGISTRY))
+    for entry in read_entries(str(_STAGING_LEDGER)):
+        matched = match_registration(entry["claim"], registrations=rows)
+        assert matched is not None, f"staging claim has NO registry match: {entry['claim']}"
+
+
+def test_committed_registry_has_no_proven_language():
+    """Anti-goal #1: the registry's `status` vocabulary is descriptive process state, never a proven/
+    not-proven signal -- a "tested" row may have FAILED out-of-sample (every row here did)."""
+    rows = load_registrations(str(_COMMITTED_REGISTRY))
+    banned = {"proven", "pass", "confirmed", "verified", "certified"}
+    for row in rows:
+        assert row["status"].lower() not in banned
diff --git a/apps/frontend/app/research/registry/page.tsx b/apps/frontend/app/research/registry/page.tsx
new file mode 100644
index 0000000..e89472a
--- /dev/null
+++ b/apps/frontend/app/research/registry/page.tsx
@@ -0,0 +1,195 @@
+"use client";
+
+import { useEffect, useState } from "react";
+import Link from "next/link";
+import { AlertTriangle, ArrowLeft, BookMarked } from "lucide-react";
+
+import { useAsOfHref } from "@/components/asof-provider";
+import { PageHeading } from "@/components/page-heading";
+import { Badge } from "@/components/ui/badge";
+import { Card, CardContent } from "@/components/ui/card";
+import { fetchRegistry, type PreRegistrationRow, type RegistryResponse } from "@/lib/api";
+import { formatIsoDate } from "@/lib/dates";
+import { cn } from "@/lib/utils";
+
+/**
+ * /research/registry — the pre-registration registry (goal-mcp-loop iter-30, J-18 / backlog B-901).
+ *
+ * A read-only table of every hypothesis ever registered/tested (selectors, rationale, registration date,
+ * source, status), reading ONLY `GET /api/research/registry` — the SAME file + loader the post-decompose
+ * gate cross-checks an incoming Evidence Claim against. No forms, no mutations: registrations are
+ * appended by the gate/tooling only, never edited here.
+ *
+ * NO proven-language anywhere on this page: `status` ("registered" / "tested" / "closed") is a
+ * descriptive PROCESS state, never a "Proven"/"Not yet proven" signal — a "tested" row may have FAILED
+ * out-of-sample (every row here currently did). Rendered in the Badge `default` (neutral/muted) variant
+ * deliberately, NOT the accent/danger coloring the Evidence page uses for PASS/FAIL, so this column is
+ * never mistaken for an evidence-status badge. The single source of "Proven" stays `/evidence`.
+ */
+export default function RegistryPage() {
+  const [state, setState] = useState<State>({ kind: "loading" });
+
+  useEffect(() => {
+    const controller = new AbortController();
+    setState({ kind: "loading" });
+    fetchRegistry(controller.signal)
+      .then((data) => setState({ kind: "ok", data }))
+      .catch(() => {
+        if (!controller.signal.aborted) setState({ kind: "error" });
+      });
+    return () => controller.abort();
+  }, []);
+
+  const rows = state.kind === "ok" ? state.data.registrations : [];
+
+  return (
+    <div className="space-y-4">
+      <div className="space-y-2">
+        <BackToResearch />
+        <PageHeading
+          title="Pre-registration registry"
+          subtitle="Every hypothesis the system has ever registered or tested — its selectors, economic rationale, and audit-trail date. The post-decompose gate refuses to certify any Evidence Claim that does not match a row here, exactly, before any referee computation runs."
+        />
+      </div>
+
+      {state.kind === "loading" ? <RegistrySkeleton /> : null}
+
+      {state.kind === "error" ? (
+        <Card className="flex items-center gap-3 border-neg bg-surface p-5 text-sm text-neg">
+          <AlertTriangle className="h-5 w-5 shrink-0" aria-hidden />
+          <div>
+            <p className="font-medium">Backend unavailable</p>
+            <p className="text-text-muted">
+              The pre-registration registry could not load from the API. Confirm the backend is running
+              and reload.
+            </p>
+          </div>
+        </Card>
+      ) : null}
+
+      {state.kind === "ok" && rows.length === 0 ? <RegistryEmptyState /> : null}
+
+      {state.kind === "ok" && rows.length > 0 ? <RegistryTable rows={rows} /> : null}
+    </div>
+  );
+}
+
+type State =
+  | { kind: "loading" }
+  | { kind: "ok"; data: RegistryResponse }
+  | { kind: "error" };
+
+/** A same-window link back to the Research hub (mirrors `research/samples/page.tsx`'s pattern exactly). */
+function BackToResearch() {
+  const asofHref = useAsOfHref();
+  return (
+    <Link
+      href={asofHref("/research")}
+      className="inline-flex items-center gap-1 text-xs font-medium text-text-muted hover:text-accent focus-visible:text-accent focus-visible:outline-none"
+    >
+      <ArrowLeft className="h-3.5 w-3.5" aria-hidden /> Back to Research
+    </Link>
+  );
+}
+
+/** The honest empty state — should not occur post-backfill, but the page must degrade gracefully rather
+ *  than crash if the registry file is ever absent/empty (anti-goal: resilience to data-shape change). */
+function RegistryEmptyState() {
+  return (
+    <Card data-testid="registry-empty">
+      <CardContent className="space-y-3 p-6">
+        <div className="flex items-center gap-2">
+          <BookMarked className="h-5 w-5 text-text-faint" aria-hidden />
+          <h2 className="text-sm font-semibold text-text">No registrations yet</h2>
+        </div>
+        <p className="max-w-2xl text-sm text-text-muted">
+          Nothing is registered yet. Once a hypothesis is registered, it appears here with its selectors,
+          rationale, registration date, and source — and only a matching registration lets an Evidence
+          Claim reach the referee.
+        </p>
+      </CardContent>
+    </Card>
+  );
+}
+
+function RegistryTable({ rows }: { rows: PreRegistrationRow[] }) {
+  return (
+    <Card className="p-0">
+      <div className="overflow-x-auto">
+        <table data-testid="registry-table" className="w-full border-collapse text-sm">
+          <thead>
+            <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-text-faint">
+              <th className="px-4 py-2 font-medium">Selectors</th>
+              <th className="px-4 py-2 font-medium">Rationale</th>
+              <th className="px-4 py-2 font-medium">Registered</th>
+              <th className="px-4 py-2 font-medium">Source</th>
+              <th className="px-4 py-2 font-medium">Status</th>
+            </tr>
+          </thead>
+          <tbody>
+            {rows.map((row) => (
+              <tr key={row.id} data-testid="registry-row" className="border-b border-border align-top last:border-b-0">
+                <td className="px-4 py-3">
+                  <SelectorChips selectors={row.selectors} />
+                </td>
+                <td className="max-w-md px-4 py-3 text-text-muted">{row.rationale}</td>
+                <td className="num whitespace-nowrap px-4 py-3 text-text">{formatIsoDate(row.registered_date)}</td>
+                <td className="max-w-xs px-4 py-3 text-xs text-text-faint">{row.source}</td>
+                <td className="px-4 py-3">
+                  <StatusBadge status={row.status} registeredBy={row.registered_by} />
+                </td>
+              </tr>
+            ))}
+          </tbody>
+        </table>
+      </div>
+    </Card>
+  );
+}
+
+/** Render a registration's selectors verbatim as compact key=value chips (mirrors the Evidence page's
+ *  `ClaimHypothesis` presentation) — read-only, re-formats nothing, no numeric edge. */
+function SelectorChips({ selectors }: { selectors: Record<string, unknown> }) {
+  const entries = Object.entries(selectors);
+  if (entries.length === 0) {
+    return <span className="text-text-muted">—</span>;
+  }
+  return (
+    <div className="flex max-w-xs flex-wrap gap-1">
+      {entries.map(([key, value]) => (
+        <Badge key={key} variant="default" className="num whitespace-nowrap text-[11px]">
+          {key}={Array.isArray(value) ? value.join("+") : String(value)}
+        </Badge>
+      ))}
+    </div>
+  );
+}
+
+/** The status column — a descriptive PROCESS state (never proven-language), deliberately rendered in the
+ *  NEUTRAL `default` badge variant (not the accent/danger PASS/FAIL coloring the Evidence page uses), so
+ *  a "tested" row is never mistaken for a proven-ness signal. Backfilled rows are visibly labeled. */
+function StatusBadge({ status, registeredBy }: { status: string; registeredBy: string }) {
+  const isBackfill = registeredBy === "backfill";
+  return (
+    <div className="flex flex-wrap items-center gap-1.5">
+      <Badge variant="default" data-testid="registry-status">
+        {status}
+      </Badge>
+      {isBackfill ? (
+        <Badge variant="default" className="text-text-faint" data-testid="registry-backfill-label">
+          backfill
+        </Badge>
+      ) : null}
+    </div>
+  );
+}
+
+function RegistrySkeleton() {
+  return (
+    <Card className="space-y-2 p-4">
+      {Array.from({ length: 8 }).map((_, i) => (
+        <div key={i} className={cn("h-7 w-full animate-pulse rounded bg-surface-2")} />
+      ))}
+    </Card>
+  );
+}
diff --git a/apps/frontend/lib/registry.ts b/apps/frontend/lib/registry.ts
new file mode 100644
index 0000000..814c4b5
--- /dev/null
+++ b/apps/frontend/lib/registry.ts
@@ -0,0 +1,33 @@
+/**
+ * Pre-registration registry types (goal-mcp-loop iter-30, J-18 / backlog B-901).
+ *
+ * Mirrors `lib/evidence.ts`'s types-plus-small-helpers pattern for the SEPARATE `GET
+ * /api/research/registry` payload — every hypothesis ever registered/tested, read VERBATIM (re-format
+ * only; nothing recomputed).
+ *
+ * This module carries NO proven-language and NO evidence-status resolution: a registration's `status`
+ * ("registered" / "tested" / "closed") is a descriptive PROCESS state, never a "Proven"/"Not yet proven"
+ * signal — a "tested" row may have FAILED out-of-sample (every backfilled row today did). The ONLY source
+ * of "Proven" stays the certified-claims ledger via `lib/evidence.ts` / `GET /api/evidence`; this file
+ * never touches that path.
+ */
+
+/** One pre-registration row, read VERBATIM from `GET /api/research/registry`. `selectors` is the EXACT
+ *  cohort selector-set (`kind` + the present cohort keys + `horizon` + `direction`) the gate matches an
+ *  incoming Evidence Claim against — re-displayed as-is, never recomputed or reformatted into a numeric
+ *  edge. */
+export interface PreRegistrationRow {
+  id: string;
+  selectors: Record<string, unknown>;
+  rationale: string;
+  registered_by: string;
+  registered_date: string;
+  source: string;
+  /** Descriptive process state (e.g. "registered" | "tested" | "closed") — NEVER proven-language. */
+  status: string;
+}
+
+/** The `GET /api/research/registry` payload: every registration, in registration (append) order. */
+export interface RegistryResponse {
+  registrations: PreRegistrationRow[];
+}
```
