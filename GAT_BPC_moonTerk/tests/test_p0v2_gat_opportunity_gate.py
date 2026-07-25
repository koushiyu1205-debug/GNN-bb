from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys

import pytest

from lunar_ice_bpc.exact.core.cuts import stable_payload_hash
from lunar_ice_bpc.guidance.opportunity_gate import (
    MATCHED_END_TO_END_MEASUREMENT_SCHEMA_V2,
    OPPORTUNITY_OBSERVATION_SCHEMA_V1,
    attach_matched_end_to_end_benefit,
    audit_opportunity_roi,
    validate_opportunity_observation,
)


def _observation(
    *,
    index: int,
    instance: str,
    stream: str = "sentinel",
    positive: bool = False,
    time_benefit: float | None = None,
    model_cost: float = 0.01,
) -> dict:
    return {
        "schema_version": OPPORTUNITY_OBSERVATION_SCHEMA_V1,
        "observation_id": f"{stream}-{instance}-{index}",
        "instance_content_hash": instance,
        "rmp_context_hash": f"context-{instance}-{index}",
        "executed_objective_spec_id": "test-objective.v1",
        "scale": 20,
        "sampling_stream": stream,
        "selection_probability": 0.5 if stream == "sentinel" else 1.0,
        "selection_manifest_hash": "pre-action-manifest",
        "selection_decision_pre_action": True,
        "target_condition_used_for_selection": stream == "targeted",
        "context_sequence_id": index,
        "solver_elapsed_sec": float(index),
        "cheap_gate_eligible": True,
        "cheap_gate_wall_sec": 0.001,
        "legal_action_count": 4,
        "rollout_attempted": True,
        "formal_label_available": True,
        "opportunity_outcome_status": "FORMAL_COUNTERFACTUAL",
        "action_value_identifiable": positive,
        "oracle_solver_gain": 0.1 if positive else 0.0,
        "oracle_solver_time_saved_sec_lcb": (
            time_benefit if positive else None
        ),
        "time_benefit_source": (
            "matched_end_to_end_counterfactual_lcb"
            if positive and time_benefit is not None
            else ""
        ),
        "model_would_be_invoked": True,
        "model_call_wall_sec_upper_bound": model_cost,
        "model_cost_source": "frozen_budget_upper_bound",
        "startup_cost_share_sec": 0.001,
        "calibration_used": False,
        "protected_final_test_used": False,
    }


def test_targeted_rows_never_inflate_population_opportunity_rate() -> None:
    sentinel = [
        _observation(
            index=index,
            instance=f"instance-{index // 5}",
            positive=index % 2 == 0,
            time_benefit=0.1,
        )
        for index in range(20)
    ]
    targeted = [
        _observation(
            index=index,
            instance=f"targeted-{index}",
            stream="targeted",
            positive=True,
            time_benefit=10.0,
        )
        for index in range(100)
    ]
    report = audit_opportunity_roi(
        [*sentinel, *targeted],
        required_scales=(20,),
        minimum_sentinel_contexts_per_scale=20,
        minimum_sentinel_instances_per_scale=4,
        minimum_positive_context_fraction_lcb=0.1,
        bootstrap_samples=200,
        seed=11,
    )
    scale = report["scale_reports"]["20"]
    assert report["passed"]
    assert report["targeted_context_count"] == 100
    assert scale[
        "targeted_context_count_excluded_from_population_estimates"
    ] == 100
    assert scale["funnel"]["oracle_positive_rate"] == pytest.approx(0.5)
    assert scale[
        "conservative_perfect_policy_net_gain_sec_per_context"
    ] > 0.0


def test_sparse_opportunities_fail_even_for_a_perfect_ranker() -> None:
    rows = []
    for instance_index in range(4):
        for local_index in range(25):
            rows.append(
                _observation(
                    index=local_index,
                    instance=f"instance-{instance_index}",
                    positive=local_index == 0,
                    time_benefit=0.1,
                    model_cost=0.01,
                )
            )
    report = audit_opportunity_roi(
        rows,
        required_scales=(20,),
        minimum_sentinel_contexts_per_scale=100,
        minimum_sentinel_instances_per_scale=4,
        minimum_positive_context_fraction_lcb=0.01,
        bootstrap_samples=200,
        seed=13,
    )
    scale = report["scale_reports"]["20"]
    assert not report["passed"]
    assert scale["funnel"]["oracle_positive_rate"] == pytest.approx(0.04)
    assert scale[
        "instance_bootstrap_net_gain_sec_per_context_ucb95"
    ] < 0.0
    assert scale["sequential_decision"] == "STOP_ACTION_FAMILY_AS_FUTILE"


def test_behaviorally_equivalent_actions_are_structural_zeroes() -> None:
    rows = []
    for instance_index in range(4):
        for local_index in range(5):
            row = _observation(
                index=local_index,
                instance=f"instance-{instance_index}",
                positive=False,
            )
            row.update(
                {
                    "formal_label_available": False,
                    "opportunity_outcome_status": (
                        "STRUCTURAL_ZERO_ACTION_EQUIVALENT"
                    ),
                    "action_value_identifiable": False,
                    "model_would_be_invoked": False,
                    "model_call_wall_sec_upper_bound": 0.0,
                    "model_cost_source": "",
                }
            )
            rows.append(row)
    report = audit_opportunity_roi(
        rows,
        required_scales=(20,),
        minimum_sentinel_contexts_per_scale=20,
        minimum_sentinel_instances_per_scale=4,
        minimum_positive_context_fraction_lcb=0.0,
        bootstrap_samples=100,
    )
    scale = report["scale_reports"]["20"]
    assert not report["training_authorized"]
    assert scale["measurement_complete_gate"]
    assert scale["instance_bootstrap_net_gain_sec_per_context_ucb95"] < 0.0
    assert scale["sequential_decision"] == "STOP_ACTION_FAMILY_AS_FUTILE"


def test_duplicate_canonical_context_cannot_inflate_sample_size() -> None:
    left = _observation(index=0, instance="instance", positive=False)
    right = copy.deepcopy(left)
    right["observation_id"] = "different-id-same-context"
    report = audit_opportunity_roi(
        [left, right],
        required_scales=(20,),
        minimum_sentinel_contexts_per_scale=1,
        minimum_sentinel_instances_per_scale=1,
        bootstrap_samples=100,
    )
    assert report["duplicate_context_count"] == 1
    assert report["sentinel_context_count"] == 1
    assert report["rejection_reasons"] == {
        "duplicate_sentinel_context": 1
    }


def test_futility_uses_benefit_ucb_not_conservative_lcb() -> None:
    rows = []
    for instance_index in range(4):
        for local_index in range(5):
            row = _observation(
                index=local_index,
                instance=f"instance-{instance_index}",
                positive=True,
                time_benefit=0.0,
            )
            row["oracle_solver_time_saved_sec_ucb"] = 1.0
            rows.append(row)
    report = audit_opportunity_roi(
        rows,
        required_scales=(20,),
        minimum_sentinel_contexts_per_scale=20,
        minimum_sentinel_instances_per_scale=4,
        minimum_positive_context_fraction_lcb=0.1,
        bootstrap_samples=100,
    )
    assert not report["linear_training_authorized"]
    assert (
        report[
            "equal_scale_perfect_policy_net_gain_sec_per_context_ucb95"
        ]
        > 0.0
    )
    assert report["route_admission_decision"] == (
        "CONTINUE_MATCHED_PAIRED_COLLECTION"
    )


def test_pressure_gain_without_end_to_end_time_saving_cannot_pass_roi() -> None:
    rows = [
        _observation(
            index=index,
            instance=f"instance-{index // 5}",
            positive=True,
            time_benefit=None,
        )
        for index in range(20)
    ]
    report = audit_opportunity_roi(
        rows,
        required_scales=(20,),
        minimum_sentinel_contexts_per_scale=20,
        minimum_sentinel_instances_per_scale=4,
        minimum_positive_context_fraction_lcb=0.1,
        bootstrap_samples=100,
    )
    scale = report["scale_reports"]["20"]
    assert not report["passed"]
    assert scale["missing_end_to_end_time_benefit_count"] == 20
    assert not scale["measurement_complete_gate"]
    assert scale["sequential_decision"] == "CONTINUE_SENTINEL_COLLECTION"


def test_sentinel_selection_cannot_depend_on_observed_target() -> None:
    row = _observation(
        index=0,
        instance="instance",
        positive=False,
    )
    row["target_condition_used_for_selection"] = True
    with pytest.raises(ValueError, match="target-independent"):
        validate_opportunity_observation(row)

    protected = copy.deepcopy(row)
    protected["target_condition_used_for_selection"] = False
    protected["protected_final_test_used"] = True
    with pytest.raises(ValueError, match="protected data"):
        validate_opportunity_observation(protected)


def test_end_to_end_time_benefit_requires_exact_safe_paired_replicates() -> None:
    observation = _observation(
        index=0,
        instance="instance",
        positive=True,
        time_benefit=None,
    )
    measurements = []
    for index, saving in enumerate((0.05, 0.04, 0.06)):
        measurements.append(
            {
                "schema_version": (
                    MATCHED_END_TO_END_MEASUREMENT_SCHEMA_V2
                ),
                "observation_id": observation["observation_id"],
                "instance_content_hash": observation[
                    "instance_content_hash"
                ],
                "rmp_context_hash": observation["rmp_context_hash"],
                "selection_manifest_hash": observation[
                    "selection_manifest_hash"
                ],
                "executed_objective_spec_id": "test-objective.v1",
                "action_frozen_before_outcome": True,
                "fresh_process_pair": True,
                "pair_order_randomized": True,
                "pair_run_order": (
                    "P0_THEN_ACTION"
                    if index % 2 == 0
                    else "ACTION_THEN_P0"
                ),
                "matched_budget_id": "budget-v1",
                "canonical_action_binding_hash": "binding-v1",
                "promotion_requested": True,
                "promotion_installed": True,
                "promotion_executed": True,
                "actual_execution_rank": 1,
                "treatment_compliance": "compliant",
                "replicate_id": f"replicate-{index}",
                "oracle_action_id": "route-a",
                "p0_solver_wall_sec": 1.0,
                "action_solver_wall_sec": 1.0 - saving,
                "p0_exact_status": "OPTIMAL",
                "action_exact_status": "OPTIMAL",
                "p0_exact_complete": True,
                "action_exact_complete": True,
                "p0_objective": 12.0,
                "action_objective": 12.0,
                "legal_universe_hash_before_sort": "universe",
                "action_legal_universe_hash_before_sort": "universe",
                "guidance_filter_count": 0,
                "extra_incomplete": False,
                "certificate_semantics_changed": False,
            }
        )
    enriched = attach_matched_end_to_end_benefit(
        observation, measurements
    )
    assert enriched["oracle_solver_time_saved_sec_lcb"] > 0.0
    assert enriched["oracle_solver_time_saved_sec_ucb"] >= (
        enriched["oracle_solver_time_saved_sec_lcb"]
    )
    assert enriched["time_benefit_source"] == (
        "matched_end_to_end_counterfactual_lcb"
    )
    assert enriched["solver_time_benefit_measurement"][
        "model_cost_included"
    ] is False

    mismatched = copy.deepcopy(measurements)
    mismatched[0]["action_objective"] = 12.1
    with pytest.raises(ValueError, match="objectives differ"):
        attach_matched_end_to_end_benefit(observation, mismatched)


def test_sentinel_manifest_is_pre_action_and_deterministic(tmp_path) -> None:
    instances = tmp_path / "instances.json"
    split = tmp_path / "split.json"
    rows = [
        {
            "accepted": True,
            "instance_content_hash": f"hash-{index}",
            "instance_id": f"instance-{index}",
            "scale": 20,
            "path": f"instance-{index}.json",
        }
        for index in range(8)
    ]
    instances.write_text(
        json.dumps({"instances": rows}), encoding="utf-8"
    )
    split.write_text(
        json.dumps(
            {
                "manifest_hash": "split-hash",
                "audit": {"passed": True},
                "development": [
                    {
                        "instance_content_hash": row[
                            "instance_content_hash"
                        ]
                    }
                    for row in rows
                ],
                "calibration": [],
                "protected_final_test": [],
            }
        ),
        encoding="utf-8",
    )
    outputs = [tmp_path / "sentinel-a.json", tmp_path / "sentinel-b.json"]
    for output in outputs:
        subprocess.run(
            [
                sys.executable,
                "scripts/build_p0v2_gat_sentinel_manifest.py",
                "--instance-manifest",
                str(instances),
                "--split-manifest",
                str(split),
                "--output",
                str(output),
                "--probability",
                "20=0.5",
                "--seed",
                "17",
            ],
            cwd=Path(__file__).resolve().parents[1],
            check=True,
            capture_output=True,
            text=True,
        )
    left = json.loads(outputs[0].read_text(encoding="utf-8"))
    right = json.loads(outputs[1].read_text(encoding="utf-8"))
    assert left == right
    assert left["selection_uses_target_or_outcome"] is False
    assert left["sampling_design"].startswith("pre_action_bernoulli")


def test_route_admission_collector_uses_actual_scale_limit(
    tmp_path,
) -> None:
    manifest = {
        "schema_version": "lunar_ice_bpc.gat_sentinel_manifest.v1",
        "instances": [
            {
                "instance_content_hash": "instance",
                "instance_id": "instance",
                "scale": 20,
                "path": "instance.json",
                "selected": True,
                "selection_probability": 0.5,
            }
        ],
    }
    manifest["manifest_hash"] = stable_payload_hash(manifest)
    manifest_path = tmp_path / "sentinel.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    rows = tmp_path / "rows" / "instance"
    for index, addable_count in enumerate((32, 33)):
        target = rows / f"context-{index}"
        target.mkdir(parents=True)
        (target / "harvest.json").write_text(
            json.dumps(
                {
                    "scale": 20,
                    "instance_content_hash": "instance",
                    "rmp_context_hash": f"context-{index}",
                    "harvest_grades": [3.0] * addable_count,
                }
            ),
            encoding="utf-8",
        )
    output = tmp_path / "observations.jsonl"
    report = tmp_path / "report.json"
    subprocess.run(
        [
            sys.executable,
            "scripts/collect_p0v2_gat_route_admission_sentinel.py",
            "--sentinel-manifest",
            str(manifest_path),
            "--training-rows-dir",
            str(tmp_path / "rows"),
            "--output-jsonl",
            str(output),
            "--report",
            str(report),
            "--scales",
            "20",
            "--p0-admission-limit-by-scale",
            "20=32",
        ],
        cwd=Path(__file__).resolve().parents[1],
        check=True,
        capture_output=True,
        text=True,
    )
    rows = [
        json.loads(line)
        for line in output.read_text(encoding="utf-8").splitlines()
    ]
    assert rows[0]["opportunity_outcome_status"] == (
        "STRUCTURAL_ZERO_ACTION_EQUIVALENT"
    )
    assert rows[1]["route_admission_effective_action_count"] == 1
    assert rows[1]["opportunity_outcome_status"] == (
        "CENSORED_RESOURCE_OR_DISCOVERY"
    )
