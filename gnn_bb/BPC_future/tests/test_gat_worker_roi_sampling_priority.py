from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from BPC_future.scripts.audit_gat_worker_roi_sampling_priority import (
    build_sampling_priority,
)


class GATWorkerROISamplingPriorityTests(unittest.TestCase):
    def test_builds_cell_gaps_and_filters_existing_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            roi_rows = [
                {
                    "name": "apollo15_20km_random_wave_randomtw_tasks020_01_seed61000_ctx_a_1_2_3",
                    "instance": (
                        "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/"
                        "apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json"
                    ),
                    "expected_context_hash": "ctx-a",
                    "target_sequence": [1, 2, 3],
                    "roi_class": "positive_primal_roi",
                    "primal_improvement": 7.5,
                },
                {
                    "name": "apollo15_20km_random_wave_randomtw_tasks020_02_seed61102_ctx_b_4_5",
                    "instance": (
                        "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/"
                        "apollo15_20km_random-wave_randomtw_tasks020_02_seed61102_logical_graph.json"
                    ),
                    "expected_context_hash": "ctx-b",
                    "target_sequence": [4, 5],
                    "roi_class": "no_observed_roi",
                    "primal_improvement": 0.0,
                },
                {
                    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_ctx_c_6_8_12",
                    "instance": (
                        "BPC_future/logical_graph/tasks_020/greedy-anchor/"
                        "tranquillitatis_balmer_like_20km/"
                        "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json"
                    ),
                    "expected_context_hash": "ctx-c",
                    "target_sequence": [6, 8, 12],
                    "roi_class": "positive_primal_roi",
                    "primal_improvement": 68.0,
                },
            ]
            roi_jsonl = tmp / "roi.jsonl"
            roi_jsonl.write_text(
                "\n".join(json.dumps(row, sort_keys=True) for row in roi_rows) + "\n",
                encoding="utf-8",
            )
            candidate_payload = {
                "candidates": [
                    {
                        "name": "existing",
                        "instance": roi_rows[0]["instance"],
                        "expected_context_hash": "ctx-a",
                        "target_sequence": [1, 2, 3],
                        "decision_name": "HIGH_PRIORITY",
                        "decision_probability": 0.95,
                        "best_true_reduced_cost": -3.0,
                        "target_support_changing_proxy": True,
                        "target_task_set_new": True,
                    },
                    {
                        "name": "new_random_wave_apollo_candidate",
                        "instance": roi_rows[1]["instance"],
                        "expected_context_hash": "ctx-new",
                        "true_dual_hash": "dual-new",
                        "cut_hash": "cut-new",
                        "branch_hash": "branch-new",
                        "forbidden_signature_hash": "forbidden-new",
                        "active_hash_before": "active-new",
                        "pool_signature_hash": "pool-signature-new",
                        "pool_task_set_hash": "pool-task-new",
                        "target_sequence": [7, 8],
                        "target_arc_option_sequence": ["0->7:a", "7->8:a", "8->0:a"],
                        "decision_name": "HIGH_PRIORITY",
                        "decision_probability": 0.75,
                        "best_true_reduced_cost": -2.0,
                        "target_support_changing_proxy": True,
                        "target_task_set_new": True,
                    },
                    {
                        "name": "new_random_wave_apollo_candidate_2",
                        "instance": roi_rows[1]["instance"],
                        "expected_context_hash": "ctx-new-2",
                        "true_dual_hash": "dual-new-2",
                        "cut_hash": "cut-new-2",
                        "branch_hash": "branch-new-2",
                        "forbidden_signature_hash": "forbidden-new-2",
                        "active_hash_before": "active-new-2",
                        "pool_signature_hash": "pool-signature-new-2",
                        "pool_task_set_hash": "pool-task-new-2",
                        "target_sequence": [7, 9],
                        "target_arc_option_sequence": ["0->7:a", "7->9:a", "9->0:a"],
                        "decision_name": "HIGH_PRIORITY",
                        "decision_probability": 0.7,
                        "best_true_reduced_cost": -1.5,
                        "target_support_changing_proxy": True,
                        "target_task_set_new": True,
                    },
                    {
                        "name": "new_greedy_tranq_candidate",
                        "instance": roi_rows[2]["instance"],
                        "expected_context_hash": "ctx-d",
                        "target_sequence": [6, 2, 9],
                        "decision_name": "HIGH_PRIORITY",
                        "decision_probability": 0.7,
                        "best_true_reduced_cost": -1.0,
                        "target_support_changing_proxy": True,
                        "target_task_set_new": True,
                    },
                    {
                        "name": "small_scale_candidate",
                        "instance": (
                            "BPC_future/logical_graph/tasks_005/random-wave/apollo15_20km/"
                            "apollo15_20km_random-wave_randomtw_tasks005_01_seed146000_logical_graph.json"
                        ),
                        "expected_context_hash": "ctx-small",
                        "target_sequence": [1],
                        "decision_name": "HIGH_PRIORITY",
                        "decision_probability": 0.99,
                        "best_true_reduced_cost": -4.0,
                        "target_support_changing_proxy": True,
                        "target_task_set_new": True,
                    },
                ]
            }
            candidates = tmp / "candidates.json"
            candidates.write_text(json.dumps(candidate_payload), encoding="utf-8")

            summary = build_sampling_priority(
                roi_jsonl=roi_jsonl,
                candidate_files=(candidates,),
                output_dir=tmp / "priority",
                report=tmp / "priority.md",
                min_positive_per_cell=2,
                min_negative_per_cell=2,
                max_recommendations=8,
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertFalse(summary["runs_bpc_or_pricing"])
            self.assertFalse(summary["official_bound_effect"])
            self.assertFalse(summary["production_ready"])
            self.assertEqual(summary["row_count"], 3)
            self.assertEqual(summary["candidate_count"], 4)
            self.assertEqual(summary["roi_class_counts"]["positive_primal_roi"], 2)
            self.assertTrue(summary["sample_gaps"])
            self.assertTrue(summary["recommendations"])
            self.assertTrue(
                all(not item["existing_roi_target"] for item in summary["recommendations"])
            )
            self.assertIn(
                "random-wave|apollo15_20km",
                summary["family_region_cells"],
            )
            self.assertTrue((tmp / "priority" / "recommendations.json").exists())
            self.assertTrue((tmp / "priority" / "recommended_candidates.json").exists())
            recommended_candidates = json.loads(
                (tmp / "priority" / "recommended_candidates.json").read_text(encoding="utf-8")
            )["candidates"]
            random_wave = next(
                item for item in recommended_candidates if item["name"] == "new_random_wave_apollo_candidate"
            )
            self.assertEqual(random_wave["true_dual_hash"], "dual-new")
            self.assertEqual(random_wave["cut_hash"], "cut-new")
            self.assertEqual(random_wave["target_arc_option_sequence"], ["0->7:a", "7->8:a", "8->0:a"])
            self.assertTrue((tmp / "priority.md").exists())

            task20_only = build_sampling_priority(
                roi_jsonl=roi_jsonl,
                candidate_files=(candidates,),
                output_dir=tmp / "priority_task20",
                report=tmp / "priority_task20.md",
                min_positive_per_cell=1,
                min_negative_per_cell=1,
                max_recommendations=8,
                candidate_task_counts=(20,),
            )
            self.assertEqual(task20_only["candidate_task_counts"], [20])
            self.assertTrue(task20_only["recommendations"])
            self.assertTrue(
                all(item["instance_task_count"] == 20 for item in task20_only["recommendations"])
            )

            one_per_cell = build_sampling_priority(
                roi_jsonl=roi_jsonl,
                candidate_files=(candidates,),
                output_dir=tmp / "priority_one_per_cell",
                report=tmp / "priority_one_per_cell.md",
                min_positive_per_cell=1,
                min_negative_per_cell=1,
                max_recommendations=8,
                max_per_cell=1,
                candidate_task_counts=(20,),
            )
            cell_counts: dict[str, int] = {}
            for item in one_per_cell["recommendations"]:
                cell_counts[item["cell"]] = cell_counts.get(item["cell"], 0) + 1
                self.assertIn("recommendation_bucket", item)
            self.assertTrue(cell_counts)
            self.assertTrue(all(count <= 1 for count in cell_counts.values()))


if __name__ == "__main__":
    unittest.main()
