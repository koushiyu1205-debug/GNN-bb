from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

try:
    import torch

    from BPC_future.scripts.build_gat_branch_action_sanity_dataset import build_dataset
    from BPC_future.scripts.train_gat_branch_action_sanity import (
        TrainBranchActionSanityArgs,
        _split_items,
        train_branch_action_sanity,
    )
    from BPC_future.scripts.export_gat_branch_action_score_map import (
        _branch_score_from_output,
        _branch_state_key_from_event,
        _state_score_key,
    )
    from BPC_future.tests.test_gat_branch_action_sanity_dataset import (
        _delta_row,
        _write_jsonl,
    )
    from BPC_future.tests.test_learning_components import _toy_payload

    HAS_LEARNING_STACK = True
except Exception:
    HAS_LEARNING_STACK = False


@unittest.skipUnless(HAS_LEARNING_STACK, "learning stack is not installed")
class GATBranchActionSanityTrainingTests(unittest.TestCase):
    def test_zero_validation_fraction_uses_all_samples_for_training(self) -> None:
        manifest = {
            "samples": [
                {"instance": "a", "path": "a0.pt"},
                {"instance": "a", "path": "a1.pt"},
                {"instance": "b", "path": "b0.pt"},
            ]
        }

        train, validation = _split_items(manifest, validation_fraction=0.0, seed=7)

        self.assertEqual(len(train), 3)
        self.assertEqual(validation, [])

    def test_tree_policy_score_mode_uses_tree_policy_probability(self) -> None:
        score = _branch_score_from_output(
            probability=0.2,
            predicted_walltime_gain=500.0,
            tree_policy_probability=0.8,
            score_mode="tree_policy",
        )
        self.assertAlmostEqual(score, 0.8)

    def test_export_score_map_state_key_boundaries(self) -> None:
        self.assertEqual(
            _branch_state_key_from_event(
                {
                    "depth": 1,
                    "branch_constraints": ["RF(5,19)=same_vehicle"],
                }
            ),
            "RF(5,19)=same_vehicle",
        )
        self.assertEqual(_branch_state_key_from_event({"depth": 0}), "root")
        self.assertIsNone(_branch_state_key_from_event({"depth": 1}))
        self.assertEqual(
            _state_score_key("RF(5,19)=same_vehicle", "node:1:depth:1:8,12"),
            "state:RF(5,19)=same_vehicle::node:1:depth:1:8,12",
        )

    def test_sanity_training_writes_offline_checkpoint_without_solver_effect(self) -> None:
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
            ]
            _write_jsonl(delta_dir / "branch_counterfactual_delta_rows.jsonl", rows)
            dataset_dir = tmp_path / "dataset"
            build_dataset([delta_dir], dataset_dir, tmp_path / "dataset_report.md")

            checkpoint = tmp_path / "checkpoint.pt"
            summary = train_branch_action_sanity(
                TrainBranchActionSanityArgs(
                    dataset_dir=dataset_dir,
                    checkpoint_out=checkpoint,
                    metrics_out=tmp_path / "metrics.json",
                    report=tmp_path / "training_report.md",
                    epochs=1,
                    hidden_dim=16,
                    option_hidden_dim=16,
                    pair_edge_dim=16,
                    branch_hidden_dim=16,
                    context_hidden_dim=8,
                    impact_hidden_dim=16,
                    min_samples=3,
                    min_target_positive=1,
                    min_hard_negative=1,
                    validation_fraction=0.34,
                    seed=7,
                )
            )

            self.assertTrue(summary["sanity_training_completed"])
            self.assertFalse(summary["production_ready"])
            self.assertFalse(summary["solver_default_effect"])
            self.assertFalse(summary["score_map_exported"])
            self.assertEqual(summary["sample_count"], 3)
            self.assertTrue(checkpoint.exists())
            saved = torch.load(checkpoint, map_location="cpu", weights_only=False)
            self.assertEqual(saved["version"], "gat_branch_action_sanity_v3_structural_aux")
            self.assertTrue(saved["training_boundary"]["sanity_only"])
            self.assertFalse(saved["training_boundary"]["score_map_exported"])
            self.assertTrue(saved["training_boundary"]["has_walltime_gain_regression_head"])
            self.assertTrue(saved["training_boundary"]["has_child_proof_cpu_regression_head"])
            self.assertTrue(saved["training_boundary"]["has_time_to_certificate_regression_head"])
            self.assertTrue(saved["training_boundary"]["has_gap_improvement_regression_head"])
            self.assertTrue(saved["training_boundary"]["has_primal_improvement_regression_head"])
            self.assertTrue(saved["training_boundary"]["has_dual_bound_gain_regression_head"])
            self.assertTrue(saved["training_boundary"]["has_fathom_gain_regression_head"])
            self.assertTrue(saved["training_boundary"]["has_branch_count_delta_regression_head"])
            self.assertTrue(saved["training_boundary"]["has_completion_bound_retry_gain_regression_head"])
            self.assertTrue(saved["training_boundary"]["has_tree_policy_head"])
            self.assertFalse(saved["exactness_contract"]["certificate_source"])
            self.assertIn("gap_improvement", summary["loss_multipliers"])
            self.assertIn("fathom_gain", summary["loss_multipliers"])
            self.assertIn("completion_bound_retry_gain", summary["loss_multipliers"])
            self.assertIn("tree_policy", summary["loss_multipliers"])
            self.assertIn("tree_policy_pairwise", summary["loss_multipliers"])
            self.assertEqual(summary["checkpoint_selection"], "validation_total")
            report = (tmp_path / "training_report.md").read_text(encoding="utf-8")
            self.assertIn("sanity_training_completed = true", report)
            self.assertIn("solver_default_effect = false", report)


if __name__ == "__main__":
    unittest.main()
