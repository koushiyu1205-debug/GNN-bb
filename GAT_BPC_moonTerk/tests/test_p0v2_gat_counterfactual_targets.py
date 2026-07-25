from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest

from lunar_ice_bpc.exact.bpc.guidance.contracts import canonical_universe_hash
from lunar_ice_bpc.guidance.trajectory_targets import (
    COUNTERFACTUAL_TRAJECTORY_SCHEMA_V2,
    COUNTERFACTUAL_TRAINING_OBJECTIVE_V2,
    FIXED_POOL_PRICING_PRESSURE_OBJECTIVE_SPEC_V1,
    P0_CONTROL_ACTION_ID,
    audit_oracle_headroom,
    materialize_counterfactual_targets,
    trajectory_utility,
    validate_counterfactual_trajectory_record,
)


def _record() -> dict:
    candidates = ["task-a", "task-b", "task-unprobed"]
    universe_hash = canonical_universe_hash(
        candidates, universe_kind="task"
    )
    arms = []
    trajectories = {
        P0_CONTROL_ACTION_ID: (
            [(0.5, None), (1.0, -0.4)],
            [(0.5, None), (1.0, -0.5)],
        ),
        "task-a": (
            [(0.25, -0.8), (1.0, -1.0)],
            [(0.30, -0.7), (1.0, -0.9)],
            [(0.28, -0.75), (1.0, -0.95)],
        ),
        "task-b": (
            [(0.65, -0.5), (1.0, -0.6)],
            [(0.70, -0.4), (1.0, -0.6)],
            [(0.68, -0.45), (1.0, -0.55)],
        ),
    }
    trajectories[P0_CONTROL_ACTION_ID] = (
        *trajectories[P0_CONTROL_ACTION_ID],
        [(0.5, None), (1.0, -0.45)],
    )
    for replicate in range(3):
        for action_id, by_replicate in trajectories.items():
            is_control = action_id == P0_CONTROL_ACTION_ID
            arms.append(
                {
                    "action_id": action_id,
                    "intervention_kind": (
                        "control"
                        if action_id == P0_CONTROL_ACTION_ID
                        else "promote_next"
                    ),
                    "replicate_id": f"r{replicate}",
                    "propensity": 1.0 if is_control else 2.0 / 3.0,
                    "action_sampling_probability": (
                        1.0 if is_control else 2.0 / 3.0
                    ),
                    "probe_policy_id": "test_probe_v1",
                    "candidate_pool_size": len(candidates),
                    "candidate_position_under_p0": (
                        None
                        if is_control
                        else candidates.index(action_id) + 1
                    ),
                    "action_selection_reason": (
                        "mandatory_noop" if is_control else "test_probe"
                    ),
                    "run_order": replicate + 1,
                    "machine_block_id": "test-machine",
                    "legal_universe_hash_before_sort": universe_hash,
                    "legal_universe_hash_after_sort": universe_hash,
                    "guidance_filter_count": 0,
                    "guidance_arc_drop_count": 0,
                    "guidance_label_drop_count": 0,
                    "guidance_branch_pair_drop_count": 0,
                    "labels_dropped": False,
                    "binding_match": True,
                    "promotion_requested": not is_control,
                    "promotion_candidate_id": (
                        None if is_control else action_id
                    ),
                    "promotion_installed": not is_control,
                    "promotion_executed": (
                        None if is_control else True
                    ),
                    "actual_execution_rank": (
                        None if is_control else 1
                    ),
                    "first_effective_action_id": (
                        None if is_control else action_id
                    ),
                    "treatment_compliance": (
                        "p0_noop" if is_control else "compliant"
                    ),
                    "noncompliance_reason": "",
                    "termination_reason": "COMPLETED_WITH_EVENT",
                    "memory_adverse_event": False,
                    "trajectory": [
                        {
                            "elapsed_sec": elapsed,
                            "best_true_rc": true_rc,
                            "rmp_progress": None,
                        }
                        for elapsed, true_rc in by_replicate[replicate]
                    ],
                }
            )
    return {
        "schema_version": COUNTERFACTUAL_TRAJECTORY_SCHEMA_V2,
        "snapshot_hash": "snapshot",
        "binding_hash": "binding",
        "instance_content_hash": "instance",
        "rmp_context_hash": "binding",
        "scale": 5,
        "candidate_kind": "task",
        "candidate_ids": candidates,
        "legal_universe_hash_before_sort": universe_hash,
        "pre_action_feature_hash": "features",
        "budget_sec": 1.0,
        "model_wall_time_budget_sec": 1.0,
        "budget_mode": "matched_wall_time",
        "guidance_overhead_included": False,
        "solver_model_cost_separated": True,
        "model_cost_included_in_solver_utility": False,
        "post_action_features_exposed_to_model": False,
        "utility_kind": "negative_discovery_auc",
        "pre_treatment_rc_scale": 1.0,
        "pre_treatment_rc_scale_source": "test_frozen_scale",
        "arms": arms,
    }


def test_counterfactual_record_rejects_confounding_and_leakage() -> None:
    assert validate_counterfactual_trajectory_record(_record())[
        "candidate_kind"
    ] == "task"

    leaked = copy.deepcopy(_record())
    leaked["post_action_features_exposed_to_model"] = True
    with pytest.raises(ValueError, match="leakage"):
        validate_counterfactual_trajectory_record(leaked)

    filtered = copy.deepcopy(_record())
    filtered["arms"][1]["guidance_filter_count"] = 1
    with pytest.raises(ValueError, match="filtered work"):
        validate_counterfactual_trajectory_record(filtered)

    one_replicate = copy.deepcopy(_record())
    one_replicate["arms"] = [
        arm
        for arm in one_replicate["arms"]
        if arm["replicate_id"] in {"r0", "r1"}
    ]
    with pytest.raises(ValueError, match="at least three blocked replicates"):
        validate_counterfactual_trajectory_record(one_replicate)


def test_trajectory_auc_rewards_earlier_and_better_discovery() -> None:
    row = validate_counterfactual_trajectory_record(_record())
    by_id = {}
    for arm in row["arms"]:
        if arm["replicate_id"] == "r0":
            by_id[arm["action_id"]] = arm
    early = trajectory_utility(
        by_id["task-a"],
        budget_sec=1.0,
        utility_kind="negative_discovery_auc",
        rc_scale=1.0,
    )
    late = trajectory_utility(
        by_id["task-b"],
        budget_sec=1.0,
        utility_kind="negative_discovery_auc",
        rc_scale=1.0,
    )
    assert early > late


def test_materialized_targets_never_make_unprobed_action_negative() -> None:
    targets = materialize_counterfactual_targets(
        _record(),
        candidate_ids=["task-a", "task-b", "task-unprobed"],
        bootstrap_samples=128,
        seed=7,
    )
    assert targets["training_objective"] == (
        COUNTERFACTUAL_TRAINING_OBJECTIVE_V2
    )
    assert targets["counterfactual_probe_mask"] == [True, True, False]
    assert targets["counterfactual_target_probabilities"][2] == 0.0
    assert (
        sum(targets["counterfactual_target_probabilities"])
        + targets["counterfactual_noop_target_probability"]
    ) == pytest.approx(
        1.0
    )
    assert targets["counterfactual_advantages"][0] > (
        targets["counterfactual_advantages"][1]
    )
    assert targets["unexplored_candidates_used_as_negative"] is False
    assert targets["p0_control_used_as_model_candidate"] is True


def test_addable_native_event_trajectory_is_diagnostic_only() -> None:
    record = _record()
    record.update(
        {
            "candidate_kind": "harvest",
            "utility_kind": "addable_discovery_auc",
            "formal_first_stage_eligible": True,
            "native_event_trace_valid": True,
            "event_time_source": "native_best_reduced_cost_events_v1",
        }
    )
    record["legal_universe_hash_before_sort"] = canonical_universe_hash(
        record["candidate_ids"], universe_kind="harvest"
    )
    for arm in record["arms"]:
        arm["legal_universe_hash_before_sort"] = record[
            "legal_universe_hash_before_sort"
        ]
        arm["legal_universe_hash_after_sort"] = record[
            "legal_universe_hash_before_sort"
        ]
    report = audit_oracle_headroom(
        [record],
        required_scales=(5,),
        minimum_contexts_per_scale=1,
        minimum_mean_oracle_gain_lcb=1.0e-6,
        minimum_positive_context_fraction_lcb=0.1,
        bootstrap_samples=100,
        seed=7,
    )
    assert not report["passed"]
    assert not report["training_authorized"]

    missing_trace = copy.deepcopy(record)
    missing_trace["native_event_trace_valid"] = False
    rejected = audit_oracle_headroom(
        [missing_trace],
        required_scales=(5,),
        minimum_contexts_per_scale=1,
        bootstrap_samples=100,
    )
    assert not rejected["passed"]
    assert not rejected["passed"]


def test_fixed_pool_pricing_pressure_is_formal_without_native_event_time() -> None:
    record = _record()
    record.update(
        {
            "candidate_kind": "harvest",
            "utility_kind": "fixed_pool_pricing_pressure_auc",
            "trajectory_objective_spec_id": (
                FIXED_POOL_PRICING_PRESSURE_OBJECTIVE_SPEC_V1
            ),
            "formal_first_stage_eligible": True,
            "online_admission_semantics_match": True,
            "event_time_source": "fixed_p0_rmp_rollout_v1",
            "rmp_rollout_trace_valid": True,
            "p0_rollout_policy_hash": "p0-policy",
            "rollout_horizon": 2,
            "phase_objective_mode": "official",
            "initial_active_columns_hash": "initial-columns",
            "initial_basis_hash": "fresh-basis",
            "dual_stabilization_state_hash": "dual-off",
            "worker_policy_hash": "fixed-pool",
            "queue_policy_id": "Q0",
            "column_pool_hash": "pool",
            "cache_state_hash": "fresh-cache",
            "thread_count": 1,
        }
    )
    record["legal_universe_hash_before_sort"] = canonical_universe_hash(
        record["candidate_ids"], universe_kind="harvest"
    )
    for arm in record["arms"]:
        arm["legal_universe_hash_before_sort"] = record[
            "legal_universe_hash_before_sort"
        ]
        arm["legal_universe_hash_after_sort"] = record[
            "legal_universe_hash_before_sort"
        ]
        action_id = arm["action_id"]
        progress = (
            0.8
            if action_id == "task-a"
            else 0.2
            if action_id == "task-b"
            else 0.1
        )
        for index, point in enumerate(arm["trajectory"], start=1):
            point["rmp_progress"] = progress * index / 2.0
            point["fixed_pool_negative_mass_reduction"] = (
                point["rmp_progress"]
            )
            point["fixed_pool_negative_count_reduction"] = (
                point["rmp_progress"]
            )
    targets = materialize_counterfactual_targets(
        record, candidate_ids=record["candidate_ids"]
    )
    assert targets["counterfactual_formal_first_stage_eligible"]
    assert targets["counterfactual_conservative_action_values"][0] > 0.0
    report = audit_oracle_headroom(
        [record],
        required_scales=(5,),
        minimum_contexts_per_scale=1,
        minimum_mean_oracle_gain_lcb=1.0e-6,
        minimum_positive_context_fraction_lcb=0.1,
        bootstrap_samples=100,
    )
    assert report["passed"]


def test_p0_noop_wins_when_every_promotion_is_harmful() -> None:
    record = _record()
    for arm in record["arms"]:
        if arm["action_id"] == P0_CONTROL_ACTION_ID:
            arm["trajectory"] = [
                {
                    "elapsed_sec": 0.1,
                    "best_true_rc": -1.0,
                    "rmp_progress": None,
                },
                {
                    "elapsed_sec": 1.0,
                    "best_true_rc": -1.0,
                    "rmp_progress": None,
                },
            ]
        else:
            arm["trajectory"] = [
                {
                    "elapsed_sec": 0.9,
                    "best_true_rc": -0.1,
                    "rmp_progress": None,
                },
                {
                    "elapsed_sec": 1.0,
                    "best_true_rc": -0.1,
                    "rmp_progress": None,
                },
            ]
    targets = materialize_counterfactual_targets(
        record,
        candidate_ids=record["candidate_ids"],
    )
    assert targets["counterfactual_noop_target_probability"] > max(
        targets["counterfactual_target_probabilities"]
    )
    assert max(
        value
        for value, mask in zip(
            targets["counterfactual_conservative_action_values"],
            targets["counterfactual_probe_mask"],
            strict=True,
        )
        if mask
    ) < 0.0


def test_memory_event_is_competing_risk_not_right_censor() -> None:
    record = _record()
    memory_arm = next(
        arm
        for arm in record["arms"]
        if arm["action_id"] == "task-a"
        and arm["replicate_id"] == "r0"
    )
    memory_arm["termination_reason"] = "MEMORY_LIMIT"
    memory_arm["memory_adverse_event"] = True
    memory_arm["resource_safety_gate_pass"] = False
    memory_arm["trajectory"] = [
        {
            "elapsed_sec": 1.0,
            "best_true_rc": None,
            "rmp_progress": None,
        }
    ]
    targets = materialize_counterfactual_targets(
        record,
        candidate_ids=record["candidate_ids"],
    )
    assert len(targets["survival_candidate_indices"]) == 8
    assert targets["counterfactual_memory_adverse_event_rates"][0] == (
        pytest.approx(1.0 / 3.0)
    )


def test_rmp_gold_target_requires_frozen_p0_rollout_contract() -> None:
    record = _record()
    record["utility_kind"] = "rmp_progress_auc"
    for arm in record["arms"]:
        for point in arm["trajectory"]:
            point["rmp_progress"] = 0.0
    with pytest.raises(ValueError, match="frozen P0 rollout contract"):
        validate_counterfactual_trajectory_record(record)


def test_noncompliant_intervention_remains_in_intention_to_treat_data() -> None:
    record = _record()
    arm = next(
        arm
        for arm in record["arms"]
        if arm["action_id"] == "task-b"
        and arm["replicate_id"] == "r0"
    )
    arm["promotion_executed"] = False
    arm["actual_execution_rank"] = None
    arm["first_effective_action_id"] = "task-a"
    arm["treatment_compliance"] = "not_executed"
    arm["noncompliance_reason"] = "candidate_became_ineligible"
    normalized = validate_counterfactual_trajectory_record(record)
    retained = next(
        row
        for row in normalized["arms"]
        if row["action_id"] == "task-b"
        and row["replicate_id"] == "r0"
    )
    assert retained["treatment_compliance"] == "not_executed"


def test_only_observable_route_harvest_record_is_formal_first_stage() -> None:
    record = _record()
    action_map = {
        "task-a": "route-a",
        "task-b": "route-b",
        "task-unprobed": "route-unprobed",
    }
    record["candidate_kind"] = "harvest"
    record["candidate_ids"] = [
        action_map[candidate_id]
        for candidate_id in record["candidate_ids"]
    ]
    legal_hash = canonical_universe_hash(
        record["candidate_ids"], universe_kind="harvest"
    )
    record["legal_universe_hash_before_sort"] = legal_hash
    record["utility_kind"] = "addable_discovery_auc"
    record["formal_first_stage_eligible"] = True
    for arm in record["arms"]:
        if arm["action_id"] in action_map:
            arm["action_id"] = action_map[arm["action_id"]]
            arm["promotion_candidate_id"] = arm["action_id"]
        arm["legal_universe_hash_before_sort"] = legal_hash
        arm["legal_universe_hash_after_sort"] = legal_hash
    targets = materialize_counterfactual_targets(
        record,
        candidate_ids=record["candidate_ids"],
    )
    assert targets["counterfactual_candidate_kind"] == "harvest"
    # Addability discovery alone is diagnostic.  Formal first-stage training
    # now requires the frozen pressure objective and online admission
    # semantics to match.
    assert targets["counterfactual_formal_first_stage_eligible"] is False


def test_counterfactual_and_censor_losses_are_finite_and_masked() -> None:
    torch = pytest.importorskip("torch")
    from lunar_ice_bpc.guidance.training import (
        counterfactual_soft_listwise_loss,
        discrete_time_survival_nll,
        survival_concordance_loss,
    )

    scores = torch.tensor([0.0, 0.0, 100.0], requires_grad=True)
    loss = counterfactual_soft_listwise_loss(
        scores,
        torch.tensor([0.75, 0.25, 0.0]),
        torch.tensor([1.0, 1.0, 0.0]),
    )
    loss.backward()
    assert torch.isfinite(loss)
    assert scores.grad is not None
    assert float(scores.grad[2]) == 0.0

    hazards = torch.zeros((3, 4), requires_grad=True)
    indices = torch.tensor([0, 1, 2])
    times = torch.tensor([0.25, 0.75, 1.0])
    events = torch.tensor([1.0, 1.0, 0.0])
    survival = discrete_time_survival_nll(
        hazards, indices, times, events
    )
    concordance = survival_concordance_loss(
        hazards, indices, times, events
    )
    assert torch.isfinite(survival)
    assert torch.isfinite(concordance)
    assert float(survival.detach()) > 0.0


def test_counterfactual_model_exposes_rank_curve_and_hazard_heads() -> None:
    torch = pytest.importorskip("torch")
    from lunar_ice_bpc.guidance.models import (
        SURVIVAL_HAZARD_BINS,
        build_model,
    )

    model = build_model("linear", node_input_dim=6, edge_input_dim=3)
    output = model(
        node_features=torch.zeros((3, 6)),
        edge_index=torch.tensor([[0, 1], [1, 2]]),
        edge_features=torch.zeros((2, 3)),
        task_node_indices=torch.tensor([1, 2]),
        resource_context=torch.tensor([1.0, 2.0, 0.0, 0.0]),
        harvest_task_masks=torch.tensor(
            [[0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
        ),
        harvest_context=torch.zeros((2, 4)),
    )
    assert output["task_scores"].shape == (2,)
    assert output["task_advantages"].shape == (2,)
    assert output["task_hazard_logits"].shape == (
        2,
        SURVIVAL_HAZARD_BINS,
    )
    assert output["arc_hazard_logits"].shape == (
        2,
        SURVIVAL_HAZARD_BINS,
    )
    assert output["harvest_hazard_logits"].shape == (
        2,
        SURVIVAL_HAZARD_BINS,
    )
    assert output["harvest_noop_score"].shape == ()
    assert output["harvest_noop_hazard_logits"].shape == (
        SURVIVAL_HAZARD_BINS,
    )


def test_training_script_uses_counterfactual_losses_for_main_heads() -> None:
    torch = pytest.importorskip("torch")
    script_path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "train_p0v2_gat_model_ladder.py"
    )
    spec = importlib.util.spec_from_file_location(
        "p0v2_counterfactual_training_script", script_path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    from lunar_ice_bpc.guidance.models import build_model

    model = build_model("linear", node_input_dim=6, edge_input_dim=3)
    row = {
        "scale": 5,
        "head": "exact_pricing",
        "training_objective": COUNTERFACTUAL_TRAINING_OBJECTIVE_V2,
        "node_features": [[0.0] * 6 for _ in range(3)],
        "edge_features": [[0.0] * 3 for _ in range(2)],
        "edge_index": [[0, 1], [1, 2]],
        "task_node_indices": [1, 2],
        "resource_context": [1.0, 2.0, 0.0, 0.0],
    }
    for prefix in ("task", "arc"):
        row.update(
            {
                f"{prefix}_counterfactual_target_probabilities": [0.8, 0.2],
                f"{prefix}_counterfactual_advantages": [0.3, -0.1],
                f"{prefix}_counterfactual_probe_mask": [1.0, 1.0],
                f"{prefix}_counterfactual_noop_target_probability": 0.1,
                f"{prefix}_counterfactual_noop_probe_mask": 1.0,
                f"{prefix}_survival_candidate_indices": [0, 1, 2],
                f"{prefix}_survival_time_fractions": [0.5, 0.25, 1.0],
                f"{prefix}_survival_event_observed": [1.0, 1.0, 0.0],
            }
        )
    normalization = module._fit_normalization([row])
    tensors = module._tensors(row, normalization)
    output = model(**tensors["inputs"])
    losses = module._row_head_losses("exact_pricing", output, tensors)
    assert set(losses) == {
        "task_counterfactual_rank_plus_survival",
        "arc_counterfactual_rank_plus_survival",
    }
    assert all(torch.isfinite(loss) for loss in losses.values())
