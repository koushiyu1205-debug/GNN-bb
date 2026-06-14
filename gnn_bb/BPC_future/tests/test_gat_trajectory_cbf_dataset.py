from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

try:
    import torch

    from BPC_future.learning.column_selector import SELECTOR_CLASS_ADD
    from BPC_future.scripts.build_gat_trajectory_cbf_dataset import build_dataset
    from BPC_future.tests.test_learning_components import _toy_payload

    HAS_LEARNING_STACK = True
except Exception:
    HAS_LEARNING_STACK = False


@unittest.skipUnless(HAS_LEARNING_STACK, "learning stack is not installed")
class GATTrajectoryCBFDatasetTests(unittest.TestCase):
    def test_builds_trajectory_labeled_candidate_batch(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            graph_path = tmp / "toy_selector_instance_logical_graph.json"
            graph_path.write_text(json.dumps(_toy_payload()), encoding="utf-8")
            capture = tmp / "capture.jsonl"
            event = {
                "event": "journey_counterfactual_replay_capture",
                "schema_version": "journey_counterfactual_replay_capture_v1",
                "diagnostic_only": True,
                "official_bound_effect": False,
                "instance": "toy_selector_instance",
                "instance_path": str(graph_path),
                "context_hash": "ctx-1",
                "cg_iter": 7,
                "pool_journey_count": 3,
                "active_basis_journey_count": 2,
                "active_basis_fractional_journey_count": 1,
                "active_task_set_count": 2,
                "rmp_objective_before": 123.0,
                "true_dual_vector": [1.0, -2.0, 3.0],
                "pool_task_sets": [[2, 3]],
                "pool_signatures": [],
                "returned_journeys": [
                    {
                        "id": "j1",
                        "task_set": [1, 3],
                        "cost": 10.0,
                        "true_reduced_cost": -5.0,
                        "signature": [["sig"]],
                        "trips": [{"tasks": [1, 3]}],
                    },
                    {
                        "id": "j2",
                        "task_set": [2],
                        "cost": 8.0,
                        "true_reduced_cost": -1.0,
                        "signature": [["sig2"]],
                        "trips": [{"tasks": [2]}],
                    },
                ],
            }
            capture.write_text(json.dumps(event, sort_keys=True) + "\n", encoding="utf-8")
            trajectory = tmp / "trajectory.jsonl"
            row = {
                "schema_version": "cbf_trajectory_gate_dataset_row_v1",
                "diagnostic_only": True,
                "official_bound_effect": False,
                "source_file": str(capture),
                "instance": "toy_selector_instance",
                "context_hash": "ctx-1",
                "cg_iter": 7,
                "label_horizon_cbf_feasible": 1,
                "horizon_delta_v": -3.0,
                "horizon_barrier_slack": 2.0,
            }
            trajectory.write_text(json.dumps(row, sort_keys=True) + "\n", encoding="utf-8")

            summary = build_dataset(
                trajectory_jsonl=trajectory,
                output_dir=tmp / "dataset",
            )

            manifest = json.loads((tmp / "dataset" / "manifest.json").read_text(encoding="utf-8"))
            sample = torch.load(
                tmp / "dataset" / manifest["samples"][0]["path"],
                map_location="cpu",
                weights_only=False,
            )
            self.assertTrue(summary["all_checks_pass"])
            self.assertFalse(summary["runs_bpc_or_pricing"])
            self.assertEqual(summary["label_counts"], {"add": 1})
            self.assertEqual(manifest["schema_version"], "gat_trajectory_cbf_dataset_manifest_v1")
            self.assertEqual(manifest["label_schema"], ["label_horizon_cbf_feasible"])
            self.assertEqual(tuple(sample.candidate_task_membership.shape), (2, 3))
            self.assertEqual(sample.candidate_task_membership.tolist(), [[1.0, 0.0, 1.0], [0.0, 1.0, 0.0]])
            self.assertEqual(sample.y_selector.tolist(), [SELECTOR_CLASS_ADD, SELECTOR_CLASS_ADD])
            self.assertEqual(sample.trajectory_label_horizon_cbf_feasible, 1)
            self.assertEqual(sample.selector_context_hash, "ctx-1")


if __name__ == "__main__":
    unittest.main()
