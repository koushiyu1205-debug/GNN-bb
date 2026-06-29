from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

try:
    import torch

    from BPC_future.scripts.audit_journey_branch_impact import BRANCH_IMPACT_FEATURE_SCHEMA
    from BPC_future.scripts.build_gat_branch_action_sanity_dataset import build_dataset
    from BPC_future.tests.test_learning_components import _toy_payload

    HAS_LEARNING_STACK = True
except Exception:
    HAS_LEARNING_STACK = False


@unittest.skipUnless(HAS_LEARNING_STACK, "learning stack is not installed")
class GATBranchActionSanityDatasetTests(unittest.TestCase):
    def test_builds_graph_samples_with_walltime_gain_as_main_label(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            instance = tmp_path / "toy.json"
            instance.write_text(json.dumps(_toy_payload(), sort_keys=True), encoding="utf-8")
            delta_dir = tmp_path / "delta"
            delta_dir.mkdir()
            rows = [
                _delta_row(
                    "target",
                    instance=instance,
                    label_type="strong_positive",
                    baseline_status="OPTIMAL",
                    alternative_status="OPTIMAL",
                    baseline_wall=260.0,
                    alternative_wall=150.0,
                    pair=[1, 2],
                    wall_improved=True,
                ),
                _delta_row(
                    "weak",
                    instance=instance,
                    label_type="strong_positive",
                    baseline_status="OPTIMAL",
                    alternative_status="OPTIMAL",
                    baseline_wall=260.0,
                    alternative_wall=230.0,
                    pair=[1, 3],
                    wall_improved=True,
                ),
                _delta_row(
                    "regression",
                    instance=instance,
                    label_type="regression",
                    baseline_status="OPTIMAL",
                    alternative_status="EXTERNAL_TIME_LIMIT",
                    baseline_wall=260.0,
                    alternative_wall=320.0,
                    pair=[2, 3],
                    regression=True,
                ),
                _delta_row(
                    "nonoptimal_gain",
                    instance=instance,
                    label_type="observed_walltime_gain",
                    baseline_status="TIME_LIMIT",
                    alternative_status="TIME_LIMIT",
                    baseline_wall=556.0,
                    alternative_wall=427.0,
                    pair=[2, 3],
                ),
                _delta_row(
                    "local_only",
                    instance=instance,
                    label_type="local_only_hard_negative",
                    baseline_status="EXTERNAL_TIME_LIMIT",
                    alternative_status="EXTERNAL_TIME_LIMIT",
                    baseline_wall=220.0,
                    alternative_wall=220.0,
                    pair=[1, 2],
                    right_censored=True,
                ),
                _delta_row(
                    "changed_timeout_no_effect",
                    instance=instance,
                    label_type="changed_timeout_no_effect_hard_negative",
                    baseline_status="EXTERNAL_TIME_LIMIT",
                    alternative_status="EXTERNAL_TIME_LIMIT",
                    baseline_wall=600.0,
                    alternative_wall=600.0,
                    pair=[1, 3],
                    no_effect_hard_negative=True,
                ),
                _delta_row(
                    "paired_probe_hard_negative",
                    instance=instance,
                    label_type="paired_probe_hard_negative_proxy",
                    baseline_status="BASELINE_CHILD_PROBE",
                    alternative_status="TIME_LIMIT",
                    baseline_wall=95.0,
                    alternative_wall=105.0,
                    pair=[2, 3],
                    no_effect_hard_negative=True,
                    right_censored=True,
                ),
                _delta_row(
                    "paired_probe_positive",
                    instance=instance,
                    label_type="paired_probe_positive_proxy",
                    baseline_status="BASELINE_CHILD_PROBE",
                    alternative_status="OPTIMAL",
                    baseline_wall=105.0,
                    alternative_wall=104.0,
                    pair=[1, 3],
                    wall_improved=True,
                    right_censored=True,
                ),
                _delta_row(
                    "gap_aux",
                    instance=instance,
                    label_type="weak_gap_fathom_positive",
                    baseline_status="EXTERNAL_TIME_LIMIT",
                    alternative_status="EXTERNAL_TIME_LIMIT",
                    baseline_wall=600.0,
                    alternative_wall=600.0,
                    pair=[1, 2],
                    right_censored=True,
                    usable_for_gap_aux_training=True,
                ),
            ]
            _write_jsonl(delta_dir / "branch_counterfactual_delta_rows.jsonl", rows)

            summary = build_dataset(
                [delta_dir],
                tmp_path / "dataset",
                tmp_path / "report.md",
                target_wall=200.0,
            )

            self.assertTrue(summary["diagnostic_only"])
            self.assertFalse(summary["runs_bpc_or_pricing"])
            self.assertEqual(summary["sample_count"], 8)
            self.assertEqual(
                summary["branch_priority_label_counts"],
                {
                    "aux_only_weak_positive": 2,
                    "not_walltime_gain": 3,
                    "walltime_gain_positive": 3,
                },
            )
            self.assertEqual(
                summary["target_wall_crossing_label_counts"],
                {
                    "not_target_wall_crossing": 7,
                    "target_wall_crossing_positive": 1,
                },
            )
            self.assertEqual(summary["row_kind_counts"]["walltime_gain_positive"], 2)
            self.assertEqual(summary["row_kind_counts"]["local_only_hard_negative"], 1)
            self.assertEqual(summary["row_kind_counts"]["paired_probe_hard_negative_proxy"], 1)
            self.assertEqual(summary["row_kind_counts"]["paired_probe_positive_proxy"], 1)
            self.assertEqual(summary["row_kind_counts"]["weak_gap_fathom_positive"], 1)
            self.assertIn(
                "not_training_sample:local_only_hard_negative",
                summary["skipped_counts"],
            )
            self.assertTrue(summary["sanity_training_dataset_ready"])
            manifest = json.loads((tmp_path / "dataset" / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["sample_count"], 8)
            self.assertEqual(manifest["branch_feature_schema"], list(BRANCH_IMPACT_FEATURE_SCHEMA))
            self.assertIn("phase1_min_child_lp_gain", manifest["context_feature_schema"])
            self.assertIn("phase1_child_lp_gain_product", manifest["context_feature_schema"])
            self.assertIn("phase1_child_lp_gain_gap", manifest["context_feature_schema"])
            self.assertIn("phase1_child_lp_gain_balance_ratio", manifest["context_feature_schema"])
            self.assertIn("phase1_cut_snapshot_min_child_lp_gain", manifest["context_feature_schema"])
            self.assertIn("phase1_cut_snapshot_child_lp_gain_product", manifest["context_feature_schema"])
            self.assertIn("phase1_cut_snapshot_child_lp_gain_gap", manifest["context_feature_schema"])
            self.assertIn(
                "phase1_cut_snapshot_child_lp_gain_balance_ratio",
                manifest["context_feature_schema"],
            )
            self.assertIn("phase1_cut_snapshot_wall_time", manifest["context_feature_schema"])
            self.assertIn("phase1_diagnostic_wall_time", manifest["context_feature_schema"])
            self.assertIn("phase2_negative_child_count", manifest["context_feature_schema"])
            self.assertIn("phase2_negative_journey_balance_gap", manifest["context_feature_schema"])
            self.assertIn("phase2_negative_severity_sum", manifest["context_feature_schema"])
            self.assertIn("phase2_negative_severity_gap", manifest["context_feature_schema"])
            self.assertIn("phase2_negative_severity_balance_ratio", manifest["context_feature_schema"])
            self.assertIn(
                "phase2_negative_child_presence_balance_gap",
                manifest["context_feature_schema"],
            )
            self.assertEqual(
                manifest["phase2_pressure_context_features"],
                [
                    "phase2_same_child_negative_severity",
                    "phase2_separate_child_negative_severity",
                    "phase2_negative_severity_sum",
                    "phase2_negative_severity_gap",
                    "phase2_negative_severity_balance_ratio",
                    "phase2_negative_child_presence_balance_gap",
                ],
            )
            self.assertEqual(
                manifest["phase2_pressure_observed_counts"],
                {
                    "phase2_same_child_negative_severity": 8,
                    "phase2_separate_child_negative_severity": 8,
                    "phase2_negative_severity_sum": 8,
                    "phase2_negative_severity_gap": 8,
                    "phase2_negative_severity_balance_ratio": 8,
                    "phase2_negative_child_presence_balance_gap": 8,
                },
            )
            self.assertEqual(
                manifest["phase2_pressure_nonzero_counts"],
                {
                    "phase2_same_child_negative_severity": 8,
                    "phase2_separate_child_negative_severity": 0,
                    "phase2_negative_severity_sum": 8,
                    "phase2_negative_severity_gap": 8,
                    "phase2_negative_severity_balance_ratio": 0,
                    "phase2_negative_child_presence_balance_gap": 8,
                },
            )
            self.assertEqual(manifest["phase2_pressure_nonzero_sample_count"], 8)
            self.assertTrue(manifest["phase2_pressure_coverage_ready"])
            self.assertIn("phase2_child_wall_time_balance_gap", manifest["context_feature_schema"])
            self.assertIn("phase2_child_status_mismatch", manifest["context_feature_schema"])
            self.assertIn("phase2_wall_time", manifest["context_feature_schema"])
            self.assertIn("phased_testing_stage_code", manifest["context_feature_schema"])
            self.assertIn("phased_testing_decision_code", manifest["context_feature_schema"])
            self.assertIn("phased_testing_elimination_reason_code", manifest["context_feature_schema"])
            self.assertIn("cut_context_dynamic_subset_row_regime_code", manifest["context_feature_schema"])
            self.assertIn("cut_context_subset_row_count", manifest["context_feature_schema"])
            self.assertIn("route_order_active_journey_count", manifest["context_feature_schema"])
            self.assertIn("route_order_active_route_signature_count", manifest["context_feature_schema"])
            self.assertIn("route_order_conflict_count", manifest["context_feature_schema"])
            self.assertIn("route_order_conflict_mass", manifest["context_feature_schema"])
            self.assertIn("route_order_top_conflict_balance_ratio", manifest["context_feature_schema"])
            self.assertIn("route_order_candidate_direction_conflict_mass", manifest["context_feature_schema"])
            self.assertIn("route_order_candidate_adjacent_conflict_mass", manifest["context_feature_schema"])
            self.assertEqual(manifest["exactness_contract"]["certificate_source"], False)
            self.assertEqual(
                manifest["exactness_contract"]["missing_phase2_pressure_is_not_low_pressure"],
                True,
            )
            summary_payload = json.loads((tmp_path / "dataset" / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary_payload["phase2_pressure_observed_counts"], manifest["phase2_pressure_observed_counts"])
            self.assertEqual(summary_payload["phase2_pressure_nonzero_counts"], manifest["phase2_pressure_nonzero_counts"])
            self.assertEqual(summary_payload["phase2_pressure_nonzero_sample_count"], 8)
            self.assertTrue(summary_payload["phase2_pressure_coverage_ready"])
            self.assertFalse(summary_payload["pressure_aware_training_dataset_ready"])
            sample = torch.load(
                tmp_path / "dataset" / manifest["samples"][0]["path"],
                map_location="cpu",
                weights_only=False,
            )
            self.assertEqual(tuple(sample.branch_pair_indices.shape), (1, 2))
            self.assertEqual(tuple(sample.branch_pair_features.shape), (1, len(BRANCH_IMPACT_FEATURE_SCHEMA)))
            self.assertEqual(tuple(sample.context_features.shape), (len(manifest["context_feature_schema"]),))
            phase1_min_index = manifest["context_feature_schema"].index("phase1_min_child_lp_gain")
            phase1_product_index = manifest["context_feature_schema"].index("phase1_child_lp_gain_product")
            phase1_gap_index = manifest["context_feature_schema"].index("phase1_child_lp_gain_gap")
            phase1_ratio_index = manifest["context_feature_schema"].index(
                "phase1_child_lp_gain_balance_ratio"
            )
            phase1_cut_min_index = manifest["context_feature_schema"].index(
                "phase1_cut_snapshot_min_child_lp_gain"
            )
            phase1_cut_product_index = manifest["context_feature_schema"].index(
                "phase1_cut_snapshot_child_lp_gain_product"
            )
            phase1_cut_gap_index = manifest["context_feature_schema"].index(
                "phase1_cut_snapshot_child_lp_gain_gap"
            )
            phase1_cut_ratio_index = manifest["context_feature_schema"].index(
                "phase1_cut_snapshot_child_lp_gain_balance_ratio"
            )
            phase1_cut_wall_index = manifest["context_feature_schema"].index("phase1_cut_snapshot_wall_time")
            phase1_diag_wall_index = manifest["context_feature_schema"].index("phase1_diagnostic_wall_time")
            phase2_gap_index = manifest["context_feature_schema"].index(
                "phase2_negative_journey_balance_gap"
            )
            phase2_severity_sum_index = manifest["context_feature_schema"].index(
                "phase2_negative_severity_sum"
            )
            phase2_severity_gap_index = manifest["context_feature_schema"].index(
                "phase2_negative_severity_gap"
            )
            phase2_severity_ratio_index = manifest["context_feature_schema"].index(
                "phase2_negative_severity_balance_ratio"
            )
            phase2_presence_gap_index = manifest["context_feature_schema"].index(
                "phase2_negative_child_presence_balance_gap"
            )
            phase2_wall_gap_index = manifest["context_feature_schema"].index(
                "phase2_child_wall_time_balance_gap"
            )
            phase2_status_mismatch_index = manifest["context_feature_schema"].index(
                "phase2_child_status_mismatch"
            )
            phased_stage_index = manifest["context_feature_schema"].index("phased_testing_stage_code")
            phased_decision_index = manifest["context_feature_schema"].index("phased_testing_decision_code")
            phased_elimination_index = manifest["context_feature_schema"].index(
                "phased_testing_elimination_reason_code"
            )
            cut_regime_index = manifest["context_feature_schema"].index(
                "cut_context_dynamic_subset_row_regime_code"
            )
            cut_subset_index = manifest["context_feature_schema"].index("cut_context_subset_row_count")
            cut_min_add_depth_index = manifest["context_feature_schema"].index(
                "cut_context_dynamic_subset_row_min_add_depth"
            )
            route_active_journey_index = manifest["context_feature_schema"].index(
                "route_order_active_journey_count"
            )
            route_signature_index = manifest["context_feature_schema"].index(
                "route_order_active_route_signature_count"
            )
            route_conflict_index = manifest["context_feature_schema"].index("route_order_conflict_count")
            route_conflict_mass_index = manifest["context_feature_schema"].index(
                "route_order_conflict_mass"
            )
            route_conflict_ratio_index = manifest["context_feature_schema"].index(
                "route_order_top_conflict_balance_ratio"
            )
            route_candidate_conflict_index = manifest["context_feature_schema"].index(
                "route_order_candidate_direction_conflict_mass"
            )
            route_candidate_adjacent_conflict_index = manifest["context_feature_schema"].index(
                "route_order_candidate_adjacent_conflict_mass"
            )
            self.assertAlmostEqual(float(sample.context_features[phase1_min_index]), 3.5)
            self.assertAlmostEqual(float(sample.context_features[phase1_product_index]), 42.0)
            self.assertAlmostEqual(float(sample.context_features[phase1_gap_index]), 1.0)
            self.assertAlmostEqual(float(sample.context_features[phase1_ratio_index]), 0.75)
            self.assertAlmostEqual(float(sample.context_features[phase1_cut_min_index]), 5.5)
            self.assertAlmostEqual(float(sample.context_features[phase1_cut_product_index]), 56.0)
            self.assertAlmostEqual(float(sample.context_features[phase1_cut_gap_index]), 2.5)
            self.assertAlmostEqual(float(sample.context_features[phase1_cut_ratio_index]), 0.6875)
            self.assertAlmostEqual(float(sample.context_features[phase1_cut_wall_index]), 0.02)
            self.assertAlmostEqual(float(sample.context_features[phase1_diag_wall_index]), 0.032)
            self.assertAlmostEqual(float(sample.context_features[phase2_gap_index]), 2.0)
            self.assertAlmostEqual(float(sample.context_features[phase2_severity_sum_index]), 0.25)
            self.assertAlmostEqual(float(sample.context_features[phase2_severity_gap_index]), 0.25)
            self.assertAlmostEqual(float(sample.context_features[phase2_severity_ratio_index]), 0.0)
            self.assertAlmostEqual(float(sample.context_features[phase2_presence_gap_index]), 1.0)
            self.assertAlmostEqual(float(sample.context_features[phase2_wall_gap_index]), 0.015)
            self.assertAlmostEqual(float(sample.context_features[phase2_status_mismatch_index]), 1.0)
            self.assertAlmostEqual(float(sample.context_features[phased_stage_index]), 4.0)
            self.assertAlmostEqual(float(sample.context_features[phased_decision_index]), 8.0)
            self.assertAlmostEqual(float(sample.context_features[phased_elimination_index]), 0.0)
            self.assertAlmostEqual(float(sample.context_features[cut_regime_index]), 4.0)
            self.assertAlmostEqual(float(sample.context_features[cut_subset_index]), 3.0)
            self.assertAlmostEqual(float(sample.context_features[cut_min_add_depth_index]), 1.0)
            self.assertAlmostEqual(float(sample.context_features[route_active_journey_index]), 19.0)
            self.assertAlmostEqual(float(sample.context_features[route_signature_index]), 18.0)
            self.assertAlmostEqual(float(sample.context_features[route_conflict_index]), 2.0)
            self.assertAlmostEqual(float(sample.context_features[route_conflict_mass_index]), 1.25)
            self.assertAlmostEqual(float(sample.context_features[route_conflict_ratio_index]), 0.5)
            self.assertAlmostEqual(float(sample.context_features[route_candidate_conflict_index]), 1.0)
            self.assertAlmostEqual(float(sample.context_features[route_candidate_adjacent_conflict_index]), 0.75)
            self.assertIn("y_gap_improvement", manifest["label_schema"])
            self.assertIn("y_fathom_gain", manifest["label_schema"])
            self.assertIn("y_branch_count_delta", manifest["label_schema"])
            self.assertIn("y_completion_bound_retry_gain", manifest["label_schema"])
            self.assertEqual(tuple(sample.branch_action_labels.shape), (1, len(manifest["label_schema"])))
            self.assertTrue(hasattr(sample, "y_walltime_gain"))
            self.assertGreater(float(sample.y_walltime_gain.view(-1)[0]), 0.0)
            self.assertTrue(hasattr(sample, "y_child_proof_cpu"))
            self.assertTrue(hasattr(sample, "y_time_to_certificate"))
            self.assertTrue(hasattr(sample, "y_gap_improvement"))
            self.assertTrue(hasattr(sample, "gap_improvement_loss_weight"))
            self.assertTrue(hasattr(sample, "y_fathom_gain"))
            self.assertTrue(hasattr(sample, "y_completion_bound_retry_gain"))
            self.assertAlmostEqual(float(sample.y_gap_improvement.view(-1)[0]), 0.25)
            self.assertAlmostEqual(float(sample.y_fathom_gain.view(-1)[0]), 2.0)
            self.assertAlmostEqual(float(sample.y_completion_bound_retry_gain.view(-1)[0]), 3.0)
            self.assertTrue((tmp_path / "dataset" / "summary.json").exists())
            report = (tmp_path / "report.md").read_text(encoding="utf-8")
            self.assertIn("sanity_training_dataset_ready = true", report)
            self.assertIn("official_bound_effect = false", report)


def _delta_row(
    experiment: str,
    *,
    instance: Path,
    label_type: str,
    baseline_status: str,
    alternative_status: str,
    baseline_wall: float,
    alternative_wall: float,
    pair: list[int],
    wall_improved: bool = False,
    regression: bool = False,
    right_censored: bool = False,
    no_effect_hard_negative: bool = False,
    usable_for_gap_aux_training: bool = False,
) -> dict[str, object]:
    labels = {
        "y_counterfactual_wall_improved": 1.0 if wall_improved else 0.0,
        "y_counterfactual_regression": 1.0 if regression else 0.0,
        "y_counterfactual_timeout_regression": 1.0 if regression else 0.0,
        "y_counterfactual_no_effect_hard_negative": 1.0 if no_effect_hard_negative else 0.0,
        "y_gap_improvement": 0.25,
        "y_primal_improvement": 1.5,
        "y_dual_bound_gain": 0.125,
        "y_fathom_gain": 2.0,
        "y_completion_bound_final_judge_retry_gain": 3.0,
    }
    branch_labels = {
        "y_tail_improved": 1.0 if wall_improved else 0.0,
        "y_completion_bound_tail": 0.0,
        "y_early_branch_continues": 0.0,
        "y_negative_chain_continues": 0.0,
        "y_active_touch": 0.0,
        "y_inactive_only": 0.0,
        "y_child_negative_pricing_events": 2.0,
        "y_child_exact_pricing_events": 3.0,
        "y_child_completion_bound_retries": 1.0,
        "y_child_early_branch_triggers": 0.0,
        "y_child_fathom_events": 1.0,
        "y_child_max_safe_bound_gain": 0.0,
        "y_child_max_corrected_bound_gain": 4.0,
    }
    return {
        "schema_version": "journey_branch_counterfactual_delta_v4",
        "experiment": experiment,
        "instance": str(instance),
        "node_id": 0,
        "depth": 0,
        "baseline_pair": [1, 2],
        "alternative_pair": pair,
        "baseline_status": baseline_status,
        "alternative_status": alternative_status,
        "baseline_wall_time": baseline_wall,
        "alternative_wall_time": alternative_wall,
        "alternative_forced_pair_matched": True,
        "right_censored_counterfactual": right_censored,
        "timeout_regression": regression,
        "counterfactual_label_type": label_type,
        "usable_for_gap_aux_training": usable_for_gap_aux_training,
        "deltas": {
            "branch_count_delta": -4.0,
        },
        "labels": labels,
        "alternative_branch_labels": branch_labels,
        "alternative_raw_row": {
            "branch_feature_vector": [float(idx) for idx in range(len(BRANCH_IMPACT_FEATURE_SCHEMA))],
            "branch_time": 12.0,
            "candidate_count": 10,
            "eligible_count": 8,
            "branch_rank_in_top": 1,
            "branch_rank_in_priority_top": 1,
            "phased_testing_stage": "phase1_lp",
            "phased_testing_decision": "probed_complete",
            "phased_testing_reason": "ok",
            "phased_testing_elimination_reason": "",
            "phased_testing_phase0_passed": True,
            "phased_testing_phase1_lp_complete": True,
            "phased_testing_phase2_heuristic_complete": False,
            "phase1_min_child_lp_gain": 3.5,
            "phase1_child_lp_gain_product": 42.0,
            "phase1_child_lp_gain_gap": 1.0,
            "phase1_child_lp_gain_balance_ratio": 0.75,
            "phase1_child_width_balance": 7,
            "phase1_wall_time": 0.012,
            "phase1_dynamic_k_probe_count": 8,
            "phase1_cut_snapshot_complete": True,
            "phase1_cut_snapshot_added_total": 3,
            "phase1_cut_snapshot_min_child_lp_gain": 5.5,
            "phase1_cut_snapshot_child_lp_gain_product": 56.0,
            "phase1_cut_snapshot_child_lp_gain_gap": 2.5,
            "phase1_cut_snapshot_child_lp_gain_balance_ratio": 0.6875,
            "phase1_cut_snapshot_wall_time": 0.02,
            "phase1_diagnostic_wall_time": 0.032,
            "phase2_negative_child_count": 1,
            "phase2_negative_journey_count": 2,
            "phase2_negative_journey_balance_gap": 2,
            "phase2_best_reduced_cost": -0.25,
            "phase2_worst_negative_severity": 0.25,
            "phase2_same_child_negative_severity": 0.25,
            "phase2_separate_child_negative_severity": 0.0,
            "phase2_negative_severity_sum": 0.25,
            "phase2_negative_severity_gap": 0.25,
            "phase2_negative_severity_balance_ratio": 0.0,
            "phase2_negative_child_presence_balance_gap": 1,
            "phase2_child_wall_time_balance_gap": 0.015,
            "phase2_child_status_mismatch": True,
            "phase2_wall_time": 0.04,
            "phase2_dynamic_k_probe_count": 8,
            "cut_context_active_count": 4,
            "cut_context_subset_row_count": 3,
            "cut_context_fleet_lb_count": 1,
            "cut_context_dynamic_subset_row_regime": "dynamic_src_child_or_deeper",
            "cut_context_dynamic_subset_row_cuts_enabled": True,
            "cut_context_dynamic_subset_row_cut_gate_enabled": True,
            "cut_context_dynamic_subset_row_min_add_depth": 1,
            "cut_context_dynamic_subset_row_max_depth": 2,
            "cut_context_dynamic_subset_row_gate_min_best_violation": 0.25,
            "route_order_active_journey_count": 19,
            "route_order_active_task_set_count": 17,
            "route_order_active_route_signature_count": 18,
            "route_order_multi_route_task_set_count": 1,
            "route_order_conflict_count": 2,
            "route_order_conflict_mass": 1.25,
            "route_order_top_conflict_balance_ratio": 0.5,
            "route_order_top_transition_count": 6,
            "route_order_top_arc_option_count": 5,
            "route_order_same_route_mass": 1.25,
            "route_order_i_before_j_mass": 0.5,
            "route_order_j_before_i_mass": 0.5,
            "route_order_direction_conflict_mass": 1.0,
            "route_order_direction_balance_ratio": 1.0,
            "route_order_adjacent_conflict_mass": 0.75,
            "route_order_adjacent_balance_ratio": 0.5,
        },
    }


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()
