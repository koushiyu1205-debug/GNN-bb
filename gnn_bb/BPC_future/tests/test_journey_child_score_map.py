from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.build_journey_child_score_map import build_child_score_map


class JourneyChildScoreMapTests(unittest.TestCase):
    def test_builds_child_score_map_from_started_child_probe_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            probe_dir = tmp_path / "probe"
            probe_dir.mkdir()
            rows = [
                _child_probe_row(
                    pair=[2, 9],
                    kind="same_vehicle",
                    fathomed=True,
                    corrected_gain=3.0,
                    retries=4.0,
                    proof_cpu=40.0,
                    negative_events=9.0,
                ),
                _child_probe_row(
                    pair=[2, 9],
                    kind="separate_vehicle",
                    fathomed=False,
                    corrected_gain=0.0,
                    retries=1.0,
                    proof_cpu=12.0,
                    negative_events=7.0,
                ),
                _child_probe_row(
                    pair=[4, 5],
                    kind="same_vehicle",
                    child_started=False,
                    corrected_gain=10.0,
                ),
            ]
            (probe_dir / "child_probe_rows.jsonl").write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
                encoding="utf-8",
            )

            summary = build_child_score_map(
                [probe_dir],
                tmp_path / "out",
                tmp_path / "report.md",
            )

            self.assertTrue(summary["diagnostic_only"])
            self.assertFalse(summary["runs_bpc_or_pricing"])
            self.assertFalse(summary["official_bound_effect"])
            self.assertFalse(summary["production_ready"])
            self.assertEqual(summary["raw_child_probe_row_count"], 3)
            self.assertEqual(summary["child_probe_row_count"], 2)
            self.assertEqual(summary["filtered_out_child_probe_row_count"], 1)
            self.assertEqual(summary["child_score_map_entry_count"], 2)
            self.assertEqual(summary["solver_child_priority_mode"], "child_score")

            score_map = json.loads((tmp_path / "out" / "journey_child_score_map.json").read_text())
            self.assertIn("node:0:depth:0:2,9:same_vehicle", score_map)
            self.assertIn("node:0:depth:0:2,9:separate_vehicle", score_map)
            self.assertGreater(
                score_map["node:0:depth:0:2,9:same_vehicle"],
                score_map["node:0:depth:0:2,9:separate_vehicle"],
            )
            report = (tmp_path / "report.md").read_text(encoding="utf-8")
            self.assertIn("journey_child_priority_mode=child_score", report)

    def test_pair_scope_aggregates_duplicate_child_kind_scores(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            child_file = tmp_path / "child_probe_rows.jsonl"
            rows = [
                _child_probe_row(pair=[1, 3], kind="same_vehicle", corrected_gain=1.0),
                _child_probe_row(pair=[1, 3], kind="same_vehicle", corrected_gain=3.0),
            ]
            child_file.write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
                encoding="utf-8",
            )

            summary = build_child_score_map(
                [child_file],
                tmp_path / "out",
                tmp_path / "report.md",
                key_scope="pair",
                right_censored_penalty=0.0,
                proof_cpu_scale=1000.0,
            )

            self.assertEqual(summary["child_probe_row_count"], 2)
            score_rows = json.loads((tmp_path / "out" / "journey_child_score_rows.json").read_text())
            self.assertEqual(len(score_rows), 1)
            self.assertEqual(score_rows[0]["key"], "1,3:same_vehicle")
            self.assertEqual(score_rows[0]["observation_count"], 2)


def _child_probe_row(
    *,
    pair: list[int],
    kind: str,
    branch_node_id: int = 0,
    branch_depth: int = 0,
    child_started: bool = True,
    complete: bool = False,
    right_censored: bool = True,
    fathomed: bool = False,
    corrected_gain: float = 0.0,
    retries: float = 0.0,
    proof_cpu: float = 0.0,
    negative_events: float = 0.0,
) -> dict[str, object]:
    return {
        "schema_version": "journey_branch_child_probe_row_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "log_file": "logs/BPC_future/logical_graph/tasks_020/demo/demo.json.jsonl",
        "right_censored": bool(right_censored),
        "label_observation_complete": bool(complete),
        "branch_node_id": int(branch_node_id),
        "branch_depth": int(branch_depth),
        "task_i": int(pair[0]),
        "task_j": int(pair[1]),
        "forced_pair": list(pair),
        "child_constraint": f"RF({int(pair[0])},{int(pair[1])})={kind}",
        "child_constraint_kind": kind,
        "child_started": bool(child_started),
        "child_labels": {
            "child_completion_bound_retry_count": float(retries),
            "child_exact_pricing_event_count": 1.0,
            "child_fathomed": 1.0 if fathomed else 0.0,
            "child_max_corrected_bound_gain": float(corrected_gain),
            "child_negative_pricing_event_count": float(negative_events),
            "child_proof_cpu": float(proof_cpu),
        },
    }


if __name__ == "__main__":
    unittest.main()
