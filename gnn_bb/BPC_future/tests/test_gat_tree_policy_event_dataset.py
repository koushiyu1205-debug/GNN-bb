from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

try:
    import torch

    from BPC_future.scripts.build_gat_tree_policy_event_dataset import (
        BRANCH_IMPACT_FEATURE_SCHEMA,
        build_tree_policy_event_dataset,
    )
    from BPC_future.tests.test_learning_components import _toy_payload

    HAS_LEARNING_STACK = True
except Exception:
    HAS_LEARNING_STACK = False


@unittest.skipUnless(HAS_LEARNING_STACK, "learning stack is not installed")
class GATTreePolicyEventDatasetTests(unittest.TestCase):
    def test_builds_tree_policy_only_samples(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            instance = root / "toy.json"
            instance.write_text(json.dumps(_toy_payload(), sort_keys=True), encoding="utf-8")
            rows = [
                {
                    "schema_version": "journey_tree_policy_event_row_v1",
                    "policy_run": "positive_tree",
                    "instance": str(instance),
                    "node_id": 0,
                    "depth": 0,
                    "baseline_pair": [1, 3],
                    "selected_pair": [1, 2],
                    "selected_pair_changed": True,
                    "candidate_count": 3,
                    "eligible_count": 3,
                    "selected_raw": {
                        "task_i": 1,
                        "task_j": 2,
                        "same_mass": 0.5,
                        "fractionality": 0.5,
                        "support_count": 2,
                    },
                    "priority_top": [{"task_i": 1, "task_j": 2}],
                    "tree_policy_label_type": "strong_positive",
                    "y_tree_policy_positive": 1.0,
                    "y_tree_policy_hard_negative": 0.0,
                    "event_loss_weight": 0.75,
                }
            ]
            input_path = root / "tree_policy_event_rows.jsonl"
            input_path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
            output_dir = root / "dataset"
            manifest = build_tree_policy_event_dataset(
                [input_path],
                output_dir,
                root / "report.md",
            )

            self.assertEqual(manifest["sample_count"], 1)
            self.assertEqual(manifest["tree_policy_label_counts"]["tree_policy_positive"], 1)
            sample = torch.load(output_dir / manifest["samples"][0]["path"], map_location="cpu", weights_only=False)
            self.assertEqual(float(sample.branch_priority_loss_weight.item()), 0.0)
            self.assertEqual(float(sample.walltime_gain_loss_weight.item()), 0.0)
            self.assertEqual(float(sample.y_tree_policy.item()), 1.0)
            self.assertAlmostEqual(float(sample.tree_policy_loss_weight.item()), 0.75)
            self.assertTrue(hasattr(sample, "branch_action_node_context_key"))
            self.assertIn(str(instance), sample.branch_action_node_context_key)
            self.assertNotIn("[1, 2]", sample.branch_action_node_context_key)

    def test_fills_selected_candidate_features_from_top_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            instance = root / "toy.json"
            instance.write_text(json.dumps(_toy_payload(), sort_keys=True), encoding="utf-8")
            rows = [
                {
                    "schema_version": "journey_tree_policy_event_row_v1",
                    "policy_run": "feature_fill",
                    "instance": str(instance),
                    "node_id": 0,
                    "depth": 0,
                    "baseline_pair": [1, 3],
                    "selected_pair": [1, 2],
                    "selected_pair_changed": True,
                    "candidate_count": 3,
                    "eligible_count": 3,
                    "top": [
                        {"task_i": 1, "task_j": 3, "same_mass": 0.1},
                        {
                            "task_i": 1,
                            "task_j": 2,
                            "same_mass": 0.25,
                            "fractionality": 0.75,
                            "support_count": 7,
                            "pool_total_child_width": 123,
                        },
                    ],
                    "tree_policy_label_type": "strong_positive",
                    "y_tree_policy_positive": 1.0,
                    "y_tree_policy_hard_negative": 0.0,
                    "event_loss_weight": 1.0,
                }
            ]
            input_path = root / "tree_policy_event_rows.jsonl"
            input_path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
            output_dir = root / "dataset"
            manifest = build_tree_policy_event_dataset(
                [input_path],
                output_dir,
                root / "report.md",
            )

            sample = torch.load(output_dir / manifest["samples"][0]["path"], map_location="cpu", weights_only=False)
            features = sample.branch_pair_features.view(-1).tolist()
            self.assertAlmostEqual(
                features[BRANCH_IMPACT_FEATURE_SCHEMA.index("same_mass")],
                0.25,
            )
            self.assertAlmostEqual(
                features[BRANCH_IMPACT_FEATURE_SCHEMA.index("fractionality")],
                0.75,
            )
            self.assertAlmostEqual(
                features[BRANCH_IMPACT_FEATURE_SCHEMA.index("support_count")],
                7.0,
            )
            self.assertAlmostEqual(
                features[BRANCH_IMPACT_FEATURE_SCHEMA.index("pool_total_child_width")],
                123.0,
            )

    def test_can_inject_strict_replay_walltime_labels(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            instance = root / "toy.json"
            instance.write_text(json.dumps(_toy_payload(), sort_keys=True), encoding="utf-8")
            rows = [
                {
                    "schema_version": "journey_tree_policy_event_row_v1",
                    "policy_run": "strict_path",
                    "instance": str(instance),
                    "node_id": 0,
                    "depth": 0,
                    "baseline_pair": [1, 3],
                    "selected_pair": [1, 2],
                    "selected_pair_changed": True,
                    "candidate_count": 3,
                    "eligible_count": 3,
                    "selected_raw": {"task_i": 1, "task_j": 2},
                    "tree_policy_label_type": "strong_positive",
                    "y_tree_policy_positive": 1.0,
                    "y_tree_policy_hard_negative": 0.0,
                    "event_loss_weight": 0.75,
                    "capped_wall_time_gain": 120.0,
                }
            ]
            input_path = root / "tree_policy_event_rows.jsonl"
            input_path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
            output_dir = root / "dataset"
            manifest = build_tree_policy_event_dataset(
                [input_path],
                output_dir,
                root / "report.md",
                include_walltime_labels=True,
            )

            self.assertEqual(manifest["sample_count"], 1)
            self.assertTrue(manifest["include_walltime_labels"])
            self.assertEqual(
                manifest["branch_priority_label_counts"]["walltime_gain_positive"],
                1,
            )
            sample = torch.load(output_dir / manifest["samples"][0]["path"], map_location="cpu", weights_only=False)
            self.assertEqual(float(sample.y_branch_priority.item()), 1.0)
            self.assertGreater(float(sample.branch_priority_loss_weight.item()), 0.0)
            self.assertAlmostEqual(float(sample.y_walltime_gain.item()), 120.0)
            self.assertGreater(float(sample.walltime_gain_loss_weight.item()), 0.0)
            self.assertEqual(float(sample.y_tree_policy.item()), 1.0)

    def test_normalizes_schema_less_branch_impact_tail_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            instance = root / "toy.json"
            instance.write_text(json.dumps(_toy_payload(), sort_keys=True), encoding="utf-8")
            rows = [
                {
                    "instance": str(instance),
                    "branch_node_id": 2,
                    "depth": 1,
                    "branch_time": 12.5,
                    "task_i": 1,
                    "task_j": 2,
                    "candidate_count": 4,
                    "eligible_count": 4,
                    "branch_feature_vector": [0.0] * len(BRANCH_IMPACT_FEATURE_SCHEMA),
                    "branch_labels": {
                        "y_completion_bound_tail": 1.0,
                        "y_child_completion_bound_retries": 3.0,
                        "y_child_exact_pricing_events": 5.0,
                        "y_child_negative_pricing_events": 2.0,
                    },
                    "children": [
                        {"time_span": 10.0, "time_to_first_certificate": 9.0},
                        {"time_span": 7.0, "time_to_first_certificate": None},
                    ],
                    "right_censored": True,
                }
            ]
            input_path = root / "branch_impact_rows.jsonl"
            input_path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
            output_dir = root / "dataset"
            manifest = build_tree_policy_event_dataset(
                [input_path],
                output_dir,
                root / "report.md",
            )

            self.assertEqual(manifest["sample_count"], 1)
            self.assertEqual(manifest["proof_tail_risk_sample_count"], 1)
            self.assertEqual(manifest["right_censored_sample_count"], 1)
            self.assertEqual(
                manifest["tree_policy_label_counts"]["tree_policy_proof_tail_hard_negative"],
                1,
            )
            sample = torch.load(output_dir / manifest["samples"][0]["path"], map_location="cpu", weights_only=False)
            self.assertEqual(float(sample.y_tree_policy.item()), 0.0)
            self.assertGreater(float(sample.tree_policy_loss_weight.item()), 0.0)
            self.assertAlmostEqual(float(sample.y_child_proof_cpu.item()), 17.0)
            self.assertAlmostEqual(float(sample.y_time_to_certificate.item()), 9.0)


if __name__ == "__main__":
    unittest.main()
