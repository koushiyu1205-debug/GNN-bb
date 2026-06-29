from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.apply_gat_branch_score_proofrisk_overlay import apply_overlay


class GATBranchScoreProofRiskOverlayTests(unittest.TestCase):
    def test_overlay_boosts_positive_suppresses_negative_and_marks_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            positive_instance = tmp_path / "positive.json"
            negative_instance = tmp_path / "negative.json"
            neutral_instance = tmp_path / "neutral.json"
            timeout_instance = (
                "BPC_future/logical_graph/tasks_020/greedy-anchor/demo/"
                "demo_randomtw_tasks020_01_seed60000_logical_graph.json"
            )
            paired_probe_instance = (
                "BPC_future/logical_graph/tasks_020/sector-wave/demo/"
                "demo_randomtw_tasks020_09_seed61817_logical_graph.json"
            )
            positive_key = "node:0:depth:0:1,2"
            negative_key = "node:0:depth:0:1,3"
            neutral_key = "node:0:depth:0:2,3"
            timeout_key = "node:0:depth:0:4,5"
            paired_probe_key = "node:0:depth:0:5,18"
            rows_path = tmp_path / "rows.json"
            rows_path.write_text(
                json.dumps(
                    [
                        _row(positive_instance, positive_key, 0.20),
                        _row(negative_instance, negative_key, 0.80),
                        _row(neutral_instance, neutral_key, 0.40),
                        _row(Path(timeout_instance), timeout_key, 0.72),
                        _row(Path(paired_probe_instance), paired_probe_key, 0.73),
                    ],
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            analysis_path = tmp_path / "analysis_summary.json"
            analysis_path.write_text(
                json.dumps(
                    {
                        "items": [
                            {
                                "instance": str(positive_instance),
                                "root_changed": True,
                                "root_selected_pair": [2, 1],
                                "baseline_status": "OPTIMAL",
                                "status": "OPTIMAL",
                                "baseline_wall": 280.0,
                                "wall": 150.0,
                            },
                            {
                                "instance": str(negative_instance),
                                "root_changed": True,
                                "root_selected_pair": [1, 3],
                                "baseline_status": "EXTERNAL_TIME_LIMIT",
                                "status": "EXTERNAL_TIME_LIMIT",
                                "baseline_wall": 600.0,
                                "wall": 600.0,
                            },
                        ],
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            timeout_path = tmp_path / "root_timeout_hard_negative_rows.jsonl"
            timeout_path.write_text(
                json.dumps(
                    {
                        "schema_version": "journey_branch_root_timeout_hard_negative_v1",
                        "instance": Path(timeout_instance).name,
                        "log_file": f"some/results/logs/{timeout_instance}.jsonl",
                        "node_id": 0,
                        "depth": 0,
                        "selected_pair": [5, 4],
                        "selected_score": 0.72,
                        "selected_pair_changed": True,
                        "baseline_status": "EXTERNAL_TIME_LIMIT",
                        "baseline_wall_time": 600.0,
                        "alternative_status": "EXTERNAL_TIME_LIMIT",
                        "alternative_wall_time": 600.0,
                        "label_type": "root_score_timeout_no_effect_hard_negative",
                        "y_branch_score_hard_negative": 1.0,
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            paired_probe_path = tmp_path / "paired_probe_rows.jsonl"
            paired_probe_path.write_text(
                json.dumps(
                    {
                        "schema_version": "journey_paired_probe_entry_v1",
                        "pair_role": "alternative",
                        "paired_label_type": "hard_negative_proxy",
                        "forced_pair": [18, 5],
                        "source_node_id": 0,
                        "source_depth": 0,
                        "instance": paired_probe_instance,
                        "status": "TIME_LIMIT",
                        "wall_time": 102.90111,
                        "paired_wall_time_gain": -9.259593,
                        "paired_child_cb_retry_gain": 0.0,
                        "child_fathomed_count": 0.0,
                        "child_proof_cpu": 62.143576,
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

            output_dir = tmp_path / "out"
            summary = apply_overlay(
                base_score_rows=rows_path,
                analyses=[analysis_path],
                timeout_evidence=[timeout_path],
                paired_probe_evidence=[paired_probe_path],
                output_dir=output_dir,
                report=tmp_path / "report.md",
                boost_score=0.68,
                suppress_score=0.05,
                min_wall_improvement=30.0,
            )

            self.assertTrue(summary["diagnostic_only"])
            self.assertFalse(summary["runs_bpc_or_pricing"])
            self.assertFalse(summary["official_bound_effect"])
            self.assertFalse(summary["certificate_effect"])
            self.assertFalse(summary["production_ready"])
            self.assertEqual(
                summary["overlay_counts"],
                {
                    "boost_positive": 1,
                    "suppress_negative": 1,
                    "suppress_paired_probe_hard_negative": 1,
                    "suppress_timeout_hard_negative": 1,
                },
            )
            self.assertEqual(summary["timeout_negative_overlay_keys"], 2)
            self.assertEqual(summary["paired_probe_negative_overlay_keys"], 2)
            rows = json.loads((output_dir / "journey_branch_score_rows.json").read_text(encoding="utf-8"))
            by_key = {row["key"]: row for row in rows}
            self.assertEqual(float(by_key[positive_key]["score"]), 0.68)
            self.assertEqual(by_key[positive_key]["proofrisk_overlay"], "boost_positive")
            self.assertEqual(float(by_key[negative_key]["score"]), 0.05)
            self.assertEqual(by_key[negative_key]["proofrisk_overlay"], "suppress_changed_nonoptimal")
            self.assertEqual(float(by_key[neutral_key]["score"]), 0.40)
            self.assertNotIn("proofrisk_overlay", by_key[neutral_key])
            self.assertEqual(float(by_key[timeout_key]["score"]), 0.05)
            self.assertEqual(by_key[timeout_key]["proofrisk_overlay"], "suppress_timeout_hard_negative")
            self.assertEqual(by_key[timeout_key]["proofrisk_overlay_evidence_kind"], "timeout_hard_negative")
            self.assertEqual(float(by_key[paired_probe_key]["score"]), 0.05)
            self.assertEqual(
                by_key[paired_probe_key]["proofrisk_overlay"],
                "suppress_paired_probe_hard_negative",
            )
            self.assertEqual(
                by_key[paired_probe_key]["proofrisk_overlay_evidence_kind"],
                "paired_probe_hard_negative",
            )


def _row(instance: Path, key: str, score: float) -> dict[str, object]:
    return {
        "instance_key": str(instance),
        "scoped_key": f"{instance}|{key}",
        "key": key,
        "score": score,
    }


if __name__ == "__main__":
    unittest.main()
