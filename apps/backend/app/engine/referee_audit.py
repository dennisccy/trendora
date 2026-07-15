"""The **referee-calibration harness** — placebo + lookahead-tripwire audit of the certifier itself
(goal-mcp-loop iter-36, J-22 / backlog B-102).

`app.engine.referee` (`certify_edge`) has never been negatively controlled: it stamps "PASS"/"FAIL" but
nobody has measured whether its own false-pass rate matches the α it claims to enforce. This module is
that calibration battery:

  1. **Seeded null factors** — `permute_null_observations` takes a REAL factor's per-date cross-section
     (a real cohort/control observation pair from an existing Research-lab claim) and, independently for
     each of `n_null_trials`, randomly reassigns which observed VALUES belong to "cohort" vs "control" on
     each date. This preserves the EXACT multiset of realized returns observed (the distribution is
     untouched) while destroying any true relationship between group membership and outcome — the
     textbook permutation-test null. Each permuted pair is certified through the SAME PURE
     `referee.certify_edge` used everywhere else; since there is by construction no real signal left, a
     well-calibrated referee should PASS roughly a fraction α of these (never more) — the "empirical
     false-pass rate" the report discloses.
  2. **One lookahead-contaminated factor** — a "factor" whose value literally equals the stock's own
     realized forward return at `contaminated_factor_horizon` (the "perfect crime" a broken harness would
     certify instantly, since ranking BY the very quantity being evaluated guarantees an enormous
     apparent edge). The referee's sealed-holdout machinery has no way to detect this class of
     contamination (it is baked into the OBSERVATIONS themselves, not a temporal boundary leak), so
     either the referee legitimately REJECTS it (an honest, welcome outcome) or it PASSES — in which case
     the report's `contaminated_caught` flag is False and the panel must render a LOUD, un-hideable
     tripwire failure state. Both outcomes are honest; only HIDING a PASS would be dishonest.

ISOLATION (the dominant failure mode — B-102's own naming): every certification this module runs — every
null trial AND the one contaminated trial — uses a FRESH `RefereeState(n_trials=1, ...)` (never derived
from any ledger's accumulated count) and writes ONLY to an explicit, caller-supplied THROWAWAY
`ledger_path` via the ordinary `app.engine.ledger.append_entry` seam. It NEVER opens, reads, or writes the
real `certified-claims.jsonl`, `staging-ledger.jsonl`, or the real Thresholdout budget — there is no code
path in this module that can reach those files. `run_referee_audit` also NEVER writes anything to the
`certified-claims.jsonl`/`staging-ledger.jsonl` writer (`app.mcp.tools.verify_edge`); it calls
`referee.certify_edge` directly.

DB-FREE WHEN INJECTED (mirrors `app.engine.forward_walk`'s `Assembler` idiom exactly): `run_referee_audit`
accepts injectable `assemble_source` / `assemble_contaminated` callables. Omit them (the production call
shape used by `_main`, the offline job) and this module lazily imports `app.mcp.tools.assemble_claim_
observations` plus the stored `forward_returns` table to pull REAL data — `session` is required only
then. Inject synthetic ones (as every test here does) and NO database is ever touched, exactly like
`tests/test_referee.py` / `tests/test_forward_walk.py`'s established pattern — this is what makes the CI
variant fast and seed-independent of the 30-year committed seed.

Persistence mirrors `app.engine.drift` exactly: `resolve_referee_audit_path()` (env override, else
config, resolved against `REPO_ROOT`), `write_referee_audit_report()` (temp-file-then-rename), and
`read_referee_audit_report()` (missing artifact -> `None`; unparseable -> an honest `status: "unreadable"`
dict — NEVER a raise).

Run the real offline job::

    python -m app.engine.referee_audit

(200 null trials by default via `config.research.referee_audit.n_null_trials`; persists the artifact at
the configured `report_path`.)
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Callable, Optional

import numpy as np

from app.config import REPO_ROOT, get_config
from app.engine import ledger as ledger_mod
from app.engine.referee import (
    DEFAULT_ALPHA_BUDGET,
    DEFAULT_ALPHA_PER_TEST,
    STATUS_INSUFFICIENT,
    STATUS_PASS,
    RefereeState,
    certify_edge,
)

# The environment-variable NAME (the NAME only — never a path VALUE literal in code) the runtime
# referee-audit report path may be overridden with. Mirrors `app.engine.drift.DRIFT_REPORT_PATH_ENV`.
REFEREE_AUDIT_PATH_ENV = "TRENDORA_REFEREE_AUDIT_PATH"

# Minimum names in one date's stored `forward_returns` cross-section to form a meaningful top-decile
# split for the lookahead-contaminated factor's construction — a date with fewer names than this is
# honestly skipped, never a fabricated 1-name "decile" (mirrors the referee's own thin-sample honesty).
_MIN_CROSS_SECTION_NAMES = 10
# "top decile" — the same 1/10 convention every Factor-Lab cohort in this codebase uses.
_DECILE_DIVISOR = 10

# The 97.5th percentile of the standard normal distribution — the two-sided z-score for a 95% Wilson
# score confidence interval on a binomial proportion. A named constant (never an inline magic number).
_WILSON_Z_95 = 1.959963984540054

# An assembler returning the REAL source claim's `(cohort_obs, control_obs, horizon)` the null generator
# permutes. Mirrors `app.engine.forward_walk.Assembler`.
SourceAssembler = Callable[[], tuple[list, list, int]]
# An assembler returning the lookahead-contaminated `(cohort_obs, control_obs)` (the horizon is the
# config-sourced `contaminated_factor_horizon`, supplied by the caller, not the assembler).
ContaminatedAssembler = Callable[[], tuple[list, list]]

# The two kinds of throwaway-ledger entries this harness appends (an audit trail of the run, never the
# real certified-claims schema's `claim`/`register_date` shape — these rows are diagnostic only).
_KIND_NULL = "null"
_KIND_CONTAMINATED = "contaminated"

# Every field key a fully-built report carries — used to construct the honest, uniformly-None fallback
# when a persisted artifact exists but cannot be parsed (mirrors `app.engine.drift`'s unreadable shape).
_REPORT_FIELDS = (
    "run_date", "n_null_trials", "seed", "alpha", "source_factor", "false_pass_count",
    "false_pass_rate", "false_pass_ci_low", "false_pass_ci_high", "n_insufficient_null",
    "contaminated_factor_horizon", "contaminated_verdict", "contaminated_expected_outcome",
    "contaminated_caught",
)


# ==================================================================================================
# Persistence — mirrors app.engine.drift exactly
# ==================================================================================================
def resolve_referee_audit_path() -> str:
    """The referee-audit report artifact path: the `TRENDORA_REFEREE_AUDIT_PATH` env override if set,
    else `config.research.referee_audit.report_path` resolved against `REPO_ROOT` when relative. Mirrors
    `app.engine.drift.resolve_drift_report_path()` exactly, so every reader/writer agrees on the SAME
    file. No path literal lives here — the default lives in config (anti-goal: No magic numbers)."""
    override = os.environ.get(REFEREE_AUDIT_PATH_ENV)
    if override:
        return override
    configured = Path(get_config().research.referee_audit.report_path)
    if not configured.is_absolute():
        configured = REPO_ROOT / configured
    return str(configured)


def _default_throwaway_ledger_path() -> str:
    """The default ISOLATED throwaway ledger the harness certifies null/contaminated trials against when
    the caller supplies none — co-located with the report artifact's directory, NEVER one of the real
    ledger paths (`evidence.resolve_ledger_path()` / `graveyard.resolve_staging_ledger_path()` are never
    referenced anywhere in this module). Overwritten fresh at the start of every `run_referee_audit` call
    (see `run_referee_audit`'s docstring) — a disposable per-run audit trail, not an accumulating ledger."""
    report_path = resolve_referee_audit_path()
    parent = os.path.dirname(os.path.abspath(report_path))
    return str(Path(parent) / "referee-audit-throwaway-ledger.jsonl")


def write_referee_audit_report(report: dict) -> None:
    """Persist the SINGLE referee-audit report artifact (OVERWRITE — only the latest run matters).
    Creates the parent directory on first write. Written via a temp-file-then-rename so a reader never
    observes a partially-written file. Mirrors `app.engine.drift.write_drift_report` exactly."""
    path = resolve_referee_audit_path()
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, sort_keys=True, default=str)
    os.replace(tmp_path, path)


def read_referee_audit_report() -> Optional[dict]:
    """The SINGLE reader the endpoint (and any future consumer) calls — no second parse path.

    - Missing artifact (the offline job has never run) -> `None`, the honest inert case.
    - Unparseable artifact -> an honest `{"status": "unreadable", ...all other fields None...}` dict —
      NEVER a raise, and never silently treated as a clean/passing run."""
    path = resolve_referee_audit_path()
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        data = None
    if not isinstance(data, dict) or "run_date" not in data:
        return {"status": "unreadable", **{key: None for key in _REPORT_FIELDS}}
    return data


# ==================================================================================================
# (1) Seeded null-factor generator — PURE, exact
# ==================================================================================================
def permute_null_observations(cohort_obs: list, control_obs: list, *, rng: np.random.Generator) -> tuple[list, list]:
    """The seeded null-factor generator (B-102 How #1): a PER-DATE random permutation of a real factor's
    cross-section. For each date present in `cohort_obs` and/or `control_obs`, pool the values observed
    that date, randomly reassign them back into groups of the SAME original per-date sizes, and repeat
    independently per date. This preserves the EXACT multiset of realized values (the distribution is
    untouched — nothing is fabricated) while destroying any true relationship between group membership
    and value (the textbook permutation-test null). PURE: no filesystem/DB access; deterministic given
    `rng`'s own state."""
    by_date_cohort: dict = {}
    by_date_control: dict = {}
    for d, v in cohort_obs:
        by_date_cohort.setdefault(d, []).append(v)
    for d, v in control_obs:
        by_date_control.setdefault(d, []).append(v)

    null_cohort: list = []
    null_control: list = []
    for d in sorted(set(by_date_cohort) | set(by_date_control)):
        cohort_vals = by_date_cohort.get(d, [])
        control_vals = by_date_control.get(d, [])
        pool = cohort_vals + control_vals
        if not pool:
            continue
        n_cohort = len(cohort_vals)
        idx = rng.permutation(len(pool))
        shuffled = [pool[i] for i in idx]
        for v in shuffled[:n_cohort]:
            null_cohort.append((d, v))
        for v in shuffled[n_cohort:]:
            null_control.append((d, v))
    return null_cohort, null_control


# ==================================================================================================
# Binomial proportion confidence interval — PURE, numpy/scipy-free (mirrors referee.py's own discipline)
# ==================================================================================================
def binomial_ci(successes: int, n: int) -> tuple[float, float]:
    """The 95% Wilson score confidence interval for a binomial proportion (`successes` out of `n`
    trials). Chosen over the naive Wald interval because it stays well-behaved at the extremes this audit
    routinely sees (0, or very few, false-passes out of ~200 trials) — Wald degenerates to a zero-width
    `[0, 0]` at zero successes, which would misleadingly read as "we are CERTAIN the true rate is exactly
    0". A closed-form formula anyone can hand-verify; no scipy dependency. Returns `(low, high)`, clamped
    to `[0, 1]`. `n == 0` returns the honest full interval `(0.0, 1.0)` — no observations, no information."""
    if n <= 0:
        return (0.0, 1.0)
    z = _WILSON_Z_95
    phat = successes / n
    denom = 1.0 + (z * z) / n
    center = phat + (z * z) / (2 * n)
    margin = z * math.sqrt((phat * (1 - phat)) / n + (z * z) / (4 * n * n))
    low = (center - margin) / denom
    high = (center + margin) / denom
    return (max(0.0, low), min(1.0, high))


# ==================================================================================================
# Report assembly — PURE
# ==================================================================================================
def build_referee_audit_report(
    *,
    run_date: str,
    n_null_trials: int,
    seed: int,
    alpha: float,
    false_pass_count: int,
    n_insufficient_null: int,
    source_factor: str,
    contaminated_factor_horizon: int,
    contaminated_verdict: dict,
) -> dict:
    """PURE assembly of the `/research/referee-audit` report dict from already-computed pieces —
    recomputes nothing beyond the `binomial_ci` formula on the supplied count. `contaminated_expected_
    outcome` is a STATIC disclosure label (`"rejected"`) per B-102's report spec — it is NOT a claim
    about what actually happened; `contaminated_caught` is the honest DERIVED boolean
    (`status != "PASS"`) the panel uses to choose between its calm and its loud tripwire-failure
    treatment. `status: "ok"` marks a report that was actually built by a real run (vs. the `read_referee_
    audit_report` "unreadable" fallback, which never calls this function)."""
    false_pass_rate = false_pass_count / n_null_trials if n_null_trials > 0 else 0.0
    ci_low, ci_high = binomial_ci(false_pass_count, n_null_trials)
    return {
        "status": "ok",
        "run_date": run_date,
        "n_null_trials": n_null_trials,
        "seed": seed,
        "alpha": alpha,
        "source_factor": source_factor,
        "false_pass_count": false_pass_count,
        "false_pass_rate": false_pass_rate,
        "false_pass_ci_low": ci_low,
        "false_pass_ci_high": ci_high,
        "n_insufficient_null": n_insufficient_null,
        "contaminated_factor_horizon": contaminated_factor_horizon,
        "contaminated_verdict": contaminated_verdict,
        "contaminated_expected_outcome": "rejected",
        "contaminated_caught": contaminated_verdict.get("status") != STATUS_PASS,
    }


# ==================================================================================================
# The harness orchestrator
# ==================================================================================================
def run_referee_audit(
    session=None,
    *,
    cfg=None,
    ledger_path: Optional[str] = None,
    run_date: Optional[str] = None,
    assemble_source: Optional[SourceAssembler] = None,
    assemble_contaminated: Optional[ContaminatedAssembler] = None,
    source_factor_label: Optional[str] = None,
) -> dict:
    """Run the full referee-calibration harness and return the (UNPERSISTED) report dict — the single
    orchestration entry point both `_main()` (the real offline job) and every test in this module
    exercise. Call `write_referee_audit_report(report)` separately to persist it (mirrors `app.engine.
    drift`'s build/write split).

    ISOLATION (the dominant failure mode): every null trial AND the one contaminated trial runs through
    `referee.certify_edge` DIRECTLY (never `app.mcp.tools.verify_edge`) against a FRESH
    `RefereeState(n_trials=1, alpha_budget_remaining=DEFAULT_ALPHA_BUDGET)` — never derived from any
    ledger's accumulated count — and each verdict is appended ONLY to `ledger_path` (a THROWAWAY file,
    freshly overwritten at the start of THIS call so repeated invocations never accumulate). This module
    contains no reference anywhere to `evidence.resolve_ledger_path()` or `graveyard.resolve_staging_
    ledger_path()`, so there is no code path that could reach the real `certified-claims.jsonl` /
    `staging-ledger.jsonl`. `ledger_path` defaults to a co-located throwaway file
    (`_default_throwaway_ledger_path()`) when omitted; tests pass an explicit `tmp_path`-backed path.

    DB-FREE WHEN INJECTED: `assemble_source` / `assemble_contaminated` mirror `app.engine.forward_walk`'s
    `Assembler` idiom. Omit them (the production call shape `_main` uses) and this pulls REAL data via
    `app.mcp.tools.assemble_claim_observations` (the first configured Factor-Lab factor's top decile) plus
    the stored `forward_returns` table (lazily imported — `session` is required only then, mirroring
    `forward_walk._default_assembler`). Inject synthetic ones (every test in this module) and NO
    session/DB is ever touched.

    DETERMINISM: given the same `cfg.research.referee_audit.seed` and the same source/contaminated
    observations, every null trial's permutation + bootstrap draws a per-trial `seed + i`, so the whole
    run (false-pass rate, CI, contaminated verdict) reproduces byte-identically."""
    cfg = cfg or get_config()
    ra_cfg = cfg.research.referee_audit
    if ledger_path is None:
        ledger_path = _default_throwaway_ledger_path()
    # Fresh start every run — a disposable audit trail for THIS run only, never an accumulating ledger.
    if os.path.exists(ledger_path):
        os.remove(ledger_path)

    if assemble_source is None:
        assemble_source, source_factor_label = _default_source_assembler(session, cfg)
    source_cohort, source_control, source_horizon = assemble_source()

    if assemble_contaminated is None:
        cohort_dates = {d for d, _ in source_cohort} | {d for d, _ in source_control}
        assemble_contaminated = _default_contaminated_assembler(session, cfg, cohort_dates)
    contaminated_cohort, contaminated_control = assemble_contaminated()

    if run_date is None:
        run_date = _default_run_date(session)

    false_pass = 0
    n_insufficient = 0
    for i in range(1, ra_cfg.n_null_trials + 1):
        trial_seed = ra_cfg.seed + i
        null_cohort, null_control = permute_null_observations(
            source_cohort, source_control, rng=np.random.default_rng(trial_seed)
        )
        verdict = certify_edge(
            null_cohort, null_control, horizon=source_horizon,
            state=RefereeState(n_trials=1, alpha_budget_remaining=DEFAULT_ALPHA_BUDGET),
            seed=trial_seed,
        )
        ledger_mod.append_entry(
            ledger_path, {"trial": i, "kind": _KIND_NULL, "verdict": verdict.to_dict()}
        )
        if verdict.status == STATUS_PASS:
            false_pass += 1
        elif verdict.status == STATUS_INSUFFICIENT:
            n_insufficient += 1

    contaminated_verdict = certify_edge(
        contaminated_cohort, contaminated_control, horizon=ra_cfg.contaminated_factor_horizon,
        state=RefereeState(n_trials=1, alpha_budget_remaining=DEFAULT_ALPHA_BUDGET),
        seed=ra_cfg.seed,
    )
    ledger_mod.append_entry(
        ledger_path, {"kind": _KIND_CONTAMINATED, "verdict": contaminated_verdict.to_dict()}
    )

    return build_referee_audit_report(
        run_date=run_date,
        n_null_trials=ra_cfg.n_null_trials,
        seed=ra_cfg.seed,
        alpha=DEFAULT_ALPHA_PER_TEST,
        false_pass_count=false_pass,
        n_insufficient_null=n_insufficient,
        source_factor=source_factor_label or "unknown",
        contaminated_factor_horizon=ra_cfg.contaminated_factor_horizon,
        contaminated_verdict=contaminated_verdict.to_dict(),
    )


# ==================================================================================================
# Default (DB-backed) assemblers — lazily imported, exactly like app.engine.forward_walk's
# ==================================================================================================
def _default_source_assembler(session, cfg) -> tuple[SourceAssembler, str]:
    """The PRODUCTION source assembler: the first configured Factor-Lab factor's top-decile claim (a REAL
    Research-lab cohort), via the SHARED `assemble_claim_observations` seam `verify_edge` also uses.
    Imported LAZILY so importing this module stays light (numpy + referee + ledger only) and DB-free
    tests never drag in the MCP/tools/SQLAlchemy stack — mirrors `forward_walk._default_assembler`."""
    from app.mcp.tools import assemble_claim_observations

    factor_key = cfg.research.factor_lab.factors[0].key
    claim = {
        "kind": "factor", "factor": factor_key, "slice_kind": "decile", "decile": 10,
        "horizon": cfg.walk_forward.default_horizon,
    }

    def assemble():
        return assemble_claim_observations(session, claim)

    return assemble, factor_key


def _default_contaminated_assembler(session, cfg, cohort_dates: set) -> ContaminatedAssembler:
    """The PRODUCTION lookahead-contaminated assembler: for each date in `cohort_dates` (the SAME
    already-vetted date span the source claim uses — bounded, never a whole-table scan, mirroring
    `app.mcp.tools._benchmark_control_observations`'s own cohort_dates-bounded query shape), read every
    stock's realized forward return at `contaminated_factor_horizon` from the ALREADY-STORED
    `forward_returns` table (the SAME table `_benchmark_control_observations` reads, just without a
    single-symbol filter), rank descending, and split into the top decile ("cohort" — the contaminated
    'factor' IS its own future return) vs. the rest ("control"). A date with fewer than
    `_MIN_CROSS_SECTION_NAMES` names is honestly skipped, never a fabricated 1-name split."""
    from collections import defaultdict

    from sqlmodel import select

    from app.models import ForwardReturn, ScannerRun

    horizon = cfg.research.referee_audit.contaminated_factor_horizon

    def assemble():
        stmt = (
            select(ScannerRun.asof_date, ForwardReturn.symbol, ForwardReturn.realized_return)
            .join(ScannerRun, ScannerRun.id == ForwardReturn.run_id)
            .where(ForwardReturn.horizon == horizon)
        )
        by_date: dict = defaultdict(list)
        for asof_date, _symbol, realized in session.exec(stmt).all():
            if realized is None:
                continue
            if cohort_dates and asof_date not in cohort_dates:
                continue
            by_date[asof_date].append(float(realized))

        cohort: list = []
        control: list = []
        for d, values in by_date.items():
            if len(values) < _MIN_CROSS_SECTION_NAMES:
                continue
            ranked = sorted(values, reverse=True)
            cut = max(1, len(ranked) // _DECILE_DIVISOR)
            for v in ranked[:cut]:
                cohort.append((d, v))
            for v in ranked[cut:]:
                control.append((d, v))
        return cohort, control

    return assemble


def _default_run_date(session) -> str:
    """The DB's latest data date — the default run-date anchor (mirrors `forward_walk._default_as_of_
    date`; never `date.today()` — this project's standing no-wall-clock discipline). Imported lazily."""
    from app.engine.prices import latest_data_date

    latest = latest_data_date(session)
    return latest.isoformat() if latest is not None else "unknown"


# ==================================================================================================
# CLI — the config-seeded OFFLINE job (mirrors `app.engine.forward_walk`'s `_main` shape)
# ==================================================================================================
def _main(argv: Optional[list] = None) -> int:  # pragma: no cover — exercised via the real offline run
    """`python -m app.engine.referee_audit` — opens a real session, runs the full harness at the
    configured `n_null_trials` (200 by default), and persists the artifact at the configured
    `report_path`. This IS the "one-off offline invocation" the phase spec calls for: nothing in the
    product wires a UI action to trigger it (J-22 is read-only), so this script is the build step that
    materializes the real, persisted artifact the panel then re-reads verbatim."""
    from sqlmodel import Session

    from app.db import get_engine

    with Session(get_engine()) as session:
        report = run_referee_audit(session)
    write_referee_audit_report(report)
    print(
        f"referee-audit @ {report['run_date']}: {report['false_pass_count']}/{report['n_null_trials']} "
        f"false-pass (rate={report['false_pass_rate']:.4f}, alpha={report['alpha']}), "
        f"contaminated verdict={report['contaminated_verdict']['status']} "
        f"caught={report['contaminated_caught']} -> {resolve_referee_audit_path()}"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_main())
