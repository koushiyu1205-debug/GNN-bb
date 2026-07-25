#!/usr/bin/env python3
"""Select the smallest statistically justified P0 V2 model rung."""

from __future__ import annotations

import argparse
import json
from math import isfinite
from pathlib import Path

from lunar_ice_bpc.guidance.evaluation import holm_rejections
from lunar_ice_bpc.guidance.models import MODEL_LADDER
from lunar_ice_bpc.guidance.training import model_selection_key
from lunar_ice_bpc.guidance.trajectory_targets import (
    COUNTERFACTUAL_TRAINING_OBJECTIVE_V2,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-metrics-jsonl", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--alpha", type=float, default=0.05)
    args = parser.parse_args()
    rows = []
    for line in Path(args.candidate_metrics_jsonl).read_text(
        encoding="utf-8"
    ).splitlines():
        if line.strip():
            rows.append(json.loads(line))
    by_kind = {}
    for row in rows:
        kind = str(row["model_kind"])
        if kind not in MODEL_LADDER:
            raise SystemExit(f"unsupported model rung {kind!r}")
        if kind in by_kind:
            raise SystemExit(f"duplicate model rung {kind!r}")
        if str(row.get("training_objective") or "") != (
            COUNTERFACTUAL_TRAINING_OBJECTIVE_V2
        ):
            raise SystemExit(
                "model-rung selection rejects legacy grade objectives"
            )
        by_kind[kind] = row
    if not by_kind:
        raise SystemExit("no candidate metrics")
    split_hashes = {
        str(row.get("split_manifest_hash") or "") for row in rows
    }
    if len(split_hashes) != 1 or not next(iter(split_hashes)):
        raise SystemExit(
            "all candidate rungs must share one non-empty split manifest hash"
        )
    highest = max(MODEL_LADDER.index(kind) for kind in by_kind)
    missing_rungs = [
        kind for kind in MODEL_LADDER[: highest + 1] if kind not in by_kind
    ]
    if missing_rungs:
        raise SystemExit(
            "model ladder cannot skip smaller rungs: "
            + ",".join(missing_rungs)
        )

    p_values = {
        kind: float(row["p_value_vs_next_smaller"])
        for kind, row in by_kind.items()
        if row.get("p_value_vs_next_smaller") is not None
    }
    holm = holm_rejections(p_values, alpha=float(args.alpha))
    decisions = []
    required_review_gates = (
        "safety_gate_pass",
        "scale5_10_non_degradation",
        "stage_b_gate_pass",
        "inference_overhead_gate_pass",
        "counterfactual_context_coverage_gate",
        "counterfactual_worst_scale_lcb_gate",
        "gold_trajectory_gate",
        "p0_noop_calibration_gate",
        "route_harvest_first_stage_gate",
        "memory_resource_safety_gate",
        "net_advantage_after_model_cost_gate",
        "instance_snapshot_bootstrap_unit_gate",
        "scale50_100_safety_only_gate",
        "unbiased_sentinel_opportunity_density_gate",
        "perfect_policy_net_benefit_gate",
        "cheap_preimport_eligibility_gate",
    )
    selected = None
    smaller_kind = None
    ladder_stopped = False
    for kind in MODEL_LADDER:
        row = by_kind.get(kind)
        if row is None:
            continue
        basic_gate = all(
            bool(row.get(gate_name))
            for gate_name in required_review_gates
        )
        opportunity_roi_eligible_scales = sorted(
            {
                int(value)
                for value in row.get(
                    "opportunity_roi_eligible_scales", ()
                )
            }
        )
        if not opportunity_roi_eligible_scales:
            basic_gate = False
        significance_required = smaller_kind is not None
        significant = (
            not significance_required
            or bool(holm.get(kind, False))
        )
        strictly_better = (
            not significance_required
            or bool(row.get("significantly_better_than_next_smaller"))
        )
        eligible = basic_gate and significant and strictly_better
        if ladder_stopped:
            eligible = False
        decisions.append(
            {
                "model_kind": kind,
                "basic_gate_pass": basic_gate,
                "significance_required": significance_required,
                "holm_reject_vs_next_smaller": bool(
                    holm.get(kind, False)
                ),
                "significantly_better_than_next_smaller": bool(
                    row.get("significantly_better_than_next_smaller")
                ),
                "eligible": eligible,
                "required_review_gates": {
                    gate_name: bool(row.get(gate_name))
                    for gate_name in required_review_gates
                },
                "opportunity_roi_eligible_scales": (
                    opportunity_roi_eligible_scales
                ),
                "lexicographic_key": [
                    value if not isinstance(value, float) or isfinite(value) else None
                    for value in model_selection_key(row)
                ],
                "ladder_already_stopped": ladder_stopped,
            }
        )
        if eligible:
            selected = row
        elif selected is not None:
            ladder_stopped = True
        smaller_kind = kind
    report = {
        "schema_version": "lunar_ice_bpc.gat_model_rung_selection.v2",
        "training_objective": COUNTERFACTUAL_TRAINING_OBJECTIVE_V2,
        "passed": selected is not None,
        "selected_model_kind": (
            None if selected is None else selected["model_kind"]
        ),
        "selected_checkpoint_family": (
            None
            if selected is None
            else selected.get("checkpoint_family")
        ),
        "selected_pcgrad_enabled": (
            False
            if selected is None
            else bool(selected.get("pcgrad_enabled"))
        ),
        "split_manifest_hash": next(iter(split_hashes)),
        "smallest_model_rule_enforced": True,
        "required_review_gates": list(required_review_gates),
        "exact_advantage_scales": [5, 10, 20, 30],
        "large_scale_evaluation_scope": (
            "scale50_100_safety_ood_resource_shadow_only"
        ),
        "holm_alpha": float(args.alpha),
        "holm_rejections": holm,
        "decisions": decisions,
        "calibration_used": False,
        "protected_final_test_used": False,
        "on_failure": "fallback_p0",
    }
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    print(str(target.resolve()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
