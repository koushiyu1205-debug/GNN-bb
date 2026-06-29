import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.build_journey_tree_replay_score_map import build_tree_replay_score_map


class JourneyTreeReplayScoreMapTests(unittest.TestCase):
    def test_builds_branch_and_child_score_maps_from_branch_tree_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log = root / "logs" / "BPC_future" / "logical_graph" / "tasks_020" / "case.json.jsonl"
            log.parent.mkdir(parents=True)
            events = [
                {
                    "event": "journey_branch",
                    "node_id": 0,
                    "depth": 0,
                    "left": "RF(2,5)=same_vehicle",
                    "right": "RF(2,5)=separate_vehicle",
                    "time": 12.0,
                },
                {
                    "event": "journey_child_queued",
                    "parent_node_id": 0,
                    "child_node_id": 1,
                    "depth": 1,
                    "constraint": "RF(2,5)=same_vehicle",
                },
                {
                    "event": "journey_child_queued",
                    "parent_node_id": 0,
                    "child_node_id": 2,
                    "depth": 1,
                    "constraint": "RF(2,5)=separate_vehicle",
                },
            ]
            log.write_text("".join(json.dumps(event) + "\n" for event in events), encoding="utf-8")

            output_dir = root / "out"
            report = root / "report.md"
            summary = build_tree_replay_score_map(
                [log],
                output_dir,
                report,
                config=Path("BPC_future/configs/moon_trek_20_smoke.yaml"),
                time_limit=600.0,
                candidate_log_top_n=200,
            )

            self.assertEqual(summary["branch_score_row_count"], 1)
            self.assertEqual(summary["child_score_row_count"], 2)
            self.assertFalse(summary["certificate_effect"])
            self.assertFalse(summary["official_bound_effect"])
            branch_rows = json.loads((output_dir / "journey_branch_tree_score_rows.json").read_text())
            child_rows = json.loads((output_dir / "journey_child_tree_score_rows.json").read_text())
            self.assertEqual(branch_rows[0]["pair"], [2, 5])
            self.assertEqual(branch_rows[0]["node_id"], 0)
            self.assertEqual(child_rows[0]["child_constraint_kind"], "same_vehicle")
            self.assertGreater(child_rows[0]["score"], child_rows[1]["score"])
            commands = (output_dir / "commands.sh").read_text(encoding="utf-8")
            self.assertIn("journey_branch_candidate_priority=branch_score_horizon", commands)
            self.assertIn("journey_child_priority_mode=child_score", commands)
            self.assertIn("journey_early_branching_enabled=False", commands)


if __name__ == "__main__":
    unittest.main()
