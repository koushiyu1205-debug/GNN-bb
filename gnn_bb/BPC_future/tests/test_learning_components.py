from __future__ import annotations

import tempfile
import unittest
import warnings
from pathlib import Path
from types import SimpleNamespace

try:
    import torch

    from BPC_future.learning.dual_stabilizer import DualStabilizer, DualStabilizerConfig
    from BPC_future.learning.gnn_model import HierarchicalOptionGAT, OptionEncoder, dual_prediction_loss
    from BPC_future.learning.graph_builder import (
        DEFAULT_NODE_FEATURE_SCHEMA,
        DEFAULT_OPTION_FEATURE_SCHEMA,
        FutureGraphBuilder,
    )
    from BPC_future.scripts.build_learning_dual_dataset import _average_cover_duals, _collect_traces
    from BPC_future.scripts.train_learning_dual_model import _split_samples

    HAS_LEARNING_STACK = True
except Exception:
    HAS_LEARNING_STACK = False


def _toy_payload() -> dict[str, object]:
    scenario = {
        "depot": {"id": "depot", "xy_km": [0.0, 0.0]},
        "vehicle": {"H": 720.0},
        "tasks": [
            {
                "id": "task_1",
                "xy_km": [1.0, 0.0],
                "d": 1.0,
                "sigma": 5.0,
                "r": 0.0,
                "D": 200.0,
                "g": 0.2,
                "local_risk": 0.1,
            },
            {
                "id": "task_2",
                "xy_km": [0.0, 2.0],
                "d": 2.0,
                "sigma": 7.0,
                "r": 10.0,
                "D": 260.0,
                "g": 0.3,
                "local_risk": 0.2,
            },
            {
                "id": "task_3",
                "xy_km": [2.0, 2.0],
                "d": 1.5,
                "sigma": 6.0,
                "r": 20.0,
                "D": 300.0,
                "g": 0.4,
                "local_risk": 0.3,
            },
        ],
    }
    nodes = [
        {"id": "depot", "kind": "depot", "xy_km": [0.0, 0.0]},
        {"id": "task_1", "kind": "task", "xy_km": [1.0, 0.0], "risk": 0.1},
        {"id": "task_2", "kind": "task", "xy_km": [0.0, 2.0], "risk": 0.2},
        {"id": "task_3", "kind": "task", "xy_km": [2.0, 2.0], "risk": 0.3},
    ]
    node_ids = [node["id"] for node in nodes]
    edges = []
    for src in node_ids:
        for dst in node_ids:
            if src == dst:
                continue
            options = [_option("low_time", 3.0, 8.0, 0.5, 1.1, 4.0)]
            if src == "depot" and dst == "task_1":
                options.append(_option("low_energy", 5.0, 3.0, 0.7, 1.4, 3.5))
                options.append(_option("low_risk", 6.0, 4.0, 99.0, 1.6, 5.0))
            elif src == "task_1" and dst == "depot":
                options = [_option("low_time", 4.0, 11.0, 0.4, 1.2, 4.5)]
            else:
                options.append(_option("low_energy", 4.5, 5.0, 0.6, 1.3, 3.8))
            edges.append({"from": src, "to": dst, "feasible": True, "path_options": options})
    return {
        "scenario": scenario,
        "logical_graph": {
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "directed_edge_count": len(edges),
            "feasible_directed_edge_count": len(edges),
        },
    }


def _option(
    path_type: str,
    travel_time: float,
    energy: float,
    risk: float,
    distance: float,
    cost: float,
) -> dict[str, object]:
    return {
        "path_type": path_type,
        "aliases": [path_type],
        "travel_time_min": travel_time,
        "energy_proxy": energy,
        "risk_integral": risk,
        "path_distance_km": distance,
        "generalized_cost": cost,
    }


@unittest.skipUnless(HAS_LEARNING_STACK, "learning stack is not installed")
class LearningGraphBuilderTests(unittest.TestCase):
    def test_toy_graph_builder_preserves_directed_options(self):
        builder = FutureGraphBuilder()
        data = builder.build_from_logical_graph(_toy_payload())

        self.assertEqual(tuple(data.x.shape), (4, len(DEFAULT_NODE_FEATURE_SCHEMA)))
        self.assertEqual(tuple(data.pair_edge_index.shape), (2, 12))
        self.assertEqual(data.option_feat.size(1), len(DEFAULT_OPTION_FEATURE_SCHEMA))
        self.assertEqual(data.option_pair_id.numel(), data.option_feat.size(0))
        self.assertFalse(bool(data.task_mask[0]))
        self.assertTrue(bool(torch.all(data.task_mask[1:])))
        self.assertEqual(data.task_ids.tolist(), [1, 2, 3])
        self.assertTrue(torch.all(torch.bincount(data.option_pair_id, minlength=data.pair_edge_index.size(1)) >= 1))

        forward_01 = data.option_feat[data.option_pair_id == 0]
        reverse_10 = data.option_feat[data.option_pair_id == 2]
        self.assertFalse(torch.allclose(forward_01[0], reverse_10[0]))

    def test_builder_applies_flat_checkpoint_normalizer(self):
        checkpoint = {
            "feature_schema": {
                "node": list(DEFAULT_NODE_FEATURE_SCHEMA),
                "option": list(DEFAULT_OPTION_FEATURE_SCHEMA),
            },
            "node_feature_mean": [0.0] * len(DEFAULT_NODE_FEATURE_SCHEMA),
            "node_feature_std": [2.0] * len(DEFAULT_NODE_FEATURE_SCHEMA),
            "option_feature_mean": [0.0] * len(DEFAULT_OPTION_FEATURE_SCHEMA),
            "option_feature_std": [2.0] * len(DEFAULT_OPTION_FEATURE_SCHEMA),
        }
        raw = FutureGraphBuilder().build_from_logical_graph(_toy_payload())
        normalized = FutureGraphBuilder.from_checkpoint(checkpoint).build_from_logical_graph(_toy_payload())
        self.assertTrue(bool(normalized.learning_features_normalized))
        self.assertTrue(torch.allclose(normalized.x, raw.x / 2.0))
        self.assertTrue(torch.allclose(normalized.option_feat, raw.option_feat / 2.0))

    def test_builder_rejects_missing_core_task_features(self):
        payload = _toy_payload()
        del payload["scenario"]["tasks"][0]["d"]

        with self.assertRaisesRegex(ValueError, "task 1 missing required numeric field"):
            FutureGraphBuilder().build_from_logical_graph(payload)

    def test_pyg_batch_offsets_option_pair_ids(self):
        from torch_geometric.data import Batch

        first = FutureGraphBuilder().build_from_logical_graph(_toy_payload())
        second = FutureGraphBuilder().build_from_logical_graph(_toy_payload())
        batch = Batch.from_data_list([first, second])
        pair_count = first.pair_edge_index.size(1)
        option_count = first.option_pair_id.numel()
        self.assertEqual(int(batch.option_pair_id[:option_count].max().item()), pair_count - 1)
        self.assertEqual(int(batch.option_pair_id[option_count:].min().item()), pair_count)
        self.assertEqual(batch.task_ids.tolist(), [1, 2, 3, 1, 2, 3])


@unittest.skipUnless(HAS_LEARNING_STACK, "learning stack is not installed")
class LearningModelTests(unittest.TestCase):
    def test_option_encoder_grouped_attention_and_extrema(self):
        data = FutureGraphBuilder().build_from_logical_graph(_toy_payload())
        encoder = OptionEncoder(
            node_hidden_dim=8,
            option_dim=data.option_feat.size(1),
            option_hidden_dim=8,
            pair_edge_dim=16,
            dropout=0.0,
        )
        node_h = torch.randn(data.x.size(0), 8)
        pair_edge_attr, aux = encoder(node_h, data.pair_edge_index, data.option_feat, data.option_pair_id)
        int_pair_edge_attr, _ = encoder(
            node_h,
            data.pair_edge_index,
            data.option_feat,
            data.option_pair_id.to(torch.int32),
        )

        self.assertEqual(tuple(pair_edge_attr.shape), (data.pair_edge_index.size(1), 16))
        self.assertEqual(tuple(int_pair_edge_attr.shape), (data.pair_edge_index.size(1), 16))
        for pair_id in range(data.pair_edge_index.size(1)):
            attention_sum = aux["option_attention"][data.option_pair_id == pair_id].sum()
            self.assertAlmostEqual(float(attention_sum.detach()), 1.0, places=5)

        risk_feature_position = 3
        self.assertAlmostEqual(float(aux["max_pool"][0, risk_feature_position]), 99.0, places=5)
        self.assertTrue(torch.all(torch.isfinite(aux["std_pool"])))
        option_counts = torch.bincount(data.option_pair_id, minlength=data.pair_edge_index.size(1))
        single_option_pair = int(torch.nonzero(option_counts == 1, as_tuple=False)[0].item())
        self.assertTrue(
            torch.allclose(
                aux["std_pool"][single_option_pair],
                torch.zeros_like(aux["std_pool"][single_option_pair]),
            )
        )

    def test_hierarchical_option_gat_forward_backward_and_negative_output(self):
        data = FutureGraphBuilder().build_from_logical_graph(_toy_payload())
        model = HierarchicalOptionGAT(
            node_dim=data.x.size(1),
            option_dim=data.option_feat.size(1),
            hidden_dim=16,
            option_hidden_dim=16,
            pair_edge_dim=16,
            num_gnn_layers=2,
            heads=4,
            dropout=0.0,
        )
        output = model(data)
        self.assertEqual(tuple(output["pred_all_nodes"].shape), (data.x.size(0),))
        self.assertEqual(tuple(output["pred_task"].shape), (int(data.task_mask.sum().item()),))
        loss = dual_prediction_loss(output["pred_task"], torch.zeros_like(output["pred_task"]), huber_delta=0.1)
        loss.backward()

        with torch.no_grad():
            for param in model.parameters():
                param.zero_()
            model.out_mlp[-1].bias.fill_(-1.0)
        negative_output = model(data)
        self.assertTrue(bool(torch.all(negative_output["pred_task"] < 0.0)))


@unittest.skipUnless(HAS_LEARNING_STACK, "learning stack is not installed")
class DualStabilizerTests(unittest.TestCase):
    def test_checkpoint_anchor_smoothing_alpha_and_fallback(self):
        data = FutureGraphBuilder().build_from_logical_graph(_toy_payload())
        model = HierarchicalOptionGAT(
            node_dim=data.x.size(1),
            option_dim=data.option_feat.size(1),
            hidden_dim=16,
            option_hidden_dim=16,
            pair_edge_dim=16,
            num_gnn_layers=1,
            heads=4,
            dropout=0.0,
        )
        with tempfile.TemporaryDirectory() as tmp:
            checkpoint_path = Path(tmp) / "fake_checkpoint.pt"
            torch.save(
                {
                    "model_state_dict": model.state_dict(),
                    "model_config": {
                        "node_dim": data.x.size(1),
                        "option_dim": data.option_feat.size(1),
                        "hidden_dim": 16,
                        "option_hidden_dim": 16,
                        "pair_edge_dim": 16,
                        "num_gnn_layers": 1,
                        "heads": 4,
                        "dropout": 0.0,
                        "use_layer_norm": True,
                    },
                    "node_feature_mean": [0.0] * data.x.size(1),
                    "node_feature_std": [1.0] * data.x.size(1),
                    "option_feature_mean": [0.0] * data.option_feat.size(1),
                    "option_feature_std": [1.0] * data.option_feat.size(1),
                    "label_mean": 0.0,
                    "label_std": 1.0,
                    "feature_schema": {
                        "node": list(DEFAULT_NODE_FEATURE_SCHEMA),
                        "option": list(DEFAULT_OPTION_FEATURE_SCHEMA),
                    },
                    "version": "v1",
                },
                checkpoint_path,
            )
            stabilizer = DualStabilizer(
                DualStabilizerConfig(checkpoint_path=str(checkpoint_path), alpha_init=0.8, alpha_decay=0.05)
            )
            anchor = stabilizer.predict_anchor(data)
            self.assertEqual(set(anchor), {1, 2, 3})
            from torch_geometric.data import Batch

            with self.assertRaisesRegex(ValueError, "exactly one PyG graph"):
                stabilizer.predict_anchor(Batch.from_data_list([data, data]))

            true_duals = {1: 10.0, 2: 20.0, 3: 30.0}
            predicted = {1: 0.0, 2: 10.0, 3: 20.0}
            smoothed = stabilizer.smooth_task_duals(true_duals, predicted, alpha=0.25)
            self.assertEqual(smoothed, {1: 7.5, 2: 17.5, 3: 27.5})

            alpha = stabilizer.update_alpha([100.0], branch_depth=0)
            self.assertAlmostEqual(alpha, 0.8)
            alpha = stabilizer.update_alpha([100.0, 90.0], branch_depth=0)
            self.assertAlmostEqual(alpha, 0.75)
            alpha = stabilizer.update_alpha([100.0, 99.99], branch_depth=1)
            self.assertEqual(alpha, 0.0)
            decision = stabilizer.handle_smoothed_pricing_result(found_negative_column=False)
            self.assertTrue(decision.use_true_dual_exact_pricing)
            self.assertEqual(stabilizer.update_alpha([100.0, 90.0, 80.0], branch_depth=0), 0.0)

            stabilizer.reset_runtime_state()
            self.assertAlmostEqual(stabilizer.alpha, 0.8)
            self.assertIsNone(stabilizer.last_anchor)
            self.assertFalse(stabilizer.handle_smoothed_pricing_result(found_negative_column=True).use_true_dual_exact_pricing)


@unittest.skipUnless(HAS_LEARNING_STACK, "learning stack is not installed")
class LearningDatasetBuilderTests(unittest.TestCase):
    def test_collect_traces_keeps_repeated_instance_runs_separate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            instance = root / "same_instance_logical_graph.json"
            first_log = root / "run1.jsonl"
            second_log = root / "run2.jsonl"
            failed_log = root / "failed.jsonl"

            first_log.write_text(
                "\n".join(
                    [
                        _trace_line(instance, cg_iter=1, value=10.0),
                        _trace_line(instance, cg_iter=2, value=20.0),
                        '{"event": "finish", "status": "OPTIMAL"}',
                    ]
                ),
                encoding="utf-8",
            )
            second_log.write_text(
                "\n".join(
                    [
                        _trace_line(instance, cg_iter=1, value=100.0),
                        _trace_line(instance, cg_iter=2, value=200.0),
                        '{"event": "finish", "status": "OPTIMAL"}',
                    ]
                ),
                encoding="utf-8",
            )
            failed_log.write_text(
                "\n".join(
                    [
                        _trace_line(instance, cg_iter=1, value=999.0),
                        '{"event": "finish", "status": "TIME_LIMIT"}',
                    ]
                ),
                encoding="utf-8",
            )

            groups = _collect_traces([root], require_finish_status="OPTIMAL")

        self.assertEqual(len(groups), 2)
        means_by_log = {
            group.log_path.name: _average_cover_duals(group.records)[1]
            for group in groups
        }
        self.assertEqual(means_by_log, {"run1.jsonl": 15.0, "run2.jsonl": 150.0})

    def test_collect_traces_filters_non_root_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            instance = root / "same_instance_logical_graph.json"
            log_path = root / "run.jsonl"
            log_path.write_text(
                "\n".join(
                    [
                        _trace_line(instance, cg_iter=1, value=10.0, node_id=0, depth=0),
                        _trace_line(instance, cg_iter=1, value=999.0, node_id=3, depth=1),
                        '{"event": "finish", "status": "OPTIMAL"}',
                    ]
                ),
                encoding="utf-8",
            )

            root_only = _collect_traces([log_path], require_finish_status="OPTIMAL")
            all_depths = _collect_traces([log_path], require_finish_status="OPTIMAL", max_depth=-1)

        self.assertEqual(len(root_only), 1)
        self.assertEqual(_average_cover_duals(root_only[0].records)[1], 10.0)
        self.assertEqual(len(all_depths[0].records), 2)

    def test_training_split_keeps_same_instance_samples_together(self):
        import random

        random.seed(3)
        samples = [
            SimpleNamespace(learning_instance_path="a"),
            SimpleNamespace(learning_instance_path="a"),
            SimpleNamespace(learning_instance_path="b"),
            SimpleNamespace(learning_instance_path="c"),
            SimpleNamespace(learning_instance_path="d"),
        ]

        train_samples, val_samples, split_info = _split_samples(
            samples,
            validation_fraction=0.4,
            split_by_instance=True,
        )

        train_instances = {sample.learning_instance_path for sample in train_samples}
        val_instances = {sample.learning_instance_path for sample in val_samples}
        self.assertEqual(split_info["mode"], "instance")
        self.assertTrue(val_instances)
        self.assertTrue(train_instances)
        self.assertFalse(train_instances & val_instances)


def _trace_line(
    instance_path: Path,
    *,
    cg_iter: int,
    value: float,
    node_id: int = 0,
    depth: int = 0,
) -> str:
    import json

    return json.dumps(
        {
            "event": "journey_learning_dual_trace",
            "instance_path": str(instance_path),
            "node_id": int(node_id),
            "depth": int(depth),
            "cg_iter": int(cg_iter),
            "time": float(cg_iter),
            "cover": {"1": float(value)},
        },
        sort_keys=True,
    )


if __name__ == "__main__":
    with warnings.catch_warnings():
        warnings.simplefilter("default")
        unittest.main()
