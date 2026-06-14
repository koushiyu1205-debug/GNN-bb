from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

try:
    import torch

    from BPC_future.scripts.build_gat_trajectory_cbf_dataset import build_dataset
    from BPC_future.scripts.train_gat_trajectory_cbf import train_trajectory_cbf
    from BPC_future.tests.test_learning_components import _toy_payload

    HAS_LEARNING_STACK = True
except Exception:
    HAS_LEARNING_STACK = False


@unittest.skipUnless(HAS_LEARNING_STACK, "learning stack is not installed")
class GATTrajectoryCBFTrainingTests(unittest.TestCase):
    def test_training_writes_horizon_cbf_checkpoint_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            graph_path = tmp / "toy_selector_instance_logical_graph.json"
            graph_path.write_text(json.dumps(_toy_payload()), encoding="utf-8")
            capture = tmp / "capture.jsonl"
            events = []
            rows = []
            for idx, feasible in enumerate([1, 0, 1, 0]):
                context_hash = f"ctx-{idx}"
                events.append(
                    {
                        "event": "journey_counterfactual_replay_capture",
                        "diagnostic_only": True,
                        "official_bound_effect": False,
                        "instance": f"toy_selector_instance_{idx % 2}",
                        "instance_path": str(graph_path),
                        "context_hash": context_hash,
                        "cg_iter": idx + 1,
                        "pool_journey_count": 3 + idx,
                        "active_basis_journey_count": 2,
                        "active_basis_fractional_journey_count": 1,
                        "active_task_set_count": 2,
                        "rmp_objective_before": 100.0 + idx,
                        "true_dual_vector": [1.0 + idx, -2.0, 3.0],
                        "pool_task_sets": [[2, 3]],
                        "pool_signatures": [],
                        "returned_journeys": [
                            {
                                "id": f"j{idx}a",
                                "task_set": [1, 3],
                                "cost": 10.0 + idx,
                                "true_reduced_cost": -5.0,
                                "signature": [["sig", idx]],
                                "trips": [{"tasks": [1, 3]}],
                            },
                            {
                                "id": f"j{idx}b",
                                "task_set": [2],
                                "cost": 8.0,
                                "true_reduced_cost": -1.0,
                                "signature": [["sig2", idx]],
                                "trips": [{"tasks": [2]}],
                            },
                        ],
                    }
                )
                rows.append(
                    {
                        "schema_version": "cbf_trajectory_gate_dataset_row_v1",
                        "diagnostic_only": True,
                        "official_bound_effect": False,
                        "source_file": str(capture),
                        "instance": f"toy_selector_instance_{idx % 2}",
                        "context_hash": context_hash,
                        "cg_iter": idx + 1,
                        "label_horizon_cbf_feasible": feasible,
                        "horizon_delta_v": -3.0 if feasible else 2.0,
                        "horizon_barrier_slack": 2.0 if feasible else -1.0,
                    }
                )
            capture.write_text(
                "\n".join(json.dumps(event, sort_keys=True) for event in events) + "\n",
                encoding="utf-8",
            )
            trajectory = tmp / "trajectory.jsonl"
            trajectory.write_text(
                "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
                encoding="utf-8",
            )
            dataset_dir = tmp / "dataset"
            build_dataset(trajectory_jsonl=trajectory, output_dir=dataset_dir)

            args = SimpleNamespace(
                dataset_dir=dataset_dir,
                checkpoint_out=tmp / "trajectory_gat.pt",
                metrics_out=tmp / "metrics.json",
                report=tmp / "report.md",
                device="cpu",
                epochs=2,
                lr=1.0e-3,
                weight_decay=1.0e-5,
                hidden_dim=16,
                option_hidden_dim=16,
                pair_edge_dim=16,
                selector_hidden_dim=16,
                num_gnn_layers=1,
                heads=4,
                dropout=0.0,
                validation_fraction=0.5,
                seed=5,
            )
            summary = train_trajectory_cbf(args)

            checkpoint = torch.load(args.checkpoint_out, map_location="cpu", weights_only=False)
            self.assertTrue(summary["all_checks_pass"])
            self.assertEqual(summary["target_label"], "label_horizon_cbf_feasible")
            self.assertFalse(summary["selector_can_certificate"])
            self.assertFalse(summary["selector_is_pricing_oracle"])
            self.assertFalse(summary["gate_can_permanently_discard_negative_columns"])
            self.assertFalse(summary["production_ready"])
            self.assertEqual(checkpoint["target_label"], "label_horizon_cbf_feasible")
            self.assertFalse(checkpoint["trajectory_contract"]["certificate_source"])
            self.assertFalse(checkpoint["trajectory_contract"]["pricing_oracle"])
            self.assertIn("never a pricing oracle", checkpoint["exactness_contract"])
            self.assertTrue(args.metrics_out.exists())
            self.assertTrue(args.report.exists())


if __name__ == "__main__":
    unittest.main()
