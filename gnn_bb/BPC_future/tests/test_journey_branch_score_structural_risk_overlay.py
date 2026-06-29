from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.apply_journey_branch_score_structural_risk_overlay import (
    apply_structural_overlay,
)


class JourneyBranchScoreStructuralRiskOverlayTests(unittest.TestCase):
    def test_exact_deep_structural_and_root_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            instance = (
                "BPC_future/logical_graph/tasks_020/greedy-anchor/demo_site/"
                "demo_randomtw_tasks020_01_seed61000_logical_graph.json"
            )
            sibling_instance = (
                "BPC_future/logical_graph/tasks_020/greedy-anchor/demo_site/"
                "demo_randomtw_tasks020_02_seed61001_logical_graph.json"
            )
            other_instance = (
                "BPC_future/logical_graph/tasks_020/sector-wave/demo_site/"
                "demo_randomtw_tasks020_03_seed61002_logical_graph.json"
            )
            rows_path = tmp_path / "rows.json"
            rows = [
                _score_row(instance, "node:3:depth:3:4,5", [4, 5], 3, 0.91),
                _score_row(sibling_instance, "node:9:depth:5:4,5", [4, 5], 5, 0.90),
                _score_row(sibling_instance, "node:0:depth:0:4,5", [4, 5], 0, 0.92),
                _score_row(sibling_instance, "node:10:depth:5:7,8", [7, 8], 5, 0.90),
                _score_row(other_instance, "node:10:depth:5:7,8", [7, 8], 5, 0.90),
            ]
            rows_path.write_text(json.dumps(rows, sort_keys=True), encoding="utf-8")
            evidence_path = tmp_path / "score_timeout_hard_negative_rows.jsonl"
            evidence_rows = [
                _evidence_row(instance, "node:3:depth:3:4,5", [4, 5], 3, 0.78),
                _evidence_row(instance, "node:4:depth:4:4,5", [4, 5], 4, 0.79),
                _evidence_row(instance, "node:5:depth:5:9,10", [9, 10], 5, 0.80),
                _evidence_row(instance, "node:6:depth:6:11,12", [11, 12], 6, 0.81),
            ]
            evidence_path.write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in evidence_rows),
                encoding="utf-8",
            )

            summary = apply_structural_overlay(
                base_score_rows=rows_path,
                evidence_paths=[evidence_path],
                output_dir=tmp_path / "out",
                report=tmp_path / "report.md",
                exact_suppress_score=0.03,
                repeated_pair_cap_score=0.35,
                high_depth_cap_score=0.55,
                family_retry_cap_score=0.65,
                structural_min_depth=4,
                repeated_pair_min_count=2,
                family_min_count=2,
            )

            self.assertTrue(summary["diagnostic_only"])
            self.assertFalse(summary["runs_bpc_or_pricing"])
            self.assertFalse(summary["official_bound_effect"])
            self.assertFalse(summary["certificate_effect"])
            self.assertEqual(summary["evidence_row_count"], 4)
            self.assertEqual(summary["overlay_counts"]["exact_timeout_hard_negative"], 1)
            self.assertGreaterEqual(summary["overlay_counts"]["repeated_failed_pair"], 1)
            output_rows = json.loads(
                (tmp_path / "out" / "journey_branch_score_rows.json").read_text(encoding="utf-8")
            )
            by_scoped = {row["scoped_key"]: row for row in output_rows}
            exact = by_scoped[f"{instance}|node:3:depth:3:4,5"]
            repeated = by_scoped[f"{sibling_instance}|node:9:depth:5:4,5"]
            root = by_scoped[f"{sibling_instance}|node:0:depth:0:4,5"]
            high_depth = by_scoped[f"{sibling_instance}|node:10:depth:5:7,8"]
            other = by_scoped[f"{other_instance}|node:10:depth:5:7,8"]
            self.assertEqual(float(exact["score"]), 0.03)
            self.assertIn("exact_timeout_hard_negative", exact["structural_proof_tail_reasons"])
            self.assertEqual(float(repeated["score"]), 0.35)
            self.assertIn("repeated_failed_pair:4,5", repeated["structural_proof_tail_reasons"])
            self.assertEqual(float(root["score"]), 0.92)
            self.assertNotIn("structural_proof_tail_overlay", root)
            self.assertEqual(float(high_depth["score"]), 0.55)
            self.assertIn("family_deep_high_score:greedy-anchor", high_depth["structural_proof_tail_reasons"])
            self.assertEqual(float(other["score"]), 0.90)
            self.assertNotIn("structural_proof_tail_overlay", other)


def _score_row(
    instance: str,
    key: str,
    pair: list[int],
    depth: int,
    score: float,
) -> dict[str, object]:
    return {
        "schema_version": "gat_branch_action_score_row_v1",
        "instance": instance,
        "instance_key": instance,
        "scoped_key": f"{instance}|{key}",
        "key": key,
        "node_id": 0,
        "depth": depth,
        "pair": pair,
        "score": score,
        "branch_score": score,
        "gat_score": score,
        "predicted_score": score,
        "diagnostic_only": True,
        "official_bound_effect": False,
        "certificate_effect": False,
    }


def _evidence_row(
    instance: str,
    key: str,
    pair: list[int],
    depth: int,
    score: float,
) -> dict[str, object]:
    node_text = key.split(":")[1]
    return {
        "schema_version": "journey_branch_score_failure_hard_negative_v1",
        "instance": instance,
        "log_file": f"some/results/logs/{instance}.jsonl",
        "node_id": int(node_text),
        "depth": depth,
        "selected_pair": pair,
        "selected_score": score,
        "selected_pair_changed": True,
        "alternative_status": "EXTERNAL_TIME_LIMIT",
        "alternative_wall_time": 600.0,
        "alternative_gap_available": True,
        "run_completion_bound_retry_count": 40,
        "run_ordinary_retry_count": 1,
        "source_experiment": "unit",
        "y_branch_score_hard_negative": 1.0,
    }


if __name__ == "__main__":
    unittest.main()
