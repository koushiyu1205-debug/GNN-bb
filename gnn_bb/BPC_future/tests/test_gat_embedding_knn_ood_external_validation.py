from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

try:
    from BPC_future.scripts.audit_gat_embedding_knn_ood_external_validation import (
        audit_gat_embedding_external_validation,
    )
    from BPC_future.scripts.build_gat_trajectory_cbf_dataset import build_dataset
    from BPC_future.scripts.train_gat_trajectory_cbf import train_trajectory_cbf
    from BPC_future.tests.test_learning_components import _toy_payload

    HAS_LEARNING_STACK = True
except Exception:
    HAS_LEARNING_STACK = False


def _make_capture_and_rows(
    *,
    root: Path,
    graph_path: Path,
    name: str,
    labels: list[int],
) -> tuple[Path, Path]:
    capture = root / f"{name}_capture.jsonl"
    trajectory = root / f"{name}_trajectory.jsonl"
    events = []
    rows = []
    for idx, feasible in enumerate(labels):
        context_hash = f"{name}-ctx-{idx}"
        events.append(
            {
                "event": "journey_counterfactual_replay_capture",
                "diagnostic_only": True,
                "official_bound_effect": False,
                "instance": f"{name}_instance_{idx % 2}",
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
                        "id": f"{name}-j{idx}a",
                        "task_set": [1, 3],
                        "cost": 10.0 + idx,
                        "true_reduced_cost": -5.0,
                        "signature": [["sig", idx]],
                        "trips": [{"tasks": [1, 3]}],
                    },
                    {
                        "id": f"{name}-j{idx}b",
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
                "instance": f"{name}_instance_{idx % 2}",
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
    trajectory.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )
    return capture, trajectory


@unittest.skipUnless(HAS_LEARNING_STACK, "learning stack is not installed")
class GATEmbeddingKNNOODExternalValidationTests(unittest.TestCase):
    def test_embedding_validation_keeps_delay_queue_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            graph_path = tmp / "toy_selector_instance_logical_graph.json"
            graph_path.write_text(json.dumps(_toy_payload()), encoding="utf-8")
            _capture, train_trajectory = _make_capture_and_rows(
                root=tmp,
                graph_path=graph_path,
                name="train",
                labels=[1, 0, 1, 0],
            )
            _capture_v, validation_trajectory = _make_capture_and_rows(
                root=tmp,
                graph_path=graph_path,
                name="validation",
                labels=[1, 0],
            )
            train_dir = tmp / "train_dataset"
            validation_dir = tmp / "validation_dataset"
            build_dataset(trajectory_jsonl=train_trajectory, output_dir=train_dir)
            build_dataset(trajectory_jsonl=validation_trajectory, output_dir=validation_dir)
            checkpoint = tmp / "trajectory_gat.pt"
            train_trajectory_cbf(
                SimpleNamespace(
                    dataset_dir=train_dir,
                    checkpoint_out=checkpoint,
                    metrics_out=tmp / "metrics.json",
                    report=tmp / "training_report.md",
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
                    seed=11,
                )
            )

            summary = audit_gat_embedding_external_validation(
                train_dataset_dir=train_dir,
                validation_dataset_dir=validation_dir,
                checkpoint=checkpoint,
                output_dir=tmp / "audit",
                report=tmp / "audit.md",
                device="cpu",
                min_validation_rows=1,
                min_validation_high_priority=0,
                min_high_priority_threshold=0.5,
                knn_k=1,
                max_neighbor_unsafe_fraction=1.0,
                safe_radius_quantile=1.0,
                safe_radius_multiplier=10.0,
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertFalse(summary["runs_bpc_or_pricing"])
            self.assertFalse(summary["official_bound_effect"])
            self.assertFalse(summary["production_ready"])
            self.assertFalse(summary["gate_can_permanently_discard_negative_columns"])
            self.assertTrue(summary["negative_columns_must_remain_eventually_reachable"])
            self.assertFalse(summary["delay_queue_can_extend_proof_budget"])
            self.assertFalse(summary["delay_queue_runs_proof_sweep"])
            self.assertIn("overall", summary["validation_metrics"])
            self.assertTrue((tmp / "audit" / "decision_records.jsonl").exists())
            self.assertTrue((tmp / "audit.md").exists())


if __name__ == "__main__":
    unittest.main()
