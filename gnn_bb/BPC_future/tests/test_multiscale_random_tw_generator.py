from __future__ import annotations

import json
import math
import tempfile
import unittest
from pathlib import Path

import numpy as np

from BPC_future.scripts.generate_moon_trek_multiscale_random_tw_benchmark import (
    NODE_FEATURE_SCHEMA,
    OPTION_FEATURE_SCHEMA,
    PROFILES,
    _apply_random_time_windows,
    _augment_matrices_with_path_options,
    _budgeted_subset_min_closed_energy,
    _export_gnn_tensors,
    _manifest_generation_summary,
    _minimum_task_spacing_km,
    _random_time_window_template,
    _time_window_audit_budgeted,
)

try:
    import torch

    HAS_TORCH = True
except Exception:
    HAS_TORCH = False


def _toy_scenario(task_count: int, *, horizon: float = 720.0) -> dict[str, object]:
    return {
        "scheduling": {"horizon_min": float(horizon)},
        "tasks": [
            {
                "id": f"task_{task_id}",
                "service_time_min": 6.0,
                "ready_time_min": 0.0,
                "due_time_min": horizon,
            }
            for task_id in range(1, int(task_count) + 1)
        ],
    }


def _toy_matrices(task_count: int) -> dict[str, object]:
    n = int(task_count) + 1
    time = np.zeros((n, n), dtype=float)
    energy = np.zeros((n, n), dtype=float)
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            time[i, j] = 8.0 + 0.7 * abs(i - j) + 0.15 * ((i + j) % 5)
            energy[i, j] = 3.0 + 0.4 * abs(i - j) + 0.05 * ((i * j) % 7)
    service_time = np.zeros(n, dtype=float)
    service_energy = np.zeros(n, dtype=float)
    service_time[1:] = 6.0
    service_energy[1:] = 0.25
    return {
        "node_names": ["depot", *[f"task_{task_id}" for task_id in range(1, int(task_count) + 1)]],
        "task_names": [f"task_{task_id}" for task_id in range(1, int(task_count) + 1)],
        "time": time,
        "energy": energy,
        "distance": energy.copy(),
        "service_time": service_time,
        "service_energy": service_energy,
    }


def _complete_multpath_payload(task_count: int, *, slow_time: float = 400.0) -> dict[str, object]:
    node_ids = ["depot", *[f"task_{task_id}" for task_id in range(1, int(task_count) + 1)]]
    nodes = [{"id": node_id, "xy_km": [float(index), 0.0]} for index, node_id in enumerate(node_ids)]
    edges = []
    for src in node_ids:
        for dst in node_ids:
            if src == dst:
                continue
            edges.append(
                {
                    "from": src,
                    "to": dst,
                    "feasible": True,
                    "path_options": [
                        {"path_type": "low_time", "aliases": ["low_time"], "travel_time_min": 10.0},
                        {"path_type": "low_energy", "aliases": ["low_energy"], "travel_time_min": float(slow_time)},
                        {"path_type": "low_risk", "aliases": ["low_risk"], "travel_time_min": 0.5 * (10.0 + float(slow_time))},
                    ],
                }
            )
    return {"logical_graph": {"nodes": nodes, "edges": edges}}


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
                "d": 1.0,
                "sigma": 7.0,
                "r": 10.0,
                "D": 260.0,
                "g": 0.3,
                "local_risk": 0.2,
            },
        ],
    }
    nodes = [
        {"id": "depot", "kind": "depot", "xy_km": [0.0, 0.0]},
        {"id": "task_1", "kind": "task", "xy_km": [1.0, 0.0], "risk": 0.1},
        {"id": "task_2", "kind": "task", "xy_km": [0.0, 2.0], "risk": 0.2},
    ]
    node_ids = [node["id"] for node in nodes]
    edges = []
    for src in node_ids:
        for dst in node_ids:
            if src == dst:
                continue
            edges.append(
                {
                    "from": src,
                    "to": dst,
                    "feasible": True,
                    "path_options": [
                        {
                            "path_type": "low_time",
                            "aliases": ["low_time"],
                            "travel_time_min": 5.0,
                            "energy_proxy": 3.0,
                            "risk_integral": 0.4,
                            "path_distance_km": 1.2,
                            "generalized_cost": 2.5,
                        }
                    ],
                }
            )
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


class MultiscaleRandomTwGeneratorTests(unittest.TestCase):
    def test_random_time_windows_vary_by_seed_and_keep_singletons_feasible(self) -> None:
        matrices = _toy_matrices(10)
        scenario_a = _toy_scenario(10)
        scenario_b = _toy_scenario(10)

        template_a = _apply_random_time_windows(scenario_a, matrices, profile=PROFILES[10], seed=101)
        template_b = _apply_random_time_windows(scenario_b, matrices, profile=PROFILES[10], seed=202)

        self.assertNotEqual(template_a, template_b)
        audit = _time_window_audit_budgeted(
            scenario_a,
            matrices,
            task_count=10,
            seed=303,
            exact_task_limit=20,
            triple_sample_count=100,
        )
        self.assertTrue(audit["single_task_timed_feasible"])
        self.assertGreaterEqual(audit["time_pair_feasible_ratio"], 0.0)
        self.assertLessEqual(audit["time_pair_feasible_ratio"], 1.0)
        self.assertIn("time_pair_estimate", audit)
        self.assertIn("wilson95_low", audit["time_pair_estimate"])

    def test_time_window_modes_have_distinct_anchor_templates(self) -> None:
        matrices = _toy_matrices(10)
        scenario = _toy_scenario(10)
        templates = {
            mode: _random_time_window_template(
                scenario,
                10,
                horizon=720.0,
                profile=PROFILES[10],
                seed=777,
                matrices=matrices,
                mode=mode,
            )
            for mode in ("greedy-anchor", "random-wave", "sector-wave")
        }

        self.assertNotEqual(templates["greedy-anchor"], templates["random-wave"])
        self.assertNotEqual(templates["greedy-anchor"], templates["sector-wave"])
        self.assertNotEqual(templates["random-wave"], templates["sector-wave"])

    def test_budgeted_energy_subset_audit_does_not_enumerate_large_combinations(self) -> None:
        matrices = _toy_matrices(100)
        subsets = _budgeted_subset_min_closed_energy(
            matrices,
            max_size=6,
            seed=404,
            exact_task_limit=20,
            sample_count=25,
        )

        self.assertEqual(len(subsets[1]), 100)
        self.assertLessEqual(len(subsets[2]), 25)
        self.assertLessEqual(len(subsets[6]), 25)
        self.assertLess(len(subsets[6]), math.comb(100, 6))

    def test_path_option_spread_enters_smart_window_floor(self) -> None:
        matrices = _augment_matrices_with_path_options(_toy_matrices(5), _complete_multpath_payload(5, slow_time=420.0))
        spread = matrices["multi_path_time_spread"]
        self.assertGreaterEqual(float(spread[1]), 410.0)

        template = _random_time_window_template(
            _toy_scenario(5, horizon=2000.0),
            5,
            horizon=2000.0,
            profile=PROFILES[5],
            seed=505,
            matrices=matrices,
        )
        min_width = max(35.0, min(80.0, 0.28 * PROFILES[5].window_base_min))
        for ready, due in template.values():
            self.assertGreaterEqual((due - ready) + 1.0e-6, min_width + 410.0)

    def test_manifest_summary_keeps_acceptance_and_distribution_stats(self) -> None:
        manifest = {
            "attempts": [
                {
                    "status": "skipped",
                    "terrain": "terrain_a",
                    "task_count": 5,
                    "time_window_mode": "greedy-anchor",
                    "reason_bucket": "time pair density out of band",
                },
                {
                    "status": "accepted",
                    "terrain": "terrain_a",
                    "task_count": 5,
                    "time_window_mode": "greedy-anchor",
                },
            ],
            "instances": [
                {
                    "terrain": "terrain_a",
                    "task_count": 5,
                    "time_window_mode": "greedy-anchor",
                    "balanced_audit": {
                        "time_pair_feasible_ratio": 0.5,
                        "time_triple_feasible_ratio": 0.25,
                        "energy_pair_feasible_ratio": 0.8,
                        "energy_triple_feasible_ratio": 0.4,
                        "energy_quad_feasible_ratio": 0.2,
                        "energy_large_feasible_ratio": 0.1,
                        "window_width_median_ratio": 0.3,
                        "window_width_to_horizon_distribution": {"median": 0.3},
                        "multi_path_spread_to_window_width_distribution": {"median": 0.2},
                    },
                }
            ],
        }

        summary = _manifest_generation_summary(manifest)
        group = summary["group_by_task_mode_terrain"]["tasks=005|mode=greedy-anchor|terrain=terrain_a"]
        self.assertEqual(group["attempt_count"], 2)
        self.assertEqual(group["accepted_count"], 1)
        self.assertAlmostEqual(group["acceptance_rate"], 0.5)
        self.assertIn("time_pair_feasible_ratio", group["metric_distributions"])
        self.assertEqual(group["skip_reason_counts"]["time pair density out of band"], 1)

    def test_minimum_task_spacing_reports_pairwise_distance(self) -> None:
        scenario = {"tasks": [{"xy_km": [0.0, 0.0]}, {"xy_km": [3.0, 4.0]}, {"xy_km": [10.0, 0.0]}]}
        self.assertAlmostEqual(_minimum_task_spacing_km(scenario), 5.0)

    def test_tensor_export_writes_npz_dict_shapes_without_learning_stack(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            graph_path = root / "instance_logical_graph.json"
            scenario_path = root / "instance.json"
            payload = _toy_payload()
            graph_path.write_text(json.dumps(payload), encoding="utf-8")
            scenario_path.write_text(json.dumps(payload["scenario"]), encoding="utf-8")

            entry = _export_gnn_tensors(
                graph_path=graph_path,
                output_root=root / "out",
                instance_id="toy",
                terrain="synthetic",
                task_count=2,
                seed=1,
                scenario_path=scenario_path,
                tensor_format="npz",
            )

            self.assertNotIn("pt", entry)
            with np.load(Path(entry["npz"])) as npz:
                self.assertEqual(tuple(npz["x"].shape), (3, len(NODE_FEATURE_SCHEMA)))
                self.assertEqual(tuple(npz["pair_edge_index"].shape), (2, 6))
                self.assertEqual(tuple(npz["option_feat"].shape), (6, len(OPTION_FEATURE_SCHEMA)))
                self.assertEqual(tuple(npz["option_pair_id"].shape), (6,))
                self.assertEqual(list(npz["node_feature_schema"]), list(NODE_FEATURE_SCHEMA))
                self.assertEqual(list(npz["option_feature_schema"]), list(OPTION_FEATURE_SCHEMA))

    @unittest.skipUnless(HAS_TORCH, "torch is not installed")
    def test_tensor_export_writes_pt_and_npz_dict_shapes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            graph_path = root / "instance_logical_graph.json"
            scenario_path = root / "instance.json"
            payload = _toy_payload()
            graph_path.write_text(json.dumps(payload), encoding="utf-8")
            scenario_path.write_text(json.dumps(payload["scenario"]), encoding="utf-8")

            entry = _export_gnn_tensors(
                graph_path=graph_path,
                output_root=root / "out",
                instance_id="toy",
                terrain="synthetic",
                task_count=2,
                seed=1,
                scenario_path=scenario_path,
                tensor_format="both",
            )

            pt_path = Path(entry["pt"])
            npz_path = Path(entry["npz"])
            meta_path = Path(entry["meta"])
            self.assertTrue(pt_path.exists())
            self.assertTrue(npz_path.exists())
            self.assertTrue(meta_path.exists())

            loaded = torch.load(pt_path, weights_only=False)
            self.assertEqual(tuple(loaded["x"].shape), (3, len(NODE_FEATURE_SCHEMA)))
            self.assertEqual(tuple(loaded["pair_edge_index"].shape), (2, 6))
            self.assertEqual(tuple(loaded["option_feat"].shape), (6, len(OPTION_FEATURE_SCHEMA)))
            self.assertEqual(loaded["node_feature_schema"], list(NODE_FEATURE_SCHEMA))
            self.assertEqual(loaded["option_feature_schema"], list(OPTION_FEATURE_SCHEMA))

            with np.load(npz_path) as npz:
                self.assertEqual(tuple(npz["x"].shape), (3, len(NODE_FEATURE_SCHEMA)))
                self.assertEqual(tuple(npz["pair_edge_index"].shape), (2, 6))
                self.assertEqual(tuple(npz["option_feat"].shape), (6, len(OPTION_FEATURE_SCHEMA)))
                self.assertEqual(list(npz["node_feature_schema"]), list(NODE_FEATURE_SCHEMA))
                self.assertEqual(list(npz["option_feature_schema"]), list(OPTION_FEATURE_SCHEMA))


if __name__ == "__main__":
    unittest.main()
