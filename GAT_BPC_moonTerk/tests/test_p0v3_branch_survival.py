from __future__ import annotations

import pytest
import importlib.util
import hashlib
import json
from pathlib import Path
import sys


def _formal_row() -> dict:
    from lunar_ice_bpc.guidance.branch_survival import (
        BRANCH_CHILD_SURVIVAL_RMST_OBJECTIVE_V1,
        BRANCH_E2E_REGRET_LISTWISE_OBJECTIVE_V2,
    )

    return {
        "branch_training_objective": (
            BRANCH_CHILD_SURVIVAL_RMST_OBJECTIVE_V1
        ),
        "branch_primary_training_objective": (
            BRANCH_E2E_REGRET_LISTWISE_OBJECTIVE_V2
        ),
        "instance_generator_domain": (
            "synthetic_polar_resource_grid_v1"
        ),
        "node_phase": "root_fractional_exact_node",
        "branch_pairs": [[1, 2], [1, 3], [2, 3]],
        "branch_context": [[0.5, 0.5, 1.0, 0.0]] * 3,
        "branch_child_observed_time_fractions": [[0.5, 1.0]] * 3,
        "branch_child_event_observed": [[1.0, 0.0]] * 3,
        "branch_child_observed_mask": [[1.0, 1.0]] * 3,
        "legal_branch_shortlist_hash_before_sort": "same",
        "legal_branch_shortlist_hash_after_sort": "same",
        "guidance_branch_pair_drop_count": 0,
    }


def test_formal_row_rejects_legacy_scalar_cost() -> None:
    from lunar_ice_bpc.guidance.branch_survival import (
        validate_branch_survival_row,
    )

    row = _formal_row()
    validate_branch_survival_row(row)
    row["branch_cost"] = 3.0
    with pytest.raises(ValueError, match="legacy scalar"):
        validate_branch_survival_row(row)


def test_p0v3_survival_loss_is_isolated_from_legacy_cost_module() -> None:
    from lunar_ice_bpc.guidance.branch_survival import (
        discrete_time_survival_nll,
    )

    assert discrete_time_survival_nll.__module__ == (
        "lunar_ice_bpc.guidance.survival_losses"
    )


def test_formal_row_requires_recognized_generator_domain() -> None:
    from lunar_ice_bpc.guidance.branch_survival import (
        validate_branch_survival_row,
    )

    row = _formal_row()
    row["instance_generator_domain"] = "unknown_generator"
    with pytest.raises(ValueError, match="instance-generator domain"):
        validate_branch_survival_row(row)


def test_deep_formal_row_requires_exact_node_specific_snapshot() -> None:
    from lunar_ice_bpc.guidance.branch_survival import (
        validate_branch_survival_row,
    )

    row = {
        **_formal_row(),
        "node_phase": "deep_fractional_exact_node",
        "parent_snapshot_origin": "exact_p0_deep_parent_snapshot",
    }
    validate_branch_survival_row(row)
    row["parent_snapshot_origin"] = "reconstructed_from_root_pool"
    with pytest.raises(ValueError, match="node-specific P0 snapshot"):
        validate_branch_survival_row(row)


def test_rmst_is_physical_horizon_fraction() -> None:
    torch = pytest.importorskip("torch")
    from lunar_ice_bpc.guidance.branch_survival import (
        restricted_mean_survival_fraction,
    )

    early_hazard = torch.tensor([[8.0, 8.0, 8.0, 8.0]])
    late_hazard = torch.tensor([[-8.0, -8.0, -8.0, -8.0]])
    early = restricted_mean_survival_fraction(early_hazard)
    late = restricted_mean_survival_fraction(late_hazard)
    assert 0.0 < float(early.item()) < float(late.item()) <= 1.0


def test_pair_input_swap_is_symmetric_and_outputs_two_children() -> None:
    torch = pytest.importorskip("torch")
    from lunar_ice_bpc.guidance.branch_survival import (
        build_branch_survival_model,
    )

    torch.manual_seed(7)
    model = build_branch_survival_model(
        "gat1x32x1",
        node_input_dim=5,
        edge_input_dim=3,
    )
    common = {
        "node_features": torch.randn(4, 5),
        "edge_index": torch.tensor(
            [[0, 1, 2, 3], [1, 2, 3, 0]],
            dtype=torch.long,
        ),
        "edge_features": torch.randn(4, 3),
        "branch_context": torch.tensor([[0.5, 0.5, 1.0, 0.0]]),
    }
    left = model(
        **common,
        branch_pairs=torch.tensor([[1, 2]], dtype=torch.long),
    )
    right = model(
        **common,
        branch_pairs=torch.tensor([[2, 1]], dtype=torch.long),
    )
    assert left["branch_child_hazard_logits"].shape == (1, 2, 4)
    assert torch.allclose(
        left["branch_child_hazard_logits"],
        right["branch_child_hazard_logits"],
    )
    assert torch.allclose(left["branch_scores"], right["branch_scores"])


def test_censored_child_contributes_survival_not_fake_event() -> None:
    torch = pytest.importorskip("torch")
    from lunar_ice_bpc.guidance.branch_survival import (
        branch_survival_losses,
    )

    hazard = torch.zeros(1, 2, 4, requires_grad=True)
    output = {
        "branch_child_hazard_logits": hazard,
        "branch_scores": torch.tensor([-1.0], requires_grad=True),
    }
    losses = branch_survival_losses(
        output,
        observed_time_fractions=torch.tensor([[0.5, 1.0]]),
        event_observed=torch.tensor([[1.0, 0.0]]),
        observed_mask=torch.tensor([[1.0, 1.0]]),
    )
    assert set(losses) == {"branch_child_survival_nll"}
    losses["branch_child_survival_nll"].backward()
    # The censored child only asks all observed hazards to stay low.
    assert bool((hazard.grad[0, 1] > 0.0).all())


def test_e2e_primary_loss_is_regret_weighted_and_action_aligned() -> None:
    torch = pytest.importorskip("torch")
    from lunar_ice_bpc.guidance.branch_survival import (
        branch_survival_losses,
    )

    output = {
        "branch_child_hazard_logits": torch.zeros(3, 2, 4),
        "branch_scores": torch.tensor(
            [0.0, 2.0, -1.0],
            requires_grad=True,
        ),
    }
    losses = branch_survival_losses(
        output,
        observed_time_fractions=torch.full((3, 2), 0.5),
        event_observed=torch.ones(3, 2),
        observed_mask=torch.ones(3, 2),
        e2e_gold_rank_index=torch.tensor([1]),
        e2e_wall_sec_by_rank=torch.tensor([100.0, 80.0, 140.0]),
    )
    assert set(losses) == {
        "branch_child_survival_nll",
        "branch_e2e_gold_listwise",
        "branch_e2e_expected_normalized_regret",
    }
    assert float(
        losses["branch_e2e_expected_normalized_regret"].detach()
    ) > 0.0
    (
        losses["branch_e2e_gold_listwise"]
        + losses["branch_e2e_expected_normalized_regret"]
    ).backward()
    assert output["branch_scores"].grad is not None
    assert float(output["branch_scores"].grad[1]) < 0.0


def test_trusted_censored_pairwise_pushes_exact_winner_up() -> None:
    torch = pytest.importorskip("torch")
    from lunar_ice_bpc.guidance.branch_survival import (
        branch_survival_losses,
    )

    output = {
        "branch_child_hazard_logits": torch.zeros(3, 2, 4),
        "branch_scores": torch.zeros(3, requires_grad=True),
    }
    losses = branch_survival_losses(
        output,
        observed_time_fractions=torch.ones(3, 2),
        event_observed=torch.zeros(3, 2),
        observed_mask=torch.ones(3, 2),
        e2e_trusted_pairwise_preferences=torch.tensor([[2, 0]]),
    )
    pairwise = losses["branch_e2e_trusted_censored_pairwise"]
    pairwise.backward()

    assert float(output["branch_scores"].grad[2]) < 0.0
    assert float(output["branch_scores"].grad[0]) > 0.0


def test_dedicated_trainer_uses_fold_train_normalization_and_e2e_gold() -> None:
    torch = pytest.importorskip("torch")
    script = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "train_p0v3_branch_survival_ladder.py"
    )
    spec = importlib.util.spec_from_file_location(
        "branch_survival_trainer",
        script,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    base = _formal_row()
    rows = []
    for index, scale in enumerate((20, 30)):
        rows.append(
            {
                **base,
                "scale": scale,
                "instance_content_hash": f"instance-{index}",
                "path_hash": f"path-{index}",
                "node_features": [
                    [float(index)] * 7,
                    [float(index + 1)] * 7,
                    [float(index + 2)] * 7,
                    [float(index + 3)] * 7,
                ],
                "edge_features": [
                    [0.1] * 3,
                    [0.2] * 3,
                    [0.3] * 3,
                    [0.4] * 3,
                ],
                "edge_index": [[0, 1, 2, 3], [1, 2, 3, 0]],
                "branch_e2e_gold_rank_index": index,
                "branch_e2e_gold_net_gain_sec": 0.98,
                "branch_e2e_p0_control_wall_sec": 10.0,
                "branch_guidance_lifecycle_overhead_sec": 0.02,
                "branch_e2e_cost_semantics": (
                    "p0_control_raw_wall_vs_all_guided_actions_"
                    "uniform_lifecycle_overhead.v1"
                ),
                "branch_e2e_wall_sec_by_rank": {
                    "0": 10.02,
                    "1": 9.02,
                    "2": 11.02,
                },
            }
        )
    normalization = module._fit_normalization(rows)
    from lunar_ice_bpc.guidance.branch_survival import (
        build_branch_survival_model,
    )

    model = build_branch_survival_model(
        "mlp2x32",
        node_input_dim=7,
        edge_input_dim=3,
    )
    history = module._train(
        model,
        rows,
        normalization,
        validation_rows=rows,
        epochs=2,
        learning_rate=1.0e-3,
    )
    evaluated = module._evaluate(model, rows, normalization)
    assert len(history["total_loss_history"]) == 2
    assert len(history["epoch_diagnostics"]) == 2
    assert history["pcgrad_trigger"].startswith(
        "three_consecutive_validation"
    )
    assert history["epoch_diagnostics"][0][
        "validation_encoder_gradients"
    ]["encoder_gradient_cosine"] is not None
    assert len(evaluated) == 2
    assert all(row["survival_nll"] >= 0.0 for row in evaluated)

    gat = build_branch_survival_model(
        "gat1x32x1",
        node_input_dim=7,
        edge_input_dim=3,
    )
    gat_history = module._train(
        gat,
        rows,
        normalization,
        validation_rows=rows,
        epochs=1,
        learning_rate=1.0e-3,
    )
    assert len(gat_history["total_loss_history"]) == 1
    assert gat_history["epoch_diagnostics"][0][
        "train_encoder_gradients"
    ]["shared_gradient_coordinate_count"] > 0


def test_pcgrad_projects_conflicting_encoder_gradients() -> None:
    torch = pytest.importorskip("torch")
    module = _trainer_module()
    first = [torch.tensor([1.0, 0.0])]
    second = [torch.tensor([-1.0, 1.0])]

    projected_first, projected_second = module._pcgrad_project(
        first,
        second,
    )

    assert torch.dot(
        projected_first[0],
        second[0],
    ).item() == pytest.approx(0.0)
    assert torch.dot(
        projected_second[0],
        first[0],
    ).item() == pytest.approx(0.0)


def _materializer_module():
    script = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "materialize_p0v3_branch_survival_rows.py"
    )
    spec = importlib.util.spec_from_file_location(
        "branch_survival_materializer",
        script,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _trainer_module():
    script = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "train_p0v3_branch_survival_ladder.py"
    )
    spec = importlib.util.spec_from_file_location(
        "branch_survival_trainer_metrics",
        script,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _readiness_module():
    script = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "audit_p0v3_branch_training_readiness.py"
    )
    spec = importlib.util.spec_from_file_location(
        "branch_survival_readiness",
        script,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _cross_domain_pilot_module():
    script = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "audit_p0v3_branch_cross_domain_pilot.py"
    )
    spec = importlib.util.spec_from_file_location(
        "branch_cross_domain_pilot",
        script,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _linear_pilot_module():
    script = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "train_p0v3_branch_cross_domain_linear_pilot.py"
    )
    spec = importlib.util.spec_from_file_location(
        "branch_cross_domain_linear",
        script,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _target_headroom_module():
    script = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "audit_p0v3_branch_target_headroom.py"
    )
    spec = importlib.util.spec_from_file_location(
        "branch_target_headroom",
        script,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _external_gold_report() -> dict:
    top3 = ["pair-0", "pair-1", "pair-2"]
    base = {
        "exact_safe": True,
        "counterfactual_universe_matches_control": True,
        "matched_end_to_end_wall_sec": 9.0,
    }
    return {
        "schema_version": (
            "lunar_ice_bpc.no_task_wait_v3_branch_state_oracle.v2"
        ),
        "instance_content_hash": "instance",
        "root_source_sha256": "parent",
        "control_exact_safe": True,
        "control_universe_safe": True,
        "control": {
            "matched_end_to_end_wall_sec": 10.0,
        },
        "state_reports": [
            {
                "path_hash": "path",
                "complete_matched_e2e_gold": True,
                "top3_candidate_ids": top3,
                "eligible_alternative_count": 2,
                "oracle_selected_rank_index": 1,
                "oracle_net_gain_sec": 1.0,
                "oracle_net_gain_ratio": 0.1,
                "arms": [
                    {**base, "requested_rank_index": 1},
                    {
                        **base,
                        "requested_rank_index": 2,
                        "matched_end_to_end_wall_sec": 11.0,
                    },
                ],
            }
        ],
    }


def test_external_e2e_gold_requires_same_parent_snapshot() -> None:
    module = _materializer_module()
    label = module._external_e2e_gold_label(
        oracle=_external_gold_report(),
        state={"path_hash": "path"},
        candidate_ids=["pair-0", "pair-1", "pair-2"],
        parent_source_sha256="parent",
    )
    assert label["oracle_selected_rank_index"] == 1
    assert label["same_parent_snapshot_bound"] is True
    assert label["matched_end_to_end_wall_sec_by_rank"] == {
        "0": 10.02,
        "1": 9.02,
        "2": 11.02,
    }
    assert label["p0_control_wall_sec"] == pytest.approx(10.0)
    assert label["oracle_net_gain_sec"] == pytest.approx(0.98)
    assert label["guidance_lifecycle_overhead_sec"] == pytest.approx(0.02)

    with pytest.raises(ValueError, match="binding/exactness"):
        module._external_e2e_gold_label(
            oracle=_external_gold_report(),
            state={"path_hash": "path"},
            candidate_ids=["pair-0", "pair-1", "pair-2"],
            parent_source_sha256="different-parent",
        )


def test_canonical_guided_cost_charges_rank0_and_does_not_double_charge() -> None:
    from lunar_ice_bpc.guidance.branch_e2e_costs import (
        canonical_guided_e2e_costs,
        canonical_selective_guidance_costs,
    )

    costs = canonical_guided_e2e_costs(
        arm_by_rank={
            0: {"matched_end_to_end_wall_sec": 10.0},
            1: {
                "matched_end_to_end_wall_sec": 9.02,
                "guidance_lifecycle_overhead_sec": 0.02,
            },
            2: {
                "matched_end_to_end_wall_sec": 11.02,
                "guidance_lifecycle_overhead_sec": 0.02,
            },
        },
        guidance_lifecycle_overhead_sec=0.02,
    )
    assert costs["p0_control_wall_sec"] == pytest.approx(10.0)
    assert costs["guided_action_wall_sec_by_rank"] == {
        "0": pytest.approx(10.02),
        "1": pytest.approx(9.02),
        "2": pytest.approx(11.02),
    }
    assert costs["oracle_selected_rank_index"] == 1
    assert costs["oracle_net_gain_sec"] == pytest.approx(0.98)
    selective = canonical_selective_guidance_costs(costs)
    assert selective["selective_oracle_action"] == "1"
    assert selective["selective_oracle_net_gain_sec"] == pytest.approx(
        0.98
    )

    no_improvement = canonical_guided_e2e_costs(
        arm_by_rank={
            rank: {"matched_end_to_end_wall_sec": 10.0 + rank}
            for rank in range(3)
        },
        guidance_lifecycle_overhead_sec=0.02,
    )
    selective = canonical_selective_guidance_costs(no_improvement)
    assert selective["selective_oracle_action"] == "ABSTAIN_TO_P0"
    assert selective["selective_oracle_net_gain_sec"] == pytest.approx(
        -0.02
    )


def test_partial_e2e_report_yields_only_trusted_observed_pair() -> None:
    module = _materializer_module()
    report = _external_gold_report()
    state = report["state_reports"][0]
    report["control_exact_safe"] = False
    report["control"]["exact_safe"] = False
    state["arms"][1]["matched_end_to_end_wall_sec"] = 8.0
    state["complete_matched_e2e_gold"] = False
    state["observed_rank_indices"] = [0, 2]
    state["missing_rank_indices"] = [1]
    state["trusted_censored_pairwise_preferences"] = [
        {
            "winner_rank_index": 2,
            "loser_rank_index": 0,
            "evidence": "EXACT_BEFORE_OTHER_CENSOR_HORIZON",
            "same_parent_snapshot": True,
            "unexplored_arm_used_as_negative": False,
        }
    ]

    assert (
        module._external_e2e_gold_label(
            oracle=report,
            state={"path_hash": "path"},
            candidate_ids=["pair-0", "pair-1", "pair-2"],
            parent_source_sha256="parent",
        )
        is None
    )
    assert module._external_e2e_pairwise_preferences(
        oracle=report,
        state={"path_hash": "path"},
        candidate_ids=["pair-0", "pair-1", "pair-2"],
        parent_source_sha256="parent",
    ) == [[2, 0]]


def test_e2e_gold_map_allows_grouped_deep_states_per_instance(
    tmp_path: Path,
) -> None:
    module = _materializer_module()
    first = _external_gold_report()
    second = _external_gold_report()
    second["state_reports"][0]["path_hash"] = "deep-path"
    first_path = tmp_path / "first.json"
    second_path = tmp_path / "second.json"
    first_path.write_text(json.dumps(first), encoding="utf-8")
    second_path.write_text(json.dumps(second), encoding="utf-8")
    mapped = module._e2e_gold_report_map(
        [first_path, second_path]
    )
    assert set(mapped["instance"]) == {"path", "deep-path"}


def test_model_selection_groups_deep_states_by_instance_and_holm() -> None:
    module = _trainer_module()
    previous = []
    current = []
    for scale in (20, 30):
        for instance in range(5):
            state_count = 4 if instance == 0 else 1
            for state in range(state_count):
                common = {
                    "instance_content_hash": (
                        f"s{scale}-i{instance}"
                    ),
                    "path_hash": f"path-{state}",
                    "scale": scale,
                    "instance_generator_domain": (
                        "real_lunar_south_pole_sp50_benchmark_v1"
                    ),
                    "survival_nll": 1.0,
                    "gold_top1_match": True,
                    "model_to_p0_wall_ratio": 1.0,
                }
                previous.append(
                    {
                        **common,
                        "model_normalized_e2e_regret": 0.04,
                    }
                )
                current.append(
                    {
                        **common,
                        "model_normalized_e2e_regret": 0.02,
                    }
                )
    summary = module._summary(previous)
    assert summary["weighting"] == (
        "generator_domain_equal_scale_equal_instance_equal_state_equal"
    )
    paired = module._paired_clustered_regret_improvement(
        previous,
        current,
    )
    assert paired["instance_cluster_count"] == 10
    assert paired["balanced_mean_improvement"] == pytest.approx(
        0.02
    )
    assert all(
        payload["bootstrap_95ci"][0] == pytest.approx(0.02)
        for payload in paired[
            "by_scale_instance_cluster_bootstrap"
        ].values()
    )
    decisions = module._holm_rejections(
        {
            ("linear", "mlp"): paired[
                "one_sided_sign_flip_p_value"
            ],
            ("mlp", "gat"): 0.5,
        }
    )
    assert decisions[("linear", "mlp")] is True
    assert decisions[("mlp", "gat")] is False


def test_complexity_ladder_cannot_skip_linear_authorization() -> None:
    module = _trainer_module()
    with pytest.raises(
        SystemExit,
        match="first run is linear-only",
    ):
        module._complexity_expansion_authorization(
            model_kinds=["linear", "mlp2x32"],
            previous_report_path=None,
            records_sha256="records",
            split_manifest_hash="split",
            readiness_report_sha256="readiness",
            training_regime="REAL_ONLY",
        )


def test_linear_gate_requires_real_map_wall_gain() -> None:
    module = _trainer_module()
    results = []
    for scale in (20, 30):
        for instance in range(3):
            results.append(
                {
                    "instance_content_hash": (
                        f"real-{scale}-{instance}"
                    ),
                    "instance_generator_domain": (
                        "real_lunar_south_pole_sp50_benchmark_v1"
                    ),
                    "path_hash": "root",
                    "scale": scale,
                    "survival_nll": 1.0,
                    "predicted_rank_index": 1,
                    "gold_rank_index": 1,
                    "gold_top1_match": True,
                    "trusted_censored_pairwise_accuracy": None,
                    "model_e2e_wall_sec": 90.0,
                    "p0_e2e_wall_sec": 100.0,
                    "oracle_e2e_wall_sec": 90.0,
                    "model_normalized_e2e_regret": 0.0,
                    "model_to_p0_wall_ratio": 0.9,
                }
            )
    gate = module._linear_vs_p0_gate(
        results,
        {"forward_p50_sec": 0.001},
    )
    assert gate["passed"] is True
    assert gate[
        "real_map_worst_scale_bootstrap_lower95"
    ] == pytest.approx(0.1)

    regressed = [
        {
            **row,
            "model_e2e_wall_sec": 110.0,
            "model_normalized_e2e_regret": 0.2,
            "model_to_p0_wall_ratio": 1.1,
        }
        for row in results
    ]
    assert module._linear_vs_p0_gate(
        regressed,
        {"forward_p50_sec": 0.001},
    )["passed"] is False


def test_model_comparison_equalizes_generator_domains() -> None:
    module = _trainer_module()
    previous = []
    current = []
    domains = [
        (
            "real_lunar_south_pole_sp50_benchmark_v1",
            1,
            -0.1,
        ),
        ("synthetic_polar_resource_grid_v1", 20, 0.01),
    ]
    for domain, instance_count, improvement in domains:
        for instance in range(instance_count):
            common = {
                "instance_content_hash": f"{domain}-{instance}",
                "instance_generator_domain": domain,
                "path_hash": "root",
                "scale": 20,
                "model_normalized_e2e_regret": 0.2,
            }
            previous.append(common)
            current.append(
                {
                    **common,
                    "model_normalized_e2e_regret": (
                        0.2 - improvement
                    ),
                }
            )
    comparison = module._paired_clustered_regret_improvement(
        previous,
        current,
    )
    assert comparison["weighting"].startswith(
        "generator_domain_equal"
    )
    assert comparison["balanced_mean_improvement"] == pytest.approx(
        -0.045
    )


def test_oracle_headroom_bootstrap_groups_deep_states_by_instance() -> None:
    module = _readiness_module()
    values = {
        20: {
            "many-deep-states": [100.0] * 20,
            "one-root-state": [0.0],
        },
        30: {
            "scale30-a": [10.0],
            "scale30-b": [10.0],
        },
    }

    balanced, clusters = module._balanced_instance_values(values)
    lower, upper, cluster_count = (
        module._bootstrap_balanced_instance_interval(
            values,
            samples=2000,
            seed=7,
        )
    )

    assert balanced == pytest.approx(30.0)
    assert len(clusters[20]) == 2
    assert cluster_count == 4
    assert lower <= balanced <= upper


def _pilot_gold_row(
    *,
    scale: int,
    instance: int,
    gold: bool,
) -> dict:
    row = {
        **_formal_row(),
        "branch_node_feature_schema": (
            "static17.cover_dual.log_scale_memory_horizon.pricing_mode2."
            "cut_dual_signed_abs.parent_same_diff_degree.log_depth."
            "normalized_incumbent_gap.incumbent_available."
            "log_processed_open_global_columns.v2"
        ),
        "instance_generator_domain": (
            "real_lunar_south_pole_sp50_benchmark_v1"
        ),
        "scale": scale,
        "instance_content_hash": f"real-{scale}-{instance}",
        "path_hash": "root",
        "calibration_used": False,
        "protected_final_test_used": False,
    }
    if gold:
        row.update(
            {
                "branch_e2e_gold_rank_index": 1,
                "branch_e2e_gold_net_gain_sec": 0.98,
                "branch_e2e_p0_control_wall_sec": 10.0,
                "branch_guidance_lifecycle_overhead_sec": 0.02,
                "branch_e2e_cost_semantics": (
                    "p0_control_raw_wall_vs_all_guided_actions_"
                    "uniform_lifecycle_overhead.v1"
                ),
                "branch_e2e_wall_sec_by_rank": {
                    "0": 10.02,
                    "1": 9.02,
                    "2": 11.02,
                },
            }
        )
    return row


def test_real_map_headroom_can_authorize_real_only_linear_without_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _cross_domain_pilot_module()
    rows = [
        _pilot_gold_row(
            scale=scale,
            instance=instance,
            gold=instance < 2,
        )
        for scale in (20, 30)
        for instance in range(3)
    ]
    records = tmp_path / "records.jsonl"
    records.write_text(
        "".join(
            json.dumps(row, sort_keys=True) + "\n" for row in rows
        ),
        encoding="utf-8",
    )
    split = tmp_path / "split.json"
    split.write_text(
        json.dumps(
            {
                "schema_version": (
                    "lunar_ice_bpc.branch_grouped_split_manifest.v2"
                ),
                "manifest_hash": "split-hash",
                "audit": {"passed": True},
                "calibration_read_authorized": False,
                "development": [
                    {
                        "instance_content_hash": row[
                            "instance_content_hash"
                        ],
                        "instance_generator_domain": row[
                            "instance_generator_domain"
                        ],
                        "scale": row["scale"],
                        "fold": index % 5,
                    }
                    for index, row in enumerate(rows)
                ],
                "calibration": [],
                "protected_final_test": [],
            }
        ),
        encoding="utf-8",
    )
    census_paths = []
    for scale in (20, 30):
        census = tmp_path / f"census-{scale}.json"
        census.write_text(
            json.dumps(
                {
                    "schema_version": (
                        "lunar_ice_bpc.no_task_wait_v3_branch_"
                        "opportunity_census.v1"
                    ),
                    "split_manifest_hash": "split-hash",
                    "instance_generator_domain": (
                        "real_lunar_south_pole_sp50_benchmark_v1"
                    ),
                    "scale": scale,
                    "development_only": True,
                    "training_authorized": False,
                    "rows": [
                        {
                            "instance_content_hash": (
                                f"real-{scale}-{instance}"
                            ),
                            "status": (
                                "EXACT_ACTIONABLE"
                                if instance < 2
                                else "EXACT_NONACTIONABLE"
                            ),
                            "driver_wall_sec": 1.0,
                        }
                        for instance in range(3)
                    ],
                }
            ),
            encoding="utf-8",
        )
        census_paths.append(census)
    target_headroom = tmp_path / "target-headroom.json"
    target_headroom.write_text(
        json.dumps(
            {
                "schema_version": (
                    "lunar_ice_bpc.branch_target_headroom_gate.v1"
                ),
                "split_manifest_hash": "split-hash",
                "target_domain": (
                    "real_lunar_south_pole_sp50_benchmark_v1"
                ),
                "calibration_used": False,
                "protected_final_test_used": False,
                "target_headroom_passed": True,
                "terminate_target_direction": False,
                "formal_feature_aux_collection_authorized": True,
                "gold_label_bindings": [
                    {
                        "instance_content_hash": row[
                            "instance_content_hash"
                        ],
                        "path_hash": row["path_hash"],
                        "label_sha256": module._e2e_label_hash(row),
                    }
                    for row in rows
                    if row.get("branch_e2e_gold_rank_index")
                    is not None
                ],
            }
        ),
        encoding="utf-8",
    )
    report = tmp_path / "pilot.json"
    census_arguments = [
        value
        for path in census_paths
        for value in ("--target-census-report", str(path))
    ]
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(module.__file__),
            "--records-jsonl",
            str(records),
            "--split-manifest",
            str(split),
            "--target-headroom-report",
            str(target_headroom),
            *census_arguments,
            "--output-report",
            str(report),
            "--bootstrap-samples",
            "200",
        ],
    )

    assert module.main() == 2
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["target_headroom_pilot_passed"] is True
    assert payload["linear_real_map_pilot_authorized"] is True
    assert payload["synthetic_transfer_pilot_authorized"] is False
    assert payload["full_collection_authorized"] is False
    assert len(payload["pilot_row_bindings"]) == len(rows)
    target = payload["domain_metrics"][
        "real_lunar_south_pole_sp50_benchmark_v1"
    ]
    assert target["instance_cluster_count"] == 6
    assert target["actionable_count_by_scale"] == {
        "20": 2,
        "30": 2,
    }
    assert target[
        "perfect_policy_net_gain_sec_mean_after_overhead"
    ] == pytest.approx((0.98 + 0.98 + 0.0) / 3.0)
    assert payload["matched_e2e_collection_authorized"] is False
    assert payload["bounded_target_expansion_authorized"] is False


def test_transfer_report_must_bind_exact_pilot_records(
    tmp_path: Path,
) -> None:
    module = _cross_domain_pilot_module()
    transfer = tmp_path / "transfer.json"
    transfer.write_text(
        json.dumps(
            {
                "schema_version": (
                    "lunar_ice_bpc."
                    "branch_cross_domain_transfer_evaluation.v1"
                ),
                "records_sha256": "different",
                "calibration_used": False,
                "protected_final_test_used": False,
                "model_kind": "linear",
                "target_domain": (
                    "real_lunar_south_pole_sp50_benchmark_v1"
                ),
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(SystemExit, match="binding mismatch"):
        module._transfer_decision(
            transfer,
            records_sha256="expected",
        )


def test_target_stop_loss_terminates_zero_signal_and_caps_expansion() -> None:
    module = _cross_domain_pilot_module()
    zero = module._target_stop_loss_decision(
        target_sample_ready=False,
        target_screen_exact_complete=True,
        target_actionable_gold_complete=True,
        target_cap_reached=False,
        target_upper=0.0,
        positive_gold_count=0,
        minimum_positive_gold_count=1,
    )
    assert zero["terminate_target_direction"] is True
    assert zero["bounded_target_expansion_authorized"] is False

    sparse_positive = module._target_stop_loss_decision(
        target_sample_ready=False,
        target_screen_exact_complete=True,
        target_actionable_gold_complete=True,
        target_cap_reached=False,
        target_upper=1.0,
        positive_gold_count=1,
        minimum_positive_gold_count=1,
    )
    assert sparse_positive["terminate_target_direction"] is False
    assert sparse_positive[
        "bounded_target_expansion_authorized"
    ] is True

    capped = module._target_stop_loss_decision(
        target_sample_ready=False,
        target_screen_exact_complete=True,
        target_actionable_gold_complete=True,
        target_cap_reached=True,
        target_upper=1.0,
        positive_gold_count=1,
        minimum_positive_gold_count=1,
    )
    assert capped["terminate_target_direction"] is True
    assert capped["bounded_target_expansion_authorized"] is False

    capped_with_censored_denominator = (
        module._target_stop_loss_decision(
            target_sample_ready=False,
            target_screen_exact_complete=False,
            target_actionable_gold_complete=True,
            target_cap_reached=True,
            target_upper=1.0,
            positive_gold_count=1,
            minimum_positive_gold_count=1,
        )
    )
    assert (
        capped_with_censored_denominator[
            "terminate_target_direction"
        ]
        is True
    )
    assert (
        capped_with_censored_denominator[
            "matched_e2e_collection_authorized"
        ]
        is False
    )
    assert capped_with_censored_denominator[
        "decision_reason_code"
    ] == "TARGET_CAP_REACHED_WITH_INSUFFICIENT_EVALUABLE_GOLD"


def test_target_headroom_reads_e2e_gold_without_child_trajectory() -> None:
    module = _target_headroom_module()
    report_path = (
        Path(__file__).resolve().parents[1]
        / "runs/p0_no_task_wait_v3_branch_parent_snapshot_e2e_20260726"
        / "scale20_instance_024/state_oracle_report.json"
    )
    report = json.loads(report_path.read_text(encoding="utf-8"))
    content_hash = report["instance_content_hash"]
    split = {
        "manifest_hash": report["split_manifest_hash"],
        "development": [
            {
                "instance_content_hash": content_hash,
                "instance_generator_domain": (
                    "real_lunar_south_pole_sp50_benchmark_v1"
                ),
                "scale": 20,
            }
        ],
    }
    binding = module._gold_binding(
        path=report_path,
        split_manifest=split,
        census_actionable_hashes={content_hash},
    )
    assert binding["branch_e2e_gold_rank_index"] == 0
    assert binding["branch_e2e_gold_net_gain_sec"] == pytest.approx(
        -0.02
    )
    assert binding["branch_e2e_wall_sec_by_rank"]["0"] == pytest.approx(
        30.978656
    )


def test_linear_pilot_compares_only_complete_gold_states() -> None:
    module = _linear_pilot_module()
    rows = [
        {"model_normalized_e2e_regret": None},
        {"model_normalized_e2e_regret": 0.1},
    ]
    assert module._gold_results(rows) == [rows[1]]


def test_readiness_rejects_changed_pilot_rows(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _readiness_module()
    row = _pilot_gold_row(scale=20, instance=0, gold=True)
    records = tmp_path / "records.jsonl"
    records.write_text(
        json.dumps(row, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    stale_row = {**row, "branch_e2e_gold_net_gain_sec": 2.0}
    stale_hash = hashlib.sha256(
        json.dumps(
            stale_row,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    pilot = tmp_path / "pilot.json"
    pilot.write_text(
        json.dumps(
            {
                "schema_version": (
                    "lunar_ice_bpc.branch_cross_domain_pilot.v1"
                ),
                "calibration_used": False,
                "protected_final_test_used": False,
                "target_domain": (
                    "real_lunar_south_pole_sp50_benchmark_v1"
                ),
                "pilot_row_bindings": [
                    {
                        "instance_content_hash": row[
                            "instance_content_hash"
                        ],
                        "path_hash": row["path_hash"],
                        "row_sha256": stale_hash,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(module.__file__),
            "--records-jsonl",
            str(records),
            "--output-report",
            str(tmp_path / "readiness.json"),
            "--cross-domain-pilot-report",
            str(pilot),
        ],
    )
    with pytest.raises(SystemExit, match="missing or changed"):
        module.main()
