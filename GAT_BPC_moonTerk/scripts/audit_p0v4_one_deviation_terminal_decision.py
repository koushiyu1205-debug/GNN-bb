#!/usr/bin/env python3
"""Bind the terminal decision for the P0V4 one-deviation GAT branch.

The original route-promotion action and the later sparse-tail revision are
audited separately.  A failed opportunity/signal/harm gate is a valid terminal
branch outcome under the predeclared plan, but it never becomes evidence that
GAT improves solve time and never authorizes an actionful runtime.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "lunar_ice_bpc.p0v4_one_deviation_terminal_decision.v1"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--route-census", required=True)
    parser.add_argument("--route-signal-gate", required=True)
    parser.add_argument("--sparse-tail-audit", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    audit = audit_terminal_decision(
        route_census_path=_resolve(args.route_census),
        route_signal_gate_path=_resolve(args.route_signal_gate),
        sparse_tail_audit_path=_resolve(args.sparse_tail_audit),
    )
    output = _resolve(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(audit, indent=2, sort_keys=True))
    return 0 if audit["terminal_decision_valid"] else 2


def audit_terminal_decision(
    *,
    route_census_path: Path,
    route_signal_gate_path: Path,
    sparse_tail_audit_path: Path,
) -> dict:
    paths = (
        route_census_path.resolve(),
        route_signal_gate_path.resolve(),
        sparse_tail_audit_path.resolve(),
    )
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        return _invalid(paths, [f"missing:{value}" for value in missing])
    route_census = _load_json(route_census_path)
    route_signal = _load_json(route_signal_gate_path)
    sparse_tail = _load_json(sparse_tail_audit_path)

    issues = []
    census_audit = dict(route_census.get("audit") or {})
    route_scale30 = dict(
        dict(census_audit.get("scales") or {}).get("30") or {}
    )
    route_scale50 = dict(
        dict(census_audit.get("scales") or {}).get("50") or {}
    )
    if bool(census_audit.get("gate_pass")):
        issues.append("route_opportunity_census_unexpectedly_passed")
    if bool(census_audit.get("gat_oracle_authorized")):
        issues.append("route_oracle_unexpectedly_authorized")
    if str(census_audit.get("failure_policy") or "") != (
        "stop_route_gat_and_report_insufficient_action_opportunity"
    ):
        issues.append("route_census_failure_policy_mismatch")
    if not bool(route_scale30.get("gate_pass")):
        issues.append("route_scale30_opportunity_gate_not_demonstrated")
    if bool(route_scale50.get("gate_pass")):
        issues.append("route_scale50_opportunity_gate_unexpectedly_passed")

    if str(route_signal.get("status") or "") != (
        "STOP_OR_REVISE_ACTION_DEFINITION"
    ):
        issues.append("route_signal_terminal_status_mismatch")
    if bool(route_signal.get("signal_gate_pass")):
        issues.append("route_signal_gate_unexpectedly_passed")
    if bool(route_signal.get("gat_training_authorized")):
        issues.append("route_training_unexpectedly_authorized")
    if int(route_signal.get("redline_count") or 0) != 0:
        issues.append("route_signal_redline")

    if str(sparse_tail.get("status") or "") != (
        "SHADOW_ONLY_STOP_FIXED_PILOT"
    ):
        issues.append("sparse_tail_terminal_status_mismatch")
    if not bool(sparse_tail.get("artifact_integrity_pass")):
        issues.append("sparse_tail_artifact_integrity_failed")
    if bool(sparse_tail.get("gat_fixed_end_to_end_gate_pass")):
        issues.append("sparse_tail_end_to_end_gate_unexpectedly_passed")
    if bool(sparse_tail.get("five_percent_solve_time_gate_pass")):
        issues.append("sparse_tail_five_percent_gate_unexpectedly_passed")
    if bool(sparse_tail.get("baseline_mutated")):
        issues.append("sparse_tail_mutated_baseline")
    fixed_budget = dict(sparse_tail.get("fixed_budget_contract") or {})
    if not bool(fixed_budget.get("evidence_collection_closed")):
        issues.append("sparse_tail_evidence_collection_not_closed")
    if bool(fixed_budget.get("additional_context_collection_authorized")):
        issues.append("sparse_tail_additional_collection_authorized")
    model = dict(sparse_tail.get("model_summary") or {})
    if bool(model.get("evaluation_authorized")) or bool(
        model.get("deployment_authorized")
    ):
        issues.append("sparse_tail_model_has_actionful_authority")
    if str(model.get("runtime_fallback") or "") != "NOOP":
        issues.append("sparse_tail_runtime_fallback_is_not_noop")

    valid = not issues
    return {
        "schema_version": SCHEMA,
        "status": (
            "STOPPED_BY_PREDECLARED_GATES"
            if valid
            else "INVALID_TERMINAL_DECISION"
        ),
        "terminal_decision_valid": valid,
        "issues": issues,
        "route_promotion_branch": {
            "opportunity_gate_pass": bool(census_audit.get("gate_pass")),
            "scale30_context_count": int(
                route_scale30.get("eligible_context_count") or 0
            ),
            "scale30_instance_count": int(
                route_scale30.get("eligible_instance_count") or 0
            ),
            "scale50_context_count": int(
                route_scale50.get("eligible_context_count") or 0
            ),
            "scale50_instance_count": int(
                route_scale50.get("eligible_instance_count") or 0
            ),
            "signal_gate_pass": bool(route_signal.get("signal_gate_pass")),
            "strong_signal_context_count": int(
                route_signal.get("strong_signal_context_count") or 0
            ),
            "oracle_authorized": False,
            "formal_training_authorized": False,
            "deployment_authorized": False,
        },
        "sparse_tail_revision_branch": {
            "fixed_context_count": int(
                dict(sparse_tail.get("data_summary") or {}).get(
                    "context_count"
                )
                or 0
            ),
            "observed_action_count": int(
                dict(sparse_tail.get("data_summary") or {}).get(
                    "observed_action_count"
                )
                or 0
            ),
            "beneficial_action_count": int(
                dict(sparse_tail.get("data_summary") or {}).get(
                    "beneficial_action_count"
                )
                or 0
            ),
            "calibration_beneficial_action_count": int(
                dict(sparse_tail.get("data_summary") or {}).get(
                    "calibration_beneficial_action_count"
                )
                or 0
            ),
            "artifact_integrity_pass": bool(
                sparse_tail.get("artifact_integrity_pass")
            ),
            "five_percent_gate_evaluable": bool(
                sparse_tail.get("five_percent_solve_time_gate_evaluable")
            ),
            "five_percent_gate_pass": bool(
                sparse_tail.get("five_percent_solve_time_gate_pass")
            ),
            "deployment_authorized": False,
            "runtime_fallback": "NOOP",
        },
        "exact_acceptance_may_proceed_without_gat": valid,
        "gat_formal_acceptance_required": False if valid else None,
        "gat_performance_claim_authorized": False,
        "one_deviation_implementation_claim_authorized": valid,
        "interpretation": (
            "the one-deviation mechanism and safety shell were implemented "
            "and exercised, while both action definitions failed their "
            "predeclared progression gates; Exact evaluation proceeds without "
            "an actionful GAT candidate"
        ),
        "certificate_or_bound_role": "none",
        "baseline_mutated": False,
        "artifacts": [
            {"path": str(path), "sha256": _sha256(path)} for path in paths
        ],
    }


def _invalid(paths: tuple[Path, ...], issues: list[str]) -> dict:
    return {
        "schema_version": SCHEMA,
        "status": "INVALID_TERMINAL_DECISION",
        "terminal_decision_valid": False,
        "issues": issues,
        "exact_acceptance_may_proceed_without_gat": False,
        "gat_formal_acceptance_required": None,
        "gat_performance_claim_authorized": False,
        "one_deviation_implementation_claim_authorized": False,
        "certificate_or_bound_role": "none",
        "baseline_mutated": False,
        "artifacts": [
            {"path": str(path), "sha256": None} for path in paths
        ],
    }


def _load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"expected JSON object: {path}")
    return value


def _sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _resolve(value: str | Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


if __name__ == "__main__":
    raise SystemExit(main())
