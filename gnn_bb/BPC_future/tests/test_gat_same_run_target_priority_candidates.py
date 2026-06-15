from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from BPC_future.scripts.build_gat_same_run_target_priority_candidates import (
    REQUIRED_CAPTURE_CONTEXT_FIELDS,
    extract_candidates,
)


def _capture_event(
    *,
    context_hash: str,
    instance_path: Path,
    true_rc: float = -3.5,
) -> dict[str, object]:
    return {
        "event": "journey_counterfactual_replay_capture",
        "context_hash": context_hash,
        "true_dual_hash": "dual-hash",
        "cut_hash": "cut-hash",
        "branch_hash": "branch-hash",
        "forbidden_signature_hash": "forbidden-hash",
        "active_hash_before": "active-hash",
        "pool_signature_hash": "pool-signature-hash",
        "pool_task_set_hash": "pool-task-set-hash",
        "instance": "toy_instance",
        "instance_path": str(instance_path),
        "cg_iter": 4,
        "pricing_kind": "exact",
        "returned_journey_count": 1,
        "returned_journeys": [
            {
                "id": "j0",
                "task_set": [1, 2],
                "sequence": [[1, 2]],
                "signature": [
                    [
                        [1, 2],
                        ["0->1:low_risk:0", "1->2:low_risk:0", "2->0:low_risk:0"],
                        0.0,
                    ]
                ],
                "true_reduced_cost": true_rc,
            }
        ],
    }


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )


class GATSameRunTargetPriorityCandidatesTests(unittest.TestCase):
    def test_extracts_high_priority_same_context_negative_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            instance = tmp / "toy_logical_graph.json"
            instance.write_text("{}", encoding="utf-8")
            capture = tmp / "capture.jsonl"
            _write_jsonl(capture, [_capture_event(context_hash="ctx-hit", instance_path=instance)])
            decisions = tmp / "decisions.jsonl"
            _write_jsonl(
                decisions,
                [
                    {
                        "decision": 1,
                        "decision_reason": "high_priority",
                        "probability": 0.95,
                        "context_hash": "ctx-hit",
                        "source_file": str(capture),
                        "sample_path": "samples/sample_000000.pt",
                        "row_index": 0,
                    }
                ],
            )

            summary = extract_candidates(
                decision_records_path=decisions,
                output_dir=tmp / "out",
                report=tmp / "report.md",
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertEqual(summary["candidate_count"], 1)
            candidate = summary["candidates"][0]
            self.assertEqual(candidate["expected_context_hash"], "ctx-hit")
            self.assertEqual(candidate["target_sequence"], [1, 2])
            self.assertEqual(candidate["target_priority_sequence"], [1, 2])
            self.assertEqual(
                candidate["target_arc_option_sequence"],
                ["0->1:low_risk:0", "1->2:low_risk:0", "2->0:low_risk:0"],
            )
            self.assertEqual(
                candidate["target_sortie_traces"],
                [
                    {
                        "sequence": [1, 2],
                        "start_time": 0.0,
                        "arc_option_sequence": [
                            "0->1:low_risk:0",
                            "1->2:low_risk:0",
                            "2->0:low_risk:0",
                        ],
                    }
                ],
            )
            self.assertLess(candidate["best_true_reduced_cost"], 0.0)
            self.assertEqual(candidate["instance_family"], "unknown")
            self.assertEqual(candidate["instance_region"], "unknown")
            self.assertIsNone(candidate["instance_task_count"])
            self.assertFalse(candidate["training_label_allowed_before_worker_reachability"])
            self.assertTrue(candidate["requires_worker_target_causal_match"])
            self.assertEqual(
                set(summary["required_capture_context_fields"]),
                set(REQUIRED_CAPTURE_CONTEXT_FIELDS),
            )
            self.assertFalse(summary["production_ready"])
            self.assertFalse(summary["certificate_ready"])
            self.assertFalse(summary["official_bound_effect"])
            self.assertTrue((tmp / "out" / "candidates.json").exists())
            self.assertTrue((tmp / "report.md").exists())

    def test_delay_queue_or_nonnegative_rows_do_not_become_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            instance = tmp / "toy_logical_graph.json"
            instance.write_text("{}", encoding="utf-8")
            capture = tmp / "capture.jsonl"
            _write_jsonl(
                capture,
                [
                    _capture_event(
                        context_hash="ctx-delay",
                        instance_path=instance,
                        true_rc=-2.0,
                    ),
                    _capture_event(
                        context_hash="ctx-nonnegative",
                        instance_path=instance,
                        true_rc=0.25,
                    ),
                ],
            )
            decisions = tmp / "decisions.jsonl"
            _write_jsonl(
                decisions,
                [
                    {
                        "decision": 0,
                        "decision_reason": "below_threshold_delay_queue",
                        "probability": 0.4,
                        "context_hash": "ctx-delay",
                        "source_file": str(capture),
                    },
                    {
                        "decision": 1,
                        "decision_reason": "high_priority",
                        "probability": 0.9,
                        "context_hash": "ctx-nonnegative",
                        "source_file": str(capture),
                    },
                ],
            )

            summary = extract_candidates(
                decision_records_path=decisions,
                output_dir=tmp / "out",
                report=tmp / "report.md",
            )

            self.assertFalse(summary["all_checks_pass"])
            self.assertEqual(summary["candidate_count"], 0)
            self.assertEqual(summary["skipped_counts"]["decision_not_high_priority"], 1)
            self.assertEqual(
                summary["skipped_counts"]["no_negative_journey_with_materialized_signature"],
                1,
            )
            self.assertFalse(
                summary["candidate_policy"]["permanent_negative_filter_allowed"]
            )

    def test_delay_queue_only_sampling_extracts_delayed_negative_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            instance = tmp / "toy_logical_graph.json"
            instance.write_text("{}", encoding="utf-8")
            capture = tmp / "capture.jsonl"
            _write_jsonl(capture, [_capture_event(context_hash="ctx-delay", instance_path=instance)])
            decisions = tmp / "decisions.jsonl"
            _write_jsonl(
                decisions,
                [
                    {
                        "decision": 1,
                        "decision_reason": "high_priority",
                        "probability": 0.91,
                        "context_hash": "ctx-high",
                        "source_file": str(capture),
                        "sample_path": "samples/sample_000001.pt",
                        "row_index": 0,
                    },
                    {
                        "decision": 0,
                        "decision_reason": "below_threshold_delay_queue",
                        "probability": 0.74,
                        "context_hash": "ctx-delay",
                        "source_file": str(capture),
                        "sample_path": "samples/sample_000002.pt",
                        "row_index": 0,
                    }
                ],
            )

            summary = extract_candidates(
                decision_records_path=decisions,
                output_dir=tmp / "out",
                report=tmp / "report.md",
                delay_queue_only=True,
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertFalse(summary["include_delay_queue"])
            self.assertTrue(summary["delay_queue_only"])
            self.assertFalse(summary["all_candidates_high_priority"])
            self.assertTrue(summary["all_candidates_high_or_delay"])
            self.assertEqual(summary["candidate_count"], 1)
            self.assertEqual(summary["candidates"][0]["decision_name"], "DELAY_QUEUE")
            self.assertFalse(
                summary["candidates"][0]["training_label_allowed_before_worker_reachability"]
            )

    def test_extracts_full_multi_sortie_target_traces(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            instance = tmp / "toy_logical_graph.json"
            instance.write_text("{}", encoding="utf-8")
            capture = tmp / "capture.jsonl"
            event = _capture_event(context_hash="ctx-multi", instance_path=instance)
            event["returned_journeys"][0]["task_set"] = [1, 2, 3]
            event["returned_journeys"][0]["sequence"] = [[1, 2], [3]]
            event["returned_journeys"][0]["signature"] = [
                [
                    [1, 2],
                    ["0->1:low_risk:0", "1->2:low_risk:0", "2->0:low_risk:0"],
                    4.0,
                ],
                [[3], ["0->3:low_time:1", "3->0:low_time:1"], 24.0],
            ]
            _write_jsonl(capture, [event])
            decisions = tmp / "decisions.jsonl"
            _write_jsonl(
                decisions,
                [
                    {
                        "decision": 1,
                        "decision_reason": "high_priority",
                        "probability": 0.97,
                        "context_hash": "ctx-multi",
                        "source_file": str(capture),
                        "sample_path": "samples/sample_000001.pt",
                        "row_index": 0,
                    }
                ],
            )

            summary = extract_candidates(
                decision_records_path=decisions,
                output_dir=tmp / "out",
                report=tmp / "report.md",
            )

            self.assertTrue(summary["all_checks_pass"])
            candidate = summary["candidates"][0]
            self.assertEqual(candidate["target_sequence"], [1, 2, 3])
            self.assertEqual(candidate["target_priority_sequence"], [1, 2])
            self.assertEqual(
                candidate["target_arc_option_sequence"],
                ["0->1:low_risk:0", "1->2:low_risk:0", "2->0:low_risk:0"],
            )
            self.assertEqual(
                candidate["target_sortie_traces"],
                [
                    {
                        "sequence": [1, 2],
                        "start_time": 4.0,
                        "arc_option_sequence": [
                            "0->1:low_risk:0",
                            "1->2:low_risk:0",
                            "2->0:low_risk:0",
                        ],
                    },
                    {
                        "sequence": [3],
                        "start_time": 24.0,
                        "arc_option_sequence": ["0->3:low_time:1", "3->0:low_time:1"],
                    },
                ],
            )

    def test_impact_ranking_prefers_new_support_changing_over_most_negative_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            instance = tmp / "toy_logical_graph.json"
            instance.write_text("{}", encoding="utf-8")
            capture = tmp / "capture.jsonl"
            event = _capture_event(context_hash="ctx-impact", instance_path=instance)
            event["active_task_sets"] = [[1, 2]]
            event["pool_task_sets"] = [[1], [2], [1, 2]]
            event["returned_journeys"] = [
                {
                    "id": "replacement",
                    "task_set": [1, 2],
                    "sequence": [[1, 2]],
                    "signature": [
                        [
                            [1, 2],
                            [
                                "0->1:low_risk:0",
                                "1->2:low_risk:0",
                                "2->0:low_risk:0",
                            ],
                            0.0,
                        ]
                    ],
                    "true_reduced_cost": -100.0,
                },
                {
                    "id": "new-support",
                    "task_set": [3, 4],
                    "sequence": [[3, 4]],
                    "signature": [
                        [
                            [3, 4],
                            [
                                "0->3:low_risk:0",
                                "3->4:low_risk:0",
                                "4->0:low_risk:0",
                            ],
                            0.0,
                        ]
                    ],
                    "true_reduced_cost": -1.0,
                },
            ]
            event["returned_journey_count"] = 2
            _write_jsonl(capture, [event])
            decisions = tmp / "decisions.jsonl"
            _write_jsonl(
                decisions,
                [
                    {
                        "decision": 1,
                        "decision_reason": "high_priority",
                        "probability": 0.97,
                        "context_hash": "ctx-impact",
                        "source_file": str(capture),
                    }
                ],
            )

            best_rc_summary = extract_candidates(
                decision_records_path=decisions,
                output_dir=tmp / "best_rc",
                report=tmp / "best_rc.md",
            )
            impact_summary = extract_candidates(
                decision_records_path=decisions,
                output_dir=tmp / "impact",
                report=tmp / "impact.md",
                candidate_ranking="impact",
            )

            self.assertEqual(best_rc_summary["candidates"][0]["target_sequence"], [1, 2])
            self.assertEqual(impact_summary["candidates"][0]["target_sequence"], [3, 4])
            self.assertEqual(
                impact_summary["candidates"][0]["target_impact_bucket"],
                "new_support_changing",
            )
            self.assertTrue(impact_summary["candidates"][0]["target_task_set_new"])
            self.assertTrue(
                impact_summary["candidates"][0]["target_support_changing_proxy"]
            )
            self.assertEqual(
                impact_summary["candidate_impact_bucket_counts"],
                {"new_support_changing": 1},
            )
            self.assertEqual(impact_summary["candidate_new_task_set_count"], 1)

    def test_excludes_existing_roi_targets_by_context_and_target_sequence(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            instance = tmp / "toy_logical_graph.json"
            instance.write_text("{}", encoding="utf-8")
            capture = tmp / "capture.jsonl"
            _write_jsonl(capture, [_capture_event(context_hash="ctx-hit", instance_path=instance)])
            decisions = tmp / "decisions.jsonl"
            _write_jsonl(
                decisions,
                [
                    {
                        "decision": 1,
                        "decision_reason": "high_priority",
                        "probability": 0.95,
                        "context_hash": "ctx-hit",
                        "source_file": str(capture),
                    }
                ],
            )
            existing = tmp / "existing_roi.jsonl"
            _write_jsonl(
                existing,
                [
                    {
                        "expected_context_hash": "ctx-hit",
                        "target_sequence": [1, 2],
                    }
                ],
            )

            summary = extract_candidates(
                decision_records_path=decisions,
                output_dir=tmp / "out",
                report=tmp / "report.md",
                exclude_existing_roi_jsonl=existing,
            )

            self.assertFalse(summary["all_checks_pass"])
            self.assertEqual(summary["candidate_count"], 0)
            self.assertEqual(summary["existing_roi_target_count"], 1)
            self.assertEqual(summary["skipped_counts"]["existing_roi_target"], 1)

    def test_candidate_metadata_and_family_region_filters_target_label_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            greedy_tranq = (
                tmp
                / "BPC_future"
                / "logical_graph"
                / "tasks_020"
                / "greedy-anchor"
                / "tranquillitatis_balmer_like_20km"
                / "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json"
            )
            greedy_tranq_10 = (
                tmp
                / "BPC_future"
                / "logical_graph"
                / "tasks_010"
                / "greedy-anchor"
                / "tranquillitatis_balmer_like_20km"
                / "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks010_02_seed61103_logical_graph.json"
            )
            random_apollo = (
                tmp
                / "BPC_future"
                / "logical_graph"
                / "tasks_020"
                / "random-wave"
                / "apollo15_20km"
                / "apollo15_20km_random-wave_randomtw_tasks020_02_seed61102_logical_graph.json"
            )
            greedy_tranq.parent.mkdir(parents=True, exist_ok=True)
            greedy_tranq_10.parent.mkdir(parents=True, exist_ok=True)
            random_apollo.parent.mkdir(parents=True, exist_ok=True)
            greedy_tranq.write_text("{}", encoding="utf-8")
            greedy_tranq_10.write_text("{}", encoding="utf-8")
            random_apollo.write_text("{}", encoding="utf-8")
            capture = tmp / "capture.jsonl"
            _write_jsonl(
                capture,
                [
                    _capture_event(context_hash="ctx-greedy-tranq", instance_path=greedy_tranq),
                    _capture_event(context_hash="ctx-greedy-tranq-10", instance_path=greedy_tranq_10),
                    _capture_event(context_hash="ctx-random-apollo", instance_path=random_apollo),
                ],
            )
            decisions = tmp / "decisions.jsonl"
            _write_jsonl(
                decisions,
                [
                    {
                        "decision": 1,
                        "decision_reason": "high_priority",
                        "probability": 0.95,
                        "context_hash": "ctx-random-apollo",
                        "source_file": str(capture),
                    },
                    {
                        "decision": 1,
                        "decision_reason": "high_priority",
                        "probability": 0.95,
                        "context_hash": "ctx-greedy-tranq",
                        "source_file": str(capture),
                    },
                    {
                        "decision": 1,
                        "decision_reason": "high_priority",
                        "probability": 0.95,
                        "context_hash": "ctx-greedy-tranq-10",
                        "source_file": str(capture),
                    },
                ],
            )

            summary = extract_candidates(
                decision_records_path=decisions,
                output_dir=tmp / "out",
                report=tmp / "report.md",
                max_candidates=4,
                include_families=("greedy-anchor",),
                include_regions=("tranq",),
                include_ordinals=(2,),
                include_task_counts=(20,),
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertEqual(summary["candidate_count"], 1)
            self.assertEqual(summary["skipped_counts"]["task_count_not_selected"], 1)
            self.assertEqual(summary["skipped_counts"]["family_not_selected"], 1)
            candidate = summary["candidates"][0]
            self.assertEqual(candidate["instance_task_count"], 20)
            self.assertEqual(candidate["instance_family"], "greedy-anchor")
            self.assertEqual(
                candidate["instance_region"],
                "tranquillitatis_balmer_like_20km",
            )
            self.assertEqual(candidate["instance_ordinal"], 2)
            self.assertEqual(summary["include_task_counts"], [20])
            self.assertEqual(summary["candidate_task_count_counts"], {"20": 1})
            self.assertEqual(
                summary["candidate_family_region_counts"],
                {"greedy-anchor|tranquillitatis_balmer_like_20km": 1},
            )


if __name__ == "__main__":
    unittest.main()
