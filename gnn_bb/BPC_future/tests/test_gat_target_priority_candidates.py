from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from BPC_future.scripts.build_gat_target_priority_candidates import extract_candidates
from BPC_future.scripts.build_gat_target_priority_worker_ab_runbook import build_runbook


def _write_capture(path: Path, *, graph_path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    events = [
        {
            "event": "journey_counterfactual_replay_capture",
            "context_hash": "ctx-safe",
            "cg_iter": 8,
            "instance": "apollo20",
            "instance_path": str(graph_path),
            "returned_journey_count": 2,
            "returned_journeys": [
                {
                    "true_reduced_cost": -1.0,
                    "sequence": [[3]],
                    "signature": [
                        [[3], ["0->3:low_risk:2", "3->0:low_risk:2"], 0.0]
                    ],
                },
                {
                    "true_reduced_cost": -4.0,
                    "sequence": [[20, 17, 16]],
                    "signature": [
                        [
                            [20, 17, 16],
                            [
                                "0->20:low_risk:2",
                                "20->17:low_risk:2",
                                "17->16:low_risk:2",
                                "16->0:low_risk:2",
                            ],
                            0.0,
                        ]
                    ],
                },
            ],
        },
        {
            "event": "journey_counterfactual_replay_capture",
            "context_hash": "ctx-delay",
            "cg_iter": 9,
            "instance": "apollo20",
            "instance_path": str(graph_path),
            "returned_journey_count": 1,
            "returned_journeys": [
                {
                    "true_reduced_cost": -2.0,
                    "sequence": [[4]],
                    "signature": [
                        [[4], ["0->4:low_risk:2", "4->0:low_risk:2"], 0.0]
                    ],
                }
            ],
        },
    ]
    path.write_text(
        "\n".join(json.dumps(event, sort_keys=True) for event in events) + "\n",
        encoding="utf-8",
    )


class GATTargetPriorityCandidateTests(unittest.TestCase):
    def test_extracts_high_priority_best_negative_target_from_capture_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            graph_path = tmp / "tasks_020" / "sector-wave" / "apollo15_20km" / "apollo.json"
            graph_path.parent.mkdir(parents=True, exist_ok=True)
            graph_path.write_text("{}", encoding="utf-8")
            capture = tmp / "capture.jsonl"
            _write_capture(capture, graph_path=graph_path)
            manifest = tmp / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "samples": [
                            {
                                "source_file": str(capture),
                                "context_hash": "ctx-safe",
                                "instance": "apollo20",
                                "row_index": 0,
                                "candidate_count": 2,
                            },
                            {
                                "source_file": str(capture),
                                "context_hash": "ctx-delay",
                                "instance": "apollo20",
                                "row_index": 1,
                                "candidate_count": 1,
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )
            decisions = tmp / "decisions.jsonl"
            decisions.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "decision_name": "HIGH_PRIORITY",
                                "decision_reason": "high_priority",
                                "probability": 0.91,
                            },
                            sort_keys=True,
                        ),
                        json.dumps(
                            {
                                "decision_name": "DELAY_QUEUE",
                                "decision_reason": "delay_neighbor_unsafe_fraction",
                                "probability": 0.8,
                            },
                            sort_keys=True,
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            summary = extract_candidates(
                decision_records_path=decisions,
                validation_manifest=manifest,
                output_dir=tmp / "out",
                report=tmp / "report.md",
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertEqual(summary["candidate_count"], 1)
            candidate = summary["candidates"][0]
            self.assertEqual(candidate["expected_context_hash"], "ctx-safe")
            self.assertEqual(candidate["target_sequence"], [20, 17, 16])
            self.assertEqual(
                candidate["target_arc_option_sequence"],
                [
                    "0->20:low_risk:2",
                    "20->17:low_risk:2",
                    "17->16:low_risk:2",
                    "16->0:low_risk:2",
                ],
            )
            self.assertEqual(candidate["best_true_reduced_cost"], -4.0)
            self.assertEqual(summary["skipped_counts"]["decision_not_selected"], 1)
            self.assertTrue((tmp / "out" / "candidates.json").exists())
            self.assertTrue((tmp / "report.md").exists())

    def test_extracted_candidates_feed_quoted_worker_runbook(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            logical_root = tmp / "logical_graph"
            for scale in (5, 10):
                for region in ("apollo15_20km", "tranquillitatis_balmer_like_20km"):
                    path = (
                        logical_root
                        / f"tasks_{scale:03d}"
                        / "sector-wave"
                        / region
                        / f"{region}_sector-wave_randomtw_tasks{scale:03d}_01_seed{scale}.json"
                    )
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text("{}", encoding="utf-8")
            graph_path = (
                logical_root
                / "tasks_020"
                / "sector-wave"
                / "apollo15_20km"
                / "apollo20.json"
            )
            graph_path.parent.mkdir(parents=True, exist_ok=True)
            graph_path.write_text("{}", encoding="utf-8")
            capture = tmp / "capture.jsonl"
            _write_capture(capture, graph_path=graph_path)
            manifest = tmp / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "samples": [
                            {
                                "source_file": str(capture),
                                "context_hash": "ctx-safe",
                                "instance": "apollo20",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            decisions = tmp / "decisions.jsonl"
            decisions.write_text(
                json.dumps(
                    {
                        "decision_name": "HIGH_PRIORITY",
                        "decision_reason": "high_priority",
                        "probability": 0.91,
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            candidate_summary = extract_candidates(
                decision_records_path=decisions,
                validation_manifest=manifest,
                output_dir=tmp / "candidates",
                report=tmp / "candidate_report.md",
            )
            self.assertTrue(candidate_summary["all_checks_pass"])

            runbook = build_runbook(
                logical_graph_root=logical_root,
                candidates_file=tmp / "candidates" / "candidates.json",
                output_dir=tmp / "runbook",
                report=tmp / "runbook.md",
            )

            worker = {
                item["command_type"]: item["command"] for item in runbook["commands"]
            }[
                f"task020_{candidate_summary['candidates'][0]['name']}_target_priority_worker"
            ]
            self.assertIn(
                "--set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=",
                worker,
            )
            self.assertIn("journey_sharded_pulse_hidden_negative_worker_expected_context_hash=ctx-safe", worker)
            self.assertFalse(runbook["certificate_ready"])
            self.assertFalse(runbook["default_enabled"])


if __name__ == "__main__":
    unittest.main()
